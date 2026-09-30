"""Figure 3 of the SHM article (understanding-shm-and-ndt, image4): NDT.

His caption: "NDT: (a) ultrasonic testing, pulse echo, an active technique.
(b) acoustic emission, a passive technique. (c) ultrasonic testing,
imaging, an active technique." His own animation (archived in
content/anim-originals/fig3-ndt-techniques.html) sketched the three; this
redraw keeps his panels, his words and his motion beats, and takes every
wave, echo and image from a model (shm_fdtd.py, 2D elastic, steel):

(a) A 12 mm, 2 MHz contact probe on a steel beam 40 mm deep; a crack 14 mm
    long, 17 mm down at its centre, tilted 13 degrees, lies under the right
    half of the probe. The recorded signal is the model's: the mean normal
    velocity under the probe, over its peak while it sends. The pulses in
    the two lanes under the probe travel at c_L and turn at the crack and
    the back wall where the model's geometry puts them.
(b) Acoustic emission: a crack grows from the underside of a 30 mm steel
    beam in four steps; each step sends out a P wave front, radius c_L t,
    which the sensor on top hears r/c_L later (checked against the model
    with a moment source at the tip).
(c) A 16 element, 2 MHz array on a 12 mm steel wall with a crack tilted
    20 degrees: each element transmits in turn and all receive (full
    matrix capture); the total focusing method builds the image,
    transmitter by transmitter. The fronts drawn are the geometric ones of
    the same model: incident (with the crack's shadow), the crack's
    specular reflection and its edge diffraction, and the back wall's echo.

Run: python tools/numfig/shm_ndt.py   (writes content/anim/nf-shm-ndt.html
and .webp and tools/numfig/shm_ndt.check.txt; the model runs are cached in
the temp directory)
"""
import base64
import io
import os
import sys

import numpy as np
from PIL import Image
from scipy.signal import hilbert

import common
import shm_fdtd as F

NAME = "shm-ndt"
HERE = os.path.dirname(os.path.abspath(__file__))

SLOW = 1e5                         # time slowed: 10 us of the model per second
US = 1e6 / SLOW                    # us of model time per second of the page
F0, NC = 2.0, 3                    # the burst: MHz, cycles (Hann)
DUR = NC / F0                      # 1.5 us
T0B = 0.5 * DUR                    # its centre: time zero of the recorded signal
DX = 0.1                           # mm (29.5 points per P wavelength, 16 per S)

# (a) pulse echo: a long beam (the page draws 50 mm of it), probe at x = 55 mm
A_W, A_D = 110.0, 40.0
A_PX, A_PW = 55.0, 12.0
A_CR = dict(x=61.0, z=17.0, a=7.0, b=0.25, tilt=13.0)
A_T = 17.0                         # us recorded
A_WIN = (30.0, 80.0)               # the part of the beam drawn
A_LANES = (0.5, 4.0)               # the lanes, mm right of the probe's axis

# (b) acoustic emission: his crack path, growing in four steps from the underside
B_W, B_D = 120.0, 30.0
B_CRACK = [(19.9, 30.0), (29.9, 21.7), (36.2, 25.9), (45.3, 17.6), (53.4, 24.5), (59.8, 15.2)]
B_SENSOR = (26.7, 8.0)             # centre and width on the top face, mm
B_EVENTS = [0.55, 2.55, 4.55, 6.55]

# (c) imaging: a wall 12 mm thick, 40 mm of it drawn, the model 25 mm longer each side
C_W, C_D, C_M = 40.0, 12.0, 25.0
C_CR = dict(x=24.0, z=8.0, a=4.0, b=0.25, tilt=20.0)
C_N, C_P, C_EW = 16, 1.5, 1.3
C_XE = 20.0 + C_P * (np.arange(C_N) - (C_N - 1) / 2)
C_T = 8.0
C_T0, C_DT = 0.6, 0.4              # first firing and the interval between firings (page s)
C_IMG = dict(dx=0.2, zmax=14.0, db=24.0)

MASTER = 8.4                       # the loop: (a) twice, (b) four events, (c) sixteen firings
A_T0 = 0.5


def drive(t):
    return F.burst(t, F0, NC)


def stamp(dx):
    return F.CFL * dx / F.CL


def env_peak(t, s, lo, hi):
    """Time and value of the envelope's maximum in [lo, hi], parabolic refine."""
    e = np.abs(hilbert(s))
    idx = np.where((t >= lo) & (t <= hi))[0]
    m = idx[np.argmax(e[idx])]
    a, b, c = e[m - 1], e[m], e[m + 1]
    d = 0.5 * (a - c) / (a - 2 * b + c)
    return t[m] + d * (t[1] - t[0]), b - 0.25 * (a - c) * d


# ------------------------------------------------------------------ (a)
def a_run(dx, crack=True, depth=A_D, pw=A_PW):
    dt = stamp(dx)
    solid, X, Z = F.block(A_W, depth, dx)
    if crack:
        F.cut(solid, X, Z, A_CR)
    src = F.cells(A_PX - pw / 2, pw, dx)
    ns = int(round(A_T / dt))
    return F.run(solid, src, [src], ns, dx, dt, drive)[0], np.array(dt)


def a_model(dx, crack=True, depth=A_D, pw=A_PW):
    key = (dx, crack, depth, pw, A_W, A_PX, A_CR, F0, NC, A_T)
    rec, dt = F.cached("a", key, lambda: a_run(dx, crack, depth, pw))
    dt = float(dt)
    ts = (np.arange(rec.size) + 0.5) * dt - T0B
    return ts, rec


def crack_ends(cr):
    th = np.radians(cr["tilt"])
    return [(cr["x"] - s * cr["a"] * np.cos(th), cr["z"] + s * cr["a"] * np.sin(th)) for s in (1, -1)]


def depth_at(cr, x):
    (x0, z0), (x1, z1) = crack_ends(cr)
    return z0 + (z1 - z0) * (x - x0) / (x1 - x0)


# ------------------------------------------------------------------ (b)
def b_run(dx):
    """The beam with the crack grown to its last point (a void 0.3 mm wide
    along the path), a moment source just past the tip; the mean v_z under
    the sensor."""
    dt = stamp(dx)
    solid, X, Z = F.block(B_W, B_D, dx)
    near = np.zeros(X.shape, bool)
    pts = np.array(B_CRACK)
    for (xa, za), (xb, zb) in zip(pts[:-1], pts[1:]):
        ux, uz = xb - xa, zb - za
        s = np.clip(((X - xa) * ux + (Z - za) * uz) / (ux * ux + uz * uz), 0, 1)
        near |= np.hypot(X - xa - s * ux, Z - za - s * uz) <= 0.15
    solid[F.PAD:F.PAD + X.shape[0], F.PAD:F.PAD + X.shape[1]] &= ~near
    tip = pts[-1] + 0.35 * (pts[-1] - pts[-2]) / np.linalg.norm(pts[-1] - pts[-2])
    point = (F.PAD + int(tip[0] / dx), F.PAD + int(tip[1] / dx))
    assert solid[point]
    rec_cells = F.cells(B_SENSOR[0] - B_SENSOR[1] / 2, B_SENSOR[1], dx)
    rise = 0.5                                    # us: the moment rate, a Hann pulse
    rate = lambda t: np.where((t >= 0) & (t <= rise), np.sin(np.pi * t / rise) ** 2, 0.0)
    ns = int(round(12.0 / dt))
    rec = F.run(solid, None, [rec_cells], ns, dx, dt, rate, point=point)[0]
    src = np.array([(point[0] - F.PAD + .5) * dx, (point[1] - F.PAD + .5) * dx])
    return rec, np.array(dt), src


