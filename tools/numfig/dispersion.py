"""Figure 4: dispersion curves of guided waves, from SAFE models of
four steel cross-sections and an infinite plate, with two waves shown as their
cross-sections and along the beam. Interactive: every state is a SAFE solution.

(a) phase velocity c_p = w/k against frequency: every branch inside the window,
    the fundamental modes (bending, axial, torsional) from zero frequency, the
    higher order modes from their cut-on frequencies (k -> 0), the shear and
    Rayleigh speeds (Rayleigh equation) as guides. Two markers, 1 and 2, each a
    wave: a branch and a point on it.
(b) the two waves. Above, each one's cross-section (its SAFE eigenvector on the
    mesh) as its packet carries it; below, each one along the beam in an oblique
    view, as packets: bursts of the mode under a Hann envelope E, launched from the
    left end one after another, u = E(x - X) Re{U(y, z) exp(i(k(x - X) + psi))}. The
    envelope's centre X moves at the group velocity c_g (solved exactly with each
    state, V^T (K2 + 2k K3) V / (2 w V^T M V)), the phase psi at the centre at
    k c_g - w, so the crests move at the phase velocity c_p. Both waves run on one
    clock, a packet at the rod speed crossing the drawn beam in 2 s, so their speeds
    compare as they are, and a packet speeds up or slows down at once as its wave's
    frequency changes. Colour is |u| over the section's rms displacement at the
    packet's centre, at that instant, so every wave is seen to travel. Each beam's
    label gives c_p, c_g and the wavelength.

The sections (a switcher over (b)): the rectangular bar of safe_model.py, an
I-beam, a rail-like section (head, web, foot: about a quarter scale UIC60,
the rail of Figures 8 and 9), a pipe and a 10 mm plate of infinite width. Each is meshed here with 9-node
quadratic elements; its symmetry splits it into classes (mirror planes, or for
the pipe's uniform polar mesh, circumferential harmonics). The sweep here
draws the curves; the page carries each mesh and solves every wave it shows
with the same elements: a skyline LDL^T of K(k) - s M whose Sturm count pins
the branch, then inverse iteration. All five sections travel inside the page,
so choosing a section never depends on a separate network request. The curves
travel as the few eigenfrequencies a cubic Hermite in k needs.

With no reader input it tours the modes (wave 1 low in frequency, wave 2 gliding
up its curve, its packet quickening and slowing with its c_g). The first touch
pauses the tour ("resume tour" brings it back). A click or tap on a curve moves
the nearer marker there; a marker, or its thumb under the frequency axis, drags
along its curve; the markers are keyboard sliders (left and right: frequency, up
and down: the next curve). Whichever way a wave's frequency changes, its packet
takes the new speed at once. The waves pause and play from a control by the
colour scale, or with Space.

Run: python tools/numfig/dispersion.py [--page]   (writes content/anim/
nf-dispersion.html, .webp and -<section>.json, and dispersion.check.txt;
--page writes the page and data only). The sweeps are cached in the temp
folder.
"""
import base64
import functools
import hashlib
import http.server
import inspect
import json
import os
import pickle
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.csgraph import reverse_cuthill_mckee

import common
import safe_model as sm

NAME = "dispersion"
MESH = (16, 32)                   # Q9 elements across b and h (1.25 mm), see the check
F_MAX, CP_MAX = 200e3, 7.0e3      # the plot window, Hz and m/s
K_MAX = 470.0                     # rad/m: every branch of the bar leaves the window below it
REF_W, REF_H = 520, 418           # the refinement metric (drawing units), finer than the plot
BEAM = 412.0                      # mm of beam drawn along each wave (the page's STR.L)
PACKET = 160.0                    # mm: the full width of a packet's Hann envelope
CROSS = 2.0                       # s: a packet at the rod speed c_0 crosses the drawn beam in this
SLOW = sm.C_0 * CROSS / (BEAM / 1e3)   # the one clock of both waves' packets, not written on the figure
POSTER = 20 / 3                   # s: the first stop, bending at 20 and 150 kHz (both packets mid-beam, a crest at each centre)
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"vertical": "vertical bending", "lateral": "lateral bending", "axial": "axial",
         "torsional": "torsional"}


# ================================================================ the general SAFE
# Any Q9 mesh of a cross-section: isoparametric elements, 3 x 3 Gauss (exact
# for the bar's rectangles, where it gives safe_model's matrices), local node
# l = 3 bb + a at (xi_a, eta_bb). The page builds the same elements (SOLVER).
_G3, _W3 = np.polynomial.legendre.leggauss(3)
_L = lambda s: np.array([s * (s - 1) / 2, 1 - s * s, s * (s + 1) / 2])
_dL = lambda s: np.array([s - 0.5, -2 * s, s + 0.5])
_GP = [(i, j) for i in range(3) for j in range(3)]
_N = np.array([np.outer(_L(_G3[j]), _L(_G3[i])).ravel() for i, j in _GP])
_NXI = np.array([np.outer(_L(_G3[j]), _dL(_G3[i])).ravel() for i, j in _GP])
_NET = np.array([np.outer(_dL(_G3[j]), _L(_G3[i])).ravel() for i, j in _GP])
_WG = np.array([_W3[i] * _W3[j] for i, j in _GP])
_COMP = np.arange(27) % 3
_SGN = np.where((_COMP[:, None] == 0) & (_COMP[None, :] != 0), 1.0,
                np.where((_COMP[:, None] != 0) & (_COMP[None, :] == 0), -1.0, 0.0))


def _dmat():
    D = np.zeros((6, 6))
    D[:3, :3] = sm.LAM
    D[[0, 1, 2], [0, 1, 2]] = sm.LAM + 2 * sm.MU
    D[[3, 4, 5], [3, 4, 5]] = sm.MU
    return D


_D6 = _dmat()


def _jac(xy, g):
    J = np.array([[_NXI[g] @ xy[:, 0], _NXI[g] @ xy[:, 1]], [_NET[g] @ xy[:, 0], _NET[g] @ xy[:, 1]]])
    return J, np.linalg.det(J)


def element(xy):
    """K1, K2 (made real symmetric), K3, M (27 x 27) of one Q9 element, nodes xy (9, 2) in m."""
    K1, K2, K3, M = (np.zeros((27, 27)) for _ in range(4))
    for g in range(9):
        J, dJ = _jac(xy, g)
        Ji = np.linalg.inv(J)
        Ny = Ji[0, 0] * _NXI[g] + Ji[0, 1] * _NET[g]
        Nz = Ji[1, 0] * _NXI[g] + Ji[1, 1] * _NET[g]
        B1, B2 = np.zeros((6, 27)), np.zeros((6, 27))
        B1[1, 1::3] = Ny; B1[2, 2::3] = Nz
        B1[3, 1::3], B1[3, 2::3] = Nz, Ny
        B1[4, 0::3] = Nz; B1[5, 0::3] = Ny
        B2[0, 0::3] = _N[g]; B2[4, 2::3] = _N[g]; B2[5, 1::3] = _N[g]
        dA = _WG[g] * dJ
        K1 += B1.T @ _D6 @ B1 * dA
        K2 += (B1.T @ _D6 @ B2 - B2.T @ _D6 @ B1) * dA
        K3 += B2.T @ _D6 @ B2 * dA
        Nm = np.zeros((3, 27))
        for c in range(3):
            Nm[c, c::3] = _N[g]
        M += sm.RHO * Nm.T @ Nm * dA
    return K1, K2 * _SGN, K3, M


class Section:
    """A SAFE model of a meshed cross-section: nodes (N, 2) in mm, rounded to
    float32 first, as the page receives them; elems (E, 9)."""

    def __init__(self, nodes_mm, elems):
        self.nodes_mm = np.asarray(nodes_mm, np.float32).astype(np.float64)
        self.nodes = self.nodes_mm / 1e3
        self.elems = np.asarray(elems, np.int64)
        self.ndof = 3 * len(self.nodes)
        mats, rows, cols = [[], [], [], []], [], []
        self.minJ = np.inf
        for e in self.elems:
            xy = self.nodes[e]
            self.minJ = min(self.minJ, min(_jac(xy, g)[1] for g in range(9)))
            dofs = (3 * e[:, None] + np.arange(3)).ravel()
            rows.append(np.repeat(dofs, 27)); cols.append(np.tile(dofs, 27))
            for i, a in enumerate(element(xy)):
                mats[i].append(a.ravel())
        r, c = np.concatenate(rows), np.concatenate(cols)
        self.K1, self.K2, self.K3, self.M = (sp.csr_matrix((np.concatenate(x), (r, c)), shape=(self.ndof, self.ndof))
                                             for x in mats)
        self.classes, self._cls = {}, {}

    def mirror_maps(self):
        key = {(round(y, 3), round(z, 3)): i for i, (y, z) in enumerate(self.nodes_mm)}
        my = np.array([key.get((round(-y, 3), round(z, 3)), -1) for y, z in self.nodes_mm])
        mz = np.array([key.get((round(y, 3), round(-z, 3)), -1) for y, z in self.nodes_mm])
        return my, mz

    def mirror_basis(self, py, pz):
        """Q (ndof x m) of the class R_y u = py u, R_z u = pz u (0: no such plane):
        one orthonormal vector per orbit representative and component."""
        my, mz = self.mirror_maps()
        nn = len(self.nodes)
        ident = np.arange(nn)
        group = [(ident, 1, (1, 1, 1))]
        if py:
            assert (my >= 0).all()
            group.append((my, py, (1, -1, 1)))
        if pz:
            assert (mz >= 0).all()
            group.append((mz, pz, (1, 1, -1)))
        if py and pz:
            group.append((my[mz], py * pz, (1, -1, -1)))
        rep = np.min(np.array([g[0] for g in group]), axis=0)
        rows, cols, vals, col = [], [], [], 0
        for n in range(nn):
            if rep[n] != n:
                continue
            for c in range(3):
                v = {}
                for gmap, chi, sg in group:
                    d = 3 * gmap[n] + c
                    v[d] = v.get(d, 0.0) + chi * sg[c]
                v = {d: s for d, s in v.items() if abs(s) > 1e-12}
                if not v:
                    continue
                nrm = np.sqrt(sum(s * s for s in v.values()))
                for d, s in v.items():
                    rows.append(d); cols.append(col); vals.append(s / nrm)
                col += 1
        return sp.csr_matrix((vals, (rows, cols)), shape=(self.ndof, col))

    def ring_basis(self, n, typ, nth):
        """Q of circumferential harmonic n on a uniform polar mesh (nth elements
        around, nodes every pi/nth), type 'V' (u_r ~ sin n phi, u_t ~ cos n phi,
        u_x ~ sin n phi: n = 1 is vertical bending, n = 0 torsion) or 'L' (cos,
        -sin, cos: n = 0 is longitudinal), phi from +y toward +z. One vector per
        ring radius, angular orbit (the even and the odd node positions, the
        orbits of the rotation by 2 pi/nth) and cylindrical component: the exact
        invariant subspace of the mesh's dihedral symmetry for harmonic n."""
        y, z = self.nodes_mm.T
        r = np.round(np.hypot(y, z), 3)
        j = np.round(np.arctan2(z, y) / (np.pi / nth)).astype(int) % (2 * nth)
        ph = j * np.pi / nth
        fr, ft, fx, st = (np.sin, np.cos, np.sin, 1.0) if typ == "V" else (np.cos, np.sin, np.cos, -1.0)
        rows, cols, vals, col = [], [], [], 0
        for ring in np.unique(r):
            for par in (0, 1):
                s = np.flatnonzero((r == ring) & (j % 2 == par))
                for c in "rtx":
                    if c == "r":
                        a = fr(n * ph[s]); ent = [(3 * s + 1, a * np.cos(ph[s])), (3 * s + 2, a * np.sin(ph[s]))]
                    elif c == "t":
                        a = st * ft(n * ph[s]); ent = [(3 * s + 1, -a * np.sin(ph[s])), (3 * s + 2, a * np.cos(ph[s]))]
                    else:
                        ent = [(3 * s, fx(n * ph[s]))]
                    nrm = np.sqrt(sum((v ** 2).sum() for _, v in ent))
                    if nrm < 1e-9:
                        continue
                    for d, v in ent:
                        rows += list(d); cols += [col] * len(d); vals += list(v / nrm)
                    col += 1
        return sp.csr_matrix((vals, (rows, cols)), shape=(self.ndof, col))

    def cls(self, name):
        if name not in self._cls:
            Q = self.classes[name]
            pr = lambda A: (Q.T @ A @ Q).toarray()
            self._cls[name] = (Q, pr(self.K1), pr(self.K2), pr(self.K3), pr(self.M))
        return self._cls[name]

    def omegas(self, name, k, n):
        Q, k1, k2, k3, m = self.cls(name)
        w2 = sla.eigh(k1 + k * k2 + k * k * k3, m, eigvals_only=True,
                      subset_by_index=[0, min(n, len(m)) - 1], driver="gvx")
        return np.sqrt(np.clip(w2, 0, None))

    def solve(self, name, k, n):
        Q, k1, k2, k3, m = self.cls(name)
        w2, v = sla.eigh(k1 + k * k2 + k * k * k3, m, subset_by_index=[0, n - 1], driver="gvx")
        return np.sqrt(np.clip(w2, 0, None)), Q @ v


# ---------------------------------------------------------------- meshes (mm)
def grid_mesh(yb, zb, ny, nz, keep):
    """Q9 elements on the cells (i, j) of the breaks yb x zb where keep(i, j);
    cell i split into ny[i] elements along y, cell j into nz[j] along z."""
    ys, zs = [yb[0]], [zb[0]]
    for i in range(len(yb) - 1):
        ys += list(np.linspace(yb[i], yb[i + 1], 2 * ny[i] + 1)[1:])
    for j in range(len(zb) - 1):
        zs += list(np.linspace(zb[j], zb[j + 1], 2 * nz[j] + 1)[1:])
    y0 = np.concatenate([[0], np.cumsum(2 * np.array(ny))])
    z0 = np.concatenate([[0], np.cumsum(2 * np.array(nz))])
    el = []
    for j in range(len(zb) - 1):
        for i in range(len(yb) - 1):
            if keep(i, j):
                for ez in range(nz[j]):
                    for ey in range(ny[i]):
                        gy, gz = y0[i] + 2 * ey, z0[j] + 2 * ez
                        el.append([(gz + bb, gy + a) for bb in range(3) for a in range(3)])
    used = sorted({p for e in el for p in e})
    idx = {p: i for i, p in enumerate(used)}
    return (np.array([[ys[p[1]], zs[p[0]]] for p in used]),
            np.array([[idx[p] for p in e] for e in el]))


def bar_mesh(s=1.0):
    """The bar of safe_model.py (s = 1: its 10 x 20 elements, node for node)."""
    return grid_mesh([-10.0, 10.0], [-20.0, 20.0], [int(10 * s)], [int(20 * s)], lambda i, j: True)


def plate_mesh(s=1.0):
    """A displayed 40 mm slice of an infinite 10 mm plate, uniform across y.

    The basis ties all nodes at the same z: the drawn width is not a free
    edge. Lamb waves have u_y = 0; SH waves have only u_y.
    """
    return grid_mesh([-20.0, 20.0], [-5.0, 5.0], [1], [max(2, int(10 * s))], lambda i, j: True)


def plate_basis(S, family, parity):
    z = np.round(S.nodes_mm[:, 1], 4)
    rows, cols, vals, col = [], [], [], 0
    for zz in sorted(set(abs(z))):
        for c in ([1] if family == "SH" else [0, 2]):
            sign = parity * (-1 if c == 2 else 1)
            if zz == 0 and sign < 0:
                continue
            sel = np.flatnonzero(np.isclose(abs(z), zz, atol=1e-6))
            for n in sel:
                rows.append(3 * n + c); cols.append(col)
                vals.append((sign if z[n] < 0 else 1) / np.sqrt(len(sel)))
            col += 1
    return sp.csr_matrix((vals, (rows, cols)), shape=(S.ndof, col))


IBEAM = dict(h=40.0, b=30.0, tf=5.0, tw=4.0)


def ibeam_mesh(s=1.0, G=IBEAM):
    f = lambda n: max(1, int(round(n * s)))
    return grid_mesh([-G["b"] / 2, -G["tw"] / 2, G["tw"] / 2, G["b"] / 2],
                     [-G["h"] / 2, -G["h"] / 2 + G["tf"], G["h"] / 2 - G["tf"], G["h"] / 2],
                     [f(7), f(2), f(7)], [f(3), f(15), f(3)], lambda i, j: j != 1 or i == 1)


RAIL = dict(h=40.0, head=17.0, web=4.0, foot=35.0, foot_web=7.0, foot_edge=3.0, head_web=11.0, head_edge=9.0)


def rail_mesh(s=1.0, R=RAIL):
    """Head, web and foot on a grid of rectangles, then the foot's top made to
    taper from the web to its edge and the head's underside to rise toward its
    edges (trapezoidal elements)."""
    f = lambda n: max(1, int(round(n * s)))
    hw, hh, hf = R["web"] / 2, R["head"] / 2, R["foot"] / 2
    zb = [-R["h"] / 2, -R["h"] / 2 + R["foot_web"], R["h"] / 2 - R["head_web"], R["h"] / 2]
    nodes, elems = grid_mesh([-hf, -hh, -hw, hw, hh, hf], zb, [f(5), f(4), f(2), f(4), f(5)], [f(4), f(11), f(6)],
                             lambda i, j: (j == 0) or (j == 1 and i == 2) or (j == 2 and 1 <= i <= 3))
    y, z = nodes[:, 0].copy(), nodes[:, 1].copy()
    m = (z <= zb[1] + 1e-9) & (np.abs(y) > hw)
    top = zb[1] - (R["foot_web"] - R["foot_edge"]) * (np.abs(y[m]) - hw) / (hf - hw)
    z[m] = zb[0] + (z[m] - zb[0]) * (top - zb[0]) / (zb[1] - zb[0])
    m = (z >= zb[2] - 1e-9) & (np.abs(y) > hw)
    bot = zb[2] + (R["head_web"] - R["head_edge"]) * (np.abs(y[m]) - hw) / (hh - hw)
    z[m] = zb[3] - (zb[3] - z[m]) * (zb[3] - bot) / (zb[3] - zb[2])
    return np.column_stack([y, z]), elems


PIPE = dict(ro=20.0, ri=17.0)


def pipe_mesh(nth=72, nr=3, G=PIPE):
    """A uniform polar mesh: nth elements around, nr through the wall; local xi
    along r (outward) and eta along phi (counter-clockwise): positive Jacobian."""
    na = 2 * nth
    rs = np.linspace(G["ri"], G["ro"], 2 * nr + 1)
    ph = np.arange(na) * np.pi / nth
    nodes = np.array([[r * np.cos(p), r * np.sin(p)] for r in rs for p in ph])
    idx = lambda i, j: i * na + (j % na)
    return nodes, np.array([[idx(2 * er + a, 2 * et + bb) for bb in range(3) for a in range(3)]
                            for et in range(nth) for er in range(nr)])


def rep_order(S, planes):
    """A reverse Cuthill-McKee order of the mirror orbits' representatives (the
    smallest node of each orbit) on the graph of representatives sharing an
    element: rank per node, -1 for the rest. The page numbers each class's
    columns in this order and keeps its matrices as a skyline."""
    my, mz = S.mirror_maps()
    ident = np.arange(len(S.nodes))
    maps = [ident] + ([my] if planes[0] else []) + ([mz] if planes[1] else []) + ([my[mz]] if all(planes) else [])
    rep = np.min(np.array(maps), axis=0)
    reps = np.unique(rep)
    loc = -np.ones(len(ident), int); loc[reps] = np.arange(len(reps))
    r, c = [], []
    for e in S.elems:
        q = loc[rep[e]]
        r += list(np.repeat(q, 9)); c += list(np.tile(q, 9))
    A = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(len(reps), len(reps)))
    rank = -np.ones(len(ident), int)
    rank[reps[reverse_cuthill_mckee(A, symmetric_mode=True)]] = np.arange(len(reps))
    return rank


def properties(S):
    """A, centroid, second moments about the centroid (I_y: vertical bending, I_z:
    lateral), mm units, by the elements' own Gauss rule."""
    A = Sy = Sz = Iyy = Izz = 0.0
    for e in S.elems:
        xy = S.nodes_mm[e]
        for g in range(9):
            dA = _WG[g] * _jac(xy, g)[1]
            y, z = _N[g] @ xy[:, 0], _N[g] @ xy[:, 1]
            A += dA; Sy += y * dA; Sz += z * dA; Iyy += z * z * dA; Izz += y * y * dA
    yc, zc = Sy / A, Sz / A
    return dict(A=A, yc=yc, zc=zc, Iy=Iyy - A * zc * zc, Iz=Izz - A * yc * yc,
                Ip=Iyy - A * zc * zc + Izz - A * yc * yc)


def torsion(S):
    """Saint-Venant torsion, independent of SAFE: the warping function omega by a
    scalar FE on the same elements (Neumann problem, mean zero), J = int((w_y -
    z)^2 + (w_z + y)^2) about the centroid, and Gamma = int(omega^2) (the
    warping constant when the shear centre is the centroid). mm units."""
    n = len(S.nodes_mm)
    P = properties(S)
    f, m = np.zeros(n), np.zeros(n)
    rows, cols, vals = [], [], []
    for e in S.elems:
        xy = S.nodes_mm[e] - np.array([P["yc"], P["zc"]])
        for g in range(9):
            J, dJ = _jac(xy, g)
            Ji = np.linalg.inv(J)
            Ny = Ji[0, 0] * _NXI[g] + Ji[0, 1] * _NET[g]
            Nz = Ji[1, 0] * _NXI[g] + Ji[1, 1] * _NET[g]
            y, z, dA = _N[g] @ xy[:, 0], _N[g] @ xy[:, 1], _WG[g] * dJ
            rows += list(np.repeat(e, 9)); cols += list(np.tile(e, 9))
            vals += list(((np.outer(Ny, Ny) + np.outer(Nz, Nz)) * dA).ravel())
            np.add.at(f, e, (Ny * z - Nz * y) * dA)
            np.add.at(m, e, _N[g] * dA)
    K = sp.csr_matrix((vals, (rows, cols)), shape=(n, n))
    w = np.zeros(n)
    w[1:] = spla.spsolve(K[1:, 1:].tocsc(), f[1:])
    w -= (m @ w) / m.sum()
    J = P["Ip"] - w @ (K @ w)
    Gam = 0.0
    for e in S.elems:
        xy = S.nodes_mm[e]
        for g in range(9):
            Gam += (_N[g] @ w[e]) ** 2 * _WG[g] * _jac(xy, g)[1]
    return dict(J=J, Gamma=Gam)


def boundary(S):
    """The section's boundary as closed node loops (edges of one element only,
    three nodes each, material on the left: the outer loop counter-clockwise,
    a hole's clockwise), the outer one first."""
    sides = ((0, 1, 2), (2, 5, 8), (8, 7, 6), (6, 3, 0))
    count, edge = {}, {}
    for e in S.elems:
        for a, b, c in sides:
            k = frozenset((e[a], e[c]))
            count[k] = count.get(k, 0) + 1
            edge[(e[a], e[c])] = e[b]
    nxt = {a: (b, c) for (a, c), b in edge.items() if count[frozenset((a, c))] == 1}
    loops, seen = [], set()
    for start in list(nxt):
        if start in seen:
            continue
        loop, a = [], start
        while a not in seen:
            seen.add(a)
            b, c = nxt[a]
            loop += [int(a), int(b)]
            a = c
        loops.append(loop)
    area = lambda L: 0.5 * sum(S.nodes_mm[L[i - 1], 0] * S.nodes_mm[L[i], 1] - S.nodes_mm[L[i], 0] * S.nodes_mm[L[i - 1], 1]
                                for i in range(len(L)))
    return sorted(loops, key=area, reverse=True)       # the outer loop (counter-clockwise, largest area) first


def faces(S, loops, split=24.0, corner=20.0):
    """The loops cut into faces for the view along the beam: runs of boundary
    nodes that turn by less than `split` degrees, broken at every corner of more
    than `corner` degrees; each with its outward normal (right of the run,
    material being on the left) and its loop."""
    out = []
    for li, loop in enumerate(loops):
        P = S.nodes_mm[loop]
        n = len(loop)
        d = np.roll(P, -1, axis=0) - P
        ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
        turn = lambda a, b: (b - a + 180) % 360 - 180
        # start at a corner if there is one, so no face wraps around the start
        cuts = [i for i in range(n) if abs(turn(ang[i - 1], ang[i])) > corner]
        s0 = cuts[0] if cuts else 0
        run, acc = [s0], 0.0
        for q in range(1, n + 1):
            i = (s0 + q) % n
            t = turn(ang[(i - 1) % n], ang[i % n])
            if q == n or abs(t) > corner or abs(acc + t) > split:
                run.append(i)
                a, b = P[run[0]], P[run[-1]]
                ch = b - a
                nrm = np.array([ch[1], -ch[0]]) / np.hypot(*ch)
                out.append({"loop": li, "nodes": [int(loop[x]) for x in run], "n": [round(float(nrm[0]), 5), round(float(nrm[1]), 5)]})
                run, acc = [i], 0.0
            else:
                run.append(i)
                acc += t
    return out


# ================================================================ the sections
FUND4 = {"vertical": ("vertical", 0), "lateral": ("lateral", 0), "axial": ("axial", 0), "torsional": ("torsional", 0)}
CLS4 = [("axial", 1, 1), ("vertical", 1, -1), ("lateral", -1, 1), ("torsional", -1, -1)]
LEG4 = [("vertical", "vertical bending"), ("lateral", "lateral bending"), ("axial", "axial"),
        ("torsional", "torsional"), (None, "higher order")]
