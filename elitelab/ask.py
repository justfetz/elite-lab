"""`elite ask "<question>"` - the in-tool tutor.

Answers from the course's own lessons instantly (no dependencies, no setup). If you've
indexed your own books with study_books.py, it also points you at the relevant pages.
This is the feature that makes the tool answer the kind of questions you'd otherwise
have to go look up: 'how does an access check work', 'what is IDOR', 'why 0xCC'.
"""
import math
import re
from collections import Counter
from pathlib import Path

from .content import load_modules

ROOT = Path(__file__).resolve().parent.parent
BOOK_INDEX = ROOT / ".book_index.pkl"

STOP = {"the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and", "or",
        "in", "on", "at", "for", "with", "how", "what", "why", "when", "where", "does",
        "do", "did", "work", "works", "working", "it", "this", "that", "these", "those",
        "i", "you", "we", "they", "my", "your", "can", "could", "would", "should", "me",
        "about", "into", "from", "as", "by", "s", "vs", "between", "explain", "tell"}


def _words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _score(query_words, text, idf):
    tc = Counter(_words(text))
    return sum(tc[w] * idf.get(w, 1.0) for w in query_words)


def _snippet(body, query_words, width=320):
    low = body.lower()
    pos = -1
    for w in query_words:
        i = low.find(w)
        if i != -1 and (pos == -1 or i < pos):
            pos = i
    if pos == -1:
        pos = 0
    start = max(0, pos - 60)
    chunk = " ".join(body[start:start + width].split())
    return ("..." if start > 0 else "") + chunk + "..."


def _book_hits(query):
    """Optional: if the user has indexed their own books, surface the best pages."""
    if not BOOK_INDEX.exists():
        return []
    try:
        import pickle
        from sklearn.metrics.pairwise import cosine_similarity
        data = pickle.loads(BOOK_INDEX.read_bytes())
        scores = cosine_similarity(data["vec"].transform([query]), data["matrix"])[0]
        out = []
        for i in scores.argsort()[::-1][:3]:
            if scores[i] > 0:
                out.append(data["meta"][i])   # (book, page)
        return out
    except Exception:
        return []


def _corpus():
    """Every askable thing in the app: lessons, tool briefings, and missions.
    Each entry: (tag_to_show, title, text_to_search, how_to_go_deeper)."""
    entries = []
    for key, mod in load_modules().items():
        for lesson in mod["lessons"]:
            entries.append((f"[{key}] {lesson['title']}", lesson["title"],
                            lesson["title"] + " " + lesson["body"], f"elite learn {key}"))
        for t in mod["tools"]:
            txt = " ".join(t.get(f, "") for f in ("name", "what", "exercise"))
            entries.append((f"[{key}] tool: {t['name']}", t["name"], txt, f"elite tools {key}"))
    try:
        from .missions import load_missions
        for mid, m in load_missions().items():
            entries.append((f"[mission {mid}] {m.title}", m.title,
                            m.title + " " + m.goal + " " + m.debrief, f"elite lab start {mid}"))
    except Exception:
        pass
    return entries


def ask(query):
    query_words = {w for w in _words(query) if w not in STOP and len(w) > 1}
    if not query_words:
        print("Ask a question, e.g.:  elite ask \"how does an access check work\"")
        return
    entries = _corpus()
    n = len(entries)
    df = Counter()
    for _, _, text, _ in entries:
        for w in set(_words(text)):
            df[w] += 1
    idf = {w: math.log((n + 1) / (df.get(w, 0) + 1)) + 1 for w in query_words}
    scored = []
    for tag, title, text, deeper in entries:
        s = _score(query_words, text, idf) + 3 * _score(query_words, title, idf)
        if s > 0:
            scored.append((s, tag, text, deeper))
    scored.sort(key=lambda t: t[0], reverse=True)

    if not scored:
        print(f"\nNothing in the app matches that yet. Try different words, or index your "
              f"books and run: python3 study_books.py ask \"{query}\"\n")
        return

    print(f"\nOn \"{query}\":\n")
    for s, tag, text, deeper in scored[:3]:
        print(f"  {tag}")
        print("  " + _snippet(text, query_words) + f"\n  -> {deeper}\n")

    books = _book_hits(query)
    if books:
        print("Your books go deeper:")
        for b, p in books:
            print(f"  {b} {p}")
        print(f"  (full answer: python3 study_books.py ask \"{query}\")")
    elif not BOOK_INDEX.exists():
        print(f"For cited answers from your own books: study_books.py ask \"{query}\"")
    print()
