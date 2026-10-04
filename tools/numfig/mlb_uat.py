"""Figure 18b: why repeating one neuron's computation across many neurons lets
a network approximate almost any function (the universal approximation
theorem). The second half of Figure 18, a figure of its own so that each half
fills the screen (mlb_neuron.py is the first: what one neuron computes).

Many tanh neurons added together: f(x) = c + sum_j v_j tanh(w_j (x - m_j)), the
neurons of Figure 18a, one hidden layer, fitted for N = 1 ... 14 by bounded
least squares (scipy, trust region, 20 starts, the analytic Jacobian) to
g(x) = 0.6 sin(4.4 pi x) exp(-0.8 x) + 0.3 sin(10 pi x + 0.3) on [0, 1].
|v_j| <= 0.4, so each neuron adds one modest S shaped step. The reader picks
N; the neurons switch on one at a time, left to right (a neuron off gives -1,
so the piece it adds, v (1 + tanh(w (x - m))), rises from 0, and the sum starts
at c - sum v: the same network, exactly), and the error plot beside it has
every N's error. Untouched, the page tours 3, 7 and 14 neurons. Pointing at a
piece names its neuron (v, w, m); a button builds the sum again.

Run: python tools/numfig/mlb_uat.py [--look] [--refit] [--verify]
  --refit   fit again instead of reading the cached fits (temp directory)
  --verify  the overlap check in the interactive states too, into the check file
"""
import hashlib
import inspect
import json
import os
import shutil
import sys
import tempfile
import threading
import warnings

import numpy as np
from scipy.optimize import least_squares

import common
import mlb_common as mc

warnings.filterwarnings("ignore", category=RuntimeWarning)
NAME = "uat"
L = []
say = L.append

# ------------------------------------------------------------------ the fits
g = lambda x: 0.6 * np.sin(2 * np.pi * 2.2 * x) * np.exp(-0.8 * x) + 0.3 * np.sin(2 * np.pi * 5 * x + 0.3)
X = np.linspace(0, 1, 400)
Y = g(X)
VMAX, NMAX, TRIES = 0.4, 14, 20


def unpack(p, N):
    return p[0], p[1:N + 1], p[N + 1:2 * N + 1], p[2 * N + 1:]


def model(p, N, x):
    c, v, w, mm = unpack(p, N)
    return c + (v[None] * np.tanh(w[None] * (x[:, None] - mm[None]))).sum(1)


def jac(p, N, x):
    c, v, w, mm = unpack(p, N)
    d = x[:, None] - mm[None]
    th = np.tanh(w[None] * d)
    s = 1 - th ** 2
    return np.hstack([np.ones((len(x), 1)), th, v[None] * s * d, -v[None] * s * w[None]])


def fit(N, tries=TRIES, seed=0):
    """Bounded least squares: |v| <= VMAX (each piece a modest S), w in [0.5, 150] (rising),
    m in [-0.1, 1.1]; the first start spaces the steps evenly, the others at random."""
    r = np.random.default_rng(seed)
    lo = np.r_[-6, -VMAX * np.ones(N), np.full(N, .5), np.full(N, -.1)]
    hi = np.r_[6, VMAX * np.ones(N), np.full(N, 150.), np.full(N, 1.1)]
    best = None
    for k in range(tries):
        m0 = np.sort(r.uniform(0, 1, N)) if k else (np.arange(N) + .5) / N
        w0 = np.clip(np.full(N, 2.0 * N) * (1 + .3 * r.standard_normal(N) * (k > 0)), 1, 145)
        edges = np.r_[0, (m0[1:] + m0[:-1]) / 2, 1]
        v0 = np.clip(np.diff(g(edges)) / 2, -.99 * VMAX, .99 * VMAX)
        c0 = np.clip(g(0.0) + v0.sum(), -5.9, 5.9)
        res = least_squares(lambda p: model(p, N, X) - Y, np.r_[c0, v0, w0, m0], jac=lambda p: jac(p, N, X),
                            bounds=(lo, hi), method="trf", max_nfev=20000)
        rms = float(np.sqrt(np.mean(res.fun ** 2)))
        if best is None or rms < best["rms"]:
            best = {"rms": rms, "p": res.x.tolist(), "opt": float(res.optimality),
                    "act": int(np.sum(res.active_mask != 0))}
    return best