# ------------------------------------------------------------------ (c)
def c_fmc():
    dt = stamp(DX)
    solid, X, Z = F.block(C_W + 2 * C_M, C_D, DX)
    cr = dict(C_CR, x=C_CR["x"] + C_M)
    F.cut(solid, X, Z, cr)
    els = [F.cells(C_M + x - C_EW / 2, C_EW, DX) for x in C_XE]
    ns = int(round(C_T / dt))
    data = np.array([F.run(solid, els[i], els, ns, DX, dt, drive) for i in range(C_N)])
    # the direct waves (the pulse under the transmitter, the surface waves
    # along the array): one run in a half space, used at each distance |i - j|
    half, _, _ = F.block(90.0, 40.0, DX)
    rels = [F.cells(30.0 + C_P * k - C_EW / 2, C_EW, DX) for k in range(C_N)]
    ref = F.run(half, rels[0], rels, ns, DX, dt, drive)
    return data, ref, np.array(dt)


def tfm(h, ts, xs, zs):
    """Per transmitter complex contributions C_i(x, z) = sum_j H[h_ij](t_i + t_j)."""
    Hs = hilbert(h, axis=2)
    dt = ts[1] - ts[0]
    Xg, Zg = np.meshgrid(xs, zs, indexing="ij")
    tau = np.sqrt((Xg[None] - C_XE[:, None, None]) ** 2 + Zg[None] ** 2) / F.CL
    out = np.zeros((C_N,) + Xg.shape, complex)
    for i in range(C_N):
        for j in range(C_N):
            f = (tau[i] + tau[j] - ts[0]) / dt
            m = np.floor(f).astype(int)
            w = f - m
            ok = (m >= 0) & (m + 1 < ts.size)
            m = np.clip(m, 0, ts.size - 2)
            out[i] += np.where(ok, (1 - w) * Hs[i, j][m] + w * Hs[i, j][m + 1], 0)
    return out


