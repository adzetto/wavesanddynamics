"""Figure 7 of the machine learning guide (stem image4): feature engineering
versus feature learning, on real data.

Data: scikit-learn's handwritten digits (1,797 images of 8 x 8 pixels, grey
levels 0..16), split two thirds for training and one third for testing
(stratified, random_state 0).

(a) Feature engineering: six features a person designs from the pixels,
counts, shares and a symmetry, each a few lines of numpy: holes (enclosed
background regions), strokes across the two middle rows, strokes down the
two middle columns, the share of ink in the top half and in the left half,
and left-right mirror symmetry. A logistic regression (scikit-learn,
standardized features) predicts the digit from those six numbers alone.

(b) Feature learning: a network 64-16-12-10 (scikit-learn MLPClassifier,
tanh, alpha 0.01) sees the raw pixels, scaled to 0..1, and learns its own
features in two layers. Each unit is drawn as what excites it: the average
training image, each image weighted by how far the unit's activation rises
above its mean (a network this small on 8 x 8 digits learns digit-like
templates in both layers; its raw weights look like noise at this size).

The page shows six test images in turn; for each, every designed feature,
every unit's activation (the tile's strength) and both models' ten class
probabilities are the models' own numbers.

Run: python tools/numfig/mla_learning.py [--look]
"""
import sys
import warnings

import numpy as np
from scipy import ndimage
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

import common
from mla_shared import LIB, report

warnings.filterwarnings("ignore", category=UserWarning)
NAME, STEM = "mla-learning", "mla_learning"

dg = load_digits()
Xtr, Xte, ytr, yte = train_test_split(dg.images, dg.target, test_size=0.33, random_state=0,
                                      stratify=dg.target)
FNAMES = ["holes", "strokes across", "strokes down", "ink in top half", "ink in left half", "mirror symmetry"]
FMAX = [2, 3, 3, 1, 1, 1]


def runs(v):
    b = (v > 6).astype(int)
    return int(((b[1:] - b[:-1]) == 1).sum() + b[0])


def designed(im):
    m = im > 4
    lab, nl = ndimage.label(~m)
    border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    holes = len([k for k in range(1, nl + 1) if k not in border])
    tot = im.sum()
    return [holes, (runs(im[3]) + runs(im[4])) / 2, (runs(im[:, 3]) + runs(im[:, 4])) / 2,
            im[:4].sum() / tot, im[:, :4].sum() / tot, 1 - np.abs(im - im[:, ::-1]).mean() / 16]


Ftr = np.array([designed(i) for i in Xtr])
Fte = np.array([designed(i) for i in Xte])
sc = StandardScaler().fit(Ftr)
lr = LogisticRegression(max_iter=5000).fit(sc.transform(Ftr), ytr)
acc_lr = lr.score(sc.transform(Fte), yte)

Ptr, Pte = Xtr.reshape(len(Xtr), -1) / 16, Xte.reshape(len(Xte), -1) / 16
mlp = MLPClassifier(hidden_layer_sizes=(16, 12), activation="tanh", alpha=0.01, max_iter=4000,
                    random_state=0).fit(Ptr, ytr)
acc_mlp = mlp.score(Pte, yte)
W1, W2 = mlp.coefs_[0], mlp.coefs_[1]
b1, b2 = mlp.intercepts_[0], mlp.intercepts_[1]


def hidden(P):
    h1 = np.tanh(P @ W1 + b1)
    h2 = np.tanh(h1 @ W2 + b2)
    return h1, h2


H1tr, H2tr = hidden(Ptr)
H1te, H2te = hidden(Pte)


def excites(H):
    """per unit: the training images averaged, each weighted by how far the unit rises above its mean"""
    w = np.maximum(0, H - H.mean(0))
    return (w.T @ Ptr) / w.sum(0)[:, None]


pref1, pref2 = excites(H1tr), excites(H2tr)


def strength(Htr, Hte):
    """an activation as 0..1 of the unit's own range over the test set"""
    lo, hi = Hte.min(0), Hte.max(0)
    return (Hte - lo) / (hi - lo)


