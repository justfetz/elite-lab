"""Missions app-01 (break) and app-01-fix (build): SQL injection, hands-on.

Ships a deliberately vulnerable SQLite-backed 'customer portal' lookup script.
- app-01      BREAK: inject to dump a secret flag from a table you weren't meant to see.
- app-01-fix  BUILD: patch portal.py so the injection fails but normal lookups still work;
              the checker actually runs your patched file to verify.

SQLite keeps it zero-setup and cross-platform; every concept maps straight to SQL Server.
"""
import hashlib
import random
import subprocess
import sys
from pathlib import Path

from .base import Mission

SEED = 0x5987112
USERNAMES = ["alice", "bob", "carol", "dave", "erin"]
INJECTION = "' UNION SELECT value FROM secrets --"


def _flag():
    rng = random.Random(SEED)
    token = hashlib.sha1(str(rng.random()).encode()).hexdigest()[:10]
    return f"flag{{sqli_{token}}}"


PORTAL_SRC = '''\
import os, sqlite3, sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "portal.db")

# Pass --show as the first argument to PRINT the exact SQL this builds, so you can
# watch your input become part of the query. (e.g. python3 portal.py --show alice)
args = sys.argv[1:]
show = bool(args) and args[0] == "--show"
if show:
    args = args[1:]
term = args[0] if args else ""

con = sqlite3.connect(DB)
# ---- VULNERABLE: user input concatenated straight into SQL ----
# Your job in app-01-fix is to make this query safe (parameterize it)
# WITHOUT breaking normal lookups.
sql = "SELECT username FROM users WHERE username = '" + term + "'"
if show:
    print("-- SQL that will run --\\n" + sql + "\\n-----------------------")
for row in con.execute(sql):
    print(row[0])
'''


def _build(workdir: Path):
    import sqlite3
    (workdir / "portal.py").write_text(PORTAL_SRC)
    dbp = workdir / "portal.db"
    if dbp.exists():
        dbp.unlink()
    con = sqlite3.connect(dbp)
    con.execute("CREATE TABLE users(username TEXT, pw TEXT)")
    con.executemany("INSERT INTO users VALUES(?,?)", [(u, "x") for u in USERNAMES])
    con.execute("CREATE TABLE secrets(name TEXT, value TEXT)")
    con.execute("INSERT INTO secrets VALUES(?,?)", ("admin_flag", _flag()))
    con.commit()
    con.close()


def setup_break(workdir: Path):
    _build(workdir)
    (workdir / "START_HERE.txt").write_text(
        "GOAL: read the admin_flag from the 'secrets' table THROUGH portal.py's SQL\n"
        "injection bug, then submit flag{...}.\n\n"
        "portal.py looks a customer up by username:\n"
        "    python3 portal.py alice        ->  alice\n\n"
        "THE KEY IDEA -- and the fix for 'I didn't really write any SQL':\n"
        "  It builds its SQL by gluing your argument into the query string. Pass\n"
        "  --show to WATCH that happen and see the exact statement YOU just wrote:\n\n"
        "      python3 portal.py --show alice\n"
        "      -- SQL that will run --\n"
        "      SELECT username FROM users WHERE username = 'alice'\n\n"
        "  Your argument landed between the quotes. Use --show on every step below:\n"
        "  you ARE writing SQL, through the argument, and --show proves it.\n\n"
        "WALK IT UP (two different injection FAMILIES, so you see the map, not 1 trick):\n\n"
        "  1. TAUTOLOGY  (the 'bypass a filter / login' family) -- make the WHERE\n"
        "     always true:\n"
        "         python3 portal.py --show \"' OR '1'='1\"\n"
        "     becomes:  ... WHERE username = '' OR '1'='1'   -> every row matches.\n"
        "     This PROVES your input runs as code. It's the root of auth-bypass bugs.\n\n"
        "  2. UNION  (the 'steal data from another table' family) -- the flag lives\n"
        "     in secrets(value), NOT users. Stitch a second SELECT on with UNION. It\n"
        "     must select ONE column (to match the first query's one column), and end\n"
        "     with  --  to comment out the trailing quote. Build it with --show so you\n"
        "     can read the exact statement you assembled; the flag prints as a 'username'.\n\n"
        "OTHER FAMILIES (named so you know they exist -- same root cause, input as code):\n"
        "  - BLIND / boolean: no data shown, so you ask yes/no questions and read the\n"
        "    answer from how the app behaves. ERROR-BASED: force a DB error that spills\n"
        "    data. STACKED: run a whole second statement where the driver allows it.\n"
        "  Master tautology + UNION first; the rest are variations on the same flaw.\n\n"
        "  3. CAPTURE:  elite lab submit app-01 flag{...}\n\n"
        "Stuck on step 2? `elite lab hint app-01` climbs to the exact argument.\n"
        "Want a clean slate?  elite lab restart app-01\n")


