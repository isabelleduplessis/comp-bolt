"""bolt log [name] [-p/--plain]

Generates a documentation report from .bolt.yml metadata, recursing through
nested experiments. Prints to stdout; redirect with '>' to save a file.
Archived experiments and jobs are excluded from the report.
"""

import os

from ..context import find_context, bolt_file_path
from ..targets import find_subdir_context
from ..yaml_io import load_yaml
from ..utils import die


def register(subparsers):
    p = subparsers.add_parser(
        "log",
        help="Generate a documentation report from Bolt metadata.",
        description=(
            "Generate a report (Markdown by default) from the .bolt.yml "
            "metadata of the current directory and everything nested inside "
            "it. Prints to stdout; redirect with '>' to save it to a file. "
            "Archived items are excluded."
        ),
    )
    p.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Name of a project/experiment to report on, instead of the current directory.",
    )
    p.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help="Print in plain text instead of Markdown.",
    )
    p.set_defaults(func=run)


def run(args):
    if args.name:
        directory, data = find_subdir_context(args.name)
        if directory is None:
            found_dir, found_data = find_context()
            if found_dir is not None and found_data.get("name") == args.name:
                directory, data = found_dir, found_data
        if directory is None:
            die(f"No project or experiment named '{args.name}' found here.")
    else:
        directory, data = find_context()
        if directory is None:
            die("Not inside a Bolt project.")

    if data.get("archived", False):
        die(f"'{data.get('name')}' is archived. Unarchive it with 'bolt archive -u' to log it.")

    tree = _build_tree(directory)

    if data.get("type") == "project":
        text = _render_project(tree)
    else:
        text = _render_experiment_root(tree)

    if args.plain:
        text = _to_plain(text)

    print(text)


def _build_tree(directory):
    data = load_yaml(bolt_file_path(directory))
    node = {"dir": directory, "data": data, "children": [], "jobs": [], "archived_job_count": 0}

    if data.get("type") == "experiment":
        node["jobs"] = [j for j in data.get("jobs", []) if not j.get("archived", False)]
        node["archived_job_count"] = sum(1 for j in data.get("jobs", []) if j.get("archived", False))

    for entry in sorted(os.listdir(directory)):
        sub = os.path.join(directory, entry)
        if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
            sub_data = load_yaml(bolt_file_path(sub))
            if sub_data.get("type") == "experiment" and not sub_data.get("archived", False):
                node["children"].append(_build_tree(sub))

    return node


def _date(iso_ts):
    if not iso_ts:
        return ""
    return str(iso_ts).split("T")[0]


def _note_lines(notes):
    return [f"- {_date(n.get('timestamp'))}: {n.get('text')}" for n in notes]


def _render_project(tree):
    data = tree["data"]
    out = []
    out.append(f"# Project: {data.get('name')}")
    out.append("")
    out.append("## Description")
    out.append("")
    out.append(str(data.get("description") or "").strip())
    out.append("")
    out.append(f"**Created:** {_date(data.get('created'))}")
    out.append("")
    out.append("---")
    out.append("")
    out.append("# Experiments")
    out.append("")

    for child in tree["children"]:
        out.extend(_render_experiment_node(child, name_level=2, detailed=False))
        out.append("---")
        out.append("")

    exp_count, job_count, status_counts, abandoned = _summarize(tree)
    out.append("# Summary")
    out.append("")
    out.append(f"**Experiments:** {exp_count}")
    out.append("")
    out.append(f"**Jobs:** {job_count}")
    out.append("")
    out.append("## Job Status Counts")
    out.append("")
    out.append(f"- Success: {status_counts.get('success', 0)}")
    out.append(f"- Fail: {status_counts.get('fail', 0)}")
    out.append(f"- Pending: {status_counts.get('pending', 0)}")
    out.append(f"- Inconclusive: {status_counts.get('inconclusive', 0)}")
    out.append(f"- Abandoned: {abandoned}")

    return "\n".join(out)


