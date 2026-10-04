"""Slide 24: both bands on the one fitted regression of slide 22 (the same 30
households, the same least-squares line). Under his notes' model, independent
normal errors with constant variance, the pointwise 95% intervals at x are

  mean response   yhat(x) +- t * s * sqrt(1/n + (x - xbar)^2 / Sxx)
  next response   yhat(x) +- t * s * sqrt(1 + 1/n + (x - xbar)^2 / Sxx)

with n = 30, s the residual SD (n - 2 degrees of freedom) and t = t(0.975, 28).
The prediction band adds the household-to-household scatter, so it stays
wide however many households are surveyed."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop, seq, wipe
from s022 import X, TRIPS, fitted

# The data and their line, then the two questions (DECK_BRIEF.md "Animated
# slides"; the blocks' moments are in s024.html): the confidence band of the
# mean is uncovered with its block, then the wider prediction band with
# its; each legend entry comes with its band.
ANIM = {"length": 5.8}

N = len(X)
RES = TRIPS - fitted(X)
S = np.sqrt(RES @ RES / (N - 2))
T = stats.t.ppf(0.975, N - 2)
XBAR, SXX = X.mean(), ((X - X.mean()) ** 2).sum()
assert N == 30 and abs(T - 2.0484) < 1e-4


def half(x, new):
    return T * S * np.sqrt(new + 1 / N + (x - XBAR) ** 2 / SXX)


def bands():
    f = Fig(976, 652)
    ax = f.axes(120, 14, 838, 502, xlim=(0.4, 6.6), ylim=(-1.0, 15.6),
                xticks=range(1, 7), yticks=range(0, 15, 2),
                xlabel="Persons per household", ylabel="Daily trips", grid=True, anim=fade(.3, .4))
    x = np.linspace(0.6, 6.4, 200)
    y = fitted(x)
    ax.area(x, y + half(x, 1), y - half(x, 1), color=C.steel2, anim=wipe(4.1, .7))
    ax.area(x, y + half(x, 0), y - half(x, 0), color=C.sky, opacity=0.8, anim=wipe(2.7, .7))
    ax.plot(x, y, color=C.accent, width=3.5, anim=draw(1.6, .6))
    ax.scatter(X, TRIPS, r=6.5, color=C.navy, anim=seq(.6, .03, visual=.25))
    ax.legend([("95% prediction interval", {"kind": "area", "color": C.steel2}),
               ("95% confidence interval for mean", {"kind": "area", "color": C.sky, "opacity": 0.8})],
              at="north west", size=26, row=40, anim=[pop(2.7), pop(4.1), pop(2.8)])
    return f.html()
