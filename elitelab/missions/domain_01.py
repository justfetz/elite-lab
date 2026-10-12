"""Missions domain-01 (attack) and domain-01-fix (defend): Active Directory path to
Domain Admin (Layer 5 - The Domain).

Offline BloodHound-style analysis. You get an AD export (groups with nesting + ACLs).
- domain-01     : starting from a user you control, find the one account you can take
                  over that is an effective Domain Admin (via nested groups). flag{user}.
- domain-01-fix : edit the export to cut that path to DA while keeping legitimate access;
                  the checker recomputes the graph to verify.
"""
import json
from pathlib import Path

from .base import Mission

START_USER = "jdoe"
DANGEROUS = {"GenericAll", "GenericWrite", "WriteDacl", "WriteOwner",
             "ForceChangePassword", "Owns", "AllExtendedRights"}

GROUPS = {
    "Domain Admins": ["Administrator", "ServerOps"],
    "ServerOps": ["svc_backup", "DBAdmins"],
    "DBAdmins": ["svc_sql", "mwilson"],
    "HelpDesk": ["jdoe", "areed"],
    "Accounting": ["bsmith", "areed"],
    "Everyone": ["jdoe", "areed", "bsmith", "mwilson", "svc_sql", "svc_backup", "Administrator"],
}
ACLS = [
    {"principal": "HelpDesk", "right": "GenericAll", "target": "svc_sql"},
    {"principal": "jdoe", "right": "ForceChangePassword", "target": "bsmith"},
    {"principal": "areed", "right": "GenericAll", "target": "Accounting"},
    {"principal": "Accounting", "right": "GenericWrite", "target": "printserver"},
]


# ---------- graph analysis (shared by solution + fix checker) ----------
def _effective_members(group, groups, seen=None):
    """Users (leaf members) of a group, resolving nested groups."""
    seen = seen or set()
    if group in seen:
        return set()
    seen.add(group)
    users = set()
    for m in groups.get(group, []):
        if m in groups:
            users |= _effective_members(m, groups, seen)
        else:
            users.add(m)
    return users


def _principals_of(user, groups):
    """The user plus every group that transitively contains them (things that act as them)."""
    out = {user}
    for g in groups:
        if user in _effective_members(g, groups):
            out.add(g)
    return out


def _reachable_das(user, groups, acls):
    principals = _principals_of(user, groups)
    controllable = {a["target"] for a in acls
                    if a["principal"] in principals and a["right"] in DANGEROUS}
    das = _effective_members("Domain Admins", groups)
    return controllable & das


def _load(workdir):
    g = json.loads((workdir / "ad_export" / "groups.json").read_text())
    a = json.loads((workdir / "ad_export" / "acls.json").read_text())
    return g, a


def _write_export(workdir, groups=None, acls=None):
    d = workdir / "ad_export"
    d.mkdir(exist_ok=True)
    (d / "groups.json").write_text(json.dumps(groups or GROUPS, indent=2))
    (d / "acls.json").write_text(json.dumps(acls or ACLS, indent=2))
    (d / "users.txt").write_text("\n".join(sorted(
        {u for u in sum(GROUPS.values(), []) if u not in GROUPS})) + "\n")


def setup_attack(workdir: Path):
    _write_export(workdir)
    (workdir / "START_HERE.txt").write_text(
        "You've compromised the user 'jdoe'. The AD export is in ./ad_export/:\n"
        "  groups.json  group -> members (a member can be another group = NESTING)\n"
        "  acls.json    who has a dangerous right (GenericAll, ForceChangePassword, ...) over whom\n\n"
        "Find the ONE account you can take control of - directly, or through a group jdoe is in -\n"
        "that is an effective member of Domain Admins (counting nested groups). Submit flag{username}.\n"
        "Tip: BloodHound automates exactly this; here, do it by hand or with a short script.\n")


