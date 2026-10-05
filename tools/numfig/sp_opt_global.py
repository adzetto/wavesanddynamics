"""Figure 9 of the signal processing document: global optimization algorithms.

The professor asked (5 Oct 2026) for the global methods his Optimization
section names to be shown working: "Add visualizations for particle swarm,
genetic algo, and such (the algos mentioned there) simulated annealing, ant
colony opt."

Model. One objective for all four, a shallow bowl with seven Gaussian wells
on the square -4 <= x_1, x_2 <= 4,

    f(x) = 0.04 |x|^2 - sum_i a_i exp(-|x - c_i|^2 / (2 s_i^2)),

with seven minima: the global one near (2.13, -1.74) and six local ones. Its
minima are found independently of the algorithms: a dense grid (1601 x 1601),
every grid point lower than its eight neighbours refined by Newton's method
with the exact gradient and Hessian, and the global one checked against
scipy's differential evolution and SHGO.

Four algorithms, each given the same budget of 400 evaluations of f:
  (a) a real-coded genetic algorithm: 20 per generation, binary tournament
      selection, BLX-0.5 crossover, Gaussian mutation, two elites kept;
  (b) particle swarm optimization (Clerc and Kennedy's constriction
      coefficients, w = 0.7298, c1 = c2 = 1.49618), 20 particles, global best;
  (c) simulated annealing: one walker, Gaussian steps of 1.0, Metropolis
      acceptance, geometric cooling from T = 2 to T = 0.002;
  (d) continuous ant colony optimization, ACO_R (Socha and Dorigo 2008,
      European Journal of Operational Research 185:1155-1173): an archive of
      the 20 best solutions ranked by f, rank weights
      w_l = exp(-(l - 1)^2 / (2 q^2 k^2)) / (q k sqrt(2 pi)), Gaussian kernels
      sigma_l = xi sum_e |s_e - s_l| / (k - 1), two ants per iteration.
GA, PSO and ACO_R start from the same 20 random points; SA starts at the first
of them. Every run is seeded (numpy SeedSequence, one stream each), and the
page draws what the runs recorded: every point evaluated, the populations,
parents, personal and swarm bests, the walker's moves, and the archive.

Run: python tools/numfig/sp_opt_global.py  (writes the page, the still and the
check file; prints the key numbers). Needs Playwright's Chromium for the
still and the page checks.
"""
import base64
import os

import numpy as np

import common
import sp_model as SM

NAME = "sp-opt-global"
LO, HI = -4.0, 4.0
BOWL = 0.04
WELLS = [  # centre x, centre y, depth a, width s
    (2.2, -1.8, 2.1, 0.95),
    (-1.4, 1.1, 1.1, 0.8),
    (-2.7, -2.5, 1.0, 0.65),
    (2.5, 2.4, 0.95, 0.7),
    (0.3, -2.9, 0.7, 0.45),
    (-3.0, 3.0, 0.75, 0.55),
    (0.5, 0.7, 0.5, 0.4),
]
NE = 400            # the budget: evaluations of f, the same for all four
NPOP = 20           # GA population, PSO swarm, ACO_R archive, and the shared start
SEED = 15
GA_P = dict(pc=0.9, alpha=0.5, pm=0.25, sm=0.6, elite=2)
PSO_P = dict(w=0.7298, c1=1.49618, c2=1.49618, v0=0.1)
SA_P = dict(T0=2.0, T1=2e-3, step=1.0)
ACO_P = dict(m=2, q=0.5, xi=0.85)
LEVELS = [-1.7, -1.5, -1.3, -1.1, -0.9, -0.7, -0.5, -0.3, -0.1, 0.1, 0.4, 0.7, 1.0]
H_PAGE = 760
T0_RUN = 0.6        # the page's clock (JS clock()): the run starts here
NS_SLOTS = NE // NPOP


def t_of(u):
    """The moment (s, first loop) at which the page's clock reads u: slots of
    20 evaluations, 1 s each for the first five, 0.5 s from the tenth on."""
    dur = []
    for k in range(NS_SLOTS):
        x = min(1.0, max(0.0, (k - 4) / 6))
        dur.append(0.5 + 0.5 * (1 - x * x * (3 - 2 * x)))
    cum = np.concatenate([[0], np.cumsum(dur)])
    k = int(min(max(np.floor(u + 1), 0), NS_SLOTS - 1))
    return T0_RUN + cum[k] + (u + 1 - k) * dur[k]


# ------------------------------------------------------------------ the objective
_A = np.array(WELLS, float)


def f(P):
    """f at points P (..., 2)."""
    P = np.asarray(P, float)
    x, y = P[..., 0], P[..., 1]
    out = BOWL * (x * x + y * y)
    for cx, cy, a, s in _A:
        out = out - a * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (2 * s * s))
    return out


def grad(p):
    p = np.asarray(p, float)
    g = 2 * BOWL * p
    for cx, cy, a, s in _A:
        d = p - (cx, cy)
        g = g + a * np.exp(-(d @ d) / (2 * s * s)) * d / (s * s)
    return g


def hess(p):
    p = np.asarray(p, float)
    Hm = 2 * BOWL * np.eye(2)
    for cx, cy, a, s in _A:
        d = p - (cx, cy)
        e = a * np.exp(-(d @ d) / (2 * s * s))
        Hm = Hm + e * (np.eye(2) / (s * s) - np.outer(d, d) / s ** 4)
    return Hm


