"""A semi-analytical finite element (SAFE) model of a solid rectangular steel
bar: the one model behind Figures 4 and 5 (dispersion.py, safe.py). The bar
of both figures is the 20 x 20 mm square of B, H below, meshed 16 x 16 (Q9
elements of 1.25 mm, dispersion.NE_BAR); any b x h rectangle can be built.

The cross-section (y, z) is meshed with 9-node quadratic quadrilaterals (Q9),
three displacements per node (ux along the bar, uy, uz in the section). Along
the bar axis x the field is the harmonic term

    u(x, y, z, t) = U(y, z) exp(i (k x - w t)).

The cross-section's strain energy then gives, for each real wavenumber k,

    [K1 + i k K2 + k^2 K3 - w^2 M] U = 0,      K2 antisymmetric.

Writing the axial dof as U_x = i V_x (the standard scaling) turns this into a
real symmetric pencil [K1 + k K2s + k^2 K3 - w^2 M] V = 0, solved for w with
scipy.linalg.eigh. The bar's two mirror planes (y = 0, z = 0) split every mode
into one of four symmetry classes, each solved on its own orthonormal
symmetry-adapted basis. The lowest branch of each class starts at w = 0 and is
one of the four fundamental modes:

    (+, +) axial, (+, -) vertical bending (uz), (-, +) lateral bending (uy),
    (-, -) torsional;

every other branch cuts on at a finite frequency w(k -> 0) > 0. On the square
(b = h) the two bending classes have the same frequencies: one bending pair.
"""
import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
from scipy.optimize import brentq

# steel, 20 x 20 mm (width b along y, height h along z): Figure 4's square bar
E, NU, RHO = 210e9, 0.29, 7850.0
B, H = 0.020, 0.020

MU = E / (2 * (1 + NU))
LAM = E * NU / ((1 + NU) * (1 - 2 * NU))
C_L = np.sqrt((LAM + 2 * MU) / RHO)          # dilatational (P) wave speed
C_T = np.sqrt(MU / RHO)                      # shear wave speed
C_0 = np.sqrt(E / RHO)                       # rod speed

CLASSES = {"axial": (1, 1), "vertical": (1, -1), "lateral": (-1, 1), "torsional": (-1, -1)}


def rayleigh_speed(nu=NU, ct=C_T):
    """Root of the Rayleigh equation (2 - x^2)^2 = 4 sqrt(1 - x^2) sqrt(1 - kappa x^2),
    x = c_R / c_T, kappa = (c_T / c_L)^2."""
    kap = (1 - 2 * nu) / (2 * (1 - nu))
    f = lambda x: (2 - x * x) ** 2 - 4 * np.sqrt(1 - x * x) * np.sqrt(1 - kap * x * x)
    return brentq(f, 0.5, 1 - 1e-12, xtol=1e-15) * ct


C_R = rayleigh_speed()


def section_constants(b=B, h=H, nu=NU):
    """Area, second moments, polar moment and the Saint-Venant torsion constant
    J of the b x h rectangle (the classical series, b <= h)."""
    A = b * h
    Iy = b * h ** 3 / 12          # about y: vertical bending (uz)
    Iz = h * b ** 3 / 12          # about z: lateral bending (uy)
    s = sum(np.tanh(n * np.pi * h / (2 * b)) / n ** 5 for n in range(1, 400, 2))
    J = h * b ** 3 / 3 * (1 - 192 / np.pi ** 5 * (b / h) * s)
    return dict(A=A, Iy=Iy, Iz=Iz, Ip=Iy + Iz, J=J)


def mesh(ny, nz, b=B, h=H):
    """ny x nz Q9 elements on [-b/2, b/2] x [-h/2, h/2]. Nodes on a
    (2ny+1) x (2nz+1) grid, index j*(2ny+1) + i (i along y, j along z);
    local node l = 3*bb + a is grid node (2ey + a, 2ez + bb)."""
    gy = np.linspace(-b / 2, b / 2, 2 * ny + 1)
    gz = np.linspace(-h / 2, h / 2, 2 * nz + 1)
    Y, Z = np.meshgrid(gy, gz)
    nodes = np.column_stack([Y.ravel(), Z.ravel()])
    nyn = 2 * ny + 1
    el = np.array([[(2 * ez + bb) * nyn + 2 * ey + a for bb in range(3) for a in range(3)]
                   for ez in range(nz) for ey in range(ny)])
    return nodes, el