def setup_fix(workdir: Path):
    _build(workdir)
    (workdir / "START_HERE.txt").write_text(
        "Same portal.py, now you play defense. Edit portal.py so the injection from\n"
        "app-01 no longer leaks the secret, but a normal lookup (python3 portal.py alice)\n"
        "still returns alice. Hint: parameterize the query. Then submit the word FIXED\n"
        "and the checker will actually run your file to confirm the fix.\n")


def _run_portal(workdir: Path, arg: str) -> str:
    try:
        p = subprocess.run([sys.executable, str(workdir / "portal.py"), arg],
                           capture_output=True, text=True, timeout=20)
        return p.stdout + p.stderr
    except Exception as e:
        return f"(error: {e})"


def check_fix(workdir: Path, submitted: str) -> bool:
    flag = _flag()
    leaked = flag in _run_portal(workdir, INJECTION)              # must be False now
    taut = _run_portal(workdir, "x' OR '1'='1")                  # must not dump users
    dumps_users = sum(u in taut for u in USERNAMES) >= 2
    normal_ok = "alice" in _run_portal(workdir, "alice")         # normal lookup still works
    # Visible red-team check: show the learner exactly what we threw at their patch.
    def mark(bad):
        return "[STILL VULNERABLE]" if bad else "[blocked] ok"
    print("\n  Red-team check -- throwing the old attacks at your patched portal.py:")
    print(f"    1) UNION injection   \"{INJECTION}\"")
    print(f"         secret leaked?   {mark(leaked)}")
    print(f"    2) tautology         \"x' OR '1'='1\"")
    print(f"         dumped users?    {mark(dumps_users)}")
    print(f"    3) normal lookup     \"alice\"")
    print(f"         still works?     {'[works] ok' if normal_ok else '[BROKEN - fix went too far]'}")
    ok = (not leaked) and (not dumps_users) and normal_ok
    print(f"  Verdict: {'PASS - your fix holds against all three.' if ok else 'FAIL - see above.'}\n")
    return ok


MISSION = Mission(
    id="app-01",
    layer="3 The App",
    title="Break the portal (SQL injection)",
    difficulty="easy",
    goal="Use SQL injection against portal.py to read admin_flag from the secrets table. "
         "Submit flag{...}.",
    flag_format="flag{sqli_...}",
    setup=setup_break,
    solution=lambda wd: _flag(),
    tools=["sqlite3", "python3", "your brain"],
    hints=[
        "A normal run: python3 portal.py alice. Now break out of the quoted string - "
        "what does python3 portal.py \"' OR '1'='1\" return, and why?",
        "The query selects ONE column (username). A UNION SELECT with one column lets you "
        "append rows from another table. The secret lives in secrets(value).",
        "Try:  python3 portal.py \"' UNION SELECT value FROM secrets --\"  "
        "The -- comments out the trailing quote. The flag prints as a 'username'.",
    ],
    debrief=(
        "You just did SQL injection: because input was glued into the query, your data "
        "became CODE and crossed into a table you were never authorized to read. This is "
        "the single most important web+DB bug, and your SQL Server background makes the "
        "mechanics obvious. DEFENSE is next: run  elite lab start app-01-fix  and patch it."),
)

MISSION_FIX = Mission(
    id="app-01-fix",
    layer="3 The App",
    title="Fix the portal (parameterize)",
    difficulty="easy",
    goal="Edit portal.py so the injection fails but normal lookups still work, then submit FIXED.",
    flag_format="FIXED (after you patch portal.py)",
    setup=setup_fix,
    tools=["python3", "parameterized queries"],
    checker=check_fix,
    hints=[
        "The fix is NOT to blocklist words like UNION - attackers bypass that. Separate the "
        "code from the data.",
        "Use a parameter placeholder: sql = \"SELECT username FROM users WHERE username = ?\" "
        "and pass the input as a bound value: con.execute(sql, (term,)).",
        "With a bound parameter, the whole input is treated as one literal username - so "
        "\"' UNION SELECT ...\" matches no user and leaks nothing, while 'alice' still works.",
    ],
    debrief=(
        "That's the whole defense: parameterized queries keep user input as DATA, never SQL "
        "code, so there is nothing to inject. Same idea in SQL Server - use parameters "
        "(sp_executesql with @params, or your ORM's binding), never string concatenation. "
        "You broke it, then you built the fix and proved it holds."),
)

MISSIONS = [MISSION, MISSION_FIX]