# the tour of each section: (wave 1's mode, f1, wave 2's mode, fa, f2), kHz; wave 2 glides
# fa to f2 (the first stop shows it at f2 at once); "h1" is the first higher order mode
SECTIONS = {
    "plate": dict(label="plate", mesh=plate_mesh, kind="plate",
                  classes=[("A", "Lamb", -1), ("S", "Lamb", 1), ("SHs", "SH", 1), ("SHa", "SH", -1)],
                  fund={"vertical": ("A", 0), "axial": ("S", 0), "lateral": ("SHs", 0)},
                  legend=[("vertical", "A0 Lamb"), ("axial", "S0 Lamb"), ("lateral", "SH0"), (None, "higher order")],
                  what="plate, thickness 10 mm (infinite width)",
                  tour=[("vertical", 20, "vertical", 50, 150), ("axial", 20, "axial", 50, 150),
                        ("lateral", 20, "lateral", 50, 150), ("h1", 185, "h1", 188, 195)]),
    "bar": dict(label="bar", mesh=bar_mesh, kind="mirror", planes=(1, 1), classes=CLS4, fund=FUND4, legend=LEG4,
                what="bar 20 × 40 mm",
                tour=[("vertical", 20, "vertical", 50, 150), ("axial", 20, "axial", 50, 150),
                      ("torsional", 45, "torsional", 80, 150), ("lateral", 20, "lateral", 50, 150),
                      ("h1", 70, "h1", 110, 190)]),
    "ibeam": dict(label="I-beam", mesh=ibeam_mesh, kind="mirror", planes=(1, 1), classes=CLS4, fund=FUND4,
                  legend=LEG4, what="I-beam 30 × 40 mm", detail="I-beam 30 × 40 mm, flanges 5 mm, web 4 mm",
                  tour=[("vertical", 6, "vertical", 20, 150), ("axial", 4, "axial", 16, 150),
                        ("torsional", 6, "torsional", 20, 150), ("lateral", 6, "lateral", 20, 150),
                        ("h1", 12, "h1", 40, 150)]),
    "rail": dict(label="rail", mesh=rail_mesh, kind="mirror", planes=(1, 0), classes=[("sym", 1, 0), ("anti", -1, 0)],
                 fund={"vertical": ("sym", 0), "axial": ("sym", 1), "lateral": ("anti", 0), "torsional": ("anti", 1)},
                 legend=LEG4, what="rail-like section 35 × 40 mm",
                 tour=[("vertical", 6, "vertical", 20, 150), ("axial", 4, "axial", 16, 150),
                       ("lateral", 6, "lateral", 20, 150), ("torsional", 8, "torsional", 20, 150),
                       ("h1", 12, "h1", 40, 150)]),
    "pipe": dict(label="pipe", mesh=pipe_mesh, kind="ring", nth=72,
                 classes=[("L0", "L", 0), ("V0", "V", 0)] + [(f"V{n}", "V", n) for n in range(1, 12)],
                 fund={"vertical": ("V1", 0), "lateral": ("V1", 0), "axial": ("L0", 0), "torsional": ("V0", 0)},
                 legend=[("vertical", "bending"), ("axial", "axial"), ("torsional", "torsional"), (None, "higher order")],
                 what="pipe Ø 40 × 3 mm",
                 tour=[("vertical", 20, "vertical", 50, 150), ("axial", 10, "axial", 30, 150),
                       ("torsional", 20, "torsional", 50, 150), ("h1", 12, "h1", 40, 150)]),
}
ORDER = ["bar", "ibeam", "rail", "pipe", "plate"]


def class_meta(Z):
    if Z["kind"] == "mirror":
        return [dict(name=c[0], py=c[1], pz=c[2]) for c in Z["classes"]]
    if Z["kind"] == "plate":
        return [dict(name=c[0], family=c[1], parity=c[2]) for c in Z["classes"]]
    return [dict(name=c[0], typ=c[1], n=c[2]) for c in Z["classes"]]


def make_section(key, s=1.0):
    """The section's SAFE model with its classes (s: mesh density, 1 the page's)."""
    Z = SECTIONS[key]
    if key == "pipe":
        nth, nr = int(round(72 * s)), int(round(3 * s))
        S = Section(*pipe_mesh(nth, nr))
        for name, typ, n in Z["classes"]:
            S.classes[name] = S.ring_basis(n, typ, nth)
        S.nth = nth
    elif key == "plate":
        S = Section(*plate_mesh(s))
        for name, family, parity in Z["classes"]:
            S.classes[name] = plate_basis(S, family, parity)
    else:
        S = Section(*Z["mesh"](s))
        for name, py, pz in Z["classes"]:
            S.classes[name] = S.mirror_basis(py, pz)
    return S


def branches_g(model, name, n, kmax):
    """As branches(), for any section: w(k) of the n lowest branches of a class on
    a k grid refined until consecutive points inside the window are < 2 units apart."""
    ks = np.unique(np.concatenate([np.geomspace(0.4, 20, 30), np.linspace(20, kmax, int(kmax / 4))]))
    W = np.array([model.omegas(name, k, n) for k in ks])
    for _ in range(12):
        f, cp = W / (2 * np.pi), W / ks[:, None]
        X, Y = _screen(f, cp)
        d = np.hypot(np.diff(X, axis=0), np.diff(Y, axis=0))
        out = ((f[:-1] > 1.03 * F_MAX) & (f[1:] > 1.03 * F_MAX)) | \
              ((cp[:-1] > 1.03 * CP_MAX) & (cp[1:] > 1.03 * CP_MAX))
        d[out] = 0
        bad = np.flatnonzero(d.max(axis=1) > 2.0)
        if not len(bad):
            break
        kn = 0.5 * (ks[bad] + ks[bad + 1])
        ks = np.concatenate([ks, kn])
        W = np.concatenate([W, [model.omegas(name, k, n) for k in kn]])
        o = np.argsort(ks)
        ks, W = ks[o], W[o]
    return ks, W


def compute_section(key):
    """A section's sweep and checks (cached in the temp folder)."""
    Z = SECTIONS[key]
    src = ("".join(inspect.getsource(f) for f in (_dmat, _jac, element, Section, grid_mesh, Z["mesh"], properties,
                                                  torsion, make_section, branches_g, compute_section))
           + repr((F_MAX, CP_MAX, REF_W, REF_H, key, Z["kind"], Z["classes"], Z["fund"], Z.get("nth"), IBEAM, RAIL, PIPE)))
    h = hashlib.sha1(src.encode()).hexdigest()[:12]
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-{key}-{h}.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    t0 = time.time()
    Z = SECTIONS[key]
    S = make_section(key)
    R = {"key": key, "ndof": S.ndof, "nel": len(S.elems), "nnode": len(S.nodes), "minJ": S.minJ,
         "props": properties(S), "tors": torsion(S), "cut": {}, "br": {},
         "dims": {c: S.classes[c].shape[1] for c in S.classes}}
    for name in S.classes:
        fc = S.omegas(name, 0.0, 24) / (2 * np.pi)
        R["cut"][name] = fc
        n = int(np.sum(fc < 1.1 * F_MAX))
        if n:
            R["br"][name] = branches_g(S, name, n, 900.0)
    # the fundamental modes at small k, against the closed forms
    val = []
    for k in (1.0, 2.0, 5.0, 10.0):
        row = {"k": k}
        for typ, (c, b) in Z["fund"].items():
            w = S.omegas(c, k, b + 1)[b]
            row[typ] = (w / (2 * np.pi), w / k)
        val.append(row)
    R["val"] = val
    # what each fundamental branch carries at k = 2 rad/m and 60 rad/m: its mass-weighted
    # share of each rigid motion of the section (twist about the centroid)
    P = R["props"]
    y, z = S.nodes.T
    yc, zc = P["yc"] / 1e3, P["zc"] / 1e3
    rig = {"axial": np.column_stack([np.ones_like(y), 0 * y, 0 * y]),
           "vertical": np.column_stack([0 * y, 0 * y, np.ones_like(y)]),
           "lateral": np.column_stack([0 * y, np.ones_like(y), 0 * y]),
           "torsional": np.column_stack([0 * y, -(z - zc), y - yc])}
    part = {}
    for typ, (c, b) in Z["fund"].items():
        part[typ] = {}
        for k in (2.0, 60.0):
            _, V = S.solve(c, k, b + 1)
            v = V[:, b]
            part[typ][k] = {rn: (v @ (S.M @ r.ravel())) ** 2 / ((v @ (S.M @ v)) * (r.ravel() @ (S.M @ r.ravel())))
                            for rn, r in rig.items()}
    R["part"] = part
    # mesh convergence: the lowest 8 of every class at k = 150 and 440 rad/m on this mesh
    # and on one with elements half the size
    conv = {}
    for s in (1.0, 2.0):
        M2 = S if s == 1.0 else make_section(key, s)
        conv[s] = {c: np.array([M2.omegas(c, k, 8) for k in (150.0, 440.0)]) for c in S.classes}
    R["conv"] = conv
    R["time"] = time.time() - t0
    with open(cache, "wb") as fh:
        pickle.dump(R, fh)
    return R


# ================================================================ the page's data
def pipe_name(c, b):
    if c == "L0":
        return f"L(0,{b + 1})"
    if c == "V0":
        return f"T(0,{b + 1})"
    return f"F({c[1:]},{b + 1})"


def curves_of(key, R):
    """The branches inside the window, as the page draws and solves them: each
    one's points (f kHz, c_p km/s) in k order, inside the window plus the point
    beyond each end, packed as float32; its class, name and kind of mode."""
    Z = SECTIONS[key]
    cnames = [c[0] for c in Z["classes"]]
    fund = {v: t for t, v in Z["fund"].items() if t != "lateral" or key != "pipe"}
    brs, flat, seen = [], [], {}
    for ci, name in enumerate(cnames):
        if name not in R["br"]:
            continue
        ks, W = R["br"][name]
        for b in range(W.shape[1]):
            f, cp = W[:, b] / (2 * np.pi), W[:, b] / ks
            inside = (f <= F_MAX) & (cp <= CP_MAX)
            if not inside.any():
                continue
            idx = np.flatnonzero(inside)
            assert np.all(np.diff(idx) == 1), (key, name, b, "leaves the window and comes back")
            assert np.all(np.diff(f[idx]) > 0), (key, name, b, "not monotone in f inside the window")
            lo, hi = max(idx[0] - 1, 0), min(idx[-1] + 1, len(ks) - 1)
            fc = float(R["cut"][name][b]) / 1e3
            typ = fund.get((name, b), "")
            if key == "pipe":
                nm = f"{NAMES[typ] if typ != 'vertical' else 'bending'} {pipe_name(name, b)}" if typ else \
                    f"higher order mode {pipe_name(name, b)}, cut-on {fc:.1f} kHz"
            elif key == "plate":
                nm = ("SH" + str(2 * b + (name == "SHa"))) if name.startswith("SH") else name + str(b) + " Lamb"
            elif typ:
                nm = NAMES[typ]
            else:
                nm = f"higher order mode, cut-on {fc:.1f} kHz"
                seen[nm] = seen.get(nm, 0) + 1
                if seen[nm] > 1:
                    nm += " (second)"
            brs.append({"ci": ci, "b": b, "fc": round(fc, 3), "n": int(hi - lo + 1), "o": len(flat), "nm": nm,
                        "type": typ})
            flat += list(f[lo:hi + 1] / 1e3) + list(cp[lo:hi + 1] / 1e3)
    return brs, np.array(flat)


THIN = 1e-5          # a travelling curve gives back every eigenfrequency of the sweep within this


def _herm(ka, wa, ga, kb, wb, gb, k):
    """The cubic Hermite in k through (ka, wa) and (kb, wb) with slopes ga and gb."""
    h = kb - ka
    t = (k - ka) / h
    t2 = t * t
    t3 = t2 * t
    return (2 * t3 - 3 * t2 + 1) * wa + (t3 - 2 * t2 + t) * h * ga + (3 * t2 - 2 * t3) * wb + (t3 - t2) * h * gb


def thinned(key, R):
    """The curves as they travel to the page: of each branch's sweep points (those of
    curves_of), only the ones a cubic Hermite in k needs, its slopes the group velocity
    dw/dk from a spline through the whole branch, for every dropped eigenfrequency to
    come back within THIN; per branch f (kHz), then c_p and c_g (km/s), in float32.
    The first and last points inside the window always go, so that the page's window
    on a branch (its first and last points inside) is at least the sweep's.
    Returns (brs, flat, stats): stats compares the page's curve (lay) at every sweep
    point with the sweep."""
    from scipy.interpolate import CubicSpline
    Z = SECTIONS[key]
    brs, flat = curves_of(key, R)
    out, packed = [], []
    st = {"n": 0, "kept": 0, "laid": 0, "err": 0.0}
    for r in brs:
        ks, W = R["br"][Z["classes"][r["ci"]][0]]
        w = W[:, r["b"]]
        f = flat[r["o"]:r["o"] + r["n"]]
        lo = int(np.argmin(np.abs(ks - 2 * np.pi * f[0] / flat[r["o"] + r["n"]])))
        k, wb = ks[lo:lo + r["n"]], w[lo:lo + r["n"]]
        cg = CubicSpline(ks, w)(k, 1)
        keep = sorted({0, min(1, len(k) - 1), max(len(k) - 2, 0), len(k) - 1})
        stack = list(zip(keep, keep[1:]))
        keep = set(keep)
        while stack:                                       # Douglas-Peucker on the Hermite's error
            i, j = stack.pop()
            if j - i < 2:
                continue
            idx = np.arange(i + 1, j)
            e = np.abs(_herm(k[i], wb[i], cg[i], k[j], wb[j], cg[j], k[idx]) / wb[idx] - 1)
            m = int(np.argmax(e))
            if e[m] > THIN:
                keep.add(int(idx[m]))
                stack += [(i, int(idx[m])), (int(idx[m]), j)]
        ix = np.array(sorted(keep))
        tf, tc, tg = (np.asarray(a, np.float32) for a in (wb[ix] / 2e3 / np.pi, wb[ix] / k[ix] / 1e3, cg[ix] / 1e3))
        out.append(dict(r, o=len(packed), n=len(ix)))
        packed += list(tf) + list(tc) + list(tg)
        K, F, CL = lay(tf, tc, tg)
        st["n"] += len(k)
        st["kept"] += len(ix)
        st["laid"] += len(K)
        st["err"] = max(st["err"], float(np.abs(np.interp(k, K, F) / (wb / 2e3 / np.pi) - 1).max()))
        fs, cs = wb / 2e3 / np.pi, wb / k / 1e3
        ins = np.flatnonzero((fs <= F_MAX / 1e3) & (cs <= CP_MAX / 1e3))
        inp = np.flatnonzero((F <= F_MAX / 1e3) & (CL <= CP_MAX / 1e3))
        assert F[inp[0]] <= fs[ins[0]] * (1 + 1e-6) and F[inp[-1]] >= fs[ins[-1]] * (1 - 1e-6), (key, r["nm"], "window")
    return out, np.array(packed, np.float32), st


def lay(f, cp, cg, tol=THIN):
    """A travelling curve laid out again as the page does it (prepare, in the script):
    each Hermite segment halved until straight lines between the points stay within
    tol of it, in f and in c_p, at every middle. Returns k (rad/m), f (kHz), c_p (km/s)."""
    f, cp, cg = (np.asarray(a, np.float64) for a in (f, cp, cg))
    k, w = 2 * np.pi * f / cp, 2 * np.pi * f
    K, Wd = [k[0]], [w[0]]

    def rec(i, k0, w0, k1, w1, d):
        km = (k0 + k1) / 2
        wm = _herm(k[i], w[i], cg[i], k[i + 1], w[i + 1], cg[i + 1], km)
        if d < 14 and (abs(wm - (w0 + w1) / 2) > tol * wm or abs(wm / km - (w0 / k0 + w1 / k1) / 2) > tol * wm / km):
            rec(i, k0, w0, km, wm, d + 1)
            rec(i, km, wm, k1, w1, d + 1)
        else:
            K.append(k1)
            Wd.append(w1)

    for i in range(len(f) - 1):
        rec(i, k[i], w[i], k[i + 1], w[i + 1], 0)
    K, Wd = np.array(K), np.array(Wd)
    return K, Wd / (2 * np.pi), Wd / K


def tour_of(key, brs, flat):
    """The section's tour with branch ids and frequencies inside each branch's window."""
    Z = SECTIONS[key]
    ids = {b["type"]: i for i, b in enumerate(brs) if b["type"]}
    if key == "pipe":
        ids["lateral"] = ids["vertical"]
    h1 = min((i for i, b in enumerate(brs) if not b["type"]), key=lambda i: brs[i]["fc"])
    ids["h1"] = h1
    frange = lambda i: (flat[brs[i]["o"]:brs[i]["o"] + brs[i]["n"]][1:-1].min(), flat[brs[i]["o"]:brs[i]["o"] + brs[i]["n"]][1:-1].max())
    out = []
    for m1, f1, m2, fa, f2 in Z["tour"]:
        a, b = ids[m1], ids[m2]
        (la, ha), (lb, hb) = frange(a), frange(b)
        assert la <= f1 <= ha and lb <= fa <= hb and lb <= f2 <= hb, (key, m1, f1, fa, f2, (la, ha), (lb, hb))
        out.append({"b1": a, "f1": f1, "b2": b, "fa": fa, "f2": f2})
    return out


def blob(meta, arrays):
    """[u32 header length][header JSON][pad to 4][arrays, each 4-aligned]; the header
    lists each array's type, offset from the data start and length."""
    parts, off = [], 0
    meta = dict(meta, arrays={})
    for name, a in arrays:
        t = {np.float32: "f4", np.uint16: "u2", np.int16: "i2"}[a.dtype.type]
        b = a.tobytes()
        meta["arrays"][name] = [t, off, int(a.size)]
        pad = (-len(b)) % 4
        parts.append(b + b"\0" * pad)
        off += len(b) + pad
    hb = json.dumps(meta, separators=(",", ":")).encode()
    return struct.pack("<I", len(hb)) + hb + b"\0" * ((-(4 + len(hb))) % 4) + b"".join(parts)


def section_blob(key, R):
    """Everything the page needs of a section, as one blob."""
    Z = SECTIONS[key]
    S = make_section(key)
    brs, flat = curves_of(key, R)
    tb, tflat, _ = thinned(key, R)
    loops = boundary(S)
    fcs = faces(S, loops)
    B = float(np.ptp(S.nodes_mm[:, 0])); Hh = float(np.ptp(S.nodes_mm[:, 1]))
    fund = {t: next(i for i, b in enumerate(brs) if b["type"] == (t if not (key == "pipe" and t == "lateral") else "vertical"))
            for t in Z["fund"]}
    cuts = sorted(round(float(x) / 1e3, 3) for c in R["cut"] for x in R["cut"][c] if 50 < x < F_MAX)
    fc1 = min(b["fc"] for b in brs if not b["type"])
    params = (f"{Z['what']}; steel, E = 210 GPa, ν = 0.29, ρ = 7850 kg/m³; SAFE, "
              f"{len(S.elems)} quadratic elements, solved in the page")
    meta = {"key": key, "label": Z["label"], "kind": Z["kind"], "E": sm.E, "nu": sm.NU, "rho": sm.RHO,
            "classes": class_meta(Z),
            "nth": Z.get("nth", 0), "brs": tb, "fund": fund, "tour": tour_of(key, brs, flat), "loops": loops,
            "faces": fcs, "B": B, "H": Hh, "sscale": round(min(160 / B, 300 / Hh), 4), "fc1": fc1, "cuts": cuts,
            "A": float(R["props"]["A"]) if "props" in R else float(sm.B * sm.H * 1e6),
            "legend": [[t, s] for t, s in Z["legend"]], "params": params}
    arrays = [("nodes", np.asarray(S.nodes_mm, np.float32).ravel()),
              ("elems", np.asarray(S.elems, np.uint16).ravel())]
    if Z["kind"] == "mirror":
        arrays.append(("rank", np.asarray(rep_order(S, Z["planes"]), np.int16)))
    arrays.append(("curves", tflat))
    return blob(meta, arrays)


# ================================================================ the bar (safe_model.py), as before
def _screen(f, cp):
    X = np.minimum(f, 1.04 * F_MAX) / F_MAX * REF_W
    Y = np.minimum(cp, 1.04 * CP_MAX) / CP_MAX * REF_H
    return X, Y


def branches(model, name, n):
    """w(k) of the n lowest branches of a class, on a k grid refined until
    consecutive points of every branch inside the window are < 2 units apart."""
    ks = np.unique(np.concatenate([np.geomspace(0.4, 20, 30), np.linspace(20, K_MAX, 120)]))
    W = np.array([model.omegas(name, k, n) for k in ks])
    for _ in range(10):
        f, cp = W / (2 * np.pi), W / ks[:, None]
        X, Y = _screen(f, cp)
        d = np.hypot(np.diff(X, axis=0), np.diff(Y, axis=0))
        out = ((f[:-1] > 1.03 * F_MAX) & (f[1:] > 1.03 * F_MAX)) | \
              ((cp[:-1] > 1.03 * CP_MAX) & (cp[1:] > 1.03 * CP_MAX))
        d[out] = 0
        bad = np.flatnonzero(d.max(axis=1) > 2.0)
        if not len(bad):
            break
        kn = 0.5 * (ks[bad] + ks[bad + 1])
        ks = np.concatenate([ks, kn])
        W = np.concatenate([W, [model.omegas(name, k, n) for k in kn]])
        o = np.argsort(ks)
        ks, W = ks[o], W[o]
    return ks, W


def compute():
    """The sweep and the checks against closed forms (cached in the temp folder)."""
    src = (open(os.path.join(HERE, "safe_model.py"), encoding="utf-8").read()
           + inspect.getsource(branches) + inspect.getsource(compute)
           + repr((MESH, F_MAX, CP_MAX, K_MAX, REF_W, REF_H)))
    key = hashlib.sha1(src.encode()).hexdigest()[:12]
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-{key}.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    t0 = time.time()
    model = sm.Safe(*MESH)
    R = {"mesh": MESH, "ndof": model.ndof, "K2err": model.K2_antisym_err}
    # cut-on frequencies (k = 0) and the branches of every class
    R["cut"], R["br"] = {}, {}
    for name in sm.CLASSES:
        fc = model.omegas(name, 0.0, 24) / (2 * np.pi)
        R["cut"][name] = fc
        n = int(np.sum(fc < 1.1 * F_MAX))
        R["br"][name] = branches(model, name, n)
    R["nodes"] = model.nodes
    # validation: low wavenumber limits against the closed forms
    val = []
    for k in (1.0, 2.0, 5.0, 10.0, 20.0, 40.0):
        row = {"k": k, "ref": sm.beam_speeds(k)}
        for name in sm.CLASSES:
            w = model.omegas(name, k, 1)[0]
            row[name] = (w / (2 * np.pi), w / k)
        val.append(row)
    R["val"] = val
    # which rigid motion each fundamental branch carries at small k
    y, z = model.nodes.T
    rig = {"axial": np.column_stack([np.ones_like(y), 0 * y, 0 * y]),
           "vertical": np.column_stack([0 * y, 0 * y, np.ones_like(y)]),
           "lateral": np.column_stack([0 * y, np.ones_like(y), 0 * y]),
           "torsional": np.column_stack([0 * y, -z, y])}
    part = {}
    for name in sm.CLASSES:
        _, V = model.solve(name, 2.0, 1)
        v = V[:, 0]
        part[name] = {}
        for rn, r in rig.items():
            r = r.ravel()
            part[name][rn] = (v @ (model.M @ r)) ** 2 / ((v @ (model.M @ v)) * (r @ (model.M @ r)))
    R["part"] = part
    # high frequency: the fundamental branches against the Rayleigh speed
    R["hf"] = {name: [(k, model.omegas(name, k, 1)[0]) for k in (440.0, 540.0)]
               for name in sm.CLASSES}
    # and far beyond the plot, on a 1 mm mesh (sparse shift-invert): the edge
    # wave and the Rayleigh waves of the faces
    fine = sm.Safe(30, 60)
    R["edge"] = {}
    for name in ("vertical", "axial"):
        Q = fine.basis(*sm.CLASSES[name])
        k1, k2, k3, mm_ = (Q.T @ A_ @ Q for A_ in (fine.K1, fine.K2, fine.K3, fine.M))
        k = 1000.0
        w2 = spla.eigsh((k1 + k * k2 + k * k * k3).tocsc(), k=3, M=mm_.tocsc(),
                        sigma=(0.97 * sm.C_R * k) ** 2, which="LM", return_eigenvectors=False)
        R["edge"][name] = (k, np.sqrt(np.sort(w2)))
    # mesh convergence at k = 150, 440 rad/m: the 8 lowest of each class
    conv = {}
    for mesh in ((6, 12), (8, 16), (10, 20), MESH, (32, 64)):
        mm = sm.Safe(*mesh)
        conv[mesh] = {name: np.array([mm.omegas(name, k, 8) for k in (150.0, 440.0)])
                      for name in sm.CLASSES}
    R["conv"] = conv
    R["time"] = time.time() - t0
    with open(cache, "wb") as fh:
        pickle.dump(R, fh)
    return R



