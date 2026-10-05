"""Figure 6 of the signal processing document: finite element model updating,
a nonlinear inverse problem, solved five ways.

The professor's animation (model-updating-solvers-animation.html, "Solving a
nonlinear inverse problem: model updating") redrawn as one numfig page.

Model (his). A two-storey shear building: floor masses m = 100 t each, storey
stiffnesses k1 (ground storey) and k2 (top storey) unknown, between 20 and
220 MN/m. The true building has (k1, k2) = (120, 80) MN/m. Measured: its two
natural frequencies, 0.3% high and 0.4% low (f1 = 3.193 Hz, f2 = 7.766 Hz),
and, if the reader adds it, the first mode's ratio phi2/phi1, 2% high. The
misfit is Phi = sum of squared residuals, each scaled by its standard
deviation (0.3% for a frequency, 5% for the ratio), plus, if the reader adds
the prior, ((k - 100)/35)^2 for each storey (design values 100 MN/m, 35%).

The 2 x 2 eigenproblem is solved in closed form: with T = k1 + 2 k2 and
R = sqrt(k1^2 + 4 k2^2), the eigenvalues of M^-1 K are (10^6/m)(T -+ R)/2,
and phi2/phi1 = (k1 + R)/(2 k2). The two frequencies fix the trace
k1 + 2 k2 and the determinant k1 k2 of M^-1 K (in units of 10^6/m), and the
swap (k1, k2) -> (2 k2, k1/2) keeps both: every building has a twin with the
same two frequencies, mirrored across the fold line k1 = 2 k2 (the swap's
fixed points, where the Jacobian of (T, k1 k2), k1 - 2 k2, vanishes).

Solvers (his, with the eigenvalue sensitivities in closed form in place of
his finite differences): gradient descent with a backtracking line search,
Gauss-Newton, Levenberg-Marquardt (Marquardt's diagonal scaling), particle
swarm (28 particles, 70 iterations) and Metropolis MCMC (4 chains, 150 + 4,000
steps). The page runs them itself (the reader may click any start on the
map), in double precision with mulberry32 seeded by the start point; this
script's port of the same code checks the page's numbers (check file).

Run: /root/venv312/bin/python tools/numfig/sp_inv_update.py [--look]
(writes the page, the still and the check file; prints the key numbers; needs
contourpy and Playwright, both in that environment).
"""
import base64
import contextlib
import math
import os
import shutil
import sys
import tempfile
import threading
import time

import numpy as np

import common

NAME = "sp-inv-update"
HERE = os.path.dirname(os.path.abspath(__file__))

MASS = 1e5                              # kg, each floor
LO, HI = 20.0, 220.0                    # MN/m, the search box
TRUE = (120.0, 80.0)                    # MN/m, the building that made the data
NOISE = (0.003, -0.004, 0.02)           # relative errors of f1, f2, phi2/phi1 in the data
SF, SR, SP, KP = 0.003, 0.05, 0.35, 100.0
STARTS = [(210.0, 30.0), (40.0, 200.0), (100.0, 40.0), (150.0, 200.0)]
VARIANTS = [(False, False), (True, False), (False, True), (True, True)]   # (mode shape, prior)
VNAME = ["frequencies only", "with the mode shape", "with the prior", "with both"]
LEVELS = np.arange(-1.0, 4.75, 0.5)     # log10 Phi of the band edges in the map
SOLVERS = ["gd", "gn", "lm", "pso", "mcmc"]
SNAME = {"gd": "gradient descent", "gn": "Gauss-Newton", "lm": "Levenberg-Marquardt",
         "pso": "particle swarm", "mcmc": "MCMC sampling"}
BURN, KEEP, PSD = 150, 4000, 5.0        # MCMC: burn-in, kept steps, proposal sd (MN/m)
NPART, NITER = 28, 70                   # particle swarm
TWO_PI = 2 * math.pi
S = 1e6 / MASS                          # 1/s^2 per MN/m


# ------------------------------------------------------------------ the model (plain floats:
# the port of the page's own code, operation for operation)
def modal(k1, k2):
    R = math.sqrt(k1 * k1 + 4 * k2 * k2)
    T = k1 + 2 * k2
    mu2 = (T + R) / 2
    mu1 = 2 * k1 * k2 / (T + R)
    return (math.sqrt(S * mu1) / TWO_PI, math.sqrt(S * mu2) / TWO_PI, (k1 + R) / (2 * k2), mu1, mu2, R)


_MT = modal(*TRUE)
DF1, DF2, DR = _MT[0] * (1 + NOISE[0]), _MT[1] * (1 + NOISE[1]), _MT[2] * (1 + NOISE[2])


class Model:
    """Residuals (and their Jacobian) of one variant; counts forward runs."""

    def __init__(self, mode=False, prior=False):
        self.mode, self.prior, self.evals = mode, prior, 0

    def resid(self, k1, k2, jac=False):
        self.evals += 1
        f1, f2, r, mu1, mu2, R = modal(k1, k2)
        e = [(f1 - DF1) / DF1 / SF, (f2 - DF2) / DF2 / SF]
        if self.mode:
            e.append((r - DR) / DR / SR)
        if self.prior:
            e.append((k1 - KP) / KP / SP)
            e.append((k2 - KP) / KP / SP)
        if not jac:
            return e
        # eigenvalue sensitivities (Fox and Kapoor): dmu/dk = phi^T (dK/dk) phi / phi^T phi
        a1 = k1 / R
        a2 = 4 * k2 / R
        c1 = f1 / (2 * mu1) / DF1 / SF
        c2 = f2 / (2 * mu2) / DF2 / SF
        J = [[c1 * ((1 - a1) / 2), c1 * (1 - a2 / 2)], [c2 * ((1 + a1) / 2), c2 * (1 + a2 / 2)]]
        if self.mode:
            cr = 1 / DR / SR
            J.append([cr * (1 + a1) / (2 * k2), cr * (2 / R - r / k2)])
        if self.prior:
            J.append([1 / KP / SP, 0.0])
            J.append([0.0, 1 / KP / SP])
        return e, J


def phi_of(e):
    s = 0.0
    for v in e:
        s += v * v
    return s


def clamp_t(a, b):
    return (max(LO, min(HI, a)), max(LO, min(HI, b)))


def normal_eq(J, e):
    a = b = c = g0 = g1 = 0.0
    for k in range(len(J)):
        a += J[k][0] * J[k][0]
        b += J[k][0] * J[k][1]
        c += J[k][1] * J[k][1]
        g0 += J[k][0] * e[k]
        g1 += J[k][1] * e[k]
    return a, b, c, g0, g1


def solve2(a, b, c, r0, r1):
    det = a * c - b * b
    if abs(det) < 1e-300:
        return None
    return ((c * r0 - b * r1) / det, (a * r1 - b * r0) / det)


def dist(p, q):
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return math.sqrt(dx * dx + dy * dy)


def run_local(kind, model, start):
    """Gradient descent (backtracking line search), Gauss-Newton or
    Levenberg-Marquardt from `start`, as his animation runs them."""
    maxit = {"gd": 400, "gn": 60, "lm": 80}[kind]
    t = clamp_t(*start)
    e, J = model.resid(t[0], t[1], jac=True)
    phi = phi_of(e)
    path, hist, evals = [t], [phi], [model.evals]
    it, step, mu = 0, 1.0, None
    while True:
        a, b, c, g0, g1 = normal_eq(J, e)
        if kind == "gd":
            G0, G1 = 2 * g0, 2 * g1
            gg = G0 * G0 + G1 * G1
            s = min(step * 2, 1e6)
            for _ in range(40):
                nt = clamp_t(t[0] - s * G0, t[1] - s * G1)
                nf = phi_of(model.resid(nt[0], nt[1]))
                if nf <= phi - 1e-4 * s * gg:
                    break
                s /= 2
            step = s
            moved = dist(nt, t)
            if nf < phi:
                t = nt
                e, J = model.resid(t[0], t[1], jac=True)
                phi = phi_of(e)
            it += 1
            path.append(t); hist.append(phi); evals.append(model.evals)
            if moved < 1e-3 or it >= maxit:
                break
        elif kind == "gn":
            d = solve2(a, b, c, -g0, -g1)
            if d is None:
                break
            nt = clamp_t(t[0] + d[0], t[1] + d[1])
            mv = dist(nt, t)
            t = nt
            e, J = model.resid(t[0], t[1], jac=True)
            phi = phi_of(e)
            it += 1
            path.append(t); hist.append(phi); evals.append(model.evals)
            if mv < 1e-3 or it >= maxit:
                break
        else:
            if mu is None:
                mu = 1e-2 * max(a, c)
            acc, mv = False, 0.0
            for _ in range(20):
                d = solve2(a * (1 + mu), b, c * (1 + mu), -g0, -g1)
                if d is not None:
                    nt = clamp_t(t[0] + d[0], t[1] + d[1])
                    nf = phi_of(model.resid(nt[0], nt[1]))
                    if nf < phi:
                        acc = True
                        break
                mu *= 3
            if acc:
                mv = dist(nt, t)
                t = nt
                e, J = model.resid(t[0], t[1], jac=True)
                phi = phi_of(e)
                mu = max(mu / 4, 1e-12)
            it += 1
            path.append(t); hist.append(phi); evals.append(model.evals)
            if (not acc) or mv < 1e-3 or it >= maxit:
                break
    return dict(kind=kind, path=path, hist=hist, evals=evals, it=it)


def mulberry32(seed):
    """mulberry32, bit for bit as JavaScript computes it."""
    st = [seed & 0xFFFFFFFF]

    def imul(x, y):
        return ((x & 0xFFFFFFFF) * (y & 0xFFFFFFFF)) & 0xFFFFFFFF

    def rnd():
        a = (st[0] + 0x6D2B79F5) & 0xFFFFFFFF
        st[0] = a
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rnd


def seed_of(start):
    """The random seed of a run: 1000 round(k1) + round(k2) of its start."""
    return 1000 * math.floor(start[0] + 0.5) + math.floor(start[1] + 0.5)


def run_pso(model, start, seed=None):
    rnd = mulberry32(seed_of(start) if seed is None else seed)
    P, gbest, gphi = [], None, math.inf
    for _ in range(NPART):
        x = [LO + (HI - LO) * rnd(), LO + (HI - LO) * rnd()]
        v = [(rnd() - 0.5) * 40, (rnd() - 0.5) * 40]
        f = phi_of(model.resid(x[0], x[1]))
        P.append(dict(x=x, v=v, b=list(x), bf=f))
        if f < gphi:
            gphi, gbest = f, list(x)
    path, hist, evals = [tuple(gbest)], [gphi], [model.evals]
    swarm = [[c for o in P for c in o["x"]]]
    for _ in range(NITER):
        for o in P:
            for dd in range(2):
                vv = 0.68 * o["v"][dd] + 1.5 * rnd() * (o["b"][dd] - o["x"][dd])
                vv = vv + 1.5 * rnd() * (gbest[dd] - o["x"][dd])
                o["v"][dd] = max(-40.0, min(40.0, vv))
            o["x"] = list(clamp_t(o["x"][0] + o["v"][0], o["x"][1] + o["v"][1]))
            f = phi_of(model.resid(o["x"][0], o["x"][1]))
            if f < o["bf"]:
                o["bf"], o["b"] = f, list(o["x"])
            if f < gphi:
                gphi, gbest = f, list(o["x"])
        path.append(tuple(gbest)); hist.append(gphi); evals.append(model.evals)
        swarm.append([c for o in P for c in o["x"]])
    return dict(kind="pso", path=path, hist=hist, evals=evals, it=NITER, swarm=swarm)


def run_mcmc(model, start, seed=None):
    rnd = mulberry32(seed_of(start) if seed is None else seed)

    def randn():
        u = max(rnd(), 1e-12)
        v = rnd()
        return math.sqrt(-2 * math.log(u)) * math.cos(TWO_PI * v)
    chains = [dict(x=tuple(s), f=0.0) for s in (tuple(start), (40.0, 200.0), (200.0, 40.0), (60.0, 60.0))]
    for c in chains:
        c["f"] = phi_of(model.resid(*c["x"]))
    trace = [[q for c in chains for q in c["x"]]]
    acc = [0, 0, 0, 0]
    for _ in range(BURN + KEEP):
        for j, c in enumerate(chains):
            y = (c["x"][0] + PSD * randn(), c["x"][1] + PSD * randn())
            if y[0] < LO or y[0] > HI or y[1] < LO or y[1] > HI:
                continue
            fy = phi_of(model.resid(y[0], y[1]))
            if math.log(rnd() + 1e-300) < -(fy - c["f"]) / 2:
                c["x"], c["f"] = y, fy
                acc[j] += 1
        trace.append([q for c in chains for q in c["x"]])
    samples = [(row[2 * c], row[2 * c + 1]) for row in trace[BURN + 1:] for c in range(4)]
    true_side = sum(1 for q in samples if q[0] < 2 * q[1]) / len(samples)
    return dict(kind="mcmc", trace=trace, samples=samples, acc=acc, evals=model.evals, n=BURN + KEEP,
                share=true_side)


