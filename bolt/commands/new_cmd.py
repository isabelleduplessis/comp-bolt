"""bolt exp <name> [-d/--description DESC]"""

import os

from ..context import require_context, save_context, bolt_file_path
from ..utils import now_iso, prompt, validate_name, die


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
    p.add_argument("name", help="Name of the experiment to create.")
    p.add_argument(
        "-d",
        "--description",
        help="Experiment description. If omitted, you will be prompted for one.",
    )
    p.set_defaults(func=run)


def run(args):
    # Must be inside a project or experiment (searches cwd and ancestors).
    require_context(allowed_types={"project", "experiment"})

    name = validate_name(args.name, "experiment name")

    target_dir = os.path.join(os.getcwd(), name)
    if os.path.exists(target_dir):
        die(f"'{name}' already exists in the current directory.")

    description = args.description
    if description is None:
        description = prompt("Experiment description: ")

    os.makedirs(target_dir)

    data = {
        "type": "experiment",
        "name": name,
        "description": description,
        "created": now_iso(),
        "archived": False,
        "notes": [],
        "updates": [],
        "jobs": [],
    }
    save_context(target_dir, data)

    print(f"Created experiment '{name}' at {target_dir}")
    print(f"Metadata stored in {bolt_file_path(target_dir)}")
