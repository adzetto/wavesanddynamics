"""Figure 21: CNN architecture. Pixels become feature maps through learned
filters, pooling keeps the strongest signals, and dense neurons produce class
probabilities.

Model: a small convolutional network trained here on scikit-learn's
handwritten digits (1797 images of 8 x 8 pixels, grey levels 0 to 16, ten
classes); 1437 train, 360 held out. Three learned 3 x 3 filters (padding 1)
with ReLU give three 8 x 8 feature maps; 2 x 2 max pooling keeps the strongest
value of each block (three 4 x 4 maps); the 48 values, flattened, feed 16
dense ReLU neurons and 10 softmax outputs. Adam, 40 epochs, batch 64. The
numpy forward and back propagation agree with PyTorch's conv2d, max_pool2d and
autograd to rounding.

The motion is the network running on three held out digits: the filter window
slides over the pixels (slowly along the first row, where the arithmetic is
shown, stopping on each position, then quickly) and each feature map fills in
as it goes; each 2 x 2 block hands its largest value to the pooled map; the
flattened values flow through the dense neurons to the ten class
probabilities. The clock (CLOCK, below) is set so a reader can follow each
step: round 3 made every step twice as long as round 2.

Run: python tools/numfig/mlb_cnn.py [--look]
"""
import numpy as np
import torch
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

import mlb_common as mc

NAME = "cnn"
NF, NH, EPOCHS, LR, BATCH, SEED = 3, 16, 40, 0.005, 64, 0
PICK = ((9, 0.82), (0, 1.0), (4, 0.77))           # the digits shown: class, confidence sought

digits = load_digits()
X, y = digits.images, digits.target               # (1797, 8, 8), values 0..16
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=360, stratify=y, random_state=0)


def im2col(x):                                    # (N,8,8) -> (N,64,9), zero padding 1
    xp = np.pad(x, ((0, 0), (1, 1), (1, 1)))
    return np.stack([xp[:, i:i + 8, j:j + 8] for i in range(3) for j in range(3)], -1).reshape(len(x), 64, 9)


def forward(x, P):
    Wc, bc, W1, b1, W2, b2 = P
    cols = im2col(x)
    z = cols @ Wc + bc                            # (N,64,NF): position r*8+c, filter f
    a = np.maximum(z, 0)
    pooled = a.reshape(-1, 4, 2, 4, 2, NF).max(axis=(2, 4))          # (N,4,4,NF)
    f = pooled.transpose(0, 3, 1, 2).reshape(len(x), -1)             # filter-major, row-major
    h = np.maximum(f @ W1 + b1, 0)
    o = h @ W2 + b2
    o = o - o.max(1, keepdims=True)
    p = np.exp(o)
    return cols, z, a, pooled, f, h, p / p.sum(1, keepdims=True)


def loss(x, t, P):
    p = forward(x, P)[-1]
    return float(-np.mean(np.log(p[np.arange(len(t)), t] + 1e-300)))


def grads(x, t, P):
    Wc, bc, W1, b1, W2, b2 = P
    cols, z, a, pooled, f, h, p = forward(x, P)
    n = len(x)
    do = p.copy(); do[np.arange(n), t] -= 1; do /= n
    gW2, gb2 = h.T @ do, do.sum(0)
    dh = do @ W2.T * (h > 0)
    gW1, gb1 = f.T @ dh, dh.sum(0)
    dpool = (dh @ W1.T).reshape(n, NF, 4, 4).transpose(0, 2, 3, 1)
    am = a.reshape(n, 4, 2, 4, 2, NF)
    flat = (am == pooled[:, :, None, :, None, :]).transpose(0, 1, 3, 5, 2, 4).reshape(n, 4, 4, NF, 4)
    first = np.zeros_like(flat)                   # the gradient goes to the first maximum, as in PyTorch
    np.put_along_axis(first, flat.argmax(-1)[..., None], True, -1)
    first = first.reshape(n, 4, 4, NF, 2, 2).transpose(0, 1, 4, 2, 5, 3)
    dz = (first * dpool[:, :, None, :, None, :]).reshape(n, 64, NF) * (z > 0)
    return [np.einsum("nkp,nkf->pf", cols, dz), dz.sum((0, 1)), gW1, gb1, gW2, gb2]


