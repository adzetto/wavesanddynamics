"""Figure 6: propagation zones in a periodically supported infinite beam.

Model: an Euler-Bernoulli beam on equally spaced pin supports, infinite in
both directions, analysed exactly as a monocoupled periodic structure (Mead
1970, 1975): the span transfer matrix on (rotation, moment) from support to
support gives the propagation constant mu per span, cosh mu = T11. A wave
propagates freely where mu is purely imaginary (the propagation zones) and
decays by exp(-Re mu) per span elsewhere. Every shape drawn is the model's:
the band edge waves (a), the span modes at the zone edges (b), the Bloch
wave inside zone 1 (d), the evanescent wave in the first stop band (e).

Run: python tools/numfig/periodic.py
"""
import os

import numpy as np
from scipy.optimize import brentq, minimize_scalar

import beam_model as bm
import common

NAME = "periodic"
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ the beam
E, RHO = 210e9, 7850.0             # steel
B, HT = 0.040, 0.010               # bar 40 mm wide, 10 mm deep
L = 0.50                           # support spacing (m)
EI = E * B * HT ** 3 / 12          # 700 N m^2
M = RHO * B * HT                   # 3.14 kg/m
SPANS_C = (0.52, 0.50, 0.48)       # (c): three slightly different spans (m)
FMAX = 700.0                       # (b) frequency axis (Hz)

fz = lambda z, Ls=L: bm.freq_from_z(z, Ls, EI, M)
zf = lambda f, Ls=L: bm.z_from_freq(f, Ls, EI, M)
Z_SS = [n * np.pi for n in (1, 2, 3)]
Z_CC = [bm.cc_root(n) for n in (1, 2, 3)]

# ------------------------------------------------------------------ zones
edges = bm.band_edges(12.0)                      # exact |cosh mu| = 1
z_edges = [z for z, _ in edges]
f_edges = [fz(z) for z in z_edges]               # SS1, CC1, SS2, CC2, SS3, CC3
zones = [(f_edges[0], f_edges[1]), (f_edges[2], f_edges[3])]

# attenuation Re mu over 0..FMAX, dense where it rises like a square root
fg = list(np.linspace(0.25, FMAX, 1400))
for fe in f_edges[:4]:
    fg += list(fe + np.geomspace(1e-4, 12, 40)) + list(fe - np.geomspace(1e-4, 12, 40))
fg = np.array(sorted(set(v for v in fg if 0 < v <= FMAX) | set(f_edges[:4])))
delta = np.array([bm.propagation_constant(zf(f)).real for f in fg])
delta[np.isin(fg, f_edges[:4])] = 0.0
delta_static = np.arccosh(2.0)                   # z -> 0: cosh mu -> -2

# ------------------------------------------------------------------ (d), (e)
z_d = brentq(bm.cosh_mu, np.pi + 1e-9, Z_CC[0] - 1e-9, xtol=1e-15)    # kappa = pi/2
f_d = fz(z_d)
res = minimize_scalar(lambda z: -bm.cosh_mu(z), bounds=(Z_CC[0], 2 * np.pi),
                      method="bounded", options={"xatol": 1e-12})
z_e = res.x                                       # strongest attenuation, stop band 1
f_e = fz(z_e)
delta_e = np.arccosh(bm.cosh_mu(z_e))

NX = 101                                          # points per span
xi = np.linspace(0, 1, NX)


def bloch_span(z, direction=+1):
    lam, th0, M0, k = bm.bloch_wave(z, L, EI, M, direction)
    w = np.array([bm.span_shape(th0, M0, k, L, EI, x) for x in xi * L])
    w = w / w[np.argmax(np.abs(w))]               # max |w| = 1, real at the peak
    return lam, th0, M0, k, w


lam_d, th_d, M_d, k_d, w_d = bloch_span(z_d)
lam_e, th_e, M_e, k_e, w_e = bloch_span(z_e)
w_e = np.real(w_e)
xm_e = xi[np.argmax(np.abs(w_e))]

# ------------------------------------------------------------------ band edge waves (a), span modes (b)
def edge_wave(z, theta0, M0):
    k = z / L
    w = np.array([bm.span_shape(theta0, M0, k, L, EI, x) for x in xi * L])
    return w / w[np.argmax(np.abs(w))]


