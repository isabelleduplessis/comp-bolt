"""bolt archive <name> [-u/--unarchive] [-s/--status]

Archives (or unarchives) a project, experiment, or job. Archived items stay
in metadata and are recoverable, but are excluded from bolt log reports and
from bolt review's job lists.
"""

import os

from ..context import save_context, find_context, bolt_file_path
from ..targets import resolve_target
from ..yaml_io import load_yaml
from ..utils import die


def register(subparsers):
    p = subparsers.add_parser(
        "archive",
        help="Archive or unarchive a project, experiment, or job.",
        description=(
            "Archive a project, experiment, or job. Archived items remain in "
            "metadata and are recoverable, but are excluded from 'bolt log' "
            "reports and from 'bolt review' job lists."
        ),
    )
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name (or relative path, for a nested job) of the item to archive.",
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
        die("Specify a project, experiment, or job name to archive (or use -s/--status).")

    target = resolve_target(args.name)

    if target is None:
        die(f"No project, experiment, or job named '{args.name}' found here.")

    if target["kind"] == "ambiguous":
        options = ", ".join(m["rel"] for m in target["matches"])
        die(f"Multiple jobs match '{args.name}' ({options}); specify the full path.")

    archived_value = not args.unarchive

    if target["kind"] == "context":
        data = target["data"]
        data["archived"] = archived_value
        save_context(target["dir"], data)
        label = data.get("name")
    else:
        job = target["job"]
        job["archived"] = archived_value
        save_context(target["exp_dir"], target["exp_data"])
        label = job.get("name")

    verb = "Unarchived" if args.unarchive else "Archived"
    print(f"{verb} '{label}'.")


def _show_status():
    directory, data = find_context()
    if directory is None:
        die("Not inside a Bolt project.")

    active = []
    archived = []

    def walk(d, dat, prefix=""):
        is_archived = dat.get("archived", False)
        label = f"{prefix}{dat.get('name')} ({dat.get('type')})"
        (archived if is_archived else active).append(label)

        # An archived experiment's jobs are reported under it, not separately.
        if dat.get("type") == "experiment" and not is_archived:
            for job in dat.get("jobs", []):
                job_label = f"{prefix}  {job.get('name')} (job)"
                (archived if job.get("archived", False) else active).append(job_label)

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
