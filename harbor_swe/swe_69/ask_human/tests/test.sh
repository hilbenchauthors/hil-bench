#!/usr/bin/env bash
# HiL-Bench SWE Evaluator for Harbor
# Reads test_patch.diff and fail_to_pass.json from /tests/,
# applies the hidden test patch, runs the SWEAP evaluation pipeline,
# and writes a binary reward (1=pass, 0=fail) to /logs/verifier/reward.txt.
set -uo pipefail
_TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p /logs/verifier
python3 - "${_TESTS_DIR}" /logs/verifier/reward.txt /tmp << 'EOF_EVALUATOR'
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

tests_dir = Path(sys.argv[1])
reward_path = Path(sys.argv[2])
tmp_dir = Path(sys.argv[3])
repo_dir = Path("/app")
run_script = Path("/root/run_script.sh")
parser_script = Path("/root/parser.py")
stdout_log = tmp_dir / "sweap_stdout.log"
stderr_log = tmp_dir / "sweap_stderr.log"
output_json = tmp_dir / "sweap_output.json"
test_patch_file = tests_dir / "test_patch.diff"
fail_to_pass_file = tests_dir / "fail_to_pass.json"


def log(msg: str) -> None:
    print(f"[verifier] {msg}", flush=True)


def write_reward(value: int) -> None:
    reward_path.write_text(str(value))
    log(f"reward={value}")


def write_reward_json(data: dict) -> None:
    reward_json_path = reward_path.parent / "reward.json"
    reward_json_path.write_text(json.dumps(data, indent=2))
    log(f"reward.json: {data}")


def get_patch_files(patch_content: str) -> list:
    # Returns list of file paths modified by the given git diff.
    files = []
    for line in patch_content.splitlines():
        m = re.match(r"^diff --git a/(.+) b/.+$", line)
        if m:
            files.append(m.group(1))
    return files


def run_cmd(cmd, **kwargs):
    log(f"+ {' '.join(str(c) for c in cmd)}")
    return subprocess.run(cmd, **kwargs)


# --- Step 1: Read test_patch ---
if not test_patch_file.exists() or test_patch_file.stat().st_size == 0:
    log("No test_patch.diff found or empty; skipping patch")
    patch_content = ""
else:
    patch_content = test_patch_file.read_text()

# --- Step 2: Setup repo working directory ---
os.chdir(repo_dir)
run_cmd(
    ["git", "config", "--global", "--add", "safe.directory", str(repo_dir)],
    capture_output=True,
)

# --- Step 3: Reset test files to HEAD (so agent changes don't corrupt test patch apply) ---
# For modified files: git checkout HEAD restores original.
# For new files (not tracked at HEAD): nothing to reset; git checkout fails harmlessly.
def is_tracked_at_head(rel_path: str) -> bool:
    r = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{rel_path}"],
        capture_output=True,
    )
    return r.returncode == 0


