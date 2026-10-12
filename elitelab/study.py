"""`elite study <ask|summarize|lesson|search|index> "..."` - your own books, from the CLI.

Thin bridge to study_books.py (the local RAG over books you own in ./books/), so you can
type `elite study ask "how does an access check work?"` instead of the longer form.
Everything stays local; see LIBRARY.md for setup.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "study_books.py"


def _load():
    spec = importlib.util.spec_from_file_location("study_books", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def study(args):
    sb = _load()
    action = args.study_action
    text = " ".join(args.text or [])
    if action == "index":
        sb.build()
        return
    if not text:
        print(f'Usage:  elite study {action} "your question or topic"')
        return
    {"ask": sb.cmd_ask, "summarize": sb.cmd_summarize,
     "lesson": sb.cmd_lesson, "search": sb.cmd_search}[action](text)
