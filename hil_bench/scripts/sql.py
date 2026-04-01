import os
import sys
from pathlib import Path

from .batch_runner import _run_batch, get_modes_from_flags

PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_sql_command(args):
    """Handle sql command - uses same batching as SWE."""
    # Set HF_HOME and related cache directory defaults
    if not os.environ.get("HF_HOME"):
        os.environ["HF_HOME"] = "/tmp/huggingface_cache"

    hf_home = os.environ["HF_HOME"]
    for var in ["HUGGINGFACE_HUB_CACHE", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME"]:
        if not os.environ.get(var):
            os.environ[var] = hf_home

    models = args.models
    passes = args.passes
    enable_ask = args.ask_human
    full_info = args.full_info
    all_modes = getattr(args, "all_modes", False)
    max_runtime = getattr(args, "max_runtime", None)

    # Handle run_name
    run_name = getattr(args, "run_name", None) or getattr(args, "batch_session_name", None)

    # Get modes to run
    modes = get_modes_from_flags(
        ask_human=enable_ask,
        full_info=full_info,
        all_modes=all_modes,
    )

    # Resolve the input path (like SWE command)
    input_path = args.path.resolve()
    if not input_path.exists():
        print(f"❌ Path not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # If path is a directory, look for instances.json inside it
    if input_path.is_dir():
        instances_path = input_path / "instances.json"
        if not instances_path.exists():
            print(f"❌ No instances.json found in {input_path}", file=sys.stderr)
            sys.exit(1)
    else:
        instances_path = input_path

    # Determine task folder (directory containing the instances file)
    task_folder = instances_path.parent

    extra_kwargs = {}
    if max_runtime is not None:
        extra_kwargs["agent.tools.total_execution_timeout"] = max_runtime
    max_steps = getattr(args, "max_steps", None)
    if max_steps is not None:
        extra_kwargs["agent.max_steps"] = max_steps
    enable_model_call_logging = getattr(args, "enable_model_call_logging", False)
    if enable_model_call_logging:
        extra_kwargs["model.enable_model_call_logging"] = True

    # Get per-instance cost limit from args (defaults to 2.5 for SQL)
    per_instance_cost_limit = getattr(args, "per_instance_cost_limit", 2.5)

    # Get output directory from args (default: results/).
    # Resolve to absolute so the path stays valid when the subprocess cwd changes.
    base_output_dir = (
        Path(args.output_dir).resolve()
        if getattr(args, "output_dir", None)
        else Path("results").resolve()
    )

    # Run the batch using the shared function
    exit_code = _run_batch(
        instances_path=instances_path,
        model_names=models,
        modes=modes,
        passes=passes,
        task_folder=task_folder,
        task_type="sql",
        num_workers=args.num_workers,
        per_instance_cost_limit=per_instance_cost_limit,
        cleanup_docker=args.cleanup_docker,
        cleanup_trajectories=False,
        dataset_name="sql",
        run_name=run_name,
        base_output_dir=base_output_dir,
        config_mapping=Path(args.config_mapping),
        judge_config=Path(args.judge_config) if args.judge_config else None,
        extra_kwargs=extra_kwargs,
    )
    sys.exit(exit_code)
