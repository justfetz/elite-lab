"""Missions mill-01 (break) and mill-01-fix (build): the HQ -> mill release link.

The manufacturing capstone. HQ sends "order release" messages to the on-site
mill-agent, which acts on them (sets the machine, runs the order). The shipped
agent trusts ANY well-formed message: no sender check, no integrity check, no
freshness check, no bounds check. So an attacker on the wire can FORGE a release
with an unsafe setpoint - breaking the sheet and downing the line (the killswitch)
- or REPLAY a captured one.

  mill-01      BREAK: craft a forged, damaging release the agent accepts.
  mill-01-fix  BUILD: add HMAC verification, freshness (anti-replay), and bounds
               checks so forged/replayed/unsafe releases are rejected and only a
               genuine, fresh, safe release runs. The checker runs YOUR agent
               against all four cases, visibly.

Offline, deterministic, zero-setup (stdlib hmac). HQ and the mill share a key -
as real endpoints do - so the FIX can verify; the attacker never needs it,
because the broken agent never checks.
"""
import hashlib
import hmac
import subprocess
import sys
import time
from pathlib import Path

from .base import Mission

SHARED_KEY = b"lakefront-mill-hq-shared-key-2026"
SAFE_SETPOINT_MAX = 1450          # m/min; above this the sheet breaks, line goes down
VALID_GRADES = {"26kraft", "42medium", "35liner", "33liner"}
FIELDS = ("order", "grade", "rolls", "weight", "setpoint", "ts", "nonce")


def _canon(d):
    return ";".join(f"{k}={d[k]}" for k in FIELDS)


def _sign(d, key=SHARED_KEY):
    return hmac.new(key, _canon(d).encode(), hashlib.sha256).hexdigest()


def _msg(d):
    return _canon(d) + ";sig=" + _sign(d)


def _valid_release(setpoint=1200, ts=None, nonce="a1b2c3",
                   grade="26kraft", rolls="40", weight="48000"):
    return {"order": "1001", "grade": grade, "rolls": rolls, "weight": weight,
            "setpoint": str(setpoint),
            "ts": str(ts if ts is not None else int(time.time())), "nonce": nonce}


# ---------- the vulnerable mill-agent (dropped for the learner) ----------
VULN_AGENT = '''#!/usr/bin/env python3
"""mill-agent: receives an order release from HQ and acts on it (sets PM3, runs it).
Usage:  python3 mill_agent.py "<release message>"

[VULN] It trusts ANY well-formed message. There is NO check of:
  - WHO sent it (no signature / HMAC) -> anyone on the wire can forge one
  - whether it's FRESH (no timestamp check) -> a captured message can be replayed
  - whether the values are SAFE (no bounds) -> an unsafe setpoint runs anyway
Your job in mill-01-fix is to add those checks."""
import sys

def parse(msg):
    d = {}
    for part in msg.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k] = v
    return d

def handle(d):
    order = d.get("order", "?")
    try:
        setpoint = int(d.get("setpoint", "0"))
    except ValueError:
        setpoint = 0
    # [VULN] accept and act, no verification whatsoever
    print(f"RELEASE ACCEPTED: order {order}, setpoint {setpoint} m/min -> PM3")
    if setpoint > 1450:
        print("!! setpoint exceeds safe max 1450 -- SHEET BREAK, PM3 DOWN !!")

if __name__ == "__main__":
    handle(parse(sys.argv[1] if len(sys.argv) > 1 else ""))
'''


def _sender_src():
    # a helper so the learner can see a genuine, signed release (and make test ones)
    return ('#!/usr/bin/env python3\n'
            '"""HQ order-release sender. Prints a genuine, signed, fresh release.\n'
            '   Usage: python3 send_release.py [setpoint]"""\n'
            'import hashlib, hmac, sys, time, random\n'
            f'KEY = {SHARED_KEY!r}\n'
            f'FIELDS = {FIELDS!r}\n'
            'def canon(d): return ";".join(f"{k}={d[k]}" for k in FIELDS)\n'
            'def sign(d): return hmac.new(KEY, canon(d).encode(), hashlib.sha256).hexdigest()\n'
            'sp = sys.argv[1] if len(sys.argv) > 1 else "1200"\n'
            'd = {"order":"1001","grade":"26kraft","rolls":"40","weight":"48000",\n'
            '     "setpoint":sp,"ts":str(int(time.time())),"nonce":str(random.randint(1,1<<30))}\n'
            'print(canon(d) + ";sig=" + sign(d))\n')


