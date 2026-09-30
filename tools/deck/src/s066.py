"""Slide 66: one Kalman update is Bayes' rule for two normal sources (his
notes; scalar case, H = 1, independent errors).

Prior, the model's prediction for this hour:  N(10, 2^2)
Sensor reading 14 mm with noise SD 3 mm:      likelihood N(14, 3^2)
Gain      K = 2^2 / (2^2 + 3^2) = 4/13 = 0.3077
Estimate  10 + K (14 - 10) = 11.2308 mm
New SD    sqrt((1 - K) 4) = sqrt(36/13) = 1.664 mm, smaller than both 2 and 3.
The posterior drawn is the normalised product of the two densities, checked
against N(11.23, 1.66^2) below. The arrow runs from the prior mean to the
posterior mean: K = 31% of the way from 10 to the reading 14."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C
from s065 import clear, legend, textw

MU0, SD0, Z, SDV = 10.0, 2.0, 14.0, 3.0
K = SD0 ** 2 / (SD0 ** 2 + SDV ** 2)
MU1 = MU0 + K * (Z - MU0)
SD1 = float(np.sqrt((1 - K) * SD0 ** 2))
assert abs(K - 4 / 13) < 1e-15 and round(K, 2) == 0.31
assert round(MU1, 2) == 11.23 and round(SD1, 2) == 1.66
assert round(100 * K) == 31 and SD1 < SD0 < SDV
_x = np.linspace(-10, 30, 40001)
_prod = norm.pdf(_x, MU0, SD0) * norm.pdf(Z, _x, SDV)
assert np.allclose(_prod / np.trapezoid(_prod, _x), norm.pdf(_x, MU1, SD1), atol=1e-9)

LABEL = "moves 31% of the way toward the sensor"


def update():
    f = Fig(976, 584)
    ax = f.axes(122, 12, 834, 474, xlim=(0, 20), ylim=(0, 0.5),
                xticks=range(0, 21, 2), yticks=[0, 0.1, 0.2, 0.3, 0.4],
                xlabel="Displacement (mm)", ylabel="Probability density")
    x = np.linspace(0, 20, 1201)
    prior, sensor, post = norm.pdf(x, MU0, SD0), norm.pdf(x, Z, SDV), norm.pdf(x, MU1, SD1)
    ax.area(x, post, color=C.steel2)
    # the arrow: prior mean to posterior mean, just over the posterior's peak
    peak = norm.pdf(MU1, MU1, SD1)
    ya = peak + 20 / (ax.h / 0.5)
    for m, col in ((MU0, C.navy), (MU1, C.blue), (Z, C.accent)):
        ax.vline(m, color=col, width=2, dash="5 6", y1=ya)
    ax.plot(x, prior, color=C.navy, width=4)
    ax.plot(x, sensor, color=C.accent, width=4, dash="14 9")
    ax.plot(x, post, color=C.blue, width=4.5)
    (x0, y0), (x1, _) = ax.P(MU0, ya), ax.P(MU1, ya)
    f.arrow((x0, y0), (x1 - 2, y0), color=C.blue, width=3)
    size = 26
    lw = textw(LABEL, size)
    f.text((x0 + x1) / 2, y0 - 12, LABEL, "south", size=size, color=C.blue)
    lab = ((x0 + x1) / 2 - lw / 2, y0 - 12 - size * 1.1, lw, size * 1.1)
    box = legend(f, ax.x + 16, ax.y + 16, [
        ("Model prediction (prior): 10 mm, SD 2", {"color": C.navy, "width": 4}),
        ("Sensor reading: 14 mm, SD 3", {"color": C.accent, "width": 4, "dash": "14 9"}),
        ("Updated estimate (posterior): 11.23 mm, SD 1.66",
         {"kind": "band", "fill": C.steel2, "color": C.blue, "width": 4.5}),
    ])
    curves = np.vstack([np.column_stack([ax.X(x), ax.Y(y)]) for y in (prior, sensor, post)])
    assert clear(box, curves, 12) and clear(lab, curves, 12), "a label sits on a curve"
    assert lab[1] > box[1] + box[3] + 16, "the arrow's label runs into the legend"
    assert lab[0] > ax.x + 8 and lab[0] + lab[2] < ax.x + ax.w - 8
    return f.html()
