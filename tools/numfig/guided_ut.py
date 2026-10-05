"""Figure 12: guided wave ultrasonic testing, from the Rayleigh-Lamb equations.

Model: a free steel plate, thickness d = 10 mm (Lamb waves, plane strain). The
Rayleigh-Lamb frequency equations are solved for the symmetric (S) and
antisymmetric (A) modes by a bracketing scan in phase velocity and Brent's
method; group velocities by central differences of the exact roots.

A 3 cycle Hann windowed tone burst at 50 kHz is launched from a transducer at
x = 0 and propagated by exact Fourier synthesis with each mode's own k(omega):

    u(x, t) = sum_j A_j cos(omega_j t - k_j(omega_j) s + phi_j),

s the path length (x for the incident wave, 2D - x for the echo from the
defect at D, which reflects a share R and transmits T = sqrt(1 - R^2)). The
same sum, evaluated in the page for every frame, is the field along the plate
in (a); at x = 0 it is the received trace in (c) (S0, flat) and (d) (A0,
steep). (b) is the dispersion curve itself with both operating points.

Run: python tools/numfig/guided_ut.py   (writes the page, the still and the
check file; prints the key numbers). coverage.py (Figure 13) imports the
model from here.
"""
import os

import numpy as np
from scipy.optimize import brentq
from scipy.signal import hilbert

import common

# ------------------------------------------------------------------ material
E, NU, RHO = 210e9, 0.29, 7850.0          # steel, as Figures 4 and 5
D_PLATE = 10e-3                           # plate thickness d (m)
H = D_PLATE / 2                           # half thickness
MU = E / (2 * (1 + NU))
LAM = E * NU / ((1 + NU) * (1 - 2 * NU))
C_L = np.sqrt((LAM + 2 * MU) / RHO)       # longitudinal (P) speed
C_T = np.sqrt(MU / RHO)                   # shear speed
C_PLATE = np.sqrt(E / (RHO * (1 - NU ** 2)))   # S0 low frequency limit

# ------------------------------------------------------------------ test
F0 = 50e3            # tone burst centre frequency (Hz): f d = 0.5 MHz mm
NCYC = 3             # Hann windowed cycles
D_DEF = 1.5          # defect distance from the transducer (m)
R_DEF = 0.5          # defect reflection coefficient (displacement), both modes
T_DEF = np.sqrt(1 - R_DEF ** 2)
X_END = 2.15         # the plate drawn from 0 to X_END (m), cut (continues) there
TP = 2.5e-3          # synthesis period (s): the spectrum's line spacing is 1/TP
THRESH = 1e-3        # spectral lines kept: amplitude above THRESH of the largest
SLOW = 5000.0        # real seconds per model second: what the SHM guide's pages import (keep)
SLOW_PAGE = 7000.0   # this page's own, and Figure 13's (b): 1.4 times SLOW (29 Sep, "a little slower")
PPM, PH_DRAW = 400, 34   # drawing units per metre along the plate; drawn thickness


def rayleigh_speed(nu=NU, ct=C_T):
    """Rayleigh wave speed: root of (2 - x)^2 = 4 sqrt(1 - x k2) sqrt(1 - x),
    x = (c/cT)^2, k2 = (cT/cL)^2."""
    k2 = (1 - 2 * nu) / (2 * (1 - nu))
    g = lambda x: (2 - x) ** 2 - 4 * np.sqrt(1 - x * k2) * np.sqrt(1 - x)
    return ct * np.sqrt(brentq(g, 0.5, 0.99999, xtol=1e-15))


C_R = rayleigh_speed()


# ------------------------------------------------------------------ Rayleigh-Lamb
def _parts(c, w):
    """k, p^2, q^2 and the real building blocks of the Rayleigh-Lamb equations
    for any sign of p^2, q^2: S = sin(x h)/x, Cc = cos(x h), xS = x sin(x h)
    (continued as sinh, cosh when x is imaginary)."""
    c = np.asarray(c, float)
    k = w / c
    p2 = (w / C_L) ** 2 - k * k
    q2 = (w / C_T) ** 2 - k * k

    def blocks(x2):
        x = np.sqrt(np.abs(x2))
        xh = x * H
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
            s = np.where(x2 > 0, np.sin(xh) / x, np.sinh(xh) / x)
            s = np.where(x == 0, H, s)
            cc = np.where(x2 > 0, np.cos(xh), np.cosh(xh))
            xs = np.where(x2 > 0, x * np.sin(xh), -x * np.sinh(xh))
            scale = np.where(x2 > 0, 1.0, np.cosh(np.minimum(xh, 700)))
        return s, cc, xs, scale

    return k, p2, q2, blocks(p2), blocks(q2)


def f_sym(c, w):
    """Symmetric Rayleigh-Lamb function, real and pole free, scaled to O(1):
    (q^2 - k^2)^2 cos(ph) sin(qh)/q + 4 k^2 p sin(ph) cos(qh)."""
    k, p2, q2, (sp, cp, xsp, gp), (sq, cq, xsq, gq) = _parts(c, w)
    return ((q2 - k * k) ** 2 * cp * sq + 4 * k * k * xsp * cq) / (k ** 4 * gp * gq)


def f_anti(c, w):
    """Antisymmetric: (q^2 - k^2)^2 sin(ph)/p cos(qh) + 4 k^2 cos(ph) q sin(qh)."""
    k, p2, q2, (sp, cp, xsp, gp), (sq, cq, xsq, gq) = _parts(c, w)
    return ((q2 - k * k) ** 2 * sp * cq + 4 * k * k * cp * xsq) / (k ** 4 * gp * gq)


FAM = {"S": f_sym, "A": f_anti}


def roots_at(fam, f, cmin=40.0, cmax=60000.0, n=6000):
    """Every phase velocity (m/s) of family 'S' or 'A' at frequency f (Hz),
    ascending: a log spaced scan for sign changes, each refined by Brent."""
    F = FAM[fam]
    w = 2 * np.pi * f
    cs = np.geomspace(cmin, cmax, n)
    v = F(cs, w)
    idx = np.nonzero(np.sign(v[:-1]) * np.sign(v[1:]) < 0)[0]
    g = lambda c: float(F(c, w))
    return [brentq(g, cs[i], cs[i + 1], xtol=1e-12, rtol=1e-15) for i in idx]


def track(fam, fs, c0):
    """Follow one branch through the increasing frequencies fs from the phase
    velocity c0 near the first: a narrow bracket around the last root."""
    F = FAM[fam]
    out, c = [], c0
    for f in fs:
        w = 2 * np.pi * f
        g = lambda x: float(F(x, w))
        lo, hi = c * 0.995, c * 1.005
        while np.sign(g(lo)) == np.sign(g(hi)):
            lo, hi = lo * 0.99, hi * 1.01
        c = brentq(g, lo, hi, xtol=1e-12, rtol=1e-15)
        out.append(c)
    return np.array(out)


def lowest(fam, f):
    return roots_at(fam, f)[0]


def group_velocity(fam, f, c=None, df=2.0):
    """c_g = d omega / d k at f by central differences of exact roots."""
    c = lowest(fam, f) if c is None else c
    cm, cc, cp_ = track(fam, [f - df, f, f + df], c)
    km, kp = 2 * np.pi * (f - df) / cm, 2 * np.pi * (f + df) / cp_
    return cc, 2 * np.pi * 2 * df / (kp - km)


