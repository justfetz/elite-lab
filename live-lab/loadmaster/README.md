# LoadMaster — the mill's cutting-stock optimizer

The real optimization problem behind Lakefront Paper: the machine makes a **200″ parent
reel**, and corrugator plants order rolls in specific widths. LoadMaster decides how to
**slit** each reel so all orders are met with the fewest reels and the least **trim waste**.

This is the classic 1-D cutting-stock problem — the authentic business core the whole
company is built around. It's what generates the orders, shipments, and truck loads that the
rest of the lab (OrderDesk, millops, the mill-agent) move around.

## Run it

```bash
pip install ortools        # optional: enables the optimal solver
python cutstock.py
```

It solves a seeded demo order pool two ways and prints the slitting plan:

- **OR-Tools CP-SAT** — enumerates feasible slitting patterns and minimizes reels run (optimal).
- **Greedy first-fit-decreasing** — the fallback if OR-Tools isn't installed.

On the demo pool the optimal plan uses **20 reels at 3.9% trim**; the greedy heuristic needs
**21**. Seeing optimization beat the heuristic by a real reel is the point.

## How it feeds the rest of the lab

```
order pool  ──LoadMaster──▶  slitting plan  ──▶  reels cut  ──▶  trucks loaded by weight
    │                                                                      │
    └──────────────── all of it lands in millops (OrderDesk shows status) ─┘
```

Later this becomes attack surface too — the optimization service takes order input, so it's
a place to practice input validation and denial-of-service thinking — but first and foremost
it's the believable reason the company has data worth protecting.