def run(kind, start, variant):
    m = Model(*VARIANTS[variant])
    if kind == "pso":
        return run_pso(m, start)
    if kind == "mcmc":
        return run_mcmc(m, start)
    return run_local(kind, m, start)


# ------------------------------------------------------------------ the same, vectorized
def modal_v(k1, k2):
    R = np.sqrt(k1 * k1 + 4 * k2 * k2)
    T = k1 + 2 * k2
    mu2 = (T + R) / 2
    mu1 = 2 * k1 * k2 / (T + R)
    return np.sqrt(S * mu1) / TWO_PI, np.sqrt(S * mu2) / TWO_PI, (k1 + R) / (2 * k2)


def phi_v(k1, k2, variant):
    mode, prior = VARIANTS[variant]
    f1, f2, r = modal_v(k1, k2)
    p = ((f1 - DF1) / DF1 / SF) ** 2 + ((f2 - DF2) / DF2 / SF) ** 2
    if mode:
        p = p + ((r - DR) / DR / SR) ** 2
    if prior:
        p = p + ((k1 - KP) / KP / SP) ** 2 + ((k2 - KP) / KP / SP) ** 2
    return p


def exact_fits():
    """The two pairs that reproduce the measured frequencies exactly: k1 + 2 k2 = L1 + L2
    and k1 k2 = L1 L2, with L = (2 pi f)^2 m / 10^6, so 2 k2^2 - (L1 + L2) k2 + L1 L2 = 0."""
    L1 = (TWO_PI * DF1) ** 2 * MASS * 1e-6
    L2 = (TWO_PI * DF2) ** 2 * MASS * 1e-6
    tr, det = L1 + L2, L1 * L2
    sq = math.sqrt(tr * tr - 8 * det)
    pairs = [(tr - 2 * k2, k2) for k2 in ((tr + sq) / 4, (tr - sq) / 4)]
    return pairs[0], pairs[1], (L1, L2, tr, det)


# ------------------------------------------------------------------ the map: exact filled contours
def _dp(pts, tol):
    """Douglas-Peucker simplification of a polyline."""
    n = len(pts)
    if n < 4:
        return pts
    keep = np.zeros(n, bool)
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        a, b = pts[i], pts[j]
        ab = b - a
        L = math.hypot(ab[0], ab[1])
        seg = pts[i + 1:j] - a
        d = np.hypot(seg[:, 0], seg[:, 1]) if L < 1e-12 else np.abs(seg[:, 0] * ab[1] - seg[:, 1] * ab[0]) / L
        k = int(np.argmax(d))
        if d[k] > tol:
            keep[i + 1 + k] = True
            stack.append((i, i + 1 + k))
            stack.append((i + 1 + k, j))
    return pts[keep]


def contours(variant, n=2401, tol=0.02):
    """For each level c of LEVELS, the region {log10 Phi < c} as closed rings
    (outer boundaries and holes), from a marching-squares contour of the exact
    closed form on an n x n grid over the box, simplified to `tol` MN/m."""
    import contourpy
    k = np.linspace(LO, HI, n)
    K1, K2 = np.meshgrid(k, k)
    Z = np.log10(phi_v(K1, K2, variant))
    gen = contourpy.contour_generator(k, k, Z, fill_type=contourpy.FillType.OuterOffset)
    out = []
    for c in LEVELS:
        rings = []
        pts_list, offs_list = gen.filled(-1e9, c)
        for p, o in zip(pts_list, offs_list):
            for a, b in zip(o[:-1], o[1:]):
                ring = p[a:b]
                if len(ring) > 3:
                    rings.append(_dp(ring[:-1] if np.allclose(ring[0], ring[-1]) else ring, tol))
        out.append(rings)
    return out


def encode_map(levels):
    """Rings as one base64 array of uint16 coordinates (0..65535 across the box)
    and their vertex counts per level."""
    counts, q = [], []
    for rings in levels:
        counts.append([len(r) for r in rings])
        for r in rings:
            q.append(np.round((r - LO) / (HI - LO) * 65535).astype("<u2").ravel())
    arr = np.concatenate(q) if q else np.zeros(0, "<u2")
    return {"n": counts, "q": base64.b64encode(arr.astype("<u2").tobytes()).decode("ascii")}


def decode_map(m):
    arr = np.frombuffer(base64.b64decode(m["q"]), "<u2").astype(float) / 65535 * (HI - LO) + LO
    out, i = [], 0
    for cnt in m["n"]:
        rings = []
        for c in cnt:
            rings.append(arr[i:i + 2 * c].reshape(-1, 2))
            i += 2 * c
        out.append(rings)
    return out


# ------------------------------------------------------------------ the exact posterior
PK1 = np.round(np.arange(100.0, 180.0 + 1e-9, 0.25), 2)   # k1 grid of the marginal drawn in (b)


def posterior(variant, nk2=20001, nk1=2001):
    """p(k1 | d) with a uniform prior on the box (times the prior term where
    the variant has it), likelihood exp(-Phi/2): Simpson's rule in k2 at
    0.01 MN/m and in k1 at 0.1 MN/m for the normalisation; returns the
    marginal on PK1 and the share of the posterior on the true side of the
    fold (k1 < 2 k2), the last from a 4,000 x 4,000 midpoint grid."""
    k2 = np.linspace(LO, HI, nk2)
    w2 = np.ones(nk2); w2[1:-1:2] = 4; w2[2:-1:2] = 2; w2 *= (k2[1] - k2[0]) / 3
    pmin = phi_v(np.array([123.6]), np.array([77.5]), variant)[0]

    def marg(k1s):
        out = np.empty(len(k1s))
        for i0 in range(0, len(k1s), 64):
            K1 = k1s[i0:i0 + 64, None]
            out[i0:i0 + 64] = (np.exp(-(phi_v(K1, k2[None, :], variant) - pmin) / 2) * w2).sum(axis=1)
        return out
    k1 = np.linspace(LO, HI, nk1)
    w1 = np.ones(nk1); w1[1:-1:2] = 4; w1[2:-1:2] = 2; w1 *= (k1[1] - k1[0]) / 3
    Z = (marg(k1) * w1).sum()
    N = 4000
    kk = LO + (HI - LO) * (np.arange(N) + 0.5) / N
    split = 0.0; tot = 0.0
    for i0 in range(0, N, 500):
        A, B = np.meshgrid(kk, kk[i0:i0 + 500])
        w = np.exp(-(phi_v(A, B, variant) - pmin) / 2)
        split += w[A < 2 * B].sum(); tot += w.sum()
    return marg(PK1) / Z, split / tot


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
/* ================================================================ the model
   His two-storey shear building: floors of m = 100 t, storey stiffnesses k1
   (ground) and k2 (top) in MN/m. The 2 x 2 eigenproblem in closed form:
   mu = (T -+ R)/2, T = k1 + 2 k2, R = sqrt(k1^2 + 4 k2^2), with lambda =
   (10^6/m) mu, the smaller root as 2 k1 k2/(T + R); phi2/phi1 = (k1 + R)/(2 k2).
   The same code, operation for operation, as sp_inv_update.py's port, which
   checks this page's numbers. */
const LO = D.lo, HI = D.hi, S = 1e6 / D.mass, TWO_PI = 2 * Math.PI;
const SF = D.sf, SR = D.sr, SPR = D.sp, KP = D.kp;
let NEV = 0;                               // forward runs of the run being computed
function modal(k1, k2) {
  const R = Math.sqrt(k1 * k1 + 4 * k2 * k2), T = k1 + 2 * k2;
  const mu2 = (T + R) / 2, mu1 = 2 * k1 * k2 / (T + R);
  return [Math.sqrt(S * mu1) / TWO_PI, Math.sqrt(S * mu2) / TWO_PI, (k1 + R) / (2 * k2), mu1, mu2, R];
}
const MT = modal(D.truek[0], D.truek[1]);
const DF1 = MT[0] * (1 + D.noise[0]), DF2 = MT[1] * (1 + D.noise[1]), DR = MT[2] * (1 + D.noise[2]);
function resid(k1, k2, o, jac) {
  NEV++;
  const q = modal(k1, k2), f1 = q[0], f2 = q[1], r = q[2], mu1 = q[3], mu2 = q[4], R = q[5];
  const e = [(f1 - DF1) / DF1 / SF, (f2 - DF2) / DF2 / SF];
  if (o.mode) e.push((r - DR) / DR / SR);
  if (o.prior) { e.push((k1 - KP) / KP / SPR); e.push((k2 - KP) / KP / SPR); }
  if (!jac) return e;
  // eigenvalue sensitivities (Fox and Kapoor), in closed form
  const a1 = k1 / R, a2 = 4 * k2 / R;
  const c1 = f1 / (2 * mu1) / DF1 / SF, c2 = f2 / (2 * mu2) / DF2 / SF;
  const J = [[c1 * ((1 - a1) / 2), c1 * (1 - a2 / 2)], [c2 * ((1 + a1) / 2), c2 * (1 + a2 / 2)]];
  if (o.mode) { const cr = 1 / DR / SR; J.push([cr * (1 + a1) / (2 * k2), cr * (2 / R - r / k2)]); }
  if (o.prior) { J.push([1 / KP / SPR, 0]); J.push([0, 1 / KP / SPR]); }
  return [e, J];
}
function phiOf(e) { let s = 0; for (let k = 0; k < e.length; k++) s += e[k] * e[k]; return s; }
const clampT = (a, b) => [Math.max(LO, Math.min(HI, a)), Math.max(LO, Math.min(HI, b))];
function normalEq(J, e) {
  let a = 0, b = 0, c = 0, g0 = 0, g1 = 0;
  for (let k = 0; k < J.length; k++) {
    a += J[k][0] * J[k][0]; b += J[k][0] * J[k][1]; c += J[k][1] * J[k][1];
    g0 += J[k][0] * e[k]; g1 += J[k][1] * e[k];
  }
  return [a, b, c, g0, g1];
}
function solve2(a, b, c, r0, r1) { const det = a * c - b * b; if (Math.abs(det) < 1e-300) return null; return [(c * r0 - b * r1) / det, (a * r1 - b * r0) / det]; }
function dist(p, q) { const dx = p[0] - q[0], dy = p[1] - q[1]; return Math.sqrt(dx * dx + dy * dy); }

