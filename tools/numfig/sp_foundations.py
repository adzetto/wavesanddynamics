"""The cover of the signal processing document: different problems, shared
inference and fitting tools.

His animation (Shared_Foundations_Animation_DSP_SI_section.html, "Different
problems · shared inference and fitting tools") sets three problems in a row,
signal processing, system identification and machine learning, over the two
foundations they share, estimation theory and optimization: estimation links
them by statistical inference, optimization by numerical fitting, and the two
foundations hand each other a criterion and a solution. Each of his nodes
holds a small animated plot. The redraw keeps his nodes, his links and his
words, as TikZ draws a diagram: thin frames; his six links (each foundation to
each problem, crossing in his figure) as one line that both foundations feed,
labelled where each joins it, with an arrow on into each problem; the
criterion one way between the foundations and the solution the other; his
grey line along the top row as dashed links. In each node a small example is
computed, not drawn by hand, and all five run on one clock, each converging
as it gets data or iterations:

  Signal processing: an adaptive line enhancer. Two sinusoids in white noise;
      an FIR predictor of M taps, updated by NLMS from w = 0, predicts each
      sample from the ones before it; what it can predict is the signal, so
      its output is the cleaned signal, drawn sample by sample.
  System identification: the resonator of Figure 1 (sp_model, f_n = 1 Hz,
      zeta = 0.1) sampled at 8 Hz, its first M taps (as Figure 2's unknown
      system), driven by white noise and measured with noise; the least
      squares FIR estimate from the first N samples, N growing.
  Machine learning: kernel ridge regression (an RBF kernel; the posterior
      mean of a Gaussian process) of noisy samples of sin(2 pi x), the
      points arriving one by one.
  Estimation theory: the unknown mean of Gaussian data with known spread,
      a normal prior; the conjugate normal posterior, its mean and 95%
      interval, after each datum.
  Optimization: gradient descent with a fixed step on the least squares
      objective of a straight line fitted to 30 points, a quadratic whose
      contours are ellipses; the iterates zigzag down to the normal
      equations' solution.

Run: python tools/numfig/sp_foundations.py [--look]  (writes the page, the
still and tools/numfig/sp_foundations.check.txt; prints the key numbers;
--look also writes frames to the temp directory)
"""
import os
import sys

import numpy as np

import common
import sp_model as SM

NAME = "sp-foundations"
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ the page's clock (s)
T0, RUN, HOLD, BACK, REST = 0.55, 5.6, 2.2, 0.8, 0.3

# ------------------------------------------------------------------ signal processing: an ALE
SP_N = 240                 # samples drawn
SP_P = (30.0, 11.7)        # periods of the two sinusoids (samples)
SP_A = (1.0, 0.6)          # their amplitudes
SP_PH = (0.0, 0.7)         # their phases (rad)
SP_SIG = 0.35              # noise standard deviation
SP_M, SP_D = 96, 1         # predictor taps, prediction delay (samples)
SP_MU = 0.15               # NLMS step
SP_SEED = 3
SP_RUNS = 400              # runs for the ensemble checks (seeds 1000 on)
SP_LONG = 2000             # their length: the filter in steady state

# ------------------------------------------------------------------ system identification
SI_FS, SI_M = 8.0, 24      # sampling (Hz), taps (3 s of the resonator)
SI_SNR = 5.0               # output to measurement noise (dB)
SI_NS = np.unique(np.round(np.geomspace(30, 3000, 18)).astype(int))   # the data lengths shown
SI_SEED = 7
SI_MC = 2000               # noise realisations for the error check

# ------------------------------------------------------------------ machine learning
ML_N = 20                  # points
ML_SIG = 0.2               # noise standard deviation
ML_ELL, ML_LAM = 0.14, 0.04   # RBF length scale; ridge = noise variance / signal variance
ML_G = 101                 # grid the fits are drawn on

# ------------------------------------------------------------------ estimation theory
EST_MU0, EST_TAU0 = -1.0, 0.8   # prior N(mu0, tau0^2)
EST_TH, EST_SIG = 0.7, 1.0      # the true mean, the data's known standard deviation
EST_N = 20
EST_SEED = 1
EST_MC = 100000                 # repetitions for the calibration check
EST_LIM = (-3.0, 3.2)           # the parameter axis drawn

# ------------------------------------------------------------------ optimization
OPT_N = 30                 # points of the line fit
OPT_X = (-3.0, 5.4)        # their abscissae, uniform
OPT_AB = (0.8, 0.5)        # the line they scatter about
OPT_NOISE = 0.3
OPT_SEED = 1
OPT_ETA = 1.6              # step, times 1 / lambda_max
OPT_K = 28                 # iterations drawn
OPT_D0 = (2.2, 0.5)        # the start, from the minimum, along the shallow and the steep axes
OPT_LEVELS = 6             # contours, geometric from 1.25 J(w0) down by OPT_Q
OPT_Q = 0.42


# ================================================================== the five models
def sp_signals(seed, N=SP_N):
    """The clean signal s, the noisy input x (from n = -(M + D)), as floats."""
    rng = np.random.default_rng(seed)
    n = np.arange(-(SP_M + SP_D), N)
    s = sum(a * np.sin(2 * np.pi * n / p + ph) for a, p, ph in zip(SP_A, SP_P, SP_PH))
    x = s + SP_SIG * rng.standard_normal(len(n))
    return n, s, x


def sp_ale(x, N=SP_N):
    """NLMS adaptive line enhancer: y(n) = w(n)^T [x(n-D) ... x(n-D-M+1)], from w = 0;
    returns the outputs for n = 0 .. N-1 and the weights after each update."""
    off = SP_M + SP_D
    w = np.zeros(SP_M)
    y = np.zeros(N)
    ws = np.zeros((N + 1, SP_M))
    for k in range(N):
        i = k + off
        u = x[i - SP_D - SP_M + 1:i - SP_D + 1][::-1]
        y[k] = w @ u
        e = x[i] - y[k]
        w = w + SP_MU * e * u / (1e-9 + u @ u)
        ws[k + 1] = w
    return y, ws


def sp_wiener():
    """The Wiener-Hopf solution R w = p from the exact autocorrelation of the input
    r(k) = sum a^2/2 cos(2 pi k / P) + sigma^2 delta(k), p_j = r(j + D); and the MMSE of
    estimating s(n) by w^T u: sigma_s^2 - p^T R^-1 p."""
    k = np.arange(SP_M + SP_D + 1)
    rs = sum(a * a / 2 * np.cos(2 * np.pi * k / p) for a, p in zip(SP_A, SP_P))
    r = rs + SP_SIG ** 2 * (k == 0)
    R = np.array([[r[abs(i - j)] for j in range(SP_M)] for i in range(SP_M)])
    pv = rs[SP_D:SP_D + SP_M]
    wo = np.linalg.solve(R, pv)
    jmin_s = rs[0] - pv @ wo
    return wo, jmin_s, R, pv


def sp_model():
    n, s, x = sp_signals(SP_SEED)
    y, ws = sp_ale(x)
    off = SP_M + SP_D
    return dict(n=n[off:], s=s[off:], x=x[off:], y=y, ws=ws)


