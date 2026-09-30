"""The fun table, "RLC and mechanical resonance" (image11): one equation, two systems.

Model: a series RLC circuit (R = 12 ohm, L = 10 mH, C = 1 uF) and a mass on a
spring with a dashpot (m = 2 kg, k = 800 N/m, c = 4.8 N s/m) obey the same
second order equation,
    L q'' + R q' + q / C = v(t)      m x'' + c x' + k x = f(t),
with the same damping ratio zeta = 0.06 (Q = 8.3). Each is given a short
kick every four cycles (a voltage pulse, a tap) and rings down between. On
screen both run in the same dimensionless time w0 t, so the charge that has
flowed round the circuit (the dots, displaced along the wire by q) and the
mass move in step: the analogy is exact. The periodic response is the sum of
the ring downs of every earlier kick, so the loop is seamless.

Run: python tools/numfig/wt_rlc.py
"""
import numpy as np
from scipy.integrate import solve_ivp

import wt_lib

NAME = "rlc"

R_, L_, C_ = 12.0, 10e-3, 1e-6
M_, K_, CD = 2.0, 800.0, 4.8
W0E, W0M = 1 / np.sqrt(L_ * C_), np.sqrt(K_ / M_)
ZE, ZM = R_ / 2 * np.sqrt(C_ / L_), CD / (2 * np.sqrt(K_ * M_))
CYCLES = 4                                     # damped cycles between kicks
F_SHOW = 0.72                                  # the damped oscillation shown at this rate (Hz)

zeta = ZE
wd1 = np.sqrt(1 - zeta ** 2)                   # damped frequency in units of w0
PERIOD_N = CYCLES * 2 * np.pi / wd1            # kick period in dimensionless time


def ring(s):
    """Response to a unit velocity kick at s = 0 (dimensionless time), zero before."""
    s = np.asarray(s, float)
    return np.where(s >= 0, np.exp(-zeta * s) * np.sin(wd1 * s) / wd1, 0.0)


def steady(s, kback=40):
    return sum(ring(s + k * PERIOD_N) for k in range(kback + 1))


lines = []
say = lines.append
say("nf-wt-rlc: the fun table, 'RLC and mechanical resonance' (image11)")
say("")
say("MODEL")
say(f"  series RLC: R = {R_} ohm, L = {L_*1e3:.0f} mH, C = {C_*1e6:.0f} uF: w0 = 1/sqrt(LC) = {W0E:.1f} rad/s"
    f" ({W0E/2/np.pi:.1f} Hz), zeta = (R/2) sqrt(C/L) = {ZE:.4f}")
say(f"  mass spring dashpot: m = {M_} kg, k = {K_:.0f} N/m, c = {CD} N s/m: w0 = sqrt(k/m) = {W0M:.1f} rad/s"
    f" ({W0M/2/np.pi:.2f} Hz), zeta = c / (2 sqrt(k m)) = {ZM:.4f}")
say(f"  the map: q <-> x, L <-> m, R <-> c, 1/C <-> k, v <-> f. Q = 1 / (2 zeta) = {1/(2*zeta):.3f}")
say(f"  a unit kick every {CYCLES} damped cycles; periodic response = sum of earlier ring downs"
    f" (40 back: residue e^(-zeta 40 P) = {np.exp(-zeta*40*PERIOD_N):.1e})")
say("")
say("CHECK 1: ring down, closed form against direct integration of each system (RK45, rtol 1e-11)")
for name, (a, b, c) in (("circuit", (L_, R_, 1 / C_)), ("mechanical", (M_, CD, K_))):
    w0 = np.sqrt(c / a)
    T = 6 * 2 * np.pi / w0
    tt = np.linspace(0, T, 2001)
    sol = solve_ivp(lambda t, y: [y[1], -(b * y[1] + c * y[0]) / a], (0, T), [0.0, 1.0], t_eval=tt,
                    rtol=1e-11, atol=1e-14)
    closed = ring(w0 * tt) / w0                  # unit velocity kick in real time
    say(f"  {name:10s}: max |closed form - RK45| / max = {np.abs(sol.y[0]-closed).max()/np.abs(closed).max():.1e}")