/* ================================================================ the solvers (his) */
function runLocal(kind, start, o) {
  const maxit = kind === 'gd' ? 400 : kind === 'gn' ? 60 : 80;
  NEV = 0;
  let t = clampT(start[0], start[1]), ej = resid(t[0], t[1], o, true), e = ej[0], J = ej[1], phi = phiOf(e);
  const path = [t], hist = [phi], evals = [NEV];
  let it = 0, step = 1, mu = null;
  for (;;) {
    const ne = normalEq(J, e), a = ne[0], b = ne[1], c = ne[2], g0 = ne[3], g1 = ne[4];
    if (kind === 'gd') {
      const G0 = 2 * g0, G1 = 2 * g1, gg = G0 * G0 + G1 * G1;
      let s = Math.min(step * 2, 1e6), nt, nf;
      for (let k = 0; k < 40; k++) {
        nt = clampT(t[0] - s * G0, t[1] - s * G1); nf = phiOf(resid(nt[0], nt[1], o));
        if (nf <= phi - 1e-4 * s * gg) break;
        s /= 2;
      }
      step = s;
      const moved = dist(nt, t);
      if (nf < phi) { t = nt; ej = resid(t[0], t[1], o, true); e = ej[0]; J = ej[1]; phi = phiOf(e); }
      it++; path.push(t); hist.push(phi); evals.push(NEV);
      if (moved < 1e-3 || it >= maxit) break;
    } else if (kind === 'gn') {
      const d = solve2(a, b, c, -g0, -g1);
      if (!d) break;
      const nt = clampT(t[0] + d[0], t[1] + d[1]), mv = dist(nt, t);
      t = nt; ej = resid(t[0], t[1], o, true); e = ej[0]; J = ej[1]; phi = phiOf(e);
      it++; path.push(t); hist.push(phi); evals.push(NEV);
      if (mv < 1e-3 || it >= maxit) break;
    } else {
      if (mu === null) mu = 1e-2 * Math.max(a, c);
      let acc = false, mv = 0, nt, nf;
      for (let k = 0; k < 20; k++) {
        const d = solve2(a * (1 + mu), b, c * (1 + mu), -g0, -g1);
        if (d) { nt = clampT(t[0] + d[0], t[1] + d[1]); nf = phiOf(resid(nt[0], nt[1], o)); if (nf < phi) { acc = true; break; } }
        mu *= 3;
      }
      if (acc) { mv = dist(nt, t); t = nt; ej = resid(t[0], t[1], o, true); e = ej[0]; J = ej[1]; phi = phiOf(e); mu = Math.max(mu / 4, 1e-12); }
      it++; path.push(t); hist.push(phi); evals.push(NEV);
      if (!acc || mv < 1e-3 || it >= maxit) break;
    }
  }
  return {kind, path, hist, evals, it};
}
function mulberry32(a) {
  return function () {
    a |= 0; a = a + 0x6D2B79F5 | 0;
    let t = Math.imul(a ^ a >>> 15, 1 | a);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  };
}
const seedOf = s => 1000 * Math.floor(s[0] + .5) + Math.floor(s[1] + .5);
function runPso(start, o) {
  const rnd = mulberry32(seedOf(start)), P = [];
  NEV = 0;
  let gbest = null, gphi = Infinity;
  for (let p = 0; p < D.npart; p++) {
    const x = [LO + (HI - LO) * rnd(), LO + (HI - LO) * rnd()], v = [(rnd() - .5) * 40, (rnd() - .5) * 40];
    const f = phiOf(resid(x[0], x[1], o));
    P.push({x, v, b: x.slice(), bf: f});
    if (f < gphi) { gphi = f; gbest = x.slice(); }
  }
  const path = [gbest.slice()], hist = [gphi], evals = [NEV], swarm = [P.flatMap(q => q.x)];
  for (let it = 0; it < D.niter; it++) {
    for (const q of P) {
      for (let dd = 0; dd < 2; dd++) {
        let vv = .68 * q.v[dd] + 1.5 * rnd() * (q.b[dd] - q.x[dd]);
        vv = vv + 1.5 * rnd() * (gbest[dd] - q.x[dd]);
        q.v[dd] = Math.max(-40, Math.min(40, vv));
      }
      q.x = clampT(q.x[0] + q.v[0], q.x[1] + q.v[1]);
      const f = phiOf(resid(q.x[0], q.x[1], o));
      if (f < q.bf) { q.bf = f; q.b = q.x.slice(); }
      if (f < gphi) { gphi = f; gbest = q.x.slice(); }
    }
    path.push(gbest.slice()); hist.push(gphi); evals.push(NEV); swarm.push(P.flatMap(q => q.x));
  }
  return {kind: 'pso', path, hist, evals, it: D.niter, swarm};
}
function runMcmc(start, o) {
  const rnd = mulberry32(seedOf(start));
  const randn = () => { const u = Math.max(rnd(), 1e-12), v = rnd(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TWO_PI * v); };
  NEV = 0;
  const ch = [start.slice(), [40, 200], [200, 40], [60, 60]].map(x => ({x, f: 0}));
  for (const c of ch) c.f = phiOf(resid(c.x[0], c.x[1], o));
  const n = D.burn + D.keep, tr = new Float64Array((n + 1) * 8), acc = [0, 0, 0, 0];
  const put = j => ch.forEach((c, i) => { tr[j * 8 + 2 * i] = c.x[0]; tr[j * 8 + 2 * i + 1] = c.x[1]; });
  put(0);
  let side = 0;
  for (let it = 1; it <= n; it++) {
    ch.forEach((c, i) => {
      const y = [c.x[0] + D.psd * randn(), c.x[1] + D.psd * randn()];
      if (y[0] < LO || y[0] > HI || y[1] < LO || y[1] > HI) return;
      const fy = phiOf(resid(y[0], y[1], o));
      if (Math.log(rnd() + 1e-300) < -(fy - c.f) / 2) { c.x = y; c.f = fy; acc[i]++; }
    });
    put(it);
    if (it > D.burn) for (const c of ch) if (c.x[0] < 2 * c.x[1]) side++;
  }
  return {kind: 'mcmc', trace: tr, n, acc, evals: NEV, share: side / (4 * D.keep)};
}
/* for the check file: one run as plain numbers */
function __solve(kind, k1, k2, mode, prior) {
  const o = {mode: !!mode, prior: !!prior}, s = [k1, k2];
  const r = kind === 'pso' ? runPso(s, o) : kind === 'mcmc' ? runMcmc(s, o) : runLocal(kind, s, o);
  if (kind === 'mcmc') return {trace: Array.from(r.trace), acc: r.acc, evals: r.evals, share: r.share};
  return {path: r.path, hist: r.hist, evals: r.evals, it: r.it, swarm: r.swarm || null};
}

/* ================================================================ runs, scenes, the tour */
const SOLVERS = ['gd', 'gn', 'lm', 'pso', 'mcmc'];
const SNAME = {gd: 'gradient descent', gn: 'Gauss-Newton', lm: 'Levenberg-Marquardt', pso: 'particle swarm', mcmc: 'MCMC sampling'};
const RUNS = new Map();
function getRun(kind, start, mode, prior) {
  const key = kind + '|' + start[0] + '|' + start[1] + '|' + (mode ? 1 : 0) + (prior ? 1 : 0);
  let r = RUNS.get(key);
  if (!r) {
    const o = {mode: !!mode, prior: !!prior};
    r = kind === 'pso' ? runPso(start, o) : kind === 'mcmc' ? runMcmc(start, o) : runLocal(kind, start, o);
    RUNS.set(key, r);
  }
  return r;
}
const runOf = (sc, kind) => getRun(kind || sc.solver, sc.start, sc.mode, sc.prior);
/* time on screen: one iteration every PACE seconds; MCMC at RATE steps a second */
const PACE = {gd: .024, gn: .45, lm: .40, pso: .10}, RATE = 1500;
const dur = r => r.kind === 'mcmc' ? r.n / RATE : r.it * PACE[r.kind];
function prog(r, u) {                      // where a run is, u seconds after it started
  if (r.kind === 'mcmc') { const n = u <= 0 ? 0 : Math.min(r.n, Math.floor(u * RATE)); return {k: n, s: 0, done: n >= r.n}; }
  if (u <= 0) return {k: 0, s: 0, done: false};
  const st = PACE[r.kind], k = Math.floor(u / st);
  return k >= r.it ? {k: r.it, s: 0, done: true} : {k, s: (u - k * st) / st, done: false};
}
const variant = sc => (sc.mode ? 1 : 0) + (sc.prior ? 2 : 0);
/* the tour, when the reader has chosen nothing: his default (Levenberg-Marquardt from
   (210, 30)), the other solvers, then the mode shape and the prior added */
const TOUR = [['lm', 0, 0], ['gn', 0, 0], ['gd', 0, 0], ['pso', 0, 0], ['mcmc', 0, 0],
              ['mcmc', 1, 0], ['lm', 1, 0], ['lm', 0, 1], ['mcmc', 0, 1]];
const T_START = .1, PRE_NEW = .5, PRE_SAME = .25, HOLD = 1.6, HOLD_MC = 2.2;
let SCHED = null;
function schedule() {
  if (SCHED) return SCHED;
  const steps = []; let off = 0;
  TOUR.forEach(([kind, m, p], j) => {
    const sc = {solver: kind, si: 0, start: D.starts[0], mode: m, prior: p};
    const q = TOUR[(j + TOUR.length - 1) % TOUR.length];
    const pre = j === 0 || q[1] !== m || q[2] !== p ? PRE_NEW : PRE_SAME, d = dur(runOf(sc));
    const len = pre + d + (kind === 'mcmc' ? HOLD_MC : HOLD);
    steps.push({sc, off, pre, d, len}); off += len;
  });
  return SCHED = {steps, period: off};
}
function tourScene(time) {
  const Sd = schedule(), N = Sd.steps.length;
  if (time < T_START) return {...Sd.steps[0].sc, t0: T_START, pre: Sd.steps[0].pre, prev: null, tour: 0};
  const c = Math.floor((time - T_START) / Sd.period), tau = time - T_START - c * Sd.period;
  let j = 0; while (j + 1 < N && Sd.steps[j + 1].off <= tau) j++;
  const st = Sd.steps[j], prev = c === 0 && j === 0 ? null : {...Sd.steps[(j + N - 1) % N].sc, u: 1e9};
  return {...st.sc, t0: T_START + c * Sd.period + st.off, pre: st.pre, prev, tour: j};
}
let PICK = null;                           // the reader's scene, once chosen
const scene = () => PICK || tourScene(t);

