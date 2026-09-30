"""Figure 2 of the sound document (sound-detection-and-tracking, image2).

His caption: "Figure 2. How Kalman Filter estimates the next location of the
target (system) by statistically combining next measurement point with an
estimate obtained from a model." His picture (from Babu and Parthasarathy
2021) draws three Gaussians along "System state": the "Previous estimate"
x^_{n|n-1} with its "Previous estimate uncertainty" P_{n|n-1}, the "Measured
state vector" z_n with its "Measurement uncertainty" R_n, and between them
the "Present estimate" x^_{n|n} with its "Present estimate uncertainty"
P_{n|n}; the Kalman gain K_n runs from 0 (the estimate) to 1 (the
measurement), and a small airplane is the target.

Model. A target flies along a line at 40 m/s. The filter's model is constant
velocity with white-noise acceleration (state: position and velocity,
Dt = 0.5 s, spectral density q); every Dt it measures the position with a
noise whose standard deviation changes with the sound's signal-to-noise
ratio (10, 16, 42, 16 m). Predict: x^_{n|n-1} = F x^_{n-1|n-1}, P_{n|n-1} =
F P F' + Q. Update: K_n = P_{n|n-1} H' / (H P_{n|n-1} H' + R_n), x^_{n|n} =
x^_{n|n-1} + K_n (z_n - H x^_{n|n-1}), P_{n|n} = (I - K_n H) P_{n|n-1}. The
figure draws the position part of each: its Gaussians are N(x^, P) of the
position, and its K_n is the position's gain, P_{n|n-1} / (P_{n|n-1} + R_n)
with the position's variance, which is exactly where the fused Gaussian
lands between 0 and 1.

The filter's first estimate (off by a draw of its stated uncertainty) and
the measurement noise are one draw of numpy's generator: the first seed
among 0, 1, 2, ... whose four innovations all lie between 0.6 and 1.6 of
their standard deviation (so every step shows a visible gap between the
prediction and the measurement) and whose estimates land nearer the target
than their measurements after the first step (where K_n is near 1 and the
two are nearly one); the numbers are that draw's, unaltered.

Run: python tools/numfig/snd_kalman.py [--look]
"""
import os
import sys

import numpy as np

import common
import snd_common

NAME = "snd-kalman"
HERE = os.path.dirname(os.path.abspath(__file__))

DT = 0.5                                   # s between measurements
V = 40.0                                   # m/s, the target
P0_POS = 30.0                              # m, where the target starts
Q_DENS = 58.8                              # m^2/s^3, white-noise acceleration
SIG_M = [10.0, 16.0, 42.0, 16.0]           # m, measurement noise at each step
SIG0 = [28.0, 21.0]                        # the first estimate's uncertainty (m, m/s)
F = np.array([[1.0, DT], [0.0, 1.0]])
Q = Q_DENS * np.array([[DT ** 3 / 3, DT ** 2 / 2], [DT ** 2 / 2, DT]])
H = np.array([[1.0, 0.0]])
NSTEP = len(SIG_M)


def truth():
    return P0_POS + V * DT * np.arange(NSTEP + 1)


def kalman(z, x0, P0=None):
    """The filter over measurements z; returns per step the prior, the gain
    and the posterior (full state), and the start."""
    x = np.array(x0, float)
    P = np.diag(np.square(SIG0)) if P0 is None else np.array(P0, float)
    out = {"x0": x.copy(), "P0": P.copy(), "steps": []}
    for k in range(len(z)):
        xp = F @ x
        Pp = F @ P @ F.T + Q
        S = (H @ Pp @ H.T)[0, 0] + SIG_M[k] ** 2
        K = (Pp @ H.T)[:, 0] / S
        d = z[k] - (H @ xp)[0]
        x = xp + K * d
        P = (np.eye(2) - np.outer(K, H[0])) @ Pp
        out["steps"].append(dict(xp=xp, Pp=Pp, S=S, K=K, d=d, x=x.copy(), P=P.copy(), z=z[k]))
    return out


