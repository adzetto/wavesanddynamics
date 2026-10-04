"""Slide 40: one process, many histories.

Model: a stationary Gaussian AR(1) response, normalized to mean 0 and variance
1, sampled every 0.1 s over his 0 to 17.9 s: X(t + 0.1) = 0.9 X(t) + e(t),
e ~ N(0, 1 - 0.9^2), X(0) ~ N(0, 1) (a correlation time of about 1 s). Twelve
realizations are drawn in the mist and one more in the accent, his "one
realization"; the dashed line is his "one time", t = 8 s, where each
realization's value is marked: the many possible values at that time. A
pseudo-random draw (numpy's default generator, seed 40), fixed so the picture
is the same every run: fig.sample's Halton points are for independent draws,
not for the steps of a path."""
import numpy as np

from fig import Fig, C, draw, fade, pop
from s031 import tw

# Many histories, then one time across them, then one history along time
# (DECK_BRIEF.md "Animated slides"; the blocks' moments are in s040.html):
# twelve realizations draw one after another, the line t = 8 s marks the
# value each has there, and the accent realization draws last. Each legend
# entry arrives with its line.
ANIM = {"length": 8.4}

DT, T_END, PHI = 0.1, 17.9, 0.9
T = np.round(np.arange(0, T_END + 1e-9, DT), 10)
T_ONE = 8.0


def paths(n=13, seed=40):
    rng = np.random.default_rng(seed)
    x = np.empty((n, len(T)))
    x[:, 0] = rng.standard_normal(n)
    e = rng.standard_normal((n, len(T) - 1)) * np.sqrt(1 - PHI ** 2)
    for i in range(1, len(T)):
        x[:, i] = PHI * x[:, i - 1] + e[:, i - 1]
    return x


X = paths()
# the model's variance is 1 at every time, so the draw is stationary from t = 0
assert abs(np.var(X) - 1) < 0.25 and np.abs(X).max() < 4.2


def history():
    f = Fig(1696, 492)
    box, lim = (118, 50, 1566, 342), dict(xlim=(-0.6, 18.5), ylim=(-4.4, 3.9))
    ax = f.axes(*box, xticks=np.arange(0, 17.6, 2.5), yticks=range(-4, 4), grid=False,
                xlabel="Time (s)", ylabel="Response (normalized)", anim=fade(.3, .4), **lim)
    for i, row in enumerate(X[1:]):
        ax.plot(T, row, color=C.mist, width=2.2, anim=draw(1.0 + .12 * i, .9))
    ax.vline(T_ONE, color=C.navy, width=3, dash="12 8", anim=draw(3.6, .4))
    ax.plot(T, X[0], color=C.accent, width=4.5, anim=draw(4.9, 1.0))
    k = int(round(T_ONE / DT))
    for j, v in enumerate(X[:, k]):
        f.circle(*ax.P(T_ONE, v), 5.5, fill=C.navy, anim=pop(4.0 + .06 * j))
    # his legend, one row over the plot
    entries = [("One realization", {"color": C.accent, "width": 4.5}),
               ("One time: many possible values", {"color": C.navy, "width": 3, "dash": "12 8"})]
    x0, cy = ax.x, 18
    for (t, st), at in zip(entries, (4.9, 3.6)):          # each with its line
        f.line([(x0, cy), (x0 + 48, cy)], stroke=st["color"], width=st["width"], dash=st.get("dash"),
               cap="butt", anim=pop(at))
        f.text(x0 + 60, cy, t, "west", size=28, anim=pop(at))
        x0 += 60 + tw(t, 28) + 56
    return f.html()
