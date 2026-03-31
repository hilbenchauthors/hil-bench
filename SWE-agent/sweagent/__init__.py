from __future__ import annotations

import os
import sys
from functools import partial
from logging import WARNING, getLogger
from pathlib import Path

import swerex.utils.log as log_swerex
from git import Repo
from packaging import version
from sweagent.utils.log import get_logger

__version__ = "1.1.0"
PYTHON_MINIMUM_VERSION = (3, 11)
SWEREX_MINIMUM_VERSION = "1.2.0"
SWEREX_RECOMMENDED_VERSION = "1.2.1"

# Monkey patch the logger to use our implementation
log_swerex.get_logger = partial(get_logger, emoji="🦖")


# Monkey patch swerex Docker deployment to fix issues with SWEAP images:
#
# 1. PIP_INDEX_URL: SWEAP images have broken /etc/pip.conf pointing to 127.0.0.1:9876.
#    This breaks `pip install swe-rex` during Docker build. Fix: add --index-url.
#
# 2. Python installation: The default swerex Dockerfile uses a multi-stage build that
#    compiles Python 3.11, then copies it to the target image. This fails for various reasons:
#    - Images that already have Python 3.11+ (unnecessary rebuild)
#    - Images with older glibc (e.g., Ubuntu 20.04 has glibc 2.31)
#    - Images with full filesystems (can't apt-get install build deps)
#    - Images with expired GPG keys (apt-get update fails)
#    - Alpine/musl-based images (no glibc compatibility)
#
#    Fix: Three-tier approach:
#    a) Check if Python 3.11+ already exists - just use it (fastest, most compatible)
#    b) Try python-build-standalone prebuilt binaries (~30MB, requires glibc 2.17+)
#       - No apt-get needed, fast (~10s)
#    c) Fall back to compiling from source if prebuilt fails
#       - Handles very old images with glibc < 2.17
#       - Uses --allow-insecure-repositories for expired GPG keys
#
# 3. HTTP request timeout: swerex's remote.py uses aiohttp with NO timeout parameter,
#    so it defaults to 300 seconds. This causes TimeoutError during setup on large
#    repos where `git add -A` takes > 5 minutes. Fix: Monkey-patch to use 600s.
#
def _apply_swerex_http_timeout_fix():
    """
    Fix swerex's HTTP timeout issue. The remote runtime uses aiohttp without
    specifying a timeout, so it defaults to 300 seconds. For large repos where
    git add -A takes > 5 minutes, this causes TimeoutError during setup.

    Solution: Monkey-patch RemoteRuntime._request to use a longer timeout.
    """
    try:
        import aiohttp
        from swerex.runtime import remote as swerex_remote

        async def patched_request(self, endpoint, payload, output_class, num_retries=0):
            """
            Patched _request that uses a 600-second timeout for HTTP requests.
            This is necessary because:
            - The original uses aiohttp's default 300s timeout
            - Large repos (e.g., protonmail/webclients) need > 5 min for git add -A
            - BashAction.timeout is inside payload, but HTTP times out first
            """
            import asyncio
            import random
            import uuid

            request_url = f"{self._api_url}/{endpoint}"
            request_id = str(uuid.uuid4())
            headers = self._headers.copy()
            headers["X-Request-ID"] = request_id

            retry_count = 0
            last_exception = None
            retry_delay = 0.1
            backoff_max = 5

            # Use 600 second HTTP timeout (10 minutes) to handle large repos
            # This should be longer than any BashAction.timeout we use
            http_timeout = aiohttp.ClientTimeout(total=600)

            while retry_count <= num_retries:
                try:
                    async with aiohttp.ClientSession(
                        connector=aiohttp.TCPConnector(force_close=True), timeout=http_timeout
                    ) as session:
                        async with session.post(
                            request_url,
                            json=payload.model_dump() if payload else None,
                            headers=headers,
                        ) as resp:
                            await self._handle_response_errors(resp)
                            return output_class(**await resp.json())
                except Exception as e:
                    last_exception = e
                    retry_count += 1
                    if retry_count <= num_retries:
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        retry_delay += random.uniform(0, 0.5)
                        retry_delay = min(retry_delay, backoff_max)
                        continue
                    self.logger.error(
                        "Error making request %s after %d retries: %s", request_id, num_retries, e
                    )
            raise last_exception

        # Apply the monkey-patch
        swerex_remote.RemoteRuntime._request = patched_request
    except Exception:
        pass  # Don't break if swerex API changes


_apply_swerex_http_timeout_fix()


