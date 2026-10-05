"""The brochure's building with sensors (brochure-shm-and-ndt-2-pages, image5,
uncaptioned): "Example of a building's dynamic response", the title of his
animation, which was Figure 1 of the SHM article (image2) until the article's
Figure 1 became the waves guide's (nf-building, his notes of 5 Oct 2026); the
page keeps that title (tests/test_shm_figures.py names it).

His drawing: the vibration of a structure, measured by sensors along its
height, equals its 1st vibration mode (shape and frequency) plus its 2nd
plus higher modes. His animation (archived in content/anim-originals/
fig1-building-sensors.html) used Euler-Bernoulli cantilever shapes with the
frequencies of a shear beam (1 : 3 : 5), which no single structure has.

Here the building is the continuum model of Miranda and Taghavi (2005): a
flexural cantilever (its walls, EI) coupled with a shear cantilever (its
frames, GA), fixed at the ground, of height H and mass m per metre,

    EI u'''' - GA u'' + m u.. = p(x, t),    alpha = H sqrt(GA / EI),

solved by finite elements (Hermite cubics; GA enters as the shear
stiffness integral of u'v'), and checked against the closed form
characteristic equation and the Euler-Bernoulli limit. A half sine pulse at
the roof sets it vibrating; with no damping the response is exactly
    u(x, t) = sum_j phi_j(x) q_j(t),  q_j'' + w_j^2 q_j = phi_j(H) P(t),
each q_j in closed form, drawn as the total (with his five sensors on it),
as the 1st mode, as the 2nd mode, and the rest as "higher modes".

Run: python tools/numfig/shm_sensors.py [--look]   (writes content/anim/
nf-shm-sensors.html and .webp and tools/numfig/shm_sensors.check.txt)
"""
import os
import sys

import numpy as np
import scipy.linalg as sla
from scipy.optimize import brentq

import common

NAME = "shm-sensors"
HERE = os.path.dirname(os.path.abspath(__file__))

H_M = 80.0                 # m, height (about 24 storeys)
MASS = 150e3               # kg per m of height (a 25 x 25 m plan, 0.8 t/m2 a floor, 3.33 m storeys)
ALPHA = 6.0                # walls and frames together
T1 = 2.4                   # s, fundamental period (about 0.1 s a storey)
NE = 40                    # elements on the page's model
NMODE = 6                  # modes on the page (the rest: see the check)
TD = 0.3                   # s, the roof pulse, a half sine
ROOF1 = 0.020              # m, the 1st mode's roof amplitude after the pulse
DEF = 400.0                # displacements drawn x DEF
MAG2 = 3                   # the 2nd mode's panel drawn x MAG2 more (stated)
T0 = 0.5                   # s, the pulse starts (page clock)
SENSORS = [0.95, 0.73, 0.5, 0.27, 0.05]   # heights, x / H (his five)


