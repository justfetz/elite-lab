# Build spec: what to build next, concretely

> **Doc status: plan** · answers: *What gets built next, and in what order?* · [doc map](README.md#doc-map)

This page is a plan, not a description of the code. Every section opens with **Built**,
**Partly built** or **Not built** and says what exists today. What elite-lab is, and what
is built mission by mission, are in [README.md](README.md) and [ATLAS.md](ATLAS.md). The
long-run picture is [VISION.md](VISION.md); this page is the build brief for it.

Hands-on first. Quizzes are reinforcement, not the point.

---

## The pieces to build

**Partly built.** Each piece below carries its own mark.

### 1. The lab (`lab/` in the repo) — the target "company"

**Partly built**, under `live-lab/` rather than `lab/`.
[live-lab/README.md](live-lab/README.md) is the one place that says which parts exist. Of
the list below, the schema and the web app exist; the Compose file, a flag table and
every AD option do not, and the schema leaves `xp_cmdshell` off.

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

**Partly built.** The first two items are not built: no mission checks a running lab, and
flags are not per user, because every learner gets the same flag for a mission. The
third is partly built: [ATLAS.md](ATLAS.md#break-and-fix-pairs) lists which
break missions have a fix twin.

- A new mission flavor that **checks the lab is reachable**, gives a goal
  ("read `\\dc01\flag.txt`"), lets you use the **real tools**, and **verifies a flag**.
- Per-user **randomized flags** so they can't be memorized or shared.
- Every attack mission gets a **blue-team twin**: after you break in, find it in the logs
  and fix the misconfig; the checker confirms the fix.

### 3. Command-drill mode (`elite drill commands`) — the muscle memory

**Built.** [`elitelab/commands.py`](elitelab/commands.py) runs it over the bank in
`drills/commands.json`.

- Prompts like "enumerate every computer in the domain (PowerShell)" → you **type the real
  command** → it checks syntax against accepted patterns. Repetition of actual keystrokes,
  spaced so weak/stale commands resurface. This is the reflex-builder.

### 4. Guided campaign (`elite path`)

**Built.** The order is the order of the mission records in the world registry
([`elitelab/world.py`](elitelab/world.py)).

- Sequences missions up the layers (Wire → Door → App → Host → Domain → Hunt) so there's a
  clear route from zero to competent, with the next step always obvious.

### 5. Tool tutors (extend `elite run`)

**Partly built.** [`elitelab/runner.py`](elitelab/runner.py) has tutors for nmap, sqlmap,
John and gobuster/ffuf. BloodHound, Impacket and Ghidra tutors are not built.

- Interpreters for **sqlmap, BloodHound, Impacket, John, Ghidra** like the nmap one: run
  the tool, parse the result, teach what it means and what to do next.

### 6. The book-grounded tutor (`elite ask`, powered by `study_books.py`)

**Built.** `elite ask` answers from the course's lessons and names the matching pages of
your indexed books. `elite study` runs the book tutor itself
([`study_books.py`](study_books.py)); [LIBRARY.md](LIBRARY.md) sets it up.

- The local RAG becomes a first-class command available mid-mission.

---

## How the books/PDFs feed all of this

**Partly built.** The pipeline runs today, with two differences from the sketch: PDFs are
read with pypdf (markitdown handles the other formats), and the index is keyword search
(TF-IDF), not embeddings. [TOOLS.md](TOOLS.md) explains the stack and the embeddings
upgrade. Each place the knowledge should show up carries its own mark.

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
  *Built: `elite ask` lists the matching pages and `elite study ask` writes the cited
  answer.*
- **Mission debriefs get deeper.** The "why" behind a Host/Domain mission (tokens, the
  object manager, services, memory) is drafted from the Internals chapters, then rewritten
  in original words for the repo. The book supplies the accuracy; the repo stays clean.
  *Not built as tooling: debriefs are written by hand in each mission module.*
- **`run` debriefs pull the relevant page.** After an nmap/BloodHound run, the explanation
  can cite the exact section that explains the mechanism.
  *Not built: `elite run` ends by printing a `study_books.py ask` command for you to run.*
- **New content generation.** `study_books.py lesson "<topic>"` drafts lessons and practice
  questions straight from the books, so the course deepens as fast as you read.
  *Built: `elite study lesson "<topic>"`.*

**The specific payoff of the Internals books:** they are the authoritative reference for
Layers 4–5 (Host and Domain). Processes, access tokens, the object manager and access
checks, services, and memory *are* the mechanics behind privilege escalation and AD
attacks. So in exactly the missions where guesswork is dangerous, the tutor is grounded in
the real reference — that's how you go from "ran a tool" to "understand the system."

---

## Build order

**Partly built.** Steps 2 and 3 are done. The open work, in order, is step 1, then the
rest of steps 4, 5 and 6.

1. The lab (`docker-compose` + vulnerable app + seed) and the first **live** app mission
   (real SQL Server SQLi, randomized flag) + its blue-team twin.
   *Not built: the schema and the app exist, the Compose file and the live mission do not.*
2. Command-drill mode. *Built.*
3. `elite path` campaign. *Built.*
4. Tool tutors for sqlmap / BloodHound / Impacket / John.
   *Partly built: sqlmap and John.*
5. AD lab scripts + a domain mission (enumerate → find the path → cut it).
   *Partly built: the domain mission exists offline as `domain-01` and `domain-01-fix`;
   the AD lab scripts do not.*
6. `elite ask` wired in, tutor defaulting to local Ollama.
   *Partly built: `elite ask` is wired in. The book tutor uses the Anthropic API when
   `ANTHROPIC_API_KEY` is set and local Ollama when `OLLAMA_MODEL` is set; with neither
   it shows the passages to read.*

The gaps the registry itself shows, such as systems with no mission yet, are listed in
[ATLAS.md](ATLAS.md#planned-not-built).