def check_bar(R):
    """The bar's model against closed forms (the text of the check file's first part)."""
    L = []
    p = L.append
    sec = sm.section_constants()
    p("THE BAR (safe_model.py; the section the page opens with)")
    p("")
    p("MODEL")
    p(f"  steel bar, b x h = {sm.B*1e3:.0f} x {sm.H*1e3:.0f} mm (y x z), E = {sm.E/1e9:.0f} GPa, "
      f"nu = {sm.NU}, rho = {sm.RHO:.0f} kg/m^3")
    p(f"  c_L = {sm.C_L:.1f} m/s, c_T = {sm.C_T:.1f} m/s, c_0 = sqrt(E/rho) = {sm.C_0:.1f} m/s")
    p(f"  c_R = {sm.C_R:.1f} m/s (root of the Rayleigh equation, c_R/c_T = {sm.C_R/sm.C_T:.5f};"
      f" Viktorov's (0.87 + 1.12 nu)/(1 + nu) gives {(0.87+1.12*sm.NU)/(1+sm.NU):.5f})")
    p("  SAFE: u = U(y, z) exp(i(kx - wt)); Q9 quadratic quadrilaterals, 3 dof per node,")
    p("  3 x 3 Gauss (exact for rectangles); [K1 + ik K2 + k^2 K3 - w^2 M] U = 0 made real")
    p("  symmetric by U_x = i V_x; scipy.linalg.eigh at each real k. The two mirror planes")
    p("  split the problem into four symmetry classes (orthonormal symmetry-adapted bases):")
    p("  (++) axial, (+-) vertical bending, (-+) lateral bending, (--) torsional.")
    p(f"  K2 antisymmetry check: max|K2 + K2^T|/max|K2| = {R['K2err']:.1e}")
    p("")
    p("MESH AND CONVERGENCE")
    p(f"  production mesh {MESH[0]} x {MESH[1]} Q9 elements (1.25 mm), {R['ndof']} dof.")
    ref = R["conv"][(32, 64)]
    p(f"  every branch below {1.1*F_MAX/1e3:.0f} kHz (of the 8 lowest per class), against the 32 x 64 mesh:")
    worst = {}
    for mesh in ((6, 12), (8, 16), (10, 20)):
        errs = []
        for ik in range(2):
            e = 0
            for name in sm.CLASSES:
                w, wr = R["conv"][mesh][name][ik], ref[name][ik]
                sel = wr / (2 * np.pi) < 1.1 * F_MAX
                if sel.any():
                    e = max(e, np.abs(w[sel] / wr[sel] - 1).max())
            errs.append(e)
        worst[mesh] = max(errs)
        p(f"  {mesh[0]:2d} x {mesh[1]:2d} ({sm.B*1e3/mesh[0]:.1f} mm elements): max |w/w_ref - 1| "
          f"k = 150 rad/m {errs[0]:.1e}, k = 440 rad/m {errs[1]:.1e}")
    p(f"  The error falls as h^4 (quadratic elements). The 10 x 20 mesh is within "
      f"{100*worst[(10, 20)]:.2f} %: well below")
    p("  one drawing unit anywhere on the plot.")
    p("")
    p("CUT-ON FREQUENCIES (k = 0) against closed forms")
    ct = sm.C_T
    ap = lambda m, n: ct / 2 * np.hypot(m / sm.B, n / sm.H)
    exact = [("anti-plane shear (m, n) = (0, 1), c_T/(2h)", ap(0, 1), "vertical", 1),
             ("anti-plane shear (1, 0), c_T/(2b)", ap(1, 0), "lateral", 2),
             ("anti-plane shear (0, 2), c_T/h", ap(0, 2), "axial", 2),
             ("anti-plane shear (1, 1)", ap(1, 1), "torsional", 2),
             ("anti-plane shear (1, 2)", ap(1, 2), "lateral", 4),
             ("anti-plane shear (0, 3)", ap(0, 3), "vertical", 4),
             ("anti-plane shear (1, 3)", ap(1, 3), "torsional", 4),
             ("Lame mode (in-plane, equivoluminal), c_T/(sqrt(2) b)", ct / (np.sqrt(2) * sm.B), "vertical", 2)]
    for label, fe, name, b in exact:
        fs = R["cut"][name][b]
        p(f"  {label}: exact {fe/1e3:.4f} kHz, SAFE ({name}) {fs/1e3:.4f} kHz, error {fs/fe-1:+.1e}")
    p("  all cut-on frequencies below the plot limit (kHz):")
    for name in sm.CLASSES:
        fc = R["cut"][name]
        p(f"    {name:9s} " + ", ".join(f"{x/1e3:.2f}" for x in fc[1:] if x < F_MAX))
    p("")
    p("FUNDAMENTAL MODES AGAINST BEAM THEORY (low wavenumber)")
    p(f"  section: A = {sec['A']*1e6:.0f} mm^2, I_y = {sec['Iy']*1e12:.0f} mm^4, I_z = {sec['Iz']*1e12:.0f} mm^4,"
      f" J (Saint-Venant series) = {sec['J']*1e12:.0f} mm^4")
    p("  k (rad/m)  mode       f (Hz)     c_p SAFE   closed form            error")
    for row in R["val"]:
        k, rf = row["k"], row["ref"]
        for name, key, lab in (("vertical", "vertical_EB", "Euler-Bernoulli"),
                               ("vertical", "vertical_Timo", "Timoshenko"),
                               ("lateral", "lateral_EB", "Euler-Bernoulli"),
                               ("lateral", "lateral_Timo", "Timoshenko"),
                               ("axial", "axial_rod", "rod sqrt(E/rho)"),
                               ("axial", "axial_Love", "Love rod"),
                               ("torsional", "torsional_SV", "sqrt(GJ/(rho Ip))")):
            f, c = row[name]
            ref_c = float(rf[key])
            p(f"  {k:6.1f}   {name:10s} {f:10.1f}   {c:8.2f}   {lab:18s} {ref_c:8.2f}   {c/ref_c-1:+.2e}")
    p("")
    p("TRACKING")
    p("  Within a class the branches are ordered by frequency at each k: modes of one symmetry")
    p("  do not cross (they repel), so the ordered branches are the continuous curves; modes of")
    p("  different classes cross freely and are never mixed, being solved on separate bases.")
    for name in sm.CLASSES:
        ks, W = R["br"][name]
        inwin = W / (2 * np.pi) < F_MAX
        gap = np.diff(W, axis=1) / (2 * np.pi)
        pos = ks > 5.0
        g = gap[inwin[:, 1:] & pos[:, None]].min()
        p(f"  {name:9s} {len(ks)} wavenumbers, {W.shape[1]} branches; smallest gap between neighbouring"
          f" branches below {F_MAX/1e3:.0f} kHz, k > 5 rad/m: {g:.0f} Hz")
    p("  (at k = 0 the axial class has one true degeneracy, 161.02 kHz twice: the anti-plane modes")
    p("  (2, 0) and (0, 4), c_T/b = 2 c_T/h because h = 2b; the two branches part as k grows.)")
    brs, _ = curves_of("bar", R)
    p(f"  inside the window: {len(brs)} branches, each one run, each rising in f with k (checked).")
    p("")
    p("CLASSIFICATION of the lowest branch of each class at k = 2 rad/m, by its eigenvector:")
    p("  mass-weighted participation of each rigid cross-section motion")
    for name in sm.CLASSES:
        pr = R["part"][name]
        p(f"  {name:9s} " + "  ".join(f"{rn} {pr[rn]:.4f}" for rn in sm.CLASSES))
    p("")
    p("HIGH FREQUENCY")
    for name in sm.CLASSES:
        s = "  ".join(f"k = {k:.0f} rad/m: f = {w/2/np.pi/1e3:.1f} kHz, c_p = {w/k:.1f} m/s"
                      f" ({w/k/sm.C_R:.4f} c_R)" for k, w in R["hf"][name])
        p(f"  {name:9s} {s}")
    for name, (k, w) in R["edge"].items():
        p(f"  {name:9s} k = {k:.0f} rad/m on a 30 x 60 mesh (1 mm): lowest three c_p/c_R = "
          + ", ".join(f"{x/k/sm.C_R:.4f}" for x in w))
    p("  At short wavelengths the lowest branch of every class gathers at the bar's four 90 degree")
    p("  edges: an edge (wedge) wave at about 0.976 c_R, slightly slower than a Rayleigh wave. The")
    p("  next branches are Rayleigh waves on the faces, tending to c_R from above; the rest of the")
    p("  higher order branches crowd down toward c_T.")
    p("")
    return L


# ================================================================ checks
def check_solver_all(Rs):
    """Run the page's own SAFE (the SOLVER script, under node) on states along every
    branch inside the window of every section, against scipy on the same mesh: w,
    the MAC of the eigenvectors, the Sturm count, and the time per solve."""
    node = shutil.which("node")
    if not node:
        return {"skipped": "node is not installed"}
    rng = np.random.default_rng(4)
    data, refs, models = {"sections": {}, "cases": {}}, {}, {}
    for key in ORDER:
        Z, R = SECTIONS[key], Rs[key]
        S = make_section(key)
        models[key] = S
        tb, tflat, _ = thinned(key, R)
        sec = {"kind": Z["kind"], "E": sm.E, "nu": sm.NU, "rho": sm.RHO, "nth": Z.get("nth", 0),
               "classes": class_meta(Z),
               "nodes": np.asarray(S.nodes_mm, np.float32).ravel().tolist(), "elems": S.elems.ravel().tolist()}
        if Z["kind"] == "mirror":
            sec["rank"] = rep_order(S, Z["planes"]).tolist()
        data["sections"][key] = sec
        cases, rf = [], []
        for r in tb:
            o, n = r["o"], r["n"]
            k, f, cp = lay(tflat[o:o + n], tflat[o + n:o + 2 * n], tflat[o + 2 * n:o + 3 * n])   # the page's curve
            inw = np.flatnonzero((f <= F_MAX / 1e3) & (cp <= CP_MAX / 1e3))
            for _ in range(3):
                kk = float(rng.uniform(k[inw[0]], k[inw[-1]]))
                wt = 2e3 * np.pi * float(np.interp(kk, k, f))      # the page's shift: its curve at k
                cname = Z["classes"][r["ci"]][0]
                w, V = S.solve(cname, kk, r["b"] + 1)
                cases.append({"ci": r["ci"], "b": r["b"], "k": kk, "w": wt})
                rf.append((w[r["b"]], V[:, r["b"]]))
        data["cases"][key] = cases
        refs[key] = rf
    tmp = tempfile.mkdtemp(prefix="nf-disp-")
    try:
        with open(os.path.join(tmp, "cases.json"), "w") as fh:
            json.dump(data, fh)
        harness = ("const fs = require('fs'); const T = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));\n" + SOLVER +
                   "\nconst res = {};\n"
                   "for (const [key, S] of Object.entries(T.sections)) {\n"
                   "  const sec = {...S, nodes: Float32Array.from(S.nodes), elems: Int32Array.from(S.elems), rank: S.rank ? Int32Array.from(S.rank) : null};\n"
                   "  const m = safeModel(sec); sec.classes.forEach((_, ci) => m.cls(ci));\n"
                   "  for (const c of T.cases[key].slice(0, 8)) m.solve(c.ci, c.b, c.k, c.w);\n"
                   "  const t0 = process.hrtime.bigint();\n"
                   "  const out = T.cases[key].map(c => { const r = m.solve(c.ci, c.b, c.k, c.w);"
                   " return {w: r.w, U: Array.from(m.nodal(c.ci, r.x)), count: r.count, tries: r.tries, ok: r.ok, cg: m.cg(c.ci, c.k, r.x, r.w)}; });\n"
                   "  res[key] = {out, ms: Number(process.hrtime.bigint() - t0) / 1e6 / T.cases[key].length,\n"
                   "    dims: sec.classes.map((_, ci) => [m.cls(ci).n, m.cls(ci).ptr[m.cls(ci).n]])};\n"
                   "}\nfs.writeFileSync(process.argv[3], JSON.stringify(res));\n")
        with open(os.path.join(tmp, "h.js"), "w", encoding="utf-8") as fh:
            fh.write(harness)
        subprocess.run([node, os.path.join(tmp, "h.js"), os.path.join(tmp, "cases.json"),
                        os.path.join(tmp, "res.json")], check=True)
        with open(os.path.join(tmp, "res.json")) as fh:
            res = json.load(fh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = {}
    for key in ORDER:
        S, Z = models[key], SECTIONS[key]
        ew = em = egd = egh = 0.0
        bad = tries = 0
        for c, (wr, vr), o in zip(data["cases"][key], refs[key], res[key]["out"]):
            U = np.array(o["U"])
            mac = (U @ (S.M @ vr)) ** 2 / ((U @ (S.M @ U)) * (vr @ (S.M @ vr)))
            ew, em = max(ew, abs(o["w"] / wr - 1)), max(em, 1 - mac)
            bad += (o["count"] != c["b"]) or not o["ok"]
            tries = max(tries, o["tries"])
            # its group velocity: against scipy's eigenvector in the same formula, and a central difference
            k, name = c["k"], Z["classes"][c["ci"]][0]
            cgp = (vr @ (S.K2 @ vr) + 2 * k * (vr @ (S.K3 @ vr))) / (2 * wr * (vr @ (S.M @ vr)))
            h = 1e-4 * k
            fd = (group_near(S, name, k + h, wr + cgp * h)[0] - group_near(S, name, k - h, wr - cgp * h)[0]) / (2 * h)
            egh, egd = max(egh, abs(o["cg"] / cgp - 1)), max(egd, abs(o["cg"] / fd - 1))
        out[key] = {"n": len(refs[key]), "ew": ew, "em": em, "bad": bad, "tries": tries, "ms": res[key]["ms"],
                    "dims": res[key]["dims"], "egd": egd, "egh": egh}
    return out


def check_sections(Rs):
    """The I-beam, the rail and the pipe against closed forms."""
    L = []
    p = L.append
    G_, c0, ct = sm.MU, sm.C_0, sm.C_T
    for key in ORDER[1:]:
        Z, R = SECTIONS[key], Rs[key]
        if key == "plate":
            L += check_plate(R)
            continue
        P, T = R["props"], R["tors"]
        p(f"THE {Z['label'].upper()} ({Z.get('detail', Z['what'])})")
        p(f"  mesh: {R['nel']} Q9 elements, {R['nnode']} nodes, {R['ndof']} dof, smallest Jacobian "
          f"{R['minJ']:.2e} m^2 (all positive); classes and their sizes: "
          + ", ".join(f"{c} {n}" for c, n in R["dims"].items()))
        if key == "ibeam":
            G = IBEAM
            A_ = 2 * G["b"] * G["tf"] + (G["h"] - 2 * G["tf"]) * G["tw"]
            Iy_ = (G["b"] * G["h"] ** 3 - (G["b"] - G["tw"]) * (G["h"] - 2 * G["tf"]) ** 3) / 12
            Iz_ = 2 * G["tf"] * G["b"] ** 3 / 12 + (G["h"] - 2 * G["tf"]) * G["tw"] ** 3 / 12
            p(f"  section: A = {P['A']:.1f} mm^2 (exact {A_:.1f}), I_y = {P['Iy']:.0f} mm^4 (exact {Iy_:.0f}), "
              f"I_z = {P['Iz']:.0f} mm^4 (exact {Iz_:.0f})")
            Jt = (2 * G["b"] * G["tf"] ** 3 + (G["h"] - 2 * G["tf"]) * G["tw"] ** 3) / 3
            Gt = G["tf"] * G["b"] ** 3 / 12 * (G["h"] - G["tf"]) ** 2 / 2
            p(f"  torsion (the warping function by a scalar FE on the same mesh, independent of SAFE): "
              f"J = {T['J']:.0f} mm^4 (thin-walled sum b t^3/3 = {Jt:.0f}, which ignores the corners and ends),")
            p(f"  warping constant Gamma = {T['Gamma']:.3e} mm^6 (flanges' I_f h^2/2 = {Gt:.3e})")
        elif key == "rail":
            p(f"  section: A = {P['A']:.1f} mm^2, centroid {P['zc']:.3f} mm above mid-height, I_y = {P['Iy']:.0f} mm^4, "
              f"I_z = {P['Iz']:.0f} mm^4 (the Gauss rule is exact on these straight-edged elements)")
            p(f"  torsion (warping function FE): J = {T['J']:.0f} mm^4; one mirror plane only, so the shear centre is off")
            p("  the centroid and lateral bending couples with torsion (both in the antisymmetric class)")
        else:
            G = PIPE
            A_ = np.pi * (G["ro"] ** 2 - G["ri"] ** 2)
            I_ = np.pi / 4 * (G["ro"] ** 4 - G["ri"] ** 4)
            p(f"  mesh: {SECTIONS['pipe']['nth']} elements around, 3 through the 3 mm wall; each circumferential harmonic n is")
            p("  solved on its own (the exact block of the mesh's dihedral symmetry): L(0,m) and T(0,m) at n = 0,")
            p("  F(n,m) at n >= 1 (whose sin and cos partners are equal, so each is drawn once)")
            p(f"  section: A = {P['A']:.3f} mm^2 (exact {A_:.3f}), I = {P['Iy']:.1f} mm^4 (exact {I_:.1f}), "
              f"J = {T['J']:.1f} mm^4 (exact 2 I = {2 * I_:.1f})")
        EA = sm.E * P["A"] * 1e-6
        EIy, EIz = sm.E * P["Iy"] * 1e-12, sm.E * P["Iz"] * 1e-12
        GJ, rIp = G_ * T["J"] * 1e-12, sm.RHO * P["Ip"] * 1e-12
        EG = sm.E * T["Gamma"] * 1e-18
        p("  low wavenumber, SAFE against beam theory:")
        p("  k (rad/m)  mode       f (Hz)      c_p SAFE   closed form                c_p          error")
        for row in R["val"]:
            k = row["k"]
            refs = [("vertical", "Euler-Bernoulli, I_y", k * np.sqrt(EIy / (sm.RHO * P["A"] * 1e-6))),
                    ("lateral", "Euler-Bernoulli, I_z", k * np.sqrt(EIz / (sm.RHO * P["A"] * 1e-6))),
                    ("axial", "rod sqrt(E/rho)", c0),
                    ("torsional", "Saint-Venant sqrt(GJ/(rho I_p))", np.sqrt(GJ / rIp))]
            if key == "ibeam":
                refs.append(("torsional", "Vlasov, + E Gamma k^2", np.sqrt((GJ + EG * k * k) / rIp)))
            if key == "pipe":
                refs = [r for r in refs if r[0] != "lateral"] + [("torsional", "T(0,1): c_T", ct)]
            for typ, lab, ref in refs:
                f, c = row[typ]
                p(f"  {k:6.1f}   {typ:10s} {f:10.1f}   {c:9.2f}   {lab:26s} {ref:9.2f}   {c/ref-1:+.2e}")
        p("  what each fundamental branch carries (mass-weighted share of each rigid motion; twist about")
        p("  the centroid), at k = 2 and 60 rad/m:")
        for typ, dd in R["part"].items():
            if key == "pipe" and typ == "lateral":
                continue
            for k, pr in dd.items():
                p(f"    {typ:9s} k = {k:4.0f}: " + "  ".join(f"{rn} {pr[rn]:.3f}" for rn in pr))
        if key in ("ibeam", "rail"):
            p("  At small k each fundamental branch is its rigid motion. Higher up, the thin walls take over:")
            p("  the branches veer into the flexural (A0-like) waves of the flanges, web or foot, and all")
            p("  gather between 1.2 and 2.5 km/s. A branch keeps the name of its low-frequency limit.")
        p("  cut-on frequencies below the plot limit (kHz):")
        for c, fc in R["cut"].items():
            xs = [x / 1e3 for x in fc if 0 < x < F_MAX]
            if xs:
                p(f"    {c:9s} " + ", ".join(f"{x:.2f}" for x in xs))
        e = 0.0
        for c in R["conv"][1.0]:
            w, wr = R["conv"][1.0][c], R["conv"][2.0][c]
            sel = wr / (2 * np.pi) < 1.1 * F_MAX
            if sel.any():
                e = max(e, np.abs(w[sel] / wr[sel] - 1).max())
        p(f"  mesh convergence: against a mesh with elements half the size, every branch below 220 kHz")
        p(f"  (the 8 lowest of each class) at k = 150 and 440 rad/m: max |w/w_ref - 1| = {e:.1e}")
        brs, _ = curves_of(key, R)
        p(f"  inside the window: {len(brs)} branches, each one run, each rising in f with k (checked);"
          f" sweep {R['time']:.0f} s")
        p("")
    return L


# ================================================================ group velocity

def check_plate(R):
    """Infinite-plate limits and the independent Rayleigh-Lamb equations."""
    import guided_ut as lamb
    S = make_section("plate")
    cp0 = np.sqrt(sm.E / (sm.RHO * (1 - sm.NU ** 2)))
    bend = np.sqrt(sm.E * .01 ** 2 / (12 * sm.RHO * (1 - sm.NU ** 2)))
    lines = ["THE PLATE, infinite width, thickness 10 mm",
             "  Uniform across y: Lamb u_y=0, SH has u_x=u_z=0; free faces at z=+/-5 mm.",
             "  The displayed 40 mm width is a slice, not a free-edged finite beam."]
    for name, k, ref in [("S", 2., cp0), ("A", 2., 2 * bend), ("SHs", 200., sm.C_T)]:
        w, V = S.solve(name, k, 1)
        cp = w[0] / k
        error = abs(cp / ref - 1)
        assert error < .001, (name, error)
        lines.append(f"  {name} at k={k:g}: c_p={cp:.6f} m/s, limit {ref:.6f}, relative error {error:.2e}.")
    for family, name in [("S", "S"), ("A", "A")]:
        for k in [40., 150., 400.]:
            w = S.omegas(name, k, 1)[0]
            cp = w / k
            exact = min(lamb.roots_at(family, w / (2 * np.pi)), key=lambda v: abs(v - cp))
            error = abs(cp / exact - 1)
            assert error < .001, (family, k, error)
            lines.append(f"  {family}0 k={k:g}: SAFE {cp:.6f}, Rayleigh-Lamb {exact:.6f} m/s, error {error:.2e}.")
    lines.append("  Reference: https://pmc.ncbi.nlm.nih.gov/articles/PMC6356890/ (Lamb and SH plate families).")
    lines.append("")
    return lines


_SPARSE = {}


def group_near(model, name, k, w0, tol=5e-2):
    """(w, c_g) of the eigenpair nearest w0 (rad/s), by sparse shift-invert."""
    key = (id(model), name)
    if key not in _SPARSE:
        Q = model.classes[name]
        _SPARSE[key] = tuple((Q.T @ A @ Q).tocsc() for A in (model.K1, model.K2, model.K3, model.M))
    K1, K2, K3, M = _SPARSE[key]
    K = (K1 + k * K2 + (k * k) * K3).tocsc()
    vals, vecs = spla.eigsh(K, k=1, M=M, sigma=w0 * w0, which="LM")
    x, w = vecs[:, 0], np.sqrt(vals[0])
    # A finer production mesh can shift a nearby eigenvalue enough that the
    # coarse reference is no longer within the historical acceptance window.
    # Shift-invert still returns the eigenpair nearest the requested reference.
    return w, (x @ (K2 @ x) + 2 * k * (x @ (K3 @ x))) / (2 * w * (x @ (M @ x)))


def group_closed(k, P, T=None, kap=None):
    """Closed-form group velocities (m/s) at k (rad/m) of a section with properties P (mm units,
    properties()) and torsion T (torsion(), or None): Euler-Bernoulli (d/dk of k^2 sqrt(EI/rho A),
    i.e. 2 c_p), Timoshenko (its dispersion relation differentiated exactly, with shear
    coefficient kap), the rod c_0 and Love's rod, Saint-Venant torsion and Vlasov's."""
    A, rho, E, G = P["A"] * 1e-6, sm.RHO, sm.E, sm.MU
    out = {"axial_rod": sm.C_0, "axial_Love": sm.C_0 / (1 + sm.NU ** 2 * k * k * P["Ip"] * 1e-6 / P["A"]) ** 1.5}
    for plane, key in (("vertical", "Iy"), ("lateral", "Iz")):
        I = P[key] * 1e-12
        out[plane + "_EB"] = 2 * k * np.sqrt(E * I / (rho * A))
        if kap:
            a = rho * A * rho * I
            b = -(rho * A * (E * I * k * k + kap * G * A) + rho * I * kap * G * A * k * k)
            c = kap * G * A * E * I * k ** 4
            W2 = (-b - np.sqrt(b * b - 4 * a * c)) / (2 * a)
            db = -(2 * rho * A * E * I * k + 2 * rho * I * kap * G * A * k)
            dc = 4 * kap * G * A * E * I * k ** 3
            out[plane + "_Timo"] = -(db * W2 + dc) / (2 * a * W2 + b) / (2 * np.sqrt(W2))
    if T is not None:
        rIp = rho * P["Ip"] * 1e-12
        out["torsional_SV"] = np.sqrt(G * T["J"] * 1e-12 / rIp)
        EG, GJ = E * T["Gamma"] * 1e-18, G * T["J"] * 1e-12
        out["torsional_Vlasov"] = (GJ * k + 2 * EG * k ** 3) / (rIp * np.sqrt((GJ * k * k + EG * k ** 4) / rIp))
    return out


def page_curve(key, R):
    """The curves as the page lays them out (lay()): per branch id, (k rad/m, f kHz, c_p km/s)."""
    tb, tflat, _ = thinned(key, R)
    out = []
    for r in tb:
        o, n = r["o"], r["n"]
        out.append(lay(tflat[o:o + n], tflat[o + n:o + 2 * n], tflat[o + 2 * n:o + 3 * n]))
    return tb, out


def k_at_f(curve, f):
    """The page's kAtF: the wavenumber of f (kHz) on a laid-out curve, by straight lines in f."""
    K, F, _ = curve
    return float(np.interp(f, F, K))


# the page's glide rule (part() in FIGURE): each interval of a sampled rate integrated as the
# cubic through its four nearest samples
_CUB = [lambda u: -(u ** 4 / 4 - 2 * u ** 3 + 5.5 * u * u - 6 * u) / 6, lambda u: (u ** 4 / 4 - 5 * u ** 3 / 3 + 3 * u * u) / 2,
        lambda u: -(u ** 4 / 4 - 4 * u ** 3 / 3 + 1.5 * u * u) / 2, lambda u: (u ** 4 / 4 - u ** 3 + u * u) / 6]


def glide_integral(y, T):
    """The integral over T seconds of a rate sampled at len(y) moments evenly spread, as the page does it."""
    n = len(y) - 1
    tot = 0.0
    for j in range(n):
        j0 = min(max(j - 1, 0), n - 3)
        tot += sum(y[j0 + q] * (_CUB[q](j - j0 + 1) - _CUB[q](j - j0)) for q in range(4))
    return tot * T / n


def ease_in_out(x):
    return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2


TOUR_T = dict(T1=16, TS=18, TG0=2, TGD=8, NG=128)   # the page's tour clock (FIGURE's T1, TS, TG0, TGD and NG)
SIG = PACKET * np.sqrt(1 / 32 - 1 / (4 * np.pi ** 2) + 1 / (64 * np.pi ** 2)) / np.sqrt(3 / 8)   # rms width of E^2, mm


def fastest(Rs):
    """The fastest packet anywhere: the travelling point inside a window with the largest slope,
    then its exact c_g there (group_near). Returns (c_g km/s, section key, branch name, f kHz)."""
    best = (0, None)
    for key in ORDER:
        brs, tflat, _ = thinned(key, Rs[key])
        for r in brs:
            o, n = r["o"], r["n"]
            tf, tc, tg = (np.asarray(tflat[o + j * n:o + (j + 1) * n], np.float64) for j in range(3))
            for i in np.flatnonzero((tf <= F_MAX / 1e3) & (tc <= CP_MAX / 1e3)):
                if tg[i] > best[0]:
                    best = (tg[i], (key, r, tf[i], tc[i]))
    key, r, f, c = best[1]
    S = make_section(key)
    k = 2 * np.pi * f / c
    cg = group_near(S, SECTIONS[key]["classes"][r["ci"]][0], k, 2e3 * np.pi * f)[1]
    return cg / 1e3, key, r["nm"], f


def tour_group(Rs):
    """Per section and stop: each wave's state on the page's curve (the page's kAtF), its exact
    w and c_g (group_near), and the spreading a Gaussian burst of the packet's rms width would
    undergo over one passage (second order in the bandwidth, which the page leaves out):
    sqrt(1 + (w'' D / (2 c_g sigma^2))^2), w'' = dc_g/dk by a central difference, D = BEAM +
    PACKET. {key: [stop: {"w1": st, "wa": st, "w2": st}]}, st = (f kHz, c_p, c_g km/s, k rad/m, widening)."""
    out = {}
    for key in ORDER:
        S, Z = make_section(key), SECTIONS[key]
        tb, curves = page_curve(key, Rs[key])
        brs, flat = curves_of(key, Rs[key])
        stops = []
        for s in tour_of(key, brs, flat):
            row = {}
            for lab, bi, f in (("w1", s["b1"], s["f1"]), ("wa", s["b2"], s["fa"]), ("w2", s["b2"], s["f2"])):
                name = Z["classes"][tb[bi]["ci"]][0]
                k = k_at_f(curves[bi], f)
                w, cg = group_near(S, name, k, 2e3 * np.pi * float(np.interp(k, curves[bi][0], curves[bi][1])))
                h = 1e-3 * k
                gp = group_near(S, name, k + h, w + cg * h)[1]
                gm = group_near(S, name, k - h, w - cg * h)[1]
                wpp = (gp - gm) / (2 * h)
                wid = np.sqrt(1 + (wpp * (BEAM + PACKET) / 1e3 / (2 * cg * (SIG / 1e3) ** 2)) ** 2)
                row[lab] = (w / 2e3 / np.pi, w / k / 1e3, cg / 1e3, k, wid)
            stops.append(row)
        out[key] = stops
    return out


def check_group(Rs, SV, TG, MS):
    """The group velocities: the page's formula against finite differences and closed forms, the
    travelling curves' slopes against it, the tours' glides integrated, the spreading left out,
    and the packets measured on the screen (the text of the check file's part)."""
    L = []
    p = L.append
    p("GROUP VELOCITY")
    p("  Every wave's c_g is the page's own, from the eigenpair it solves: differentiating")
    p("  [K1 + k K2 + k^2 K3 - w^2 M] V = 0 in k and taking V^T of it, the terms in dV/dk cancel (K and M")
    p("  symmetric), leaving c_g = dw/dk = V^T (K2 + 2k K3) V / (2 w V^T M V) (Hellmann-Feynman): the exact")
    p("  slope of the model's own dispersion curve at that point, two skyline products per state.")
    if "skipped" not in SV:
        p("  The page's script under node, at the solver check's random states, against scipy on the same mesh:")
        for key in ORDER:
            v = SV[key]
            p(f"    {SECTIONS[key]['label']:7s} max |c_g,page / c_g,FD - 1| = {v['egd']:.1e} (central difference of w(k), step 1e-4 k),"
              f" against scipy's eigenvector in the same formula {v['egh']:.1e}")
    p("  Against closed forms at low wavenumber (SAFE: the formula on the eigenpair by shift-invert; FD a central")
    p("  difference of w(k), step 0.01 rad/m):")
    p("  k (rad/m)  mode       c_g SAFE (m/s)  FD - SAFE     closed form                     c_g (m/s)   error")
    for key in ORDER:
        S, Z = make_section(key), SECTIONS[key]
        if key == "plate":
            p("  plate: the A0, S0 and SH0 phase-speed checks are listed above; c_g checked against FD by the page solver check.")
            continue
        P = properties(S)
        T = torsion(S)
        kap = 10 * (1 + sm.NU) / (12 + 11 * sm.NU) if key == "bar" else None
        ks = (1.0, 2.0, 5.0, 10.0, 20.0, 40.0) if key == "bar" else (1.0, 2.0, 5.0, 10.0)
        p(f"  {Z['label']}:")
        for k in ks:
            ref = group_closed(k, P, T, kap=kap)
            got = {}
            rows = [("vertical", "Euler-Bernoulli (2 c_p)", ref["vertical_EB"])]
            if key == "bar":
                rows += [("vertical", "Timoshenko", ref["vertical_Timo"]), ("lateral", "Euler-Bernoulli (2 c_p)", ref["lateral_EB"]),
                         ("lateral", "Timoshenko", ref["lateral_Timo"])]
            elif key != "pipe":
                rows += [("lateral", "Euler-Bernoulli (2 c_p)", ref["lateral_EB"])]
            rows += [("axial", "rod c_0", ref["axial_rod"]), ("axial", "Love rod", ref["axial_Love"])]
            if key == "pipe":
                rows += [("torsional", "T(0,1): c_T", sm.C_T)]
            elif key == "ibeam":
                rows += [("torsional", "Vlasov, + E Gamma k^2", ref["torsional_Vlasov"])]
            else:
                rows += [("torsional", "Saint-Venant sqrt(GJ/(rho I_p))", ref["torsional_SV"])]
            for typ, lab, c in rows:
                name, b = Z["fund"][typ]
                if typ not in got:                  # shift-invert from the dense solve's w, accurate at small w
                    w, cg = group_near(S, name, k, S.omegas(name, k, b + 1)[b], tol=1e-3)
                    h = .01                         # rad/m: the round-off of w and the difference's own error balance there
                    got[typ] = (cg, (group_near(S, name, k + h, w + cg * h, tol=1e-2)[0] - group_near(S, name, k - h, w - cg * h, tol=1e-2)[0]) / (2 * h))
                cg, fd = got[typ]
                p(f"  {k:6.1f}   {typ:10s} {cg:13.3f}   {fd - cg:+.1e}      {lab:31s} {c:9.3f}   {cg / c - 1:+.2e}")
    p("  (Euler-Bernoulli's c_g = 2 c_p holds as k -> 0 and parts from SAFE as shear and rotary inertia")
    p("  enter, where Timoshenko follows; the rod speed likewise, where Love's lateral inertia follows.)")
    # the travelling curves' slopes against the exact c_g
    worst = {}
    for key in ORDER:
        S, Z = make_section(key), SECTIONS[key]
        tb, tflat, _ = thinned(key, Rs[key])
        e, where = 0.0, ""
        for r in tb:
            o, n = r["o"], r["n"]
            tf, tc, tg = (np.asarray(tflat[o + j * n:o + (j + 1) * n], np.float64) for j in range(3))
            K, Wk = 2 * np.pi * tf / tc, 2 * np.pi * tf
            kin = K[(tf <= F_MAX / 1e3) & (tc <= CP_MAX / 1e3)]
            name = Z["classes"][r["ci"]][0]
            for k in np.linspace(kin.min(), kin.max(), 42)[1:-1]:
                i = min(max(int(np.searchsorted(K, k, side="right")) - 1, 0), len(K) - 2)
                h, s = K[i + 1] - K[i], (k - K[i]) / (K[i + 1] - K[i])
                herm = ((6 * s * s - 6 * s) * Wk[i] + (6 * s - 6 * s * s) * Wk[i + 1]) / h + (3 * s * s - 4 * s + 1) * tg[i] + (3 * s * s - 2 * s) * tg[i + 1]
                w0 = 1e3 * _herm(K[i], Wk[i], tg[i], K[i + 1], Wk[i + 1], tg[i + 1], k)     # rad/s
                cg = group_near(S, name, k, w0)[1]
                if abs(herm * 1e3 / cg - 1) > e:
                    e, where = abs(herm * 1e3 / cg - 1), f"{r['nm']}, {w0 / 2e3 / np.pi:.0f} kHz"
        worst[key] = (e, where)
    p("  The travelling curves carry slopes too (the spline's, for the cubic Hermite that draws them), but")
    p("  not to this accuracy: along every branch inside the window, 40 states each, their slope against")
    p("  the exact c_g: " + "; ".join(f"{SECTIONS[k]['label']} {worst[k][0]:.1e} ({worst[k][1]})" for k in ORDER) + ".")
    p("  The worst lie at veerings, where two branches of a class nearly touch and c_g turns within a")
    p("  fraction of a kHz. So the waves never use them: c_g always comes from a solved state.")
    # the glides
    p(f"  The tour's glides: wave 2's rates solved at {TOUR_T['NG'] + 1} moments evenly spread over the 8 s glide, each")
    p("  interval integrated as the cubic through its four nearest (the page's rule), against Simpson")
    p(f"  on {4 * TOUR_T['NG'] + 1} moments. Largest difference in the envelope's travel over a glide (mm of the page) and")
    p("  in the phase at its centre (rad):")
    for key in ORDER:
        S, Z = make_section(key), SECTIONS[key]
        tb, curves = page_curve(key, Rs[key])
        brs, flat = curves_of(key, Rs[key])
        dx = dp = tot = 0.0
        for s in tour_of(key, brs, flat):
            cv, name = curves[s["b2"]], Z["classes"][tb[s["b2"]]["ci"]][0]
            N = 4 * TOUR_T["NG"]
            v, r = [], []
            for j in range(N + 1):
                k = k_at_f(cv, s["fa"] if j == 0 else s["f2"] if j == N else s["fa"] + (s["f2"] - s["fa"]) * ease_in_out(j / N))
                w, cg = group_near(S, name, k, 2e3 * np.pi * float(np.interp(k, cv[0], cv[1])))
                v.append(cg * 1e3 / SLOW)
                r.append((k * cg - w) / SLOW)
            from scipy.integrate import simpson
            for y, acc in ((v, "x"), (r, "p")):
                d_ = abs(glide_integral(y[::4], TOUR_T["TGD"]) - simpson(y, dx=TOUR_T["TGD"] / N))
                if acc == "x":
                    dx, tot = max(dx, d_), max(tot, simpson(y, dx=TOUR_T["TGD"] / N))
                else:
                    dp = max(dp, d_)
        p(f"    {Z['label']:7s} {dx:.1e} mm (of up to {tot:.0f} mm travelled in a glide), {dp:.1e} rad")
    # the tours' c_g, and what the rigid envelope leaves out
    p("  The spreading left out: the envelope rides at c_g unchanged (the first order in the burst's")
    p(f"  bandwidth). A Gaussian burst of the packet's rms width ({SIG:.1f} mm) would widen over one passage")
    p(f"  (D = {BEAM:.0f} + {PACKET:.0f} mm) by sqrt(1 + (w'' D / (2 c_g sigma^2))^2), w'' = dc_g/dk: at the tours' states")
    for key in ORDER:
        ws = [row[l][4] for row in TG[key] for l in ("w1", "wa", "w2")]
        big = max(((row[l][4], row[l][0]) for row in TG[key] for l in ("w1", "wa", "w2")))
        p(f"    {SECTIONS[key]['label']:7s} median {np.median(ws):.2f}, largest {big[0]:.2f} (at {big[1]:.0f} kHz)")
    p("  A burst of one or two cycles on a dispersive branch would smear as it goes. The figure shows the")
    p("  group velocity's own picture: the envelope carried whole at c_g, which a burst narrow enough in")
    p("  band keeps; the widening above is what this short one would add, left out.")
    # on the screen
    if MS:
        p("  Measured on the screen (Playwright, the page at 1000 px, two pixels a unit): each beam's top")
        p("  outline read from its picture at moments 0.1 s apart (the ink's upper boundary by its coverage),")
        p("  fitted with the outline the page draws (the top-back node's path, packet centre X0 + v t, phase")
        p("  at the centre psi0 + r t, all moments at once); the envelope's speed v and the crests'")
        p("  v - r / k, times SLOW, against the state's c_g and c_p:")
        for c in MS:
            p(f"    {c['case']:20s} wave {c['w']}: {c['nm']}, {c['f']:.1f} kHz, {c['n']} moments over {c['span']:.1f} s;"
              f" fit rms {c['res']:.3f} units")
            p(f"      c_g {c['cg']:.4f} km/s, on screen {c['cg_s']:.4f} ({c['cg_s'] / c['cg'] - 1:+.1e});"
              f" c_p {c['cp']:.4f}, on screen {c['cp_s']:.4f} ({c['cp_s'] / c['cp'] - 1:+.1e})")
        t1 = [c for c in MS if c["case"] == "tour"]
        if len(t1) == 2:
            p(f"    the two beams: envelope speeds on screen in the ratio {t1[1]['cg_s'] / t1[0]['cg_s']:.4f}, c_g in the ratio"
              f" {t1[1]['cg'] / t1[0]['cg']:.4f}; crest over envelope {t1[0]['cp_s'] / t1[0]['cg_s']:.4f} and"
              f" {t1[1]['cp_s'] / t1[1]['cg_s']:.4f}, c_p / c_g {t1[0]['cp'] / t1[0]['cg']:.4f} and {t1[1]['cp'] / t1[1]['cg']:.4f}")
        dr = [c for c in MS if c["case"].startswith(("click", "drag"))]
        if len(dr) == 2:
            p(f"    the drag slowed wave 1's packet {dr[0]['cg_s'] / dr[1]['cg_s']:.3f} times on screen (c_g: {dr[0]['cg'] / dr[1]['cg']:.3f}), its crests")
            p(f"    running {dr[1]['cp_s'] / dr[1]['cg_s']:.2f} times the envelope's speed through it at 62 kHz.")
        p("  The residual differences are the picture's: a packet only 1.5 wavelengths long pins its centre")
        p("  to about 0.2 mm a moment, the crests (whose phase every pixel column sees) far better.")
    p("")
    return L


# The page controls (common.py) cover the bottom right: two 28 px buttons 6 px apart and
# from the edge (68 px), or 22 px, 4 and 3 px (51 px) at 480 px wide and under, one 18 px
# button under 300 px. The parameter line runs along the bottom from x = 18 at 14 units:
# it must end left of 1000 - 51 * 1000 / 301 = 830 units to clear them at every width.
PARAM_MAX = 830


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def overlaps_all(times, live=False, width=672):
    """common.overlaps for every section: the page is served with its .json files,
    each section chosen in turn (setSectionNow), and each moment drawn (the tour's
    clock set); then switches frozen half way. {section: {moment: faults}}; the
    moments with faults are photographed to the temp folder."""
    from playwright.sync_api import sync_playwright

    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = {}
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        for n in os.listdir(common.ANIM):
            if n.startswith(f"nf-{NAME}") and not n.endswith(".webp"):
                shutil.copy(os.path.join(common.ANIM, n), os.path.join(tmp, "anim", n))
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=tmp))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            q = "overlap" if live else "still&overlap"
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?{q}")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            if live:
                pg.evaluate("setPlay(false)")

            def grab(key, moment):
                lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                # and the two markers apart (their discs are drawn, not type: the check above
                # does not see them): at least one diameter between their centres when both show
                gap = pg.evaluate("(() => { if (SW || USER) return 99; const q = tourAt(CUR, t - TOUR.off), a = LAST[0], b = LAST[1];"
                                  " return q.mk[0] > .35 && q.mk[1] > .35 ? Math.hypot(PX(a.f) - PX(b.f), PY(a.cp) - PY(b.cp)) : 99; })()")
                if gap < 21:
                    lab = lab + [["marker 1", "marker 2", round(gap, 1), 0]]
                wp = pg.evaluate("18 + textW(CUR.params, 14)")
                if live and wp > PARAM_MAX:
                    lab = lab + [["parameters", "page controls", round(wp), PARAM_MAX]]
                if lab or cro:
                    out.setdefault(key, {})[moment] = {"labels": lab, "crossings": cro}
                    pg.locator("canvas").screenshot(path=os.path.join(
                        tempfile.gettempdir(), f"nf-{NAME}-{'live-' if live else ''}overlap-{key}-{moment}.png"))

            for key in ORDER:
                pg.evaluate(f"setSectionNow('{key}')")
                pg.wait_for_function(f"CUR.key === '{key}'", timeout=30000)
                for s in times:
                    pg.evaluate(f"() => {{ t = {s:.6g}; render(); }}")
                    grab(key, f"t{s:g}")
                out.setdefault(key, {})
            for a, c in zip(ORDER, ORDER[1:] + ORDER[:1]):
                for pp in (0.3, 0.6, 0.85):
                    pg.evaluate(f"() => {{ freezeSwitch('{a}', '{c}', {pp}); t = {POSTER:.6g}; render(); }}")
                    grab(f"{a}-{c}", f"p{pp:g}")
                pg.evaluate("freezeSwitch(null)")
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


