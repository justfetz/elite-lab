"""The world registry -- the SINGLE source of truth for Lakefront.

Everything the learner sees (the map, the campaign path, the engagement board,
the scenarios) is DERIVED from the four tables below. Add an exercise in ONE
place -- an Exercise record in EXERCISES -- and it appears on the map (by its
zone), in the campaign (by its list position), on the engagement board (if it
has a network `system`), and in any scenario that lists it. No more editing five
files and forgetting one; validate() fails the test suite if anything drifts.

The spine is the IT/OT topology from real industrial security: three trust
worlds that must not freely touch, joined by one controlled conduit.

  ZONES    the trust worlds (IT business / IT corporate / DMZ conduit / OT floor / People)
  SYSTEMS  the things on the network, each placed in exactly one zone
  EXERCISES one record per mission: where it lives, what skill it teaches, how it
           chains (requires/grants loot), and -- new -- the business invariant it
           must not break and the evidence it emits (for detection/forensics)
  SCENARIOS ordered chains of exercises around one incident, held together by the
           business question "can Lakefront keep producing and shipping?"
"""
from dataclasses import dataclass, field
from typing import List

# ---------------------------------------------------------------------------
# vocabulary (kept small and ordered so views can sort by it)
# ---------------------------------------------------------------------------
# the rungs a single business system can be climbed through -- depth without reskins
LEVELS = ["intro", "toolkit", "guided", "implementation",
          "stateful", "operational", "investigation", "recovery"]
# the four things you ever do to a system. `detect` is the connective tissue that
# turns isolated exercises into campaigns: something broke -> find it -> fix it.
VERBS = ["recon", "build", "break", "fix", "detect"]


@dataclass(frozen=True)
class Zone:
    id: str
    name: str
    trust: str          # one-word posture: public / internal / conduit / isolated / human
    blurb: str


@dataclass(frozen=True)
class System:
    id: str
    zone: str           # Zone.id
    name: str
    addr: str           # network locator ("" if not a host on the wire)
    blurb: str


@dataclass(frozen=True)
class Exercise:
    mission: str                     # the Mission.id this record points at
    system: str                      # System.id it lives on
    skill: str                       # the one skill it teaches (the engage-board desc)
    level: str                       # one of LEVELS
    verb: str                        # one of VERBS
    requires: List[str] = field(default_factory=list)   # loot ids needed to reach it
    grants: List[str] = field(default_factory=list)     # loot ids solving it yields
    invariant: str = ""              # business function that must STILL work after a fix
    emits: List[str] = field(default_factory=list)      # evidence artifacts (for detect)
    board: bool = True               # show on the engagement board (a live network target)


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    question: str                    # the business invariant the whole chain defends
    narrative: str
    steps: List[str]                 # ordered Mission.ids (break -> detect -> fix -> ...)


# ---------------------------------------------------------------------------
# 1) ZONES -- the trust worlds
# ---------------------------------------------------------------------------
ZONES = [
    Zone("it_public", "IT / Business (public)", "public",
         "The internet-facing side: the customer portal and the AI order agent. "
         "Where an outsider knocks first."),
    Zone("it_corp", "IT / Corporate (internal)", "internal",
         "The office network: Active Directory, employee workstations, the SOC. "
         "Reached after a foothold, not from the street."),
    Zone("dmz", "DMZ / Conduit", "conduit",
         "The one controlled chokepoint between business and plant. Orders cross "
         "HERE, one direction only, and nothing reaches back."),
    Zone("ot", "OT / Plant floor", "isolated",
         "The mill itself: the release agent, PM3, the optimizer. No internet path. "
         "If it stops, the company bleeds money."),
    Zone("people", "People", "human",
         "The human layer -- email and trust. The #1 way in, and no firewall covers it."),
]

# ---------------------------------------------------------------------------
# 2) SYSTEMS -- placed in exactly one zone
# ---------------------------------------------------------------------------
SYSTEMS = [
    System("orderdesk", "it_public", "Customer Portal", "10.10.0.20",
           "Public web app (OrderDesk) over the millops SQL Server."),
    System("millie", "it_public", "Millie, the AI order agent", "10.10.0.50",
           "RAG agent that reads customer documents and writes orders."),
    System("dc01", "it_corp", "Domain Controller dc01", "10.10.0.10",
           "Active Directory -- the corporate crown jewels."),
    System("ws01", "it_corp", "Workstation ws01", "10.10.0.31",
           "An employee machine: leaked hashes, a local priv-esc, a licensed binary."),
    System("soc", "it_corp", "SOC / log pipeline", "",
           "Auth + process telemetry flows here. Where you catch the machine being wrong."),
    System("release", "dmz", "Order-release staging", "10.15.0.4",
           "The one-way conduit: HQ writes a signed release here; the floor reads it."),
    System("mill", "ot", "Mill-floor agent", "10.20.0.5",
           "Receives order releases behind the OT firewall and drives PM3."),
    System("pm3", "ot", "PM3 paper machine", "",
           "The process line + moisture/speed/steam dashboard. The physical consequence."),
    System("loadmaster", "ot", "LoadMaster optimizer", "",
           "Cutting-stock + truck-load optimization for the floor."),
    System("wire", "it_corp", "The wire", "",
           "Network traffic + logs -- the cross-cutting recon surface."),
    System("email", "people", "Corporate email", "",
           "The inbox: phishing, homoglyph domains, spoofed senders."),
]

