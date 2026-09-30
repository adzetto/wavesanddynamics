"""Exact Euler-Bernoulli beam dynamics shared by nf-periodic (Figure 6) and
nf-multispan (Figure 7): beams on pin supports, harmonic motion e^{i w t}.

State at a section: y = [w, theta, M, Q] with theta = w', M = EI w'', Q = EI w'''.
Over a uniform segment y(x) = F(x) y(0), F in closed form with the Krylov
functions S, T, U, V of z = k x, k^4 = m w^2 / EI. A pin support fixes w = 0
and passes theta and M; the shear jumps by the unknown reaction. So a span
between two pins condenses to a 2 x 2 transfer matrix on (theta, M), from
support to support: the monocoupled periodic structure of Mead (1970, 1975).

  cosh(mu) = T11 = S - T U / V                     (z = k L)

gives the propagation constant mu of the infinite periodic beam, and
A = T11 / T12, B = -1 / T12 the span's dynamic stiffness for end rotations
(end moments = [[A, B], [B, A]] rotations; 4EI/L and 2EI/L at w = 0), which
the Wittrick-Williams count turns into exact natural frequencies of a
continuous beam. Nothing here is approximate except the floating point.
"""

import numpy as np
from scipy.optimize import brentq


# ------------------------------------------------------------------ basics
def krylov(z):
    """Krylov (Rayleigh) functions: S' = V, V' = U, U' = T, T' = S."""
    ch, sh, c, s = np.cosh(z), np.sinh(z), np.cos(z), np.sin(z)
    return (ch + c) / 2, (sh + s) / 2, (ch - c) / 2, (sh - s) / 2


def wavenumber(omega, EI, m):
    """Flexural wavenumber k = (m w^2 / EI)^(1/4)."""
    return (m * omega ** 2 / EI) ** 0.25


def field(x, k, EI):
    """4 x 4 field transfer matrix of a uniform segment of length x:
    [w, theta, M, Q](x) = F [w, theta, M, Q](0), exact."""
    S, T, U, V = krylov(k * x)
    return np.array([
        [S, T / k, U / (EI * k ** 2), V / (EI * k ** 3)],
        [k * V, S, T / (EI * k), U / (EI * k ** 2)],
        [EI * k ** 2 * U, EI * k * V, S, T / k],
        [EI * k ** 3 * T, EI * k ** 2 * U, k * V, S],
    ])


def span_T(k, L, EI):
    """2 x 2 transfer matrix of a span between two pins, on (theta, M):
    [theta, M](L) = T [theta, M](0). det T = 1, T11 = T22."""
    S, T, U, V = krylov(k * L)
    t11 = S - T * U / V
    t12 = (T - U * U / V) / (EI * k)
    t21 = EI * k * (V - T * T / V)
    return np.array([[t11, t12], [t21, t11]])


def cosh_mu(z):
    """cosh(mu) of the periodic pin supported beam as a function of z = k L
    (the span length drops out): (cos z sinh z - sin z cosh z)/(sinh z - sin z)."""
    S, T, U, V = krylov(z)
    return S - T * U / V


def span_state0(theta0, M0, k, L, EI):
    """The shear Q(0) that makes w(L) = 0 for a span with w(0) = 0."""
    S, T, U, V = krylov(k * L)
    return -(theta0 * EI * k ** 2 * T + M0 * k * U) / V


def span_shape(theta0, M0, k, L, EI, x):
    """w(x) on a pinned span from its left-end rotation and moment (exact)."""
    Q0 = span_state0(theta0, M0, k, L, EI)
    S, T, U, V = krylov(k * x)
    return theta0 * T / k + M0 * U / (EI * k ** 2) + Q0 * V / (EI * k ** 3)


# ------------------------------------------------------------------ roots
def ss_root(n):
    """k L of the n-th mode of a simply supported span: n pi."""
    return n * np.pi


def cc_root(n):
    """k L of the n-th mode of a clamped-clamped span: cos z cosh z = 1."""
    g = lambda z: np.cos(z) - 1.0 / np.cosh(z)
    a = (n + 0.5) * np.pi
    return brentq(g, a - 0.5, a + 0.5, xtol=1e-15, rtol=1e-15)


def pc_root(n):
    """k L of the n-th mode of a pinned-clamped span: tan z = tanh z."""
    g = lambda z: np.sin(z) * np.cosh(z) - np.cos(z) * np.sinh(z)
    a = (n + 0.25) * np.pi
    return brentq(lambda z: g(z) / np.cosh(z), a - 0.4, a + 0.4, xtol=1e-15, rtol=1e-15)


def freq_from_z(z, L, EI, m):
    """Frequency in Hz at which k L = z."""
    return (z / L) ** 2 * np.sqrt(EI / m) / (2 * np.pi)


