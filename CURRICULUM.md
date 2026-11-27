# The curriculum: how the learning is organised

> **Doc status: current** · answers: *How is the learning organised?* · [doc map](README.md#doc-map)

What elite-lab is and how to start are in [README.md](README.md). This page covers how the
material is arranged: the three pillars, the layer spine, and the loop that makes it stick.

One thing it is **not**: a Rust kernel, an OS, or a single app. Those are destinations you
might *build* — and "write tool X in C/Rust" can be a mission *inside* this training ground —
but the vehicle itself is a Python CLI, because the point is the security concepts and
fast iteration, not the implementation language. It's cross-platform (Linux, macOS,
Windows) so the same tool teaches `grep` on the wire and PowerShell on a domain.

## The three pillars

1. **Learn** — `elite learn / quiz / drill`
   The map. Short original lessons, shuffled quizzes, and endless self-generating
   drills (subnetting, ports, real commands) across the fundamentals.

2. **Lab** — `elite lab`
   The doing. HTB-style missions: a **goal**, a real **artifact** to work on, a **flag**
   to capture or a **checker** that runs your work, and unlockable **hints**. This is what
   makes it a training ground instead of a book. [MISSIONS.md](MISSIONS.md) explains how a
   mission is built.

3. **Ask** — `elite ask` and `elite study`
   The brain. `elite ask` answers from the course's own lessons. `elite study` is a local
   RAG over books *you own* (PDF/TXT/MD): ask questions, get summaries, generate lessons —
   grounded in the text with page citations. The index stays on your machine, and with a
   local model so does everything else, so any book you legally own is fair game for
   personal study. [LIBRARY.md](LIBRARY.md) sets it up.

## The spine: "how data moves"

Every topic and mission is placed on the path data actually travels, each layer carrying
both an offensive and a defensive skill:

| Layer | Where the data is | Learn modules | Tools | Offense ↔ Defense |
|------|-------------------|---------------|-------|-------------------|
| 1 The Wire   | network / packets | `networking`, `tools-recon` | nmap, tcpdump, Wireshark | scan ↔ detect scans |
| 2 The Door   | services & auth   | `security`, `tools-pw`      | Hydra, John, Hashcat     | crack ↔ lockout + MFA |
| 3 The App    | web & data        | `web-vulns`, `tools-web`    | Burp, ffuf, sqlmap       | inject ↔ parameterize |
| 4 The Host   | OS internals      | `windows`, `linux`, `tools-re` | Ghidra, gdb, Sysinternals | exploit ↔ harden |
| 5 The Domain | Active Directory  | `windows-ps`, `tools-ad`    | BloodHound, Impacket, GOAD | find the path ↔ cut it |
| 6 The Hunt   | logs & telemetry  | (woven in)                  | Sysmon, SIEM, event logs | hide ↔ detect |

Three more labels cover surfaces those six do not:

- **7 The Mill (OT)** — the order-release link between HQ and the plant floor: forge a
  release ↔ verify it. Learn module: `threat-modeling`.
- **AI product** — the RAG agent: inject through a document ↔ treat retrieved text as data.
  Learn module: `threat-modeling`.
- **People** — email: phish ↔ triage. Learn module: `people`.

New to all of it? `basics` defines the words and `shell-basics` teaches the terminal.

## Layers and zones: two addresses for every mission

- Its **layer** says how deep in the stack the skill sits. The mission module carries it,
  and `elite path` and `elite lab list` group by it.
- Its **zone** says where in the company its system sits. The world registry carries it.
  `elite map` groups by zone, and the `elite engage` board groups by the systems inside
  the zones. [SCENARIO.md](SCENARIO.md) tells the story behind them.

[ATLAS.md](ATLAS.md) is generated from the code and lists every mission both ways. Look
there, not here, for which layers and missions exist today.

## What makes CLI learning effective

The mission loop is deliberately the HTB formula:

- a concrete **goal** you either hit or don't,
- a real **artifact** (a log, a hash file, a binary, a program to patch),
- you use the **real tool**, not a simulator,
- a **checker** gives instant pass/fail,
- **progressive hints** so you're never truly stuck,
- scaffolding that **fades** as you level up.

Then reps make it stick: the command drill resurfaces what you miss, and `elite review`
tells you what to redo. [PRINCIPLES.md](PRINCIPLES.md) holds the design rules behind this.

## What comes next

Plans are not kept on this page. [VISION.md](VISION.md) is the long-run picture and
[SPEC.md](SPEC.md) is the build order; each section there is marked built or not built.
