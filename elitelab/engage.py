"""`elite engage` - the connected Lakefront engagement (open sandbox + loot chaining).

Recon reveals the whole company surface. Each target maps to a mission; solving it
yields LOOT, and deeper targets stay locked until you hold the loot that reaches them
(web app -> DB service credential -> Domain Admin). State is DERIVED from your lab
progress, and the target list + the recon map are DERIVED from the world registry
(elitelab/world.py), so nothing here can drift out of sync with the rest of the tool.
"""
from . import progress, world
from .missions import load_missions


def _targets():
    """The engagement board = the live-network exercises, grouped by their system,
    in the registry's campaign order. Built fresh from the registry every call."""
    targets = []
    for s in world.systems():
        for e in world.exercises_on(s.id):
            if not e.board:
                continue
            loc = f"{s.name}  ({s.addr})" if s.addr else s.name
            targets.append({
                "mission": e.mission, "area": loc, "desc": e.skill,
                "grants": e.grants, "requires": e.requires,
            })
    return targets


def _recon_text():
    """The recon map = every system on the wire, straight from the registry."""
    lines = ["Recon complete. Lakefront Paper's surface:\n"]
    for z in world.zones():
        hosts = [s for s in world.systems_in(z.id) if s.addr]
        if not hosts:
            continue
        lines.append(f"  [{z.name}]")
        for s in hosts:
            lines.append(f"    {s.addr:<11} {s.id:<11} {s.blurb}")
        lines.append("")
    lines.append("Everything is open - hit it in any order. But the deepest targets need loot you")
    lines.append("only get by breaking something else first (the web app leaks a credential that is")
    lines.append("also a domain account; local root on ws01 reaches the licensed binary). Chase the")
    lines.append("chain -- and note the one conduit between the business side and the plant floor.")
    return "\n".join(lines)


def _loot(solved, targets):
    loot = set()
    for t in targets:
        if t["mission"] in solved:
            loot.update(t["grants"])
    return loot


def _status(t, solved, loot):
    if t["mission"] in solved:
        return "done"
    if t["requires"] and not (set(t["requires"]) & loot):
        return "locked"
    return "open"


def _reconned():
    return progress.load().get("engagement", {}).get("reconned", False)


def engage(args):
    action = getattr(args, "engage_action", None)
    if action == "recon":
        p = progress.load()
        p.setdefault("engagement", {})["reconned"] = True
        progress.save(p)
        print("\n" + _recon_text())
        print("\nSee your targets:  elite engage\n")
        return

    missions = load_missions()
    targets = _targets()
    solved = {mid for mid in missions if progress.lab_state(mid)["solved"]}
    if not _reconned():
        print("\nYou've been hired to assess Lakefront Paper. Start by mapping the surface:\n"
              "  elite engage recon\n")
        return

    loot = _loot(solved, targets)
    done = sum(1 for t in targets if t["mission"] in solved)
    print(f"\nLakefront Paper - engagement   ({done}/{len(targets)} targets cleared)")
    print("Loot: " + (", ".join(sorted(loot)) if loot else "(none yet)") + "\n")

    area = None
    marks = {"done": "[x]", "open": "[>]", "locked": "[#]"}
    for t in targets:
        if t["area"] != area:
            area = t["area"]
            print(f"  {area}")
        st = _status(t, solved, loot)
        print(f"    {marks[st]} {t['mission']:<13} {t['desc']}")
        if st == "open":
            m = missions.get(t["mission"])
            goal = (m.goal.split(". ")[0] if m else "")[:88]
            print(f"          goal: {goal}")
            print(f"          ->    elite lab start {t['mission']}")
        elif st == "locked":
            print(f"          locked - need: " + " or ".join(t["requires"]))

    openset = [t for t in targets if _status(t, solved, loot) == "open"]
    print("\n  Your toolkit (build these any time): " + ", ".join(world.toolkit()))
    print("  The incident chains:  elite scenario")
    if openset:
        print(f"\nAvailable now: {', '.join(t['mission'] for t in openset[:4])}"
              f"{' ...' if len(openset) > 4 else ''}")
        print(f"Go:  elite lab start {openset[0]['mission']}\n")
    elif done == len(targets):
        print("\nEvery target cleared and every break hardened. You assessed the whole company. "
              "That's the job.\n")
    else:
        print("\nEverything available is done - clear a dependency to unlock the locked targets.\n")
