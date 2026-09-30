"""The fun table, "Noncontact vibration sensing" (image9): a laser Doppler vibrometer.

Model: a He-Ne laser (632.8 nm) watches a point near the tip of a steel
cantilever vibrating in its first bending mode (Euler-Bernoulli, exact mode
shape and frequency). The light returned from the moving surface is mixed
with the reference beam; the detector sees the fringe signal
    I(t) = (1 + cos(4 pi u(t) / lambda)) / 2,
one fringe for every half wavelength the surface moves, so the fringes
come fastest where the surface moves fastest: their rate, 2 |v| / lambda,
is the Doppler shift of the returned light. The strip under the beam is
that signal over the last period, the newest at the right.

Run: python tools/numfig/wt_laser.py
"""
import numpy as np
from scipy.linalg import eigh

import wt_lib

NAME = "laser"

LAMBDA = 632.8e-9
LB, BW, TH = 0.150, 0.020, 0.002                    # cantilever length, width, thickness (m)
E, RHO = 210e9, 7850.0
EI, MA = E * BW * TH ** 3 / 12, RHO * BW * TH
BETA1 = 1.875104068711961
SIG1 = (np.cosh(BETA1) + np.cos(BETA1)) / (np.sinh(BETA1) + np.sin(BETA1))
F1 = BETA1 ** 2 / (2 * np.pi * LB ** 2) * np.sqrt(EI / MA)
XI_SPOT = 0.82                                       # the laser spot, as a share of the length from the root
U_TIP = 2.2e-6                                       # tip amplitude (m)
F_SHOW = 0.5                                         # the mode shown at 0.5 Hz


def phi(xi):
    b = BETA1 * xi
    return np.cosh(b) - np.cos(b) - SIG1 * (np.sinh(b) - np.sin(b))


U_SPOT = U_TIP * phi(XI_SPOT) / phi(1.0)

lines = []
say = lines.append
say("nf-wt-laser: the fun table, 'Noncontact vibration sensing' (image9)")
say("")
say("MODEL")
say(f"  steel cantilever {LB*1e3:.0f} x {BW*1e3:.0f} x {TH*1e3:.0f} mm, E = {E/1e9:.0f} GPa, rho = {RHO:.0f} kg/m^3:"
    f" first mode f1 = beta1^2 / (2 pi L^2) sqrt(EI/m) = {F1:.3f} Hz")
say(f"  tip amplitude {U_TIP*1e6:.1f} um; laser spot at {XI_SPOT:.2f} L, where the mode moves {U_SPOT*1e6:.3f} um")
say(f"  He-Ne {LAMBDA*1e9:.1f} nm: {4*U_SPOT/LAMBDA:.2f} fringes per half period; peak Doppler shift"
    f" 2 v_max / lambda = {2*2*np.pi*F1*U_SPOT/LAMBDA/1e3:.3f} kHz")
say("")
say("CHECK 1: f1 of the cantilever, closed form against Hermite FE (clamped root, free tip)")
for ne in (4, 16, 64):
    K, M = wt_lib.hermite_beam(ne, LB, EI, MA)
    k = list(range(2, K.shape[0]))
    lam, vec = eigh(K[np.ix_(k, k)], M[np.ix_(k, k)])
    f = np.sqrt(lam[0]) / (2 * np.pi)
    w = vec[0::2, 0]; w = w / w[-1]
    xi = np.linspace(0, 1, ne + 1)[1:]
    say(f"  {ne:3d} elements: f1 = {f:.5f} Hz ({f/F1-1:+.1e}); nodal mode shape off the closed form by"
        f" {np.abs(w - phi(xi)/phi(1.0)).max():.1e}")
say("")
say("CHECK 2: the drawn fringe signal carries the velocity: demodulate it and compare")
fs = 2e6
tt = np.arange(0, 3 / F1, 1 / fs)
u = U_SPOT * np.sin(2 * np.pi * F1 * tt)
phase = 4 * np.pi * u / LAMBDA
I_sig = np.cos(phase)                                  # the AC part of the detector signal
Q_sig = np.sin(phase)                                  # its quadrature (a real LDV makes it optically)
ph_rec = np.unwrap(np.arctan2(Q_sig, I_sig))
v_rec = np.gradient(ph_rec, tt) * LAMBDA / (4 * np.pi)
v_true = 2 * np.pi * F1 * U_SPOT * np.cos(2 * np.pi * F1 * tt)
inner = slice(10, -10)
say(f"  velocity from the fringe phase: max error {np.abs(v_rec-v_true)[inner].max()/np.abs(v_true).max():.1e}"
    f" of v_max = {np.abs(v_true).max()*1e3:.3f} mm/s")
