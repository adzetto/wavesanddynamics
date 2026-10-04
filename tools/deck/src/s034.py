"""Slide 34: Monte Carlo for his spring in three pictures.

Model (his notes, slide 26's inputs): F ~ N(100, 10^2) N, k lognormal with
mean 20 and SD 2 N/mm, independent, Y = F/k mm, 200,000 draws. The draw is
numpy's default generator with seed 7 (F first, then k, as slide 33's): it
gives every number his picture prints and his picture's shapes, so it is taken
to be his run: mean 5.050 mm, SD 0.715 mm, 1,490 outputs beyond 7 mm (0.745%,
printed 0.74% as his), the first 1,500 pairs spanning F 67 to 128 N and k 15
to 28 N/mm, and a running mean that starts at 4.86, dips to 4.75 at N = 36
and crosses 5.00 near N = 1,000.

draw     the first 1,500 pairs (k, F), each dot coloured by its y = F/k on a
         sequential scale (light to dark as y grows), with its colour bar.
collect  the density of all 200,000 outputs on 0.05 mm bins, the mean, and
         the tail beyond 7 mm in the accent.
error    the running mean for N = 10 to 200,000 on a log axis, with +-2 SE =
         +-2 SD/sqrt(N) from the running SD, the exact mean 5.050 (slide 32)
         and the first order value 5.000.
His panel texts: first order gives P(Y > 7) = 1 - Phi(2/0.707) = 0.23%, the
simulation 0.74%, about 3 times more; SD/sqrt(N) = 0.0016 mm at N = 200,000."""
from functools import lru_cache

import numpy as np
from scipy import stats

from fig import Fig, C, fade, pop, wipe
from fig import draw as draw_in          # draw() is this slide's first picture
from s031 import legend, ramp, tw

# The three pictures in turn (DECK_BRIEF.md "Animated slides"; the blocks'
# moments are in s034.html): the input pairs arrive a hundred at a time and
# their colour scale after them; the histogram of the outputs rises and its
# tail is marked; the running mean draws out as N grows, its band uncovered
# with it.
ANIM = {"length": 10.7}
from s032 import MEAN as EXACT
from s033 import simulate, hist_area

F, K, Y = simulate(7)
N = len(Y)
assert f"{Y.mean():.3f}" == "5.050" and f"{Y.std(ddof=1):.3f}" == "0.715"
assert int((Y > 7).sum()) == 1490 and f"{100 * (Y > 7).mean():.2f}" == "0.74"
P1 = stats.norm.sf(7, 5.0, np.sqrt(0.5))
assert f"{100 * P1:.2f}" == "0.23" and round(0.74 / 0.23) == 3
assert f"{Y.std(ddof=1) / np.sqrt(N):.4f}" == "0.0016"
assert f"{EXACT:.3f}" == "5.050"

H = 436
TOP, PH = 8, 330                      # the plot boxes' top and height, shared
YR = (2.7, 8.1)                       # the colour scale, his bar's range
SEQ = ramp(C.mist, C.navy)
LAB = 24                              # the panels' annotations


@lru_cache(maxsize=None)
def running():
    n = np.arange(1, N + 1)
    m = np.cumsum(Y) / n
    v = (np.cumsum(Y ** 2) - n * m ** 2) / np.maximum(n - 1, 1)
    return n, m, np.sqrt(np.maximum(v, 0))


