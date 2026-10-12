"""Mission priv-01: Linux privilege escalation (Layer 4 - The Host).

Offline analysis of a host snapshot (sudo rights + SUID binaries + a cron job). Find the
ONE thing that lets a normal user become root. Teaches the GTFOBins mindset: a trusted
program used in an untrusted way.
"""
from pathlib import Path

from .base import Mission

ANSWER = "awk"   # sudo NOPASSWD on awk -> awk 'BEGIN{system("/bin/sh")}' = root shell

SUDO_L = """\
User lowpriv may run the following commands on host01:
    (root) NOPASSWD: /usr/bin/awk
    (root) /usr/bin/systemctl status *
    (root) NOPASSWD: /usr/bin/apt-get update
"""

SUID = """\
-rwsr-xr-x 1 root root   68208 /usr/bin/passwd
-rwsr-xr-x 1 root root  166056 /usr/bin/sudo
-rwsr-xr-x 1 root root   44664 /usr/bin/chsh
-rwsr-xr-x 1 root root   55528 /usr/bin/mount
-rwsr-xr-x 1 root root   31032 /usr/bin/pkexec
"""

CRON = """\
# /etc/crontab
*/5 * * * * root /opt/scripts/backup.sh
0 2 * * *   root /usr/bin/apt-get upgrade -y
"""


def setup(workdir: Path):
    (workdir / "sudo_l.txt").write_text(SUDO_L)
    (workdir / "suid.txt").write_text(SUID)
    (workdir / "crontab.txt").write_text(CRON)
    (workdir / "START_HERE.txt").write_text(
        "You have a shell as the user 'lowpriv' on host01. Three recon outputs are here:\n"
        "  sudo_l.txt   what sudo lets you run (output of `sudo -l`)\n"
        "  suid.txt     SUID root binaries on the box\n"
        "  crontab.txt  scheduled root jobs\n\n"
        "Exactly ONE of these gives a clean path to a ROOT SHELL. Name the program you'd abuse.\n"
        "Submit flag{program}  (just the program name).\n"
        "Tip: think GTFOBins - a legitimate tool that can be made to spawn a shell when run as root.\n")


MISSION = Mission(
    id="priv-01",
    layer="4 The Host",
    title="Linux privilege escalation",
    difficulty="medium",
    goal="From the host snapshot, find the one program that gives a root shell. Submit flag{program}.",
    flag_format="flag{program}",
    setup=setup,
    solution=lambda wd: f"flag{{{ANSWER}}}",
    tools=["your brain", "GTFOBins (the concept)"],
    hints=[
        "Start with sudo_l.txt - anything you can run as root with NOPASSWD is the first place to "
        "look. Which of those can execute arbitrary commands or spawn a shell?",
        "systemctl status is restricted (just status), apt-get update only updates - neither hands "
        "you a shell directly. But one of the NOPASSWD entries is a general-purpose text tool that "
        "can run system commands.",
        "awk can run shell commands: sudo awk 'BEGIN{system(\"/bin/sh\")}' - and since it runs as "
        "root (NOPASSWD), that's an instant root shell. The answer is awk.",
    ],
    debrief=(
        "That's the GTFOBins mindset: privilege escalation is usually a TRUSTED program used in an "
        "UNTRUSTED way. awk, vim, find, less, tar and dozens more can spawn shells or read/write "
        "files; give one of them sudo/SUID and you've handed out root. DEFENSE: grant sudo only to "
        "specific, non-shell-capable commands, avoid NOPASSWD on anything scriptable, and audit SUID "
        "binaries. (systemctl was close - unrestricted `sudo systemctl` is also exploitable via its "
        "pager; here it was limited to `status *`.)"),
)
