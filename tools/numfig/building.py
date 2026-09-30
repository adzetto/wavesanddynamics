"""Figure 1 of the waves guide: the lateral natural dynamic response of a
building and its analysis through the discretized formulation.

A five storey shear building: rigid floors with lumped masses m1..m5 (floor 1
at the bottom), storeys of lateral stiffness k1..k5 (storey 1 at the ground),
M = diag(m), K tridiagonal (k1 + k2, -k2; ...; -k5, k5), exactly the matrices
under the figure. The eigenproblem K phi = w^2 M phi is solved (scipy.linalg.
eigh, mass-normalised modes). The building is set vibrating by a lateral
impulse at the roof, x(0) = 0, M x'(0) = [0, 0, 0, 0, m5 v0]: its undamped free
vibration is exactly x(t) = sum_j phi_j (phi_j^T M x'(0) / w_j) sin(w_j t), drawn
as the total and, term by term, as the 1st mode, the 2nd mode and the higher
modes (3 to 5), each at its own computed frequency. Columns take the exact
shape of a fixed-fixed column between two rigid floors (cubic).

Run: python tools/numfig/building.py [--look]   (writes content/anim/
nf-building.html and .webp and tools/numfig/building.check.txt)
"""
import os
import sys

import numpy as np
import scipy.linalg as sla

import common

NAME = "building"
HERE = os.path.dirname(os.path.abspath(__file__))

M_T = np.array([200.0, 200.0, 200.0, 200.0, 150.0])     # t, floor 1 (bottom) .. roof
K_MN = np.array([350.0, 330.0, 300.0, 260.0, 210.0])     # MN/m, storey 1 (ground) .. 5
H_S = 3.2                                                # m, storey height
ROOF_AMP = 1.5e-3                                        # m, 1st mode amplitude at the roof
SLOW = 5.0                                               # time slowed
DEF = 800.0                                              # displacements drawn x DEF
MAG = [1, 2, 4]                                          # 1st, 2nd, higher panels, relative
T0 = 0.45                                                # s, the impulse (motion from here)
HL0, HL_DT = 1.4, 1.8                                    # storey highlight: start, s per storey


def matrices(m, k):
    n = len(m)
    K = np.zeros((n, n))
    for s in range(n):            # storey s joins floor s - 1 (the ground for s = 0) and floor s
        K[s, s] += k[s]
        if s:
            K[s - 1, s - 1] += k[s]
            K[s - 1, s] -= k[s]
            K[s, s - 1] -= k[s]
    return np.diag(m), K


def modes(M, K):
    w2, Phi = sla.eigh(K, M)                 # mass-normalised: Phi^T M Phi = I
    Phi = Phi * np.sign(Phi[-1])             # roof positive
    return np.sqrt(w2), Phi


def compute():
    m, k = M_T * 1e3, K_MN * 1e6
    M, K = matrices(m, k)
    w, Phi = modes(M, K)
    n = len(m)
    # the impulse at the roof: modal velocities phi_j^T M x'(0), amplitudes / w_j
    e = np.zeros(n); e[-1] = 1.0
    g = Phi.T @ M @ e / w                     # per unit roof velocity
    v0 = ROOF_AMP / abs(g[0] * Phi[-1, 0])
    Q = g * v0                                # q_j(t) = Q_j sin(w_j t), m
    R = dict(m=m, k=k, M=M, K=K, w=w, Phi=Phi, Q=Q, v0=v0)
    # checks
    R["res"] = max(np.linalg.norm(K @ Phi[:, j] - w[j] ** 2 * M @ Phi[:, j]) / np.linalg.norm(K @ Phi[:, j])
                   for j in range(n))
    R["orth"] = np.abs(Phi.T @ M @ Phi - np.eye(n)).max()
    R["kortho"] = np.abs(Phi.T @ K @ Phi - np.diag(w ** 2)).max() / w[-1] ** 2
    # uniform building against the closed form w_j = 2 sqrt(k/m) sin((2j - 1) pi / (2(2n + 1)))
    Mu, Ku = matrices(np.full(n, 200e3), np.full(n, 400e6))
    wu, _ = modes(Mu, Ku)
    wc = 2 * np.sqrt(400e6 / 200e3) * np.sin((2 * np.arange(1, n + 1) - 1) * np.pi / (2 * (2 * n + 1)))
    R["uniform"] = (wu, wc)
    # superposition against the exact state-space solution x(t) = expm(A t) [0; x'(0)]
    A = np.block([[np.zeros((n, n)), np.eye(n)], [-np.linalg.solve(M, K), np.zeros((n, n))]])
    z0 = np.concatenate([np.zeros(n), v0 * e])
    err = 0.0
    for tt in np.linspace(0.05, 3.0, 12):
        x_ex = (sla.expm(A * tt) @ z0)[:n]
        x_mod = Phi @ (Q * np.sin(w * tt))
        err = max(err, np.abs(x_ex - x_mod).max() / np.abs(x_ex).max())
    R["super"] = err
    # effective modal masses (base excitation): sum = total mass
    iota = np.ones(n)
    gam = Phi.T @ M @ iota
    R["meff"] = gam ** 2
    # Rayleigh quotient of the static roof-load shape (upper bound on w1)
    xs = np.linalg.solve(K, M @ iota)
    R["rayleigh"] = np.sqrt(xs @ K @ xs / (xs @ M @ xs))
    return R


