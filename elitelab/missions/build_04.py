"""Mission build-04: Build a fuzzer that finds a real crash (Layer 4 - The Host).

You implement a mutation fuzzer and point it at a deliberately vulnerable C program.
The checker compiles the target, hands your fuzz() a run function, and passes only if
your fuzzer discovers an input that actually crashes it. Ties straight to bin-01 and to
your optimization background - a fuzzer is a search over the input space.
"""
import shutil
import subprocess
from pathlib import Path

from .base import Mission

VULN_C = r"""#include <string.h>
int main(int argc, char **argv) {
    char buf[16];
    if (argc > 1) strcpy(buf, argv[1]);   /* classic overflow: no bounds check */
    return 0;
}
"""

SKELETON = r'''#!/usr/bin/env python3
"""A mutation fuzzer. Implement mutate() and fuzz().
The checker imports this file and calls fuzz(run_target)."""
import random


def mutate(data: bytes) -> bytes:
    """Return a mutated input to try. To find a buffer overflow, the mutation that matters
    most is LENGTH - grow the input. Mix in some length growth and some random bytes."""
    # TODO: e.g. return b"A" * random.randint(1, 2000)
    #       (a real fuzzer also flips bytes and inserts metacharacters)
    raise NotImplementedError


def fuzz(run_target) -> bytes:
    """Loop: mutate an input, run it, and RETURN the first input that crashes the target.
    run_target(inp: bytes) -> int returncode.  A negative returncode means the process was
    killed by a signal (e.g. SIGSEGV) - that's a crash."""
    # TODO:
    #   data = b"A"
    #   for _ in range(2000):
    #       candidate = mutate(data)
    #       rc = run_target(candidate)
    #       if rc != 0:            # nonzero or negative = crash/abort
    #           return candidate
    #   return b""
    raise NotImplementedError
'''


def setup(workdir: Path):
    (workdir / "fuzzer.py").write_text(SKELETON)
    (workdir / "START_HERE.txt").write_text(
        "Implement mutate() and fuzz() in fuzzer.py. The target is a C program with a\n"
        "classic unbounded strcpy into a 16-byte buffer - a long enough argument smashes\n"
        "the stack and crashes it. Your fuzzer must discover a crashing input.\n"
        "The checker compiles the target and runs YOUR fuzz(run_target); you pass if the\n"
        "input it returns really crashes the program. Submit BUILT.\n"
        "(Needs a C compiler - gcc/clang - like bin-01.)\n")


def _compile_target(workdir: Path):
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        return None
    src = workdir / "_vuln.c"
    src.write_text(VULN_C)
    out = workdir / "_vuln"
    try:
        subprocess.run([cc, "-O0", "-fno-stack-protector", "-o", str(out), str(src)],
                       check=True, capture_output=True, timeout=60)
        return out
    except Exception:
        # some toolchains force stack protection; try without the flag (SIGABRT still counts)
        try:
            subprocess.run([cc, "-O0", "-o", str(out), str(src)], check=True,
                           capture_output=True, timeout=60)
            return out
        except Exception:
            return None


def check_build(workdir: Path, submitted: str) -> bool:
    target = _compile_target(workdir)
    if target is None:
        return False

    budget = {"n": 0}

    def run_target(inp):
        budget["n"] += 1
        if budget["n"] > 5000:
            raise RuntimeError("fuzz budget exceeded")
        if isinstance(inp, str):
            inp = inp.encode()
        try:
            p = subprocess.run([str(target), inp.decode("latin1", "ignore")],
                               capture_output=True, timeout=5)
            return p.returncode
        except subprocess.TimeoutExpired:
            return -99

    import importlib.util
    spec = importlib.util.spec_from_file_location("_fuzzer", workdir / "fuzzer.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        crashing = mod.fuzz(run_target)
    except Exception:
        return False
    if not crashing:
        return False
    # independently confirm the returned input really crashes the target
    if isinstance(crashing, str):
        crashing = crashing.encode()
    try:
        rc = subprocess.run([str(target), crashing.decode("latin1", "ignore")],
                            capture_output=True, timeout=5).returncode
    except Exception:
        return False
    return rc != 0


MISSION = Mission(
    id="build-04",
    layer="4 The Host",
    title="Build a fuzzer",
    difficulty="medium",
    goal="Implement mutate()/fuzz() so your fuzzer finds an input that crashes the vulnerable "
         "target, then submit BUILT.",
    flag_format="BUILT (after your fuzzer finds a crash)",
    setup=setup,
    checker=check_build,
    tools=["python3", "a C compiler"],
    hints=[
        "The target overflows a 16-byte buffer with strcpy. What kind of input overflows a "
        "fixed buffer? A LONG one. Make mutate() return progressively longer data.",
        "mutate: return b'A' * random.randint(1, 2000). fuzz: loop, run each candidate, return "
        "the first one whose returncode != 0.",
        "A returncode < 0 means a signal killed it (SIGSEGV = -11). That's your crash - return "
        "that input immediately.",
    ],
    debrief=(
        "You built a fuzzer and found a real memory-corruption crash. This is how an enormous "
        "share of real vulnerabilities are discovered - AFL++ and libFuzzer are this idea plus "
        "coverage feedback (they watch which inputs reach NEW code and evolve them), which is "
        "exactly a search/optimization problem - your wheelhouse. You've now built a scanner, a "
        "packet parser, a breakpoint engine, and a fuzzer: the core of an offensive toolkit, by hand."),
)
