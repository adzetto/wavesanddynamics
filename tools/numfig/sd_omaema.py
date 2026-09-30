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

  EMA (bottom row): a shaker on the roof applies a known sine sweep,
  0.4 to 7 Hz; the force and the roof acceleration are recorded; the
  frequency response a3/F is their ratio, and a three mode modal model
  fitted to it gives the modal parameters.

Both rows find the model's three natural frequencies; the check file
compares them with the eigenvalues and with the closed form of a uniform
shear building, w_n = 2 sqrt(k/m) sin((2n - 1) pi / (2(2N + 1))).

Run: python tools/numfig/sd_omaema.py [--look]   (writes content/anim/
nf-sd-omaema.html and .webp and tools/numfig/sd_omaema.check.txt)
"""
import os
import sys

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
B_T0 = 7.0                                 # loop time the sweep starts
FS_PAGE = 60.0                             # Hz: the page's samples (simulated at 120 Hz)
TW = 8.0                                   # s: the window of the ambient traces
LEVELS = [1, 2, 4, 8, 16, 32, 64]          # averages shown on the way to the whole record


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


def frf(M, K, C, f):
    """Receptance matrices H(f) = (K - w^2 M + i w C)^-1, shape (len(f), 3, 3)."""
    return np.array([np.linalg.inv(K - (2 * np.pi * x) ** 2 * M + 2j * np.pi * x * C) for x in np.atleast_1d(f)])


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


# ------------------------------------------------------------------ EMA
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
                fit_err=fit_err, shapes=shapes)


# ------------------------------------------------------------------ the page's signals
def page_signals(ss):
    """One loop of both rows, periodic (the loop is seamless): simulated at
    2 FS_PAGE, kept at FS_PAGE. Top: the ambient forces (white samples at FS,
    linear between them: another realization of the record's process).
    Bottom: the sweep from loop time B_T0."""
    dt = 1 / (2 * FS_PAGE)
    n = int(round(LOOP * 2 * FS_PAGE))
    tt = np.arange(n) * dt
    rng = np.random.default_rng(SEED_PAGE)
    nf = int(round(LOOP * FS))
    knots = F_RMS * rng.standard_normal((nf, 3))
    tk = np.arange(nf + 1) / FS
    fam = np.stack([np.interp(tt, tk, np.vstack([knots, knots[:1]])[:, j]) for j in range(3)], 1)
    acc_a, dis_a = periodic(ss, fam, dt)
    fsw = np.zeros((n, 3))
    fsw[:, 2] = SW_AMP * sweep(tt - B_T0)
    acc_b, dis_b = periodic(ss, fsw, dt)
    # the steady state against a run twice as long from rest (its last period)
    worst = 0.0
    for f, a, d in ((fam, acc_a, dis_a), (fsw, acc_b, dis_b)):
        a2, d2 = run(ss, np.tile(f, (16, 1)), dt)
        worst = max(worst, np.abs(d2[-n:] - d).max() / np.abs(d).max(), np.abs(a2[-n:] - a).max() / np.abs(a).max())
    k = slice(0, n, 2)
    return dict(tt=tt[k], knots=knots, acc_a=acc_a[k], dis_a=dis_a[k], acc_b=acc_b[k], dis_b=dis_b[k],
                fsw=fsw[k, 2], periodic_err=worst, dis_a_full=dis_a, dis_b_full=dis_b)


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
const COL = [{x: 22, w: 170}, {x: 240, w: 120}, {x: 408, w: 170}, {x: 626, w: 320}];
const ROW = [{y: 88, h: 120, lab: 76}, {y: 312, h: 120, lab: 300}];
const cx = c => COL[c].x + COL[c].w / 2;
const DASH = '–';
const WORDS = [
  [['Unknown, random force', '(e.g., wind, traffic,', 'footsteps)'], ['Structure'], ['Sensors measure', 'output only'],
   ['Output-only System ID', '(Operational Modal Analysis ' + DASH + ' OMA)']],
  [['Known, controlled force', '(e.g., shaker,', 'earthquake)'], ['Structure'], ['Sensors measure', 'input and output'],
   ['Input-Output System ID', '(Experimental Modal Analysis ' + DASH + ' EMA)']]];

/* ------------------------------------------------------------ signals */
const NPS = D.n, FSP = D.fsp;
const AA = [0, 1, 2].map(j => b64i8(D.a.acc[j])), DA = [0, 1, 2].map(j => b64f32(D.a.dis[j]));
const KN = [0, 1, 2].map(j => b64i8(D.a.knots[j]));
const AB = b64i8(D.b.acc), DB = [0, 1, 2].map(j => b64f32(D.b.dis[j]));
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

/* ------------------------------------------------------------ pieces */
function box(c, r, p, o = {}) {
  const x = COL[c].x, y = ROW[r].y, w = COL[c].w, h = ROW[r].h;
  if (o.fill && p > 0) { ctx.save(); ctx.globalAlpha *= clamp(p * 2); ctx.fillStyle = o.fill; ctx.fillRect(x, y, w, h); ctx.restore(); }
  line([[x, y + h], [x, y], [x + w, y], [x + w, y + h], [x, y + h]], { color: C.ink, width: o.width || 1.4, progress: p });
}
function words(r, t0) {
  WORDS[r].forEach((ls, c) => {
    const a = lab(t0 + .03 * c), n = ls.length;
    ls.forEach((s, i) => text(s, cx(c), ROW[r].lab - 20 * (n - 1 - i) + rise(a), { size: 17, align: 'center', alpha: a }));
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

/* the frame: three storeys, rigid floors; u (drawing units) at floors 1..3 */
function frameDraw(r, u, p, o = {}) {
  const X = cx(1) + 6, HW = 26, SH = 30, yg = ROW[r].y + 106;
  const fl = [0, u[0], u[1], u[2]];
  const ys = k => yg - SH * k;
  // the ground
  line([[X - 50, yg], [X + 44, yg]], { width: 1.8, progress: p });
  if (p >= 1) { ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
    for (let x = X - 46; x < X + 44; x += 7) { ctx.moveTo(x, yg); ctx.lineTo(x - 5, yg + 6); } ctx.stroke(); ctx.restore(); }
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

/* ------------------------------------------------------------ the plots */
const PL = r => ({ x: COL[3].x, y: ROW[r].y, w: COL[3].w, h: ROW[r].h, xlim: [0, D.fmax], ylim: D.ylim[r] });
const FR = D.fr, NF = FR.length, SPEC = D.spec.map(s => b64f32(s)), FRB = D.frf.f, HB = b64f32(D.frf.db);
function plot(r, p) {
  const P = PL(r);
  const g = axes({ ...P, xticks: [0, 1, 2, 3, 4, 5, 6, 7], yticks: D.yticks[r], yfmt: () => '', progress: p });
  const a = clamp(p * 1.4);
  for (const v of D.yticks[r]) math(fmt(v), P.x + P.w + 7, g.Y(v) + 5, { size: 15, alpha: a });
  math(D.ylab[r], 993, P.y + P.h / 2, { size: 15, align: 'center', rot: -Math.PI / 2, alpha: a });
  return g;
}
function curve(g, P, xs, ys, o, upto = Infinity) {
  const pts = [];
  for (let i = 0; i < xs.length; i++) { if (xs[i] > upto) break; pts.push([g.X(xs[i]), g.Y(clamp(ys[i], P.ylim[0], P.ylim[1]))]); }
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
    math(fid[k].toFixed(2), x, y - 9 + rise(ak), { size: 15, color: C.accent, align: 'center', alpha: ak });
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
    math('F_{' + (fl + 1) + '}', x0 + 8, lvl[j] + 5, { size: 14, color: C.muted, alpha: lab(.3) });
    zeroLine(x0 + 32, x0 + sw - 8, lvl[j], tr);
    trace(fAt, s - D.tw, s, x0 + 32, x0 + sw - 8, lvl[j], 13, { color: C.guide, width: 1.1, alpha: tr });
    const ac = AA[fl], x3 = COL[2].x;
    math('a_{' + (fl + 1) + '}', x3 + 8, lvl[j] + 5, { size: 14, alpha: lab(.34) });
    zeroLine(x3 + 32, x3 + COL[2].w - 8, lvl[j], tr);
    trace(q => cr(ac, q) / 127, s - D.tw, s, x3 + 32, x3 + COL[2].w - 8, lvl[j], 13, { color: C.navy, width: 1.2, alpha: tr });
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
  const P = PL(r), g = plot(r, seg(.12, .4));
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
  text('record ' + D.rec[k], g.X(D.reclab), P.y + 20, { size: 14, color: C.muted, align: 'center', alpha: lab(.45) });
}

/* ------------------------------------------------------------ bottom row: EMA */
function rowB() {
  const r = 1, y0 = ROW[r].y, s = tau();
  words(r, .14);
  for (let c = 0; c < 3; c++) box(c, r, seg(.06 + .04 * c, .35));
  flow(r, seg(.3, .25));
  // the input is measured too: from the force to the sensors
  const yb = y0 + ROW[r].h, yf = yb + 20;
  const fp = seg(.35, .35);
  line([[cx(0), yb + 1], [cx(0), yf], [cx(2), yf]], { width: 1.8, progress: fp });
  if (fp >= 1) arrow(cx(2), yf, cx(2), yb + 7, { width: 1.8, head: 9 });
  // the test: the sweep and the decay after it, drawn up to the cursor while it runs
  const w0 = BT0 - .5, w1 = BT0 + SWT + 1.5;              // loop times shown in the boxes
  const going = s >= BT0 && s < w1;                       // the cursor runs
  const wiping = s >= BT0 - .45 && s < BT0;               // the last test fades before the next
  const wipe = wiping ? 1 - clamp((s - (BT0 - .45)) / .3) : 1;
  const upto = going ? s : w1;
  const x1 = COL[0].x, x3 = COL[2].x, tr = seg(.2, .4);
  const XS = (c, q) => COL[c].x + 32 + (COL[c].w - 40) * (q - w0) / (w1 - w0);
  const TOP = y0 + 34, BOT = y0 + 86;
  math('F', x1 + 8, y0 + 65, { size: 14, alpha: lab(.34) });
  zeroLine(x1 + 32, x1 + COL[0].w - 8, y0 + 60, tr);
  math('F', x3 + 8, TOP + 5, { size: 14, alpha: lab(.38) });
  math('a_{3}', x3 + 8, BOT + 5, { size: 14, alpha: lab(.4) });
  zeroLine(x3 + 32, x3 + COL[2].w - 8, TOP, tr); zeroLine(x3 + 32, x3 + COL[2].w - 8, BOT, tr);
  const aB = q => cr(AB, q) / 127;
  const al = tr * wipe;
  const draw3 = (c, f, y, hh) => trace(f, w0, upto, XS(c, w0), XS(c, upto), y, hh, { color: C.navy, width: 1.1, alpha: al });
  if (upto > w0 && al > 0) {
    draw3(0, q => sweepF(q - BT0), y0 + 60, 26);
    draw3(2, q => sweepF(q - BT0), TOP, 16);
    draw3(2, aB, BOT, 24);
  }
  if (going) for (const c of [0, 2]) line([[XS(c, s), y0 + 6], [XS(c, s), y0 + ROW[r].h - 6]], { color: C.ink, width: 1, alpha: .45 });
  // the structure and the shaker on its roof
  const u = [0, 1, 2].map(j => cr(DB[j], s));
  const F = frameDraw(r, u, seg(.14, .35));
  const sa = lab(.35), ys = F.ys(3), xb = COL[1].x + 8;       // a modal shaker beside the roof, on its stinger
  ctx.save(); ctx.globalAlpha *= sa; ctx.fillStyle = C.navy; ctx.fillRect(xb, ys - 6, 15, 12); ctx.restore();
  line([[xb + 15, ys], [F.X - F.HW - 3 + u[2], ys]], { color: C.ink, width: 1.4, alpha: sa });
  // the frequency response a3/F, revealed as the sweep passes each frequency
  const P = PL(r), g = plot(r, seg(.16, .4));
  const sweeping = s >= BT0 && s < BT0 + SWT;
  const fs = sweeping ? D.f0 + RATE * (s - BT0) : Infinity;   // the sweep's frequency now
  curve(g, P, FRB, HB, { color: C.navy, width: 1.6, alpha: wipe, progress: seg(.3, .45) }, fs);
  if (sweeping) g.inside(() => line([[g.X(fs), P.y + 1], [g.X(fs), P.y + P.h - 1]], { color: C.ink, width: 1, alpha: .45 }));
  const l0 = T0 + Math.floor((t - T0) / L) * L;           // this loop's start, page clock
  const am = D.fn.map((f, i) => {
    if (!sweeping) return wipe * lab(.62 + .06 * i);        // (at the intro: once the curve is drawn)
    // marked once the sweep has passed the peak's half power band and the cursor has cleared its value
    const w = math(D.ema[i].toFixed(2), 0, -1e4, { size: 15, alpha: 0 });
    const fclear = D.ema[i] + (w / 2 + 5) / (P.w / D.fmax);
    const tp = BT0 + (Math.max(D.fpass[i], fclear) - D.f0) / RATE;
    return s >= tp ? settle(l0 + tp, .28) : 0;
  });
  marks(g, P, FRB, HB, D.ema, lab(.5), am);
  const xl = seg(.3, .3);
  math('f\\ (\\rm{Hz})', P.x + P.w / 2, P.y + P.h + 42, { size: 16, align: 'center', alpha: xl });
}

function draw() {
  rowA(); rowB();
  const pa = lab(.9);
  math(D.params, 22, H - 12, { size: 14, color: C.muted, alpha: pa });
}
boot();
"""


def main():
    M, K, C, w, Phi = frame()
    ss = statespace(M, K, C)
    fn = w / 2 / np.pi
    O = oma(ss)
    E = ema(ss, M, K, C)
    P = page_signals(ss)

    # ---- the plots' curves, in dB of each one's highest point
    fr = O["fr"]
    band = (fr >= 0.15) & (fr <= 7.0)
    ref = O["spectra"][-1][band].max()
    spec = [db(s[band], ref) for s in O["spectra"]]
    hdb = 20 * np.log10(np.abs(E["h3"]) / np.abs(E["h3"]).max())
    keep = np.arange(0, E["fr"].size, 2)
    # where the sweep has passed each mode's half power band
    fpass = [f * (1 + 2 * ZETA) for f in fn]
    # the traces' scales
    a_amp = np.abs(P["acc_a"]).max()
    knots_amp = np.abs(P["knots"]).max()
    b_amp = np.abs(P["acc_b"][:, 2]).max()
    gain_a = 7.0 / np.abs(P["dis_a"]).max()                  # drawing units per metre, top row
    gain_b = 9.0 / np.abs(P["dis_b"]).max()
    seg_s = NPER / FS
    def rec_len(n):
        s = seg_s * (n + 1) / 2
        return f"{s / 60:.0f} min" if s < 3600 * 0.99 else f"{s / 3600:.0f} h"
    levels = O["levels"]
    poster = round(T0 + B_T0 + SW_T + 2.0, 2)
    data = {
        "loop": LOOP, "t0": T0, "bt0": B_T0, "swt": SW_T, "f0": SW_F0, "f1": SW_F1, "taper": SW_TAPER,
        "fmax": FMAX, "fs": FS, "fsp": FS_PAGE, "n": int(P["tt"].size), "tw": TW, "step": 0.8, "pick": 6.0,
        "poster": poster,
        "a": {"acc": [common.i8(P["acc_a"][:, j] / a_amp * 127) for j in range(3)],
              "dis": [common.f32(P["dis_a"][:, j] * gain_a) for j in range(3)],
              "knots": [common.i8(P["knots"][:, j] / knots_amp * 127) for j in range(3)]},
        "b": {"acc": common.i8(P["acc_b"][:, 2] / b_amp * 127),
              "dis": [common.f32(P["dis_b"][:, j] * gain_b) for j in range(3)]},
        "fr": fr[band], "spec": [common.f32(s) for s in spec],
        "rec": [rec_len(n) for n in levels],
        "frf": {"f": E["fr"][keep], "db": common.f32(hdb[keep])},
        "ylim": [[-45, 12], [-45, 12]], "yticks": [[0, -20, -40], [0, -20, -40]],
        "ylab": [r"\rm{spectrum\ (dB)}", r"|a_{3}/F|\ (\rm{dB})"], "reclab": 2.65,
        "fn": fn, "fpass": fpass, "oma": O["f"], "ema": E["fit"][:, 0],
        "params": (r"\rm{shear frame, 3 floors: }m\rm{ = 25 t, }k\rm{ = 9.5 MN/m, }\zeta\rm{ = 2 %;   model }"
                   r"f_{n}\rm{ = " + ", ".join(f"{v:.2f}" for v in fn) + r" Hz (dashed);   sweep 0.4 to 7 Hz in 12 s}"),
    }
    # the output-only identification's own scatter: the same pipeline on other records
    errs = []
    for seed in range(8):
        rng = np.random.default_rng(seed)
        acc, _ = run(ss, F_RMS * rng.standard_normal((int(T_OMA * FS), 3)), 1 / FS)
        errs.append(ssi_cov(acc)[0][:3] - fn)
    errs = np.array(errs)
    scatter = dict(n=len(errs), rms=np.sqrt((errs ** 2).mean(0)), max=np.abs(errs).max(0),
                   agree=int(sum(all(f"{a:.2f}" == f"{b:.2f}" for a, b in zip(e + fn, fn)) for e in errs)))
    txt = report(M, K, C, w, Phi, O, E, P, dict(gain_a=gain_a, gain_b=gain_b, poster=poster, a_amp=a_amp,
                                                    b_amp=b_amp, knots_amp=knots_amp, scatter=scatter))
    with open(os.path.join(HERE, "sd_omaema.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Figure 2: OMA and EMA workflow"
    aria = ("Two workflows on one three storey frame. Top: an unknown random force shakes it, sensors measure "
            "the output only, and the output spectrum, averaged over a longer and longer record, shows the "
            "modes that output-only identification finds. Bottom: a shaker applies a known sweep, sensors "
            "measure input and output, and their ratio, the frequency response, gives the same three "
            "natural frequencies.")
    common.build_html(NAME, title, aria, 1000, 512, data, poster_js(JS, poster))
    # the page's own motion: its Catmull-Rom sway between the 60 Hz samples against the
    # simulation's 120 Hz samples there, and its sweep formula against this one
    import guided_ut
    mid = lambda arr, g: arr[1::2][:1300] * g                                  # the samples the page lacks
    q = (2 * np.arange(1300) + 1) / (2 * FS_PAGE)
    cases = [(f"Array.from({{length: 1300}}, (_, i) => cr(DA[{j}], (2 * i + 1) / {2 * FS_PAGE:g}))",
              mid(P["dis_a_full"][:, j], gain_a)) for j in range(3)]
    cases += [(f"Array.from({{length: 1300}}, (_, i) => cr(DB[{j}], (2 * i + 1) / {2 * FS_PAGE:g}))",
               mid(P["dis_b_full"][:, j], gain_b)) for j in range(3)]
    sway = guided_ut.check_page(NAME, cases)
    ts = np.arange(0, SW_T, 0.013)
    force = guided_ut.check_page(NAME, [(f"Array.from({{length: {ts.size}}}, (_, i) => sweepF(i * 0.013))", sweep(ts))])
    sd_check.append(os.path.join(HERE, "sd_omaema.check.txt"), [
        "", "THE PAGE'S OWN MOTION (evaluated in the browser)",
        "  the frames' sway: the page's Catmull-Rom interpolation of its 60 Hz samples, half way between them,",
        f"  against the simulation's 120 Hz samples there (both rows, all floors, the first {1300 / FS_PAGE:.1f} s):",
        f"  largest difference {sway:.3f} drawing units (the sway reaches 7 and 9 units)",
        f"  the page's sweep formula against this generator's, every 13 ms: largest difference {force:.1e}"
        " (amplitude 1)"])
    print("still:", common.still(NAME))
    sd_check.append(os.path.join(HERE, "sd_omaema.check.txt"),
                    sd_check.record(NAME, 2 * LOOP + T0, 0.1, "--dense" in sys.argv))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 3.0, 6.0, 7.8, 9.0, 12.0, 16.0, 19.0]))


