"""bolt job <name> [-d/--description DESC] [-c/--copy SCRIPT]"""

import os
import shutil

from ..context import require_context, save_context
from ..utils import now_iso, prompt, validate_name, die


def register(subparsers):
    p = subparsers.add_parser(
        "job",
        help="Create a new job (shell script) in the current experiment.",
        description=(
            "Create a new job file in the current experiment directory. "
            "By default an empty script is created; use -c/--copy to start "
            "from a copy of an existing script instead."
        ),
    )
    p.add_argument("name", help="Filename of the job script to create.")
    p.add_argument(
        "-d",
        "--description",
        help="Job description. If omitted, you will be prompted for one.",
    )
    p.add_argument(
        "-c",
        "--copy",
        metavar="SCRIPT",
        help="Path to an existing script to copy as the starting point for this job.",
    )
    p.set_defaults(func=run)


def run(args):
    directory, data = require_context(allowed_types={"experiment"})

    name = validate_name(args.name, "job name")

    target_file = os.path.join(os.getcwd(), name)
    if os.path.exists(target_file):
        die(f"'{name}' already exists in the current directory.")

    description = args.description
    if description is None:
        description = prompt("Job description: ")

    if args.copy:
        source = args.copy
        if not os.path.isfile(source):
            die(f"Cannot copy: '{source}' does not exist or is not a file.")
        shutil.copyfile(source, target_file)
    else:
        # Jobs are always files, never directories; create an empty script.
        open(target_file, "a").close()

    job_entry = {
        "name": name,
        "description": description,
        "created": now_iso(),
        "status": "pending",
        "status_description": None,
        "review_timestamp": None,
        "archived": False,
        "update_history": [],
        "reviews": [],
    }

    data.setdefault("jobs", []).append(job_entry)
    save_context(directory, data)

    print(f"Created job '{name}' in {os.getcwd()}")
    print("Status: pending")
