#!/usr/bin/env python3
"""Generate the tab-completion data for the EliteLab PowerShell module.

The data is read from elitelab.cli's own argparse parser, so the PowerShell
side never keeps its own list of subcommands, options or choices:

    python pwsh/build_completions.py            # rewrite EliteLab.Completions.json
    python pwsh/build_completions.py --check    # exit 1 if the file is out of date

Run it after any change to the parser or to the modules it offers as choices.
tests/test_pwsh_assets.py and the Pester suite both fail when the two drift.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "pwsh" / "EliteLab" / "EliteLab.Completions.json"
SCHEMA = 1

# argparse words these two differently across Python versions; fixed text keeps
# the generated file identical on every Python the project supports.
BUILTIN_HELP = {
    argparse._HelpAction: "show the help for this command and exit",
    argparse._VersionAction: "show the elite-lab version and exit",
}


def _nargs(action):
    """How many words a positional takes: an int, or one of ? * + ... as argparse spells it."""
    if action.nargs is None:
        return 1
    return action.nargs


def describe(parser):
    """One parser as plain data: its options, its positionals and its subcommands."""
    options, positionals, commands = [], [], []
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            helps = {choice.dest: (choice.help or "") for choice in action._choices_actions}
            for name, sub in action.choices.items():
                node = {"name": name, "help": helps.get(name, "")}
                node.update(describe(sub))
                commands.append(node)
        elif action.option_strings:
            options.append({
                "flags": list(action.option_strings),
                "help": BUILTIN_HELP.get(type(action), action.help or ""),
                "takes_value": action.nargs != 0,
            })
        else:
            positionals.append({
                "name": action.dest,
                "help": action.help or "",
                "nargs": _nargs(action),
                "choices": None if action.choices is None else [str(c) for c in action.choices],
            })
    return {"options": options, "positionals": positionals, "commands": commands}


def build():
    """The completion tree for the CLI as it is right now."""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from elitelab.cli import build_parser
    from elitelab.content import load_modules

    parser = build_parser(load_modules())
    tree = {"schema": SCHEMA, "generated_by": "pwsh/build_completions.py", "prog": parser.prog}
    tree.update(describe(parser))
    return tree


def render(tree):
    return json.dumps(tree, indent=2, ensure_ascii=True) + "\n"


def committed():
    """The tree in the committed file, or None when it is missing or unreadable."""
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="do not write; exit 1 when the committed file is out of date")
    args = ap.parse_args(argv)
    tree = build()
    if args.check:
        if committed() != tree:
            print("%s is out of date with elitelab.cli's parser.\n"
                  "Regenerate it:  python pwsh/build_completions.py" % OUT.relative_to(ROOT),
                  file=sys.stderr)
            return 1
        print("%s matches the parser." % OUT.relative_to(ROOT))
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(tree))
    print("wrote %s" % OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
