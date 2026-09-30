"""Figure 18: what one neuron computes, and why repeating that computation
across many neurons lets a network approximate almost any function (the
universal approximation theorem).

(a) One neuron from Figure 17. Figure 17's iris network (4-5-5-3, tanh hidden
neurons, softmax output) is imported from mlb_mlp.py, its own data, seed and
first weights, and its gradient descent is replayed here epoch by epoch with
its own gradient code, so every weight is Figure 17's (checked bit for bit
against its trained weights and its snapshots). A small copy of that network
marks the neuron explained; the large diagram is that neuron's computation
for Figure 17's held out versicolor flower: each input times its trained
weight, the products summed with the bias, tanh (softmax for an output
neuron, with the other two outputs as they are), the output. A click on
another neuron of the small copy replays its computation. The plot below it
is how the neuron's weights moved in the 300 epochs of training; pointing at
the plot shows the whole neuron as it was at that epoch (the untrained one at
epoch 0), pointing at a weight shows it before and after training.

(b) Many neurons added together: f(x) = c + sum_j v_j tanh(w_j (x - m_j)),
the same tanh neurons, one hidden layer, fitted for N = 1 ... 14 by bounded
least squares (scipy, trust region, 20 starts, the analytic Jacobian) to
g(x) = 0.6 sin(4.4 pi x) exp(-0.8 x) + 0.3 sin(10 pi x + 0.3) on [0, 1].
|v_j| <= 0.4, so each neuron adds one modest S shaped step. The reader picks
N; the neurons switch on one at a time, left to right (a neuron off gives -1,
so the piece it adds, v (1 + tanh(w (x - m))), rises from 0, and the sum starts
at c - sum v: the same network, exactly), and the error plot beside it has
every N's error. Panel (b) keeps its own clock: it tours 3, 7, 14.

Run: python tools/numfig/mlb_neuron.py [--look] [--refit] [--verify]
  --refit   fit (b) again instead of reading the cached fits (temp directory)
  --verify  the overlap check in the interactive states too, into the check file
"""
import decimal
import hashlib
import inspect
import json
import os
import re
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
NAME = "neuron"
L = []
say = L.append

# ------------------------------------------------------------------ (a) Figure 17's network
# Importing mlb_mlp runs Figure 17's model: its data split, seed, first weights and training.
# Its module code also writes Figure 17's check file, which is not this figure's to write.
_write = mc.check
mc.check = lambda name, lines: None
try:
    import mlb_mlp as F17
finally:
    mc.check = _write

SIZES, LR, EPOCHS = F17.SIZES, F17.LR, F17.EPOCHS


def unflat(p):
    """Figure 17's snapshot layout (all weight matrices, row major, then the biases)
    back to its lists of arrays."""
    W, b, o = [], [], 0
    for a, c in zip(SIZES[:-1], SIZES[1:]):
        W.append(p[o:o + a * c].reshape(a, c).copy())
        o += a * c
    for c in SIZES[1:]:
        b.append(p[o:o + c].copy())
        o += c
    return W, b


def flat(W, b):
    return np.concatenate([w.ravel() for w in W] + [v.ravel() for v in b])


# replay the training from Figure 17's first weights with Figure 17's own gradients
W, b = unflat(np.array(F17.snaps[0], dtype=float))
HIST = []
for e in range(EPOCHS + 1):
    HIST.append(flat(W, b))
    if e == EPOCHS:
        break
    GW, Gb = F17.grads(F17.A, F17.ytr, W, b)
    for i in range(3):
        W[i] -= LR * GW[i]
        b[i] -= LR * Gb[i]
HIST = np.array(HIST)
SAME_W = all(np.array_equal(W[i], F17.W[i]) and np.array_equal(b[i], F17.b[i]) for i in range(3))
SAME_S = all(np.array_equal(HIST[F17.SNAP * q], np.asarray(s)) for q, s in enumerate(F17.snaps))
if not (SAME_W and SAME_S):
    raise RuntimeError("Figure 17's training was not replayed exactly: mlb_mlp.py changed how it trains")

# the flower: Figure 17's held out flower 2 of 3
FLI = 1
FL = F17.FL[FLI]
SPECIES = [str(s) for s in F17.iris.target_names]
if SPECIES[FL["sp"]] != "versicolor":
    raise RuntimeError("Figure 17's second flower is no longer the versicolor")
X0 = np.asarray(FL["z"], dtype=float)          # standardized, as the network sees it


def forward(x, p):
    """Every neuron of the network for one flower: pre-activations z and outputs."""
    Wq, bq = unflat(p)
    z1 = x @ Wq[0] + bq[0]
    h1 = np.tanh(z1)
    z2 = h1 @ Wq[1] + bq[1]
    h2 = np.tanh(z2)
    z3 = h2 @ Wq[2] + bq[2]
    pr = F17.softmax(z3[None])[0]
    return z1, h1, z2, h2, z3, pr


# the epochs the page carries: every epoch to 20, every 2nd to 60, then every 5th
EPS = list(range(0, 20)) + list(range(20, 60, 2)) + list(range(60, EPOCHS + 1, 5))
P_S, Z_S, A_S = [], [], []
for e in EPS:
    z1, h1, z2, h2, z3, pr = forward(X0, HIST[e])
    P_S.append(HIST[e])
    Z_S.append(np.r_[z1, z2, z3])
    A_S.append(np.r_[X0, h1, h2, pr])
P_S, Z_S, A_S = np.array(P_S), np.array(Z_S), np.array(A_S)
FIN = len(EPS) - 1
dfl = max(np.max(np.abs(A_S[FIN, 4:9] - FL["h1"])), np.max(np.abs(A_S[FIN, 9:14] - FL["h2"])),
          np.max(np.abs(A_S[FIN, 14:] - FL["p"])))

# the 13 neurons that compute, in the order the page numbers them
NEU = [(Lq, j) for Lq in (1, 2, 3) for j in range(SIZES[Lq])]
OFFW, OFFB = [0, 20, 45], [60, 65, 70]
TOUR = [0, 9, 11]                              # hidden 1 neuron 1, hidden 2 neuron 5, output versicolor


def w_of(s, Lq, i, j):
    return P_S[s, OFFW[Lq - 1] + i * SIZES[Lq] + j]


def b_of(s, Lq, j):
    return P_S[s, OFFB[Lq - 1] + j]


def v_of(s, Lq, i):
    return A_S[s, [0, 4, 9, 14][Lq] + i]


# Figure 17's layout, read from its page script, so the small copy has its proportions
m = re.search(r"const LX = \[([\d.,\s]+)\], YC = (\d+), GAP = (\d+), R = (\d+);", F17.JS)
LX17 = [float(v) for v in m.group(1).split(",")] if m else [196, 392, 588, 760]

# ------------------------------------------------------------------ what the page prints
# The page decodes float32 and prints with JavaScript's toFixed; check that every number it
# can show (any neuron, any carried epoch) reads the same as the float64 value would.


def to_fixed(v, d):
    """JavaScript's num(v, d) of mlb_common: toFixed, half away from zero on the exact binary value."""
    if abs(v) < .5 * 10 ** -d:
        v = 0.0
    q = decimal.Decimal(v).quantize(decimal.Decimal(1).scaleb(-d), rounding=decimal.ROUND_HALF_UP)
    return f"{q:.{d}f}"


