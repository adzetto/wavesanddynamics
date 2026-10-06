"""Figure 19: training and validation loss over the epochs of a real training
run, and the model itself at the epoch the cursor has reached.

Model: two classes of points in the plane (scikit-learn's two circles, noise
0.2, inner radius half the outer), 15 % of the labels flipped at random (noise
the model should not learn). 70 training points, 400 validation points, both
standardized with the training statistics. A fully connected network
2 -> 64 -> 64 -> 2, tanh hidden units, softmax output, its last layer started
small (the first prediction is close to 1/2 for every point), trained on the
cross-entropy by plain full batch gradient descent (one weight update per
epoch, learning rate 0.05) for 4000 epochs. Training and validation loss are
the cross-entropy over each set after every epoch. The model panel shows the
network's probability of class 1 on a 44 x 44 grid, saved every 250
epochs and at the validation minimum; the line is where it is 0.5.

Run: python tools/numfig/mlb_loss.py [--look]
"""
import numpy as np
from sklearn.datasets import make_circles

import common
import mlb_common as mc

NAME = "loss"
NTR, NVA, NOISE, FACTOR, FLIP = 70, 400, 0.2, 0.5, 0.15
H, LR, EPOCHS, SEED, DSEED = 64, 0.05, 4000, 2, 0
GN, GR = 44, 2.4                                 # model panel grid: GN x GN on [-GR, GR]^2

X, y = make_circles(NTR + NVA, noise=NOISE, factor=FACTOR, random_state=DSEED)
flip = np.random.default_rng(DSEED).uniform(size=y.size) < FLIP
y = np.where(flip, 1 - y, y)
Xt, yt, Xv, yv = X[:NTR], y[:NTR], X[NTR:], y[NTR:]
mu, sd = Xt.mean(0), Xt.std(0)
Xt, Xv = (Xt - mu) / sd, (Xv - mu) / sd

g = np.random.default_rng(SEED)
P = [g.standard_normal((2, H)), g.standard_normal(H) * 0.5,
     g.standard_normal((H, H)) * np.sqrt(1 / H), np.zeros(H),
     g.standard_normal((H, 2)) * np.sqrt(1 / H) * 0.1, np.zeros(2)]


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def forward(Xs, P):
    a1 = np.tanh(Xs @ P[0] + P[1])
    a2 = np.tanh(a1 @ P[2] + P[3])
    return softmax(a2 @ P[4] + P[5]), a1, a2


def loss(Xs, ys, P):
    p = forward(Xs, P)[0]
    return float(-np.mean(np.log(p[np.arange(len(ys)), ys]))), float(np.mean(p.argmax(1) == ys))


def grads(Xs, ys, P):
    p, a1, a2 = forward(Xs, P)
    d3 = p.copy()
    d3[np.arange(len(ys)), ys] -= 1
    d3 /= len(ys)
    G = [None] * 6
    G[4], G[5] = a2.T @ d3, d3.sum(0)
    d2 = (d3 @ P[4].T) * (1 - a2 ** 2)
    G[2], G[3] = a1.T @ d2, d2.sum(0)
    d1 = (d2 @ P[2].T) * (1 - a1 ** 2)
    G[0], G[1] = Xs.T @ d1, d1.sum(0)
    return G


def gradcheck(P, n=40, h=1e-6):
    G = grads(Xt, yt, P)
    rr = np.random.default_rng(7)
    worst = 0.0
    for _ in range(n):
        i = rr.integers(6)
        idx = tuple(rr.integers(s) for s in P[i].shape)
        old = P[i][idx]
        P[i][idx] = old + h; lp = loss(Xt, yt, P)[0]
        P[i][idx] = old - h; lm = loss(Xt, yt, P)[0]
        P[i][idx] = old
        fd = (lp - lm) / (2 * h)
        worst = max(worst, abs(fd - G[i][idx]) / max(1e-8, abs(fd) + abs(G[i][idx])))
    return worst


P0 = [p.copy() for p in P]
gc0 = gradcheck(P)
gx = np.linspace(-GR, GR, GN)
GX, GY = np.meshgrid(gx, gx)                     # row = x2 (from -GR up), column = x1
grid = np.c_[GX.ravel(), GY.ravel()]


