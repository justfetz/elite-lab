"""The PowerShell module's Python-side contracts (issue #1).

The module itself is tested with Pester (tests/pwsh). These tests cover the parts
that are Python or data, so they run anywhere pytest runs, with no PowerShell:

  - the tab-completion data is generated from elitelab.cli's parser and has not drifted
  - elite_bootstrap.py decodes the arguments PowerShell hands it, exactly
  - every PowerShell drill is well formed: its answer matches its own patterns in the
    engine that checks answers at run time (Python's re), and its wrong answer does not
  - drills/commands.json is what _build_commands.py generates
  - `elite doctor` still prints the shape Test-EliteSetup parses
"""
import base64
import importlib.util
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from elitelab import commands, doctor  # noqa: E402

BOOTSTRAP = ROOT / "pwsh" / "EliteLab" / "elite_bootstrap.py"
COMPLETIONS = ROOT / "pwsh" / "EliteLab" / "EliteLab.Completions.json"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build_completions = _load(ROOT / "pwsh" / "build_completions.py", "build_completions")
bootstrap = _load(BOOTSTRAP, "elite_bootstrap")

BANK = commands.load_bank()
PS_DRILLS = [c for c in BANK if c["platform"] == "powershell"]
NEW_PS_DRILLS = [c for c in PS_DRILLS if c["id"].startswith("ps-")]

# the eight subjects the issue lists, by the id prefix of the drills that cover each
TOPICS = {
    "event logs": ("ps-evt-",),
    "services and scheduled tasks": ("ps-svc-", "ps-task-"),
    "local users and groups": ("ps-user-", "ps-group-"),
    "file permissions": ("ps-acl-",),
    "firewall rules": ("ps-fw-",),
    "file hashes": ("ps-hash-", "ps-sig-"),
    "processes and listening ports": ("ps-proc-", "ps-port-", "ps-conn-"),
    "read-only directory queries": ("ps-ad-",),
}


# ---------- tab completion: generated from the parser, and not drifted ----------
def test_completions_match_the_parser():
    """FAILS when the CLI's parser (or a module it offers as a choice) changes and
    the completion data was not regenerated."""
    assert COMPLETIONS.exists(), "run: python pwsh/build_completions.py"
    committed = json.loads(COMPLETIONS.read_text(encoding="utf-8"))
    assert committed == build_completions.build(), (
        "pwsh/EliteLab/EliteLab.Completions.json is out of date with elitelab.cli's parser.\n"
        "Regenerate it:  python pwsh/build_completions.py")


def test_completions_cover_every_subcommand():
    """Independent of the generator: the names in the data are the names argparse knows."""
    from elitelab.cli import build_parser
    from elitelab.content import load_modules
    import argparse

    parser = build_parser(load_modules())
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    tree = json.loads(COMPLETIONS.read_text(encoding="utf-8"))
    assert [c["name"] for c in tree["commands"]] == list(sub.choices)
    lab = next(c for c in tree["commands"] if c["name"] == "lab")
    assert {c["name"] for c in lab["commands"]} >= {"list", "start", "hint", "submit", "status"}
    learn = next(c for c in tree["commands"] if c["name"] == "learn")
    assert learn["positionals"][0]["choices"] == list(load_modules())


def test_completions_check_flag_detects_drift(tmp_path, monkeypatch):
    stale = tmp_path / "stale.json"
    tree = build_completions.build()
    tree["commands"] = tree["commands"][:-1]            # one subcommand missing
    stale.write_text(build_completions.render(tree), encoding="utf-8")
    monkeypatch.setattr(build_completions, "OUT", stale)
    monkeypatch.setattr(build_completions, "ROOT", tmp_path)
    assert build_completions.main(["--check"]) == 1
    assert build_completions.main([]) == 0              # regenerates
    assert build_completions.main(["--check"]) == 0


# ---------- the bootstrap: arguments arrive exactly as typed ----------
def _encode(args):
    return "".join(base64.b64encode(a.encode("utf-8")).decode("ascii") + ";" for a in args)


@pytest.mark.parametrize("args", [
    [],
    [""],
    ["doctor"],
    ["ask", 'what is "idor"'],
    ["lab", "submit", "wire-01", "flag{10.0.0.5:hunter2}"],
    ["a b", "", "it's", "trailing\\", "100% & | < > ^", "tab\tand\nnewline"],
    ["caf\u00e9", "\u65e5\u672c\u8a9e", "\U0001f512"],
    ["--", "-x", "-p", "80,443"],
])
def test_bootstrap_decodes_arguments_exactly(args):
    assert bootstrap.decode_arguments(_encode(args)) == args


