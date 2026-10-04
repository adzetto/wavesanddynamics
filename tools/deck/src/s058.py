"""Slide 58: the Gaussian process of slide 57 conditioned on three CPT tests
(his notes: kriging; illustrative).

Prior: mean 6 MPa, sigma = 1 MPa, squared-exponential kernel with l = 1.5 m.
Tests (his picture): qc = 7.4, 5.1 and 6.8 MPa at 1.0, 3.2 and 8.5 m, each
with measurement SD 0.2 MPa. The posterior at x is normal with
    mean  m + k_x^T (K + 0.2^2 I)^-1 (y - m)
    var   sigma^2 - k_x^T (K + 0.2^2 I)^-1 k_x.
His two points, asserted: A at 3.7 m, 0.5 m from a test: 4.98 +- 0.71 (2 SD),
his 5.0 +- 0.7; B at 6.0 m, far from all tests: 5.94 +- 1.91, his 5.9 +- 1.9,
almost the prior 6 +- 2.

field  the posterior mean, its +-2 SD band and three curves drawn from the
       posterior (z from numpy's PCG64 generator, fixed seed).
point  the predictive densities at A and B against the prior's N(6, 1).
Both legends are drawn by legend_rows(), a helper the shared fig.py does not
have: entries in rows, so that the legends clear the band and the curves."""
import re

import numpy as np
from scipy import stats

from fig import Fig, C, SERIES, draw, fade, pop
from s053 import tw, tint

# The data, then what they do to the field (DECK_BRIEF.md "Animated slides";
# the blocks' moments are in s058.html): the three measurements, the band
# pinched at them, the best estimate and three possible profiles, the two
# places A and B; then the prior and the two predictions there.
ANIM = {"length": 8.5}
from s057 import MEAN, SD, kernel

ELL, NOISE = 1.5, 0.2
XT = np.array([1.0, 3.2, 8.5])
YT = np.array([7.4, 5.1, 6.8])
XA, XB = 3.7, 6.0
X = np.linspace(0, 10, 401)
SEED = 58


def posterior(xs):
    K = kernel(XT, XT, ELL) + NOISE ** 2 * np.eye(len(XT))
    ks = kernel(xs, XT, ELL)
    mu = MEAN + ks @ np.linalg.solve(K, YT - MEAN)
    cov = kernel(xs, xs, ELL) - ks @ np.linalg.solve(K, ks.T)
    return mu, cov


MU, COV = posterior(X)
SDX = np.sqrt(np.clip(np.diag(COV), 0, None))
(MA, MB), cab = posterior(np.array([XA, XB]))
SA, SB = np.sqrt(np.diag(cab))
assert (round(MA, 1), round(2 * SA, 1)) == (5.0, 0.7)
assert (round(MB, 1), round(2 * SB, 1)) == (5.9, 1.9)
assert (MEAN, 2 * SD) == (6, 2)
_w, _v = np.linalg.eigh(COV)
DRAWS = MU[:, None] + (_v * np.sqrt(np.clip(_w, 0, None))) @ \
    np.random.default_rng(SEED).standard_normal((len(X), 3))

SKY_INK = "#" + "".join(f"{round(0.7 * int(C.sky[i:i + 2], 16) + 0.3 * int(C.navy[i:i + 2], 16)):02X}"
                        for i in (1, 3, 5))          # deck.css --sky-ink: sky 70%, navy 30%


def legend_rows(ax, rows, at="north east", size=26, pad=12, sample=44, gap=28, row=36, inset=14,
                anim=None):
    """pgfplots' legend, its entries in rows: a 1 px ink box, white, inside
    the axis. rows: lists of (label, style); style as fig.Axes.legend's
    (color, width, dash; kind='area', 'mark' or 'linemark'). Returns the box.
    anim= as fig.Axes.legend's: the whole legend, or a list, its box then
    each entry, row after row."""
    n = sum(len(r) for r in rows)
    box, each = (anim[0], list(anim[1:])) if isinstance(anim, (list, tuple)) else (anim, [anim] * n)
    each = iter(each)
    f = ax.f
    width = lambda t: tw(re.sub(r"<[^>]+>", "", t), size)
    wrow = [sum(sample + 10 + width(t) for t, _ in r) + gap * (len(r) - 1) for r in rows]
    bw, bh = 2 * pad + max(wrow), 2 * pad + size + 4 + row * (len(rows) - 1)
    bx = ax.x + ax.w - inset - bw if "east" in at else ax.x + inset
    by = ax.y + inset if "north" in at else ax.y + ax.h - inset - bh
    f.rect(bx, by, bw, bh, fill=C.paper, stroke=C.ink, width=1.0, anim=box)
    for i, r in enumerate(rows):
        x, cy = bx + pad, by + pad + (size + 4) / 2 + i * row
        for t, st in r:
            a = next(each)
            kind = st.get("kind", "line")
            if kind == "area":
                f.rect(x, cy - 10, sample, 20, fill=st["color"], fill_opacity=st.get("opacity"), anim=a)
            elif kind == "mark":
                f.circle(x + sample / 2, cy, st.get("r", 8), fill=st["color"], anim=a)
            elif kind == "linemark":             # pgfplots' line with its marks
                f.line([(x, cy), (x + sample, cy)], stroke=st["color"], width=st.get("width", 3),
                       cap="butt", anim=a)
                f.circle(x + sample / 2, cy, st.get("r", 7), fill=st["color"], anim=a)
            else:
                f.line([(x, cy), (x + sample, cy)], stroke=st["color"], width=st.get("width", 3),
                       dash=st.get("dash"), cap="butt", anim=a)
            f.text(x + sample + 10, cy, t, "west", size=size, anim=a)
            x += sample + 10 + width(t) + gap
    return bx, by, bw, bh


