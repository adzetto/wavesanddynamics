"""Figure 17: a multi-layer perceptron. Data flows left to right, every
connection has a learned weight, and training adjusts all the weights to
reduce the prediction error.

Model: Fisher's iris measurements (scikit-learn's copy): 150 flowers, four
measurements in cm, three species. 120 flowers train, 30 are held out
(stratified). The network is 4 -> 5 -> 5 -> 3, tanh hidden units, softmax
output (each neuron also has a bias), trained on the cross-entropy by full
batch gradient descent, learning rate 0.3, 300 epochs, from small random
weights. Inputs are standardized with the training mean and deviation.

The motion: first the training run (every weight at its value at that epoch;
line width is the size of the weight, blue positive, crimson negative) while
the prediction error falls; then three held-out flowers, one of each species,
pass through the trained network layer by layer (node colour: the value each
neuron computes) to the three output probabilities.

Run: python tools/numfig/mlb_mlp.py [--look]
"""
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

import common
import mlb_common as mc

NAME = "mlp"
SIZES, LR, EPOCHS, SEED, SNAP = [4, 5, 5, 3], 0.3, 300, 0, 10

iris = load_iris()
X, y = iris.data, iris.target
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=30, stratify=y, random_state=0)
mu, sd = Xtr.mean(0), Xtr.std(0)
A, B = (Xtr - mu) / sd, (Xte - mu) / sd


def softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def forward(Z, W, b):
    h1 = np.tanh(Z @ W[0] + b[0])
    h2 = np.tanh(h1 @ W[1] + b[1])
    return h1, h2, softmax(h2 @ W[2] + b[2])


def loss(Z, t, W, b):
    p = forward(Z, W, b)[2]
    return float(-np.mean(np.log(p[np.arange(len(t)), t])))


def grads(Z, t, W, b):
    h1, h2, p = forward(Z, W, b)
    d3 = p.copy()
    d3[np.arange(len(t)), t] -= 1
    d3 /= len(t)
    d2 = (d3 @ W[2].T) * (1 - h2 ** 2)
    d1 = (d2 @ W[1].T) * (1 - h1 ** 2)
    return [Z.T @ d1, h1.T @ d2, h2.T @ d3], [d1.sum(0), d2.sum(0), d3.sum(0)]


g = np.random.default_rng(SEED)
W = [g.standard_normal((a, c)) * np.sqrt(1 / a) for a, c in zip(SIZES[:-1], SIZES[1:])]
b = [np.zeros(c) for c in SIZES[1:]]

# gradient check at the start
GW, Gb = grads(A, ytr, W, b)
worst = 0.0
for i in range(3):
    for idx in np.ndindex(W[i].shape):
        o = W[i][idx]
        W[i][idx] = o + 1e-6; lp = loss(A, ytr, W, b)
        W[i][idx] = o - 1e-6; lm = loss(A, ytr, W, b)
        W[i][idx] = o
        fd = (lp - lm) / 2e-6
        worst = max(worst, abs(fd - GW[i][idx]) / max(1e-9, abs(fd) + abs(GW[i][idx])))

L, snaps = [], []
for e in range(EPOCHS + 1):
    L.append(loss(A, ytr, W, b))
    if e % SNAP == 0:
        snaps.append(np.concatenate([w.ravel() for w in W] + [v.ravel() for v in b]))
    if e == EPOCHS:
        break
    GW, Gb = grads(A, ytr, W, b)
    for i in range(3):
        W[i] -= LR * GW[i]
        b[i] -= LR * Gb[i]
acc_tr = int(np.sum(forward(A, W, b)[2].argmax(1) == ytr))
acc_te = int(np.sum(forward(B, W, b)[2].argmax(1) == yte))

