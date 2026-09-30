"""Slide 65a (ours, not in his file): the Kalman filter's logic as one loop,
and one weigh-and-update step in one dimension, drawn exactly.

The picture is the next slide's hour (s066: the model predicts N(10, 2^2) mm,
the sensor reads 14 mm with noise SD 3 mm; H = 1), in the loop's symbols:
    prediction   x^-_k = 10 mm,   P-_k = 4 mm^2
    measurement  z_k = 14 mm,     R = 9 mm^2
    gain         K_k = P- / (P- + R) = 4/13, the loop's K for H = 1
    update       x^_k = x^- + K (z - x^-) = 11.23 mm,   P_k = (1 - K) P- = 36/13
The update's curve is the normalised product of the prediction's density
and the measurement's likelihood, checked against N(x^_k, P_k) below.

The lever: a level beam on a fulcrum under x^_k, symmetric about it (its own
weight balances), carrying the two precisions, 1/P- at x^-_k and 1/R at z_k,
drawn as discs of those areas. Their arms are K and 1 - K of the gap between
the two, and they balance, (1/P-) K = (1/R) (1 - K), which is the gain's
formula again: the update is where the two precisions balance. The scale
under the beam reads 0 at the prediction and 1 at the reading; the fulcrum
stands at K. The slide's words are ours (his.OURS): no em dash.

The slide plays (DECK_BRIEF.md "Animated slides"): once around the loop, each
box as its step comes and the picture drawn as the step says. Predict: the
prediction's density. Observe: the reading's. Weigh: the lever, its fulcrum
setting off from the prediction (0 on the scale) and coming to rest at K,
where the two precisions balance. Update: the product, the update's density.
Then the loop closes for the next hour and the take-away comes."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, draw, fade, keys, pop
from s066 import MU0, SD0, Z, SDV, K, MU1, SD1

# the loop's steps, seconds from the slide's start; the boxes and the wires
# in s065a.html start at these cues
T_PRED, T_OBS, T_GAIN, T_UPD, T_NEXT = 0.3, 2.3, 4.3, 6.6, 8.5
ANIM = {"length": 9.8}

PM, R = SD0 ** 2, SDV ** 2                  # P-_k and R, mm^2
PK = (1 - K) * PM                           # P_k
assert abs(K - PM / (PM + R)) < 1e-15 and abs(MU1 - (MU0 + K * (Z - MU0))) < 1e-12
assert abs(np.sqrt(PK) - SD1) < 1e-12 and PK < PM < R
_x = np.linspace(-10, 30, 40001)
_prod = norm.pdf(_x, MU0, SD0) * norm.pdf(Z, _x, SDV)
assert np.allclose(_prod / np.trapezoid(_prod, _x), norm.pdf(_x, MU1, np.sqrt(PK)), atol=1e-9)
assert abs(K / PM - (1 - K) / R) < 1e-15   # the lever balances

LO, HI = 5.0, 21.0                          # mm: each curve down to 7 % of its peak


def weigh():
    """The update in one dimension: the prediction's and the measurement's
    densities, their product (the update), and over them the lever."""
    W, H = 568, 540                          # 24 px clear of the boxes either side
    f = Fig(W, H)
    for name, t in (("predict", T_PRED), ("observe", T_OBS), ("weigh", T_GAIN), ("update", T_UPD),
                    ("next", T_NEXT)):
        f.cue(name, t)
    base = H - 58                            # the axis line
    ax = f.axes(8, 128, W - 16, base - 128, xlim=(LO, HI), ylim=(0, 0.245), frame=False)
    xs = np.linspace(LO, HI, 1401)
    prior, sensor, post = norm.pdf(xs, MU0, SD0), norm.pdf(xs, Z, SDV), norm.pdf(xs, MU1, SD1)
    assert max(prior[0], prior[-1], sensor[0], sensor[-1]) < .07 * post.max()
    xa, xf, xb = (float(ax.X(v)) for v in (MU0, MU1, Z))
    # the lever: a beam level on a fulcrum under the update, symmetric about
    # it (its own weight balances), with the precisions 1/P- and 1/R at the
    # prediction and at the reading, discs of those areas
    r0, r1 = 40 / SD0, 40 / SDV
    assert abs((r0 / r1) ** 2 - R / PM) < 1e-12
    half = (xb - xf) + 44
    yb = 2 * r0 + 6                          # the beam
    th, tw = 30, 18                          # the fulcrum
    ls = 30
    ylab = yb + th + 8                       # the scale under it: 0, K, 1
    # when each step's marks arrive: its curve drawn, its point named on the
    # axis, then its guide let down to the scale
    t_curve = {MU0: T_PRED + .5, Z: T_OBS + .4, MU1: T_UPD + .4}
    ax.area(xs, post, color=C.steel2, anim=fade(T_UPD + .4, .6))
    for m, sd, col in ((MU0, SD0, C.navy), (MU1, SD1, C.blue), (Z, SDV, C.accent)):
        f.line([(float(ax.X(m)), float(ax.Y(norm.pdf(m, m, sd))) - 4), (float(ax.X(m)), ylab + ls + 6)],
               stroke=col, width=2, dash="5 6", cap="butt", anim=draw(t_curve[m] + .9, .5))
    ax.plot(xs, prior, color=C.navy, width=4, anim=draw(t_curve[MU0], 1.0))
    ax.plot(xs, sensor, color=C.accent, width=4, dash="14 9", anim=draw(t_curve[Z], 1.0))
    ax.plot(xs, post, color=C.blue, width=4.5, anim=draw(t_curve[MU1], 1.0))
    f.line([(ax.x, base), (ax.x + ax.w, base)], stroke=C.ink, width=2, cap="butt", anim=fade(T_PRED + .2, .4))
    for X, s, col, m in ((xa, "<m>x̂ₖ⁻</m>", C.navy, MU0), (xf, "<m>x̂ₖ</m>", C.blue, MU1),
                         (xb, "<m>zₖ</m>", C.accent, Z)):
        f.line([(X, base), (X, base - 10)], stroke=C.ink, width=2, cap="butt", anim=pop(t_curve[m]))
        f.text(X, base + 12, s, "north", size=30, color=col, cls="ml", anim=pop(t_curve[m]))
    # the lever: the beam and the two weights, then the fulcrum sets off from
    # the prediction (0) and rests at K, where the precisions balance
    t_lever = T_GAIN + .3
    slide_ = pop(t_lever + .3) + keys([t_lever + .3, t_lever + .7], [xa, xf], prop="x", visual=.8)
    f.poly([(xf, yb + 2), (xf - tw, yb + th), (xf + tw, yb + th)], fill=C.sky, anim=slide_)
    f.line([(xf - half, yb), (xf + half, yb)], stroke=C.ink, width=4, cap="butt", anim=fade(t_lever, .3))
    f.circle(xa, yb - 2 - r0, r0, fill=C.navy, anim=pop(t_lever + .1))
    f.circle(xb, yb - 2 - r1, r1, fill=C.accent, anim=pop(t_lever + .2))
    # the scale reads 0 under the prediction, where the fulcrum sets off, and
    # names K where it comes to rest
    rest = slide_.parts[-1].end
    for X, s, a in ((xa, "0", pop(t_lever + .3)), (xf, "<m>K</m>", pop(rest - .1)), (xb, "1", pop(t_lever + .3))):
        f.text(X, ylab, s, "north", size=ls, anim=a)
    # the weights, named: the precisions
    f.text(xa - r0 - 10, yb - 8, "<m>1/Pₖ⁻</m>", "south east", size=28, color=C.navy, cls="ml",
           anim=pop(t_lever + .2))
    f.text(xb + r1 + 10, yb - 8, "<m>1/R</m>", "south west", size=28, color=C.accent, anim=pop(t_lever + .3))
    # the scale clears the curves; the lever stays inside the picture
    top = min(float(ax.Y(v.max())) for v in (prior, sensor, post))
    assert ylab + ls + 10 < top, "the lever's scale runs into the curves"
    assert xf - half > 0 and xf + half < W
    return f.html()
