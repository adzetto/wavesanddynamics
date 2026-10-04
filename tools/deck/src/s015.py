"""Slide 15: the two frameworks on one example, his concrete strength: known
sigma = 3 MPa and n = 25 tests, so a sample mean has standard error
3/sqrt(25) = 0.6 MPa.

repeated  FREQUENTIST. The population mean is fixed at 32 MPa. 25 repeated
          samples of 25 tests: their means are 25 deterministic draws from the
          sampling distribution N(32, 0.6^2) (fig.sample, skip 45), each with
          its 95% interval xbar +- 1.96 x 0.6 = xbar +- 1.176 MPa. Two of the
          25 miss the fixed true mean and are drawn in the accent: as his notes
          say, a finite set of intervals need not cover exactly 95%.
update    BAYESIAN. Prior mu ~ N(30, 2^2); the data, xbar = 32 MPa with
          v_D = 3^2/25 = 0.36 MPa^2, give the likelihood of mu, drawn scaled
          to unit area (the N(32, 0.36) density); the posterior is
          N(31.83, 0.575^2), the numbers of slides 18 and 19.
The same axes box in both, so the pair reads as one figure; his long y label
of the second is set on two lines to stay within its axis."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop, sample
from s013 import legend

# The frequentist column, then the Bayesian (DECK_BRIEF.md "Animated slides";
# the blocks' moments are in s015.html): the fixed true mean, then the 25
# repeated intervals one by one from the first sample up; the prior, the
# likelihood and the posterior, each with its legend entry.
ANIM = {"length": 9.9}

SIGMA, N, MU = 3.0, 25, 32.0
SE = SIGMA / np.sqrt(N)
HALF = stats.norm.ppf(0.975) * SE
assert (SE, round(HALF, 3)) == (0.6, 1.176)
MEANS = sample(25, stats.norm(MU, SE), skip=45)
MISS = np.abs(MEANS - MU) > HALF
assert MISS.sum() == 2

M0, V0, VD = 30.0, 2.0 ** 2, SIGMA ** 2 / N
VP = 1 / (1 / V0 + 1 / VD)
MP = VP * (M0 / V0 + MU / VD)
PRIOR, LIKE, POST = stats.norm(M0, np.sqrt(V0)), stats.norm(MU, np.sqrt(VD)), stats.norm(MP, np.sqrt(VP))
assert (round(MP, 2), round(np.sqrt(VP), 3)) == (31.83, 0.575)

W, H = 832, 394
BOX = (160, 46, 652, 258)            # the axes box, the same in both


def repeated():
    f = Fig(W, H)
    ax = f.axes(*BOX, xlim=(29, 35), ylim=(0, 26), xticks=[30, 31, 32, 33, 34],
                yticks=[1, 5, 10, 15, 20, 25], xlabel="Mean strength (MPa)",
                ylabel="Repeated sample", anim=fade(1.1, .4))
    ax.vline(MU, color=C.blue, width=2.5, dash="8 6", anim=draw(1.5, .4))
    for i, (m, miss) in enumerate(zip(MEANS, MISS), start=1):
        f.line(ax._pts([m - HALF, m + HALF], [i, i]), stroke=C.accent if miss else C.navy,
               width=4.5, cap="butt", clip=ax.clip, anim=draw(1.925 + .075 * i, .25))
    X, _ = ax.P(MU, 0)
    f.text(X, BOX[1] - 12, "Fixed true mean", "south", color=C.blue, anim=pop(1.6))
    return f.html()


def update():
    f = Fig(W, H)
    ax = f.axes(*BOX, xlim=(26, 36), ylim=(0, 0.8), xticks=[26, 28, 30, 32, 34, 36],
                yticks=[0, 0.2, 0.4, 0.6], ytick_nd=1, xlabel="Unknown mean <m>μ</m> (MPa)",
                ylabel='<span style="display:block;text-align:center">Density / <br>scaled likelihood</span>',
                ylabel_gap=104, anim=fade(5.8, .4))
    x = np.linspace(26, 36, 1000)
    ax.plot(x, PRIOR.pdf(x), color=C.navy, width=3, dash="10 6", anim=draw(6.2, .6))
    ax.plot(x, LIKE.pdf(x), color=C.accent, width=3.5, anim=draw(6.9, .6))
    ax.plot(x, POST.pdf(x), color=C.blue, width=4.5, anim=draw(7.6, .7))
    legend(ax, [("Prior", {"color": C.navy, "width": 3, "dash": "10 6"}),
                ("Likelihood (scaled)", {"color": C.accent, "width": 3.5}),
                ("Posterior", {"color": C.blue, "width": 4.5})], at="north west",
           size=24, row=34, pad=14, sample=40, gap=10,
           anim=[pop(6.2), pop(6.3), pop(7.0), pop(7.7)])
    return f.html()
