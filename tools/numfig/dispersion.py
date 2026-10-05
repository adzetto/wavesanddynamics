"""Figure 4: dispersion curves of guided waves, from SAFE models of five steel
waveguides, with two waves shown as their cross-sections and as wave packets
along the waveguide. Interactive: every state is a SAFE solution.

(a) phase velocity c_p = w/k against frequency: every branch inside the
    section's window, the fundamental modes (bending, axial, torsional) from zero
    frequency, the higher order modes from their cut-on frequencies (k -> 0,
    marked on the top frame), the shear and Rayleigh speeds as guides. Two
    markers, 1 and 2, each a wave: a branch and a point on it.
(b) the two waves. Above, each one's cross-section (its SAFE eigenvector on the
    mesh) as its packet carries it; below, each one along the waveguide in an
    oblique view, as packets: bursts of the mode under a Hann envelope E,
    u = E(x - X) Re{U(y, z) exp(i(k(x - X) + psi))}. The envelope's centre X moves
    at the group velocity c_g (V^T (K2 + 2k K3) V / (2 w V^T M V) of the solved
    state), the phase psi at the centre at k c_g - w, so the crests move at the
    phase velocity c_p. Each section has one clock, the same for every operating
    point and both waves (its slow-motion factor written under the waveguides),
    and one length scale, so a slow packet lags a fast one as it does in the steel.

The sections, each plotted over a frequency window in which it holds as many
branches as its reference (c_p up to 10 km/s; the window's end in a gap between
the frequencies where branches enter):
  bar    square steel bar 20 x 20 mm, 0 to 190 kHz (f h to 3,800 kHz mm): the
         square rod of Hayashi, Kawashima and Rose (2004, Fig. 2, SAFE), 11 branches;
  I-beam IPE 80 (EN 10365), 0 to 52 kHz: no published curves found, the same
         model on a mesh refined twice is the reference, 20 branches;
  rail   60E1 (UIC60, EN 13674-1, the outline of its standard drawing), 0 to
         22.5 kHz: Ramatlo, Wilke and Loveday (2018, Fig. 1, SAFE, UIC60), 16;
  pipe   NPS 1 1/4 schedule 40 (ASME B36.10M: 42.16 x 3.56 mm), 0 to 175 kHz:
         the exact solution of Gazis (1959), 22;
  plate  10 mm, infinite width, 0 to 250 kHz (f d to 2.5 MHz mm): the exact
         Rayleigh-Lamb and shear horizontal solutions, 5 (A0, S0, SH0, A1, SH1).
Each is meshed with 9-node quadratic elements (the bar, pipe and plate on
structured grids, the I-beam and rail by a constrained Delaunay triangulation
of their outline, each triangle split into three quadrilaterals: the `triangle`
package, pip install triangle, needed only to mesh those two); its symmetry
splits it into classes (the square's C4v, the mirror planes, or the pipe's
circumferential harmonics). The sweep here draws the curves; the page carries
each mesh and solves every wave it shows with the same elements: a skyline
LDL^T of K(k) - s M whose Sturm count pins the branch, then inverse iteration.
The tour's glides take their packets' rates from exact group velocities
computed here (glide_rates), so that a stop starts without solving 129 states.

With no reader input it tours the modes (wave 1 low in frequency, wave 2 gliding
up the same or another curve, its packet quickening and slowing with its c_g).
The first touch pauses the tour ("resume tour" brings it back). A click or tap on
a curve moves the nearer marker there; a marker, or its thumb under the frequency
axis, drags along its curve; the markers are keyboard sliders. The waves pause
and play from a control by the colour scale, or with Space. ?section=<key> (bar,
ibeam, rail, pipe, plate) opens the page on that section.

Run: python tools/numfig/dispersion.py [--page | --text]   (writes content/anim/
nf-dispersion.html and .webp, and dispersion.check.txt with its two extracts,
dispersion_branches.check.txt and dispersion_plate.check.txt; --page writes the
page only; --text writes the reports again from the page's checks, kept from the
last full run while the page is unchanged). Figure 4a (dispersion_wavelength.py)
is built from this page. The sweeps are cached in the temp folder.
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

import common
import safe_model as sm

NAME = "dispersion"
CP_MAX = 10.0e3                   # m/s: the top of the plot, every section
REF_W, REF_H = 520, 418           # the refinement metric (drawing units), finer than the plot
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"vertical": "vertical bending", "lateral": "lateral bending", "axial": "axial",
         "torsional": "torsional"}


# ================================================================ the general SAFE
# Any Q9 mesh of a cross-section: isoparametric elements, 3 x 3 Gauss (exact
# for rectangles, where it gives safe_model's matrices), local node
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


def _dmat(lam=None, mu=None):
    lam, mu = (sm.LAM if lam is None else lam), (sm.MU if mu is None else mu)
    D = np.zeros((6, 6))
    D[:3, :3] = lam
    D[[0, 1, 2], [0, 1, 2]] = lam + 2 * mu
    D[[3, 4, 5], [3, 4, 5]] = mu
    return D


_D6 = _dmat()


def _jac(xy, g):
    J = np.array([[_NXI[g] @ xy[:, 0], _NXI[g] @ xy[:, 1]], [_NET[g] @ xy[:, 0], _NET[g] @ xy[:, 1]]])
    return J, np.linalg.det(J)


def element(xy, D=None):
    """K1, K2 (made real symmetric), K3, M (27 x 27) of one Q9 element, nodes xy (9, 2) in m;
    D the elasticity (default the steel's)."""
    D = _D6 if D is None else D
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
        K1 += B1.T @ D @ B1 * dA
        K2 += (B1.T @ D @ B2 - B2.T @ D @ B1) * dA
        K3 += B2.T @ D @ B2 * dA
        Nm = np.zeros((3, 27))
        for c in range(3):
            Nm[c, c::3] = _N[g]
        M += sm.RHO * Nm.T @ Nm * dA
    return K1, K2 * _SGN, K3, M


_RY, _RZ = np.diag([1.0, -1.0, 1.0]), np.diag([1.0, 1.0, -1.0])
_RD = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, 1.0, 0]])      # the diagonal y <-> z


class Section:
    """A SAFE model of a meshed cross-section: nodes (N, 2) in mm, rounded to
    float32 first, as the page receives them; elems (E, 9)."""

    def __init__(self, nodes_mm, elems, D=None):
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
            for i, a in enumerate(element(xy, D)):
                mats[i].append(a.ravel())
        r, c = np.concatenate(rows), np.concatenate(cols)
        self.K1, self.K2, self.K3, self.M = (sp.csr_matrix((np.concatenate(x), (r, c)), shape=(self.ndof, self.ndof))
                                             for x in mats)
        self.classes, self._cls = {}, {}

    def maps(self):
        """Node maps of the mirrors y -> -y, z -> -z and of the diagonal y <-> z
        (-1 where the image is not a node)."""
        key = {(round(y, 3), round(z, 3)): i for i, (y, z) in enumerate(self.nodes_mm)}
        f = lambda g: np.array([key.get(g(y, z), -1) for y, z in self.nodes_mm])
        return (f(lambda y, z: (round(-y, 3), round(z, 3))), f(lambda y, z: (round(y, 3), round(-z, 3))),
                f(lambda y, z: (round(z, 3), round(y, 3))))

    def mirror_maps(self):
        return self.maps()[:2]

    def group(self, py, pz, pd=0):
        """The symmetry operations of a class as (node map, component matrix,
        character): the mirror y -> -y (character py; 0: not used), z -> -z (pz),
        and with pd the diagonal y <-> z (the square's C4v)."""
        my, mz, md = self.maps()
        nn = len(self.nodes)
        els = [(np.arange(nn), np.eye(3), 1.0)]
        if py:
            assert (my >= 0).all()
            els.append((my, _RY, float(py)))
        if pz:
            assert (mz >= 0).all()
            els.append((mz, _RZ, float(pz)))
        if py and pz:
            els.append((my[mz], _RY @ _RZ, float(py * pz)))
        if pd:
            assert (md >= 0).all()
            els += [(md[m], _RD @ R, chi * pd) for m, R, chi in els]
        return els

    def group_basis(self, els):
        """Q (ndof x m), orthonormal, of the class whose operations and characters
        are els: per orbit (its smallest node the representative) the projections
        P e of the representative's three unit displacements, P the class's
        projector (1/|G|) sum chi(g) g, orthonormalised within the orbit (on a
        mirror line or the diagonal they are dependent or vanish)."""
        nn = len(self.nodes)
        rep = np.min(np.array([m for m, _, _ in els]), axis=0)
        rows, cols, vals, col = [], [], [], 0
        for n in np.flatnonzero(rep == np.arange(nn)):
            acc = []
            for c in range(3):
                v = {}
                for m, R, chi in els:
                    for c2 in range(3):
                        if R[c2, c]:
                            d = 3 * int(m[n]) + c2
                            v[d] = v.get(d, 0.0) + chi * R[c2, c]
                for u in acc:
                    dot = sum(v.get(d, 0.0) * x for d, x in u.items())
                    if dot:
                        for d, x in u.items():
                            v[d] = v.get(d, 0.0) - dot * x
                nrm = np.sqrt(sum(x * x for x in v.values()))
                if nrm > 1e-9:
                    acc.append({d: x / nrm for d, x in v.items() if abs(x) > 1e-12 * nrm})
            for u in acc:
                for d, x in u.items():
                    rows.append(d); cols.append(col); vals.append(x)
                col += 1
        return sp.csr_matrix((vals, (rows, cols)), shape=(self.ndof, col))

    def mirror_basis(self, py, pz, pd=0):
        return self.group_basis(self.group(py, pz, pd))

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
        if self.classes[name].shape[1] > 400:
            return sparse_modes(self, name, k, n)[0]
        Q, k1, k2, k3, m = self.cls(name)
        w2 = sla.eigh(k1 + k * k2 + k * k * k3, m, eigvals_only=True,
                      subset_by_index=[0, min(n, len(m)) - 1], driver="gvx")
        return np.sqrt(np.clip(w2, 0, None))

    def solve(self, name, k, n):
        if self.classes[name].shape[1] > 400:
            return sparse_modes(self, name, k, n)
        Q, k1, k2, k3, m = self.cls(name)
        w2, v = sla.eigh(k1 + k * k2 + k * k * k3, m, subset_by_index=[0, n - 1], driver="gvx")
        return np.sqrt(np.clip(w2, 0, None)), Q @ v


def sparse_modes(model, name, k, n):
    """Lowest generalized eigenpairs, without dense matrices on refined meshes."""
    if not hasattr(model, "_sparse_modes"):
        model._sparse_modes = {}
    if name not in model._sparse_modes:
        Q = model.classes[name]
        model._sparse_modes[name] = (Q, *((Q.T @ A @ Q).tocsc() for A in (model.K1, model.K2, model.K3, model.M)))
    Q, k1, k2, k3, m = model._sparse_modes[name]
    K = k1 + k * k2 + k * k * k3
    count = min(n, m.shape[0] - 2)
    vals, vec = spla.eigsh(K, k=count, M=m, sigma=-1., which="LM", tol=1e-10,
                           v0=np.linspace(1., 2., m.shape[0]))
    order = np.argsort(vals)
    return np.sqrt(np.clip(vals[order], 0, None)), Q @ vec[:, order]


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


SQ = 20.0          # mm: the square bar's side (Hayashi, Kawashima and Rose 2004, Fig. 2: a square rod)
NE_BAR = 16        # Q9 elements along each side: 1.25 mm


def bar_mesh(s=1.0):
    n = max(2, int(round(NE_BAR * s)))
    return grid_mesh([-SQ / 2, SQ / 2], [-SQ / 2, SQ / 2], [n], [n], lambda i, j: True)


PLATE_D = 10.0     # mm


def plate_mesh(s=1.0):
    """A 40 mm slice of an infinite 10 mm plate, uniform across y (its basis
    ties all nodes at the same z: the slice's sides are not free edges). Lamb
    waves have u_y = 0; SH waves have only u_y."""
    return grid_mesh([-20.0, 20.0], [-PLATE_D / 2, PLATE_D / 2], [1], [max(2, int(10 * s))], lambda i, j: True)


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


PIPE = dict(ro=42.16 / 2, ri=42.16 / 2 - 3.56)   # NPS 1 1/4 schedule 40 (ASME B36.10M): OD 42.16 mm, wall 3.56 mm
PIPE_NTH, PIPE_NR = 72, 3                         # elements around and through the wall


def pipe_mesh(nth=PIPE_NTH, nr=PIPE_NR, G=PIPE):
    """A uniform polar mesh: nth elements around, nr through the wall; local xi
    along r (outward) and eta along phi (counter-clockwise): positive Jacobian."""
    na = 2 * nth
    rs = np.linspace(G["ri"], G["ro"], 2 * nr + 1)
    ph = np.arange(na) * np.pi / nth
    nodes = np.array([[r * np.cos(p), r * np.sin(p)] for r in rs for p in ph])
    idx = lambda i, j: i * na + (j % na)
    return nodes, np.array([[idx(2 * er + a, 2 * et + bb) for bb in range(3) for a in range(3)]
                            for et in range(nth) for er in range(nr)])


# The 60E1 (UIC60) rail, EN 13674-1: the right half of its outline (mm, the foot's
# underside at z = 0, counter-clockwise from the foot's centre to the top of the
# head), lines and cubic Beziers as the profile's standard drawing has them (the
# WirthRail 60E1 data sheet, its vector outline scaled to the 172 mm height and
# 150 mm foot): R2 and R4 at the foot's tip, its top at 1:14 and 1:2.75 joined by
# R40, R35 and R7 into the web's R120 flanks (16.5 mm at its narrowest, 60.25 to
# 92.25 mm above the foot), R7 and the 1:2.75 underside of the head, R3, the head's
# 1:20 side, R13, R80 and R300 over the top, 72 mm wide 14.3 mm below it.
RAIL60E1 = [
    ("l", [[0.0, 0.0], [72.985, 0.0]]),
    ("c", [[72.985, 0.0], [73.523, 0.0], [74.029, 0.209], [74.41, 0.59]]),
    ("c", [[74.41, 0.59], [74.791, 0.971], [75.0, 1.477], [75.0, 2.016]]),
    ("l", [[75.0, 2.016], [75.0, 7.79]]),
    ("c", [[75.0, 7.79], [75.0, 8.808], [74.618, 9.779], [73.924, 10.525]]),
    ("c", [[73.924, 10.525], [73.23, 11.271], [72.288, 11.721], [71.271, 11.794]]),
    ("l", [[71.271, 11.794], [55.671, 12.909]]),
    ("c", [[55.671, 12.909], [51.977, 13.173], [48.34, 13.948], [44.858, 15.213]]),
    ("l", [[44.858, 15.213], [16.504, 25.524]]),
    ("c", [[16.504, 25.524], [15.513, 25.885], [14.602, 26.476], [13.869, 27.234]]),
    ("c", [[13.869, 27.234], [13.136, 27.992], [12.577, 28.923], [12.251, 29.924]]),
    ("c", [[12.251, 29.924], [11.951, 30.845], [11.686, 31.789], [11.464, 32.733]]),
    ("c", [[11.464, 32.733], [9.34, 41.742], [8.263, 51.0], [8.263, 60.254]]),
    ("l", [[8.263, 60.254], [8.263, 92.248]]),
    ("c", [[8.263, 92.248], [8.263, 101.502], [9.34, 110.762], [11.464, 119.77]]),
    ("c", [[11.464, 119.77], [11.686, 120.715], [11.952, 121.661], [12.251, 122.578]]),
    ("c", [[12.251, 122.578], [12.577, 123.58], [13.136, 124.511], [13.869, 125.268]]),
    ("c", [[13.869, 125.268], [14.602, 126.027], [15.513, 126.618], [16.504, 126.978]]),
    ("l", [[16.504, 126.978], [35.076, 133.732]]),
    ("c", [[35.076, 133.732], [35.687, 133.954], [36.198, 134.357], [36.557, 134.898]]),
    ("c", [[36.557, 134.898], [36.916, 135.439], [37.089, 136.067], [37.057, 136.716]]),
    ("l", [[37.057, 136.716], [36.008, 157.687]]),
    ("c", [[36.008, 157.687], [35.937, 159.108], [35.638, 160.497], [35.117, 161.815]]),
    ("c", [[35.117, 161.815], [34.609, 163.102], [33.902, 164.294], [33.016, 165.36]]),
    ("c", [[33.016, 165.36], [32.13, 166.426], [31.085, 167.338], [29.913, 168.071]]),
    ("c", [[29.913, 168.071], [28.711, 168.823], [27.4, 169.371], [26.016, 169.699]]),
    ("c", [[26.016, 169.699], [20.847, 170.929], [15.535, 171.644], [10.227, 171.825]]),
    ("c", [[10.227, 171.825], [6.834, 171.941], [3.392, 172.0], [0.0, 172.0]]),
]
RAIL_STD = dict(A=7670.0, Iy=3038.3e4, Iz=512.3e4, zc=80.92, m=60.21)   # EN 13674-1's 60E1: mm^2, mm^4, mm, kg/m
RAIL_H = 12.0      # mm: the triangulation's edge (its quadrilaterals about half that)
RAIL_FOOT_H, RAIL_FOOT_Z = 8.0, 24.0   # mm: the edge along the foot's outline, up to this height over its underside
IPE80 = dict(h=80.0, b=46.0, tw=3.8, tf=5.2, r=5.0)                     # EN 10365
IPE80_STD = dict(A=764.0, Iy=80.14e4, Iz=8.49e4, It=0.70e4, Iw=0.12e9)  # its tables: mm^2, mm^4, mm^6
IPE_H = 4.0        # mm


def _polyline(segs, nb=48):
    pts = []
    for k, P in segs:
        P = np.asarray(P, float)
        if k == "l":
            pts += [P[0], P[1]]
        else:
            t = np.linspace(0, 1, nb)[:, None]
            pts += list((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3])
    pts = np.array(pts)
    keep = [0] + [i for i in range(1, len(pts)) if np.hypot(*(pts[i] - pts[i - 1])) > 1e-9]
    return pts[keep]


def _resample(poly, h, corner=20.0, hfun=None):
    """Points along an open polyline about h apart (or hfun(point) apart: evenly
    spread in the integral of 1 / hfun along each stretch), its ends and its
    corners (turns of more than `corner` degrees) kept."""
    d = np.diff(poly, axis=0)
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    turn = np.abs((np.diff(ang) + 180) % 360 - 180)
    keep = [0] + [i + 1 for i in np.flatnonzero(turn > corner)] + [len(poly) - 1]
    out = [poly[0]]
    for a, b in zip(keep, keep[1:]):
        seg = poly[a:b + 1]
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(seg, axis=0).T))])
        if hfun is None:
            ts = np.linspace(0, s[-1], max(1, int(np.ceil(s[-1] / h))) + 1)[1:]
        else:
            ss = np.linspace(0, s[-1], 400)
            P = np.column_stack([np.interp(ss, s, seg[:, 0]), np.interp(ss, s, seg[:, 1])])
            g = np.concatenate([[0], np.cumsum(np.diff(ss) / np.array([hfun(q) for q in (P[1:] + P[:-1]) / 2]))])
            ts = np.interp(np.linspace(0, g[-1], max(1, int(np.ceil(g[-1]))) + 1)[1:], g, ss)
        for t in ts:
            out.append([np.interp(t, s, seg[:, 0]), np.interp(t, s, seg[:, 1])])
    return np.array(out)


def _project(pts, dense):
    """The nearest points of a dense polyline to pts."""
    A, B = dense[:-1], dense[1:]
    AB = B - A
    L2 = (AB ** 2).sum(1) + 1e-30
    out = []
    for p in np.atleast_2d(pts):
        t = np.clip(((p - A) * AB).sum(1) / L2, 0, 1)
        Q = A + t[:, None] * AB
        out.append(Q[np.argmin(((Q - p) ** 2).sum(1))])
    return np.array(out)


def _q9(V, T, on_curve, dense):
    """Triangles (counter-clockwise) split into three quadrilaterals each (corner,
    edge midpoints, centroid), then 9-node elements; boundary nodes for which
    on_curve holds are moved onto the outline `dense`, and each centre node set
    by the blending of its element's edges."""
    nodes, idx = [], {}

    def node(key, xy):
        if key not in idx:
            idx[key] = len(nodes)
            nodes.append(np.asarray(xy, float))
        return idx[key]

    quads = []
    for t in T:
        a, b, c = (int(v) for v in t)
        va, vb, vc = node(("v", a), V[a]), node(("v", b), V[b]), node(("v", c), V[c])
        m = {(p, q): node(("m",) + tuple(sorted((p, q))), (V[p] + V[q]) / 2) for p, q in ((a, b), (b, c), (c, a))}
        g = node(("g", a, b, c), (V[a] + V[b] + V[c]) / 3)
        quads += [(va, m[(a, b)], g, m[(c, a)]), (vb, m[(b, c)], g, m[(a, b)]), (vc, m[(c, a)], g, m[(b, c)])]
    N = np.array(nodes)
    cnt = {}
    for q in quads:
        for i in range(4):
            e = tuple(sorted((q[i], q[(i + 1) % 4])))
            cnt[e] = cnt.get(e, 0) + 1
    bnd = {e for e, c in cnt.items() if c == 1}
    on = [n for n in sorted({n for e in bnd for n in e}) if on_curve(N[n])]
    N[on] = _project(N[on], dense)
    N, mid, els = list(N), {}, []
    for c0, c1, c2, c3 in quads:
        ms = []
        for p, r in ((c0, c1), (c1, c2), (c2, c3), (c3, c0)):
            key = tuple(sorted((p, r)))
            if key not in mid:
                xy = (N[p] + N[r]) / 2
                if key in bnd and on_curve(xy):
                    xy = _project(xy, dense)[0]
                mid[key] = len(N)
                N.append(xy)
            ms.append(mid[key])
        N.append((N[ms[0]] + N[ms[1]] + N[ms[2]] + N[ms[3]]) / 2 - (N[c0] + N[c1] + N[c2] + N[c3]) / 4)
        els.append([c0, ms[0], c1, ms[3], len(N) - 1, ms[1], c3, ms[2], c2])
    return np.array(N), np.array(els)


