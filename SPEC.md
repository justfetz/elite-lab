# Build spec: what to build next, concretely

The one-liner: **a command-line cyber range where you break and defend a small, real
"company" (a domain + an app on SQL Server), the real tools run against it, and a local
AI tutor grounded in your security books explains every step and drills it into memory.**

Hands-on first. Quizzes are reinforcement, not the point.

---

## The pieces to build

### 1. The lab (`lab/` in the repo) — the target "company"
- **`docker-compose.yml`** that stands up:
  - **SQL Server Developer** (`mcr.microsoft.com/mssql/server`), free.
  - A **small vulnerable web app** (Python/Flask) that talks to it: a login + a customer
    search, built with string-concatenated SQL on purpose.
  - Seed SQL: realistic tables, an over-privileged app login (`db_owner`), `xp_cmdshell`
    reachable, a flag in a table the app shouldn't expose.
- **AD options**, documented + scripted where possible: a PowerShell seed script for a
  single Windows Server eval DC with deliberate misconfigs (kerberoastable account, a
  user with DCSync), plus pointers to GOAD for the full forest.
- The kill chain the lab makes possible: **web SQLi → DB → stored cred → domain account →
  Domain Admin**, with logs at every step for the blue-team side.

### 2. Live-target missions (extend the existing mission engine)
- A new mission flavor that **checks the lab is reachable**, gives a goal
  ("read `\\dc01\flag.txt`"), lets you use the **real tools**, and **verifies a flag**.
- Per-user **randomized flags** so they can't be memorized or shared.
- Every attack mission gets a **blue-team twin**: after you break in, find it in the logs
  and fix the misconfig; the checker confirms the fix.

### 3. Command-drill mode (`elite drill commands`) — the muscle memory
- Prompts like "enumerate every computer in the domain (PowerShell)" → you **type the real
  command** → it checks syntax against accepted patterns. Repetition of actual keystrokes,
  spaced so weak/stale commands resurface. This is the reflex-builder.

### 4. Guided campaign (`elite path`)
- Sequences missions up the layers (Wire → Door → App → Host → Domain → Hunt) so there's a
  clear route from zero to competent, with the next step always obvious.

### 5. Tool tutors (extend `elite run`)
- Interpreters for **sqlmap, BloodHound, Impacket, John, Ghidra** like the nmap one: run
  the tool, parse the result, teach what it means and what to do next.

### 6. The book-grounded tutor (`elite ask`, powered by `study_books.py`)
- The local RAG becomes a first-class command available mid-mission.

---

## How the books/PDFs feed all of this

Your books are the **knowledge base the whole tool reasons from** — not copied into it,
but read locally and turned into understanding:

```
your PDFs (Windows Internals P1/P2, + open books)
   → markitdown extracts clean text
   → chunked + embedded in a LOCAL index
   → retrieval finds the right pages for any question
   → an LLM (local Ollama or API) explains, grounded, citing [book p.N]
```

Where that knowledge actually shows up:

- **`elite ask` mid-mission.** Stuck on why SMB (445) or Kerberos (88) matters? The tutor
  answers from *Windows Internals*, not model guesswork — authoritative and cited.
- **Mission debriefs get deeper.** The "why" behind a Host/Domain mission (tokens, the
  object manager, services, memory) is drafted from the Internals chapters, then rewritten
  in original words for the repo. The book supplies the accuracy; the repo stays clean.
- **`run` debriefs pull the relevant page.** After an nmap/BloodHound run, the explanation
  can cite the exact section that explains the mechanism.
- **New content generation.** `study_books.py lesson "<topic>"` drafts lessons and practice
  questions straight from the books, so the course deepens as fast as you read.

**The specific payoff of the Internals books:** they are the authoritative reference for
Layers 4–5 (Host and Domain). Processes, access tokens, the object manager and access
checks, services, and memory *are* the mechanics behind privilege escalation and AD
attacks. So in exactly the missions where guesswork is dangerous, the tutor is grounded in
the real reference — that's how you go from "ran a tool" to "understand the system."

---

## Build order

1. The lab (`docker-compose` + vulnerable app + seed) and the first **live** app mission
   (real SQL Server SQLi, randomized flag) + its blue-team twin.
2. Command-drill mode.
3. `elite path` campaign.
4. Tool tutors for sqlmap / BloodHound / Impacket / John.
5. AD lab scripts + a domain mission (enumerate → find the path → cut it).
6. `elite ask` wired in, tutor defaulting to local Ollama.