def _render_experiment_root(tree):
    data = tree["data"]
    out = []
    out.append(f"# Experiment: {data.get('name')}")
    out.append("")
    out.append("## Description")
    out.append("")
    out.append(str(data.get("description") or "").strip())
    out.append("")
    out.append(f"**Created:** {_date(data.get('created'))}")
    out.append("")
    out.append("---")
    out.append("")

    if data.get("notes"):
        out.append("## Notes")
        out.append("")
        out.extend(_note_lines(data["notes"]))
        out.append("")
        out.append("---")
        out.append("")

    if tree["jobs"]:
        out.append("## Jobs")
        out.append("")
        for job in tree["jobs"]:
            out.extend(_render_job_detailed(job, name_level=3))

    if tree["children"]:
        out.append("## Nested Experiments")
        out.append("")
        for child in tree["children"]:
            out.extend(_render_experiment_node(child, name_level=3, detailed=True))
            out.append("---")
            out.append("")

    return "\n".join(out)


def _render_experiment_node(node, name_level, detailed):
    data = node["data"]
    out = []
    out.append("#" * name_level + f" {data.get('name')}")
    out.append("")

    section_level = name_level + 1
    child_level = name_level + 2

    out.append("#" * section_level + " Description")
    out.append("")
    out.append(str(data.get("description") or "").strip())
    out.append("")

    if data.get("notes"):
        out.append("#" * section_level + " Notes")
        out.append("")
        out.extend(_note_lines(data["notes"]))
        out.append("")

    if node["jobs"]:
        out.append("#" * section_level + " Jobs")
        out.append("")
        for job in node["jobs"]:
            if detailed:
                out.extend(_render_job_detailed(job, name_level=child_level))
            else:
                out.extend(_render_job_compact(job, name_level=child_level))

    if node["children"]:
        out.append("#" * section_level + " Nested Experiments")
        out.append("")
        for child in node["children"]:
            out.extend(_render_experiment_node(child, name_level=child_level, detailed=detailed))

    return out


def _render_job_compact(job, name_level):
    out = []
    out.append("#" * name_level + f" {job.get('name')}")
    out.append("")
    out.append(f"**Description:** {job.get('description', '')}")
    out.append("")
    out.append(f"**Status:** {job.get('status', 'pending')}")
    out.append("")
    out.append(f"**Last Review:** {_date(job.get('review_timestamp'))}")
    out.append("")
    out.append(f"**Result:** {job.get('status_description') or ''}")
    out.append("")
    return out


def _render_job_detailed(job, name_level):
    out = []
    out.append("#" * name_level + f" {job.get('name')}")
    out.append("")

    section_level = name_level + 1
    out.append("#" * section_level + " Description")
    out.append("")
    out.append(job.get("description", ""))
    out.append("")
    out.append("#" * section_level + " Current Status")
    out.append("")
    out.append(job.get("status", "pending"))
    out.append("")
    out.append("#" * section_level + " Current Result")
    out.append("")
    out.append(job.get("status_description") or "")
    out.append("")

    reviews = job.get("reviews", [])
    if reviews:
        out.append("#" * section_level + " Review History")
        out.append("")
        review_level = section_level + 1
        for review in reviews:
            out.append("#" * review_level + f" {_date(review.get('timestamp'))}")
            out.append("")
            out.append(f"**Status:** {review.get('status')}")
            out.append("")
            out.append(f"**Result:** {review.get('result')}")
            out.append("")

    return out


def _summarize(tree):
    exp_count = 0
    job_count = 0
    status_counts = {}
    abandoned = 0

    def walk(node):
        nonlocal exp_count, job_count, abandoned
        exp_count += 1
        abandoned += node.get("archived_job_count", 0)
        for job in node["jobs"]:
            job_count += 1
            status = job.get("status", "pending")
            status_counts[status] = status_counts.get(status, 0) + 1
        for child in node["children"]:
            walk(child)

    for child in tree["children"]:
        walk(child)

    return exp_count, job_count, status_counts, abandoned


def _to_plain(markdown_text):
    out_lines = []
    for line in markdown_text.split("\n"):
        if line.strip() == "---":
            continue
        if line.startswith("#"):
            stripped = line.lstrip("#")
            level = len(line) - len(stripped)
            text = stripped.strip()
            indent = "  " * max(level - 1, 0)
            out_lines.append(f"{indent}{text}")
        else:
            out_lines.append(line.replace("**", ""))
    return "\n".join(out_lines)
