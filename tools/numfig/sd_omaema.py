"""Figure 2 of the SHM article (understanding-shm-and-ndt, image3):
"OMA and EMA workflow."

His block diagram, his words, and through it the signals of one structure:
a three storey shear frame (rigid floors, m = 25 t each, storey stiffness
k = 9.5 MN/m, 2 % damping in every mode).

  OMA (top row): an unknown random force (independent white noise on the
  three floors) shakes the frame; three accelerometers record the output
  only. The plot is the output's spectrum (the first singular value of the
  output spectral matrix, the frequency domain decomposition), averaged
  over a longer and longer record; the modes are identified from the
  output alone by covariance driven stochastic subspace identification.

  EMA (bottom row), the two measured inputs his words name, "(e.g.,
  shaker, earthquake)" (the professor's note of Oct 2026: "also add shaker
  and base earthquake motion recorded"):
  - a shaker: an electrodynamic shaker on a stand beside the frame drives
    the roof through a stinger and a force sensor with a known sine sweep,
    0.4 to 7 Hz; the force F and the roof acceleration a3 are recorded;
  - an earthquake: the ground moves (a Kanai-Tajimi filtered, enveloped
    white noise, seeded), an accelerometer on the foundation records the
    ground acceleration a_g, the floors respond (exact state space, first
    order hold); the input-output relation is the transmissibility a3/a_g.
  In both, the frequency response is estimated from the two records,
  H1 = S_xy / S_xx (Welch), and drawn on the model's exact curve; a modal
  model fitted to it gives the three natural frequencies. The row shows the
  two inputs in turn, test after test, until the reader picks one (chips;
  ?view=shaker or ?view=earthquake preselects one).

Both rows find the model's three natural frequencies; the check file
compares them with the eigenvalues and with the closed form of a uniform
shear building, w_n = 2 sqrt(k/m) sin((2n - 1) pi / (2(2N + 1))).

Run: python tools/numfig/sd_omaema.py [--look] [--dense]   (writes content/
anim/nf-sd-omaema.html and .webp and tools/numfig/sd_omaema.check.txt)
"""
import os
import shutil
import sys
import tempfile
import threading

import numpy as np
import scipy.linalg as sla
from scipy import signal
from scipy.optimize import least_squares

import common
import sd_check
from sd_check import poster_js

NAME = "sd-omaema"
HERE = os.path.dirname(os.path.abspath(__file__))

MASS, STIFF, ZETA = 25e3, 9.5e6, 0.02      # kg per floor, N/m per storey, every mode
FS = 40.0                                  # Hz: the recordings
F_RMS = 100.0                              # N: each floor's ambient force (white samples at FS, linear between)
T_OMA = 7200.0                             # s: the ambient record (2 h)
NPER = 4096                                # Welch segment (102.4 s), Hann, half overlap
SEED_REC, SEED_PAGE = 6, 11                # the record's realization, the page's (another, same process)
SSI_ORDER, SSI_ROWS = 6, 30                # stochastic subspace identification: order, block rows
SW_F0, SW_F1, SW_T = 0.4, 7.0, 12.0        # the sweep: Hz, Hz, s (linear)
SW_TAPER = 0.4                             # s, cosine taper at both ends
SW_AMP = 2.0e3                             # N, the shaker's force amplitude
FS_SIM = 400.0                             # Hz: the sweep test's simulation
T_EMA = 200.0                              # s: its record (the frame is still again long before)
FMAX = 7.0                                 # Hz: the plots
LOOP = 22.0                                # s: the page's loop
T0 = 0.6                                   # s: the loop starts (page clock)
B_T0 = 7.0                                 # loop time the sweep (or the ground motion) starts
FS_PAGE = 60.0                             # Hz: the page's samples (top row simulated at 120 Hz)
TW = 8.0                                   # s: the window of the ambient traces
LEVELS = [1, 2, 4, 8, 16, 32, 64]          # averages shown on the way to the whole record
# the earthquake (bottom row's second input)
FS_Q = 480.0                               # Hz: its record, and the bottom row's simulations (8 x FS_PAGE)
SEED_Q = 3                                 # the ground motion's white noise
WN_FS = 100.0                              # Hz: the white noise samples, linear between
KT_FG, KT_ZG = 2.5, 0.6                    # Kanai-Tajimi ground filter: Hz, damping (firm ground)
CP_FF, CP_ZF = 0.25, 0.6                   # Clough-Penzien high pass: Hz, damping
ENV_T1, ENV_T2, ENV_C = 1.5, 7.0, 0.5      # Jennings, Housner and Tsai envelope: s, s, 1/s
Q_END, Q_TAPER = 14.5, 1.0                 # s: the motion is over (a cosine taper over its last second)
PGA = 0.03                                 # m/s^2: a weak motion, as monitored buildings mostly record
T_Q = 200.0                                # s: its record (from rest to rest)
H = 552                                    # the drawing's height (W = 1000)


# ------------------------------------------------------------------ model
def frame():
    """M, K, C (modal damping ZETA), the natural frequencies and the mass
    normalised mode shapes (roof positive)."""
    M = MASS * np.eye(3)
    K = STIFF * np.array([[2.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 1.0]])
    w2, Phi = sla.eigh(K, M)
    w = np.sqrt(w2)
    Phi = Phi * np.sign(Phi[-1])
    C = M @ Phi @ np.diag(2 * ZETA * w) @ Phi.T @ M
    return M, K, C, w, Phi


def closed_form():
    """Uniform shear building, N = 3 floors, fixed base:
    w_n = 2 sqrt(k/m) sin((2n - 1) pi / (2(2N + 1)))."""
    n = np.arange(1, 4)
    return 2 * np.sqrt(STIFF / MASS) * np.sin((2 * n - 1) * np.pi / 14)


def statespace(M, K, C):
    """x = [u, v]; outputs [acceleration (3), displacement (3)], inputs the floor forces."""
    Mi = np.linalg.inv(M)
    A = np.block([[np.zeros((3, 3)), np.eye(3)], [-Mi @ K, -Mi @ C]])
    B = np.vstack([np.zeros((3, 3)), Mi])
    Cy = np.vstack([np.hstack([-Mi @ K, -Mi @ C]), np.hstack([np.eye(3), np.zeros((3, 3))])])
    Dy = np.vstack([Mi, np.zeros((3, 3))])
    return signal.StateSpace(A, B, Cy, Dy)


def both_statespace(M, K, C):
    """The bottom row's frame, x = [u, v] relative to the ground; inputs the
    roof force F and the ground acceleration a_g; outputs the floors' absolute
    accelerations (3) and their displacements relative to the ground (3):
    M u'' + C u' + K u = e3 F - M iota a_g, absolute acceleration u'' + a_g."""
    Mi = np.linalg.inv(M)
    e3, iota = np.array([0.0, 0.0, 1.0]), np.ones(3)
    A = np.block([[np.zeros((3, 3)), np.eye(3)], [-Mi @ K, -Mi @ C]])
    B = np.vstack([np.zeros((3, 2)), np.column_stack([Mi @ e3, -iota])])
    Cy = np.vstack([np.hstack([-Mi @ K, -Mi @ C]), np.hstack([np.eye(3), np.zeros((3, 3))])])
    Dy = np.vstack([np.column_stack([Mi @ e3, np.zeros(3)]), np.zeros((3, 2))])
    return signal.StateSpace(A, B, Cy, Dy)


def frf(M, K, C, f):
    """Receptance matrices H(f) = (K - w^2 M + i w C)^-1, shape (len(f), 3, 3)."""
    return np.array([np.linalg.inv(K - (2 * np.pi * x) ** 2 * M + 2j * np.pi * x * C) for x in np.atleast_1d(f)])


def transmissibility(M, K, C, f):
    """The exact absolute acceleration transmissibility ground -> roof,
    a3 / a_g = 1 - w^2 [H(w) (-M iota)]_3."""
    iota = np.ones(3)
    return np.array([1 + (2 * np.pi * x) ** 2 * (h @ (M @ iota))[2] for x, h in zip(np.atleast_1d(f), frf(M, K, C, f))])


def run(ss, force, dt):
    """Accelerations and displacements for the floor forces `force` (n, 3), linear
    between samples (lsim's first order hold is then exact)."""
    t = np.arange(force.shape[0]) * dt
    _, y, _ = signal.lsim(ss, force, t, interp=True)
    return y[:, :3], y[:, 3:]


def periodic(ss, force, dt, reps=8):
    """The periodic steady state for a periodic force: the period run `reps`
    times from rest, the last kept (what the start leaves decays as
    exp(-zeta w1 t): 1e-6 after 7 periods of 22 s)."""
    acc, dis = run(ss, np.tile(force, (reps, 1)), dt)
    n = force.shape[0]
    return acc[-n:], dis[-n:]


def sweep(t):
    """The shaker's force over the sweep, per unit amplitude: a linear sine sweep
    SW_F0 -> SW_F1 in SW_T seconds, cosine tapered at both ends."""
    t = np.asarray(t, float)
    r = (SW_F1 - SW_F0) / SW_T
    on = (t >= 0) & (t <= SW_T)
    w = np.ones_like(t)
    w = np.where(t < SW_TAPER, 0.5 - 0.5 * np.cos(np.pi * np.clip(t, 0, SW_TAPER) / SW_TAPER), w)
    w = np.where(t > SW_T - SW_TAPER, 0.5 - 0.5 * np.cos(np.pi * np.clip(SW_T - t, 0, SW_TAPER) / SW_TAPER), w)
    return np.where(on, w * np.sin(2 * np.pi * (SW_F0 * t + 0.5 * r * t * t)), 0.0)


def mac(a, b):
    return float(np.abs(np.vdot(a, b)) ** 2 / (np.vdot(a, a).real * np.vdot(b, b).real))


# ------------------------------------------------------------------ OMA
def welch_parts(acc, fs=FS, nper=NPER):
    """Hann windowed, half overlapping segments: each one's cross spectral
    matrix (one sided), shape (segments, frequencies up to FMAX + 0.5, 3, 3)."""
    hop = nper // 2
    win = signal.windows.hann(nper, sym=False)
    scale = 2.0 / (fs * (win ** 2).sum())
    n = (acc.shape[0] - nper) // hop + 1
    fr = np.fft.rfftfreq(nper, 1 / fs)
    keep = fr <= FMAX + 0.5
    out = np.zeros((n, keep.sum(), 3, 3), complex)
    for s in range(n):
        X = np.fft.rfft(acc[s * hop:s * hop + nper] * win[:, None], axis=0)[keep]
        out[s] = scale * X[:, :, None] * X[:, None, :].conj()
    return fr[keep], out


