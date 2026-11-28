# How a mission is designed

> **Doc status: current** · answers: *How is a mission designed, and how do I add one?* · [doc map](README.md#doc-map)

This is the recipe the existing missions follow, written down from the code. The worked
example is one break-and-fix pair, `mill-01` and `mill-01-fix`: forge an order release
across the link from HQ to the mill, then verify releases so that only a genuine one runs.
The example is described at the level the registry describes it. The mission's own files
teach the details when you start it.

A mission lives in two places, and a test fails if either exists without the other:

| Where | What it holds |
|-------|---------------|
| A `Mission` object in a module under [`elitelab/missions/`](elitelab/missions) | What the learner gets and how the work is checked: `setup`, the goal, the hints, the debrief, and either a `solution` or a `checker`. |
| One `Exercise` record in the world registry, [`elitelab/world.py`](elitelab/world.py) | Where the mission sits in the company and how it chains to the others. |

Every screen in the CLI and [ATLAS.md](ATLAS.md) is derived from those two places. No
screen keeps a mission list of its own.

## The recipe

1. [Write the registry record.](#1-the-registry-record)
2. [Name the seam and the invariant.](#2-the-seam-and-the-invariant)
3. [Hand over a real artifact and name a real tool.](#3-a-real-artifact-and-a-real-tool)
4. [Check the learner's work by running it.](#4-a-checker-that-runs-the-learners-work)
5. [Give it a fix twin that a look-alike patch cannot pass.](#5-the-fix-twin)
6. [Declare what it leaves for the hunt.](#6-what-the-mission-leaves-for-the-hunt)
7. [Prove with a test that it is solvable.](#7-the-test-that-proves-it-is-solvable)

## 1. The registry record

There is one record per mission, in `EXERCISES`. A record's position in that list is the
mission's place in the campaign. These are the two records for the pair:

<!-- quoted from: elitelab/world.py -->
```python
    Exercise("mill-01", "mill", "the HQ->mill release link -- forge a release and down PM3",
             "guided", "break", grants=["mill_control"], emits=["release.log"]),
    Exercise("mill-01-fix", "mill",
             "BLUE: verify releases (HMAC + freshness + no-replay + bounds)",
             "stateful", "fix", requires=["mill_control"], grants=["hardened_mill"],
             invariant="legitimate releases still reach PM3 and production continues",
             emits=["release.log"]),
```

| Field | What it means | In the example | What reads it |
|-------|---------------|----------------|---------------|
| `mission` | The id of the `Mission` object this record points at. | `mill-01` and `mill-01-fix` | `world.validate()`, which the test suite calls: every mission needs one record and every record one mission. |
| `system` | The system the mission lives on. Each system sits in one zone. | `mill`, the mill-floor agent, in the OT zone | `elite map` and the `elite engage` board group missions by system. |
| `skill` | The one skill the mission teaches, in a line. | The two quoted strings above | The `elite engage` board shows it as the target's description. ATLAS.md prints it. |
| `level` | The rung the mission sits on. One of `LEVELS`. | `guided` for the break. `stateful` for the fix: its checker sends the same release twice, so the agent has to remember what it accepted. | `elite engage` lists the missions at level `toolkit` as your toolkit. For the other levels it is a label. |
| `verb` | What you do to the system. One of `VERBS`. | `break`, then `fix` | `elite scenario` tags each step with it (RED, BLUE, HUNT, TOOL, RECON). |
| `requires` | Loot ids. The mission stays locked on the engage board until you hold any one of them. | The fix needs `mill_control`. | `elite engage`. `validate()` fails if nothing grants a required id. |
| `grants` | Loot ids that solving the mission gives you. | The break grants `mill_control`; the fix grants `hardened_mill`. | `elite engage` |
| `invariant` | The business function that must still work after a fix. | "legitimate releases still reach PM3 and production continues" | `elite scenario` prints it under the step as "keep working". The fix twin's checker is what enforces it (step 5). |
| `emits` | The evidence the mission's activity leaves behind for a detection mission. | `release.log` | Nothing in the CLI reads it yet (step 6). |
| `board` | Whether the mission shows on the `elite engage` board as a live network target. True unless you say otherwise. | True for both | `elite engage` |

## 2. The seam and the invariant

A mission starts from a **seam**: a place where one part of the company trusts another.
[SCENARIO.md](SCENARIO.md) lists the seams as hit points. For the pair it is the
order-release link. HQ sends a release, the mill-floor agent acts on it, and the agent as
shipped trusts any well-formed message. The break mission makes the learner prove that
trust can be abused.

The **invariant** is the other half: what the business must still be able to do once the
hole is closed. A fix that stops the attack by stopping production is not a fix. For the
pair the invariant is that legitimate releases still reach PM3. It goes in the fix twin's
record, and the fix twin's checker tests it.

## 3. A real artifact and a real tool

`setup(workdir)` writes the mission's files into the learner's work folder, and
`elite lab start <id>` runs it and lists what it wrote. For the pair
([`elitelab/missions/mill_01.py`](elitelab/missions/mill_01.py)) that is the mill agent as
a Python program the learner can read, run and edit, a sender script that prints a genuine
signed release, and `START_HERE.txt`. The break mission adds a sample release.

The rules the existing missions follow:

- **The artifact is the real kind of thing**: a log, a hash file, a compiled binary, a
  program to patch. It is never a question about one.
- **The learner uses the tool the job uses**, at their own prompt. The mission's `tools`
  list names it, and `elite lab start` turns every listed tool that has a cheat sheet into
  an `elite cheat` pointer.
- **`START_HERE.txt` states the task**, so the learner always has a next action
  ([PRINCIPLES.md](PRINCIPLES.md), rules 3 and 3a).
- **Setup and the check agree.** Anything random comes from a fixed seed in the module,
  so both arrive at the same answer without a separate answer file.
- **Hints go from a nudge to the answer**, one per `elite lab hint`.
- **The debrief is shown on success**: the lesson, then the defence.

## 4. A checker that runs the learner's work

`Mission.check()` in [`elitelab/missions/base.py`](elitelab/missions/base.py) does one of
two things:

- **Flag.** With no `checker`, it compares what the learner submits with what the
  mission's `solution(workdir)` returns. That proves the learner found the answer. It
  does not prove no shortcut exists.
- **Checker.** With a `checker(workdir, submitted)`, the submitted word is only the signal
  to start. The checker runs the learner's files and decides from what they do.

Both missions in the pair use a checker:

- `mill-01` passes when the release the learner saved is run through the shipped agent,
  the agent accepts it, and the agent reports the line going down.
- `mill-01-fix` passes when the learner's patched agent gives the right verdict on every
  release the checker sends it.

The rules a checker follows, as the pair's checkers do:

- **A crash is a fail.** The helper that runs the learner's program reports failure when it
  exits with an error or writes to stderr, so a traceback can never pass as a defence.
- **The checker starts from a clean state.** The fix checker forgets what an earlier
  attempt recorded before it sends anything. In the same spirit, `ai-01-fix` plants its
  poisoned document again, so deleting the document does not count as a fix.
- **The checker shows its work.** The fix checker prints each case and its verdict, so
  the learner sees which one failed.

## 5. The fix twin

A fix twin is a second mission on the same system:

- Its id is the break mission's id plus `-fix`, and it lives in the same module.
- Its record `requires` the loot the break `grants`, so the engage board unlocks it after
  the break.
- Its `setup` hands over the vulnerable program or data again, to be patched.
- Its checker tests both halves: the attack no longer works, **and** the invariant still
  holds. Every fix twin's checker does this.

The checker must also reject a patch that only looks right. `mill-01-fix` is the model.
Its checker builds each reject case so that exactly one defence can catch it:

<!-- quoted from: elitelab/missions/mill_01.py -->
```python
    # EACH reject case is otherwise VALID, FRESH, and SAFE - so it can only be caught
    # by the ONE defense it targets. A patch that skips a check will accept its case.
```

It sends a genuine release, which the agent must accept. It sends the same release again,
which the agent must reject as a replay. Then it sends one case per remaining defence:

<!-- quoted from: elitelab/missions/mill_01.py -->
```python
    for name, msg in [("forged (bad signature, else valid)", bad_sig),
                      ("future timestamp", future),
                      ("stale timestamp", stale),
                      ("unsafe setpoint", unsafe),
                      ("invalid grade", badgrade),
                      ("invalid quantity", badqty)]:
```

A test holds the checker to that. It submits a patch that checks some of the defences and
skips the others, and asserts that the checker fails it:

<!-- quoted from: tests/test_elite.py -->
```python
def test_mill_fix_rejects_defective_patch(tmp_path):
    """A plausible patch that checks bounds+age but NOT the signature/replay must FAIL -
    proving the checker catches an incomplete defense, not just the reference solution."""
    m = MISSIONS["mill-01-fix"]
    m.setup(tmp_path)
    (tmp_path / "mill_agent.py").write_text(_MILL_DEFECTIVE_AGENT)
    assert not m.check(tmp_path, "FIXED"), "checker PASSED a defective (no-HMAC) patch"
```

Today that negative test exists for `mill-01-fix` only. The other fix twins have the
positive test in step 7, and no test yet submits a look-alike patch to them. A new fix
twin should arrive with one.

## 6. What the mission leaves for the hunt

The `emits` field names the evidence a mission's activity would leave behind: for the
pair, `release.log`. The idea is the full loop from [SCENARIO.md](SCENARIO.md): break it,
find it in the logs, then fix it. `elite scenario` puts a detect step between the break
and the fix for that reason.

How far this is wired today:

- **`emits` is a declaration.** Nothing in the CLI reads the field.
- **Running a break mission records nothing.** Solving `mill-01` does not produce a
  `release.log`. Where a file with a declared name does exist, the mission's own `setup`
  generated it as the artifact to work on: `wire-01` hands you an `access.log`.
- **The detect missions bring their own evidence.** `hunt-01` generates its `auth.log`
  and `proc.log` from its seed. It does not read what an earlier mission did.
- So the detect step of a scenario practises the skill on a separate incident, not on the
  trail of the break you just ran.

When you add a mission, fill in `emits` anyway. It is the contract a later detection
mission will be built against, and [ATLAS.md](ATLAS.md#evidence-the-registry-declares)
prints it. Don't describe it to a learner as a log they can open.

## 7. The test that proves it is solvable

[`tests/test_elite.py`](tests/test_elite.py) runs every mission, so a mission that cannot
be solved cannot be merged:

- **Flag missions.** `test_flag_mission_solvable` sets the mission up, asks `solution()`
  for the answer, and checks that the answer passes and a wrong flag fails.
- **Checker missions.** `test_checker_mission_solvable` sets the mission up and asserts
  that the checker **fails** the untouched files. Then it applies the mission's entry in
  `SOLVERS` and asserts that the checker passes. A checker mission with no entry in
  `SOLVERS` fails the suite. For the pair the entries are `_solve_mill01` and
  `_solve_mill01fix`.
- **The registry.** `test_registry_matches_code` fails when a mission has no record, a
  record has no mission, or a record names a zone, system, level, verb or loot id that
  does not exist.
- **The docs.** The suite also fails when [ATLAS.md](ATLAS.md) is not what
  `_build_atlas.py` generates, or when a mission in the registry is missing from it.

## Adding a mission: the checklist

1. Write the module in `elitelab/missions/`. Expose `MISSION`, or `MISSIONS` for a pair.
   The package finds it by itself.
2. Add its `Exercise` record to `EXERCISES` in `elitelab/world.py`, at its place in the
   campaign. If it lives on a new system, add the `System` first.
3. If it has a checker, add its solver to `SOLVERS` in `tests/test_elite.py`. If it is a
   fix twin, add a test that submits a look-alike patch and expects a fail.
4. Run `pytest -q`.
5. Run `python3 _build_atlas.py`, and commit `ATLAS.md` and `README.md` with the code.
