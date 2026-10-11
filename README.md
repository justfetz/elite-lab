# elite-lab

A terminal-first course for going deep on the fundamentals that don't expire:
networking, Windows internals, Linux, and the security tooling professionals
actually use. It's built to be *practiced* — lessons, shuffled quizzes, endless
self-generating drills, and briefings for real tools, each paired with a lab
exercise you run yourself.

The philosophy: knowing *about* security is cheap and getting cheaper. Being able
to *do* it — and to explain why a system breaks and how to defend it — is what
lasts. So every topic ends in something you do at a prompt, not just something you
read.

```
$ python3 elite.py list
$ python3 elite.py learn windows
$ python3 elite.py quiz windows
$ python3 elite.py tools tools-ad
$ python3 elite.py drill subnet
```

---

## ⚖️ Ethics & the law — read this first

Every offensive tool in this course is for machines **you own** or have **explicit
written permission** to test. Unauthorized scanning, access, or attack is a crime
in most of the world (e.g. the US Computer Fraud and Abuse Act, the UK Computer
Misuse Act) — intent doesn't matter, permission does.

Build a lab and stay inside it:

- **Virtual machines** you control (VirtualBox, VMware, Hyper-V, UTM).
- **Docker** targets that are *meant* to be broken: [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/), [DVWA](https://github.com/digininja/DVWA).
- **Active Directory labs:** free Windows Server evaluation VMs, or [GOAD](https://github.com/Orange-Cyberdefense/GOAD) ("Game of Active Directory").
- **CTF platforms** with permission baked in: [picoCTF](https://picoctf.org/), [TryHackMe](https://tryhackme.com/), [Hack The Box](https://www.hackthebox.com/).

The course teaches attack **and** defense on purpose. You learn to protect systems
by understanding exactly how they fall.

---

## Quick start

No dependencies for the course itself — just **Python 3.8+**.

```bash
git clone https://github.com/justfetz/elite-lab.git
cd elite-lab
python3 elite.py list          # see every module and your progress
python3 elite.py learn networking
```

Common commands:

| Command | What it does |
|---------|--------------|
| `elite list` | List all modules, with your best quiz score on each |
| `elite learn <module>` | Read a module's lessons, one page at a time |
| `elite quiz <module>` | Take a shuffled quiz (answers and options both shuffle); score is saved |
| `elite tools <module>` | Show tool briefings: what it is, legal note, setup, commands to try, a drill |
| `elite drill subnet` | Endless, randomly generated subnetting practice |
| `elite drill ports` | Endless well-known-port practice |
| `elite lab list` | HTB-style missions: a goal, a flag, a checker, hints |
| `elite lab start <id>` | Set up a mission (generates the artifact to work on) |
| `elite lab hint <id>` | Unlock the next hint |
| `elite lab submit <id> <flag>` | Check your captured flag |
| `elite progress` | Your best score and attempts per module |
| `elite reset` | Clear saved progress |

(`elite` above is shorthand for `python3 elite.py`.)

## Missions (the training ground)

`elite lab` is where it stops being a book. Each mission gives you a goal, a real
artifact, and a flag to capture; a checker verifies it and hints unlock when you're
stuck — the Hack The Box loop, offline and legal. Try the first one:

```bash
python3 elite.py lab start wire-01     # hunt a brute-force in an access log with grep/awk
python3 elite.py lab start crack-01    # crack a weak MD5 with John/Hashcat
```

See `CURRICULUM.md` for the full "how data moves" layer map and the mission roadmap.

---

## What's inside

**Fundamentals**

| Module | Covers |
|--------|--------|
| `networking` | OSI model, IP addressing & CIDR, TCP vs UDP, ports, DNS |
| `security` | CIA triad, authentication vs authorization, hashing vs encryption, attack classes & defenses, rules of engagement |
| `windows` | processes, access tokens & privileges, services, the Windows API & syscalls, the registry & autostart, objects/handles & access checks |
| `linux` | the shell and pipes, permissions & SUID, processes and listening sockets |

**Tooling** (each tool: what it is → legal note → setup → commands to try → a lab drill)

| Module | Tools |
|--------|-------|
| `tools-recon` | nmap, masscan |
| `tools-web` | Burp Suite, ffuf, sqlmap |
| `tools-ad` | BloodHound, Impacket |
| `tools-pw` | Hashcat, John the Ripper |
| `tools-re` | gdb (+pwndbg), Ghidra, AFL++ |

---

## How it works

The course is **data, not code**. Each module is a JSON file in `modules/` with
lessons, quiz questions, and tool briefings. The Python in `elitelab/` is just the
engine that loads and presents them.

```
elite-lab/
├── elite.py            # entry point:  python3 elite.py ...
├── elitelab/
│   ├── cli.py          # argument parsing and commands
│   ├── content.py      # loads modules/*.json
│   ├── ui.py           # lessons, quizzes, tool briefings
│   ├── drills.py       # self-generating subnet & ports practice
│   └── progress.py     # saves scores to ~/.elite_lab_progress.json
├── modules/            # the course content (JSON)
└── study_books.py      # local-only study aid (see below)
```

### Add your own module

Drop a new file in `modules/`, e.g. `modules/crypto.json`:

```json
{
  "key": "crypto",
  "title": "Applied cryptography",
  "order": 25,
  "lessons": [
    { "title": "Symmetric vs asymmetric", "body": "..." }
  ],
  "quiz": [
    { "q": "AES is...", "options": ["symmetric", "asymmetric"],
      "answer": 0, "why": "One shared key, fast, used for bulk data." }
  ],
  "tools": []
}
```

It appears in `elite list` immediately — no code changes. `_build_modules.py` and
`_build_tools.py` show how the shipped modules were generated.

---

## Studying from your own books (local only)

`study_books.py` runs entirely on your machine over books *you own* (PDF/TXT/MD in a
`books/` folder). It retrieves the most relevant pages locally, then — if you've
configured an LLM — turns them into an answer, a summary, or a full lesson, grounded
in the text and citing `[book p.N]`. Because nothing is ever redistributed, any book
you legally own is fair game for personal study.

```bash
pip install pypdf scikit-learn
# put books you own in ./books/
python3 study_books.py index
python3 study_books.py ask       "how does an access check work?"
python3 study_books.py summarize "the object manager"
python3 study_books.py lesson    "processes and threads"
python3 study_books.py search    "access tokens"      # passages only, no LLM
```

LLM backend is auto-detected: **Anthropic API** (`ANTHROPIC_API_KEY`) or a **local
Ollama** model (`OLLAMA_MODEL=llama3.1`, free/offline). With neither, every command
falls back to showing you the passages to read.

> `books/` and the index are **gitignored and must never be committed.** This repo
> contains only original course content — never book text. For personal study you can
> index anything you own; only open-licensed material (OWASP, NIST, OSTEP, RFCs, …)
> may ever be baked into a shared/public build.

---

## Roadmap

- **Lab exercises with auto-checkers** — a log-analysis drill, a pcap question, a
  "fix this insecure config" challenge, each with a checker that verifies your answer.
- **A Linux privilege-escalation track** to match the Windows one.
- **An AI-security capstone** — build a deliberately vulnerable RAG/text-to-SQL
  agent, make it leak, then harden it (least-privilege identity, query allow-lists,
  treating retrieved text as data). The payoff track for anyone coming from a
  database background.
- **Spaced repetition** — questions you miss come back sooner.

---

## License

Code is released under the MIT License (see `LICENSE`). Course text is original and
free to use for learning. It is not affiliated with any tool, vendor, or book
mentioned.