def draw(seed):
    """The filter's first estimate (the target's start and speed, off by a draw
    of their stated uncertainty) and the four measurements, from one seed."""
    tr = truth()
    rng = np.random.default_rng(seed)
    e0 = rng.standard_normal(2) * np.array(SIG0)
    x0 = [tr[0] + e0[0], V + e0[1]]
    z = tr[1:] + rng.standard_normal(NSTEP) * np.array(SIG_M)
    return x0, z


def pick_seed():
    tr = truth()
    for seed in range(1000):
        x0, z = draw(seed)
        kf = kalman(z, x0=x0)
        ok = True
        for k, s in enumerate(kf["steps"]):
            r = abs(s["d"]) / np.sqrt(s["S"])
            nearer = abs(s["x"][0] - tr[k + 1]) < abs(z[k] - tr[k + 1])
            if not (0.6 <= r <= 1.6) or (k > 0 and not nearer):
                ok = False
                break
        if ok:
            return seed, x0, z, kf
    raise RuntimeError("no draw among 1000 seeds")


def gauss(x, m, s):
    return np.exp(-0.5 * ((x - m) / s) ** 2) / (np.sqrt(2 * np.pi) * s)


def validate(seed, x0, z, kf):
    tr = truth()
    L = []
    say = L.append
    say("Figure 2 (nf-snd-kalman): how the Kalman filter estimates the next location of the target.")
    say("Generator: tools/numfig/snd_kalman.py")
    say("")
    say("MODEL")
    say(f"  target: along a line at {V:g} m/s from {P0_POS:g} m; position measured every Dt = {DT:g} s")
    say(f"  filter: constant velocity, state (position, velocity), white-noise acceleration q = {Q_DENS:g} m^2/s^3:")
    say("    F = [[1, Dt], [0, 1]], Q = q [[Dt^3/3, Dt^2/2], [Dt^2/2, Dt]], H = [1, 0]")
    say(f"  first estimate x^_(0|0) = ({x0[0]:.3f} m, {x0[1]:.3f} m/s), standard deviations ({SIG0[0]:g} m,"
        f" {SIG0[1]:g} m/s); the target starts at {tr[0]:g} m")
    say(f"  measurement noise, standard deviation per step: {', '.join(f'{v:g}' for v in SIG_M)} m (R_n its square)")
    say(f"  the draw: numpy default_rng({seed}) gives the first estimate's error and the measurement noise;")
    say("  it is the first seed whose four innovations lie within 0.6 to 1.6 of their standard")
    say("  deviation (a visible gap at every step) and whose estimates land nearer the target than")
    say("  their measurements after the first step. Its values, unaltered:")
    for k, s in enumerate(kf["steps"]):
        say(f"    n = {k + 1}: target {tr[k + 1]:.3f} m, z_n = {z[k]:.3f} m (error {z[k] - tr[k + 1]:+.3f} m)")
    say("")
    say("THE STEPS (position part; the figure draws these numbers)")
    for k, s in enumerate(kf["steps"]):
        sp, sm, spost = np.sqrt(s["Pp"][0, 0]), SIG_M[k], np.sqrt(s["P"][0, 0])
        say(f"  n = {k + 1}: previous estimate {s['xp'][0]:8.3f} m, sd {sp:6.3f} m | measured {s['z']:8.3f} m,"
            f" sd {sm:5.2f} m")
        say(f"         K_n = {s['K'][0]:.4f} | present estimate {s['x'][0]:8.3f} m, sd {spost:6.3f} m"
            f" | target {tr[k + 1]:.3f} m, error {s['x'][0] - tr[k + 1]:+.3f} m")
    say("")
    say("CHECK 1: the present estimate is the normalised product of the two Gaussians (the")
    say("  previous estimate and the measurement), integrated on a grid of 400001 points:")
    worst = 0.0
    for k, s in enumerate(kf["steps"]):
        mp, sp, sm = s["xp"][0], np.sqrt(s["Pp"][0, 0]), SIG_M[k]
        x = np.linspace(mp - 12 * max(sp, sm), mp + 12 * max(sp, sm), 400001)
        w = gauss(x, mp, sp) * gauss(x, s["z"], sm)
        w /= np.trapezoid(w, x)
        m = np.trapezoid(x * w, x)
        v = np.trapezoid((x - m) ** 2 * w, x)
        e = max(abs(m - s["x"][0]), abs(np.sqrt(v) - np.sqrt(s["P"][0, 0])))
        worst = max(worst, e)
        say(f"    n = {k + 1}: mean {m:.6f} m, sd {np.sqrt(v):.6f} m")
    say(f"    largest difference from the filter's numbers {worst:.1e} m")
    say("  and K_n = P_{n|n-1} / (P_{n|n-1} + R_n) with the position's variance puts it there:"
        f" largest |x^_(n|n) - (x^_(n|n-1) + K_n d_n)| = "
        f"{max(abs(s['x'][0] - (s['xp'][0] + s['K'][0] * s['d'])) for s in kf['steps']):.1e} m")
    say("")
    say("CHECK 2: batch least squares. The whole trajectory x_0 ... x_n estimated at once from the")
    say("  first estimate, the process model and the measurements (information form, one linear")
    say("  solve); its last state and that state's marginal covariance against the filter:")
    worst_m, worst_c = 0.0, 0.0
    for n in range(1, NSTEP + 1):
        dim = 2 * (n + 1)
        A = np.zeros((dim, dim))
        b = np.zeros(dim)
        P0i = np.linalg.inv(kf["P0"])
        A[:2, :2] += P0i
        b[:2] += P0i @ kf["x0"]
        Qi = np.linalg.inv(Q)
        for k in range(n):
            i, j = 2 * k, 2 * (k + 1)
            G = np.zeros((2, dim))
            G[:, i:i + 2] = -F
            G[:, j:j + 2] = np.eye(2)
            A += G.T @ Qi @ G
            hz = np.zeros(dim)
            hz[j] = 1.0
            A += np.outer(hz, hz) / SIG_M[k] ** 2
            b += hz * z[k] / SIG_M[k] ** 2
        xs = np.linalg.solve(A, b)
        Cov = np.linalg.inv(A)
        s = kf["steps"][n - 1]
        worst_m = max(worst_m, np.abs(xs[-2:] - s["x"]).max())
        worst_c = max(worst_c, np.abs(Cov[-2:, -2:] - s["P"]).max())
    say(f"    largest difference in the state {worst_m:.1e}, in the covariance {worst_c:.1e}")
    say("")
    say("CHECK 3: Monte Carlo, 40000 flights drawn from the filter's own model (start around the")
    say("  first estimate with its uncertainty, random acceleration of density q, measurement noise")
    say("  R_n), filtered with the same gains: the errors' spread is the filter's P, the")
    say("  innovations' spread its S (sampling error of a standard deviation here: 0.35 %):")
    rng = np.random.default_rng(12345)
    M = 40000
    xt = np.array(x0)[None, :] + rng.standard_normal((M, 2)) * np.array(SIG0)
    Lq = np.linalg.cholesky(Q)
    x = np.tile(np.array(x0, float), (M, 1))              # the filter is linear: all flights at once
    worst = 0.0
    for k, s in enumerate(kf["steps"]):
        xt = xt @ F.T + rng.standard_normal((M, 2)) @ Lq.T
        zz = xt[:, 0] + rng.standard_normal(M) * SIG_M[k]
        xp = x @ F.T
        d = zz - xp[:, 0]
        x = xp + d[:, None] * s["K"][None, :]
        err = x[:, 0] - xt[:, 0]
        r1, r2 = err.std() / np.sqrt(s["P"][0, 0]), d.std() / np.sqrt(s["S"])
        worst = max(worst, abs(r1 - 1), abs(r2 - 1))
        say(f"    n = {k + 1}: sd of the estimate's error {err.std():.3f} m against sqrt(P_n|n) ="
            f" {np.sqrt(s['P'][0, 0]):.3f} m; sd of the innovation {d.std():.3f} m against sqrt(S) ="
            f" {np.sqrt(s['S']):.3f} m")
    say(f"    largest relative difference {worst * 100:.2f} %")
    say("  (the flight the figure draws is one such flight without random acceleration: straight")
    say(f"   at {V:g} m/s, which the model allows)")
    say("")
    say("DISPLAY")
    say(f"  one filter step (Dt = {DT:g} s) every 2.7 s of the page: the last estimate moves on with the")
    say("  model and widens (predict), the measurement arrives, the gain's pointer slides from 0 to")
    say("  K_n while the estimate moves and narrows with it (update), then the picture rests. The")
    say("  shapes between two steps are a transition; where each step lands is the filter's numbers,")
    say("  and the K_n printed is always the step's own. His names sit under their Gaussians' means,")
    say("  pushed apart only as far as they must be; the uncertainties, his words, are listed with")
    say("  their values under them. The airplane is the target, at its true position at each step.")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA, ST = D.steps, NS = ST.length;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const T0 = D.t0, TS = D.ts, PER = NS * TS + D.reset;
