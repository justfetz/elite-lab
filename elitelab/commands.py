"""Command-drill mode: type the real command, get checked, with spaced repetition.

The muscle-memory engine. Commands live in drills/commands.json (data-driven).
Selection is weighted toward commands you miss or haven't seen, so weak spots
resurface until they stick.
"""
import json
import random
import re
from pathlib import Path

from . import progress
from .ui import ask

BANK = Path(__file__).resolve().parent.parent / "drills" / "commands.json"


def _norm(s):
    return re.sub(r"\s+", " ", s.strip())


def load_bank():
    return json.loads(BANK.read_text())


def matches(cmd, answer):
    n = _norm(answer)
    if n.lower() == _norm(cmd["answer"]).lower():
        return True
    for pat in cmd.get("accept", []):
        try:
            if re.fullmatch(pat, n, re.IGNORECASE):
                return True
        except re.error:
            pass
    return False


def _weight(cid, stats):
    e = stats.get(cid)
    if not e:
        return 5                      # never seen -> show it
    return max(1, 4 - e.get("streak", 0))  # mastered (high streak) -> show less


def drill_commands():
    bank = load_bank()
    last = None
    print("\nType the REAL command for each task. 'skip' to reveal, 'q' to stop.\n")
    answered = 0
    correct = 0
    while True:
        stats = progress.cmd_stats()
        pool = [c for c in bank if c["id"] != last] or bank
        weights = [_weight(c["id"], stats) for c in pool]
        c = random.choices(pool, weights=weights)[0]
        last = c["id"]
        print(f"[{c['platform']}] {c['prompt']}")
        a = ask("> ")
        if a.lower() in ("q", "quit"):
            break
        if a.lower() == "skip":
            print(f"  answer: {c['answer']}\n")
            continue
        ok = matches(c, a)
        progress.cmd_record(c["id"], ok)
        answered += 1
        correct += ok
        if ok:
            print(f"  correct. {c.get('why', '')}\n")
        else:
            print(f"  not quite -> {c['answer']}\n  {c.get('why', '')}\n")
    if answered:
        print(f"\nCommand drill: {correct}/{answered} correct this session.\n")
