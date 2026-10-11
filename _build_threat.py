"""Generates modules/threat-modeling.json - original content on threat-modeling
principles (STRIDE, the four questions, data-flow diagrams, trust boundaries).
These are standard industry concepts, written here in original words; no book text
is reproduced."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "modules"


def L(t, b): return {"title": t, "body": b}
def Q(q, o, a, w): return {"q": q, "options": o, "answer": a, "why": w}


tm = {
    "key": "threat-modeling", "title": "Threat modeling", "order": 5,
    "lessons": [
        L("The four questions",
          "Threat modeling is just a disciplined way to ask, of anything you build:\n"
          "  1. What are we building?        (model the system)\n"
          "  2. What can go wrong?           (find the threats)\n"
          "  3. What are we going to do?     (mitigate them)\n"
          "  4. Did we do a good job?        (check your work)\n"
          "That's the whole method. For Northwind AI it's how you derive the hit points "
          "BEFORE you start breaking things - instead of poking randomly, you model the "
          "system, enumerate what can go wrong at each part, and turn each threat into a "
          "mission. Threat modeling is the map; the missions are you walking it."),
        L("STRIDE - what can go wrong",
          "STRIDE is a checklist of the six things that go wrong, each the violation of one "
          "security property:\n"
          "  Spoofing                -> breaks Authentication   (pretending to be someone)\n"
          "  Tampering               -> breaks Integrity        (changing data/code)\n"
          "  Repudiation             -> breaks Non-repudiation   (denying you did it)\n"
          "  Information disclosure   -> breaks Confidentiality   (leaking data)\n"
          "  Denial of service       -> breaks Availability      (knocking it offline)\n"
          "  Elevation of privilege   -> breaks Authorization      (gaining rights)\n"
          "Walk each component and ask 'which of these apply?'. Our missions ARE STRIDE: "
          "crack-01 is Spoofing (stolen creds), app-01 SQLi is Tampering + Information "
          "disclosure + Elevation of privilege, bin-01 defeats a check (Tampering/EoP), "
          "wire-01 is about catching it so the attacker can't repudiate."),
        L("Data flow diagrams and trust boundaries",
          "To find threats you first draw the system as a data flow diagram with four shapes:\n"
          "  - external entities (users, other systems)   - squares\n"
          "  - processes (your code, the app, the agent)   - circles\n"
          "  - data stores (SQL Server, files, the index)  - parallel lines\n"
          "  - data flows (requests, queries, documents)   - arrows\n"
          "Then draw TRUST BOUNDARIES: lines where data crosses from less-trusted to more-"
          "trusted (browser -> app, app -> SQL Server, a customer's uploaded doc -> the RAG "
          "index). Threats cluster on those boundaries. Northwind's boundaries: the internet "
          "edge, the app-to-database link, the AD domain edge, and - the new one - untrusted "
          "content flowing into the AI agent."),
        L("What to do about a threat",
          "For every threat you have four responses:\n"
          "  Mitigate  - add a control that makes it hard (parameterize the query, add MFA)\n"
          "  Eliminate - remove the feature/asset entirely (don't store what you don't need)\n"
          "  Transfer  - make it someone else's job (managed service, insurance, a contract)\n"
          "  Accept    - decide the risk is tolerable and document that decision\n"
          "The blue-team twin of each mission is you MITIGATING: break it, then add the control "
          "and prove it holds. 'Did we do a good job?' means every element of the diagram and "
          "every STRIDE category has an answer - that completeness is what a real assessment delivers."),
        L("Threat modeling the AI product",
          "The RAG agent is Northwind's crown jewel and its newest attack surface, so run STRIDE "
          "on it directly:\n"
          "  Tampering             -> prompt injection: untrusted text in a document becomes "
          "instructions the agent follows\n"
          "  Information disclosure -> the agent retrieves and reveals data the user wasn't allowed "
          "to see (oversharing / weak row-level security)\n"
          "  Elevation of privilege -> an over-permissioned agent identity does more than the user "
          "could (the text-to-SQL agent running as db_owner)\n"
          "  Spoofing / Repudiation -> who did the agent act as, and is it logged?\n"
          "The trust boundary that matters most: the one between RETRIEVED CONTENT and the agent's "
          "INSTRUCTIONS. Treat retrieved text as data, never as commands - that single boundary is "
          "the heart of the capstone."),
    ],
    "quiz": [
        Q("Which STRIDE category does SQL injection that dumps a secret table MOST represent?",
          ["Denial of service", "Information disclosure", "Repudiation", "Spoofing"], 1,
          "Reading data you shouldn't is Information disclosure (it's also Tampering/EoP)."),
        Q("Stolen or cracked credentials are which STRIDE threat?",
          ["Tampering", "Spoofing", "Denial of service", "Repudiation"], 1,
          "Using someone's creds is impersonation = Spoofing (breaks authentication)."),
        Q("Threats cluster where...",
          ["the code is newest", "data crosses a trust boundary", "there are no comments",
           "the database is largest"], 1,
          "Trust boundaries - where data moves from less- to more-trusted - are where to look."),
        Q("Prompt injection against the RAG agent is best described as...",
          ["Denial of service", "untrusted content becoming instructions (Tampering)",
           "a hardware fault", "a weak password"], 1,
          "Retrieved/untrusted text crosses into the instruction flow and is obeyed - Tampering."),
    ],
}

(OUT / "threat-modeling.json").write_text(json.dumps(tm, indent=2, ensure_ascii=True))
print("wrote threat-modeling.json")
