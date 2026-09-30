"""Slide 37: three assumed joint models for R and S with the same marginals.

Model: (R, S) jointly normal, R ~ N(100, 10^2) kN, S ~ N(70, 8^2) kN, with
correlation rho = -0.6, 0 or +0.6. G = R - S has mean 30 kN and variance
10^2 + 8^2 - 2 rho (10)(8) = 164 - 160 rho: SD 16.12, 12.81 and 8.25 kN, and
failure P(G < 0) = Phi(-30/SD) = 3.141%, 0.957% and 0.014%, his numbers.

Top: 500 pairs from each joint model (fig.sample: Halton points through a
Gaussian copula, the same every run). Bottom: the density of G with its
failure tail G < 0 in orange, as his caption names it ("orange tail is
P(G < 0)"). His scenario colours: A orange, B navy, C purple, mapped to the
accent, navy and blue."""
import numpy as np
from scipy import stats

from fig import Fig, C, sample

MR, SR, MS, SS = 100.0, 10.0, 70.0, 8.0
RHOS = (-0.6, 0.0, 0.6)
SD = {r: np.sqrt(SR ** 2 + SS ** 2 - 2 * r * SR * SS) for r in RHOS}
PF = {r: stats.norm.cdf(-(MR - MS) / SD[r]) for r in RHOS}
assert [f"{SD[r]:.2f}" for r in RHOS] == ["16.12", "12.81", "8.25"]
assert [f"{100 * PF[r]:.3f}" for r in RHOS] == ["3.141", "0.957", "0.014"]
assert all(abs(SD[r] ** 2 - (164 - 160 * r)) < 1e-9 for r in RHOS)

COL = {-0.6: C.accent, 0.0: C.navy, 0.6: C.blue}
W = 544
X0, PW = 108, 420                    # the plot boxes' left edge and width
PH1, PH2 = 170, 108                  # the scatter's and the density's heights
# six panels at his density: this slide sets its figure words a step smaller
# (s037.html: ticks 24 px, axis labels 26 px), so the bands under a plot are
TICKS, LABEL = 24, 26                # the tick numbers' and the labels' size
XL = 14 + TICKS + 8                  # a plot's bottom to its x label's top
BAND = XL + LABEL                    # a plot's bottom to its x label's foot


def _xlabel(f, ax, s):
    """The x label at this slide's tighter step under its tick numbers
    (fig.py spaces it for 28 px ticks)."""
    f.text(ax.x + ax.w / 2, ax.y + ax.h + XL, s, "north", cls="axl")


def _column(rho, ymax, yticks):
    y1 = 6 + PH1 + BAND + 22         # the subtitle's top: well clear of the label above
    y2 = y1 + LABEL + 8              # the density's top: close under its subtitle
    f = Fig(W, y2 + PH2 + BAND + 4)
    # top: the pairs
    ax = f.axes(X0, 6, PW, PH1, xlim=(68, 134), ylim=(42, 98), xticks=[80, 100, 120],
                yticks=[60, 80], ylabel="Demand <m>S</m> (kN)",
                ylabel_gap=14 + TICKS + 12 + LABEL / 2 + 6)
    _xlabel(f, ax, "Capacity <m>R</m> (kN)")
    r, s = sample(500, stats.norm(MR, SR), stats.norm(MS, SS), rho=rho)
    ax.scatter(r, s, r=3.6, color=COL[rho], opacity=0.55)
    # between: his subtitle, over the plot it describes
    f.text(X0 + PW / 2, y1, f"SD = {SD[rho]:.2f} kN; failure = {100 * PF[rho]:.3f}%", "north",
           size=LABEL)
    # bottom: the margin
    box, lim = (X0, y2, PW, PH2), dict(xlim=(-30, 90), ylim=(0, ymax))
    g = stats.norm(MR - MS, SD[rho])
    xs = np.linspace(-25, 0, 200)
    f.axes(*box, frame=False, **lim).area(xs, g.pdf(xs), color=C.orange)   # "orange tail"
    bx = f.axes(*box, xticks=[-25, 0, 25, 50, 75], yticks=yticks, ytick_nd=2,
                ylabel="Density", ylabel_gap=14 + 2 * TICKS + 12 + LABEL / 2 + 2, **lim)
    _xlabel(f, bx, "Resulting margin <m>G</m> (kN)")
    x = np.linspace(-25, 85, 600)
    bx.plot(x, g.pdf(x), color=COL[rho], width=3.5)
    bx.vline(0, color=C.orange_edge, width=2.5, dash=None)
    return f.html()


def col_a():
    return _column(-0.6, 0.0265, [0, 0.01, 0.02])


def col_b():
    return _column(0.0, 0.0335, [0, 0.01, 0.02, 0.03])


def col_c():
    return _column(0.6, 0.052, [0, 0.02, 0.04])
