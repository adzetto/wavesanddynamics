"""Figure 11, conventional (bulk wave) ultrasonic testing, redrawn from a 2D
elastic finite-difference time-domain model of a steel block.

The model is plane-strain elastodynamics in velocity-stress form on a
staggered grid (Virieux 1986), second order in space and time; with voids
as cells of zero density and stiffness it is the EFIT of Fellinger et al.
(1995), the usual scheme for ultrasonic testing:

    rho dv_x/dt = ds_xx/dx + ds_xz/dz        ds_xx/dt = (lam + 2 mu) dv_x/dx + lam dv_z/dz
    rho dv_z/dt = ds_xz/dx + ds_zz/dz        ds_zz/dt = lam dv_x/dx + (lam + 2 mu) dv_z/dz
                                             ds_xz/dt = mu (dv_x/dz + dv_z/dx)

v_x and v_z live on cell faces, s_xx and s_zz at cell centres, s_xz at cell
corners. Every face of the block and of the flaw is traction free: the cells
outside are void, a face between steel and void takes half the density, and
a corner touching a void gets zero shear modulus (the harmonic mean).

A probe transmits by pressing on the top face with a uniform normal traction
p(t), a 5 MHz, 3 cycle Hann burst, and receives the mean normal velocity
over the same face. (a) and (b) are one run with a 10 mm probe over the
flaw. (c) and (d) are 32 runs, one per element of a 32 element array (full
matrix capture), imaged with the total focusing method.

Writes content/anim/nf-bulk-ut.html (+ -field.png, -tfm.png), the still
nf-bulk-ut.webp, and tools/numfig/bulk_ut.check.txt. The simulations are
cached in the temp directory (about 3 minutes on 16 threads without it).
"""
import hashlib
import io
import os
import sys
import tempfile
import time

import numpy as np
from PIL import Image
from scipy.signal import hilbert

# numba probes for the `coverage` package when it loads; this folder's
# coverage.py (Figure 13) is not that package, so load numba without it
_HERE = os.path.dirname(os.path.abspath(__file__))
_PATH = sys.path[:]
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
from numba import njit, prange  # noqa: E402
sys.path[:] = _PATH

import common  # noqa: E402

# ------------------------------------------------------------------ model
# units: mm, us, and stresses in units of the probe's peak pressure p0
CL, CT = 5.9, 3.23                  # steel, mm/us (5900, 3230 m/s)
RHO_SI = 7850.0                     # kg/m^3, for the report
F0, NC = 5.0, 3                     # burst: MHz, cycles
WB, DB = 50.0, 25.0                 # block, mm
FLAW = dict(x=29.0, z=12.0, a=1.5, b=0.6, tilt=12.0)   # void; tilt: major axis, right end up
PROBE = dict(x=29.0, w=10.0)        # single probe over the flaw
NE, PITCH_C, EW_C = 32, 15, 13      # array: elements, pitch and width in cells of 0.04 mm
DX, DT = 0.04, 1 / 240              # grid, mm and us (CFL number 0.615)
T_PE, T_FMC = 10.0, 11.0            # recorded windows, us
FRAME_EVERY, REC_EVERY = 12, 2      # 0.05 us per frame, 1/120 us per sample
BOX = 5                             # 5 x 5 cells per field pixel (0.2 mm)
FCLIP = 0.5                         # field colour range, +- p0
TFM_DX, TFM_X, TFM_Z = 0.1, 14.0, 27.0
DR = 40.0                           # dB stored in the TFM atlas
PAD = 2


def burst(t):
    T = NC / F0
    on = (t >= 0) & (t <= T)
    return np.where(on, np.sin(2 * np.pi * F0 * t) * 0.5 * (1 - np.cos(2 * np.pi * F0 * t / NC)), 0.0)


T0 = 0.5 * NC / F0                  # centre of the burst: time zero of (b) and of the TFM
P0 = float(np.abs(burst(np.linspace(0, NC / F0, 200001))).max())


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


def _media(solid):
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