def _mirror_y(nodes, els):
    """A mesh of y >= 0 mirrored about y = 0 (nodes on the axis shared; a
    mirrored element keeps its orientation with xi reversed)."""
    nodes = nodes.copy()
    on = np.abs(nodes[:, 0]) < 1e-9
    nodes[on, 0] = 0.0
    new = np.where(on, np.arange(len(nodes)), -1)
    new[~on] = len(nodes) + np.arange((~on).sum())
    out = np.vstack([nodes, nodes[~on] * [-1, 1]])
    return out, np.vstack([els, new[els][:, [2, 1, 0, 5, 4, 3, 8, 7, 6]]])


def _mirror_z(nodes, els):
    sw = lambda P: P[:, ::-1]
    n2, e2 = _mirror_y(sw(nodes), els)
    return sw(n2), e2      # the swap flips every element and swapping back flips it again


def _tri_q9(poly, h, axes, hfun=None):
    """Q9 elements of the region bounded by the open polyline `poly` (from a point
    on a symmetry axis around to another) closed along the axes; h the
    triangulation's edge (hfun: a finer edge along parts of the outline, from
    which the quality bound grades the inside). axes: 'y' (the half y >= 0,
    closed by y = 0) or 'yz' (the quarter, closed by y = 0 and z = 0)."""
    import triangle                                  # pip install triangle: only here
    b = _resample(poly, h, hfun=hfun)
    if axes == "yz":                                 # the quarter: its corner (0, 0) joins the two axes
        b = np.vstack([b, [[0.0, 0.0]]])
        axis = lambda p: abs(p[0]) < 1e-9 or abs(p[1]) < 1e-9
    else:
        axis = lambda p: abs(p[0]) < 1e-9
    n = len(b)
    T = triangle.triangulate(dict(vertices=b, segments=[[i, (i + 1) % n] for i in range(n)]),
                             f"pq30a{0.433 * h * h:.4f}")
    nodes, els = _q9(T["vertices"], T["triangles"], lambda p: not axis(p), poly)
    nodes, els = _mirror_y(nodes, els)
    return _mirror_z(nodes, els) if axes == "yz" else (nodes, els)


def rail_mesh(s=1.0):
    """The 60E1 rail: the right half triangulated, mirrored; z from the foot's
    underside, moved so the mid-height is at z = 0. The foot (its outline below
    RAIL_FOOT_Z) gets edges of RAIL_FOOT_H: its thin tips carry the foot's
    flapping modes, which the uniform mesh put 0.6 % high against one of half the size."""
    hfun = lambda p: (RAIL_FOOT_H if p[1] < RAIL_FOOT_Z else RAIL_H) / s
    nodes, els = _tri_q9(_polyline(RAIL60E1), RAIL_H / s, "y", hfun=hfun)
    nodes[:, 1] -= 86.0
    return nodes, els


def ipe_outline(G=IPE80, n_arc=24):
    """The quarter y >= 0, z >= 0 of an IPE profile from (b_w/2, 0) around to (0, h/2)."""
    H2, B2, w2 = G["h"] / 2, G["b"] / 2, G["tw"] / 2
    yf = H2 - G["tf"]
    cy, cz = w2 + G["r"], yf - G["r"]
    arc = [(cy - G["r"] * np.cos(t), cz + G["r"] * np.sin(t)) for t in np.linspace(0, np.pi / 2, n_arc)]
    return np.array([(w2, 0.0)] + arc + [(B2, yf), (B2, H2), (0.0, H2)])


def ibeam_mesh(s=1.0):
    return _tri_q9(ipe_outline(), IPE_H / s, "yz")


# ================================================================ the sections
FUND4 = {"vertical": ("vertical", 0), "lateral": ("lateral", 0), "axial": ("axial", 0), "torsional": ("torsional", 0)}
CLS4 = [("axial", 1, 1), ("vertical", 1, -1), ("lateral", -1, 1), ("torsional", -1, -1)]
LEG4 = [("vertical", "vertical bending"), ("lateral", "lateral bending"), ("axial", "axial"),
        ("torsional", "torsional"), (None, "higher order")]
STEEL = "steel, E = 210 GPa, ν = 0.29, ρ = 7850 kg/m³"
SECTIONS = {
    # the square's classes, C4v: A1 (axial), B1, E (one partner of each bending pair:
    # the (+, -) class, named vertical), A2 (torsional), B2; py, pz, pd the characters
    # of the mirrors y -> -y, z -> -z and of the diagonal
    "bar": dict(label="bar", kind="c4v", mesh=bar_mesh, fmax=190e3, xticks=[0, 50, 100, 150],
                classes=[("axial", 1, 1, 1), ("B1", 1, 1, -1), ("vertical", 1, -1, 0), ("torsional", -1, -1, -1),
                         ("B2", -1, -1, 1)],
                fund={"vertical": ("vertical", 0), "axial": ("axial", 0), "torsional": ("torsional", 0)},
                pairs=True, legend=[("vertical", "bending"), ("axial", "axial"), ("torsional", "torsional"),
                                    (None, "higher order")],
                what="square bar 20 × 20 mm",
                strip=dict(L=900.0, pw=410.0, d=.6, a=40.0, ys=1.0, lj=4, lm=10, slow=2.0e4),
                tour=[("vertical", 5, "vertical", 20, 150), ("axial", 20, "axial", 50, 150),
                      ("torsional", 20, "torsional", 50, 150), ("h1", 100, "h1", 105, 185)]),
    "ibeam": dict(label="I-beam", kind="mirror", mesh=ibeam_mesh, planes=(1, 1), fmax=52e3,
                  xticks=[0, 10, 20, 30, 40, 50], classes=CLS4, fund=FUND4, legend=LEG4, what="I-beam IPE 80",
                  strip=dict(L=1800.0, pw=950.0, d=.6, a=40.0, ys=1.0, lj=4, lm=10, slow=5300.0),
                  tour=[("vertical", 3, "vertical", 5, 10), ("axial", 3, "axial", 5, 12),
                        ("torsional", 3, "torsional", 4, 20), ("lateral", 1, "lateral", 2, 20), ("h1", 2, "h1", 3, 20)]),
    "rail": dict(label="rail", kind="mirror", mesh=rail_mesh, planes=(1, 0), fmax=22.5e3,
                 xticks=[0, 5, 10, 15, 20], classes=[("sym", 1, 0), ("anti", -1, 0)],
                 fund={"vertical": ("sym", 0), "axial": ("sym", 1), "lateral": ("anti", 0), "torsional": ("anti", 1)},
                 legend=LEG4, what="rail 60E1 (UIC60)",
                 strip=dict(L=3500.0, pw=1600.0, d=.6, a=40.0, ys=1.0, lj=4, lm=10, slow=2700.0),
                 tour=[("vertical", 2, "vertical", 3, 5), ("axial", 2, "axial", 3, 10),
                       ("lateral", 1, "lateral", 2, 15), ("torsional", 2, "torsional", 3, 15), ("h1", 2, "h1", 3, 15)]),
    "pipe": dict(label="pipe", kind="ring", mesh=pipe_mesh, nth=PIPE_NTH, fmax=175e3, xticks=[0, 25, 50, 75, 100, 125, 150, 175],
                 classes=[("L0", "L", 0), ("V0", "V", 0)] + [(f"V{n}", "V", n) for n in range(1, 13)],
                 fund={"vertical": ("V1", 0), "axial": ("L0", 0), "torsional": ("V0", 0)}, pairs=True,
                 legend=[("vertical", "bending"), ("axial", "axial"), ("torsional", "torsional"), (None, "higher order")],
                 what="pipe NPS 1¼ schedule 40, 42.16 × 3.56 mm",
                 strip=dict(L=800.0, pw=380.0, d=.6, a=40.0, ys=1.0, lj=4, lm=10, slow=1.6e4),
                 tour=[("vertical", 10, "vertical", 20, 40), ("axial", 10, "axial", 20, 45),
                       ("torsional", 20, "torsional", 40, 120), ("h1", 10, "h1", 15, 120)]),
    "plate": dict(label="plate", kind="plate", mesh=plate_mesh, fmax=250e3, xticks=[0, 50, 100, 150, 200, 250],
                  classes=[("A", "Lamb", -1), ("S", "Lamb", 1), ("SHs", "SH", 1), ("SHa", "SH", -1)],
                  fund={"vertical": ("A", 0), "axial": ("S", 0), "lateral": ("SHs", 0)},
                  legend=[("vertical", "A0 Lamb"), ("axial", "S0 Lamb"), ("lateral", "SH0"), (None, "higher order")],
                  what="plate 10 mm thick, infinite width",
                  strip=dict(L=560.0, pw=210.0, d=.5, a=30.0, ys=3.5, lj=4, lm=8, slow=2.4e4),
                  tour=[("vertical", 10, "vertical", 50, 150), ("axial", 20, "axial", 50, 240),
                        ("lateral", 20, "lateral", 50, 240), (("SHa", 0), 175, ("SHa", 0), 180, 245)]),
}
ORDER = ["bar", "ibeam", "rail", "pipe", "plate"]


def class_meta(Z):
    if Z["kind"] == "mirror":
        return [dict(name=c[0], py=c[1], pz=c[2], pd=0) for c in Z["classes"]]
    if Z["kind"] == "c4v":
        return [dict(name=c[0], py=c[1], pz=c[2], pd=c[3]) for c in Z["classes"]]
    if Z["kind"] == "plate":
        return [dict(name=c[0], family=c[1], parity=c[2]) for c in Z["classes"]]
    return [dict(name=c[0], typ=c[1], n=c[2]) for c in Z["classes"]]


def make_section(key, s=1.0):
    """The section's SAFE model with its classes (s: mesh density, 1 the page's)."""
    Z = SECTIONS[key]
    if key == "pipe":
        nth, nr = int(round(PIPE_NTH * s)), max(2, int(round(PIPE_NR * s)))
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
        for c in Z["classes"]:
            S.classes[c[0]] = S.mirror_basis(*c[1:])
    return S


def _rcm(A):
    """Reverse Cuthill-McKee from a pseudo-peripheral node (George and Liu: from the node of
    least degree, on to the farthest node of least degree until the eccentricity stops
    growing; neighbours taken in order of degree): on the rail a skyline a quarter smaller
    than from the node of least degree alone (scipy's start)."""
    from collections import deque
    from scipy.sparse.csgraph import shortest_path
    A = sp.csr_matrix(A)
    A.sort_indices()
    deg = np.diff(A.indptr)
    v, ecc = int(np.argmin(deg)), -1.0
    while True:
        dist = shortest_path(A, unweighted=True, indices=v)
        if dist.max() <= ecc:
            break
        ecc = dist.max()
        far = np.flatnonzero(dist == ecc)
        v = int(far[np.argmin(deg[far])])
    seen = np.zeros(A.shape[0], bool)
    seen[v] = True
    order, q = [], deque([v])
    while q:
        u = q.popleft()
        order.append(u)
        nb = [w for w in A.indices[A.indptr[u]:A.indptr[u + 1]] if not seen[w]]
        nb.sort(key=lambda w: (deg[w], w))
        for w in nb:
            seen[w] = True
            q.append(w)
    assert len(order) == A.shape[0], "the mesh's graph is not connected"
    return np.array(order[::-1])


def rep_order(S, cm):
    """A reverse Cuthill-McKee order of the orbit representatives (the smallest
    node of each orbit under the class's operations) on the graph of
    representatives sharing an element: rank per node, -1 for the rest. The page
    numbers a class's columns in this order and keeps its matrices as a skyline."""
    els = S.group(cm.get("py", 0), cm.get("pz", 0), cm.get("pd", 0))
    rep = np.min(np.array([m for m, _, _ in els]), axis=0)
    reps = np.unique(rep)
    loc = -np.ones(len(rep), int); loc[reps] = np.arange(len(reps))
    r, c = [], []
    for e in S.elems:
        q = loc[rep[e]]
        r += list(np.repeat(q, 9)); c += list(np.tile(q, 9))
    A = sp.csr_matrix((np.ones(len(r)), (r, c)), shape=(len(reps), len(reps)))
    rank = -np.ones(len(rep), int)
    rank[reps[_rcm(A)]] = np.arange(len(reps))
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


def _screen(f, cp, fmax):
    X = np.minimum(f, 1.04 * fmax) / fmax * REF_W
    Y = np.minimum(cp, 1.04 * CP_MAX) / CP_MAX * REF_H
    return X, Y


def kmax_of(S, fmax):
    """A wavenumber past which every branch of every class lies above fmax: the
    lowest branch over the classes, found at k = 2 pi fmax / 900 m/s and raised
    until it is 4 % over fmax."""
    k = 2 * np.pi * fmax / 900.0
    while min(S.omegas(c, k, 1)[0] for c in S.classes) / (2 * np.pi) < 1.04 * fmax:
        k *= 1.25
    return k


def branches_g(model, name, n, kmax, fmax):
    """w(k) of the n lowest branches of a class on a k grid refined until
    consecutive points inside the window are < 2 units apart."""
    ks = np.unique(np.concatenate([np.geomspace(0.4, 0.05 * kmax, 30), np.linspace(0.05 * kmax, kmax, 120)]))
    W = np.array([model.omegas(name, k, n) for k in ks])
    for _ in range(14):
        f, cp = W / (2 * np.pi), W / ks[:, None]
        X, Y = _screen(f, cp, fmax)
        d = np.hypot(np.diff(X, axis=0), np.diff(Y, axis=0))
        out = ((f[:-1] > 1.03 * fmax) & (f[1:] > 1.03 * fmax)) | \
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


MODEL = "safe-q9-2"   # the formulation and sweep; change it when either changes (the cache key holds it)


def section_key(key):
    """What a section's sweep depends on: the formulation's version, the mesh itself,
    its classes, window and material."""
    Z = SECTIONS[key]
    nodes, elems = pipe_mesh() if key == "pipe" else Z["mesh"]()
    h = hashlib.sha1(repr((MODEL, key, Z["kind"], Z["classes"], Z["fund"], Z["fmax"], CP_MAX, REF_W, REF_H,
                           sm.E, sm.NU, sm.RHO)).encode())
    h.update(np.asarray(nodes, np.float32).tobytes()); h.update(np.asarray(elems, np.int64).tobytes())
    return h.hexdigest()[:12]


def _clean(R):
    """A sweep without the points where a branch's w^2 fell under the solver's round-off (clipped to 0)."""
    for name, (ks, W) in list(R["br"].items()):
        m = (ks >= 0.4) & (W.min(axis=1) > 0)
        R["br"][name] = (ks[m], W[m])
    return R


def compute_section(key):
    """A section's sweep and checks (cached in the temp folder)."""
    Z = SECTIONS[key]
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-{key}-{section_key(key)}.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return _clean(pickle.load(fh))
    t0 = time.time()
    fmax = Z["fmax"]
    S = make_section(key)
    kmax = kmax_of(S, fmax)
    R = {"key": key, "ndof": S.ndof, "nel": len(S.elems), "nnode": len(S.nodes), "minJ": S.minJ, "kmax": kmax,
         "props": properties(S), "tors": torsion(S), "cut": {}, "br": {},
         "dims": {c: S.classes[c].shape[1] for c in S.classes}}
    for name in S.classes:
        fc = S.omegas(name, 0.0, 30) / (2 * np.pi)
        R["cut"][name] = fc
        n = int(np.sum(fc < 1.1 * fmax))
        if n:
            R["br"][name] = branches_g(S, name, n, kmax, fmax)
    # the fundamental modes at small k, against the closed forms
    val = []
    for k in (1.0, 2.0, 5.0, 10.0):
        row = {"k": k}
        for typ, (c, b) in Z["fund"].items():
            w = S.omegas(c, k, b + 1)[b]
            row[typ] = (w / (2 * np.pi), w / k)
        val.append(row)
    R["val"] = val
    R["time"] = time.time() - t0
    with open(cache, "wb") as fh:
        pickle.dump(R, fh)
    return _clean(R)


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
    beyond each end, packed as float32; its class, name and kind of mode. A
    branch may turn back in f (a backward wave below its cut-on frequency: f
    falls as k grows, then rises), but never leaves the window and comes back."""
    Z = SECTIONS[key]
    fmax = Z["fmax"]
    cnames = [c[0] for c in Z["classes"]]
    fund = {v: t for t, v in Z["fund"].items()}
    brs, flat, seen = [], [], {}
    for ci, name in enumerate(cnames):
        if name not in R["br"]:
            continue
        ks, W = R["br"][name]
        for b in range(W.shape[1]):
            f, cp = W[:, b] / (2 * np.pi), W[:, b] / ks
            inside = (f <= fmax) & (cp <= CP_MAX)
            if not inside.any():
                continue
            idx = np.flatnonzero(inside)
            assert np.all(np.diff(idx) == 1), (key, name, b, "leaves the window and comes back")
            lo, hi = max(idx[0] - 1, 0), min(idx[-1] + 1, len(ks) - 1)
            fc = float(R["cut"][name][b]) / 1e3
            typ = fund.get((name, b), "")
            if key == "pipe":
                nm = f"{NAMES[typ] if typ != 'vertical' else 'bending'} {pipe_name(name, b)}" if typ else \
                    f"higher order mode {pipe_name(name, b)}, cut-on {fc:.1f} kHz"
            elif key == "plate":
                nm = ("SH" + str(2 * b + (name == "SHa"))) if name.startswith("SH") else name + str(b) + " Lamb"
            elif typ:
                nm = "bending" if Z.get("pairs") and typ == "vertical" else NAMES[typ]
            else:
                nm = f"higher order mode, cut-on {fc:.1f} kHz"
                seen[nm] = seen.get(nm, 0) + 1
                if seen[nm] > 1:
                    nm += " (second)"
            back = bool(np.any(np.diff(f[idx]) <= 0))
            brs.append({"ci": ci, "b": b, "fc": round(fc, 3), "n": int(hi - lo + 1), "o": len(flat), "nm": nm,
                        "type": typ, "back": back})
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
        ins = np.flatnonzero((fs <= Z["fmax"] / 1e3) & (cs <= CP_MAX / 1e3))
        inp = np.flatnonzero((F <= Z["fmax"] / 1e3) & (CL <= CP_MAX / 1e3))
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
    if Z.get("pairs"):
        ids["lateral"] = ids["vertical"]
    h1 = min((i for i, b in enumerate(brs) if not b["type"]), key=lambda i: brs[i]["fc"])
    ids["h1"] = h1
    frange = lambda i: (flat[brs[i]["o"]:brs[i]["o"] + brs[i]["n"]][1:-1].min(), flat[brs[i]["o"]:brs[i]["o"] + brs[i]["n"]][1:-1].max())
    ids.update({(Z["classes"][r["ci"]][0], r["b"]): i for i, r in enumerate(brs)})   # or (class, branch)
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


def elem_sizes(S):
    """Each element's longest corner-to-corner edge (mm)."""
    P = S.nodes_mm[S.elems[:, [0, 2, 8, 6]]]
    return np.max(np.hypot(*(np.roll(P, -1, axis=1) - P).transpose(2, 0, 1)), axis=1)


def mesh_words(key, S):
    """The mesh in words, for the parameter line: the plate's elements are 1 mm through its
    thickness (its basis makes the slice's width immaterial); the others' longest edges."""
    if key == "plate":
        return f"{len(S.elems)} quadratic elements through the thickness, {PLATE_D / len(S.elems):.3g} mm each"
    hs = elem_sizes(S)
    msz = f"{hs.max():.3g} mm" if hs.max() - hs.min() < .02 * hs.max() else f"{hs.min():.2g} to {hs.max():.2g} mm"
    return f"{len(S.elems)} quadratic elements of {msz}"


def sci(v, tex=True):
    """2.6 x 10^4, in the engine's TeX or as text."""
    e = int(np.floor(np.log10(v)))
    m = v / 10 ** e
    if m >= 9.95:
        m, e = m / 10, e + 1
    return f"{m:.1f}\\ \\times\\ 10^{{{e}}}" if tex else f"{m:.1f} × 10^{e}"


def strip_of(key, R):
    """The drawn waveguide of a section (the page's sec.T): its length L (mm) and the
    packets' Hann envelope pw (mm) across, the oblique view (depth factor d, angle a in
    degrees, ys the drawn width over the slice's, for the plate), the scale s (units a
    mm) that fits L and the receding depth between x = 40 and 970 units, and one clock:
    the steel's time slowed `slow` times, for every operating point and both waves (so
    the crests of the tour's highest frequency f cycle at f / slow, about 7 Hz)."""
    Z = SECTIONS[key]
    G = dict(Z["strip"])
    S_nodes = (pipe_mesh() if key == "pipe" else Z["mesh"]())[0]
    B = float(np.ptp(S_nodes[:, 0]))
    cd = G["d"] * np.cos(np.radians(G["a"]))
    s = 930.0 / (G["L"] + B * G["ys"] * cd)
    return dict(G, s=round(s, 5), x1=round(40 + s * G["L"], 3),
                label=r"\rm{shown}\ " + sci(G["slow"]) + r"\ \rm{times slower than real time}")


