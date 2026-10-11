"""Endless, randomly-generated practice drills (no fixed answer key needed)."""
import ipaddress
import random

from .ui import ask

PORTS = {
    "FTP (control)": 21, "SSH": 22, "Telnet": 23, "SMTP": 25, "DNS": 53,
    "HTTP": 80, "POP3": 110, "IMAP": 143, "HTTPS": 443, "SMB": 445,
    "RDP": 3389, "MySQL": 3306, "PostgreSQL": 5432, "LDAP": 389, "Kerberos": 88,
    "RPC endpoint mapper": 135, "WinRM (HTTP)": 5985,
}


def _subnet_question():
    prefix = random.choice([24, 25, 26, 27, 28, 29, 30, 16, 20, 22, 23])
    host = ipaddress.IPv4Address(random.choice([
        random.randint(0x0A000000, 0x0AFFFFFF),   # 10.x.x.x
        random.randint(0xC0A80000, 0xC0A8FFFF),   # 192.168.x.x
        random.randint(0xAC100000, 0xAC1FFFFF),   # 172.16-31.x.x
    ]))
    net = ipaddress.IPv4Network(f"{host}/{prefix}", strict=False)
    return host, prefix, net


def drill_ports():
    score = total = 0
    print("\nType the default port number, or q to stop.\n")
    while True:
        service, port = random.choice(list(PORTS.items()))
        reply = ask(f"Default port for {service}? ")
        if reply.lower() == "q":
            break
        total += 1
        if reply == str(port):
            score += 1
            print("  Correct!\n")
        else:
            print(f"  It's {port}.\n")
    if total:
        print(f"\nPorts drill: {score}/{total}\n")


def drill_subnet():
    score = total = 0
    print("\nAnswer each part, or q to stop.\n")
    while True:
        host, prefix, net = _subnet_question()
        usable = max(net.num_addresses - 2, 0)
        print(f"Host {host}/{prefix}")
        parts = [
            ("Network address", str(net.network_address)),
            ("Broadcast address", str(net.broadcast_address)),
            ("Usable hosts", str(usable)),
        ]
        stop = False
        for label, expected in parts:
            reply = ask(f"  {label}? ")
            if reply.lower() == "q":
                stop = True
                break
            total += 1
            if reply.replace(",", "") == expected:
                score += 1
                print("    Correct")
            else:
                print(f"    It's {expected}")
        if stop:
            break
        print(f"  (Netmask {net.netmask}, block size {net.num_addresses})\n")
    if total:
        print(f"\nSubnet drill: {score}/{total}\n")


DRILLS = {"ports": drill_ports, "subnet": drill_subnet}
