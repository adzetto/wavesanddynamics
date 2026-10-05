"""Figure 1 of "From Bridges to Photons" (from-bridges-to-photons): the double slit.

His caption: "Figure 1. Double-slit interference as a mode-shape problem.
(a) With the path unrecorded, waves from slits A and B superpose coherently
and the screen intensity shows fringes. (b) With the slits tagged by
perpendicular polarizations, the two contributions cannot cancel and the
intensity becomes a smooth sum of two single-slit (sinc^2) envelopes. The
intensity profiles are computed from the two-source superposition."

Model (lengths in wavelengths). A line source 100 wavelengths in front of an
opaque screen with two slits, a = 1.2 wide and d = 4.8 apart centre to
centre (A above, B below); the detecting screen L = 12 behind them. Each
slit's field is the 2D Huygens-Fresnel (first Rayleigh-Sommerfeld)
superposition over its aperture,

    U_s(x, y) = (ik/2) Int_slit U_inc(0, y') H1(k rho) x / rho dy',

U_inc = H0(k r) the source's own field; the field is time harmonic,
Re{U e^{-i w t}}. (a) One polarization: the field is U_A + U_B and the
screen intensity |U_A + U_B|^2. (b) Perpendicular polarizations: the two
fields cannot cancel and the intensity is |U_A|^2 + |U_B|^2. Photons land one
at a time with the probability density of that intensity on the screen
(fixed seeds; arrival times a Poisson process of rising rate), and a
histogram of where they land builds up to it.

Run: python tools/numfig/ph_slits.py  (writes content/anim/nf-ph-slits.html
and .webp and tools/numfig/ph_slits.check.txt, and runs the overlap check;
--look also writes frames; --quick <t ...> only writes the page and frames at
its poster and at those times, while designing)
"""
import base64
import os
import sys

import numpy as np
from scipy.special import hankel1

import common

NAME = "ph-slits"
HERE = os.path.dirname(os.path.abspath(__file__))

K = 2 * np.pi              # wavenumber, lengths in wavelengths
A_W = 1.2                  # slit width a
D_S = 4.8                  # slit separation d, centre to centre
S_SRC = 100.0              # the source, this far in front of the slits
L_SCR = 12.0               # the screen, this far behind them
Y_SCR = 11.0               # the screen's half height
H_ENV = 1 / 6              # the field's envelope grid
RHO0 = 0.5                 # its regularised range compensation, sqrt(rho + rho0)
NQ = 800                   # Gauss-Legendre points per slit
DY = 0.01                  # the screen's fine grid
DC = 0.05                  # the curves' grid on the page

N_PH = 10000               # photons per screen
N_BIN = 88                 # histogram bins over the screen (0.25 wavelength each)
N_REF = 800                # the histogram's scale: counts over max(n, N_REF)
SEEDS = (1927, 1961)       # (a), (b): Davisson and Germer; Joensson's electron double slit
T_P0 = 0.9                 # page s: the first photons may land
FIRST_S = 4.0              # photons expected in the first second
BUILD = 6.5                # page s: when the last is expected
CYCLE = 10.0               # page s: one build, hold and fade
PERIOD = 1.0               # page s per optical period
LAM = 19.0                 # drawing units per wavelength


def u_inc(x, y):
    """The source's field H0(k r), the source at (-S_SRC, 0)."""
    return hankel1(0, K * np.hypot(x + S_SRC, y))


def slit_field(x, y, yc, a=A_W, n=NQ, src=u_inc):
    """U at the points (x, y), x > 0, from the slit centred at yc: the 2D
    first Rayleigh-Sommerfeld integral, Gauss-Legendre over the aperture."""
    g, w = np.polynomial.legendre.leggauss(n)
    ys, ws = yc + a / 2 * g, a / 2 * w
    uin = src(np.zeros_like(ys), ys)
    x = np.asarray(x, float)[..., None]
    y = np.asarray(y, float)[..., None]
    rho = np.sqrt(x * x + (y - ys) ** 2)
    return (0.5j * K * hankel1(1, K * rho) * x / rho * (uin * ws)).sum(-1)


def field(x, y, yc, a=A_W, n=NQ, src=u_inc, block=4000):
    """slit_field over many points, in blocks (memory)."""
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    out = np.empty(x.shape, complex)
    fx, fy, fo = x.ravel(), y.ravel(), out.reshape(-1)
    for i in range(0, fx.size, block):
        fo[i:i + block] = slit_field(fx[i:i + block], fy[i:i + block], yc, a, n, src)
    return out


def fraunhofer(theta, a=A_W, d=D_S, both=True):
    """Two slits under a normal plane wave, far field, 2D, per unit angle
    (first Rayleigh-Sommerfeld, so a cos^2 obliquity):
    cos^2 th sinc^2(pi a sin th / lam) cos^2(pi d sin th / lam); `both`
    False gives the sum of the two single slits, cos^2 th sinc^2 / 2."""
    s = np.sin(theta)
    env = np.cos(theta) ** 2 * np.sinc(a * s) ** 2
    return env * np.cos(np.pi * d * s) ** 2 if both else env / 2


def model():
    u0 = abs(u_inc(0.0, 0.0))                                   # the incident amplitude at the slits
    ys = np.round(np.arange(-Y_SCR, Y_SCR + DY / 2, DY), 10)
    ua = field(np.full_like(ys, L_SCR), ys, +D_S / 2) / u0
    ub = ua[::-1].copy()                                        # B is A mirrored: the source is on the axis
    ia = np.abs(ua + ub) ** 2
    ib = np.abs(ua) ** 2 + np.abs(ub) ** 2
    # A's field on a grid, as its envelope U e^{-ik rho} sqrt(rho + rho0): smooth
    gx = np.arange(0, L_SCR + H_ENV / 2, H_ENV)
    gy = np.arange(-Y_SCR, Y_SCR + H_ENV / 2, H_ENV)
    X, Yg = np.meshgrid(gx, gy, indexing="ij")
    U = np.zeros(X.shape, complex)
    inner = X > 0
    U[inner] = field(X[inner], Yg[inner], +D_S / 2) / u0
    edge = ~inner                                               # the aperture plane: its boundary values
    inside = np.abs(Yg[edge] - D_S / 2) < A_W / 2
    U[edge] = np.where(inside, u_inc(0.0, Yg[edge]) / u0, 0)
    rho = np.hypot(X, Yg - D_S / 2)
    E = U * np.exp(-1j * K * rho) * np.sqrt(rho + RHO0)
    return dict(u0=u0, ys=ys, ua=ua, ub=ub, ia=ia, ib=ib, gx=gx, gy=gy, E=E)


def catmull(E, fx, fy):
    """Catmull-Rom interpolation of the grid E at fractional indices, as the page does it."""
    nx, ny = E.shape
    fx, fy = np.clip(fx, 0, nx - 1), np.clip(fy, 0, ny - 1)
    i = np.minimum(np.floor(fx).astype(int), nx - 2)
    j = np.minimum(np.floor(fy).astype(int), ny - 2)
    tx, ty = fx - i, fy - j
    cr = lambda p0, p1, p2, p3, t: p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)))
    at = lambda di, dj: E[np.clip(i + di, 0, nx - 1), np.clip(j + dj, 0, ny - 1)]   # edge samples repeat
    rows = [cr(*[at(di, dj) for di in (-1, 0, 1, 2)], tx) for dj in (-1, 0, 1, 2)]
    return cr(*rows, ty)