# the fits take minutes: kept in the temp directory, keyed by everything that shapes them
KEY = hashlib.sha1((inspect.getsource(fit) + inspect.getsource(model) + inspect.getsource(jac)
                    + repr((VMAX, NMAX, TRIES, X.tolist()[:3], len(X), np.__version__))).encode()).hexdigest()[:12]
CACHE = os.path.join(tempfile.gettempdir(), f"nf-mlb-uat-fits-{KEY}.json")
if os.path.exists(CACHE) and "--refit" not in sys.argv:
    with open(CACHE, encoding="utf-8") as fh:
        FITS = json.load(fh)
    how = f"read from {CACHE} (--refit fits again)"
else:
    FITS = {}
    for N in range(1, NMAX + 1):
        FITS[str(N)] = fit(N)
        print(f"  fitted N = {N}: RMS {FITS[str(N)]['rms']:.4f}")
    with open(CACHE, "w", encoding="utf-8") as fh:
        json.dump(FITS, fh)
    how = "fitted now"

NETS = []
for N in range(1, NMAX + 1):
    F = FITS[str(N)]
    p = np.array(F["p"])
    c, v, w, mm = unpack(p, N)
    o = np.argsort(mm)                          # the pieces in the order they step
    rms = float(np.sqrt(np.mean((model(p, N, X) - Y) ** 2)))
    mx = float(np.max(np.abs(model(p, N, X) - Y)))
    # what each neuron adds as it switches on (its output from -1, off, to tanh): v (1 + tanh),
    # rising from 0; before any is on the output is c - sum v, so the pieces and that level add up
    # to the network exactly: c + sum v tanh = (c - sum v) + sum v (1 + tanh)
    pieces = v[o][None] * (1 + np.tanh(w[o][None] * (X[:, None] - mm[o][None])))
    base = float(c - v.sum())
    NETS.append({"n": N, "c": float(c), "base": base, "v": v[o], "w": w[o], "m": mm[o], "rms": rms, "max": mx,
                 "opt": F["opt"], "act": F["act"], "sumdiff": float(np.max(np.abs(base + pieces.sum(1) - model(p, N, X)))),
                 "part": float(max(np.max(np.abs(base + pieces[:, :k].sum(1))) for k in range(N + 1)))})

# the Jacobian the fits use, against central differences
rj = np.random.default_rng(5)
pj = np.r_[.1, rj.uniform(-.4, .4, 5), rj.uniform(2, 40, 5), rj.uniform(0, 1, 5)]
Jn = np.zeros((len(X), len(pj)))
for q in range(len(pj)):
    dp = np.zeros(len(pj))
    dp[q] = 1e-6
    Jn[:, q] = (model(pj + dp, 5, X) - model(pj - dp, 5, X)) / 2e-6
jerr = float(np.max(np.abs(Jn - jac(pj, 5, X))) / np.max(np.abs(Jn)))

say("nf-mlb-uat: Figure 18b, many neurons approximating a function (Figure 18a is nf-mlb-neuron)")
say("")
say("MANY NEURONS: f(x) = c + sum_j v_j tanh(w_j (x - m_j)), least squares on 400 points of [0, 1]")
say(f"  target g(x) = 0.6 sin(4.4 pi x) exp(-0.8 x) + 0.3 sin(10 pi x + 0.3)")
say(f"  bounded (trust region): |v_j| <= {VMAX}, 0.5 <= w_j <= 150, -0.1 <= m_j <= 1.1, |c| <= 6;")
say(f"  {TRIES} starts per N, the best kept; the fits are cached in the temp directory (--refit fits again)")
say(f"  analytic Jacobian against central differences: largest relative error {jerr:.1e}")
for nt in NETS:
    say(f"  N = {nt['n']:2d}: RMS error {nt['rms']:.4f}, max error {nt['max']:.4f}; first order optimality"
        f" {nt['opt']:.1e} ({nt['act']} bounds active); level and pieces add up to f within {nt['sumdiff']:.0e}")