def section_blob(key, R):
    """Everything the page needs of a section, as one blob."""
    Z = SECTIONS[key]
    S = make_section(key)
    brs, flat = curves_of(key, R)
    tb, tflat, _ = thinned(key, R)
    loops = boundary(S)
    fcs = faces(S, loops)
    B = float(np.ptp(S.nodes_mm[:, 0])); Hh = float(np.ptp(S.nodes_mm[:, 1]))
    fund = {t: next(i for i, b in enumerate(brs) if b["type"] == t) for t in Z["fund"]}
    if Z.get("pairs"):
        fund["lateral"] = fund["vertical"]
    cuts = sorted(round(float(b["fc"]), 3) for b in brs if b["fc"] > .05)    # kHz: the drawn higher order branches' own
    fc1 = min(b["fc"] for b in brs if not b["type"])
    params = f"{Z['what']}; SAFE, {mesh_words(key, S)}, solved in the page"
    meta = {"key": key, "label": Z["label"], "kind": Z["kind"], "E": sm.E, "nu": sm.NU, "rho": sm.RHO,
            "classes": class_meta(Z), "fmax": Z["fmax"] / 1e3, "xticks": Z["xticks"], "strip": strip_of(key, R),
            "nth": getattr(S, "nth", 0), "brs": tb, "fund": fund, "tour": tour_of(key, brs, flat), "loops": loops,
            "faces": fcs, "B": B, "H": Hh, "sscale": round(min(160 / B, 300 / Hh), 4), "fc1": fc1, "cuts": cuts,
            "A": float(R["props"]["A"]), "legend": [[t, s_] for t, s_ in Z["legend"]], "params": params}
    arrays = [("nodes", np.asarray(S.nodes_mm, np.float32).ravel()),
              ("elems", np.asarray(S.elems, np.uint16).ravel())]
    if Z["kind"] == "mirror":
        arrays.append(("rank", np.asarray(rep_order(S, {"py": Z["planes"][0], "pz": Z["planes"][1]}), np.int16)))
    elif Z["kind"] == "c4v":
        arrays.append(("rank", np.asarray(rep_order(S, {"py": 1, "pz": 1}), np.int16)))
        arrays.append(("rank8", np.asarray(rep_order(S, {"py": 1, "pz": 1, "pd": 1}), np.int16)))
    arrays.append(("curves", tflat))
    arrays.append(("glide", glide_rates(key, R)))
    return blob(meta, arrays)


def glide_rates(key, R):
    """Wave 2's exact group velocity (km/s) at the NG + 1 moments of each tour stop's glide, at
    the wavenumbers the page takes there (its kAtF on the laid-out curve, as k_at_f), from the
    section's model by shift-invert (group_near): the page integrates these rather than solve
    NG + 1 states as each stop begins. Stop after stop, NG + 1 each (cached with the sweep)."""
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-{key}-{section_key(key)}-glide.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    Z, S = SECTIONS[key], make_section(key)
    tb, curves = page_curve(key, R)
    brs, flat = curves_of(key, R)
    NG = TOUR_T["NG"]
    out = []
    for s_ in tour_of(key, brs, flat):
        cv, name = curves[s_["b2"]], Z["classes"][tb[s_["b2"]]["ci"]][0]
        for j in range(NG + 1):
            f = s_["fa"] if j == 0 else s_["f2"] if j == NG else s_["fa"] + (s_["f2"] - s_["fa"]) * ease_in_out(j / NG)
            out.append(group_near(S, name, k_at_f(cv, f), 2e3 * np.pi * f)[1] / 1e3)
    arr = np.asarray(out, np.float32)
    with open(cache, "wb") as fh:
        pickle.dump(arr, fh)
    return arr


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
        sec = {"kind": Z["kind"], "E": sm.E, "nu": sm.NU, "rho": sm.RHO, "nth": getattr(S, "nth", 0),
               "classes": class_meta(Z),
               "nodes": np.asarray(S.nodes_mm, np.float32).ravel().tolist(), "elems": S.elems.ravel().tolist()}
        if Z["kind"] == "mirror":
            sec["rank"] = rep_order(S, {"py": Z["planes"][0], "pz": Z["planes"][1]}).tolist()
        elif Z["kind"] == "c4v":
            sec["rank"] = rep_order(S, {"py": 1, "pz": 1}).tolist()
            sec["rank8"] = rep_order(S, {"py": 1, "pz": 1, "pd": 1}).tolist()
        data["sections"][key] = sec
        cases, rf = [], []
        for r in tb:
            o, n = r["o"], r["n"]
            k, f, cp = lay(tflat[o:o + n], tflat[o + n:o + 2 * n], tflat[o + 2 * n:o + 3 * n])   # the page's curve
            inw = np.flatnonzero((f <= Z["fmax"] / 1e3) & (cp <= CP_MAX / 1e3))
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
                   "  const sec = {...S, nodes: Float32Array.from(S.nodes), elems: Int32Array.from(S.elems), rank: S.rank ? Int32Array.from(S.rank) : null,"
                   " rank8: S.rank8 ? Int32Array.from(S.rank8) : null};\n"
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


# ================================================================ references, independent of SAFE
from scipy.optimize import brentq as _brentq
from scipy.special import jv as _jv, yv as _yv, jvp as _jvp, yvp as _yvp, iv as _iv, kv as _kv, ivp as _ivp, kvp as _kvp


def _cst(x2, h):
    """cos(x h), sin(x h)/x and x sin(x h) for x = sqrt(x2), x2 of either sign: real."""
    if x2 > 0:
        x = np.sqrt(x2)
        return np.cos(x * h), np.sin(x * h) / x, x * np.sin(x * h)
    if x2 < 0:
        x = np.sqrt(-x2)
        return np.cosh(x * h), np.sinh(x * h) / x, -x * np.sinh(x * h)
    return 1.0, h, 0.0


def lamb(fam, k, w, d=PLATE_D / 1e3):
    """The Rayleigh-Lamb functions of a free plate of thickness d, real for every real k
    and w (h = d/2, p^2 = w^2/c_L^2 - k^2, q^2 = w^2/c_T^2 - k^2): symmetric
    (k^2 - q^2)^2 cos(ph) sin(qh)/q + 4 k^2 p sin(ph) cos(qh), antisymmetric
    (k^2 - q^2)^2 sin(ph)/p cos(qh) + 4 k^2 cos(ph) q sin(qh)."""
    h = d / 2
    Cp, Sp, Tp = _cst((w / sm.C_L) ** 2 - k * k, h)
    Cq, Sq, Tq = _cst((w / sm.C_T) ** 2 - k * k, h)
    a = (2 * k * k - (w / sm.C_T) ** 2) ** 2
    return a * Cp * Sq + 4 * k * k * Tp * Cq if fam == "S" else a * Sp * Cq + 4 * k * k * Cp * Tq


def lamb_root_near(fam, k, w0, rel=3e-3, m=300):
    """The root of the Rayleigh-Lamb function nearest w0 within w0 (1 +- rel)."""
    ws = w0 * np.linspace(1 - rel, 1 + rel, m)
    F = np.array([lamb(fam, k, w) for w in ws])
    best = None
    for i in np.flatnonzero(np.sign(F[:-1]) * np.sign(F[1:]) < 0):
        r = _brentq(lambda w: lamb(fam, k, w), ws[i], ws[i + 1], xtol=1e-13 * w0)
        if best is None or abs(r - w0) < abs(best - w0):
            best = r
    return best


def lamb_cutoffs(fam, fmax, d=PLATE_D / 1e3):
    """k = 0: symmetric cos(w h/c_L) sin(w h/c_T) = 0, antisymmetric sin(w h/c_L) cos(w h/c_T) = 0."""
    out = []
    for m in range(1, 60):
        out += [(2 * m - 1) * sm.C_L / (2 * d), m * sm.C_T / d] if fam == "S" else \
               [(2 * m - 1) * sm.C_T / (2 * d), m * sm.C_L / d]
    return sorted(f for f in out if f < fmax)


def _zpair(n, g2, r):
    """The radial equation's two solutions Z'' + Z'/r + (g2 - n^2/r^2) Z = 0 at r and their
    r-derivatives: J_n, Y_n of g r (g2 > 0), I_n, K_n of |g| r (g2 < 0)."""
    if g2 > 0:
        g = np.sqrt(g2)
        return [(_jv(n, g * r), g * _jvp(n, g * r)), (_yv(n, g * r), g * _yvp(n, g * r))]
    g = np.sqrt(-g2)
    return [(_iv(n, g * r), g * _ivp(n, g * r)), (_kv(n, g * r), g * _kvp(n, g * r))]


def gazis_det(n, k, w, a, b):
    """The determinant of the traction matrix of a free hollow cylinder (radii a < b),
    harmonic n, wavenumber k, frequency w (Gazis 1959), real. u = grad(phi) + curl(psi
    e_x) + curl curl(chi e_x), each potential Z(r) exp(i(n th + k x)), Z a radial solution
    (alpha^2 = w^2/c_L^2 - k^2 for phi, beta^2 = w^2/c_T^2 - k^2 for psi and chi):
      u_r = Phi' + i n Psi/r + i k X',  u_th = i n Phi/r - Psi' - n k X/r,  u_x = i k Phi + beta^2 X;
    rows sigma_rr, sigma_rth, sigma_rx at r = a and b, columns J and Y (or I and K) of
    each potential; the factors i taken out of the psi and chi columns and of the
    sigma_rth and sigma_rx rows, every entry is real; columns scaled to unit size."""
    lam_, mu = sm.LAM, sm.MU
    al2, be2 = (w / sm.C_L) ** 2 - k * k, (w / sm.C_T) ** 2 - k * k
    rows = []
    for r in (a, b):
        cols = []
        for pot, g2 in (("phi", al2), ("psi", be2), ("chi", be2)):
            for Z, Zp in _zpair(n, g2, r):
                Zpp = -Zp / r - (g2 - n * n / (r * r)) * Z
                if pot == "phi":
                    ur, urp = Zp, Zpp
                    uth, uthp = n * Z / r, n * (Zp / r - Z / (r * r))
                    srr = lam_ * (-(w / sm.C_L) ** 2) * Z + 2 * mu * urp
                    srt = mu * (uthp - uth / r + n * ur / r)
                    srx = mu * (k * Zp + k * ur)
                elif pot == "psi":
                    ur, urp = n * Z / r, n * (Zp / r - Z / (r * r))
                    uth, uthp = -Zp, -Zpp
                    srr = -2 * mu * urp
                    srt = mu * (uthp - uth / r - n * ur / r)
                    srx = -mu * k * ur
                else:
                    ur, urp = k * Zp, k * Zpp
                    uth, uthp = -n * k * Z / r, -n * k * (Zp / r - Z / (r * r))
                    srr = -2 * mu * urp
                    srt = mu * (uthp - uth / r - n * ur / r)
                    srx = mu * (be2 * Zp - k * ur)
                cols.append((srr, srt, srx))
        rows += list(np.array(cols).T)
    M = np.array(rows)
    return np.linalg.det(M / np.maximum(np.abs(M).max(axis=0), 1e-300))


def gazis_root_near(n, k, w0, a, b, rel=3e-3, m=300):
    """The root of the Gazis determinant nearest w0 within w0 (1 +- rel)."""
    ws = w0 * np.linspace(1 - rel, 1 + rel, m)
    F = np.array([gazis_det(n, k, w, a, b) for w in ws])
    best = None
    for i in np.flatnonzero(np.sign(F[:-1]) * np.sign(F[1:]) < 0):
        r = _brentq(lambda w: gazis_det(n, k, w, a, b), ws[i], ws[i + 1], xtol=1e-13 * w0)
        if best is None or abs(r - w0) < abs(best - w0):
            best = r
    return best


def cyl_cutoffs(n, fmax, a, b, part, nf=30000):
    """k = 0 cut-off frequencies (Hz, below fmax) of the free hollow cylinder, exactly:
    'shear' (u_x only: J_n'(be a) Y_n'(be b) - J_n'(be b) Y_n'(be a) = 0, be = w/c_T);
    'plane' (u_r, u_th, plane strain: phi = Z_n(w r/c_L) cos n th, psi = Z_n(w r/c_T) sin n th,
    sigma_rr = sigma_rth = 0 at both radii); for n = 0 'phi' (radial) and 'psi' (torsional)."""
    lam_, mu = sm.LAM, sm.MU

    def F(w):
        if part == "shear":
            be = w / sm.C_T
            return _jvp(n, be * a) * _yvp(n, be * b) - _jvp(n, be * b) * _yvp(n, be * a)
        rows = []
        for r in (a, b):
            rr, rt = [], []
            for which, g in (("phi", w / sm.C_L), ("psi", w / sm.C_T)):
                if part in ("phi", "psi") and which != part:
                    continue
                for Zf, Zpf in ((_jv, _jvp), (_yv, _yvp)):
                    Z, Zp = Zf(n, g * r), g * Zpf(n, g * r)
                    Zpp = -Zp / r - (g * g - n * n / (r * r)) * Z
                    if which == "phi":
                        rr.append(lam_ * (-(w / sm.C_L) ** 2) * Z + 2 * mu * Zpp)
                        rt.append(mu * (-2 * n * Zp / r + 2 * n * Z / (r * r)))
                    else:
                        rr.append(2 * mu * n * (Zp / r - Z / (r * r)))
                        rt.append(mu * (-Zpp + Zp / r - n * n * Z / (r * r)))
            rows += [rr] if part == "phi" else [rt] if part == "psi" else [rr, rt]
        M = np.array(rows)
        return np.linalg.det(M / np.maximum(np.abs(M).max(axis=0), 1e-300))
    ws = np.linspace(2 * np.pi * fmax * 1e-4, 2 * np.pi * fmax, nf)
    Fv = np.array([F(w) for w in ws])
    out = []
    for i in np.flatnonzero(np.sign(Fv[:-1]) * np.sign(Fv[1:]) < 0):
        r = _brentq(F, ws[i], ws[i + 1], xtol=1e-12 * ws[i + 1])
        if abs(F(r)) < 1e-6:                 # a root, not a pole of the scaled determinant
            out.append(r / (2 * np.pi))
    return out


# Hayashi, Kawashima and Rose (2004), "Calculation for guided waves in pipes and rails",
# Key Engineering Materials 270-273, 410-415, Fig. 2: phase velocity of a square rod h x h,
# SAFE (12 x 12 elements), Poisson's ratio 0.3, c/c_T to 3 against f h to 5,000 kHz mm. Its
# 765 dots, read from the paper's vector drawing (the PDF at sites.esm.psu.edu): f h in
# half kHz mm and c/c_T in thousandths, int16 pairs in base64.
HAYASHI_SQUARE = (
    "XADVAFwAnANcAGMGxgAoAcYAnAPGAGMGLAFhASwBnAMsAWMGkgGWAZIBnAOSAWMG+AHAAfgBnAP4AWMGXgLfAV4CnANeAmMGtwL/"
    "AbcCnAO3AmMGHQMZAh0DnAMdA2MGHQNzBoMDMwKDA5wDgwNjBu0DSALtA5wD7QNeBlcEXQJXBJwDVwReBr0EbQK9BJwDvQReBiMF"
    "fQIjBZwDIwVYBnwFjQJ8BZwDfAVYBuIFngLiBZwD4gVYBkgGqQJIBpwDSAZTBq4GuAKuBpwDrgZTBhQHwwIUB5wDFAdOBn4HzwJ+"
    "B5wDfgdOBuQH2gLkB5wD5AdOBk4I5AJOCJwDTghJBrQI6QK0CJwDtAhDBhoJ9AIaCZwDGglDBoAJ/gKACZwDgAk+BuYJBAPmCZwD"
    "5gk5BkwKCQNMCpwDTAo5BrIKEwOyCpwDsgo0BhgLEwMYC5wDGAsuBoILHgOCC5wDggspBt8LHgPfC5wD3wsiBicMLgMnDMEDRQwo"
    "A0UMnANFDB0GqwwoA6sMnAOrDBgGEQ0zAxENnAMRDRIGdw0zA3cNnAN3DQ0G3Q04A90NnAPdDQMGNg49AzYOnAM2DvgFnA5DA5wO"
    "nAOcDu4FBg9IAwYPnAMGD+cFbA9IA2wPnANsD9wFbA86C9YPTQPWD5wD1g/RBdYPGgjWD48KPBBNAzwQnAM8EMIFPBAABzwQ/Ami"
    "EFIDohCcA6IQtwWiEGgGohB8CQgRUgMIEZwDCBGtBQgRAwYIEQEJbhFYA24RnANuEZ0FbhG3BW4RiQjUEV0D1BGcA9QRgwXUEY0F"
    "1BG8BdQRFQg6El0DOhKcAzoSLwU6ElMFOhJ4BToSoAegEl0DoBKcA6AS4ASgEi8FoBJoBaASKgcKE2IDChOcAwoTqwQKEw8FChNZ"
    "BQoTxwYKE3kLdBNoA3QTnAN0E4cEdBP1BHQTRAV0E20GdBOECtoTaAPaE5wD2hNlBNoT2wTaEy8F2hMdBtoT5wkzFGgDMxScAzMU"
    "SwQzFMYEMxQaBTMU1wUzFHEJmRRoA5kUnAOZFDQEmRS2BJkUBQWZFKIFmRQcCf8UbQP/FJwD/xQlBP8UpgT/FPAE/xRuBf8U3Qhl"
    "FW0DZRWcA2UVFQRlFZwEZRXbBGUVSQVlFZ4IyxVyA8sVnAPLFQUEyxWMBMsVywTLFSQFyxV0CDEWcgMxFpwDMRb7AzEWgQQxFrsE"
    "MRYFBTEWRAgxFuMKMRaEC5sWcgObFpwDmxbwA5sWdQSbFqsEmxbqBJsWHwibFlwJmxYEC/QWcgP0FpwD9BbrA/QWcAT0FpwE9BbV"
    "BPQWAAj0FnQI9BaZCl4XdwNeF5wDXhfmA14XZQReF4wEXhfABF4X1gdeF+AHXhdACsQXdwPEF5wDxBfbA8QXWwTEF3oExBexBMQX"
    "XwfEF78HxBfsCSoYdwMqGJwDKhjWAyoYVgQqGHAEKhicBCoYAAcqGKUHKhiiCZAYfQOQGJwDkBjRA5AYUASQGGUEkBiRBJAYsgaQ"
    "GIkHkBhcCfYYfQP2GJwD9hjLA/YYRgT2GFsE9hiBBPYYcwb2GHQH9hghCfYYGQtcGX0DXBmcA1wZxgNcGUYEXBlQBFwZcARcGT4G"
    "XBlaB1wZ5whcGSAKwhl9A8IZnAPCGcYDwhk6BMIZRgTCGWUEwhkNBsIZPwfCGbgIwhmTCSwafQMsGpwDLBrBAywaOgQsGj8ELBpb"
    "BCwa4QUsGioHLBqJCCwaJgksGvYJkhqCA5IanAOSGrwDkhovBJIaNASSGlYEkhrCBZIaFQeSGl8Ikhq9CJIa3Qj8GoID/BqcA/wa"
    "vAP8Gi8E/BpLBPwaogX8GvYG/BoQCPwaNAj8GqgIYhuCA2IbnANiG7wDYhsqBGIbRgRiG4MFYhvWBmIbmgdiGxAIYht0CMgbhwPI"
    "G5wDyBu2A8gbJQTIGzoEyBtoBcgbtwbIG0oHyBvrB8gbVAguHIcDLhycAy4csQMuHBoELhwlBC4cNAQuHFMFLhyNBi4cFQcuHMoH"
    "LhwvCJQchwOUHJwDlByxA5QcGgSUHB8ElBwvBJQcPgWUHF4GlBz2BpQcqgeUHBUI+hyHA/ocnAP6HLED+hwVBPocGgT6HCUE+hwp"
    "BfocNAb6HNYG+hyJB/oc+wdTHYcDUx2cA1MdsQNTHRAEUx0aBFMdJQRTHRoFUx0NBlMdwQZTHW8HUx3gB7kdhwO5HZwDuR2sA7kd"
    "CgS5HRoEuR0fBLkdCgW5HecFuR2sBrkdVAe5HdEHIx6HAyMeoQMjHqwDIx4FBCMeFQQjHhoEIx76BCMewgUjHpcGIx41ByMevweN"
    "HowDjR6hA40erAONHgUEjR4QBI0eFQSNHuoEjR6nBY0eiAaNHiAHjR6qB/MejAPzHqED8x6nA/MeAATzHhAE8x7gBPMejQXzHngG"
    "8x4GB/MeoAdZH4wDWR+hA1kfpwNZH/sDWR8QBFkf1QRZH3gFWR9jBlkf8QZZH44Hvx+MA78foQO/H6cDvx/7A78fCgS/H8YEvx9j"
    "Bb8fUwa/H9YGvx+EByUgkgMlIKEDJSCnAyUg9QMlIAUEJSAKBCUguwQlIE4FJSBDBiUgwQYlINEGJSB0B4sgkgOLIKEDiyCnA4sg"
    "9QOLIAUEiyC2BIsgPgWLIDQGiyCsBosgaQeLILgL5CCSA+QgoQPkIKcD5CDwA+QgAATkIAUE5CCrBOQgLwXkICIG5CCdBuQgXwfk"
    "IG8K5CCZC0ohkgNKIaEDSiGnA0oh8ANKIfsDSiEFBEohpgRKIR8FSiENBkohiAZKIVQHSiGDCUohBAtKIToLSiFPC7QhkgO0IaED"
    "tCGnA7Qh8AO0IfsDtCEFBLQhnAS0IQ8FtCEDBrQhcwa0IUoHtCHSCLQhsgm0IbkKtCEJCxoikgMaIqEDGiKnAxoi6wMaIvsDGiIA"
    "BBoikQQaIgUFGiLuBRoiYwYaIkUHGiJJCBoiwggaIkUKGiLICoQikgOEIqEDhCKnA4Qi6wOEIvUDhCIABIQijASEIvoEhCLhBYQi"
    "TgaEIjUHhCLbB4QiHwiEItwJhCKPCuoikgPqIqED6iLmA+oi9QPqIvsD6iKHBOoi6gTqIswF6iI+BuoiKgfqInkH6iKlB+oifAnq"
    "IloKUCOSA1AjoQNQI+YDUCPwA1Aj+wNQI3oEUCPgBFAjvAVQIy4GUCMLB1AjKgdQI1QHUCMmCVAjJgq2I5IDtiOhA7Yj5gO2I/AD"
    "tiP7A7YjegS2I9sEtiOtBbYjGAa2I9YGtiPrBrYjNQe2I9cItiP2CRwkkgMcJKEDHCTmAxwk8AMcJPsDHCRwBBwk0AQcJKIFHCQN"
    "BhwknQYcJLIGHCQqBxwkjggcJMwJgiSXA4IkoQOCJOADgiTwA4Ik+wOCJGsEgiTGBIIkkgWCJPgFgiRtBoIkggaCJCAHgiRPCIIk"
    "ognoJJcD6CShA+gk4APoJOsD6CT1A+gkZQToJLsE6CSDBegk7gXoJD4G6CRYBugkFQfoJBAI6CR3Cegk6ApSJZcDUiWhA1Il2wNS"
    "JesDUiX1A1IlYARSJbYEUiV4BVIl3AVSJRgGUiUuBlIlEAdSJdsHUiVSCVIlmAm4JZcDuCWhA7gl2wO4JeYDuCX1A7glWwS4JasE"
    "uCVoBbglzAW4JfMFuCUNBrglCwe4JaUHuCXNCLglKwkiJpcDIiahAyIm2wMiJuYDIib1AyImWwQiJqYEIiZZBSImvAUiJtEFIibu"
    "BSImAAciJnQHIiY/CCImBwmIJpcDiCahA4gmpwOIJtsDiCbmA4gm8AOIJlAEiCahBIgmTgWIJq0FiCa3BYgmzAWIJvsGiCZFB4gm"
    "2weIJucIiCY6C+EmnAPhJqED4SanA+Em2wPhJuYD4SbwA+EmUAThJpwE4SZEBeEmnQXhJqIF4Sa3BeEm9gbhJiAH4SZ+B+EmyAjh"
    "JpQKRyecA0cnoQNHJ6cDRyfbA0cn5gNHJ/ADRydLBEcnkQRHJzkFRyeIBUcnmAVHJ50FRyfrBkcn9gZHJz8HRyeoCEcnEQqtJ5wD"
    "rSehA60npwOtJ9YDrSfmA60n8AOtJ0YErSeMBK0nLwWtJ3MFrSeIBa0n0QatJ+YGrScAB60njgitJ6gJ")
