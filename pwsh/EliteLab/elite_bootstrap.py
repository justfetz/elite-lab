"""Start elitelab.cli for the EliteLab PowerShell module.

Invoke-Elite cannot put the learner's arguments on Python's command line and
keep them intact on every PowerShell: Windows PowerShell 5.1 drops embedded
double quotes and empty arguments on the way to a native program. So the module
hands them over in the ELITELAB_ARGV environment variable instead - each
argument UTF-8 encoded, then base64, then closed with a ';' - and this file
turns them back into the list elitelab.cli expects.

Text piped to elite in PowerShell arrives the same way and for the same reason:
the module writes it to a UTF-8 file under the temp folder and names the file in
ELITELAB_STDIN. PowerShell's own pipe to a native program is ASCII in 5.1, with a
byte-order mark in front of it when the console is set to UTF-8.

Run without those variables (python elite_bootstrap.py doctor) it uses its own
command line and its own input, so it is also a plain entry point.
"""
import base64
import importlib.util
import os
import sys

ENV_NAME = "ELITELAB_ARGV"
STDIN_ENV_NAME = "ELITELAB_STDIN"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))      # <clone>/pwsh/EliteLab -> <clone>

EXIT_BAD_ARGV = 2
EXIT_NO_PACKAGE = 3


def decode_arguments(raw):
    """'<b64>;<b64>;' -> ['first', 'second'].

    Every argument ends with ';', so '' means no arguments and ';' means one
    empty argument. Raises ValueError on anything else.
    """
    if not raw:
        return []
    parts = raw.split(";")
    if parts[-1] != "":
        raise ValueError("the last argument is not closed with ';'")
    return [base64.b64decode(part.encode("ascii"), validate=True).decode("utf-8")
            for part in parts[:-1]]


def main():
    raw = os.environ.pop(ENV_NAME, None)   # pop: missions that start Python must not inherit it
    if raw is None:
        args = sys.argv[1:]
    else:
        try:
            args = decode_arguments(raw)
        except ValueError as exc:          # binascii.Error and UnicodeError are ValueErrors
            print("elite: could not read the arguments PowerShell passed (%s)." % exc,
                  file=sys.stderr)
            return EXIT_BAD_ARGV

    stdin_path = os.environ.pop(STDIN_ENV_NAME, None)
    if stdin_path:
        try:
            sys.stdin = open(stdin_path, "r", encoding="utf-8")
        except OSError as exc:
            print("elite: could not read the piped input (%s)." % exc, file=sys.stderr)
            return EXIT_BAD_ARGV

    # Python put this file's folder first on the path; the clone's root belongs there.
    if HERE in sys.path:
        sys.path.remove(HERE)
    if os.path.isfile(os.path.join(ROOT, "elitelab", "cli.py")):
        sys.path.insert(0, ROOT)

    if importlib.util.find_spec("elitelab") is None:
        print("elite: the elitelab package was not found.\n"
              "  Import the module from a clone:  Import-Module ./pwsh/EliteLab\n"
              "  or install the package:          pip install -e .",
              file=sys.stderr)
        return EXIT_NO_PACKAGE

    from elitelab.cli import main as elite_main
    sys.argv = [os.path.join(ROOT, "elite.py")] + args
    return elite_main(args)


if __name__ == "__main__":
    sys.exit(main())
