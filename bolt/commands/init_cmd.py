"""bolt init <path> [-d/--description DESC]"""
import os

from ..context import save_context, bolt_file_path
from ..utils import now_iso, prompt, resolve_new_target, die


def register(subparsers):
    p = subparsers.add_parser(
        "init",
        help="Create a new Bolt project directory.",
        description="Create a new project directory with Bolt metadata.",
    )
    p.add_argument("path", help="Path of the project to create.")
    p.add_argument(
        "-d",
        "--description",
        help="Project description. If omitted, you will be prompted for one.",
    )
    p.set_defaults(func=run)


def run(args):

    #name = validate_name(args.path, "project name")
    target_dir = resolve_new_target(args.path, "directory")
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
        description = prompt("Project description: ")

    os.makedirs(target_dir, exist_ok=True)

    data = {
        "type": "project",
        "description": description,
        "created": now_iso(),
        "archived": False,
        "notes": [],
        "results": [],
        "updates": [],
    }
    save_context(target_dir, data)

    if adopting:
        print(f"Initialized existing directory '{os.path.basename(target_dir)}' as a Bolt project at {target_dir}")
    else:
        print(f"Initialized Bolt project '{os.path.basename(target_dir)}' at {target_dir}")
    print(f"Metadata stored in {bolt_file_path(target_dir)}")