# ---------------------------------------------------------------------------
# 3) EXERCISES -- ONE record per mission, in campaign order.
#    List position IS the campaign order. Add a mission here and it appears
#    everywhere. `board=False` keeps intro/toolkit/people off the network board.
# ---------------------------------------------------------------------------
EXERCISES = [
    Exercise("wire-01", "wire", "read the traffic and find the leak", "intro", "recon",
             board=False, emits=["pcap", "access.log"]),

    Exercise("build-01", "wire", "build a port scanner", "toolkit", "build", board=False),
    Exercise("build-02", "wire", "build a packet sniffer", "toolkit", "build", board=False),

    Exercise("crack-01", "ws01", "a leaked password-hash dump", "implementation", "break",
             grants=["domain_user_cred"], emits=["auth.log"]),

    Exercise("app-01", "orderdesk", "order lookup looks injectable (SQLi)", "guided", "break",
             grants=["db_service_cred"], emits=["app.log", "sql_audit"]),
    Exercise("app-01-fix", "orderdesk", "BLUE: parameterize the query", "implementation", "fix",
             requires=["db_service_cred"], grants=["hardened_sqli"],
             invariant="a customer can still look up their own orders"),
    Exercise("idor-01", "orderdesk", "order pages use sequential IDs (IDOR)", "guided", "break",
             grants=["customer_pii"], emits=["app.log"]),
    Exercise("idor-01-fix", "orderdesk", "BLUE: enforce ownership checks", "implementation", "fix",
             requires=["customer_pii"], grants=["hardened_idor"],
             invariant="a customer can still see their own orders"),

    Exercise("bin-01", "ws01", "a licensed tool guarding a key (needs local access)",
             "implementation", "break", requires=["root_ws01"], grants=["license_key"]),
    Exercise("priv-01", "ws01", "low-priv shell; a sudo/SUID misconfig may give root",
             "implementation", "break", grants=["root_ws01"], emits=["auth.log", "proc.log"]),

    Exercise("build-03", "wire", "build a debugger (breakpoints)", "toolkit", "build", board=False),
    Exercise("build-04", "wire", "build a fuzzer", "toolkit", "build", board=False),

    Exercise("domain-01", "dc01", "map a path to Domain Admin -- needs a foothold",
             "operational", "break", requires=["domain_user_cred", "db_service_cred"],
             grants=["domain_admin"], emits=["security.evtx"]),
    Exercise("domain-01-fix", "dc01", "BLUE: cut the path to DA", "operational", "fix",
             requires=["domain_admin"], grants=["hardened_ad"],
             invariant="legitimate admins can still manage the domain"),

    Exercise("ai-01", "millie", "the RAG product; retrieves customer documents (injection)",
             "guided", "break", grants=["admin_api_key"], emits=["agent.log"]),
    Exercise("ai-01-fix", "millie", "BLUE: stop the injection", "implementation", "fix",
             requires=["admin_api_key"], grants=["hardened_agent"],
             invariant="normal customer questions still get a real answer"),

    Exercise("hunt-01", "soc", "reconstruct the breach from auth + process logs",
             "investigation", "detect", grants=["incident_report"],
             emits=["incident_report"]),

    Exercise("phish-01", "email", "triage a phishing email and pull the real link",
             "guided", "detect", board=False, emits=["email_headers"]),

    Exercise("mill-01", "mill", "the HQ->mill release link -- forge a release and down PM3",
             "guided", "break", grants=["mill_control"], emits=["release.log"]),
    Exercise("mill-01-fix", "mill",
             "BLUE: verify releases (HMAC + freshness + no-replay + bounds)",
             "stateful", "fix", requires=["mill_control"], grants=["hardened_mill"],
             invariant="legitimate releases still reach PM3 and production continues",
             emits=["release.log"]),
]

