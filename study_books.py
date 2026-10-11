#!/usr/bin/env python3
"""study_books.py - a LOCAL, personal study aid over PDFs you legally own.

This is deliberately separate from the course. It builds a search index over PDF
files you place in ./books/ (which is gitignored) so you can look things up while
you study. It never copies book text into the repo, and you should not commit the
index or the PDFs. For personal use only.

Usage:
    pip install pypdf scikit-learn
    # put your own PDFs in ./books/
    python study_books.py index
    python study_books.py search "how does an access check work"

'search' returns the book, page, and a short snippet so you can go read that page
in your own copy - it points you at the source rather than reproducing it.
"""
import pickle
import sys
from pathlib import Path

BOOKS = Path(__file__).resolve().parent / "books"
INDEX = Path(__file__).resolve().parent / ".book_index.pkl"
SNIPPET = 240  # keep snippets short: pointers to your own copy, not a reproduction


def build():
    try:
        from pypdf import PdfReader
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        sys.exit("Install deps first:  pip install pypdf scikit-learn")
    if not BOOKS.is_dir() or not list(BOOKS.glob("*.pdf")):
        sys.exit("Put PDFs you own in ./books/ first.")
    chunks, meta = [], []
    for pdf in sorted(BOOKS.glob("*.pdf")):
        reader = PdfReader(str(pdf))
        for pageno, page in enumerate(reader.pages, 1):
            text = (page.extract_text() or "").strip()
            if len(text) > 40:
                chunks.append(text)
                meta.append((pdf.name, pageno))
    if not chunks:
        sys.exit("No extractable text found.")
    vec = TfidfVectorizer(stop_words="english")
    matrix = vec.fit_transform(chunks)
    INDEX.write_bytes(pickle.dumps({"vec": vec, "matrix": matrix, "meta": meta, "chunks": chunks}))
    print(f"Indexed {len(chunks)} pages from {len(set(m[0] for m in meta))} book(s). "
          f"(Index stays local; it's gitignored.)")


def search(query, k=5):
    if not INDEX.exists():
        sys.exit("No index yet. Run:  python study_books.py index")
    from sklearn.metrics.pairwise import cosine_similarity
    data = pickle.loads(INDEX.read_bytes())
    scores = cosine_similarity(data["vec"].transform([query]), data["matrix"])[0]
    for i in scores.argsort()[::-1][:k]:
        if scores[i] <= 0:
            continue
        book, page = data["meta"][i]
        snippet = " ".join(data["chunks"][i].split())[:SNIPPET]
        print(f"\n[{book} p.{page}]  (relevance {scores[i]:.2f})\n  {snippet}...")
    print("\nOpen those pages in your own copy to read the full text.\n")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "index":
        build()
    elif len(sys.argv) >= 3 and sys.argv[1] == "search":
        search(" ".join(sys.argv[2:]))
    else:
        print(__doc__)
