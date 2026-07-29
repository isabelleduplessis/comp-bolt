"""bolt result | command | bolt result | bolt result --remove"""

import sys

from ..context import require_context, save_context
from ..utils import now_iso, choose_from_list, die


MAX_LINES_WITHOUT_WARNING = 100


def register(subparsers):
    p = subparsers.add_parser(
        "result",
        help="Store command output as an experiment/project result.",
        description=(
            "Store multiline command output as a timestamped result. "
            "Input may come from a pipe or be pasted interactively."
        ),
    )

    p.add_argument(
        "-r",
        "--remove",
        action="store_true",
        help="Remove a previously stored result.",
    )

    p.set_defaults(func=run)


def _format_result(result):
    preview = result["content"].replace("\n", " ")
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return f"{result['timestamp']}  {preview}"


def _read_result_text():
    if not sys.stdin.isatty():
        return sys.stdin.read().rstrip()

    print("Paste result text. Press Ctrl+D when finished:")
    try:
        return sys.stdin.read().rstrip()
    except KeyboardInterrupt:
        print()
        die("Aborted.")


def run(args):
    directory, data = require_context(allowed_types={"project", "experiment"})
    results = data.setdefault("results", [])

    if args.remove:
        if not results:
            die("There are no results to remove.")

        result = choose_from_list(
            results,
            formatter=_format_result,
            prompt_text="Select a result to remove",
        )

        results.remove(result)
        save_context(directory, data)

        print("Result removed.")
        return

    text = _read_result_text()

    if not text.strip():
        die("Result cannot be empty.")

    line_count = len(text.splitlines())

    if line_count > MAX_LINES_WITHOUT_WARNING:
        response = input(
            f"Result contains {line_count} lines. Store anyway? [y/N]: "
        ).strip().lower()

        if response not in {"y", "yes"}:
            print("Cancelled.")
            return

    results.append(
        {
            "timestamp": now_iso(),
            "content": text,
        }
    )

    save_context(directory, data)

    print(f"Stored result ({line_count} lines).")
