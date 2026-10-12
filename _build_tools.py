"""Generates the tool-briefing modules. Original content; lab/authorized use only."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"

LEGAL = ("Only run this against machines you own or have explicit written permission to test. "
         "Scanning or attacking other systems is illegal.")


def T(name, what, install, try_, exercise, legal=LEGAL):
    return {"name": name, "what": what, "legal": legal, "install": install,
            "try": try_, "exercise": exercise}


recon = {
    "key": "tools-recon", "title": "Tools: recon & scanning", "order": 50,
    "lessons": [
        {"title": "The recon mindset",
         "body": "Before attacking anything you map it: which hosts are alive, which ports are open, "
                 "what software and versions answer. Every open port is a service; every service is a "
                 "version; every version may have known bugs. Recon is just disciplined curiosity, and "
                 "it is the same whether you are attacking a lab or defending your own network."},
    ],
    "tools": [
        T("nmap",
          "The standard port scanner and service mapper. Finds live hosts, open ports, service "
          "versions, and OS guesses. Open = a program answers (SYN-ACK); closed = RST; filtered = no "
          "reply (firewall). A SYN scan (-sS) is fast and never completes the handshake.",
          "Preinstalled on Kali; else `sudo apt install nmap` / `brew install nmap`.",
          ["nmap localhost", "nmap -sV 127.0.0.1", "nmap -sS -p- 10.0.0.0/24   # your own lab subnet"],
          "Scan your own machine with -sV. For each open port, name the program and decide whether it "
          "should be open. That question is network hardening in one line."),
        T("masscan",
          "An internet-scale asynchronous scanner - like nmap but built for huge address ranges at "
          "high packet rates. Use it to find live ports fast, then hand those to nmap -sV for detail.",
          "`sudo apt install masscan`.",
          ["masscan 10.0.0.0/24 -p80,443 --rate 1000   # your own lab only"],
          "On your lab subnet, masscan for open 80/443, then re-scan just those hosts with nmap -sV. "
          "Notice the speed-vs-detail tradeoff."),
    ],
}

web = {
    "key": "tools-web", "title": "Tools: web app testing", "order": 60,
    "lessons": [
        {"title": "Why web is the biggest attack surface",
         "body": "Most organisations expose far more web than anything else, and web bugs are where a "
                 "database background pays off fastest. Set up a deliberately vulnerable target first "
                 "(OWASP Juice Shop or DVWA in Docker) so every tool below has something legal to hit."},
    ],
    "tools": [
        T("Burp Suite (Community)",
          "An intercepting proxy: it sits between your browser and a site so you can read and modify "
          "every request. The free edition does manual testing and repeating requests; Pro adds an "
          "automated scanner. This is the center of most web testing.",
          "Download from PortSwigger; bundled in Kali. Pair with PortSwigger's free Web Security Academy.",
          ["# point your browser's proxy at 127.0.0.1:8080, then browse your local Juice Shop"],
          "Intercept a login on your local Juice Shop, change one field, and forward it. Watch how the "
          "server reacts - that is the whole game of web testing."),
        T("ffuf",
          "A fast web fuzzer: it requests many paths/parameters from a wordlist to discover hidden "
          "pages, directories, or parameters a site did not advertise.",
          "`sudo apt install ffuf` or `go install`.",
          ["ffuf -u http://localhost:3000/FUZZ -w /usr/share/wordlists/dirb/common.txt"],
          "Fuzz your local lab app for hidden directories. Compare what ffuf finds to what the site "
          "links to - the gap is attack surface."),
        T("sqlmap",
          "Automates finding and exploiting SQL injection: detects injectable parameters, fingerprints "
          "the DBMS, and can dump data. With ten years of SQL Server you will understand exactly what it "
          "does under the hood - and why parameterised queries stop it.",
          "`sudo apt install sqlmap` or `pip install sqlmap`.",
          ["sqlmap -u 'http://localhost/item?id=1' --batch        # your own lab app",
           "sqlmap -u 'http://localhost/item?id=1' --dbs --batch"],
          "Stand up a tiny vulnerable PHP+SQL app (or DVWA) on localhost, let sqlmap find the injection, "
          "then rewrite the query with parameters and watch sqlmap fail. That before/after is a great blog post."),
    ],
}

ad = {
    "key": "tools-ad", "title": "Tools: Active Directory", "order": 70,
    "lessons": [
        {"title": "Why AD is the enterprise battleground",
         "body": "Most companies run on Active Directory, so most real intrusions become AD attacks: "
                 "steal one credential, then find a path to Domain Admin. Build a lab first - free Windows "
                 "Server evaluation VMs, or the GOAD ('Game of Active Directory') project, which stands up "
                 "a whole deliberately vulnerable domain for you to practise on legally."},
    ],
    "tools": [
        T("BloodHound",
          "Maps an Active Directory domain as a graph and finds attack paths - e.g. 'this normal user "
          "can eventually reach Domain Admin via these three hops'. Defenders use the same graph to find "
          "and cut those paths. A collector (SharpHound) gathers the data; BloodHound visualises it.",
          "BloodHound Community Edition (Docker); SharpHound collector on the domain.",
          ["# run SharpHound in your lab domain, then import the data into BloodHound and run",
           "# the built-in query 'Shortest paths to Domain Admins'"],
          "In your GOAD/eval lab, collect with SharpHound and find the shortest path to Domain Admin. "
          "Then change one group membership and watch the path disappear. That is remediation."),
        T("Impacket",
          "A Python toolkit implementing Windows network protocols (SMB, Kerberos, RPC). Its example "
          "scripts (secretsdump, psexec, GetUserSPNs for Kerberoasting) are the workhorses of AD testing "
          "and of understanding how those protocols really work.",
          "`pipx install impacket` or clone the repo.",
          ["GetUserSPNs.py lab.local/user:pass -dc-ip 10.0.0.10 -request   # your lab DC only"],
          "In your lab, Kerberoast a service account with GetUserSPNs, crack the ticket offline with "
          "hashcat, then fix it by setting a long managed-service-account password. Attack then defend."),
    ],
}

passwords = {
    "key": "tools-pw", "title": "Tools: password & hash cracking", "order": 80,
    "lessons": [
        {"title": "Why cracking teaches defense",
         "body": "Cracking your own test hashes is the fastest way to internalise why slow salted "
                 "hashing matters. Fast unsalted hashes (MD5, raw SHA-256) fall in seconds; bcrypt/scrypt/"
                 "Argon2 with a good cost factor resist even GPUs. You learn the defense by feeling the attack."},
    ],
    "tools": [
        T("Hashcat",
          "The leading GPU password cracker. Takes a hash type and a wordlist or mask and tries "
          "candidates at enormous speed. Great for proving to yourself how weak fast hashes are.",
          "`sudo apt install hashcat`; a GPU helps but CPU works for learning.",
          ["hashcat -m 0 -a 0 your_md5_hashes.txt rockyou.txt    # hashes YOU generated"],
          "Hash a list of weak passwords you make up with MD5, crack them with hashcat, then re-hash "
          "the same list with bcrypt and try again. Time both. That contrast is the lesson."),
        T("John the Ripper",
          "The classic, format-rich cracker (jumbo edition handles hundreds of hash types). Its *2john "
          "helpers turn files (zip, pdf, shadow) into crackable hashes - useful for understanding where "
          "hashes hide.",
          "`sudo apt install john` (get the 'jumbo' build for more formats).",
          ["unshadow /etc/passwd /etc/shadow > mine.txt   # on your OWN machine",
           "john --wordlist=rockyou.txt mine.txt"],
          "On a throwaway VM you control, add a user with a weak password and crack it from the shadow "
          "file. Then set a strong passphrase and watch the wordlist attack fail."),
        T("Hydra (THC-Hydra)",
          "The ONLINE password guesser - and the key contrast to John/Hashcat. John and Hashcat are "
          "OFFLINE: you already HAVE the hash and crack it on your own machine (fast, silent, unlimited "
          "tries). Hydra is ONLINE: it throws guesses at a LIVE service (SSH, FTP, a web login) that "
          "answers yes/no. Use Hydra only when you have a login prompt but no hash. It is slow, LOUD "
          "(every try hits real logs), and can lock accounts - the opposite trade-off from offline cracking.",
          "`sudo apt install hydra` (Kali: preinstalled).",
          ["# against YOUR OWN lab service only (e.g. OrderDesk's login on localhost):",
           "hydra -l millops_admin -P small_wordlist.txt 127.0.0.1 http-post-form \\",
           "  \"/login:username=^USER^&password=^PASS^:Bad credentials\""],
          "Decide offline vs online first: do you have the hash, or just a login box? If OrderDesk leaks "
          "its hashes, that's OFFLINE (John). If you only had the login form, that's where Hydra fits. "
          "Run it against your own local lab, watch it trip the logs, and feel why online cracking is noisy."),
    ],
}

reverse = {
    "key": "tools-re", "title": "Tools: reverse engineering & bare metal", "order": 90,
    "lessons": [
        {"title": "Reading what code really does",
         "body": "The bare-metal track: compile your own small C programs, then read what they became. "
                 "This is how you build the muscle that closed-source and exploitation work both need - "
                 "and it never goes stale."},
    ],
    "tools": [
        T("gdb (with pwndbg/GEF)",
          "The GNU debugger: step through a program instruction by instruction, inspect registers and "
          "memory, set breakpoints. The pwndbg/GEF add-ons make it far friendlier for security work.",
          "`sudo apt install gdb`; then install pwndbg or GEF.",
          ["gcc -g -o hello hello.c", "gdb ./hello", "# break main ; run ; info registers ; x/8x $sp"],
          "Write a 10-line C program, compile with -g, and step through main in gdb. Watch the stack "
          "change as you call a function. That picture is the foundation of exploitation."),
        T("Ghidra",
          "The NSA's free reverse-engineering suite. Disassembles and decompiles a binary into readable "
          "C-like pseudocode, so you can study what a program does without source.",
          "Download Ghidra (needs a JDK).",
          ["# open a small binary YOU compiled and compare Ghidra's decompilation to your source"],
          "Compile a tiny program, open it in Ghidra, and match the decompiled output back to your own "
          "code. Doing this on code you wrote builds intuition fast."),
        T("AFL++",
          "A coverage-guided fuzzer: it mutates inputs by the millions and watches which ones reach new "
          "code or crash the target. Your optimization background fits here - a fuzzer is a search "
          "algorithm over the input space.",
          "`sudo apt install afl++` or build from source.",
          ["afl-cc -o target target.c", "afl-fuzz -i seeds -o out -- ./target @@"],
          "Write a small C parser with a deliberate bug, fuzz it with AFL++, and catch the crash. Then "
          "fix it and confirm the crash is gone. That loop is real vulnerability research in miniature."),
    ],
}

for mod in (recon, web, ad, passwords, reverse):
    mod.setdefault("quiz", [])
    (OUT / f"{mod['key']}.json").write_text(json.dumps(mod, indent=2, ensure_ascii=True))

print("wrote tool modules:", len(list(OUT.glob('tools-*.json'))))