def setup_break(workdir: Path):
    (workdir / "mill_agent.py").write_text(VULN_AGENT)
    (workdir / "send_release.py").write_text(_sender_src())
    (workdir / "sample_release.txt").write_text(_msg(_valid_release()) + "\n")
    (workdir / "START_HERE.txt").write_text(
        "GOAL: forge an order-release message the mill-agent ACCEPTS and that would damage\n"
        "the mill -- an UNSAFE setpoint (over 1450 m/min breaks the sheet and downs PM3).\n"
        "Submit the message you forged.\n\n"
        "The agent runs a release:  python3 mill_agent.py \"<message>\"\n"
        "A genuine release is in sample_release.txt (semicolon key=value fields + a sig).\n"
        "See one made live:  python3 send_release.py\n\n"
        "DO THIS:\n"
        "  1. READ mill_agent.py. Notice it never checks the signature, the timestamp, or\n"
        "     the setpoint bounds -- it acts on anything well-formed.\n"
        "  2. Because it never checks the signature, you DON'T need the key. Hand it a\n"
        "     release with order=... and setpoint=9999 (unsafe). You can drop the sig\n"
        "     entirely. Try it:\n"
        "        python3 mill_agent.py \"order=1001;setpoint=9999\"\n"
        "     See 'SHEET BREAK, PM3 DOWN'? That's the killswitch -- you just downed the line.\n"
        "  3. SAVE that forged message to a file called attack.txt (the checker runs it\n"
        "     through the mill-agent to confirm it was accepted and damaging):\n"
        "        echo 'order=1001;setpoint=9999' > attack.txt\n"
        "     Then submit:\n"
        "        elite lab submit mill-01 PWNED\n\n"
        "Then defend it:  elite lab start mill-01-fix\n")


def check_attack(workdir: Path, submitted: str) -> bool:
    f = workdir / "attack.txt"
    if not f.exists():
        return False
    msg = f.read_text().strip()
    out, ok = _run_agent(workdir, msg)
    # the vulnerable agent must have ACCEPTED it AND it must be damaging (unsafe setpoint
    # -> the 'SHEET BREAK' line). That proves a forged, harmful release got through.
    return ok and "RELEASE ACCEPTED" in out and "SHEET BREAK" in out


def setup_fix(workdir: Path):
    (workdir / "mill_agent.py").write_text(VULN_AGENT)
    (workdir / "send_release.py").write_text(_sender_src())
    (workdir / "START_HERE.txt").write_text(
        "Now defend the mill. Edit mill_agent.py so it REJECTS forged, replayed, and unsafe\n"
        "releases, and ACCEPTS only a genuine, fresh, in-bounds one. HQ and the mill share a\n"
        "key, so you can verify. Add these checks to handle(), and print a line starting with\n"
        "'REJECTED' when any fails (print 'RELEASE ACCEPTED' only when all pass):\n\n"
        "  1. INTEGRITY / SENDER  -- recompute the HMAC-SHA256 over the canonical fields\n"
        f"       (order;grade;rolls;weight;setpoint;ts;nonce) with the shared key\n"
        f"       {SHARED_KEY!r}\n"
        "       and compare to the message's sig (use hmac.compare_digest). No match -> reject.\n"
        "  2. FRESHNESS  -- reject if ts is more than 120 seconds old OR in the future\n"
        "       (abs(now - ts) > 120). A timestamp window alone isn't enough, though...\n"
        "  3. NO REPLAY  -- the same signed release can be resent inside that window. Keep a\n"
        "       record of nonces you've ACCEPTED (persist it to a file next to the agent) and\n"
        "       reject any nonce you've seen before.\n"
        "  4. BOUNDS  -- reject if setpoint > 1450, grade not in\n"
        f"       {sorted(VALID_GRADES)}, or rolls/weight not positive.\n\n"
        "The signing is exactly what send_release.py does -- read it. Then submit FIXED; the\n"
        "checker runs YOUR agent against a forged, a replayed, an unsafe, and a genuine\n"
        "release, and shows you each verdict.\n\n"
        "Cheat for the commands you'll want:  elite cheat grep   (and read send_release.py)\n")


def _run_agent(workdir: Path, message: str):
    """(stdout, ok). ok=False on crash - a broken agent can never pass."""
    try:
        p = subprocess.run([sys.executable, str(workdir / "mill_agent.py"), message],
                           capture_output=True, text=True, timeout=20)
        return p.stdout, (p.returncode == 0 and not p.stderr.strip())
    except Exception:
        return "", False


def _accepted(out):
    return "RELEASE ACCEPTED" in out


def _rejected(out):
    return "REJECTED" in out


