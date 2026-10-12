# The scenario: you are the security team at Vantaris AI

Everything in elite-lab hangs on one fiction, so every mission has a reason to exist.

**Vantaris AI is a startup building and selling a RAG agent product** — an AI assistant
that answers customer questions over the customer's own documents and data. You are the
**security team**. Your job is to find and fix every **hit point** across the company
*before* an attacker (or a customer's auditor) does — across the org, the app, and the
product itself.

That last part is the twist, and it's the whole reason this is current: **the product you
sell is also attack surface.** A RAG/agent that can read data and call tools is a new kind
of door. Securing it is the skill companies are desperate for right now.

## The method: threat-model first, then verify

You don't poke at Vantaris randomly — you **threat-model** it (see the `threat-modeling`
module). Draw the system, mark the trust boundaries, walk STRIDE at each one, and every
threat you find becomes a hit point to prove with a mission. STRIDE =
**S**poofing, **T**ampering, **R**epudiation, **I**nformation disclosure,
**D**enial of service, **E**levation of privilege.

## The attack surface (every hit point maps to a layer, a STRIDE threat, and a mission)

| Hit point | STRIDE | Layer | Mission(s) |
|-----------|--------|-------|------------|
| **People / the wire** — exposed services, intrusion in the logs | R / D | 1 Wire | `wire-01` (done) |
| **The door** — weak/stolen credentials, crackable hashes | **S** | 2 Door | `crack-01` (done) |
| **The app** — the product's web API: SQL injection, broken authz | **T·I·E** | 3 App | `app-01` + `app-01-fix` (done) |
| **The data** — SQL Server: over-privileged login, `xp_cmdshell`, RLS bypass | **I·E** | 3 App / 4 Host | *live SQL Server lab (next)* |
| **The host** — a suspicious binary; privilege escalation | **T·E** | 4 Host | `bin-01` (done) |
| **The domain** — Active Directory: one cred → Domain Admin | **S·E** | 5 Domain | *AD lab (planned)* |
| **The product (AI)** — prompt injection, retrieval data leakage, over-permissioned agent | **T·I·E** | AI | *capstone (planned)* |
| **The hunt** — can you detect all of the above in the logs? | **R** | 6 Hunt | blue-team twin of each mission |

## How you play it

You work the surface the way a real security team does an assessment:

1. **Recon** the org (`elite run nmap …` against the lab) — what's exposed?
2. **Break** each hit point in its mission — prove the risk with a captured flag.
3. **Fix** it in the blue-team twin — and have the checker confirm the hole is closed.
4. **Understand** it — `elite ask` pulls the mechanism from your books (Windows Internals
   for host/domain, OWASP for the app and the AI product).

When you've cleared every hit point, you've done end-to-end what Vantaris AI would pay a
consultant for — and you have the muscle memory to do it on a real engagement.

## Why the AI product is the keystone

Vantaris's product is a RAG agent — exactly the thing every company is now shipping and
nobody knows how to secure. The capstone turns the product on itself: you attack Vantaris's
own agent (feed it a poisoned document, make its text-to-SQL agent leak rows it shouldn't,
trick it into misusing a tool), then harden it (least-privilege identity, query allow-lists,
treating retrieved text as data not instructions). Your SQL Server decade is the edge:
you already know how the data tier leaks; now you learn how the AI on top of it leaks too.