def poster_time(R):
    """A moment in the storey 3 highlight where all three terms are well away
    from zero (the printed frame shows each panel deformed)."""
    w, Q, Phi = R["w"], R["Q"], R["Phi"]
    best, tb = -1, None
    lo, hi = HL0 + 2 * HL_DT + 0.35, HL0 + 3 * HL_DT - 0.35
    for t in np.linspace(lo, hi, 2000):
        s = np.sin(w * (t - T0) / SLOW)
        c = Q * s
        r1, r2 = abs(c[0] * Phi[-1, 0]) / abs(Q[0] * Phi[-1, 0]), abs(c[1]) / abs(Q[1])
        hi_ = Phi[:, 2:] @ c[2:]
        r3 = np.abs(hi_).max() / np.abs(Phi[:, 2:] @ np.abs(Q[2:])).max()
        score = min(r1, r2, r3)
        if score > best:
            best, tb = score, t
    return float(round(tb, 3)), best


def check(R, tp):
    L = []
    p = L.append
    w, Phi, Q = R["w"], R["Phi"], R["Q"]
    f = w / 2 / np.pi
    p("Figure 1 (nf-building): lateral natural vibration of a five storey shear building")
    p("")
    p("MODEL (floor 1 at the bottom, storey 1 at the ground; the matrices of the figure)")
    p("  m_1 .. m_5 = " + ", ".join(f"{x:.0f}" for x in M_T) + " t")
    p("  k_1 .. k_5 = " + ", ".join(f"{x:.0f}" for x in K_MN) + " MN/m, storey height "
      f"{H_S} m")
    p("  M = diag(m), K = [k1 + k2, -k2; -k2, k2 + k3, -k3; ...; -k5, k5]; C = 0 in the animation")
    p("  K (MN/m):")
    for row in R["K"] / 1e6:
        p("    " + "  ".join(f"{x:7.0f}" for x in row))
    p("")
    p("EIGENPROBLEM K phi = w^2 M phi (scipy.linalg.eigh, mass-normalised)")
    for j in range(5):
        p(f"  mode {j+1}: f = {f[j]:7.4f} Hz, T = {1/f[j]:.4f} s, phi (floor 1..5, roof = 1) = "
          + ", ".join(f"{x/Phi[-1, j]:+.4f}" for x in Phi[:, j]))
    p(f"  residual max |K phi - w^2 M phi| / |K phi| = {R['res']:.1e}")
    p(f"  orthogonality max |Phi^T M Phi - I| = {R['orth']:.1e}, max |Phi^T K Phi - W^2| / w5^2 = {R['kortho']:.1e}")
    wu, wc = R["uniform"]
    p("  the same solver on a uniform building (m = 200 t, k = 400 MN/m) against the closed form")
    p("  w_j = 2 sqrt(k/m) sin((2j - 1) pi / 22):")
    p("    " + ", ".join(f"f_{j+1} {wu[j]/2/np.pi:.6f} Hz ({wu[j]/wc[j]-1:+.1e})" for j in range(5)))
    p(f"  Rayleigh quotient of the static shape under floor inertia loads: f = {R['rayleigh']/2/np.pi:.4f} Hz"
      f" >= f_1 ({R['rayleigh']/w[0]-1:+.2e})")
    meff = R["meff"]
    p("  effective modal masses (t): " + ", ".join(f"{x/1e3:.1f}" for x in meff)
      + f"; sum {meff.sum()/1e3:.3f} t = total mass {M_T.sum():.0f} t")
    p("")
    p("THE MOTION")
    p(f"  a lateral impulse at the roof, x(0) = 0, x'(0) = {R['v0']*1e3:.3f} mm/s at floor 5, chosen so that")
    p(f"  the 1st mode's roof amplitude is {ROOF_AMP*1e3:.1f} mm; q_j(t) = Q_j sin(w_j t),"
      " Q_j = phi_j^T M x'(0) / w_j")
    p("  roof amplitude of each term (mm): " + ", ".join(f"{abs(Q[j]*Phi[-1, j])*1e3:.4f}" for j in range(5)))
    p("  roof amplitude of each term, relative to the 1st: "
      + ", ".join(f"{abs(Q[j]*Phi[-1, j])/abs(Q[0]*Phi[-1, 0]):.3f}" for j in range(5)))
    p(f"  the sum of the modal terms against the exact state-space solution expm(A t):"
      f" max relative error {R['super']:.1e}")
    p(f"  displacements drawn x {DEF:.0f}; the 2nd mode panel x {MAG[1]} more and the higher modes"
      f" x {MAG[2]} more (stated in the figure)")
    p(f"  time slowed {SLOW:.0f}: on screen f_1 = {f[0]/SLOW:.3f} Hz ... f_5 = {f[-1]/SLOW:.3f} Hz;"
      f" the impulse at t = {T0} s of the page's clock")
    p(f"  poster (printed frame) at t = {tp} s")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
