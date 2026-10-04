"""Slide 56: the weigh station of slide 55, lambda = 2 trucks per hour,
answering his two questions.

counts  the number of trucks in a 2-hour window: Poisson with mean
        lambda t = 4, P(N = k) = e^(-4) 4^k / k!, k = 0 to 12. His numbers:
        P(0) = 1.8%, P(2) = 14.7%, P(4) = 19.5%, P(6) = 10.4%, P(8) = 3.0%,
        P(N >= 8) = 5.1%; the bars add up to 1.
gaps    the wait to the next truck: exponential with rate lambda = 2 per
        hour, f(w) = 2 e^(-2w), mean 1/lambda = 0.5 h, P(wait > 1 h) = e^(-2)
        = 13.5% (shaded). The histogram is 4000 simulated waits, a
        deterministic draw from that exponential (fig.sample), as densities
        per hour in bins of 0.1 h."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, grow, pop, sample
from s053 import tw

# Counts, then gaps (DECK_BRIEF.md "Animated slides"; the blocks' moments
# are in s056.html): the Poisson bars rise from 0 trucks up with their
# labels; then the simulated waits rise, the exponential model draws over
# them, its mean is marked and the wait beyond 1 h is shaded.
ANIM = {"length": 7.9}

LAM, T = 2.0, 2.0
POIS = stats.poisson(LAM * T)
K = np.arange(0, 13)
PMF = POIS.pmf(K)
LABELLED = (0, 2, 4, 6, 8)
assert [f"{100 * PMF[k]:.1f}%" for k in LABELLED] == ["1.8%", "14.7%", "19.5%", "10.4%", "3.0%"]
assert round(100 * POIS.sf(7), 1) == 5.1 and abs(POIS.pmf(np.arange(0, 60)).sum() - 1) < 1e-12
EXP = stats.expon(scale=1 / LAM)
assert EXP.mean() == 0.5 and round(100 * EXP.sf(1.0), 1) == 13.5 == round(100 * np.exp(-2), 1)
N = 4000

# his formulas: the caret he typed stays in the text; the exponent is set as one
EXP_M = 'e<span class="mk">^</span><sup>(−λw)</sup>'


def counts():
    f = Fig(832, 440)
    ax = f.axes(112, 8, 700, 334, xlim=(-0.7, 12.7), ylim=(0, 0.226), xticks=K,
                yticks=[0, 0.05, 0.1, 0.15, 0.2], ticks="out",
                xlabel="Number of trucks in a 2-hour window", ylabel="Probability", anim=fade(.5, .4))
    for k, p in zip(K, PMF):
        ax.bars([k], [p], width=0.64, color=C.amber if k == LAM * T else C.navy,
                anim=grow(.9 + .07 * k, .4))
    for k in LABELLED:
        ax.text(k, PMF[k] + 0.0035, f"{100 * PMF[k]:.1f}%", "south", size=24, anim=pop(1.2 + .07 * k))
        # clear of the next bar: half the label is narrower than a bar step less half a bar
        assert tw(f"{100 * PMF[k]:.1f}%", 24) / 2 < (1 - 0.32) * 700 / 13.4
    return f.html()


def gaps():
    f = Fig(832, 440)
    ax = f.axes(112, 8, 700, 334, xlim=(-0.12, 3.12), ylim=(0, 2.14),
                xticks=[0, 0.5, 1, 1.5, 2, 2.5, 3], yticks=[0, 0.5, 1, 1.5, 2], ticks="out",
                xlabel="Waiting time to the next truck (h)",
                ylabel="Probability density (per h)", anim=fade(3.1, .4))
    edges = np.round(np.arange(0, 3.0001, 0.1), 10)
    n, _ = np.histogram(sample(N, EXP), edges)
    ax.bars((edges[:-1] + edges[1:]) / 2, n / (N * 0.1), width=0.1 * 0.92, color=C.steel2,
            anim=grow(3.4, .4, .03))
    w = np.linspace(1, 3, 300)
    ax.area(w, EXP.pdf(w), color=C.amber, opacity=0.6, anim=fade(5.8, .4))
    ax.vline(0.5, color=C.navy, width=2.5, dash="10 6", anim=draw(5.2, .35))
    w = np.linspace(0, 3, 600)
    ax.plot(w, EXP.pdf(w), color=C.blue, width=4, anim=draw(4.4, .7))
    ax.text(0.57, 1.02, "mean wait <m>1/λ = 0.5</m> h", "west", size=26, color=C.navy, anim=pop(5.4))
    ax.text(1.22, 0.56, '<m>P</m>(wait &gt; 1 h) = <m>e<span class="mk">^</span><sup>(−2)</sup></m> = 13.5%',
            "west", size=28, color=C.accent, anim=pop(6.0))
    ax.legend([("waiting times, simulated", {"kind": "area", "color": C.steel2}),
               (f"model: <m>λ{EXP_M}</m>", {"color": C.blue, "width": 4})],
              at="north east", size=26, row=38, anim=[pop(3.4), pop(3.4), pop(4.4)])
    return f.html()
