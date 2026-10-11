"""Mission crack-01: Crack the CEO (Layer 2 - The Door).

Ships a file of unsalted MD5 password hashes. The learner uses a REAL tool (John
the Ripper or Hashcat) to crack the CEO's password and submit it. Teaches why fast,
unsalted hashing is a disaster - by letting you break it yourself.
"""
import hashlib
import random
from pathlib import Path

from .base import Mission

SEED = 0xC4AC7001
# Deliberately weak, dictionary-style passwords so a small wordlist cracks them fast.
WEAK = ["princess", "football", "iloveyou", "sunshine", "monkey123",
        "superman", "baseball", "shadow", "michael", "jennifer"]
USERS = ["ceo", "cfo", "it_admin", "reception", "warehouse"]


def _generate():
    rng = random.Random(SEED)
    assigned = {u: rng.choice(WEAK) for u in USERS}
    return assigned


def setup(workdir: Path):
    assigned = _generate()
    lines = [f"{u}:{hashlib.md5(pw.encode()).hexdigest()}" for u, pw in assigned.items()]
    (workdir / "hashes.txt").write_text("\n".join(lines) + "\n")
    (workdir / "START_HERE.txt").write_text(
        "hashes.txt holds user:md5 pairs dumped from a breached app (unsalted MD5).\n"
        "Crack the CEO's password with John or Hashcat and submit flag{password}.\n\n"
        "John:    john --format=raw-md5 --wordlist=<rockyou.txt> hashes.txt ; john --show ...\n"
        "Hashcat: hashcat -m 0 -a 0 hashes.txt <rockyou.txt>\n"
        "(rockyou.txt ships with Kali, or grab a common-password list. These are weak,\n"
        " dictionary words on purpose - they fall in seconds, which is the whole point.)\n")


def solution(workdir: Path) -> str:
    return f"flag{{{_generate()['ceo']}}}"


MISSION = Mission(
    id="crack-01",
    layer="2 The Door",
    title="Crack the CEO",
    difficulty="easy",
    goal="Crack the CEO's MD5 password in hashes.txt and submit flag{password}.",
    flag_format="flag{password}",
    setup=setup,
    solution=solution,
    tools=["john", "hashcat", "md5"],
    hints=[
        "The hashes are raw MD5 (32 hex chars, no salt). Tell your cracker the format: "
        "john --format=raw-md5, or hashcat -m 0.",
        "Point it at a common-password wordlist (rockyou.txt). These passwords are ordinary "
        "dictionary words, so a wordlist attack finds them almost instantly.",
        "After cracking, read the CEO's line: `john --show --format=raw-md5 hashes.txt`. The "
        "password after ceo: is your flag.",
    ],
    debrief=(
        "You just proved why MD5 for passwords is indefensible: unsalted + fast means a "
        "GPU tries billions of guesses a second and a wordlist finds common passwords "
        "instantly. DEFENSE: store passwords with a SLOW, SALTED hash (bcrypt, scrypt, "
        "Argon2) tuned to a high cost. The salt kills precomputed rainbow tables; the slow "
        "cost makes mass cracking impractical. Same stolen file, completely different outcome."),
)