def si_h():
    wn = 2 * np.pi * SM.FN
    wd = wn * np.sqrt(1 - SM.ZETA ** 2)
    r, th = np.exp(-SM.ZETA * wn / SI_FS), wd / SI_FS
    k = np.arange(SI_M)
    return r ** k * np.sin(k * th), r, th


def si_regressors(u, n_rows):
    """Rows [u(n), u(n-1), ..., u(n-M+1)] for n = M-1 .. M-1+n_rows-1."""
    return np.array([u[n - np.arange(SI_M)] for n in range(SI_M - 1, SI_M - 1 + n_rows)])


def si_model():
    h, r, th = si_h()
    rng = np.random.default_rng(SI_SEED)
    nmax = int(SI_NS[-1])
    u = rng.standard_normal(nmax + SI_M)
    y0 = np.convolve(u, h)[:nmax + SI_M]
    sig = np.sqrt(np.mean(y0[SI_M - 1:] ** 2)) * 10 ** (-SI_SNR / 20)
    y = y0 + sig * rng.standard_normal(len(y0))
    U = si_regressors(u, nmax)
    Y = y[SI_M - 1:SI_M - 1 + nmax]
    est = [np.linalg.lstsq(U[:N], Y[:N], rcond=None)[0] for N in SI_NS]
    return dict(h=h, r=r, th=th, u=u, y=y, y0=y0, sig=sig, U=U, Y=Y, est=np.array(est))


def ml_f(x):
    return np.sin(2 * np.pi * x)


def ml_draw(seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0.02, 0.98, ML_N)
    y = ml_f(x) + ML_SIG * rng.standard_normal(ML_N)
    return x, y


def ml_fit(x, y, xg):
    """Kernel ridge regression: f(x) = k(x)^T (K + lam I)^-1 y, k(a, b) = exp(-(a - b)^2 / (2 ell^2))."""
    if len(x) == 0:
        return np.zeros_like(xg)
    K = np.exp(-(x[:, None] - x[None, :]) ** 2 / (2 * ML_ELL ** 2))
    a = np.linalg.solve(K + ML_LAM * np.eye(len(x)), y)
    return np.exp(-(xg[:, None] - x[None, :]) ** 2 / (2 * ML_ELL ** 2)) @ a


def ml_seed():
    """The first seed from 1 whose points leave no gap wider than 0.12 in [0, 1] once
    all have arrived and whose fit improves steadily: the error of the fit to
    sin(2 pi x) after n points never rises by more than 0.03 from one n to the next."""
    xg = np.linspace(0, 1, ML_G)
    for seed in range(1, 500):
        x, y = ml_draw(seed)
        xs = np.sort(np.r_[0.0, x, 1.0])
        rm = [np.sqrt(np.mean((ml_fit(x[:n], y[:n], xg) - ml_f(xg)) ** 2)) for n in range(ML_N + 1)]
        if np.diff(xs).max() <= 0.12 and np.diff(rm).max() <= 0.03:
            return seed, rm
    raise RuntimeError("no seed")


def ml_model():
    seed, rm = ml_seed()
    x, y = ml_draw(seed)
    xg = np.linspace(0, 1, ML_G)
    fits = np.array([ml_fit(x[:n], y[:n], xg) for n in range(ML_N + 1)])
    return dict(seed=seed, x=x, y=y, xg=xg, fits=fits, rmse=np.array(rm))


def est_post(x, mu0=EST_MU0, tau0=EST_TAU0, sig=EST_SIG):
    """The conjugate normal posterior after each of the first n data, n = 0 .. len(x)."""
    n = np.arange(len(x) + 1)
    S = np.r_[0.0, np.cumsum(x)]
    tau2 = 1 / (1 / tau0 ** 2 + n / sig ** 2)
    return tau2 * (mu0 / tau0 ** 2 + S / sig ** 2), np.sqrt(tau2)


def est_model():
    rng = np.random.default_rng(EST_SEED)
    x = EST_TH + EST_SIG * rng.standard_normal(EST_N)
    mu, tau = est_post(x)
    return dict(x=x, mu=mu, tau=tau)


def opt_model():
    rng = np.random.default_rng(OPT_SEED)
    xd = rng.uniform(*OPT_X, OPT_N)
    yd = OPT_AB[0] + OPT_AB[1] * xd + OPT_NOISE * rng.standard_normal(OPT_N)
    X = np.c_[np.ones(OPT_N), xd]
    Hm = X.T @ X / OPT_N                     # J(w) = |X w - y|^2 / (2 N): its Hessian
    g0 = X.T @ yd / OPT_N
    ws = np.linalg.solve(Hm, g0)
    J = lambda w: np.sum((X @ w - yd) ** 2) / (2 * OPT_N)
    lam, V = np.linalg.eigh(Hm)              # lam[0] shallow, lam[1] steep
    if V[0, 0] < 0:
        V[:, 0] = -V[:, 0]
    if V[1, 1] < 0:
        V[:, 1] = -V[:, 1]
    eta = OPT_ETA / lam[1]
    w = ws - OPT_D0[0] * V[:, 0] + OPT_D0[1] * V[:, 1]      # up the valley, a little up the wall
    path = [w.copy()]
    for _ in range(OPT_K):
        w = w - eta * (Hm @ w - g0)
        path.append(w.copy())
    path = np.array(path)
    c0 = J(path[0]) - J(ws)
    levels = 1.25 * c0 * OPT_Q ** np.arange(OPT_LEVELS)
    return dict(xd=xd, yd=yd, X=X, H=Hm, g0=g0, ws=ws, J=J, lam=lam, V=V, eta=eta, path=path,
                levels=levels, c0=c0)