zc = np.count_nonzero(np.diff(np.sign(I_sig[(tt >= 0.25 / F1) & (tt < 0.75 / F1)])) != 0)
say(f"  zero crossings of the fringe signal in one half period: {zc} = 2 x {zc/2:.0f} fringes; 4 U / lambda ="
    f" {4*U_SPOT/LAMBDA:.2f}")
say("")
say("DRAWING")
say(f"  cantilever {LB*1e3:.0f} mm = 300 units; its motion drawn x {40/(U_TIP)/2000:.0f} (tip {U_TIP*1e6:.1f} um = 40 units)")
say(f"  time slowed {F1/F_SHOW:.1f} x: the mode ({F1:.2f} Hz) shows at {F_SHOW} Hz; the strip holds one period.")
wt_lib.write_check(NAME, lines)

DATA = {"f": F_SHOW, "xi": XI_SPOT, "beta": BETA1, "sig": SIG1, "phitip": float(phi(1.0)),
        "ph": 4 * np.pi * U_SPOT / LAMBDA}

JS = r"""
const T0 = -.25 / DATA.f, POSTER_T = 0;                  // t = 0 (and the still): the tip at full swing
const BX = 842, BY0 = 356, BL = 300, TIP = 40;          // cantilever root (x, y), length, tip swing
const HX0 = 42, HX1 = 212, HY = 150;                     // the vibrometer head, the beam's height
const SX0 = 42, SX1 = 700, SY = 272, SH = 64;            // the fringe strip
const phi = xi => { const b = DATA.beta * xi; return Math.cosh(b) - Math.cos(b) - DATA.sig * (Math.sinh(b) - Math.sin(b)); };
const NB = 41, SHAPE = []; for (let i = 0; i < NB; i++) SHAPE.push(phi(i / (NB - 1)) / DATA.phitip);
const w = 2 * Math.PI * DATA.f;
const NS = 240, ST = new Uint8ClampedArray(NS);
function draw() {
  const tt = t - T0, aS = 1;
  const q = Math.sin(w * tt);                              // modal coordinate: tip at q TIP
  // the cantilever, clamped in the ground, bending in its first mode
  ground(BX - 70, BX + 70, BY0, { alpha: aS });
  const pts = SHAPE.map((s, i) => [BX + TIP * q * s, BY0 - BL * i / (NB - 1)]);
  line(pts, { color: C.ink, width: SW.struct + 3 });
  // the spot, where the beam meets the surface (the beam leaves the head level)
  const ys = BY0 - BL * DATA.xi, xs = BX + TIP * q * phi(DATA.xi) / DATA.phitip - 6;
  const yb = HY + 40;
  line([[HX1, yb], [xs, yb]], { color: C.accent, width: 7, alpha: 1 });
  dot(xs, yb, 10, { color: C.accent, fill: C.accent });
  // the head: a navy box, its lens
  line([[HX0, HY], [HX1, HY], [HX1, HY + 80], [HX0, HY + 80]], { color: C.navy, width: 2, fill: C.navy, close: true, alpha: aS });
  dot(HX1, yb, 13, { color: C.navy, fill: '#fff', width: 5, alpha: aS });
  // the fringe signal over the last period: I = (1 + cos(4 pi u / lambda)) / 2, newest at the right
  const a = 1;
  if (a > 0) {
    ctx.save(); ctx.globalAlpha *= a;
    const dw = (SX1 - SX0) / NS;
    for (let i = 0; i < NS; i++) {
      const s = tt - (1 - (i + .5) / NS) / DATA.f;          // the time this column shows
      const I = .5 * (1 + Math.cos(DATA.ph * Math.sin(w * s)));
      ctx.fillStyle = seq(.08 + .82 * I); ctx.fillRect(SX0 + i * dw, SY, dw + .6, SH);
    }
    ctx.restore();
    line([[SX0, SY], [SX1, SY], [SX1, SY + SH], [SX0, SY + SH]], { color: C.ink, width: SW.axis, close: true, alpha: a });
  }
}
boot();
"""

TITLE = "Noncontact vibration sensing"
ARIA = ("A laser beam from a vibrometer meets a vibrating cantilever; the strip below is the "
        "interference signal it records, its fringes crowding where the surface moves fastest, "
        "which is the Doppler shift.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
