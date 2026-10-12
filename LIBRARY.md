# Build your own library + a free local AI tutor

This guide sets up a private study system: a shelf of books *you own*, searched locally,
with a free AI model running **on your own laptop** — no account, no internet, nothing
leaves your machine. You end up able to ask your books questions in plain English from the
terminal.

It's powered by `study_books.py` (a small local RAG — retrieve relevant pages, then let a
model explain them, grounded in the text and citing `[book p.N]`).

> **The rule, up front:** only index books you **legally own**. The `books/` folder is
> gitignored and **never committed** — your library stays on your disk. This repo ships
> only original and open-licensed material, never book text.

---

## Part 1 — What to put on the shelf

A layered reading list that matches the course. **[FREE]** marks ones you can download
legally and free, right now. The rest are classics worth owning.

### Free & open — grab these today
- **OSTEP — Operating Systems: Three Easy Pieces** — [FREE] `ostep.org`. The clearest OS book written.
- **OWASP Web Security Testing Guide** — [FREE] `owasp.org`. The web-testing bible.
- **NIST SP 800-series** — [FREE] `csrc.nist.gov`. The actual standards defenders are held to.
- **MITRE ATT&CK** — [FREE] `attack.mitre.org`. The shared language for attacker behavior.
- **RFCs** — [FREE] `ietf.org`. How the protocols *actually* work, from the source.

### Foundations (how systems really work)
- **Windows Internals, Part 1 & 2** — Russinovich et al. *(you have these)*
- **Computer Systems: A Programmer's Perspective** — Bryant & O'Hallaron.

### The wire (networking & packets)
- **Computer Networking: A Top-Down Approach** — Kurose & Ross.
- **TCP/IP Illustrated, Vol. 1** — W. Richard Stevens.
- **Practical Packet Analysis** — Chris Sanders.

### The app (web)
- **The Web Application Hacker's Handbook** — Stuttard & Pinto.
- **Real-World Bug Hunting** — Peter Yaworski. *(you have this)*

### Scripting it yourself (offense + defense in Python)
- **Violent Python** — TJ O'Connor. *(you found this)*
- **Black Hat Python** / **Gray Hat Python** — Justin Seitz. *(you have these)*

### Below the surface (binary & reversing)
- **Hacking: The Art of Exploitation** — Jon Erickson. The one that makes it click.
- **Practical Malware Analysis** — Sikorski & Honig.

### The blue side (detection & defense)
- **The Practice of Network Security Monitoring** — Richard Bejtlich.
- **Serious Cryptography** — Jean-Philippe Aumasson.

You don't need all of these. Start with the free ones plus the two or three you already own,
index them, and grow the shelf as you go.

---

## Part 2 — Run a free AI model on your laptop (Ollama)

**Ollama** runs open models locally. One-time setup:

```powershell
winget install Ollama.Ollama      # install (Windows). macOS/Linux: see ollama.com
# close and reopen your terminal so `ollama` is on PATH
ollama pull llama3.1              # download the model (~4.7 GB). This is your local AI.
```

Verify it's alive:

```powershell
ollama run llama3.1 "say hello in one line"
```

If that talks back, you have a working AI model on your own hardware. (It needs roughly
8 GB of free RAM. Tight on memory? `ollama pull llama3.2:3b` is smaller and lighter.)

> Prefer a stronger model and don't mind it leaving your machine? Set `ANTHROPIC_API_KEY`
> instead and `study_books.py` uses Claude automatically. Local-first is the default here
> because your library should stay yours.

---

## Part 3 — Index your library

Put the files you own in `books/` (PDF, TXT, or MD), then build the search index **once**:

```powershell
pip install pypdf scikit-learn        # one-time: the PDF reader + the search math
mkdir books                           # if it doesn't exist yet
#   ... copy your PDFs into books\ ...
python study_books.py index
```

It prints how many pages it indexed. Think of this exactly like a database index: you pay
the cost once, and every question afterward is a fast lookup. **Re-run `index` whenever you
add or change a book** — otherwise the new one won't be searchable.

---

## Part 4 — Ask your books questions (in the terminal)

Point it at your local model, then ask:

```powershell
$env:OLLAMA_MODEL = "llama3.1"        # tell it to use your local AI (this terminal session)
python study_books.py ask "how does an access check work?"
```

Four ways to interrogate the shelf:

```powershell
python study_books.py ask       "why is a SYN scan stealthier than a connect scan?"
python study_books.py summarize "the Windows object manager"
python study_books.py lesson    "processes and threads"      # explanation + key points + quiz
python study_books.py search    "access token"               # just show the raw pages, no model
```

Every answer cites the pages it used (`[book p.N]`) so you can jump to the source and read
it yourself — the model points you *into* the book, it doesn't replace it.

**No model configured?** Every command still works — it falls back to showing you the most
relevant passages to read. The model is the bonus, not the engine.

---

## How it fits together

```
your PDFs ──pypdf──▶ text ──scikit-learn(TF-IDF)──▶ searchable index ──▶ top pages
                                                                            │
                        your question ────────────────────────────────────┘
                                                                            ▼
                                              local model (Ollama) explains, cites [book p.N]
```

- **pypdf** reads the words out of the PDF.
- **scikit-learn** turns them into something searchable and finds the right pages.
- **Ollama** runs the model that explains those pages — on your laptop, for free.

Private by construction: your books, your index, and your model all live on your disk.
