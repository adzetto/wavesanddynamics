"""Slide 52: his constructed path, read from his chart: the response sampled
once a second, t = 0 to 10 s, against a limit of 2 mm. The first sampled value
above the limit is at 4 s (his "first observed crossing"); the last, X(T) at
T = 10 s, is below it; the path was above the limit at 4, 5 and 6 s. Sampling
can miss a crossing between two observations."""
import numpy as np

from fig import Fig, C

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
                xlabel="Time (s)", ylabel="Response (mm)", grid=True)
    ax.hline(LIMIT, color=C.deep, width=3, dash="12 8")
    ax.plot(T, X, color=C.navy, width=4)
    ax.scatter(T, X, r=7, color=C.navy)
    ax.mark(FIRST, X[FIRST], r=12)
    ax.text(FIRST - 0.22, X[FIRST] + 0.2, "First observed crossing", "south east", size=30,
            color=C.accent)
    ax.legend([("Limit = 2 mm", {"color": C.deep, "dash": "12 8", "width": 3})],
              at="north east", size=28, row=40, pad=16, sample=56, inset=18)
    return f.html()
