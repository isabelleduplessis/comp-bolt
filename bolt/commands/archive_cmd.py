"""bolt archive <name> [-u/--unarchive] [-s/--status]

Archives (or unarchives) a project or experiment. Archived items stay in
metadata and are recoverable, but are excluded from bolt log reports and
from bolt review's in progress list.
"""

import os

from ..context import save_context, find_context, bolt_file_path
from ..targets import resolve_target
from ..yaml_io import load_yaml
from ..utils import die


def register(subparsers):
    p = subparsers.add_parser(
        "archive",
        help="Archive or unarchive a project or experiment.",
        description=(
            "Archive a project or experiment. Archived items remain in "
            "metadata and are recoverable, but are excluded from 'bolt log' "
            "reports and from 'bolt review'."
        ),
    )
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name (or relative path, for a nested experiment) of the item to archive.",
    )
    p.add_argument(
        "-u",
        "--unarchive",
        action="store_true",
        help="Unarchive the item instead of archiving it.",
    )
    p.add_argument(
        "-s",
        "--status",
        action="store_true",
        help="Show active vs. archived items below the current directory.",
    )
    p.set_defaults(func=run)


def run(args):
    if args.status:
        _show_status()
        return

    if not args.name:
        die("Specify a project or experiment name to archive (or use -s/--status).")

    target = resolve_target(args.name)

    if target is None:
        die(f"No project or experiment named '{args.name}' found here.")

    if target["kind"] == "ambiguous":
        options = ", ".join(m["rel"] for m in target["matches"])
        die(f"Multiple experiments match '{args.name}' ({options}); specify the full path.")

    data = target["data"]
    data["archived"] = not args.unarchive
    save_context(target["dir"], data)

    verb = "Unarchived" if args.unarchive else "Archived"
    print(f"{verb} '{data.get('name')}'.")


def _show_status():
    directory, data = find_context()
    if directory is None:
        die("Not inside a Bolt project.")

    active = []
    archived = []

    def walk(d, dat, prefix=""):
        is_archived = dat.get("archived", False)
        status_suffix = f", status={dat['status']}" if dat.get("type") == "experiment" else ""
        label = f"{prefix}{dat.get('name')} ({dat.get('type')}{status_suffix})"
        (archived if is_archived else active).append(label)

        # An archived experiment's descendants are reported under it, not separately.
        if not is_archived:
            for entry in sorted(os.listdir(d)):
                sub = os.path.join(d, entry)
                if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
                    sub_data = load_yaml(bolt_file_path(sub))
                    if sub_data.get("type") == "experiment":
                        walk(sub, sub_data, prefix + "  ")

    walk(directory, data)

    print("Active:")
    if active:
        for item in active:
            print(f"  {item}")
    else:
        print("  (none)")

    print("Archived:")
    if archived:
        for item in archived:
            print(f"  {item}")
    else:
        print("  (none)")