def train(P, snaps_at=()):
    tr, va, tra, vaa, snaps = [], [], [], [], []
    for e in range(EPOCHS + 1):
        a, b = loss(Xt, yt, P); c, d = loss(Xv, yv, P)
        tr.append(a); va.append(c); tra.append(b); vaa.append(d)
        if e in snaps_at:
            snaps.append(forward(grid, P)[0][:, 1].reshape(GN, GN))
        if e == EPOCHS:
            break
        G = grads(Xt, yt, P)
        for i in range(6):
            P[i] -= LR * G[i]
    return tr, va, tra, vaa, snaps


va_first = train([p.copy() for p in P0])[1]      # a first run finds the validation minimum
SNAPS = sorted(set(range(0, EPOCHS + 1, 250)) | {int(np.argmin(va_first))})
P = [p.copy() for p in P0]
tr, va, tra, vaa, snaps = train(P, SNAPS)
gc1 = gradcheck(P)
tr, va = np.array(tr), np.array(va)
K = int(np.argmin(va))
pend = forward(Xt, P)[0].argmax(1)
kept = int(np.sum(pend[flip[:NTR]] == yt[flip[:NTR]]))
kept_min = None

# the epochs drawn: every 10, and the minimum
EP = np.array(sorted(set(range(0, EPOCHS + 1, 10)) | {K}))

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-loss: Figure 19, training and validation loss curves")
say("")
say("MODEL")
say(f"  data: make_circles({NTR + NVA}, noise={NOISE}, factor={FACTOR}, random_state={DSEED}); {int(flip.sum())} labels flipped"
    f" ({FLIP:.0%} at random, seed {DSEED}); first {NTR} training, last {NVA} validation;")
say(f"  standardized with the training mean and deviation. {int(flip[:NTR].sum())} flipped labels are in the training set.")
say(f"  network 2-{H}-{H}-2, tanh, softmax; {sum(p.size for p in P)} weights; init N(0,1) first layer,")
say(f"  N(0, 1/{H}) after, last layer x 0.1; cross-entropy; full batch gradient descent, learning rate {LR},"
    f" {EPOCHS} epochs (seed {SEED}).")
say("")
say("CHECK 1: back propagation against central differences (40 random weights, h = 1e-6)")
say(f"  largest relative error: {gc0:.1e} at the start, {gc1:.1e} at the end")
say("")
say("CHECK 2: gradient descent on a smooth loss with a small step never raises it")
ups = np.diff(tr)
say(f"  training loss rose in {int(np.sum(ups > 0))} of {EPOCHS} epochs (largest rise {max(0.0, ups.max()):.1e});"
    f" {tr[0]:.4f} -> {tr[-1]:.4f}")
say("")
say("CHECK 3: the loss of a network that knows nothing is ln 2 per point")
say(f"  ln 2 = {np.log(2):.4f}; training loss at epoch 0 = {tr[0]:.4f}, validation {va[0]:.4f}"
    f" (the small last layer starts every prediction near 1/2)")
p0 = np.full((NTR, 2), .5)
say(f"  cross-entropy of a constant 0.5 prediction, computed: {-np.mean(np.log(p0[np.arange(NTR), yt])):.4f}")
say("")
say("RESULT")
say(f"  validation loss is smallest at epoch {K}: {va[K]:.4f} (training {tr[K]:.4f});"
    f" accuracy {tra[K]:.2f} training, {vaa[K]:.2f} validation")
say(f"  at epoch {EPOCHS}: training {tr[-1]:.4f}, validation {va[-1]:.4f} ({va[-1]/va[K]:.2f} x its minimum);"
    f" accuracy {tra[-1]:.2f} training, {vaa[-1]:.2f} validation")
after = np.diff(va[K:])
say(f"  after the minimum the validation loss rises in {int(np.sum(after > 0))} of {after.size} epochs")
say(f"  training points whose (flipped, wrong) label the final network reproduces: {kept} of {int(flip[:NTR].sum())}"
    f" (memorized noise)")