say("")
say("CHECK 2: resonance: the frequency response of each, computed, against w0 and the half power")
say("  bandwidth w0 / Q")
for name, (a, b, c) in (("circuit", (L_, R_, 1 / C_)), ("mechanical", (M_, CD, K_))):
    w0 = np.sqrt(c / a)
    w = np.linspace(0.5 * w0, 1.5 * w0, 400001)
    H = 1 / np.abs(c - a * w ** 2 + 1j * b * w)
    k = np.argmax(H)
    half = w[H >= H[k] / np.sqrt(2)]
    bw = half[-1] - half[0]
    wpk_closed = w0 * np.sqrt(1 - 2 * zeta ** 2)
    say(f"  {name:10s}: peak at {w[k]/w0:.6f} w0 (closed form sqrt(1 - 2 zeta^2) = {wpk_closed/w0:.6f}),"
        f" half power bandwidth {bw/w0:.5f} w0 (light damping value 2 zeta = {2*zeta:.5f}, {bw/w0/(2*zeta)-1:+.1e})")
say("")
say("DRAWING")
say(f"  both drawn against w0 t: the damped oscillation at {F_SHOW} Hz on screen, so time is slowed"
    f" {W0E*wd1/2/np.pi/F_SHOW:.0f} x (circuit) and {W0M*wd1/2/np.pi/F_SHOW:.2f} x (mass);")
say(f"  a kick every {CYCLES/F_SHOW:.2f} s. The dots move along the wire by q, the mass by x, one scale.")
say(f"  loop closure |x(P) - x(0)| = {abs(steady(np.array([PERIOD_N - 1e-12]))[0] - steady(np.array([0.0]))[0]):.1e}")
wt_lib.write_check(NAME, lines)

xmax = np.abs(steady(np.linspace(0, PERIOD_N, 20001))).max()
DATA = {"zeta": zeta, "wd": wd1, "P": PERIOD_N, "f": F_SHOW, "xmax": xmax}

