"""Tiny JSON progress store in the user's home directory."""
import json
import time
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
    entry["last_pct"] = pct
    entry["attempts"] = entry.get("attempts", 0) + 1
    entry["last"] = time.time()
    save(p)
    return entry


def lab_state(mission_id):
    return load().get("labs", {}).get(mission_id, {"hints": 0, "solved": False, "tries": 0})


def lab_update(mission_id, **changes):
    p = load()
    labs = p.setdefault("labs", {})
    entry = labs.setdefault(mission_id, {"hints": 0, "solved": False, "tries": 0})
    entry.update(changes)
    entry["last"] = time.time()
    save(p)
    return entry


def cmd_stats():
    return load().get("cmddrill", {})


def cmd_record(cid, correct):
    p = load()
    d = p.setdefault("cmddrill", {})
    e = d.setdefault(cid, {"seen": 0, "correct": 0, "streak": 0})
    e["seen"] += 1
    if correct:
        e["correct"] += 1
        e["streak"] = e.get("streak", 0) + 1
    else:
        e["streak"] = 0
    e["last"] = time.time()
    save(p)
    return e
