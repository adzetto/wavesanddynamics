"""Slide 4: the chance of finding the one defect among 25 items when k are
inspected without replacement. Hypergeometric: P(find) = 1 - C(24,k)/C(25,k),
which is k/25 exactly (his 3/25 = 12%, P(miss) = C(24,3)/C(25,3) = 88%)."""
import numpy as np
from scipy.stats import hypergeom

from fig import Fig, C

K = np.arange(0, 26)
P_FIND = 1 - hypergeom(25, 1, K).pmf(0)          # lot 25, 1 defect, K drawn
assert np.allclose(P_FIND, K / 25)
assert abs(hypergeom(25, 1, 3).pmf(0) - 0.88) < 1e-12


def curve():
    f = Fig(976, 650)
    ax = f.axes(136, 14, 822, 500, xlim=(-1, 26), ylim=(-4, 104),
                xticks=[0, 3, 10, 15, 20, 25], yticks=range(0, 101, 20),
                xlabel="Number inspected without replacement",
                ylabel="Chance of finding the defect (%)", grid=True)
    ax.plot(K, 100 * P_FIND, color=C.navy, width=3)
    ax.scatter(K, 100 * P_FIND, r=6, color=C.navy)
    ax.mark(3, 100 * P_FIND[3], r=12)
    x0, y0 = ax.P(8.6, 12)
    ax.leader((x0 - 10, y0), (3, 12), gap=19, width=2.5)
    f.text(x0, y0, "3 inspected: 12%", "west", size=32, color=C.accent)
    return f.html()
