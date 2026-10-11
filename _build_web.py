"""Generates modules/web-vulns.json - the web vulnerability classes and how bug
hunters find them. Original content (standard OWASP-style concepts), aligned with
the App layer. No book text is reproduced; books stay in local study only."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


web = {
    "key": "web-vulns", "title": "Web vulnerabilities & bug hunting", "order": 55,
    "lessons": [
        L("How bug hunters actually work",
          "Finding web bugs is a repeatable process, not luck:\n"
          "  1. MAP the app - every page, parameter, API endpoint, cookie, header. You can't test "
          "what you haven't found (use a proxy like Burp to record everything).\n"
          "  2. Understand the INTENDED behavior of each feature.\n"
          "  3. Then ask, at every input: what happens if I send something unexpected? Someone "
          "else's ID? A script? A URL? A quote?\n"
          "Bugs live in the gap between what the developer expected and what the app actually "
          "accepts. Most of the classes below are just disciplined versions of that one question."),
        L("IDOR - broken object-level authorization",
          "The app trusts an ID you can change. GET /orders/1001 shows your order; what about "
          "/orders/1002? If it shows someone else's, that's an Insecure Direct Object Reference - "
          "the server authenticated you but never checked you're authorized for THAT object.\n"
          "FIND: change IDs (numbers, UUIDs, filenames) and watch for other users' data.\n"
          "FIX: check ownership on every object access, server-side - never trust the ID alone. "
          "(This is the single most common and lucrative bug-bounty class.)"),
        L("XSS - cross-site scripting",
          "Your input is reflected into a page and runs as script in other users' browsers.\n"
          "  Reflected: your input echoes straight back (a search box that prints your query).\n"
          "  Stored:    your input is saved and shown to others (a comment, a profile name) - worse.\n"
          "FIND: submit a harmless marker like a unique string, see if it lands in HTML unescaped; "
          "then test a script payload on a target you own.\n"
          "FIX: output-encode everything by context, and set a Content-Security-Policy. XSS is "
          "data (your input) being treated as code (script) - the same root cause as SQL injection."),
        L("CSRF - cross-site request forgery",
          "A malicious page makes the victim's browser send an authenticated request to your app "
          "('change email to attacker@evil') using the victim's cookies, without their intent.\n"
          "FIND: does a state-changing request work without an unpredictable token tied to the user?\n"
          "FIX: anti-CSRF tokens, SameSite cookies, and re-auth for sensitive actions."),
        L("SSRF - server-side request forgery",
          "You get the SERVER to make a request for you. A 'fetch this URL' feature pointed at "
          "http://169.254.169.254/ (cloud metadata) or internal hosts can leak credentials or reach "
          "systems you can't touch directly.\n"
          "FIND: any feature that takes a URL/host and fetches it - try internal/metadata addresses.\n"
          "FIX: allow-list destinations, block internal ranges, don't let user input choose the host."),
        L("More classes to carry",
          "  Open redirect   - /login?next=//evil.com sends users offsite; used in phishing.\n"
          "  Auth/session    - weak reset tokens, no rate limiting, session fixation, JWT 'none'.\n"
          "  Info disclosure - stack traces, .git/ exposed, verbose errors, secrets in JS.\n"
          "  Business logic  - buy for a negative quantity, skip a payment step, race conditions.\n"
          "The method never changes: map it, understand it, then push every input past what the "
          "developer expected. Report via the program's responsible-disclosure/bug-bounty process."),
    ],
    "quiz": [
        Q("Changing /orders/1001 to /orders/1002 and seeing someone else's order is...",
          ["XSS", "IDOR", "CSRF", "SSRF"], 1,
          "Insecure Direct Object Reference - missing object-level authorization."),
        Q("Which bug makes the SERVER fetch an internal/metadata URL for you?",
          ["XSS", "CSRF", "SSRF", "Open redirect"], 2,
          "Server-Side Request Forgery - the server makes the request on your behalf."),
        Q("Stored XSS is worse than reflected because...",
          ["it's faster", "it's saved and served to other users automatically",
           "it needs no browser", "it only affects you"], 1,
          "The payload persists and hits every viewer, not just someone you lure to a link."),
        Q("XSS and SQL injection share what root cause?",
          ["weak passwords", "data being treated as code", "no HTTPS", "slow servers"], 1,
          "Untrusted input crossing into a code/interpreter context - the data/code boundary."),
        Q("The right first step in testing any web app is...",
          ["run exploits immediately", "map every page, parameter and endpoint",
           "crack its passwords", "DDoS it"], 1,
          "You can't test what you haven't found - map the full attack surface first."),
    ],
}

(OUT / "web-vulns.json").write_text(json.dumps(web, indent=2, ensure_ascii=True))
print("wrote web-vulns.json")