say("  the page switches the neurons on one at a time, left to right: a neuron off gives -1, so its piece")
say("  v (1 + tanh(w (x - m))) rises from 0 to 2v, and the sum starts at the level c - sum v (all off);")
say(f"  every partial sum stays inside the plot: largest |value| {max(nt['part'] for nt in NETS):.2f} (axis +-1.3)")
mono = all(NETS[q + 1]["rms"] < NETS[q]["rms"] for q in range(NMAX - 1))
say(f"CHECK: the error falls with every neuron added, 1 -> {NMAX}: {mono}")
say(f"CHECK: tanh(u) = 2 sigma(2u) - 1, so these are the sigmoid networks of the earlier figure: its fits gave")
say(f"  RMS 0.1768, 0.0831, 0.0030 for N = 3, 7, 14; these give "
    f"{NETS[2]['rms']:.4f}, {NETS[6]['rms']:.4f}, {NETS[13]['rms']:.4f}")
say("")

# ------------------------------------------------------------------ the page
XS = np.linspace(0, 1, 241)
DATA = {
    "xs": XS, "g": g(XS),
    "nets": [{"n": nt["n"], "base": nt["base"], "v": nt["v"], "w": nt["w"], "m": nt["m"], "rms": nt["rms"]} for nt in NETS],
}