S1, S2 = strength(H1tr, H1te), strength(H2tr, H2te)

# six test images, digits in this order: for each digit the first test image the network gets
# right with p > 0.9 and the designed features get right, except for 7 and 8, where it is the
# first the designed features get wrong (4 of 6 right, near their 70 % on the whole test set)
ORDER, MISS = [3, 0, 7, 4, 2, 8], {7, 8}
pl, pm = lr.predict(sc.transform(Fte)), mlp.predict(Pte)
qm = mlp.predict_proba(Pte).max(1)
pick = []
for dgt in ORDER:
    ok = np.where((yte == dgt) & (pm == dgt) & (qm > 0.9) & ((pl != dgt) if dgt in MISS else (pl == dgt)))[0]
    pick.append(int(ok[0]))
pick = np.array(pick)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-learning: Figure 7, feature engineering versus feature learning")
say("")
say(f"DATA: scikit-learn digits, {len(dg.images)} images 8 x 8; train {len(Xtr)}, test {len(Xte)} (stratified, seed 0)")
say("")
say("(a) SIX DESIGNED FEATURES + LOGISTIC REGRESSION")
for n, lo, hi in zip(FNAMES, Ftr.min(0), Ftr.max(0)):
    say(f"  {n:18s} training range {lo:.3f} .. {hi:.3f}")
say(f"  test accuracy {acc_lr:.4f}")
say("(b) NETWORK 64-16-12-10 ON RAW PIXELS")
say(f"  MLPClassifier(16, 12), tanh, alpha 0.01, adam; {mlp.n_iter_} epochs; test accuracy {acc_mlp:.4f}")
say("")
say("CHECK 1: the page's forward pass (numpy) against scikit-learn's predict_proba")
h1, h2 = hidden(Pte)
z = h2 @ mlp.coefs_[2] + mlp.intercepts_[2]
p = np.exp(z - z.max(1, keepdims=True))
p /= p.sum(1, keepdims=True)
say(f"  max |softmax(ours) - predict_proba| over the test set = {np.abs(p - mlp.predict_proba(Pte)).max():.1e}")
say("CHECK 2: the designed features on images whose answer is known by hand")
zero = np.zeros((8, 8))
zero[1:7, 2] = zero[1:7, 5] = zero[1, 2:6] = zero[6, 2:6] = 16          # a drawn '0': a ring
one = np.zeros((8, 8))
one[1:7, 3:5] = 16                                                    # a drawn '1': a bar
f0, f1 = designed(zero), designed(one)
say(f"  ring:  holes {f0[0]} (1), strokes across {f0[1]} (2), strokes down {f0[2]} (2),"
    f" top {f0[3]:.2f} (0.50), left {f0[4]:.2f} (0.50), symmetry {f0[5]:.2f} (1.00)")
say(f"  bar:   holes {f1[0]} (0), strokes across {f1[1]} (1), strokes down {f1[2]} (1),"
    f" top {f1[3]:.2f} (0.50), left {f1[4]:.2f} (0.50), symmetry {f1[5]:.2f} (1.00)")
say("CHECK 3: the logistic regression's probabilities sum to one; the page's argmax is predict")
PL = lr.predict_proba(sc.transform(Fte))
say(f"  max |sum p - 1| = {np.abs(PL.sum(1) - 1).max():.1e}; argmax == predict on all: {bool(np.all(PL.argmax(1) == pl))}")
say("")
say("THE SIX TEST IMAGES")
for i in pick:
    say(f"  test #{i}: digit {yte[i]}; designed features predict {pl[i]} (p {PL[i].max():.2f}),"
        f" network predicts {pm[i]} (p {qm[i]:.2f})")
say("")
say("PAGE (1000 x 625): a test image every 4.5 s (2.6 s before 5 Oct 2026). As an image comes in (0.3 s), the")
say("  last image's features, unit activations and probabilities fade out; then each stage fills in turn (features")
say("  from 0.35 s, layer 1 at 0.45 s, layer 2 at 0.65 s, the probabilities at 0.85 s and 0.9 s), and the answer")
say("  rests about 3.2 s. The probability bars stand on an axis from 0 to 1; a key under the tiles reads them.")
report(STEM, L)