def z_from_freq(f, L, EI, m):
    return L * wavenumber(2 * np.pi * f, EI, m)


# ------------------------------------------------------------------ periodic
def propagation_constant(z):
    """mu = delta + i kappa per span, the branch with delta >= 0 and
    0 <= kappa <= pi. Pass band: delta = 0. Stop band: kappa is 0 or pi."""
    c = cosh_mu(z)
    if abs(c) <= 1:
        return complex(0.0, np.arccos(c))
    if c > 1:
        return complex(np.arccosh(c), 0.0)
    return complex(np.arccosh(-c), np.pi)


def band_edges(zmax, n_scan=200000):
    """Values of z = k L where |cosh mu| = 1, found by bracketing and
    Brent's method on the exact cosh(mu)."""
    zs = np.linspace(1e-3, zmax, n_scan)
    c = np.array([cosh_mu(z) for z in zs])
    out = []
    for sgn in (1.0, -1.0):
        g = c - sgn
        idx = np.nonzero(np.sign(g[:-1]) * np.sign(g[1:]) < 0)[0]
        for i in idx:
            out.append((brentq(lambda z: cosh_mu(z) - sgn, zs[i], zs[i + 1],
                               xtol=1e-15, rtol=1e-15), sgn))
    return sorted(out)


def power_at_support(theta, M, omega):
    """Time averaged power through a section where w = 0, in +x:
    P = (omega/2) Im{Q w* - M theta*} = -(omega/2) Im{M theta*}."""
    return -0.5 * omega * np.imag(M * np.conj(theta))


def bloch_wave(z, L, EI, m, direction=+1):
    """The Bloch (Floquet) wave of the infinite beam on pins every L at
    k L = z: returns (lam, theta0, M0, k) with [theta, M] at support n+1 =
    lam * [theta, M] at support n. In a pass band lam = exp(-i kappa') is
    picked so that the power flows in `direction`; in a stop band lam is
    the real eigenvalue with |lam| < 1 (decaying in +x)."""
    k = z / L
    omega = np.sqrt(EI / m) * k ** 2
    T = span_T(k, L, EI)
    ev, vec = np.linalg.eig(T)
    if abs(abs(ev[0]) - 1) < 1e-9 and abs(abs(ev[1]) - 1) < 1e-9:
        P = [power_at_support(vec[0, j], vec[1, j], omega) for j in (0, 1)]
        j = int(np.argmax(np.array(P) * direction))
    else:
        j = int(np.argmin(np.abs(ev)))
    return ev[j], vec[0, j], vec[1, j], k


# ------------------------------------------------------------------ multispan
def span_stiffness(k, L, EI):
    """Dynamic stiffness of a pinned span for its end rotations:
    [m_L, m_R] = [[A, B], [B, A]] [theta_L, theta_R]."""
    T = span_T(k, L, EI)
    return T[0, 0] / T[0, 1], -1.0 / T[0, 1]


_CC = np.array([cc_root(n) for n in range(1, 41)])


def cc_count(z):
    """Number of clamped-clamped span frequencies below k L = z (J0)."""
    return int(np.searchsorted(_CC, z))