JS = r"""
const RATE = 2 * Math.PI * DATA.f / DATA.wd;          // dimensionless time per screen second
const LOOP = DATA.P / RATE;                            // screen seconds between kicks
const S0 = Math.PI / 2 / DATA.wd, POSTER_T = 0;         // t = 0 (and the still): the first swing at its peak
function ring(s) { return s < 0 ? 0 : Math.exp(-DATA.zeta * s) * Math.sin(DATA.wd * s) / DATA.wd; }
function resp(s) { let x = 0; for (let k = 0; k <= 40; k++) x += ring(s + k * DATA.P); return x / DATA.xmax; }
// the circuit: a loop of wire, R and L on top, C on the right, the kicking source on the left
const CX0 = 64, CX1 = 424, CY0 = 92, CY1 = 322, CM = (CY0 + CY1) / 2;
const WIRE = [[CX0, CY1], [CX0, CY0], [CX1, CY0], [CX1, CY1], [CX0, CY1]];   // the loop, round
const PER = 2 * (CX1 - CX0 + CY1 - CY0);
function onLoop(s) {                                    // a point at arc length s round the loop
  s = wrap(s, PER);
  for (let i = 1; i < WIRE.length; i++) {
    const d = Math.hypot(WIRE[i][0] - WIRE[i - 1][0], WIRE[i][1] - WIRE[i - 1][1]);
    if (s <= d) return [lerp(WIRE[i - 1][0], WIRE[i][0], s / d), lerp(WIRE[i - 1][1], WIRE[i][1], s / d)];
    s -= d;
  }
  return WIRE[0];
}
const PARTS = [[CX0, CM - 34, CX0, CM + 34], [118, CY0, 214, CY0], [262, CY0, 382, CY0], [CX1, CM - 22, CX1, CM + 22]];
const inPart = p => PARTS.some(([x0, y0, x1, y1]) => p[0] >= Math.min(x0, x1) - 10 && p[0] <= Math.max(x0, x1) + 10 && p[1] >= Math.min(y0, y1) - 10 && p[1] <= Math.max(y0, y1) + 10);
function circuit(a) {
  const w = SW.struct;
  // wires, broken where the parts sit
  line([[CX0, CM + 34], [CX0, CY1], [CX1, CY1], [CX1, CM + 22]], { color: C.ink, width: w, alpha: a });
  line([[CX0, CM - 34], [CX0, CY0], [118, CY0]], { color: C.ink, width: w, alpha: a });
  line([[214, CY0], [262, CY0]], { color: C.ink, width: w, alpha: a });
  line([[382, CY0], [CX1, CY0], [CX1, CM - 22]], { color: C.ink, width: w, alpha: a });
  // R: a zigzag
  const zz = [[118, CY0]]; for (let k = 0; k < 6; k++) zz.push([126 + k * 15, CY0 + (k % 2 ? 22 : -22)]); zz.push([214, CY0]);
  line(zz, { color: C.ink, width: w, alpha: a });
  // L: four loops
  const coil = []; for (let i = 0; i <= 120; i++) { const u = i / 120, th = u * 4 * Math.PI; coil.push([262 + u * 120, CY0 - 26 * Math.abs(Math.sin(th / 2))]); }
  line(coil, { color: C.ink, width: w, alpha: a });
  // C: two plates across the right wire
  for (const dy of [-10, 10]) line([[CX1 - 34, CM + dy], [CX1 + 34, CM + dy]], { color: C.ink, width: w + 2, alpha: a });
  line([[CX1, CM - 22], [CX1, CM - 10]], { color: C.ink, width: w, alpha: a });
  line([[CX1, CM + 10], [CX1, CM + 22]], { color: C.ink, width: w, alpha: a });
  // the source that kicks it: a circle with a pulse
  dot(CX0, CM, 34, { color: C.ink, fill: '#fff', width: w, alpha: a });
  line([[CX0 - 18, CM + 10], [CX0 - 6, CM + 10], [CX0 - 6, CM - 12], [CX0 + 6, CM - 12], [CX0 + 6, CM + 10], [CX0 + 18, CM + 10]], { color: C.ink, width: SW.thin, alpha: a });
}
// the mechanical twin: wall, spring over dashpot, the mass on the floor
const MW = 560, MF = 330, MY1 = 190, MY2 = 276, MX = 800, MB = 118;
function mech(x, a) {
  const w = SW.struct, xm = MX + x;
  big(MW, (MY1 + MY2) / 2, 3.6, () => fixedEnd(0, 0, { h: 52, dir: 1, alpha: a }));
  ground(MW, 960, MF, { alpha: a });
  // spring: a zigzag stretched between the wall and the mass
  const x0 = MW, x1 = xm - MB / 2, sp = [[x0, MY1], [x0 + 22, MY1]];
  for (let k = 0; k < 8; k++) sp.push([lerp(x0 + 30, x1 - 30, (k + .5) / 8), MY1 + (k % 2 ? 20 : -20)]);
  sp.push([x1 - 22, MY1], [x1, MY1]);
  line(sp, { color: C.ink, width: w, alpha: a });
  // dashpot: a cylinder fixed to the wall, its piston on the mass
  const cyl0 = x0 + 40, cyl1 = x0 + 150;
  line([[x0, MY2], [cyl0, MY2]], { color: C.ink, width: w, alpha: a });
  line([[cyl1, MY2 - 22], [cyl0, MY2 - 22], [cyl0, MY2 + 22], [cyl1, MY2 + 22]], { color: C.ink, width: w, alpha: a });
  const px = Math.min(cyl1 - 12, x1 - 90);
  line([[px, MY2 - 16], [px, MY2 + 16]], { color: C.ink, width: w + 2, alpha: a });
  line([[px, MY2], [x1, MY2]], { color: C.ink, width: w, alpha: a });
  // the mass, on two rollers
  line([[xm - MB / 2, MF - 16], [xm + MB / 2, MF - 16], [xm + MB / 2, MF - 16 - MB * 1.25], [xm - MB / 2, MF - 16 - MB * 1.25]],
       { color: C.ink, width: w, fill: C.steel, close: true, alpha: a });
  for (const dx of [-MB / 4, MB / 4]) dot(xm + dx, MF - 8, 8, { color: C.ink, fill: '#fff', width: 4, alpha: a });
}
function draw() {
  const s = S0 + t * RATE;                             // dimensionless time since a kick
  const q = resp(wrap(s, DATA.P));
  const aS = 1, aD = 1;
  circuit(aS);
  // the charge that has flowed: dots displaced along the wire by q, hidden inside the parts
  const AMP = 70;
  for (let k = 0; k < 16; k++) {
    const p = onLoop(k / 16 * PER + AMP * q);
    if (!inPart(p)) dot(p[0], p[1], 8, { color: C.blue, fill: C.blue, alpha: aD });
  }
  mech(AMP * q, aS);
}
boot();
"""

TITLE = "RLC and mechanical resonance"
ARIA = ("A series resistor, inductor and capacitor circuit beside a mass on a spring with a damper: "
        "each is kicked and rings down, the charge in the wire and the mass moving in step, because "
        "both obey the same equation.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