def photons(pdf, ys, seed):
    """N_PH landing points drawn from pdf on the screen (inverse CDF, linear
    between the fine grid's points), a place across the screen's width for
    each, and arrival times: a Poisson process whose expected count is
    n(tau) = n0 (e^{tau / tau0} - 1), FIRST_S in the first second and N_PH
    by BUILD, by time rescaling of unit exponential gaps."""
    rng = np.random.default_rng(seed)
    cdf = np.concatenate([[0], np.cumsum((pdf[1:] + pdf[:-1]) / 2 * np.diff(ys))])
    cdf /= cdf[-1]
    y = np.interp(rng.random(N_PH), cdf, ys)
    z = rng.random(N_PH)
    tau0 = tau_scale()
    n0 = FIRST_S / np.expm1(1 / tau0)
    gam = np.cumsum(rng.exponential(size=N_PH))
    tau = tau0 * np.log1p(gam / n0)
    return y, z, tau


def tau_scale():
    """tau0 with n(1) / n(BUILD) = FIRST_S / N_PH (bisection)."""
    lo, hi = 0.2, 3.0
    for _ in range(80):
        m = (lo + hi) / 2
        r = np.expm1(BUILD / m) / np.expm1(1 / m)
        lo, hi = (m, hi) if r > N_PH / FIRST_S else (lo, m)
    return (lo + hi) / 2


def b64(a, dtype):
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const LAM = D.lam, L = D.L, Y = D.Y, HD = D.d / 2, HA = D.a / 2, KW = 2 * Math.PI;
const YC = 279, FT = YC - Y * LAM, FB = YC + Y * LAM;       // the axis, the field's top and bottom
const py = y => YC - y * LAM;                               // the model's y (up) on the page
function geo(x0) {
  const src = x0 + 16, xb = x0 + 110, xs = xb + L * LAM;
  return { x0, src, xb, xs, brk: x0 + 66, sw: 34, pl: xs + 34, ax: xs + 34 + 84 };
}
const GA = geo(0), GB = geo(500);
function bytes(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
const i16 = s => new Int16Array(bytes(s).buffer), u16 = s => new Uint16Array(bytes(s).buffer), u8 = s => bytes(s);
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));

/* ---------------------------------------------------------------- the field
   A's envelope E = U e^{-ik rho} sqrt(rho + rho0) on the model's grid, rebuilt
   at the canvas's own resolution by Catmull-Rom and its carrier, as in
   ph_slits.py; B is A mirrored in the axis. Each layer keeps, per pixel, the
   phase of U (cos, sin) and a darkness from |U|: the crest lines drawn are
   where Re{U e^{-i w t}} peaks, where cos(phi - w t) is near 1. */
const EV = i16(D.env.b64), ENX = D.env.nx, ENY = D.env.ny, EH = D.env.h, ESC = D.env.scale;
const BT = .17;                                            // half the drawn screen's thickness (wavelengths)
const C0 = .35, KC = 1 / (1 - C0);                         // a crest line: ((cos(phi - w t) - C0) / (1 - C0))^3, 0 below C0
const _w = new Float64Array(4), _v = new Float64Array(4), ENV = [0, 0];
function crw(u, w) {                                       // Catmull-Rom weights at u
  const u2 = u * u, u3 = u2 * u;
  w[0] = .5 * (-u3 + 2 * u2 - u); w[1] = .5 * (3 * u3 - 5 * u2 + 2); w[2] = .5 * (-3 * u3 + 4 * u2 + u); w[3] = .5 * (u3 - u2);
}
function envAt(x, y) {                                     // Catmull-Rom of the envelope at (x, y), into ENV
  const fx = clamp(x / EH, 0, ENX - 1), fy = clamp((y + Y) / EH, 0, ENY - 1);
  const i = Math.min(ENX - 2, Math.floor(fx)), j = Math.min(ENY - 2, Math.floor(fy));
  crw(fx - i, _w); crw(fy - j, _v);
  let re = 0, im = 0;
  for (let a = 0; a < 4; a++) {                            // the grid's edge samples repeat beyond it
    const ia = Math.min(ENX - 1, Math.max(0, i - 1 + a));
    let r = 0, m = 0;
    for (let b = 0; b < 4; b++) {
      const o = 2 * (ia * ENY + Math.min(ENY - 1, Math.max(0, j - 1 + b)));
      r += _v[b] * EV[o]; m += _v[b] * EV[o + 1];
    }
    re += _w[a] * r; im += _w[a] * m;
  }
  ENV[0] = re * ESC; ENV[1] = im * ESC;
}
let F = null;                                              // the field at the canvas's resolution
function buildField(res) {
  const nx = Math.round(L * LAM * res), ny = 2 * Math.round(Y * LAM * res), n = nx * ny;
  const ac = new Float32Array(n), as = new Float32Array(n), ag = new Float32Array(n), ar = new Float32Array(n);
  const sc = new Float32Array(n), ss = new Float32Array(n), sg = new Float32Array(n);
  const ur = new Float32Array(n), ui = new Float32Array(n);
  for (let r = 0; r < ny; r++) for (let c = 0; c < nx; c++) {
    const x = (c + .5) / nx * L, y = Y - (r + .5) / ny * 2 * Y, k = r * nx + c;
    envAt(x, y);
    const er = ENV[0], ei = ENV[1], rho = Math.hypot(x, y - HD), m = 1 / Math.sqrt(rho + D.rho0);
    const cw = Math.cos(KW * rho), sw = Math.sin(KW * rho);
    ur[k] = (er * cw - ei * sw) * m; ui[k] = (er * sw + ei * cw) * m;
    ar[k] = rho;
  }
  for (let r = 0; r < ny; r++) for (let c = 0; c < nx; c++) {
    const k = r * nx + c, kb = (ny - 1 - r) * nx + c;      // B at (x, y) is A at (x, -y)
    const x = (c + .5) / nx * L, y = Y - (r + .5) / ny * 2 * Y;
    const aa = Math.hypot(ur[k], ui[k]) || 1e-9;
    ac[k] = ur[k] / aa; as[k] = ui[k] / aa;
    const back = x > BT ? 1 : 0;                           // under the drawn screen: not shown
    ag[k] = back * Math.min(1, aa * Math.sqrt(ar[k] + D.rho0) / D.n0);
    const vr = ur[k] + ur[kb], vi = ui[k] + ui[kb], va = Math.hypot(vr, vi) || 1e-9;
    sc[k] = vr / va; ss[k] = vi / va;
    sg[k] = back * Math.min(1, va * Math.sqrt(Math.hypot(x, y) + D.rho0) / D.n0);
  }
  const cv2 = document.createElement('canvas'); cv2.width = nx; cv2.height = ny;
  const g2 = cv2.getContext('2d');
  F = { res, nx, ny, ac, as, ag, ar, sc, ss, sg,
        A: { c: cv2, g: g2, img: g2.createImageData(nx, ny) },
        B: (() => { const c = document.createElement('canvas'); c.width = nx; c.height = ny; const g = c.getContext('2d'); return { c, g, img: g.createImageData(nx, ny) }; })() };
  buildSource(res);
}
/* the source's own field H0(k r): its phase is k r - pi/4 + dphi(r), the
   correction tabulated in DATA (exact, scipy) */
