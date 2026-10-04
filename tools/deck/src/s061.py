"""Slide 61: two estimators of the same theta, as distributions of their
error theta_hat - theta over repeated datasets (his notes: illustrative
Gaussian errors).

A  unbiased, SD 1:           error ~ N(0, 1),     MSE = 1 + 0 = 1
B  bias 0.5, SD 0.5:         error ~ N(0.5, 0.5^2), MSE = 0.25 + 0.5^2 = 0.5
MSE = variance + bias^2, so the biased B has the lower MSE. The dashed line
is zero error, the true theta."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop

# Target, observation, estimator, then what makes a rule better
# (DECK_BRIEF.md "Animated slides"; the blocks' moments are in s061.html):
# the two estimators' errors draw around zero, the unbiased wide one first,
# then the biased narrow one, each with its legend entry.
ANIM = {"length": 6.4}
from s053 import tw
from s058 import legend_rows, _top

A, B = stats.norm(0, 1), stats.norm(0.5, 0.5)
MSE_A, MSE_B = A.var() + A.mean() ** 2, B.var() + B.mean() ** 2
assert np.isclose(MSE_A, 1) and np.isclose(MSE_B, 0.5)


def errors():
    f = Fig(976, 432)
    x, y, w, h = 124, 8, 844, 322
    rows = [[("A: unbiased, SD = 1", {"color": C.navy, "width": 4})],
            [("B: bias = 0.5, SD = 0.5", {"color": C.accent, "width": 4})]]
    # the legend (top right) clears the curves beneath it; the axis clears B's peak
    lw = 2 * 12 + 44 + 10 + tw("B: bias = 0.5, SD = 0.5", 26)
    xl = -3.3 + (w - 14 - lw) / w * 7.6
    e = np.linspace(xl - 0.1, 4.3, 400)
    top = max(_top(-0.03, np.maximum(A.pdf(e), B.pdf(e)).max(), h, 14 + 2 * 12 + 30 + 36 + 12),
              np.ceil(100 * B.pdf(0.5) * 1.08) / 100)
    ax = f.axes(x, y, w, h, xlim=(-3.3, 4.3), ylim=(-0.03, top), xticks=range(-3, 5),
                yticks=[0, 0.2, 0.4, 0.6, 0.8], xlabel="Estimation error <m>θ̂ − θ</m>",
                ylabel="Density", anim=fade(3.2, .4))
    ax.vline(0, color=C.blue, width=2.5, dash="8 6", anim=draw(3.6, .4))
    e = np.linspace(-3.3, 4.3, 900)
    ax.plot(e, A.pdf(e), color=C.navy, width=4, anim=draw(3.9, .7))
    ax.plot(e, B.pdf(e), color=C.accent, width=4, anim=draw(4.7, .7))
    bx, by, bw, bh = legend_rows(ax, rows, anim=[pop(3.9), pop(3.9), pop(4.7)])
    under = (ax.X(e) > bx - 6) & (ax.X(e) < bx + bw + 6)
    assert (ax.Y(np.maximum(A.pdf(e), B.pdf(e))[under]) > by + bh + 6).all()
    return f.html()
