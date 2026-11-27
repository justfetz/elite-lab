# elite-lab

> **Doc status: current** · answers: *What is elite-lab, what is built, and where do I start?* · [doc map](#doc-map)

**What it is.** elite-lab is a terminal training range for security skills, written in
Python. It gives you a goal and real files, you do the work at your own prompt with real
tools, and it checks the result: a flag you captured, or your own code run by a checker.

**The goal.** That you can *do* security, not only describe it: break a system, fix it
without stopping the business, and find the attack in the logs.

**The company you defend.** You are the security team at **Lakefront Paper & Container
Co.**, a fictional paper maker with a mill on the Chicago River. It has a public order
portal, an AI order agent, an office network and a plant floor that has to keep producing.
Every mission is set there. [SCENARIO.md](SCENARIO.md) tells its story.

**What is built, and what is planned.** `_build_atlas.py` writes this block from the code,
and a test fails when it falls behind:

<!-- BEGIN GENERATED BLOCK: built. _build_atlas.py writes this from the registry; change the code and rerun it, don't edit here. -->

**Built today:** 20 missions on 8 of the 11 systems, in 4 of the 5 zones. Around them: 2 incident scenarios, 15 learn modules, 3 drills and 5 tool tutors.

| Zone of the company | Systems in it | Missions built |
|---|---|---|
| IT / Business (public) | Customer Portal · Millie, the AI order agent | 6 |
| IT / Corporate (internal) | Domain Controller dc01 · Workstation ws01 · SOC / log pipeline · The wire | 11 |
| DMZ / Conduit | Order-release staging | none yet |
| OT / Plant floor | Mill-floor agent · PM3 paper machine · LoadMaster optimizer | 2 |
| People | Corporate email | 1 |

**Planned, not built.** The registry shows these gaps:

- no mission yet on Order-release staging, PM3 paper machine or LoadMaster optimizer;
- no fix mission yet to pair with the break missions `crack-01`, `bin-01` and `priv-01`;
- no mission yet at the `recovery` level (the levels run from `intro` to `recovery`).

<!-- END GENERATED BLOCK: built -->

[ATLAS.md](ATLAS.md) lists every mission and what it teaches. Larger plans are in
[VISION.md](VISION.md) and [SPEC.md](SPEC.md), with each section marked built or not built.
The largest is a live lab you host yourself, which is [partly built](live-lab/README.md).

**How to start.** You need only Python 3.8 or newer.

```bash
git clone https://github.com/justfetz/elite-lab.git
cd elite-lab
python3 elite.py
```

The last command greets you and names your next one. [Quick start](#quick-start) lists the
commands that follow, and `elite doctor` tells you if a mission wants an extra tool.

---

## Doc map

Each doc has one job. The table gives the question it answers and its status, and every
doc opens with the same line you see at the top of this page.

| Doc | The question it answers | Status |
|-----|-------------------------|--------|
| [README.md](README.md) | What is elite-lab, what is built, and where do I start? | current |
| [SCENARIO.md](SCENARIO.md) | Who is the company I defend, and where can it be broken? | current |
| [ATLAS.md](ATLAS.md) | Which missions exist, where does each one live, and what is not built yet? | current |
| [MISSIONS.md](MISSIONS.md) | How is a mission designed, and how do I add one? | current |
| [CURRICULUM.md](CURRICULUM.md) | How is the learning organised? | current |
| [PRINCIPLES.md](PRINCIPLES.md) | Which design decisions are settled? | current |
| [VISION.md](VISION.md) | Where is this going in the long run? | plan |
| [SPEC.md](SPEC.md) | What gets built next, and in what order? | plan |
| [LIBRARY.md](LIBRARY.md) | How do I set up the local AI tutor over my own books? | reference |
| [TOOLS.md](TOOLS.md) | Which libraries and tools does the project use, and why those? | reference |
| [live-lab/README.md](live-lab/README.md) | What is the optional live lab, and how much of it exists? | current |
| [live-lab/orderdesk/README.md](live-lab/orderdesk/README.md) | How do I run the OrderDesk portal on my own machine? | reference |
| [live-lab/loadmaster/README.md](live-lab/loadmaster/README.md) | What does LoadMaster solve, and how do I run it? | reference |

What the three statuses mean:

- **current** describes the project as it stands today: the code, and the fiction the
  code is built on. Where one disagrees with the code, the doc is wrong.
  [ATLAS.md](ATLAS.md) is generated from the code, and a test fails when it falls behind.
- **plan** describes what we intend to build. Each section opens by saying whether it is
  built, partly built or not built.
- **reference** is background and how-to material: setup guides and tool lists. Read it
  to use something, not to learn what state the project is in.

---

## What you'll be able to do

After working through it, you can:

- **Read a network and an attack the way a pro does** — scan with nmap (and *build* your
  own scanner), read packets byte by byte, and hunt an intrusion in logs.
- **Find and fix real web bugs** — SQL injection and broken access control (IDOR), by
  exploiting them *and* writing the patch that stops them.
- **Work below the surface** — reverse a compiled binary, build a debugger's breakpoint
  engine and a crash-finding fuzzer, and escalate privileges on a Linux host.
- **Attack and defend an enterprise** — walk nested AD groups and ACLs to Domain Admin,
  then cut the path.
- **Secure the new attack surface** — break an AI/RAG agent with prompt injection and
  harden it, the skill almost nobody has yet.
- **Defend the plant floor** — forge an order release across the link from HQ to the mill,
  then verify releases so that only a genuine one runs.
- **Catch the human way in** — triage a phishing email and pull out the real link.

Each of those is a mission with a goal and a checker. The **fix** and **build** missions run
*your actual code* against real cases — open sockets, compile and fuzz a C target, send a
forged *and* a genuine release at your patched agent — and several show you each probe and
verdict, so you see exactly what holds. (The missions that take a flag use a fixed one,
for zero-setup personal practice: a flag proves you got the answer, not that no shortcut
exists.)

---

## Quick start

No dependencies for the core — just **Python 3.8+**.

```bash
git clone https://github.com/justfetz/elite-lab.git
cd elite-lab
python3 elite.py doctor                 # check your setup — what's installed, what (if anything) to get
python3 elite.py engage                 # assess the fake company as one connected job
python3 elite.py lab start app-01       # or jump into a single mission (break SQLi, then fix it)
python3 elite.py ask "what is idor"     # hit a term you don't know? ask the app
```

**You need almost nothing to start.** The core runs on Python 3.8+ alone, and most missions
are playable immediately. A handful want an external tool (a C compiler for the reversing/
fuzzing missions; John/Hashcat for cracking) — `elite doctor` tells you which, with the exact
install command, so you only get what you'll actually use.

**bash or PowerShell?** The tool itself (`python3 elite.py`) runs the same on any OS. The
hands-on *mission* commands are bash/Unix (grep, nmap, john, sudo…), so use a Unix shell:
macOS Terminal, any Linux terminal, or **WSL on Windows** (`wsl --install` once). PowerShell
has its own module (`windows-ps`) for the Windows/AD material. New to the terminal? Start
with **`python3 elite.py learn shell-basics`** — it covers the shell, paths, flags, pipes,
grep, and curl from zero.

Prefer a real command everywhere? Install it (optional):

```bash
pip install -e .            # now `elite ...` works from any directory
pip install -e ".[books]"   # also enables study_books.py (local tutor over your own PDFs)
pytest -q                   # run the suite — proves every mission is solvable
```

(Below, `elite` is shorthand for `python3 elite.py`.)

---

## Your first week (a suggested test run)

Start every session the same way: **`elite review`** (it tells you what to redo) →
**`elite engage`** (pick a target). Then, roughly:

| Day | Focus | Do |
|-----|-------|----|
| 1 | The loop + the wire | `elite engage recon`; clear `wire-01` (hunt a brute-force) and `build-01` (write a scanner) |
| 2 | Web | `app-01` + `app-01-fix` (SQLi break→fix), `idor-01` + `idor-01-fix`; skim `elite learn web-vulns` |
| 3 | Credentials + reps | `crack-01`; then `elite drill commands` and `elite drill subnet` for muscle memory |
| 4 | Below the surface | `bin-01` (reverse a crackme), `build-03` (debugger), `build-04` (fuzzer), `priv-01` (Linux privesc) |
| 5 | The domain | `elite learn windows-ps`, then `domain-01` + `domain-01-fix` (path to DA, then cut it) |
| 6 | The AI product | `elite learn threat-modeling`, then `ai-01` + `ai-01-fix` (prompt injection, then defend) |
| 7 | Consolidate | `elite review` — redo anything shaky or stale; finish clearing `engage` |

You don't have to follow it — `engage` always offers a valid next move. This week is a
sample, not the whole course, and it ends with the coach pulling back your weak spots.
`elite path` is the full campaign, in order.

---

## ⚖️ Ethics & the law

Every mission here is **self-contained and offline** — nothing touches a system you don't
own. When you graduate to real tools and labs, the rule is simple: only test machines **you
own** or have **explicit written permission** to test. Unauthorized scanning or access is a
crime (US Computer Fraud and Abuse Act, UK Computer Misuse Act); intent doesn't matter,
permission does. `elite run` enforces this — it refuses active tools aimed outside your lab.

Safe places to graduate to: a VM lab you control; deliberately-vulnerable Docker apps
([OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), [DVWA](https://github.com/digininja/DVWA));
[GOAD](https://github.com/Orange-Cyberdefense/GOAD) for Active Directory;
and CTF platforms with permission built in ([picoCTF](https://picoctf.org/),
[TryHackMe](https://tryhackme.com/), [Hack The Box](https://www.hackthebox.com/)).

The course teaches attack **and** defense on purpose — you learn to protect systems by
understanding exactly how they fall.

---

## The commands

`python3 elite.py -h` prints the full list. These are the ones you will use:

| Command | What it does |
|---------|--------------|
| `elite status` (or `elite help`) | Home screen: your progress, your next move and what is available |
| `elite doctor` | Check your setup: what is installed and what, if anything, to get |
| `elite map` | The company: its zones, its systems and the missions on each |
| `elite engage` | Assess the company as one connected job; recon reveals the surface, loot unlocks deeper targets |
| `elite path` | A linear guided campaign through the missions, with your progress and a NEXT marker |
| `elite scenario [id]` | Incident chains: break, detect and fix one incident end to end |
| `elite review` | The coach: what to redo now — weak spots, barely-cleared missions, stale mastery |
| `elite lab list` / `elite lab status` | The missions, and your progress on each |
| `elite lab start/hint/restart <id>` | Set up a mission, unlock a hint, or start it again clean |
| `elite lab submit <id> <flag>` | Check your work: the flag you captured, or the word that starts the checker |
| `elite run <tool> ...` | Run a real tool (nmap, sqlmap, john, gobuster) and get a taught debrief |
| `elite ask "<question>"` | In-tool tutor — answers any term from the course (and points at your indexed books) |
| `elite study ask/summarize/lesson "<topic>"` | Cited answers from your *own* books via a free local model — see [LIBRARY.md](LIBRARY.md) |
| `elite list` | Every learn module, with your best quiz score |
| `elite learn / quiz <module>` | Read a module's lessons, or take a shuffled quiz (optional reinforcement) |
| `elite tools [module]` | Every tool the course briefs you on, or one module's full briefings |
| `elite cheat [tool]` | Instant command reference for a tool, such as grep, curl or nmap |
| `elite drill commands / subnet / ports` | Reps: type the real command / subnet / port; spaced repetition |
| `elite catalog` | Everything available to you: modules, missions, drills, books and docs |
| `elite progress` / `elite reset` | Your scores / clear saved progress |

---

## The missions (the training ground)

Each mission gives you a goal, a real artifact, and either a flag to capture or a checker
that runs your work; hints unlock when you're stuck — the Hack The Box loop, offline and
legal. Many break missions come with a **fix twin**: you break the thing, then you patch
it, and the checker runs *your* patch.

The full list of missions lives in one place, [ATLAS.md](ATLAS.md), which is generated
from the code: every mission by campaign order, by zone and by layer.
[MISSIONS.md](MISSIONS.md) explains how a mission is designed and how to add one.

In **`engage`** mode you recon the company, then attack in any order — and the loot you
capture (a credential from the web app, local root on a workstation) unlocks the deeper
targets (the Domain Controller, a licensed binary). It's one connected assessment built
from the same missions.

The **build-your-own-tools** missions hand you a skeleton with `TODO`s; the checker runs
your implementation against real cases (listeners it opens on localhost, packets it
builds, a C program it compiles for your fuzzer). You learn the tool by building it.

---

## The learn modules (reference, not the main event)

Lessons are there to *support* the missions — reach for them when a mission exposes a gap,
or via `elite ask`. `elite list` shows every module, and [ATLAS.md](ATLAS.md) has the
generated table of modules, lessons, quizzes and tool briefings.

---

## Study from your own books (local, private)

`elite study` answers questions from books *you own*, and every answer cites its page.
With a free local model (Ollama) everything stays on your machine: no account and no
bill. If you set `ANTHROPIC_API_KEY` instead, it uses that API, and the excerpts it sends
leave your machine. With neither, it shows you the passages to read.

```bash
elite study ask "how does an access check work?"
```

[LIBRARY.md](LIBRARY.md) is the one guide to setting it up: what to put on the shelf, how
to run a local model, how to index your books and how to ask. [TOOLS.md](TOOLS.md) explains
the libraries behind it.

> `books/` and its index are **gitignored and never committed.** This repo contains only
> original content — never book text. Index anything you own for personal study; only
> open-licensed material (OWASP, NIST, OSTEP, RFCs…) may go in a shared build.

---

## How it works

Content is **data**; the engine is **code**. Each module is a JSON file in `modules/`;
each mission is a small Python module in `elitelab/missions/` with a `setup()` and either a
flag `solution()` or a `checker()` that runs your work. One record per mission in the world
registry places it in the company; the map, the campaign, the engagement board and the
scenarios are all derived from that registry.

```
elite.py                 # entry point
elitelab/
  cli.py                 # commands
  world.py               # the registry: zones, systems, one record per mission, scenarios
  missions/              # one module per mission (setup + checker/solution)
  engage.py  map.py  scenario.py  lab.py   # views derived from the registry
  review.py              # the coach
  ask.py                 # the in-tool tutor
  runner.py              # `elite run` tool tutors
  content.py ui.py ...   # module loading + lesson/quiz/drill UI
modules/   *.json        # learn content (data); the _build_*.py scripts generate these
drills/                  # the command-drill bank
tests/                   # pytest: every mission is solvable; the docs match the code
_build_atlas.py          # writes ATLAS.md and the block at the top of this page
study_books.py           # local RAG over your own books
live-lab/                # the optional running version of the company
```

Extend it by adding a JSON file to `modules/` (a new lesson/quiz) or a mission module to
`elitelab/missions/` plus its registry record — the test suite will tell you if a mission
isn't solvable, isn't registered, or isn't in the atlas. [MISSIONS.md](MISSIONS.md) walks
through it.

---

## License

MIT (see `LICENSE`). Course text is original and free to use for learning. Not affiliated
with any tool, vendor, or book mentioned.
