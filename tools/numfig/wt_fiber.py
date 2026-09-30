"""The fun table, "Guided light" (image6): light pulses guided by total reflection.

Model: an unclad glass fibre, a rod of n = 1.50 in air, 1 mm across: many
thousands of modes, so geometric optics is its exact limit. Three short
light pulses leave the centre of the entrance face together on rays at 0,
22 and 38 degrees to the axis. Every ray meets the faces beyond the critical
angle (48.2 degrees to the axis at most), so it reflects totally and stays
in; each pulse moves along its zigzag at c / n, so the steeper rays fall
behind along the axis (t = n z / (c cos theta)): modal dispersion, the
optical twin of the dispersion of elastic guided waves in plates and rails.

Run: python tools/numfig/wt_fiber.py
"""
import numpy as np

import wt_lib

NAME = "fiber"

N1, N2 = 1.50, 1.00
D = 1.0e-3                                   # rod diameter (m)
ANG = [0.0, 22.0, -38.0]                     # ray angles to the axis (deg); sign: first face met
C0 = 299792458.0
ZLEN = 5.6e-3                                # m of fibre in the cell
SLOW = 5.0e10                                # screen seconds per model second x 1 / SLOW


def path(theta_deg, zlen=ZLEN):
    """Vertices (z, x) of the ray from the centre of the entrance face, reflecting
    specularly at x = +-D/2, until z = zlen."""
    th = np.radians(theta_deg)
    pts = [(0.0, 0.0)]
    if th == 0:
        return np.array([(0.0, 0.0), (zlen, 0.0)])
    z, x, s = 0.0, 0.0, np.sign(th)
    slope = np.tan(abs(th))
    while True:
        dz = (D / 2 - s * x) / slope           # to the face ahead
        if z + dz >= zlen:
            pts.append((zlen, x + s * slope * (zlen - z)))
            return np.array(pts)
        z += dz; x = s * D / 2; pts.append((z, x)); s = -s


lines = []
say = lines.append
say("nf-wt-fiber: the fun table, 'Guided light' (image6)")
say("")
say("MODEL")
say(f"  unclad glass fibre: n1 = {N1} in air (n2 = {N2}), {D*1e3:.1f} mm across, geometric optics;")
say(f"  number of guided modes of a slab this thick at 633 nm ~ 2 V / pi ="
    f" {2*(np.pi*D/633e-9*np.sqrt(N1**2-N2**2))/np.pi:.0f}, so rays are the exact limit.")
thc = np.degrees(np.arccos(N2 / N1))
say(f"  total internal reflection needs the angle to the face normal above asin(n2/n1) ="
    f" {np.degrees(np.arcsin(N2/N1)):.2f} deg, i.e. rays within {thc:.2f} deg of the axis.")
say("")
say("CHECK 1: every ray reflects totally, and the reflection loses nothing (Fresnel, TE and TM)")
for a in ANG:
    ti = np.radians(90 - abs(a))
    if a == 0:
        say("  ray at 0 deg: never meets a face")
        continue
    ct = np.sqrt((N1 / N2 * np.sin(ti)) ** 2 - 1 + 0j)          # imaginary cos of the refracted angle
    rs = (N1 * np.cos(ti) - N2 * 1j * ct.imag) / (N1 * np.cos(ti) + N2 * 1j * ct.imag)
    rp = (N2 * np.cos(ti) - N1 * 1j * ct.imag) / (N2 * np.cos(ti) + N1 * 1j * ct.imag)
    say(f"  ray at {abs(a):4.1f} deg: incidence {np.degrees(ti):.1f} deg > critical"
        f" {np.degrees(np.arcsin(N2/N1)):.1f} deg; |r_TE| = {abs(rs):.12f}, |r_TM| = {abs(rp):.12f}")
say("")
say("CHECK 2: time along the fibre, traced ray by ray against n z / (c cos theta)")
for a in ANG:
    p = path(a)
    traced = np.sum(np.linalg.norm(np.diff(p, axis=0), axis=1)) * N1 / C0
    closed = N1 * ZLEN / (C0 * np.cos(np.radians(a)))
    say(f"  {abs(a):4.1f} deg: {len(p)-2} reflections, traced {traced*1e12:.6f} ps, closed form {closed*1e12:.6f} ps"
        f" ({traced/closed-1:+.1e})")
spread = N1 * ZLEN / C0 * (1 / np.cos(np.radians(max(abs(a) for a in ANG))) - 1)
say(f"  spread between the axial and the steepest pulse over {ZLEN*1e3:.1f} mm: {spread*1e12:.3f} ps"
    f" (modal dispersion n L / c (1 / cos theta - 1))")
say("")
say("CHECK 3: a ray is the limit of a guided mode: the exact TE mode of the slab with the ray's transverse")
say("  wavenumber, its group velocity d w / d beta against the ray's speed along the axis (c / n) cos theta")
from scipy.optimize import brentq as _brentq
LAM = 633e-9


