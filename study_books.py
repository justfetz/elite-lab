#!/usr/bin/env python3
"""study_books.py - ask questions, get summaries, and generate lessons from books
you OWN, entirely on your own machine.

This is a personal study aid. It runs on your computer, over files you put in ./books/
(PDF, TXT, or MD). Because it never redistributes anything, you can index any book you
legally own here - including the Windows Internals PDFs. It does two things:

  1. RETRIEVE  - a local index finds the most relevant pages for your question.
  2. SYNTHESIZE - an LLM turns those pages into an answer / summary / lesson, grounded
                  in the text and citing [book p.N]. If no LLM is configured it just
                  shows you the passages to read.

Commands:
    python study_books.py index                      build/refresh the index
    python study_books.py search  "access tokens"    show matching passages (no LLM)
    python study_books.py ask     "how does an access check work?"
    python study_books.py summarize "the object manager"
    python study_books.py lesson  "processes and threads"

LLM backends (auto-detected, in this order):
    - Anthropic API   : set ANTHROPIC_API_KEY  (pip install anthropic)
    - Local Ollama    : run `ollama serve` and set OLLAMA_MODEL=llama3.1 (no API, no cost)
    - none            : commands fall back to showing passages to read yourself

Setup:
    pip install pypdf scikit-learn
    # put PDFs/notes you own in ./books/
"""
import json
import os
import pickle
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BOOKS = ROOT / "books"
INDEX = ROOT / ".book_index.pkl"
TOPK = 6


# ---------- indexing & retrieval (always local) ----------
def _chunk(text, label_prefix, size=1500):
    for i in range(0, len(text), size):
        yield f"{label_prefix} {i // size + 1}", text[i:i + size]


def _read_file(path):
    """Yield (label, text) for a file. PDFs go page-by-page (so citations are p.N);
    other formats go through Microsoft's markitdown when available."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            for i, page in enumerate(PdfReader(str(path)).pages, 1):
                yield f"p.{i}", (page.extract_text() or "")
            return
        except Exception:
            pass  # fall through to markitdown for tricky PDFs
    if ext in {".txt", ".md"}:
        yield from _chunk(path.read_text(encoding="utf-8", errors="ignore"), "chunk")
        return
    # docx/pptx/html/epub/pdf-fallback: markitdown -> one markdown doc, chunked
    try:
        from markitdown import MarkItDown
    except ImportError:
        sys.exit(f"{path.name}: need markitdown for this format.  pip install markitdown")
    md = MarkItDown().convert(str(path)).text_content
    yield from _chunk(md, "section")


def build():
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: F401
    except ImportError:
        sys.exit("Install deps:  pip install pypdf scikit-learn")
    from sklearn.feature_extraction.text import TfidfVectorizer
    if not BOOKS.is_dir() or not any(BOOKS.iterdir()):
        sys.exit("Put books you own (.pdf/.txt/.md) in ./books/ first.")
    chunks, meta = [], []
    exts = {".pdf", ".txt", ".md", ".docx", ".pptx", ".html", ".htm", ".epub"}
    for f in sorted(BOOKS.iterdir()):
        if f.suffix.lower() not in exts:
            continue
        for label, text in _read_file(f):
            if len((text or "").strip()) > 40:
                chunks.append(text)
                meta.append((f.name, label))
    if not chunks:
        sys.exit("No extractable text found in ./books/.")
    vec = TfidfVectorizer(stop_words="english")
    matrix = vec.fit_transform(chunks)
    INDEX.write_bytes(pickle.dumps({"vec": vec, "matrix": matrix, "meta": meta, "chunks": chunks}))
    print(f"Indexed {len(chunks)} pages/chunks from {len(set(m[0] for m in meta))} file(s). "
          "(Local only; gitignored.)")


def retrieve(query, k=TOPK):
    if not INDEX.exists():
        sys.exit("No index yet. Run:  python study_books.py index")
    from sklearn.metrics.pairwise import cosine_similarity
    data = pickle.loads(INDEX.read_bytes())
    scores = cosine_similarity(data["vec"].transform([query]), data["matrix"])[0]
    hits = []
    for i in scores.argsort()[::-1][:k]:
        if scores[i] > 0:
            book, label = data["meta"][i]
            hits.append({"book": book, "page": label, "score": float(scores[i]),
                         "text": data["chunks"][i]})
    return hits


# ---------- optional LLM synthesis ----------
def _llm(prompt, system):
    """Return model text, or None if no backend is configured."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic
        except ImportError:
            sys.exit("Anthropic key set but package missing:  pip install anthropic")
        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("RAG_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=1200, system=system,
            messages=[{"role": "user", "content": prompt}])
        return r.content[0].text
    model = os.environ.get("OLLAMA_MODEL")
    if model:
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        body = json.dumps({"model": model, "system": system, "prompt": prompt,
                           "stream": False}).encode()
        try:
            req = urllib.request.Request(f"{host}/api/generate", data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())["response"]
        except Exception as e:
            sys.exit(f"Ollama call failed ({e}). Is `ollama serve` running?")
    return None


def _context(hits):
    return "\n\n".join(f"[{h['book']} {h['page']}]\n{h['text'].strip()}" for h in hits)


def _show_passages(hits):
    print("\n(No LLM configured - showing the passages to read yourself. Set "
          "ANTHROPIC_API_KEY or OLLAMA_MODEL to get written answers.)\n")
    for h in hits:
        snippet = " ".join(h["text"].split())[:300]
        print(f"[{h['book']} {h['page']}]  (relevance {h['score']:.2f})\n  {snippet}...\n")


SYSTEM = ("You are a precise study tutor. Use ONLY the provided excerpts from the user's "
          "own books. Cite sources inline as [book p.N]. If the excerpts do not cover the "
          "question, say so plainly. Explain in your own words - do not reproduce long verbatim "
          "passages. Keep it clear and grounded.")


def _synthesize(hits, task):
    if not hits:
        print("No relevant passages found. Try different words or re-index.")
        return
    answer = _llm(f"Excerpts from my books:\n\n{_context(hits)}\n\n{task}", SYSTEM)
    if answer is None:
        _show_passages(hits)
    else:
        print("\n" + answer.strip() + "\n")
        print("Sources: " + ", ".join(sorted({f"{h['book']} {h['page']}" for h in hits})) + "\n")


def cmd_ask(q):
    _synthesize(retrieve(q), f"Answer this question grounded in the excerpts: {q}")


def cmd_summarize(topic):
    _synthesize(retrieve(topic),
                f"Summarize what these excerpts say about '{topic}' as a tight briefing "
                "with a few bullet points.")


def cmd_lesson(topic):
    _synthesize(retrieve(topic),
                f"Write a short lesson on '{topic}' from these excerpts: a plain-language "
                "explanation, 3-5 key points, and 3 quiz questions with answers. Ground every "
                "claim in the excerpts and cite pages.")


def cmd_search(q):
    _show_passages(retrieve(q))


if __name__ == "__main__":
    cmds = {"index": lambda a: build(), "search": cmd_search, "ask": cmd_ask,
            "summarize": cmd_summarize, "lesson": cmd_lesson}
    if len(sys.argv) >= 2 and sys.argv[1] in cmds:
        if sys.argv[1] == "index":
            build()
        elif len(sys.argv) >= 3:
            cmds[sys.argv[1]](" ".join(sys.argv[2:]))
        else:
            print(f"Usage: python study_books.py {sys.argv[1]} \"your text\"")
    else:
        print(__doc__)
