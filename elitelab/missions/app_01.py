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
term = sys.argv[1] if len(sys.argv) > 1 else ""

con = sqlite3.connect(DB)
# ---- VULNERABLE: user input concatenated straight into SQL ----
# Your job in app-01-fix is to make this query safe (parameterize it)
# WITHOUT breaking normal lookups.
sql = "SELECT username FROM users WHERE username = '" + term + "'"
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
        "portal.py looks up a customer by username against portal.db:\n"
        "    python3 portal.py alice\n"
        "It builds its SQL by gluing your input into the query string. There is a\n"
        "'secrets' table you were never meant to reach. Use a UNION-based SQL injection\n"
        "to read the admin_flag out of it, then submit flag{...}.\n")


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
    tautology = _run_portal(workdir, "x' OR '1'='1")             # must not dump users
    dumps_users = sum(u in tautology for u in USERNAMES) >= 2
    normal_ok = "alice" in _run_portal(workdir, "alice")         # normal lookup still works
    return (not leaked) and (not dumps_users) and normal_ok


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