say(f"  model panel: p(class 1) on a {GN} x {GN} grid over [-{GR}, {GR}]^2 at epochs {SNAPS}")
say(f"  curves drawn at {EP.size} epochs (every 10, and epoch {K})")
mc.check(NAME, L)

S = np.array(snaps)
SC = np.abs(S - 0.5).max(axis=(1, 2))
DATA = {
    "ep": EP, "tr": tr[EP], "va": va[EP], "kmin": K, "epochs": EPOCHS,
    "snaps": SNAPS, "gn": GN, "gr": GR,
    # each saved field as p - 1/2 over its own largest |p - 1/2|, in 127ths, and that scale:
    # the first fields are within 0.01 of 1/2 and would lose their shape on a fixed scale
    "p": common.i8((S - 0.5) / SC[:, None, None] * 127), "sc": SC,
    "xt": Xt, "yt": yt, "trAcc": [tra[K], tra[-1]], "vaAcc": [vaa[K], vaa[-1]],
    "vmin": va[K], "params": f"{FLIP:.0%} of labels flipped; {NTR} training, {NVA} validation points",
}

JS = r"""
const D = DATA, EP = D.ep, NE = EP.length, GN = D.gn, GR = D.gr, NS = D.snaps.length, PR = b64i8(D.p);
const T_RUN = .6, SWEEP = 7.5, REST = 2.2, BACK = 1.1, HOLD0 = .5, PER = SWEEP + REST + BACK + HOLD0;
/* the epoch the cursor has reached: a sweep over the run, a rest at its end, an eased return */
function cursorEpoch() {
  if (t < T_RUN) return 0;
  const c = (t - T_RUN) % PER;
  if (c < SWEEP) return D.epochs * easeInOut(c / SWEEP);
  if (c < SWEEP + REST) return D.epochs;
  if (c < SWEEP + REST + BACK) return D.epochs * (1 - easeInOut((c - SWEEP - REST) / BACK));
  return 0;
}
const POSTER_T = T_RUN + SWEEP + 1;

/* ------------------------------------------------ the loss panel */
const LA = { x: 76, y: 58, w: 520, h: 290 };
let TRP = null, VAP = null;                      // the two curves in drawing units, made once
function curvePts(A, arr) { const p = new Array(NE); for (let i = 0; i < NE; i++) p[i] = [A.X(EP[i]), A.Y(arr[i])]; return p; }
function valAt(arr, e) { return interp(EP, arr, e); }

/* ------------------------------------------------ the model panel */
const MA = { x: 673, y: 58, w: 290, h: 290 };
const off = document.createElement('canvas'); off.width = GN; off.height = GN;
const og = off.getContext('2d'), img = og.createImageData(GN, GN);
/* the two classes as Figures 2(a), 9 and 13 draw them: class 0 open navy circles on white,
   class 1 filled navy on steel; crimson is the validation loss's alone */
const ORA = _hex('#FFFFFF'), PUR = _hex(C.steel2), WHITE = [255, 255, 255];
const field = new Float32Array(GN * GN);
function fieldAt(e) {                            // p(class 1) at epoch e, between two saved epochs
  const S = D.snaps; let k = 0;
  while (k < NS - 2 && S[k + 1] <= e) k++;
  const s = clamp((e - S[k]) / (S[k + 1] - S[k]));
  const a = D.sc[k] / 127, b = D.sc[k + 1] / 127;
  for (let i = 0; i < GN * GN; i++) field[i] = .5 + lerp(PR[k * GN * GN + i] * a, PR[(k + 1) * GN * GN + i] * b, s);
  return field;
}
function paintField(f, alpha) {
  const d = img.data;
  for (let r = 0; r < GN; r++) for (let c = 0; c < GN; c++) {
    const v = f[r * GN + c], u = Math.min(1, Math.abs(v - .5) * 2.2), C0 = v < .5 ? ORA : PUR;
    const o = ((GN - 1 - r) * GN + c) * 4;       // row 0 of the grid is the bottom
    for (let q = 0; q < 3; q++) d[o + q] = Math.round(lerp(WHITE[q], C0[q], u));
    d[o + 3] = 255;
  }
  og.putImageData(img, 0, 0);
  ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = true;
  const cw = MA.w / (GN - 1);
  ctx.beginPath(); ctx.rect(MA.x, MA.y, MA.w, MA.h); ctx.clip();
  ctx.drawImage(off, MA.x - cw / 2, MA.y - cw / 2, MA.w + cw, MA.h + cw);
  ctx.restore();
}
/* where p = 0.5: marching squares on the grid, linear along each cell edge */
const HX = new Float32Array(4), HY = new Float32Array(4);
let nh = 0;
function edgeHit(a, b, c0, r0, c1, r1) {
  if ((a < 0) === (b < 0)) return;
  const s = a / (a - b), cw = MA.w / (GN - 1);
  HX[nh] = MA.x + lerp(c0, c1, s) * cw; HY[nh] = MA.y + MA.h - lerp(r0, r1, s) * cw; nh++;
}
function boundary(f, alpha) {
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = C.ink; ctx.lineWidth = 1.5; ctx.beginPath();
  for (let r = 0; r < GN - 1; r++) for (let c = 0; c < GN - 1; c++) {
    const a = f[r * GN + c] - .5, b = f[r * GN + c + 1] - .5, q = f[(r + 1) * GN + c + 1] - .5, d = f[(r + 1) * GN + c] - .5;
    nh = 0;
    edgeHit(a, b, c, r, c + 1, r); edgeHit(b, q, c + 1, r, c + 1, r + 1);
    edgeHit(q, d, c + 1, r + 1, c, r + 1); edgeHit(d, a, c, r + 1, c, r);
    if (nh >= 2) { ctx.moveTo(HX[0], HY[0]); ctx.lineTo(HX[1], HY[1]); }
    if (nh === 4) { ctx.moveTo(HX[2], HY[2]); ctx.lineTo(HX[3], HY[3]); }
  }
  ctx.stroke(); ctx.restore();
}

function draw() {
  const e = cursorEpoch(), la = lab(.1);
  /* loss */
  const A = axes({ ...LA, xlim: [0, D.epochs], ylim: [0, 1.2], xticks: [0, 1000, 2000, 3000, 4000],
    yticks: [0, .2, .4, .6, .8, 1, 1.2], yfmt: v => v === 0 ? '0' : v.toFixed(1), grid: true,
    xlabel: '\\rm{epoch}', ylabel: '\\rm{loss}', ylabelGap: 46, tickSize: 16, progress: seg(0, .35) });
  const xk = A.X(D.kmin), oa = seg(.55, .3);
  A.inside(() => {
    ctx.save(); ctx.globalAlpha = .55 * oa; ctx.fillStyle = C.wash; ctx.fillRect(xk, LA.y, LA.x + LA.w - xk, LA.h); ctx.restore();
    line([[xk, LA.y], [xk, LA.y + LA.h]], { color: C.guide, width: 1, dash: [5, 4], progress: oa });
    if (!TRP) { TRP = curvePts(A, D.tr); VAP = curvePts(A, D.va); }
    line(TRP, { color: C.blue, width: 2.4, progress: seg(.12, .42) });
    line(VAP, { color: C.accent, width: 2.4, progress: seg(.18, .42) });
  });
  const ka = lab(.62), ky = LA.y + 20 + rise(ka);
  // the cursor, and where each curve is at that epoch: drawn before the labels and the legend, it
  // passes behind them, as pgfplots draws a plot under its legend; it breaks 3 units round the label
  const ca = lab(.55);
  if (ca > 0) {
    const cx = A.X(e), o = { color: C.ink, width: 1, alpha: .5 * ca };
    ctx.save(); ctx.font = font({ size: 16 }); const q = ctx.measureText('overfitting begins'); ctx.restore();
    const b0 = xk + 8 - q.actualBoundingBoxLeft - 3, b1 = xk + 8 + q.actualBoundingBoxRight + 3;
    if (ka > 0 && cx > b0 && cx < b1) {
      line([[cx, LA.y], [cx, ky - q.actualBoundingBoxAscent - 3]], o);
      line([[cx, ky + q.actualBoundingBoxDescent + 3], [cx, LA.y + LA.h]], o);
    } else line([[cx, LA.y], [cx, LA.y + LA.h]], o);
    dot(cx, A.Y(valAt(D.tr, e)), 3.6, { color: '#fff', fill: C.blue, width: 1.2, alpha: ca });
    dot(cx, A.Y(valAt(D.va, e)), 3.6, { color: '#fff', fill: C.accent, width: 1.2, alpha: ca });
  }
  text('overfitting begins', xk + 8, ky, { size: 16, color: C.accent, alpha: ka });
  dot(xk, A.Y(D.vmin), 4, { color: '#fff', fill: C.accent, width: 1.3, alpha: ka });
  legend(LA.x + 12, LA.y + LA.h - 70, 172, [
    [(x, y, a) => line([[x - 12, y], [x + 12, y]], { color: C.blue, width: 2.4, alpha: a }), 'training loss'],
    [(x, y, a) => line([[x - 12, y], [x + 12, y]], { color: C.accent, width: 2.4, alpha: a }), 'validation loss'],
  ], { alpha: lab(.3) });

  /* the model at that epoch */
  const ma = seg(.1, .35);
  text(`the model at epoch ${Math.round(e)}`, MA.x, 38 + rise(la), { size: 17, color: C.body, alpha: la });
  paintField(fieldAt(e), ma);
  boundary(field, seg(.3, .3));
  const M = axes({ ...MA, xlim: [-GR, GR], ylim: [-GR, GR], xticks: [-2, 0, 2], yticks: [-2, 0, 2],
    xlabel: 'x_1', ylabel: 'x_2', ylabelGap: 34, tickSize: 16, progress: seg(.04, .35) });
  M.inside(() => {
    for (let i = 0; i < D.yt.length; i++) {
      const p = settle(.14 + .003 * i, .24), c = D.yt[i] ? [C.navy, '#fff'] : ['#fff', C.navy];
      if (p > 0) mark('circle', M.X(D.xt[i][0]), M.Y(D.xt[i][1]), 3.3 * (.55 + .45 * p), { fill: c[0], stroke: c[1], width: D.yt[i] ? .9 : 1.2, alpha: p });
    }
  });
  // the key of the model panel: the training points' labels and the region the model gives class 1
  const kk = lab(.5), ky2 = MA.y + MA.h + 82;
  let kx = MA.x - 4;
  mark('circle', kx + 5, ky2 - 5, 4, { fill: '#fff', stroke: C.navy, width: 1.2, alpha: kk });
  kx += 18 + text('class 0', kx + 16, ky2, { size: 16, alpha: kk }) + 22;
  mark('circle', kx + 5, ky2 - 5, 4, { fill: C.navy, stroke: '#fff', width: .9, alpha: kk });
  kx += 18 + text('class 1', kx + 16, ky2, { size: 16, alpha: kk }) + 22;
  rect(kx - 2, ky2 - 13, 14, 14, { fill: C.steel2, stroke: C.ink, width: 1, alpha: kk });
  text('predicted class 1', kx + 20, ky2, { size: 16, alpha: kk });
  text(D.params, 18, H - 12, { size: 15, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 19: Training loss curve"
ARIA = (f"A real training run of a small neural network over {EPOCHS} epochs. Left: the training loss "
        f"falls throughout, the validation loss falls to its lowest point at epoch {K} and then rises, "
        "and a dashed line marks where overfitting begins. Right: the model's two class regions at the "
        "epoch a cursor has reached; the boundary is smooth near the lowest validation loss and later "
        "bends around single mislabeled training points, memorizing them.")

if __name__ == "__main__":
    print(f"validation minimum at epoch {K}: {va[K]:.4f}; end {va[-1]:.4f}; memorized {kept} flipped labels")
    mc.publish(NAME, TITLE, ARIA, 1000, 490, DATA, JS, look=(0.3, 0.6, 1.2, 2.5, 4.5, 6.5, 8.1, 10.0, 11.2))