def draw():
    f = Fig(526, H)
    ax = f.axes(96, TOP, 290, PH, xlim=(14.2, 28.8), ylim=(64, 133),
                xticks=[15, 20, 25], yticks=range(70, 131, 10),
                xlabel="Stiffness <m>k</m> (N/mm)", ylabel="Force <m>F</m> (N)", anim=fade(.5, .4))
    n = 1500
    t = (Y[:n] - YR[0]) / (YR[1] - YR[0])
    for i, (x, yv, tt) in enumerate(zip(K[:n], F[:n], t)):
        X, Yp = ax.P(x, yv)
        f.circle(X, Yp, 3.6, fill=SEQ(tt), clip=ax.clip, anim=fade(.9 + .12 * (i // 100), .25))
    # the colour bar: the same scale, his ticks 3 to 8 mm
    bx, bw = ax.x + ax.w + 22, 20
    steps = 110
    for i in range(steps):
        y0 = TOP + PH - (i + 1) * PH / steps
        f.rect(bx, y0, bw, PH / steps + 0.6, fill=SEQ((i + 0.5) / steps), anim=fade(2.8, .4))
    f.rect(bx, TOP, bw, PH, stroke=C.ink, width=1.5, anim=fade(2.8, .4))
    for v in range(3, 9):
        yy = TOP + PH - (v - YR[0]) / (YR[1] - YR[0]) * PH
        f.line([(bx + bw, yy), (bx + bw + 8, yy)], stroke=C.ink, width=1.5, cap="butt", anim=fade(2.8, .4))
        f.text(bx + bw + 14, yy, str(v), "west", cls="tk", anim=fade(2.8, .4))
    f.text(bx + bw + 62, TOP + PH / 2, "<m>y = F/k</m> (mm)", "center", cls="axl", rot=-90,
           anim=fade(2.8, .4))
    assert bx + bw + 62 + 16 < f.w
    return f.html()


def collect():
    f = Fig(592, H)
    box, lim = (100, TOP, 480, PH), dict(xlim=(2.5, 9.5), ylim=(0, 0.6))
    ax0 = f.axes(*box, frame=False, **lim)
    edges = np.round(np.arange(2.5, 9.5001, 0.05), 2)
    h = hist_area(ax0, Y, edges, anim=wipe(3.9, .8, "up"))
    hot = edges[:-1] >= 7.0 - 1e-9
    xs = np.repeat(edges[np.r_[hot, True] & (edges >= 7.0 - 1e-9)], 2)[1:-1]
    ax0.area(xs, np.repeat(h[hot], 2), 0.0, color=C.amber, anim=fade(4.8, .3))
    ax = f.axes(*box, xticks=[4, 6, 8], yticks=np.arange(0, 0.51, 0.1), ytick_nd=1,
                xlabel="Displacement <m>y</m> (mm)", ylabel="Density", anim=fade(3.5, .4), **lim)
    ax.vline(Y.mean(), color=C.navy, width=3.5, dash=None, anim=draw_in(5.0, .35))
    # his two labels, right of the peak, each clear of the bars under it
    mids = (edges[:-1] + edges[1:]) / 2
    x1, y1 = 6.2, 0.555
    f.text(*ax.P(x1, y1), "mean 5.050 mm<br> SD 0.715 mm", "north west", size=LAB, anim=pop(5.3))
    assert h[mids >= x1].max() < y1 - (2 * 1.3 * LAB) / PH * 0.6 - 0.02
    x2, y2 = 5.85, 0.31
    lab = "<m>P(Y > 7 mm) = 0.74%</m>"
    X2, Y2 = ax.P(x2, y2)
    f.text(X2, Y2, lab, "south west", size=LAB, color=C.accent, anim=pop(5.7))
    assert h[mids >= x2].max() < y2 - 0.015
    assert X2 + tw(lab, LAB) < ax.x + ax.w - 6
    f.arrow((X2 + 150, Y2 + 6), ax.P(7.26, 0.028), color=C.accent, width=2.5, anim=draw_in(5.8, .4))
    return f.html()


def error():
    f = Fig(514, H)
    n, m, s = running()
    box, lim = (104, TOP, 400, PH), dict(xlim=(8, 3e5), ylim=(4.7, 5.4), xlog=True)
    # plotted on a log grid of N: every point of the path from 10 to 1,000,
    # then 1,200 log-spaced ones (the path is smooth there)
    idx = np.unique(np.concatenate([np.arange(10, 1000),
                                    np.geomspace(1000, N, 1200).astype(int)])) - 1
    se = 2 * s[idx] / np.sqrt(n[idx])
    f.axes(*box, frame=False, **lim).area(n[idx], m[idx] + se, m[idx] - se, color=C.steel2,
                                          anim=wipe(7.6, 1.4))
    # decade ticks; the exponent inside <m> so it reads at the tick's size
    sup = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    ax = f.axes(*box, xticks=[10.0 ** e for e in range(1, 6)],
                xticklabels=[f"<m>10{sup[e]}</m>" for e in range(1, 6)],
                yticks=np.arange(4.7, 5.41, 0.1), ytick_nd=1,
                xlabel="Number of simulations <m>N</m>", ylabel="Estimated mean (mm)",
                anim=fade(6.5, .4), **lim)
    ax.plot([8, 3e5], [EXACT, EXACT], color=C.blue, width=3, dash="12 7", anim=draw_in(6.9, .5))
    ax.plot([8, 3e5], [5.0, 5.0], color=C.accent, width=3.5, dash="0.1 8", anim=draw_in(7.2, .5))
    ax.plot(n[idx], m[idx], color=C.navy, width=3.5, anim=draw_in(7.6, 1.4))
    bx, by, bw, bh = legend(f, ax.x + ax.w - 10, ax.y + 10, [
        ("<m>± 2 SE = ± 2 SD/√N</m>", {"kind": "area", "color": C.steel2}),
        ("running mean", {"color": C.navy, "width": 3.5}),
        ("exact mean 5.050", {"color": C.blue, "width": 3, "dash": "12 7"}),
        ("first order 5.000", {"color": C.accent, "width": 3.5, "dash": "0.1 8"}),
    ], size=LAB, row=31, pad=12, sample=40, anchor="north east",
        anim=[pop(6.9), pop(7.6), pop(7.6), pop(6.9), pop(7.2)])
    # the legend sits over no data: the band's top under it stays below it
    n0 = 10 ** np.interp(bx, [ax.x, ax.x + ax.w], np.log10(lim["xlim"]))
    under = n[idx] >= n0
    assert (m[idx] + se)[under].max() < 5.4 - (by + bh - ax.y) / PH * 0.7
    return f.html()
