#!/usr/bin/env python3
"""
Calculate industry-standard pass@1 success rates from SWE-agent batch run results.
Following practices used by OpenAI, Anthropic, and academia.

Pass@1 = percentage of problems where the first generated solution is correct.
This is determined by checking if the model's patch actually fixes the failing tests.

Supports both:
1. Official SWE-bench instances (uses swebench harness)
2. Custom instances (uses custom_eval.py)
"""

import json
import time
import traceback
from pathlib import Path
from typing import TypedDict

import yaml
from swebench.harness.constants import KEY_INSTANCE_ID, KEY_MODEL, KEY_PREDICTION
from swebench.harness.run_evaluation import main as run_evaluation

from .custom_eval import evaluate_custom_instances


class SWEAgentPrediction(TypedDict):
    model_name_or_path: str
    instance_id: str
    model_patch: str


def load_predictions(trajectory_dir: str | Path) -> dict[str, SWEAgentPrediction] | None:
    """Load predictions from SWE-agent trajectory directory."""
    preds_file = Path(trajectory_dir) / "preds.json"
    if not preds_file.exists():
        print(f"❌ Predictions file not found: {preds_file}")
        return None
    return json.loads(preds_file.read_text())


def convert_preds_to_jsonl(preds_dict: dict[str, SWEAgentPrediction], output_path: Path) -> None:
    """
    Convert SWE-agent preds.json format to SWE-bench JSONL format.
    """
    with open(output_path, "w") as f:
        for pred_data in preds_dict.values():
            f.write(
                json.dumps(
                    {
                        KEY_INSTANCE_ID: pred_data["instance_id"],
                        KEY_MODEL: pred_data["model_name_or_path"],
                        KEY_PREDICTION: pred_data["model_patch"],
                    }
                )
                + "\n"
            )


def get_cost_runtime(trajectory_dir: str | Path) -> dict[str, dict[str, float]]:
    """
    Load per-instance cost and runtime from trajectory files.

    Returns:
        dict: Mapping of instance_id to dict with 'cost' and 'runtime' keys
    """
    trajectory_path = Path(trajectory_dir)
    instance_metrics = {}

    # Find all .traj files in subdirectories
    traj_files = list(trajectory_path.glob("**/*.traj"))

    for traj_file in traj_files:
        traj_data = json.loads(traj_file.read_text())
        instance_id = traj_file.stem
        cost = 0.0
        if "info" in traj_data and "model_stats" in traj_data["info"]:
            cost = traj_data["info"]["model_stats"].get("instance_cost", 0.0)

        # Calculate total runtime by summing execution_time from all steps
        runtime = 0.0
        if "trajectory" in traj_data:
            for step in traj_data["trajectory"]:
                if "execution_time" in step:
                    runtime += step["execution_time"]

        instance_metrics[instance_id] = {
            "cost": cost,
            "runtime": runtime,
        }

    return instance_metrics


def get_total_cost(trajectory_dir: str | Path) -> float:
    """Get total cost from exit status file if available."""
    trajectory_path = Path(trajectory_dir)
    exit_status_file = trajectory_path / "run_batch_exit_statuses.yaml"

    if exit_status_file.exists():
        with open(exit_status_file, "r") as f:
            exit_data = yaml.safe_load(f)
        return exit_data.get("total_cost", 0)

    return 0


def run_swebench_evaluation(
    predictions_path: Path,
    dataset_name: str = "princeton-nlp/SWE-bench_Verified",
    split: str = "test",
    max_workers: int = 4,
    run_id: str | None = None,
    timeout: int = 1800,
    instance_ids: list | None = None,
) -> dict:
    """
    Run SWE-bench eval to determine pass@1.

    This runs the patches through Docker containers to verify they actually
    pass the failing tests.

    Args:
        predictions_path: Path to JSONL file with predictions. Results will be saved in
          predictions_path.parent / "swebench_eval_results" / run_id
        dataset_name: SWE-bench dataset name (Lite, Verified, or full)
        split: Dataset split to use (default: "test")
        max_workers: Number of parallel evaluation workers
        run_id: Unique identifier for this evaluation run (defaults to swe_eval_{timestamp})
        timeout: Timeout for the entire evaluation in seconds
        instance_ids: Optional list of specific instance IDs to evaluate

    Returns:
        dict with evaluation results including resolved instances (empty list if evaluation fails)
    """
    if run_id is None:
        run_id = f"swe_eval_{int(time.time())}"

    if instance_ids is None:
        instance_ids = []

    output_dir = predictions_path.parent / "swebench_eval_results"
    output_dir.mkdir(exist_ok=True)

    print("🧪 Running SWE-bench evaluation...")
    print(f"   Dataset: {dataset_name}")
    print(f"   Split: {split}")
    print(f"   Predictions: {predictions_path}")
    print(f"   Workers: {max_workers}")
    print(f"   Run ID: {run_id}")

    empty_results = {"resolved_instances": [], "resolved_count": 0, "raw_results": {}}

    try:
        report_path = run_evaluation(
            dataset_name=dataset_name,
            split=split,
            instance_ids=instance_ids,
            predictions_path=str(predictions_path),
            max_workers=max_workers,
            force_rebuild=False,
            cache_level="env",
            clean=False,
            open_file_limit=4096,
            run_id=run_id,
            timeout=timeout,
            namespace=None,
            rewrite_reports=False,
            modal=False,
        )
        if report_path is None:
            return empty_results
        return parse_swebench_results(report_path)

    except:
        print("⚠️  SWE-bench evaluation failed")
        traceback.print_exc()
        return empty_results