g = np.random.default_rng(SEED)
P = [g.standard_normal((9, NF)) * 0.1, np.zeros(NF), g.standard_normal((NF * 16, NH)) * np.sqrt(2 / (NF * 16)) * 0.1,
     np.zeros(NH), g.standard_normal((NH, 10)) * np.sqrt(1 / NH), np.zeros(10)]

# check the numpy network against PyTorch on 20 training images
torch.set_default_dtype(torch.float64)
Pt = [torch.tensor(p, requires_grad=True) for p in P]
xt = torch.tensor(Xtr[:20])[:, None]
zt = torch.nn.functional.conv2d(xt, Pt[0].T.reshape(NF, 1, 3, 3), bias=Pt[1], padding=1)
pt = torch.nn.functional.max_pool2d(torch.relu(zt), 2)
ot = torch.relu(pt.reshape(20, -1) @ Pt[2] + Pt[3]) @ Pt[4] + Pt[5]
torch.nn.functional.cross_entropy(ot, torch.tensor(ytr[:20])).backward()
G = grads(Xtr[:20], ytr[:20], P)
_, z20, _, p20, *_ = forward(Xtr[:20], P)
chk_conv = float(np.max(np.abs(z20.reshape(20, 8, 8, NF).transpose(0, 3, 1, 2) - zt.detach().numpy())))
chk_pool = float(np.max(np.abs(p20.transpose(0, 3, 1, 2) - pt.detach().numpy())))
chk_grad = max(float(np.max(np.abs(G[i] - Pt[i].grad.numpy()))) for i in range(6))

M = [np.zeros_like(p) for p in P]; V = [np.zeros_like(p) for p in P]
step, hist = 0, []
for ep in range(EPOCHS):
    perm = g.permutation(len(Xtr))
    for k in range(0, len(Xtr), BATCH):
        j = perm[k:k + BATCH]
        G = grads(Xtr[j], ytr[j], P)
        step += 1
        for i in range(6):
            M[i] = .9 * M[i] + .1 * G[i]; V[i] = .999 * V[i] + .001 * G[i] ** 2
            P[i] -= LR * (M[i] / (1 - .9 ** step)) / (np.sqrt(V[i] / (1 - .999 ** step)) + 1e-8)
    hist.append((ep + 1, loss(Xtr, ytr, P)))
ptr = forward(Xtr, P)[-1]; pte = forward(Xte, P)[-1]
acc_tr, acc_te = int(np.sum(ptr.argmax(1) == ytr)), int(np.sum(pte.argmax(1) == yte))

# the three held out digits: a 9, a 0 and a 4, each the correctly read one whose confidence is
# nearest 0.82, 1 and 0.77, so the probabilities shown range from hesitant to sure
idx = []
ok = pte.argmax(1) == yte
for c, target in PICK:
    ids = np.where(ok & (yte == c))[0]
    idx.append(int(ids[np.argmin(np.abs(pte[ids, c] - target))]))
cols, z, a, pooled, f, h, p = forward(Xte[idx], P)
DIG = []
for n, i in enumerate(idx):
    zf = z[n].reshape(8, 8, NF)
    best = int(np.argmax(a[n][:, 0]))              # where filter 1 responds most: the callouts' example
    DIG.append({
        "img": Xte[i].astype(int), "a": a[n].T.reshape(NF, 64), "z": z[n].T.reshape(NF, 64),
        "pool": pooled[n].transpose(2, 0, 1).reshape(NF, 16), "h": h[n], "p": p[n], "label": int(yte[i]),
        "best": best,
    })

