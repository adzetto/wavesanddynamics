"""Figure 7 of the signal processing document: the types of optimization problem.

The professor's own animation (optimization_problem_types_animation.html, six
scenes, each with its traits, the methods that solve it and a note) redrawn as
one numfig figure. Each scene is a small problem solved here, exactly, and the
page draws what the solver did:

  1 convex             f(x) = (x - x*)^T A (x - x*)/2, A with eigenvalues 1 and 6
                       (axes turned 30 degrees), x* = (0.8, 0.5); gradient
                       descent x_{k+1} = x_k - eta grad f(x_k), eta = 0.2, 25 steps
                       from three starts.
  2 linear program     his example: maximize 3 x1 + 2 x2 subject to x1 <= 3.5,
                       x1 + x2 <= 4, x1 + 3 x2 <= 6, x >= 0. The tableau simplex
                       (Dantzig's rule) from the origin, vertex to vertex, and the
                       interior point method's central path (the log barrier's
                       maximizer for mu = infinity down to 1e-3), checked against
                       scipy.optimize.linprog.
  3 nonconvex, local   the Styblinski-Tang function f(x) = sum_i (x_i^4 - 16 x_i^2
                       + 5 x_i)/2 on [-5, 5]^2, four minima; gradient descent,
                       eta = 0.01, 30 steps from (0.9, 4.6), stops in a local one.
  4 nonconvex, global  the same function; particle swarm optimization (16
                       particles, constriction coefficients 0.7298 and 1.49618,
                       40 iterations, seeded) finds the global minimum.
  5 constrained        the quadratic of 1 with x1 + x2 <= -2.5; the quadratic
                       penalty F_mu = f + mu max(0, x1 + x2 + 2.5)^2 minimized by
                       Newton's method for mu = 0.1, 1, 10, 100, against SLSQP
                       and the closed form (KKT).
  6 multi-objective    two objectives of the ZDT1 kind, f1 = x1, f2 = g (1 -
                       sqrt(x1/g)), g = 1 + (x2 + x3)/2, 0 <= x <= 1, exact
                       Pareto front f2 = 1 - sqrt(f1); NSGA-II (40 candidates,
                       40 generations, seeded).

Every number the page moves comes from DATA; the page computes only closed
forms (the quadratics' level sets and the penalty's minimizer x(mu)), checked
against these in the check file. No random numbers in the page.

Run: /root/venv312/bin/python tools/numfig/sp_opt_types.py [--verify]
  (writes the page, the still and the check file; prints the key numbers;
   --verify also checks the page's closed forms, runs the overlap check over
   the whole tour and every scene and chip state, and drives the live page;
   pymoo, where installed, runs its own NSGA-II as an independent check)
"""
import os
import sys

import contourpy
import numpy as np
from scipy.optimize import differential_evolution, linprog, minimize

import common

NAME = "sp-opt-types"
W, H = 1000, 640

# ------------------------------------------------------------------ timing (the page's own)
DUR = 8.0          # one scene, s; the tour steps through all six
TA = 0.5           # the solver starts this long into its scene
TDONE = 5.6        # the scene complete: the poster moment

# ------------------------------------------------------------------ 1 and 5: the convex quadratic
THETA = np.deg2rad(30.0)
LAM = np.array([1.0, 6.0])
ROT = np.array([[np.cos(THETA), -np.sin(THETA)], [np.sin(THETA), np.cos(THETA)]])
AQ = ROT @ np.diag(LAM) @ ROT.T
XQ = np.array([0.8, 0.5])                        # its minimum
ETA_Q = 0.2                                      # = 1.2/l_max: the steep direction damped by -0.2
K_Q = 25
STARTS_Q = [(-3.5, 1.7), (3.4, 3.3), (-1.4, -3.5)]
LEVELS_Q = [0.5 * r * r for r in (0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8, 5.4)]


def f_q(x):
    d = np.asarray(x, float) - XQ
    return 0.5 * np.einsum("...i,ij,...j->...", d, AQ, d)


def gd_quadratic(x0, k=K_Q, eta=ETA_Q):
    p = [np.array(x0, float)]
    for _ in range(k):
        p.append(p[-1] - eta * AQ @ (p[-1] - XQ))
    return np.array(p)


# ------------------------------------------------------------------ 2: his linear program
A_LP = np.array([[1.0, 0.0], [1.0, 1.0], [1.0, 3.0]])
B_LP = np.array([3.5, 4.0, 6.0])
C_LP = np.array([3.0, 2.0])
POLY = np.array([[0, 0], [3.5, 0], [3.5, 0.5], [3, 1], [0, 2]], float)
MU_DOTS = [10.0, 1.0, 0.1, 0.01, 0.001]


def simplex(A, b, c):
    """max c^T x subject to A x <= b, x >= 0 (b >= 0): the tableau simplex from the
    origin (the slacks basic), Dantzig's rule (the most negative reduced cost
    enters), the ratio test picks the row that leaves. Returns the vertices
    visited, the objective there and the final tableau's reduced costs."""
    m, n = A.shape
    T = np.zeros((m + 1, n + m + 1))
    T[:m, :n], T[:m, n:n + m], T[:m, -1] = A, np.eye(m), b
    T[m, :n] = -c
    basis = list(range(n, n + m))
    path = [np.zeros(n)]
    while True:
        j = int(np.argmin(T[m, :-1]))
        if T[m, j] >= -1e-12:
            break
        col = T[:m, j]
        ratio = np.where(col > 1e-12, T[:m, -1] / np.where(col > 1e-12, col, 1), np.inf)
        i = int(np.argmin(ratio))
        T[i] /= T[i, j]
        for r in range(m + 1):
            if r != i:
                T[r] -= T[r, j] * T[i]
        basis[i] = j
        x = np.zeros(n)
        for r, bv in enumerate(basis):
            if bv < n:
                x[bv] = T[r, -1]
        path.append(x)
    return np.array(path), T[m, -1], T[m, :-1].copy()


def barrier_max(A, b, c, mu, x):
    """The maximizer of c^T x / mu + sum log(b - A x) (mu = inf: the analytic
    centre), by Newton's method with a backtracking line search that keeps
    every slack positive. A, b hold every inequality (x >= 0 as -x <= 0)."""
    w = 0.0 if np.isinf(mu) else 1.0 / mu
    for _ in range(100):
        s = b - A @ x
        g = w * c - A.T @ (1 / s)                  # gradient of the function maximized
        Hm = A.T @ np.diag(1 / s ** 2) @ A          # minus its Hessian
        dx = np.linalg.solve(Hm, g)
        lam2 = g @ dx
        if lam2 < 1e-26:
            break
        tt = 1.0
        phi = lambda z: w * (c @ z) + np.sum(np.log(b - A @ z))
        while np.any(b - A @ (x + tt * dx) <= 0) or phi(x + tt * dx) < phi(x) + 0.25 * tt * lam2:
            tt *= 0.5
        x = x + tt * dx
    return x


def central_path():
    Aall = np.vstack([A_LP, -np.eye(2)])
    ball = np.r_[B_LP, 0.0, 0.0]
    x = barrier_max(Aall, ball, C_LP, np.inf, np.array([1.0, 0.5]))
    centre = x.copy()
    mus = np.r_[np.logspace(2.5, -3, 111)]
    pts, gaps = [centre], []
    for mu in mus:
        x = barrier_max(Aall, ball, C_LP, mu, x)
        pts.append(x.copy())
        s = ball - Aall @ x
        lam = mu / s                               # the dual point on the path
        gaps.append((mu, ball @ lam - C_LP @ x, np.abs(Aall.T @ lam - C_LP).max()))
    dots, x = [], centre.copy()
    for mu in MU_DOTS:                             # path following: each from the last
        x = barrier_max(Aall, ball, C_LP, mu, x)
        dots.append(x.copy())
    return centre, np.array(pts), np.array(dots), gaps


# ------------------------------------------------------------------ 3 and 4: Styblinski-Tang
LO, HI = -5.0, 5.0
START_ST = (0.9, 4.6)
ETA_ST = 0.01
K_ST = 30
LEVELS_ST = [-76, -70, -62, -54, -46, -38, -30, -22, -14, -5, 10, 40, 90, 160]
PSO_N, PSO_IT, PSO_W, PSO_C, PSO_VMAX = 16, 40, 0.7298, 1.49618, 2.0


def f_st(x):
    x = np.asarray(x, float)
    return 0.5 * np.sum(x ** 4 - 16 * x ** 2 + 5 * x, axis=-1)


def g_st(x):
    return 2 * x ** 3 - 16 * x + 2.5


def st_critical():
    """The three critical points of one coordinate's x^4 - 16 x^2 + 5 x, the roots
    of 4 x^3 - 32 x + 5, in closed form (trigonometric: three real roots)."""
    p, q = -8.0, 1.25                               # x^3 + p x + q = 0
    m = 2 * np.sqrt(-p / 3)
    th = np.arccos(3 * q / (p * m)) / 3
    return np.sort(m * np.cos(th - 2 * np.pi * np.arange(3) / 3))


def gd_st():
    p = [np.array(START_ST, float)]
    for _ in range(K_ST):
        p.append(p[-1] - ETA_ST * g_st(p[-1]))
    return np.array(p)


def pso(seed, n=PSO_N, iters=PSO_IT):
    """Global best particle swarm (Kennedy and Eberhart; Clerc's constriction
    coefficients): v <- w v + c r1 (p - x) + c r2 (g - x), |v| <= vmax per
    coordinate, x kept in the box. Returns every iterate."""
    rng = np.random.default_rng(seed)
    x = rng.uniform(LO, HI, (n, 2))
    v = rng.uniform(-1, 1, (n, 2))
    f = f_st(x)
    pb, pf = x.copy(), f.copy()
    j = int(np.argmin(pf))
    g, gf = pb[j].copy(), pf[j]
    X, G, GF = [x.copy()], [g.copy()], [gf]
    for _ in range(iters):
        r1, r2 = rng.random((n, 2)), rng.random((n, 2))
        v = PSO_W * v + PSO_C * r1 * (pb - x) + PSO_C * r2 * (g - x)
        v = np.clip(v, -PSO_VMAX, PSO_VMAX)
        x = np.clip(x + v, LO, HI)
        f = f_st(x)
        better = f < pf
        pb[better], pf[better] = x[better], f[better]
        j = int(np.argmin(pf))
        if pf[j] < gf:
            g, gf = pb[j].copy(), pf[j]
        X.append(x.copy())
        G.append(g.copy())
        GF.append(gf)
    return np.array(X), np.array(G), np.array(GF)


def pick_pso_seed(xg, tries=200, outside=5):
    """The first seed whose best particle stays outside the global minimum's basin
    (a coordinate above the barrier at 0.157) for the first `outside` iterations
    and that still ends at the global minimum: a run in which the swarm is drawn
    to a local basin first and has to find the global one. Also: how many of
    `tries` seeds end at the global minimum, and how many of those start with a
    best particle already in its basin."""
    barrier = st_critical()[1]
    chosen, found, inside0 = None, 0, 0
    for s in range(tries):
        X, G, GF = pso(s)
        ok = bool(np.linalg.norm(G[-1] - xg) < 1e-2)
        found += ok
        inb = np.all(G < barrier, axis=1)
        inside0 += ok and bool(inb[0])
        if chosen is None and ok and not inb[:outside].any():
            chosen = s
    return chosen, found, inside0


def st_contours():
    xs = np.linspace(LO, HI, 401)
    Xg, Yg = np.meshgrid(xs, xs)
    Z = f_st(np.stack([Xg, Yg], -1))
    gen = contourpy.contour_generator(xs, xs, Z)
    out = []
    for li, L in enumerate(LEVELS_ST):
        for seg in gen.lines(L):
            pts = rdp(np.asarray(seg), 0.006)
            if len(pts) >= 2:
                out.append((li, pts))
    return out