# Ramatlo, Wilke and Loveday (2018), "Development of an optimal piezoelectric transducer to
# excite guided waves in a rail web", NDT&E International (the authors' manuscript at the
# University of Pretoria repository), Fig. 1(a): wavenumber against frequency of the UIC60
# rail, SAFE with four-node elements. The frequencies where its curves meet k = 0 below
# 22.5 kHz, read at 1600 dots per inch from 69.55 px/kHz (to about 0.02 kHz; the second
# near 5.1 kHz runs under the paper's thick highlighted curve and is placed to 0.1 kHz):
RAMATLO_CUTONS = [1.34, 4.04, 5.08, 5.15, 9.80, 9.88, 13.37, 14.14, 15.94, 19.23, 21.77, 22.24]


def _nearest_pairs(a, b):
    """Pair two sorted lists in order (same length), as (a_i, b_i)."""
    return list(zip(sorted(a), sorted(b)))


def branch_k_at(R, name, b, f):
    """The wavenumbers (rad/m) where the sweep's branch b of class `name` has frequency f (Hz)."""
    from scipy.interpolate import CubicSpline
    ks, W = R["br"][name]
    w = W[:, b]
    sp_ = CubicSpline(ks, w)
    wt = 2 * np.pi * f
    out = []
    for i in np.flatnonzero((w[:-1] - wt) * (w[1:] - wt) <= 0):
        out.append(_brentq(lambda k: sp_(k) - wt, ks[i], ks[i + 1], xtol=1e-12))
    return out


def window_branches(key, R):
    """(class, branch, cut-on Hz, name) of every branch drawn."""
    Z = SECTIONS[key]
    brs, _ = curves_of(key, R)
    return [(Z["classes"][r["ci"]][0], r["b"], float(R["cut"][Z["classes"][r["ci"]][0]][r["b"]]), r["nm"]) for r in brs]


def mesh_conv(key, R):
    """The section's mesh against one with elements about half the size: every cut-on
    frequency below fmax, and the frequency of every drawn branch at the wavenumber where
    the page's mesh puts it at fmax; with the elements' size and the shortest wavelength
    at fmax (cached with the sweep)."""
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-{key}-{section_key(key)}-conv2.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    Z = SECTIONS[key]
    fmax = Z["fmax"]
    S, F = make_section(key), make_section(key, 2.0)
    out = {"nel": len(S.elems), "nel_f": len(F.elems), "dof": S.ndof, "dof_f": F.ndof,
           "h": elem_sizes(S), "h_f": elem_sizes(F), "cut": [], "end": []}
    for name in S.classes:
        cs = [x for x in R["cut"][name] if 50 < x < fmax]
        if cs:
            wf = F.omegas(name, 0.0, len(R["cut"][name][R["cut"][name] < fmax])) / (2 * np.pi)
            for x in cs:
                out["cut"].append((name, x, float(wf[np.argmin(abs(wf - x))])))
    for name, b, fc, nm in window_branches(key, R):
        ks = branch_k_at(R, name, b, fmax)
        if not ks:
            continue
        k = max(ks)
        wf = F.omegas(name, k, b + 1)[b] / (2 * np.pi)
        out["end"].append((nm, name, b, k, fmax, float(wf)))
    with open(cache, "wb") as fh:
        pickle.dump(out, fh)
    return out


def conv_lines(key, R, C):
    """The check file's lines on a section's mesh."""
    Z = SECTIONS[key]
    L = []
    p = L.append
    kmax = max(e[3] for e in C["end"])
    lam = 2e3 * np.pi / kmax
    hmax = float(C["h"].max())
    ec = max((abs(f / x - 1) for _, x, f in C["cut"]), default=0.0)
    ee = max(abs(e[5] / e[4] - 1) for e in C["end"])
    top = sorted(C["cut"], key=lambda c: c[1])[-3:]
    if key == "plate":                 # the slice's width is immaterial (its basis ties each depth): the thickness counts
        hmax = PLATE_D / C["nel"]
        p(f"  mesh: {C['nel']} Q9 elements through the {PLATE_D:g} mm thickness ({C['dof']} dof), {hmax:.2f} mm each;"
          f" refined: {C['nel_f']} ({C['dof_f']} dof), {PLATE_D / C['nel_f']:.2f} mm (the 40 mm slice's width is immaterial)")
    else:
        p(f"  mesh: {C['nel']} Q9 elements ({C['dof']} dof), element sides {float(C['h'].min()):.2f} to {hmax:.2f} mm;"
          f" refined: {C['nel_f']} ({C['dof_f']} dof), {float(C['h_f'].min()):.2f} to {float(C['h_f'].max()):.2f} mm")
    p(f"  shortest wavelength at {Z['fmax'] / 1e3:g} kHz: {lam:.1f} mm (k = {kmax:.1f} rad/m), {lam / hmax:.1f} elements"
      f" ({2 * lam / hmax:.0f} nodes) of the largest size across it")
    p(f"  against the refined mesh: every cut-on below {Z['fmax'] / 1e3:g} kHz within {100 * ec:.3f} %, every branch's"
      f" frequency at its wavenumber at {Z['fmax'] / 1e3:g} kHz within {100 * ee:.3f} %")
    if top:
        p("  the highest cut-ons: " + "; ".join(f"{x / 1e3:.3f} kHz (refined {f / 1e3:.3f}, {100 * (x / f - 1):+.3f} %)"
                                               for _, x, f in top))
    worst = max(C["end"], key=lambda e: abs(e[5] / e[4] - 1))
    p(f"  the largest end difference: {worst[0]} at k = {worst[3]:.1f} rad/m: {worst[4] / 1e3:.3f} kHz, refined"
      f" {worst[5] / 1e3:.3f} kHz ({100 * (worst[4] / worst[5] - 1):+.3f} %)")
    return L, dict(lam=lam, hmax=hmax, per=lam / hmax, ec=ec, ee=ee)


def count_line(key, R, ref_cuts, ref_name):
    """Branches below fmax: ours (drawn) against the reference's cut-ons."""
    Z = SECTIONS[key]
    wb = window_branches(key, R)
    nf = sum(1 for w in wb if w[2] < 50)
    ours = sorted(w[2] / 1e3 for w in wb if w[2] >= 50)
    return (f"  branches below {Z['fmax'] / 1e3:g} kHz: {len(wb)} drawn ({nf} from zero frequency, {len(ours)} cutting on);"
            f" {ref_name}: {nf + len(ref_cuts)} ({len(ref_cuts)} cutting on)"), ours


def ref_plate(R):
    L = []
    p = L.append
    Z = SECTIONS["plate"]
    fmax, d = Z["fmax"], PLATE_D / 1e3
    exA, exS = lamb_cutoffs("A", fmax), lamb_cutoffs("S", fmax)
    exSH = [n * sm.C_T / (2 * d) for n in range(1, 40) if n * sm.C_T / (2 * d) < fmax]
    p(f"THE PLATE: steel, {PLATE_D:g} mm thick, infinite width; f d to {fmax * d / 1e3:.2f} MHz mm")
    p("  The SAFE slice (40 mm, its basis tying every node of one depth) has free faces at z = +-5 mm and no edges:")
    p("  Lamb waves (u_x, u_z) and shear horizontal waves (u_y) of the infinite plate, each family on its own basis.")
    p("  REFERENCE: the exact Rayleigh-Lamb equations (symmetric and antisymmetric, solved here by sign changes")
    p("  and Brent) and the SH dispersion w^2 = c_T^2 (k^2 + (n pi/d)^2), independent of SAFE.")
    p(f"  exact cut-ons below {fmax / 1e3:g} kHz: antisymmetric Lamb " + ", ".join(f"{x / 1e3:.3f}" for x in exA) +
      " kHz (f d = c_T/2), symmetric Lamb " + (", ".join(f"{x / 1e3:.3f}" for x in exS) or "none (S1 at c_L/2d = "
                                                + f"{sm.C_L / (2 * d) / 1e3:.1f} kHz)") +
      ", SH " + ", ".join(f"{x / 1e3:.3f}" for x in exSH) + " kHz")
    line, ours = count_line("plate", R, exA + exS + exSH, "exact Lamb and SH")
    p(line + "; the drawn: " + ", ".join(w[3] for w in window_branches("plate", R)))
    S = make_section("plate")
    errs = []
    for name, b, fc, nm in window_branches("plate", R):
        ks, W = R["br"][name]
        for f in np.linspace(max(fc, 1e3) * 1.05, fmax * .98, 4):
            kk = branch_k_at(R, name, b, f)
            if not kk:
                continue
            k = kk[-1]
            w = S.omegas(name, k, b + 1)[b]
            if name.startswith("SH"):
                n_ = 2 * b + (name == "SHa")
                ex = sm.C_T * np.hypot(k, n_ * np.pi / d)
            else:
                ex = lamb_root_near(name, k, w)
            errs.append((nm, f, k, w, ex))
    e = max(abs(w / ex - 1) for _, _, _, w, ex in errs if ex)
    p(f"  SAFE against the exact roots at {len(errs)} points along the five branches: max |w_SAFE/w_exact - 1| = {e:.1e}")
    for nm, f, k, w, ex in errs[::4]:
        p(f"    {nm:9s} k = {k:7.2f} rad/m: SAFE {w / 2e3 / np.pi:9.4f} kHz, exact {ex / 2e3 / np.pi:9.4f} kHz, c_p {w / k:7.1f} m/s")
    # group velocities, exact (central difference of the exact roots) and SAFE
    cases = [("A", 0, 50e3), ("A", 0, 150e3), ("S", 0, 200e3), ("A", 1, 230e3)]
    for fam, b, f in cases:
        k = branch_k_at(R, fam, b, f)[-1]
        w = S.omegas(fam, k, b + 1)[b]
        h = 1e-4 * k
        cg_ex = (lamb_root_near(fam, k + h, w) - lamb_root_near(fam, k - h, w)) / (2 * h)
        _, V = S.solve(fam, k, b + 1)
        v = V[:, b]
        cg_s = (v @ (S.K2 @ v) + 2 * k * (v @ (S.K3 @ v))) / (2 * w * (v @ (S.M @ v)))
        p(f"    {fam}{b} at {f / 1e3:g} kHz: c_p {w / k:7.1f} m/s (exact {lamb_root_near(fam, k, w) / k:7.1f}), c_g SAFE"
          f" {cg_s:7.1f}, exact {cg_ex:7.1f} m/s")
    p("  S0 at k -> 0 tends to the plate speed sqrt(E/(rho (1 - nu^2))) = "
      f"{np.sqrt(sm.E / (sm.RHO * (1 - sm.NU ** 2))):.1f} m/s, A0 to sqrt(w) (D/rho d)^(1/4) (checked below).")
    p("")
    return dict(lines=L, nref=3 + len(exA + exS + exSH))


def ref_pipe(R):
    L = []
    p = L.append
    Z = SECTIONS["pipe"]
    fmax = Z["fmax"]
    a, b_ = PIPE["ri"] / 1e3, PIPE["ro"] / 1e3
    p(f"THE PIPE: NPS 1 1/4 schedule 40 (ASME B36.10M): OD {2 * PIPE['ro']:.2f} mm, wall {PIPE['ro'] - PIPE['ri']:.2f} mm")
    p("  REFERENCE: the exact solution of Gazis (1959) for the free hollow cylinder, solved here independently of")
    p("  SAFE: at k = 0 the harmonic n splits into axial shear (J_n'(be a) Y_n'(be b) = J_n'(be b) Y_n'(be a)) and")
    p("  plane strain (a 4 x 4 Bessel determinant; for n = 0 the radial and the torsional 2 x 2); at k > 0 the full")
    p("  6 x 6 determinant of the three potentials, made real, its roots by sign changes and Brent.")
    ex = {}
    for name, typ, n in Z["classes"]:
        if name == "L0":
            ex[name] = cyl_cutoffs(0, fmax, a, b_, "phi") + cyl_cutoffs(0, fmax, a, b_, "shear")
        elif name == "V0":
            ex[name] = cyl_cutoffs(0, fmax, a, b_, "psi")
        else:
            ex[name] = cyl_cutoffs(n, fmax, a, b_, "plane") + cyl_cutoffs(n, fmax, a, b_, "shear")
    allex = sorted(x for v in ex.values() for x in v)
    line, ours = count_line("pipe", R, allex, "exact (Gazis)")
    p(line)
    worst = 0.0
    for name, typ, n in Z["classes"]:
        sf = [x for x in R["cut"][name] if 50 < x < fmax]
        xs = sorted(ex[name])
        if not sf and not xs:
            continue
        pairs = list(zip(sorted(sf), xs))
        worst = max([worst] + [abs(s_ / x - 1) for s_, x in pairs])
        lab = {"L0": "L(0,m)", "V0": "T(0,m)"}.get(name, f"F({n},m)")
        p(f"    {lab:7s} exact " + ", ".join(f"{x / 1e3:.3f}" for x in xs) + " kHz; SAFE " +
          ", ".join(f"{s_ / 1e3:.3f}" for s_ in sorted(sf)) + (" (same count)" if len(sf) == len(xs) else " (COUNTS DIFFER)"))
    p(f"  every cut-on: max |f_SAFE/f_exact - 1| = {worst:.1e}")
    S = make_section("pipe")
    errs = []
    for name, b, fc, nm in window_branches("pipe", R):
        n = 0 if name in ("L0", "V0") else int(name[1:])
        if name == "V0" and b == 0:
            continue                               # T(0,1): w = c_T k exactly (beta = 0 makes the determinant degenerate)
        for f in (max(fc, 1e3) * 1.1 + (fmax - max(fc, 1e3) * 1.1) * q for q in (.25, .75)):
            kk = branch_k_at(R, name, b, f)
            if not kk:
                continue
            k = kk[-1]
            w = S.omegas(name, k, b + 1)[b]
            r = gazis_root_near(n, k, w, a, b_)
            errs.append((nm, k, w, r))
    good = [e for e in errs if e[3]]
    e = max(abs(w / r - 1) for _, _, w, r in good)
    p(f"  SAFE against Gazis's roots at {len(good)} points (two on each drawn branch but T(0,1)): max |w_SAFE/w_exact - 1| = {e:.1e}"
      + ("" if len(good) == len(errs) else f"; {len(errs) - len(good)} points without a root nearby"))
    for nm, k, w, r in good[::6]:
        p(f"    {nm:42s} k = {k:7.2f} rad/m: SAFE {w / 2e3 / np.pi:9.4f} kHz, exact {r / 2e3 / np.pi:9.4f} kHz")
    w1 = S.omegas("V0", 100.0, 1)[0]
    p(f"  T(0,1): c_p = {w1 / 100:.4f} m/s at k = 100 rad/m, c_T = {sm.C_T:.4f} m/s exactly ({w1 / 100 / sm.C_T - 1:+.1e})")
    p("")
    return dict(lines=L, nref=3 + len(allex))


def bar_nu03():
    """The square bar's branches at Hayashi's Poisson ratio 0.3 (E and rho as the steel's: the curves in
    f h/c_T and c/c_T depend on nu alone), to f h/c_T = 1.7 (cached)."""
    cache = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-bar-nu03-{section_key('bar')}.pkl")
    if os.path.exists(cache):
        with open(cache, "rb") as fh:
            return pickle.load(fh)
    nu = 0.3
    mu = sm.E / (2 * (1 + nu)); lam_ = sm.E * nu / ((1 + nu) * (1 - 2 * nu))
    ct = np.sqrt(mu / sm.RHO)
    S = Section(*bar_mesh(), D=_dmat(lam_, mu))
    for c in SECTIONS["bar"]["classes"]:
        S.classes[c[0]] = S.mirror_basis(*c[1:])
    h = SQ / 1e3
    fm = 1.7 * ct / h
    out = {"ct": ct, "br": {}, "cut": {}}
    for name in S.classes:
        fc = S.omegas(name, 0.0, 30) / (2 * np.pi)
        out["cut"][name] = fc
        n = int(np.sum(fc < fm))
        if n:
            out["br"][name] = branches_g(S, name, n, kmax_of(S, fm), fm)
    with open(cache, "wb") as fh:
        pickle.dump(out, fh)
    return out


