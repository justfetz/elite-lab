"""Mission model.

A mission is an HTB-style challenge: a goal, an artifact you work on, a flag you
capture, a checker that verifies it, and hints you can unlock. Missions are
deterministic - setup() and solution() both derive from a fixed per-mission seed,
so the correct flag is never stored on disk for the learner to peek at.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List


def normalize(flag: str) -> str:
    """Forgiving comparison: ignore case, surrounding space, and flag{...} wrapper."""
    f = flag.strip().lower()
    if f.startswith("flag{") and f.endswith("}"):
        f = f[5:-1]
    return f.strip()


@dataclass
class Mission:
    id: str                       # e.g. "wire-01"
    layer: str                    # e.g. "1 The Wire"
    title: str
    difficulty: str               # intro | easy | medium | hard
    goal: str                     # what the learner must achieve
    flag_format: str              # e.g. "flag{IP:PASSWORD}"
    setup: Callable[[Path], None]            # write artifacts into the mission workdir
    solution: Callable[[Path], str] = lambda wd: ""   # correct flag (unused if checker set)
    hints: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    debrief: str = ""             # shown after success: the lesson + the defense
    # Optional custom checker for "fix it" / build missions: (workdir, submitted) -> bool.
    # When set, it replaces the default flag comparison.
    checker: Callable[[Path, str], bool] = None

    def check(self, workdir: Path, submitted: str) -> bool:
        if self.checker is not None:
            return self.checker(workdir, submitted)
        return normalize(submitted) == normalize(self.solution(workdir))
