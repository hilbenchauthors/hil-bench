"""
Custom instance evaluation for HIL-bench tasks using swebench infrastructure.

This module provides deep integration with swebench while supporting:
- Fully custom local git repositories (not from GitHub)
- Custom installation specs (Python version, test commands, dependencies)
- Standard swebench grading and log parsing

Key differences from standard swebench:
- Local repos are COPIED into Docker containers (not cloned from GitHub)
- Custom specs can be defined per-instance (not limited to MAP_REPO_VERSION_TO_SPECS)
- Supports metadata.json format for task configuration

Custom instances are defined in tasks/*/metadata.json with:
- repo_name: Local path to git repo
- image_name: Base Docker image (optional, derived from specs if not provided)
- swe_bench_metadata.FAIL_TO_PASS: Tests that should pass after the fix
- swe_bench_metadata.PASS_TO_PASS: Tests that should still pass
- test_cmd: Command to run tests (default: pytest -rA)
- install_cmd: Command to install project (default: pip install -e .)
- python_version: Python version (default: 3.11)
- pip_packages: Additional pip packages to install
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import time
import traceback
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, NotRequired, Required, TypedDict

import docker
import docker.errors
from filelock import FileLock, Timeout
from swebench.harness.constants import (
    END_TEST_OUTPUT,
    INSTANCE_IMAGE_BUILD_DIR,
    MAP_REPO_TO_EXT,
    MAP_REPO_VERSION_TO_SPECS,
    RUN_EVALUATION_LOG_DIR,
    START_TEST_OUTPUT,
)
from swebench.harness.docker_build import build_env_images, build_image
from swebench.harness.log_parsers import MAP_REPO_TO_PARSER
from swebench.harness.log_parsers.go import parse_log_gotest
from swebench.harness.log_parsers.java import parse_log_gradle_custom, parse_log_maven
from swebench.harness.log_parsers.javascript import (
    parse_log_jest,
    parse_log_karma,
    parse_log_vitest,
)
from swebench.harness.log_parsers.python import parse_log_pytest
from swebench.harness.log_parsers.ruby import parse_log_minitest
from swebench.harness.log_parsers.rust import parse_log_cargo
import swebench.harness.docker_utils as swebench_docker_utils
import swebench.harness.run_evaluation as swebench_run_evaluation
from swebench.harness.run_evaluation import run_instance
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec

from .instance_utils import extract_original_instance_id


def exec_run_with_timeout_utf8_safe(container, cmd, timeout: int | None = 60):
    exec_result = b""
    exec_id = None
    exception = None
    timed_out = False

    def run_command():
        nonlocal exec_result, exec_id, exception
        try:
            exec_id = container.client.api.exec_create(container.id, cmd)["Id"]
            exec_stream = container.client.api.exec_start(exec_id, stream=True)
            for chunk in exec_stream:
                exec_result += chunk
        except Exception as e:
            exception = e

    thread = threading.Thread(target=run_command)
    start_time = time.time()
    thread.start()
    thread.join(timeout)

    if exception:
        raise exception

    if thread.is_alive():
        if exec_id is not None:
            exec_pid = container.client.api.exec_inspect(exec_id)["Pid"]
            container.exec_run(f"kill -TERM {exec_pid}", detach=True)
        timed_out = True
    end_time = time.time()
    return exec_result.decode("utf-8", errors="replace"), timed_out, end_time - start_time


# Patch swebench to avoid hard failures when command output includes non-UTF-8 bytes.
swebench_docker_utils.exec_run_with_timeout = exec_run_with_timeout_utf8_safe
swebench_run_evaluation.exec_run_with_timeout = exec_run_with_timeout_utf8_safe

# =============================================================================
# Patch Failure Detection
# =============================================================================


def _detect_test_patch_failure(test_output: str, model_patch: str, test_patch: str) -> str | None:
    """
    Detect if test_patch failed to apply during evaluation.

    This distinguishes between:
    - test_patch failure → input validation error (data provider's fault)
    - model_patch failure → agent's fault (not input validation error)

    Args:
        test_output: The test output from swebench evaluation
        model_patch: The agent's solution patch
        test_patch: The test patch from metadata

    Returns:
        Error message if test_patch failed, None otherwise
    """
    if not test_output:
        return None

    failure_patterns = [
        r"error: patch failed:",
        r"patch does not apply",
        r"error: while searching for:",
    ]

    for pattern in failure_patterns:
        if re.search(pattern, test_output, re.IGNORECASE):
            # Extract the file that failed
            file_match = re.search(r"error: patch failed: ([^\n:]+)", test_output)
            if file_match:
                failed_file = file_match.group(1).strip()
                # Check if this file is in test_patch (input validation error)
                # vs model_patch (agent's fault)
                if failed_file in test_patch:
                    return f"SWE INPUT VALIDATION FAILED: test_patch failed to apply to file: {failed_file}"
                elif failed_file in model_patch:
                    # Agent's fault - not an input validation error
                    return None
                else:
                    # Unknown file - could be either, treat as potential input error
                    return f"SWE INPUT VALIDATION FAILED: A patch failed to apply to file: {failed_file}"
            # Generic patch failure - check if test_patch is non-empty
            if test_patch and test_patch.strip():
                return "SWE INPUT VALIDATION FAILED: test_patch failed to apply"
            return None

    return None


# =============================================================================
# Module-level Image Rebuild Tracking
# =============================================================================

# Track which images have been rebuilt during this process to avoid redundant rebuilds.
# This is especially important when running multiple passes of the same task,
# as each pass calls calculate_pass_at_1 separately but the same images can be reused.
_REBUILT_IMAGES: set[str] = set()


# =============================================================================
# Test Spec Augmentation
# =============================================================================


_JS_TS_LANGUAGES = ("js", "ts", "javascript", "typescript", "jsx", "tsx")
_PYTHON_LANGUAGES = ("py", "python")
_GO_LANGUAGES = ("go", "golang")


def _is_hilbench_swe_image(image_name: str) -> bool:
    return image_name.startswith("hilbench-swe:")


def _extract_test_file_path(test_name: str, language: str) -> str:
    """
    Extract the file path from a test name.

    Examples:
        Python: "test/units/test_foo.py::test_bar" -> "test/units/test_foo.py"
        Go: "TestFoo" -> "TestFoo" (no file path extraction needed)
        JS/TS: "test/user.js | User socket methods..." -> "test/user.js"
               "src/__tests__/foo.test.js" -> "src/__tests__/foo.test.js"

    Note: This returns the path as-is from the test name (including any leading
    slashes if present). The caller is responsible for handling path variations.
    """
    if language in _PYTHON_LANGUAGES:
        # Python tests use :: to separate file from test name
        # "test/foo.py::test_bar" -> "test/foo.py"
        # "test/foo.py::TestClass::test_method" -> "test/foo.py"
        return test_name.split("::")[0] if "::" in test_name else test_name
    if language in _JS_TS_LANGUAGES:
        # JS/TS Mocha tests use " | " to separate file from test description
        # "test/user.js | User socket methods..." -> "test/user.js"
        if " | " in test_name:
            return test_name.split(" | ")[0].strip()
        return test_name
    # For other languages, return as-is (may need language-specific handling)
    return test_name


def _augment_go_test_command(test_command: str, test_names: list[str]) -> str:
    """
    Augment a Go test command with specific test names using -run flag.

    Go test syntax:
    - go test -v ./...                         # Run all tests
    - go test -v -run "TestFoo" ./...          # Run tests matching pattern
    - go test -v -run "TestFoo|TestBar" ./...  # Run multiple tests

    We add -run flag with test names joined by |
    """
    if not test_names:
        return test_command

    # Filter to just test function names (starting with Test)
    go_test_names = [t for t in test_names if t.startswith("Test")]
    if not go_test_names:
        return test_command

    # Check if -run flag already exists
    if "-run" in test_command:
        return test_command  # Don't override existing -run flag

    # Build the -run pattern
    run_pattern = "|".join(go_test_names)

    # Insert -run after "go test" but before other args
    parts = test_command.split()
    if len(parts) >= 2 and parts[0] == "go" and parts[1] == "test":
        # Insert -run after "go test"
        new_parts = parts[:2] + ["-run", f'"{run_pattern}"'] + parts[2:]
        return " ".join(new_parts)

    return test_command


def augment_test_spec_with_required_tests(
    test_spec: TestSpec,
    fail_to_pass: list[str],
    pass_to_pass: list[str] | None = None,
    test_files: list[str] | None = None,
    run_script_content: str | None = None,
) -> TestSpec:
    """
    Augment the test_spec's eval_script_list to ensure tests from FAIL_TO_PASS
    (and optionally PASS_TO_PASS) are included in the test run.

    By default, swebench only runs tests from files modified in test_patch.
    This function adds any additional test files from FAIL_TO_PASS/PASS_TO_PASS
    that aren't already included.

    Language-specific handling:
    - SWEAP (run_script.sh): Pass test files as comma-separated argument
    - Python: Appends test file paths to pytest command
    - Go: Uses -run flag for test name filtering (doesn't append paths)
    - Others: Appends test paths to command

    Args:
        test_spec: The TestSpec from make_test_spec
        fail_to_pass: List of tests that must pass after the fix
        pass_to_pass: Optional list of tests that must remain passing
        test_files: Optional list of test files (used for SWEAP format)

    Returns:
        Modified TestSpec with augmented eval_script_list
    """
    if not fail_to_pass and not pass_to_pass:
        return test_spec

    # Find the test command in eval_script_list
    eval_script_list = list(test_spec.eval_script_list)  # Make a mutable copy
    start_marker = f": '{START_TEST_OUTPUT}'"
    end_marker = f": '{END_TEST_OUTPUT}'"
    start_idx = None
    end_idx = None
    for i, cmd in enumerate(eval_script_list):
        if start_marker in cmd:
            start_idx = i
        elif end_marker in cmd:
            end_idx = i
            break
    if start_idx is None or end_idx is None or end_idx <= start_idx + 1:
        # Markers not found or no command between them
        return test_spec

    # There should be exactly one command between start and end markers
    test_cmd_idx = start_idx + 1
    test_command = eval_script_list[test_cmd_idx]

    # Handle SWEAP: test_cmd runs run_script.sh with parser.py
    # Format: "bash /root/run_script.sh > /tmp/stdout.log 2> /tmp/stderr.log; python /root/parser.py ..."
    # Scripts are at /root/ (NOT /app/) so agent cannot see them during problem-solving
    # We need to insert test identifiers as comma-separated arg AFTER run_script.sh but BEFORE the redirect
    #
    # IMPORTANT: Pass test identifiers from FAIL_TO_PASS, NOT test_files.
    # - test_files may contain fixture/config files that aren't runnable tests
    # - FAIL_TO_PASS contains the actual test identifiers the runner expects:
    #   - Go: test names like "TestFoo" for -run flag
    #   - Python: pytest test IDs like "test/foo.py::TestClass::test_method"
    if "run_script.sh" in test_command:
        # Use FAIL_TO_PASS test identifiers
        args_to_pass = list(fail_to_pass or []) + list(pass_to_pass or [])

        # Special case: ansible-test doesn't understand pytest ID syntax (::Class::method)
        uses_ansible_test = run_script_content and "ansible-test" in run_script_content
        if uses_ansible_test and args_to_pass and any("::" in t for t in args_to_pass):
            # Strip ::Class::method suffix to get file paths
            extracted_files = list(set(t.split("::")[0] for t in args_to_pass if "::" in t))
            args_to_pass = (
                extracted_files
                if extracted_files
                else (list(test_files) if test_files else args_to_pass)
            )

        # JS/TS: Strip " | description" suffix from test names.
        # SWEAP JS/TS test names use "file | test description" format (e.g., Mocha/Jest).
        # Some run_script.sh files handle this (NodeBB strips it, Protonmail parses it),
        # but others (element-hq) pass it directly to Jest which misinterprets | as regex OR.
        # Stripping to just file paths is safe for all cases:
        # - NodeBB: Already strips, no change
        # - Protonmail: Falls back to file-only mode, runs more tests but correct ones
        # - Element-hq: Now correctly finds test files
        # - Tutanota: Gracefully falls back to file-only mode
        # Matching still works because parser.py regenerates full "file | test" names.
        if test_spec.language in _JS_TS_LANGUAGES and args_to_pass:
            stripped_args = []
            for t in args_to_pass:
                if " | " in t:
                    # Extract just the file path before " | "
                    file_path = t.split(" | ")[0].strip()
                    stripped_args.append(file_path)
                else:
                    stripped_args.append(t)
            # Deduplicate while preserving order (same file may have multiple tests)
            seen = set()
            args_to_pass = []
            for arg in stripped_args:
                if arg not in seen:
                    seen.add(arg)
                    args_to_pass.append(arg)

        if args_to_pass:
            # Pass tests as separate quoted arguments (not comma-joined) to avoid
            # comma-splitting issues in run_script.sh. This handles parameterized
            # pytest tests like test_func[1,2,3] which contain commas inside brackets.
            quoted_tests = []
            for t in args_to_pass:
                escaped = t.replace("'", "'\\''")
                quoted_tests.append(f"'{escaped}'")
            quoted_args = " ".join(quoted_tests)
            # Insert args after "run_script.sh" but before redirection or semicolon
            # Pattern: "bash /root/run_script.sh" -> "bash /root/run_script.sh 'test1' 'test2'"
            new_test_command = test_command.replace(
                "/root/run_script.sh", f"/root/run_script.sh {quoted_args}"
            )
            eval_script_list[test_cmd_idx] = new_test_command
            return replace(test_spec, eval_script_list=eval_script_list)
        return test_spec

    # Handle Go specially - use -run flag for test names
    if test_spec.language in _GO_LANGUAGES:
        all_tests = list(fail_to_pass or []) + list(pass_to_pass or [])
        new_test_command = _augment_go_test_command(test_command, all_tests)
        if new_test_command != test_command:
            eval_script_list[test_cmd_idx] = new_test_command
            return replace(test_spec, eval_script_list=eval_script_list)
        return test_spec

    # For other languages (Python, JS, etc.), collect test file paths
    required_tests = set()
    for test_name in fail_to_pass or []:
        test_path = _extract_test_file_path(test_name, test_spec.language)
        required_tests.add(test_path)
    for test_name in pass_to_pass or []:
        test_path = _extract_test_file_path(test_name, test_spec.language)
        required_tests.add(test_path)
    if not required_tests:
        return test_spec

    parts = test_command.split()
    if not parts:
        return test_spec

    # Find existing test paths in the command
    existing_tests = set()
    for i, part in enumerate(parts):
        # Skip the test runner command and flags
        if part.startswith("-") or i == 0:
            continue
        existing_tests.add(part)

    # Find tests that need to be added
    tests_to_add = required_tests - existing_tests
    if not tests_to_add:
        return test_spec

    new_test_command = test_command + " " + " ".join(sorted(tests_to_add))
    eval_script_list[test_cmd_idx] = new_test_command
    return replace(test_spec, eval_script_list=eval_script_list)


def clear_rebuilt_images_cache() -> None:
    """Clear the module-level rebuilt images cache. Useful for testing or fresh runs."""
    global _REBUILT_IMAGES
    _REBUILT_IMAGES = set()


def get_rebuilt_images_cache() -> set[str]:
    """Get the current rebuilt images cache (for debugging)."""
    return _REBUILT_IMAGES.copy()


# =============================================================================
# File System Utilities
# =============================================================================


def _remove_broken_symlinks(directory: Path) -> int:
    """
    Recursively remove broken symlinks from a directory.

    Docker's tar process fails when it encounters broken symlinks during
    image build. This function removes them to prevent build failures.

    Args:
        directory: Path to the directory to clean

    Returns:
        Number of broken symlinks removed
    """
    removed = 0
    for root, dirs, files in os.walk(directory, topdown=False):
        root_path = Path(root)
        # Check files (including symlinks to files)
        for name in files:
            path = root_path / name
            if path.is_symlink() and not path.exists():
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass  # Ignore errors during removal
        # Check directories (including symlinks to directories)
        for name in dirs:
            path = root_path / name
            if path.is_symlink() and not path.exists():
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass  # Ignore errors during removal
    if removed > 0:
        print(f"🧹 Removed {removed} broken symlink(s) from {directory}")
    return removed


# =============================================================================
# Patch Utilities
# =============================================================================

# Patterns for files that should be filtered from patches (generated/binary files)
PATCH_FILTER_PATTERNS = [
    r"__pycache__/",  # Python bytecode cache
    r"node_modules/",  # Node.js dependencies
    r"\.egg-info/",  # Python egg info
    r"diff --git a/\S+\.pyc ",  # Python compiled files
    r"diff --git a/\S+\.pyo ",  # Python optimized files
    r"diff --git a/\S+\.so ",  # Shared objects
    r"diff --git a/\S+\.dll ",  # Windows DLLs
    r"diff --git a/\S+\.dylib ",  # macOS dynamic libraries
    # HIL-bench infrastructure files
    r"diff --git a/parser\.py b/parser\.py",  # SWEAP parser script
    r"diff --git a/run_script\.sh b/run_script\.sh",  # SWEAP run script
    # Redis persistence files (CLEARLY not code - Redis creates these at runtime)
    r"appendonlydir/",  # Redis AOF persistence directory
    r"diff --git a/\S*dump\.rdb ",  # Redis RDB snapshot
    r"diff --git a/\S*appendonly\.aof ",  # Redis AOF persistence file
]


def filter_patch(patch: str) -> str:
    """
    Filter out generated/binary files from a patch.

    Model patches sometimes include __pycache__ and other generated files
    that can cause patch application to fail. This removes those hunks.

    Args:
        patch: The full patch string (unified diff format)

    Returns:
        Filtered patch with generated files removed
    """
    if not patch:
        return patch

    # Split patch into individual file diffs
    # Each file diff starts with "diff --git"
    file_diffs = re.split(r"(?=diff --git )", patch)

    filtered_diffs = []
    for diff in file_diffs:
        if not diff.strip():
            continue

        # Check if this diff is for a file that should be filtered
        should_filter = False
        for pattern in PATCH_FILTER_PATTERNS:
            if re.search(pattern, diff):
                should_filter = True
                break

        if not should_filter:
            filtered_diffs.append(diff)

    return "".join(filtered_diffs)


# =============================================================================
# SWEAP Log Parser (for run_script.sh output)
# =============================================================================


def parse_log_sweap_json(log: str, test_spec: TestSpec) -> dict[str, str]:
    """
    Parser for SWEAP test output JSON produced by instance-specific parser.py.

    SWEAP instances provide two scripts:
    - run_script.sh: Runs tests with correct environment and flags
    - parser.py: Parses test output into structured JSON

    The test_cmd runs both and outputs JSON like:
    {
        "tests": [
            {"name": "test_name", "status": "PASSED|FAILED|SKIPPED|ERROR"},
            ...
        ]
    }

    This parser reads that JSON and converts to swebench's status map format.

    Args:
        log: JSON output from parser.py (captured via `cat /tmp/output.json`)
        test_spec: TestSpec (unused but required by swebench parser interface)

    Returns:
        dict: test case to test status mapping
    """
    from swebench.harness.constants import TestStatus

    test_status_map = {}

    # Find JSON in the log output using markers
    # The test_cmd outputs: echo 'SWEAP_JSON_START'; cat output.json; echo 'SWEAP_JSON_END'
    # This allows reliable extraction even if shell output gets interleaved
    data = None

    # Strategy 1: Look for our markers (most reliable)
    start_marker = "SWEAP_JSON_START"
    end_marker = "SWEAP_JSON_END"
    start_idx = log.find(start_marker)
    end_idx = log.find(end_marker)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        json_section = log[start_idx + len(start_marker) : end_idx].strip()
        try:
            data = json.loads(json_section)
        except json.JSONDecodeError:
            pass

    # Strategy 2: Look for JSON structure directly
    if data is None:
        json_start = log.find('{\n  "tests"')
        if json_start == -1:
            json_start = log.find('{"tests"')

        if json_start != -1:
            section = log[json_start:]
            for end_pattern in ["\n  ]\n}", "]\n}", "]}"]:
                end_pos = section.rfind(end_pattern)
                if end_pos != -1:
                    json_str = section[: end_pos + len(end_pattern)]
                    try:
                        data = json.loads(json_str)
                        break
                    except json.JSONDecodeError:
                        continue

    # Strategy 3: Try parsing entire log (last resort)
    if data is None:
        try:
            data = json.loads(log.strip())
        except json.JSONDecodeError:
            pass

    if data is None:
        return test_status_map

    # Filter results to only include FAIL_TO_PASS
    required_tests: set[str] = set()
    if test_spec is not None:
        required_tests.update(test_spec.FAIL_TO_PASS or [])
        required_tests.update(test_spec.PASS_TO_PASS or [])

    def _extract_pytest_components(test_name: str) -> tuple[str | None, str, str]:
        """
        Extract components from a pytest-style test name.

        Returns: (file_path, func_with_params, func_base)
        - file_path: "path/file.py" or None if no path
        - func_with_params: "test_foo[param]" or "test_foo"
        - func_base: "test_foo" (without parameters)
        """
        file_path = None
        func_with_params = test_name

        if "::" in test_name:
            # Split on :: - could be file::func or file::Class::method
            parts = test_name.split("::")
            file_path = parts[0]
            func_with_params = parts[-1]  # Last part is always the function

        # Strip parameters
        func_base = func_with_params.split("[")[0] if "[" in func_with_params else func_with_params

        return file_path, func_with_params, func_base

    def _paths_match(path1: str | None, path2: str | None) -> bool:
        """
        Check if two file paths match, handling different root prefixes.

        Examples that should match:
        - "test/units/utils/file.py" and "units/utils/file.py"
        - "path/to/file.py" and "path/to/file.py"
        - None and None
        """
        if path1 is None and path2 is None:
            return True
        if path1 is None or path2 is None:
            return False

        # Exact match
        if path1 == path2:
            return True

        # Suffix match (handles different root prefixes)
        return (
            path1.endswith("/" + path2)
            or path2.endswith("/" + path1)
            or path1.endswith(path2)
            or path2.endswith(path1)
        )

    def _find_matching_required_test(parser_test_name: str) -> str | None:
        """
        Find a matching required test name, handling various test name format mismatches.

        Handles ALL combinations of:
        1. Exact match
        2. Parametrized tests: test_foo[param] ↔ test_foo
        3. Path differences: test/path/file.py::test_foo ↔ path/file.py::test_foo ↔ test_foo
        4. JS/TS pipe format with path prefix and describe block mismatches
        5. Case-insensitive matching

        Matching priority:
        1. Exact match (return immediately)
        2. Path + func match (with or without params)
        3. Func-only match (when required has no path)
        """
        # === 1. Exact match ===
        if parser_test_name in required_tests:
            return parser_test_name

        # === 2. JS/TS pipe format (handle separately) ===
        if " | " in parser_test_name:
            parser_path, parser_desc = parser_test_name.split(" | ", 1)
            for req_test in required_tests:
                if " | " in req_test:
                    req_path, req_desc = req_test.split(" | ", 1)
                    path_matches = (
                        req_path == parser_path
                        or req_path.endswith(parser_path)
                        or parser_path.endswith(req_path)
                    )
                    desc_matches = (
                        req_desc == parser_desc
                        or req_desc.endswith(" | " + parser_desc)
                        or parser_desc.endswith(" | " + req_desc)
                    )
                    if path_matches and desc_matches:
                        return req_test
                else:
                    if (
                        req_test == parser_path
                        or req_test.endswith(parser_path)
                        or parser_path.endswith(req_test)
                    ):
                        return req_test
            return None

        # === 3. Pytest format (path::func or just func, with or without params) ===
        parser_path, parser_func_params, parser_func_base = _extract_pytest_components(
            parser_test_name
        )
        parser_func_base_lower = parser_func_base.lower()
        # Two-pass matching: prefer path matches, fallback to func-only
        fallback_match = None
        for req_test in required_tests:
            # Skip JS/TS format
            if " | " in req_test:
                continue
            req_path, req_func_params, req_func_base = _extract_pytest_components(req_test)
            req_func_base_lower = req_func_base.lower()
            # Function names must match (case-insensitive)
            if parser_func_base_lower != req_func_base_lower:
                continue
            # Check parameter compatibility
            params_compatible = (
                parser_func_params == req_func_params  # Exact match
                or req_func_params == req_func_base  # Required has no params
                or parser_func_params == parser_func_base  # Parser has no params
            )
            if not params_compatible:
                continue
            # If both have paths, prefer path matches
            if parser_path is not None and req_path is not None:
                if _paths_match(parser_path, req_path):
                    return req_test  # Best match: paths align
                # Paths don't match - save as fallback (func name matched)
                if fallback_match is None:
                    fallback_match = req_test
            else:
                # At least one has no path - this is a valid match
                return req_test

        # If no path match found, use func-name-only fallback (backward compat)
        return fallback_match

    # Parse the tests array from parser.py output
    tests = data.get("tests", [])
    for test in tests:
        test_name = test.get("name", "")
        status_str = test.get("status", "").upper()
        if not test_name:
            continue

        # Find matching required test (exact or suffix match)
        matched_name = test_name
        if required_tests:
            matched_name = _find_matching_required_test(test_name)
            if matched_name is None:
                continue

        # Map parser.py status to swebench TestStatus
        if status_str == "PASSED":
            test_status_map[matched_name] = TestStatus.PASSED.value
        elif status_str == "FAILED":
            test_status_map[matched_name] = TestStatus.FAILED.value
        elif status_str == "SKIPPED":
            test_status_map[matched_name] = TestStatus.SKIPPED.value
        elif status_str == "ERROR":
            test_status_map[matched_name] = TestStatus.ERROR.value
        else:
            # Unknown status, treat as error
            test_status_map[matched_name] = TestStatus.ERROR.value

    # === Handle bare test names that have parametrized variants ===
    # If FAIL_TO_PASS contains both "path::test_foo" (bare) and "path::test_foo[param]" (parametrized),
    # and parametrized variants passed, mark the bare name as passed too.
    # This handles the case where pytest only reports parametrized variants in output.
    # Also handles path differences (e.g., required has "test_foo" but status_map has "path::test_foo[param]")
    if required_tests:
        for req_test in required_tests:
            # Skip if already in test_status_map
            if req_test in test_status_map:
                continue
            # Skip JS/TS format (handled separately)
            if " | " in req_test:
                continue
            # Check if this is a bare name (no parameters)
            if "[" in req_test:
                continue
            # Extract components from the required test
            req_path, _, req_func_base = _extract_pytest_components(req_test)
            req_func_base_lower = req_func_base.lower()
            # Find all parametrized variants of this test in test_status_map
            # Match by function name, allowing different paths
            parametrized_variants = []
            for status_test in test_status_map.keys():
                if "[" not in status_test:
                    continue  # Only look at parametrized tests
                status_path, _, status_func_base = _extract_pytest_components(status_test)
                # Function base names must match
                if status_func_base.lower() != req_func_base_lower:
                    continue
                # If required has a path, status path must match (allowing different roots)
                if req_path is not None:
                    if status_path is None or not _paths_match(req_path, status_path):
                        continue
                # This is a parametrized variant of the required test
                parametrized_variants.append(status_test)
            # If we found parametrized variants and ALL of them passed, mark bare name as passed
            if parametrized_variants:
                all_passed = all(
                    test_status_map.get(t) == TestStatus.PASSED.value for t in parametrized_variants
                )
                if all_passed:
                    test_status_map[req_test] = TestStatus.PASSED.value

    return test_status_map


# =============================================================================
# Type Definitions
# =============================================================================

# All supported log parser types - maps to swebench parser functions
LogParserType = Literal[
    "pytest",  # Python pytest (most common)
    "jest",  # JavaScript Jest
    "vitest",  # JavaScript Vitest
    "karma",  # JavaScript Karma
    "gotest",  # Go testing
    "maven",  # Java Maven
    "gradle",  # Java Gradle
    "cargo",  # Rust Cargo
    "minitest",  # Ruby Minitest/RSpec
    "sweap_json",  # SWEAP: JSON output from instance-specific parser.py
]

# Map parser type names to actual parser functions
LOG_PARSER_MAP: dict[LogParserType, Callable] = {
    "pytest": parse_log_pytest,
    "jest": parse_log_jest,
    "vitest": parse_log_vitest,
    "karma": parse_log_karma,
    "gotest": parse_log_gotest,
    "maven": parse_log_maven,
    "gradle": parse_log_gradle_custom,
    "cargo": parse_log_cargo,
    "minitest": parse_log_minitest,
    "sweap_json": parse_log_sweap_json,
}


class CustomInstallSpecs(TypedDict, total=False):
    """
    Installation specifications for a custom project.

    Required fields:
        test_cmd: Command(s) to run tests.
                  Examples: "pytest -rA", "npm test", "go test ./..."
        install: Command to install your project.
                 Examples: "pip install -e .", "npm install", "go mod download"

    Language/Environment fields:
        python: Python version string (for Python projects using conda env)
        base_image: Custom base Docker image, e.g., "node:18", "golang:1.21"
                    If provided, skips swebench's conda-based env image.
        env_setup: List of commands to set up environment (replaces conda)
                   Use this for non-Python projects or custom setups.

    Optional fields:
        packages: Conda packages to install (Python/conda only)
        pip_packages: List of pip packages to install after conda setup
        pre_install: List of commands to run BEFORE install (e.g., apt-get)
        build: List of build commands (run after install)
        eval_commands: Commands to run at start of evaluation (e.g., exports)
        apt_pkgs: List of apt packages to install
        docker_specs: Dict with conda_version, ubuntu_version overrides

    Examples:
        # Python project (uses conda)
        {"python": "3.11", "test_cmd": "pytest -rA", "install": "pip install -e .",
         "log_parser": "pytest"}

        # Node.js project (custom base image)
        {"base_image": "node:18", "test_cmd": "npm test", "install": "npm install",
         "log_parser": "jest"}

        # Go project
        {"base_image": "golang:1.21", "test_cmd": "go test ./...", "install": "go mod download",
         "log_parser": "gotest"}
    """

    test_cmd: str
    install: str
    log_parser: LogParserType  # parser for test output

    # Language/Environment (pick one approach)
    python: NotRequired[str]  # Python version -> uses conda
    base_image: NotRequired[str]  # Custom base image -> skips conda
    env_setup: NotRequired[list[str]]  # Custom env setup commands

    packages: NotRequired[str]
    pip_packages: NotRequired[list[str]]
    pre_install: NotRequired[list[str]]
    build: NotRequired[list[str]]
    eval_commands: NotRequired[list[str]]
    apt_pkgs: NotRequired[list[str]]
    docker_specs: NotRequired[dict]

    # For pre-configured images (e.g., jefzda): skip install since image is ready
    skip_install: NotRequired[bool]


class SWEBenchMetadata(TypedDict, total=False):
    """
    SWE-bench style test metadata.

    Defines which tests should change status after the fix is applied.
    This is the core of SWE-bench evaluation: tests in FAIL_TO_PASS should
    fail before the fix and pass after; tests in PASS_TO_PASS should pass
    both before and after.
    """

    FAIL_TO_PASS: list[str]  # Tests that should pass after fix (were failing)
    PASS_TO_PASS: list[str]  # Tests that should remain passing


class CustomInstanceMetadata(TypedDict, total=False):
    """
    Metadata for a custom HIL-bench instance (from metadata.json).

    Example metadata.json:
    {
        "instance_id": "myproject__issue-42",
        "repo_name": "/path/to/local/repo",
        "log_parser": "pytest",
        "swe_bench_metadata": {
            "FAIL_TO_PASS": ["tests/test_feature.py::test_new_feature"],
            "PASS_TO_PASS": ["tests/test_existing.py::test_still_works"]
        },
        "test_patch": "diff --git a/tests/test_feature.py ...",
        "test_cmd": "pytest -rA",
        "install_cmd": "pip install -e ."
    }
    """

    instance_id: Required[str]
    repo_name: Required[str]  # Path to local repo
    log_parser: Required[LogParserType]  # Parser for test output (pytest, jest, etc.)
    image_name: str  # Docker image (optional if using specs)

    swe_bench_metadata: Required[SWEBenchMetadata]
    test_cmd: Required[str]  # Test command
    test_patch: str  # Patch adding new tests

    # Custom specs (can be inline or reference)
    language: str  # Language: "py", "js", "go", etc. (default: inferred)
    python_version: str  # Python version (default: 3.11)
    base_image: str  # Custom base image for non-Python
    install_cmd: str  # Install command (default: pip install -e .)
    pip_packages: list[str]  # Additional pip packages
    pre_install: list[str]  # Pre-install commands
    env_setup: list[str]  # Custom environment setup (non-Python)
    packages: str  # Conda packages or "requirements.txt"

    # SWEAP-specific fields
    test_files: list[str]  # List of test files for run_script.sh


class LocalInstance(TypedDict, total=False):
    """
    Instance format for local repo evaluation.

    Unlike SWEbenchInstance, this uses a local_repo_path instead of
    relying on GitHub cloning.
    """

    instance_id: Required[str]  # Unique ID, e.g. "my-project__issue-123"
    repo: Required[str]  # Fake repo name for specs lookup
    version: Required[str]  # Version string for specs lookup
    local_repo_path: Required[str]  # Path to local git repository
    test_patch: Required[str]  # Diff with test changes to apply
    problem_statement: str  # Description of the issue
    FAIL_TO_PASS: str  # JSON list of tests that should pass after fix
    PASS_TO_PASS: str  # JSON list of tests that should stay passing
    test_files: list[str]  # List of test files for SWEAP run_script.sh


class Prediction(TypedDict):
    """A model's prediction (patch) for an instance."""

    instance_id: str
    model_name_or_path: str
    model_patch: str


# =============================================================================
# Result Classes
# =============================================================================


@dataclass
class CustomEvalResult:
    """Result of evaluating a single custom instance."""

    instance_id: str
    resolved: bool
    resolution_status: str  # ResolvedStatus value
    report: dict = field(default_factory=dict)
    patch_applied: bool = False
    error: str | None = None
    log: str = ""


# =============================================================================
# Specs Registration
# =============================================================================


def infer_language_from_specs(specs: CustomInstallSpecs) -> str:
    """
    Infer the language identifier from specs.

    swebench uses language extensions to dispatch to language-specific
    handlers (dockerfiles, script generators, log parsers).

    Priority:
    1. test_cmd (most reliable - "go test", "pytest", "npm test", etc.)
    2. base_image (for custom images)
    3. python version (legacy)
    4. Default to Python

    Returns:
        Language extension: "py", "js", "go", "java", "rb", "rs", "c", "php"
    """
    # 1. Check test_cmd first (most reliable indicator)
    test_cmd = specs.get("test_cmd", "")
    if isinstance(test_cmd, list):
        test_cmd = " ".join(test_cmd)
    test_cmd_lower = test_cmd.lower()

    if "go test" in test_cmd_lower:
        return "go"
    if "pytest" in test_cmd_lower or "py.test" in test_cmd_lower:
        return "py"
    if "jest" in test_cmd_lower or "vitest" in test_cmd_lower or "npm test" in test_cmd_lower:
        return "js"
    if "cargo test" in test_cmd_lower:
        return "rs"
    if "mvn" in test_cmd_lower or "gradle" in test_cmd_lower:
        return "java"
    if "rake" in test_cmd_lower or "rspec" in test_cmd_lower or "minitest" in test_cmd_lower:
        return "rb"

    # 2. Check base_image for hints
    base_image = specs.get("base_image", "")
    if "node" in base_image:
        return "js"
    if "golang" in base_image or "go:" in base_image:
        return "go"
    if "rust" in base_image:
        return "rs"
    if "ruby" in base_image:
        return "rb"
    if "openjdk" in base_image or "java" in base_image:
        return "java"
    if "php" in base_image:
        return "php"

    # 3. If python version is specified, it's Python
    if "python" in specs and "base_image" not in specs:
        return "py"

    # 4. Default to Python (most common, uses common handlers)
    return "py"


def register_custom_specs(
    repo_name: str,
    version: str,
    specs: CustomInstallSpecs,
    language: str | None = None,
) -> None:
    """
    Register custom specs so swebench can find them.

    This injects specs into swebench's global MAP_REPO_VERSION_TO_SPECS
    and MAP_REPO_TO_EXT so that make_test_spec() and other swebench
    functions work correctly.

    Args:
        repo_name: A repo identifier (e.g., "custom/myproject")
        version: A version string (e.g., "1.0")
        specs: CustomInstallSpecs with python, test_cmd, install, etc.
        language: Language extension ("py", "js", "go", etc.)
                  If not provided, inferred from specs.

    Example:
        # Python project
        register_custom_specs("custom/myproject", "1.0", {
            "python": "3.11",
            "test_cmd": "pytest -rA",
            "install": "pip install -e .",
        })

        # Node.js project
        register_custom_specs("custom/frontend", "1.0", {
            "base_image": "node:18",
            "test_cmd": "npm test",
            "install": "npm install",
        }, language="js")
    """
    if repo_name not in MAP_REPO_VERSION_TO_SPECS:
        MAP_REPO_VERSION_TO_SPECS[repo_name] = {}
    MAP_REPO_VERSION_TO_SPECS[repo_name][version] = specs

    # Register language for swebench dispatcher
    if language is None:
        language = infer_language_from_specs(specs)
    MAP_REPO_TO_EXT[repo_name] = language

    # Register log parser for grading based on test command/language
    if repo_name not in MAP_REPO_TO_PARSER:
        parser = _select_log_parser(specs, language)
        if parser:
            MAP_REPO_TO_PARSER[repo_name] = parser


def _ensure_test_cmd_flags(test_cmd: str) -> str:
    """
    Ensure test command has required flags for swebench's log parsers.

    Each log parser expects output in a specific format. This adds the
    necessary flags if they're missing.

    Args:
        test_cmd: The test command from metadata

    Returns:
        Test command with required flags added
    """
    # pytest needs -rA for "PASSED/FAILED testname" format
    if "pytest" in test_cmd and "-rA" not in test_cmd:
        test_cmd = test_cmd.replace("pytest", "pytest -rA", 1)

    # Jest needs --verbose for "✓ test name" format
    if "jest" in test_cmd and "--verbose" not in test_cmd:
        test_cmd = test_cmd + " --verbose"

    # Vitest needs --reporter=verbose for "✓ test name" format
    if "vitest" in test_cmd and "--reporter" not in test_cmd:
        test_cmd = test_cmd + " --reporter=verbose"

    # Go test and Cargo test work with default output, no flags needed

    return test_cmd


def _select_log_parser(specs: CustomInstallSpecs, language: str | None):
    """
    Select the appropriate log parser based on explicit config, test command, or language.

    Priority:
    1. Explicit log_parser field in specs (required for new instances)
    2. Inferred from test_cmd (legacy/fallback)
    3. Inferred from language (legacy/fallback)
    4. Default to pytest

    Returns the parser function.
    """
    # 1. Use explicit log_parser if provided
    if "log_parser" in specs:
        parser_type = specs["log_parser"]
        if parser_type in LOG_PARSER_MAP:
            return LOG_PARSER_MAP[parser_type]
        else:
            raise ValueError(
                f"Unknown log_parser: {parser_type}. Valid options: {list(LOG_PARSER_MAP.keys())}"
            )

    # 2. Infer from test command (legacy support)
    test_cmd = specs.get("test_cmd", "")
    if isinstance(test_cmd, list):
        test_cmd = " ".join(test_cmd)
    test_cmd_lower = test_cmd.lower()

    if "pytest" in test_cmd_lower or "py.test" in test_cmd_lower:
        return parse_log_pytest
    if "jest" in test_cmd_lower:
        return parse_log_jest
    if "vitest" in test_cmd_lower:
        return parse_log_vitest
    if "karma" in test_cmd_lower:
        return parse_log_karma
    if "go test" in test_cmd_lower:
        return parse_log_gotest
    if "mvn" in test_cmd_lower or "maven" in test_cmd_lower:
        return parse_log_maven
    if "gradle" in test_cmd_lower:
        return parse_log_gradle_custom
    if "cargo test" in test_cmd_lower:
        return parse_log_cargo
    if "rspec" in test_cmd_lower or "minitest" in test_cmd_lower or "rake test" in test_cmd_lower:
        return parse_log_minitest

    # 3. Fall back to language-based defaults
    if language in _PYTHON_LANGUAGES:
        return parse_log_pytest
    if language in _JS_TS_LANGUAGES:
        return parse_log_jest
    if language in ("go", "golang"):
        return parse_log_gotest
    if language in ("rs", "rust"):
        return parse_log_cargo
    if language in ("rb", "ruby"):
        return parse_log_minitest

    # 4. Default to pytest (works for many simple cases)
    return parse_log_pytest


def specs_from_metadata(metadata: CustomInstanceMetadata) -> tuple[CustomInstallSpecs, str | None]:
    """
    Create CustomInstallSpecs from metadata.json fields.

    Maps the metadata.json format to swebench's specs format.

    IMPORTANT: If metadata contains an 'image_name' field (e.g., jefzda/sweap-images:...),
    this is used as the base_image to ensure evaluation uses the SAME Docker image
    that the agent used during solving. This prevents environment discrepancies.

    Returns:
        Tuple of (specs, language) where language may be None (to be inferred)
    """
    test_cmd = metadata["test_cmd"]
    test_cmd = _ensure_test_cmd_flags(test_cmd)

    specs: CustomInstallSpecs = {
        "test_cmd": test_cmd,
        "install": metadata.get("install_cmd", "pip install -e ."),
        "log_parser": metadata["log_parser"],
    }

    # See if we can use preconfigured images directly so evaluation uses the SAME image as the agent during solving.
    # We intentionally treat hil-bench-agent:* and hilbench-swe:* identically.
    def _is_hil_bench_preconfigured_image(image: str) -> bool:
        return image.startswith("hil-bench-agent:") or image.startswith("hilbench-swe:")

    if "image_name" in metadata and metadata["image_name"]:
        image_name = metadata["image_name"]
        # Use preconfigured images directly - they have repo at /app with all deps installed
        if image_name and (
            image_name.startswith("jefzda/") or _is_hil_bench_preconfigured_image(image_name)
        ):
            specs["base_image"] = image_name
            specs["skip_install"] = True
            specs["python"] = metadata.get("python_version", "3.11")
        elif "base_image" in metadata:
            specs["base_image"] = metadata["base_image"]
            if "env_setup" in metadata:
                specs["env_setup"] = metadata["env_setup"]
            base_img = metadata["base_image"]
            if base_img.startswith("python:"):
                specs["python"] = base_img.split(":")[1].split("-")[0]
            else:
                specs["python"] = metadata.get("python_version", "3.11")
        else:
            specs["python"] = metadata.get("python_version", "3.11")
    elif "base_image" in metadata:
        specs["base_image"] = metadata["base_image"]
        if "env_setup" in metadata:
            specs["env_setup"] = metadata["env_setup"]
        # Extract python version from base_image if it's a python image (e.g., "python:3.11")
        base_img = metadata["base_image"]
        if base_img.startswith("python:"):
            specs["python"] = base_img.split(":")[1].split("-")[0]
        else:
            specs["python"] = metadata.get("python_version", "3.11")
    else:
        specs["python"] = metadata.get("python_version", "3.11")

    if "pip_packages" in metadata:
        specs["pip_packages"] = metadata["pip_packages"]

    if "pre_install" in metadata:
        specs["pre_install"] = metadata["pre_install"]

    if "packages" in metadata:
        specs["packages"] = metadata["packages"]

    language = metadata.get("language")

    return specs, language


# =============================================================================
# Dockerfile Templates for Local Repos
# =============================================================================

# For Python projects (uses swebench's conda-based env image)
_DOCKERFILE_INSTANCE_LOCAL_PYTHON = r"""FROM --platform={platform} {env_image_name}

# Copy local repo (must be in build context as 'local_repo')
COPY ./local_repo /testbed
RUN chmod -R 777 /testbed

COPY ./setup_repo.sh /root/
RUN sed -i -e 's/\r$//' /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""

# For non-Python projects (uses custom base image, no conda)
_DOCKERFILE_INSTANCE_LOCAL_GENERIC = r"""FROM {base_image}

# Install git (needed for patch application and diffing)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* || true

# Copy local repo
COPY ./local_repo /testbed
RUN chmod -R 777 /testbed

COPY ./setup_repo.sh /root/
RUN sed -i -e 's/\r$//' /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""

# For pre-configured images (like jefzda) where repo is at /app and dependencies are installed, we just copy our modified repo (with setup_patch) to /app, overwriting the original
# Workarounds for jefzda images (same as configs/swe/default.yaml):
# 1. ENTRYPOINT: Clears broken /bin/bash entrypoint, keeps container running for exec
# 2. PIP_INDEX_URL: Overrides pip.conf pointing to non-existent 127.0.0.1:9876
# 3. /testbed symlink: swebench hardcodes DOCKER_WORKDIR="/testbed", so we symlink to /app
# 4. run_script.sh + parser.py: SWEAP instance-specific scripts for test execution and output parsing
_DOCKERFILE_INSTANCE_PRECONFIGURED = r"""FROM {base_image}

# Fix pip config: jefzda images have pip.conf pointing to non-existent 127.0.0.1:9876
ENV PIP_INDEX_URL=https://pypi.org/simple/

# Install patch utility (required by swebench for applying diffs during evaluation)
# Detect package manager and install patch if missing
RUN if ! command -v patch >/dev/null 2>&1; then \
        if command -v apk >/dev/null 2>&1; then \
            apk add --no-cache patch; \
        elif command -v apt-get >/dev/null 2>&1; then \
            apt-get update && apt-get install -y --no-install-recommends patch && rm -rf /var/lib/apt/lists/*; \
        elif command -v yum >/dev/null 2>&1; then \
            yum install -y patch && yum clean all; \
        fi; \
    fi

# Copy local repo to /app (jefzda images have repo at /app, not /testbed). This overwrites the existing repo with our version (which has setup_patch applied)
COPY ./local_repo /app
RUN chmod -R 777 /app

# Copy SWEAP scripts for test execution to /root/ (NOT /app/)
# CRITICAL: These MUST be outside /app so agent cannot see them during problem-solving
COPY ./run_script.sh /root/run_script.sh
COPY ./parser.py /root/parser.py
RUN chmod +x /root/run_script.sh || true

# Create /testbed symlink: swebench hardcodes DOCKER_WORKDIR="/testbed" in run_evaluation.py
# This symlink lets swebench's "cd /testbed" work while repo actually lives at /app
RUN ln -s /app /testbed

COPY ./setup_repo.sh /root/
RUN sed -i -e 's/\r$//' /root/setup_repo.sh
RUN /bin/sh /root/setup_repo.sh

WORKDIR /app/

# Fix entrypoint: jefzda images have /bin/bash as entrypoint but bash is at /usr/bin/bash
# swebench expects to be able to exec commands in the running container
ENTRYPOINT ["/bin/sh", "-c", "sleep infinity"]
"""


def is_python_specs(specs: CustomInstallSpecs) -> bool:
    """Check if specs are for a Python project (uses conda)."""
    # If 'python' version is specified and no custom base_image, it's Python
    return "python" in specs and "base_image" not in specs


def make_repo_script_list_local(
    specs: CustomInstallSpecs,
    repo: str,
    repo_directory: str,
    base_commit: str | None,
    env_name: str,
) -> list[str]:
    """
    Create setup commands for a local repo (no git clone).

    Handles:
    - Pre-configured images (skip_install=True): Only configures git for diffing
    - Python projects: Activates conda environment and runs install
    - Non-Python projects: Uses custom env_setup or just runs install
    """
    setup_commands = [
        f"chmod -R 777 {repo_directory}",
        f"cd {repo_directory}",
    ]
    skip_install = specs.get("skip_install", False)
    if not skip_install:
        if is_python_specs(specs):
            # Python project: activate conda environment
            setup_commands.extend(
                [
                    "source /opt/miniconda3/bin/activate",
                    f"conda activate {env_name}",
                    'echo "Current environment: $CONDA_DEFAULT_ENV"',
                ]
            )
        elif "env_setup" in specs:
            # Custom environment setup commands
            setup_commands.extend(specs["env_setup"])

        if "pre_install" in specs:
            for cmd in specs["pre_install"]:
                setup_commands.append(cmd)

        if "install" in specs:
            install_cmd = specs["install"]
            if isinstance(install_cmd, str):
                setup_commands.append(install_cmd)
            else:
                setup_commands.extend(install_cmd)

        if "build" in specs:
            setup_commands.extend(specs["build"])

    # Clean git state for proper diffing (works for any language)
    setup_commands.extend(
        [
            "git config --global user.email setup@swebench.config",
            "git config --global user.name SWE-bench",
            "git commit --allow-empty -am SWE-bench",
        ]
    )

    return setup_commands


# =============================================================================
# Docker Image Building for Local Repos
# =============================================================================


def build_instance_image_local(
    test_spec: TestSpec,
    local_repo_path: str | Path,
    client: docker.DockerClient,
    force_rebuild: bool = False,
    specs: CustomInstallSpecs | None = None,
) -> str:
    """
    Build an instance image using a local repository.

    Instead of cloning from GitHub, this copies the local repo into
    the Docker build context and uses COPY in the Dockerfile.

    Supports both:
    - Python projects (uses swebench's conda-based env image)
    - Non-Python projects (uses custom base_image from specs)

    Args:
        test_spec: TestSpec with repo/version info
        local_repo_path: Path to local git repository
        client: Docker client
        force_rebuild: Force rebuild even if image exists
        specs: Optional specs dict (if not provided, looks up from MAP_REPO_VERSION_TO_SPECS)

    Returns:
        The image name/tag
    """
    local_repo_path = Path(local_repo_path).expanduser()
    if not local_repo_path.exists():
        raise ValueError(f"Local repo path does not exist: {local_repo_path}")

    image_name = test_spec.instance_image_key
    source_repo_id = str(local_repo_path.resolve())

    # Marker file to track which source repo was used for the last build.
    lock_dir = Path(f"/tmp/hil_bench_image_locks_{os.getuid()}")
    lock_dir.mkdir(parents=True, exist_ok=True)
    marker_file = lock_dir / f"{image_name.replace(':', '_').replace('/', '_')}.built"

    # PRIORITY PATH: If base_image is hil-bench-agent:* or hilbench-swe:*, use it directly
    # instead of relying on potentially stale cached local/sweb.eval.* images.
    # These images are built by _build_agent_image() in hil_bench_agent.py with the
    # correct file locations (/root/parser.py, /root/run_script.sh).
    def _is_hil_bench_preconfigured_image(image: str) -> bool:
        return image.startswith("hil-bench-agent:") or image.startswith("hilbench-swe:")

    if specs is not None:
        base_image = specs.get("base_image", "")
        if _is_hil_bench_preconfigured_image(base_image):
            try:
                # Check if the preconfigured image exists
                hil_bench_img = client.images.get(base_image)
                # Check if target image is already tagged from this preconfigured image
                try:
                    existing_img = client.images.get(image_name)
                    if existing_img.id == hil_bench_img.id:
                        print(f"ℹ️  Image {image_name} already tagged from {base_image}")
                        return image_name
                except docker.errors.ImageNotFound:
                    pass
                # Tag the preconfigured image with the expected image_name
                hil_bench_img.tag(image_name)
                print(f"🏷️  Tagged {base_image} as {image_name} (priority path)")
                marker_file.write_text(source_repo_id)
                return image_name
            except docker.errors.ImageNotFound:
                raise RuntimeError(
                    f"Preconfigured image not found but it should already have been built: {base_image}. Check the build log for errors"
                )

    # FAST PATH: Check if image already exists from same source BEFORE acquiring lock.
    # This avoids waiting for a lock when another process already built the image.
    try:
        client.images.get(image_name)
        # Image exists - check if it was built from the same source
        if marker_file.exists():
            saved_source_id = marker_file.read_text().strip()
            if saved_source_id == source_repo_id:
                print(f"ℹ️  Using existing image (same source, no lock needed): {image_name}")
                return image_name
        # Image exists but no marker or different source
        if not force_rebuild:
            print(f"ℹ️  Using existing image: {image_name}")
            return image_name
    except docker.errors.ImageNotFound:
        pass

    # Need to build - acquire lock to prevent concurrent builds
    # Use polling with short timeouts to check if another process finished building
    instance_lock_file = lock_dir / f"{image_name.replace(':', '_').replace('/', '_')}.lock"
    pid = os.getpid()
    lock = FileLock(instance_lock_file, timeout=30)  # Short timeout for polling

    print(f"🔒 [{pid}] Acquiring lock for instance image: {image_name}...")
    max_wait_time = 1800  # 30 minutes total
    waited_time = 0
    while waited_time < max_wait_time:
        try:
            lock.acquire(timeout=30)  # Try to acquire with 30s timeout
            break  # Got the lock
        except Timeout:
            # Couldn't get lock - check if image was built while waiting
            waited_time += 30
            try:
                client.images.get(image_name)
                if marker_file.exists():
                    saved_source_id = marker_file.read_text().strip()
                    if saved_source_id == source_repo_id:
                        print(
                            f"ℹ️  [{pid}] Image built by another process while waiting ({waited_time}s): {image_name}"
                        )
                        return image_name
            except docker.errors.ImageNotFound:
                pass
            print(f"⏳ [{pid}] Still waiting for lock ({waited_time}s elapsed)...")
    else:
        raise TimeoutError(f"Timeout waiting for lock after {max_wait_time}s: {instance_lock_file}")

    try:  # Use try/finally to ensure lock is released
        # Double-check if image was built while we waited for the lock
        # Check both the Docker image AND the marker file
        try:
            client.images.get(image_name)
            # Image exists - check if it was built from the same source repo
            if marker_file.exists():
                saved_source_id = marker_file.read_text().strip()
                if saved_source_id == source_repo_id:
                    print(
                        f"ℹ️  [{pid}] Image already built from same source ({source_repo_id}): {image_name}"
                    )
                    return image_name
                elif not force_rebuild:
                    # Different source but not forcing rebuild - use existing image
                    print(
                        f"ℹ️  [{pid}] Reusing existing image (built from different source): {image_name}"
                    )
                    return image_name
                else:
                    # Different source AND force_rebuild - will rebuild below
                    print(
                        f"ℹ️  [{pid}] Image exists but from different source, will rebuild: {image_name}"
                    )
            elif not force_rebuild:
                # No marker but image exists - use it
                print(f"ℹ️  [{pid}] Using existing image (no source marker): {image_name}")
                return image_name
        except docker.errors.ImageNotFound:
            pass

        # Now we have exclusive access to build this image
        if force_rebuild:
            # Remove existing image to ensure clean state
            try:
                client.images.remove(image_name, force=True)
                print(f"🗑️  [{pid}] Removed existing image: {image_name}")
            except docker.errors.ImageNotFound:
                print(f"ℹ️  [{pid}] Image {image_name} not found (nothing to remove)")
            except Exception as e:
                print(f"⚠️  Failed to remove image {image_name}: {e}")

        # Get specs (required for setup script generation)
        if specs is None:
            specs = MAP_REPO_VERSION_TO_SPECS[test_spec.repo][test_spec.version]
        assert specs is not None, "specs must be provided or available in MAP_REPO_VERSION_TO_SPECS"

        # Use the preconfigured hil-bench-agent:*/hilbench-swe:* image directly.
        base_image = specs.get("base_image", "")
        if _is_hil_bench_preconfigured_image(base_image):
            print(
                f"✅ [{pid}] Using preconfigured image directly (no rebuild needed): {base_image}"
            )
            # Tag the preconfigured image with the expected image_name so run_instance finds it
            try:
                img = client.images.get(base_image)
                img.tag(image_name)
                print(f"🏷️  [{pid}] Tagged {base_image} as {image_name}")
            except docker.errors.ImageNotFound:
                # These images are built by hil_bench_agent.py BEFORE validation/eval.
                # If missing, something went wrong upstream - fail immediately with clear error.
                raise RuntimeError(
                    f"Preconfigured image not found: {base_image}. "
                    "This image should have been built by hil_bench_agent.py before validation. "
                    "Search logs for '[Sandbox] Building agent Docker image' or "
                    "'[Sandbox] Agent image build' to find the build output."
                )
            except Exception as e:
                # Other errors (e.g., tagging failed due to permissions) - also fail clearly
                raise RuntimeError(
                    f"Failed to use agent image {base_image}: {e}. "
                    "Check Docker permissions and image state."
                )
            else:
                # Mark this image as built from the current source
                marker_file.write_text(source_repo_id)
                return image_name

        # Set up build directory
        build_dir = INSTANCE_IMAGE_BUILD_DIR / test_spec.instance_image_key.replace(":", "__")
        build_dir.mkdir(parents=True, exist_ok=True)

        # Copy local repo to build context
        local_repo_dest = build_dir / "local_repo"
        if local_repo_dest.exists():
            print(f"🗑️  [{pid}] Removing old local_repo: {local_repo_dest}")
            # Use ignore_errors=True to handle broken symlinks gracefully
            # (symlinks pointing to non-existent files will cause rmtree to fail otherwise)
            shutil.rmtree(local_repo_dest, ignore_errors=True)
            # If directory still exists after ignore_errors, try a more aggressive removal
            if local_repo_dest.exists():
                import subprocess

                subprocess.run(["rm", "-rf", str(local_repo_dest)], check=False)
        print(f"📦 [{pid}] Copying local repo from {local_repo_path} to {local_repo_dest}")
        # Use symlinks=True to preserve symlinks as symlinks rather than resolving them
        # (broken symlinks will fail if we try to resolve them)
        shutil.copytree(local_repo_path, local_repo_dest, symlinks=True)

        # Remove broken symlinks - Docker's tar process fails on them
        _remove_broken_symlinks(local_repo_dest)

        # Determine repo directory based on image type
        # Pre-configured images (jefzda) have repo at /app, others use /testbed
        is_preconfigured = specs.get("skip_install", False)
        repo_directory = "/app" if is_preconfigured else "/testbed"

        setup_commands = make_repo_script_list_local(
            specs, test_spec.repo, repo_directory, None, "testbed"
        )
        # Use sh for preconfigured images (jefzda might not have bash at expected path)
        shell_shebang = "#!/bin/sh" if is_preconfigured else "#!/bin/bash"
        setup_script = "\n".join([shell_shebang, "set -eux"] + setup_commands) + "\n"

        # Copy SWEAP scripts (run_script.sh and parser.py) to build context
        task_dir = local_repo_path.parent

        # Copy run_script.sh
        run_script_path = task_dir / "run_script.sh"
        run_script_dest = build_dir / "run_script.sh"
        if run_script_path.exists():
            run_script_dest.write_text(run_script_path.read_text())
            print(f"📦 [{pid}] Including run_script.sh in Docker image")
        else:
            # Create placeholder so Dockerfile COPY doesn't fail
            run_script_dest.write_text(
                "#!/bin/sh\necho 'ERROR: run_script.sh not provided'\nexit 1\n"
            )

        # Copy parser.py (instance-specific output parser)
        parser_path = task_dir / "parser.py"
        parser_dest = build_dir / "parser.py"
        if parser_path.exists():
            parser_dest.write_text(parser_path.read_text())
            print(f"📦 [{pid}] Including parser.py in Docker image")
        else:
            # Create placeholder that outputs empty JSON so Dockerfile COPY doesn't fail
            parser_dest.write_text(
                '#!/usr/bin/env python3\nimport json,sys\njson.dump({"tests":[]},open(sys.argv[3],"w"))\n'
            )

        # Choose Dockerfile based on project type
        if is_preconfigured:
            # Pre-configured image (e.g., jefzda): just copy repo to /app and configure git. Image already has all dependencies installed
            base_image = specs.get("base_image", "ubuntu:22.04")
            # Safety check: preconfigured images should have been handled above and returned early.
            # If we reach here with one, something went wrong - fail loudly.
            if _is_hil_bench_preconfigured_image(base_image):
                raise RuntimeError(
                    f"BUG: Reached Dockerfile build path with preconfigured image: {base_image}. "
                    "This should have been handled in the priority path above. "
                    "Check that the preconfigured image exists and was built correctly."
                )
            dockerfile = _DOCKERFILE_INSTANCE_PRECONFIGURED.format(
                base_image=base_image,
            )
            platform = "linux/amd64"
            print(f"📦 [{pid}] Using pre-configured image: {base_image}")
        elif is_python_specs(specs):
            # Python project: use swebench's env image with conda
            # First ensure the env image exists (builds base + env images if needed)
            #
            # Use file-based locking to prevent race conditions when multiple workers
            # try to build the same base/env image simultaneously. We lock on BOTH:
            # 1. Base image (e.g., sweb.base.py.x86_64) - shared across many instances
            # 2. Env image (e.g., sweb.env.py.x86_64.abc123) - specific to repo/version
            #
            # Different images can still build in parallel; we only serialize builds
            # of the same image to prevent the "Dockerfile empty" race condition.
            #
            # Use user-specific lock directory to avoid permission conflicts between users
            # (reuse the same lock_dir we created above)

            env_image_key = test_spec.env_image_key
            # Base image name follows swebench pattern: sweb.base.{lang}.{platform}:latest
            base_image_key = f"sweb.base.py.{test_spec.platform}:latest"

            env_lock_file = lock_dir / f"{env_image_key.replace(':', '_').replace('/', '_')}.lock"
            base_lock_file = lock_dir / f"{base_image_key.replace(':', '_').replace('/', '_')}.lock"

            # Check if env image already exists (fast path, no lock needed)
            env_image_exists = False
            try:
                client.images.get(env_image_key)
                env_image_exists = True
                print(f"ℹ️  Environment image already exists: {env_image_key}")
            except docker.errors.ImageNotFound:
                pass

            if not env_image_exists or force_rebuild:
                print(f"🔧 Building environment image for {test_spec.instance_id}...")

                # Lock on base image first (coarser lock), then env image
                # This ensures only one worker builds the base image at a time
                print(f"🔒 Acquiring locks for {base_image_key} and {env_image_key}...")

                with FileLock(base_lock_file, timeout=1800):  # 30 min timeout for long builds
                    with FileLock(env_lock_file, timeout=1800):
                        # Double-check if image was built while we waited for the lock
                        try:
                            client.images.get(env_image_key)
                            print(
                                f"ℹ️  Environment image was built by another worker: {env_image_key}"
                            )
                        except docker.errors.ImageNotFound:
                            # Image still doesn't exist, we need to build it
                            print(f"🔨 Building environment image: {env_image_key}")
                            _, env_failed = build_env_images(
                                client=client,
                                dataset=[test_spec],
                                force_rebuild=force_rebuild,
                            )
                            if env_failed:
                                raise RuntimeError(
                                    f"Failed to build environment image: {env_failed}"
                                )

            dockerfile = _DOCKERFILE_INSTANCE_LOCAL_PYTHON.format(
                platform=test_spec.platform,
                env_image_name=test_spec.env_image_key,
            )
            platform = test_spec.platform
        else:
            # Non-Python: use custom base image
            base_image = specs.get("base_image", "ubuntu:22.04")
            # Safety check: preconfigured images should have been handled above and returned early.
            if _is_hil_bench_preconfigured_image(base_image):
                raise RuntimeError(
                    f"BUG: Reached Dockerfile build path with preconfigured image: {base_image}. "
                    "This should have been handled in the priority path above. "
                    "Check that the preconfigured image exists and was built correctly."
                )
            dockerfile = _DOCKERFILE_INSTANCE_LOCAL_GENERIC.format(
                base_image=base_image,
            )
            platform = "linux/amd64"

        build_image(
            image_name=image_name,
            setup_scripts={"setup_repo.sh": setup_script},
            dockerfile=dockerfile,
            platform=platform,
            client=client,
            build_dir=build_dir,
            nocache=force_rebuild,
        )

        # Write marker file with source repo ID (for cross-process tracking)
        marker_file.write_text(source_repo_id)
        print(f"✅ [{pid}] Built image from {source_repo_id}: {image_name}")

        return image_name
    finally:
        lock.release()


# =============================================================================
# Evaluation Functions
# =============================================================================


def get_repo_head_commit(repo_path: str | Path) -> str:
    """Get the current HEAD commit hash from a git repository."""
    import subprocess

    repo_path = str(Path(repo_path).expanduser().resolve())
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"Failed to get HEAD commit: {result.stderr}")
    return result.stdout.strip()


def run_local_instance(
    instance: LocalInstance,
    prediction: Prediction,
    run_id: str,
    client: docker.DockerClient | None = None,
    timeout: int = 1800,
    force_rebuild: bool = False,
    run_script_content_override: str | None = None,
    base_commit_override: str | None = None,
) -> dict[str, Any]:
    """
    Run evaluation on a single local instance using swebench infrastructure.

    This builds a Docker image with the local repo copied in, then uses
    swebench's run_instance() for the actual evaluation.

    Uses swebench's:
    - make_test_spec() for proper eval script generation (language-aware)
    - run_instance() for test execution
    - grading infrastructure for result evaluation

    Args:
        instance: LocalInstance with local_repo_path
        prediction: Prediction with model_patch
        run_id: Unique run identifier
        client: Docker client (created if not provided)
        timeout: Timeout in seconds
        force_rebuild: Force rebuild of instance image

    Returns:
        Dict with 'completed' and 'resolved' keys
    """
    if client is None:
        client = docker.from_env(timeout=300)  # longer timeout in case daemon is slow

    local_repo_path = Path(instance["local_repo_path"]).expanduser()
    specs = MAP_REPO_VERSION_TO_SPECS[instance["repo"]][instance["version"]]
    base_image = str(specs.get("base_image", "") or "")
    use_hilbench_swe_image_path = _is_hilbench_swe_image(base_image)
    if use_hilbench_swe_image_path:
        # For hilbench-swe images, /app is already prepared in-image.
        base_commit = base_commit_override or "HEAD"
        print(
            f"ℹ️  [{instance['instance_id']}] image-first eval for {base_image}; "
            f"skipping host git rev-parse, base_commit={base_commit}"
        )
    else:
        # Legacy path for non-hilbench-swe image families.
        base_commit = get_repo_head_commit(local_repo_path)

    # Create a SWEbenchInstance-like dict for make_test_spec
    # make_test_spec will use this to generate proper eval scripts
    mock_instance = {
        "instance_id": instance["instance_id"],
        "repo": instance["repo"],
        "version": instance["version"],
        "base_commit": base_commit,
        "test_patch": instance["test_patch"],
        "problem_statement": instance.get("problem_statement", ""),
        "hints_text": "",
        "FAIL_TO_PASS": instance["FAIL_TO_PASS"],
        "PASS_TO_PASS": instance.get("PASS_TO_PASS", "[]"),
    }

    # Create test spec using swebench's make_test_spec
    # This generates the proper eval_script based on language (py, js, etc.)
    test_spec = make_test_spec(mock_instance, namespace=None)  # type: ignore

    # Augment test_spec to ensure tests from FAIL_TO_PASS are included in the test run.
    # By default, swebench only runs tests from files modified in test_patch.
    # This ensures all required tests are run even if they're in different files.
    fail_to_pass_str = instance.get("FAIL_TO_PASS", "[]")
    pass_to_pass_str = instance.get("PASS_TO_PASS", "[]")
    fail_to_pass = (
        json.loads(fail_to_pass_str) if isinstance(fail_to_pass_str, str) else fail_to_pass_str
    )
    pass_to_pass = (
        json.loads(pass_to_pass_str) if isinstance(pass_to_pass_str, str) else pass_to_pass_str
    )
    test_files = instance.get("test_files")
    # Read run_script.sh content for ansible-specific argument handling.
    if run_script_content_override is not None:
        run_script_content = run_script_content_override
    else:
        run_script_path = local_repo_path.parent / "run_script.sh"
        run_script_content = run_script_path.read_text() if run_script_path.exists() else None
    test_spec = augment_test_spec_with_required_tests(
        test_spec,
        fail_to_pass,
        pass_to_pass,
        test_files=test_files,
        run_script_content=run_script_content,
    )

    # IMPORTANT: Mark the test_spec as "remote" so swebench's run_instance() skips
    # its build_instance_image() call (which would fail looking for env images).
    #
    # is_remote_image is a property that returns `self.namespace is not None`,
    # so we set namespace to a dummy value to make it return True.
    # This causes build_container() to skip build_instance_image() and just
    # verify the image exists (which it does, since we build it below).
    #
    # We set this BEFORE building so instance_image_key is consistent.
    # We need to use object.__setattr__ because TestSpec is a frozen dataclass.
    object.__setattr__(test_spec, "namespace", "local")

    if use_hilbench_swe_image_path:
        # For hilbench-swe, do NOT copy/build from host repo. Just tag the prebuilt
        # image to swebench's expected instance image key.
        try:
            prebuilt_img = client.images.get(base_image)
        except docker.errors.ImageNotFound:
            raise RuntimeError(
                f"hilbench-swe image not found for evaluation: {base_image}. "
                "Build/prebuild this image before running pass@1."
            )
        prebuilt_img.tag(test_spec.instance_image_key)
        print(
            f"🏷️  [{instance['instance_id']}] tagged {base_image} as {test_spec.instance_image_key}"
        )
    else:
        # Build the instance image with local repo (legacy path)
        build_instance_image_local(
            test_spec,
            instance["local_repo_path"],
            client,
            force_rebuild=force_rebuild,
            specs=specs,
        )

    # IMPORTANT: force_rebuild=False here because we already built the image
    # correctly in build_instance_image_local. If we pass True, swebench will
    # rebuild using its standard method (git clone from GitHub) which breaks
    # local custom instances.
    result = run_instance(
        test_spec=test_spec,
        pred=prediction,  # type: ignore
        rm_image=False,
        force_rebuild=False,
        client=client,
        run_id=run_id,
        timeout=timeout,
    )

    return result


def run_custom_evaluation(
    instance_id: str,
    local_repo_path: str,
    specs: CustomInstallSpecs,
    test_patch: str,
    model_patch: str,
    fail_to_pass_tests: list[str],
    pass_to_pass_tests: list[str] | None = None,
    run_id: str = "custom-eval",
    timeout: int = 1800,
    force_rebuild: bool = False,
    model_name: str = "custom-model",
    language: str | None = None,
    test_files: list[str] | None = None,
    run_script_content_override: str | None = None,
    base_commit_override: str | None = None,
) -> dict[str, Any]:
    """
    Run evaluation on a fully custom local repository with custom specs.

    This is the main entry point for evaluating a model's patch on
    a completely custom codebase (not from SWE-bench).

    Uses swebench infrastructure for:
    - Test spec generation (language-aware eval scripts)
    - Test execution (run_instance)
    - Grading (get_eval_report)

    Args:
        instance_id: Unique identifier (e.g., "myproject__issue-42")
        local_repo_path: Path to your local git repository
        specs: CustomInstallSpecs with python version, test command, etc.
        test_patch: Diff that adds tests which verify the fix
        model_patch: Diff that the model generated as a fix
        fail_to_pass_tests: List of test names that should pass after fix
        pass_to_pass_tests: List of tests that should remain passing
        run_id: Unique identifier for this evaluation run
        timeout: Timeout in seconds
        force_rebuild: Force rebuild Docker images
        model_name: Name/identifier for the model
        language: Language extension ("py", "js", etc.) - inferred if not provided
        test_files: List of test files for SWEAP run_script.sh format

    Returns:
        Dict with 'completed' and 'resolved' keys
    """
    # Generate a repo name from instance_id
    repo_name = instance_id.rsplit("__", 1)[0].replace("__", "/")
    if "/" not in repo_name:
        repo_name = f"custom/{repo_name}"
    version = "1.0"

    # Register the custom specs with swebench
    register_custom_specs(repo_name, version, specs, language=language)

    # Create the instance
    instance: LocalInstance = {
        "instance_id": instance_id,
        "repo": repo_name,
        "version": version,
        "local_repo_path": local_repo_path,
        "test_patch": test_patch,
        "problem_statement": "",
        "FAIL_TO_PASS": json.dumps(fail_to_pass_tests),
        "PASS_TO_PASS": json.dumps(pass_to_pass_tests or []),
    }
    if test_files:
        instance["test_files"] = test_files

    # Create the prediction
    prediction: Prediction = {
        "instance_id": instance_id,
        "model_name_or_path": model_name,
        "model_patch": model_patch,
    }

    return run_local_instance(
        instance=instance,
        prediction=prediction,
        run_id=run_id,
        timeout=timeout,
        force_rebuild=force_rebuild,
        run_script_content_override=run_script_content_override,
        base_commit_override=base_commit_override,
    )


# =============================================================================
# Metadata-based Evaluation (for tasks/*/metadata.json)
# =============================================================================


def load_custom_instance_metadata(task_dir: Path) -> CustomInstanceMetadata | None:
    """Load metadata.json from a task directory."""
    metadata_file = task_dir / "metadata.json"
    if not metadata_file.exists():
        return None
    return json.loads(metadata_file.read_text())


def evaluate_from_metadata(
    metadata: CustomInstanceMetadata,
    task_dir: Path,
    model_patch: str,
    run_id: str = "custom-eval",
    timeout: int = 1800,
    force_rebuild: bool = False,
    model_name: str = "custom-model",
) -> dict[str, Any]:
    """
    Evaluate an instance using metadata.json configuration.

    This is the bridge between the metadata.json format and the
    swebench-based evaluation.

    Args:
        metadata: Loaded metadata.json contents
        task_dir: Directory containing the task
        model_patch: The model's predicted fix (diff)
        run_id: Unique run identifier
        timeout: Timeout in seconds
        force_rebuild: Force rebuild Docker images
        model_name: Name/identifier for the model

    Returns:
        Dict with 'completed' and 'resolved' keys
    """
    swe_metadata = metadata.get("swe_bench_metadata", {})

    # Create specs from metadata
    specs, language = specs_from_metadata(metadata)

    # Get repo path (resolve relative paths)
    # Check for "app" directory first (for jefzda images), fall back to "repo"
    default_repo_path = task_dir / "app"
    if not default_repo_path.exists():
        default_repo_path = task_dir / "repo"
    repo_path = metadata.get("repo_name", str(default_repo_path))
    if repo_path.startswith("./"):
        repo_path = str(task_dir / repo_path[2:])
    elif repo_path == "app":  # used by hil_bench_agent.py to indicate that repo is at task_dir/app
        repo_path = str(task_dir / "app")

    image_name = str(metadata.get("image_name", "") or "")
    run_script_content_override = None
    base_commit_override = None
    if _is_hilbench_swe_image(image_name):
        run_script_path = task_dir / "run_script.sh"
        if run_script_path.exists():
            run_script_content_override = run_script_path.read_text()
        # The prebuilt hilbench-swe image already encodes the prepared repo state.
        base_commit_override = "HEAD"
        # The actual repo lives inside the Docker image, not on disk.
        # Override repo_path to task_dir (which exists) so run_local_instance's
        # existence check passes without needing a local checkout.
        repo_path = str(task_dir)

    return run_custom_evaluation(
        instance_id=metadata.get("instance_id", task_dir.name),
        local_repo_path=repo_path,
        specs=specs,
        test_patch=metadata.get("test_patch", ""),
        model_patch=model_patch,
        fail_to_pass_tests=swe_metadata.get("FAIL_TO_PASS", []),
        pass_to_pass_tests=swe_metadata.get("PASS_TO_PASS", []),
        run_id=run_id,
        timeout=timeout,
        force_rebuild=force_rebuild,
        model_name=model_name,
        language=language,
        test_files=metadata.get("test_files"),
        run_script_content_override=run_script_content_override,
        base_commit_override=base_commit_override,
    )


def _evaluate_single_instance(
    instance_id: str,
    pred_data: Mapping[str, Any],
    tasks_dir: Path,
    run_id: str,
    timeout: int,
    force_rebuild: bool,
    rebuilt_images: set[str] | None = None,
) -> tuple[str, dict, bool, bool]:
    """
    Evaluate a single custom instance.

    Args:
        instance_id: The instance ID to evaluate
        pred_data: Prediction data with 'model_patch' key
        tasks_dir: Directory containing task subdirectories
        run_id: Unique identifier for this evaluation run
        timeout: Timeout in seconds
        force_rebuild: Force rebuild Docker images
        rebuilt_images: Set of already-rebuilt image keys (for smart caching)

    Returns:
        Tuple of (instance_id, result_dict, resolved, is_error)
    """
    # Extract original instance_id (handles blocker test configs)
    original_instance_id = extract_original_instance_id(instance_id)

    # Find the task directory
    task_dir = tasks_dir / original_instance_id
    if not task_dir.exists():
        # Try without prefix (e.g., "demo__simple_demo" -> tasks/demo)
        parts = original_instance_id.split("__")
        if len(parts) > 1:
            task_dir = tasks_dir / parts[0]

    metadata = load_custom_instance_metadata(task_dir)

    # If no metadata found, check if tasks_dir itself is the task directory
    # (when running a single task)
    if metadata is None:
        metadata = load_custom_instance_metadata(tasks_dir)
        if metadata is not None:
            task_dir = tasks_dir

    if metadata is None:
        print(f"⚠️  No metadata found for {instance_id} in {tasks_dir}, skipping")
        return (instance_id, {}, False, False)

    print(f"🧪 Evaluating custom instance: {instance_id}")

    try:
        # Filter out __pycache__ and other generated files from the patch
        # These can cause patch application failures
        raw_patch = pred_data.get("model_patch", "") or ""
        clean_patch = filter_patch(raw_patch)
        if raw_patch != clean_patch:
            print(f"   ℹ️  [{instance_id}] Filtered generated files from patch")

        # Smart rebuild: only force rebuild if we haven't already rebuilt this image
        # The image key is based on original_instance_id (the actual task, not pass variants)
        should_rebuild = force_rebuild
        if rebuilt_images is not None and force_rebuild:
            if original_instance_id in rebuilt_images:
                # Already rebuilt this image, skip rebuild
                should_rebuild = False
            else:
                # Mark as rebuilt for future evaluations
                rebuilt_images.add(original_instance_id)

        result = evaluate_from_metadata(
            metadata=metadata,
            task_dir=task_dir,
            model_patch=clean_patch,
            run_id=run_id,
            timeout=timeout,
            force_rebuild=should_rebuild,
            model_name=pred_data.get("model_name_or_path", "unknown"),
        )

        result_dict = {
            "completed": result.get("completed", False),
            "resolved": result.get("resolved", False),
        }

        model_name = pred_data.get("model_name_or_path", "unknown").replace("/", "__")
        log_dir = RUN_EVALUATION_LOG_DIR / run_id / model_name / instance_id

        if result.get("resolved"):
            print(f"   ✅ [{instance_id}] RESOLVED")
            return (instance_id, result_dict, True, False)

        # Evaluation did not resolve - check for test_patch failure (input validation error)
        test_output_file = log_dir / "test_output.txt"
        test_output = ""
        if test_output_file.exists():
            try:
                test_output = test_output_file.read_text()
            except OSError:
                pass

        test_patch = metadata.get("test_patch", "")
        input_validation_error = _detect_test_patch_failure(test_output, clean_patch, test_patch)
        if input_validation_error:
            print(f"   ❌ [{instance_id}] {input_validation_error}")
            result_dict["input_validation_error"] = input_validation_error
            return (instance_id, result_dict, False, True)

        if not result.get("completed"):
            print(f"   ❌ [{instance_id}] ERROR (evaluation did not complete)")
            if "test_output" in result:
                test_out = result.get("test_output", "")
                print(
                    f"   Test output: {test_out[:500]}..."
                    if len(test_out) > 500
                    else f"   Test output: {test_out or 'N/A'}"
                )
            if "error" in result:
                print(f"   Error: {result['error']}")
            print(f"   📋 Full logs: {log_dir}/run_instance.log")
            return (instance_id, result_dict, False, True)
        else:
            print(f"   ❌ [{instance_id}] FAILED (tests did not pass)")
            print(f"   📋 Test output: {log_dir}/test_output.txt")
            print(f"   📋 Full logs: {log_dir}/run_instance.log")
            return (instance_id, result_dict, False, False)

    except Exception as e:
        result_dict = {
            "completed": False,
            "resolved": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }
        print(f"   ❌ [{instance_id}] EXCEPTION: {e}")
        traceback.print_exc()
        return (instance_id, result_dict, False, True)


def evaluate_custom_instances(
    predictions: Mapping[str, Mapping[str, Any]],
    tasks_dir: Path,
    run_id: str = "custom-eval",
    timeout: int = 1800,
    force_rebuild: bool = False,
    max_workers: int = 1,
) -> dict[str, Any]:
    """
    Evaluate multiple custom instances from a tasks directory.

    Args:
        predictions: Dict mapping instance_id to prediction data
                    Each prediction should have 'model_patch' key
        tasks_dir: Directory containing task subdirectories with metadata.json
        run_id: Unique identifier for this evaluation run
        timeout: Timeout in seconds per instance
        force_rebuild: Force rebuild Docker images
        max_workers: Number of parallel workers for evaluation (default: 1)

    Returns:
        dict with evaluation results in swebench-compatible format:
        {
            "resolved_ids": [...],
            "resolved_instances": int,
            "total_instances": int,
            "error_ids": [...],
            "results": {instance_id: {...}, ...}
        }
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from threading import Lock

    global _REBUILT_IMAGES

    results: dict[str, dict] = {}
    resolved_ids: list[str] = []
    error_ids: list[str] = []

    # Use module-level cache for tracking rebuilt images across multiple
    # evaluate_custom_instances calls (e.g., when running multiple passes).
    # This avoids redundant rebuilds across the entire batch run.
    rebuilt_lock = Lock()

    def safe_rebuilt_check_and_add(image_key: str) -> bool:
        """Thread-safe check-and-add for rebuilt images. Returns True if should rebuild."""
        with rebuilt_lock:
            if image_key in _REBUILT_IMAGES:
                return False
            _REBUILT_IMAGES.add(image_key)
            return True

    # Wrapper that uses thread-safe rebuilt tracking
    def evaluate_with_tracking(
        instance_id: str, pred_data: Mapping[str, Any]
    ) -> tuple[str, dict, bool, bool]:
        original_instance_id = extract_original_instance_id(instance_id)

        # Determine if we should rebuild
        should_rebuild = force_rebuild and safe_rebuilt_check_and_add(original_instance_id)

        return _evaluate_single_instance(
            instance_id=instance_id,
            pred_data=pred_data,
            tasks_dir=tasks_dir,
            run_id=run_id,
            timeout=timeout,
            force_rebuild=should_rebuild,
            rebuilt_images=None,  # We handle this at the wrapper level
        )

    if max_workers <= 1:
        # Sequential execution
        for instance_id, pred_data in predictions.items():
            inst_id, result_dict, resolved, is_error = evaluate_with_tracking(
                instance_id, pred_data
            )
            if result_dict:  # Empty dict means skipped (no metadata)
                results[inst_id] = result_dict
                if resolved:
                    resolved_ids.append(inst_id)
                elif is_error:
                    error_ids.append(inst_id)
    else:
        # Parallel execution
        print(f"🔄 Running parallel evaluation with {max_workers} workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_instance = {
                executor.submit(evaluate_with_tracking, instance_id, pred_data): instance_id
                for instance_id, pred_data in predictions.items()
            }

            for future in as_completed(future_to_instance):
                try:
                    inst_id, result_dict, resolved, is_error = future.result()
                    if result_dict:  # Empty dict means skipped (no metadata)
                        results[inst_id] = result_dict
                        if resolved:
                            resolved_ids.append(inst_id)
                        elif is_error:
                            error_ids.append(inst_id)
                except Exception as e:
                    instance_id = future_to_instance[future]
                    print(f"   ❌ [{instance_id}] Future exception: {e}")
                    error_ids.append(instance_id)
                    results[instance_id] = {
                        "completed": False,
                        "resolved": False,
                        "error": str(e),
                        "traceback": traceback.format_exc(),
                    }

    return {
        "resolved_ids": resolved_ids,
        "resolved_instances": len(resolved_ids),
        "total_instances": len(predictions),
        "error_ids": error_ids,
        "results": results,
    }


# =============================================================================
# Convenience / Example Specs
# =============================================================================

# ----- Python Examples (use conda) -----

EXAMPLE_SPECS_PYTEST: CustomInstallSpecs = {
    "python": "3.11",
    "test_cmd": "pytest -rA",
    "install": "pip install -e .",
    "pip_packages": ["pytest"],
}

EXAMPLE_SPECS_WITH_DEPS: CustomInstallSpecs = {
    "python": "3.10",
    "test_cmd": "pytest -rA --tb=short",
    "install": "pip install -e .",
    "packages": "requirements.txt",
    "pip_packages": ["pytest", "pytest-cov"],
}

# ----- Non-Python Examples (custom base image) -----

EXAMPLE_SPECS_NODEJS: CustomInstallSpecs = {
    "base_image": "node:18",
    "test_cmd": "npm test",
    "install": "npm install",
}

EXAMPLE_SPECS_GOLANG: CustomInstallSpecs = {
    "base_image": "golang:1.21",
    "test_cmd": "go test ./...",
    "install": "go mod download",
}

EXAMPLE_SPECS_RUST: CustomInstallSpecs = {
    "base_image": "rust:1.75",
    "test_cmd": "cargo test",
    "install": "cargo build",
}

EXAMPLE_SPECS_GENERIC: CustomInstallSpecs = {
    "base_image": "ubuntu:22.04",
    "env_setup": [
        "apt-get update",
        "apt-get install -y build-essential",
    ],
    "test_cmd": "./run_tests.sh",
    "install": "make install",
}
