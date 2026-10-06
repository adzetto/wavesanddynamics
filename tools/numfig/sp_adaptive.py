"""Figure 3 of the signal processing document (his Figure 2; renumbered on the page
since 5 Oct 2026, when figures were added before it): adaptive filtering used for
system identification.

His caption: "Adaptive filtering used for system identification. The same
input drives both the unknown system and the adaptive filter; the error
between their outputs, e(n) = d(n) - y(n), is used to update the filter's
coefficients, step by step, until the filter reproduces the unknown system's
behavior."

Model. The unknown system is the resonator of Figure 1 (sp_model: f_n = 1 Hz,
zeta = 0.1) sampled at fs = 8 Hz over its first 6 s: an FIR system of M = 48
taps, h_k = r^k sin(k theta), r = exp(-zeta w_n / fs), theta = w_d / fs.
The input x(n) is white and Gaussian, scaled so that the system's output has
unit power; d(n) is that output plus white measurement noise 30 dB below it.
An adaptive FIR filter of the same length starts from w = 0 and is updated by
NLMS, w(n+1) = w(n) + mu e(n) u(n) / (delta + |u(n)|^2), mu = 0.5, the input
having run before n = 0 so that the regressor u(n) is full from the start.

The page runs the same NLMS itself on the same numbers (float32 inputs, double
arithmetic) when it loads: (a) the diagram, its two boxes holding h and the
live w(n); (b) the learning curve, this run and the mean of 400 runs (numpy);
(c) the magnitude responses |H| and |W_n|, computed in the page from h and w(n).

Run: python tools/numfig/sp_adaptive.py  (writes the page, the still and the
check file; prints the key numbers).
"""
import os

import numpy as np

import common
import sp_model as SM

FS = 8.0          # sampling frequency (Hz)
M = 48            # taps, 6 s of the resonator
MU = 0.5          # NLMS step
DELTA = 1e-6      # NLMS regularisation
SNR_DB = 30.0     # output to measurement noise
N = 600           # samples shown
R = 400           # runs in the mean learning curve
SEED = 12         # the run shown; the mean uses seeds 1000 .. 1000 + R - 1