# ------------------------------------------------------------------ the clock
# Seconds; each digit runs on its own clock u, from 0 to DP. Round 3 (30 Sep 2026), the client:
# "fig 21, 23 yavaşlat" (slow them down). Every step of the explanation takes twice as long as in
# round 2, the window holds on each position of the first row before it glides on, and the
# pooling sweep rests on the block whose arithmetic is shown. The intro is unchanged.
T0, DP, NDG = .3, 14.0, 3                    # the first digit starts; one digit; three digits in turn
DIN, S0 = .4, .5                             # the digit fades in; the window lands on its first position
SLOW, SH = .32, .18                          # first row: a position every SLOW, held SH, then a glide
SF0 = S0 + 8 * SLOW
FAST = .044                                  # each of the other 56 positions
SEND = SF0 + 56 * FAST
REST = .6                                    # the window fades in where filter 1 responds most
P0, PBLK, PH = SEND + .24, .07, .4           # pooling: a block every PBLK, the block shown below PH more
PEND = P0 + 16 * PBLK + PH
FLD, FLOW = .6, .7                           # flatten; the values flowing on to the next layer
FL0 = PEND + .1
DN0 = FL0 + FLD + .1
OT0 = DN0 + FLOW + .14
PR0, PRD = OT0 + FLOW + .14, .5              # the prediction arrives
FOD = .5
FO = DP - .1 - FOD                           # the digit fades out, then .1 s blank
POSTER_T = T0 + 11.5                         # the first digit complete: reduced motion and print
CLOCK = dict(T0=T0, DP=DP, NDG=NDG, DIN=DIN, S0=S0, SLOW=SLOW, SH=SH, SF0=SF0, FAST=FAST, SEND=SEND, REST=REST,
             P0=P0, PBLK=PBLK, PH=PH, PEND=PEND, FL0=FL0, FLD=FLD, DN0=DN0, FLOW=FLOW, OT0=OT0, PR0=PR0,
             PRD=PRD, FO=FO, FOD=FOD, POSTER_T=POSTER_T)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-cnn: Figure 21, a convolutional network on handwritten digits")
say("")
say("MODEL")
say("  data: scikit-learn load_digits, 1797 images 8 x 8, grey levels 0..16, 10 classes;")
say("  1437 train, 360 held out (stratified, random_state 0); raw grey levels in.")
say(f"  conv {NF} filters 3 x 3, padding 1, bias, ReLU -> max pool 2 x 2 -> flatten {NF * 16} ->")
say(f"  dense {NH} ReLU -> dense 10 softmax; {sum(q.size for q in P)} parameters; cross-entropy;")
say(f"  Adam (lr {LR}), batch {BATCH}, {EPOCHS} epochs, seed {SEED}.")
say("")
say("CHECK 1: the numpy network against PyTorch (float64), 20 training images, untrained weights")
say(f"  conv2d output max |difference| {chk_conv:.1e}; max_pool2d {chk_pool:.1e};"
    f" every gradient (autograd) {chk_grad:.1e}")
say("")
say("CHECK 2: a filter response by hand: digit 1 shown, filter 1 at its strongest position")
d0 = DIG[0]; r, c = divmod(d0["best"], 8)
patch = np.pad(Xte[idx[0]], 1)[r:r + 3, c:c + 3]
hand = float((patch * P[0][:, 0].reshape(3, 3)).sum() + P[1][0])
say(f"  row {r}, column {c}: sum(patch x filter) + b = {hand:.6f}; the network's value {d0['z'][0][d0['best']]:.6f}")
say("")
say("CHECK 3: pooling keeps the largest value of each 2 x 2 block")
am = d0["a"][0].reshape(8, 8)
say(f"  max |pooled - block maximum| = {np.max(np.abs(d0['pool'][0].reshape(4, 4) - am.reshape(4, 2, 4, 2).max((1, 3)))):.1e}")
say("")
say("RESULT")
say(f"  training loss by epoch 10, 20, 30, 40: {[round(v, 4) for e, v in hist if e % 10 == 0]}")
say(f"  accuracy: training {acc_tr} of 1437, held out {acc_te} of 360 ({acc_te / 360:.1%})")
for d in DIG:
    say(f"  digit shown: label {d['label']}, predicted {int(np.argmax(d['p']))} with p = {d['p'].max():.4f};"
        f" probabilities sum to {d['p'].sum():.12f}")
