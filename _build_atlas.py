#!/usr/bin/env python3
"""Generates ATLAS.md and the "what is built" block at the top of README.md.

Nothing in either is typed by hand. Every row and every count is read from the code:

  elitelab/world.py      the registry: zones, systems, exercises, scenarios
  elitelab/missions/     each mission module: title, layer, difficulty, flag or checker
  modules/*.json         the learn modules
  drills/commands.json   the command-drill bank
  elitelab/runner.py     the `elite run` tool tutors
  elitelab/cheat.py      the `elite cheat` sheets

    python3 _build_atlas.py           write ATLAS.md and refresh the README block
    python3 _build_atlas.py --check   write nothing; exit 1 if either is out of date

Unlike the other _build_*.py files this one writes nothing on import, because
tests/test_docs.py imports it and compares its output with the committed files.
So after you add or change a mission, run this script and commit what it writes;
the test suite fails until you do.
"""
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from elitelab import world  # noqa: E402
from elitelab.cheat import CHEATS  # noqa: E402
from elitelab.commands import load_bank  # noqa: E402
from elitelab.content import load_modules  # noqa: E402
from elitelab.drills import DRILLS  # noqa: E402
from elitelab.missions import load_missions  # noqa: E402
from elitelab.runner import TOOLS  # noqa: E402

ATLAS = ROOT / "ATLAS.md"
README = ROOT / "README.md"

# The status line every doc opens with (see the doc map in README.md).
STATUS_LINE = ("> **Doc status: current** · answers: *Which missions exist, where does each "
               "one live, and what is not built yet?* · [doc map](README.md#doc-map)")

# README.md keeps one generated block between these two markers.
BEGIN = ("<!-- BEGIN GENERATED BLOCK: built. _build_atlas.py writes this from the registry; "
         "change the code and rerun it, don't edit here. -->")
END = "<!-- END GENERATED BLOCK: built -->"

FIX_SUFFIX = "-fix"     # a fix twin is its break mission's id plus this suffix


# ---------------------------------------------------------------------------
# small formatting helpers
# ---------------------------------------------------------------------------
def _n(count, noun, plural=None):
    return f"{count} {noun if count == 1 else (plural or noun + 's')}"


def _and(items, last="and"):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + f" {last} " + items[-1]


def _cell(text):
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _ids(ids):
    return " ".join(f"`{i}`" for i in ids)


def _table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in rows:
        out.append("| " + " | ".join(_cell(c) for c in row) + " |")
    return out


# ---------------------------------------------------------------------------
# the facts, read from the code
# ---------------------------------------------------------------------------
class Facts:
    def __init__(self):
        self.missions = load_missions()
        self.exercises = world.exercises()
        self.zones = world.zones()
        self.systems = world.systems()
        self.scenarios = world.scenarios()
        self.modules = load_modules()
        self.bank = load_bank()

        ids = {e.mission for e in self.exercises}
        self.breaks = [e for e in self.exercises if e.verb == "break"]
        self.twin = {e.mission: e.mission + FIX_SUFFIX for e in self.breaks
                     if e.mission + FIX_SUFFIX in ids}

        # what the registry declares that no mission covers yet
        self.empty_systems = [s for s in self.systems if not world.exercises_on(s.id)]
        self.unpaired = [e.mission for e in self.breaks if e.mission not in self.twin]
        self.unused_levels = [lv for lv in world.LEVELS
                              if not any(e.level == lv for e in self.exercises)]
        self.unused_verbs = [v for v in world.VERBS
                             if not any(e.verb == v for e in self.exercises)]

    def source(self, mission_id):
        """Repo-relative path of the module that defines a mission."""
        mod = sys.modules[self.missions[mission_id].setup.__module__]
        return Path(mod.__file__).resolve().relative_to(ROOT).as_posix()

    def checked_by(self, mission_id):
        return "checker" if self.missions[mission_id].checker is not None else "flag"

    def zone_missions(self, zone_id):
        return [e.mission for e in self.exercises
                if world.system(e.system).zone == zone_id]

    def covered_zones(self):
        return [z for z in self.zones if self.zone_missions(z.id)]

    def gaps(self):
        """One plain sentence per gap the registry itself shows."""
        out = []
        if self.empty_systems:
            out.append("no mission yet on " + _and([s.name for s in self.empty_systems], "or"))
        if self.unpaired:
            out.append("no fix mission yet to pair with the break "
                       + ("mission " if len(self.unpaired) == 1 else "missions ")
                       + _and([f"`{m}`" for m in self.unpaired]))
        if self.unused_levels:
            out.append("no mission yet at the "
                       + _and([f"`{lv}`" for lv in self.unused_levels], "or")
                       + f" level (the levels run from `{world.LEVELS[0]}` to "
                       f"`{world.LEVELS[-1]}`)")
        if self.unused_verbs:
            out.append("no mission yet with the verb "
                       + _and([f"`{v}`" for v in self.unused_verbs], "or"))
        return out


