"""Figure 1 of the sound document (sound-detection-and-tracking, image1).

His caption: "Figure 1. Sensor configurations: (a) linear array sensors (b)
circular array sensors." His picture (from Wang et al. 2020, Symphony) draws
(a) two sensors m and n at (rho_m, beta_m) and (rho_n, beta_n), d_{n,m}
apart, a plane wave arriving at the angle theta, the angle gamma at n, and
the Additional Distance the wave travels to m; (b) six sensors on a circle,
with d_{0,2}, gamma, theta, (rho, beta_2) and (rho, beta_0).

Model. A plane sound wave in air, c = 343 m/s (20 degrees C), comes from the
direction theta (from the x axis, the side it comes from): s = (cos, sin)
theta. A sensor at p hears its front at t(p) = t0 - p.s / c. The front that
has just reached n still has
    Additional Distance  Dd = (p_n - p_m).s = d_{n,m} cos(theta + gamma - beta_n)
to go before it reaches m (gamma: the angle at n between the chord to m and
the line to the origin, as he draws it), so m hears it tau = Dd / c later.
In (b), n = 0 (beta_0 = 0), m = 2, gamma = 30 degrees: Dd = d_{0,2} cos(theta +
gamma). The page moves the front at c, time slowed 10^4, and lights each
sensor when the front reaches it.

Run: python tools/numfig/snd_array.py [--look]
"""
import os
import sys

import numpy as np

import common
import snd_common

NAME = "snd-array"
HERE = os.path.dirname(os.path.abspath(__file__))

C_AIR = 343.0                      # m/s, dry air at 20 C
SLOW = 1e4                         # time slowed on the page
SC = 52.0                          # page units per cm, both panels
DEG = np.pi / 180

# (a) two sensors, polar coordinates about the origin O (cm, degrees)
A_RN, A_BN, A_RM, A_BM, A_TH = 6.0, 13.0, 4.5, 77.0, 30.0
# (b) six sensors on a circle of radius rho, sensor k at beta_k = 60 k degrees
B_R, B_TH = 3.0, 25.0

# where each panel sits on the page (page units) and the part the front sweeps
OA, CB = (70.0, 460.0), (735.0, 290.0)
RECT_A = (70.0, 64.0, 475.0, 460.0)      # the axes' extent: the front is drawn inside it
RECT_B = (530.0, 66.0, 985.0, 470.0)
T0, HOLD = 0.5, 1.5                # the loop starts, and rests after the sweeps (the result whole 2.6 s)


def unit(a):
    return np.array([np.cos(a), np.sin(a)])


def ang(v):
    return np.arctan2(v[1], v[0])


def between(u, v):
    """The angle from vector u to vector v, in (-pi, pi]."""
    return np.arctan2(u[0] * v[1] - u[1] * v[0], u @ v)


def corners(rect, origin):
    x0, y0, x1, y1 = rect
    return [np.array([(x - origin[0]) / SC, (origin[1] - y) / SC]) for x in (x0, x1) for y in (y0, y1)]


def sweep(rect, origin, s, points):
    """The front's travel over the panel: it starts where it first touches
    the panel and leaves where it last does (projections on s, cm), and the
    page time (s) at which it reaches each point."""
    pr = [c @ s for c in corners(rect, origin)]
    s0, s1 = max(pr) + 0.2, min(pr) - 0.2
    v = C_AIR * 100 / SLOW                     # cm per page second
    return s0, s1, v, [(s0 - p @ s) / v for p in points]


def gcc_phat_delay(a, b, fs, up=64):
    """The delay of b after a, s, from the peak of the generalised cross
    correlation with phase transform, interpolated by zero padding the
    cross spectrum `up` times."""
    n = a.size
    X = np.fft.rfft(b) * np.conj(np.fft.rfft(a))
    X /= np.abs(X) + 1e-30
    r = np.fft.irfft(X, n * up)
    k = int(np.argmax(r))
    if k > n * up // 2:
        k -= n * up
    return k / (fs * up)


