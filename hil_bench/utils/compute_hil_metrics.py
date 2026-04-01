"""
Compute HIL-Bench metrics from SWE-agent runs.

Calculates human-in-the-loop specific metrics:
- Total questions asked via ask_human
- Number of blockers discovered
- Ask precision, recall, and F1 scores
"""

from __future__ import annotations

from typing import TypedDict

from ..ask_human_server import Log


class GlobalMetrics(TypedDict):
    instances: dict[str, Log]
    precision: float
    recall: float
    ask_f1: float
    n_questions: int
    n_blockers_present: int
    n_blockers_discovered: int


def compute_hil_metrics(
    logs: dict[str, Log],
) -> GlobalMetrics:
    """
    Compute HIL metrics from server logs.

    Args:
        logs: Dictionary of logs from ask_human_server

    Returns:
        Dictionary with global metrics and logs with (instance) metrics added
    """
    total_questions = 0
    total_blockers_present = 0
    total_blockers_discovered = 0

    for log_data in logs.values():
        n_blockers = log_data["n_blockers"]
        # Support both old "entries" key and new "questions" key for backwards compatibility
        questions = log_data.get("questions") or log_data.get("entries", [])

        n_discovered = len({name for e in questions if (name := e["blocker_name"]) is not None})
        n_questions = len(questions)

        precision = n_discovered / n_questions if n_questions > 0 else 0.0
        recall = n_discovered / n_blockers if n_blockers > 0 else 0.0
        ask_f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        log_data["precision"] = precision
        log_data["recall"] = recall
        log_data["ask_f1"] = ask_f1

        total_questions += n_questions
        total_blockers_present += n_blockers
        total_blockers_discovered += n_discovered

    global_precision = total_blockers_discovered / total_questions if total_questions > 0 else 0.0
    global_recall = (
        total_blockers_discovered / total_blockers_present if total_blockers_present > 0 else 0.0
    )
    global_ask_f1 = (
        2 * (global_precision * global_recall) / (global_precision + global_recall)
        if (global_precision + global_recall) > 0
        else 0.0
    )

    return {
        "instances": logs,
        "precision": global_precision,
        "recall": global_recall,
        "ask_f1": global_ask_f1,
        "n_questions": total_questions,
        "n_blockers_present": total_blockers_present,
        "n_blockers_discovered": total_blockers_discovered,
    }


def print_hil_metrics_summary(metrics: GlobalMetrics):
    """Print a summary of HIL metrics."""
    print()
    print("=" * 80)
    print("HIL-Bench Metrics Summary")
    print("=" * 80)

    print(f"# questions asked:\t{metrics['n_questions']}")
    print(f"# blockers:\t\t{metrics['n_blockers_present']}")
    print(f"# blockers discovered:\t{metrics['n_blockers_discovered']}")

    print()
    print(f"Ask Precision:\t{metrics['precision']:.2%}")
    print(f"Ask Recall:\t{metrics['recall']:.2%}")
    print(f"Ask F1 Score:\t{metrics['ask_f1']:.2%}")
    print("=" * 80)
    print()
