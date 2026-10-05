"""Figure 18a: what one neuron computes. The first half of Figure 18, a figure
of its own so that each half fills the screen (mlb_uat.py is the second:
why repeating that computation across many neurons lets a network
approximate almost any function).

Figure 17's iris network (4-5-5-3, tanh hidden neurons, softmax output) is
imported from mlb_mlp.py, its own data, seed and first weights, and its
gradient descent is replayed here epoch by epoch with its own gradient code,
so every weight is Figure 17's (checked bit for bit against its trained
weights and its snapshots). On the left, that network for Figure 17's held out
versicolor flower: the four measurements in a small table beside the input
neurons, every other neuron filled with its value. Every one of the 17
neurons can be chosen. On the right, the chosen neuron's computation: each
input times its trained weight, the products summed with the bias, tanh
(softmax for an output neuron, with the other two outputs as they are), the
output; for an input neuron, the measurement standardized with the training
mean and SD, and handed on along its five weights. Below, how the neuron's
weights moved in the 300 epochs of training, with a slider of the epoch shown
and a button that replays the training: the whole network, the chosen
neuron's numbers and its plot follow the epoch. Untouched, the page tours
four neurons: hidden 1 neuron 1, hidden 2 neuron 5, the versicolor output,
and the petal length input.

Run: python tools/numfig/mlb_neuron.py [--look] [--verify]
  --verify  the overlap check in the interactive states too, into the check file
"""
import decimal
import os
import re
import shutil
import sys
import tempfile
import threading
import warnings

import numpy as np

import common
import mlb_common as mc

warnings.filterwarnings("ignore", category=RuntimeWarning)
NAME = "neuron"
L = []
say = L.append

# ------------------------------------------------------------------ Figure 17's network
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
FEAT = [str(f) for f in F17.DATA["features"]]
if SPECIES[FL["sp"]] != "versicolor":
    raise RuntimeError("Figure 17's second flower is no longer the versicolor")
X0 = np.asarray(FL["z"], dtype=float)          # standardized, as the network sees it
MU, SD = np.asarray(F17.mu, dtype=float), np.asarray(F17.sd, dtype=float)
RAW = np.asarray(FL["raw"], dtype=float)
if np.max(np.abs((RAW - MU) / SD - X0)) > 1e-12:
    raise RuntimeError("Figure 17 no longer standardizes with its training mean and deviation")


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

# all 17 neurons in the order the page numbers them: the inputs, the two hidden layers, the outputs
NEU = [(Lq, j) for Lq in (0, 1, 2, 3) for j in range(SIZES[Lq])]
OFFW, OFFB, BASE = [0, 20, 45], [60, 65, 70], [0, 4, 9, 14]
TOUR = [4, 13, 15, 2]                          # hidden 1 neuron 1, hidden 2 neuron 5, versicolor, petal length


def w_of(s, Lq, i, j):
    return P_S[s, OFFW[Lq - 1] + i * SIZES[Lq] + j]


def b_of(s, Lq, j):
    return P_S[s, OFFB[Lq - 1] + j]


def v_of(s, Lq, i):
    return A_S[s, BASE[Lq] + i]


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
        if Lq == 0:
            continue                            # an input's numbers are hidden 1's inputs, below
        n_in = SIZES[Lq - 1]
        for i in range(n_in):
            wi = OFFW[Lq - 1] + i * SIZES[Lq] + j
            xi = BASE[Lq - 1] + i
            pairs = [(P_S[s, wi], P32[s, wi]), (A_S[s, xi], A32[s, xi]),
                     (P_S[s, wi] * A_S[s, xi], P32[s, wi] * A32[s, xi])]
            for a, c in pairs:
                shown += 1
                differ += to_fixed(a, 2) != to_fixed(c, 2)
        ai = BASE[Lq] + j
        for a, c, d in [(b_of(s, Lq, j), P32[s, OFFB[Lq - 1] + j], 2), (Z_S[s, k - 4], Z32[s, k - 4], 2),
                        (A_S[s, ai], A32[s, ai], 3 if Lq == 3 else 2)]:
            shown += 1
            differ += to_fixed(a, d) != to_fixed(c, d)
# an input's standardization, as the page prints it: the measurement to 1 decimal, the training
# mean and SD to 3 (sent as these strings: the mean of sepal length is 5.8575 exactly, which float64
# holds as 5.857499..., and the page must print what is checked here), the standardized value to 2;
# the printed numbers give the printed value again
CMS, MUS, SDS = ([to_fixed(v, d) for v in a] for a, d in ((RAW, 1), (MU, 3), (SD, 3)))
std_ok = [to_fixed((float(CMS[i]) - float(MUS[i])) / float(SDS[i]), 2) == to_fixed(X0[i], 2) for i in range(4)]

say("nf-mlb-neuron: Figure 18a, one neuron of Figure 17 (Figure 18b is nf-mlb-uat)")
say("")
say("ONE NEURON FROM FIGURE 17")
say(f"  Figure 17's network imported from mlb_mlp.py: {SIZES}, tanh, softmax, seed {F17.SEED},")
say(f"  learning rate {LR}, {EPOCHS} epochs of full batch gradient descent on the cross-entropy.")
say(f"  training replayed here from its epoch 0 weights with its own grads(): final weights and biases")
say(f"  equal mlb_mlp's bit for bit: {SAME_W}; its {len(F17.snaps)} snapshots (every {F17.SNAP} epochs) equal: {SAME_S}")
say(f"  (mlb_mlp's own check: back propagation against central differences, largest relative error {F17.worst:.1e})")
say(f"  flower: Figure 17's held out flower {FLI + 1} of 3, {SPECIES[FL['sp']]}, {np.round(RAW, 1).tolist()} cm,")
say(f"  standardized with the training mean {np.round(MU, 3).tolist()} and SD {np.round(SD, 3).tolist()}:")
say(f"  {np.round(X0, 4).tolist()}")
say(f"  this forward pass against Figure 17's for the same flower (h1, h2, p): largest difference {dfl:.1e}")
say(f"  the page carries {len(EPS)} epochs: 0 to 19, every 2nd to 58, every 5th to {EPOCHS}")
say("")
say("  every neuron at epoch 300 (trained) and epoch 0 (untrained), for this flower:")
for k, (Lq, j) in enumerate(NEU):
    if Lq == 0:
        out0 = [w_of(FIN, 1, j, q) for q in range(SIZES[1])]
        say(f"  input {FEAT[j]:13s}   {RAW[j]:.1f} cm: x = ({RAW[j]:.1f} - {MU[j]:.3f}) / {SD[j]:.3f} = {X0[j]:+.4f};"
            f" weights out = {np.round(out0, 3).tolist()}")
        continue
    n_in = SIZES[Lq - 1]
    ws = [w_of(FIN, Lq, i, j) for i in range(n_in)]
    xs = [v_of(FIN, Lq - 1, i) for i in range(n_in)]
    z, a = Z_S[FIN, k - 4], A_S[FIN, BASE[Lq] + j]
    z0, a0 = Z_S[0, k - 4], A_S[0, BASE[Lq] + j]
    act = "softmax" if Lq == 3 else "tanh"
    name = f"output {SPECIES[j]}" if Lq == 3 else f"hidden {Lq} neuron {j + 1}"
    chk = (abs(a - np.tanh(z)) if Lq < 3 else
           abs(a - np.exp(z) / np.exp(Z_S[FIN, 10:13]).sum()))
    say(f"  {name:19s} w = {np.round(ws, 3).tolist()}, b = {b_of(FIN, Lq, j):+.3f}; x = {np.round(xs, 3).tolist()}")
    say(f"  {'':19s} z = {z:+.4f}, {act}: {a:+.4f} (formula {chk:.0e}); epoch 0: z = {z0:+.4f}, output {a0:+.4f}")