# ---------------------------------------------------------------------------
# README.md: the generated block on the first screen
# ---------------------------------------------------------------------------
def render_readme_block(f=None):
    f = f or Facts()
    covered = len(f.systems) - len(f.empty_systems)
    lines = [
        f"**Built today:** {_n(len(f.exercises), 'mission')} on {covered} of the "
        f"{_n(len(f.systems), 'system')}, in {len(f.covered_zones())} of the "
        f"{_n(len(f.zones), 'zone')}. Around them: "
        f"{_n(len(f.scenarios), 'incident scenario')}, "
        f"{_n(len(f.modules), 'learn module')}, {_n(len(DRILLS), 'drill')} and "
        f"{_n(len(TOOLS), 'tool tutor')}.",
        "",
    ]
    lines += _table(["Zone of the company", "Systems in it", "Missions built"],
                    [[z.name, " · ".join(s.name for s in world.systems_in(z.id)),
                      len(f.zone_missions(z.id)) or "none yet"] for z in f.zones])
    lines.append("")
    gaps = f.gaps()
    if gaps:
        lines.append("**Planned, not built.** The registry shows these gaps:")
        lines.append("")
        lines += [f"- {g};" for g in gaps[:-1]] + [f"- {gaps[-1]}."]
    else:
        lines.append("**Planned, not built.** The registry shows no gap: every system, break "
                     "mission and level has its mission.")
    return "\n".join(lines) + "\n"


def splice_readme(text, f=None):
    """Return README text with the generated block replaced."""
    if BEGIN not in text or END not in text:
        raise SystemExit("README.md has lost its generated-block markers; restore:\n"
                         f"  {BEGIN}\n  {END}")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return head + BEGIN + "\n\n" + render_readme_block(f) + "\n" + END + tail