w_ss1 = edge_wave(Z_SS[0], 1.0, 0.0)             # eigenvector (1, 0): lam = -1
w_cc1 = edge_wave(Z_CC[0], 0.0, 1.0)             # eigenvector (0, 1): lam = +1
w_ss2 = edge_wave(Z_SS[1], 1.0, 0.0)             # lam = +1
w_cc2 = edge_wave(Z_CC[1], 0.0, 1.0)             # lam = -1


def cc_mode(z):
    s = (np.cosh(z) - np.cos(z)) / (np.sinh(z) - np.sin(z))
    x = z * xi
    w = np.cosh(x) - np.cos(x) - s * (np.sinh(x) - np.sin(x))
    return w / w[np.argmax(np.abs(w))]


# ------------------------------------------------------------------ validation
lines = []
say = lines.append
say("nf-periodic: Figure 6, propagation zones of a beam on periodic pin supports")
say("")
say("MODEL")
say("  Euler-Bernoulli beam, infinite, pin supports every L; harmonic e^{i w t}.")
say("  Exact span transfer matrix on (rotation, moment) between two pins, from the")
say("  closed form field matrix (Krylov functions); propagation constant mu per span")
say("  from cosh mu = T11 = S - T U / V at z = k L (Mead 1970, monocoupled periodic).")
say(f"  steel bar {B*1e3:.0f} x {HT*1e3:.0f} mm, E = {E/1e9:.0f} GPa, rho = {RHO:.0f} kg/m^3:"
    f" EI = {EI:.1f} N m^2, m = {M:.3f} kg/m, L = {L} m (L/h = {L/HT:.0f}, EB valid)")
say("  No mesh: every quantity is closed form; roots by Brent's method to 1e-15 in z.")
say("")
say("CHECK 1: zone edges against single span frequencies (closed form)")
say("  edge        z computed          z closed form        |dz|       f (Hz)")
names = ["SS1 (n pi)", "CC1 (4.7300)", "SS2 (2 pi)", "CC2 (7.8532)", "SS3 (3 pi)", "CC3 (10.996)"]
ref = [Z_SS[0], Z_CC[0], Z_SS[1], Z_CC[1], Z_SS[2], Z_CC[2]]
worst = 0.0
for nm, (z, sgn), zr in zip(names, edges, ref):
    worst = max(worst, abs(z - zr))
    say(f"  {nm:12s} {z:.12f}  {zr:.12f}  {abs(z-zr):.1e}   {fz(z):9.3f}   cosh mu = {sgn:+.0f}")
say(f"  worst |dz| = {worst:.1e}; f(z) = (z/L)^2 sqrt(EI/m)/(2 pi), so df/f = 2 dz/z")
say("  zone 1 = [SS1, CC1], zone 2 = [SS2, CC2]: bounded by the simply supported and")
say("  fixed fixed span frequencies, as the text states.")
say("")
say("CHECK 2: static limit (continuous beam carry over)")
c0 = bm.cosh_mu(1e-3)
say(f"  cosh mu(z -> 0) = {c0:.6f} (closed form -2); e^mu = -(2 - sqrt 3) = {-(2-np.sqrt(3)):.6f},"
    f" Re mu = {delta_static:.6f}")
say("")
say("CHECK 3: transfer matrix is reciprocal (det T = 1) and symmetric (T11 = T22)")
dets = [abs(np.linalg.det(bm.span_T(z / L, L, EI)) - 1) for z in np.linspace(0.2, 9.5, 400)]
say(f"  max |det T - 1| over z in [0.2, 9.5]: {max(dets):.1e}")
say("")
say("CHECK 4: band edge waves (a) against the closed form span modes")
say(f"  SS wave  vs sin(pi x/L):          max |dw| = {np.max(np.abs(w_ss1 - np.sin(np.pi*xi))):.1e}")
say(f"  CC wave  vs clamped clamped mode: max |dw| = {np.max(np.abs(w_cc1 - cc_mode(Z_CC[0]))):.1e}")
say(f"  SS2 mode vs sin(2 pi x/L):        max |dw| = {np.max(np.abs(np.abs(w_ss2) - np.abs(np.sin(2*np.pi*xi)))):.1e}")
say(f"  CC2 mode vs clamped clamped mode: max |dw| = {np.max(np.abs(np.abs(w_cc2) - np.abs(cc_mode(Z_CC[1])))):.1e}")
T1 = bm.span_T(Z_SS[0] / L, L, EI); T2 = bm.span_T(Z_CC[0] / L, L, EI)
say(f"  T at SS1 maps (1,0) to {T1 @ [1, 0]} (lam = -1: adjacent spans alternate)")
say(f"  T at CC1 maps (0,1) to {T2 @ [0, 1]} (lam = +1: all spans alike)")
say("")
say("CHECK 5: Bloch wave (d), direct transfer across one span and one support")
Q0 = bm.span_state0(th_d, M_d, k_d, L, EI)
yL = bm.field(L, k_d, EI) @ np.array([0, th_d, M_d, Q0])
say(f"  w(L) = {abs(yL[0]):.1e} (pin); |[theta, M](L) - lam [theta, M](0)| ="
    f" {abs(yL[1]-lam_d*th_d)+abs(yL[2]-lam_d*M_d):.1e} (relative to |M| {abs(M_d):.2e})")
