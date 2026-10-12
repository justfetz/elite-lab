#!/usr/bin/env python3
"""OrderDesk - Lakefront Paper & Container Co.'s customer portal.

*** TRAINING ONLY - INTENTIONALLY VULNERABLE. RUN LOCALLY (127.0.0.1) ONLY. ***
Never expose this on a public domain - it is broken on purpose. Each hole is
tagged [VULN] with the lesson and the tool you'd point at it.

Zero setup: seeds a local SQLite file mirroring the millops schema. The felt
mill theme and the "where's my order?" map are the product; the holes live
underneath it, the way they do in a real app.

    pip install flask
    python app.py        # http://127.0.0.1:5000

The map uses free OpenStreetMap tiles (no key). A legacy Google Maps key is
still [VULN]-leaked in the page source - the 'live-key' lesson.

WHERE TO POINT YOUR TOOLS (the CLI walks you through these in order):
    nmap    -> find the service        sqlmap -> /track?order=1000
    john    -> a hash from /debug/hashes   browser/curl -> IDOR on /orders/<id>
    view-source -> the leaked key in the page's JavaScript
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
app.secret_key = "dev-not-secret"

# [VULN] live-key: a real key would be referrer-restricted and server-side.
MAPS_API_KEY = "AIzaSyB-LakefrontDEMOkey-donotuse-0000000000"

# mill + customer-plant coordinates, for the delivery map
MILL = (41.889, -87.635)                      # Chicago river mill
CITY = {"Rockford": (42.271, -89.094), "Gary": (41.593, -87.346),
        "Milwaukee": (43.038, -87.911), "Chicago": MILL}
# how far along the route an order is, by status (for the truck marker)
PROGRESS = {"received": 0.0, "released": 0.33, "loaded": 0.6, "shipped": 0.96}
STATUS_CLASS = {"received": "wet", "released": "warn", "loaded": "kraft", "shipped": "felt"}


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
    # [VULN] crack-01: unsalted SHA-256. 'admin' is the weak one.
    con.executemany("INSERT INTO Users VALUES (?,?,?,?,?)", [
        (1, 1, "rockford_ap", sha256("autumn2024"), 0),
        (2, 1, "millops_admin", sha256("admin"), 1)])
    con.executemany("INSERT INTO Orders VALUES (?,?,?,?,?,?)", [
        (1000, 1, "26# kraft linerboard", 40, 48000, "received"),
        (1001, 2, "42# medium", 60, 51000, "released"),
        (1002, 1, "35# linerboard", 25, 30000, "loaded"),
        (1003, 3, "33# linerboard", 32, 38000, "shipped")])
    con.commit()
    con.close()


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>OrderDesk - Lakefront Paper</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600&family=Barlow+Condensed:wght@500;600&display=swap" rel="stylesheet">
{{ head|safe }}
<style>
:root{
  --bg:#E9EDEE;--panel:#F8FAFA;--ink:#18262B;--ink2:#4D5C61;--ink3:#7D8A8E;--line:#D3DADC;
  --felt:#2F6B5A;--felt-soft:#DCEAE4;--kraft:#9C7A4F;--kraft-soft:#EFE4D2;--wet:#2D6FA8;--wet-soft:#D8E6F2;
  --warn:#B67A10;--warn-soft:#F6E9CC;--bad:#B4402C;
  box-sizing:border-box;padding-top:env(safe-area-inset-top,0);padding-bottom:env(safe-area-inset-bottom,0);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#101719;--panel:#182226;--ink:#E4EBEC;--ink2:#A9B6B9;--ink3:#76868A;--line:#2A373B;
  --felt:#5DB394;--felt-soft:#1D3A31;--kraft:#C4A174;--kraft-soft:#312616;--wet:#6AA6DC;--wet-soft:#152A3B;
  --warn:#E3A93A;--warn-soft:#3A2E14;--bad:#E57560;}}
:root[data-theme="dark"]{
  --bg:#101719;--panel:#182226;--ink:#E4EBEC;--ink2:#A9B6B9;--ink3:#76868A;--line:#2A373B;
  --felt:#5DB394;--felt-soft:#1D3A31;--kraft:#C4A174;--kraft-soft:#312616;--wet:#6AA6DC;--wet-soft:#152A3B;
  --warn:#E3A93A;--warn-soft:#3A2E14;--bad:#E57560;}
*,*::before,*::after{box-sizing:inherit}
body{margin:0;background:var(--bg);color:var(--ink);font-family:"Barlow",system-ui,sans-serif}
header{background:var(--panel);border-bottom:3px solid var(--kraft);padding:14px 22px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
header h1{font-family:"Barlow Condensed",sans-serif;font-size:21px;margin:0;letter-spacing:.01em}
header .mark{color:var(--felt);font-size:22px}
header .sub{color:var(--ink3);font-size:13px} header .sp{flex:1}
.wrap{max-width:900px;margin:22px auto;padding:0 18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0}
.card h2{font-family:"Barlow Condensed",sans-serif;font-size:17px;margin:0 0 12px;letter-spacing:.02em}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:0 0 4px}
.tile{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.tile .n{font-family:"Barlow Condensed",sans-serif;font-size:26px;font-weight:600}
.tile .l{color:var(--ink3);font-size:12px;text-transform:uppercase;letter-spacing:.05em}
table{width:100%;border-collapse:collapse} th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--ink3);font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.pill{display:inline-block;font-size:12px;padding:2px 9px;border-radius:20px}
.pill.felt{background:var(--felt-soft);color:var(--felt)} .pill.kraft{background:var(--kraft-soft);color:var(--kraft)}
.pill.wet{background:var(--wet-soft);color:var(--wet)} .pill.warn{background:var(--warn-soft);color:var(--warn)}
input{padding:9px;border-radius:7px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font-family:inherit}
button{padding:9px 16px;border:0;border-radius:7px;background:var(--felt);color:#fff;font-weight:600;cursor:pointer;font-family:inherit}
a{color:var(--felt)} .muted{color:var(--ink3);font-size:13px}
#map{height:300px;border-radius:10px;border:1px solid var(--line);margin-top:6px}
</style></head><body>
<header><span class="mark">&#9608;</span>
  <h1>Lakefront Paper &amp; Container Co.</h1>
  <span class="sub">OrderDesk</span><span class="sp"></span>
  <span class="muted">{{ who }}</span></header>
<div class="wrap">{{ body|safe }}</div>
<!-- [VULN] live-key: legacy Google Maps key ships to every visitor in the source -->
<script>const MAPS_KEY = "{{ maps_key }}"; /* legacy delivery-map key */</script>
{{ tail|safe }}
</body></html>"""


