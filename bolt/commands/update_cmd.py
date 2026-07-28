"""bolt update <project/exp/job>

Updates the name and/or description of a project, experiment, or job,
retaining the previous values in an update history with timestamps.
"""

import os

from ..context import save_context
from ..targets import resolve_target
from ..utils import now_iso, prompt, die


def register(subparsers):
    p = subparsers.add_parser(
        "update",
        help="Update the name and/or description of a project, experiment, or job.",
        description=(
            "Update the name and/or description of a project, experiment, or "
            "job. Previous values are retained (with timestamps) in the "
            "item's update history."
        ),
    )
    p.add_argument(
        "name",
        help="Current name (or relative path, for a nested job) of the item to update.",
    )
    p.set_defaults(func=run)


def run(args):
    target = resolve_target(args.name)

    if target is None:
        die(f"No project, experiment, or job named '{args.name}' found here.")

    if target["kind"] == "ambiguous":
        options = ", ".join(m["rel"] for m in target["matches"])
        die(f"Multiple jobs match '{args.name}' ({options}); specify the full path.")

    if target["kind"] == "context":
        _update_context(target["dir"], target["data"])
    else:
        _update_job(target["exp_dir"], target["exp_data"], target["job"])


def _update_context(directory, data):
    current_name = data.get("name")
    current_desc = data.get("description")

    print(f"Updating {data.get('type')} '{current_name}'")
    print(f"Current description: {current_desc}")

    new_name = prompt(f"New name (leave blank to keep '{current_name}', 'q' to quit): ")
    new_desc = prompt("New description (leave blank to keep current, 'q' to quit): ")

    timestamp = now_iso()
    updates = data.setdefault("updates", [])
    changed = False

    if new_name and new_name != current_name:
        new_dir = os.path.join(os.path.dirname(directory), new_name)
        if os.path.exists(new_dir):
            die(f"Cannot rename: '{new_name}' already exists in the parent directory.")
        os.rename(directory, new_dir)
        directory = new_dir
        updates.append(
            {
                "timestamp": timestamp,
                "field": "name",
                "old_value": current_name,
                "new_value": new_name,
            }
        )
        data["name"] = new_name
        changed = True

    if new_desc and new_desc != current_desc:
        updates.append(
            {
                "timestamp": timestamp,
                "field": "description",
                "old_value": current_desc,
                "new_value": new_desc,
            }
        )
        data["description"] = new_desc
        changed = True

    if not changed:
        print("No changes made.")
        return

    save_context(directory, data)
    print(f"Updated {data.get('type')} at {directory}")


def _update_job(exp_dir, exp_data, job):
    current_name = job.get("name")
    current_desc = job.get("description")

    print(f"Updating job '{current_name}'")
    print(f"Current description: {current_desc}")

    new_name = prompt(f"New name (leave blank to keep '{current_name}', 'q' to quit): ")
    new_desc = prompt("New description (leave blank to keep current, 'q' to quit): ")

    timestamp = now_iso()
    history = job.setdefault("update_history", [])
    changed = False

    if new_name and new_name != current_name:
        old_path = os.path.join(exp_dir, current_name)
        new_path = os.path.join(exp_dir, new_name)
        if os.path.exists(new_path):
            die(f"Cannot rename: '{new_name}' already exists in this experiment.")
        if os.path.isfile(old_path):
            os.rename(old_path, new_path)
        history.append(
            {
                "timestamp": timestamp,
                "field": "name",
                "old_value": current_name,
                "new_value": new_name,
            }
        )
        job["name"] = new_name
        changed = True

    if new_desc and new_desc != current_desc:
        history.append(
            {
                "timestamp": timestamp,
                "field": "description",
                "old_value": current_desc,
                "new_value": new_desc,
            }
        )
        job["description"] = new_desc
        changed = True

    if not changed:
        print("No changes made.")
        return

    save_context(exp_dir, exp_data)
    print(f"Updated job '{job['name']}'")
