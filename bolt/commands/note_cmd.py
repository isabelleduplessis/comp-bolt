"""bolt note ["text"] | bolt note -e/--edit | bolt note -v/--view"""

import os

from ..context import require_context, save_context, bolt_file_path, load_context
from ..utils import now_iso, prompt, choose_from_list, die


def register(subparsers):
    p = subparsers.add_parser(
        "note",
        help="Add, edit, or view timestamped notes on a project/experiment.",
        description="Add a timestamped note to the current project or experiment.",
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
        help=(
            "Print notes for the current directory and every experiment "
            "nested inside it, grouped by relative path."
        ),
    )
    p.set_defaults(func=run)


def _format_note(note):
    preview = note["text"].replace("\n", " ")
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return f"{note['timestamp']}  {preview}"


def _collect_notes(root_dir, cwd):
    """Recursively gather notes from root_dir and every nested experiment
    below it. Returns a list of (rel_path, name, notes)."""
    results = []
    data = load_context(root_dir)
    notes = data.get("notes", [])
    if notes:
        rel = os.path.relpath(root_dir, cwd)
        rel_display = "." if rel == "." else (rel if rel.startswith(".") else f"./{rel}")
        results.append((rel_display, data.get("name"), notes))

    for entry in sorted(os.listdir(root_dir)):
        sub = os.path.join(root_dir, entry)
        if os.path.isdir(sub) and os.path.isfile(bolt_file_path(sub)):
            sub_data = load_context(sub)
            if sub_data.get("type") == "experiment":
                results.extend(_collect_notes(sub, cwd))

    return results


def run(args):
    directory, data = require_context(allowed_types={"project", "experiment"})
    notes = data.setdefault("notes", [])

    if args.view:
        groups = _collect_notes(directory, directory)
        if not groups:
            print("No notes here.")
            return
        for rel, name, group_notes in groups:
            print(f"{rel} ({name}):")
            for note_entry in group_notes:
                print(f"  [{note_entry['timestamp']}] {note_entry['text']}")
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
