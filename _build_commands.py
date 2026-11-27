"""Generates drills/commands.json - the command bank for muscle-memory drills.
Original content: standard commands every operator should have in their fingers,
seeded by RTFM-style references. `accept` holds extra regex variants; an exact
(whitespace/case-insensitive) match to `answer` always passes too.

A drill may also carry `wrong`: one plausible answer that is NOT right and that the
patterns must reject. Every PowerShell drill has one, and its own answer matches its
own patterns; tests/test_pwsh_assets.py and the Pester suite check both, and the
Pester suite also parses every PowerShell answer with the PowerShell parser."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "drills"
OUT.mkdir(exist_ok=True)


def C(id, platform, prompt, answer, why, accept=None, wrong=None):
    entry = {"id": id, "platform": platform, "prompt": prompt, "answer": answer,
             "why": why, "accept": accept or []}
    if wrong is not None:
        entry["wrong"] = wrong
    return entry


# --- building blocks for the PowerShell patterns -------------------------------------
# Patterns are matched case-insensitively against the answer with runs of whitespace
# collapsed to one space, so they are written in lower case with single spaces.
# They accept what a practised administrator would type for the same job - the short
# names where and select, a pipe without spaces, columns in another order - and nothing
# that would not run or would answer a different question.
Q = r"['\"]?"                               # an optional quote of either kind
QQ = r"['\"]"                               # a quote that has to be there
SP = r" ?"                                  # an optional space
PIPE = r" ?\| ?"                            # a pipe, spaces optional
WHERE = r"(where-object|where|\?)"          # Where-Object and its two short names
SELECT = r"(select-object|select)"          # Select-Object and its short name


def where(prop, op, word, literal=False):
    """Where-Object in both spellings.

    `Where-Object Prop -op word` takes the word bare or quoted. Inside a script block,
    `{ $_.Prop -op 'word' }`, a bare word is a parse error, so the quotes are required.
    literal=True is for a value that is not a string, such as $null or $true.
    """
    simple = word if literal else Q + word + Q
    block = word if literal else QQ + word + QQ
    return [WHERE + r" (-property )?" + prop + " " + op + " " + simple,
            WHERE + r" \{" + SP + r"\$_\." + prop + " " + op + " " + block + SP + r"\}"]


def select(*props):
    """Select-Object with exactly these properties, in any order."""
    one = "(" + "|".join(props) + ")"
    each_once = "".join(r"(?=.*\b" + p + r"\b)" for p in props)
    return SELECT + r" (-property )?" + each_once + one + ("(," + SP + one + "){%d}" % (len(props) - 1))


def piped(left, rights):
    """left | right, for every spelling of the right-hand side."""
    if isinstance(rights, str):
        rights = [rights]
    return [left + PIPE + right for right in rights]


def event_filter(log, event_id, extra=""):
    """Get-WinEvent -FilterHashtable @{LogName='..';Id=..}: spaces optional, either key
    first, and the log name quoted - a bare word in a hashtable is taken as a command."""
    name = "logname" + SP + "=" + SP + QQ + log + QQ
    ident = "id" + SP + "=" + SP + str(event_id)
    sep = SP + ";" + SP
    head = r"get-winevent -filterhashtable @\{" + SP
    tail = extra + SP + r"\}"
    return [head + name + sep + ident + tail, head + ident + sep + name + tail]


def any_order(command, *parts):
    """command followed by each of these parameters exactly once, in any order."""
    each_once = "".join("(?=.* -" + part + ")" for part in parts)
    return command + each_once + "( -(" + "|".join(parts) + ")){%d}" % len(parts)


FINANCE = Q + r"c:\\shares\\finance" + Q            # C:\Shares\Finance, quoted or not
AGENT = Q + r"c:\\tools\\agent\.exe" + Q            # C:\Tools\agent.exe, quoted or not
PATH_ARG = r"(-(path|literalpath) )?"
ACL = r"\(get-acl " + PATH_ARG + FINANCE + r"\)"
CIM_SERVICE = r"get-ciminstance (-classname )?win32_service"
CIM_PROCESS = r"get-ciminstance (-classname )?win32_process"
SPOOLER = r" -filter \"name" + SP + "=" + SP + r"'spooler'\""


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
      [r"get-adcomputer -filter \*"],
      wrong="Get-ADComputer *"),
    C("ad-dcs", "powershell", "List all domain controllers",
      "Get-ADDomainController -Filter *", "DCs are the crown jewels of AD.",
      [r"get-addomaincontroller -filter \*"],
      wrong="Get-ADDomain"),
    C("ad-dadmins", "powershell", "Show the members of Domain Admins",
      "Get-ADGroupMember 'Domain Admins'", "Who holds the keys to the domain.",
      [r"get-adgroupmember ['\"]?domain admins['\"]?"],
      wrong="Get-ADGroup 'Domain Admins'"),
    C("local-admins", "powershell", "List members of the local Administrators group",
      "Get-LocalGroupMember Administrators", "Who is admin on THIS box.",
      [r"get-localgroupmember administrators"],
      wrong="Get-LocalGroup Administrators"),
    C("net-listen", "powershell", "Show listening TCP connections (PowerShell)",
      "Get-NetTCPConnection -State Listen", "PowerShell's answer to 'what's exposed here'.",
      [r"get-nettcpconnection -state listen"],
      wrong="Get-NetTCPConnection -State Established"),
    C("whoami-priv", "windows", "Show your token's privileges (cmd/PowerShell)",
      "whoami /priv", "SeImpersonate/SeBackup/SeDebug here are privesc gold."),
    C("failed-logons", "powershell", "Find failed-logon events in the Security log",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625}",
      "Event 4625 = failed logon: spot brute force.",
      [r"get-winevent -filterhashtable @\{logname=['\"]security['\"];id=4625\}"],
      wrong="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624}"),
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
    # === PowerShell for administrators and defenders (issue #1) ===========================
    # Every one of these reads; none of them changes a machine. Each has a `wrong`.
    # --- event logs ---
    C("ps-evt-newest", "powershell", "Show the 50 newest events in the System log",
      "Get-WinEvent -LogName System -MaxEvents 50",
      "-MaxEvents caps the count, and Get-WinEvent returns the newest first. "
      "-Newest belongs to the older Get-EventLog.",
      [any_order("get-winevent", "logname " + Q + "system" + Q, "maxevents 50")],
      wrong="Get-WinEvent -LogName System -Newest 50"),
    C("ps-evt-logon-ok", "powershell", "List successful logons (event 4624) from the Security log",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=4624}",
      "4624 is a logon that worked; 4625 is one that failed. The hashtable filters at the source, "
      "which is far faster than filtering afterwards.",
      event_filter("security", 4624),
      wrong="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625}"),
    C("ps-evt-last-day", "powershell", "Find failed logons (event 4625) from the last 24 hours",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625;StartTime=(Get-Date).AddDays(-1)}",
      "StartTime is the oldest event you want. EndTime with the same value would return everything "
      "BEFORE yesterday.",
      event_filter("security", 4625, SP + ";" + SP + "starttime" + SP + "=" + SP
                   + r"\(get-date\)\.add(days\(-1\)|hours\(-24\))"),
      wrong="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4625;EndTime=(Get-Date).AddDays(-1)}"),
    C("ps-evt-account-created", "powershell", "Find user accounts that were created (event 4720)",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=4720}",
      "4720 = a user account was created. 4726 is the opposite: an account was deleted.",
      event_filter("security", 4720),
      wrong="Get-WinEvent -FilterHashtable @{LogName='Security';Id=4726}"),
    C("ps-evt-log-cleared", "powershell", "Find when the Security audit log was cleared (event 1102)",
      "Get-WinEvent -FilterHashtable @{LogName='Security';Id=1102}",
      "1102 is written to the Security log itself when someone clears it. A cleared log is a finding.",
      event_filter("security", 1102),
      wrong="Get-WinEvent -FilterHashtable @{LogName='System';Id=1102}"),
    C("ps-evt-service-installed", "powershell",
      "Find services that were installed on this machine (event 7045)",
      "Get-WinEvent -FilterHashtable @{LogName='System';Id=7045}",
      "7045 lives in the System log (the Security log's version is 4697). A new service is a "
      "common way to stay on a machine.",
      event_filter("system", 7045),
      wrong="Get-WinEvent -FilterHashtable @{LogName='Security';Id=7045}"),
    C("ps-evt-scriptblock", "powershell", "Read PowerShell script-block logging events (event 4104)",
      "Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational';Id=4104}",
      "4104 records the script text that ran. It is in the Operational log, not the classic "
      "'Windows PowerShell' log.",
      event_filter("microsoft-windows-powershell/operational", 4104),
      wrong="Get-WinEvent -FilterHashtable @{LogName='Windows PowerShell';Id=4104}"),
    C("ps-evt-list-logs", "powershell", "List every event log on this machine with its record count",
      "Get-WinEvent -ListLog *",
      "-ListLog describes the logs. -LogName * asks for the events themselves, from every log at once.",
      [r"get-winevent -listlog " + Q + r"\*" + Q],
      wrong="Get-WinEvent -LogName *"),
    C("ps-evt-from-file", "powershell", r"Read the events in the saved log file C:\Cases\security.evtx",
      r"Get-WinEvent -Path C:\Cases\security.evtx",
      "-Path reads an exported .evtx file, so you can work a case away from the machine. "
      "-LogName only names a live log.",
      [r"get-winevent -path " + Q + r"c:\\cases\\security\.evtx" + Q],
      wrong=r"Get-WinEvent -LogName C:\Cases\security.evtx"),
    # --- services and scheduled tasks ---
    C("ps-svc-running", "powershell", "List only the services that are running",
      "Get-Service | Where-Object Status -eq Running",
      "Get-Service has no -Status parameter: filter its objects with Where-Object.",
      piped("get-service", where("status", "-eq", "running")),
      wrong="Get-Service -Status Running"),
    C("ps-svc-account", "powershell", "Show each service's start mode and the account it runs as",
      "Get-CimInstance Win32_Service | Select-Object Name, StartMode, StartName",
      "StartName is the account. It lives on the Win32_Service class, not on what Get-Service returns.",
      piped(CIM_SERVICE, select("name", "startmode", "startname")),
      wrong="Get-Service | Select-Object Name, StartMode, StartName"),
    C("ps-svc-binary", "powershell", "Show the program file behind the service named Spooler",
      "Get-CimInstance Win32_Service -Filter \"Name='Spooler'\" | Select-Object Name, PathName",
      "PathName is the command the service starts. Check where it lives and who can write there.",
      piped(CIM_SERVICE + SPOOLER, [select("name", "pathname"), SELECT + r" (-property |-expandproperty )?pathname"])
      + [r"\(" + CIM_SERVICE + SPOOLER + r"\)\.pathname"],
      wrong="Get-Service Spooler | Select-Object Name, PathName"),
    C("ps-svc-auto-stopped", "powershell",
      "Find services that are set to start automatically but are not running",
      "Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' }",
      "An automatic service that is stopped either failed or was stopped by someone. Both are worth a look.",
      piped("get-service",
            [WHERE + r" \{" + SP + r"\$_\.starttype -eq " + QQ + "automatic" + QQ
             + r" -and \$_\.status -ne " + QQ + "running" + QQ + SP + r"\}",
             WHERE + r" \{" + SP + r"\$_\.status -ne " + QQ + "running" + QQ
             + r" -and \$_\.starttype -eq " + QQ + "automatic" + QQ + SP + r"\}"]),
      wrong="Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -eq 'Running' }"),
    C("ps-task-active", "powershell", "List the scheduled tasks that are not disabled",
      "Get-ScheduledTask | Where-Object State -ne Disabled",
      "Ready and Running tasks will fire. Start an audit with the ones that can actually run.",
      piped("get-scheduledtask", where("state", "-ne", "disabled")),
      wrong="Get-ScheduledTask | Where-Object State -eq Disabled"),
    C("ps-task-action", "powershell", "Show what the scheduled task named Backup actually runs",
      "(Get-ScheduledTask -TaskName Backup).Actions",
      "Actions holds the program and its arguments. Get-ScheduledTaskInfo shows when it ran, not what.",
      [r"\(get-scheduledtask (-taskname )?" + Q + "backup" + Q + r"\)\.actions"]
      + piped(r"get-scheduledtask (-taskname )?" + Q + "backup" + Q, SELECT + r" -expandproperty actions"),
      wrong="Get-ScheduledTaskInfo -TaskName Backup"),
    C("ps-task-lastrun", "powershell",
      "Show when the scheduled task named Backup last ran, and with what result",
      "Get-ScheduledTaskInfo -TaskName Backup",
      "LastRunTime and LastTaskResult are on the info object. Get-ScheduledTask alone shows only the state.",
      [r"get-scheduledtaskinfo (-taskname )?" + Q + "backup" + Q]
      + piped(r"get-scheduledtask (-taskname )?" + Q + "backup" + Q, "get-scheduledtaskinfo"),
      wrong="Get-ScheduledTask -TaskName Backup"),
    C("ps-task-nonmicrosoft", "powershell",
      r"List the scheduled tasks that live outside the \Microsoft\ folder",
      r"Get-ScheduledTask | Where-Object TaskPath -notlike '\Microsoft\*'",
      r"Windows keeps its own tasks under \Microsoft\. What sits elsewhere was added by someone.",
      piped("get-scheduledtask", where("taskpath", "-notlike", r"\\microsoft\\\*")),
      wrong=r"Get-ScheduledTask -TaskPath '\Microsoft\*'"),
    # --- local users and groups ---
    C("ps-user-enabled", "powershell", "List the local accounts that are enabled",
      "Get-LocalUser | Where-Object Enabled",
      "Enabled is a property to filter on. Get-LocalUser has no -Enabled parameter.",
      piped("get-localuser", [WHERE + r" (-property )?enabled( -eq \$true)?",
                              WHERE + r" \{" + SP + r"\$_\.enabled( -eq \$true)?" + SP + r"\}"]),
      wrong="Get-LocalUser -Enabled"),
    C("ps-user-lastlogon", "powershell",
      "Show each local account's name, whether it is enabled, and its last logon",
      "Get-LocalUser | Select-Object Name, Enabled, LastLogon",
      "A local account calls it LastLogon. LastLogonDate is what Active Directory calls it.",
      piped("get-localuser", select("name", "enabled", "lastlogon")),
      wrong="Get-LocalUser | Select-Object Name, Enabled, LastLogonDate"),
    C("ps-user-pw-never", "powershell", "Find the local accounts whose password never expires",
      "Get-LocalUser | Where-Object { $null -eq $_.PasswordExpires }",
      "A local account with no expiry has an empty PasswordExpires. PasswordNeverExpires is an "
      "Active Directory property.",
      piped("get-localuser", [WHERE + r" \{" + SP + r"\$null -eq \$_\.passwordexpires" + SP + r"\}",
                              WHERE + r" \{" + SP + r"-not \$_\.passwordexpires" + SP + r"\}"]
            + where("passwordexpires", "-eq", r"\$null", literal=True)),
      wrong="Get-LocalUser | Where-Object PasswordNeverExpires"),
    C("ps-group-rdp", "powershell", "List who may log on to this machine over Remote Desktop",
      "Get-LocalGroupMember 'Remote Desktop Users'",
      "Membership of Remote Desktop Users is what allows it. Remote Management Users is WinRM, "
      "a different door.",
      [r"get-localgroupmember (-(group|name) )?" + QQ + "remote desktop users" + QQ],
      wrong="Get-LocalGroupMember 'Remote Management Users'"),
    # --- file permissions ---
    C("ps-acl-entries", "powershell", r"Show who has what access to C:\Shares\Finance",
      r"(Get-Acl C:\Shares\Finance).Access",
      "Access is the list of entries: who, allow or deny, and which rights. The Mode column of "
      "Get-ChildItem is attributes, not permissions.",
      [ACL + r"\.access"] + piped(r"get-acl " + PATH_ARG + FINANCE, SELECT + r" -expandproperty access"),
      wrong=r"Get-ChildItem C:\Shares\Finance | Select-Object Mode"),
    C("ps-acl-owner", "powershell", r"Show the owner of C:\Shares\Finance",
      r"(Get-Acl C:\Shares\Finance).Owner",
      "The owner can always change the permissions, so it matters. It is on the ACL, not on the item.",
      [ACL + r"\.owner"]
      + piped(r"get-acl " + PATH_ARG + FINANCE, SELECT + r" (-property |-expandproperty )?owner"),
      wrong=r"(Get-Item C:\Shares\Finance).Owner"),
    C("ps-acl-everyone", "powershell",
      r"From the access list of C:\Shares\Finance, show only the entries for Everyone",
      r"(Get-Acl C:\Shares\Finance).Access | Where-Object IdentityReference -eq Everyone",
      "IdentityReference names who the entry is for. An Everyone entry that allows writing is a finding.",
      piped(ACL + r"\.access", where("identityreference", "-eq", "everyone")),
      wrong=r"(Get-Acl C:\Shares\Finance).Access | Where-Object Identity -eq Everyone"),
    C("ps-acl-inheritance", "powershell",
      r"Check whether C:\Shares\Finance has stopped inheriting permissions from its parent",
      r"(Get-Acl C:\Shares\Finance).AreAccessRulesProtected",
      "True means inheritance is off and the folder carries its own list. IsInherited is a "
      "property of one entry, not of the folder.",
      [ACL + r"\.areaccessrulesprotected"],
      wrong=r"(Get-Acl C:\Shares\Finance).IsInherited"),
    # --- firewall ---
    C("ps-fw-profiles", "powershell", "Show whether the firewall is on for each profile",
      "Get-NetFirewallProfile | Select-Object Name, Enabled",
      "There are three profiles (Domain, Private, Public) and each has its own switch.",
      piped("get-netfirewallprofile", select("name", "enabled")),
      wrong="Get-NetFirewallRule | Select-Object Name, Enabled"),
    C("ps-fw-inbound-allow", "powershell",
      "List the enabled inbound firewall rules that allow traffic",
      "Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True",
      "Without -Enabled True the list also holds rules that are switched off and let nothing in.",
      [any_order("get-netfirewallrule", "direction inbound", "action allow", "enabled true")],
      wrong="Get-NetFirewallRule -Direction Inbound -Action Allow"),
    C("ps-fw-outbound-block", "powershell", "List the outbound firewall rules that block traffic",
      "Get-NetFirewallRule -Direction Outbound -Action Block",
      "Outbound block rules are what stops a program from calling out.",
      [any_order("get-netfirewallrule", "direction outbound", "action block")],
      wrong="Get-NetFirewallRule -Direction Inbound -Action Block"),
    C("ps-fw-rule-ports", "powershell",
      "Show which ports the firewall rule with the display name 'Lab Web' covers",
      "Get-NetFirewallRule -DisplayName 'Lab Web' | Get-NetFirewallPortFilter",
      "A rule object does not carry its ports. Pipe it to Get-NetFirewallPortFilter to see them.",
      piped(r"get-netfirewallrule -displayname " + QQ + "lab web" + QQ, "get-netfirewallportfilter"),
      wrong="Get-NetFirewallRule -DisplayName 'Lab Web' | Select-Object LocalPort"),
    # --- file hashes and signatures ---
    C("ps-hash-sha256", "powershell", r"Compute the SHA-256 hash of C:\Tools\agent.exe",
      r"Get-FileHash C:\Tools\agent.exe",
      "SHA256 is the default, so no -Algorithm is needed. MD5 is not what a modern feed lists.",
      [r"get-filehash " + PATH_ARG + AGENT + r"( -algorithm sha256)?",
       r"get-filehash -algorithm sha256 " + PATH_ARG + AGENT],
      wrong=r"Get-FileHash C:\Tools\agent.exe -Algorithm MD5"),
    C("ps-hash-sha1", "powershell",
      r"Compute the SHA-1 hash of C:\Tools\agent.exe (an old report lists SHA-1)",
      r"Get-FileHash C:\Tools\agent.exe -Algorithm SHA1",
      "The algorithm names have no dash: SHA1, SHA256, SHA384, SHA512, MD5.",
      [r"get-filehash " + PATH_ARG + AGENT + r" -algorithm sha1",
       r"get-filehash -algorithm sha1 " + PATH_ARG + AGENT],
      wrong=r"Get-FileHash C:\Tools\agent.exe -Algorithm SHA-1"),
    C("ps-hash-tree", "powershell", r"Hash every file under C:\Tools, subfolders included",
      r"Get-ChildItem C:\Tools -Recurse -File | Get-FileHash",
      "Get-FileHash has no -Recurse. Let Get-ChildItem find the files and pipe them in.",
      piped(any_order(r"get-childitem " + PATH_ARG + Q + r"c:\\tools" + Q, "recurse", "file"), "get-filehash")
      + piped(any_order(r"get-childitem", "recurse", "file") + " " + PATH_ARG + Q + r"c:\\tools" + Q,
              "get-filehash"),
      wrong=r"Get-FileHash C:\Tools -Recurse"),
    C("ps-sig-check", "powershell", r"Check the digital signature of C:\Tools\agent.exe",
      r"Get-AuthenticodeSignature C:\Tools\agent.exe",
      "Status says Valid, NotSigned or HashMismatch, and SignerCertificate says who signed it.",
      [r"get-authenticodesignature (-(filepath|literalpath) )?" + AGENT],
      wrong=r"Get-FileHash C:\Tools\agent.exe -Algorithm Authenticode"),
    # --- processes and listening ports ---
    C("ps-proc-path", "powershell", "List the running processes with the file each one runs from",
      "Get-Process | Select-Object Name, Id, Path",
      "A process object calls it Path. ExecutablePath is the Win32_Process name for the same thing.",
      piped("get-process", select("name", "id", "path")),
      wrong="Get-Process | Select-Object Name, Id, ExecutablePath"),
    C("ps-proc-cmdline", "powershell", "Show the full command line of every running process",
      "Get-CimInstance Win32_Process | Select-Object ProcessId, Name, CommandLine",
      "The command line is on Win32_Process. It shows the arguments a program was started with, "
      "which is where the story usually is.",
      piped(CIM_PROCESS, select("processid", "name", "commandline")),
      wrong="Get-CimInstance Win32_Service | Select-Object ProcessId, Name, CommandLine"),
    C("ps-proc-parent", "powershell", "Show every process with the process ID of its parent",
      "Get-CimInstance Win32_Process | Select-Object Name, ProcessId, ParentProcessId",
      "The parent tells you what started it: a document viewer that starts a shell is a finding.",
      piped(CIM_PROCESS, select("name", "processid", "parentprocessid")),
      wrong="Get-Process | Select-Object Name, Id, ParentProcessId"),
    C("ps-proc-by-id", "powershell", "Show the process whose ID is 4242",
      "Get-Process -Id 4242",
      "A bare value is taken as a process NAME. An ID needs -Id.",
      [r"get-process -id 4242"],
      wrong="Get-Process 4242"),
    C("ps-port-owner", "powershell", "Find which process owns the listener on TCP port 3389",
      "Get-NetTCPConnection -LocalPort 3389 -State Listen",
      "A listener is a LOCAL port. The OwningProcess column is the ID to hand to Get-Process -Id.",
      [any_order("get-nettcpconnection", "localport 3389", "state listen")]
      + piped(any_order("get-nettcpconnection", "localport 3389", "state listen"),
              [select("owningprocess"), select("localport", "owningprocess"),
               SELECT + " -expandproperty owningprocess"])
      + [r"\(" + any_order("get-nettcpconnection", "localport 3389", "state listen") + r"\)\.owningprocess"],
      wrong="Get-NetTCPConnection -RemotePort 3389 -State Listen"),
    C("ps-port-udp", "powershell", "List the UDP endpoints this machine is listening on",
      "Get-NetUDPEndpoint",
      "UDP has no connections, so it has its own cmdlet. Get-NetTCPConnection knows only TCP.",
      [r"get-netudpendpoint"],
      wrong="Get-NetTCPConnection -Protocol UDP"),
    C("ps-conn-established", "powershell",
      "List the established TCP connections with their remote address, remote port and owning process",
      "Get-NetTCPConnection -State Established | Select-Object RemoteAddress, RemotePort, OwningProcess",
      "Established means a live conversation. This is the answer to 'what is this machine talking to'.",
      piped("get-nettcpconnection -state established", select("remoteaddress", "remoteport", "owningprocess")),
      wrong="Get-NetTCPConnection -State Listen | Select-Object RemoteAddress, RemotePort, OwningProcess"),
    # --- read-only directory queries ---
    C("ps-ad-disabled", "powershell", "List the disabled user accounts in the domain",
      "Search-ADAccount -AccountDisabled -UsersOnly",
      "Search-ADAccount has a switch for the common account audits. With Get-ADUser the "
      "filter is Enabled -eq $false: there is no Disabled attribute.",
      [any_order("search-adaccount", "accountdisabled", "usersonly"),
       r"get-aduser -filter " + QQ + r"enabled -eq \$false" + QQ,
       r"get-aduser -filter \{" + SP + r"enabled -eq \$false" + SP + r"\}"],
      wrong="Get-ADUser -Filter 'Disabled -eq $true'"),
    C("ps-ad-inactive", "powershell", "Find user accounts that have not logged on for 90 days",
      "Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00 -UsersOnly",
      "The time span is days.hours:minutes:seconds. A bare 90 is taken as 90 ticks, nine "
      "millionths of a second, so every account that has ever been idle matches.",
      [any_order("search-adaccount", "accountinactive", r"timespan 90\.00:00:00", "usersonly"),
       any_order("search-adaccount", "accountinactive", "timespan " + QQ + r"90(\.00:00:00)?" + QQ, "usersonly"),
       any_order("search-adaccount", "accountinactive", r"timespan \(new-timespan -days 90\)", "usersonly")],
      wrong="Search-ADAccount -AccountInactive -TimeSpan 90 -UsersOnly"),
    C("ps-ad-locked", "powershell", "List the accounts that are locked out right now",
      "Search-ADAccount -LockedOut",
      "LockedOut is worked out by the directory, so Get-ADUser -Filter cannot search on it. "
      "Search-ADAccount can.",
      [r"search-adaccount -lockedout( -usersonly)?", r"search-adaccount -usersonly -lockedout"],
      wrong="Get-ADUser -Filter 'LockedOut -eq $true'"),
    C("ps-ad-pw-never", "powershell", "List the domain users whose password never expires",
      "Get-ADUser -Filter 'PasswordNeverExpires -eq $true'",
      "Service accounts often have this set, which is why they are worth listing.",
      [r"get-aduser -filter " + QQ + r"passwordneverexpires -eq \$true" + QQ,
       r"get-aduser -filter \{" + SP + r"passwordneverexpires -eq \$true" + SP + r"\}",
       r"search-adaccount -passwordneverexpires( -usersonly)?",
       r"search-adaccount -usersonly -passwordneverexpires"],
      wrong="Get-ADUser -Filter 'PasswordExpires -eq $false'"),
    C("ps-ad-memberof", "powershell", "Show every group the user jsmith belongs to",
      "Get-ADPrincipalGroupMembership jsmith",
      "This asks about one account's groups. Get-ADGroupMember asks the opposite: one group's members.",
      [r"get-adprincipalgroupmembership (-identity )?" + Q + "jsmith" + Q],
      wrong="Get-ADGroupMember jsmith"),
    C("ps-ad-nested-admins", "powershell",
      "List the members of Domain Admins, including the members of groups nested inside it",
      "Get-ADGroupMember 'Domain Admins' -Recursive",
      "Nested groups hide administrators. The switch is -Recursive; -Recurse belongs to Get-ChildItem.",
      [r"get-adgroupmember (-identity )?" + QQ + "domain admins" + QQ + " -recursive",
       r"get-adgroupmember -recursive (-identity )?" + QQ + "domain admins" + QQ],
      wrong="Get-ADGroupMember 'Domain Admins' -Recurse"),
    C("ps-ad-pw-policy", "powershell", "Show the domain's default password policy",
      "Get-ADDefaultDomainPasswordPolicy",
      "Length, age, history, complexity and lockout in one object: the first thing to compare "
      "with a baseline.",
      [r"get-addefaultdomainpasswordpolicy"],
      wrong="Get-ADDomainPasswordPolicy"),
    C("ps-ad-user-dates", "powershell",
      "Show jsmith's last logon date and when the password was last set",
      "Get-ADUser jsmith -Properties LastLogonDate, PasswordLastSet",
      "Get-ADUser returns a short default set. Anything else has to be asked for with "
      "-Properties, or it comes back empty.",
      [r"get-aduser (-identity )?" + Q + "jsmith" + Q + r" -properties lastlogondate," + SP + "passwordlastset",
       r"get-aduser (-identity )?" + Q + "jsmith" + Q + r" -properties passwordlastset," + SP + "lastlogondate"],
      wrong="Get-ADUser jsmith | Select-Object LastLogonDate, PasswordLastSet"),
]

(OUT / "commands.json").write_text(json.dumps(bank, indent=2, ensure_ascii=True))
print(f"wrote {len(bank)} commands to drills/commands.json")
