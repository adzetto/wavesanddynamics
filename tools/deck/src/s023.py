"""Slide 23: regression read as a probability model, on his illustrative data:
Y | x ~ N(beta0 + beta1 x, sigma^2) with beta0 = 75 MPa, beta1 = -80 MPa
(per unit w/c), sigma = 3 MPa (his note under the chart).

tests    60 (as his picture has): w/c ratio x uniform on [0.38, 0.64] and the
         scatter N(0, 3^2), a deterministic draw (fig.sample, independent)
band     95% of outcomes at each x: mean +- 1.96 sigma
curves   the normal density of Y at x = 0.42, 0.55 and 0.62, drawn sideways
         to the left of its x, over mean +- 3.5 sigma
limit    25 MPa. At x = 0.55 the mean is 31 MPa, so
         P(Y < 25 | x = 0.55) = Phi((25 - 31)/3) = Phi(-2) = 2.3% (his number),
         the small shaded tail of the middle curve."""
import numpy as np
from scipy import stats

from fig import Fig, C, sample

B0, B1, SIGMA, LIMIT = 75.0, -80.0, 3.0, 25.0
Z95 = stats.norm.ppf(0.975)
XT, E = sample(60, stats.uniform(0.38, 0.26), stats.norm(0, SIGMA))
YT = B0 + B1 * XT + E
assert B0 + B1 * 0.55 == 31.0
assert round(100 * stats.norm(31, SIGMA).cdf(LIMIT), 1) == 2.3


def mean(x):
    return B0 + B1 * np.asarray(x, float)


def model():
    f = Fig(976, 604)
    ax = f.axes(120, 14, 838, 470, xlim=(0.34, 0.68), ylim=(12, 58),
                xticks=np.arange(0.35, 0.66, 0.05), yticks=range(15, 56, 5), xtick_nd=2,
                xlabel="Water-to-cement ratio <m>x</m>", ylabel="28-day strength <m>Y</m> (MPa)")
    xb = np.linspace(0.36, 0.67, 50)
    ax.area(xb, mean(xb) + Z95 * SIGMA, mean(xb) - Z95 * SIGMA, color=C.steel)
    ax.hline(LIMIT, color=C.accent, width=2.5, dash="10 7")
    ax.text(0.365, LIMIT + 0.7, "25 MPa limit", "south west", color=C.accent)
    ax.plot(xb, mean(xb), color=C.navy, width=4.5)
    ax.scatter(XT, YT, r=6, color=C.navy, opacity=0.5)
    # the distribution of Y at three x values, on its side
    A = 0.03                                      # the peak's width, in x units
    for x0 in (0.42, 0.55, 0.62):
        m = mean(x0)
        y = np.linspace(m - 3.5 * SIGMA, m + 3.5 * SIGMA, 400)
        g = np.exp(-0.5 * ((y - m) / SIGMA) ** 2)          # pdf / its peak
        ax.vline(x0, color=C.blue, width=1.5, dash="2 5", y0=y[0], y1=y[-1])
        if x0 == 0.55:                                     # the tail below the limit
            t = y[y <= LIMIT]
            gt = np.exp(-0.5 * ((t - m) / SIGMA) ** 2)
            pts = ax._pts(x0 - A * gt, t) + ax._pts([x0, x0], [LIMIT, t[0]])
            f.poly(pts, fill=C.amber)
        ax.plot(x0 - A * g, y, color=C.blue, width=3.5)
    # his reading of the middle curve
    lx, ly = ax.P(0.366, 17.6)
    f.text(lx, ly, "<m>P(Y &lt; 25 | x = 0.55) = 2.3%</m>", "west", color=C.accent)
    tip = ax.P(0.5445, 23.2)
    f.arrow((lx + 372, ly - 8), tip, color=C.accent, width=2.5)
    pad, row, size = 16, 40, 26
    bx, by, bw, bh = ax.legend([("95% of outcomes at each <m>x</m>", {"kind": "area", "color": C.steel}),
                                ("tests", {"kind": "mark", "color": C.paper, "r": 6}),
                                ("mean: <m>β₀ + β₁x</m>", {"color": C.navy, "width": 4})],
                               at="north east", pad=pad, size=size, row=row)
    # the legend's test mark as the tests are drawn (fig's legend has no opacity for marks)
    f.circle(bx + pad + 22, by + pad + size / 2 + row, 6, fill=C.navy, opacity=0.5)
    return f.html()
