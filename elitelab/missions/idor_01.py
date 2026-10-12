"""Missions idor-01 (attack) and idor-01-fix (defend): Insecure Direct Object Reference
(Layer 3 - The App). The #1 bug-bounty bug: the app authenticates you but never checks
you're AUTHORIZED for the object whose ID you asked for.
"""
import hashlib
import sys
import subprocess
from pathlib import Path

from .base import Mission

SEED = 0x1D0A
FLAG = "flag{idor_" + hashlib.sha1(str(SEED).encode()).hexdigest()[:8] + "}"
ADMIN_ORDER = 1003

ORDERS_SRC = '''#!/usr/bin/env python3
"""Customer order lookup. You are logged in as the session user passed as arg 1."""
import os, sqlite3, sys

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orders.db")
session_user = sys.argv[1] if len(sys.argv) > 1 else "alice"
order_id = sys.argv[2] if len(sys.argv) > 2 else ""

con = sqlite3.connect(DB)
row = con.execute("SELECT owner, item, note FROM orders WHERE id = ?", (order_id,)).fetchone()
# VULNERABLE: looks up the order by id but never checks it belongs to session_user.
if row:
    print("Order %s | owner=%s | item=%s | note=%s" % (order_id, row[0], row[1], row[2]))
else:
    print("No such order.")
'''


def _build(workdir: Path):
    import sqlite3
    (workdir / "orders.py").write_text(ORDERS_SRC)
    dbp = workdir / "orders.db"
    if dbp.exists():
        dbp.unlink()
    con = sqlite3.connect(dbp)
    con.execute("CREATE TABLE orders(id INTEGER, owner TEXT, item TEXT, note TEXT)")
    con.executemany("INSERT INTO orders VALUES(?,?,?,?)", [
        (1001, "alice", "Keyboard", "deliver Tuesday"),
        (1002, "alice", "Monitor", "gift wrap"),
        (ADMIN_ORDER, "admin", "Server", FLAG),      # not alice's - the target
        (1004, "bob", "Mouse", "no rush"),
    ])
    con.commit()
    con.close()


def setup_attack(workdir: Path):
    _build(workdir)
    (workdir / "START_HERE.txt").write_text(
        "You are logged in as 'alice'. Look up your orders:\n"
        "    python3 orders.py alice 1001\n"
        "Your orders are 1001 and 1002. But the app only checks that you're logged in, not that\n"
        "the order is yours. There's an admin order whose note holds a flag. Access it as alice\n"
        "and submit the flag. (Hint: try other nearby order IDs.)\n")


def setup_fix(workdir: Path):
    _build(workdir)
    (workdir / "START_HERE.txt").write_text(
        "Same app. Fix orders.py so a user can only see THEIR OWN orders: alice must still read\n"
        "order 1001, but must NOT be able to read the admin order " + str(ADMIN_ORDER) + ".\n"
        "Then submit FIXED; the checker runs your app both ways to confirm.\n")


def _run(workdir, user, oid):
    try:
        p = subprocess.run([sys.executable, str(workdir / "orders.py"), user, str(oid)],
                           capture_output=True, text=True, timeout=20)
        return p.stdout + p.stderr
    except Exception as e:
        return f"(error: {e})"


def check_fix(workdir: Path, submitted: str) -> bool:
    leaked = FLAG in _run(workdir, "alice", ADMIN_ORDER)      # must be blocked now
    own_ok = "Keyboard" in _run(workdir, "alice", 1001)        # her own still works
    return (not leaked) and own_ok


MISSION = Mission(
    id="idor-01",
    layer="3 The App",
    title="Break access control (IDOR)",
    difficulty="easy",
    goal="As alice, read the admin order's note via IDOR and submit the flag inside it.",
    flag_format="flag{idor_...}",
    setup=setup_attack,
    solution=lambda wd: FLAG,
    tools=["python3", "curiosity"],
    hints=[
        "Your orders are 1001 and 1002. The app fetches whatever id you ask for. What's at 1003?",
        "Run: python3 orders.py alice 1003 - the app never checks the order is yours.",
        "The note field of that order is the flag. That's IDOR: authenticated, but not authorized.",
    ],
    debrief=(
        "IDOR: the server knew WHO you are but never checked you were allowed to see THAT object. "
        "It's the most common serious web bug because it hides in normal-looking features. DEFENSE "
        "next (idor-01-fix): check ownership on every object access. Your DB background makes the "
        "fix obvious - scope the query to the current user."),
)

MISSION_FIX = Mission(
    id="idor-01-fix",
    layer="3 The App",
    title="Enforce access control",
    difficulty="easy",
    goal="Fix orders.py so alice can read her own orders but not others', then submit FIXED.",
    flag_format="FIXED (after you add the ownership check)",
    setup=setup_fix,
    checker=check_fix,
    tools=["python3"],
    hints=[
        "The bug: the query finds an order by id but ignores who owns it. Tie the lookup to the "
        "session user.",
        "Add owner to the WHERE clause: SELECT ... FROM orders WHERE id = ? AND owner = ?, and "
        "pass (order_id, session_user). Now a mismatched owner returns nothing.",
        "After the fix: alice 1001 still shows her order; alice 1003 returns 'No such order.' "
        "because that row's owner is admin, not alice.",
    ],
    debrief=(
        "That's authorization done right: every object access is scoped to the current user, "
        "server-side. The same rule applies everywhere - APIs, file downloads, report IDs: never "
        "trust that an ID the user supplied is one they're allowed to see. Check ownership, always."),
)

MISSIONS = [MISSION, MISSION_FIX]