def parse_swebench_results(report_path: Path) -> dict:
    """
    Parse SWE-bench evaluation report JSON.

    The report contains:
    - resolved_ids: list of instance IDs that passed all tests
    - resolved_instances: count of resolved instances
    - total_instances: total count in dataset
    - etc.

    Returns:
        dict with resolved_instances list and metrics
    """
    data = json.loads(report_path.read_text())
    resolved = data.get("resolved_ids", [])

    return {
        "resolved_instances": resolved,
        "resolved_count": len(resolved),
        "raw_results": data,
    }


def calculate_pass_at_1(
    trajectory_dir: str | Path,
    dataset_name: str = "princeton-nlp/SWE-bench_Verified",
    max_workers: int = 4,
    tasks_dir: str | Path | None = None,
) -> dict:
    """
    Calculate pass@1 using swe bench.

    Pass@1 = percentage of problems where the first generated solution is correct.

    If the instances are from a SWE bench dataset, provide the name; otherwise, use
    `tasks_dir` to specify the path to the tasks directory for local instances.
    Evaluating local and SWE-bench instances in one call is not supported.

    Args:
        trajectory_dir: Path to SWE-agent trajectory directory
        dataset_name: SWE-bench dataset name for evaluation
        max_workers: Number of parallel workers for evaluation
        tasks_dir: Path to tasks directory

    Returns:
        dict with pass@1 results
    """
    trajectory_path = Path(trajectory_dir)
    print(f"🧮 Calculating pass@1 for: {trajectory_dir}")

    predictions = load_predictions(trajectory_dir)
    if predictions is None or not predictions:
        raise ValueError("❌ No predictions found")

    total_instances = len(predictions)
    print(f"📊 Found {total_instances} instances")

    instance_metrics = get_cost_runtime(trajectory_dir)
    # Sum up individual instance costs and runtimes
    total_cost = sum(m.get("cost", 0) for m in instance_metrics.values())
    total_runtime = sum(m.get("runtime", 0) for m in instance_metrics.values())

    if tasks_dir:
        tasks_path = Path(tasks_dir)
        print(f"\n🔬 Running custom instance evaluation with {max_workers} workers...")
        # Use multiple path components to create a unique run_id
        # This avoids collisions when running multiple models/modes/passes in batch
        # e.g., "results/demo_test3/openai_gpt-5-codex/full_info/pass_1"
        #    -> "custom-eval.demo_test3.openai_gpt-5-codex.full_info.pass_1"
        # Note: run_id is used in Docker container names, so no slashes allowed
        path_parts = trajectory_path.parts[-4:]  # Get last 4 components for uniqueness
        custom_run_id = "custom-eval." + ".".join(path_parts)
        eval_results = evaluate_custom_instances(
            predictions=predictions,
            tasks_dir=tasks_path,
            run_id=custom_run_id,
            # Force rebuild to ensure clean state - custom instances are often iterated on
            # The evaluate_custom_instances function now tracks which images have been rebuilt
            # to avoid redundant rebuilds across passes
            force_rebuild=True,
            max_workers=max_workers,
        )
        resolved = eval_results.get("resolved_ids", [])
        instance_type = "custom"
    else:
        preds_jsonl_path = trajectory_path / "all_preds.jsonl"
        convert_preds_to_jsonl(predictions, preds_jsonl_path)

        print("\n🔬 Running test validation via SWE-bench...")
        eval_results = run_swebench_evaluation(
            predictions_path=preds_jsonl_path,
            dataset_name=dataset_name,
            max_workers=max_workers,
        )
        resolved = eval_results.get("resolved_instances", [])
        instance_type = "swebench"

    print(f"✅ Test validation complete: {len(resolved)} instances resolved")

    patches_generated = sum(
        1 for pred_data in predictions.values() if pred_data.get("model_patch", "").strip()
    )

    results = {
        "total_instances": total_instances,
        "pass_at_1_count": len(resolved),
        "pass_at_1_rate": (len(resolved) / total_instances) * 100 if total_instances > 0 else 0,
        "resolved_instances": resolved,
        "patches_generated": patches_generated,
        "patch_generation_rate": (
            (patches_generated / total_instances) * 100 if total_instances > 0 else 0
        ),
        "total_cost": total_cost,
        "total_runtime": total_runtime,
        "instances": instance_metrics,
        "instance_type": instance_type,
        "raw_eval_results": eval_results,
    }

    return results


def print_pass_at_1_summary(results: dict | None) -> None:
    if results is None:
        return

    print("\n" + "=" * 60)
    print("🎯 PASS@1 EVALUATION")
    print("=" * 60)

    print(
        f"📊 PASS@1: {results['pass_at_1_rate']:.1f}% ({results['pass_at_1_count']}/{results['total_instances']})"
    )

    if results.get("resolved_instances"):
        print(f"✅ RESOLVED INSTANCES ({len(results['resolved_instances'])}):")

    print(f"✅ Passes tests: {results['pass_at_1_count']}")
    print(
        f"🔧 Patches generated: {results['patches_generated']} ({results['patch_generation_rate']:.1f}%)"
    )

    # Cost
    if results.get("total_cost", 0) > 0:
        print(f"\n💰 COST: ${results['total_cost']:.4f}")
        if results["pass_at_1_count"] > 0:
            cost_per_success = results["total_cost"] / results["pass_at_1_count"]
            print(f"   Cost per success: ${cost_per_success:.4f}")

    print("=" * 60)