DATA = {
    "img": Xte[pick].reshape(len(pick), -1), "lab": yte[pick],
    "f": Fte[pick], "fmax": FMAX, "fn": FNAMES,
    "pl": PL[pick], "pm": mlp.predict_proba(Pte)[pick],
    "p1": pref1 / pref1.max(1, keepdims=True),            # 16 x 64, each tile to its own darkest
    "p2": pref2 / pref2.max(1, keepdims=True),            # 12 x 64
    "a1": S1[pick], "a2": S2[pick],
    "acc": [acc_lr, acc_mlp], "n": [len(Xtr), len(Xte)],
}

JS = LIB + r"""
const D = DATA, K = D.lab.length;
/* a test image every PER s. As one comes in, the last image's answer goes (FD s: its features,
   its units and its probabilities fade); then the new pass fills each stage in turn and rests,
   so no image is ever shown beside another image's answer (5 Oct 2026: 2.6 s a digit before) */
const T0 = .05, PER = 4.5, FD = .3;
const POSTER_T = T0 + 3;
/* the image on show, its predecessor, and how far its pass has come */
function slot() {
  if (t < T0) return {k: 0, prev: -1, u: 0};
  const n = Math.floor((t - T0) / PER);
  return {k: n % K, prev: n === 0 ? -1 : (n - 1) % K, u: t - T0 - n * PER};
}
/* a stage of the pass: whose values it shows (k), how much of them (g, growing from nothing on a
   spring that starts d s in) and how visible they are (a: the last image's, going out) */
function stage(s, d) {
  if (s.prev >= 0 && s.u < FD) return {k: s.prev, g: 1, a: 1 - s.u / FD};
  return {k: s.k, g: sp(s.u - d, .3), a: 1};
}

function pix(x, y, cell, v, alpha) {                    // an 8 x 8 image, v in [0, 1]
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha;
  for (let r = 0; r < 8; r++) for (let c = 0; c < 8; c++) {
    const i = Math.round(clamp(v[r * 8 + c]) * 255) * 3;
    ctx.fillStyle = `rgb(${SEQ[i]},${SEQ[i + 1]},${SEQ[i + 2]})`;
    ctx.fillRect(x + c * cell, y + r * cell, cell + .35, cell + .35);
  }
  ctx.restore();
}
/* learned features as tiles; each tile's strength is how strongly this image excites the unit */
function tiles(x0, y0, n, cols, cell, gap, get, act, alpha) {
  for (let j = 0; j < n; j++) {
    const x = x0 + (j % cols) * (8 * cell + gap), y = y0 + Math.floor(j / cols) * (8 * cell + gap);
    pix(x, y, cell, get(j), alpha * (.12 + .88 * act(j)));
    box(x, y, 8 * cell, 8 * cell, {stroke: C.ink, width: .6, alpha: alpha * .55});
  }
}
function input(s, x, y, cell, a) {
  const na = s.prev < 0 ? 1 : clamp(s.u / FD);
  if (s.prev >= 0) pix(x, y, cell, D.img[s.prev].map(v => v / 16), a * (1 - na));
  pix(x, y, cell, D.img[s.k].map(v => v / 16), a * na);
  box(x, y, 8 * cell, 8 * cell, {stroke: C.ink, width: 1.2, alpha: a});
  text('input, 8 × 8 pixels', x + 4 * cell, y + 8 * cell + 23, {size: 16, color: C.body, align: 'center', alpha: a});
}
/* ten class probabilities on a probability axis, the largest in accent. a: the axis and digits;
   st: the stage whose probabilities are drawn (they grow, or the last image's go out) */
function bars(x0, y0, probs, a, st) {
  const W_ = 20, P_ = 29, Hh = 100, ba = st.a * a;
  line([[x0 - 10, y0], [x0 + 10 * P_ - 3, y0]], {width: 1.2, alpha: a});
  line([[x0 - 10, y0], [x0 - 10, y0 - Hh]], {width: 1.2, alpha: a});
  for (const v of [0, .5, 1]) line([[x0 - 10, y0 - Hh * v], [x0 - 5, y0 - Hh * v]], {width: 1.1, alpha: a});
  for (const v of [0, .5, 1]) text(v === .5 ? '0.5' : String(v), x0 - 16, y0 - Hh * v + 5.6, {size: 16, align: 'right', alpha: a});
  let best = 0; for (let i = 1; i < 10; i++) if (probs[i] > probs[best]) best = i;
  const hi = clamp((st.g - .5) * 2) * ba, lo = 1 - (st.g > .5 ? hi / Math.max(ba, 1e-9) * ba : 0);
  for (let i = 0; i < 10; i++) {
    const h = Hh * probs[i] * st.g;
    if (h > .3) box(x0 + i * P_, y0 - h, W_, h, {fill: i === best ? C.accent : C.sky, alpha: ba});
    // the answer's digit turns crimson once its bar has grown; the two never show at once
    const cx = x0 + i * P_ + W_ / 2, cr = i === best ? clamp(2 * hi - 1) : 0, ck = i === best ? clamp(1 - 2 * hi) : 1;
    if (ck > 0) text(String(i), cx, y0 + 19, {size: 16, align: 'center', alpha: a * ck});
    if (cr > 0) text(String(i), cx, y0 + 19, {size: 16, align: 'center', alpha: a * cr, color: C.accent, bold: true});
  }
  const la = clamp((st.g - .7) / .3) * ba;
  text('predicts ' + best, x0 + 10 * P_ - 3, y0 - Hh - 12, {size: 17, align: 'right', alpha: la, color: C.accent});
  math('p = ' + probs[best].toFixed(2), x0 + 2, y0 - Hh - 12, {size: 16, color: C.body, alpha: la});
  text('probability of each digit', x0 + 5 * P_ - 3, y0 + 43, {size: 16, color: C.body, align: 'center', alpha: a});
}
function draw() {
  const s = slot();
  const IC = 13, OUT = 700;

  /* (a) feature engineering */
  const a0 = arrive(0);
  sub('a', 18, 34, 'feature engineering', a0);
  text('humans design the features first', 53, 58, {size: 16, color: C.body, alpha: arrive(.05)});
  const AY = 98, MY = AY + 4 * IC;
  input(s, 24, AY, IC, a0);
  const FX = 196, FY = AY + 10, RH = 26;
  arrow(24 + 8 * IC + 8, MY, FX - 12, MY, {width: 1.3, head: 9, alpha: seg(.06, .3)});
  D.fn.forEach((nm, i) => {
    const a = arrive(.08 + .03 * i), y = FY + i * RH, st = stage(s, .35 + .04 * i), v = D.f[st.k][i] * st.g;
    text(nm, FX, y, {size: 16, alpha: a});
    line([[FX + 140, y - 5], [FX + 220, y - 5]], {color: C.rule, width: 5, alpha: a});
    const w = 80 * clamp(v / D.fmax[i]);
    if (w > .5) line([[FX + 140, y - 5], [FX + 140 + w, y - 5]], {color: C.navy, width: 5, alpha: a * st.a});
    const vs = D.fmax[i] > 1 ? (Math.round(v * 2) / 2).toFixed(Math.round(v * 2) % 2 ? 1 : 0) : v.toFixed(2);
    text(vs, FX + 264, y, {size: 16, align: 'right', alpha: a * st.a * clamp(st.g * 3)});
  });
  text('six designed features', FX + 132, FY + 6 * RH + 10, {size: 16, color: C.body, align: 'center', alpha: arrive(.3)});
  const ba = arrive(.2);
  arrow(FX + 276, MY, 504, MY, {width: 1.3, head: 9, alpha: ba});
  node(568, MY, 116, 56, ['logistic', 'regression'], {alpha: ba, size: 16, gap: 19});
  arrow(632, MY, OUT - 32, MY, {width: 1.3, head: 9, alpha: ba});
  const sa = stage(s, .85);
  // the probability axis is centred a quarter below the arrow, so the arrow runs between its numbers
  bars(OUT, MY + 75, Array.from({length: 10}, (_, i) => D.pl[sa.k][i]), arrive(.28), sa);

  /* (b) feature learning */
  const BY = 322, b0 = arrive(.06);
  sub('b', 18, BY, 'feature learning', b0);
  text('the network learns its own features from the pixels', 53, BY + 24, {size: 16, color: C.body, alpha: arrive(.1)});
  const IY = BY + 62, MB = IY + 4 * IC;
  input(s, 24, IY, IC, b0);
  const CELL = 3.8, GAP = 5, TS = 8 * CELL, LX = 196;
  arrow(24 + 8 * IC + 8, MB, LX - 12, MB, {width: 1.3, head: 9, alpha: seg(.1, .3)});
  const t1 = arrive(.14), t2 = arrive(.22);
  const L1Y = MB - (4 * TS + 3 * GAP) / 2;
  const s1 = stage(s, .45), s2 = stage(s, .65);
  tiles(LX, L1Y, 16, 4, CELL, GAP, j => D.p1[j], j => D.a1[s1.k][j] * s1.g * s1.a, t1);
  text('layer 1: 16 units', LX + (4 * TS + 3 * GAP) / 2, L1Y + 4 * TS + 3 * GAP + 23, {size: 16, color: C.body, align: 'center', alpha: t1});
  const L2X = LX + 4 * TS + 3 * GAP + 48, L2Y = MB - (3 * TS + 2 * GAP) / 2;
  arrow(LX + 4 * TS + 3 * GAP + 10, MB, L2X - 12, MB, {width: 1.3, head: 9, alpha: t2});
  tiles(L2X, L2Y, 12, 4, CELL, GAP, j => D.p2[j], j => D.a2[s2.k][j] * s2.g * s2.a, t2);
  text('layer 2: 12 units', L2X + (4 * TS + 3 * GAP) / 2, L1Y + 4 * TS + 3 * GAP + 23, {size: 16, color: C.body, align: 'center', alpha: t2});
  const OX = (L2X + 4 * TS + 3 * GAP + OUT - 40) / 2, oa = arrive(.28);
  arrow(L2X + 4 * TS + 3 * GAP + 10, MB, OX - 46, MB, {width: 1.3, head: 9, alpha: oa});
  node(OX, MB, 80, 56, ['output', 'layer'], {alpha: oa, size: 16, gap: 19});
  arrow(OX + 46, MB, OUT - 32, MB, {width: 1.3, head: 9, alpha: oa});
  const so = stage(s, .9);
  bars(OUT, MB + 75, Array.from({length: 10}, (_, i) => D.pm[so.k][i]), arrive(.32), so);
  // what a tile is, as a key: the picture is what excites its unit, the darkness how much this image does
  const ka = arrive(.4), ky = L1Y + 4 * TS + 3 * GAP + 50;
  text('each tile: what excites its unit;', LX - 172, ky + 21, {size: 16, color: C.body, alpha: ka});
  const k1 = LX + 72;
  pix(k1, ky, CELL, D.p1[0], ka * .2); box(k1, ky, TS, TS, {stroke: C.ink, width: .6, alpha: ka * .55});
  text('quiet', k1 + TS + 8, ky + 21, {size: 16, color: C.body, alpha: ka});
  const k2 = k1 + TS + 60;
  pix(k2, ky, CELL, D.p1[0], ka); box(k2, ky, TS, TS, {stroke: C.ink, width: .6, alpha: ka * .55});
  text('excited by this image', k2 + TS + 8, ky + 21, {size: 16, color: C.body, alpha: ka});

  text('scikit-learn digits; test accuracy ' + (D.acc[0] * 100).toFixed(0) + '% (a), ' + (D.acc[1] * 100).toFixed(0) + '% (b)',
       18, H - 14, {size: 15, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 7: Feature engineering versus feature learning"
ARIA = ('One handwritten digit feeds two models: above, six features a person designed, such as holes and '
        'strokes, go into a logistic regression; below, a small neural network takes the raw pixels and its '
        'two layers of learned features light up as the image excites them. Both give ten digit '
        'probabilities, and six test images take turns.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 625, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.6, 1.0, 1.7, 3.0, 4.6, 4.9, 5.6]))