def rdp(p, eps):
    """Ramer-Douglas-Peucker: the polyline within eps (data units) of p."""
    if len(p) < 3:
        return p
    a, b = p[0], p[-1]
    ab = b - a
    L = np.hypot(*ab)
    if L < 1e-12:
        d = np.hypot(*(p - a).T)
    else:
        d = np.abs(ab[0] * (p[:, 1] - a[1]) - ab[1] * (p[:, 0] - a[0])) / L
    i = int(np.argmax(d))
    if d[i] > eps:
        left, right = rdp(p[:i + 1], eps), rdp(p[i:], eps)
        return np.vstack([left[:-1], right])
    return np.vstack([a, b])


# ------------------------------------------------------------------ 5: the quadratic penalty
A_C = np.array([1.0, 1.0])
B_C = -2.5
MUS = [0.1, 1.0, 10.0, 100.0]


def penalty_closed(mu):
    """argmin f + mu max(0, a^T x - b)^2 in closed form: on the infeasible side
    (where the minimizer lies for every finite mu) the penalized function is the
    quadratic with Hessian A + 2 mu a a^T, so x(mu) solves
    (A + 2 mu a a^T) x = A xq + 2 mu b a."""
    Hm = AQ + 2 * mu * np.outer(A_C, A_C)
    return np.linalg.solve(Hm, AQ @ XQ + 2 * mu * B_C * A_C)


def penalty_newton(mus=MUS):
    """The penalty method as it runs: for each mu, Newton's method on the
    piecewise quadratic F_mu from the previous solution (the first from the
    unconstrained minimum), to a gradient below 1e-12. Returns the solutions and
    the Newton steps each took."""
    x = XQ.copy()
    sols, steps = [], []
    for mu in mus:
        for k in range(50):
            gap = A_C @ x - B_C
            g = AQ @ (x - XQ) + 2 * mu * max(gap, 0) * A_C
            if np.abs(g).max() < 1e-12:
                break
            Hm = AQ + (2 * mu * np.outer(A_C, A_C) if gap > 0 else 0)
            x = x - np.linalg.solve(Hm, g)
        sols.append(x.copy())
        steps.append(k)
    return np.array(sols), steps


def kkt_closed():
    Ai = np.linalg.inv(AQ)
    q = A_C @ Ai @ A_C
    lam = (A_C @ XQ - B_C) / q
    return XQ - lam * Ai @ A_C, lam, q


# ------------------------------------------------------------------ 6: two objectives, NSGA-II
NS_N, NS_G, NS_PC, NS_EC, NS_EM = 40, 40, 0.9, 15.0, 20.0
NS_NV = 3                                         # variables
NS_PM = 1.0 / NS_NV


def zdt(X):
    """f1 = x1, f2 = g (1 - sqrt(x1/g)), g = 1 + the mean of x2 .. xn (ZDT1's
    construction; ZDT1 itself takes g = 1 + 9 mean, whose f2 reaches 10)."""
    f1 = X[:, 0]
    g = 1 + X[:, 1:].mean(1)
    return np.stack([f1, g * (1 - np.sqrt(f1 / g))], 1)


def nondominated_sort(F):
    """Deb's fast non-dominated sort: the front (0, 1, ...) of each row of F."""
    n = len(F)
    dom = [[] for _ in range(n)]
    cnt = np.zeros(n, int)
    for i in range(n):
        for j in range(n):
            if i != j:
                if np.all(F[i] <= F[j]) and np.any(F[i] < F[j]):
                    dom[i].append(j)
                elif np.all(F[j] <= F[i]) and np.any(F[j] < F[i]):
                    cnt[i] += 1
    rank = np.full(n, -1)
    cur = [i for i in range(n) if cnt[i] == 0]
    r = 0
    while cur:
        nxt = []
        for i in cur:
            rank[i] = r
            for j in dom[i]:
                cnt[j] -= 1
                if cnt[j] == 0:
                    nxt.append(j)
        cur, r = nxt, r + 1
    return rank


def crowding(F, idx):
    d = np.zeros(len(idx))
    if len(idx) <= 2:
        return np.full(len(idx), np.inf)
    for m in range(F.shape[1]):
        o = np.argsort(F[idx, m], kind="stable")
        fm = F[idx[o], m]
        d[o[0]] = d[o[-1]] = np.inf
        span = fm[-1] - fm[0]
        if span > 0:
            d[o[1:-1]] += (fm[2:] - fm[:-2]) / span
    return d


def sbx(p1, p2, rng):
    """Simulated binary crossover (Deb and Agrawal), eta_c = 15, then kept in [0, 1]."""
    u = rng.random(p1.shape)
    beta = np.where(u <= 0.5, (2 * u) ** (1 / (NS_EC + 1)), (1 / (2 * (1 - u))) ** (1 / (NS_EC + 1)))
    c1 = 0.5 * ((1 + beta) * p1 + (1 - beta) * p2)
    c2 = 0.5 * ((1 - beta) * p1 + (1 + beta) * p2)
    return np.clip(c1, 0, 1), np.clip(c2, 0, 1)


def poly_mutation(x, rng):
    """Deb's polynomial mutation with bounds [0, 1], eta_m = 20, each variable with
    probability 1/n."""
    x = x.copy()
    for i in range(len(x)):
        if rng.random() < NS_PM:
            u = rng.random()
            d1, d2 = x[i], 1 - x[i]
            if u < 0.5:
                dq = (2 * u + (1 - 2 * u) * (1 - d1) ** (NS_EM + 1)) ** (1 / (NS_EM + 1)) - 1
            else:
                dq = 1 - (2 * (1 - u) + 2 * (u - 0.5) * (1 - d2) ** (NS_EM + 1)) ** (1 / (NS_EM + 1))
            x[i] = np.clip(x[i] + dq, 0, 1)
    return x


def nsga2(seed):
    """NSGA-II (Deb, Pratap, Agarwal and Meyarivan 2002): binary tournaments on
    (front, crowding distance), SBX crossover with probability 0.9, polynomial
    mutation, and the elitist selection of the best N of parents and children
    by front and crowding. Each candidate keeps its id while it survives.
    Returns the generations (ids, fronts) and every candidate's objectives."""
    rng = np.random.default_rng(seed)
    X = rng.random((NS_N, NS_NV))
    F = zdt(X)
    ids = np.arange(NS_N)
    table = {int(i): F[k] for k, i in enumerate(ids)}
    nxt = NS_N
    gens = [(ids.copy(), nondominated_sort(F))]
    for _ in range(NS_G):
        rank = nondominated_sort(F)
        cd = np.zeros(NS_N)
        for r in range(rank.max() + 1):
            idx = np.where(rank == r)[0]
            cd[idx] = crowding(F, idx)

        def tour():
            a, b = rng.integers(0, NS_N, 2)
            if rank[a] != rank[b]:
                return a if rank[a] < rank[b] else b
            return a if cd[a] >= cd[b] else b

        kids = []
        while len(kids) < NS_N:
            p1, p2 = X[tour()], X[tour()]
            if rng.random() < NS_PC:
                c1, c2 = sbx(p1, p2, rng)
            else:
                c1, c2 = p1.copy(), p2.copy()
            kids += [poly_mutation(c1, rng), poly_mutation(c2, rng)]
        Xo = np.array(kids[:NS_N])
        Fo = zdt(Xo)
        ido = np.arange(nxt, nxt + NS_N)
        nxt += NS_N
        Xc, Fc, idc = np.vstack([X, Xo]), np.vstack([F, Fo]), np.r_[ids, ido]
        rc = nondominated_sort(Fc)
        keep = []
        for r in range(rc.max() + 1):
            idx = np.where(rc == r)[0]
            if len(keep) + len(idx) <= NS_N:
                keep += list(idx)
            else:
                d = crowding(Fc, idx)
                o = np.argsort(-d, kind="stable")
                keep += list(idx[o[:NS_N - len(keep)]])
                break
        keep = np.array(keep)
        X, F, ids = Xc[keep], Fc[keep], idc[keep]
        for k, i in enumerate(ids):
            table[int(i)] = F[k]
        gens.append((ids.copy(), nondominated_sort(F)))
    return gens, table, X, F


def hypervolume(F, ref=(1.0, 1.0)):
    """The area the points dominate inside the reference box (two objectives)."""
    P = F[(F[:, 0] < ref[0]) & (F[:, 1] < ref[1])]
    P = P[np.argsort(P[:, 0])]
    hv, best = 0.0, ref[1]
    xs = np.r_[P[:, 0], ref[0]]
    for k in range(len(P)):
        best = min(best, P[k, 1])
        hv += (xs[k + 1] - xs[k]) * (ref[1] - best)
    return hv