const N = 5;
const lab = t0 => settle(t0, .28);         // a label arriving
const rise = s => 4 * (1 - s);             // ... settling 4 units into place

/* ---------------------------------------------------------------- layout */
const GY = 452, SH = 62, BW = 96;          // ground, storey height, building width
const CX = [156, 398, 618, 838];           // total, 1st, 2nd, higher modes
const lev = i => GY - i * SH;              // floor i (0 = ground)
const G = D.gain;                          // drawing units per metre of displacement

/* ---------------------------------------------------------------- the motion
   x_i(t) = sum_j Q_j phi_j(i) sin(w_j (t - T0) / SLOW), zero before the impulse */
function terms() {
  const tau = Math.max(0, t - D.t0) / D.slow;
  return D.Q.map((q, j) => q * Math.sin(D.w[j] * tau));
}
function disp(c, js, mag) {                // floor displacements (units) of the modes js
  const u = [0];
  for (let i = 0; i < N; i++) { let s = 0; for (const j of js) s += c[j] * D.phi[j][i]; u.push(s * G * mag); }
  return u;
}
const ENV = [0, 1].map(j => [0].concat(D.phi[j].map(v => Math.abs(D.Q[j]) * v * G * D.mag[j])));

/* ---------------------------------------------------------------- drawing */
function column(cx, x0, u, s, o) {         // the column of storey s: fixed-fixed, cubic
  const pts = [];
  for (let q = 0; q <= 14; q++) {
    const e = q / 14, h = 3 * e * e - 2 * e * e * e;
    pts.push([cx + x0 + u[s - 1] + (u[s] - u[s - 1]) * h, lev(s - 1) - SH * e]);
  }
  line(pts, o);
}
function building(cx, u, o = {}) {
  const {color = C.blue, width = 1.8, dash = null, alpha = 1, progress = 1, thin = false, hl = 0, hs = 0} = o;
  const pr = progress * N;
  for (let s = 1; s <= N; s++) {
    const ps = clamp(pr - (s - 1));
    if (ps <= 0) break;
    for (const x0 of [-BW / 2, BW / 2]) {
      column(cx, x0, u, s, {color, width, dash, alpha, progress: ps});
      if (hl > 0 && s === hs) column(cx, x0, u, s, {color: C.accent, width: width + .4, alpha: alpha * hl, progress: ps});
    }
    if (ps >= 1 && !thin)                  // a rigid floor
      line([[cx - BW / 2 + u[s] - 3, lev(s)], [cx + BW / 2 + u[s] + 3, lev(s)]], {color: C.navy, width: 3, alpha});
    else if (ps >= 1)
      line([[cx - BW / 2 + u[s], lev(s)], [cx + BW / 2 + u[s], lev(s)]], {color, width, dash, alpha});
  }
}
function ground(x0, x1, y, progress, alpha) {
  line([[x0, y], [x1, y]], {width: 2.2, progress, alpha});
  if (progress < 1) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
  for (let x = x0 + 4; x < x1; x += 8) { ctx.moveTo(x, y); ctx.lineTo(x - 6, y + 7); }
  ctx.stroke(); ctx.restore();
}
function xdots(x, y, n, sz, alpha) {       // an italic x with n dots over it; returns its width
  const w = math('x', x, y, {size: sz, alpha});
  const cx = x + w * .5 + sz * .07, cy = y - sz * .66;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = C.ink;
  for (let k = 0; k < n; k++) { ctx.beginPath(); ctx.arc(cx + (k - (n - 1) / 2) * sz * .2, cy, sz * .05, 0, 2 * Math.PI); ctx.fill(); }
  ctx.restore();
  return w;
}
function equation(x, y, alpha) {           // M x'' + C x' + K x = 0, centred on x
  const sz = 23, parts = [['M'], [2], [' + C'], [1], [' + Kx = 0']];
  const width = p => typeof p[0] === 'number' ? math('x', 0, -1e4, {size: sz, alpha: 0}) : math(p[0], 0, -1e4, {size: sz, alpha: 0});
  let cx = x - parts.reduce((s, p) => s + width(p) + 1, 0) / 2;
  for (const p of parts) cx += (typeof p[0] === 'number' ? xdots(cx, y, p[0], sz, alpha) : math(p[0], cx, y, {size: sz, alpha})) + 1;
}

