"""Slide 46: the normalized autocorrelation of his notes, a valid damped-cosine
covariance rho(tau) = exp(-0.7 |tau|) cos(2 pi 2 tau), with its decay envelope
exp(-0.7 tau) (dashed), for lags 0 to 5 s. rho(0) = 1; the peaks repeat every
0.5 s (a 2 Hz rhythm) and shrink by exp(-0.35) = 0.70 each time; the deepest
trough, at tau = 0.25 s, is -exp(-0.175) = -0.84."""
import numpy as np

from fig import Fig, C, draw, fade, pop

# What to look for, then the autocorrelation that shows it (DECK_BRIEF.md
# "Animated slides"; the blocks' moments are in s046.html): the curve draws
# out lag by lag, then the envelope it decays inside.
ANIM = {"length": 5.5}

A, F0 = 0.7, 2.0                                  # 1/s, Hz


def rho(tau):
    return np.exp(-A * np.abs(tau)) * np.cos(2 * np.pi * F0 * tau)


TAU = np.linspace(0, 5, 2001)
assert rho(0.0) == 1.0
assert round(float(rho(0.25)), 2) == -0.84 and round(float(rho(0.5)), 2) == 0.70
assert abs(TAU[np.argmin(rho(TAU))] - 0.25) < 0.01


def acf():
    f = Fig(976, 650)
    ax = f.axes(136, 14, 822, 500, xlim=(-0.12, 5.12), ylim=(-1, 1.12),
                xticks=range(0, 6), yticks=[-1, -0.5, 0, 0.5, 1],
                xlabel="Lag <m>τ</m> (s)", ylabel="Normalized autocorrelation", grid=True,
                anim=fade(.9, .4))
    ax.hline(0, color=C.guide, dash=None, width=1.5, anim=fade(1.2, .3))
    ax.plot(TAU, np.exp(-A * TAU), color=C.accent, width=3, dash="12 8", anim=draw(3.0, .8))
    ax.plot(TAU, rho(TAU), color=C.navy, width=4, anim=draw(1.3, 1.4))
    ax.legend([("Decay envelope", {"color": C.accent, "dash": "12 8", "width": 3})],
              at="north east", size=28, row=40, pad=16, sample=56, inset=18, anim=pop(3.0))
    return f.html()