def _apply_swerex_fixes():
    try:
        from swerex import PACKAGE_NAME, REMOTE_EXECUTABLE_NAME
        from swerex.deployment import docker as swerex_docker

        original_glibc_dockerfile = swerex_docker.DockerDeployment.glibc_dockerfile.fget

        @property
        def patched_glibc_dockerfile(self):
            original = original_glibc_dockerfile(self)

            # Fix 1: Add --index-url to pip install to override broken pip.conf
            patched = original.replace(
                "pip3 install --no-cache-dir swe-rex",
                "pip3 install --no-cache-dir --index-url https://pypi.org/simple/ swe-rex",
            )

            # Fix 2: Convert multi-stage build to single-stage to avoid glibc mismatch
            # Remove the builder stage and COPY, build Python directly in target image
            if "AS builder" in patched and "COPY --from=builder" in patched:
                python_dir = self._config.python_standalone_dir
                if self._config.platform:
                    platform_arg = f"--platform={self._config.platform}"
                else:
                    platform_arg = ""

                # Three-tier Python installation strategy:
                # Tier 1: Use existing Python 3.11+ if available (fastest, most compatible)
                # Tier 2: Download python-build-standalone prebuilt binaries (fast, needs glibc 2.17+)
                # Tier 3: Compile from source (slowest, handles ancient systems)
                pbs_url = "https://github.com/indygreg/python-build-standalone/releases/download/20240107/cpython-3.11.7+20240107-x86_64-unknown-linux-gnu-install_only.tar.gz"
                patched = (
                    "ARG BASE_IMAGE\n\n"
                    f"FROM {platform_arg} $BASE_IMAGE\n"
                    f"WORKDIR {python_dir}\n"
                    # Install patch utility (required by swebench for applying diffs)
                    # Detect package manager and install patch if missing
                    "RUN if ! command -v patch >/dev/null 2>&1; then \\\n"
                    "        if command -v apk >/dev/null 2>&1; then \\\n"
                    "            apk add --no-cache patch; \\\n"
                    "        elif command -v apt-get >/dev/null 2>&1; then \\\n"
                    "            apt-get update && apt-get install -y --no-install-recommends patch && rm -rf /var/lib/apt/lists/*; \\\n"
                    "        elif command -v yum >/dev/null 2>&1; then \\\n"
                    "            yum install -y patch && yum clean all; \\\n"
                    "        fi; \\\n"
                    "    fi\n\n"
                    # Three-tier Python installation
                    "RUN set -e; \\\n"
                    # Tier 1: Check if system Python 3.11+ already exists
                    "    SYSTEM_PY=$(command -v python3 2>/dev/null || true); \\\n"
                    '    if [ -n "$SYSTEM_PY" ]; then \\\n'
                    "        PY_VER=$($SYSTEM_PY -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")' 2>/dev/null || echo '0.0'); \\\n"
                    "        PY_MAJOR=$(echo $PY_VER | cut -d. -f1); \\\n"
                    "        PY_MINOR=$(echo $PY_VER | cut -d. -f2); \\\n"
                    '        if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then \\\n'
                    '            echo "Using existing Python $PY_VER at $SYSTEM_PY"; \\\n'
                    "            $SYSTEM_PY -m ensurepip --upgrade 2>/dev/null || true; \\\n"
                    "            if $SYSTEM_PY -m pip --version >/dev/null 2>&1; then \\\n"
                    "                mkdir -p python3.11/bin; \\\n"
                    "                ln -sf $SYSTEM_PY python3.11/bin/python3; \\\n"
                    "                PIP_PATH=$(dirname $SYSTEM_PY)/pip3; \\\n"
                    '                if [ -x "$PIP_PATH" ]; then ln -sf $PIP_PATH python3.11/bin/pip3; fi; \\\n'
                    "                exit 0; \\\n"
                    "            fi; \\\n"
                    "            echo 'System Python found but pip is unavailable, trying next tier...'; \\\n"
                    "        fi; \\\n"
                    "    fi; \\\n"
                    # Tier 2: Try distro Python first (avoids external downloads on Debian images)
                    "    if command -v apt-get >/dev/null 2>&1; then \\\n"
                    "        echo 'Trying distro Python via apt...'; \\\n"
                    "        apt-get update -o Acquire::AllowInsecureRepositories=true \\\n"
                    "            -o Acquire::AllowDowngradeToInsecureRepositories=true 2>/dev/null || true; \\\n"
                    "        if apt-get install -y --allow-unauthenticated --no-install-recommends \\\n"
                    "            python3 python3-pip ca-certificates 2>/dev/null; then \\\n"
                    "            APY=$(command -v python3 || true); \\\n"
                    "            if [ -n \"$APY\" ]; then \\\n"
                    "                APY_VER=$($APY -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")' 2>/dev/null || echo '0.0'); \\\n"
                    "                APY_MAJOR=$(echo $APY_VER | cut -d. -f1); \\\n"
                    "                APY_MINOR=$(echo $APY_VER | cut -d. -f2); \\\n"
                    "                if [ \"$APY_MAJOR\" -ge 3 ] && [ \"$APY_MINOR\" -ge 11 ]; then \\\n"
                    "                    mkdir -p python3.11/bin; \\\n"
                    "                    ln -sf $APY python3.11/bin/python3; \\\n"
                    "                    APIP=$(command -v pip3 || true); \\\n"
                    "                    if [ -n \"$APIP\" ]; then ln -sf $APIP python3.11/bin/pip3; fi; \\\n"
                    "                    echo \"Using apt-installed Python $APY_VER\"; \\\n"
                    "                    exit 0; \\\n"
                    "                fi; \\\n"
                    "            fi; \\\n"
                    "        fi; \\\n"
                    "    fi; \\\n"
                    # Tier 3: Try python-build-standalone (curl or wget)
                    "    echo 'No suitable Python found, trying python-build-standalone...'; \\\n"
                    "    ( \\\n"
                    "        ( command -v curl >/dev/null 2>&1 && \\\n"
                    f"          curl -fsSL {pbs_url} | tar xzf - \\\n"
                    "        ) || \\\n"
                    "        ( command -v wget >/dev/null 2>&1 && \\\n"
                    f"          wget -qO- {pbs_url} | tar xzf - \\\n"
                    "        ) \\\n"
                    "    ) && mv python python3.11 \\\n"
                    f"      && {python_dir}/python3.11/bin/python3 --version \\\n"
                    "    && exit 0; \\\n"
                    # Tier 4: Compile from source
                    "    echo 'python-build-standalone failed, falling back to compilation...'; \\\n"
                    "    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /tmp/* /var/tmp/*; \\\n"
                    "    apt-get update -o Acquire::AllowInsecureRepositories=true \\\n"
                    "        -o Acquire::AllowDowngradeToInsecureRepositories=true 2>/dev/null || true; \\\n"
                    "    apt-get install -y --allow-unauthenticated --no-install-recommends \\\n"
                    "        -o Dir::Cache::Archives=/dev/shm \\\n"
                    "        wget gcc make zlib1g-dev libssl-dev 2>/dev/null; \\\n"
                    "    cd /tmp; \\\n"
                    "    wget -q https://www.python.org/ftp/python/3.11.8/Python-3.11.8.tgz; \\\n"
                    "    tar xzf Python-3.11.8.tgz; \\\n"
                    "    cd Python-3.11.8; \\\n"
                    f"    ./configure --prefix={python_dir}/python3.11 --enable-shared \\\n"
                    f"        LDFLAGS='-Wl,-rpath={python_dir}/python3.11/lib'; \\\n"
                    "    make -j$(nproc) && make install && ldconfig; \\\n"
                    "    rm -rf /tmp/Python*\n\n"
                    # Set up environment
                    f"ENV PATH={python_dir}/python3.11/bin:$PATH\n"
                    f"ENV LD_LIBRARY_PATH={python_dir}/python3.11/lib:${{LD_LIBRARY_PATH:-}}\n"
                    # Verify Python works
                    f"RUN {python_dir}/python3.11/bin/python3 --version\n"
                    # Install swe-rex (use pip3 if available, else python -m pip)
                    # Add --break-system-packages for PEP 668 externally managed environments (Debian/Ubuntu)
                    f"RUN {python_dir}/python3.11/bin/pip3 install --no-cache-dir --break-system-packages --index-url https://pypi.org/simple/ {PACKAGE_NAME} 2>/dev/null \\\n"
                    f"    || {python_dir}/python3.11/bin/python3 -m pip install --no-cache-dir --break-system-packages --index-url https://pypi.org/simple/ {PACKAGE_NAME}\n\n"
                    # Create symlinks for swe-rex executable
                    # When using system Python, pip installs scripts to system bin (e.g. /usr/local/bin)
                    # but swerex expects them at {python_dir}/python3.11/bin/swerex-remote
                    # So we need to create symlinks IN {python_dir}/python3.11/bin/ pointing to the actual location
                    f"RUN mkdir -p {python_dir}/python3.11/bin && \\\n"
                    f'    if [ ! -x "{python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME}" ]; then \\\n'
                    f"        ACTUAL_BIN=$(command -v {REMOTE_EXECUTABLE_NAME} 2>/dev/null || echo ''); \\\n"
                    f'        if [ -n "$ACTUAL_BIN" ] && [ -x "$ACTUAL_BIN" ]; then \\\n'
                    f'            ln -sf "$ACTUAL_BIN" {python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME}; \\\n'
                    f'            echo "Created symlink: {python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME} -> $ACTUAL_BIN"; \\\n'
                    "        else \\\n"
                    f"            for p in /usr/local/bin/{REMOTE_EXECUTABLE_NAME} /usr/bin/{REMOTE_EXECUTABLE_NAME}; do \\\n"
                    f'                if [ -x "$p" ]; then ln -sf "$p" {python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME}; break; fi; \\\n'
                    "            done; \\\n"
                    "        fi; \\\n"
                    "    fi && \\\n"
                    f"    ln -sf {python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME} /usr/local/bin/{REMOTE_EXECUTABLE_NAME} 2>/dev/null || true\n\n"
                    f"RUN {python_dir}/python3.11/bin/{REMOTE_EXECUTABLE_NAME} --version\n"
                )

            return patched

        swerex_docker.DockerDeployment.glibc_dockerfile = patched_glibc_dockerfile
    except Exception:
        pass  # Don't break if swerex API changes