say(f"  the three output probabilities sum to {A_S[FIN, 14:].sum():.15f}")
say(f"  the page prints what it decodes (float32, JavaScript toFixed) as float64 would print it:")
say(f"  {shown - differ} of {shown} numbers the same ({differ} differ); inputs, weights, products, biases and z")
say(f"  to 2 decimals, tanh outputs to 2, probabilities to 3; measurements, mean and SD printed as sent:")
say(f"  {CMS} cm, mean {MUS}, SD {SDS}")
say(f"CHECK: an input's printed standardization, (measurement - mean) / SD in the printed numbers,")
say(f"  gives its printed value again: {all(std_ok)} {std_ok}")
say("")

# ------------------------------------------------------------------ the page
DATA = {
    "eps": EPS, "P": common.f32(P_S), "Z": common.f32(Z_S), "A": common.f32(A_S),
    "wmax": float(F17.DATA["wmax"]), "tour": TOUR,
    "cm": CMS, "mu": MUS, "sd": SDS, "feat": FEAT, "species": SPECIES,
}

JS = r"""
const D = DATA;
/* ================================================ Figure 17's network at every carried epoch */
const NSMP = D.eps.length, FIN = NSMP - 1;                 // FIN: epoch 300, the trained network
const PAR = b64f32(D.P), ZZ = b64f32(D.Z), AA = b64f32(D.A);
const SZ = [4, 5, 5, 3], OFFW = [0, 20, 45], OFFB = [60, 65, 70], BASE = [0, 4, 9, 14];
const NEU = [];                                            // all 17: inputs, hidden 1, hidden 2, outputs
for (let L = 0; L <= 3; L++) for (let j = 0; j < SZ[L]; j++) NEU.push({ L, j });
const NK = NEU.length, kOf = (L, j) => BASE[L] + j, isIn = k => NEU[k].L === 0;
const wAt = (s, L, i, j) => PAR[s * 73 + OFFW[L - 1] + i * SZ[L] + j];
const bAt = (s, L, j) => PAR[s * 73 + OFFB[L - 1] + j];
const zAt = (s, k) => ZZ[s * 13 + k - 4];                  // a computing neuron's pre-activation
const valAt = (s, L, i) => AA[s * 17 + BASE[L] + i];     // layer 0: the standardized inputs
const outAt = (s, k) => valAt(s, NEU[k].L, NEU[k].j);
/* the guide's signed colours (mlb_common): a weight blue if positive, crimson if negative, its
   width its size; a neuron filled with its value, the ends on SIGNED's lightness-matched stops */
const vcol = v => signed(v * 2 / 3);
const wcol = w => w >= 0 ? S_POS : S_NEG;
const wfrac = w => Math.min(1, Math.abs(w) / D.wmax);
const LAYER = ['input layer', 'hidden layer 1', 'hidden layer 2', 'output layer'];
const nName = k => { const N = NEU[k]; return N.L === 0 ? `input layer, ${D.feat[N.j]}` : N.L === 3 ? `output layer, ${D.species[N.j]}` : `${LAYER[N.L]}, neuron ${N.j + 1}`; };
const nRows = k => isIn(k) ? SZ[1] : SZ[NEU[k].L - 1];    // an input's rows: its weights out

/* ================================================ the reader's choices (explicit state) */
let SEL = null;       // a neuron chosen: {k, t0, prev: {k, v0, sw}}; null: the tour
let HOV = -1;         // the weight pointed at (its row in the neuron's view; nRows: the bias)
let EPI = FIN;        // the epoch shown, chosen with the slider (a carried epoch's index)
let HSC = -1;         // the epoch pointed at on the training plot; -1: none
let REP = null;       // the training replayed: {t0}
let HN = -1, HB = ''; // the neuron and the control under the pointer
let DRAG = false;     // the slider's handle held
let DOWN = false;     // the replay chip held down
function reset() { SEL = null; HOV = -1; EPI = FIN; HSC = -1; REP = null; DOWN = false; }
const TAP = matchMedia('(hover: none)').matches;         // a touch screen: the hint says tap
const REPLEN = 6;                                          // the 300 epochs, replayed in 6 s
function nearest(e) { let best = 0; for (let q = 1; q < NSMP; q++) if (Math.abs(D.eps[q] - e) < Math.abs(D.eps[best] - e)) best = q; return best; }
const replaying = () => REP && t >= REP.t0 && t < REP.t0 + REPLEN;
const sNow = () => HSC >= 0 ? HSC : replaying() ? nearest(300 * easeInOut((t - REP.t0) / REPLEN)) : EPI;

/* ================================================ the clock: the tour, a neuron every PA seconds */
const T_IN = .35, PA = 8, TOUR = D.tour;
function aNow() {
  if (SEL) return SEL;
  const u = Math.max(0, t - T_IN), i = Math.floor(u / PA), nt = TOUR.length;
  return { k: TOUR[i % nt], t0: T_IN + i * PA, prev: i ? { k: TOUR[(i - 1) % nt], v0: T_IN + (i - 1) * PA + (i > 1 ? .15 : 0), sw: T_IN + i * PA } : null };
}
/* a neuron's view starts .15 s after the switch when another view fades out first; prev.v0 is
   where the view fading out had started, prev.sw the moment it was left */
const viewStart = st => st.t0 + (st.prev ? .15 : 0);
/* one neuron's computation, seconds after it is chosen: the inputs flow along their weights one
   after another, the products go on to the sum, the bias joins, z goes through the activation */
function simT(n) {
  const f0 = .55, fs = .3, fd = .75, fEnd = f0 + fs * (n - 1) + fd;
  const tb = fEnd + .3, tz = tb + .45, ta = tz + .3, to = ta + .75;
  return { f0, fs, fd, tb, tz, ta, to };
}
/* an input's: the measurement, standardized, then handed on along its five weights */
const SIN = { box: .3, x: .8, f0: 1.1, fs: .22, fd: .6 };
const POSTER_T = T_IN + simT(4).to + .5;                   // the first neuron of the tour computed
/* draw something as it was at the moment sw (a view fading out keeps its last state) */
function at(sw, f) { const tt = t; t = sw; try { f(); } finally { t = tt; } }

/* ================================================ the network, left */
const NX = [164, 244, 324, 404], NYC = 212, NG = 46;
const NR = L => L ? 13 : 12;
const NY = (L, i) => NYC + (i - (SZ[L] - 1) / 2) * NG;
const TBL = { name: 96, val: 144 };                        // the inputs' table: names, then values
function ownEdges(k, s, T0, fa) {                          // the chosen neuron's connections, flowing with its view
  const N = NEU[k];
  if (N.L === 0) {
    for (let j = 0; j < SZ[1]; j++) {
      const w = wAt(s, 1, N.j, j), fl = seg(T0 + SIN.f0 + SIN.fs * j, SIN.fd), wd = .9 + 2.6 * wfrac(w);
      const ends = [[NX[0] + NR(0), NY(0, N.j)], [NX[1] - NR(1), NY(1, j)]], on = HOV === j && fa >= 1;
      if (on) line(ends, { color: '#fff', width: wd + 5, progress: fl });
      line(ends, { color: wcol(w), width: on ? wd + 1.4 : wd, alpha: .95 * fa, progress: fl });
    }
    return;
  }
  const n = SZ[N.L - 1], T = simT(n);
  for (let i = 0; i < n; i++) {
    const w = wAt(s, N.L, i, N.j), fl = seg(T0 + T.f0 + T.fs * i, T.fd), wd = .9 + 2.6 * wfrac(w);
    const ends = [[NX[N.L - 1] + NR(N.L - 1), NY(N.L - 1, i)], [NX[N.L] - NR(N.L), NY(N.L, N.j)]], on = HOV === i && fa >= 1;
    if (on) line(ends, { color: '#fff', width: wd + 5, progress: fl });
    line(ends, { color: wcol(w), width: on ? wd + 1.4 : wd, alpha: .95 * fa, progress: fl });
  }
}
function network(st, s, T0, fo) {
  const k = st.k, N = NEU[k];
  ['input', 'hidden 1', 'hidden 2', 'output'].forEach((h, L) => {
    const a = lab(.03 * L);
    text(h, NX[L], NY(1, 0) - NR(1) - 15 + rise(a), { size: 15, color: C.body, align: 'center', alpha: a });
  });
  // every connection, faint: the chosen neuron's own stand out
  for (let m = 0; m < 3; m++) {
    const pr = seg(.04 + .06 * m, .35);
    for (let i = 0; i < SZ[m]; i++) for (let j = 0; j < SZ[m + 1]; j++) {
      const w = wAt(s, m + 1, i, j), a = wfrac(w);
      line([[NX[m] + NR(m), NY(m, i)], [NX[m + 1] - NR(m + 1), NY(m + 1, j)]],
           { color: wcol(w), width: .35 + 1.5 * a, alpha: .1 + .26 * a, progress: pr });
    }
  }
  if (st.prev && fo > 0) at(st.prev.sw, () => ownEdges(st.prev.k, s, st.prev.v0, fo));
  ownEdges(k, s, T0, 1);
  // the neurons: the inputs plain, with x_i in them; the others filled with their values
  for (let L = 0; L < 4; L++) for (let i = 0; i < SZ[L]; i++) {
    const kk = kOf(L, i), a = settle(.03 + .05 * L + .012 * i, S), me = kk === k, r = NR(L);
    const fill = L ? vcol(valAt(s, L, i)) : '#FFFFFF';
    node(NX[L], NY(L, i), r * (.6 + .4 * a), { fill, stroke: C.ink, width: me ? 2.4 : 1.2, alpha: a });
    if (!L) math(`x_{${i + 1}}`, NX[0] - 1, NY(0, i) + 5, { size: 14, align: 'center', alpha: a });
    if (me) dot(NX[L], NY(L, i), r + 5, { color: C.navy, fill: null, width: 1.6, alpha: lab(T0) });
    else if (HN === kk) dot(NX[L], NY(L, i), r + 5, { color: C.guide, fill: null, width: 1.2 });
  }
  // the flower's four measurements, a small table beside the input neurons
  D.feat.forEach((f, i) => {
    const a = lab(.08 + .03 * i), y = NY(0, i) + 5, on = k === i;
    text(f, TBL.name, y + rise(a), { size: 15, color: on ? C.ink : C.body, align: 'right', alpha: a });
    math(`${D.cm[i]}\\,\\rm{cm}`, TBL.val, y + rise(a), { size: 15, align: 'right', alpha: a });
  });
  D.species.forEach((sp, j) => text(sp, NX[3] + NR(3) + 9, NY(3, j) + 5,
    { size: 15, color: k === kOf(3, j) ? C.ink : C.body, alpha: lab(.2 + .03 * j) }));
  const fa = lab(.3);
  text('held out versicolor flower', 18, NY(1, 4) + NR(1) + 32, { size: 15, color: C.body, alpha: fa });
  if (!STILL) text(TAP ? 'tap any neuron' : 'click any neuron', NX[3] + 84, NY(1, 4) + NR(1) + 32, { size: 14, color: C.muted, align: 'right', alpha: fa });
}

/* ================================================ the chosen neuron, right */
const XR = 525, YM = 238, ROW = 50;
const XI = 590, XS = 800, RS = 25, XO = 966, RO = 16;
const XW0 = XI + 18, XW1 = 698, XWL = (XW0 + XW1) / 2, XP = 726;
const BOX = { x: 850, y: YM - 42, w: 76, h: 84 };
const rowY = (i, n) => YM + (i - (n - 1) / 2) * ROW;
const EY = 402;                                            // the equations
function rim(x, y) { const dx = XS - x, dy = YM - y, d = Math.hypot(dx, dy); return [XS - dx / d * RS, YM - dy / d * RS]; }
function neuronView(k, T0, s, fa) {
  const N = NEU[k], n = SZ[N.L - 1], T = simT(n), out = N.L === 3;
  const la = o => lab(T0 + o) * fa, sk = seg(T0 + .02, .35);
  text(nName(k), XR, 84 + rise(la(0)), { size: 17, color: C.body, alpha: la(0) });
  text(`from ${LAYER[N.L - 1]}`, XI, rowY(0, n) - 30, { size: 15, color: C.body, align: 'center', alpha: la(.04) });
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
  const Cz = out ? [0, 1, 2].reduce((acc, q) => q === N.j ? acc : acc + Math.exp(zAt(s, 14 + q)), 0) : 0;
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
  const zl = out ? `z_{${N.j + 1}}` : 'z';
  const terms = Array.from({ length: n }, (_, i) => `w_{${i + 1}}x_{${i + 1}}`).join(' + ');
  const e1 = math(`${zl} = ${terms} + b`, XR, EY, { size: 17, alpha: la(.22) });
  math(`= ${num(z)}`, XR + e1 + 6, EY, { size: 17, alpha: lab(T0 + T.tz) * fa });
  const e2 = out ? '\\rm{output} = \\rm{exp}(' + zl + ') / (\\rm{exp}(z_{1}) + \\rm{exp}(z_{2}) + \\rm{exp}(z_{3}))'
                 : '\\rm{output} = \\rm{tanh}(z)';
  const w2 = math(e2, XR, EY + 30, { size: 17, alpha: la(.24) });
  math(`= ${out ? av.toFixed(3) : num(av)}`, XR + w2 + 6, EY + 30, { size: 17, alpha: lab(T0 + T.to) * fa });
  if (out) {
    const oth = [0, 1, 2].filter(q => q !== N.j).map(q => `z_{${q + 1}} = ${num(zAt(s, 14 + q))}`).join(',\\ \\ ');
    math(`\\rm{with}\\ \\ ${oth}`, XR, EY + 60, { size: 17, color: C.body, alpha: lab(T0 + T.ta) * fa });
  }
}
/* an input neuron computes nothing: it hands on the measurement, standardized */
const XRAW = 552, IB = { x: 604, y: YM - 23, w: 92, h: 46 }, XN = 744, RN = 16;
const XA0 = 806, XA1 = 880, XAL = (XA0 + XA1) / 2, XPP = 910, XT = 964, RT = 12;
function inputView(k, T0, s, fa) {
  const N = NEU[k], i = N.j, x = valAt(s, 0, i), la = o => lab(T0 + o) * fa, sk = seg(T0 + .02, .35);
  text(nName(k), XR, 84 + rise(la(0)), { size: 17, color: C.body, alpha: la(0) });
  // the measurement, standardized: (x - mu) / sigma
  math(`${D.cm[i]}\\,\\rm{cm}`, XRAW, YM + 6, { size: 16, align: 'center', alpha: la(.05) });
  arrow(XRAW + 25, YM, IB.x - 3, YM, { color: C.ink, width: 1.3, head: 8, alpha: sk * fa });
  rect(IB.x, IB.y, IB.w, IB.h, { fill: '#fff', stroke: C.ink, width: 1.3, alpha: sk * fa });
  math('(x - \\mu) / \\sigma', IB.x + IB.w / 2, YM + 6, { size: 16, align: 'center', alpha: la(SIN.box) });
  const xp = seg(T0 + SIN.box + .1, .4);
  arrow(IB.x + IB.w + 3, YM, IB.x + IB.w + 3 + (XN - RN - 6 - IB.x - IB.w) * xp, YM, { color: C.ink, width: 1.3, head: 8, alpha: (xp > 0 ? 1 : 0) * fa });
  const na = settle(T0 + SIN.x, S);
  node(XN, YM, RN * (.6 + .4 * na), { fill: mixHex('#FFFFFF', vcol(x / 2), na), alpha: na * fa });
  math(`x_{${i + 1}}`, XN, YM + 6, { size: 16, align: 'center', alpha: na * fa });
  math(num(x), XN, YM + RN + 22, { size: 17, align: 'center', alpha: la(SIN.x + .1) });
  // handed on along its five weights, one to each neuron of hidden layer 1
  text('to hidden layer 1', XT, rowY(0, SZ[1]) - 30, { size: 15, color: C.body, align: 'right', alpha: la(.12) });
  for (let j = 0; j < SZ[1]; j++) {
    const y = rowY(j, SZ[1]), w = wAt(s, 1, i, j), t1 = T0 + SIN.f0 + SIN.fs * j;
    const fl = seg(t1, SIN.fd), wd = 1.2 + 3 * wfrac(w);
    line([[XN + RN, YM], [XA0 - 4, y]], { color: C.ink, width: 1.1, progress: seg(t1 - .2, .22), alpha: fa });
    line([[XA0, y], [XA1, y]], { color: C.rule, width: 1.2, progress: sk, alpha: fa });
    if (fl > 0) arrow(XA0, y, lerp(XA0 + 12, XA1, fl), y, { color: wcol(w), width: wd, head: 7 + 1.5 * wd, alpha: .92 * fa });
    const a = la(.14 + .03 * j), lbl = `w = ${num(w)}`, lw = math(lbl, 0, -1e4, { size: 15, alpha: 0 });
    if (HOV === j) rect(XAL - lw / 2 - 5, y - 26, lw + 10, 20, { fill: C.steel, stroke: null, alpha: a });
    math(lbl, XAL, y - 11, { size: 15, align: 'center', color: HOV === j ? C.ink : C.body, alpha: a });
    math(num(w * x), XPP, y + 6, { size: 16, align: 'center', alpha: lab(t1 + SIN.fd) * fa });
    const ta = settle(T0 + .1 + .03 * j, S);
    node(XT, y, RT * (.6 + .4 * ta), { fill: '#fff', alpha: ta * fa });
    text(String(j + 1), XT, y + 5, { size: 14, align: 'center', alpha: ta * fa });
  }
  // the same, as an equation
  math(`x_{${i + 1}} = (${D.cm[i]} - ${D.mu[i]}) / ${D.sd[i]} = ${num(x)}`, XR, EY,
       { size: 17, alpha: la(SIN.x) });
  math('\\mu,\\ \\sigma:\\ \\rm{mean\\ and\\ SD\\ over\\ the\\ training\\ flowers}', XR, EY + 30, { size: 17, color: C.body, alpha: la(SIN.x + .1) });
}
const view = (k, T0, s, fa) => isIn(k) ? inputView(k, T0, s, fa) : neuronView(k, T0, s, fa);

/* ================================================ its weights during training, with the epoch */
const TP = { x: 92, y: 400, w: 330, h: 112 };
const TX = e => TP.x + e / 300 * TP.w;
const SL = { y: TP.y + TP.h + 64, x0: TX(0), x1: TX(300) };
const RP = { x: 18, y: SL.y - 14, w: 58, h: 28 };         // replay: a chip on the slider's left
function trajOf(k, i, q) {
  const N = NEU[k];
  if (N.L === 0) return wAt(q, 1, N.j, i);
  const n = SZ[N.L - 1];
  return i < n ? wAt(q, N.L, i, N.j) : bAt(q, N.L, N.j);
}
const nLines = k => isIn(k) ? SZ[1] : SZ[NEU[k].L - 1] + 1;
const lineName = (k, i) => isIn(k) ? `\\to ${i + 1}` : i < SZ[NEU[k].L - 1] ? `w_{${i + 1}}` : 'b';
const TRG = [];
function trange(k) {                           // the neuron's weights over training, with room
  if (TRG[k]) return TRG[k];
  let lo = 0, hi = 0;
  for (let i = 0; i < nLines(k); i++) for (let q = 0; q < NSMP; q++) { const v = trajOf(k, i, q); lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const pad = .1 * (hi - lo) + .06; lo -= pad; hi += pad;
  const st = Math.floor(hi) - Math.ceil(lo) >= 2 ? 1 : .5, ticks = [];   // whole numbers only where three fit
  for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) ticks.push(+v.toFixed(2));
  return (TRG[k] = { lo, hi, ticks });
}
const TYv = (k, v) => { const r = trange(k); return TP.y + TP.h - (v - r.lo) / (r.hi - r.lo) * TP.h; };
function trainPlot(k, T0, s) {
  const nl = nLines(k), la = lab(.12), R = trange(k), bias = !isIn(k);
  text(isIn(k) ? 'its weights out, during training' : 'its weights during training', TP.x - 70, TP.y - 16 + rise(la), { size: 16, color: C.body, alpha: la });
  const G = axes({ ...TP, xlim: [0, 300], ylim: [R.lo, R.hi], xticks: [0, 100, 200, 300], yticks: R.ticks,
                   progress: seg(.08, .35) });
  G.inside(() => {
    line([[TP.x, G.Y(0)], [TP.x + TP.w, G.Y(0)]], { color: C.rule, width: 1 });
    for (let i = 0; i < nl; i++) {
      const pts = [];
      for (let q = 0; q < NSMP; q++) pts.push([G.X(D.eps[q]), G.Y(trajOf(k, i, q))]);
      const b_ = bias && i === nl - 1, col = b_ ? C.body : wcol(trajOf(k, i, FIN)), on = HOV < 0 || HOV === i;
      line(pts, { color: col, width: HOV === i ? 2.6 : 1.5, alpha: on ? 1 : .3, progress: seg(T0 + .15 + .04 * i, .6), dash: b_ ? [5, 3] : null });
    }
    if (s < FIN) line([[G.X(D.eps[s]), TP.y], [G.X(D.eps[s]), TP.y + TP.h]], { color: C.ink, width: 1, dash: [3, 3] });
  });
  // which line is which, at its trained value, spread so they never touch
  const ends = [], ea = lab(T0 + .5);
  for (let i = 0; i < nl; i++) { const y0 = TYv(k, trajOf(k, i, FIN)); ends.push({ i, y0, y: y0 + 5 }); }
  ends.sort((p, q) => p.y - q.y);
  for (let q = 1; q < ends.length; q++) ends[q].y = Math.max(ends[q].y, ends[q - 1].y + 14);
  const over = ends[ends.length - 1].y - (TP.y + TP.h + 8);
  if (over > 0) for (const e of ends) e.y -= over;
  for (const e of ends) {
    if (Math.abs(e.y - 5 - e.y0) > 2) line([[TP.x + TP.w + 2, e.y0], [TP.x + TP.w + 13, e.y - 5]], { color: C.guide, width: .8, alpha: ea });
    math(lineName(k, e.i), TP.x + TP.w + 16, e.y, { size: 15, color: HOV === e.i ? C.ink : C.body, alpha: ea });
  }
  // the epoch shown: a dot on each line
  if (s < FIN) for (let i = 0; i < nl; i++)
    dot(TX(D.eps[s]), TYv(k, trajOf(k, i, s)), 3, { color: '#fff', fill: bias && i === nl - 1 ? C.body : wcol(trajOf(k, i, FIN)), width: 1 });
  // the weight pointed at, before and after training
  if (HOV >= 0 && HOV < nl) {
    const w0 = trajOf(k, HOV, 0), w1 = trajOf(k, HOV, FIN), c = bias && HOV === nl - 1 ? C.body : wcol(w1);
    dot(TX(0), TYv(k, w0), 3.6, { color: c, fill: '#fff', width: 1.6 });
    dot(TX(300), TYv(k, w1), 3.6, { color: c, fill: c, width: 1.6 });
    const nm = isIn(k) ? `w\\ (\\rm{to\\ neuron}\\ ${HOV + 1})` : lineName(k, HOV);
    math(`${nm}:\\ \\ ${num(w0)}\\ \\rm{before\\ training}\\ \\ \\to\\ \\ ${num(w1)}\\ \\rm{after}`, XR, EY + 104, { size: 17 });
  }
}
function slider(s) {
  if (STILL) return;                            // paper has no slider: the epoch is in the corner
  const a = lab(.35), hx = TX(D.eps[s]);
  line([[SL.x0, SL.y], [SL.x1, SL.y]], { color: C.rule, width: 3, alpha: a });
  line([[SL.x0, SL.y], [hx, SL.y]], { color: C.mist, width: 3, alpha: a });
  for (const e of [0, 100, 200, 300]) line([[TX(e), SL.y - 5], [TX(e), SL.y + 5]], { color: C.rule, width: 1, alpha: a });
  dot(hx, SL.y, HB === 'handle' || DRAG ? 8.5 : 7.5, { color: C.navy, fill: '#fff', width: 2, alpha: a });
  math(`\\rm{epoch}\\ ${D.eps[s]}`, SL.x1 + 20, SL.y + 5, { size: 16, color: s === FIN ? C.body : C.ink, alpha: a });
  // replay the training: a chip in words, not the frame's play glyph; 'stop' while it plays, and
  // pale with less motion, where the slider shows the epochs instead
  const rp = replaying();
  uiChip(RP.x, RP.y, RP.w, RP.h, rp ? 'stop' : 'replay',
         { on: rp, hover: HB === 'play' && !REDUCED, down: DOWN && !REDUCED, off: REDUCED }, a);
}

function draw() {
  panel('a', 18, 36, { alpha: lab(0) });
  text('one neuron from Figure 17', 52, 36 + rise(lab(.03)), { size: 17, color: C.body, alpha: lab(.03) });
  const st = aNow(), s = sNow(), T0 = viewStart(st), fo = st.prev ? 1 - seg(st.t0, .16) : 0;
  network(st, s, T0, fo);
  if (fo > 0) at(st.prev.sw, () => view(st.prev.k, st.prev.v0, s, fo));
  view(st.k, T0, s, 1);
  const ep = s === 0 ? 'before training, epoch 0' : s < FIN ? `during training, epoch ${D.eps[s]}` : 'trained, epoch 300';
  text(ep, 990, 36, { size: 15, color: s < FIN ? C.ink : C.muted, align: 'right', alpha: lab(.1) });
  trainPlot(st.k, T0, s);
  slider(s);
  math('\\rm{training:}\\ \\ w ← w - \\eta\\,\\partial L/\\partial w,\\ \\ \\eta\\ = 0.3', XR, EY + 134, { size: 16, color: C.body, alpha: lab(.3) });
  text('network of Figure 17 (iris, 4-5-5-3, tanh, softmax, 300 epochs of gradient descent); inputs standardized; values rounded',
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
  place();
}

/* ================================================ the reader's hand: pointer and keyboard */
const FIG = document.querySelector('.fig'), KB = { nr: [], wb: [], sl: null, pb: null, key: '' };
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
function redraw() { if (!playing) render(); }
const quick = () => REDUCED || STILL || !playing;         // paused, or less motion: switch at once
function chooseNeuron(k) {
  const cur = aNow();
  SEL = quick() ? { k, t0: t - 1e3, prev: null } : { k, t0: t, prev: { k: cur.k, v0: viewStart(cur), sw: t } };
  HOV = -1; redraw();
}
function holdA() { if (!SEL) SEL = aNow(); }    // exploring holds the tour where it is
function replay() {
  if (REDUCED) return;                          // a replay is motion: drawn off, the slider instead
  holdA();
  if (replaying()) { REP = null; EPI = FIN; redraw(); return; }
  REP = { t0: t }; EPI = FIN; HSC = -1;
  if (!playing) setPlay(true);
}
function chooseEpoch(q) { holdA(); REP = null; EPI = clamp(q, 0, FIN); redraw(); }
/* hit areas as large as the layout allows: a neuron half the 46 unit spacing round it, the replay
   chip and the slider 44 units tall (30 CSS px at 672), the handle 36 units wide */
function hitNode(X, Y) {
  for (let k = 0; k < NK; k++) if (Math.hypot(X - NX[NEU[k].L], Y - NY(NEU[k].L, NEU[k].j)) < 23) return k;
  // an input's row of the table chooses it too
  for (let i = 0; i < 4; i++) if (X > 12 && X < NX[0] && Math.abs(Y - NY(0, i)) < 23) return i;
  return -1;
}
function hitControl(X, Y) {
  if (STILL) return '';
  if (X >= RP.x - 8 && X <= SL.x0 - 12 && Y >= RP.y - 8 && Y <= RP.y + RP.h + 8) return 'play';
  if (Math.abs(Y - SL.y) < 22 && X > SL.x0 - 12 && X < SL.x1 + 12) return Math.abs(X - TX(D.eps[sNow()])) < 18 ? 'handle' : 'track';
  return '';
}
function hitWeight(X, Y) {
  const k = aNow().k, n = nRows(k);
  if (isIn(k)) { for (let j = 0; j < n; j++) if (X > XA0 - 10 && X < XPP + 26 && Math.abs(Y - rowY(j, n)) < 19) return j; return -1; }
  for (let i = 0; i < n; i++) if (X > XI - 64 && X < XP + 26 && Math.abs(Y - rowY(i, n)) < 19) return i;
  if (Math.abs(X - XS) < 42 && Y > YM + RS + 4 && Y < YM + 112) return n;
  return -1;
}
const inTrain = (X, Y) => X >= TP.x - 3 && X <= TP.x + TP.w + 3 && Y >= TP.y - 3 && Y <= TP.y + TP.h + 3;
/* the controls' own ground: the whole left column, where the network, its table and hint, the
   training plot and the slider's row (its label ends near x 512) lie. A click there that misses
   does nothing; on open ground a click still pauses, as in every figure */
const ground = (X, Y) => X < 520;
const epochAt = X => nearest(clamp((X - TP.x) / TP.w) * 300);
function nearLine(Y, q) {                       // the weight whose line passes nearest, within 9 units
  const k = aNow().k;
  let best = -1, bd = 9;
  for (let i = 0; i < nLines(k); i++) { const d = Math.abs(TYv(k, trajOf(k, i, q)) - Y); if (d < bd) { bd = d; best = i; } }
  return best;
}
let LASTP = 'mouse', PRESS = '';   // the pointer's kind; the control a press began on, until its click
if (!STILL) {
  const css = document.createElement('style');
  css.textContent = '.nfk{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;' +
    'outline:none;color:transparent;font:inherit;overflow:hidden}.nfk:focus-visible{outline:2px solid #095A94;outline-offset:2px}' +
    '.nfk[hidden]{display:none}.nfk.nfs:focus-visible{outline-offset:0}';
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
  const roving = (list, i, pick, count = () => list.length) => e => {
    const d = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key], n = count();
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
  // the chosen neuron's weights and bias: one stop, the arrow keys move the highlight along them
  const gW = group('Weights of the chosen neuron'), showW = j => { holdA(); HOV = j; redraw(); };
  for (let i = 0; i < 6; i++) {
    const b = add(gW, 'button', 'radio', '');
    b.addEventListener('focus', () => showW(i));
    b.addEventListener('blur', e => { if (!gW.contains(e.relatedTarget)) { HOV = -1; redraw(); } });
    b.addEventListener('keydown', roving(KB.wb, i, showW, () => KB.wb.filter(x => !x.hidden).length));
    KB.wb.push(b);
  }
  KB.pb = add(FIG, 'button', null, 'Replay the training, epoch 0 to 300');
  if (REDUCED) { KB.pb.setAttribute('aria-disabled', 'true'); KB.pb.setAttribute('aria-label', 'Replay needs motion; use the epoch slider'); }
  KB.pb.addEventListener('click', e => { e.stopPropagation(); replay(); });
  KB.sl = add(FIG, 'div', 'slider', 'Epoch of training shown');
  KB.sl.classList.add('nfs');                    // its ring hugs the track, clear of the replay chip
  KB.sl.tabIndex = 0;
  KB.sl.setAttribute('aria-valuemin', '0'); KB.sl.setAttribute('aria-valuemax', '300');
  KB.sl.addEventListener('keydown', e => {
    const d = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 10, PageDown: -10 }[e.key];
    const q = e.key === 'Home' ? 0 : e.key === 'End' ? FIN : d ? sNow() + d : -1;
    if (q < 0) return;
    e.preventDefault(); chooseEpoch(q);
  });
  cv.style.touchAction = 'pan-y pinch-zoom';
  cv.addEventListener('pointermove', e => {
    const [X, Y] = toUnits(e);
    if (DRAG) { chooseEpoch(nearest(clamp((X - SL.x0) / (SL.x1 - SL.x0)) * 300)); return; }
    if (e.pointerType !== 'mouse') return;
    const hn = hitNode(X, Y), hb = hitControl(X, Y), tr = inTrain(X, Y);
    let hw = -1, hs = -1;
    if (tr) { hs = epochAt(X); hw = nearLine(Y, hs); }
    else if (!hb && hn < 0) hw = hitWeight(X, Y);
    const acts = hn >= 0 || hw >= 0 || (hb !== '' && !(hb === 'play' && REDUCED));
    cv.style.cursor = tr ? 'crosshair' : acts ? 'pointer' : ground(X, Y) ? 'default' : '';
    if (hw >= 0 || hs >= 0) holdA();
    if (hn !== HN || hb !== HB || hw !== HOV || hs !== HSC) { HN = hn; HB = hb; HOV = hw; HSC = hs; redraw(); }
  });
  cv.addEventListener('pointerleave', () => { if (DRAG) return; HN = -1; HB = ''; HOV = -1; HSC = -1; DOWN = false; cv.style.cursor = ''; redraw(); });
  cv.addEventListener('pointerdown', e => {
    LASTP = e.pointerType;
    const [X, Y] = toUnits(e), hb = e.button === 0 ? hitControl(X, Y) : '';
    PRESS = hb;
    if (hb === 'handle' || hb === 'track') {
      DRAG = true; cv.setPointerCapture(e.pointerId);
      chooseEpoch(nearest(clamp((X - SL.x0) / (SL.x1 - SL.x0)) * 300));
    } else if (hb === 'play' && !REDUCED) { DOWN = true; redraw(); }
  });
  const drop = () => { if (DRAG || DOWN) { DRAG = false; DOWN = false; redraw(); } };
  cv.addEventListener('pointerup', drop);
  cv.addEventListener('pointercancel', drop);
  // a click on a neuron, a control, a weight or the plot is a choice, and the click that ends a
  // press on the slider or the replay chip is that press's: none of them may also pause (the engine
  // toggles on a click of the canvas), so they stop on the way down; so does a near miss on the
  // controls' own ground
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const pr = PRESS; PRESS = '';
    if (pr === 'handle' || pr === 'track') { e.stopPropagation(); return; }   // the epoch is set on the way
    const [X, Y] = toUnits(e);
    const k = hitNode(X, Y), hb = hitControl(X, Y), w = hitWeight(X, Y);
    if (hb === 'play') { if (pr === 'play') replay(); }
    else if (pr === 'play') { /* pressed on the chip, let go off it: nothing */ }
    else if (k >= 0) chooseNeuron(k);
    else if (hb) { /* the slider: set on the way down */ }
    else if (inTrain(X, Y)) { if (LASTP !== 'mouse') chooseEpoch(epochAt(X)); else chooseEpoch(HSC >= 0 ? HSC : epochAt(X)); }
    else if (w >= 0) { holdA(); if (LASTP !== 'mouse') { HOV = HOV === w ? -1 : w; redraw(); } }
    else if (!ground(X, Y)) return;
    e.stopPropagation();
  }, true);
}
/* the keyboard's stand-ins sit on what they choose, and say what is chosen */
function place() {
  if (STILL || !KB.sl) return;
  const st = aNow(), n = nRows(st.k), s = sNow(), rp = replaying();
  const key = cv.clientWidth + ':' + st.k + ':' + s + ':' + HOV + ':' + rp;
  if (key === KB.key) return;
  KB.key = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  const box = (el, x0, y0, x1, y1) => { el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0); };
  KB.nr.forEach((b, k) => {
    const x = NX[NEU[k].L], y = NY(NEU[k].L, NEU[k].j), r = NR(NEU[k].L);
    box(b, x - r - 3, y - r - 3, x + r + 3, y + r + 3);
    b.setAttribute('aria-checked', String(k === st.k)); b.tabIndex = k === st.k ? 0 : -1;
  });
  const bias = !isIn(st.k), last = bias ? n : n - 1, wt = HOV >= 0 && HOV <= last ? HOV : 0;
  KB.wb.forEach((b, i) => {
    b.hidden = i > last;
    if (i > last) return;
    if (isIn(st.k)) box(b, XAL - 42, rowY(i, n) - 28, XAL + 42, rowY(i, n) + 5);
    else if (i < n) box(b, XWL - 42, rowY(i, n) - 28, XWL + 42, rowY(i, n) + 5);
    else box(b, XS - 36, YM + 86, XS + 36, YM + 108);
    const w0 = trajOf(st.k, i, 0), w1 = trajOf(st.k, i, FIN);
    const what = isIn(st.k) ? `weight to hidden layer 1 neuron ${i + 1}` : i < n ? 'weight ' + (i + 1) : 'bias';
    b.setAttribute('aria-label', `${what} of ${nName(st.k)}: ${num(w0)} before training, ${num(w1)} after`);
    b.setAttribute('aria-checked', String(i === HOV)); b.tabIndex = i === wt ? 0 : -1;
  });
  box(KB.pb, RP.x, RP.y, RP.x + RP.w, RP.y + RP.h);
  if (!REDUCED) KB.pb.setAttribute('aria-label', rp ? 'Stop the replay of the training' : 'Replay the training, epoch 0 to 300');
  box(KB.sl, SL.x0 - 9, SL.y - 16, SL.x1 + 10, SL.y + 16);   // the ring only: the hit band is hitControl's
  KB.sl.setAttribute('aria-valuenow', String(D.eps[s]));
  const said = isIn(st.k) ? `x = ${num(outAt(s, st.k))}` : NEU[st.k].L === 3 ? outAt(s, st.k).toFixed(3) : num(outAt(s, st.k));
  KB.sl.setAttribute('aria-valuetext', `epoch ${D.eps[s]}: ${nName(st.k)} gives ${said}`);
}
boot();
"""