def _run(solid, src, recs, nsteps, dx, dt, frame=None):
    """Transmit on the surface faces of the cells `src` (top row of steel at
    j = PAD), record the mean v_z on each group of `recs` every REC_EVERY
    steps (time (2m + 1/2) dt), and call frame(txx, tzz) after every
    FRAME_EVERY steps (time 12 k dt)."""
    nx, nz = solid.shape
    bx, bz, l2m, lam, muc = _media(solid)
    vx = np.zeros((nx + 1, nz), np.float32); vz = np.zeros((nx, nz + 1), np.float32)
    txx = np.zeros((nx, nz), np.float32); tzz = np.zeros((nx, nz), np.float32)
    txz = np.zeros((nx + 1, nz + 1), np.float32)
    k = np.float32(dt / dx)
    s = burst(np.arange(nsteps) * dt) / P0
    rec = np.zeros((len(recs), nsteps // REC_EVERY))
    frames = []
    for n in range(nsteps):
        tzz[src, PAD - 1] = -s[n]           # traction on the top face (void row above it)
        _step_v(vx, vz, txx, tzz, txz, bx, bz, k)
        if n % REC_EVERY == 0:
            for g, idx in enumerate(recs):
                rec[g, n // REC_EVERY] = vz[idx, PAD].mean()
        _step_t(vx, vz, txx, tzz, txz, l2m, lam, muc, k)
        if frame is not None and (n + 1) % FRAME_EVERY == 0:
            frames.append(frame(txx, tzz))
        if n % 400 == 0 and not np.isfinite(vz[nx // 2, PAD]):
            raise FloatingPointError("unstable")
    return rec, frames


def _block(dx, flaw=True):
    nbx, nbz = int(round(WB / dx)), int(round(DB / dx))
    solid = np.zeros((nbx + 2 * PAD, nbz + 2 * PAD), bool)
    solid[PAD:PAD + nbx, PAD:PAD + nbz] = True
    if flaw:
        X, Z = np.meshgrid((np.arange(nbx) + .5) * dx, (np.arange(nbz) + .5) * dx, indexing="ij")
        solid[PAD:PAD + nbx, PAD:PAD + nbz] &= ~_in_flaw(X, Z)
    return solid, nbx, nbz


def _in_flaw(X, Z):
    th = np.radians(FLAW["tilt"])
    dx_, dz_ = X - FLAW["x"], Z - FLAW["z"]
    u = dx_ * np.cos(th) - dz_ * np.sin(th)
    v = dx_ * np.sin(th) + dz_ * np.cos(th)
    return (u / FLAW["a"]) ** 2 + (v / FLAW["b"]) ** 2 <= 1


def flaw_outline(n=721):
    """The void's boundary, (x, z) in mm, as the model draws it."""
    th, ph = np.radians(FLAW["tilt"]), np.linspace(0, 2 * np.pi, n)
    u, v = FLAW["a"] * np.cos(ph), FLAW["b"] * np.sin(ph)
    return FLAW["x"] + u * np.cos(th) + v * np.sin(th), FLAW["z"] - u * np.sin(th) + v * np.cos(th)


def pulse_echo(dx=DX, frames=True):
    """(a) and (b): the 10 mm probe over the flaw. Returns the A-scan
    (mean v_z on the probe) and the field p = -(s_xx + s_zz)/2 every 0.05 us."""
    dt = DT * dx / DX
    solid, nbx, nbz = _block(dx)
    i0 = PAD + int(round((PROBE["x"] - PROBE["w"] / 2) / dx))
    src = np.arange(i0, i0 + int(round(PROBE["w"] / dx)))

    def frame(txx, tzz):
        p = -0.5 * (txx[PAD:PAD + nbx, PAD:PAD + nbz] + tzz[PAD:PAD + nbx, PAD:PAD + nbz])
        return p.reshape(nbx // BOX, BOX, nbz // BOX, BOX).mean(axis=(1, 3)).astype(np.float32)

    ns = int(round(T_PE / dt))
    rec, fr = _run(solid, src, [src], ns, dx, dt, frame if frames else None)
    return rec[0], (np.array(fr) if frames else None), dt


def elements(dx=DX):
    """Cell indices (padded grid) and centres (mm from the left face) of the
    32 elements, 13 cells wide at a 15 cell pitch, centred on the block."""
    first = int(round(WB / 2 / dx)) - (NE * PITCH_C) // 2 + (PITCH_C - EW_C) // 2
    els = [PAD + first + PITCH_C * k + np.arange(EW_C) for k in range(NE)]
    cen = np.array([(e.mean() - PAD + .5) * dx for e in els])
    return els, cen


def fmc():
    """(c) and (d): full matrix capture, one run per transmitting element,
    and one run in a half-space (90 x 36 mm, no echo returns within 11 us)
    for the direct waves along the array."""
    solid, _, _ = _block(DX)
    els, cen = elements()
    ns = int(round(T_FMC / DT))
    data = np.zeros((NE, NE, ns // REC_EVERY), np.float32)
    t = time.time()
    for k in range(NE):
        data[k] = _run(solid, els[k], els, ns, DX, DT)[0]
        print(f"  FMC shot {k + 1:2d}/{NE}  {time.time() - t:5.0f} s", flush=True)
    rnx, rnz = int(round(90 / DX)), int(round(36 / DX))
    half = np.zeros((rnx + 2 * PAD, rnz + 2 * PAD), bool); half[PAD:PAD + rnx, PAD:PAD + rnz] = True
    i0 = PAD + int(round(34 / DX))
    rels = [i0 + PITCH_C * k + np.arange(EW_C) for k in range(NE)]
    ref = _run(half, rels[0], rels, ns, DX, DT)[0].astype(np.float32)
    return data, ref, cen


def plane_wave(dx):
    """A near plane wave: a 40 mm probe on a 100 x 25 mm block, no flaw. Its
    back wall echo tests the travel time of the scheme's P wave alone."""
    dt = DT * dx / DX
    nbx, nbz = int(round(100 / dx)), int(round(DB / dx))
    solid = np.zeros((nbx + 2 * PAD, nbz + 2 * PAD), bool)
    solid[PAD:PAD + nbx, PAD:PAD + nbz] = True
    i0 = PAD + int(round(30 / dx))
    src = np.arange(i0, i0 + int(round(40 / dx)))
    return _run(solid, src, [src], int(round(9.5 / dt)), dx, dt)[0][0], dt


def rayleigh_run(dx):
    """A half-space check of the free surface: 60 x 24 mm (nothing returns
    within 8 us), one element transmits at x = 20 mm, two receive 12 and
    18.6 mm away."""
    dt = DT * dx / DX
    nx, nz = int(round(60 / dx)), int(round(24 / dx))
    half = np.zeros((nx + 2 * PAD, nz + 2 * PAD), bool)
    half[PAD:PAD + nx, PAD:PAD + nz] = True
    pc, ew, i0 = int(round(0.6 / dx)), int(round(EW_C * DX / dx)), PAD + int(round(20 / dx))
    grp = [i0 + k * pc + np.arange(ew) for k in (0, 20, 31)]
    rec, _ = _run(half, grp[0], grp[1:], int(round(8 / dt)), dx, dt)
    return rec, dt


def _cached(tag, fn):
    key = hashlib.sha1(repr((tag, CL, CT, F0, NC, WB, DB, FLAW, PROBE, NE, PITCH_C, EW_C, DX, DT,
                             T_PE, T_FMC, BOX, 3)).encode()).hexdigest()[:12]
    path = os.path.join(tempfile.gettempdir(), f"numfig-bulk-ut-{tag}-{key}.npz")
    if os.path.exists(path):
        with np.load(path) as z:
            return tuple(z[f"a{i}"] for i in range(len(z.files)))
    t = time.time()
    out = fn()
    print(f"  {tag}: {time.time() - t:.0f} s")
    np.savez(path, **{f"a{i}": np.asarray(a) for i, a in enumerate(out)})
    return tuple(np.asarray(a) for a in out)


# ------------------------------------------------------------------ analysis
def env_peak(t, s, lo, hi):
    """Time and value of the envelope's maximum in [lo, hi], parabolic refine."""
    e = np.abs(hilbert(s))
    idx = np.where((t >= lo) & (t <= hi))[0]
    m = idx[np.argmax(e[idx])]
    a, b, c = e[m - 1], e[m], e[m + 1]
    d = 0.5 * (a - c) / (a - 2 * b + c)
    return t[m] + d * (t[1] - t[0]), b - 0.25 * (a - c) * d


def rayleigh_speed():
    from scipy.optimize import brentq
    kap = (CT / CL) ** 2
    f = lambda x: (2 - x * x) ** 2 - 4 * np.sqrt(1 - x * x) * np.sqrt(1 - kap * x * x)
    return brentq(f, 0.5, 1 - 1e-12, xtol=1e-14) * CT


@njit(parallel=True)
def _tfm(hr, hi, cen, xs, zs, t0, c, ts0, dts):
    """Per-transmitter complex TFM contributions C_i(x, z) =
    sum_j h_ij(t0 + (|x - e_i| + |x - e_j|)/c), linear interpolation."""
    ne = cen.size
    nt = hr.shape[2]
    out_r = np.zeros((ne, xs.size, zs.size))
    out_i = np.zeros((ne, xs.size, zs.size))
    for a in prange(xs.size):
        r = np.empty(ne)
        for b in range(zs.size):
            for e in range(ne):
                r[e] = np.sqrt((xs[a] - cen[e]) ** 2 + zs[b] ** 2)
            for i in range(ne):
                sr = 0.0
                si = 0.0
                for j in range(ne):
                    f = (t0 + (r[i] + r[j]) / c - ts0) / dts
                    m = int(np.floor(f))
                    if m >= 0 and m + 1 < nt:
                        w = f - m
                        sr += (1 - w) * hr[i, j, m] + w * hr[i, j, m + 1]
                        si += (1 - w) * hi[i, j, m] + w * hi[i, j, m + 1]
                out_r[i, a, b] = sr
                out_i[i, a, b] = si
    return out_r, out_i


def sci_tex(v):
    """v as m x 10^e for the page's math(): 1.1e6 -> 1.1 \\times\\ 10^{6}."""
    e = int(np.floor(np.log10(v)))
    return f"{v / 10 ** e:.3g} \\times\\ 10^{{{e}}}"


def _png(a):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "PNG", optimize=True)
    return b.getvalue()


def _atlas(frames, cols):
    n, h, w = frames.shape
    rows = -(-n // cols)
    out = np.zeros((rows * h, cols * w), np.uint8)
    for k in range(n):
        r, c = divmod(k, cols)
        out[r * h:(r + 1) * h, c * w:(c + 1) * w] = frames[k]
    return out


def main():
    rep = []
    say = lambda s="": (rep.append(s), print(s))

    # ---- (a), (b): pulse echo with the single probe
    ascan, field, dt = _cached("pe", lambda: pulse_echo())
    dt = float(dt)
    ts = (REC_EVERY * np.arange(ascan.size) + 0.5) * dt - T0     # time from the burst's centre
    field = np.concatenate([np.zeros_like(field[:1]), field])      # frame k at 0.05 k us
    # echo times, against 2d/c
    X, Z = flaw_outline(200001)
    under = np.abs(X - PROBE["x"]) <= PROBE["w"] / 2
    d_f = float(Z[under].min())
    x_top = float(X[np.argmin(np.where(under, Z, 1e9))])
    tf_th, tb_th = 2 * d_f / CL, 2 * DB / CL
    tf, af = env_peak(ts, ascan, tf_th - .6, tf_th + .6)
    tb, ab = env_peak(ts, ascan, tb_th - .6, tb_th + .6)
    t_ip, a_ip = env_peak(ts, ascan, -.3, .6)
    norm = np.abs(ascan).max()

    # ---- grid convergence of the echo times (no frames)
    conv = []
    for h in (0.1, 0.05, 0.04, 0.025):
        if h == DX:
            conv.append((h, tf, tb))
            continue
        s, dth = _cached(f"pe{h:g}", lambda h=h: (pulse_echo(h, frames=False)[0], DT * h / DX))
        th = (REC_EVERY * np.arange(s.size) + 0.5) * float(dth) - T0
        conv.append((h, env_peak(th, s, tf_th - .6, tf_th + .6)[0], env_peak(th, s, tb_th - .6, tb_th + .6)[0]))

    pw = {}
    for h in (0.05, 0.04, 0.025):
        s, dth = _cached(f"pw{h:g}", lambda h=h: plane_wave(h))
        th = (REC_EVERY * np.arange(s.size) + 0.5) * float(dth) - T0
        pw[h] = env_peak(th, s, tb_th - .6, tb_th + .6)[0]
    pw_ext = pw[0.025] - (pw[0.05] - pw[0.025]) / 3                  # Richardson, second order

    # ---- (c), (d): full matrix capture and the total focusing method
    data, ref, cen = _cached("fmc", fmc)
    tr = (REC_EVERY * np.arange(data.shape[2]) + 0.5) * DT
    idx = np.abs(np.arange(NE)[:, None] - np.arange(NE)[None, :])
    scat = data.astype(float) - ref.astype(float)[idx]
    recip = np.abs(scat - scat.transpose(1, 0, 2)).max() / np.abs(scat).max()
    h = hilbert(scat, axis=-1)
    xc = cen - WB / 2
    xs = np.round(np.arange(-TFM_X, TFM_X + 1e-9, TFM_DX), 6)
    zs = np.round(np.arange(0, TFM_Z + 1e-9, TFM_DX), 6)
    cr, ci = _tfm(np.ascontiguousarray(h.real), np.ascontiguousarray(h.imag), xc, xs, zs,
                  T0, CL, tr[0], tr[1] - tr[0])
    part = np.abs(np.cumsum(cr + 1j * ci, axis=0))                     # (NE, nx, nz)
    part /= np.arange(1, NE + 1)[:, None, None]                        # mean over transmitters 1 ... k
    peak = part[-1].max()
    db = 20 * np.log10(np.maximum(part / peak, 1e-12))
    fin = part[-1]
    upper = zs < 20
    kf = np.unravel_index(np.argmax(fin[:, upper]), fin[:, upper].shape)
    fx, fz = xs[kf[0]], zs[upper][kf[1]]
    lower = zs >= 20
    bw_z = zs[lower][np.argmax(fin[:, lower].max(axis=0))]
    bw_db = 20 * np.log10(fin[:, lower].max() / peak)
    fl_db = 20 * np.log10(fin[:, upper].max() / peak)
    dist = np.hypot(X - WB / 2 - fx, Z - fz).min()
    # each path's contribution to the flaw's pixel: the fan's opacity in (c)
    rf = np.hypot(fx - xc, fz)
    tau = T0 + (rf[:, None] + rf[None, :]) / CL
    amp = np.abs(np.array([[np.interp(tau[i, j], tr, np.abs(h[i, j])) for j in range(NE)]
                           for i in range(NE)]))
    amp /= amp.max()
    # the Rayleigh wave along a free surface, at two grids: group speed from
    # the envelope peaks, phase speed from the cross-correlation of the pulses
    cr_th = rayleigh_speed()
    ray = []
    for hh in (0.04, 0.02):
        rr, dth = _cached(f"ray{hh:g}", lambda hh=hh: rayleigh_run(hh))
        dth = float(dth)
        tt = (REC_EVERY * np.arange(rr.shape[1]) + 0.5) * dth
        d1, d2 = 20 * 0.6, 31 * 0.6
        a1 = env_peak(tt, rr[0], T0 + d1 / 3.1, T0 + d1 / 2.85)[0]
        a2 = env_peak(tt, rr[1], T0 + d2 / 3.1, T0 + d2 / 2.85)[0]
        g1 = rr[0] * (np.abs(tt - a1) < 0.45)
        g2 = rr[1] * (np.abs(tt - a2) < 0.45)
        xc_ = np.correlate(g2, g1, "full")
        m = np.argmax(xc_)
        sh = m - (g1.size - 1) + 0.5 * (xc_[m - 1] - xc_[m + 1]) / (xc_[m - 1] - 2 * xc_[m] + xc_[m + 1])
        ray.append((hh, (d2 - d1) / (a2 - a1), (d2 - d1) / (sh * (tt[1] - tt[0]))))

    # ---- report
    lam = CL ** 2 - 2 * CT ** 2
    nu = lam / (2 * (lam + CT ** 2))
    E = RHO_SI * (CT * 1e3) ** 2 * (3 * lam + 2 * CT ** 2) / (lam + CT ** 2) / 1e9
    say("Figure 11 (nf-bulk-ut): conventional (bulk wave) ultrasonic testing")
    say("generator: tools/numfig/bulk_ut.py")
    say()
    say("MODEL")
    say("  2D plane-strain elastodynamics, velocity-stress, staggered grid (Virieux 1986),")
    say("  second order in space and time; voids as cells of zero density and stiffness,")
    say("  i.e. EFIT (Fellinger et al. 1995). Elastic, so P, S and Rayleigh waves and mode")
    say("  conversion are all in it. Every face of the block and of the flaw is traction free.")
    say(f"  steel: cL = {CL * 1e3:.0f} m/s, cT = {CT * 1e3:.0f} m/s, rho = {RHO_SI:.0f} kg/m3"
        f"  (nu = {nu:.3f}, E = {E:.1f} GPa)")
    say(f"  block {WB:g} x {DB:g} mm; flaw: elliptical void, centre (x, z) = ({FLAW['x']:g}, {FLAW['z']:g}) mm"
        f" (x from the left face, z down from the top face),")
    say(f"  semi-axes {FLAW['a']:g} x {FLAW['b']:g} mm, major axis inclined {FLAW['tilt']:g} deg (right end up)")
    say(f"  source: uniform normal traction on the probe face, {F0:g} MHz, {NC} cycles, Hann window;"
        f" burst centre t0 = {T0:g} us")
    say("  receiver: mean normal particle velocity v over the same face; (b) plots v/v0, v0 its peak"
        " in the initial pulse")
    say(f"  (a), (b): one probe {PROBE['w']:g} mm wide centred at x = {PROBE['x']:g} mm, over the flaw")
    say(f"  (c), (d): {NE} elements, pitch {PITCH_C * DX:.2f} mm, width {EW_C * DX:.2f} mm, centres"
        f" x = {cen[0]:.2f} ... {cen[-1]:.2f} mm; one run per transmitter (full matrix capture)")
    say(f"  field shown in (a): p = -(s_xx + s_zz)/2 over p0 (peak probe pressure), mean of"
        f" {BOX} x {BOX} cells ({BOX * DX:.1f} mm pixels), colour range +-{FCLIP:g},"
        f" stored in steps of p0/{63 / FCLIP:.0f}")
    say()
    say("GRID")
    lt, ll = CT / F0 / DX, CL / F0 / DX
    fmax = F0 * (1 + 2 / NC)
    say(f"  dx = {DX} mm: {ll:.1f} points per P wavelength and {lt:.1f} per S wavelength at {F0:g} MHz;"
        f" {CL / fmax / DX:.1f} and {CT / fmax / DX:.1f} at {fmax:.1f} MHz (edge of the burst's main lobe)")
    say(f"  dt = {DT * 1e3:.3f} ns; CFL number cL dt/dx = {CL * DT / DX:.3f} (limit 1/sqrt 2 = 0.707)")
    say(f"  block {int(WB / DX)} x {int(DB / DX)} cells; pulse echo {int(T_PE / DT)} steps;"
        f" FMC {NE} runs x {int(T_FMC / DT)} steps; half-space reference 2250 x 900 cells")
    say("  echo times (envelope peaks, from the burst's centre) as the grid is refined:")
    say("    the figure's model (10 mm probe, flaw):")
    for hh, a1, a2 in conv:
        say(f"      dx = {hh:.3f} mm   flaw echo {a1:.4f} us   back wall echo {a2:.4f} us")
    c1, c2, c3 = conv[0][2], conv[1][2], conv[3][2]
    say(f"      back wall, dx halved twice (0.1, 0.05, 0.025 mm): changes {c2 - c1:+.4f} and {c3 - c2:+.4f} us,"
        f" ratio {(c2 - c1) / (c3 - c2):.1f} (4 for second order)")
    say("    a near plane wave (40 mm probe, 100 x 25 mm block, no flaw), back wall echo:")
    say(f"      dx = 0.050 mm {pw[0.05]:.4f} us, 0.040 mm {pw[0.04]:.4f} us, 0.025 mm {pw[0.025]:.4f} us;"
        f" Richardson limit {pw_ext:.4f} us")
    say()
    say("VALIDATION")
    say(f"  1. P wave travel time: the plane wave's back wall echo, extrapolated to dx -> 0, arrives at"
        f" {pw_ext:.4f} us;")
    say(f"     2d/cL = 2 x {DB:g} / {CL} = {tb_th:.4f} us; error {pw_ext - tb_th:+.4f} us"
        f" ({(pw_ext - tb_th) / tb_th * 100:+.3f} %). At the figure's dx = {DX} mm the grid's own"
        f" dispersion delays it {pw[0.04] - pw_ext:+.4f} us ({(pw[0.04] - pw_ext) / tb_th * 100:+.2f} %).")
    say(f"  2. the figure's A scan (b), dx = {DX} mm:")
    say(f"     back wall echo {tb:.4f} us vs 2d/cL = {tb_th:.4f} us: {tb - tb_th:+.4f} us"
        f" ({(tb - tb_th) / tb_th * 100:+.2f} %)")
    say(f"     flaw echo {tf:.4f} us vs 2 d_f/cL = {tf_th:.4f} us, d_f = {d_f:.3f} mm the top of the void under"
        f" the probe (x = {x_top:.2f} mm): {tf - tf_th:+.4f} us ({(tf - tf_th) / tf_th * 100:+.2f} %)")
    eb = conv[3][2] - (conv[1][2] - conv[3][2]) / 3
    ef = conv[3][1] - (conv[1][1] - conv[3][1]) / 3
    say(f"     extrapolated to dx -> 0 (Richardson, 0.05 and 0.025 mm): back wall {eb:.4f} us"
        f" ({(eb - tb_th) / tb_th * 100:+.2f} %), flaw {ef:.4f} us ({(ef - tf_th) / tf_th * 100:+.2f} %).")
    say("     With the travel time exact (1), these small offsets are the echoes' own shape (a finite")
    say("     probe; a curved flaw that also shadows the back wall), not an error of the model.")
    say(f"     echo amplitudes over the initial pulse: flaw {af / a_ip:.3f}, back wall {ab / a_ip:.3f}")
    say(f"  3. Rayleigh wave along a free face (half-space, receivers 12 and 18.6 mm from the"
        f" transmitter); root of the Rayleigh equation cR = {cr_th * 1e3:.0f} m/s:")
    for hh, cg, cp in ray:
        say(f"     dx = {hh:.2f} mm: phase speed {cp * 1e3:.0f} m/s ({(cp / cr_th - 1) * 100:+.2f} %),"
            f" group speed {cg * 1e3:.0f} m/s ({(cg / cr_th - 1) * 100:+.2f} %)")
    say(f"     both errors fall by {(ray[0][2] / cr_th - 1) / (ray[1][2] / cr_th - 1):.1f} and"
        f" {(ray[0][1] / cr_th - 1) / (ray[1][1] / cr_th - 1):.1f} when dx halves (second order)."
        f" The figure uses no surface wave:")
    say("     they cancel in the FMC data (PROCESSING), and the echoes of (b) are bulk P waves.")
    say(f"  4. reciprocity of the scattered FMC data: max|h_ij - h_ji| / max|h| = {recip:.1e}"
        f" over all {NE * NE} pairs")
    say(f"  5. TFM (d): flaw peak at x = {fx:+.2f} mm, z = {fz:.2f} mm (x from the array centre);"
        f" nearest point of the void's boundary {dist:.2f} mm away")
    say(f"     (void centre x = {FLAW['x'] - WB / 2:+.2f}, z = {FLAW['z']:.2f} mm; its top at z = {d_f:.2f} mm)")
    say(f"     back wall imaged at z = {bw_z:.2f} mm (true {DB:g} mm, pixel {TFM_DX} mm); levels: back wall"
        f" {bw_db:.1f} dB, flaw {fl_db:.1f} dB")
    say(f"  (p0 = {P0:.4f} of the burst's sine amplitude; t0 = {T0:g} us, the burst's centre, is time"
        f" zero of (b) and of the TFM delays)")
    say()
    say("PROCESSING")
    say("  FMC: h_ij = recorded - half-space run at the same element distance |i - j| (same grid,")
    say("  so the direct waves cancel exactly): removes the initial pulse and the surface waves")
    say("  along the array, keeps every echo (flaw, back wall, side walls).")
    say("  TFM: I(x, z) = | sum_i sum_j H[h_ij](t0 + (|x - e_i| + |x - e_j|)/cL) |, H the analytic")
    say(f"  signal, t0 = {T0:g} us, {TFM_DX} mm pixels over x = +-{TFM_X:g} mm, z = 0 ... {TFM_Z:g} mm.")
    say("  (d) builds up the mean over transmitters 1 ... k (the partial sum over k), each exact,")
    say(f"  in dB of the complete image's peak, 30 dB range (the partial images peak at most"
        f" {20 * np.log10(part.max() / peak):+.1f} dB).")
    say("  The fan in (c) is the delay-law path of the flaw's")
    say("  peak pixel; each line's opacity is that pair's |H[h_ij]| at its delay (the pair's")
    say("  contribution to the pixel).")

    # ---- data for the page
    # the field, 7 bit (63 levels a sign, steps of p0/126), in chunks the page
    # loads in the order it plays them: the first is on screen at once
    q = (128 + 2 * np.clip(np.round(field / FCLIP * 63), -63, 63)).astype(np.uint8)
    q = q.transpose(0, 2, 1)                                             # frames (z, x)
    chunks, fsizes = [], []
    for i, (a, b_) in enumerate(zip(FIELD_CUTS[:-1], FIELD_CUTS[1:])):
        png = _png(_atlas(q[a:b_], 10))
        src = f"nf-bulk-ut-field-{i}.png"
        with open(os.path.join(common.ANIM, src), "wb") as fh:
            fh.write(png)
        chunks.append({"n0": a, "n1": b_, "cols": 10, "src": src})
        fsizes.append(len(png))
    old = os.path.join(common.ANIM, "nf-bulk-ut-field.png")                # the single atlas of round 1
    if os.path.exists(old):
        os.remove(old)
    b = np.clip(np.round(255 * (1 + db / DR)), 0, 255).astype(np.uint8)
    tpng = _png(_atlas(b.transpose(0, 2, 1), 8))
    with open(os.path.join(common.ANIM, "nf-bulk-ut-tfm.png"), "wb") as fh:
        fh.write(tpng)
    keep = ts <= 10.0
    env = np.abs(hilbert(ascan))
    def window(t_c):
        i = np.argmin(np.abs(ts - t_c))
        lo = hi = i
        while lo > 0 and env[lo] > 0.08 * env[i]: lo -= 1
        while hi < env.size - 1 and env[hi] > 0.08 * env[i]: hi += 1
        return [float(ts[lo]), float(ts[hi])]
    ox, oz = flaw_outline(97)
    DATA = {
        "wb": WB, "db": DB, "cl": CL, "t0": T0,
        "flaw": {"x": ox, "z": oz, "top": [x_top, d_f]},
        "probe": [PROBE["x"] - PROBE["w"] / 2, PROBE["x"] + PROBE["w"] / 2],
        "el": {"c": cen, "w": EW_C * DX},
        "ascan": {"t0": float(ts[0]), "dt": float(ts[1] - ts[0]), "n": int(keep.sum()),
                  "v": common.f32(ascan[keep] / norm)},
        "echo": {"tf": tf, "tb": tb, "af": af / norm, "ab": ab / norm, "tf_th": tf_th, "tb_th": tb_th,
                 "wf": window(tf), "wb": window(tb)},
        "field": {"n": int(field.shape[0]), "w": int(field.shape[1]), "h": int(field.shape[2]),
                  "chunks": chunks, "span": 126, "dt": FRAME_EVERY * DT, "clip": FCLIP},
        "tfm": {"n": NE, "w": int(xs.size), "h": int(zs.size), "cols": 8, "x": [xs[0], xs[-1]],
                "z": [zs[0], zs[-1]], "dr": DR, "peak": [fx, fz], "bw": bw_z},
        "amp": common.i8(np.round(amp * 127)),
        "slow": SLOW_PAGE, "tend": T_PE, "pace": SLOW_PAGE / SLOW, "slowtex": sci_tex(SLOW_PAGE),
    }
    js = JS
    path = common.build_html(
        "bulk-ut", "Figure 11: Conventional (bulk wave) ultrasonic testing",
        "A simulated steel block, 50 by 25 mm, with a small flaw. (a) A pulse from a single probe "
        "travels down, and echoes from the flaw and the back wall return; (b) the A scan the probe "
        "records; (c) a 32 element array fires each element in turn while all receive; (d) the "
        "image built from every path shows the flaw and the back wall.",
        1000, H, DATA, js)
    html = os.path.getsize(path)
    say()
    say("PAGE")
    say(f"  nf-bulk-ut.html {html / 1e3:.0f} kB (draws at once; the data below loads behind it)")
    say(f"  nf-bulk-ut-field-0..{len(chunks) - 1}.png: {field.shape[0]} frames {field.shape[1]} x"
        f" {field.shape[2]}, 0.05 us apart, 7 bit, in the order they play: frames "
        + ", ".join(f"{c['n0']}-{c['n1'] - 1} {s / 1e3:.0f} kB" for c, s in zip(chunks, fsizes)))
    say(f"  nf-bulk-ut-tfm.png {len(tpng) / 1e3:.0f} kB ({NE} partial images {xs.size} x {zs.size});"
        f" total {(html + sum(fsizes) + len(tpng)) / 1e6:.2f} MB")
    say(f"  time slowed {SLOW_PAGE / 1e6:g} x 10^6 in (a) and (b): {T_PE:g} us of the model in {T_PE * SLOW_PAGE / 1e6:g} s;"
        f" (c) fires its 32 elements at the same pace ({SLOW_PAGE / SLOW:g} x the first design, 8 s for the 10 us)")
    with open(os.path.join(common.HERE, "bulk_ut.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(rep) + "\n")
    print(common.still("bulk-ut"))
    if "--frames" in sys.argv:
        for p in common.frames("bulk-ut", [0.6, 1.5, 3.0, 5.0, 6.8, 9.0, 11.5, 12.8, 13.8, 15.2, 16.5, 21.0, 27.0]):
            print(p)


SLOW = 8e5                           # 10 us in 8 s: the time scale sd_waves.py imports (keep)
SLOW_PAGE = 1.1e6                    # this page's own, 10 us in 11 s: 1.375 x slower (29 Sep, "a little slower")
FIELD_CUTS = [0, 25, 70, 130, 201]   # field chunks: 15, 110, 380, 680 kB
H = 872
JS = r"""
/* Figure 11 from the EFIT model in bulk_ut.py.
   (a) the model's field p/p0 every 0.05 us (nf-bulk-ut-field-*.png, loaded
   in the order they play), (b) the A scan the probe recorded in the same run,
   (c) the array's firing order and the delay-law paths of each transmitter
   to the flaw's pixel, each path's opacity its measured contribution, (d) the
   TFM image over transmitters 1 ... k (nf-bulk-ut-tfm.png, dB of the complete
   image). Labels ride the fronts at the model's c_L. */
const S = 9.2, BW = DATA.wb * S, BD = DATA.db * S;          // blocks: 9.2 units per mm
const A = {x: 76, y: 96}, CC = {x: 76, y: 492};            // blocks (a) and (c)
const PB = {x: 628, y: 96, w: 348, h: BD};                  // A scan axes
const SD = 10.5, PD = {x: 628, y: 492, w: 28 * SD, h: 27 * SD};   // image axes
const FL = '#781E2C', DRD = 30;                             // flaw outline, dB shown
const XB = (b, x) => b.x + x * S, YB = (b, z) => b.y + z * S;
const AS = b64f32(DATA.ascan.v), AMP = b64i8(DATA.amp);

/* the clock. The intro is over by 0.8 s and the physics starts at TI. A
   cycle: (a) and (b) sweep the model's 10 us in S1 = 11 s while (c) fires its
   32 elements and (d) sums them, at the same pace (DATA.pace, the slowing
   over the first design's 8 s); (a) eases back to the snapshot the still
   shows; a hold; a fade; again. */
const TI = 0.6, S1 = DATA.tend * DATA.slow / 1e6, RW = 1.0, HOLD = 2.4, FADE = 0.6;
const TSNAP = 3.35;                                         // model time of the snapshot, us
const SLOT = Array.from({length: 32}, (_, k) => DATA.pace * (0.18 + 0.22 * Math.max(0, 1 - k / 5)));
const FIRE = SLOT.map((_, k) => SLOT.slice(0, k).reduce((a, b) => a + b, 0));
const PER = S1 + RW + HOLD + FADE;
const POSTER_T = TI + S1 + RW + 1.2;

function state() {
  if (t < TI) return {u: -1, ts: 0, rec: -1, k: -1, fade: 1, c0: TI};
  const u = (t - TI) % PER, c0 = t - u;
  let ts = TSNAP, rec = DATA.tend;
  if (u < S1) { ts = DATA.tend * u / S1; rec = ts; }
  else if (u < S1 + RW) ts = DATA.tend - (DATA.tend - TSNAP) * easeInOut((u - S1) / RW);
  let k = -1;
  for (let i = 0; i < 32; i++) if (u >= FIRE[i]) k = i;
  const fade = 1 - easeInOut(clamp((u - S1 - RW - HOLD) / FADE));
  return {u, ts, rec, k, fade, c0};
}
/* a label arriving on Motion's spring: alpha and a small drop */
function arrive(t0) { const s = settle(t0, .28); return {a: clamp(s), dy: (1 - s) * -8}; }

/* ---------------------------------------------------------------- data
   The figure draws at once; the field arrives chunk by chunk, first frames
   first, and each frame shows as soon as its chunk is decoded. The still
   (?still) waits for all of it. */
const FLD = DATA.field.chunks.map(() => null);
let TFM = null;
function grab(src) {
  return new Promise((ok, no) => {
    const im = new Image();
    im.onload = () => {
      const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
      const g = c.getContext('2d', {willReadFrequently: true}); g.drawImage(im, 0, 0);
      const d = g.getImageData(0, 0, c.width, c.height).data, px = new Uint8Array(c.width * c.height);
      for (let i = 0; i < px.length; i++) px[i] = d[4 * i];
      ok({W: c.width, px});
    };
    im.onerror = no; im.src = src;
  });
}
const redraw = () => { if (document.documentElement.dataset.ready === '1' && !playing) render(); };
const first = grab(DATA.field.chunks[0].src).then(d => { FLD[0] = d; redraw(); });
const image = grab('nf-bulk-ut-tfm.png').then(d => { TFM = d; redraw(); });
const rest = first.then(async () => {
  for (let i = 1; i < FLD.length; i++) { FLD[i] = await grab(DATA.field.chunks[i].src); redraw(); }
});
function offscreen(w, h) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'); return {c, g, img: g.createImageData(w, h)};
}
const FC = offscreen(DATA.field.w, DATA.field.h), TC = offscreen(DATA.tfm.w, DATA.tfm.h);
/* the field's ramp: DIVERGING with the steel itself as zero, as Figures 12 and 13 */
const FLUT = _ramp(['#043052', '#2E6A9E', '#9CBBD6', '#E3EBF2', '#DEABAB', '#B03F4D', '#651020'].map(_hex));
const FMAP = new Uint16Array(256);           // stored byte -> FLUT entry
for (let b = 0; b < 256; b++) FMAP[b] = 3 * Math.round(clamp(((b - 128) / DATA.field.span * 2 + 1) / 2) * 255);
let fcur = -1, tcur = '';
function fieldFrame(n) {                     // true once frame n is in FC
  const ch = DATA.field.chunks;
  let i = 0;
  while (i < ch.length - 1 && n >= ch[i].n1) i++;
  const F = FLD[i];
  if (!F) return false;
  if (n === fcur) return true;
  fcur = n;
  const {w, h} = DATA.field, m = n - ch[i].n0, c = m % ch[i].cols, r = Math.floor(m / ch[i].cols), d = FC.img.data;
  for (let z = 0; z < h; z++) {
    let s = (r * h + z) * F.W + c * w, o = z * w * 4;
    for (let x = 0; x < w; x++, s++, o += 4) {
      const L = FMAP[F.px[s]];
      d[o] = FLUT[L]; d[o + 1] = FLUT[L + 1]; d[o + 2] = FLUT[L + 2]; d[o + 3] = 255;
    }
  }
  FC.g.putImageData(FC.img, 0, 0);
  return true;
}
/* the image after transmitters 1 ... k+1, blended from the one before by w */
function tfmImage(k, w) {
  const key = k + ':' + w.toFixed(3);
  if (key === tcur) return;
  tcur = key;
  const {w: nw, h: nh, cols, dr} = DATA.tfm, d = TC.img.data;
  const ox = n => (n % cols) * nw, oy = n => Math.floor(n / cols) * nh;
  for (let z = 0; z < nh; z++) {
    let a = (oy(k) + z) * TFM.W + ox(k), b = k > 0 ? (oy(k - 1) + z) * TFM.W + ox(k - 1) : -1, o = z * nw * 4;
    for (let x = 0; x < nw; x++, a++, b++, o += 4) {
      const pa = TFM.px[a], pb = b >= 0 ? TFM.px[b] : 0, v = pb + (pa - pb) * w;
      const L = 3 * Math.round(clamp((v / 255 * dr - dr + DRD) / DRD) * 255);
      d[o] = SEQ[L]; d[o + 1] = SEQ[L + 1]; d[o + 2] = SEQ[L + 2]; d[o + 3] = 255;
    }
  }
  TC.g.putImageData(TC.img, 0, 0);
}

/* ---------------------------------------------------------------- parts */
function blockOutline(b, pr) {
  line([[b.x, b.y + BD], [b.x, b.y], [b.x + BW, b.y], [b.x + BW, b.y + BD]], {color: C.ink, width: 1.6, progress: pr});
  line([[b.x, b.y + BD], [b.x + BW, b.y + BD]], {color: C.ink, width: 2.4, progress: pr});
}
function steel(b, a) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.steel; ctx.fillRect(b.x, b.y, BW, BD); ctx.restore();
}
function flawShape(b, a) {
  if (a <= 0) return;
  line(DATA.flaw.x.map((x, i) => [XB(b, x), YB(b, DATA.flaw.z[i])]),
       {color: FL, width: 1.1, fill: C.accent, close: true, alpha: a});
}
function ramp(lut, x, y, w, h, vertical, alpha) {
  if (alpha <= 0) return;
  const g = vertical ? ctx.createLinearGradient(0, y + h, 0, y) : ctx.createLinearGradient(x, 0, x + w, 0);
  for (let i = 0; i <= 64; i++) { const k = Math.round(i / 64 * 255) * 3; g.addColorStop(i / 64, `rgb(${lut[k]},${lut[k + 1]},${lut[k + 2]})`); }
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = g; ctx.fillRect(x, y, w, h); ctx.restore();
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], {color: C.ink, width: 1, close: true, alpha});
}
function tri(x, y, s, color, alpha) {        // a marker pointing down at (x, y)
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.beginPath();
  ctx.moveTo(x, y); ctx.lineTo(x - s * .6, y - s); ctx.lineTo(x + s * .6, y - s); ctx.closePath(); ctx.fill(); ctx.restore();
}
/* a label riding a front at depth z (mm), its arrow the way the front moves */
function ride(s, x, z, up, col, a) {
  if (a <= 0) return;
  const y0 = YB(A, up ? z - 1.2 : z + 1.2), y1 = YB(A, up ? z - 3.7 : z + 3.7);
  arrow(XB(A, x), y0, XB(A, x), y1, {color: col, width: 1.4, head: 7, alpha: a});
  text(s, XB(A, x + 1.1), (y0 + y1) / 2 + 5, {size: 15, color: col, alpha: a});
}
const param = (s, x, y, a) => math(s, x, y, {size: 14, color: C.muted, alpha: a});
/* labels the A scan's playhead passes behind: their ink boxes, kept as they
   are drawn; gapLine() is a vertical line broken 3 units clear of each */
const KEEP = [];
function keepText(s, x, y, o) {
  text(s, x, y, o);
  if (!(o.alpha > 0)) return;
  ctx.save(); ctx.font = font(o); ctx.textAlign = o.align || 'left'; const q = ctx.measureText(s); ctx.restore();
  KEEP.push([x - q.actualBoundingBoxLeft, y - q.actualBoundingBoxAscent, x + q.actualBoundingBoxRight, y + q.actualBoundingBoxDescent]);
}
function gapLine(x, y0, y1, o) {
  const cuts = KEEP.filter(b => x > b[0] - 3 && x < b[2] + 3).map(b => [b[1] - 3, b[3] + 3]).sort((p, q) => p[0] - q[0]);
  let y = y0;
  for (const [p, q] of cuts) { if (p > y + .5) line([[x, y], [x, Math.min(p, y1)]], o); y = Math.max(y, q); if (y >= y1) return; }
  if (y1 > y + .5) line([[x, y], [x, y1]], o);
}
/* the engine's dim(), its knockout as deep as the label's ink (the slash and
   the subscripts reach below dim()'s own), opaque from the first frame so the
   line never shows through the label while both fade in */
function dimk(x1, x2, y, label, o) {
  const {color, alpha, size} = o;
  dim(x1, x2, y, '', {color, alpha});
  if (alpha <= 0) return;
  const w = math(label, 0, -1e4, {size, alpha: 0}), bx = (x1 + x2) / 2 - w / 2 - 4, by = y - size * .62;
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(bx, by, w + 8, size * 1.42); ctx.restore();
  KEEP.push([bx, by, bx + w + 8, by + size * 1.42]);
  math(label, (x1 + x2) / 2, y + size * .34, {size, align: 'center', color, alpha});
}

/* ---------------------------------------------------------------- (a) */
function drawA(st) {
  steel(A, seg(0, 0.3));
  if (t >= TI && st.fade > 0 && fieldFrame(clamp(Math.round(st.ts / DATA.field.dt), 0, DATA.field.n - 1))) {
    ctx.save(); ctx.globalAlpha *= st.fade; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(FC.c, A.x, A.y, BW, BD); ctx.restore();
  }
  blockOutline(A, seg(0, 0.4));
  flawShape(A, seg(0.3, 0.25));
  const s = settle(0.2, .28), [p0, p1] = DATA.probe;        // the probe arrives on the top face
  ctx.save(); ctx.globalAlpha *= clamp(s); ctx.fillStyle = C.navy;
  ctx.fillRect(XB(A, p0), A.y - 16 + (1 - s) * -20, (p1 - p0) * S, 16); ctx.restore();
  const da = seg(0.35, 0.3), xd = A.x - 17;                 // the thickness d, as Figure 12 marks it
  arrow(xd, A.y + 1, xd, A.y + BD - 1, {width: 1.1, head: 7, both: true, alpha: da});
  math('d', xd - 8, A.y + BD / 2 + 6, {size: 17, align: 'right', alpha: da});
  const g = arrive(0.35), bw = 100, bx = A.x + BW - bw, by = A.y + BD + 18;   // colour bar, as Figure 12
  ramp(FLUT, bx, by + g.dy, bw, 8, false, g.a);
  for (const v of [-0.5, 0, 0.5]) {
    const x = bx + (v / DATA.field.clip + 1) / 2 * bw;
    line([[x, by + 8 + g.dy], [x, by + 12 + g.dy]], {width: 1, alpha: g.a});
    math(fmt(v), x, by + 27 + g.dy, {size: 15, align: 'center', alpha: g.a});
  }
  math('p/p_{0}', bx - 8, by + 9 + g.dy, {size: 16, align: 'right', alpha: g.a});
  if (t >= TI) {                                             // the model's clock, as Figure 12 shows it
    const a = st.fade * clamp((t - st.c0) / 0.2);
    math(`t = ${(st.ts - DATA.t0).toFixed(2)}\\,\\rm{\u00b5s}`, A.x + BW, 34, {size: 16, align: 'right', alpha: a});
    const ta = st.ts - DATA.t0, c = DATA.cl, [xt, zt] = DATA.flaw.top;
    const win = (a0, a1, b0, b1) => clamp((ta - a0) / (a1 - a0)) * (1 - clamp((ta - b0) / (b1 - b0)));
    ride('incident pulse', 36.5, c * ta, false, C.ink, st.fade * win(0.5, 0.8, 3.2, 3.5));
    ride('flaw echo', xt, 2 * zt - c * ta, true, C.accent, st.fade * win(2.25, 2.55, 3.08, 3.25));
    ride('back wall echo', 36.5, 2 * DATA.db - c * ta, true, C.ink, st.fade * win(4.6, 4.9, 7.45, 7.75));
  }
  const pa = seg(0.5, 0.3);
  math('\\rm{time slowed }' + DATA.slowtex, A.x + BW, 54, {size: 14, color: C.muted, align: 'right', alpha: pa});
  param('\\rm{steel }50 \\times\\ 25\\ \\rm{mm},\\ c_{\\rm{L}} = 5900\\ \\rm{m/s},\\ c_{\\rm{T}} = 3230\\ \\rm{m/s}', A.x, by + 10, pa);
  param('\\rm{probe 10 mm, 5 MHz, 3 cycle Hann burst}', A.x, by + 29, pa);
}

/* ---------------------------------------------------------------- (b) */
function drawB(st) {
  const pr = seg(0.05, 0.4), la = seg(0.3, 0.3);
  const ax = axes({x: PB.x, y: PB.y, w: PB.w, h: PB.h, xlim: [-0.5, 10], ylim: [-1.15, 1.15],
                   xticks: [0, 2, 4, 6, 8, 10], yticks: [-1, 0, 1], xlabel: 't\\ \\rm{(\u00b5s)}',
                   ylabel: 'v/v_{0}', progress: pr, ylabelGap: 38});
  line([[PB.x, ax.Y(0)], [PB.x + PB.w, ax.Y(0)]], {color: C.rule, width: 1, alpha: pr});
  for (const z of [0, 5, 10, 15, 20, 25]) {                 // depth of the reflector, z = c t / 2
    const x = ax.X(2 * z / DATA.cl);
    line([[x, PB.y], [x, PB.y + 5]], {width: 1.1, alpha: la});
    math(String(z), x, PB.y - 7, {size: 15, align: 'center', alpha: la});
  }
  math('z = c_{\\rm{L}}t/2\\ \\rm{(mm)}', PB.x + PB.w / 2, PB.y - 29, {size: 16, align: 'center', alpha: la});
  if (st.rec < 0 || st.fade <= 0) return;
  const a = st.fade, tr = st.rec - DATA.t0, {t0: q0, dt: dq, n} = DATA.ascan;
  const m = Math.min(n - 1, Math.floor((tr - q0) / dq));
  if (m >= 1) {
    const pts = [];
    for (let i = 0; i <= m; i++) pts.push([ax.X(q0 + i * dq), ax.Y(AS[i])]);
    const [w0, w1] = DATA.echo.wf, i0 = Math.ceil((w0 - q0) / dq), i1 = Math.min(m, Math.floor((w1 - q0) / dq));
    ax.inside(() => {
      line(pts, {color: C.navy, width: 1.8, alpha: a});
      if (i1 > i0) line(pts.slice(i0, i1 + 1), {color: C.accent, width: 1.9, alpha: a});
    });
  }
  const E = DATA.echo, when = te => st.c0 + (te + DATA.t0) / DATA.tend * S1;
  const lab = (s, tt, x, v, col, align) => {                 // each echo named once it is recorded
    if (tr < tt) return;
    const g = arrive(when(tt));
    s.split('\n').forEach((r, i) => keepText(r, ax.X(x), ax.Y(v) + g.dy + 16 * i, {size: 15, color: col, align, alpha: g.a * a}));
  };
  /* the arrivals 2d/c predicts: a guide, and the time as Figure 12 marks it */
  const pred = [[E.tf, E.tf_th, -0.45, '2z_{\\rm{f}}/c_{\\rm{L}}'],
                [E.tb, E.tb_th, -0.8, `2d/c_{\\rm{L}} = ${E.tb_th.toFixed(2)}\\,\\rm{\u00b5s}`]];
  for (const [te, tt, v, s] of pred) {
    if (tr < te + 0.3) continue;
    const g = arrive(when(te + 0.3));
    line([[ax.X(tt), PB.y], [ax.X(tt), PB.y + PB.h]], {color: C.guide, width: 1, dash: [5, 4], alpha: g.a * a});
    dimk(ax.X(0), ax.X(tt), ax.Y(v), s, {size: 14, color: C.body, alpha: g.a * a});
  }
  lab('initial\npulse', 0.35, 0.45, 0.86, C.body, 'left');
  lab('flaw echo', E.tf + 0.3, E.tf_th + 0.15, E.af + 0.14, C.accent, 'left');
  lab('back wall echo', E.tb + 0.3, E.tb_th - 0.15, E.ab + 0.2, C.body, 'right');
  // the playhead, last: it passes behind the labels, never through them
  const tc = st.ts - DATA.t0, xc = ax.X(tc), ca = a * clamp((t - st.c0) / 0.2);
  gapLine(xc, PB.y, PB.y + PB.h, {color: C.ink, width: 1, alpha: 0.45 * ca});
  dot(xc, ax.Y(AS[clamp(Math.round((tc - q0) / dq), 0, n - 1)]), 3, {color: C.navy, alpha: ca});
}

/* ---------------------------------------------------------------- (c) */
function drawC(st) {
  steel(CC, seg(0.1, 0.3));
  const ga = seg(0.4, 0.3);                                  // the region imaged in (d)
  for (const x of [DATA.wb / 2 + DATA.tfm.x[0], DATA.wb / 2 + DATA.tfm.x[1]])
    line([[XB(CC, x), CC.y], [XB(CC, x), CC.y + BD]], {color: C.guide, width: 1, dash: [5, 4], alpha: ga});
  text('region imaged in (d)', XB(CC, DATA.wb / 2), YB(CC, 23.6), {size: 15, align: 'center', color: C.muted, alpha: ga});
  const c = DATA.el.c, hw = DATA.el.w / 2, F = [XB(CC, DATA.wb / 2 + DATA.tfm.peak[0]), YB(CC, DATA.tfm.peak[1])];
  const rays = (k, a, pa, pb) => {                           // transmitter k: out to the flaw, back to all
    if (a <= 0) return;
    line([[XB(CC, c[k]), CC.y], F], {color: C.blue, width: 1.5, progress: pa, alpha: a});
    for (let j = 0; j < 32; j++)
      line([F, [XB(CC, c[j]), CC.y]], {color: C.sky, width: 0.9, progress: pb, alpha: a * (0.1 + 0.9 * AMP[k * 32 + j] / 127)});
  };
  const k = st.k, t0k = k >= 0 ? st.c0 + FIRE[k] : 0;
  if (k > 0) rays(k - 1, st.fade * (1 - seg(t0k, 0.12)), 1, 1);
  if (k >= 0) rays(k, st.fade, seg(t0k, 0.1), seg(t0k + 0.05, 0.12));
  flawShape(CC, seg(0.3, 0.25));
  blockOutline(CC, seg(0.1, 0.4));
  const s = settle(0.25, .28), ya = CC.y - 16 + (1 - s) * -20;
  const x0 = XB(CC, c[0] - hw), x1 = XB(CC, c[31] + hw);
  ctx.save(); ctx.globalAlpha *= clamp(s);
  ctx.fillStyle = C.navy; ctx.fillRect(x0, ya, x1 - x0, 16);
  const lit = (j, a) => { if (a > 0) { ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.amber; ctx.fillRect(XB(CC, c[j] - hw), ya, DATA.el.w * S, 16); ctx.restore(); } };
  if (k > 0) lit(k - 1, st.fade * (1 - seg(t0k, 0.12)));
  if (k >= 0) lit(k, st.fade * seg(t0k, 0.06));
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 0.8;
  for (let j = 0; j < 31; j++) { const x = XB(CC, (c[j] + c[j + 1]) / 2); ctx.beginPath(); ctx.moveTo(x, ya); ctx.lineTo(x, ya + 16); ctx.stroke(); }
  ctx.restore();
  if (k >= 0) {                                              // the marker steps along the array
    const g = settle(t0k, 0.16), xm = k > 0 ? lerp(XB(CC, c[k - 1]), XB(CC, c[k]), g) : XB(CC, c[0]);
    tri(xm, CC.y - 20, 7, C.amber, st.fade * (k > 0 ? 1 : clamp(g)));
    text(`transmitter ${k + 1} of 32`, CC.x + BW, CC.y - 30, {size: 15, align: 'right', color: C.body, alpha: st.fade});
  }
  param('32\\ \\rm{elements, pitch 0.6 mm; each transmits in turn, all receive}', CC.x, CC.y + BD + 26, seg(0.5, 0.3));
}

/* ---------------------------------------------------------------- (d) */
function drawD(st) {
  const T = DATA.tfm, px = (T.x[1] - T.x[0]) / (T.w - 1);
  const X = x => PD.x + (x - T.x[0]) / (T.x[1] - T.x[0]) * PD.w, Y = z => PD.y + z / 27 * PD.h;
  if (TFM && st.k >= 0 && st.fade > 0) {
    tfmImage(st.k, seg(st.c0 + FIRE[st.k], 0.15));
    ctx.save(); ctx.beginPath(); ctx.rect(PD.x, PD.y, PD.w, PD.h); ctx.clip();
    ctx.globalAlpha *= st.fade; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(TC.c, X(T.x[0] - px / 2), Y(T.z[0] - px / 2), T.w * px * SD, T.h * px * SD); ctx.restore();
  }
  axes({x: PD.x, y: PD.y, w: PD.w, h: PD.h, xlim: T.x, ylim: [27, 0], xticks: [-10, -5, 0, 5, 10],
        yticks: [0, 5, 10, 15, 20, 25], xlabel: 'x\\ \\rm{(mm)}', ylabel: 'z\\ \\rm{(mm)}', progress: seg(0.15, 0.4), ylabelGap: 38});
  line(DATA.flaw.x.map((x, i) => [X(x - DATA.wb / 2), Y(DATA.flaw.z[i])]),
       {color: C.accent, width: 1.3, dash: [3.5, 2.5], close: true, alpha: seg(0.45, 0.3)});
  const g = arrive(0.4), bx = PD.x + PD.w + 16;
  ramp(SEQ, bx, PD.y + g.dy, 11, PD.h, true, g.a);
  for (const v of [0, -10, -20, -30]) {
    const y = PD.y - v / DRD * PD.h + g.dy;
    line([[bx + 11, y], [bx + 15, y]], {width: 1, alpha: g.a});
    math(fmt(v), bx + 19, y + 5, {size: 15, alpha: g.a});
  }
  text('dB', bx + 5.5, PD.y - 9 + g.dy, {size: 15, align: 'center', alpha: g.a});
  if (st.k >= 5) {
    const h = arrive(st.c0 + FIRE[5]), a = h.a * st.fade;
    text('flaw', X(T.peak[0] - 2.4), Y(T.peak[1] - 1.4) + h.dy, {size: 16, align: 'right', color: C.ink, alpha: a});
    text('back wall', X(-13.2), Y(T.bw - 1.8) + h.dy, {size: 16, color: C.ink, alpha: a});
  }
  param('\\rm{total focusing method, }32 \\times\\ 32\\ \\rm{paths}', PD.x - 38, PD.y + PD.h + 74, seg(0.5, 0.3));
}

function titles() {
  const g = arrive(0);
  for (const [l, s, x, y] of [['a', 'single probe, pulse echo', 18, 34], ['b', 'A scan', 572, 34],
                              ['c', 'array probe, many paths', 18, 424], ['d', 'B scan image', 572, 424]]) {
    const w = panel(l, x, y + g.dy, {alpha: g.a});
    text(s, x + w + 8, y + g.dy, {size: 17, color: C.body, alpha: g.a});
  }
}

function draw() {
  const st = state();
  KEEP.length = 0;
  titles(); drawA(st); drawB(st); drawC(st); drawD(st);
}

for (const p of [first, image, rest]) p.catch(() => {});
if (STILL) Promise.all([first, image, rest]).then(boot, boot);
else boot();
"""

if __name__ == "__main__":
    main()