function h0phase(r) {
  const T = D.h0, u = r / T.dr;
  if (u >= T.v.length - 1) return KW * r - Math.PI / 4 - 1 / (8 * KW * r);
  const i = Math.floor(u), w = u - i;
  return KW * r - Math.PI / 4 + T.v[i] * (1 - w) + T.v[i + 1] * w;
}
let SZ = null;                                             // the source's zone
const NEAR = 2.2, CONE = 42 * Math.PI / 180, BAND = 3.3, BANDX = 1.9;
function buildSource(res) {
  const G = GA, x0 = G.src - 8, w = G.xb - x0, h = 2 * BAND * LAM + 8, y0 = YC - h / 2;
  const nx = Math.round(w * res), ny = Math.round(h * res), n = nx * ny;
  const c = new Float32Array(n), s = new Float32Array(n), g = new Float32Array(n), dist = new Float32Array(n);
  const zone = new Uint8Array(n);
  for (let r = 0; r < ny; r++) for (let q = 0; q < nx; q++) {
    const k = r * nx + q, px = x0 + (q + .5) / res, pyy = y0 + (r + .5) / res;
    const dx = (px - G.src) / LAM, dy = (YC - pyy) / LAM, rn = Math.hypot(dx, dy);
    let ph = 0, gain = 0, d = 0;
    if (px < G.brk && dx > 0) {                             // near the source: its circles, in a cone
      const ang = Math.abs(Math.atan2(dy, dx));
      gain = clamp((CONE - ang) / .2) * clamp((NEAR - rn) / .45) * clamp((rn - .2) / .12);
      ph = h0phase(rn); d = rn; zone[k] = 1;
    } else if (px >= G.brk) {                               // before the slits: the same source, 100 wavelengths off
      const xm = (px - G.xb) / LAM, ym = dy, r100 = Math.hypot(xm + D.s, ym);
      gain = clamp((BAND - Math.abs(ym)) / .6) * clamp((xm + BANDX) / .5) * (xm < -BT ? 1 : 0);
      ph = h0phase(r100); d = xm + BANDX; zone[k] = 2;
    }
    c[k] = Math.cos(ph); s[k] = Math.sin(ph); g[k] = gain * .85; dist[k] = d;
  }
  const cv2 = document.createElement('canvas'); cv2.width = nx; cv2.height = ny;
  const g2 = cv2.getContext('2d');
  SZ = { nx, ny, x0, y0, w, h, c, s, g, dist, zone, cv: cv2, g2, img: g2.createImageData(nx, ny) };
}
const COL = { a: hex(C.blue), b: hex(C.accent), inc: hex(C.muted) };
const inv = rgb => rgb.map(v => 1 - v / 255);
const KA = inv(COL.a), KB = inv(COL.b), KI = inv(COL.inc);
/* the intro: the source's waves open out, then the slits' fields from the
   slits to the screen (a drawing of the field along its own path) */
const REV = { n0: .08, n1: .3, b0: .16, b1: .4, f0: .34, f1: .82 };
function paintSource(cw, sw) {
  const S = SZ, d = S.img.data, n = S.nx * S.ny;
  const rn = lerp(0, NEAR + .4, seg(REV.n0, REV.n1 - REV.n0, easeOut)), rb = lerp(0, BANDX + .6, seg(REV.b0, REV.b1 - REV.b0, easeOut));
  for (let k = 0, o = 0; k < n; k++, o += 4) {
    let g = S.g[k];
    if (g > 0) {
      g *= clamp(((S.zone[k] === 1 ? rn : rb) - S.dist[k]) / .35);
      const q = (S.c[k] * cw + S.s[k] * sw - C0) * KC; g = q > 0 ? g * q * q * q : 0;
    }
    d[o] = 255 * (1 - g * KI[0]); d[o + 1] = 255 * (1 - g * KI[1]); d[o + 2] = 255 * (1 - g * KI[2]); d[o + 3] = 255;
  }
  S.g2.putImageData(S.img, 0, 0);
}
function paintField(cw, sw) {
  const { nx, ny, ac, as, ag, ar, sc, ss, sg } = F, dA = F.A.img.data, dB = F.B.img.data;
  const R = lerp(0, 19, seg(REV.f0, REV.f1 - REV.f0, easeOut)), intro = R < 19;
  for (let r = 0; r < ny; r++) {
    const ra = r * nx, rb = (ny - 1 - r) * nx;
    for (let c = 0; c < nx; c++) {
      const k = ra + c, kb = rb + c, o = 4 * k;
      let ma = 1, mb = 1, ms = 1;
      if (intro) { ma = clamp((R - ar[k]) / .8); mb = clamp((R - ar[kb]) / .8); ms = Math.max(ma, mb); }
      const q = Math.max(0, (sc[k] * cw + ss[k] * sw - C0) * KC);
      const fs = sg[k] * ms * q * q * q;                     // (a): one field, U_A + U_B
      dA[o] = 255 * (1 - fs * KA[0]); dA[o + 1] = 255 * (1 - fs * KA[1]); dA[o + 2] = 255 * (1 - fs * KA[2]); dA[o + 3] = 255;
      const qa = Math.max(0, (ac[k] * cw + as[k] * sw - C0) * KC), qb = Math.max(0, (ac[kb] * cw + as[kb] * sw - C0) * KC);
      const fa = ag[k] * ma * qa * qa * qa, fb = ag[kb] * mb * qb * qb * qb;   // (b): two fields that cannot cancel
      dB[o] = 255 * (1 - fa * KA[0]) * (1 - fb * KB[0]); dB[o + 1] = 255 * (1 - fa * KA[1]) * (1 - fb * KB[1]);
      dB[o + 2] = 255 * (1 - fa * KA[2]) * (1 - fb * KB[2]); dB[o + 3] = 255;
    }
  }
  F.A.g.putImageData(F.A.img, 0, 0); F.B.g.putImageData(F.B.img, 0, 0);
}

/* ---------------------------------------------------------------- the photons */
const PH = ['a', 'b'].map(k => {
  const p = D.ph[k], y = u16(p.y), z = u8(p.z), tt = u16(p.t), n = y.length;
  const Y2 = new Float32Array(n), T = new Float32Array(n), BIN = new Uint16Array(n);
  for (let i = 0; i < n; i++) {
    Y2[i] = -Y + 2 * Y * y[i] / 65535; T[i] = tt[i] / 1000;
    BIN[i] = Math.min(D.nbin - 1, Math.floor((Y2[i] + Y) / (2 * Y) * D.nbin));
  }
  return { y: Y2, z, t: T, bin: BIN, n, counts: new Uint16Array(D.nbin) };
});
function landed(P, tau) {                                  // how many have landed by tau (binary search)
  let lo = 0, hi = P.n;
  while (lo < hi) { const m = (lo + hi) >> 1; if (P.t[m] <= tau) lo = m + 1; else hi = m; }
  return lo;
}
function photonClock() {                                   // tau within the cycle, its start, and the fade
  if (t < D.tp0) return null;
  const k = Math.floor((t - D.tp0) / D.cycle), tau = t - D.tp0 - k * D.cycle;
  return { tau, start: D.tp0 + k * D.cycle, fade: 1 - seg(D.tp0 + k * D.cycle + D.cycle - .5, .35, easeOut) };
}