JS = r"""
const D = DATA;
const XSS = D.xs, NX = XSS.length, NETS = D.nets, NMAX = NETS.length;
/* a neuron's piece: what it adds as it switches on, v (1 + tanh(w (x - m))), from 0 to 2v */
const PIE = NETS.map(nt => nt.v.map((v, j) => Float64Array.from(XSS, x => v * (1 + Math.tanh(nt.w[j] * (x - nt.m[j]))))));
const LRMS = NETS.map(nt => Math.log10(nt.rms));

/* ================================================ the reader's choices (explicit state) */
let NSEL = null;      // a number of neurons chosen (or built again): {n, t0, prev}; null: the tour
let HC = 0;           // the chip (or the error plot's marker) under the pointer
let HP = -1;          // the piece pointed at in the plot
let HR = false;       // the pointer is on the button that builds the sum again
function reset() { NSEL = null; HC = 0; HP = -1; HR = false; }

/* ================================================ the clock: 3, 7 and 14 neurons in turn */
const TB = .35, TOURB = [3, 7, 14], BGAP = .45, BHOLD = 4.5;
const stepB = n => Math.min(.55, 4.2 / n), buildB = n => n * stepB(n);
const BDUR = TOURB.map(n => BGAP + buildB(n) + BHOLD), BPER = BDUR.reduce((a, b) => a + b);
const POSTER_T = TB + BDUR[0] + BDUR[1] + BGAP + buildB(14) + .6;   // 14 neurons added up
function bNow() {
  if (NSEL) return NSEL;
  const c0 = Math.max(0, t - TB), cy = Math.floor(c0 / BPER);
  let c = c0 - cy * BPER, i = 0, base = TB + cy * BPER;
  while (i < TOURB.length - 1 && c >= BDUR[i]) { c -= BDUR[i]; base += BDUR[i]; i++; }
  const first = cy === 0 && i === 0;
  return { n: TOURB[i], t0: base, prev: first ? null : { n: TOURB[(i + TOURB.length - 1) % TOURB.length], t0: -1e3, sw: base } };
}
/* draw something as it was at the moment sw (a fit fading out keeps its last state) */
function at(sw, f) { const tt = t; t = sw; try { f(); } finally { t = tt; } }

/* ================================================ the layout */
const YT = 36, CH = { x: 532, y: YT - 18, w: 26, h: 24, gap: 4 };
const RB = { x: CH.x + NMAX * (CH.w + CH.gap) + 14, y: YT - 6, r: 12 };       // build again
const FP = { x: 76, y: 96, w: 540, h: 296 }, EP = { x: 724, y: 96, w: 240, h: 296 };
const pts = Array.from({ length: NX }, () => [0, 0]);
function builtB(st) {                          // pieces added so far, as a real number
  const u = t - st.t0 - BGAP, s = stepB(st.n);
  if (u <= 0) return 0;
  const q = Math.floor(u / s);
  return q >= st.n ? st.n : q + easeInOut(u / s - q);
}
function fitCurves(A, st, fa, grow, hp) {
  const P = PIE[st.n - 1], c = NETS[st.n - 1].base, u = builtB(st), kk = Math.floor(u), fr = u - kk;
  for (let j = 0; j < Math.min(st.n, kk + 1); j++) {
    const sc = j < kk ? 1 : fr; if (sc <= 0) continue;
    for (let i = 0; i < NX; i++) { pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(sc * P[j][i]); }
    const on = j === kk, me = j === hp;
    line(pts, { color: on || me ? C.accent : C.sky, width: me ? 2.6 : on ? 1.8 : 1.1, alpha: (on || me ? 1 : hp >= 0 ? .4 : .75) * fa });
  }
  for (let i = 0; i < NX; i++) {
    let v = c;
    for (let j = 0; j < Math.min(st.n, kk + 1); j++) v += (j < kk ? 1 : fr) * P[j][i];
    pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(v);
  }
  line(pts, { color: C.blue, width: 2.4, alpha: fa, progress: grow });
}

function draw() {
  const la = lab(.06), st = bNow();
  panel('b', 18, YT, { alpha: lab(.04) });
  text('many neurons added together', 52, YT + rise(la), { size: 17, color: C.body, alpha: la });
  // the number of neurons: the reader's choice
  text('number of neurons', CH.x - 12, YT, { size: 15, color: C.body, align: 'right', alpha: la });
  for (let q = 1; q <= NMAX; q++) {
    const x = CH.x + (q - 1) * (CH.w + CH.gap), on = q === st.n, a = lab(.08 + .012 * q);
    rect(x, CH.y, CH.w, CH.h, { fill: on ? C.navy : HC === q ? C.steel : '#fff', stroke: on ? C.navy : C.guide, width: 1, alpha: a });
    text(String(q), x + CH.w / 2, CH.y + 17, { size: 15, color: on ? '#fff' : C.body, align: 'center', alpha: a });
  }
  // build the sum again: a round button with the restart arrow
  if (!STILL) {
    const a = lab(.3), col = HR ? C.navy : C.guide;
    dot(RB.x, RB.y, RB.r, { color: col, fill: HR ? C.steel : '#fff', width: 1.2, alpha: a });
    const arc = []; for (let q = 0; q <= 20; q++) { const an = -.5 + 4.6 * q / 20; arc.push([RB.x + 5.6 * Math.cos(an), RB.y + 5.6 * Math.sin(an)]); }
    line(arc, { color: col, width: 1.5, alpha: a });
    const e = arc[arc.length - 1];
    line([[e[0] - 3.2, e[1] - 1.6], [e[0], e[1]], [e[0] + 1, e[1] - 3.4]], { color: col, width: 1.5, alpha: a });
  }
  // the fit: the target, the pieces, their sum
  const A = axes({ ...FP, xlim: [0, 1], ylim: [-1.3, 1.3], xticks: [0, .25, .5, .75, 1], yticks: [-1, -.5, 0, .5, 1],
                   xfmt: v => v === .5 ? '0.5' : fmt(v), yfmt: v => v === .5 ? '0.5' : v === -.5 ? '−0.5' : fmt(v),
                   xlabel: 'x', progress: seg(.1, .35) });
  const u = builtB(st), done = u >= st.n, hp = done ? HP : -1;
  text(`${st.n} neuron${st.n > 1 ? 's' : ''}`, FP.x, FP.y - 12, { size: 17, alpha: la });
  math(`\\rm{error}\\ \\ ${NETS[st.n - 1].rms.toFixed(3)}`, FP.x + FP.w, FP.y - 12,
       { size: 15, color: C.body, align: 'right', alpha: done ? lab(st.t0 + BGAP + buildB(st.n)) : 0 });
  A.inside(() => {
    line([[FP.x, A.Y(0)], [FP.x + FP.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.2, .3) });
    for (let i = 0; i < NX; i++) { pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(D.g[i]); }
    line(pts, { color: C.guide, width: 1.6, dash: [2.5, 3.5], progress: seg(.15, .4) });
    if (st.prev) { const fo = 1 - seg(st.t0, BGAP * .7); if (fo > 0) at(st.prev.sw, () => fitCurves(A, st.prev, fo, 1, -1)); }
    fitCurves(A, st, st.prev ? seg(st.t0 + BGAP * .5, BGAP * .5) : 1, st.prev ? 1 : seg(.3, .4), hp);
  });
  // the piece pointed at: its neuron's numbers, over the plot's foot
  if (hp >= 0) {
    const nt = NETS[st.n - 1], y = FP.y + FP.h - 14;
    math(`\\rm{neuron}\\ ${hp + 1}:\\ \\ v = ${num(nt.v[hp])},\\ \\ w = ${nt.w[hp].toFixed(1)},\\ \\ m = ${num(nt.m[hp])}`,
         FP.x + FP.w - 12, y, { size: 15, color: C.accent, align: 'right' });
  }
  // the error for every number of neurons, log scale; the one shown glides along it
  const E = axes({ ...EP, xlim: [.5, NMAX + .5], ylim: [-3, 0], xticks: [1, 5, 10, 14], yticks: [-3, -2, -1, 0],
                   yfmt: v => ['0.001', '0.01', '0.1', '1'][v + 3], xlabel: '\\rm{number\\ of\\ neurons}',
                   ylabel: '\\rm{error}', ylabelGap: 50, grid: true, progress: seg(.12, .35) });
  const ep = [];
  for (let q = 1; q <= NMAX; q++) ep.push([E.X(q), E.Y(LRMS[q - 1])]);
  line(ep, { color: C.blue, width: 1.6, progress: seg(.25, .5) });
  for (let q = 1; q <= NMAX; q++) mark('circle', E.X(q), E.Y(LRMS[q - 1]), HC === q ? 4.8 : 3.4,
                                      { fill: HC === q ? C.steel : '#fff', stroke: C.blue, width: 1.3, alpha: seg(.3 + .02 * q, .2) });
  const n0 = st.prev ? st.prev.n : st.n, gl = settle(st.t0, .45), nq = lerp(n0, st.n, Math.min(1, gl));
  const q0 = clamp(Math.floor(nq), 1, NMAX - 1), fq = clamp(nq - q0);
  dot(E.X(nq), E.Y(lerp(LRMS[q0 - 1], LRMS[q0], fq)), 5, { color: '#fff', fill: C.accent, width: 1.4, alpha: seg(.4, .25) });
  // the network's formula over the plot, and which line is which under it
  const lA = lab(.4), ly = FP.y + FP.h + 84;
  math('f(x) = c + \\Sigma_{j} v_{j}\\,\\rm{tanh}(w_{j}(x - m_{j}))', FP.x + FP.w / 2, FP.y - 12, { size: 17, align: 'center', alpha: lA });
  const items = [[C.guide, 1.6, [2.5, 3.5], 'target function'], [C.sky, 1.2, null, 'one neuron’s piece'],
                 [C.accent, 1.8, null, 'the piece being added'], [C.blue, 2.4, null, 'their sum']];
  let lx = FP.x + 22;
  for (const [col, wd, dash, words] of items) {
    line([[lx - 14, ly - 5], [lx + 14, ly - 5]], { color: col, width: wd, dash, alpha: lA });
    lx += 24 + text(words, lx + 22, ly, { size: 15, alpha: lA }) + 40;
  }
  architecture(st);
  text('tanh neurons as in (a), switched on one at a time; each network fitted by least squares to 400 points of the target; error: root mean square',
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
  if (!STILL) text('point at a piece', FP.x + FP.w, FP.y + FP.h + 44, { size: 14, color: C.muted, align: 'right', alpha: lab(.5) });
  place();
}

/* the network chosen, as a network: 1 input, N tanh neurons, 1 linear output, every connection
   drawn; a neuron is blue once its piece is added. Its output bias is base + sum(v), since each
   piece is v (1 + tanh(...)); it has 3N + 1 fitted weights and biases. */
const AR = { y: 520, cy: 654, xi: 240, xh: 490, xo: 800, ri: 13, rh: 5, dy: 13 };
function architecture(st) {
  const n = st.n, nt = NETS[n - 1], a = lab(.5), built = builtB(st);
  cv.dataset.architecture = `1-${n}-1`;
  text(`Selected architecture: 1 input → ${n} hidden neuron${n === 1 ? '' : 's'} → 1 output`, FP.x, AR.y, { size: 18, alpha: a });
  text('input', AR.xi, AR.y + 31, { size: 15, align: 'center', alpha: a });
  text(`${n} tanh neuron${n === 1 ? '' : 's'}`, AR.xh, AR.y + 31, { size: 15, align: 'center', alpha: a });
  text('linear output', AR.xo, AR.y + 31, { size: 15, align: 'center', alpha: a });
  const ys = Array.from({ length: n }, (_, j) => AR.cy + (j - (n - 1) / 2) * AR.dy);
  for (let j = 0; j < n; j++) {
    const col = j < built ? C.blue : C.guide;
    line([[AR.xi + AR.ri, AR.cy], [AR.xh - 8, ys[j]]], { color: col, width: 1, alpha: a * .65 });
    line([[AR.xh + 8, ys[j]], [AR.xo - AR.ri, AR.cy]], { color: col, width: 1, alpha: a * .65 });
  }
  for (let j = 0; j < n; j++) dot(AR.xh, ys[j], AR.rh, { color: C.blue, fill: j < built ? C.steel : '#fff', width: 1.1, alpha: a });
  dot(AR.xi, AR.cy, AR.ri, { color: C.blue, fill: '#fff', width: 1.5, alpha: a });
  dot(AR.xo, AR.cy, AR.ri, { color: C.blue, fill: '#fff', width: 1.5, alpha: a });
  math('x', AR.xi, AR.cy + 5, { size: 16, align: 'center', alpha: a });
  text('g', AR.xo, AR.cy + 5, { size: 16, align: 'center', alpha: a });
  text(`Output bias ${(nt.base + nt.v.reduce((s, v) => s + v, 0)).toFixed(3)}; ${3 * n + 1} fitted parameters`,
       FP.x, AR.cy + 118, { size: 15, color: C.muted, alpha: a });
  text('Every hidden neuron connects to the input and output; weights match the selected fit above.',
       FP.x, AR.cy + 143, { size: 14, color: C.muted, alpha: a });
}

/* ================================================ the reader's hand: pointer and keyboard */
const FIG = document.querySelector('.fig'), KB = { cr: [], rb: null, key: '' };
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
function redraw() { if (!playing) render(); }
const quick = () => REDUCED || STILL;                    // less motion: the sum at once
function chooseN(n, again) {
  const cur = bNow();
  if (!playing && !quick()) setPlay(true);
  NSEL = quick() ? { n, t0: t - 1e3, prev: null } : { n, t0: t, prev: again ? null : { n: cur.n, t0: cur.t0, sw: t } };
  HP = -1; redraw();
}
function hitChip(X, Y) {
  if (Y >= CH.y - 4 && Y <= CH.y + CH.h + 4) {
    const q = Math.floor((X - CH.x + CH.gap / 2) / (CH.w + CH.gap));
    if (q >= 0 && q < NMAX) return q + 1;
  }
  if (X >= EP.x && X <= EP.x + EP.w && Y >= EP.y - 6 && Y <= EP.y + EP.h + 6) {
    const q = Math.round((X - EP.x) / EP.w * NMAX + .5);
    if (q >= 1 && q <= NMAX && Math.abs(X - (EP.x + (q - .5) / NMAX * EP.w)) < 9) return q;
  }
  return 0;
}
const onRB = (X, Y) => !STILL && Math.hypot(X - RB.x, Y - RB.y) < RB.r + 4;
function hitPiece(X, Y) {                      // the piece whose curve passes nearest, within 7 units
  const st = bNow();
  if (builtB(st) < st.n || X < FP.x || X > FP.x + FP.w || Y < FP.y || Y > FP.y + FP.h) return -1;
  const i = Math.round((X - FP.x) / FP.w * (NX - 1)), P = PIE[st.n - 1], A = 1.3, best = { j: -1, d: 7 };
  for (let j = 0; j < st.n; j++) { const y = FP.y + FP.h - (P[j][i] + A) / (2 * A) * FP.h, d = Math.abs(y - Y); if (d < best.d) { best.d = d; best.j = j; } }
  return best.j;
}
if (!STILL) {
  const css = document.createElement('style');
  css.textContent = '.nfk{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;' +
    'outline:none;color:transparent;font:inherit;overflow:hidden}.nfk:focus-visible{outline:2px solid #095A94;outline-offset:2px}';
  document.head.appendChild(css);
  const ctl = FIG.querySelector('.ctl');
  const add = (parent, tag, role, label) => {
    const el = document.createElement(tag); el.className = 'nfk';
    if (tag === 'button') el.type = 'button';
    if (role) el.setAttribute('role', role);
    if (label) el.setAttribute('aria-label', label);
    parent === FIG ? FIG.insertBefore(el, ctl) : parent.appendChild(el);
    return el;
  };
  const gB = document.createElement('div');
  gB.setAttribute('role', 'radiogroup'); gB.setAttribute('aria-label', 'Number of neurons added together');
  FIG.insertBefore(gB, ctl);
  const roving = (list, i, pick) => e => {
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key], n = list.length;
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : d ? (i + d + n) % n : (e.key === 'Enter' || e.key === ' ') ? i : -1;
    if (j < 0) return;
    e.preventDefault(); list[j].focus(); pick(j);
  };
  for (let q = 1; q <= NMAX; q++) {
    const b = add(gB, 'button', 'radio', `${q} neuron${q > 1 ? 's' : ''}`);
    b.addEventListener('keydown', roving(KB.cr, q - 1, j => chooseN(j + 1)));
    KB.cr.push(b);
  }
  KB.rb = add(FIG, 'button', null, 'Add the neurons again, one at a time');
  KB.rb.addEventListener('click', e => { e.stopPropagation(); chooseN(bNow().n, true); });
  cv.addEventListener('pointermove', e => {
    if (e.pointerType !== 'mouse') return;
    const [X, Y] = toUnits(e), hc = hitChip(X, Y), hr = onRB(X, Y), hp = hc || hr ? -1 : hitPiece(X, Y);
    cv.style.cursor = hc || hr || hp >= 0 ? 'pointer' : '';
    if (hc !== HC || hr !== HR || hp !== HP) { HC = hc; HR = hr; HP = hp; redraw(); }
  });
  cv.addEventListener('pointerleave', () => { HC = 0; HR = false; HP = -1; cv.style.cursor = ''; redraw(); });
  // a click on a chip, a marker, the button or a piece is a choice: it must not also pause
  // (the engine toggles on a click of the canvas), so it stops on the way down
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const [X, Y] = toUnits(e), c = hitChip(X, Y), p = hitPiece(X, Y);
    if (c) chooseN(c);
    else if (onRB(X, Y)) chooseN(bNow().n, true);
    else if (p >= 0) { HP = HP === p ? -1 : p; redraw(); }
    else return;
    e.stopPropagation();
  }, true);
}
/* the keyboard's stand-ins sit on what they choose, and say what is chosen */
function place() {
  if (STILL || !KB.rb) return;
  const bs = bNow(), key = cv.clientWidth + ':' + bs.n;
  if (key === KB.key) return;
  KB.key = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  const box = (el, x0, y0, x1, y1) => { el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0); };
  KB.cr.forEach((b, q) => {
    box(b, CH.x + q * (CH.w + CH.gap), CH.y, CH.x + q * (CH.w + CH.gap) + CH.w, CH.y + CH.h);
    b.setAttribute('aria-checked', String(q + 1 === bs.n)); b.tabIndex = q + 1 === bs.n ? 0 : -1;
  });
  box(KB.rb, RB.x - RB.r - 2, RB.y - RB.r - 2, RB.x + RB.r + 2, RB.y + RB.r + 2);
}
boot();
"""

