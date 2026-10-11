# The vision: elite-lab as a cyber range you command

The end state: `elite` is the console for a small, deliberately flawed "company" you
run on your own hardware — a domain, a few hosts, and an app with a real database —
and the tool walks you through attacking and defending every layer, teaching the
lesson at each step and drilling it until it's muscle memory.

---

## 1. The "company" you practice on (the lab)

You build a sandbox that looks like a real org. Everything here is free and legal
because you own all of it.

### Active Directory (the domain)

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

`elite` gains three mission *flavors*, all sharing the same goal/flag/checker/hint loop:

1. **Self-contained** (built today): generated artifact + flag. Always works, no lab.
2. **Live-target**: `elite lab start ad-01` checks the lab is reachable, gives a goal
   ("get Domain Admin and read `\\dc01\flag.txt`"), you use the *real* tools, capture the
   flag, submit, checker verifies. This is Hack The Box, but it's *your* box.
3. **Blue-team twin**: every attack mission has a defense counterpart. After you break
   in, `elite lab start ad-01-defend` hands you the logs and asks you to detect the
   attack and cut the path — and checks your remediation.

Around the missions:

- `elite run <tool> …` — run the real tool, get a taught debrief (built; nmap today,
  sqlmap/BloodHound/Impacket/John next).
- `elite ask "…"` — the local book RAG, always a command away mid-mission.
- `elite path` — a guided campaign that walks the "how data moves" layers in order.

---

## 3. How tools actually get learned (the muscle-memory engine)

Reading doesn't stick; reps do. Each tool/skill moves through five stages, and the tool
tracks where you are on each:

1. **Concept** — a short lesson (`elite learn`) so you know *why*.
2. **Demo** — `elite run` on a sample, so you see the shape of a real result.
3. **Guided mission** — do it for real with hints available.
4. **Unguided mission** — same class of task, no hints, a fresh target.
5. **Teach-back** — explain it, or write the *detection* for it. Teaching is the test.

Two mechanics build the literal muscle memory:

- **Command drills.** Like the subnet/ports drills, but for keystrokes:
  "Enumerate every computer in the domain in PowerShell" → you type the real command →
  it checks it. Repetition of the actual syntax, not multiple choice.
- **Spaced repetition.** Missed quiz items and tools you haven't touched in a while
  resurface automatically, so nothing you learned decays silently.

And the **spine keeps everything located**: you never learn a tool in a vacuum, you learn
*where it sits* — nmap at the Wire, John at the Door, sqlmap at the App, Ghidra at the
Host, BloodHound at the Domain, Sysmon across the Hunt. That mental map is what separates
someone who knows tools from someone who understands systems.

---

## 4. A day in the tool (end to end)

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

- [x] Engine: lessons, quizzes, drills, missions, `elite run`, local book RAG.
- [ ] **Lab provisioner**: a `lab/` folder — Docker Compose for SQL Server + a small
      vulnerable app (seed + deliberate flaws), and scripts/pointers for the AD options.
- [ ] **Live-target mission type**: reachability check + flag verification against the lab.
- [ ] **Command-drill mode** for real keystroke repetition.
- [ ] **Blue-team twins** for the first few missions.
- [ ] `elite ask` and `elite path` as first-class commands.
- [ ] Tool tutors for sqlmap, BloodHound, Impacket, John, Ghidra.
