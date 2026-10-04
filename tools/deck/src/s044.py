"""Slide 44: time averages of one record, for two stationary models (his notes).

Left: independent zero-mean samples X_t ~ N(0, 1). The time average of one
record of length L, (X_1 + ... + X_L)/L, settles on the ensemble mean 0 as L
grows (its SD is 1/sqrt(L)). Four records of 700 samples are a fixed
pseudo-random draw (numpy's PCG64, seed below; a quasi-random sequence would
converge faster than independent samples do, so it would not be faithful here).

Right: a random constant, X(t) = Z with Z ~ N(0, 1) drawn once per realization.
The process is strictly stationary, yet each record's time average is its own
Z at every length, while the ensemble mean is 0 (dashed). The four offsets are
four equally likely values of Z, its 1/8, 3/8, 5/8 and 7/8 quantiles (fig.sample)."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, SERIES, draw, fade, pop, sample

# One panel, then the other (DECK_BRIEF.md "Animated slides"; the blocks'
# moments are in s044.html): the four time averages draw out together as
# the record lengthens, settling on the common mean on the left and on
# their own offsets on the right.
ANIM = {"length": 7.2}

L = np.arange(1, 701)
rng = np.random.default_rng(4401)
MEANS = np.cumsum(rng.standard_normal((4, len(L))), axis=1) / L
Z = sample(4, norm(), skip=3)
assert np.allclose(np.sort(Z), norm.ppf([1 / 8, 3 / 8, 5 / 8, 7 / 8]))
assert np.abs(MEANS[:, -1]).max() < 0.1               # settled near the common mean
YL = 2.0
assert np.abs(MEANS).max() < YL and np.abs(Z).max() < YL

W, H = 832, 470
BOX = (104, 48, 704, 330)


def _panel(title, curves, t0):
    f = Fig(W, H)
    x, y, w, h = BOX
    f.text(x, y - 12, title, "south west", size=28, color=C.ink, font="serif", weight=600,
           anim=pop(t0))
    ax = f.axes(x, y, w, h, xlim=(-15, 715), ylim=(-YL, YL), xticks=range(0, 701, 100),
                yticks=[-2, -1, 0, 1, 2], xlabel="Record length", ylabel="Time average",
                anim=fade(t0 + .1, .4))
    ax.hline(0, width=2, anim=fade(t0 + .4, .3))
    for k, c in enumerate(curves):
        ax.plot(L, c, color=SERIES[k], width=3, anim=draw(t0 + .6, 1.6))
    return f.html()


def independent():
    return _panel("Independent zero-mean samples", MEANS, 0.3)


def constant():
    return _panel("Random constant: <m>X(t) = Z</m>", [np.full(len(L), z) for z in Z], 3.3)
