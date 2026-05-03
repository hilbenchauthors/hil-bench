"""
Comprehensive fix script for Harbor HiL-Bench SWE tasks.

Groups of changes:
  Group 2: Fix HF bucket names (kellu-scale -> ScaleAI) in image_source_defaults.json,
            image_archive.json (x100), and metadata.json image_archive sub-object (x100)
  Group 3: Fix run_script_path/parser_script_path (/tests/ -> /root/) in metadata.json (x100),
            fix language capitalization in swe_0 (Python -> python)
  Group 4: Fix markdown fence corruption in blocker_registry.json for swe_38/57/62/99
  Group 1: Create tests/ folder (test.sh, test_patch.diff, fail_to_pass.json) in all 300
            task mode directories (100 tasks x 3 modes: baseline, full_info, ask_human)
  Group 5: Add docker_image to [environment] in all 300 task.toml files so Harbor uses the
            prebuilt image directly (skipping the slow docker build step)
  Group 6: Fix blocker_registry.json type field from single-element list to string in all
            100 tasks (e.g. ["missing parameters"] -> "missing parameters")
"""

import json
import re
import sys
import tomllib
from pathlib import Path

try:
    import toml as _toml  # type: ignore
except ImportError:
    _toml = None

HARBOR_SWE = Path(__file__).parent
TASK_DIRS = sorted(
    (d for d in HARBOR_SWE.iterdir() if d.is_dir() and re.match(r"^swe_\d+$", d.name)),
    key=lambda p: int(p.name.split("_")[1]),
)
MODES = ["baseline", "full_info", "ask_human"]
OLD_BUCKET = "kellu-scale/hil-bench-swe-images"
NEW_BUCKET = "ScaleAI/hil-bench-swe-images"
OLD_HF_URL_BASE = "https://huggingface.co/buckets/kellu-scale/hil-bench-swe-images"
NEW_HF_URL_BASE = "https://huggingface.co/buckets/ScaleAI/hil-bench-swe-images"

# ---------------------------------------------------------------------------
# Universal test.sh content (identical for all 300 task-mode directories)
# ---------------------------------------------------------------------------
TEST_SH = r"""#!/usr/bin/env bash
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
"""


# ---------------------------------------------------------------------------
# Helper: fix markdown fence corrupted blocker id
# ---------------------------------------------------------------------------
def fix_blocker_id(raw_id: str) -> str:
    """Strip markdown code fence wrappers from a blocker id field."""
    s = raw_id.strip()
    # Match ```lang\n<content>\n``` or ```\n<content>\n```
    m = re.match(r"^```[a-z]*\n(.+?)\n```$", s, re.DOTALL)
    if m:
        return m.group(1).strip()
    return s


# ---------------------------------------------------------------------------
# Group 2: Fix HF bucket
# ---------------------------------------------------------------------------
def fix_hf_bucket_in_obj(obj: dict) -> bool:
    """Fix hf_bucket and hf_url in a dict in-place. Returns True if changed."""
    changed = False
    if obj.get("hf_bucket") == OLD_BUCKET:
        obj["hf_bucket"] = NEW_BUCKET
        changed = True
    if "hf_url" in obj and OLD_HF_URL_BASE in obj["hf_url"]:
        obj["hf_url"] = obj["hf_url"].replace(OLD_HF_URL_BASE, NEW_HF_URL_BASE)
        changed = True
    return changed


def group2_fix_image_source_defaults() -> None:
    path = HARBOR_SWE / "shared/image_source_defaults.json"
    with open(path) as f:
        data = json.load(f)
    if data.get("default_hf_bucket") == OLD_BUCKET:
        data["default_hf_bucket"] = NEW_BUCKET
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"  [G2] Fixed: {path.relative_to(HARBOR_SWE)}")
    else:
        print(f"  [G2] Already correct: {path.relative_to(HARBOR_SWE)}")


def group2_fix_task_files(task_dir: Path) -> None:
    # Fix image_archive.json
    ia_path = task_dir / "shared/image_archive.json"
    if ia_path.exists():
        with open(ia_path) as f:
            ia = json.load(f)
        if fix_hf_bucket_in_obj(ia):
            with open(ia_path, "w") as f:
                json.dump(ia, f, indent=2)
                f.write("\n")

    # Fix metadata.json image_archive sub-object
    meta_path = task_dir / "shared/metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        if "image_archive" in meta and isinstance(meta["image_archive"], dict):
            if fix_hf_bucket_in_obj(meta["image_archive"]):
                with open(meta_path, "w") as f:
                    json.dump(meta, f, indent=2)
                    f.write("\n")