def render(body, head="", tail="", who="not signed in"):
    return render_template_string(PAGE, body=body, head=head, tail=tail,
                                  who=who, maps_key=MAPS_API_KEY)


def _who():
    return f"signed in: {session['user']}" if "user" in session else \
           '<a href="/login">sign in</a>'


@app.route("/")
def dashboard():
    rows = db().execute("SELECT OrderId,CustomerId,PaperGrade,Rolls,WeightLbs,Status FROM Orders").fetchall()
    open_orders = sum(1 for r in rows if r["Status"] != "shipped")
    tons = sum(r["WeightLbs"] for r in rows) / 2000
    trs = ""
    for r in rows:
        cls = STATUS_CLASS.get(r["Status"], "wet")
        trs += (f"<tr><td><a href='/orders/{r['OrderId']}'>{r['OrderId']}</a></td>"
                f"<td>{r['PaperGrade']}</td><td>{r['Rolls']}</td>"
                f"<td>{r['WeightLbs']:,}</td>"
                f"<td><span class='pill {cls}'>{r['Status']}</span></td></tr>")
    body = f"""
      <div class="card"><h2>Mill dashboard</h2>
        <div class="tiles">
          <div class="tile"><div class="n">{open_orders}</div><div class="l">Open orders</div></div>
          <div class="tile"><div class="n">{tons:.0f}</div><div class="l">Tons in play</div></div>
          <div class="tile"><div class="n">200&Prime;</div><div class="l">Parent reel</div></div>
          <div class="tile"><div class="n">3</div><div class="l">Plants served</div></div>
        </div>
        <p class="muted">Chicago mill &rarr; corrugator plants. Trucks loaded by weight.</p>
        <table><tr><th>Order</th><th>Grade</th><th>Rolls</th><th>Weight (lbs)</th><th>Status</th></tr>
        {trs}</table></div>
      <div class="card"><h2>Track an order</h2>
        <form action="/track"><input name="order" placeholder="order #, e.g. 1000">
        <button>Track</button></form></div>"""
    return render(body, who=_who())


