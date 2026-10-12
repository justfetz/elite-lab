"""Mission build-01: Build your own port scanner (Layer 1 - The Wire / build-your-own-tools).

You implement the core of a TCP port scanner in Python. The checker opens real
listeners on localhost and runs YOUR scanner against them - it passes only if your
code finds exactly the open ports (all of them, no false positives). You learn nmap
by building a tiny one.
"""
import random
import socket
import subprocess
import sys
from pathlib import Path

from .base import Mission

SKELETON = '''\
#!/usr/bin/env python3
"""A tiny TCP port scanner - fill in scan_port(). Usage: python3 scanner.py <host> <ports>
   <ports> can be "80,443" or a range "20000-20010"."""
import socket
import sys


def scan_port(host, port, timeout=0.5):
    # TODO: return True if a TCP connection to (host, port) succeeds, else False.
    #
    #   s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #   s.settimeout(timeout)
    #   result = s.connect_ex((host, port))   # 0 means the port is open
    #   s.close()
    #   return result == 0
    #
    # Write those lines yourself - that connect_ex call IS a port scan.
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
    (workdir / "scanner.py").write_text(SKELETON)
    (workdir / "START_HERE.txt").write_text(
        "Open scanner.py and implement scan_port() so it returns True for an open TCP port.\n"
        "Contract the checker relies on:\n"
        "  python3 scanner.py <host> <ports>   prints one line '<port> open' per open port.\n"
        "Test it yourself against something you're running (e.g. python3 -m http.server):\n"
        "  python3 scanner.py 127.0.0.1 8000-8005\n"
        "When it works, submit BUILT and the checker will run your scanner against real\n"
        "listeners it opens on localhost.\n")


def check_build(workdir: Path, submitted: str) -> bool:
    base = random.randint(20000, 40000)
    open_ports = [base, base + 2, base + 5]      # leave gaps (base+1,3,4,6 stay closed)
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
    return reported == set(open_ports)   # found all open, no false positives


MISSION = Mission(
    id="build-01",
    layer="1 The Wire",
    title="Build your own port scanner",
    difficulty="easy",
    goal="Implement scan_port() in scanner.py so it correctly finds open TCP ports, then submit BUILT.",
    flag_format="BUILT (after scanner.py works)",
    setup=setup,
    checker=check_build,
    tools=["python3", "sockets"],
    hints=[
        "A TCP 'scan' of one port is just trying to connect to it. Open a socket: "
        "socket.socket(socket.AF_INET, socket.SOCK_STREAM).",
        "Set a short timeout (s.settimeout(0.5)) so closed/filtered ports don't hang, then use "
        "s.connect_ex((host, port)) - it returns 0 when the port is open (no exception needed).",
        "Return (connect_ex(...) == 0) and close the socket. That's the whole scanner - the same "
        "idea nmap's connect scan uses, just without nmap's speed and stealth.",
    ],
    debrief=(
        "You built a working TCP port scanner. Now you understand what nmap does under the hood: "
        "a connect scan completes the TCP handshake (gets logged), while nmap's default SYN scan "
        "sends SYN and never finishes - faster and quieter. Next builds in this track: a raw-socket "
        "packet sniffer, then a ptrace mini-debugger (Gray Hat Python), then a fuzzer against your "
        "own crackme. Building the tool is how you truly learn it."),
)