@pytest.mark.parametrize("raw", ["ZG9jdG9y", "!!!;", "ZG9jdG9y;extra"])
def test_bootstrap_rejects_malformed_arguments(raw):
    with pytest.raises(ValueError):
        bootstrap.decode_arguments(raw)


def _run_bootstrap(args, tmp_path, use_env=True):
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    env.pop(bootstrap.ENV_NAME, None)
    argv = [sys.executable, str(BOOTSTRAP)]
    if use_env:
        env[bootstrap.ENV_NAME] = _encode(args)
    else:
        argv += args
    return subprocess.run(argv, capture_output=True, text=True, env=env, input="q\n", timeout=60)


def test_bootstrap_runs_the_cli(tmp_path):
    r = _run_bootstrap(["--version"], tmp_path)
    assert r.returncode == 0 and r.stdout.strip().startswith("elite-lab "), r.stderr


def test_bootstrap_without_the_variable_uses_its_command_line(tmp_path):
    r = _run_bootstrap(["--version"], tmp_path, use_env=False)
    assert r.returncode == 0 and r.stdout.strip().startswith("elite-lab "), r.stderr


def test_bootstrap_returns_the_exit_code_of_a_failing_subcommand(tmp_path):
    r = _run_bootstrap(["learn", "no-such-module"], tmp_path)
    assert r.returncode == 2
    assert "invalid choice" in r.stderr


def test_bootstrap_reads_piped_input_from_the_file_powershell_names(tmp_path):
    """`'q' | elite learn networking`: the module writes the piped text to a file and
    names it in ELITELAB_STDIN, so the answer arrives exactly, on every PowerShell."""
    answers = tmp_path / "input.txt"
    answers.write_text("q\n", encoding="utf-8")
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    env[bootstrap.ENV_NAME] = _encode(["learn", "networking"])
    env[bootstrap.STDIN_ENV_NAME] = str(answers)
    r = subprocess.run([sys.executable, str(BOOTSTRAP)], capture_output=True, text=True,
                       env=env, stdin=subprocess.DEVNULL, timeout=60)
    assert r.returncode == 0, r.stderr
    assert "lesson 1/" in r.stdout and "lesson 2/" not in r.stdout    # 'q' stopped it


def test_bootstrap_reports_piped_input_it_cannot_read(tmp_path):
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    env[bootstrap.STDIN_ENV_NAME] = str(tmp_path / "not-there.txt")
    r = subprocess.run([sys.executable, str(BOOTSTRAP), "--version"], capture_output=True,
                       text=True, env=env, timeout=60)
    assert r.returncode == bootstrap.EXIT_BAD_ARGV
    assert "could not read the piped input" in r.stderr and "Traceback" not in r.stderr


def test_bootstrap_reports_unreadable_arguments(tmp_path):
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    env[bootstrap.ENV_NAME] = "not base64;"
    r = subprocess.run([sys.executable, str(BOOTSTRAP)], capture_output=True, text=True,
                       env=env, timeout=60)
    assert r.returncode == bootstrap.EXIT_BAD_ARGV
    assert "could not read the arguments" in r.stderr and "Traceback" not in r.stderr


def test_bootstrap_works_from_a_path_with_spaces_and_non_ascii(tmp_path):
    clone = tmp_path / "Zo\u00eb M\u00fcller" / "elite lab clone"
    for name in ("elitelab", "modules", "drills"):
        shutil.copytree(ROOT / name, clone / name, ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copy(ROOT / "elite.py", clone / "elite.py")
    (clone / "pwsh" / "EliteLab").mkdir(parents=True)
    shutil.copy(BOOTSTRAP, clone / "pwsh" / "EliteLab" / BOOTSTRAP.name)
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path), PYTHONUTF8="1")
    env[bootstrap.ENV_NAME] = _encode(["doctor"])
    r = subprocess.run([sys.executable, str(clone / "pwsh" / "EliteLab" / BOOTSTRAP.name)],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=60)
    assert r.returncode == 0 and "elite doctor" in r.stdout, r.stderr


# ---------- the drills ----------
def _accepted_by_patterns(drill, text):
    """True when one of the drill's own patterns accepts the text - the same call
    commands.matches() makes, without its exact-answer shortcut."""
    n = commands._norm(text)
    return any(re.fullmatch(pat, n, re.IGNORECASE) for pat in drill.get("accept", []))


