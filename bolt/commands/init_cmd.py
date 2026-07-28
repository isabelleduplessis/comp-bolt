"""bolt init <name> [-d/--description DESC]"""

import os

from ..context import save_context, bolt_file_path
from ..utils import now_iso, prompt, validate_name, die


def register(subparsers):
    p = subparsers.add_parser(
        "init",
        help="Create a new Bolt project directory.",
        description="Create a new project directory with Bolt metadata.",
    )
    p.add_argument("name", help="Name of the project to create.")
    p.add_argument(
        "-d",
        "--description",
        help="Project description. If omitted, you will be prompted for one.",
    )
    p.set_defaults(func=run)


def run(args):
    name = validate_name(args.name, "project name")

    target_dir = os.path.join(os.getcwd(), name)
    if os.path.exists(target_dir):
        die(f"'{name}' already exists in the current directory.")

    description = args.description
    if description is None:
        description = prompt("Project description: ")

    os.makedirs(target_dir)

    data = {
        "type": "project",
        "name": name,
        "description": description,
        "created": now_iso(),
        "archived": False,
        "notes": [],
        "updates": [],
    }
    save_context(target_dir, data)

    print(f"Initialized Bolt project '{name}' at {target_dir}")
    print(f"Metadata stored in {bolt_file_path(target_dir)}")
