"""bolt exp <name> [-d/--description DESC]"""
import os

from ..context import find_project_root, save_context, bolt_file_path
from ..utils import now_iso, prompt, resolve_new_target, die


def register(subparsers):
    p = subparsers.add_parser(
        "new",
        help="Create a new experiment directory inside the current directory.",
        description=(
            "Create a new experiment directory inside the current directory. "
            "Must be run inside an existing Bolt project or experiment. "
            "Experiments may be nested arbitrarily."
        ),
    )
    p.add_argument("path", help="Path of the experiment to create.")
    p.add_argument(
        "-d",
        "--description",
        help="Experiment description. If omitted, you will be prompted for one.",
    )
    p.set_defaults(func=run)


def run(args): # you don't have to be inside a project to run the command, but the dir would need to be in a project

    target_dir = resolve_new_target(args.path, "directory")

    project_dir, project_data = find_project_root(target_dir)

    if project_dir is None:
        die(
            f"'{target_dir}' is not inside a Bolt project."
        )

    name = os.path.basename(target_dir)

    adopting = False
    if os.path.exists(target_dir):
        if not os.path.isdir(target_dir):
            die(f"'{name}' already exists in the current directory and is not a directory.")
        if os.path.isfile(bolt_file_path(target_dir)):
            die(f"'{name}' is already a Bolt directory.")
        adopting = True

    description = args.description
    if description is None:
        description = prompt("Experiment description: ")

    os.makedirs(target_dir, exist_ok=True)

    data = {
        "type": "experiment",
        "description": description,
        "created": now_iso(),
        "archived": False,
        "status": "in progress",
        "status_description": None,
        "review_timestamp": None,
        "notes": [],
        "results": [],
        "updates": [],
        "reviews": [],
    }
    save_context(target_dir, data)

    if adopting:
        print(f"Initialized existing directory '{name}' as an experiment at {target_dir}")
    else:
        print(f"Created experiment '{name}' at {target_dir}")
    print(f"Metadata stored in {bolt_file_path(target_dir)}")
    print("Status: in progress")