def ref_bar(R):
    from scipy.optimize import minimize_scalar
    L = []
    p = L.append
    Z = SECTIONS["bar"]
    fmax, h = Z["fmax"], SQ / 1e3
    ct = sm.C_T
    p(f"THE BAR: square steel bar {SQ:g} x {SQ:g} mm; f h to {fmax * h / 1e3 * 1e3:,.0f} kHz mm")
    p("  The square's symmetry, C4v, splits it into five classes: A1 (axial), B1, E (each bending pair once: the")
    p("  class symmetric about y = 0 and antisymmetric about z = 0), A2 (torsional) and B2, each solved on its own")
    p("  orthonormal basis (the projector of the class on each orbit's displacements). Modes of different classes")
    p("  cross freely; within a class they repel, so the frequency-ordered eigenvalues are the curves.")
    ap = lambda m, n: ct / (2 * h) * np.hypot(m, n)
    exact = [(f"anti-plane shear ({m}, {n}), c_T/(2h) sqrt(m^2 + n^2)", ap(m, n)) for m, n in
             ((1, 0), (1, 1), (2, 0), (2, 1), (2, 2), (3, 0)) if ap(m, n) < fmax]
    exact += [(f"Lame mode {m}, m c_T/(sqrt(2) h)", m * ct / (np.sqrt(2) * h)) for m in (1, 2) if m * ct / (np.sqrt(2) * h) < fmax]
    allcut = sorted(x for c in R["cut"] for x in R["cut"][c] if 50 < x < fmax * 1.2)
    p("  exact cut-ons (k = 0) against SAFE:")
    for lab, fe in exact:
        fs = min(allcut, key=lambda x: abs(x - fe))
        p(f"    {lab}: exact {fe / 1e3:.4f} kHz, SAFE {fs / 1e3:.4f} kHz ({fs / fe - 1:+.1e})")
    # Hayashi, Kawashima and Rose (2004)
    q = np.frombuffer(base64.b64decode("".join(HAYASHI_SQUARE)), "<i2").reshape(-1, 2).astype(float)
    FH, CC = q[:, 0] / 2, q[:, 1] / 1000
    B03 = bar_nu03()
    cth = B03["ct"]
    curves = []
    for name, (ks, W) in B03["br"].items():
        for b in range(W.shape[1]):
            curves.append((name, b, B03["cut"][name][b], W[:, b] / (2 * np.pi) * h / cth, W[:, b] / ks / cth))
    bend = next(cv for cv in curves if cv[0] == "vertical" and cv[1] == 0)
    sel = (CC < 0.85) & (FH < 1500)
    order = np.argsort(bend[3])
    cost = lambda cT: np.sum((np.interp(FH[sel] / cT, bend[3][order], bend[4][order]) - CC[sel]) ** 2)
    r = minimize_scalar(cost, bounds=(2500, 4000), method="bounded")
    cTH = r.x
    XM = 5100.0 / cTH                  # their axis, in f h / c_T

    def near(xd, yd):
        best, which = np.inf, None
        for i, (name, b, fc, x, y) in enumerate(curves):
            m = (y < 3.6) & (x < 1.15 * XM)
            if m.sum() < 2:
                continue
            P_ = np.column_stack([x[m] / XM, y[m] / 3.0])
            A_, B_ = P_[:-1], P_[1:]
            AB = B_ - A_
            t_ = np.clip(((np.array([xd / XM, yd / 3.0]) - A_) * AB).sum(1) / ((AB ** 2).sum(1) + 1e-30), 0, 1)
            dd = np.sqrt((((A_ + t_[:, None] * AB) - np.array([xd / XM, yd / 3.0])) ** 2).sum(1)).min()
            if dd < best:
                best, which = dd, i
        return best, which
    res = [near(FH[i] / cTH, CC[i]) for i in range(len(FH))]
    dd = np.array([x[0] for x in res]); wh = np.array([x[1] for x in res])
    tol = 0.012
    p("  PUBLISHED: Hayashi, Kawashima and Rose (2004), Key Eng. Mater. 270-273, 410-415, Fig. 2: the phase")
    p("  velocity of a square rod h x h by SAFE (12 x 12 elements, Poisson's ratio 0.3), c/c_T to 3 against f h to")
    p("  5,000 kHz mm; its 765 dots read from the paper's vector drawing. Here the same square at nu = 0.3, in the")
    p("  same normalized axes. The paper does not give c_T: fitted on the bending branch's dots below c/c_T = 0.85")
    p(f"  and f h = 1,500 kHz mm alone ({sel.sum()} dots): c_T = {cTH:.0f} m/s, rms {np.sqrt(r.fun / sel.sum()):.4f} in c/c_T.")
    p(f"  Every one of the 765 dots against our nearest curve (in the plot's units: f h over the 5,100 kHz mm axis,")
    p(f"  c/c_T over 3): median {np.median(dd):.4f}, 95 % {np.percentile(dd, 95):.4f}, largest {dd.max():.4f}; the dots"
      f" themselves are 0.008 across.")
    # the count: at each frequency of the paper's (its dots lie on a grid in f h, one a curve), its dots
    # under c/c_T = 3 against our curves there (the same square at nu = 0.3, in the same axes)
    def ours_at(x):
        n = 0
        for (name, b, fc, X, Y) in curves:
            o = np.argsort(X)
            if X[o][0] <= x <= X[o][-1] and np.interp(x, X[o], Y[o]) <= 3.0:
                n += 1
        return n
    tab = [(g, int(np.sum((FH == g) & (CC <= 3.0))), ours_at(g / cTH)) for g in np.unique(FH)]
    same = sum(1 for _, a, b in tab if a == b)
    lead = [(g, a, b) for g, a, b in tab if b > a]
    trail = [(g, a, b) for g, a, b in tab if b < a]
    xw = fmax * h / ct                                   # our window's end, in f h/c_T
    # each level n of the count: from which of the paper's frequencies ours holds n branches on, and the
    # paper's dots (three frequencies running: a stray dot, as at 398 kHz mm, does not count)
    def first(col, n):
        return next((tab[i][0] for i in range(len(tab) - 2) if min(tab[i + j][col] for j in range(3)) >= n), None)
    lags = []
    for n in range(4, ours_at(xw) + 1):
        go, gp = first(2, n), first(1, n)
        if go and gp:
            lags.append(gp / go - 1)
    p(f"  THE COUNT: at each of the paper's {len(tab)} frequencies (its dots lie on a grid of about 51 kHz mm, one on each")
    p(f"  curve under c/c_T = 3), its dots against our curves at the same f h/c_T: the same at {same}; ours one or more")
    p(f"  ahead at {len(lead)}, behind at {len(trail)}. Up to our window, each new branch appears in the paper's dots {100 * min(lags):.0f} to")
    p(f"  {100 * max(lags):.0f} % higher in f h than in ours (median {100 * float(np.median(lags)):.1f} %), as from a stiffer mesh (12 x 12 elements;")
    p("  the rail's published four-node elements do the same), so the counts part for a few of its frequency steps")
    p("  after each branch enters and agree between. The paper's frequencies nearest our window's end:")
    near_w = sorted(tab, key=lambda r: abs(r[0] / cTH - xw))[:5]
    for g, a, b in sorted(near_w):
        p(f"    f h {g:5.0f} kHz mm (f h/c_T = {g / cTH:.3f}): the paper {a:2d} curves, ours {b:2d}")
    wb = window_branches("bar", R)
    pub = [a for g, a, b in sorted(near_w, key=lambda r: abs(r[0] / cTH - xw))[:2]]
    p(f"  OUR WINDOW ends at {fmax / 1e3:g} kHz (f h/c_T = {xw:.3f}; the paper's f h {xw * cTH:,.0f} kHz mm by its c_T), in the widest")
    p(f"  stretch where the paper's figure and ours hold the same number of branches: {len(wb)} (the paper's dots at its two")
    p(f"  nearest frequencies: {pub[0]} and {pub[1]}). Our figure (steel, nu = {sm.NU}, c_p up to {CP_MAX / 1e3:g} km/s): {len(wb)} branches,")
    p(f"  {sum(1 for w in wb if w[2] < 50)} from zero frequency (bending, axial, torsional), the rest cutting on at")
    p("    " + ", ".join(f"{w[2] / 1e3:.2f}" for w in sorted(wb, key=lambda w: w[2]) if w[2] >= 50) + " kHz")
    late = sorted((float(x), c) for c in R["cut"] for x in R["cut"][c] if 50 < x < fmax and
                  not any(abs(x - w[2]) < 1 for w in wb if w[0] == c))
    if late:
        p(f"  ({len(late)} more cut on below {fmax / 1e3:g} kHz, at " + ", ".join(f"{x / 1e3:.2f}" for x, _ in late) + " kHz, but their phase")
        p("  velocity stays above the window until past its end: they are not drawn and carry no cut-on mark, as the")
        p("  paper's figure has them only above its c/c_T = 3 there)")
    p("")
    nref = pub[0] if pub[0] == pub[1] else None
    return dict(lines=L, nref=nref, cTH=cTH, med=float(np.median(dd)), mx=float(dd.max()))


def ref_rail(R):
    L = []
    p = L.append
    Z = SECTIONS["rail"]
    fmax = Z["fmax"]
    P = R["props"]
    p("THE RAIL: 60E1 (UIC60), EN 13674-1, 60.21 kg/m: height 172 mm, foot 150 mm, head 72 mm, web 16.5 mm")
    p("  Its outline: the profile's standard drawing (the WirthRail 60E1 data sheet's vector outline, scaled to")
    p("  172 mm and 150 mm): R2 and R4 at the foot's tip, the foot's top at 1:14 and 1:2.75 joined by R40, R35 and R7")
    p("  into the web's R120 flanks, R7 and the 1:2.75 underside of the head, R3, the head's 1:20 side, R13, R80, R300.")
    p(f"  section (Gauss on the mesh): A = {P['A']:.1f} mm^2 (EN 13674-1: {RAIL_STD['A']:.0f}, {P['A'] / RAIL_STD['A'] - 1:+.2%}),"
      f" centroid {P['zc'] + 86:.2f} mm over the foot ({RAIL_STD['zc']}), I_y = {P['Iy'] / 1e4:.1f} cm^4"
      f" ({RAIL_STD['Iy'] / 1e4:.1f}, {P['Iy'] / RAIL_STD['Iy'] - 1:+.2%}), I_z = {P['Iz'] / 1e4:.1f} cm^4"
      f" ({RAIL_STD['Iz'] / 1e4:.1f}, {P['Iz'] / RAIL_STD['Iz'] - 1:+.2%}); mass {P['A'] * sm.RHO / 1e6:.2f} kg/m")
    p("  PUBLISHED: Ramatlo, Wilke and Loveday (2018), NDT&E International, Fig. 1(a): the UIC60 rail's wavenumber")
    p("  against frequency to 60 kHz, SAFE with four-node elements. The frequencies where its curves meet k = 0,")
    p(f"  read from the figure (to about 0.02 kHz), below {fmax / 1e3:g} kHz:")
    line, ours = count_line("rail", R, RAMATLO_CUTONS, "Ramatlo et al.")
    p(line)
    pairs = _nearest_pairs(ours, RAMATLO_CUTONS)
    p("  paired in order (ours, theirs, difference): " + "; ".join(f"{a:.2f}, {b:.2f} ({a / b - 1:+.1%})" for a, b in pairs))
    dev = [a / b - 1 for a, b in pairs]
    p(f"  ours lie {-max(dev):.1%} to {-min(dev):.1%} under theirs (mean {-np.mean(dev):.1%}): linear four-node elements are stiffer than")
    p("  quadratic ones and raise every frequency; the count and the order are the same. Their next cut-on, 23.67 kHz")
    p(f"  (ours {sorted(x for c in R['cut'] for x in R['cut'][c] if x > fmax)[0] / 1e3:.2f}), lies above the window.")
    p("")
    return dict(lines=L, nref=4 + len(RAMATLO_CUTONS))


def ref_ibeam(R):
    L = []
    p = L.append
    P, T = R["props"], R["tors"]
    G = IPE80
    p(f"THE I-BEAM: IPE 80 (EN 10365): h {G['h']:g} mm, b {G['b']:g} mm, web {G['tw']:g} mm, flanges {G['tf']:g} mm, root radius {G['r']:g} mm")
    p(f"  section (Gauss on the mesh): A = {P['A']:.1f} mm^2 (tables {IPE80_STD['A']:.0f}), I_y = {P['Iy'] / 1e4:.2f} cm^4"
      f" ({IPE80_STD['Iy'] / 1e4:.2f}), I_z = {P['Iz'] / 1e4:.3f} cm^4 ({IPE80_STD['Iz'] / 1e4:.2f}); Saint-Venant"
      f" J = {T['J'] / 1e4:.3f} cm^4 (the tables' I_t {IPE80_STD['It'] / 1e4:.2f}, from a thin-walled")
    p(f"  formula with fillet terms), warping constant {T['Gamma'] / 1e6:.1f} cm^6 (the tables' I_w {IPE80_STD['Iw'] / 1e6:.0f},"
      " the flanges' I_z (h - t_f)^2/4)")
    p("  PUBLISHED: no dispersion curves of an IPE 80 (or another standard I-section) were found. The reference is")
    p("  independent and computed here: the same section meshed with elements of half the size (MESH below), and")
    p("  beam theory at low wavenumber (Euler-Bernoulli bending in both planes, the rod, Vlasov torsion).")
    wb = window_branches("ibeam", R)
    p(f"  branches below {SECTIONS['ibeam']['fmax'] / 1e3:g} kHz: {len(wb)}, {sum(1 for w in wb if w[2] < 50)} from zero"
      " frequency, the rest cutting on at " + ", ".join(f"{w[2] / 1e3:.2f}" for w in sorted(wb, key=lambda w: w[2]) if w[2] >= 50) + " kHz")
    p("")
    return dict(lines=L, nref=None)


# ================================================================ group velocity
def group_near(model, name, k, w0, tol=1e-4):
    """(w, c_g) of the eigenpair nearest w0 (rad/s), by sparse shift-invert."""
    if not hasattr(model, "_group_sparse"):
        model._group_sparse = {}
    if name not in model._group_sparse:
        Q = model.classes[name]
        model._group_sparse[name] = tuple((Q.T @ A @ Q).tocsc() for A in (model.K1, model.K2, model.K3, model.M))
    K1, K2, K3, M = model._group_sparse[name]
    K = (K1 + k * K2 + (k * k) * K3).tocsc()
    # Avoid a singular factorization when the requested shift is itself exact
    # (notably the pipe's nondispersive torsional branch).
    vals, vecs = spla.eigsh(K, k=1, M=M, sigma=w0 * w0 * (1 + 1e-8), which="LM")
    x, w = vecs[:, 0], np.sqrt(vals[0])
    if abs(w / w0 - 1) > tol:
        raise RuntimeError(f"group_near: {name} k = {k}: found {w}, wanted {w0}")
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
    """The page's kAtF: the wavenumber of f (kHz) on a laid-out curve, by straight lines in f;
    where f is met twice (a backward wave), the last crossing, as the page."""
    K, F, _ = curve
    if np.all(np.diff(F) > 0):
        return float(np.interp(f, F, K))
    best = None
    for i in range(len(F) - 1):
        if F[i] != F[i + 1] and (F[i] - f) * (F[i + 1] - f) <= 0:
            k = K[i] + (K[i + 1] - K[i]) * (f - F[i]) / (F[i + 1] - F[i])
            best = k if best is None else max(best, k)
    return float(best)


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
SIG_PW = np.sqrt(1 / 32 - 1 / (4 * np.pi ** 2) + 1 / (64 * np.pi ** 2)) / np.sqrt(3 / 8)   # the rms width of E^2 over the envelope's width