/* ================================================================ layout */
const MX = 92, MY = 146, MS = 420;         // (a): the map's plot square
const KX = k => MX + (k - LO) / (HI - LO) * MS, KY = k => MY + MS - (k - LO) / (HI - LO) * MS;
const CBX = MX + MS + 16, CBW = 12;        // the colour bar
const RX = 616, RX1 = 980;                 // the right column
const BX = 690, BY = 146, BW = 290, BH = 176;   // (b)
const TY = 404;                            // the table's top rule
const ROW1 = 10, ROW2 = 52, CHH = 30;      // the chip rows
const LEV = D.levels, NL = LEV.length;
/* the bands of the map: SEQ (white to navy) from high misfit to low */
const BAND = LEV.map((_, j) => seq(lerp(.70, .05, j / (NL - 1))));
const lab = t0 => settle(t0, .28), rise = s => 5 * (1 - s);
function tw(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
let LAY = null;
function layout() {                         // the chips, measured once the type has loaded
  if (LAY) return LAY;
  const L = {solver: [], start: [], opt: []};
  let x = 98;
  for (const s of SOLVERS) { const w = Math.round(tw(SNAME[s], 15) + 26); L.solver.push({x, y: ROW1, w, h: CHH}); x += w + 8; }
  x = 98;
  for (const s of D.starts) { const w = Math.round(tw('(' + s[0] + ', ' + s[1] + ')', 15) + 26); L.start.push({x, y: ROW2, w, h: CHH}); x += w + 8; }
  x += 40;
  L.add = x - 10;
  for (const s of ['mode shape', 'prior']) { const w = Math.round(tw(s, 15) + 26); L.opt.push({x, y: ROW2, w, h: CHH}); x += w + 8; }
  return LAY = L;
}

/* ================================================================ the map, drawn once per size */
function b64u16(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new Uint16Array(u.buffer); }
const MAPS = D.maps.map(m => {
  const q = b64u16(m.q), out = []; let i = 0;
  for (const cnt of m.n) {
    const rings = [];
    for (const c of cnt) { const r = new Float64Array(2 * c); for (let j = 0; j < 2 * c; j++) r[j] = LO + q[i++] / 65535 * (HI - LO); rings.push(r); }
    out.push(rings);
  }
  return out;
});
const OFF = {};
function mapImage(v) {
  const px = Math.max(8, Math.round(MS * cv.width / W)), key = v + ':' + px;
  if (OFF[key]) return OFF[key];
  for (const k in OFF) if (!k.endsWith(':' + px)) delete OFF[k];
  const c = document.createElement('canvas'); c.width = c.height = px;
  const g = c.getContext('2d'), f = px / (HI - LO);
  g.fillStyle = '#fff'; g.fillRect(0, 0, px, px);
  for (let j = NL - 1; j >= 0; j--) {
    g.beginPath();
    for (const r of MAPS[v][j]) {
      for (let i = 0; i < r.length; i += 2) { const x = (r[i] - LO) * f, y = px - (r[i + 1] - LO) * f; i ? g.lineTo(x, y) : g.moveTo(x, y); }
      g.closePath();
    }
    g.fillStyle = BAND[j]; g.fill('evenodd');
  }
  return OFF[key] = c;
}

/* ================================================================ drawing the runs */
const CASE = 4.4;                          // white casing under a path
function pathLine(pts, a, width = 2.2) {
  if (pts.length < 2) return;
  line(pts, {color: '#fff', width: CASE, alpha: a});
  line(pts, {color: C.accent, width, alpha: a});
}
function marker(x, y, a, r = 6) { dot(x, y, r, {color: '#fff', fill: C.accent, width: 1.8, alpha: a}); }
function startRing(s, a) {
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = C.accent; ctx.lineWidth = 1.6; ctx.setLineDash([3, 3]);
  ctx.beginPath(); ctx.arc(KX(s[0]), KY(s[1]), 9.5, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
}
function drawLocal(sc, r, u, a) {
  const p = prog(r, u), P = r.path, run0 = sc.t0 + sc.pre;
  const pts = []; for (let j = 0; j <= p.k; j++) pts.push([KX(P[j][0]), KY(P[j][1])]);
  let cur = pts[pts.length - 1];
  if (!p.done && u > 0) {
    const g = r.kind === 'gd' ? p.s : settle(run0 + p.k * PACE[r.kind], .3);
    const nx = P[p.k + 1];
    cur = [lerp(cur[0], KX(nx[0]), g), lerp(cur[1], KY(nx[1]), g)];
    pts.push(cur);
  }
  startRing(P[0], a);
  pathLine(pts, a, r.kind === 'gd' ? 1.8 : 2.2);
  if (r.kind !== 'gd') for (let j = 1; j <= p.k; j++) dot(KX(P[j][0]), KY(P[j][1]), 2.6, {color: C.accent, fill: C.accent, width: .8, alpha: a});
  marker(cur[0], cur[1], a);
}
function drawSwarm(sc, r, u, a) {
  const p = prog(r, u), X = r.swarm, k = p.k, s = p.done ? 0 : u > 0 ? p.s : 0;
  const at = (j, i) => [KX(X[j][2 * i]), KY(X[j][2 * i + 1])];
  for (let i = 0; i < D.npart; i++) {
    const pts = []; for (let j = Math.max(0, k - 5); j <= k; j++) pts.push(at(j, i));
    let cur = pts[pts.length - 1];
    if (s > 0 && k < r.it) { const nx = at(k + 1, i); cur = [lerp(cur[0], nx[0], s), lerp(cur[1], nx[1], s)]; pts.push(cur); }
    if (pts.length > 1) line(pts, {color: C.sky, width: 1.1, alpha: a * .8});
    dot(cur[0], cur[1], 2.8, {color: C.navy, fill: C.navy, width: .8, alpha: a});
  }
  const g = r.path[k];
  marker(KX(g[0]), KY(g[1]), a);
}
function drawChains(sc, r, u, a) {
  const p = prog(r, u), n = p.k, T = r.trace;
  ctx.save(); ctx.globalAlpha *= a * .2; ctx.fillStyle = C.accent;
  for (let j = D.burn + 1; j <= n; j++) for (let c = 0; c < 4; c++) ctx.fillRect(KX(T[j * 8 + 2 * c]) - 1.1, KY(T[j * 8 + 2 * c + 1]) - 1.1, 2.2, 2.2);
  ctx.restore();
  startRing([T[0], T[1]], a);
  for (let c = 0; c < 4; c++) marker(KX(T[n * 8 + 2 * c]), KY(T[n * 8 + 2 * c + 1]), a, 4.6);
}
function drawRun(sc, u, a) {
  if (a <= 0) return;
  const r = runOf(sc);
  if (r.kind === 'mcmc') drawChains(sc, r, u, a);
  else if (r.kind === 'pso') drawSwarm(sc, r, u, a);
  else drawLocal(sc, r, u, a);
}

/* ================================================================ (a) the map */
function cross(x, y, a) {
  for (const [c, w] of [['#fff', 4.6], [C.ink, 2]]) {
    line([[x - 6, y - 6], [x + 6, y + 6]], {color: c, width: w, alpha: a});
    line([[x + 6, y - 6], [x - 6, y + 6]], {color: c, width: w, alpha: a});
  }
}
function ring(x, y, a) {
  dot(x, y, 6.5, {color: '#fff', fill: null, width: 4, alpha: a});
  dot(x, y, 6.5, {color: C.ink, fill: null, width: 1.7, alpha: a});
}
function knock(x, y, w, h, a) { ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(x, y, w, h); ctx.restore(); }
function tag(s, x, y, a, o = {}) {        // a label on the map, on a white knockout
  const size = o.size || 16, w = o.math ? math(s, 0, -1e4, {size, alpha: 0}) : tw(s, size);
  const x0 = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  knock(x0 - 4, y - size * .82, w + 8, size * 1.18, a);
  if (o.math) math(s, x0, y, {size, color: o.color || C.ink, alpha: a});
  else text(s, x0, y, {size, color: o.color || C.ink, alpha: a});
}
function mapPanel(sc, u) {
  const a0 = seg(.04, .3);
  // the bands: the map of the variant shown, cross-faded from the one before
  const v = variant(sc), pv = sc.prev ? variant(sc.prev) : v, xf = pv !== v ? seg(sc.t0, .45) : 1;
  ctx.save(); ctx.globalAlpha = a0;
  if (xf < 1) ctx.drawImage(mapImage(pv), MX, MY, MS, MS);
  ctx.globalAlpha = a0 * xf; ctx.drawImage(mapImage(v), MX, MY, MS, MS);
  ctx.restore();
  const A = axes({x: MX, y: MY, w: MS, h: MS, xlim: [LO, HI], ylim: [LO, HI], xticks: [50, 100, 150, 200], yticks: [50, 100, 150, 200],
                  xlabel: '\\rm{storey 1 stiffness }k_{1}\\rm{ (MN/m)}', ylabel: '\\rm{storey 2 stiffness }k_{2}\\rm{ (MN/m)}',
                  tickSize: 16, labelSize: 17, ylabelGap: 50, progress: seg(0, .35)});
  A.inside(() => {
    // the fold line k1 = 2 k2: a building and its twin lie mirrored across it
    line([[KX(40), KY(20)], [KX(220), KY(110)]], {color: C.guide, width: 1.2, dash: [5, 4], progress: seg(.25, .35)});
    // the design values the prior pulls toward
    const pa = (sc.prior ? 1 : 0) * (sc.prev && !sc.prev.prior ? seg(sc.t0, .3) : 1);
    const pp = sc.prev && sc.prev.prior && !sc.prior ? 1 - seg(sc.t0, .3) : 0;
    const da = Math.max(pa, pp);
    if (da > 0) line([[KX(100) - 5, KY(100) - 5], [KX(100) + 5, KY(100) - 5], [KX(100) + 5, KY(100) + 5], [KX(100) - 5, KY(100) + 5]], {color: C.ink, width: 1.5, close: true, fill: '#fff', alpha: da});
    // the runs: the one before fading out, the one shown
    if (sc.prev) drawRun(sc.prev, sc.prev.u, 1 - seg(sc.t0, .25));
    drawRun(sc, u, seg(sc.t0, .2) * seg(.3, .2));
    // the true building and the two exact fits of the measured frequencies
    const ma = lab(.3);
    ring(KX(D.fits[1][0]), KY(D.fits[1][1]), ma);
    cross(KX(D.truek[0]), KY(D.truek[1]), ma);
  });
  // labels, each on its knockout, over whatever passed beneath
  const la = lab(.42);
  tag('true', KX(D.truek[0]) - 10, KY(D.truek[1]) - 15, la, {align: 'center'});
  tag('twin', KX(D.fits[1][0]) + 2, KY(D.fits[1][1]) + 27, la, {align: 'center'});
  const fa = lab(.5), fx = KX(186), fy = KY(93);
  ctx.save(); ctx.translate(fx, fy); ctx.rotate(-Math.atan(.5));
  const fw = math('k_{1} = 2k_{2}', 0, -1e4, {size: 15, alpha: 0});
  knock(-fw / 2 - 4, -26, fw + 8, 19, fa);
  math('k_{1} = 2k_{2}', -fw / 2, -11, {size: 15, color: C.body, alpha: fa});
  ctx.restore();
  if (sc.prior || (sc.prev && sc.prev.prior)) {
    const da = sc.prior ? (sc.prev && !sc.prev.prior ? seg(sc.t0, .3) : 1) : 1 - seg(sc.t0, .3);
    tag('design', KX(100) - 12, KY(100) + 5, da * la, {align: 'right'});
  }
  // the colour bar: the bands, log scale
  const ca = lab(.3), y0 = MY, y1 = MY + MS, lo = -1.5, hi = 5;
  const Yc = l => y1 - (l - lo) / (hi - lo) * (y1 - y0);
  ctx.save(); ctx.globalAlpha *= ca;
  for (let j = 0; j < NL; j++) { const top = Yc(LEV[j]), bot = j ? Yc(LEV[j - 1]) : y1; ctx.fillStyle = BAND[j]; ctx.fillRect(CBX, top, CBW, bot - top); }
  ctx.restore();
  line([[CBX, y0], [CBX + CBW, y0], [CBX + CBW, y1], [CBX, y1]], {color: C.ink, width: 1, close: true, alpha: ca});
  for (let l = -1; l <= 4; l++) {
    line([[CBX + CBW, Yc(l)], [CBX + CBW + 4, Yc(l)]], {color: C.ink, width: 1, alpha: ca});
    math(l === 0 ? '1' : l === 1 ? '10' : '10^{' + l + '}', CBX + CBW + 7, Yc(l) + 5, {size: 15, alpha: ca});
  }
  math('\\Phi', CBX + CBW / 2, y0 - 9, {size: 16, align: 'center', alpha: ca});
}

/* ================================================================ (b) misfit against cost */
const STYLE = {gd: {color: C.sky, dash: null}, gn: {color: C.blue, dash: [6, 4]}, lm: {color: C.navy, dash: null}, pso: {color: C.navy, dash: [1.5, 3.5]}};
const l10 = Math.log10;
function convPanel(sc, u) {
  const A = axes({x: BX, y: BY, w: BW, h: BH, xlim: [0, 4.4], ylim: [-8, 5], xticks: [0, 1, 2, 3, 4], yticks: [-8, -4, 0, 4],
                  xfmt: v => v === 0 ? '1' : v === 1 ? '10' : '10^{' + v + '}', yfmt: v => v === 0 ? '1' : '10^{' + v + '}',
                  tickSize: 16, labelSize: 17, progress: seg(.05, .35)});
  const ca = seg(.35, .4), la = clamp(seg(.05, .35) * 1.4);
  text('forward-model runs', BX + BW / 2, BY + BH + 49, {size: 17, align: 'center', alpha: la});
  math('\\Phi', BX - 52, BY + BH / 2 + 6, {size: 17, align: 'center', alpha: la});
  A.inside(() => {
    for (const kind of ['gd', 'gn', 'lm', 'pso']) {
      const r = runOf(sc, kind), on = kind === sc.solver, pts = [];
      const p = on ? prog(r, u) : {k: r.hist.length - 1, s: 0, done: true};
      for (let j = 0; j <= p.k; j++) pts.push([A.X(l10(r.evals[j])), A.Y(Math.max(-9, l10(Math.max(r.hist[j], 1e-30))))]);
      if (on && !p.done && u > 0 && p.k + 1 < r.hist.length) {
        const g = kind === 'gd' || kind === 'pso' ? p.s : settle(sc.t0 + sc.pre + p.k * PACE[kind], .3), q = pts[pts.length - 1];
        pts.push([lerp(q[0], A.X(l10(r.evals[p.k + 1])), g), lerp(q[1], A.Y(Math.max(-9, l10(Math.max(r.hist[p.k + 1], 1e-30)))), g)]);
      }
      if (on) {
        if (pts.length > 1) line(pts, {color: C.accent, width: 2.4, alpha: seg(sc.t0, .2)});
        if (kind === 'gn' || kind === 'lm') for (const q of pts.slice(0, p.k + 1)) dot(q[0], q[1], 2.4, {color: C.accent, fill: C.accent, width: .8});
      } else if (pts.length > 1) line(pts, {color: STYLE[kind].color, width: 1.7, dash: STYLE[kind].dash, progress: ca});
    }
  });
}
/* ================================================================ (b) for MCMC: the posterior of k1 */
function postPanel(sc, u) {
  const r = runOf(sc), v = variant(sc), ex = D.post.p[v], k0 = D.post.k0, dk = D.post.dk;
  const p = prog(r, u), n = p.k, T = r.trace, NB = 40, h0 = 100, h1 = 180, bw = (h1 - h0) / NB;
  const cnt = new Float64Array(NB); let m = 0;
  for (let j = D.burn + 1; j <= n; j++) for (let c = 0; c < 4; c++) { const b = Math.floor((T[j * 8 + 2 * c] - h0) / bw); m++; if (b >= 0 && b < NB) cnt[b]++; }
  // the y range: the exact peak and the finished histogram's, so nothing moves as samples arrive
  if (!r.ymax) {
    const fin = new Float64Array(NB);
    for (let j = D.burn + 1; j <= r.n; j++) for (let c = 0; c < 4; c++) { const b = Math.floor((T[j * 8 + 2 * c] - h0) / bw); if (b >= 0 && b < NB) fin[b]++; }
    const hmax = Math.max(...fin) / (4 * D.keep * bw), emax = Math.max(...ex);
    r.ymax = Math.ceil(Math.max(hmax, emax) * 1.3 / .02) * .02;
  }
  const ym = r.ymax, step = ym > .16 ? .05 : ym > .08 ? .04 : .02;
  const yt = []; for (let y = 0; y <= ym + 1e-9; y += step) yt.push(+y.toFixed(2));
  const A = axes({x: BX, y: BY, w: BW, h: BH, xlim: [h0, h1], ylim: [0, ym], xticks: [100, 120, 140, 160, 180], yticks: yt,
                  yfmt: y => y === 0 ? '0' : y.toFixed(2), xlabel: 'k_{1}\\rm{ (MN/m)}', ylabel: 'p(k_{1}\\,|\\,d)\\rm{ (m/MN)}', ylabelGap: 62,
                  tickSize: 16, labelSize: 17, progress: seg(.05, .35)});
  A.inside(() => {
    if (m > 0) for (let b = 0; b < NB; b++) {
      const hgt = cnt[b] / (m * bw); if (hgt <= 0) continue;
      const x0 = A.X(h0 + b * bw), x1 = A.X(h0 + (b + 1) * bw), y = A.Y(hgt);
      line([[x0, A.Y(0)], [x0, y], [x1, y], [x1, A.Y(0)]], {color: C.accent, width: 1, fill: C.wash, alpha: seg(sc.t0, .2)});
    }
    const pts = ex.map((v_, i) => [A.X(k0 + i * dk), A.Y(v_)]);
    line(pts, {color: C.navy, width: 2.2, progress: seg(sc.t0, .4)});
  });
  // the key, as the family draws one
  const ka = lab(sc.t0 + .1), kw = 196, kx = BX + BW - kw - 8, ky = BY + 8;
  line([[kx, ky], [kx + kw, ky], [kx + kw, ky + 28], [kx, ky + 28]], {color: C.ink, width: 1, fill: '#fff', close: true, alpha: ka});
  line([[kx + 10, ky + 14], [kx + 34, ky + 14]], {color: C.navy, width: 2.2, alpha: ka});
  text('exact', kx + 41, ky + 19, {size: 15, alpha: ka});
  line([[kx + 96, ky + 21], [kx + 96, ky + 8], [kx + 116, ky + 8], [kx + 116, ky + 21]], {color: C.accent, width: 1, fill: C.wash, alpha: ka});
  text('samples', kx + 123, ky + 19, {size: 15, alpha: ka});
}

/* ================================================================ the table */
const n0 = v => Math.round(v).toLocaleString('en-US');
function outcome(r) { const e = r.path[r.path.length - 1]; return e[0] < 2 * e[1] ? 'true' : 'twin'; }
function table(sc, u) {
  const ta = lab(.45), cx = [RX + 34, 836, 900, RX1];
  line([[RX, TY], [RX1, TY]], {color: C.ink, width: 1.3, alpha: ta});
  text('solver', cx[0], TY + 18, {size: 16, color: C.body, alpha: ta});
  text('iterations', cx[1], TY + 18, {size: 16, color: C.body, align: 'right', alpha: ta});
  text('runs', cx[2], TY + 18, {size: 16, color: C.body, align: 'right', alpha: ta});
  text('ends at', cx[3], TY + 18, {size: 16, color: C.body, align: 'right', alpha: ta});
  line([[RX, TY + 26], [RX1, TY + 26]], {color: C.ink, width: .8, alpha: ta});
  SOLVERS.forEach((kind, i) => {
    const y = TY + 48 + i * 24, r = runOf(sc, kind), on = kind === sc.solver;
    const p = on ? prog(r, u) : {k: kind === 'mcmc' ? r.n : r.it, done: true};
    const col = on ? C.accent : C.ink;
    if (kind === 'mcmc') { for (let q = 0; q < 3; q++) dot(RX + 6 + q * 9, y - 5, 2, {color: on ? C.accent : C.navy, fill: on ? C.accent : C.navy, width: .6, alpha: ta}); }
    else line([[RX, y - 5], [RX + 26, y - 5]], {color: on ? C.accent : STYLE[kind].color, width: on ? 2.4 : 1.7, dash: on ? null : STYLE[kind].dash, alpha: ta});
    text(SNAME[kind], cx[0], y, {size: 16, color: col, alpha: ta});
    const it = kind === 'mcmc' ? p.k : p.done ? r.it : Math.min(r.it, p.k + (u > 0 ? 1 : 0));
    const ev = kind === 'mcmc' ? (p.done ? r.evals : null) : r.evals[it];
    text(n0(it), cx[1], y, {size: 16, color: col, align: 'right', alpha: ta});
    if (ev !== null) text(n0(ev), cx[2], y, {size: 16, color: col, align: 'right', alpha: ta});
    if (p.done) text(kind === 'mcmc' ? Math.round(100 * r.share) + '% true' : outcome(r), cx[3], y, {size: 16, color: col, align: 'right', alpha: ta});
  });
  line([[RX, TY + 158], [RX1, TY + 158]], {color: C.ink, width: 1.3, alpha: ta});
}
/* the measured data and the model at the current estimate */
function dataBlock(sc, u) {
  const a = lab(.55), y = TY + 186, r = runOf(sc);
  const f3 = v => v.toFixed(3), x1 = RX + 78, x2 = RX + 196, x3 = RX + 306;
  text('measured', RX, y, {size: 16, color: C.body, alpha: a});
  math('f_{1} = ' + f3(DF1) + '\\rm{ Hz}', x1, y, {size: 16, alpha: a});
  math('f_{2} = ' + f3(DF2) + '\\rm{ Hz}', x2, y, {size: 16, alpha: a});
  math('r = ' + DR.toFixed(2), x3, y, {size: 16, color: sc.mode ? C.ink : C.guide, alpha: a});
  if (r.kind === 'mcmc') {          // the samples' share on the true side of the fold, and the exact one
    if (!prog(r, u).done) return;
    text('true side', RX, y + 24, {size: 16, color: C.body, alpha: a});
    text('sampled ' + Math.round(100 * r.share) + '%', x1, y + 24, {size: 16, color: C.accent, alpha: a});
    text('exact ' + (100 * D.post.split[variant(sc)]).toFixed(1) + '%', x2, y + 24, {size: 16, color: C.navy, alpha: a});
    return;
  }
  const p = prog(r, u), k = p.done || u <= 0 ? p.k : p.k + (settle(sc.t0 + sc.pre + p.k * (PACE[r.kind] || 0), .3) > .5 ? 1 : 0);
  const e = r.path[Math.min(k, r.path.length - 1)], q = modal(e[0], e[1]), y2 = y + 24;
  text('model', RX, y2, {size: 16, color: C.body, alpha: a});
  math('f_{1} = ' + f3(q[0]) + '\\rm{ Hz}', x1, y2, {size: 16, color: C.accent, alpha: a});
  math('f_{2} = ' + f3(q[1]) + '\\rm{ Hz}', x2, y2, {size: 16, color: C.accent, alpha: a});
  math('r = ' + q[2].toFixed(2), x3, y2, {size: 16, color: C.accent, alpha: a});
}
/* the building, as TikZ draws a shear frame */
function frame(cx, gy, a) {
  const w = 54, h = 30;
  line([[cx - 42, gy], [cx + 42, gy]], {width: 1.8, alpha: a});
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
  for (let x = cx - 38; x <= cx + 42; x += 7) { ctx.moveTo(x, gy); ctx.lineTo(x - 5, gy + 6); }
  ctx.stroke(); ctx.restore();
  for (let s = 0; s < 2; s++) {
    const y0 = gy - s * h, y1 = gy - (s + 1) * h;
    line([[cx - w / 2, y0], [cx - w / 2, y1]], {width: 1.5, alpha: a});
    line([[cx + w / 2, y0], [cx + w / 2, y1]], {width: 1.5, alpha: a});
    line([[cx - w / 2 - 4, y1], [cx + w / 2 + 4, y1]], {color: C.navy, width: 3.2, alpha: a});
    math('k_{' + (s + 1) + '}', cx + w / 2 + 9, y0 - h / 2 + 5, {size: 15, alpha: a});
    math('m', cx - w / 2 - 11, y1 + 5, {size: 15, align: 'right', alpha: a});
  }
}

/* ================================================================ chips */
let HOVER = null, DOWN = null;             // {g, i}: the chip under the pointer, the one pressed
const isH = (g, i) => HOVER && HOVER.g === g && HOVER.i === i, isD = (g, i) => DOWN && DOWN.g === g && DOWN.i === i;
function chips(sc) {
  const L = layout(), a = lab(.1);
  text('solver', L.solver[0].x - 10, ROW1 + 20, {size: 15, color: C.body, align: 'right', alpha: a});
  SOLVERS.forEach((s, i) => { const c = L.solver[i]; uiChip(c.x, c.y, c.w, c.h, SNAME[s], {on: sc.solver === s, hover: isH('solver', i), down: isD('solver', i)}, a); });
  text('start', L.start[0].x - 10, ROW2 + 20, {size: 15, color: C.body, align: 'right', alpha: a});
  D.starts.forEach((s, i) => { const c = L.start[i]; uiChip(c.x, c.y, c.w, c.h, '(' + s[0] + ', ' + s[1] + ')', {on: sc.si === i, hover: isH('start', i), down: isD('start', i)}, a); });
  text('add', L.add, ROW2 + 20, {size: 15, color: C.body, align: 'right', alpha: a});
  ['mode shape', 'prior'].forEach((s, i) => { const c = L.opt[i]; uiChip(c.x, c.y, c.w, c.h, s, {on: i ? !!sc.prior : !!sc.mode, hover: isH('opt', i), down: isD('opt', i)}, a); });
}

/* ================================================================ draw */
function draw() {
  const sc = scene(), u = t - sc.t0 - sc.pre;
  chips(sc);
  frame(930, 92, lab(.2));
  sub_('a', 18, 128, 'misfit of the measured data', lab(.04));
  if (!STILL) text('click the map to start there', MX + MS, 128, {size: 15, color: C.muted, align: 'right', alpha: lab(.5)});
  mapPanel(sc, u);
  if (sc.solver === 'mcmc') {
    const ba = lab(.06); sub_('b', RX - 4, 128, 'posterior of', ba);
    math('k_{1}', RX + 31 + tw('posterior of ', 17), 128, {size: 17, color: C.body, alpha: ba});
    postPanel(sc, u);
  }
  else { sub_('b', RX - 4, 128, 'misfit against cost', lab(.06)); convPanel(sc, u); }
  table(sc, u);
  dataBlock(sc, u);
  const pa = lab(.6);
  mixed(D.params[0], 18, H - 34, {size: 14, color: C.muted, alpha: pa});
  mixed(D.params[1], 18, H - 13, {size: 14, color: C.muted, alpha: pa});
  place();
}
/* runs of words (text) and of symbols ({m: ...}, math), set one after the other */
function mixed(parts, x, y, o) { let cx = x; for (const q of parts) cx += typeof q === 'string' ? text(q, cx, y, o) : math(q.m, cx, y, o); return cx - x; }
function sub_(l, x, y, words, a) { panel(l, x, y, {alpha: a}); text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }

/* ================================================================ the reader's hand */
const FIG = document.querySelector('.fig');
function shown() { return scene(); }
function choose(ch) {
  const cur = shown(), u = t - cur.t0 - cur.pre;
  const next = {solver: cur.solver, si: cur.si, start: cur.start, mode: cur.mode, prior: cur.prior, ...ch};
  const prev = {solver: cur.solver, si: cur.si, start: cur.start, mode: cur.mode, prior: cur.prior, u};
  const vchg = variant(prev) !== variant(next);
  next.pre = vchg ? PRE_NEW : PRE_SAME; next.prev = prev;
  next.t0 = playing ? t : t - next.pre - dur(runOf(next)) - 2;
  PICK = next;
  if (!playing) render();
  sync(); say();
}
function reset() { PICK = null; HOVER = DOWN = null; sync(); }
/* ?view=SOLVER-START-DATA preselects a state (the overlap check runs every one):
   SOLVER gd, gn, lm, pso or mcmc; START 0 to 3 or k1_k2; DATA f, fm, fp or fmp */
(() => {
  const m = /[?&]view=([a-z]+)-([\d._]+)-(f[mp]*)/.exec(location.search);
  if (!m || !SOLVERS.includes(m[1])) return;
  const st = m[2].includes('_') ? m[2].split('_').map(Number) : D.starts[+m[2]];
  if (!st) return;
  PICK = {solver: m[1], si: m[2].includes('_') ? -1 : +m[2], start: st, mode: m[3].includes('m') ? 1 : 0, prior: m[3].includes('p') ? 1 : 0,
          t0: T_START, pre: PRE_NEW, prev: null};
})();
const KB = {solver: [], start: [], opt: []};
let said = null, PLACED = '';
function say() {
  if (!said) return;
  const sc = shown(), r = runOf(sc), where = '(' + sc.start.map(v => +v.toFixed(1)).join(', ') + ')';
  const data = 'frequencies' + (sc.mode ? ' and mode shape' : '') + (sc.prior ? ', with the prior' : '');
  if (r.kind === 'mcmc') said.textContent = 'MCMC from ' + where + ' on ' + data + ': ' + Math.round(100 * r.share) + ' percent of 16,000 samples on the true side of the fold.';
  else { const e = r.path[r.path.length - 1]; said.textContent = SNAME[r.kind] + ' from ' + where + ' on ' + data + ': ' + r.it + ' iterations, ' + n0(r.evals[r.evals.length - 1]) + ' forward runs, ends at k1 = ' + e[0].toFixed(1) + ', k2 = ' + e[1].toFixed(1) + ' MN/m (' + (outcome(r) === 'twin' ? 'the twin' : 'the true side') + ').'; }
}
function sync() {
  const sc = shown();
  KB.solver.forEach((b, i) => { b.setAttribute('aria-checked', String(SOLVERS[i] === sc.solver)); b.tabIndex = SOLVERS[i] === sc.solver ? 0 : -1; });
  KB.start.forEach((b, i) => { b.setAttribute('aria-checked', String(sc.si === i)); b.tabIndex = sc.si === i || (sc.si < 0 && i === 0) ? 0 : -1; });
  KB.opt.forEach((b, i) => b.setAttribute('aria-pressed', String(!!(i ? sc.prior : sc.mode))));
}
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
const inMap = (X, Y) => X >= MX && X <= MX + MS && Y >= MY && Y <= MY + MS;
function place() {                         // the keyboard's stand-ins sit on the chips they choose
  if (STILL || !LAY || !KB.solver.length) return;
  const key = String(cv.clientWidth);
  if (key === PLACED) return;
  PLACED = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  const put = (b, c) => { b.style.left = px(c.x - 3); b.style.top = px(c.y - 6); b.style.width = px(c.w + 6); b.style.height = px(c.h + 12);
    b.style.setProperty('--ix', px(3)); b.style.setProperty('--iy', px(6)); };   // the ring hugs the drawn chip
  KB.solver.forEach((b, i) => put(b, LAY.solver[i])); KB.start.forEach((b, i) => put(b, LAY.start[i])); KB.opt.forEach((b, i) => put(b, LAY.opt[i]));
}
if (!STILL) {
  document.head.insertAdjacentHTML('beforeend', '<style>.nfm{position:absolute;box-sizing:border-box;margin:0;padding:0;' +
    'border:0;background:transparent;color:transparent;cursor:pointer;-webkit-tap-highlight-color:transparent;overflow:hidden;font:inherit}' +
    '.nfm:focus{outline:none}.nfm::after{content:"";position:absolute;inset:var(--iy,4px) var(--ix,2px)}' +
    '.nfm:focus-visible::after{outline:2px solid #095A94;outline-offset:1px}</style>');
  const ctl = FIG.querySelector('.ctl');
  const group = (label, role) => { const g = document.createElement('div'); if (role) g.setAttribute('role', role); g.setAttribute('aria-label', label); FIG.insertBefore(g, ctl); return g; };
  const gS = group('Solver', 'radiogroup'), gT = group('Starting point', 'radiogroup'), gO = group('Data added to the misfit', 'group');
  const roving = (list, i, pick) => e => {
    const d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key], n = list.length;
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : d ? (i + d + n) % n : -1;
    if (j < 0) return;
    e.preventDefault(); list[j].focus(); pick(j);
  };
  const mk = (g, list, gname, label, role, onPick) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'nfm'; b.textContent = label;
    if (role) b.setAttribute('role', role);
    b.setAttribute('aria-label', label);
    const i = list.length;
    b.addEventListener('click', ev => { ev.stopPropagation(); onPick(i); });
    b.addEventListener('pointerenter', () => { HOVER = {g: gname, i}; if (!playing) render(); });
    b.addEventListener('pointerleave', () => { HOVER = DOWN = null; if (!playing) render(); });
    b.addEventListener('pointerdown', () => { DOWN = {g: gname, i}; if (!playing) render(); });
    b.addEventListener('pointerup', () => { DOWN = null; if (!playing) render(); });
    b.addEventListener('pointercancel', () => { HOVER = DOWN = null; if (!playing) render(); });
    g.appendChild(b); list.push(b);
    return b;
  };
  SOLVERS.forEach(s => mk(gS, KB.solver, 'solver', SNAME[s], 'radio', i => choose({solver: SOLVERS[i]})));
  D.starts.forEach(s => mk(gT, KB.start, 'start', 'start at k1 = ' + s[0] + ', k2 = ' + s[1] + ' MN/m', 'radio', i => choose({si: i, start: D.starts[i]})));
  ['add the measured mode shape', 'add the prior toward the design values'].forEach(s => mk(gO, KB.opt, 'opt', s, null,
    i => choose(i ? {prior: shown().prior ? 0 : 1} : {mode: shown().mode ? 0 : 1})));
  KB.solver.forEach((b, i) => b.addEventListener('keydown', roving(KB.solver, i, j => choose({solver: SOLVERS[j]}))));
  KB.start.forEach((b, i) => b.addEventListener('keydown', roving(KB.start, i, j => choose({si: j, start: D.starts[j]}))));
  said = document.createElement('div'); said.setAttribute('role', 'status');
  said.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;pointer-events:none';
  FIG.appendChild(said);
  sync();
  /* a click on the map chooses a start there (on a chip's start if within 10 units);
     a click on the chips' rows or the map never also pauses */
  cv.addEventListener('pointermove', e => { const [X, Y] = toUnits(e); cv.style.cursor = inMap(X, Y) ? 'crosshair' : Y < ROW2 + CHH + 10 ? 'default' : ''; });
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const [X, Y] = toUnits(e);
    if (inMap(X, Y)) {
      const k1 = LO + (X - MX) / MS * (HI - LO), k2 = LO + (MY + MS - Y) / MS * (HI - LO);
      const near = D.starts.findIndex(s => Math.hypot(KX(s[0]) - X, KY(s[1]) - Y) < 10);
      if (near >= 0) choose({si: near, start: D.starts[near]});
      else choose({si: -1, start: [Math.round(k1 * 10) / 10, Math.round(k2 * 10) / 10]});
      e.stopPropagation();
    } else if (Y < ROW2 + CHH + 10) e.stopPropagation();
  }, true);
}
boot();
"""


# ------------------------------------------------------------------ the page
TITLE = "Figure 6: Finite element model updating, a nonlinear inverse problem"
ARIA = ("A map of the misfit between measured and computed natural frequencies over the two storey "
        "stiffnesses of a two-storey shear building: a long curved valley holds two pairs that fit the "
        "data exactly, the true building and its twin. Gradient descent, Gauss-Newton, Levenberg-Marquardt, "
        "a particle swarm and MCMC sampling run on it from a chosen start, beside their misfit against the "
        "number of forward-model runs and a table of iterations; adding the measured mode shape or a prior "
        "reshapes the map.")


def poster_time(steps_len):
    """The tour starts at 0.1 s with a 0.5 s fade; the poster is 0.9 s after his
    default run (Levenberg-Marquardt from (210, 30)) has converged."""
    return round(0.1 + 0.5 + steps_len * 0.40 + 0.9, 3)


def model_data():
    good, twin, _ = exact_fits()
    maps, post, split = [], [], []
    for v in range(4):
        maps.append(encode_map(contours(v)))
        p, s = posterior(v)
        post.append(p)
        split.append(s)
    lm0 = run("lm", STARTS[0], 0)
    data = dict(
        mass=MASS, lo=LO, hi=HI, truek=list(TRUE), noise=list(NOISE), sf=SF, sr=SR, sp=SP, kp=KP,
        starts=[list(s) for s in STARTS], npart=NPART, niter=NITER, burn=BURN, keep=KEEP, psd=PSD,
        levels=[float(x) for x in LEVELS], maps=maps, fits=[list(good), list(twin)],
        post=dict(k0=float(PK1[0]), dk=0.25, p=[np.round(p, 6).tolist() for p in post], split=split),
        poster=poster_time(lm0["it"]),
        params=[["two-storey shear building, floors of 100 t; measured ", {"m": "f_{1}"}, ", ", {"m": "f_{2}"},
                 " 0.3% high and 0.4% low, mode ratio ", {"m": r"r = \phi_{2}/\phi_{1}"}, " 2% high; ", {"m": r"\sigma"},
                 " 0.3% and 5%"],
                ["prior 100 MN/m ", {"m": r"\pm"}, " 35%; swarm of 28 particles, 70 iterations; Metropolis MCMC, 4 chains of "
                 "4,150 steps; random seed ", {"m": r"1000k_{1} + k_{2}"}, " of the start"]],
    )
    return data, dict(good=good, twin=twin, post=post, split=split, lm0=lm0)


def build():
    t0 = time.time()
    data, res = model_data()
    print(f"model data in {time.time() - t0:.1f} s; poster at t = {data['poster']} s")
    path = common.build_html(NAME, TITLE, ARIA, 1000, 700, data, JS)
    print("page:", path, os.path.getsize(path), "bytes")
    return data, res


# ------------------------------------------------------------------ validation
def local_minima(variant):
    """Every local minimum of Phi in the box, from L-BFGS-B started on a 25 x 25 grid."""
    from scipy.optimize import minimize
    f = lambda x: float(phi_v(np.array(x[0]), np.array(x[1]), variant))
    mins = []
    for a in np.linspace(25, 215, 25):
        for b in np.linspace(25, 215, 25):
            r = minimize(f, [a, b], method="L-BFGS-B", bounds=[(LO, HI), (LO, HI)],
                         options=dict(ftol=1e-15, gtol=1e-12, maxiter=5000))
            if not any(math.hypot(*(r.x - m)) < 0.5 for m, _ in mins):
                mins.append((r.x, r.fun))
    return sorted(mins, key=lambda z: z[1])


def saddle(variant):
    """The saddle of Phi between the two minima (Newton on the gradient), or None."""
    from scipy.optimize import root
    m = Model(*VARIANTS[variant])

    def grad(x):
        e, J = m.resid(x[0], x[1], jac=True)
        return np.array([2 * sum(J[k][0] * e[k] for k in range(len(e))), 2 * sum(J[k][1] * e[k] for k in range(len(e)))])

    def hess(x, h=1e-5):
        return np.column_stack([(grad(x + d) - grad(x - d)) / (2 * h) for d in (np.array([h, 0]), np.array([0, h]))])
    for k1 in np.linspace(126, 152, 27):
        ks = np.linspace(55, 85, 3001)
        k2 = ks[int(np.argmin(phi_v(np.full_like(ks, k1), ks, variant)))]
        sol = root(grad, [k1, k2], jac=hess, tol=1e-14)
        if sol.success:
            ev = np.linalg.eigvalsh(hess(sol.x))
            if ev[0] < 0 < ev[1]:
                return sol.x, float(phi_v(np.array(sol.x[0]), np.array(sol.x[1]), variant))
    return None


def validate(data, res):
    import scipy.linalg as sla
    L = []
    say = L.append
    good, twin = res["good"], res["twin"]
    _, _, (L1, L2, tr, det) = exact_fits()
    say("Figure 6 (nf-sp-inv-update): finite element model updating, a nonlinear inverse problem;")
    say("check of tools/numfig/sp_inv_update.py")
    say("")
    say("MODEL (the professor's animation, model-updating-solvers-animation.html)")
    say(f"  two-storey shear building, floor masses m = {MASS / 1e3:.0f} t each; K = 10^6 [k1 + k2, -k2; -k2, k2] N/m,")
    say(f"  k1 (ground storey) and k2 (top storey) in MN/m, searched in [{LO:.0f}, {HI:.0f}] MN/m.")
    say(f"  true building (k1, k2) = ({TRUE[0]:.0f}, {TRUE[1]:.0f}) MN/m: f1 = {_MT[0]:.6f} Hz (= 10/pi exactly: lambda1 = 400 s^-2),")
    say(f"  f2 = {_MT[1]:.6f} Hz (lambda2 = 2,400 s^-2), first-mode ratio phi2/phi1 = {_MT[2]:.6f} (= 2).")
    say(f"  measured (his fixed errors): f1 = {DF1:.6f} Hz (+0.3%), f2 = {DF2:.6f} Hz (-0.4%), r = {DR:.4f} (+2%).")
    say("  misfit Phi = ((f1 - f1m)/(0.003 f1m))^2 + ((f2 - f2m)/(0.003 f2m))^2 [+ ((r - rm)/(0.05 rm))^2 with the")
    say("  mode shape] [+ ((k1 - 100)/35)^2 + ((k2 - 100)/35)^2 with the prior]; uniform prior on the box.")
    say("  closed form: T = k1 + 2 k2, R = sqrt(k1^2 + 4 k2^2), mu2 = (T + R)/2, mu1 = 2 k1 k2/(T + R) (MN/m),")
    say("  lambda = 10^6 mu / m, f = sqrt(lambda)/(2 pi), r = (k1 + R)/(2 k2).")
    say("")
    say("THE TWIN (Hadamard's second condition, uniqueness, fails)")
    say(f"  the frequencies fix the trace and determinant of M^-1 K: k1 + 2 k2 = L1 + L2 = {tr:.6f} and")
    say(f"  k1 k2 = L1 L2 = {det:.6f} (MN/m, L = (2 pi f)^2 m / 10^6: L1 = {L1:.6f}, L2 = {L2:.6f}), so")
    say(f"  2 k2^2 - (L1 + L2) k2 + L1 L2 = 0 has two roots: (k1, k2) = ({good[0]:.4f}, {good[1]:.4f}) next to the")
    say(f"  true building and its twin ({twin[0]:.4f}, {twin[1]:.4f}) MN/m. The twin of any (k1, k2) is (2 k2, k1/2):")
    say("  it keeps k1 + 2 k2 and k1 k2, |det| of the map is 1, and its fixed points are the fold line k1 = 2 k2,")
    say("  where the Jacobian of (k1 + 2 k2, k1 k2), k1 - 2 k2, vanishes.")
    gf = modal(*good); tf = modal(*twin)
    say(f"  both reproduce the data: f1 = {gf[0]:.9f}, {tf[0]:.9f} Hz; f2 = {gf[1]:.9f}, {tf[1]:.9f} Hz (measured")
    say(f"  {DF1:.9f}, {DF2:.9f}); their mode ratios differ: r = {gf[2]:.4f} and {tf[2]:.4f} (measured {DR:.4f}).")
    say("  with exact data the pair would be (120, 80) and (160, 60) (r = 2 and 3). A 0.3% error in f1 and")
    say(f"  -0.4% in f2 move the fit near the truth by {math.hypot(good[0] - 120, good[1] - 80):.2f} MN/m (k1 +{100 * (good[0] / 120 - 1):.1f}%,"
        f" k2 {100 * (good[1] / 80 - 1):.1f}%): stability, Hadamard's third condition, is weak too.")
    say("")
    say("VALIDATION")
    # 1. closed form against a general eigensolver
    e_f = e_r = 0.0
    for k1 in np.linspace(LO, HI, 21):
        for k2 in np.linspace(LO, HI, 21):
            K = 1e6 * np.array([[k1 + k2, -k2], [-k2, k2]])
            w2, V = sla.eigh(K, MASS * np.eye(2))
            q = modal(k1, k2)
            e_f = max(e_f, abs(q[0] / (np.sqrt(w2[0]) / TWO_PI) - 1), abs(q[1] / (np.sqrt(w2[1]) / TWO_PI) - 1))
            e_r = max(e_r, abs(q[2] / (V[1, 0] / V[0, 0]) - 1))
    say("  1. the closed-form eigenpairs against scipy.linalg.eigh(K, M) on a 21 x 21 grid over the box:")
    say(f"     largest relative difference {e_f:.1e} in f1, f2 and {e_r:.1e} in phi2/phi1.")
    # 2. sensitivities against central differences
    e_j = 0.0
    rng = np.random.default_rng(6)
    for _ in range(400):
        k1, k2 = rng.uniform(LO, HI, 2)
        for v in range(4):
            m = Model(*VARIANTS[v])
            e, J = m.resid(k1, k2, jac=True)
            J = np.array(J)
            for j, h in ((0, 1e-5 * k1), (1, 1e-5 * k2)):
                xp = [k1, k2]; xm = [k1, k2]; xp[j] += h; xm[j] -= h
                fd = (np.array(m.resid(*xp)) - np.array(m.resid(*xm))) / (2 * h)
                e_j = max(e_j, float(np.max(np.abs(J[:, j] - fd) / np.maximum(1.0, np.abs(J[:, j])))))
    say("  2. the eigenvalue sensitivities (Fox and Kapoor, closed form) against central differences at 400")
    say(f"     random points in all four variants: largest difference {e_j:.1e} (relative, or absolute below 1).")
    # 3. the swap
    pts = rng.uniform(LO, HI / 2, size=(20000, 2))
    a = phi_v(pts[:, 0], pts[:, 1], 0); b = phi_v(2 * pts[:, 1], pts[:, 0] / 2, 0)
    say("  3. Phi (frequencies only) at 20,000 points and at their twins (2 k2, k1/2): largest difference")
    say(f"     {float(np.max(np.abs(a - b))):.1e} (bit for bit: the swap only scales by powers of 2 and reorders sums).")
    # 4. minima, numerically
    say("  4. every local minimum, from L-BFGS-B started on a 25 x 25 grid (eigenvalues of the Hessian > 0):")
    minima = {}
    for v in range(4):
        mins = local_minima(v)
        minima[v] = mins
        txt = "; ".join(f"({x[0]:.4f}, {x[1]:.4f}) Phi = {f:.4g}" for x, f in mins)
        say(f"     {VNAME[v]}: {txt}")
    d_good = min(math.hypot(*(x - np.array(good))) for x, _ in minima[0])
    d_twin = min(math.hypot(*(x - np.array(twin))) for x, _ in minima[0])
    say(f"     frequencies only: the two minima against the quadratic's roots: {d_good:.1e} and {d_twin:.1e} MN/m.")
    say("     with the mode shape the twin is not even a local minimum (one minimum left); with the prior it")
    say("     stays a local minimum, Phi 2.49 above the global one: a local solver started on its side is still")
    say("     trapped, though the global optimum is now unique.")
    for v in (0, 2):
        sd = saddle(v)
        if sd:
            say(f"     saddle between them, {VNAME[v]}: ({sd[0][0]:.4f}, {sd[0][1]:.4f}), Phi = {sd[1]:.4f}"
                + (f" (on the fold: k1 - 2 k2 = {sd[0][0] - 2 * sd[0][1]:.1e})" if v == 0 else ""))
    # 5. the map
    say(f"  5. the map: filled contours of log10 Phi at {', '.join(f'{c:g}' for c in LEVELS)} (half decades),")
    say("     marching squares (contourpy) on a 2,401 x 2,401 grid of the closed form (0.083 MN/m),")
    say("     simplified to 0.02 MN/m (Douglas-Peucker; kept vertices are contour points) and stored to 0.003 MN/m.")
    worst_l = []; verts = 0
    for v in range(4):
        lv = decode_map(data["maps"][v])
        for c, rings in zip(LEVELS, lv):
            for r in rings:
                inside = (r[:, 0] > LO + 0.01) & (r[:, 0] < HI - 0.01) & (r[:, 1] > LO + 0.01) & (r[:, 1] < HI - 0.01)
                if inside.any():
                    z = np.log10(phi_v(r[inside, 0], r[inside, 1], v))
                    worst_l.append(np.abs(z - c))
                    verts += int(inside.sum())
    wl = np.concatenate(worst_l)
    say(f"     log10 Phi at the {verts:,} stored vertices off the box edge against their level: median"
        f" {np.median(wl):.1e},")
    say(f"     99th percentile {np.percentile(wl, 99):.1e}, largest {wl.max():.1e} decades (the largest where the band")
    say("     closes around a minimum and log10 Phi is steepest).")
    areas = []
    for v in (0, 1):
        A1 = [sum(abs(_area(r)) for r in rings) for rings in contours(v, n=1201)]
        A2 = [sum(abs(_area(r)) for r in rings) for rings in decode_map(data["maps"][v])]
        areas.append(max(abs(a1 / a2 - 1) for a1, a2 in zip(A1, A2) if a2 > 1.0))
    say("     grid convergence: band areas from a 1,201 grid against the 2,401 grid, largest relative change")
    say(f"     {areas[0]:.1e} (frequencies only) and {areas[1]:.1e} (with the mode shape), bands over 1 (MN/m)^2.")
    # 6. the exact posterior
    say("  6. the exact posterior, p(k | d) proportional to exp(-Phi/2) on the box: share on the true side of the fold")
    say("     (k1 < 2 k2), midpoint rule on N x N grids:")
    for v in range(4):
        sh = []
        for N in (1000, 2000, 4000):
            kk = LO + (HI - LO) * (np.arange(N) + 0.5) / N
            tot = side = 0.0
            pmin = phi_v(np.array([123.6]), np.array([77.5]), v)[0]
            for i0 in range(0, N, 500):
                A_, B_ = np.meshgrid(kk, kk[i0:i0 + 500])
                w = np.exp(-(phi_v(A_, B_, v) - pmin) / 2)
                side += w[A_ < 2 * B_].sum(); tot += w.sum()
            sh.append(side / tot)
        say(f"     {VNAME[v]:20s} N = 1,000: {sh[0]:.7f}   2,000: {sh[1]:.7f}   4,000: {sh[2]:.7f}")
    say("     frequencies only, exactly one half: the swap maps one side onto the other and keeps area and Phi")
    say("     (the box cuts nothing that carries weight).")
    pk = np.array(res["post"][0])
    say("     the marginal p(k1 | d) drawn in (b) (Simpson, 0.01 MN/m in k2) integrates over 100..180 MN/m to")
    say(f"     {np.trapezoid(pk, PK1):.6f} (frequencies only): all of the posterior lies in the range drawn.")
    # 7. the samplers against it
    say("  7. MCMC (his Metropolis: 4 chains, proposal sd 5 MN/m, 150 burn-in + 4,000 kept steps) against the")
    say("     exact share, from each start chip (16,000 samples each):")
    for v in range(4):
        row = []
        for st in STARTS:
            r = run("mcmc", st, v)
            row.append(f"{100 * r['share']:.1f}%")
        say(f"     {VNAME[v]:20s} " + ", ".join(row) + f"   exact {100 * res['split'][v]:.1f}%")
    accs = run("mcmc", STARTS[0], 0)["acc"]
    say(f"     acceptance from (210, 30), frequencies only: {', '.join(str(a) for a in accs)} of 4,150 per chain"
        f" ({100 * sum(accs) / (4 * 4150):.1f}%).")
    say("     the share is unbiased but noisy: see PSO/MCMC SEEDS below.")
    say("")
    say("PSO/MCMC SEEDS (the same code with seeds 1 to 500 in place of the start's seed)")
    for v in (0, 2, 1):
        outs, its = [], []
        for seed in range(1, 501):
            m = Model(*VARIANTS[v])
            rr = run_pso(m, STARTS[0], seed)
            e = rr["path"][-1]
            outs.append(e[0] < 2 * e[1])
            P = rr["path"]; k = len(P) - 1
            while k > 0 and dist(P[k - 1], e) < 0.01:
                k -= 1
            its.append(k)
        say(f"  particle swarm, {VNAME[v]}: true side {100 * np.mean(outs):.1f}%, twin side {100 * (1 - np.mean(outs)):.1f}%;"
            f" best point settled (to 0.01 MN/m) after a median {np.median(its):.0f} of 70 iterations")
    shares = {0: [], 2: []}
    for v in (0, 2):
        for seed in range(1, 41):
            shares[v].append(run_mcmc(Model(*VARIANTS[v]), STARTS[0], seed)["share"])
    for v in (0, 2):
        a_ = np.array(shares[v])
        say(f"  MCMC, {VNAME[v]}, seeds 1 to 40: true-side share {100 * a_.mean():.1f}% +- {100 * a_.std():.1f}%"
            f" (exact {100 * res['split'][v]:.1f}%)")
    say("")
    say("RUNS FROM THE START CHIPS (iterations, forward runs, end point; the tour runs (210, 30))")
    keyrows = {}
    for si, st in enumerate(STARTS):
        for v in range(4):
            parts = []
            for kind in ("gd", "gn", "lm", "pso"):
                r = run(kind, st, v)
                e = r["path"][-1]
                side = "true" if e[0] < 2 * e[1] else "twin"
                parts.append(f"{kind} {r['it']}/{r['evals'][-1]} {side} ({e[0]:.2f}, {e[1]:.2f})")
                keyrows[(si, v, kind)] = (r["it"], r["evals"][-1], side, e, r["hist"][-1])
            rm = run("mcmc", st, v)
            parts.append(f"mcmc 4150/{rm['evals']} {100 * rm['share']:.1f}% true")
            say(f"  ({st[0]:.0f}, {st[1]:.0f}) {VNAME[v]}:")
            say("     " + "; ".join(parts[:2]))
            say("     " + "; ".join(parts[2:]))
    say("  (gradient descent stops when a step moves less than 0.001 MN/m, Gauss-Newton likewise, Levenberg-")
    say("  Marquardt also when no damping gives a decrease; the swarm runs its 70 iterations.)")
    say("")
    with session() as open_:
        cc = crosscheck(open_)
        ctl = check_controls(open_)
        st_res, st_err = check_states(open_)
    say("THE PAGE AGAINST THE PORT (Playwright, headless Chromium)")
    say(f"  {cc['count']} runs: 5 solvers x 4 variants x 7 starts (the 4 chips and (163.7, 48.2), (57.3, 141.9),")
    say("  (201.4, 187.6)). Largest difference between the page's numbers and this script's, path points in")
    say("  MN/m (and Phi, relative), the whole swarm, every MCMC chain state:")
    say("     " + ", ".join(f"{k} {cc['worst'][k]:.1e}" for k in SOLVERS))
    say(f"  iteration counts, forward-run counts and acceptances identical: {all(cc['same'].values())}")
    say(f"  the page's f1, f2, r at 1,681 grid points against numpy: {cc['e_modal']:.1e} (relative)")
    say(f"  the page's data: f1 = {cc['data'][0]:.12f}, f2 = {cc['data'][1]:.12f}, r = {cc['data'][2]:.12f}"
        f" (port: {DF1:.12f}, {DF2:.12f}, {DR:.12f})")
    say(f"  script errors: {cc['errors'] or 'none'}")
    say("")
    say("THE PAGE LIVE (672 px)")
    say(f"  after the intro playing: {ctl['playing_after_intro']}; clock runs: {ctl['clock_runs']}; keyboard stand-ins: {ctl['buttons']}")
    for b, sc in zip(["gradient descent", "Gauss-Newton", "Levenberg-Marquardt", "particle swarm", "MCMC sampling",
                      "(210, 30)", "(40, 200)", "(100, 40)", "(150, 200)", "mode shape", "prior"], ctl["after_clicks"]):
        say(f"  click '{b}': solver {sc[0]}, start chip {sc[1]}, mode shape {int(sc[2])}, prior {int(sc[3])}, still playing {sc[4]}")
    say(f"  click on the map: start chip {ctl['map_click'][0]} (none), start {ctl['map_click'][1]} MN/m, still playing"
        f" {ctl['map_click'][2]}")
    say(f"  click on open ground pauses, as in every figure: {ctl['ground_click_pauses']}")
    say(f"  arrow key in the solver group chooses: {ctl['arrow_key']}; status: {ctl['status']}")
    say(f"  restart returns to the tour: {ctl['restart_tour']}; frames per second while 16,000 samples are drawn:"
        f" {ctl['fps_mcmc']:.0f} (headless, software)")
    say(f"  script errors: {ctl['errors'] or 'none'}")
    say("")
    bad = [r for r in st_res if r[2] or r[3]]
    say("OVERLAPS (engine.js ?overlap)")
    say("  the poster and every 0.25 s of the tour up to it: clean (common.still raises otherwise)")
    say(f"  every state through ?view=SOLVER-START-DATA: {len(states())} chip states and 4 clicked starts, each at")
    say(f"  5 moments (before the run, its start, 35% and 70% through, after it): {len(st_res)} frames,"
        f" {len(bad)} with collisions")
    for r in bad[:10]:
        say(f"    {r[0]} t = {r[1]}: {r[2][:2]} {r[3][:2]}")
    say(f"  script errors: {st_err or 'none'}")
    say("")
    say("THE PAGE")
    say(f"  W = 1000, H = 700, POSTER_T = {data['poster']} s: his default, Levenberg-Marquardt from (210, 30) on the")
    say("  frequencies, converged on the twin. The tour: Levenberg-Marquardt, Gauss-Newton, gradient descent, the")
    say("  swarm and MCMC from (210, 30) on the frequencies; MCMC and Levenberg-Marquardt with the mode shape;")
    say("  Levenberg-Marquardt and MCMC with the prior; then again. One iteration every 0.40 s (Levenberg-")
    say("  Marquardt), 0.45 s (Gauss-Newton), 0.024 s (gradient descent), 0.10 s (swarm); MCMC 1,500 steps a second.")
    say("  A chip or a click on the map chooses (the tour stops); restart returns to it; paused or with less")
    say("  motion, the chosen run shows complete. Keyboard: two radio groups and two toggles; a status line.")
    path = os.path.join(common.ANIM, f"nf-{NAME}.html")
    say(f"  page {os.path.getsize(path):,} bytes; still {os.path.getsize(os.path.join(common.ANIM, f'nf-{NAME}.webp')):,} bytes")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(HERE, "sp_inv_update.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return keyrows


def _area(r):
    x, y = r[:, 0], r[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


# ------------------------------------------------------------------ the page in Chromium
@contextlib.contextmanager
def session():
    """The page served over http beside the fonts, in headless Chromium;
    yields open(query) -> (page, errors)."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{NAME}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pages = []

            def open_(query, width=672, dpr=1):
                pg = b.new_page(viewport={"width": width, "height": 1100}, device_scale_factor=dpr)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
                pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?{query}")
                pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
                pages.append(pg)
                return pg, errs
            yield open_
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def crosscheck(open_):
    """Every solver from every chip start and three other starts, in every
    variant, run by the page and by the port: the largest difference."""
    starts = STARTS + [(163.7, 48.2), (57.3, 141.9), (201.4, 187.6)]
    pg, errs = open_("still")
    worst = {k: 0.0 for k in SOLVERS}
    same = {k: True for k in SOLVERS}
    count = 0
    for st in starts:
        for v, (mode, prior) in enumerate(VARIANTS):
            for kind in SOLVERS:
                js = pg.evaluate(f"__solve('{kind}', {st[0]!r}, {st[1]!r}, {int(mode)}, {int(prior)})")
                py = run(kind, st, v)
                count += 1
                if kind == "mcmc":
                    a = np.array(js["trace"]); b = np.array(py["trace"]).ravel()
                    d = float(np.max(np.abs(a - b))) if a.shape == b.shape else math.inf
                    same[kind] &= js["acc"] == py["acc"] and js["evals"] == py["evals"]
                else:
                    a = np.array(js["path"]); b = np.array(py["path"])
                    d = float(np.max(np.abs(a - b))) if a.shape == b.shape else math.inf
                    h = np.array(js["hist"]); hp = np.array(py["hist"])
                    d = max(d, float(np.max(np.abs(h - hp) / np.maximum(1.0, np.abs(hp)))) if h.shape == hp.shape else math.inf)
                    same[kind] &= js["it"] == py["it"] and js["evals"] == py["evals"]
                    if kind == "pso":
                        a = np.array(js["swarm"]); b = np.array(py["swarm"])
                        d = max(d, float(np.max(np.abs(a - b))) if a.shape == b.shape else math.inf)
                worst[kind] = max(worst[kind], d)
    # the page's own misfit and frequencies at grid points, against the vectorized closed form
    kk = np.linspace(LO, HI, 41)
    pts = [(float(a), float(b)) for a in kk for b in kk]
    pf = np.array(pg.evaluate("pts => pts.map(p => modal(p[0], p[1]).slice(0, 3))", pts))
    f1, f2, r = modal_v(np.array([p[0] for p in pts]), np.array([p[1] for p in pts]))
    e_modal = float(np.max(np.abs(pf - np.column_stack([f1, f2, r])) / np.abs(np.column_stack([f1, f2, r]))))
    pd = np.array(pg.evaluate("[DF1, DF2, DR, POSTER_T]"))
    return dict(worst=worst, same=same, count=count, starts=starts, e_modal=e_modal,
                data=pd, errors=errs)


