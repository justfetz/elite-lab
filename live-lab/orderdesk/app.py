#!/usr/bin/env python3
"""OrderDesk - Lakefront Paper & Container Co.'s customer portal.

*** TRAINING ONLY - INTENTIONALLY VULNERABLE ***
A deliberately insecure web app you host on your OWN machine to practice against.
Each hole is tagged [VULN] with the lesson and the tool you'd point at it.

Runs with zero database setup: it seeds a local SQLite file that mirrors the
millops schema, so you can start immediately. (The SQL Server version in
../db/schema.sql is the "real" backend you graduate to.)

    pip install flask
    python app.py
    # then open http://127.0.0.1:5000

WHERE TO POINT YOUR TOOLS (the CLI will walk you through these in order):
    nmap     -> find the service:   elite run nmap 127.0.0.1
    john     -> crack a login hash you pull from the DB (see /debug/hashes)
    sqlmap   -> the order tracker:  http://127.0.0.1:5000/track?order=1000
    curl/browser -> IDOR:           http://127.0.0.1:5000/orders/1001
    view-source  -> leaked API key in the dashboard's JavaScript
"""
import hashlib
import sqlite3
from pathlib import Path

try:
    from flask import Flask, request, g, redirect, session, render_template_string
except ImportError:
    raise SystemExit("OrderDesk needs Flask:  pip install flask")

DB = Path(__file__).with_name("orderdesk.db")
app = Flask(__name__)
app.secret_key = "dev-not-secret"  # fine for a local lab

# [VULN] a real Google Maps key would be restricted by referrer and scoped.
# This one is embedded in client JS unrestricted - the 'live-key' lesson.
MAPS_API_KEY = "AIzaSyB-LakefrontDEMOkey-donotuse-0000000000"


def sha256(s):
    return hashlib.sha256(s.encode()).hexdigest()


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_):
    d = g.pop("db", None)
    if d:
        d.close()


def seed():
    con = sqlite3.connect(DB)
    con.executescript("""
        DROP TABLE IF EXISTS Customers; DROP TABLE IF EXISTS Users; DROP TABLE IF EXISTS Orders;
        CREATE TABLE Customers (CustomerId INTEGER PRIMARY KEY, PlantName TEXT, City TEXT);
        CREATE TABLE Users (UserId INTEGER PRIMARY KEY, CustomerId INT, Username TEXT, PwHash TEXT, IsAdmin INT);
        CREATE TABLE Orders (OrderId INTEGER PRIMARY KEY, CustomerId INT, PaperGrade TEXT, Rolls INT, WeightLbs INT, Status TEXT);
    """)
    con.executemany("INSERT INTO Customers VALUES (?,?,?)", [
        (1, "Rockford Corrugated", "Rockford"),
        (2, "Gary Container Works", "Gary"),
        (3, "Milwaukee Box Co", "Milwaukee")])
    # [VULN] unsalted SHA-256 - crack-01's lesson. 'admin' is the weak one.
    con.executemany("INSERT INTO Users VALUES (?,?,?,?,?)", [
        (1, 1, "rockford_ap", sha256("autumn2024"), 0),
        (2, 1, "millops_admin", sha256("admin"), 1)])
    con.executemany("INSERT INTO Orders VALUES (?,?,?,?,?,?)", [
        (1000, 1, "26# kraft linerboard", 40, 48000, "received"),
        (1001, 2, "42# medium", 60, 51000, "released"),      # belongs to Gary, not Rockford
        (1002, 1, "35# linerboard", 25, 30000, "shipped")])
    con.commit()
    con.close()


PAGE = """<!doctype html><html><head><title>OrderDesk - Lakefront Paper</title>
<style>
 body{font-family:system-ui,sans-serif;margin:0;background:#0f1720;color:#e8eef5}
 header{background:#16222e;padding:14px 22px;border-bottom:3px solid #d98c2b}
 header b{color:#d98c2b;font-size:19px} .wrap{max-width:860px;margin:24px auto;padding:0 18px}
 .card{background:#16222e;border:1px solid #24323f;border-radius:10px;padding:18px;margin:14px 0}
 table{width:100%;border-collapse:collapse} th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #24323f}
 th{color:#9fb3c8;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
 input{padding:8px;border-radius:6px;border:1px solid #33475a;background:#0f1720;color:#e8eef5}
 button{padding:8px 14px;border:0;border-radius:6px;background:#d98c2b;color:#1a1200;font-weight:600;cursor:pointer}
 a{color:#d98c2b} .muted{color:#9fb3c8;font-size:13px}
</style></head><body>
<header><b>&#9608; Lakefront Paper &amp; Container Co.</b> &nbsp;<span class="muted">OrderDesk portal</span></header>
<div class="wrap">{{ body|safe }}</div>
<!-- [VULN] live-key: the maps key ships to every visitor in the page source -->
<script>const MAPS_KEY = "{{ maps_key }}"; /* used to draw the delivery map */</script>
</body></html>"""


