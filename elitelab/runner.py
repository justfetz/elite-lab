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


# flags whose value is a target (sqlmap -u, gobuster -u, --url=, etc.)
_TARGET_FLAGS = {"u", "url", "host", "target", "t", "domain"}
# common file extensions, so a wordlist/key filename isn't mistaken for a host
_FILE_EXT = {"txt", "lst", "log", "pem", "json", "xml", "html", "htm", "csv",
             "conf", "cfg", "db", "py", "key", "pub", "md", "yaml", "yml", "ini",
             "sh", "gz", "zip", "pcap"}


def _looks_like_host(tok):
    if tok == "localhost":
        return True
    if re.match(r"^[\d.]+(/\d+)?$", tok):              # bare IP or CIDR
        return True
    if "." in tok and re.search(r"[A-Za-z]", tok):     # a dotted name...
        tld = tok.rsplit(".", 1)[-1].lower()
        if tld in _FILE_EXT:                            # ...but a filename, not a host
            return False
        return bool(re.match(r"^[A-Za-z]{2,24}$", tld))
    return False


def _hosts_in(args):
    """Pull every host/URL/CIDR target out of the args - including glued forms like
    -uhttp://x and --url=http://x - while ignoring wordlist/key FILENAMES. Fails
    CLOSED: a URL, an explicit -u value, or a domain is judged by the gate."""
    hosts = []
    for a in args:
        forced = False                                 # came from a URL or -u/--url
        if a.startswith("--"):
            m = re.match(r"^--([A-Za-z][\w-]*)[=:](.*)$", a)
            if not m:
                continue                               # a bare long flag like --authorized
            forced = m.group(1).lower() in _TARGET_FLAGS
            a = m.group(2)
        elif a.startswith("-"):
            name, a = a[1:2], a[2:]                     # -u<value> or -sV
            if not a:
                continue
            forced = name.lower() in _TARGET_FLAGS
        if re.match(r"^\w+://", a):                     # had a scheme -> definitely a target
            forced = True
            a = re.sub(r"^\w+://", "", a)
        a = a.split("@")[-1].split("?")[0]             # strip userinfo / query
        host = a if re.match(r"^[\d.]+/\d+$", a) else a.split("/")[0]
        if re.search(r":\d+$", host):
            host = host.rsplit(":", 1)[0]
        if host and (forced or _looks_like_host(host)):
            hosts.append(host)
    return hosts


def _target_is_lab(args):
    """True only if EVERY host-looking arg is localhost or private (your own lab).
    Unknown/unparseable domains and public CIDRs are rejected (fail closed)."""
    hosts = _hosts_in(args)
    if not hosts:
        return True  # no explicit target (e.g. --help); let the tool decide
    for h in hosts:
        if h == "localhost" or h.endswith(".local"):
            continue
        try:
            net = ipaddress.ip_network(h, strict=False)   # handles bare IP and CIDR
        except ValueError:
            return False   # a real hostname/domain -> not your lab
        if not (net.is_private or net.is_loopback):
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

def interpret_sqlmap(output):
    low = output.lower()
    lines = ["LESSON - reading sqlmap:"]
    if "is vulnerable" in low or "injectable" in low or "parameter" in low and "vulnerab" in low:
        params = re.findall(r"parameter '([^']+)'", output)
        dbms = re.findall(r"back-end DBMS: ([^\n]+)", output)
        lines.append("  Injectable parameter found" + (f": {params[0]}" if params else "") + ".")
        if dbms:
            lines.append(f"  Back-end DBMS identified: {dbms[0].strip()}.")
        lines.append("  That means user input is reaching the SQL engine as CODE. From here an "
                     "attacker dumps tables, reads files, sometimes runs commands.")
    else:
        lines.append("  No injection reported here. A well-parameterized app gives sqlmap nothing.")
    lines.append("  DEFENSE: parameterized queries / prepared statements. See the app-01 mission.")
    return "\n".join(lines)


def interpret_john(output):
    cracked = re.findall(r"^(\S+):(\S+)", output, re.MULTILINE)
    # john --show prints user:password lines
    lines = ["LESSON - reading John the Ripper:"]
    real = [(u, p) for u, p in cracked if p and ":" not in p]
    if real:
        lines.append(f"  {len(real)} hash(es) cracked. Each one was a weak/common password a "
                     "wordlist guessed, because the hashing was fast and/or unsalted.")
    else:
        lines.append("  Nothing cracked from this output. Strong, slow, salted hashing resists "
                     "wordlist attacks - which is exactly the point.")
    lines.append("  DEFENSE: store passwords with bcrypt/scrypt/Argon2 at a high cost. See crack-01.")
    return "\n".join(lines)


def interpret_gobuster(output):
    found = re.findall(r"^(/\S+)\s+\(Status:\s*(\d+)", output, re.MULTILINE)
    lines = ["LESSON - reading gobuster/ffuf:"]
    if found:
        lines.append(f"  {len(found)} path(s) discovered that weren't linked anywhere:")
        for path, status in found[:8]:
            lines.append(f"    {status}  {path}")
        lines.append("  Hidden endpoints = attack surface the developer forgot about (admin "
                     "panels, backups, .git). Always map before you test.")
    else:
        lines.append("  No hidden paths found with this wordlist. Try a bigger/different list.")
    lines.append("  DEFENSE: don't rely on secrecy of URLs; protect every endpoint, remove "
                 "backups and .git from web roots.")
    return "\n".join(lines)


SAMPLE_SQLMAP = """\
[*] starting @ 12:00:00
[12:00:01] [INFO] testing connection to the target URL
[12:00:03] [INFO] GET parameter 'id' is 'MySQL >= 5.0 boolean-based blind' injectable
[12:00:04] [INFO] the back-end DBMS is MySQL
GET parameter 'id' is vulnerable.
back-end DBMS: MySQL
"""
SAMPLE_JOHN = """\
ceo:superman
reception:shadow
2 password hashes cracked, 3 left
"""
SAMPLE_GOBUSTER = """\
/admin                (Status: 301)
/backup               (Status: 200)
/.git/config          (Status: 200)
/login                (Status: 200)
"""

TOOLS = {
    "nmap": {"needs_target": True, "interpret": interpret_nmap, "sample": SAMPLE_NMAP,
             "study": "what do open ports tell an attacker"},
    "sqlmap": {"needs_target": True, "interpret": interpret_sqlmap, "sample": SAMPLE_SQLMAP,
               "study": "how does SQL injection work"},
    "john": {"needs_target": False, "interpret": interpret_john, "sample": SAMPLE_JOHN,
             "study": "why is fast unsalted hashing dangerous"},
    "gobuster": {"needs_target": True, "interpret": interpret_gobuster, "sample": SAMPLE_GOBUSTER,
                 "study": "how bug hunters map an app"},
    "ffuf": {"needs_target": True, "interpret": interpret_gobuster, "sample": SAMPLE_GOBUSTER,
             "study": "how bug hunters map an app"},
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