P = bm.power_at_support(th_d, M_d, 2 * np.pi * f_d)
say(f"  lam = exp({np.log(lam_d):.6f}), |lam| - 1 = {abs(lam_d)-1:.1e}; power flow P = {P:.3e} > 0 (to +x)")
say("")
say("CHECK 6: a finite beam of 10 equal spans has 10 modes in each zone (Mead)")
cb = bm.ContinuousBeam([(L, EI, M)] * 10)
fN = cb.frequencies(20)
in1 = np.sum((fN >= zones[0][0] - 1e-9) & (fN <= zones[0][1] + 1e-9))
in2 = np.sum((fN >= zones[1][0] - 1e-9) & (fN <= zones[1][1] + 1e-9))
say(f"  first 20 frequencies (Hz): {np.array2string(fN, precision=1, max_line_width=200)}")
say(f"  in zone 1: {in1} of 10, in zone 2: {in2} of 10; FE cross check (Hermite, 16 el/span):")
fFE = bm.fe_frequencies([(L, EI, M)] * 10, 16, 20)
say(f"  max relative difference exact vs FE: {np.max(np.abs(fFE/fN-1)):.1e}")
say("")
say("OPERATING POINTS")
say(f"  (d) f = {f_d:.3f} Hz (z = {z_d:.6f}, the pinned clamped span root 3.926602),"
    f" cosh mu = 0, mu = i pi/2 per span, no decay")
say(f"  (e) f = {f_e:.3f} Hz (z = {z_e:.6f}), the strongest attenuation in the first stop band:"
    f" Re mu = {delta_e:.4f}, e^(-Re mu) = {np.exp(-delta_e):.4f} per span, lam = {np.real(lam_e):+.4f}")
say(f"  attenuation below zone 1 tends to Re mu = {delta_static:.4f} at f -> 0")
say("")
say("(c) THREE SPANS, EACH WITH ITS OWN FIRST ZONE")
zc = []
for i, Ls in enumerate(SPANS_C):
    lo, hi = fz(Z_SS[0], Ls), fz(Z_CC[0], Ls)
    zc.append((lo, hi))
    say(f"  span {i+1}: L = {Ls:.2f} m, zone 1 = [{lo:.1f}, {hi:.1f}] Hz")
common_zone = (max(z[0] for z in zc), min(z[1] for z in zc))
say(f"  common zone = [{common_zone[0]:.1f}, {common_zone[1]:.1f}] Hz")

SLOW = 200
say("")
say(f"TIME: slowed {SLOW} x: every wave oscillates at f/{SLOW} on screen"
    f" ({f_edges[0]/SLOW:.2f} Hz for SS1 up to {f_edges[3]/SLOW:.2f} Hz for CC2).")

check = "\n".join(lines) + "\n"
print(check)
with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(check)

# ------------------------------------------------------------------ data for the page
DATA = {
    "slow": SLOW,
    "xi": xi,
    "edges": f_edges[:4],
    "fmax": FMAX,
    "spec": {"f": fg, "d": delta},
    "a": {"ss": w_ss1, "cc": w_cc1, "fss": f_edges[0], "fcc": f_edges[1]},
    "b": {"ss1": w_ss1, "cc1": w_cc1, "ss2": w_ss2, "cc2": w_cc2},
    "c": {"L": list(SPANS_C), "zones": zc, "common": list(common_zone)},
    "d": {"f": f_d, "re": np.real(w_d), "im": np.imag(w_d), "arg": float(np.angle(lam_d)),
          "amax": float(np.max(np.abs(w_d)))},
    "e": {"f": f_e, "w": w_e, "lam": float(np.real(lam_e)), "delta": delta_e, "xm": xm_e,
          "amax": float(np.max(np.abs(w_e)))},
}