TITLE = "Figure 18a: What one neuron computes"
ARIA = ("The iris network of Figure 17 with one neuron marked, and that neuron's own computation for a held out "
        "versicolor flower: its inputs times its trained weights, summed with its bias, passed through tanh "
        "(softmax for an output neuron) to its output; an input neuron standardizes its measurement and hands it "
        "on along its weights. Below, how the neuron's weights moved during the 300 training epochs, with a "
        "slider of the epoch shown and a button that replays the training; any of the 17 neurons can be chosen.")


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
    mc.publish(NAME, TITLE, ARIA, 1000, 640, DATA, JS,
               look=(0.3, 0.8, 1.4, 2.2, 3.0, 4.0, 5.0, 9.5, 12.0, 17.5, 20.0, 25.5, 27.5, 31.0))
    T_IN, PA = .35, 8
    sim = lambda n: .55 + .3 * (n - 1) + .75 + .3 + .45 + .3 + .75
    POSTER = T_IN + sim(4) + .5
    say("THE PAGE")
    say(f"  W = 1000, H = 640. POSTER_T = {POSTER:g} s: the first neuron of the tour computed.")
    say(f"  Untouched, the page tours hidden 1 neuron 1, hidden 2 neuron 5, the versicolor output and the petal")
    say(f"  length input, {PA} s each. A neuron's computation takes {sim(4):.1f} s (4 inputs) or {sim(5):.1f} s (5): each")
    say("  input's arrow grows along its weight in 0.75 s, 0.3 s after the one before; its product arrives and")
    say("  goes on to the sum; the bias joins; z goes to the activation, where the operating point glides")
    say("  along the curve (Motion spring, 0.4 s, no bounce); the output node fills. An input standardizes its")
    say("  measurement, then its five weights flow out to hidden layer 1, 0.22 s apart. The network's own")
    say("  connections flow with the view.")
    say("  The reader chooses any of the 17 neurons (a click on it, or on an input's row of the table); the")
    say("  slider under the training plot sets the epoch shown, the round button replays the 300 epochs in")
    say(f"  {6} s, and pointing at the plot shows that epoch: the network's values, the chosen neuron's numbers")
    say("  and its plot follow. Pointing at a weight (diagram or plot) shows it before and after training.")
    say("  Paused, or with less motion, a choice is made at once (a replay plays the page again).")
    say("  Keyboard: a radio group of the 17 neurons, one stop per weight and the bias, the replay button and")
    say("  the slider of epochs. Touch: a tap chooses, a drag on the slider scrubs.")
    say("  overlap check (engine.js ?overlap) at the poster and every 0.25 s up to it: clean (common.still)")
    if "--verify" in sys.argv:
        states = [("page clocks", "")]
        for k in range(17):
            Lq = NEU[k][0]
            n_rows = SIZES[1] if Lq == 0 else SIZES[Lq - 1]
            last = n_rows - 1 if Lq == 0 else n_rows
            for q in (FIN, 0, 10, 30, 60):
                for h in (-1, 0, last):
                    states.append((f"neuron {k}, epoch {EPS[q]}, weight {h}",
                                   f"t = 70; REP = null; HSC = -1; SEL = {{k: {k}, t0: t - 1e3, prev: null}}; EPI = {q}; HOV = {h}; HN = {(k + 5) % 17}; HB = ''"))
        states += [(f"neuron switch, {d:.1f} s in", f"REP = null; HB = ''; EPI = {FIN}; SEL = {{k: {k2}, t0: 30, prev: {{k: {k1}, v0: 0, sw: 30}}}}; t = {30 + d}")
                   for k1, k2 in ((4, 15), (15, 2), (2, 13), (13, 6)) for d in np.arange(0, 5.01, .1)]
        states += [(f"replay, {d:.1f} s in", f"SEL = {{k: 9, t0: 0, prev: null}}; HB = 'play'; REP = {{t0: 40}}; t = {40 + d}")
                   for d in np.arange(0, 6.01, .25)]
        states += [(f"tour, t = {tt:.2f}", f"SEL = null; REP = null; EPI = {FIN}; HB = ''; t = {tt}")
                   for tt in list(np.arange(0, 4 * PA + 1, .25))]
        res, clocks = verify(states)
        if abs(clocks[0] - POSTER) > 1e-9 or clocks[1] != PA:
            raise RuntimeError(f"the page's clocks {clocks} are not the check file's ({POSTER}, {PA})")
        bad = [(nm, a, c) for nm, a, c in res if a or c]
        say(f"  --verify: the page's POSTER_T and tour period read back: {clocks[0]:g} s, {clocks[1]} s")
        say(f"  --verify: {len(res)} states: every neuron at epochs 300, 0, 10, 40 and 160 with its first and last")
        say("  weight pointed at, four neuron switches frame by frame (0.1 s), a replay every 0.25 s and the")
        say(f"  tour every 0.25 s for {4 * PA} s: {len(bad)} with collisions")
        for nm, a, c in bad[:12]:
            say(f"    {nm}: {a[:3]} {c[:3]}")
    mc.check(NAME, L)