JS = r"""
const D = DATA;
const X = b64f32(D.x), DD = b64f32(D.d), HK = b64f32(D.h), ENS = b64f32(D.ens);
const M = D.m, N = D.n, MU = D.mu, FS = D.fs;
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);

/* ------------------------------------------------------------ the run
   The page's own NLMS on DATA's input and desired output: w(n) for every n,
   the error e(n) and the output y(n). Computed once, then read by draw(). */
const WS = new Float64Array((N + 1) * M), E = new Float64Array(N), SM8 = new Float64Array(N);
function nlms() {
  const w = new Float64Array(M), u = new Float64Array(M);
  for (let n = 0; n < N; n++) {
    let yy = 0, uu = 0;
    for (let k = 0; k < M; k++) { u[k] = X[n + M - 1 - k]; yy += w[k] * u[k]; uu += u[k] * u[k]; }
    const e = DD[n] - yy, g = MU * e / (D.delta + uu);
    E[n] = e;
    for (let k = 0; k < M; k++) w[k] += g * u[k];
    WS.set(w, (n + 1) * M);
  }
  for (let n = 0; n < N; n++) {              // e^2 over the last period (8 samples), in dB
    let s = 0, c = 0;
    for (let j = Math.max(0, n - 7); j <= n; j++) { s += E[j] * E[j]; c++; }
    SM8[n] = 10 * Math.log10(s / c);
  }
}
nlms();
const wAt = (n, k) => WS[n * M + k];

/* ------------------------------------------------------------ clock
   Intro (README, round 2): strokes by .95 s, labels by 1.2 s. The run starts
   at .55 s: 600 samples in 7.5 s, rests 2.6 s; what the run drew fades out,
   the filter fades back in at n = 0, and it runs again (no fast rewind). */
const T0 = .55, RUN = 7.5, HOLD = 2.6, FADE = .45, REST = .3, PER = RUN + HOLD + 2 * FADE + REST;
function nNow() {                       // samples played, and the alpha of what the run has drawn
  if (t < T0) return {n: 0, a: 1};
  const c = Math.floor((t - T0) / PER), u = t - T0 - c * PER, b0 = T0 + c * PER;
  if (u < RUN) return {n: N * u / RUN, a: 1};
  if (u < RUN + HOLD) return {n: N, a: 1};
  if (u < RUN + HOLD + FADE) return {n: N, a: 1 - seg(b0 + RUN + HOLD, FADE)};
  return {n: 0, a: seg(b0 + RUN + HOLD + FADE, FADE)};
}
const POSTER_T = T0 + RUN + .6;

/* ------------------------------------------------------------ (a) */
const UB = {x: 196, y: 76, w: 420, h: 84}, AB = {x: 196, y: 214, w: 420, h: 84};
const SX = (bx, k) => bx.x + 14 + k * (bx.w - 28) / (M - 1), SS = 40 / D.hmax * .95;
const SJ = {x: 744, y: AB.y + AB.h / 2, r: 15};
function box(b, p) { line([[b.x, b.y], [b.x + b.w, b.y], [b.x + b.w, b.y + b.h], [b.x, b.y + b.h], [b.x, b.y]], {color: C.ink, width: 1.8, progress: p}); }
function stems(b, val, col, al, ghost) {
  const yb = b.y + b.h / 2;
  line([[b.x + 8, yb], [b.x + b.w - 8, yb]], {color: C.rule, width: 1, alpha: al});
  if (ghost) for (let k = 0; k < M; k++) dot(SX(b, k), yb - SS * HK[k], 2.3, {color: C.guide, fill: '#fff', width: 1, alpha: al});
  ctx.save(); ctx.globalAlpha *= al; ctx.strokeStyle = col; ctx.lineWidth = 1.3; ctx.beginPath();
  for (let k = 0; k < M; k++) { const x = SX(b, k); ctx.moveTo(x, yb); ctx.lineTo(x, yb - SS * val(k)); }
  ctx.stroke(); ctx.fillStyle = col;
  for (let k = 0; k < M; k++) { ctx.beginPath(); ctx.arc(SX(b, k), yb - SS * val(k), 1.9, 0, 2 * Math.PI); ctx.fill(); }
  ctx.restore();
}
function panelA(nf, ra) {
  panel('a', 20, 34, {alpha: seg(0, .2)});
  text('system identification', 54, 34, {size: 17, color: C.body, alpha: seg(.03, .25)});
  const w0 = seg(.02, .3), w1 = seg(.12, .3), w2 = seg(.22, .3);
  // the input and its branch point
  const yI = (UB.y + UB.h / 2 + AB.y + AB.h / 2) / 2, xN = 128;
  line([[52, yI], [xN, yI]], {width: 1.6, progress: w0});
  dot(xN, yI, 3, {color: C.ink, fill: C.ink, alpha: w0});
  line([[xN, yI], [xN, UB.y + UB.h / 2]], {width: 1.6, progress: w0});
  line([[xN, yI], [xN, AB.y + AB.h / 2]], {width: 1.6, progress: w0});
  arrow(xN, UB.y + UB.h / 2, UB.x - 2, UB.y + UB.h / 2, {width: 1.6, head: 10, alpha: w1});
  arrow(xN, AB.y + AB.h / 2, AB.x - 2, AB.y + AB.h / 2, {width: 1.6, head: 10, alpha: w1});
  box(UB, seg(.04, .4)); box(AB, seg(.08, .4));
  // the outputs into the summing junction, and the error out of it
  const yU = UB.y + UB.h / 2, yA = SJ.y;
  line([[UB.x + UB.w, yU], [SJ.x, yU]], {width: 1.6, progress: w1});
  arrow(SJ.x, yU, SJ.x, SJ.y - SJ.r - 1, {width: 1.6, head: 10, alpha: w2});
  arrow(AB.x + AB.w, yA, SJ.x - SJ.r - 1, yA, {width: 1.6, head: 10, alpha: w2});
  ctx.save(); ctx.globalAlpha *= w2; ctx.beginPath(); ctx.arc(SJ.x, SJ.y, SJ.r, 0, 2 * Math.PI);
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1.6; ctx.stroke(); ctx.restore();
  math('\\Sigma', SJ.x, SJ.y + 6, {size: 17, align: 'center', alpha: w2});
  const xE = 900, yF = AB.y + AB.h + 36, xU = AB.x + AB.w / 2;
  line([[SJ.x + SJ.r, yA], [xE, yA], [xE, yF], [xU, yF]], {width: 1.6, progress: seg(.26, .4)});
  // the adaptation: the error drives the filter's coefficients. It enters the
  // box from below: the textbook's diagonal through the box would cross the
  // live coefficients drawn inside it
  arrow(xU, yF, xU, AB.y + AB.h + 1, {width: 1.6, head: 10, alpha: seg(.5, .25)});
  math('\\rm{update}', xU + 10, yF - 12, {size: 16, color: C.muted, alpha: seg(.55, .25)});
  // words and symbols
  const L1 = lab(.12), L2 = lab(.18), L3 = lab(.24), L4 = lab(.3);
  text('unknown system', UB.x, UB.y - 9 + rise(L1), {size: 16, alpha: L1});
  text('adaptive filter', AB.x, AB.y - 9 + rise(L2), {size: 16, alpha: L2});
  math('x(n)', 52, yI - 10 + rise(L1), {size: 17, alpha: L1});
  math('d(n)', UB.x + UB.w + 16, yU - 10 + rise(L2), {size: 17, alpha: L2});
  math('y(n)', AB.x + AB.w + 16, yA - 10 + rise(L3), {size: 17, alpha: L3});
  math('+', SJ.x + 8, SJ.y - SJ.r - 8 + rise(L3), {size: 16, alpha: L3});
  math('-', SJ.x - SJ.r - 12, SJ.y - 9 + rise(L3), {size: 16, alpha: L3});
  math('e(n) = d(n) - y(n)', SJ.x + SJ.r + 12, yA - 10 + rise(L4), {size: 17, alpha: L4});
  math('h_k', UB.x + UB.w - 10, UB.y + 20, {size: 16, color: C.navy, align: 'right', alpha: lab(.34)});
  math('w_k(n)', AB.x + AB.w - 10, AB.y + 20, {size: 16, color: C.blue, align: 'right', alpha: lab(.38)});
  // inside the boxes: the unknown system's coefficients, and the filter's, live
  const sa = seg(.3, .3);
  stems(UB, k => HK[k], C.navy, sa, false);
  const n0 = Math.floor(nf), fr = nf - n0, n1 = Math.min(N, n0 + 1);
  stems(AB, k => lerp(wAt(n0, k), wAt(n1, k), fr), C.blue, sa * ra, true);
  // the sample counter, and how fast the record plays
  const ca = seg(.5, .2);
  math(`n = ${Math.round(nf)}`, 980, 34, {size: 16, align: 'right', alpha: ca * ra});
  math('\\rm{time sped up }' + D.speed + '\\,\\times', 980, 58, {size: 16, color: C.muted, align: 'right', alpha: ca});
}

/* ------------------------------------------------------------ (b) */
const PB = {x: 84, y: 398, w: 392, h: 176};
function panelB(nf, ra) {
  panel('b', 20, 372, {alpha: seg(.08, .2)});
  text('learning curve', 54, 372, {size: 17, color: C.body, alpha: seg(.1, .25)});
  const A = axes({x: PB.x, y: PB.y, w: PB.w, h: PB.h, xlim: [0, N], ylim: [-40, 5],
                  xticks: [0, 100, 200, 300, 400, 500, 600], yticks: [-40, -30, -20, -10, 0],
                  xlabel: 'n', ylabel: '\\rm{mean square error (dB)}', ylabelGap: 44,
                  grid: true, tickSize: 16, progress: seg(.1, .35)});
  // the floor: the measurement noise, what no filter can remove
  const fa = seg(.35, .25);
  A.inside(() => line([[PB.x, A.Y(D.floor)], [PB.x + PB.w, A.Y(D.floor)]], {color: C.guide, width: 1, dash: [5, 4], alpha: fa}));
  text('noise floor', PB.x + 8, A.Y(D.floor) + 19, {size: 16, color: C.muted, alpha: fa});
  // the mean of 400 runs, whole; this run, up to n
  const ens = []; for (let n = 0; n < N; n++) ens.push([A.X(n + .5), A.Y(ENS[n])]);
  A.inside(() => line(ens, {color: C.navy, width: 2.2, progress: seg(.2, .4)}));
  const k = Math.min(N - 1, Math.floor(nf));
  if (t >= T0 && k > 0) {
    const run = []; for (let n = 0; n <= k; n++) run.push([A.X(n + .5), A.Y(Math.max(-44, SM8[n]))]);
    A.inside(() => line(run, {color: C.sky, width: 1.2, alpha: ra}));
  }
  if (t >= T0) dot(A.X(k + .5), A.Y(clamp(SM8[k], -40, 5)), 4, {color: '#fff', fill: C.accent, width: 1.4, alpha: seg(T0, .15) * ra});
  // legend
  const la = seg(.4, .25), LX = PB.x + PB.w - 192, LY = PB.y + 10;
  if (la > 0) {
    ctx.save(); ctx.globalAlpha *= la; ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 1;
    ctx.fillRect(LX, LY, 184, 54); ctx.strokeRect(LX, LY, 184, 54); ctx.restore();
    line([[LX + 10, LY + 18], [LX + 38, LY + 18]], {color: C.sky, width: 1.2, alpha: la});
    text('this run', LX + 46, LY + 23.5, {size: 16, alpha: la});
    line([[LX + 10, LY + 39], [LX + 38, LY + 39]], {color: C.navy, width: 2.2, alpha: la});
    text(`mean of ${D.runs} runs`, LX + 46, LY + 44.5, {size: 16, alpha: la});
  }
}

/* ------------------------------------------------------------ (c) */
const PC = {x: 596, y: 398, w: 364, h: 176}, NF = 161;
const CS = new Float64Array(NF * M), SN = new Float64Array(NF * M);
for (let i = 0; i < NF; i++) for (let k = 0; k < M; k++) { const a = 2 * Math.PI * (i / (NF - 1)) * (FS / 2) * k / FS; CS[i * M + k] = Math.cos(a); SN[i * M + k] = Math.sin(a); }
function magnitude(val) {
  const out = new Float64Array(NF);
  for (let i = 0; i < NF; i++) {
    let re = 0, im = 0;
    for (let k = 0; k < M; k++) { const v = val(k); re += v * CS[i * M + k]; im -= v * SN[i * M + k]; }
    out[i] = Math.hypot(re, im);
  }
  return out;
}
const HM = magnitude(k => HK[k]);
function panelC(nf, ra) {
  panel('c', 540, 372, {alpha: seg(.1, .2)});
  text('frequency response', 574, 372, {size: 17, color: C.body, alpha: seg(.12, .25)});
  const A = axes({x: PC.x, y: PC.y, w: PC.w, h: PC.h, xlim: [0, FS / 2], ylim: [0, 7.5],
                  xticks: [0, 1, 2, 3, 4], yticks: [0, 2, 4, 6],
                  xlabel: '\\rm{frequency}\\ f\\ (\\rm{Hz})', ylabel: '|H|,\\ |W|', ylabelGap: 36,
                  grid: true, tickSize: 16, progress: seg(.14, .35)});
  const fx = i => A.X(i / (NF - 1) * FS / 2);
  const hp = []; for (let i = 0; i < NF; i++) hp.push([fx(i), A.Y(HM[i])]);
  const n0 = Math.floor(nf), fr = nf - n0, n1 = Math.min(N, n0 + 1);
  const WM = magnitude(k => lerp(wAt(n0, k), wAt(n1, k), fr));
  const wp = []; for (let i = 0; i < NF; i++) wp.push([fx(i), A.Y(WM[i])]);
  A.inside(() => {                      // the filter under, the system's dashes on top: they meet
    if (t >= T0) line(wp, {color: C.blue, width: 2.4, alpha: seg(T0, .2) * ra});
    line(hp, {color: C.navy, width: 1.6, dash: [7, 4], progress: seg(.22, .4)});
  });
  // legend
  const la = seg(.4, .25), LX = PC.x + PC.w - 192, LY = PC.y + 10;
  if (la > 0) {
    ctx.save(); ctx.globalAlpha *= la; ctx.fillStyle = '#fff'; ctx.strokeStyle = C.ink; ctx.lineWidth = 1;
    ctx.fillRect(LX, LY, 184, 54); ctx.strokeRect(LX, LY, 184, 54); ctx.restore();
    line([[LX + 10, LY + 18], [LX + 38, LY + 18]], {color: C.navy, width: 1.6, dash: [7, 4], alpha: la});
    text('unknown system', LX + 46, LY + 23.5, {size: 16, alpha: la});
    line([[LX + 10, LY + 39], [LX + 38, LY + 39]], {color: C.blue, width: 2.4, alpha: la});
    text('adaptive filter', LX + 46, LY + 44.5, {size: 16, alpha: la});
  }
}

function draw() {
  const {n: nf, a: ra} = nNow();
  panelA(nf, ra);
  panelB(nf, ra);
  panelC(nf, ra);
  math(D.params, 20, H - 14, {size: 15, color: C.muted, alpha: seg(.45, .3)});
}
boot();
"""


