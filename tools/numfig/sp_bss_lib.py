"""Two sensors, two sources: the blind source separation model shared by
Figures 10 and 11 of the signal processing document (sp_bss_ica.py, method 1,
kurtosis ICA; sp_bss_sobi.py, method 2, SOBI-family separation and Wiener
denoising), so that both figures separate the very same records.

The model is the professor's own (his page "Blind source separation, method
2"), number for number, with his seeded generator:

  fs = 500 Hz; a record of T = 4, 16 or 64 s, N = 500 T samples.
  s1(t) = (1 + 0.5 sin 2 pi 0.4 t)(sin 2 pi 3 t + 0.45 sin(2 pi 6 t + 0.7) + 0.25 sin(2 pi 9 t + 1.3)):
          a harmonic excitation (rotating machinery), 3 Hz with its 6 and 9 Hz
          harmonics, amplitude-modulated at 0.4 Hz;
  s2(t) = sum_i a_i exp(-zeta w_n (t - t_i)) sin(w_d (t - t_i)) for 0 <= t - t_i <= 2 s:
          impacts, each ringing an 11 Hz mode with zeta = 0.08; t_1 = 0.1 s,
          t_(i+1) = t_i + 0.25 + 0.6 r, a_i = +-(0.5 + 0.5 r), r from mulberry32(21);
  both standardized over the record (zero mean, unit variance);
  x = A s + sigma n, A = [[1, 0.7], [0.45, 1]], n two standardized white
  Gaussian channels (his Box-Muller on mulberry32(7 + T)), and
  sigma^2 = P_min 10^(-SNR/10), P_min = min_i sum_j A_ij^2 = 1.2025: the SNR
  is the weaker sensor's.

(His method 1 page has seven fixed impacts in 3 s; they cannot fill a 16 s
or 64 s record, so both figures use the impact train above.)

Every stage of both methods is a 2 x 4 matrix acting on u = [s1, s2, n1, n2]
(his own device), except the Wiener filter of method 2. The pages get u (the
first 4 s, every second sample, int8) and the matrices; they draw
(display matrix) u themselves.

The methods, exact:
  kurtosis_ica(x): whitening z = W x (W from the sample covariance, his PCA
      convention), then the rotation y = R(theta) z maximizing
      K(theta) = |kurt y1| + |kurt y2|, kurt = E y^4 - 3. K is a trigonometric
      polynomial in theta through the five fourth moments of z, so theta is
      found on a 0.01 degree grid and refined to 1e-12 rad.
  sobi_family(x, T): his method 2 (Welch cross-spectra, noise floor = median,
      bands 4 standard errors above it, noise-corrected whitening from the
      bands' summed real cross-spectral matrices, joint diagonalization of the
      bands' matrices by one rotation, Wiener gains with over-subtraction
      1 + 2/sqrt(K)); the rotation in closed form: the off-diagonal of
      R D_k R^T is h_k . (cos 2 theta, sin 2 theta), h_k = (q_k, (r_k - p_k)/2),
      so J(theta) = v' G v with G = sum h_k h_k', minimized by G's eigenvector
      of the smaller eigenvalue.
  match(B): sign and permutation (no method can know them): the pairing of
      outputs and sources with the larger |G_11 G_22| or |G_12 G_21|,
      G = B A; SIR per source from G.

LIB is the JavaScript both pages share (data, the stage clock, chips,
lanes, scatter, table, controls); each figure's script follows it. A change
to LIB reaches a page when its generator is run again (reskin.py tracks the
generator's own JS string only).
"""
import math

import numpy as np

FS = 500.0
A = np.array([[1.0, 0.7], [0.45, 1.0]])
FN, ZETA = 11.0, 0.08
WN = 2 * math.pi * FN
WD = WN * math.sqrt(1 - ZETA ** 2)
PMIN = float(min((A ** 2).sum(1)))           # 1.2025, the weaker sensor's signal power
RECORDS = (4, 16, 64)                        # s
WELCH = {4: 256, 16: 1024, 64: 2048}         # Welch segment per record (his LEN)
SNRS = tuple(range(-30, 41, 5))              # the reader's choices (dB)
SHOW_T = 4.0                                 # seconds shown
DECIM = 2                                    # every second sample shown: 250 Hz
FMAX = 40.0                                  # Hz shown of the spectra


