# The scenario: you are the security team at Lakefront Paper & Container Co.

> **Doc status: current** · answers: *Who is the company I defend, and where can it be broken?* · [doc map](README.md#doc-map)

Everything in elite-lab hangs on one fiction, so every mission has a reason to exist. The
company is a real-feeling one on purpose — a manufacturer, not a vague "tech startup" —
because the interesting security lives in the seams of a business that actually makes and
ships something.

## The company

**Lakefront Paper & Container Co.** runs a paper mill on the Chicago River. It takes orders
from **corrugator plants** (the factories that turn paper rolls into cardboard), makes the
product, **loads trucks by weight**, and delivers. The business side and the plant floor
are separate trust worlds joined by one controlled conduit, and that split is the whole
point:

```
       the business side (IT)                                 the plant floor (OT)
  ┌──────────────────────────────┐                       ┌──────────────────────────────┐
  │ public                       │      one conduit      │ FIREWALL                     │
  │   OrderDesk  customer portal │   ┌───────────────┐   │  └─ mill-agent: receives the │
  │   Millie     AI order agent  │──▶│ order-release │──▶│     release and drives PM3   │
  │ office network               │   │ staging (DMZ) │   │     PM3  the paper machine   │
  │   dc01, ws01, the SOC        │   └───────────────┘   │     LoadMaster  optimizer    │
  └──────────────────────────────┘   one direction only  └──────────────────────────────┘
          ▲
          │  corrugator-plant customers log in to "see my orders"
       customer
```

- **OrderDesk** — the public web portal. Customers log in and track orders and shipments.
- **Millie** — an AI assistant bolted on last year: a RAG agent that reads customer
  documents and writes orders.
- **millops** — the SQL Server database behind OrderDesk: customers, users, orders,
  trucks, shipments.
- **The office network** — Active Directory on `dc01`, employee workstations such as
  `ws01`, and the SOC's log pipeline.
- **Order-release staging** — the conduit. HQ writes a signed order release here and the
  floor reads it. Orders cross in one direction only.
- **mill-agent** — the on-site service behind the plant firewall that receives an order
  release and drives PM3, the paper machine.
- **LoadMaster** — cutting-stock and truck-load optimization for the floor (your
  optimization background lives here).
- **Email** — the human layer, which no firewall covers: where phishing arrives.

The diagram is a sketch and leaves out email and the wire itself. The zones, the systems
in each and their addresses come from the world registry: [ATLAS.md](ATLAS.md#missions-by-zone-and-system) prints them, and
`elite map` shows them with your progress.

**You are the security team.** Your job: find and fix every way Lakefront can be broken —
across the office IT, the public app, the mill floor, and the AI product — before an
attacker (or a customer's auditor) does. You work it from the CLI, with your own tools
(`elite tools`) and your own bookshelf (`elite study`) as your kit.

## Why the split matters

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

## The attack surface — every hit point maps to a STRIDE threat and a system

| Hit point | STRIDE | Where it lives |
|-----------|--------|----------------|
| **The wire** — exposed services, an intrusion in the logs | R / D | The wire |
| **The HQ↔mill link** — forge or replay an order release across the seam | **S·T** | Order-release staging and the mill-floor agent |
| **The door** — weak or stolen credentials, crackable hashes | **S** | Workstation ws01 |
| **OrderDesk (the app)** — SQL injection, broken access control (see other plants' orders) | **T·I·E** | Customer Portal |
| **The DOM / client** — a leaked API key in the page's JavaScript, client-side trust | **I** | Customer Portal, in the [live lab](live-lab/README.md) only |
| **millops (the data)** — an over-privileged login, a dynamic-SQL procedure | **I·E** | The portal's database, in the [live lab](live-lab/README.md) only |
| **The host** — a suspicious binary; privilege escalation | **T·E** | Workstation ws01 |
| **The domain** — Active Directory: one credential → Domain Admin | **S·E** | Domain Controller dc01 |
| **Millie (the AI product)** — prompt injection, cross-customer data leak, an over-permissioned agent | **T·I·E** | Millie, the AI order agent |
| **People** — phishing, lookalike domains, spoofed senders | **S** | Corporate email |
| **The hunt** — can you find all of the above in the logs? | **R** | SOC / log pipeline |

This table does not list missions, because that list changes.
[ATLAS.md](ATLAS.md#missions-by-zone-and-system) is generated from the registry and shows
which missions exist on each system today. A system marked "none yet" there has no
mission.

## How you play it

1. **Recon** the company (`elite engage recon`) — what's exposed?
2. **Threat-model** a surface — what could go wrong here, and which STRIDE threat is it?
3. **Prove it** — run the mission; the checker runs *your* work, so you can't fake it.
4. **Fix it** — many break missions have a fix twin; you write the patch that closes the hole.
5. **Hunt it** — then take the defender's chair and find an intrusion in the logs.

`elite scenario` chains those steps around one incident, end to end.

## The live lab

The offline missions stay zero-setup. On top of them, `live-lab/` is an *optional* running
version of Lakefront that you host on your own machine and attack with real tools.
[live-lab/README.md](live-lab/README.md) says which parts of it exist today.

> **Legal & local, always.** Every bit of this runs on hardware you own, against a fictional
> company. `elite run` refuses active tools aimed outside your lab. The rule never changes:
> test only what you own or have written permission to test.