@app.route("/track")
def track():
    order = request.args.get("order", "")
    # [VULN] live-sqli: order number concatenated straight into SQL.
    #   sqlmap -u "http://127.0.0.1:5000/track?order=1000"
    q = f"SELECT OrderId,PaperGrade,Status FROM Orders WHERE OrderId = {order or 0}"
    try:
        rows = db().execute(q).fetchall()
    except Exception as e:
        return render(f"<div class='card'><h2>Tracking</h2>Query error: {e}</div>", who=_who())
    trs = "".join(f"<tr><td>{r['OrderId']}</td><td>{r['PaperGrade']}</td>"
                  f"<td><span class='pill {STATUS_CLASS.get(r['Status'],'wet')}'>{r['Status']}</span></td></tr>"
                  for r in rows) or "<tr><td colspan=3 class='muted'>no match</td></tr>"
    return render(f"<div class='card'><h2>Tracking &lsquo;{order}&rsquo;</h2><table>"
                  f"<tr><th>Order</th><th>Grade</th><th>Status</th></tr>{trs}</table>"
                  f"<p class='muted'><a href='/'>&larr; back</a></p></div>", who=_who())


LEAFLET_HEAD = ('<link rel="stylesheet" '
                'href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">')
LEAFLET_JS = ('<script '
              'src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>')


@app.route("/orders/<int:oid>")
def order_detail(oid):
    # [VULN] live-idor: no check this order belongs to the signed-in plant.
    r = db().execute("SELECT * FROM Orders WHERE OrderId=?", (oid,)).fetchone()
    if not r:
        return render("<div class='card'><h2>Not found</h2>No such order.</div>", who=_who())
    cust = db().execute("SELECT PlantName,City FROM Customers WHERE CustomerId=?",
                        (r["CustomerId"],)).fetchone()
    city = cust["City"] if cust else "Chicago"
    dest = CITY.get(city, MILL)
    frac = PROGRESS.get(r["Status"], 0.0)
    truck = (MILL[0] + (dest[0] - MILL[0]) * frac, MILL[1] + (dest[1] - MILL[1]) * frac)
    cls = STATUS_CLASS.get(r["Status"], "wet")
    body = f"""
      <div class="card"><h2>Order {r['OrderId']} &mdash; where's my order?</h2>
        <p>{cust['PlantName'] if cust else 'Plant'} &middot; {r['PaperGrade']} &middot;
           {r['Rolls']} rolls &middot; {r['WeightLbs']:,} lbs &middot;
           <span class="pill {cls}">{r['Status']}</span></p>
        <div id="map"></div>
        <p class="muted">Chicago mill &rarr; {city}. Truck position reflects order status.
           &nbsp;<a href="/">&larr; back</a></p></div>"""
    tail = LEAFLET_JS + f"""<script>
      const mill={list(MILL)}, dest={list(dest)}, truck={list(truck)};
      const map=L.map('map').setView([{(MILL[0]+dest[0])/2},{(MILL[1]+dest[1])/2}],7);
      L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
        {{maxZoom:18, attribution:'&copy; OpenStreetMap'}}).addTo(map);
      L.marker(mill).addTo(map).bindPopup('Lakefront mill - Chicago');
      L.marker(dest).addTo(map).bindPopup('{city} - {cust['PlantName'] if cust else ''}');
      L.polyline([mill,dest],{{color:'#9C7A4F',dashArray:'6,8'}}).addTo(map);
      L.circleMarker(truck,{{radius:9,color:'#2F6B5A',fillColor:'#2F6B5A',fillOpacity:1}})
        .addTo(map).bindPopup('your load - {r['Status']}');
    </script>"""
    return render(body, head=LEAFLET_HEAD, tail=tail, who=_who())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        row = db().execute("SELECT PwHash FROM Users WHERE Username=?", (u,)).fetchone()
        if row and row["PwHash"] == sha256(p):
            session["user"] = u
            return redirect("/")
        return render("<div class='card'><h2>Sign in</h2>Bad credentials. "
                      "<a href='/login'>try again</a></div>", who=_who())
    return render("""<div class="card"><h2>Sign in</h2>
      <form method="post">
        <p><input name="username" placeholder="username"></p>
        <p><input name="password" type="password" placeholder="password"></p>
        <button>Sign in</button></form></div>""", who=_who())


@app.route("/debug/hashes")
def debug_hashes():
    # stand-in for "you dumped these" - feed to John:  elite run john
    rows = db().execute("SELECT Username,PwHash FROM Users").fetchall()
    return "<pre>" + "\n".join(f"{r['Username']}:{r['PwHash']}" for r in rows) + "</pre>"


if __name__ == "__main__":
    if not DB.exists():
        seed()
        print(f"seeded {DB.name}")
    print("OrderDesk on http://127.0.0.1:5000  (local only; Ctrl-C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)