def fdd(G):
    """First singular value and vector of the spectral matrix at each frequency."""
    U, S, _ = np.linalg.svd(G)
    return S[:, 0], U[:, :, 0]


def ssi_cov(y, fs=FS, order=SSI_ORDER, rows=SSI_ROWS):
    """Covariance driven stochastic subspace identification (Peeters and De
    Roeck 1999): output covariances R_1 ... R_2i in a block Toeplitz matrix,
    its SVD truncated at `order` gives the observability matrix, whose shift
    gives A; A's eigenvalues are the poles, C times its eigenvectors the
    mode shapes. Returns frequencies (Hz), damping ratios, shapes (3, modes)."""
    N, l = y.shape
    y = y - y.mean(0)
    R = [(y[k:].T @ y[:N - k]) / (N - k) for k in range(2 * rows + 1)]
    T = np.block([[R[a + b + 1] for b in range(rows)] for a in range(rows)])
    U, s, _ = np.linalg.svd(T)
    O = U[:, :order] * np.sqrt(s[:order])
    A = np.linalg.pinv(O[:-l]) @ O[l:]
    lam, psi = np.linalg.eig(A)
    mu = np.log(lam) * fs
    keep = mu.imag > 0
    mu, psi = mu[keep], psi[:, keep]
    o = np.argsort(np.abs(mu))
    mu, psi = mu[o], psi[:, o]
    shapes = O[:l] @ psi
    return np.abs(mu) / 2 / np.pi, -mu.real / np.abs(mu), shapes


def oma(ss, seed=SEED_REC):
    rng = np.random.default_rng(seed)
    n = int(T_OMA * FS)
    force = F_RMS * rng.standard_normal((n, 3))
    acc, _ = run(ss, force, 1 / FS)
    fr, parts = welch_parts(acc)
    csum = np.cumsum(parts, axis=0)
    levels = LEVELS + [parts.shape[0]]
    spectra = [fdd(csum[k - 1] / k)[0] for k in levels]
    s1, u1 = fdd(csum[-1] / parts.shape[0])
    f_id, z_id, sh = ssi_cov(acc)
    return dict(fr=fr, levels=levels, spectra=spectra, s1=s1, u1=u1, nseg=parts.shape[0], acc=acc,
                f=f_id, zeta=z_id, shapes=sh)


# ------------------------------------------------------------------ EMA: the shaker
def h1(x, y, fs):
    """H1 = S_xy / S_xx by Welch's method over one rectangular segment, the
    whole record: a test that starts and ends at rest leaves nothing out
    (a window or shorter segments would cut its transient)."""
    f, sxy = signal.csd(x, y, fs=fs, window="boxcar", nperseg=x.size, detrend=False)
    _, sxx = signal.welch(x, fs=fs, window="boxcar", nperseg=x.size, detrend=False)
    return f, sxy / sxx


def ema(ss, M, K, C):
    """One sweep from rest, recorded until the frame is still again; the FRF
    a3/F from their transforms, and a three mode modal model fitted to it."""
    dt = 1 / FS_SIM
    t = np.arange(int(T_EMA * FS_SIM)) * dt
    F = SW_AMP * sweep(t)
    force = np.zeros((t.size, 3))
    force[:, 2] = F
    acc, _ = run(ss, force, dt)
    fr = np.fft.rfftfreq(t.size, dt)
    Hm = np.fft.rfft(acc, axis=0) / np.fft.rfft(F)[:, None]              # accelerance: 3 floors / roof force
    band = (fr >= SW_F0 + 0.15) & (fr <= SW_F1 - 0.15)
    fb, hb = fr[band], Hm[band]
    exact = np.array([-(2 * np.pi * x) ** 2 * h[:, 2] for x, h in zip(fb, frf(M, K, C, fb))])
    err = np.abs(hb - exact).max() / np.abs(exact).max()
    # the same through Welch's H1 (one rectangular segment, the whole record)
    fw, hw = h1(F, acc[:, 2], FS_SIM)
    h1_err = np.abs(hw[band] - hb[:, 2]).max() / np.abs(hb[:, 2]).max()

    def model(p, fq):                                                     # a driving point accelerance, 3 modes
        om = 2 * np.pi * fq
        out = np.zeros(fq.size, complex)
        for r in range(3):
            fn, z, a = p[3 * r:3 * r + 3]
            wn = 2 * np.pi * fn
            out += -om ** 2 * a / (wn ** 2 - om ** 2 + 2j * z * wn * om)
        return out

    h3 = hb[:, 2]
    mob = np.abs(h3 / (2j * np.pi * fb))
    p0, lo, hi = [], [], []
    for g in (1.4, 3.9, 5.6):                  # start: the mobility's peaks near these, half power widths
        near = np.where(np.abs(fb - g) < 0.4)[0]
        i = near[np.argmax(mob[near])]
        j, k_ = i, i
        while mob[j] > mob[i] / np.sqrt(2):
            j -= 1
        while mob[k_] > mob[i] / np.sqrt(2):
            k_ += 1
        z0 = (fb[k_] - fb[j]) / (2 * fb[i])
        p0 += [fb[i], z0, mob[i] * 2 * z0 * 2 * np.pi * fb[i]]
        lo += [fb[i] * 0.9, 1e-4, 0.0]
        hi += [fb[i] * 1.1, 0.2, np.inf]

    def res(p):
        d = (model(p, fb) - h3) / np.abs(h3)
        return np.concatenate([d.real, d.imag])

    sol = least_squares(res, p0, bounds=(lo, hi), x_scale="jac", xtol=1e-15, ftol=1e-15, gtol=1e-15)
    p = sol.x.reshape(3, 3)
    fit_err = np.abs(model(sol.x, fb) - h3).max() / np.abs(h3).max()
    # the mode shapes: each floor's FRF with the fitted poles, its residues by linear least squares
    om = 2 * np.pi * fb
    basis = np.stack([-om ** 2 / ((2 * np.pi * fn) ** 2 - om ** 2 + 2j * z * 2 * np.pi * fn * om) for fn, z, _ in p], 1)
    A = np.vstack([basis.real, basis.imag])
    shapes = np.array([np.linalg.lstsq(A, np.concatenate([hb[:, r].real, hb[:, r].imag]), rcond=None)[0]
                       for r in range(3)])                               # (floor, mode): phi_i phi_3
    return dict(fr=fb, h3=h3, exact=exact[:, 2], fit=p, p0=np.array(p0).reshape(3, 3), frf_err=err,
                fit_err=fit_err, shapes=shapes, h1_err=h1_err)


# ------------------------------------------------------------------ EMA: the earthquake
def kt_cp():
    """White noise -> ground acceleration: the Kanai-Tajimi filter (firm ground)
    times the Clough-Penzien high pass, which takes away the low frequencies
    that would leave the ground displaced."""
    wg, wf = 2 * np.pi * KT_FG, 2 * np.pi * CP_FF
    num = np.polymul([2 * KT_ZG * wg, wg ** 2], [1.0, 0.0, 0.0])
    den = np.polymul([1.0, 2 * KT_ZG * wg, wg ** 2], [1.0, 2 * CP_ZF * wf, wf ** 2])
    return signal.TransferFunction(num, den)


def envelope(t):
    """Jennings, Housner and Tsai (1968): rises as (t/t1)^2, holds to t2, then
    decays as exp(-c (t - t2)); a cosine taper over the last second ends it at
    Q_END."""
    t = np.asarray(t, float)
    e = np.where(t < ENV_T1, (t / ENV_T1) ** 2, np.where(t <= ENV_T2, 1.0, np.exp(-ENV_C * (t - ENV_T2))))
    s = np.clip((t - (Q_END - Q_TAPER)) / Q_TAPER, 0, 1)
    e = e * (0.5 + 0.5 * np.cos(np.pi * s))
    return np.where((t >= 0) & (t <= Q_END), e, 0.0)


def integrate(a, dt):
    """Velocity and displacement of an acceleration linear between its samples,
    exactly: v by the trapezoid, u by the cubic each interval holds."""
    v = np.concatenate([[0.0], np.cumsum((a[1:] + a[:-1]) / 2 * dt)])
    u = np.concatenate([[0.0], np.cumsum(v[:-1] * dt + dt * dt * (2 * a[:-1] + a[1:]) / 6)])
    return v, u


def ground_motion(n):
    """The ground acceleration, n samples at FS_Q (linear between): seeded white
    noise (WN_FS samples, linear between) through kt_cp() from rest, times the
    envelope; then a baseline correction, a combination of the envelope and
    the envelope times t, that brings the ground's velocity and displacement
    back to zero exactly at Q_END; scaled to PGA. Returns a, v, u, the
    correction's coefficients and the uncorrected end values."""
    dt = 1 / FS_Q
    t = np.arange(n) * dt
    rng = np.random.default_rng(SEED_Q)
    nw = int(round(Q_END * WN_FS)) + 1
    wn = rng.standard_normal(nw)
    wt = np.interp(t, np.arange(nw) / WN_FS, wn, right=0.0)
    _, a, _ = signal.lsim(kt_cp(), wt, t, interp=True)
    e = envelope(t)
    a = a * e
    k = int(round(Q_END * FS_Q))
    va, ua = integrate(a, dt)
    v1, u1 = integrate(e, dt)
    v2, u2 = integrate(e * t, dt)
    c = np.linalg.solve([[v1[k], v2[k]], [u1[k], u2[k]]], [va[k], ua[k]])
    a = a - c[0] * e - c[1] * e * t
    a[k + 1:] = 0.0
    scale = PGA / np.abs(a).max()
    a = a * scale
    v, u = integrate(a, dt)
    return a, v, u, c, (va[k] * scale, ua[k] * scale)


