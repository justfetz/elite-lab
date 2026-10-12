# Feature atlas — goal, status, and % to completion

Snapshot of where elite-lab is. Legend: ✅ done · 🟡 partial · ⬜ not started.

## The goal (north star)

A command-line cyber range where you **break and defend a small, real "company"
(Vantaris AI — a domain + an app on SQL Server + a RAG product)**, run the real tools
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
| 3 The App | 🟡 | 70% | `app-01`+`app-01-fix` (SQLi), `idor-01`+`idor-01-fix` (access control), `web-vulns`; XSS/SSRF still to add |
| 4 The Host | 🟡 | 65% | `bin-01` crackme, `priv-01` Linux privesc, `build-03` debugger, `build-04` fuzzer |
| 5 The Domain | 🟡 | 55% | `domain-01` + `domain-01-fix`: path-to-DA analysis & remediation; `windows-ps` module. Live AD lab still planned |
| 6 The Hunt | 🟡 | 55% | `hunt-01`: correlate auth + process logs to find the breach and the C2; more detections to add |
| AI product (capstone) | 🟡 | 55% | `ai-01` + `ai-01-fix`: prompt-injection attack & defend on a RAG agent; live text-to-SQL agent still planned |

## Systems & infrastructure

| Feature | Status | ~% | Notes |
|---|---|---|---|
| Mission engine (goal/flag/checker/hints) | ✅ | 95% | solid; custom checkers + multi-mission modules supported |
| Build-missions (checker runs your code) | ✅ | 100% | scanner, sniffer, debugger, fuzzer all verify real implementations |
| Break+fix pairs (blue-team twin) | 🟡 | 50% | `app-01-fix`, `idor-01-fix`, `ai-01-fix`, `domain-01-fix`; a few attack missions still need twins |
| Spaced repetition + review coach | ✅ | 85% | `elite review` ranks weak/stale/unfinished; drills resurface overdue items |
| Randomized per-user flags | ⬜ | 0% | flags are deterministic — memorizable/shareable |
| **Command-drill mode** (type the real command) | ✅ | 90% | `elite drill commands`: 22 commands, spaced repetition; add more over time |
| **`elite path`** (guided campaign up the layers) | ✅ | 90% | `elite path`: ordered campaign by layer with your progress + NEXT |
| **`elite engage`** (connected company, open sandbox + loot) | ✅ | 85% | recon reveals the surface; loot chains to unlock deeper targets, derived from mission progress |
| **Live lab provisioner** (Docker SQL Server + app, AD) | ⬜ | 0% | the realism jump — not built |
| Tool tutors beyond nmap (sqlmap/BloodHound/John/…) | ⬜ | 10% | framework ready; interpreters not written |
| `study_books.py` + `elite ask` | ✅ | 90% | `elite ask` answers from course lessons instantly; study_books adds book-grounded answers |
| Docs (SCENARIO/VISION/SPEC/CURRICULUM/ATLAS) | ✅ | 90% | the thinking is captured |
| On GitHub, MIT, README | ✅ | 100% | justfetz/elite-lab |
| Packaging + test suite | ✅ | 90% | `pip install -e .` gives the `elite` command; 25 pytest checks prove every mission solvable + CLI runs |

## Honest overall: ~74%

The **engine, the fundamentals, build/break, command drills, and missions on every
layer (Wire → Door → App → Host → Domain → AI) are real** — the hard parts (checkers
that run and verify your actual code; a local book tutor) work. What's still thin is
**realism**: the live Docker/SQL-Server/AD lab, dedicated Hunt (blue-team) missions, and
tool tutors beyond nmap.

## Next three, in order

1. **Live SQL Server lab + mission** — turns `app-01` into Vantaris's real product (Docker
   SQL Server Developer + the vulnerable app); the realism jump, and your turf.
2. **`elite path`** — a guided campaign that sequences the missions up the layers, so there's
   one clear route from zero to competent.
3. **A Hunt (blue-team) mission + more tool tutors** — detect an attack in logs; add sqlmap/
   BloodHound/John tutors to `elite run`.