def model():
    # ---- (a)
    pn = A_RN * unit(A_BN * DEG)
    pm = A_RM * unit(A_BM * DEG)
    sa = unit(A_TH * DEG)
    d_nm = np.linalg.norm(pm - pn)
    gam = abs(between(-pn, pm - pn))
    dd_a = (pn - pm) @ sa
    dd_a_formula = d_nm * np.cos(A_TH * DEG + gam - A_BN * DEG)
    Fa = pm + dd_a * sa                              # m's ray meets the front through n
    foot = Fa - pn                                   # the front through n is normal to s
    # ---- (b)
    pk = [B_R * unit(60 * k * DEG) for k in range(6)]
    sb = unit(B_TH * DEG)
    d_02 = np.linalg.norm(pk[2] - pk[0])
    gam_b = abs(between(-pk[0], pk[2] - pk[0]))
    dd_b = (pk[0] - pk[2]) @ sb
    dd_b_formula = d_02 * np.cos(B_TH * DEG + gam_b)
    Fb = pk[2] + dd_b * sb
    # ---- the page's clock: both fronts reach the far sensor at the poster
    s0a, s1a, v, ta = sweep(RECT_A, OA, sa, [pn, pm, Fa])
    s0b, s1b, _, tb = sweep(RECT_B, CB, sb, pk + [Fb])
    swa, swb = (s0a - s1a) / v, (s0b - s1b) / v
    hit = max(ta[1], tb[2]) + 0.02
    oa, ob = hit - ta[1], hit - tb[2]
    per = max(oa + swa, ob + swb) + HOLD
    return dict(pn=pn, pm=pm, sa=sa, d_nm=d_nm, gam=gam, dd_a=dd_a, dd_a_formula=dd_a_formula,
                Fa=Fa, foot=foot, pk=pk, sb=sb, d_02=d_02, gam_b=gam_b, dd_b=dd_b,
                dd_b_formula=dd_b_formula, Fb=Fb, s0a=s0a, s1a=s1a, s0b=s0b, s1b=s1b, v=v,
                ta=ta, tb=tb, oa=oa, ob=ob, per=per, hit=hit, swa=swa, swb=swb)


