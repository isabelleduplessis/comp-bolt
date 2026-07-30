"""bolt log [name] [-p/--plain]

Generates a documentation report from .bolt.yml metadata, recursing through
nested experiments. Prints to stdout; redirect with '>' to save a file.
Archived experiments are excluded.
"""

import os
from datetime import datetime

from ..context import find_context, bolt_file_path, load_context
from ..targets import find_subdir_context
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
    is_project = data.get("type") == "project"
    text = _render_report(tree, is_project)

    if args.plain:
        text = _to_plain(text)

    print(text)


def _build_tree(directory):
    data = load_context(bolt_file_path(directory))
    node = {"dir": directory, "data": data, "children": []}

    for entry in sorted(os.listdir(directory)):
        sub = os.path.join(directory, entry)
        if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
            sub_data = load_context(bolt_file_path(sub))
            if sub_data.get("type") == "experiment" and not sub_data.get("archived", False):
                node["children"].append(_build_tree(sub))

    return node


def _datetime(iso_ts):
    """Render an ISO timestamp as 'YYYY-MM-DD HH:MM:SS'. Falls back to the
    raw date portion if the timestamp can't be parsed."""
    if not iso_ts:
        return ""
    raw = str(iso_ts)
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return raw.split("T")[0]


def _status_label(status):
    # Keep the raw status vocabulary as-is (complete, in progress,
    # inconclusive, fail) — just title-case it for display.
    return (status or "in progress").title()


def _note_lines(notes):
    return [f"- **{_datetime(n.get('timestamp'))}:** {n.get('text')}" for n in notes]


def _result_lines(results):
    lines = []
    for result in results:
        ts = _datetime(result.get("timestamp"))
        content = str(result.get("content") or "")
        lines.append(f"{ts}:")
        lines.append("```")
        lines.extend(content.split("\n"))
        lines.append("```")
        lines.append("")
    return lines


def _review_lines(reviews):
    lines = []
    for review in reviews:
        ts = _datetime(review.get("timestamp"))
        status = _status_label(review.get("status"))
        result = str(review.get("result") or "").strip()
        lines.append(f"- **{ts}:** Status: {status}. {result}")
    return lines


def _tree_lines(root):
    """Ascii directory-style tree for a single top-level experiment root."""
    lines = [f"{root['data'].get('name')}/"]
    lines.extend(_tree_children_lines(root, ""))
    return lines


def _tree_children_lines(node, prefix):
    lines = []
    children = node["children"]
    for i, child in enumerate(children):
        is_last = i == len(children) - 1
        connector = "└── " if is_last else "├── "
        suffix = "/" if child["children"] else ""
        lines.append(f"{prefix}{connector}{child['data'].get('name')}{suffix}")
        extension = "    " if is_last else "│   "
        lines.extend(_tree_children_lines(child, prefix + extension))
    return lines


def _flatten(node, path, out):
    out.append((node, path))
    for child in node["children"]:
        _flatten(child, f"{path}/{child['data'].get('name')}", out)


def _count_archived(directory):
    """Archived experiments are excluded from the tree entirely, so re-walk
    the raw filesystem to count them separately for the Abandoned tally."""
    count = 0
    for entry in sorted(os.listdir(directory)):
        sub = os.path.join(directory, entry)
        if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
            sub_data = load_context(bolt_file_path(sub))
            if sub_data.get("type") == "experiment":
                if sub_data.get("archived", False):
                    count += 1
                else:
                    count += _count_archived(sub)
    return count


def _render_report(tree, is_project):
    out = []

    if is_project:
        data = tree["data"]
        out.append(f"# {data.get('name')}")
        out.append("")
        description = str(data.get("description") or "").strip().replace("\n", " ")
        out.append(f"**Description:** {description}")
        out.append("")
        out.append(f"**Project Created:** {_datetime(data.get('created'))}")
        out.append("")
        out.append("---")
        out.append("")
        roots = tree["children"]
    else:
        roots = [tree]

    out.append("# Summary")
    out.append("")
    out.append("```bash")
    for root in roots:
        out.extend(_tree_lines(root))
    out.append("```")
    out.append("")

    flat = []
    for root in roots:
        _flatten(root, root["data"].get("name"), flat)

    status_counts = {}
    for node, _path in flat:
        status = node["data"].get("status", "in progress")
        status_counts[status] = status_counts.get(status, 0) + 1

    out.append(f"**Experiment Directories:** {len(flat)}")
    out.append(f"- Complete: {status_counts.get('complete', 0)}")
    out.append(f"- In Progress: {status_counts.get('in progress', 0)}")
    out.append(f"- Inconclusive: {status_counts.get('inconclusive', 0)}")
    out.append(f"- Fail: {status_counts.get('fail', 0)}")
    out.append("")

    for node, path in flat:
        data = node["data"]
        out.append(f"## {path}")
        out.append("")
        out.append("| Description | Status | Last Review Date | Review |")
        out.append("|-------------|--------|-------------------|--------|")
        description = str(data.get("description") or "").strip().replace("\n", " ")
        status_label = _status_label(data.get("status", "in progress"))
        last_review = _datetime(data.get("review_timestamp"))
        result = str(data.get("status_description") or "").strip().replace("\n", " ")
        out.append(f"| {description} | {status_label} | {last_review} | {result} |")
        out.append("")

        reviews = data.get("reviews", [])
        if len(reviews) > 1:
            out.append("#### Review History")
            out.append("")
            out.extend(_review_lines(reviews))
            out.append("")

        if data.get("notes"):
            out.append("#### Notes")
            out.append("")
            out.extend(_note_lines(data["notes"]))
            out.append("")

        if data.get("results"):
            out.append("#### Results")
            out.append("")
            out.extend(_result_lines(data["results"]))

    out.append("---")
    out.append("")
    out.append(f"Log generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return "\n".join(out)


def _to_plain(markdown_text):
    out_lines = []
    in_code_block = False
    for line in markdown_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            out_lines.append(line)
            continue
        if stripped == "---":
            continue
        if line.startswith("#"):
            hashes = line[: len(line) - len(line.lstrip("#"))]
            level = len(hashes)
            text = line.lstrip("#").strip()
            indent = "  " * max(level - 1, 0)
            out_lines.append(f"{indent}{text}")
            continue
        out_lines.append(line.replace("**", ""))
    return "\n".join(out_lines)