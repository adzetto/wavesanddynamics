"""The SHM and NDT guide's cover (understanding-shm-and-ndt, image1): the whole
structure, and one spot of it imaged closely.

His note on the cover (5 Oct 2026): "Tepedeki resim => vertical size 2x", with
a sketch: a tall building (about 12 storeys) on a fixed base, small sensors on
several floors on its left side, a circled spot on its side with an arrow to an
inset labelled "imaging": a test piece with an array probe (a comb of
elements) on its top surface, a defect (an ellipse) inside it and the back
wall near its bottom. Redrawn at twice the old height, 1000 x 346, from two
models:

Left, the building: a 12 storey steel moment frame as a shear building (rigid
floors, each storey's columns fixed at both ends), floor masses and storey
stiffnesses from its members, eigenvalues by scipy, checked against the closed
form of the uniform chain and by time integration. It sways in its first mode
in real time (f1 = 0.78 Hz); the columns between two floors take the shape of
a column fixed at both ends whose ends move apart (the cubic 3 s^2 - 2 s^3),
which is what the shear building assumes. Accelerometers ride floors 3, 6, 9
and 12 on its left side.

Right, "imaging": the circled beam to column joint, a 16 mm steel flange at
the NDT scale. A 16 element, 2 MHz array on its top face fires one element
after another and all receive (full matrix capture), computed by the 2D
elastic finite difference model of the SHM guide's Figure 3 (shm_fdtd.py,
imported: velocity-stress, staggered grid, voids as cells of zero density and
stiffness) with an elliptical void as the defect; the total focusing method
builds the image beside the piece, transmitter by transmitter. The fronts
drawn in the piece are the geometric ones of the same model (the incident
circle, cut where the void shadows it; the void's specular echo, by the law of
reflection off the ellipse; the back wall's echo), and each receiver lights up
when the void's echo reaches it.

Run: python tools/numfig/shm_cover.py [--look]   (writes content/anim/
nf-shm-cover.html and .webp and tools/numfig/shm_cover.check.txt; the model
runs are cached in the temp directory)
"""
import base64
import io
import os
import sys

import numpy as np
from PIL import Image
from scipy.linalg import eigh
from scipy.signal import hilbert

import common
import shm_fdtd as F
import wt_lib

NAME = "shm-cover"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1000, 346                     # twice the old cover's height (1000 x 173)

# ------------------------------------------------------------------ the building
N_ST, H_ST = 12, 3.5                 # storeys, storey height (m): 42 m
BAYS, BAY = 3, 5.0                   # bays of 5 m each way: a 15 x 15 m plan
N_COL = (BAYS + 1) ** 2              # 16 columns per storey
E_ST = 210e9                         # steel (Pa)
I_COL = 43190e-8                     # HE 360 B, strong axis (m^4)
M_FL = 270e3                         # floor mass (kg): 1.2 t/m^2 over the 225 m^2 plan
# ------------------------------------------------------------------ the imaging
F0, NC = 2.0, 3                      # MHz, cycles of the Hann burst
DUR = NC / F0                        # 1.5 us
T0B = 0.5 * DUR                      # the burst's centre: time zero of the records and the delays
DX = 0.1                             # mm: 29.5 points per P wavelength, 16 per S
WP, DP, MARG = 30.0, 16.0, 25.0      # the piece drawn (mm), its thickness, the model's margin each side
DEF = dict(x=17.0, z=8.0, a=3.0, b=1.2, tilt=10.0)   # elliptical void: centre, semi-axes (mm), tilt (deg, right end up)
NE, PITCH, EW = 16, 1.5, 1.3         # array: elements, pitch, element width (mm)
XE = WP / 2 + PITCH * (np.arange(NE) - (NE - 1) / 2)
T_REC = 9.0                          # us recorded per firing
PIX, ZMAX, DB = 0.2, 17.6, 24.0      # image: pixel (mm), depth shown (mm), dB range
SLOW = 1e5                           # the waves' time slowed: 10 us of the model per second
T_FIRE = 7.0                         # us of each firing shown (from the burst's start)
# ------------------------------------------------------------------ the page's clock (s)
T0_BLD = 0.35                        # the building, held at full sway, is let go
HOLD = 1.8                           # the image complete, held, before the next loop fades it
POSTER_TAU = 3.0                     # the still: 3 us into the last firing (the void's echo on its way back)


# ------------------------------------------------------------------ the building
def building():
    """The shear building: masses, storey stiffnesses, modes, the closed form and a
    time integration of the first mode's free vibration."""
    k = N_COL * 12 * E_ST * I_COL / H_ST ** 3
    n = N_ST
    K = np.zeros((n, n))
    for i in range(n):
        K[i, i] = 2 * k if i < n - 1 else k
        if i:
            K[i, i - 1] = K[i - 1, i] = -k
    M = M_FL * np.eye(n)
    w2, phi = eigh(K, M)
    w = np.sqrt(w2)
    f = w / (2 * np.pi)
    j = np.arange(1, n + 1)
    w_cf = 2 * np.sqrt(k / M_FL) * np.sin((2 * j - 1) * np.pi / (2 * (2 * n + 1)))
    floors = np.arange(1, n + 1)
    shape_err = 0.0
    for m in range(3):
        cf = np.sin(floors * (2 * m + 1) * np.pi / (2 * n + 1))
        ph = phi[:, m] / phi[-1, m]
        shape_err = max(shape_err, np.abs(ph - cf / cf[-1]).max())
    psi = np.r_[0.0, phi[:, 0] / phi[-1, 0]]                     # mode 1 at the base and the floors, roof = 1
    # free vibration from the first mode's shape (Newmark, average acceleration):
    # the roof's period from its zero crossings, against T1 and against the
    # method's own period pi dt / atan(w dt / 2)
    T1 = 2 * np.pi / w[0]
    dt = T1 / 400
    u, v = phi[:, 0] / phi[-1, 0], np.zeros(n)
    a = -np.linalg.solve(M, K @ u)
    keff = K + 4 / dt ** 2 * M
    roof, ts = [u[-1]], [0.0]
    for s in range(1, int(round(6 * T1 / dt)) + 1):
        rhs = M @ (4 / dt ** 2 * u + 4 / dt * v + a)
        un = np.linalg.solve(keff, rhs)
        an = 4 / dt ** 2 * (un - u) - 4 / dt * v - a
        v = v + dt / 2 * (a + an)
        u, a = un, an
        roof.append(u[-1]); ts.append(s * dt)
    roof, ts = np.array(roof), np.array(ts)
    zc = [ts[i] - roof[i] * (ts[i + 1] - ts[i]) / (roof[i + 1] - roof[i])
          for i in range(len(roof) - 1) if roof[i] > 0 >= roof[i + 1]]      # downward crossings
    T_nm = (zc[-1] - zc[0]) / (len(zc) - 1)
    T_nm_cf = np.pi * dt / np.arctan(w[0] * dt / 2)
    # modal participation of the first mode (uniform masses), the share of the mass it moves
    ones = np.ones(n)
    p1 = phi[:, 0] @ M @ ones
    meff = p1 ** 2 / (phi[:, 0] @ M @ phi[:, 0]) / (M_FL * n)
    return dict(k=k, f=f, w=w, w_cf=w_cf, shape_err=shape_err, psi=psi, T1=T1, dt=dt,
                T_nm=T_nm, T_nm_cf=T_nm_cf, nz=len(zc), meff=meff)


