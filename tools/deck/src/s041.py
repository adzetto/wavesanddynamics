"""Slide 41: one realization of each of his four families, drawn from the
models his later slides use (each a pseudo-random draw, numpy's default
generator with a fixed seed, so the pictures are the same every run).

markov    his pavement chain of slide 53, yearly steps, P = [[0.8, 0.2, 0],
          [0, 0.7, 0.3], [0, 0, 1]] over 20 years from Good. Seed 6 gives a
          path like his: 5 years Good, 7 Degraded, then Failed.
walk      his daily settlement random walk of slide 51: zero drift, normal
          steps of SD 0.3 mm, 40 daily readings, each one marked (seed 49:
          a dip, then the long climb of his picture).
poisson   his truck arrivals of slide 55: a Poisson process of rate 2 per
          hour over 7 hours, N(t) stepping up by one at each arrival (seed
          241: 14 arrivals, the expected count, spread as his).
vibration a narrow-band Gaussian response as slide 47's, normalized: two
          lightly damped modes (1.5% damping), 2 Hz with 75% of the
          variance and 4 Hz with 25%, whose beat gives his double crests; by
          the spectral representation (400 cosines, random phases), 6 s.
The four keep his colours (navy, orange, purple, teal: the deck's navy,
accent, blue and sky), their plots bare as his: the axis lines, no numbers."""
import numpy as np

from fig import Fig, C, draw, fade, seq

# The four families one at a time, each tracing out its history
# (DECK_BRIEF.md "Animated slides"; the headings' moments are in
# s041.html): the chain steps year by year, the walk day by day, the
# arrivals count up, the vibration draws; then the table that sorts them.
ANIM = {"length": 8.2}

P = np.array([[0.8, 0.2, 0.0], [0.0, 0.7, 0.3], [0.0, 0.0, 1.0]])
assert np.allclose(P.sum(axis=1), 1)
PW, PH = 342, 236                     # every plot box, the four the same size
LEFT, RIGHT = 436, 380                # the two columns: the left holds his state names
FH = PH + 8


def _chain(seed=6, years=20):
    rng = np.random.default_rng(seed)
    s = [0]
    for _ in range(years):
        s.append(int(rng.choice(3, p=P[s[-1]])))
    return np.array(s)


STATES = _chain()
assert [int((STATES == k).sum()) for k in range(3)] == [5, 7, 9]


def _axes(f, xlim, ylim, **kw):
    """A bare plot box, his style: the left and bottom lines, no numbers. In
    the left column it sits right, after his state names; in the right one,
    left."""
    x0 = LEFT - PW - 8 if f.w == LEFT else 2
    return f.axes(x0, 4, PW, PH, xlim=xlim, ylim=ylim, box=False, ticks="none", **kw)


def markov():
    f = Fig(LEFT, FH)
    ax = _axes(f, (-0.8, 20.8), (-0.25, 2.25), yticks=[0, 1, 2],
               yticklabels=["Good", "Degr.", "Failed"], anim=fade(.5, .4))
    t = np.arange(len(STATES) + 1)
    ax.step(t, np.r_[STATES, STATES[-1]], color=C.navy, width=5, anim=seq(.8, .06))
    return f.html()


def walk(seed=49):
    f = Fig(RIGHT, FH)
    rng = np.random.default_rng(seed)
    x = np.r_[0.0, np.cumsum(rng.normal(0, 0.3, 39))]
    ax = _axes(f, (-1.5, 40.5), (x.min() - 0.4, x.max() + 0.4), anim=fade(1.8, .4))
    d = np.arange(40)
    ax.plot(d, x, color=C.accent, width=3.5, anim=seq(2.1, .025))
    ax.scatter(d, x, r=4.5, color=C.accent, anim=seq(2.1, .025, visual=.2))
    return f.html()


def poisson(seed=241, rate=2.0, hours=7.0):
    f = Fig(LEFT, FH)
    rng = np.random.default_rng(seed)
    t = np.cumsum(rng.exponential(1 / rate, 40))
    t = t[t < hours]
    n = len(t)
    assert n == 14                    # his rate x 7 h = 14 expected
    ax = _axes(f, (-0.2, hours + 0.1), (-0.8, n + 0.8), anim=fade(3.1, .4))
    ax.step(np.r_[0, t, hours], np.r_[0, np.arange(1, n + 1), n], color=C.blue, width=4,
            anim=seq(3.4, .06))
    return f.html()


def vibration(seed=47, dur=6.0):
    f = Fig(RIGHT, FH)
    rng = np.random.default_rng(seed)
    fr = np.linspace(0.05, 10, 400)
    df = fr[1] - fr[0]

    def mode(f0, z):                  # an SDOF's response spectrum to white noise
        r = fr / f0
        return 1 / ((1 - r ** 2) ** 2 + (2 * z * r) ** 2)

    g1, g2 = mode(2.0, 0.015), mode(4.0, 0.015)
    G = 0.75 * g1 / (g1.sum() * df) + 0.25 * g2 / (g2.sum() * df)   # variance 1
    assert abs(G.sum() * df - 1) < 1e-9
    t = np.linspace(0, dur, 1500)
    ph = rng.uniform(0, 2 * np.pi, len(fr))
    x = (np.sqrt(2 * G * df)[:, None] * np.cos(2 * np.pi * fr[:, None] * t + ph[:, None])).sum(0)
    ax = _axes(f, (-0.15, dur + 0.15), (x.min() - 0.3, x.max() + 0.3), anim=fade(4.4, .4))
    ax.plot(t, x, color=C.sky, width=3, anim=draw(4.7, .9))
    return f.html()