f32 = lambda a: np.asarray(a, dtype=np.float32).astype(np.float64)
P32, Z32, A32 = f32(P_S), f32(Z_S), f32(A_S)
shown = differ = 0
for s in range(len(EPS)):
    for k, (Lq, j) in enumerate(NEU):
        n_in = SIZES[Lq - 1]
        for i in range(n_in):
            wi = OFFW[Lq - 1] + i * SIZES[Lq] + j
            xi = [0, 4, 9, 14][Lq - 1] + i
            pairs = [(P_S[s, wi], P32[s, wi]), (A_S[s, xi], A32[s, xi]),
                     (P_S[s, wi] * A_S[s, xi], P32[s, wi] * A32[s, xi])]
            for a, c in pairs:
                shown += 1
                differ += to_fixed(a, 2) != to_fixed(c, 2)
        ai = [0, 4, 9, 14][Lq] + j
        for a, c, d in [(b_of(s, Lq, j), P32[s, OFFB[Lq - 1] + j], 2), (Z_S[s, k], Z32[s, k], 2),
                        (A_S[s, ai], A32[s, ai], 3 if Lq == 3 else 2)]:
            shown += 1
            differ += to_fixed(a, d) != to_fixed(c, d)

say("nf-mlb-neuron: Figure 18, one neuron of Figure 17, and many neurons approximating a function")
say("")
say("(a) ONE NEURON FROM FIGURE 17")
say(f"  Figure 17's network imported from mlb_mlp.py: {SIZES}, tanh, softmax, seed {F17.SEED},")
say(f"  learning rate {LR}, {EPOCHS} epochs of full batch gradient descent on the cross-entropy.")
say(f"  training replayed here from its epoch 0 weights with its own grads(): final weights and biases")
say(f"  equal mlb_mlp's bit for bit: {SAME_W}; its {len(F17.snaps)} snapshots (every {F17.SNAP} epochs) equal: {SAME_S}")
say(f"  (mlb_mlp's own check: back propagation against central differences, largest relative error {F17.worst:.1e})")
say(f"  small copy laid out as Figure 17's LX = {LX17}" + ("" if m else " (WARNING: not found in mlb_mlp.JS, defaults used)"))
say(f"  flower: Figure 17's held out flower {FLI + 1} of 3, {SPECIES[FL['sp']]}, {np.round(FL['raw'], 1).tolist()} cm,")
say(f"  standardized with the training mean and deviation: {np.round(X0, 4).tolist()}")
say(f"  this forward pass against Figure 17's for the same flower (h1, h2, p): largest difference {dfl:.1e}")
say(f"  the page carries {len(EPS)} epochs: 0 to 19, every 2nd to 58, every 5th to {EPOCHS}")
say("")
say("  every neuron at epoch 300 (trained) and epoch 0 (untrained), for this flower:")
for k, (Lq, j) in enumerate(NEU):
    n_in = SIZES[Lq - 1]
    ws = [w_of(FIN, Lq, i, j) for i in range(n_in)]
    xs = [v_of(FIN, Lq - 1, i) for i in range(n_in)]
    z, a = Z_S[FIN, k], A_S[FIN, [0, 4, 9, 14][Lq] + j]
    z0, a0 = Z_S[0, k], A_S[0, [0, 4, 9, 14][Lq] + j]
    act = "softmax" if Lq == 3 else "tanh"
    name = f"output {SPECIES[j]}" if Lq == 3 else f"hidden {Lq} neuron {j + 1}"
    chk = (abs(a - np.tanh(z)) if Lq < 3 else
           abs(a - np.exp(z) / np.exp(Z_S[FIN, 10:13]).sum()))
    say(f"  {name:19s} w = {np.round(ws, 3).tolist()}, b = {b_of(FIN, Lq, j):+.3f}; x = {np.round(xs, 3).tolist()}")
    say(f"  {'':19s} z = {z:+.4f}, {act}: {a:+.4f} (formula {chk:.0e}); epoch 0: z = {z0:+.4f}, output {a0:+.4f}")
say(f"  the three output probabilities sum to {A_S[FIN, 14:].sum():.15f}")
say(f"  the page prints what it decodes (float32, JavaScript toFixed) as float64 would print it:")
say(f"  {shown - differ} of {shown} numbers the same ({differ} differ); inputs, weights, products, biases and z")
say(f"  to 2 decimals, tanh outputs to 2, probabilities to 3")
say("")

# ------------------------------------------------------------------ (b) many neurons
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
CACHE = os.path.join(tempfile.gettempdir(), f"nf-mlb-neuron-fits-{KEY}.json")
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

say("(b) MANY NEURONS: f(x) = c + sum_j v_j tanh(w_j (x - m_j)), least squares on 400 points of [0, 1]")
say(f"  target g(x) = 0.6 sin(4.4 pi x) exp(-0.8 x) + 0.3 sin(10 pi x + 0.3)")
say(f"  bounded (trust region): |v_j| <= {VMAX}, 0.5 <= w_j <= 150, -0.1 <= m_j <= 1.1, |c| <= 6;")
say(f"  {TRIES} starts per N, the best kept; fits {how}")
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
    "eps": EPS, "P": common.f32(P_S), "Z": common.f32(Z_S), "A": common.f32(A_S),
    "wmax": float(F17.DATA["wmax"]), "lx": LX17, "tour": TOUR,
    "cm": np.asarray(FL["raw"], dtype=float), "species": SPECIES,
    "xs": XS, "g": g(XS),
    "nets": [{"n": nt["n"], "base": nt["base"], "v": nt["v"], "w": nt["w"], "m": nt["m"], "rms": nt["rms"]} for nt in NETS],
}

