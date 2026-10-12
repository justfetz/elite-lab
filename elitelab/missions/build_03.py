"""Mission build-03: Build the breakpoint engine of a debugger (Layer 4 - The Host).

Every software debugger sets a breakpoint the same way: overwrite the target
instruction byte with 0xCC (the x86 INT3 trap), and keep the original byte so you can
restore it and continue. You implement that save-patch-restore engine. On real hardware
this runs through ptrace (PEEK/POKETEXT); here you operate on a code buffer so it's
testable without root, but the mechanism is identical.
"""
from pathlib import Path

from .base import Mission

INT3 = 0xCC

SKELETON = r'''#!/usr/bin/env python3
"""The core of a debugger: software breakpoints via 0xCC (x86 INT3).
Implement plant_breakpoint() and remove_breakpoint()."""

INT3 = 0xCC


def plant_breakpoint(code: bytearray, addr: int) -> int:
    """Save the byte currently at code[addr], overwrite it with INT3 (0xCC),
    and RETURN the saved original byte (you need it to restore later).
    On real hardware: ptrace PEEKTEXT to read, POKETEXT to write 0xCC."""
    # TODO: original = code[addr]; code[addr] = INT3; return original
    raise NotImplementedError


def remove_breakpoint(code: bytearray, addr: int, original: int) -> None:
    """Put the original byte back so execution can continue normally.
    On real hardware: POKETEXT the original byte back."""
    # TODO: code[addr] = original
    raise NotImplementedError


if __name__ == "__main__":
    prog = bytearray(b"\x90\x90\xb8\x2a\x00\x00\x00\xc3")  # nops; mov eax,42; ret
    saved = plant_breakpoint(prog, 2)
    print("breakpoint planted at 2, byte is now", hex(prog[2]))
    remove_breakpoint(prog, 2, saved)
    print("restored, byte is", hex(prog[2]))
'''


def setup(workdir: Path):
    (workdir / "debugger.py").write_text(SKELETON)
    (workdir / "START_HERE.txt").write_text(
        "Implement plant_breakpoint() and remove_breakpoint() in debugger.py.\n"
        "  plant_breakpoint(code, addr): save code[addr], write 0xCC there, return the saved byte.\n"
        "  remove_breakpoint(code, addr, original): write the saved byte back.\n"
        "That save-patch-restore dance IS how gdb sets a breakpoint (via ptrace on a real\n"
        "process). The checker tests it on a code buffer. Submit BUILT when it works.\n")


def check_build(workdir: Path, submitted: str) -> bool:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_dbg", workdir / "debugger.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return False
    try:
        code = bytearray(b"\x90\x91\x92\x93\x94\x95")
        # plant at two addresses
        o1 = mod.plant_breakpoint(code, 1)
        o3 = mod.plant_breakpoint(code, 3)
        if not (o1 == 0x91 and o3 == 0x93 and code[1] == INT3 and code[3] == INT3):
            return False
        # untouched bytes stay
        if code[0] != 0x90 or code[2] != 0x92:
            return False
        # restore in reverse order, buffer returns to original
        mod.remove_breakpoint(code, 3, o3)
        mod.remove_breakpoint(code, 1, o1)
        return code == bytearray(b"\x90\x91\x92\x93\x94\x95")
    except Exception:
        return False


MISSION = Mission(
    id="build-03",
    layer="4 The Host",
    title="Build a debugger's breakpoint engine",
    difficulty="medium",
    goal="Implement plant_breakpoint()/remove_breakpoint() (the 0xCC INT3 trick), then submit BUILT.",
    flag_format="BUILT (after the breakpoint engine works)",
    setup=setup,
    checker=check_build,
    tools=["python3", "ptrace (for the real version)"],
    hints=[
        "plant: read original = code[addr] FIRST, then set code[addr] = 0xCC, then return original. "
        "Order matters - save before you overwrite.",
        "remove: just code[addr] = original. You kept it from plant.",
        "Why 0xCC? It's x86 INT3 - a one-byte instruction that traps to the debugger. gdb writes "
        "it over your instruction, catches the trap, restores the byte, single-steps, re-plants it.",
    ],
    debrief=(
        "That's the heart of every debugger. The full version wires these two functions to ptrace: "
        "PTRACE_PEEKTEXT to read the byte, PTRACE_POKETEXT to write 0xCC, PTRACE_CONT to run, and on "
        "the SIGTRAP you restore the byte, PTRACE_SINGLESTEP, and re-plant. You now understand how "
        "gdb and every RE tool actually stop a running program. Next build: a fuzzer."),
)
