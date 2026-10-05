"""Figure 13: coverage of bulk wave testing against guided wave testing, on
one real length scale (the 10 mm steel plate of Figure 12, a 2 m span).

(a) Bulk wave testing. A 10 mm, 5 MHz contact probe (circular piston) on the
plate. Its field is the Rayleigh integral in the edge wave form (a direct plane
wave under the face minus the wave diffracted from the rim),

    p / (rho c v0) = exp(ikz) H(a - r)
                     - (1/2pi) int a (a - r cos f) / (r^2 + a^2 - 2 a r cos f)
                                   exp(ik sqrt(z^2 + r^2 + a^2 - 2 a r cos f)) df,

checked against the Rayleigh surface integral itself. Averaged over the probe's
band (5 MHz, 60 % at -6 dB) it gives the pulsed beam; its -6 dB pulse echo
width at each depth is the insonified zone. The probe steps along the plate at
an index below the narrowest zone, so coverage builds up position by position,
and a flaw lights up only while a zone covers it.

His note (5 Oct 2026): "Figure 13 -> bulk wave testing => slide a bit slower
and animate vertical waves so people can see it's vertical wave prop. easier",
with a sketch of a probe on the top face and short horizontal fronts stacked
under it down to the bottom face. So the probe now dwells at its first
positions and at the positions over each flaw, and at each of those it sends
its pulse: the probe's band in time (a Gaussian, 5 MHz, 60 % at -6 dB), drawn
as its crests and troughs, plane fronts as wide as the beam's -6 dB zone at
each depth, running straight down through the thickness at c_L, back from the
lamination's top where one lies under the beam (earlier) and from the back
wall elsewhere, and up again to the probe; time slowed 2 x 10^5. Between the
dwells it steps on briskly; which positions exist and what each covers is the
model, the pace is designed.

(b) Guided wave testing. The S0 mode of Figure 12 (3 cycle, 50 kHz, from
guided_ut.py: same Rayleigh-Lamb roots, same Fourier synthesis) is launched once
from the transducer at x = 0 and sweeps the span to the next sensor position at
2 m; each flaw reflects (single scattering), and the echoes arrive at the
transducer at the burst centre + 2 x / c_g.

Run: python tools/numfig/ut_coverage.py
"""
import os

import numpy as np
from scipy.signal import hilbert

import common
import guided_ut as gu

# ------------------------------------------------------------------ (a) probe
C_L = gu.C_L                 # the same steel
F_PROBE = 5e6                # probe centre frequency (Hz)
D_PROBE = 10e-3              # probe diameter (m)
A_PROBE = D_PROBE / 2
BW = 0.60                    # -6 dB fractional bandwidth of the probe's spectrum
INDEX = 5e-3                 # scan index (m), below the narrowest -6 dB zone
SPAN = 2.0                   # span between the two sensor positions (m)
THICK = gu.D_PLATE
# flaws: laminations (flat, planar) inside the plate: x centre, depth, length, height
FLAWS = [dict(x=0.60, z=6.0e-3, L=24e-3, h=1.2e-3), dict(x=1.40, z=3.5e-3, L=24e-3, h=1.2e-3)]
R_FLAW = 0.25                # S0 displacement reflection of each flaw (schematic, frequency independent)
T_FLAW = np.sqrt(1 - R_FLAW ** 2)
SLOW = gu.SLOW_PAGE           # (b): Figure 12's own slowing (7,000), the same S0 wave in the same plate
PPM, PH_DRAW = gu.PPM, gu.PH_DRAW
# ------------------------------------------------------------------ (a) the pulse and the pace
SLOW_A = 2e5                 # the pulse's time slowed: 5 us of the model per second
EXT_MIN = 0.1                # the pulse's crests and troughs drawn: those above a tenth of its peak
VIS = 0.32                   # the glide (s) of a step to a position where the probe dwells
FIRE = 0.06                  # after the glide, the pulse leaves
PAUSE = 0.15                 # after the pulse is home, the next step
N_START = 2                  # the first positions, each with its pulse
D_NEAR, Q_NEAR = 0.36, 0.58  # beside a dwell: the step's time, and its ratio from one step to the next
R_FAST = 70.0                # positions per second in between
POSTER_TAU = 0.75            # the still: the pulse at flaw 2's middle position, 0.75 us in (its echo half way up)


def piston(r, z, k, nphi=4096):
    """CW pressure over rho c v0 of a baffled circular piston of radius
    A_PROBE at radius r and depth z (arrays of one shape), edge wave form."""
    r = np.asarray(r, float)
    r = np.where(np.abs(r - A_PROBE) < 1e-9, A_PROBE, r)     # on the rim: H = 1/2, kernel 1/2
    z = np.asarray(z, float)
    phi = (np.arange(nphi) + 0.5) * 2 * np.pi / nphi
    R2 = r[..., None] ** 2 + A_PROBE ** 2 - 2 * A_PROBE * r[..., None] * np.cos(phi)
    ker = (A_PROBE ** 2 - A_PROBE * r[..., None] * np.cos(phi)) / R2
    edge = (ker * np.exp(1j * k * np.sqrt(z[..., None] ** 2 + R2))).mean(-1)
    direct = np.where(r < A_PROBE, np.exp(1j * k * z), np.where(r == A_PROBE, 0.5 * np.exp(1j * k * z), 0))
    return direct - edge


def rayleigh_surface(x, z, k, nr=200, nphi=400):
    """The Rayleigh integral over the face itself (Gauss-Legendre in radius,
    trapezoid in angle): the reference the edge wave form is checked against."""
    g, w = np.polynomial.legendre.leggauss(nr)
    rr, wr = A_PROBE * (g + 1) / 2, w * A_PROBE / 2
    ph = (np.arange(nphi) + 0.5) * 2 * np.pi / nphi
    X, Y = rr[:, None] * np.cos(ph), rr[:, None] * np.sin(ph)
    R = np.sqrt((x - X) ** 2 + Y ** 2 + z * z)
    val = (np.exp(1j * k * R) / R * rr[:, None]).sum(1) * (2 * np.pi / nphi)
    return (-1j * k / (2 * np.pi)) * (val * wr).sum()


def pulsed_beam(xs, zs, nf=25):
    """RMS amplitude of the pulsed field over the probe's Gaussian band, on the
    grid xs (lateral) by zs (depth)."""
    sig = BW * F_PROBE / (2 * np.sqrt(2 * np.log(2)))
    fs = np.linspace(F_PROBE - 3 * sig, F_PROBE + 3 * sig, nf)
    wt = np.exp(-(fs - F_PROBE) ** 2 / (2 * sig ** 2))
    X, Z = np.meshgrid(np.abs(xs), zs)
    E = np.zeros_like(X)
    for f, w in zip(fs, wt):
        E += w ** 2 * np.abs(piston(X, Z, 2 * np.pi * f / C_L)) ** 2
    return np.sqrt(E / (wt ** 2).sum())


def zone_halfwidth(xs, A):
    """-6 dB pulse echo half width at each depth: the outermost x where A^2 is
    at least half its maximum at that depth (the near field's ripples inside
    are covered by the neighbouring positions: see union_coverage)."""
    out = []
    xp = xs >= 0
    for row in A:
        pe = (row[xp] / row.max()) ** 2
        j = np.nonzero(pe >= 0.5)[0][-1]
        out.append(np.interp(0.5, [pe[j + 1], pe[j]], [xs[xp][j + 1], xs[xp][j]]))
    return np.array(out)


def union_coverage(xs, A, index):
    """The worst pulse echo response (dB, relative to each depth's maximum)
    anywhere in the plate when the probe sits every `index`: at each depth and
    each x in one index cell, the best of all positions."""
    pe = (A / A.max(1, keepdims=True)) ** 2
    dx = xs[1] - xs[0]
    m = int(round(index / dx))
    worst = 1.0
    for row in pe:
        cells = [max(np.interp(x0 - j * index, xs, row) for j in range(-8, 9)) for x0 in np.arange(m) * dx]
        worst = min(worst, min(cells))
    return 10 * np.log10(worst)


# ------------------------------------------------------------------ (b) guided wave
def gw_field(comp, x, tm):
    """S0 along the plate at one time: incident, transmitted past each flaw,
    and the two echoes (single scattering)."""
    x1, x2 = FLAWS[0]["x"], FLAWS[1]["x"]
    ph = lambda s: comp["w"] * tm - np.outer(s, comp["k"]) + comp["p"]
    S = lambda s: (comp["a"] * np.cos(ph(s))).sum(1)
    inc, e1, e2 = S(x), S(2 * x1 - x), S(2 * x2 - x)
    R, T = R_FLAW, T_FLAW
    return np.where(x < x1, inc + R * e1 + T * T * R * e2,
                    np.where(x < x2, T * inc + T * R * e2, T * T * inc))


def gw_received(comp, t):
    x1, x2 = FLAWS[0]["x"], FLAWS[1]["x"]
    return (gu.synth(comp, 0.0, t) + gu.synth(comp, 2 * x1, t, R_FLAW)
            + gu.synth(comp, 2 * x2, t, T_FLAW ** 2 * R_FLAW))


# ------------------------------------------------------------------ (a) the pulse
def pulse():
    """The probe's pulse in time: its Gaussian band (F_PROBE, BW at -6 dB) is
    g(s) = exp(-s^2 / (2 sigma^2)) cos(2 pi f0 s), sigma = 1/(2 pi sigma_f),
    sigma_f = BW f0 / (2 sqrt(2 ln 2)). Its crests and troughs (s, g) where
    |g| >= EXT_MIN: the fronts the page draws."""
    from scipy.optimize import brentq
    sf = BW * F_PROBE / (2 * np.sqrt(2 * np.log(2)))
    st = 1 / (2 * np.pi * sf)
    g = lambda s: np.exp(-s ** 2 / (2 * st ** 2)) * np.cos(2 * np.pi * F_PROBE * s)
    dg = lambda s: -np.exp(-s ** 2 / (2 * st ** 2)) * (s / st ** 2 * np.cos(2 * np.pi * F_PROBE * s)
                                                       + 2 * np.pi * F_PROBE * np.sin(2 * np.pi * F_PROBE * s))
    s = (np.arange(-4000, 4001) + 0.5) * (5 * st / 4000)          # no grid point on s = 0
    d = dg(s)
    ext = [brentq(dg, s[i], s[i + 1], xtol=1e-18) for i in range(len(s) - 1) if d[i] * d[i + 1] < 0]
    ext = [(e, g(e)) for e in ext if abs(g(e)) >= EXT_MIN]
    return st, ext