JS = r"""
const D = DATA;
/* ================================================ Figure 17's network at every carried epoch */
const NSMP = D.eps.length, FIN = NSMP - 1;                 // FIN: epoch 300, the trained network
const PAR = b64f32(D.P), ZZ = b64f32(D.Z), AA = b64f32(D.A);
const SZ = [4, 5, 5, 3], OFFW = [0, 20, 45], OFFB = [60, 65, 70], BASE = [0, 4, 9, 14];
const NEU = [];                                            // the 13 neurons that compute
for (let L = 1; L <= 3; L++) for (let j = 0; j < SZ[L]; j++) NEU.push({ L, j });
const wAt = (s, L, i, j) => PAR[s * 73 + OFFW[L - 1] + i * SZ[L] + j];
const bAt = (s, L, j) => PAR[s * 73 + OFFB[L - 1] + j];
const zAt = (s, k) => ZZ[s * 13 + k];
const valAt = (s, L, i) => AA[s * 17 + BASE[L] + i];     // layer 0: the standardized inputs
const outAt = (s, k) => valAt(s, NEU[k].L, NEU[k].j);
/* Figure 17's colours: a weight blue if positive, crimson if negative, its width its size;
   a neuron filled with its value */
const vcol = v => v >= 0 ? mixHex('#FFFFFF', C.blue, clamp(v)) : mixHex('#FFFFFF', K.red, clamp(-v));
const wcol = w => w >= 0 ? C.blue : K.red;
const wfrac = w => Math.min(1, Math.abs(w) / D.wmax);
const LAYER = ['input layer', 'hidden layer 1', 'hidden layer 2', 'output layer'];
const nName = k => NEU[k].L === 3 ? `output layer, ${D.species[NEU[k].j]}` : `${LAYER[NEU[k].L]}, neuron ${NEU[k].j + 1}`;

/* ================================================ the reader's choices (explicit state) */
let SEL = null;       // a neuron chosen: {k, t0, prev: {k, v0, sw}}; null: the tour
let NSEL = null;      // a number of neurons chosen: {n, t0, prev}; null: the tour
let HOV = -1;         // the weight pointed at (its row; n = the bias)
let SCR = -1;         // the epoch pointed at on the training plot (a carried epoch); -1: trained
let HN = -1, HC = 0;  // the small network's neuron and the chip under the pointer
function reset() { SEL = null; NSEL = null; HOV = -1; SCR = -1; }

/* ================================================ the clocks: (a) and (b) keep their own */
const TB = .35, TOURB = [3, 7, 14], BGAP = .45, BHOLD = 4.5;
const stepB = n => Math.min(.55, 4.2 / n), buildB = n => n * stepB(n);
const BDUR = TOURB.map(n => BGAP + buildB(n) + BHOLD), BPER = BDUR.reduce((a, b) => a + b);
const POSTER_T = TB + BDUR[0] + BDUR[1] + BGAP + buildB(14) + .6;   // 14 neurons added up
const PA = Math.ceil(POSTER_T) + 3, TOUR = D.tour;                 // (a) tours its neurons slowly
function aNow() {
  if (SEL) return SEL;
  const i = Math.max(0, Math.floor(t / PA)), nt = TOUR.length;
  return { k: TOUR[i % nt], t0: i * PA, prev: i ? { k: TOUR[(i - 1) % nt], v0: (i - 1) * PA + (i > 1 ? .15 : 0), sw: i * PA } : null };
}
/* a neuron's view starts .15 s after the switch when another view fades out first; prev.v0 is
   where the view fading out had started, prev.sw the moment it was left */
const viewStart = st => st.t0 + (st.prev ? .15 : 0);
function bNow() {
  if (NSEL) return NSEL;
  const c0 = Math.max(0, t - TB), cy = Math.floor(c0 / BPER);
  let c = c0 - cy * BPER, i = 0, base = TB + cy * BPER;
  while (i < TOURB.length - 1 && c >= BDUR[i]) { c -= BDUR[i]; base += BDUR[i]; i++; }
  const first = cy === 0 && i === 0;
  return { n: TOURB[i], t0: base, prev: first ? null : { n: TOURB[(i + TOURB.length - 1) % TOURB.length], t0: -1e3, sw: base } };
}
/* one neuron's computation, seconds after it is chosen: the inputs flow along their weights one
   after another, the products go on to the sum, the bias joins, z goes through the activation */
function simT(n) {
  const f0 = .55, fs = .3, fd = .75, fEnd = f0 + fs * (n - 1) + fd;
  const tb = fEnd + .3, tz = tb + .45, ta = tz + .3, to = ta + .75;
  return { f0, fs, fd, tb, tz, ta, to };
}
/* draw something as it was at the moment sw (a view fading out keeps its last state) */
function at(sw, f) { const tt = t; t = sw; try { f(); } finally { t = tt; } }

/* ================================================ (a) Figure 17's network, small */
const SC = .48, SX0 = 88, SYC = 206, SG = 40, SR = 9;
const SX = D.lx.map(v => SX0 + (v - D.lx[0]) * SC);
const SY = (L, i) => SYC + (i - (SZ[L] - 1) / 2) * SG;
function inputsOf(k, s, T0, fa, draw) {        // the neuron's own connections, flowing with the diagram
  const N = NEU[k], n = SZ[N.L - 1], T = simT(n);
  for (let i = 0; i < n; i++) {
    const w = wAt(s, N.L, i, N.j), fl = draw ? seg(T0 + T.f0 + T.fs * i, T.fd) : 1, wd = .9 + 2.6 * wfrac(w);
    const ends = [[SX[N.L - 1] + SR, SY(N.L - 1, i)], [SX[N.L] - SR, SY(N.L, N.j)]], on = HOV === i && fa >= 1;
    if (on) line(ends, { color: '#fff', width: wd + 5, progress: fl });   // the weight pointed at, lifted
    line(ends, { color: wcol(w), width: on ? wd + 1.4 : wd, alpha: .95 * fa, progress: fl });
  }
}
function smallNet(st, s, T0, fo) {
  const k = st.k, N = NEU[k], T = simT(SZ[N.L - 1]);
  ['input', 'hidden 1', 'hidden 2', 'output'].forEach((h, L) => {
    const a = lab(.03 * L);
    text(h, SX[L], SY(1, 0) - SR - 16 + rise(a), { size: 15, color: C.body, align: 'center', alpha: a });
  });
  // every connection, faint: the neuron's own stand out
  for (let m = 0; m < 3; m++) {
    const pr = seg(.04 + .06 * m, .35);
    for (let i = 0; i < SZ[m]; i++) for (let j = 0; j < SZ[m + 1]; j++) {
      const w = wAt(s, m + 1, i, j), a = wfrac(w);
      line([[SX[m] + SR, SY(m, i)], [SX[m + 1] - SR, SY(m + 1, j)]],
           { color: wcol(w), width: .35 + 1.5 * a, alpha: .12 + .3 * a, progress: pr });
    }
  }
  if (st.prev && fo > 0) at(st.prev.sw, () => inputsOf(st.prev.k, s, st.prev.v0, fo, true));
  inputsOf(k, s, T0, 1, true);
  // the neurons: the inputs of the one explained carry their values, it its own once computed
  for (let L = 0; L < 4; L++) for (let i = 0; i < SZ[L]; i++) {
    const a = settle(.03 + .05 * L + .012 * i, S), me = L === N.L && i === N.j;
    let fill = '#FFFFFF';
    if (L === N.L - 1) fill = mixHex('#FFFFFF', vcol(L ? valAt(s, L, i) : valAt(s, 0, i) / 2), lab(T0 + .1));
    if (me) fill = mixHex('#FFFFFF', vcol(outAt(s, k)), seg(T0 + T.to, .3));
    node(SX[L], SY(L, i), SR * (.6 + .4 * a), { fill, stroke: C.ink, width: me ? 2.6 : 1.2, alpha: a });
    if (me) dot(SX[L], SY(L, i), SR + 4.5, { color: C.ink, fill: null, width: 1, alpha: lab(T0) });
  }
  if (HN >= 0 && HN !== k) dot(SX[NEU[HN].L], SY(NEU[HN].L, NEU[HN].j), SR + 5, { color: C.guide, fill: null, width: 1.4 });
  // the flower's measurements and the three species, as Figure 17 labels them
  D.cm.forEach((v, i) => math(`${v.toFixed(1)}\\,\\rm{cm}`, SX[0] - SR - 8, SY(0, i) + 5,
                              { size: 15, color: C.body, align: 'right', alpha: lab(.1 + .03 * i) }));
  D.species.forEach((sp, j) => text(sp, SX[3] + SR + 10, SY(3, j) + 5, { size: 15, color: C.body, alpha: lab(.2 + .03 * j) }));
  const fa = lab(.3);
  text('held out versicolor flower', SX[0] - 50, SY(1, 4) + SR + 30, { size: 15, color: C.body, alpha: fa });
  if (!STILL) text('click a neuron', SX[3] + 40, SY(1, 4) + SR + 30, { size: 14, color: C.muted, align: 'right', alpha: fa });
}

/* ================================================ (a) the neuron, large */
const XI = 522, XP = 676, XS = 764, YM = 206, ROW = 44, RS = 24;
const BOX = { x: 820, y: YM - 45, w: 90, h: 90 }, XO = 954, RO = 17;
const XW0 = XI + 16, XW1 = XP - 27, XWL = (XW0 + XW1) / 2, XR = XI - 58;   // XR: the column's left edge
const rowY = (i, n) => YM + (i - (n - 1) / 2) * ROW;
function rim(x, y) { const dx = XS - x, dy = YM - y, d = Math.hypot(dx, dy); return [XS - dx / d * RS, YM - dy / d * RS]; }
function neuronView(k, T0, s, fa) {
  const N = NEU[k], n = SZ[N.L - 1], T = simT(n), out = N.L === 3;
  const la = o => lab(T0 + o) * fa, sk = seg(T0 + .02, .35);
  text(nName(k), XR, 64 + rise(la(0)), { size: 17, alpha: la(0) });
  text(`from ${LAYER[N.L - 1]}`, XI, rowY(0, n) - 29, { size: 15, color: C.body, align: 'center', alpha: la(.04) });
  for (let i = 0; i < n; i++) {
    const y = rowY(i, n), w = wAt(s, N.L, i, N.j), x = valAt(s, N.L - 1, i), t1 = T0 + T.f0 + T.fs * i;
    const fl = seg(t1, T.fd), wd = 1.2 + 3 * wfrac(w);
    line([[XW0, y], [XW1, y]], { color: C.rule, width: 1.2, progress: sk, alpha: fa });
    // the input times its weight: an arrow growing to the product, in the weight's colour and width
    if (fl > 0) arrow(XW0, y, lerp(XW0 + 12, XW1, fl), y, { color: wcol(w), width: wd, head: 7 + 1.5 * wd, alpha: .92 * fa });
    // the weight, above its line
    const a = la(.1 + .03 * i), lbl = `w_{${i + 1}} = ${num(w)}`, lw = math(lbl, 0, -1e4, { size: 15, alpha: 0 });
    if (HOV === i) rect(XWL - lw / 2 - 5, y - 26, lw + 10, 20, { fill: C.steel, stroke: null, alpha: a });
    math(lbl, XWL, y - 11, { size: 15, align: 'center', color: HOV === i ? C.ink : C.body, alpha: a });
    // the input
    const na = settle(T0 + .03 * i, S);
    node(XI, y, 15 * (.6 + .4 * na), { fill: '#fff', alpha: na * fa });
    math(`x_{${i + 1}}`, XI, y + 6, { size: 16, align: 'center', alpha: na * fa });
    math(num(x), XI - 22, y + 6, { size: 16, align: 'right', alpha: la(.08 + .03 * i) });
    // the product arrives, then goes on to the sum
    const tp = t1 + T.fd, [ex, ey] = rim(XP + 23, y);
    math(num(w * x), XP, y + 6, { size: 16, align: 'center', alpha: lab(tp) * fa });
    line([[XP + 23, y], [ex, ey]], { color: C.ink, width: 1.1, progress: seg(tp + .05, .22), alpha: fa });
  }
  // the sum, and the bias joining it
  const sa = settle(T0 + .1, S);
  node(XS, YM, RS * (.6 + .4 * sa), { fill: '#fff', alpha: sa * fa });
  math('\\Sigma', XS, YM + 8, { size: 24, align: 'center', alpha: sa * fa });
  arrow(XS, YM + 84, XS, YM + RS + 3, { color: C.ink, width: 1.3, head: 8, alpha: sk * fa });
  const bl = `b = ${num(bAt(s, N.L, N.j))}`, ba = la(.16), bw = math(bl, 0, -1e4, { size: 15, alpha: 0 });
  if (HOV === n) rect(XS - bw / 2 - 5, YM + 89, bw + 10, 20, { fill: C.steel, stroke: null, alpha: ba });
  math(bl, XS, YM + 104, { size: 15, align: 'center', color: HOV === n ? C.ink : C.body, alpha: ba });
  const bp = seg(T0 + T.tb, .4);
  if (bp > 0 && bp < 1) dot(XS, lerp(YM + 84, YM + RS + 3, bp), 3.6, { color: '#fff', fill: C.ink, width: 1.2, alpha: fa });
  math(out ? `z_{${N.j + 1}}` : 'z', XS + 17, YM - RS - 6, { size: 17, alpha: sa * fa });
  // the activation: tanh, or for an output neuron the softmax with the other two outputs as they are
  const xl = out ? [-6, 6] : [-3, 3], yl = out ? [-.12, 1.12] : [-1.15, 1.15];
  const Cz = out ? [0, 1, 2].reduce((acc, q) => q === N.j ? acc : acc + Math.exp(zAt(s, 10 + q)), 0) : 0;
  const f = out ? (z => 1 / (1 + Cz * Math.exp(-z))) : Math.tanh;
  const A = axes({ ...BOX, xlim: xl, ylim: yl, xticks: [], yticks: [], progress: sk, alpha: fa });
  A.inside(() => {
    line([[BOX.x, A.Y(0)], [BOX.x + BOX.w, A.Y(0)]], { color: C.rule, width: 1, alpha: sk * fa });
    const pts = [];
    for (let q = 0; q <= 72; q++) { const z = xl[0] + (xl[1] - xl[0]) * q / 72; pts.push([A.X(z), A.Y(f(z))]); }
    line(pts, { color: C.blue, width: 2.2, progress: seg(T0 + .12, .4), alpha: fa });
  });
  text(out ? 'softmax' : 'tanh', BOX.x + BOX.w / 2, BOX.y - 10, { size: 15, color: C.body, align: 'center', alpha: la(.2) });
  arrow(XS + RS + 2, YM, BOX.x - 3, YM, { color: C.ink, width: 1.3, head: 8, alpha: sk * fa });
  const z = zAt(s, k), av = outAt(s, k), zp = seg(T0 + T.tz, .3);
  if (zp > 0 && zp < 1) dot(lerp(XS + RS + 2, BOX.x - 3, zp), YM, 3.6, { color: '#fff', fill: C.ink, width: 1.2, alpha: fa });
  const op = settle(T0 + T.ta, .4);
  if (op > 0) {                                   // the operating point glides along the curve to z
    const zz = lerp(0, clamp(z, xl[0] + .08, xl[1] - .08), op), px = A.X(zz), py = A.Y(f(zz));
    A.inside(() => line([[px, BOX.y + BOX.h], [px, py]], { color: C.guide, width: 1, dash: [4, 3], alpha: Math.min(1, op) * fa }));
    dot(px, py, 4.4, { color: '#fff', fill: C.accent, width: 1.3, alpha: Math.min(1, op) * fa });
  }
  // the output
  arrow(BOX.x + BOX.w + 3, YM, XO - RO - 3, YM, { color: C.ink, width: 1.3, head: 8, alpha: sk * fa });
  const oq = seg(T0 + T.to - .4, .35);
  if (oq > 0 && oq < 1) dot(lerp(BOX.x + BOX.w + 3, XO - RO - 3, oq), YM, 3.6, { color: '#fff', fill: C.ink, width: 1.2, alpha: fa });
  const oa = settle(T0 + .14, S);
  node(XO, YM, RO * (.6 + .4 * oa), { fill: mixHex('#FFFFFF', vcol(av), seg(T0 + T.to, .3)), alpha: oa * fa });
  text('output', XO, YM - RO - 12, { size: 15, color: C.body, align: 'center', alpha: la(.2) });
  math(out ? av.toFixed(3) : num(av), XO, YM + RO + 24, { size: 17, align: 'center', alpha: lab(T0 + T.to) * fa });
  // the same, as equations
  const EX = XR, EY = 352, zl = out ? `z_{${N.j + 1}}` : 'z';
  const terms = Array.from({ length: n }, (_, i) => `w_{${i + 1}}x_{${i + 1}}`).join(' + ');
  const e1 = math(`${zl} = ${terms} + b`, EX, EY, { size: 16, alpha: la(.22) });
  math(`= ${num(z)}`, EX + e1 + 6, EY, { size: 16, alpha: lab(T0 + T.tz) * fa });
  const e2 = out ? '\\rm{output} = \\rm{exp}(' + zl + ') / (\\rm{exp}(z_{1}) + \\rm{exp}(z_{2}) + \\rm{exp}(z_{3}))'
                 : '\\rm{output} = \\rm{tanh}(z)';
  const w2 = math(e2, EX, EY + 28, { size: 16, alpha: la(.24) });
  math(`= ${out ? av.toFixed(3) : num(av)}`, EX + w2 + 6, EY + 28, { size: 16, alpha: lab(T0 + T.to) * fa });
  if (out) {
    const oth = [0, 1, 2].filter(q => q !== N.j).map(q => `z_{${q + 1}} = ${num(zAt(s, 10 + q))}`).join(',\\ \\ ');
    math(`\\rm{with}\\ \\ ${oth}`, EX, EY + 56, { size: 16, color: C.body, alpha: lab(T0 + T.ta) * fa });
  }
}

/* ================================================ (a) its weights during training */
const TP = { x: 74, y: 380, w: 290, h: 108 };
const TX = e => TP.x + e / 300 * TP.w;
function trajOf(k, i, q) { const N = NEU[k], n = SZ[N.L - 1]; return i < n ? wAt(q, N.L, i, N.j) : bAt(q, N.L, N.j); }
const TRG = [];
function trange(k) {                           // the neuron's weights and bias over training, with room
  if (TRG[k]) return TRG[k];
  const n = SZ[NEU[k].L - 1];
  let lo = 0, hi = 0;
  for (let i = 0; i <= n; i++) for (let q = 0; q < NSMP; q++) { const v = trajOf(k, i, q); lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const pad = .1 * (hi - lo) + .06; lo -= pad; hi += pad;
  const st = hi - lo > 1.6 ? 1 : .5, ticks = [];
  for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) ticks.push(+v.toFixed(2));
  return (TRG[k] = { lo, hi, ticks });
}
const TYv = (k, v) => { const r = trange(k); return TP.y + TP.h - (v - r.lo) / (r.hi - r.lo) * TP.h; };
function trainPlot(k, T0, ey) {
  const N = NEU[k], n = SZ[N.L - 1], la = lab(.12), R = trange(k);
  text('its weights during training', TP.x - 56, TP.y - 16 + rise(la), { size: 16, color: C.body, alpha: la });
  const G = axes({ ...TP, xlim: [0, 300], ylim: [R.lo, R.hi], xticks: [0, 100, 200, 300], yticks: R.ticks,
                   xlabel: '\\rm{epoch}', progress: seg(.08, .35) });
  G.inside(() => {
    line([[TP.x, G.Y(0)], [TP.x + TP.w, G.Y(0)]], { color: C.rule, width: 1 });
    for (let i = 0; i <= n; i++) {
      const pts = [];
      for (let q = 0; q < NSMP; q++) pts.push([G.X(D.eps[q]), G.Y(trajOf(k, i, q))]);
      const col = i < n ? wcol(trajOf(k, i, FIN)) : C.body, on = HOV < 0 || HOV === i;
      line(pts, { color: col, width: HOV === i ? 2.6 : 1.5, alpha: on ? 1 : .3, progress: seg(T0 + .15 + .04 * i, .6), dash: i < n ? null : [5, 3] });
    }
    if (SCR >= 0) line([[G.X(D.eps[SCR]), TP.y], [G.X(D.eps[SCR]), TP.y + TP.h]], { color: C.ink, width: 1, dash: [3, 3] });
  });
  // which line is which: w1 ... wn and b at their trained values, spread so they never touch
  const ends = [], ea = lab(T0 + .5);
  for (let i = 0; i <= n; i++) { const y0 = TYv(k, trajOf(k, i, FIN)); ends.push({ i, y0, y: y0 + 5 }); }
  ends.sort((p, q) => p.y - q.y);
  for (let q = 1; q < ends.length; q++) ends[q].y = Math.max(ends[q].y, ends[q - 1].y + 14);
  const over = ends[ends.length - 1].y - (TP.y + TP.h + 8);
  if (over > 0) for (const e of ends) e.y -= over;
  for (const e of ends) {
    if (Math.abs(e.y - 5 - e.y0) > 2) line([[TP.x + TP.w + 2, e.y0], [TP.x + TP.w + 13, e.y - 5]], { color: C.guide, width: .8, alpha: ea });
    math(e.i < n ? `w_{${e.i + 1}}` : 'b', TP.x + TP.w + 16, e.y, { size: 15, color: HOV === e.i ? C.ink : C.body, alpha: ea });
  }
  // the weight pointed at, before and after training
  if (HOV >= 0 && HOV <= n) {
    const w0 = trajOf(k, HOV, 0), w1 = trajOf(k, HOV, FIN), c = HOV < n ? wcol(w1) : C.body;
    dot(TX(0), TYv(k, w0), 3.6, { color: c, fill: '#fff', width: 1.6 });
    dot(TX(300), TYv(k, w1), 3.6, { color: c, fill: c, width: 1.6 });
    const nm = HOV < n ? `w_{${HOV + 1}}` : 'b';
    math(`${nm}:\\ \\ ${num(w0)}\\ \\rm{before\\ training}\\ \\ \\to\\ \\ ${num(w1)}\\ \\rm{after}`, XR, ey, { size: 16 });
  }
  if (SCR >= 0) for (let i = 0; i <= n; i++)
    dot(TX(D.eps[SCR]), TYv(k, trajOf(k, i, SCR)), 3, { color: '#fff', fill: i < n ? wcol(trajOf(k, i, FIN)) : C.body, width: 1 });
}

function panelA() {
  panel('a', 18, 34, { alpha: lab(0) });
  text('one neuron from Figure 17', 52, 34 + rise(lab(.03)), { size: 17, color: C.body, alpha: lab(.03) });
  const st = aNow(), s = SCR >= 0 ? SCR : FIN, T0 = viewStart(st);
  const fo = st.prev ? 1 - seg(st.t0, .16) : 0;
  smallNet(st, s, T0, fo);
  if (fo > 0) at(st.prev.sw, () => neuronView(st.prev.k, st.prev.v0, s, fo));
  neuronView(st.k, T0, s, 1);
  const ey = 352 + 90;                          // training, a paragraph of its own under the neuron's equations
  const ep = SCR === 0 ? 'before training, epoch 0' : SCR > 0 && SCR < FIN ? `during training, epoch ${D.eps[SCR]}` : 'trained, epoch 300';
  text(ep, 990, 64, { size: 15, color: SCR >= 0 && SCR < FIN ? C.ink : C.muted, align: 'right', alpha: lab(.1) });
  math('\\rm{training:}\\ \\ w ← w - \\eta\\,\\partial L/\\partial w,\\ \\ \\eta\\, = 0.3', XR, ey, { size: 16, color: C.body, alpha: lab(.3) });
  trainPlot(st.k, T0, ey + 28);
  if (!STILL) text('point at the plot', TP.x + TP.w, TP.y - 16, { size: 14, color: C.muted, align: 'right', alpha: lab(.35) });
}

/* ================================================ (b) many neurons added together */
const YB = 600, CH = { x: 546, y: YB - 18, w: 26, h: 24, gap: 4 };
const FP = { x: 76, y: 636, w: 516, h: 200 }, EP = { x: 720, y: 636, w: 244, h: 200 };
const XSS = D.xs, NX = XSS.length, NETS = D.nets, NMAX = NETS.length;
/* a neuron's piece: what it adds as it switches on, v (1 + tanh(w (x - m))), from 0 to 2v */
const PIE = NETS.map(nt => nt.v.map((v, j) => Float64Array.from(XSS, x => v * (1 + Math.tanh(nt.w[j] * (x - nt.m[j]))))));
const LRMS = NETS.map(nt => Math.log10(nt.rms));
const pts = Array.from({ length: NX }, () => [0, 0]);
function builtB(st) {                          // pieces added so far, as a real number
  const u = t - st.t0 - BGAP, s = stepB(st.n);
  if (u <= 0) return 0;
  const q = Math.floor(u / s);
  return q >= st.n ? st.n : q + easeInOut(u / s - q);
}
function fitCurves(A, st, fa, grow) {
  const P = PIE[st.n - 1], c = NETS[st.n - 1].base, u = builtB(st), kk = Math.floor(u), fr = u - kk;
  for (let j = 0; j < Math.min(st.n, kk + 1); j++) {
    const sc = j < kk ? 1 : fr; if (sc <= 0) continue;
    for (let i = 0; i < NX; i++) { pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(sc * P[j][i]); }
    line(pts, { color: j === kk ? C.accent : C.sky, width: j === kk ? 1.8 : 1.1, alpha: (j === kk ? 1 : .75) * fa });
  }
  for (let i = 0; i < NX; i++) {
    let v = c;
    for (let j = 0; j < Math.min(st.n, kk + 1); j++) v += (j < kk ? 1 : fr) * P[j][i];
    pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(v);
  }
  line(pts, { color: C.blue, width: 2.4, alpha: fa, progress: grow });
}
function panelB() {
  const la = lab(.06), st = bNow();
  panel('b', 18, YB, { alpha: lab(.04) });
  text('many neurons added together', 52, YB + rise(la), { size: 17, color: C.body, alpha: la });
  // the number of neurons: the reader's choice
  text('number of neurons', CH.x - 12, YB, { size: 15, color: C.body, align: 'right', alpha: la });
  for (let q = 1; q <= NMAX; q++) {
    const x = CH.x + (q - 1) * (CH.w + CH.gap), on = q === st.n, a = lab(.08 + .012 * q);
    rect(x, CH.y, CH.w, CH.h, { fill: on ? C.navy : HC === q ? C.steel : '#fff', stroke: on ? C.navy : C.guide, width: 1, alpha: a });
    text(String(q), x + CH.w / 2, CH.y + 17, { size: 15, color: on ? '#fff' : C.body, align: 'center', alpha: a });
  }
  // the fit: the target, the pieces, their sum
  const A = axes({ ...FP, xlim: [0, 1], ylim: [-1.3, 1.3], xticks: [0, .5, 1], yticks: [-1, 0, 1],
                   xfmt: v => v === .5 ? '0.5' : fmt(v), xlabel: 'x', progress: seg(.1, .35) });
  const u = builtB(st), done = u >= st.n;
  text(`${st.n} neuron${st.n > 1 ? 's' : ''}`, FP.x, FP.y - 10, { size: 17, alpha: la });
  math(`\\rm{error}\\ \\ ${NETS[st.n - 1].rms.toFixed(3)}`, FP.x + FP.w, FP.y - 10,
       { size: 15, color: C.body, align: 'right', alpha: done ? lab(st.t0 + BGAP + buildB(st.n)) : 0 });
  A.inside(() => {
    line([[FP.x, A.Y(0)], [FP.x + FP.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.2, .3) });
    for (let i = 0; i < NX; i++) { pts[i][0] = A.X(XSS[i]); pts[i][1] = A.Y(D.g[i]); }
    line(pts, { color: C.guide, width: 1.6, dash: [2.5, 3.5], progress: seg(.15, .4) });
    if (st.prev) { const fo = 1 - seg(st.t0, BGAP * .7); if (fo > 0) at(st.prev.sw, () => fitCurves(A, st.prev, fo, 1)); }
    fitCurves(A, st, st.prev ? seg(st.t0 + BGAP * .5, BGAP * .5) : 1, st.prev ? 1 : seg(.3, .4));
  });
  // the error for every number of neurons, log scale; the one shown glides along it
  const E = axes({ ...EP, xlim: [.5, NMAX + .5], ylim: [-3, 0], xticks: [1, 5, 10, 14], yticks: [-3, -2, -1, 0],
                   yfmt: v => ['0.001', '0.01', '0.1', '1'][v + 3], xlabel: '\\rm{number\\ of\\ neurons}',
                   ylabel: '\\rm{error}', ylabelGap: 50, grid: true, progress: seg(.12, .35) });
  const ep = [];
  for (let q = 1; q <= NMAX; q++) ep.push([E.X(q), E.Y(LRMS[q - 1])]);
  line(ep, { color: C.blue, width: 1.6, progress: seg(.25, .5) });
  for (let q = 1; q <= NMAX; q++) mark('circle', E.X(q), E.Y(LRMS[q - 1]), HC === q ? 4.6 : 3.2,
                                      { fill: '#fff', stroke: C.blue, width: 1.3, alpha: seg(.3 + .02 * q, .2) });
  const n0 = st.prev ? st.prev.n : st.n, g = settle(st.t0, .45), nq = lerp(n0, st.n, Math.min(1, g));
  const q0 = clamp(Math.floor(nq), 1, NMAX - 1), fq = clamp(nq - q0);
  dot(E.X(nq), E.Y(lerp(LRMS[q0 - 1], LRMS[q0], fq)), 5, { color: '#fff', fill: C.accent, width: 1.4, alpha: seg(.4, .25) });
  // legend
  const ly = FP.y + FP.h + 80, lA = lab(.4);
  const items = [[(x, y, a) => line([[x - 14, y], [x + 14, y]], { color: C.guide, width: 1.6, dash: [2.5, 3.5], alpha: a }), 'target function'],
                 [(x, y, a) => line([[x - 14, y], [x + 14, y]], { color: C.sky, width: 1.2, alpha: a }), 'one neuron’s piece'],
                 [(x, y, a) => line([[x - 14, y], [x + 14, y]], { color: C.accent, width: 1.8, alpha: a }), 'the piece being added'],
                 [(x, y, a) => line([[x - 14, y], [x + 14, y]], { color: C.blue, width: 2.4, alpha: a }), 'their sum']];
  let lx = 180;
  for (const [key, words] of items) { key(lx, ly - 5, lA); lx += 24 + text(words, lx + 22, ly, { size: 15, alpha: lA }) + 40; }
}

function draw() {
  panelA();
  text('network of Figure 17 (iris, 4-5-5-3, tanh, softmax, 300 epochs of gradient descent); inputs standardized; values rounded',
       18, 564, { size: 14, color: C.muted, alpha: lab(.5) });
  panelB();
  text('tanh neurons as in (a), switched on one at a time; each network fitted by least squares to 400 points of the target; error: root mean square',
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
  place();
}

/* ================================================ the reader's hand: pointer and keyboard */
const FIG = document.querySelector('.fig'), KB = { nr: [], wb: [], cr: [], sl: null, key: '' };
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
function redraw() { if (!playing) render(); }
const quick = () => REDUCED || STILL || !playing;         // paused, or less motion: switch at once
function chooseNeuron(k) {
  const cur = aNow();
  SEL = quick() ? { k, t0: t - 1e3, prev: null } : { k, t0: t, prev: { k: cur.k, v0: viewStart(cur), sw: t } };
  HOV = -1; redraw();
}
function holdA() { if (!SEL) SEL = aNow(); }    // exploring (a) holds its tour where it is: nothing moves
function chooseN(n) {
  const cur = bNow();
  NSEL = quick() ? { n, t0: t - 1e3, prev: null } : { n, t0: t, prev: { n: cur.n, t0: cur.t0, sw: t } };
  redraw();
}
function hitNode(X, Y) {
  for (let k = 0; k < NEU.length; k++) if (Math.hypot(X - SX[NEU[k].L], Y - SY(NEU[k].L, NEU[k].j)) < 18) return k;
  return -1;
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
function hitWeight(X, Y) {
  const N = NEU[aNow().k], n = SZ[N.L - 1];
  for (let i = 0; i < n; i++) if (X > XI - 64 && X < XP + 26 && Math.abs(Y - rowY(i, n)) < 19) return i;
  if (Math.abs(X - XS) < 42 && Y > YM + RS + 4 && Y < YM + 112) return n;
  return -1;
}
const inTrain = (X, Y) => X >= TP.x - 3 && X <= TP.x + TP.w + 3 && Y >= TP.y - 3 && Y <= TP.y + TP.h + 3;
const onNeuron = (X, Y) => Math.hypot(X - XS, Y - YM) < RS + 4 || Math.hypot(X - XO, Y - YM) < RO + 5;
function sampleAt(X) {
  const e = clamp((X - TP.x) / TP.w) * 300;
  let best = 0;
  for (let q = 1; q < NSMP; q++) if (Math.abs(D.eps[q] - e) < Math.abs(D.eps[best] - e)) best = q;
  return best;
}
function nearLine(Y, q) {                       // the weight whose line passes nearest, within 9 units
  const N = NEU[aNow().k], n = SZ[N.L - 1];
  let best = -1, bd = 9;
  for (let i = 0; i <= n; i++) { const d = Math.abs(TYv(aNow().k, trajOf(aNow().k, i, q)) - Y); if (d < bd) { bd = d; best = i; } }
  return best;
}
let DRAG = false, LASTP = 'mouse';
if (!STILL) {
  const css = document.createElement('style');
  css.textContent = '.nfk{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;' +
    'outline:none;color:transparent;font:inherit;overflow:hidden}.nfk:focus-visible{outline:2px solid #095A94;outline-offset:2px}' +
    '.nfk[hidden]{display:none}';
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
  const group = label => { const g = document.createElement('div'); g.setAttribute('role', 'radiogroup'); g.setAttribute('aria-label', label); FIG.insertBefore(g, ctl); return g; };
  const roving = (list, i, pick) => e => {
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key], n = list.length;
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : d ? (i + d + n) % n : (e.key === 'Enter' || e.key === ' ') ? i : -1;
    if (j < 0) return;
    e.preventDefault(); list[j].focus(); pick(j);
  };
  const gA = group('Neuron of Figure 17 to explain');
  NEU.forEach((N, k) => {
    const b = add(gA, 'button', 'radio', nName(k));
    b.style.borderRadius = '50%';
    b.addEventListener('keydown', roving(KB.nr, k, j => chooseNeuron(j)));
    KB.nr.push(b);
  });
  for (let i = 0; i < 6; i++) {
    const b = add(FIG, 'button', null, '');
    b.addEventListener('focus', () => { holdA(); HOV = i; redraw(); });
    b.addEventListener('blur', () => { HOV = -1; redraw(); });
    KB.wb.push(b);
  }
  KB.sl = add(FIG, 'div', 'slider', 'Epoch of training shown: arrows move through the epochs');
  KB.sl.tabIndex = 0;
  KB.sl.setAttribute('aria-valuemin', '0'); KB.sl.setAttribute('aria-valuemax', '300');
  KB.sl.addEventListener('focus', () => { holdA(); SCR = FIN; redraw(); });
  KB.sl.addEventListener('blur', () => { SCR = -1; redraw(); });
  KB.sl.addEventListener('keydown', e => {
    const d = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 10, PageDown: -10 }[e.key];
    const q = e.key === 'Home' ? 0 : e.key === 'End' ? FIN : d ? clamp((SCR < 0 ? FIN : SCR) + d, 0, FIN) : -1;
    if (q < 0) return;
    e.preventDefault(); SCR = q; redraw();
  });
  const gB = group('Number of neurons added together');
  for (let q = 1; q <= NMAX; q++) {
    const b = add(gB, 'button', 'radio', `${q} neuron${q > 1 ? 's' : ''}`);
    b.addEventListener('keydown', roving(KB.cr, q - 1, j => chooseN(j + 1)));
    KB.cr.push(b);
  }
  cv.style.touchAction = 'pan-y';
  cv.addEventListener('pointermove', e => {
    const [X, Y] = toUnits(e);
    if (DRAG) { SCR = sampleAt(X); redraw(); return; }
    if (e.pointerType !== 'mouse') return;
    let cur = '', hn = hitNode(X, Y), hc = hitChip(X, Y), hw = -1, sc = -1;
    if (inTrain(X, Y)) { sc = sampleAt(X); hw = nearLine(Y, sc); cur = 'crosshair'; }
    else if (onNeuron(X, Y)) sc = 0;            // the neuron itself: as it was before training
    else hw = hitWeight(X, Y);
    if (hn >= 0 || hc || hw >= 0 || (sc === 0 && !inTrain(X, Y))) cur = cur || 'pointer';
    cv.style.cursor = cur;
    if (hw >= 0 || sc >= 0) holdA();
    if (hn !== HN || hc !== HC || hw !== HOV || sc !== SCR) { HN = hn; HC = hc; HOV = hw; SCR = sc; redraw(); }
  });
  cv.addEventListener('pointerleave', () => { if (DRAG) return; HN = -1; HC = 0; HOV = -1; SCR = -1; cv.style.cursor = ''; redraw(); });
  cv.addEventListener('pointerdown', e => {
    LASTP = e.pointerType;
    const [X, Y] = toUnits(e);
    if (e.pointerType !== 'mouse' && inTrain(X, Y)) { holdA(); DRAG = true; cv.setPointerCapture(e.pointerId); SCR = sampleAt(X); redraw(); }
  });
  const drop = () => { if (DRAG) { DRAG = false; SCR = -1; redraw(); } };
  cv.addEventListener('pointerup', drop);
  cv.addEventListener('pointercancel', drop);
  // a click on a neuron, a chip, a weight or the plot is a choice: it must not also pause
  // (the engine toggles on a click of the canvas), so it stops on the way down
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const [X, Y] = toUnits(e);
    const k = hitNode(X, Y), c = hitChip(X, Y), w = hitWeight(X, Y);
    if (k >= 0) chooseNeuron(k);
    else if (c) chooseN(c);
    else if (w >= 0) { holdA(); if (LASTP !== 'mouse') { HOV = HOV === w ? -1 : w; redraw(); } }
    else if (onNeuron(X, Y)) { holdA(); if (LASTP !== 'mouse') { SCR = SCR === 0 ? -1 : 0; redraw(); } }
    else if (!inTrain(X, Y)) return;
    e.stopPropagation();
  }, true);
}
/* the keyboard's stand-ins sit on what they choose, and say what is chosen */
function place() {
  if (STILL || !KB.sl) return;
  const st = aNow(), bs = bNow(), N = NEU[st.k], n = SZ[N.L - 1], s = SCR >= 0 ? SCR : FIN;
  const key = cv.clientWidth + ':' + st.k + ':' + bs.n + ':' + s;
  if (key === KB.key) return;
  KB.key = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  const box = (el, x0, y0, x1, y1) => { el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0); };
  KB.nr.forEach((b, k) => {
    const x = SX[NEU[k].L], y = SY(NEU[k].L, NEU[k].j);
    box(b, x - SR - 3, y - SR - 3, x + SR + 3, y + SR + 3);
    b.setAttribute('aria-checked', String(k === st.k)); b.tabIndex = k === st.k ? 0 : -1;
  });
  KB.wb.forEach((b, i) => {
    b.hidden = i > n;
    if (i > n) return;
    const y = i < n ? rowY(i, n) : YM + 98;
    if (i < n) box(b, XWL - 42, y - 28, XWL + 42, y + 5); else box(b, XS - 36, y - 12, XS + 36, y + 10);
    const w0 = trajOf(st.k, i, 0), w1 = trajOf(st.k, i, FIN);
    b.setAttribute('aria-label', `${i < n ? 'weight ' + (i + 1) : 'bias'} of ${nName(st.k)}: ${num(w0)} before training, ${num(w1)} after`);
  });
  box(KB.sl, TP.x, TP.y, TP.x + TP.w, TP.y + TP.h);
  KB.sl.setAttribute('aria-valuenow', String(D.eps[s]));
  KB.sl.setAttribute('aria-valuetext', `epoch ${D.eps[s]}: ${nName(st.k)} gives ${NEU[st.k].L === 3 ? outAt(s, st.k).toFixed(3) : num(outAt(s, st.k))}`);
  KB.cr.forEach((b, q) => {
    box(b, CH.x + q * (CH.w + CH.gap), CH.y, CH.x + q * (CH.w + CH.gap) + CH.w, CH.y + CH.h);
    b.setAttribute('aria-checked', String(q + 1 === bs.n)); b.tabIndex = q + 1 === bs.n ? 0 : -1;
  });
}
boot();
"""