def fastest(Rs):
    """The fastest packet anywhere: the travelling point inside a window with the largest slope,
    then its exact c_g there (group_near). Returns (c_g km/s, section key, branch name, f kHz)."""
    best = (0, None)
    for key in ORDER:
        brs, tflat, _ = thinned(key, Rs[key])
        for r in brs:
            o, n = r["o"], r["n"]
            tf, tc, tg = (np.asarray(tflat[o + j * n:o + (j + 1) * n], np.float64) for j in range(3))
            for i in np.flatnonzero((tf <= SECTIONS[key]["fmax"] / 1e3) & (tc <= CP_MAX / 1e3)):
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
    sqrt(1 + (w'' D / (2 c_g sigma^2))^2), w'' = dc_g/dk by a central difference, D = L + pw of
    the section. {key: [stop: {"w1": st, "wa": st, "w2": st}]}, st = (f kHz, c_p, c_g km/s, k rad/m, widening)."""
    out = {}
    for key in ORDER:
        S, Z = make_section(key), SECTIONS[key]
        G = Z["strip"]
        sig = SIG_PW * G["pw"] / 1e3
        tb, curves = page_curve(key, Rs[key])
        brs, flat = curves_of(key, Rs[key])
        stops = []
        for s in tour_of(key, brs, flat):
            row = {}
            for lab, bi, f in (("w1", s["b1"], s["f1"]), ("wa", s["b2"], s["fa"]), ("w2", s["b2"], s["f2"])):
                name = Z["classes"][tb[bi]["ci"]][0]
                k = k_at_f(curves[bi], f)
                # Identify the branch by its eigenvalue index, then use its
                # exact eigenfrequency as the shift instead of a linear seed.
                branch = tb[bi]["b"]
                exact_w = S.omegas(name, k, branch + 1)[branch]
                w, cg = group_near(S, name, k, exact_w)
                h = 1e-3 * k
                gp = group_near(S, name, k + h, w + cg * h)[1]
                gm = group_near(S, name, k - h, w - cg * h)[1]
                wpp = (gp - gm) / (2 * h)
                wid = np.sqrt(1 + (wpp * (G["L"] + G["pw"]) / 1e3 / (2 * cg * sig ** 2)) ** 2)
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
        P, T = Rs[key]["props"], Rs[key]["tors"]
        kap = 10 * (1 + sm.NU) / (12 + 11 * sm.NU) if key == "bar" else None
        # (the plate's A0 at k of 1 or 2 rad/m: w^2 some 1e-11 of its stiffness's scale, round-off decides it)
        ks = (1.0, 2.0, 5.0, 10.0, 20.0) if key == "bar" else (5.0, 10.0, 20.0) if key == "plate" else (1.0, 2.0, 5.0)
        p(f"  {Z['label']}:")
        for k in ks:
            if key == "plate":
                d = PLATE_D / 1e3
                D_ = sm.E * d ** 3 / (12 * (1 - sm.NU ** 2))
                rows = [("vertical", "plate bending 2 sqrt(D/(rho d)) k", 2 * k * np.sqrt(D_ / (sm.RHO * d))),
                        ("axial", "plate speed sqrt(E/(rho (1 - nu^2)))", np.sqrt(sm.E / (sm.RHO * (1 - sm.NU ** 2)))),
                        ("lateral", "SH0: c_T", sm.C_T)]
            else:
                ref = group_closed(k, P, T, kap=kap)
                rows = [("vertical", "Euler-Bernoulli (2 c_p)", ref["vertical_EB"])]
                if key == "bar":
                    rows += [("vertical", "Timoshenko", ref["vertical_Timo"])]
                elif key in ("ibeam", "rail"):
                    rows += [("lateral", "Euler-Bernoulli (2 c_p), I_z", ref["lateral_EB"])]
                rows += [("axial", "rod c_0", ref["axial_rod"]), ("axial", "Love rod", ref["axial_Love"])]
                if key == "pipe":
                    rows += [("torsional", "T(0,1): c_T", sm.C_T)]
                elif key == "ibeam":
                    rows += [("torsional", "Vlasov, + E Gamma k^2", ref["torsional_Vlasov"])]
                else:
                    rows += [("torsional", "Saint-Venant sqrt(GJ/(rho I_p))", ref["torsional_SV"])]
            got = {}
            for typ, lab, c in rows:
                name, b = Z["fund"][typ]
                if typ not in got:                  # shift-invert from the dense solve's w, accurate at small w
                    w, cg = group_near(S, name, k, S.omegas(name, k, b + 1)[b], tol=1e-3)
                    h = .01                         # rad/m: the round-off of w and the difference's own error balance there
                    got[typ] = (cg, (group_near(S, name, k + h, w + cg * h, tol=1e-2)[0] - group_near(S, name, k - h, w - cg * h, tol=1e-2)[0]) / (2 * h))
                cg, fd = got[typ]
                p(f"  {k:6.1f}   {typ:10s} {cg:13.3f}   {fd - cg:+.1e}      {lab:36s} {c:9.3f}   {cg / c - 1:+.2e}")
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
            kin = K[(tf <= Z["fmax"] / 1e3) & (tc <= CP_MAX / 1e3)]
            name = Z["classes"][r["ci"]][0]
            for k in np.linspace(kin.min(), kin.max(), 12)[1:-1]:
                i = min(max(int(np.searchsorted(K, k, side="right")) - 1, 0), len(K) - 2)
                h, s_ = K[i + 1] - K[i], (k - K[i]) / (K[i + 1] - K[i])
                herm = ((6 * s_ * s_ - 6 * s_) * Wk[i] + (6 * s_ - 6 * s_ * s_) * Wk[i + 1]) / h + (3 * s_ * s_ - 4 * s_ + 1) * tg[i] + (3 * s_ * s_ - 2 * s_) * tg[i + 1]
                w0 = 1e3 * _herm(K[i], Wk[i], tg[i], K[i + 1], Wk[i + 1], tg[i + 1], k)     # rad/s
                cg = group_near(S, name, k, w0)[1]
                if abs(herm * 1e3 / cg - 1) > e:
                    e, where = abs(herm * 1e3 / cg - 1), f"{r['nm']}, {w0 / 2e3 / np.pi:.1f} kHz"
        worst[key] = (e, where)
    p("  The travelling curves carry slopes too (the spline's, for the cubic Hermite that draws them), but")
    p("  not to this accuracy: along every branch inside the window, 10 states each, their slope against")
    p("  the exact c_g: " + "; ".join(f"{SECTIONS[k]['label']} {worst[k][0]:.1e} ({worst[k][1]})" for k in ORDER) + ".")
    p("  The worst lie at veerings, where two branches of a class nearly touch and c_g turns within a")
    p("  fraction of a kHz. So the waves never use them: c_g always comes from a solved state.")
    # the glides: the page's integration rule on the travelling curve's rates
    p(f"  The tour's glides: wave 2's rates (envelope speed and centre phase rate, from c_g and k) at {TOUR_T['NG'] + 1}")
    p("  moments evenly spread over the 8 s glide, each interval integrated as the cubic through its four nearest")
    p(f"  (the page's rule), against Simpson on {4 * TOUR_T['NG'] + 1} moments; the rates here from the travelling curve (the")
    p("  rule is what is checked). The page's own rates are exact: each moment's c_g computed here by shift-invert on")
    p("  the same model at the wavenumber the page takes (glide_rates) and carried with the section, so that a stop")
    p(f"  begins without solving {TOUR_T['NG'] + 1} states; the wave drawn at each moment is still solved in the page.")
    p("  Largest difference in the envelope's travel over a glide (mm of the page) and in the phase at its centre (rad):")
    from scipy.integrate import simpson
    for key in ORDER:
        Z = SECTIONS[key]
        slow = Z["strip"]["slow"]
        tb, curves = page_curve(key, Rs[key])
        tb2, tflat, _ = thinned(key, Rs[key])
        brs, flat = curves_of(key, Rs[key])
        dx = dp = tot = 0.0
        for s_ in tour_of(key, brs, flat):
            r = tb2[s_["b2"]]
            o, n = r["o"], r["n"]
            tf, tc, tg = (np.asarray(tflat[o + j * n:o + (j + 1) * n], np.float64) for j in range(3))
            Kt, Wt = 2 * np.pi * tf / tc, 2e3 * np.pi * tf
            cv = curves[s_["b2"]]
            N = 4 * TOUR_T["NG"]
            v, rr = [], []
            for j in range(N + 1):
                k = k_at_f(cv, s_["fa"] if j == 0 else s_["f2"] if j == N else s_["fa"] + (s_["f2"] - s_["fa"]) * ease_in_out(j / N))
                i = min(max(int(np.searchsorted(Kt, k, side="right")) - 1, 0), len(Kt) - 2)
                h, q = Kt[i + 1] - Kt[i], (k - Kt[i]) / (Kt[i + 1] - Kt[i])
                cg = ((6 * q * q - 6 * q) * Wt[i] + (6 * q - 6 * q * q) * Wt[i + 1]) / h + 1e3 * ((3 * q * q - 4 * q + 1) * tg[i] + (3 * q * q - 2 * q) * tg[i + 1])
                w = _herm(Kt[i], Wt[i], 1e3 * tg[i], Kt[i + 1], Wt[i + 1], 1e3 * tg[i + 1], k)
                v.append(cg * 1e3 / slow)
                rr.append((k * cg - w) / slow)
            for y, acc in ((v, "x"), (rr, "p")):
                d_ = abs(glide_integral(y[::4], TOUR_T["TGD"]) - simpson(y, dx=TOUR_T["TGD"] / N))
                if acc == "x":
                    dx, tot = max(dx, d_), max(tot, simpson(y, dx=TOUR_T["TGD"] / N))
                else:
                    dp = max(dp, d_)
        p(f"    {Z['label']:7s} {dx:.1e} mm (of up to {tot:.0f} mm travelled in a glide), {dp:.1e} rad")
    # the tours' c_g, and what the rigid envelope leaves out
    p("  The spreading left out: the envelope rides at c_g unchanged (the first order in the burst's")
    p(f"  bandwidth). A Gaussian burst of the packet's rms width ({100 * SIG_PW:.1f} % of its envelope's) would widen over one")
    p("  passage (D = L + pw of its section) by sqrt(1 + (w'' D / (2 c_g sigma^2))^2), w'' = dc_g/dk: at the tours' states")
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
                                  " return q.mk[0] > .35 && q.mk[1] > .35 ? (() => { const p = markerLabels(markerPos(LAST, q, false, 1)); return Math.hypot(p[0].x-p[1].x, p[0].y-p[1].y); })() : 99; })()")
                if gap < 21:
                    lab = lab + [["marker 1", "marker 2", round(gap, 1), 0]]
                wp = pg.evaluate("footW(CUR)")
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


STR_YC = (612, 778)   # the page's waveguides' centre lines (FIGURE's STR.yc); scale, end and view are the section's T


def _outline(img, w, sc, T, m):
    """Beam w's top outline in a canvas image of sc pixels a drawing unit: per pixel column over
    the beam, the upper boundary of the first ink met from the white above, to a fraction of a
    pixel by the ink's coverage (the rows it partly covers, summed up to the first it covers
    wholly: exact for an edge smoothed by area), searched from 20 units over the top-back node's
    rest line to 14 under it (the drawn displacement is 11 units at most). The columns start 40
    units in from the left end, past its slanting top face."""
    ink = 0.2126 * 0x27 + 0.7152 * 0x22 + 0.0722 * 0x1C
    Lum = img[..., :3].astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    cov = np.clip((255 - Lum) / (255 - ink), 0, 1)
    top = STR_YC[w] - T["s"] * (m["z"] + m["e"] * T["sd"])
    r0, r1 = int((top - 20) * sc), int((top + 14) * sc)
    X, Y = [], []
    for c in range(int((T["x1"] - T["s"] * T["L"] + 40) * sc), int((T["x1"] - 8) * sc)):
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


def _outline_model(X, Y, m, sc, T):
    """The misfit of an outline (X, Y pixels) to the one the page draws: the top-back node's path
    along the beam by stripView's own formulas (its U, the drawn scale g, the samples 1 mm apart
    joined by straight lines) with the packet centred at p[0] (mm) and the phase p[1] at its centre,
    moved down by p[2] pixels (the ink's half width and the threshold)."""
    x = np.linspace(-T["L"], 0.0, 413)               # the page's samples (NXS)
    CD, SD, PW, s, x1 = T["cd"], T["sd"], T["pw"], T["s"], T["x1"]

    def resid(p):
        xi = x - p[0]
        E = np.where(np.abs(xi) < PW / 2, np.cos(np.pi * xi / PW) ** 2, 0.0)
        cs, sn = E * np.cos(m["k"] * xi + p[1]), E * np.sin(m["k"] * xi + p[1])
        d = m["e"] + m["g"] * m["u"][1] * cs
        Xp = sc * (x1 + s * (x - m["g"] * m["u"][0] * sn + d * CD))
        Yp = sc * (m["yc"] - s * (m["z"] + m["g"] * m["u"][2] * cs + d * SD))
        return np.interp(X, Xp, Yp) + p[2] - Y
    return resid


def _fit_outline(X, Y, m, sc, T):
    """One moment's packet from its outline: the centre from _fit_packet, the phase the best of 16,
    then _outline_model's misfit least squared. Returns (Xc mm, psi, rms residual in pixels)."""
    from scipy.optimize import least_squares
    resid = _outline_model(X, Y, m, sc, T)
    xc = (_fit_packet(X, Y, m["k"] / (T["s"] * sc), T["pw"] * T["s"] * sc)[0] / sc - T["x1"]) / T["s"] - m["e"] * T["cd"]
    spread = lambda q: float(np.sum((resid(q) - np.median(resid(q))) ** 2))
    best = min(((xc, ps, 0.0) for ps in np.arange(16) * np.pi / 8), key=spread)
    r = least_squares(resid, [best[0], best[1], -np.median(resid(best))], x_scale=[1.0, .1, 1.0], xtol=1e-12, ftol=1e-12)
    return r.x[0], r.x[1], float(np.sqrt(np.mean(r.fun ** 2)))


def _fit_motion(ts, outlines, m, sc, fits, T):
    """All the moments at once: the centre X0 + v t and the phase psi0 + r t (the page's motion while
    a state holds) and one vertical offset, least squared over every outline together, from the
    moments' own fits. This parts the envelope from the carrier where the wavelength outgrows the
    packet and one moment alone can trade one for the other. Returns (v mm/s, r rad/s, rms px)."""
    from scipy.optimize import least_squares
    ts = np.asarray(ts)
    pe = np.polyfit(ts, [f[0] for f in fits], 1)
    pr = np.polyfit(ts, np.unwrap([f[1] for f in fits]), 1)
    res = [_outline_model(X, Y, m, sc, T) for X, Y in outlines]
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


def axial_dip(R):
    """The square bar's axial branch: the frequency (kHz) of its least group velocity between 20 kHz
    and fmax, from the sweep (the drag in measure_screen goes there)."""
    from scipy.interpolate import CubicSpline
    ks, W = R["br"]["axial"]
    w = W[:, 0]
    cg = CubicSpline(ks, w)(ks, 1)
    f = w / (2e3 * np.pi)
    m = (f > 20) & (f < SECTIONS["bar"]["fmax"] / 1e3)
    return float(f[m][np.argmin(cg[m])])


def measure_screen(fdip):
    """The packets measured on the screen: the page at 1000 px, two pixels a drawing unit, and each
    waveguide's top outline read from its pictures (_outline) and fitted with its packet
    (_fit_packet) at moments 0.1 s apart. The tour's first stop on the bar (both waves, the
    poster's moment +- 1 s); then the reader: a click moves wave 1 onto the axial curve at 30 kHz,
    a drag takes it to fdip kHz (where the axial branch's c_g is least). Speeds in km/s: pixels a
    second / (2 px a unit x T.s units a mm) x T.slow. Returns the cases."""
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
            if n.startswith(f"nf-{NAME}.") and not n.endswith(".webp"):
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
                T = pg.evaluate("(() => { const T = {...CUR.T}; delete T.XM; return T; })()")
                # each wave's state as the page holds it, and the node its outline is drawn from
                # (the highest in the oblique view: the top-back one)
                st = pg.evaluate("[0, 1].map(w => { const S = LAST[w], T = CUR.T; let n = 0, bv = -1e9;"
                                 " for (let q = 0; q < CUR.N; q++) { const v = CUR.GZ[q] + (CUR.GY[q] - CUR.ymin) * T.ys * T.sd; if (v > bv) { bv = v; n = q; } }"
                                 " return {k: S.k, cg: S.cg, cp: S.cp, f: S.f, lam: S.lam, nm: CUR.BR[S.id].nm,"
                                 " u: [S.U[3 * n], S.U[3 * n + 1], S.U[3 * n + 2]], e: (CUR.GY[n] - CUR.ymin) * T.ys, z: CUR.GZ[n]}; })")
                fits, held, outl = {w: [] for w in ws}, {w: [] for w in ws}, {w: [] for w in ws}
                ms = {}
                for s_ in times:
                    q = pg.evaluate(f"() => {{ t = {s_:.6f}; render(); const q = stateNow(); return {{amp: q.amp, X: q.X.map(x => wrapX(CUR.T, x)), ps: q.ps}}; }}")
                    img = np.array(Image.open(io.BytesIO(pg.locator("canvas").screenshot())))
                    for w in ws:
                        ms[w] = m = dict(st[w], k=st[w]["k"] / 1e3, yc=STR_YC[w],
                                         g=min(11, .5 * T["s"] * st[w]["lam"] / (2 * np.pi)) * q["amp"] / T["s"])
                        outl[w].append(_outline(img, w, sc, T, m))
                        fits[w].append(_fit_outline(*outl[w][-1], m, sc, T))
                        held[w].append((q["X"][w], q["ps"][w]))
                for w in ws:
                    ts = np.array(times) - times[0]
                    v, r, rms = _fit_motion(ts, outl[w], ms[w], sc, fits[w], T)
                    k = ms[w]["k"]
                    hx = np.polyfit(ts, [h[0] for h in held[w]], 1)[0]
                    cases.append({"case": label, "w": w + 1, "nm": st[w]["nm"], "f": st[w]["f"], "cg": st[w]["cg"], "cp": st[w]["cp"],
                                  "cg_s": v * T["slow"] / 1e6, "cp_s": (v - r / k) * T["slow"] / 1e6, "res": rms / sc,
                                  "cg_1": _speeds(ts, fits[w], k)[0] * T["slow"] / 1e6, "cg_state": hx * T["slow"] / 1e6,
                                  "n": len(times), "span": times[-1] - times[0]})
                return st

            # the tour's first stop on the bar, printed moments around the poster's
            pg = page("?still")
            run(pg, "tour", (0, 1), [POSTER + .1 * j for j in range(-10, 11)])
            pg.close()
            # the reader: a click on the axial curve at 30 kHz takes wave 1 there, a drag to fdip
            pg = page("")
            pg.wait_for_timeout(1200)
            at = lambda js: pg.evaluate(f"(() => {{ const r = cv.getBoundingClientRect(), [x, y] = {js};"
                                        " return [r.left + x * r.width / W, r.top + y * r.height / H]; })()")
            ax = "CUR.BR[CUR.fund.axial]"
            pg.mouse.click(*at(f"[PX(30), PY(cpAtF({ax}, 30))]"))
            pg.evaluate("setPlay(false)")

            def settle_at(frac):                      # the clock run on until wave 1's packet is centred near frac L
                pg.evaluate(f"() => {{ for (let j = 0; j < 40000; j++) {{ t += .01; stateNow(); const X = wrapX(CUR.T, USER.X[0]);"
                            f" if (Math.abs(X - ({frac}) * CUR.T.L) < .008 * CUR.T.L && t - USER.t0 > 1.2) break; }} render(); }}")
                return pg.evaluate("t")

            t0 = settle_at(-.9)
            run(pg, "click, axial 30 kHz", (0,), [t0 + .1 * j for j in range(15)])
            x0, y0 = at("[PX(LAST[0].f), PY(LAST[0].cp)]")
            pg.mouse.move(x0, y0)
            pg.mouse.down()
            for j in range(1, 25):
                f = 30 + (fdip - 30) * j / 24
                pg.mouse.move(*at(f"[PX({f}), PY(cpAtF({ax}, {f}))]"))
            pg.mouse.up()
            t0 = settle_at(-.8)
            run(pg, f"drag, axial {fdip:.0f} kHz", (0,), [t0 + .1 * j for j in range(21)])
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
    if (sec.kind === 'mirror' || sec.kind === 'c4v') {
      // the class's operations: mirrors y -> -y (character py), z -> -z (pz) and, for the
      // square (C4v), the diagonal y <-> z (pd), each a node map and a 3 x 3 component map;
      // per orbit (its representative in the RCM order of `rank`, or `rank8` for the C4v
      // orbits) the projections of its three unit displacements, orthonormalised in turn
      const key = (y, z) => Math.round(y * 1e3) + ',' + Math.round(z * 1e3), at = new Map();
      for (let n = 0; n < N; n++) at.set(key(sec.nodes[2 * n], sec.nodes[2 * n + 1]), n);
      const map = f => Int32Array.from({length: N}, (_, n) => at.get(f(sec.nodes[2 * n], sec.nodes[2 * n + 1])));
      const my = map((y, z) => key(-y, z)), mz = map((y, z) => key(y, -z));
      const I3 = [1, 0, 0, 0, 1, 0, 0, 0, 1], Ry = [1, 0, 0, 0, -1, 0, 0, 0, 1], Rz = [1, 0, 0, 0, 1, 0, 0, 0, -1];
      const mul3 = (A, B) => Array.from({length: 9}, (_, i) => { const r = i / 3 | 0, c = i % 3; return A[3 * r] * B[c] + A[3 * r + 1] * B[3 + c] + A[3 * r + 2] * B[6 + c]; });
      let G = [[n => n, 1, I3]];
      if (C.py) G.push([n => my[n], C.py, Ry]);
      if (C.pz) G.push([n => mz[n], C.pz, Rz]);
      if (C.py && C.pz) G.push([n => my[mz[n]], C.py * C.pz, mul3(Ry, Rz)]);
      if (C.pd) {
        const md = map((y, z) => key(z, y)), Rd = [1, 0, 0, 0, 0, 1, 0, 1, 0];
        G = G.concat(G.map(([g, chi, R]) => [n => md[g(n)], chi * C.pd, mul3(Rd, R)]));
      }
      const rank = C.pd ? sec.rank8 : sec.rank, reps = [];
      for (let n = 0; n < N; n++) if (rank[n] >= 0) reps[rank[n]] = n;
      for (const n of reps) {
        const acc = [];
        for (let c = 0; c < 3; c++) {
          const v = new Map();
          for (const [g, chi, R] of G) for (let c2 = 0; c2 < 3; c2++) {
            const r = R[3 * c2 + c];
            if (r) { const d = 3 * g(n) + c2; v.set(d, (v.get(d) || 0) + chi * r); }
          }
          for (const u of acc) {
            let dt = 0;
            for (const [d, x] of u) dt += x * (v.get(d) || 0);
            if (dt) for (const [d, x] of u) v.set(d, (v.get(d) || 0) - dt * x);
          }
          let s2 = 0;
          for (const x of v.values()) s2 += x * x;
          if (s2 < 1e-18) continue;
          const nv = Math.sqrt(s2), u = new Map();
          for (const [d, x] of v) if (Math.abs(x) > 1e-12 * nv) u.set(d, x / nv);
          acc.push(u);
        }
        for (const u of acc) { for (const [d, x] of u) put(d, m, x); m++; }
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
    const iterate = (F, start) => {                    // M x of one step is the next step's right side
      let x = new Float64Array(C.n);
      if (start) x.set(start);
      else for (let i = 0; i < C.n; i++) x[i] = Math.sin(12.9898 * (i + 1)) * 43758.5453 % 1;   // a fixed start
      let w2 = F.s, Mx = mul(C.M, C, x);
      for (let it = 0; it < 40; it++) {
        x = ldlSolve(F.A, C, F.d, Mx);
        Mx = mul(C.M, C, x);
        const nm = Math.sqrt(dot(x, Mx));
        for (let i = 0; i < C.n; i++) { x[i] /= nm; Mx[i] /= nm; }
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
const CM = D.cmax;                                       // km/s: the top of the plot, every section

/* ---------------------------------------------------------------- layout
   Each section has its own frequency window (sec.fm, kHz): its published curves'
   range. WIN is the section being drawn (CUR between frames, so the pointer maps
   through the window on show); PX and PY map through it. */
const P = {x: 88, y: 64, w: 452, h: 326};
let WIN = {fm: 1};
const PX = f => P.x + f / WIN.fm * P.w, PY = c => P.y + P.h - c / CM * P.h;
function inWin(sec, f) { const o = WIN; WIN = sec; try { return f(); } finally { WIN = o; } }
const WC = [C.navy, C.accent];                           // wave 1, wave 2
const SEC = {cx: [688, 888], cy: 244, G: 18};             // section views: centres, largest drawn displacement
const STR = {x1: 950, yc: [%d, %d], G: 11, SL: .5};       // dispersion.py's STR_YC
/* the packets: each wave runs along its waveguide as bursts of its own mode under a Hann
   envelope T.pw mm across, one after another T.rep mm apart, so that one crosses the drawn
   T.L mm at a time. The envelope's centre X moves at c_g and the phase psi at the centre
   at k c_g - w, so the crests move at c_p. Each section has one clock, T.slow times slower
   than the steel's, for every operating point and both waves, so a slow packet lags a fast
   one as it would; and one length scale, T.s units a millimetre (dispersion.py, strip_of). */
const wrapX = (T, x) => x - T.rep * Math.floor((x - T.xl) / T.rep);   // a packet's centre, onto [xl, xl + rep)
// a state's rates: the envelope's speed (mm/s on the page) and its centre phase's (rad/s);
// k in rad/m, f in kHz, c_g in km/s
const rates = (sec, k, f, cg) => ({v: cg * 1e6 / sec.T.slow, r: (k * cg - 2 * Math.PI * f) * 1e3 / sec.T.slow});
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
const NXS = 413;                                         // samples along each drawn waveguide
function prepare(buf) {
  const {meta, arr} = parseBlob(buf), sec = {...meta, key: meta.key, meta};
  sec.fm = meta.fmax;                                    // kHz: the section's window
  sec.nodes = arr.nodes; sec.N = arr.nodes.length / 2;
  sec.model = safeModel({E: meta.E, nu: meta.nu, rho: meta.rho, nodes: arr.nodes, elems: Int32Array.from(arr.elems),
                         kind: meta.kind, rank: arr.rank ? Int32Array.from(arr.rank) : null,
                         rank8: arr.rank8 ? Int32Array.from(arr.rank8) : null, nth: meta.nth, classes: meta.classes});
  sec.elems = Int32Array.from(arr.elems); sec.NE = sec.elems.length / 9;
  sec.GLC = arr.glide;                                   // km/s: the tour's glides' exact group velocities
  sec.GY = Float32Array.from({length: sec.N}, (_, n) => arr.nodes[2 * n]);
  sec.GZ = Float32Array.from({length: sec.N}, (_, n) => arr.nodes[2 * n + 1]);
  sec.ymin = Math.min(...sec.GY);
  // the drawn waveguide: its length scale, oblique view and clock (dispersion.py, strip_of)
  const T = sec.T = {...meta.strip};
  T.cd = T.d * Math.cos(T.a * Math.PI / 180); T.sd = T.d * Math.sin(T.a * Math.PI / 180);
  T.rep = T.L + T.pw; T.xl = -T.L - T.pw / 2; T.dx = T.L / (NXS - 1);
  T.XM = Float32Array.from({length: NXS}, (_, m) => (m - (NXS - 1)) * T.dx);
  sec.BR = inWin(sec, () => meta.brs.map((r, id) => {
    const C_ = arr.curves, {k, f, cp} = lay(C_.subarray(r.o, r.o + r.n), C_.subarray(r.o + r.n, r.o + 2 * r.n), C_.subarray(r.o + 2 * r.n, r.o + 3 * r.n));
    const xy = Array.from(f, (_, i) => [PX(Math.min(f[i], 1.04 * sec.fm)), PY(Math.min(cp[i], 1.04 * CM))]);
    const inw = i => f[i] <= sec.fm && cp[i] <= CM;
    let i0 = 0, i1 = f.length - 1;
    while (!inw(i0)) i0++;
    while (!inw(i1)) i1--;
    // a backward wave (f falling as k grows, below its cut-on) makes f(k) turn back
    let mono = true, fmin = Infinity, fmax = -Infinity;
    for (let i = i0; i <= i1; i++) { fmin = Math.min(fmin, f[i]); fmax = Math.max(fmax, f[i]); if (i > Math.max(0, i0 - 1) && f[i] <= f[i - 1]) mono = false; }
    if (i0 > 0 && f[i0] <= f[i0 - 1]) mono = false;
    return {...r, id, f, cp, k, xy, i0, i1, mono, fmin, fmax};
  }));
  sec.HG = fc => Math.min(4, Math.floor(5 * (fc - meta.fc1) / (sec.fm - meta.fc1 || 1)));
  sec.TOUR = meta.tour.map(s => ({...s, k1: kAtF(sec.BR[s.b1], s.f1), ka: kAtF(sec.BR[s.b2], s.fa), k2: kAtF(sec.BR[s.b2], s.f2)}));
  sec.faces = meta.faces;
  // each face's neighbours in its loop, for creases and silhouettes along the waveguide
  for (const F of sec.faces) {
    const same = sec.faces.filter(G => G.loop === F.loop);
    F.prev = same.find(G => G.nodes[G.nodes.length - 1] === F.nodes[0]);
    F.next = same.find(G => G.nodes[0] === F.nodes[F.nodes.length - 1]);
    F.front = F.n[0] - T.sd * F.n[1] < 0;
    F.depth = F.nodes.reduce((a, n) => a + T.ys * sec.GY[n] - T.sd * sec.GZ[n], 0) / F.nodes.length;
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
function kAtF(br, f, k0) {                               // the wavenumber of f (kHz) on the branch, in the window; where
  f = clamp(f, br.fmin, br.fmax);                        // f is met twice (a backward wave), the crossing nearest k0, else the last
  if (br.mono) {
    const i = seek(br.f, f, 0, br.f.length - 1), s = clamp((f - br.f[i]) / (br.f[i + 1] - br.f[i]));
    return lerp(br.k[i], br.k[i + 1], s);
  }
  let best = null;
  for (let i = Math.max(0, br.i0 - 1); i < Math.min(br.f.length - 1, br.i1 + 1); i++) {
    const a = br.f[i], b = br.f[i + 1];
    if (a === b || (a - f) * (b - f) > 0) continue;
    const k = lerp(br.k[i], br.k[i + 1], (f - a) / (b - a));
    if (best === null || (k0 === undefined ? k > best : Math.abs(k - k0) < Math.abs(best - k0))) best = k;
  }
  return best === null ? br.k[br.i1] : clamp(best, br.k[br.i0], br.k[br.i1]);
}
const cpAtF = (br, f, k0) => atK(br, kAtF(br, f, k0)).cp;   // c_p on the drawn curve at f, in its window
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
const CACHE = new Map(), LAST = [null, null], HF = new Map(), XS = new Map();
/* a state's frequency and group velocity alone (the tour's rates, the tooltip), remembered;
   its last few eigenpairs kept too (XS), so that solved() need not solve them again */
function exact(sec, id, k) {
  const key = sec.key + ':' + id + ':' + k.toFixed(6), c = CACHE.get(key);
  if (c) return c;
  let r = HF.get(key);
  if (!r) {
    const br = sec.BR[id], s = sec.model.solve(br.ci, br.b, k, 2e3 * Math.PI * atK(br, k).f, null);
    r = {k, f: s.w / (2e3 * Math.PI), cg: sec.model.cg(br.ci, k, s.x, s.w) / 1e3};
    HF.set(key, r);
    if (HF.size > 800) HF.delete(HF.keys().next().value);
    XS.set(key, s);
    if (XS.size > 4) XS.delete(XS.keys().next().value);
  }
  return r;
}
const rateOf = (sec, id, k) => { const e = exact(sec, id, k); return rates(sec, k, e.f, e.cg); };
function solved(sec, st, w) {
  const br = sec.BR[st.id], key = sec.key + ':' + st.id + ':' + st.k.toFixed(6);
  let r = CACHE.get(key);
  const p = LAST[w], near = p && p.sec === sec.key && p.id === st.id && Math.abs(p.k - st.k) < .08 * st.k;
  if (!r) {
    const s = XS.get(key) || sec.model.solve(br.ci, br.b, st.k, 2e3 * Math.PI * atK(br, st.k).f, near ? p.x : null);
    const x = Float64Array.from(s.x);
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
const TOUR = {off: 0};
/* wave 2's glide in stop i, as the rates it passes through at NG + 1 moments evenly spread
   over the glide's TGD s: the exact group velocity of each moment's state comes with the
   section (dispersion.py, glide_rates: the same model's eigenpairs at the wavenumbers this
   page takes, by kAtF), so a stop starts without solving NG + 1 states; and their integrals
   over time, each interval by the cubic through its four nearest moments, integrated
   exactly. Remembered per section. */
const NG = 128;
function glideOf(sec, i) {
  const all = sec.GL || (sec.GL = []);
  if (!all[i]) {
    const s = sec.TOUR[i], br = sec.BR[s.b2], k = new Float64Array(NG + 1), v = new Float64Array(NG + 1), r = new Float64Array(NG + 1);
    for (let j = 0; j <= NG; j++) {
      k[j] = j === 0 ? s.ka : j === NG ? s.k2 : kAtF(br, s.fa + (s.f2 - s.fa) * easeInOut(j / NG));
      const q = rates(sec, k[j], atK(br, k[j]).f, sec.GLC[i * (NG + 1) + j]);
      v[j] = q.v; r[j] = q.r;
    }
    const h = TGD / NG, I = y => { const o = new Float64Array(NG + 1); for (let j = 0; j < NG; j++) o[j + 1] = o[j] + h * part(y, j, 1); return o; };
    all[i] = {s, k, v, r, IV: I(v), IR: I(r)};
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
    // the first stop: both packets at the middle of the drawn length at the poster's moment
    return {st: [{id: s.b1, k: s.k1}, {id: s.b2, k: s.k2}], X: R.map(q => -sec.T.L / 2 + q.v * d), ps: R.map(q => q.r * d), rt: R,
            amp: settle(o + .45, .8) * out, mk: [settle(o + .6, .28) * out, settle(o + .6, .28) * out], lab: lab(o + .3) * out};
  }
  const u = tau - T1, n = Math.floor(u / TS), ta = u - n * TS, i = (n + 1) % T.length, s = T[i], t0 = o + T1 + n * TS;
  const X = clamp((ta - TG0) / TGD), f2 = s.fa + (s.f2 - s.fa) * easeInOut(X);
  const G = glideOf(sec, i), g2 = glideAt(G, ta);
  const R1 = rateOf(sec, s.b1, s.k1), out = 1 - seg(t0 + TS - 1, 1);
  return {st: [{id: s.b1, k: s.k1}, {id: s.b2, k: X <= 0 ? s.ka : X >= 1 ? s.k2 : kAtF(sec.BR[s.b2], f2)}],
          X: [sec.T.xl + R1.v * ta, sec.T.xl + g2.x], ps: [PH0 + R1.r * ta, PH0 + g2.p], rt: [R1, {v: g2.v, r: g2.r}],
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
  USER = {st: q.st.map(s => ({...s})), X: q.X.map(x => wrapX(CUR.T, x)), ps: q.ps.slice(), tl: t, t0: t, a0: q.amp, m0: q.mk.slice()};
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
    return S ? rates(CUR, S.k, S.f, S.cg) : rateOf(CUR, USER.st[w].id, USER.st[w].k);
  });
  for (let w = 0; w < 2; w++) {
    USER.X[w] = wrapX(CUR.T, USER.X[w] + rt[w].v * dt);
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
  // the windows differ: the same share of the new section's window
  const br = from.BR[st.id], q = atK(br, st.k), f = q.f / from.fm * to.fm;
  let id = br.type && to.fund[br.type] !== undefined ? to.fund[br.type] : -1;
  if (id < 0) {
    let bd = Infinity;
    for (const b of to.BR) if (f >= b.fmin && f <= b.fmax) { const d = Math.abs(cpAtF(b, f) - q.cp); if (d < bd) { bd = d; id = b.id; } }
    if (id < 0) id = to.fund.vertical;
  }
  return {id, k: kAtF(to.BR[id], f)};
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
    if (USER) { USER.st = USER.st.map(s => mapState(from, to, s)); USER.X = USER.X.map(x => wrapX(to.T, x * to.T.L / from.T.L)); }
    else TOUR.off = t - (playing ? 0 : POSTER_T);
    CUR = to;
    LAST[0] = LAST[1] = null;
    syncSwitch();
    if (!playing) { const tick = () => { render(); if (SW) requestAnimationFrame(tick); }; requestAnimationFrame(tick); }
  }, () => syncSwitch());
}
function setSectionNow(key) {                            // at once, no animation (the checks and a still use it)
  return load(key).then(to => {
    if (CUR.key !== key) {
      if (USER) { USER.st = USER.st.map(s => mapState(CUR, to, s)); USER.X = USER.X.map(x => wrapX(to.T, x * to.T.L / CUR.T.L)); }
      CUR = to; LAST[0] = LAST[1] = null;
    }
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
function mathW(s, size) { ctx.save(); const w = _mathDraw(_runs(s), 0, 0, size, C.ink, false); ctx.restore(); return w; }
const FOOT_GAP = 8;
// the right end of a section's parameter lines (drawing units): both must clear the page controls
const footW = sc => 18 + Math.max(textW(sc.params, 14), textW(D.steel + ';', 14) + FOOT_GAP + mathW(sc.T.label, 14));
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
  // each section in its own window: a point at the same share of either window, joined on the screen
  for (const type of ['vertical', 'lateral', 'axial', 'torsional']) {
    if (A.fund[type] === undefined || B.fund[type] === undefined) continue;
    if (type === 'lateral' && (A.fund.lateral === A.fund.vertical) && (B.fund.lateral === B.fund.vertical)) continue;
    const ba = A.BR[A.fund[type]], bb = B.BR[B.fund[type]], pts = [];
    const lo = lerp(ba.fmin / A.fm, bb.fmin / B.fm, e);
    for (let i = 0; i <= 160; i++) {
      const u = i / 160;
      if (u < lo) continue;
      const ya = inWin(A, () => PY(Math.min(1.04 * CM, cpAtF(ba, u * A.fm)))), yb = inWin(B, () => PY(Math.min(1.04 * CM, cpAtF(bb, u * B.fm))));
      pts.push([P.x + u * P.w, lerp(ya, yb, e)]);
    }
    line(pts, {...STY[type], alpha: a});
  }
}
function xTicks(sec, a) {                                // a section's frequency ticks: inward, at the bottom and the top
  if (a <= 0) return;
  inWin(sec, () => {
    for (const v of sec.meta.xticks) {
      const x = PX(v);
      line([[x, P.y + P.h], [x, P.y + P.h - 5]], {color: C.ink, width: 1.1, alpha: a});
      line([[x, P.y], [x, P.y + 5]], {color: C.ink, width: 1.1, alpha: a});
      math(fmt(v), x, P.y + P.h + 21, {size: 15, align: 'center', alpha: a});
    }
  });
}
const GUIDE = {color: C.guide, width: 1, dash: [5, 4]};
const LEG = {y: P.y + P.h + 76, dy: 19, gap: 24};         // the legend: two rows under the frequency axis
function legend(sec, a) {                                // three columns of two, centred under the plot, off every curve
  if (a <= 0) return;
  const E = [...sec.legend, ['guide', 'shear, Rayleigh']], cols = [];
  for (let i = 0; i < E.length; i += 2) cols.push(E.slice(i, i + 2));
  const cw = cols.map(c => Math.max(...c.map(([, s]) => textW(s, 14))) + 32 + LEG.gap), LW = cw.reduce((x, y) => x + y, 0) - LEG.gap;
  let x0 = P.x + (P.w - LW) / 2;
  cols.forEach((c, j) => {
    c.forEach(([type, s], r) => {
      const y = LEG.y + r * LEG.dy, st = type === 'guide' ? GUIDE : type ? STY[type] : HIGH;
      line([[x0, y - 5], [x0 + 26, y - 5]], {...st, alpha: a});
      text(s, x0 + 32, y, {size: 14, alpha: a});
    });
    x0 += cw[j];
  });
}
function plotA(S, q, sw) {
  panel('a', 18, 34, {alpha: lab(0)});
  text('dispersion curves', 52, 34 + rise(lab(.03)), {size: 17, color: C.body, alpha: lab(.03)});
  const ax = axes({x: P.x, y: P.y, w: P.w, h: P.h, xlim: [0, WIN.fm], ylim: [0, CM],
    xticks: [], yticks: [0, 2, 4, 6, 8, 10],
    xlabel: '\\rm{frequency}\\ f\\ \\rm{(kHz)}', ylabel: '\\rm{phase velocity}\\ c_{\\rm{p}}\\ \\rm{(km/s)}',
    ylabelGap: 44, progress: seg(0, .35)});
  const p = sw ? swP() : 1, A = sw ? sw.from : CUR, e = easeInOut(clamp((p - .1) / .8));
  const out = sw ? 1 - clamp(p / .4) : 0, inn = sw ? clamp((p - .35) / .45) : 1;
  // each section's own frequency ticks: the old fade before the new arrive
  const ta = clamp(seg(0, .35) * 1.4);
  if (sw) { xTicks(A, ta * (1 - clamp(p / .35))); xTicks(CUR, ta * clamp((p - .45) / .35)); } else xTicks(CUR, ta);
  ax.inside(() => {
    for (const [sec, a] of sw ? [[A, out], [CUR, inn]] : [[CUR, 1]]) {
      if (a <= 0) continue;
      ctx.save(); ctx.globalAlpha = .55 * seg(.3, .3) * a; ctx.fillStyle = C.steel;
      ctx.fillRect(P.x, P.y, inWin(sec, () => PX(sec.fc1)) - P.x, P.h); ctx.restore();
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
    if (s <= 0 || fc > sec.fm) continue;
    const x = inWin(sec, () => PX(fc)), y = P.y + 1;
    ctx.save(); ctx.globalAlpha = s; ctx.fillStyle = C.guide; ctx.beginPath();
    ctx.moveTo(x, y + 7 * s); ctx.lineTo(x - 3.8, y); ctx.lineTo(x + 3.8, y); ctx.closePath(); ctx.fill(); ctx.restore();
  }
  const ca = lab(.40);
  for (const [sec, a] of sw ? [[A, out], [CUR, inn]] : [[CUR, 1]])
    text('cut-on', Math.max(P.x + 2, inWin(sec, () => PX(sec.fc1)) - 2), P.y - 8 + rise(ca), {size: 14, color: C.muted, alpha: ca * a});
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
  const labels = markerLabels(pos);
  for (let w = 0; w < 2; w++) {
    if (labels[w].y !== pos[w].y) {
      line([[pos[w].x, pos[w].y], [labels[w].x, labels[w].y]], {color: WC[w], width: 1, alpha: pos[w].a});
      dot(pos[w].x, pos[w].y, 2.5, {color: WC[w], fill: WC[w], alpha: pos[w].a});
    }
    badge(w, labels[w].x, labels[w].y, pos[w].a);
  }
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
function markerLabels(pos) {
  const labels = pos.map(p => ({...p}));
  if (pos.every(p => p.a > .35) && Math.hypot(pos[0].x-pos[1].x, pos[0].y-pos[1].y) < 24) {
    labels[0].y -= 14; labels[1].y += 14;
  }
  return labels;
}
function markerPos(S, q, sw, e) {
  const at = (s, a) => ({x: PX(s.f), y: PY(s.cp), a});
  if (!sw) return [0, 1].map(w => at(S[w], q.mk[w]));
  // during a switch: from the old points (in the old window) to the new ones, riding the morphing curves
  return [0, 1].map(w => {
    const A = sw.S0[w], B = S[w], a = Math.max(q.mk[w], sw.q0.mk[w] * (1 - clamp((swP() - .6) / .4)));
    if (!A) return at(B, a * clamp((swP() - .5) / .3));
    const ba = sw.from.BR[A.id], bb = CUR.BR[B.id];
    const pa = inWin(sw.from, () => [PX(A.f), PY(A.cp)]), pb = [PX(B.f), PY(B.cp)];
    if (ba.type && ba.type === bb.type) {
      const u = lerp(A.f / sw.from.fm, B.f / CUR.fm, e);
      const ya = inWin(sw.from, () => PY(cpAtF(ba, u * sw.from.fm))), yb = PY(cpAtF(bb, u * CUR.fm));
      return {x: P.x + u * P.w, y: lerp(ya, yb, e), a};
    }
    return {x: lerp(pa[0], pb[0], e), y: lerp(pa[1], pb[1], e), a};
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

/* ---------------------------------------------------------------- (b) along the waveguide
   An oblique view of T.L mm of the waveguide ending at x = 0: x to the right, z up,
   y receding at T.a degrees, times T.d (the plate: a wide slab, its slice's width
   drawn T.ys times over, seen from above). The section's boundary, cut into faces (runs
   of boundary nodes of one direction), is swept along x; the faces turned to the
   reader are drawn from the farthest to the nearest, and the face at x = 0 last.
   The wave runs along it as packets: every point moves as
   E(x - X) Re{U(y, z) exp(i(k(x - X) + psi))}, E the Hann envelope T.pw mm across
   about the packet's centre X (which moves at c_g; psi turns at k c_g - w, so the
   crests move at c_p), drawn with its largest displacement STR.G units but never
   steeper than STR.SL, and coloured by |u| / U_rms at that instant (U_rms the
   section's rms displacement at the packet's centre), so every wave, the axial one
   too, is seen to travel. The faces' colours are one small image a wave, made each
   frame: a column a sample along the waveguide, a row a node of each drawn face. It is
   laid on the face in parallelogram pieces cut to the deformed outline: fine where
   the packet is, one piece over the straight, white beam on either side. A bore's
   faces are drawn only near the open end, where they show. */
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
  const T = sec.T, s = T.s, yc = STR.yc[w], U = S.U, k = S.k / 1e3, NX = NXS, N = sec.N, y0 = sec.ymin;
  const XM = T.XM, PW = T.pw, CD = T.cd, SD = T.sd, x1 = T.x1, ys = T.ys;
  const g = Math.min(STR.G, STR.SL * s * S.lam / (2 * Math.PI)) * amp / s;   // mm per unit of U
  // the packet on the waveguide: E cos and E sin of the phase at each sample, zero off it
  const X0 = wrapX(T, Xc), cs = new Float32Array(NX), sn = new Float32Array(NX);
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
    const X = new Float32Array(NX), Y = new Float32Array(NX), e = (sec.GY[n] - y0) * ys;
    const ux = g * U[3 * n], uy = g * U[3 * n + 1], uz = g * U[3 * n + 2];
    for (let m = 0; m < NX; m++) {
      const d = e + uy * cs[m];
      X[m] = x1 + s * (XM[m] - ux * sn[m] + d * CD);
      Y[m] = yc - s * (sec.GZ[n] + uz * cs[m] + d * SD);
    }
    rows.set(n, r = {X, Y});
    return r;
  };
  const c0 = cs[NX - 1], s0 = sn[NX - 1];
  const end = n => { const d = (sec.GY[n] - y0) * ys + g * U[3 * n + 1] * c0;
    return [x1 + s * (-g * U[3 * n] * s0 + d * CD), yc - s * (sec.GZ[n] + g * U[3 * n + 2] * c0 + d * SD)]; };
  const E_ = Array.from({length: N}, (_, n) => end(n));
  const mag = (n, m) => Math.sqrt(S.AX[n] * sn[m] * sn[m] + S.TR[n] * cs[m] * cs[m]);
  // pieces along x: straight lines between their ends stay within 0.6 units of the deformed edge,
  // which bends with the carrier and the envelope together (wavenumbers 2 pi / lambda and 2 pi / PW)
  const bend = Math.max(1e-9, g * s), kE = 2 * Math.PI / S.lam + 2 * Math.PI / PW;
  const step = 2 * Math.round(clamp(Math.sqrt(8 * .6 / bend) / kE / T.dx / 2, 1, 12)), ca = fillA * clamp(amp * 1.25);
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
      // its mesh: lines along the waveguide at every T.lj-th node of the face, sections every T.lm samples
      if (F.outer) {
        ctx.save(); ctx.globalAlpha *= .45 * fillA; ctx.strokeStyle = C.sky; ctx.lineWidth = .6; ctx.beginPath();
        const lj = F.nodes.length <= 3 ? 1 : T.lj;          // a face of one element across: its middle line
        for (let j = lj; j < F.nodes.length - 1; j += lj) { const r = row(F.nodes[j]); ctx.moveTo(r.X[0], r.Y[0]); for (let m = 2; m < NX; m += 2) ctx.lineTo(r.X[m], r.Y[m]); }
        const R_ = F.nodes.map(row);
        for (let m = NX - 1; m > 0; m -= T.lm) { ctx.moveTo(R_[0].X[m], R_[0].Y[m]); for (let j = 1; j < R_.length; j++) ctx.lineTo(R_[j].X[m], R_[j].Y[m]); }
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
  WIN = CUR;
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
  // the parameters: the section and its mesh, then the steel and the section's one clock (its slow-motion factor)
  const pa = lab(.7), foot = (sc, a) => {
    if (a <= 0) return;
    text(sc.params, 18, H - 36, {size: 14, color: C.muted, alpha: a});
    const w = text(D.steel + ';', 18, H - 16, {size: 14, color: C.muted, alpha: a});
    math(sc.T.label, 18 + w + FOOT_GAP, H - 16, {size: 14, color: C.muted, alpha: a});
  };
  if (sw && p < 1) { foot(sw.from, pa * (1 - clamp(p / .4))); foot(CUR, pa * clamp((p - .45) / .4)); }
  else foot(CUR, pa);
  place(S);
}

// ?section=rail (bar, ibeam, rail, pipe or plate) opens the page on that section, for the checks and a
// still of each; without it the page opens on the bar
const SEL = (/[?&]section=(\w+)/.exec(location.search) || [])[1];
CUR = prepare(b64buf(D.blobs[SEL in D.blobs ? SEL : 'bar']));

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
      el.setAttribute('aria-valuemin', br.fmin.toFixed(1)); el.setAttribute('aria-valuemax', br.fmax.toFixed(1));
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
    if (br.id === S.id || S.f < br.fmin || S.f > br.fmax) continue;
    const k = kAtF(br, S.f), cp = atK(br, k).cp, d = (cp - S.cp) * dir;
    if (d > 1e-6 && (!best || d < best.d)) best = {d, id: br.id, k};
  }
  return best;
}
function key(w, e) {
  const S = LAST[w]; if (!S || S.sec !== CUR.key) return;
  const br = CUR.BR[S.id], big = e.shiftKey || e.key === 'PageUp' || e.key === 'PageDown' ? 10 : 1;
  let st = null;
  const df = big * CUR.fm / 200;                         // 1 kHz on a 200 kHz window, in proportion on the others
  if (e.key === 'ArrowRight' || e.key === 'PageUp') st = {id: S.id, k: kAtF(br, S.f + df, S.k)};
  else if (e.key === 'ArrowLeft' || e.key === 'PageDown') st = {id: S.id, k: kAtF(br, S.f - df, S.k)};
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
    '.nfb{position:absolute;margin:0;padding:0;border:0;background:transparent;cursor:pointer;outline:none;font:inherit;color:transparent;overflow:hidden}' +
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
      let st = {id: br.id, k: GRAB.axis ? kAtF(br, (X - P.x) / P.w * WIN.fm, USER.st[GRAB.w].k) : nearOn(br, X, Y).k};
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

FIGURE = FIGURE.replace("yc: [%d, %d]", f"yc: [{STR_YC[0]}, {STR_YC[1]}]")   # one source for the strips' centres
JS = "const D = DATA;\n" + SOLVER + FIGURE + "\nboot();\n"


def check_text(Rs, refs, convs, SV, sizes, ov, ovl, TG, MS, perf):
    L = ["Figure 4 (nf-dispersion): SAFE dispersion curves of guided waves in five steel waveguides, each over",
         "the frequency window of its reference: published curves for four (the bar, the rail, the pipe, the",
         "plate), and for the I-beam, of which none were found, the same model on a mesh refined twice; every",
         "wave the page shows solved in the page by the same SAFE model", ""]
    p = L.append
    p("MATERIAL AND METHOD")
    p(f"  steel: E = {sm.E / 1e9:.0f} GPa, nu = {sm.NU}, rho = {sm.RHO:.0f} kg/m^3: c_L = {sm.C_L:.1f} m/s, c_T = {sm.C_T:.1f} m/s,")
    p(f"  c_0 = sqrt(E/rho) = {sm.C_0:.1f} m/s, c_R = {sm.C_R:.1f} m/s (the Rayleigh equation's root, c_R/c_T = {sm.C_R / sm.C_T:.5f})")
    p("  SAFE: u = U(y, z) exp(i(kx - wt)); 9-node isoparametric quadrilaterals, 3 x 3 Gauss, 3 dof a node;")
    p("  [K1 + ik K2 + k^2 K3 - w^2 M] U = 0, made real symmetric by U_x = i V_x; each symmetry class on its")
    p("  own orthonormal basis; the lowest eigenpairs at each real k (dense eigh, or sparse shift-invert).")
    p("  The square bar, the pipe and the plate are meshed on structured grids; the I-beam and the rail by a")
    p("  constrained quality Delaunay triangulation of the outline (Shewchuk's Triangle, minimum angle 30")
    p("  degrees), each triangle split into three quadrilaterals, then 9-node elements, the boundary nodes moved")
    p("  onto the true outline; a half or quarter meshed and mirrored, so the mirror planes hold exactly.")
    p(f"  The window of every section: f up to its own fmax and c_p up to {CP_MAX / 1e3:g} km/s. fmax is chosen in a gap")
    p("  between the frequencies where branches enter the window (their c_p falling through its top), so that every")
    p("  branch drawn enters well before fmax and none is about to (each is drawn once); in all but the bar this is")
    p("  also a gap between cut-on frequencies. The cut-on marks on the top frame are the k = 0 frequencies of")
    p("  exactly the drawn higher order branches.")
    p("")
    p("SUMMARY")
    p("  section  window        reference                                      branches   mesh                    per shortest")
    p("                                                                        ours/ref.                          wavelength")
    rows = [("bar", "Hayashi, Kawashima and Rose 2004 (SAFE), Fig. 2"), ("ibeam", "independent: the mesh refined twice"),
            ("rail", "Ramatlo, Wilke and Loveday 2018 (SAFE), Fig. 1"), ("pipe", "exact, Gazis 1959"),
            ("plate", "exact, Rayleigh-Lamb and SH")]
    for key, ref in rows:
        Z, R, C = SECTIONS[key], Rs[key], convs[key]
        nb = len(window_branches(key, R))
        nref = refs[key]["nref"]
        p(f"  {Z['label']:7s}  0-{Z['fmax'] / 1e3:g} kHz  {ref:46s}  {nb:2d}/{nref if nref is not None else '-':>2}     "
          f"{C['nel']:4d} Q9, {C['hmax']:.2f} mm max   {C['lam'] / C['hmax'] if 'lam' in C else 0:4.1f}")
    p("")
    for key in ORDER:
        L += refs[key]["lines"]
        p(f"  MESH ({SECTIONS[key]['label']})")
        L += convs[key]["lines"]
        p("")
    ref, gen = sm.Safe(NE_BAR, NE_BAR, SQ / 1e3, SQ / 1e3), make_section("bar")
    pairs = ((gen.K1, ref.K1), (gen.K2, ref.K2), (gen.K3, ref.K3), (gen.M, ref.M))
    dm = max(abs(A - B).max() / abs(B).max() for A, B in pairs)
    p("THE PAGE SOLVES EVERY WAVE IT SHOWS")
    p("  Each section travels as its mesh (nodes in float32, the Python model reading the same rounded")
    p("  values) and its symmetry. The page builds the same isoparametric Q9 elements (3 x 3 Gauss),")
    p("  assembles each class on its own basis (the projections of each orbit's displacements, orthonormalised:")
    p("  mirror planes, the square's C4v, or the pipe's harmonics) as a skyline in an RCM order, and solves a")
    p("  wave (class, branch, k) exactly: a skyline LDL^T of K(k) - s M counts its negative pivots (Sylvester:")
    p("  the eigenvalues below s), s moves until exactly `branch` lie below, and inverse iteration converges on")
    p("  the branch's own eigenpair; should it head for a nearer one below s, the count brackets the branch's")
    p("  alone, bisection narrows the bracket, and the iteration runs again from its middle.")
    p(f"  The bar's general assembly gives safe_model's rectangle matrices: max relative difference {dm:.1e}.")
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
    if perf:
        p("  In headless Chromium (the page at 672 px, this shared machine): from choosing a section to its first")
        p("  frame (its data read, its classes' matrices assembled, its two waves solved and drawn), and a frame")
        p("  of its first glide (wave 2 at a wavenumber not met before: one state solved, both beams drawn):")
        for key in ORDER:
            q = perf.get(key)
            if q:
                p(f"    {SECTIONS[key]['label']:7s} switch to the first frame {q['switch']:.0f} ms; a glide frame {q['frame']:.0f} ms")
    p("  The curves travel thinned: only the eigenfrequencies a cubic Hermite in k needs (its slopes the group")
    p(f"  velocity, from a spline through the branch) to give every dropped one back within {THIN:.0e}; the page lays")
    p(f"  each segment out again within {THIN:.0e}. The page's curve at every point of the sweep:")
    for key in ORDER:
        st = thinned(key, Rs[key])[2]
        p(f"    {SECTIONS[key]['label']:7s} {st['kept']} of {st['n']} points travel ({st['kept'] / st['n']:.0%}),"
          f" laid out as {st['laid']}: max |f_page/f - 1| = {st['err']:.1e}")
    p("")
    L += check_group(Rs, SV, TG, MS)
    p("TIME: ONE CLOCK A SECTION")
    p("  Each section's packets, both waves and every operating point, run on one clock: the steel's time")
    p("  slowed T.slow times (written under the waveguides), and one length scale, T.s drawing units a mm. A")
    p("  packet's envelope moves at c_g / slow and its crests at c_p / slow, as they are; nothing is scaled per")
    p("  wave. So a slow packet lags a fast one, and dragging a wave along its curve changes both speeds at once.")
    p("  The clock keeps the crests of the tour's highest frequency cycling at about 7.5 a second (f / slow), so")
    p("  they are seen to move rather than flicker; the length shown holds two or more wavelengths of wave 1 in")
    p("  its packet. Per section: length shown L, envelope pw, slow, and the tour's states with the seconds each")
    p("  packet takes to cross L, the crests' frequency on the page, and c_p / c_g (above 1 the crests run")
    p("  forward through the envelope, below 1 backward):")
    for key in ORDER:
        Z = SECTIONS[key]
        G = Z["strip"]
        brs, flat = curves_of(key, Rs[key])
        cross = lambda cg: G["L"] / (cg * 1e6 / G["slow"])
        p(f"  {Z['label']}: L = {G['L']:.0f} mm, pw = {G['pw']:.0f} mm, slow = {G['slow']:.4g} (1 s of the page = {1e6 / G['slow']:.1f} us)")
        for i, (s_, row) in enumerate(zip(tour_of(key, brs, flat), TG[key])):
            def at(st):
                return (f"{st[0]:.3g} kHz: c_p {st[1]:.2f}, c_g {st[2]:.2f} km/s, lambda {2e3 * np.pi / st[3]:.0f} mm;"
                        f" crosses in {cross(st[2]):.1f} s, crests {st[0] * 1e3 / G['slow']:.2f} Hz, c_p/c_g {st[1] / st[2]:.2f}")
            p(f"    stop {i + 1}, wave 1: {brs[s_['b1']]['nm']}, {at(row['w1'])}")
            p(f"            wave 2: {brs[s_['b2']]['nm']}, {at(row['wa'])}")
            p(f"                    gliding to {at(row['w2'])}")
        r0 = TG[key][0]
        p(f"    the first stop's wave 1 takes {cross(r0['w1'][2]) / cross(r0['w2'][2]):.2f} times as long as wave 2 to cross"
          f" (c_g {r0['w1'][2]:.2f} and {r0['w2'][2]:.2f} km/s)")
    p("  The first stop of each section is the caption's comparison: one mode low in frequency, where the")
    p("  whole section moves, and high, where the motion gathers at the surfaces (or in the thin walls).")
    p("  Tour: 16 s on the first stop, then 18 s a stop: markers arrive, wave 2 glides up its curve over 8 s, a")
    p("  hold, 1 s of rest between modes; each stop launches both packets anew from the left end.")
    p("")
    p("THE PLATE AS A PLATE")
    p("  The plate's waves run along a wide, thin slab in an oblique view seen from above (its depth drawn at")
    p(f"  {SECTIONS['plate']['strip']['d']} of the width, at {SECTIONS['plate']['strip']['a']:g} degrees): {PLATE_D:g} mm thick and"
      f" {40 * SECTIONS['plate']['strip']['ys']:.0f} mm wide, the slice's width drawn {SECTIONS['plate']['strip']['ys']:g} times over (the plate")
    p("  is uniform across its width, so the slice's mode shape is the plate's). Its top face is lit by |u| at the")
    p("  surface, the same across the width: the crests are straight lines across the plate, for Lamb waves")
    p("  (u_x, u_z: the top face and the near edge heave) and SH waves (u_y: the top face's lines along x sway")
    p("  across). The section view above it shows the computed shape through the thickness.")
    p("")
    p("INTERACTION")
    p("  The section switcher over (b) (a radio group: arrows move and choose) changes the window: the old")
    p("  frequency ticks fade before the new arrive, the fundamental curves morph at the same share of either")
    p("  window, the higher order curves cross fade, the markers glide and the waves fade over (0.8 s of wall")
    p("  time). A wave keeps its kind (bending, axial, torsional) at the same share of the new window, or takes")
    p("  the curve nearest in c_p; its packet keeps its share of the drawn length. The tour starts again on")
    p("  the new section. Hover names a curve and gives f, wavelength, c_p and c_g there; a marker or its thumb")
    p("  drags along its curve (on a backward-wave branch, to the crossing nearest the wave), the arrows step")
    p("  it (1 kHz on a 200 kHz window, in proportion on the others), up and down move it to the next curve.")
    p("")
    p("PAYLOAD")
    p(f"  nf-dispersion.html {sizes['page'] / 1024:.0f} KB: the engine, this script and all five sections inside (no request is")
    p("  made when a section is chosen); the nf-dispersion-<section>.json files are neither written nor read.")
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
    p("")
    p("compute: " + ", ".join(f"{SECTIONS[k]['label']} {Rs[k]['time']:.0f} s" for k in ORDER) + " (this shared machine)")
    return "\n".join(L) + "\n"


POSTER = 20 / 3      # s: the first stop, both packets at the middle of the drawn length, the intro long over
TITLE = "Figure 4: Schematic dispersion curves for guided waves in a beam"
ARIA = ("Phase velocity against frequency for steel waveguides computed with a SAFE model: bending, axial and "
        "torsional modes start at zero frequency, higher order modes cut on above a threshold and approach the "
        "shear and Rayleigh speeds. Two waves marked 1 and 2 are shown as their cross sections and along the "
        "waveguide: at low frequency the whole section moves, at high frequency the motion gathers at the surfaces. "
        "Along the waveguide each wave runs as packets whose envelope moves at its group velocity while the crests "
        "inside move at its phase velocity, on one clock per section. "
        "The cross section can be switched between a square bar, an IPE 80 I-beam, a 60E1 rail, a schedule 40 pipe "
        "and a plate, each over its own frequency range; the markers can be dragged along the curves or moved with "
        "the arrow keys, and Space pauses the waves.")
HEIGHT = 880


def build_page(Rs=None):
    """The sweeps (cached), the sections' blobs and the page. Returns (Rs, page path, blobs)."""
    Rs = Rs or {key: compute_section(key) for key in ORDER}
    blobs = {key: section_blob(key, Rs[key]) for key in ORDER}
    b64 = {key: base64.b64encode(blobs[key]).decode("ascii") for key in ORDER}
    for key, s_ in b64.items():                  # the site's check for his private details reads text files
        if re.search(r"gmail|300\W{0,3}4065", s_, re.I):
            raise RuntimeError(f"the {key} blob's base64 happens to spell a private pattern")
    data = {"cmax": CP_MAX / 1e3, "ct": sm.C_T / 1e3, "cr": sm.C_R / 1e3, "poster": POSTER,
            "secs": [{"key": k, "label": SECTIONS[k]["label"]} for k in ORDER], "steel": STEEL, "blobs": b64}
    path = common.build_html(NAME, TITLE, ARIA, 1000, HEIGHT, data, JS)
    return Rs, path, blobs


def plate_text(refs, convs, SV):
    """The plate's independent checks and the page's solver against scipy for every section
    (dispersion_plate.check.txt), from the full report's parts."""
    L = ["Plate checks and the browser solver (dispersion.py; the full report is dispersion.check.txt)", ""]
    L += refs["plate"]["lines"] + ["  MESH (plate)"] + convs["plate"]["lines"] + [""]
    L.append("THE PAGE'S SOLVER (its script under node) AGAINST SCIPY ON THE SAME MESH, EVERY SECTION")
    if "skipped" in SV:
        L.append(f"  skipped: {SV['skipped']}")
    else:
        for key in ORDER:
            v = SV[key]
            L.append(f"  {SECTIONS[key]['label']:7s} {v['n']:3d} states: max |w_page/w_scipy - 1| = {v['ew']:.1e}, max (1 - MAC) ="
                     f" {v['em']:.1e}, Sturm count wrong or rejected: {v['bad']}, {v['ms']:.2f} ms a solve (node)")
    return "\n".join(L) + "\n"


def branches_text(Rs, refs, text_):
    """The branch count audit (dispersion_branches.check.txt): each section's drawn branches against
    its reference, from the full report."""
    L = ["Displayed branch count audit (dispersion.py; the full report is dispersion.check.txt)",
         f"Each section over its own frequency window and c_p up to {CP_MAX / 1e3:g} km/s; the window's end lies in a gap",
         "between the frequencies where branches enter it, so every branch drawn enters well before the end and",
         "none is about to (in the bar three branches cut on below its end but enter only above it: not drawn).", ""]
    L += ["SUMMARY"] + text_.split("SUMMARY\n", 1)[1].split("\n\n", 1)[0].split("\n") + [""]
    starts = {"bar": "THE COUNT", "ibeam": "branches below", "rail": "branches below", "pipe": "branches below",
              "plate": "exact cut-ons below"}
    for key in ORDER:
        lines = refs[key]["lines"]
        i0 = next(i for i, l in enumerate(lines) if starts[key] in l)
        L.append(f"{SECTIONS[key]['label']}:")
        for l in lines[i0:]:
            if not l.strip() or l.strip().startswith(("SAFE against", "T(0,1)")):
                break
            L.append(l)
        L.append("")
    return "\n".join(L)


def page_perf():
    """Headless Chromium: for each section, the time from choosing it to its first frame drawn (its
    data read, its classes assembled, its two waves solved: what a reader waits for), and the time of
    a frame in the first glide (wave 2 at a wavenumber not solved before: one state solved, both
    beams drawn), the heaviest frame of the tour."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = {}
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{NAME}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 672, "height": 1400})
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?still")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=60000)
            for key in ORDER:
                ms = pg.evaluate("""async key => {
                  if (key !== CUR.key) { delete LOADED[key]; delete PENDING[key]; }
                  CACHE.clear(); HF.clear(); XS.clear(); LAST[0] = LAST[1] = null; t = POSTER_T;
                  const t0 = performance.now();
                  await setSectionNow(key);
                  const t1 = performance.now();
                  t = TOUR.off + T1 + TG0 + 3; render();
                  const t2 = performance.now();
                  t += 1 / 60; render();
                  const t3 = performance.now();
                  return {switch: t1 - t0, frame: t3 - t2};
                }""", key)
                out[key] = ms
            if errs:
                raise RuntimeError(f"page errors: {errs}")
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    Rs, path, blobs = build_page()
    sizes = {"page": os.path.getsize(path)}
    print("page:", path, sizes["page"], "bytes")
    if "--page" in sys.argv:
        return
    refs = {"bar": ref_bar(Rs["bar"]), "ibeam": ref_ibeam(Rs["ibeam"]), "rail": ref_rail(Rs["rail"]),
            "pipe": ref_pipe(Rs["pipe"]), "plate": ref_plate(Rs["plate"])}
    convs = {}
    for key in ORDER:
        C = mesh_conv(key, Rs[key])
        lines, q = conv_lines(key, Rs[key], C)
        convs[key] = dict(C, lines=lines, **q)
        print(key, "mesh:", q)
    # the page's own checks (node, Chromium), kept with the page they ran on: --text writes the
    # report again from them alone, while the page is unchanged
    keep = os.path.join(tempfile.gettempdir(), f"nf-{NAME}-checks.pkl")
    with open(path, "rb") as fh:
        page_hash = hashlib.sha1(fh.read()).hexdigest()
    got = None
    if "--text" in sys.argv and os.path.exists(keep):
        with open(keep, "rb") as fh:
            got = pickle.load(fh)
        if got.get("page") != page_hash:
            raise RuntimeError("--text: the page changed since its checks ran; run the full check")
    if got is None:
        SV = check_solver_all(Rs)
        print("page solver:", {k: (v["ew"], v["bad"], v["ms"]) for k, v in SV.items()} if "skipped" not in SV else SV)
        TG = tour_group(Rs)
        perf = page_perf()
        print("perf:", perf)
        look = common.still(NAME)          # the bar's poster, and the overlap check to it (raises on a collision)
        ov = overlaps_all(tour_times())
        ovl = overlaps_all([.9, POSTER, 20, 29, 40], live=True)
        MS = measure_screen(axial_dip(Rs["bar"]))
        print("on screen:", MS)
        got = dict(page=page_hash, SV=SV, TG=TG, perf=perf, look=look, ov=ov, ovl=ovl, MS=MS)
        with open(keep, "wb") as fh:
            pickle.dump(got, fh)
    SV, TG, perf, look, ov, ovl, MS = (got[k] for k in ("SV", "TG", "perf", "look", "ov", "ovl", "MS"))
    text_ = check_text(Rs, refs, convs, SV, sizes, ov, ovl, TG, MS, perf)
    with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text_)
    for nm, t_ in ((f"{NAME}_branches.check.txt", branches_text(Rs, refs, text_)),
                   (f"{NAME}_plate.check.txt", plate_text(refs, convs, SV))):
        with open(os.path.join(HERE, nm), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(t_)
    print(text_)
    print("still:", look)
    bad = {k: v for k, v in {**ov, **{"live " + a: b for a, b in ovl.items()}}.items() if v}
    if bad:
        raise RuntimeError("collisions: " + json.dumps(bad)[:3000])


if __name__ == "__main__":
    main()