def minima(n=1601):
    """Every minimum of f on the square: a dense grid, each grid point lower
    than its eight neighbours refined by Newton's method (exact gradient and
    Hessian). Returns [(x, f, |grad|, Hessian eigenvalues)], lowest first."""
    xs = np.linspace(LO, HI, n)
    X, Y = np.meshgrid(xs, xs)
    Z = f(np.stack([X, Y], -1))
    c = Z[1:-1, 1:-1]
    low = np.ones_like(c, bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx or dy:
                low &= c < Z[1 + dy:n - 1 + dy, 1 + dx:n - 1 + dx]
    out = []
    for j, i in zip(*np.nonzero(low)):
        p = np.array([xs[i + 1], xs[j + 1]])
        for _ in range(50):
            step = np.linalg.solve(hess(p), grad(p))
            p = p - step
            if np.abs(step).max() < 1e-15:
                break
        out.append((p, float(f(p)), float(np.linalg.norm(grad(p))), np.linalg.eigvalsh(hess(p))))
    out.sort(key=lambda m: m[1])
    grid_min = (np.array([X.flat[np.argmin(Z)], Y.flat[np.argmin(Z)]]), float(Z.min()))
    return out, grid_min, xs[1] - xs[0]


# ------------------------------------------------------------------ the algorithms
class Counted:
    """The objective with a counter: every point asked for is one evaluation,
    logged in order."""

    def __init__(self, obj=None):
        self.obj = obj or f
        self.x, self.v = [], []

    @property
    def n(self):
        return len(self.v)

    def __call__(self, P):
        P = np.atleast_2d(np.asarray(P, float))
        v = self.obj(P)
        self.x.extend(P.tolist())
        self.v.extend(v.tolist())
        return v


def reflect(P):
    """Points stepped outside the square, mirrored back in."""
    P = np.where(P < LO, 2 * LO - P, P)
    P = np.where(P > HI, 2 * HI - P, P)
    return np.clip(P, LO, HI)


def streams(seed):
    """One random stream each: the shared start, GA, PSO, SA, ACO_R."""
    return [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(5)]


def run_ga(X0, rng, pc, alpha, pm, sm, elite, obj=None):
    F = Counted(obj)
    N = len(X0)
    ids = np.arange(N)
    pop, fit = X0.copy(), F(X0)
    pops, pars, xcs, tours = [ids.copy()], [], [], []
    while F.n + N <= NE:
        won = []
        tours.append((fit.copy(), won))           # each generation: its fitness, its tournaments' winners

        def tour():
            i, j = rng.integers(N, size=2)
            w = int(i if fit[i] <= fit[j] else j)
            won.append(w)
            return w
        par, xc, ch = [], [], []
        for _ in range(N // 2):
            i, j = tour(), tour()
            p1, p2 = pop[i], pop[j]
            if rng.random() < pc:                      # BLX-alpha on each coordinate
                lo, hi = np.minimum(p1, p2), np.maximum(p1, p2)
                d = hi - lo
                kids = [rng.uniform(lo - alpha * d, hi + alpha * d) for _ in range(2)]
            else:
                kids = [p1.copy(), p2.copy()]
            for kid in kids:
                x0 = reflect(kid)
                x1 = reflect(x0 + sm * rng.standard_normal(2)) if rng.random() < pm else x0.copy()
                par.append((ids[i], ids[j]))
                xc.append(x0)
                ch.append(x1)
        cid = np.arange(F.n, F.n + N)
        ch = np.array(ch)
        cf = F(ch)
        eo = np.argsort(fit, kind="stable")[:elite]          # the best parents stay
        wo = np.argsort(cf, kind="stable")[::-1][:elite]     # in place of the worst children
        nid, npos, nfit = cid.copy(), ch.copy(), cf.copy()
        nid[wo], npos[wo], nfit[wo] = ids[eo], pop[eo], fit[eo]
        pars.append(np.array(par))
        xcs.append(np.array(xc))
        ids, pop, fit = nid, npos, nfit
        pops.append(ids.copy())
    return dict(F=F, pops=np.array(pops), par=np.array(pars), xc=np.array(xcs), tours=tours)


def run_pso(X0, rng, w, c1, c2, v0, obj=None):
    F = Counted(obj)
    N = len(X0)
    x = X0.copy()
    v = rng.uniform(-1, 1, (N, 2)) * v0 * (HI - LO)
    fx = F(x)
    pb, pf, pid = x.copy(), fx.copy(), np.arange(N)
    g = int(np.argmin(pf))
    pbs, gs, vs = [pid.copy()], [pid[g]], []
    while F.n + N <= NE:
        r1, r2 = rng.random((N, 2)), rng.random((N, 2))
        v = w * v + c1 * r1 * (pb - x) + c2 * r2 * (pb[g] - x)
        vs.append(v.copy())
        xn = x + v
        out = (xn < LO) | (xn > HI)                    # absorbing walls
        xn = np.clip(xn, LO, HI)
        v = np.where(out, 0.0, v)
        base = F.n
        fn = F(xn)
        x = xn
        better = fn < pf
        pb[better], pf[better], pid[better] = x[better], fn[better], base + np.nonzero(better)[0]
        g = int(np.argmin(pf))
        pbs.append(pid.copy())
        gs.append(pid[g])
    return dict(F=F, pb=np.array(pbs), g=np.array(gs), v=np.array(vs))


def run_sa(x0, rng, T0, T1, step, obj=None):
    F = Counted(obj)
    x = np.array(x0, float)
    fx = float(F(x)[0])
    cur, best = [0], [0]
    K = NE - 1
    a = (T1 / T0) ** (1 / (K - 1))
    acc, up, Ts, dl = [], [], [], []
    for k in range(K):
        T = T0 * a ** k
        y = reflect(x + step * rng.standard_normal(2))
        fy = float(F(y)[0])
        d = fy - fx
        ok = bool(d <= 0 or rng.random() < np.exp(-d / T))
        acc.append(ok)
        up.append(d > 0)
        Ts.append(T)
        dl.append(d)
        if ok:
            x, fx = y, fy
            cur.append(F.n - 1)
        else:
            cur.append(cur[-1])
        best.append(best[-1] if F.v[best[-1]] <= fx else cur[-1])
    return dict(F=F, cur=np.array(cur), best=np.array(best), acc=np.array(acc), up=np.array(up),
                T=np.array(Ts), d=np.array(dl), a=a)


def aco_weights(k, q):
    l = np.arange(1, k + 1)
    w = np.exp(-(l - 1) ** 2 / (2 * q * q * k * k)) / (q * k * np.sqrt(2 * np.pi))
    return w, w / w.sum()


def aco_sigma(S, xi):
    k = len(S)
    return xi * np.abs(S[None, :, :] - S[:, None, :]).sum(1) / (k - 1)


def run_aco(X0, rng, m, q, xi, obj=None):
    F = Counted(obj)
    k = len(X0)
    fs0 = F(X0)
    o = np.argsort(fs0, kind="stable")
    sid, S, fs = o.copy(), X0[o].copy(), fs0[o].copy()
    _, p = aco_weights(k, q)
    arch, guide, sigs, granks = [sid.copy()], [], [], []
    while F.n + m <= NE:
        sig = aco_sigma(S, xi)
        g = rng.choice(k, size=m, p=p)
        granks.extend(g.tolist())
        X = reflect(S[g] + sig[g] * rng.standard_normal((m, 2)))
        base = F.n
        fX = F(X)
        guide.extend(sid[g].tolist())
        sigs.append(sig)
        S2, f2 = np.vstack([S, X]), np.concatenate([fs, fX])
        i2 = np.concatenate([sid, base + np.arange(m)])
        o = np.argsort(f2, kind="stable")[:k]
        sid, S, fs = i2[o], S2[o], f2[o]
        arch.append(sid.copy())
    return dict(F=F, arch=np.array(arch), guide=np.array(guide), sig=np.array(sigs), p=p, granks=np.array(granks))


def run_all(seed=SEED, obj=None):
    r0, rg, rp, rs, ra = streams(seed)
    X0 = r0.uniform(LO, HI, (NPOP, 2))
    return dict(X0=X0, ga=run_ga(X0, rg, **GA_P, obj=obj), pso=run_pso(X0, rp, **PSO_P, obj=obj),
                sa=run_sa(X0[0], rs, **SA_P, obj=obj), aco=run_aco(X0, ra, **ACO_P, obj=obj))


def best_of(F):
    """(best point, best value, evaluations) of a run."""
    v = np.array(F.v)
    i = int(np.argmin(v))
    return np.array(F.x[i]), float(v[i]), F.n


# ------------------------------------------------------------------ the page's data
def i16(a):
    """Integers as base64 of little-endian int16, for the page's b64i16()."""
    a = np.asarray(a)
    assert np.abs(a).max() < 32768
    return base64.b64encode(np.ascontiguousarray(a, dtype="<i2").tobytes()).decode("ascii")


def contours(n=401, tol=0.003):
    """The contour lines of f at LEVELS, simplified (Douglas-Peucker, tol) and
    packed as int16 of 4000 x, one array per level: [count, x, y, x, y, ...]."""
    import contourpy
    xs = np.linspace(LO, HI, n)
    X, Y = np.meshgrid(xs, xs)
    gen = contourpy.contour_generator(xs, xs, f(np.stack([X, Y], -1)))

    def dp(P):
        if len(P) < 3:
            return P
        a, b = P[0], P[-1]
        ab = b - a
        L = np.hypot(*ab)
        q = P - a
        d = np.abs(ab[0] * q[:, 1] - ab[1] * q[:, 0]) / L if L > 1e-12 else np.hypot(q[:, 0], q[:, 1])
        i = int(np.argmax(d))
        if d[i] <= tol:
            return np.array([a, b])
        return np.vstack([dp(P[:i + 1])[:-1], dp(P[i:])])

    out, npts = [], 0
    for lv in LEVELS:
        flat = []
        for seg in gen.lines(lv):
            if len(seg) < 4:
                continue
            closed = np.allclose(seg[0], seg[-1])
            P = dp(seg) if not closed else np.vstack([dp(seg[:len(seg) // 2 + 1])[:-1], dp(seg[len(seg) // 2:])])
            flat += [len(P)] + np.round(P * 4000).astype(int).ravel().tolist()
            npts += len(P)
        out.append(i16(flat))
    return out, npts


JS = r"""
const D = DATA;
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);
function b64i16(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new Int16Array(u.buffer); }
const LO = D.lo, HI = D.hi, NP = D.np, NE = D.ne, G = D.gens, NS = NE / NP;

/* ------------------------------------------------------------ the runs
   Each algorithm's evaluations in order (positions and values), and what it
   decided: the GA's populations and parents, the swarm's personal and global
   bests, the walker's current and best points, the ant archive. Ids are
   evaluation numbers, 0 to 399. */
const run = o => ({x: b64f32(o.x), f: b64f32(o.f)});
const RG = run(D.ga), RP = run(D.pso), RS = run(D.sa), RA = run(D.aco);
const GPOP = b64i16(D.ga.pop), GPAR = b64i16(D.ga.par), GXC = b64f32(D.ga.xc);
const PPB = b64i16(D.pso.pb), PG = b64i16(D.pso.g);
const SCUR = b64i16(D.sa.cur), SBEST = b64i16(D.sa.best), SACC = b64i8(D.sa.acc), SUP = b64i8(D.sa.up);
const AARCH = b64i16(D.aco.arch), AGUIDE = b64i16(D.aco.guide);
const AK = NP, AM = D.aco.m, AQ = D.aco.q, AXI = D.aco.xi, AI = (NE - NP) / AM;
const AW = (() => { const w = []; for (let l = 1; l <= AK; l++) w.push(Math.exp(-((l - 1) ** 2) / (2 * AQ * AQ * AK * AK))); return w.map(v => v / w[0]); })();
/* best so far after n evaluations, n = 0 .. 400 */
function bestCurve(R) { const b = [Infinity]; for (let i = 0; i < NE; i++) b.push(Math.min(b[i], R.f[i])); return b; }
const BEST = [bestCurve(RG), bestCurve(RP), bestCurve(RS), bestCurve(RA)];
/* the evaluation that holds the best so far, after n evaluations */
function bestIds(R) { const b = new Int16Array(NE + 1); for (let i = 1; i < NE; i++) b[i + 1] = R.f[i] < R.f[b[i]] ? i : b[i]; return b; }
const BID = [bestIds(RG), bestIds(RP), bestIds(RS), bestIds(RA)];
/* the kernels of an archive: sigma_l = xi sum_e |s_e - s_l| / (k - 1), each coordinate */
function sigmas(ids) {
  const out = [];
  for (let l = 0; l < AK; l++) {
    let sx = 0, sy = 0; const a = ids[l];
    for (let e = 0; e < AK; e++) { const b = ids[e]; sx += Math.abs(RA.x[2 * b] - RA.x[2 * a]); sy += Math.abs(RA.x[2 * b + 1] - RA.x[2 * a + 1]); }
    out.push([AXI * sx / (AK - 1), AXI * sy / (AK - 1)]);
  }
  return out;
}
const SIG = []; for (let i = 0; i <= AI; i++) SIG.push(sigmas(AARCH.subarray(i * AK, (i + 1) * AK)));

/* ------------------------------------------------------------ clock
   Intro (README, round 2): the maps by .8 s, labels by 1.2 s. The run starts
   at .6 s. Every 20 evaluations are one slot, the same budget for all four at
   every moment: u runs from -1 (nothing evaluated) to 19 (all 400),
   n = 20 (u + 1). The first five slots take 1 s each, where the four are
   still exploring; from the tenth on 0.5 s (a smooth step between). The run
   rests on its end, fades and starts again. */
const T0 = .6, DUR = [], CUM = [0];
for (let k = 0; k < NS; k++) { const x = clamp((k - 4) / 6); DUR.push(.5 + .5 * (1 - x * x * (3 - 2 * x))); CUM.push(CUM[k] + DUR[k]); }
const RUN = CUM[NS], HOLD = 2.6, FADE = .5, REST = .35, PER = RUN + HOLD + FADE + REST;
let BASE = T0;                                   // the start of this loop, set from t by clock()
function clock() {
  if (t < T0) { BASE = T0; return {u: -1, a: 1}; }
  const c = Math.floor((t - T0) / PER), w = t - T0 - c * PER;
  BASE = T0 + c * PER;
  if (w < RUN) { let k = 0; while (k < NS - 1 && CUM[k + 1] <= w) k++; return {u: k - 1 + (w - CUM[k]) / DUR[k], a: 1}; }
  if (w < RUN + HOLD) return {u: NS - 1, a: 1};
  if (w < RUN + HOLD + FADE) return {u: NS - 1, a: 1 - seg(BASE + RUN + HOLD, FADE)};
  return {u: -1, a: 0};
}
/* the moment of this loop at which the clock reads u */
const tOf = u => { const k = clamp(Math.floor(u + 1), 0, NS - 1); return BASE + CUM[k] + (u + 1 - k) * DUR[k]; };
const POSTER_T = (() => { const k = Math.floor(D.poster + 1); return T0 + CUM[k] + (D.poster + 1 - k) * DUR[k]; })();

/* ------------------------------------------------------------ layout */
const MS = 280, MAPS = [{x: 66, y: 44}, {x: 382, y: 44}, {x: 66, y: 378}, {x: 382, y: 378}];
const EP = {x: 754, y: 44, w: 226, h: 280}, YL = D.ylim;
const DOT = 4;
function mapOf(m) {
  const k = MS / (HI - LO);
  return {X: v => m.x + (v - LO) * k, Y: v => m.y + MS - (v - LO) * k, k, m};
}
const P = (M, R, id) => [M.X(R.x[2 * id]), M.Y(R.x[2 * id + 1])];
function clip(m, fn) { ctx.save(); ctx.beginPath(); ctx.rect(m.x, m.y, MS, MS); ctx.clip(); fn(); ctx.restore(); }
function ring(x, y, r, col, a, w = 1.3) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI);
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke(); ctx.restore();
}
function disc(x, y, r, col, a) {             // a filled dot with a white rim, as the k-means figure draws points
  if (a <= 0) return;
  dot(x, y, r, {color: '#fff', fill: col, width: 1.1, alpha: a});
}
function best(x, y, a) { if (a > 0) dot(x, y, 5.2, {color: '#fff', fill: C.accent, width: 1.4, alpha: a}); }
function thin(p, q, col, a, w = 1) { if (a > 0) line([p, q], {color: col, width: w, alpha: a}); }
/* a colour between two of the palette's, s in [0, 1] */
function mix(c1, c2, s) {
  const p = _hex(c1), q = _hex(c2);
  return '#' + [0, 1, 2].map(i => Math.round(lerp(p[i], q[i], clamp(s))).toString(16).padStart(2, '0')).join('');
}

/* the contour lines, decoded once: per level a list of polylines in f's coordinates */
const LEV = D.contours.map(s => {
  const a = b64i16(s), out = []; let i = 0;
  while (i < a.length) { const n = a[i++], pl = []; for (let j = 0; j < n; j++) { pl.push([a[i] / 4000, a[i + 1] / 4000]); i += 2; } out.push(pl); }
  return out;
});
function landscape(M, t0) {
  const al = seg(t0, .45);
  if (al <= 0) return;
  ctx.save(); ctx.globalAlpha *= al; ctx.strokeStyle = C.rule; ctx.lineWidth = 1; ctx.beginPath();
  for (const lv of LEV) for (const pl of lv) {
    ctx.moveTo(M.X(pl[0][0]), M.Y(pl[0][1]));
    for (let j = 1; j < pl.length; j++) ctx.lineTo(M.X(pl[j][0]), M.Y(pl[j][1]));
  }
  ctx.stroke(); ctx.restore();
}
function minimaMarks(M, a) {
  D.minima.forEach((q, i) => {
    const x = M.X(q[0]), y = M.Y(q[1]);
    if (i === 0) { ring(x, y, 6, C.ink, a, 1.4); line([[x - 3.6, y], [x + 3.6, y]], {color: C.ink, width: 1.2, alpha: a}); line([[x, y - 3.6], [x, y + 3.6]], {color: C.ink, width: 1.2, alpha: a}); }
    else ring(x, y, 3.2, C.ink, a, 1.2);
  });
}
function frame(M, o) {
  const {xl, yl, t0} = o, ticks = [-4, -2, 0, 2, 4];
  axes({x: M.m.x, y: M.m.y, w: MS, h: MS, xlim: [LO, HI], ylim: [LO, HI], xticks: ticks, yticks: ticks,
        xfmt: v => xl ? fmt(v) : '', yfmt: v => yl ? fmt(v) : '', xlabel: xl ? 'x_1' : '', ylabel: yl ? 'x_2' : '',
        ylabelGap: 46, tickSize: 16, labelSize: 17, progress: seg(t0, .4)});
}
function header(m, letter, words, t0) {
  const s = lab(t0);
  panel(letter, m.x, m.y - 14 + rise(s), {alpha: s});
  if (typeof words === 'string') text(words, m.x + 35, m.y - 14 + rise(s), {size: 17, color: C.body, alpha: s});
  else words(m.x + 35, m.y - 14 + rise(s), s);
}
function counter(m, s, a, isMath) {
  if (a <= 0) return;
  if (isMath) math(s, m.x + MS, m.y - 14, {size: 16, align: 'right', alpha: a});
  else text(s, m.x + MS, m.y - 14, {size: 15, align: 'right', alpha: a});
}

/* the shared start: the 20 random points arrive one evaluation at a time,
   the best of those evaluated so far in crimson */
function startPts(M, R, u, a, col, j) {
  for (let i = 0; i < NP; i++) {
    const ue = -1 + (i + 1) / NP;
    if (u < ue - .12) break;
    const s = settle(tOf(ue - .12), .18), [x, y] = P(M, R, i);
    disc(x, y, DOT * s, col, a * Math.min(1, s * 1.5));
  }
  const n = Math.max(0, Math.floor(NP * (u + 1) + 1e-9));
  if (n >= 1) best(...P(M, R, BID[j][n]), a);
}

/* ------------------------------------------------------------ (a) genetic algorithm
   Generation g runs over u in [g, g + 1): the children of population g are
   born one by one (each joined to its two parents for a moment, then moved
   by its mutation, if it has one), and at the end the population is
   replaced by the children, the two best parents taking the places of the
   two worst children. */
const GB = c => .03 + .6 * c / (NP - 1), GE = c => GB(c) + .16;
function gaCount(u) {
  if (u < 0) return Math.max(0, Math.floor(NP * (u + 1) + 1e-9));
  const g = Math.floor(u); if (g >= G) return NE;
  let n = NP * (g + 1); const s = u - g;
  for (let c = 0; c < NP; c++) if (s >= GE(c)) n++;
  return n;
}
function drawGA(M, u, a) {
  if (u < 0) { startPts(M, RG, u, a, C.navy, 0); return; }
  const g = Math.min(G, Math.floor(u)), s = g >= G ? 1 : u - g;
  const pop = GPOP.subarray(g * NP, (g + 1) * NP);
  if (g >= G) { for (const id of pop) { const [x, y] = P(M, RG, id); disc(x, y, DOT, C.navy, a); } best(...P(M, RG, BID[0][NE]), a); return; }
  const next = new Set(GPOP.subarray((g + 1) * NP, (g + 2) * NP));
  const selA = 1 - clamp((s - .8) / .2), kid = mix(C.blue, C.navy, (s - .8) / .2);
  // the links first, under every dot
  for (let c = 0; c < NP; c++) {
    if (s < GB(c)) break;
    const la = clamp((s - GB(c)) / .05) * (1 - clamp((s - GE(c) - .04) / .2));
    if (la <= 0) continue;
    const xc = [M.X(GXC[2 * (g * NP + c)]), M.Y(GXC[2 * (g * NP + c) + 1])];
    for (const k of [0, 1]) thin(P(M, RG, GPAR[2 * (g * NP + c) + k]), xc, C.guide, a * .9 * la, 1.1);
    // a mutation: the child's jump from where crossover put it, dotted
    const xf = P(M, RG, NP * (g + 1) + c), mv = clamp((s - GB(c) - .05) / .11);
    if (Math.hypot(xf[0] - xc[0], xf[1] - xc[1]) > 1 && mv > 0)
      line([xc, [lerp(xc[0], xf[0], mv), lerp(xc[1], xf[1], mv)]], {color: C.navy, width: 1.1, dash: [2, 3], alpha: a * la});
  }
  // the parents: all of population g, the two that stay drawn on
  for (const id of pop) { const [x, y] = P(M, RG, id); disc(x, y, DOT, C.navy, a * (next.has(id) ? 1 : selA)); }
  // the children: born at the crossover point, moved by mutation, then members
  for (let c = 0; c < NP; c++) {
    if (s < GB(c)) break;
    const id = NP * (g + 1) + c, xc = [M.X(GXC[2 * (g * NP + c)]), M.Y(GXC[2 * (g * NP + c) + 1])], xf = P(M, RG, id);
    const mv = easeInOut(clamp((s - GB(c) - .05) / .11)), x = lerp(xc[0], xf[0], mv), y = lerp(xc[1], xf[1], mv);
    const born = settle(tOf(g + GB(c)), .12), keep = next.has(id) ? 1 : selA;
    if (s < GE(c)) ring(x, y, (DOT - .2) * born, C.navy, a * born, 1.3);
    else disc(x, y, DOT, kid, a * keep);
  }
  best(...P(M, RG, BID[0][gaCount(u)]), a);
}

/* ------------------------------------------------------------ (b) particle swarm
   Iteration g runs over u in [g, g + 1): every particle flies along its
   velocity arrow to its next position (u in [g, g + .5]), is evaluated, its
   personal best and the swarm's best are updated, and the next arrows grow. */
const PFLY = .5;
function psoCount(u) { if (u < 0) return Math.max(0, Math.floor(NP * (u + 1) + 1e-9)); const g = Math.floor(u); return g >= G ? NE : NP * (g + 1) + (u - g >= PFLY ? NP : 0); }
function drawPSO(M, u, a) {
  if (u < 0) {
    const ga = clamp((u + .28) / .2);
    if (ga > 0) for (let i = 0; i < NP; i++) arrowTo(M, P(M, RP, i), P(M, RP, NP + i), a * ga, ga);
    startPts(M, RP, u, a, C.blue, 1);
    return;
  }
  const g = Math.min(G, Math.floor(u)), s = g >= G ? 1 : u - g;
  const done = g >= G ? G : (s >= PFLY ? g + 1 : g);       // updates evaluated
  // personal bests: a faint line from each particle to its own best point
  const pos = [];
  for (let i = 0; i < NP; i++) {
    const p0 = P(M, RP, NP * g + i), p1 = g < G ? P(M, RP, NP * (g + 1) + i) : p0;
    const e = g < G ? easeInOut(clamp(s / PFLY)) : 1;
    pos.push([lerp(p0[0], p1[0], e), lerp(p0[1], p1[1], e)]);
  }
  for (let i = 0; i < NP; i++) {
    const pb = P(M, RP, PPB[done * NP + i]);
    if (Math.hypot(pb[0] - pos[i][0], pb[1] - pos[i][1]) > 2) { thin(pos[i], pb, C.mist, a * .9, 1); ring(pb[0], pb[1], 2.6, C.sky, a, 1.1); }
  }
  // velocity arrows: the step each particle is about to take (or is taking)
  for (let i = 0; i < NP; i++) {
    if (g < G && s < PFLY) arrowTo(M, pos[i], P(M, RP, NP * (g + 1) + i), a, 1);
    else if (done < G) { const ga = clamp((s - .6) / .22); if (ga > 0) arrowTo(M, pos[i], P(M, RP, NP * (done + 1) + i), a * ga, ga); }
  }
  for (let i = 0; i < NP; i++) disc(pos[i][0], pos[i][1], DOT, C.blue, a);
  // the swarm's best, gliding to its new place when the swarm finds a better one
  const g0 = P(M, RP, PG[Math.max(0, done - 1)]), g1 = P(M, RP, PG[done]);
  const gs = done > 0 && g < G && s >= PFLY ? settle(tOf(g + PFLY), .2) : 1;
  best(lerp(g0[0], g1[0], gs), lerp(g0[1], g1[1], gs), a);
}
function arrowTo(M, p, q, a, grow) {
  const dx = (q[0] - p[0]) * grow, dy = (q[1] - p[1]) * grow, L = Math.hypot(dx, dy);
  if (L < 4 || a <= 0) return;
  arrow(p[0], p[1], p[0] + dx, p[1] + dy, {color: C.blue, width: 1.3, head: Math.min(8, 2 + L * .4), alpha: a * .9});
}

/* ------------------------------------------------------------ (c) simulated annealing
   One evaluation per proposal, at the same pace as the others: the walker
   (navy) and its recent path, the proposals it rejected (faint grey), the
   uphill steps it accepted (open rings), and the temperature. */
const SWIN = 30;
const saN = u => clamp(Math.floor(NP * (u + 1) + 1e-9), 0, NE);
function drawSA(M, u, a) {
  const nf = NP * (u + 1), n = saN(u);
  if (n < 1) return;
  // rejected proposals of the last SWIN evaluations, fading with age
  for (let j = Math.max(1, n - SWIN); j < n; j++) {
    const age = (nf - j - 1) / SWIN;
    if (!SACC[j - 1]) { const [x, y] = P(M, RS, j); dot(x, y, 1.9, {color: C.guide, fill: C.guide, width: .6, alpha: a * .75 * (1 - age)}); }
  }
  // the path: the walker's last accepted moves
  for (let j = Math.max(1, n - SWIN); j < n; j++) {
    if (!SACC[j - 1]) continue;
    const age = (nf - j - 1) / SWIN, p = P(M, RS, SCUR[j - 1]), q = P(M, RS, j);
    thin(p, q, C.navy, a * .85 * (1 - age), 1.3);
    if (SUP[j - 1]) ring(q[0], q[1], 3, C.navy, a * (1 - age), 1.2);
  }
  const k = SCUR[n - 1], kb = n >= 2 ? SCUR[n - 2] : k, fr = clamp((nf - n) / .5);
  const p1 = P(M, RS, k), p0 = P(M, RS, kb);
  disc(lerp(p0[0], p1[0], easeOut(fr)), lerp(p0[1], p1[1], easeOut(fr)), 4.4, C.navy, a);
  best(...P(M, RS, SBEST[n - 1]), a);
}
const saT = u => { const n = saN(u); return n < 2 ? D.sa.T0 : D.sa.T0 * Math.pow(D.sa.ar, n - 2); };

/* ------------------------------------------------------------ (d) ACO_R
   The archive of the 20 best points so far, ranked by f: each holds a
   Gaussian kernel (its 1 sigma ellipse, darker for higher rank, the
   pheromone), new ants are drawn from a kernel chosen by rank (each joined
   to its kernel's centre for a moment), and the archive keeps the best 20. */
const AWIN = 8;
const acoIt = u => clamp(Math.floor(10 * u + 1e-9), 0, AI);      // iterations done
function drawACO(M, u, a) {
  if (u < 0) { startPts(M, RA, u, a, C.navy, 3); return; }
  const it = acoIt(u), ids = AARCH.subarray(it * AK, (it + 1) * AK), sg = SIG[it];
  const ka = clamp(u / .25);
  clip(M.m, () => {
    for (let l = AK - 1; l >= 0; l--) {
      const id = ids[l], [x, y] = P(M, RA, id);
      ctx.save(); ctx.globalAlpha *= a * ka * (.18 + .55 * AW[l]); ctx.strokeStyle = C.sky; ctx.lineWidth = 1.1;
      ctx.beginPath(); ctx.ellipse(x, y, Math.max(.5, sg[l][0] * M.k), Math.max(.5, sg[l][1] * M.k), 0, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
    }
  });
  // the newest ants, each joined to the centre of the kernel it was drawn from
  const uf = 10 * u;
  for (let j = Math.max(0, it - AWIN); j < it; j++) {
    const age = (uf - j - 1) / AWIN;
    for (let m = 0; m < AM; m++) {
      const id = NP + AM * j + m, gid = AGUIDE[AM * j + m], q = P(M, RA, id);
      thin(P(M, RA, gid), q, C.sky, a * .9 * (1 - age), 1);
      disc(q[0], q[1], DOT - .4, C.blue, a * (1 - age * .6));
    }
  }
  for (let l = AK - 1; l >= 1; l--) { const [x, y] = P(M, RA, ids[l]); disc(x, y, 2.6, C.navy, a); }
  best(...P(M, RA, ids[0]), a);
}

/* ------------------------------------------------------------ (e) convergence
   The best so far after each evaluation as step lines, built once (the
   layout is fixed): pts in drawing units, cut[n] the points up to n. */
let ECACHE = null;
function eCurves(A) {
  if (!ECACHE) ECACHE = BEST.map(b => {
    const pts = [[A.X(1), A.Y(b[1])]], cut = [0, 1];
    for (let i = 2; i <= NE; i++) { if (b[i] !== b[i - 1]) pts.push([A.X(i), A.Y(b[i - 1])]); pts.push([A.X(i), A.Y(b[i])]); cut.push(pts.length); }
    return {pts, cut};
  });
  return ECACHE;
}
const SER = [
  {name: 'genetic algorithm', color: C.navy, dash: null, width: 2.2},
  {name: 'particle swarm', color: C.blue, dash: [8, 4], width: 2.2},
  {name: 'simulated annealing', color: C.sky, dash: [2, 3], width: 2.4},
  {name: 'ant colony', color: C.ink, dash: [9, 3, 2, 3], width: 1.6},
];
function drawE(u, a, counts) {
  header({x: 700, y: EP.y}, 'e', 'convergence', .14);
  const A = axes({x: EP.x, y: EP.y, w: EP.w, h: EP.h, xlim: [0, NE], ylim: YL, xticks: [0, 100, 200, 300, 400],
                  yticks: D.yticks, xlabel: '\\rm{function evaluations}', ylabel: '\\rm{best}\\ f\\ \\rm{so far}',
                  ylabelGap: 54, tickSize: 16, labelSize: 17, grid: true, progress: seg(.12, .4)});
  const ga = seg(.4, .3);
  A.inside(() => line([[EP.x, A.Y(D.fstar)], [EP.x + EP.w, A.Y(D.fstar)]], {color: C.guide, width: 1, dash: [5, 4], alpha: ga}));
  const EC = eCurves(A);
  A.inside(() => {
    SER.forEach((s, j) => line(EC[j].pts, {color: s.color, width: s.width * .7, dash: s.dash, alpha: .22 * seg(.3 + .05 * j, .4)}));
    if (u > -1) {
      const cx = A.X(NP * (u + 1));
      line([[cx, EP.y], [cx, EP.y + EP.h]], {color: C.rule, width: 1, alpha: a});
      SER.forEach((s, j) => { if (counts[j] >= 1) line(EC[j].pts.slice(0, EC[j].cut[counts[j]]), {color: s.color, width: s.width, dash: s.dash, alpha: a}); });
    }
  });
  text('global minimum', EP.x + EP.w - 6, A.Y(D.fstar) - 10, {size: 14, color: C.muted, align: 'right', alpha: ga});
  // legend
  const la = seg(.45, .25), LX = EP.x + EP.w - 180, LY = EP.y + 8, LH = 22;
  if (la > 0) {
    ctx.save(); ctx.globalAlpha *= la; ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 1;
    ctx.fillRect(LX, LY, 174, 4 * LH + 8); ctx.strokeRect(LX, LY, 174, 4 * LH + 8); ctx.restore();
    SER.forEach((s, j) => {
      const y = LY + 15 + j * LH;
      line([[LX + 8, y], [LX + 30, y]], {color: s.color, width: s.width, dash: s.dash, alpha: la});
      text(s.name, LX + 36, y + 5, {size: 15, alpha: la});
    });
  }
  return A;
}

/* ------------------------------------------------------------ the key */
function key(t0) {
  const x0 = 702, y0 = 412, LH = 27, gx = x0 + 14, tx = x0 + 36;
  const rows = [
    [a => { ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = C.rule; ctx.lineWidth = 1; for (const r of [5, 9, 13]) { ctx.beginPath(); ctx.arc(gx, 7, r, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); } ctx.restore(); }, [['contours of '], ['f', 1], [', every 0.2']]],
    [a => { ring(gx, 0, 6, C.ink, a, 1.4); line([[gx - 3.6, 0], [gx + 3.6, 0]], {color: C.ink, width: 1.2, alpha: a}); line([[gx, -3.6], [gx, 3.6]], {color: C.ink, width: 1.2, alpha: a}); }, 'global minimum'],
    [a => ring(gx, 0, 3.2, C.ink, a, 1.2), 'local minima'],
    [a => best(gx, 0, a), 'best point so far'],
    [a => { thin([gx - 12, -5], [gx, 4], C.guide, a, 1.1); thin([gx + 12, -5], [gx, 4], C.guide, a, 1.1); disc(gx - 12, -5, DOT, C.navy, a); disc(gx + 12, -5, DOT, C.navy, a); disc(gx, 4, DOT, C.blue, a); }, '(a) parents and a child'],
    [a => { arrow(gx - 12, 3, gx + 12, -3, {color: C.blue, width: 1.3, head: 7, alpha: a * .9}); disc(gx - 12, 3, DOT, C.blue, a); }, '(b) particle and velocity'],
    [a => { dot(gx - 9, -3, 1.9, {color: C.guide, fill: C.guide, width: .6, alpha: a * .75}); dot(gx - 3, 4, 1.9, {color: C.guide, fill: C.guide, width: .6, alpha: a * .75}); ring(gx + 8, 0, 3, C.navy, a, 1.2); }, '(c) rejected, uphill accepted'],
    [a => { ctx.save(); ctx.globalAlpha *= a * .7; ctx.strokeStyle = C.sky; ctx.lineWidth = 1.1; ctx.beginPath(); ctx.ellipse(gx, 0, 13, 7, 0, 0, 2 * Math.PI); ctx.stroke(); ctx.restore(); disc(gx, 0, 2.6, C.navy, a); }, '(d) archive point and kernel'],
  ];
  rows.forEach(([g, s], i) => {
    const a = lab(t0 + .03 * i), y = y0 + i * LH;
    if (a <= 0) return;
    ctx.save(); ctx.translate(0, y + rise(a)); g(a); ctx.restore();
    if (typeof s === 'string') text(s, tx, y + 5 + rise(a), {size: 15, color: C.body, alpha: a});
    else {                                   // words with a symbol in math
      let x = tx;
      for (const [w, m] of s) x += m ? math(w, x, y + 5 + rise(a), {size: 16, color: C.body, alpha: a}) + 1
                                     : text(w, x, y + 5 + rise(a), {size: 15, color: C.body, alpha: a});
    }
  });
}

function draw() {
  const {u, a} = clock();
  const Ms = MAPS.map(mapOf);
  // the four maps: the same landscape, its minima, the run
  const subs = ['genetic algorithm', 'particle swarm', 'simulated annealing', null];
  Ms.forEach((M, j) => {
    frame(M, {xl: j >= 2, yl: j % 2 === 0, t0: .03 * j});
    clip(M.m, () => landscape(M, .1 + .04 * j));
    minimaMarks(M, seg(.4 + .03 * j, .25));
  });
  header(MAPS[0], 'a', subs[0], .05);
  header(MAPS[1], 'b', subs[1], .08);
  header(MAPS[2], 'c', subs[2], .11);
  header(MAPS[3], 'd', (x, y, s) => {
    const w = text('ant colony, ', x, y, {size: 17, color: C.body, alpha: s});
    math('\\rm{ACO}_{\\rm{R}}', x + w, y, {size: 17, color: C.body, alpha: s});
  }, .14);
  if (a > 0) {
    clip(Ms[0].m, () => drawGA(Ms[0], u, a));
    clip(Ms[1].m, () => drawPSO(Ms[1], u, a));
    clip(Ms[2].m, () => drawSA(Ms[2], u, a));
    drawACO(Ms[3], u, a);
  }
  // counters
  const ca = seg(.5, .2);
  const gen = u < 0 ? 0 : Math.min(G, Math.floor(u) + (u - Math.floor(u) >= .8 ? 1 : 0));
  counter(MAPS[0], `generation ${gen}`, ca);
  const itp = u < 0 ? 0 : Math.min(G, Math.floor(u) + (u - Math.floor(u) >= PFLY ? 1 : 0));
  counter(MAPS[1], `iteration ${itp}`, ca);
  const T = saT(u), Ts = T >= .095 ? T.toFixed(2) : T.toPrecision(2);
  counter(MAPS[2], `T = ${Ts}`, ca, true);
  // the gauge under the temperature: its length is log T between T_0 and T_end
  if (ca > 0) {
    const gw = 64, gx = MAPS[2].x + MS - gw, gy = MAPS[2].y - 8, fr = clamp(Math.log(T / D.sa.T1) / Math.log(D.sa.T0 / D.sa.T1));
    ctx.save(); ctx.globalAlpha *= ca; ctx.fillStyle = C.steel2; ctx.fillRect(gx, gy, gw, 3);
    ctx.fillStyle = C.navy; ctx.fillRect(gx, gy, gw * fr, 3); ctx.restore();
  }
  counter(MAPS[3], `iteration ${u < 0 ? 0 : acoIt(u)}`, ca);
  const n = u < 0 && t < T0 ? 0 : Math.round(NP * (u + 1));
  drawE(u, a, [gaCount(u), psoCount(u), saN(u), u < 0 ? saN(u) : Math.min(NE, NP + AM * acoIt(u))].map(v => a > 0 ? v : 0));
  math(`n = ${a > 0 ? n : 0}`, EP.x + EP.w, EP.y - 14, {size: 16, align: 'right', alpha: ca});
  key(.5);
  math(D.params[0], 20, H - 32, {size: 14, color: C.muted, alpha: seg(.45, .3)});
  math(D.params[1], 20, H - 12, {size: 14, color: C.muted, alpha: seg(.5, .3)});
}
boot();
"""


def build(still=True):
    mins, grid_min, dx = minima()
    xs, fs = mins[0][0], mins[0][1]
    R = run_all()
    G = len(R["ga"]["pops"]) - 1
    lines, npts = contours()
    res = {}
    for key in ("ga", "pso", "sa", "aco"):
        bx, bf, n = best_of(R[key]["F"])
        res[key] = (bx, bf, n, float(np.hypot(*(bx - xs))))
    print(f"global minimum f* = {fs:.10f} at ({xs[0]:.8f}, {xs[1]:.8f}); {len(mins)} minima")
    for key, (bx, bf, n, d) in res.items():
        print(f"  {key:4s}: {n} evaluations, best f = {bf:.8f} at ({bx[0]:.5f}, {bx[1]:.5f}), "
              f"f - f* = {bf - fs:.2e}, distance {d:.2e}")
    print(f"contours: {len(LEVELS)} levels, {npts} points")
    data = dict(
        lo=LO, hi=HI, np=NPOP, ne=NE, gens=G, poster=3.35,
        minima=[[float(m[0][0]), float(m[0][1])] for m in mins], fstar=fs,
        ylim=[-2.0, 0.0], yticks=[-2, -1.5, -1, -0.5, 0],
        contours=lines,
        ga=dict(x=common.f32(np.array(R["ga"]["F"].x)), f=common.f32(R["ga"]["F"].v),
                pop=i16(R["ga"]["pops"]), par=i16(R["ga"]["par"]), xc=common.f32(R["ga"]["xc"])),
        pso=dict(x=common.f32(np.array(R["pso"]["F"].x)), f=common.f32(R["pso"]["F"].v),
                 pb=i16(R["pso"]["pb"]), g=i16(R["pso"]["g"])),
        sa=dict(x=common.f32(np.array(R["sa"]["F"].x)), f=common.f32(R["sa"]["F"].v),
                cur=i16(R["sa"]["cur"]), best=i16(R["sa"]["best"]),
                acc=common.i8(R["sa"]["acc"].astype(int)), up=common.i8(R["sa"]["up"].astype(int)),
                T0=SA_P["T0"], T1=SA_P["T1"], ar=R["sa"]["a"]),
        aco=dict(x=common.f32(np.array(R["aco"]["F"].x)), f=common.f32(R["aco"]["F"].v),
                 arch=i16(R["aco"]["arch"]), guide=i16(R["aco"]["guide"]), m=ACO_P["m"], q=ACO_P["q"], xi=ACO_P["xi"]),
        params=[
            r"f(x) = 0.04|x|^2 - \Sigma\ a_i\ \rm{exp}(-|x - c_i|^2/2s_i^2)\rm{, seven wells;   400 evaluations of }f\,\rm{ each, seed %d;   "
            r"GA: tournament, blend crossover }\alpha\ = 0.5\rm{, }p_{\rm{m}} = 0.25\rm{, 2 elites}" % SEED,
            r"\rm{PSO: }w = 0.7298,\ c_1 = c_2 = 1.4962\rm{;   SA: }T\ \rm{from 2 to 0.002, geometric, steps of 1;   "
            r"continuous ACO (ACO}_{\rm{R}}\rm{): }k = 20,\ m = 2,\ q = 0.5,\ \xi\ = 0.85",
        ],
    )
    title = "Figure 9: Four global optimization algorithms on one landscape with seven minima"
    aria = ("Four contour maps of the same landscape with seven minima show a genetic algorithm, particle swarm "
            "optimization, simulated annealing and continuous ant colony optimization searching it, each with 400 "
            "evaluations of the objective; a fifth panel plots the best value each has found against the evaluations "
            "used, with the global minimum as a dashed line.")
    common.build_html(NAME, title, aria, 1000, H_PAGE, data, JS)
    if still:
        png = common.still(NAME, quality=88)
        print("still:", png)
    return dict(mins=mins, grid_min=grid_min, dx=dx, R=R, res=res, npts=npts)


# ------------------------------------------------------------------ validation
KEYS = ("ga", "pso", "sa", "aco")
NAMES = dict(ga="GA", pso="PSO", sa="SA", aco="ACO_R")
STUDY = 200          # seeds in the robustness study


def descend(p, obj=None, jac=None):
    """A local, gradient based search from p (BFGS): where a local method ends."""
    from scipy.optimize import minimize
    obj, jac = obj or f, (jac if obj else grad)
    return minimize(lambda q: float(obj(np.asarray(q))), np.asarray(p, float), jac=jac, method="BFGS",
                    options=dict(gtol=1e-10)).x


def basin(p, mins):
    q = descend(p)
    return int(np.argmin([np.hypot(*(q - m[0])) for m in mins]))


_MINS = None


def _study(seed):
    """One seed of the robustness study (run in a process pool)."""
    R = run_all(seed)
    out = dict(seed=seed)
    for k in KEYS:
        bx, bf, n = best_of(R[k]["F"])
        out[k] = (bx, bf, n, basin(bx, _MINS))
    F0 = f(R["X0"])
    out["start"] = basin(R["X0"][int(np.argmin(F0))], _MINS)
    # the GA's tournaments: the rank (0 = best) of each winner in its population, and the
    # exact probabilities of each rank, every one of the N^2 pairs of contestants enumerated
    N = NPOP
    I, J = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    obs, exp, dup = np.zeros(N), np.zeros(N), 0
    for fit, won in R["ga"]["tours"]:
        rk = np.argsort(np.argsort(fit, kind="stable"), kind="stable")
        exp += np.bincount(rk[np.where(fit[I] <= fit[J], I, J)].ravel(), minlength=N) / N ** 2 * len(won)
        obs += np.bincount(rk[won], minlength=N)
        dup += len(np.unique(fit)) < N
    out["tour"] = (obs, exp, dup, len(R["ga"]["tours"]))
    sa = R["sa"]
    out["sa_up"] = (sa["acc"][sa["up"]], np.exp(-sa["d"][sa["up"]] / sa["T"][sa["up"]]), sa["T"][sa["up"]])
    out["aco_ranks"] = R["aco"]["granks"]
    return out


def _bench(args):
    """One run of all four on a textbook test function."""
    name, seed = args
    obj = dict(himmelblau=himmelblau, rastrigin=rastrigin)[name]
    R = run_all(seed, obj=obj)
    return name, seed, {k: best_of(R[k]["F"]) for k in KEYS}


def himmelblau(P):
    P = np.asarray(P, float)
    x, y = P[..., 0], P[..., 1]
    return (x * x + y - 11) ** 2 + (x + y * y - 7) ** 2


def rastrigin(P):
    P = np.asarray(P, float)
    return 20 + (P * P - 10 * np.cos(2 * np.pi * P)).sum(-1)


HIMMELBLAU_MIN = np.array([(3.0, 2.0), (-2.805118, 3.131312), (-3.779310, -3.283186), (3.584428, -1.848126)])


def validate(B):
    """The minima of f by three independent routes, the runs' parameters and
    results, the mechanisms against closed forms, the implementations on
    textbook test functions, a 200 seed robustness study, and the page's own
    arithmetic; writes sp_opt_global.check.txt and prints it."""
    global _MINS
    from multiprocessing import Pool
    from scipy.optimize import differential_evolution, shgo
    mins, R = B["mins"], B["R"]
    _MINS = mins
    xs, fs = mins[0][0], mins[0][1]
    bounds = [(LO, HI), (LO, HI)]
    fo = lambda q: float(f(np.asarray(q)))
    de = differential_evolution(fo, bounds, seed=1, tol=1e-14, atol=0, popsize=40, maxiter=3000, polish=True)
    sh = shgo(fo, bounds, sampling_method="sobol", n=512, iters=3)
    conv = []
    for n in (201, 401, 801, 1601, 3201):
        g = np.linspace(LO, HI, n)
        X, Y = np.meshgrid(g, g)
        conv.append((n, g[1] - g[0], float(f(np.stack([X, Y], -1)).min())))
    # a local method from random starts: how often it reaches the global minimum
    rng = np.random.default_rng(2026)
    starts = rng.uniform(LO, HI, (2000, 2))
    with Pool(4) as pool:
        loc = pool.starmap(basin, [(p, mins) for p in starts], chunksize=50)
        study = pool.map(_study, range(STUDY), chunksize=5)
        bench = pool.map(_bench, [(nm, sd) for nm in ("himmelblau", "rastrigin") for sd in range(100)], chunksize=5)
    loc = np.array(loc)

    L = []
    say = L.append
    say("Figure 9, global optimization algorithms: check of tools/numfig/sp_opt_global.py")
    say("")
    say("MODEL")
    say(f"  f(x) = {BOWL:g} |x|^2 - sum_i a_i exp(-|x - c_i|^2 / (2 s_i^2)) on -4 <= x_1, x_2 <= 4, seven wells:")
    for cx, cy, aa, ss in WELLS:
        say(f"    c = ({cx:+.1f}, {cy:+.1f}), a = {aa:.2f}, s = {ss:.2f}")
    say(f"  Budget: {NE} evaluations of f for each algorithm, counted by a wrapper around f (every point")
    say(f"  asked for is one evaluation). GA, PSO and ACO_R start from the same {NPOP} uniform random points;")
    say("  SA starts at the first of them. Seed: numpy SeedSequence(%d).spawn(5), one stream for the start" % SEED)
    say("  and one for each algorithm (default_rng). Points stepped outside the square are mirrored back")
    say("  in (GA, SA, ACO_R); PSO's walls absorb (the particle stops on the wall, that velocity component")
    say("  is set to zero).")
    say(f"  (a) GA: {NPOP} per generation, binary tournament selection (with replacement), BLX-alpha crossover")
    say(f"      (alpha = {GA_P['alpha']:g}, probability {GA_P['pc']:g}), Gaussian mutation (probability {GA_P['pm']:g} per child,")
    say(f"      sigma = {GA_P['sm']:g}), the {GA_P['elite']} best parents replace the {GA_P['elite']} worst children: {len(R['ga']['pops']) - 1} generations.")
    say(f"  (b) PSO: {NPOP} particles, global best, v <- w v + c1 r1 (p - x) + c2 r2 (g - x), w = {PSO_P['w']:g},")
    say(f"      c1 = c2 = {PSO_P['c1']:g} (Clerc and Kennedy's constriction, chi = 0.7298 with phi = 4.1); first")
    say(f"      velocities uniform in +-{PSO_P['v0'] * (HI - LO):g}: {len(R['pso']['pb']) - 1} iterations.")
    say(f"  (c) SA: Gaussian proposals, sigma = {SA_P['step']:g}; Metropolis acceptance, exp(-df / T) for uphill moves;")
    say(f"      T_k = {SA_P['T0']:g} a^k, a = {R['sa']['a']:.8f}, from {SA_P['T0']:g} to {SA_P['T1']:g} over {NE - 1} proposals.")
    say(f"  (d) ACO_R (Socha and Dorigo 2008): archive k = {NPOP} solutions sorted by f; rank weights")
    say("      w_l = exp(-(l - 1)^2 / (2 q^2 k^2)) / (q k sqrt(2 pi)), q = %g; each ant picks one archive" % ACO_P["q"])
    say("      solution l with probability w_l / sum w and samples N(s_l, sigma_l) in each coordinate,")
    say("      sigma_l = xi sum_e |s_e - s_l| / (k - 1), xi = %g; m = %d ants per iteration, then the archive" % (ACO_P["xi"], ACO_P["m"]))
    say(f"      keeps the best k: {len(R['aco']['arch']) - 1} iterations. (The paper's optional rotation of the")
    say("      coordinate system for correlated variables is not used.)")
    say("")
    say("THE OBJECTIVE'S MINIMA, FOUND INDEPENDENTLY OF THE ALGORITHMS")
    say(f"  Dense grid, 1601 x 1601 points (spacing {B['dx']:.4f}); every grid point lower than its eight")
    say("  neighbours refined by Newton's method with the exact gradient and Hessian:")
    for i, (p, v, gn, ev) in enumerate(mins):
        say(f"    {'global' if i == 0 else 'local '} x = ({p[0]:+.10f}, {p[1]:+.10f}), f = {v:+.12f}, |grad f| = {gn:.1e},"
            f" Hessian eigenvalues {ev[0]:.4f}, {ev[1]:.4f}")
    say(f"  All {len(mins)} have a positive definite Hessian: they are minima. The global one lies "
        f"{mins[1][1] - fs:.4f} below the next.")
    say("  Grid convergence: the grid's lowest value against f*")
    for n, h, v in conv:
        say(f"    {n:5d} x {n:<5d} (h = {h:.5f}): {v:+.10f}, above f* by {v - fs:.2e}")
    say(f"  scipy differential_evolution (seed 1, polished): f = {de.fun:+.12f} at ({de.x[0]:+.10f}, {de.x[1]:+.10f}),")
    say(f"    against Newton: {abs(de.fun - fs):.1e} in f, {np.hypot(*(de.x - xs)):.1e} in x.")
    say(f"  scipy shgo (Sobol, 512 points, 3 iterations): f = {sh.fun:+.12f} at ({sh.x[0]:+.10f}, {sh.x[1]:+.10f}),")
    say(f"    against Newton: {abs(sh.fun - fs):.1e} in f, {np.hypot(*(sh.x - xs)):.1e} in x.")
    say(f"  A local method (BFGS) from {len(starts)} uniform random starts reaches the global minimum from "
        f"{np.mean(loc == 0) * 100:.1f}% of them;")
    say("    the others stop in a local minimum: " + ", ".join(f"{np.mean(loc == i) * 100:.1f}%" for i in range(1, len(mins))) + ".")
    say("")
    say(f"THE RUNS SHOWN (seed {SEED})")
    for k in KEYS:
        bx, bf, n, d = B["res"][k]
        say(f"  {NAMES[k]:5s}: {n} evaluations; best f = {bf:+.10f} at ({bx[0]:+.6f}, {bx[1]:+.6f});"
            f" f - f* = {bf - fs:.2e}; distance to the global minimizer {d:.2e}")
    X0 = R["X0"]
    F0 = f(X0)
    b0 = int(np.argmin(F0))
    st0 = basin(X0[b0], mins)
    say(f"  The best of the {NPOP} shared starting points, f = {F0[b0]:+.4f} at ({X0[b0][0]:+.3f}, {X0[b0][1]:+.3f}), lies in the basin")
    sab = basin(X0[0], mins)
    nin = sum(basin(q, mins) == 0 for q in X0)
    say(f"  of the local minimum at ({mins[st0][0][0]:+.3f}, {mins[st0][0][1]:+.3f}) (f = {mins[st0][1]:+.4f}), the second deepest; so does SA's start,")
    say(f"  ({X0[0][0]:+.3f}, {X0[0][1]:+.3f}), f = {F0[0]:+.4f} (basin {sab}, counting the minima above from 0). {nin} of the 20 lie higher up on")
    say("  the global well's slopes. First evaluation below the second lowest minimum (that is, low in the global well):")
    f2 = mins[1][1]
    firsts = {}
    for k in KEYS:
        v = np.array(R[k]["F"].v)
        firsts[k] = int(np.nonzero(v < f2)[0][0]) + 1
    say("    " + ", ".join(f"{NAMES[k]} {firsts[k]}" for k in KEYS) + " (evaluation number).")
    say("")
    say(f"ROBUSTNESS: THE SAME SETTINGS, {STUDY} SEEDS (0 to {STUDY - 1})")
    for k in KEYS:
        ok = np.array([o[k][3] == 0 for o in study])
        d = np.array([np.hypot(*(o[k][0] - xs)) for o in study])
        ns = {o[k][2] for o in study}
        say(f"  {NAMES[k]:5s}: ends in the global minimum's basin in {ok.mean() * 100:.1f}% of seeds, within 0.1 of it in"
            f" {np.mean(d < .1) * 100:.1f}%; median distance {np.median(d):.1e}; evaluations {sorted(ns)}")
    allok = np.array([all(o[k][3] == 0 for k in KEYS) for o in study])
    away = np.array([o["start"] != 0 for o in study])
    say(f"  All four in the global basin: {allok.mean() * 100:.1f}% of seeds. The best starting point lies outside the")
    say(f"  global basin for {away.sum()} seeds; for {np.sum(away & allok)} of them all four still end in it. Seed {SEED}, shown, is one of")
    say("  these, chosen so that the figure shows the search for the global well.")
    say("")
    say("THE MECHANISMS AGAINST CLOSED FORMS (pooled over the 200 seeds)")
    N = NPOP
    obs = sum(o["tour"][0] for o in study)
    exp = sum(o["tour"][1] for o in study)
    dup = sum(o["tour"][2] for o in study)
    ngen = sum(o["tour"][3] for o in study)
    nt = obs.sum()
    po, pe = obs / nt, exp / nt
    pr = (2 * (N - np.arange(N)) - 1) / N ** 2
    se = np.sqrt(pe * (1 - pe) / nt)
    say("  GA tournament (size 2, with replacement): for distinct values P(winner has rank r) = (2 (N - r) - 1) / N^2,")
    say(f"    r = 0 the best: {pr[0]:.4f} for rank 0. But a child neither crossed nor mutated (probability 0.1 x 0.75) is a")
    say(f"    copy of its parent, and {dup} of the {ngen} populations hold equal values, where the first contestant wins")
    say("    a tie; the exact probabilities, every one of the N^2 pairs enumerated for each population, give")
    say(f"    rank 0 {pe[0]:.4f}, rank 9 {pe[9]:.4f}, rank 19 {pe[19]:.5f}; observed over {int(nt)} tournaments {po[0]:.4f},")
    say(f"    {po[9]:.4f} and {po[19]:.5f}; largest deviation over the 20 ranks {np.abs((po - pe) / se).max():.2f} standard errors.")
    acc = np.concatenate([o["sa_up"][0] for o in study])
    pex = np.concatenate([o["sa_up"][1] for o in study])
    Tu = np.concatenate([o["sa_up"][2] for o in study])
    say(f"  SA Metropolis rule: {len(acc)} uphill proposals; accepted {acc.mean():.4f}, expected mean exp(-df/T) {pex.mean():.4f}")
    say(f"    ({(acc.mean() - pex.mean()) / np.sqrt(np.sum(pex * (1 - pex))) * len(acc):+.2f} standard errors); by temperature:")
    for lo_, hi_ in ((0.5, 2.1), (0.05, 0.5), (0.0, 0.05)):
        mk = (Tu >= lo_) & (Tu < hi_)
        say(f"      T in [{lo_:g}, {hi_:g}): accepted {acc[mk].mean():.4f}, expected {pex[mk].mean():.4f} ({mk.sum()} proposals)")
    ar = np.concatenate([o["aco_ranks"] for o in study])
    _, pa = aco_weights(NPOP, ACO_P["q"])
    oa = np.bincount(ar, minlength=NPOP) / len(ar)
    sa_ = np.sqrt(pa * (1 - pa) / len(ar))
    say(f"  ACO_R rank weights (q = {ACO_P['q']:g}, k = {NPOP}): p_1 = {pa[0]:.5f}, p_20 = {pa[-1]:.5f} in closed form; chosen")
    say(f"    over {len(ar)} ants {oa[0]:.5f} and {oa[-1]:.5f}; largest deviation {np.abs((oa - pa) / sa_).max():.2f} standard errors.")
    sig0 = R["aco"]["sig"][0]
    S0 = np.array(R["aco"]["F"].x)[R["aco"]["arch"][0]]
    brute = np.array([[ACO_P["xi"] * sum(abs(S0[e][c] - S0[l][c]) for e in range(NPOP)) / (NPOP - 1) for c in (0, 1)] for l in range(NPOP)])
    say(f"  ACO_R kernel widths: sigma_l recomputed term by term against the run's: {np.abs(brute - sig0).max():.1e}.")
    say("")
    say("THE IMPLEMENTATIONS ON TEXTBOOK TEST FUNCTIONS (the same settings, 400 evaluations, seeds 0 to 99)")
    for nm, txt in (("himmelblau", "Himmelblau, f = (x^2 + y - 11)^2 + (x + y^2 - 7)^2: four minima, f = 0 (textbook)"),
                    ("rastrigin", "Rastrigin, f = 20 + sum (x_i^2 - 10 cos 2 pi x_i): f = 0 at the origin (textbook), 81 local\n"
                                  "  minima in the square, the nearest four at f = 0.995 (a harder test at this budget)")):
        say(f"  {txt}")
        for k in KEYS:
            rs = [b[2][k] for b in bench if b[0] == nm]
            bfv = np.array([r[1] for r in rs])
            if nm == "himmelblau":
                dd = np.array([np.hypot(*(HIMMELBLAU_MIN - r[0]).T).min() for r in rs])
            else:
                dd = np.array([np.hypot(*r[0]) for r in rs])
            say(f"    {NAMES[k]:5s}: best f median {np.median(bfv):.1e}; within 0.05 of a textbook minimizer in {np.mean(dd < .05) * 100:.0f}% of seeds")
    # the page's own numbers
    exprs = ["BEST.map(b => b.slice(1))", "Array.from(BID[0]).concat(Array.from(BID[1]), Array.from(BID[2]), Array.from(BID[3]))",
             "SIG[0].flat()", "SIG[100].flat()", f"SIG[{len(R['aco']['arch']) - 1}].flat()",
             "Array.from(GPOP)", "Array.from(AARCH)", "Array.from(PPB)", "Array.from(SCUR)"]
    got = SM.check_page(NAME, exprs)
    e_best = 0.0
    e_bid = 0
    for j, k in enumerate(KEYS):
        v32 = np.array(R[k]["F"].v, dtype=np.float32).astype(float)
        e_best = max(e_best, np.abs(got[0][j] - np.minimum.accumulate(v32)).max())
        bid = np.zeros(NE + 1, int)
        for i in range(1, NE):
            bid[i + 1] = i if v32[i] < v32[bid[i]] else bid[i]
        e_bid = max(e_bid, int(np.abs(got[1][j * (NE + 1):(j + 1) * (NE + 1)] - bid).max()))
    last = len(R["aco"]["arch"]) - 1
    sig_py = [R["aco"]["sig"][0], R["aco"]["sig"][100]]
    # the archive after the last iteration has no recorded sigma: recompute it
    S_last = np.array(R["aco"]["F"].x)[R["aco"]["arch"][last]]
    sig_py.append(aco_sigma(S_last, ACO_P["xi"]))
    e_sig = max(np.abs(got[2 + i] - sig_py[i].ravel()).max() / np.abs(sig_py[i]).max() for i in range(3))
    a_sig = max(np.abs(got[2 + i] - sig_py[i].ravel()).max() for i in range(3))
    e_int = max(np.abs(got[5] - R["ga"]["pops"].ravel()).max(), np.abs(got[6] - R["aco"]["arch"].ravel()).max(),
                np.abs(got[7] - R["pso"]["pb"].ravel()).max(), np.abs(got[8] - R["sa"]["cur"]).max())
    say("")
    say("THE PAGE'S OWN NUMBERS (headless Chromium)")
    say(f"  Best so far curves of (e), computed in the page from the float32 values, against numpy on the same: {e_best:.1e}.")
    say(f"  The evaluation holding the best so far, after every n, all four: largest index difference {e_bid}.")
    say("  ACO_R kernel widths computed in the page (from float32 positions) against the run's, at iterations")
    say(f"  0, 100 and {last}: largest difference {a_sig:.1e} in x ({e_sig:.1e} of the largest width; float32 positions).")
    say(f"  The populations, archives, personal bests and walker positions the page decodes: largest difference {int(e_int)}.")
    per = t_of(NS_SLOTS - 1) - T0_RUN + 2.6 + 0.5 + 0.35
    moments = [0.3, 0.6, 0.9, 1.2] + [round(t_of(u), 3) for u in
                                      (-0.9, -0.5, -0.1, 0.3, 1.25, 1.55, 2.2, 3.35, 5.6, 8.4, 12.7, 16.3, 18.6, 19.0)]
    moments += [round(T0_RUN + per - x, 3) for x in (1.0, 0.6, 0.2)] + [round(T0_RUN + per + x, 3) for x in (0.1, 0.5)]
    ov = common.overlaps(NAME, moments)
    nl = sum(len(v["labels"]) for v in ov.values())
    nc = sum(len(v["crossings"]) for v in ov.values())
    say("")
    say("OVERLAP CHECK (engine.js ?overlap)")
    say(f"  The poster and {len(moments)} moments from 0.3 s to {max(moments):.1f} s (intro, run, rest, fade, restart): {nl} labels")
    say(f"  meeting, {nc} strokes through a label. common.still() also checks every 0.25 s up to the poster.")
    say(f"  Page {os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.html')) / 1024:.0f} KB, poster "
        f"{os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.webp')) / 1024:.0f} KB.")
    say("")
    say("DISPLAY")
    say("  One shared clock: in each slot every algorithm spends 20 more evaluations (GA: a generation, PSO: an")
    say("  iteration, SA: 20 proposals, ACO_R: 10 iterations of 2 ants), so at every moment all four have used")
    say("  the same budget, counted by n in (e). The first five slots take 1 s each, from the tenth on 0.5 s")
    say(f"  (a smooth step between): the run takes {t_of(NS_SLOTS - 1) - T0_RUN:.2f} s, rests 2.6 s, fades and starts again.")
    say("  Each curve in (e) is drawn up to its own algorithm's count (GA's children are evaluated one by one")
    say("  as they are born; PSO's swarm all at once on arrival), with the whole run faint behind it.")
    say(f"  Contours of f every 0.2 from {LEVELS[0]:g} to 0.1, then 0.4, 0.7, 1.0 ({B['npts']} points after Douglas-Peucker")
    say("  simplification within 0.003, about 0.1 drawing units). Kernels in (d) are 1 sigma ellipses, darker for")
    say("  higher rank weight; the GA's links join each child to its two parents; a dotted segment is a mutation.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_opt_global.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    validate(build())