# ------------------------------------------------------------------ the imaging
def drive(t):
    return F.burst(t, F0, NC)


def stamp(dx):
    return F.CFL * dx / F.CL


def fmc_run(dx):
    """Full matrix capture on the piece (the model 25 mm longer each side, so
    nothing returns from its ends within the record), and one run in a half
    space for the direct waves along the array."""
    dt = stamp(dx)
    solid, X, Z = F.block(WP + 2 * MARG, DP, dx)
    F.cut(solid, X, Z, dict(DEF, x=DEF["x"] + MARG))
    els = [F.cells(MARG + x - EW / 2, EW, dx) for x in XE]
    ns = int(round(T_REC / dt))
    data = np.array([F.run(solid, els[i], els, ns, dx, dt, drive) for i in range(NE)])
    half, _, _ = F.block(90.0, 40.0, dx)
    rels = [F.cells(30.0 + PITCH * q - EW / 2, EW, dx) for q in range(NE)]
    ref = F.run(half, rels[0], rels, ns, dx, dt, drive)
    return data, ref, np.array(dt)


def fmc(dx):
    key = (dx, WP, DP, MARG, tuple(sorted(DEF.items())), NE, PITCH, EW, F0, NC, T_REC, 1)
    data, ref, dt = F.cached("cover-fmc", key, lambda: fmc_run(dx))
    dt = float(dt)
    ts = (np.arange(data.shape[2]) + 0.5) * dt - T0B            # from the burst's centre
    h = data.astype(float).copy()
    for i in range(NE):
        for j in range(NE):
            h[i, j] -= ref[abs(i - j)]
    return ts, h


def plane_run(dx):
    """A near plane wave: a 60 mm probe in the middle of a 160 mm long piece of
    the same thickness, no void (nothing returns from its ends in time): the
    back wall echo tests the scheme's P travel time."""
    dt = stamp(dx)
    solid, _, _ = F.block(160.0, DP, dx)
    src = F.cells(50.0, 60.0, dx)
    return F.run(solid, src, [src], int(round((2 * DP / F.CL + 2.5) / dt)), dx, dt, drive)[0], np.array(dt)


def plane_echo(dx):
    rec, dt = F.cached("cover-plane", (dx, DP, F0, NC, 2), lambda: plane_run(dx))
    dt = float(dt)
    ts = (np.arange(rec.size) + 0.5) * dt - T0B
    return env_peak(ts, rec / np.abs(rec[ts < 1.0]).max(), 2 * DP / F.CL - 1.5, 2 * DP / F.CL + 1.5)


def env_peak(t, s, lo, hi):
    """Time and value of the envelope's maximum in [lo, hi], parabolic refine."""
    e = np.abs(hilbert(s))
    idx = np.where((t >= lo) & (t <= hi))[0]
    m = idx[np.argmax(e[idx])]
    a, b, c = e[m - 1], e[m], e[m + 1]
    d = 0.5 * (a - c) / (a - 2 * b + c)
    return t[m] + d * (t[1] - t[0]), b - 0.25 * (a - c) * d


def tfm(h, ts, xs, zs):
    """Per transmitter complex contributions C_i(x, z) = sum_j H[h_ij](t_i + t_j),
    t = distance / c_L from each element's centre (shm_ndt.tfm, for this array)."""
    Hs = hilbert(h, axis=2)
    dt = ts[1] - ts[0]
    Xg, Zg = np.meshgrid(xs, zs, indexing="ij")
    tau = np.sqrt((Xg[None] - XE[:, None, None]) ** 2 + Zg[None] ** 2) / F.CL
    out = np.zeros((NE,) + Xg.shape, complex)
    for i in range(NE):
        for j in range(NE):
            f = (tau[i] + tau[j] - ts[0]) / dt
            m = np.floor(f).astype(int)
            w = f - m
            ok = (m >= 0) & (m + 1 < ts.size)
            m = np.clip(m, 0, ts.size - 2)
            out[i] += np.where(ok, (1 - w) * Hs[i, j][m] + w * Hs[i, j][m + 1], 0)
    return out


def outline(n=721):
    """The void's boundary (x, z) in mm, and its outward unit normals, as
    shm_fdtd.cut() cuts it: u = (x - x0) cos t - (z - z0) sin t, v = (x - x0) sin t + (z - z0) cos t."""
    th, ph = np.radians(DEF["tilt"]), np.arange(n) * 2 * np.pi / n
    u, v = DEF["a"] * np.cos(ph), DEF["b"] * np.sin(ph)
    x = DEF["x"] + u * np.cos(th) + v * np.sin(th)
    z = DEF["z"] - u * np.sin(th) + v * np.cos(th)
    gu, gv = np.cos(ph) / DEF["a"], np.sin(ph) / DEF["b"]
    nx, nz = gu * np.cos(th) + gv * np.sin(th), -gu * np.sin(th) + gv * np.cos(th)
    L = np.hypot(nx, nz)
    return x, z, nx / L, nz / L


def echo_paths():
    """The void's first echo from element i to element j, by the law of
    reflection: the shortest path i -> Q -> j over boundary points Q that both
    see (us after the burst's centre)."""
    x, z, nx, nz = outline(7201)
    out = np.zeros((NE, NE))
    for i in range(NE):
        di = np.hypot(x - XE[i], z)
        si = nx * (XE[i] - x) + nz * (0 - z) > 0
        for j in range(NE):
            dj = np.hypot(x - XE[j], z)
            sj = nx * (XE[j] - x) + nz * (0 - z) > 0
            out[i, j] = np.min(np.where(si & sj, di + dj, np.inf)) / F.CL
    return out


def png_uri(a):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


