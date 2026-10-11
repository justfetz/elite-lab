"""Mission bin-01: Crack the binary (Layer 4 - The Host / reverse engineering).

Compiles a small stripped crackme natively on your machine. The key is XOR-hidden,
so `strings` alone won't reveal it - you recover it with gdb/objdump/Ghidra, then run
the binary to confirm 'Access granted'. This is the feel-the-superpower mission: pull
a secret out of a binary that looks like noise.
"""
import hashlib
import random
import shutil
import subprocess
from pathlib import Path

from .base import Mission

SEED = 0xB1A0C0DE
XOR = 0x5A

SRC = r"""#include <stdio.h>
#include <string.h>
/* the key, XOR-__XORHEX__ encoded so `strings` shows garbage, not the password */
static unsigned char enc[] = { __BYTES__ };
int main(int argc, char **argv) {
    if (argc < 2) { printf("usage: %s <key>\n", argv[0]); return 1; }
    size_t n = sizeof(enc);
    if (strlen(argv[1]) != n) { printf("Access denied.\n"); return 1; }
    for (size_t i = 0; i < n; i++)
        if ((unsigned char)(argv[1][i] ^ __XORHEX__) != enc[i]) { printf("Access denied.\n"); return 1; }
    printf("Access granted.\n");
    return 0;
}
"""


def _key():
    rng = random.Random(SEED)
    return "k3y_" + hashlib.sha1(str(rng.random()).encode()).hexdigest()[:6]


def _compiler():
    return shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")


def setup(workdir: Path):
    key = _key()
    enc = ", ".join(str(ord(c) ^ XOR) for c in key)
    src = SRC.replace("__XORHEX__", f"0x{XOR:02X}").replace("__BYTES__", enc)
    cfile = workdir / "_crackme.c"
    cfile.write_text(src)
    cc = _compiler()
    note = workdir / "START_HERE.txt"
    if cc:
        try:
            subprocess.run([cc, "-s", "-O0", "-o", str(workdir / "crackme"), str(cfile)],
                           check=True, capture_output=True, timeout=60)
            cfile.unlink()  # remove the source - the whole point is to reverse the binary
            note.write_text(
                "crackme is a compiled program that wants a secret key:\n"
                "    ./crackme WRONG        -> Access denied.\n"
                "    ./crackme <the key>    -> Access granted.\n\n"
                "`strings crackme` won't reveal it (the key is XOR-encoded). Reverse it:\n"
                "  strings crackme            # confirm the key isn't sitting in plaintext\n"
                "  objdump -d crackme | less  # find the compare loop and the XOR constant\n"
                "  gdb ./crackme              # break in main, inspect the encoded bytes\n"
                "  (or open it in Ghidra and read the decompiled main)\n"
                "Recover the key, confirm with ./crackme <key>, then submit flag{key}.\n")
            return
        except Exception as e:
            note_err = f"(auto-compile failed: {e})\n"
    else:
        note_err = ""
    note.write_text(
        note_err +
        "This mission needs a C compiler (gcc or clang) to build the crackme on your\n"
        "machine. Install one (Linux/WSL: `sudo apt install build-essential`; macOS:\n"
        "`xcode-select --install`) and run `elite lab start bin-01` again. A _crackme.c\n"
        "was left here, but for the real challenge you want to reverse the COMPILED binary,\n"
        "not read the source.\n")


MISSION = Mission(
    id="bin-01",
    layer="4 The Host",
    title="Crack the binary",
    difficulty="medium",
    goal="Recover the secret key hidden in the compiled 'crackme' and submit flag{key}.",
    flag_format="flag{key}",
    setup=setup,
    solution=lambda wd: f"flag{{{_key()}}}",
    tools=["strings", "objdump", "gdb", "Ghidra"],
    hints=[
        "First prove the easy way fails: `strings crackme` - the key is not in plaintext, "
        "because it's stored XOR-encoded. So you must look at the code.",
        "Disassemble: `objdump -d crackme`. Find the loop in main that compares your input "
        "byte-by-byte. Notice it XORs each input byte with a constant (0x5A) before comparing.",
        "The encoded key bytes are in the binary's data. XOR each of them with 0x5A to get the "
        "key. In gdb you can also just read the 'enc' bytes and decode them. Then ./crackme <key>.",
    ],
    debrief=(
        "You just reverse-engineered a program: no source, yet you recovered its secret by "
        "reading what the compiler emitted. That is the core skill behind malware analysis, "
        "exploit development, and understanding closed-source software like Windows. The XOR "
        "'hiding' here is exactly why obscurity is not security - the key was always in the "
        "binary; you just had to read it. Next stop: patch the compare so ANY key is accepted "
        "(that's binary patching), or try a harder crackme with real anti-analysis tricks."),
)