# ------------------------------------------------------------------ synthesis
def burst(f0=F0, ncyc=NCYC, tp=TP, dt=0.05e-6):
    """The Hann windowed tone burst on one period tp, sampled at dt."""
    n = int(round(tp / dt))
    t = np.arange(n) * dt
    T = ncyc / f0
    s = np.where(t <= T, 0.5 * (1 - np.cos(2 * np.pi * t / T)) * np.sin(2 * np.pi * f0 * t), 0.0)
    return t, s


def components(fam, f0=F0, ncyc=NCYC, tp=TP, thresh=THRESH):
    """The burst's spectral lines above `thresh`, each with its wavenumber on
    the lowest branch of family fam: omega, k, amplitude, phase (float32, as
    the page gets them, so page and traces use the same numbers)."""
    t, s = burst(f0, ncyc, tp)
    n = len(t)
    Sp = np.fft.rfft(s)
    fr = np.fft.rfftfreq(n, t[1] - t[0])
    A = 2 * np.abs(Sp) / n
    keep = A > thresh * A.max()
    fk = fr[keep]
    c = track(fam, fk, lowest(fam, fk[0]))
    w = 2 * np.pi * fk
    comp = dict(w=w, k=w / c, a=A[keep], p=np.angle(Sp)[keep], f=fk, c=c)
    for key in ("w", "k", "a", "p"):
        comp[key] = comp[key].astype(np.float32).astype(np.float64)
    return comp


def synth(comp, s, t, gain=1.0):
    """u at path length s (m) for times t (s): the Fourier sum."""
    t = np.atleast_1d(t)
    ph = comp["w"][None, :] * t[:, None] - comp["k"][None, :] * s + comp["p"][None, :]
    return gain * (comp["a"][None, :] * np.cos(ph)).sum(1)


def received(comp, t):
    """The trace at the transducer (x = 0): outgoing burst plus defect echo."""
    return synth(comp, 0.0, t) + synth(comp, 2 * D_DEF, t, R_DEF)


def field(comp, x, tm):
    """Pulse echo field along the plate at one model time (numpy reference for
    the page's own sum)."""
    a = x <= D_DEF
    ph_i = comp["w"] * tm - np.outer(x, comp["k"]) + comp["p"]
    ph_r = comp["w"] * tm - np.outer(2 * D_DEF - x, comp["k"]) + comp["p"]
    inc = (comp["a"] * np.cos(ph_i)).sum(1)
    ref = (comp["a"] * np.cos(ph_r)).sum(1)
    return np.where(a, inc + R_DEF * ref, T_DEF * inc)


def field_ae(comp, x, tm):
    """The same burst launched at the defect, travelling both ways."""
    ph = comp["w"] * tm - np.outer(np.abs(x - D_DEF), comp["k"]) + comp["p"]
    return (comp["a"] * np.cos(ph)).sum(1)


def mode_shape(fam, f, c, z):
    """Lamb mode displacements (u_x, u_z) across the thickness z in [-h, h]
    from the potentials (phi, psi) = (A cos pz, B sin qz) (S) or
    (A sin pz, B cos qz) (A), (A, B) the null vector of the traction free
    conditions at z = h. Also returns |det| scaled, a check that c is a root."""
    w = 2 * np.pi * f
    k = w / c
    p = np.sqrt(complex((w / C_L) ** 2 - k * k))
    q = np.sqrt(complex((w / C_T) ** 2 - k * k))
    g = LAM * (k * k + p * p) + 2 * MU * p * p
    if fam == "S":
        M = np.array([[-g * np.cos(p * H), -2j * MU * k * q * np.cos(q * H)],
                      [-2j * MU * k * p * np.sin(p * H), MU * (k * k - q * q) * np.sin(q * H)]])
    else:
        M = np.array([[-g * np.sin(p * H), 2j * MU * k * q * np.sin(q * H)],
                      [2j * MU * k * p * np.cos(p * H), MU * (k * k - q * q) * np.cos(q * H)]])
    A, B = M[0, 1], -M[0, 0]
    if fam == "S":
        ux = 1j * k * A * np.cos(p * z) + q * B * np.cos(q * z)
        uz = -p * A * np.sin(p * z) - 1j * k * B * np.sin(q * z)
    else:
        ux = 1j * k * A * np.sin(p * z) - q * B * np.sin(q * z)
        uz = p * A * np.cos(p * z) - 1j * k * B * np.cos(q * z)
    det = abs(np.linalg.det(M)) / (abs(M[0, 0] * M[1, 1]) + abs(M[0, 1] * M[1, 0]))
    return ux, uz, det


def check_page(name, cases):
    """Evaluate the page's own sum in a browser and return the largest
    difference from numpy over `cases`: [(mode, tm, ae, numpy_values)] for
    fieldAt(mode, tm, ae), or [(js_expression, numpy_values)]."""
    from playwright.sync_api import sync_playwright
    path = os.path.join(common.ANIM, f"nf-{name}.html").replace("\\", "/")
    worst = 0.0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file:///" + path + "?still")
        pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
        for case in cases:
            if len(case) == 2:
                expr, ref = case
            else:
                mode, tm, ae, ref = case
                expr = f"fieldAt('{mode}', {tm!r}, {str(ae).lower()})"
            got = np.array(pg.evaluate(f"Array.from({expr})"))
            worst = max(worst, float(np.abs(got - ref).max()))
        b.close()
    return worst


def envelope_peak(t, u, t_min):
    env = np.abs(hilbert(u))
    m = t >= t_min
    i = np.argmax(env[m])
    return t[m][i], env[m][i], env


def width6(t, env, t_min, t_max):
    m = (t >= t_min) & (t <= t_max)
    e = env[m]
    above = np.nonzero(e >= 0.5 * e.max())[0]
    return t[m][above[-1]] - t[m][above[0]]


def sci_tex(v):
    """v as m x 10^e for the page's math(): 7000 -> 7\\,\\times\\,10^{3}."""
    e = int(np.floor(np.log10(v)))
    return f"{v / 10 ** e:.3g}\\,\\times\\,10^{{{e}}}"


