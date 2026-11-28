# The vision: elite-lab as a cyber range you command

> **Doc status: plan** · answers: *Where is this going in the long run?* · [doc map](README.md#doc-map)

This page is a plan, not a description of the code. Every section opens with **Built**,
**Partly built** or **Not built** and says what exists today. For what exists, mission by
mission, read [ATLAS.md](ATLAS.md), which is generated from the code.

The end state: `elite` is the console for a small, deliberately flawed "company" you
run on your own hardware — a domain, a few hosts, and an app with a real database —
and the tool walks you through attacking and defending every layer, teaching the
lesson at each step and drilling it until it's muscle memory.

The company in this plan now has a name and a story: Lakefront Paper & Container Co., in
[SCENARIO.md](SCENARIO.md).

---

## 1. The "company" you practice on (the lab)

**Partly built.** The company exists as a story and as offline missions. The hosted lab
described here is the part still to build; [live-lab/README.md](live-lab/README.md) tracks it.

You build a sandbox that looks like a real org. Everything here is free and legal
because you own all of it.

### Active Directory (the domain)

**Partly built.** The first option below is built: `domain-01` and `domain-01-fix` work on
an exported AD graph, with no VMs
([`elitelab/missions/domain_01.py`](elitelab/missions/domain_01.py)). The other options are
not built: nothing in the repo stands up a domain controller.

Three ways, lightest to most realistic:

- **Canned data (no VMs).** Ship/point at sample BloodHound datasets and a seeded AD
  graph. You learn the *analysis* (find the path to Domain Admin) with zero setup.
  Great for offline missions and for learning BloodHound before you can host a DC.
- **Minimal home lab.** One Windows Server **evaluation** VM (free, 180 days) promoted
  to a Domain Controller with `Install-ADDSForest`, plus one Windows client joined to
  the domain. A PowerShell seed script creates users, groups, and *deliberate
  misconfigurations* (kerberoastable service accounts, a user with DCSync rights, an
  over-nested admin group). This is your personal GOAD-lite.
- **GOAD** ("Game of Active Directory"). An open project that builds a whole vulnerable
  multi-DC forest with Vagrant/Ansible. The heavyweight, most realistic option.
- **Samba AD DC on Linux.** A lightweight domain controller without Windows licensing —
  good for Kerberos/LDAP fundamentals when you don't want VMs.

### The app + SQL Server (the data tier)

**Partly built.** A database schema and a vulnerable web app exist, and they are not yet
wired to each other or to a domain, so the kill chain below does not run end to end on
live targets. [live-lab/README.md](live-lab/README.md) is the one place that says which
parts exist.

Stand up a small 3-tier app so the database, the web layer, and the domain all meet in
one target:

```
browser → web app → SQL Server Developer edition  (service runs as a DOMAIN account)
```

- **SQL Server Developer** is free and full-featured. Run it in Docker
  (`mcr.microsoft.com/mssql/server`) or on a Windows box in the lab.
- Seed it with realistic data and **deliberate flaws**: an over-privileged service
  login (`db_owner`/`sysadmin`), `xp_cmdshell` left enabled, a web query built by string
  concatenation (SQL injection), row-level security the app can be tricked into bypassing.
- Join the app's service account to the domain, so a SQL/app compromise becomes a
  *domain* foothold. That's the realistic kill chain: **web bug → database → stored
  credential → domain**. Your ten years of SQL Server is the edge here — you already
  know ownership chaining, `EXECUTE AS`, linked servers, and where creds hide.

This one app exercises four layers at once: App (SQLi), Host (the SQL service account),
Domain (lateral movement), and Hunt (SQL Server Audit + Windows event logs).

---

## 2. How the tool drives it

**Partly built.** Of the three mission flavors, the first is built, the second is not, and
the third is partly built. The commands around the missions are built.

`elite` gains three mission *flavors*, all sharing the same goal/flag/checker/hint loop:

1. **Self-contained**: generated artifact + flag. Always works, no lab.
   *Built: every mission in [ATLAS.md](ATLAS.md) is this flavor.*
2. **Live-target**: `elite lab start ad-01` checks the lab is reachable, gives a goal
   ("get Domain Admin and read `\\dc01\flag.txt`"), you use the *real* tools, capture the
   flag, submit, checker verifies. This is Hack The Box, but it's *your* box.
   *Not built: no mission checks a running lab.*
3. **Blue-team twin**: every attack mission has a defense counterpart. After you break
   in, `elite lab start ad-01-defend` hands you the logs and asks you to detect the
   attack and cut the path — and checks your remediation.
   *Partly built: fix twins exist as `<id>-fix` and their checkers run your remediation.
   [ATLAS.md](ATLAS.md#break-and-fix-pairs) lists which break missions have one. Detecting
   the attack in the logs is a separate mission, not part of the twin.*

Around the missions:

- `elite run <tool> …` — run the real tool, get a taught debrief.
  *Built for the tutors [ATLAS.md](ATLAS.md#at-a-glance) lists. BloodHound and Impacket
  tutors are not built.*
- `elite ask "…"` — the tutor, always a command away mid-mission.
  *Built: it answers from the course's lessons and points at your indexed books;
  `elite study ask` writes the book-grounded answer.*
- `elite path` — a guided campaign that walks the "how data moves" layers in order.
  *Built: it walks the registry's campaign order.*

---

## 3. How tools actually get learned (the muscle-memory engine)

**Partly built.** Stages 1 to 3 exist as separate commands. Command drills are built and
spaced repetition is partly built. Stages 4 and 5 are not built, and the tool does not
track a stage per skill: it records quiz scores, mission state and drill history
([`elitelab/progress.py`](elitelab/progress.py)).

Reading doesn't stick; reps do. Each tool/skill moves through five stages, and the tool
tracks where you are on each:

1. **Concept** — a short lesson (`elite learn`) so you know *why*. *Built.*
2. **Demo** — `elite run` on a sample, so you see the shape of a real result. *Built: when
   the tool is not installed, `elite run` teaches from a bundled sample.*
3. **Guided mission** — do it for real with hints available. *Built.*
4. **Unguided mission** — same class of task, no hints, a fresh target. *Not built.*
5. **Teach-back** — explain it, or write the *detection* for it. Teaching is the test.
   *Not built.*

Two mechanics build the literal muscle memory:

- **Command drills.** Like the subnet/ports drills, but for keystrokes:
  "Enumerate every computer in the domain in PowerShell" → you type the real command →
  it checks it. Repetition of the actual syntax, not multiple choice.
  *Built: `elite drill commands`.*
- **Spaced repetition.** Missed quiz items and tools you haven't touched in a while
  resurface automatically, so nothing you learned decays silently.
  *Partly built: missed and overdue commands come back in the command drill, and
  `elite review` lists stale and barely-cleared missions and weak quizzes. Single quiz
  questions do not resurface on their own.*

And the **spine keeps everything located**: you never learn a tool in a vacuum, you learn
*where it sits* — nmap at the Wire, John at the Door, sqlmap at the App, Ghidra at the
Host, BloodHound at the Domain, Sysmon across the Hunt. That mental map is what separates
someone who knows tools from someone who understands systems.
[CURRICULUM.md](CURRICULUM.md) holds the spine.

---

## 4. A day in the tool (end to end)

**Not built as written.** This walk needs the hosted lab: steps 1, 3 and 4 run real tools
against live hosts. The offline version of the same chain is built. `elite engage` chains
the missions through loot, and `elite scenario` walks one incident from break to detect to
fix.

A single campaign against your lab company, chaining the layers:

1. `elite run nmap 10.10.0.0/24` → find the web host and the DC. *(Wire)*
2. `elite lab start app-01` → SQL-inject the app, read a connection string with stored
   creds. *(App — your SQL Server home turf)*
3. Those creds are a domain user → `elite run bloodhound` → find a path to Domain Admin.
   *(Domain)*
4. `elite run impacket …` → walk the path, read the flag on the DC. *(Host/Domain)*
5. `elite lab start app-01-defend` → now find your own attack in the SQL Server audit and
   Windows logs, then fix the service-account privilege that made it possible. *(Hunt +
   hardening)*

Every step: real tool, real target you own, a flag that proves it, a debrief that teaches
it, and a defensive counterpart so you learn to close what you just opened.

---

## 5. Build order to get there

**Partly built.** The build order is kept in one place,
[SPEC.md](SPEC.md#build-order), with a mark on every step. In short: the engine, the
command drills, the fix twins, `elite ask` and `elite path` exist; the hosted lab and the
missions against live targets are the open work.
