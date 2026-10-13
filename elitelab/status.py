"""`elite status` - the home screen. One place that answers "where am I, what have
I done, what's next, and what's available?" so you're never untethered from the goal."""
import pickle
from pathlib import Path

from . import progress
from .content import load_modules
from .lab import CAMPAIGN
from .missions import load_missions

ROOT = Path(__file__).resolve().parent.parent
BOOK_INDEX = ROOT / ".book_index.pkl"


def _bar(done, total, width=14):
    filled = round(width * done / total) if total else 0
    return "#" * filled + "-" * (width - filled)


def _books():
    """(n_books, n_chunks) if the study index exists, else None."""
    if not BOOK_INDEX.exists():
        return None
    try:
        data = pickle.loads(BOOK_INDEX.read_bytes())
        meta = data.get("meta", [])
        return len({m[0] for m in meta}), len(meta)
    except Exception:
        return None


def status(args=None):
    missions = load_missions()
    order = [m for m in CAMPAIGN if m in missions]
    solved = {mid for mid in order if progress.lab_state(mid)["solved"]}
    next_id = next((m for m in order if m not in solved), None)

    print("\n  Lakefront Paper & Container Co. -- you're the security team.\n")
    print(f"  PROGRESS   {_bar(len(solved), len(order))}  "
          f"{len(solved)}/{len(order)} targets cleared\n")

    # the surface, grouped by layer, compact
    print("  THE SURFACE")
    layer = None
    line = ""
    for mid in order:
        m = missions[mid]
        if m.layer != layer:
            if line:
                print(line)
            layer = m.layer
            line = f"    {layer:<12} "
        mark = "[x]" if mid in solved else ("[>]" if mid == next_id else "[ ]")
        if len(line) > 66:
            print(line)
            line = f"    {'':<12} "
        line += f"{mark} {mid}   "
    if line:
        print(line)

    # next move
    if next_id:
        print(f"\n  >> YOUR NEXT MOVE\n       elite lab start {next_id}"
              f"      ({missions[next_id].title})")
    else:
        print("\n  >> Every target cleared. Try `elite review` to keep it sharp.")

    # learn
    mods = list(load_modules())
    print("\n  LEARN  (elite learn <topic>)")
    print("    " + " · ".join(mods))

    # books
    b = _books()
    print("\n  YOUR BOOKS  (elite study ask \"...\")")
    if b:
        print(f"    {b[0]} books, {b[1]:,} pages indexed and ready.")
    else:
        print("    Not set up yet -- run a free local AI over books you own. See LIBRARY.md")

    # the map
    print("\n  THE MAP")
    print("    elite map         the company + how it all connects  <- new to this? start here")
    print("    elite status      this screen            elite path        full campaign")
    print("    elite lab ...     start/hint/submit      elite review      what to redo")
    print("    elite learn ...   read a topic           elite quiz ...    test yourself")
    print("    elite ask \"..\"    course tutor           elite study ask   your own books")
    print("    elite tools       the toolkit            elite doctor      setup check")
    print("    elite drill ...   muscle-memory reps     elite engage      the connected job\n")