def fe(alpha, ne, H=1.0, EI=1.0, m=1.0):
    """Stiffness and consistent mass of the fixed base cantilever, dofs
    (u, u') at nodes 1..ne (node 0 fixed)."""
    L = H / ne
    GA = alpha ** 2 * EI / H ** 2
    kb = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                 [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
    ks = GA / (30 * L) * np.array([[36, 3 * L, -36, 3 * L], [3 * L, 4 * L * L, -3 * L, -L * L],
                                   [-36, -3 * L, 36, -3 * L], [3 * L, -L * L, -3 * L, 4 * L * L]])
    mm = m * L / 420 * np.array([[156, 22 * L, 54, -13 * L], [22 * L, 4 * L * L, 13 * L, -3 * L * L],
                                 [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L * L, -22 * L, 4 * L * L]])
    n = 2 * (ne + 1)
    K, M = np.zeros((n, n)), np.zeros((n, n))
    for e in range(ne):
        i = 2 * e
        K[i:i + 4, i:i + 4] += kb + ks
        M[i:i + 4, i:i + 4] += mm
    return K[2:, 2:], M[2:, 2:]


def modes(alpha, ne, **kw):
    K, M = fe(alpha, ne, **kw)
    w2, V = sla.eigh(K, M)                    # mass normalised
    V = V * np.sign(V[-2])                    # roof displacement positive
    return np.sqrt(w2), V, K, M


def char(g, a):
    """Miranda and Taghavi (2005), eq. 6: the eigenvalue equation of the
    coupled cantilever, beta^2 = alpha^2 + gamma^2."""
    b = np.sqrt(a * a + g * g)
    return 2 + (2 + a ** 4 / (g * g * b * b)) * np.cos(g) * np.cosh(b) + a * a / (g * b) * np.sin(g) * np.sinh(b)


def closed(a, n):
    """The first n roots gamma_i and w_i sqrt(m H^4 / EI) = gamma_i sqrt(gamma_i^2 + alpha^2)."""
    gs = np.linspace(1e-3, 40, 400001)
    v = char(gs, a)
    out = []
    for i in np.where(np.sign(v[:-1]) != np.sign(v[1:]))[0]:
        out.append(brentq(char, gs[i], gs[i + 1], args=(a,), xtol=1e-14))
        if len(out) == n:
            break
    g = np.array(out)
    return g, g * np.sqrt(g * g + a * a)


def pulse_unit(w, Om, td):
    """The undamped unit-mass response to sin(Om t) on [0, td]: its closed
    form while the pulse acts, and (a, b) of a cos wt + b sin wt after it."""
    x = lambda t: (np.sin(Om * t) - Om / w * np.sin(w * t)) / (w * w - Om * Om)
    v = lambda t: (Om * np.cos(Om * t) - Om * np.cos(w * t)) / (w * w - Om * Om)
    xd, vd = x(td), v(td)
    a = xd * np.cos(w * td) - vd / w * np.sin(w * td)
    b = xd * np.sin(w * td) + vd / w * np.cos(w * td)
    return x, a, b


def compute():
    lam, _, _, _ = modes(ALPHA, 160)
    w1 = 2 * np.pi / T1
    EI = MASS * H_M ** 4 * (w1 / lam[0]) ** 2     # the flexural rigidity that makes T1
    GA = ALPHA ** 2 * EI / H_M ** 2
    w, V, K, M = modes(ALPHA, NE, H=H_M, EI=EI, m=MASS)
    nd = NE + 1
    xs = np.linspace(0, 1, nd)
    phi = np.vstack([np.zeros((1, V.shape[1])), V[0::2]])     # displacements at nodes 0..NE
    top = phi[-1]
    Om = np.pi / TD
    # q_j(t) = phi_j(H) P0 x_j(t); the roof's share of mode j: phi_j(H)^2 P0 x_j
    ab = np.array([pulse_unit(wj, Om, TD)[1:] for wj in w])
    amp_unit = np.hypot(ab[:, 0], ab[:, 1]) * top ** 2
    P0 = ROOF1 / amp_unit[0]
    g = P0 * top ** 2                                           # m per unit x_j, at the roof
    R = dict(EI=EI, GA=GA, w=w, V=V, K=K, M=M, phi=phi, top=top, xs=xs, P0=P0, g=g, ab=ab,
             amp=g * np.hypot(ab[:, 0], ab[:, 1]), Om=Om)

    # ---- checks
    # mesh convergence of f1..f4 (the page's model is NE elements)
    R["conv"] = [(ne, modes(ALPHA, ne)[0][:4]) for ne in (5, 10, 20, 40, 80, 160)]
    _, lc = closed(ALPHA, 5)
    R["closed"] = lc
    R["fe160"] = modes(ALPHA, 160)[0][:5]
    # Euler-Bernoulli limit (alpha = 0): beta_n H = 1.8751, 4.6941, 7.8548
    beb = np.array([1.875104068711961, 4.694091132974175, 7.854757438237613])
    R["eb"] = (np.sqrt(modes(0.0, 160)[0][:3]), beb)
    # shear limit: alpha large, gamma_n -> (2n - 1) pi / 2
    gbig, _ = closed(200.0, 3)
    R["shear"] = (gbig, (2 * np.arange(1, 4) - 1) * np.pi / 2)
    # orthogonality and the eigen residual on the page's model
    R["orth"] = np.abs(V.T @ M @ V - np.eye(V.shape[1])).max()
    R["res"] = max(np.linalg.norm(K @ V[:, j] - w[j] ** 2 * M @ V[:, j]) / np.linalg.norm(K @ V[:, j])
                   for j in range(6))
    # the modal response against a direct integration of M u.. + K u = e_roof P(t)
    n = K.shape[0]
    e = np.zeros(n); e[-2] = 1.0
    A = np.block([[np.zeros((n, n)), np.eye(n)], [-np.linalg.solve(M, K), np.zeros((n, n))]])
    Bv = np.concatenate([np.zeros(n), np.linalg.solve(M, e)])
    dt = TD / 400
    Ed = sla.expm(A * dt)
    # exact zero order hold is too coarse for a sine; integrate the forcing with Simpson on each step
    Ah = sla.expm(A * dt / 2)
    z = np.zeros(2 * n)
    tt = np.arange(0, 6.0 + 1e-9, dt)
    Pf = lambda t: P0 * np.where((t >= 0) & (t <= TD), np.sin(Om * np.clip(t, 0, TD)), 0.0)
    roof_ex = np.zeros(tt.size)
    for i in range(1, tt.size):
        t0_ = tt[i - 1]
        z = Ed @ z + dt / 6 * (Ed @ Bv * Pf(t0_) + 4 * Ah @ Bv * Pf(t0_ + dt / 2) + Bv * Pf(t0_ + dt))
        roof_ex[i] = z[n - 2]
    roof_mod = np.array([roof(R, t, NMODE) for t in tt])
    roof_all = np.array([roof(R, t, len(w)) for t in tt])
    R["direct"] = np.abs(roof_all - roof_ex).max() / np.abs(roof_ex).max()
    R["trunc"] = np.abs(roof_mod - roof_all).max() / np.abs(roof_all).max()
    return R


def qj(R, j, t):
    """The roof's share of mode j at time t after the pulse starts (m)."""
    w, Om, g = R["w"][j], R["Om"], R["g"][j]
    if t <= 0:
        return 0.0
    if t <= TD:
        return g * (np.sin(Om * t) - Om / w * np.sin(w * t)) / (w * w - Om * Om)
    a, b = R["ab"][j]
    return g * (a * np.cos(w * t) + b * np.sin(w * t))


def roof(R, t, nm):
    return sum(qj(R, j, t) for j in range(nm))


def poster_time(R):
    """After the intro, a moment when the 1st and 2nd modes are both near an
    extreme with opposite signs at the roof: every panel clearly deformed,
    the total visibly not the 1st mode alone."""
    best, tb = -1, None
    for t in np.linspace(3.0, 12.0, 9001):
        s = t - T0
        r1, r2 = qj(R, 0, s) / R["amp"][0], qj(R, 1, s) / R["amp"][1]
        sc = min(abs(r1), abs(r2)) - (0.5 if r1 * r2 > 0 else 0)
        if sc > best:
            best, tb = sc, t
    return float(round(tb, 3)), best


def check(R, tp, score):
    L = []
    p = L.append
    w = R["w"]
    f = w / 2 / np.pi
    p("Figure 1 (nf-shm-sensors): a building's dynamic response, the sum of its modes")
    p("generator: tools/numfig/shm_sensors.py")
    p("")
    p("MODEL: the continuum building of Miranda and Taghavi (2005), J. Struct. Eng. 131(2):")
    p("  a flexural cantilever (walls, EI) and a shear cantilever (frames, GA) acting together,")
    p("  EI u'''' - GA u'' + m u.. = p(x, t), fixed at the ground (u = u' = 0), free at the roof")
    p(f"  H = {H_M:g} m, m = {MASS/1e3:g} t/m, alpha = H sqrt(GA/EI) = {ALPHA:g}")
    p(f"  EI = {R['EI']:.4e} N m^2, GA = {R['GA']:.4e} N (EI chosen so that T1 = {T1} s)")
    p(f"  finite elements: {NE} Hermite cubics (u, u' at each node), consistent mass; GA enters as")
    p("  the integral of GA u' v' (the tension-string matrix)")
    p("")
    p("MODES (the page's model)")
    for j in range(5):
        p(f"  mode {j+1}: f = {f[j]:8.4f} Hz, T = {1/f[j]:.4f} s, T1/T = {w[j]/w[0]:.4f}")
    xs, phi = R["xs"], R["phi"]
    for j in (1, 2):
        s = phi[:, j] / phi[-1, j]
        zc = [xs[i] - s[i] * (xs[i + 1] - xs[i]) / (s[i + 1] - s[i]) for i in range(len(s) - 1) if s[i] * s[i + 1] < 0]
        p(f"  mode {j+1} nodes at x/H = " + ", ".join(f"{v:.4f}" for v in zc))
    p(f"  eigen residual max |K phi - w^2 M phi| / |K phi| = {R['res']:.1e};"
      f" max |Phi^T M Phi - I| = {R['orth']:.1e}")
    p("")
    p("CHECK 1: against the closed form (Miranda and Taghavi 2005, eq. 6):")
    p("  2 + [2 + a^4/(g^2 b^2)] cos g cosh b + [a^2/(g b)] sin g sinh b = 0, b^2 = a^2 + g^2,")
    p("  w sqrt(m H^4/EI) = g sqrt(g^2 + a^2), roots by bisection (brentq, 1e-14)")
    lc = R["closed"]
    p("  dimensionless w_n, closed form: " + ", ".join(f"{v:.8f}" for v in lc))
    for ne, lam in R["conv"]:
        p(f"    FE {ne:3d} elements: " + ", ".join(f"{v:.8f} ({v/lc[k]-1:+.1e})" for k, v in enumerate(lam)))
    p("  (the error falls 16 x per halving: the Hermite element's h^4 convergence of eigenvalues)")
    p("CHECK 2: the same FE code at alpha = 0 against Euler-Bernoulli cantilever roots beta_n H:")
    bf, be = R["eb"]
    p("  " + ", ".join(f"{a:.8f} vs {b:.8f} ({a/b-1:+.1e})" for a, b in zip(bf, be)))
    p("CHECK 3: the closed form at alpha = 200 against the shear beam, gamma_n -> (2n - 1) pi/2:")
    gb, gs = R["shear"]
    p("  " + ", ".join(f"{a:.5f} vs {b:.5f} ({a/b-1:+.1e})" for a, b in zip(gb, gs)))
    p("")
    p("THE MOTION")
    p(f"  a half sine pulse P(t) = P0 sin(pi t / {TD}) at the roof for {TD} s, then free, undamped;")
    p(f"  P0 = {R['P0']/1e3:.1f} kN makes the 1st mode's roof amplitude {ROOF1*1e3:.0f} mm")
    p("  q_j(t) = phi_j(H) P0 x_j(t), x_j'' + w_j^2 x_j = sin(pi t/td) on [0, td], closed form:")
    p("  (sin(W t) - (W/w) sin(w t)) / (w^2 - W^2) while it acts, a cos wt + b sin wt after")
    amp = R["amp"]
    p("  roof amplitude of each mode after the pulse (mm): " + ", ".join(f"{v*1e3:.3f}" for v in amp[:6]))
    p("  relative to the 1st: " + ", ".join(f"{v/amp[0]:.4f}" for v in amp[:6]))
    p(f"  CHECK 4: the roof displacement from all {len(R['w'])} modes against a direct integration of")
    p(f"    M u.. + K u = e_roof P(t) (exact matrix exponential, Simpson on the load, dt = {TD/400*1e3:.2f} ms),")
    p(f"    0 to 6 s: max difference / max |u| = {R['direct']:.1e}")
    p(f"  the page keeps {NMODE} modes: max difference in the roof displacement against all modes over 6 s,"
      f" {R['trunc']:.1e} of its maximum")
    p("")
    p("THE PAGE")
    p(f"  real time (no slowing): f1 = {f[0]:.3f} Hz on screen; the pulse at t = {T0} s of the page's clock")
    p(f"  building drawn 320 units high (4 units per m); displacements x {DEF:g} (the 1st mode's roof swings")
    p(f"  {ROOF1*DEF*4:.0f} units); the 2nd mode's panel x {MAG2} more (stated), its envelope"
      f" {amp[1]*DEF*4*MAG2:.1f} units at the roof")
    p("  the dashed outlines of each mode are its two extreme positions, +- its amplitude after the pulse")
    p(f"  sensors at x/H = " + ", ".join(f"{v:g}" for v in SENSORS) + " (his five), on the total")
    p(f"  poster (printed frame) at t = {tp} s (both modes within {1-score:.2f} of an extreme, opposite signs"
      " at the roof)")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);