/* the box */
const BX = { x: 104, y: 104, w: 720, h: 292 };
const XL = D.xlim, YMAX = D.ymax;
const X = v => BX.x + (v - XL[0]) / (XL[1] - XL[0]) * BX.w;
const Yp = v => BX.y + BX.h - v / YMAX * BX.h;
const KY = BX.y + 42;                               // the gain's arrow
const COL = { prior: C.blue, meas: C.body, post: C.accent };
const FILL = { prior: C.steel, meas: C.grid, post: C.wash };
const pdf = (x, m, s) => Math.exp(-.5 * ((x - m) / s) ** 2) / (Math.sqrt(2 * Math.PI) * s);

/* ------------------------------------------------------------ the clock
   each step: predict (the last estimate moves on with the model and widens),
   measure (the measurement arrives), update (the gain slides from 0 to K_n
   and the estimate moves and narrows with it), then hold. */
const B_PRED = [0, .55], B_MEAS = [.55, .35], B_UPD = [1.0, .6];
function clock() {
  if (t < T0) return { n: 0, u: -1, rs: 0 };
  const p = (t - T0) % PER, n = Math.floor(p / TS);
  if (n >= NS) return { n: NS - 1, u: TS + 1, rs: (p - NS * TS) / D.reset };   // resetting
  return { n, u: p - n * TS, rs: 0, base: t - p + n * TS };
}
const sg = (u, b) => easeInOut(clamp((u - b[0]) / b[1]));

