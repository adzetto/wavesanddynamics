"""Slide 65: a Kalman filter tracks a bridge displacement, one reading an hour.

The model of his notes: the true displacement starts at 5 mm and drifts by
0.25 mm an hour plus a random change of SD 0.6 mm,
    x[k] = x[k-1] + 0.25 + w[k],   w ~ N(0, 0.6^2),
and the sensor reads it with noise of SD 3 mm (H = 1),
    z[k] = x[k] + v[k],            v ~ N(0, 3^2),   k = 0 .. 39 (40 hours).
The filter starts from the first reading (x^[0] = z[0], P[0] = 9) and then,
every hour, predicts (x^- = x^ + 0.25, P- = P + 0.36) and updates with the
gain K = P- / (P- + 9). The band is the estimate +/- 2 SD (2 sqrt(P)).

The draw is numpy's PCG64 generator, seed 7815: the first seed whose
typical errors (root mean square over the 40 hours) come within 0.025 mm of
his "sensor alone 3.1 mm, Kalman estimate 1.6 mm" and whose truth stays
inside the +/- 2 SD band at every hour, as in his figure (first_seed()
repeats the search). A time series needs a random order in time, which
fig.sample's Halton points (low-discrepancy, in sequence) do not give; the
seed makes it the same draw every run.

The helpers below (textw, legend, clear, dense) are shared by slides 67 to 69."""
import html as _html
import os
import re

import numpy as np

from fig import Fig, C, draw, fade, pop, seq, wipe

# The three steps, then forty hours of them (DECK_BRIEF.md "Animated
# slides"; the blocks' moments are in s065.html): the unknown truth, then
# each hour's reading with the estimate stepping after it inside its band.
# Each legend entry arrives with what it names.
ANIM = {"length": 7.4}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

# ------------------------------------------------------------------ helpers
_ADV = None


def textw(s, px):
    """The width in px of a figure label (CMU Serif 500, as .ft sets it),
    from the font's own advance widths; tags are dropped."""
    global _ADV
    if _ADV is None:
        from fontTools.ttLib import TTFont
        font = TTFont(os.path.join(ROOT, "content", "fonts-cmu", "cmu-serif-500-roman.woff2"))
        cmap, hmtx = font.getBestCmap(), font["hmtx"]
        upm = font["head"].unitsPerEm
        _ADV = {cp: hmtx[g][0] / upm for cp, g in cmap.items()}
    plain = _html.unescape(re.sub(r"<[^>]+>", "", s))
    return sum(_ADV.get(ord(c), 0.5) for c in plain) * px


def legend(f, x, y, entries, size=24, row=36, pad=14, sample=46, gap=12, cols=1, colgap=34,
           anim=None):
    """pgfplots' legend with its top-left corner at figure px (x, y): a white
    box with a 1 px ink rule, a sample and his words on each row, filled
    column by column (cols > 1 as matplotlib's ncol). A style is a dict: kind
    "line" (color, width, dash), "dot" (color, r, opacity), "band" (fill,
    color: a line over a band) or "area" (fill, stroke). Returns the box.
    anim= as fig.Axes.legend's: the whole legend, or a list, its box then
    each entry."""
    box, each = (anim[0], list(anim[1:])) if isinstance(anim, (list, tuple)) else (anim, [anim] * len(entries))
    rows = -(-len(entries) // cols)
    colw = [max(textw(t, size) for t, _ in entries[c * rows:(c + 1) * rows])
            for c in range(cols)]
    w = 2 * pad + sum(sample + gap + cw for cw in colw) + colgap * (cols - 1)
    h = 2 * pad + size + row * (rows - 1)
    f.rect(x, y, w, h, fill=C.paper, stroke=C.ink, width=1.0, anim=box)
    for i, ((t, st), a) in enumerate(zip(entries, each)):
        c, r = divmod(i, rows)
        cx = x + pad + sum(sample + gap + cw + colgap for cw in colw[:c])
        cy = y + pad + size / 2 + r * row
        x0, x1 = cx, cx + sample
        kind = st.get("kind", "line")
        if kind == "dot":
            f.circle((x0 + x1) / 2, cy, st.get("r", 6), fill=st["color"], opacity=st.get("opacity"), anim=a)
        elif kind in ("band", "area"):
            f.rect(x0, cy - 11, sample, 22, fill=st["fill"], stroke=st.get("stroke"),
                   width=st.get("stroke_width", 1.5), anim=a)
            if kind == "band":
                f.line([(x0, cy), (x1, cy)], stroke=st["color"], width=st.get("width", 4), cap="butt",
                       anim=a)
        else:
            f.line([(x0, cy), (x1, cy)], stroke=st["color"], width=st.get("width", 3.5),
                   dash=st.get("dash"), cap="butt", anim=a)
        f.text(x1 + gap, cy, t, "west", size=size, anim=a)
    return x, y, w, h


def clear(box, pts, margin=8):
    """True when none of the figure-px points lies in the box (x, y, w, h)
    grown by `margin`: a label is clear of the data it sits over."""
    x, y, w, h = box
    p = np.asarray(pts, float)
    inside = ((p[:, 0] > x - margin) & (p[:, 0] < x + w + margin) &
              (p[:, 1] > y - margin) & (p[:, 1] < y + h + margin))
    return not inside.any()


def dense(ax, xs, ys, n=12):
    """A polyline of data points as figure px, each segment cut in n, so
    clear() sees the line between the points too."""
    X, Y = np.asarray(ax.X(xs), float), np.asarray(ax.Y(ys), float)
    t = np.linspace(0, 1, n, endpoint=False)
    px = np.concatenate([X[:-1, None] + (X[1:, None] - X[:-1, None]) * t, X[-1:, None]], axis=None)
    py = np.concatenate([Y[:-1, None] + (Y[1:, None] - Y[:-1, None]) * t, Y[-1:, None]], axis=None)
    return np.column_stack([px, py])


# ------------------------------------------------------------------ the model
N, X0, DRIFT, SD_W, SD_V = 40, 5.0, 0.25, 0.6, 3.0
SEED = 7815


def simulate(seed=SEED):
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, SD_W, N - 1)
    v = rng.normal(0.0, SD_V, N)
    x = X0 + np.concatenate([[0.0], np.cumsum(DRIFT + w)])
    z = x + v
    xh, P = np.empty(N), np.empty(N)
    xh[0], P[0] = z[0], SD_V ** 2
    for k in range(1, N):
        xp, Pp = xh[k - 1] + DRIFT, P[k - 1] + SD_W ** 2          # predict
        K = Pp / (Pp + SD_V ** 2)                                  # gain
        xh[k], P[k] = xp + K * (z[k] - xp), (1 - K) * Pp           # update
    return x, z, xh, P