def seg_hits(p0, p1, q0, q1):
    """Whether segments p0p1 and q0q1 cross."""
    d = lambda a, b, c: (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return (d(p0, p1, q0) * d(p0, p1, q1) < 0) and (d(q0, q1, p0) * d(q0, q1, p1) < 0)


def png_uri(a):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


# ------------------------------------------------------------------ main
def main():
    rep = []
    say = lambda s="": rep.append(s)
    c = F.CL

    # ---- (a)
    ts, ra = a_model(DX)
    v0 = np.abs(ra[ts < 1.0]).max()
    va = ra / v0
    z1 = depth_at(A_CR, A_PX + A_LANES[0])
    z2 = depth_at(A_CR, A_PX + A_LANES[1])
    tc, ac = env_peak(ts, va, 4.8, 7.8)
    tb, ab = env_peak(ts, va, 12.5, 15.0)
    ts0, r0 = a_model(DX, crack=False)
    tb0, ab0 = env_peak(ts0, r0 / np.abs(r0[ts0 < 1.0]).max(), 12.5, 15.0)
    env = np.abs(hilbert(va))
    gap = env[(ts > tc + 1.3) & (ts < tb - 1.3)].max()
    # the crack echo's own window (for its colour): where its envelope is above 3 % of the peak
    win = (ts > tc - 1.6) & (ts < tc + 1.6) & (env > 0.03)
    cwin = [float(ts[win].min()), float(ts[win].max())]
    (x0, zz0), (x1, zz1) = crack_ends(A_CR)

    # ---- (a) the grid, and the scheme's travel time on its own
    conv = []
    for dx in (0.1, 0.05, 0.025):
        t_, r_ = a_model(dx)
        r_ = r_ / np.abs(r_[t_ < 1.0]).max()
        conv.append((dx, env_peak(t_, r_, 4.8, 7.8), env_peak(t_, r_, 12.5, 15.0)))
    pw = []
    for dx in (0.1, 0.05, 0.025):
        t_, r_ = a_model(dx, crack=False, pw=80.0)
        pw.append((dx, env_peak(t_, r_ / np.abs(r_[t_ < 1.0]).max(), 12.5, 15.0)[0]))
    rich = pw[2][1] + (pw[2][1] - pw[1][1]) / 3

    # ---- (b)
    rb, dtb, src = F.cached("b", (DX, B_W, B_D, B_CRACK, B_SENSOR, 2), lambda: b_run(DX))
    dtb = float(dtb)
    tsb = (np.arange(rb.size) + 0.5) * dtb
    first = tsb[np.argmax(np.abs(rb) > 0.02 * np.abs(rb).max())]
    sx0, sx1 = B_SENSOR[0] - B_SENSOR[1] / 2, B_SENSOR[0] + B_SENSOR[1] / 2
    near_x = np.clip(src[0], sx0, sx1)
    rmin = np.hypot(src[0] - near_x, src[1])
    # the arrival at the sensor's centre, for each event, as the page times it
    hits = []
    for k in range(4):
        tip = np.array(B_CRACK[k + 2])
        nx = np.clip(tip[0], sx0, sx1)
        hits.append(float(np.hypot(tip[0] - nx, tip[1]) / c))

    # ---- (c)
    data, ref, dtc = F.cached("c", (DX, C_W, C_D, C_M, C_CR, C_N, C_P, C_EW, F0, NC, C_T, 2), c_fmc)
    dtc = float(dtc)
    tsc = (np.arange(data.shape[2]) + 0.5) * dtc - T0B
    h = data.copy()
    for i in range(C_N):
        for j in range(C_N):
            h[i, j] -= ref[abs(i - j)]
    recip = np.abs(h - h.transpose(1, 0, 2)).max() / np.abs(h).max()
    xs = np.arange(0, C_W + 1e-9, C_IMG["dx"])
    zs = np.arange(0, C_IMG["zmax"] + 1e-9, C_IMG["dx"])
    Ci = tfm(h, tsc, xs, zs)
    parts = np.cumsum(Ci, axis=0) / np.arange(1, C_N + 1)[:, None, None]
    full = np.abs(parts[-1])
    peak = full.max()
    tiles = np.clip(20 * np.log10(np.abs(parts) / peak + 1e-12), -C_IMG["db"], 0)
    tiles8 = np.round((tiles + C_IMG["db"]) / C_IMG["db"] * 255).astype(np.uint8)   # (k, x, z)
    cols = 4
    th_, tw_ = zs.size, xs.size
    atlas = np.zeros((4 * th_, cols * tw_), np.uint8)
    for k in range(C_N):
        r_, c_ = divmod(k, cols)
        atlas[r_ * th_:(r_ + 1) * th_, c_ * tw_:(c_ + 1) * tw_] = tiles8[k].T
    img = png_uri(atlas)
    Xg, Zg = np.meshgrid(xs, zs, indexing="ij")
    (cx0, cz0), (cx1, cz1) = crack_ends(C_CR)
    above = Zg < C_D - 1.5
    jc = np.unravel_index(np.argmax(np.where(above, full, 0)), full.shape)
    pc = np.array([xs[jc[0]], zs[jc[1]]])
    u = np.linspace(0, 1, 2001)
    cl = np.stack([cx0 + u * (cx1 - cx0), cz0 + u * (cz1 - cz0)], 1)
    dist = np.min(np.hypot(cl[:, 0] - pc[0], cl[:, 1] - pc[1]))
    ib = np.argmin(np.abs(xs - 12.0))
    zb = zs[np.argmax(full[ib])]
    lvl_bw = 20 * np.log10(full[ib].max() / peak)
    # the first crack echo at each receiver, per transmitter (us after the burst's start)
    q = np.stack([cx0 + np.linspace(0, 1, 401) * (cx1 - cx0), cz0 + np.linspace(0, 1, 401) * (cz1 - cz0)], 1)
    d_e = np.hypot(q[None, :, 0] - C_XE[:, None], q[None, :, 1])            # (element, point)
    arrive = np.min(d_e[:, None, :] + d_e[None, :, :], axis=2) / c          # (i, j)

    # ---- the page's clock
    last_hit = B_EVENTS[3] + hits[3] / US
    poster = round(last_hit + 0.06, 3)
    pa = (poster - A_T0) % (MASTER / 2)
    assert (A_T - T0B) / US < pa < MASTER / 2 - 0.4, pa            # (a): the whole signal recorded
    assert C_T0 + C_N * C_DT + 0.15 < poster < MASTER - 0.4           # (c): the image complete

    # ---- report
    say("Figure 3 (nf-shm-ndt): NDT, (a) pulse echo, (b) acoustic emission, (c) imaging")
    say("generator: tools/numfig/shm_ndt.py, model: tools/numfig/shm_fdtd.py")
    say("")
    say("MODEL")
    say("  2D plane-strain elastodynamics, velocity-stress on a staggered grid (Virieux 1986),")
    say("  voids as cells of zero density and stiffness (EFIT, Fellinger et al. 1995); every face")
    say("  of the steel and of a crack is traction free. P, S and Rayleigh waves and mode")
    say("  conversion are all in it.")
    say(f"  steel: c_L = {c*1e3:.0f} m/s, c_T = {F.CT*1e3:.0f} m/s, rho = {F.RHO_SI:.0f} kg/m3")
    say(f"  source: uniform normal traction on the probe or element face, {F0:g} MHz, {NC} cycles,")
    say(f"  Hann window ({DUR:g} us); receiver: the mean normal velocity over the same face")
    say(f"  grid: dx = {DX} mm ({c/F0/DX:.1f} points per P wavelength, {F.CT/F0/DX:.1f} per S), CFL {F.CFL}")
    say("")
    say("(a) PULSE ECHO")
    say(f"  beam {A_D:g} mm deep, modelled {A_W:g} mm long (the page draws {A_WIN[1]-A_WIN[0]:g} mm of it; nothing")
    say(f"  returns from its ends within the {A_T:g} us recorded); probe {A_PW:g} mm wide")
    say(f"  crack: a void {2*A_CR['a']:g} x {2*A_CR['b']:g} mm, centre {A_CR['x']-A_PX:+g} mm from the probe's axis,")
    say(f"  {A_CR['z']:g} mm down, tilted {A_CR['tilt']:g} deg (right end up): from ({x0-A_PX:+.2f}, {zz0:.2f}) to"
        f" ({x1-A_PX:+.2f}, {zz1:.2f}) mm")
    say("  the recorded signal, over its peak while the probe sends (Excitation = 1):")
    say(f"    Reflection (crack): envelope peak {ac:.3f} at t = {tc:.3f} us")
    say(f"    Boundary (back wall): envelope peak {ab:.3f} at t = {tb:.3f} us;"
        f" without the crack {ab0:.3f} at {tb0:.3f} us")
    say(f"    the crack shadows the back wall: its echo keeps {ab/ab0*100:.0f} % of its height")
    say(f"    between the two echoes the signal stays below {gap:.3f} (no other echo)")
    say("  echo times as the grid is refined (envelope peaks, from the burst's centre):")
    for dx, (t1_, a1_), (t2_, a2_) in conv:
        say(f"    dx = {dx:5.3f} mm: Reflection {t1_:.4f} us ({a1_:.3f}), Boundary {t2_:.4f} us ({a2_:.3f})")
    say("")
    say("  CHECK 1, the scheme's P travel time: an 80 mm probe (a near plane wave), no crack,")
    say("  back wall echo:")
    for dx, t_ in pw:
        say(f"    dx = {dx:5.3f} mm: {t_:.4f} us")
    say(f"    Richardson (second order, 0.05 and 0.025 mm): {rich:.4f} us;"
        f" 2d/c_L = {2*A_D/c:.4f} us, error {(rich/(2*A_D/c)-1)*100:+.3f} %")
    say(f"  CHECK 2, the figure's back wall echo: {tb:.4f} us against 2d/c_L = {2*A_D/c:.4f} us"
        f" ({(tb/(2*A_D/c)-1)*100:+.2f} %, the 12 mm probe's own diffraction and the grid)")
    say(f"  CHECK 3, the crack echo: the crack lies {min(zz0, zz1):.2f} to {max(zz0, zz1):.2f} mm down;"
        f" under the probe from {depth_at(A_CR, A_PX + A_PW/2):.2f}")
    say(f"    to {zz0:.2f} mm, so 2z/c_L = {2*depth_at(A_CR, A_PX + A_PW/2)/c:.3f} to {2*zz0/c:.3f} us: its echo peaks"
        f" at {tc:.3f} us,")
    say("    from the deeper, left end under the probe; the right end's diffraction comes first,")
    say("    a small bump before it")
    say("  the lanes on the page: 1D kinematics at c_L under the probe's right half, where the")
    say(f"    crack is: down lane {A_LANES[0]:g} mm right of the axis meets the crack {z1:.2f} mm down"
        f" (t = {z1/c:.3f} us), up lane")
    say(f"    {A_LANES[1]:g} mm right meets it {z2:.2f} mm down; the lane's crack echo reaches the probe at"
        f" {2*z1/c:.3f} us,")
    say(f"    its back wall echo at {2*A_D/c:.3f} us (recorded peaks {tc:.3f} and {tb:.3f} us; on the page"
        f" {abs(tc-2*z1/c)*1e3/US:.0f} and {abs(tb-2*A_D/c)*1e3/US:.0f} ms apart)")
    say("    the lanes show where the waves are; the recorded signal shows how strong they are")
    say("")
    say("(b) ACOUSTIC EMISSION")
    say(f"  beam {B_W:g} x {B_D:g} mm; his crack path from the underside, grown in four steps; sensor"
        f" {B_SENSOR[1]:g} mm wide on top at x = {B_SENSOR[0]:g} mm")
    say("  each step sends a P wave front from the new tip: radius c_L t on the page, clipped to the")
    say("  beam (the fronts are the direct ones; the reflections from the faces are not drawn)")
    for k in range(4):
        say(f"    step {k+1}: tip ({B_CRACK[k+2][0]:.1f}, {B_CRACK[k+2][1]:.1f}) mm, nearest point of the sensor"
            f" {hits[k]*c:.2f} mm away: heard {hits[k]:.3f} us later ({hits[k]/US*1e3:.0f} ms on the page)")
    say("  CHECK 4, the model: the crack as a void 0.3 mm wide along the whole path, a moment source")
    say(f"    (a centre of dilation, rate a 0.5 us Hann pulse) at ({src[0]:.2f}, {src[1]:.2f}) mm, just past the tip:")
    say(f"    the sensor's signal first exceeds 2 % of its peak at {first:.3f} us; the P front's")
    say(f"    geometric arrival at the sensor's nearest point, {rmin:.3f} mm away, is {rmin/c:.3f} us"
        f" ({first - rmin/c:+.3f} us, the")
    say("    source pulse's rise and the threshold)")
    say("")
    say("(c) IMAGING")
    say(f"  wall {C_D:g} mm thick, modelled {C_W + 2*C_M:g} mm long, {C_W:g} mm drawn; crack: a void"
        f" {2*C_CR['a']:g} x {2*C_CR['b']:g} mm, centre ({C_CR['x']:g}, {C_CR['z']:g}) mm, tilted {C_CR['tilt']:g} deg")
    say(f"  array: {C_N} elements, pitch {C_P:g} mm (half a P wavelength is {c/F0/2:.3f} mm), width {C_EW:g} mm,"
        f" centres x = {C_XE[0]:.2f} ... {C_XE[-1]:.2f} mm")
    say(f"  full matrix capture: {C_N} runs, each element transmits, all receive, {C_T:g} us")
    say("  the direct waves (under the transmitter, along the array) are taken out with a run in a")
    say("  half space (no echo within the record) at the same element distance |i - j|")
    say(f"  CHECK 5, reciprocity of the scattered data: max|h_ij - h_ji| / max|h| = {recip:.1e}")
    say("  total focusing: I(x, z) = |sum_i sum_j H[h_ij](t_i + t_j)|, t = distance / c_L, the burst's")
    say(f"  centre as time zero, {C_IMG['dx']:g} mm pixels; the page shows the mean over transmitters 1 ... k")
    say(f"  after the k-th firing, in dB of the complete image's peak, {C_IMG['db']:g} dB range")
    say(f"  CHECK 6, the image: the crack's peak at ({pc[0]:.2f}, {pc[1]:.2f}) mm, {dist:.2f} mm from the crack's"
        f" line (the crack")
    say(f"    runs from ({cx0:.2f}, {cz0:.2f}) to ({cx1:.2f}, {cz1:.2f}) mm); the back wall imaged at z = {zb:.2f} mm"
        f" (true {C_D:g}),")
    say(f"    {lvl_bw:+.1f} dB, at x = 12 mm, away from the crack's shadow")
    say("  the fronts drawn: the incident circle c_L t about the transmitter, cut where the crack")
    say("  shadows it; the crack's specular front, a circle about the transmitter's mirror image in")
    say("  the crack's line, over the rays that meet the crack; its edge waves, circles about each")
    say("  tip starting when the incident front reaches it; the back wall's echo, a circle about")
    say("  the mirror image in the back wall, cut where the crack shadows its path. The receivers")
    say("  light up when the first crack echo reaches them (shortest path via the crack).")
    say("")
    say("TIME")
    say(f"  time slowed {SLOW:.0e} (10 us of the model per second) in all three panels; the loop is"
        f" {MASTER:g} s:")
    say(f"  (a) a shot every {MASTER/2:g} s from t = {A_T0} s; (b) growth steps at t = "
        + ", ".join(f"{v:g}" for v in B_EVENTS) + " s;")
    late = int((arrive > C_DT * US).sum())
    say(f"  (c) a firing every {C_DT:g} s from t = {C_T0:g} s ({C_DT*US:.1f} us each); the crack's first echo"
        f" reaches a receiver {arrive.min():.2f} to {arrive.max():.2f} us")
    say(f"      after the burst starts ({late} of {C_N*C_N} pairs later than the firing's {C_DT*US:.1f} us:"
        f" those receivers are not lit)")
    say(f"  poster (printed frame) at t = {poster} s: (a) recorded, (b) the last step heard, (c) the image complete")
    txt = "\n".join(rep) + "\n"

    # ---- data for the page
    dec = 2
    data = {
        "poster": poster, "us": US, "master": MASTER, "f0": F0, "nc": NC, "dur": DUR, "cl": c,
        "a": {"t0": A_T0, "win": A_WIN[1] - A_WIN[0], "d": A_D, "px": A_PX - A_WIN[0], "pw": A_PW,
              "lanes": list(A_LANES), "z1": z1, "z2": z2,
              "crack": [[x0 - A_WIN[0], zz0], [x1 - A_WIN[0], zz1]], "cb": A_CR["b"],
              "sig": {"t0": float(ts[0]), "dt": float(ts[dec] - ts[0]), "v": np.round(va[::dec], 3).tolist()},
              "tc": tc, "ac": ac, "tb": tb, "ab": ab, "cwin": cwin, "tdur": T0B},
        "b": {"w": B_W, "d": B_D, "crack": B_CRACK, "sensor": list(B_SENSOR), "events": B_EVENTS,
              "hits": hits},
        "c": {"w": C_W, "d": C_D, "crack": [[cx0, cz0], [cx1, cz1]], "cr": C_CR, "xe": C_XE.tolist(),
              "ew": C_EW, "t0": C_T0, "dt": C_DT, "arrive": arrive.tolist(),
              "img": img, "tw": int(tw_), "th": int(th_), "cols": cols, "zmax": C_IMG["zmax"]},
    }
    return data, txt, locals()


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const MASTER = D.master, US = D.us, CL = D.cl;
const phase = () => ((t % MASTER) + MASTER) % MASTER;
/* the burst the probes send, s(tau), tau in us from its start */
function burst(tau) {
  if (tau < 0 || tau > D.dur) return null;
  return Math.sin(2 * Math.PI * D.f0 * tau) * .5 * (1 - Math.cos(2 * Math.PI * D.f0 * tau / D.nc));
}
/* text and math in a row; returns the width */
function row(parts, x, y, o = {}) {
  const w = parts.reduce((s, [k, v]) => s + (k === 't' ? text(v, 0, -1e4, { ...o, alpha: 0 }) : math(v, 0, -1e4, { ...o, alpha: 0 })), 0);
  let cx = o.align === 'right' ? x - w : o.align === 'center' ? x - w / 2 : x;
  for (const [k, v] of parts) cx += k === 't' ? text(v, cx, y, { ...o, align: 'left' }) : math(v, cx, y, { ...o, align: 'left' });
  return w;
}
function tip(x, y, ang, color, size = 7, alpha = 1) {        // a TikZ stealth tip at (x, y)
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(x, y);
  ctx.lineTo(x - size * Math.cos(ang - .38), y - size * Math.sin(ang - .38));
  ctx.lineTo(x - size * .62 * Math.cos(ang), y - size * .62 * Math.sin(ang));
  ctx.lineTo(x - size * Math.cos(ang + .38), y - size * Math.sin(ang + .38)); ctx.closePath(); ctx.fill(); ctx.restore();
}
/* a cut through a long member: the edge with a small zigzag in it */
function cutEdge(x, y0, y1, p, alpha = 1) {
  const m = (y0 + y1) / 2;
  line([[x, y0], [x, m - 7], [x - 4, m - 2.5], [x + 4, m + 2.5], [x, m + 7], [x, y1]], { color: C.ink, width: 1.1, progress: p, alpha });
}
function piece(x0, y0, w, h, p, o = {}) {                     // steel: fill, top face, back wall, cut ends
  const { cut = true } = o;
  if (p <= 0) return;
  ctx.save(); ctx.fillStyle = C.steel; ctx.fillRect(x0, y0, w * clamp(p), h); ctx.restore();   // laid in with its faces
  line([[x0, y0], [x0 + w, y0]], { width: 1.6, progress: p });
  line([[x0, y0 + h], [x0 + w, y0 + h]], { width: 2.4, progress: p });
  if (cut) { cutEdge(x0, y0, y0 + h, p); cutEdge(x0 + w, y0, y0 + h, p); }
  else { line([[x0, y0], [x0, y0 + h]], { width: 1.6, progress: p }); line([[x0 + w, y0], [x0 + w, y0 + h]], { width: 1.6, progress: p }); }
}
/* labels that a moving line or a wave front passes behind: their ink boxes.
   inkBox() measures a run of text as text() would set it; gapLine() is a
   vertical line broken 3 units clear of every box kept in KEEP */
const KEEP = [];
function inkBox(s, x, y, o) {
  ctx.save(); ctx.font = font({ size: 16, ...o }); ctx.textAlign = o.align || 'left'; const q = ctx.measureText(s); ctx.restore();
  return [x - q.actualBoundingBoxLeft, y - q.actualBoundingBoxAscent, x + q.actualBoundingBoxRight, y + q.actualBoundingBoxDescent];
}
function keepText(s, x, y, o) { text(s, x, y, o); if (o.alpha > 0) KEEP.push(inkBox(s, x, y, o)); }
function gapLine(x, y0, y1, o) {
  const cuts = KEEP.filter(b => x > b[0] - 3 && x < b[2] + 3).map(b => [b[1] - 3, b[3] + 3]).sort((p, q) => p[0] - q[0]);
  let y = y0;
  for (const [p, q] of cuts) { if (p > y + .5) line([[x, y], [x, Math.min(p, y1)]], o); y = Math.max(y, q); if (y >= y1) return; }
  if (y1 > y + .5) line([[x, y], [x, y1]], o);
}
function crackLine(p0, p1, half, alpha = 1, prog = 1) {       // a crack: a thin crimson void
  if (prog <= 0) return;
  const a = Math.atan2(p1[1] - p0[1], p1[0] - p0[0]), L = Math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * prog;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.translate(p0[0], p0[1]); ctx.rotate(a);
  ctx.beginPath(); ctx.ellipse(L / 2, 0, L / 2, Math.max(half, 1.6), 0, 0, 2 * Math.PI);
  ctx.fillStyle = C.accent; ctx.fill(); ctx.strokeStyle = '#781E2C'; ctx.lineWidth = .8; ctx.stroke(); ctx.restore();
}

/* ================================================================ (a) pulse echo */
const A = D.a, AX0 = 200, AY0 = 92, AS = 4, AW = A.win * AS, AH = A.d * AS;
const PCX = AX0 + A.px * AS, LD = PCX + A.lanes[0] * AS, LU = PCX + A.lanes[1] * AS;
const ay = z => AY0 + z * AS, ax = x => AX0 + x * AS;
const SIG = A.sig, NS = SIG.v.length;
const G = { x: 480, y: 92, w: 480, h: 160, xlim: [-1, 16], ylim: [-1.25, 1.25] };
const gX = v => G.x + (v - G.xlim[0]) / (G.xlim[1] - G.xlim[0]) * G.w;
const gY = v => G.y + G.h - (v - G.ylim[0]) / (G.ylim[1] - G.ylim[0]) * G.h;
const SW = 7;                                                 // a lane pulse's half width
function packet(x, zLead, zTrail, zLo, zHi, f, color, up) {  // one pulse in a lane, z in mm
  const a = Math.max(zLo, Math.min(zLead, zTrail)), b = Math.min(zHi, Math.max(zLead, zTrail));
  if (b <= a) return;
  const pts = [];
  for (let z = a; z <= b + 1e-9; z += .06) { const v = f(z); pts.push([x + SW * (v === null ? 0 : v), ay(z)]); }
  line(pts, { color, width: 1.7 });
  if (zLead >= zLo && zLead <= zHi) tip(x, ay(zLead) + (up ? -3 : 3), up ? -Math.PI / 2 : Math.PI / 2, color, 8);
}
function panelA() {
  panel('a', 18, 34, { alpha: lab(0) });
  // the probe, and what he calls it
  const pp = settle(.1, .28), la = lab(.2);
  ctx.save(); ctx.globalAlpha *= pp; ctx.fillStyle = C.navy; ctx.fillRect(PCX - A.pw * AS / 2, AY0 - 14 + rise(pp), A.pw * AS, 14); ctx.restore();
  text('Acoustic sensor', 250, 50 + rise(la), { size: 16, align: 'right', alpha: la });
  text('(sends and receives waves)', 250, 69 + rise(la), { size: 15, color: C.body, align: 'right', alpha: la });
  arrow(256, 60, PCX - A.pw * AS / 2 - 3, AY0 - 9, { width: 1.2, head: 7, alpha: la });
  // the beam
  piece(AX0, AY0, AW, AH, seg(.02, .35));
  text('Steel beam', AX0 + 8, AY0 + AH - 10, { size: 15, color: C.body, alpha: lab(.3) });
  const dA = lab(.4);                                          // its depth d, as the signal's 2d / c_L uses it
  arrow(AX0 - 16, AY0, AX0 - 16, AY0 + AH, { width: 1, head: 7, both: true, color: C.ink, alpha: dA });
  math('d', AX0 - 24, AY0 + AH / 2 + 6, { size: 17, align: 'right', alpha: dA });
  const [c0, c1] = A.crack, cp = seg(.2, .25);
  crackLine([ax(c0[0]), ay(c0[1])], [ax(c1[0]), ay(c1[1])], A.cb * AS, 1, cp);
  text('crack', ax(c1[0]) + 6, ay(c1[1]) - 4, { size: 15, color: C.accent, alpha: lab(.35) });
  // the lanes' guides
  const gp = seg(.25, .3), ga = .9;
  line([[LD, AY0 + 5], [LD, AY0 + AH - 5]], { color: C.guide, width: 1, dash: [3, 4], progress: gp, alpha: ga });
  line([[LU, AY0 + AH - 5], [LU, AY0 + 5]], { color: C.guide, width: 1, dash: [3, 4], progress: gp, alpha: ga });
  if (gp >= 1) { tip(LD, AY0 + AH - 3, Math.PI / 2, C.guide, 6, ga); tip(LU, AY0 + 3, -Math.PI / 2, C.guide, 6, ga); }
  // the shot: tau, us after the probe starts to send
  const s = t - A.t0, ph = s < 0 ? -1 : s % (MASTER / 2), tau = ph * US;
  const fade = ph < 0 ? 0 : 1 - clamp((ph - (MASTER / 2 - .35)) / .3);
  if (ph >= 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(AX0, AY0 - 1, AW, AH + 2); ctx.clip();
    const d = A.d, z1 = A.z1, z2 = A.z2;
    // down: the pulse the probe sends
    packet(LD, CL * tau, CL * (tau - D.dur), 0, d, z => burst(tau - z / CL), C.navy, false);
    // up: the crack's echo, from where the down lane meets the crack
    const t1 = z1 / CL;
    if (tau > t1) packet(LU, z1 - CL * (tau - t1), z1 - CL * (tau - t1 - D.dur), 0, z2, z => burst(tau - t1 - (z1 - z) / CL), C.accent, true);
    // up: the back wall's echo
    const tw = d / CL;
    if (tau > tw) packet(LU, d - CL * (tau - tw), d - CL * (tau - tw - D.dur), 0, d, z => burst(tau - tw - (d - z) / CL), C.navy, true);
    ctx.restore();
  }
  // the recorded signal
  const ap = seg(.05, .4);
  text('Recorded signal', G.x + G.w / 2, G.y - 12 + rise(lab(.1)), { size: 16, color: C.body, align: 'center', alpha: lab(.1) });
  const g = axes({ ...G, xticks: [0, 4, 8, 12, 16], yticks: [-1, 0, 1], progress: ap,
                   xlabel: '\\rm{Time}\\ \\ t\\ (\\rm{µs})', ylabel: '\\rm{Amplitude}', ylabelGap: 40 });
  g.inside(() => line([[G.x, gY(0)], [G.x + G.w, gY(0)]], { color: C.rule, width: 1, alpha: ap }));
  if (ph >= 0 && fade > 0) {
    const tn = tau - A.tdur;                                  // the signal's own time (burst centre = 0)
    const n = Math.min(NS, Math.floor((tn - SIG.t0) / SIG.dt) + 1);
    if (n > 1) {
      const pts = []; for (let i = 0; i < n; i++) pts.push([gX(SIG.t0 + i * SIG.dt), gY(SIG.v[i])]);
      g.inside(() => {
        line(pts, { color: C.navy, width: 1.5, alpha: fade });
        const i0 = Math.max(0, Math.floor((A.cwin[0] - SIG.t0) / SIG.dt)), i1 = Math.min(n, Math.ceil((A.cwin[1] - SIG.t0) / SIG.dt));
        if (i1 > i0 + 1) line(pts.slice(i0, i1), { color: C.accent, width: 1.7, alpha: fade });
      });
    }
    const seen = te => fade * clamp((tn - te) / 2.5);         // a label arrives as the signal passes
    keepText('Excitation', gX(.75), gY(1.02), { size: 15, color: C.body, alpha: seen(0) });
    keepText('Reflection', gX(A.tc) - 18, gY(A.ac) - 10, { size: 15, color: C.accent, alpha: seen(A.tc) });
    keepText('Boundary', gX(A.tb) - 18, gY(A.ab) - 10, { size: 15, color: C.body, alpha: seen(A.tb) });
    const da = seen(A.tb) * .95, yd = gY(-1.12);
    if (da > 0) {
      arrow(gX(0), yd, gX(2 * A.d / CL), yd, { width: .9, head: 6, both: true, color: C.muted, alpha: da });
      const lw = math('2d/c_{\\rm{L}} = ' + (2 * A.d / CL).toFixed(1) + '\\,\\rm{µs}', 0, -1e4, { size: 14, alpha: 0 });
      const xm = (gX(0) + gX(2 * A.d / CL)) / 2, kb = [xm - lw / 2 - 4, yd - 10, xm + lw / 2 + 4, yd + 10];
      // the knockout as deep as the label's ink (the slash, the subscript), opaque from the first frame
      ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(kb[0], kb[1], kb[2] - kb[0], kb[3] - kb[1]); ctx.restore();
      KEEP.push(kb);
      math('2d/c_{\\rm{L}} = ' + (2 * A.d / CL).toFixed(1) + '\\,\\rm{µs}', xm, yd + 5, { size: 14, color: C.muted, align: 'center', alpha: da });
    }
    // the cursor, last: it passes behind the labels
    if (n > 1 && tn < G.xlim[1]) {
      const xc = gX(tn), v = SIG.v[n - 1];
      gapLine(xc, G.y + 2, G.y + G.h - 2, { color: C.guide, width: 1, alpha: .8 * fade });
      dot(xc, gY(v), 3.2, { color: C.navy, fill: C.navy, alpha: fade });
    }
  }
  const pa = lab(.8);
  row([['m', 'c_{\\rm{L}} = 5900\\,\\rm{m/s}'], ['t', ', beam 40 mm deep']], AX0, AY0 + AH + 22, { size: 14, color: C.muted, alpha: pa });
  text('probe 12 mm, 2 MHz, 3 cycles', AX0, AY0 + AH + 40, { size: 14, color: C.muted, alpha: pa });
}

/* ================================================================ (b) acoustic emission */
const B = D.b, BX0 = 40, BY0 = 400, BS = 3;
const bx = x => BX0 + x * BS, by = z => BY0 + z * BS;
function panelB() {
  const la = lab(.04);
  panel('b', 18, 352, { alpha: la });
  text('Acoustic Emission (sensor is only listening)', 54, 352, { size: 16, color: C.body, alpha: la });
  piece(BX0, BY0, B.w * BS, B.d * BS, seg(.06, .35), { cut: false });
  const sbO = { size: 15, color: C.body, align: 'right', alpha: lab(.3) }, sbB = inkBox('Steel beam', bx(B.w) - 8, by(B.d) - 9, sbO);
  text('Steel beam', bx(B.w) - 8, by(B.d) - 9, sbO);
  const ph = phase(), P = B.crack.map(p => [bx(p[0]), by(p[1])]);
  const reset = 1 - clamp((ph - (MASTER - .35)) / .3);
  // the crack: its first stretch, then one step at each event
  line([P[0], P[1]], { color: C.accent, width: 2.6, progress: seg(.2, .25) });
  const grown = [P[1]];
  B.events.forEach((te, k) => {
    if (t < te || ph < te) return;
    const g = seg(te + (t - ph), .08);
    grown.push([lerp(P[k + 1][0], P[k + 2][0], g), lerp(P[k + 1][1], P[k + 2][1], g)]);
  });
  if (grown.length > 1) line(grown, { color: C.accent, width: 2.6, alpha: reset });
  // the P fronts, radius c_L tau from each new tip, inside the beam
  // inside the beam, and behind its name (the name's box, 3 units round, cut out of the clip)
  ctx.save(); ctx.beginPath(); ctx.rect(BX0, BY0, B.w * BS, B.d * BS);
  ctx.rect(sbB[0] - 3, sbB[1] - 3, sbB[2] - sbB[0] + 6, sbB[3] - sbB[1] + 6); ctx.clip('evenodd');
  B.events.forEach((te, k) => {
    const tau = (ph - te) * US;
    if (tau <= 0 || t < te) return;
    const r = CL * tau;                                       // mm
    if (r > 160) return;
    const a = clamp(Math.sqrt(8 / r), .3, 1) * reset;       // 2D spreading, 1 / sqrt r
    ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = C.blue; ctx.lineWidth = 1.6;
    ctx.beginPath(); ctx.arc(P[k + 2][0], P[k + 2][1], r * BS, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
  });
  ctx.restore();
  // the sensor, and each front it hears
  const sp = settle(.15, .28), sx = bx(B.sensor[0]), sw = B.sensor[1] * BS;
  ctx.save(); ctx.globalAlpha *= sp; ctx.fillStyle = C.navy; ctx.fillRect(sx - sw / 2, BY0 - 16 + rise(sp), sw, 16); ctx.restore();
  let heard = 0;
  B.events.forEach((te, k) => { const th = te + B.hits[k] / US; if (t >= th && ph >= th) heard = Math.max(heard, Math.exp(-(ph - th) / .3)); });
  if (heard > .01) {
    ctx.save(); ctx.globalAlpha *= heard; ctx.fillStyle = C.amber; ctx.fillRect(sx - sw / 2, BY0 - 16, sw, 16);
    ctx.strokeStyle = C.accent; ctx.lineWidth = 1.5;
    for (const r of [9, 15]) { ctx.beginPath(); ctx.arc(sx, BY0 - 16, r, -Math.PI * .8, -Math.PI * .2); ctx.stroke(); }
    ctx.restore();
  }
  const pa = lab(.85);
  row([['t', 'P wave fronts, radius '], ['m', 'c_{\\rm{L}}\\,t'], ['t', ', from each step of the crack']], BX0, 514, { size: 14, color: C.muted, alpha: pa });
}

/* ================================================================ (c) imaging */
const Cc = D.c, CX0 = 466, CY0 = 410, CS = 5.75, CWd = Cc.w * CS, CHd = Cc.d * CS;
const IX0 = 750, IY0 = 410;
const cxp = x => CX0 + x * CS, czp = z => CY0 + z * CS;
const E1 = Cc.crack[0], E2 = Cc.crack[1];
function crosses(p0, p1, q0, q1) {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  return d(p0, p1, q0) * d(p0, p1, q1) < 0 && d(q0, q1, p0) * d(q0, q1, p1) < 0;
}
function mirror(S, a, b) {                                     // S reflected in the line ab
  const ux = b[0] - a[0], uz = b[1] - a[1], L = ux * ux + uz * uz;
  const s = ((S[0] - a[0]) * ux + (S[1] - a[1]) * uz) / L, fx = a[0] + s * ux, fz = a[1] + s * uz;
  return [2 * fx - S[0], 2 * fz - S[1]];
}
const inWall = p => p[0] >= 0 && p[0] <= Cc.w && p[1] >= 0 && p[1] <= Cc.d;
let QUIET = [];                                                 // label boxes the fronts pass behind
const quiet = p => { const x = cxp(p[0]), y = czp(p[1]); return QUIET.some(b => x > b[0] - 4 && x < b[2] + 4 && y > b[1] - 4 && y < b[3] + 4); };
/* a front: points c + R (cos, sin) over the angles where keep(p) holds, as runs */
function front(cx, cz, R, keep, o) {
  if (R <= 0) return;
  const n = Math.max(24, Math.ceil(R * 10)); let run = [];
  const flush = () => { if (run.length > 1) line(run, o); run = []; };
  for (let k = 0; k <= n; k++) {
    const a = 2 * Math.PI * k / n, p = [cx + R * Math.cos(a), cz + R * Math.sin(a)];
    if (keep(p) && !quiet(p)) run.push([cxp(p[0]), czp(p[1])]); else flush();
  }
  flush();
}
const TILE = [];
function tiles() {
  const cv2 = document.createElement('canvas'); cv2.width = IMG.width; cv2.height = IMG.height;
  const g2 = cv2.getContext('2d'); g2.drawImage(IMG, 0, 0);
  const src = g2.getImageData(0, 0, IMG.width, IMG.height).data;
  for (let k = 0; k < Cc.xe.length; k++) {
    const r0 = Math.floor(k / Cc.cols) * Cc.th, c0 = (k % Cc.cols) * Cc.tw;
    const tc = document.createElement('canvas'); tc.width = Cc.tw; tc.height = Cc.th;
    const tg = tc.getContext('2d'), im = tg.createImageData(Cc.tw, Cc.th);
    for (let y = 0; y < Cc.th; y++) for (let x = 0; x < Cc.tw; x++) {
      const v = src[((r0 + y) * IMG.width + c0 + x) * 4], o = (y * Cc.tw + x) * 4;
      im.data[o] = SEQ[v * 3]; im.data[o + 1] = SEQ[v * 3 + 1]; im.data[o + 2] = SEQ[v * 3 + 2]; im.data[o + 3] = 255;
    }
    tg.putImageData(im, 0, 0); TILE.push(tc);
  }
}
function panelC() {
  const la = lab(.08);
  panel('c', 440, 352, { alpha: la });
  piece(CX0, CY0, CWd, CHd, seg(.1, .35));
  const stO = { size: 15, color: C.body, alpha: lab(.3) }, crO = { size: 15, color: C.accent, alpha: lab(.35) };
  const crX = cxp(E2[0]) + 5, crY = czp(E2[1]) - 5;
  QUIET = [inkBox('structure', CX0 + 8, CY0 + CHd - 8, stO), inkBox('crack', crX, crY, crO)];
  text('structure', CX0 + 8, CY0 + CHd - 8, stO);
  const ph = phase(), nF = Cc.xe.length;
  const k = t < Cc.t0 ? -1 : Math.floor((ph - Cc.t0) / Cc.dt);   // the firing under way
  const reset = 1 - clamp((ph - (MASTER - .35)) / .3);
  const fired = k >= 0 && k < nF, tau = fired ? (ph - Cc.t0 - k * Cc.dt) * US : 0;
  const S = fired ? [Cc.xe[k], 0] : null;
  // the waves of this firing, inside the wall
  if (fired) {
    ctx.save(); ctx.beginPath(); ctx.rect(CX0, CY0, CWd, CHd); ctx.clip();
    const R = CL * tau, a = clamp(Math.sqrt(2.5 / Math.max(R, .1)), .3, 1);
    const tail = 1 - clamp((tau - (Cc.dt * US - .6)) / .6);
    // incident, cut by the crack's shadow
    front(S[0], S[1], R, p => p[1] >= 0 && inWall(p) && !crosses(S, p, E1, E2), { color: C.blue, width: 1.5, alpha: a * tail });
    // the back wall's echo, where neither leg of its path meets the crack
    const Sb = [S[0], 2 * Cc.d];
    front(Sb[0], Sb[1], R, p => {
      if (!inWall(p) || p[1] >= Cc.d) return false;
      const s = (Cc.d - Sb[1]) / (p[1] - Sb[1]), W = [Sb[0] + s * (p[0] - Sb[0]), Cc.d];
      return !crosses(S, W, E1, E2) && !crosses(W, p, E1, E2);
    }, { color: C.sky, width: 1.1, alpha: .8 * a * tail });
    // the crack: its specular front, and the waves from its two edges
    const Sm = mirror(S, E1, E2);
    front(Sm[0], Sm[1], R, p => inWall(p) && crosses(Sm, p, E1, E2), { color: C.accent, width: 1.6, dash: [5, 3], alpha: tail });
    for (const E of [E1, E2]) {
      const r = R - Math.hypot(S[0] - E[0], S[1] - E[1]);
      if (r > 0) front(E[0], E[1], r, inWall, { color: C.accent, width: 1, dash: [3, 3], alpha: .75 * clamp(Math.sqrt(1.2 / r), .35, 1) * tail });
    }
    ctx.restore();
  }
  crackLine([cxp(E1[0]), czp(E1[1])], [cxp(E2[0]), czp(E2[1])], Cc.cr.b * CS, 1, seg(.22, .25));
  text('crack', crX, crY, crO);
  // the array: each element transmits in turn, all receive
  const ap = settle(.18, .28), ew = Cc.ew * CS, pitch = (Cc.xe[1] - Cc.xe[0]) * CS;
  ctx.save(); ctx.globalAlpha *= ap;
  const ax0 = cxp(Cc.xe[0]) - pitch / 2, ax1 = cxp(Cc.xe[nF - 1]) + pitch / 2, ay0 = CY0 - 12 + rise(ap);
  ctx.fillStyle = C.navy; ctx.fillRect(ax0, ay0, ax1 - ax0, 12);
  for (let j = 0; j < nF; j++) {
    const x = cxp(Cc.xe[j]);
    if (fired) {
      const hit = tau - Cc.arrive[k][j];                        // the crack's echo front arrives
      if (hit > 0) { ctx.save(); ctx.globalAlpha *= Math.exp(-hit / 1.5) * .9; ctx.fillStyle = C.accent; ctx.fillRect(x - ew / 2, ay0, ew, 12); ctx.restore(); }
    }
    if (j === k && fired) { ctx.save(); ctx.globalAlpha *= clamp(1 - (tau - D.dur) / 1.5, .35, 1); ctx.fillStyle = C.amber; ctx.fillRect(x - ew / 2, ay0, ew, 12); ctx.restore(); }
  }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = .8;
  for (let j = 1; j < nF; j++) { const x = (cxp(Cc.xe[j - 1]) + cxp(Cc.xe[j])) / 2; ctx.beginPath(); ctx.moveTo(x, ay0); ctx.lineTo(x, ay0 + 12); ctx.stroke(); }
  ctx.restore();
  const sa = lab(.25);
  text('Scanning transducers', ax0, 374 + rise(sa), { size: 16, alpha: sa });
  arrow(ax0, 386, ax1, 386, { width: 1.3, head: 8, alpha: sa });
  if (fired) tip(cxp(Cc.xe[k]), 391, Math.PI / 2, C.amber, 7, ap);
  // the image, transmitter by transmitter
  const ia = lab(.3), ip = seg(.15, .35), IW = CWd, IH = Cc.zmax * CS;
  text('Resulting Image', IX0 + IW / 2, IY0 - 12 + rise(ia), { size: 16, color: C.body, align: 'center', alpha: ia });
  arrow(CX0 + CWd + 10, CY0 + CHd / 2, IX0 - 10, CY0 + CHd / 2, { width: 3, head: 11, alpha: lab(.35) });
  const done = t < Cc.t0 ? 0 : Math.min(nF, Math.floor((ph - Cc.t0) / Cc.dt));   // firings completed
  if (TILE.length && done > 0 && reset > 0) {
    const tin = (ph - Cc.t0 - done * Cc.dt) / .15, cur = TILE[done - 1];
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.globalAlpha *= reset;
    if (done > 1 && tin < 1) { ctx.drawImage(TILE[done - 2], IX0, IY0, IW, IH); ctx.globalAlpha *= clamp(tin); }
    else if (done === 1 && tin < 1) ctx.globalAlpha *= clamp(tin);
    ctx.drawImage(cur, IX0, IY0, IW, IH); ctx.restore();
  }
  line([[IX0, IY0], [IX0 + IW, IY0], [IX0 + IW, IY0 + IH], [IX0, IY0 + IH], [IX0, IY0]], { width: 1.3, progress: ip });
  if (done > 0) {
    const ra = .9 * reset * clamp((ph - Cc.t0 - Cc.dt) / .3);
    line([[IX0 + E1[0] * CS, IY0 + E1[1] * CS], [IX0 + E2[0] * CS, IY0 + E2[1] * CS]], { color: C.accent, width: 1, dash: [3, 3], alpha: ra });
    text('back wall', IX0 + 8, IY0 + (Cc.d - 3.2) * CS, { size: 14, color: C.muted, alpha: ra });
  }
  const pa = lab(.9);
  text(`${nF} elements, pitch 1.5 mm, 2 MHz; total focusing method, 24 dB`, CX0, 514, { size: 14, color: C.muted, alpha: pa });
}

function draw() {
  KEEP.length = 0;
  panelA(); panelB(); panelC();
  math('\\rm{time slowed }10^{5}\\,\\times', W - 18, 34, { size: 14, color: C.muted, align: 'right', alpha: lab(.9) });
}
const IMG = new Image();
IMG.src = D.c.img;
IMG.decode().then(tiles).catch(() => {}).finally(() => boot());
"""


def main_page():
    data, txt, L = main()
    with open(os.path.join(HERE, "shm_ndt.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Figure 3: NDT techniques"                 # his own title for his animation
    aria = ("Three nondestructive tests on steel, computed from an elastic wave model. (a) A sensor sends a "
            "pulse into a beam and records its echoes from a crack and from the back wall. (b) A growing "
            "crack sends out waves that a listening sensor picks up. (c) An array of transducers fires one "
            "element after another and the echoes build an image that shows the crack.")
    common.build_html(NAME, title, aria, 1000, 548, data, JS)
    print("still:", common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.0, 3.0, 4.6, 6.0]))


if __name__ == "__main__":
    main_page()
