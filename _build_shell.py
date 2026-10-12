"""Generates modules/shell-basics.json - very basic grep & curl, plus how AI coding
tools use them. Original content."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


shell = {
    "key": "shell-basics", "title": "grep & curl (and how AI uses them)", "order": 8,
    "lessons": [
        L("grep - find lines that match",
          "grep searches text for a pattern and prints the matching lines. That's it.\n"
          "  grep error app.log            lines containing 'error'\n"
          "  grep -i error app.log         -i = ignore case (Error, ERROR too)\n"
          "  grep -r TODO .                -r = search every file under here\n"
          "  grep -n error app.log         -n = show line numbers\n"
          "  grep -v error app.log         -v = INVERT: lines WITHOUT 'error'\n"
          "  grep -c error app.log         -c = just count the matches\n"
          "  grep -E 'cat|dog' file        -E = regex (here, cat OR dog)\n"
          "The magic is piping: feed another command's output into grep with |:\n"
          "  ps aux | grep ssh             running processes, filtered to ssh\n"
          "In security this is 80% of log analysis - that's exactly what wire-01 is."),
        L("curl - talk to a URL from the terminal",
          "curl makes web requests and prints what comes back. It's your browser without the window.\n"
          "  curl http://site/page         fetch the page body\n"
          "  curl -I http://site           -I = headers only (HEAD request)\n"
          "  curl -v http://site           -v = verbose: see the whole request/response + TLS\n"
          "  curl -L http://site           -L = follow redirects (3xx)\n"
          "  curl -o out.html http://site  -o = save to a file\n"
          "  curl -d 'user=a&pw=b' http://site/login   -d = POST this form data\n"
          "  curl -H 'Authorization: Bearer X' http://api   -H = add a header\n"
          "curl is how you inspect what a server really sends, test an API, or check an "
          "endpoint - the first tool you reach for on the App layer."),
        L("Piping them together",
          "The Unix idea: small tools, chained with |, each doing one thing. Examples:\n"
          "  curl -s http://site | grep -i 'password'     fetch a page, show lines mentioning password\n"
          "  curl -sI http://site | grep -i server         just the Server: header\n"
          "  grep -rn 'api_key' .                          hunt hardcoded secrets in a codebase\n"
          "-s makes curl silent (no progress bar) so the pipe is clean. Learning to chain "
          "curl + grep + sort + uniq is the difference between staring at data and answering "
          "a question with it."),
        L("How AI coding tools use grep & curl",
          "When an AI coding assistant (like the one that built this repo) works in a codebase, "
          "it mostly uses the SAME tools you just learned:\n"
          "  - grep / ripgrep (rg): before changing code, it searches the repo for where a "
          "function, variable, or string is defined and used - so it edits the right place and "
          "doesn't miss callers. 'Find every use of parse_packet' is just grep.\n"
          "  - curl / HTTP fetch: to read documentation, test an API endpoint, or check that a "
          "local server responds, it makes the same requests curl does.\n"
          "The AI isn't doing anything mystical - it reads with grep, fetches with curl, runs "
          "code, reads the output, and decides the next step. Watching how it chains these is a "
          "great way to learn the workflow yourself: the tools are the same, the loop is the same."),
    ],
    "quiz": [
        Q("Which grep flag searches all files in a directory tree?",
          ["-i", "-r", "-v", "-c"], 1, "-r = recursive."),
        Q("How do you fetch ONLY the response headers with curl?",
          ["curl -v", "curl -o", "curl -I", "curl -L"], 2, "-I sends a HEAD request: headers only."),
        Q("What does `ps aux | grep ssh` do?",
          ["kills ssh", "lists processes, showing only lines mentioning ssh",
           "opens an ssh session", "counts files"], 1,
          "ps lists processes; grep filters that output to ssh lines."),
        Q("When an AI coding tool needs to find where a function is used, it most likely...",
          ["guesses", "greps the codebase for the name", "deletes the file", "reboots"], 1,
          "It searches (grep/ripgrep) for the symbol - same tool you just learned."),
    ],
}

(OUT / "shell-basics.json").write_text(json.dumps(shell, indent=2, ensure_ascii=True))
print("wrote shell-basics.json")