/* ---------------------------------------------------------------- the pieces */
function barrier(G, a) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.ink;
  const w = 2 * BT * LAM, x = G.xb - BT * LAM;
  ctx.fillRect(x, FT, w, py(HD + HA) - FT);
  ctx.fillRect(x, py(HD - HA), w, py(-HD + HA) - py(HD - HA));
  ctx.fillRect(x, py(-HD - HA), w, FB - py(-HD - HA));
  ctx.restore();
}
function sourceZone(G) {
  ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(SZ.cv, SZ.x0 + (G.x0 - GA.x0), SZ.y0, SZ.w, SZ.h); ctx.restore();
  const s = settle(.06, .26);
  dot(G.src, YC, 5 * (.6 + .4 * s), { color: C.ink, fill: C.ink, width: 1, alpha: clamp(s) });
  // the axis, broken where the source's 100 wavelengths are left out
  const ga = seg(.1, .3), gx = G.brk;
  line([[G.src + 8, YC], [gx - 5, YC]], { color: C.guide, width: 1, dash: [4, 4], alpha: .8 * ga });
  line([[gx + 5, YC], [G.xb - 8, YC]], { color: C.guide, width: 1, dash: [4, 4], alpha: .8 * ga });
  for (const dx of [-4, 3]) line([[gx + dx - 3, YC + 7], [gx + dx + 3, YC - 7]], { color: C.ink, width: 1.3, alpha: ga });
}
function screenPlate(G, pr) {
  const x = G.xs, w = G.sw;
  if (pr > 0) { ctx.save(); ctx.fillStyle = C.steel; ctx.fillRect(x, FT, w, (FB - FT) * pr); ctx.restore(); }
  line([[x, FT], [x, FB]], { color: C.ink, width: 2, progress: pr });
}
/* the landed dots: a dot that has landed never moves, so each panel keeps
   them in a canvas of its own at the frame's pixels (PL.base), whole blocks
   of BLK photons at a time, and only adds new blocks; it is drawn again from
   the first block when the dots' size, the frame's size or the cycle
   changes. Each frame the plate (PL.plate) is the base and the last part
   block, laid on the frame at once: the same pixels at a given t whatever
   frames came before, and one draw instead of 20,000 dots */
const BLK = 256, PL = [{}, {}];
function plateDots(g, P, i0, i1, x0, w, r, round) {
  g.beginPath();
  for (let i = i0; i < i1; i++) {
    const x = x0 + P.z[i] / 255 * w, y = py(P.y[i]);
    if (round) { g.moveTo(x + r, y); g.arc(x, y, r, 0, 2 * Math.PI); } else g.rect(x - r, y - r, 2 * r, 2 * r);
  }
  g.fill();
}
function plate(G, P, c, ns, r, round) {
  const kx = cv.width / W, ky = cv.height / H, ox = Math.floor(G.xs * kx), oy = Math.floor((FT - 3) * ky);
  const pw = Math.ceil((G.xs + G.sw) * kx) - ox + 1, ph = Math.ceil((FB + 3) * ky) - oy + 1;
  const key = `${cv.width}x${cv.height}:${r}`;
  if (c.key !== key) {
    for (const k of ['base', 'plate']) { c[k] = document.createElement('canvas'); c[k].width = pw; c[k].height = ph; }
    c.gb = c.base.getContext('2d'); c.gp = c.plate.getContext('2d');
    for (const g of [c.gb, c.gp]) { g.setTransform(kx, 0, 0, ky, -ox, -oy); g.fillStyle = C.navy; }
    c.key = key; c.blocks = 0;
  }
  const x0 = G.xs + 2.5, w = G.sw - 5, nb = Math.floor(ns / BLK);
  if (nb < c.blocks) { c.gb.save(); c.gb.setTransform(1, 0, 0, 1, 0, 0); c.gb.clearRect(0, 0, pw, ph); c.gb.restore(); c.blocks = 0; }
  if (nb > c.blocks) { plateDots(c.gb, P, c.blocks * BLK, nb * BLK, x0, w, r, round); c.blocks = nb; }
  c.gp.save(); c.gp.setTransform(1, 0, 0, 1, 0, 0); c.gp.clearRect(0, 0, pw, ph); c.gp.drawImage(c.base, 0, 0); c.gp.restore();
  plateDots(c.gp, P, nb * BLK, ns, x0, w, r, round);
  return { img: c.plate, x: ox / kx, y: oy / ky, w: pw / kx, h: ph / ky };
}
/* a dot's radius once landed: clear single dots while few have landed, fine
   grain once thousands have (the plate then shows their density); in steps
   of 1/32 of a unit, so the kept dots are drawn again only when it shows */
const grain = n => Math.round(32 * (.5 + 1.3 * clamp(1 - Math.log10(Math.max(n, 1)) / 3.3))) / 32;
function grains(G, P, tau, st, fade, c) {                  // the dots on the screen, and the fresh ones arriving
  const n = landed(P, tau);
  if (n <= 0 || fade <= 0) return n;
  // a fresh detection lands as a dot and settles into the plate; only while
  // they come few at a time (the expected rate, n0 / tau0 e^{tau / tau0})
  const x0 = G.xs + 2.5, w = G.sw - 5, hl = clamp((30 - D.n0ph / D.tau0 * Math.exp(tau / D.tau0)) / 24);
  const r = grain(n), round = r > .8;
  let ns = n;                                              // the settled ones: all but those still arriving
  if (hl > 0) while (ns > 0 && tau - P.t[ns - 1] < .32) ns--;
  const im = plate(G, P, c, ns, r, round);
  ctx.save(); ctx.globalAlpha *= fade * .82; ctx.drawImage(im.img, im.x, im.y, im.w, im.h); ctx.restore();
  for (let i = n - 1; i >= ns; i--) {
    const s = settle(st + P.t[i], .26), x = x0 + P.z[i] / 255 * w, y = py(P.y[i]);
    dot(x, y, lerp(lerp(r, 3.6, hl), r, s), { color: C.navy, fill: C.navy, width: 0, alpha: fade * lerp(1, .82, s) });
  }
  return n;
}
function histogram(G, P, n, fade) {
  const cnt = P.counts; cnt.fill(0);
  for (let i = 0; i < n; i++) cnt[P.bin[i]]++;
  if (fade <= 0 || n === 0) return;
  // counts per bin over max(n, nref) photons: the bars grow with the first
  // nref, then settle onto the probability density as n grows
  const bh = 2 * Y / D.nbin, k = D.S / (Math.max(n, D.nref) * bh);
  ctx.save(); ctx.globalAlpha *= fade; ctx.fillStyle = C.mist; ctx.beginPath();
  for (let b = 0; b < D.nbin; b++) {
    if (!cnt[b]) continue;
    const y0 = py(-Y + (b + 1) * bh), y1 = py(-Y + b * bh);
    ctx.rect(G.pl, y0, cnt[b] * k, y1 - y0);
  }
  ctx.fill(); ctx.restore();
}
function curve(G, v, color, width, pr, alpha = 1, dash = null) {
  const pts = [];
  for (let i = 0; i < v.length; i++) pts.push([G.pl + v[i] * D.S, py(-Y + i * D.dc)]);
  line(pts, { color, width, progress: pr, alpha, dash });
}
function plotAxis(G, pr) {                                // the plate's back, the histogram's zero
  line([[G.pl, FT], [G.pl, FB]], { color: C.ink, width: 1.3, progress: pr });
}
/* the position on the screen, in wavelengths: an axis right of the intensity */
function scale(G, pr) {
  line([[G.ax, FT], [G.ax, FB]], { color: C.ink, width: 1.1, progress: pr });
  const a = clamp((pr - .5) * 2);
  for (const v of [-10, -5, 0, 5, 10]) {
    line([[G.ax, py(v)], [G.ax - 5, py(v)]], { color: C.ink, width: 1.1, alpha: a });
    math(fmt(v), G.ax + 6, py(v) + 5.6, { size: 16, alpha: a });
  }
  math('y/\\lambda', G.ax, FT - 12, { size: 17, alpha: a });
}
/* his P_A and P_B, the two single-slit patterns of (b): a legend in the
   intensity's upper right, between y = 9.4 and 6.8 wavelengths, where every
   curve stays within 10 units of the plate */
