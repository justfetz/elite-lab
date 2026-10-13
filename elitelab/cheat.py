"""`elite cheat <tool>` - instant command reference, available from anywhere.

The principle: a learner is never stranded. Direction ("what do I do") comes from
status/map/the mission; RESOURCES ("how do I do it") come from here - the exact
commands for a tool, the moment you need them, without leaving what you're doing.
"""

# Each: short "what", then (command, plain-English note) lines, + a cross-OS note.
CHEATS = {
    "grep": ("print the lines that match a pattern", [
        ("grep word file", "lines containing 'word'"),
        ("grep -i word file", "-i: ignore case (Word, WORD too)"),
        ("grep -c word file", "-c: just COUNT the matches"),
        ("grep -n word file", "-n: show line numbers"),
        ("grep -v word file", "-v: INVERT - lines that DON'T match"),
        ("grep -r word .", "-r: search every file under here"),
        ("grep -E 'a|b' file", "-E: regex (a OR b)"),
        ("grep word file | awk '{print $2}' | sort | uniq -c | sort -rn",
         "count column-2 values, biggest first - the log-hunting workhorse"),
    ], "PowerShell: Select-String word file. Pipelines: use WSL."),
    "curl": ("talk to a URL from the terminal (your browser without the window)", [
        ("curl http://site/p", "fetch the page body"),
        ("curl -I http://site", "-I: headers only (HEAD request)"),
        ("curl -v http://site", "-v: verbose - see the whole request/response"),
        ("curl -L http://site", "-L: follow redirects"),
        ("curl -o out.html http://site", "-o: save to a file"),
        ("curl -d 'user=a&pw=b' http://site/login", "-d: POST this form data"),
        ("curl -H 'Authorization: Bearer X' http://api", "-H: add a header"),
        ("curl 'http://site/o?id=5'", "tamper a parameter by hand (IDOR testing)"),
    ], "PowerShell: curl is aliased to Invoke-WebRequest; use curl.exe for real curl."),
    "awk": ("pull out and process columns of text", [
        ("awk '{print $2}' file", "print the 2nd whitespace field of each line"),
        ("awk '{print $1, $4}' file", "print fields 1 and 4"),
        ("awk -F, '{print $3}' file", "-F, : split on commas instead of spaces"),
        ("awk '/error/{print $2}' file", "only lines matching /error/, print field 2"),
        ("awk '{s+=$3} END{print s}' file", "sum column 3"),
    ], None),
    "find": ("search the filesystem for files by name, type, permission, time", [
        ("find . -name '*.log'", "every .log under here"),
        ("find / -perm -4000 2>/dev/null", "SUID binaries - classic privesc hunt"),
        ("find . -type f -mtime -1", "files changed in the last day"),
        ("find . -size +10M", "files bigger than 10 MB"),
        ("find / -user root -writable 2>/dev/null", "root-owned files you can write"),
    ], "PowerShell: Get-ChildItem -Recurse -Filter *.log"),
    "sort": ("order lines; pair with uniq to count", [
        ("sort file", "alphabetical/numeric sort"),
        ("sort -rn file", "-r reverse, -n numeric (biggest number first)"),
        ("sort file | uniq", "collapse duplicate lines (must sort first)"),
        ("sort file | uniq -c", "-c: count how many times each line appeared"),
        ("... | sort | uniq -c | sort -rn", "the 'top N' idiom: count, then rank"),
    ], None),
    "chmod": ("change file permissions (read/write/execute)", [
        ("chmod +x script.sh", "make it executable"),
        ("chmod 600 secret.txt", "owner read/write only (rwx = 4+2+1 per group)"),
        ("chmod 755 file", "owner all, others read+execute"),
        ("ls -l file", "see the current permissions (-rwxr-xr-x)"),
    ], "Permissions are a core security concept - least privilege starts here."),
    "strings": ("pull human-readable text out of a binary", [
        ("strings program", "every printable run of characters - fast first look"),
        ("strings program | grep -i pass", "hunt for hardcoded secrets/prompts"),
        ("strings -n 8 program", "-n 8: only strings 8+ chars (less noise)"),
    ], "First move when reversing a crackme - the answer is often sitting in plain text."),
    "ssh": ("log into a remote machine securely", [
        ("ssh user@host", "connect"),
        ("ssh -p 2222 user@host", "-p: non-default port"),
        ("ssh -i key.pem user@host", "-i: use a private key file"),
        ("ssh user@host 'cat /etc/hostname'", "run one command and exit"),
    ], "Only to machines you own or are authorized to access."),
    "nmap": ("scan a host for open ports and services (recon)", [
        ("nmap 127.0.0.1", "quick scan of your own machine"),
        ("nmap -sV 127.0.0.1", "-sV: identify the service + version on each port"),
        ("nmap -p 1-1000 target", "-p: a specific port range"),
    ], "Only against your own lab / RFC1918. elite run nmap gives a taught debrief; "
       "full briefing: elite tools tools-recon."),
    "john": ("crack password hashes offline", [
        ("john hashes.txt", "auto-detect format, try default wordlist+rules"),
        ("john --wordlist=rockyou.txt hashes.txt", "use a specific wordlist"),
        ("john --show hashes.txt", "show what you've already cracked"),
    ], "Only hashes from systems you own. Full briefing: elite tools tools-pw."),
    "sudo": ("run a command as another user (usually root) - and a privesc lead", [
        ("sudo -l", "list what the current user is ALLOWED to run as root - start here"),
        ("sudo command", "run one command as root"),
    ], "On a host you're assessing, 'sudo -l' is the first privesc question you ask."),
}
ALIASES = {"nc": "netcat", "ripgrep": "grep", "rg": "grep", "uniq": "sort",
           "select-string": "grep"}


def cheat(args):
    tool = (getattr(args, "tool", None) or "").lower().strip()
    tool = ALIASES.get(tool, tool)
    if not tool:
        print("\n  Command references (elite cheat <tool>) -- the 'how do I do it' lane:")
        print("    " + " · ".join(sorted(CHEATS)))
        print("  e.g.  elite cheat grep   |   deeper tool briefings: elite tools\n")
        return
    if tool not in CHEATS:
        near = [k for k in CHEATS if tool in k or k in tool]
        print(f"\n  No cheat for '{tool}'. Available: {', '.join(sorted(CHEATS))}")
        if near:
            print(f"  Did you mean: {', '.join(near)}?")
        print()
        return
    what, lines, note = CHEATS[tool]
    print(f"\n  {tool} -- {what}\n")
    for cmd, desc in lines:
        print(f"    {cmd}")
        print(f"        {desc}")
    if note:
        print(f"\n  {note}")
    print()
