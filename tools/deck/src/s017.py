"""Slide 17: why 1.96. Z = (Xbar - mu)/SE is N(0, 1) under his assumptions
(25 independent normal tests, sigma = 3 MPa known), and the central 95% of
N(0, 1) lies between -z and z with z = Phi^-1(0.975) = 1.95996, his 1.96;
each tail holds 2.5%. Back in MPa: SE = 3/sqrt(25) = 0.6, 1.96 x 0.6 =
1.176, and xbar = 32 gives his [30.82, 33.18] MPa."""
import numpy as np
from scipy import stats

from fig import Fig, C

Z975 = stats.norm.ppf(0.975)
assert round(Z975, 2) == 1.96
assert abs(stats.norm.cdf(1.96) - stats.norm.cdf(-1.96) - 0.95) < 5e-4
SE = 3 / np.sqrt(25)
assert SE == 0.6 and round(1.96 * SE, 3) == 1.176
assert (round(32 - 1.96 * SE, 2), round(32 + 1.96 * SE, 2)) == (30.82, 33.18)


def central():
    f = Fig(832, 452)
    ax = f.axes(120, 12, 700, 330, xlim=(-3.9, 3.9), ylim=(0, 0.43),
                xticks=[-1.96, 0, 1.96], yticks=[0, 0.1, 0.2, 0.3, 0.4], ytick_nd=1,
                xlabel="Standardized mean <m>Z</m>", ylabel="Density")
    pdf = stats.norm.pdf
    mid = np.linspace(-1.96, 1.96, 500)
    ax.area(mid, pdf(mid), color=C.steel2)
    for a, b in ((-3.9, -1.96), (1.96, 3.9)):
        t = np.linspace(a, b, 300)
        ax.area(t, pdf(t), color=C.amber)
    x = np.linspace(-3.9, 3.9, 1000)
    ax.plot(x, pdf(x), color=C.navy, width=4)
    ax.text(0, 0.19, "95%", "center", size=46, color=C.navy)
    for s in (-1, 1):
        ax.text(s * 2.75, 0.075, "2.5%", "center", color=C.accent)
    return f.html()