def system():
    """The unknown system: the resonator's first M samples."""
    p = SM.pole()
    r, th = np.exp(p.real / FS), p.imag / FS
    k = np.arange(M)
    return r, th, r ** k * np.sin(k * th)


def run(h, seed, sx, sv, f32=False):
    """One NLMS identification: input, desired output, errors, weights."""
    rng = np.random.default_rng(seed)
    x = sx * rng.standard_normal(N + M - 1)
    v = sv * rng.standard_normal(N)
    d = np.convolve(x, h)[M - 1:M - 1 + N] + v
    if f32:                                   # the numbers the page gets
        x = x.astype(np.float32).astype(np.float64)
        d = d.astype(np.float32).astype(np.float64)
    w = np.zeros(M)
    W = np.zeros((N + 1, M))
    e = np.zeros(N)
    for n in range(N):
        u = x[n:n + M][::-1]
        e[n] = d[n] - w @ u
        w = w + MU * e[n] * u / (DELTA + u @ u)
        W[n + 1] = w
    return dict(x=x, d=d, v=v, e=e, W=W)


def ensemble(h, sx, sv, runs, n, seed0=1000):
    """e^2(n) of `runs` independent identifications (seeds seed0 ...), run
    side by side: the same draws and the same recursion as run()."""
    X, V = [], []
    for s in range(runs):
        rng = np.random.default_rng(seed0 + s)
        X.append(sx * rng.standard_normal(n + M - 1))
        V.append(sv * rng.standard_normal(n))
    X, V = np.array(X), np.array(V)
    Dd = np.array([np.convolve(x, h)[M - 1:M - 1 + n] for x in X]) + V
    W = np.zeros((runs, M))
    E2 = np.zeros((runs, n))
    msd = np.zeros(n)
    for k in range(n):
        U = X[:, k:k + M][:, ::-1]
        e = Dd[:, k] - np.einsum("ij,ij->i", W, U)
        E2[:, k] = e * e
        W += (MU * e / (DELTA + np.einsum("ij,ij->i", U, U)))[:, None] * U
        msd[k] = np.mean(np.sum((W - h) ** 2, axis=1))
    return E2, W, msd


