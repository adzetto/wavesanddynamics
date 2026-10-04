"""Slide 21: the two-sided z-test of his notes. 25 tests, sigma = 3 MPa
known, so SE = 3/sqrt(25) = 0.6 MPa; the claim H0: mu = 33 MPa. If H0 is
true the sample mean is N(33, 0.6^2); the observed 32 MPa gives
z = (32 - 33)/0.6 = -1.67, and each tail beyond |x - 33| >= 1 holds
Phi(-1/0.6) = 4.8%, so p = 4.8% + 4.8% = 9.6% (two-sided) > 5%."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, draw, fade, num, pop

# The four steps, each with its part of the picture (DECK_BRIEF.md
# "Animated slides"; the steps' moments are in s021.html): the claim draws
# the sampling distribution under H0, the statistic places the observed
# mean, the p-value fills the two tails.
ANIM = {"length": 7.6}

MU0, SE, XBAR = 33.0, 3 / np.sqrt(25), 32.0
H0 = norm(MU0, SE)
Z = (XBAR - MU0) / SE
TAIL = H0.cdf(XBAR)                                   # one tail
assert SE == 0.6 and round(Z, 2) == -1.67
assert round(100 * TAIL, 1) == 4.8 and round(100 * 2 * TAIL, 1) == 9.6
assert round(100 * 2 * norm.cdf(-abs(Z)), 1) == 9.6   # his P(|Z| >= 1.67)


def bottom_axis(f, ax, ticks, label, anim=None):
    """pgfplots' 'axis x line=bottom, hide y axis': the x axis alone, its
    ticks outward, as a density's baseline (no density values to read)."""
    y = ax.y + ax.h
    f.line([(ax.x, y), (ax.x + ax.w, y)], stroke=C.ink, width=2, cap="butt", anim=anim)
    for v in ticks:
        X = float(ax.X(v))
        f.line([(X, y), (X, y + 10)], stroke=C.ink, width=2, cap="butt", anim=anim)
        f.text(X, y + 24, num(v), "north", cls="tk", anim=anim)
    f.text(ax.x + ax.w / 2, y + 24 + 28 + 16, label, "north", cls="axl", anim=anim)


def test():
    f = Fig(832, 600)
    ax = f.axes(16, 20, 800, 452, xlim=(30.4, 35.6), ylim=(0, 0.74), frame=False)
    x = np.linspace(30.55, 35.45, 900)
    lo = np.linspace(30.55, XBAR, 300)
    hi = np.linspace(2 * MU0 - XBAR, 35.45, 300)
    ax.area(lo, H0.pdf(lo), color=C.amber, anim=fade(4.2, .4))
    ax.area(hi, H0.pdf(hi), color=C.amber, anim=fade(4.2, .4))
    ax.plot(x, H0.pdf(x), color=C.navy, width=4.5, anim=draw(1.3, .8))
    ax.vline(XBAR, color=C.blue, width=4, dash=None, y0=0, y1=0.74, anim=draw(2.9, .4))
    bottom_axis(f, ax, [31, 32, 33, 34, 35], "Sample mean of 25 tests (MPa)", anim=fade(1.0, .4))
    # his words, where his picture puts them
    xo, yt = ax.P(XBAR, 0.74)
    f.text(xo - 16, yt + 2, "observed", "north east", color=C.blue, anim=pop(3.2))
    f.text(xo - 16, yt + 40, "<m>x̄ = 32</m>", "north east", color=C.blue, anim=pop(3.3))
    xr = ax.x + ax.w
    f.text(xr, yt + 40, "<m>p = 4.8% + 4.8%</m>", "north east", color=C.accent, anim=pop(4.7))
    f.text(xr, yt + 78, "<m>= 9.6%</m> (two-sided)", "north east", color=C.accent, anim=pop(4.85))
    xc, yc = ax.P(MU0, 0.335)
    f.text(xc, yc, "if <m>H₀</m> is true:", "center", color=C.navy, anim=pop(1.9))
    f.text(xc, yc + 42, "<m>x̄ ~ N(33, 0.6²)</m>", "center", color=C.navy, anim=pop(2.05))
    for xv in (31.3, 34.7):
        ax.text(xv, 0.105, "4.8%", "center", color=C.accent, anim=pop(4.45))
    return f.html()
