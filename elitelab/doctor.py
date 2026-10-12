"""`elite doctor` - check your machine and say what (if anything) to install.

The core course needs only Python, so most missions are playable immediately. A few
need an external tool; this tells you which, so you install only what you'll use.
"""
import importlib.util
import shutil
import sys


def _which_any(names):
    for n in names:
        p = shutil.which(n)
        if p:
            return n
    return None


# (label, found-name-or-None, what it's for, how to install)
def _tool_checks():
    return [
        ("C compiler (gcc/clang)", _which_any(["cc", "gcc", "clang"]),
         "bin-01 (reverse a crackme), build-04 (fuzz a C target)",
         "Linux/WSL: sudo apt install build-essential   |   macOS: xcode-select --install"),
        ("gdb + objdump", _which_any(["gdb"]) and _which_any(["objdump"]),
         "bin-01 / build-03 when you reverse for real",
         "sudo apt install gdb binutils"),
        ("John the Ripper", _which_any(["john"]),
         "crack-01, and `elite run john`",
         "sudo apt install john   (Kali: preinstalled)"),
        ("Hashcat", _which_any(["hashcat"]),
         "crack-01 (GPU cracking), `elite run`",
         "sudo apt install hashcat"),
        ("nmap", _which_any(["nmap"]),
         "`elite run nmap`, real scanning of your lab",
         "sudo apt install nmap   |   macOS: brew install nmap"),
        ("sqlmap", _which_any(["sqlmap"]),
         "`elite run sqlmap`",
         "sudo apt install sqlmap   |   pip install sqlmap"),
        ("gobuster / ffuf", _which_any(["gobuster", "ffuf"]),
         "`elite run gobuster` / `ffuf`",
         "sudo apt install gobuster   (or ffuf)"),
    ]


PYLIBS = [("pypdf", "study_books.py: read PDFs"),
          ("sklearn", "study_books.py / elite ask: book search (pip install scikit-learn)"),
          ("markitdown", "study_books.py: read docx/pptx/html/epub")]


def doctor(args=None):
    print("\nelite doctor - what's on this machine\n")
    v = sys.version_info
    py_ok = v >= (3, 8)
    print(f"  [{'ok' if py_ok else '!!'}] Python {v.major}.{v.minor}  "
          f"({'good' if py_ok else 'need 3.8+'})")
    print("       The core course runs on Python alone - most missions are playable now.\n")

    print("  External tools (install only when a mission asks):")
    missing = []
    for label, found, purpose, install in _tool_checks():
        mark = "ok" if found else "--"
        print(f"    [{mark}] {label:<24} for: {purpose}")
        if not found:
            missing.append((label, install))

    print("\n  For study_books.py (optional local book tutor):")
    for mod, purpose in PYLIBS:
        found = importlib.util.find_spec(mod) is not None
        print(f"    [{'ok' if found else '--'}] {mod:<12} {purpose}")

    if missing:
        print("\n  To install what's missing (only if you want those missions):")
        for label, install in missing:
            print(f"    - {label}: {install}")
    print("\n  Nothing stopping you from starting:  elite engage")
    print("  (Missions that need a tool say so in their START_HERE, and fall back gracefully.)\n")
