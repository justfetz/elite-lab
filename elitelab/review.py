"""`elite review` - the spaced-repetition coach.

Looks at everything you've done and tells you what to redo NOW, ranked: missions you
barely cleared or left unfinished, quizzes you scored low on, commands you keep missing,
and mastery that's gone stale (spaced repetition). The point is retention - the thing that
actually separates people who get good from people who don't.
"""
import time

from . import progress
from .content import load_modules
from .missions import load_missions

DAY = 86400
STALE_DAYS = 7          # mastered items older than this resurface for a re-prove


def _age_days(last):
    return (time.time() - last) / DAY if last else None


def review(args):
    p = progress.load()
    modules = load_modules()
    missions = load_missions()
    items = []   # (priority, reason, action)  -- lower priority number = more urgent

    # 1) Unfinished missions you started but didn't capture
    for mid, m in missions.items():
        st = progress.lab_state(mid)
        if st.get("started") and not st["solved"]:
            items.append((1, f"unfinished: {mid} - {m.title}", f"elite lab start {mid}"))

    # 2) Weak quizzes (you took it and scored under 80%)
    for key, mod in modules.items():
        if not mod["quiz"]:
            continue
        e = p.get(key)
        if e and e.get("best", 0) < 80:
            items.append((2, f"weak quiz: {key} (best {e['best']}%)",
                          f"elite learn {key}  then  elite quiz {key}"))

    # 3) Shaky commands (seen a few times, still missing more than you hit)
    cs = progress.cmd_stats()
    weak_cmds = [cid for cid, e in cs.items() if e["seen"] >= 2 and e["correct"] / e["seen"] < 0.6]
    if weak_cmds:
        items.append((2, f"{len(weak_cmds)} command(s) you keep missing", "elite drill commands"))

    # 4) Barely-cleared missions (solved, but it took many tries or all the hints)
    for mid, m in missions.items():
        st = progress.lab_state(mid)
        if st["solved"] and (st["tries"] > 2 or st["hints"] >= 2):
            items.append((3, f"barely cleared {mid} (tries {st['tries']}, hints {st['hints']}) "
                             "- redo it clean, no hints", f"elite lab start {mid}"))

    # 5) Stale mastery (spaced repetition: you had it, prove you still do)
    for mid, m in missions.items():
        st = progress.lab_state(mid)
        age = _age_days(st.get("last"))
        if st["solved"] and age and age > STALE_DAYS:
            items.append((4, f"stale: solved {mid} {int(age)}d ago - still got it?",
                          f"elite lab start {mid}"))

    solved = sum(1 for mid in missions if progress.lab_state(mid)["solved"])
    print(f"\nReview coach   ({solved}/{len(missions)} missions cleared)\n")

    if not items:
        print("  Nothing flagged - you're either fresh or in good shape.")
        print("  Keep moving:  elite engage   (or  elite path )\n")
        return

    items.sort(key=lambda t: t[0])
    labels = {1: "FINISH", 2: "SHORE UP", 3: "REDO CLEAN", 4: "REFRESH"}
    shown_cap = 8
    for prio, reason, action in items[:shown_cap]:
        print(f"  [{labels[prio]}] {reason}")
        print(f"            -> {action}\n")
    if len(items) > shown_cap:
        print(f"  (+{len(items) - shown_cap} more - clear these first.)\n")
    # point them at the single most urgent thing
    top = items[0]
    print(f"Start here:  {top[2]}\n")
