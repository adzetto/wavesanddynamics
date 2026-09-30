"""Slide 68: a Kalman filter on the model of his notes, "a correctly
specified scalar random walk model with Q = .035 mm^2 and R = .65 mm^2".

    x[k] = x[k-1] + w[k],   w ~ N(0, 0.035)     (the displacement, mm)
    z[k] = x[k] + v[k],     v ~ N(0, 0.65)      (the noisy observations)
    k = 0 .. 89 measurement steps.
Correctly specified all through: the truth starts from the filter's own prior,
x[0] ~ N(0, 1), and the filter starts from that prior (x^ = 0, P = 1) and
updates with every observation (K = P- / (P- + R), then P- = P + Q). The band
is the 95% posterior interval, x^ +/- 1.96 sqrt(P); P settles to
(-Q + sqrt(Q^2 + 4QR)) / 2 = 0.134 mm^2 (SD 0.37 mm).
The draw is numpy's PCG64 generator, seed 0 (a time series needs a random
order in time, which fig.sample's Halton points do not give)."""
import numpy as np

from fig import Fig, C
from s065 import clear, dense, legend

N, Q, R, SEED = 90, 0.035, 0.65, 0


def simulate(seed=SEED):
    rng = np.random.default_rng(seed)
    x0 = rng.normal(0.0, 1.0)
    w = rng.normal(0.0, np.sqrt(Q), N - 1)
    v = rng.normal(0.0, np.sqrt(R), N)
    x = x0 + np.concatenate([[0.0], np.cumsum(w)])
    z = x + v
    xh, P = np.empty(N), np.empty(N)
    xp, Pp = 0.0, 1.0                                  # the prior
    for k in range(N):
        if k:
            xp, Pp = xh[k - 1], P[k - 1] + Q            # predict (F = 1)
        K = Pp / (Pp + R)
        xh[k], P[k] = xp + K * (z[k] - xp), (1 - K) * Pp   # update
    return x, z, xh, P


T = np.arange(N)
TRUE, Z, XH, P = simulate()
P_SS = (-Q + np.sqrt(Q * Q + 4 * Q * R)) / 2
assert abs(P[-1] - P_SS) < 1e-9 and round(np.sqrt(P_SS), 2) == 0.37
COVER = float(np.mean(np.abs(TRUE - XH) <= 1.96 * np.sqrt(P)))
assert 0.9 < COVER <= 1.0          # the interval covers the truth, as a 95% interval should


def filtered():
    f = Fig(1696, 484)
    ax = f.axes(108, 14, 1572, 378, xlim=(-2, 91), ylim=(-3.4, 4.4),
                xticks=range(0, 81, 20), yticks=range(-3, 4),
                xlabel="Measurement step", ylabel="Displacement (mm)")
    lo, hi = XH - 1.96 * np.sqrt(P), XH + 1.96 * np.sqrt(P)
    ax.area(T, hi, lo, color=C.steel2)
    ax.scatter(T, Z, r=5.5, color=C.amber, opacity=0.8)
    ax.plot(T, TRUE, color=C.ink, width=2.6, dash="11 7")
    ax.plot(T, XH, color=C.navy, width=4)
    box = legend(f, ax.x + 18, ax.y + 16, [
        ("Noisy observations", {"kind": "dot", "color": C.amber, "r": 5.5, "opacity": 0.8}),
        ("95% posterior interval", {"kind": "area", "fill": C.steel2}),
        ("Simulated truth", {"color": C.ink, "width": 2.6, "dash": "11 7"}),
        ("Kalman estimate", {"color": C.navy, "width": 4}),
    ], cols=2)
    data = np.vstack([dense(ax, T, hi), dense(ax, T, TRUE), np.column_stack([ax.X(T), ax.Y(Z)])])
    assert clear(box, data, margin=10), "the legend sits on the data"
    return f.html()
