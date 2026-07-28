"""Shared helpers used across bolt commands."""

import os
import sys
from datetime import datetime


def now_iso():
    """Return the current local time as an ISO-8601 string (second precision)."""
    return datetime.now().isoformat(timespec="seconds")


def prompt(text):
    """Prompt the user for a line of input, stripped of surrounding whitespace.

    Typing 'q' (case-insensitive) at any prompt cancels the current command.
    """
    try:
        value = input(text).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        die("Aborted.")

    if value.lower() == "q":
        print("Cancelled.")
        sys.exit(0)

    return value


def die(message, code=1):
    """Print an error message to stderr and exit."""
    print(f"bolt: error: {message}", file=sys.stderr)
    sys.exit(code)


def validate_name(name, what="name"):
    """Validate that a user-supplied name is safe to use as a single path segment."""
    if not name or not name.strip():
        die(f"{what} cannot be empty.")
    if os.sep in name or (os.altsep and os.altsep in name):
        die(f"{what} cannot contain path separators ('{name}').")
    if name in (".", ".."):
        die(f"{what} is not a valid name ('{name}').")
    return name


def choose_from_list(items, formatter=None, prompt_text="Select an option"):
    """Print a numbered list and prompt the user to pick one. Returns the chosen item."""
    if not items:
        return None
    formatter = formatter or (lambda x: str(x))
    for i, item in enumerate(items, start=1):
        print(f"  [{i}] {formatter(item)}")
    while True:
        choice = prompt(f"{prompt_text} (1-{len(items)}, or 'q' to quit): ")
        if choice.isdigit() and 1 <= int(choice) <= len(items):
            return items[int(choice) - 1]
        print(f"Please enter a number between 1 and {len(items)}.")