# ------------------------------------------------------------------ the page
JS = r"""
const G = DATA;
// times travel in microseconds; the page works in seconds
for (const k of ['tc', 'tmax', 'dt_tr', 'tend_ae', 'poster_tm']) G[k] = G[k + '_us'] * 1e-6;
for (const m of ['S0', 'A0']) {
  G[m].tend = G[m].tend_us * 1e-6; G[m].echo_t = G[m].echo_us * 1e-6; G[m].slope = G[m].slope_mskhz / 1000;
}
/* the physics starts at 0.35 s: the loop begins with its quiet gap, so the
   first gap is already under way when the page opens */
const GAP = 0.8, T0 = 0.35 - GAP, SLOW = G.slow;
const TC = G.tc;                                   // burst centre (s)
const PX0 = 90, PPM = G.ppm, PY = 108, PH = G.ph;  // plate: x = 0 at PX0, PPM units per metre
/* the plate as a thin slab in an oblique view, as Figure 4 draws its plate: its top
   face recedes DX3, DY3 up and to the right. The model is plane strain, so the wave
   is the same across the plate's width: the top face carries the front face's field,
   and the defect (a notch across the width) cuts the top face from edge to edge. */
const DX3 = 14, DY3 = 10;
const XU = x => PX0 + x * PPM;
const ACC = C.accent, FLAW = '#781E2C', LBL = 16, SUB = 18, TICK = 16, S = .28;   // crimson: the defect and its echo alone
// a diverging ramp for the displacement field whose zero is the steel itself
const FLUT = _ramp(['#043052', '#2E6A9E', '#9CBBD6', '#E3EBF2', '#DEABAB', '#B03F4D', '#651020'].map(_hex));

function dec(o) { return { w: b64f32(o.w), k: b64f32(o.k), a: b64f32(o.a), p: b64f32(o.p) }; }
const MODE = { S0: dec(G.S0.c), A0: dec(G.A0.c) };
const TRACE = { S0: b64f32(G.S0.trace), A0: b64f32(G.A0.trace) };
const NX = G.nx, DXM = G.dx, ID = Math.round(G.D / DXM);
const U = new Float64Array(NX);

/* The Fourier sum along the plate at model time tm (s): the pulse echo from
   x = 0 with the defect at D (reflects R, transmits T), or (ae) the same burst
   launched at the defect itself, travelling both ways. Each spectral line is
   rotated along x by exp(-i k dx): exact, no table. */
function fieldAt(mode, tm, ae) {
  U.fill(0);
  const m = MODE[mode], n = m.w.length, D = G.D, R = G.R, T = G.T;
  for (let j = 0; j < n; j++) {
    const k = m.k[j], a = m.a[j], ph = m.w[j] * tm + m.p[j];
    const cd = Math.cos(k * DXM), sd = Math.sin(k * DXM);
    if (!ae) {
      let c = Math.cos(ph), s = Math.sin(ph);                       // incident, path x
      for (let i = 0; i < NX; i++) {
        U[i] += (i <= ID ? a : a * T) * c;
        const c2 = c * cd + s * sd; s = s * cd - c * sd; c = c2;
      }
      const b = ph - 2 * k * D;                                     // echo, path 2D - x
      c = Math.cos(b); s = Math.sin(b);
      for (let i = 0; i <= ID; i++) {
        U[i] += a * R * c;
        const c2 = c * cd - s * sd; s = s * cd + c * sd; c = c2;
      }
    } else {
      const b = ph - k * D;                                         // path D - x, x < D
      let c = Math.cos(b), s = Math.sin(b);
      for (let i = 0; i < ID; i++) {
        U[i] += a * c;
        const c2 = c * cd - s * sd; s = s * cd + c * sd; c = c2;
      }
      c = Math.cos(ph); s = Math.sin(ph);                           // path x - D, x >= D
      for (let i = ID; i < NX; i++) {
        U[i] += a * c;
        const c2 = c * cd + s * sd; s = s * cd - c * sd; c = c2;
      }
    }
  }
  return U;
}

/* The loop: a quiet gap, the S0 pulse echo, the A0 pulse echo, then the
   acoustic emission burst, each in model time slowed SLOW times. */
const M0 = -20e-6;
const CY = [{ id: 'S0', mode: 'S0', m1: G.S0.tend, say: 'S_0\\rm{, 50 kHz, pulse echo}' },
            { id: 'A0', mode: 'A0', m1: G.A0.tend, say: 'A_0\\rm{, 50 kHz, pulse echo}' },
            { id: 'AE', mode: 'S0', m1: G.tend_ae, say: 'S_0\\rm{, 50 kHz, acoustic emission}' }];
let _acc = 0;
for (const c of CY) { c.r0 = _acc + GAP; c.r1 = c.r0 + (c.m1 - M0) * SLOW; _acc = c.r1; }
const PER = _acc + GAP;
function now() {
  const tt = t - T0, loop = Math.floor(tt / PER), tau = tt - loop * PER;
  let cyc = null;
  for (const c of CY) if (tau >= c.r0 && tau < c.r1) cyc = c;
  return { loop, tau, cyc, b: T0 + loop * PER, tm: cyc ? M0 + (tau - cyc.r0) / SLOW : null };
}
/* a cycle's own marks: they settle in just before it starts, fade after it ends */
function cycA(c, st, fin = .28, fout = .3) {
  return settle(st.b + c.r0 - fin - .05, fin) * (1 - seg(st.b + c.r1, fout));
}
const cycTm = (c, st) => clamp(M0 + (st.tau - c.r0) / SLOW, M0, c.m1);
const POSTER_T = T0 + PER + CY[0].r0 + (G.poster_tm - M0) * SLOW;

/* ------------------------------------------------------------ helpers */
function offscreen(w, h) { const cvs = document.createElement('canvas'); cvs.width = w; cvs.height = h; const g = cvs.getContext('2d'); return { cvs, g, img: g.createImageData(w, h) }; }
const FIM = offscreen(NX, 3), BAR = offscreen(256, 1);
for (let i = 0; i < 256; i++) BAR.img.data.set([FLUT[3 * i], FLUT[3 * i + 1], FLUT[3 * i + 2], 255], 4 * i);
BAR.g.putImageData(BAR.img, 0, 0);
function paintField(u, alpha) {
  const d = FIM.img.data;
  for (let i = 0; i < NX; i++) {
    const li = Math.round((clamp(u[i], -1, 1) + 1) * 127.5) * 3;
    for (let r = 0; r < 3; r++) { const o = (r * NX + i) * 4; d[o] = FLUT[li]; d[o + 1] = FLUT[li + 1]; d[o + 2] = FLUT[li + 2]; d[o + 3] = 255; }
  }
  FIM.g.putImageData(FIM.img, 0, 0);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = true;
  ctx.beginPath(); ctx.rect(XU(0), PY, XU(G.xend) - XU(0), PH); ctx.clip();
  ctx.drawImage(FIM.cvs, 0, 1, NX, 1, XU(-DXM / 2), PY, NX * DXM * PPM, PH);
  ctx.restore();
  // the top face: the same field, sheared onto it (u, v) -> (u + DX3 v, PY - DY3 v)
  ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = true; topPath(); ctx.clip();
  ctx.transform(1, 0, DX3, -DY3, 0, PY);
  ctx.drawImage(FIM.cvs, 0, 1, NX, 1, XU(-DXM / 2), 0, NX * DXM * PPM, 1);
  ctx.restore();
}
function topPath() {                               // the top face, as a path (for its fill and its clip)
  const x0 = XU(0), x1 = XU(G.xend);
  ctx.beginPath(); ctx.moveTo(x0, PY); ctx.lineTo(x1, PY); ctx.lineTo(x1 + DX3, PY - DY3); ctx.lineTo(x0 + DX3, PY - DY3); ctx.closePath();
}
function topCut(x, o = {}) {                      // the top face's edge at the cut: zigzag, as the front's
  const pts = [], n = 4, a = 3;
  for (let i = 0; i <= n; i++) { const v = i / n, e = (i % 2 ? a : -a) * (i > 0 && i < n ? 1 : 0); pts.push([x + DX3 * v + e, PY - DY3 * v]); }
  line(pts, { color: C.ink, width: 1.3, ...o });
}
function cutEdge(x, y0, y1, o = {}) {            // a zigzag cut: the plate continues
  const pts = [], n = 6, a = 4;
  for (let i = 0; i <= n; i++) pts.push([x + (i % 2 ? a : -a) * (i > 0 && i < n ? 1 : 0), lerp(y0 - 3, y1 + 3, i / n)]);
  line(pts, { color: C.ink, width: 1.3, ...o });
}
function notch(xc, o = {}) {                      // the defect: a surface notch across the width
  const w = 5, dp = PH * 0.45, x = XU(xc);
  ctx.save(); ctx.globalAlpha *= (o.alpha ?? 1);
  ctx.beginPath(); ctx.moveTo(x - w / 2, PY); ctx.lineTo(x + w / 2, PY); ctx.lineTo(x + w / 2 + DX3, PY - DY3); ctx.lineTo(x - w / 2 + DX3, PY - DY3); ctx.closePath();
  ctx.fillStyle = o.fill || ACC; ctx.fill(); ctx.strokeStyle = FLAW; ctx.lineWidth = 1.1; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x - w / 2, PY - .5); ctx.lineTo(x - w / 2, PY + dp - w / 2);
  ctx.arc(x, PY + dp - w / 2, w / 2, Math.PI, 0, true); ctx.lineTo(x + w / 2, PY - .5); ctx.closePath();
  ctx.fillStyle = o.fill || ACC; ctx.fill(); ctx.strokeStyle = FLAW; ctx.lineWidth = 1.1; ctx.stroke(); ctx.restore();
}
function colourBar(x, y, w, labs, alpha) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = true; ctx.drawImage(BAR.cvs, x, y, w, 8); ctx.restore();
  line([[x, y], [x + w, y], [x + w, y + 8], [x, y + 8], [x, y]], { color: C.ink, width: .8, alpha });
  for (const [v, s] of [[-1, '-1'], [0, '0'], [1, '1']]) {
    const xx = x + (v + 1) / 2 * w;
    line([[xx, y + 8], [xx, y + 11]], { color: C.ink, width: .8, alpha });
    math(s, xx, y + 26, { size: TICK, align: 'center', alpha });
  }
  for (const [lab, a] of labs) if (a > 0) math(lab, x - 10, y + 9, { size: 17, align: 'right', alpha: alpha * a });
}
function interp(xs, ys, x) {
  let lo = 0, hi = xs.length - 1;
  if (x <= xs[0]) return ys[0]; if (x >= xs[hi]) return ys[hi];
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] > x) hi = m; else lo = m; }
  return lerp(ys[lo], ys[hi], (x - xs[lo]) / (xs[hi] - xs[lo]));
}
function mix(a, b, s) { const A = _hex(a), B = _hex(b); return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], s))).join(',')})`; }
/* labels a time cursor passes behind: their ink boxes, kept as they are
   drawn; gapLine() is a vertical line broken 3 units clear of each */
const KEEP = [];
function keepText(s, x, y, o) {
  text(s, x, y, o);
  if (!(o.alpha > 0)) return;
  ctx.save(); ctx.font = font(o); ctx.textAlign = o.align || 'left'; const q = ctx.measureText(s); ctx.restore();
  KEEP.push([x - q.actualBoundingBoxLeft, y - q.actualBoundingBoxAscent, x + q.actualBoundingBoxRight, y + q.actualBoundingBoxDescent]);
}
function gapLine(x, y0, y1, o) {
  const cuts = KEEP.filter(b => x > b[0] - 3 && x < b[2] + 3).map(b => [b[1] - 3, b[3] + 3]).sort((p, q) => p[0] - q[0]);
  let y = y0;
  for (const [p, q] of cuts) { if (p > y + .5) line([[x, y], [x, Math.min(p, y1)]], o); y = Math.max(y, q); if (y >= y1) return; }
  if (y1 > y + .5) line([[x, y], [x, y1]], o);
}
/* the engine's dim(), its knockout as deep as the label's ink (the slash and
   the subscript g reach below dim()'s own), opaque from the first frame so the
   line never shows through the label while both fade in */
function dimk(x1, x2, y, label, o) {
  const { color, alpha, size } = o;
  dim(x1, x2, y, '', { color, alpha });
  if (alpha <= 0) return;
  const w = math(label, 0, -1e4, { size, alpha: 0 }), bx = (x1 + x2) / 2 - w / 2 - 4, by = y - size * .62;
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(bx, by, w + 8, size * 1.42); ctx.restore();
  KEEP.push([bx, by, bx + w + 8, by + size * 1.42]);
  math(label, (x1 + x2) / 2, y + size * .34, { size, align: 'center', color, alpha });
}

/* ------------------------------------------------------------ (a) the plate */
function panelA(st) {
  panel('a', 20, 34, { alpha: seg(0, .25) });
  for (const c of CY) {                           // what is on show, and the model clock
    const a = cycA(c, st);
    if (a <= 0) continue;
    math(c.say, 58, 34, { size: SUB, color: C.body, alpha: a });
    math(`t = ${Math.max(0, Math.round(cycTm(c, st) * 1e6))}\\,\\rm{µs}`, 950, 34, { size: 17, align: 'right', alpha: a });
  }
  text(G.slowtxt, 950, 56, { size: 15, color: C.muted, align: 'right', alpha: seg(.5, .3) });

  // the plate: steel, the outline drawing itself; the far face heavier
  const x0 = XU(0), x1 = XU(G.xend), pa = seg(0, .4);
  ctx.save(); ctx.globalAlpha *= seg(.05, .25); ctx.fillStyle = C.steel; ctx.fillRect(x0, PY, x1 - x0, PH); topPath(); ctx.fill(); ctx.restore();
  let fieldOn = 0;
  if (st.cyc) {
    const c = st.cyc;
    fieldOn = 1 - seg(st.b + c.r1 - .45, .45);
    paintField(fieldAt(c.mode, st.tm, c.id === 'AE'), fieldOn);
  }
  line([[x1, PY], [x0, PY], [x0, PY + PH], [x1, PY + PH]], { color: C.ink, width: 1.6, progress: pa });
  line([[x0, PY + PH], [x1, PY + PH]], { color: C.ink, width: 2.4, progress: pa });
  line([[x0, PY], [x0 + DX3, PY - DY3], [x1 + DX3, PY - DY3]], { color: C.ink, width: 1.2, progress: pa });
  cutEdge(x1, PY, PY + PH, { alpha: seg(.3, .2) }); topCut(x1, { alpha: seg(.3, .2) });

  // transducer on the top face at the left end; the defect, a surface notch
  const tIn = settle(.12, S), dIn = settle(.18, S);
  ctx.save(); ctx.globalAlpha *= tIn; ctx.fillStyle = C.navy; ctx.fillRect(XU(0) + 4, PY - DY3 / 2 - 13 - 8 * (1 - tIn), 12, 13); ctx.restore();
  const ae = cycA(CY[2], st, .28, .45);
  let flash = 0;
  if (st.cyc === CY[2] && st.tm > 0 && st.tm < G.ncyc / G.f0) flash = Math.sin(Math.PI * st.tm * G.f0 / G.ncyc) ** 2;  // the source's own Hann envelope
  ctx.save(); ctx.translate(0, -8 * (1 - dIn)); notch(G.D, { alpha: dIn, fill: flash > 0 ? mix(ACC, C.amber, flash) : ACC }); ctx.restore();
  const lIn = settle(.25, S), ly = PY - DY3 - 20 - 6 * (1 - lIn);
  // one name gives way to the other in turn (out, then in), never both at once in one place
  const aOld = lIn * clamp(1 - 2 * ae), aNew = lIn * clamp(2 * ae - 1);
  text('transducer', XU(0) - 4, ly, { size: LBL, color: C.body, alpha: aOld });
  text('sensor', XU(0) - 4, ly, { size: LBL, color: C.body, alpha: aNew });
  text('defect', XU(G.D), ly, { size: LBL, color: C.body, align: 'center', alpha: aOld });
  text('acoustic emission', XU(G.D), ly, { size: LBL, color: C.body, align: 'center', alpha: aNew });

  if (st.cyc && fieldOn > .02) packetArrows(st, fieldOn);

  // the length axis, in metres
  const ya = PY + PH + 16;
  line([[XU(0), ya], [XU(2), ya]], { color: C.ink, width: 1.3, progress: seg(.08, .35) });
  [0, .5, 1, 1.5, 2].forEach((v, i) => {
    const a = seg(.15 + .05 * i, .25);
    line([[XU(v), ya], [XU(v), ya - 5]], { color: C.ink, width: 1.1, alpha: a });
    math(fmt(v), XU(v), ya + 20, { size: TICK, align: 'center', alpha: a });
  });
  math('x\\ (\\rm{m})', XU(2) + 36, ya + 20, { size: 17, align: 'left', alpha: seg(.4, .25) });
  const aA0 = cycA(CY[1], st);
  colourBar(XU(1.76), ya + 30, 110, [[G.S0.lab, 1 - aA0], [G.A0.lab, aA0]], seg(.45, .3));
  // the plate thickness, dimensioned at the free left end
  const da = seg(.35, .25), xd = XU(0) - 16;
  arrow(xd, PY + PH / 2, xd, PY, { width: 1, head: 6, alpha: da }); arrow(xd, PY + PH / 2, xd, PY + PH, { width: 1, head: 6, alpha: da });
  math('d', xd - 7, PY + PH / 2 + 6, { size: 17, align: 'right', alpha: da });
  // what was computed, under the plate
  const pl = seg(.55, .3);
  math(G.params[0], XU(0), ya + 44, { size: 15, color: C.muted, alpha: pl });
  math(G.params[1], XU(0), ya + 63, { size: 15, color: C.muted, alpha: pl });
}
/* arrows over the packets: their centres move at the mode's group velocity */
function packetArrows(st, al) {
  const c = st.cyc, cg = G[c.mode].cg, dt = st.tm - TC, y = PY - DY3 - 8;
  const put = (x, dir, lab, col) => {
    if (x < 0.1 || x > G.xend - 0.08) return;
    const xm = XU(x), L = 26;
    arrow(xm - dir * L / 2, y, xm + dir * L / 2, y, { color: col, width: 1.4, head: 8, alpha: al });
    // keep clear of the transducer and defect labels
    const clear = clamp((x - 0.3) / 0.12) * clamp((Math.abs(x - G.D) - 0.24) / 0.1);
    if (lab) text(lab, xm, y - 8, { size: LBL, color: col === ACC ? ACC : C.muted, align: 'center', alpha: al * clear });
  };
  if (dt <= 0) return;
  if (c.id === 'AE') { put(G.D - cg * dt, -1, '', C.ink); put(G.D + cg * dt, 1, '', C.ink); return; }
  const xi = cg * dt;
  put(xi, 1, xi < G.D ? 'incident' : 'transmitted', C.ink);
  if (xi > G.D) put(2 * G.D - xi, -1, 'echo', ACC);
}

/* ------------------------------------------------------------ (b) dispersion */
const BX = { x: 90, y: 262, w: 360, h: 262 };
function panelB(st) {
  panel('b', 20, 246, { alpha: seg(.05, .25) });
  text('operating points', 58, 246, { size: SUB, color: C.body, alpha: settle(.1, S) });
  const A = axes({ ...BX, xlim: [0, G.fmax], ylim: [0, 7], xticks: [0, 50, 100, 150, 200, 250],
                   yticks: [0, 1, 2, 3, 4, 5, 6, 7], grid: true, progress: seg(.05, .4),
                   xlabel: '\\rm{frequency }f\\ (\\rm{kHz})', ylabel: '\\rm{phase velocity }c_{\\rm{p}}\\ (\\rm{km/s})', ylabelGap: 42,
                   tickSize: TICK });
  // the tone burst's -6 dB band: the stretch of each curve the burst samples
  const bA = seg(.45, .3);
  ctx.save(); ctx.globalAlpha *= bA; ctx.fillStyle = C.steel;
  ctx.fillRect(A.X(G.band[0]), BX.y + 1, A.X(G.band[1]) - A.X(G.band[0]), BX.h - 2); ctx.restore();
  text('burst band', A.X((G.band[0] + G.band[1]) / 2), BX.y + BX.h - 9, { size: LBL, color: C.body, align: 'center', alpha: bA });
  // shear and Rayleigh speeds: A0 and S0 tend to c_R at high frequency
  const rA = seg(.35, .3);
  for (const [v, lab, dy] of [[G.cT, '\\rm{shear}', -6], [G.cR, '\\rm{Rayleigh}', 16]]) {
    A.inside(() => line([[A.X(0), A.Y(v)], [A.X(G.fmax), A.Y(v)]], { color: C.guide, width: 1, dash: [5, 4], alpha: rA }));
    const w = math(lab === '\\rm{shear}' ? 'c_{\\rm{T}}' : 'c_{\\rm{R}}', A.X(4), A.Y(v) + dy, { size: 17, color: C.body, alpha: rA });
    math(lab, A.X(4) + w + 6, A.Y(v) + dy, { size: LBL, color: C.body, alpha: rA });
  }
  const curve = (f, c, t0) => A.inside(() => line(f.map((v, i) => [A.X(v), A.Y(c[i])]), { color: C.blue, width: 2.4, progress: seg(t0, .4) }));
  curve(G.disp.f, G.disp.S0, .15); curve(G.disp.f, G.disp.A0, .2); curve(G.disp.fA1, G.disp.A1, .25);
  const la0 = settle(.5, S), la1 = settle(.55, S), la2 = settle(.6, S);
  math('S_0', A.X(168), A.Y(5.15) - 12 - 5 * (1 - la0), { size: 18, alpha: la0 });
  math('A_0', A.X(150), A.Y(2.45) + 27 + 5 * (1 - la1), { size: 18, alpha: la1 });
  math('A_1', A.X(G.a1lab[0]) - 8, A.Y(G.a1lab[1]) + 23, { size: 18, align: 'left', alpha: la2 });
  // where A1 cuts on (k = 0), marked in grey as Figure 4 marks its cut-on frequencies
  const ca = settle(.6, S), xc = A.X(G.fc_a1);
  ctx.save(); ctx.globalAlpha *= ca; ctx.fillStyle = C.guide; ctx.beginPath();
  ctx.moveTo(xc, BX.y + 1 + 7); ctx.lineTo(xc - 5, BX.y + 1); ctx.lineTo(xc + 5, BX.y + 1); ctx.closePath(); ctx.fill(); ctx.restore();
  text('cut-on', xc, BX.y - 6, { size: LBL, color: C.body, align: 'center', alpha: ca });
  // the operating points glide along the computed curves onto 50 kHz
  const g = settle(.5, .35), fx = G.f0 / 1e3;
  for (const md of ['S0', 'A0']) {
    const f = lerp(4, fx, g), c = interp(G.disp.f, G.disp[md], f), cx = G[md].cp / 1e3, sl = G[md].slope;
    A.inside(() => line([[A.X(fx - 34), A.Y(cx - 34 * sl)], [A.X(fx + 34), A.Y(cx + 34 * sl)]], { color: C.navy, width: 1.6, alpha: seg(.8, .25) }));
    const act = md === 'S0' ? Math.max(cycA(CY[0], st, .4, .4), cycA(CY[2], st, .4, .4)) : cycA(CY[1], st, .4, .4);
    if (act > 0 && g > 0) dot(A.X(f), A.Y(c), 5 + 5 * act, { color: C.navy, fill: null, width: 1.3, alpha: act * Math.min(1, g * 4) });
    if (g > 0) dot(A.X(f), A.Y(c), 5, { color: C.navy, fill: C.navy, alpha: Math.min(1, g * 4) });
  }
  const lo = settle(.85, S);
  text('non dispersive', A.X(fx - 14), A.Y(G.S0.cp / 1e3) - 17 - 5 * (1 - lo), { size: LBL, color: C.body, alpha: lo });
  text('dispersive', A.X(fx + 10), A.Y(G.A0.cp / 1e3) + 24 + 5 * (1 - lo), { size: LBL, color: C.body, alpha: lo });
}

/* ------------------------------------------------------------ (c), (d) received */
const AX = { x: 590, w: 360, h: 104 };
function ascan(which, y0, letter, sub, st, tIn) {
  panel(letter, 520, y0 - 13, { alpha: seg(tIn, .25) });
  math(sub, 555, y0 - 13, { size: SUB, color: C.body, alpha: settle(tIn + .05, S) });
  const bottom = which === 'A0', tmaxu = G.tmax * 1e6;
  const A = axes({ x: AX.x, y: y0, w: AX.w, h: AX.h, xlim: [0, tmaxu], ylim: [-1.15, 1.15],
                   xticks: [0, 200, 400, 600, 800, 1000, 1200, 1400], yticks: [-1, 0, 1],
                   xfmt: bottom ? (v => fmt(v)) : (v => ''), xlabel: bottom ? 't\\ (\\rm{µs})' : '',
                   ylabel: 'u/u_0', ylabelGap: 40, progress: seg(tIn, .4), tickSize: TICK });
  A.inside(() => line([[A.X(0), A.Y(0)], [A.X(tmaxu), A.Y(0)]], { color: C.rule, width: 1 }));
  const tr = TRACE[which], n = tr.length, dtu = G.dt_tr * 1e6, cyc = CY.find(c => c.id === which);
  const [wa, wb] = G[which].win_us;
  // in the first loop the trace draws itself in step with its cycle's clock;
  // after that it stays whole and the cursor replays it
  let upto = 0;
  if (st.loop === 0) { if (st.cyc === cyc) upto = st.tm; else if (st.tau >= cyc.r1) upto = G.tmax; }
  else if (st.loop > 0) upto = G.tmax;
  const k1 = Math.min(n, Math.floor(upto * 1e6 / dtu) + 1);
  const part = (i0, i1, col) => {                  // the trace from sample i0 to i1 (exclusive)
    i1 = Math.min(i1, k1); if (i1 - i0 < 2) return;
    const pts = []; for (let i = i0; i < i1; i++) pts.push([A.X(i * dtu), A.Y(tr[i])]);
    A.inside(() => line(pts, { color: col, width: 1.8 }));
  };
  const ia = Math.round(wa / dtu), ib = Math.round(wb / dtu);
  part(0, ia + 1, C.navy); part(ia, ib + 1, ACC); part(ib, n, C.navy);   // the defect echo in the accent
  // the arrival the group velocity predicts: burst centre + 2D/c_g
  const tg = 2 * G.D / G[which].cg, ta = A.X((G.tc + tg) * 1e6), la = seg(tIn + .5, .3), lb = settle(tIn + .6, S);
  A.inside(() => line([[ta, y0 + 26], [ta, y0 + AX.h]], { color: C.guide, width: 1, dash: [5, 4], alpha: la }));
  dimk(A.X(G.tc * 1e6), ta, y0 + 15, `2D/c_{\\rm{g}} = ${Math.round(tg * 1e6)}\\,\\rm{µs}`, { size: LBL, color: C.ink, alpha: la });
  keepText('initial pulse', A.X(70), A.Y(-.6), { size: LBL, color: C.body, alpha: lb });
  // beside the echo, clear of the guide: after the compact S0 echo; right of the guide under the smeared A0 one
  if (which === 'S0') keepText('defect echo', A.X(wb) + 8, A.Y(.42), { size: LBL, color: ACC, alpha: lb });
  else keepText('defect echo', ta + 6, A.Y(-.6), { size: LBL, color: ACC, alpha: lb });
  // the time cursor of this trace's cycle
  const ca = seg(st.b + cyc.r0, .2) * (1 - seg(st.b + cyc.r1, .3));
  if (ca > 0 && st.tau > cyc.r0 - .01) {
    const tm = cycTm(cyc, st), cx = A.X(tm * 1e6), i = clamp(Math.round(tm * 1e6 / dtu), 0, n - 1);
    gapLine(cx, y0, y0 + AX.h, { color: C.ink, width: 1, alpha: .55 * ca });   // behind the labels
    dot(cx, A.Y(tm < 0 ? 0 : tr[i]), 3, { color: i >= ia && i <= ib ? ACC : C.navy, fill: i >= ia && i <= ib ? ACC : C.navy, alpha: ca });
  }
}

function draw() {
  const st = now();
  KEEP.length = 0;
  panelA(st);
  panelB(st);
  ascan('S0', 262, 'c', 'S_0\\rm{, compact echo}', st, .1);
  ascan('A0', 420, 'd', 'A_0\\rm{, smeared echo}', st, .15);
}
boot();
"""