/* ------------------------------------------------------------ what is drawn now */
function state() {
  const c = clock(), out = [];
  const tgt = D.truth;
  let n = c.n, u = c.u;
  const rs = c.rs;
  if (c.u < 0) {                                   // before the loop: the first estimate
    return { bells: [{ k: 'post', m: D.x0, s: D.s0, a: seg(.05, .3) }], plane: tgt[0], step: 0, K: null, rs: 0, legend: null };
  }
  if (rs > 0) {                                    // the last step's picture fades, the target flies back
    const s = ST[NS - 1], f = 1 - easeInOut(clamp(rs / .5));
    return { bells: [{ k: 'prior', m: s.mp, s: s.sp, a: f }, { k: 'meas', m: s.z, s: s.sm, a: f },
                     { k: 'post', m: s.mu, s: s.su, a: f }, { k: 'post', m: D.x0, s: D.s0, a: easeInOut(clamp((rs - .45) / .5)) }],
             plane: lerp(tgt[NS], tgt[0], easeInOut(clamp(rs / .9))), step: rs < .5 ? NS : 0, K: { s, f, g: 1 }, rs, legend: { n: NS - 1, f } };
  }
  const s = ST[n], prev = n > 0 ? ST[n - 1] : null;
  const from = prev ? { m: prev.mu, s: prev.su } : { m: D.x0, s: D.s0 };
  const bells = [];
  // the previous step's prediction and measurement leave
  const out0 = 1 - easeInOut(clamp(u / .22));
  if (prev && out0 > 0) { bells.push({ k: 'prior', m: prev.mp, s: prev.sp, a: out0 }); bells.push({ k: 'meas', m: prev.z, s: prev.sm, a: out0 }); }
  // predict: the last estimate moves on and widens, and becomes the previous estimate
  const gp = settle(c.base + B_PRED[0], .45);
  const mp = lerp(from.m, s.mp, gp), spp = lerp(from.s, s.sp, gp);
  const ghost = 1 - easeInOut(clamp(u / .35));
  if (ghost > 0) bells.push({ k: 'post', m: from.m, s: from.s, a: ghost, ghost: true });
  bells.push({ k: 'prior', m: mp, s: spp, a: clamp(u / .12) });
  // measure
  const am = settle(c.base + B_MEAS[0], .3);
  if (u >= B_MEAS[0]) bells.push({ k: 'meas', m: s.z, s: s.sm, a: am, grow: am });
  // update
  const g = u >= B_UPD[0] ? settle(c.base + B_UPD[0], .5) : 0;
  if (u >= B_UPD[0]) bells.push({ k: 'post', m: lerp(s.mp, s.mu, g), s: lerp(s.sp, s.su, g), a: clamp((u - B_UPD[0]) / .12) });
  const plane = lerp(n > 0 ? D.truth[n] : D.truth[0], D.truth[n + 1], gp);
  return { bells, plane, step: n + 1, K: u >= B_UPD[0] - .2 ? { s, f: clamp((u - B_UPD[0] + .2) / .2), g } : null, rs: 0,
           legend: { n, u } };
}

