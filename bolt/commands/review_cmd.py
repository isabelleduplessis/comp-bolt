"""bolt review [job]

Reviews a job anywhere below the current project/experiment, including jobs
inside nested experiments. With no argument, lists all pending jobs (shown
as paths like ./job1.sh or ./exp2/job2.sh) and lets you pick one.
"""

from ..context import require_context, save_context
from ..targets import collect_all_jobs
from ..utils import now_iso, prompt, choose_from_list, die

STATUS_MAP = {
    "s": "success",
    "success": "success",
    "f": "fail",
    "fail": "fail",
    "p": "pending",
    "pending": "pending",
    "i": "inconclusive",
    "inconclusive": "inconclusive",
}


def register(subparsers):
    p = subparsers.add_parser(
        "review",
        help="Review a job (searches nested experiments too) and record its status.",
        description=(
            "Review a job below the current project or experiment, including "
            "jobs inside nested experiments. If no job is given, you'll be "
            "prompted to choose from all pending jobs found."
        ),
    )
    p.add_argument(
        "job",
        nargs="?",
        default=None,
        help=(
            "Name or relative path of the job to review (e.g. 'run.sh' or "
            "'./exp2/job2.sh'). If omitted, you'll be prompted to pick one."
        ),
    )
    p.set_defaults(func=run)


def run(args):
    directory, _ = require_context(allowed_types={"project", "experiment"})
    all_jobs = collect_all_jobs(directory, include_archived=False)

    if not all_jobs:
        die("No jobs found to review here.")

    if args.job:
        target = args.job
        norm = target if target.startswith("./") else f"./{target}"
        matches = [
            j for j in all_jobs
            if j["job"]["name"] == target or j["rel"] in (target, norm)
        ]
        if not matches:
            die(f"No job matching '{target}' found below the current directory.")
        if len(matches) > 1:
            options = ", ".join(m["rel"] for m in matches)
            die(f"Multiple jobs match '{target}' ({options}); specify the full path.")
        entry = matches[0]
    else:
        pending = [j for j in all_jobs if j["job"].get("status") == "pending"]
        if not pending:
            die("No pending jobs to review. Specify a job name explicitly instead.")
        print("Pending jobs:")
        entry = choose_from_list(
            pending,
            formatter=lambda j: j["rel"],
            prompt_text="Select a job to review",
        )

    job_entry = entry["job"]

    status_input = prompt("Status ([s]uccess / [f]ail / [p]ending / [i]nconclusive): ")
    status = STATUS_MAP.get(status_input.strip().lower())
    while status is None:
        status_input = prompt("Please enter one of s/f/p/i: ")
        status = STATUS_MAP.get(status_input.strip().lower())

    result_text = prompt("Status description: ")
    timestamp = now_iso()

    job_entry.setdefault("reviews", []).append(
        {
            "timestamp": timestamp,
            "status": status,
            "result": result_text,
        }
    )
    job_entry["status"] = status
    job_entry["status_description"] = result_text
    job_entry["review_timestamp"] = timestamp

    save_context(entry["exp_dir"], entry["exp_data"])

    print(f"Recorded review for '{entry['rel']}': {status}")