# ---------------------------------------------------------------------------
# ATLAS.md: the whole file
# ---------------------------------------------------------------------------
def render_atlas(f=None):
    f = f or Facts()
    m = f.missions
    lessons = sum(len(mod["lessons"]) for mod in f.modules.values())
    questions = sum(len(mod["quiz"]) for mod in f.modules.values())
    briefings = sum(len(mod["tools"]) for mod in f.modules.values())
    covered = len(f.systems) - len(f.empty_systems)
    checkers = sum(1 for e in f.exercises if f.checked_by(e.mission) == "checker")

    out = [
        "# Atlas: what is built",
        "",
        STATUS_LINE,
        "",
        "This file is generated. `python3 _build_atlas.py` writes it from the world registry",
        "([`elitelab/world.py`](elitelab/world.py)), the mission modules",
        "([`elitelab/missions/`](elitelab/missions)), the learn modules ([`modules/`](modules))",
        "and the drill bank ([`drills/`](drills)). Don't edit it by hand: change the code, run",
        "the script and commit both. A test fails when this file and the code disagree.",
        "",
        "What a mission is, and what each registry field means, is in [MISSIONS.md](MISSIONS.md).",
        "",
        "## At a glance",
        "",
    ]
    out += _table(["What", "Count", "Read from"], [
        ["Missions", len(f.exercises),
         f"`EXERCISES` in the registry, one record per mission; {checkers} run your work "
         f"with a checker, {len(f.exercises) - checkers} take a flag"],
        ["Zones", len(f.zones),
         f"`ZONES` in the registry; {len(f.covered_zones())} carry at least one mission"],
        ["Systems", len(f.systems),
         f"`SYSTEMS` in the registry; {covered} carry at least one mission"],
        ["Incident scenarios", len(f.scenarios), "`SCENARIOS` in the registry"],
        ["Learn modules", len(f.modules),
         f"`modules/*.json`: {_n(lessons, 'lesson')}, {_n(questions, 'quiz question')}, "
         f"{_n(briefings, 'tool briefing')}"],
        ["Drills", len(DRILLS),
         f"`elite drill`: {', '.join(DRILLS)}; the command bank holds "
         f"{_n(len(f.bank), 'command')}"],
        ["Tool tutors", len(TOOLS), f"`elite run`: {', '.join(TOOLS)}"],
        ["Cheat sheets", len(CHEATS), f"`elite cheat`: {', '.join(CHEATS)}"],
        ["Tests", "run `pytest -q`", "the test run prints its own count; no doc repeats it"],
    ])

    out += ["", "## Planned, not built", "",
            "These are the gaps the registry shows: the systems, break missions and levels",
            "that no mission covers yet.", ""]
    gaps = f.gaps()
    out += [f"- {g[0].upper()}{g[1:]}." for g in gaps] or ["- None."]
    out += ["",
            "Plans that go beyond the registry, such as a live lab you host yourself, are in",
            "[VISION.md](VISION.md) and [SPEC.md](SPEC.md). Each section there is marked built,",
            "partly built or not built.",
            "",
            "## Missions, in campaign order",
            "",
            "The order of `EXERCISES` in the registry is the campaign order `elite path` walks.",
            "The skill column is the registry's own `skill` line. Checked by: **checker** means",
            "the mission runs the files you wrote; **flag** means you submit an answer and the",
            "mission compares it with its own solution.",
            ""]
    rows = []
    for i, e in enumerate(f.exercises, 1):
        s = world.system(e.system)
        rows.append([i, f"[`{e.mission}`]({f.source(e.mission)})", m[e.mission].title,
                     s.name, e.verb, e.level, f.checked_by(e.mission), e.skill])
    out += _table(["#", "Mission", "Title", "System", "Verb", "Level", "Checked by",
                   "Skill, in the registry's words"], rows)
    out += ["",
            f"Verbs, in registry order: {', '.join(f'`{v}`' for v in world.VERBS)}. "
            f"Levels, lowest rung first: {', '.join(f'`{lv}`' for lv in world.LEVELS)}.",
            "",
            "## Missions by zone and system",
            "",
            "The registry's view, which `elite map` prints with your progress: each zone is a",
            "trust world, each system sits in exactly one zone, and each mission lives on one",
            "system.",
            ""]
    rows = []
    for z in f.zones:
        for s in world.systems_in(z.id):
            on = [e.mission for e in world.exercises_on(s.id)]
            rows.append([z.name, z.trust, f"{s.name} (`{s.id}`)", s.addr or "",
                         _ids(on) or "none yet"])
    out += _table(["Zone", "Trust", "System", "Address", "Missions"], rows)

    out += ["",
            "## Missions by layer",
            "",
            "The mission modules' view, which `elite path` and `elite lab list` print: each",
            "mission module labels itself with a layer and a difficulty.",
            ""]
    by_layer = {}
    for e in f.exercises:                    # campaign order inside each layer
        mission = m[e.mission]
        by_layer.setdefault(mission.layer, []).append(f"`{e.mission}` ({mission.difficulty})")
    out += _table(["Layer", "Missions (difficulty)"],
                  [[layer, ", ".join(by_layer[layer])] for layer in sorted(by_layer)])

    out += ["",
            "## Break and fix pairs",
            "",
            f"A fix twin is its break mission's id plus `{FIX_SUFFIX}`. The invariant is the",
            "business function that must still work after the fix.",
            ""]
    rows = []
    for e in f.breaks:
        twin = f.twin.get(e.mission)
        inv = world.exercise(twin).invariant if twin else ""
        rows.append([f"`{e.mission}`", f"`{twin}`" if twin else "none yet", inv])
    out += _table(["Break", "Fix twin", "What must still work after the fix"], rows)

    out += ["",
            "## The loot chain",
            "",
            "Solving a mission grants loot. A mission that needs loot stays locked on the",
            "`elite engage` board until you hold any one of the items it lists.",
            ""]
    out += _table(["Mission", "Needs (any one)", "Grants"],
                  [[f"`{e.mission}`", _ids(e.requires), _ids(e.grants)]
                   for e in f.exercises if e.requires or e.grants])

    out += ["",
            "## Evidence the registry declares",
            "",
            "The `emits` field names the evidence a mission's activity leaves for a later",
            "detection mission. [MISSIONS.md](MISSIONS.md#6-what-the-mission-leaves-for-the-hunt)",
            "says how far that is wired today.",
            ""]
    out += _table(["Mission", "Verb", "Emits"],
                  [[f"`{e.mission}`", e.verb, _ids(e.emits)] for e in f.exercises if e.emits])

    out += ["",
            "## Incident scenarios",
            "",
            "`elite scenario` walks these. Each chains existing missions around one incident.",
            ""]
    out += _table(["Scenario", "The question it defends", "Steps, in order"],
                  [[f"`{sc.id}`: {sc.title}", sc.question, _ids(sc.steps)]
                   for sc in f.scenarios])

    out += ["",
            "## Learn modules",
            "",
            "`elite learn <module>` reads the lessons, `elite quiz <module>` asks the",
            "questions and `elite tools <module>` shows the tool briefings.",
            ""]
    out += _table(["Module", "Title", "Lessons", "Quiz questions", "Tool briefings"],
                  [[f"`{key}`", mod["title"], len(mod["lessons"]), len(mod["quiz"]),
                    len(mod["tools"])] for key, mod in f.modules.items()])

    platforms = Counter(c["platform"] for c in f.bank)
    out += ["",
            "## The command-drill bank",
            "",
            "`elite drill commands` asks you to type the real command. The bank, by platform:",
            ""]
    out += _table(["Platform", "Commands"],
                  [[p, n] for p, n in sorted(platforms.items(), key=lambda kv: (-kv[1], kv[0]))])
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------------
# write or check
# ---------------------------------------------------------------------------
def _read(path):
    return path.read_text(encoding="utf-8")


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    f = Facts()
    wanted = {ATLAS: render_atlas(f), README: splice_readme(_read(README), f)}
    stale = [p for p, text in wanted.items() if not p.exists() or _read(p) != text]
    if check:
        for p in stale:
            print(f"out of date: {p.name}  (run: python3 _build_atlas.py)")
        return 1 if stale else 0
    for p in stale:
        _write(p, wanted[p])
        print(f"wrote {p.name}")
    if not stale:
        print("ATLAS.md and the README block are already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
