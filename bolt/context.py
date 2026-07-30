"""Locate and load the Bolt context (nearest project or experiment) for the cwd."""

import os

from .utils import die
from .yaml_io import load_yaml, save_yaml

BOLT_FILE = ".bolt.yml"


def bolt_file_path(directory):
    return os.path.join(directory, BOLT_FILE)

def load_context(directory):
    data = load_yaml(directory)
    data["name"] = os.path.basename(os.path.normpath(directory))
    return data



def find_context(start=None):
    """Walk upward from `start` (default: cwd) looking for the nearest .bolt.yml.

    Returns (directory, data) if found, otherwise (None, None).
    """
    current = os.path.abspath(start or os.getcwd())

    while True:
        candidate = bolt_file_path(current)
        if os.path.isfile(candidate):
            return current, load_context(candidate) # replaced load yaml to get rid of name

        parent = os.path.dirname(current)
        if parent == current:
            # reached filesystem root
            return None, None
        current = parent


def require_context(start=None, allowed_types=None):
    """Find the nearest Bolt context, dying with a helpful error if none exists.

    If `allowed_types` is given (e.g. {"experiment"}), the found context's
    `type` field must be one of them, or bolt dies with an error.
    """
    directory, data = find_context(start)
    if directory is None:
        die(
            "Not inside a Bolt project. Run 'bolt init <path>' to create one first."
        )

    if allowed_types and data.get("type") not in allowed_types:
        found_type = data.get("type", "unknown")
        wanted = " or ".join(sorted(allowed_types))
        article = "an" if wanted[0] in "aeiou" else "a"
        die(
            f"This command must be run inside {article} {wanted} directory "
            f"(found a '{found_type}' at {directory})."
        )

    return directory, data


def save_context(directory, data):
    save_yaml(bolt_file_path(directory), data)


def find_project_root(start=None):
    """Find the outermost Bolt-tracked ancestor (the project) containing `start`.

    Starting from the nearest .bolt.yml, keep walking up through any further
    .bolt.yml ancestors. Returns (directory, data) of the project root, or
    (None, None) if `start` isn't inside a Bolt project at all.
    """
    directory, data = find_context(start)
    if directory is None:
        return None, None

    root_dir, root_data = directory, data
    current = directory
    while True:
        parent = os.path.dirname(current)
        if parent == current:
            break
        candidate = bolt_file_path(parent)
        if os.path.isfile(candidate):
            root_dir, root_data = parent, load_yaml(candidate)
            current = parent
        else:
            break

    if root_data.get("type") != "project":
        return None, None

    return root_dir, root_data