# ------------------------------------------------------------------ (a) the pace
def schedule(n, lit, t_life):
    """When each probe position begins (s, from the first step), its glide, and
    the moment its pulse leaves (-1 where the probe does not dwell). It dwells,
    and sends its pulse, at the first N_START positions and at the three
    positions round the middle of each flaw's lit range; beside those the
    steps are slow (D_NEAR, shrinking Q_NEAR times a step), and in between they
    run at R_FAST. Only the pace is designed; which positions exist and what
    each covers is the model."""
    mids = [int(round(np.mean(l))) for l in lit]
    dwell_at = sorted(set(range(N_START)) | {m + d for m in mids for d in (-1, 0, 1)})
    D = VIS + FIRE + t_life + PAUSE
    idx = np.arange(n)
    dist = np.min(np.abs(idx[:, None] - np.array(dwell_at)[None, :]), axis=1)
    dwell = np.where(dist == 0, D, np.maximum(1 / R_FAST, D_NEAR * Q_NEAR ** np.maximum(dist - 1, 0)))
    tstep = np.concatenate([[0.0], np.cumsum(dwell)[:-1]])
    vis = np.minimum(VIS, 0.7 * dwell)
    vis[0] = 0.0
    tfire = np.where(dist == 0, tstep + vis + FIRE, -1.0)
    tfire[0] = 0.30                                    # the first position: the probe is there from the start
    return tstep, vis, tfire, float(np.cumsum(dwell)[-1]), dwell_at, D


def r5(a):
    """Rounded as build_html rounds what the page gets (5 places)."""
    return np.round(np.asarray(a, float), 5)


def fronts_a(ip, tau, bz, bw, ext, cl, flaws, index_mm, thick_mm):
    """The port of the page's frontsA(): [kind (0 down, 1 flaw echo, 2 back wall
    echo), depth (mm), x from, x to (m), |g|] for the pulse at position ip,
    tau us after its centre left the face."""
    def halfw(z):
        if z <= bz[0]:
            return bw[0]
        if z >= bz[-1]:
            return bw[-1]
        p = (z - bz[0]) / (bz[1] - bz[0])
        i = min(len(bz) - 2, int(np.floor(p)))
        return bw[i] + (bw[i + 1] - bw[i]) * (p - i)

    def minus(spans, fl):
        s = spans
        for f in fl:
            n = []
            for a, b in s:
                if f["x1"] <= a or f["x0"] >= b:
                    n.append([a, b])
                else:
                    if f["x0"] > a:
                        n.append([a, f["x0"]])
                    if f["x1"] < b:
                        n.append([f["x1"], b])
            s = n
        return s

    xs = (ip + 1) * index_mm / 1000
    fl = [dict(x0=f["x"] - f["L_mm"] / 2000, x1=f["x"] + f["L_mm"] / 2000, zt=f["z_mm"] - f["h_mm"] / 2) for f in flaws]
    span = lambda z: [xs - halfw(z) / 1000, xs + halfw(z) / 1000]
    out = []
    for se, ge in ext:
        zd = cl * (tau - se)
        A = abs(ge)
        if zd < 0:
            continue
        if zd <= thick_mm:
            for a, b in minus([span(zd)], [f for f in fl if f["zt"] < zd]):
                out.append([0, zd, a, b, A])
        for f in fl:
            zr = 2 * f["zt"] - zd
            if zd > f["zt"] and zr >= 0:
                a, b = span(zr)
                a2, b2 = max(a, f["x0"]), min(b, f["x1"])
                if b2 > a2:
                    out.append([1, zr, a2, b2, A])
        zb = 2 * thick_mm - zd
        if zd > thick_mm and zb >= 0:
            for a, b in minus([span(zb)], fl):
                out.append([2, zb, a, b, A])
    return out


