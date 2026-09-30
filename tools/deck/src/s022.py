"""Slide 22: his illustrative survey, drawn from the model his notes give.

Daily household trips at household size x = 1..6, five households at each
size (30 in all, as in his picture): trips | x ~ N(1.03 + 1.80 x, 1.0^2).
The mean line is his notes' fit, 1.03 + 1.80 x; the scatter, SD 1.0 trip,
is what his picture shows (the residual SD of his points is about 1.0). The
30 residuals are the deterministic draw slide 12's residual panel uses
(fig.sample, skip 34: the draw whose least-squares line is his), so the two
slides agree number for number. The accent line is the least-squares fit to
these points: 1.03 + 1.80 x, as his notes give it.

DATA and FIT are shared with slide 24, which draws its two bands on them."""
import numpy as np
from scipy import stats

from fig import Fig, C, sample

B0, B1, SIGMA = 1.03, 1.80, 1.0
X = np.repeat(np.arange(1, 7), 5).astype(float)          # persons per household
TRIPS = B0 + B1 * X + sample(30, stats.norm(0, SIGMA), skip=34)   # as src/s012.py
FIT = np.polyfit(X, TRIPS, 1)[::-1]                        # (intercept, slope)
assert (round(FIT[0], 2), round(FIT[1], 2)) == (B0, B1), FIT


def fitted(x):
    return FIT[0] + FIT[1] * np.asarray(x, float)


def trips():
    f = Fig(976, 652)
    ax = f.axes(120, 14, 838, 502, xlim=(0.4, 6.6), ylim=(0.8, 14.8),
                xticks=range(1, 7), yticks=range(2, 15, 2),
                xlabel="Persons per household", ylabel="Daily household trips", grid=True)
    xs = np.array([0.6, 6.4])
    ax.plot(xs, fitted(xs), color=C.accent, width=4.5)
    ax.scatter(X, TRIPS, r=8, color=C.navy)
    f.text(ax.x + 26, ax.y + 22, "Illustrative survey data", "north west")
    return f.html()
