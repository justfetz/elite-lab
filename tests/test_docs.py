"""Doc tests: the docs are only worth reading if they cannot drift from the code.

These fail when:
  - the retired company name comes back anywhere in the repo;
  - ATLAS.md, or the generated block in README.md, is not what _build_atlas.py writes;
  - a mission in the registry is missing from the atlas;
  - a doc in the README's doc map is missing, or does not open with its status line;
  - a Markdown doc is not in the doc map;
  - a section of a plan doc does not say whether it is built;
  - a relative link in a doc, or its #anchor, does not resolve;
  - code quoted in a doc is no longer in the file it was quoted from;
  - `elite catalog` names a doc the map does not have.

Everything is read as UTF-8 with universal newlines, so the suite gives the same
answer on Linux, macOS and Windows.
"""
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import _build_atlas  # noqa: E402
from elitelab import world  # noqa: E402

README = ROOT / "README.md"
ATLAS = ROOT / "ATLAS.md"

# The retired name, spelled in two halves so this file passes its own test.
OLD_NAME = "van" + "taris"

STATUSES = ("current", "plan", "reference")
STATUS_RE = re.compile(r"^> \*\*Doc status: (\w+)\*\* · answers: \*(.+)\* · \[doc map\]\(([^)]+)\)$")
BUILT_RE = re.compile(r"^\*\*(Built|Partly built|Not built)\b")
LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
QUOTE_RE = re.compile(r"<!-- quoted from: (\S+) -->\n```[^\n]*\n(.*?)\n```", re.S)

_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "books", "book_index", ".venv", "venv",
              "build", "dist", "node_modules"}


def _read(path):
    return Path(path).read_text(encoding="utf-8")