# ------------------------------------------------------------------ the page's fronts, in Python
def fronts_py(k, tc):
    """The same fronts the page draws for firing k, tc us after the burst's centre
    (the port of frontPts() in the page's script): lists of [index, x, z]."""
    a, b, th = DEF["a"], DEF["b"], np.radians(DEF["tilt"])
    ct, st = np.cos(th), np.sin(th)

    def uv(x, z):
        dx, dz = x - DEF["x"], z - DEF["z"]
        return (dx * ct - dz * st) / a, (dx * st + dz * ct) / b

    def hits(x1, z1, x2, z2):
        u1, v1 = uv(x1, z1)
        u2, v2 = uv(x2, z2)
        du, dv = u2 - u1, v2 - v1
        L2 = du * du + dv * dv
        s = 0.0 if L2 == 0 else min(1.0, max(0.0, -(u1 * du + v1 * dv) / L2))
        cu, cv = u1 + s * du, v1 + s * dv
        return cu * cu + cv * cv < 1

    inside = lambda x, z: 0 <= x <= WP and 0 <= z <= DP
    S = (XE[k], 0.0)
    R = F.CL * tc
    out = {"inc": [], "bw": [], "df": []}
    if R <= 0:
        return out
    n = max(120, int(np.ceil(R * 24)))
    for q in range(n + 1):
        ang = 2 * np.pi * q / n
        x, z = S[0] + R * np.cos(ang), R * np.sin(ang)
        if z >= 0 and inside(x, z) and not hits(S[0], 0, x, z):
            out["inc"].append([q, x, z])
        xb, zb = S[0] + R * np.cos(ang), 2 * DP + R * np.sin(ang)
        if inside(xb, zb) and zb < DP:
            s = (DP - 2 * DP) / (zb - 2 * DP)
            xw = S[0] + s * (xb - S[0])
            if not hits(S[0], 0, xw, DP) and not hits(xw, DP, xb, zb):
                out["bw"].append([q, xb, zb])
    m = 720
    for q in range(m):
        ph = 2 * np.pi * q / m
        u, v = a * np.cos(ph), b * np.sin(ph)
        qx, qz = DEF["x"] + u * ct + v * st, DEF["z"] - u * st + v * ct
        gu, gv = np.cos(ph) / a, np.sin(ph) / b
        nx, nz = gu * ct + gv * st, -gu * st + gv * ct
        L = np.hypot(nx, nz)
        nx, nz = nx / L, nz / L
        sx, sz = S[0] - qx, S[1] - qz
        d = np.hypot(sx, sz)
        if nx * sx + nz * sz <= 0 or R <= d:
            continue
        ix, iz = -sx / d, -sz / d
        dn = ix * nx + iz * nz
        rx, rz = ix - 2 * dn * nx, iz - 2 * dn * nz
        x, z = qx + (R - d) * rx, qz + (R - d) * rz
        if inside(x, z):
            out["df"].append([q, x, z])
    return out


