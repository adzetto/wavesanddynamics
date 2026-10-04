"""Slide 67: two estimates combined by the same rule (his notes).

Case A, the Bayesian mean strength (slides 18 and 19): the old estimate is
the prior belief N(30, 2^2) MPa, the new data the mean of 25 tests, 32 MPa
with standard error 0.6 (variance 0.36).
Case B, the Kalman update (his heading, "slides 65–66": his 65 and 66, with
our loop, 65a, between them): the old estimate is the model prediction
N(10, 2^2) mm, the new data a sensor reading 14 mm with SD 3 (variance 9).
Both: new = old + w (data - old), w = var(old) / (var(old) + var(data)),
and the combined variance (1 - w) var(old). For normal distributions this is
exactly Bayes' rule, so each combined curve is N(new, (1 - w) var(old)):
A  w = 4 / 4.36 = 0.917, new 31.83 MPa, SD 0.575
B  w = 4 / 13   = 0.308, new 11.23 mm,  SD 1.664
Each panel is scaled to its own highest density, as his are; the densities
have no axis of their own there, only the quantity (MPa, mm)."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, draw, fade, num, pop
from s065 import clear, textw

# Case A, then case B, then the rule they share (DECK_BRIEF.md "Animated
# slides"; the blocks' moments are in s067.html): in each, the old estimate,
# the new data, then their combination, each with its words.
ANIM = {"length": 8.1}


def combine(old, var_old, data, var_data):
    w = var_old / (var_old + var_data)
    return w, old + w * (data - old), (1 - w) * var_old


W_A, NEW_A, VAR_A = combine(30.0, 4.0, 32.0, 0.36)
W_B, NEW_B, VAR_B = combine(10.0, 4.0, 14.0, 9.0)
assert (round(W_A, 2), round(NEW_A, 2)) == (0.92, 31.83)
assert (round(W_B, 2), round(NEW_B, 2)) == (0.31, 11.23)
assert round(3 / np.sqrt(25), 1) == 0.6 and round(0.6 ** 2, 2) == 0.36
# the rule is Bayes' rule: the normalised product of the two densities
for old, vo, data, vd, new, vn in ((30, 4, 32, 0.36, NEW_A, VAR_A), (10, 4, 14, 9, NEW_B, VAR_B)):
    _x = np.linspace(old - 30, old + 30, 60001)
    _p = norm.pdf(_x, old, np.sqrt(vo)) * norm.pdf(data, _x, np.sqrt(vd))
    assert np.allclose(_p / np.trapezoid(_p, _x), norm.pdf(_x, new, np.sqrt(vn)), atol=1e-8)

SIZE = 24                      # his legend words, set beside their curves


def _label(f, ax, xv, yf, s, anchor, color, anim=None):
    """His words at data x and a fraction yf of the panel's height (a <br>
    breaks a long one in two); returns the label's box in figure px."""
    X, Y = float(ax.X(xv)), ax.y + ax.h * (1 - yf)
    lines = s.split("<br>")
    w = max(textw(t, SIZE) for t in lines)
    h = SIZE * (1.05 if len(lines) == 1 else 1.3 * len(lines))
    f.text(X, Y, s, anchor, size=SIZE, color=color, anim=anim)
    dx = {"west": 0, "east": -w, "south": -w / 2, "north": -w / 2}[anchor]
    dy = {"west": -h / 2, "east": -h / 2, "south": -h, "north": 0}[anchor]
    return X + dx, Y + dy, w, h


def _panel(xlim, ticks, unit, old, data, new, labels, t0):
    """One case: the old estimate (navy), the new data (accent, dashed) and
    the combined estimate (a blue-edged fill) over the quantity's axis."""
    f = Fig(832, 372)
    ax = f.axes(18, 10, 796, 262, xlim=xlim, ylim=(0, 1), frame=False)
    x = np.linspace(xlim[0] + 0.5, xlim[1] - 0.5, 1400)
    ys = [d.pdf(x) for d in (old, data, new)]
    top = max(float(y.max()) for y in ys) / 0.95
    ys = [y / top for y in ys]
    at = (t0 + .4, t0 + 1.0, t0 + 1.7)              # old, data, combined
    ax.area(x, ys[2], color=C.steel2, anim=fade(at[2], .5))
    ax.plot(x, ys[2], color=C.blue, width=2.2, anim=draw(at[2], .6))
    ax.plot(x, ys[0], color=C.navy, width=4, anim=draw(at[0], .6))
    ax.plot(x, ys[1], color=C.accent, width=4, dash="14 9", anim=draw(at[1], .6))
    # the quantity's axis: a baseline with outward ticks, as his
    yb = ax.y + ax.h + 4
    f.line([(ax.x, yb), (ax.x + ax.w, yb)], stroke=C.ink, width=2, cap="butt", anim=fade(t0 + .2, .4))
    for t in ticks:
        X = float(ax.X(t))
        f.line([(X, yb), (X, yb + 10)], stroke=C.ink, width=2, cap="butt", anim=fade(t0 + .2, .4))
        f.text(X, yb + 22, num(t), "north", cls="tk", anim=fade(t0 + .2, .4))
    f.text(ax.x + ax.w / 2, yb + 22 + 28 + 14, unit, "north", cls="axl", anim=fade(t0 + .2, .4))
    curves = np.vstack([np.column_stack([ax.X(x), ax.Y(y)]) for y in ys])
    for (xv, yf, s, anchor), color, t in zip(labels, (C.navy, C.accent, C.blue), at):
        box = _label(f, ax, xv, yf, s, anchor, color, anim=pop(t + .3))
        assert clear(box, curves, 10), f"{s!r} sits on a curve"
        assert box[0] >= ax.x - 1 and box[0] + box[2] <= ax.x + ax.w + 1, f"{s!r} leaves the panel"
    return f.html()


def case_a():
    return _panel((23.5, 38.5), range(24, 39, 2), "MPa",
                  norm(30, 2), norm(32, 0.6), norm(NEW_A, np.sqrt(VAR_A)), [
                      (24.0, 0.42, "prior belief: 30 MPa (SD 2)", "west"),
                      (32.9, 0.72, "25 tests: 32 MPa (SE 0.6)", "west"),
                      (31.15, 0.9, "combined: 31.83 MPa", "east"),
                  ], t0=0.3)


def case_b():
    return _panel((1.5, 25.5), range(5, 26, 5), "mm",
                  norm(10, 2), norm(14, 3), norm(NEW_B, np.sqrt(VAR_B)), [
                      (7.6, 0.84, "model prediction: <br>10 mm (SD 2)", "east"),
                      (17.4, 0.52, "sensor: 14 mm (SD 3)", "west"),
                      (12.9, 0.9, "combined: 11.23 mm", "west"),
                  ], t0=3.4)