/* ---------------------------------------------------------------- layout */
const GY = 446, HB = 320, BW = 110, TOP = GY - HB;       // ground, height, width, roof
const CX = [158, 452, 744];                               // total, 1st mode, 2nd mode
const NX = D.xs.length, NM = D.w.length;
const lev = x => GY - HB * x;
const G = D.gain;                                         // drawing units per metre of displacement

/* ---------------------------------------------------------------- the motion
   q_j(tau), tau = t - T0 seconds after the pulse starts: the roof's share of
   mode j, exact (closed form), m */
function q(j, tau) {
  if (tau <= 0) return 0;
  const w = D.w[j], Om = D.Om;
  if (tau <= D.td) return D.g[j] * (Math.sin(Om * tau) - Om / w * Math.sin(w * tau)) / (w * w - Om * Om);
  return D.A[j] * Math.cos(w * tau) + D.B[j] * Math.sin(w * tau);
}
function shape(js, qs, mag) {                             // lateral displacement at each node, units
  const u = new Float64Array(NX);
  for (const j of js) for (let i = 0; i < NX; i++) u[i] += D.psi[j][i] * qs[j] * G * mag;
  return u;
}
const at = (u, x) => { const p = x * (NX - 1), i = Math.min(NX - 2, Math.floor(p)); return lerp(u[i], u[i + 1], p - i); };

