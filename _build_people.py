"""Generates modules/people.json - the People layer: phishing, email auth, lookalike
domains, and the recon attackers do before they ever send a packet (public GitHub
leaks, Shodan). Defensive framing: you learn the indicators so you can SPOT them.
Original, beginner-friendly content."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


people = {
    "key": "people", "title": "The People layer (phishing & recon)", "order": 15,
    "lessons": [
        L("Why people are the #1 way in",
          "Most breaches don't start with a clever exploit - they start with a person\n"
          "clicking something. Phishing (a fake email), smishing (text), vishing (phone),\n"
          "and pretexting (a believable story) all target the human, not the machine. You\n"
          "can't patch a person, so the defense is recognition + process. That's this layer:\n"
          "learn the tells, and the alarm goes off in your head before you click."),
        L("Anatomy of a phishing email - read the RAW headers",
          "The pretty email hides the truth; the raw headers tell it. Always read the source.\n"
          "  Inspect it on either OS:\n"
          "    Linux/macOS/WSL:  cat suspicious.eml        grep -i 'from\\|spf' suspicious.eml\n"
          "    PowerShell:       Get-Content suspicious.eml  (or:  type suspicious.eml)\n"
          "                      Select-String -Path suspicious.eml -Pattern 'From|spf'\n"
          "  What to check, in order:\n"
          "    From: vs Return-Path/Reply-To  -> do they match? A mismatch is a red flag.\n"
          "    The link's REAL href vs its display text -> hover/read source, never trust text.\n"
          "    The sending domain -> is it the real one, or a lookalike? (next lesson)"),
        L("SPF, DKIM, DMARC - did the mail prove who it is?",
          "Three checks that say whether a 'From' is forged. They show up in the\n"
          "Authentication-Results header:\n"
          "  SPF   - was the sending server ALLOWED to send for that domain?  (pass/fail)\n"
          "  DKIM  - is there a valid cryptographic signature from the domain?  (pass/none)\n"
          "  DMARC - given SPF+DKIM, does the domain's policy say to trust it?  (pass/fail)\n"
          "A real message from a well-run domain passes all three. 'spf=fail ... dkim=none\n"
          "... dmarc=fail' on a From you trust means the sender is almost certainly spoofed.\n"
          "This is the single fastest tell in email triage."),
        L("Lookalike domains and homoglyphs",
          "Attackers register domains that LOOK like yours so a glance trusts them:\n"
          "  - a letter swapped for a twin:  lakefront  ->  1akefront  (one for L),\n"
          "    rn for m, 0 for o, vv for w.  These are 'homoglyphs'.\n"
          "  - an extra word:   lakefront-paper-support.com   (real domain never had it)\n"
          "  - a different TLD:  lakefront-paper.co  instead of .com\n"
          "Defense: read the domain character by character, right-to-left from the TLD.\n"
          "The real registered domain is the last two labels before the TLD - judge THAT,\n"
          "not the subdomain the attacker put your real name in (portal.lakefront.evil.com)."),
        L("Mail flow and MX records (how the letter arrives)",
          "When mail is sent to you@lakefront-paper.com, the sender looks up the domain's\n"
          "MX record (a DNS entry naming the mail servers) and delivers there. You can see\n"
          "a domain's MX with:  nslookup -type=mx lakefront-paper.com  (works on both OSes;\n"
          "Linux/WSL also has  dig mx lakefront-paper.com). Why it matters: the 'Received:'\n"
          "chain in the headers should end at YOUR real MX hosts. A message that entered\n"
          "through servers that aren't your MX, claiming to be internal, is suspect."),
        L("Recon: what attackers learn before they knock",
          "Before any email or scan, attackers gather. Defenders check the same sources to\n"
          "see what they're exposing:\n"
          "  - PUBLIC CODE (GitHub): a repo pushed with a hardcoded password, API key, or\n"
          "    internal hostname is a gift. Real breaches start here constantly. Defense:\n"
          "    scan your own repos for secrets, rotate anything that ever leaked, keep\n"
          "    secrets in env/secret-stores, never in the code or git history.\n"
          "  - SHODAN (shodan.io): a search engine that scans the whole internet and indexes\n"
          "    what every exposed device/service answers - open ports, banners, product and\n"
          "    version. Attackers search it for 'this product, this version, exposed'.\n"
          "    Defense: search Shodan for YOUR own IPs/org and close what shouldn't be public.\n"
          "  The lesson: your attack surface includes everything you've published - code,\n"
          "  DNS, and anything plugged into the internet - not just the app you meant to ship."),
    ],
    "quiz": [
        Q("Fastest signal that a 'From' address is forged?",
          ["the subject is urgent", "spf=fail and dmarc=fail in Authentication-Results",
           "the email has images", "it was sent at night"], 1,
          "SPF/DKIM/DMARC failures mean the sender couldn't prove it owns the domain."),
        Q("'1akefront-paper.com' (digit one, not L) is an example of...",
          ["a subdomain", "a homoglyph lookalike domain", "an MX record", "a DKIM key"], 1,
          "A character swapped for a look-alike twin to pass a quick glance."),
        Q("Where should you judge whether a domain is really yours?",
          ["the subdomain", "the last two labels before the TLD", "the http vs https",
           "the link text"], 1,
          "portal.lakefront.evil.com is really evil.com; judge the registered domain."),
        Q("A hardcoded password pushed to a public GitHub repo is...",
          ["fine if the repo is small", "a common real-world breach entry point",
           "protected by git", "only a problem if starred"], 1,
          "Attackers scan public code for secrets; rotate anything that ever leaked."),
        Q("What does Shodan let someone do?",
          ["send phishing email", "search the internet for exposed devices/services and versions",
           "crack hashes", "sign DKIM"], 1,
          "It indexes what internet-connected services expose - check your own exposure."),
    ],
}

(OUT / "people.json").write_text(json.dumps(people, indent=2, ensure_ascii=True))
print("wrote people.json")
