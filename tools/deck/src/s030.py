"""Slide 30: why the tangent misses the mean, F fixed at 100 N.

Y = 100/k mm. At k = 18, 20 and 22 N/mm, Y = 5.556, 5.000 and 4.545 mm:
the softer spring gains 0.556 and the stiffer loses only 0.455, so the
average of the two outer cases is 5.0505 mm, above Y(20) = 5.00. The first
order line, the tangent at k = 20, is Y = 5 - 0.25 (k - 20): it cannot see
the bend. The second order term 1/2 Y''(20) sigma_k^2 = 1/2 x 200/20^3 x 2^2
= 0.05 mm reproduces the shift (his numbers, all asserted below). The
tangent is drawn in orange because his words name it so ("The tangent
(orange)"); everything else takes the deck's palette."""
import numpy as np

from fig import Fig, C

F = 100.0


def y(k):
    return F / np.asarray(k, float)


def tangent(k):
    return 5.0 - 0.25 * (np.asarray(k, float) - 20)


PTS = [18, 20, 22]
AVG = (float(y(18)) + float(y(22))) / 2
assert [round(float(y(k)), 2) for k in PTS] == [5.56, 5.0, 4.55]
assert round(float(y(18)) - 5, 2) == 0.56 and round(float(y(22)) - 5, 2) == -0.45
assert round(AVG, 2) == 5.05
assert 2 * F / 20 ** 3 == 0.025 and 0.5 * 0.025 * 2 ** 2 == 0.05
assert abs(-F / 20 ** 2 - (-0.25)) < 1e-12                # the tangent's slope


def curve():
    f = Fig(976, 454)
    ax = f.axes(112, 8, 848, 346, xlim=(13.2, 30.8), ylim=(3, 8.0),
                xticks=range(14, 31, 2), yticks=range(3, 8),
                xlabel="Stiffness <m>k</m> (N/mm), fixed <m>F = 100</m> N", ylabel="<m>Y</m> (mm)")
    k = np.linspace(13.2, 30.8, 700)
    for kv in PTS:
        ax.vline(kv, color=C.ink, width=2, dash="2 6", y0=3, y1=float(y(kv)))
    ax.hline(AVG, color=C.blue, width=3, dash="16 7 3 7")
    ax.plot(k, tangent(k), color=C.orange_edge, width=3.5, dash="13 8")   # "The tangent (orange)"
    ax.plot(k, y(k), color=C.navy, width=4.5)
    ax.scatter(PTS, y(PTS), r=9, color=C.navy)
    # his two readings, each by its point
    x0, y0 = ax.P(15.3, 7.84)                     # above the curve, left of the legend
    f.text(x0, y0, "<m>k = 18</m>: 5.56 mm <br>(+0.56)", "north west", color=C.accent)
    ax.leader((x0 + 100, y0 + 66), (18, float(y(18))), gap=16, width=2)
    x1, y1 = ax.P(23.2, 4.66)
    f.text(x1, y1, "<m>k = 22</m>: 4.55 mm (<m>−0.45</m>)", "west", color=C.accent)
    ax.leader((x1 - 8, y1), (22, float(y(22))), gap=16, width=2)
    ax.legend([("<m>Y</m> = 100 / <m>k</m> (curve)", {"color": C.navy, "width": 4.5}),
               ("First order: tangent at <m>k = 20</m>", {"color": C.orange_edge, "width": 3.5, "dash": "13 8"}),
               ("Average of <m>k = 18</m> and 22: 5.05 mm", {"color": C.blue, "width": 3, "dash": "16 7 3 7"})],
              at="north east", size=26, row=40)
    return f.html()