TITLE = ("Figure 18b: Why repeating that computation across many neurons lets a network approximate "
         "almost any function (the universal approximation theorem)")
ARIA = ("Networks of 1 to 14 tanh neurons fitted to one wiggly target function: their pieces added one at a "
        "time, and the error falling as neurons are added, from 0.30 with one neuron to 0.003 with fourteen. "
        "The selected number of neurons also shows its exact 1-N-1 architecture with all input and output "
        "connections.")


def verify(states):
    """The overlap check (engine.js ?overlap) in the states a reader can reach."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = []
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, "nf-mlb-uat.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            br = p.chromium.launch()
            pg = br.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-mlb-uat.html?t=0&overlap")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.evaluate("setPlay(false)")
            clock = pg.evaluate("POSTER_T")
            for name, js in states:
                pg.evaluate(f"() => {{ {js}; render(); }}")
                lab_, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                out.append((name, lab_, cro))
            br.close()
            if errs:
                out.append(("script errors", errs, []))
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out, clock


if __name__ == "__main__":
    print("RMS", [round(nt["rms"], 4) for nt in NETS])
    mc.publish(NAME, TITLE, ARIA, 1000, 830, DATA, JS, look=(0.3, 0.8, 1.6, 3.0, 5.0, 8.0, 12.0, 17.0))
    TB, BGAP, BHOLD = .35, .45, 4.5
    stepB = lambda n: min(.55, 4.2 / n)
    BD = [BGAP + n * stepB(n) + BHOLD for n in (3, 7, 14)]
    POSTER = TB + BD[0] + BD[1] + BGAP + 14 * stepB(14) + .6
    say("THE PAGE")
    say(f"  W = 1000, H = 830. POSTER_T = {POSTER:g} s: 14 neurons added up.")
    say("  Under the plots, the N chosen as a network: its fully connected 1-N-1 topology, a neuron blue once")
    say("  its piece is added, the output bias base + sum(v) and the 3N + 1 fitted parameters.")
    say(f"  The page tours 3, 7 and 14 neurons, {sum(BD):g} s a round; a neuron switches on every")
    say("  min(0.55, 4.2/N) s, the fit is held 4.5 s; the error plot's marker glides to the N shown.")
    say("  A chip or a marker of the error plot chooses N (the click stops before the engine's pause; paused,")
    say("  the page plays again to build it); the round button builds the same N again; pointing at a piece")
    say("  of a finished sum (or tapping it) names its neuron: v, w and m. With less motion, the sum at once.")
    say("  Keyboard: a radio group of 1 to 14 neurons and the button. Touch: a tap chooses.")
    say("  overlap check (engine.js ?overlap) at the poster and every 0.25 s up to it: clean (common.still)")
    if "--verify" in sys.argv:
        states = [(f"{n} neurons, {f:.0%} built, piece {hp}", f"NSEL = {{n: {n}, t0: 60, prev: null}}; HC = {n}; HP = {hp}; "
                   f"t = 60 + {BGAP} + {n * stepB(n) * f}") for n in range(1, NMAX + 1) for f in (.3, .7, 1.2)
                  for hp in ((-1, 0, n - 1) if f > 1 else (-1,))]
        states += [(f"tour, t = {tt:.2f}", f"NSEL = null; HC = 0; HP = -1; t = {tt}") for tt in np.arange(0, 3 * 13, .25)]
        res, clock = verify(states)
        if abs(clock - POSTER) > 1e-9:
            raise RuntimeError(f"the page's POSTER_T {clock} is not the check file's {POSTER}")
        bad = [(nm, a, c) for nm, a, c in res if a or c]
        say(f"  --verify: {len(res)} states: every number of neurons at 30, 70 and 120 per cent built (finished,")
        say(f"  with its first and last piece pointed at) and the tour every 0.25 s: {len(bad)} with collisions")
        for nm, a, c in bad[:12]:
            say(f"    {nm}: {a[:3]} {c[:3]}")
    mc.check(NAME, L)