def test_drill_bank_is_well_formed():
    ids = [c["id"] for c in BANK]
    assert len(ids) == len(set(ids)), "duplicate drill ids"
    for c in BANK:
        assert {"id", "platform", "prompt", "answer", "why", "accept"} <= set(c), c["id"]
        for pat in c["accept"]:
            re.compile(pat)
    raw = (ROOT / "drills" / "commands.json").read_bytes()
    assert all(b < 128 for b in raw), "drills/commands.json must stay ASCII (Windows reads it as cp1252)"


def test_at_least_thirty_new_powershell_drills_on_every_listed_subject():
    assert len(NEW_PS_DRILLS) >= 30
    for topic, prefixes in TOPICS.items():
        covered = [c["id"] for c in NEW_PS_DRILLS if c["id"].startswith(prefixes)]
        assert len(covered) >= 2, f"too few drills on {topic}: {covered}"
    unplaced = [c["id"] for c in NEW_PS_DRILLS
                if not c["id"].startswith(tuple(p for ps in TOPICS.values() for p in ps))]
    assert not unplaced, f"drills outside the listed subjects: {unplaced}"


@pytest.mark.parametrize("drill", PS_DRILLS, ids=[c["id"] for c in PS_DRILLS])
def test_powershell_drill_answer_matches_and_wrong_answer_does_not(drill):
    assert drill["accept"], "a PowerShell drill needs at least one accept pattern"
    assert _accepted_by_patterns(drill, drill["answer"]), "the answer does not match its own patterns"
    assert commands.matches(drill, drill["answer"])
    wrong = drill.get("wrong")
    assert wrong, "a PowerShell drill needs one plausible wrong answer"
    assert commands._norm(wrong).lower() != commands._norm(drill["answer"]).lower()
    assert not commands.matches(drill, wrong), f"the wrong answer is accepted: {wrong}"
    # sloppy typing must not turn a right answer wrong: case and spacing are free
    assert commands.matches(drill, "  " + drill["answer"].upper().replace(" ", "   ") + " ")


VARIANTS = json.loads((ROOT / "tests" / "drill_variants.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("variant", VARIANTS,
                         ids=["%s: %s" % (v["id"], v["note"]) for v in VARIANTS])
def test_powershell_drill_accepts_what_an_admin_types_and_nothing_that_would_not_run(variant):
    """Other spellings of a right answer are right (where, select, a pipe without
    spaces, columns in another order); a command that would not run, or that answers a
    different question, is not. tests/drill_variants.json is the table; the Pester suite
    reads the same file, so .NET's regex engine has to agree with Python's."""
    drill = next(c for c in PS_DRILLS if c["id"] == variant["id"])
    assert commands.matches(drill, variant["text"]) is variant["accepted"], variant["note"]


def test_commands_json_is_what_the_builder_generates(tmp_path):
    """drills/commands.json is generated. Edit _build_commands.py, then run it."""
    shutil.copy(ROOT / "_build_commands.py", tmp_path / "_build_commands.py")
    runpy.run_path(str(tmp_path / "_build_commands.py"), run_name="__main__")
    generated = json.loads((tmp_path / "drills" / "commands.json").read_text(encoding="utf-8"))
    assert generated == BANK, "run: python _build_commands.py"


# ---------- `elite doctor`: the shape Test-EliteSetup parses ----------
def test_doctor_prints_one_marked_line_per_check(capsys):
    doctor.doctor()
    lines = capsys.readouterr().out.splitlines()
    marked = [ln for ln in lines if re.match(r"^\s*\[(ok|--|!!)\]\s+\S", ln)]
    assert len(marked) == 1 + len(doctor._tool_checks()) + len(doctor.PYLIBS)
    assert re.match(r"^\s*\[(ok|!!)\] Python \d+\.\d+\s+\(.+\)$", marked[0])
    tools = marked[1:1 + len(doctor._tool_checks())]
    assert all(" for: " in ln for ln in tools), "tool lines are '<label>  for: <purpose>'"
    labels = [label for label, _found, _purpose, _install in doctor._tool_checks()]
    assert [re.match(r"^\s*\[..\]\s+(.+?)\s+for: ", ln).group(1) for ln in tools] == labels
    # the section headers Test-EliteSetup groups by
    assert any(ln.startswith("  External tools") and ln.rstrip().endswith(":") for ln in lines)
    assert any("study_books" in ln and ln.rstrip().endswith(":") for ln in lines)
