# Atlas: what is built

> **Doc status: current** · answers: *Which missions exist, where does each one live, and what is not built yet?* · [doc map](README.md#doc-map)

This file is generated. `python3 _build_atlas.py` writes it from the world registry
([`elitelab/world.py`](elitelab/world.py)), the mission modules
([`elitelab/missions/`](elitelab/missions)), the learn modules ([`modules/`](modules))
and the drill bank ([`drills/`](drills)). Don't edit it by hand: change the code, run
the script and commit both. A test fails when this file and the code disagree.

What a mission is, and what each registry field means, is in [MISSIONS.md](MISSIONS.md).

## At a glance

| What | Count | Read from |
|---|---|---|
| Missions | 20 | `EXERCISES` in the registry, one record per mission; 11 run your work with a checker, 9 take a flag |
| Zones | 5 | `ZONES` in the registry; 4 carry at least one mission |
| Systems | 11 | `SYSTEMS` in the registry; 8 carry at least one mission |
| Incident scenarios | 2 | `SCENARIOS` in the registry |
| Learn modules | 15 | `modules/*.json`: 62 lessons, 49 quiz questions, 13 tool briefings |
| Drills | 3 | `elite drill`: ports, subnet, commands; the command bank holds 22 commands |
| Tool tutors | 5 | `elite run`: nmap, sqlmap, john, gobuster, ffuf |
| Cheat sheets | 11 | `elite cheat`: grep, curl, awk, find, sort, chmod, strings, ssh, nmap, john, sudo |
| Tests | run `pytest -q` | the test run prints its own count; no doc repeats it |

## Planned, not built

These are the gaps the registry shows: the systems, break missions and levels
that no mission covers yet.

- No mission yet on Order-release staging, PM3 paper machine or LoadMaster optimizer.
- No fix mission yet to pair with the break missions `crack-01`, `bin-01` and `priv-01`.
- No mission yet at the `recovery` level (the levels run from `intro` to `recovery`).

Plans that go beyond the registry, such as a live lab you host yourself, are in
[VISION.md](VISION.md) and [SPEC.md](SPEC.md). Each section there is marked built,
partly built or not built.

## Missions, in campaign order

The order of `EXERCISES` in the registry is the campaign order `elite path` walks.
The skill column is the registry's own `skill` line. Checked by: **checker** means
the mission runs the files you wrote; **flag** means you submit an answer and the
mission compares it with its own solution.

| # | Mission | Title | System | Verb | Level | Checked by | Skill, in the registry's words |
|---|---|---|---|---|---|---|---|
| 1 | [`wire-01`](elitelab/missions/wire_01.py) | Intrusion in the logs | The wire | recon | intro | flag | read the traffic and find the leak |
| 2 | [`build-01`](elitelab/missions/build_01.py) | Build your own port scanner | The wire | build | toolkit | checker | build a port scanner |
| 3 | [`build-02`](elitelab/missions/build_02.py) | Build a packet sniffer (parser) | The wire | build | toolkit | checker | build a packet sniffer |
| 4 | [`crack-01`](elitelab/missions/crack_01.py) | Crack the CEO | Workstation ws01 | break | implementation | flag | a leaked password-hash dump |
| 5 | [`app-01`](elitelab/missions/app_01.py) | Break the portal (SQL injection) | Customer Portal | break | guided | flag | order lookup looks injectable (SQLi) |
| 6 | [`app-01-fix`](elitelab/missions/app_01.py) | Fix the portal (parameterize) | Customer Portal | fix | implementation | checker | BLUE: parameterize the query |
| 7 | [`idor-01`](elitelab/missions/idor_01.py) | Break access control (IDOR) | Customer Portal | break | guided | flag | order pages use sequential IDs (IDOR) |
| 8 | [`idor-01-fix`](elitelab/missions/idor_01.py) | Enforce access control | Customer Portal | fix | implementation | checker | BLUE: enforce ownership checks |
| 9 | [`bin-01`](elitelab/missions/bin_01.py) | Crack the binary | Workstation ws01 | break | implementation | flag | a licensed tool guarding a key (needs local access) |
| 10 | [`priv-01`](elitelab/missions/priv_01.py) | Linux privilege escalation | Workstation ws01 | break | implementation | flag | low-priv shell; a sudo/SUID misconfig may give root |
| 11 | [`build-03`](elitelab/missions/build_03.py) | Build a debugger's breakpoint engine | The wire | build | toolkit | checker | build a debugger (breakpoints) |
| 12 | [`build-04`](elitelab/missions/build_04.py) | Build a fuzzer | The wire | build | toolkit | checker | build a fuzzer |
| 13 | [`domain-01`](elitelab/missions/domain_01.py) | Path to Domain Admin | Domain Controller dc01 | break | operational | flag | map a path to Domain Admin -- needs a foothold |
| 14 | [`domain-01-fix`](elitelab/missions/domain_01.py) | Cut the path to Domain Admin | Domain Controller dc01 | fix | operational | checker | BLUE: cut the path to DA |
| 15 | [`ai-01`](elitelab/missions/ai_01.py) | Poison the agent (prompt injection) | Millie, the AI order agent | break | guided | checker | the RAG product; retrieves customer documents (injection) |
| 16 | [`ai-01-fix`](elitelab/missions/ai_01.py) | Defend the agent | Millie, the AI order agent | fix | implementation | checker | BLUE: stop the injection |
| 17 | [`hunt-01`](elitelab/missions/hunt_01.py) | Hunt the intrusion | SOC / log pipeline | detect | investigation | flag | reconstruct the breach from auth + process logs |
| 18 | [`phish-01`](elitelab/missions/phish_01.py) | Triage a phishing email | Corporate email | detect | guided | flag | triage a phishing email and pull the real link |
| 19 | [`mill-01`](elitelab/missions/mill_01.py) | Forge a mill release (down the line) | Mill-floor agent | break | guided | checker | the HQ->mill release link -- forge a release and down PM3 |
| 20 | [`mill-01-fix`](elitelab/missions/mill_01.py) | Verify the mill release | Mill-floor agent | fix | stateful | checker | BLUE: verify releases (HMAC + freshness + no-replay + bounds) |

Verbs, in registry order: `recon`, `build`, `break`, `fix`, `detect`. Levels, lowest rung first: `intro`, `toolkit`, `guided`, `implementation`, `stateful`, `operational`, `investigation`, `recovery`.

## Missions by zone and system

The registry's view, which `elite map` prints with your progress: each zone is a
trust world, each system sits in exactly one zone, and each mission lives on one
system.

| Zone | Trust | System | Address | Missions |
|---|---|---|---|---|
| IT / Business (public) | public | Customer Portal (`orderdesk`) | 10.10.0.20 | `app-01` `app-01-fix` `idor-01` `idor-01-fix` |
| IT / Business (public) | public | Millie, the AI order agent (`millie`) | 10.10.0.50 | `ai-01` `ai-01-fix` |
| IT / Corporate (internal) | internal | Domain Controller dc01 (`dc01`) | 10.10.0.10 | `domain-01` `domain-01-fix` |
| IT / Corporate (internal) | internal | Workstation ws01 (`ws01`) | 10.10.0.31 | `crack-01` `bin-01` `priv-01` |
| IT / Corporate (internal) | internal | SOC / log pipeline (`soc`) |  | `hunt-01` |
| IT / Corporate (internal) | internal | The wire (`wire`) |  | `wire-01` `build-01` `build-02` `build-03` `build-04` |
| DMZ / Conduit | conduit | Order-release staging (`release`) | 10.15.0.4 | none yet |
| OT / Plant floor | isolated | Mill-floor agent (`mill`) | 10.20.0.5 | `mill-01` `mill-01-fix` |
| OT / Plant floor | isolated | PM3 paper machine (`pm3`) |  | none yet |
| OT / Plant floor | isolated | LoadMaster optimizer (`loadmaster`) |  | none yet |
| People | human | Corporate email (`email`) |  | `phish-01` |

## Missions by layer

The mission modules' view, which `elite path` and `elite lab list` print: each
mission module labels itself with a layer and a difficulty.

| Layer | Missions (difficulty) |
|---|---|
| 1 The Wire | `wire-01` (intro), `build-01` (easy), `build-02` (medium) |
| 2 The Door | `crack-01` (easy) |
| 3 The App | `app-01` (easy), `app-01-fix` (easy), `idor-01` (easy), `idor-01-fix` (easy) |
| 4 The Host | `bin-01` (medium), `priv-01` (medium), `build-03` (medium), `build-04` (medium) |
| 5 The Domain | `domain-01` (hard), `domain-01-fix` (hard) |
| 6 The Hunt | `hunt-01` (medium) |
| 7 The Mill (OT) | `mill-01` (medium), `mill-01-fix` (hard) |
| AI product | `ai-01` (medium), `ai-01-fix` (medium) |
| People | `phish-01` (easy) |

## Break and fix pairs

A fix twin is its break mission's id plus `-fix`. The invariant is the
business function that must still work after the fix.

| Break | Fix twin | What must still work after the fix |
|---|---|---|
| `crack-01` | none yet |  |
| `app-01` | `app-01-fix` | a customer can still look up their own orders |
| `idor-01` | `idor-01-fix` | a customer can still see their own orders |
| `bin-01` | none yet |  |
| `priv-01` | none yet |  |
| `domain-01` | `domain-01-fix` | legitimate admins can still manage the domain |
| `ai-01` | `ai-01-fix` | normal customer questions still get a real answer |
| `mill-01` | `mill-01-fix` | legitimate releases still reach PM3 and production continues |

## The loot chain

Solving a mission grants loot. A mission that needs loot stays locked on the
`elite engage` board until you hold any one of the items it lists.

| Mission | Needs (any one) | Grants |
|---|---|---|
| `crack-01` |  | `domain_user_cred` |
| `app-01` |  | `db_service_cred` |
| `app-01-fix` | `db_service_cred` | `hardened_sqli` |
| `idor-01` |  | `customer_pii` |
| `idor-01-fix` | `customer_pii` | `hardened_idor` |
| `bin-01` | `root_ws01` | `license_key` |
| `priv-01` |  | `root_ws01` |
| `domain-01` | `domain_user_cred` `db_service_cred` | `domain_admin` |
| `domain-01-fix` | `domain_admin` | `hardened_ad` |
| `ai-01` |  | `admin_api_key` |
| `ai-01-fix` | `admin_api_key` | `hardened_agent` |
| `hunt-01` |  | `incident_report` |
| `mill-01` |  | `mill_control` |
| `mill-01-fix` | `mill_control` | `hardened_mill` |

## Evidence the registry declares

The `emits` field names the evidence a mission's activity leaves for a later
detection mission. [MISSIONS.md](MISSIONS.md#6-what-the-mission-leaves-for-the-hunt)
says how far that is wired today.

| Mission | Verb | Emits |
|---|---|---|
| `wire-01` | recon | `pcap` `access.log` |
| `crack-01` | break | `auth.log` |
| `app-01` | break | `app.log` `sql_audit` |
| `idor-01` | break | `app.log` |
| `priv-01` | break | `auth.log` `proc.log` |
| `domain-01` | break | `security.evtx` |
| `ai-01` | break | `agent.log` |
| `hunt-01` | detect | `incident_report` |
| `phish-01` | detect | `email_headers` |
| `mill-01` | break | `release.log` |
| `mill-01-fix` | fix | `release.log` |

## Incident scenarios

`elite scenario` walks these. Each chains existing missions around one incident.

| Scenario | The question it defends | Steps, in order |
|---|---|---|
| `compromised-release`: Compromised production release | Can you keep PM3 producing while cutting the path from the public side to the floor? | `ai-01` `app-01` `mill-01` `hunt-01` `mill-01-fix` `ai-01-fix` |
| `customer-data-breach`: Customer data breach | Can customers still look up their own orders once you lock cross-customer access? | `idor-01` `app-01` `hunt-01` `idor-01-fix` `app-01-fix` |

## Learn modules

`elite learn <module>` reads the lessons, `elite quiz <module>` asks the
questions and `elite tools <module>` shows the tool briefings.

| Module | Title | Lessons | Quiz questions | Tool briefings |
|---|---|---|---|---|
| `basics` | Getting started (what the words mean) | 8 | 3 | 0 |
| `threat-modeling` | Threat modeling | 5 | 4 | 0 |
| `shell-basics` | Terminal basics (bash, PowerShell, grep & curl) | 6 | 6 | 0 |
| `networking` | Networking fundamentals | 6 | 8 | 0 |
| `people` | The People layer (phishing & recon) | 6 | 5 | 0 |
| `security` | Security principles | 6 | 5 | 0 |
| `windows` | Windows internals | 6 | 5 | 0 |
| `windows-ps` | PowerShell for security | 5 | 5 | 0 |
| `linux` | Linux fundamentals | 3 | 3 | 0 |
| `tools-recon` | Tools: recon & scanning | 1 | 0 | 2 |
| `web-vulns` | Web vulnerabilities & bug hunting | 6 | 5 | 0 |
| `tools-web` | Tools: web app testing | 1 | 0 | 3 |
| `tools-ad` | Tools: Active Directory | 1 | 0 | 2 |
| `tools-pw` | Tools: password & hash cracking | 1 | 0 | 3 |
| `tools-re` | Tools: reverse engineering & bare metal | 1 | 0 | 3 |

## The command-drill bank

`elite drill commands` asks you to type the real command. The bank, by platform:

| Platform | Commands |
|---|---|
| powershell | 6 |
| linux | 4 |
| nmap | 4 |
| curl | 2 |
| john | 2 |
| dig | 1 |
| hashcat | 1 |
| sqlmap | 1 |
| windows | 1 |
