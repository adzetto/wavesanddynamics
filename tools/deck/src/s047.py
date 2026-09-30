"""Slide 47: three views of one narrow-band random vibration (his notes).

The model: a zero-mean Gaussian process with autocorrelation
R(tau) = exp(-a |tau|) cos(2 pi f0 tau), a = 0.5 1/s, f0 = 2 Hz (his curve: the
peaks every 0.5 s shrink by exp(-0.25) = 0.78, and his spectrum peaks at 4).

1  x(t): one record of the process, 5 s at 100 samples/s, simulated exactly as
   the first coordinate of a damped rotation driven by white noise,
   s[k+1] = exp(-a dt) Rot(2 pi f0 dt) s[k] + sqrt(1 - exp(-2 a dt)) w[k], started
   in its stationary law (numpy's PCG64, seed below), then divided by its own
   SD, so its variance is exactly 1.
2  R(tau) for lags 0 to 3 s: R(0) = variance = 1.
3  The one-sided spectrum G(f) = 2 S(f), S the Fourier transform of R:
   G(f) = L(f - f0) + L(f + f0), L(f) = 2a / (a^2 + (2 pi f)^2). Its peak is
   G(2 Hz) = 4.0; its area is R(0) = 1 (asserted by quadrature)."""
import numpy as np
from scipy.integrate import quad

from fig import Fig, C

A, F0, DT = 0.5, 2.0, 0.01


def R(tau):
    return np.exp(-A * np.abs(tau)) * np.cos(2 * np.pi * F0 * tau)


def G(f):
    L = lambda u: 2 * A / (A * A + (2 * np.pi * u) ** 2)
    return L(f - F0) + L(f + F0)


def record(seed=4701, n=501):
    rng = np.random.default_rng(seed)
    r, th = np.exp(-A * DT), 2 * np.pi * F0 * DT
    rot = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
    s = np.empty((n, 2))
    s[0] = rng.standard_normal(2)
    w = rng.standard_normal((n, 2))
    for k in range(1, n):
        s[k] = r * rot @ s[k - 1] + np.sqrt(1 - r * r) * w[k]
    x = s[:, 0]
    return np.arange(n) * DT, (x - x.mean()) / x.std()


T, X = record()
F = np.linspace(0, 5, 2001)
assert abs(X.var() - 1) < 1e-12 and R(0) == 1
assert abs(quad(G, 0, np.inf, limit=500)[0] - 1) < 1e-9
assert round(float(G(F0)), 1) == 4.0 and abs(F[np.argmax(G(F))] - F0) < 1e-9

W, H = 544, 440
BOX = (106, 46, 424, 300)


def _frame(title):
    f = Fig(W, H)
    x, y, w, h = BOX
    f.text(x, y - 12, title, "south west", size=28, color=C.navy, font="serif", weight=600)
    return f


def signal():
    f = _frame("1&ensp;Signal in time: <m>x(t)</m>")
    ax = f.axes(*BOX, xlim=(-0.12, 5.12), ylim=(-3.4, 3.4), xticks=range(0, 6),
                yticks=[-2, -1, 0, 1, 2], xlabel="Time <m>t</m> (s)",
                ylabel="<m>x</m> (normalized)")
    ax.plot(T, X, color=C.navy, width=2.5)
    ax.text(0.04, -3.24, "variance scaled to 1", "south west", size=24, color=C.muted)
    return f.html()


def autocorrelation():
    f = _frame("2&ensp;Autocorrelation: <m>R(τ)</m>")
    ax = f.axes(*BOX, xlim=(-0.08, 3.08), ylim=(-1.02, 1.72), xticks=[0, 0.5, 1, 1.5, 2, 2.5, 3],
                yticks=[-0.5, 0, 0.5, 1],
                xlabel="Lag <m>τ</m> (s)", ylabel="<m>R(τ)</m>")
    ax.hline(0, color=C.guide, dash=None, width=1.5)
    tau = np.linspace(0, 3, 1501)
    ax.plot(tau, R(tau), color=C.accent, width=3.5)
    # R(0): the variance
    ax.mark(0, 1, r=8)
    ax.text(0.28, 1.45, "<m>R(0) = variance = 1</m>", "west", size=26, color=C.accent)
    ax.leader(ax.P(0.245, 1.43), (0, 1), gap=14, width=2)
    # the rhythm: the peaks come back every 0.5 s
    ax.text(1.22, 1.22, "repeats every 0.5 s <br>(a 2 Hz rhythm)", "north west", size=26,
            color=C.body)
    f.arrow(ax.P(1.19, 1.02), ax.P(1.03, 0.67), color=C.body, width=2)
    return f.html()


def spectrum():
    f = _frame("3&ensp;Spectrum: <m>G(f)</m>")
    ax = f.axes(*BOX, xlim=(-0.12, 5.12), ylim=(-0.12, 4.4), xticks=range(0, 6),
                yticks=range(0, 5), xlabel="Frequency <m>f</m> (Hz)",
                ylabel="<m>G(f)</m>&ensp;(<m>x²</m> per Hz)")
    ax.area(F, G(F), color=C.steel2)
    ax.plot(F, G(F), color=C.blue, width=3.5)
    ax.text(2.28, 3.55, "peak at 2 Hz", "west", size=26, color=C.blue)
    ax.text(2.7, 2.1, "shaded area <br><m>= variance = 1</m>", "west", size=26, color=C.body)
    return f.html()