def validate(r):
    """Every length and delay three ways, and the delays a correlator would
    measure from sampled signals; returns the report."""
    L = []
    say = L.append
    tau_a, tau_b = r["dd_a"] / 100 / C_AIR, r["dd_b"] / 100 / C_AIR
    say("Figure 1 (nf-snd-array): sensor configurations, (a) linear array sensors,")
    say("(b) circular array sensors. Generator: tools/numfig/snd_array.py")
    say("")
    say("MODEL")
    say(f"  A plane sound wave in air, c = {C_AIR:g} m/s (20 C), from the direction theta (measured")
    say("  from the x axis, on the side it comes from), s = (cos theta, sin theta). A sensor at p")
    say("  hears the front at t(p) = t0 - p.s / c. The front that has just reached the reference")
    say("  sensor n has the Additional Distance Dd = (p_n - p_m).s still to go before it reaches m;")
    say("  m hears it tau = Dd / c later.")
    say("  gamma, as he draws it: the angle at n between the chord to m and the line from n to the")
    say("  origin. The chord's direction is then beta_n + pi - gamma, and")
    say("    Dd = d_{n,m} cos(theta + gamma - beta_n).")
    say("  Symphony (Wang et al. 2020, eq. 6) writes the relative delay as")
    say("  d_{n,m} cos(pi - (gamma - beta_n) - theta) / v; cos(pi - x) = -cos x, so it is the same")
    say("  length, its sign set by which of the two sensors is counted first.")
    say("")
    say("(a) LINEAR ARRAY SENSORS")
    say(f"  n at (rho_n, beta_n) = ({A_RN:g} cm, {A_BN:g} deg), m at (rho_m, beta_m) = ({A_RM:g} cm, {A_BM:g} deg),")
    say(f"  theta = {A_TH:g} deg")
    say(f"  d_{{n,m}} = {r['d_nm']:.4f} cm, gamma = {r['gam'] / DEG:.3f} deg")
    say(f"  Additional Distance: (p_n - p_m).s = {r['dd_a']:.6f} cm")
    say(f"                       d cos(theta + gamma - beta_n) = {r['dd_a_formula']:.6f} cm"
        f" (difference {abs(r['dd_a'] - r['dd_a_formula']):.1e})")
    fm = np.linalg.norm(r["Fa"] - r["pm"])
    say(f"                       the drawn construction, |m F| with F on m's ray and nF normal to s:")
    say(f"                       {fm:.6f} cm; nF.s = {r['foot'] @ r['sa']:.1e} (a right angle at F)")
    say(f"  time delay tau = Dd / c = {tau_a * 1e6:.3f} us")
    say("")
    say("(b) CIRCULAR ARRAY SENSORS")
    say(f"  six sensors on a circle of radius rho = {B_R:g} cm, sensor k at beta_k = 60 k deg; theta = {B_TH:g} deg")
    say(f"  d_{{0,2}} = rho sqrt(3) = {r['d_02']:.4f} cm ({B_R * np.sqrt(3):.4f}), gamma = {r['gam_b'] / DEG:.3f} deg")
    say(f"  Additional Distance: (p_0 - p_2).s = {r['dd_b']:.6f} cm")
    say(f"                       d_{{0,2}} cos(theta + gamma) = {r['dd_b_formula']:.6f} cm"
        f" (difference {abs(r['dd_b'] - r['dd_b_formula']):.1e})")
    fb = np.linalg.norm(r["Fb"] - r["pk"][2])
    say(f"                       |2 F| = {fb:.6f} cm")
    say(f"  time delay tau = Dd / c = {tau_b * 1e6:.3f} us")
    rel = [((r["pk"][0] - p) @ r["sb"]) / 100 / C_AIR * 1e6 for p in r["pk"]]
    order = sorted(range(6), key=lambda k: rel[k])
    say("  every sensor's delay after sensor 0 (us): "
        + ", ".join(f"{k}: {rel[k]:.2f}" for k in range(6)))
    say("  the front reaches them in the order " + ", ".join(str(k) for k in order)
        + ": all six apart, whatever theta")
    say(f"  spacing of neighbours rho = {B_R:g} cm: no spatial aliasing below c / (2 rho) ="
        f" {C_AIR / (2 * B_R / 100):.0f} Hz")
    say("")
    # ---- a correlator's view: sampled signals, delayed exactly, GCC-PHAT
    fs, n = 48000, 8192
    rng = np.random.default_rng(1)
    src = rng.standard_normal(n)
    S = np.fft.rfft(src)
    f = np.fft.rfftfreq(n, 1 / fs)

    def at(delay):
        return np.fft.irfft(S * np.exp(-2j * np.pi * f * delay), n)

    say("CHECK: the delays a correlator measures. White noise (48 kHz, 8192 samples) arriving")
    say("  at each sensor with its plane-wave delay (applied exactly, as a phase in the frequency")
    say("  domain); GCC-PHAT between the pair, its peak found on a grid 64 times finer:")
    est_a = gcc_phat_delay(at(0.0), at(tau_a), fs)
    say(f"  (a) n, m: {est_a * 1e6:.3f} us against tau = {tau_a * 1e6:.3f} us"
        f" (error {abs(est_a - tau_a) * 1e6:.3f} us; one sample is {1e6 / fs:.2f} us)")
    sig = [at(rel[k] * 1e-6) for k in range(6)]
    errs = []
    for k in range(1, 6):
        e = gcc_phat_delay(sig[0], sig[k], fs)
        errs.append(abs(e - rel[k] * 1e-6))
    est_b = gcc_phat_delay(sig[0], sig[2], fs)
    say(f"  (b) 0, 2: {est_b * 1e6:.3f} us against tau = {tau_b * 1e6:.3f} us;"
        f" all five pairs (0, k) within {max(errs) * 1e6:.3f} us")
    say("")
    say("DISPLAY")
    say(f"  both panels at {SC:g} page units per cm; the front moves at c, time slowed {SLOW:.0e}:")
    say(f"  {r['v']:.2f} cm of travel per second of the page; it crosses the extra distance of (a)"
        f" in {r['dd_a'] / r['v']:.2f} s")
    say(f"  and of (b) in {r['dd_b'] / r['v']:.2f} s. The loop is {r['per']:.2f} s; both fronts reach"
        f" the far sensor (m, 2)")
    say(f"  {r['hit']:.2f} s into it; the printed frame is that moment.")
    say("  The red Additional Distance grows from F to m exactly as the front travels it; each")
    say("  sensor lights when the front reaches it. The front is drawn only inside the axes and is")
    say("  left out where it would pass a label or a sensor (the gap a TikZ node's white fill leaves).")
    say("  The intro: the axes and his two rays per panel are drawn from their far ends, each arrow's head")
    say("  fading in once its shaft is longer than the head (no bare heads in the first frames).")
    say("  Type: the labels with subscripts ((rho_m, beta_m), d_{n,m}, Delta d, ...) are 20, so their")
    say("  subscripts are 14; the formula lines 18 (subscripts 12.6); the parameter line 15.")
    say("  Type: the engine sets Greek in CMU Serif, whose theta and rho are its Greek-text shapes")
    say("  (TeX's vartheta, and a rho with a curled tail); TeX's math italic theta and rho (the")
    say("  closed theta, the plain rho) are in Latin Modern Math, which the figure fonts do not carry.")
    return "\n".join(L) + "\n", tau_a, tau_b, rel