def newmark(M, K, C, ag, dt, sub):
    """Average acceleration Newmark (gamma 1/2, beta 1/4) for M u'' + C u' + K u
    = -M iota a_g, a_g linear between its samples and each interval cut in
    `sub` steps: the independent check of the state space response. Returns
    the roof's relative displacement at the samples."""
    h = dt / sub
    iota = np.ones(3)
    Keff = K + 2 / h * C + 4 / h ** 2 * M
    lu = sla.lu_factor(Keff)
    u = np.zeros(3); v = np.zeros(3); acc = np.zeros(3)
    out = [0.0]
    for i in range(ag.size - 1):
        for s in range(sub):
            g1 = ag[i] + (ag[i + 1] - ag[i]) * (s + 1) / sub
            rhs = -M @ iota * g1 + M @ (4 / h ** 2 * u + 4 / h * v + acc) + C @ (2 / h * u + v)
            un = sla.lu_solve(lu, rhs)
            vn = 2 / h * (un - u) - v
            an = 4 / h ** 2 * (un - u) - 4 / h * v - acc
            u, v, acc = un, vn, an
        out.append(u[2])
    return np.array(out)


def quake(M, K, C):
    """The recorded earthquake: the ground motion, the frame's response from
    rest (exact state space, first order hold), H1 from the two records against
    the exact transmissibility, and a modal model of the transmissibility
    fitted to it."""
    dt = 1 / FS_Q
    n = int(T_Q * FS_Q)
    t = np.arange(n) * dt
    ag, vg, ug, corr, raw_end = ground_motion(n)
    ss = both_statespace(M, K, C)
    _, y, _ = signal.lsim(ss, np.column_stack([np.zeros(n), ag]), t, interp=True)
    aabs, urel = y[:, :3], y[:, 3:]
    f, hq = h1(ag, aabs[:, 2], FS_Q)
    band = (f >= 0.3) & (f <= FMAX)
    fb, hb = f[band], hq[band]
    exact = transmissibility(M, K, C, fb)
    err = np.abs(hb - exact).max() / np.abs(exact).max()
    # what a Hann windowed Welch average of 40.96 s segments would read (the transient cut up)
    fw, sxy = signal.csd(ag, aabs[:, 2], fs=FS_Q, window="hann", nperseg=int(40.96 * FS_Q), detrend=False)
    _, sxx = signal.welch(ag, fs=FS_Q, window="hann", nperseg=int(40.96 * FS_Q), detrend=False)
    hw = sxy / sxx
    wpk = [np.abs(hw[np.abs(fw - g) < 0.2]).max() / np.abs(exact[np.abs(fb - g) < 0.2]).max() - 1
           for g in (1.38, 3.87, 5.59)]

    def model(p, fq):                                                     # 1 + sum w^2 c_r / (w_r^2 - w^2 + 2i z w_r w)
        om = 2 * np.pi * fq
        out = np.ones(fq.size, complex)
        for r in range(3):
            fn, z, c = p[3 * r:3 * r + 3]
            wn = 2 * np.pi * fn
            out += om ** 2 * c / (wn ** 2 - om ** 2 + 2j * z * wn * om)
        return out

    mag = np.abs(hb)
    p0, lo, hi = [], [], []
    for g in (1.4, 3.9, 5.6):
        near = np.where(np.abs(fb - g) < 0.4)[0]
        i = near[np.argmax(mag[near])]
        j, k_ = i, i
        while mag[j] > mag[i] / np.sqrt(2):
            j -= 1
        while mag[k_] > mag[i] / np.sqrt(2):
            k_ += 1
        z0 = (fb[k_] - fb[j]) / (2 * fb[i])
        c0 = -2 * z0 * (hb[i] - 1).imag                                    # at w_r: T - 1 = c_r / (2i z_r)
        p0 += [fb[i], z0, c0]
        lo += [fb[i] * 0.9, 1e-4, -np.inf]
        hi += [fb[i] * 1.1, 0.2, np.inf]

    def res(p):
        d = (model(p, fb) - hb) / np.abs(hb)
        return np.concatenate([d.real, d.imag])

    sol = least_squares(res, p0, bounds=(lo, hi), x_scale="jac", xtol=1e-15, ftol=1e-15, gtol=1e-15)
    p = sol.x.reshape(3, 3)
    fit_err = np.abs(model(sol.x, fb) - hb).max() / np.abs(hb).max()
    # Arias intensity, exact for the piecewise linear record: pi / (2 g) int a^2 dt
    ia = np.concatenate([[0.0], np.cumsum(dt * (ag[:-1] ** 2 + ag[:-1] * ag[1:] + ag[1:] ** 2) / 3)]) * np.pi / (2 * 9.80665)
    d5, d95 = t[np.searchsorted(ia, 0.05 * ia[-1])], t[np.searchsorted(ia, 0.95 * ia[-1])]
    # the independent check: Newmark, finer and finer, against the state space (first 30 s)
    m30 = int(30 * FS_Q) + 1
    nm = [np.abs(newmark(M, K, C, ag[:m30], dt, sub) - urel[:m30, 2]).max() / np.abs(urel[:m30, 2]).max()
          for sub in (1, 2, 4)]
    return dict(t=t, ag=ag, vg=vg, ug=ug, aabs=aabs, urel=urel, fr=fb, h=hb, exact=exact, err=err, fit=p,
                p0=np.array(p0).reshape(3, 3), fit_err=fit_err, ia=ia, d5=d5, d95=d95, corr=corr,
                raw_end=raw_end, newmark=nm, welch_peaks=wpk)


# ------------------------------------------------------------------ the page's signals
def page_signals(ss):
    """One loop of the top row, periodic (the loop is seamless): simulated at
    2 FS_PAGE, kept at FS_PAGE; the ambient forces are white samples at FS,
    linear between them (another realization of the record's process)."""
    dt = 1 / (2 * FS_PAGE)
    n = int(round(LOOP * 2 * FS_PAGE))
    tt = np.arange(n) * dt
    rng = np.random.default_rng(SEED_PAGE)
    nf = int(round(LOOP * FS))
    knots = F_RMS * rng.standard_normal((nf, 3))
    tk = np.arange(nf + 1) / FS
    fam = np.stack([np.interp(tt, tk, np.vstack([knots, knots[:1]])[:, j]) for j in range(3)], 1)
    acc_a, dis_a = periodic(ss, fam, dt)
    a2, d2 = run(ss, np.tile(fam, (16, 1)), dt)
    worst = max(np.abs(d2[-n:] - dis_a).max() / np.abs(dis_a).max(), np.abs(a2[-n:] - acc_a).max() / np.abs(acc_a).max())
    k = slice(0, n, 2)
    return dict(tt=tt[k], knots=knots, acc_a=acc_a[k], dis_a=dis_a[k], periodic_err=worst, dis_a_full=dis_a)


def ema_signals(M, K, C, Q):
    """The bottom row's three histories, each the periodic steady state of its
    own forcing, simulated at FS_Q (the earthquake record's own samples) and
    kept at FS_PAGE: the shaker's sweep every loop (b), the earthquake every
    loop (q), and the two in turn (r: a sweep loop, then an earthquake loop).
    Displacements are absolute (relative + the ground's)."""
    ss = both_statespace(M, K, C)
    dt = 1 / FS_Q
    n = int(round(LOOP * FS_Q))
    tt = np.arange(n) * dt
    k0, kq = int(round(B_T0 * FS_Q)), int(round(Q_END * FS_Q)) + 1
    F = SW_AMP * sweep(tt - B_T0)
    ag = np.zeros(n); ag[k0:k0 + kq] = Q["ag"][:kq]
    ug = np.zeros(n); ug[k0:k0 + kq] = Q["ug"][:kq]
    zero = np.zeros(n)
    forcing = {"b": np.column_stack([F, zero]), "q": np.column_stack([zero, ag]),
               "r": np.vstack([np.column_stack([F, zero]), np.column_stack([zero, ag])])}
    ground = {"b": zero, "q": ug, "r": np.concatenate([zero, ug])}
    out, worst = {}, 0.0
    for key, u_in in forcing.items():
        m = u_in.shape[0]
        _, y, _ = signal.lsim(ss, np.tile(u_in, (8, 1)), np.arange(8 * m) * dt, interp=True)
        _, y2, _ = signal.lsim(ss, np.tile(u_in, (16, 1)), np.arange(16 * m) * dt, interp=True)
        y, y2 = y[-m:], y2[-m:]
        worst = max(worst, np.abs(y2 - y).max(0).max() / np.abs(y).max())
        out[key] = dict(acc=y[:, 2], dis=y[:, 3:] + ground[key][:, None], ground=ground[key])
    return out, worst, ag, ug


def db(x, ref):
    return 10 * np.log10(np.maximum(x, 1e-30) / ref)