# ------------------------------------------------------------------ the page
JS = r"""
const D = DATA;
const DUR = D.dur, TA = D.ta, TDONE = D.tdone, POSTER_T = TDONE;
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);

/* ================================================ the six scenes, in his order and his terms */
const SC = [
  {chip: 'convex', tags: [0, 1, 1, 2, 0], lim: [[-4, 4], [-4, 4]], tk: [[-4, -2, 0, 2, 4], [-4, -2, 0, 2, 4]], ax: ['x_1', 'x_2'],
   head: 'f(x) = (x - x^{*})^{⊤}A\\,(x - x^{*})/2',
   methods: [['gradient descent', 'path'], ['Newton’s method'], ['conjugate gradient'], ['stochastic gradient descent']],
   params: [['t', 'eigenvalues of '], ['m', 'A'], ['t', ': 1 and 6, '], ['m', 'x^{*} = (0.8,\\ 0.5)'], ['t', ';   gradient descent '],
            ['m', 'x_{k+1} = x_k - \\eta∇f(x_k)\\rm{, }\\eta\\ = 0.2'], ['t', ', 25 steps from three starts']]},
  {chip: 'linear program', tags: [0, 0, 0, 2, 0], lim: [[0, 4], [0, 4]], tk: [[0, 1, 2, 3, 4], [0, 1, 2, 3, 4]], ax: ['x_1', 'x_2'],
   head: '\\rm{maximize }3x_1 + 2x_2',
   methods: [['simplex method', 'path'], ['interior point method', 'dash']],
   params: [['t', 'subject to '], ['m', 'x_1 ≤ 3.5,\\ \\ x_1 + x_2 ≤ 4,\\ \\ x_1 + 3x_2 ≤ 6,\\ \\ x_1, x_2 ≥ 0'],
            ['t', ';   simplex from the origin;   central path '], ['m', '\\mu\\ = ∞'], ['t', ' to 0.001']]},
  {chip: 'nonconvex, local', tags: [1, 1, 1, 0, 0], lim: [[-5, 5], [-5, 5]], tk: [[-4, -2, 0, 2, 4], [-4, -2, 0, 2, 4]], ax: ['x_1', 'x_2'],
   head: 'f(x) = \\Sigma_{i}\\,(x_i^4 - 16x_i^2 + 5x_i)/2',
   methods: [['gradient descent', 'path'], ['Newton’s method'], ['conjugate gradient'], ['stochastic gradient descent']],
   params: [['t', 'the Styblinski-Tang function, four minima;   gradient descent, '], ['m', '\\eta\\ = 0.01'], ['t', ', 30 steps from (0.9, 4.6)']]},
  {chip: 'nonconvex, global', tags: [1, 1, 1, 1, 0], lim: [[-5, 5], [-5, 5]], tk: [[-4, -2, 0, 2, 4], [-4, -2, 0, 2, 4]], ax: ['x_1', 'x_2'],
   head: 'f(x) = \\Sigma_{i}\\,(x_i^4 - 16x_i^2 + 5x_i)/2',
   methods: [['particle swarm optimization', 'swarm'], ['genetic algorithm'], ['simulated annealing'], ['ant colony optimization']],
   params: [['t', 'particle swarm: ' + D.pso.n + ' particles, inertia 0.7298, '], ['m', 'c_1 = c_2 = 1.49618'],
            ['t', ', ' + D.pso.it + ' iterations, seed ' + D.pso.seed + ';   open circles: where they started']]},
  {chip: 'constrained', tags: [0, 1, 0, 2, 0], lim: [[-4, 4], [-4, 4]], tk: [[-4, -2, 0, 2, 4], [-4, -2, 0, 2, 4]], ax: ['x_1', 'x_2'],
   head: '\\rm{minimize }f(x)\\rm{ subject to }x_1 + x_2 ≤ -2.5',
   methods: [['quadratic penalty', 'path'], ['+ Newton’s method'], ['+ gradient descent']],
   params: [['m', 'f'], ['t', ' of the convex scene;   '], ['m', 'F_{\\mu} = f + \\mu\\ \\rm{max}(0,\\ x_1 + x_2 + 2.5)^2\\rm{, }\\mu\\ = 0.1,\\ 1,\\ 10,\\ 100'],
            ['t', ', each minimized by Newton’s method;   dashed: '], ['m', 'f']]},
  {chip: 'multi-objective', tags: [0, 1, 0, 2, 1], lim: [[0, 1], [0, 2.2]], tk: [[0, .25, .5, .75, 1], [0, .5, 1, 1.5, 2]], ax: ['f_1', 'f_2'],
   head: '\\rm{minimize }f_1 = x_1\\rm{ and }f_2 = g\\,(1 - \\sqrt{x_1/g})',
   methods: [['NSGA-II', 'front'], ['other evolutionary algorithms']],
   params: [['m', 'g = 1 + (x_2 + x_3)/2\\rm{, }0 ≤ x_i ≤ 1'], ['t', ';   NSGA-II: ' + D.ns.n + ' candidates, ' + D.ns.g + ' generations, seed ' + D.ns.seed]]},
];
const ROWS = [['(i)', 'convex', 'nonconvex'], ['(ii)', 'linear', 'nonlinear'], ['(iii)', 'constrained', 'unconstrained'],
              ['(iv)', 'local', 'global'], ['', 'one objective', 'two objectives']];

/* ================================================ the reader's choice, and the tour */
/* SEL: a scene chosen {i, t0, prev}; null: the tour from the first. ?view=N (1 to 6)
   starts the tour at scene N, for the overlap check of every scene; absent, nothing. */
const VIEW = (() => { const m = /[?&]view=(\d+)/.exec(location.search), v = m ? +m[1] : 0; return v >= 1 && v <= 6 ? v - 1 : -1; })();
let SEL = null, HC = -1, HD = -1;
function reset() { SEL = VIEW >= 0 ? {i: VIEW, t0: 0, prev: -1} : null; HC = HD = -1; sync(); }
function now() {
  const t0 = SEL ? SEL.t0 : 0, i0 = SEL ? SEL.i : 0, u = Math.max(0, t - t0), k = Math.floor(u / DUR);
  const i = (i0 + k) % 6, tau = u - k * DUR;
  return {i, tau, st: t - tau, prev: k > 0 ? (i + 5) % 6 : SEL ? SEL.prev : -1, intro: !SEL && k === 0};
}

/* ================================================ layout */
const FP = {x: 86, y: 62, w: 466, h: 466};
const RX = 612, XA = 662, XB = 812;
const CH = {x: 612, y: 56, w: 180, h: 34, gx: 12, py: 44};
const YT = 222, YR = [254, 284, 314, 344, 382], YM = 428, YMI = 460, PM = 29;
const chipXY = j => [CH.x + (j % 2) * (CH.w + CH.gx), CH.y + Math.floor(j / 2) * CH.py];
function tw(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
/* a chip as the engine's uiChip draws it, with its type at 17 (the column has the room) */
function chip(x, y, w, h, label, st, a) {
  const fill = st.on ? C.navy : st.down ? C.steel2 : st.hover ? C.steel : '#fff';
  const edge = st.on || st.hover || st.down ? C.navy : C.guide;
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], {color: edge, width: 1, fill, close: true, alpha: a});
  text(label, x + w / 2, y + h / 2 + 6, {size: 17, align: 'center', alpha: a, color: st.on ? '#fff' : st.hover ? C.ink : C.body});
}

/* ================================================ closed forms the page computes */
/* a symmetric 2 x 2 matrix's eigen pairs, the smaller first */
function eig2(a, b, d) {
  const m = (a + d) / 2, r = Math.hypot((a - d) / 2, b), l1 = m - r, l2 = m + r;
  let vx = b, vy = l1 - a;
  if (Math.hypot(vx, vy) < 1e-14) { vx = a <= d ? 1 : 0; vy = a <= d ? 0 : 1; }
  const n = Math.hypot(vx, vy); vx /= n; vy /= n;
  return {l1, l2, v1: [vx, vy], v2: [-vy, vx]};
}
/* the level set {F0 + (x - m)^T H (x - m)/2 = L} (H = [h11, h12, h22]) as points, the
   whole ellipse, or only its part on one side of the line a^T x = b (side -1: a^T x <= b,
   +1: >=), the arc's ends exactly on the line */
function levelArc(H, m, F0, L, side, a, b, n) {
  if (L <= F0) return null;
  const E = eig2(H[0], H[1], H[2]), r = Math.sqrt(2 * (L - F0)), s1 = r / Math.sqrt(E.l1), s2 = r / Math.sqrt(E.l2);
  const P = p => [m[0] + s1 * Math.cos(p) * E.v1[0] + s2 * Math.sin(p) * E.v2[0], m[1] + s1 * Math.cos(p) * E.v1[1] + s2 * Math.sin(p) * E.v2[1]];
  let p0 = 0, p1 = 2 * Math.PI;
  if (side) {
    const al = s1 * (a[0] * E.v1[0] + a[1] * E.v1[1]), be = s2 * (a[0] * E.v2[0] + a[1] * E.v2[1]);
    const rho = Math.hypot(al, be), ph = Math.atan2(be, al), k = (b - a[0] * m[0] - a[1] * m[1]) / rho;
    // a^T x(p) = a^T m + rho cos(p - ph)
    if (side < 0) { if (k <= -1) return null; if (k < 1) { const c = Math.acos(k); p0 = ph + c; p1 = ph + 2 * Math.PI - c; } }
    else { if (k >= 1) return null; if (k > -1) { const c = Math.acos(k); p0 = ph - c; p1 = ph + c; } }
  }
  const out = [];
  for (let j = 0; j <= n; j++) out.push(P(p0 + (p1 - p0) * j / n));
  return out;
}
/* A = R diag(l1, l2) R^T, R turning theta: [a11, a12, a22]; and the minimum */
const AQ = (() => { const th = D.q.theta * Math.PI / 180, c = Math.cos(th), s = Math.sin(th), [l1, l2] = D.q.lam;
  return [l1 * c * c + l2 * s * s, (l1 - l2) * c * s, l1 * s * s + l2 * c * c]; })();
const XQ = D.q.xs;
/* the penalty's minimizer: (A + 2 mu a a^T) x = A xq + 2 mu b a, and F_mu there */
function penX(mu) {
  const a = D.c.a, b = D.c.b;
  const h11 = AQ[0] + 2 * mu * a[0] * a[0], h12 = AQ[1] + 2 * mu * a[0] * a[1], h22 = AQ[2] + 2 * mu * a[1] * a[1];
  const r0 = AQ[0] * XQ[0] + AQ[1] * XQ[1] + 2 * mu * b * a[0], r1 = AQ[1] * XQ[0] + AQ[2] * XQ[1] + 2 * mu * b * a[1];
  const det = h11 * h22 - h12 * h12;
  return [(h22 * r0 - h12 * r1) / det, (h11 * r1 - h12 * r0) / det];
}
function fq(x) { const d0 = x[0] - XQ[0], d1 = x[1] - XQ[1]; return (AQ[0] * d0 * d0 + 2 * AQ[1] * d0 * d1 + AQ[2] * d1 * d1) / 2; }
function Fmu(x, mu) { const g = D.c.a[0] * x[0] + D.c.a[1] * x[1] - D.c.b; return fq(x) + mu * Math.max(0, g) ** 2; }
const fst = x => .5 * ((x[0] ** 4 - 16 * x[0] ** 2 + 5 * x[0]) + (x[1] ** 4 - 16 * x[1] ** 2 + 5 * x[1]));
const ZDT = f1 => 1 - Math.sqrt(f1);                  // the exact Pareto front

/* ================================================ the drawn pieces */
const ST_LINES = (() => { const c = b64f32(D.st.xy), out = []; let o = 0;
  for (const [lv, n] of D.st.lines) { const p = []; for (let j = 0; j < n; j++) p.push([c[o + 2 * j], c[o + 2 * j + 1]]); o += 2 * n; out.push(p); }
  return out; })();
function contoursST(A, a, pr) {
  A.inside(() => { for (const p of ST_LINES) line(p.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.mist, width: 1.1, alpha: a, progress: pr}); });
}
function contoursQ(A, a, pr, mu) {          // f's level sets; with mu, F_mu's (the feasible part is f's)
  const L = D.q.levels;
  A.inside(() => {
    for (const lv of L) {
      if (mu === undefined) { const p = levelArc(AQ, XQ, 0, lv, 0, null, 0, 160); if (p) line(p.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.mist, width: 1.1, alpha: a, progress: pr}); continue; }
      const a_ = D.c.a, b_ = D.c.b, m = penX(mu);
      const Hm = [AQ[0] + 2 * mu * a_[0] * a_[0], AQ[1] + 2 * mu * a_[0] * a_[1], AQ[2] + 2 * mu * a_[1] * a_[1]];
      const pf = levelArc(AQ, XQ, 0, lv, -1, a_, b_, 140), pi = levelArc(Hm, m, Fmu(m, mu), lv, 1, a_, b_, 140);
      const po = levelArc(AQ, XQ, 0, lv, 1, a_, b_, 140);
      if (po && mu > 0) line(po.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.steel2, width: 1, dash: [3, 3], alpha: a});
      if (pf) line(pf.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.mist, width: 1.1, alpha: a});
      if (pi) line(pi.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.mist, width: 1.1, alpha: a});
    }
  });
}
/* an iterative run: the chords of its steps, a dot at each iterate, the start open, the
   marker gliding from iterate k to k + 1 */
function run(A, P, k, s, a, o = {}) {
  const K = P.length - 1, kk = Math.min(k, K), col = o.col || C.blue;
  const pts = []; for (let j = 0; j <= kk; j++) pts.push([A.X(P[j][0]), A.Y(P[j][1])]);
  const at = kk < K ? [lerp(P[kk][0], P[kk + 1][0], s), lerp(P[kk][1], P[kk + 1][1], s)] : P[K];
  pts.push([A.X(at[0]), A.Y(at[1])]);
  line(pts, {color: col, width: 1.5, alpha: a * .9});
  for (let j = 1; j <= kk; j++) dot(A.X(P[j][0]), A.Y(P[j][1]), 2.4, {color: col, fill: col, width: .8, alpha: a});
  dot(A.X(P[0][0]), A.Y(P[0][1]), 5, {color: C.navy, fill: '#fff', width: 1.6, alpha: a});
  dot(A.X(at[0]), A.Y(at[1]), 5.6, {color: '#fff', fill: C.navy, width: 1.6, alpha: a});
}
/* where a stepped run is: iterate k and the glide s to the next, one step every `step` s */
function stepAt(S, t0, step, K) {
  const u = S.tau - t0; if (u < 0) return {k: 0, s: 0, on: false};
  const k = Math.floor(u / step); if (k >= K) return {k: K, s: 0, on: true};
  return {k, s: settle(S.st + t0 + k * step, step * .8), on: true};
}
/* a label with a white ground under it, so a pale level line never runs through it */
function tag(s, x, y, o = {}) {
  const size = o.size || 16, w = o.m ? math(s, 0, -1e4, {size, alpha: 0}) : tw(s, size), al = o.align || 'left';
  const x0 = al === 'center' ? x - w / 2 : al === 'right' ? x - w : x;
  ctx.save(); ctx.globalAlpha *= (o.alpha === undefined ? 1 : o.alpha); ctx.fillStyle = '#fff'; ctx.fillRect(x0 - 3, y - size * .78, w + 6, size * 1.08); ctx.restore();
  return o.m ? math(s, x, y, {size, align: al, color: o.color || C.body, alpha: o.alpha}) : text(s, x, y, {size, align: al, color: o.color || C.body, alpha: o.alpha});
}
function minMark(A, p, a, glob) {
  if (glob) dot(A.X(p[0]), A.Y(p[1]), 6, {color: '#fff', fill: C.accent, width: 1.6, alpha: a});
  else dot(A.X(p[0]), A.Y(p[1]), 4.6, {color: C.ink, fill: '#fff', width: 1.3, alpha: a});
}

/* ================================================ scene 1: convex */
function scene1(A, S, a) {
  contoursQ(A, a, seg(S.st + .05, .45));
  const st = stepAt(S, TA, .16, D.q.k);
  for (const P of D.q.runs) run(A, P, st.k, st.s, a * seg(S.st + .3, .2));
  const la = lab(S.st + TA + .16 * D.q.k + .1) * a, x = A.X(XQ[0]), y = A.Y(XQ[1]);
  minMark(A, XQ, la, true);
  line([[x + 8, y + 7], [x + 44, y + 40]], {color: C.guide, width: 1, alpha: la});
  tag('global minimum', x + 48, y + 54 + rise(la), {color: C.accent, alpha: la});
  return {head: `k = ${st.on ? st.k : 0}`};
}
/* ================================================ scene 2: his linear program */
function scene2(A, S, a) {
  const P = D.lp.poly.map(q => [A.X(q[0]), A.Y(q[1])]);
  line(P, {color: C.ink, width: 1.6, fill: C.steel, close: true, alpha: a * seg(S.st + .05, .3)});
  // the simplex: vertex to vertex, each pivot a glide along an edge
  const V = D.lp.simplex, GL = [1.0, .7], HOLD = .25;
  let pos = V[0], seg_ = 0;
  for (let j = 0; j < V.length - 1; j++) {
    const s0 = TA + j * (GL[0] + HOLD), g = S.tau < s0 ? 0 : settle(S.st + s0, GL[j] * .85);
    if (S.tau >= s0) { pos = [lerp(V[j][0], V[j + 1][0], g), lerp(V[j][1], V[j + 1][1], g)]; seg_ = j + g; }
  }
  const cv_ = D.lp.c[0] * pos[0] + D.lp.c[1] * pos[1], la0 = lab(S.st + .25) * a;
  // the level lines passed (3 x1 + 2 x2 = 2, 4, ...) and the one through the simplex's point
  A.inside(() => {
    for (const lv of [2, 4, 6, 8, 10]) if (cv_ >= lv) line([[A.X(0), A.Y(lv / 2)], [A.X(4), A.Y((lv - 12) / 2)]], {color: C.guide, width: 1, dash: [5, 4], alpha: a * .8});
    if (S.tau >= TA) line([[A.X(0), A.Y(cv_ / 2)], [A.X(4), A.Y((cv_ - 12) / 2)]], {color: C.blue, width: 1.6, dash: [7, 4], alpha: a});
  });
  // the objective's direction, across the level lines
  arrow(A.X(.42), A.Y(2.62), A.X(1.02), A.Y(3.02), {color: C.ink, width: 1.3, head: 9, alpha: la0});
  // the path walked so far
  const walked = [V[0]]; for (let j = 1; j < V.length && j <= Math.floor(seg_); j++) walked.push(V[j]);
  walked.push(pos);
  line(walked.map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.navy, width: 2.4, alpha: a});
  for (let j = 0; j < V.length && j <= Math.floor(seg_); j++) dot(A.X(V[j][0]), A.Y(V[j][1]), 3.2, {color: C.navy, fill: C.navy, alpha: a});
  // the interior point method's central path, from the analytic centre to the same vertex
  const tc = TA + (V.length - 1) * (GL[0] + HOLD) + .1, pr = seg(S.st + tc, .9);
  if (pr > 0) {
    const cp = D.lp.central.map(q => [A.X(q[0]), A.Y(q[1])]);
    line(cp, {color: C.blue, width: 2, dash: [6, 4], alpha: a, progress: pr});
    dot(cp[0][0], cp[0][1], 4.4, {color: C.blue, fill: '#fff', width: 1.5, alpha: a});
    D.lp.dots.forEach((q, j) => { if (pr > .3 + .14 * j) dot(A.X(q[0]), A.Y(q[1]), 2.8, {color: C.blue, fill: C.blue, alpha: a}); });
  }
  dot(A.X(pos[0]), A.Y(pos[1]), 5.6, {color: '#fff', fill: C.navy, width: 1.6, alpha: a * (S.tau >= TA ? 1 : 0)});
  const la = lab(S.st + TA + (V.length - 1) * (GL[0] + HOLD) - .1) * a, xo = D.lp.opt;
  minMark(A, xo, la, true);
  // the labels last, each on its own white ground
  tag('feasible region', A.X(1.0), A.Y(1.22), {align: 'center', alpha: la0, size: 17});
  tag('objective increases', A.X(.3), A.Y(3.3) - rise(la0), {alpha: la0});
  tag('optimum at a vertex', A.X(3.4), A.Y(.2) - rise(la), {align: 'right', color: C.accent, alpha: la});
  return {head: `3x_1 + 2x_2 = ${cv_.toFixed(1)}`};
}
/* ================================================ scene 3: nonconvex, a local search */
function scene3(A, S, a, o) {
  contoursST(A, o.keepOut ? o.fin : a, o.keepIn ? 1 : seg(S.st + .05, .45));
  const st = stepAt(S, TA, .13, D.st.k);
  run(A, D.st.run, st.k, st.s, a * seg(S.st + .3, .2));
  const end = D.st.run[D.st.k], la = lab(S.st + TA + .13 * D.st.k + .1) * a, lb = lab(S.st + TA + .13 * D.st.k + .4) * a;
  for (const m of D.st.minima.slice(1)) if (m !== D.st.minima[3]) minMark(A, m, lb, false);
  tag('local minimum', A.X(end[0]) + 12, A.Y(end[1]) + 26 + rise(la), {alpha: la});
  minMark(A, D.st.minima[0], lb, true);
  tag('global minimum', A.X(D.st.minima[0][0]), A.Y(D.st.minima[0][1]) + 30 + rise(lb), {align: 'center', color: C.accent, alpha: lb});
  return {head: `k = ${st.on ? st.k : 0}`};
}
/* ================================================ scene 4: the same function, a swarm */
function scene4(A, S, a, o) {
  contoursST(A, o.keepIn ? o.fout : a, o.keepIn ? 1 : seg(S.st + .05, .45));
  const X = D.pso.X, n = D.pso.n, IT = D.pso.it, step = .1;
  const st = stepAt(S, TA, step, IT), k = st.k, s = st.s;
  const pa = a * seg(S.st + .15, .25);
  for (let j = 0; j < n; j++) dot(A.X(X[0][j][0]), A.Y(X[0][j][1]), 3.2, {color: C.sky, fill: '#fff', width: 1.1, alpha: pa * (k > 0 || s > .05 ? .8 : 0)});
  for (let j = 0; j < n; j++) {
    const p0 = X[k][j], p1 = k < IT ? X[k + 1][j] : p0, at = [lerp(p0[0], p1[0], s), lerp(p0[1], p1[1], s)];
    const prev = k > 0 ? X[k - 1][j] : p0;
    if (k > 0 || s > 0) line([[A.X(prev[0]), A.Y(prev[1])], [A.X(p0[0]), A.Y(p0[1])], [A.X(at[0]), A.Y(at[1])]], {color: C.sky, width: 1.1, alpha: pa * .8});
    dot(A.X(at[0]), A.Y(at[1]), 3.6, {color: '#fff', fill: C.blue, width: 1, alpha: pa});
  }
  const g = D.pso.G[Math.min(IT, k + (s > .5 ? 1 : 0))];
  dot(A.X(g[0]), A.Y(g[1]), 7.5, {color: C.accent, fill: null, width: 1.8, alpha: pa});
  const lb = lab(S.st + TA + step * IT + .1) * a, gm = D.st.minima[0];
  minMark(A, gm, lb, true);
  tag('global minimum', A.X(gm[0]), A.Y(gm[1]) + 32 + rise(lb), {align: 'center', color: C.accent, alpha: lb});
  return {head: `\\rm{iteration}\\ ${st.on ? k : 0}`};
}
/* ================================================ scene 5: constrained, a quadratic penalty */
function scene5(A, S, a) {
  const a_ = D.c.a, b_ = D.c.b, MU = D.c.mus;
  // the feasible half plane inside the box: x1 + x2 <= -2
  const fe = [[-4, -4], [-4, b_ + 4], [b_ + 4, -4]].map(q => [A.X(q[0]), A.Y(q[1])]);
  line(fe, {color: C.steel, width: 1, fill: C.steel, close: true, alpha: a * seg(S.st + .05, .3)});
  // mu: 0, then each outer iteration's value, gliding in log mu
  const T1 = TA, PER = .95, GLIDE = .6;
  let mu = 0, kdone = -1;
  for (let j = 0; j < MU.length; j++) {
    const s0 = T1 + j * PER; if (S.tau < s0) break;
    const g = settle(S.st + s0, GLIDE * .8), m0 = j ? MU[j - 1] : 0;
    mu = j ? Math.exp(lerp(Math.log(m0), Math.log(MU[j]), g)) : MU[0] * g;
    if (g > .999) kdone = j;
  }
  contoursQ(A, a, seg(S.st + .05, .45), mu);
  A.inside(() => line([[A.X(-4), A.Y(b_ + 4)], [A.X(b_ + 4), A.Y(-4)]], {color: C.ink, width: 1.6, alpha: a * seg(S.st + .05, .3)}));
  tag('feasible', A.X(-3.7), A.Y(-3.55), {alpha: a * lab(S.st + .2), color: C.body});
  tag('infeasible', A.X(3.7), A.Y(3.45), {align: 'right', alpha: a * lab(S.st + .2), color: C.body});
  // the solutions x(mu_k) reached, and the marker at x(mu) now
  const xs = [XQ]; for (let j = 0; j <= kdone; j++) xs.push(D.c.sols[j]);
  const at = penX(mu);
  line([...xs, at].map(q => [A.X(q[0]), A.Y(q[1])]), {color: C.blue, width: 1.5, alpha: a * .9});
  for (let j = 1; j < xs.length; j++) dot(A.X(xs[j][0]), A.Y(xs[j][1]), 2.6, {color: C.blue, fill: C.blue, alpha: a});
  const la0 = lab(S.st + .25) * a;
  dot(A.X(XQ[0]), A.Y(XQ[1]), 5, {color: C.navy, fill: '#fff', width: 1.6, alpha: la0});
  tag('unconstrained minimum', A.X(XQ[0]) + 12, A.Y(XQ[1]) - 12 - rise(la0), {alpha: la0});
  dot(A.X(at[0]), A.Y(at[1]), 5.6, {color: '#fff', fill: C.navy, width: 1.6, alpha: a * (S.tau >= T1 ? 1 : 0)});
  const la = lab(S.st + T1 + MU.length * PER) * a, xs_ = D.c.opt;
  minMark(A, xs_, la, true);
  tag('constrained optimum', A.X(xs_[0]) + 12, A.Y(xs_[1]) + 36 + rise(la), {align: 'right', color: C.accent, alpha: la});
  const show = kdone >= 0 ? MU[kdone] : (S.tau >= T1 ? MU[0] : 0);
  return {head: `\\mu\\ = ${show < 1 ? show.toFixed(1) : Math.round(show)}`};
}
/* ================================================ scene 6: two objectives */
const NS_F = b64f32(D.ns.F);
function scene6(A, S, a) {
  const G = D.ns.g, step = .1, st = stepAt(S, TA, step, G), k = st.k, s = st.s;
  // the exact Pareto front f2 = 1 - sqrt(f1)
  const fr = []; for (let j = 0; j <= 200; j++) { const f1 = (j / 200) ** 2; fr.push([A.X(f1), A.Y(ZDT(f1))]); }
  line(fr, {color: C.navy, width: 2.2, alpha: a, progress: seg(S.st + .05, .45)});
  const gen = D.ns.gens, cur = gen[k], nxt = k < G ? gen[k + 1] : cur, pa = a * seg(S.st + .2, .25);
  const inN = new Set(nxt.ids), inC = new Set(cur.ids);
  const draw1 = (id, nd, al) => {
    const x = A.X(NS_F[2 * id]), y = A.Y(NS_F[2 * id + 1]);
    if (nd) dot(x, y, 4.4, {color: '#fff', fill: C.accent, width: 1, alpha: al});
    else dot(x, y, 3.8, {color: C.sky, fill: '#fff', width: 1.3, alpha: al});
  };
  // the generation shown, and the next arriving: who survives stays put, who goes fades,
  // who is new appears; a survivor's front can change
  cur.ids.forEach((id, j) => {
    const nj = nxt.ids.indexOf(id);
    if (nj >= 0) { const ndc = cur.nd[j], ndn = nxt.nd[nj]; draw1(id, s < .5 ? ndc : ndn, pa); }
    else draw1(id, cur.nd[j], pa * (1 - s));
  });
  nxt.ids.forEach((id, j) => { if (!inC.has(id)) draw1(id, nxt.nd[j], pa * s); });
  const lp = lab(S.st + .35) * a;
  tag('exact Pareto front', A.X(.035), A.Y(.38) + rise(lp), {alpha: lp, color: C.navy});
  // the key: a thin box, white, inside the axes' empty corner
  const kx = A.X(.6), ky = A.Y(2.12), la = lab(S.st + .3) * a;
  line([[kx, ky], [A.X(.985), ky], [A.X(.985), ky + 66], [kx, ky + 66]], {color: C.ink, width: 1, fill: '#fff', close: true, alpha: la});
  dot(kx + 18, ky + 20, 4.4, {color: '#fff', fill: C.accent, width: 1, alpha: la});
  text('non-dominated', kx + 32, ky + 25, {size: 15, alpha: la});
  dot(kx + 18, ky + 46, 3.8, {color: C.sky, fill: '#fff', width: 1.3, alpha: la});
  text('dominated', kx + 32, ky + 51, {size: 15, alpha: la});
  return {head: `\\rm{generation}\\ ${st.on ? k : 0}`};
}
const SCENES = [scene1, scene2, scene3, scene4, scene5, scene6];

/* ================================================ the right column */
function column(S, a0) {
  const cur = SC[S.i], prv = S.prev >= 0 ? SC[S.prev] : cur, g = S.prev >= 0 ? settle(S.st, .35) : 1;
  text('problem type', RX, 40, {size: 16, color: C.muted, alpha: lab(.06)});
  SC.forEach((sc, j) => { const [x, y] = chipXY(j); chip(x, y, CH.w, CH.h, sc.chip, {on: j === S.i, hover: j === HC, down: j === HD}, lab(.08 + .03 * j)); });
  // his four characteristics, the one that applies marked
  const ta = lab(.16);
  text('characteristics', RX, YT, {size: 16, color: C.muted, alpha: ta});
  ROWS.forEach((r, j) => {
    const y = YR[j], ra = lab(.18 + .03 * j), wa = tw(r[1], 17), wb = tw(r[2], 17);
    const ext = v => v === 0 ? [XA - 6, XA + wa + 6] : v === 1 ? [XB - 6, XB + wb + 6] : [XA - 6, XB + wb + 6];
    const e0 = ext(prv.tags[j]), e1 = ext(cur.tags[j]), x0 = lerp(e0[0], e1[0], g), x1 = lerp(e0[1], e1[1], g);
    ctx.save(); ctx.globalAlpha = ra; ctx.fillStyle = C.steel; ctx.fillRect(x0, y - 17, x1 - x0, 24); ctx.restore();
    const on = v => cur.tags[j] === v || cur.tags[j] === 2;
    if (r[0]) text(r[0], RX, y, {size: 16, color: C.muted, alpha: ra});
    text(r[1], XA, y, {size: 17, color: on(0) && g > .5 ? C.navy : C.guide, alpha: ra});
    text(r[2], XB, y, {size: 17, color: on(1) && g > .5 ? C.navy : C.guide, alpha: ra});
    if (j === 3) {
      const eq = (cur.tags[3] === 2 ? g : 0) + (prv.tags[3] === 2 && S.prev >= 0 ? 1 - g : 0);
      math('=', (XA + wa + XB) / 2, y, {size: 17, color: C.navy, align: 'center', alpha: ra * clamp(eq)});
    }
  });
  // the methods that solve it; the one drawn has its key
  text('methods that solve it', RX, YM, {size: 16, color: C.muted, alpha: lab(.3)});
  cur.methods.forEach(([name, key], j) => {
    const y = YMI + j * PM, al = a0 * lab(.32 + .03 * j);
    if (key) swatch(key, RX + 2, y - 6, al);
    text(name, RX + 44, y, {size: 17, color: key ? C.ink : C.body, alpha: al});
  });
}
function swatch(key, x, y, a) {
  if (key === 'path') { line([[x, y + 4], [x + 14, y - 3], [x + 28, y + 1]], {color: C.blue, width: 1.5, alpha: a}); dot(x + 14, y - 3, 2.4, {color: C.blue, fill: C.blue, alpha: a}); dot(x + 28, y + 1, 4.6, {color: '#fff', fill: C.navy, width: 1.4, alpha: a}); }
  else if (key === 'dash') line([[x, y], [x + 30, y]], {color: C.blue, width: 2, dash: [6, 4], alpha: a});
  else if (key === 'swarm') { for (const [dx, dy] of [[3, 3], [13, -4], [24, 2]]) dot(x + dx, y + dy, 3.4, {color: '#fff', fill: C.blue, width: 1, alpha: a}); }
  else if (key === 'front') { dot(x + 6, y, 4.4, {color: '#fff', fill: C.accent, width: 1, alpha: a}); dot(x + 22, y, 4.4, {color: '#fff', fill: C.accent, width: 1, alpha: a}); }
}

/* ================================================ the frame */
function draw() {
  const S = now(), sc = SC[S.i];
  const fin = S.intro ? 1 : seg(S.st, .3), fout = 1 - seg(S.st + DUR - .3, .3), a = fin * fout;
  // the axes: their ticks change with the scene; the box stays
  const same = j => j >= 0 && JSON.stringify(SC[j].lim) === JSON.stringify(sc.lim);
  const nxt = (S.i + 1) % 6, ta = (same(S.prev) && !S.intro ? 1 : fin) * (same(nxt) ? 1 : fout);
  const A = axes({x: FP.x, y: FP.y, w: FP.w, h: FP.h, xlim: sc.lim[0], ylim: sc.lim[1], xticks: sc.tk[0], yticks: sc.tk[1],
                  tickSize: 16, labelSize: 18, ylabelGap: 46, progress: 0, alpha: 0,
                  xfmt: v => fmt(v), yfmt: v => fmt(v)});
  line([[FP.x, FP.y + FP.h], [FP.x + FP.w, FP.y + FP.h], [FP.x + FP.w, FP.y], [FP.x, FP.y], [FP.x, FP.y + FP.h]], {color: C.ink, width: 1.3, progress: seg(0, .35)});
  ticks(A, sc, ta * seg(.05, .35));
  // the scene: its landscape, its solver, its labels; the landscape stays from the local
  // search to the swarm (the tour's next scene), drawn once
  const o = {fin, fout, keepIn: S.i === 3 && S.prev === 2, keepOut: S.i === 2};
  const hd = SCENES[S.i](A, S, a, o);
  math(sc.head, FP.x, FP.y - 16, {size: 17, color: C.body, alpha: a * lab(S.st + (S.intro ? .2 : .05))});
  math(hd.head, FP.x + FP.w, FP.y - 16, {size: 17, align: 'right', alpha: a * lab(S.st + (S.intro ? .3 : .1))});
  column(S, a);
  let px = 18; const pa = a * seg(S.intro ? .45 : S.st + .1, .3);
  for (const [kind, str] of sc.params) px += (kind === 'm' ? math : text)(str, px, H - 14, {size: 14, color: C.muted, alpha: pa});
  place(S);
}
function ticks(A, sc, a) {
  if (a <= 0) return;
  const {x, y, w, h} = FP;
  for (const v of sc.tk[0]) {
    line([[A.X(v), y + h], [A.X(v), y + h - 5]], {color: C.ink, width: 1.1, alpha: a}); line([[A.X(v), y], [A.X(v), y + 5]], {color: C.ink, width: 1.1, alpha: a});
    math(fmt(v), A.X(v), y + h + 22, {size: 16, align: 'center', alpha: a});
  }
  for (const v of sc.tk[1]) {
    line([[x, A.Y(v)], [x + 5, A.Y(v)]], {color: C.ink, width: 1.1, alpha: a}); line([[x + w, A.Y(v)], [x + w - 5, A.Y(v)]], {color: C.ink, width: 1.1, alpha: a});
    math(fmt(v), x - 8, A.Y(v) + 5.6, {size: 16, align: 'right', alpha: a});
  }
  math(sc.ax[0], x + w / 2, y + h + 52, {size: 18, align: 'center', alpha: a});
  math(sc.ax[1], x - 46, y + h / 2, {size: 18, align: 'center', rot: -Math.PI / 2, alpha: a});
}

/* ================================================ the reader's hand: chips, keyboard */
const FIG = cv.closest('.fig'), BTN = [];
let said = null, KEY = '';
function sync() {
  const i = now().i;
  BTN.forEach((b, j) => { b.setAttribute('aria-checked', String(j === i)); b.tabIndex = j === i ? 0 : -1; });
}
function place(S) { if (BTN.length && KEY !== String(S.i)) { KEY = String(S.i); sync(); } }
/* choosing never pauses: playing, the scene starts again from its beginning and the tour
   goes on from it; paused, it shows complete */
function choose(i) {
  const cur = now();
  SEL = playing ? {i, t0: t, prev: cur.i} : {i, t0: t - TDONE, prev: -1};
  render(); sync();
  if (said) said.textContent = 'Problem type: ' + SC[i].chip + '.';
}
if (!STILL) {
  document.head.insertAdjacentHTML('beforeend', '<style>.nfo{position:absolute;pointer-events:auto;box-sizing:border-box;margin:0;padding:0;' +
    'border:0;background:transparent;color:transparent;cursor:pointer;-webkit-tap-highlight-color:transparent;font:inherit;overflow:hidden}' +
    '.nfo:focus{outline:none}.nfo::after{content:"";position:absolute;left:var(--l);right:var(--r);top:var(--t);bottom:var(--b)}' +
    '.nfo:focus-visible::after{outline:2px solid #095A94;outline-offset:1px}</style>');
  const group = document.createElement('div');
  group.setAttribute('role', 'radiogroup'); group.setAttribute('aria-label', 'Problem type');
  group.style.cssText = 'position:absolute;inset:0;pointer-events:none';
  SC.forEach((sc, j) => {
    const [x, y] = chipXY(j), b = document.createElement('button');
    b.type = 'button'; b.className = 'nfo'; b.textContent = sc.chip;
    b.setAttribute('role', 'radio'); b.setAttribute('aria-label', sc.chip);
    // the hit area: the chip and half the gaps around it (the whole grid, no dead gap)
    const x0 = x - CH.gx / 2, x1 = x + CH.w + CH.gx / 2, y0 = y - (CH.py - CH.h) / 2, y1 = y + CH.h + (CH.py - CH.h) / 2;
    b.style.left = x0 / W * 100 + '%'; b.style.width = (x1 - x0) / W * 100 + '%';
    b.style.top = y0 / H * 100 + '%'; b.style.height = (y1 - y0) / H * 100 + '%';
    // the focus ring hugs the drawn chip
    b.style.setProperty('--l', (x - x0) / (x1 - x0) * 100 + '%'); b.style.setProperty('--r', (x1 - x - CH.w) / (x1 - x0) * 100 + '%');
    b.style.setProperty('--t', (y - y0) / (y1 - y0) * 100 + '%'); b.style.setProperty('--b', (y1 - y - CH.h) / (y1 - y0) * 100 + '%');
    b.addEventListener('click', ev => { ev.stopPropagation(); choose(j); });
    b.addEventListener('keydown', ev => {
      const d = {ArrowRight: 1, ArrowDown: 2, ArrowLeft: -1, ArrowUp: -2}[ev.key];
      const to = d ? (j + d + 6) % 6 : ev.key === 'Home' ? 0 : ev.key === 'End' ? 5 : -1;
      if (to < 0) return;
      ev.preventDefault(); choose(to); BTN[to].focus();
    });
    b.addEventListener('pointerenter', () => { HC = j; render(); });
    b.addEventListener('pointerleave', () => { HC = -1; HD = -1; render(); });
    b.addEventListener('pointerdown', () => { HD = j; render(); });
    b.addEventListener('pointerup', () => { HD = -1; render(); });
    b.addEventListener('pointercancel', () => { HC = -1; HD = -1; render(); });
    group.appendChild(b); BTN.push(b);
  });
  FIG.insertBefore(group, FIG.querySelector('.ctl'));
  said = document.createElement('div'); said.setAttribute('role', 'status');
  said.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;pointer-events:none';
  FIG.appendChild(said);
}
reset();
boot();
"""


