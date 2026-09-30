"""Slide 53: his pavement Markov chain, one inspection interval per step.

States Good, Degraded, Failed; each year a section stays or moves one state
worse. His transition matrix (rows: from, columns: to):

    P = [[0.8, 0.2, 0.0],
         [0.0, 0.7, 0.3],
         [0.0, 0.0, 1.0]]

rules  the three states and the rules: a self-loop "stays: p_ii" over each
       state, an arrow for each move one state worse.
tree   every path for two intervals from Good. A path's probability is the
       product of its branch probabilities; paths that end in the same state
       add: Good 0.8 x 0.8 = 0.64, Degraded 0.8 x 0.2 + 0.2 x 0.7 = 0.16 +
       0.14 = 0.30, Failed 0.2 x 0.3 = 0.06, as pi_0 P^2 gives them.

Helpers the next slides borrow (the shared system has no text measure or
tint): tw() measures a label in CMU Serif from the font files themselves,
tint() is TikZ's colour!k (k of the colour over paper), loop() is TikZ's
"loop above" with a Stealth tip."""
import math
import os
from functools import lru_cache

import numpy as np

from fig import Fig, C, stealth

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

P = np.array([[0.8, 0.2, 0.0],
              [0.0, 0.7, 0.3],
              [0.0, 0.0, 1.0]])
PI2 = np.array([1.0, 0.0, 0.0]) @ P @ P
assert np.allclose(P.sum(axis=1), 1)
assert np.allclose(PI2, [0.64, 0.30, 0.06])
assert np.isclose(0.8 * 0.2 + 0.2 * 0.7, 0.30) and np.isclose(0.8 * 0.2, 0.16)


# ------------------------------------------------------------------ helpers
@lru_cache(maxsize=None)
def _metrics(bold):
    from fontTools.ttLib import TTFont
    font = TTFont(os.path.join(ROOT, "content", "fonts-cmu",
                               f"cmu-serif-{700 if bold else 500}-roman.woff2"))
    return font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm


def tw(s, size=28, bold=False):
    """The width in px of a plain label set in CMU Serif (the figures' face)."""
    cmap, hmtx, upm = _metrics(bold)
    return sum(hmtx[cmap.get(ord(ch), cmap[ord("x")])][0] for ch in s) * size / upm


def tint(color, k):
    """TikZ's color!k: k of the colour mixed into paper."""
    c = color.lstrip("#")
    rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(255 + (v - 255) * k):02X}" for v in rgb)


