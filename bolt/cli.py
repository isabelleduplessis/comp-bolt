"""Comp-BOLT command line interface."""

import argparse
import sys

from . import __version__
from .commands import (
    init_cmd,
    new_cmd,
    job_cmd,
    review_cmd,
    note_cmd,
    update_cmd,
    archive_cmd,
    log_cmd,
)
from .context import find_project_root
from .targets import collect_all_jobs

DESCRIPTION = (
    "Comp-BOLT: Computational Biology project Organization, Logging, and Tracking\n\n"
    "Frictionless, well-documented project directories for computational\n"
    "biology work. Bolt wraps mkdir/touch with hidden .bolt.yml metadata\n"
    "tracking projects, experiments, jobs, notes, and reviews."
)

EPILOG = """\
examples:
  bolt init "ID015_mammoth_phylogeny"    create a new project
  bolt new "pathphynder"                 create an experiment in the current dir
  bolt job "run_pathphynder.sh"          create a job script in the current experiment
  bolt job "v2.sh" -c v1.sh              create a job by copying an existing script
  bolt review                            review a pending job (searches nested experiments)
  bolt review ./exp2/job2.sh             review a specific job by path
  bolt note "Received new sequencing data"
  bolt note -e                           edit an existing note
  bolt note -v                           view notes in the current directory
  bolt update pathphynder                rename / re-describe something
  bolt archive run_pathphynder.sh        archive a job, experiment, or project
  bolt archive -s                        show active vs. archived items
  bolt log > project_report.md           generate a report from metadata
  bolt log pathphynder -p                plain-text summary of one experiment

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
    job_cmd.register(subparsers)
    review_cmd.register(subparsers)
    note_cmd.register(subparsers)
    update_cmd.register(subparsers)
    archive_cmd.register(subparsers)
    log_cmd.register(subparsers)

    return parser


def _warn_pending_jobs():
    """If run inside a project, warn (non-blocking) about pending jobs anywhere in it."""
    root_dir, root_data = find_project_root()
    if root_dir is None:
        return

    all_jobs = collect_all_jobs(root_dir, cwd=root_dir, include_archived=False)
    pending = [j for j in all_jobs if j["job"].get("status") == "pending"]
    if not pending:
        return

    count = len(pending)
    plural = "s" if count != 1 else ""
    verb = "have" if count != 1 else "has"
    print(f"{count} job{plural} currently {verb} pending status. Run bolt review to update them.")


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    _warn_pending_jobs()
    args.func(args)


if __name__ == "__main__":
    main()
