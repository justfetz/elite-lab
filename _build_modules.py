"""Generates modules/*.json from Python dicts (run once; not part of the app).

All lesson text here is original, written for this course. It deliberately does
NOT reproduce text from any copyrighted book.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"
OUT.mkdir(exist_ok=True)


def L(title, body):
    return {"title": title, "body": body}


def Q(q, options, answer, why):
    return {"q": q, "options": options, "answer": answer, "why": why}


networking = {
    "key": "networking", "title": "Networking fundamentals", "order": 10,
    "lessons": [
        L("The OSI model",
          "Seven layers, bottom to top:\n"
          "  1 Physical     bits on wire, fibre or radio\n"
          "  2 Data Link    frames on one network (Ethernet, MAC, switches)\n"
          "  3 Network      packets between networks (IP, routers)\n"
          "  4 Transport    end-to-end delivery between programs (TCP, UDP, ports)\n"
          "  5 Session      managing conversations\n"
          "  6 Presentation encoding, compression, encryption formats\n"
          "  7 Application  what programs speak (HTTP, DNS, SMTP)\n"
          "Mnemonic: Please Do Not Throw Sausage Pizza Away. Real networks use the simpler "
          "4-layer TCP/IP model, but people still say 'layer 3' and 'layer 7' from OSI."),
        L("IP addresses and CIDR",
          "IPv4 is 32 bits as four 0-255 numbers. CIDR 192.168.1.0/24 means the first 24 bits "
          "are the network, the rest number hosts.\n"
          "  /24 = 256 addresses, 254 usable hosts\n"
          "  usable = 2^(32-prefix) - 2  (network + broadcast are reserved)\n"
          "Private ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16. 127.0.0.1 is loopback."),
        L("TCP vs UDP",
          "TCP: connection-oriented, reliable, ordered. Handshake is SYN -> SYN-ACK -> ACK. "
          "Used by web, SSH, email.\n"
          "UDP: connectionless, no guarantees, low overhead. Used by DNS, video, games.\n"
          "TCP when every byte matters; UDP when speed matters more than perfection."),
        L("Ports",
          "IP finds the machine; the port (0-65535) finds the program. Memorise:\n"
          "  22 SSH   53 DNS   80 HTTP   443 HTTPS   445 SMB   3389 RDP\n"
          "  88 Kerberos   135 RPC   389 LDAP   5985 WinRM  (the Windows/AD cluster)\n"
          "Every open port is a door. Telnet (23) and plain FTP (21) send passwords in clear text."),
        L("DNS",
          "Names to IPs. Your resolver walks root -> TLD -> authoritative servers. Records: "
          "A (IPv4), AAAA (IPv6), CNAME (alias), MX (mail), TXT (SPF/DKIM), NS. Runs on UDP 53 "
          "(TCP for big answers). Answers cache for their TTL."),
        L("Tor and onion routing",
          "Normally a web request is one hop you can trace: your IP talks straight to the server,\n"
          "and anyone watching either end (your ISP, the site) sees who is talking to whom.\n"
          "Tor breaks that link by routing you through THREE volunteer relays, with layered\n"
          "('onion') encryption so no single relay knows both who you are and where you're going:\n\n"
          "  you -> [Guard] -> [Middle] -> [Exit] -> website\n\n"
          "  - Guard (entry): knows your IP, but NOT the site - the payload is still encrypted.\n"
          "  - Middle: knows only 'traffic from Guard goes to Exit'. Neither end.\n"
          "  - Exit: talks to the site and knows the destination, but NOT your IP.\n\n"
          "The onion: your client encrypts the request in three layers - Exit's key inside\n"
          "Middle's key inside Guard's key. Each relay peels ONE layer (the only one it can\n"
          "decrypt) and passes the rest on. So the link between 'who' and 'where' is never held\n"
          "in one place. The path (a 'circuit') rotates every few minutes.\n\n"
          "Key limits to understand: the EXIT sees your traffic in whatever form you sent it - if\n"
          "it isn't HTTPS, the exit can read it, so HTTPS still matters on Tor. Tor hides WHO is\n"
          "talking, not WHAT is said. Defenders care about Tor two ways: as a privacy tool for\n"
          "at-risk users (journalists, activists), and as something to recognise in logs (traffic\n"
          "from known exit-node IPs). '.onion' hidden services go a step further - the server is\n"
          "reached THROUGH the network too, so neither side learns the other's IP."),
    ],
    "quiz": [
        Q("Which OSI layer do routers and IP addresses operate at?",
          ["Layer 2", "Layer 3", "Layer 4", "Layer 7"], 1,
          "Layer 3 (Network) routes packets between networks by IP."),
        Q("Correct order of the TCP three-way handshake?",
          ["SYN, ACK, SYN-ACK", "SYN, SYN-ACK, ACK", "ACK, SYN, SYN-ACK", "SYN-ACK, SYN, ACK"], 1,
          "Client SYN, server SYN-ACK, client ACK."),
        Q("Usable hosts in a /24?", ["256", "255", "254", "128"], 2,
          "256 addresses minus network and broadcast = 254."),
        Q("Which is a private IP?", ["8.8.8.8", "172.20.4.1", "172.32.0.1", "11.0.0.5"], 1,
          "172.16.0.0/12 spans 172.16-172.31, so 172.20.4.1 is private."),
        Q("A live video call most likely uses...", ["TCP", "UDP", "SMTP", "ARP"], 1,
          "Real-time media prefers UDP; a late packet is useless."),
        Q("Which port is Kerberos?", ["88", "389", "445", "3389"], 0,
          "Kerberos is TCP/UDP 88, central to Active Directory auth."),
        Q("In a Tor circuit, which relay knows the website you're visiting?",
          ["the Guard (entry)", "the Middle", "the Exit", "all three"], 2,
          "The Exit talks to the site, so it knows the destination - but not your IP."),
        Q("Why does HTTPS still matter when using Tor?",
          ["Tor is slower without it", "the Exit node can read non-HTTPS traffic",
           "it hides your IP", "it rotates the circuit"], 1,
          "Tor hides WHO is talking, not WHAT is said; the exit sees unencrypted traffic in clear."),
    ],
}

security = {
    "key": "security", "title": "Security principles", "order": 20,
    "lessons": [
        L("The CIA triad",
          "Confidentiality - only authorised people can read it. Integrity - it is not changed "
          "without permission. Availability - it works when needed. For any threat, ask which of "
          "the three it attacks."),
        L("AuthN vs AuthZ",
          "Authentication = proving who you are. Authorisation = what you may do once known. "
          "Factors: something you know (password), have (key/phone), are (biometric). MFA mixes "
          "DIFFERENT factor types; two passwords is not MFA. Phishing-resistant MFA (passkeys, "
          "hardware keys) beats SMS codes."),
        L("Design rules",
          "Least privilege - minimum access needed. Defense in depth - layer controls. Fail "
          "securely - deny on error. Zero trust - verify every request, never trust by location. "
          "Kerckhoffs: assume the attacker knows your design; only the keys are secret."),
        L("Hashing vs encryption",
          "Encryption is reversible with a key (symmetric AES for bulk; asymmetric RSA/ECC for "
          "key exchange and signatures). Hashing is one-way, fixed-size output. Store passwords "
          "with a slow salted hash (bcrypt, scrypt, Argon2) - never plain SHA-256, MD5, or "
          "reversible encryption. TLS uses asymmetric to agree a key, then symmetric for speed."),
        L("Attack classes and defenses",
          "Phishing -> training, phishing-resistant MFA. SQL injection -> parameterised queries. "
          "XSS -> output encoding, CSP. Memory corruption -> memory-safe languages. MITM -> TLS "
          "with cert validation. DDoS -> rate limiting, CDNs. The pattern: most attacks exploit "
          "the line between DATA and CODE, or between trusted and untrusted input."),
        L("Rules of engagement",
          "Only test systems you own or have WRITTEN permission to test. Unauthorised access is a "
          "crime (US CFAA, UK Computer Misuse Act). Practise legally: your own VM lab, deliberately "
          "vulnerable apps (OWASP Juice Shop, DVWA), and CTFs (picoCTF, TryHackMe, Hack The Box). "
          "Found a real bug? Use responsible disclosure or a bug bounty."),
    ],
    "quiz": [
        Q("A DDoS attack mainly targets which CIA property?",
          ["Confidentiality", "Integrity", "Availability", "Authenticity"], 2,
          "It knocks a service offline: availability."),
        Q("Which is true MFA?",
          ["Password + security question", "Password + hardware key", "Two passwords", "Username + password"], 1,
          "Know + have are different factor types."),
        Q("How should passwords be stored?",
          ["AES-encrypted", "MD5", "Slow salted hash (Argon2)", "Plain text, access-controlled"], 2,
          "Slow salted hashes make stolen databases expensive to crack."),
        Q("Main defense against SQL injection?",
          ["A firewall", "Parameterised queries", "Longer passwords", "HTTPS"], 1,
          "Parameterised queries keep user input as data, never code."),
        Q("Giving a program only the access it needs is...",
          ["Defense in depth", "Zero trust", "Least privilege", "Fail securely"], 2,
          "Least privilege limits blast radius if it's compromised."),
    ],
}

windows = {
    "key": "windows", "title": "Windows internals", "order": 30,
    "lessons": [
        L("Processes",
          "A process is the container for a running program: private virtual memory, an image "
          "(.exe), a PID and a parent, an access TOKEN (its security identity), a handle table "
          "(open files/keys/objects), and one or more threads. Threads run code; the process just "
          "holds resources. A process can normally only do what its token's user can do."),
        L("Access tokens and privileges",
          "The token answers 'who is this and what may it do': the user SID, group SIDs, and "
          "privileges (e.g. SeDebugPrivilege, SeBackupPrivilege). SYSTEM is the most powerful local "
          "identity. Privilege escalation is almost always about getting a more powerful token - by "
          "abusing a service, a privilege, or a misconfiguration."),
        L("Services",
          "A service is a background process managed by the Service Control Manager (services.exe). "
          "It can start at boot with no user logged in, usually runs under LocalSystem/LocalService/"
          "NetworkService, and is configured under HKLM\\SYSTEM\\CurrentControlSet\\Services. Many "
          "share svchost.exe. Because they often run as SYSTEM and auto-start, misconfigured services "
          "(e.g. a binary users can overwrite, or an unquoted service path) are classic privilege-"
          "escalation paths and malware persistence."),
        L("The Windows API and system calls",
          "Programs can't touch hardware directly; they ask the OS through the Win32 API "
          "(kernel32/advapi32/user32.dll). Calls funnel down to ntdll.dll (the Native API) and then a "
          "syscall into the kernel, which does the work and checks permissions. A program's API calls "
          "reveal intent: OpenProcess + WriteProcessMemory + CreateRemoteThread together signal code "
          "injection, which is exactly what EDR watches for."),
        L("The registry and autostart",
          "The registry is Windows' central config database (hives like HKLM and HKCU). Attackers "
          "and admins both care about autostart extensibility points (ASEPs): Run/RunOnce keys, "
          "services, scheduled tasks, startup folders. Enumerating every place code can start is the "
          "core of both malware persistence and hunting for it (Autoruns lists them all)."),
        L("Objects, handles and securable resources",
          "The Object Manager tracks kernel objects (files, processes, registry keys, mutexes...). "
          "You get a HANDLE to one, and each access is checked against the object's security "
          "descriptor (its owner and ACL) using your token. 'Can this user open this file for write?' "
          "is an access check: token vs ACL. Most Windows privilege bugs are a wrong answer to that "
          "question."),
    ],
    "quiz": [
        Q("What carries a process's security identity?",
          ["Its PID", "Its access token", "Its handle table", "Its parent process"], 1,
          "The token holds the user SID, groups and privileges."),
        Q("Most Windows services run under which kind of account?",
          ["A normal user", "Privileged accounts like LocalSystem", "No account", "The guest account"], 1,
          "LocalSystem/LocalService/NetworkService - why services are a privesc target."),
        Q("Which API combination suggests code injection?",
          ["CreateFile + ReadFile", "OpenProcess + WriteProcessMemory + CreateRemoteThread",
           "RegOpenKey + RegCloseKey", "GetSystemTime + Sleep"], 1,
          "Open another process, write into it, run a thread there."),
        Q("An 'access check' compares...",
          ["two passwords", "a token against an object's security descriptor",
           "a hash against a salt", "a port against a firewall rule"], 1,
          "Your token's SIDs/privileges vs the object's owner and ACL."),
        Q("Where do services and Run keys both matter for attackers?",
          ["Encryption", "Autostart / persistence", "Networking", "Compression"], 1,
          "They are autostart extensibility points - ways to survive reboot."),
    ],
}

linux = {
    "key": "linux", "title": "Linux fundamentals", "order": 40,
    "lessons": [
        L("Everything is a file; the shell",
          "Files, devices, even processes appear under the filesystem. The shell (bash/zsh) glues "
          "small tools with pipes: `cmd1 | cmd2` feeds one's output into the next. Core tools: ls, "
          "cd, cat, less, grep (search), find (locate files), awk/cut (columns), sort, uniq, wc. "
          "Learning to chain these is 80% of day-to-day Linux and log analysis."),
        L("Permissions and users",
          "Each file has an owner, a group, and rwx bits for owner/group/other (e.g. 0640). root "
          "(uid 0) can do anything. sudo runs one command as root. Least privilege on Linux = correct "
          "ownership and mode, plus not running as root. SUID binaries run as their owner regardless "
          "of who launches them - a classic privilege-escalation hunting ground."),
        L("Processes and networking from the shell",
          "ps/top show processes; kill sends signals. ss -tulpn shows listening sockets and the "
          "program behind each port - the Linux answer to 'what's exposed on this box'. systemctl "
          "manages services (the systemd equivalent of Windows services). Logs live in journalctl "
          "and /var/log."),
    ],
    "quiz": [
        Q("Which command shows listening ports and their programs?",
          ["ls -l", "ss -tulpn", "chmod 777", "grep -r"], 1,
          "ss -tulpn: TCP/UDP listening sockets with PID/program."),
        Q("A SUID binary runs with...",
          ["the caller's privileges", "the file owner's privileges", "no privileges", "root always"], 1,
          "It runs as its owner - why misconfigured SUID is a privesc path."),
        Q("What does `grep error app.log | wc -l` do?",
          ["Deletes errors", "Counts lines containing 'error'", "Sorts the log", "Opens an editor"], 1,
          "grep filters to matching lines, wc -l counts them."),
    ],
}

for mod in (networking, security, windows, linux):
    (OUT / f"{mod['key']}.json").write_text(json.dumps(mod, indent=2, ensure_ascii=True))

print("wrote", len(list(OUT.glob("*.json"))), "modules")