/* ------------------------------------------------------------ drawing helpers */
function bell(b, fillPass) {
  const pts = [], lo = Math.max(XL[0], b.m - 5 * b.s), hi = Math.min(XL[1], b.m + 5 * b.s);
  if (hi <= lo) return;
  const N = 220;
  for (let i = 0; i <= N; i++) { const x = lo + (hi - lo) * i / N; pts.push([X(x), Yp(pdf(x, b.m, b.s) * (b.grow ?? 1))]); }
  if (fillPass) {
    ctx.save(); ctx.globalAlpha *= b.a * (b.ghost ? .5 : .75); ctx.fillStyle = FILL[b.k];
    ctx.beginPath(); ctx.moveTo(pts[0][0], BX.y + BX.h);
    for (const p of pts) ctx.lineTo(p[0], p[1]);
    ctx.lineTo(pts[pts.length - 1][0], BX.y + BX.h); ctx.closePath(); ctx.fill(); ctx.restore();
    return;
  }
  line(pts, { color: COL[b.k], width: b.k === 'post' ? 2.4 : 2.2, alpha: b.a * (b.ghost ? .45 : 1), dash: b.k === 'meas' ? [7, 4] : null });
}
/* x with a hat and a subscript: TeX's \hat{x}_{...} */
function xhat(sub, x, y, o) {
  const size = o.size || 17, w = math('x_{' + sub + '}', 0, -1e4, { size, alpha: 0 });
  const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  math('x_{' + sub + '}', x0, y, { ...o, align: 'left' });
  ctx.save(); ctx.font = font({ size, italic: true }); const wx = ctx.measureText('x').width; ctx.restore();
  const cx = x0 + wx * .56 + size * .05, a = o.alpha ?? 1;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = o.color || C.ink; ctx.lineWidth = size * .055; ctx.lineJoin = 'miter';
  ctx.beginPath(); ctx.moveTo(cx - size * .2, y - size * .56); ctx.lineTo(cx, y - size * .74); ctx.lineTo(cx + size * .2, y - size * .56);
  ctx.stroke(); ctx.restore();
  return w;
}
/* text and math in a row */
function row(parts, x, y, o = {}) {
  const wd = ([k, v]) => k === 't' ? text(v, 0, -1e4, { ...o, alpha: 0 }) : k === 'h' ? xhat(v, 0, -1e4, { ...o, alpha: 0 }) : math(v, 0, -1e4, { ...o, alpha: 0 });
  const w = parts.reduce((s, p) => s + wd(p), 0);
  let cx = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  for (const [k, v] of parts) {
    const oo = { ...o, align: 'left' };
    cx += k === 't' ? text(v, cx, y, oo) : k === 'h' ? xhat(v, cx, y, oo) : math(v, cx, y, oo);
  }
  return w;
}

