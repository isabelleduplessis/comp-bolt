"""bolt note ["text"] | bolt note -e/--edit"""

from ..context import require_context, save_context
from ..utils import now_iso, prompt, choose_from_list, die


def register(subparsers):
    p = subparsers.add_parser(
        "note",
        help="Add or edit a timestamped note on the current project/experiment.",
        description=(
            "Add a timestamped note to the current project or experiment. "
            "Jobs do not have notes."
        ),
    )
    p.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Note text. If omitted, you will be prompted to type one.",
    )
    p.add_argument(
        "-e",
        "--edit",
        action="store_true",
        help="Edit an existing note (fix a typo) instead of adding a new one.",
    )
    p.add_argument(
        "-v",
        "--view",
        action="store_true",
        help="Print the notes for the current project/experiment instead of adding one.",
    )
    p.set_defaults(func=run)


def _format_note(note):
    preview = note["text"].replace("\n", " ")
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return f"{note['timestamp']}  {preview}"


def run(args):
    directory, data = require_context(allowed_types={"project", "experiment"})
    notes = data.setdefault("notes", [])

    if args.view:
        if not notes:
            print("No notes here.")
            return
        for note_entry in notes:
            print(f"[{note_entry['timestamp']}] {note_entry['text']}")
        return

    if args.edit:
        if not notes:
            die("There are no notes to edit yet.")
        print("Notes:")
        note_entry = choose_from_list(
            notes, formatter=_format_note, prompt_text="Select a note to edit"
        )
        print(f"Current text: {note_entry['text']}")
        new_text = prompt("New text: ")
        if not new_text:
            die("Note text cannot be empty.")
        note_entry["text"] = new_text
        save_context(directory, data)
        print("Note updated.")
        return

    text = args.text
    if text is None:
        text = prompt("Note: ")
    if not text:
        die("Note text cannot be empty.")

    notes.append({"timestamp": now_iso(), "text": text})
    save_context(directory, data)

    print("Note added.")