say(f"  learned filters (rows of 3), bias: {np.round(P[0].T.reshape(NF, 3, 3), 3).tolist()}, {np.round(P[1], 3).tolist()}")
say("")
say("MOTION (round 3, 30 Sep 2026: the client asked for Figures 21 and 23 slower; round 2 in brackets)")
say(f"  intro unchanged; each digit on its own clock from 0 (the first digit's starts at t = {T0:g} s):")
say(f"  the digit fades in over {DIN:.2f} s [0.25]; the filter window lands on its first position at {S0:.2f} [0.30]")
say(f"  first row, where the arithmetic is shown: 8 positions x {SLOW:.2f} s [0.16], each held {SH:.2f} s,"
    f" then a {SLOW - SH:.2f} s glide [a 0.16 s glide, no hold]")
say(f"  the other 56 positions x {FAST:.3f} s [0.022]; the scan ends at {SEND:.2f} [2.81] and the window"
    f" fades in where filter 1 responds most over {REST:.2f} s [0.30]")
say(f"  pooling from {P0:.2f} [2.93]: 16 blocks x {PBLK:.2f} s [0.035], and {PH:.2f} s more on the block shown"
    f" below [none], which appears then [at the start]; done at {PEND:.2f} [3.49]")
say(f"  flatten {FLD:.2f} s [0.30]; on to the dense neurons {FLOW:.2f} s [0.35], to the class probabilities"
    f" {FLOW:.2f} s [0.35]")
say(f"  the prediction at {PR0:.2f} [4.73] over {PRD:.2f} s [0.28], held {FO - PR0 - PRD:.2f} s [1.64],"
    f" faded out over {FOD:.2f} s [0.30]")
say(f"  one digit {DP:.1f} s [7.0]; the three in turn loop every {NDG * DP:.1f} s [21.0]")
say(f"  poster (reduced motion, print) at t = {POSTER_T:.2f} s [6.30]: the first digit complete")
mc.check(NAME, L)

DATA = {"filt": P[0].T.reshape(NF, 9), "fb": P[1], "digits": DIG, "acc": [acc_tr, acc_te],
        "w1": P[2], "w2": P[4]}