# ================================================================== the page
JS = r"""
const D = DATA, CK = D.clock;
const NARROW = () => (cv.clientWidth || W) < 480;     // a phone: titles larger, the small words left out
const KW = () => NARROW() ? 1.7 : 1;                   // stroke widths, times
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);

/* ------------------------------------------------------------ the clock
   One loop for the five examples: from T0 each takes its steps over RUN s
   (a datum, an estimate or an iteration per step, each a Motion spring
   glide), holds, glides home and starts again. */
const T0 = CK.t0, RUN = CK.run, HOLD = CK.hold, BACK = CK.back, REST = CK.rest;
const PER = RUN + HOLD + BACK + REST;
const POSTER_T = T0 + RUN + 1.0;
function loopAt() {
  if (t < T0) return { u: -1, b0: T0 };
  const c = Math.floor((t - T0) / PER);
  return { u: t - T0 - c * PER, b0: T0 + c * PER };
}
/* an example of n steps: k steps taken (0..n), s the glide into the k-th,
   back the glide home, a the alpha of what it leaves behind */
function stepper(n) {
  const L = loopAt(), dt = RUN / n;
  if (L.u < 0) return { k: 0, s: 1, back: 0, a: 1, b0: L.b0, dt };
  if (L.u < RUN) {
    const k = Math.min(n, Math.floor(L.u / dt) + 1);
    return { k, s: settle(L.b0 + (k - 1) * dt, Math.min(.22, .8 * dt)), back: 0, a: 1, b0: L.b0, dt };
  }
  if (L.u < RUN + HOLD) return { k: n, s: 1, back: 0, a: 1, b0: L.b0, dt };
  const tb = L.b0 + RUN + HOLD;
  return { k: n, s: 1, back: settle(tb, BACK * .8), a: 1 - seg(tb, .4), b0: L.b0, dt };
}
/* the value of state k glided from state k - 1, then home to state 0 */
const glide = (S, st, i) => {
  const v = st.k > 0 ? lerp(S(st.k - 1, i), S(st.k, i), st.s) : S(0, i);
  return lerp(v, S(0, i), st.back);
};
/* the newest thing's alpha as it arrives (j from 1) */
const arrive = (st, j) => j < st.k ? st.a : j === st.k ? st.a * settle(st.b0 + (j - 1) * st.dt, .2) : 0;
function clip(r, f) { ctx.save(); ctx.beginPath(); ctx.rect(r.x, r.y, r.w, r.h); ctx.clip(); f(); ctx.restore(); }

/* ------------------------------------------------------------ layout */
const NW = 290, NH = 190, TOPY = 7, BOTY = 263, BUS = 221;
const XT = [167, 500, 833], XF = [300, 700];          // centres of the problems, of the foundations
const XR = [XF[0] - NW / 2 + 60, XF[1] + NW / 2 - 60]; // where the foundations' links leave them
const NODES = [
  { cx: XT[0], y: TOPY, title: 'Signal processing', sub: ['estimate signals', 'adapt filter coefficients'], plot: plotSP },
  { cx: XT[1], y: TOPY, title: 'System identification', sub: ['infer dynamic models', 'estimate system parameters'], plot: plotSI },
  { cx: XT[2], y: TOPY, title: 'Machine learning', sub: ['learn representations', 'and predictive mappings'], plot: plotML },
  { cx: XF[0], y: BOTY, title: 'Estimation theory', sub: ['unknowns, noise, priors', 'estimates, uncertainty'], plot: plotEST },
  { cx: XF[1], y: BOTY, title: 'Optimization', sub: ['objective, constraints', 'compute a solution'], plot: plotOPT },
];
const plotRect = n => NARROW() ? { x: n.cx - NW / 2 + 12, y: n.y + 50, w: NW - 24, h: 128 }
                               : { x: n.cx - NW / 2 + 16, y: n.y + 43, w: NW - 32, h: 92 };

/* ------------------------------------------------------------ signal processing */
const SP = D.sp, SPX = b64f32(SP.x), SPY = b64f32(SP.y);
function penAt() {                                    // samples the filter has put out, the trace's alpha
  const L = loopAt();
  if (L.u < 0) return { n: 0, a: 1 };
  if (L.u < RUN) return { n: SP.n * L.u / RUN, a: 1 };
  if (L.u < RUN + HOLD) return { n: SP.n, a: 1 };
  return { n: SP.n, a: 1 - seg(L.b0 + RUN + HOLD, .5) };
}
function plotSP(r, i0) {
  const N = SP.n, X = i => r.x + 5 + i * (r.w - 10) / (N - 1), Y = v => r.y + r.h / 2 - v * (r.h / 2 - 3) / SP.amp;
  const pen = penAt();
  clip(r, () => {
    line([[r.x, Y(0)], [r.x + r.w, Y(0)]], { color: C.rule, width: 1, alpha: seg(i0 + .1, .3) });
    line(Array.from(SPX, (v, i) => [X(i), Y(v)]), { color: C.mist, width: 1.25 * KW(), progress: seg(i0 + .08, .45) });
    if (pen.n <= 0 || pen.a <= 0) return;
    const n0 = Math.min(N - 1, Math.floor(pen.n)), pts = [];
    for (let i = 0; i <= n0; i++) pts.push([X(i), Y(SPY[i])]);
    const f = pen.n - n0;
    if (n0 < N - 1 && f > 0) pts.push([X(n0 + f), Y(lerp(SPY[n0], SPY[n0 + 1], f))]);
    if (pts.length > 1) line(pts, { color: C.navy, width: 2 * KW(), alpha: pen.a });
    const e = pts[pts.length - 1];
    dot(e[0], e[1], 3.4 * Math.sqrt(KW()), { color: '#fff', fill: C.accent, width: 1.1, alpha: pen.a });
  });
}

/* ------------------------------------------------------------ system identification */
const SI = D.si, NSI = SI.ns.length;                  // states: 0 (no data), then the estimate from N_j samples
const siState = (k, i) => k === 0 ? 0 : SI.est[k - 1][i];
function plotSI(r, i0) {
  const M = SI.m, X = k => r.x + 9 + k * (r.w - 18) / (M - 1), y0 = r.y + r.h * .56, Y = v => y0 - v * (r.h * .56 - 5) / SI.amp;
  const st = stepper(NSI), ga = seg(i0 + .12, .3), sa = seg(i0 + .18, .3);
  clip(r, () => {
    line([[r.x, y0], [r.x + r.w, y0]], { color: C.rule, width: 1, alpha: seg(i0 + .1, .3) });
    for (let k = 0; k < M; k++) dot(X(k), Y(SI.h[k]), 2.5 * Math.sqrt(KW()), { color: C.guide, fill: '#fff', width: 1, alpha: ga });
    if (sa <= 0) return;
    ctx.save(); ctx.globalAlpha *= sa; ctx.strokeStyle = C.navy; ctx.lineWidth = 1.3 * KW(); ctx.beginPath();
    const v = []; for (let k = 0; k < M; k++) v.push(glide(siState, st, k));
    for (let k = 0; k < M; k++) { ctx.moveTo(X(k), y0); ctx.lineTo(X(k), Y(v[k])); }
    ctx.stroke(); ctx.fillStyle = C.navy;
    for (let k = 0; k < M; k++) { ctx.beginPath(); ctx.arc(X(k), Y(v[k]), 1.9 * Math.sqrt(KW()), 0, 2 * Math.PI); ctx.fill(); }
    ctx.restore();
  });
}

/* ------------------------------------------------------------ machine learning */
const ML = D.ml, FITS = b64f32(ML.fits), NG = ML.g, TRUEF = b64f32(ML.f);
const mlState = (k, i) => FITS[k * NG + i];
function plotML(r, i0) {
  const X = x => r.x + 5 + x * (r.w - 10), Y = v => r.y + r.h / 2 - v * (r.h / 2 - 4) / ML.amp;
  const st = stepper(ML.n);
  clip(r, () => {
    line([[r.x, Y(0)], [r.x + r.w, Y(0)]], { color: C.rule, width: 1, alpha: seg(i0 + .1, .3) });
    line(Array.from(TRUEF, (v, i) => [X(i / (NG - 1)), Y(v)]), { color: C.guide, width: KW(), dash: [5, 4], progress: seg(i0 + .1, .45) });
    const fit = []; for (let i = 0; i < NG; i++) fit.push([X(i / (NG - 1)), Y(glide(mlState, st, i))]);
    line(fit, { color: C.blue, width: 2.2 * KW(), progress: seg(i0 + .16, .4) });
    for (let j = 1; j <= ML.n; j++) {
      const a = arrive(st, j); if (a <= 0) continue;
      dot(X(ML.x[j - 1]), Y(ML.y[j - 1]), 3 * Math.sqrt(KW()), { color: C.navy, fill: '#fff', width: 1.3 * KW(), alpha: a });
    }
  });
}

/* ------------------------------------------------------------ estimation theory */
const ES = D.est;
const npdf = (x, m, s) => Math.exp(-.5 * ((x - m) / s) * ((x - m) / s)) / (s * 2.5066282746310002);
function plotEST(r, i0) {
  const [lo, hi] = ES.lim, X = v => r.x + 5 + (v - lo) / (hi - lo) * (r.w - 10);
  const base = r.y + r.h - 11, PY = p => base - p * (r.h - 16) / ES.pmax;
  const st = stepper(ES.n);
  const m = glide((k) => ES.mu[k], st, 0), s = glide((k) => ES.tau[k], st, 0);
  const fa = seg(i0 + .14, .3);
  clip(r, () => {
    // the 95% interval under the posterior, the posterior, the axis
    const a = m - 1.959963984540054 * s, b = m + 1.959963984540054 * s, band = [[X(a), base]];
    for (let i = 0; i <= 60; i++) { const v = a + (b - a) * i / 60; band.push([X(v), PY(npdf(v, m, s))]); }
    band.push([X(b), base]);
    if (fa > 0) { ctx.save(); ctx.globalAlpha *= fa; ctx.fillStyle = C.steel2; ctx.beginPath(); band.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.fill(); ctx.restore(); }
    line([[X(ES.th), base], [X(ES.th), r.y + 3]], { color: C.guide, width: KW(), dash: [5, 4], progress: seg(i0 + .12, .3) });
    const curve = []; for (let i = 0; i <= 160; i++) { const v = lo + (hi - lo) * i / 160; curve.push([X(v), PY(npdf(v, m, s))]); }
    line(curve, { color: C.navy, width: 2.2 * KW(), progress: seg(i0 + .1, .45) });
    line([[r.x, base], [r.x + r.w, base]], { color: C.ink, width: 1.1 * KW(), progress: seg(i0 + .06, .35) });
    // the data, as they arrive: a tick under the axis each
    for (let j = 1; j <= ES.n; j++) {
      const al = arrive(st, j); if (al <= 0) continue;
      line([[X(ES.x[j - 1]), base + 3], [X(ES.x[j - 1]), base + 9]], { color: C.navy, width: 1.3 * KW(), alpha: al });
    }
    dot(X(m), base, 3.6 * Math.sqrt(KW()), { color: '#fff', fill: C.accent, width: 1.1, alpha: fa });
  });
}

/* ------------------------------------------------------------ optimization */
const OP = D.opt, NOP = OP.path.length - 1;
const opState = (k, i) => OP.path[k][i];
function plotOPT(r, i0) {
  // one scale for both parameters, so each step meets the contours at right angles as drawn
  const S = Math.min((r.w - 12) / OP.box[2], (r.h - 10) / OP.box[3]), cx = r.x + r.w / 2, cy = r.y + r.h / 2;
  const P = (w1, w2) => [cx + S * (w1 - OP.box[0]), cy - S * (w2 - OP.box[1])];
  const st = stepper(NOP);
  clip(r, () => {
    // contours of J: ellipses about the minimum, exact (the eigenvectors of its Hessian)
    OP.levels.forEach((c, i) => {
      const a0 = Math.sqrt(2 * c / OP.lam[0]), a1 = Math.sqrt(2 * c / OP.lam[1]), pts = [];
      for (let j = 0; j <= 96; j++) {
        const f = 2 * Math.PI * j / 96, p = a0 * Math.cos(f), q = a1 * Math.sin(f);
        pts.push(P(OP.ws[0] + p * OP.v[0][0] + q * OP.v[0][1], OP.ws[1] + p * OP.v[1][0] + q * OP.v[1][1]));
      }
      line(pts, { color: C.sky, width: KW(), progress: seg(i0 + .1 + .03 * i, .35) });
    });
    const [mx, my] = P(OP.ws[0], OP.ws[1]), ma = seg(i0 + .3, .2);
    line([[mx - 4, my], [mx + 4, my]], { color: C.ink, width: 1.2 * KW(), alpha: ma });
    line([[mx, my - 4], [mx, my + 4]], { color: C.ink, width: 1.2 * KW(), alpha: ma });
    // the steps taken, and the iterate on its way to the next
    const w1 = glide(opState, st, 0), w2 = glide(opState, st, 1);
    if (st.k > 0 && st.a > 0) {
      const pts = OP.path.slice(0, st.k).map(q => P(q[0], q[1]));
      pts.push(P(w1, w2));
      line(pts, { color: C.navy, width: 1.3 * KW(), alpha: st.a });
      for (let j = 1; j < st.k; j++) { const q = P(OP.path[j][0], OP.path[j][1]); dot(q[0], q[1], 1.8, { color: C.navy, fill: C.navy, width: .6, alpha: st.a }); }
    }
    const s0 = P(OP.path[0][0], OP.path[0][1]);
    dot(s0[0], s0[1], 3.4 * Math.sqrt(KW()), { color: C.navy, fill: '#fff', width: 1.3, alpha: seg(i0 + .3, .2) });
    const c = P(w1, w2);
    dot(c[0], c[1], 4.2 * Math.sqrt(KW()), { color: '#fff', fill: C.accent, width: 1.2, alpha: seg(i0 + .32, .2) });
  });
}

/* ------------------------------------------------------------ nodes and links */
function node(n, i) {
  const x0 = n.cx - NW / 2, i0 = .03 * i;
  line([[x0, n.y], [x0 + NW, n.y], [x0 + NW, n.y + NH], [x0, n.y + NH], [x0, n.y]], { color: C.ink, width: 1.3 * KW(), progress: seg(i0, .4) });
  const ta = settle(.08 + i0, .28);
  if (NARROW()) text(n.title, n.cx, n.y + 37 + rise(ta), { size: 28, align: 'center', alpha: ta });
  else {
    text(n.title, n.cx, n.y + 31 + rise(ta), { size: 22, align: 'center', alpha: ta });
    const sa = lab(.3 + i0);
    n.sub.forEach((s, j) => text(s, n.cx, n.y + 158 + 20 * j + rise(sa), { size: 17, color: C.body, align: 'center', alpha: sa }));
  }
  n.plot(plotRect(n), i0 + .05);
}
function grow(x1, y1, x2, y2, p, o) { if (p > 0) arrow(x1, y1, lerp(x1, x2, p), lerp(y1, y2, p), o); }
function links() {
  const k = KW(), o = { color: C.ink, width: 1.3 * k, head: 9 + 2 * (k - 1) };
  // the problems overlap: plain links along the top row
  const ym = TOPY + NH / 2;
  for (let i = 0; i < 2; i++) line([[XT[i] + NW / 2, ym], [XT[i + 1] - NW / 2, ym]], { color: C.guide, width: k, dash: [5, 4], progress: seg(.4, .25) });
  // the foundations' links rise into one line and on into each problem
  line([[XR[0], BOTY], [XR[0], BUS]], { width: 1.3 * k, progress: seg(.3, .2) });
  line([[XR[1], BOTY], [XR[1], BUS]], { width: 1.3 * k, progress: seg(.3, .2) });
  const pb = seg(.42, .3);
  if (pb > 0) line([[XT[0], BUS], [XT[2], BUS]], { width: 1.3 * k, progress: pb });
  for (const x of XR) dot(x, BUS, 2.6 * Math.sqrt(k), { color: C.ink, fill: C.ink, width: 1, alpha: seg(.45, .15) });
  XT.forEach((x, i) => grow(x, BUS, x, TOPY + NH + 1, seg(.55 + .04 * i, .22), o));
  // the criterion one way, the solution the other
  const xa = XF[0] + NW / 2 + 5, xb = XF[1] - NW / 2 - 5, yc = BOTY + NH / 2;
  grow(xa, yc - 9, xb, yc - 9, seg(.5, .3), o);
  grow(xb, yc + 9, xa, yc + 9, seg(.58, .3), o);
  if (NARROW()) return;
  const la = lab(.62), lb = lab(.7);
  text('statistical inference', XR[0] - 9, BUS + 25 + rise(la), { size: 16, color: C.body, align: 'right', alpha: la });
  text('numerical fitting', XR[1] + 9, BUS + 25 + rise(la), { size: 16, color: C.body, alpha: la });
  text('shared tools for data-driven models', (XT[0] + XT[2]) / 2, BUS + 25 + rise(lb), { size: 16, color: C.body, align: 'center', alpha: lb });
  text('criterion', (xa + xb) / 2, yc - 17 + rise(lb), { size: 16, color: C.body, align: 'center', alpha: lb });
  text('solution', (xa + xb) / 2, yc + 28 + rise(lb), { size: 16, color: C.body, align: 'center', alpha: lb });
}

function draw() {
  NODES.forEach(node);
  links();
}
boot();
"""