function curveKey(G, a) {
  if (a <= 0) return;
  const x = G.pl + 24, y = py(9.4), w = 54, h = py(6.8) - py(9.4);
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], { color: C.guide, width: 1, fill: 'white', close: true, alpha: a });
  for (const [i, sym, col, dash] of [[0, 'P_{A}', C.blue, null], [1, 'P_{B}', C.accent, [5, 3]]]) {
    const yy = y + 20 + i * 21;
    line([[x + 6, yy - 5], [x + 22, yy - 5]], { color: col, width: 1.6, dash, alpha: a });
    math(sym, x + 27, yy, { size: 17, alpha: a });
  }
}

/* ---------------------------------------------------------------- the panels */
function panelA(ck) {
  const G = GA;
  panel('a', 18, 34, { alpha: lab(0) });
  text('Path not recorded: fringes', 53, 34, { size: 18, color: C.body, alpha: lab(.03) });
  ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(F.A.c, G.xb, FT, L * LAM, FB - FT); ctx.restore();
  sourceZone(G);
  barrier(G, seg(0, .22));
  photonsPanel(G, PH[0], ck, PL[0]);
  plotAxis(G, seg(.04, .35));
  scale(G, seg(.06, .35));
  curve(G, D.pa, C.navy, 2.2, seg(.3, .45));
  labels(G, 'Same polarization: waves add and cancel at the screen');
}
function panelB(ck) {
  const G = GB;
  line([[500, 18], [500, H - 44]], { color: C.rule, width: 1, alpha: seg(0, .3) });
  panel('b', 518, 34, { alpha: lab(.02) });
  text('Paths tagged: no fringes', 553, 34, { size: 18, color: C.body, alpha: lab(.05) });
  ctx.save(); ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(F.B.c, G.xb, FT, L * LAM, FB - FT); ctx.restore();
  sourceZone(G);
  barrier(G, seg(0, .22));
  photonsPanel(G, PH[1], ck, PL[1]);
  plotAxis(G, seg(.04, .35));
  scale(G, seg(.08, .35));
  curve(G, D.pA, C.blue, 1.4, seg(.42, .4));
  curve(G, D.pB, C.accent, 1.4, seg(.46, .4), 1, [5, 3]);
  curve(G, D.pb, C.navy, 2.2, seg(.3, .45));
  curveKey(G, lab(.6));
  // his polarization arrows: A vertical, B horizontal
  const pa = settle(.3, .28), xa = G.xb - 34;
  arrow(xa, py(HD + HA + 1.55) + 17, xa, py(HD + HA + 1.55) - 17, { color: C.blue, width: 2.4, head: 10, both: true, alpha: clamp(pa) });
  arrow(xa - 17, py(-HD - HA - 1.7), xa + 17, py(-HD - HA - 1.7), { color: C.accent, width: 2.4, head: 10, both: true, alpha: clamp(settle(.34, .28)) });
  labels(G, 'Perpendicular polarizations at A and B: the two waves cannot cancel');
}
function photonsPanel(G, P, ck, c) {
  screenPlate(G, seg(.04, .35));
  let n = 0, fade = 1;
  if (ck) { fade = ck.fade; n = grains(G, P, ck.tau, ck.start, fade, c); }
  histogram(G, P, n, fade);
  const ca = lab(.9) * (ck ? 1 : 0);
  if (ca > 0 && n > 0) {
    const s = n === 1 ? '1 photon' : `${n.toLocaleString('en-US')} photons`;
    text(s, G.xs + G.sw / 2 + 28, FT - 12, { size: 16, color: C.body, align: 'center', alpha: ca * fade });
  }
}
function labels(G, sentence) {
  const la = lab(.2), lb = lab(.26);
  text('A', G.xb - 12, py(HD + HA) - 7 + rise(la), { size: 18, align: 'right', alpha: la });
  text('B', G.xb - 12, py(-HD - HA) + 20 - rise(la), { size: 18, align: 'right', alpha: la });
  const y = FB + 24;
  text('Source', Math.max(G.src, G.x0 + 30), y + rise(lb), { size: 17, align: 'center', alpha: lb });
  text('Screen', G.xs + G.sw, y + rise(lb), { size: 17, align: 'right', alpha: lb });
  text('Intensity', G.pl + 44, y + rise(lb), { size: 17, align: 'center', alpha: lb });
  const ls = lab(.45), at = sentence.indexOf(': ') + 1;
  [sentence.slice(0, at), sentence.slice(at + 1)].forEach((s, i) =>
    text(s, G.x0 + 18, FB + 51 + i * 21 + rise(ls), { size: 17, color: C.body, alpha: ls }));
}