def render(body):
    return render_template_string(PAGE, body=body, maps_key=MAPS_API_KEY)


@app.route("/")
def dashboard():
    who = session.get("user", "guest")
    rows = db().execute("SELECT OrderId,PaperGrade,Rolls,WeightLbs,Status FROM Orders").fetchall()
    trs = "".join(f"<tr><td><a href='/orders/{r['OrderId']}'>{r['OrderId']}</a></td>"
                  f"<td>{r['PaperGrade']}</td><td>{r['Rolls']}</td>"
                  f"<td>{r['WeightLbs']:,}</td><td>{r['Status']}</td></tr>" for r in rows)
    body = f"""
      <div class="card"><b>Mill dashboard</b> &mdash; logged in as <b>{who}</b>
        &nbsp;<span class="muted">(<a href="/login">log in</a>)</span>
        <p class="muted">Chicago mill &rarr; corrugator plants. Trucks loaded by weight.</p>
        <table><tr><th>Order</th><th>Grade</th><th>Rolls</th><th>Weight (lbs)</th><th>Status</th></tr>
        {trs}</table></div>
      <div class="card"><b>Track an order</b>
        <form action="/track"><input name="order" placeholder="order #, e.g. 1000">
        <button>Track</button></form></div>"""
    return render(body)


@app.route("/track")
def track():
    order = request.args.get("order", "")
    # [VULN] live-sqli: the order number is concatenated straight into SQL.
    #   point sqlmap here:  sqlmap -u "http://127.0.0.1:5000/track?order=1000"
    #   or by hand:  /track?order=1000 OR 1=1   returns every plant's orders.
    q = f"SELECT OrderId,PaperGrade,Status FROM Orders WHERE OrderId = {order or 0}"
    try:
        rows = db().execute(q).fetchall()
    except Exception as e:
        return render(f"<div class='card'>Query error: {e}</div>")
    trs = "".join(f"<tr><td>{r['OrderId']}</td><td>{r['PaperGrade']}</td><td>{r['Status']}</td></tr>"
                  for r in rows) or "<tr><td colspan=3 class='muted'>no match</td></tr>"
    return render(f"<div class='card'><b>Tracking '{order}'</b><table>"
                  f"<tr><th>Order</th><th>Grade</th><th>Status</th></tr>{trs}</table>"
                  f"<p class='muted'><a href='/'>&larr; back</a></p></div>")


@app.route("/orders/<int:oid>")
def order_detail(oid):
    # [VULN] live-idor: no check that this order belongs to the logged-in plant.
    #   anyone can walk IDs:  /orders/1000, /orders/1001 (another customer's)
    r = db().execute("SELECT * FROM Orders WHERE OrderId=?", (oid,)).fetchone()
    if not r:
        return render("<div class='card'>No such order.</div>")
    return render(f"<div class='card'><b>Order {r['OrderId']}</b>"
                  f"<p>Plant #{r['CustomerId']} &middot; {r['PaperGrade']} &middot; "
                  f"{r['Rolls']} rolls &middot; {r['WeightLbs']:,} lbs &middot; {r['Status']}</p>"
                  f"<p class='muted'><a href='/'>&larr; back</a></p></div>")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        row = db().execute("SELECT PwHash FROM Users WHERE Username=?", (u,)).fetchone()
        if row and row["PwHash"] == sha256(p):
            session["user"] = u
            return redirect("/")
        return render("<div class='card'>Bad credentials. <a href='/login'>try again</a></div>")
    return render("""<div class="card"><b>Log in</b>
      <form method="post">
        <p><input name="username" placeholder="username"></p>
        <p><input name="password" type="password" placeholder="password"></p>
        <button>Log in</button></form></div>""")


@app.route("/debug/hashes")
def debug_hashes():
    # Stand-in for "you pulled these via the SQLi / a DB dump." Feed to John:
    #   elite run john  (or: john --format=raw-sha256 hashes.txt)
    rows = db().execute("SELECT Username,PwHash FROM Users").fetchall()
    return "<pre>" + "\n".join(f"{r['Username']}:{r['PwHash']}" for r in rows) + "</pre>"


if __name__ == "__main__":
    if not DB.exists():
        seed()
        print(f"seeded {DB.name}")
    print("OrderDesk on http://127.0.0.1:5000  (Ctrl-C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)
