"""The fun table, "Radar reflection" (image8): ground penetrating radar finds a rebar.

Model: a GPR antenna slides along a concrete deck slab (150 mm, relative
permittivity 6.25, so radar waves travel at v = c / 2.5 = 0.12 m/ns) with a
25 mm reinforcing bar at 50 mm cover. At each position the echo from the
bar returns after t = 2 (sqrt(dx^2 + d^2) - r) / v; drawn at its apparent
depth v t / 2 under the antenna, the echoes trace the hyperbola whose apex
sits on the bar, the signature GPR reads. The underside of the slab, a
change of permittivity too, answers at 2 D / v everywhere.
Checked against a two dimensional FDTD simulation of Maxwell's equations.

Run: python tools/numfig/wt_radar.py
"""
import numpy as np
from scipy.signal import hilbert

import wt_lib

NAME = "radar"

C0 = 299792458.0
EPS = 6.25
V = C0 / np.sqrt(EPS)
D_SLAB = 0.150
R_BAR, COVER = 0.0125, 0.050
D_C = COVER + R_BAR                         # depth of the bar's centre
XS = (-0.30, 0.30)                          # scan (m), the bar at x = 0
SCAN_V = 0.25                               # antenna speed (m/s), real time on screen


def t_bar(x):
    return 2 * (np.sqrt(x * x + D_C * D_C) - R_BAR) / V


# ------------------------------------------------------------------ FDTD check
def fdtd(bar_x=None, bottom=True, dx=1.25e-3, tmax=4.2e-9, f0=2.0e9, depth=D_SLAB):
    """2D TMz FDTD of the travel time law: concrete above the slab's underside
    (y = D_SLAB; air below it, or concrete when bottom is False), so the
    antenna's own coupling across the top face stays out of the check;
    optional PEC bar centred (bar_x, D_C); a soft Ricker source and a receiver
    at (0, 0). Returns (t, Ez at the receiver)."""
    x = np.arange(-0.34, 0.34, dx); y = np.arange(-0.16, 0.34, dx)
    nx, ny = len(x), len(y)
    X, Y = np.meshgrid(x, y, indexing="ij")
    er = np.where((Y <= depth) | (not bottom), EPS, 1.0)
    pec = np.zeros((nx, ny), bool)
    if bar_x is not None:
        pec = (X - bar_x) ** 2 + (Y - D_C) ** 2 <= R_BAR ** 2
    eps0, mu0 = 8.8541878128e-12, 4e-7 * np.pi
    dt = 0.99 * dx / (C0 * np.sqrt(2))
    npml = 40
    ramp = lambda n: (np.clip(n, 0, None) / npml) ** 3
    ix = np.arange(nx); iy = np.arange(ny)
    prof = np.maximum(ramp(npml - ix)[:, None], ramp(ix - (nx - 1 - npml))[:, None])         + np.maximum(ramp(npml - iy)[None, :], ramp(iy - (ny - 1 - npml))[None, :])
    sig = 0.8 * (4 / (dx * 377.0)) * prof
    ca = (1 - sig * dt / (2 * eps0 * er)) / (1 + sig * dt / (2 * eps0 * er))
    cb = (dt / (eps0 * er * dx)) / (1 + sig * dt / (2 * eps0 * er))
    Ez = np.zeros((nx, ny)); Hx = np.zeros((nx, ny - 1)); Hy = np.zeros((nx - 1, ny))
    i0 = int(np.argmin(np.abs(x))); j0 = int(np.argmin(np.abs(y)))
    nt = int(tmax / dt)
    t0 = 1.2 / f0
    rec = np.zeros(nt)
    curl = np.zeros_like(Ez)
    for n in range(nt):
        Hx -= dt / (mu0 * dx) * (Ez[:, 1:] - Ez[:, :-1])
        Hy += dt / (mu0 * dx) * (Ez[1:, :] - Ez[:-1, :])
        curl[:] = 0
        curl[1:-1, :] += Hy[1:, :] - Hy[:-1, :]
        curl[:, 1:-1] -= Hx[:, 1:] - Hx[:, :-1]
        Ez = ca * Ez + cb * curl
        tt = (n + 1) * dt - t0
        Ez[i0, j0] += (1 - 2 * (np.pi * f0 * tt) ** 2) * np.exp(-(np.pi * f0 * tt) ** 2)
        Ez[pec] = 0.0
        rec[n] = Ez[i0, j0]
    return (np.arange(nt) + 1) * dt, rec


