# OrderDesk — the Lakefront customer portal (training target)

A small, **intentionally vulnerable** web app you host on your own machine. It's the public
face of Lakefront Paper: a mill dashboard, a login, and order tracking — wired onto the same
weaknesses the `millops` schema documents, so you practice finding and fixing them.

> Local and legal: this is a target you run for yourself on `127.0.0.1`. Nothing here touches
> a system you don't own.

## Run it

```bash
pip install flask
python app.py
# open http://127.0.0.1:5000
```

It seeds its own SQLite file on first run — no database setup needed. (The SQL Server
version in `../db/schema.sql` is the backend you graduate to later.)

## The four holes, and the tool for each

Each is tagged `[VULN]` in `app.py` with the lesson. The point of every one is the same:
exploit it to understand it, then **write the fix.**

| Hole | Where | Concept | Tool you'd reach for | The fix |
|------|-------|---------|----------------------|---------|
| SQL injection | order tracker | unsanitized input in a query | `sqlmap` | parameterized queries |
| Broken access control (IDOR) | order detail page | no ownership check | browser / `curl` | check the order belongs to the logged-in plant |
| Leaked API key | the page source | client-side secret | view-source | restrict + rotate the key server-side |
| Weak / unsalted password | the login | fast unsalted hash | `john` (on a dumped hash) | salt + a slow KDF (bcrypt/argon2) |

## How the CLI points you (the design)

You never have to guess which tool to use. Each live mission's briefing names **the surface,
the tool, and the target** at the moment you need it — then explains *why* that tool fits
*that* hole. OrderDesk is the running target those missions aim you at. Build order and the
mission list are in `../README.md`.

The defensive habit this builds: for every hole you open, you close it. The repo keeps both
the broken version (to learn on) and the fix (to verify you understood).
