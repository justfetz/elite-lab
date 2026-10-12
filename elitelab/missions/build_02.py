"""Mission build-02: Build a packet parser/sniffer (Layer 1 - The Wire).

The hard, portable skill is PARSING raw packet bytes - that's what you implement and
what the checker tests (with crafted frames, no root needed). The live-capture loop
(raw sockets, needs root/Linux) is provided for when you run it for real.
"""
import socket
import struct
from pathlib import Path

from .base import Mission

SKELETON = r'''#!/usr/bin/env python3
"""Parse an Ethernet+IPv4+TCP frame. Implement parse_packet(). Live capture (root/Linux):
   sudo python3 sniffer.py"""
import socket
import struct
import sys


def parse_packet(raw: bytes) -> dict:
    """Given raw bytes starting at the Ethernet header, return:
       {"src_ip","dst_ip","proto","src_port","dst_port"}  (ports 0 if not TCP/UDP).

    Layout to walk:
      Ethernet = 14 bytes:  dst(6) src(6) ethertype(2).  IPv4 ethertype == 0x0800.
      IPv4 starts at offset 14:
        byte 14  = version(4 bits) | IHL(4 bits).  IHL * 4 = IP header length in bytes.
        byte 14+9 = protocol (6 = TCP, 17 = UDP).
        bytes 14+12 .. 14+16 = source IP (4 bytes)
        bytes 14+16 .. 14+20 = dest IP   (4 bytes)
      TCP/UDP starts at 14 + (IHL*4):  src port (2 bytes), dst port (2 bytes).

    Hints: socket.inet_ntoa(b4) -> "a.b.c.d";  struct.unpack("!H", two_bytes)[0] -> int;
           ihl = (raw[14] & 0x0F).
    """
    # TODO: implement the walk above and return the dict.
    raise NotImplementedError("implement parse_packet")


def main():  # live capture - Linux + root
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
    while True:
        raw = s.recvfrom(65535)[0]
        try:
            info = parse_packet(raw)
            print(f"{info['src_ip']}:{info['src_port']} -> {info['dst_ip']}:{info['dst_port']} "
                  f"proto {info['proto']}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
'''


def setup(workdir: Path):
    (workdir / "sniffer.py").write_text(SKELETON)
    (workdir / "START_HERE.txt").write_text(
        "Implement parse_packet(raw) in sniffer.py (see the docstring for the exact byte\n"
        "layout). The checker feeds it known Ethernet+IPv4+TCP frames and verifies you pull\n"
        "the right source/dest IPs and ports. No root needed to pass - it's pure parsing.\n"
        "To run it live later: sudo python3 sniffer.py  (Linux, raw sockets need root).\n"
        "Submit BUILT when parse_packet works.\n")


def _frame(src_ip, dst_ip, sport, dport):
    eth = struct.pack("!6s6sH", b"\xaa" * 6, b"\xbb" * 6, 0x0800)
    ip = struct.pack("!BBHHHBBH4s4s", 0x45, 0, 40, 0, 0, 64, 6, 0,
                     socket.inet_aton(src_ip), socket.inet_aton(dst_ip))
    tcp = struct.pack("!HH", sport, dport) + b"\x00" * 16
    return eth + ip + tcp


def check_build(workdir: Path, submitted: str) -> bool:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_sniffer", workdir / "sniffer.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return False
    cases = [("10.0.0.1", "10.0.0.2", 1234, 80), ("192.168.1.50", "8.8.8.8", 51000, 443)]
    for s_ip, d_ip, sp, dp in cases:
        try:
            r = mod.parse_packet(_frame(s_ip, d_ip, sp, dp))
            if not (r["src_ip"] == s_ip and r["dst_ip"] == d_ip
                    and int(r["src_port"]) == sp and int(r["dst_port"]) == dp):
                return False
        except Exception:
            return False
    return True


MISSION = Mission(
    id="build-02",
    layer="1 The Wire",
    title="Build a packet sniffer (parser)",
    difficulty="medium",
    goal="Implement parse_packet() to extract IPs and ports from raw Ethernet/IPv4/TCP bytes, "
         "then submit BUILT.",
    flag_format="BUILT (after parse_packet works)",
    setup=setup,
    checker=check_build,
    tools=["python3", "struct", "sockets"],
    hints=[
        "Start at the IP header: it begins at offset 14 (after the 14-byte Ethernet header). "
        "ihl = raw[14] & 0x0F; the IP header is ihl*4 bytes long.",
        "src IP = raw[26:30], dst IP = raw[30:34] (that's 14+12 and 14+16). Turn 4 bytes into "
        "a string with socket.inet_ntoa(). protocol = raw[23].",
        "TCP starts at 14 + ihl*4. src_port = struct.unpack('!H', raw[off:off+2])[0]; "
        "dst_port is the next 2 bytes.",
    ],
    debrief=(
        "You can now read packets off the wire byte by byte - the thing Wireshark does for you. "
        "This parsing skill is everything in network forensics and protocol analysis: once you "
        "can walk headers, you can spot tunneled data, malformed packets, and covert channels. "
        "Next build: a ptrace mini-debugger."),
)