def report(M, K, C, w, Phi, O, E, P, X):
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
    say("EMA (bottom row): input and output")
    say(f"  a shaker on the roof: linear sine sweep {SW_F0:g} to {SW_F1:g} Hz in {SW_T:g} s, cosine tapered {SW_TAPER:g} s at both ends,")
    say(f"  {SW_AMP/1e3:g} kN; simulated from rest at {FS_SIM:g} Hz (first order hold, exact), recorded {T_EMA:g} s")
    say("  frequency response a3/F: the transforms of the roof acceleration and the force, divided")
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
    say("BOTH FIND THE SAME FREQUENCIES (as the figure prints them, two decimals)")
    say("  model " + ", ".join(f"{v:.2f}" for v in fn) + " Hz; OMA " + ", ".join(f"{v:.2f}" for v in O["f"])
        + " Hz; EMA " + ", ".join(f"{v:.2f}" for v in E["fit"][:, 0]) + " Hz")
    assert all(f"{a:.2f}" == f"{b:.2f}" == f"{c:.2f}" for a, b, c in zip(fn, O["f"], E["fit"][:, 0]))
    say("")
    say("THE PAGE")
    say(f"  one loop of {LOOP:g} s, both rows periodic (seamless): the steady state of the loop's forces, the")
    say(f"  period simulated 8 times from rest at {2*FS_PAGE:g} Hz, kept at {FS_PAGE:g} Hz; against 16 periods:"
        f" largest difference {P['periodic_err']:.1e}")
    say(f"  top row: another realization (seed {SEED_PAGE}) of the same ambient process, a {TW:g} s window scrolling in real time;")
    say(f"    the spectrum builds up once, over the first {0.8*7:.1f} s, then the modes are marked")
    say(f"  bottom row: the sweep from loop time {B_T0:g} s, in real time; a3/F drawn as the sweep passes each")
    say("    frequency; a mode is marked once the sweep has passed its half power band and the cursor its value")
    say(f"  frames drawn 30 units a storey; sway x {X['gain_a']/1e3:.0f} units/mm (top: ambient), x"
        f" {X['gain_b']/1e3:.1f} units/mm (bottom: the sweep)")
    say(f"  the traces are scaled to their largest values: ambient force {X['knots_amp']:.0f} N, accelerations"
        f" {X['a_amp']*1e3:.1f} mm/s^2 (top), roof {X['b_amp']:.3f} m/s^2 (bottom)")
    say(f"  poster (printed frame) at t = {X['poster']} s: both rows complete, the sweep just over")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