JS = r"""
const D = DATA, NF = 3;
/* ------------------------------------------------ layout */
const PIX = { x: 24, y: 126, s: 15 }, FILT = { x: 190, s: 12, y: [70, 168, 266] };
const MAPS = { x: 270, s: 11, y: [44, 142, 240] }, POOL = { x: 410, s: 11, y: [66, 164, 262] };
const FLAT = { x: 508, y: 42, w: 10, h: 288 }, DEN = { x: 604, r: 6.5, gap: 19 }, OUT = { x: 704, r: 8, gap: 29 }, YC = 186;
const DY = i => YC + (i - 7.5) * DEN.gap, OY = j => YC + (j - 4.5) * OUT.gap;
const FY = k => FLAT.y + (k + .5) * FLAT.h / 48;
/* ------------------------------------------------ colours */
const grey = v => mixHex('#FFFFFF', C.ink, clamp(v / 16));
const wcol = w => w >= 0 ? mixHex('#FFFFFF', C.blue, clamp(w / .8)) : mixHex('#FFFFFF', K.red, clamp(-w / .8));
let AMAX = 1;
const act = v => mixHex('#FFFFFF', C.navy, clamp(v / AMAX));
/* ------------------------------------------------ the clock: three digits in turn (CLOCK, in the Python) */
/*CLOCK*/
function now() {
  if (t < T0) return { d: 0, u: -1 };
  const c = (t - T0) % (DP * NDG);
  return { d: Math.floor(c / DP), u: c - Math.floor(c / DP) * DP };
}
/* the filter window's position index at local time u (real, -1 before the scan). Along the
   first row, where the arithmetic is shown, it lands on each position and holds there SH before
   gliding to the next; from the second row on it sweeps one position every FAST */
function scanPos(u) {
  if (u < S0) return -1;
  if (u < SF0) { const k = Math.floor((u - S0) / SLOW); return k + (k < 7 ? easeInOut(clamp((u - S0 - k * SLOW - SH) / (SLOW - SH))) : 0); }
  if (u < SEND) return 8 + (u - SF0) / FAST;
  return 64;
}
/* the 2 x 2 block being pooled at local time u (-1 before, 16 after): PBLK each, and block pb,
   the one whose arithmetic is shown, PH longer */
function poolBlock(u, pb) {
  const s = u - P0;
  if (s < 0) return -1;
  if (s < pb * PBLK) return Math.floor(s / PBLK);
  if (s < (pb + 1) * PBLK + PH) return pb;
  return Math.min(16, Math.floor((s - PH) / PBLK));
}

function grid(x, y, n, s, col, alpha, o = {}) { cells(x, y, n, n, s, col, { alpha, gridColor: C.rule, gridWidth: .6, frame: C.ink, frameWidth: 1.1, ...o }); }

function draw() {
  const st = now(), Dg = D.digits[st.d], u = st.u;
  const fin = u >= 0 ? 1 - clamp((u - FO) / FOD) : 0;                  // this digit fading out at its end
  const din = u >= 0 ? clamp(u / DIN) : 0;
  const sp = scanPos(u), filled = Math.min(64, Math.floor(sp + 1e-9) + 1);   // positions whose value is known: those the window has reached
  const bk = Dg.best, br = Math.floor(bk / 8), bc = bk % 8;             // where filter 1 responds most
  const pb = Math.floor(br / 2) * 4 + Math.floor(bc / 2), pbl = poolBlock(u, pb);   // its 2 x 2 block; the block being pooled
  AMAX = Math.max(...Dg.a.map(r => Math.max(...r)), 1e-6);

  /* pixels */
  const ga = seg(0, .3);
  grid(PIX.x, PIX.y, 8, PIX.s, (i, j) => din > 0 ? mixHex('#FFFFFF', grey(Dg.img[i][j]), din * fin) : null, ga);
  /* learned filters */
  for (let f = 0; f < NF; f++) {
    const a = seg(.06 + .04 * f, .3);
    grid(FILT.x, FILT.y[f], 3, FILT.s, (i, j) => wcol(D.filt[f][i * 3 + j]), a);
    text(String(f + 1), FILT.x - 8, FILT.y[f] + 22, { size: 14, color: C.muted, align: 'right', alpha: a });
  }
  /* feature maps and pooled maps */
  const pk = pbl < 0 ? -1 : Math.min(16, pbl + 1);                       // pooled blocks known
  for (let f = 0; f < NF; f++) {
    const a = seg(.1 + .04 * f, .3);
    grid(MAPS.x, MAPS.y[f], 8, MAPS.s, (i, j) => { const k = i * 8 + j; return k < filled && u >= 0 ? mixHex('#FFFFFF', act(Dg.a[f][k]), fin) : null; }, a);
    grid(POOL.x, POOL.y[f], 4, POOL.s, (i, j) => { const k = i * 4 + j; return k < pk ? mixHex('#FFFFFF', act(Dg.pool[f][k]), fin) : null; }, seg(.16 + .04 * f, .3));
    // lines from each filter to its map
    line([[FILT.x + 36 + 4, FILT.y[f] + 18], [MAPS.x - 4, MAPS.y[f] + 44]], { color: C.guide, width: 1, alpha: seg(.2, .3) });
    line([[MAPS.x + 88 + 4, MAPS.y[f] + 44], [POOL.x - 4, POOL.y[f] + 22]], { color: C.guide, width: 1, alpha: seg(.24, .3) });
  }
  /* the filter window on the pixels, and the cell it writes in each map; it fades as the scan ends */
  const wa = u >= S0 ? fin * (1 - clamp((u - SEND) / .2)) : 0;
  if (wa > 0) {
    const q = Math.min(63, sp), r = Math.floor(q / 8), c = Math.min(7, q - 8 * r);
    rect(PIX.x + (c - 1) * PIX.s, PIX.y + (r - 1) * PIX.s, 3 * PIX.s, 3 * PIX.s, { stroke: C.accent, width: 2.2, alpha: wa });
    const k = Math.floor(q + 1e-9), rr = Math.floor(k / 8), cc = k % 8;
    for (let f = 0; f < NF; f++) rect(MAPS.x + cc * MAPS.s, MAPS.y[f] + rr * MAPS.s, MAPS.s, MAPS.s, { stroke: C.accent, width: 1.8, alpha: wa });
  }
  // after the scan: the window rests where filter 1 responds most
  const rest = u >= SEND ? clamp((u - SEND) / REST) : 0;
  if (rest > 0 && fin > 0) {
    rect(PIX.x + (bc - 1) * PIX.s, PIX.y + (br - 1) * PIX.s, 3 * PIX.s, 3 * PIX.s, { stroke: C.accent, width: 2.2, alpha: rest * fin });
    rect(MAPS.x + bc * MAPS.s, MAPS.y[0] + br * MAPS.s, MAPS.s, MAPS.s, { stroke: C.accent, width: 1.8, alpha: rest * fin });
  }
  /* pooling: the block being reduced */
  if (pbl >= 0 && u < PEND + .2 && fin > 0) {
    const b = Math.min(15, pbl), pr = Math.floor(b / 4), pc = b % 4;
    for (let f = 0; f < NF; f++) {
      rect(MAPS.x + 2 * pc * MAPS.s, MAPS.y[f] + 2 * pr * MAPS.s, 2 * MAPS.s, 2 * MAPS.s, { stroke: C.accent, width: 1.8, alpha: fin });
      rect(POOL.x + pc * POOL.s, POOL.y[f] + pr * POOL.s, POOL.s, POOL.s, { stroke: C.accent, width: 1.8, alpha: fin });
    }
  }
  /* flatten */
  const fl = u < FL0 ? 0 : clamp((u - FL0) / FLD);
  rect(FLAT.x, FLAT.y, FLAT.w, FLAT.h, { stroke: C.ink, width: 1.1, alpha: seg(.2, .3) });
  if (fl > 0) {
    const nk = Math.floor(48 * fl);
    for (let k = 0; k < nk; k++) {
      const f = Math.floor(k / 16), q = k % 16;
      rect(FLAT.x, FLAT.y + k * FLAT.h / 48, FLAT.w, FLAT.h / 48 + .3, { fill: mixHex('#FFFFFF', act(Dg.pool[f][q]), fin), stroke: null });
    }
    rect(FLAT.x, FLAT.y, FLAT.w, FLAT.h, { stroke: C.ink, width: 1.1 });
  }
  for (let f = 0; f < NF; f++) line([[POOL.x + 44 + 4, POOL.y[f] + 22], [FLAT.x - 4, FLAT.y + (f + .5) * FLAT.h / 3]], { color: C.guide, width: 1, alpha: seg(.28, .3) });
  /* dense neurons, fully connected */
  const ea = seg(.25, .35);
  const dnf = u < DN0 ? 0 : clamp((u - DN0) / FLOW), otf = u < OT0 ? 0 : clamp((u - OT0) / FLOW);
  ctx.save(); ctx.lineWidth = .5; ctx.strokeStyle = C.guide; ctx.globalAlpha = .16 * ea; ctx.beginPath();
  for (let k = 0; k < 48; k++) for (let i = 0; i < 16; i++) { ctx.moveTo(FLAT.x + FLAT.w, FY(k)); ctx.lineTo(DEN.x - DEN.r, DY(i)); }
  for (let i = 0; i < 16; i++) for (let j = 0; j < 10; j++) { ctx.moveTo(DEN.x + DEN.r, DY(i)); ctx.lineTo(OUT.x - OUT.r, OY(j)); }
  ctx.stroke(); ctx.restore();
  if (dnf > 0 && dnf < 1) flowLines(FLAT.x + FLAT.w, FY, 48, DEN.x - DEN.r, DY, 16, dnf);
  if (otf > 0 && otf < 1) flowLines(DEN.x + DEN.r, DY, 16, OUT.x - OUT.r, OY, 10, otf);
  const hmax = Math.max(...Dg.h, 1e-6);
  for (let i = 0; i < 16; i++) node(DEN.x, DY(i), DEN.r, { fill: dnf >= 1 ? mixHex('#FFFFFF', mixHex('#FFFFFF', C.blue, Dg.h[i] / hmax), fin) : '#FFFFFF', width: 1.1, alpha: seg(.3 + .01 * i, .3) });
  /* class probabilities */
  const pred = Dg.p.indexOf(Math.max(...Dg.p));
  for (let j = 0; j < 10; j++) {
    const a = seg(.34 + .01 * j, .3), y = OY(j), win = j === pred && otf >= 1;
    node(OUT.x, y, OUT.r, { fill: otf >= 1 ? mixHex('#FFFFFF', mixHex('#FFFFFF', C.blue, Dg.p[j]), fin) : '#FFFFFF', width: 1.2, alpha: a });
    math(String(j), OUT.x + 20, y + 5, { size: 15, color: win ? mixHex(C.body, C.accent, fin) : C.body, alpha: a });
    const bw = 80 * Dg.p[j] * easeOut(otf);
    rect(OUT.x + 34, y - 5, 80, 10, { stroke: C.rule, width: .8, alpha: a });
    if (otf > 0) rect(OUT.x + 34, y - 5, Math.max(.4, bw), 10, { fill: win ? C.accent : C.blue, stroke: null, alpha: fin });
    if (otf > 0 && Dg.p[j] >= .005) math(Dg.p[j].toFixed(2), OUT.x + 120, y + 5, { size: 14, color: win ? C.accent : C.body, alpha: fin * otf });
  }
  /* the prediction */
  const pa = u < PR0 ? 0 : clamp((u - PR0) / PRD) * fin;
  text('predicted', 870, 150 + rise(pa), { size: 16, color: C.body, alpha: pa });
  text(String(pred), 870, 196 + rise(pa), { size: 40, color: C.accent, alpha: pa });
  text(`true label ${Dg.label}`, 870, 226 + rise(pa), { size: 15, color: C.muted, alpha: pa });

  /* stage names, his words */
  const sl = [['pixels', PIX.x + 60], ['learned filters', FILT.x + 18], ['feature maps', MAPS.x + 44], ['pooling', POOL.x + 22],
              ['flatten', FLAT.x + 5], ['dense neurons', DEN.x], ['class probabilities', OUT.x + 70]];
  sl.forEach(([s, x], k) => { const a = lab(.12 + .04 * k); text(s, x, 368 + rise(a), { size: 15, color: C.body, align: 'center', alpha: a }); });
  line([[18, 386], [982, 386]], { color: C.rule, width: 1, alpha: lab(.3) });

  /* the arithmetic of one filter position, and of one pooling block */
  const ca = lab(.35);
  let q = -1;
  if (u >= S0 && u < SF0) q = Math.floor(sp + 1e-9);                   // the position the window last landed on
  else if (u >= SF0 && u < SEND) q = 7;
  else if (u >= SEND) q = bk;
  const cr = q >= 0 ? Math.floor(q / 8) : 0, cc_ = q >= 0 ? q % 8 : 0, cv = q >= 0 ? fin : 0;
  text('filter 1 at the window', 24, 414 + rise(ca), { size: 16, color: C.body, alpha: ca });
  const CS = 34, gx = 24, gy = 424;
  const pv = (i, j) => { const rr = cr + i - 1, cc = cc_ + j - 1; return rr < 0 || rr > 7 || cc < 0 || cc > 7 ? 0 : Dg.img[rr][cc]; };
  cells(gx, gy, 3, 3, CS, (i, j) => q >= 0 ? mixHex('#FFFFFF', grey(pv(i, j)), .45 * cv) : null, { alpha: ca, gridColor: C.rule });
  cells(gx + 3 * CS + 34, gy, 3, 3, CS, (i, j) => mixHex('#FFFFFF', wcol(D.filt[0][i * 3 + j]), .55), { alpha: ca, gridColor: C.rule });
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
    if (q >= 0) math(String(pv(i, j)), gx + j * CS + CS / 2, gy + i * CS + CS / 2 + 5, { size: 14, align: 'center', alpha: cv * ca });
    math(num(D.filt[0][i * 3 + j], 1), gx + 3 * CS + 34 + j * CS + CS / 2, gy + i * CS + CS / 2 + 5, { size: 14, align: 'center', alpha: ca });
  }
  math('\\times', gx + 3 * CS + 17, gy + 1.5 * CS + 5, { size: 17, align: 'center', alpha: ca });
  const tx = gx + 6 * CS + 50;
  math('\\rm{sum\\ of\\ products} + b', tx, gy + 22, { size: 16, color: C.body, alpha: ca });
  if (q >= 0) {
    math(`= ${num(Dg.z[0][q], 1)}`, tx, gy + 48, { size: 16, alpha: cv * ca });
    math(`\\rm{ReLU:}\\ \\ ${num(Dg.a[0][q], 1)}`, tx, gy + 76, { size: 16, color: C.accent, alpha: cv * ca });
  }
  // pooling: the block holding that position, shown once the sweep reaches it
  const px0 = 640;
  text('pooling, one 2 × 2 block', px0, 414 + rise(ca), { size: 16, color: C.body, alpha: ca });
  const pr0 = Math.floor(pb / 4) * 2, pc0 = (pb % 4) * 2;
  const pvis = pbl >= pb ? fin : 0;
  cells(px0, gy + 15, 2, 2, CS, (i, j) => pvis > 0 ? mixHex('#FFFFFF', act(Dg.a[0][(pr0 + i) * 8 + pc0 + j]), .35 * pvis) : null, { alpha: ca, gridColor: C.rule });
  let mx = -1, mi = 0; for (let i = 0; i < 4; i++) { const v = Dg.a[0][(pr0 + (i >> 1)) * 8 + pc0 + (i & 1)]; if (v > mx) { mx = v; mi = i; } }
  if (pvis > 0) {
    for (let i = 0; i < 4; i++) math(num(Dg.a[0][(pr0 + (i >> 1)) * 8 + pc0 + (i & 1)], 1), px0 + (i & 1) * CS + CS / 2, gy + 15 + (i >> 1) * CS + CS / 2 + 5, { size: 14, align: 'center', alpha: pvis * ca });
    rect(px0 + (mi & 1) * CS, gy + 15 + (mi >> 1) * CS, CS, CS, { stroke: C.accent, width: 2, alpha: pvis * ca });
    math(`\\rm{max} = ${num(mx, 1)}`, px0 + 2 * CS + 16, gy + 15 + CS + 5, { size: 16, color: C.accent, alpha: pvis * ca });
  }
  text(`scikit-learn digits, 8 × 8 pixels; 3 learned 3 × 3 filters, 2 × 2 max pooling, 16 dense ReLU, 10 softmax; held out accuracy ${D.acc[1]}/360`,
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
}
/* data flowing along the dense connections: each line drawn from its start by p */
function flowLines(x0, Y0, n0, x1, Y1, n1, p) {
  ctx.save(); ctx.lineWidth = .7; ctx.strokeStyle = C.blue; ctx.globalAlpha = .28; ctx.beginPath();
  const e = easeOut(p);
  for (let a = 0; a < n0; a++) for (let b = 0; b < n1; b++) {
    const ya = Y0(a), yb = Y1(b);
    ctx.moveTo(x0, ya); ctx.lineTo(lerp(x0, x1, e), lerp(ya, yb, e));
  }
  ctx.stroke(); ctx.restore();
}
boot();
"""
assert JS.count("/*CLOCK*/") == 1
JS = JS.replace("/*CLOCK*/", "const " + ", ".join(f"{k} = {round(v, 6):g}" for k, v in CLOCK.items()) + ";")

TITLE = "Figure 21: CNN architecture"
ARIA = ("A small convolutional network reading a handwritten digit of 8 by 8 pixels. A 3 by 3 window slides "
        "over the pixels and three learned filters turn them into three feature maps, filled in as the window "
        "moves; the arithmetic of one window position is shown below. Two by two max pooling keeps the "
        "strongest value of each block, the pooled values are flattened, and dense neurons produce ten class "
        "probabilities, the largest on the right digit. Three held out digits are read in turn.")

if __name__ == "__main__":
    print(f"accuracy {acc_tr}/1437, {acc_te}/360; checks conv {chk_conv:.1e} pool {chk_pool:.1e} grad {chk_grad:.1e}")
    mc.publish(NAME, TITLE, ARIA, 1000, 570, DATA, JS,
               look=(0.3, 0.8, 1.2, 1.9, 2.5, 4.6, 6.2, 6.8, 7.9, 8.6, 9.5, 10.4, 11.8, 14.1, 17.0))
