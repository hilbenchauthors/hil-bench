import json
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

from ..utils.instance_utils import extract_original_instance_id
from ..utils.config_mapping import (
    load_and_apply_judge_config,
    load_config_mapping,
    resolve_agent_config_path,
    validate_agent_hosting_config,
)


@dataclass
class RunConfig:
    """Configuration for a single run."""

    # Optional "instance set" name (e.g. SQL task-type folder like "100_instances").
    # When present, output_dir includes this as the leaf directory so that metrics.json
    # are collected consistently by the batch runner.
    instance_name: str | None
    model_name: str
    mode_name: str
    enable_ask: bool
    full_info: bool
    pass_number: int
    output_dir: Path


@dataclass
class BatchResult:
    """Result from a single run."""

    config: RunConfig
    returncode: int

    @property
    def success(self) -> bool:
        return self.returncode == 0


@dataclass
class BatchRunnerConfig:
    """Configuration for the batch runner."""

    # Models to run
    model_names: list[str]

    # Modes to run: list of (mode_name, enable_ask, full_info)
    modes: list[tuple[str, bool, bool]]

    # Optional additional axis for batching (e.g., SQL runs across multiple instance files).
    # When provided, the runner executes (instances x models x modes x passes).
    instance_names: list[str] | None = None

    # Number of passes (k runs for variation)
    passes: int = 1

    # Run name for organizing results
    run_name: str | None = None

    # Base output directory (default: results/)
    base_output_dir: Path | None = None

    # Additional run-specific settings
    num_workers: int = 5
    cleanup_docker: bool = True
    cleanup_trajectories: bool = False