JS = r"""
const G = DATA;
G.tc = G.tc_us * 1e-6; G.tmax = G.tmax_us * 1e-6; G.dt_tr = G.dt_tr_us * 1e-6;
const T0 = 0.15, SLOW = G.slow, SLOWA = G.slow_a, M0 = -20e-6, S = .28;
const PX0 = 90, PPM = G.ppm, PH = G.ph, ZS = PH / G.thick_mm;   // ZS: drawing units per mm of depth
const XU = x => PX0 + x * PPM;
const PYA = 76, YB = 378, PYB = YB + 104;                                     // the two strips
const ACC = C.accent, FLAW = '#781E2C', LBL = 16, TICK = 16, HEAD = 17;      // type: labels, ticks, headings
const STOPS = ['#043052', '#2E6A9E', '#9CBBD6', null, '#DEABAB', '#B03F4D', '#651020'];
const lutWith = mid => _ramp(STOPS.map(s => _hex(s || mid)));
const LUT_STEEL = lutWith(C.steel), LUT_DONE = lutWith(C.mist);
/* the beam under the probe, pale (steel to mist): the pulse's fronts are drawn on it */
const BLUT = _ramp(['#E3EBF2', '#D3DFEA', '#BFD1E1', '#A9C3DA'].map(_hex));

/* ------------------------------------------------------------ data */
const COMP = { w: b64f32(G.c.w), k: b64f32(G.c.k), a: b64f32(G.c.a), p: b64f32(G.c.p) };
const TRACE = b64f32(G.trace);
const NX = G.nx, DXM = G.dx, U = new Float64Array(NX);
const I1 = Math.round(G.flaws[0].x / DXM), I2 = Math.round(G.flaws[1].x / DXM);
const BEAM = b64i8(G.beam.a), BNX = G.beam.nx, BNZ = G.beam.nz;
const BZ = G.beam.z_mm, BW = G.beam.w_mm;
const XP = i => (i + 1) * G.index_mm / 1000;                  // probe position i (m): the first flush with the end
function halfw(z) {                                            // the -6 dB zone's half width (mm) at depth z (mm)
  if (z <= BZ[0]) return BW[0];
  if (z >= BZ[BZ.length - 1]) return BW[BW.length - 1];
  const p = (z - BZ[0]) / (BZ[1] - BZ[0]), i = Math.min(BZ.length - 2, Math.floor(p));
  return BW[i] + (BW[i + 1] - BW[i]) * (p - i);
}

/* the S0 burst along the plate at model time tm: incident (passing each flaw
   with T), the echo from flaw 1 (R) and from flaw 2 (T R, then T again past
   flaw 1): the Fourier sum, each line rotated along x */
function fieldAt(tm) {
  U.fill(0);
  const { w, k, a, p } = COMP, n = w.length, R = G.R, T = G.T, x1 = G.flaws[0].x, x2 = G.flaws[1].x;
  for (let j = 0; j < n; j++) {
    const kj = k[j], aj = a[j], ph = w[j] * tm + p[j], cd = Math.cos(kj * DXM), sd = Math.sin(kj * DXM);
    let c = Math.cos(ph), s = Math.sin(ph);
    for (let i = 0; i < NX; i++) {
      U[i] += (i < I1 ? aj : i < I2 ? aj * T : aj * T * T) * c;
      const c2 = c * cd + s * sd; s = s * cd - c * sd; c = c2;
    }
    for (const [xf, iEnd, g1, g2] of [[x1, I1, R, R], [x2, I2, T * T * R, T * R]]) {
      const b = ph - 2 * kj * xf;
      c = Math.cos(b); s = Math.sin(b);
      for (let i = 0; i < iEnd; i++) {
        U[i] += aj * (i < I1 ? g1 : g2) * c;
        const c2 = c * cd - s * sd; s = s * cd + c * sd; c = c2;
      }
    }
  }
  return U;
}

/* the bulk probe's pulse at position ip, tau us after its centre left the
   face: its crests and troughs (DATA ext: s, g) as plane fronts [kind, depth
   (mm), x from, x to (m), |g|], each as wide as the -6 dB zone at its depth,
   running straight down at c_L; a column of the beam over a lamination turns
   back at its top (kind 1, the echo), every other column at the back wall
   (kind 2); up again to the probe */
function frontsA(ip, tau) {
  const xs = XP(ip), D = G.thick_mm, c = G.cl, out = [];
  const fl = G.flaws.map(f => ({ x0: f.x - f.L_mm / 2000, x1: f.x + f.L_mm / 2000, zt: f.z_mm - f.h_mm / 2 }));
  const span = z => [xs - halfw(z) / 1000, xs + halfw(z) / 1000];
  const minus = (spans, cut) => {
    let s = spans;
    for (const f of cut) {
      const n = [];
      for (const [a, b] of s) {
        if (f.x1 <= a || f.x0 >= b) n.push([a, b]);
        else { if (f.x0 > a) n.push([a, f.x0]); if (f.x1 < b) n.push([f.x1, b]); }
      }
      s = n;
    }
    return s;
  };
  for (const [se, ge] of G.ext) {
    const zd = c * (tau - se), A = Math.abs(ge);
    if (zd < 0) continue;
    if (zd <= D) for (const [a, b] of minus([span(zd)], fl.filter(f => f.zt < zd))) out.push([0, zd, a, b, A]);
    for (const f of fl) {
      const zr = 2 * f.zt - zd;
      if (zd > f.zt && zr >= 0) {
        const [a, b] = span(zr), a2 = Math.max(a, f.x0), b2 = Math.min(b, f.x1);
        if (b2 > a2) out.push([1, zr, a2, b2, A]);
      }
    }
    const zb = 2 * D - zd;
    if (zd > D && zb >= 0) for (const [a, b] of minus([span(zb)], fl)) out.push([2, zb, a, b, A]);
  }
  return out;
}

/* ------------------------------------------------------------ the clock
   One loop: the guided wave shot (model time, slowed SLOW times) and the bulk
   probe's scan start together; the scan's pace is designed (dwelling, with a
   pulse, at its first positions and over each flaw; brisk in between), the
   positions are the model's */
const SHOT0 = .3, SHOT1 = SHOT0 + (G.shot_end_us * 1e-6 - M0) * SLOW;
const SCAN0 = .3, SCAN1 = SCAN0 + G.tscan, HOLD = 2.4, FADE = .8;
const PER = SCAN1 + HOLD + FADE;
function now() {
  if (t < T0) return { loop: -1, tau: -1, b: T0 };
  const tt = t - T0, loop = Math.floor(tt / PER);
  return { loop, tau: tt - loop * PER, b: T0 + loop * PER };
}
function probeIndex(st) {                    // the position the probe is at (or heading to)
  if (st.tau < SCAN0) return -1;
  const s = st.tau - SCAN0, ts = G.tstep;
  let lo = 0, hi = ts.length - 1;
  if (s >= ts[hi]) return hi;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (ts[m] > s) hi = m; else lo = m; }
  return lo;
}
/* the pulse where the probe dwells: us since its centre left the face (its
   leading crest leaves at the position's firing time); null elsewhere */
function tauAt(st, ip) {
  if (ip < 0 || st.loop < 0 || G.tfire[ip] < 0) return null;
  return G.ext[0][0] + (st.tau - SCAN0 - G.tfire[ip]) * 1e6 / SLOWA;
}
const alive = tau => tau !== null && tau >= G.ext[0][0] && tau <= G.tend_us;
const fadeOut = st => st.loop < 0 ? 1 : 1 - seg(st.b + SCAN1 + HOLD, FADE);
const POSTER_T = T0 + SCAN0 + G.poster_scan;

/* ------------------------------------------------------------ helpers */
function offscreen(w, h) { const cvs = document.createElement('canvas'); cvs.width = w; cvs.height = h; const g = cvs.getContext('2d'); return { cvs, g, img: g.createImageData(w, h) }; }
const FIM = offscreen(NX, 3), BAR = offscreen(256, 1), BIM = offscreen(BNX, BNZ);
for (let i = 0; i < 256; i++) BAR.img.data.set([LUT_STEEL[3 * i], LUT_STEEL[3 * i + 1], LUT_STEEL[3 * i + 2], 255], 4 * i);
BAR.g.putImageData(BAR.img, 0, 0);
for (let q = 0; q < BNX * BNZ; q++) { const li = Math.round(BEAM[q] / 127 * 255) * 3; BIM.img.data.set([BLUT[li], BLUT[li + 1], BLUT[li + 2], 255], 4 * q); }
BIM.g.putImageData(BIM.img, 0, 0);
function cutEdge(x, y0, y1, o = {}) {
  const pts = [], n = 6, a = 4;
  for (let i = 0; i <= n; i++) pts.push([x + (i % 2 ? a : -a) * (i > 0 && i < n ? 1 : 0), lerp(y0 - 3, y1 + 3, i / n)]);
  line(pts, { color: C.ink, width: 1.3, ...o });
}
/* the plate as a thin slab in an oblique view, as Figures 4 and 12 draw it: its top face
   recedes DX3, DY3 up and to the right; the front face is the section the strip shows */
const DX3 = 14, DY3 = 10;
function topPath(py, xa, xb) {                  // the top face over x = xa ... xb (canvas), as a path
  ctx.beginPath(); ctx.moveTo(xa, py); ctx.lineTo(xb, py); ctx.lineTo(xb + DX3, py - DY3); ctx.lineTo(xa + DX3, py - DY3); ctx.closePath();
}
function topCut(x, py, o = {}) {                // the top face's edge at the cut: zigzag, as the front's
  const pts = [], n = 4, a = 3;
  for (let i = 0; i <= n; i++) { const v = i / n, e = (i % 2 ? a : -a) * (i > 0 && i < n ? 1 : 0); pts.push([x + DX3 * v + e, py - DY3 * v]); }
  line(pts, { color: C.ink, width: 1.3, ...o });
}
function plate(py, prog, fillA) {
  const x0 = XU(0), x1 = XU(G.xend);
  ctx.save(); ctx.globalAlpha *= fillA; ctx.fillStyle = C.steel; ctx.fillRect(x0, py, x1 - x0, PH); topPath(py, x0, x1); ctx.fill(); ctx.restore();
  return () => {
    line([[x1, py], [x0, py], [x0, py + PH], [x1, py + PH]], { color: C.ink, width: 1.6, progress: prog });
    line([[x0, py + PH], [x1, py + PH]], { color: C.ink, width: 2.4, progress: prog });
    line([[x0, py], [x0 + DX3, py - DY3], [x1 + DX3, py - DY3]], { color: C.ink, width: 1.2, progress: prog });
    cutEdge(x1, py, py + PH, { alpha: clamp(prog * 3 - 2) }); topCut(x1, py, { alpha: clamp(prog * 3 - 2) });
  };
}
function lengthAxis(py, t0) {
  const ya = py + PH + 16;
  line([[XU(0), ya], [XU(2), ya]], { color: C.ink, width: 1.3, progress: seg(t0, .35) });
  for (const v of [0, .5, 1, 1.5, 2]) {
    const a = seg(t0 + .08 + v * .1, .25);
    line([[XU(v), ya], [XU(v), ya - 5]], { color: C.ink, width: 1.1, alpha: a });
    keepMath(fmt(v), XU(v), ya + 21, { size: TICK, align: 'center', alpha: a });
  }
  keepMath('x\\ (\\rm{m})', XU(2) + 34, ya + 21, { size: 17, alpha: seg(t0 + .3, .25) });
}
/* a flaw (a lamination), drawn in the strip: dashed until found, filled after */
function flawMark(x, py, zmm, state, alpha, glow) {
  const cx = XU(x), cy = py + zmm * ZS, rx = 6, ry = 3;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.ellipse(cx, cy, rx, ry, 0, 0, 2 * Math.PI);
  if (state > 0) { ctx.fillStyle = mix(C.steel, ACC, state); ctx.fill(); }
  ctx.strokeStyle = FLAW; ctx.lineWidth = 1.1 + 1.2 * glow; if (state < .5) ctx.setLineDash([2.5, 2]); ctx.stroke();
  if (glow > 0) { ctx.setLineDash([]); ctx.globalAlpha *= glow; ctx.strokeStyle = C.amber; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.ellipse(cx, cy, rx + 3 + 3 * glow, ry + 3 + 3 * glow, 0, 0, 2 * Math.PI); ctx.stroke(); }
  ctx.restore();
}
function mix(a, b, s) { const A = _hex(a), B = _hex(b); return `rgb(${A.map((v, i) => Math.round(lerp(v, B[i], s))).join(',')})`; }
function swatchText(x, y, s, o = {}) { text(s, x, y, { size: 17, color: C.body, ...o }); }
/* labels a line passes behind: their ink boxes, kept as they are drawn;
   gapLine() (vertical) and gapSeg() (any) are lines broken 3 units clear of each */
const KEEP = [];
function keepText(s, x, y, o) {
  text(s, x, y, o);
  if (!(o.alpha > 0)) return;
  ctx.save(); ctx.font = font(o); ctx.textAlign = o.align || 'left'; const q = ctx.measureText(s); ctx.restore();
  KEEP.push([x - q.actualBoundingBoxLeft, y - q.actualBoundingBoxAscent, x + q.actualBoundingBoxRight, y + q.actualBoundingBoxDescent]);
}
function keepMath(s, x, y, o) {                   // math; its box from its width and size
  const w = math(s, x, y, o), x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  if (o.alpha > 0) KEEP.push([x0 - 1, y - o.size * .95, x0 + w + 1, y + o.size * .45]);
}
function gapLine(x, y0, y1, o) {
  const cuts = KEEP.filter(b => x > b[0] - 3 && x < b[2] + 3).map(b => [b[1] - 3, b[3] + 3]).sort((p, q) => p[0] - q[0]);
  let y = y0;
  for (const [p, q] of cuts) { if (p > y + .5) line([[x, y], [x, Math.min(p, y1)]], o); y = Math.max(y, q); if (y >= y1) return; }
  if (y1 > y + .5) line([[x, y], [x, y1]], o);
}
function gapSeg(p, q, o) {
  const dx = q[0] - p[0], dy = q[1] - p[1], cuts = [];
  for (const b of KEEP) {
    let t0 = 0, t1 = 1, ok = true;
    for (const [pp, qq] of [[-dx, p[0] - (b[0] - 3)], [dx, b[2] + 3 - p[0]], [-dy, p[1] - (b[1] - 3)], [dy, b[3] + 3 - p[1]]]) {
      if (pp === 0) { if (qq < 0) { ok = false; break; } continue; }
      const r = qq / pp;
      if (pp < 0) { if (r > t1) { ok = false; break; } if (r > t0) t0 = r; } else { if (r < t0) { ok = false; break; } if (r < t1) t1 = r; }
    }
    if (ok && t1 > t0) cuts.push([t0, t1]);
  }
  cuts.sort((u, v) => u[0] - v[0]);
  const P = u => [p[0] + dx * u, p[1] + dy * u];
  let s = 0;
  for (const [a, b] of cuts) { if (a > s) line([P(s), P(a)], o); s = Math.max(s, b); }
  if (s < 1) line([P(s), q], o);
}
/* the engine's dim(), its knockout as deep as the label's ink and opaque from
   the first frame, so the line never shows through the label while both fade
   in (as Figures 11 and 12) */
function dimk(x1, x2, y, label, o) {
  const { color, alpha, size } = o;
  dim(x1, x2, y, '', { color, alpha });
  if (alpha <= 0) return;
  const w = math(label, 0, -1e4, { size, alpha: 0 }), bx = (x1 + x2) / 2 - w / 2 - 4, by = y - size * .62;
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(bx, by, w + 8, size * 1.42); ctx.restore();
  KEEP.push([bx, by, bx + w + 8, by + size * 1.42]);
  math(label, (x1 + x2) / 2, y + size * .34, { size, align: 'center', color, alpha });
}

/* ------------------------------------------------------------ (a) bulk wave */
function panelA(st) {
  panel('a', 20, 34, { alpha: seg(0, .25) });
  text('bulk wave testing', 58, 34, { size: HEAD, color: C.body, alpha: settle(.05, S) });
  const fo = fadeOut(st), ip = probeIndex(st), tau = tauAt(st, ip);
  const drawOutline = plate(PYA, seg(0, .4), seg(.05, .25));
  // coverage: every zone so far (index below the narrowest zone: they join up)
  // the probe and the window under it settle in at every loop's start, as in the first (they
  // are drawn from the scan's first position on)
  const pa = settle(st.b + SCAN0, S) * fo;
  let xs = null;
  if (ip >= 0) {
    const tsI = st.b + SCAN0 + G.tstep[ip];
    const g = ip === 0 ? 1 : settle(tsI, G.vis[ip]);
    xs = ip === 0 ? XP(0) : lerp(XP(ip - 1), XP(ip), g);
    const edge = xs + G.wmid_mm / 2000;
    ctx.save(); ctx.globalAlpha *= pa; ctx.fillStyle = C.mist;
    ctx.fillRect(XU(0), PYA, XU(Math.min(edge, G.span)) - XU(0), PH); ctx.restore();
  }
  // flaws: lit while a zone covers them, found afterwards
  G.flaws.forEach((f, n) => {
    const [a0, a1] = G.lit[n];
    let state = 0, glow = 0;
    if (ip >= a0) state = 1;
    if (ip >= a0 && ip <= a1) glow = 1;
    else if (ip > a1) glow = 1 - seg(st.b + SCAN0 + G.tstep[a1 + 1], .5);
    flawMark(f.x, PYA, f.z_mm, state * fo, settle(.2 + .05 * n, S), glow * fo);
  });
  // the probe's insonified zone (-6 dB, pulse echo) beneath it; where it
  // dwells, the zone fills as its pulse goes down
  if (xs !== null) {
    const zw = G.beam.w_mm, zz = G.beam.z_mm, pts = [];
    for (let q = 0; q < zz.length; q++) pts.push([XU(xs + zw[q] / 1000), PYA + zz[q] * ZS]);
    for (let q = zz.length - 1; q >= 0; q--) pts.push([XU(xs - zw[q] / 1000), PYA + zz[q] * ZS]);
    // (a lamination wider than the beam stops it: below is its shadow)
    const zlim = G.flaws.reduce((m, f) => {
      const zt = f.z_mm - f.h_mm / 2, w = halfw(zt) / 1000;
      return f.x - f.L_mm / 2000 <= XP(ip) - w && f.x + f.L_mm / 2000 >= XP(ip) + w ? Math.min(m, zt) : m;
    }, G.thick_mm);
    const za = seg(st.b + SCAN0, .3) * fo, zg = tau === null ? G.thick_mm : clamp(G.cl * (tau - G.ext[0][0]), 0, zlim);
    if (zg > 0) {
      ctx.save(); ctx.globalAlpha *= .9 * za; ctx.beginPath(); ctx.rect(XU(xs) - 20, PYA, 40, zg * ZS); ctx.clip();
      ctx.fillStyle = C.blue; ctx.beginPath();
      pts.forEach(([x, y], q) => q ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill(); ctx.restore();
    }
  }
  drawOutline();
  lengthAxis(PYA, .05);
  if (xs !== null) {
    const pw = G.probe_mm / 1000 * PPM;
    ctx.save(); ctx.globalAlpha *= pa; ctx.fillStyle = C.navy; ctx.fillRect(XU(xs) - pw / 2, PYA - 11, pw, 11); ctx.restore();
    text('probe', XU(xs), PYA - 19, { size: 17, color: C.body, align: 'center', alpha: pa });
    spy(st, xs, pa, ip, tau);
  }
  // counters: positions, coverage
  const ca = st.loop <= 0 ? settle(.3, S) : settle(st.b + .05, S);   // at each loop's start they settle in again
  const npos = ip + 1, cov = ip < 0 ? 0 : Math.min(100, (XP(ip) + G.wmid_mm / 2000) / G.span * 100);
  const cw = covLine(950, 34, cov, ca * fo);
  text(`probe position ${Math.max(0, npos)} of ${G.npos}`, 950 - cw - 40, 34, { size: HEAD, color: C.body, align: 'right', alpha: ca * fo });
  legend(92, 170, seg(.5, .3));
  math(G.params_a, 92, 272, { size: 15, color: C.muted, alpha: seg(.6, .3) });
  // the pulse's slowing, and its clock while it runs
  text(G.slowtxt_a, 92, 306, { size: 15, color: C.muted, alpha: seg(.5, .3) });
  if (alive(tau)) {
    const ta = fo * clamp((tau - G.ext[0][0]) / .08) * clamp((G.tend_us - tau) / .08);
    math(`t = ${Math.max(0, tau).toFixed(2)}\\,\\rm{µs}`, 464, 306, { size: HEAD, align: 'right', alpha: ta });
  }
}
function covLine(xr, y, pct, a) {
  const s = `coverage ${Math.round(pct)}%`;
  const w = text(s, xr, y, { size: HEAD, color: C.body, align: 'right', alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.mist; ctx.fillRect(xr - w - 25, y - 12, 17, 12); ctx.restore();
  line([[xr - w - 25, y - 12], [xr - w - 8, y - 12], [xr - w - 8, y], [xr - w - 25, y], [xr - w - 25, y - 12]], { color: C.ink, width: .8, alpha: a });
  return w + 25;
}
function legend(x, y, a) {
  if (a <= 0) return;
  const w = 380, h = 76;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(x, y, w, h); ctx.restore();
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], { color: C.ink, width: 1, alpha: a });
  const r1 = y + 29, r2 = y + 59, c1 = x + 14, c2 = x + 184;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.mist; ctx.fillRect(c1, r1 - 12, 22, 13);
  ctx.fillStyle = C.blue; ctx.globalAlpha *= .9; ctx.fillRect(c1 + 8, r2 - 14, 6, 17); ctx.restore();
  swatchText(c1 + 32, r1, 'inspected', { alpha: a });
  swatchText(c1 + 32, r2, '\u22126 dB zone', { alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.ellipse(c2 + 10, r1 - 5, 7, 3.5, 0, 0, 2 * Math.PI); ctx.fillStyle = ACC; ctx.fill();
  ctx.strokeStyle = FLAW; ctx.lineWidth = 1.1; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(c2 + 10, r2 - 5, 7, 3.5, 0, 0, 2 * Math.PI); ctx.setLineDash([2.5, 2]); ctx.stroke(); ctx.restore();
  swatchText(c2 + 26, r1, 'flaw found', { alpha: a });
  swatchText(c2 + 26, r2, 'flaw not yet found', { alpha: a });
}
/* the plate under the probe, to scale: the computed pulsed beam (pale) and
   its -6 dB pulse echo zone, in a window 36 mm wide moving with the probe;
   where the probe dwells, its pulse runs down and back in it */
const SPY = { x: 520, y: 182, w: 432, mm: 12 };
function spy(st, xs, a0, ip, tau) {
  const a = a0 * seg(.45, .3);
  if (a <= 0) return;
  const hw = SPY.w / 2 / SPY.mm, h = G.thick_mm * SPY.mm, cx = SPY.x + SPY.w / 2, xr = SPY.x + SPY.w;
  // the window: centred on the probe, but it stops at the plate's free end
  const wc = Math.max(xs, hw / 1000), X = x => cx + (x - wc) * 1000 * SPY.mm, px = X(xs);
  const x0 = Math.max(SPY.x, X(0));                               // left edge of steel in the window
  const wx0 = XU(wc - hw / 1000), wx1 = XU(wc + hw / 1000);
  line([[wx0, PYA - 2], [wx1, PYA - 2], [wx1, PYA + PH + 2], [wx0, PYA + PH + 2], [wx0, PYA - 2]], { color: C.guide, width: 1, alpha: a });
  gapSeg([wx0, PYA + PH + 2], [SPY.x, SPY.y - 18], { color: C.guide, width: .9, dash: [4, 3], alpha: a });
  gapSeg([wx1, PYA + PH + 2], [xr, SPY.y - 18], { color: C.guide, width: .9, dash: [4, 3], alpha: a });
  // the pulsed field under the probe (steel to mist), then its -6 dB zone
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.steel; ctx.fillRect(x0, SPY.y, xr - x0, h);
  ctx.imageSmoothingEnabled = true;
  const bx0 = px + G.beam.x0_mm * SPY.mm, bw = BNX * G.beam.dx_mm * SPY.mm;
  ctx.beginPath(); ctx.rect(x0, SPY.y, xr - x0, h); ctx.clip();
  ctx.drawImage(BIM.cvs, bx0 - G.beam.dx_mm * SPY.mm / 2, SPY.y, bw, h + G.beam.dx_mm * SPY.mm);
  ctx.restore();
  for (const sg of [-1, 1]) line(BZ.map((z, q) => [px + sg * BW[q] * SPY.mm, SPY.y + z * SPY.mm]), { color: C.navy, width: 1.2, dash: [5, 3], alpha: a });
  const zl = 8.7;
  math('\\rm{\u22126 dB}', px + halfw(zl) * SPY.mm + 30, SPY.y + zl * SPY.mm, { size: LBL, color: C.navy, alpha: a });
  // flaws passing through the window, at their true size and depth
  G.flaws.forEach((f, n) => {
    const fx = X(f.x);
    if (Math.abs(f.x - wc) * 1000 > hw + f.L_mm / 2) return;
    const [a0_, a1_] = G.lit[n], lit = ip >= a0_ && ip <= a1_, found = ip >= a0_;
    ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.rect(SPY.x, SPY.y, SPY.w, h); ctx.clip();
    ctx.beginPath(); ctx.ellipse(fx, SPY.y + f.z_mm * SPY.mm, f.L_mm / 2 * SPY.mm, f.h_mm / 2 * SPY.mm, 0, 0, 2 * Math.PI);
    if (found) { ctx.fillStyle = lit ? ACC : mix(C.steel, ACC, .75); ctx.fill(); }
    ctx.strokeStyle = FLAW; ctx.lineWidth = lit ? 1.8 : 1.1; if (!found) ctx.setLineDash([3, 2.5]); ctx.stroke(); ctx.restore();
  });
  // the pulse: its crests and troughs as plane fronts, down (navy), back from a
  // flaw (crimson) or from the back wall (blue)
  if (alive(tau)) {
    const fa = a * clamp((G.tend_us - tau) / .08);
    ctx.save(); ctx.beginPath(); ctx.rect(x0, SPY.y, xr - x0, h); ctx.clip();
    const fr = frontsA(ip, tau), col = k => k === 1 ? ACC : k === 2 ? C.blue : C.navy;
    for (const [kind, z, xa, xb, A] of fr) {
      const y = SPY.y + z * SPY.mm;
      line([[X(xa), y], [X(xb), y]], { color: col(kind), width: 2.4, alpha: fa * A });
    }
    // which way each packet runs: an arrow beside its middle crest, right of the zone
    const done = new Set();
    for (const [kind, z] of fr.filter(f => f[4] === 1)) {
      if (done.has(kind)) continue;
      done.add(kind);
      const y = SPY.y + z * SPY.mm, xa_ = px + halfw(z) * SPY.mm + 13, dir = kind === 0 ? 1 : -1;
      arrow(xa_, y - 12 * dir, xa_, y + 12 * dir, { color: col(kind), width: 1.7, head: 8, alpha: fa });
    }
    ctx.restore();
  }
  // the probe positions in the window: visited ones navy, the next ones grey;
  // shown while the steps are slow enough to follow (at speed they would strobe)
  if (ip >= 0) {
    const iv = (G.tstep[ip + 1] ?? G.tstep[ip] + 1) - G.tstep[ip], ta = a * clamp((iv - .12) / .2);
    if (ta > 0) for (let j = Math.max(0, ip - 5); j <= Math.min(G.npos - 1, ip + 5); j++) {
      const xx = X(XP(j));
      if (xx < SPY.x + 2 || xx > xr - 2) continue;
      line([[xx, SPY.y], [xx, SPY.y + 7]], { color: j <= ip ? C.navy : C.guide, width: 1.4, alpha: ta });
    }
  }
  // the plate's faces (its free end, when in the window), the probe (10 mm), a scale bar
  line([[x0, SPY.y], [xr, SPY.y]], { color: C.ink, width: 1.6, alpha: a });
  line([[x0, SPY.y + h], [xr, SPY.y + h]], { color: C.ink, width: 2.4, alpha: a });
  if (X(0) >= SPY.x - .5) line([[X(0), SPY.y], [X(0), SPY.y + h]], { color: C.ink, width: 1.6, alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy; ctx.fillRect(px - G.probe_mm / 2 * SPY.mm, SPY.y - 14, G.probe_mm * SPY.mm, 14); ctx.restore();
  const sb = xr - 5 * SPY.mm, sy = SPY.y + h + 16;
  line([[sb, sy], [sb + 5 * SPY.mm, sy]], { color: C.ink, width: 1.4, alpha: a });
  line([[sb, sy - 4], [sb, sy + 4]], { color: C.ink, width: 1, alpha: a }); line([[sb + 5 * SPY.mm, sy - 4], [sb + 5 * SPY.mm, sy + 4]], { color: C.ink, width: 1, alpha: a });
  text('5 mm', sb - 10, sy + 6, { size: LBL, color: C.body, align: 'right', alpha: a });
  text('beam under the probe, to scale', SPY.x, SPY.y + h + 24, { size: 15, color: C.muted, alpha: a });
}

/* ------------------------------------------------------------ (b) guided wave */
function panelB(st) {
  const yh = YB;
  panel('b', 20, yh, { alpha: seg(.05, .25) });
  text('guided wave testing', 58, yh, { size: HEAD, color: C.body, alpha: settle(.1, S) });
  const fo = fadeOut(st);
  const drawOutline = plate(PYB, seg(.05, .4), seg(.1, .25));
  let tm = null, front = 0;
  if (st.loop >= 0 && st.tau >= SHOT0) {
    tm = Math.min(M0 + (st.tau - SHOT0) / SLOW, G.shot_end_us * 1e-6);
    front = clamp(G.cg * (tm - G.tc), 0, G.span);
  }
  // the covered length, then the field on top of it (its zero is the fill under it)
  const covA = fo;
  // (the model is plane strain: the guided wave covers the plate's whole width, so its top face too)
  if (front > 0) { ctx.save(); ctx.globalAlpha *= covA; ctx.fillStyle = C.mist; ctx.fillRect(XU(0), PYB, XU(front) - XU(0), PH);
    topPath(PYB, XU(0), XU(front)); ctx.fill(); ctx.restore(); }
  if (tm !== null && st.tau < SHOT1 + .6) {
    const u = fieldAt(tm), d = FIM.img.data, fa = (1 - seg(st.b + SHOT1, .5)) * fo;
    for (let i = 0; i < NX; i++) {
      const L = (i * DXM <= front && covA > .5) ? LUT_DONE : LUT_STEEL, li = Math.round((clamp(u[i], -1, 1) + 1) * 127.5) * 3;
      for (let r = 0; r < 3; r++) { const o = (r * NX + i) * 4; d[o] = L[li]; d[o + 1] = L[li + 1]; d[o + 2] = L[li + 2]; d[o + 3] = 255; }
    }
    FIM.g.putImageData(FIM.img, 0, 0);
    ctx.save(); ctx.globalAlpha *= fa; ctx.imageSmoothingEnabled = true;
    ctx.beginPath(); ctx.rect(XU(0), PYB, XU(G.xend) - XU(0), PH); ctx.clip();
    ctx.drawImage(FIM.cvs, 0, 1, NX, 1, XU(-DXM / 2), PYB, NX * DXM * PPM, PH); ctx.restore();
    ctx.save(); ctx.globalAlpha *= fa; ctx.imageSmoothingEnabled = true; topPath(PYB, XU(0), XU(G.xend)); ctx.clip();
    ctx.transform(1, 0, DX3, -DY3, 0, PYB);                // (u, v) -> (u + DX3 v, PYB - DY3 v): the same field, sheared
    ctx.drawImage(FIM.cvs, 0, 1, NX, 1, XU(-DXM / 2), 0, NX * DXM * PPM, 1); ctx.restore();
  }
  // flaws: found when the wave reaches them (its centre, at the group velocity)
  G.flaws.forEach((f, n) => {
    const tHit = G.tc + (f.x - f.L_mm / 2000) / G.cg, hit = tm !== null && tm >= tHit;
    const tRealHit = st.b + SHOT0 + (tHit - M0) * SLOW;
    const glow = hit ? 1 - seg(tRealHit + .5, .6) : 0;
    flawMark(f.x, PYB, f.z_mm, (hit ? 1 : 0) * fo, settle(.25 + .05 * n, S), glow * fo);
  });
  drawOutline();
  // the transducer at x = 0 and the next sensor position at the end of the span
  const tIn = settle(.15, S);
  ctx.save(); ctx.globalAlpha *= tIn; ctx.fillStyle = C.navy; ctx.fillRect(XU(0), PYB - 13 - 8 * (1 - tIn), 12, 13); ctx.restore();
  ctx.save(); ctx.globalAlpha *= tIn; ctx.setLineDash([3, 2.5]); ctx.strokeStyle = C.navy; ctx.lineWidth = 1.3;
  ctx.strokeRect(XU(G.span) - 12, PYB - 13 - 8 * (1 - tIn), 12, 13); ctx.restore();
  const lIn = settle(.25, S);
  text('transducer', XU(0) - 4, PYB - 48 - 6 * (1 - lIn), { size: 17, color: C.body, alpha: lIn });
  text('next sensor position', XU(G.span), PYB - 48 - 6 * (1 - lIn), { size: 17, color: C.body, align: 'right', alpha: lIn });
  // between the two sensors, what lies between them: the span the one shot inspects, dimensioned
  dimk(XU(0), XU(G.span), PYB - 25, G.spanlab, { size: 17, color: C.ink, alpha: settle(.3, S) });
  lengthAxis(PYB, .1);
  // readouts
  const ca = settle(.3, S), cr = st.loop <= 0 ? ca : settle(st.b + .05, S);
  const cw = covLine(950, yh, front / G.span * 100, cr * fo);
  text('one transducer position', 950 - cw - 40, yh, { size: HEAD, color: C.body, align: 'right', alpha: ca });
  if (tm !== null) math(`t = ${Math.max(0, Math.round(tm * 1e6))}\\,\\rm{µs}`, 58, yh + 30, { size: HEAD, alpha: fo * seg(st.b + SHOT0, .3) });
  text(G.slowtxt, 160, yh + 30, { size: 15, color: C.muted, alpha: seg(.5, .3) });
  ascanB(st, tm, fo);
}
/* the received trace, on a time axis laid under the plate so that t maps to
   the distance c_g (t - t_c)/2: each echo sits under its flaw */
function ascanB(st, tm, fo) {
  const y0 = PYB + 104, h = 92, tmaxu = G.tmax * 1e6;
  const XT = tu => XU(G.cg * (tu * 1e-6 - G.tc) / 2);
  const ax = XT(0), aw = XT(tmaxu) - XT(0);
  const A = axes({ x: ax, y: y0, w: aw, h, xlim: [0, tmaxu], ylim: [-1.15, 1.15], xticks: [0, 100, 200, 300, 400, 500, 600, 700],
                   yticks: [-1, 0, 1], xlabel: 't\\ (\\rm{µs})', ylabel: 'u/u_0', ylabelGap: 38, progress: seg(.1, .4),
                   tickSize: TICK, labelSize: 17 });
  A.inside(() => line([[A.X(0), A.Y(0)], [A.X(tmaxu), A.Y(0)]], { color: C.rule, width: 1 }));
  // guides from each flaw down to where its echo is expected, burst centre + 2x/c_g
  const la = seg(.55, .3);
  G.flaws.forEach((f, n) => {
    const te = (G.tc + 2 * f.x / G.cg) * 1e6, x = A.X(te);
    line([[XU(f.x), PYB + PH + 23], [XU(f.x), y0]], { color: C.guide, width: 1, dash: [5, 4], alpha: la * .8 });
    A.inside(() => line([[x, y0], [x, y0 + h]], { color: C.guide, width: 1, dash: [5, 4], alpha: la }));
    keepText(`flaw ${n + 1} echo`, x + 6, y0 + 18, { size: LBL, color: ACC, alpha: la });
  });
  keepText('initial pulse', A.X(62), A.Y(-.62), { size: LBL, color: C.body, alpha: la });
  if (tm !== null && tm > 0) {
    const n = TRACE.length, dtu = G.dt_tr * 1e6, k1 = Math.min(n, Math.floor(tm * 1e6 / dtu) + 1);
    const cuts = [0];
    for (const [wa, wb] of G.win_us) cuts.push(Math.round(wa / dtu), Math.round(wb / dtu));
    cuts.push(n - 1);
    for (let q = 0; q + 1 < cuts.length; q++) {
      const i0 = cuts[q], i1 = Math.min(cuts[q + 1] + 1, k1), pts = [];
      for (let i = i0; i < i1; i++) pts.push([A.X(i * dtu), A.Y(TRACE[i])]);
      if (pts.length > 1) A.inside(() => line(pts, { color: q % 2 ? ACC : C.navy, width: 1.8, alpha: fo }));
    }
    // once both echoes are in: where the echo times put the flaws
    const ra = seg(st.b + SHOT1 - .2, .6) * fo;
    G.flaws.forEach((f, n) => {
      const tpk = G.echo_us[n], xl = G.cg * (tpk * 1e-6 - G.tc) / 2;
      keepMath(`x = c_{\\rm{g}}t/2 = ${xl.toFixed(2)}\\,\\rm{m}`, A.X(tpk) + 6, y0 + h - 10, { size: 15, color: C.body, alpha: ra });
    });
    if (st.tau < SHOT1) {
      const cx = A.X(tm * 1e6);
      gapLine(cx, y0, y0 + h, { color: C.ink, width: 1, alpha: .55 * fo });   // behind the labels
      const inEcho = G.win_us.some(([wa, wb]) => tm * 1e6 >= wa && tm * 1e6 <= wb);
      dot(cx, A.Y(TRACE[k1 - 1]), 3, { color: inEcho ? ACC : C.navy, fill: inEcho ? ACC : C.navy, alpha: fo });
    }
  }
  // colour bar of the field in the plate
  const cb = seg(.45, .3), bx = 410, by = YB + 30;
  ctx.save(); ctx.globalAlpha *= cb; ctx.imageSmoothingEnabled = true; ctx.drawImage(BAR.cvs, bx, by - 9, 96, 9); ctx.restore();
  line([[bx, by - 9], [bx + 96, by - 9], [bx + 96, by], [bx, by], [bx, by - 9]], { color: C.ink, width: .8, alpha: cb });
  math('u_x/u_0', bx - 9, by, { size: 15, align: 'right', alpha: cb });
  for (const [v, s] of [[0, '-1'], [.5, '0'], [1, '1']]) { line([[bx + v * 96, by], [bx + v * 96, by + 3]], { color: C.ink, width: .8, alpha: cb }); math(s, bx + v * 96, by + 18, { size: 15, align: 'center', alpha: cb }); }
}

function draw() {
  const st = now();
  KEEP.length = 0;
  panelA(st);
  panelB(st);
  math(G.params, 500, H - 12, { size: 15, color: C.muted, align: 'center', alpha: seg(.6, .3) });
}
boot();
"""


