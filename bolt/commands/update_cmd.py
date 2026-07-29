"""bolt update <project/experiment>

Updates the name and/or description of a project or experiment, retaining
the previous values in an update history with timestamps.
"""

import os

from ..context import save_context
from ..targets import resolve_target
from ..utils import now_iso, prompt, die


def register(subparsers):
    p = subparsers.add_parser(
        "update",
        help="Update the name and/or description of a project or experiment.",
        description=(
            "Update the name and/or description of a project or experiment. "
            "Previous values are retained (with timestamps) in its update "
            "history."
        ),
    )
    p.add_argument(
        "name",
        help="Current name (or relative path, for a nested experiment) of the item to update.",
    )
    p.set_defaults(func=run)


def run(args):
    target = resolve_target(args.name)

    if target is None:
        die(f"No project or experiment named '{args.name}' found here.")

    if target["kind"] == "ambiguous":
        options = ", ".join(m["rel"] for m in target["matches"])
        die(f"Multiple experiments match '{args.name}' ({options}); specify the full path.")

    directory = target["dir"]
    data = target["data"]

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
        new_dir = os.path.join(os.path.dirname(os.path.normpath(directory)), new_name)

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