/* the matrices: entries as terms, each tied to its storey (k) or floor (m) */
const MENT = Array.from({length: N}, (_, i) => Array.from({length: N}, (_, j) => i === j ? [['m', i + 1, '']] : [['0']]));
const KENT = Array.from({length: N}, (_, i) => Array.from({length: N}, (_, j) => {
  if (i === j) return i < N - 1 ? [['k', i + 1, ''], ['k', i + 2, ' + ']] : [['k', i + 1, '']];
  if (Math.abs(i - j) === 1) return [['k', Math.max(i, j) + 1, '-']];
  return [['0']];
}));
function entry(terms, x, y, sz, hs, hl, kind, alpha) {  // centred at x; the storey's terms in accent
  const str = tm => tm[0] === '0' ? '0' : tm[2] + tm[0] + '_{' + tm[1] + '}';
  const w = terms.reduce((s, tm) => s + math(str(tm), 0, -1e4, {size: sz, alpha: 0}), 0);
  let cx = x - w / 2;
  for (const tm of terms) {
    const on = tm[0] === kind && tm[1] === hs && hl > 0;
    const ww = math(str(tm), cx, y, {size: sz, alpha});
    if (on) math(str(tm), cx, y, {size: sz, color: C.accent, alpha: alpha * hl});
    cx += ww;
  }
}
function matrix(name, lx, x0, dx, ents, kind, hs, hl, alpha, bp) {
  const y0 = 592, dy = 33, sz = 18;
  math(name + ' =', lx, y0 + 2 * dy + 6, {size: 20, align: 'right', alpha});
  // the block the highlighted storey or floor assembles into
  if (hl > 0) {
    const r = kind === 'k' ? [Math.max(0, hs - 2), hs - 1] : [hs - 1, hs - 1];
    const xa = x0 + r[0] * dx - dx / 2 + 6, xb = x0 + r[1] * dx + dx / 2 - 6;
    const ya = y0 + r[0] * dy - 22, yb = y0 + r[1] * dy + 11;
    ctx.save(); ctx.globalAlpha *= hl * alpha; ctx.fillStyle = C.wash; ctx.fillRect(xa, ya, xb - xa, yb - ya); ctx.restore();
  }
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++)
    entry(ents[i][j], x0 + j * dx, y0 + i * dy + 6, sz, hs, hl, kind, alpha);
  const left = x0 - dx / 2 + 2, right = x0 + 4 * dx + dx / 2 - 2, top = y0 - 22, bot = y0 + 4 * dy + 14;
  for (const [x, s] of [[left, 1], [right, -1]])
    line([[x + 7 * s, top], [x, top], [x, bot], [x + 7 * s, bot]], {width: 1.3, progress: bp});
}