def page_data(sp, si, ml, es, op):
    # the optimization plane: the outer contour's and the path's extent (centre, width, height)
    c = op["levels"][0]
    f = np.linspace(0, 2 * np.pi, 721)
    e = op["ws"][:, None] + op["V"] @ np.vstack([np.sqrt(2 * c / op["lam"][0]) * np.cos(f),
                                                  np.sqrt(2 * c / op["lam"][1]) * np.sin(f)])
    ext = np.c_[e, op["path"].T]
    lo, hi = ext.min(1), ext.max(1)
    box = [0.5 * (lo[0] + hi[0]), 0.5 * (lo[1] + hi[1]), hi[0] - lo[0], hi[1] - lo[1]]
    return {
        "clock": {"t0": T0, "run": RUN, "hold": HOLD, "back": BACK, "rest": REST},
        "sp": {"n": SP_N, "x": common.f32(sp["x"]), "y": common.f32(sp["y"]), "amp": 2.3},
        "si": {"m": SI_M, "h": si["h"], "est": si["est"], "ns": SI_NS.tolist(), "amp": 1.12},
        "ml": {"n": ML_N, "x": ml["x"], "y": ml["y"], "g": ML_G, "fits": common.f32(ml["fits"]),
               "f": common.f32(ml_f(ml["xg"])), "amp": 1.75},
        "est": {"n": EST_N, "x": es["x"], "mu": es["mu"], "tau": es["tau"], "th": EST_TH,
                "lim": list(EST_LIM), "pmax": 1.06 / (es["tau"].min() * np.sqrt(2 * np.pi))},
        "opt": {"ws": op["ws"], "lam": op["lam"], "v": op["V"], "path": op["path"], "levels": op["levels"],
                "box": box},
    }