def _dmat():
    D = np.zeros((6, 6))
    D[:3, :3] = LAM
    D[[0, 1, 2], [0, 1, 2]] = LAM + 2 * MU
    D[[3, 4, 5], [3, 4, 5]] = MU
    return D


def _element(dy, dz):
    """Q9 matrices of one dy x dz rectangle, 3 x 3 Gauss (exact here).
    Strain order: exx, eyy, ezz, gyz, gxz, gxy; dofs 3*l + (x, y, z)."""
    g, w = np.polynomial.legendre.leggauss(3)
    L = lambda s: np.array([s * (s - 1) / 2, 1 - s * s, s * (s + 1) / 2])
    dL = lambda s: np.array([s - 0.5, -2 * s, s + 0.5])
    D = _dmat()
    K1, K2, K3, M = (np.zeros((27, 27)) for _ in range(4))
    for i, xi in enumerate(g):
        for j, eta in enumerate(g):
            N = np.outer(L(eta), L(xi)).ravel()
            Ny = np.outer(L(eta), dL(xi)).ravel() * 2 / dy
            Nz = np.outer(dL(eta), L(xi)).ravel() * 2 / dz
            B1, B2 = np.zeros((6, 27)), np.zeros((6, 27))
            B1[1, 1::3] = Ny                          # eyy = uy,y
            B1[2, 2::3] = Nz                          # ezz = uz,z
            B1[3, 1::3], B1[3, 2::3] = Nz, Ny         # gyz = uy,z + uz,y
            B1[4, 0::3] = Nz                          # gxz = ux,z (+ uz,x)
            B1[5, 0::3] = Ny                          # gxy = ux,y (+ uy,x)
            B2[0, 0::3] = N                           # exx = ux,x    (d/dx -> ik)
            B2[4, 2::3] = N                           # uz,x in gxz
            B2[5, 1::3] = N                           # uy,x in gxy
            dA = w[i] * w[j] * dy * dz / 4
            K1 += B1.T @ D @ B1 * dA
            K2 += (B1.T @ D @ B2 - B2.T @ D @ B1) * dA
            K3 += B2.T @ D @ B2 * dA
            Nm = np.zeros((3, 27))
            for c in range(3):
                Nm[c, c::3] = N
            M += RHO * Nm.T @ Nm * dA
    # i-scaling of the axial dof: K2 -> real symmetric K2s
    comp = np.arange(27) % 3
    S = np.where((comp[:, None] == 0) & (comp[None, :] != 0), 1.0,
                 np.where((comp[:, None] != 0) & (comp[None, :] == 0), -1.0, 0.0))
    return K1, K2 * S, K3, M, K2