def build():
    lam = C_L / F_PROBE
    k0 = 2 * np.pi / lam
    N_cf = (D_PROBE ** 2 - lam ** 2) / (4 * lam)
    N_simple = D_PROBE ** 2 * F_PROBE / (4 * C_L)
    print(f"probe: lambda = {lam*1e3:.3f} mm, N = {N_cf*1e3:.2f} mm (D^2 f/4c = {N_simple*1e3:.2f} mm)")

    # the pulsed beam in the plate, and the insonified zone
    xs = np.arange(-20e-3, 20e-3 + 1e-9, 0.25e-3)
    zs = np.arange(0.25e-3, THICK + 1e-9, 0.25e-3)
    A = pulsed_beam(xs, zs)
    A = np.vstack([A[:1], A])                       # z = 0: the face row repeated
    zs = np.concatenate([[0.0], zs])
    w = zone_halfwidth(xs, A)
    print(f"-6 dB pulse echo zone: width {2*w.min()*1e3:.2f} to {2*w.max()*1e3:.2f} mm; index {INDEX*1e3:g} mm")
    assert INDEX < 2 * w.min(), "the index must be below the narrowest zone"

    # probe positions and when each flaw is under a zone
    npos = int(round(SPAN / INDEX))
    xp = (np.arange(npos) + 1) * INDEX              # the first flush with the free end, the last at the span's end
    lit = []
    for fl in FLAWS:
        wz = np.interp(fl["z"], zs, w)
        on = np.nonzero(np.abs(xp - fl["x"]) <= wz + fl["L"] / 2)[0]
        lit.append([int(on[0]), int(on[-1])])

    # the pulse, and the pace
    sig_t, ext = pulse()
    cl_mm_us = C_L / 1e3                            # mm/us
    t_rt = 2 * THICK * 1e3 / cl_mm_us               # us, down and back
    tend = ext[-1][0] * 1e6 + t_rt                  # the last crest home from the back wall (us after the centre left)
    t_life = (tend - ext[0][0] * 1e6) * 1e-6 * SLOW_A
    t_step, vis, t_fire, t_scan, dwell_at, D_dwell = schedule(npos, lit, t_life)
    print(f"{npos} probe positions; flaws under the zone at positions {lit}; the probe dwells at {[d + 1 for d in dwell_at]}"
          f" ({D_dwell:.2f} s each, a pulse {t_life:.3f} s); scan {t_scan:.1f} s")
    ip_p = int(round(np.mean(lit[1])))
    poster_scan = float(t_fire[ip_p] + (POSTER_TAU - ext[0][0] * 1e6) * 1e-6 * SLOW_A)

    # the guided wave shot
    cp, cg = gu.group_velocity("S", gu.F0)
    comp = gu.components("S")
    tc = gu.NCYC / gu.F0 / 2
    dt_tr = 1e-6
    tmax = tc + 2 * SPAN / cg          # the time axis ends where the echo from 2 m would
    ttr = np.arange(0, tmax + dt_tr / 2, dt_tr)
    trace = gw_received(comp, ttr)
    echoes = []
    te = np.arange(0, 1.2e-3, 0.1e-6)
    for i, fl in enumerate(FLAWS):
        g = R_FLAW * (T_FLAW ** 2 if i else 1)
        ee = gu.synth(comp, 2 * fl["x"], te, g)
        tpk, apk, env = gu.envelope_peak(te, ee, 0)
        near = np.abs(te - tpk) < 200e-6
        big = te[near][env[near] >= 0.03 * apk]       # drawn in the accent
        echoes.append(dict(t=tpk, pred=tc + 2 * fl["x"] / cg, amp=apk, win=(big[0], big[-1])))
        print(f"flaw {i+1} echo: envelope peak {tpk*1e6:.1f} us, burst centre + 2x/c_g = {(tc + 2*fl['x']/cg)*1e6:.1f} us")

    dx = 2.5e-3
    xend = 2.15
    nx = int(round(xend / dx)) + 1
    exag = PH_DRAW / (THICK * PPM)
    data = dict(
        slow=SLOW, slowtxt=f"shown {SLOW:,.0f} × slower", tc_us=tc * 1e6, f0=gu.F0, ncyc=gu.NCYC, cg=cg, span=SPAN, xend=xend, nx=nx, dx=dx,
        ppm=PPM, ph=PH_DRAW, thick_mm=THICK * 1e3, R=R_FLAW, T=T_FLAW, index_mm=INDEX * 1e3, npos=npos,
        tstep=t_step, vis=vis, tfire=t_fire, tscan=t_scan, lit=lit, poster_scan=poster_scan, shot_end_us=tmax * 1e6,
        slow_a=SLOW_A, slowtxt_a=f"shown {SLOW_A:,.0f} × slower", cl=cl_mm_us, ext=[[e * 1e6, g] for e, g in ext], tend_us=tend,
        wmid_mm=float(2 * np.interp(THICK / 2, zs, w) * 1e3), probe_mm=D_PROBE * 1e3,
        flaws=[dict(x=f["x"], z_mm=f["z"] * 1e3, L_mm=f["L"] * 1e3, h_mm=f["h"] * 1e3) for f in FLAWS],
        beam=dict(nx=len(xs), nz=len(zs), x0_mm=xs[0] * 1e3, dx_mm=0.25, z_mm=zs * 1e3, w_mm=w * 1e3,
                  a=common.i8(np.clip(A / A.max(), 0, 1) * 127)),
        c=dict(w=common.f32(comp["w"]), k=common.f32(comp["k"]), a=common.f32(comp["a"]), p=common.f32(comp["p"])),
        trace=common.f32(trace), dt_tr_us=dt_tr * 1e6, tmax_us=tmax * 1e6,
        echo_us=[e["t"] * 1e6 for e in echoes], win_us=[[v * 1e6 for v in e["win"]] for e in echoes],
        # the parameter lines, set as math (variables italic, units upright)
        params_a=r"\rm{probe 10 mm, 5 MHz;}\ N = " + f"{N_simple*1e3:.0f}" + r"\,\rm{mm};\ \rm{index}\ " + f"{INDEX*1e3:g}" + r"\,\rm{mm}",
        # (b), between the two sensors (29 Sep, "2 sensor arasına title"): the span one shot inspects
        spanlab=r"\rm{whole span inspected at once: }" + f"{SPAN:g}" + r"\,\rm{m}",
        params=(r"\rm{steel plate,}\ d = 10\,\rm{mm}\ (\rm{drawn}\ " + f"{exag:g}" + r"\ \times\ \rm{thicker});\ \ S_0\ \rm{at 50 kHz, group velocity}\ " + f"{cg:.0f}" + r"\,\rm{m/s};\ \ \rm{flaws}\ " + f"{FLAWS[0]['L']*1e3:g}" + r"\,\rm{mm long, reflection}\ " + f"{R_FLAW:g}"),
    )
    title = "Figure 13: Coverage comparison between the two families of ultrasonic testing"
    aria = (f"On the same 2 m steel plate, a bulk wave probe steps along {npos} positions, each covering only "
            "the narrow zone beneath it; where it pauses, its pulse runs straight down through the plate and "
            "back, from a flaw or from the back wall, and a flaw lights up only when the probe is over it. A "
            "single guided wave shot from one transducer sweeps the whole span in 0.4 ms and returns an echo "
            "from each flaw.")
    W, H = 1000, 760
    common.build_html("coverage", title, aria, W, H, data, JS)
    res = dict(xs=xs, zs=zs, A=A, w=w, lam=lam, k0=k0, N_cf=N_cf, N_simple=N_simple, npos=npos, lit=lit,
               t_scan=t_scan, cp=cp, cg=cg, comp=comp, echoes=echoes, tc=tc, nx=nx, dx=dx, exag=exag,
               sig_t=sig_t, ext=ext, t_rt=t_rt, tend=tend, t_life=t_life, dwell_at=dwell_at, D_dwell=D_dwell,
               t_step=t_step, t_fire=t_fire, poster_scan=poster_scan, ip_p=ip_p, data=data, W=W, H=H)
    png = common.still("coverage")
    print("still:", png)
    validate(res)
    return res