TITLE = "Different problems, shared inference and fitting tools"
ARIA = ("Three problems, signal processing, system identification and machine learning, draw on two shared "
        "foundations, estimation theory by statistical inference and optimization by numerical fitting, which "
        "hand each other a criterion and a solution. In each box a small computed example converges: an "
        "adaptive filter cleans a noisy signal, an impulse response is estimated from input and output data, a "
        "kernel model fits arriving points, a posterior narrows as data arrive, and gradient descent walks down "
        "a contour map to its minimum.")


def validate(sp, si, ml, es, op):
    """Independent comparisons for each example (closed forms, other solvers,
    Monte Carlo); returns the numbers the check file reports."""
    import scipy.linalg as sl
    from scipy.signal import lfilter
    out = {}

    # ---- signal processing: the ALE against Wiener-Hopf theory
    wo, js, R, pv = sp_wiener()
    wmid, wend, mse = [], [], []
    for k in range(SP_RUNS):
        n, s_, x = sp_signals(1000 + k, SP_LONG)
        y, ws = sp_ale(x, SP_LONG)
        wmid.append(ws[SP_N])
        wend.append(ws[-1])
        mse.append((y[:SP_N] - s_[SP_M + SP_D:SP_M + SP_D + SP_N]) ** 2)
    wmid, wend, mse = np.array(wmid), np.array(wend), np.array(mse)
    # the response at each tone, W(e^{iw}) = sum w_k e^{-iw(k + D)}: the noise-only directions of R,
    # where each run's weights wander slowly (time constant M sigma_x^2 / (mu sigma^2) samples), do
    # not reach it; in steady state its mean is the Wiener filter's
    resp = []
    for p in SP_P:
        ev = np.exp(-1j * 2 * np.pi / p * (np.arange(SP_M) + SP_D))
        r_, r0 = wend @ ev, wmid @ ev
        resp.append((p, np.mean(r_), np.std(r_.real, ddof=1) / np.sqrt(SP_RUNS),
                     np.std(r_.imag, ddof=1) / np.sqrt(SP_RUNS), wo @ ev, np.mean(r0)))
    out["sp_resp"] = resp
    jex = SP_MU / (2 - SP_MU) * (js + SP_SIG ** 2)            # NLMS excess, steady state
    out["sp_js"], out["sp_jex"] = js, jex
    tail = slice(SP_N // 2, SP_N)
    out["sp_mse_ens"] = mse[:, tail].mean()
    out["sp_mse_run"] = np.mean((sp["y"] - sp["s"])[tail] ** 2)
    out["sp_mse_in"] = SP_SIG ** 2
    out["sp_sig2"] = sum(a * a / 2 for a in SP_A)
    gains = []
    for a, p in zip(SP_A, SP_P):
        om = 2 * np.pi / p
        Wz = np.sum(wo * np.exp(-1j * om * (np.arange(SP_M) + SP_D)))
        g = SP_M * a * a / 4 / (SP_SIG ** 2 + SP_M * a * a / 4)
        gains.append((p, abs(Wz), np.angle(Wz), g))
    out["sp_gain"] = gains
    # the run drawn: the rms error of its output, window by window
    e = (sp["y"] - sp["s"]) ** 2
    out["sp_win"] = [(a, b, np.sqrt(e[a:b].mean())) for a, b in ((0, 30), (30, 60), (60, 120), (120, SP_N))]

    # ---- system identification
    h, r, th = si["h"], si["r"], si["th"]
    imp = np.zeros(SI_M)
    imp[0] = 1
    h_rec = lfilter([0, r * np.sin(th)], [1, -2 * r * np.cos(th), r * r], imp)
    out["si_rec"] = np.abs(h_rec - h).max()
    out["si_cont"] = np.abs(SM.h(np.arange(SI_M) / SI_FS) - h).max()
    U, Y = si["U"], si["Y"]
    dl = 0.0
    for N, e_ in zip(SI_NS, si["est"]):
        ne = sl.solve(U[:N].T @ U[:N], U[:N].T @ Y[:N], assume_a="pos")
        q, rr = np.linalg.qr(U[:N])
        qr = sl.solve_triangular(rr, q.T @ Y[:N])
        dl = max(dl, np.abs(ne - e_).max(), np.abs(qr - e_).max())
    out["si_solvers"] = dl
    mc = []
    rng = np.random.default_rng(99)
    for N in (int(SI_NS[5]), int(SI_NS[-1])):
        Ui = U[:N]
        G = np.linalg.inv(Ui.T @ Ui)
        theo = si["sig"] ** 2 * np.trace(G)
        y0 = Ui @ h
        errs = []
        for _ in range(SI_MC):
            yk = y0 + si["sig"] * rng.standard_normal(N)
            errs.append(np.sum((G @ (Ui.T @ yk) - h) ** 2))
        errs = np.array(errs)
        mc.append((N, errs.mean(), errs.std(ddof=1) / np.sqrt(SI_MC), theo))
    out["si_mc"] = mc
    out["si_rel"] = [(int(N), np.linalg.norm(e_ - h) / np.linalg.norm(h)) for N, e_ in zip(SI_NS, si["est"])]
    out["si_snr"] = 10 * np.log10(np.mean(si["y0"][SI_M - 1:] ** 2) / si["sig"] ** 2)

    # ---- machine learning
    import warnings
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import RBF
    from sklearn.kernel_ridge import KernelRidge
    dk = dg = 0.0
    xg = ml["xg"][:, None]
    for n in range(1, ML_N + 1):
        X_, Y_ = ml["x"][:n, None], ml["y"][:n]
        kr = KernelRidge(alpha=ML_LAM, kernel="rbf", gamma=1 / (2 * ML_ELL ** 2)).fit(X_, Y_)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gp = GaussianProcessRegressor(kernel=RBF(ML_ELL, "fixed"), alpha=ML_LAM, optimizer=None).fit(X_, Y_)
        dk = max(dk, np.abs(kr.predict(xg) - ml["fits"][n]).max())
        dg = max(dg, np.abs(gp.predict(xg) - ml["fits"][n]).max())
    out["ml_krr"], out["ml_gpr"] = dk, dg

    # ---- estimation theory
    g = np.linspace(-8, 8, 160001)
    lp = -0.5 * ((g - EST_MU0) / EST_TAU0) ** 2
    worst = 0.0
    for n in (1, 5, EST_N):
        ll = lp - 0.5 * np.sum((es["x"][:n, None] - g[None, :]) ** 2, axis=0) / EST_SIG ** 2
        pd = np.exp(ll - ll.max())
        pd /= np.trapezoid(pd, g)
        m = np.trapezoid(g * pd, g)
        sd = np.sqrt(np.trapezoid((g - m) ** 2 * pd, g))
        worst = max(worst, abs(m - es["mu"][n]), abs(sd - es["tau"][n]))
    out["est_grid"] = worst
    m, t2 = EST_MU0, EST_TAU0 ** 2
    seq = [m]
    for xi in es["x"]:
        t2n = 1 / (1 / t2 + 1 / EST_SIG ** 2)
        m = t2n * (m / t2 + xi / EST_SIG ** 2)
        t2 = t2n
        seq.append(m)
    out["est_seq"] = np.abs(np.array(seq) - es["mu"]).max()
    rng = np.random.default_rng(4242)
    thetas = EST_MU0 + EST_TAU0 * rng.standard_normal(EST_MC)
    xs = thetas[:, None] + EST_SIG * rng.standard_normal((EST_MC, EST_N))
    tau2 = 1 / (1 / EST_TAU0 ** 2 + EST_N / EST_SIG ** 2)
    mus = tau2 * (EST_MU0 / EST_TAU0 ** 2 + xs.sum(1) / EST_SIG ** 2)
    z = 1.959963984540054
    out["est_cov"] = np.mean(np.abs(thetas - mus) <= z * np.sqrt(tau2))
    out["est_cov_se"] = np.sqrt(0.95 * 0.05 / EST_MC)
    out["est_in"] = abs(es["mu"][-1] - EST_TH) <= z * es["tau"][-1]

    # ---- optimization
    pf = np.polyfit(op["xd"], op["yd"], 1)[::-1]
    out["opt_pf"] = np.abs(pf - op["ws"]).max()
    d = np.linalg.norm(op["path"] - op["ws"], axis=1)
    out["opt_d"] = d
    out["opt_rate"] = d[-1] / d[-2]
    out["opt_rate_th"] = max(abs(1 - op["eta"] * op["lam"][0]), abs(1 - op["eta"] * op["lam"][1]))
    worst = 0.0
    for c in op["levels"]:
        f = np.linspace(0, 2 * np.pi, 97)
        pts = op["ws"][:, None] + op["V"] @ np.vstack([np.sqrt(2 * c / op["lam"][0]) * np.cos(f),
                                                        np.sqrt(2 * c / op["lam"][1]) * np.sin(f)])
        Jv = np.array([op["J"](q) for q in pts.T]) - op["J"](op["ws"])
        worst = max(worst, np.abs(Jv / c - 1).max())
    out["opt_ell"] = worst
    return out


def page_check(sp, ml):
    """The arrays as the page decodes them, against the model's numbers."""
    got = SM.check_page(NAME, ["Array.from(SPY)", "Array.from(SPX)", "Array.from(FITS)"])
    return max(np.abs(got[0] - sp["y"]).max(), np.abs(got[1] - sp["x"]).max(),
               np.abs(got[2] - ml["fits"].ravel()).max())


def report(sp, si, ml, es, op, v, pg, over):
    L = []
    say = L.append
    say("nf-sp-foundations: the signal processing guide's cover (his animation \"Different problems,")
    say("shared inference and fitting tools\"), check of tools/numfig/sp_foundations.py")
    say("")
    say("Five small examples, one in each of his nodes, computed here with fixed seeds; the page draws")
    say("their numbers (DATA) and computes nothing but the drawing (normal densities and ellipses from")
    say("the closed forms below).")
    say("")
    say("1. SIGNAL PROCESSING: an adaptive line enhancer")
    say(f"  s(n) = {SP_A[0]:g} sin(2 pi n / {SP_P[0]:g}) + {SP_A[1]:g} sin(2 pi n / {SP_P[1]:g} + {SP_PH[1]:g}), "
        f"x(n) = s(n) + v(n), v white Gaussian, sigma = {SP_SIG:g}")
    snr_in = 10 * np.log10(v["sp_sig2"] / SP_SIG ** 2)
    say(f"  (input SNR {snr_in:.1f} dB, seed {SP_SEED}). An FIR predictor of M = {SP_M} taps, delay D = {SP_D}:")
    say(f"  y(n) = w(n)^T [x(n-1) ... x(n-{SP_M})], NLMS from w = 0, mu = {SP_MU:g}; y(n) is the cleaned signal.")
    say(f"  {SP_N} samples drawn, the filter's output sample by sample.")
    say("  CHECK 1: the filter learnt against the Wiener filter, w_o = R^-1 p from the input's exact")
    say("    autocorrelation r(k) = sum A^2/2 cos(2 pi k / P) + sigma^2 delta(k), p_j = r(j + D). Their responses at")
    say(f"    each tone, W(e^{{iw}}) = sum w_k e^{{-iw(k + D)}}, the NLMS filter's after n = {SP_LONG} (steady state),")
    say(f"    mean of {SP_RUNS} runs (seeds 1000 on), with standard errors:")
    for p, m, se_r, se_i, wi, m0 in v["sp_resp"]:
        say(f"    period {p:g}: {m.real:.4f} {m.imag:+.4f}i (+- {se_r:.4f}, {se_i:.4f}) against {wi.real:.4f}"
            f" {wi.imag:+.4f}i ({(m.real - wi.real) / se_r:+.1f} and {(m.imag - wi.imag) / se_i:+.1f} standard errors);")
        say(f"      after the {SP_N} samples drawn, {m0.real:.4f}: the filter has nearly converged.")
    say("  CHECK 2: the single tone ALE gain (Widrow and Stearns), G = (M A^2/4) / (sigma^2 + M A^2/4), against")
    say("    the Wiener filter's response at each tone, W(e^{iw}) = sum w_k e^{-iw(k + D)}:")
    for p, mag, ang, g in v["sp_gain"]:
        say(f"    period {p:g}: |W| = {mag:.4f}, arg W = {ang:+.4f} rad, closed form G = {g:.4f} ({mag / g - 1:+.1e})")
    say("  CHECK 3: the error of the cleaned signal, E (y - s)^2, against theory: the Wiener residual")
    say(f"    J_s = sigma_s^2 - p^T R^-1 p = {v['sp_js']:.5f} plus the NLMS excess mu/(2 - mu) (J_s + sigma^2) =")
    say(f"    {v['sp_jex']:.5f}: {v['sp_js'] + v['sp_jex']:.5f}. Measured over n = {SP_N // 2} to {SP_N - 1}: "
        f"{v['sp_mse_ens']:.5f} ({SP_RUNS} runs, {v['sp_mse_ens'] / (v['sp_js'] + v['sp_jex']) - 1:+.0%}: the filter is"
        " still converging")
    say("    early in that window),")
    say(f"    {v['sp_mse_run']:.5f} in the run drawn; the noise it removes: sigma^2 = {SP_SIG ** 2:.4f}"
        f" ({10 * np.log10(SP_SIG ** 2 / v['sp_mse_run']):.1f} dB less).")
    say("    rms error of the run drawn, by window: " +
        ", ".join(f"n {a} to {b - 1}: {e:.3f}" for a, b, e in v["sp_win"]))
    say("")
    say("2. SYSTEM IDENTIFICATION: least squares FIR from input and output data")
    say(f"  The resonator of Figure 1 (sp_model, f_n = {SM.FN:g} Hz, zeta = {SM.ZETA:g}) sampled at {SI_FS:g} Hz, its"
        f" first M = {SI_M} taps,")
    say(f"  h_k = r^k sin(k theta), r = {si['r']:.6f}, theta = {si['th']:.6f} rad (Figure 2's unknown system,"
        " shorter).")
    say(f"  Input white Gaussian (unit variance), output measured with white noise {v['si_snr']:.1f} dB below it"
        f" (seed {SI_SEED}).")
    say(f"  h estimated by least squares from the first N samples, N = {', '.join(str(int(n)) for n in SI_NS)}.")
    say(f"  CHECK 1: h_k against the impulse response of its recursion h_k = 2 r cos(theta) h_k-1 - r^2 h_k-2"
        f" (+ r sin(theta) at k = 1): {v['si_rec']:.1e};")
    say(f"    against sp_model.h(k / f_s), the continuous impulse response sampled: {v['si_cont']:.1e}.")
    say(f"  CHECK 2: the estimate by lstsq (SVD) against the normal equations (Cholesky) and QR: {v['si_solvers']:.1e}.")
    say("  CHECK 3: the estimate's error against theory, E |h_N - h|^2 = sigma^2 tr((U^T U)^-1), over "
        f"{SI_MC} noise draws (same input):")
    for N, m, se, th_ in v["si_mc"]:
        say(f"    N = {N}: {m:.5f} +- {se:.5f} against {th_:.5f} ({(m - th_) / se:+.1f} standard errors)")
    say("    relative error of the estimates drawn: " + ", ".join(f"N {n}: {e:.3f}" for n, e in v["si_rel"][::3])
        + f", N {v['si_rel'][-1][0]}: {v['si_rel'][-1][1]:.3f}")
    say("")
    say("3. MACHINE LEARNING: kernel ridge regression, the points arriving one by one")
    say(f"  y_i = sin(2 pi x_i) + e_i, x_i uniform on [0.02, 0.98], e_i ~ N(0, {ML_SIG:g}^2), {ML_N} points, seed"
        f" {ml['seed']}: the first seed from 1")
    say("  for which no gap between the points (and the ends) is wider than 0.12 and the fit's error never rises")
    say("  by more than 0.03 from one point to the next. The seed is chosen for the picture, a fit that improves")
    say("  steadily as the points arrive; the choice is a display decision and is stated here.")
    say(f"  f_n(x) = k(x)^T (K + lambda I)^-1 y, RBF kernel exp(-(a - b)^2 / (2 l^2)), l = {ML_ELL:g}, lambda ="
        f" {ML_LAM:g} = ({ML_SIG:g})^2 / 1^2;")
    say(f"  drawn on {ML_G} points of [0, 1]; before the first point the fit is the prior mean, 0.")
    say(f"  CHECK 1: against scikit-learn's KernelRidge, every n: {v['ml_krr']:.1e}.")
    say(f"  CHECK 2: against scikit-learn's GaussianProcessRegressor (the same kernel fixed, noise {ML_LAM:g}),"
        f" its posterior mean: {v['ml_gpr']:.1e}.")
    say("  rms error of the fit against sin(2 pi x): " +
        ", ".join(f"n = {n}: {ml['rmse'][n]:.3f}" for n in (0, 2, 5, 10, 15, 20)))
    say("")
    say("4. ESTIMATION THEORY: a normal mean, the conjugate posterior")
    say(f"  x_i ~ N(theta, {EST_SIG:g}^2), theta = {EST_TH:g} (unknown to the estimator), prior N({EST_MU0:g},"
        f" {EST_TAU0:g}^2), {EST_N} data, seed {EST_SEED};")
    say("  posterior N(mu_n, tau_n^2), 1/tau_n^2 = 1/tau_0^2 + n/sigma^2, mu_n = tau_n^2 (mu_0/tau_0^2 + sum x_i/sigma^2).")
    say(f"  mu_n: n = 0: {es['mu'][0]:.3f}, 1: {es['mu'][1]:.3f}, 5: {es['mu'][5]:.3f}, 10: {es['mu'][10]:.3f},"
        f" 20: {es['mu'][20]:.4f}; tau_n: {es['tau'][0]:.3f} to {es['tau'][-1]:.4f};")
    lo, hi = es["mu"][-1] - 1.959963984540054 * es["tau"][-1], es["mu"][-1] + 1.959963984540054 * es["tau"][-1]
    say(f"  the 95% interval at n = 20, [{lo:.3f}, {hi:.3f}], holds theta: {bool(v['est_in'])}.")
    say(f"  CHECK 1: against the posterior computed on a grid (prior x likelihood, 160,001 points on [-8, 8],"
        f" trapezoid rule), its mean and standard deviation at n = 1, 5, 20: {v['est_grid']:.1e}.")
    say(f"  CHECK 2: the batch formula against updating one datum at a time: {v['est_seq']:.1e}.")
    say(f"  CHECK 3: calibration. With theta drawn from the prior, {EST_MC:,} times, the 95% interval at"
        f" n = {EST_N} holds theta")
    say(f"    in {v['est_cov'] * 100:.2f}% of them (95% expected, standard error {v['est_cov_se'] * 100:.2f}%).")
    say("")
    say("5. OPTIMIZATION: gradient descent on a least squares objective")
    say(f"  A line y = w_1 + w_2 x fitted to {OPT_N} points (x uniform on [{OPT_X[0]:g}, {OPT_X[1]:g}], y = "
        f"{OPT_AB[0]:g} + {OPT_AB[1]:g} x + N(0, {OPT_NOISE:g}^2), seed {OPT_SEED}):")
    say("  J(w) = |X w - y|^2 / (2 N), a quadratic; its Hessian X^T X / N has eigenvalues "
        f"{op['lam'][0]:.4f} and {op['lam'][1]:.4f} (condition {op['lam'][1] / op['lam'][0]:.2f}),")
    ang = np.degrees(np.arctan2(op["V"][1, 0], op["V"][0, 0]))
    say(f"  its shallow axis at {ang:+.1f} deg. w_{{k+1}} = w_k - eta grad J(w_k), eta = {OPT_ETA:g} / lambda_max ="
        f" {op['eta']:.4f}, {OPT_K} steps from")
    say(f"  w_0 = w* - {OPT_D0[0]:g} v_shallow + {OPT_D0[1]:g} v_steep = ({op['path'][0][0]:.4f}, {op['path'][0][1]:.4f})"
        f" to ({op['path'][-1][0]:.5f}, {op['path'][-1][1]:.5f});")
    say(f"  w* = ({op['ws'][0]:.5f}, {op['ws'][1]:.5f}). Distance to w*: " +
        ", ".join(f"k = {k}: {v['opt_d'][k]:.4f}" for k in (0, 1, 2, 4, 8, 16, OPT_K)))
    say(f"  CHECK 1: w* (normal equations) against numpy.polyfit: {v['opt_pf']:.1e}; the last iterate is"
        f" {v['opt_d'][-1]:.1e} from it.")
    say(f"  CHECK 2: the rate. The error obeys e_k+1 = (I - eta H) e_k, so it shrinks by max |1 - eta lambda_i| ="
        f" {v['opt_rate_th']:.6f}")
    say(f"    per step once the steep mode has died out; measured over the last step: {v['opt_rate']:.6f}"
        f" ({v['opt_rate'] / v['opt_rate_th'] - 1:+.1e}).")
    say(f"  CHECK 3: the contours drawn, J = J* + c for c = 1.25 J(w_0) x {OPT_Q:g}^j, j = 0 .. {OPT_LEVELS - 1},"
        f" are the ellipses")
    say("    w* + V diag(sqrt(2 c / lambda)) (cos f, sin f); J evaluated from the data on 97 points of each:"
        f" {v['opt_ell']:.1e} (relative).")
    say("  The plane is drawn at one scale for w_1 and w_2, so each step meets the contours at right angles")
    say("  as drawn.")
    say("")
    say("PAGE")
    say(f"  The arrays the page decodes (float32: the noisy input, the filter's output, the {ML_N + 1} fits)"
        f" against the model's: {pg:.1e}.")
    say("  Other numbers travel as JSON rounded to 5 decimals (the estimates, the posterior's mean and spread,")
    say("  the iterates, the Hessian's eigenvectors).")
    say("")
    say("DISPLAY AND CLOCK")
    say(f"  One loop for the five examples: from t = {T0:g} s each takes its steps over {RUN:g} s, holds {HOLD:g} s,")
    say(f"  glides home in {BACK:g} s (its trail fading) and rests {REST:g} s: a loop of {RUN + HOLD + BACK + REST:g} s.")
    say(f"  Steps: the filter's {SP_N} samples at an even pace ({SP_N / RUN:.1f} per second; n has no unit, so no"
        f" slowing is claimed);")
    say(f"  {len(SI_NS)} estimates as N grows geometrically; {ML_N} points; {EST_N} data; {OPT_K} iterations; each"
        " step a Motion spring glide")
    say("  between the states computed here (the states are exact; the glides only carry the eye from one to")
    say(f"  the next). The still (print, reduced motion): t = {T0 + RUN + 1.0:g} s, every example converged.")
    say("  Crimson marks the current estimate where it is a point: the filter's newest output sample, the")
    say("  posterior mean, the iterate.")
    say("")
    say("OVERLAP (engine ?overlap, common.overlaps; common.still also samples every 0.25 s up to the poster)")
    for width, res in over:
        bad = {k: v_ for k, v_ in res.items() if v_["labels"] or v_["crossings"]}
        say(f"  {width} px: moments {', '.join(res)}: " + ("none" if not bad else str(bad)))
    txt = "\n".join(L) + "\n"
    with open(os.path.join(HERE, "sp_foundations.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


def build():
    sp, si, ml, es, op = sp_model(), si_model(), ml_model(), est_model(), opt_model()
    data = page_data(sp, si, ml, es, op)
    common.build_html(NAME, TITLE, ARIA, 1000, 460, data, JS)
    png = common.still(NAME, width=672)
    print("still:", png)
    pg = page_check(sp, ml)
    v = validate(sp, si, ml, es, op)
    per = RUN + HOLD + BACK + REST
    times = [0.2, 0.45, 0.7, 1.0, 1.3, 2.0, 3.0, 4.5, 6.0, T0 + RUN + 1.0, T0 + RUN + HOLD + 0.3,
             T0 + RUN + HOLD + 0.7, T0 + per - 0.1, T0 + per + 0.4, T0 + per + 2.5, T0 + 2 * per + 6.5]
    over = [(672, common.overlaps(NAME, times)), (360, common.overlaps(NAME, times, width=360))]
    report(sp, si, ml, es, op, v, pg, over)
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.15, 0.4, 0.8, 1.2, 2.0, 3.5, 7.15, 9.2, 9.8]))
    return sp, si, ml, es, op


if __name__ == "__main__":
    build()