# ------------------------------------------------------------------ the page
JS = r"""
const D = DATA;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const L = D.loop, T0 = D.t0, BT0 = D.bt0, SWT = D.swt, RATE = (D.f1 - D.f0) / D.swt;
const tau = () => ((t - T0) % L + L) % L;                  // loop time (before T0: the end of a loop)
const first = () => t < T0 + L;                           // the first loop: the spectrum builds up once
const POSTER_T = D.poster;

/* ------------------------------------------------------------ layout */
const COL = [{x: 22, w: 170}, {x: 232, w: 160}, {x: 432, w: 150}, {x: 622, w: 320}];
const ROW = [{y: 88, h: 120, lab: 76}, {y: 316, h: 140, lab: 304}];
const cx = c => COL[c].x + COL[c].w / 2;
const DASH = '–';
const WORDS = [
  [['Unknown, random force', '(e.g., wind, traffic,', 'footsteps)'], ['Structure'], ['Sensors measure', 'output only'],
   ['Output-only System ID', '(Operational Modal Analysis ' + DASH + ' OMA)']],
  [['Known, controlled force', '(e.g., shaker,', 'earthquake)'], ['Structure'], ['Sensors measure', 'input and output'],
   ['Input-Output System ID', '(Experimental Modal Analysis ' + DASH + ' EMA)']]];

/* ------------------------------------------------------------ the bottom row's input
   his "(e.g., shaker, earthquake)": a shaker driving the roof, or a recorded
   ground motion. The row shows them in turn, test after test (test 0, in the
   first loop, is the shaker's), until the reader picks one; ?view=shaker or
   ?view=earthquake picks one from the start (the overlap check of each). */
const INPUT = ['shaker', 'earthquake'];
const VIEW = (() => { const v = new URLSearchParams(location.search).get('view'); return v === 'shaker' ? 0 : v === 'earthquake' ? 1 : null; })();
let PIN = VIEW, HC = -1, DC = -1;            // the reader's pick; the chip under the pointer, pressed
function reset() { PIN = VIEW; }             // restart: in turn again
const parity = k => ((k % 2) + 2) % 2;
const testNo = () => Math.floor((t - T0 - BT0 + .15) / L);   // the test the row shows: the next one once the last has faded
const shown = () => PIN !== null ? PIN : parity(testNo());   // 0: the shaker, 1: the earthquake

/* ------------------------------------------------------------ signals */
const NPS = D.n, FSP = D.fsp;
const AA = [0, 1, 2].map(j => b64i8(D.a.acc[j])), DA = [0, 1, 2].map(j => b64f32(D.a.dis[j]));
const KN = [0, 1, 2].map(j => b64i8(D.a.knots[j]));
/* the bottom row: three histories, each the periodic steady state of its own
   forcing: the shaker every loop (EB), the earthquake every loop (EQ), the two
   in turn (ER, two loops long, the shaker's loop first) */
const EB = {acc: b64i8(D.b.acc), dis: [0, 1, 2].map(j => b64f32(D.b.dis[j]))};
const EQ = {acc: b64i8(D.q.acc), dis: [0, 1, 2].map(j => b64f32(D.q.dis[j])), ag: b64i8(D.q.ag), ug: b64f32(D.q.ug)};
const ER = {acc: b64i8(D.r.acc), dis: [0, 1, 2].map(j => b64f32(D.r.dis[j]))};
const wrap = (i, n) => ((i % n) + n) % n;
function cr(arr, s) {                                     // Catmull-Rom through the periodic samples, s in seconds
  const u = s * FSP, i = Math.floor(u), f = u - i, n = arr.length;
  const p0 = arr[wrap(i - 1, n)], p1 = arr[wrap(i, n)], p2 = arr[wrap(i + 1, n)], p3 = arr[wrap(i + 2, n)];
  return p1 + .5 * f * (p2 - p0 + f * (2 * p0 - 5 * p1 + 4 * p2 - p3 + f * (3 * (p1 - p2) + p3 - p0)));
}
function sweepF(s) {                                      // the shaker's force, per unit amplitude, s after its start
  if (s < 0 || s > SWT) return 0;
  const tp = D.taper, w = s < tp ? .5 - .5 * Math.cos(Math.PI * s / tp) : s > SWT - tp ? .5 - .5 * Math.cos(Math.PI * (SWT - s) / tp) : 1;
  return w * Math.sin(2 * Math.PI * (D.f0 * s + .5 * RATE * s * s));
}
/* the bottom frame now: floors and ground (units) */
function bottomNow() {
  const s = tau(), s2 = ((t - T0) % (2 * L) + 2 * L) % (2 * L);
  if (PIN === 0) return {u: EB.dis.map(a => cr(a, s)), g: 0};
  if (PIN === 1) return {u: EQ.dis.map(a => cr(a, s)), g: cr(EQ.ug, s)};
  return {u: ER.dis.map(a => cr(a, s2)), g: s2 >= L ? cr(EQ.ug, s2 - L) : 0};
}
/* the records of test k at loop time q: the roof's acceleration and the input, each scaled to 1 */
function a3Of(k, q) {
  if (PIN === 0) return cr(EB.acc, q) / 127;
  if (PIN === 1) return cr(EQ.acc, q) / 127;
  return cr(ER.acc, parity(k) * L + q) / 127;
}
const agOf = q => cr(EQ.ag, q) / 127;
function ariasAt(s) {                                     // the earthquake's Arias intensity so far, of its whole, s after its start
  const u = clamp(s * 20, 0, D.arias.length - 1), i = Math.min(D.arias.length - 2, Math.floor(u));
  return lerp(D.arias[i], D.arias[i + 1], u - i);
}

/* ------------------------------------------------------------ pieces */
function box(c, r, p, o = {}) {
  const x = COL[c].x, y = ROW[r].y, w = COL[c].w, h = ROW[r].h;
  if (o.fill && p > 0) { ctx.save(); ctx.globalAlpha *= clamp(p * 2); ctx.fillStyle = o.fill; ctx.fillRect(x, y, w, h); ctx.restore(); }
  line([[x, y + h], [x, y], [x + w, y], [x + w, y + h], [x, y + h]], { color: C.ink, width: o.width || 1.4, progress: p });
}
function words(r, t0) {
  WORDS[r].forEach((ls, c) => {
    const a = lab(t0 + .03 * c), n = ls.length;
    ls.forEach((s, i) => text(s, cx(c), ROW[r].lab - 22 * (n - 1 - i) + rise(a), { size: 19, align: 'center', alpha: a }));
  });
}
function flow(r, a) {                                      // the arrows between the boxes
  const y = ROW[r].y + ROW[r].h / 2;
  for (let c = 0; c < 3; c++) arrow(COL[c].x + COL[c].w + 7, y, COL[c + 1].x - 7, y, { width: 1.8, head: 9, alpha: a });
}
/* a trace: f(s) for s in [s0, s1] mapped onto [x0, x1], centred on y, half height hh; sampled
   at least as often as the page's data (FSP a second), so no cycle of it is lost or aliased */
function trace(f, s0, s1, x0, x1, y, hh, o) {
  const n = Math.max(2, Math.ceil((x1 - x0) * 1.6), Math.ceil((s1 - s0) * 1.5 * FSP)), pts = [];
  for (let i = 0; i <= n; i++) { const s = s0 + (s1 - s0) * i / n; pts.push([x0 + (x1 - x0) * i / n, y - hh * f(s)]); }
  line(pts, o);
}
const zeroLine = (x0, x1, y, a) => line([[x0, y], [x1, y]], { color: C.rule, width: 1, alpha: a });

/* the frame: three storeys, rigid floors; u (drawing units) at floors 1..3 and g at the ground,
   all absolute; the pale frame at rest stays where it was */
function frameDraw(r, u, p, o = {}) {
  const X = o.X ?? cx(1) + 6, HW = 26, SH = 30, yg = o.yg ?? ROW[r].y + 106, g = o.g || 0;
  const g0 = o.g0 ?? X - 50, g1 = o.g1 ?? X + 44;
  const fl = [g, u[0], u[1], u[2]];
  const ys = k => yg - SH * k;
  // the ground
  line([[g0 + g, yg], [g1 + g, yg]], { width: 1.8, progress: p });
  if (p >= 1) { ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
    for (let x = g0 + 4; x < g1; x += 7) { ctx.moveTo(x + g, yg); ctx.lineTo(x + g - 5, yg + 6); } ctx.stroke(); ctx.restore(); }
  // at rest, pale
  const rest = [[X - HW, yg], [X - HW, ys(3)], [X + HW, ys(3)], [X + HW, yg]];
  line(rest, { color: C.rule, width: 1, progress: p });
  for (let k = 1; k < 3; k++) line([[X - HW, ys(k)], [X + HW, ys(k)]], { color: C.rule, width: 1, alpha: p });
  // columns: a fixed-fixed column between rigid floors bends as 3s^2 - 2s^3
  for (const sgn of [-1, 1]) {
    const pts = [];
    for (let k = 0; k < 3; k++) for (let i = (k ? 1 : 0); i <= 10; i++) {
      const s = i / 10, h = 3 * s * s - 2 * s * s * s;
      pts.push([X + sgn * HW + fl[k] + (fl[k + 1] - fl[k]) * h, ys(k) - SH * s]);
    }
    line(pts, { color: C.blue, width: 1.8, progress: p });
  }
  for (let k = 1; k <= 3; k++) line([[X - HW - 3 + fl[k], ys(k)], [X + HW + 3 + fl[k], ys(k)]], { color: C.navy, width: 2.6, progress: p });
  // accelerometers on each floor
  const sa = o.sensors ?? 1;
  if (sa > 0) for (let k = 1; k <= 3; k++) {
    ctx.save(); ctx.globalAlpha *= sa; ctx.fillStyle = C.navy; ctx.fillRect(X + HW - 11 + fl[k], ys(k) - 7.5, 6.5, 6.5); ctx.restore();
  }
  return { X, HW, SH, yg, ys };
}
/* the shaker beside the roof: an electrodynamic shaker in a trunnion on a post, standing on the
   ground; its armature, the stinger and the force sensor (F) at the roof move with the roof */
function shakerDraw(F, u3, a) {
  if (a <= 0) return;
  const yr = F.ys(3), xe = F.X - F.HW - 3 + u3;            // the roof's left end
  const b0 = F.X - 94, b1 = F.X - 60, px = (b0 + b1) / 2;  // the body, fixed
  line([[b0 + 5, yr + 10], [px, yr + 19], [b1 - 5, yr + 10]], { width: 1.4, alpha: a });   // trunnion
  line([[px, yr + 19], [px, F.yg - 3]], { width: 1.6, alpha: a });                          // post
  line([[px - 10, F.yg - 1.5], [px + 10, F.yg - 1.5]], { width: 3, alpha: a });             // base plate
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy;
  ctx.fillRect(b1 - 8, yr - 4, 18 + u3, 8);                                                 // armature (its back inside the body)
  ctx.fillRect(xe - 7, yr - 6, 7, 12);                                                      // force sensor
  ctx.restore();
  line([[b1 + 10 + u3, yr], [xe - 7, yr]], { width: 1.6, alpha: a });                      // stinger
  line([[b0, yr - 10], [b1, yr - 10], [b1, yr + 10], [b0, yr + 10]], { width: 1.4, fill: C.steel, close: true, alpha: a });
  line([[b1 - 5, yr - 10], [b1 - 5, yr + 10]], { color: C.ink, width: 1, alpha: a });      // its front plate
  dot(px, yr, 3, { color: C.ink, fill: '#fff', width: 1.2, alpha: a });                      // the trunnion's pivot
  math('F', xe - 3.5, yr - 13, { size: 17, align: 'center', alpha: a });
}
/* the earthquake: the ground moves under the frame, an accelerometer on the foundation records it */
function quakeDraw(F, g, a) {
  if (a <= 0) return;
  const sx = F.X - F.HW - 18 + g;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy; ctx.fillRect(sx - 3.5, F.yg - 8, 7, 7); ctx.restore();
  math('a_{g}', F.X - F.HW - 27, F.yg - 14, { size: 17, align: 'right', alpha: a });
  arrow(F.X - 24, F.yg + 16, F.X + 24, F.yg + 16, { color: C.guide, width: 1.4, head: 7, both: true, alpha: a });
}

/* ------------------------------------------------------------ the plots */
const PL = r => ({ x: COL[3].x, y: ROW[r].y, w: COL[3].w, h: ROW[r].h, xlim: [0, D.fmax] });
const FR = D.fr, SPEC = D.spec.map(s => b64f32(s));
const FRF = [D.frf.b, D.frf.q].map(o => ({ f: o.f, est: b64f32(o.est), mod: b64f32(o.mod) }));
function plot(r, p, which) {
  const P = PL(r), lim = D.ylim[which], ticks = D.yticks[which];
  const g = axes({ ...P, ylim: lim, xticks: [0, 1, 2, 3, 4, 5, 6, 7], yticks: ticks, yfmt: () => '', progress: p, tickSize: 16 });
  const a = clamp(p * 1.4);
  for (const v of ticks) math(fmt(v), P.x + P.w + 7, g.Y(v) + 5.5, { size: 16, alpha: a });
  math(D.ylab[which], 992, P.y + P.h / 2, { size: 17, align: 'center', rot: -Math.PI / 2, alpha: a });
  return { g, P: { ...P, ylim: lim } };
}
/* a curve inside the plot, clipped by its box (a value beyond the axis leaves the plot, it is not
   drawn along the frame) */
function curve(g, P, xs, ys, o, upto = Infinity) {
  const pts = [];
  for (let i = 0; i < xs.length; i++) { if (xs[i] > upto) break; pts.push([g.X(xs[i]), g.Y(ys[i])]); }
  if (pts.length > 1) g.inside(() => line(pts, o));
}
function yAt(xs, ys, f) {
  let i = 1; while (i < xs.length - 1 && xs[i] < f) i++;
  return lerp(ys[i - 1], ys[i], (f - xs[i - 1]) / (xs[i] - xs[i - 1]));
}
/* the model's frequencies, dashed up to the curve; the identified ones, a dot and its value */
function marks(g, P, xs, ys, fid, al, am) {
  D.fn.forEach((f, k) => {
    const yc = g.Y(yAt(xs, ys, f));
    if (al > 0) line([[g.X(f), P.y + P.h], [g.X(f), yc + 7]], { color: C.guide, width: 1, dash: [4, 3], alpha: al });
    const ak = am[k];
    if (ak <= 0) return;
    const x = g.X(fid[k]), y = g.Y(yAt(xs, ys, fid[k]));
    dot(x, y, 3.6, { color: C.accent, fill: C.accent, alpha: ak });
    math(fid[k].toFixed(2), x, y - 9 + rise(ak), { size: 16, color: C.accent, align: 'center', alpha: ak });
  });
}

/* ------------------------------------------------------------ top row: OMA */
function rowA() {
  const r = 0, y0 = ROW[r].y, s = tau();
  words(r, .08);
  for (let c = 0; c < 3; c++) box(c, r, seg(.02 + .04 * c, .35));
  flow(r, seg(.25, .25));
  // the unknown forces (grey) and the three accelerations, a window scrolling with the record
  const sw = COL[0].w, x0 = COL[0].x, tr = seg(.2, .4);
  const lvl = [y0 + 24, y0 + 60, y0 + 96];                 // floors 3, 2, 1 top to bottom
  for (let j = 0; j < 3; j++) {
    const fl = 2 - j, kn = KN[fl], nk = kn.length;
    const fAt = q => { const u = q * D.fs, i = Math.floor(u), w = u - i; return lerp(kn[wrap(i, nk)], kn[wrap(i + 1, nk)], w) / 127; };
    math('F_{' + (fl + 1) + '}', x0 + 8, lvl[j] + 5, { size: 17, color: C.muted, alpha: lab(.3) });
    zeroLine(x0 + 34, x0 + sw - 8, lvl[j], tr);
    trace(fAt, s - D.tw, s, x0 + 34, x0 + sw - 8, lvl[j], 13, { color: C.guide, width: 1.1, alpha: tr });
    const ac = AA[fl], x3 = COL[2].x;
    math('a_{' + (fl + 1) + '}', x3 + 8, lvl[j] + 5, { size: 17, alpha: lab(.34) });
    zeroLine(x3 + 34, x3 + COL[2].w - 8, lvl[j], tr);
    trace(q => cr(ac, q) / 127, s - D.tw, s, x3 + 34, x3 + COL[2].w - 8, lvl[j], 13, { color: C.navy, width: 1.2, alpha: tr });
  }
  // the structure, swaying with its computed response; the random forces act on every floor
  const u = [0, 1, 2].map(j => cr(DA[j], s));
  const F = frameDraw(r, u, seg(.1, .35));
  const fa = lab(.35);
  for (let k = 1; k <= 3; k++) {
    const y = F.ys(k) - 4, xa = F.X - F.HW - 24;
    arrow(xa - 8, y, xa + 8, y, { color: C.guide, width: 1.4, head: 6, both: true, alpha: fa });
  }
  // the output spectrum, averaged over more and more of the record, and the modes it holds
  const { g, P } = plot(r, seg(.12, .4), 0);
  const nL = SPEC.length;
  let k = nL - 1, w = 1;                                   // the level shown and its blend from the one before
  if (first()) {
    const q = t - T0 - .2;
    k = q < 0 ? 0 : Math.min(nL - 1, 1 + Math.floor(q / D.step));
    w = q < 0 ? 1 : clamp((q - (k - 1) * D.step) / .25);
  }
  const cp = seg(.25, .45);
  if (k > 0 && w < 1) curve(g, P, FR, SPEC[k - 1], { color: C.navy, width: 1.6, alpha: 1 - w });
  curve(g, P, FR, SPEC[k], { color: C.navy, width: 1.6, alpha: k > 0 ? w : 1, progress: cp });
  const done = !first() || t >= T0 + D.pick;
  const am = D.fn.map((_, i) => done ? (first() ? lab(T0 + D.pick + .08 * i) : 1) : 0);
  marks(g, P, FR, SPEC[nL - 1], D.oma, lab(.5), am);
  // the record so far, under the spectrum between the first two modes
  text('record ' + D.rec[k], g.X(D.reclab), g.Y(D.recdb), { size: 16, color: C.muted, align: 'center', alpha: lab(.45) });
  math('f\\ (\\rm{Hz})', P.x + P.w / 2, P.y + P.h + 42, { size: 17, align: 'center', alpha: seg(.3, .3) });
}

/* ------------------------------------------------------------ bottom row: EMA, a shaker or an earthquake */
const CHIP = [{x: 30, w: 62}, {x: 98, w: 88}], CHY = ROW[1].y + 7, CHH = 27;
function rowB() {
  const r = 1, y0 = ROW[r].y, s = tau(), k = testNo(), cs = shown();
  words(r, .14);
  for (let c = 0; c < 3; c++) box(c, r, seg(.06 + .04 * c, .35));
  flow(r, seg(.3, .25));
  // the input is measured too: from the input to the sensors
  const yb = y0 + ROW[r].h, yf = yb + 20;
  const fp = seg(.35, .35);
  line([[cx(0), yb + 1], [cx(0), yf], [cx(2), yf]], { width: 1.8, progress: fp });
  if (fp >= 1) arrow(cx(2), yf, cx(2), yb + 7, { width: 1.8, head: 9 });
  // the reader's choice of input, in the input's box
  const ca = lab(.3);
  INPUT.forEach((nm, i) => uiChip(CHIP[i].x, CHY, CHIP[i].w, CHH, nm, { on: i === cs, hover: HC === i, down: DC === i, size: 16 }, ca));
  // the test: the input and the response, drawn up to the cursor while it runs; between two tests
  // the last one fades and, while they take turns, the next input takes its place
  const w0 = BT0 - .5, w1 = BT0 + SWT + 1.5;              // loop times shown in the boxes
  const going = s >= w0 + .5 && s < w1;                   // the cursor runs
  const wiping = s >= BT0 - .45 && s < BT0 - .15;
  const wipe = wiping ? 1 - clamp((s - (BT0 - .45)) / .3) : 1;
  const swap = PIN === null;                              // the inputs take turns: the outgoing fades, the next arrives
  const enter = swap && s >= BT0 - .15 && s < BT0 + .15 ? clamp((s - (BT0 - .15)) / .3) : 1;
  const own = swap ? (wiping ? wipe : enter) : 1;         // the alpha of what belongs to the input shown
  const upto = going ? s : w1;
  const x1 = COL[0].x, x3 = COL[2].x, tr = seg(.2, .4);
  const XS = (c, q) => COL[c].x + 34 + (COL[c].w - 42) * (q - w0) / (w1 - w0);
  const TOP = y0 + 46, BOT = y0 + 106, YI = y0 + 92;
  const inName = cs === 0 ? 'F' : 'a_{g}', inRec = cs === 0 ? (q => sweepF(q - BT0)) : agOf;
  math(inName, x1 + 8, YI + 5, { size: 17, alpha: lab(.34) * own });
  zeroLine(x1 + 34, x1 + COL[0].w - 8, YI, tr);
  math(inName, x3 + 8, TOP + 5, { size: 17, alpha: lab(.38) * own });
  math('a_{3}', x3 + 8, BOT + 5, { size: 17, alpha: lab(.4) });
  zeroLine(x3 + 34, x3 + COL[2].w - 8, TOP, tr); zeroLine(x3 + 34, x3 + COL[2].w - 8, BOT, tr);
  const al = tr * wipe * (swap ? enter : 1);
  const draw3 = (c, f, y, hh) => trace(f, w0, upto, XS(c, w0), XS(c, upto), y, hh, { color: C.navy, width: 1.1, alpha: al });
  if (upto > w0 && al > 0) {
    draw3(0, inRec, YI, 26);
    draw3(2, inRec, TOP, 17);
    draw3(2, q => a3Of(k, q), BOT, 24);
  }
  if (going) {
    line([[XS(0, s), y0 + 40], [XS(0, s), y0 + ROW[r].h - 6]], { color: C.ink, width: 1, alpha: .45 });
    line([[XS(2, s), y0 + 6], [XS(2, s), y0 + ROW[r].h - 6]], { color: C.ink, width: 1, alpha: .45 });
  }
  // the structure, and its input: the shaker at the roof, or the ground moving under it
  const B = bottomNow();
  const F = frameDraw(r, B.u, seg(.14, .35), { X: COL[1].x + 114, yg: y0 + 118, g: B.g, g0: COL[1].x + 20, g1: COL[1].x + 148 });
  const ea = lab(.35) * own;
  if (cs === 0) shakerDraw(F, B.u[2], ea); else quakeDraw(F, B.g, ea);
  // the frequency response from the two records, H1 = Sxy / Sxx, on the model's exact curve
  const { g, P } = plot(r, seg(.16, .4), 1 + cs);
  const R = FRF[cs], mp = seg(.3, .45);
  curve(g, P, R.f, R.mod, { color: C.mist, width: 6, alpha: own, progress: mp });
  const l0 = T0 + Math.floor((t - T0) / L) * L;           // this loop's start, page clock
  let am, ra = wipe * (swap ? enter : 1), reach = Infinity;
  if (cs === 0) {
    const sweeping = s >= BT0 && s < BT0 + SWT;
    if (sweeping) {
      reach = D.f0 + RATE * (s - BT0);                    // the sweep's frequency now
      g.inside(() => line([[g.X(reach), P.y + 1], [g.X(reach), P.y + P.h - 1]], { color: C.ink, width: 1, alpha: .45 }));
    }
    am = D.fn.map((f, i) => {
      if (!sweeping) return ra * lab(.62 + .06 * i);       // (at the intro: once the curve is drawn)
      // marked once the sweep has passed the peak's half power band and the cursor has cleared its value
      const w = math(D.ema[i].toFixed(2), 0, -1e4, { size: 15, alpha: 0 });
      const fclear = D.ema[i] + (w / 2 + 5) / (P.w / D.fmax);
      const tp = BT0 + (Math.max(D.fpass[i], fclear) - D.f0) / RATE;
      return s >= tp ? settle(l0 + tp, .28) : 0;
    });
  } else {
    // every frequency at once: the estimate firms up as the ground motion's energy (Arias) arrives,
    // and the modes are marked once 95 % of it has
    const shaking = s >= BT0 && s < w1;
    if (shaking) ra *= ariasAt(s - BT0);
    am = D.fn.map((f, i) => {
      if (!shaking) return wipe * (swap ? enter : 1) * lab(.62 + .06 * i);
      const tp = BT0 + D.d95 + .08 * i;
      return s >= tp ? settle(l0 + tp, .28) : 0;
    });
  }
  curve(g, P, R.f, R.est, { color: C.navy, width: 1.6, alpha: ra, progress: mp }, reach);
  marks(g, P, R.f, R.mod, cs === 0 ? D.ema : D.emaq, lab(.5), am);
  // the axis, and the key to the two curves: a row under the axis label, at the plot's right (both
  // inputs' curves fill the plot, and its free bands are where the identified values stand)
  const xl = seg(.3, .3), ky = P.y + P.h + 64;
  math('f\\ (\\rm{Hz})', P.x + P.w / 2, P.y + P.h + 42, { size: 17, align: 'center', alpha: xl });
  const wm = text('model', 0, -1e4, { size: 16, alpha: 0 }), wh = math('H_{1}', 0, -1e4, { size: 16, alpha: 0 });
  const k1 = P.x + P.w - wh, k0 = k1 - 26 - 20 - wm;
  line([[k0 - 24, ky - 5], [k0 - 6, ky - 5]], { color: C.mist, width: 6, alpha: xl });
  text('model', k0, ky, { size: 16, color: C.body, alpha: xl });
  line([[k1 - 24, ky - 5], [k1 - 6, ky - 5]], { color: C.navy, width: 1.6, alpha: xl });
  math('H_{1}', k1, ky, { size: 16, alpha: xl });
}

function draw() {
  rowA(); rowB();
  const pa = lab(.9);
  math(D.params, 22, H - 30, { size: 15, color: C.muted, alpha: pa });
  math(D.params2, 22, H - 11, { size: 15, color: C.muted, alpha: pa });
}

/* ------------------------------------------------------------ the reader's hand: the two chips
   a radio group (arrows move and pick); a pick holds until the figure is restarted, and a click
   on a chip, or just beside one, never pauses the figure */
if (!STILL) {
  const FIG = document.querySelector('.fig'), css = document.createElement('style');
  // the focus ring 3 units outside the drawn chip, a white gap between (its box set per chip below)
  css.textContent = '.nfc{position:absolute;box-sizing:border-box;margin:0;padding:0;border:0;background:transparent;color:transparent;' +
    'cursor:pointer;font:inherit;white-space:nowrap;-webkit-tap-highlight-color:transparent}.nfc:focus{outline:none}' +
    '.nfc::after{content:"";position:absolute;left:var(--rx);right:var(--rx);top:var(--ry);bottom:var(--ry)}' +
    '.nfc:focus-visible::after{outline:2px solid #095A94;outline-offset:0}';
  document.head.appendChild(css);
  const group = document.createElement('div');
  group.setAttribute('role', 'radiogroup');
  group.setAttribute('aria-label', 'Measured input of the input-output test (they take turns until one is picked)');
  FIG.insertBefore(group, FIG.querySelector('.ctl'));
  const names = ['Shaker on the roof: a measured swept sine force', 'Recorded earthquake: the measured ground acceleration'];
  const btns = [], pct = (v, of) => (v / of * 100) + '%';
  const sync = () => btns.forEach((b, i) => { b.setAttribute('aria-checked', String(PIN === i)); b.tabIndex = i === (PIN ?? 0) ? 0 : -1; });
  const pick = i => { PIN = i; sync(); if (!playing) render(); };
  INPUT.forEach((nm, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'nfc'; b.setAttribute('role', 'radio'); b.textContent = nm;
    b.setAttribute('aria-label', names[i]);
    b.style.left = pct(CHIP[i].x, W); b.style.width = pct(CHIP[i].w, W);
    b.style.top = pct(CHY + CHH / 2 - 18, H); b.style.height = pct(36, H);
    b.style.setProperty('--rx', pct(-3, CHIP[i].w)); b.style.setProperty('--ry', pct(18 - CHH / 2 - 3, 36));
    b.addEventListener('click', e => { e.stopPropagation(); pick(i); });
    b.addEventListener('keydown', e => {
      const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
      const j = e.key === 'Home' ? 0 : e.key === 'End' ? 1 : d ? (i + d + 2) % 2 : -1;
      if (j < 0) return;
      e.preventDefault(); btns[j].focus(); pick(j);
    });
    const hover = (h, d) => () => { HC = h; DC = d; if (!playing) render(); };
    b.addEventListener('pointerenter', hover(i, -1)); b.addEventListener('pointerleave', hover(-1, -1));
    b.addEventListener('pointerdown', hover(i, i)); b.addEventListener('pointerup', hover(i, -1));
    group.appendChild(b); btns.push(b);
  });
  sync();
  const rs = document.getElementById('rs');
  rs.addEventListener('click', () => sync());               // restart: in turn again
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), X = (e.clientX - r.left) * W / r.width, Y = (e.clientY - r.top) * H / r.height;
    if (X > CHIP[0].x - 8 && X < CHIP[1].x + CHIP[1].w + 6 && Y > CHY - 12 && Y < CHY + CHH + 12) e.stopPropagation();
  }, true);
}
boot();
"""


