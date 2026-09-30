"""The elastic model behind the NDT figure of the SHM article (shm_ndt.py).

Plane-strain elastodynamics in velocity-stress form on a staggered grid
(Virieux 1986), second order in space and time; voids are cells of zero
density and stiffness, which is the EFIT of Fellinger et al. (1995), the
scheme of the waves guide's Figure 11 (bulk_ut.py), written again here so
that the two figures do not depend on each other's files:

    rho dv_x/dt = ds_xx/dx + ds_xz/dz        ds_xx/dt = (lam + 2 mu) dv_x/dx + lam dv_z/dz
    rho dv_z/dt = ds_xz/dx + ds_zz/dz        ds_zz/dt = lam dv_x/dx + (lam + 2 mu) dv_z/dz
                                             ds_xz/dt = mu (dv_x/dz + dv_z/dx)

Units: mm, us, and stresses in units of the source's peak traction. Every
face of the steel and of a crack is traction free: the cells outside are
void, a face between steel and void takes half the density, and a corner
touching a void gets zero shear modulus (the harmonic mean).
"""
import hashlib
import os
import sys
import tempfile
import time

import numpy as np

# numba probes for a package named `coverage` when it loads; keep this
# folder (whose scripts are not that package) off the path while it does
_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = sys.path[:]
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
from numba import njit, prange  # noqa: E402
sys.path[:] = _PATH

CL, CT = 5.9, 3.23              # steel, mm/us (5900, 3230 m/s)
RHO_SI = 7850.0                 # kg/m^3
PAD = 2                         # void cells around the steel
CFL = 0.6                       # c_L dt / dx (limit 1/sqrt 2)


def burst(t, f0, nc):
    """A Hann windowed tone burst of nc cycles at f0 (MHz), starting at t = 0 (us)."""
    T = nc / f0
    on = (t >= 0) & (t <= T)
    return np.where(on, np.sin(2 * np.pi * f0 * t) * 0.5 * (1 - np.cos(2 * np.pi * f0 * t / nc)), 0.0)


@njit(parallel=True, fastmath=True)
def _step_v(vx, vz, txx, tzz, txz, bx, bz, k):
    nx, nz = txx.shape
    for i in prange(1, nx):
        for j in range(nz):
            vx[i, j] += k * bx[i, j] * (txx[i, j] - txx[i - 1, j] + txz[i, j + 1] - txz[i, j])
    for i in prange(nx):
        for j in range(1, nz):
            vz[i, j] += k * bz[i, j] * (txz[i + 1, j] - txz[i, j] + tzz[i, j] - tzz[i, j - 1])


@njit(parallel=True, fastmath=True)
def _step_t(vx, vz, txx, tzz, txz, l2m, lam, muc, k):
    nx, nz = txx.shape
    for i in prange(nx):
        for j in range(nz):
            dvx = vx[i + 1, j] - vx[i, j]
            dvz = vz[i, j + 1] - vz[i, j]
            txx[i, j] += k * (l2m[i, j] * dvx + lam[i, j] * dvz)
            tzz[i, j] += k * (lam[i, j] * dvx + l2m[i, j] * dvz)
    for i in prange(1, nx):
        for j in range(1, nz):
            txz[i, j] += k * muc[i, j] * (vx[i, j] - vx[i, j - 1] + vz[i, j] - vz[i - 1, j])


def media(solid):
    """EFIT coefficients from a boolean map of steel cells (density 1)."""
    nx, nz = solid.shape
    rho = solid.astype(float)
    mu, l2m = rho * CT ** 2, rho * CL ** 2
    rp = np.zeros((nx + 2, nz)); rp[1:-1] = rho
    rb = 0.5 * (rp[:-1] + rp[1:])
    bx = np.where(rb > 0, 1 / np.where(rb > 0, rb, 1), 0)
    rp = np.zeros((nx, nz + 2)); rp[:, 1:-1] = rho
    rb = 0.5 * (rp[:, :-1] + rp[:, 1:])
    bz = np.where(rb > 0, 1 / np.where(rb > 0, rb, 1), 0)
    mp = np.zeros((nx + 2, nz + 2)); mp[1:-1, 1:-1] = mu
    c4 = [mp[:-1, :-1], mp[1:, :-1], mp[:-1, 1:], mp[1:, 1:]]
    ok = np.logical_and.reduce([c > 0 for c in c4])
    muc = np.where(ok, 4 / sum(1 / np.where(c > 0, c, 1) for c in c4), 0)
    f = lambda a: np.ascontiguousarray(a, dtype=np.float32)
    return f(bx), f(bz), f(l2m), f(l2m - 2 * mu), f(muc)