def te_mode(k0, m):
    """(beta, u) of TE mode m of the slab: u tan(u - m pi / 2) = sqrt(V^2 - u^2), u = kappa d / 2."""
    V = k0 * D / 2 * np.sqrt(N1 ** 2 - N2 ** 2)
    f = lambda u: u * np.tan(u - m * np.pi / 2) - np.sqrt(V * V - u * u)
    u = _brentq(f, m * np.pi / 2 + 1e-9, min((m + 1) * np.pi / 2, V) - 1e-9, xtol=1e-12)
    return np.sqrt((k0 * N1) ** 2 - (2 * u / D) ** 2), u


for a in ANG:
    if a == 0:
        continue
    k0 = 2 * np.pi / LAM
    m = int(round(k0 * N1 * np.sin(np.radians(abs(a))) * D / np.pi))
    b0, u = te_mode(k0, m)
    th = np.degrees(np.arcsin(2 * u / D / (k0 * N1)))
    e = 1e-7
    bp, _ = te_mode(k0 * (1 + e), m); bm, _ = te_mode(k0 * (1 - e), m)
    vg = C0 * 2 * e * k0 / (bp - bm)
    vray = C0 / N1 * np.cos(np.radians(th))
    say(f"  TE{m} (its ray at {th:.4f} deg): v_g = {vg:.6e} m/s, (c / n) cos theta = {vray:.6e} m/s ({vg/vray-1:+.1e})")
say("  the difference is the Goos-Hanchen shift at each reflection, of order the wavelength over the thickness.")
say("")
say("DRAWING")
say(f"  1000 units = {ZLEN*1e3:.1f} mm, the same scale across (rod {D*1e3:.0f} mm = {D/ZLEN*1000:.0f} units): no stretch.")
say(f"  time slowed {SLOW:.1e} x: the axial pulse crosses the cell in {N1*ZLEN/C0*SLOW:.2f} s on screen.")
wt_lib.write_check(NAME, lines)

DATA = {"z": ZLEN, "d": D, "n": N1, "c": C0, "slow": SLOW,
        "rays": [{"p": (path(a) / ZLEN).ravel().tolist(), "cos": float(np.cos(np.radians(a)))} for a in ANG]}

JS = r"""
const YM = H / 2, X0 = 30, SC = W, HC = DATA.d / DATA.z / 2 * W;   // path coordinates in cell lengths; the end face at X0
const V = DATA.c / DATA.n / DATA.slow / DATA.z;   // pulse speed along its ray, cell lengths per second
const LOOP = 1 / (V * Math.min(...DATA.rays.map(r => r.cos))) + .9;
const U0 = .56 / V, POSTER_T = 0;                          // t = 0 (and the still): the axial pulse past half way
const R = DATA.rays.map(r => { const p = []; for (let i = 0; i < r.p.length; i += 2) p.push([X0 + r.p[i] * SC, YM - r.p[i + 1] * SC]); return p; });
const LEN = R.map(p => { let L = 0; for (let i = 1; i < p.length; i++) L += Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]); return L; });
function along(p, s) {                                     // the point at arc length s, and the piece behind it
  let left = s;
  for (let i = 1; i < p.length; i++) {
    const d = Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]);
    if (left <= d) return [lerp(p[i - 1][0], p[i][0], left / d), lerp(p[i - 1][1], p[i][1], left / d), i];
    left -= d;
  }
  return [p[p.length - 1][0], p[p.length - 1][1], p.length - 1];
}
function pulse(p, s, len, a) {                              // a pulse len long ending at arc length s
  const pts = [], s0 = Math.max(0, s - len);
  for (let k = 0; k <= 12; k++) { const q = along(p, lerp(s0, s, k / 12)); pts.push([q[0], q[1]]); }
  line(pts, { color: C.accent, width: 20, alpha: a });
}
function draw() {
  const u = wrap(U0 + t, LOOP);
  const aS = 1, aR = 1;
  // the rod: glass, its two faces
  ctx.save(); ctx.globalAlpha *= aS; ctx.fillStyle = C.steel; ctx.fillRect(X0, YM - HC, W, 2 * HC); ctx.restore();
  line([[X0, YM - HC], [X0, YM + HC]], { color: C.ink, width: SW.struct, alpha: aS });
  for (const s of [-1, 1]) line([[X0, YM + s * HC], [W, YM + s * HC]], { color: C.ink, width: SW.struct });
  // the three ray paths, and a pulse on each: all leave together, the steep ones fall behind
  R.forEach((p, i) => {
    line(p, { color: C.sky, width: SW.thin, alpha: aR });
    const s = u * V * W;                                   // arc length travelled (drawing units)
    if (s > 0 && s - 60 < LEN[i]) pulse(p, Math.min(s, LEN[i]), 60, clamp((LEN[i] + 60 - s) / 60) * clamp(s / 30) * aR);
  });
  dot(X0, YM, 13, { color: C.ink, fill: '#fff', width: 5, alpha: aS });
}
boot();
"""

TITLE = "Guided light"
ARIA = ("Three light pulses enter a glass fibre together on rays at different angles and zigzag "
        "down it by total internal reflection; the steeper rays fall behind, which is modal "
        "dispersion.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