def _repo_files():
    """Every file that belongs to the repo: tracked, or new and not ignored."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
        files = [ROOT / name for name in out.decode("utf-8").split("\0") if name]
        files = [f for f in files if f.is_file()]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    # not a git checkout (an unpacked archive, say): walk the tree instead
    files = []
    for path in ROOT.rglob("*"):
        parts = path.relative_to(ROOT).parts
        if path.is_file() and not (_SKIP_DIRS & set(parts)) \
                and not any(part.endswith(".egg-info") for part in parts):
            files.append(path)
    return files


def _rel(path):
    return Path(path).relative_to(ROOT).as_posix()


# Markdown under these folders belongs to work that lands separately (the PowerShell
# module and CI, issue #1). It is held to the doc map and the link check once it joins
# the map; until then these tests leave it alone.
OUTSIDE_THE_MAP = ("pwsh", ".github")

REPO_FILES = _repo_files()
MD_FILES = sorted(f for f in REPO_FILES if f.suffix.lower() == ".md"
                  and _rel(f).split("/")[0] not in OUTSIDE_THE_MAP)


def _without_fences(text):
    return re.sub(r"^```.*?^```[^\n]*$", "", text, flags=re.M | re.S)


def _without_code(text):
    return re.sub(r"`[^`\n]*`", "", _without_fences(text))


def _section(text, heading):
    """The body of the `## heading` section."""
    m = re.search(r"^## " + re.escape(heading) + r"\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    assert m, f"no '## {heading}' section"
    return m.group(1)


def _doc_map():
    """[(path, question, status)] from the doc map table in README.md."""
    try:
        body = _section(_read(README), "Doc map")
    except (OSError, AssertionError):
        return []
    rows = []
    for line in body.splitlines():
        m = re.match(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.+?)\s*\|\s*(\w+)\s*\|$", line)
        if m:
            rows.append((m.group(2), m.group(3), m.group(4)))
    return rows


DOC_MAP = _doc_map()
PLAN_DOCS = [path for path, _, status in DOC_MAP if status == "plan"]


# ---------- one company name ----------
def test_old_company_name_is_gone():
    hits = []
    for path in REPO_FILES:
        rel = _rel(path)
        if OLD_NAME in rel.lower():
            hits.append(rel + " (the file's name)")
        try:
            if OLD_NAME.encode("ascii") in path.read_bytes().lower():
                hits.append(rel)
        except OSError:
            pass
    assert not hits, ("the company is Lakefront Paper & Container Co.; the retired name is "
                      "still in:\n  " + "\n  ".join(hits))


# ---------- the generated atlas ----------
def test_atlas_matches_the_code():
    assert ATLAS.is_file(), "ATLAS.md is missing. Run: python3 _build_atlas.py"
    assert _read(ATLAS) == _build_atlas.render_atlas(), (
        "ATLAS.md is not what the registry and the mission modules generate. "
        "Run: python3 _build_atlas.py  (and commit ATLAS.md)")


def test_readme_block_matches_the_code():
    text = _read(README)
    assert _build_atlas.splice_readme(text) == text, (
        "the generated 'what is built' block in README.md is out of date. "
        "Run: python3 _build_atlas.py  (and commit README.md)")


def test_every_registry_mission_is_in_the_atlas():
    atlas = _read(ATLAS)
    campaign = _section(atlas, "Missions, in campaign order")
    listed = re.findall(r"^\|\s*\d+\s*\|\s*\[`([^`]+)`\]", campaign, flags=re.M)
    assert listed == world.campaign_order(), (
        "the atlas's campaign table and the registry disagree on the missions or their order")
    for heading in ("Missions by zone and system", "Missions by layer"):
        body = _section(atlas, heading)
        missing = [e.mission for e in world.exercises() if f"`{e.mission}`" not in body]
        assert not missing, f"'{heading}' in ATLAS.md is missing: {', '.join(missing)}"


# ---------- the doc map and the status lines ----------
def test_doc_map_is_there():
    assert DOC_MAP, "README.md needs a '## Doc map' table: | [doc](doc) | question | status |"
    paths = [path for path, _, _ in DOC_MAP]
    assert len(paths) == len(set(paths)), "a doc is listed twice in the doc map"
    for path, question, status in DOC_MAP:
        assert status in STATUSES, f"{path}: status '{status}' is not one of {STATUSES}"
        assert question.endswith("?"), f"{path}: the map should give the question it answers"
    assert PLAN_DOCS, "the doc map marks no doc as a plan"


@pytest.mark.parametrize("path,question,status", DOC_MAP, ids=[row[0] for row in DOC_MAP])
def test_doc_exists_and_opens_with_its_status_line(path, question, status):
    doc = ROOT / path
    assert doc.is_file(), f"the doc map lists {path}, which does not exist"
    lines = [line for line in _read(doc).splitlines() if line.strip()]
    assert lines[0].startswith("# "), f"{path} should open with its title"
    m = STATUS_RE.match(lines[1])
    assert m, (f"{path}: the line under the title must be the status line, like\n"
               "  > **Doc status: current** · answers: *The question?* · [doc map](README.md#doc-map)\n"
               f"  found: {lines[1]}")
    assert m.group(1) == status, f"{path} says '{m.group(1)}', the doc map says '{status}'"
    assert m.group(2) == question, f"{path}: its question differs from the doc map's"
    back = "#doc-map" if path == "README.md" else "../" * path.count("/") + "README.md#doc-map"
    assert m.group(3) == back, f"{path}: the doc map link should be {back}"


def test_every_doc_is_in_the_map():
    mapped = {path for path, _, _ in DOC_MAP}
    missing = sorted(_rel(f) for f in MD_FILES if _rel(f) not in mapped)
    assert not missing, ("add these to the doc map in README.md, with the question each "
                         "answers and its status: " + ", ".join(missing))


@pytest.mark.parametrize("path", PLAN_DOCS)
def test_plan_doc_sections_say_whether_they_are_built(path):
    text = _without_fences(_read(ROOT / path))
    sections = re.split(r"^#{2,3} ", text, flags=re.M)[1:]
    assert sections, f"{path} has no sections"
    for section in sections:
        lines = [line for line in section.splitlines() if line.strip()]
        title, body = lines[0], lines[1:]
        assert body and BUILT_RE.match(body[0]), (
            f"{path}, section '{title}': a plan section must open with **Built**, "
            "**Partly built** or **Not built**")


def test_catalog_docs_are_in_the_map():
    from elitelab.catalog import DOCS
    mapped = {path for path, _, _ in DOC_MAP}
    unknown = [name for name, _ in DOCS if name.endswith(".md") and name not in mapped]
    assert not unknown, f"`elite catalog` lists docs the doc map does not have: {unknown}"


# ---------- links ----------
def _anchors(md_path):
    """The #anchors GitHub gives a Markdown file's headings."""
    anchors, seen = set(), {}
    for line in _without_fences(_read(md_path)).splitlines():
        m = re.match(r"^#{1,6}\s+(.*?)\s*$", line)
        if not m:
            continue
        title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", m.group(1))     # a link keeps its text
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        n = seen.get(slug, 0)
        seen[slug] = n + 1
        anchors.add(slug if n == 0 else f"{slug}-{n}")
    return anchors


def test_every_relative_link_resolves():
    assert MD_FILES, "found no Markdown files to check"
    broken = []
    for doc in MD_FILES:
        for target in LINK_RE.findall(_without_code(_read(doc))):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("//"):
                continue                                    # http:, https:, mailto: ...
            path_part, _, fragment = target.partition("#")
            dest = (doc.parent / unquote(path_part)).resolve() if path_part else doc
            if not dest.exists():
                broken.append(f"{_rel(doc)}: {target}  (no such file)")
            elif fragment and dest.suffix.lower() == ".md" and fragment not in _anchors(dest):
                broken.append(f"{_rel(doc)}: {target}  (no such heading)")
    assert not broken, "broken relative links:\n  " + "\n  ".join(broken)


# ---------- quoted code ----------
def test_quoted_code_is_still_in_its_source():
    def norm(text):
        return "\n".join(line.rstrip() for line in text.splitlines())

    quotes = [(doc, src, block) for doc in MD_FILES
              for src, block in QUOTE_RE.findall(_read(doc))]
    assert quotes, "MISSIONS.md marks its code quotes with '<!-- quoted from: path -->'"
    stale = [f"{_rel(doc)} quotes {src}" for doc, src, block in quotes
             if not (ROOT / src).is_file() or norm(block) not in norm(_read(ROOT / src))]
    assert not stale, ("a doc quotes code that has since changed; update the quote:\n  "
                       + "\n  ".join(stale))
