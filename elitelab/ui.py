"""Shared terminal helpers: wrapping, prompting, and quiz/drill loops."""
import random
import sys
import textwrap

WIDTH = 88


def say(text=""):
    """Print prose wrapped to WIDTH, but leave indented lines (tables, code) as-is."""
    for para in str(text).split("\n"):
        if para.startswith("  ") or not para:
            print(para)
        else:
            print(textwrap.fill(para, WIDTH))


def rule(title=""):
    print("\n" + title)
    print("-" * min(len(title) or 40, WIDTH))


def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        sys.exit(0)


def run_lessons(mod):
    lessons = mod["lessons"]
    for i, lesson in enumerate(lessons, 1):
        rule(f"{mod['title']} - lesson {i}/{len(lessons)}: {lesson['title']}")
        print()
        say(lesson["body"])
        if i < len(lessons):
            if ask("\n[Enter] next, [q] quit: ").lower() == "q":
                return
    print(f"\nModule complete. Test yourself:  elite quiz {mod['key']}\n")


def run_quiz(mod, record_fn=None):
    questions = list(mod["quiz"])
    if not questions:
        print("This module has no quiz yet.")
        return
    random.shuffle(questions)
    correct = 0
    for n, item in enumerate(questions, 1):
        q, options, answer, why = item["q"], item["options"], item["answer"], item["why"]
        print(f"\nQ{n}/{len(questions)}. {q}")
        order = list(range(len(options)))
        random.shuffle(order)
        letters = list("abcd"[:len(options)])
        for letter, idx in zip(letters, order):
            print(f"   {letter}) {options[idx]}")
        choice = ""
        while choice not in letters:
            choice = ask(f"Your answer ({'/'.join(letters)}): ").lower()
        if order[letters.index(choice)] == answer:
            correct += 1
            print("  Correct. " + why)
        else:
            print(f"  Not quite - the answer is: {options[answer]}\n  {why}")
    pct = round(100 * correct / len(questions))
    print(f"\nScore: {correct}/{len(questions)} ({pct}%)")
    if record_fn:
        record_fn(mod["key"], pct)
    if pct < 80:
        print(f"Tip: review with  elite learn {mod['key']}")
    print()


def show_all_tools(modules):
    """`elite tools` with no module: the whole arsenal at a glance."""
    groups = [(k, m) for k, m in modules.items() if m.get("tools")]
    print("\n  The toolkit  (elite tools <module> for the full briefing on any group)\n")
    for key, mod in groups:
        print(f"  {mod['title']}  [{key}]")
        for t in mod["tools"]:
            what = (t.get("what", "").split(". ")[0]).strip().rstrip(".")
            print(f"    - {t['name']:<16} {what}")
        print()
    print("  Go deeper:")
    print("    elite tools <module>     full briefing (what / legal / setup / try / drill)")
    print("    elite run <tool> ...     run the real tool and get a taught debrief")
    print("    elite doctor             which of these are installed on your machine\n")


def show_tools(mod):
    tools = mod["tools"]
    if not tools:
        print("This module has no tool briefings.")
        return
    for t in tools:
        rule(t["name"])
        say("WHAT   " + t.get("what", ""))
        if t.get("legal"):
            say("LEGAL  " + t["legal"])
        if t.get("install"):
            say("SETUP  " + t["install"])
        if t.get("try"):
            print("  TRY (in your own lab):")
            for cmd in t["try"]:
                print(f"    $ {cmd}")
        if t.get("exercise"):
            say("DRILL  " + t["exercise"])
    print()