# three held-out flowers, one per species, each the most typical (median confidence) of its kind
pte = forward(B, W, b)[2]
show = []
for s in range(3):
    ids = np.where(yte == s)[0]
    conf = pte[ids, s]
    show.append(int(ids[np.argsort(conf)[len(ids) // 2]]))
FL = []
for i in show:
    h1, h2, p = forward(B[i:i + 1], W, b)
    FL.append({"raw": Xte[i], "z": B[i], "h1": h1[0], "h2": h2[0], "p": p[0], "sp": int(yte[i])})

# ------------------------------------------------------------------ checks
Lc = []
say = Lc.append
say("nf-mlb-mlp: Figure 17, a multi-layer perceptron trained on the iris flowers")
say("")
say("MODEL")
say("  Fisher's iris data (scikit-learn): 150 flowers, sepal and petal length and width in cm,")
say("  three species. 120 train, 30 held out (stratified, random_state 0); standardized with the")
say(f"  training mean {np.round(mu, 3).tolist()} and deviation {np.round(sd, 3).tolist()}.")
say(f"  network {SIZES}, tanh, softmax, {sum(w.size for w in W)} weights and {sum(v.size for v in b)} biases;"
    f" weights N(0, 1/fan in), seed {SEED}.")
say(f"  cross-entropy, full batch gradient descent, learning rate {LR}, {EPOCHS} epochs; weights saved every {SNAP}.")
say("")
say("CHECK 1: back propagation against central differences, every weight at the start")
say(f"  largest relative error {worst:.1e}")
say("")
say("CHECK 2: the error only falls (gradient descent with a small step)")
say(f"  cross-entropy {L[0]:.4f} -> {L[50]:.4f} (epoch 50) -> {L[100]:.4f} (100) -> {L[-1]:.4f} (300);"
    f" rises in {int(np.sum(np.diff(L) > 0))} of {EPOCHS} epochs")
say(f"  a network that knows nothing scores ln 3 = {np.log(3):.4f}")
say("")
say("CHECK 3: accuracy")
say(f"  training {acc_tr} of 120, held out {acc_te} of 30")
say("")
say("THE THREE FLOWERS SHOWN (held out)")
for f in FL:
    say(f"  {iris.target_names[f['sp']]:10s} {np.round(f['raw'], 1).tolist()} cm -> p = {np.round(f['p'], 4).tolist()}")
say(f"  their probabilities sum to {[round(float(f['p'].sum()), 12) for f in FL]}")
mc.check(NAME, Lc)

S = np.array(snaps)
DATA = {
    "sizes": SIZES, "snaps": common.f32(S), "nsnap": len(snaps), "snap": SNAP, "epochs": EPOCHS,
    "loss": L, "flowers": FL, "names": list(iris.target_names), "acc": [acc_tr, acc_te],
    "features": ["sepal length", "sepal width", "petal length", "petal width"],
    "wmax": float(np.abs(S[:, :sum(a * c for a, c in zip(SIZES[:-1], SIZES[1:]))]).max()),
}

JS = r"""
const D = DATA, SZ = D.sizes, SN = b64f32(D.snaps), NSN = D.nsnap, NW = 4 * 5 + 5 * 5 + 5 * 3;
const LX = [196, 392, 588, 760], YC = 244, GAP = 70, R = 16;
const NY = SZ.map(n => Array.from({ length: n }, (_, i) => YC + (i - (n - 1) / 2) * GAP));
const OFF = [0, 20, 45];                         // where each weight matrix starts in a snapshot
/* the clock: the intro, the training run, then three flowers through the trained network */
const T_TR = .6, TR = 3.6, T_FW = T_TR + TR + .5, FP = 2.7, NFL = 3, T_BACK = T_FW + NFL * FP, BACK = 1.0;
const PER = T_BACK + BACK + .4 - T_TR;
const POSTER_T = T_FW + 1.7;
function loopT() { return t < T_TR ? t : T_TR + (t - T_TR) % PER; }
function epochNow(tt) {
  if (tt < T_TR) return 0;
  if (tt < T_TR + TR) return D.epochs * easeInOut((tt - T_TR) / TR);
  if (tt < T_BACK) return D.epochs;
  return D.epochs * (1 - easeInOut(clamp((tt - T_BACK) / BACK)));
}
const WN = new Float32Array(NW);
function weightsAt(e) {
  const u = e / D.snap, k = Math.min(NSN - 2, Math.floor(u)), s = clamp(u - k);
  for (let i = 0; i < NW; i++) WN[i] = lerp(SN[k * 73 + i], SN[(k + 1) * 73 + i], s);
  return WN;
}
const wAt = (m, i, j) => WN[OFF[m] + i * SZ[m + 1] + j];
/* a value as a colour: blue positive, crimson negative, white zero (signed(), ending at
   its matched middle stops, so a full node is no darker than its lines) */
const vcol = v => signed(v * 2 / 3);

function draw() {
  const tt = loopT(), e = epochNow(tt);
  weightsAt(e);
  const la = lab(.08);
  ['input layer', 'hidden layer 1', 'hidden layer 2', 'output layer'].forEach((s, k) =>
    text(s, LX[k], 44 + rise(lab(.05 * k)), { size: 16, color: C.body, align: 'center', alpha: lab(.05 * k) }));
  // the forward pass: which flower, and how far the data has flowed
  let fl = -1, fp = 0, fade = 1;
  if (tt >= T_FW && tt < T_BACK) { fl = Math.floor((tt - T_FW) / FP); fp = tt - T_FW - fl * FP; fade = 1 - easeInOut(clamp((fp - (FP - .3)) / .28)); }
  const F = fl >= 0 ? D.flowers[fl] : null;
  const layerOn = [clamp(fp / .3), clamp((fp - .3) / .35), clamp((fp - .65) / .35), clamp((fp - 1.0) / .35)];
  // connections: width the size of the weight, colour its sign
  const wm = D.wmax;
  for (let m = 0; m < 3; m++) {
    const flow = F ? layerOn[m + 1] : 0;
    for (let i = 0; i < SZ[m]; i++) for (let j = 0; j < SZ[m + 1]; j++) {
      const w = wAt(m, i, j), a = Math.min(1, Math.abs(w) / wm);
      const p0 = [LX[m] + R, NY[m][i]], p1 = [LX[m + 1] - R, NY[m + 1][j]];
      const pr = seg(.1 + .07 * m, .4);
      line([p0, p1], { color: w >= 0 ? S_POS : S_NEG, width: .5 + 3.2 * a, alpha: (.24 + .6 * a) * (F ? 1 - .2 * fade : 1), progress: pr });
      if (flow > 0 && flow < 1)
        line([p0, p1], { color: w >= 0 ? S_POS : S_NEG, width: .5 + 3.2 * a, alpha: (.35 + .6 * a) * fade, progress: easeOut(flow) });
    }
  }
  // neurons: filled with what they compute for the flower passing through
  for (let k = 0; k < 4; k++) for (let i = 0; i < SZ[k]; i++) {
    const a = settle(.04 + .06 * k + .015 * i, .26);
    let fill = '#FFFFFF';
    if (F && layerOn[k] > 0) {
      const v = k === 0 ? F.z[i] / 2 : k === 1 ? F.h1[i] : k === 2 ? F.h2[i] : F.p[i];
      fill = vcol(v * layerOn[k] * fade);
    }
    node(LX[k], NY[k][i], R * (.6 + .4 * a), { fill, stroke: C.ink, width: 1.4, alpha: a });
  }
  // the four measurements, and the flower's values
  D.features.forEach((f, i) => {
    const a = lab(.12 + .04 * i), y = NY[0][i];
    text(f, LX[0] - R - 12, y - 3 + rise(a), { size: 15, color: C.body, align: 'right', alpha: a });
    if (F) math(`${F.raw[i].toFixed(1)}\\,\\rm{cm}`, LX[0] - R - 12, y + 16, { size: 15, align: 'right', alpha: layerOn[0] * fade });
  });
  // the three species and their probabilities
  D.names.forEach((s, j) => {
    const a = lab(.3 + .04 * j), y = NY[3][j], x = LX[3] + R + 12;
    const win = F && j === F.p.indexOf(Math.max(...F.p)) && layerOn[3] >= 1;
    text(s, x, y + 5 + rise(a), { size: 15, color: win ? C.ink : C.body, bold: !!win, alpha: a });
    if (F && layerOn[3] > 0) {
      const p = F.p[j] * easeOut(layerOn[3]), bw = 76 * p, bx = x + 84;
      rect(bx, y - 6, Math.max(.5, bw), 12, { fill: C.blue, stroke: null, alpha: fade });
      rect(bx, y - 6, 76, 12, { fill: null, stroke: C.rule, width: 1, alpha: fade });
      math(F.p[j].toFixed(2), bx + 82, y + 5, { size: 15, alpha: layerOn[3] * fade });
    }
  });

  /* below: the prediction error falling as the weights are adjusted */
  const PA = { x: 92, y: 468, w: 330, h: 104 };
  text('prediction error', PA.x, 452 + rise(lab(.3)), { size: 16, color: C.body, alpha: lab(.3) });
  const G = axes({ ...PA, xlim: [0, D.epochs], ylim: [0, 1], xticks: [0, 100, 200, 300], yticks: [0, .5, 1],
    yfmt: v => v === .5 ? '0.5' : fmt(v), xlabel: '\\rm{epoch}', progress: seg(.2, .35), grid: true });
  const upto = Math.round(e), pts = [];
  for (let i = 0; i <= upto; i++) pts.push([G.X(i), G.Y(Math.min(1, D.loss[i]))]);
  G.inside(() => line(pts, { color: C.blue, width: 2.2 }));
  if (tt >= T_TR) dot(G.X(e), G.Y(Math.min(1, D.loss[upto])), 3.6, { color: '#fff', fill: C.blue, width: 1.2 });
  math(`\\rm{cross\\ entropy}\\ \\ ${D.loss[upto].toFixed(3)}`, PA.x + PA.w, 452 + rise(lab(.3)), { size: 15, color: C.blue, align: 'right', alpha: lab(.3) });

  /* what is happening now */
  const SX0 = 500, sa = lab(.35);
  let head = 'training', sub = `epoch ${upto}: adjusting all weights`;
  if (tt < T_TR) sub = 'random starting weights';
  if (F) { head = 'prediction'; sub = `held out flower ${fl + 1} of 3`; }
  if (tt >= T_BACK) { head = 'training'; sub = 'back to random weights'; }
  text(head, SX0, 482 + rise(sa), { size: 17, alpha: sa });
  text(sub, SX0, 506 + rise(sa), { size: 16, color: C.body, alpha: sa });
  if (F) text(`true species: ${D.names[F.sp]}`, SX0, 530, { size: 16, color: C.body, alpha: layerOn[3] * fade });
  legend(SX0 + 262, 460, 218, [
    [(x, y, a) => line([[x - 12, y], [x + 12, y]], { color: S_POS, width: 2.6, alpha: a }), 'positive weight'],
    [(x, y, a) => line([[x - 12, y], [x + 12, y]], { color: S_NEG, width: 2.6, alpha: a }), 'negative weight'],
    [(x, y, a) => { line([[x - 12, y - 4], [x + 12, y - 4]], { color: C.ink, width: .6, alpha: a }); line([[x - 12, y + 3], [x + 12, y + 3]], { color: C.ink, width: 3, alpha: a }); }, 'width: size of weight'],
  ], { alpha: lab(.4) });
  text(`iris flowers (Fisher); network 4-5-5-3, tanh, softmax; gradient descent; right: ${D.acc[0]}/120 train, ${D.acc[1]}/30 held out`,
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 17: Multi-Layer Perceptron (MLP): data flows left to right"
ARIA = ("A network of four input neurons for the four measurements of an iris flower, two hidden layers "
        "of five neurons, and three output neurons for the three species, every neuron connected to every "
        "neuron in the next layer. Line width shows the size of each learned weight, blue positive and "
        "crimson negative. The weights change as training runs and a small plot shows the prediction error "
        "falling; then three held out flowers flow through the trained network from left to right and "
        "each gets its species probabilities.")

if __name__ == "__main__":
    print(f"accuracy {acc_tr}/120, {acc_te}/30; loss {L[0]:.3f} -> {L[-1]:.4f}; shown {show}")
    mc.publish(NAME, TITLE, ARIA, 1000, 668, DATA, JS, look=(0.3, 0.7, 2.0, 4.2, 5.0, 5.4, 5.9, 6.4, 7.4, 10.0, 13.6))
