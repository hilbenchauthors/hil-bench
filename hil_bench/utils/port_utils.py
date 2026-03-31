"""Utility functions for finding available ports."""

import socket


def find_available_port(start_port: int = 9521, max_attempts: int = 100) -> int:
    """
    Find an available port starting from start_port.

    Tries ports incrementally until finding one that's available.

    Args:
        start_port: Port to start searching from
        max_attempts: Maximum number of ports to try

    Returns:
        An available port number

    Raises:
        RuntimeError: If no available port found after max_attempts
    """
    for offset in range(max_attempts):
        port = start_port + offset
        if is_port_available(port):
            return port

    raise RuntimeError(
        f"Could not find available port after trying {max_attempts} ports starting from {start_port}"
    )


def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    for host in ("127.0.0.1", "localhost"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)
                if s.connect_ex((host, port)) == 0:
                    return False
        except OSError:  # ignore DNS/network errors and fall back to bind checks
            pass
    for host in ("127.0.0.1", "0.0.0.0"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
        except OSError:
            return False
    return True
