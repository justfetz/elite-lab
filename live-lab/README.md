# live-lab — Lakefront Paper & Container Co., for real

The offline missions teach the concepts with zero setup. **live-lab** is the optional
graduation: a real, running version of the company (see `../SCENARIO.md`) that you host on
your own machine and attack with real tools — then defend.

It's a **"Northwind for security"**: a reproducible sample company whose database, data, and
app ship here in the repo. Some objects are *intentionally* vulnerable — each tagged `[VULN]`
with the lesson — so you find the hole, exploit it, and write the fix.

> **Legal & local.** Everything here runs on hardware you own, against a fictional company.
> This is a target you build for yourself. Never point these techniques at a system you don't
> own or lack written permission to test.

## What's here (and what's coming)

```
live-lab/
  db/
    schema.sql      ✅ the millops SQL Server schema + seed data + a vulnerable proc
  orderdesk/        ⏳ the OrderDesk web portal (login, order tracking, the mill dashboard)
  mill-agent/       ⏳ the on-site edge service (receives order releases over TCP/UDP)
  millie/           ⏳ the AI order agent (RAG + data agent over millops)
  docker-compose.yml ⏳ brings the whole company up with one command
```

✅ = built · ⏳ = being built, in order.

## Step 1 — the database (available now)

Run a local SQL Server (free **Developer edition**, or the official container):

```bash
# option A: Docker (works on Windows/Mac/Linux)
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Your_strong_pw1" \
  -p 1433:1433 --name millops-sql -d mcr.microsoft.com/mssql/server:2022-latest

# then load the schema (sqlcmd ships in the image, or use Azure Data Studio):
docker exec -i millops-sql /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'Your_strong_pw1' -i - < db/schema.sql
```

That creates the `millops` database. Now open `db/schema.sql` and read it as the security
team would: **find every `[VULN]` tag and name the lesson.** There are four to start —
unsalted hashes, an injectable tracking proc, an over-privileged app login, and a weak admin
password. The upcoming OrderDesk app wires a UI onto exactly these holes.

## The planned missions (against your own running company)

| Mission | Surface | You do | Then you fix |
|---|---|---|---|
| `live-sqli` | OrderDesk tracking | inject via `sp_TrackOrder` with real `sqlmap` | parameterize (`sp_executesql`) |
| `live-idor` | OrderDesk orders | tamper an ID to read another plant's orders | enforce per-customer authz |
| `live-key`  | OrderDesk DOM | find the Maps API key leaked in client JS | restrict + rotate the key |
| `live-link` | HQ↔mill seam | sniff and forge an order release to `mill-agent` | authenticate + sign the link |
| `live-millie` | the AI agent | prompt-inject Millie into leaking another plant's data | scope the agent + least-privilege DB login |
| `live-hunt` | the logs | spot the SQLi, the phish, and the Tor exit node | — (detection) |

Build order follows the table. Next up: the `db/` is in; the OrderDesk portal (with the
mill dashboard as its front page) comes next.