def generate_run_name(model_names: list[str], modes: list[tuple[str, bool, bool]]) -> str:
    """Generate a default run name based on configuration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Summarize models
    if len(model_names) == 1:
        model_part = model_names[0].replace("/", "_").replace(":", "_")
    else:
        model_part = f"{len(model_names)}models"

    # Summarize modes
    if len(modes) == 3:
        mode_part = "all_modes"
    elif len(modes) == 1:
        mode_part = modes[0][0]
    else:
        mode_part = f"{len(modes)}modes"

    return f"{model_part}_{mode_part}_{timestamp}"


def create_results_directory(
    run_name: str,
    base_output_dir: Path | None = None,
) -> Path:
    """
    Create and return the results directory for a batch run.

    When an explicit run_name is provided and the directory already contains
    trajectory files from a previous run, a timestamped subdirectory is
    created so the old results are never mixed with or overwritten by the
    new run:

        results/{run_name}/                 ← first run (no prior trajectories)
        results/{run_name}_20240318_221500/ ← second run (directory existed)

    When run_name is auto-generated it already embeds a timestamp, so no
    further disambiguation is needed.
    """
    if base_output_dir is None:
        base_output_dir = Path("results")

    results_dir = base_output_dir / run_name

    # If the directory exists and already contains trajectory files from a
    # previous run, suffix the directory name with the current timestamp so
    # the new run gets a clean, isolated output directory.
    if results_dir.exists():
        has_trajs = any(results_dir.rglob("*.traj"))
        if has_trajs:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = base_output_dir / f"{run_name}_{timestamp}"
            print(
                f"⚠️  Output directory already contains trajectories from a previous run.\n"
                f"   Writing this run's output to: {results_dir}"
            )

    results_dir.mkdir(parents=True, exist_ok=True)

    return results_dir


def generate_run_configs(
    config: BatchRunnerConfig,
    results_dir: Path,
) -> list[RunConfig]:
    """Generate all run configurations (models x modes x passes)."""
    runs = []

    instance_names = config.instance_names or [None]

    for model_name in config.model_names:
        model_safe = model_name.replace("/", "_").replace(":", "_")

        for mode_name, enable_ask, full_info in config.modes:
            for pass_num in range(1, config.passes + 1):
                for instance_name in instance_names:
                    # Create output directory path
                    if config.passes > 1:
                        base_dir = results_dir / model_safe / mode_name / f"pass_{pass_num}"
                    else:
                        base_dir = results_dir / model_safe / mode_name

                    output_dir = base_dir / instance_name if instance_name else base_dir

                    runs.append(
                        RunConfig(
                            instance_name=instance_name,
                            model_name=model_name,
                            mode_name=mode_name,
                            enable_ask=enable_ask,
                            full_info=full_info,
                            pass_number=pass_num,
                            output_dir=output_dir,
                        )
                    )

    return runs


def print_batch_plan(runs: list[RunConfig], results_dir: Path):
    """Print the batch run plan."""
    print(f"\n{'='*70}")
    print("🚀 Batch Run Plan")
    print(f"{'='*70}")
    print(f"   Results directory: {results_dir}")
    print(f"   Total runs: {len(runs)}")
    print()

    # Group by model
    by_model: dict[str, list[RunConfig]] = {}
    for run in runs:
        if run.model_name not in by_model:
            by_model[run.model_name] = []
        by_model[run.model_name].append(run)

    for model, model_runs in by_model.items():
        print(f"   📦 {model}:")
        # Group by mode
        by_mode: dict[str, list[RunConfig]] = {}
        for run in model_runs:
            if run.mode_name not in by_mode:
                by_mode[run.mode_name] = []
            by_mode[run.mode_name].append(run)

        for mode, mode_runs in by_mode.items():
            if len(mode_runs) > 1:
                print(f"      - {mode} (passes 1-{len(mode_runs)})")
            else:
                print(f"      - {mode}")

    print(f"{'='*70}\n")


def print_batch_summary(results: list[BatchResult], results_dir: Path):
    """Print summary of batch run results."""
    print(f"\n{'='*70}")
    print("📊 Batch Run Summary")
    print(f"{'='*70}")
    print(f"   Results directory: {results_dir}")
    print()

    # Group by model and mode
    for result in results:
        status = "✅" if result.success else "❌"
        pass_info = f" (pass {result.config.pass_number})" if result.config.pass_number > 1 else ""
        print(f"   {status} {result.config.model_name} / {result.config.mode_name}{pass_info}")
        print(f"      └─ {result.config.output_dir}")

    # Summary stats
    total = len(results)
    passed = sum(1 for r in results if r.success)
    failed = total - passed

    print()
    if failed > 0:
        print(f"   ⚠️  {failed}/{total} runs failed")
    else:
        print(f"   ✅ All {total} runs completed successfully")
    print(f"{'='*70}\n")


def save_batch_config(
    config: BatchRunnerConfig, results_dir: Path, extra_config: dict | None = None
):
    """Save batch configuration to results directory."""
    config_data = {
        "timestamp": datetime.now().isoformat(),
        "instance_names": config.instance_names,
        "model_names": config.model_names,
        "modes": [{"name": m[0], "enable_ask": m[1], "full_info": m[2]} for m in config.modes],
        "passes": config.passes,
        "run_name": config.run_name,
        "num_workers": config.num_workers,
    }

    if extra_config:
        config_data.update(extra_config)

    config_file = results_dir / "batch_config.json"
    with open(config_file, "w") as f:
        json.dump(config_data, f, indent=2, default=str)

    print(f"💾 Batch config saved to: {config_file}")


def save_batch_results(results: list[BatchResult], results_dir: Path):
    """Save batch results summary to results directory."""
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "total_runs": len(results),
        "successful_runs": sum(1 for r in results if r.success),
        "failed_runs": sum(1 for r in results if not r.success),
        "runs": [
            {
                "model_name": r.config.model_name,
                "mode_name": r.config.mode_name,
                "pass_number": r.config.pass_number,
                "output_dir": str(r.config.output_dir),
                "returncode": r.returncode,
                "success": r.success,
            }
            for r in results
        ],
    }

    results_file = results_dir / "batch_results.json"
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2)

    print(f"💾 Batch results saved to: {results_file}")


def load_run_metrics(output_dir: Path) -> dict | None:
    """
    Load metrics from a run's output directory.

    Looks for metrics.json in the output directory.
    """
    metrics_file = output_dir / "metrics.json"
    if metrics_file.exists():
        try:
            with open(metrics_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse metrics from {metrics_file}")
    return None


def load_run_predictions(output_dir: Path) -> dict | None:
    """
    Load predictions from a run's output directory.

    Looks for preds.json in the output directory.
    """
    preds_file = output_dir / "preds.json"
    if preds_file.exists():
        try:
            with open(preds_file, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse predictions from {preds_file}")
    return None


def aggregate_numeric_values(values: list[float | int]) -> dict:
    """
    Aggregate a list of numeric values into statistics.

    Returns:
        Dict with mean, std, min, max, and individual values
    """
    if not values:
        return {"mean": None, "std": None, "min": None, "max": None, "values": []}

    result = {
        "mean": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "values": values,
    }

    if len(values) > 1:
        result["std"] = statistics.stdev(values)
    else:
        result["std"] = 0.0

    return result


def collect_consolidated_metrics(results: list[BatchResult], config: BatchRunnerConfig) -> dict:
    """
    Collect and aggregate metrics from all completed runs.

    Structure:
        {
            "summary": {
                "total_runs": N,
                "successful_runs": M,
                "passes": K,
            },
            "by_model": {
                "model_name": {
                    "by_mode": {
                        "mode_name": {
                            "pass_at_1_rate": {"mean": X, "std": Y, "values": [...]},
                            "pass_at_1_count": {"mean": X, ...},
                            "total_cost": {"mean": X, ...},
                            # HIL metrics (if applicable)
                            "ask_f1": {"mean": X, ...},
                            "precision": {"mean": X, ...},
                            "recall": {"mean": X, ...},
                            # Per-pass raw metrics
                            "per_pass": [
                                {"pass": 1, "metrics": {...}},
                                ...
                            ]
                        }
                    },
                    # Aggregated across all modes
                    "aggregated": {...}
                }
            },
            "all_instance_results": [
                {
                    "instance_id": "...",
                    "model": "...",
                    "mode": "...",
                    "pass": 1,
                    "resolved": true/false,
                    "cost": X,
                    ...
                }
            ]
        }
    """
    # Organize results by model and mode
    by_model: dict[str, dict[str, list[tuple[BatchResult, dict | None]]]] = {}
    all_instance_results = []

    for result in results:
        model = result.config.model_name
        mode = result.config.mode_name

        if model not in by_model:
            by_model[model] = {}
        if mode not in by_model[model]:
            by_model[model][mode] = []

        # Load metrics for this run
        metrics = load_run_metrics(result.config.output_dir)
        by_model[model][mode].append((result, metrics))

        # Collect per-instance results
        if metrics:
            resolved_set = set(metrics.get("resolved_instances", []))
            instances_data = metrics.get("instances", {})

            for instance_id, instance_info in instances_data.items():
                # instances_data is keyed by traj file stems (full instance IDs).
                # resolved_instances also uses full instance IDs after _reorganize_mixed_results.
                instance_result = {
                    "instance_id": instance_id,
                    "model": model,
                    "mode": mode,
                    "pass": result.config.pass_number,
                    "resolved": instance_id in resolved_set,
                    "cost": instance_info.get("cost", 0),
                    "runtime": instance_info.get("runtime", 0),
                }
                all_instance_results.append(instance_result)

    # Aggregate metrics
    consolidated = {
        "summary": {
            "total_runs": len(results),
            "successful_runs": sum(1 for r in results if r.success),
            "failed_runs": sum(1 for r in results if not r.success),
            "passes": config.passes,
            "models": config.model_names,
            "modes": [m[0] for m in config.modes],
        },
        "by_model": {},
        "all_instance_results": all_instance_results,
    }

    # Metrics to aggregate (numeric values that should be averaged across passes)
    aggregate_keys = [
        "pass_at_1_rate",
        "pass_at_1_count",
        "patches_generated",
        "patch_generation_rate",
        "total_cost",
        "total_runtime",
    ]

    # HIL-specific metrics
    hil_keys = [
        "precision",
        "recall",
        "ask_f1",
        "n_questions",
        "n_blockers_present",
        "n_blockers_discovered",
    ]

    for model, modes_data in by_model.items():
        model_result = {"by_mode": {}}

        for mode, runs in modes_data.items():
            mode_result: dict = {"per_pass": []}

            # Collect values for each metric across passes
            metric_values: dict[str, list[float]] = {k: [] for k in aggregate_keys + hil_keys}

            for result, metrics in runs:
                pass_data: dict = {
                    "pass": result.config.pass_number,
                    "output_dir": str(result.config.output_dir),
                }

                if metrics:
                    pass_data["metrics"] = metrics

                    # Collect numeric values for aggregation
                    for key in aggregate_keys:
                        if key in metrics and metrics[key] is not None:
                            metric_values[key].append(float(metrics[key]))

                    # HIL metrics are nested under "hil_metrics"
                    hil_metrics = metrics.get("hil_metrics", {})
                    for key in hil_keys:
                        if key in hil_metrics and hil_metrics[key] is not None:
                            metric_values[key].append(float(hil_metrics[key]))

                mode_result["per_pass"].append(pass_data)

            # Add aggregated values
            for key, values in metric_values.items():
                if values:
                    mode_result[key] = aggregate_numeric_values(values)

            model_result["by_mode"][mode] = mode_result

        consolidated["by_model"][model] = model_result

    return consolidated


def save_consolidated_metrics(metrics: dict, results_dir: Path):
    """Save consolidated metrics to results directory."""
    metrics_file = results_dir / "consolidated_metrics.json"
    with open(metrics_file, "w") as f:
        json.dump(metrics, f, indent=2, default=str)

    print(f"💾 Consolidated metrics saved to: {metrics_file}")


def collect_consolidated_results(
    results: list[BatchResult], config: BatchRunnerConfig, task_type: str = "swe"
) -> dict:
    """
    Collect outputs and evaluation results from all completed runs.

    For each model/mode/pass/instance, collects:
    - output: the SQL query (for SQL) or patch (for SWE)
    - results: evaluation outcome including test status

    Args:
        results: List of batch run results
        config: Batch runner configuration
        task_type: Either "swe" or "sql" to determine output handling

    Returns:
        Dict with consolidated results structured by model/mode/pass/instance
    """
    consolidated = {
        "summary": {
            "total_runs": len(results),
            "successful_runs": sum(1 for r in results if r.success),
            "passes": config.passes,
            "models": config.model_names,
            "modes": [m[0] for m in config.modes],
            "task_type": task_type,
        },
        "instances": [],
    }

    for result in results:
        # NOTE: We include ALL runs, not just successful ones.
        # The agent may have produced a valid solution (preds.json) even if
        # evaluation failed. We want these solutions in consolidated_results.json
        # so that hil_bench_agent.py can:
        # 1. Display the agent's work in feedback
        # 2. Correctly attribute solutions to models
        # If predictions don't exist, we'll skip via the check below.

        model = result.config.model_name
        mode = result.config.mode_name
        pass_num = result.config.pass_number
        output_dir = result.config.output_dir

        # Load predictions (contains patches/SQL queries)
        predictions = load_run_predictions(output_dir)
        if not predictions:
            continue

        # Load metrics (contains evaluation results)
        metrics = load_run_metrics(output_dir)
        raw_eval_results = metrics.get("raw_eval_results", {}) if metrics else {}
        resolved_ids = set(metrics.get("resolved_instances", [])) if metrics else set()

        for instance_id, pred_data in predictions.items():
            # Get the output (patch for SWE, SQL query for SQL)
            output = pred_data.get("model_patch", "")

            # Extract original instance ID for display (strip model/mode/pass suffixes)
            original_id = extract_original_instance_id(instance_id, model, mode, pass_num)

            # Build the result entry. preds.json keys and resolved_instances both use full
            # instance IDs after _reorganize_mixed_results, so match directly on instance_id.
            instance_result = {
                "instance_id": instance_id,
                "original_instance_id": original_id,
                "model": model,
                "mode": mode,
                "pass": pass_num,
                "output": output,
                "resolved": instance_id in resolved_ids,
            }

            # Get evaluation results (keyed by full instance ID)
            eval_result = raw_eval_results.get("results", {}).get(instance_id, {})

            if task_type == "swe":
                # For SWE: include test status mapping
                # First try to get from eval_result in metrics.json
                result_data = eval_result.get("result", eval_result)
                test_status = result_data.get("tests_status", {})
                test_output = None

                # If test_status is empty, try to read from logs/run_evaluation report.json
                if metrics and not test_status:
                    instance_type = metrics.get("instance_type", "")
                    if instance_type == "custom":
                        # Build the log path pattern
                        path_parts = output_dir.parts[-4:]
                        run_id = "custom-eval." + ".".join(path_parts)
                        log_base = (
                            Path("logs/run_evaluation") / run_id / config.run_name / original_id
                        )

                        # Try to read report.json for test_status
                        report_path = log_base / "report.json"
                        if report_path.exists():
                            try:
                                with open(report_path, "r") as f:
                                    report_data = json.load(f)
                                    # report.json is keyed by instance_id
                                    instance_report = report_data.get(original_id, {})
                                    test_status = instance_report.get("tests_status", {})
                            except (json.JSONDecodeError, OSError):
                                pass

                        # Read test_output.txt for full test output
                        test_output_path = log_base / "test_output.txt"
                        if test_output_path.exists():
                            try:
                                test_output = test_output_path.read_text()
                            except OSError:
                                pass

                # Create a simple {test_name: true/false} mapping
                test_results = {}
                for category in ["FAIL_TO_PASS", "PASS_TO_PASS"]:
                    cat_data = test_status.get(category, {})
                    for test in cat_data.get("success", []):
                        test_results[test] = True
                    for test in cat_data.get("failure", []):
                        test_results[test] = False

                instance_result["results"] = {
                    "completed": eval_result.get("completed", False),
                    "resolved": eval_result.get("resolved", False),
                    "test_results": test_results,
                    "tests_status": test_status,
                }

                # Include full test output if available
                if test_output is not None:
                    instance_result["results"]["test_output"] = test_output

            elif task_type == "sql":
                instance_result["results"] = {
                    "status": "correct" if original_id in resolved_ids else "incorrect",
                    "error": eval_result.get("error") if eval_result else None,
                }

                # Load query results saved during pass@1 calculation
                query_results_file = output_dir / "sql_query_results.json"
                if query_results_file.exists():
                    try:
                        query_results = json.loads(query_results_file.read_text())
                        instance_query = query_results.get(instance_id) or query_results.get(
                            original_id, {}
                        )

                        if instance_query:
                            # Include ground truth query and result
                            if "gt_query" in instance_query:
                                instance_result["results"]["ground_truth_query"] = instance_query[
                                    "gt_query"
                                ]
                            if "gt_result" in instance_query:
                                instance_result["results"]["ground_truth_result"] = instance_query[
                                    "gt_result"
                                ]

                            # Include predicted query and result
                            if "pred_result" in instance_query:
                                instance_result["results"]["pred_query"] = instance_query[
                                    "pred_query"
                                ]
                                instance_result["results"]["pred_result"] = instance_query[
                                    "pred_result"
                                ]
                    except (json.JSONDecodeError, OSError):
                        pass

            consolidated["instances"].append(instance_result)

    return consolidated


def save_consolidated_results(results_data: dict, results_dir: Path):
    """Save consolidated results to results directory."""
    results_file = results_dir / "consolidated_results.json"
    with open(results_file, "w") as f:
        json.dump(results_data, f, indent=2, default=str)

    print(f"💾 Consolidated results saved to: {results_file}")


def print_consolidated_metrics_summary(metrics: dict):
    """Print a summary of consolidated metrics."""
    print(f"\n{'='*70}")
    print("📈 Consolidated Metrics Summary")
    print(f"{'='*70}")

    summary = metrics.get("summary", {})
    passes = summary.get("passes", 1)

    print(f"   Total runs: {summary.get('total_runs', 0)}")
    print(f"   Successful: {summary.get('successful_runs', 0)}")
    print(f"   Passes: {passes}")
    print()

    by_model = metrics.get("by_model", {})

    for model, model_data in by_model.items():
        print(f"   📦 {model}:")

        for mode, mode_data in model_data.get("by_mode", {}).items():
            pass_at_1 = mode_data.get("pass_at_1_rate", {})

            if pass_at_1 and pass_at_1.get("mean") is not None:
                mean = pass_at_1["mean"]
                std = pass_at_1.get("std", 0)

                if passes > 1:
                    values_str = ", ".join(f"{v:.1f}%" for v in pass_at_1.get("values", []))
                    print(f"      {mode}: pass@1 = {mean:.1f}% ± {std:.1f}% [{values_str}]")
                else:
                    print(f"      {mode}: pass@1 = {mean:.1f}%")

                # Print HIL metrics if available
                ask_f1 = mode_data.get("ask_f1", {})
                if ask_f1 and ask_f1.get("mean") is not None:
                    f1_mean = ask_f1["mean"]
                    if passes > 1:
                        f1_std = ask_f1.get("std", 0)
                        print(f"             ask_f1 = {f1_mean:.2%} ± {f1_std:.2%}")
                    else:
                        print(f"             ask_f1 = {f1_mean:.2%}")

                # Print cost if available
                total_cost = mode_data.get("total_cost", {})
                if total_cost and total_cost.get("mean") is not None:
                    cost_mean = total_cost["mean"]
                    print(f"             cost = ${cost_mean:.2f}")
            else:
                print(f"      {mode}: (no metrics available)")

        print()

    print(f"{'='*70}\n")


def run_batch(
    config: BatchRunnerConfig,
    run_fn: Callable[[RunConfig, int, int], int],
    extra_config: dict | None = None,
) -> list[BatchResult]:
    """
    Execute a batch of runs.

    Args:
        config: Batch runner configuration
        run_fn: Function to execute a single run. Takes (run_config, run_index, total_runs)
                and returns exit code.
        extra_config: Additional configuration to save (e.g., instances_file, task_folder)

    Returns:
        List of BatchResult objects
    """
    # Generate run name if not provided
    run_name = config.run_name or generate_run_name(config.model_names, config.modes)

    # Create results directory
    results_dir = create_results_directory(run_name, config.base_output_dir)

    # Generate all run configurations
    runs = generate_run_configs(config, results_dir)

    # Print plan
    print_batch_plan(runs, results_dir)

    # Save batch config
    save_batch_config(config, results_dir, extra_config)

    # Execute runs
    results = []
    for i, run_config in enumerate(runs):
        print(f"\n{'='*70}")
        pass_info = f", pass {run_config.pass_number}" if config.passes > 1 else ""
        print(
            f"[{i+1}/{len(runs)}] Running: {run_config.model_name} ({run_config.mode_name}{pass_info})"
        )
        print(f"{'='*70}\n")

        # Create output directory
        run_config.output_dir.mkdir(parents=True, exist_ok=True)

        # Execute run
        returncode = run_fn(run_config, i, len(runs))
        results.append(BatchResult(config=run_config, returncode=returncode))

    # Save run results summary
    save_batch_results(results, results_dir)

    # Collect and save consolidated metrics
    consolidated_metrics = collect_consolidated_metrics(results, config)
    save_consolidated_metrics(consolidated_metrics, results_dir)

    # Collect and save consolidated results (outputs and evaluation results)
    task_type = extra_config.get("task_type", "swe") if extra_config else "swe"
    consolidated_results = collect_consolidated_results(results, config, task_type)
    save_consolidated_results(consolidated_results, results_dir)

    # Print summaries
    print_batch_summary(results, results_dir)
    print_consolidated_metrics_summary(consolidated_metrics)

    return results


def get_modes_from_flags(
    ask_human: bool = False,
    full_info: bool = False,
    all_modes: bool = False,
) -> list[tuple[str, bool, bool]]:
    """
    Get list of modes to run based on CLI flags.

    Returns:
        List of (mode_name, enable_ask, full_info) tuples
    """
    if all_modes:
        return [
            ("baseline", False, False),
            ("ask_human", True, False),
            ("full_info", False, True),
        ]

    modes = []
    if ask_human:
        modes.append(("ask_human", True, False))
    if full_info:
        modes.append(("full_info", False, True))
    if not modes:
        modes.append(("baseline", False, False))
    return modes


def _run_batch(
    instances_path: Path,
    model_names: list[str],
    modes: list[tuple[str, bool, bool]],
    passes: int,
    task_folder: Path,
    task_type: str,
    num_workers: int = 5,
    num_tasks: int | None = None,
    per_instance_cost_limit: float = 5.0,
    redo_existing: bool = True,
    cleanup_docker: bool = True,
    cleanup_trajectories: bool = False,
    dataset_name: str = "princeton-nlp/SWE-bench_Verified",
    run_name: str | None = None,
    base_output_dir: Path | None = None,
    config_mapping: Path | None = None,
    judge_config: Path | None = None,
    extra_kwargs: dict | None = None,
) -> int:
    """
    Unified batch runner for both SWE and SQL task types.

    This function consolidates the shared logic between SWE and SQL batch runs,
    handling all the common operations:
    - Creating results directory
    - Building model configs
    - Running sweagent batch
    - Computing metrics
    - Saving consolidated results

    Args:
        instances_path: Path to instances.json file
        model_names: List of model names to run
        modes: List of (mode_name, enable_ask, full_info) tuples
        passes: Number of passes per configuration
        task_folder: Directory containing task subdirectories
        task_type: Either "swe" or "sql"
        num_workers: Number of parallel workers
        num_tasks: Optional limit on number of tasks
        per_instance_cost_limit: Cost limit per instance
        redo_existing: Whether to re-run existing results
        cleanup_docker: Whether to clean up stale Docker containers
        cleanup_trajectories: Whether to clean up old trajectories
        dataset_name: Dataset name for evaluation
        run_name: Optional run name (auto-generated if not provided)
        base_output_dir: Base output directory (default: "results")
        config_mapping: Required mapping file path for task_type/mode/model configs
        judge_config: Optional ask_human judge config path (required for ask_human mode)
        extra_kwargs: Additional kwargs to pass to run_sweagent_batch

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    load_dotenv()

    # Import here to avoid circular imports
    from .swe import _reorganize_mixed_results, run_sweagent_batch

    # Generate run name and create results directory
    run_name = run_name or generate_run_name(model_names, modes)
    if base_output_dir is None:
        base_output_dir = Path("results")
    results_dir = create_results_directory(run_name, base_output_dir)

    # Load instances
    original_instances = json.loads(instances_path.read_text())
    if num_tasks:
        original_instances = original_instances[:num_tasks]

    # Build model_configs list for mixed batch
    model_configs = []
    for model_name in model_names:
        for mode_name, enable_ask, full_info in modes:
            model_configs.append((model_name, mode_name, enable_ask, full_info))

    if config_mapping is None:
        raise ValueError("--config-mapping is required")
    needs_ask_human = any(enable_ask for _, _, enable_ask, _ in model_configs)
    if needs_ask_human and judge_config is None:
        raise ValueError("--judge-config is required when ask_human mode is selected")
    if needs_ask_human and judge_config is not None:
        load_and_apply_judge_config(Path(judge_config).resolve())

    mapping_path = Path(config_mapping).resolve()
    project_root = Path(__file__).parent.parent.parent
    mapping_data = load_config_mapping(mapping_path, project_root)
    resolved_agent_configs: dict[tuple[str, str], str] = {}
    for model_name, mode_name, _enable_ask, _full_info in model_configs:
        resolved_path = resolve_agent_config_path(
            mapping_data,
            task_type=task_type,
            mode=mode_name,
            model_name=model_name,
            mapping_file=mapping_path,
            project_root=project_root,
        )
        resolved_agent_configs[(model_name, mode_name)] = str(resolved_path)
    checked_paths = set()
    for resolved_path in resolved_agent_configs.values():
        if resolved_path in checked_paths:
            continue
        checked_paths.add(resolved_path)
        validate_agent_hosting_config(resolved_path)

    total_combinations = len(model_configs)
    total_instance_runs = total_combinations * passes * len(original_instances)

    # Print batch plan
    task_label = "SQL" if task_type == "sql" else "SWE"
    print(f"\n{'='*70}")
    print(f"🚀 {task_label} Batch Run Plan (Single Call - All Models/Modes)")
    print(f"{'='*70}")
    print(f"   Results directory: {results_dir}")
    print(f"   Models: {len(model_names)}")
    print(f"   Modes: {len(modes)}")
    print(f"   Passes: {passes}")
    print(f"   Instances: {len(original_instances)}")
    print("   Total sweagent calls: 1")
    print(f"   Total instance runs: {total_instance_runs}")
    print()

    for model in model_names:
        print(f"   📦 {model}:")
        for mode_name, enable_ask, full_info in modes:
            mode_desc = mode_name
            if enable_ask:
                mode_desc += " (ask_human)"
            elif full_info:
                mode_desc += " (full info in prompt)"
            print(f"      - {mode_desc}: {passes} passes × {len(original_instances)} instances")

    print(f"{'='*70}\n")

    # Save batch config
    config = BatchRunnerConfig(
        model_names=model_names,
        modes=modes,
        passes=passes,
        run_name=run_name,
        base_output_dir=base_output_dir,
        num_workers=num_workers,
        cleanup_docker=cleanup_docker,
        cleanup_trajectories=cleanup_trajectories,
    )
    extra_config = {
        "instances_file": str(instances_path),
        "task_folder": str(task_folder),
        "per_instance_cost_limit": per_instance_cost_limit,
        "optimization": "single_batch_mixed",
        "task_type": task_type,
    }
    if num_tasks is not None:
        extra_config["num_tasks"] = num_tasks
    if dataset_name:
        extra_config["dataset"] = dataset_name
    extra_config["config_mapping"] = str(mapping_path)
    if judge_config is not None:
        extra_config["judge_config"] = str(Path(judge_config).resolve())
    save_batch_config(config, results_dir, extra_config)

    # Determine instances_type based on task type.
    instances_type = "expert_file" if task_type in ("sql", "add_business_info") else "file"

    # Run the batch
    # Extract max_steps and enable_model_call_logging from extra_kwargs (passed from CLI)
    kwargs = extra_kwargs.copy() if extra_kwargs else {}
    max_steps = kwargs.pop("agent.max_steps", None)
    enable_model_call_logging = kwargs.pop("model.enable_model_call_logging", False)

    returncode, ask_human_logs = run_sweagent_batch(
        instances_file=instances_path,
        model_configs=model_configs,
        output_dir=results_dir,
        task_folder=task_folder,
        num_workers=num_workers,
        num_tasks=num_tasks,
        per_instance_cost_limit=per_instance_cost_limit,
        max_steps=max_steps,
        enable_model_call_logging=enable_model_call_logging,
        redo_existing=redo_existing,
        cleanup_docker=cleanup_docker,
        cleanup_trajectories=cleanup_trajectories,
        dataset_name=dataset_name,
        passes=passes,
        resolved_agent_configs=resolved_agent_configs,
        judge_config=Path(judge_config).resolve() if judge_config is not None else None,
        task_type=task_type,
        instances_type=instances_type,
        **kwargs,
    )
    if returncode != 0:
        print(
            "\n❌ Batch execution failed before evaluation; skipping metrics/summary computation.",
            file=sys.stderr,
        )
        return returncode

    # Reorganize results into model/mode/pass structure
    _reorganize_mixed_results(results_dir, model_configs, passes)

    # Compute metrics for each model/mode/pass configuration
    print("\n📊 Computing metrics for each configuration...")

    # For SWE task type, clear the rebuilt images cache.
    if task_type == "swe":
        from hil_bench.utils.custom_eval import clear_rebuilt_images_cache

        clear_rebuilt_images_cache()

    # List of eval configs to run in parallel
    eval_configs = []
    for model_name, mode_name, enable_ask, full_info in model_configs:
        model_safe = model_name.replace("/", "_").replace(":", "_")
        for pass_num in range(1, passes + 1):
            if passes > 1:
                pass_output_dir = results_dir / model_safe / mode_name / f"pass_{pass_num}"
            else:
                pass_output_dir = results_dir / model_safe / mode_name
            eval_configs.append(
                (model_name, mode_name, enable_ask, full_info, pass_num, pass_output_dir)
            )

    def _run_single_eval(
        eval_config: tuple[str, str, bool, bool, int, Path],
    ) -> dict[str, Any]:
        """
        Run evaluation for a single model/mode/pass configuration.
        Returns a dict with all info needed to build BatchResult and print summary.
        """
        model_name, mode_name, enable_ask, full_info, pass_num, pass_output_dir = eval_config
        model_safe = model_name.replace("/", "_").replace(":", "_")
        result_info: dict[str, Any] = {
            "model_name": model_name,
            "mode_name": mode_name,
            "enable_ask": enable_ask,
            "full_info": full_info,
            "pass_num": pass_num,
            "pass_output_dir": pass_output_dir,
            "metrics": None,
            "error": None,
        }
        if not (pass_output_dir.exists() and (pass_output_dir / "preds.json").exists()):
            return result_info
        try:
            if task_type == "swe":
                from hil_bench.utils.calculate_pass_at_1 import calculate_pass_at_1

                metrics = calculate_pass_at_1(
                    trajectory_dir=str(pass_output_dir),
                    dataset_name=dataset_name,
                    max_workers=1,  # single worker because we're already parallel at this level
                    tasks_dir=str(task_folder) if task_folder else None,
                )
            elif task_type == "sql":
                from hil_bench.utils.calculate_sql_pass_at_1 import calculate_sql_pass_at_1

                metrics = calculate_sql_pass_at_1(
                    trajectory_dir=str(pass_output_dir),
                    tasks_dir=str(task_folder),
                    max_workers=1,  # single worker because we're already parallel at this level
                    instances_file=str(instances_path),
                )

                # Save query results separately for consolidated_results.json and remove them from metrics
                if "results" in metrics:
                    query_results = {}
                    for inst_id, inst_result in metrics["results"].items():
                        query_data = {}
                        for key in [
                            "gt_query",
                            "pred_query",
                            "gt_result",
                            "pred_result",
                            "gt_result_csv",
                            "pred_result_csv",
                        ]:
                            if key in inst_result:
                                query_data[key] = inst_result.pop(key)
                        if query_data:
                            query_results[inst_id] = query_data

                    if query_results:
                        query_results_file = pass_output_dir / "sql_query_results.json"
                        query_results_file.write_text(
                            json.dumps(query_results, indent=2, default=str)
                        )
                        for inst_id, query_data in query_results.items():
                            if "gt_result_csv" in query_data:
                                gt_csv_file = pass_output_dir / f"{inst_id}_gt_result.csv"
                                gt_csv_file.write_text(query_data["gt_result_csv"])
                            if "pred_result_csv" in query_data:
                                pred_csv_file = pass_output_dir / f"{inst_id}_pred_result.csv"
                                pred_csv_file.write_text(query_data["pred_result_csv"])
            else:
                # Fallback for unknown task types
                with open(pass_output_dir / "preds.json", "r") as f:
                    preds = json.load(f)
                metrics = {
                    "total_instances": len(preds),
                    "patches_generated": sum(1 for p in preds.values() if p.get("model_patch")),
                }

            # Compute HIL metrics for ask_human mode
            if enable_ask:
                mode_safe = mode_name.replace("-", "_")
                pass_suffix = f"__pass_{pass_num}" if passes > 1 else ""
                pattern_suffix = f"__{model_safe}__{mode_safe}{pass_suffix}"

                filtered_logs = {}
                if ask_human_logs:
                    filtered_logs = {k: v for k, v in ask_human_logs.items() if pattern_suffix in k}

                if filtered_logs:
                    from hil_bench.utils.compute_hil_metrics import compute_hil_metrics

                    hil_metrics = compute_hil_metrics(filtered_logs)
                    metrics["hil_metrics"] = hil_metrics

                    # Save filtered logs for this pass directory
                    pass_logs_file = pass_output_dir / "ask_human_logs.json"
                    pass_logs_file.write_text(json.dumps(filtered_logs, indent=2))
                else:
                    # No questions asked - compute zero metrics
                    # Count blockers from task folder or instance data
                    try:
                        from hil_bench.utils.compute_hil_metrics import (
                            compute_zero_hil_metrics,
                            get_n_blockers_from_registry,
                        )

                        n_blockers = get_n_blockers_from_registry(
                            str(task_folder) if task_folder else None
                        )
                        metrics["hil_metrics"] = compute_zero_hil_metrics(n_blockers)
                    except Exception:
                        metrics["hil_metrics"] = {
                            "precision": 0.0,
                            "recall": 0.0,
                            "ask_f1": 0.0,
                            "n_questions": 0,
                            "n_blockers_present": 0,
                            "n_blockers_discovered": 0,
                        }

            # Save metrics
            metrics_file = pass_output_dir / "metrics.json"
            metrics_file.write_text(json.dumps(metrics, indent=2))

            result_info["metrics"] = metrics
        except Exception as e:
            result_info["error"] = str(e)
        return result_info

    print(f"🔄 Running {len(eval_configs)} evaluations in parallel with {num_workers} workers...")
    eval_results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_config = {
            executor.submit(_run_single_eval, config): config for config in eval_configs
        }
        for future in as_completed(future_to_config):
            try:
                result_info = future.result()
                eval_results.append(result_info)
            except Exception as e:
                config = future_to_config[future]
                eval_results.append(
                    {
                        "model_name": config[0],
                        "mode_name": config[1],
                        "enable_ask": config[2],
                        "full_info": config[3],
                        "pass_num": config[4],
                        "pass_output_dir": config[5],
                        "metrics": None,
                        "error": f"Future exception: {e}",
                    }
                )

    eval_results.sort(key=lambda r: (r["model_name"], r["mode_name"], r["pass_num"]))

    all_results = []
    for result_info in eval_results:
        model_name = result_info["model_name"]
        mode_name = result_info["mode_name"]
        enable_ask = result_info["enable_ask"]
        full_info = result_info["full_info"]
        pass_num = result_info["pass_num"]
        pass_output_dir = result_info["pass_output_dir"]
        metrics = result_info["metrics"]
        error = result_info["error"]
        if error:
            print(f"   ⚠️  {model_name} / {mode_name} pass {pass_num}: metrics failed - {error}")
        elif metrics:
            hil = metrics.get("hil_metrics", {})
            if task_type in ("swe", "sql"):
                pass_rate = metrics.get("pass_at_1_rate", 0)
                if hil:
                    ask_f1 = hil.get("ask_f1", 0)
                    print(
                        f"   ✅ {model_name} / {mode_name} pass {pass_num}: "
                        f"{pass_rate:.1f}% pass@1, {ask_f1:.1%} ask_f1"
                    )
                else:
                    print(
                        f"   ✅ {model_name} / {mode_name} pass {pass_num}: "
                        f"{pass_rate:.1f}% pass@1"
                    )
            else:
                total = metrics.get("total_instances", 0)
                generated = metrics.get("patches_generated", 0)
                if hil:
                    ask_f1 = hil.get("ask_f1", 0)
                    print(
                        f"   ✅ {model_name} / {mode_name} pass {pass_num}: "
                        f"{generated}/{total} queries, {ask_f1:.1%} ask_f1"
                    )
                else:
                    print(
                        f"   ✅ {model_name} / {mode_name} pass {pass_num}: "
                        f"{generated}/{total} queries generated"
                    )

        run_config = RunConfig(
            instance_name=None,
            model_name=model_name,
            mode_name=mode_name,
            enable_ask=enable_ask,
            full_info=full_info,
            pass_number=pass_num,
            output_dir=pass_output_dir,
        )
        all_results.append(BatchResult(config=run_config, returncode=returncode))

    # Collect and save consolidated metrics + results
    consolidated_metrics = collect_consolidated_metrics(all_results, config)
    save_consolidated_metrics(consolidated_metrics, results_dir)
    consolidated_results = collect_consolidated_results(all_results, config, task_type)
    save_consolidated_results(consolidated_results, results_dir)

    # Print summary
    print(f"\n{'='*70}")
    print(f"📊 {task_label} Batch Run Summary")
    print(f"{'='*70}")
    print(f"   Results directory: {results_dir}")
    print("   Sweagent calls made: 1")
    print()

    for result in all_results:
        status = "✅" if result.success else "❌"
        pass_info = f" (pass {result.config.pass_number})" if passes > 1 else ""
        print(f"   {status} {result.config.model_name} / {result.config.mode_name}{pass_info}")

    print(f"{'='*70}\n")

    print_consolidated_metrics_summary(consolidated_metrics)

    # Return exit code
    failed = sum(1 for r in all_results if not r.success)
    return 1 if failed > 0 else 0