/* ---------------------------------------------------------------- draw */
function draw() {
  const c = terms();
  const tot = disp(c, [0, 1, 2, 3, 4], 1), m1 = disp(c, [0], D.mag[0]), m2 = disp(c, [1], D.mag[1]), mh = disp(c, [2, 3, 4], D.mag[2]);
  const zero = [0, 0, 0, 0, 0, 0];
  // the storey highlight: one storey at a time, quietly
  const k_ = Math.floor((t - D.hl0) / D.hldt), hs = t < D.hl0 ? 0 : ((k_ % N) + N) % N + 1;
  const ph = (t - D.hl0 - k_ * D.hldt) / D.hldt;
  const hl = t < D.hl0 ? 0 : Math.min(1, ph / .15, (1 - ph) / .15);

  // titles and frequencies
  const tt = [lab(.08), lab(.12), lab(.16), lab(.20)];
  text('Total vibration', CX[0], 40 + rise(tt[0]), {size: 17, color: C.body, align: 'center', alpha: tt[0]});
  text('of the building', CX[0], 60 + rise(tt[0]), {size: 17, color: C.body, align: 'center', alpha: tt[0]});
  text('1st mode', CX[1], 50 + rise(tt[1]), {size: 17, color: C.body, align: 'center', alpha: tt[1]});
  text('2nd mode', CX[2], 50 + rise(tt[2]), {size: 17, color: C.body, align: 'center', alpha: tt[2]});
  text('Higher modes', CX[3], 50 + rise(tt[3]), {size: 17, color: C.body, align: 'center', alpha: tt[3]});
  const fa = [lab(.30), lab(.34), lab(.38)];
  math('f_{1} = ' + D.f[0].toFixed(2) + '\\ \\rm{Hz}', CX[1], 80 + rise(fa[0]), {size: 16, align: 'center', alpha: fa[0]});
  math('f_{2} = ' + D.f[1].toFixed(2) + '\\ \\rm{Hz}', CX[2], 80 + rise(fa[1]), {size: 16, align: 'center', alpha: fa[1]});
  math('f_{3}, f_{4}, f_{5} = ', CX[3], 80 + rise(fa[2]), {size: 16, align: 'center', alpha: fa[2]});
  math(D.f.slice(2).map(v => v.toFixed(1)).join(', ') + '\\ \\rm{Hz}', CX[3], 100 + rise(fa[2]), {size: 16, align: 'center', alpha: fa[2]});
  text('× ' + D.mag[1], CX[2], 120 + rise(fa[1]), {size: 14, color: C.muted, align: 'center', alpha: fa[1]});
  text('× ' + D.mag[2], CX[3], 120 + rise(fa[2]), {size: 14, color: C.muted, align: 'center', alpha: fa[2]});

  // ground and buildings
  ground(40, 950, GY, seg(0, .30), 1);
  const bp = [0, 1, 2, 3].map(p => seg(.05 + .05 * p, .35));
  // undeformed frame behind the total, envelopes behind the two modes
  building(CX[0], zero, {color: C.rule, width: 1, progress: bp[0], thin: true});
  for (const [p, j] of [[1, 0], [2, 1]]) {
    building(CX[p], ENV[j], {color: C.guide, width: 1, dash: [4, 3], progress: bp[p], alpha: .9, thin: true});
    building(CX[p], ENV[j].map(v => -v), {color: C.guide, width: 1, dash: [4, 3], progress: bp[p], alpha: .9, thin: true});
  }
  building(CX[3], zero, {color: C.rule, width: 1, progress: bp[3], thin: true});
  building(CX[0], tot, {progress: bp[0], hl, hs});
  building(CX[1], m1, {progress: bp[1]});
  building(CX[2], m2, {progress: bp[2]});
  building(CX[3], mh, {progress: bp[3]});
  // the lumped masses on the total building, and the labels of floors and storeys
  for (let i = 1; i <= N; i++) {
    const ms = settle(.30 + .03 * i, .28);
    if (ms <= 0) continue;
    const x = CX[0] + tot[i], y = lev(i), on = hl > 0 && hs === i;
    dot(x, y, 9.5 * (.5 + .5 * ms), {color: C.ink, fill: C.steel, width: 1.2, alpha: ms});
    if (on) dot(x, y, 9.5, {color: C.accent, fill: C.wash, width: 1.8, alpha: hl});
    math('m_{' + i + '}', CX[0] - BW / 2 - 46, y + 6, {size: 17, align: 'right', alpha: ms});
    if (on) math('m_{' + i + '}', CX[0] - BW / 2 - 46, y + 6, {size: 17, align: 'right', color: C.accent, alpha: hl});
    const ky = lev(i - 1) - SH / 2 + 6;
    math('k_{' + i + '}', CX[0] + BW / 2 + 50, ky, {size: 17, alpha: ms});
    if (on) math('k_{' + i + '}', CX[0] + BW / 2 + 50, ky, {size: 17, color: C.accent, alpha: hl});
  }
  // = and +
  const oa = lab(.35), oy = lev(2.5) + 10;
  text('=', 300, oy + rise(oa), {size: 32, align: 'center', alpha: oa});
  text('+', 508, oy + rise(oa), {size: 32, align: 'center', alpha: oa});
  text('+', 728, oy + rise(oa), {size: 32, align: 'center', alpha: oa});

  // the equation of motion, the eigenproblem, and the matrices
  const ea = lab(.50);
  equation(500, 506 + rise(ea), ea);
  const ga = lab(.58);
  const w1 = text('natural modes: ', 0, -1e4, {size: 15, alpha: 0}), w2 = math('(K - ω^{2}M)φ = 0', 0, -1e4, {size: 16, alpha: 0});
  text('natural modes: ', 500 - (w1 + w2) / 2, 534 + rise(ga), {size: 15, color: C.muted, alpha: ga});
  math('(K - ω^{2}M)φ = 0', 500 - (w1 + w2) / 2 + w1, 534 + rise(ga), {size: 16, color: C.body, alpha: ga});
  const ma = lab(.60), bpm = seg(.55, .30);
  matrix('M', 92, 130, 50, MENT, 'm', hs, hl, ma, bpm);
  matrix('K', 470, 520, 96, KENT, 'k', hs, hl, lab(.66), bpm);

  // parameters and time scale
  const pa = lab(.80);
  text(D.params, 18, H - 14, {size: 14, color: C.muted, alpha: pa});
  text(D.slowtxt, W - 18, H - 14, {size: 14, color: C.muted, align: 'right', alpha: pa});
}
boot();
"""


def main():
    R = compute()
    tp, score = poster_time(R)
    w, Phi, Q = R["w"], R["Phi"], R["Q"]
    f = w / 2 / np.pi
    gain = DEF * (62.0 / H_S)                   # units per metre: the drawing's storey is 62 units
    data = {
        "poster": tp, "t0": T0, "slow": SLOW, "hl0": HL0, "hldt": HL_DT,
        "w": w.tolist(), "f": f.tolist(), "Q": Q.tolist(), "phi": Phi.T.tolist(),
        "gain": gain, "mag": MAG,
        "params": ("floors 200, 200, 200, 200, 150 t; storeys 350, 330, 300, 260, 210 MN/m, 3.2 m high; "
                   f"impulse at the roof, C = 0; displacements × {DEF:.0f}"),
        "slowtxt": f"time slowed {SLOW:.0f} ×",
    }
    title = ("Figure 1: Lateral natural dynamic response of a building and its analysis through "
             "discretized formulation")
    aria = ("A five storey building struck at the roof vibrates freely; its total motion is drawn as the "
            "exact sum of its 1st mode, its 2nd mode and its higher modes, each vibrating at its own computed "
            "natural frequency. Below, the equation of motion with the mass and stiffness matrices, whose "
            "entries light up storey by storey.")
    common.build_html(NAME, title, aria, 1000, 790, data, JS)
    txt = check(R, tp)
    with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    print("poster score", round(score, 3))
    # the equation is set in two calls, so the italic C's box meets the x beside
    # it; their ink does not touch (README, "Nothing overlaps")
    print("still:", common.still(NAME, allow=[("C", "x")]))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.6, 0.9, 1.4, 3.0, 6.0]))


if __name__ == "__main__":
    main()