JS = r"""
const POSTER_T = __POSTER_T__;            // the moment every standing wave is nearest its extreme
const SLOW = DATA.slow, XI = DATA.xi, NX = XI.length;
const TS = 0.35, RAMP = 0.25;             // the physics starts at TS, full speed by TS + RAMP
function clock() { const s = t - TS; return s <= 0 ? 0 : s < RAMP ? s * s / (2 * RAMP) : s - RAMP / 2; }
const phase = f => 2 * Math.PI * f / SLOW * clock();
const lab = t0 => settle(t0, .28);        // labels arrive

/* a beam row: n spans of length Lp from x0 at height y, pins, dots at both ends */
function beamRow(x0, y, Lp, n, prog, o = {}) {
  const { pinS = 12, dots = true, alpha = 1 } = o;
  line([[x0, y], [x0 + n * Lp, y]], { color: C.ink, width: 1.8, progress: prog, alpha });
  if (prog <= 0) return;
  for (let i = 0; i <= n; i++) {
    const a = clamp((prog * n - i) * 4 + 1) * alpha;
    if (a > 0) pin(x0 + i * Lp, y, { s: pinS, alpha: a });
  }
  if (dots) for (const s of [-1, 1]) for (let k = 1; k <= 3; k++) {
    const xx = s < 0 ? x0 - 8 - 7 * k : x0 + n * Lp + 8 + 7 * k;
    dot(xx, y, 1.5, { color: C.ink, alpha: alpha * (s < 0 ? clamp(prog * 6) : clamp(prog * 6 - 5)) });
  }
}
/* polyline of a wave over spans: shape(n, i) gives the value at XI[i] of span n */
function wavePts(x0, y, Lp, n, A, shape) {
  const pts = [];
  for (let s = 0; s < n; s++) for (let i = (s ? 1 : 0); i < NX; i++)
    pts.push([x0 + (s + XI[i]) * Lp, y - A * shape(s, i)]);
  return pts;
}
/* the engine's dim(), its knockout opaque from the first frame: the line never
   shows through the label while both fade in */
function dimk(x1, x2, y, label, o) {
  const { alpha = 1, size = 17 } = o;
  dim(x1, x2, y, '', { alpha });
  if (alpha <= 0) return;
  const w = math(label, 0, -1e4, { size, alpha: 0 });
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect((x1 + x2) / 2 - w / 2 - 4, y - size * .62, w + 8, size * 1.42); ctx.restore();
  math(label, (x1 + x2) / 2, y + size * .34, { size, align: 'center', alpha });
}
function sub(letter, x, y, words, a) {
  panel(letter, x, y, { alpha: a });
  if (words) text(words, x + 38, y, { size: 16, color: C.body, alpha: a });
}

/* ------------------------------------------------ (a) the two band edge waves */
function drawA() {
  sub('a', 18, 34, 'two freely propagating waves', lab(0));
  const y = 108, Lp = 128, A = 36;
  const rows = [
    { x0: 62, w: DATA.a.ss, sgn: s => (s % 2 ? -1 : 1), f: DATA.a.fss,
      lab: 'first mode, simply supported span', mu: '\\mu\\ = i\\pi' },
    { x0: 560, w: DATA.a.cc, sgn: s => 1, f: DATA.a.fcc,
      lab: 'first mode, fixed fixed span', mu: '\\mu\\ = 0' },
  ];
  rows.forEach((r, k) => {
    beamRow(r.x0, y, Lp, 3, seg(.05 * k, .35));
    const q = Math.cos(phase(r.f));
    const pts = wavePts(r.x0, y, Lp, 3, A * q, (s, i) => r.sgn(s) * r.w[i]);
    line(pts, { color: C.blue, width: 2.4, progress: seg(.2 + .05 * k, .4) });
    const la = lab(.45 + .05 * k);
    if (k === 0) { const da = lab(.5); if (da > 0) dimk(r.x0 + 3, r.x0 + Lp - 3, y + 52, 'L', { alpha: da, size: 16 }); }
    text(r.lab, r.x0 + 1.5 * Lp, y + 80 + 5 * (1 - la), { size: 15, color: C.body, align: 'center', alpha: la });
    math(`f = ${r.f.toFixed(1)}\\,\\rm{Hz},\\ \\ ${r.mu}`, r.x0 + 1.5 * Lp, y + 101 + 5 * (1 - la),
         { size: 15, align: 'center', color: C.ink, alpha: la });
  });
}

/* ------------------------------------------------ (b) the spectrum */
function drawB() {
  const y0 = 238;
  sub('b', 18, y0, 'propagation zones', lab(.04));
  const ax = { x: 112, y: y0 + 88, w: 846, h: 132 };
  const [e1, e2, e3, e4] = DATA.edges;
  const X = v => ax.x + v / DATA.fmax * ax.w;
  // zones behind the axis
  const za = seg(.2, .3), zl = lab(.45);
  if (za > 0) for (const [lo, hi, name] of [[e1, e2, '1st propagation zone'], [e3, e4, '2nd propagation zone']]) {
    ctx.save(); ctx.globalAlpha = za; ctx.fillStyle = C.steel;
    ctx.fillRect(X(lo), ax.y, X(hi) - X(lo), ax.h); ctx.restore();
    text(name, (X(lo) + X(hi)) / 2, ax.y + 22, { size: 14, color: C.navy, align: 'center', alpha: zl });   // clear of the edge guides
  }
  const g = axes({ ...ax, xlim: [0, DATA.fmax], ylim: [0, 1.5],
    xticks: [0, 100, 200, 300, 400, 500, 600, 700], yticks: [0, .5, 1, 1.5],
    xlabel: '\\rm{frequency}\\ \\ f\\ (\\rm{Hz})', ylabel: '\\rm{Re}\\,\\mu', ylabelGap: 50, progress: seg(.04, .4),
    yfmt: v => v === 0 ? '0' : v.toFixed(1) });
  // attenuation per span: the computed curve
  const F = DATA.spec.f, D = DATA.spec.d;
  const pts = F.map((f, i) => [g.X(f), g.Y(D[i])]);
  g.inside(() => line(pts, { color: C.navy, width: 2.2, progress: seg(.28, .45) }));
  text('attenuation per span', g.X(294), g.Y(1.3), { size: 15, color: C.navy, align: 'center', alpha: lab(.7) });
  // edge guides and the span modes that bound the zones, arriving from above
  const sk = [[e1, DATA.b.ss1, 'ss'], [e2, DATA.b.cc1, 'cc'], [e3, DATA.b.ss2, 'ss'], [e4, DATA.b.cc2, 'cc']];
  sk.forEach(([f, w, kind], k) => {
    const s = lab(.5 + .05 * k);
    if (s <= 0) return;
    const cx = X(f), yb = y0 + 44 - 8 * (1 - s), Lp = 62, A = 11, xs = cx - Lp / 2;
    line([[cx, ax.y], [cx, ax.y + ax.h]], { color: C.guide, width: 1, dash: [5, 4], alpha: s });
    line([[xs, yb], [xs + Lp, yb]], { color: C.ink, width: 1.5, alpha: s });
    const q = Math.cos(phase(f));
    line(XI.map((v, i) => [xs + v * Lp, yb - A * q * w[i]]), { color: C.blue, width: 1.8, alpha: s });
    if (kind === 'ss') { pin(xs, yb, { s: 8, alpha: s }); pin(xs + Lp, yb, { s: 8, alpha: s }); }
    else { fixedEnd(xs, yb, { h: 18, dir: 1, alpha: s }); fixedEnd(xs + Lp, yb, { h: 18, dir: -1, alpha: s }); }
    text(f.toFixed(1), cx, yb + 34, { size: 14, color: C.muted, align: 'center', alpha: s });
  });
  // the operating points of (d) and (e), gliding along the computed curve
  const interp = f => { let i = 1; while (i < F.length - 1 && F[i] < f) i++;
    const u = (f - F[i - 1]) / (F[i] - F[i - 1]); return lerp(D[i - 1], D[i], clamp(u)); };
  [[DATA.d.f, '(d)', .7], [DATA.e.f, '(e)', .76]].forEach(([f, name, t0]) => {
    const s = settle(t0, .45);
    if (s <= 0) return;
    const ff = lerp(0.25, f, s), px = g.X(ff), py = g.Y(interp(ff));
    dot(px, py, 4.2, { color: C.accent, fill: C.accent, alpha: clamp(s * 3) });
    // the name arrives with its point: it would cut the curve where it climbs steeply on the way
    text(name, px, py - 11, { size: 15, bold: true, color: C.accent, align: 'center', alpha: clamp((s - .9) / .08) });
  });
}

/* ------------------------------------------------ (c) three slightly different spans */
function drawC() {
  const y0 = 524;
  sub('c', 18, y0, 'a nearly periodic beam', lab(.08));
  const Ls = DATA.c.L, sc = 262, y = y0 + 84, x0 = 62;
  const xs = [x0]; Ls.forEach(l => xs.push(xs[xs.length - 1] + l * sc));
  const p = seg(.08, .4);
  line([[x0 - 26, y], [xs[3] + 26, y]], { color: C.ink, width: 1.8, progress: p });
  xs.forEach(x => { const a = clamp(((p * (xs[3] - x0 + 52) - 26 - (x - x0)) / 20) + 1); if (a > 0) pin(x, y, { s: 12, alpha: a }); });
  for (const s of [-1, 1]) for (let k = 1; k <= 3; k++)
    dot(s < 0 ? x0 - 30 - 7 * k : xs[3] + 30 + 7 * k, y, 1.5, { alpha: s < 0 ? clamp(p * 6) : clamp(p * 6 - 5) });
  const dash = [null, [9, 5], [2.5, 3.5]];
  Ls.forEach((l, i) => {
    const cx = (xs[i] + xs[i + 1]) / 2, a = lab(.5 + .05 * i);
    text(`span ${i + 1}`, cx, y - 22 + 5 * (1 - a), { size: 15, color: C.body, align: 'center', alpha: a });
    if (a > 0) {
      dim(xs[i] + 3, xs[i + 1] - 3, y + 34, '', { alpha: a });
      math(`L_{${i + 1}} = ${l.toFixed(2)}\\,\\rm{m}`, cx, y + 60 + 5 * (1 - a), { size: 15, align: 'center', alpha: a });
    }
  });
  // the zones: each span's first zone as a pair of lines, the common zone shaded
  const ax = { x: 600, y: y0 + 8, w: 358, h: 128 };
  const g = axes({ ...ax, xlim: [80, 240], ylim: [0, 4], xticks: [80, 120, 160, 200, 240], yticks: [],
    xlabel: '\\rm{frequency}\\ \\ f\\ (\\rm{Hz})', progress: seg(.12, .4) });
  const [clo, chi] = DATA.c.common, ca = seg(.62, .25);
  if (ca > 0) {
    ctx.save(); ctx.globalAlpha = ca; ctx.fillStyle = C.steel;
    ctx.fillRect(g.X(clo), ax.y + 1, g.X(chi) - g.X(clo), ax.h - 2); ctx.restore();
    text('common zone', (g.X(clo) + g.X(chi)) / 2, g.Y(.45) + 5, { size: 15, color: C.navy, align: 'center', alpha: lab(.7) });
  }
  DATA.c.zones.forEach(([lo, hi], i) => {
    const yy = g.Y(3.4 - i), pz = seg(.3 + .05 * i, .3);
    for (const f of [lo, hi]) line([[g.X(f), yy - 15], [g.X(f), yy + 15]], { color: C.navy, width: 2.2, dash: dash[i], progress: pz });
    line([[g.X(lo), yy], [g.X(hi), yy]], { color: C.navy, width: 1.1, dash: dash[i], progress: pz, alpha: .8 });
    text(`span ${i + 1}`, ax.x - 8, yy + 5, { size: 15, align: 'right', alpha: lab(.35 + .05 * i) });
  });
}

/* ------------------------------------------------ (d), (e) one wave in a zone, one outside */
function drawRow(letter, words, y0, t0, kind) {
  sub(letter, 18, y0, words, lab(t0));
  const y = y0 + 62, x0 = 66, Lp = 108.5, n = 8, A = 38;
  beamRow(x0, y, Lp, n, seg(t0, .4), { pinS: 11 });
  const ph = phase(kind === 'd' ? DATA.d.f : DATA.e.f);
  let pts;
  if (kind === 'd') {
    const D = DATA.d;
    pts = wavePts(x0, y, Lp, n, A, (s, i) => {
      const ps = s * D.arg + ph; return D.re[i] * Math.cos(ps) - D.im[i] * Math.sin(ps); });
  } else {
    const Ee = DATA.e, q = Math.cos(ph);
    pts = wavePts(x0, y, Lp, n, A, (s, i) => Math.pow(Ee.lam, s) * Ee.w[i] * q);
  }
  // the envelope: e^{-Re mu per span}, through the span maxima
  const ea = seg(t0 + .43, .35);
  if (ea > 0) {
    const d = kind === 'd' ? 0 : DATA.e.delta, am = kind === 'd' ? DATA.d.amax : DATA.e.amax;
    const xm = kind === 'd' ? 0 : DATA.e.xm;
    for (const sg of [-1, 1]) {
      const env = [];
      for (let k = 0; k <= 160; k++) { const u = xm + k / 160 * (n - xm); env.push([x0 + u * Lp, y - sg * A * am * Math.exp(-d * (u - xm))]); }
      line(env, { color: kind === 'd' ? C.guide : C.accent, width: 1.2, dash: [5, 4], alpha: ea, progress: ea });
    }
  }
  line(pts, { color: C.blue, width: 2.4, progress: seg(t0 + .18, .4) });
  const la = lab(t0 + .68);
  if (kind === 'd') math(`f = ${DATA.d.f.toFixed(0)}\\,\\rm{Hz},\\ \\ \\rm{Re}\\,\\mu\\ = 0`, 958, y0, { size: 16, align: 'right', alpha: la });
  else math(`f = ${DATA.e.f.toFixed(0)}\\,\\rm{Hz},\\ \\ \\rm{Re}\\,\\mu\\ = ${DATA.e.delta.toFixed(2)},\\ \\ e^{-\\rm{Re}\\,\\mu} = ${Math.exp(-DATA.e.delta).toFixed(2)}`,
            958, y0, { size: 16, align: 'right', alpha: la });
}

function draw() {
  drawA(); drawB(); drawC();
  drawRow('d', 'inside a propagation zone', 750, .12, 'd');
  drawRow('e', 'outside a propagation zone', 890, .17, 'e');
  const fa = lab(.95);
  text('steel bar 40 × 10 mm, E = 210 GPa, ρ = 7850 kg/m³, pin supports every L = 0.5 m',
       18, H - 14, { size: 14, color: C.muted, alpha: fa });
  text(`time slowed ${SLOW} ×`, W - 18, H - 14, { size: 14, color: C.muted, align: 'right', alpha: fa });
}
boot();
"""


