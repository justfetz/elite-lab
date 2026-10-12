# Feature atlas — goal, status, and % to completion

Snapshot of where elite-lab is. Legend: ✅ done · 🟡 partial · ⬜ not started.

## The goal (north star)

A command-line cyber range where you **break and defend a small, real "company"
(Northwind AI — a domain + an app on SQL Server + a RAG product)**, run the real tools
against it, and a **local AI tutor grounded in your security books** explains every step
and **drills it into muscle memory**. Hands-on first.

## Pillars

| Feature | Status | ~% | Notes |
|---|---|---|---|
| **Learn** (lessons/quizzes/drills) | 🟡 | 70% | 12 modules; fundamentals solid, tool modules thin (1 lesson each) |
| **Lab** (build/break missions) | 🟡 | 40% | 9 missions, 4 of 6 layers; all offline, none live-target yet |
| **Ask** (book RAG tutor) | 🟡 | 70% | ask/summarize/lesson + markitdown work; needs an LLM backend + `elite ask` CLI |
| **Run** (tool-runner-tutor) | 🟡 | 25% | framework + safety gate done; only nmap tutor (of ~6) |

## Missions by layer / hit point

| Layer (hit point) | Status | ~% | What exists / what's missing |
|---|---|---|---|
| 1 The Wire | 🟡 | 60% | `wire-01` (log hunt), `build-01` scanner, `build-02` sniffer, nmap tutor |
| 2 The Door | 🟡 | 40% | `crack-01` (hash cracking); needs a live auth/brute mission |
| 3 The App | 🟡 | 55% | `app-01`+`app-01-fix` (SQLi break+fix), `web-vulns` module; needs IDOR/XSS missions |
| 4 The Host | 🟡 | 50% | `bin-01` crackme, `build-03` debugger, `build-04` fuzzer; needs a privesc mission |
| 5 The Domain | 🟡 | 55% | `domain-01` + `domain-01-fix`: path-to-DA analysis & remediation; `windows-ps` module. Live AD lab still planned |
| 6 The Hunt | ⬜ | 15% | `wire-01` touches detection; **no dedicated blue-team missions** |
| AI product (capstone) | 🟡 | 55% | `ai-01` + `ai-01-fix`: prompt-injection attack & defend on a RAG agent; live text-to-SQL agent still planned |

## Systems & infrastructure

| Feature | Status | ~% | Notes |
|---|---|---|---|
| Mission engine (goal/flag/checker/hints) | ✅ | 95% | solid; custom checkers + multi-mission modules supported |
| Build-missions (checker runs your code) | ✅ | 100% | scanner, sniffer, debugger, fuzzer all verify real implementations |
| Break+fix pairs (blue-team twin) | 🟡 | 15% | only `app-01-fix`; every attack mission should get one |
| Randomized per-user flags | ⬜ | 0% | flags are deterministic — memorizable/shareable |
| **Command-drill mode** (type the real command) | ✅ | 90% | `elite drill commands`: 22 commands, spaced repetition; add more over time |
| **`elite path`** (guided campaign up the layers) | ⬜ | 0% | not built |
| **Live lab provisioner** (Docker SQL Server + app, AD) | ⬜ | 0% | the realism jump — not built |
| Tool tutors beyond nmap (sqlmap/BloodHound/John/…) | ⬜ | 10% | framework ready; interpreters not written |
| `study_books.py` (local RAG) | ✅ | 85% | works; LLM backend optional; not yet wired as `elite ask` |
| Docs (SCENARIO/VISION/SPEC/CURRICULUM/ATLAS) | ✅ | 90% | the thinking is captured |
| On GitHub, MIT, README | ✅ | 100% | justfetz/elite-lab |

## Honest overall: ~55%

The **engine, the fundamentals, build/break, command drills, and the AI capstone are
real** — the hard parts (checkers that run and verify your actual code; a local book
tutor) work. What's still thin is **realism and the enterprise layers**: the live
Docker/SQL-Server/AD lab, a Domain (Active Directory) mission, the `elite path` campaign,
and tool tutors beyond nmap.

## Next three, in order

1. **Command-drill mode** — the muscle memory you keep asking for; bounded, high-impact.
2. **Live SQL Server lab + mission** — turns `app-01` into Northwind's real product; your turf.
3. **AD lab + a Domain mission** — the enterprise battleground (Layer 5), currently the biggest gap.