def delay(a, b, dt):
    """Time by which b lags a, from the peak of their cross correlation (parabolic refinement)."""
    cc = np.correlate(b, a, "full")
    k = int(np.argmax(np.abs(cc)))
    cc = cc * np.sign(cc[k])
    y0, y1, y2 = cc[k - 1:k + 2]
    return (k - (len(a) - 1) + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2)) * dt


lines = []
say = lines.append
say("nf-wt-radar: the fun table, 'Radar reflection' (image8)")
say("")
say("MODEL")
say(f"  concrete slab {D_SLAB*1e3:.0f} mm thick, relative permittivity {EPS} (lossless here): v = c / sqrt(eps) ="
    f" {V/1e9:.4f} m/ns")
say(f"  steel bar {2*R_BAR*1e3:.0f} mm, cover {COVER*1e3:.0f} mm (centre at {D_C*1e3:.1f} mm); zero offset antenna")
say("  echo from the bar at t(x) = 2 (sqrt(x^2 + d^2) - r) / v (the specular point faces the antenna),")
say(f"  from the underside at 2 D / v = {2*D_SLAB/V*1e9:.3f} ns; apparent depth v t / 2.")
say("")
say("CHECK: 2D FDTD of Maxwell's equations (TMz, 1.25 mm cells, a 2 GHz Ricker pulse, the bar a")
say("  perfect conductor, a graded absorbing layer; the antenna's own coupling across the top face")
say("  left out, concrete above the underside), echo = run with the bar minus run without;")
say("  each echo's delay behind the zero offset echo (cross correlation) against t(x) - t(0)")
TAG = f"radar{EPS}-{D_SLAB}-{R_BAR}-{COVER}"                       # the cache follows the model
t_ref, r_ref = wt_lib.cached(TAG, fdtd, None)
dtf = t_ref[1] - t_ref[0]
tt, r0 = wt_lib.cached(TAG, fdtd, bar_x=0.0)
e0 = r0 - r_ref
for xo in (0.05, 0.10, 0.15):
    tt, rr = wt_lib.cached(TAG, fdtd, bar_x=-xo)
    fd = delay(e0, rr - r_ref, dtf)
    ex = t_bar(xo) - t_bar(0.0)
    say(f"  offset {xo*1e3:5.0f} mm: FDTD {fd*1e12:7.1f} ps, closed form {ex*1e12:7.1f} ps ({(fd-ex)*1e12:+.1f} ps,"
        f" {fd/ex-1:+.1e})")
tt, rh = wt_lib.cached(TAG, fdtd, None, bottom=False)                     # concrete all the way: no underside
tt, r2 = wt_lib.cached(TAG, fdtd, None, depth=D_SLAB + 0.030)             # the underside 30 mm lower
fd = delay(r_ref - rh, r2 - rh, dtf)
v_meas = 2 * 0.030 / fd
say(f"  velocity from the underside's echo moving 30 mm deeper: {v_meas/1e9:.4f} m/ns against"
    f" c / sqrt(eps) = {V/1e9:.4f} m/ns ({v_meas/V-1:+.1e})")