TITLE = ("Figure 18: What one neuron computes, and why repeating that computation across many neurons "
         "lets a network approximate almost any function (the universal approximation theorem)")
ARIA = ("Top: the iris network of Figure 17 with one neuron marked, and that neuron's own computation for a held "
        "out versicolor flower: its inputs times its trained weights, summed with its bias, passed through tanh "
        "(softmax for an output neuron) to its output, with a small plot of how its weights moved during the 300 "
        "training epochs; choosing another neuron replays its computation. Bottom: networks of 1 to 14 tanh "
        "neurons fitted to one wiggly target function, their pieces added one at a time, the error falling as "
        "neurons are added, from 0.30 with one neuron to 0.003 with fourteen.")


def verify(states):
    """The overlap check (engine.js ?overlap) in the states a reader can reach: each state is a
    script run on the page, then the frame is drawn and its collisions read."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = []
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, "nf-mlb-neuron.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            br = p.chromium.launch()
            pg = br.new_page(viewport={"width": 672, "height": 1400}, device_scale_factor=1)
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-mlb-neuron.html?t=0&overlap")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.evaluate("setPlay(false)")
            clocks = pg.evaluate("[POSTER_T, PA]")
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
    return out, clocks


if __name__ == "__main__":
    print("RMS", [round(nt["rms"], 4) for nt in NETS])
    mc.publish(NAME, TITLE, ARIA, 1000, 970, DATA, JS,
               look=(0.3, 0.8, 1.4, 2.2, 3.0, 4.0, 5.0, 8.0, 12.0, 17.0, 21.0))
    # the page's clocks, as its script sets them (checked against the page under --verify)
    TB, BGAP, BHOLD = .35, .45, 4.5
    stepB = lambda n: min(.55, 4.2 / n)
    BD = [BGAP + n * stepB(n) + BHOLD for n in (3, 7, 14)]
    POSTER = TB + BD[0] + BD[1] + BGAP + 14 * stepB(14) + .6
    PA = int(np.ceil(POSTER)) + 3
    sim = lambda n: .55 + .3 * (n - 1) + .75 + .3 + .45 + .3 + .75 + .3
    say("THE PAGE")
    say(f"  W = 1000, H = 970. POSTER_T = {POSTER:g} s: in (b) 14 neurons added up, in (a) the first neuron computed.")
    say(f"  (a) tours hidden 1 neuron 1, hidden 2 neuron 5 and the versicolor output, {PA} s each. A neuron's")
    say(f"  computation takes {sim(4):.1f} s (4 inputs) or {sim(5):.1f} s (5): each input's arrow grows along its weight in")
    say("  0.75 s, 0.3 s after the one before; its product arrives and goes on to the sum; the bias joins;")
    say("  z goes to the activation, where the operating point glides along the curve (Motion spring, 0.4 s,")
    say("  no bounce); the output node fills. The small copy's connections flow with the large diagram.")
    say(f"  (b) keeps its own clock: 3, 7 and 14 neurons in turn, {sum(BD):g} s a round; a neuron switches on every")
    say("  min(0.55, 4.2/N) s, the fit is held 4.5 s; the error plot's marker glides to the N shown.")
    say("  A click on a neuron of the small copy, a chip or a marker of the error plot chooses (the click")
    say("  stops before the engine's pause); paused, or with less motion, the choice is made at once. Pointing")
    say("  at a weight (large diagram or plot) shows it before and after training; at the plot, the whole")
    say(f"  network at that epoch (the page carries {len(EPS)}); at the neuron itself, the neuron before training.")
    say("  Keyboard: a radio group of the 13 neurons, one stop per weight and the bias, a slider of epochs on")
    say("  the plot, a radio group of 1 to 14 neurons. Touch: a tap chooses, a drag on the plot scrubs.")
    say("  overlap check (engine.js ?overlap) at the poster and every 0.25 s up to it: clean (common.still)")
    if "--verify" in sys.argv:
        states = [("page clocks", "")]
        for k in range(13):
            n_in = SIZES[NEU[k][0] - 1]
            for q in (-1, 0, 10, 30, 60, FIN):
                for h in (-1, 0, n_in - 1, n_in):
                    states.append((f"neuron {k}, epoch {EPS[q] if q >= 0 else 'trained'}, weight {h}",
                                   f"t = 70; SEL = {{k: {k}, t0: t - 1e3, prev: null}}; SCR = {q}; HOV = {h}; HN = {(k + 5) % 13}"))
        states += [(f"{n} neurons, {f:.0%} built", f"SEL = null; SCR = -1; HOV = -1; HN = -1; NSEL = {{n: {n}, t0: 60, prev: null}}; HC = {n}; "
                    f"t = 60 + {BGAP} + {n * stepB(n) * f}") for n in range(1, NMAX + 1) for f in (.3, .7, 1.2)]
        states += [(f"neuron switch, {d:.1f} s in", f"NSEL = null; HC = 0; SEL = {{k: {k2}, t0: 30, prev: {{k: {k1}, v0: 0, sw: 30}}}}; t = {30 + d}")
                   for k1, k2 in ((0, 11), (11, 7), (9, 2)) for d in np.arange(0, 5.01, .1)]
        states += [(f"tour, t = {tt:.2f}", f"SEL = null; NSEL = null; t = {tt}")
                   for tt in list(np.arange(0, 3 * PA + 1, .25))]
        res, clocks = verify(states)
        if abs(clocks[0] - POSTER) > 1e-9 or clocks[1] != PA:
            raise RuntimeError(f"the page's clocks {clocks} are not the check file's ({POSTER}, {PA})")
        bad = [(nm, a, c) for nm, a, c in res if a or c]
        say(f"  --verify: the page's POSTER_T and tour period read back: {clocks[0]:g} s, {clocks[1]} s")
        say(f"  --verify: {len(res)} states: every neuron at epochs trained, 0, 10, 40, 160 and 300 with weights and")
        say("  the bias pointed at, every number of neurons at 30, 70 and 100 per cent built, three neuron")
        say(f"  switches frame by frame (0.1 s), and both tours every 0.25 s for {3 * PA} s: {len(bad)} with collisions")
        for nm, a, c in bad[:12]:
            say(f"    {nm}: {a[:3]} {c[:3]}")
    mc.check(NAME, L)