def main():
    M, K, C, w, Phi = frame()
    ss = statespace(M, K, C)
    fn = w / 2 / np.pi
    O = oma(ss)
    E = ema(ss, M, K, C)
    Q = quake(M, K, C)
    P = page_signals(ss)
    BS, b_err, ag_loop, ug_loop = ema_signals(M, K, C, Q)

    # ---- the plots' curves, in dB of each one's highest point (the transmissibility in dB of 1)
    fr = O["fr"]
    band = (fr >= 0.15) & (fr <= 7.0)
    ref = O["spectra"][-1][band].max()
    spec = [db(s[band], ref) for s in O["spectra"]]
    hmax = np.abs(E["h3"]).max()
    keep = np.arange(0, E["fr"].size, 2)
    keepq = np.arange(0, Q["fr"].size, 2)
    frf_b = {"f": E["fr"][keep], "est": common.f32(20 * np.log10(np.abs(E["h3"][keep]) / hmax)),
             "mod": common.f32(20 * np.log10(np.abs(E["exact"][keep]) / hmax))}
    frf_q = {"f": Q["fr"][keepq], "est": common.f32(20 * np.log10(np.abs(Q["h"][keepq]))),
             "mod": common.f32(20 * np.log10(np.abs(Q["exact"][keepq])))}
    # where the sweep has passed each mode's half power band
    fpass = [f * (1 + 2 * ZETA) for f in fn]
    # the traces' scales
    a_amp = np.abs(P["acc_a"]).max()
    knots_amp = np.abs(P["knots"]).max()
    gain_a = 7.0 / np.abs(P["dis_a"]).max()                  # drawing units per metre, top row
    dmax = max(np.abs(BS[k]["dis"]).max() for k in BS)
    gain_e = 9.0 / dmax                                      # the bottom row, all three histories
    n8 = slice(0, None, int(round(FS_Q / FS_PAGE)))
    nl = int(round(LOOP * FS_Q))

    def acc_i8(a, halves=1):
        parts = np.split(a, halves)
        return common.i8(np.concatenate([p / np.abs(p).max() * 127 for p in parts]))

    seg_s = NPER / FS

    def rec_len(n):
        s = seg_s * (n + 1) / 2
        return f"{s / 60:.0f} min" if s < 3600 * 0.99 else f"{s / 3600:.0f} h"

    levels = O["levels"]
    poster = round(T0 + B_T0 + SW_T + 2.0, 2)
    ar = Q["ia"] / Q["ia"][-1]
    arias = [round(float(np.interp(x, Q["t"], ar)), 4) for x in np.arange(0, Q_END + 1e-9, 0.05)]
    data = {
        "loop": LOOP, "t0": T0, "bt0": B_T0, "swt": SW_T, "f0": SW_F0, "f1": SW_F1, "taper": SW_TAPER,
        "fmax": FMAX, "fs": FS, "fsp": FS_PAGE, "n": int(P["tt"].size), "tw": TW, "step": 0.8, "pick": 6.0,
        "poster": poster,
        "a": {"acc": [common.i8(P["acc_a"][:, j] / a_amp * 127) for j in range(3)],
              "dis": [common.f32(P["dis_a"][:, j] * gain_a) for j in range(3)],
              "knots": [common.i8(P["knots"][:, j] / knots_amp * 127) for j in range(3)]},
        "b": {"acc": acc_i8(BS["b"]["acc"][n8]), "dis": [common.f32(BS["b"]["dis"][n8, j] * gain_e) for j in range(3)]},
        "q": {"acc": acc_i8(BS["q"]["acc"][n8]), "dis": [common.f32(BS["q"]["dis"][n8, j] * gain_e) for j in range(3)],
              "ag": acc_i8(ag_loop[n8]), "ug": common.f32(ug_loop[n8] * gain_e)},
        "r": {"acc": acc_i8(BS["r"]["acc"][n8], 2), "dis": [common.f32(BS["r"]["dis"][n8, j] * gain_e) for j in range(3)]},
        "fr": fr[band], "spec": [common.f32(s) for s in spec],
        "rec": [rec_len(n) for n in levels],
        "frf": {"b": frf_b, "q": frf_q},
        "ylim": [[-45, 12], [-45, 12], [-35, 45]], "yticks": [[0, -20, -40], [0, -20, -40], [40, 20, 0, -20]],
        "ylab": [r"\rm{spectrum\ (dB)}", r"|a_{3}/F|\ (\rm{dB})", r"|a_{3}/a_{g}|\ (\rm{dB})"], "reclab": 2.62, "recdb": -42.0,
        "fn": fn, "fpass": fpass, "oma": O["f"], "ema": E["fit"][:, 0], "emaq": Q["fit"][:, 0],
        "arias": arias, "d95": float(Q["d95"]),
        "params": (r"\rm{shear frame, 3 floors: }m\rm{ = 25 t, }k\rm{ = 9.5 MN/m, }\zeta\rm{ = 2%;   model }"
                   r"f_{n}\rm{ = " + ", ".join(f"{v:.2f}" for v in fn) + r" Hz (dashed)}"),
        # (the hyphen is U+2010: math() sets an ASCII hyphen as a minus sign)
        "params2": (r"\rm{shaker: sweep 0.4 to 7 Hz in 12 s;   earthquake: Kanai‐Tajimi noise (2.5 Hz, }\zeta_{g}"
                    r"\rm{ = 0.6), enveloped, PGA " + f"{PGA:g}" + r" m/s}^{2}"),
    }
    quick = "--quick" in sys.argv          # the page alone, to look at it: no scatter, no checks, no check file
    # the output-only identification's own scatter: the same pipeline on other records
    errs = []
    for seed in (range(8) if not quick else []):
        rng = np.random.default_rng(seed)
        acc, _ = run(ss, F_RMS * rng.standard_normal((int(T_OMA * FS), 3)), 1 / FS)
        errs.append(ssi_cov(acc)[0][:3] - fn)
    errs = np.array(errs) if errs else np.zeros((1, 3))
    scatter = dict(n=len(errs), rms=np.sqrt((errs ** 2).mean(0)), max=np.abs(errs).max(0),
                   agree=int(sum(all(f"{a:.2f}" == f"{b:.2f}" for a, b in zip(e + fn, fn)) for e in errs)))
    X = dict(gain_a=gain_a, gain_e=gain_e, poster=poster, a_amp=a_amp, knots_amp=knots_amp, scatter=scatter,
             b_err=b_err, dmax=dmax, BS=BS)
    txt = report(M, K, C, w, Phi, O, E, Q, P, X)
    if not quick:
        with open(os.path.join(HERE, "sd_omaema.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(txt)
    print(txt)
    title = "Figure 2: OMA and EMA workflow"
    aria = ("Two workflows on one three storey frame. Top: an unknown random force shakes it, sensors measure "
            "the output only, and the output spectrum, averaged over a longer and longer record, shows the "
            "modes that output-only identification finds. Bottom: a known input, in turn a shaker's swept force "
            "at the roof and a recorded earthquake ground motion, sensors measure input and output, and the "
            "frequency response estimated from them, drawn on the model's exact curve, gives the same three "
            "natural frequencies. Two chips pick the input.")
    common.build_html(NAME, title, aria, 1000, H, data, poster_js(JS, poster))
    if quick:
        return
    # the page's own motion: its Catmull-Rom sway between the 60 Hz samples against the
    # simulations' samples there, its sweep formula and its Arias intensity against this one
    import guided_ut
    q = (2 * np.arange(1300) + 1) / (2 * FS_PAGE)
    cases = [(f"Array.from({{length: 1300}}, (_, i) => cr(DA[{j}], (2 * i + 1) / {2 * FS_PAGE:g}))",
              P["dis_a_full"][1::2][:1300, j] * gain_a) for j in range(3)]
    half = int(round(FS_Q / FS_PAGE / 2))                     # the simulation's sample half way between two of the page's
    for key, arr in (("EB", "b"), ("EQ", "q")):
        cases += [(f"Array.from({{length: 1300}}, (_, i) => cr({key}.dis[{j}], (2 * i + 1) / {2 * FS_PAGE:g}))",
                   BS[arr]["dis"][half::2 * half][:1300, j] * gain_e) for j in range(3)]
    cases += [(f"Array.from({{length: 2600}}, (_, i) => cr(ER.dis[{j}], (2 * i + 1) / {2 * FS_PAGE:g}))",
               BS["r"]["dis"][half::2 * half][:2600, j] * gain_e) for j in range(3)]
    cases.append(("Array.from({length: 1300}, (_, i) => cr(EQ.ug, (2 * i + 1) / 120))",
                  ug_loop[half::2 * half][:1300] * gain_e))
    sway = guided_ut.check_page(NAME, cases)
    ts = np.arange(0, SW_T, 0.013)
    force = guided_ut.check_page(NAME, [(f"Array.from({{length: {ts.size}}}, (_, i) => sweepF(i * 0.013))", sweep(ts))])
    tq = np.arange(0, Q_END, 0.037)
    arias_err = guided_ut.check_page(NAME, [(f"Array.from({{length: {tq.size}}}, (_, i) => ariasAt(i * 0.037))",
                                             np.interp(tq, Q["t"], ar))])
    sd_check.append(os.path.join(HERE, "sd_omaema.check.txt"), [
        "", "THE PAGE'S OWN MOTION (evaluated in the browser)",
        "  the frames' sway: the page's Catmull-Rom interpolation of its 60 Hz samples, half way between them,",
        "  against the simulations' samples there (the top row, the bottom row's three histories and the",
        f"  ground, all floors): largest difference {sway:.3f} drawing units (the sway reaches 7 and 9 units)",
        f"  the page's sweep formula against this generator's, every 13 ms: largest difference {force:.1e}"
        " (amplitude 1)",
        f"  the page's Arias intensity (its 20 Hz table, linear between; it fades the earthquake's estimate in)"
        f" against the record's: {arias_err:.1e}"])
    print("still:", common.still(NAME))
    rec = sd_check.record(NAME, 2 * LOOP + T0, 0.1, "--dense" in sys.argv)
    # each input held by the reader (?view=), over two loops
    times = [round(float(x), 2) for x in np.arange(0.1, 2 * LOOP + T0 + 1e-9, 0.2)]
    held = {}
    for v in ("shaker", "earthquake"):
        res = overlaps_at(f"view={v}", times)
        held[v] = {k_: r for k_, r in res.items() if r["labels"] or r["crossings"]}
        if held[v]:
            print("COLLISIONS", v, list(held[v].items())[:5])
    rec.insert(-1, f"  each input held by the reader (?view=shaker, ?view=earthquake), at the poster and every 0.2 s"
                   f" from 0.1 to {times[-1]:g} s ({len(times)} moments each): "
                   + ("nothing collides" if not any(held.values()) else "COLLISIONS"))
    sd_check.append(os.path.join(HERE, "sd_omaema.check.txt"), rec)
    if any(held.values()):
        raise SystemExit("collisions with an input held")
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 3.0, 6.0, 7.8, 9.0, 12.0, 16.0, 19.0, 30.0, 36.0]))