def setup_fix(workdir: Path):
    _write_export(workdir)
    (workdir / "START_HERE.txt").write_text(
        "Same AD export. Now cut jdoe's path to Domain Admin: edit ad_export/groups.json or\n"
        "ad_export/acls.json so jdoe can no longer reach any effective Domain Admin - WITHOUT\n"
        "gutting the domain (Administrator must stay an effective Domain Admin, and the Accounting\n"
        "group must keep its members). Then submit FIXED; the checker recomputes the graph.\n")


def solution_attack(workdir: Path) -> str:
    reach = _reachable_das(START_USER, *(_load(workdir)))
    return f"flag{{{sorted(reach)[0]}}}" if reach else "flag{none}"


def check_fix(workdir: Path, submitted: str) -> bool:
    try:
        groups, acls = _load(workdir)
    except Exception:
        return False
    jdoe_safe = not _reachable_das(START_USER, groups, acls)          # path cut
    admin_still_da = "Administrator" in _effective_members("Domain Admins", groups)
    accounting_intact = "bsmith" in groups.get("Accounting", [])      # didn't gut the domain
    return jdoe_safe and admin_still_da and accounting_intact


MISSION = Mission(
    id="domain-01",
    layer="5 The Domain",
    title="Path to Domain Admin",
    difficulty="hard",
    goal="From user jdoe, find the account you can take over that is an effective Domain Admin "
         "(via nested groups + ACLs). Submit flag{username}.",
    flag_format="flag{username}",
    setup=setup_attack,
    solution=solution_attack,
    tools=["your brain", "python3 (optional)", "BloodHound (for real)"],
    hints=[
        "Two questions to answer separately, then intersect: (1) which accounts can jdoe control? "
        "(2) who are the EFFECTIVE Domain Admins, including nested groups?",
        "Controllable = any ACL target where the principal is jdoe OR a group jdoe is in "
        "(check groups.json for jdoe's groups), with a dangerous right. Effective DAs = expand "
        "'Domain Admins' recursively through nested groups.",
        "jdoe is in HelpDesk; HelpDesk has GenericAll over a service account; that service account "
        "is nested (DBAdmins -> ServerOps -> Domain Admins) into Domain Admins. That account is your answer.",
    ],
    debrief=(
        "You just did by hand what BloodHound draws as a graph: a low-privilege user owning a "
        "powerful one through nested groups and an ACL nobody audited. This is how almost every "
        "real AD compromise escalates. DEFENSE is next (domain-01-fix): cut the edge. The fixes in "
        "practice: don't nest service/ops groups into Domain Admins, and remove dangerous ACLs like "
        "GenericAll that a broad group holds over privileged accounts."),
)

MISSION_FIX = Mission(
    id="domain-01-fix",
    layer="5 The Domain",
    title="Cut the path to Domain Admin",
    difficulty="hard",
    goal="Edit the AD export so jdoe can no longer reach Domain Admin, without gutting the domain. "
         "Submit FIXED.",
    flag_format="FIXED (after you cut the path)",
    setup=setup_fix,
    checker=check_fix,
    tools=["a text editor", "the graph in your head"],
    hints=[
        "You can cut the path at either end: remove the dangerous ACL (HelpDesk GenericAll over the "
        "service account), or remove that account from the nested group that reaches Domain Admins.",
        "Edit ad_export/acls.json (delete the HelpDesk->svc_sql GenericAll entry) OR ad_export/"
        "groups.json (remove svc_sql from DBAdmins). Keep Administrator in Domain Admins and bsmith "
        "in Accounting.",
        "After editing, re-run your analysis: jdoe's controllable set should no longer intersect the "
        "effective Domain Admins. Then submit FIXED.",
    ],
    debrief=(
        "Cutting one edge broke the whole path - that's why attackers map the graph and defenders "
        "prune it. Real remediation: tier your admin groups (no service/ops groups nested into "
        "Domain Admins), audit ACLs on privileged objects, and run BloodHound yourself regularly so "
        "you find these edges before an attacker does. Layer 5 cleared."),
)

MISSIONS = [MISSION, MISSION_FIX]
