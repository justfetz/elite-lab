"""Generates modules/windows-ps.json - advanced PowerShell for enumeration & privesc.
Original content. Enumeration/ACL commands are standard admin cmdlets; use them only
on systems you own or are authorized to administer."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


ps = {
    "key": "windows-ps", "title": "PowerShell for security", "order": 35,
    "lessons": [
        L("Objects, not text - why it matters",
          "PowerShell pipes OBJECTS with named fields, not lines of text. That makes it a query "
          "language over the whole machine - close to SQL, which your background makes intuitive:\n"
          "  Get-Process | Where-Object CPU -gt 100 | Sort-Object CPU -Descending | Select Name,Id,CPU\n"
          "reads as SELECT name,id,cpu FROM processes WHERE cpu>100 ORDER BY cpu DESC. Because it is "
          "built on .NET it can reach processes, services, the registry, event logs, the firewall, "
          "WMI/CIM, and Active Directory - and it is already on every Windows box, which is why both "
          "admins and attackers live in it."),
        L("Local enumeration cheat-set",
          "The first questions on any host - what is here, what runs, what listens:\n"
          "  Get-Process                         running programs\n"
          "  Get-Service | ? Status -eq Running  running services\n"
          "  Get-CimInstance Win32_Service | select Name,StartName,PathName   service account + binary\n"
          "  Get-NetTCPConnection -State Listen  open local ports and owning PID\n"
          "  Get-LocalUser ; Get-LocalGroupMember Administrators   who is local admin\n"
          "  Get-ScheduledTask | ? State -ne Disabled             autostart via tasks\n"
          "  Get-ItemProperty 'HKLM:\\...\\CurrentVersion\\Run'      autostart via registry\n"
          "For each result ask: what is this, and should it be here? That is threat hunting."),
        L("Enumerating the whole domain",
          "With RSAT's ActiveDirectory module (on a domain-joined box with rights) you can map an "
          "entire organization:\n"
          "  Get-ADDomainController -Filter *        every domain controller (the crown jewels)\n"
          "  Get-ADComputer -Filter * -Properties OperatingSystem | select Name,OperatingSystem\n"
          "                                          every computer in the domain\n"
          "  Get-ADUser -Filter * -Properties LastLogonDate        every user account\n"
          "  Get-ADGroupMember 'Domain Admins'       who holds the keys\n"
          "This is exactly what an attacker runs after landing one credential - and what BloodHound "
          "collects automatically. DEFENSE: tiering, limiting who can read sensitive attributes, and "
          "alerting on bulk AD enumeration."),
        L("How permissions leak",
          "Most privilege escalation is a wrong answer to 'who can touch this?'. Common leaks:\n"
          "  Get-Acl C:\\path | Format-List       read an object's owner + ACL\n"
          "  icacls C:\\path                       quick ACL dump; look for (F)/(M) for Users/Everyone\n"
          "Leaks to hunt:\n"
          "  - a service whose BINARY or folder is writable by normal users (replace it -> runs as "
          "the service account, often SYSTEM)\n"
          "  - an unquoted service path with spaces (C:\\Program Files\\... -> C:\\Program.exe hijack)\n"
          "  - over-broad shares/ACLs granting Everyone or Authenticated Users Modify\n"
          "  - nested group membership: a user is admin somewhere via a group inside a group\n"
          "  - dangerous privileges on your token (whoami /priv): SeImpersonate, SeBackup, SeDebug\n"
          "Each is least-privilege violated. DEFENSE: correct ACLs, quoted paths, minimal group "
          "nesting, and removing privileges nobody needs."),
        L("Living off the land, and how it is caught",
          "Attackers prefer built-in PowerShell because it looks like admin work and drops no malware "
          "('living off the land'). So defenders instrument it:\n"
          "  - Script Block Logging records the actual code that ran (event ID 4104), even obfuscated\n"
          "  - AMSI lets AV scan scripts in memory as they execute\n"
          "  - Constrained Language Mode limits what untrusted scripts can do\n"
          "  - Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625}   failed logons (brute force)\n"
          "Knowing both sides - what the cmdlets can do and how they are logged - is the whole game."),
    ],
    "quiz": [
        Q("What does PowerShell pass between pipeline stages?",
          ["Plain text lines", "Objects with named fields", "Bytes", "JSON only"], 1,
          "Objects with properties - why it feels like querying the machine."),
        Q("Which lists every domain controller?",
          ["Get-Process", "Get-ADDomainController -Filter *", "Get-Service", "Get-LocalUser"], 1,
          "The ActiveDirectory module's Get-ADDomainController enumerates DCs."),
        Q("A service whose binary is writable by normal users lets you...",
          ["read email", "run code as the service account (often SYSTEM)", "change the wallpaper",
           "nothing"], 1,
          "Replace the binary; it runs with the service's privileges at next start."),
        Q("Which event ID records failed logons (useful for spotting brute force)?",
          ["4104", "4625", "1102", "7045"], 1,
          "4625 = failed logon. (4104 is script block logging.)"),
        Q("Why do attackers favor built-in PowerShell?",
          ["It is faster than C", "It drops no malware and looks like admin activity",
           "It is encrypted", "It bypasses all logging"], 1,
          "'Living off the land' blends in - though 4104/AMSI still catch much of it."),
    ],
}

(OUT / "windows-ps.json").write_text(json.dumps(ps, indent=2, ensure_ascii=True))
print("wrote windows-ps.json")