def build():
    r, th, h = system()
    sx = 1 / np.sqrt((h ** 2).sum())          # unit output power
    sv = np.sqrt(10 ** (-SNR_DB / 10))
    shown = run(h, SEED, sx, sv, f32=True)
    ens = ensemble(h, sx, sv, R, N)[0].mean(0)
    ens_db = 10 * np.log10(ens)
    floor = 10 * np.log10(sv ** 2)
    print(f"r = {r:.6f}, theta = {th:.6f} rad, r^M = {r ** M:.4f}, max h = {h.max():.4f}")
    print(f"mean learning curve: n=0 {ens_db[0]:.2f} dB, n=300 {ens_db[300]:.2f} dB, "
          f"last 100 {10 * np.log10(ens[-100:].mean()):.2f} dB; floor {floor:.1f} dB")
    data = dict(
        m=M, n=N, mu=MU, delta=DELTA, fs=FS, runs=R, speed=round(N / FS / 7.5), hmax=float(np.abs(h).max()), floor=floor,
        x=common.f32(shown["x"]), d=common.f32(shown["d"]), h=common.f32(h), ens=common.f32(ens_db),
        params=(r"\rm{unknown system: the resonator of Figure 1 sampled at %g Hz, its first %d samples;   white input, noise %g dB below }"
                r"d(n)\rm{;   NLMS, }\mu\rm{ = %g}" % (FS, M, SNR_DB, MU)),
    )
    title = "Figure 3: Adaptive filtering used for system identification"
    aria = ("A block diagram: the same input drives an unknown system and an adaptive filter, and the "
            "error between their outputs updates the filter. Inside the filter's box its 48 coefficients, "
            "computed by a real NLMS run, grow from zero onto the unknown system's; the learning curve falls "
            "to the noise floor and the filter's frequency response rises onto the system's resonance.")
    common.build_html("sp-adaptive", title, aria, 1000, 660, data, JS)
    png = common.still("sp-adaptive")
    print("still:", png)
    res = dict(r=r, th=th, h=h, sx=sx, sv=sv, shown=shown, ens=ens, floor=floor)
    validate(res)
    return res


