"""Slide 42: five records of one process, stationary and not (his notes).

Time runs t = 0, 1, ..., 200 s. Left: a Gaussian AR(1) process started in its
stationary law, X[t] = phi X[t-1] + sqrt(1 - phi^2) e[t] with phi = 0.7 (his
notes give no coefficient), so E X(t) = 0 and Var X(t) = 1 at every t. Right:
the same kind of process times a growing scale s(t) = sqrt(0.2 + 0.02 t), so
Var X(t) = 0.2 + 0.02 t. The band is the model's +-2 SD at each time.

The bars are the model's variance averaged over his three windows, 0-60,
70-130 and 140-200 s: 1.0 in each on the left; on the right the variance is
linear in t, so each window's average is its value at the window's middle,
0.8, 2.2 and 3.6 (his numbers, asserted). Each bar spans its window on the
time axis of the panel above it.

The five records of each panel are a fixed draw (numpy's PCG64 with the seeds
below), the same every run."""
import numpy as np

from fig import Fig, C, SERIES

T = np.arange(0, 201)                        # s
PHI = 0.7
WINDOWS = [(0, 60), (70, 130), (140, 200)]
SEEDS = (4201, 4202)                         # left panel, right panel


def var_right(t):
    return 0.2 + 0.02 * np.asarray(t, float)


def records(seed, n=5):
    """n AR(1) records with unit variance, each started in its stationary law."""
    rng = np.random.default_rng(seed)
    e = rng.standard_normal((n, len(T)))
    x = np.empty_like(e)
    x[:, 0] = e[:, 0]
    for i in range(1, len(T)):
        x[:, i] = PHI * x[:, i - 1] + np.sqrt(1 - PHI ** 2) * e[:, i]
    return x


def window_var(var):
    return [float(np.mean(var(T[(T >= a) & (T <= b)]))) for a, b in WINDOWS]


LEFT = window_var(lambda t: np.ones_like(t, float))
RIGHT = window_var(var_right)
assert [round(v, 1) for v in LEFT] == [1.0, 1.0, 1.0]
assert [round(v, 1) for v in RIGHT] == [0.8, 2.2, 3.6]
assert np.allclose(RIGHT, [0.8, 2.2, 3.6])

X_LEFT = records(SEEDS[0])
X_RIGHT = records(SEEDS[1]) * np.sqrt(var_right(T))

# the figure: two columns (stationary, not), a record panel over a bar panel
W, H = 976, 622
BOX_W = 380
COLS = (96, 570)                              # left edge of each column's boxes
TS_Y, TS_H = 48, 244                          # record panels
BAR_Y, BAR_H = 456, 110                       # variance panels
YL = 8.4


def _title(f, x, y, words, color):
    f.text(x, y, words, "south west", size=28, color=color, font="serif", weight=600)


def stationarity():
    f = Fig(W, H)
    panels = [
        (COLS[0], X_LEFT, np.ones_like(T, float), C.steel, C.navy, LEFT, C.navy,
         "Stationary: the rules stay the same", C.navy),
        (COLS[1], X_RIGHT, var_right(T), C.wash, C.accent, RIGHT, C.amber,
         "Not stationary: the spread grows", C.deep),
    ]
    assert np.abs(X_LEFT).max() < YL and np.abs(X_RIGHT).max() < YL
    for k, (x0, xs, var, band, edge, wv, bar, title, tcol) in enumerate(panels):
        _title(f, x0, TS_Y - 12, title, tcol)
        ax = f.axes(x0, TS_Y, BOX_W, TS_H, xlim=(-6, 206), ylim=(-YL, YL),
                    xticks=[0, 50, 100, 150, 200], yticks=[-8, -4, 0, 4, 8],
                    xlabel="Time (s)", ylabel="Response" if k == 0 else None)
        sd = np.sqrt(var)
        ax.area(T, 2 * sd, -2 * sd, color=band)
        ax.plot(T, 2 * sd, color=edge, width=1.5)
        ax.plot(T, -2 * sd, color=edge, width=1.5)
        ax.hline(0)
        for i, x in enumerate(xs):
            ax.plot(T, x, color=[C.navy, C.blue, C.sky, C.deep, C.muted][i], width=2)
        ax.legend([("±2 SD band", {"kind": "area", "color": band})], at="north west",
                  pad=10, row=30, sample=40, size=24, inset=10)

        _title(f, x0, BAR_Y - 12, "Variance in three time windows", C.ink)
        bx = f.axes(x0, BAR_Y, BOX_W, BAR_H, xlim=(-6, 206), ylim=(0, 5), box=False,
                    ticks="out", xticks=[30, 100, 170],
                    xticklabels=["0–60 s", "70–130 s", "140–200 s"], yticks=[0, 2, 4],
                    ylabel="Variance", ylabel_gap=58)
        bx.bars([30, 100, 170], wv, width=60, color=bar)
        for (a, b), v in zip(WINDOWS, wv):
            bx.text((a + b) / 2, v, f"{v:.1f}", "south", dy=-6)
    return f.html()