def bezier(p0, p1, p2, p3, n=80):
    t = np.linspace(0, 1, n)[:, None]
    a, b, c, d = (np.array(p, float) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d


def curve_arrow(f, pts, color=C.ink, width=3.0):
    """A curve through pts (figure px) with a Stealth tip at its last point."""
    pts = np.asarray(pts, float)
    end = pts[-1]
    ang = math.atan2(end[1] - pts[-4][1], end[0] - pts[-4][0])
    d, back = stealth(end[0], end[1], ang, width)
    keep = pts[np.hypot(*(pts - end).T) >= back]
    stop = end - back * np.array([math.cos(ang), math.sin(ang)])
    f.line([tuple(p) for p in keep] + [tuple(stop)], stroke=color, width=width, cap="butt")
    f.path(d, stroke="none", fill=color)


def loop(f, cx, cy, r, color=C.ink, width=3.0, a0=116, a1=64, reach=104, gap=5):
    """TikZ's loop above: out of the circle (cx, cy, r) at angle a0, back in
    at a1 (degrees, anticlockwise from east), the tip `gap` px off the rim.
    Returns the loop's top in figure px."""
    def at(a, rr):
        return cx + rr * math.cos(math.radians(a)), cy - rr * math.sin(math.radians(a))
    p0, p3 = at(a0, r + 1), at(a1, r + gap)
    o, i = math.radians(a0 - 10), math.radians(a1 + 10)
    p1 = (p0[0] + reach * math.cos(o), p0[1] - reach * math.sin(o))
    p2 = (p3[0] + reach * math.cos(i), p3[1] - reach * math.sin(i))
    pts = bezier(p0, p1, p2, p3, 120)
    curve_arrow(f, pts, color, width)
    return float(pts[:, 1].min())


def box(f, x, y, w, h, label, color, size=28, bold=False, k=0.07):
    """His state token: a box in the state's colour (TikZ draw=c, fill=c!7)
    with its name in the colour, centred at (x, y)."""
    f.rect(x - w / 2, y - h / 2, w, h, fill=tint(color, k), stroke=color, width=2)
    f.text(x, y, label, "center", size=size, color=color, weight=700 if bold else None)


# ------------------------------------------------------------------ figures
GOOD, DEGR, FAIL = C.navy, C.accent, C.deep


def rules():
    f = Fig(688, 281)
    r, cy = 74, 201
    xs = (78, 344, 610)
    names = ("Good", "Degraded", "Failed")
    for x, name, col, stay in zip(xs, names, (GOOD, DEGR, FAIL), np.diag(P)):
        f.circle(x, cy, r, fill=tint(col, 0.08), stroke=col, width=2.5)
        f.text(x, cy, name, "center", size=30, color=col)
        top = loop(f, x, cy, r)
        f.text(x, top - 12, f"stays: {stay:.1f}", "south", size=28)
    for (a, b), p in zip(((0, 1), (1, 2)), (P[0, 1], P[1, 2])):
        x0, x1 = xs[a] + r + 8, xs[b] - r - 8
        f.arrow((x0, cy), (x1, cy), color=C.ink, width=3)
        f.text((x0 + x1) / 2, cy - 14, f"{p:.1f}", "south", size=30, weight=700)
    return f.html()


def tree():
    f = Fig(976, 452)
    bw, bh = 108, 50
    X = (54, 298, 542)                         # Year 0, 1, 2: box centres
    L = (36, 146, 256, 366)                    # the four leaves
    M = ((L[0] + L[1]) / 2, (L[2] + L[3]) / 2)
    R = (M[0] + M[1]) / 2

    def branch(x0, y0, x1, y1, p, above):
        a = (x0 + bw / 2 + 10, y0)
        b = (x1 - bw / 2 - 10, y1)
        f.line([a, b], stroke=C.body, width=2.5)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        f.text(mx - 4, my + (-8 if above else 8), p, "south east" if above else "north east", size=28)

    branch(X[0], R, X[1], M[0], "0.8", True)
    branch(X[0], R, X[1], M[1], "0.2", False)
    branch(X[1], M[0], X[2], L[0], "0.8", True)
    branch(X[1], M[0], X[2], L[1], "0.2", False)
    branch(X[1], M[1], X[2], L[2], "0.7", True)
    branch(X[1], M[1], X[2], L[3], "0.3", False)
    box(f, X[0], R, bw, bh, "Good", GOOD)
    box(f, X[1], M[0], bw, bh, "Good", GOOD)
    box(f, X[1], M[1], bw, bh, "Degr.", DEGR)
    for y, name, col in zip(L, ("Good", "Degr.", "Degr.", "Failed"), (GOOD, DEGR, DEGR, FAIL)):
        box(f, X[2], y, bw, bh, name, col)
    # each path's product, as he wrote it
    px = X[2] + bw / 2 + 34
    paths = (("0.8 × 0.8 = 0.64", GOOD, True), ("0.8 × 0.2 = 0.16", DEGR, False),
             ("0.2 × 0.7 = 0.14", DEGR, False), ("0.2 × 0.3 = 0.06", FAIL, True))
    wmax = 0
    for y, (s, col, bold) in zip(L, paths):
        f.text(px, y, s, "west", size=28, color=col, weight=700 if bold else None)
        wmax = max(wmax, tw(s, 28, bold))
    # the two Degraded paths add
    bx = px + wmax + 26
    f.line([(bx - 14, L[1]), (bx, L[1]), (bx, L[2]), (bx - 14, L[2])], stroke=DEGR, width=2.5,
           cap="butt", join="miter")
    f.text(bx + 14, (L[1] + L[2]) / 2, "0.30", "west", size=28, color=DEGR, weight=700)
    assert bx + 14 + tw("0.30", 28, True) < f.w
    for x, s in zip(X, ("Year 0", "Year 1", "Year 2")):
        f.text(x, 436, s, "center", size=26, color=C.muted)
    return f.html()