def model():
    bld = building()
    # ---- the imaging: FMC, TFM, the checks
    ts, h = fmc(DX)
    recip = np.abs(h - h.transpose(1, 0, 2)).max() / np.abs(h).max()
    xs = np.round(np.arange(0, WP + 1e-9, PIX), 6)
    zs = np.round(np.arange(0, ZMAX + 1e-9, PIX), 6)
    Ci = tfm(h, ts, xs, zs)
    parts = np.cumsum(Ci, axis=0) / NE                                 # the image after k firings: the partial sum
    full = np.abs(parts[-1])
    peak = full.max()
    db = np.clip(20 * np.log10(np.abs(parts) / peak + 1e-12), -DB, 0)
    tiles8 = np.round((db + DB) / DB * 255).astype(np.uint8)           # (k, x, z)
    cols = 4
    tw, th = xs.size, zs.size
    atlas = np.zeros((NE // cols * th, cols * tw), np.uint8)
    for q in range(NE):
        r_, c_ = divmod(q, cols)
        atlas[r_ * th:(r_ + 1) * th, c_ * tw:(c_ + 1) * tw] = tiles8[q].T
    img = png_uri(atlas)
    Xg, Zg = np.meshgrid(xs, zs, indexing="ij")
    ox, oz, _, _ = outline(72001)
    above = Zg < DP - 2.0
    jd = np.unravel_index(np.argmax(np.where(above, full, 0)), full.shape)
    pd = np.array([xs[jd[0]], zs[jd[1]]])
    lvl_d = 20 * np.log10(full[jd] / peak)
    dist = np.hypot(ox - pd[0], oz - pd[1]).min()
    top = (float(ox[np.argmin(oz)]), float(oz.min()))
    ib = np.argmin(np.abs(xs - 6.0))                                    # away from the void's shadow
    zb = zs[np.argmax(full[ib])]
    lvl_b = 20 * np.log10(full[ib].max() / peak)
    part_pk = 20 * np.log10(np.abs(parts).max(axis=(1, 2)) / peak)
    # the element over the void's top: its own echo (pulse echo) against the
    # geometric path, twice the nearest distance to the boundary
    je = int(np.argmin(np.abs(XE - top[0])))
    dmin = np.hypot(ox - XE[je], oz).min()
    t_def, a_def = env_peak(ts, h[je, je] / np.abs(h).max(), 2 * dmin / F.CL - 1.0, 2 * dmin / F.CL + 1.0)
    jb = 0                                                              # the first element: far from the void's shadow
    t_bw, a_bw = env_peak(ts, h[jb, jb] / np.abs(h).max(), 2 * DP / F.CL - 1.0, 2 * DP / F.CL + 1.0)
    arrive = echo_paths()
    # the grid: the same at half the cell (the image's void peak and level)
    ts2, h2 = fmc(DX / 2)
    C2 = tfm(h2, ts2, xs, zs).sum(0) / NE
    f2 = np.abs(C2)
    j2 = np.unravel_index(np.argmax(np.where(above, f2, 0)), f2.shape)
    conv = dict(pd2=(xs[j2[0]], zs[j2[1]]), lvl2=20 * np.log10(f2[j2] / f2.max()),
                tfm_diff=np.abs(f2 / f2.max() - full / peak).max())
    t_def2 = env_peak(ts2, h2[je, je] / np.abs(h2).max(), 2 * dmin / F.CL - 1.0, 2 * dmin / F.CL + 1.0)[0]
    # the scheme's P travel time: a near plane wave's back wall echo at three grids
    pw = [(dx, plane_echo(dx)[0]) for dx in (0.1, 0.05, 0.025)]
    rich = pw[2][1] + (pw[2][1] - pw[1][1]) / 3

    # ---- the page's clock
    US = 1e6 / SLOW                       # model us per page second
    DTF = T_FIRE / US                     # page s per firing
    TB = bld["T1"]
    # the still: POSTER_TAU us into the last firing, with the building at full
    # sway: the first firing's time chosen so that both fall together
    tau_p = POSTER_TAU / US
    want = 0.5                            # the first firing about half a second in
    nhalf = round((want + (NE - 1) * DTF + tau_p - T0_BLD) / (TB / 2))
    tf0 = T0_BLD + nhalf * TB / 2 - (NE - 1) * DTF - tau_p
    poster = tf0 + (NE - 1) * DTF + tau_p
    period = np.ceil((tf0 + NE * DTF + HOLD + 0.35) / TB) * TB        # a whole number of sways
    return dict(bld=bld, ts=ts, h=h, recip=recip, xs=xs, zs=zs, img=img, tw=tw, th=th, cols=cols,
                pd=pd, lvl_d=lvl_d, dist=dist, top=top, zb=zb, lvl_b=lvl_b, part_pk=part_pk,
                je=je, dmin=dmin, t_def=t_def, a_def=a_def, t_bw=t_bw, a_bw=a_bw, arrive=arrive,
                conv=conv, t_def2=t_def2, pw=pw, rich=rich, US=US, DTF=DTF, tf0=tf0, poster=poster,
                period=period, nhalf=nhalf)


JS = r"""
/* ---- the cover: W 1000, H 346 (twice the old cover's height) ---- */
const D = DATA, B = D.b, I = D.i;
const NARROW = () => (cv.clientWidth || W) < 480;    // a phone: strokes heavier, the few words left out
const K = () => NARROW() ? 1.8 : 1;                   // stroke widths, times
const lab = t0 => settle(t0, .28) * (NARROW() ? 0 : 1);
const POSTER_T = D.poster;

/* ------------------------------------------------ the clock */
const T0B = D.t0b, P = D.period, TF0 = I.tf0, DTF = I.dtf, US = I.us, NE = I.xe.length;
function Q() { return t < T0B ? 1 : Math.cos(2 * Math.PI * (t - T0B) / B.tb); }   // let go from full sway
const phase = () => ((t % P) + P) % P;

/* ------------------------------------------------ the building: a shear frame in its first mode */
const GY = 322, HS = B.hs, BX = 36, BW = B.bw, NB = B.bays, NS = B.storeys, AMP = B.amp;
const PSI = B.psi;                                    // mode 1 at the base (0) and floors 1 ... 12, roof 1
const fy = n => GY - n * HS;
const sw = (n, q) => q * AMP * PSI[n];
/* a column line j: in each storey the shape of a column fixed at both ends whose ends move apart */
function column(j, q, p) {
  const x0 = BX + j * BW / NB, pts = [];
  for (let n = 1; n <= NS; n++) {
    const a = sw(n - 1, q), b = sw(n, q);
    for (let s = n === 1 ? 0 : 1; s <= 6; s++) { const r = s / 6; pts.push([x0 + a + (b - a) * r * r * (3 - 2 * r), fy(n - 1) - r * HS]); }
  }
  line(pts, { color: C.blue, width: (j % NB ? 1.1 : 1.9) * K(), progress: p });
}
function ground(p) {
  const x0 = BX - 34, x1 = BX + BW + 34;
  line([[x0, GY], [x1, GY]], { width: 1.8 * K(), progress: p });
  if (p < 1) return;
  ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = K(); ctx.beginPath();
  for (let x = x0 + 7; x < x1; x += 7) { ctx.moveTo(x, GY); ctx.lineTo(x - 6, GY + 7); }
  ctx.stroke(); ctx.restore();
}
function building(q, p) {                             // the columns rise; each floor follows
  if (p <= 0) return;
  line([[BX, GY], [BX, GY - HS * NS * p], [BX + BW, GY - HS * NS * p], [BX + BW, GY]], { color: C.rule, width: K() });
  for (let n = 1; n <= NS; n++) {
    if (n / NS > p + 1e-9) break;
    if (NARROW() && n % 2 && n < NS) continue;
    const u = sw(n, q), roof = n === NS;
    line([[BX + u, fy(n)], [BX + BW + u, fy(n)]], { color: roof ? C.navy : C.sky, width: (roof ? 2.4 : .9) * K() });
  }
  for (let j = 0; j <= NB; j++) column(j, q, p);
}
const SENS = [3, 6, 9, 12];                           // accelerometers on the left side, every third floor
function sensors(q) {
  SENS.forEach((n, i) => {
    const a = settle(.3 + .04 * i, .28); if (a <= 0) return;
    const s = 7 * Math.sqrt(K()) * (.6 + .4 * a), x = BX + 3 + s / 2 + sw(n, q), y = fy(n);
    ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy; ctx.fillRect(x - s / 2, y - s - .9, s, s); ctx.restore();
  });
}

/* ------------------------------------------------ the inset: imaging the circled joint */
const FX0 = 270, FX1 = 988, FY0 = 24, FY1 = 322;      // its frame
const S = I.s, PX0 = 290, PY0 = 104;                   // units per mm; the piece's top left corner
const WPu = I.wp * S, DPu = I.dp * S;
const IX0 = PX0 + WPu + 54, IY0 = PY0, IW = WPu, IH = I.zmax * S;   // the image beside it, to the same scale
const px = x => PX0 + x * S, pz = z => PY0 + z * S;
const DF = I.def, CT = Math.cos(DF.tilt * Math.PI / 180), ST = Math.sin(DF.tilt * Math.PI / 180);
const CL = I.cl, T0P = I.t0b, WP = I.wp, DP = I.dp;
function uv(x, z) { const dx = x - DF.x, dz = z - DF.z; return [(dx * CT - dz * ST) / DF.a, (dx * ST + dz * CT) / DF.b]; }
function hits(x1, z1, x2, z2) {                       // does the segment pass through the void?
  const [u1, v1] = uv(x1, z1), [u2, v2] = uv(x2, z2), du = u2 - u1, dv = v2 - v1, L2 = du * du + dv * dv;
  const s = L2 === 0 ? 0 : Math.min(1, Math.max(0, -(u1 * du + v1 * dv) / L2)), cu = u1 + s * du, cv = v1 + s * dv;
  return cu * cu + cv * cv < 1;
}
const inside = (x, z) => x >= 0 && x <= WP && z >= 0 && z <= DP;
/* the fronts of firing k, tc us after the burst's centre: [index, x, z] (mm) of
   the incident circle (cut where the void shadows it), the back wall's echo
   (a circle about the mirror image, cut where the void shadows its path) and
   the void's echo (each boundary point the wave reaches sends it on by the law
   of reflection) */
function frontPts(k, tc) {
  const sx = I.xe[k], R = CL * tc, out = { inc: [], bw: [], df: [] };
  if (R <= 0) return out;
  const n = Math.max(120, Math.ceil(R * 24));
  for (let q = 0; q <= n; q++) {
    const ang = 2 * Math.PI * q / n, c = Math.cos(ang), s = Math.sin(ang);
    const x = sx + R * c, z = R * s;
    if (z >= 0 && inside(x, z) && !hits(sx, 0, x, z)) out.inc.push([q, x, z]);
    const zb = 2 * DP + R * s;
    if (inside(x, zb) && zb < DP) {
      const xw = sx + (DP - 2 * DP) / (zb - 2 * DP) * (x - sx);
      if (!hits(sx, 0, xw, DP) && !hits(xw, DP, x, zb)) out.bw.push([q, x, zb]);
    }
  }
  for (let q = 0; q < 720; q++) {
    const ph = 2 * Math.PI * q / 720, u = DF.a * Math.cos(ph), v = DF.b * Math.sin(ph);
    const qx = DF.x + u * CT + v * ST, qz = DF.z - u * ST + v * CT;
    const gu = Math.cos(ph) / DF.a, gv = Math.sin(ph) / DF.b;
    let nx = gu * CT + gv * ST, nz = -gu * ST + gv * CT; const L = Math.hypot(nx, nz); nx /= L; nz /= L;
    const ex = sx - qx, ez = -qz, d = Math.hypot(ex, ez);
    if (nx * ex + nz * ez <= 0 || R <= d) continue;
    const ix = -ex / d, iz = -ez / d, dn = ix * nx + iz * nz, rx = ix - 2 * dn * nx, rz = iz - 2 * dn * nz;
    const x = qx + (R - d) * rx, z = qz + (R - d) * rz;
    if (inside(x, z)) out.df.push([q, x, z]);
  }
  return out;
}
function runs(pts, wrapN, o) {                        // consecutive samples as strokes (a closed curve's
  if (wrapN && pts.length > 1 && pts[0][0] === 0 && pts[pts.length - 1][0] === wrapN - 1) {   // last run joins its first)
    let i = pts.length - 1; while (i > 0 && pts[i - 1][0] === pts[i][0] - 1) i--;
    pts = pts.slice(i).map(([q, x, z]) => [q - wrapN, x, z]).concat(pts.slice(0, i));
  }
  let run = [], prev = -1e9;
  const flush = () => { if (run.length > 1) line(run, o); run = []; };
  for (const [q, x, z] of pts) { if (q !== prev + 1) flush(); run.push([px(x), pz(z)]); prev = q; }
  flush();
}
function cutEdge(x, y0, y1, p) {                      // a cut through a long member: a small zigzag
  const m = (y0 + y1) / 2;
  line([[x, y0], [x, m - 9], [x - 5, m - 3], [x + 5, m + 3], [x, m + 9], [x, y1]], { color: C.ink, width: 1.3 * K(), progress: p });
}
function piece(p) {
  if (p <= 0) return;
  ctx.save(); ctx.fillStyle = C.steel; ctx.fillRect(PX0, PY0, WPu * clamp(p), DPu); ctx.restore();
  line([[PX0, PY0], [PX0 + WPu, PY0]], { width: 1.7 * K(), progress: p });
  line([[PX0, PY0 + DPu], [PX0 + WPu, PY0 + DPu]], { width: 2.6 * K(), progress: p });
  cutEdge(PX0, PY0, PY0 + DPu, p); cutEdge(PX0 + WPu, PY0, PY0 + DPu, p);
}
function voidShape(o) {                               // the defect: the void, filled and hatched
  const cx = px(DF.x), cz = pz(DF.z), rot = -DF.tilt * Math.PI / 180;
  ctx.save(); ctx.globalAlpha *= o.alpha;
  ctx.beginPath(); ctx.ellipse(cx, cz, DF.a * S, DF.b * S, rot, 0, 2 * Math.PI);
  if (o.dash) { ctx.setLineDash(o.dash); ctx.strokeStyle = C.accent; ctx.lineWidth = 1.3; ctx.stroke(); ctx.restore(); return; }
  ctx.fillStyle = C.accent; ctx.fill();
  ctx.save(); ctx.clip(); ctx.strokeStyle = '#781E2C'; ctx.lineWidth = .9; ctx.beginPath();     // hatched, as his sketch
  for (let x = cx - 44; x < cx + 44; x += 4.4) { ctx.moveTo(x - 16, cz + 16); ctx.lineTo(x + 16, cz - 16); }
  ctx.stroke(); ctx.restore();
  ctx.beginPath(); ctx.ellipse(cx, cz, DF.a * S, DF.b * S, rot, 0, 2 * Math.PI);
  ctx.strokeStyle = '#781E2C'; ctx.lineWidth = 1.2; ctx.stroke(); ctx.restore();
}
const TILE = [];
function tiles() {                                    // the images after 1, 2, ... 16 firings, through SEQ
  const c2 = document.createElement('canvas'); c2.width = IMG.width; c2.height = IMG.height;
  const g2 = c2.getContext('2d'); g2.drawImage(IMG, 0, 0);
  const src = g2.getImageData(0, 0, IMG.width, IMG.height).data;
  for (let k = 0; k < NE; k++) {
    const r0 = Math.floor(k / I.cols) * I.th, c0 = (k % I.cols) * I.tw;
    const tc = document.createElement('canvas'); tc.width = I.tw; tc.height = I.th;
    const tg = tc.getContext('2d'), im = tg.createImageData(I.tw, I.th);
    for (let y = 0; y < I.th; y++) for (let x = 0; x < I.tw; x++) {
      const v = src[((r0 + y) * IMG.width + c0 + x) * 4], o = (y * I.tw + x) * 4;
      im.data[o] = SEQ[v * 3]; im.data[o + 1] = SEQ[v * 3 + 1]; im.data[o + 2] = SEQ[v * 3 + 2]; im.data[o + 3] = 255;
    }
    tg.putImageData(im, 0, 0); TILE.push(tc);
  }
}
function tip(x, y, ang, color, size, alpha) {         // a TikZ stealth tip at (x, y)
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(x, y);
  ctx.lineTo(x - size * Math.cos(ang - .38), y - size * Math.sin(ang - .38));
  ctx.lineTo(x - size * .62 * Math.cos(ang), y - size * .62 * Math.sin(ang));
  ctx.lineTo(x - size * Math.cos(ang + .38), y - size * Math.sin(ang + .38)); ctx.closePath(); ctx.fill(); ctx.restore();
}
function inset() {
  const ph = phase(), lp = Math.floor(t / P);
  const k = ph < TF0 ? -1 : Math.floor((ph - TF0) / DTF);               // the firing under way
  const fired = k >= 0 && k < NE, tau = fired ? (ph - TF0 - k * DTF) * US : 0;   // us since its burst began
  const reset = lp === 0 && ph < TF0 ? 1 : 1 - clamp((ph - (P - .35)) / .3);
  piece(seg(.1, .3));
  // this firing's fronts, inside the piece
  if (fired) {
    const tc = tau - T0P, F = frontPts(k, tc), R = CL * Math.max(tc, .05);
    const a = clamp(Math.sqrt(4 / R), .35, 1), tail = 1 - clamp((tau - (I.tfire - .6)) / .6);
    ctx.save(); ctx.beginPath(); ctx.rect(PX0, PY0, WPu, DPu); ctx.clip();
    runs(F.inc, 0, { color: C.blue, width: 2.2 * K(), alpha: a * tail });
    runs(F.bw, 0, { color: C.sky, width: 1.9 * K(), alpha: .9 * a * tail });
    runs(F.df, 720, { color: C.accent, width: 2.4 * K(), alpha: Math.max(.55, a) * tail });
    ctx.restore();
  }
  voidShape({ alpha: settle(.22, .28) });
  // the array: each element fires in turn, all receive
  const ap = settle(.16, .28), ew = I.ew * S, pitch = (I.xe[1] - I.xe[0]) * S, ah = 14;
  const ax0 = px(I.xe[0]) - pitch / 2, ax1 = px(I.xe[NE - 1]) + pitch / 2, ay0 = PY0 - ah + 4 * (1 - ap);
  ctx.save(); ctx.globalAlpha *= ap; ctx.fillStyle = C.navy; ctx.fillRect(ax0, ay0, ax1 - ax0, ah);
  for (let j = 0; j < NE; j++) {
    const x = px(I.xe[j]);
    if (fired) {
      const hit = tau - T0P - I.arrive[k][j];             // the void's echo reaches element j
      if (hit > 0) { ctx.save(); ctx.globalAlpha *= Math.exp(-hit / 1.5) * .9; ctx.fillStyle = C.accent; ctx.fillRect(x - ew / 2, ay0, ew, ah); ctx.restore(); }
      if (j === k) { ctx.save(); ctx.globalAlpha *= clamp(1 - (tau - I.dur) / 1.5, .35, 1); ctx.fillStyle = C.amber; ctx.fillRect(x - ew / 2, ay0, ew, ah); ctx.restore(); }
    }
  }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = .9;
  for (let j = 1; j < NE; j++) { const x = (px(I.xe[j - 1]) + px(I.xe[j])) / 2; ctx.beginPath(); ctx.moveTo(x, ay0); ctx.lineTo(x, ay0 + ah); ctx.stroke(); }
  ctx.restore();
  if (fired) tip(px(I.xe[k]), ay0 - 3, Math.PI / 2, C.amber, 9, ap);
  // the image, firing by firing, beside the piece
  arrow(PX0 + WPu + 12, PY0 + DPu / 2, IX0 - 12, PY0 + DPu / 2, { width: 2.6 * K(), head: 12, alpha: settle(.35, .28) });
  const done = ph < TF0 ? 0 : Math.min(NE, Math.floor((ph - TF0) / DTF));
  const show = done;
  if (TILE.length && show > 0 && reset > 0) {
    const tin = (ph - TF0 - show * DTF) / .15, cur = TILE[show - 1];
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.globalAlpha *= reset;
    if (show > 1 && tin < 1) { ctx.drawImage(TILE[show - 2], IX0, IY0, IW, IH); ctx.globalAlpha *= clamp(tin); }
    else if (show === 1 && tin < 1) ctx.globalAlpha *= clamp(tin);
    ctx.drawImage(cur, IX0, IY0, IW, IH); ctx.restore();
  }
  line([[IX0, IY0], [IX0 + IW, IY0], [IX0 + IW, IY0 + IH], [IX0, IY0 + IH], [IX0, IY0]], { width: 1.4 * K(), progress: seg(.15, .35) });
  if (show > 0 && reset > 0) {
    // the void where it is, over the image
    const cx = IX0 + DF.x * S, cz = IY0 + DF.z * S;
    ctx.save(); ctx.globalAlpha *= .9 * reset * clamp((ph - TF0 - DTF) / .3); ctx.setLineDash([3, 3]); ctx.strokeStyle = C.accent; ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.ellipse(cx, cz, DF.a * S, DF.b * S, -DF.tilt * Math.PI / 180, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
  }
}

function draw() {
  const q = Q();
  ground(seg(0, .25));
  building(q, seg(.02, .36));
  sensors(q);
  // the inset's frame, and the circled joint with the arrow to it
  line([[FX0, FY0], [FX1, FY0], [FX1, FY1], [FX0, FY1], [FX0, FY0]], { width: 1.3 * K(), progress: seg(.08, .36) });
  const ua = settle(.28, .28), jx = BX + BW + sw(B.joint, q), jy = fy(B.joint), r = 11;
  if (ua > 0) {
    ctx.save(); ctx.globalAlpha *= ua; ctx.beginPath(); ctx.arc(jx, jy, r, 0, 2 * Math.PI); ctx.lineWidth = 1.4 * K(); ctx.strokeStyle = C.ink; ctx.stroke(); ctx.restore();
    const ar = seg(.3, .25);
    if (ar > 0) arrow(jx + r + 3, jy, lerp(jx + r + 3, FX0 - 3, ar), jy, { width: 1.3 * K(), head: 10 });
  }
  inset();
  // the two words
  math('f_1 = ' + B.f1.toFixed(2) + '\\,\\rm{Hz}', BX + BW + 22, 52, { size: 18, color: C.body, alpha: lab(.34) });
  text('imaging', FX0 + 18, FY0 + 40, { size: 21, color: C.ink, alpha: lab(.3) });
}
const IMG = new Image();
IMG.src = I.img;
const READY = IMG.decode().then(tiles).catch(() => {});   // the image tiles; drawn once ready
if (STILL) READY.then(boot, boot);
else boot();
"""

TITLE = "A building's first mode, and ultrasonic imaging of a defect in one of its joints"
ARIA = ("A tall building sways in its first vibration mode with sensors on its floors. A circled joint "
        "is shown magnified: an ultrasonic array on a steel plate fires its elements one after another, "
        "the waves echo from a small defect and the back wall, and the image built from the echoes "
        "beside it reveals the defect.")


def page_data(r):
    b = r["bld"]
    return {
        "t0b": T0_BLD, "period": r["period"], "poster": r["poster"],
        "b": {"tb": b["T1"], "f1": b["f"][0], "psi": b["psi"], "hs": 24.0, "bw": 103.0, "bays": BAYS,
              "storeys": N_ST, "amp": 11.0, "joint": 4},
        "i": {"xe": XE, "ew": EW, "wp": WP, "dp": DP, "def": DEF, "cl": F.CL, "t0b": T0B, "dur": DUR,
              "us": r["US"], "tf0": r["tf0"], "dtf": r["DTF"], "tfire": T_FIRE, "s": 10.5,
              "arrive": r["arrive"], "img": r["img"], "tw": r["tw"], "th": r["th"], "cols": r["cols"],
              "zmax": ZMAX, "pix": PIX, "db": DB},
    }


def page_check(r):
    """The page's fronts against the Python port, at several firings and moments."""
    import guided_ut as G
    cases = []
    for k, tc in [(0, 1.0), (5, 2.2), (9, 2.6), (9, 4.1), (15, 3.0 - T0B), (12, 5.6)]:
        ref = fronts_py(k, tc)
        for key in ("inc", "bw", "df"):
            arr = np.array(ref[key], float).reshape(-1, 3)
            cases.append((f"frontPts({k}, {tc!r}).{key}.flat()", arr.ravel()))
    worst = 0.0
    from playwright.sync_api import sync_playwright
    path = os.path.join(common.ANIM, f"nf-{NAME}.html").replace("\\", "/")
    counts = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto("file:///" + path + "?still")
        pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
        for expr, ref in cases:
            got = np.array(pg.evaluate(f"Array.from({expr})"), float)
            counts.append((len(got) // 3, len(ref) // 3))
            if got.shape != ref.shape:
                worst = np.inf
                continue
            if got.size:
                worst = max(worst, float(np.abs(got - ref).max()))
        b.close()
    del G
    return worst, counts


def report(r, page, counts, over):
    L = []
    say = L.append
    b = r["bld"]
    f = b["f"]
    say("nf-shm-cover: the SHM and NDT guide's cover (image1), twice the old height (1000 x 346)")
    say("generator: tools/numfig/shm_cover.py; model imported: shm_fdtd.py (the elastic scheme of the SHM")
    say("guide's Figure 3, nf-shm-ndt; its own checks in shm_ndt.check.txt); the checks that bear on this")
    say("page are run here.")
    say("")
    say("THE BUILDING (left): a 12 storey steel moment frame as a shear building")
    say(f"  {N_ST} storeys of {H_ST:g} m ({N_ST*H_ST:g} m), {BAYS} x {BAYS} bays of {BAY:g} m ({BAYS*BAY:g} x {BAYS*BAY:g} m plan),"
        f" {N_COL} columns per storey")
    say(f"  floors rigid, each storey's columns fixed at both ends: storey stiffness k = {N_COL} x 12 E I / h^3,")
    say(f"  HE 360 B columns, I = {I_COL*1e8:,.0f} cm^4 (strong axis), E = {E_ST/1e9:g} GPa, h = {H_ST:g} m:"
        f" k = {b['k']/1e6:.1f} MN/m")
    say(f"  floor mass m = {M_FL/1e3:g} t (1.2 t/m^2 over the plan), the roof's the same; K tridiagonal, M = m I,")
    say("  eigenvalues by scipy.linalg.eigh")
    say(f"  f1 = {f[0]:.4f} Hz (T1 = {b['T1']:.3f} s), f2 = {f[1]:.4f} Hz, f3 = {f[2]:.4f} Hz; mode 1 moves"
        f" {b['meff']*100:.1f} % of the mass")
    say(f"  (T1 against the rule of thumb T = N/10 = {N_ST/10:.1f} s for a frame of N storeys: the right size)")
    say("  CHECK 1: the uniform chain fixed at its foot and free at its top has, in closed form,")
    say("    omega_j = 2 sqrt(k/m) sin((2j - 1) pi / (2 (2N + 1))), phi_j(n) = sin(n (2j - 1) pi / (2N + 1)):")
    for j in range(3):
        say(f"    f{j+1} = {f[j]:.10f} Hz, closed form {b['w_cf'][j]/(2*np.pi):.10f} Hz"
            f" ({f[j]/(b['w_cf'][j]/(2*np.pi))-1:+.1e})")
    say(f"    modes 1 to 3 against sin(n (2j - 1) pi / (2N + 1)), 1 at the roof: largest difference {b['shape_err']:.1e}")
    say("  CHECK 2: free vibration from mode 1's shape, Newmark's average acceleration, dt = T1/400,")
    say(f"    six periods: the roof's period from its {b['nz']} downward zero crossings {b['T_nm']:.6f} s; the")
    say(f"    method's own period pi dt / atan(omega_1 dt / 2) = {b['T_nm_cf']:.6f} s"
        f" ({b['T_nm']/b['T_nm_cf']-1:+.1e}); T1 = {b['T1']:.6f} s")
    say(f"    ({b['T_nm']/b['T1']-1:+.1e}, the method's known lengthening (omega dt)^2/12 ="
        f" {(2*np.pi/400)**2/12:.1e}); the motion stays in mode 1")
    say(f"  drawn: mode 1 alone, u_n(t) = phi_1(n) U cos(2 pi f1 (t - {T0_BLD})), let go from full sway at"
        f" t = {T0_BLD} s, in real time")
    say(f"    (a sway every {b['T1']:.3f} s); {N_ST*H_ST:g} m drawn {24*N_ST:g} units (24 per storey), {BAYS*BAY:g} m"
        " drawn 103 units; the roof's sway drawn 11 units")
    say("    (enlarged: the shape is exact, its size is not a prediction); between two floors each column")
    say("    line takes the fixed-fixed shape u = u_(n-1) + (u_n - u_(n-1)) (3 s^2 - 2 s^3), the shear building's;")
    say("    its rest outline in the rule's grey; accelerometers on floors 3, 6, 9 and 12, on the left side;")
    say("    the circled joint: the right hand column at floor 4, its beam to column connection")
    say("")
    say("THE INSET, imaging (right): the circled joint's 16 mm steel flange at the NDT scale")
    say("  model: shm_fdtd.py, 2D plane strain elastodynamics, velocity-stress on a staggered grid (Virieux")
    say("  1986), voids as cells of zero density and stiffness (EFIT, Fellinger et al. 1995), every face")
    say(f"  traction free; steel c_L = {F.CL*1e3:.0f} m/s, c_T = {F.CT*1e3:.0f} m/s, rho = {F.RHO_SI:.0f} kg/m3")
    say(f"  piece {DP:g} mm thick, {WP:g} mm drawn of {WP+2*MARG:g} mm modelled (nothing returns from its ends within"
        f" the {T_REC:g} us recorded)")
    say(f"  defect: an elliptical void {2*DEF['a']:g} x {2*DEF['b']:g} mm, centre ({DEF['x']:g}, {DEF['z']:g}) mm,"
        f" tilted {DEF['tilt']:g} deg (right end up); its top at ({r['top'][0]:.2f}, {r['top'][1]:.3f}) mm")
    say(f"  array: {NE} elements, pitch {PITCH:g} mm (half a P wavelength at {F0:g} MHz is {F.CL/F0/2:.3f} mm),"
        f" width {EW:g} mm, centres x = {XE[0]:.2f} ... {XE[-1]:.2f} mm")
    say(f"  each element sends a {NC} cycle Hann burst at {F0:g} MHz ({DUR:g} us; a uniform normal traction on")
    say("  its face), all receive (the mean normal velocity over each face): full matrix capture, 16 runs")
    say(f"  grid: dx = {DX} mm ({F.CL/F0/DX:.1f} points per P wavelength, {F.CT/F0/DX:.1f} per S), CFL {F.CFL}")
    say("  the direct waves (under the transmitter, along the array) taken out with a run in a half space")
    say("  at the same element distance |i - j| (as shm_ndt.py)")
    say(f"  CHECK 3: the scheme's P travel time: a 60 mm probe (a near plane wave) on the {DP:g} mm piece,")
    say("    no void, its back wall echo (envelope peak from the burst's centre):")
    for dx, t_ in r["pw"]:
        say(f"    dx = {dx:5.3f} mm: {t_:.4f} us")
    say(f"    Richardson (second order, 0.05 and 0.025 mm): {r['rich']:.4f} us; 2d/c_L = {2*DP/F.CL:.4f} us,"
        f" error {(r['rich']/(2*DP/F.CL)-1)*100:+.3f} %")
    say(f"  CHECK 4: the echoes in the full matrix capture (dx = {DX} mm), envelope peaks from the burst's centre:")
    say(f"    element {r['je']+1} (x = {XE[r['je']]:.2f} mm, over the void's top) hears the void at"
        f" {r['t_def']:.3f} us; twice its nearest distance to the")
    say(f"    void ({r['dmin']:.3f} mm) over c_L is {2*r['dmin']/F.CL:.3f} us ({r['t_def']-2*r['dmin']/F.CL:+.3f} us;"
        f" at dx = {DX/2:g} mm {r['t_def2']:.3f} us)")
    say(f"    element 1 (x = {XE[0]:.2f} mm, clear of the void) hears the back wall at {r['t_bw']:.3f} us;"
        f" 2d/c_L = {2*DP/F.CL:.3f} us")
    say(f"    ({(r['t_bw']/(2*DP/F.CL)-1)*100:+.2f} %: a 1.3 mm element is no plane wave; CHECK 3 times the scheme)")
    say(f"  CHECK 5: reciprocity of the scattered data: max|h_ij - h_ji| / max|h| = {r['recip']:.1e}")
    say("  total focusing: I(x, z) = |sum_i sum_j H[h_ij](t_i + t_j)|, t = distance / c_L from each element's")
    say(f"  centre, the burst's centre as time zero, {PIX:g} mm pixels over x = 0 ... {WP:g} mm, z = 0 ... {ZMAX:g} mm;")
    say("  after the k-th firing the page shows the partial sum, |sum over transmitters 1 ... k| / 16, in dB")
    say(f"  of the complete image's peak, {DB:g} dB range: the image forms out of white as the elements fire")
    say(f"  (after 1, 4, 8 and 15 firings its peak is " + ", ".join(f"{r['part_pk'][q]:+.1f}" for q in (0, 3, 7, 14))
        + " dB)")
    say(f"  CHECK 6: the image: the void's peak at ({r['pd'][0]:.2f}, {r['pd'][1]:.2f}) mm, {r['lvl_d']:+.1f} dB,"
        f" {r['dist']:.2f} mm from the void's boundary (its top")
    say(f"    at ({r['top'][0]:.2f}, {r['top'][1]:.2f}) mm: the echo comes from the face the waves see); the back wall"
        f" imaged at z = {r['zb']:.2f} mm (true {DP:g}),")
    say(f"    {r['lvl_b']:+.1f} dB, at x = 6 mm, clear of the void's shadow")
    c = r["conv"]
    say(f"  CHECK 7: the grid: the full matrix capture again at dx = {DX/2:g} mm (59 points per P wavelength):")
    say(f"    the complete image's void peak at ({c['pd2'][0]:.2f}, {c['pd2'][1]:.2f}) mm, {c['lvl2']:+.1f} dB (at dx = {DX:g} mm"
        f" ({r['pd'][0]:.2f}, {r['pd'][1]:.2f}) mm, {r['lvl_d']:+.1f} dB);")
    say(f"    the two images, each over its own peak, differ by {c['tfm_diff']:.3f} at most (of 1)")
    say("  the fronts drawn (the page's frontPts): the incident circle c_L t about the transmitter, cut where")
    say("    the void shadows it; the back wall's echo, a circle about the transmitter's mirror image in the")
    say("    back wall, cut where the void shadows its path; the void's echo, each boundary point the wave")
    say("    reaches (n . (S - Q) > 0) sending it on along the reflected ray Q + (c_L t - |SQ|) r(Q),")
    say("    r = i - 2 (i . n) n: the law of reflection off the ellipse. A receiver lights up when the")
    say("    void's first echo reaches it: min over Q seen from both of (|SQ| + |QR|) / c_L, from the burst's centre")
    say(f"  CHECK 8: the page's own fronts against the Python port, 6 moments x 3 fronts: largest difference {page:.1e} mm")
    say("    (points kept: " + ", ".join(f"{g}" for g, _ in counts) + ")")
    say("")
    say("DRAWING AND CLOCK")
    say(f"  the inset at 10.5 units per mm (7.1 px per mm at 672 px), the piece and the image side by side,")
    say("  to the same scale; the defect accent filled and hatched (his sketch), drawn dashed over the image")
    say("  fronts: incident C.blue 2.2, the back wall's echo C.sky 1.9, the void's echo crimson 2.4; their")
    say("  opacity falls as 1/sqrt(r) (cylindrical spreading), from 1 at r = 4 mm to 0.35 (the void's echo")
    say("  never below 0.55); the receivers flash crimson as the void's echo arrives, fading over 1.5 us")
    say(f"  the waves' time slowed 10^5 ({r['US']:g} us of the model per second); a firing every {r['DTF']:.2f} s"
        f" ({T_FIRE:g} us shown each), 16 firings")
    say(f"  from t = {r['tf0']:.3f} s; the image complete from {r['tf0']+NE*r['DTF']:.2f} s; the loop is {r['period']:.3f} s,"
        f" {r['period']/b['T1']:.0f} sways of the building,")
    say("  the image fading in its last 0.35 s; the building's motion has no seam (one cosine).")
    say(f"  the still (print, and a reader who asks for less motion): t = {r['poster']:.3f} s, {POSTER_TAU:g} us into"
        f" the 16th firing (the void's echo on its way back),")
    say(f"  the image of 15 firings beside it, and the building at full sway ({r['nhalf']} half sways after it is let go)")
    say("")
    say("OVERLAP (engine ?overlap, common.overlaps at 672 px; common.still also samples every 0.25 s")
    say("  up to the poster):")
    for kk, v in over.items():
        say(f"  {kk}: labels {v['labels'] or 'none'}, crossings {v['crossings'] or 'none'}")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(HERE, "shm_cover.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


def build():
    r = model()
    b = r["bld"]
    print(f"building: f1 = {b['f'][0]:.4f} Hz, T1 = {b['T1']:.4f} s; imaging: void peak {r['pd']}, "
          f"back wall {r['zb']:.2f} mm; loop {r['period']:.3f} s, poster {r['poster']:.3f} s")
    common.build_html(NAME, TITLE, ARIA, W, H, page_data(r), wt_lib.QUIET_CTL + "\n" + JS)
    page, counts = page_check(r)
    png = common.still(NAME, width=672)
    print("still:", png)
    P = r["period"]
    times = [0.3, 0.6, 1.0, 2.0, 4.4, 7.7, r["poster"] - 0.2, r["poster"], P - 0.2, P + 1.3, P + 5.0]
    over = common.overlaps(NAME, times)
    report(r, page, counts, over)
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.1, 0.25, 0.45, 0.8, 1.4, 3.0, r["poster"], P - 0.3, P + 0.6]))
    return r


if __name__ == "__main__":
    build()