# ------------------------------------------------------------------ his generator
def mulberry32(seed):
    """His seeded generator, bit for bit (32-bit integer arithmetic)."""
    s = seed & 0xFFFFFFFF

    def r():
        nonlocal s
        s = (s + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((s ^ (s >> 15)) * (s | 1)) & 0xFFFFFFFF
        t = ((t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return r


def gauss_from(r):
    """His Box-Muller (the cosine branch only): two draws per value."""
    def g():
        u1 = r()
        u2 = r()
        return math.sqrt(-2 * math.log(u1 + 1e-12)) * math.cos(2 * math.pi * u2)
    return g


def standardize(a):
    a = np.asarray(a, float) - np.mean(a)
    return a / math.sqrt(float(a @ a) / len(a))


# ------------------------------------------------------------------ the model
def harmonic(t):
    return ((1 + 0.5 * np.sin(2 * math.pi * 0.4 * t))
            * (np.sin(2 * math.pi * 3 * t) + 0.45 * np.sin(2 * math.pi * 6 * t + 0.7)
               + 0.25 * np.sin(2 * math.pi * 9 * t + 1.3)))


def impacts(T, seed=21):
    """(t_i, a_i) as his loop draws them: sign, then size, then the gap."""
    r = mulberry32(seed)
    out, t = [], 0.1
    while t < T:
        sign = -1.0 if r() < 0.5 else 1.0
        out.append((t, sign * (0.5 + 0.5 * r())))
        t += 0.25 + 0.6 * r()
    return out


def impact_train(t, imp, cut=2.0):
    """Each impact rings the damped 11 Hz mode; his page drops it after 2 s
    (exp(-zeta w_n 2 s) = 1.6e-5); cut=None keeps it forever (method 1 page)."""
    v = np.zeros_like(t)
    for t0, a in imp:
        u = t - t0
        m = (u >= 0) & (u <= cut) if cut is not None else (u >= 0)
        v[m] += a * np.exp(-ZETA * WN * u[m]) * np.sin(WD * u[m])
    return v


def noise(N, seed):
    """Two standardized white Gaussian channels, drawn alternately as his loop does."""
    g = gauss_from(mulberry32(seed))
    nn = np.array([[g(), g()] for _ in range(N)])
    return np.vstack([standardize(nn[:, 0]), standardize(nn[:, 1])])


def record(T, noise_seed=None):
    """u = [s1, s2, n1, n2] for a record of T seconds (noise seed 7 + T, his)."""
    N = int(round(T * FS))
    t = np.arange(N) / FS
    imp = impacts(T)
    s = np.vstack([standardize(harmonic(t)), standardize(impact_train(t, imp))])
    n = noise(N, 7 + T if noise_seed is None else noise_seed)
    return dict(T=T, N=N, t=t, imp=imp, s=s, n=n, u=np.vstack([s, n]))


def sigma(snr):
    return math.sqrt(PMIN / 10 ** (snr / 10))


def augmented(sg):
    """x = Aug u: the sensors as a 2 x 4 matrix on [s1, s2, n1, n2]."""
    return np.hstack([A, sg * np.eye(2)])


# ------------------------------------------------------------------ shared pieces
def whitener(c11, c12, c22):
    """W with W C W' = I, rows the principal axes over their root eigenvalues
    (his convention: e1 = (c12, l1 - c11) normalized, e2 = e1 turned +90 deg)."""
    tr = (c11 + c22) / 2
    dd = math.sqrt(((c11 - c22) / 2) ** 2 + c12 ** 2)
    l1 = tr + dd
    l2 = max(tr - dd, 1e-9 * l1)
    if abs(c12) > 1e-15:
        e1 = np.array([c12, l1 - c11])
    else:
        e1 = np.array([1.0, 0.0]) if c11 >= c22 else np.array([0.0, 1.0])
    e1 = e1 / math.hypot(*e1)
    e2 = np.array([-e1[1], e1[0]])
    return np.array([e1 / math.sqrt(l1), e2 / math.sqrt(l2)])


def rot(th):
    """R(theta) = [[c, s], [-s, c]]: y = R z turns the cloud by -theta."""
    c, s = math.cos(th), math.sin(th)
    return np.array([[c, s], [-s, c]])


def wrap45(th):
    """theta modulo 90 degrees into [-45, 45) degrees (radians in and out)."""
    q = math.pi / 2
    return (th + math.pi / 4) % q - math.pi / 4


def corr(a, b):
    """Pearson correlation; 0 for an output the Wiener filter emptied (every gain 0)."""
    a = a - a.mean()
    b = b - b.mean()
    d = float(a @ a) * float(b @ b)
    return float(a @ b / math.sqrt(d)) if d > 0 else 0.0


def match(B):
    """Pair outputs with sources (G = B A): identity if |G11 G22| >= |G12 G21|,
    else swapped; the sign of each matched gain; SIR per output, the matched
    source's power over the other's (unit-variance sources): G_ij^2 / G_ik^2."""
    G = B @ A
    perm = [0, 1] if abs(G[0, 0] * G[1, 1]) >= abs(G[0, 1] * G[1, 0]) else [1, 0]
    sign = [1.0 if G[i, perm[i]] >= 0 else -1.0 for i in range(2)]
    sir = [10 * math.log10(G[i, perm[i]] ** 2 / max(G[i, 1 - perm[i]] ** 2, 1e-300)) for i in range(2)]
    # per source j: the output that carries it
    out = [perm.index(j) for j in range(2)]
    return dict(G=G, perm=perm, sign=sign, sir=sir, out=out,
                sir_src=[sir[out[j]] for j in range(2)])


def scores(y, s, m):
    """Correlation of each source with its matched output (sign removed)."""
    return [abs(corr(y[m["out"][j]], s[j])) for j in range(2)]


# ------------------------------------------------------------------ method 1
def moments4(z):
    z1, z2 = z
    return np.array([np.mean(z1 ** 4), np.mean(z1 ** 3 * z2), np.mean(z1 ** 2 * z2 ** 2),
                     np.mean(z1 * z2 ** 3), np.mean(z2 ** 4)])


def kurt_pair(m, th):
    """Excess kurtosis of y1 = c z1 + s z2 and y2 = -s z1 + c z2 (z white)."""
    c, s = np.cos(th), np.sin(th)
    k1 = c ** 4 * m[0] + 4 * c ** 3 * s * m[1] + 6 * c ** 2 * s ** 2 * m[2] + 4 * c * s ** 3 * m[3] + s ** 4 * m[4] - 3
    k2 = s ** 4 * m[0] - 4 * s ** 3 * c * m[1] + 6 * s ** 2 * c ** 2 * m[2] - 4 * s * c ** 3 * m[3] + c ** 4 * m[4] - 3
    return k1, k2


def kcrit(m, th):
    k1, k2 = kurt_pair(m, th)
    return np.abs(k1) + np.abs(k2)


def kurtosis_ica(x):
    """Method 1: centre, whiten, and turn to the largest |kurt y1| + |kurt y2|."""
    xc = x - x.mean(1, keepdims=True)
    C = xc @ xc.T / x.shape[1]
    W = whitener(C[0, 0], C[0, 1], C[1, 1])
    z = W @ xc
    m = moments4(z)
    th = maximize_k(m)
    return dict(W=W, z=z, m=m, theta=th, K=float(kcrit(m, th)), B=rot(th) @ W, C=C)


# ------------------------------------------------------------------ method 2
def hann(L):
    """His window: 0.5 - 0.5 cos(2 pi i / L), i = 0 .. L-1 (periodic Hann)."""
    return 0.5 - 0.5 * np.cos(2 * math.pi * np.arange(L) / L)


def welch(chs, L):
    """His Welch cross-spectra: Hann, 50% overlap, segments while o + L <= N,
    no scaling; S_ij[k] = mean over segments of conj(X_i) X_j, k = 0 .. L/2."""
    chs = np.atleast_2d(chs)
    N = chs.shape[1]
    w = hann(L)
    starts = list(range(0, N - L + 1, L // 2))
    X = np.array([[np.fft.rfft(c[o:o + L] * w) for o in starts] for c in chs])
    S = np.einsum("isk,jsk->ijk", np.conj(X), X) / len(starts)
    return S, len(starts)


def his_median(a):
    """His median: the element at floor(n / 2) of the sorted values."""
    b = np.sort(np.asarray(a))
    return float(b[len(b) // 2])


def jd_angle(Ds):
    """The one rotation that best diagonalizes every 2 x 2 symmetric D_k:
    theta in [-45, 45) deg minimizing J = sum_k (R D_k R')_12^2, in closed
    form; also G (J(theta) = v' G v, v = (cos 2 theta, sin 2 theta))."""
    h = np.array([[D[0, 1], (D[1, 1] - D[0, 0]) / 2] for D in Ds])
    G = h.T @ h
    ev, vec = np.linalg.eigh(G)
    v = vec[:, 0]
    return wrap45(0.5 * math.atan2(v[1], v[0])), G, ev


def jcurve(G, th):
    """J(theta) from G: (G11 + G22)/2 + (G11 - G22)/2 cos 4 theta + G12 sin 4 theta."""
    return (G[0, 0] + G[1, 1]) / 2 + (G[0, 0] - G[1, 1]) / 2 * np.cos(4 * th) + G[0, 1] * np.sin(4 * th)


def gain_apply(y, G, L):
    """His applyGain: zero-pad to the next power of two, scale each FFT bin by
    the gain interpolated linearly on the Welch bins, invert, keep N samples.
    Linear in y for a fixed gain."""
    N = len(y)
    N2 = 1 << (N - 1).bit_length()
    F = np.fft.fft(np.concatenate([y, np.zeros(N2 - N)]))
    k = np.arange(N2)
    kk = np.where(k <= N2 // 2, k, N2 - k)
    pos = kk * L / N2
    k0 = np.floor(pos).astype(int)
    k1 = np.minimum(k0 + 1, L // 2)
    g = G[k0] + (G[k1] - G[k0]) * (pos - k0)
    return np.fft.ifft(F * g).real[:N]


def sobi_family(x, T, turn90=False):
    """Method 2 on the sensors x of a T s record (his algorithm; the rotation exact).
    turn90: theta taken in [0, 90) deg rather than [-45, 45): a quarter turn more only
    swaps the outputs and one sign (the permutation no blind method can know)."""
    L = WELCH[T]
    H = L // 2 + 1
    S, K = welch(x, L)
    f1 = his_median(S[0, 0].real[1:])
    f2 = his_median(S[1, 1].real[1:])
    sd1, sd2 = f1 / math.sqrt(K), f2 / math.sqrt(K)
    a = S[0, 0].real[1:] - f1
    d = S[1, 1].real[1:] - f2
    b = S[0, 1].real[1:]
    ex = a / sd1 + d / sd2
    order = np.argsort(-ex, kind="stable")
    chosen = order[ex[order] > 4]
    if len(chosen) < 4:
        chosen = order[:4]
    sa, sb, sd = float(a[chosen].sum()), float(b[chosen].sum()), float(d[chosen].sum())
    sa, sd = max(sa, 1e-9), max(sd, 1e-9)
    if sa * sd - sb * sb <= 0:
        sb = math.copysign(0.95 * math.sqrt(sa * sd), sb)
    Msum = np.array([[sa, sb], [sb, sd]])
    W0 = whitener(sa, sb, sd)                 # W0 Msum W0' = I (Welch units)
    Ds = [W0 @ np.array([[a[k], b[k]], [b[k], d[k]]]) @ W0.T for k in chosen]
    th, G, ev = jd_angle(Ds)
    if turn90:
        th = th % (math.pi / 2)
    # the scale of a whitening is free: the page's z has unit RMS
    Cx = x @ x.T / x.shape[1]
    kz = math.sqrt(np.trace(W0 @ Cx @ W0.T) / 2)
    W = W0 / kz
    B = rot(th) @ W
    yraw = B @ x
    Sy, Ky = welch(yraw, L)
    over = 1 + 2 / math.sqrt(Ky)
    gains, nv = [], []
    idx = np.arange(H)
    for i in range(2):
        n_i = B[i, 0] ** 2 * f1 + B[i, 1] ** 2 * f2
        P = Sy[i, i].real
        g = np.maximum(0, P - over * n_i) / (P + 1e-30)
        gains.append((g[np.maximum(0, idx - 1)] + 2 * g + g[np.minimum(H - 1, idx + 1)]) / 4)
        nv.append(n_i)
    yden = np.array([gain_apply(yraw[i], gains[i], L) for i in range(2)])
    return dict(L=L, H=H, K=K, S=S, floors=(f1, f2), ex=ex, chosen=np.sort(chosen) + 1,
                Msum=Msum, W0=W0, kz=kz, W=W, Ds=Ds, theta=th, G=G, ev=ev, B=B,
                yraw=yraw, Sy=Sy, Ky=Ky, over=over, nv=nv, gains=gains, yden=yden)


def psd_db(S, L):
    """His Welch units to a one-sided PSD in dB re 1/Hz (signals in units of
    the sources' standard deviation): 2 S / (fs sum w^2), sum w^2 = 3L/8."""
    return 10 * np.log10(np.maximum(2 * np.asarray(S) / (FS * 3 * L / 8), 1e-30))


# ------------------------------------------------------------------ for the pages
def shown(a):
    """The first 4 s, every second sample (250 Hz): what the lanes and the
    scatter draw."""
    n = int(round(SHOW_T * FS))
    return np.asarray(a)[..., :n:DECIM]


def i8pack(rows):
    """Rows as int8 (each scaled to +-127 by its own largest value) and the scales."""
    import common
    rows = np.atleast_2d(rows)
    sc = [127.0 / max(float(np.abs(r).max()), 1e-12) for r in rows]
    return [common.i8(r * s) for r, s in zip(rows, sc)], sc


def kappa(M, u):
    """RMS of the two channels of M u: the one scale a stage is drawn in."""
    y = M @ u
    return math.sqrt(float(np.mean(y * y)))


LIB = r"""
/* ---- sp_bss shared: data, the stage clock, chips, lanes, scatter, table,
   controls (tools/numfig/sp_bss_lib.py); the figure's own script follows ---- */
const D = DATA, MINUS = '−';
const num = (v, d) => (Math.abs(v) < .5 * Math.pow(10, -d) ? 0 : v).toFixed(d).replace('-', MINUS);
const arrive = t0 => settle(t0, .28), rise = s => 5 * (1 - s);
function tw(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
const mw = (s, size) => math(s, 0, -1e4, {size, alpha: 0});
function sub(l, x, y, words, a) { panel(l, x, y, {alpha: a}); if (words) text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }
function mix(c1, c2, s) {
  const a = _hex(c1), b = _hex(c2), q = i => Math.round(lerp(a[i], b[i], clamp(s)));
  return '#' + [0, 1, 2].map(i => q(i).toString(16).padStart(2, '0')).join('');
}
/* u = [s1, s2, n1, n2] of each record: the first 4 s, every second sample */
const i8f = (s, sc) => Float64Array.from(b64i8(s), v => v / sc);
const RECS = D.recs.map(r => r.u.map((s, c) => i8f(s, r.sc[c])));
const NP = RECS[0][0].length, DT = D.dt;               // samples shown, their spacing (s)
function applyM(M, U) {                                 // a 2 x 4 matrix on u
  return [0, 1].map(i => { const m = M[i], o = new Float64Array(NP);
    for (let n = 0; n < NP; n++) o[n] = m[0] * U[0][n] + m[1] * U[1][n] + m[2] * U[2][n] + m[3] * U[3][n];
    return o; });
}
const rotM = th => [[Math.cos(th), Math.sin(th)], [-Math.sin(th), Math.cos(th)]];
const mul24 = (R, M) => [0, 1].map(i => M[0].map((_, j) => R[i][0] * M[0][j] + R[i][1] * M[1][j]));
function rotSig(th, Z) {                                // R(theta) z, sample by sample
  const c = Math.cos(th), s = Math.sin(th), a = new Float64Array(NP), b = new Float64Array(NP);
  for (let n = 0; n < NP; n++) { a[n] = c * Z[0][n] + s * Z[1][n]; b[n] = -s * Z[0][n] + c * Z[1][n]; }
  return [a, b];
}
function lerpSig(P, Q, e) {
  if (e >= 1) return Q; if (e <= 0) return P;
  return [0, 1].map(i => { const o = new Float64Array(NP); for (let n = 0; n < NP; n++) o[n] = P[i][n] + (Q[i][n] - P[i][n]) * e; return o; });
}

/* ------------------------------------------------------------ the stage clock
   Stage k of the tour holds [TOUR0 + k PER, TOUR0 + (k+1) PER); it arrives
   with its own motion in its first MORPH seconds (a rotation where the stage
   turns the cloud, otherwise a glide from the stage before). A stage the
   reader chooses starts at once: TOUR0 moves, and what was on the screen
   glides into it (JUMP). A new SNR or record glides the same way (CHG).
   Both are explicit state; draw() stays a function of the clock. */
const PER = 5.2, MORPH = 1.0, TOUR_START = 0;
let TOUR0 = TOUR_START, JUMP = null, CHG = null;
function clock() {
  const u = t - TOUR0;
  if (u < 0) return {k: 0, ph: 0, cyc: -1};
  const c = Math.floor(u / PER);
  return {k: c % NS, ph: u - c * PER, cyc: c};
}
/* the stage on screen: k, its phase, the stage it comes from, the progress
   of its own motion e and of a chosen stage's glide tr */
function where() {
  const c = clock();
  let from = (c.k + NS - 1) % NS, e = settle(TOUR0 + Math.max(c.cyc, 0) * PER, MORPH), tr = 1;
  if (c.cyc <= 0 && c.k === 0 && TOUR0 === TOUR_START) e = 1;            // the first stage: nothing before it
  if (JUMP && c.cyc === JUMP.cyc && c.k === JUMP.k) {
    from = JUMP.from; tr = settle(JUMP.t, .7);
    if (!TURNS[c.k]) e = 1;                                              // the glide is its motion
  }
  return {k: c.k, ph: c.ph, cyc: c.cyc, from, e, tr};
}
/* the cursor: the record shown plays once per stage, in real time */
const CUR0 = .6;
function cursor(w) {
  const tau = w.ph - CUR0, a = clamp(tau / .25) * clamp((D.show + .35 - tau) / .25);
  return {n: clamp(Math.floor(tau / DT), 0, NP - 1), tau: clamp(tau, 0, D.show), a: STILL ? 0 : a};
}

/* ------------------------------------------------------------ chips
   chip(): engine uiChip's look (white, grey edge; chosen navy with white
   type; hover steel; pressed steel2), with a word and a symbol in math */
function chip(x, y, w, h, words, sym, st = {}, a = 1) {
  const fill = st.on ? C.navy : st.down ? C.steel2 : st.hover ? C.steel : '#fff';
  const edge = st.on || st.hover || st.down ? C.navy : C.guide;
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], {color: edge, width: 1, fill, close: true, alpha: a});
  const col = st.on ? '#fff' : st.hover ? C.ink : C.body, size = 15;
  const w1 = words ? tw(words, size) : 0, w2 = sym ? mw(sym, size) : 0, gap = words && sym ? 4 : 0;
  const x0 = x + (w - w1 - gap - w2) / 2, yb = y + h / 2 + 5;
  if (words) text(words, x0, yb, {size, color: col, alpha: a});
  if (sym) math(sym, x0 + w1 + gap, yb, {size, color: col, alpha: a});
}
function chipW(words, sym) { return (words ? tw(words, 15) : 0) + (sym ? mw(sym, 15) + 4 : 0) + 22; }

/* ------------------------------------------------------------ lanes
   two stacked axes over the 4 s shown; y in units of the stage's RMS */
const YL = 5.4;
function lanes(L, sig, o) {
  const xt = [0, 1, 2, 3, 4];
  const out = [];
  for (let i = 0; i < 2; i++) {
    const y0 = L.y + i * (L.h + L.gap);
    const ax = axes({x: L.x, y: y0, w: L.w, h: L.h, xlim: [0, D.show], ylim: [-YL, YL], xticks: xt, yticks: [-4, 0, 4],
      xfmt: i ? fmt : () => '', tickSize: 16, labelSize: 17, progress: o.p});
    out.push(ax);
    ax.inside(() => {
      line([[L.x, ax.Y(0)], [L.x + L.w, ax.Y(0)]], {color: C.rule, width: 1, alpha: o.p});
      const pts = new Array(NP);
      for (let n = 0; n < NP; n++) pts[n] = [ax.X(n * DT), ax.Y(sig[i][n])];
      line(pts, {color: o.color, width: 1.35, progress: o.draw});
      if (o.ov && o.ov.a > .01) {
        const q = o.ov.sig[i], ov = new Array(NP);
        for (let n = 0; n < NP; n++) ov[n] = [ax.X(n * DT), ax.Y(q[n])];
        line(ov, {color: C.navy, width: 1.3, dash: [5, 3.5], alpha: o.ov.a});
      }
      if (o.cur && o.cur.a > 0) line([[ax.X(o.cur.tau), y0], [ax.X(o.cur.tau), y0 + L.h]], {color: C.ink, width: 1, alpha: .45 * o.cur.a});
    });
  }
  return out;
}
/* a symbol that changes with the stage: the old one leaves before the new one comes */
function swap(e) { return [clamp(1 - 2.2 * e), clamp(2.2 * e - 1.2)]; }
function ylab(s, x, y, a) { if (a > .01) math(s, x, y, {size: 18, align: 'center', rot: -Math.PI / 2, alpha: a}); }

/* ------------------------------------------------------------ scatter
   the joint scatter of the two channels, drawn as the point cloud itself,
   with the images of the two source axes (the signal columns of the stage's
   matrix) as arrows */
function scatter(S, sig, o) {
  const ax = axes({x: S.x, y: S.y, w: S.s, h: S.s, xlim: [-YL, YL], ylim: [-YL, YL], xticks: [-4, 0, 4], yticks: [-4, 0, 4],
    tickSize: 16, progress: o.p});
  ax.inside(() => {
    line([[S.x, ax.Y(0)], [S.x + S.s, ax.Y(0)]], {color: C.rule, width: 1, alpha: o.p});
    line([[ax.X(0), S.y], [ax.X(0), S.y + S.s]], {color: C.rule, width: 1, alpha: o.p});
    ctx.save(); ctx.globalAlpha *= .42 * o.pts; ctx.fillStyle = C.blue;
    for (let n = 0; n < NP; n++) ctx.fillRect(ax.X(sig[0][n]) - 1.3, ax.Y(sig[1][n]) - 1.3, 2.6, 2.6);
    ctx.restore();
  });
  return ax;
}
function sourceArrows(ax, cols, a, len) {
  if (a <= .01) return;
  for (let j = 0; j < 2; j++) {
    const vx = cols[j][0] * len, vy = cols[j][1] * len, L = Math.hypot(vx, vy);
    if (L < 1e-6) continue;
    arrow(ax.X(0), ax.Y(0), ax.X(vx), ax.Y(vy), {color: C.ink, width: 1.6, head: 10, alpha: a});
  }
  for (let j = 0; j < 2; j++) {                         // their labels after both strokes, on a knockout
    const vx = cols[j][0] * len, vy = cols[j][1] * len, L = Math.hypot(vx, vy);
    if (L < 1e-6) continue;
    const s = 's_' + (j + 1), X = ax.X(vx + vx / L * .62), Y = ax.Y(vy + vy / L * .62) + 6, wd = mw(s, 17);
    ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(X - wd / 2 - 3, Y - 15, wd + 6, 20); ctx.restore();
    math(s, X, Y, {size: 17, align: 'center', alpha: a});
  }
}

/* ------------------------------------------------------------ table
   booktabs: a 1.3 rule above and below, 0.8 under the head */
function rule(x0, x1, y, w, a) { line([[x0, y], [x1, y]], {color: C.ink, width: w, alpha: a}); }
/* a line of words and maths: [['t', words], ['m', maths], ...] (maths turns '-' into a minus sign, words keep it) */
function mixed(parts, x, y, o) { let w = 0; for (const [k, s] of parts) w += k === 'm' ? math(s, x + w, y, o) : text(s, x + w, y, o); return w; }

/* ------------------------------------------------------------ the reader's hand
   chips are drawn on the canvas; each has a transparent button over it for
   the keyboard and the pointer (a radio in its group). A click on a chip or
   just beside it never pauses the figure. */
const FIG = cv.closest('.fig'), HOV = {}, DOWN = {}, GROUPS = [];
function redraw() { if (!playing) render(); }
function group(name, label, items, get, set) {
  const g = {name, items, get, set, buttons: []};
  GROUPS.push(g);
  if (STILL) return g;
  const box = document.createElement('div');
  box.setAttribute('role', 'radiogroup'); box.setAttribute('aria-label', label);
  box.style.cssText = 'position:absolute;inset:0;pointer-events:none';
  items.forEach((it, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'nfb'; b.setAttribute('role', 'radio'); b.setAttribute('aria-label', it.aria);
    b.addEventListener('click', ev => { ev.stopPropagation(); set(i); sync(); });
    b.addEventListener('keydown', ev => {
      const n = items.length, d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[ev.key];
      const j = ev.key === 'Home' ? 0 : ev.key === 'End' ? n - 1 : d ? (get() + d + n) % n : -1;
      if (j < 0) return;
      ev.preventDefault(); set(j); sync(); g.buttons[j].focus();
    });
    b.addEventListener('pointerenter', () => { HOV[name] = i; redraw(); });
    b.addEventListener('pointerleave', () => { if (HOV[name] === i) HOV[name] = -1; DOWN[name] = -1; redraw(); });
    b.addEventListener('pointerdown', () => { DOWN[name] = i; redraw(); });
    b.addEventListener('pointerup', () => { DOWN[name] = -1; redraw(); });
    b.addEventListener('pointercancel', () => { HOV[name] = -1; DOWN[name] = -1; redraw(); });
    box.appendChild(b); g.buttons.push(b);
  });
  FIG.insertBefore(box, FIG.querySelector('.ctl'));
  return g;
}
function place(g, rects) {                              // each button over its chip, its hit area padded
  if (STILL) return;
  rects.forEach((r, i) => {
    const b = g.buttons[i]; if (!b) return;
    b.style.left = r[0] / W * 100 + '%'; b.style.top = r[1] / H * 100 + '%';
    b.style.width = r[2] / W * 100 + '%'; b.style.height = r[3] / H * 100 + '%';
  });
}
let said = null;
function sync() {
  for (const g of GROUPS) g.buttons.forEach((b, i) => { b.setAttribute('aria-checked', String(i === g.get())); b.tabIndex = i === g.get() ? 0 : -1; });
  if (said && typeof status === 'function') said.textContent = status();
}
const BANDS = [];                                       // [x0, y0, x1, y1]: clicks there are the controls'
if (!STILL) {
  document.head.insertAdjacentHTML('beforeend', '<style>.nfb{position:absolute;pointer-events:auto;box-sizing:border-box;margin:0;padding:0;' +
    'border:0;background:transparent;color:transparent;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.nfb:focus{outline:none}.nfb:focus-visible{outline:2px solid #095A94;outline-offset:-3px}</style>');
  said = document.createElement('div'); said.setAttribute('role', 'status');
  said.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;pointer-events:none';
  FIG.appendChild(said);
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), X = (e.clientX - r.left) * W / r.width, Y = (e.clientY - r.top) * H / r.height;
    if (BANDS.some(b => X >= b[0] && X <= b[2] && Y >= b[1] && Y <= b[3])) e.stopPropagation();
  }, true);
}
/* a chosen stage: it starts now and what is on the screen glides into it;
   paused (or less motion), the stage is shown complete */
function chooseStage(j) {
  const w = where();
  if (playing && !REDUCED) {
    const snap = snapNow();                              // the figure's view on the screen now
    TOUR0 = t - j * PER;
    JUMP = {k: j, cyc: clock().cyc, from: w.k, t, snap};
  } else { TOUR0 = t - j * PER - 2.6; JUMP = null; }
  CHG = null; render();
}
/* a new SNR or record: the cloud and the traces glide to the new numbers */
function chooseData(f) {
  const snap = playing && !REDUCED ? snapNow() : null;
  f(); ENDS = null;
  CHG = snap ? {t, snap} : null;
  render();
}
let ENDS = null;
/* query: ?snr=<dB>&len=<s>&stage=<1..> preselect a state (for the checks);
   nothing happens without them */
const Q = new URLSearchParams(location.search);
"""


# ------------------------------------------------------------------ checks shared by both figures
def maximize_k(m):
    """The rotation of white data with fourth moments m that maximizes K."""
    from scipy.optimize import minimize_scalar
    grid = np.deg2rad(np.arange(-45, 45, 0.01))
    g0 = grid[int(np.argmax(kcrit(m, grid)))]
    h = np.deg2rad(0.011)
    r = minimize_scalar(lambda th: -kcrit(m, th), bounds=(g0 - h, g0 + h), method="bounded",
                        options=dict(xatol=1e-13))
    return wrap45(float(r.x))


def his_whitener_m1(c11, c12, c22):
    """His method 1 page's whitener (l2 without a floor, e1 = (1, 0) when c12 ~ 0)."""
    tr = (c11 + c22) / 2
    dd = math.sqrt(((c11 - c22) / 2) ** 2 + c12 ** 2)
    l1, l2 = tr + dd, tr - dd
    e1 = np.array([c12, l1 - c11]) if abs(c12) > 1e-12 else np.array([1.0, 0.0])
    e1 = e1 / math.hypot(*e1)
    e2 = np.array([-e1[1], e1[0]])
    return np.array([e1 / math.sqrt(l1), e2 / math.sqrt(l2)])


def his_kica_grid(u, Aug, step, centre=True, m1=False):
    """His kurtosis ICA as his pages run it: whitening, then the first maximum
    of |kurt y1| + |kurt y2| on a grid of `step` degrees from -45 to 45."""
    x = Aug @ u
    xc = x - x.mean(1, keepdims=True) if centre else x
    C = xc @ xc.T / x.shape[1]
    W = (his_whitener_m1 if m1 else whitener)(C[0, 0], C[0, 1], C[1, 1])
    WAug = W @ Aug
    z = WAug @ u
    best, bk, d = 0.0, -1.0, -45.0
    while d <= 45:
        th = d * math.pi / 180
        c, s = math.cos(th), math.sin(th)
        a, b = c * z[0] + s * z[1], -s * z[0] + c * z[1]
        k = abs(np.mean(a ** 4) - 3) + abs(np.mean(b ** 4) - 3)
        if k > bk:
            bk, best = k, th
        d += step
    return W, best, rot(best) @ WAug


def his_match(F):
    """His pages' pairing: each output to the source with the larger |gain|."""
    out = []
    for i in range(2):
        j = 0 if abs(F[i][0]) > abs(F[i][1]) else 1
        out.append((j, math.copysign(1.0, F[i][j]) if F[i][j] != 0 else 1.0))
    return out


def his_page(path, actions, read, wait=250):
    """Open one of his pages headless, do each action (JS) and read the
    readout after it: a list of strings."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 1400})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + path)
        pg.wait_for_timeout(600)
        for act in actions:
            pg.evaluate(act)
            pg.wait_for_timeout(wait)
            out.append(pg.evaluate(read))
        b.close()
    if errs:
        raise RuntimeError(f"{path}: script errors {errs}")
    return out


def _serve(name):
    import shutil
    import tempfile
    import threading
    import common
    tmp = tempfile.mkdtemp(prefix="numfig-")
    import os
    os.makedirs(os.path.join(tmp, "anim"))
    shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
    shutil.copy(os.path.join(common.ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
    srv = common._server(tmp)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return tmp, srv


def check_states(name, queries, times, width=672):
    """The engine's overlap check (?overlap) in every state a reader can reach:
    the page is opened once per query (?still&overlap&<query>) and drawn at
    each moment in `times`. Returns (faults, moments checked, script errors)."""
    import shutil
    from playwright.sync_api import sync_playwright
    tmp, srv = _serve(name)
    faults, n, errs = [], 0, []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            for q in queries:
                pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still&overlap&{q}")
                pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
                for t in ["still"] + list(times):
                    if t != "still":
                        pg.evaluate(f"() => {{ t = {t:.6g}; render(); }}")
                    lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                    n += 1
                    for a in lab:
                        faults.append(f"{q} t={t}: labels {a[0]!r} and {a[1]!r} meet at ({a[2]}, {a[3]})")
                    for c in cro:
                        faults.append(f"{q} t={t}: a stroke crosses {c[0]!r} at ({c[1]}, {c[2]})")
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return faults, n, errs


def page_eval(name, query, exprs):
    """Evaluate JavaScript expressions in nf-<name>.html opened as a still."""
    import shutil
    from playwright.sync_api import sync_playwright
    tmp, srv = _serve(name)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still&{query}")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            out = [pg.evaluate(e) for e in exprs]
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    if errs:
        raise RuntimeError(f"nf-{name}: script errors {errs}")
    return out


def interact(name, steps, width=672):
    """Drive the page as a reader does (not a still): each step is (what, JS
    to run in the page, JS that must be true afterwards, wait ms). Returns
    the failures, the console errors and the intro's end state."""
    import shutil
    from playwright.sync_api import sync_playwright
    tmp, srv = _serve(name)
    fails, errs = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1100})
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            for what, act, ok, wait in steps:
                if act.startswith("click:"):
                    pg.locator(act[6:]).click()
                elif act.startswith("key:"):
                    pg.keyboard.press(act[4:])
                elif act:
                    pg.evaluate(act)
                pg.wait_for_timeout(wait)
                if ok and not pg.evaluate(ok):
                    fails.append(what)
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return fails, errs


def check_glides(name, actions, width=672):
    """The overlap check through the glides a reader starts: each action (a
    stage chosen, chooseStage(j), or new numbers, chooseData(...)) is taken
    while playing at moment t0, then the glide is drawn at 11 moments over
    1.2 s. Returns (frames drawn, faults)."""
    import shutil
    from playwright.sync_api import sync_playwright
    tmp, srv = _serve(name)
    faults, n, errs = [], 0, []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?overlap")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            for t0, act in actions:
                pg.evaluate(f"() => {{ setPlay(true); t = {t0}; render(); {act}; setPlay(false); }}")
                tc = pg.evaluate("t")
                for dt in (0.02, 0.06, 0.1, 0.15, 0.2, 0.3, 0.4, 0.55, 0.7, 0.9, 1.2):
                    pg.evaluate(f"() => {{ t = {tc + dt}; render(); }}")
                    lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                    n += 1
                    faults += [f"{act} at t={t0}+{dt}: labels {a[0]!r}, {a[1]!r}" for a in lab]
                    faults += [f"{act} at t={t0}+{dt}: a stroke crosses {c[0]!r}" for c in cro]
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return n, faults + [f"script error: {e}" for e in errs]