STR_S, STR_YC, STR_X1 = 2.2, (580, 746), 950   # the page's beams: units per mm, their centre lines, x = 0


def _outline(img, w, sc):
    """Beam w's top outline in a canvas image of sc pixels a drawing unit: per pixel column over
    the beam, the upper boundary of the first ink met from the white above, to a fraction of a
    pixel by the ink's coverage (the rows it partly covers, summed up to the first it covers
    wholly: exact for an edge smoothed by area), searched from 88 units over the beam's centre
    line to 30. The columns start 40 units in from the left end, past its slanting top face."""
    ink = 0.2126 * 0x27 + 0.7152 * 0x22 + 0.0722 * 0x1C
    Lum = img[..., :3].astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    cov = np.clip((255 - Lum) / (255 - ink), 0, 1)
    r0, r1 = int((STR_YC[w] - 88) * sc), int((STR_YC[w] - 30) * sc)
    X, Y = [], []
    for c in range(int((STR_X1 - STR_S * BEAM + 40) * sc), int((STR_X1 - 8) * sc)):
        col = cov[r0:r1, c]
        full = np.flatnonzero(col > .97)
        if not len(full) or full[0] < 3:
            continue
        f0 = full[0]
        X.append(c + .5)
        Y.append(r0 + f0 - col[max(f0 - 3, 0):f0].sum())
    return np.array(X), np.array(Y)


def _fit_packet(X, Y, kp, Wp):
    """Fit Y = Y0 + E(X - Xc) (a cos kp(X - Xc) + b sin kp(X - Xc)), E the Hann envelope Wp pixels
    across: for each trial centre the rest is linear least squares; the centre by a scan and a
    bounded search. Returns (Xc, the carrier's phase at Xc, rms residual in pixels)."""
    from scipy.optimize import minimize_scalar

    def solve(xc):
        u = X - xc
        E = np.where(np.abs(u) < Wp / 2, np.cos(np.pi * u / Wp) ** 2, 0.0)
        A = np.column_stack([np.ones_like(X), E * np.cos(kp * u), E * np.sin(kp * u)])
        coef = np.linalg.lstsq(A, Y, rcond=None)[0]
        r = Y - A @ coef
        return r @ r, coef

    grid = np.arange(X.min() - Wp / 2, X.max() + Wp / 2, 2.0)
    x0 = grid[int(np.argmin([solve(x)[0] for x in grid]))]
    xc = minimize_scalar(lambda x: solve(x)[0], bounds=(x0 - 3, x0 + 3), method="bounded", options={"xatol": 1e-5}).x
    cost, (_, a, b) = solve(xc)
    return xc, np.arctan2(-b, a), np.sqrt(cost / len(X))


def _outline_model(X, Y, m, sc):
    """The misfit of an outline (X, Y pixels) to the one the page draws: the top-back node's path
    along the beam by stripView's own formulas (its U, the drawn scale g, the samples 1 mm apart
    joined by straight lines) with the packet centred at p[0] (mm) and the phase p[1] at its centre,
    moved down by p[2] pixels (the ink's half width and the threshold)."""
    x = np.arange(-BEAM, 0.5, 1.0)
    CD, SD = .6 * np.cos(np.radians(40)), .6 * np.sin(np.radians(40))

    def resid(p):
        xi = x - p[0]
        E = np.where(np.abs(xi) < PACKET / 2, np.cos(np.pi * xi / PACKET) ** 2, 0.0)
        cs, sn = E * np.cos(m["k"] * xi + p[1]), E * np.sin(m["k"] * xi + p[1])
        d = m["e"] + m["g"] * m["u"][1] * cs
        Xp = sc * (STR_X1 + STR_S * (x - m["g"] * m["u"][0] * sn + d * CD))
        Yp = sc * (m["yc"] - STR_S * (m["z"] + m["g"] * m["u"][2] * cs + d * SD))
        return np.interp(X, Xp, Yp) + p[2] - Y
    return resid


def _fit_outline(X, Y, m, sc):
    """One moment's packet from its outline: the centre from _fit_packet, the phase the best of 16,
    then _outline_model's misfit least squared. Returns (Xc mm, psi, rms residual in pixels)."""
    from scipy.optimize import least_squares
    resid = _outline_model(X, Y, m, sc)
    CD = .6 * np.cos(np.radians(40))
    xc = (_fit_packet(X, Y, m["k"] / (STR_S * sc), PACKET * STR_S * sc)[0] / sc - STR_X1) / STR_S - m["e"] * CD
    spread = lambda q: float(np.sum((resid(q) - np.median(resid(q))) ** 2))
    best = min(((xc, ps, 0.0) for ps in np.arange(16) * np.pi / 8), key=spread)
    r = least_squares(resid, [best[0], best[1], -np.median(resid(best))], x_scale=[1.0, .1, 1.0], xtol=1e-12, ftol=1e-12)
    return r.x[0], r.x[1], float(np.sqrt(np.mean(r.fun ** 2)))


def _fit_motion(ts, outlines, m, sc, fits):
    """All the moments at once: the centre X0 + v t and the phase psi0 + r t (the page's motion while
    a state holds) and one vertical offset, least squared over every outline together, from the
    moments' own fits. This parts the envelope from the carrier where the wavelength outgrows the
    packet and one moment alone can trade one for the other. Returns (v mm/s, r rad/s, rms px)."""
    from scipy.optimize import least_squares
    ts = np.asarray(ts)
    pe = np.polyfit(ts, [f[0] for f in fits], 1)
    pr = np.polyfit(ts, np.unwrap([f[1] for f in fits]), 1)
    res = [_outline_model(X, Y, m, sc) for X, Y in outlines]
    dY = float(np.median([np.median(rf([f[0], f[1], 0.0])) for rf, f in zip(res, fits)]))

    def all_(p):
        return np.concatenate([rf([p[0] + p[1] * s, p[2] + p[3] * s, p[4]]) for rf, s in zip(res, ts)])

    r = least_squares(all_, [pe[1], pe[0], pr[1], pr[0], -dY], x_scale=[1.0, 1.0, .1, .1, 1.0], xtol=1e-13, ftol=1e-13)
    return r.x[1], r.x[3], float(np.sqrt(np.mean(r.fun ** 2)))


def _speeds(ts, fits, k):
    """From (Xc mm, psi) at the moments ts: the envelope's speed and the crests' (mm a second of the
    page, straight-line fits; psi unwrapped, a crest where k (x - Xc) + psi is a whole turn), and
    the largest departure of either from its line (mm)."""
    Xc = np.array([f[0] for f in fits])
    C = Xc - np.unwrap([f[1] for f in fits]) / k
    pe, pc = np.polyfit(ts, Xc, 1), np.polyfit(ts, C, 1)
    return pe[0], pc[0], float(max(np.abs(Xc - np.polyval(pe, ts)).max(), np.abs(C - np.polyval(pc, ts)).max()))


def measure_screen():
    """The packets measured on the screen: the page at 1000 px, two pixels a drawing unit, and each
    beam's top outline read from its pictures (_outline) and fitted with its packet (_fit_packet)
    at moments 0.1 s apart. The tour's first stop on the bar (both beams, the poster's moment
    +- 0.6 s); then the reader: a click moves wave 1 onto the axial curve at 30 kHz, a drag takes
    it to 62 kHz (where the axial branch's c_g is least). Speeds in km/s of the beam: pixels a
    second / (2 x 2.2 px/mm) x SLOW. Returns the cases."""
    from PIL import Image
    from playwright.sync_api import sync_playwright
    import io

    sc = 2
    tmp = tempfile.mkdtemp(prefix="numfig-")
    cases = []
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        for n in os.listdir(common.ANIM):
            if n.startswith(f"nf-{NAME}") and not n.endswith(".webp"):
                shutil.copy(os.path.join(common.ANIM, n), os.path.join(tmp, "anim", n))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html"
        with sync_playwright() as p:
            b = p.chromium.launch()

            def page(q):
                pg = b.new_page(viewport={"width": 1000, "height": 1400}, device_scale_factor=sc)
                pg.goto(url + q)
                pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
                return pg

            def run(pg, label, ws, times):
                # each wave's state as the page holds it, and the node its outline is drawn from
                # (the highest in the oblique view: the top-back one)
                st = pg.evaluate("[0, 1].map(w => { const S = LAST[w]; let n = 0, bv = -1e9;"
                                 " for (let q = 0; q < CUR.N; q++) { const v = CUR.GZ[q] + (CUR.GY[q] - CUR.ymin) * SD; if (v > bv) { bv = v; n = q; } }"
                                 " return {k: S.k, cg: S.cg, cp: S.cp, f: S.f, lam: S.lam, nm: CUR.BR[S.id].nm,"
                                 " u: [S.U[3 * n], S.U[3 * n + 1], S.U[3 * n + 2]], e: CUR.GY[n] - CUR.ymin, z: CUR.GZ[n]}; })")
                fits, held, outl = {w: [] for w in ws}, {w: [] for w in ws}, {w: [] for w in ws}
                ms = {}
                for s in times:
                    q = pg.evaluate(f"() => {{ t = {s:.6f}; render(); const q = stateNow(); return {{amp: q.amp, X: q.X.map(wrapX), ps: q.ps}}; }}")
                    img = np.array(Image.open(io.BytesIO(pg.locator("canvas").screenshot())))
                    for w in ws:
                        ms[w] = m = dict(st[w], k=st[w]["k"] / 1e3, yc=STR_YC[w], g=min(11, .5 * STR_S * st[w]["lam"] / (2 * np.pi)) * q["amp"] / STR_S)
                        outl[w].append(_outline(img, w, sc))
                        fits[w].append(_fit_outline(*outl[w][-1], m, sc))
                        held[w].append((q["X"][w], q["ps"][w]))
                for w in ws:
                    ts = np.array(times) - times[0]
                    v, r, rms = _fit_motion(ts, outl[w], ms[w], sc, fits[w])
                    k = ms[w]["k"]
                    hx = np.polyfit(ts, [h[0] for h in held[w]], 1)[0]
                    cases.append({"case": label, "w": w + 1, "nm": st[w]["nm"], "f": st[w]["f"], "cg": st[w]["cg"], "cp": st[w]["cp"],
                                  "cg_s": v * SLOW / 1e6, "cp_s": (v - r / k) * SLOW / 1e6, "res": rms / sc,
                                  "cg_1": _speeds(ts, fits[w], k)[0] * SLOW / 1e6, "cg_state": hx * SLOW / 1e6,
                                  "n": len(times), "span": times[-1] - times[0]})
                return st

            # the tour's first stop on the bar, printed moments around the poster's
            pg = page("?still")
            run(pg, "tour", (0, 1), [POSTER + .1 * j for j in range(-10, 11)])
            pg.close()
            # the reader: a click on the axial curve at 30 kHz takes wave 1 there, a drag to 62 kHz
            pg = page("")
            pg.wait_for_timeout(1200)
            at = lambda js: pg.evaluate(f"(() => {{ const r = cv.getBoundingClientRect(), [x, y] = {js};"
                                        " return [r.left + x * r.width / W, r.top + y * r.height / H]; })()")
            ax = "CUR.BR[CUR.fund.axial]"
            pg.mouse.click(*at(f"[PX(30), PY(cpAtF({ax}, 30))]"))
            pg.evaluate("setPlay(false)")

            def settle_at(x_mm):                      # the clock run on until wave 1's packet is centred near x_mm
                pg.evaluate(f"() => {{ for (let j = 0; j < 20000; j++) {{ t += .01; stateNow(); const X = wrapX(USER.X[0]);"
                            f" if (Math.abs(X - ({x_mm})) < 3 && t - USER.t0 > 1.2) break; }} render(); }}")
                return pg.evaluate("t")

            t0 = settle_at(-380)
            run(pg, "click, axial 30 kHz", (0,), [t0 + .1 * j for j in range(15)])
            x0, y0 = at("[PX(LAST[0].f), PY(LAST[0].cp)]")
            pg.mouse.move(x0, y0)
            pg.mouse.down()
            for j in range(1, 25):
                f = 30 + 32 * j / 24
                pg.mouse.move(*at(f"[PX({f}), PY(cpAtF({ax}, {f}))]"))
            pg.mouse.up()
            t0 = settle_at(-330)
            run(pg, "drag, axial 62 kHz", (0,), [t0 + .1 * j for j in range(21)])
            pg.close()
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return cases


def tour_times():
    """Moments across the tour for the overlap check: the intro, the first stop,
    and each later stop's arrival, glide, hold and rest."""
    ts = [.3, .6, .9, 1.2, 1.6, 2.5, POSTER, 12, 15.5]
    for n in range(5):
        t0 = 16 + 18 * n
        ts += [t0 + d for d in (.2, .5, 1, 2, 4, 6, 8, 10, 14, 17.2)]
    return ts