class Safe:
    """The SAFE model on an ny x nz mesh of the b x h section."""

    def __init__(self, ny=16, nz=16, b=B, h=H):
        self.ny, self.nz, self.b, self.h = ny, nz, b, h
        self.nodes, self.elems = mesh(ny, nz, b, h)
        nn = len(self.nodes)
        self.ndof = 3 * nn
        k1, k2s, k3, m, k2 = _element(b / ny, h / nz)
        self.K2_antisym_err = np.abs(k2 + k2.T).max() / np.abs(k2).max()
        dofs = (3 * self.elems[:, :, None] + np.arange(3)).reshape(len(self.elems), 27)
        r = np.repeat(dofs, 27, axis=1).ravel()
        c = np.tile(dofs, (1, 27)).ravel()
        asm = lambda ke: sp.csr_matrix((np.tile(ke.ravel(), len(dofs)), (r, c)),
                                       shape=(self.ndof, self.ndof))
        self.K1, self.K2, self.K3, self.M = asm(k1), asm(k2s), asm(k3), asm(m)
        self._cls = {}

    # ------------------------------------------------------------ symmetry
    def mirror(self):
        """Node maps of the two reflections y -> -y and z -> -z."""
        nyn, nzn = 2 * self.ny + 1, 2 * self.nz + 1
        j, i = np.divmod(np.arange(len(self.nodes)), nyn)
        return j * nyn + (nyn - 1 - i), (nzn - 1 - j) * nyn + i

    def basis(self, py, pz):
        """Orthonormal basis (sparse, ndof x m) of the displacements with
        R_y u = py u and R_z u = pz u, where (R_y u)(node) = S_y u(mirror_y node)
        and S_y = diag(1, -1, 1), S_z = diag(1, 1, -1)."""
        my, mz = self.mirror()
        sy, sz = np.array([1, -1, 1]), np.array([1, 1, -1])
        nyn = 2 * self.ny + 1
        j, i = np.divmod(np.arange(len(self.nodes)), nyn)
        reps = np.flatnonzero((i <= self.ny) & (j <= self.nz))
        rows, cols, vals, col = [], [], [], 0
        for n in reps:
            for c in range(3):
                v = {}
                for node, s in ((n, 1), (my[n], py * sy[c]), (mz[n], pz * sz[c]),
                                (my[mz[n]], py * pz * sy[c] * sz[c])):
                    v[3 * node + c] = v.get(3 * node + c, 0) + s
                v = {d: s for d, s in v.items() if s != 0}
                if not v:
                    continue
                nrm = np.sqrt(sum(s * s for s in v.values()))
                for d, s in v.items():
                    rows.append(d); cols.append(col); vals.append(s / nrm)
                col += 1
        return sp.csr_matrix((vals, (rows, cols)), shape=(self.ndof, col))

    def cls(self, name):
        if name not in self._cls:
            Q = self.basis(*CLASSES[name])
            proj = lambda A: (Q.T @ A @ Q).toarray()
            self._cls[name] = (Q, proj(self.K1), proj(self.K2), proj(self.K3), proj(self.M))
        return self._cls[name]

    # ------------------------------------------------------------ solve
    def solve(self, name, k, n):
        """The n lowest (w, V) of class `name` at wavenumber k (rad/m): w in
        rad/s, V the full-length real eigenvectors (columns), U_x = i V_x."""
        Q, k1, k2, k3, m = self.cls(name)
        w2, v = sla.eigh(k1 + k * k2 + k * k * k3, m, subset_by_index=[0, n - 1],
                         driver="gvx")
        return np.sqrt(np.clip(w2, 0, None)), Q @ v

    def omegas(self, name, k, n):
        Q, k1, k2, k3, m = self.cls(name)
        w2 = sla.eigh(k1 + k * k2 + k * k * k3, m, eigvals_only=True,
                      subset_by_index=[0, n - 1], driver="gvx")
        return np.sqrt(np.clip(w2, 0, None))

    def sweep(self, name, ks, n):
        """w[k index, branch] of the n lowest branches (sorted within the class)."""
        return np.array([self.omegas(name, k, n) for k in ks])

    # ------------------------------------------------------------ fields
    def split(self, v):
        """Nodal (ux, uy, uz) amplitudes of an eigenvector: ux is the
        quadrature part (U_x = i V_x), uy, uz in phase."""
        return v[0::3], v[1::3], v[2::3]

    def boundary(self):
        """Grid-node loop around the section (counter-clockwise from (-b/2, -h/2))."""
        nyn, nzn = 2 * self.ny + 1, 2 * self.nz + 1
        idx = lambda i, j: j * nyn + i
        loop = [idx(i, 0) for i in range(nyn)]
        loop += [idx(nyn - 1, j) for j in range(1, nzn)]
        loop += [idx(i, nzn - 1) for i in range(nyn - 2, -1, -1)]
        loop += [idx(0, j) for j in range(nzn - 2, 0, -1)]
        return np.array(loop)


def beam_speeds(k, sec=None):
    """Closed-form phase velocities (m/s) at wavenumber k (rad/m) for the
    comparisons in the check files: Euler-Bernoulli and Timoshenko bending
    (both planes), the rod (and Love's rod), and Saint-Venant torsion."""
    s = sec or section_constants()
    A = s["A"]
    out = {}
    kap = 10 * (1 + NU) / (12 + 11 * NU)          # Cowper, rectangle
    for plane, I in (("vertical", s["Iy"]), ("lateral", s["Iz"])):
        out[plane + "_EB"] = k * np.sqrt(E * I / (RHO * A))
        a = RHO * A * RHO * I
        bq = -(RHO * A * (E * I * k ** 2 + kap * MU * A) + RHO * I * kap * MU * A * k ** 2)
        cq = kap * MU * A * E * I * k ** 4
        w2 = (-bq - np.sqrt(bq * bq - 4 * a * cq)) / (2 * a)
        out[plane + "_Timo"] = np.sqrt(w2) / k
    out["axial_rod"] = C_0 + 0 * k
    out["axial_Love"] = C_0 / np.sqrt(1 + NU ** 2 * k ** 2 * s["Ip"] / A)
    out["torsional_SV"] = np.sqrt(MU * s["J"] / (RHO * s["Ip"])) + 0 * k
    return out
