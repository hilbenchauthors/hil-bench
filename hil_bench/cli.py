import argparse
import json
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from .scripts.batch_runner import get_modes_from_flags
from .scripts.sql import run_sql_command
from .scripts.swe import create_single_instance_file, resolve_swe_input_path

load_dotenv()


def _validate_mode_flags(args) -> None:
    """Enforce that --all-modes is exclusive with individual mode flags."""
    if args.all_modes and (getattr(args, "ask_human", False) or getattr(args, "full_info", False)):
        print(
            "Error: --all-modes cannot be combined with --ask-human or --full-info",
            file=sys.stderr,
        )
        sys.exit(1)


def sql_command(args):
    """Handle sql command with mode-flag validation."""
    _validate_mode_flags(args)
    run_sql_command(args)


def swe_command(args):
    """Handle swe command."""
    _validate_mode_flags(args)
    path = args.path.resolve()
    input_type, resolved_path, task_folder, temp_instances_file = resolve_swe_input_path(
        path, max_tasks=args.num_tasks
    )

    modes = get_modes_from_flags(
        ask_human=args.ask_human,
        full_info=args.full_info,
        all_modes=args.all_modes,
    )
    model_names = args.model_names
    passes = args.passes

    kwargs = {}
    if args.max_runtime is not None:
        kwargs["agent.tools.total_execution_timeout"] = args.max_runtime
    if args.max_steps is not None:
        kwargs["agent.max_steps"] = args.max_steps
    if args.enable_model_call_logging:
        kwargs["model.enable_model_call_logging"] = True

    instances_path = resolved_path
    try:
        if input_type == "single":
            instance = create_single_instance_file(resolved_path, full_info=False)
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir="/tmp")
            tmp.write(json.dumps([instance], indent=2))
            tmp.close()
            temp_instances_file = Path(tmp.name)
            instances_path = temp_instances_file

        from .scripts.batch_runner import _run_batch

        exit_code = _run_batch(
            instances_path=instances_path,
            model_names=model_names,
            modes=modes,
            passes=passes,
            task_folder=task_folder,
            task_type="swe",
            num_workers=args.num_workers,
            num_tasks=args.num_tasks,
            per_instance_cost_limit=args.per_instance_cost_limit,
            redo_existing=not args.no_redo,
            cleanup_docker=args.cleanup_docker,
            cleanup_trajectories=args.cleanup_trajectories,
            dataset_name=args.dataset,
            run_name=args.run_name,
            base_output_dir=Path(args.output_dir) if args.output_dir else None,
            config_mapping=Path(args.config_mapping),
            judge_config=Path(args.judge_config) if args.judge_config else None,
            extra_kwargs=kwargs,
        )
        sys.exit(exit_code)
    finally:
        if temp_instances_file and temp_instances_file.exists():
            temp_instances_file.unlink()


def main():
    parser = argparse.ArgumentParser(
        description="HIL-Bench: Human-in-the-Loop Benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    sql_parser = subparsers.add_parser("sql", help="Run HIL-Bench SQL task type")
    sql_parser.add_argument("path", type=Path, help="Path to instances.json file for SQL tasks")
    sql_parser.add_argument("--model", "-m", dest="models", nargs="+", required=True)
    sql_parser.add_argument("--passes", "-k", type=int, default=3)
    sql_parser.add_argument("--config-template", default=None)
    sql_parser.add_argument("--run-name", type=str, default=None)
    sql_parser.add_argument("--batch-session-name", type=str, default=None)
    sql_parser.add_argument(
        "--num-tasks",
        "-n",
        type=int,
        default=None,
        help="Run only the first N SQL instances from the input instances file.",
    )
    sql_parser.add_argument("--num-workers", "-w", type=int, default=15)
    sql_parser.add_argument("--ask-human", action="store_true")
    sql_parser.add_argument("--full-info", action="store_true")
    sql_parser.add_argument("--all-modes", action="store_true")
    sql_parser.add_argument("--cleanup-docker", action="store_true", default=True)
    sql_parser.add_argument("--no-cleanup-docker", dest="cleanup_docker", action="store_false")
    sql_parser.add_argument("--max-runtime", type=int, default=None)
    sql_parser.add_argument("--per-instance-cost-limit", type=float, default=2.5)
    sql_parser.add_argument("--output-dir", "-o", type=Path, default=None)
    sql_parser.add_argument("--max-steps", type=int, default=None)
    sql_parser.add_argument("--enable-model-call-logging", action="store_true")
    sql_parser.add_argument(
        "--config-mapping",
        type=Path,
        required=True,
        help="YAML mapping task_type/mode/model to full agent config path.",
    )
    sql_parser.add_argument(
        "--judge-config",
        type=Path,
        default=None,
        help="YAML config for ask_human judge backend/model/hosting.",
    )
    sql_parser.set_defaults(func=sql_command)

    swe_parser = subparsers.add_parser("swe", help="Run SWE-agent on HIL-Bench tasks")
    swe_parser.add_argument("path", type=Path)
    swe_parser.add_argument("--model", "-m", dest="model_names", nargs="+", required=True)
    swe_parser.add_argument("--output-dir", "-o", type=Path, default=None)
    swe_parser.add_argument("--ask-human", action="store_true")
    swe_parser.add_argument("--full-info", action="store_true")
    swe_parser.add_argument("--all-modes", action="store_true")
    swe_parser.add_argument("--passes", "-k", type=int, default=1)
    swe_parser.add_argument("--run-name", type=str, default=None)
    swe_parser.add_argument("--num-tasks", "-n", type=int, default=None)
    swe_parser.add_argument("--num-workers", "-w", type=int, default=10)
    swe_parser.add_argument("--per-instance-cost-limit", type=float, default=5.0)
    swe_parser.add_argument("--max-runtime", type=int, default=None)
    swe_parser.add_argument("--no-redo", action="store_true")
    swe_parser.add_argument("--cleanup-docker", action="store_true", default=True)
    swe_parser.add_argument("--no-cleanup-docker", dest="cleanup_docker", action="store_false")
    swe_parser.add_argument("--cleanup-trajectories", action="store_true", default=False)
    swe_parser.add_argument("--dataset", default="princeton-nlp/SWE-bench_Verified")
    swe_parser.add_argument("--max-steps", type=int, default=None)
    swe_parser.add_argument("--enable-model-call-logging", action="store_true")
    swe_parser.add_argument(
        "--config-mapping",
        type=Path,
        required=True,
        help="YAML mapping task_type/mode/model to full agent config path.",
    )
    swe_parser.add_argument(
        "--judge-config",
        type=Path,
        default=None,
        help="YAML config for ask_human judge backend/model/hosting.",
    )
    swe_parser.set_defaults(func=swe_command)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
