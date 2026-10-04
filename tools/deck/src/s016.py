"""Slide 16: one test against the average of 25, on one strength axis.

A single cylinder's strength is X ~ N(32, 3^2) MPa (sigma = 3 MPa, the
material). The average of n = 25 independent tests is Xbar ~ N(32, 0.6^2):
Var(Xbar) = (1/n^2) x n sigma^2 = sigma^2/n, so SE = 3/sqrt(25) = 0.6 MPa.
Both panels share the axes (20 to 44 MPa, density 0 to 0.7), so the
narrowing is seen at its true size. The dots are deterministic draws
(fig.sample): 11 single tests from N(32, 3^2) (skip 7) and 9 sample means
from N(32, 0.6^2) (skip 20). The arrows span one SD, 29 to 35 MPa, and one
SE, 31.4 to 32.6 MPa; the faint curve in the second panel is the first
panel's, single cylinders again.

star() is his five-pointed star beside the take-away, a regular star
(outer to inner radius 2.618, a pentagram's), navy."""
import math

import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop, sample, seq

# One cylinder, then the average of 25 (DECK_BRIEF.md "Animated slides"; the
# blocks' moments are in s016.html): each panel's curve draws, its draws are
# counted out along the axis and its spread is dimensioned; the second
# panel keeps the first's curve faint behind it. The star comes with the
# take-away.
ANIM = {"length": 9.8}

MU, SIGMA, N = 32.0, 3.0, 25
SE = SIGMA / math.sqrt(N)
assert SE == 0.6 and math.isclose(SIGMA ** 2 / N, SE ** 2)
ONE, AVG = stats.norm(MU, SIGMA), stats.norm(MU, SE)
TESTS = sample(11, ONE, skip=7)
MEANS = sample(9, AVG, skip=20)

W, H = 1696, 372
BOXES = ((112, 52, 740, 232), (944, 52, 740, 232))
TITLE = {"size": 30, "weight": 700}
X = np.linspace(20, 44, 1200)


def _axes(f, box, first, anim=None):
    return f.axes(*box, xlim=(20, 44), ylim=(0, 0.7), xticks=[20, 25, 30, 35, 40],
                  yticks=[0, 0.2, 0.4, 0.6], ytick_nd=1,
                  yticklabels=None if first else ["", "", "", ""],
                  xlabel="Strength (MPa)", ylabel="Density" if first else None, anim=anim)


def _span(f, ax, a, b, y, color=C.accent, width=2.5, anim=None):
    """A dimension from a to b at height y (data): a two-headed arrow, or,
    where the span is too short for two heads, a line between two arrows
    that point in from outside (the drawing office's small dimension)."""
    (xa, Y), (xb, _) = ax.P(a, y), ax.P(b, y)
    head = 6 * width + 4
    if xb - xa > 3 * head:
        m = (xa + xb) / 2
        f.arrow((m, Y), (xa, Y), color=color, width=width, anim=anim)
        f.arrow((m, Y), (xb, Y), color=color, width=width, anim=anim)
        return xb
    f.line([(xa, Y), (xb, Y)], stroke=color, width=width, cap="butt", anim=anim)
    f.arrow((xa - 1.6 * head, Y), (xa, Y), color=color, width=width, anim=anim)
    f.arrow((xb + 1.6 * head, Y), (xb, Y), color=color, width=width, anim=anim)
    return xb + 1.6 * head


def spread():
    f = Fig(W, H)
    # one cylinder
    a = _axes(f, BOXES[0], True, anim=fade(.8, .4))
    a.area(X, ONE.pdf(X), color=C.mist, anim=fade(1.4, .5))
    a.plot(X, ONE.pdf(X), color=C.navy, width=3, anim=draw(1.2, .7))
    a.scatter(TESTS, np.full(TESTS.shape, 0.032), r=7, color=C.paper, stroke=C.navy,
              anim=seq(2.0, .1))
    _span(f, a, MU - SIGMA, MU + SIGMA, 0.2, anim=draw(3.3, .35))
    xm, ym = a.P(MU, 0.2)
    f.text(xm, ym - 14, "<m>σ</m> = 3 MPa (± 1 SD)", "south", color=C.accent, anim=pop(3.5))
    x0, y0, w0, _ = BOXES[0]
    f.text(x0 + w0 / 2, y0 - 14, "One cylinder: where a single test lands", "south",
           color=C.navy, **TITLE, anim=pop(.9))
    # the average of 25
    b = _axes(f, BOXES[1], False, anim=fade(5.3, .4))
    b.area(X, ONE.pdf(X), color=C.steel, anim=fade(5.6, .4))
    b.area(X, AVG.pdf(X), color=C.blue, opacity=0.3, anim=fade(6.3, .5))
    b.plot(X, AVG.pdf(X), color=C.blue, width=3, anim=draw(6.1, .7))
    b.scatter(MEANS, np.full(MEANS.shape, 0.032), r=7, color=C.paper, stroke=C.blue,
              anim=seq(6.9, .1))
    xe = _span(f, b, MU - SE, MU + SE, 0.36, anim=draw(8.0, .3))
    _, ye = b.P(MU, 0.36)
    f.text(xe + 12, ye, "SE = 0.6 MPa", "west", color=C.accent, anim=pop(8.1))
    xf, yf = b.P(37.6, 0.075)
    f.text(xf, yf, "faint: single <br>cylinders", "south west", size=26, color=C.muted,
           anim=pop(5.7))
    x1, y1, w1, _ = BOXES[1]
    f.text(x1 + w1 / 2, y1 - 14, "Average of 25: where a sample mean lands", "south",
           color=C.blue, **TITLE, anim=pop(5.4))
    return f.html()


def star():
    f = Fig(40, 38)
    R, r = 19.0, 19.0 / 2.618
    cx, cy = 20.0, 20.5
    pts = [(cx + (R if k % 2 == 0 else r) * math.sin(k * math.pi / 5),
            cy - (R if k % 2 == 0 else r) * math.cos(k * math.pi / 5)) for k in range(10)]
    f.poly(pts, fill=C.navy, anim=pop(9.1))
    return f.html()
