"""Shared target resolution for commands that act on a project/experiment/job
by name: bolt update, bolt archive, and (for job discovery) bolt review.
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


def collect_all_jobs(root_dir, cwd=None, include_archived=True):
    """Recursively collect every job under `root_dir` (an experiment or
    project directory), including nested experiments within experiments.

    Returns a list of dicts: {exp_dir, exp_data, job, rel} where `rel` is a
    path like './job1.sh' or './exp2/job2.sh' relative to `cwd`.
    """
    cwd = cwd or os.getcwd()
    results = []

    data = load_yaml(bolt_file_path(root_dir))
    if data.get("type") == "experiment" and (include_archived or not data.get("archived", False)):
        for job in data.get("jobs", []):
            if not include_archived and job.get("archived", False):
                continue
            rel = os.path.relpath(os.path.join(root_dir, job["name"]), start=cwd)
            if not rel.startswith("."):
                rel = f"./{rel}"
            results.append({"exp_dir": root_dir, "exp_data": data, "job": job, "rel": rel})

    if include_archived or not data.get("archived", False):
        for entry in sorted(os.listdir(root_dir)):
            sub = os.path.join(root_dir, entry)
            if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
                sub_data = load_yaml(bolt_file_path(sub))
                if sub_data.get("type") == "experiment":
                    results.extend(collect_all_jobs(sub, cwd, include_archived))

    return results


def resolve_target(name):
    """Resolve `name` to a project, experiment, or job, searching (in order):

    1. A subdirectory of the cwd named `name` with its own .bolt.yml.
    2. The current context itself (its `name` field matches).
    3. A job directly inside the current context.
    4. Any job nested anywhere below the current context (matched by exact
       name or by its relative path, e.g. 'exp2/job2.sh').

    Returns one of:
      {"kind": "context", "dir": ..., "data": ...}
      {"kind": "job", "exp_dir": ..., "exp_data": ..., "job": ...}
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

    if data.get("type") == "experiment":
        for job in data.get("jobs", []):
            if job.get("name") == name:
                return {"kind": "job", "exp_dir": directory, "exp_data": data, "job": job}

    all_jobs = collect_all_jobs(directory)
    norm = name if name.startswith("./") else f"./{name}"
    matches = [j for j in all_jobs if j["job"].get("name") == name or j["rel"] in (name, norm)]
    if len(matches) == 1:
        m = matches[0]
        return {"kind": "job", "exp_dir": m["exp_dir"], "exp_data": m["exp_data"], "job": m["job"]}
    if len(matches) > 1:
        return {"kind": "ambiguous", "matches": matches}

    return None
