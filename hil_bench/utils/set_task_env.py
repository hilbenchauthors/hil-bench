"""
Set task-specific environment variables for SWE-agent instances.
* sets TASK_INSTANCE_ID environment variable (via post_startup_commands for SWE)
"""

import json
import shlex
import sys


def add_task_env_to_instances(instances_file):
    """
    Set TASK_INSTANCE_ID environment variable in container (for SWE tasks).

    Strategy:
    1. Read instances.json
    2. For each instance, add post_startup_command to set TASK_INSTANCE_ID

    This ensures:
    - ask_human tool can send the right id for server to look up the blocker registry

    Note: For SQL tasks, TASK_INSTANCE_ID is set in DefaultSQLAgent.setup() since SQL
    environments don't support post_startup_commands.

    Args:
        instances_file: Path to instances.json file
    """
    with open(instances_file, "r") as f:
        instances = json.load(f)

    updated_instances = []
    for instance in instances:
        # Use _original_instance_id if available (for mixed-mode runs),
        # otherwise use instance_id (SWE format) or problem_statement.id (SQL format)
        instance_id = instance.get("_original_instance_id")
        if not instance_id:
            instance_id = instance.get("instance_id")
        if not instance_id:
            # SQL format: problem_statement.id
            problem_stmt = instance.get("problem_statement", {})
            if isinstance(problem_stmt, dict):
                instance_id = problem_stmt.get("id")
        if not instance_id:
            # Skip instances without any id
            updated_instances.append(instance)
            continue

        # Also check extra_fields.TASK_INSTANCE_ID for explicit override
        extra_fields = instance.get("extra_fields", {})
        if "TASK_INSTANCE_ID" in extra_fields:
            instance_id = extra_fields["TASK_INSTANCE_ID"]

        # Initialize post_startup_commands if needed
        if "post_startup_commands" not in instance:
            instance["post_startup_commands"] = []

        # Add command to set TASK_INSTANCE_ID environment variable
        instance["post_startup_commands"].append(
            f"export TASK_INSTANCE_ID={shlex.quote(instance_id)}"
        )

        updated_instances.append(instance)

    # Write back to file
    with open(instances_file, "w") as f:
        json.dump(updated_instances, f, indent=2)

    return len(updated_instances)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: set_task_env.py <instances_file>")
        sys.exit(1)

    instances_file = sys.argv[1]

    count = add_task_env_to_instances(instances_file)
    print(f"✅ Updated {count} instances with TASK_INSTANCE_ID set")
