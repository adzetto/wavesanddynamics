"""Slide 59: the autocorrelation of a stationary AR(1),
X_t - mu = phi (X_(t-1) - mu) + eps_t, |phi| < 1, stationary start: rho(h) =
phi^|h| (his notes). His two coefficients: phi = 0.8 (persistent, slow decay)
and phi = -0.6 (alternating), lags 0 to 14."""
import numpy as np

from fig import Fig, C, fade, pop, seq
from s058 import legend_rows

# The model, then its autocorrelation for two values of phi (DECK_BRIEF.md
# "Animated slides"; the blocks' moments are in s059.html): each sequence
# of lags is counted out, the persistent one, then the alternating one.
ANIM = {"length": 5.7}

H = np.arange(0, 15)
PHIS = ((0.8, C.navy), (-0.6, C.accent))
assert np.isclose(0.8 ** 2, 0.64) and np.isclose((-0.6) ** 1, -0.6)


def acf():
    f = Fig(976, 676)
    ax = f.axes(136, 14, 822, 542, xlim=(-0.6, 14.6), ylim=(-0.72, 1.1), xticks=range(0, 15, 2),
                yticks=[-0.5, -0.25, 0, 0.25, 0.5, 0.75, 1], xlabel="Lag (samples)",
                ylabel="Autocorrelation <m>ρ(h)</m>", anim=fade(.9, .4))
    ax.hline(0, color=C.guide, width=2, dash=None, anim=fade(1.2, .3))
    for (phi, col), t0 in zip(PHIS, (1.5, 2.8)):
        rho = phi ** H
        ax.plot(H, rho, color=col, width=3, anim=seq(t0, .07))
        ax.scatter(H, rho, r=7, color=col, anim=seq(t0, .07, visual=.25))
    legend_rows(ax, [[(f"<m>φ = {num}</m>", {"kind": "linemark", "color": col})]
                     for num, (_, col) in zip(("0.8", "−0.6"), PHIS)], size=28, row=42,
                anim=[pop(1.5), pop(1.5), pop(2.8)])
    return f.html()