if patch_content:
    patch_files = get_patch_files(patch_content)
    if patch_files:
        tracked = [f for f in patch_files if is_tracked_at_head(f)]
        new_files = [f for f in patch_files if not is_tracked_at_head(f)]
        if tracked:
            log(f"Resetting {len(tracked)} modified test file(s) to HEAD")
            res = run_cmd(
                ["git", "checkout", "HEAD", "--"] + tracked,
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                log(f"WARNING: git checkout HEAD failed:\n{res.stderr}")
        for nf in new_files:
            nf_path = repo_dir / nf
            if nf_path.exists():
                log(f"Removing new test file (not tracked at HEAD): {nf}")
                nf_path.unlink()

# --- Step 4: Apply test_patch (introduces hidden tests targeting the blockers) ---
if patch_content:
    log("Applying test_patch...")
    res = run_cmd(
        ["git", "apply", "--verbose", "--reject", str(test_patch_file)],
        capture_output=True,
        text=True,
    )
    log(res.stdout)
    log(res.stderr)
    if res.returncode != 0:
        log("ERROR: test_patch failed to apply")
        write_reward(0)
        write_reward_json({"resolved": 0, "fail_to_pass_passed": 0, "fail_to_pass_total": 0})
        sys.exit(0)

# --- Step 5: Build per-language test args from FAIL_TO_PASS ---
with open(fail_to_pass_file) as f:
    fail_to_pass = json.load(f)

if not fail_to_pass:
    log("No FAIL_TO_PASS tests defined; writing reward=1")
    write_reward(1)
    write_reward_json({"resolved": 1, "fail_to_pass_passed": 0, "fail_to_pass_total": 0})
    sys.exit(0)

run_script_content = run_script.read_text() if run_script.exists() else ""
uses_ansible_test = "ansible-test" in run_script_content
is_js_ts = any(" | " in t for t in fail_to_pass)

args = list(fail_to_pass)

if uses_ansible_test:
    # Strip ::ClassName::method to get the pytest file path; run_script.sh handles this too
    # but we deduplicate here to avoid running the same file multiple times.
    if any("::" in t for t in args):
        extracted = list(dict.fromkeys(t.split("::")[0] for t in args if "::" in t))
        args = extracted if extracted else args
elif is_js_ts:
    # Strip " | test description" to get just the test file path; run_script.sh needs paths.
    seen = set()
    stripped = []
    for t in args:
        fp = t.split(" | ")[0].strip() if " | " in t else t
        if fp not in seen:
            seen.add(fp)
            stripped.append(fp)
    args = stripped
# Go tasks: use raw function names as-is (run_script.sh builds a regex from them)

log(f"Test args ({len(args)}): {args}")

# --- Step 6: Run run_script.sh with specific test args ---
log("Running run_script.sh...")
with open(stdout_log, "w") as out_f, open(stderr_log, "w") as err_f:
    run_result = subprocess.run(
        ["bash", str(run_script)] + args,
        stdout=out_f,
        stderr=err_f,
        cwd=repo_dir,
    )
log(f"run_script.sh exited with {run_result.returncode}")

# --- Step 7: Run parser.py to get structured JSON output ---
log("Running parser.py...")
parse_result = run_cmd(
    ["python3", str(parser_script), str(stdout_log), str(stderr_log), str(output_json)],
    capture_output=True,
    text=True,
)
log(parse_result.stdout)
log(parse_result.stderr)
if parse_result.returncode != 0:
    log("ERROR: parser.py failed")
    write_reward(0)
    sys.exit(0)

# --- Step 8: Check all FAIL_TO_PASS tests ---
with open(output_json) as f:
    parsed = json.load(f)

tests_map = {t["name"]: t["status"] for t in parsed.get("tests", [])}
log(f"Parsed {len(tests_map)} test result(s)")


def find_match(required: str) -> Optional[str]:
    # Multi-level matching between FAIL_TO_PASS names and parser.py output names:
    #   1. Exact match (primary, matches private HiL-Bench behavior)
    #   2. Suffix/prefix match (safety net for path-style variations)
    #   3. File + last-component match (handles ansible file::class::method vs file::method)
    if required in tests_map:
        return tests_map[required]
    # Suffix/prefix match
    for name, status in tests_map.items():
        if name.endswith(required) or required.endswith(name):
            return status
    # Last component + file prefix match (ansible class insertion)
    if "::" in required:
        req_file = required.split("::")[0]
        req_last = required.split("::")[-1]
        for name, status in tests_map.items():
            if name.split("::")[-1] == req_last and name.startswith(req_file):
                return status
    return None


all_pass = True
n_passed = 0
for required_test in fail_to_pass:
    status = find_match(required_test)
    if status == "PASSED":
        log(f"PASS: {required_test}")
        n_passed += 1
    else:
        log(f"FAIL: {required_test} -> {status!r}")
        all_pass = False

# --- Step 9: Write binary reward.txt and detailed reward.json ---
reward_value = 1 if all_pass else 0
write_reward(reward_value)

reward_data: dict = {
    "resolved": reward_value,
    "fail_to_pass_passed": n_passed,
    "fail_to_pass_total": len(fail_to_pass),
}
# Merge ask_human sidecar metrics when available (ask_human mode only).
# The sidecar writes to /harbor_shared/ via the shared named volume.
ask_human_metrics_path = Path("/harbor_shared/ask_human_metrics.json")
if ask_human_metrics_path.exists():
    try:
        with open(ask_human_metrics_path) as f:
            ah = json.load(f)
        reward_data["n_questions"] = ah.get("total_questions", 0)
        reward_data["n_blockers"] = ah.get("n_blockers", 0)
        reward_data["blockers_resolved"] = ah.get("blockers_resolved", 0)
        reward_data["precision"] = ah.get("precision", 0.0)
        reward_data["recall"] = ah.get("recall", 0.0)
        reward_data["f1"] = ah.get("f1", 0.0)
    except Exception as e:
        log(f"WARNING: could not read ask_human_metrics.json: {e}")
write_reward_json(reward_data)

# --- Step 10: Cleanup - reset test files to HEAD (or remove if new) ---
if patch_content:
    patch_files = get_patch_files(patch_content)
    if patch_files:
        tracked = [f for f in patch_files if is_tracked_at_head(f)]
        new_files = [f for f in patch_files if not is_tracked_at_head(f)]
        if tracked:
            run_cmd(
                ["git", "checkout", "HEAD", "--"] + tracked,
                capture_output=True,
                text=True,
            )
        for nf in new_files:
            nf_path = repo_dir / nf
            if nf_path.exists():
                nf_path.unlink()
EOF_EVALUATOR
