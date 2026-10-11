"""Mission wire-01: Intrusion in the logs (Layer 1 - The Wire / The Hunt).

Offline, cross-platform. The learner greps a synthetic auth log to find the one
IP that brute-forced the admin login and the password that finally worked.
"""
import random
from pathlib import Path

from .base import Mission

SEED = 0x7117E01  # fixed -> setup and solution agree without storing the answer
USERS = ["admin", "jdoe", "svc_backup", "mwilson", "ceo"]
PASSWORDS = ["letmein", "Summer2026!", "P@ssw0rd", "hunter2", "Dragon#99",
             "qwerty123", "changeme", "Welcome1", "Fall2026!", "trustno1"]
NORMAL_IPS = ["10.2.0.14", "10.2.0.31", "10.2.4.7", "10.2.1.88", "10.2.3.19"]
PATHS = ["/dashboard", "/reports", "/profile", "/api/v1/orders", "/logout"]


def _generate(workdir=None):
    rng = random.Random(SEED)
    attacker = "45." + ".".join(str(rng.randint(1, 254)) for _ in range(3))
    good_password = rng.choice(PASSWORDS)
    # a realistic-looking app log mixing normal traffic with a brute-force burst
    lines = []
    base_ts = 1760000000
    t = base_ts
    for _ in range(140):
        t += rng.randint(1, 40)
        ip = rng.choice(NORMAL_IPS)
        user = rng.choice(USERS)
        path = rng.choice(PATHS)
        lines.append(f"{t} {ip} \"GET {path}\" 200 user={user}")
    # the attack: ~25 failed admin logins from one IP, then one success
    wrong = [p for p in PASSWORDS if p != good_password]
    for _ in range(25):
        t += rng.randint(1, 3)
        pw = rng.choice(wrong)
        lines.append(f'{t} {attacker} "POST /admin/login" 401 user=admin pass={pw}')
    t += 2
    lines.append(f'{t} {attacker} "POST /admin/login" 200 user=admin pass={good_password}')
    # a few more normal lines after, so the success is not simply the last line
    for _ in range(12):
        t += rng.randint(1, 40)
        lines.append(f'{t} {rng.choice(NORMAL_IPS)} "GET {rng.choice(PATHS)}" 200 user={rng.choice(USERS)}')
    rng.shuffle(lines)  # the attacker's lines are scattered, not contiguous
    if workdir is not None:
        (workdir / "access.log").write_text("\n".join(lines) + "\n")
    return attacker, good_password


def setup(workdir: Path):
    _generate(workdir)
    (workdir / "START_HERE.txt").write_text(
        "You are the on-call analyst. The web app's access log is access.log.\n"
        "One external IP brute-forced the admin login and eventually got in.\n"
        "Find that IP and the password that returned 200. Submit flag{IP:PASSWORD}.\n")


def solution(workdir: Path) -> str:
    attacker, pw = _generate(None)
    return f"flag{{{attacker}:{pw}}}"


MISSION = Mission(
    id="wire-01",
    layer="1 The Wire",
    title="Intrusion in the logs",
    difficulty="intro",
    goal="Find the IP that brute-forced /admin/login and the password that succeeded. "
         "Submit flag{IP:PASSWORD}.",
    flag_format="flag{IP:PASSWORD}",
    setup=setup,
    solution=solution,
    tools=["grep", "awk", "sort", "uniq"],
    hints=[
        "A brute-force shows up as many failures from ONE source. Count 401s per IP: "
        "grep 401 access.log  (then look at the IP column).",
        "Try: grep '401' access.log | awk '{print $2}' | sort | uniq -c | sort -rn | head "
        "- the IP with far more 401s than anyone else is your attacker.",
        "Now find that same IP's single 200 on /admin/login: "
        "grep <attacker-ip> access.log | grep '/admin/login' | grep ' 200 '. "
        "The pass= field on that line is the password.",
    ],
    debrief=(
        "You just did detection: a brute-force is a signal (many 401s from one source) "
        "hiding in noise. DEFENSE: rate-limit and lock out repeated failures, alert on "
        "the pattern, and require MFA so a guessed password is not enough. Also notice "
        "the app logged the password in cleartext - never do that; it turns your logs "
        "into a second breach."),
)