# ------------------------------------------------------------------ build
def compute():
    r = {}
    # 1
    runs = [gd_quadratic(s) for s in STARTS_Q]
    r["q_runs"] = runs
    # 2
    path, zval, reduced = simplex(A_LP, B_LP, C_LP)
    centre, cpath, cdots, gaps = central_path()
    lp = linprog(-C_LP, A_ub=A_LP, b_ub=B_LP, bounds=[(0, None)] * 2, method="highs")
    r.update(simplex=path, zval=zval, reduced=reduced, centre=centre, cpath=cpath, cdots=cdots, gaps=gaps, linprog=lp)
    # 3, 4
    crit = st_critical()
    xg = np.array([crit[0], crit[0]])
    minima = [xg, np.array([crit[2], crit[0]]), np.array([crit[0], crit[2]]), np.array([crit[2], crit[2]])]
    gd = gd_st()
    seed, found, inside0 = pick_pso_seed(xg)
    X, G, GF = pso(seed)
    r.update(crit=crit, minima=minima, gd=gd, pso_seed=seed, pso_found=found, pso_inside0=inside0, pso=(X, G, GF),
             contours=st_contours())
    # 5
    sols, steps = penalty_newton()
    xstar, lam, q = kkt_closed()
    slsqp = minimize(f_q, XQ, method="SLSQP", constraints=[{"type": "ineq", "fun": lambda x: B_C - A_C @ x}],
                     options={"ftol": 1e-14, "maxiter": 500})
    r.update(pen=sols, pen_steps=steps, xstar=xstar, lam=lam, q=q, slsqp=slsqp)
    # 6
    ns_seed = 1
    gens, table, Xf, Ff = nsga2(ns_seed)
    r.update(ns_seed=ns_seed, gens=gens, table=table, ns_X=Xf, ns_F=Ff)
    return r


