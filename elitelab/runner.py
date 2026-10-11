"""`elite run <tool> ...` - the command-a-tool-and-learn-the-lesson loop.

It runs a REAL security tool against a target you specify, captures the output,
then interprets it and teaches the lesson. A safety gate refuses network tools
aimed at anything outside your own lab (localhost / RFC1918) unless you pass
--authorized to assert written permission. If the tool isn't installed, it still
teaches using a bundled sample so you see the format.

This is intentionally extensible: add an entry to TOOLS with a command and an
interpret(output)->str function, and `elite run <name>` works.
"""
import ipaddress
import re
import shutil
import subprocess

from .ui import say, rule

WELL_KNOWN = {
    21: "FTP (cleartext)", 22: "SSH", 23: "Telnet (cleartext!)", 25: "SMTP",
    53: "DNS", 80: "HTTP", 88: "Kerberos", 110: "POP3", 135: "MSRPC",
    139: "NetBIOS", 143: "IMAP", 389: "LDAP", 443: "HTTPS", 445: "SMB",
    3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 5985: "WinRM",
}


def _target_is_lab(args):
    """True if every host-looking arg is localhost or RFC1918 (your own lab)."""
    hosts = [a for a in args if re.match(r"^[\d.]+$", a) or a in ("localhost",)]
    if not hosts:
        return True  # no explicit target (e.g. --help); let the tool decide
    for h in hosts:
        if h == "localhost":
            continue
        try:
            ip = ipaddress.ip_address(h)
        except ValueError:
            return False
        if not (ip.is_private or ip.is_loopback):
            return False
    return True


# ---------- interpreters ----------
def interpret_nmap(output):
    ports = re.findall(r"^(\d+)/tcp\s+open\s+(\S+)", output, re.MULTILINE)
    lines = ["LESSON - reading an nmap result:"]
    if not ports:
        lines.append("  No open TCP ports parsed. A fully filtered host (no replies) usually "
                     "means a firewall is dropping packets - itself a finding.")
    else:
        lines.append(f"  {len(ports)} open port(s). Every open port is a service = attack surface:")
        for p, svc in ports:
            note = WELL_KNOWN.get(int(p), "")
            flag = "  <-- cleartext, avoid" if int(p) in (21, 23) else ""
            lines.append(f"    {p}/tcp {svc}  {note}{flag}")
        lines.append("  Ask of EACH: what program is this, does it need to be exposed, and is it "
                     "patched? Closing or firewalling what you don't need is hardening in one move.")
    lines.append("  Next: `nmap -sV <target>` to get versions, then check each version for known "
                 "CVEs. DEFENSE side: this same scan is what you run on your OWN network to find "
                 "doors before an attacker does.")
    return "\n".join(lines)


SAMPLE_NMAP = """Starting Nmap
Nmap scan report for lab-host (10.0.0.50)
Host is up (0.00040s latency).
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
445/tcp  open  microsoft-ds
3389/tcp open  ms-wbt-server
Nmap done: 1 IP address (1 host up) scanned
"""

TOOLS = {
    "nmap": {
        "needs_target": True,
        "interpret": interpret_nmap,
        "sample": SAMPLE_NMAP,
        "study": "what do open ports tell an attacker",
    },
}


def run(args):
    if not args.toolargs:
        print("Usage: elite run <tool> [args...]   e.g. elite run nmap 127.0.0.1")
        print("Known tutors:", ", ".join(TOOLS) + ".  Other tools run with a generic lesson.")
        return
    authorized = "--authorized" in args.toolargs
    toolargs = [a for a in args.toolargs if a != "--authorized"]
    tool, rest = toolargs[0], toolargs[1:]
    spec = TOOLS.get(tool, {})

    if spec.get("needs_target") and not authorized and not _target_is_lab(rest):
        rule("Refused - target outside your lab")
        say("That target is not localhost or a private (RFC1918) address, so I won't run an "
            "active tool at it. Scanning or attacking systems you don't own or have WRITTEN "
            "permission for is illegal. Point it at your own lab (127.0.0.1, 10.x, 172.16-31.x, "
            "192.168.x), or re-run with --authorized to assert you have permission.")
        return

    have = shutil.which(tool)
    if have:
        rule(f"Running: {tool} {' '.join(rest)}")
        try:
            proc = subprocess.run([tool, *rest], capture_output=True, text=True, timeout=300)
            output = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            output = "(timed out after 5 min)"
        except Exception as e:
            output = f"(failed to run: {e})"
        print(output)
    else:
        rule(f"{tool} is not installed - teaching from a sample instead")
        say(f"Install {tool} to run it for real. Here's a representative output so you learn the "
            "shape of the result:")
        output = spec.get("sample", "")
        print("\n" + output)

    rule("Debrief")
    if spec.get("interpret"):
        say(spec["interpret"](output))
    else:
        say(f"'{tool}' ran. Read its output above carefully: what did it reveal, and what would "
            "you do next with it? There's no built-in tutor for this tool yet.")
    if spec.get("study"):
        say(f"\nGo deeper from your books:  python3 study_books.py ask \"{spec['study']}\"")
    print()