say(f"  the bar is not large against the wavelength (k r = {2*np.pi*2e9*np.sqrt(EPS)/C0*R_BAR:.2f} at 2 GHz):")
say("  the travel time law is the specular (geometric) limit; the full wave run follows it within 11 ps")
say("  at 50 mm and 2 ps beyond, where the paths are longer against the bar.")
say("")
say("DRAWING")
say(f"  scan from {XS[0]*1e3:.0f} to {XS[1]*1e3:.0f} mm = 1000 units, depth to the same scale;"
    f" the antenna moves at {SCAN_V} m/s in real time.")
say("  only the part of the hyperbola above the underside is drawn (apparent depth < D).")
wt_lib.write_check(NAME, lines)

xh = np.linspace(-0.30, 0.30, 241)
zh = V * t_bar(xh) / 2
DATA = {"xs": list(XS), "D": D_SLAB, "r": R_BAR, "dc": D_C, "v": SCAN_V,
        "hx": xh.tolist(), "hz": zh.tolist()}

JS = r"""
const X0 = DATA.xs[0], X1 = DATA.xs[1], SC = W / (X1 - X0), XC = x => (x - X0) * SC;
const YS = 96, ZC = z => YS + z * SC;                   // the slab's top face; depth to scale
const SCAN = (X1 - X0 - .10) / DATA.v, LOOP = SCAN + 1.5;
const U0 = SCAN * .98, POSTER_T = 0;                     // t = 0 (and the still): the pass all but done
const HX = DATA.hx, HZ = DATA.hz;
function draw() {
  const u = wrap(U0 + t, LOOP);
  const aS = 1;
  const xa = Math.min(X0 + .05 + u * DATA.v, X1 - .05);  // antenna centre (m)
  const k = clamp(1 - (u - (LOOP - .45)) / .4);          // the record clears before the next pass
  // the slab: concrete, the bar in it
  ctx.save(); ctx.globalAlpha *= aS; ctx.fillStyle = C.grid; ctx.fillRect(0, YS, W, DATA.D * SC); ctx.restore();
  line([[0, YS], [W, YS]], { color: C.ink, width: SW.struct });
  line([[0, ZC(DATA.D)], [W, ZC(DATA.D)]], { color: C.ink, width: SW.struct });
  dot(XC(0), ZC(DATA.dc), DATA.r * SC, { color: '#781E2C', fill: C.accent, width: 3, alpha: 1 });
  // the record: the underside answering everywhere, the bar's hyperbola, both built as the antenna passes
  const xr = xa;
  line([[XC(X0 + .05), ZC(DATA.D) - 16], [XC(xr), ZC(DATA.D) - 16]], { color: C.navy, width: SW.thin, alpha: k * aS });
  const hp = [];
  for (let i = 0; i < HX.length; i++) if (HX[i] >= X0 + .05 && HX[i] <= xr && HZ[i] < DATA.D - .012) hp.push([XC(HX[i]), ZC(HZ[i])]);
  if (hp.length > 1) line(hp, { color: C.accent, width: SW.data, alpha: k });
  // the antenna, and the path to the bar's near face and back
  const dxb = 0 - xa, L = Math.hypot(dxb, DATA.dc), ex = xa + dxb * (1 - DATA.r / L), ez = DATA.dc * (1 - DATA.r / L);
  if (u > 0) line([[XC(xa), YS], [XC(ex), ZC(ez)]], { color: C.blue, width: SW.thin, alpha: k });
  const aw = .08 * SC;
  line([[XC(xa) - aw / 2, YS], [XC(xa) + aw / 2, YS], [XC(xa) + aw / 2, YS - 44], [XC(xa) - aw / 2, YS - 44]],
       { color: C.navy, width: 2, fill: C.navy, close: true, alpha: aS });
}
boot();
"""

TITLE = "Radar reflection"
ARIA = ("A radar antenna slides along a concrete slab; the echoes from a buried steel bar, drawn at "
        "their apparent depth, trace a hyperbola whose apex sits on the bar, while the slab's "
        "underside answers at the same depth everywhere.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