def page_data(r):
    X, G, GF = r["pso"]
    lines, xy = [], []
    for li, pts in r["contours"]:
        lines.append([li, len(pts)])
        xy.append(pts.ravel())
    # the candidates NSGA-II showed, renumbered in order of appearance
    shown = []
    for ids, _ in r["gens"]:
        for i in ids:
            if int(i) not in shown:
                shown.append(int(i))
    ren = {i: k for k, i in enumerate(shown)}
    Fshow = np.array([r["table"][i] for i in shown])
    gens = [{"ids": [ren[int(i)] for i in ids], "nd": [int(v == 0) for v in rank]} for ids, rank in r["gens"]]
    return dict(
        dur=DUR, ta=TA, tdone=TDONE,
        q=dict(theta=30, lam=LAM, xs=XQ, levels=LEVELS_Q, k=K_Q, runs=r["q_runs"]),
        lp=dict(poly=POLY, c=C_LP, simplex=r["simplex"], central=r["cpath"][np.r_[0:len(r["cpath"]) - 1:2, len(r["cpath"]) - 1]],
                dots=r["cdots"],
                opt=r["linprog"].x),
        st=dict(k=K_ST, run=r["gd"], minima=r["minima"], lines=lines, xy=common.f32(np.concatenate(xy))),
        pso=dict(n=PSO_N, it=PSO_IT, seed=r["pso_seed"], X=X, G=G),
        c=dict(a=A_C, b=B_C, mus=MUS, sols=r["pen"], opt=r["slsqp"].x),
        ns=dict(n=NS_N, g=NS_G, seed=r["ns_seed"], F=common.f32(Fshow.ravel()), gens=gens),
    )


