"""Utilities for managing the ask_human server."""

import json
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from .port_utils import find_available_port


@dataclass
class AskHumanServer:
    """Represents a running ask_human server."""

    process: subprocess.Popen
    port: int
    url: str

    def get_logs(self, timeout: int = 10) -> dict | None:
        """Retrieve logs from the server."""
        try:
            req = urllib.request.Request(
                f"http://localhost:{self.port}/get_logs",
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode())
        except Exception:
            pass
        return None

    def stop(self, timeout: int = 5) -> None:
        """Stop the server gracefully."""
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


class AskHumanServerError(Exception):
    """Raised when the ask_human server fails to start."""


@dataclass
class BusinessInfoServer:
    """Represents a running get_business_info server."""

    process: subprocess.Popen
    port: int
    url: str

    def stop(self, timeout: int = 20) -> None:
        """Stop the server gracefully."""
        self.process.terminate()
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()


class BusinessInfoServerError(Exception):
    """Raised when the get_business_info server fails to start."""


@contextmanager
def start_ask_human_server(
    blockers: dict | list | None = None,
    tasks_dir: Path | None = None,
    port: int = 19521,
    startup_wait: float = 2.0,
    capture_output: bool = False,
    verbose: bool = True,
    instance_id: str = "default",
) -> Iterator[AskHumanServer]:
    """
    Context manager for starting and stopping the ask_human server.

    Accepts blockers in one of two ways:
    1. blockers: A dict/list containing the blocker registry data (passed as JSON to server)
    2. tasks_dir: A directory path (server will look for blocker_registry.json files)

    If both are provided, blockers takes precedence.

    Args:
        blockers: Blocker registry data. Can be:
            - A list of blocker entries
            - A dict with "blockers" key (single instance format)
            - A dict mapping instance_id to blocker registry (multi-instance format)
        tasks_dir: Directory containing tasks with blocker_registry.json files
        port: Port to start searching from (will find available port)
        startup_wait: Seconds to wait for server startup
        capture_output: If True, capture stdout/stderr instead of showing them
        verbose: If True, print status messages
        instance_id: Instance ID to use when blockers is in single-instance format

    Yields:
        AskHumanServer instance with process, port, and url

    Raises:
        AskHumanServerError: If server fails to start

    Example:
        # Using blockers directly (single instance)
        with start_ask_human_server(blockers={"blockers": [...]}) as server:
            # server.url contains the /ask endpoint URL
            # server.port contains the port number
            pass
        # Server is automatically stopped on exit

        # Using blockers directly (multi-instance)
        with start_ask_human_server(blockers={"id1": {"blockers": [...]}, "id2": {"blockers": [...]}}) as server:
            pass

        # Using tasks directory
        with start_ask_human_server(tasks_dir=Path("./tasks")) as server:
            pass
    """
    actual_port = find_available_port(port)
    if verbose and actual_port != port:
        print(f"⚠️  Port {port} is in use, using port {actual_port} instead")

    cmd = [
        sys.executable,
        "-m",
        "hil_bench.ask_human_server",
        "--port",
        str(actual_port),
    ]

    # Add blockers or tasks-dir
    if blockers is not None:
        # Normalize to the multi-instance format: {instance_id: {"blockers": [...]}}
        if isinstance(blockers, list):
            # List of blockers -> wrap in instance
            blockers = {instance_id: {"blockers": blockers}}
        elif isinstance(blockers, dict):
            if "blockers" in blockers:
                # Single-instance format -> wrap with instance_id
                blockers = {instance_id: blockers}
            # else: already in multi-instance format, pass through
        cmd.extend(["--blockers-json", json.dumps(blockers)])
    elif tasks_dir is not None:
        cmd.extend(["--tasks-dir", str(tasks_dir.resolve())])

    if verbose:
        print(f"🚀 Starting ask_human server on port {actual_port}...")

    if capture_output:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    time.sleep(startup_wait)

    # Check if server started successfully
    if process.poll() is not None:
        stderr_output = ""
        if process.stderr:
            stderr_output = process.stderr.read().decode()
        raise AskHumanServerError(f"Failed to start ask_human server: {stderr_output}")

    server_url = f"http://localhost:{actual_port}/ask"
    if verbose:
        print(f"✅ ask_human server started at {server_url}")

    server = AskHumanServer(process=process, port=actual_port, url=server_url)

    try:
        yield server
    finally:
        if verbose:
            print("🛑 Stopping ask_human server...")
        server.stop()
        if verbose:
            print("✅ Server stopped.")


@contextmanager
def start_business_info_server(
    port: int = 19531,
    startup_wait: float = 2.0,
    capture_output: bool = False,
    verbose: bool = True,
    skip_warmup: bool = False,
    ready_timeout: float = 300.0,
    ready_poll_interval: float = 2.0,
) -> Iterator[BusinessInfoServer]:
    """Context manager for starting and stopping the get_business_info server."""
    actual_port = find_available_port(port)
    if verbose and actual_port != port:
        print(f"⚠️  Port {port} is in use, using port {actual_port} instead")

    cmd = [
        sys.executable,
        "-m",
        "hil_bench.business_info_server",
        "--port",
        str(actual_port),
    ]
    if skip_warmup:
        cmd.append("--skip-warmup")

    if verbose:
        print(f"🚀 Starting get_business_info server on port {actual_port}...")

    if capture_output:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    else:
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    time.sleep(startup_wait)
    if process.poll() is not None:
        stderr_output = ""
        if process.stderr:
            stderr_output = process.stderr.read().decode()
        raise BusinessInfoServerError(f"Failed to start get_business_info server: {stderr_output}")

    # Wait until health endpoint responds to avoid startup races.
    # On cold start, warmup may download the embedding model and take a while.
    server_url = f"http://localhost:{actual_port}"
    ready = False
    last_error = None
    deadline = time.time() + max(1.0, ready_timeout)
    while time.time() < deadline:
        if process.poll() is not None:
            break
        try:
            with urllib.request.urlopen(f"{server_url}/health", timeout=1.0) as response:
                if response.status == 200:
                    ready = True
                    break
        except Exception as exc:
            last_error = exc
            time.sleep(max(1, ready_poll_interval))
    if not ready:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        raise BusinessInfoServerError(
            "get_business_info server did not become ready in time"
            + (f": {last_error}" if last_error else "")
        )
    if verbose:
        print(f"✅ get_business_info server started at {server_url}")

    server = BusinessInfoServer(process=process, port=actual_port, url=server_url)
    try:
        yield server
    finally:
        if verbose:
            print("🛑 Stopping get_business_info server...")
        server.stop()
        if verbose:
            print("✅ get_business_info server stopped.")
