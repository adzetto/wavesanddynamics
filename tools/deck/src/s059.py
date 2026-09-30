"""Slide 59: the autocorrelation of a stationary AR(1),
X_t - mu = phi (X_(t-1) - mu) + eps_t, |phi| < 1, stationary start: rho(h) =
phi^|h| (his notes). His two coefficients: phi = 0.8 (persistent, slow decay)
and phi = -0.6 (alternating), lags 0 to 14."""
import numpy as np

from fig import Fig, C
from s058 import legend_rows

H = np.arange(0, 15)
PHIS = ((0.8, C.navy), (-0.6, C.accent))
assert np.isclose(0.8 ** 2, 0.64) and np.isclose((-0.6) ** 1, -0.6)


def acf():
    f = Fig(976, 676)
    ax = f.axes(136, 14, 822, 542, xlim=(-0.6, 14.6), ylim=(-0.72, 1.1), xticks=range(0, 15, 2),
                yticks=[-0.5, -0.25, 0, 0.25, 0.5, 0.75, 1], xlabel="Lag (samples)",
                ylabel="Autocorrelation <m>ρ(h)</m>")
    ax.hline(0, color=C.guide, width=2, dash=None)
    for phi, col in PHIS:
        rho = phi ** H
        ax.plot(H, rho, color=col, width=3)
        ax.scatter(H, rho, r=7, color=col)
    legend_rows(ax, [[(f"<m>φ = {num}</m>", {"kind": "linemark", "color": col})]
                     for num, (_, col) in zip(("0.8", "−0.6"), PHIS)], size=28, row=42)
    return f.html()