def overlaps_at(query, times, width=672):
    """common.overlaps() with a query string: the collisions at the poster and
    at each moment in `times`, with the page in that state."""
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
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?still&overlap&{query}")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(150)
            for s in [None] + list(times):
                if s is not None:
                    pg.evaluate(f"() => {{ t = {s:.6g}; render(); }}")
                lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                out["still" if s is None else f"t={s:g}"] = {"labels": lab, "crossings": cro}
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def report(M, K, C, w, Phi, O, E, Q, P, X):
    L = []
    say = L.append
    fn = w / 2 / np.pi
    cf = closed_form() / 2 / np.pi
    say("Figure 2 (nf-sd-omaema): OMA and EMA workflow")
    say("generator: tools/numfig/sd_omaema.py")
    say("")
    say("MODEL")
    say(f"  shear frame, 3 floors, rigid floor slabs: m = {MASS/1e3:g} t each floor, k = {STIFF/1e6:g} MN/m each")
    say(f"  storey, damping {ZETA*100:g} % in every mode (C = M Phi diag(2 zeta w) Phi^T M)")
    say("  natural frequencies (eigenvalues of K, M) against the closed form of a uniform shear building,")
    say("  w_n = 2 sqrt(k/m) sin((2n - 1) pi / (2(2N + 1))), N = 3:")
    for r in range(3):
        say(f"    f_{r+1} = {fn[r]:.6f} Hz, closed form {cf[r]:.6f} Hz ({fn[r]/cf[r]-1:+.1e})")
    say("  mode shapes (roof = 1): " + "; ".join(", ".join(f"{v:.4f}" for v in Phi[:, r] / Phi[2, r]) for r in range(3)))
    say("")
    say("OMA (top row): output only")
    say(f"  ambient force: independent white noise on the 3 floors, {F_RMS:g} N rms, samples at {FS:g} Hz,")
    say("  linear between them; response by the exact first order hold discretization (scipy lsim)")
    say(f"  record {T_OMA/3600:g} h at {FS:g} Hz, three floor accelerations (seed {SEED_REC})")
    say(f"  spectrum: Welch, Hann, {NPER} samples ({NPER/FS:.1f} s, df = {FS/NPER:.4f} Hz), half overlap, {O['nseg']} averages;")
    say("  the 3 x 3 output spectral matrix, its first singular value s1(f) (frequency domain decomposition)")
    say("  the plot builds up through " + ", ".join(str(n) for n in O["levels"]) + " averages (the record so far)")
    say(f"  identification: covariance driven stochastic subspace identification, order {SSI_ORDER}, {SSI_ROWS} block rows")
    shapes = O["shapes"]
    for r in range(3):
        ph = shapes[:, r] / shapes[2, r]
        say(f"    mode {r+1}: f = {O['f'][r]:.5f} Hz ({(O['f'][r]-fn[r])*1e3:+.2f} mHz, {O['f'][r]/fn[r]-1:+.1e}),"
            f" zeta = {O['zeta'][r]*100:.2f} %, MAC with the model's shape {mac(ph, Phi[:, r]):.5f}")
    sc = X["scatter"]
    say(f"  CHECK: the same identification on {sc['n']} records of 2 h (seeds 0 to {sc['n']-1}, this one among them):")
    say("    the frequencies scatter " + ", ".join(f"{v*1e3:.1f}" for v in sc["rms"]) + " mHz rms about the model's"
        " (modes 1, 2, 3), largest error " + ", ".join(f"{v*1e3:.1f}" for v in sc["max"]) + " mHz;")
    say("    this record's errors are within that scatter, and the two decimals the figure prints hold for "
        f"{sc['agree']} of the {sc['n']} records")
    say("")
    say("EMA (bottom row), input 1, the shaker: input and output")
    say(f"  an electrodynamic shaker on a stand beside the frame drives the roof through a stinger and a force")
    say(f"  sensor: linear sine sweep {SW_F0:g} to {SW_F1:g} Hz in {SW_T:g} s, cosine tapered {SW_TAPER:g} s at both ends,")
    say(f"  {SW_AMP/1e3:g} kN; simulated from rest at {FS_SIM:g} Hz (first order hold, exact), recorded {T_EMA:g} s")
    say("  frequency response a3/F: H1 = S_xy / S_xx (Welch, one rectangular segment: the whole record, which")
    say(f"  starts and ends at rest); the same as the ratio of the two transforms to {E['h1_err']:.1e}")
    say(f"  CHECK: against the exact accelerance -w^2 (K - w^2 M + i w C)^-1 over {SW_F0+0.15:g} to {SW_F1-0.15:g} Hz:")
    say(f"    largest difference {E['frf_err']:.1e} of its largest value")
    say("  modal parameters: a driving point model of 3 modes, -w^2 sum a_r / (w_r^2 - w^2 + 2i zeta_r w_r w),")
    say("  fitted by least squares (start: the mobility's peaks and half power widths);")
    say(f"  largest misfit {E['fit_err']:.1e}")
    for r in range(3):
        f_, z_, a_ = E["fit"][r]
        ph = E["shapes"][:, r] / E["shapes"][2, r]
        say(f"    mode {r+1}: f = {f_:.6f} Hz ({f_/fn[r]-1:+.1e}), zeta = {z_*100:.4f} %,"
            f" MAC (residues of the three floors) {mac(ph, Phi[:, r]):.7f}")
    say("  (peak picking alone would read " + ", ".join(f"{v:.3f}" for v in E["p0"][:, 0])
        + " Hz: at 2 % damping the modes' tails move the peaks)")
    say("")
    say("EMA (bottom row), input 2, the earthquake: base motion recorded")
    say(f"  ground acceleration: seeded white noise (seed {SEED_Q}, unit variance, samples at {WN_FS:g} Hz, linear between)")
    say(f"  through a Kanai-Tajimi filter (firm ground: f_g = {KT_FG:g} Hz, zeta_g = {KT_ZG:g}) and the Clough-Penzien")
    say(f"  high pass (f_f = {CP_FF:g} Hz, zeta_f = {CP_ZF:g}), from rest (scipy lsim, first order hold), sampled at {FS_Q:g} Hz;")
    say(f"  times the Jennings, Housner and Tsai envelope ((t/{ENV_T1:g})^2 to {ENV_T1:g} s, 1 to {ENV_T2:g} s, then"
        f" exp(-{ENV_C:g} (t - {ENV_T2:g})), a cosine")
    say(f"  taper over its last {Q_TAPER:g} s, zero after {Q_END:g} s)")
    c = Q["corr"]
    say(f"  baseline: a_g - c1 e(t) - c2 t e(t) with c1, c2 such that the ground's velocity and displacement are zero")
    say(f"  at {Q_END:g} s (before it: {Q['raw_end'][0]*1e3:.3f} mm/s, {Q['raw_end'][1]*1e3:.3f} mm); after it:"
        f" {Q['vg'][-1]:.1e} m/s, {Q['ug'][-1]:.1e} m at the record's end")
    say(f"  scaled to PGA {PGA:g} m/s^2 (a weak motion, as monitored buildings mostly record):"
        f" PGV {np.abs(Q['vg']).max()*1e3:.2f} mm/s, PGD {np.abs(Q['ug']).max()*1e3:.2f} mm;")
    say(f"  Arias intensity {Q['ia'][-1]*1e6:.2f} x 1e-6 m/s, significant duration (5 to 95 %) {Q['d5']:.2f} to"
        f" {Q['d95']:.2f} s ({Q['d95']-Q['d5']:.2f} s)")
    say("  the frame's response from rest: M u'' + C u' + K u = -M iota a_g (u relative to the ground), state space")
    say(f"  with the record linear between its samples (lsim, first order hold: exact), {T_Q:g} s; roof: relative"
        f" {np.abs(Q['urel'][:, 2]).max()*1e3:.2f} mm,")
    say(f"  absolute acceleration {np.abs(Q['aabs'][:, 2]).max():.3f} m/s^2 (the ground's own {PGA:g})")
    nm = Q["newmark"]
    say(f"  CHECK: Newmark's average acceleration on the same record, the first 30 s, steps of 1/{FS_Q:g}, 1/{2*FS_Q:g},"
        f" 1/{4*FS_Q:g} s: largest difference")
    say(f"    from the state space {nm[0]:.1e}, {nm[1]:.1e}, {nm[2]:.1e} of the roof's largest (second order:"
        f" ratios {nm[0]/nm[1]:.2f}, {nm[1]/nm[2]:.2f})")
    say("  transmissibility a3/a_g: H1 = S_xy / S_xx (Welch, one rectangular segment, the whole record from rest")
    say("  to rest; Hann windowed 40.96 s segments, half overlap, would cut the transient and read the peaks "
        + ", ".join(f"{v*100:+.0f} %" for v in Q["welch_peaks"]) + ")")
    say(f"  CHECK: against the exact a3/a_g = 1 - w^2 [(K - w^2 M + i w C)^-1 (-M iota)]_3 over 0.3 to {FMAX:g} Hz:")
    say(f"    largest difference {Q['err']:.1e} of its largest value ({20*np.log10(np.abs(Q['exact']).max()):.1f} dB);"
        f" at 0.3 Hz |a3/a_g| = {np.abs(Q['h'][0]):.4f} (rigid at low frequency: 1)")
    say("  modal parameters: a model of 3 modes, 1 + w^2 sum c_r / (w_r^2 - w^2 + 2i zeta_r w_r w), fitted by least")
    say(f"  squares (start: the peaks and half power widths); largest misfit {Q['fit_err']:.1e}")
    cs_ = Phi[2] * (Phi.T @ M @ np.ones(3))
    for r in range(3):
        f_, z_, c_ = Q["fit"][r]
        say(f"    mode {r+1}: f = {f_:.6f} Hz ({f_/fn[r]-1:+.1e}), zeta = {z_*100:.4f} %, c = {c_:+.5f}"
            f" (phi_r,3 Gamma_r = {cs_[r]:+.5f})")
    say(f"  CHECK: sum of the fitted c_r = {Q['fit'][:, 2].sum():.6f} (closed form: sum phi_r,3 Gamma_r = 1, the roof's"
        " share of a rigid motion)")
    say("")
    say("ALL FIND THE SAME FREQUENCIES (as the figure prints them, two decimals)")
    say("  model " + ", ".join(f"{v:.2f}" for v in fn) + " Hz; OMA " + ", ".join(f"{v:.2f}" for v in O["f"])
        + " Hz; EMA, shaker " + ", ".join(f"{v:.2f}" for v in E["fit"][:, 0])
        + " Hz; EMA, earthquake " + ", ".join(f"{v:.2f}" for v in Q["fit"][:, 0]) + " Hz")
    assert all(f"{a:.2f}" == f"{b:.2f}" == f"{c:.2f}" == f"{d:.2f}"
               for a, b, c, d in zip(fn, O["f"], E["fit"][:, 0], Q["fit"][:, 0]))
    say("")
    say("THE PAGE")
    say(f"  one loop of {LOOP:g} s, both rows periodic (seamless): the steady state of the loop's forces")
    say(f"  top row: the period simulated 8 times from rest at {2*FS_PAGE:g} Hz, kept at {FS_PAGE:g} Hz; against 16"
        f" periods: largest difference {P['periodic_err']:.1e}")
    say(f"    another realization (seed {SEED_PAGE}) of the same ambient process, a {TW:g} s window scrolling in real time;")
    say(f"    the spectrum builds up once, over the first {0.8*7:.1f} s, then the modes are marked")
    say(f"  bottom row: the test from loop time {B_T0:g} s, in real time; three histories, each the periodic steady")
    say(f"    state of its own forcing (8 periods from rest at {FS_Q:g} Hz, kept at {FS_PAGE:g} Hz; against 16 periods:"
        f" largest difference {X['b_err']:.1e}):")
    say("    the shaker every loop, the earthquake every loop, and the two in turn (two loops: the shaker's, then the")
    say("    earthquake's); the row shows the inputs in turn (test 0, in the first loop, is the shaker's; the intro")
    say("    shows the earthquake's before it), and a chip holds one, with its own history, until a restart")
    say("    shaker: a3/F drawn as the sweep passes each frequency; a mode is marked once the sweep has passed its")
    say("    half power band and the cursor its value")
    say("    earthquake: every frequency at once; the estimate firms up with the ground motion's Arias intensity and")
    say(f"    the modes are marked at 95 % of it ({Q['d95']:.2f} s into the motion)")
    say(f"  frames drawn 30 units a storey; sway x {X['gain_a']/1e3:.0f} units/mm (top: ambient), x"
        f" {X['gain_e']/1e3:.2f} units/mm (bottom: all three histories,")
    say(f"    the same scale; the largest absolute floor displacement {X['dmax']*1e3:.2f} mm draws 9 units); the ground"
        f" moves {np.abs(X['BS']['q']['ground']).max()*X['gain_e']:.1f} units at most")
    say(f"  the traces are scaled to their largest values: ambient force {X['knots_amp']:.0f} N, accelerations"
        f" {X['a_amp']*1e3:.1f} mm/s^2 (top); each bottom record to its own largest")
    say(f"  poster (printed frame) at t = {X['poster']} s: both rows complete, the sweep just over (the shaker shown,")
    say("    the earthquake's chip beside it)")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
