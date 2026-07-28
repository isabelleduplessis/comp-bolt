"""Shared target resolution for commands that act on a project or experiment
by name: bolt update, bolt archive, bolt review, bolt log.
"""

import os

from .context import bolt_file_path, find_context
from .yaml_io import load_yaml


def find_subdir_context(name, base=None):
    """If `name` is a subdirectory of `base` (default cwd) with its own
    .bolt.yml, return (directory, data). Otherwise (None, None).
    """
    base = base or os.getcwd()
    sub = os.path.join(base, name)
    if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
        return sub, load_yaml(bolt_file_path(sub))
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

    data = load_yaml(bolt_file_path(root_dir))
    is_archived = data.get("archived", False)

    if data.get("type") == "experiment" and include_root and (include_archived or not is_archived):
        rel = os.path.relpath(root_dir, cwd)
        rel_display = "." if rel == "." else (rel if rel.startswith(".") else f"./{rel}")
        results.append({"dir": root_dir, "data": data, "rel": rel_display})

    if include_archived or not is_archived:
        for entry in sorted(os.listdir(root_dir)):
            sub = os.path.join(root_dir, entry)
            if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
                sub_data = load_yaml(bolt_file_path(sub))
                if sub_data.get("type") == "experiment":
                    results.extend(
                        collect_all_experiments(sub, cwd, include_archived, include_root=True)
                    )

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