def validate(r):
    """Closed forms for the probe, the pulsed beam's convergence, coverage,
    the pulse and its echo times, the page's own sums; writes ut_coverage.check.txt."""
    from scipy.optimize import brentq
    from scipy.special import j1
    L = []
    say = L.append
    k0, lam = r["k0"], r["lam"]
    # 1. the edge wave form against the Rayleigh surface integral
    pts = [(0, 5e-3), (3e-3, 5e-3), (6e-3, 8e-3), (2e-3, 1e-3), (4.5e-3, 2e-3), (0, 21e-3), (8e-3, 30e-3)]
    surf = max(abs(abs(piston(np.array(x), np.array(z), k0)) - abs(rayleigh_surface(x, z, k0))) /
               abs(rayleigh_surface(x, z, k0)) for x, z in pts)
    # 2. on axis against the closed form, and the near field length
    zz = np.linspace(0.5e-3, 80e-3, 20001)
    num = np.abs(piston(np.zeros_like(zz), zz, k0))
    cf = 2 * np.abs(np.sin(k0 / 2 * (np.sqrt(zz ** 2 + A_PROBE ** 2) - zz)))
    ax_err = np.abs(num - cf).max()
    z_last = zz[np.argmax(num)]
    # 3. far field, -6 dB half angles, one way and pulse echo
    Rff = 0.4
    th = np.linspace(0, 0.25, 5001)
    pf = np.abs(piston(Rff * np.sin(th), Rff * np.cos(th), k0))
    pf /= pf[0]
    th6 = th[np.nonzero(pf >= 0.5)[0][-1]]
    th3 = th[np.nonzero(pf >= 1 / np.sqrt(2))[0][-1]]
    u6 = brentq(lambda u: 2 * j1(u) / u - 0.5, 1, 3)
    u3 = brentq(lambda u: (2 * j1(u) / u) ** 2 - 0.5, 1, 3)
    th6_cf, th3_cf = np.arcsin(u6 / (k0 * A_PROBE)), np.arcsin(u3 / (k0 * A_PROBE))
    # 4. the pulsed beam: twice the frequencies, and a finer rim sum
    zc = np.array([1e-3, 3e-3, 5e-3, 6.5e-3, 8e-3, 10e-3])
    xs = r["xs"]
    A1 = pulsed_beam(xs, zc)
    A2 = pulsed_beam(xs, zc, nf=49)
    w1, w2 = zone_halfwidth(xs, A1), zone_halfwidth(xs, A2)
    conv = np.abs(w1 - w2).max()
    # 5. coverage of the union of zones at the index
    worst = union_coverage(xs, r["A"][1:], INDEX)
    # 6. the pulse: its spectrum's -6 dB band (zero padded FFT), and its crests
    sig_t, ext = r["sig_t"], r["ext"]
    tt = np.arange(-3e-6, 3e-6, 1e-10)
    gg = np.exp(-tt ** 2 / (2 * sig_t ** 2)) * np.cos(2 * np.pi * F_PROBE * tt)
    nfft = 1 << 23
    spec = np.abs(np.fft.rfft(gg, nfft))
    ff = np.fft.rfftfreq(nfft, 1e-10)
    above = ff[spec >= 0.5 * spec.max()]
    band = (above[-1] - above[0]) / F_PROBE
    # the echo times the fronts give (1D, at c_L): the back wall and each flaw's top
    d = r["data"]
    cl = d["cl"]
    t_bw = 2 * d["thick_mm"] / cl
    t_fl = [2 * (f["z_mm"] - f["h_mm"] / 2) / cl for f in d["flaws"]]
    # 7. the page's fronts against the Python port, at moments of the pulses it sends
    ext5 = [[float(r5(e * 1e6)), float(r5(g))] for e, g in ext]
    bz, bw = r5(d["beam"]["z_mm"]), r5(d["beam"]["w_mm"])
    flaws5 = [{k: float(r5(v)) for k, v in f.items()} for f in d["flaws"]]
    cl5 = float(r5(cl))
    m1, m2 = int(round(np.mean(r["lit"][0]))), int(round(np.mean(r["lit"][1])))
    cases = [(0, 0.4), (0, 1.9), (1, 2.9), (m1 - 1, 1.2), (m1, 0.95), (m1 + 1, 1.5), (m2, POSTER_TAU), (m2 + 1, 0.5),
             (m1 - 3, 1.6), (m1 + 3, 1.0)]
    js = []
    for ip, tau in cases:
        ref = fronts_a(ip, tau, bz, bw, ext5, cl5, flaws5, float(r5(d["index_mm"])), float(r5(d["thick_mm"])))
        js.append((f"frontsA({ip}, {tau!r}).flat()", np.array(ref, float).ravel()))
    page_a, counts = check_fronts(js)
    # 8. the guided wave: echo times, and the page's own sum
    xg = np.arange(r["nx"]) * r["dx"]
    page = gu.check_page("coverage", [(f"fieldAt({tm!r})", gw_field(r["comp"], xg, tm)) for tm in (150e-6, 300e-6, 480e-6)])
    over = common.overlaps("coverage", [0.5, 0.9, 1.4, 2.2, 3.0, 4.4, 7.0, 9.5, 12.0, 14.6, 17.0, 19.6,
                                        T_LOOP(r) - 0.5, T_LOOP(r) + 1.2])

    say("Figure 13, coverage of bulk and guided wave testing: check of tools/numfig/ut_coverage.py")
    say("")
    say("MODEL (a): BULK WAVE PROBE")
    say(f"  Circular piston, D = {D_PROBE*1e3:g} mm, centre frequency {F_PROBE/1e6:g} MHz, in the steel of Figure 12")
    say(f"  (c_L = {C_L:.1f} m/s): lambda = {lam*1e3:.3f} mm, k a = {k0*A_PROBE:.2f}.")
    say("  Field: the Rayleigh integral in edge wave form (direct plane wave under the face minus the")
    say("  rim's diffracted wave), a 4096 point sum round the rim.")
    say(f"  Pulsed beam: RMS over a Gaussian band, {BW*100:g} % at -6 dB, 25 frequencies over +-3 sigma;")
    say("  grid 0.25 mm, 40 mm wide by the plate's 10 mm depth.")
    say("  Insonified zone: at each depth, where the pulse echo response (field squared) is within")
    say("  -6 dB of that depth's maximum; the zone's outer edge is drawn.")
    say("")
    say("VALIDATION (a)")
    say(f"  1. Edge wave form against the Rayleigh surface integral itself (200 x 400 point")
    say(f"     Gauss-Legendre by trapezoid quadrature) at 7 points from z = 1 to 30 mm:")
    say(f"     largest relative difference {surf:.1e}.")
    say(f"  2. On axis against 2|sin(k (sqrt(z^2 + a^2) - z)/2)|, z = 0.5 to 80 mm: largest difference {ax_err:.1e}.")
    say(f"     Last on-axis maximum (near field length): {z_last*1e3:.3f} mm against (D^2 - lambda^2)/(4 lambda) =")
    say(f"     {r['N_cf']*1e3:.3f} mm ({(z_last - r['N_cf'])*1e3:+.3f} mm, the grid step is 0.004 mm);")
    say(f"     D^2 f/(4c) = {r['N_simple']*1e3:.2f} mm.")
    say(f"  3. Far field (R = 0.4 m, {Rff/r['N_cf']:.0f} near field lengths), -6 dB half angle: one way {np.degrees(th6):.3f} deg against")
    say(f"     asin({u6:.4f}/(k a)) = {np.degrees(th6_cf):.3f} deg (2 J1(u)/u = 1/2); pulse echo")
    say(f"     {np.degrees(th3):.3f} deg against asin({u3:.4f}/(k a)) = {np.degrees(th3_cf):.3f} deg (0.514 lambda/D).")
    say(f"  4. Pulsed beam with 49 frequencies instead of 25: zone edge moves at most {conv*1e6:.2f} um.")
    say("")
    say("COVERAGE (a)")
    w = r["w"]
    say(f"  Zone width over the depth: {2*w.min()*1e3:.2f} to {2*w.max()*1e3:.2f} mm "
        f"({2*np.interp(THICK/2, r['zs'], w)*1e3:.2f} mm at mid depth).")
    say(f"  Scan index {INDEX*1e3:g} mm, below the narrowest zone: {r['npos']} positions over the {SPAN:g} m span,")
    say(f"  the first with the probe flush with the free end (centre at {INDEX*1e3:g} mm), the last at {SPAN:g} m.")
    say(f"  Union of all zones: the weakest pulse echo response anywhere in the plate is {worst:.2f} dB")
    say("  (above -6 dB: the span is covered completely).")
    for n, (a, b) in enumerate(r["lit"]):
        f = FLAWS[n]
        say(f"  Flaw {n+1} (lamination {f['L']*1e3:g} mm long, at x = {f['x']:g} m, {f['z']*1e3:g} mm deep) lies in a zone")
        say(f"  at positions {a+1} to {b+1} only.")
    say("")
    say("THE PULSE (a), his note of 5 Oct 2026: the vertical waves")
    say(f"  The probe's band in time: g(s) = exp(-s^2/(2 sigma^2)) cos(2 pi f0 s), sigma = 1/(2 pi sigma_f),")
    say(f"  sigma_f = BW f0/(2 sqrt(2 ln 2)) = {BW*F_PROBE/(2*np.sqrt(2*np.log(2)))/1e6:.4f} MHz: sigma = {sig_t*1e6:.4f} us.")
    say(f"  CHECK: its spectrum (zero padded FFT) is above half its peak over {above[0]/1e6:.3f} to {above[-1]/1e6:.3f} MHz,")
    say(f"     {band*100:.2f} % of f0 (the model's band: {BW*100:g} %).")
    say("  Its crests and troughs above a tenth of its peak (Brent's method on g'(s) = 0), drawn as fronts:")
    say("     " + ", ".join(f"s = {e*1e6:+.4f} us, g = {g:+.4f}" for e, g in ext))
    say(f"  Each front is a plane as wide as the -6 dB zone at its depth, at depth c_L (tau - s), straight down")
    say(f"  at c_L = {cl:.5f} mm/us; a column of the beam over a lamination turns back at the lamination's top")
    say("  (its depth z_f - h/2: the model's laminations are flat and planar), every other column at the back")
    say("  wall; up again at c_L; gone when it reaches the probe's face. Down navy, back from a flaw crimson")
    say("  (the echo), back from the back wall blue; each front's opacity is its |g|.")
    say(f"  CHECK: the echo times the fronts give against 2 z / c_L: back wall {t_bw:.4f} us (2d/c_L = "
        f"{2*THICK/C_L*1e6:.4f} us);")
    for n, tf in enumerate(t_fl):
        f = FLAWS[n]
        say(f"     flaw {n+1}, top at {(f['z']-f['h']/2)*1e3:.1f} mm: {tf:.4f} us ({2*(f['z']-f['h']/2)/C_L*1e6:.4f} us); its"
            f" echo comes home {t_bw - tf:.3f} us before the back wall's would")
    say(f"  CHECK: the page's own fronts (frontsA) against the Python port at {len(cases)} moments of the pulses"
        f" (positions {sorted(set(c[0]+1 for c in cases))}):")
    say(f"     largest difference {page_a:.1e} (mm, m and |g| alike); fronts compared: "
        + ", ".join(str(g) for g, _ in counts))
    say(f"  The pulse shown {SLOW_A:,.0f} x slower (5 us of the model per second): down and back through the 10 mm")
    say(f"  in {r['t_rt']:.3f} us, {r['t_rt']*1e-6*SLOW_A:.3f} s on the page; from its first crest leaving to its last"
        f" home {r['tend']-ext[0][0]*1e6:.3f} us, {r['t_life']:.3f} s.")
    say("")
    say("THE PACE (a): designed; which positions exist and what each covers is the model")
    say(f"  The probe dwells, and sends its pulse, at positions {[p + 1 for p in r['dwell_at']]}: the first {N_START}, and the")
    say(f"  three round the middle of each flaw's lit range ({[m + 1 for m in (m1, m2)]}); each dwell {r['D_dwell']:.3f} s (glide"
        f" {VIS} s, the pulse {r['t_life']:.3f} s, a pause {PAUSE} s).")
    say(f"  Beside a dwell a step takes {D_NEAR} s, {Q_NEAR} times less at each step further away, down to"
        f" {1/R_FAST:.4f} s ({R_FAST:g} positions per second) in between.")
    say(f"  The scan takes {r['t_scan']:.2f} s (the old page's 7.8 s: his \"slide a bit slower\"); the loop"
        f" {T_LOOP(r):.2f} s (scan, then 2.4 s held, 0.8 s fading).")
    say(f"  The still: position {r['ip_p']+1} (flaw 2's middle), {POSTER_TAU} us into its pulse: the flaw's echo half way"
        " up, crimson; t = {:.3f} s.".format(0.15 + 0.3 + r["poster_scan"]))
    say("")
    say("MODEL (b): GUIDED WAVE")
    say(f"  The S0 mode of Figure 12 (guided_ut.py): Rayleigh-Lamb roots, 3 cycle Hann burst at 50 kHz,")
    say(f"  {len(r['comp']['w'])} spectral lines each with its own k(omega); c_p = {r['cp']:.1f} m/s, c_g = {r['cg']:.1f} m/s.")
    say(f"  Two flaws, each reflecting {R_FLAW:g} and transmitting sqrt(1 - R^2) = {T_FLAW:.4f} (frequency")
    say("  independent, schematic), single scattering: the echo from flaw 2 passes flaw 1 twice.")
    say("")
    say("VALIDATION (b)")
    for n, e in enumerate(r["echoes"]):
        say(f"  Echo {n+1}: envelope peak (Hilbert) {e['t']*1e6:.1f} us against burst centre + 2x/c_g = "
            f"{e['pred']*1e6:.1f} us ({(e['t']-e['pred'])*1e6:+.2f} us);")
        say(f"     the flaw placed at c_g (t - t_c)/2 = {r['cg']*(e['t']-r['tc'])/2:.4f} m (true {FLAWS[n]['x']:g} m).")
    say(f"  Coverage front: the burst centre, at c_g, reaches the next sensor position ({SPAN:g} m) at")
    say(f"  {(r['tc'] + SPAN/r['cg'])*1e6:.1f} us.")
    say(f"  The page's own sum against numpy at three moments: largest difference {page:.1e}.")
    say("")
    say("DISPLAY")
    say("  Both strips are the plate of Figure 12 as a thin slab in an oblique view (its top face receding 14 by")
    say("  10 units); the front face is the section the strip shows. In (b) the top face carries the guided wave's")
    say("  field and coverage too (plane strain: the same across the width); in (a) it is left plain, the probe")
    say("  inspecting only its own track.")
    say(f"  {r['W']} x {r['H']}. Both strips on one scale, {PPM} units/m; the plate's thickness drawn {r['exag']:g} times"
        " enlarged; the window")
    say(f"  under the probe drawn to scale (12 units/mm, 36 mm wide), its beam pale (steel to mist) so the fronts")
    say(f"  read on it. The guided wave shown {SLOW:,.0f} x slower (as Figure 12); the pulse in (a) {SLOW_A:,.0f} x slower,")
    say("  each labelled \"shown N x slower\". At each loop's start the probe, the window under it and the readouts")
    say("  settle in again (they faded out with the loop before), as in the first.")
    say("  In the strip the probe's -6 dB zone fills downward with its pulse where it dwells, down to the back")
    say("  wall, or to a lamination's top where one covers the whole beam (below it is its shadow); the plate is")
    say("  drawn 8.5 times thicker there, so the fronts themselves are drawn in the window, at their true width.")
    say(f"  (b): between the transducer and the next sensor position, a dimension of the span one shot")
    say(f"  inspects, {SPAN:g} m (x = 0 to {SPAN:g} m on the strip's own scale), on a white knockout.")
    say("  Type (5 Oct 2026): headings and the strips' labels 17, ticks and the notes in the plots 16, the")
    say("  parameter lines and the slowing 15, nothing under 15; percent closed up (80%).")
    say("  Beside each packet of fronts in the window an arrow says which way it runs (down navy; up crimson")
    say("  from a flaw, blue from the back wall), at its middle crest's depth.")
    say("")
    say("OVERLAP (engine ?overlap, common.overlaps at 672 px; common.still also samples every 0.25 s up to")
    say("  the poster):")
    for k, v in over.items():
        say(f"  {k}: labels {v['labels'] or 'none'}, crossings {v['crossings'] or 'none'}")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "ut_coverage.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


def T_LOOP(r):
    return 0.3 + r["t_scan"] + 2.4 + 0.8


def check_fronts(cases):
    """The page's frontsA() in a browser against the port: largest difference and the counts compared."""
    from playwright.sync_api import sync_playwright
    path = os.path.join(common.ANIM, "nf-coverage.html").replace("\\", "/")
    worst, counts = 0.0, []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file:///" + path + "?still")
        pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
        for expr, ref in cases:
            got = np.array(pg.evaluate(f"Array.from({expr})"), float)
            counts.append((len(got) // 5, len(ref) // 5))
            if got.shape != ref.shape:
                worst = np.inf
                continue
            if got.size:
                worst = max(worst, float(np.abs(got - ref).max()))
        b.close()
    return worst, counts


if __name__ == "__main__":
    build()