def _top(lo, peak, h, clear):
    """The axis top that leaves `clear` px over `peak` for the legend."""
    return np.ceil(10 * (peak * h - lo * clear) / (h - clear)) / 10


BAND = tint(C.blue, 0.14)
LEFT_ROWS = [[("±2 SD (95%)", {"kind": "area", "color": BAND}),
              ("CPT measurements", {"kind": "mark", "color": C.ink})],
             [("best estimate (posterior mean)", {"color": C.blue, "width": 4.5})]]


def field():
    f = Fig(976, 438)
    x, y, w, h = 96, 8, 872, 338
    # the legend (two rows, top right) must clear the band where it stands
    lw = 2 * 12 + max(44 + 10 + tw("±2 SD (95%)", 26) + 28 + 44 + 10 + tw("CPT measurements", 26),
                      44 + 10 + tw("best estimate (posterior mean)", 26))
    xl = -0.5 + (w - 14 - lw) / w * 11                       # its left edge, in metres
    under = X >= xl - 0.1
    peak = max((MU + 2 * SDX)[under].max(), DRAWS[under].max())
    top = _top(2.5, peak, h, 14 + 2 * 12 + 30 + 36 + 10)
    ax = f.axes(x, y, w, h, xlim=(-0.5, 10.5), ylim=(2.5, top), xticks=range(0, 11, 2),
                yticks=range(3, int(top) + 1), xlabel="Distance along the site (m)",
                ylabel="Cone resistance qc (MPa)", anim=fade(.5, .4))
    ax.area(X, MU + 2 * SDX, MU - 2 * SDX, color=BAND, anim=fade(1.4, .5))
    for xv, col, t in ((XA, C.accent, 3.9), (XB, C.sky, 4.1)):
        ax.vline(xv, color=col, width=2.5, dash="3 5", anim=draw(t, .35))
    for k, col in enumerate((C.accent, C.navy, C.sky)):
        ax.plot(X, DRAWS[:, k], color=col, width=2.2, anim=draw(2.4 + .2 * k, .7))
    ax.plot(X, MU, color=C.blue, width=4.5, anim=draw(1.6, .9))
    for j, (xv, yv) in enumerate(zip(XT, YT)):
        ax.mark(xv, yv, r=9, color=C.ink, anim=pop(.8 + .15 * j))
    ax.text(XA + 0.1, 2.95, "A", "west", size=30, color=C.accent, weight=700, anim=pop(4.0))
    ax.text(XB + 0.1, 2.95, "B", "west", size=30, color=SKY_INK, weight=700, anim=pop(4.2))
    bx, by, bw, bh = legend_rows(ax, LEFT_ROWS, anim=[pop(.8), pop(1.4), pop(.8), pop(1.6)])
    inside = (ax.X(X) > bx - 6) & (ax.X(X) < bx + bw + 6)
    assert (ax.Y((MU + 2 * SDX)[inside]) > by + bh + 6).all()
    assert (ax.Y(DRAWS[inside]) > by + bh + 6).all()
    return f.html()


def point():
    f = Fig(688, 438)
    x, y, w, h = 104, 8, 576, 338
    rows = [[("before data (any location)", {"color": C.navy, "dash": "10 6", "width": 3})],
            [(f"A: 3.7 m (near a test): {MA:.1f} ± {2 * SA:.1f}", {"color": C.accent, "width": 4})],
            [(f"B: 6.0 m (far from tests): {MB:.1f} ± {2 * SB:.1f}", {"color": C.sky, "width": 4})]]
    a, b, prior = stats.norm(MA, SA), stats.norm(MB, SB), stats.norm(MEAN, SD)
    top = _top(0, a.pdf(MA), h, 14 + 2 * 12 + 30 + 2 * 36 + 10)
    ax = f.axes(x, y, w, h, xlim=(2.5, 9.5), ylim=(0, top), xticks=range(3, 10),
                yticks=np.arange(0, top, 0.5), xlabel="Predicted qc (MPa)",
                ylabel="Probability density", anim=fade(4.8, .4))
    q = np.linspace(2.5, 9.5, 700)
    ax.area(q, b.pdf(q), color=C.sky, opacity=0.35, anim=fade(6.4, .4))
    ax.area(q, a.pdf(q), color=C.amber, opacity=0.45, anim=fade(5.8, .4))
    ax.plot(q, prior.pdf(q), color=C.navy, width=3, dash="10 6", anim=draw(5.1, .6))
    ax.plot(q, b.pdf(q), color=C.sky, width=4, anim=draw(6.4, .6))
    ax.plot(q, a.pdf(q), color=C.accent, width=4, anim=draw(5.8, .6))
    bx, by, bw, bh = legend_rows(ax, rows, anim=[pop(5.1), pop(5.1), pop(5.8), pop(6.4)])
    assert ax.Y(a.pdf(MA)) > by + bh + 6 and bx > ax.x
    return f.html()
