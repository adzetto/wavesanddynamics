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
SLOW = gu.SLOW
PPM, PH_DRAW = gu.PPM, gu.PH_DRAW


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


# ------------------------------------------------------------------ scan schedule
def schedule(n, flaw_idx):
    """Start time (s, from the first step) of each probe position: slow for the
    first steps, then fast, easing down while a flaw is under the probe. Only
    the pace is designed; which positions exist and what each covers is the model."""
    r_slow, r_fast = 3.0, 75.0
    i = np.arange(n, dtype=float)
    ramp = np.clip((i - 2) / 10, 0, 1)
    ramp = ramp * ramp * (3 - 2 * ramp)
    rate = r_slow + (r_fast - r_slow) * ramp
    for fi in flaw_idx:
        rate = rate / (1 + 6.0 * np.exp(-((i - fi) / 4.0) ** 2))
    return np.concatenate([[0.0], np.cumsum(1 / rate)[:-1]]), np.cumsum(1 / rate)[-1]


JS = r"""
const G = DATA;
G.tc = G.tc_us * 1e-6; G.tmax = G.tmax_us * 1e-6; G.dt_tr = G.dt_tr_us * 1e-6;
const T0 = 0.15, SLOW = G.slow, M0 = -20e-6, S = .28;
const PX0 = 90, PPM = G.ppm, PH = G.ph, ZS = PH / G.thick_mm;   // ZS: drawing units per mm of depth
const XU = x => PX0 + x * PPM;
const PYA = 78, YB = 338, PYB = YB + 100;                                     // the two strips
const ACC = C.accent, FLAW = '#781E2C', LBL = 15;
const STOPS = ['#043052', '#2E6A9E', '#9CBBD6', null, '#DEABAB', '#B03F4D', '#651020'];
const lutWith = mid => _ramp(STOPS.map(s => _hex(s || mid)));
const LUT_STEEL = lutWith(C.steel), LUT_DONE = lutWith(C.mist);
const BLUT = _ramp(['#E3EBF2', '#C9D7E4', '#5B8DB8', '#095A94', '#043052'].map(_hex));

/* ------------------------------------------------------------ data */
const COMP = { w: b64f32(G.c.w), k: b64f32(G.c.k), a: b64f32(G.c.a), p: b64f32(G.c.p) };
const TRACE = b64f32(G.trace);
const NX = G.nx, DXM = G.dx, U = new Float64Array(NX);
const I1 = Math.round(G.flaws[0].x / DXM), I2 = Math.round(G.flaws[1].x / DXM);
const BEAM = b64i8(G.beam.a), BNX = G.beam.nx, BNZ = G.beam.nz;
const XP = i => (i + 1) * G.index_mm / 1000;                  // probe position i (m): the first flush with the end

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

/* ------------------------------------------------------------ the clock
   One loop: the guided wave shot (model time, slowed SLOW times) and the bulk
   probe's scan start together; the scan's pace is designed (slow first steps,
   fast, easing while a flaw is under the probe), the positions are the model's */
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
const fadeOut = st => st.loop < 0 ? 1 : 1 - seg(st.b + SCAN1 + HOLD, FADE);
const POSTER_T = T0 + PER + SCAN0 + G.poster_scan;

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
function plate(py, prog, fillA) {
  const x0 = XU(0), x1 = XU(G.xend);
  ctx.save(); ctx.globalAlpha *= fillA; ctx.fillStyle = C.steel; ctx.fillRect(x0, py, x1 - x0, PH); ctx.restore();
  return () => {
    line([[x1, py], [x0, py], [x0, py + PH], [x1, py + PH]], { color: C.ink, width: 1.6, progress: prog });
    line([[x0, py + PH], [x1, py + PH]], { color: C.ink, width: 2.4, progress: prog });
    cutEdge(x1, py, py + PH, { alpha: clamp(prog * 3 - 2) });
  };
}
function lengthAxis(py, t0) {
  const ya = py + PH + 16;
  line([[XU(0), ya], [XU(2), ya]], { color: C.ink, width: 1.3, progress: seg(t0, .35) });
  for (const v of [0, .5, 1, 1.5, 2]) {
    const a = seg(t0 + .08 + v * .1, .25);
    line([[XU(v), ya], [XU(v), ya - 5]], { color: C.ink, width: 1.1, alpha: a });
    math(fmt(v), XU(v), ya + 19, { size: 15, align: 'center', alpha: a });
  }
  math('x\\ (\\rm{m})', XU(2) + 36, ya + 19, { size: 16, align: 'left', alpha: seg(t0 + .3, .25) });
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
function swatchText(x, y, s, o = {}) { text(s, x, y, { size: LBL, color: C.body, ...o }); }
/* labels the time cursor passes behind: their ink boxes, kept as they are
   drawn; gapLine() is a vertical line broken 3 units clear of each */
const KEEP = [];
function keepText(s, x, y, o) {
  text(s, x, y, o);
  if (!(o.alpha > 0)) return;
  ctx.save(); ctx.font = font(o); ctx.textAlign = o.align || 'left'; const q = ctx.measureText(s); ctx.restore();
  KEEP.push([x - q.actualBoundingBoxLeft, y - q.actualBoundingBoxAscent, x + q.actualBoundingBoxRight, y + q.actualBoundingBoxDescent]);
}
function keepMath(s, x, y, o) {                   // left aligned math; its box from its width and size
  const w = math(s, x, y, o);
  if (o.alpha > 0) KEEP.push([x - 1, y - o.size * .95, x + w + 1, y + o.size * .45]);
}
function gapLine(x, y0, y1, o) {
  const cuts = KEEP.filter(b => x > b[0] - 3 && x < b[2] + 3).map(b => [b[1] - 3, b[3] + 3]).sort((p, q) => p[0] - q[0]);
  let y = y0;
  for (const [p, q] of cuts) { if (p > y + .5) line([[x, y], [x, Math.min(p, y1)]], o); y = Math.max(y, q); if (y >= y1) return; }
  if (y1 > y + .5) line([[x, y], [x, y1]], o);
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
  text('bulk wave testing', 58, 34, { size: 16, color: C.body, alpha: settle(.05, S) });
  const fo = fadeOut(st), ip = probeIndex(st);
  const drawOutline = plate(PYA, seg(0, .4), seg(.05, .25));
  // coverage: every zone so far (index below the narrowest zone: they join up)
  let xs = null;
  if (ip >= 0) {
    const i0 = ip, tsI = st.b + SCAN0 + G.tstep[i0], nxt = G.tstep[i0 + 1] ?? G.tstep[i0] + .3;
    const vis = Math.min(.32, .7 * (nxt - G.tstep[i0]));
    const g = i0 === 0 ? 1 : settle(tsI, vis);
    xs = i0 === 0 ? XP(0) : lerp(XP(i0 - 1), XP(i0), g);
    const edge = xs + G.wmid_mm / 2000;
    ctx.save(); ctx.globalAlpha *= fo; ctx.fillStyle = C.mist;
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
  // the probe and its insonified zone (-6 dB, pulse echo) beneath it
  if (xs !== null) {
    const zw = G.beam.w_mm, zz = G.beam.z_mm, pts = [];
    for (let q = 0; q < zz.length; q++) pts.push([XU(xs + zw[q] / 1000), PYA + zz[q] * ZS]);
    for (let q = zz.length - 1; q >= 0; q--) pts.push([XU(xs - zw[q] / 1000), PYA + zz[q] * ZS]);
    const za = seg(st.b + SCAN0, .3) * fo;
    ctx.save(); ctx.globalAlpha *= .9 * za; ctx.fillStyle = C.blue; ctx.beginPath();
    pts.forEach(([x, y], q) => q ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  drawOutline();
  if (xs !== null) {
    const pa = seg(st.b + SCAN0 - .3, .3) * fo, pw = G.probe_mm / 1000 * PPM;
    ctx.save(); ctx.globalAlpha *= pa; ctx.fillStyle = C.navy; ctx.fillRect(XU(xs) - pw / 2, PYA - 11, pw, 11); ctx.restore();
    text('probe', XU(xs), PYA - 17, { size: 14, color: C.body, align: 'center', alpha: pa });
    spy(st, xs, pa);
  }
  lengthAxis(PYA, .05);
  // counters: positions, coverage
  const ca = settle(.3, S);
  const npos = ip + 1, cov = ip < 0 ? 0 : Math.min(100, (XP(ip) + G.wmid_mm / 2000) / G.span * 100);
  const cw = covLine(950, 34, cov, ca * fo + (ip < 0 ? ca : 0) * (1 - fo));
  text(`probe position ${Math.max(0, npos)} of ${G.npos}`, 950 - cw - 40, 34, { size: 16, color: C.body, align: 'right', alpha: ca });
  legend(92, 178, seg(.5, .3));
  text(G.params_a, 92, 272, { size: 14, color: C.muted, alpha: seg(.6, .3) });
}
function covLine(xr, y, pct, a) {
  const s = `coverage ${Math.round(pct)} %`;
  const w = text(s, xr, y, { size: 16, color: C.body, align: 'right', alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.mist; ctx.fillRect(xr - w - 24, y - 11, 16, 11); ctx.restore();
  line([[xr - w - 24, y - 11], [xr - w - 8, y - 11], [xr - w - 8, y], [xr - w - 24, y], [xr - w - 24, y - 11]], { color: C.ink, width: .8, alpha: a });
  return w + 24;
}
function legend(x, y, a) {
  if (a <= 0) return;
  const w = 360, h = 70;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(x, y, w, h); ctx.restore();
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], { color: C.ink, width: 1, alpha: a });
  const r1 = y + 26, r2 = y + 54, c1 = x + 14, c2 = x + 170;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.mist; ctx.fillRect(c1, r1 - 11, 22, 12);
  ctx.fillStyle = C.blue; ctx.globalAlpha *= .9; ctx.fillRect(c1 + 8, r2 - 13, 6, 16); ctx.restore();
  swatchText(c1 + 32, r1, 'inspected', { alpha: a });
  swatchText(c1 + 32, r2, '\u22126 dB zone', { alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.ellipse(c2 + 10, r1 - 5, 7, 3.5, 0, 0, 2 * Math.PI); ctx.fillStyle = ACC; ctx.fill();
  ctx.strokeStyle = FLAW; ctx.lineWidth = 1.1; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(c2 + 10, r2 - 5, 7, 3.5, 0, 0, 2 * Math.PI); ctx.setLineDash([2.5, 2]); ctx.stroke(); ctx.restore();
  swatchText(c2 + 26, r1, 'flaw found', { alpha: a });
  swatchText(c2 + 26, r2, 'flaw not yet found', { alpha: a });
}
/* the beam under the probe, to scale: the computed pulsed field and its -6 dB
   pulse echo zone, in a window 40 mm wide moving with the probe */
const SPY = { x: 530, y: 188, w: 360, mm: 9 };
function spy(st, xs, a0) {
  const a = a0 * seg(.45, .3);
  if (a <= 0) return;
  const hw = SPY.w / 2 / SPY.mm, h = G.thick_mm * SPY.mm, cx = SPY.x + SPY.w / 2;
  // the window: centred on the probe, but it stops at the plate's free end
  const wc = Math.max(xs, hw / 1000), X = x => cx + (x - wc) * 1000 * SPY.mm, px = X(xs);
  const x0 = Math.max(SPY.x, X(0));                               // left edge of steel in the window
  const wx0 = XU(wc - hw / 1000), wx1 = XU(wc + hw / 1000);
  line([[wx0, PYA - 2], [wx1, PYA - 2], [wx1, PYA + PH + 2], [wx0, PYA + PH + 2], [wx0, PYA - 2]], { color: C.guide, width: 1, alpha: a });
  line([[wx0, PYA + PH + 2], [SPY.x, SPY.y - 14]], { color: C.guide, width: .9, dash: [4, 3], alpha: a });
  line([[wx1, PYA + PH + 2], [SPY.x + SPY.w, SPY.y - 14]], { color: C.guide, width: .9, dash: [4, 3], alpha: a });
  // the pulsed field under the probe (steel to navy), then its -6 dB zone
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.steel; ctx.fillRect(x0, SPY.y, SPY.x + SPY.w - x0, h);
  ctx.imageSmoothingEnabled = true;
  const bx0 = px + G.beam.x0_mm * SPY.mm, bw = BNX * G.beam.dx_mm * SPY.mm;
  ctx.beginPath(); ctx.rect(x0, SPY.y, SPY.x + SPY.w - x0, h); ctx.clip();
  ctx.drawImage(BIM.cvs, bx0 - G.beam.dx_mm * SPY.mm / 2, SPY.y, bw, h + G.beam.dx_mm * SPY.mm);
  ctx.restore();
  const zw = G.beam.w_mm, zz = G.beam.z_mm;
  for (const sg of [-1, 1]) line(zz.map((z, q) => [px + sg * zw[q] * SPY.mm, SPY.y + z * SPY.mm]), { color: C.navy, width: 1.2, dash: [5, 3], alpha: a });
  math('\\rm{\u22126 dB}', px + zw[Math.round(zz.length * .45)] * SPY.mm + 6, SPY.y + h * .5, { size: 14, color: C.navy, alpha: a });
  // flaws passing through the window, at their true size and depth
  const ip = probeIndex(st);
  G.flaws.forEach((f, n) => {
    const fx = X(f.x);
    if (Math.abs(f.x - wc) * 1000 > hw + f.L_mm / 2) return;
    const [a0_, a1_] = G.lit[n], lit = ip >= a0_ && ip <= a1_, found = ip >= a0_;
    ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.rect(SPY.x, SPY.y, SPY.w, h); ctx.clip();
    ctx.beginPath(); ctx.ellipse(fx, SPY.y + f.z_mm * SPY.mm, f.L_mm / 2 * SPY.mm, f.h_mm / 2 * SPY.mm, 0, 0, 2 * Math.PI);
    if (found) { ctx.fillStyle = lit ? ACC : mix(C.steel, ACC, .75); ctx.fill(); }
    ctx.strokeStyle = FLAW; ctx.lineWidth = lit ? 1.8 : 1.1; if (!found) ctx.setLineDash([3, 2.5]); ctx.stroke(); ctx.restore();
  });
  // the probe positions in the window: visited ones navy, the next ones grey;
  // shown while the steps are slow enough to follow (at speed they would strobe)
  if (ip >= 0) {
    const iv = (G.tstep[ip + 1] ?? G.tstep[ip] + 1) - G.tstep[ip], ta = a * clamp((iv - .12) / .2);
    if (ta > 0) for (let j = Math.max(0, ip - 5); j <= Math.min(G.npos - 1, ip + 5); j++) {
      const xx = X(XP(j));
      if (xx < SPY.x + 2 || xx > SPY.x + SPY.w - 2) continue;
      line([[xx, SPY.y], [xx, SPY.y + 7]], { color: j <= ip ? C.navy : C.guide, width: 1.4, alpha: ta });
    }
  }
  // the plate's faces (its free end, when in the window), the probe (10 mm), a scale bar
  line([[x0, SPY.y], [SPY.x + SPY.w, SPY.y]], { color: C.ink, width: 1.6, alpha: a });
  line([[x0, SPY.y + h], [SPY.x + SPY.w, SPY.y + h]], { color: C.ink, width: 2.4, alpha: a });
  if (X(0) >= SPY.x - .5) line([[X(0), SPY.y], [X(0), SPY.y + h]], { color: C.ink, width: 1.6, alpha: a });
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy; ctx.fillRect(px - G.probe_mm / 2 * SPY.mm, SPY.y - 14, G.probe_mm * SPY.mm, 14); ctx.restore();
  const sb = SPY.x + SPY.w - 5 * SPY.mm - 4, sy = SPY.y + h + 16;
  line([[sb, sy], [sb + 5 * SPY.mm, sy]], { color: C.ink, width: 1.4, alpha: a });
  line([[sb, sy - 4], [sb, sy + 4]], { color: C.ink, width: 1, alpha: a }); line([[sb + 5 * SPY.mm, sy - 4], [sb + 5 * SPY.mm, sy + 4]], { color: C.ink, width: 1, alpha: a });
  text('5 mm', sb + 2.5 * SPY.mm, sy + 17, { size: 14, color: C.body, align: 'center', alpha: a });
  text('beam under the probe, to scale', SPY.x, SPY.y + h + 21, { size: 14, color: C.muted, alpha: a });
}

/* ------------------------------------------------------------ (b) guided wave */
function panelB(st) {
  const yh = YB;
  panel('b', 20, yh, { alpha: seg(.05, .25) });
  text('guided wave testing', 58, yh, { size: 16, color: C.body, alpha: settle(.1, S) });
  const fo = fadeOut(st);
  const drawOutline = plate(PYB, seg(.05, .4), seg(.1, .25));
  let tm = null, front = 0;
  if (st.loop >= 0 && st.tau >= SHOT0) {
    tm = Math.min(M0 + (st.tau - SHOT0) / SLOW, G.shot_end_us * 1e-6);
    front = clamp(G.cg * (tm - G.tc), 0, G.span);
  }
  // the covered length, then the field on top of it (its zero is the fill under it)
  const covA = fo;
  if (front > 0) { ctx.save(); ctx.globalAlpha *= covA; ctx.fillStyle = C.mist; ctx.fillRect(XU(0), PYB, XU(front) - XU(0), PH); ctx.restore(); }
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
  text('transducer', XU(0) - 4, PYB - 46 - 6 * (1 - lIn), { size: LBL, color: C.body, alpha: lIn });
  text('next sensor position', XU(G.span), PYB - 46 - 6 * (1 - lIn), { size: LBL, color: C.body, align: 'right', alpha: lIn });
  // between the two sensors, what lies between them: the span the one shot inspects, dimensioned
  dimk(XU(0), XU(G.span), PYB - 24, G.spanlab, { size: LBL, color: C.ink, alpha: settle(.3, S) });
  lengthAxis(PYB, .1);
  // readouts
  const ca = settle(.3, S);
  const cw = covLine(950, yh, front / G.span * 100, ca * (tm === null ? 1 : fo));
  text('one transducer position', 950 - cw - 40, yh, { size: 16, color: C.body, align: 'right', alpha: ca });
  if (tm !== null) math(`t = ${Math.max(0, Math.round(tm * 1e6))}\\,\\rm{µs}`, 58, yh + 26, { size: LBL, alpha: fo * seg(st.b + SHOT0 - .3, .3) });
  math('\\rm{time slowed }' + G.slowtex, 146, yh + 26, { size: 14, color: C.muted, alpha: seg(.5, .3) });
  ascanB(st, tm, fo);
}
/* the received trace, on a time axis laid under the plate so that t maps to
   the distance c_g (t - t_c)/2: each echo sits under its flaw */
function ascanB(st, tm, fo) {
  const y0 = PYB + 96, h = 88, tmaxu = G.tmax * 1e6;
  const XT = tu => XU(G.cg * (tu * 1e-6 - G.tc) / 2);
  const ax = XT(0), aw = XT(tmaxu) - XT(0);
  const A = axes({ x: ax, y: y0, w: aw, h, xlim: [0, tmaxu], ylim: [-1.15, 1.15], xticks: [0, 100, 200, 300, 400, 500, 600, 700],
                   yticks: [-1, 0, 1], xlabel: 't\\ (\\rm{µs})', ylabel: 'u/u_0', ylabelGap: 34, progress: seg(.1, .4) });
  A.inside(() => line([[A.X(0), A.Y(0)], [A.X(tmaxu), A.Y(0)]], { color: C.rule, width: 1 }));
  // guides from each flaw down to where its echo is expected, burst centre + 2x/c_g
  const la = seg(.55, .3);
  G.flaws.forEach((f, n) => {
    const te = (G.tc + 2 * f.x / G.cg) * 1e6, x = A.X(te);
    line([[XU(f.x), PYB + PH + 22], [XU(f.x), y0]], { color: C.guide, width: 1, dash: [5, 4], alpha: la * .8 });
    A.inside(() => line([[x, y0], [x, y0 + h]], { color: C.guide, width: 1, dash: [5, 4], alpha: la }));
    keepText(`flaw ${n + 1} echo`, x + 6, y0 + 16, { size: 14, color: ACC, alpha: la });
  });
  keepText('initial pulse', A.X(64), A.Y(-.6), { size: 14, color: C.body, alpha: la });
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
      keepMath(`x = c_{\\rm{g}}t/2 = ${xl.toFixed(2)}\\,\\rm{m}`, A.X(tpk) + 6, y0 + h - 10, { size: 14, color: C.body, alpha: ra });
    });
    if (st.tau < SHOT1) {
      const cx = A.X(tm * 1e6);
      gapLine(cx, y0, y0 + h, { color: C.ink, width: 1, alpha: .55 * fo });   // behind the labels
      const inEcho = G.win_us.some(([wa, wb]) => tm * 1e6 >= wa && tm * 1e6 <= wb);
      dot(cx, A.Y(TRACE[k1 - 1]), 3, { color: inEcho ? ACC : C.navy, fill: inEcho ? ACC : C.navy, alpha: fo });
    }
  }
  // colour bar of the field in the plate
  const cb = seg(.45, .3), bx = 400, by = YB + 26;
  ctx.save(); ctx.globalAlpha *= cb; ctx.imageSmoothingEnabled = true; ctx.drawImage(BAR.cvs, bx, by - 8, 90, 8); ctx.restore();
  line([[bx, by - 8], [bx + 90, by - 8], [bx + 90, by], [bx, by], [bx, by - 8]], { color: C.ink, width: .8, alpha: cb });
  math('u_x/u_0', bx - 8, by, { size: 14, align: 'right', alpha: cb });
  for (const [v, s] of [[0, '-1'], [.5, '0'], [1, '1']]) { line([[bx + v * 90, by], [bx + v * 90, by + 3]], { color: C.ink, width: .8, alpha: cb }); math(s, bx + v * 90, by + 17, { size: 14, align: 'center', alpha: cb }); }
}

function draw() {
  const st = now();
  KEEP.length = 0;
  panelA(st);
  panelB(st);
  text(G.params, 500, H - 12, { size: 14, color: C.muted, align: 'center', alpha: seg(.6, .3) });
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
    t_step, t_scan = schedule(npos, [np.mean(l) for l in lit])
    print(f"{npos} probe positions; flaws under the zone at positions {lit}; scan {t_scan:.1f} s")

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
        slow=SLOW, slowtex=gu.sci_tex(SLOW), tc_us=tc * 1e6, f0=gu.F0, ncyc=gu.NCYC, cg=cg, span=SPAN, xend=xend, nx=nx, dx=dx,
        ppm=PPM, ph=PH_DRAW, thick_mm=THICK * 1e3, R=R_FLAW, T=T_FLAW, index_mm=INDEX * 1e3, npos=npos,
        tstep=t_step, tscan=t_scan, lit=lit, poster_scan=float(t_step[300]) + 0.25, shot_end_us=tmax * 1e6,
        wmid_mm=float(2 * np.interp(THICK / 2, zs, w) * 1e3), probe_mm=D_PROBE * 1e3,
        flaws=[dict(x=f["x"], z_mm=f["z"] * 1e3, L_mm=f["L"] * 1e3, h_mm=f["h"] * 1e3) for f in FLAWS],
        beam=dict(nx=len(xs), nz=len(zs), x0_mm=xs[0] * 1e3, dx_mm=0.25, z_mm=zs * 1e3, w_mm=w * 1e3,
                  a=common.i8(np.clip(A / A.max(), 0, 1) * 127)),
        c=dict(w=common.f32(comp["w"]), k=common.f32(comp["k"]), a=common.f32(comp["a"]), p=common.f32(comp["p"])),
        trace=common.f32(trace), dt_tr_us=dt_tr * 1e6, tmax_us=tmax * 1e6,
        echo_us=[e["t"] * 1e6 for e in echoes], win_us=[[v * 1e6 for v in e["win"]] for e in echoes],
        params_a=f"probe 10 mm, 5 MHz; N = {N_simple*1e3:.0f} mm; index {INDEX*1e3:g} mm",
        # (b), between the two sensors (29 Sep, "2 sensor arasına title"): the span one shot inspects
        spanlab=r"\rm{whole span inspected at once: }" + f"{SPAN:g}" + r"\,\rm{m}",
        params=(f"steel plate, d = 10 mm (drawn {exag:g} × thicker); S0 at 50 kHz, group velocity {cg:.0f} m/s; "
                f"flaws {FLAWS[0]['L']*1e3:g} mm long, reflection {R_FLAW:g}"),
    )
    title = "Figure 13: Coverage comparison between the two families of ultrasonic testing"
    aria = (f"On the same 2 m steel plate, a bulk wave probe steps along {npos} positions, each covering only "
            "the narrow zone beneath it, and a flaw lights up only when the probe is over it; a single guided "
            "wave shot from one transducer sweeps the whole span in 0.4 ms and returns an echo from each flaw.")
    common.build_html("coverage", title, aria, 1000, 716, data, JS)
    png = common.still("coverage")
    print("still:", png)
    res = dict(xs=xs, zs=zs, A=A, w=w, lam=lam, k0=k0, N_cf=N_cf, N_simple=N_simple, npos=npos, lit=lit,
               t_scan=t_scan, cp=cp, cg=cg, comp=comp, echoes=echoes, tc=tc, nx=nx, dx=dx, exag=exag)
    validate(res)
    return res


def validate(r):
    """Closed forms for the probe, the pulsed beam's convergence, coverage,
    echo times and the page's own sum; writes ut_coverage.check.txt."""
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
    # 6. the guided wave: echo times, and the page's own sum
    xg = np.arange(r["nx"]) * r["dx"]
    page = gu.check_page("coverage", [(f"fieldAt({tm!r})", gw_field(r["comp"], xg, tm)) for tm in (150e-6, 300e-6, 480e-6)])

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
    say("  The scan's pace on the page is designed (slow first steps, then fast, easing while a flaw")
    say(f"  is under the probe; {r['t_scan']:.1f} s in all); the positions and what each covers are the model's.")
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
    say(f"  Both strips on one scale, {PPM} units/m; the plate's thickness drawn {r['exag']:g} times enlarged, the")
    say(f"  inset under the probe drawn to scale (9 units/mm). Guided wave time slowed {SLOW:g} times.")
    say(f"  (b): between the transducer and the next sensor position, a dimension of the span one shot")
    say(f"  inspects, {SPAN:g} m (x = 0 to {SPAN:g} m on the strip's own scale), on a white knockout.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "ut_coverage.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
