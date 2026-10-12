"""Generates drills/commands.json - the command bank for muscle-memory drills.
Original content: standard commands every operator should have in their fingers,
seeded by RTFM-style references. `accept` holds extra regex variants; an exact
(whitespace/case-insensitive) match to `answer` always passes too."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "drills"
OUT.mkdir(exist_ok=True)


def C(id, platform, prompt, answer, why, accept=None):
    return {"id": id, "platform": platform, "prompt": prompt, "answer": answer,
            "why": why, "accept": accept or []}


bank = [
    # --- recon / nmap (Wire) ---
    C("nmap-default", "nmap", "Scan the default top-1000 TCP ports of 10.0.0.5",
      "nmap 10.0.0.5", "Bare nmap = top 1000 TCP ports.",
      [r"nmap (?!.*-p)10\.0\.0\.5"]),
    C("nmap-allports", "nmap", "Scan ALL 65535 TCP ports of 10.0.0.5",
      "nmap -p- 10.0.0.5", "-p- means every TCP port.",
      [r"nmap .*-p-.*10\.0\.0\.5", r"nmap 10\.0\.0\.5 -p-"]),
    C("nmap-sv", "nmap", "Detect service versions on 10.0.0.5",
      "nmap -sV 10.0.0.5", "-sV fingerprints the software/version behind each port.",
      [r"nmap .*-sv.*10\.0\.0\.5"]),
    C("nmap-syn", "nmap", "Fast SYN (half-open) scan of the 10.0.0.0/24 subnet",
      "nmap -sS 10.0.0.0/24", "-sS never finishes the handshake: faster, quieter.",
      [r"nmap .*-ss.*10\.0\.0\.0/24"]),
    # --- linux enumeration (Host/Door) ---
    C("ss-listen", "linux", "List listening TCP/UDP sockets with the owning program",
      "ss -tulpn", "t=tcp u=udp l=listening p=process n=numeric.", [r"ss -[a-z]*"]),
    C("sudo-l", "linux", "Show what the current user may run via sudo",
      "sudo -l", "First thing to check for Linux privesc."),
    C("find-suid", "linux", "Find SUID binaries anywhere on the filesystem",
      "find / -perm -4000 2>/dev/null", "SUID binaries run as their owner - a privesc hunt.",
      [r"find / -perm -4000.*"]),
    C("ps-aux", "linux", "List all running processes (full detail)",
      "ps aux", "Classic full process listing."),
    # --- windows / AD PowerShell (Domain/Host) ---
    C("ad-computers", "powershell", "List every computer in the domain",
      "Get-ADComputer -Filter *", "Enumerates all domain-joined machines.",
      [r"get-adcomputer -filter \*"]),
    C("ad-dcs", "powershell", "List all domain controllers",
      "Get-ADDomainController -Filter *", "DCs are the crown jewels of AD.",
      [r"get-addomaincontroller -filter \*"]),
    C("ad-dadmins", "powershell", "Show the members of Domain Admins",
      "Get-ADGroupMember 'Domain Admins'", "Who holds the keys to the domain.",
      [r"get-adgroupmember ['\"]?domain admins['\"]?"]),
    C("local-admins", "powershell", "List members of the local Administrators group",
      "Get-LocalGroupMember Administrators", "Who is admin on THIS box.",
      [r"get-localgroupmember administrators"]),
    C("net-listen", "powershell", "Show listening TCP connections (PowerShell)",
      "Get-NetTCPConnection -State Listen", "PowerShell's answer to 'what's exposed here'.",
      [r"get-nettcpconnection -state listen"]),
    C("whoami-priv", "windows", "Show your token's privileges (cmd/PowerShell)",
      "whoami /priv", "SeImpersonate/SeBackup/SeDebug here are privesc gold."),
    C("failed-logons", "powershell", "Find failed-logon events in the Security log",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625}",
      "Event 4625 = failed logon: spot brute force.",
      [r"get-winevent -filterhashtable @\{logname=['\"]security['\"];id=4625\}"]),
    # --- password cracking (Door) ---
    C("john-md5", "john", "Crack raw-MD5 hashes in hashes.txt with John and rockyou.txt",
      "john --format=raw-md5 --wordlist=rockyou.txt hashes.txt",
      "Tell John the hash format and give it a wordlist.",
      [r"john --format=raw-md5 --wordlist=\S*rockyou\S* hashes\.txt"]),
    C("hashcat-md5", "hashcat", "Crack MD5 hashes in hashes.txt with hashcat and rockyou.txt",
      "hashcat -m 0 -a 0 hashes.txt rockyou.txt",
      "-m 0 = MD5, -a 0 = straight wordlist attack.",
      [r"hashcat -m 0 -a 0 hashes\.txt \S*rockyou\S*"]),
    C("john-show", "john", "Show the passwords John has already cracked for hashes.txt",
      "john --show hashes.txt", "Reads cracked results from the pot file."),
    # --- web (App) ---
    C("curl-head", "curl", "Fetch only the response headers of http://10.0.0.5",
      "curl -I http://10.0.0.5", "-I = HEAD request: headers only.",
      [r"curl -i http://10\.0\.0\.5"]),
    C("curl-verbose", "curl", "Make a verbose request to http://10.0.0.5 (show the exchange)",
      "curl -v http://10.0.0.5", "-v shows the full request/response, TLS and all.",
      [r"curl -v http://10\.0\.0\.5"]),
    C("dig-mx", "dig", "Look up the MX (mail) records for example.com",
      "dig MX example.com", "MX = which server receives the domain's mail.",
      [r"dig mx example\.com", r"dig example\.com mx"]),
    C("sqlmap-basic", "sqlmap", "Test the id param of http://10.0.0.5/item?id=1 for SQLi, no prompts",
      "sqlmap -u 'http://10.0.0.5/item?id=1' --batch",
      "--batch takes defaults so it runs unattended.",
      [r"sqlmap -u ['\"]?http://10\.0\.0\.5/item\?id=1['\"]? --batch"]),
]

(OUT / "commands.json").write_text(json.dumps(bank, indent=2, ensure_ascii=True))
print(f"wrote {len(bank)} commands to drills/commands.json")
