#!/usr/bin/env python3
"""LoadMaster's cutting-stock solver - Lakefront Paper & Container Co.

The real optimization problem behind the mill: a paper machine produces a wide
"parent" reel (here, 200 inches). Corrugator-plant customers order rolls in
specific widths. You must SLIT the 200" reel into those widths, deciding how
many parent reels to run and how to cut each, so that:

  - every order's demand is met, and
  - total TRIM WASTE (the leftover strip on each reel) is minimized.

This is the classic 1-D cutting-stock problem. We solve it two ways:

  - OPTIMAL:  OR-Tools CP-SAT over feasible slitting patterns (minimize reels).
  - FALLBACK: first-fit-decreasing greedy, if ortools isn't installed.

    pip install ortools        # for the optimal solver
    python cutstock.py         # runs a demo order pool on a 200" reel
"""
import random
from dataclasses import dataclass

REEL_WIDTH = 200          # inches of the parent reel
MIN_TRIM_OK = 0           # a pattern may use up to the full width


@dataclass(frozen=True)
class Order:
    plant: str
    width: int            # roll width in inches
    demand: int           # rolls needed


def mock_order_pool(seed: int = 7) -> list:
    """A believable pool of corrugator-plant orders (seeded = reproducible)."""
    rng = random.Random(seed)
    widths = [40, 44, 55, 62, 70, 88]          # common linerboard roll widths
    plants = ["Rockford", "Gary", "Milwaukee"]
    pool = []
    for w in widths:
        pool.append(Order(rng.choice(plants), w, rng.randint(5, 18)))
    return pool


# ---------- pattern enumeration ----------
def feasible_patterns(widths, reel=REEL_WIDTH):
    """Every maximal way to pack these widths into one reel, as count-vectors.
    A pattern is a tuple (c0, c1, ...) = how many of each width it slits."""
    patterns = []

    def rec(i, remaining, counts):
        if i == len(widths):
            if remaining < min(widths):        # maximal: can't fit any more
                patterns.append(tuple(counts))
            return
        maxc = remaining // widths[i]
        for c in range(maxc + 1):
            counts.append(c)
            rec(i + 1, remaining - c * widths[i], counts)
            counts.pop()

    rec(0, reel, [])
    # drop the all-zero pattern and any that aren't maximal duplicates
    seen, out = set(), []
    for p in patterns:
        if any(p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _trim(pattern, widths):
    return REEL_WIDTH - sum(c * w for c, w in zip(pattern, widths))


# ---------- optimal solver (OR-Tools CP-SAT) ----------
def solve_optimal(orders):
    from ortools.sat.python import cp_model
    widths = [o.width for o in orders]
    demand = [o.demand for o in orders]
    patterns = feasible_patterns(widths)

    m = cp_model.CpModel()
    # x[p] = how many parent reels we cut using pattern p
    x = [m.NewIntVar(0, sum(demand), f"x{p}") for p in range(len(patterns))]
    # meet every order's demand
    for i in range(len(orders)):
        m.Add(sum(patterns[p][i] * x[p] for p in range(len(patterns))) >= demand[i])
    # minimize total reels run
    m.Minimize(sum(x))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    status = solver.Solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    used = [(patterns[p], int(solver.Value(x[p]))) for p in range(len(patterns))
            if solver.Value(x[p]) > 0]
    return used, widths


# ---------- greedy fallback (first-fit decreasing) ----------
def solve_greedy(orders):
    widths = [o.width for o in orders]
    pieces = []
    for o in orders:
        pieces += [o.width] * o.demand
    pieces.sort(reverse=True)
    reels = []                      # each reel = remaining capacity
    layout = []                     # each reel = list of widths cut
    for w in pieces:
        for r in range(len(reels)):
            if reels[r] >= w:
                reels[r] -= w
                layout[r].append(w)
                break
        else:
            reels.append(REEL_WIDTH - w)
            layout.append([w])
    # fold identical layouts into (pattern, count)
    from collections import Counter
    patt = Counter()
    for cut in layout:
        vec = tuple(cut.count(w) for w in widths)
        patt[vec] += 1
    return list(patt.items()), widths


# ---------- report ----------
def report(orders, used, widths, label):
    total_reels = sum(n for _, n in used)
    total_trim = sum(_trim(p, widths) * n for p, n in used)
    produced = REEL_WIDTH * total_reels
    print(f"\n=== LoadMaster slitting plan ({label}) ===")
    print(f"Parent reel: {REEL_WIDTH}\"   Orders in pool:")
    for o in orders:
        print(f"   {o.plant:<10} {o.width}\" x {o.demand}")
    print(f"\n{'reels':>5}  pattern (widths cut)                 trim\"")
    for p, n in sorted(used, key=lambda t: -t[1]):
        cut = " + ".join(f"{c}x{w}\"" for c, w in zip(p, widths) if c)
        print(f"{n:>5}  {cut:<36} {_trim(p, widths):>4}")
    pct = 100 * total_trim / produced if produced else 0
    print(f"\nTotal parent reels: {total_reels}")
    print(f"Total trim waste:   {total_trim}\"  ({pct:.1f}% of produced width)")
    print("The whole game: fewer reels and less trim = more margin per ton.\n")
    return total_reels, total_trim


def plan(orders=None):
    orders = orders or mock_order_pool()
    try:
        res = solve_optimal(orders)
        if res:
            used, widths = res
            return report(orders, used, widths, "OR-Tools CP-SAT, optimal")
    except ImportError:
        pass
    used, widths = solve_greedy(orders)
    return report(orders, used, widths, "greedy FFD - install ortools for optimal")


if __name__ == "__main__":
    plan()
