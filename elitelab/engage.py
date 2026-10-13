"""`elite engage` - the connected Lakefront engagement (open sandbox + loot chaining).

Recon reveals the whole company surface. Each target maps to a mission you already have;
solving it yields LOOT, and a few deeper targets stay locked until you hold the loot that
reaches them (web app -> DB service credential -> Domain Admin). State is DERIVED from your
lab progress, so it stays in sync with everything else automatically.
"""
from . import progress
from .missions import load_missions

# Each target reuses an existing mission. requires = loot ids; satisfied if you hold ANY.
ENGAGEMENT = [
    {"id": "portal-sqli", "area": "Customer Portal  (web, 10.10.0.20)", "mission": "app-01",
     "desc": "order lookup looks injectable", "grants": ["db_service_cred"], "requires": []},
    {"id": "portal-idor", "area": "Customer Portal  (web, 10.10.0.20)", "mission": "idor-01",
     "desc": "order pages use sequential IDs", "grants": ["customer_pii"], "requires": []},
    {"id": "portal-sqli-fix", "area": "Customer Portal  (web, 10.10.0.20)", "mission": "app-01-fix",
     "desc": "BLUE: parameterize the query", "grants": ["hardened_sqli"], "requires": ["db_service_cred"]},
    {"id": "portal-idor-fix", "area": "Customer Portal  (web, 10.10.0.20)", "mission": "idor-01-fix",
     "desc": "BLUE: enforce ownership checks", "grants": ["hardened_idor"], "requires": ["customer_pii"]},
    {"id": "ws01-dump", "area": "Workstation ws01  (10.10.0.31)", "mission": "crack-01",
     "desc": "a leaked password-hash dump", "grants": ["domain_user_cred"], "requires": []},
    {"id": "ws01-priv", "area": "Workstation ws01  (10.10.0.31)", "mission": "priv-01",
     "desc": "low-priv shell; a sudo/SUID misconfig may give root", "grants": ["root_ws01"], "requires": []},
    {"id": "ws01-bin", "area": "Workstation ws01  (10.10.0.31)", "mission": "bin-01",
     "desc": "a licensed tool guarding a key (needs local access)", "grants": ["license_key"],
     "requires": ["root_ws01"]},
    {"id": "dc-path", "area": "Domain Controller dc01  (10.10.0.10)", "mission": "domain-01",
     "desc": "map a path to Domain Admin -- needs a domain foothold", "grants": ["domain_admin"],
     "requires": ["domain_user_cred", "db_service_cred"]},
    {"id": "dc-fix", "area": "Domain Controller dc01  (10.10.0.10)", "mission": "domain-01-fix",
     "desc": "BLUE: cut the path to DA", "grants": ["hardened_ad"], "requires": ["domain_admin"]},
    {"id": "agent-inject", "area": "Millie, the AI order agent  (10.10.0.50)", "mission": "ai-01",
     "desc": "the RAG product; retrieves customer documents", "grants": ["admin_api_key"], "requires": []},
    {"id": "agent-fix", "area": "Millie, the AI order agent  (10.10.0.50)", "mission": "ai-01-fix",
     "desc": "BLUE: stop the injection", "grants": ["hardened_agent"], "requires": ["admin_api_key"]},
    {"id": "soc-hunt", "area": "SOC / log pipeline", "mission": "hunt-01",
     "desc": "auth + process logs from the breach", "grants": ["incident_report"], "requires": []},
]
TOOLKIT = ["build-01", "build-02", "build-03", "build-04"]

RECON_TEXT = """\
Recon complete. Lakefront Paper's surface:

  10.10.0.10  dc01      Active Directory domain controller (the crown jewels)
  10.10.0.20  app01     Customer Portal - public web app on SQL Server
  10.10.0.31  ws01      an employee workstation
  10.10.0.50  agent01   Millie, the AI order agent (RAG)
              soc       log pipeline (auth + process telemetry)

Everything is open - hit it in any order. But the deepest targets need loot you only get
by breaking something else first (the web app leaks a credential that is also a domain
account; local root on ws01 lets you reach the licensed binary). Chase the chain.
"""


def _loot(solved):
    loot = set()
    for t in ENGAGEMENT:
        if t["mission"] in solved:
            loot.update(t["grants"])
    return loot


def _status(t, solved, loot):
    if t["mission"] in solved:
        return "done"
    if t["requires"] and not (set(t["requires"]) & loot):
        return "locked"
    return "open"


def _reconned():
    return progress.load().get("engagement", {}).get("reconned", False)


def engage(args):
    action = getattr(args, "engage_action", None)
    if action == "recon":
        p = progress.load()
        p.setdefault("engagement", {})["reconned"] = True
        progress.save(p)
        print("\n" + RECON_TEXT)
        print("See your targets:  elite engage\n")
        return

    missions = load_missions()
    solved = {mid for mid in missions if progress.lab_state(mid)["solved"]}
    if not _reconned():
        print("\nYou've been hired to assess Lakefront Paper. Start by mapping the surface:\n"
              "  elite engage recon\n")
        return

    loot = _loot(solved)
    done = sum(1 for t in ENGAGEMENT if t["mission"] in solved)
    print(f"\nLakefront Paper - engagement   ({done}/{len(ENGAGEMENT)} targets cleared)")
    print("Loot: " + (", ".join(sorted(loot)) if loot else "(none yet)") + "\n")

    area = None
    marks = {"done": "[x]", "open": "[>]", "locked": "[#]"}
    for t in ENGAGEMENT:
        if t["area"] != area:
            area = t["area"]
            print(f"  {area}")
        st = _status(t, solved, loot)
        print(f"    {marks[st]} {t['mission']:<13} {t['desc']}")
        if st == "open":
            m = missions.get(t["mission"])
            goal = (m.goal.split(". ")[0] if m else "")[:88]
            print(f"          goal: {goal}")
            print(f"          ->    elite lab start {t['mission']}")
        elif st == "locked":
            print(f"          locked - need: " + " or ".join(t["requires"]))

    openset = [t for t in ENGAGEMENT if _status(t, solved, loot) == "open"]
    print("\n  Your toolkit (build these any time): " + ", ".join(TOOLKIT))
    if openset:
        print(f"\nAvailable now: {', '.join(t['mission'] for t in openset[:4])}"
              f"{' ...' if len(openset) > 4 else ''}")
        print(f"Go:  elite lab start {openset[0]['mission']}\n")
    elif done == len(ENGAGEMENT):
        print("\nEvery target cleared and every break hardened. You assessed the whole company. "
              "That's the job.\n")
    else:
        print("\nEverything available is done - clear a dependency to unlock the locked targets.\n")