def build():
    print(f"c_L = {C_L:.1f} m/s, c_T = {C_T:.1f} m/s, c_plate = {C_PLATE:.1f} m/s, c_R = {C_R:.2f} m/s")
    fmax = 280e3
    fgrid = np.arange(0.5e3, fmax + 1, 0.5e3)
    s0 = track("S", fgrid, C_PLATE)
    a0 = track("A", fgrid, lowest("A", fgrid[0]))
    # A1 from just above its cut-off (f d = c_T/2), the second antisymmetric root
    fc_a1 = C_T / (2 * D_PLATE)
    fa1 = fgrid[fgrid > fc_a1]
    while len(roots_at("A", fa1[0])) < 2:          # c_p above the scan's 60 km/s
        fa1 = fa1[1:]
    a1 = track("A", fa1, roots_at("A", fa1[0])[1])
    # check that tracking stayed on the lowest branches: rescan a few frequencies
    for f in (10e3, 100e3, 200e3, 275e3):
        i = np.argmin(np.abs(fgrid - f))
        assert abs(roots_at("S", fgrid[i])[0] / s0[i] - 1) < 1e-9
        assert abs(roots_at("A", fgrid[i])[0] / a0[i] - 1) < 1e-9

    # operating points, group velocities, local slopes dc_p/df
    ops = {}
    for md, fam in (("S0", "S"), ("A0", "A")):
        cp, cg = group_velocity(fam, F0)
        cpm, cpp = track(fam, [F0 - 500, F0 + 500], cp)[[0, 1]]
        slope = (cpp - cpm) / 1000.0            # (m/s)/Hz = (km/s)/kHz
        ops[md] = dict(cp=cp, cg=cg, slope=slope)
        print(f"{md} at {F0/1e3:.0f} kHz: c_p = {cp:.1f} m/s, c_g = {cg:.1f} m/s, dc_p/df = {slope*1e3:.3f} (m/s)/kHz")

    # the burst, its band, the synthesis and the received traces
    comp = {md: components(fam) for md, fam in (("S0", "S"), ("A0", "A"))}
    tb, sb = burst()
    Sb = np.abs(np.fft.rfft(sb)); fb = np.fft.rfftfreq(len(tb), tb[1] - tb[0])
    above = fb[Sb >= 0.5 * Sb.max()]
    band = (above.min() / 1e3, above.max() / 1e3)
    tc = NCYC / F0 / 2
    dt_tr, tmax = 1e-6, 1400e-6
    ttr = np.arange(0, tmax + dt_tr / 2, dt_tr)
    traces, echo = {}, {}
    for md in ("S0", "A0"):
        traces[md] = received(comp[md], ttr)
        te = np.arange(0, 2.4e-3, 0.1e-6)
        ee = synth(comp[md], 2 * D_DEF, te, R_DEF)
        tpk, apk, env = envelope_peak(te, ee, 0)
        near = np.abs(te - tpk) < 600e-6
        big = te[near][env[near] >= 0.03 * apk]          # where the echo is drawn in the accent
        echo[md] = dict(t=tpk, amp=apk, pred=tc + 2 * D_DEF / ops[md]["cg"],
                        w6=width6(te, env, tpk - 600e-6, tpk + 600e-6),
                        win=(max(big[0], 0.0), min(big[-1], tmax)))
        print(f"{md} echo: envelope peak {tpk*1e6:.1f} us (burst centre + 2D/c_g = {echo[md]['pred']*1e6:.1f} us), "
              f"-6 dB width {echo[md]['w6']*1e6:.1f} us, peak {apk:.3f}")
    inc = synth(comp["S0"], 0.0, np.arange(0, 200e-6, 0.1e-6))
    w6_burst = width6(np.arange(0, 200e-6, 0.1e-6), np.abs(hilbert(inc)), 0, 200e-6)

    # end of each cycle: the plate has gone quiet (echo received, transmitted wave gone)
    tend = {"S0": 660e-6, "A0": 1360e-6}
    tend_ae = 420e-6
    poster_tm = tc + 1.80 / ops["S0"]["cg"]           # S0: transmitted at 1.8 m, echo at 1.2 m

    dx = 2.5e-3
    nx = int(round(X_END / dx)) + 1
    exag = PH_DRAW / (D_PLATE * PPM)
    # the parameter lines, set as math (variables italic, units upright)
    params = [r"\rm{steel plate,}\ d = 10\,\rm{mm}\ (\rm{drawn}\ " + f"{exag:g}" + r"\ \times\ \rm{thicker}),\ \ "
              r"E = 210\,\rm{GPa},\ \ \nu\ = 0.29,\ \ \rho\ = 7850\,\rm{kg/m}^{3}",
              r"\rm{3 cycle Hann burst at 50 kHz; defect at}\ " + f"{D_DEF:g}" + r"\,\rm{m},\ \rm{reflection}\ " + f"{R_DEF:g}"]
    keep = a1 < 7.6e3                                  # (b) shows c_p up to 7 km/s, as Figure 4 does
    data = dict(
        slow=SLOW_PAGE, slowtxt=f"shown {SLOW_PAGE:,.0f} × slower", tc_us=tc * 1e6, f0=F0, ncyc=NCYC, D=D_DEF, R=R_DEF, T=T_DEF, xend=X_END, nx=nx, dx=dx,
        ppm=PPM, ph=PH_DRAW, fmax=fmax / 1e3, cR=C_R / 1e3, cT=C_T / 1e3, fc_a1=fc_a1 / 1e3, band=band,
        tmax_us=tmax * 1e6, dt_tr_us=dt_tr * 1e6, tend_ae_us=tend_ae * 1e6, poster_tm_us=poster_tm * 1e6,
        disp=dict(f=fgrid / 1e3, S0=s0 / 1e3, A0=a0 / 1e3, fA1=fa1[keep] / 1e3, A1=a1[keep] / 1e3),
        a1lab=[float(np.interp(6.75e3, a1[::-1], fa1[::-1]) / 1e3), 6.75],
        params=params,
    )
    for md in ("S0", "A0"):
        c = comp[md]
        data[md] = dict(cp=ops[md]["cp"], cg=ops[md]["cg"], slope_mskhz=ops[md]["slope"] * 1e3, tend_us=tend[md] * 1e6,
                        echo_us=echo[md]["t"] * 1e6, win_us=[v * 1e6 for v in echo[md]["win"]],
                        lab="u_x/u_0" if md == "S0" else "u_z/u_0",
                        c=dict(w=common.f32(c["w"]), k=common.f32(c["k"]), a=common.f32(c["a"]), p=common.f32(c["p"])),
                        trace=common.f32(traces[md]))
    title = ("Figure 12: Guided wave ultrasonic testing")
    aria = ("A tone burst computed from the Rayleigh-Lamb equations travels along a 10 mm steel plate, reflects "
            "from a defect 1.5 m away and returns: as the S0 mode it stays compact, as the dispersive A0 mode it "
            "smears out, while the dispersion curves mark both operating points and the received signals draw "
            "themselves. Then the defect launches the same wave itself, as an acoustic emission.")
    common.build_html("guided-ut", title, aria, 1000, 590, data, JS)
    png = common.still("guided-ut")
    print("still:", png)
    res = dict(s0=s0, a0=a0, fgrid=fgrid, fa1=fa1, a1=a1, ops=ops, comp=comp, echo=echo,
               w6_burst=w6_burst, band=band, tc=tc, traces=traces, ttr=ttr, nx=nx, dx=dx, exag=exag)
    validate(res)
    return res