/* ---------------------------------------------------------------- drawing */
function building(cx, u, o = {}) {
  const { color = C.blue, width = 2, dash = null, alpha = 1, progress = 1, roof = C.navy } = o;
  if (progress <= 0) return;
  for (const s of [-1, 1]) {                              // the walls rise from the ground, then the roof
    const pts = []; for (let i = 0; i < NX; i++) pts.push([cx + s * BW / 2 + u[i], lev(i / (NX - 1))]);
    line(pts, { color, width, dash, alpha, progress: clamp(progress / .8) });
  }
  const rp = clamp((progress - .8) / .2);
  if (rp > 0) line([[cx - BW / 2 + u[NX - 1], TOP], [cx + BW / 2 + u[NX - 1], TOP]], { color: roof, width: roof === color ? width : 2.6, dash, alpha, progress: rp });
}
function ground(x0, x1, y, progress) {
  line([[x0, y], [x1, y]], { width: 2.2, progress });
  if (progress < 1) return;
  ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
  for (let x = x0 + 4; x < x1; x += 8) { ctx.moveTo(x, y); ctx.lineTo(x - 6, y + 7); }
  ctx.stroke(); ctx.restore();
}
function ordinal(n, suf, rest, x, y, a) {                 // "1st vibration mode", the suffix raised
  const w = math(n + '^{\\rm{' + suf + '}}\\rm{ ' + rest + '}', 0, -1e4, { size: TS, alpha: 0 });
  math(n + '^{\\rm{' + suf + '}}\\rm{ ' + rest + '}', x - w / 2, y, { size: TS, alpha: a });
}
const TS = 24;                                            // his words: at his picture's own relative size

