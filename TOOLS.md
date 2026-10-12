# Tools & libraries — what we used, and what each one is for

An inventory of the libraries and tools behind this project — especially the
**local AI study system** (`study_books.py` + `LIBRARY.md`) — organized by the problem
each one solves, so you can answer "what would I reach for here, and why this over the
alternatives?"

Everything here is free and links to the official source.

> For the **security** tools (nmap, John, sqlmap, Ghidra, …), the app has guided briefings
> built in — run `elite tools tools-recon`, `tools-web`, `tools-pw`, `tools-ad`, `tools-re`,
> or ask `elite ask "<tool>"`. Those are taught in context, mapped to the mission that uses
> them. This file covers the build/study stack those briefings don't.

---

## Building a local "ask my own books" system (the RAG stack)

This is the pipeline behind `study_books.py`. Five stages — read → chunk → index → retrieve
→ generate — and a library for each.

| Stage / need | Library | What it does | Why this one |
|---|---|---|---|
| Read text out of a PDF | **[pypdf](https://pypdf.readthedocs.io/)** | Pure-Python PDF parser; pulls text page by page | Zero native dependencies; page-level output is what lets answers cite `p.N` |
| Read docx / pptx / html / epub | **[markitdown](https://github.com/microsoft/markitdown)** | Microsoft's converter: office/web docs → Markdown | One library for every non-PDF format; also a fallback for tricky PDFs |
| Make the text *searchable* (the "R" in RAG) | **[scikit-learn](https://scikit-learn.org/)** | `TfidfVectorizer` turns each page into a vector; `cosine_similarity` finds the closest to your question | No model download, instant, excellent for exact-vocabulary technical books. The saved index behaves like a database index: pay the cost once, query fast forever |
| Run a free AI model on your own laptop | **[Ollama](https://ollama.com/)** | Downloads and runs open models locally (`ollama pull llama3.1`) | Private, offline, no account, no bill — your machine is the server |
| The model that writes the answer | **[Llama 3.1 8B](https://ollama.com/library/llama3.1)** (Meta) | Reads the retrieved pages and explains them in plain English | Good enough *because retrieval already did the hard part* — it only has to explain 6 pages, not recall a whole book |
| A stronger model (optional) | **[Anthropic API](https://docs.claude.com/)** | `pip install anthropic`, set `ANTHROPIC_API_KEY` | Sharper reasoning/synthesis; costs pennies, but your excerpts leave the machine |
| Quiet pypdf's font warnings (optional) | **[fontTools](https://github.com/fonttools/fonttools)** | Full font-encoding parsing | Purely cosmetic — text extracts fine without it |

### When keyword search isn't enough — the upgrade path
TF-IDF matches on shared *words*. For questions phrased with different vocabulary than the
book ("how does the OS decide if I'm allowed" vs. the page's "access check"), swap in
**dense embeddings**, which match on *meaning*:

| Need | Library | What it does |
|---|---|---|
| Embed text by meaning | **[sentence-transformers](https://www.sbert.net/)** | Turns text into semantic vectors using a small local model |
| Store & search those vectors | **[FAISS](https://github.com/facebookresearch/faiss)** or **[Chroma](https://www.trychroma.com/)** | Fast nearest-neighbor search over embeddings |

Same five-stage skeleton — only *index* and *retrieve* change. Building a `retrieve_dense()`
next to the current TF-IDF one, and A/B-ing them on your own books, is one of the best
learning exercises in this repo.

---

## The terminal & dev basics we used

| Need | Tool | What it does |
|---|---|---|
| A Unix shell on Windows | **[WSL](https://learn.microsoft.com/windows/wsl/install)** | Real Linux inside Windows (`wsl --install`); where the bash mission commands run |
| Windows-native scripting | **[PowerShell](https://learn.microsoft.com/powershell/)** | Windows/AD automation; covered by the `windows-ps` module. Not the same as bash |
| Install software on Windows | **[winget](https://learn.microsoft.com/windows/package-manager/)** | Windows' package manager: `winget install Ollama.Ollama` |
| Find lines matching a pattern | **grep** / **[ripgrep](https://github.com/BurntSushi/ripgrep)** | Search text, logs, code. ripgrep is grep but much faster and `.gitignore`-aware |
| Talk to a URL from the terminal | **[curl](https://curl.se/)** | HTTP by hand: fetch a page, POST a form, inspect headers |
| Version control | **[git](https://git-scm.com/)** | Clone this repo, pull updates, track your own changes |
| The language it's all in | **[Python 3.8+](https://www.python.org/)** | Runs the whole tool; `pip` installs the libraries above |

`elite learn shell-basics` teaches grep, curl, pipes, paths, and flags from zero.

---

## How the study stack fits together

```
your PDFs ──pypdf──▶ text ──scikit-learn(TF-IDF)──▶ searchable index ──▶ top 6 pages
                                                                            │
                        your question ────────────────────────────────────┘
                                                                            ▼
                                        local model (Ollama + Llama 3.1) explains, cites [book p.N]
```

- **pypdf / markitdown** get the words out of the files.
- **scikit-learn** turns them into something searchable and finds the right pages.
- **Ollama + Llama 3.1** run the model that explains those pages — on your laptop, for free.

Private by construction: your books, your index, and your model all live on your own disk.
See **[`LIBRARY.md`](LIBRARY.md)** for the step-by-step setup.