class ContinuousBeam:
    """A beam over len(spans)+1 pins; span i has (L, EI, m). joints[i] is the
    rotational stiffness (N m/rad) joining the end rotations of spans i and
    i+1 over their shared pin: None or inf for a continuous beam, 0 for two
    independent simply supported spans, anything between for a partially
    continuous deck (a continuity plate, a link slab, a bearing).
    Exact natural frequencies by the Wittrick-Williams count on the dynamic
    stiffness of the support rotations (a spring adds no member frequencies,
    so J0 is the members' clamped-clamped count alone), exact mode shapes
    from the null vector of that matrix."""

    def __init__(self, spans, joints=None):
        self.spans = [tuple(map(float, s)) for s in spans]
        n = len(self.spans)
        self.joints = list(joints) if joints is not None else [None] * (n - 1)
        self.x0 = np.concatenate([[0.0], np.cumsum([s[0] for s in self.spans])])
        # rotation DOFs: one per pin, two over a pin with a finite joint
        self.left, self.right, self.springs, d = [], [], [], 0
        for i in range(n):
            if i == 0:
                self.left.append(d); d += 1
            else:
                kj = self.joints[i - 1]
                if kj is None or np.isinf(kj):
                    self.left.append(self.right[i - 1])
                else:
                    self.left.append(d); self.springs.append((self.right[i - 1], d, float(kj))); d += 1
            self.right.append(d); d += 1
        self.ndof = d

    def K(self, omega):
        K = np.zeros((self.ndof, self.ndof))
        for i, (L, EI, m) in enumerate(self.spans):
            A, B = span_stiffness(wavenumber(omega, EI, m), L, EI)
            a, b = self.left[i], self.right[i]
            K[a, a] += A
            K[b, b] += A
            K[a, b] += B
            K[b, a] += B
        for a, b, kj in self.springs:
            K[a, a] += kj
            K[b, b] += kj
            K[a, b] -= kj
            K[b, a] -= kj
        return K

    def J(self, omega):
        j0 = sum(cc_count(L * wavenumber(omega, EI, m)) for L, EI, m in self.spans)
        return j0 + int(np.sum(np.linalg.eigvalsh(self.K(omega)) < 0))

    def frequencies(self, n, tol=1e-13):
        """The first n natural frequencies (Hz), each bisected to tol."""
        out, lo = [], 1e-6
        hi = 1.0
        while self.J(hi) < n:
            hi *= 2
        for r in range(1, n + 1):
            a, b = lo, hi
            while self.J(b) < r:
                b *= 2
            while (b - a) > tol * b:
                c = 0.5 * (a + b)
                if self.J(c) >= r:
                    b = c
                else:
                    a = c
            out.append(0.5 * (a + b))
            lo = out[-1] * (1 + 1e-12)
        return np.array(out) / (2 * np.pi)

    def mode(self, f, npts=400):
        """Exact mode shape at natural frequency f (Hz): per span (x, w)."""
        omega = 2 * np.pi * f
        K = self.K(omega)
        u, s, vt = np.linalg.svd(K)
        theta = vt[-1]
        xs, ws = [], []
        for i, (L, EI, m) in enumerate(self.spans):
            k = wavenumber(omega, EI, m)
            T = span_T(k, L, EI)
            tl, tr = theta[self.left[i]], theta[self.right[i]]
            M0 = (tr - T[0, 0] * tl) / T[0, 1]      # internal moment at the left end
            x = np.linspace(0, L, npts)
            xs.append(self.x0[i] + x)
            ws.append(span_shape(tl, M0, k, L, EI, x))
        return xs, ws, s[-1] / s[0]

    def residual(self, f):
        """Smallest singular value of K relative to the largest, at f."""
        s = np.linalg.svd(self.K(2 * np.pi * f), compute_uv=False)
        return s[-1] / s[0]


def fe_frequencies(spans, ne, n, joints=None):
    """Cross-check: Hermite cubic finite elements, ne per span, consistent
    mass; w = 0 at every support. joints as in ContinuousBeam: over a pin
    with a finite joint the two spans keep their own rotation DOF, tied by
    the spring. The first n frequencies (Hz)."""
    from scipy.linalg import eigh
    joints = list(joints) if joints is not None else [None] * (len(spans) - 1)
    elems, springs, fixed, d = [], [], [], 0
    prev = None
    for i, (L, EI, m) in enumerate(spans):
        nodes = []
        for j in range(ne + 1):
            if j == 0 and prev is not None:
                kj = joints[i - 1]
                if kj is None or np.isinf(kj):
                    nodes.append(prev)
                else:
                    nodes.append((prev[0], d)); springs.append((prev[1], d, float(kj))); d += 1
            else:
                nodes.append((d, d + 1)); d += 2
        fixed += [nodes[0][0], nodes[-1][0]]
        elems.append((L, EI, m, nodes))
        prev = nodes[-1]
    Kg, Mg = np.zeros((d, d)), np.zeros((d, d))
    for L, EI, m, nodes in elems:
        l = L / ne
        ke = EI / l ** 3 * np.array([[12, 6 * l, -12, 6 * l], [6 * l, 4 * l * l, -6 * l, 2 * l * l],
                                     [-12, -6 * l, 12, -6 * l], [6 * l, 2 * l * l, -6 * l, 4 * l * l]])
        me = m * l / 420 * np.array([[156, 22 * l, 54, -13 * l], [22 * l, 4 * l * l, 13 * l, -3 * l * l],
                                     [54, 13 * l, 156, -22 * l], [-13 * l, -3 * l * l, -22 * l, 4 * l * l]])
        for e in range(ne):
            dd = [nodes[e][0], nodes[e][1], nodes[e + 1][0], nodes[e + 1][1]]
            Kg[np.ix_(dd, dd)] += ke
            Mg[np.ix_(dd, dd)] += me
    for a, b, kj in springs:
        Kg[a, a] += kj
        Kg[b, b] += kj
        Kg[a, b] -= kj
        Kg[b, a] -= kj
    free = [i for i in range(d) if i not in set(fixed)]
    lam = eigh(Kg[np.ix_(free, free)], Mg[np.ix_(free, free)], eigvals_only=True,
               subset_by_index=[0, n - 1])
    return np.sqrt(lam) / (2 * np.pi)