def check_fix(workdir: Path, submitted: str) -> bool:
    # start clean: forget nonces a previous attempt recorded
    seen = workdir / ".seen_nonces"
    if seen.exists():
        seen.unlink()
    now = int(time.time())
    uid = str(now)
    # EACH reject case is otherwise VALID, FRESH, and SAFE - so it can only be caught
    # by the ONE defense it targets. A patch that skips a check will accept its case.
    bad_sig = _canon(_valid_release(nonce="s-" + uid)) + ";sig=deadbeef"   # only HMAC catches it
    future  = _msg(_valid_release(ts=now + 9999, nonce="f-" + uid))        # only freshness
    stale   = _msg(_valid_release(ts=now - 600,  nonce="o-" + uid))        # only freshness
    unsafe  = _msg(_valid_release(setpoint=9999, nonce="u-" + uid))        # only bounds
    badgrade = _msg(_valid_release(grade="99zzz", nonce="g-" + uid))       # only bounds
    badqty  = _msg(_valid_release(rolls="-5",    nonce="q-" + uid))        # only bounds
    genuine = _msg(_valid_release(nonce="ok-" + uid))                      # must ACCEPT

    cases = []
    og, okg = _run_agent(workdir, genuine)                    # run genuine -> records nonce
    cases.append(("genuine (signed, fresh, safe)", okg and _accepted(og), "accept"))
    orp, okrp = _run_agent(workdir, genuine)                  # same message again -> replay
    cases.append(("replayed (duplicate nonce)",
                  okrp and _rejected(orp) and not _accepted(orp), "reject"))
    for name, msg in [("forged (bad signature, else valid)", bad_sig),
                      ("future timestamp", future),
                      ("stale timestamp", stale),
                      ("unsafe setpoint", unsafe),
                      ("invalid grade", badgrade),
                      ("invalid quantity", badqty)]:
        o, ok = _run_agent(workdir, msg)
        cases.append((name, ok and _rejected(o) and not _accepted(o), "reject"))
    if seen.exists():
        seen.unlink()

    print("\n  Mill-link check -- releases sent to your agent:")
    allgood = True
    for name, passed, expect in cases:
        mark = f"[{expect}ed] ok" if passed else f"[did NOT {expect} / crashed]"
        if not passed:
            allgood = False
        print(f"    {name:<36} {mark}")
    print(f"  Verdict: {'PASS - only a genuine, fresh release runs.' if allgood else 'FAIL - see above.'}\n")
    return allgood


MISSION = Mission(
    id="mill-01",
    layer="7 The Mill (OT)",
    title="Forge a mill release (down the line)",
    difficulty="medium",
    goal="The mill-agent trusts any well-formed release. Forge a damaging one (unsafe "
         "setpoint > 1450), save it to attack.txt, then submit PWNED.",
    flag_format="PWNED (after attack.txt downs the line)",
    setup=setup_break,
    checker=check_attack,
    tools=["python3", "a text editor"],
    hints=[
        "Read mill_agent.py: handle() prints RELEASE ACCEPTED for anything, and warns on "
        "setpoint > 1450 but STILL runs it. It never checks the signature, so you can omit it.",
        "A forged, damaging release needs only order and an unsafe setpoint (over 1450), e.g. "
        "order=1001;setpoint=9999.",
        "Save it and submit:  echo 'order=1001;setpoint=9999' > attack.txt  then  "
        "elite lab submit mill-01 PWNED. (Run it through mill_agent.py first to watch the line "
        "go down.)",
    ],
    debrief=(
        "You forged a control message because the mill blindly trusted the wire. In OT, that's "
        "not data theft - it's physical damage and downtime, the exact leverage ransomware "
        "crews use against manufacturers. The IT->OT boundary is where it happens. DEFENSE is "
        "mill-01-fix: authenticate the sender (HMAC), reject stale messages (anti-replay), and "
        "bound every value - so a forged or replayed release can't move the machine."),
)

MISSION_FIX = Mission(
    id="mill-01-fix",
    layer="7 The Mill (OT)",
    title="Verify the mill release",
    difficulty="hard",
    goal="Patch mill_agent.py to reject forged, replayed, and unsafe releases (HMAC + freshness "
         "+ bounds) and accept only a genuine one. Submit FIXED.",
    flag_format="FIXED (after mill_agent.py verifies releases)",
    setup=setup_fix,
    checker=check_fix,
    tools=["python3", "hmac", "a text editor"],
    hints=[
        "send_release.py shows the signing exactly: HMAC-SHA256 over "
        "'order;grade;rolls;weight;setpoint;ts;nonce' with the shared key. Recompute it and "
        "compare to d['sig'] with hmac.compare_digest. (A valid-looking but wrongly-signed "
        "message must be rejected on the signature ALONE.)",
        "Freshness both ways: reject if abs(time.time() - int(d['ts'])) > 120 (too old OR in "
        "the future). Then stop replays WITHIN that window: save accepted nonces to a file "
        "next to the agent and reject any nonce you've already seen.",
        "Bounds: reject if int(d['setpoint']) > 1450, d['grade'] not in the valid set, or "
        "int(d['rolls'])<=0 / int(d['weight'])<=0. Print a line starting 'REJECTED' on any "
        "failure; print 'RELEASE ACCEPTED' (and record the nonce) only if ALL checks pass.",
    ],
    debrief=(
        "This is defense-in-depth on a control channel: AUTHENTICATE (HMAC proves it came from "
        "HQ and wasn't altered), FRESHNESS (a timestamp window - or better, a one-time nonce - "
        "stops replay), and VALIDATE (bounds stop a signed-but-insane command). Miss any one and "
        "the mill is still exposed. Real OT adds signed firmware, network segmentation, and a "
        "hard physical interlock the software can't override."),
)

MISSIONS = [MISSION, MISSION_FIX]