# ================================================================ the page
SOLVER = r"""
/* ---------------------------------------------------------------- SAFE
   The cross-section's own model, solved in the page: 9-node quadratic
   elements (isoparametric, 3 x 3 Gauss) on the section's mesh, three
   displacements a node, [K1 + k K2 + k^2 K3 - w^2 M] V = 0 with U_x = i V_x.
   The mesh's symmetry splits the problem into classes, each solved on its
   own orthonormal basis: mirror classes (the parity of each mirror plane),
   or, for a pipe's uniform polar mesh, circumferential harmonics (the exact
   block diagonalisation of its dihedral symmetry). A class's matrices are
   kept as a skyline (profile) in an RCM order; a state (class, branch, k) is
   solved exactly: LDL^T of K(k) - s M, whose negative pivots count the
   eigenvalues below s (Sylvester), pins the branch; inverse iteration then
   converges on its eigenpair. */
function safeModel(sec) {
  const Mo = sec, N = sec.nodes.length / 2, NE = sec.elems.length / 9;
  const MU = Mo.E / (2 * (1 + Mo.nu)), LAM = Mo.E * Mo.nu / ((1 + Mo.nu) * (1 - 2 * Mo.nu));
  const Dm = [[LAM + 2 * MU, LAM, LAM, 0, 0, 0], [LAM, LAM + 2 * MU, LAM, 0, 0, 0], [LAM, LAM, LAM + 2 * MU, 0, 0, 0],
              [0, 0, 0, MU, 0, 0], [0, 0, 0, 0, MU, 0], [0, 0, 0, 0, 0, MU]];
  const g3 = [-Math.sqrt(.6), 0, Math.sqrt(.6)], w3 = [5 / 9, 8 / 9, 5 / 9];
  const L = s => [s * (s - 1) / 2, 1 - s * s, s * (s + 1) / 2], dL = s => [s - .5, -2 * s, s + .5];
  const GP = [];                                        // shape functions at the Gauss points, local node 3 bb + a
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    const Lx = L(g3[i]), Le = L(g3[j]), dLx = dL(g3[i]), dLe = dL(g3[j]), N_ = [], Nx = [], Ne = [];
    for (let bb = 0; bb < 3; bb++) for (let a = 0; a < 3; a++) { N_.push(Le[bb] * Lx[a]); Nx.push(Le[bb] * dLx[a]); Ne.push(dLe[bb] * Lx[a]); }
    GP.push({N: N_, Nx, Ne, w: w3[i] * w3[j]});
  }
  const X = i => sec.nodes[2 * i] * 1e-3, Y = i => sec.nodes[2 * i + 1] * 1e-3;   // m
  const ecache = new Map();
  /* the matrices of element e (27 x 27 each), shared by elements of one shape */
  function element(e) {
    const nd = sec.elems.subarray(9 * e, 9 * e + 9), y0 = X(nd[0]), z0 = Y(nd[0]);
    const xy = Array.from(nd, n => [X(n) - y0, Y(n) - z0]);
    const key = xy.map(([a, b]) => Math.round(a * 1e9) + ',' + Math.round(b * 1e9)).join(';');
    let m = ecache.get(key);
    if (m) return m;
    const K1 = new Float64Array(729), K2 = new Float64Array(729), K3 = new Float64Array(729), Me = new Float64Array(729);
    for (const G of GP) {
      let a11 = 0, a12 = 0, a21 = 0, a22 = 0;
      for (let l = 0; l < 9; l++) { a11 += G.Nx[l] * xy[l][0]; a12 += G.Nx[l] * xy[l][1]; a21 += G.Ne[l] * xy[l][0]; a22 += G.Ne[l] * xy[l][1]; }
      const det = a11 * a22 - a12 * a21, i11 = a22 / det, i12 = -a12 / det, i21 = -a21 / det, i22 = a11 / det;
      const Ny = G.Nx.map((v, l) => i11 * v + i12 * G.Ne[l]), Nz = G.Nx.map((v, l) => i21 * v + i22 * G.Ne[l]);
      const B1 = Array.from({length: 6}, () => new Float64Array(27)), B2 = Array.from({length: 6}, () => new Float64Array(27));
      for (let l = 0; l < 9; l++) {
        B1[1][3 * l + 1] = Ny[l]; B1[2][3 * l + 2] = Nz[l];
        B1[3][3 * l + 1] = Nz[l]; B1[3][3 * l + 2] = Ny[l];
        B1[4][3 * l] = Nz[l]; B1[5][3 * l] = Ny[l];
        B2[0][3 * l] = G.N[l]; B2[4][3 * l + 2] = G.N[l]; B2[5][3 * l + 1] = G.N[l];
      }
      const dA = G.w * det;
      const DB = B => B.map((_, r) => new Float64Array(27).map((_, c) => Dm[r].reduce((s, d, q) => s + d * B[q][c], 0)));
      const DB1 = DB(B1), DB2 = DB(B2);
      for (let a = 0; a < 27; a++) for (let c = 0; c < 27; c++) {
        let s1 = 0, s12 = 0, s21 = 0, s3 = 0;
        for (let r = 0; r < 6; r++) { s1 += B1[r][a] * DB1[r][c]; s12 += B1[r][a] * DB2[r][c]; s21 += B2[r][a] * DB1[r][c]; s3 += B2[r][a] * DB2[r][c]; }
        K1[a * 27 + c] += s1 * dA; K2[a * 27 + c] += (s12 - s21) * dA; K3[a * 27 + c] += s3 * dA;
        if (a % 3 === c % 3) Me[a * 27 + c] += Mo.rho * G.N[a / 3 | 0] * G.N[c / 3 | 0] * dA;
      }
    }
    // U_x = i V_x makes K2 real symmetric: axial rows against in-plane columns keep
    // their sign, in-plane rows against the axial column change it, the rest vanish
    for (let a = 0; a < 27; a++) for (let c = 0; c < 27; c++) {
      const ax = a % 3 === 0, cx = c % 3 === 0;
      K2[a * 27 + c] *= ax && !cx ? 1 : !ax && cx ? -1 : 0;
    }
    m = [K1, K2, K3, Me];
    ecache.set(key, m);
    return m;
  }
  /* each class's basis: every dof in at most two columns (col0, v0; col1, v1) */
  const bases = {};
  function basis(ci) {
    if (bases[ci]) return bases[ci];
    const C = sec.classes[ci], nd = 3 * N;
    const c0 = new Int32Array(nd).fill(-1), c1 = new Int32Array(nd).fill(-1), v0 = new Float64Array(nd), v1 = new Float64Array(nd);
    let m = 0;
    const put = (g, col, v) => { if (c0[g] < 0) { c0[g] = col; v0[g] = v; } else { c1[g] = col; v1[g] = v; } };
    if (sec.kind === 'mirror') {
      const key = (y, z) => Math.round(y * 1e3) + ',' + Math.round(z * 1e3), at = new Map();
      for (let n = 0; n < N; n++) at.set(key(sec.nodes[2 * n], sec.nodes[2 * n + 1]), n);
      const my = Int32Array.from({length: N}, (_, n) => at.get(key(-sec.nodes[2 * n], sec.nodes[2 * n + 1])));
      const mz = Int32Array.from({length: N}, (_, n) => at.get(key(sec.nodes[2 * n], -sec.nodes[2 * n + 1])));
      const G = [[n => n, 1, [1, 1, 1]]];
      if (C.py) G.push([n => my[n], C.py, [1, -1, 1]]);
      if (C.pz) G.push([n => mz[n], C.pz, [1, 1, -1]]);
      if (C.py && C.pz) G.push([n => my[mz[n]], C.py * C.pz, [1, -1, -1]]);
      const reps = [];
      for (let n = 0; n < N; n++) if (sec.rank[n] >= 0) reps[sec.rank[n]] = n;
      for (const n of reps) for (let c = 0; c < 3; c++) {
        const v = new Map();
        for (const [g, chi, sg] of G) { const d = 3 * g(n) + c; v.set(d, (v.get(d) || 0) + chi * sg[c]); }
        let s2 = 0;
        for (const x of v.values()) s2 += x * x;
        if (s2 < 1e-12) continue;
        for (const [d, x] of v) if (Math.abs(x) > 1e-12) put(d, m, x / Math.sqrt(s2));
        m++;
      }
    } else if (sec.kind === 'plate') {
      const z = Array.from({length: N}, (_, n) => Math.round(sec.nodes[2 * n + 1] * 1e4) / 1e4);
      const levels = [...new Set(z.map(Math.abs))].sort((a, b) => a - b);
      for (const zz of levels) for (const c of C.family === 'SH' ? [1] : [0, 2]) {
        const sign = C.parity * (c === 2 ? -1 : 1);
        if (zz === 0 && sign < 0) continue;
        const sel = [];
        for (let n = 0; n < N; n++) if (Math.abs(Math.abs(z[n]) - zz) < 1e-6) sel.push(n);
        for (const n of sel) put(3 * n + c, m, (z[n] < 0 ? sign : 1) / Math.sqrt(sel.length));
        m++;
      }
    } else {                                            // a harmonic n of type V or L on a polar mesh
      const r = [], ph = [], par = [];
      for (let q = 0; q < N; q++) {
        const y = sec.nodes[2 * q], z = sec.nodes[2 * q + 1];
        r.push(Math.round(Math.hypot(y, z) * 1e3));
        const j = ((Math.round(Math.atan2(z, y) / (Math.PI / sec.nth)) % (2 * sec.nth)) + 2 * sec.nth) % (2 * sec.nth);
        ph.push(j * Math.PI / sec.nth); par.push(j % 2);
      }
      const rings = [...new Set(r)].sort((a, b) => a - b), n = C.n;
      const [fr, ft, fx, st] = C.typ === 'V' ? [Math.sin, Math.cos, Math.sin, 1] : [Math.cos, Math.sin, Math.cos, -1];
      for (const R of rings) for (const p of [0, 1]) {
        const sel = [];
        for (let q = 0; q < N; q++) if (r[q] === R && par[q] === p) sel.push(q);
        for (const comp of ['r', 't', 'x']) {
          const ent = [];
          for (const q of sel) {
            const a = comp === 'r' ? fr(n * ph[q]) : comp === 't' ? st * ft(n * ph[q]) : fx(n * ph[q]);
            if (comp === 'r') { ent.push([3 * q + 1, a * Math.cos(ph[q])]); ent.push([3 * q + 2, a * Math.sin(ph[q])]); }
            else if (comp === 't') { ent.push([3 * q + 1, -a * Math.sin(ph[q])]); ent.push([3 * q + 2, a * Math.cos(ph[q])]); }
            else ent.push([3 * q, a]);
          }
          let s2 = 0;
          for (const [, x] of ent) s2 += x * x;
          if (s2 < 1e-12) continue;
          for (const [d, x] of ent) if (Math.abs(x) > 1e-14) put(d, m, x / Math.sqrt(s2));
          m++;
        }
      }
    }
    return (bases[ci] = {m, c0, c1, v0, v1});
  }
  /* a class's four matrices as a skyline: row i holds columns first[i]..i at ptr[i] */
  const classes = {};
  function cls(ci) {
    if (classes[ci]) return classes[ci];
    const Bs = basis(ci), n = Bs.m, first = new Int32Array(n);
    for (let i = 0; i < n; i++) first[i] = i;
    const cols = g => { const o = []; if (Bs.c0[g] >= 0) o.push(Bs.c0[g]); if (Bs.c1[g] >= 0) o.push(Bs.c1[g]); return o; };
    for (let e = 0; e < NE; e++) {
      const cs = [];
      for (let l = 0; l < 9; l++) for (let c = 0; c < 3; c++) cs.push(...cols(3 * sec.elems[9 * e + l] + c));
      let lo = Infinity;
      for (const c of cs) lo = Math.min(lo, c);
      for (const c of cs) first[c] = Math.min(first[c], lo);
    }
    const ptr = new Int32Array(n + 1);
    for (let i = 0; i < n; i++) ptr[i + 1] = ptr[i] + i - first[i] + 1;
    const mats = [0, 1, 2, 3].map(() => new Float64Array(ptr[n]));
    for (let e = 0; e < NE; e++) {
      const Ke = element(e), dof = [];
      for (let l = 0; l < 9; l++) for (let c = 0; c < 3; c++) dof.push(3 * sec.elems[9 * e + l] + c);
      for (let a = 0; a < 27; a++) {
        const ga = dof[a];
        for (const [ca, va] of [[Bs.c0[ga], Bs.v0[ga]], [Bs.c1[ga], Bs.v1[ga]]]) {
          if (ca < 0) continue;
          for (let b = 0; b < 27; b++) {
            const gb = dof[b];
            for (const [cb, vb] of [[Bs.c0[gb], Bs.v0[gb]], [Bs.c1[gb], Bs.v1[gb]]]) {
              if (cb < 0 || cb > ca) continue;
              const at = ptr[ca] + cb - first[ca], f = va * vb;
              for (let q = 0; q < 4; q++) mats[q][at] += f * Ke[q][a * 27 + b];
            }
          }
        }
      }
    }
    return (classes[ci] = {n, first, ptr, K1: mats[0], K2: mats[1], K3: mats[2], M: mats[3]});
  }
  function ldl(A, C) {                                  // in place: L below the diagonal, D apart
    const {n, first, ptr} = C, d = new Float64Array(n), u = new Float64Array(n);
    let neg = 0;
    for (let i = 0; i < n; i++) {
      const fi = first[i], pi = ptr[i] - fi;
      for (let j = fi; j < i; j++) {
        const fj = first[j], pj = ptr[j] - fj;
        let s = A[pi + j];
        for (let q = Math.max(fi, fj); q < j; q++) s -= u[q] * A[pj + q];
        u[j] = s; A[pi + j] = s / d[j];
      }
      let dd = A[pi + i];
      for (let q = fi; q < i; q++) dd -= u[q] * A[pi + q];
      if (Math.abs(dd) < 1e-300) dd = 1e-300;
      d[i] = dd; if (dd < 0) neg++;
    }
    return {d, neg};
  }
  function ldlSolve(A, C, d, b) {
    const {n, first, ptr} = C, x = Float64Array.from(b);
    for (let i = 0; i < n; i++) { const pi = ptr[i] - first[i]; let s = x[i]; for (let q = first[i]; q < i; q++) s -= A[pi + q] * x[q]; x[i] = s; }
    for (let i = 0; i < n; i++) x[i] /= d[i];
    for (let i = n - 1; i >= 0; i--) { const pi = ptr[i] - first[i], xi = x[i]; for (let q = first[i]; q < i; q++) x[q] -= A[pi + q] * xi; }
    return x;
  }
  function mul(A, C, x) {                               // y = A x, A symmetric in skyline storage
    const {n, first, ptr} = C, y = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      const pi = ptr[i] - first[i];
      let s = A[pi + i] * x[i];
      for (let q = first[i]; q < i; q++) { const a = A[pi + q]; s += a * x[q]; y[q] += a * x[i]; }
      y[i] += s;
    }
    return y;
  }
  const dot = (a, b) => { let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * b[i]; return s; };
  /* the eigenpair of `branch` (0 the lowest) of class ci at wavenumber k (rad/m), from the
     tabulated w of that branch (rad/s): the shift starts 1e-4 of w under it and moves
     until exactly `branch` eigenvalues lie below; x0, a neighbour's vector, keeps the sign.
     Inverse iteration from there goes to the nearest eigenvalue, which is the branch's
     (the nearest above the shift) unless one below is nearer: then the branch's alone is
     bracketed (`branch` eigenvalues under the lower end, more under the upper), the bracket
     narrowed by bisection, and the iteration run from its middle. */
  function solve(ci, branch, k, wTab, x0) {
    const C = cls(ci), len = C.ptr[C.n], K = new Float64Array(len), w2t = wTab * wTab;
    for (let i = 0; i < len; i++) K[i] = C.K1[i] + k * C.K2[i] + k * k * C.K3[i];
    const factor = s => { const A = new Float64Array(len); for (let i = 0; i < len; i++) A[i] = K[i] - s * C.M[i]; const g = ldl(A, C); g.A = A; g.s = s; return g; };
    const iterate = (F, start) => {
      let x = new Float64Array(C.n);
      if (start) x.set(start);
      else for (let i = 0; i < C.n; i++) x[i] = Math.sin(12.9898 * (i + 1)) * 43758.5453 % 1;   // a fixed start
      let w2 = F.s;
      for (let it = 0; it < 40; it++) {
        x = ldlSolve(F.A, C, F.d, mul(C.M, C, x));
        const nm = Math.sqrt(dot(x, mul(C.M, C, x)));
        for (let i = 0; i < C.n; i++) x[i] /= nm;
        const w2n = dot(x, mul(K, C, x)), done = Math.abs(w2n - w2) < 1e-13 * w2n;
        w2 = w2n;
        if (done && it > 0) break;
      }
      return {x, w2};
    };
    let off = 2e-4, lo = -Infinity, hi = Infinity, f = null, tries = 0;
    for (let s = w2t * (1 - off); ; ) {
      f = factor(s);
      if (f.neg === branch || ++tries > 80) break;
      if (f.neg > branch) hi = s; else lo = s;
      if (lo > -Infinity && hi < Infinity) s = (lo + hi) / 2;
      else { off *= 4; s = w2t * (f.neg > branch ? 1 - off : 1 + off); }
    }
    const count = f.neg;
    lo = f.s;
    let r = iterate(f, x0 && x0.length === C.n ? x0 : null);
    if (!(r.w2 > lo && r.w2 < hi)) {
      for (let j = 0; hi === Infinity && j < 40; j++) {
        const s = f.s * (1 + 1e-3 * 2 ** j), g = factor(s); tries++;
        if (g.neg > branch) hi = s; else lo = s;
      }
      for (let j = 0; j < 60 && hi - lo > 1e-6 * hi; j++) { const m = (lo + hi) / 2, g = factor(m); tries++; if (g.neg > branch) hi = m; else lo = m; }
      r = iterate(factor((lo + hi) / 2), null);
    }
    return {w: Math.sqrt(r.w2), x: r.x, count, tries, ok: count === branch && r.w2 > lo && r.w2 < hi};
  }
  /* the nodal field (ux, uy, uz at every node) of a class vector */
  function nodal(ci, x) {
    const B = basis(ci), U = new Float64Array(3 * N);
    for (let g = 0; g < 3 * N; g++) {
      if (B.c0[g] >= 0) U[g] += B.v0[g] * x[B.c0[g]];
      if (B.c1[g] >= 0) U[g] += B.v1[g] * x[B.c1[g]];
    }
    return U;
  }
  /* the group velocity of a solved state (m/s): differentiating [K(k) - w^2 M] V = 0 in k and
     taking V^T of it (K symmetric) leaves dw/dk = V^T (K2 + 2k K3) V / (2 w V^T M V), the exact
     slope of the model's own dispersion curve at its eigenpair (Hellmann-Feynman) */
  function cg(ci, k, x, w) {
    const C = cls(ci);
    return (dot(x, mul(C.K2, C, x)) + 2 * k * dot(x, mul(C.K3, C, x))) / (2 * w * dot(x, mul(C.M, C, x)));
  }
  return {cls, solve, nodal, basis, N, cg};
}
"""

