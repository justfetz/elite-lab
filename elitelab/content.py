"""Loads course modules from the modules/ directory.

A module is a JSON file with this shape:

    {
      "key": "networking",
      "title": "Networking fundamentals",
      "order": 10,
      "lessons":  [ {"title": "...", "body": "..."}, ... ],
      "quiz":     [ {"q": "...", "options": [...], "answer": 0, "why": "..."}, ... ],
      "tools":    [ {"name": "nmap", "what": "...", "legal": "...",
                     "install": "...", "try": ["cmd", ...], "exercise": "..."}, ... ]
    }

Every field except key/title is optional, so a module can be lessons-only,
a tool reference, or a mix. Content is data, not code, so you extend the
course by dropping in a new JSON file - no Python changes needed.
"""
import json
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parent.parent / "modules"


def load_modules():
    """Return an ordered dict-like list of (key, module) sorted by 'order' then title."""
    mods = {}
    for path in sorted(MODULES_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            raise SystemExit(f"Could not read module {path.name}: {e}")
        key = data.get("key") or path.stem
        data.setdefault("lessons", [])
        data.setdefault("quiz", [])
        data.setdefault("tools", [])
        data["key"] = key
        mods[key] = data
    return dict(sorted(mods.items(), key=lambda kv: (kv[1].get("order", 999), kv[1]["title"])))


def get_module(modules, key):
    if key not in modules:
        keys = ", ".join(modules)
        raise SystemExit(f"Unknown module '{key}'. Available: {keys}")
    return modules[key]