let lastW = -1;
function draw() {
  if (cv.width !== lastW) { lastW = cv.width; buildField(clamp(cv.width / W, .5, 1)); }
  const ph = KW * t / D.period, cw = Math.cos(ph), sw = Math.sin(ph);
  paintSource(cw, sw); paintField(cw, sw);
  const ck = photonClock();
  panelA(ck); panelB(ck);
  math(D.params, 18, H - 9, { size: 15, color: C.muted, alpha: lab(.5) });
}
boot();
"""


def main():
    rep = []
    say = rep.append
    m = model()
    ys, ua, ub, ia, ib = m["ys"], m["ua"], m["ub"], m["ia"], m["ib"]
    norm_a = np.trapezoid(ia, ys)
    norm_b = np.trapezoid(ib, ys)
    pdf_a, pdf_b = ia / norm_a, ib / norm_b
    # the page's curves: every DC wavelength
    step = int(round(DC / DY))
    pa, pb = pdf_a[::step], pdf_b[::step]
    pA, pB = (np.abs(ua) ** 2 / norm_b)[::step], (np.abs(ub) ** 2 / norm_b)[::step]
    S = 76.0 / pdf_a.max()                                      # drawing units per unit of probability density
    # the display's darkness: A's field alone at its brightest on the screen, 0.85
    rho_s = np.hypot(L_SCR, ys - D_S / 2)
    n0 = float((np.abs(ua) * np.sqrt(rho_s + RHO0)).max() / 0.85)
    # the envelope, int16
    E = m["E"]
    esc = float(np.abs(E).max() / 32000)
    env = np.stack([E.real, E.imag], -1) / esc
    env16 = np.round(env).astype("<i2")
    # H0's phase beyond k r - pi/4, for the source's circles
    rr = np.arange(0, 3.0 + 1e-9, 0.01)
    zz = K * np.maximum(rr, 1e-3)
    dphi = np.angle(hankel1(0, zz) * np.exp(-1j * (zz - np.pi / 4)))
    # photons
    tau0 = tau_scale()
    ph = {}
    stats = {}
    for key, pdf, seed in (("a", pdf_a, SEEDS[0]), ("b", pdf_b, SEEDS[1])):
        y, z, tau = photons(pdf, ys, seed)
        yq = np.round((y + Y_SCR) / (2 * Y_SCR) * 65535).astype("<u2")
        tq = np.round(tau * 1000).astype("<u2")
        zq = np.round(z * 255).astype("u1")
        ph[key] = {"y": b64(yq, "<u2"), "z": b64(zq, "u1"), "t": b64(tq, "<u2")}
        stats[key] = (y, tau)
    last = max(stats["a"][1][-1], stats["b"][1][-1])
    poster = round(T_P0 + last + 0.6, 2)
    assert last + 0.9 < CYCLE - 0.5, last
    data = {
        "lam": LAM, "L": L_SCR, "Y": Y_SCR, "a": A_W, "d": D_S, "s": S_SRC, "rho0": RHO0, "n0": n0,
        "period": PERIOD, "tp0": T_P0, "cycle": CYCLE, "poster": poster, "nbin": N_BIN, "S": S, "dc": DC,
        "nref": N_REF, "tau0": tau0, "n0ph": FIRST_S / np.expm1(1 / tau0),
        "env": {"nx": int(E.shape[0]), "ny": int(E.shape[1]), "h": H_ENV, "scale": esc, "b64": b64(env16, "<i2")},
        "h0": {"dr": 0.01, "v": np.round(dphi, 6).tolist()},
        "pa": np.round(pa, 5).tolist(), "pb": np.round(pb, 5).tolist(),
        "pA": np.round(pA, 5).tolist(), "pB": np.round(pB, 5).tolist(),
        "ph": ph,
        "params": (r"a = %g\lambda,\ \ d = %g\lambda,\ \ L = %g\lambda\rm{;\ source\ %g}\lambda\rm{\ from\ the\ slits;\ "
                   r"%s\ photons\ per\ screen;\ one\ optical\ period\ per\ second}" % (A_W, D_S, L_SCR, S_SRC, f"{N_PH:,}")),
    }
    return data, m, stats, dict(pdf_a=pdf_a, pdf_b=pdf_b, S=S, n0=n0, tau0=tau0, poster=poster, last=last, esc=esc)


def minima(y, v, lim):
    """Local minima of v(y) for |y| < lim, refined by a parabola."""
    out = []
    for i in range(1, v.size - 1):
        if abs(y[i]) < lim and v[i] < v[i - 1] and v[i] <= v[i + 1]:
            a, b, c = v[i - 1], v[i], v[i + 1]
            den = a - 2 * b + c
            out.append(y[i] + (0.5 * (a - c) / den if den else 0) * (y[1] - y[0]))
    return np.array(out)


def two_point_dark(m, L=L_SCR, d=D_S):
    """Where the path difference from the two slit centres is (m + 1/2)
    wavelengths on the screen x = L (bisection)."""
    f = lambda y: np.hypot(L, y + d / 2) - np.hypot(L, y - d / 2) - (m + 0.5)
    lo, hi = 0.0, 40.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


def validate(m, data, stats, info):
    """The checks of ph_slits.check.txt."""
    from scipy import stats as st
    L = []
    say = L.append
    ys, ua, ub, ia, ib = m["ys"], m["ua"], m["ub"], m["ia"], m["ib"]
    pdf_a, pdf_b = info["pdf_a"], info["pdf_b"]

    # 1. the superposition against Fraunhofer, far away, under a normal plane wave
    plane = lambda x, y: np.ones_like(np.asarray(y, float), complex)
    th = np.radians(np.linspace(-60, 60, 481))
    R = 1e5
    fa = field(R * np.cos(th), R * np.sin(th), +D_S / 2, src=plane)
    fb = field(R * np.cos(th), R * np.sin(th), -D_S / 2, src=plane)
    two = np.abs(fa + fb) ** 2
    one = np.abs(fa) ** 2 + np.abs(fb) ** 2
    e_two = np.abs(two / two.max() - fraunhofer(th) / fraunhofer(np.array(0.0))).max()
    e_one = np.abs(one / one.max() - fraunhofer(th, both=False) / fraunhofer(np.array(0.0), both=False)).max()
    # the absolute level: the 2D far field of one slit, |U|^2 = (k/2)^2 (2 / (pi k R)) cos^2 th a^2 sinc^2
    lvl = np.abs(fa[240]) ** 2 / ((K / 2) ** 2 * 2 / (np.pi * K * R) * A_W ** 2)

    # 2. the page's screen against the two-source superposition of two Fraunhofer slits: each
    #    slit's own far field (a^2 / (lambda L) = 0.12), sinc^2 about its own centre, lit at the
    #    source's angle, the two added with their exact path lengths (his caption's model)
    def slit_far(yc, y, L=L_SCR):
        r = np.hypot(L, y - yc)
        th = np.arctan2(y - yc, L)
        ui = u_inc(0.0, yc) / u0
        thi = np.arctan2(yc, S_SRC)                                  # the light's angle at the slit
        return (0.5j * K * np.sqrt(2 / (np.pi * K * r)) * np.exp(1j * (K * r - 3 * np.pi / 4))
                * np.cos(th) * ui * A_W * np.sinc(A_W * (np.sin(th) - np.sin(thi))))
    u0 = m["u0"]
    fA, fB = slit_far(+D_S / 2, ys), slit_far(-D_S / 2, ys)
    s_a = np.abs(np.abs(fA + fB) ** 2 - ia).max() / ia.max()
    s_b = np.abs(np.abs(fA) ** 2 + np.abs(fB) ** 2 - ib).max() / ia.max()
    s_A = np.abs(np.abs(fA) ** 2 - np.abs(ua) ** 2).max() / (np.abs(ua) ** 2).max()
    # 2b. the whole double slit's Fraunhofer formula (angles from the midpoint) holds only far
    #     away: the page's screen is at d^2 / (lambda L) = 1.9; the same angles on screens further off
    far = []
    thg = np.radians(np.linspace(-40, 40, 321))
    for Lf in (L_SCR, 4 * L_SCR, 16 * L_SCR, 64 * L_SCR):
        xx, yy = np.full_like(thg, Lf), Lf * np.tan(thg)
        ga = field(xx, yy, +D_S / 2) / u0
        gb = field(xx, yy, -D_S / 2) / u0
        rr = np.hypot(xx, yy)
        va = np.abs(ga + gb) ** 2 * rr
        vb = (np.abs(ga) ** 2 + np.abs(gb) ** 2) * rr
        far.append((Lf, np.abs(va / va.max() - fraunhofer(thg) / fraunhofer(np.array(0.0))).max(),
                    np.abs(vb / vb.max() - fraunhofer(thg, both=False) / fraunhofer(np.array(0.0), both=False)).max()))
    mins = minima(ys, ia, 10.5)
    mins = mins[mins > 0]
    fr_mins = [L_SCR * np.tan(np.arcsin((k + 0.5) / D_S)) for k in range(len(mins))]
    tp_mins = [two_point_dark(k) for k in range(len(mins))]
    vis = (ia.max() - ia[np.argmin(np.abs(ys - mins[0]))]) / (ia.max() + ia[np.argmin(np.abs(ys - mins[0]))])
    peaks_b = int(((ib[1:-1] > ib[:-2]) & (ib[1:-1] >= ib[2:])).sum())
    cross = np.trapezoid(2 * np.real(ua * np.conj(ub)), ys) / np.trapezoid(ib, ys)

    # 3. convergence: the screen's intensity with 400 and 1600 Gauss points against 800
    u0 = m["u0"]
    yc = ys[::10]
    conv = []
    for n in (400, 1600):
        un = field(np.full_like(yc, L_SCR), yc, +D_S / 2, n=n) / u0
        conv.append((n, np.abs(np.abs(un + un[::-1]) ** 2 - ia[::10]).max() / ia.max()))
    yn = np.linspace(D_S / 2 - 1.2, D_S / 2 + 1.2, 145)                # the grid's first column behind the slit
    n8 = field(np.full_like(yn, H_ENV), yn, +D_S / 2) / u0
    n32 = field(np.full_like(yn, H_ENV), yn, +D_S / 2, n=3200) / u0
    near_conv = np.abs(n8 - n32).max() / np.abs(n32).max()

    # 4. the page's field: the envelope grid and Catmull-Rom against the integral itself
    rng = np.random.default_rng(0)
    px = rng.uniform(0.02, L_SCR, 3000)
    py_ = rng.uniform(-Y_SCR, Y_SCR, 3000)
    direct = field(px, py_, +D_S / 2) / u0
    rho = np.hypot(px, py_ - D_S / 2)
    env = catmull(m["E"], px / H_ENV, (py_ + Y_SCR) / H_ENV)
    rec = env * np.exp(1j * K * rho) / np.sqrt(rho + RHO0)
    err = np.abs(rec - direct) * np.sqrt(rho + RHO0) / np.abs(m["E"]).max()
    # and just behind the slit, where the drawn screen's back face is (x = 0.17)
    nx_ = rng.uniform(0.17, 1.0, 3000)
    ny_ = rng.uniform(D_S / 2 - 1.4, D_S / 2 + 1.4, 3000)
    nd = field(nx_, ny_, +D_S / 2) / u0
    nr = np.hypot(nx_, ny_ - D_S / 2)
    ne = np.abs(catmull(m["E"], nx_ / H_ENV, (ny_ + Y_SCR) / H_ENV) * np.exp(1j * K * nr) / np.sqrt(nr + RHO0) - nd)
    ne = ne * np.sqrt(nr + RHO0) / np.abs(m["E"]).max()
    near = [(lo, hi, ne[(nx_ >= lo) & (nx_ < hi)].max()) for lo, hi in ((0.17, 0.35), (0.35, 0.5), (0.5, 1.0))]
    q16 = (np.abs(np.round(m["E"].real / info["esc"]) * info["esc"] - m["E"].real).max()) / np.abs(m["E"]).max()

    # 5. the photons
    ph_lines = []
    for key, pdf in (("a", pdf_a), ("b", pdf_b)):
        y, tau = stats[key]
        cdf = np.concatenate([[0], np.cumsum((pdf[1:] + pdf[:-1]) / 2 * np.diff(ys))])
        cdf /= cdf[-1]
        ks = st.kstest(y, lambda v: np.interp(v, ys, cdf))
        edges = np.linspace(-Y_SCR, Y_SCR, N_BIN + 1)
        obs = np.histogram(y, edges)[0]
        exp = np.diff(np.interp(edges, ys, cdf)) * y.size
        keep = exp >= 5
        chi = st.chisquare(obs[keep], exp[keep] * obs[keep].sum() / exp[keep].sum())
        n1 = int((tau <= 1.0).sum())
        ph_lines.append((key, ks.statistic, ks.pvalue, chi.statistic, int(keep.sum()) - 1, chi.pvalue, n1, tau[-1]))

    k = K
    say("Figure 1 (nf-ph-slits): double-slit interference as a mode-shape problem")
    say("generator: tools/numfig/ph_slits.py")
    say("")
    say("MODEL (lengths in wavelengths, lambda = 1, k = 2 pi)")
    say(f"  a line source (a point in 2D) at x = -{S_SRC:g}, on the axis; an opaque screen at x = 0 with two slits")
    say(f"  of width a = {A_W:g}, centres y = +{D_S/2:g} (A) and -{D_S/2:g} (B), so d = {D_S:g}; the detecting screen at")
    say(f"  x = L = {L_SCR:g}, drawn over |y| < {Y_SCR:g}. ad / (lambda L) = {A_W*D_S/L_SCR:.2f}: the far-field side of")
    say("  the document's ad / (lambda L) > 1 for two separate bands.")
    say("  incident field U_inc = H0(k r); each slit's field behind the screen is the first Rayleigh-Sommerfeld")
    say("  (Huygens-Fresnel) integral in 2D over its aperture, with U_inc in the slit and 0 on the screen:")
    say("    U_s(x, y) = (i k / 2) Int_slit U_inc(0, y') H1(k rho) x / rho dy',  rho = |(x, y) - (0, y')|")
    say("  time harmonic, the field Re{U e^{-i w t}}. (a) one polarization: U = U_A + U_B, intensity |U_A + U_B|^2.")
    say("  (b) perpendicular polarizations: E = U_A e_A + U_B e_B with e_A . e_B = 0, so |E|^2 = |U_A|^2 + |U_B|^2.")
    say(f"  all fields divided by |U_inc| at the slits ({u0:.6f}). B is A mirrored in the axis (the source is on it).")
    say(f"  quadrature: {NQ} Gauss-Legendre points per slit; screen sampled every {DY:g}.")
    say("")
    say("CHECK 1, the superposition against the Fraunhofer formula (normal plane wave, R = 1e5, |theta| <= 60 deg)")
    say("  2D far field: I(theta) = cos^2 theta sinc^2(pi a sin theta) cos^2(pi d sin theta) (the cos^2 is the")
    say("  Rayleigh-Sommerfeld obliquity), and without the interference term cos^2 theta sinc^2(pi a sin theta) / 2")
    say(f"    |U_A + U_B|^2, normalised, against it: largest difference {e_two:.1e} of the peak")
    say(f"    |U_A|^2 + |U_B|^2 against the sum of the two single-slit envelopes: largest difference {e_one:.1e}")
    say(f"    the level on axis: |U_A|^2 / ((k/2)^2 (2 / (pi k R)) a^2) = {lvl:.6f} (1 exactly in the far field)")
    say("")
    say(f"CHECK 2, the page's screen (source {S_SRC:g} away, screen at L = {L_SCR:g}) against the two-source")
    say("  superposition of two Fraunhofer slits: each slit's own far field (a^2 / (lambda L) = "
        f"{A_W**2/L_SCR:.2f}), sinc^2 about")
    say("  its own centre and lit at the source's angle, the two added with their exact path lengths:")
    say("    U_s = (i k / 2) sqrt(2 / (pi k r_s)) e^{i (k r_s - 3 pi / 4)} cos th_s U_inc(0, y_s) a sinc(a (sin th_s - sin th_i))")
    say(f"    (a) |U_A + U_B|^2: largest difference {s_a*100:.2f} % of its peak; (b) |U_A|^2 + |U_B|^2: {s_b*100:.2f} %")
    say(f"    one slit, |U_A|^2 against its sinc^2 envelope: {s_A*100:.2f} % of its peak (absolute levels, not rescaled)")
    say("CHECK 2b, the whole double slit's Fraunhofer formula, angles from the midpoint, holds only far away (the page's")
    say(f"  screen is at d^2 / (lambda L) = {D_S**2/L_SCR:.1f}); the same angles, |theta| <= 40 deg, on screens further off,")
    say("  intensity times r, normalised:")
    for Lf, ea, eb in far:
        say(f"    L = {Lf:5g}: (a) largest difference {ea*100:5.2f} % of the peak, (b) {eb*100:5.2f} %")
    say("    the differences fall with L; what is left far off comes from the source's own distance, 100")
    say(f"    wavelengths, which lights the slits {np.degrees(np.arctan2(D_S / 2, S_SRC)):.1f} deg off normal (a plane wave: CHECK 1)")
    say("  dark fringes of (a), y > 0: the computed minima, the exact two-point condition |r_A - r_B| = (m + 1/2),")
    say("  and Fraunhofer d sin theta = (m + 1/2):")
    for i_, (y0, y1, y2) in enumerate(zip(mins, tp_mins, fr_mins)):
        say(f"    m = {i_}: computed {y0:.3f}, two-point {y1:.3f} ({y0-y1:+.3f}), Fraunhofer {y2:.3f} ({y0-y2:+.3f})")
    say(f"  fringe visibility at the centre (V = (I_max - I_min) / (I_max + I_min), first dark fringe): {vis:.4f}")
    say(f"  (b) has {peaks_b} maximum on the screen: one smooth hump, no fringes")
    say(f"  the interference term 2 Re(U_A U_B*) integrates over the screen to {cross*100:+.2f} % of the total:")
    say("  the fringes move the light, they do not make or lose it")
    say("")
    say("CONVERGENCE")
    for n, e in conv:
        say(f"  (a) on the screen with {n} Gauss points instead of {NQ}: largest change {e:.1e} of the peak")
    say(f"  the grid's first column behind the slit (x = 1/6): {NQ} against 3200 points, largest change {near_conv:.1e}")
    say("")
    say("THE FIELD ON THE PAGE")
    say(f"  A's field on a grid every 1/{round(1/H_ENV)} wavelength, {m['E'].shape[0]} x {m['E'].shape[1]} points, stored as its envelope")
    say(f"  E = U e^{{-i k rho}} sqrt(rho + {RHO0:g}) (rho from A's centre), int16 (rounding {q16:.1e} of max |E|); the page")
    say("  rebuilds U at its own pixel size by Catmull-Rom and the exact carrier e^{i k rho}; B is A mirrored.")
    say("  rebuilt against the integral at 3000 random points, in units of max |E|:")
    for lo in (0.0, 0.5, 1.0, 2.0):
        sel = rho > lo
        say(f"    beyond {lo:g} wavelength of the slit's centre: largest error {err[sel].max():.1e}")
    say("  crest lines: where Re{U e^{-i w t}} peaks, darkness g ((cos(phi - w t) - 0.35) / 0.65)^3, phi = arg U;")
    say(f"  g = min(1, |U| sqrt(rho + {RHO0:g}) / n0) takes out the 2D spreading 1 / sqrt(rho) so the far lobes stay")
    say(f"  visible (rho from each slit in (b), from the midpoint in (a)); n0 = {info['n0']:.4f}: A alone peaks at 0.85")
    say("  on the screen, so where A and B add in (a) the lines are darkest and where they cancel they vanish.")
    say("  colour is polarization: (a) one field, blue; (b) A blue, B crimson; the source's field grey.")
    say("  crest lines rather than the engine's DIVERGING map: its crimson arm would mean a negative field in (a)")
    say("  and slit B's light in (b); as crest lines one colour means one polarization in both panels.")
    say("  the opaque screen is drawn 0.34 wavelength thick, centred on the aperture plane; the field within 0.17")
    say("  of the plane lies under it, where the grid's error is largest. Just behind it, in units of max |E|:")
    for lo, hi, e in near:
        say(f"    {lo:g} <= x < {hi:g}: largest error {e:.1e}")
    say("  the source's field H0(k r) is drawn near the source (r < 2.2, a 42 deg cone) and in front of the slits")
    say(f"  (the last 1.9 wavelengths, |y| < 3.3, {S_SRC:g} from the source); the break mark on the axis stands for the")
    say(f"  {S_SRC - 2.2 - 1.9:.1f} wavelengths between. The phase of H0 beyond k r - pi/4 is tabulated from scipy for r < 3.")
    say("")
    say("THE PHOTONS")
    say(f"  {N_PH} per screen; each lands at y drawn from the screen's intensity as a probability density (inverse")
    say("  CDF, linear between the fine grid's points) and anywhere across the drawn plate's width; arrival")
    say(f"  times a Poisson process with expected count n(tau) = n0 (e^{{tau/tau0}} - 1), tau0 = {info['tau0']:.4f} s,")
    say(f"  {FIRST_S:g} expected in the first second and {N_PH} by {BUILD:g} s (time rescaling of unit exponential gaps);")
    say(f"  seeds {SEEDS[0]} (a) and {SEEDS[1]} (b).")
    for key, ks, kp, chi, dof, cp, n1, tl in ph_lines:
        say(f"    ({key}) Kolmogorov-Smirnov against the density: D = {ks:.4f}, p = {kp:.2f}; histogram of {N_BIN} bins,")
        say(f"        chi^2 = {chi:.1f} on {dof} degrees of freedom, p = {cp:.2f}; {n1} landed in the first second,")
        say(f"        the last at {tl:.3f} s")
    say(f"  the histogram: bins of {2*Y_SCR/N_BIN:g} wavelength, counts / (max(n, {N_REF}) bin), in the same units as the")
    say("  curve (the probability density), so its bars grow with the first photons and then settle onto the curve.")
    say("  both panels use one density scale: the same light, in (a) moved into fringes twice the smooth level.")
    say("  the screen carries a position scale, y / lambda = -10 ... 10, right of each intensity plot; in (b) the two")
    say("  single-slit patterns are named as the document names them, P_A (solid, blue) and P_B (dashed, crimson),")
    say("  P = P_A + P_B, in a legend in the plot's upper right (from 6.8 to 9.4 wavelengths up, where every curve")
    say("  stays within 10 units of the plate).")
    say("  drawing: landed dots never move, so each panel keeps them in a canvas of its own at the frame's pixels,")
    say(f"  whole blocks of 256 photons at a time, and lays it on the frame in one draw (the last part block and the")
    say("  dots still arriving are drawn each frame); the field is rebuilt at the frame's resolution up to 1 pixel per")
    say("  unit (a full-screen frame scales it up, smoothly).")
    say("")
    say("TIME")
    say(f"  one optical period per second of the page (for 600 nm light, time slowed {3e8/600e-9:.0e} times); the crests")
    say(f"  move lambda per second. The intro draws the field along its own path: the source's waves (0.08 to 0.4 s),")
    say("  then the slits' fields out to the screen (0.34 to 0.82 s): a drawing, not the switch-on transient, which")
    say("  would take the light 12 periods (12 s here) to reach the screen. The photons start at 0.9 s; the cycle")
    say(f"  is {CYCLE:g} s: they land, the histogram holds, then fades in 0.35 s and starts again.")
    say(f"  poster (print, reduced motion) at t = {info['poster']} s: all {N_PH} photons landed in both panels.")
    return L


def page():
    data, m, stats, info = main()
    title = "Figure 1: Double-slit interference as a mode-shape problem"
    aria = ("Two double-slit experiments computed from a wave model. (a) Waves from slits A and B overlap and cancel "
            "along dark lines, and single photons landing on the screen build up a histogram of bright and dark "
            "fringes. (b) With the slits' polarizations perpendicular, the blue and red waves overlap without "
            "cancelling, and the photons build up one smooth hump, the sum of the two single-slit patterns.")
    common.build_html(NAME, title, aria, 1000, 600, data, JS)
    print("poster", info["poster"], "last photon", round(info["last"], 3))
    if "--quick" in sys.argv:                                   # a look while designing: no still, no check
        print(common.frames(NAME, [info["poster"]] + [float(v) for v in sys.argv[sys.argv.index("--quick") + 1:]]))
        return data, m, stats, info
    lines = validate(m, data, stats, info)
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(HERE, "ph_slits.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    print("still:", common.still(NAME))                         # raises on any collision up to the poster
    # the moments after the poster: the photons fading, the plate empty, the next build starting
    late = [9.0, 10.5, 10.8, 11.2, 12.0, 14.0]
    res = common.overlaps(NAME, late)
    faults = [f"{w}: {r}" for w, r in res.items() if r["labels"] or r["crossings"]]
    lines += ["", "OVERLAP (engine.js ?overlap, common.still and common.overlaps)",
              f"  clean at the poster and every 0.25 s from 0.25 to {np.ceil(max(3.0, info['poster']) / .25) * .25:.2f} s"
              " (common.still),",
              "  and at " + ", ".join(f"{v:g}" for v in late) + " s (the fade and the next build): "
              + ("clean" if not faults else "; ".join(faults)),
              "  no label on a label and no stroke through a label; nothing allowed."]
    with open(os.path.join(HERE, "ph_slits.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    if faults:
        raise RuntimeError("overlaps after the poster: " + "; ".join(faults))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.2, 0.45, 0.7, 1.2, 2.5, 4.5, 6.2]))
    return data, m, stats, info


if __name__ == "__main__":
    if "--model" in sys.argv:
        import time
        t0 = time.time()
        mm = model()
        print("model", round(time.time() - t0, 1), "s", mm["E"].shape)
    else:
        page()