FIGURE = r"""
const POSTER_T = D.poster;
const FM = D.fmax, CM = D.cmax, SLOW = D.slow;

/* ---------------------------------------------------------------- layout */
const P = {x: 88, y: 64, w: 452, h: 326};
const PX = f => P.x + f / FM * P.w, PY = c => P.y + P.h - c / CM * P.h;
const WC = [C.navy, C.accent];                           // wave 1, wave 2
const SEC = {cx: [688, 888], cy: 244, G: 18};             // section views: centres, largest drawn displacement
const STR = {s: 2.2, L: 412, x1: 950, yc: [580, 746], d: .6, a: 40 * Math.PI / 180, G: 11, SL: .5};
const CD = STR.d * Math.cos(STR.a), SD = STR.d * Math.sin(STR.a);
/* the packets: each wave runs along its beam as bursts of its own mode under a Hann
   envelope PW mm across, one after another REP mm apart, so that one crosses the drawn
   beam at a time. The envelope's centre X moves at c_g and the phase psi at the centre
   at k c_g - w, so the crests move at c_p; both waves on one clock, SLOW times slower
   than the beam's (dispersion.py: a packet at the rod speed crosses the beam in 2 s). */
const PW = D.pw, REP = STR.L + PW, XL = -STR.L - PW / 2;
const wrapX = x => x - REP * Math.floor((x - XL) / REP);   // a packet's centre, brought onto [XL, XL + REP)
// a state's rates: the envelope's speed (mm/s on the page) and its centre phase's (rad/s);
// k in rad/m, f in kHz, c_g in km/s
const rates = (k, f, cg) => ({v: cg * 1e6 / SLOW, r: (k * cg - 2 * Math.PI * f) * 1e3 / SLOW});
const SW_ = {x0: 624, x1: 986, y0: 17, y1: 43};          // the section switcher's cells
const PLAY = {x: 862, y: 430, r: 10};                     // the play control, its label to the right
const CBAR = {x: 650, y: 426, w: 190, h: 8};              // the colour scale
const STY = {
  vertical:  {color: C.navy, width: 2.6, dash: null},
  lateral:   {color: C.navy, width: 2.2, dash: [9, 5]},
  axial:     {color: C.blue, width: 2.2, dash: null},
  torsional: {color: C.blue, width: 2.2, dash: [10, 4, 2, 4]},
};
const HIGH = {color: C.sky, width: 1.4, dash: null};
const styleOf = br => br.type ? STY[br.type] : HIGH;

/* ---------------------------------------------------------------- sections
   Each section is a blob (dispersion.py's blob()): a JSON header, then its
   mesh, its RCM ranks and its curves. The bar's is in the page; the others
   are fetched (as base64 in JSON) when first wanted. A curve travels as the few
   eigenfrequencies a cubic Hermite in k needs (slopes: the group velocity) and
   is laid out again here (lay: as dispersion.py's), in points close enough for
   straight lines between them to stay within 1e-5 of it. */
function b64buf(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u.buffer; }
function parseBlob(buf) {
  const L = new DataView(buf).getUint32(0, true), meta = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 4, L)));
  const base = (4 + L + 3) & ~3, arr = {}, T = {f4: Float32Array, u2: Uint16Array, i2: Int16Array};
  for (const [nm, [t, off, len]] of Object.entries(meta.arrays)) arr[nm] = new T[t](buf, base + off, len);
  return {meta, arr};
}
const LOADED = {}, PENDING = {};
function lay(f, cp, cg, tol = 1e-5) {                    // k (rad/m), f (kHz), c_p (km/s) along a travelling curve
  const n = f.length, k = i => 2 * Math.PI * f[i] / cp[i], w = i => 2 * Math.PI * f[i], K = [k(0)], W = [w(0)];
  const herm = (i, x) => {
    const ka = k(i), h = k(i + 1) - ka, t = (x - ka) / h, t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * w(i) + (t3 - 2 * t2 + t) * h * cg[i] + (3 * t2 - 2 * t3) * w(i + 1) + (t3 - t2) * h * cg[i + 1];
  };
  const rec = (i, k0, w0, k1, w1, d) => {
    const km = (k0 + k1) / 2, wm = herm(i, km);
    if (d < 14 && (Math.abs(wm - (w0 + w1) / 2) > tol * wm || Math.abs(wm / km - (w0 / k0 + w1 / k1) / 2) > tol * wm / km)) {
      rec(i, k0, w0, km, wm, d + 1); rec(i, km, wm, k1, w1, d + 1);
    } else { K.push(k1); W.push(w1); }
  };
  for (let i = 0; i + 1 < n; i++) rec(i, k(i), w(i), k(i + 1), w(i + 1), 0);
  return {k: Float64Array.from(K), f: Float64Array.from(W, x => x / (2 * Math.PI)), cp: Float64Array.from(W, (x, i) => x / K[i])};
}
function prepare(buf) {
  const {meta, arr} = parseBlob(buf), sec = {...meta, key: meta.key, meta};
  sec.nodes = arr.nodes; sec.N = arr.nodes.length / 2;
  sec.model = safeModel({E: meta.E, nu: meta.nu, rho: meta.rho, nodes: arr.nodes, elems: Int32Array.from(arr.elems),
                         kind: meta.kind, rank: arr.rank ? Int32Array.from(arr.rank) : null, nth: meta.nth, classes: meta.classes});
  sec.elems = Int32Array.from(arr.elems); sec.NE = sec.elems.length / 9;
  sec.GY = Float32Array.from({length: sec.N}, (_, n) => arr.nodes[2 * n]);
  sec.GZ = Float32Array.from({length: sec.N}, (_, n) => arr.nodes[2 * n + 1]);
  sec.ymin = Math.min(...sec.GY);
  sec.BR = meta.brs.map((r, id) => {
    const C_ = arr.curves, {k, f, cp} = lay(C_.subarray(r.o, r.o + r.n), C_.subarray(r.o + r.n, r.o + 2 * r.n), C_.subarray(r.o + 2 * r.n, r.o + 3 * r.n));
    const xy = Array.from(f, (_, i) => [PX(Math.min(f[i], 1.04 * FM)), PY(Math.min(cp[i], 1.04 * CM))]);
    const inw = i => f[i] <= FM && cp[i] <= CM;
    let i0 = 0, i1 = f.length - 1;
    while (!inw(i0)) i0++;
    while (!inw(i1)) i1--;
    return {...r, id, f, cp, k, xy, i0, i1};
  });
  sec.HG = fc => Math.min(4, Math.floor(5 * (fc - meta.fc1) / (FM - meta.fc1 || 1)));
  sec.TOUR = meta.tour.map(s => ({...s, k1: kAtF(sec.BR[s.b1], s.f1), ka: kAtF(sec.BR[s.b2], s.fa), k2: kAtF(sec.BR[s.b2], s.f2)}));
  sec.faces = meta.faces;
  // each face's neighbours in its loop, for creases and silhouettes along the beam
  for (const F of sec.faces) {
    const same = sec.faces.filter(G => G.loop === F.loop);
    F.prev = same.find(G => G.nodes[G.nodes.length - 1] === F.nodes[0]);
    F.next = same.find(G => G.nodes[0] === F.nodes[F.nodes.length - 1]);
    F.front = F.n[0] - SD * F.n[1] < 0;
    F.depth = F.nodes.reduce((a, n) => a + sec.GY[n] - SD * sec.GZ[n], 0) / F.nodes.length;
    F.outer = F.loop === 0;
  }
  sec.draw = sec.faces.filter(F => F.front).sort((a, b) => b.depth - a.depth);
  const ang = (A, B) => Math.acos(clamp(A.n[0] * B.n[0] + A.n[1] * B.n[1], -1, 1)) * 180 / Math.PI;
  for (const F of sec.draw) {
    F.edge0 = !F.prev || !F.prev.front || ang(F, F.prev) > 30;
    F.edge1 = !F.next || !F.next.front || ang(F, F.next) > 30;
  }
  LOADED[sec.key] = sec;
  return sec;
}
function load(key) {
  if (LOADED[key]) return Promise.resolve(LOADED[key]);
  if (!PENDING[key]) PENDING[key] = Promise.resolve().then(() => prepare(b64buf(D.blobs[key])))
    .catch(e => { delete PENDING[key]; throw e; });
  return PENDING[key];
}
const prefetch = () => { for (const s of D.secs) if (!LOADED[s.key]) load(s.key).catch(() => {}); };

/* ---------------------------------------------------------------- curves */
function seek(a, v, lo, hi) {                            // the last i in [lo, hi) with a[i] <= v, a increasing
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (a[m] <= v) lo = m; else hi = m; }
  return lo;
}
function atK(br, k) {                                    // (f, c_p) on the drawn curve at k
  const i = seek(br.k, k, 0, br.k.length - 1), s = clamp((k - br.k[i]) / (br.k[i + 1] - br.k[i]));
  return {f: lerp(br.f[i], br.f[i + 1], s), cp: lerp(br.cp[i], br.cp[i + 1], s)};
}
function kAtF(br, f) {                                   // the wavenumber of f (kHz) on the branch, in the window
  f = clamp(f, br.f[br.i0], br.f[br.i1]);
  const i = seek(br.f, f, 0, br.f.length - 1), s = clamp((f - br.f[i]) / (br.f[i + 1] - br.f[i]));
  return lerp(br.k[i], br.k[i + 1], s);
}
function cpAtF(br, f) {                                  // c_p on the drawn curve at f, clamped to its window
  f = clamp(f, br.f[br.i0], br.f[br.i1]);
  const i = seek(br.f, f, 0, br.f.length - 1), s = clamp((f - br.f[i]) / (br.f[i + 1] - br.f[i]));
  return lerp(br.cp[i], br.cp[i + 1], s);
}
const kIn = (br, k) => clamp(k, br.k[br.i0], br.k[br.i1]);
function nearOn(br, X, Y) {                              // the nearest point of a curve (inside the window) to (X, Y)
  let best = {d: Infinity, k: br.k[br.i0]};
  for (let i = Math.max(0, br.i0 - 1); i < Math.min(br.xy.length - 1, br.i1 + 1); i++) {
    const [ax, ay] = br.xy[i], [bx, by] = br.xy[i + 1], dx = bx - ax, dy = by - ay;
    const s = clamp(((X - ax) * dx + (Y - ay) * dy) / (dx * dx + dy * dy || 1));
    const d = Math.hypot(ax + s * dx - X, ay + s * dy - Y);
    if (d < best.d) best = {d, k: lerp(br.k[i], br.k[i + 1], s)};
  }
  best.k = kIn(br, best.k);
  return best;
}
function nearest(sec, X, Y) {
  let best = {d: Infinity, id: -1, k: 0};
  for (const br of sec.BR) { const q = nearOn(br, X, Y); if (q.d < best.d) best = {d: q.d, id: br.id, k: q.k}; }
  return best;
}

/* ---------------------------------------------------------------- states
   A wave is a section, a branch and a wavenumber; its solution comes from the
   section's own SAFE model, kept for the next frames, and its group velocity from
   that solution (the model's cg: exact, where the travelling curve's slopes, made
   only to draw the curves, are off by up to a few per cent at a veering). Colour is
   |u| over the section's rms displacement (U^T M U = rho A U_rms^2) at the packet's
   centre, the drawn shapes at a fixed largest size. A state's sign follows the
   wave's last one on the same branch, so a wave never jumps half a wavelength while
   dragged or gliding. */
const CACHE = new Map(), LAST = [null, null], HF = new Map();
/* a state's frequency and group velocity alone (the tour's rates, the tooltip), remembered */
function exact(sec, id, k) {
  const key = sec.key + ':' + id + ':' + k.toFixed(6), c = CACHE.get(key);
  if (c) return c;
  let r = HF.get(key);
  if (!r) {
    const br = sec.BR[id], s = sec.model.solve(br.ci, br.b, k, 2e3 * Math.PI * atK(br, k).f, null);
    r = {k, f: s.w / (2e3 * Math.PI), cg: sec.model.cg(br.ci, k, s.x, s.w) / 1e3};
    HF.set(key, r);
    if (HF.size > 800) HF.delete(HF.keys().next().value);
  }
  return r;
}
const rateOf = (sec, id, k) => { const e = exact(sec, id, k); return rates(k, e.f, e.cg); };
function solved(sec, st, w) {
  const br = sec.BR[st.id], key = sec.key + ':' + st.id + ':' + st.k.toFixed(6);
  let r = CACHE.get(key);
  const p = LAST[w], near = p && p.sec === sec.key && p.id === st.id && Math.abs(p.k - st.k) < .08 * st.k;
  if (!r) {
    const s = sec.model.solve(br.ci, br.b, st.k, 2e3 * Math.PI * atK(br, st.k).f, near ? p.x : null);
    const x = s.x;
    if (!near) {                                         // a fixed sign: the largest entry positive
      let m = 0;
      for (let i = 1; i < x.length; i++) if (Math.abs(x[i]) > Math.abs(x[m])) m = i;
      if (x[m] < 0) for (let i = 0; i < x.length; i++) x[i] = -x[i];
    }
    const RMS = 1 / Math.sqrt(sec.rho * sec.meta.A * 1e-6);
    const U = sec.model.nodal(br.ci, x), N = sec.N, AX = new Float32Array(N), TR = new Float32Array(N), Un = new Float32Array(3 * N);
    let um = 0;
    for (let n = 0; n < N; n++) {
      const ux = U[3 * n] / RMS, uy = U[3 * n + 1] / RMS, uz = U[3 * n + 2] / RMS;
      AX[n] = ux * ux; TR[n] = uy * uy + uz * uz; um = Math.max(um, Math.hypot(U[3 * n], U[3 * n + 1], U[3 * n + 2]));
    }
    for (let g = 0; g < 3 * N; g++) Un[g] = U[g] / um;
    r = {sec: sec.key, id: st.id, k: st.k, x, U: Un, AX, TR, f: s.w / (2e3 * Math.PI), cp: s.w / st.k / 1e3,
         cg: sec.model.cg(br.ci, st.k, x, s.w) / 1e3, lam: 2e3 * Math.PI / st.k, ok: s.ok};
    CACHE.set(key, r);
    if (CACHE.size > 240) CACHE.delete(CACHE.keys().next().value);
  }
  if (near && p !== r) {
    let d = 0;
    for (let i = 0; i < r.x.length; i++) d += r.x[i] * p.x[i];
    if (d < 0) { r = {...r, x: r.x.map(v => -v), U: r.U.map(v => -v)}; CACHE.set(key, r); }
  }
  LAST[w] = r;
  return r;
}

/* ---------------------------------------------------------------- the tour
   First the caption's comparison, bending low and high in frequency (T1 s).
   Then every TS s a stop: wave 1 on a mode's curve, wave 2 gliding up (TG0 to
   TG0 + TGD), a hold, and a rest in which the waves die away and the markers
   move on. Each wave runs as its packets: the envelope's centre is its group
   velocity integrated on the page's clock, the phase at the centre k c_g - w
   integrated, both from the exact group velocities, so the packet speeds up and
   slows down with c_g as wave 2 glides. At a stop both waves launch a packet from
   the left end; the first stop has both mid-beam, a crest at each centre, at the
   poster's moment. The tour runs on its own clock, t - TOUR.off: the reader's
   first touch stops it, "resume tour" starts it again at its next stop, a new
   section at its first. */
const T1 = 16, TS = 18, TG0 = 2, TGD = 8;
const PH0 = Math.PI / 4;                                  // each later stop starts both centres an eighth of a cycle in
const XP = -STR.L / 2;                                    // where the first stop's packets are at the poster's moment
const TOUR = {off: 0};
/* wave 2's glide in stop i, as the rates it passes through: exact at NG + 1 moments evenly
   spread over the glide's TGD s (solved while the stop's first TG0 s run, or all at once if
   a moment of the glide is wanted first), and their integrals over time, each interval by
   the cubic through its four nearest moments, integrated exactly. Remembered per section. */
const NG = 128;
function glideOf(sec, i) {
  const all = sec.GL || (sec.GL = []);
  if (!all[i]) {
    const s = sec.TOUR[i], br = sec.BR[s.b2], k = new Float64Array(NG + 1);
    for (let j = 0; j <= NG; j++) k[j] = j === 0 ? s.ka : j === NG ? s.k2 : kAtF(br, s.fa + (s.f2 - s.fa) * easeInOut(j / NG));
    all[i] = {s, k, v: new Float64Array(NG + 1), r: new Float64Array(NG + 1), n: 0, IV: null, IR: null};
  }
  return all[i];
}
// the antiderivatives, from 0, of the four Lagrange cubics on the moments 0, 1, 2, 3 (part() takes differences)
const CUB = [u => -(u ** 4 / 4 - 2 * u ** 3 + 5.5 * u * u - 6 * u) / 6, u => (u ** 4 / 4 - 5 * u ** 3 / 3 + 3 * u * u) / 2,
             u => -(u ** 4 / 4 - 4 * u ** 3 / 3 + 1.5 * u * u) / 2, u => (u ** 4 / 4 - u ** 3 + u * u) / 6];
function part(y, j, s) {                                 // the integral of y over [j, j + s] (s <= 1), in moments
  const j0 = clamp(j - 1, 0, NG - 3);
  let a = 0;
  for (let q = 0; q < 4; q++) a += y[j0 + q] * (CUB[q](j - j0 + s) - CUB[q](j - j0));
  return a;
}
function glideFill(sec, G, upto) {
  for (; G.n <= Math.min(upto, NG); G.n++) { const q = rateOf(sec, G.s.b2, G.k[G.n]); G.v[G.n] = q.v; G.r[G.n] = q.r; }
  if (G.n > NG && !G.IV) {
    const h = TGD / NG, I = y => { const o = new Float64Array(NG + 1); for (let j = 0; j < NG; j++) o[j + 1] = o[j] + h * part(y, j, 1); return o; };
    G.IV = I(G.v); G.IR = I(G.r);
  }
  return G;
}
function glideAt(G, ta) {                                // wave 2's travel since the stop began (mm, rad) and its rates at ta
  const a = {v: G.v[0], r: G.r[0]};
  if (ta <= TG0) return {x: a.v * ta, p: a.r * ta, ...a};
  const u = (ta - TG0) / TGD * NG, h = TGD / NG;
  if (u >= NG) {
    const d = ta - TG0 - TGD;
    return {x: a.v * TG0 + G.IV[NG] + G.v[NG] * d, p: a.r * TG0 + G.IR[NG] + G.r[NG] * d, v: G.v[NG], r: G.r[NG]};
  }
  const j = Math.floor(u), s = u - j;
  return {x: a.v * TG0 + G.IV[j] + h * part(G.v, j, s), p: a.r * TG0 + G.IR[j] + h * part(G.r, j, s),
          v: lerp(G.v[j], G.v[j + 1], s), r: lerp(G.r[j], G.r[j + 1], s)};
}
function tourAt(sec, tau) {
  const T = sec.TOUR, o = TOUR.off;
  if (tau < T1) {
    const s = T[0], out = 1 - seg(o + T1 - 1, 1), d = tau - POSTER_T, R = [rateOf(sec, s.b1, s.k1), rateOf(sec, s.b2, s.k2)];
    return {st: [{id: s.b1, k: s.k1}, {id: s.b2, k: s.k2}], X: R.map(q => XP + q.v * d), ps: R.map(q => q.r * d), rt: R,
            amp: settle(o + .45, .8) * out, mk: [settle(o + .6, .28) * out, settle(o + .6, .28) * out], lab: lab(o + .3) * out};
  }
  const u = tau - T1, n = Math.floor(u / TS), ta = u - n * TS, i = (n + 1) % T.length, s = T[i], t0 = o + T1 + n * TS;
  const X = clamp((ta - TG0) / TGD), f2 = s.fa + (s.f2 - s.fa) * easeInOut(X);
  const G = glideFill(sec, glideOf(sec, i), ta >= TG0 ? NG : Math.floor(ta / TG0 * NG) + 1), g2 = glideAt(G, ta);
  const R1 = rateOf(sec, s.b1, s.k1), out = 1 - seg(t0 + TS - 1, 1);
  return {st: [{id: s.b1, k: s.k1}, {id: s.b2, k: X <= 0 ? s.ka : X >= 1 ? s.k2 : kAtF(sec.BR[s.b2], f2)}],
          X: [XL + R1.v * ta, XL + g2.x], ps: [PH0 + R1.r * ta, PH0 + g2.p], rt: [R1, {v: g2.v, r: g2.r}],
          amp: settle(t0 + .25, .8) * out, mk: [settle(t0 + .2, .28) * out, settle(t0 + .3, .28) * out],
          lab: settle(t0 + .2, .4) * out};
}

/* ---------------------------------------------------------------- the reader
   USER is null while the tour plays. The first touch of a curve, a marker, a
   thumb or a key takes over where the tour stands, and the waves run on from
   there: each frame moves every packet on by the time since the last at the rates
   of the state then shown, so a new frequency changes its speed at once while the
   envelope and the phase at its centre stay where they were (the crests close in
   or open out about the centre); "resume tour" hands back after a short fade. */
let CUR = null, USER = null, HAND = null, HOVER = null, GRAB = null, USED = 0, SW = null;
function takeOver() {
  if (USER && !HAND) return;
  const q = HAND ? handState() : tourAt(CUR, t - TOUR.off);
  USER = {st: q.st.map(s => ({...s})), X: q.X.map(wrapX), ps: q.ps.slice(), tl: t, t0: t, a0: q.amp, m0: q.mk.slice()};
  HAND = null;
  if (!USED) USED = Math.max(t, 1e-6);
}
function resumeTour() {                                  // a short fade, then the tour's next stop
  if (!USER || HAND) return;
  const tau = t - TOUR.off, next = tau < T1 ? T1 : T1 + (Math.floor((tau - T1) / TS) + 1) * TS;
  HAND = {t0: t, next};
  if (!playing) setPlay(true);
}
function handState() {
  const q = userState(), e = seg(HAND.t0, .35);
  return {...q, amp: q.amp * (1 - e), mk: q.mk.map(m => m * (1 - e)), lab: 1 - e};
}
function reset() { USER = null; HAND = null; GRAB = null; HOVER = null; LAST[0] = LAST[1] = null; TOUR.off = 0; }
function userState() {
  const dt = Math.max(0, t - USER.tl);
  USER.tl = t;
  const rt = [0, 1].map(w => {
    const S = LAST[w] && LAST[w].sec === CUR.key && LAST[w].id === USER.st[w].id ? LAST[w] : null;
    return S ? rates(S.k, S.f, S.cg) : rateOf(CUR, USER.st[w].id, USER.st[w].k);
  });
  for (let w = 0; w < 2; w++) {
    USER.X[w] = wrapX(USER.X[w] + rt[w].v * dt);
    USER.ps[w] = (USER.ps[w] + rt[w].r * dt) % (2 * Math.PI);
  }
  const e = settle(USER.t0, .6);
  return {st: USER.st, X: USER.X, ps: USER.ps, rt, amp: lerp(USER.a0, 1, e), mk: USER.m0.map(m => lerp(m, 1, e)), lab: 1};
}
function stateNow() {
  if (HAND && t >= HAND.t0 + .35) { TOUR.off = t - HAND.next; USER = null; HAND = null; }
  if (HAND) return handState();
  return USER ? userState() : tourAt(CUR, t - TOUR.off);
}
/* the same kind of wave on another section: a fundamental mode keeps its kind,
   another the curve nearest in c_p; the frequency stays where the curve allows */
function mapState(from, to, st) {
  const br = from.BR[st.id], q = atK(br, st.k);
  let id = br.type && to.fund[br.type] !== undefined ? to.fund[br.type] : -1;
  if (id < 0) {
    let bd = Infinity;
    for (const b of to.BR) if (q.f >= b.f[b.i0] && q.f <= b.f[b.i1]) { const d = Math.abs(cpAtF(b, q.f) - q.cp); if (d < bd) { bd = d; id = b.id; } }
    if (id < 0) id = to.fund.vertical;
  }
  return {id, k: kAtF(to.BR[id], q.f)};
}

/* ---------------------------------------------------------------- switching
   A new section: the four fundamental curves morph into the new ones, the
   higher order curves cross fade, the markers glide to their new points, the
   waves fade out (running on) and the new section's fade in (0.8 s of the wall
   clock, so it runs while the waves are paused too). */
const SWD = .8, now = () => performance.now() / 1000;
let NEXT = null;                                         // a choice made during a switch: taken when it ends
function chooseSection(key) {
  if (SW) { NEXT = key; syncSwitch(); return; }
  NEXT = null;
  if (CUR.key === key) return;
  load(key).then(to => {
    if (SW) { NEXT = key; return; }
    if (CUR.key === key) return;
    const q = stateNow(), from = CUR;
    SW = {from, to, t0: now() - (REDUCED ? SWD : 0), ta: t, q0: {...q, st: q.st.map(s => ({...s})), X: q.X.slice(), ps: q.ps.slice()}, S0: [LAST[0], LAST[1]]};
    if (USER) USER.st = USER.st.map(s => mapState(from, to, s));
    else TOUR.off = t - (playing ? 0 : POSTER_T);
    CUR = to;
    LAST[0] = LAST[1] = null;
    syncSwitch();
    if (!playing) { const tick = () => { render(); if (SW) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }
  }, () => syncSwitch());
}
function setSectionNow(key) {                            // at once, no animation (the checks and a still use it)
  return load(key).then(to => {
    if (CUR.key !== key) { if (USER) USER.st = USER.st.map(s => mapState(CUR, to, s)); CUR = to; LAST[0] = LAST[1] = null; }
    SW = null; syncSwitch(); render();
  });
}
let FROZEN = null;
function freezeSwitch(a, b, p) {                         // a switch held at progress p, for the checks and frames
  if (a === null) { FROZEN = null; SW = null; SWHI = null; return; }
  const from = LOADED[a], to = LOADED[b], q = tourAt(from, t - TOUR.off);
  const S0 = [solved(from, q.st[0], 0), solved(from, q.st[1], 1)];
  const ix = k => D.secs.findIndex(s => s.key === k);
  CUR = to; SW = {from, to, t0: 0, ta: t, q0: q, S0}; FROZEN = p; SWHI = {from: ix(a), to: ix(b), t0: t};
}
/* the old section's waves while they fade out: running on at the rates they had */
function fading(sw) {
  const q = sw.q0, d = t - sw.ta;
  return {...q, X: q.X.map((x, w) => x + q.rt[w].v * d), ps: q.ps.map((p, w) => p + q.rt[w].r * d)};
}
const swP = () => SW ? (FROZEN !== null ? FROZEN : clamp((now() - SW.t0) / SWD)) : 1;

/* ---------------------------------------------------------------- helpers */
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const LEV = 64, SEQC = Array.from({length: LEV}, (_, i) => seq(i / (LEV - 1)));
const CB = 3;                                            // the colour scale: |u| / U_rms from 0 to 3
const lev = m => Math.min(LEV - 1, Math.round(m / CB * (LEV - 1)));
const num = (v, d) => (Math.abs(v - Math.round(v)) < .05 && v >= 1 ? String(Math.round(v)) : v.toFixed(d));
function badge(w, x, y, a = 1, r = 10) {                // a wave's mark: its number on its colour
  if (a <= .01) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(x - 5.5, y - 7, 11, 14); ctx.restore();
  dot(x, y, r * (.7 + .3 * a), {color: '#fff', fill: WC[w], width: 1.6, alpha: a});
  text(String(w + 1), x, y + 5, {size: 14, bold: true, color: '#fff', align: 'center', alpha: a});
}
function textW(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
function tri(x, y, s, color, a = 1, up = true) {
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = color; ctx.beginPath();
  if (up) { ctx.moveTo(x, y); ctx.lineTo(x - s * .72, y + s); ctx.lineTo(x + s * .72, y + s); }
  else { ctx.moveTo(x - s * .45, y - s * .6); ctx.lineTo(x + s * .6, y); ctx.lineTo(x - s * .45, y + s * .6); }
  ctx.closePath(); ctx.fill(); ctx.restore();
}

/* ---------------------------------------------------------------- (a) */
function curvesOf(sec, a, prog, skipFund) {             // a section's curves, higher order first
  if (a <= 0) return;
  for (const br of sec.BR) if (!br.type) line(br.xy, {...HIGH, alpha: a, progress: prog ? prog(br) : 1});
  if (skipFund) return;
  const order = ['vertical', 'lateral', 'axial', 'torsional'];
  for (const br of sec.BR) if (br.type) line(br.xy, {...STY[br.type], alpha: a, progress: prog ? seg(.12 + .05 * order.indexOf(br.type), .40) : 1});
}
function morphFund(A, B, e, a) {                         // the fundamental curves of A becoming B's
  for (const type of ['vertical', 'lateral', 'axial', 'torsional']) {
    if (A.fund[type] === undefined || B.fund[type] === undefined) continue;
    if (type === 'lateral' && (A.fund.lateral === A.fund.vertical) && (B.fund.lateral === B.fund.vertical)) continue;
    const ba = A.BR[A.fund[type]], bb = B.BR[B.fund[type]], pts = [];
    for (let i = 0; i <= 160; i++) {
      const f = FM * i / 160, lo = lerp(ba.f[ba.i0], bb.f[bb.i0], e);
      if (f < lo) continue;
      pts.push([PX(f), PY(Math.min(1.04 * CM, lerp(cpAtF(ba, f), cpAtF(bb, f), e)))]);
    }
    line(pts, {...STY[type], alpha: a});
  }
}
const GUIDE = {color: C.guide, width: 1, dash: [5, 4]};
function legend(sec, a) {                                // two rows, three columns: under every section's curves
  if (a <= 0) return;
  const E = [...sec.legend, ['guide', 'shear, Rayleigh']], cols = [];
  for (let i = 0; i < E.length; i += 2) cols.push(E.slice(i, i + 2));
  const cw = cols.map(c => Math.max(...c.map(([, s]) => textW(s, 14))) + 38), LW = cw.reduce((x, y) => x + y, 0) + 10, LH = 2 * 17 + 9;
  const LX = P.x + P.w - 8 - LW, LY = P.y + P.h - 8 - LH;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 1;
  ctx.fillRect(LX, LY, LW, LH); ctx.strokeRect(LX, LY, LW, LH); ctx.restore();
  let x0 = LX + 8;
  cols.forEach((c, j) => {
    c.forEach(([type, s], r) => {
      const y = LY + 17 + r * 17, st = type === 'guide' ? GUIDE : type ? STY[type] : HIGH;
      line([[x0, y - 5], [x0 + 26, y - 5]], {...st, alpha: a});
      text(s, x0 + 32, y, {size: 14, alpha: a});
    });
    x0 += cw[j];
  });
}
function plotA(S, q, sw) {
  panel('a', 18, 34, {alpha: lab(0)});
  text('dispersion curves', 52, 34 + rise(lab(.03)), {size: 17, color: C.body, alpha: lab(.03)});
  const ax = axes({x: P.x, y: P.y, w: P.w, h: P.h, xlim: [0, FM], ylim: [0, CM],
    xticks: [0, 25, 50, 75, 100, 125, 150, 175, 200], yticks: [0, 1, 2, 3, 4, 5, 6, 7],
    xlabel: '\\rm{frequency}\\ f\\ \\rm{(kHz)}', ylabel: '\\rm{phase velocity}\\ c_{\\rm{p}}\\ \\rm{(km/s)}',
    ylabelGap: 44, progress: seg(0, .35)});
  const p = sw ? swP() : 1, A = sw ? sw.from : CUR, e = easeInOut(clamp((p - .1) / .8));
  const out = sw ? 1 - clamp(p / .4) : 0, inn = sw ? clamp((p - .35) / .45) : 1;
  ax.inside(() => {
    for (const [sec, a] of sw ? [[A, out], [CUR, inn]] : [[CUR, 1]]) {
      if (a <= 0) continue;
      ctx.save(); ctx.globalAlpha = .55 * seg(.3, .3) * a; ctx.fillStyle = C.steel;
      ctx.fillRect(P.x, P.y, PX(sec.fc1) - P.x, P.h); ctx.restore();
    }
    for (const [c, a0] of [[D.ct, .35], [D.cr, .40]])
      line([[P.x, PY(c)], [P.x + P.w, PY(c)]], {color: C.guide, width: 1, dash: [5, 4], progress: seg(a0, .35)});
    if (sw) { curvesOf(A, out, null, true); curvesOf(CUR, inn, null, true); morphFund(A, CUR, e, 1); }
    else curvesOf(CUR, 1, br => seg(.40 + .06 * CUR.HG(br.fc), .38));
    // the waves' curves and the one under the pointer, lifted over the rest
    const em = seg(.9, .3) * (sw ? clamp((p - .85) / .15) : 1), sel = new Set([S[0].id, S[1].id]);
    for (const id of [...sel, HOVER ? HOVER.id : -1]) {
      if (id < 0 || em <= 0 || !CUR.BR[id]) continue;
      const br = CUR.BR[id], st = styleOf(br), hot = HOVER && id === HOVER.id && !sel.has(id);
      line(br.xy, {color: '#fff', width: st.width + 4, alpha: em});
      line(br.xy, {...st, color: hot ? C.ink : st.color === C.sky ? C.blue : st.color, width: st.width + 1, alpha: em});
    }
  });
  // cut-on frequencies on the top frame
  for (const [sec, a] of sw ? [[A, out], [CUR, inn]] : [[CUR, 1]]) for (const fc of sec.cuts) {
    const s = settle(.40 + .06 * sec.HG(fc), .28) * a;
    if (s <= 0 || fc > FM) continue;
    const x = PX(fc), y = P.y + 1;
    ctx.save(); ctx.globalAlpha = s; ctx.fillStyle = C.guide; ctx.beginPath();
    ctx.moveTo(x, y + 7 * s); ctx.lineTo(x - 3.8, y); ctx.lineTo(x + 3.8, y); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  const ca = lab(.40);
  for (const [sec, a] of sw ? [[A, out], [CUR, inn]] : [[CUR, 1]])
    text('cut-on', Math.max(P.x + 2, PX(sec.fc1) - 2), P.y - 8 + rise(ca), {size: 14, color: C.muted, alpha: ca * a});
  const ga = lab(.55);
  // the guide speeds named at the lines' right ends, outside the frame (the legend says which is which)
  math('c_{\\rm{T}}', P.x + P.w + 6, PY(D.ct) - 1 + rise(ga), {size: 15, color: C.body, alpha: ga});
  math('c_{\\rm{R}}', P.x + P.w + 6, PY(D.cr) + 12 + rise(ga), {size: 15, color: C.body, alpha: ga});
  const la = lab(.65);
  if (sw) { legend(A, la * (1 - clamp(p / .35))); legend(CUR, la * clamp((p - .45) / .35)); } else legend(CUR, la);
  // the waves: a thumb under the frequency axis, and the marker on the curve
  const pos = markerPos(S, q, sw, e);
  for (let w = 0; w < 2; w++) {
    const a = pos[w].a;
    if (a <= .01) continue;
    tri(pos[w].x, P.y + P.h + 1.5, 7, WC[w], a);
  }
  // before the first touch, each marker breathes once every 2.4 s: it can be moved
  if (!STILL && !USED && !sw) for (let w = 0; w < 2; w++) {
    const ph = ((t + w * 1.2) % 2.4) / 2.4, a = pos[w].a * .5 * (1 - ph) * seg(1.4, .6);
    if (a > .01) dot(pos[w].x, pos[w].y, 11 + 12 * easeOut(ph), {color: WC[w], fill: null, width: 1.2, alpha: a});
  }
  for (let w = 0; w < 2; w++) badge(w, pos[w].x, pos[w].y, pos[w].a);
  if (!STILL && HOVER && !GRAB && !sw) tooltip();
  // the slot: how to use it until it is used, then the way back to the tour
  if (!STILL) {
    const hint = 1 - (USED ? seg(USED, .4) : 0), back = USER && !HAND ? settle(USER.t0 + .3, .3) : 0;
    if (hint > .01) text('drag 1 or 2 along its curve, or pick a curve', P.x + P.w, 34, {size: 14, color: C.muted, align: 'right', alpha: hint * lab(1.2)});
    if (back > .01) {
      const w_ = textW('resume tour', 14);
      tri(P.x + P.w - w_ - 9, 29.5, 10, C.blue, back, false);
      text('resume tour', P.x + P.w, 34, {size: 14, color: C.blue, align: 'right', alpha: back});
    }
    placeResume(back > .5);
  }
}
function markerPos(S, q, sw, e) {
  const at = (s, a) => ({x: PX(s.f), y: PY(s.cp), a});
  if (!sw) return [0, 1].map(w => at(S[w], q.mk[w]));
  // during a switch: from the old points to the new ones, riding the morphing curves
  return [0, 1].map(w => {
    const A = sw.S0[w], B = S[w], a = Math.max(q.mk[w], sw.q0.mk[w] * (1 - clamp((swP() - .6) / .4)));
    if (!A) return at(B, a * clamp((swP() - .5) / .3));
    const f = lerp(A.f, B.f, e), ba = sw.from.BR[A.id], bb = CUR.BR[B.id];
    if (ba.type && ba.type === bb.type) return {x: PX(f), y: PY(lerp(cpAtF(ba, f), cpAtF(bb, f), e)), a};
    return {x: lerp(PX(A.f), PX(B.f), e), y: lerp(PY(A.cp), PY(B.cp), e), a};
  });
}
const lamTex = mm => mm < 1e3 ? mm.toPrecision(3) + '\\ \\rm{mm}' : (mm / 1e3).toFixed(2) + '\\ \\rm{m}';
function tooltip() {                                     // the curve under the pointer: its name, f, wavelength, c_p and c_g
  const br = CUR.BR[HOVER.id], q = atK(br, HOVER.k), x = PX(q.f), y = PY(q.cp), e = exact(CUR, HOVER.id, HOVER.k);
  dot(x, y, 4.5, {color: C.ink, fill: '#fff', width: 1.2});
  const L = [['t', br.nm], ['m', 'f = ' + q.f.toFixed(1) + '\\ \\rm{kHz},\\ \\ \\lambda\\ = ' + lamTex(2e3 * Math.PI / HOVER.k)],
             ['m', 'c_{\\rm{p}} = ' + q.cp.toFixed(2) + '\\ \\rm{km/s},\\ \\ c_{\\rm{g}} = ' + e.cg.toFixed(2) + '\\ \\rm{km/s}']];
  const w = Math.max(...L.map(([k, s]) => k === 't' ? textW(s, 14) : math(s, 0, -1e4, {size: 14, alpha: 0}))) + 16, h = 60;
  // beside the point, inside the plot, never over the point itself
  let bx = x + 14 + w < P.x + P.w - 4 ? x + 14 : x - 14 - w, by = y - h - 12;
  bx = clamp(bx, P.x + 4, P.x + P.w - 4 - w);
  if (by < P.y + 4) by = y + 12;
  ctx.save(); ctx.fillStyle = '#fff'; ctx.strokeStyle = C.rule; ctx.lineWidth = 1; ctx.fillRect(bx, by, w, h); ctx.strokeRect(bx, by, w, h); ctx.restore();
  L.forEach(([k, s], i) => k === 't' ? text(s, bx + 8, by + 18 + 17 * i, {size: 14, color: C.ink}) :
    math(s, bx + 8, by + 18 + 17 * i, {size: 14, color: C.body}));
}

/* ---------------------------------------------------------------- (b) switcher */
const ICON = {
  bar: [[[-3, -6], [3, -6], [3, 6], [-3, 6]]],
  ibeam: [[[-5, -6], [5, -6], [5, -4], [1, -4], [1, 4], [5, 4], [5, 6], [-5, 6], [-5, 4], [-1, 4], [-1, -4], [-5, -4]]],
  rail: [[[-6, 6], [6, 6], [6, 5], [1, 3.4], [1, -2.5], [3, -3], [3, -6], [-3, -6], [-3, -3], [-1, -2.5], [-1, 3.4], [-6, 5]]],
  pipe: 'ring',
  plate: [[[-6, -1.5], [6, -1.5], [6, 1.5], [-6, 1.5]]],
};
let SWHI = null;
function switcher() {
  const n = D.secs.length, cw = (SW_.x1 - SW_.x0) / n, a = lab(.1), y0 = SW_.y0, h = SW_.y1 - SW_.y0;
  panel('b', 590, 34, {alpha: lab(.05)});
  // the chosen cell's fill glides to a new choice
  const i1 = D.secs.findIndex(s => s.key === CUR.key);
  if (!SWHI || SWHI.to !== i1) SWHI = {from: SWHI ? lerp(SWHI.from, SWHI.to, settle(SWHI.t0, .3)) : i1, to: i1, t0: t};
  const hx = SW_.x0 + cw * lerp(SWHI.from, SWHI.to, SW ? easeInOut(clamp(swP() / .4)) : 1);
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C.steel; ctx.fillRect(hx, y0, cw, h);
  ctx.strokeStyle = C.rule; ctx.lineWidth = 1; ctx.strokeRect(SW_.x0, y0, SW_.x1 - SW_.x0, h);
  for (let i = 1; i < n; i++) { ctx.beginPath(); ctx.moveTo(SW_.x0 + cw * i, y0 + 5); ctx.lineTo(SW_.x0 + cw * i, y0 + h - 5); ctx.stroke(); }
  ctx.restore();
  D.secs.forEach((s, i) => {
    const on = i === i1, cx = SW_.x0 + cw * i, lw = textW(s.label, 15), ix = cx + (cw - lw - 20) / 2 + 6, iy = y0 + h / 2;
    const pend = PENDING[s.key] && !LOADED[s.key];
    ctx.save(); ctx.globalAlpha = a * (pend ? .5 + .3 * Math.sin(now() * 6) : 1); ctx.lineWidth = 1; ctx.strokeStyle = on ? C.ink : C.body;
    ctx.fillStyle = on ? C.navy : C.mist;
    ctx.beginPath();
    if (ICON[s.key] === 'ring') { ctx.arc(ix, iy, 6, 0, 2 * Math.PI); ctx.arc(ix, iy, 4, 0, 2 * Math.PI, true); }
    else for (const poly of ICON[s.key]) poly.forEach(([x, y], j) => j ? ctx.lineTo(ix + x, iy + y) : ctx.moveTo(ix + x, iy + y));
    ctx.closePath(); ctx.fill('evenodd'); ctx.restore();
    text(s.label, ix + 12, y0 + h / 2 + 5, {size: 15, color: on ? C.ink : C.body, alpha: a});
  });
}

/* ---------------------------------------------------------------- (b) sections
   Each wave's cross-section as its packet carries it: the section at the packet's
   centre, u = Re{U exp(i psi)}, which turns at k c_g - w, so it holds still for a
   wave that does not disperse and turns over for one that does. */
function sectionView(sec, w, S, psi, amp, draw_, fillA, la) {
  const cx = SEC.cx[w], cy = SEC.cy, s = sec.sscale, g = SEC.G * amp, c = Math.cos(psi), sn = Math.sin(psi), U = S.U, N = sec.N;
  const xs = new Float32Array(N), ys = new Float32Array(N), mg = new Float32Array(N);
  for (let n = 0; n < N; n++) {                          // U_x = i V_x: the in-plane parts go as cos psi, the axial as sin psi
    xs[n] = cx + sec.GY[n] * s + g * U[3 * n + 1] * c;
    ys[n] = cy - sec.GZ[n] * s - g * U[3 * n + 2] * c;
    mg[n] = Math.sqrt(S.AX[n] * sn * sn + S.TR[n] * c * c);
  }
  const loops = sec.loops.map(L => L.map(n => [xs[n], ys[n]]));
  if (fillA > 0) {
    ctx.save(); ctx.globalAlpha *= fillA; ctx.fillStyle = C.steel; ctx.beginPath();
    for (const L of loops) L.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y));
    ctx.fill('evenodd'); ctx.restore();
    const paths = Array.from({length: LEV}, () => new Path2D()), el = sec.elems;
    const SUB = [[0, 1, 4, 3], [1, 2, 5, 4], [3, 4, 7, 6], [4, 5, 8, 7]];
    for (let e = 0; e < sec.NE; e++) for (const q of SUB) {
      const a = el[9 * e + q[0]], b = el[9 * e + q[1]], cc = el[9 * e + q[2]], d = el[9 * e + q[3]];
      const p = paths[lev((mg[a] + mg[b] + mg[cc] + mg[d]) / 4)];
      // back to the first corner by a line: Path2D's closePath costs ten times a lineTo
      p.moveTo(xs[a], ys[a]); p.lineTo(xs[b], ys[b]); p.lineTo(xs[cc], ys[cc]); p.lineTo(xs[d], ys[d]); p.lineTo(xs[a], ys[a]);
    }
    ctx.save(); ctx.globalAlpha *= fillA * clamp(amp * 1.25); ctx.lineWidth = .6; ctx.lineJoin = 'miter';
    for (let l = 0; l < LEV; l++) { ctx.fillStyle = ctx.strokeStyle = SEQC[l]; ctx.fill(paths[l]); ctx.stroke(paths[l]); }
    ctx.restore();
    ctx.save(); ctx.globalAlpha *= .75 * fillA; ctx.strokeStyle = C.sky; ctx.lineWidth = .6; ctx.beginPath();
    for (let e = 0; e < sec.NE; e++) for (const [a, b, d] of [[0, 1, 2], [2, 5, 8], [8, 7, 6], [6, 3, 0]]) {
      const na = el[9 * e + a], nb = el[9 * e + b], nd = el[9 * e + d];
      ctx.moveTo(xs[na], ys[na]); ctx.lineTo(xs[nb], ys[nb]); ctx.lineTo(xs[nd], ys[nd]);
    }
    ctx.stroke(); ctx.restore();
  }
  for (const L of loops) line(L, {color: C.ink, width: 1.5, progress: draw_, close: true});
  for (const L of sec.loops) line(L.map(n => [cx + sec.GY[n] * s, cy - sec.GZ[n] * s]),
    {color: C.ink, width: 1, dash: [4, 3], alpha: .6 * fillA, close: true});
  // its label: the wave's mark and frequency, over it
  const lw = math('f = ' + num(S.f, 1) + '\\ \\rm{kHz}', 0, -1e4, {size: 16, alpha: 0}), lx = cx - (lw + 26) / 2;
  const ly = Math.max(64, cy - sec.H * s / 2 - SEC.G - 8);  // just over the section, whatever its height
  badge(w, lx + 10, ly - 6, la);
  math('f = ' + num(S.f, 1) + '\\ \\rm{kHz}', lx + 26, ly, {size: 16, alpha: la});
}

/* ---------------------------------------------------------------- (b) along the beam
   An oblique view of 412 mm of the beam ending at x = 0: x to the right, z up,
   y receding at 40 degrees, halved. The section's boundary, cut into faces (runs
   of boundary nodes of one direction), is swept along x; the faces turned to the
   reader are drawn from the farthest to the nearest, and the face at x = 0 last.
   The wave runs along it as packets: every point moves as
   E(x - X) Re{U(y, z) exp(i(k(x - X) + psi))}, E the Hann envelope PW mm across
   about the packet's centre X (which moves at c_g; psi turns at k c_g - w, so the
   crests move at c_p), drawn with its largest displacement STR.G units but never
   steeper than STR.SL, and coloured by |u| / U_rms at that instant (U_rms the
   section's rms displacement at the packet's centre), so every wave, the axial one
   too, is seen to travel. The faces' colours are one small image a wave, made each
   frame: a column a millimetre along the beam, a row a node of each drawn face. It is
   laid on the face in parallelogram pieces cut to the deformed outline: fine where
   the packet is, one piece over the straight, white beam on either side. A bore's
   faces are drawn only near the open end, where they show. */
const NXS = STR.L + 1, XM = Float32Array.from({length: NXS}, (_, m) => m - STR.L);   // x (mm) of each sample
const PADX = 16, PAD = 2, IMG = [0, 1].map(() => ({cv: document.createElement('canvas'), im: null, px: null}));
const SEQ32 = (() => {                                    // the colour scale as RGBA words, for writing a pixel at once
  const u = new Uint32Array(256), b = new Uint8Array(u.buffer);
  for (let i = 0; i < 256; i++) { b[4 * i] = SEQ[3 * i]; b[4 * i + 1] = SEQ[3 * i + 1]; b[4 * i + 2] = SEQ[3 * i + 2]; b[4 * i + 3] = 255; }
  return u;
})();
const MIX = new Uint32Array(256), MIXB = new Uint8Array(MIX.buffer), STEEL = [0xE3, 0xEB, 0xF2];
/* wave w's |u|: columns the samples along x, rows each drawn face's nodes. While the wave fades
   (its colour at ca over steel at fillA over the page), the colours come mixed so, and the pieces
   are laid opaque: pieces overlap a little, and laid at an alpha each overlap would show */
function faceImage(w, sec, S, cs, sn, ca, fillA) {
  const A = IMG[w], W_ = NXS + 2 * PADX, H_ = sec.draw.reduce((a, F) => a + F.nodes.length + 2 * PAD, 0);
  if (A.cv.width !== W_ || A.cv.height !== H_ || !A.im) {
    A.cv.width = W_; A.cv.height = H_;
    A.im = A.cv.getContext('2d').createImageData(W_, H_); A.px = new Uint32Array(A.im.data.buffer);
    A.a = new Float32Array(W_); A.b = new Float32Array(W_);
  }
  let LUT = SEQ32;
  if (ca < 1 || fillA < 1) {
    for (let i = 0; i < 256; i++) for (let c = 0; c < 3; c++)
      MIXB[4 * i + c] = Math.round(ca * SEQ[3 * i + c] + (1 - ca) * (fillA * STEEL[c] + (1 - fillA) * 255));
    for (let i = 0; i < 256; i++) MIXB[4 * i + 3] = 255;
    LUT = MIX;
  }
  const px = A.px, a = A.a, b = A.b, sc = 255 / CB;
  let i0 = W_, i1 = 0;                                   // the columns the packet covers
  for (let i = 0; i < W_; i++) {
    const m = clamp(i - PADX, 0, NXS - 1);
    a[i] = sn[m] * sn[m]; b[i] = cs[m] * cs[m];
    if (a[i] + b[i] > 0) { if (i < i0) i0 = i; i1 = i + 1; }
  }
  let y0 = 0;
  A.r0 = sec.draw.map(F => {
    const rows = F.nodes.length;
    for (let j = 0; j < rows + 2 * PAD; j++) {
      const n = F.nodes[clamp(j - PAD, 0, rows - 1)], ax = S.AX[n], tr = S.TR[n], o = (y0 + j) * W_;
      px.fill(LUT[0], o, o + W_);
      for (let i = i0; i < i1; i++) px[o + i] = LUT[Math.min(255, Math.round(Math.sqrt(ax * a[i] + tr * b[i]) * sc))];
    }
    y0 += rows + 2 * PAD;
    return y0 - rows - PAD;
  });
  A.cv.getContext('2d').putImageData(A.im, 0, 0);
  return A;
}
// the samples [m, m + mw] of a face's block laid on P0 + u U + v V, reaching ea before and eb
// after along U, ev past along V
function piece(img, m, mw, r0, rows, P0, U, V, ea, eb, ev) {
  const LU = Math.hypot(U[0], U[1]) || 1, LV = Math.hypot(V[0], V[1]) || 1, c0 = PADX + .5 + m;
  const da = Math.min(ea / LU, (PADX - 1) / mw), db = Math.min(eb / LU, (PADX - 1) / mw), dv = Math.min(ev / LV, PAD / rows);
  ctx.save(); ctx.transform(U[0], U[1], V[0], V[1], P0[0], P0[1]);
  ctx.drawImage(img, c0 - da * mw, r0 - dv * rows, mw * (1 + da + db), rows * (1 + 2 * dv), -da, -dv, 1 + da + db, 1 + 2 * dv);
  ctx.restore();
}
function stripView(sec, w, S, Xc, psi, amp, draw_, fillA, la) {
  const s = STR.s, yc = STR.yc[w], U = S.U, k = S.k / 1e3, NX = NXS, N = sec.N, y0 = sec.ymin;
  const g = Math.min(STR.G, STR.SL * s * S.lam / (2 * Math.PI)) * amp / s;   // mm per unit of U
  // the packet on the beam: E cos and E sin of the phase at each sample, zero off it
  const X0 = wrapX(Xc), cs = new Float32Array(NX), sn = new Float32Array(NX);
  let p0 = NX, p1 = -1;
  for (let m = 0; m < NX; m++) {
    const xi = XM[m] - X0;
    if (Math.abs(xi) >= PW / 2) continue;
    const e = Math.cos(Math.PI * xi / PW) ** 2, th = k * xi + psi;
    cs[m] = e * Math.cos(th); sn[m] = e * Math.sin(th);
    if (m < p0) p0 = m;
    p1 = m;
  }
  const rows = new Map();                                // a node's deformed, projected positions along x
  const row = n => {
    let r = rows.get(n);
    if (r) return r;
    const X = new Float32Array(NX), Y = new Float32Array(NX), e = sec.GY[n] - y0;
    const ux = g * U[3 * n], uy = g * U[3 * n + 1], uz = g * U[3 * n + 2];
    for (let m = 0; m < NX; m++) {
      const d = e + uy * cs[m];
      X[m] = STR.x1 + s * (XM[m] - ux * sn[m] + d * CD);
      Y[m] = yc - s * (sec.GZ[n] + uz * cs[m] + d * SD);
    }
    rows.set(n, r = {X, Y});
    return r;
  };
  const c0 = cs[NX - 1], s0 = sn[NX - 1];
  const end = n => { const d = sec.GY[n] - y0 + g * U[3 * n + 1] * c0;
    return [STR.x1 + s * (-g * U[3 * n] * s0 + d * CD), yc - s * (sec.GZ[n] + g * U[3 * n + 2] * c0 + d * SD)]; };
  const E_ = Array.from({length: N}, (_, n) => end(n));
  const mag = (n, m) => Math.sqrt(S.AX[n] * sn[m] * sn[m] + S.TR[n] * cs[m] * cs[m]);
  // pieces along x: straight lines between their ends stay within 0.6 units of the deformed edge,
  // which bends with the carrier and the envelope together (wavenumbers 2 pi / lambda and 2 pi / PW)
  const bend = Math.max(1e-9, g * s), kE = 2 * Math.PI / S.lam + 2 * Math.PI / PW;
  const step = 2 * Math.round(clamp(Math.sqrt(8 * .6 / bend) / kE / 2, 1, 12)), ca = fillA * clamp(amp * 1.25);
  const breaks = m0 => {                                 // fine over the packet, one piece either side of it
    const out = [m0];
    for (let m = m0; m < NX - 1; ) {
      const n = p1 < 0 || m > p1 ? NX - 1 : m < p0 - 1 ? p0 - 1 : Math.min(m + step, NX - 1);
      out.push(n); m = n;
    }
    return out;
  };
  const pts = r => Array.from({length: NX}, (_, m) => [r.X[m], r.Y[m]]);
  const o = {color: C.ink, width: 1.4, progress: draw_};
  // an edge along the beam: through line() while it draws itself or the check records it,
  // else straight from the arrays (the same stroke, without a point array a frame)
  const edge = r => {
    if (CHECK || draw_ < 1) return line(pts(r), o);
    ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1.4; ctx.beginPath(); ctx.moveTo(r.X[0], r.Y[0]);
    for (let m = 1; m < NX; m++) ctx.lineTo(r.X[m], r.Y[m]);
    ctx.stroke(); ctx.restore();
  };
  const lo = F => F.outer ? 0 : NX - 1 - 24;              // a bore shows only through its open end
  const IM = fillA > 0 && ca > 0 ? faceImage(w, sec, S, cs, sn, ca, fillA) : null;
  sec.draw.forEach((F, fi) => {
    const A = row(F.nodes[0]), B = row(F.nodes[F.nodes.length - 1]), ms = breaks(lo(F));
    if (fillA > 0) {
      const path = new Path2D();
      ms.forEach((m, i) => i ? path.lineTo(A.X[m], A.Y[m]) : path.moveTo(A.X[m], A.Y[m]));
      for (let i = ms.length - 1; i >= 0; i--) path.lineTo(B.X[ms[i]], B.Y[ms[i]]);
      path.closePath();
      // no clip (a clip a face costs more than all its pieces): the pieces follow the
      // deformed edges within 0.6 units and barely cross them. A piece is the parallelogram
      // of its quad's mean sides; its corners are off the quad's by the quad's twist d (along
      // the edges, where fibres stretch unequally), so pieces overlap along x by 2|d| more,
      // closing the wedges that would open between neighbours at the edges
      ctx.save();
      if (!IM) { ctx.save(); ctx.globalAlpha *= fillA; ctx.fillStyle = C.steel; ctx.fill(path); ctx.restore(); }
      if (IM) {                                          // opaque: the fade is in the image's colours
        const r0 = IM.r0[fi];
        for (let i = 0; i + 1 < ms.length; i++) {
          const m = ms[i], n = ms[i + 1], first = i === 0, last = n === NX - 1;
          const tl = [A.X[m], A.Y[m]], tr = [A.X[n], A.Y[n]], bl = [B.X[m], B.Y[m]], br = [B.X[n], B.Y[n]];
          const Uv = [(tr[0] - tl[0] + br[0] - bl[0]) / 2, (tr[1] - tl[1] + br[1] - bl[1]) / 2];
          const Vv = [(bl[0] - tl[0] + br[0] - tr[0]) / 2, (bl[1] - tl[1] + br[1] - tr[1]) / 2];
          const Q0 = [(tl[0] + tr[0] + bl[0] + br[0]) / 4 - (Uv[0] + Vv[0]) / 2, (tl[1] + tr[1] + bl[1] + br[1]) / 4 - (Uv[1] + Vv[1]) / 2];
          const ex = .8 + Math.hypot(tl[0] + br[0] - tr[0] - bl[0], tl[1] + br[1] - tr[1] - bl[1]) / 2;
          piece(IM.cv, m, n - m, r0, F.nodes.length, Q0, Uv, Vv, first ? .8 : ex, last ? .8 : ex, .35);
        }
      }
      ctx.restore();
      // its mesh: lines along the beam at every fourth node (4 mm on a 1 mm mesh), sections every 10 mm
      if (F.outer) {
        ctx.save(); ctx.globalAlpha *= .45 * fillA; ctx.strokeStyle = C.sky; ctx.lineWidth = .6; ctx.beginPath();
        for (let j = 4; j < F.nodes.length - 1; j += 4) { const r = row(F.nodes[j]); ctx.moveTo(r.X[0], r.Y[0]); for (let m = 2; m < NX; m += 2) ctx.lineTo(r.X[m], r.Y[m]); }
        const R_ = F.nodes.map(row);
        for (let m = NX - 1; m > 0; m -= 10) { ctx.moveTo(R_[0].X[m], R_[0].Y[m]); for (let j = 1; j < R_.length; j++) ctx.lineTo(R_[j].X[m], R_[j].Y[m]); }
        ctx.stroke(); ctx.restore();
      }
    }
    if (F.outer && F.edge0) edge(A);                    // a bore's faces show only through the open end
    if (F.outer && F.edge1) edge(B);
    if (F.outer) line(F.nodes.map(n => { const r = row(n); return [r.X[0], r.Y[0]]; }), o);
  });
  // the face at x = 0: the section there, coloured as above
  if (fillA > 0) {
    ctx.save(); ctx.beginPath();
    for (const L of sec.loops) L.forEach((n, i) => i ? ctx.lineTo(...E_[n]) : ctx.moveTo(...E_[n]));
    ctx.globalAlpha *= fillA; ctx.fillStyle = C.steel; ctx.fill('evenodd'); ctx.restore();
    if (ca > 0) {
      const paths = Array.from({length: LEV}, () => new Path2D()), el = sec.elems, SUB = [[0, 1, 4, 3], [1, 2, 5, 4], [3, 4, 7, 6], [4, 5, 8, 7]];
      const mg = Float32Array.from({length: N}, (_, n) => mag(n, NX - 1));
      for (let e = 0; e < sec.NE; e++) for (const q of SUB) {
        const a = el[9 * e + q[0]], b = el[9 * e + q[1]], cc = el[9 * e + q[2]], d = el[9 * e + q[3]];
        const p = paths[lev((mg[a] + mg[b] + mg[cc] + mg[d]) / 4)], A = E_[a], B = E_[b], Cc = E_[cc], Dd = E_[d];
        p.moveTo(A[0], A[1]); p.lineTo(B[0], B[1]); p.lineTo(Cc[0], Cc[1]); p.lineTo(Dd[0], Dd[1]); p.lineTo(A[0], A[1]);
      }
      ctx.save(); ctx.globalAlpha *= ca; ctx.lineWidth = .5; ctx.lineJoin = 'miter';
      for (let l = 0; l < LEV; l++) { ctx.fillStyle = ctx.strokeStyle = SEQC[l]; ctx.fill(paths[l]); ctx.stroke(paths[l]); }
      ctx.restore();
    }
  }
  for (const L of sec.loops) line(L.map(n => E_[n]), {...o, close: true});
  // the header: the wave's mark and mode, its two speeds and its wavelength
  const hy = yc - 96;
  badge(w, 26, hy - 5, la);
  text(sec.BR[S.id].nm, 44, hy, {size: 16, color: C.ink, alpha: la});
  math('c_{\\rm{p}} = ' + S.cp.toFixed(2) + '\\ \\rm{km/s},\\ \\ \\ c_{\\rm{g}} = ' + S.cg.toFixed(2) + '\\ \\rm{km/s},\\ \\ \\ \\lambda\\ = ' +
       lamTex(S.lam), 982, hy, {size: 16, align: 'right', alpha: la});
}

/* ---------------------------------------------------------------- the play control */
function playControl() {
  if (STILL) return;
  const a = lab(.6), x = PLAY.x, y = PLAY.y;
  dot(x, y, PLAY.r, {color: playing ? C.ink : C.navy, fill: playing ? '#fff' : C.navy, width: 1.2, alpha: a});
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = playing ? C.ink : '#fff';
  if (playing) { ctx.fillRect(x - 3.6, y - 4.5, 2.6, 9); ctx.fillRect(x + 1, y - 4.5, 2.6, 9); }
  else { ctx.beginPath(); ctx.moveTo(x - 2.6, y - 4.8); ctx.lineTo(x + 4.6, y); ctx.lineTo(x - 2.6, y + 4.8); ctx.closePath(); ctx.fill(); }
  ctx.restore();
  if (!playing) text('paused', x + 16, CBAR.y + 8, {size: 15, color: C.ink, alpha: a});
}

/* ---------------------------------------------------------------- draw */
function draw() {
  const q = stateNow(), sw = SW, p = swP();
  if (sw && p >= 1 && FROZEN === null) { SW = null; syncSwitch(); if (NEXT) setTimeout(() => chooseSection(NEXT)); }
  const S = [solved(CUR, q.st[0], 0), solved(CUR, q.st[1], 1)];
  plotA(S, q, sw && p < 1 ? sw : null);
  switcher();
  // the waves: the old section's fading out, then the new one's coming in
  let sec = CUR, SS = S, env = 1, V = q;
  if (sw && p < 1) {
    if (p < .4) { sec = sw.from; V = fading(sw); SS = sw.S0[0] && sw.S0[1] ? sw.S0 : [solved(sw.from, V.st[0], 0), solved(sw.from, V.st[1], 1)]; env = 1 - easeInOut(p / .4); }
    else env = easeInOut((p - .4) / .6);
  }
  const dr = seg(.10, .40), fl = seg(.35, .30);
  for (let w = 0; w < 2; w++) sectionView(sec, w, SS[w], V.ps[w], V.amp * env, dr, fl, V.lab * lab(.3) * env);
  // the colour scale and the play control
  const ca = lab(.6), BY = CBAR.y + rise(ca);
  if (ca > 0) {
    ctx.save(); ctx.globalAlpha = ca;
    for (let i = 0; i < 100; i++) { ctx.fillStyle = seq((i + .5) / 100); ctx.fillRect(CBAR.x + CBAR.w * i / 100, BY, CBAR.w / 100 + .6, CBAR.h); }
    ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.strokeRect(CBAR.x, BY, CBAR.w, CBAR.h); ctx.restore();
    for (let v = 0; v <= CB; v++) {
      line([[CBAR.x + CBAR.w * v / CB, BY + CBAR.h], [CBAR.x + CBAR.w * v / CB, BY + CBAR.h + 4]], {width: 1, alpha: ca});
      math(String(v), CBAR.x + CBAR.w * v / CB, BY + CBAR.h + 20, {size: 14, align: 'center', alpha: ca});
    }
    math('|u|\\,/\\,U_{\\rm{rms}}', CBAR.x - 10, BY + 8, {size: 15, align: 'right', alpha: ca});
  }
  playControl();
  const dr2 = seg(.15, .45), fl2 = seg(.40, .30);
  for (let w = 0; w < 2; w++) stripView(sec, w, SS[w], V.X[w], V.ps[w], V.amp * env, dr2, fl2, V.lab * lab(.35) * env);
  const pa = lab(.7);
  if (sw && p < 1) { text(sw.from.params, 18, H - 16, {size: 14, color: C.muted, alpha: pa * (1 - clamp(p / .4))}); text(CUR.params, 18, H - 16, {size: 14, color: C.muted, alpha: pa * clamp((p - .4) / .4)}); }
  else text(CUR.params, 18, H - 16, {size: 14, color: C.muted, alpha: pa});
  place(S);
}

CUR = prepare(b64buf(D.blob));

/* ---------------------------------------------------------------- input */
const FIG = document.querySelector('.fig'), OV = [], RG = [];
let RESUME = null, PLAYB = null;
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
const inPlot = (X, Y) => X > P.x - 6 && X < P.x + P.w + 6 && Y > P.y - 6 && Y < P.y + P.h + 16;
function redraw() { if (!playing) render(); }
function setWave(w, st) { takeOver(); USER.st[w] = st; redraw(); }
function markerAt(X, Y, touch) {
  let best = -1, bd = touch ? 30 : 18;
  for (let w = 0; w < 2; w++) {
    const S = LAST[w]; if (!S || S.sec !== CUR.key) continue;
    const d = Math.min(Math.hypot(PX(S.f) - X, PY(S.cp) - Y), Y > P.y + P.h ? Math.abs(PX(S.f) - X) + Math.abs(P.y + P.h + 5 - Y) * .5 : Infinity);
    if (d < bd) { bd = d; best = w; }
  }
  return best;
}
const px = v => (v * cv.clientWidth / W).toFixed(1) + 'px';
function box(el, x0, y0, x1, y1) { el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0); }
function place(S) {                                      // the overlays follow the drawing
  if (!OV.length) return;
  for (let w = 0; w < 2; w++) {
    const el = OV[w], br = CUR.BR[S[w].id];
    el.style.left = px(PX(S[w].f)); el.style.top = px(PY(S[w].cp));
    const txt = br.nm + ', ' + S[w].f.toFixed(1) + ' kHz, phase velocity ' + S[w].cp.toFixed(2) + ' km/s, group velocity ' +
      S[w].cg.toFixed(2) + ' km/s, wavelength ' + (S[w].lam < 1e3 ? S[w].lam.toPrecision(3) + ' mm' : (S[w].lam / 1e3).toFixed(2) + ' m');
    if (el.getAttribute('aria-valuetext') !== txt) {
      el.setAttribute('aria-valuetext', txt); el.setAttribute('aria-valuenow', S[w].f.toFixed(1));
      el.setAttribute('aria-valuemin', br.f[br.i0].toFixed(1)); el.setAttribute('aria-valuemax', br.f[br.i1].toFixed(1));
    }
  }
  const n = D.secs.length, cw = (SW_.x1 - SW_.x0) / n;
  RG.forEach((b, i) => box(b, SW_.x0 + cw * i, SW_.y0, SW_.x0 + cw * (i + 1), SW_.y1));
  box(PLAYB, PLAY.x - PLAY.r - 4, PLAY.y - PLAY.r - 4, PLAY.x + 96, PLAY.y + PLAY.r + 4);
}
function placeResume(on) {
  if (!RESUME) return;
  RESUME.hidden = !on;
  if (on) { const w_ = textW('resume tour', 14); box(RESUME, P.x + P.w - w_ - 18, 18, P.x + P.w + 4, 40); }
}
function syncPlay() {
  if (!PLAYB) return;
  PLAYB.setAttribute('aria-label', (playing ? 'Pause' : 'Play') + ' the waves (Space)');
  PLAYB.setAttribute('aria-pressed', String(!playing));
}
function syncSwitch() {
  const k = NEXT || (SW ? SW.to.key : CUR.key);
  RG.forEach((b, i) => { const on = D.secs[i].key === k; b.setAttribute('aria-checked', String(on)); b.tabIndex = on ? 0 : -1; });
}
function neighbour(S, dir) {                             // the curve just above (dir 1) or below at this frequency
  let best = null;
  for (const br of CUR.BR) {
    if (br.id === S.id || S.f < br.f[br.i0] || S.f > br.f[br.i1]) continue;
    const k = kAtF(br, S.f), cp = atK(br, k).cp, d = (cp - S.cp) * dir;
    if (d > 1e-6 && (!best || d < best.d)) best = {d, id: br.id, k};
  }
  return best;
}
function key(w, e) {
  const S = LAST[w]; if (!S || S.sec !== CUR.key) return;
  const br = CUR.BR[S.id], big = e.shiftKey || e.key === 'PageUp' || e.key === 'PageDown' ? 10 : 1;
  let st = null;
  if (e.key === 'ArrowRight' || e.key === 'PageUp') st = {id: S.id, k: kAtF(br, S.f + big)};
  else if (e.key === 'ArrowLeft' || e.key === 'PageDown') st = {id: S.id, k: kAtF(br, S.f - big)};
  else if (e.key === 'Home') st = {id: S.id, k: br.k[br.i0]};
  else if (e.key === 'End') st = {id: S.id, k: br.k[br.i1]};
  else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') { const n = neighbour(S, e.key === 'ArrowUp' ? 1 : -1); if (n) st = {id: n.id, k: n.k}; else { e.preventDefault(); return; } }
  else return;
  e.preventDefault();
  setWave(w, st);
}
if (!STILL) {
  const css = document.createElement('style');
  css.textContent = '.nfw{position:absolute;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;pointer-events:none;outline:none}' +
    '.nfb{position:absolute;margin:0;padding:0;border:0;background:transparent;cursor:pointer;outline:none;font:inherit;color:transparent}' +
    '.nfw:focus-visible,.nfb:focus-visible{outline:2px solid #095A94;outline-offset:2px}.nfb[hidden]{display:none}';
  document.head.appendChild(css);
  const ctl = FIG.querySelector('.ctl'), add = el => { FIG.insertBefore(el, ctl); return el; };
  // the section switcher: a radio group, arrows move and choose
  const rg = add(document.createElement('div'));
  rg.setAttribute('role', 'radiogroup'); rg.setAttribute('aria-label', 'Cross section');
  D.secs.forEach((s, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'nfb'; b.setAttribute('role', 'radio'); b.textContent = s.label;
    b.setAttribute('aria-label', s.label);
    b.addEventListener('click', e => { e.stopPropagation(); chooseSection(s.key); });
    b.addEventListener('keydown', e => {
      const d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key], n = D.secs.length;
      const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : d ? (i + d + n) % n : -1;
      if (j < 0) return;
      e.preventDefault(); RG[j].focus(); chooseSection(D.secs[j].key);
    });
    b.addEventListener('focus', prefetch); b.addEventListener('pointerenter', prefetch);
    rg.appendChild(b); RG.push(b);
  });
  syncSwitch();
  // the two waves: keyboard sliders sitting on the markers
  for (let w = 0; w < 2; w++) {
    const el = add(document.createElement('div'));
    el.className = 'nfw'; el.tabIndex = 0; el.setAttribute('role', 'slider');
    el.setAttribute('aria-label', 'Wave ' + (w + 1) + ' on the dispersion curves: left and right arrows change its frequency, up and down move it to the next curve');
    el.addEventListener('keydown', e => key(w, e));
    OV.push(el);
  }
  // play and pause the waves; Space does it anywhere but on a button
  PLAYB = add(document.createElement('button'));
  PLAYB.type = 'button'; PLAYB.className = 'nfb';
  PLAYB.addEventListener('click', e => { e.stopPropagation(); setPlay(!playing); });
  RESUME = add(document.createElement('button'));
  RESUME.type = 'button'; RESUME.className = 'nfb'; RESUME.hidden = true; RESUME.textContent = 'resume tour';
  RESUME.setAttribute('aria-label', 'Resume the tour of the modes');
  RESUME.addEventListener('click', e => { e.stopPropagation(); resumeTour(); RESUME.blur(); redraw(); });
  const setPlay0 = setPlay;
  setPlay = p => { setPlay0(p); syncPlay(); if (!p) render(); };
  syncPlay();
  // Space plays and pauses anywhere, a section's cell too (its choice is made by the arrows);
  // only on the other buttons it presses them
  document.addEventListener('keydown', e => {
    if (e.key !== ' ' || e.ctrlKey || e.metaKey || e.altKey) return;
    const btn = e.target.closest && e.target.closest('button');
    if (btn && btn.getAttribute('role') !== 'radio') return;
    e.preventDefault(); setPlay(!playing);
  });
  cv.style.touchAction = 'pan-y';
  let swallow = false;
  cv.addEventListener('pointerdown', e => {
    const [X, Y] = toUnits(e), touch = e.pointerType !== 'mouse';
    if (!inPlot(X, Y) || SW) return;
    swallow = true;
    let w = markerAt(X, Y, touch), st = null;
    if (w < 0) {
      const n = nearest(CUR, X, Y);
      if (n.d > (touch ? 24 : 12)) return;
      const d = [0, 1].map(v => LAST[v] && LAST[v].sec === CUR.key ? Math.hypot(PX(LAST[v].f) - X, PY(LAST[v].cp) - Y) : Infinity);
      w = d[0] <= d[1] ? 0 : 1; st = {id: n.id, k: n.k};
    }
    GRAB = {w, axis: Y > P.y + P.h};
    HOVER = null;
    cv.setPointerCapture(e.pointerId); e.preventDefault();
    if (st) setWave(w, st); else { takeOver(); redraw(); }
    cv.style.cursor = 'grabbing';
  });
  cv.addEventListener('pointermove', e => {
    const [X, Y] = toUnits(e);
    if (GRAB) {
      const br = CUR.BR[USER.st[GRAB.w].id];
      // along its own curve; a pointer drawn well away onto another curve takes the wave there
      let st = {id: br.id, k: GRAB.axis ? kAtF(br, (X - P.x) / P.w * FM) : nearOn(br, X, Y).k};
      if (!GRAB.axis) { const own = nearOn(br, X, Y), n = nearest(CUR, X, Y); if (own.d > 28 && n.d < 8 && n.id !== br.id) st = {id: n.id, k: n.k}; }
      setWave(GRAB.w, st);
      return;
    }
    if (e.pointerType !== 'mouse') return;
    let h = null, cur = '';
    if (inPlot(X, Y) && !SW) {
      if (markerAt(X, Y, false) >= 0) cur = 'grab';
      else { const n = nearest(CUR, X, Y); if (n.d <= 12) { h = {id: n.id, k: n.k}; cur = 'pointer'; } else cur = 'default'; }
    }
    cv.style.cursor = cur;
    if ((h && (!HOVER || h.id !== HOVER.id || Math.abs(h.k - HOVER.k) > 1e-9)) || (!h && HOVER)) { HOVER = h; redraw(); }
  });
  const drop = () => { if (GRAB) { GRAB = null; cv.style.cursor = ''; redraw(); } };
  cv.addEventListener('pointerup', drop);
  cv.addEventListener('pointercancel', drop);
  cv.addEventListener('pointerleave', () => { if (HOVER && !GRAB) { HOVER = null; cv.style.cursor = ''; redraw(); } });
  // a press in the plot chooses a wave: it must not also pause (the engine
  // toggles on a click of the canvas), so the click stops on the way down
  FIG.addEventListener('click', e => { if (swallow && e.target === cv) e.stopPropagation(); swallow = false; }, true);
}
"""

