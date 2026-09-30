"""Slide 38: the reliability of his first case, independent normal R and S.

Model: R ~ N(100, 10^2) kN, S ~ N(70, 8^2) kN, independent, so the margin
G = R - S ~ N(30, 164) kN exactly (linear, jointly normal). Its reliability
index is beta = mu_G/sigma_G = 30/sqrt(164) = 30/12.81 = 2.34 and the failure
probability P(G < 0) = Phi(-beta) = 0.957%, his 0.96%. The picture is the
density of G on his range, -30 to 85 kN, with the failure region G < 0 (R < S)
in his red (the deck's deep) and the limit G = 0 dashed."""
import numpy as np
from scipy import stats

from fig import Fig, C

G = stats.norm(30, np.sqrt(164))
BETA = G.mean() / G.std()
assert f"{G.std():.2f}" == "12.81" and f"{BETA:.2f}" == "2.34" and f"{30 / 12.81:.2f}" == "2.34"
assert f"{100 * G.cdf(0):.2f}" == "0.96" and abs(stats.norm.cdf(-BETA) - G.cdf(0)) < 1e-15


def margin():
    f = Fig(976, 668)
    box, lim = (150, 10, 806, 562), dict(xlim=(-34, 90), ylim=(-0.0012, 0.0335))
    ax0 = f.axes(*box, frame=False, **lim)
    xs = np.linspace(-30, 0, 300)
    ax0.area(xs, G.pdf(xs), color=C.deep, opacity=0.45)
    ax = f.axes(*box, xticks=range(-20, 81, 20), yticks=[0, 0.01, 0.02, 0.03], ytick_nd=2,
                xlabel="Safety margin <m>G</m> = capacity − demand (kN)",
                ylabel="Probability density", grid=True, **lim)
    ax.vline(0, color=C.deep, width=3, dash="10 7")
    x = np.linspace(-30, 85, 800)
    ax.plot(x, G.pdf(x), color=C.navy, width=5)
    X, Y = ax.P(-3.5, 0.0138)
    f.text(X, Y, "Failure<br> <m>R &lt; S</m>", "east", size=30, color=C.deep)
    return f.html()