/* ------------------------------------------------------------ labels under the axis
   his three names, each under its Gaussian's mean; where two would meet
   they are pushed apart the least they must (clusters merged, as a 1D
   label placement does), and kept inside the box's width */
const LAB = {
  prior: [['t', 'Previous'], ['t', 'estimate'], ['h', 'n|n-1']],
  post: [['t', 'Present'], ['t', 'estimate'], ['h', 'n|n']],
  meas: [['t', 'Measured'], ['t', 'state vector'], ['m', 'z_{n}']],
};
const LW = {};
function labW(k) {
  if (LW[k]) return LW[k];
  const ws = LAB[k].map(([kk, v]) => kk === 't' ? text(v, 0, -1e4, { size: 16, alpha: 0 }) : kk === 'h' ? xhat(v, 0, -1e4, { size: 17, alpha: 0 }) : math(v, 0, -1e4, { size: 17, alpha: 0 }));
  return (LW[k] = Math.max(...ws));
}
function place(items, lo, hi, gap) {
  items.sort((a, b) => a.x - b.x);
  let cl = items.map(it => ({ its: [it], x0: it.x - it.w / 2, w: it.w }));
  const ideal = c => { let off = 0, s = 0; for (const it of c.its) { s += it.x - it.w / 2 - off; off += it.w + gap; } return s / c.its.length; };
  let merged = true;
  while (merged) {
    merged = false;
    for (let i = 0; i < cl.length; i++) cl[i].x0 = Math.min(Math.max(ideal(cl[i]), lo), hi - cl[i].w);
    for (let i = 1; i < cl.length; i++) {
      if (cl[i].x0 < cl[i - 1].x0 + cl[i - 1].w + gap) {
        const a = cl[i - 1], b = cl[i];
        cl.splice(i - 1, 2, { its: a.its.concat(b.its), x0: 0, w: a.w + gap + b.w });
        merged = true; break;
      }
    }
  }
  for (const c of cl) { let x = c.x0; for (const it of c.its) { it.cx = x + it.w / 2; x += it.w + gap; } }
  return items;
}
function nameLabels(bells) {
  // one name per kind: the most visible bell of each kind carries it
  const best = {};
  for (const b of bells) if (!b.ghost && (!best[b.k] || b.a > best[b.k].a)) best[b.k] = b;
  const items = Object.values(best).filter(b => b.a > .02).map(b => ({ k: b.k, x: X(clamp(b.m, XL[0], XL[1])), w: labW(b.k), a: b.a }));
  place(items, BX.x - 30, BX.x + BX.w + 30, 16);
  for (const it of items) {
    const y0 = BX.y + BX.h + 50;
    LAB[it.k].forEach(([k, v], i) => {
      const o = { size: k === 't' ? 16 : 17, color: COL[it.k], align: 'center', alpha: it.a };
      const y = y0 + i * 19 + (i === 2 ? 3 : 0);
      if (k === 't') text(v, it.cx, y, o); else if (k === 'h') xhat(v, it.cx, y, o); else math(v, it.cx, y, o);
    });
    // the mean, marked on the axis
    const xm = it.x;
    line([[xm, BX.y + BX.h], [xm, BX.y + BX.h - 7]], { color: COL[it.k], width: 2, alpha: it.a });
  }
}