def validate(q):
    """Wiener and NLMS theory against the runs, and the page's own NLMS;
    writes sp_adaptive.check.txt and prints it."""
    r, th, h, sx, sv = q["r"], q["th"], q["h"], q["sx"], q["sv"]
    # 1. the unknown system is the resonator sampled: h_k = h(k / fs)
    e_h = np.abs(h - SM.h(np.arange(M) / FS)).max()
    tail = r ** M
    # 2. the page's own NLMS against numpy on the same float32 numbers
    shown = q["shown"]
    exprs = [f"Array.from(WS.slice({n * M}, {(n + 1) * M}))" for n in (1, 100, 300, N)] + ["Array.from(E)"]
    got = SM.check_page("sp-adaptive", exprs)
    e_w = max(np.abs(g - shown["W"][n]).max() for g, n in zip(got[:4], (1, 100, 300, N)))
    e_e = np.abs(got[4] - shown["e"]).max()
    # 3. the Wiener solution: white input, so w_o = h; the run ends near it
    wn = shown["W"][N]
    dev_db = 20 * np.log10(np.linalg.norm(wn - h) / np.linalg.norm(h))
    # 4. steady state and rate, a long ensemble against NLMS theory
    LONG, RL = 3000, 200
    E2, Wl, msdn = ensemble(h, sx, sv, RL, LONG, seed0=5000)
    mse = E2.mean(0)
    jmin = sv ** 2
    j_ss = mse[1500:].mean()
    # independence theory, Gaussian input: E 1/|u|^2 = 1/(sigma_x^2 (M - 2))
    msd_th = MU * jmin * M / ((2 - MU) * sx ** 2 * (M - 2))
    j_th = jmin + sx ** 2 * msd_th
    msd = msdn[1500:].mean()
    nn = np.arange(40, 250)
    slope = np.polyfit(nn, 10 * np.log10(msdn[nn] - msd_th), 1)[0]
    slope_th = 10 * np.log10(1 - MU * (2 - MU) / M)
    # 5. the page's |H| against numpy's FFT of h
    fgrid = np.linspace(0, FS / 2, 161)
    Hn = np.abs(np.exp(-2j * np.pi * np.outer(fgrid / FS, np.arange(M))) @ h)
    Hpg = SM.check_page("sp-adaptive", ["Array.from(HM)"])[0]
    e_H = np.abs(Hpg - Hn).max()
    ipk = np.argmax(Hn)

    L = []
    say = L.append
    say("Figure 3, adaptive filtering used for system identification: check of tools/numfig/sp_adaptive.py")
    say("")
    say("MODEL")
    say(f"  Unknown system: the resonator of Figure 1 (f_n = {SM.FN:g} Hz, zeta = {SM.ZETA:g}) sampled at")
    say(f"  fs = {FS:g} Hz over its first {M} samples (6 s): h_k = r^k sin(k theta), r = {r:.6f},")
    say(f"  theta = {th:.6f} rad; the response left out after 6 s starts at r^M = {tail:.4f} of the first peak.")
    say(f"  Input: white Gaussian, sigma_x = {sx:.5f}, so the system's output has unit power.")
    say(f"  d(n) = (h * x)(n) + v(n), v white Gaussian {SNR_DB:g} dB below: sigma_v^2 = {sv ** 2:.4g}.")
    say(f"  Adaptive filter: {M} taps from w = 0, NLMS w <- w + mu e u / (delta + |u|^2), mu = {MU:g},")
    say(f"  delta = {DELTA:g}; the input runs before n = 0 so u(0) is full. The run shown: seed {SEED}; the")
    say(f"  mean learning curve: {R} runs, seeds 1000 to {1000 + R - 1} (numpy default_rng).")
    say("")
    say("VALIDATION")
    say(f"  1. h_k against the resonator h(k / fs): largest difference {e_h:.1e}.")
    say("  2. The page runs the same NLMS itself (float32 input and d, double arithmetic); against")
    say(f"     numpy on the same numbers: weights at n = 1, 100, 300, 600 within {e_w:.1e}, errors")
    say(f"     e(n) within {e_e:.1e}.")
    say("  3. Wiener solution: with white input R = sigma_x^2 I and p = sigma_x^2 h, so w_o = h and")
    say(f"     J_min = sigma_v^2 = {10 * np.log10(jmin):.2f} dB. The run shown ends at |w(600) - h| / |h| = {dev_db:.1f} dB.")
    say(f"  4. NLMS independence theory (Gaussian input) against {RL} runs of {LONG} samples (seeds 5000 on),")
    say("     averages over n = 1500 to 3000:")
    say(f"     weight error E|w - h|^2 = {msd:.4e} against mu sigma_v^2 M / ((2 - mu) sigma_x^2 (M - 2)) =")
    say(f"     {msd_th:.4e} ({(msd - msd_th) / msd_th * 100:+.1f} %);")
    say(f"     mean square error {10 * np.log10(j_ss):.2f} dB against J_min + sigma_x^2 E|w - h|^2 = {10 * np.log10(j_th):.2f} dB")
    say(f"     ({10 * np.log10(j_ss / j_th):+.2f} dB).")
    say(f"     Rate: E|w - h|^2 falls {slope:.4f} dB per sample (n = 40 to 250); the theory's")
    say(f"     10 log10(1 - mu(2 - mu)/M) = {slope_th:.4f} dB per sample. The runs converge {(slope - slope_th) / slope_th * 100:.0f} % faster:")
    say("     successive regressors of the delay line share all but one sample, which the")
    say("     independence assumption leaves out.")
    say(f"  5. The page's |H(f)| (a direct sum at 161 frequencies) against numpy: {e_H:.1e}; its peak")
    say(f"     {Hn[ipk]:.3f} at {fgrid[ipk]:.3f} Hz (the damped natural frequency is {SM.FN * np.sqrt(1 - SM.ZETA ** 2):.3f} Hz).")
    say("")
    say("DISPLAY")
    say(f"  {N} samples at {FS:g} Hz (75 s of the record) play in 7.5 s: time sped up 10 times. In (b)")
    say("  this run is e^2 averaged over the last 8 samples (one period of the resonance). The run rests")
    say("  2.6 s at n = 600; what it drew (the filter's coefficients, this run's curve, |W|, the counter)")
    say("  fades out in 0.45 s and back in at n = 0, so nothing rewinds fast. Tick labels, legends and")
    say("  notes at 16 units, the parameter line at 15.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_adaptive.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