_apply_swerex_fixes()

# See https://github.com/SWE-agent/SWE-agent/issues/585
getLogger("datasets").setLevel(WARNING)
getLogger("numexpr.utils").setLevel(WARNING)
getLogger("LiteLLM").setLevel(WARNING)

PACKAGE_DIR = Path(__file__).resolve().parent

if sys.version_info < PYTHON_MINIMUM_VERSION:
    msg = (
        f"Python {sys.version_info.major}.{sys.version_info.minor} is not supported. "
        "SWE-agent requires Python 3.11 or higher."
    )
    raise RuntimeError(msg)

assert PACKAGE_DIR.is_dir(), PACKAGE_DIR
REPO_ROOT = PACKAGE_DIR.parent
assert REPO_ROOT.is_dir(), REPO_ROOT
CONFIG_DIR = Path(os.getenv("SWE_AGENT_CONFIG_DIR", PACKAGE_DIR.parent / "config"))
assert CONFIG_DIR.is_dir(), CONFIG_DIR

TOOLS_DIR = Path(os.getenv("SWE_AGENT_TOOLS_DIR", PACKAGE_DIR.parent / "tools"))
assert TOOLS_DIR.is_dir(), TOOLS_DIR

TRAJECTORY_DIR = Path(os.getenv("SWE_AGENT_TRAJECTORY_DIR", PACKAGE_DIR.parent / "trajectories"))
assert TRAJECTORY_DIR.is_dir(), TRAJECTORY_DIR