TITLE = "Figure 7: Six types of optimization problem and the methods that solve them"
ARIA = ("Six small optimization problems, one at a time, chosen with six buttons: a convex quadratic solved by "
        "gradient descent, a linear program solved by the simplex method and an interior point path, a function "
        "with four minima where gradient descent stops in a local one and a particle swarm finds the global one, a "
        "constrained problem solved with a growing quadratic penalty, and two objectives whose Pareto front NSGA-II "
        "finds. Beside each, which of the four characteristics apply and the methods that solve it.")


def best_hv_on_front(n, ref=(1.0, 1.0)):
    """The largest hypervolume n points on the exact front f2 = 1 - sqrt(f1) can
    have (reference point (1, 1)): their f1 values optimized from an even start."""
    from scipy.optimize import minimize as mz

    def neg(u):
        s_ = np.sort(np.clip(u, 0, 1))
        xs = np.r_[s_, ref[0]]
        return -np.sum((xs[1:] - xs[:-1]) * np.sqrt(s_))
    u0 = (np.arange(n) + 0.5) / n
    res = mz(neg, u0, method="L-BFGS-B", bounds=[(0, 1)] * n, options={"maxiter": 5000, "ftol": 1e-15, "gtol": 1e-12})
    return -res.fun


def pymoo_nsga2(seed):
    """The same problem in pymoo's own NSGA-II (an independent implementation),
    40 candidates, 40 generations: its final hypervolume."""
    try:
        from pymoo.algorithms.moo.nsga2 import NSGA2
        from pymoo.core.problem import Problem
        from pymoo.indicators.hv import HV
        from pymoo.optimize import minimize as pm_min
    except ImportError:
        return None

    class Zdt(Problem):
        def __init__(self):
            super().__init__(n_var=NS_NV, n_obj=2, xl=0.0, xu=1.0)

        def _evaluate(self, x, out, *a, **k):
            out["F"] = zdt(x)
    res = pm_min(Zdt(), NSGA2(pop_size=NS_N), ("n_gen", NS_G), seed=seed, verbose=False)
    F = res.F
    return dict(hv=float(HV(ref_point=np.array([1.0, 1.0]))(F)), F=F,
                gap=float(np.max(F[:, 1] - (1 - np.sqrt(F[:, 0])))))


