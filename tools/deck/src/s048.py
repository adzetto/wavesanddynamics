"""Slide 48: one record, its FFT and its periodogram (his notes).

The model: a resonance at 4 Hz sampled at 20 Hz, the AR(2) process
x[n] = a1 x[n-1] + a2 x[n-2] + e[n] with poles r exp(+-i 2 pi 4 dt), r = 0.985,
dt = 0.05 s, so a1 = 2 r cos(0.4 pi), a2 = -r^2, and the innovation variance set
so that Var x = 1. Its one-sided spectrum is
G(f) = 2 s_e^2 dt / |1 - a1 z - a2 z^2|^2, z = exp(-i 2 pi f dt):
2.9e-3 at 0 Hz, 6.6 at 4 Hz and 8.0e-4 at 10 Hz, his dashed curve.

The record: N = 2000 samples (100 s at 20 Hz), started in the stationary law
and run with numpy's PCG64 (seed below), the same every run. The periodogram
is one FFT of the whole record, one-sided, in x^2 per Hz:
P(f_k) = 2 (dt/N) |X(f_k)|^2 at f_k = k/(N dt), a step of 0.01 Hz.
Slide 49 takes the same record from here."""
import numpy as np

from fig import Fig, C

FS, DT, N = 20.0, 0.05, 2000
R_POLE, F_RES = 0.985, 4.0
_w0 = 2 * np.pi * F_RES * DT
A1, A2 = 2 * R_POLE * np.cos(_w0), -R_POLE ** 2
SE2 = (1 + A2) * ((1 - A2) ** 2 - A1 ** 2) / (1 - A2)      # Var x = 1


def G(f):
    """The model's one-sided spectrum, x^2 per Hz."""
    z = np.exp(-2j * np.pi * np.asarray(f, float) * DT)
    return 2 * SE2 * DT / np.abs(1 - A1 * z - A2 * z * z) ** 2


def record(seed=4801):
    rng = np.random.default_rng(seed)
    g1 = A1 / (1 - A2)                                        # lag-1 correlation
    x = np.empty(N)
    x[:2] = np.linalg.cholesky([[1, g1], [g1, 1]]) @ rng.standard_normal(2)
    e = rng.standard_normal(N) * np.sqrt(SE2)
    for k in range(2, N):
        x[k] = A1 * x[k - 1] + A2 * x[k - 2] + e[k]
    return np.arange(N) * DT, x


T, X = record()
F = np.fft.rfftfreq(N, DT)[1:-1]                              # 0.01 to 9.99 Hz
P = 2 * DT / N * np.abs(np.fft.rfft(X)[1:-1]) ** 2
FT = np.linspace(0, 10, 2001)

assert N * DT == 100 and FS * DT == 1
assert round(float(G(0)), 4) == 0.0029 and round(float(G(4)), 1) == 6.6
assert round(float(G(10)), 5) == 0.00080
assert abs(np.trapezoid(G(np.linspace(0, 10, 200001)), dx=10 / 200000) - 1) < 1e-3   # Var x = 1


SUPS = dict(zip("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹"))


def log_axis(lo, hi, every=2):
    """Decade ticks from 10^lo to 10^hi, labelled every `every` decades, set
    as maths (10 with his superscript characters) so the exponent is read at
    the label's size (fig.log_ticks' <sup> would be read at 20 px)."""
    ex = range(lo, hi + 1)
    return ([10.0 ** e for e in ex],
            ["<m>10" + "".join(SUPS[c] for c in str(e)) + "</m>" if (e - lo) % every == 0 else ""
             for e in ex])


W, H = 1120, 426
REC = (80, 50, 330, 292)
PER = (566, 50, 540, 292)
YLOG = (1e-6, 10 ** 1.3)


def estimate():
    f = Fig(W, H)
    x, y, w, h = REC
    f.text(x, y - 12, "Record: 100 s at 20 Hz (<m>N = 2000</m>)", "south west", size=28,
           color=C.navy, font="serif", weight=600)
    ax = f.axes(x, y, w, h, xlim=(-2, 102), ylim=(-3.9, 3.9), xticks=range(0, 101, 20),
                yticks=[-3, 0, 3], xlabel="Time (s)", ylabel="<m>x</m>", ylabel_gap=62)
    ax.plot(T, X, color=C.navy, width=1.1)

    x, y, w, h = PER
    f.text(x, y - 12, "One periodogram: right on average, jagged", "south west", size=28,
           color=C.navy, font="serif", weight=600)
    yt, yl = log_axis(-6, 1)
    ax = f.axes(x, y, w, h, xlim=(-0.3, 10.3), ylim=YLOG, ylog=True, xticks=range(0, 11, 2),
                yticks=yt, yticklabels=yl, xlabel="Frequency (Hz)",
                ylabel="PSD (<m>x²</m> per Hz)", ylabel_gap=102)
    ax.plot(F, P, color=C.mist, width=1.2)
    ax.plot(FT, G(FT), color=C.accent, width=3, dash="12 7")
    # his two legend entries, set beside their curves
    ax.text(3.62, 10 ** 0.62, "True spectrum", "east", size=26, color=C.accent)
    ax.text(5.05, 10 ** -1.15, "Periodogram (one FFT <br>of the whole record)", "south west",
            size=24, color="var(--sky-ink)")
    return f.html()
