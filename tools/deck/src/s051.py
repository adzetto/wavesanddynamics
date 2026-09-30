"""Slide 51: a zero-drift random walk of sensor bias (his notes).

X_n = X_0 + e_1 + ... + e_n with X_0 = 0 and independent normal increments
e_i ~ N(0, 0.3^2) mm, so E[X_n] = X_0 and Var(X_n) = n 0.3^2: the standard
deviation grows as sqrt(n). The band is the pointwise 95% interval
+-1.96 * 0.3 * sqrt(n) mm (7.4 mm at n = 160, as his band ends); it is not a
promise that 95% of whole paths stay inside. Four paths of 160 steps are a
fixed draw (numpy's PCG64, seed below), the same every run."""
import numpy as np

from fig import Fig, C, SERIES

SIGMA, N, Z95 = 0.3, 160, 1.959964
n = np.arange(0, N + 1)
HALF = Z95 * SIGMA * np.sqrt(n)
assert round(float(HALF[-1]), 1) == 7.4

rng = np.random.default_rng(5101)
PATHS = np.concatenate([np.zeros((4, 1)), np.cumsum(rng.normal(0, SIGMA, (4, N)), axis=1)], axis=1)
YL = 8.4
assert np.abs(PATHS).max() < YL


def walk():
    f = Fig(976, 616)
    ax = f.axes(136, 14, 822, 470, xlim=(-4, 164), ylim=(-YL, YL),
                xticks=range(0, 161, 40), yticks=[-8, -4, 0, 4, 8],
                xlabel="Step <m>n</m>", ylabel="Sensor bias (mm)")
    ax.area(n, HALF, -HALF, color=C.steel)
    ax.hline(0)
    for k, p in enumerate(PATHS):
        ax.plot(n, p, color=SERIES[k], width=2.5)
    ax.legend([("Pointwise 95% band", {"kind": "area", "color": C.steel})], at="north west",
              size=28, row=40, pad=14, sample=48, inset=16)
    return f.html()