def validate(r, ver=None):
    """The models against closed forms, textbook values and independent
    implementations; writes sp_opt_types.check.txt and prints it."""
    L = []
    say = L.append
    say("Figure 7, six types of optimization problem: check of tools/numfig/sp_opt_types.py")
    say("")
    say("THE FIGURE")
    say("  His animation (six scenes, traits, methods, a note each) redrawn: one plot that shows one scene at")
    say("  a time, six chips to choose it, the tour stepping through all six (8 s each, 48 s a round), and")
    say("  beside the plot his four characteristics (i) to (iv), the one that applies marked (a fifth line,")
    say("  one or two objectives, marks the multi-objective scene), with the methods that solve each problem")
    say("  (the one drawn with its key). Every moving thing is a solver's own iterate, computed here; the")
    say("  page's random numbers in his version (the swarm, the Pareto candidates) are seeded runs here.")
    say("")
    # ---------------------------------------------------------------- 1
    eig = np.linalg.eigvalsh(AQ)
    Mq = np.eye(2) - ETA_Q * AQ
    err_c, ends, ratios = [], [], []
    for s0, P in zip(STARTS_Q, r["q_runs"]):
        closed = XQ + np.array([np.linalg.matrix_power(Mq, k) @ (np.array(s0) - XQ) for k in range(K_Q + 1)])
        err_c.append(np.abs(P - closed).max())
        e = np.linalg.norm(P - XQ, axis=1)
        ends.append(e[-1])
        ratios.append(e[-1] / e[-2])
    rho = np.max(np.abs(1 - ETA_Q * eig))
    say("1  CONVEX: f(x) = (x - x*)^T A (x - x*)/2, A = R diag(1, 6) R^T (R turns 30 degrees), x* = (0.8, 0.5)")
    say(f"   A = [[{AQ[0, 0]:.6f}, {AQ[0, 1]:.6f}], [{AQ[1, 0]:.6f}, {AQ[1, 1]:.6f}]]; eigenvalues {eig[0]:.12f}, {eig[1]:.12f}")
    say(f"   gradient descent, eta = {ETA_Q:g}, {K_Q} steps from {', '.join(str(s0) for s0 in STARTS_Q)}")
    say(f"   a. the iterates against the closed form x_k - x* = (I - eta A)^k (x_0 - x*): largest difference {max(err_c):.1e}")
    say(f"   b. the error shrinks by max|1 - eta l| = {rho:.6f} per step at worst (the shallow direction, 1 - 0.2 x 1);")
    say(f"      the runs' last ratios |e_25|/|e_24| = {', '.join(f'{v:.6f}' for v in ratios)}")
    say(f"   c. all three reach the one minimum: |x_25 - x*| = {', '.join(f'{v:.4f}' for v in ends)} (from 4 to 5 away)")
    say("")
    # ---------------------------------------------------------------- 2
    lp = r["linprog"]
    Aall = np.vstack([A_LP, -np.eye(2)])
    ball = np.r_[B_LP, 0.0, 0.0]
    verts = []
    for i in range(5):
        for j in range(i + 1, 5):
            M2 = Aall[[i, j]]
            if abs(np.linalg.det(M2)) > 1e-12:
                v = np.linalg.solve(M2, ball[[i, j]])
                if np.all(Aall @ v <= ball + 1e-12):
                    verts.append(v)
    verts = np.unique(np.round(verts, 12), axis=0) + 0.0
    vals = verts @ C_LP
    y = r["reduced"][2:5]                          # the slacks' reduced costs: the duals
    gaps = np.array(r["gaps"])
    gap_rel = np.max(np.abs(gaps[:, 1] - 5 * gaps[:, 0]) / (5 * gaps[:, 0]))
    path = r["simplex"]
    say("2  LINEAR PROGRAM (his): maximize 3 x1 + 2 x2, x1 <= 3.5, x1 + x2 <= 4, x1 + 3 x2 <= 6, x >= 0")
    say(f"   the tableau simplex from the origin (Dantzig's rule) visits {' -> '.join('(' + ', '.join(f'{c:g}' for c in v) + ')' for v in path)}")
    say(f"   objective {r['zval']:.12g}; the final reduced costs {np.round(r['reduced'], 12).tolist()} are all >= 0: optimal")
    say(f"   a. scipy.optimize.linprog (HiGHS): x = ({lp.x[0]:.12g}, {lp.x[1]:.12g}), value {-lp.fun:.12g};")
    say(f"      its duals {np.round(-lp.ineqlin.marginals, 12).tolist()} against the tableau's {np.round(y, 12).tolist()};")
    say(f"      b^T y = {B_LP @ y:.12g} = c^T x (strong duality)")
    say(f"   b. every vertex of the polygon (the {len(verts)} feasible crossings of two constraint lines) and its value:")
    say("      " + ", ".join(f"({v[0]:g}, {v[1]:g}) {c:g}" for v, c in zip(verts, vals)))
    say(f"      the largest, {vals.max():g}, at ({verts[np.argmax(vals)][0]:g}, {verts[np.argmax(vals)][1]:g}): the optimum is a vertex")
    say(f"   c. the central path: the maximizer of c^T x/mu + sum log(slack) by Newton's method, mu = inf (analytic")
    say(f"      centre ({r['centre'][0]:.6f}, {r['centre'][1]:.6f})) down to 1e-3 over {len(gaps)} values. On the path the duality")
    say(f"      gap b^T l - c^T x with l = mu/slack equals 5 mu exactly (5 inequalities): largest relative difference")
    say(f"      {gap_rel:.1e}, dual residual |A^T l - c| <= {gaps[:, 2].max():.1e}; at mu = 1e-3 the path is")
    say(f"      {np.linalg.norm(r['cpath'][-1] - lp.x):.2e} from the vertex. Dots at mu = 10, 1, 0.1, 0.01, 0.001.")
    say("")
    # ---------------------------------------------------------------- 3, 4
    crit = r["crit"]
    roots = np.sort(np.roots([4, 0, -32, 5]).real)
    xg, xl = r["minima"][0], r["minima"][3]
    fg = f_st(xg)
    pub = f_st(np.array([-2.903534, -2.903534]))
    gd = r["gd"]
    e = np.abs(gd - xl).max(axis=1)
    rate_th = 1 - ETA_ST * (6 * crit[2] ** 2 - 16)
    xs = np.linspace(LO, HI, 2001)
    Xg, Yg = np.meshgrid(xs, xs)
    Z = f_st(np.stack([Xg, Yg], -1))
    jg = np.unravel_index(np.argmin(Z), Z.shape)
    say("3  NONCONVEX, LOCAL: Styblinski-Tang, f(x) = sum_i (x_i^4 - 16 x_i^2 + 5 x_i)/2 on [-5, 5]^2")
    say(f"   one coordinate's critical points, the roots of 4x^3 - 32x + 5, in closed form (trigonometric):")
    say(f"   {crit[0]:.12f} (minimum), {crit[1]:.12f} (the barrier), {crit[2]:.12f} (minimum); numpy's roots differ by")
    say(f"   {np.abs(roots - crit).max():.1e}. Four minima: f = {f_st(xg):.6f} (global), {f_st(r['minima'][1]):.6f} twice, {f_st(xl):.6f}")
    say(f"   a. the textbook minimum (Surjanovic and Bingham; Jamil and Yang): x_i = -2.903534, f = -39.16616 per")
    say(f"      coordinate: f(-2.903534, -2.903534) = {pub:.8f} against the closed form's {fg:.8f}")
    say(f"   b. a grid of 2001 x 2001 points: its lowest point ({Xg[jg]:.3f}, {Yg[jg]:.3f}), f = {Z[jg]:.6f} (>= {fg:.6f})")
    say(f"   c. gradient descent, eta = {ETA_ST:g}, from {START_ST}: x_{K_ST} = ({gd[-1][0]:.6f}, {gd[-1][1]:.6f}), f = {f_st(gd[-1]):.6f};")
    say(f"      {e[-1]:.1e} from the local minimum ({xl[0]:.6f}, {xl[1]:.6f}), {f_st(xl) - fg:.4f} above the global one;")
    say(f"      the error's last ratio {e[-1] / e[-2]:.6f} against 1 - eta f''(x*) = {rate_th:.6f} (linear convergence)")
    say("")
    X, G, GF = r["pso"]
    inb = np.all(G < crit[1], axis=1)
    k_in = int(np.argmax(inb))
    near = np.linalg.norm(G - xg, axis=1) < 1e-2
    k_1e2 = int(np.argmax(near)) if near.any() else -1
    gath = int((np.linalg.norm(X[-1] - xg, axis=1) < 0.3).sum())
    de = differential_evolution(f_st, [(LO, HI)] * 2, seed=1, tol=1e-12, polish=True)
    say(f"4  NONCONVEX, GLOBAL: particle swarm, {PSO_N} particles, w = {PSO_W}, c1 = c2 = {PSO_C}, |v| <= {PSO_VMAX},")
    say(f"   {PSO_IT} iterations, seed {r['pso_seed']}: the first seed of 0 to 199 whose best particle stays outside the")
    say(f"   global minimum's basin for the first 5 iterations and that still ends at the global minimum (its first")
    say(f"   best: ({G[0][0]:.3f}, {G[0][1]:.3f}), f = {GF[0]:.3f}). The best enters the global basin at iteration {k_in}, is")
    say(f"   within 1e-2 of the minimum from iteration {k_1e2}; at the end {gath} of {PSO_N} particles are within 0.3 of it.")
    say(f"   a. the final best ({G[-1][0]:.8f}, {G[-1][1]:.8f}), f = {GF[-1]:.10f}: {np.linalg.norm(G[-1] - xg):.1e} from the closed")
    say(f"      form's minimum, f above it by {GF[-1] - fg:.1e}")
    say(f"   b. an independent global method, scipy's differential evolution (seed 1, polished): ({de.x[0]:.8f},")
    say(f"      {de.x[1]:.8f}), f = {de.fun:.10f}")
    say(f"   c. robustness: {r['pso_found']} of 200 seeds end within 1e-2 of the global minimum, {r['pso_inside0']} of them with a")
    say(f"      first best already in its basin; the other {200 - r['pso_found']} end in a local one (a swarm is likely, not certain,")
    say(f"      to find it)")
    say("")
    # ---------------------------------------------------------------- 5
    sols, steps = r["pen"], r["pen_steps"]
    closed = np.array([penalty_closed(mu) for mu in MUS])
    xstar, lam, q = r["xstar"], r["lam"], r["q"]
    sq = r["slsqp"]
    d0 = np.linalg.norm(XQ - xstar)
    say(f"5  CONSTRAINED: f of 1 subject to x1 + x2 <= {B_C:g}; F_mu = f + mu max(0, x1 + x2 - ({B_C:g}))^2")
    say(f"   the KKT point in closed form: x* = xq - l A^-1 a, l = (a^T xq - b)/(a^T A^-1 a) = {lam:.12f}:")
    say(f"   x* = ({xstar[0]:.12f}, {xstar[1]:.12f}), f(x*) = {f_q(xstar):.12f}")
    say(f"   a. scipy's SLSQP (ftol 1e-14): ({sq.x[0]:.12f}, {sq.x[1]:.12f}); {np.linalg.norm(sq.x - xstar):.1e} from the closed form")
    say(f"   b. Newton's method on each F_mu, warm started (the penalty method as it runs) against the closed form")
    say(f"      (A + 2 mu a a^T) x = A xq + 2 mu b a: largest difference {np.abs(sols - closed).max():.1e}; Newton steps per mu:")
    say(f"      {steps} (F_mu is quadratic on the infeasible side, where every x(mu) lies)")
    for mu, xm in zip(MUS, sols):
        say(f"      mu = {mu:>5g}: x(mu) = ({xm[0]:+.6f}, {xm[1]:+.6f}), |x(mu) - x*| = {np.linalg.norm(xm - xstar):.3e}"
            f" = |xq - x*|/(1 + 2 mu a^T A^-1 a) = {d0 / (1 + 2 * mu * q):.3e};"
            f" multiplier 2 mu (a^T x - b) = {2 * mu * (A_C @ xm - B_C):.6f}")
    say(f"      (the multipliers tend to l = {lam:.6f}; the error falls as 1/mu: an exterior penalty never quite gets there)")
    say("")
    # ---------------------------------------------------------------- 6
    gens = r["gens"]
    Ff = r["ns_F"]
    rk = nondominated_sort(Ff)
    nd = Ff[rk == 0]
    gap = nd[:, 1] - (1 - np.sqrt(nd[:, 0]))
    hv = hypervolume(nd)
    hv40 = best_hv_on_front(NS_N)
    brute_ok = True
    for ids, rank in gens:
        Fg = np.array([r["table"][int(i)] for i in ids])
        nd_b = np.array([not np.any(np.all(Fg <= Fg[j], 1) & np.any(Fg < Fg[j], 1)) for j in range(len(Fg))])
        brute_ok &= bool(np.all(nd_b == (rank == 0)))
    pm = pymoo_nsga2(r["ns_seed"])
    hv_pm_ours = None
    if pm is not None:
        hv_pm_ours = hypervolume(pm["F"][nondominated_sort(pm["F"]) == 0])
    say(f"6  MULTI-OBJECTIVE: f1 = x1, f2 = g (1 - sqrt(x1/g)), g = 1 + (x2 + x3)/2, 0 <= x <= 1 (ZDT1's construction)")
    say("   For a given f1 = x1, f2 = g - sqrt(x1 g) grows with g (its derivative 1 - sqrt(x1/g)/2 > 0), so the Pareto")
    say("   set is x2 = x3 = 0 and the exact front f2 = 1 - sqrt(f1), 0 <= f1 <= 1. Both objectives are convex (f2 is g,")
    say("   affine, minus a geometric mean, concave), the box is convex: (i) convex, (ii) nonlinear, (iii) constrained.")
    say(f"   NSGA-II as Deb et al. (2002): {NS_N} candidates, {NS_G} generations, SBX (p = {NS_PC}, eta = {NS_EC:g}), polynomial")
    say(f"   mutation (p = 1/3, eta = {NS_EM:g}), binary tournaments on front and crowding distance, seed {r['ns_seed']}.")
    say(f"   a. the final candidates against the exact front: {int((rk == 0).sum())} of {NS_N} non-dominated; f2 - (1 - sqrt(f1))")
    say(f"      at most {gap.max():.4f}, median {np.median(gap):.4f}")
    say(f"   b. hypervolume (reference (1, 1)): {hv:.5f}; the exact front's is 2/3 = {2 / 3:.5f}, and the best any {NS_N} points on")
    say(f"      it can reach is {hv40:.5f} (optimized): the final set holds {hv / hv40 * 100:.2f}% of that")
    say(f"   c. the non-dominated candidates of every generation by brute force (no other candidate as good in both and")
    say(f"      better in one) against the fast sort: {'the same in all ' + str(len(gens)) + ' generations' if brute_ok else 'DIFFERENT'}")
    if pm is not None:
        say(f"   d. pymoo's own NSGA-II (0.6, an independent implementation; the same problem, {NS_N} candidates, {NS_G}")
        say(f"      generations, seed {r['ns_seed']}): hypervolume {pm['hv']:.5f} by pymoo's HV, {hv_pm_ours:.5f} by this file's; its")
        say(f"      largest gap to the front {pm['gap']:.4f}")
    say("")
    if ver:
        say("THE PAGE")
        for line_ in ver:
            say("  " + line_)
        say("")
    say("DISPLAY")
    say(f"  W = {W}, H = {H}. One scene every {DUR:g} s: its solver starts {TA:g} s in and is done by about 4.5 s, its labels")
    say(f"  by 5 s; POSTER_T = {TDONE:g} s shows the first scene complete (with ?view=N, scene N). The intro: the box and the")
    say("  first landscape draw in 0.45 s, the chips and the characteristics arrive by 0.4 s, gradient descent starts at")
    say("  0.5 s. Between iterates a marker glides (a Motion spring, for the eye; the iterates themselves are exact):")
    say("  descent one step every 0.16 s (scene 1) or 0.13 s (scene 3), the swarm and NSGA-II one iteration or")
    say("  generation every 0.1 s, the simplex one pivot per 1 s and 0.7 s, the penalty one mu every 0.95 s (log mu")
    say("  glides between them; the page draws F_mu's level sets and x(mu) in closed form at every moment). NSGA-II")
    say("  replaces candidates, it does not move them: a survivor stays put, one dropped fades, a new one appears.")
    say("  The landscape stays from scene 3 into scene 4 (the tour's order). Chips choose a scene (the tour goes on from")
    say("  it; paused, it shows complete); keyboard: a radio group, arrows move. ?view=N (1 to 6) starts on scene N.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_opt_types.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return txt


def _serve():
    import shutil
    import tempfile
    import threading
    tmp = tempfile.mkdtemp(prefix="numfig-")
    os.makedirs(os.path.join(tmp, "anim"))
    shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
    shutil.copy(os.path.join(common.ANIM, f"nf-{NAME}.html"), os.path.join(tmp, "anim"))
    srv = common._server(tmp)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return tmp, srv


def verify(r):
    """In headless Chromium: the page's closed forms against these, the overlap check
    over the whole tour and in every scene and chip state, and the live page (no
    errors, the intro, the loop, the chips and the keyboard). Returns report lines."""
    import shutil
    from playwright.sync_api import sync_playwright
    out = []
    tmp, srv = _serve()
    url = f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            # ---- the closed forms in the page
            pg = b.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "?still")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pts = [[-3.1, 2.2], [0.4, -1.7], [2.9, 3.3], [-1.2, -0.8], [3.7, -3.9]]
            fq_pg = np.array(pg.evaluate(f"{pts}.map(fq)"))
            fst_pg = np.array(pg.evaluate(f"{pts}.map(fst)"))
            mus = [0.0, 0.05, 0.1, 0.37, 1.0, 3.2, 10.0, 31.6, 100.0]
            px_pg = np.array(pg.evaluate(f"{mus}.map(penX)"))
            e1 = np.abs(fq_pg - f_q(np.array(pts))).max() / np.abs(f_q(np.array(pts))).max()
            e2 = np.abs(fst_pg - f_st(np.array(pts))).max() / np.abs(f_st(np.array(pts))).max()
            e3 = np.abs(px_pg - np.array([penalty_closed(m) for m in mus])).max()
            # the level arcs: points on F_mu = L, the arcs' ends on the boundary line
            arcs = pg.evaluate("""(() => { const a = D.c.a, b = D.c.b, out = [];
              for (const mu of [0.1, 1, 10, 100]) for (const lv of D.q.levels) {
                const m = penX(mu), Hm = [AQ[0] + 2 * mu * a[0] * a[0], AQ[1] + 2 * mu * a[0] * a[1], AQ[2] + 2 * mu * a[1] * a[1]];
                const pf = levelArc(AQ, XQ, 0, lv, -1, a, b, 60), pi = levelArc(Hm, m, Fmu(m, mu), lv, 1, a, b, 60);
                if (pf) out.push([mu, lv, -1, pf]); if (pi) out.push([mu, lv, 1, pi]); }
              return out; })()""")
            e4 = e5 = 0.0
            for mu, lv, side, P in arcs:
                P = np.array(P)
                Fv = f_q(P) + mu * np.maximum(0, P @ A_C - B_C) ** 2
                e4 = max(e4, np.abs(Fv - lv).max() / lv)
                g_ = P @ A_C - B_C
                e5 = max(e5, (side * g_ < -1e-9).sum())         # every point on its own side
            ends_ok = 0.0
            for mu, lv, side, P in arcs:
                P = np.array(P)
                if np.linalg.norm(P[0] - P[-1]) > 1e-9:      # a part of an ellipse: its ends on the line
                    ends_ok = max(ends_ok, np.abs(P[[0, -1]] @ A_C - B_C).max())
            out.append(f"closed forms in the page against numpy: f of 1 and 5 at 5 points {e1:.1e} (relative), the")
            out.append(f"Styblinski-Tang f {e2:.1e}, the penalty's x(mu) at 9 values of mu {e3:.1e}; the level sets drawn in")
            out.append(f"scene 5 ({len(arcs)} arcs for mu = 0.1, 1, 10, 100): F_mu on them equals the level within {e4:.1e} (relative),")
            out.append(f"{int(e5)} points on the wrong side of the line, the arcs' ends on it within {ends_ok:.1e}")
            pg.close()
            # ---- the overlap check: the tour, every scene from its start, every chip state
            pg = b.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "?t=0&overlap")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.evaluate("setPlay(false)")
            states = [(f"tour t = {tt:.2f}", f"SEL = null; HC = HD = -1; t = {tt}") for tt in np.arange(0, 48.01, .25)]
            for v in range(6):
                states += [(f"view {v + 1} t = {tt:g}", f"SEL = {{i: {v}, t0: 0, prev: -1}}; HC = HD = -1; t = {tt}")
                           for tt in (0.1, 0.3, 0.6, 1, 1.5, 2.2, 3, 3.8, 4.6, 5.6, 7, 7.85)]
                for j in range(6):
                    states += [(f"view {v + 1} chip {j + 1} hover", f"SEL = {{i: {v}, t0: 0, prev: -1}}; HC = {j}; HD = -1; t = 5.6"),
                               (f"view {v + 1} chip {j + 1} pressed", f"SEL = {{i: {v}, t0: 0, prev: -1}}; HC = {j}; HD = {j}; t = 5.6")]
                # chosen mid-scene from another: the glide of the marks
                states += [(f"chosen {v + 1} from {w + 1} +{dt:g}", f"SEL = {{i: {v}, t0: 20, prev: {w}}}; HC = HD = -1; t = {20 + dt}")
                           for w in range(6) if w != v for dt in (0.05, 0.15, 0.3)]
            bad = []
            for nm, js in states:
                pg.evaluate(f"() => {{ {js}; render(); }}")
                lab_, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                if lab_ or cro:
                    bad.append((nm, lab_[:3], cro[:3]))
            out.append(f"overlap check (engine.js ?overlap) in {len(states)} states: the tour every 0.25 s over its 48 s, each")
            out.append("scene from its start at 12 moments, every chip hovered and pressed in every scene, and every scene")
            out.append(f"chosen from every other at 0.05, 0.15 and 0.3 s: {len(bad)} with a collision")
            for nm, a_, c_ in bad[:20]:
                out.append(f"  {nm}: {a_} {c_}")
            pg.close()
            # ---- the live page
            pg = b.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            cons = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: cons.append(m.text) if m.type in ("error", "warning") else None)
            pg.goto(url)
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(1600)
            t1, pl = pg.evaluate("[t, playing]")
            pg.locator(".nfo").nth(3).click()
            s3 = pg.evaluate("[now().i, playing, SEL.i, [...document.querySelectorAll('.nfo')].map(b => b.getAttribute('aria-checked'))]")
            pg.wait_for_timeout(500)
            tau3 = pg.evaluate("now().tau")
            pg.locator(".nfo").nth(3).focus()
            pg.keyboard.press("ArrowRight")
            s4 = pg.evaluate("[now().i, document.activeElement.textContent, playing]")
            pg.keyboard.press("ArrowDown")
            s5 = pg.evaluate("[now().i, document.activeElement.textContent]")
            pg.locator("#pp").click()
            pg.locator(".nfo").nth(0).click()
            s6 = pg.evaluate("[now().i, playing, Math.abs(now().tau - TDONE) < 1e-6]")
            pg.locator("#pp").click()
            pg.evaluate("SEL = null; t = 47.6")
            pg.wait_for_timeout(900)
            s7 = pg.evaluate("[now().i, t > 48]")
            pg.locator("#rs").click()
            pg.wait_for_timeout(300)
            s8 = pg.evaluate("[SEL === null, t < 1, playing]")
            # a click on the canvas away from the chips still pauses (the engine's toggle)
            pg.mouse.click(300, 200)
            s9 = pg.evaluate("playing")
            pg.close()
            pg = b.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "?view=5")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(300)
            v5 = pg.evaluate("[now().i, SEL.i]")
            hit = pg.evaluate("(() => { const b = document.querySelector('.nfo').getBoundingClientRect(); return [b.width, b.height]; })()")
            pg.close()
            b.close()
        ok = (pl and t1 > 1.4 and s3[0] == 3 and s3[1] and s3[3][3] == "true" and s4[0] == 4 and s4[1] == "constrained"
              and s4[2] and s5[0] == 0 and not s6[1] and s6[0] == 0 and s6[2] and s7[0] == 0 and s7[1] and all(s8)
              and not s9 and v5 == [4, 4])
        out.append(f"live page: script errors {len(errs)}, console errors or warnings {len(cons)}; after 1.6 s t = {t1:.2f}, playing")
        out.append(f"{pl}; a click on chip 4 shows scene {s3[0] + 1} and the figure keeps playing ({s3[1]}), aria-checked")
        out.append(f"{s3[3]}; 0.5 s later its clock is at {tau3:.2f} s; ArrowRight moves to scene {s4[0] + 1} ('{s4[1]}'), ArrowDown")
        out.append(f"(two on, wrapping) to scene {s5[0] + 1}; paused, a chip shows its scene complete ({s6[2]}) and stays paused;")
        out.append(f"the tour wraps from scene 6 to scene {s7[0] + 1}; restart returns to the tour at t = 0 ({s8}); a click on the")
        out.append(f"canvas away from the chips pauses (playing {s9}); ?view=5 starts on scene {v5[0] + 1}. A chip's hit area at")
        out.append(f"672 px: {hit[0]:.1f} x {hit[1]:.1f} CSS px. All as expected: {ok}")
        if errs or cons:
            out.append(f"  errors: {errs[:5]} {cons[:5]}")
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return out, bad


def build(verify_=False):
    r = compute()
    data = page_data(r)
    common.build_html(NAME, TITLE, ARIA, W, H, data, JS)
    png = common.still(NAME)
    print("still:", png)
    size = os.path.getsize(os.path.join(common.ANIM, f"nf-{NAME}.html"))
    wsize = os.path.getsize(os.path.join(common.ANIM, f"nf-{NAME}.webp"))
    print(f"page: {size / 1024:.1f} KB, still: {wsize / 1024:.1f} KB")
    ver = None
    if verify_:
        ver, bad = verify(r)
        ver.append(f"page {size / 1024:.1f} KB, still {wsize / 1024:.1f} KB; common.still's own check (the poster and every")
        ver.append("0.25 s up to it): clean")
    validate(r, ver)
    return r


if __name__ == "__main__":
    build("--verify" in sys.argv)
