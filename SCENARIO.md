# The scenario: you are the security team at Lakefront Paper & Container Co.

Everything in elite-lab hangs on one fiction, so every mission has a reason to exist. The
company is a real-feeling one on purpose — a manufacturer, not a vague "tech startup" —
because the interesting security lives in the seams of a business that actually makes and
ships something.

## The company

**Lakefront Paper & Container Co.** runs a paper mill on the Chicago River. It takes orders
from **corrugator plants** (the factories that turn paper rolls into cardboard), makes the
product, **loads trucks by weight**, and delivers. Two systems run the business, and the
split between them is the whole point:

```
        HQ / cloud (IT)                              the mill floor (OT)
  ┌──────────────────────────┐                ┌────────────────────────────────┐
  │ OrderDesk  customer portal│   order        │  FIREWALL                      │
  │ LoadMaster truck loading  │   release       │   └─ mill-agent: receives the  │
  │ "Millie"   AI order agent │ ──TCP/IP──────▶ │        release, runs the order │
  │ SQL Server (millops DB)   │ ◀─UDP status──  │        on the machine          │
  └──────────────────────────┘                 └────────────────────────────────┘
          ▲
          │  corrugator-plant customers log in to "see my orders"
       customer
```

- **OrderDesk** — the public web portal. Customers log in and track orders and shipments.
- **LoadMaster** — schedules and loads trucks by weight (your optimization background lives here).
- **Millie** — an AI assistant bolted on last year: a RAG + data agent that answers
  "where's my order?" by reading the docs *and* querying the database.
- **mill-agent** — the on-site service behind the plant firewall that receives an order
  release over TCP and reports machine status back as UDP datagrams.
- **millops** — the SQL Server database: customers, orders, trucks, shipments, routes, users.

**You are the security team.** Your job: find and fix every way Lakefront can be broken —
across the office IT, the public app, the mill floor, and the AI product — before an
attacker (or a customer's auditor) does. You work it from the CLI, with your own tools
(`elite tools`) and your own bookshelf (`elite study`) as your kit.

## Why two components

A single app has no interesting trust boundary. The moment HQ and the mill talk across the
firewall, you get the thing security is actually about: **the seam.** Is that order-release
link authenticated? Encrypted? Replay-protected? Can someone on the wire forge a release to
the machine? That IT→OT boundary is exactly where real manufacturing attacks happen
(ransomware's favorite target, because mill downtime is enormously expensive).

## The method: threat-model first, then verify

You don't poke at Lakefront randomly — you **threat-model** it (`elite learn threat-modeling`).
Draw the system, mark the trust boundaries, walk **STRIDE** at each one, and every threat you
find becomes a hit point to prove with a mission. STRIDE = **S**poofing, **T**ampering,
**R**epudiation, **I**nformation disclosure, **D**enial of service, **E**levation of privilege.

## The attack surface — every hit point maps to a layer, a STRIDE threat, and a mission

| Hit point | STRIDE | Layer | Mission(s) |
|-----------|--------|-------|------------|
| **The wire** — exposed services, an intrusion in the logs | R / D | 1 Wire | `wire-01` |
| **The HQ↔mill link** — forge/replay an order release across the seam | **S·T** | 1 Wire | *live-lab (building)* |
| **The door** — weak/stolen credentials, crackable hashes | **S** | 2 Door | `crack-01` |
| **OrderDesk (the app)** — SQL injection, broken access control (see other plants' orders) | **T·I·E** | 3 App | `app-01`/`-fix`, `idor-01`/`-fix` |
| **The DOM / client** — a leaked API key in the page's JavaScript, client-side trust | **I** | 3 App | *live-lab (building)* |
| **millops (the data)** — over-privileged login, dynamic-SQL proc, `xp_cmdshell` | **I·E** | 3 App / 4 Host | *live-lab (building)* |
| **The host** — a suspicious binary; privilege escalation | **T·E** | 4 Host | `bin-01`, `priv-01` |
| **The domain** — Active Directory: one cred → Domain Admin | **S·E** | 5 Domain | `domain-01`/`-fix` |
| **Millie (the AI product)** — prompt injection, cross-customer data leak, over-permissioned agent | **T·I·E** | AI | `ai-01`/`-fix`, *live agent (building)* |
| **The hunt** — can you detect all of the above: brute force, phishing, a Tor exit node in the logs? | **R** | 6 Hunt | `hunt-01`, *Tor/phishing (planned)* |

## How you play it

1. **Recon** the company (`elite engage recon`) — what's exposed?
2. **Threat-model** a surface — what could go wrong here, and which STRIDE threat is it?
3. **Prove it** — run the mission; the checker runs *your* work, so you can't fake it.
4. **Fix it** — most missions have a break→fix pair; you write the patch that closes the hole.
5. **Hunt it** — then find the same attack in the logs, from the defender's chair.

## The live lab (being built)

The offline missions stay zero-setup. On top of them, `live-lab/` is an *optional* real
version of Lakefront you host on your own machine (Docker + SQL Server), so you attack a
**real running app with real tools** — the `millops` database, the OrderDesk portal (with
its mill dashboard), the mill-agent link, and Millie the AI agent. It's a "Northwind for
security": a reproducible sample company whose schema, data, and procs ship in the repo —
some of them *intentionally* vulnerable, clearly labeled, for you to find and fix.

> **Legal & local, always.** Every bit of this runs on hardware you own, against a fictional
> company. `elite run` refuses active tools aimed outside your lab. The rule never changes:
> test only what you own or have written permission to test.
