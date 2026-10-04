"""Slide 28: the linear case, the spring with k fixed at 20 N/mm.

Y = F/20 = 0.05 F with F ~ N(100, 10^2) N, so Y ~ N(5.00, 0.50^2) mm
exactly: the line maps the input density (along the bottom) onto the output
density (up the side) without changing its shape. His three forces 90, 100
and 110 N give 4.5, 5.0 and 5.5 mm: equal steps in, equal steps out. His
load example, checked: W = D + L, D 400 +- 20 and L 150 +- 40 kN
independent, gives mu_W = 550 kN and sigma_W = sqrt(20^2 + 40^2) = 44.7 kN."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, draw, fade, pop, seq, wipe

# The formulas, then the spring that obeys them (DECK_BRIEF.md "Animated
# slides"; the blocks' moments are in s028.html): the straight line, the
# input density rising from the force axis, the three equal steps carried up
# to the line and across, then the output density out of the Y axis: the
# same shape.
ANIM = {"length": 8.4}

K = 20.0
F_DIST = norm(100, 10)
Y_DIST = norm(100 / K, 10 / K)
assert (Y_DIST.mean(), Y_DIST.std()) == (5.0, 0.5)
assert [f / K for f in (90, 100, 110)] == [4.5, 5.0, 5.5]
assert 400 + 150 == 550 and round(np.hypot(20, 40), 1) == 44.7

Y0 = 2.2                      # the axis floor: the F density's baseline
F0 = 60.0                     # the axis wall: the Y density's baseline


def line():
    f = Fig(832, 500)
    ax = f.axes(96, 8, 720, 392, xlim=(F0, 140), ylim=(Y0, 8.0),
                xticks=range(60, 141, 10), yticks=range(3, 8),
                xlabel="Force <m>F</m> (N), fixed <m>k = 20</m> N/mm", ylabel="<m>Y</m> (mm)",
                anim=fade(2.9, .4))
    # the input density along the bottom (peak 1.0 mm tall), the output up
    # the side (peak 14 N wide): the same normal curve, scaled by the line
    fx = np.linspace(F0, 140, 400)
    ax.area(fx, Y0 + 1.0 * F_DIST.pdf(fx) / F_DIST.pdf(100), Y0, color=C.steel2,
            anim=wipe(4.1, .6, "up"))
    yy = np.linspace(Y0, 8.0, 400)
    wx = F0 + 14.0 * Y_DIST.pdf(yy) / Y_DIST.pdf(5)
    f.poly(ax._pts(wx, yy) + ax._pts([F0, F0], [8.0, Y0]), fill=C.blue, fill_opacity=0.42,
           clip=ax.clip, anim=wipe(6.3, .6))
    for j, fv in enumerate((90, 100, 110)):
        yv, t = fv / K, 5.1 + .35 * j             # up from F to the line, then across to Y
        ax.vline(fv, color=C.ink, width=2, dash="2 6", y0=Y0, y1=yv, anim=draw(t, .3))
        ax.hline(yv, color=C.ink, width=2, dash="2 6", x0=F0, x1=fv, anim=fade(t + .3, .3))
    ax.plot([F0, 140], [F0 / K, 140 / K], color=C.navy, width=4.5, anim=draw(3.3, .6))
    ax.scatter([90, 100, 110], [4.5, 5.0, 5.5], r=8, color=C.navy, anim=seq(5.35, .35))
    ax.text(76.5, 6.5, "<m>Y</m>: normal", "west", color=C.blue, anim=pop(6.6))
    ax.text(76.5, 6.1, "mean 5.0, SD 0.5", "west", color=C.blue, anim=pop(6.7))
    ax.text(138, 3.66, "<m>F</m>: normal", "east", color="var(--sky-ink)", anim=pop(4.4))
    ax.text(138, 3.26, "mean 100, SD 10", "east", color="var(--sky-ink)", anim=pop(4.5))
    ax.legend([("<m>Y = F</m> / 20 (straight line)", {"color": C.navy, "width": 4.5})],
              at="north west", size=26, row=40, anim=pop(3.4))
    return f.html()
