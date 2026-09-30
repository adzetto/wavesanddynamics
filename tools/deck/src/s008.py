"""Slide 8: eight families, each drawn from its own density or mass function
(scipy.stats), on a common baseline, scaled to the panel's height. The
parameters give the shapes of his gallery:

normal       N(0, 1) on [-3.6, 3.6]
lognormal    ln X ~ N(0, 0.5^2) on [0, 4]            mode e^-0.25 = 0.78
gumbel       largest value, location 0, scale 1, on [-3, 7]
weibull      shape 3.5, scale 1, on [0, 2.2]          weakest link
exponential  rate 1 on [0, 6]                         no memory
poisson      mean 3, counts 0 to 10                   his bars: p(2) = p(3)
binomial     n = 10, p = 0.2, 0 to 10 successes       "a sample of 10"
beta         Beta(2, 5) on [0, 1]                     mode 1/5
Continuous families are an area (mist) under the density drawn in navy;
counts are bars, one per value."""
import numpy as np
from scipy import stats

from fig import Fig, C

W, H = 400, 150


def _panel(dist, lo, hi, discrete=False, kmax=None):
    f = Fig(W, H)
    base = H - 4
    top = 8
    f.line([(0, base), (W, base)], stroke=C.ink, width=2, cap="butt")
    if discrete:
        k = np.arange(0, kmax + 1)
        p = dist.pmf(k)
        scale = (base - top) / p.max()
        step = W / (kmax + 1)
        for kk, pp in zip(k, p):
            hgt = pp * scale
            if hgt < 0.5:
                continue
            x0 = kk * step + step * 0.16
            f.rect(x0 + step * 0.04, base - hgt, step * 0.6, hgt, fill=C.navy)
        return f.html()
    x = np.linspace(lo, hi, 700)
    y = dist.pdf(x)
    y = np.nan_to_num(y)
    scale = (base - top) / y.max()
    X = (x - lo) / (hi - lo) * (W - 8) + 4
    Y = base - y * scale
    pts = list(zip(X, Y))
    f.poly(pts + [(X[-1], base), (X[0], base)], fill=C.mist)
    f.line(pts, stroke=C.navy, width=3)
    return f.html()


def normal():
    return _panel(stats.norm(), -3.6, 3.6)


def lognormal():
    return _panel(stats.lognorm(0.5), 0, 4)


def gumbel():
    return _panel(stats.gumbel_r(), -3, 7)


def weibull():
    return _panel(stats.weibull_min(3.5), 0, 2.2)


def exponential():
    return _panel(stats.expon(), 0, 6)


def poisson():
    d = stats.poisson(3)
    assert abs(d.pmf(2) - d.pmf(3)) < 1e-12
    return _panel(d, 0, 0, discrete=True, kmax=10)


def binomial():
    return _panel(stats.binom(10, 0.2), 0, 0, discrete=True, kmax=10)


def beta():
    return _panel(stats.beta(2, 5), 0, 1)
