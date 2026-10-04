"""Slide 36: capacity, demand and the margin G = R - S (his first case).

Model: R ~ N(100, 10^2) kN and S ~ N(70, 8^2) kN, independent. G = R - S is
linear, so its moments are exact: E[G] = 100 - 70 = 30 kN and Var(G) = 10^2 +
8^2 - 2 Cov(R, S) = 164 kN^2; R and S jointly normal make G normal, and the
failure area is P(G < 0) = Phi(-30/sqrt(164)) = 0.9575%, his 0.96%. His example
realization: R = 95, S = 80 gives G = 15 kN.

marginals  the two densities on his force axis, 35 to 140 kN; his legend sits
           over the plot in one row (inside, it would cover a curve).
margin     the density of G on -20 to 80 kN, the failure tail G < 0 in the
           accent and the limit G = 0."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop
from s031 import legend, tw

# Demand, capacity, then their margin (DECK_BRIEF.md "Animated slides"; the
# blocks' moments are in s036.html): S and R draw with their legend
# entries; then the density of G, its limit G = 0 and the failure tail
# beyond it; then the derivation of its mean and variance.
ANIM = {"length": 7.6}

R, S = stats.norm(100, 10), stats.norm(70, 8)
MU, VAR = R.mean() - S.mean(), R.var() + S.var() - 2 * 0.0
G = stats.norm(MU, np.sqrt(VAR))
PF = G.cdf(0)
assert (MU, VAR) == (30, 164) and 95 - 80 == 15
assert f"{100 * PF:.2f}" == "0.96" and f"{100 * PF:.3f}" == "0.957"

H = 362
TOP, PH = 46, 214                     # the plot boxes, under a line of words


def marginals():
    f = Fig(832, H)
    ax = f.axes(118, TOP, 700, PH, xlim=(32, 143), ylim=(-0.002, 0.054),
                xticks=range(40, 141, 20), yticks=[0, 0.02, 0.04], ytick_nd=2,
                xlabel="Force (kN)", ylabel="Density", grid=True, anim=fade(1.0, .4))
    x = np.linspace(35, 140, 700)
    ax.plot(x, S.pdf(x), color=C.accent, width=4, anim=draw(1.4, .7))
    ax.plot(x, R.pdf(x), color=C.navy, width=4, anim=draw(2.0, .7))
    # his legend, one row over the plot, centred on it
    entries = [("<m>R</m>: capacity, mean 100, SD 10", C.navy),
               ("<m>S</m>: demand, mean 70, SD 8", C.accent)]
    size, sample, gap = 24, 44, 40
    widths = [sample + 12 + tw(t, size) for t, _ in entries]
    total = sum(widths) + gap
    x0 = min(ax.x + ax.w / 2 - total / 2, f.w - 4 - total)
    cy = 16
    for ((t, col), w), at in zip(zip(entries, widths), (2.0, 1.4)):    # each with its curve
        f.line([(x0, cy), (x0 + sample, cy)], stroke=col, width=4, cap="butt", anim=pop(at))
        f.text(x0 + sample + 12, cy, t, "west", size=size, anim=pop(at))
        x0 += w + gap
    assert x0 - gap <= f.w - 4
    return f.html()


def margin():
    f = Fig(832, H)
    box, lim = (118, TOP, 700, PH), dict(xlim=(-24, 84), ylim=(-0.0013, 0.034))
    ax0 = f.axes(*box, frame=False, **lim)
    xs = np.linspace(-20, 0, 200)
    ax0.area(xs, G.pdf(xs), color=C.amber, anim=fade(4.3, .4))
    ax = f.axes(*box, xticks=range(-20, 81, 20), yticks=[0, 0.01, 0.02, 0.03], ytick_nd=2,
                xlabel="Margin <m>G = R − S</m> (kN)", ylabel="Density", grid=True,
                anim=fade(3.0, .4), **lim)
    x = np.linspace(-20, 80, 700)
    ax.plot(x, G.pdf(x), color=C.blue, width=4, anim=draw(3.4, .8))
    ax.vline(0, color=C.accent, width=3, dash=None, anim=draw(4.2, .4))
    f.text(ax.x + ax.w / 2, 16, "Independent case: failure area <m>≈</m> 0.96%", "center", size=26,
           anim=pop(4.6))
    return f.html()