def block(width, depth, dx):
    """A steel block width x depth (mm) with PAD void cells around it, and
    the cell centres (x, z) of its cells, mm from its top left corner."""
    nbx, nbz = int(round(width / dx)), int(round(depth / dx))
    solid = np.zeros((nbx + 2 * PAD, nbz + 2 * PAD), bool)
    solid[PAD:PAD + nbx, PAD:PAD + nbz] = True
    X, Z = np.meshgrid((np.arange(nbx) + .5) * dx, (np.arange(nbz) + .5) * dx, indexing="ij")
    return solid, X, Z


def cut(solid, X, Z, crack):
    """Cut an elliptical void (a crack): crack = dict(x, z, a, b, tilt), the
    centre (mm), the semi-axes along and across it (mm), and its tilt in
    degrees (the right end up)."""
    th = np.radians(crack["tilt"])
    u = (X - crack["x"]) * np.cos(th) - (Z - crack["z"]) * np.sin(th)
    v = (X - crack["x"]) * np.sin(th) + (Z - crack["z"]) * np.cos(th)
    inside = (u / crack["a"]) ** 2 + (v / crack["b"]) ** 2 <= 1
    solid[PAD:PAD + X.shape[0], PAD:PAD + X.shape[1]] &= ~inside
    return int(inside.sum())


def cells(x0, w, dx):
    """The padded-grid column indices of a face from x0 to x0 + w (mm)."""
    i0 = PAD + int(round(x0 / dx))
    return np.arange(i0, i0 + max(1, int(round(w / dx))))


def run(solid, src, recs, nsteps, dx, dt, drive, point=None):
    """March the model nsteps of dt.

    Transmission: a uniform normal traction drive(t) pressing on the top face
    over the columns `src` (the probe), or, with point = (i, j), a moment
    source in the steel: the stresses s_xx and s_zz at cell (i, j) take the
    increment drive(t) dt each step (an opening crack, a centre of dilation).
    Reception: the mean v_z over the top face of each column group in
    `recs`, sampled after every velocity update, at times (n + 1/2) dt.
    """
    nx, nz = solid.shape
    bx, bz, l2m, lam, muc = media(solid)
    vx = np.zeros((nx + 1, nz), np.float32); vz = np.zeros((nx, nz + 1), np.float32)
    txx = np.zeros((nx, nz), np.float32); tzz = np.zeros((nx, nz), np.float32)
    txz = np.zeros((nx + 1, nz + 1), np.float32)
    k = np.float32(dt / dx)
    s = drive(np.arange(nsteps) * dt).astype(np.float32)
    rec = np.zeros((len(recs), nsteps))
    for n in range(nsteps):
        if point is None:
            tzz[src, PAD - 1] = -s[n]          # traction on the top face (void row above it)
        _step_v(vx, vz, txx, tzz, txz, bx, bz, k)
        for g, idx in enumerate(recs):
            rec[g, n] = vz[idx, PAD].mean()
        if point is not None:
            txx[point] += s[n] * dt
            tzz[point] += s[n] * dt
        _step_t(vx, vz, txx, tzz, txz, l2m, lam, muc, k)
        if n % 500 == 0 and not np.isfinite(vz[nx // 2, PAD]):
            raise FloatingPointError("unstable")
    return rec


def cached(tag, key, fn):
    """fn()'s arrays, kept in the temp directory under tag and a hash of key."""
    h = hashlib.sha1(repr((tag, key, CL, CT, CFL, 1)).encode()).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), f"numfig-shm-{tag}-{h}.npz")
    if os.path.exists(path):
        with np.load(path) as z:
            return tuple(z[f"a{i}"] for i in range(len(z.files)))
    t0 = time.time()
    out = fn()
    print(f"  {tag}: {time.time() - t0:.1f} s", flush=True)
    np.savez(path, **{f"a{i}": np.asarray(a) for i, a in enumerate(out)})
    return tuple(np.asarray(a) for a in out)
