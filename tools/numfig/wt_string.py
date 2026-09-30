"""The fun table, "Vibrating string" (image3): a guitar string's standing wave.

Model: an ideal string fixed at both ends, the high E string of a guitar
(scale length 0.648 m, tuned to E4 = 329.63 Hz, tension 72 N). Its second
mode, w = A sin(2 pi x / L) cos(w2 t), inside its envelope, with the node
that stays still at midspan: a standing wave, which is (CHECK 2) the sum of
two waves A/2 sin(k x -/+ w2 t) running opposite ways between the ends.

Run: python tools/numfig/wt_string.py
"""
import numpy as np
from scipy.linalg import eigh_tridiagonal

import wt_lib

NAME = "string"

L, F1, T = 0.648, 329.63, 72.0               # m, Hz (E4), N
MU = T / (2 * L * F1) ** 2                   # kg/m, from the tuning: f1 = sqrt(T/mu) / 2L
C = np.sqrt(T / MU)                          # wave speed (m/s)
MODE = 2
SLOW = 1000.0

lines = []
say = lines.append
say("nf-wt-string: the fun table, 'Vibrating string' (image3)")
say("")
say("MODEL")
say(f"  ideal string, fixed ends: L = {L} m (guitar scale), tension T = {T} N, tuned to E4 f1 = {F1} Hz,")
say(f"  so mu = T / (2 L f1)^2 = {MU*1e3:.4f} g/m (a plain steel string of 0.25 mm: {7850*np.pi*0.000127**2*1e3:.4f} g/m);")
say(f"  wave speed c = sqrt(T/mu) = {C:.2f} m/s. Mode {MODE}: w = A sin(2 pi x/L) cos(w2 t),"
    f" f2 = {MODE*F1:.2f} Hz.")
say("")
say("CHECK 1: natural frequencies, finite differences (T w'' = -mu w^2 w, fixed ends) against n c / 2L")
for N in (50, 200, 800):
    h = L / N
    d = np.full(N - 1, 2 * T / (MU * h * h)); e = np.full(N - 2, -T / (MU * h * h))
    lam = eigh_tridiagonal(d, e, select="i", select_range=(0, 2))[0]
    fs = np.sqrt(lam) / (2 * np.pi)
    say(f"  {N:4d} intervals: " + ", ".join(f"f{n+1} = {fs[n]:.4f} Hz ({fs[n]/((n+1)*F1)-1:+.1e})" for n in range(3)))
say("  second order convergence to f_n = n f1, as the central difference must.")
say("")
say("CHECK 2: the standing wave is the sum of two travelling waves (d'Alembert)")
x = np.linspace(0, L, 401)
k = MODE * np.pi / L
w2 = 2 * np.pi * MODE * F1
worst = 0.0
for tt in np.linspace(0, 1 / (MODE * F1), 37):
    sw = np.sin(k * x) * np.cos(w2 * tt)
    tw = 0.5 * np.sin(k * x - w2 * tt) + 0.5 * np.sin(k * x + w2 * tt)
    worst = max(worst, np.abs(sw - tw).max())
say(f"  max |sin(kx) cos(wt) - [sin(kx - wt) + sin(kx + wt)]/2| over a period = {worst:.1e}")
say(f"  and each travelling wave moves at w/k = {w2/k:.2f} m/s = c: the dispersion relation of the string.")
say("")
say("DRAWING")
say(f"  string {L} m = 800 units; amplitude drawn 112 units (a real amplitude of 1.4 mm drawn x 65).")
say(f"  time slowed {SLOW:.0f} x: mode {MODE} ({MODE*F1:.1f} Hz) shows at {MODE*F1/SLOW:.3f} Hz,"
    f" a seamless loop of one period, {SLOW/(MODE*F1):.3f} s.")
wt_lib.write_check(NAME, lines)

DATA = {"n": MODE, "f": MODE * F1 / SLOW}

JS = r"""
const XA = 100, XB = 900, YM = 200, A = 112, NP = 161;
const POSTER_T = 0;                                         // t = 0 (and the still): a crest, the string at full swing
const K = DATA.n * Math.PI;
function wave(fn, alpha, o) {
  const pts = [];
  for (let i = 0; i < NP; i++) { const u = i / (NP - 1); pts.push([lerp(XA, XB, u), YM - A * fn(u)]); }
  line(pts, { ...o, alpha });
}
function draw() {
  const ph = 2 * Math.PI * DATA.f * t;
  const aS = 1, aW = 1;
  // the ends: fixed, hatched as TikZ draws a wall
  big(XA, YM, 4, () => fixedEnd(0, 0, { h: 62, dir: 1, alpha: aS }));
  big(XB, YM, 4, () => fixedEnd(0, 0, { h: 62, dir: -1, alpha: aS }));
  // the rest line and the envelope, dashed
  line([[XA, YM], [XB, YM]], { color: C.rule, width: SW.thin, alpha: aS });
  for (const s of [-1, 1]) wave(u => s * Math.sin(K * u), aW, { color: C.guide, width: SW.guide, dash: DASH });
  // the standing wave: the string itself
  const pts = [];
  for (let i = 0; i < NP; i++) { const u = i / (NP - 1); pts.push([lerp(XA, XB, u), YM - A * Math.sin(K * u) * Math.cos(ph)]); }
  line(pts, { color: C.blue, width: SW.data });
  // the node: still while everything else moves
  for (let j = 1; j < DATA.n; j++) dot(lerp(XA, XB, j / DATA.n), YM, 13, { color: C.ink, fill: '#fff', width: 5, alpha: aW });
}
boot();
"""

TITLE = "Vibrating string"
ARIA = ("A guitar string fixed at both ends vibrates in its second mode: a standing wave "
        "swinging inside its dashed envelope, with a still node at the middle.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