# ---------------------------------------------------------------------------
# Group 3: Fix metadata fields
# ---------------------------------------------------------------------------
def group3_fix_metadata(task_dir: Path) -> None:
    meta_path = task_dir / "shared/metadata.json"
    if not meta_path.exists():
        return
    with open(meta_path) as f:
        meta = json.load(f)
    changed = False

    # Fix run_script_path / parser_script_path
    if meta.get("run_script_path") == "/tests/run_script.sh":
        meta["run_script_path"] = "/root/run_script.sh"
        changed = True
    if meta.get("parser_script_path") == "/tests/parser.py":
        meta["parser_script_path"] = "/root/parser.py"
        changed = True

    # Fix language capitalization for swe_0 (Python -> python)
    if task_dir.name == "swe_0" and meta.get("language") == "Python":
        meta["language"] = "python"
        changed = True

    if changed:
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
            f.write("\n")


# ---------------------------------------------------------------------------
# Group 4: Fix blocker registry markdown fences
# ---------------------------------------------------------------------------
def group4_fix_blocker_registry(task_dir: Path) -> None:
    br_path = task_dir / "shared/ask-human-data/blocker_registry.json"
    if not br_path.exists():
        return
    with open(br_path) as f:
        data = json.load(f)
    changed = False
    for blocker in data.get("blockers", []):
        raw_id = blocker.get("id", "")
        fixed = fix_blocker_id(raw_id)
        if fixed != raw_id:
            blocker["id"] = fixed
            changed = True
    if changed:
        with open(br_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"  [G4] Fixed blocker ids in: {task_dir.name}")


# ---------------------------------------------------------------------------
# Group 1: Create tests/ directories
# ---------------------------------------------------------------------------
def group1_create_tests_dir(task_dir: Path, mode: str) -> None:
    """Create tests/ with test.sh, test_patch.diff, fail_to_pass.json."""
    meta_path = task_dir / "shared/metadata.json"
    with open(meta_path) as f:
        meta = json.load(f)

    test_patch = meta.get("test_patch", "")
    fail_to_pass = meta.get("swe_bench_metadata", {}).get("FAIL_TO_PASS", [])

    mode_dir = task_dir / mode
    tests_dir = mode_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)

    # Write test.sh
    test_sh_path = tests_dir / "test.sh"
    test_sh_path.write_text(TEST_SH)
    test_sh_path.chmod(0o755)

    # Write test_patch.diff
    (tests_dir / "test_patch.diff").write_text(test_patch)

    # Write fail_to_pass.json
    (tests_dir / "fail_to_pass.json").write_text(
        json.dumps(fail_to_pass, indent=2) + "\n"
    )


# ---------------------------------------------------------------------------
# Group 6: Fix blocker type field from list to string
# ---------------------------------------------------------------------------
def group6_fix_blocker_type(task_dir: Path) -> bool:
    """Convert single-element list type fields to strings (idempotent)."""
    br_path = task_dir / "shared/ask-human-data/blocker_registry.json"
    if not br_path.exists():
        return False
    with open(br_path) as f:
        data = json.load(f)
    changed = False
    for blocker in data.get("blockers", []):
        t = blocker.get("type")
        if isinstance(t, list):
            blocker["type"] = t[0] if t else ""
            changed = True
    if changed:
        with open(br_path, "w") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    return changed


# ---------------------------------------------------------------------------
# Group 5: Add docker_image to [environment] in task.toml
# ---------------------------------------------------------------------------
def _write_task_toml(path: Path, data: dict) -> None:
    """Write a task.toml using toml if available, otherwise manual patching."""
    if _toml is not None:
        path.write_text(_toml.dumps(data))
        return
    # Fallback: insert docker_image line into the [environment] section manually
    lines = path.read_text().splitlines(keepends=True)
    result = []
    in_env = False
    inserted = False
    for line in lines:
        stripped = line.strip()
        if stripped == "[environment]":
            in_env = True
        elif stripped.startswith("[") and in_env:
            in_env = False
        if in_env and not inserted and stripped.startswith("build_timeout_sec"):
            result.append(line)
            result.append(f'docker_image = "PLACEHOLDER"\n')
            inserted = True
            continue
        result.append(line)
    path.write_text("".join(result))