/* ------------------------------------------------------------ the airplane (the target) */
function plane(xc, yc, a) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(xc, yc);
  ctx.lineWidth = 1.25; ctx.strokeStyle = C.ink; ctx.fillStyle = '#fff'; ctx.lineJoin = 'round';
  const shape = pts => { ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); for (const p of pts.slice(1)) ctx.lineTo(p[0], p[1]); ctx.closePath(); ctx.fill(); ctx.stroke(); };
  shape([[1, -4], [-9, -13], [-4, -13], [9, -4]]);                       // far wing, behind
  ctx.beginPath(); ctx.moveTo(-31, -5); ctx.lineTo(19, -5);                // body, nose to the right
  ctx.bezierCurveTo(27, -5, 32, -2, 32, 0); ctx.bezierCurveTo(32, 2, 27, 4, 19, 4);
  ctx.lineTo(-22, 4); ctx.bezierCurveTo(-27, 4, -30, 0, -31, -5); ctx.closePath(); ctx.fill(); ctx.stroke();
  shape([[-31, -5], [-36, -16], [-30, -16], [-21, -5]]);                  // tail fin
  shape([[-1, 1], [-13, 15], [-7, 15], [10, 1]]);                          // near wing
  ctx.fillStyle = C.navy; ctx.beginPath(); ctx.moveTo(24, -3); ctx.lineTo(28, -3); ctx.lineTo(29.5, -1); ctx.lineTo(24, -1); ctx.closePath(); ctx.fill();
  ctx.restore();
}

/* ------------------------------------------------------------ draw */
function draw() {
  const S = state();
  const ap = seg(0, .4);
  const A = axes({ x: BX.x, y: BX.y, w: BX.w, h: BX.h, xlim: XL, ylim: [0, YMAX], xticks: D.xticks, yticks: D.yticks,
                   progress: ap, ylabel: '\\rm{Probability}', ylabelGap: 62, yfmt: v => v === 0 ? '0' : v.toFixed(2) });
  math('\\rm{System\\ state}\\ (\\rm{m})', BX.x + BX.w + 12, BX.y + BX.h + 5, { size: 17, alpha: clamp(ap * 1.4) });
  // the Gaussians: fills, then strokes
  A.inside(() => { for (const b of S.bells) bell(b, true); for (const b of S.bells) bell(b, false); });
  // the gain: from 0 at the previous estimate to 1 at the measurement
  if (S.K) {
    const { s, f, g } = S.K, x0 = X(s.mp), x1 = X(s.z), dir = Math.sign(x1 - x0) || 1;
    arrow(x0, KY, x1, KY, { width: 1.5, head: 9, both: true, alpha: f });
    text('0', x0 - dir * 10, KY + 5, { size: 16, align: dir > 0 ? 'right' : 'left', alpha: f });
    text('1', x1 + dir * 10, KY + 5, { size: 16, align: dir > 0 ? 'left' : 'right', alpha: f });
    const pk = s.K * (g ?? 1), xk = lerp(x0, x1, pk);
    const gp = { color: C.guide, width: 1, dash: [4, 4] };
    line([[x0, KY + 6], [x0, Yp(pdf(s.mp, s.mp, s.sp))]], { ...gp, alpha: f });
    line([[x1, KY + 6], [x1, Yp(pdf(s.z, s.z, s.sm))]], { ...gp, alpha: f });
    const su = lerp(s.sp, s.su, g ?? 1);
    line([[xk, KY + 6], [xk, Yp(pdf(0, 0, su))]], { color: C.accent, width: 1.2, dash: [4, 4], alpha: f });
    ctx.save(); ctx.globalAlpha *= f; ctx.fillStyle = C.accent; ctx.beginPath();
    ctx.moveTo(xk, KY + 1); ctx.lineTo(xk - 6, KY - 9); ctx.lineTo(xk + 6, KY - 9); ctx.closePath(); ctx.fill(); ctx.restore();
    // the value is K_n itself, over the place the pointer is going to
    const kx = clamp(lerp(x0, x1, s.K), BX.x + 60, BX.x + BX.w - 60);
    math(`K_{n} = ${s.K.toFixed(2)}`, kx, KY - 15, { size: 17, align: 'center', alpha: f });
  }
  // his names under the axis
  nameLabels(S.bells);
  // the target, flying above
  const pa = seg(.1, .3), px = X(S.plane);
  plane(px, 64, pa);
  text('target', px - 42, 68, { size: 15, color: C.muted, align: 'right', alpha: pa });
  math(`n = ${S.step}`, BX.x + BX.w, 36, { size: 17, align: 'right', alpha: seg(.2, .3) });
  legend(S);
  math(D.params, 22, H - 14, { size: 14, color: C.muted, alpha: seg(.5, .3) });
}

