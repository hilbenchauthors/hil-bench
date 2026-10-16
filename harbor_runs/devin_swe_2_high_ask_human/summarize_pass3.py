#!/usr/bin/env python3
"""Compute HiL-Bench pass@3 accuracy and micro ask-human metrics."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_trial_rewards(job_dir: Path) -> list[tuple[str, dict[str, Any]]]:
    trials: list[tuple[str, dict[str, Any]]] = []
    for result_path in sorted(job_dir.glob("*/result.json")):
        result = json.loads(result_path.read_text())
        task_name = result["task_name"]
        verifier_result = result.get("verifier_result")
        rewards = verifier_result.get("rewards") if verifier_result else None
        if not isinstance(rewards, dict):
            raise ValueError(f"{result_path}: missing verifier rewards")
        trials.append((task_name, rewards))
    return trials


def summarize(
    trials: list[tuple[str, dict[str, Any]]],
    *,
    expected_tasks: int = 200,
    attempts_per_task: int = 3,
) -> dict[str, Any]:
    expected_trials = expected_tasks * attempts_per_task
    if len(trials) != expected_trials:
        raise ValueError(f"expected {expected_trials} trials, found {len(trials)}")

    successes: dict[str, list[int]] = defaultdict(list)
    total_questions = 0
    total_blockers = 0
    total_blockers_resolved = 0

    for task_name, rewards in trials:
        solve_key = "solve" if "solve" in rewards else "resolved"
        successes[task_name].append(int(rewards[solve_key]))
        for metric in ("n_questions", "n_blockers", "blockers_resolved"):
            if metric not in rewards:
                raise ValueError(f"{task_name}: missing {metric}")
        total_questions += int(rewards["n_questions"])
        total_blockers += int(rewards["n_blockers"])
        total_blockers_resolved += int(rewards["blockers_resolved"])

    if len(successes) != expected_tasks:
        raise ValueError(f"expected {expected_tasks} tasks, found {len(successes)}")
    wrong_attempts = {
        task_name: len(values)
        for task_name, values in successes.items()
        if len(values) != attempts_per_task
    }
    if wrong_attempts:
        raise ValueError(
            f"tasks without exactly {attempts_per_task} attempts: {wrong_attempts}"
        )

    solved_tasks = sum(any(values) for values in successes.values())
    precision = total_blockers_resolved / total_questions if total_questions else 0.0
    recall = total_blockers_resolved / total_blockers if total_blockers else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "n_tasks": expected_tasks,
        "attempts_per_task": attempts_per_task,
        "n_trials": len(trials),
        "tasks_solved_at_least_once": solved_tasks,
        "accuracy_pass_at_3": solved_tasks / expected_tasks,
        "total_questions": total_questions,
        "total_blockers": total_blockers,
        "total_blockers_resolved": total_blockers_resolved,
        "micro_precision": precision,
        "micro_recall": recall,
        "micro_f1": f1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job_dir", type=Path)
    args = parser.parse_args()

    summary = summarize(load_trial_rewards(args.job_dir))
    output_path = args.job_dir / "pass3-summary.json"
    output_path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print(f"Summary written to {output_path}")


if __name__ == "__main__":
    main()