JS = "const D = DATA;\n" + SOLVER + FIGURE + "\nboot();\n"


def check_text(Rs, SV, sizes, ov, ovl, TG, MS):
    L = ["Figure 4 (nf-dispersion): SAFE dispersion curves of guided waves in four steel sections",
         "and an infinite plate, every wave solved in the page by the same SAFE model", ""]
    L += check_bar(Rs["bar"])
    L += check_sections(Rs)
    p = L.append
    ref, gen = sm.Safe(*MESH), make_section("bar")
    pairs = ((gen.K1, ref.K1), (gen.K2, ref.K2), (gen.K3, ref.K3), (gen.M, ref.M))
    dm = (max(abs(A - B).max() / abs(B).max() for A, B in pairs)
          if all(A.shape == B.shape for A, B in pairs) else None)
    p("THE PAGE SOLVES EVERY WAVE IT SHOWS")
    p("  Each section travels as its mesh (nodes in float32, the Python model reading the same rounded")
    p("  values) and its symmetry. The page builds the same isoparametric Q9 elements (3 x 3 Gauss),")
    p("  assembles each class on its own basis (mirror orbits, or the pipe's harmonics) as a skyline in")
    p("  an RCM order, and solves a wave (class, branch, k) exactly: the shift s sits 1e-4 of w under")
    p("  the drawn curve's w at k; a skyline LDL^T of K(k) - s M counts its negative pivots (Sylvester:")
    p("  the eigenvalues below s), s moves until exactly `branch` lie below, and inverse iteration")
    p("  converges on the branch's own eigenpair at that k. Should it head for a nearer eigenvalue")
    p("  below s, the count brackets the branch's alone, bisection narrows the bracket, and the")
    p("  iteration runs again from its middle.")
    if dm is None:
        p("  The bar's general assembly and safe_model use different mesh densities; matrix dimensions are not directly comparable.")
    else:
        p(f"  The bar's general assembly gives safe_model's matrices: max relative difference {dm:.1e}.")
    if "skipped" in SV:
        p(f"  (the node check skipped: {SV['skipped']})")
    else:
        p("  The page's script itself, under node, against scipy on the same mesh, at three random")
        p("  wavenumbers on every branch inside the window:")
        for key in ORDER:
            v = SV[key]
            p(f"    {SECTIONS[key]['label']:7s} {v['n']:3d} states: max |w_page/w_scipy - 1| = {v['ew']:.1e}, "
              f"max (1 - MAC) = {v['em']:.1e}, Sturm count wrong or rejected: {v['bad']},")
            p(f"            shift moved at most {v['tries']} time(s), {v['ms']:.2f} ms a solve (node, this machine);"
              f" classes (size, skyline): " + ", ".join(f"{a} {b}" for a, b in v["dims"]))
    p("  So every state the reader picks, and every frame of the tour, is an exact SAFE eigenpair of")
    p("  its section: the marker sits at its own (f, c_p), the section and the beam draw its own")
    p("  eigenvector.")
    p("  The curves travel thinned. Of the sweep's eigenfrequencies (points at most 2 drawing units")
    p("  apart) only those go that a cubic Hermite in k needs (its slopes the group velocity, from a")
    p(f"  spline through the branch) to give every dropped one back within {THIN:.0e}; the page lays each")
    p("  segment out again, halving it until straight lines between its points stay within")
    p(f"  {THIN:.0e} of the Hermite in f and in c_p. The page's curve at every point of the sweep:")
    for key in ORDER:
        st = thinned(key, Rs[key])[2]
        p(f"    {SECTIONS[key]['label']:7s} {st['kept']} of {st['n']} points travel ({st['kept'] / st['n']:.0%}),"
          f" laid out as {st['laid']}: max |f_page/f - 1| = {st['err']:.1e}")
    p("  (the shift sits 1e-4 under the page's curve, so it stays below the branch's eigenvalue).")
    p("")
    L += check_group(Rs, SV, TG, MS)
    cross = lambda cg: BEAM / (cg * 1e6 / SLOW)
    p("THE TOURS (wave 1, then wave 2 gliding; each state's f, c_p, c_g and wavelength, and the seconds its")
    p("packet takes to cross the drawn beam)")
    for key in ORDER:
        brs, flat = curves_of(key, Rs[key])
        p(f"  {SECTIONS[key]['label']}:")
        for s, row in zip(tour_of(key, brs, flat), TG[key]):
            at = lambda st: f"{st[0]:.3g} kHz (c_p {st[1]:.2f}, c_g {st[2]:.2f} km/s, {2e3 * np.pi / st[3]:.1f} mm; {cross(st[2]):.1f} s)"
            p(f"    1: {brs[s['b1']]['nm']}, {at(row['w1'])}")
            p(f"    2: {brs[s['b2']]['nm']}, {at(row['wa'])}")
            p(f"       to {at(row['w2'])}")
    p("  The first stop of each section shows wave 2 at its high frequency from the start: the")
    p("  caption's comparison, the whole section moving at low frequency, the surfaces at high.")
    p("")
    allcg = [row[l][2] for key in ORDER for row in TG[key] for l in ("w1", "wa", "w2")]
    fast = fastest(Rs)
    p("TIME AND DRAWING")
    p("  The waves run as packets (b): each beam carries bursts of its own mode under a Hann envelope")
    p(f"  E(x) = cos^2(pi x / {PACKET:.0f} mm) ({PACKET:.0f} mm across, {SIG:.1f} mm rms), one after another {BEAM + PACKET:.0f} mm apart,")
    p(f"  so one crosses the drawn {BEAM:.0f} mm at a time, launched from the left end:")
    p("  u = E(x - X) Re{U exp(i(k(x - X) + psi))}. X, the envelope's centre, moves at c_g; psi, the phase")
    p("  at the centre, turns at k c_g - w, so a crest (k (x - X) + psi a whole turn) moves at")
    p("  X' - psi'/k = w/k = c_p. Both waves are on one clock, not written on the figure:")
    p(f"  {SLOW:.4g} times slower than the beam's, so that a packet at the rod speed c_0 crosses the {BEAM:.0f} mm")
    p(f"  in {CROSS:g} s (1 s of the page is {1e6 / SLOW:.1f} us of the beam). The fastest c_g in any window is")
    p(f"  {fast[0]:.3f} km/s (the {SECTIONS[fast[1]]['label']}'s {fast[2]} at {fast[3]:.0f} kHz: {cross(fast[0]):.2f} s); at the tours' states")
    p(f"  the packets cross in {cross(max(allcg)):.1f} to {cross(min(allcg)):.1f} s.")
    p(f"  A wave cycles on the page at f / {SLOW:.4g}: {150e3 / SLOW:.1f} Hz at 150 kHz, {20e3 / SLOW:.1f} Hz at 20 kHz.")
    p("  In the tour X and psi are the exact c_g and k c_g - w integrated in time (the glides by the rule")
    p("  above), a pure function of the clock; under the reader's hand each frame moves them on by its")
    p("  time at the rates of the state then shown, so a new frequency changes the speed at once and the")
    p("  crests close in or open out about the centre, neither the envelope nor the phase at it jumping.")
    p("  Each section view shows its wave's cross-section at the packet's centre, u = Re{U exp(i psi)}:")
    p("  still for a wave that does not disperse (c_g = c_p), turning over for one that does.")
    p("  Tour: 16 s on the caption's comparison, then 18 s a stop: markers arrive, wave 2 glides up its")
    p("  curve over 8 s, a hold, 1 s of rest between modes; each stop launches both packets anew.")
    p("  Colour: |u| / U_rms at each point at that instant, E sqrt(U_x^2 sin^2 + (U_y^2 + U_z^2) cos^2) of")
    p("  the phase, U_rms the section's rms displacement at the packet's centre (U^T M U = rho A U_rms^2);")
    p("  0 to 3, so the beam is white where no packet is. Shape: the largest displacement drawn 18 units")
    p("  in the sections (each section at its own scale, the bar 7.5 units per mm) and at most 11 units")
    p("  along the beam, never steeper than 0.5 (2.2 units per mm, 412 mm ending at x = 0). Along the beam")
    p("  the boundary is cut into faces (runs of one direction); those turned to the reader are drawn far")
    p("  to near, each an image of |u| made each frame (a column a millimetre) laid on its deformed outline")
    p("  in pieces, fine over the packet and one piece over the still beam either side of it; the face at")
    p("  x = 0 last; creases and silhouettes are inked.")
    p("")
    p("INTERACTION")
    p("  The section switcher over (b) (a radio group: arrows move and choose) morphs the fundamental")
    p("  curves into the new section's in 0.8 s of wall time (so also while the waves are paused), cross")
    p("  fades the higher order curves, glides the markers and fades the waves over. A wave keeps its")
    p("  kind (bending, axial, torsional) and frequency where the new section has that mode there, and")
    p("  otherwise takes the curve nearest in c_p. The tour starts again on the new section.")
    p("  The play control by the colour scale, and Space, pause and resume the waves: the phases stop")
    p("  with the clock and run on from there; dragging while paused redraws the frozen frame.")
    p("  The first touch of a curve, marker, thumb or key stops the tour; \"resume tour\" hands back")
    p("  after a 0.35 s fade, at the tour's next stop. Hover shows a curve's name and its f, wavelength,")
    p("  c_p and c_g (solved there) under the pointer. Each wave's label over its beam gives c_p, c_g and")
    p("  the wavelength; its slider reads them out. Hits: 18 units (marker), 12 (curve) with a mouse; 30 and 24 by")
    p("  touch. A drag follows its own curve, and moves to another only when the pointer is drawn")
    p("  well away (28 units) onto it (8 units).")
    p("")
    p("PAYLOAD")
    p(f"  nf-dispersion.html {sizes['page'] / 1024:.0f} KB (the engine, this script and the bar, inline); fetched")
    p("  when a section is first chosen or its switch is pointed at: " +
      ", ".join(f"nf-dispersion-{k}.json {sizes[k] / 1024:.0f} KB" for k in ORDER[1:]) +
      f"; {sum(sizes.values()) / 1024:.0f} KB in all.")
    p("")
    p("OVERLAP (engine ?overlap, 672 px)")
    nt = len(tour_times())
    faults = {k: v for k, v in ov.items() if v}
    p(f"  printed (still): the bar's poster and every 0.25 s to {POSTER:g} s (common.still), then every section at")
    p(f"  {nt} moments across its tour, and every switch held at 30, 60 and 85 %: " +
      ("no collisions" if not faults else f"collisions in {sorted(faults)}"))
    faults2 = {k: v for k, v in ovl.items() if v}
    p("  live (the controls drawn, waves paused): every section at 5 moments: " +
      ("no collisions" if not faults2 else f"collisions in {sorted(faults2)}"))
    p(f"  and each section's parameter line ends left of x = {PARAM_MAX} units, clear of the page controls")
    p("  at every width from 300 px (they cover the last 51 px of the bottom right from 480 px down, 68 above)")
    p("")
    p(f"compute: the bar {Rs['bar']['time']:.0f} s, " + ", ".join(f"{SECTIONS[k]['label']} {Rs[k]['time']:.0f} s" for k in ORDER[1:]))
    return "\n".join(L) + "\n"


