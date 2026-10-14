"""`elite map` - the territory. The mental model the missions hang on: what the
company IS, how it's segmented into trust zones, and which mission lives where.

The whole map is DERIVED from the world registry (elitelab/world.py): the zones,
the systems in each, and the exercises on each system. Nothing here is hand-kept.
"""
from . import progress, world
from .missions import load_missions


def status_map(args=None):
    missions = load_missions()

    print("\n  THE TERRITORY -- Lakefront Paper & Container Co.\n")
    print("  WHAT THE COMPANY IS")
    print("    A Chicago paper mill. It takes orders from corrugator plants, makes the")
    print("    product, loads trucks by weight, and ships. It has two faces that must NOT")
    print("    freely touch:")
    print("      the BUSINESS side  - the public portal + the AI agent (where attackers knock)")
    print("      the PLANT floor    - PM3 and the mill (the crown jewel: if it stops, the")
    print("                           company bleeds money - that's ransom leverage)")
    print("    Between them sits ONE controlled conduit. The cardinal sin of industrial")
    print("    security is letting the business network reach the floor; the whole map is")
    print("    built to show -- and defend -- that boundary.\n")

    print("  THE ZONES   (trust world  ->  what's in it  ->  the missions there)\n")
    for z in world.zones():
        print(f"    [{z.name}]   ({z.trust})")
        for s in world.systems_in(z.id):
            addr = f"{s.addr:<11}" if s.addr else f"{'':<11}"
            print(f"      {addr}{s.name}")
            print(f"                 {s.blurb}")
            ex = world.exercises_on(s.id)
            if ex:
                parts = []
                for e in ex:
                    mark = "x" if progress.lab_state(e.mission)["solved"] else " "
                    parts.append(f"[{mark}] {e.mission}")
                print(f"                 missions: " + "  ".join(parts))
        print()

    print("  THE LOOP  (how you work ANY system)")
    print("    threat-model  ->  recon  ->  break (prove it)  ->  fix (keep it working)  ->")
    print("    detect (catch it in the logs). Break to understand the risk; fix to learn the")
    print("    defense; detect to catch the next one. All three matter.\n")

    print("  SEE THE REAL THING")
    print("    live-lab/  is the company running for real: OrderDesk (portal + PM3 dashboard),")
    print("    LoadMaster (the optimizer), and the millops schema. Host it locally.\n")

    print("  WHERE TO GO")
    print("    elite status     where you are, your next move")
    print("    elite path       the ordered campaign through every zone")
    print("    elite scenario   the incident chains (break -> detect -> fix, end to end)")
    print("    elite engage     the open engagement board + loot chain")
    print("    elite learn <topic>    read a module     elite lab start <id>   do a mission\n")