def group5_add_docker_image(task_dir: Path, mode: str) -> bool:
    """Add docker_image to [environment] in the mode's task.toml (idempotent)."""
    task_toml_path = task_dir / mode / "task.toml"
    if not task_toml_path.exists():
        return False

    content = task_toml_path.read_text()
    data = tomllib.loads(content)

    # The image name lives in metadata.image_name
    image_name = data.get("metadata", {}).get("image_name", "")
    if not image_name:
        print(f"  [G5] WARN: no image_name in metadata for {task_dir.name}/{mode}")
        return False

    env_section = data.get("environment", {})
    if env_section.get("docker_image") == image_name:
        return False  # Already correct, no change needed

    # Patch the TOML text directly (preserve formatting)
    if "docker_image" in content:
        # Replace existing wrong value
        patched = re.sub(
            r'^docker_image\s*=\s*"[^"]*"',
            f'docker_image = "{image_name}"',
            content,
            flags=re.MULTILINE,
        )
    else:
        # Insert docker_image right after the [environment] header line
        patched = re.sub(
            r"(\[environment\]\s*\n)",
            f'\\1docker_image = "{image_name}"\n',
            content,
        )

    task_toml_path.write_text(patched)
    return True


# ---------------------------------------------------------------------------
# Group 7: Add pull_policy: never to all docker-compose.yaml files
# ---------------------------------------------------------------------------
def group7_fix_pull_policy(task_dir: Path, mode: str) -> int:
    """Add pull_policy: never to every service in the mode's docker-compose.yaml.

    Docker Compose v2 defaults to pull_policy: always for services without a
    build section, which causes it to attempt pulling local images from Docker
    Hub (and fail). This fix prevents that by explicitly setting pull_policy:
    never so Compose uses whatever image is already present locally.

    Returns the number of services patched.
    """
    compose_path = task_dir / mode / "environment" / "docker-compose.yaml"
    if not compose_path.exists():
        return 0

    content = compose_path.read_text()
    if "pull_policy" in content:
        return 0

    # Insert `pull_policy: never` before each `image:` line under a service
    new_content = content.replace("\n    image:", "\n    pull_policy: never\n    image:")
    if new_content == content:
        return 0

    compose_path.write_text(new_content)
    services_patched = new_content.count("pull_policy: never")
    return services_patched


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[DRY RUN] No files will be modified.\n")

    print(f"Processing {len(TASK_DIRS)} task directories...\n")

    # Group 2a: image_source_defaults.json (shared, once)
    print("=== Group 2: Fix HF bucket ===")
    if not dry_run:
        group2_fix_image_source_defaults()

    g2_changed = 0
    g3_changed = 0
    g4_changed = 0
    g1_created = 0
    g5_changed = 0
    g6_changed = 0
    g7_services = 0

    for task_dir in TASK_DIRS:
        if not dry_run:
            # Group 2b: per-task image_archive.json and metadata.json image_archive
            group2_fix_task_files(task_dir)
            g2_changed += 1

            # Group 3: metadata fields
            group3_fix_metadata(task_dir)
            g3_changed += 1

            # Group 4: blocker registry id markdown fences (only for affected tasks)
            group4_fix_blocker_registry(task_dir)
            g4_changed += 1

            # Group 6: blocker type field list -> string (all tasks)
            if group6_fix_blocker_type(task_dir):
                g6_changed += 1

            # Group 1 + 5 + 7: tests/ dirs, docker_image, and pull_policy for each mode
            for mode in MODES:
                mode_dir = task_dir / mode
                if mode_dir.exists():
                    group1_create_tests_dir(task_dir, mode)
                    g1_created += 1
                    if group5_add_docker_image(task_dir, mode):
                        g5_changed += 1
                    g7_services += group7_fix_pull_policy(task_dir, mode)
        else:
            for mode in MODES:
                mode_dir = task_dir / mode
                if mode_dir.exists():
                    g1_created += 1
                    # Count services that would be patched in dry-run
                    compose_path = task_dir / mode / "environment" / "docker-compose.yaml"
                    if compose_path.exists() and "pull_policy" not in compose_path.read_text():
                        g7_services += compose_path.read_text().count("\n    image:")

    print(f"\n=== Summary ===")
    print(f"  [G2] Fixed HF bucket in {g2_changed} task dirs + image_source_defaults.json")
    print(f"  [G3] Fixed metadata fields in {g3_changed} task dirs")
    print(f"  [G4] Checked blocker registries in {g4_changed} task dirs")
    print(f"  [G1] Created/updated tests/ in {g1_created} task-mode dirs")
    print(f"  [G5] Added docker_image to [environment] in {g5_changed} task.toml files")
    print(f"  [G6] Fixed blocker type list->string in {g6_changed} blocker_registry.json files")
    print(f"  [G7] Added pull_policy: never to {g7_services} services across docker-compose.yaml files")
    if dry_run:
        print("\n(Dry run complete - no files written)")


if __name__ == "__main__":
    main()
