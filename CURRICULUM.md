# What elite-lab is (and isn't)

**It is a Python-packaged, command-line _training ground_ for offensive and defensive
security.** One tool, `elite`, that you learn in, practice in, and ask questions in.
It's cross-platform (Linux, macOS, Windows) so the same tool teaches `grep` on the wire
and PowerShell on a domain.

**It is not** a Rust kernel, an OS, or a single app. Those are destinations you might
*build* — and "write tool X in C/Rust" can be a mission *inside* this training ground —
but the vehicle itself is a Python CLI, because the point is the security concepts and
fast iteration, not the implementation language.

## The three pillars

1. **Learn** — `elite learn / quiz / drill`
   The map. Short original lessons, shuffled quizzes, and endless self-generating
   drills (subnetting, ports) across the fundamentals.

2. **Lab** — `elite lab`
   The doing. HTB-style missions: a **goal**, a real **artifact** to work on, a **flag**
   to capture, an automatic **checker**, and unlockable **hints**. Early missions scaffold
   heavily; later ones just hand you a target and a flag. This is what makes it a training
   ground instead of a book.

3. **Ask** — `study_books.py` (local, AI-focused)
   The brain. A local RAG over books *you own* (PDF/TXT/MD): ask questions, get summaries,
   generate lessons — grounded in the text with page citations. Nothing leaves your
   machine, so any book you legally own is fair game for personal study.

## The spine: "how data moves"

Every topic and mission is placed on the path data actually travels, each layer carrying
both an offensive and a defensive skill:

| Layer | Where the data is | Learn module | Tools | Offense ↔ Defense |
|------|-------------------|--------------|-------|-------------------|
| 1 The Wire   | network / packets | `networking` | nmap, tcpdump, Wireshark | scan ↔ detect scans |
| 2 The Door   | services & auth   | `security`   | Hydra, John, Hashcat     | crack ↔ lockout + MFA |
| 3 The App    | web & data        | `security`   | Burp, ffuf, sqlmap       | inject ↔ parameterize |
| 4 The Host   | OS internals      | `windows`, `windows-ps`, `linux` | Ghidra, gdb, Sysinternals | exploit ↔ harden |
| 5 The Domain | Active Directory  | `windows-ps` | BloodHound, Impacket, GOAD | find the path ↔ cut it |
| 6 The Hunt   | logs & telemetry  | (woven in)   | Sysmon, SIEM, event logs | hide ↔ detect |

## What makes CLI learning effective

The mission loop is deliberately the HTB formula:

- a concrete **goal** you either hit or don't,
- a real **artifact** (a log, a hash file, later a pcap, a binary, a live target),
- you use the **real tool**, not a simulator,
- a **checker** gives instant pass/fail on a **flag**,
- **progressive hints** so you're never truly stuck,
- scaffolding that **fades** as you level up.

## Roadmap

- **More missions per layer**, including "bring-your-own-target" missions that orchestrate
  Docker/GOAD/Juice Shop on your machine and verify a known flag — the closest thing to HTB.
- **A PowerShell/AD mission**: enumerate a (lab) domain, find the permission leak, cut it.
- **Reverse-engineering missions**: ship a small crackme binary; find the key with Ghidra/gdb.
- **AI-security capstone**: a deliberately vulnerable RAG / text-to-SQL agent you attack
  (prompt injection, data leakage) and then harden — the payoff for a database background.
- **An `elite ask` built into the CLI** that uses the local book RAG as an always-available tutor.
