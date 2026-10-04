"""Slide 26: the spring of his notes, Y = F/k, simulated.

F ~ N(100, 10^2) N; k lognormal with mean 20 N/mm and SD 2 N/mm, so
ln k ~ N(ln 20 - s^2/2, s^2) with s^2 = ln(1 + 0.1^2); F and k independent.
The inputs are a deterministic draw of 20 000 pairs (fig.sample: a Halton
sequence through the inverse CDFs, independent), and every Y is F/k of its
pair. Each panel is the histogram of its variable as a density. At the mean
inputs Y = 100/20 = 5 mm (his number)."""
import numpy as np
from scipy import stats

from fig import Fig, C, fade, pop, sample, wipe

# The definitions, the example, then its three histograms in the order the
# calculation runs (DECK_BRIEF.md "Animated slides"; the blocks' moments are
# in s026.html): F, then k, then the Y they make, each rising from its axis.
ANIM = {"length": 6.4}

N = 20000
S2 = np.log(1 + (2 / 20) ** 2)
K_DIST = stats.lognorm(np.sqrt(S2), scale=np.exp(np.log(20) - S2 / 2))
F, K = sample(N, stats.norm(100, 10), K_DIST)
Y = F / K
assert abs(K_DIST.mean() - 20) < 1e-9 and abs(K_DIST.std() - 2) < 1e-9
assert 100 / 20 == 5.0
assert abs(F.mean() - 100) < 0.1 and abs(K.mean() - 20) < 0.02


def hist(ax, values, edges, color, opacity, anim=None):
    """A density histogram as one filled outline: the bins touching, as a
    simulation's histogram is drawn (no gaps between bars)."""
    h, e = np.histogram(values, edges, density=True)
    xs = np.repeat(e, 2)[1:-1]
    ys = np.repeat(h, 2)
    pts = ax._pts(np.r_[xs[0], xs, xs[-1]], np.r_[0, ys, 0])
    ax.f.poly(pts, fill=color, fill_opacity=opacity, clip=ax.clip, anim=anim)
    return h


PANELS = [  # values, bins, x range, x ticks, y top, y ticks, decimals, x label, colour, opacity, name
    (F, np.arange(50, 150.1, 2), (52, 148), range(60, 141, 20), 0.045, [0, 0.01, 0.02, 0.03, 0.04], 2,
     "Force <m>F</m> (N)", C.navy, 0.62, "F"),
    (K, np.arange(12, 32.01, 0.4), (12, 32), range(15, 31, 5), 0.225, [0, 0.05, 0.1, 0.15, 0.2], 2,
     "Stiffness <m>k</m> (N/mm)", C.amber, 0.8, "k"),
    (Y, np.arange(2, 9.61, 0.15), (2.2, 9.4), range(4, 9, 2), 0.63, [0, 0.2, 0.4, 0.6], 1,
     "Displacement <m>Y</m> (mm)", C.blue, 0.6, "Y"),
]


def histograms(height=300):
    f = Fig(1696, height)
    h = height - 104
    for i, (v, bins, xl, xt, top, yt, nd, lab, col, op, name) in enumerate(PANELS):
        t = 2.5 + 0.9 * i
        ax = f.axes(118 + 576 * i, 8, 418, h, xlim=xl, ylim=(0, top), xticks=xt, yticks=yt,
                    ytick_nd=nd, xlabel=lab, ylabel="Density", anim=fade(t, .4))
        hh = hist(ax, v, bins, col, op, anim=wipe(t + .3, .6, "up"))
        # his letter by the peak, as his picture has it: just right of the
        # histogram where it has fallen to 60% of its peak, level with the top
        j = np.argmax(hh)
        j += np.argmax(hh[j:] < 0.6 * hh.max())
        x, y = ax.P(bins[j + 1], hh.max())
        f.text(x + 18, y, f"<m>{name}</m>", "north west", size=40, color=C.navy, anim=pop(t + .8))
    return f.html()
