"""The 'elite lab' command: HTB-style missions with goals, flags, hints, checkers."""
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
    say("FILES  " + str(wd))
    for f in sorted(wd.iterdir()):
        print(f"         - {f.name}")
    print()
    say("Work in that folder, then submit:  elite lab submit "
        f"{m.id} '{m.flag_format}'")
    say(f"Stuck? Unlock a hint:  elite lab hint {m.id}")
    print()


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


HANDLERS = {"list": lab_list, "start": lab_start, "hint": lab_hint,
            "submit": lab_submit, "status": lab_status}