# ---------------------------------------------------------------------------
# 4) SCENARIOS -- ordered chains around one incident. These reference ONLY the
#    missions above, so they pressure-test the schema with no new content. The
#    shape is always the campaign loop: break -> detect -> fix -> prove it holds.
# ---------------------------------------------------------------------------
SCENARIOS = [
    Scenario(
        "compromised-release", "Compromised production release",
        "Can you keep PM3 producing while cutting the path from the public side to the floor?",
        "A customer document poisons Millie; the agent's database reach exposes a service "
        "credential; that reach is abused to forge an order release that crosses the conduit "
        "and downs PM3. You reconstruct the chain from the logs, verify the release link, and "
        "close the injection -- without stopping legitimate orders.",
        ["ai-01", "app-01", "mill-01", "hunt-01", "mill-01-fix", "ai-01-fix"]),
    Scenario(
        "customer-data-breach", "Customer data breach",
        "Can customers still look up their own orders once you lock cross-customer access?",
        "Sequential order IDs and an injectable lookup let one customer read another's data. "
        "You detect the scraping in the access logs, then enforce ownership and parameterize "
        "the query -- while every customer keeps seeing their own orders.",
        ["idor-01", "app-01", "hunt-01", "idor-01-fix", "app-01-fix"]),
]


# ---------------------------------------------------------------------------
# derived accessors -- the views call these; they never hand-maintain a list
# ---------------------------------------------------------------------------
def zones():
    return list(ZONES)


def systems():
    return list(SYSTEMS)


def zone(zid):
    return next((z for z in ZONES if z.id == zid), None)


def system(sid):
    return next((s for s in SYSTEMS if s.id == sid), None)


def exercises():
    return list(EXERCISES)


def exercise(mission):
    return next((e for e in EXERCISES if e.mission == mission), None)


def scenarios():
    return list(SCENARIOS)


def scenario(sid):
    return next((s for s in SCENARIOS if s.id == sid), None)


def systems_in(zid):
    """Systems in a zone, in table order."""
    return [s for s in SYSTEMS if s.zone == zid]


def exercises_on(sid):
    """Exercises that live on a system, in campaign order."""
    return [e for e in EXERCISES if e.system == sid]


def zone_of(mission):
    """The Zone an exercise's system sits in (None if unknown)."""
    e = exercise(mission)
    if not e:
        return None
    s = system(e.system)
    return zone(s.zone) if s else None


def campaign_order():
    """The canonical mission sequence = EXERCISES in list order."""
    return [e.mission for e in EXERCISES]


def board_exercises():
    """Only the live-network targets (what `elite engage` shows)."""
    return [e for e in EXERCISES if e.board]


def toolkit():
    """The build-your-own-tools missions."""
    return [e.mission for e in EXERCISES if e.level == "toolkit"]


def all_grants():
    g = set()
    for e in EXERCISES:
        g.update(e.grants)
    return g


# ---------------------------------------------------------------------------
# validate() -- the drift guard. The test suite calls this; if you add a mission
# without a record, mistype a zone, or require loot nothing grants, it FAILS.
# ---------------------------------------------------------------------------
def validate(mission_ids=None):
    """Return a list of problems ([] means the registry is coherent).

    If mission_ids is given (the real set from load_missions()), it also checks
    that the registry and the code agree exactly -- the heart of the no-drift
    guarantee.
    """
    problems = []
    zone_ids = {z.id for z in ZONES}
    sys_ids = {s.id for s in SYSTEMS}

    # every system sits in a real zone
    for s in SYSTEMS:
        if s.zone not in zone_ids:
            problems.append(f"system {s.id!r} references missing zone {s.zone!r}")

    # every exercise is well-formed and placed
    seen = set()
    for e in EXERCISES:
        if e.mission in seen:
            problems.append(f"exercise {e.mission!r} listed more than once")
        seen.add(e.mission)
        if e.system not in sys_ids:
            problems.append(f"exercise {e.mission!r} references missing system {e.system!r}")
        if e.level not in LEVELS:
            problems.append(f"exercise {e.mission!r} has unknown level {e.level!r}")
        if e.verb not in VERBS:
            problems.append(f"exercise {e.mission!r} has unknown verb {e.verb!r}")

    # every required loot is granted somewhere (the chain is reachable)
    grants = all_grants()
    for e in EXERCISES:
        for need in e.requires:
            if need not in grants:
                problems.append(f"exercise {e.mission!r} requires {need!r}, which nothing grants")

    # every scenario step is a real exercise
    for sc in SCENARIOS:
        for step in sc.steps:
            if step not in seen:
                problems.append(f"scenario {sc.id!r} step {step!r} is not an exercise")

    # the registry and the code agree exactly (no mission without a record, and vice versa)
    if mission_ids is not None:
        missing = set(mission_ids) - seen
        extra = seen - set(mission_ids)
        for m in sorted(missing):
            problems.append(f"mission {m!r} exists in code but has no registry record")
        for m in sorted(extra):
            problems.append(f"registry record {m!r} has no mission in code")

    return problems
