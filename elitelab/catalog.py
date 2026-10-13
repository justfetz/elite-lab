"""`elite catalog` - the card catalog. A flat inventory of every material available
to the learner: learn modules, missions, drills, tool briefings, your books, the
live lab, and the reference docs. "What is there to work with?" in one list."""
import pickle
from pathlib import Path

from . import progress
from .content import load_modules
from .drills import DRILLS
from .missions import load_missions

ROOT = Path(__file__).resolve().parent.parent
BOOK_INDEX = ROOT / ".book_index.pkl"
DOCS = [("README.md", "start here"), ("map (elite map)", "the territory + how it connects"),
        ("SCENARIO.md", "the company story"), ("CURRICULUM.md", "the layer map"),
        ("LIBRARY.md", "set up your local AI book tutor"), ("TOOLS.md", "the tool/library index"),
        ("PRINCIPLES.md", "the design rules"), ("ATLAS.md", "live status / what's next")]


def _count(mod):
    bits = []
    n = len(mod["lessons"])
    if n:
        bits.append(f"{n} lesson" + ("" if n == 1 else "s"))
    if mod["quiz"]:
        bits.append("quiz")
    if mod["tools"]:
        bits.append(f"{len(mod['tools'])} tool" + ("" if len(mod['tools']) == 1 else "s"))
    return ", ".join(bits)


def catalog(args=None):
    modules = load_modules()
    missions = load_missions()
    lessons = sum(len(m["lessons"]) for m in modules.values())
    tools = sum(len(m["tools"]) for m in modules.values())

    print("\n  THE MATERIALS -- everything available to you\n")

    print(f"  LEARN MODULES ({lessons} lessons)   -- elite learn <topic>  /  elite quiz <topic>")
    for key, mod in modules.items():
        print(f"    {key:<16} {mod['title']:<40} {_count(mod)}")

    print(f"\n  MISSIONS ({len(missions)})   -- elite lab start <id>     (x = cleared)")
    layer = None
    for mid, m in missions.items():
        if m.layer != layer:
            layer = m.layer
            print(f"    {layer}")
        mark = "x" if progress.lab_state(mid)["solved"] else " "
        print(f"      [{mark}] {mid:<14} {m.title}")

    print(f"\n  DRILLS   -- elite drill <kind>")
    print(f"    {', '.join(DRILLS)}   (muscle-memory reps, spaced repetition)")

    print(f"\n  TOOL BRIEFINGS ({tools})   -- elite tools   (nmap, sqlmap, John, Hydra, Ghidra ...)")

    print(f"\n  YOUR BOOKS   -- elite study ask \"...\"")
    if BOOK_INDEX.exists():
        try:
            meta = pickle.loads(BOOK_INDEX.read_bytes()).get("meta", [])
            print(f"    {len({m[0] for m in meta})} books, {len(meta):,} pages indexed (local AI). See LIBRARY.md")
        except Exception:
            print("    index present. See LIBRARY.md")
    else:
        print("    not set up -- run a free local model over books you own. See LIBRARY.md")

    print(f"\n  THE LIVE LAB   -- live-lab/   (host the company for real)")
    print("    orderdesk/   the customer portal + PM3 mill dashboard (python app.py)")
    print("    loadmaster/  the cutting-stock optimizer (python cutstock.py)")
    print("    db/          the millops SQL Server schema")

    print(f"\n  REFERENCE DOCS")
    for name, desc in DOCS:
        print(f"    {name:<22} {desc}")
    print()
