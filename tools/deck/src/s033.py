"""Slide 33: Monte Carlo for his spring, Y = F/k mm.

Model (his slide 26): F ~ N(100, 10^2) N, k lognormal with mean 20 and SD 2
N/mm, independent. His simulation, as his notes give it: N = 200,000 pairs,
seed 2409 (numpy's default generator, F drawn first, then k). It gives his
numbers exactly: mean 5.0516 mm (his 5.052) and SD 0.71725 mm (his 0.717);
the model's own values are 5.050 and 0.716 (slide 32). A pseudo-random draw,
not fig.sample's Halton points: the slide is about simulation error, and a
low-discrepancy draw would not show his numbers or his convergence.

The histogram is the density of the 200,000 outputs on 0.05 mm bins; the two
guides are the output at the mean inputs, 100/20 = 5.00 mm, and the simulated
mean. His three illustrative draws: 100/20 = 5.00, 110/18 = 6.11, 90/22 =
4.09 mm."""
from functools import lru_cache

import numpy as np

from fig import Fig, C, draw, fade, pop, wipe
from s031 import legend

# Why simulate, the four steps one by one, then the run itself
# (DECK_BRIEF.md "Animated slides"; the blocks' moments are in s033.html):
# the histogram of the outputs rises, the output at the mean inputs and the
# simulated mean are marked, each with its legend entry.
ANIM = {"length": 8.4}

N = 200_000
MU_K, SD_K = 20.0, 2.0
S2 = np.log(1 + (SD_K / MU_K) ** 2)
M = np.log(MU_K) - S2 / 2

assert [f"{a / b:.2f}" for a, b in ((100, 20), (110, 18), (90, 22))] == ["5.00", "6.11", "4.09"]


@lru_cache(maxsize=None)
def simulate(seed=2409, n=N):
    """F, k and Y = F/k for n draws of the model (numpy's default generator)."""
    rng = np.random.default_rng(seed)
    F = rng.normal(100, 10, n)
    k = rng.lognormal(M, np.sqrt(S2), n)
    return F, k, F / k


_, _, Y = simulate()
assert f"{Y.mean():.3f}" == "5.052" and f"{Y.std(ddof=1):.3f}" == "0.717"


def hist_area(ax, values, edges, color=C.mist, anim=None):
    """A density histogram drawn as one filled outline (pgfplots' ybar
    interval, bars touching): at 0.05 mm bins, single bars would only buzz."""
    h, e = np.histogram(values, edges, density=True)
    xs = np.repeat(e, 2)[1:-1]
    ys = np.repeat(h, 2)
    ax.area(xs, ys, 0.0, color=color, anim=anim)
    return h


def histogram():
    f = Fig(832, 410)
    # headroom over the peak (0.56) holds the legend clear of the bars
    box, lim = (126, 6, 682, 302), dict(xlim=(2.2, 9.5), ylim=(0, 0.8))
    ax0 = f.axes(*box, frame=False, **lim)
    h = hist_area(ax0, Y, np.arange(2.2, 9.5001, 0.05), anim=wipe(4.8, .8, "up"))
    ax = f.axes(*box, xticks=range(3, 10), yticks=np.arange(0, 0.71, 0.1), ytick_nd=1,
                xlabel="Simulated displacement <m>Y</m> (mm)", ylabel="Density", anim=fade(4.4, .4), **lim)
    ax.vline(Y.mean(), color=C.navy, width=3.5, dash=None, anim=draw(6.0, .35))
    ax.vline(100 / 20, color=C.accent, width=3.5, dash="10 7", anim=draw(5.6, .35))
    bx, by, bw, bh = legend(f, ax.x + ax.w - 12, ax.y + 12, [
        ("Output at mean inputs: 5.00", {"color": C.accent, "width": 3.5, "dash": "10 7"}),
        ("Simulated mean: 5.05", {"color": C.navy, "width": 3.5}),
    ], size=24, row=36, sample=36, pad=12, anchor="north east", anim=[pop(5.6), pop(5.6), pop(6.0)])
    # the legend stays clear of the guides and of every bar under it
    x0 = 2.2 + (bx - ax.x) / ax.w * 7.3
    assert x0 > Y.mean() + 0.1
    mids = np.arange(2.2, 9.5, 0.05) + 0.025
    assert h[mids > x0 - 0.05].max() < 0.8 * (1 - (by + bh - ax.y) / ax.h)
    return f.html()
