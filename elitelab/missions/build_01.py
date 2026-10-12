"""Mission build-01: Build your own port scanner (Layer 1 - The Wire).

Taught as a staircase so a beginner never faces a blank function: SEE a worked example
run, POKE it, then BUILD the real thing. The checker opens real listeners on localhost
and runs YOUR scanner against them - it passes only when your code finds exactly the
open ports. You learn nmap by building a tiny one.
"""
import random
import socket
import subprocess
import sys
from pathlib import Path

from .base import Mission

# Rung 2: a runnable worked example the learner sees FIRST (not graded; just to learn from).
SCAN_ONE = '''#!/usr/bin/env python3
"""A WORKED EXAMPLE. Run it first:   python3 scan_one.py
It checks whether ONE port on your own machine is open. Read every line, then change the
port number near the top and run it again. A port scanner is just this, repeated."""
import socket

host = "127.0.0.1"   # your own machine ("localhost") - always safe to scan
port = 80            # <-- change this (try 22, 443, 9999) and re-run to see it change

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # make a TCP socket (like a phone)
s.settimeout(0.5)                                       # give up after 0.5s if nobody answers
result = s.connect_ex((host, port))                     # try to connect; 0 means SUCCESS = open
s.close()                                               # hang up

print(f"port {port} is", "OPEN" if result == 0 else "closed")
'''

# Rung 5: the real mission file. Only scan_port is yours to write.
SKELETON = '''#!/usr/bin/env python3
"""A tiny TCP port scanner. Fill in scan_port().  Usage: python3 scanner.py <host> <ports>
   <ports> can be "80,443" or a range "20-25"."""
import socket
import sys


def scan_port(host, port, timeout=0.5):
    # You already did this in scan_one.py - it printed whether a port was open.
    # Here, do the SAME thing, but RETURN True if the port is open and False if not.
    # (Make a socket, set the timeout, call connect_ex((host, port)), and return whether
    #  the result was 0. Don't forget to close the socket.)
    raise NotImplementedError("implement scan_port")


def parse_ports(spec):
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    if len(sys.argv) < 3:
        print("usage: python3 scanner.py <host> <ports>")
        return
    host, ports = sys.argv[1], parse_ports(sys.argv[2])
    for p in ports:
        if scan_port(host, p):
            print(f"{p} open")


if __name__ == "__main__":
    main()
'''


def setup(workdir: Path):
    (workdir / "scan_one.py").write_text(SCAN_ONE)
    (workdir / "scanner.py").write_text(SKELETON)
    (workdir / "START_HERE.txt").write_text(
        "GOAL: write scan_port() in scanner.py so it finds open TCP ports.\n\n"
        "Never written one? Do these in order - each step is tiny:\n\n"
        "  1. SEE IT    python3 scan_one.py\n"
        "               A worked example. It checks ONE port and says open/closed.\n\n"
        "  2. POKE IT   Edit scan_one.py, change `port` to 22, then 443, then 9999, and\n"
        "               run it again each time. Notice: connect_ex returns 0 when OPEN.\n\n"
        "  3. BUILD IT  Open scanner.py and write scan_port(). It's exactly what scan_one.py\n"
        "               does - just wrapped in a function that RETURNS True (open) / False (closed)\n"
        "               instead of printing.\n\n"
        "  4. CHECK IT  python3 scanner.py 127.0.0.1 20-25     (try it yourself)\n"
        "               then:  elite lab submit build-01 BUILT\n\n"
        "Stuck on a step?  elite lab hint build-01   (it asks questions; it won't hand you code).\n")


def check_build(workdir: Path, submitted: str) -> bool:
    base = random.randint(20000, 40000)
    open_ports = [base, base + 2, base + 5]       # leave gaps (base+1,3,4,6 stay closed)
    listeners = []
    try:
        for p in open_ports:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", p))
            s.listen()
            listeners.append(s)
        rng = f"{base}-{base + 6}"
        proc = subprocess.run([sys.executable, str(workdir / "scanner.py"), "127.0.0.1", rng],
                              capture_output=True, text=True, timeout=30)
        reported = set()
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit() and "open" in parts[1]:
                reported.add(int(parts[0]))
    except Exception:
        return False
    finally:
        for s in listeners:
            s.close()
    return reported == set(open_ports)


MISSION = Mission(
    id="build-01",
    layer="1 The Wire",
    title="Build your own port scanner",
    difficulty="easy",
    goal="Implement scan_port() in scanner.py so it finds open TCP ports, then submit BUILT. "
         "New to this? Run scan_one.py first - the mission walks you up from there.",
    flag_format="BUILT (after scanner.py works)",
    setup=setup,
    checker=check_build,
    tools=["python3", "sockets"],
    hints=[
        "Did you run `python3 scan_one.py` and change the port a few times? scan_port does the "
        "SAME thing - just copy what scan_one.py does into the function to start, then make it "
        "RETURN a value instead of printing.",
        "The key line is connect_ex((host, port)). You saw what it returns when a port is open: "
        "0. So your function should end by returning whether that result == 0.",
        "The whole body is four lines: make the socket, set the timeout, call connect_ex, close "
        "the socket, and `return result == 0`. If you look at the exact lines in scan_one.py to "
        "do it, retype them here from memory once afterward so it actually sticks.",
    ],
    debrief=(
        "You built a working TCP port scanner - and if you climbed the rungs, you UNDERSTOOD "
        "every line instead of pasting it. That's the difference the whole tool is built on. "
        "Under the hood you now know what nmap does: a connect scan completes the TCP handshake "
        "(and gets logged), while nmap's default SYN scan sends SYN and never finishes - faster "
        "and quieter. Next builds: a packet sniffer, a debugger, a fuzzer."),
)
