"""Command-line interface for elite-lab."""
import argparse
import sys

from . import __version__, progress
from .content import load_modules, get_module
from .drills import DRILLS
from .lab import HANDLERS as LAB_HANDLERS
from .ui import run_lessons, run_quiz, show_tools, ask


def cmd_list(modules, args):
    p = progress.load()
    print("\nModules (elite learn <name>):\n")
    for key, mod in modules.items():
        def plural(n, word):
            return f"{n} {word}" + ("" if n == 1 else "s")
        bits = []
        if mod["lessons"]:
            bits.append(plural(len(mod["lessons"]), "lesson"))
        if mod["quiz"]:
            bits.append("quiz")
        if mod["tools"]:
            bits.append(plural(len(mod["tools"]), "tool"))
        best = p.get(key, {}).get("best")
        score = f"  [best {best}%]" if best is not None else ""
        print(f"  {key:<16} {mod['title']:<30} {', '.join(bits)}{score}")
    print(f"\nDrills (elite drill <name>): {', '.join(DRILLS)}")
    print("Tools briefings: elite tools <module>")
    print("Progress: elite progress\n")


def cmd_learn(modules, args):
    run_lessons(get_module(modules, args.module))


def cmd_quiz(modules, args):
    run_quiz(get_module(modules, args.module), record_fn=progress.record_quiz)


def cmd_tools(modules, args):
    show_tools(get_module(modules, args.module))


def cmd_drill(modules, args):
    DRILLS[args.kind]()


def cmd_progress(modules, args):
    p = progress.load()
    if not p:
        print("\nNo quizzes taken yet. Start with:  elite learn networking\n")
        return
    print()
    for key, mod in modules.items():
        e = p.get(key)
        if e:
            print(f"  {key:<16} best {e['best']}%  over {e['attempts']} attempt(s)")
    print()


def cmd_reset(modules, args):
    if ask("Clear all progress? [y/N] ").lower() == "y":
        progress.save({})
        print("Cleared.")


def build_parser(modules):
    keys = list(modules)
    p = argparse.ArgumentParser(prog="elite", description="Learn networking, Windows internals and security tooling.")
    p.add_argument("--version", action="version", version=f"elite-lab {__version__}")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("list", help="show all modules and progress")
    for name, help_ in [("learn", "read a module's lessons"),
                        ("quiz", "quiz yourself on a module"),
                        ("tools", "show a module's tool briefings")]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("module", choices=keys)
    sp = sub.add_parser("drill", help="endless practice")
    sp.add_argument("kind", choices=list(DRILLS))
    sub.add_parser("progress", help="show quiz scores")
    sub.add_parser("reset", help="clear progress")

    # ask: the in-tool tutor
    ap = sub.add_parser("ask", help="ask a question; answers from the course (and your books)")
    ap.add_argument("query", nargs="+", help='e.g. elite ask "how does an access check work"')

    # path: the guided campaign
    sub.add_parser("path", help="guided campaign through the missions, with your progress")

    # review: the spaced-repetition coach
    sub.add_parser("review", help="what to redo now: weak spots + stale mastery")

    # engage: the connected company engagement (open sandbox)
    ep = sub.add_parser("engage", help="assess Vantaris AI as one connected engagement")
    ep.add_argument("engage_action", nargs="?", choices=["recon"],
                    help="'recon' to reveal the surface; omit for the target board")

    # run: command a real tool, learn the lesson
    rp = sub.add_parser("run", help="run a real security tool and get a taught debrief")
    rp.add_argument("toolargs", nargs=argparse.REMAINDER,
                    help="tool and its args, e.g. nmap 127.0.0.1")

    # lab: HTB-style missions
    lab = sub.add_parser("lab", help="missions: goal, flag, hints, checker")
    lsub = lab.add_subparsers(dest="lab_action")
    lsub.add_parser("list", help="list missions")
    lsub.add_parser("status", help="your mission progress")
    for name in ("start", "hint"):
        q = lsub.add_parser(name)
        q.add_argument("mission")
    q = lsub.add_parser("submit")
    q.add_argument("mission")
    q.add_argument("flag")
    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    modules = load_modules()
    parser = build_parser(modules)
    handlers = {"list": cmd_list, "learn": cmd_learn, "quiz": cmd_quiz,
                "tools": cmd_tools, "drill": cmd_drill,
                "progress": cmd_progress, "reset": cmd_reset}
    args = parser.parse_args(argv)
    if not args.command:
        cmd_list(modules, args)
        print("Run 'elite learn networking' to begin, or 'elite lab list' for missions.")
        return
    if args.command == "lab":
        action = args.lab_action or "list"
        LAB_HANDLERS[action](args)
        return
    if args.command == "run":
        from .runner import run as run_tool
        run_tool(args)
        return
    if args.command == "path":
        LAB_HANDLERS["campaign"](args)
        return
    if args.command == "ask":
        from .ask import ask as ask_tutor
        ask_tutor(" ".join(args.query))
        return
    if args.command == "engage":
        from .engage import engage
        engage(args)
        return
    if args.command == "review":
        from .review import review
        review(args)
        return
    handlers[args.command](modules, args)
