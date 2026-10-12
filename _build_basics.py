"""Generates modules/basics.json - a plain-language glossary of the orientation
terms a newcomer hits first (flag, mission, break/fix, checker, hint, CTF, layer).
So `elite ask "what is a flag"` returns a definition, not just a mission that uses
the word. Original, beginner-friendly content."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


basics = {
    "key": "basics", "title": "Getting started (what the words mean)", "order": 1,
    "lessons": [
        L("What a flag is",
          "A flag is a secret token you can only get by actually pulling off the challenge -\n"
          "proof you did the thing, not just read about it. It's a capture-the-flag (CTF)\n"
          "convention. In this tool a flag looks like  flag{sqli_ab12cd34}. When a mission says\n"
          "'submit flag{...}', it means: complete the hack, read the secret token it exposes,\n"
          "and hand it back with  elite lab submit <mission> 'flag{...}'. You can't guess it -\n"
          "you have to earn it, which is the whole point."),
        L("What a mission is",
          "A mission is one hands-on task: a goal, some real files it drops in a working folder,\n"
          "and a checker that verifies your actual work. Missions are the core of the tool -\n"
          "you learn by DOING one, not by reading. Start one with  elite lab start <id>,\n"
          "work in the folder it names, then submit. See them all with  elite lab list."),
        L("Break and fix pairs",
          "Many missions come in two halves. The BREAK half (e.g. app-01) has you exploit a\n"
          "flaw so you understand the risk in your own hands. The FIX half (app-01-fix) has you\n"
          "patch it and proves the patch holds. Breaking teaches the danger; fixing teaches the\n"
          "defense - and the defense is the real job. Always do both."),
        L("What a checker is",
          "The checker is the program that runs YOUR solution to decide if you passed - it runs\n"
          "your code, opens the sockets, re-reads the file. That's why you can't fake a mission:\n"
          "it checks what you actually did, not what you claim. For a break mission it confirms\n"
          "you captured the real flag; for a fix mission it runs your patched file to confirm\n"
          "the hole is closed and normal use still works."),
        L("What a hint is",
          "Stuck on a mission? Unlock a hint with  elite lab hint <id>. Hints escalate: the\n"
          "first is a gentle nudge, the last usually spells out the answer. They're there so you\n"
          "wrestle first and only get the answer after - that's when it sticks. Using a hint is\n"
          "never cheating; charging straight to the last one before thinking just skips the rep."),
        L("Capture the flag (CTF)",
          "CTF is the format this borrows: a safe, legal challenge where success is proven by\n"
          "capturing a hidden 'flag' token. Real CTF platforms (picoCTF, Hack The Box, TryHackMe)\n"
          "run the same loop against bigger targets. Here it's offline and self-contained, so\n"
          "every mission is something you're fully allowed to attack."),
        L("Layers and engage",
          "The missions are grouped into LAYERS that follow how data moves through a company:\n"
          "the Wire (network), the Door (credentials), the App (web), the Host (a machine), the\n"
          "Domain (Active Directory), the Hunt (detection), and the AI product.  elite engage\n"
          "turns those into one connected assessment of the company - recon the surface, then\n"
          "attack any target. Think of layers as the map and engage as walking it."),
        L("Which tool answers which question",
          "Two tutors, different jobs.  elite ask \"...\"  answers from THIS course - concepts,\n"
          "tools, what a mission or term means (instant, no setup).  elite study ask \"...\"\n"
          "answers from YOUR OWN books (the PDFs you indexed), using a local AI. So 'what is a\n"
          "flag' or 'explain this mission' -> elite ask. 'What does Windows Internals say about\n"
          "access tokens' -> elite study ask. Course question vs book question."),
    ],
    "quiz": [
        Q("What is a 'flag' in a mission?",
          ["your username", "a secret token you capture by completing the challenge",
           "a command-line option", "an error message"], 1,
          "The flag proves you actually did the task; you submit it to pass."),
        Q("Why can't you fake completing a mission?",
          ["an instructor watches", "the checker runs your actual work",
           "you sign a pledge", "you can - it's honor-based"], 1,
          "The checker executes your real solution, so only genuine work passes."),
        Q("You want to know what YOUR Windows Internals PDF says. Which command?",
          ["elite ask", "elite study ask", "elite learn", "elite drill"], 1,
          "elite study searches your own indexed books; elite ask answers from the course."),
    ],
}

(OUT / "basics.json").write_text(json.dumps(basics, indent=2, ensure_ascii=True))
print("wrote basics.json")
