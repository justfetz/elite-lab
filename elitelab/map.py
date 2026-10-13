"""`elite map` - the territory. The mental model the missions hang on: what the
company IS, its attack surface, and how each layer, learn-module, and mission
connect. Answers "what am I defending and how does it all relate?" """
from .missions import load_missions

# Curated per-layer: what the layer is AT LAKEFRONT, and which module teaches it.
# Mission ids are filled in dynamically so this stays in sync with the code.
LAYERS = [
    ("1 The Wire",  "network traffic + the logs",          "networking"),
    ("2 The Door",  "portal logins + password hashes",      "security"),
    ("3 The App",   "OrderDesk portal -> millops DB",       "web-vulns"),
    ("4 The Host",  "one machine: reverse + escalate",      "linux"),
    ("5 The Domain", "the Windows Active Directory",        "windows-ps"),
    ("AI product",  "Millie, the AI order agent",           "threat-modeling"),
    ("6 The Hunt",  "spotting all of it in the logs",       "web-vulns"),
]


def status_map(args=None):
    missions = load_missions()
    by_layer = {}
    for mid, m in missions.items():
        by_layer.setdefault(m.layer, []).append(mid)

    print("\n  THE TERRITORY -- Lakefront Paper & Container Co.\n")
    print("  WHAT THE COMPANY IS")
    print("    A Chicago paper mill. It takes orders from corrugator plants, makes the")
    print("    product, loads trucks by weight, and ships. It has two faces:")
    print("      OrderDesk   - the PUBLIC customer portal  (where an attacker knocks)")
    print("      PM3 / mill  - the INTERNAL process floor   (the crown jewel: if it")
    print("                    stops, the company bleeds money - that's ransom leverage)")
    print("    Underneath: millops (a SQL Server database) and Millie (an AI order agent).")
    print("    YOU are the security team. Find and fix every way in, before someone else does.\n")

    print("  HOW IT ALL CONNECTS   (layer  ->  what it is here  ->  learn it  ->  prove it)\n")
    print(f"    {'LAYER':<13}{'AT LAKEFRONT':<34}{'LEARN':<16}MISSIONS")
    for layer, what, learn in LAYERS:
        mids = by_layer.get(layer, [])
        mstr = ", ".join(mids) if mids else "(hunt across all)"
        print(f"    {layer:<13}{what:<34}{learn:<16}{mstr}")

    print("\n  THE LOOP  (how you work ANY surface)")
    print("    threat-model  ->  recon  ->  exploit (prove it)  ->  fix  ->  hunt (detect it)")
    print("    Break it to understand the risk; fix it to learn the defense. Both halves matter.\n")

    print("  SEE THE REAL THING")
    print("    live-lab/  is the company running for real: OrderDesk (the portal + mill")
    print("    dashboard) and millops. Host it locally and point real tools at it.\n")

    print("  WHERE TO GO")
    print("    elite status   where you are, your next move")
    print("    elite path     the ordered campaign through every layer")
    print("    elite learn <topic>    read a module     elite lab start <id>   do a mission\n")
