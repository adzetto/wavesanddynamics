"""The figures of the kit (kit.html): every Axes call once, on real models."""
import numpy as np
from scipy import stats

from fig import Fig, C, SERIES, log_ticks


def axes_demo():
    """Three densities with a legend, a shaded tail and a guide: the pgfplots box."""
    f = Fig(820, 218)
    ax = f.axes(96, 8, 700, 132, xlim=(20, 40), ylim=(0, 0.72), xticks=range(20, 41, 5),
                yticks=[0, 0.2, 0.4, 0.6], ytick_nd=1, xlabel="Unknown mean <m>μ</m> (MPa)",
                ylabel="Density", grid=True)
    x = np.linspace(20, 40, 600)
    prior, like = stats.norm(30, 2), stats.norm(32, 0.6)
    v = 1 / (1 / 4 + 1 / 0.36)
    post = stats.norm(v * (30 / 4 + 32 / 0.36), np.sqrt(v))
    xs = np.linspace(33, 40, 200)
    ax.area(xs, post.pdf(xs), color=C.mist)
    ax.plot(x, prior.pdf(x), color=SERIES[0], width=3, dash="10 6")
    ax.plot(x, like.pdf(x) * 0.95, color=SERIES[1], width=3)
    ax.plot(x, post.pdf(x), color=SERIES[2], width=4)
    ax.vline(33)
    ax.legend([("Prior", {"color": SERIES[0], "dash": "10 6"}), ("Likelihood", {"color": SERIES[1]}),
               ("Posterior", {"color": SERIES[2]})], at="north west")
    return f.html()


def marks_demo():
    """A step, stems, a histogram, intervals and a log axis, side by side."""
    f = Fig(820, 218)
    a1 = f.axes(70, 8, 200, 132, xlim=(0, 10), ylim=(0, 12), xticks=[0, 5, 10], yticks=[0, 5, 10],
                xlabel="Time (h)")
    t = np.cumsum(stats.expon(scale=1 / 1.1).ppf(np.linspace(0.05, 0.95, 11)))
    a1.step(np.r_[0, t], np.arange(0, len(t) + 1), color=C.navy, width=3)
    a2 = f.axes(330, 8, 200, 132, xlim=(-0.5, 8.5), ylim=(-0.6, 1.05), xticks=[0, 4, 8],
                yticks=[-0.5, 0, 0.5, 1], ytick_nd=1, xlabel="Lag")
    k = np.arange(0, 9)
    a2.hline(0, color=C.rule, dash=None)
    a2.stem(k, 0.8 ** k * np.cos(0.9 * k), color=C.blue)
    a3 = f.axes(590, 8, 210, 132, xlim=(0.1, 1000), ylim=(0, 1), xlog=True, xticks=log_ticks(-1, 3)[0],
                xticklabels=log_ticks(-1, 3)[1], yticks=[0, 0.5, 1], ytick_nd=1, xlabel="Return period")
    a3.interval(1, 100, 0.7, color=C.navy)
    a3.errorbar([3, 30, 300], [0.3, 0.45, 0.5], [0.2, 0.35, 0.38], [0.4, 0.55, 0.62], color=C.accent)
    return f.html()
