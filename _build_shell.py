"""Generates modules/shell-basics.json - terminal fundamentals, bash vs PowerShell,
grep & curl, and how AI coding tools use them. Original, beginner-friendly content."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


shell = {
    "key": "shell-basics", "title": "Terminal basics (bash, PowerShell, grep & curl)", "order": 8,
    "lessons": [
        L("Terminal vs shell; bash vs PowerShell",
          "A TERMINAL is the window. A SHELL is the program inside it that runs what you type.\n"
          "Common shells:\n"
          "  bash / zsh   on macOS and Linux (and WSL on Windows)\n"
          "  PowerShell   on Windows\n"
          "They do the same job with different syntax. For elite-lab:\n"
          "  - the TOOL itself is Python - `python3 elite.py` runs the same everywhere.\n"
          "  - the mission commands are mostly bash/Unix (grep, nmap, john, sudo, gcc).\n"
          "So use a Unix shell: macOS Terminal, any Linux terminal, or WSL on Windows\n"
          "(install once: `wsl --install`). The PowerShell-specific material lives in the\n"
          "'windows-ps' module, for Windows and Active Directory work.\n"
          "Rule of thumb: bash for the missions; PowerShell when a lesson says PowerShell."),
        L("The terminal basics you actually need",
          "The PROMPT ($ on bash, > on PowerShell) waits for a command. A command line is:\n"
          "  program   options(flags)   arguments\n"
          "  nmap      -sV              127.0.0.1\n"
          "Flags tweak behavior: short like -v, long like --verbose; combine short ones: -la.\n"
          "Arguments are what it acts on (a file, a host, a URL).\n"
          "Move around the filesystem:\n"
          "  pwd   where am I        ls    list what's here       cd dir   go into dir\n"
          "Paths: /  = root,  ~  = your home,  .  = here,  ..  = one level up.\n"
          "Running & stopping: press Enter to run; Ctrl-C to stop a running command; `clear`.\n"
          "Lifesavers: Up-arrow re-runs your last command, Tab auto-completes names, and\n"
          "`<command> --help` (or `man <command>`) shows how to use it.\n"
          "Quote anything with spaces or symbols: elite ask \"what is idor\"."),
        L("grep - find lines that match",
          "grep searches text for a pattern and prints the matching lines. That's it.\n"
          "  grep error app.log            lines containing 'error'\n"
          "  grep -i error app.log         -i = ignore case (Error, ERROR too)\n"
          "  grep -r TODO .                -r = search every file under here\n"
          "  grep -n error app.log         -n = show line numbers\n"
          "  grep -v error app.log         -v = INVERT: lines WITHOUT 'error'\n"
          "  grep -c error app.log         -c = just count the matches\n"
          "  grep -E 'cat|dog' file        -E = regex (here, cat OR dog)\n"
          "The magic is piping - feed another command's output into grep with |:\n"
          "  ps aux | grep ssh             running processes, filtered to ssh\n"
          "In security this is 80% of log analysis - exactly what wire-01 and hunt-01 are."),
        L("curl - talk to a URL from the terminal",
          "curl makes web requests and prints what comes back. Your browser without the window.\n"
          "  curl http://site/page         fetch the page body\n"
          "  curl -I http://site           -I = headers only (HEAD request)\n"
          "  curl -v http://site           -v = verbose: see the whole request/response + TLS\n"
          "  curl -L http://site           -L = follow redirects (3xx)\n"
          "  curl -o out.html http://site  -o = save to a file\n"
          "  curl -d 'user=a&pw=b' http://site/login   -d = POST this form data\n"
          "  curl -H 'Authorization: Bearer X' http://api   -H = add a header\n"
          "curl is how you inspect what a server really sends, test an API, or check an endpoint\n"
          "- the first tool you reach for on the App layer."),
        L("Piping them together",
          "The Unix idea: small tools chained with |, each doing one thing. Examples:\n"
          "  curl -s http://site | grep -i 'password'     fetch a page, show password lines\n"
          "  curl -sI http://site | grep -i server         just the Server: header\n"
          "  grep -rn 'api_key' .                          hunt hardcoded secrets in a codebase\n"
          "-s makes curl silent so the pipe is clean. Chaining curl + grep + sort + uniq is the\n"
          "difference between staring at data and answering a question with it."),
        L("How AI coding tools use grep & curl",
          "When an AI coding assistant (like the one that built this repo) works in a codebase,\n"
          "it mostly uses the SAME commands you just learned:\n"
          "  - grep / ripgrep (rg): before changing code it searches the repo for where a\n"
          "    function or string is defined and used, so it edits the right place. 'Find every\n"
          "    use of parse_packet' is just grep.\n"
          "  - curl / HTTP fetch: to read docs, test an API, or check a local server responds.\n"
          "It isn't magic - it reads with grep, fetches with curl, runs code, reads the output,\n"
          "and decides the next step. The tools are the same; watching the loop teaches you the\n"
          "workflow."),
    ],
    "quiz": [
        Q("For the hands-on missions, which terminal should a Windows user use?",
          ["Command Prompt (cmd)", "WSL (a Unix shell) or PowerShell per the lesson",
           "the Python REPL", "Notepad"], 1,
          "Mission commands are bash/Unix - use WSL; PowerShell for the windows-ps material."),
        Q("In `nmap -sV 127.0.0.1`, what is `-sV`?",
          ["the program", "a flag/option", "the target", "a file"], 1,
          "Flags/options tweak how the program runs; the target is the argument."),
        Q("How do you stop a command that's currently running?",
          ["close the laptop", "Ctrl-C", "type stop", "Ctrl-S"], 1,
          "Ctrl-C interrupts the running process."),
        Q("Which grep flag searches all files in a directory tree?",
          ["-i", "-r", "-v", "-c"], 1, "-r = recursive."),
        Q("How do you fetch ONLY the response headers with curl?",
          ["curl -v", "curl -o", "curl -I", "curl -L"], 2, "-I sends a HEAD request: headers only."),
        Q("When an AI coding tool needs to find where a function is used, it most likely...",
          ["guesses", "greps the codebase for the name", "deletes the file", "reboots"], 1,
          "It searches (grep/ripgrep) for the symbol - same tool you just learned."),
    ],
}

(OUT / "shell-basics.json").write_text(json.dumps(shell, indent=2, ensure_ascii=True))
print("wrote shell-basics.json")
