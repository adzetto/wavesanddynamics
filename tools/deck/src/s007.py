"""Slide 7: the three small pictures of the probability machinery.

dots   25 equally likely outcomes, 3 of them favourable: P(A) = 3/25 = 12%.
area   X ~ N(0, 1); the shaded area between a = -0.5 and b = 1 (where his
       picture puts them) is P(a < X < b) = Phi(1) - Phi(-0.5) = 0.5328.
cloud  (X, Y) jointly normal with correlation 0.7: 200 points drawn from
       that model by a Halton sequence (deterministic, the same every run).
His Bayes numbers, checked: prior 0.01, sensitivity 0.90, false alarms
0.05 give P(D|A) = 0.009 / (0.009 + 0.0495) = 0.1538, his 15.4%."""
import numpy as np
from scipy.stats import norm

from fig import Fig, C, sample

A, B = -0.5, 1.0
assert abs((norm.cdf(B) - norm.cdf(A)) - 0.5328) < 1e-4
assert round(100 * 0.01 * 0.90 / (0.01 * 0.90 + 0.99 * 0.05), 1) == 15.4


def dots():
    f = Fig(164, 164)
    k = 0
    for row in range(5):
        for col in range(5):
            f.circle(14 + col * 34, 14 + row * 34, 11.5, fill=C.accent if k < 3 else C.navy)
            k += 1
    return f.html()


def area():
    f = Fig(420, 170)
    ax = f.axes(8, 6, 404, 112, xlim=(-3.3, 3.3), ylim=(0, 0.42), box=False,
                xticks=[A, B], xticklabels=["<m>a</m>", "<m>b</m>"], ticks="out")
    x = np.linspace(-3.3, 3.3, 600)
    xs = np.linspace(A, B, 200)
    ax.area(xs, norm.pdf(xs), color=C.amber)
    ax.plot(x, norm.pdf(x), color=C.navy, width=3.5)
    return f.html()


def cloud():
    f = Fig(420, 170)
    ax = f.axes(46, 6, 366, 112, xlim=(-3, 3), ylim=(-3, 3), box=False,
                xlabel="Load <m>X</m>", ylabel="Response <m>Y</m>", ylabel_gap=26)
    x, y = sample(200, norm(), norm(), rho=0.7)
    ax.scatter(x, y, r=4.5, color=C.navy, opacity=0.55)
    return f.html()