function draw() {
  const tau = t - D.t0, qs = D.w.map((_, j) => q(j, tau));
  const all = Array.from({ length: NM }, (_, j) => j);
  const tot = shape(all, qs, 1), m1 = shape([0], qs, 1), m2 = shape([1], qs, D.mag2);
  const zero = new Float64Array(NX);
  const env1 = D.psi[0].map(v => v * D.amp[0] * G), env2 = D.psi[1].map(v => v * D.amp[1] * G * D.mag2);

  // titles: his words
  const tt = [lab(.06), lab(.10), lab(.14), lab(.18)];
  text('Vibration of', CX[0], 34 + rise(tt[0]), { size: TS, align: 'center', alpha: tt[0] });
  text('structure', CX[0], 61 + rise(tt[0]), { size: TS, align: 'center', alpha: tt[0] });
  ordinal('1', 'st', 'vibration mode', CX[1], 34 + rise(tt[1]), tt[1]);
  text('shape and frequency', CX[1], 61 + rise(tt[1]), { size: TS, align: 'center', alpha: tt[1] });
  ordinal('2', 'nd', 'vibration mode', CX[2], 34 + rise(tt[2]), tt[2]);
  text('shape and frequency', CX[2], 61 + rise(tt[2]), { size: TS, align: 'center', alpha: tt[2] });
  const fa = [lab(.30), lab(.34)];
  math('f_{1} = ' + D.f[0].toFixed(2) + '\\,\\rm{Hz}', CX[1], 87 + rise(fa[0]), { size: 20, align: 'center', alpha: fa[0] });
  math('f_{2} = ' + D.f[1].toFixed(2) + '\\,\\rm{Hz}', CX[2], 87 + rise(fa[1]), { size: 20, align: 'center', alpha: fa[1] });
  math('\\times\\ ' + D.mag2, CX[2] + 44, TOP - 7 + rise(fa[1]), { size: 16, color: C.muted, alpha: fa[1] });

  // ground and buildings
  ground(46, 890, GY, seg(0, .30));
  const bp = [0, 1, 2].map(p => seg(.05 + .05 * p, .35));
  building(CX[0], zero, { color: C.rule, width: 1, progress: bp[0], roof: C.rule });
  for (const [p, env] of [[1, env1], [2, env2]]) {
    building(CX[p], env, { color: C.guide, width: 1, dash: [5, 4], progress: bp[p], alpha: .9, roof: C.guide });
    building(CX[p], env.map(v => -v), { color: C.guide, width: 1, dash: [5, 4], progress: bp[p], alpha: .9, roof: C.guide });
  }
  building(CX[0], tot, { progress: bp[0] });
  building(CX[1], m1, { progress: bp[1] });
  building(CX[2], m2, { progress: bp[2] });

  // the push at the roof that sets it vibrating
  if (tau > 0 && tau < D.td) {
    const s = Math.sin(D.Om * tau), xr = CX[0] - BW / 2 + tot[NX - 1] - 5;
    arrow(xr - 20 - 38 * s, TOP + 7, xr, TOP + 7, { color: C.accent, width: 2, head: 10, alpha: clamp(s * 3) });
  }

  // = and +, and the rest
  const oa = lab(.35), oy = lev(.5) + 10;
  text('=', 305, oy + rise(oa), { size: 32, align: 'center', alpha: oa });
  text('+', 598, oy + rise(oa), { size: 32, align: 'center', alpha: oa });
  text('+', 886, oy + rise(oa), { size: 32, align: 'center', alpha: oa });
  text('Higher', 946, oy - 30 + rise(tt[3]), { size: TS, align: 'center', alpha: tt[3] });
  text('modes', 946, oy - 3 + rise(tt[3]), { size: TS, align: 'center', alpha: tt[3] });
  text('…', 946, oy + 22 + rise(tt[3]), { size: TS, color: C.body, align: 'center', alpha: tt[3] });

  // swinging, back and forth
  const da = lab(.40);
  for (const p of [1, 2]) arrow(CX[p] - 22, TOP - 11, CX[p] + 22, TOP - 11, { width: 1.2, head: 7, both: true, alpha: da });

  // the sensors ride on the structure, and so does what he calls them
  const la = lab(.45), lx = CX[0] - 22 + at(tot, .5), ly = lev(.5);
  text('Sensors', lx, ly, { size: 20, align: 'center', base: 'middle', rot: -Math.PI / 2, alpha: la });
  D.sensors.forEach((xh, i) => {
    const ms = settle(.30 + .03 * i, .28);
    if (ms <= 0) return;
    const sx = CX[0] + 18 + at(tot, xh), sy = Math.min(lev(xh), GY - 8);
    const sz = 12 * (.6 + .4 * ms);
    ctx.save(); ctx.globalAlpha *= ms; ctx.fillStyle = C.navy; ctx.fillRect(sx - sz / 2, sy - sz / 2, sz, sz); ctx.restore();
    if (la > 0) {
      const ty = ly + (sy - ly) * .55;
      arrow(lx + 13, ty, sx - 9, sy, { width: 1.1, head: 7, alpha: la });
    }
  });

  const pa = lab(.8);
  let x = 18;
  x += text('building ' + D.H + ' m tall, walls and frames (continuum, ', x, H - 13, { size: 16, color: C.muted, alpha: pa });
  x += math('\\alpha\\ = ' + D.alpha, x, H - 13, { size: 16, color: C.muted, alpha: pa });
  text('); a 0.3 s push at the roof, then free, undamped; displacements × ' + D.def + '; real time', x, H - 13, { size: 16, color: C.muted, alpha: pa });
}
boot();
"""


def main():
    R = compute()
    tp, score = poster_time(R)
    w = R["w"]
    f = w / 2 / np.pi
    nm = NMODE
    psi = (R["phi"] / R["top"])[:, :nm].T                       # shapes, roof = 1
    gain = DEF * 4.0                                            # units per metre: 4 units per m of height
    data = {
        "poster": tp, "t0": T0, "td": TD, "Om": R["Om"],
        "w": w[:nm].tolist(), "f": f[:nm].tolist(),
        "g": R["g"][:nm].tolist(), "A": (R["g"][:nm] * R["ab"][:nm, 0]).tolist(),
        "B": (R["g"][:nm] * R["ab"][:nm, 1]).tolist(), "amp": R["amp"][:nm].tolist(),
        "xs": R["xs"].tolist(), "psi": psi.tolist(), "gain": gain, "mag2": MAG2,
        "sensors": SENSORS, "H": int(H_M), "alpha": int(ALPHA), "def": int(DEF),
    }
    title = "Figure 1: Example of a building's dynamic response"
    aria = ("A building with five sensors along its height vibrates after a short push at its roof. Its computed "
            "motion equals its 1st vibration mode plus its 2nd vibration mode plus higher modes, each "
            "swinging at its own natural frequency, drawn side by side in real time.")
    common.build_html(NAME, title, aria, 1000, 500, data, JS)
    txt = check(R, tp, score)
    with open(os.path.join(HERE, "shm_sensors.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    print("still:", common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.0, 3.2, 5.0]))


if __name__ == "__main__":
    main()
