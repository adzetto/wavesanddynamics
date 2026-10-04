"""Slide 52: his constructed path, read from his chart: the response sampled
once a second, t = 0 to 10 s, against a limit of 2 mm. The first sampled value
above the limit is at 4 s (his "first observed crossing"); the last, X(T) at
T = 10 s, is below it; the path was above the limit at 4, 5 and 6 s. Sampling
can miss a crossing between two observations."""
import numpy as np

from fig import Fig, C, draw, fade, pop, seq

# The limit, then the path second by second (DECK_BRIEF.md "Animated
# slides"; the blocks' moments are in s052.html): its first crossing is
# marked as it happens, and the path ends back below; then the two
# questions, each answered by what was just seen.
ANIM = {"length": 5.7}

T = np.arange(0, 11)                                            # s
X = np.array([0.0, 0.4, 0.7, 1.5, 2.5, 2.7, 2.1, 1.4, 1.8, 1.2, 1.4])   # mm
LIMIT = 2.0
FIRST = int(T[np.argmax(X > LIMIT)])
assert FIRST == 4 and X[-1] < LIMIT and X.max() > LIMIT
assert list(T[X > LIMIT]) == [4, 5, 6]


def path():
    f = Fig(976, 650)
    ax = f.axes(136, 14, 822, 500, xlim=(-0.4, 10.4), ylim=(-0.15, 3.2),
                xticks=range(0, 11, 2), yticks=[0, 0.5, 1, 1.5, 2, 2.5, 3],
                xlabel="Time (s)", ylabel="Response (mm)", grid=True, anim=fade(.3, .4))
    ax.hline(LIMIT, color=C.deep, width=3, dash="12 8", anim=draw(.6, .5))
    ax.plot(T, X, color=C.navy, width=4, anim=seq(1.0, .2))
    ax.scatter(T, X, r=7, color=C.navy, anim=seq(1.0, .2, visual=.25))
    ax.mark(FIRST, X[FIRST], r=12, anim=pop(1.0 + .2 * FIRST + .1))
    ax.text(FIRST - 0.22, X[FIRST] + 0.2, "First observed crossing", "south east", size=30,
            color=C.accent, anim=pop(1.0 + .2 * FIRST + .2))
    ax.legend([("Limit = 2 mm", {"color": C.deep, "dash": "12 8", "width": 3})],
              at="north east", size=28, row=40, pad=16, sample=56, inset=18, anim=pop(.7))
    return f.html()
