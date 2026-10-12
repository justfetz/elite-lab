# Design principles (the North Star)

Decisions that are settled. Build toward these; don't re-litigate them.

1. **Coach over terminal. Real terminal commands are the learning apparatus — period.**
   The learning happens when the user runs real tools (`grep`, `nmap`, `gdb`, `john`, …)
   in their own terminal on real files. The app's job is to assign the right next thing,
   check that it was actually done, and teach the lesson. We train the craft, not a sandbox.

2. **RAG is a feature, not the interface.** `elite ask` / `study_books.py` are the
   knowledge brain — the "what is this?" button, grounded in the user's own books. We do
   NOT put an AI mentor in front of the commands. The commands are the product surface.

3. **There is always exactly one clear next action.** Every screen ends in a concrete
   command. No blank-page "now what?". `engage` names available targets; `path` shows NEXT;
   `ask` links where to go deeper. This is the thing that makes it a product.

4. **Checkers run the user's actual work.** A mission passes because the user's code/analysis
   really works (we open listeners and scan them, compile and fuzz, recompute the AD graph,
   run the agent and confirm the leak) — not because they typed a remembered string.

5. **Offline, legal, zero-setup is the default.** Self-contained missions that work with no
   lab stand-up. Real external tools and live labs are an *optional* graduation step, never
   a prerequisite to start.

6. **Don't clone what exists; hand off to it.** GOAD, Hack The Box, PortSwigger Academy are
   great targets. We're the teacher/coach layer, and we point serious users to them rather
   than rebuilding them.

7. **Content is data; the engine is code.** New lessons/missions/commands are added as data
   or small modules, so the thing grows without touching the core.
