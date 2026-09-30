"""Slide 55: trucks at a weigh station, a homogeneous Poisson process with
rate lambda = 2 per hour, three days of 10 hours.

His three days had 2, 3 and 2 trucks in the first 2 h and 24, 13 and 26 in
10 h (expected lambda x 10 = 20). Given those counts, a Poisson process puts
its arrivals independently and uniformly in each window, so each day is
drawn that way: its first-2-h arrivals uniform on [0, 2), the rest uniform on
[2, 10], from numpy's PCG64 generator (Halton points would space the trucks
evenly, and the clumps and gaps are the point of the slide). The seed is the
first from 0 whose first two hours can be counted by eye, trucks there at
least 0.2 h apart, as his note asks the reader to count them; the same draw
on every run.

ticks   one row per day, a tick per truck, the first two hours shaded.
counts  N(t), the trucks so far: a staircase per day, one step per truck,
        around the average lambda t; the count at t = 2 h marked."""
import numpy as np

from fig import Fig, C, num
from s053 import tw

LAM, HOURS = 2.0, 10.0
FIRST = (2, 3, 2)                 # trucks in the first 2 h, his three days
TOTAL = (24, 13, 26)              # trucks in 10 h
COLORS = (C.navy, C.accent, C.blue)
DAYS = ("Day 1", "Day 2", "Day 3")
STYLE = (None, None, "14 5")      # navy and blue differ by line style too


def _days(seed):
    rng = np.random.default_rng(seed)
    out = []
    for a, n in zip(FIRST, TOTAL):
        out.append(np.sort(np.r_[rng.uniform(0, 2, a), rng.uniform(2, HOURS, n - a)]))
    return out


def _countable(days):
    return all(np.diff(t[t < 2]).min() >= 0.2 for t in days)


SEED = next(s for s in range(1000) if _countable(_days(s)))
ARRIVALS = _days(SEED)
for t, a, n in zip(ARRIVALS, FIRST, TOTAL):
    assert (t < 2).sum() == a and len(t) == n and t.max() <= HOURS
assert LAM * HOURS == 20


def ticks():
    f = Fig(832, 440)
    x0, x1, lo, hi = 110, 690, -0.3, 10.3
    X = lambda v: x0 + (np.asarray(v, float) - lo) / (hi - lo) * (x1 - x0)
    base = 344
    rows = (100, 202, 304)
    f.rect(X(0), 4, X(2) - X(0), base - 4, fill=C.steel)
    f.text(X(1), 14, "first 2 h", "north", size=28, color=C.body)
    for y, t, col, day, n in zip(rows, ARRIVALS, COLORS, DAYS, TOTAL):
        for v in t:
            f.line([(X(v), y - 34), (X(v), y + 34)], stroke=col, width=3, cap="butt")
        f.text(0, y, day, "west", size=28, color=col, weight=700)
        f.text(x1 + 14, y, f"{n} trucks", "west", size=28, color=col)
    assert x1 + 14 + tw("13 trucks", 28) < f.w
    # the time axis, bottom only, ticks out
    f.line([(x0, base), (x1, base)], stroke=C.ink, width=2, cap="square")
    for v in range(0, 11, 2):
        f.line([(X(v), base), (X(v), base + 10)], stroke=C.ink, width=2, cap="butt")
        f.text(X(v), base + 24, num(v), "north", cls="tk")
    f.text((x0 + x1) / 2, base + 68, "Time of day (h)", "north", cls="axl")
    return f.html()


def counts():
    f = Fig(832, 440)
    ax = f.axes(96, 8, 716, 334, xlim=(-0.3, 10.3), ylim=(-1.2, 34), xticks=range(0, 11, 2),
                yticks=range(0, 31, 5), xlabel="Time (h)", ylabel="Trucks so far, <m>N(t)</m>")
    ax.vline(2)
    ax.plot([0, HOURS], [0, LAM * HOURS], color=C.ink, width=2.5, dash="9 6")
    for t, col, dash in zip(ARRIVALS, COLORS, STYLE):
        ax.step(np.r_[0, t, HOURS], np.r_[0, np.arange(1, len(t) + 1), len(t)],
                color=col, width=3, dash=dash)
    for t, col in zip(ARRIVALS, COLORS):
        ax.mark(2, (t < 2).sum(), r=8, color=col, ring_w=2.5)
    ax.legend([(d, {"color": c, "dash": s, "width": 3}) for d, c, s in zip(DAYS, COLORS, STYLE)]
              + [("average: 2 per hour × <m>t</m>", {"color": C.ink, "dash": "9 6", "width": 2.5})],
              at="north west", size=26, row=34, pad=14)
    return f.html()
