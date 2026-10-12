# elite-lab

A terminal cyber range that teaches offensive **and** defensive security by making you
*do* it — break a vulnerable app, then fix it; reverse a binary; trace a path to Domain
Admin; poison an AI agent and then defend it. It's a coach, not a video course: it assigns
real work on real files, checks your actual solution, and teaches the lesson behind it.

## ▶ Start here

```bash
git clone https://github.com/justfetz/elite-lab.git
cd elite-lab
python3 elite.py
```

That's it. Running `python3 elite.py` greets you and tells you exactly what to do next
(`elite doctor` to check your setup, then `elite engage` to begin). You need nothing but
**Python 3.8+** to start.

---

**The bet:** knowing *about* security is cheap and getting cheaper. Being able to *do* it —
and to explain why a system breaks and how to defend it — is what lasts. So every topic
ends in something you run at a prompt, not something you watch.

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

Each of those is a mission with a goal, a flag, and a checker that runs *your* work — so
you can't fake it, and you know the moment you've actually got it.

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

You don't have to follow it — `engage` always offers a valid next move — but this hits
every layer once and ends with the coach pulling back your weak spots.

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

| Command | What it does |
|---------|--------------|
| `elite engage` | Assess the company as one connected job; recon reveals the surface, loot unlocks deeper targets |
| `elite path` | A linear guided campaign through the missions, with your progress and a NEXT marker |
| `elite review` | The coach: what to redo now — weak spots, barely-cleared missions, stale mastery |
| `elite lab start/hint/submit <id>` | Set up a mission, unlock a hint, check your captured flag |
| `elite run <tool> ...` | Run a real tool (nmap, sqlmap, john, gobuster) and get a taught debrief |
| `elite ask "<question>"` | In-tool tutor — answers any term from the course (and your indexed books) |
| `elite learn / quiz <module>` | Read a module's lessons, or take a shuffled quiz (optional reinforcement) |
| `elite drill commands / subnet / ports` | Reps: type the real command / subnet / port; spaced repetition |
| `elite progress` / `elite reset` | Your scores / clear saved progress |

---

## The missions (the training ground)

Each mission gives you a goal, a real artifact, and a flag to capture; a checker verifies it
and hints unlock when you're stuck — the Hack The Box loop, offline and legal. Many come as
**break + fix pairs**, and the checker runs *your* code.

| Layer | Missions |
|-------|----------|
| 1 The Wire | `wire-01` hunt a brute-force · `build-01` write a port scanner · `build-02` write a packet parser |
| 2 The Door | `crack-01` crack password hashes with John/Hashcat |
| 3 The App | `app-01`/`-fix` SQL injection · `idor-01`/`-fix` broken access control |
| 4 The Host | `bin-01` reverse a crackme · `priv-01` Linux privesc · `build-03` a debugger's breakpoint engine · `build-04` a fuzzer |
| 5 The Domain | `domain-01`/`-fix` path to Domain Admin, then cut it |
| 6 The Hunt | `hunt-01` correlate logs to find the breach and its C2 |
| AI product | `ai-01`/`-fix` prompt-injection attack, then defend the RAG agent |

In **`engage`** mode you recon the company, then attack in any order — and the loot you
capture (a credential from the web app, local root on a workstation) unlocks the deeper
targets (the Domain Controller, a licensed binary). It's one connected assessment built
from the same missions.

The **build-your-own-tools** missions (`build-01`…`build-04`) hand you a skeleton with
`TODO`s; the checker runs your implementation against real targets (listeners it opens, a
crackme it compiles, a vulnerable C program it fuzzes). You learn the tool by building it.

---

## The learn modules (reference, not the main event)

Lessons are there to *support* the missions — reach for them when a mission exposes a gap,
or via `elite ask`.

**Fundamentals:** `threat-modeling` · `shell-basics` (grep & curl) · `networking` ·
`security` · `web-vulns` · `windows` · `windows-ps` · `linux`
**Tool briefings:** `tools-recon` · `tools-web` · `tools-ad` · `tools-pw` · `tools-re`

---

## Study from your own books (local, private)

`study_books.py` runs entirely on your machine over books *you own* (PDF/TXT/MD in a
`books/` folder). It finds the relevant pages locally, then — if you've configured an LLM —
turns them into an answer, summary, or lesson, grounded in the text and citing `[book p.N]`.

```bash
pip install pypdf scikit-learn markitdown
# put books you own in ./books/
python3 study_books.py index
python3 study_books.py ask "how does an access check work?"
```

LLM backend is auto-detected: Anthropic API (`ANTHROPIC_API_KEY`) or local Ollama
(`OLLAMA_MODEL=llama3.1`, free/offline). With neither, it shows you the passages to read.

**New to this?** See **[`LIBRARY.md`](LIBRARY.md)** — a full walkthrough: what books to put on
the shelf, how to run a **free AI model on your own laptop** (Ollama), how to index your
library, and how to ask it questions from the terminal.

> `books/` and its index are **gitignored and never committed.** This repo contains only
> original content — never book text. Index anything you own for personal study; only
> open-licensed material (OWASP, NIST, OSTEP, RFCs…) may go in a shared build.

---

## How it works

Content is **data**; the engine is **code**. Each module is a JSON file in `modules/`;
each mission is a small Python module in `elitelab/missions/` with a `setup()` and either a
flag `solution()` or a `checker()` that runs your work.

```
elite.py                 # entry point
elitelab/
  cli.py                 # commands
  engage.py  path/review # the connected job, campaign, and coach
  ask.py                 # the in-tool tutor
  runner.py              # `elite run` tool tutors
  missions/              # one module per mission (setup + checker/solution)
  content.py ui.py ...   # module loading + lesson/quiz/drill UI
modules/   *.json        # learn content (data)
tests/                   # pytest: proves every mission is solvable
study_books.py           # local RAG over your own books
```

Extend it by dropping a JSON file in `modules/` (a new lesson/quiz) or a mission module in
`elitelab/missions/` — the test suite will tell you if a mission isn't solvable.

See `CURRICULUM.md` (the layer map), `SCENARIO.md` (the company story), `PRINCIPLES.md`
(the design rules), `LIBRARY.md` (set up your own book shelf + a free local AI tutor),
`SPEC.md` (the build brief), and `ATLAS.md` (live status / what's next).

---

## What's next (honest)

Done: all 7 layers have missions, break/fix pairs, build-your-own-tools, the AI capstone,
spaced repetition, the review coach, packaging, and tests. Still thin:

- **Realism** — an optional Docker/AD live lab for when you want real targets (kept optional
  on purpose; the core stays zero-setup).
- **Depth** — more missions per layer (a second web bug like XSS, a Door password-spray).
- **More tool tutors** in `elite run` (BloodHound, gdb, Ghidra workflows).

See `ATLAS.md` for the current completion map.

---

## License

MIT (see `LICENSE`). Course text is original and free to use for learning. Not affiliated
with any tool, vendor, or book mentioned.
