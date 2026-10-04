"""Slide 12: the two checks of his picture, each a model held against data.

Normal Q-Q plot: his 32 illustrative cylinder tests, the same 32 values
slide 13's histogram shows (s013 imports TESTS from here). They are a seeded
pseudo-random draw from N(32.1, 3.1^2) MPa (numpy default_rng, seed 12, the
slide's number: fixed, so the draw is the same on every run), rescaled to his
reconstructed sample's statistics exactly (his notes: n = 32, sample mean
32.1 MPa, sample SD 3.1 MPa), which moves no point off its place in the
pattern. A Q-Q plot exists to show a real sample's scatter about the line, so
the draw is random, not quantile-even like fig.sample. The ordered strengths
are plotted against the standard normal quantiles at Blom's plotting
positions (i - 3/8)/(n + 1/4); the line is the fitted normal model, mean +
SD x quantile = 32.1 + 3.1 z MPa.

Regression residuals: the survey behind his trip regression (slide 22; his
notes: a simulated survey, least-squares fit about 1.03 + 1.80 x persons).
30 households, 5 of each size from 1 to 6 persons, with daily trips =
1.03 + 1.80 x persons + e, e ~ N(0, 1) trips (the scatter of his residual
picture, about one trip). The e are deterministic Halton draws (fig.sample,
skip 34, the draw whose least-squares line is his, 1.03 + 1.80 x persons).
Plotted: observed minus fitted against the fitted trips, around zero."""
import numpy as np
from scipy import stats

from fig import Fig, C, draw, fade, pop, sample, seq

# Fit: the Q-Q plot's points arrive from the lowest quantile up, then the
# fitted line draws through them; Check: the residuals arrive around zero
ANIM = {"length": 6.2}

# his 32 tests: a seeded random draw, rescaled to his mean and SD
SEED, N = 12, 32
RAW = np.random.default_rng(SEED).normal(32.1, 3.1, N)
TESTS = 32.1 + 3.1 * (RAW - RAW.mean()) / RAW.std(ddof=1)
FIT = stats.norm(TESTS.mean(), TESTS.std(ddof=1))
assert np.isclose(FIT.mean(), 32.1) and np.isclose(FIT.std(), 3.1)
Z = stats.norm.ppf((np.arange(1, N + 1) - 0.375) / (N + 0.25))
OBS = np.sort(TESTS)
assert 24 < OBS[0] and OBS[-1] < 40                   # inside the axis

# the trip survey and its least-squares line
PERSONS = np.repeat(np.arange(1, 7), 5).astype(float)
TRIPS = 1.03 + 1.80 * PERSONS + sample(30, stats.norm(0, 1), skip=34)
B1, B0 = np.polyfit(PERSONS, TRIPS, 1)
assert (round(B0, 2), round(B1, 2)) == (1.03, 1.80)
FITTED = B0 + B1 * PERSONS
RESID = TRIPS - FITTED

TITLE = {"size": 30, "weight": 700}


def checks():
    f = Fig(976, 572)
    # Normal Q-Q plot
    qa = f.axes(112, 60, 344, 404, xlim=(-2.5, 2.5), ylim=(24, 40),
                xticks=[-2, -1, 0, 1, 2], yticks=[25, 30, 35, 40],
                xlabel="Theoretical normal quantiles", ylabel="Observed strength (MPa)", anim=fade(.7, .4))
    z = np.array([-2.5, 2.5])
    qa.plot(z, FIT.mean() + FIT.std() * z, color=C.accent, width=3, anim=draw(2.1, .55))
    qa.scatter(Z, OBS, r=6.5, color=C.navy, anim=seq(1.0, .033, visual=.25))
    f.text(112 + 172, 60 - 16, "Normal Q–Q plot", "south", **TITLE, anim=pop(.8))
    # Regression residuals
    ra = f.axes(616, 60, 344, 404, xlim=(2, 13), ylim=(-3, 3),
                xticks=[4, 6, 8, 10, 12], yticks=[-2, -1, 0, 1, 2],
                xlabel="Fitted trips", ylabel="Observed minus fitted", anim=fade(3.0, .4))
    ra.hline(0, color=C.accent, width=3, dash=None, anim=draw(3.25, .45))
    ra.scatter(FITTED, RESID, r=6.5, color=C.navy, anim=seq(3.6, .03, visual=.25))
    f.text(616 + 172, 60 - 16, "Regression residuals", "south", **TITLE, anim=pop(3.1))
    return f.html()