def main():
    Rs = {"bar": compute()}
    for key in ORDER[1:]:
        Rs[key] = compute_section(key)
    blobs = {key: section_blob(key, Rs[key]) for key in ORDER}
    b64 = {key: base64.b64encode(blobs[key]).decode("ascii") for key in ORDER}
    for key, s in b64.items():                   # the site's check for his private details reads text files
        if re.search(r"gmail|300\W{0,3}4065", s, re.I):
            raise RuntimeError(f"the {key} blob's base64 happens to spell a private pattern")
    for key in ORDER[1:]:                        # JSON: a type Wix's static host serves
        with open(os.path.join(common.ANIM, f"nf-{NAME}-{key}.json"), "w", encoding="ascii", newline="\n") as fh:
            json.dump({"blob": b64[key]}, fh)
        old = os.path.join(common.ANIM, f"nf-{NAME}-{key}.bin")
        if os.path.exists(old):
            os.remove(old)
    data = {"fmax": F_MAX / 1e3, "cmax": CP_MAX / 1e3, "ct": sm.C_T / 1e3, "cr": sm.C_R / 1e3, "slow": SLOW,
            "pw": PACKET, "poster": POSTER, "secs": [{"key": k, "label": SECTIONS[k]["label"]} for k in ORDER],
            "blob": b64["bar"], "blobs": b64}
    title = "Figure 4: Schematic dispersion curves for guided waves in a beam"
    aria = ("Phase velocity against frequency for a steel beam computed with a SAFE model: bending, axial and "
            "torsional modes start at zero frequency, higher order modes cut on above a threshold and approach the "
            "shear and Rayleigh speeds. Two waves marked 1 and 2 are shown as their cross sections and along the "
            "beam: at low frequency the whole section moves, at high frequency the motion gathers at the surfaces. "
            "Along the beam each wave runs as packets whose envelope moves at its group velocity while the crests "
            "inside move at its phase velocity, both speeds given over the beam. "
            "The cross section can be switched between a bar, an I-beam, a rail, a pipe and an infinite plate; the markers can be "
            "dragged along the curves or moved with the arrow keys, and Space pauses the waves.")
    assert f"L: {BEAM:g}," in FIGURE and f"const NG = {TOUR_T['NG']};" in FIGURE and \
        "const T1 = {T1}, TS = {TS}, TG0 = {TG0}, TGD = {TGD};".format(**TOUR_T) in FIGURE, "the page's constants moved"
    path = common.build_html(NAME, title, aria, 1000, 848, data, JS)
    sizes = {"page": os.path.getsize(path),
             **{k: os.path.getsize(os.path.join(common.ANIM, f"nf-{NAME}-{k}.json")) for k in ORDER[1:]}}
    print("sizes (bytes):", sizes)
    if "--page" in sys.argv:
        return
    SV = check_solver_all(Rs)
    print("page solver:", SV)
    TG = tour_group(Rs)
    look = common.still(NAME)          # the bar's poster, and the overlap check to it (raises on a collision)
    ov = overlaps_all(tour_times())
    ovl = overlaps_all([.9, POSTER, 20, 29, 40], live=True)
    MS = measure_screen()
    print("on screen:", MS)
    text_ = check_text(Rs, SV, sizes, ov, ovl, TG, MS)
    with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text_)
    print(text_)
    print("still:", look)
    bad = {k: v for k, v in {**ov, **{"live " + a: b for a, b in ovl.items()}}.items() if v}
    if bad:
        raise RuntimeError("collisions: " + json.dumps(bad)[:3000])


if __name__ == "__main__":
    main()
