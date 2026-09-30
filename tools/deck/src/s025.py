"""Slide 25: 30 annual peak flows and the Gumbel model fitted to them.

The years are a deterministic draw from a Gumbel (largest value) model,
location 165 m3/s, scale 60 m3/s: fig.sample(30, ..., skip=1) gives its
quantiles at k/32, k = 1..31 but 16, a draw with both tails; the draw's
second (independent) coordinate puts the years in order. The flow model is
the maximum likelihood Gumbel fit to those 30 values, and the right panel is
its quantile function against the return period T:

    x_T = loc - scale * ln(-ln(1 - 1/T))

His notes: 30 simulated annual maxima, a fitted Gumbel, a 100-year quantile
"near 421 m3/s" (here 418.8), i.e. 1% annual exceedance."""
import numpy as np
from scipy import stats

from fig import Fig, C, sample

YEARS = 30
Q, ORDER = sample(YEARS, stats.gumbel_r(165, 60), stats.uniform(), skip=1)
FLOWS = Q[np.argsort(ORDER)]                         # year 1, 2, ... 30
LOC, SCALE = stats.gumbel_r.fit(FLOWS)


def quantile(T):
    return LOC - SCALE * np.log(-np.log(1 - 1 / np.asarray(T, float)))


Q100 = float(quantile(100))
assert abs(Q100 - 421) < 5, Q100                      # his "near 421 m3/s"
assert abs(stats.gumbel_r(LOC, SCALE).sf(Q100) - 0.01) < 1e-12


def observed():
    f = Fig(832, 424)
    ax = f.axes(124, 12, 690, 316, xlim=(-0.8, 31.2), ylim=(0, 420),
                xticks=range(0, 31, 5), yticks=range(0, 401, 100),
                xlabel="Year of observation", ylabel="Annual peak flow (m<m>³</m>/s)")
    ax.bars(np.arange(1, YEARS + 1), FLOWS, width=0.72, color=C.steel2, stroke=C.navy)
    return f.html()


def extrapolation():
    f = Fig(832, 424)
    # decade labels as TeX sets them, the exponent inside the maths (fig.log_ticks'
    # <sup> labels read as 20 px to the legibility check)
    ticks, labels = [1, 10, 100], ["<m>10⁰</m>", "<m>10¹</m>", "<m>10²</m>"]
    ax = f.axes(124, 12, 690, 316, xlim=(0.9, 260), ylim=(80, 490), xlog=True,
                xticks=ticks, xticklabels=labels, yticks=range(100, 401, 100),
                xlabel="Return period (years)", ylabel="Flow quantile (m<m>³</m>/s)")
    # pgfplots' minor ticks between the decades, inward, top and bottom
    for d in (1, 10, 100):
        for k in range(2, 10):
            v = d * k
            if v > 260:
                break
            X = float(ax.X(v))
            for y0, y1 in ((ax.y + ax.h, ax.y + ax.h - 6), (ax.y, ax.y + 6)):
                f.line([(X, y0), (X, y1)], stroke=C.ink, width=1.5, cap="butt")
    T = np.geomspace(1.05, 220, 600)
    ax.vline(100, color=C.accent, width=2.5, dash="10 7")
    ax.plot(T, quantile(T), color=C.navy, width=4.5)
    ax.mark(100, Q100, r=10)
    x, y = ax.P(100, Q100)
    f.text(x - 22, y - 30, "1% annual exceedance", "east", color=C.accent)
    return f.html()