def validate(r):
    """The closed-form limits, the synthesis error and the page's own sum;
    writes guided_ut.check.txt and prints the key numbers."""
    L = []
    say = L.append
    rel = lambda a, b: f"{(a - b) / b * 100:+.4f} %"
    # 1. S0 and A0 at low f d
    f_lo = 1e3
    s0_lo = lowest("S", f_lo)
    Db = E * D_PLATE ** 3 / (12 * (1 - NU ** 2))
    kirch = lambda f: (2 * np.pi * f) ** 0.5 * (Db / (RHO * D_PLATE)) ** 0.25
    a0_lo = {f: group_velocity("A", f) for f in (1e3, 100.0)}
    # 2. high f d: A0 and S0 tend to the Rayleigh speed
    f_hi = 2e6                                    # f d = 20 MHz mm
    s0_hi, a0_hi = lowest("S", f_hi), lowest("A", f_hi)
    # 3. A1 cut-off (k -> 0): f d = c_T / 2
    k_small = 1e-3
    g = lambda f: float(f_anti(2 * np.pi * f / k_small, 2 * np.pi * f))
    fs = np.linspace(150e3, 170e3, 401)
    v = np.array([g(f) for f in fs])
    i = np.nonzero(np.sign(v[:-1]) != np.sign(v[1:]))[0][0]
    fc_num = brentq(g, fs[i], fs[i + 1], xtol=1e-6)
    fc_cf = C_T / (2 * D_PLATE)
    # 4. scan density: roots unchanged when the scan is twice as fine
    dens = max(abs(roots_at(fam, f, n=12000)[0] / roots_at(fam, f)[0] - 1)
               for fam in "SA" for f in (5e3, 50e3, 150e3, 250e3))
    # 5. mode shapes at the operating points: how uniform the shown component is
    z = np.linspace(-H, H, 201)
    ux, uz, detS = mode_shape("S", F0, r["ops"]["S0"]["cp"], z)
    s_unif = abs(ux[-1]) / abs(ux[100]) - 1
    s_ratio = abs(uz[-1]) / abs(ux[100])
    ux, uz, detA = mode_shape("A", F0, r["ops"]["A0"]["cp"], z)
    a_unif = abs(uz[-1]) / abs(uz[100]) - 1
    a_ratio = abs(ux[-1]) / abs(uz[100])
    # 6. synthesis: the page's lines against a long period, every line
    tt = np.arange(-20e-6, 1400e-6, 0.5e-6)
    syn = {}
    for md, fam in (("S0", "S"), ("A0", "A")):
        ref = components(fam, tp=10e-3, thresh=1e-6)
        c = r["comp"][md]
        syn[md] = max(float(np.abs(synth(c, s, tt) - synth(ref, s, tt)).max()) for s in (0, .5, 1, 1.5, 2, 3))
    # 7. the page's own sum against numpy
    xg = np.arange(r["nx"]) * r["dx"]
    cases = [("S0", 366e-6, False, field(r["comp"]["S0"], xg, 366e-6)),
             ("A0", 700e-6, False, field(r["comp"]["A0"], xg, 700e-6)),
             ("S0", 150e-6, True, field_ae(r["comp"]["S0"], xg, 150e-6))]
    page = check_page("guided-ut", cases)

    ops, ec = r["ops"], r["echo"]
    say("Figure 12, guided wave ultrasonic testing: check of tools/numfig/guided_ut.py")
    say("")
    say("MODEL")
    say(f"  Lamb waves in a free steel plate (plane strain), thickness d = {D_PLATE*1e3:g} mm;")
    say(f"  E = {E/1e9:g} GPa, nu = {NU}, rho = {RHO:g} kg/m3 (as Figures 4 and 5).")
    say(f"  c_L = {C_L:.1f} m/s, c_T = {C_T:.1f} m/s, c_plate = sqrt(E/(rho(1-nu^2))) = {C_PLATE:.1f} m/s,")
    say(f"  c_R = {C_R:.2f} m/s (root of the Rayleigh equation).")
    say("  Rayleigh-Lamb equations, symmetric and antisymmetric, written real and pole free for")
    say("  real or imaginary p, q. Roots in phase velocity: a 6000 point log scan from 40 m/s to")
    say("  60 km/s, each sign change refined by Brent (1e-12 m/s). Branches S0, A0, A1 followed by")
    say("  continuation on a 0.5 kHz grid from 0.5 to 280 kHz, and checked against a full rescan")
    say("  at 10, 100, 200 and 275 kHz. Group velocity: central differences of exact roots, df = 2 Hz.")
    say(f"  Scan twice as fine: largest change of a root {dens:.1e} (relative).")
    say("")
    say(f"OPERATING POINTS (f = {F0/1e3:g} kHz, f d = {F0/1e6*D_PLATE*1e3:g} MHz mm)")
    for md, word in (("S0", "flat, non dispersive"), ("A0", "steep, dispersive")):
        o = ops[md]
        say(f"  {md}: c_p = {o['cp']:.1f} m/s, c_g = {o['cg']:.1f} m/s, dc_p/df = {o['slope']*1e3:+.3f} (m/s)/kHz  ({word})")
    say("")
    say("VALIDATION AGAINST CLOSED FORMS")
    say(f"  1. S0 as f d -> 0 (f = 1 kHz): c_p = {s0_lo:.3f} m/s against the plate velocity")
    say(f"     {C_PLATE:.3f} m/s: {rel(s0_lo, C_PLATE)}")
    say("  2. A0 as f d -> 0 against Kirchhoff bending, c_p = (omega^2 D/(rho d))^(1/4), c_g = 2 c_p")
    say("     (the error falls as (k d)^2, ten times per decade of f: shear and rotary inertia):")
    for f, (cp, cg) in a0_lo.items():
        say(f"     f = {f/1e3:g} kHz: c_p = {cp:.4f} m/s against {kirch(f):.4f} m/s ({rel(cp, kirch(f))}),"
            f" c_g = {cg:.4f} against {2*kirch(f):.4f} m/s ({rel(cg, 2*kirch(f))})")
    say(f"  3. f d = 20 MHz mm: S0 c_p = {s0_hi:.4f} m/s, A0 c_p = {a0_hi:.4f} m/s against the")
    say(f"     Rayleigh speed {C_R:.4f} m/s: S0 {rel(s0_hi, C_R)}, A0 {rel(a0_hi, C_R)}")
    say(f"  4. A1 cut-off (k -> 0): {fc_num/1e3:.4f} kHz against f d = c_T/2, {fc_cf/1e3:.4f} kHz:")
    say(f"     {rel(fc_num, fc_cf)}")
    say(f"  5. Echo arrival, envelope peak (Hilbert) of the synthesized echo against the burst")
    say(f"     centre ({r['tc']*1e6:g} us) + 2D/c_g:")
    for md in ("S0", "A0"):
        e = ec[md]
        say(f"     {md}: {e['t']*1e6:.1f} us against {e['pred']*1e6:.1f} us ({(e['t']-e['pred'])*1e6:+.1f} us)")
    say("     (A0, by stationary phase: the upper half of the band, where c_g is higher and changes")
    say("     more slowly, spreads less, so the smeared envelope peaks before the centre frequency's")
    say("     group delay.)")
    say("")
    say("MODE SHAPES AT 50 kHz (traction free null vector; |det| scaled "
        f"{max(detS, detA):.1e})")
    say(f"  S0: u_x varies {s_unif*100:+.2f} % from mid-plane to surface; |u_z(h)|/|u_x(0)| = {s_ratio:.3f}")
    say(f"  A0: u_z varies {a_unif*100:+.2f} % from mid-plane to surface; |u_x(h)|/|u_z(0)| = {a_ratio:.3f}")
    say("  The page colours the plate with each mode's dominant component (u_x for S0, u_z for")
    say("  A0), taken uniform through the thickness, as these numbers allow.")
    say("")
    say("SYNTHESIS")
    say(f"  Burst: {NCYC} cycle Hann window at {F0/1e3:g} kHz, sampled every 0.05 us on one period of")
    say(f"  {TP*1e3:g} ms (line spacing {1/TP:g} Hz); lines above {THRESH:g} of the largest kept:")
    c = r["comp"]["S0"]
    say(f"  {len(c['w'])} lines, {c['f'][0]/1e3:.2f} to {c['f'][-1]/1e3:.2f} kHz, each with its own k(omega) on S0 or A0.")
    say("  Error against a 10 ms period and lines down to 1e-6 (x = 0 to 3 m, t = -20 to 1400 us),")
    say(f"  as a share of the burst amplitude: S0 {syn['S0']:.1e}, A0 {syn['A0']:.1e}.")
    say(f"  The page sums the same lines (float32) at {r['nx']} points ({r['dx']*1e3:g} mm) along the plate")
    say(f"  for every frame; against numpy at three moments: largest difference {page:.1e}.")
    say(f"  Echo widths (-6 dB of the envelope): burst {r['w6_burst']*1e6:.1f} us, S0 echo {ec['S0']['w6']*1e6:.1f} us,")
    say(f"  A0 echo {ec['A0']['w6']*1e6:.1f} us ({ec['A0']['w6']/r['w6_burst']:.1f} times the burst).")
    say(f"  Burst band (-6 dB of the spectrum): {r['band'][0]:.1f} to {r['band'][1]:.1f} kHz.")
    say(f"  Defect at D = {D_DEF:g} m: reflection {R_DEF:g}, transmission sqrt(1 - R^2) = {T_DEF:.3f}, frequency")
    say("  independent, no mode conversion; the transducer end does not reflect (the record stops")
    say("  once the echo is back).")
    say("")
    say("DISPLAY")
    say(f"  Model time shown {SLOW_PAGE:,.0f} x slower, as Figure 13 (b) ({SLOW_PAGE / SLOW:g} x the {SLOW:,.0f} the SHM guide uses), said on the page.")
    say(f"  Plate {X_END:g} m long drawn at {PPM} units/m; its thickness")
    say(f"  is drawn {r['exag']:g} times enlarged (said in the parameter line).")
    say("  The plate is a thin slab in an oblique view, as Figure 4 draws its plate (5 Oct 2026): its top face")
    say("  recedes 14 by 10 units and carries the front face's field, sheared onto it; the model is plane strain,")
    say("  so the wave is the same across the plate's width, and the defect, a notch across the width, cuts the")
    say("  top face from edge to edge. Crimson marks the defect and its echo alone (5 Oct 2026): the operating")
    say("  points and their slopes navy, the burst band steel, the A1 cut-on grey as in Figure 4.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "guided_ut.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