def states():
    """Every interactive state: solver x start chip x data."""
    out = []
    for kind in SOLVERS:
        for si in range(len(STARTS)):
            for dat in ("f", "fm", "fp", "fmp"):
                out.append((kind, si, dat))
    return out


def check_states(open_):
    """The overlap check (engine.js ?overlap) in every state the chips reach,
    through ?view=, at moments across each run and after it; and a few clicked
    starts."""
    res, errs_all = [], []
    todo = [(f"{k}-{si}-{dat}", k, si, dat) for k, si, dat in states()]
    todo += [("lm-163.7_48.2-f", "lm", -1, "f"), ("pso-57.3_141.9-fp", "pso", -1, "fp"),
             ("gd-201.4_187.6-fm", "gd", -1, "fm"), ("mcmc-163.7_48.2-fmp", "mcmc", -1, "fmp")]
    for view, kind, si, dat in todo:
        pg, errs = open_(f"view={view}&still&overlap")
        d = pg.evaluate("(() => { const r = runOf(scene()); return dur(r); })()")
        run0 = 0.1 + 0.5
        moments = [0.15, run0 + 0.1, run0 + 0.35 * d, run0 + 0.7 * d, run0 + d + 0.6]
        for tt in moments:
            pg.evaluate(f"() => {{ t = {tt:.6g}; render(); }}")
            lab_, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
            res.append((view, round(tt, 3), lab_, cro))
        errs_all += errs
        pg.close()
    return res, errs_all


