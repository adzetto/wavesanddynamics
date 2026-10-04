"""Slide 49: Welch's method on slide 48's record (his notes: the same 100 s).

The record x (N = 2000, dt = 0.05 s) is cut into segments of L = 256 samples
(12.8 s) with 50% overlap, a step of 128 samples, so K = (2000 - 256)//128 + 1
= 14 segments. Each segment has its mean removed, is multiplied by the Hann
window w[n] = sin^2(pi n / 256) and gives the one-sided periodogram
P_k(f) = 2 |sum w[n] x[n] exp(-i 2 pi f n dt)|^2 / (fs sum w^2) at f = j/12.8 s,
a step of 0.078 Hz (his 0.08). Their mean is the Welch average P_W; the script
checks that it equals scipy.signal.welch on the whole record.

1  the first 40 s of the record (light), the first four tapered segments
   w x in the series colours, and their Hann windows above them, one per row;
2  the periodograms of those four segments;
3  slide 48's single periodogram (light), the Welch average of all 14 (navy)
   and the model's spectrum G(f) (dashed)."""
import numpy as np
from scipy import signal

from fig import Fig, C, SERIES, draw, fade, pop

# Welch's three steps in order (DECK_BRIEF.md "Animated slides"; the panels'
# moments are in s049.html): the record, then each window and the segment it
# tapers; the four periodograms one by one; then the single periodogram, the
# true spectrum and the Welch average over them, each with its key.
ANIM = {"length": 9.8}
from s048 import X, DT, G, F as F1, P as P1, log_axis

FS, L, STEP = 20.0, 256, 128
K = (len(X) - L) // STEP + 1
WIN = signal.get_window("hann", L)
SEGS = [np.arange(k * STEP, k * STEP + L) for k in range(K)]
FW, PK = None, []
for idx in SEGS:
    FW, p = signal.periodogram(X[idx], fs=FS, window=WIN, detrend="constant", scaling="density")
    PK.append(p)
PW = np.mean(PK, axis=0)

assert K == 14 and L * DT == 12.8 and round(1 / (L * DT), 2) == 0.08
_f, _pw = signal.welch(X, fs=FS, window="hann", nperseg=L, noverlap=L - STEP)
assert np.allclose(_f, FW) and np.allclose(_pw, PW)

YLOG = (1e-6, 10 ** 1.3)
FT = np.linspace(0, 10, 2001)
W = 544
H_ROW = 408                                   # the figure row, as tall for all three
TOP = 92                                      # the boxes' top, under two title lines


def _title(f, x, n, words, anim=None):
    """His numbered title over its box: the number hangs beside the first
    line (a title of two lines is set at 1.3; the number takes that line's
    place, half-leading included)."""
    y = TOP - 10
    lines = words.count("<br>") + 1
    ny = y - (lines - 1) * 28 * 1.3 - (4.2 if lines > 1 else 0)
    f.text(x, ny, n, "south west", size=28, color=C.navy, font="serif", weight=600, anim=anim)
    f.text(x + 28, y, words, "south west", size=28, color=C.navy, font="serif", weight=600, anim=anim)


def segments():
    f = Fig(W, H_ROW)
    _title(f, 24, "1", "Cut into overlapping segments, <br>taper each with a window", anim=pop(.3))
    ax = f.axes(24, TOP, 506, 226, xlim=(0, 40), ylim=(-3.6, 11.8), box=False, ticks="out",
                xticks=range(0, 41, 10), xlabel="Time (s)", anim=fade(.4, .4))
    t = np.arange(len(X)) * DT
    keep = t <= 40
    ax.plot(t[keep], X[keep], color=C.steel2, width=1.1, anim=draw(.7, .9))
    for k in range(4):
        idx = SEGS[k]
        ax.plot(t[idx], WIN * (X[idx] - X[idx].mean()), color=SERIES[k], width=1.5,
                anim=draw(1.8 + .35 * k, .5))
    for k in range(4):                        # the windows, one row each, over the record
        idx = SEGS[k]
        base = 4.6 + 1.55 * k
        ax.plot(t[idx], base + 2.2 * WIN, color=SERIES[k], width=3, anim=draw(1.7 + .35 * k, .4))
    return f.html()


def periodograms():
    f = Fig(W, H_ROW)
    _title(f, 104, "2", "Periodogram of each <br>segment (still noisy)", anim=pop(3.4))
    yt, yl = log_axis(-6, 1)
    ax = f.axes(104, TOP, 426, 226, xlim=(-0.3, 10.3), ylim=YLOG, ylog=True,
                xticks=range(0, 11, 2), yticks=yt, yticklabels=yl, xlabel="Frequency (Hz)",
                ylabel="PSD", ylabel_gap=92, anim=fade(3.5, .4))
    for k in range(4):
        ax.plot(FW[1:], PK[k][1:], color=SERIES[k], width=2, anim=draw(3.8 + .25 * k, .7))
    return f.html()


def average():
    """Panel 3, with his legend as a key under the panel."""
    f = Fig(W, 560)
    _title(f, 76, "3", "Average them: smooth estimate", anim=pop(5.4))
    yt, yl = log_axis(-6, 1)
    ax = f.axes(76, TOP, 454, 226, xlim=(-0.3, 10.3), ylim=YLOG, ylog=True,
                xticks=range(0, 11, 2), yticks=yt, yticklabels=yl, xlabel="Frequency (Hz)",
                anim=fade(5.5, .4))
    ax.plot(F1, P1, color=C.mist, width=1.1, anim=draw(5.8, .7))
    ax.plot(FT, G(FT), color=C.accent, width=3, dash="12 7", anim=draw(6.4, .6))
    ax.plot(FW, PW, color=C.navy, width=4, anim=draw(7.0, .8))
    rows = [("single periodogram", dict(stroke=C.mist, width=2.5)),
            ("Welch average of 14 segments", dict(stroke=C.navy, width=4)),
            ("true spectrum", dict(stroke=C.accent, width=3, dash="12 7"))]
    y0 = H_ROW + 24
    for i, ((words, st), at) in enumerate(zip(rows, (5.8, 7.0, 6.4))):   # each key with its curve
        cy = y0 + 17 + i * 40
        f.line([(76, cy), (76 + 52, cy)], cap="butt", anim=pop(at), **st)
        f.text(76 + 66, cy, words, "west", size=26, anim=pop(at))
    return f.html()
