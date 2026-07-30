"""Comp-BOLT command line interface."""

import argparse
import sys

from . import __version__
from .commands import (
    init_cmd,
    new_cmd,
    review_cmd,
    note_cmd,
    result_cmd,
    update_cmd,
    archive_cmd,
    log_cmd,
)
from .context import find_project_root
from .targets import collect_all_experiments

DESCRIPTION = (
    "Comp-BOLT: Comp Bio project Organization, Logging, and Tracing\n"
    "Version: 0.1.0\n"
    "Well-documented project directories and report generation."
)

EPILOG = """\
Type 'q' at any prompt to cancel. Run 'bolt <command> -h' for help on a
specific command.
"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="bolt",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"bolt {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command", metavar="<command>", required=True
    )

    init_cmd.register(subparsers)
    new_cmd.register(subparsers)
    review_cmd.register(subparsers)
    note_cmd.register(subparsers)
    result_cmd.register(subparsers)
    update_cmd.register(subparsers)
    archive_cmd.register(subparsers)
    log_cmd.register(subparsers)

    return parser


def _warn_pending_jobs():
    """If run inside a project, warn (non-blocking) about in progress experiments anywhere in it."""
    root_dir, root_data = find_project_root()
    if root_dir is None:
        return

    all_exps = collect_all_experiments(root_dir, cwd=root_dir, include_archived=False)
    pending = [e for e in all_exps if e["data"].get("status") == "in progress"]
    if not pending:
        return

    count = len(pending)
    plural = "s" if count != 1 else ""
    verb = "have" if count != 1 else "has"
    print(f"{count} experiment{plural} currently {verb} in progress status. Run bolt review to update them.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    if args.command != "log":
        _warn_pending_jobs()
    args.func(args)


if __name__ == "__main__":
    main()