T = np.arange(N)
TRUE, Z, XH, P = simulate()
RMS_Z = float(np.sqrt(np.mean((Z - TRUE) ** 2)))
RMS_K = float(np.sqrt(np.mean((XH - TRUE) ** 2)))
# his numbers: "Typical error: sensor alone 3.1 mm, Kalman estimate 1.6 mm."
assert round(RMS_Z, 1) == 3.1 and round(RMS_K, 1) == 1.6
assert abs(RMS_Z - 3.1) < 0.025 and abs(RMS_K - 1.6) < 0.025
# "uncertainty shrinks": the band narrows after the first few steps
assert P[0] == 9 and np.all(np.diff(P[:6]) < 0)
# the truth inside the band at every hour
assert np.all(np.abs(TRUE - XH) <= 2 * np.sqrt(P))


def first_seed():
    """The search that chose SEED (slow; not run on import)."""
    for s in range(100000):
        x, z, xh, p = simulate(s)
        if (abs(np.sqrt(np.mean((z - x) ** 2)) - 3.1) < 0.025 and
                abs(np.sqrt(np.mean((xh - x) ** 2)) - 1.6) < 0.025 and
                np.all(np.abs(x - xh) <= 2 * np.sqrt(p))):
            return s


def track():
    f = Fig(976, 596)
    ax = f.axes(120, 14, 836, 480, xlim=(-1.5, 40.5), ylim=(-1, 25),
                xticks=range(0, 41, 5), yticks=range(0, 21, 5),
                xlabel="Time step (e.g. hour)", ylabel="Displacement (mm)", anim=fade(2.2, .4))
    band_lo, band_hi = XH - 2 * np.sqrt(P), XH + 2 * np.sqrt(P)
    ax.area(T, band_hi, band_lo, color=C.steel2, anim=wipe(3.45, 1.95, ease="linear"))
    ax.plot(T, TRUE, color=C.ink, width=2.6, dash="11 7", anim=draw(2.6, .8))
    ax.plot(T, XH, color=C.blue, width=4.5, anim=seq(3.45, .05))   # each hour after its reading
    for t, z in zip(T, Z):
        X, Y = ax.P(t, z)
        f.circle(X, Y, 8.2, fill=C.paper, anim=pop(3.4 + .05 * t, .25))
        f.circle(X, Y, 6.5, fill=C.amber, anim=pop(3.4 + .05 * t, .25))
    box = legend(f, ax.x + 18, ax.y + 18, [
        ("sensor readings (noise SD 3 mm)", {"kind": "dot", "color": C.amber, "r": 6.5}),
        ("true displacement (unknown)", {"color": C.ink, "width": 2.6, "dash": "11 7"}),
        ("Kalman estimate ±2 SD", {"kind": "band", "fill": C.steel2, "color": C.blue, "width": 4.5}),
    ], anim=[pop(2.6), pop(3.4), pop(2.6), pop(3.45)])
    data = np.vstack([dense(ax, T, band_hi), dense(ax, T, TRUE), np.column_stack([ax.X(T), ax.Y(Z)])])
    assert clear(box, data, margin=10), "the legend sits on the data"
    return f.html()