/* ------------------------------------------------------------ the uncertainties, his words, with values */
function legend(S) {
  const y = BX.y + BX.h + 150, cols = [BX.x - 40, BX.x + 238, BX.x + 486];
  const L = S.legend;
  let vals = null;
  if (L) {
    const s = ST[L.n];
    const upd = L.u === undefined ? 1 : L.u >= B_UPD[0] ? 1 : 0, mea = L.u === undefined ? 1 : L.u >= B_MEAS[0] ? 1 : 0;
    const f = L.f ?? 1;
    vals = [{ v: s.sp, a: f }, { v: s.su, a: f * upd }, { v: s.sm, a: f * mea }];
  }
  const ent = [['prior', 'Previous estimate uncertainty', 'P_{n|n-1}'], ['post', 'Present estimate uncertainty', 'P_{n|n}'],
               ['meas', 'Measurement uncertainty', 'R_{n}']];
  const la = seg(.3, .3);
  ent.forEach(([k, words, sym], i) => {
    const x = cols[i];
    line([[x, y - 5], [x + 26, y - 5]], { color: COL[k], width: k === 'post' ? 2.4 : 2.2, dash: k === 'meas' ? [7, 4] : null, alpha: la });
    text(words, x + 34, y, { size: 15, color: C.body, alpha: la });
    const v = vals ? vals[i] : null;
    const tail = v && v.a > 0 ? ` = (${v.v.toFixed(1)}\\,\\rm{m})^{2}` : '';
    math(sym + tail, x + 34, y + 21, { size: 16, alpha: la });
  });
}
boot();
"""


def page_data(seed, z, kf):
    tr = truth()
    steps = []
    for k, s in enumerate(kf["steps"]):
        steps.append({"mp": s["xp"][0], "sp": np.sqrt(s["Pp"][0, 0]), "z": s["z"], "sm": SIG_M[k],
                      "K": s["K"][0], "mu": s["x"][0], "su": np.sqrt(s["P"][0, 0])})
    peak = 1 / (np.sqrt(2 * np.pi) * min(st["su"] for st in steps))          # the sharpest estimate
    ymax = float(np.ceil(peak * 1.36 / 0.02) * 0.02)
    return {
        "steps": steps, "x0": kf["x0"][0], "s0": SIG0[0], "truth": tr, "t0": 0.25, "ts": 2.7, "reset": 1.0,
        "xlim": [-20.0, 160.0], "xticks": [0, 50, 100, 150], "ymax": ymax,
        "yticks": [round(v, 2) for v in np.arange(0, ymax + 1e-9, 0.02)],
        "poster": 0.25 + 1 * 2.7 + 2.2,
        "params": (r"\rm{target at %g m/s; constant velocity model, }\Delta t = %g\,\rm{s},\ q = %g\,\rm{m}^{2}\rm{/s}^{3}\rm{;"
                   r"\ \ }K_{n} = P_{n|n-1}/(P_{n|n-1} + R_{n})\rm{, position part}"
                   % (V, DT, Q_DENS)),
    }


def main():
    seed, x0, z, kf = pick_seed()
    txt = validate(seed, x0, z, kf)
    with open(os.path.join(HERE, "snd_kalman.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    data = page_data(seed, z, kf)
    title = ("Figure 2: How Kalman Filter estimates the next location of the target (system) by statistically "
             "combining next measurement point with an estimate obtained from a model")
    aria = ("A Kalman filter tracking a flying target along a line. At each step the previous estimate moves on "
            "with the model and widens, a measurement arrives, and the two Gaussians combine into the present "
            "estimate, narrower than either, placed between them by the Kalman gain K between 0 and 1.")
    common.build_html(NAME, title, aria, 1000, 616, data, JS)
    print("still:", common.still(NAME))
    snd_common.append(os.path.join(HERE, "snd_kalman.check.txt"), snd_common.loop_overlaps(NAME, data["t0"] + len(data["steps"]) * data["ts"] + data["reset"] + 0.4))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.4, 0.8, 1.2, 1.6, 2.4, 3.3, 4.2, 6.5, 9.0, 11.5]))


if __name__ == "__main__":
    main()