def poster_time(freqs, ts=0.35, ramp=0.25, t_lo=1.45, t_hi=20.0):
    """The still: the first moment after the intro when every standing wave
    is nearest its extreme (largest smallest |cos(phase)|), on the page's clock."""
    tt = np.arange(t_lo, t_hi, 0.001)
    c = tt - ts - ramp / 2
    m = np.min(np.abs(np.cos(2 * np.pi * np.outer(np.array(freqs) / SLOW, c))), axis=0)
    j = int(np.argmax(m - 0.004 * (tt - t_lo)))
    return float(tt[j]), float(m[j])


POSTER, POSTER_M = poster_time([f_edges[0], f_edges[1], f_edges[2], f_edges[3], f_e])
JS = JS.replace("__POSTER_T__", f"{POSTER:.3f}")
print(f"POSTER_T = {POSTER:.3f} s: every standing wave at >= {100*POSTER_M:.1f} % of its amplitude")

TITLE = "Figure 6: Propagation zones in a periodically supported infinite beam"
ARIA = ("Five panels computed from an exact periodic beam model: the two band edge waves on pin "
        "supported spans; the attenuation per span against frequency with the first and second "
        "propagation zones shaded between the simply supported and fixed fixed span frequencies; "
        "three slightly different spans and their overlapping first zones; a wave inside a zone "
        "travelling at full amplitude; and a wave outside a zone decaying span by span.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 1034, DATA, JS)
    print(common.still(NAME))
