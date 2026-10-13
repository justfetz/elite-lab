"""The 'elite lab' command: HTB-style missions with goals, flags, hints, checkers."""
import shutil
from pathlib import Path

from . import progress
from .missions import load_missions
from .ui import say, rule

WORKROOT = Path.home() / ".elite_lab" / "missions"


def _workdir(mission_id):
    d = WORKROOT / mission_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def lab_list(args):
    missions = load_missions()
    print("\nMissions (elite lab start <id>):\n")
    layer = None
    for mid, m in missions.items():
        if m.layer != layer:
            layer = m.layer
            print(f"  --- Layer {layer} ---")
        st = progress.lab_state(mid)
        mark = "[SOLVED]" if st["solved"] else "        "
        print(f"  {mark} {mid:<10} {m.title:<26} ({m.difficulty})")
    print("\n  elite lab start <id>   set up a mission")
    print("  elite lab hint <id>    reveal the next hint")
    print("  elite lab submit <id> <flag>   check your answer\n")


def _get(missions, mid):
    if mid not in missions:
        raise SystemExit(f"Unknown mission '{mid}'. See: elite lab list")
    return missions[mid]


def lab_start(args):
    m = _get(load_missions(), args.mission)
    wd = _workdir(m.id)
    m.setup(wd)
    progress.lab_update(m.id, started=True)
    rule(f"{m.id}: {m.title}   (Layer {m.layer}, {m.difficulty})")
    print()
    say("GOAL   " + m.goal)
    if m.tools:
        say("TOOLS  " + ", ".join(m.tools))
        from .cheat import CHEATS, ALIASES
        refs = []
        for t in m.tools:
            for word in t.lower().replace("/", " ").split():
                key = ALIASES.get(word, word)
                if key in CHEATS and key not in refs:
                    refs.append(key)
        if refs:
            say("CHEAT  need the commands? " + "  ".join(f"elite cheat {r}" for r in refs))
    say("FILES  " + str(wd))
    for f in sorted(wd.iterdir()):
        print(f"         - {f.name}")
    print()
    say("Work in that folder, then submit:  elite lab submit "
        f"{m.id} '{m.flag_format}'")
    say(f"Stuck? Unlock a hint:  elite lab hint {m.id}")
    say(f"Want a clean slate?  elite lab restart {m.id}")
    print()


def lab_restart(args):
    """Wipe a mission's working files AND its saved state, then set it up fresh."""
    m = _get(load_missions(), args.mission)
    wd = _workdir(m.id)
    if wd.exists():
        shutil.rmtree(wd)                 # throw away any edits/files you made
    progress.lab_reset(m.id)              # forget hints/tries/solved for this one
    print(f"\n  Restarted {m.id}: fresh files, and its hints/tries/solved cleared.")
    lab_start(args)                       # rebuild and show it like a first start


def lab_hint(args):
    m = _get(load_missions(), args.mission)
    st = progress.lab_state(m.id)
    shown = st["hints"]
    if shown >= len(m.hints):
        print("\nNo more hints - you have them all. Re-read them in order and try the commands.\n")
        return
    print(f"\nHint {shown + 1}/{len(m.hints)}:")
    say("  " + m.hints[shown])
    progress.lab_update(m.id, hints=shown + 1)
    print()


def lab_submit(args):
    m = _get(load_missions(), args.mission)
    wd = _workdir(m.id)
    if not any(wd.iterdir()):
        raise SystemExit(f"Set the mission up first:  elite lab start {m.id}")
    st = progress.lab_state(m.id)
    tries = st["tries"] + 1
    if m.check(wd, args.flag):
        progress.lab_update(m.id, solved=True, tries=tries)
        print("\n  *** CORRECT - flag captured! ***\n")
        rule("Debrief")
        say(m.debrief)
        print()
    else:
        progress.lab_update(m.id, tries=tries)
        print(f"\n  Not the flag (attempt {tries}). Check the exact format: {m.flag_format}")
        print(f"  Need a nudge?  elite lab hint {m.id}\n")


def lab_status(args):
    missions = load_missions()
    print()
    for mid, m in missions.items():
        st = progress.lab_state(mid)
        state = "solved" if st["solved"] else ("in progress" if st.get("started") else "not started")
        print(f"  {mid:<10} {state:<12} hints used {st['hints']}/{len(m.hints)}  tries {st['tries']}")
    print()


# Recommended campaign order (layer by layer). Only real missions.
CAMPAIGN = [
    "wire-01", "build-01", "build-02",
    "crack-01",
    "app-01", "app-01-fix", "idor-01", "idor-01-fix",
    "bin-01", "priv-01", "build-03", "build-04",
    "domain-01", "domain-01-fix",
    "ai-01", "ai-01-fix",
    "hunt-01",
    "phish-01",
    "mill-01", "mill-01-fix",
]


def campaign(args):
    missions = load_missions()
    order = [m for m in CAMPAIGN if m in missions]
    solved = {mid for mid in order if progress.lab_state(mid)["solved"]}
    next_id = next((m for m in order if m not in solved), None)
    print(f"\nLakefront Paper — your campaign   ({len(solved)}/{len(order)} solved)\n")
    layer = None
    for mid in order:
        m = missions[mid]
        if m.layer != layer:
            layer = m.layer
            print(f"  Layer {layer}")
        mark = "[x]" if mid in solved else ("[>]" if mid == next_id else "[ ]")
        tail = "   <- NEXT" if mid == next_id else ""
        print(f"    {mark} {mid:<13} {m.title}{tail}")
    print()
    if next_id:
        print(f"Next:  elite lab start {next_id}\n")
    else:
        print("Every mission cleared. You've worked the whole surface - nice.\n")


HANDLERS = {"list": lab_list, "start": lab_start, "hint": lab_hint,
            "submit": lab_submit, "status": lab_status, "campaign": campaign,
            "restart": lab_restart}
