"""Shared target resolution for commands that act on a project or experiment
by name: bolt update, bolt archive, bolt review, bolt log.
"""

import os

from .context import bolt_file_path, find_context, load_context


def find_subdir_context(name, base=None):
    """If `name` is a subdirectory of `base` (default cwd) with its own
    .bolt.yml, return (directory, data). Otherwise (None, None).
    """
    base = base or os.getcwd()
    sub = os.path.join(base, name)
    if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
        return sub, load_context(sub)
    return None, None


def collect_all_experiments(root_dir, cwd=None, include_archived=True, include_root=True):
    """Recursively collect every experiment at or below `root_dir`, including
    experiments nested arbitrarily deep inside other experiments.

    Returns a list of dicts: {dir, data, rel}, where `rel` is a path like
    '.' (root_dir itself), './mapping', or './phylogeny/pathphynder',
    relative to `cwd`.
    """
    cwd = cwd or os.getcwd()
    results = []

    def walk(directory, data, add_current):
        is_archived = data.get("archived", False)
        if data.get("type") == "experiment" and add_current and (
            include_archived or not is_archived
        ):
            rel = os.path.relpath(directory, cwd)
            rel_display = "." if rel == "." else (rel if rel.startswith(".") else f"./{rel}")
            results.append({"dir": directory, "data": data, "rel": rel_display})

        if not include_archived and is_archived:
            return

        for entry in sorted(os.listdir(directory)):
            sub = os.path.join(directory, entry)
            if not os.path.isdir(sub):
                continue
            if os.path.isfile(bolt_file_path(sub)):
                sub_data = load_context(sub)
                if sub_data.get("type") == "experiment":
                    walk(sub, sub_data, add_current=True)
            else:
                walk_unmanaged(sub)

    def walk_unmanaged(directory):
        for entry in sorted(os.listdir(directory)):
            sub = os.path.join(directory, entry)
            if not os.path.isdir(sub):
                continue
            if os.path.isfile(bolt_file_path(sub)):
                sub_data = load_context(sub)
                if sub_data.get("type") == "experiment":
                    walk(sub, sub_data, add_current=True)
            else:
                walk_unmanaged(sub)

    walk(root_dir, load_context(root_dir), include_root)

    return results


def resolve_target(name):
    """Resolve `name` to a project or experiment, searching (in order):

    1. A subdirectory of the cwd named `name` with its own .bolt.yml.
    2. The current context itself (its `name` field matches).
    3. Any experiment nested anywhere below the current context (matched by
       exact name or by its relative path, e.g. 'exp2/exp3').

    Returns one of:
      {"kind": "context", "dir": ..., "data": ...}
      {"kind": "ambiguous", "matches": [...]}
      None if nothing matched.
    """
    sub_dir, sub_data = find_subdir_context(name)
    if sub_dir:
        return {"kind": "context", "dir": sub_dir, "data": sub_data}

    directory, data = find_context()
    if directory is None:
        return None

    if data.get("name") == name:
        return {"kind": "context", "dir": directory, "data": data}

    all_exps = collect_all_experiments(directory, include_archived=True, include_root=False)
    norm = name if name.startswith("./") else f"./{name}"
    matches = [
        e for e in all_exps
        if e["data"].get("name") == name or e["rel"] in (name, norm)
    ]
    if len(matches) == 1:
        m = matches[0]
        return {"kind": "context", "dir": m["dir"], "data": m["data"]}
    if len(matches) > 1:
        return {"kind": "ambiguous", "matches": matches}

    return None
