"""bolt review [experiment]

Reviews an experiment anywhere at or below the current project/experiment,
including experiments nested inside other experiments. With no argument,
lists every in-progress experiment (shown as paths like . or ./exp2/exp3)
and lets you pick one.
"""

from ..context import require_context, save_context
from ..targets import collect_all_experiments
from ..utils import now_iso, prompt, choose_from_list, die

STATUS_MAP = {
    "c": "complete",
    "complete": "complete",
    "p": "in progress",
    "progress": "in progress",
    "in progress": "in progress",
    "i": "inconclusive",
    "inconclusive": "inconclusive",
    "f": "fail",
    "fail": "fail",
}


def register(subparsers):
    p = subparsers.add_parser(
        "review",
        help="Review an experiment's status (searches nested experiments too).",
        description=(
            "Review an experiment at or below the current project or "
            "experiment, including experiments nested inside other "
            "experiments. If none is given, you'll be prompted to choose "
            "from all in-progress experiments found."
        ),
    )
    p.add_argument(
        "experiment",
        nargs="?",
        default=None,
        help=(
            "Name or relative path of the experiment to review (e.g. "
            "'mapping' or './phylogeny/pathphynder'). If omitted, you'll be "
            "prompted to pick one."
        ),
    )
    p.set_defaults(func=run)


def run(args):
    directory, data = require_context(allowed_types={"project", "experiment"})

    # A project itself has no status; only its experiments do. When run from
    # a project root, don't offer the project as a reviewable target.
    include_root = data.get("type") == "experiment"
    all_exps = collect_all_experiments(
        directory, include_archived=False, include_root=include_root
    )

    if not all_exps:
        die("No experiments found to review here.")

    if args.experiment:
        target = args.experiment
        norm = target if target.startswith("./") else f"./{target}"
        matches = [
            e for e in all_exps
            if e["data"]["name"] == target or e["rel"] in (target, norm)
        ]
        if not matches:
            die(f"No experiment matching '{target}' found below the current directory.")
        if len(matches) > 1:
            options = ", ".join(m["rel"] for m in matches)
            die(f"Multiple experiments match '{target}' ({options}); specify the full path.")
        entry = matches[0]
    else:
        in_progress = [e for e in all_exps if e["data"].get("status") == "in progress"]
        if not in_progress:
            die("No in-progress experiments to review. Specify one explicitly instead.")
        print("In-progress experiments:")
        entry = choose_from_list(
            in_progress,
            formatter=lambda e: e["rel"],
            prompt_text="Select an experiment to review",
        )

    exp_data = entry["data"]

    status_input = prompt("Status ([c]omplete / in [p]rogress / [i]nconclusive / [f]ail): ")
    status = STATUS_MAP.get(status_input.strip().lower())
    while status is None:
        status_input = prompt("Please enter one of c/p/i/f: ")
        status = STATUS_MAP.get(status_input.strip().lower())

    result_text = prompt("Status description: ")
    timestamp = now_iso()

    exp_data.setdefault("reviews", []).append(
        {
            "timestamp": timestamp,
            "status": status,
            "result": result_text,
        }
    )
    exp_data["status"] = status
    exp_data["status_description"] = result_text
    exp_data["review_timestamp"] = timestamp

    save_context(entry["dir"], exp_data)

    print(f"Recorded review for '{entry['rel']}': {status}")