def get_agent_commit_hash() -> str:
    """Get the commit hash of the current SWE-agent commit.

    If we cannot get the hash, we return an empty string.
    """
    try:
        repo = Repo(REPO_ROOT, search_parent_directories=False)
    except Exception:
        return "unavailable"
    return repo.head.object.hexsha


def get_rex_commit_hash() -> str:
    import swerex

    try:
        repo = Repo(
            Path(swerex.__file__).resolve().parent.parent.parent, search_parent_directories=False
        )
    except Exception:
        return "unavailable"
    return repo.head.object.hexsha


def get_rex_version() -> str:
    from swerex import __version__ as rex_version

    return rex_version


def get_agent_version_info() -> str:
    hash = get_agent_commit_hash()
    rex_hash = get_rex_commit_hash()
    rex_version = get_rex_version()
    return f"This is SWE-agent version {__version__} ({hash=}) with SWE-ReX version {rex_version} ({rex_hash=})."


def impose_rex_lower_bound() -> None:
    rex_version = get_rex_version()
    minimal_rex_version = "1.2.0"
    if version.parse(rex_version) < version.parse(minimal_rex_version):
        msg = (
            f"SWE-ReX version {rex_version} is too old. Please update to at least {minimal_rex_version} by "
            "running `pip install --upgrade swe-rex`."
            "You can also rerun `pip install -e .` in this repository to install the latest version."
        )
        raise RuntimeError(msg)
    if version.parse(rex_version) < version.parse(SWEREX_RECOMMENDED_VERSION):
        msg = (
            f"SWE-ReX version {rex_version} is not recommended. Please update to at least {SWEREX_RECOMMENDED_VERSION} by "
            "running `pip install --upgrade swe-rex`."
            "You can also rerun `pip install -e .` in this repository to install the latest version."
        )
        get_logger("swe-agent", emoji="👋").warning(msg)


impose_rex_lower_bound()
get_logger("swe-agent", emoji="👋").info(get_agent_version_info())


__all__ = [
    "PACKAGE_DIR",
    "CONFIG_DIR",
    "get_agent_commit_hash",
    "get_agent_version_info",
    "__version__",
]
