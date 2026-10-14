"""`elite scenario` - the incident chains.

A scenario is the campaign unit above a single exercise: an ordered chain of
missions around ONE incident, held together by a business invariant ("can
Lakefront keep producing and shipping?"). The shape is always the full loop --
break it, DETECT it in the evidence, fix it, and prove legitimate work still
flows. Scenarios are defined in the world registry (elitelab/world.py).

  elite scenario            list the incident chains
  elite scenario <id>       walk one chain step by step, with your progress
"""
from . import progress, world
from .missions import load_missions

_VERB_TAG = {"break": "RED ", "fix": "BLUE", "detect": "HUNT",
             "build": "TOOL", "recon": "RECON"}


def _step_lines(sc, missions):
    for step in sc.steps:
        e = world.exercise(step)
        m = missions.get(step)
        solved = progress.lab_state(step)["solved"]
        mark = "[x]" if solved else "[ ]"
        verb = _VERB_TAG.get(e.verb, e.verb.upper()) if e else "?"
        title = m.title if m else step
        yield f"    {mark} {verb}  {step:<13} {title}"
        if e and e.invariant:
            yield f"              keep working: {e.invariant}"


def scenario(args):
    sid = getattr(args, "scenario_id", None)
    missions = load_missions()

    if not sid:
        print("\n  INCIDENT CHAINS -- secure Lakefront end to end\n")
        print("  Each chain is one incident: break it, catch it in the logs, fix it, and")
        print("  prove the business keeps running. Deeper than any single mission.\n")
        for sc in world.scenarios():
            steps = sc.steps
            done = sum(1 for s in steps if progress.lab_state(s)["solved"])
            print(f"    {sc.id:<22} {sc.title}   ({done}/{len(steps)})")
            print(f"      {sc.question}")
        print("\n  Walk one:  elite scenario <id>\n")
        return

    sc = world.scenario(sid)
    if not sc:
        ids = ", ".join(s.id for s in world.scenarios())
        raise SystemExit(f"Unknown scenario '{sid}'. Try one of: {ids}")

    done = sum(1 for s in sc.steps if progress.lab_state(s)["solved"])
    next_step = next((s for s in sc.steps if not progress.lab_state(s)["solved"]), None)
    print(f"\n  {sc.title}   ({done}/{len(sc.steps)} steps)\n")
    print(f"  THE QUESTION  {sc.question}\n")
    print("  WHAT HAPPENS")
    for line in _wrap(sc.narrative, 4, 74):
        print(line)
    print("\n  THE CHAIN   (RED break / HUNT detect / BLUE fix)")
    for line in _step_lines(sc, missions):
        print(line)
    if next_step:
        print(f"\n  >> NEXT  elite lab start {next_step}\n")
    else:
        print("\n  Chain complete -- you broke it, caught it, fixed it, and kept Lakefront "
              "running.\n")


def _wrap(text, indent, width):
    words, line, out = text.split(), "", []
    pad = " " * indent
    for w in words:
        if len(line) + len(w) + 1 > width:
            out.append(pad + line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        out.append(pad + line)
    return out