JS = r"""
const D = DATA, A = D.a, B = D.b;
const POSTER_T = D.poster;
const SC = D.sc, VPX = D.v * SC;          // page units per cm; the front's speed, units per s
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const OA = D.oa, CB = D.cb, RD = 15;      // the panels' origins; a sensor's radius
const T0 = D.t0, PER = D.per;
const phase = () => t < T0 ? -1 : (t - T0) % PER;
const scr = (O, p) => [O[0] + p[0] * SC, O[1] - p[1] * SC];
const add = (p, v, k = 1) => [p[0] + k * v[0], p[1] + k * v[1]];
const sub = (p, q) => [p[0] - q[0], p[1] - q[1]];
const nrm = v => { const l = Math.hypot(v[0], v[1]); return [v[0] / l, v[1] / l]; };
const dir = a => [Math.cos(a), -Math.sin(a)];         // an angle (y up) as a page direction
const DG = Math.PI / 180;

/* ---------------------------------------------------------------- helpers */
/* the part of segment pq inside rect (x0, y0, x1, y1), or null */
function clipSeg(p, q, r) {
  const dx = q[0] - p[0], dy = q[1] - p[1];
  let u0 = 0, u1 = 1;
  for (const [pp, qq] of [[-dx, p[0] - r[0]], [dx, r[2] - p[0]], [-dy, p[1] - r[1]], [dy, r[3] - p[1]]]) {
    if (pp === 0) { if (qq < 0) return null; continue; }
    const k = qq / pp;
    if (pp < 0) u0 = Math.max(u0, k); else u1 = Math.min(u1, k);
  }
  return u1 > u0 ? [[p[0] + u0 * dx, p[1] + u0 * dy], [p[0] + u1 * dx, p[1] + u1 * dy]] : null;
}
/* segment pq drawn around the keep-outs (label boxes, sensor discs): the
   gaps a TikZ node's white fill would leave, without a box */
function cutLine(p, q, keep, o) {
  const dx = q[0] - p[0], dy = q[1] - p[1];
  let spans = [[0, 1]];
  for (const k of keep) {
    let a, b;
    if (k.r) {
      const fx = p[0] - k.x, fy = p[1] - k.y, qa = dx * dx + dy * dy, qb = 2 * (fx * dx + fy * dy), qc = fx * fx + fy * fy - k.r * k.r;
      const disc = qb * qb - 4 * qa * qc; if (disc <= 0) continue;
      a = (-qb - Math.sqrt(disc)) / (2 * qa); b = (-qb + Math.sqrt(disc)) / (2 * qa);
    } else {
      const c = clipSeg(p, q, [k.x0, k.y0, k.x1, k.y1]); if (!c) continue;
      const L2 = dx * dx + dy * dy;
      a = ((c[0][0] - p[0]) * dx + (c[0][1] - p[1]) * dy) / L2; b = ((c[1][0] - p[0]) * dx + (c[1][1] - p[1]) * dy) / L2;
    }
    const next = [];
    for (const [u0, u1] of spans) {
      if (b <= u0 || a >= u1) { next.push([u0, u1]); continue; }
      if (a > u0) next.push([u0, a]);
      if (b < u1) next.push([b, u1]);
    }
    spans = next;
  }
  for (const [u0, u1] of spans) if (u1 - u0 > 1e-3) line([[p[0] + u0 * dx, p[1] + u0 * dy], [p[0] + u1 * dx, p[1] + u1 * dy]], o);
}
/* an arc about c from angle a0 to a1 (radians, y up), as a stroke */
function arc(c, r, a0, a1, o) {
  const pts = []; for (let i = 0; i <= 40; i++) { const a = a0 + (a1 - a0) * i / 40; pts.push([c[0] + r * Math.cos(a), c[1] - r * Math.sin(a)]); }
  line(pts, o);
}
/* a label: its box (for the front to go round) and its drawing */
function box(kind, s, x, y, o) {
  const size = o.size || 17;
  let w;
  if (kind === 'm') w = math(s, 0, -1e4, { size, alpha: 0 });
  else { ctx.save(); ctx.font = font({ size }); w = ctx.measureText(s).width; ctx.restore(); }
  const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  return { x0: x0 - 4, x1: x0 + w + 4, y0: y - .82 * size - 3, y1: y + .4 * size + 3 };
}
function put(L, alpha) {
  for (const [kind, s, x, y, o] of L) (kind === 'm' ? math : text)(s, x, y, { ...o, alpha: (o.alpha ?? 1) * alpha });
}
/* a sensor: a navy disc, its name in white; amber while the front passes it */
function sensor(p, name, a, flash) {
  if (a <= 0) return;
  const r = RD * (.85 + .15 * a);
  ctx.save(); ctx.globalAlpha *= a;
  ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 2 * Math.PI); ctx.fillStyle = C.navy; ctx.fill();
  if (flash > .01) { ctx.globalAlpha *= flash; ctx.fillStyle = C.amber; ctx.fill(); ctx.globalAlpha /= flash; }
  ctx.strokeStyle = C.ink; ctx.lineWidth = 1.3; ctx.stroke(); ctx.restore();
  math(name, p[0], p[1] + 6, { size: 18, color: '#fff', align: 'center', alpha: a });
}
/* a right angle mark at F, between the directions u and v */
function rightAngle(F, u, v, k, o) {
  line([add(F, u, k), add(add(F, u, k), v, k), add(F, v, k)], o);
}
/* the wave's ray of length L along u, arriving at tip as p goes from 0 to 1: drawn
   from its far end, its head fading in once its shaft is longer than the head */
function ray(tip, u, L, p) {
  const len = L * p;
  if (len <= 0) return;
  const tail = add(tip, u, L), now = add(tail, u, -len), ha = clamp((len - 14) / 12);
  if (ha < 1) line([tail, add(now, u, ha * 7)], { width: 1.8 });
  if (ha > 0) arrow(tail[0], tail[1], now[0], now[1], { width: 1.8, head: 12, alpha: ha });
}
/* an axis drawn from (x1, y1) to (x2, y2) as p goes from 0 to 1, its head likewise */
function axisArrow(x1, y1, x2, y2, p) {
  if (p <= 0) return;
  const ex = lerp(x1, x2, p), ey = lerp(y1, y2, p), len = Math.hypot(ex - x1, ey - y1), ha = clamp((len - 12) / 12);
  if (ha < 1) line([[x1, y1], [ex, ey]], { width: 1.4 });
  if (ha > 0) arrow(x1, y1, ex, ey, { width: 1.4, head: 10, alpha: ha });
}
/* the flash of a sensor the front reached at page time th (in the loop) */
const flashAt = (ph, th) => ph < th ? 0 : Math.exp(-(ph - th) / .45);

/* ---------------------------------------------------------------- a panel's wave */
function wave(P, O, rect, keep) {
  /* P: {s0, s1, off, th}, the front's travel (cm along s) and start (s in the loop) */
  const ph = phase();
  if (ph < 0) return null;
  const u = ph - P.off;
  if (u < 0) return null;
  const S = P.s0 - D.v * u;                   // the front: p.s = S
  if (S < P.s1) return { S, on: false };
  const s = [Math.cos(P.th), Math.sin(P.th)];
  const Q = scr(O, [S * s[0], S * s[1]]), f = [-Math.sin(P.th), -Math.cos(P.th)];
  const c = clipSeg(add(Q, f, -1500), add(Q, f, 1500), rect);
  const fade = 1 - clamp((ph - (PER - .35)) / .3);
  if (c) cutLine(c[0], c[1], keep, { color: C.blue, width: 2.2, alpha: fade });
  return { S, on: true };
}

/* ================================================================ (a) */
const pn = scr(OA, A.pn), pm = scr(OA, A.pm), FA = scr(OA, A.F), SA = dir(A.th);
const LA = [
  ['m', 'x', 468, OA[1] + 26, { size: 18, align: 'center' }],
  ['m', 'y', OA[0] - 18, 80, { size: 18, align: 'center' }],
  ['m', '(\\rho_{m},\\ \\beta_{m})', pm[0] - 6, pm[1] - 30, { size: 20, align: 'center' }],
  ['m', '(\\rho_{n},\\ \\beta_{n})', pn[0] + 4, pn[1] + 42, { size: 20, align: 'center' }],
  ['m', 'd_{n,m}', A.dlab[0], A.dlab[1], { size: 20, align: 'center' }],
  ['m', '\\gamma', A.glab[0], A.glab[1], { size: 20, align: 'center' }],
  ['m', '\\theta', A.tlab[0], A.tlab[1], { size: 20, align: 'center' }],
  ['t', 'Additional Distance', A.alab[0], A.alab[1], { size: 17, color: C.accent, align: 'center' }],
  ['m', '\\Delta d', A.ddlab[0], A.ddlab[1], { size: 20, color: C.accent, align: 'center' }],
];
let KA = null;
function panelA() {
  const ph = phase(), off = A.off, P = { s0: A.s0, s1: A.s1, off, th: A.th };
  panel('a', 18, 30, { alpha: lab(0) });
  text('linear array sensors', 54, 30, { size: 18, color: C.body, alpha: lab(.04) });
  if (!KA) KA = LA.map(([k, s, x, y, o]) => box(k, s, x, y, o)).concat([pn, pm].map(p => ({ x: p[0], y: p[1], r: RD + 3 })));
  // the axes
  const ap = seg(0, .4);
  axisArrow(OA[0], OA[1], 475, OA[1], ap);
  axisArrow(OA[0], OA[1], OA[0], 64, ap);
  // the geometry he draws, grey and dashed
  const gp = seg(.12, .35), G = { color: C.guide, width: 1.1, dash: [5, 4] };
  line([OA, add(pm, nrm(sub(OA, pm)), RD + 1)], { ...G, progress: gp });
  line([OA, add(pn, nrm(sub(OA, pn)), RD + 1)], { ...G, progress: gp });
  line([add(pn, [1, 0], RD + 2), add(pn, [1, 0], 80)], { ...G, progress: gp });
  line([add(pn, nrm(sub(FA, pn)), RD + 2), FA], { ...G, progress: seg(.2, .35) });
  const ua = nrm(sub(pm, pn)), da = seg(.22, .3);
  if (da > 0) arrow(add(pn, ua, RD + 3)[0], add(pn, ua, RD + 3)[1], add(pm, ua, -RD - 3)[0], add(pm, ua, -RD - 3)[1],
                    { color: C.guide, width: 1.1, head: 8, both: true, dash: [5, 4], alpha: da });
  const aa = seg(.25, .3);
  arc(pn, 40, A.th_on, A.th_om, { color: C.guide, width: 1.3, progress: aa });
  arc(pn, 54, 0, A.th, { color: C.guide, width: 1.3, progress: aa });
  // the wave: his two rays, and the front itself sweeping in
  const ra = seg(.15, .35);
  ray(add(pn, SA, RD + 3), SA, 96, ra);
  ray(FA, SA, 96, ra);
  const w = wave(P, OA, D.rect_a, KA);
  // the Additional Distance: faint until the front has passed n, then drawn as it travels
  const mEdge = add(pm, SA, RD + 1), full = Math.hypot(FA[0] - mEdge[0], FA[1] - mEdge[1]);
  line([FA, mEdge], { color: C.accent, width: 2.6, alpha: .22 * seg(.3, .3) });
  let g = 0;
  if (w) g = w.S >= A.sF ? 0 : clamp((A.sF - w.S) * SC / full);
  const reset = ph < 0 ? 0 : 1 - clamp((ph - (PER - .35)) / .3);
  if (g > 0) line([FA, add(FA, SA, -full * g)], { color: C.accent, width: 2.6, alpha: reset });
  rightAngle(FA, nrm(sub(pm, FA)), nrm(sub(pn, FA)), 9, { color: C.accent, width: 1.2, alpha: seg(.3, .3) });
  const pa = seg(.35, .25);
  arrow(A.alab[0], A.alab[1] + 8, A.alab[0], A.aline - 7, { color: C.accent, width: 1.5, head: 9, alpha: pa });
  // the sensors, lit as the front reaches them
  const sa = settle(.08, .28);
  sensor(pn, 'n', sa, flashAt(ph, off + A.tn));
  sensor(pm, 'm', sa, flashAt(ph, off + A.tm));
  put(LA, lab(.3));
  // what it gives
  const fa = lab(.45);
  math(`\\Delta d = d_{n,m}\\,\\rm{cos}(\\theta\\ + \\gamma\\ - \\beta_{n}) = ${A.dd.toFixed(2)}\\,\\rm{cm},\\quad \\tau\\ = \\Delta d/c = ${A.tau.toFixed(1)}\\,\\rm{µs}`,
       22, 512, { size: 18, alpha: fa });
}

/* ================================================================ (b) */
const PK = B.pk.map(p => scr(CB, p)), FB = scr(CB, B.F), SB = dir(B.th);
const LB = [
  ['m', 'x', 982, CB[1] + 26, { size: 18, align: 'center' }],
  ['m', 'y', CB[0] - 18, 78, { size: 18, align: 'center' }],
  ['m', '(\\rho,\\ \\beta_{2})', PK[2][0] - 40, PK[2][1] - 30, { size: 20, align: 'center' }],
  ['m', '(\\rho,\\ \\beta_{0})', PK[0][0] + 30, PK[0][1] + 44, { size: 20, align: 'center' }],
  ['m', 'd_{0,2}', B.dlab[0], B.dlab[1], { size: 20, align: 'center' }],
  ['m', '\\Delta d', B.ddlab[0], B.ddlab[1], { size: 20, color: C.accent, align: 'center' }],
  ['m', '\\gamma', B.glab[0], B.glab[1], { size: 20, align: 'center' }],
  ['m', '\\theta', B.tlab[0], B.tlab[1], { size: 20, align: 'center' }],
];
let KB = null;
function panelB() {
  const ph = phase(), off = B.off, P = { s0: B.s0, s1: B.s1, off, th: B.th };
  panel('b', 520, 30, { alpha: lab(.02) });
  text('circular array sensors', 556, 30, { size: 18, color: C.body, alpha: lab(.06) });
  const discs = PK.map(p => ({ x: p[0], y: p[1], r: RD + 3 }));
  if (!KB) KB = LB.map(([k, s, x, y, o]) => box(k, s, x, y, o)).concat(discs);
  // the axes, round the sensors that sit on them
  const ap = seg(.03, .4);
  if (ap > 0) {
    cutLine([530, CB[1]], [530 + (975 - 530) * ap, CB[1]], discs, { width: 1.4 });
    if (ap >= 1) arrow(975, CB[1], 985, CB[1], { width: 1.4, head: 10 });
    axisArrow(CB[0], 470, CB[0], 66, ap);
  }
  // the hexagon he draws, light; the radius to sensor 2 and the chord 0 to 2, grey
  const hp = seg(.1, .4);
  for (let k = 0; k < 6; k++) {
    const p = PK[k], q = PK[(k + 1) % 6], u = nrm(sub(q, p));
    line([add(p, u, RD + 2), add(q, u, -RD - 2)], { color: C.rule, width: 1.3, dash: [4, 4], progress: hp });
  }
  const gp = seg(.18, .35), G = { color: C.guide, width: 1.1, dash: [5, 4] };
  line([CB, add(PK[2], nrm(sub(CB, PK[2])), RD + 1)], { ...G, progress: gp });
  line([add(PK[0], nrm(sub(FB, PK[0])), RD + 2), FB], { ...G, progress: seg(.22, .35) });
  const ub = nrm(sub(PK[2], PK[0])), da = seg(.24, .3);
  if (da > 0) arrow(add(PK[0], ub, RD + 3)[0], add(PK[0], ub, RD + 3)[1], add(PK[2], ub, -RD - 3)[0], add(PK[2], ub, -RD - 3)[1],
                    { color: C.guide, width: 1.1, head: 8, both: true, dash: [5, 4], alpha: da });
  const aa = seg(.27, .3);
  arc(PK[0], 40, 150 * DG, Math.PI, { color: C.guide, width: 1.3, progress: aa });
  arc(PK[0], 54, 0, B.th, { color: C.guide, width: 1.3, progress: aa });
  // the rays, and the front
  const ra = seg(.17, .35);
  ray(add(PK[0], SB, RD + 3), SB, 80, ra);
  ray(FB, SB, 80, ra);
  const w = wave(P, CB, D.rect_b, KB);
  const mEdge = add(PK[2], SB, RD + 1), full = Math.hypot(FB[0] - mEdge[0], FB[1] - mEdge[1]);
  line([FB, mEdge], { color: C.accent, width: 2.6, alpha: .22 * seg(.32, .3) });
  let g = 0;
  if (w) g = w.S >= B.sF ? 0 : clamp((B.sF - w.S) * SC / full);
  const reset = ph < 0 ? 0 : 1 - clamp((ph - (PER - .35)) / .3);
  if (g > 0) line([FB, add(FB, SB, -full * g)], { color: C.accent, width: 2.6, alpha: reset });
  rightAngle(FB, nrm(sub(PK[2], FB)), nrm(sub(PK[0], FB)), 9, { color: C.accent, width: 1.2, alpha: seg(.32, .3) });
  const sa = settle(.1, .28);
  for (let k = 0; k < 6; k++) sensor(PK[k], String(k), sa, flashAt(ph, off + B.tk[k]));
  put(LB, lab(.32));
  const fa = lab(.47);
  math(`\\Delta d = d_{0,2}\\,\\rm{cos}(\\theta\\ + \\gamma) = ${B.dd.toFixed(2)}\\,\\rm{cm},\\quad \\tau\\ = \\Delta d/c = ${B.tau.toFixed(1)}\\,\\rm{µs}`,
       524, 512, { size: 18, alpha: fa });
}

function draw() {
  panelA(); panelB();
  math(D.params, 22, H - 10, { size: 15, color: C.muted, alpha: lab(.6) });
}
boot();
"""


