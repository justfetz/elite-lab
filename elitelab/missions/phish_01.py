"""Mission phish-01 (The People layer): triage a phishing email.

Ships a realistic .eml a dispatcher at Lakefront might receive. The learner reads
the RAW headers and body - not a rendered preview - to spot the tells (SPF/DKIM/
DMARC failure, a lookalike sender domain, a link whose real href differs from its
display text) and pulls the flag hidden in the real malicious link.

Flag-based (solution derives from a fixed seed), so no secret sits on disk in the
clear and the generic test covers it. Cross-platform: inspect with cat/grep
(Linux/WSL) or Get-Content/Select-String (PowerShell).
"""
import hashlib
import random
from pathlib import Path

from .base import Mission

SEED = 0x9113F00D


def _flag():
    rng = random.Random(SEED)
    token = hashlib.sha1(str(rng.random()).encode()).hexdigest()[:10]
    return f"flag{{phish_{token}}}"


# The malicious link carries the flag in its query string - you only see it by
# reading the raw source, never by trusting the display text.
EML = '''\
Return-Path: <billing@1akefront-paper-support.com>
Received: from mail.1akefront-paper-support.com (unknown [45.137.201.88])
	by mx.lakefront-paper.com with ESMTP id 7F2A1;
	Tue, 13 Oct 2026 04:12:55 -0700 (PDT)
Authentication-Results: mx.lakefront-paper.com;
	spf=fail (sender IP is 45.137.201.88) smtp.mailfrom=1akefront-paper-support.com;
	dkim=none;
	dmarc=fail (p=reject) header.from=lakefront-paper.com
From: "Lakefront IT Helpdesk" <helpdesk@lakefront-paper.com>
Reply-To: <billing@1akefront-paper-support.com>
To: <dispatch@lakefront-paper.com>
Subject: [ACTION REQUIRED] Your mailbox will be LOCKED in 24 hours
Date: Tue, 13 Oct 2026 04:12:50 -0700
Content-Type: text/html; charset="utf-8"

<html><body>
<p>Dear user,</p>
<p>Your mailbox is over quota and will be <b>locked within 24 hours</b>.
Verify your account now to avoid interruption to order processing.</p>
<p>
  <a href="http://1akefront-paper-support.com/verify?ref=__FLAG__">
     https://portal.lakefront-paper.com/account/verify
  </a>
</p>
<p>Thank you,<br>Lakefront IT</p>
</body></html>
'''


def setup(workdir: Path):
    (workdir / "suspicious_email.eml").write_text(EML.replace("__FLAG__", _flag()))
    (workdir / "START_HERE.txt").write_text(
        "GOAL: triage the phishing email 'suspicious_email.eml'. Read the RAW source\n"
        "(never trust the pretty version), confirm it's a phish, and pull the flag that's\n"
        "hidden in the REAL destination of its 'verify' link. Submit flag{phish_...}.\n\n"
        "Read it on either OS:\n"
        "    Linux / macOS / WSL:   cat suspicious_email.eml\n"
        "    Windows PowerShell:    type suspicious_email.eml      (or Get-Content ...)\n\n"
        "RUN THE TRIAGE CHECKLIST (each line is a real tell):\n\n"
        "  1. AUTH RESULTS   Find the 'Authentication-Results' header. What are spf, dkim,\n"
        "                    and dmarc? (All failing on a From you'd trust = spoofed sender.)\n\n"
        "  2. FROM vs REPLY  Compare the 'From:' domain with 'Return-Path:' and 'Reply-To:'.\n"
        "                    Do they match? A mismatch means the reply goes to the attacker.\n\n"
        "  3. THE DOMAIN     Look hard at the sender/reply domain. Is it really\n"
        "                    lakefront-paper.com, or a lookalike? (Read it character by\n"
        "                    character - one twin letter is all it takes.)\n\n"
        "  4. THE LINK       The link TEXT says portal.lakefront-paper.com. Read the actual\n"
        "                    href in the source - where does it REALLY go? That mismatch is\n"
        "                    the whole trick. The flag is in that real URL.\n\n"
        "  Pull just the links fast:\n"
        "    Linux/WSL:   grep -o 'http[^\"]*' suspicious_email.eml\n"
        "    PowerShell:  Select-String -Path suspicious_email.eml -Pattern 'http[^\"]*'\n\n"
        "  5. CAPTURE:  elite lab submit phish-01 flag{phish_...}\n\n"
        "Stuck? `elite lab hint phish-01`.   Learn the theory:  elite learn people\n")


MISSION = Mission(
    id="phish-01",
    layer="People",
    title="Triage a phishing email",
    difficulty="easy",
    goal="Read the raw headers of suspicious_email.eml, confirm the spoof, and pull the flag "
         "hidden in the real destination of its link. Submit flag{phish_...}.",
    flag_format="flag{phish_...}",
    setup=setup,
    solution=lambda wd: _flag(),
    tools=["a text viewer (cat / type)", "grep / Select-String", "your eyes"],
    hints=[
        "Read the Authentication-Results header: spf=fail, dkim=none, dmarc=fail. The From "
        "says lakefront-paper.com but it could NOT prove it - so the From is forged.",
        "Compare domains: From is helpdesk@lakefront-paper.com, but Return-Path and Reply-To "
        "are @1akefront-paper-support.com. Look closely: that's a digit '1', not an 'L'. "
        "A homoglyph lookalike.",
        "The link's display text is portal.lakefront-paper.com, but the real href is "
        "http://1akefront-paper-support.com/verify?ref=flag{...}. The flag is the ref= value. "
        "Pull it with grep -o 'http[^\"]*' (or Select-String).",
    ],
    debrief=(
        "You triaged a phish the way a defender does: you read the RAW email, not the preview. "
        "Three tells convicted it - SPF/DKIM/DMARC all failed, the Return-Path/Reply-To domain "
        "was a homoglyph lookalike (1akefront, a digit for an L), and the link's real href went "
        "somewhere other than its display text. That's the #1 way real breaches start, and now "
        "the alarm will go off in your head. Defense for the company: DMARC set to p=reject, "
        "user training, and link-rewriting/sandboxing at the mail gateway."),
)

MISSIONS = [MISSION]
