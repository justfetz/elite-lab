"""Tiny JSON progress store in the user's home directory."""
import json
from pathlib import Path

PROGRESS_FILE = Path.home() / ".elite_lab_progress.json"


def load():
    try:
        return json.loads(PROGRESS_FILE.read_text())
    except (OSError, ValueError):
        return {}


def save(progress):
    try:
        PROGRESS_FILE.write_text(json.dumps(progress, indent=2))
    except OSError:
        pass  # progress is a convenience, never crash over it


def record_quiz(key, pct):
    p = load()
    entry = p.setdefault(key, {})
    entry["best"] = max(pct, entry.get("best", 0))
    entry["attempts"] = entry.get("attempts", 0) + 1
    save(p)
    return entry