def page_data(r, tau_a, tau_b):
    OAv, CBv = np.array(OA), np.array(CB)

    def scr(O, p):
        return O + np.array([p[0], -p[1]]) * SC

    pn, pm, Fa = scr(OAv, r["pn"]), scr(OAv, r["pm"]), scr(OAv, r["Fa"])
    # label spots, from the geometry: d beside the chord's middle, gamma and theta on
    # their bisectors, the Additional Distance above its segment
    um = (pm - pn) / np.linalg.norm(pm - pn)
    dlab_a = (pn + pm) / 2 + 26 * np.array([-um[1], um[0]]) * np.sign(-um[1] or 1) * -1
    if dlab_a[1] < ((pn + pm) / 2)[1]:
        dlab_a = (pn + pm) / 2 - (dlab_a - (pn + pm) / 2)
    dlab_a = dlab_a + np.array([0, 6])
    th_om = np.arctan2(*(r["pm"] - r["pn"])[::-1])              # n to m, y up
    th_on = np.arctan2(-r["pn"][1], -r["pn"][0])                # n to O
    if th_on - th_om < -np.pi:                                  # the short way round
        th_on += 2 * np.pi
    mid_g = (th_on + th_om) / 2
    glab_a = pn + 60 * np.array([np.cos(mid_g), -np.sin(mid_g)]) + np.array([0, 6])
    th = A_TH * DEG
    tlab_a = pn + 72 * np.array([np.cos(th / 2), -np.sin(th / 2)]) + np.array([0, 6])
    sa_scr = np.array([np.cos(th), -np.sin(th)])
    xa = 188.0                                                  # the label's centre
    # where the red segment is under it
    t_ = (xa - pm[0]) / sa_scr[0]
    aline = pm[1] + t_ * sa_scr[1]
    alab = np.array([xa, Fa[1] - 36])

    def ddspot(p, q, at, off):
        # beside the red segment p to q, `at` of the way, `off` units to its lower right
        u = (q - p) / np.linalg.norm(q - p)
        nrm = np.array([-u[1], u[0]])
        if nrm[1] < 0:
            nrm = -nrm
        return p + at * (q - p) + off * nrm + np.array([0, 6])

    ddlab_a = ddspot(pm, Fa, 0.62, 20)
    # (b)
    pk = [scr(CBv, p) for p in r["pk"]]
    ub = (pk[2] - pk[0]) / np.linalg.norm(pk[2] - pk[0])
    nb = np.array([-ub[1], ub[0]])
    if nb[1] > 0:
        nb = -nb
    dlab_b = (pk[0] + pk[2]) / 2 + 24 * nb + np.array([0, 6])
    glab_b = pk[0] + 60 * np.array([np.cos(165 * DEG), -np.sin(165 * DEG)]) + np.array([0, 6])
    tb_ = B_TH * DEG
    tlab_b = pk[0] + 74 * np.array([np.cos(tb_ / 2), -np.sin(tb_ / 2)]) + np.array([0, 6])
    ddlab_b = ddspot(pk[2], scr(CBv, r["Fb"]), 0.78, 20)
    return {
        "poster": T0 + r["hit"] + 0.04, "sc": SC, "v": r["v"], "t0": T0, "per": r["per"],
        "oa": list(OA), "cb": list(CB), "rect_a": list(RECT_A), "rect_b": list(RECT_B),
        "a": {"pn": r["pn"], "pm": r["pm"], "F": r["Fa"], "th": th, "th_on": th_on, "th_om": th_om,
              "s0": r["s0a"], "s1": r["s1a"], "off": r["oa"], "tn": r["ta"][0], "tm": r["ta"][1],
              "sF": float(r["Fa"] @ r["sa"]), "dd": r["dd_a"], "tau": tau_a * 1e6,
              "dlab": dlab_a, "glab": glab_a, "tlab": tlab_a, "alab": alab, "aline": aline,
              "ddlab": ddlab_a},
        "b": {"pk": r["pk"], "F": r["Fb"], "th": B_TH * DEG, "s0": r["s0b"], "s1": r["s1b"],
              "off": r["ob"], "tk": r["tb"][:6], "sF": float(r["Fb"] @ r["sb"]), "dd": r["dd_b"],
              "tau": tau_b * 1e6, "dlab": dlab_b, "glab": glab_b, "tlab": tlab_b,
              "ddlab": ddlab_b},
        "params": (r"\rm{sound in air, }c = %g\,\rm{m/s;\ \ time slowed }10^{4}\,\times;\ \ \ "
                   r"(\rm{a})\ \rho_{n} = %g\,\rm{cm},\ \beta_{n} = %g\deg,\ \rho_{m} = %g\,\rm{cm},\ "
                   r"\beta_{m} = %g\deg,\ \theta\ = %g\deg;\ \ \ (\rm{b})\ \rho\ = %g\,\rm{cm},\ "
                   r"\beta_{k} = 60\deg\,k,\ \theta\ = %g\deg"
                   % (C_AIR, A_RN, A_BN, A_RM, A_BM, A_TH, B_R, B_TH)),
    }


def main():
    r = model()
    txt, tau_a, tau_b, rel = validate(r)
    with open(os.path.join(HERE, "snd_array.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    data = page_data(r, tau_a, tau_b)
    title = "Figure 1: Sensor configurations: (a) linear array sensors (b) circular array sensors"
    aria = ("Two microphone arrays and a plane sound wave. (a) A pair of sensors m and n: the wave front "
            "that reaches n still has an additional distance to travel to m, which gives the time delay "
            "between them. (b) Six sensors on a circle: the front reaches each at a different time.")
    common.build_html(NAME, title, aria, 1000, 556, data, JS)
    print("still:", common.still(NAME))
    snd_common.append(os.path.join(HERE, "snd_array.check.txt"), snd_common.loop_overlaps(NAME, data["t0"] + data["per"] + 0.4))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.2, 3.0, 4.0]))
    return r


if __name__ == "__main__":
    main()