def check_controls(open_):
    """The page live: no script errors, the intro ends, the clock runs, and each
    control does what it says without pausing the figure."""
    pg, errs = open_("", width=672, dpr=1)
    out = {}
    pg.wait_for_timeout(1600)
    out["playing_after_intro"] = pg.evaluate("playing")
    t1 = pg.evaluate("t"); pg.wait_for_timeout(500); t2 = pg.evaluate("t")
    out["clock_runs"] = t2 > t1
    btns = pg.locator("button.nfm")
    out["buttons"] = btns.count()
    # each chip: click it, the state changes, the figure keeps playing
    seen = []
    for i in range(btns.count()):
        btns.nth(i).click()
        pg.wait_for_timeout(120)
        sc = pg.evaluate("(() => { const s = scene(); return [s.solver, s.si, s.mode, s.prior, playing]; })()")
        seen.append(sc)
    out["after_clicks"] = seen
    # a click on the map: a start there, still playing
    box = pg.locator("canvas").bounding_box()
    u = box["width"] / 1000
    pg.mouse.click(box["x"] + (92 + 0.7 * 420) * u, box["y"] + (146 + 0.6 * 420) * u)
    pg.wait_for_timeout(150)
    out["map_click"] = pg.evaluate("(() => { const s = scene(); return [s.si, s.start, playing]; })()")
    # a click on open ground (the table) still pauses, as in every figure
    pg.mouse.click(box["x"] + 800 * u, box["y"] + 500 * u)
    pg.wait_for_timeout(100)
    out["ground_click_pauses"] = not pg.evaluate("playing")
    # keyboard: the solver group takes arrows
    pg.evaluate("playing || setPlay(true)")
    pg.locator("button.nfm").nth(0).focus()
    pg.keyboard.press("ArrowRight")
    pg.wait_for_timeout(100)
    out["arrow_key"] = pg.evaluate("scene().solver")
    out["status"] = pg.evaluate("document.querySelector('[role=status]').textContent")
    # restart: back to the tour
    pg.evaluate("document.getElementById('rs').click()")
    out["restart_tour"] = pg.evaluate("PICK === null && t < 0.2")
    # frame time over two seconds of the MCMC step of the tour (16,000 samples drawn)
    pg.evaluate("t = 29.5; PICK = null")
    fps = pg.evaluate("""() => new Promise(res => { let n = 0; const t0 = performance.now();
        function f() { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else res(n / 2); }
        requestAnimationFrame(f); })""")
    out["fps_mcmc"] = fps
    out["errors"] = errs
    pg.close()
    return out


def look(times=(), views=(), out=None):
    """PNGs of moments of the tour and of states (?view=), to look at."""
    out = out or tempfile.gettempdir()
    paths = []
    with session() as open_:
        for q, nm in [(f"still&t={x:g}", f"t{x:g}") for x in times] + [(f"view={v}&still&t={x:g}", f"{v}-t{x:g}") for v, x in views]:
            pg, errs = open_(q, dpr=2)
            png = os.path.join(out, f"nf-{NAME}-{nm}.png")
            pg.locator("canvas").screenshot(path=png)
            if errs:
                print("errors", nm, errs)
            paths.append(png)
            pg.close()
    return paths


def main():
    data, res = build()
    png = common.still(NAME)
    print("still:", png)
    validate(data, res)
    if "--look" in sys.argv:
        print(look(times=(0.3, 0.8, 1.4, data["poster"], 12.8, 21.1, 29.75, 35.2, 46.56, 51.2)))


if __name__ == "__main__":
    if "--look-only" in sys.argv:
        print(look(times=[float(x) for x in sys.argv[2:] if not x.startswith("--") and "-" not in x],
                   views=[(v.split("@")[0], float(v.split("@")[1])) for v in sys.argv[2:] if "@" in v]))
    else:
        main()
