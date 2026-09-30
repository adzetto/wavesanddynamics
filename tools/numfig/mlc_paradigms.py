"""Figure 27 of the machine learning guide (image24): reinforcement learning
beside supervised and unsupervised learning, what feeds each model and what it
learns to do with it.

(a) Supervised: 90 labeled examples of three classes (two features); softmax
    regression fitted by gradient descent; it learns to predict the label of a
    new point.
(b) Unsupervised: the same 90 points without their labels; k-means (k = 3)
    finds three groups on its own.
(c) Reinforcement: no examples at all; the agent of Figure 30 (mlc_grid.py)
    feeds on the rewards its own actions earn, and learns a strategy.

Every boundary drawn is the model's own at that iteration: the page clips the
plot to the half planes of the fitted linear scores (softmax) or of the
centroids (k-means). (c) replays the run's transcript as Figure 30 does.

Run: python tools/numfig/mlc_paradigms.py
"""
import numpy as np

import common
import mlc_grid as g
import mlc_lib as lib

NAME = "mlc-paradigms"

# ------------------------------------------------------------------ the data
rng = np.random.default_rng(5)
CENTRES = np.array([[2.6, 3.0], [7.2, 2.8], [5.0, 7.4]])
NPER, SIG = 30, 0.95
X = np.vstack([rng.normal(c, SIG, (NPER, 2)) for c in CENTRES])
X = np.clip(X, 0.3, 9.7).round(2)
y = np.repeat(np.arange(3), NPER)

# ------------------------------------------------------------------ (a) softmax regression
mu, sd = X.mean(0), X.std(0)
Z = (X - mu) / sd
W = rng.normal(0, 0.3, (3, 2))
b = np.zeros(3)
Y = np.eye(3)[y]
LR, ITERS = 0.3, 60
sm, hist = [], []
for it in range(ITERS + 1):
    s = Z @ W.T + b
    s -= s.max(1, keepdims=True)
    P = np.exp(s)
    P /= P.sum(1, keepdims=True)
    hist.append((it, -np.mean(np.log(P[np.arange(len(y)), y])), np.mean(P.argmax(1) == y)))
    Wr = W / sd                                   # scores in raw feature units
    br = b - (W / sd) @ mu
    sm.append(np.column_stack([Wr, br]).round(5).tolist())
    G = (P - Y) / len(y)
    W = W - LR * G.T @ Z
    b = b - LR * G.sum(0)

# ------------------------------------------------------------------ (b) k-means
KSEED = 4
c = X[np.random.default_rng(KSEED).choice(len(X), 3, replace=False)].copy()
km = [{"c": c.round(4).tolist(), "lab": None}]
lab_old = None
while True:
    lab = np.argmin(((X[:, None] - c[None]) ** 2).sum(2), 1)
    if lab_old is not None and np.all(lab == lab_old):
        break
    km[-1]["lab"] = lab.tolist()
    c = np.array([X[lab == k].mean(0) for k in range(3)])
    km.append({"c": c.round(4).tolist(), "lab": None})
    lab_old = lab
km[-1]["lab"] = lab.tolist()
purity = sum(np.bincount(y[lab == k]).max() for k in range(3)) / len(y)

# ------------------------------------------------------------------ (c) the grid world run
snaps, log = g.run()
rets = []
acc = 0.0
for rec in log:
    acc += rec[3]
    if rec[5]:
        rets.append(acc)
        acc = 0.0
rets = np.array(rets)

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-paradigms: Figure 27, three kinds of learning side by side")
say("")
say("DATA (a), (b): 3 classes x 30 points, Gaussian, sigma 0.95, centres "
    f"{CENTRES.tolist()}, numpy seed 5; features clipped to [0.3, 9.7].")
say("")
say("(a) SUPERVISED: softmax regression on standardised features, gradient descent, rate "
    f"{LR}, {ITERS} iterations from small random weights.")
for it in (0, 5, 10, 20, 40, 60):
    say(f"  iteration {it:2d}: cross entropy {hist[it][1]:.4f}, training accuracy {hist[it][2]:.3f}")
say("  check: the loss falls monotonically: "
    f"{all(hist[i + 1][1] <= hist[i][1] + 1e-12 for i in range(ITERS))}")
from sklearn.linear_model import LogisticRegression  # noqa: E402
ref = LogisticRegression(C=1e6, max_iter=5000).fit(Z, y)
say(f"  check: an unregularised solver (sklearn) also separates the classes: accuracy {ref.score(Z, y):.3f}")
say("")
say(f"(b) UNSUPERVISED: k-means, k = 3, Lloyd's algorithm from 3 data points (seed {KSEED}),")
say(f"  {len(km) - 1} updates to convergence (assignments stop changing).")
for i, st in enumerate(km):
    say(f"  step {i}: centroids {np.round(st['c'], 2).tolist()}")
say(f"  check: groups against the hidden labels, purity {purity:.3f} (1 point in the overlap)")
from sklearn.cluster import KMeans  # noqa: E402
sk = KMeans(3, n_init=20, random_state=0).fit(X)
d = np.max([np.min(np.linalg.norm(sk.cluster_centers_ - np.array(ci), axis=1)) for ci in km[-1]["c"]])
say(f"  check: sklearn KMeans (20 restarts) finds the same centroids to {d:.1e}")
say("")
say("(c) REINFORCEMENT: the run of Figure 30 (grid world, Q-learning, seed 21); what feeds it")
say("  is the reward its own actions earn; total reward per episode = 1 - 0.02 (steps - 1).")
say(f"  episodes 1-10: {np.round(rets[:10], 2).tolist()}")
say(f"  mean of the last 50: {rets[-50:].mean():.3f} (best possible 0.86, 8 steps; epsilon 0.2")
say("  still explores at the end)")
say(f"  check: total rewards match the episode lengths: "
    f"{np.allclose(rets, 1 - 0.02 * (np.diff([0] + [k + 1 for k, r in enumerate(log) if r[5]]) - 1))}")

code = np.array([rec[1] * 4 + rec[2] for rec in log])
DATA = {"X": X.tolist(), "y": y.tolist(), "sm": sm, "km": km, "ret": rets.round(3).tolist(),
        "tr": common.i8(code), "n": len(log)}

JS = r"""
/* ---- (c): the run of Figure 30, replayed from its transcript */
const TR = b64i8(DATA.tr), NS = DATA.n, MOVE = [[0, 1], [0, -1], [-1, 0], [1, 0]];
const VS = new Float32Array((NS + 1) * 25), AM = new Int8Array((NS + 1) * 25), ENDS = [0];
(() => {
  const Q = new Float64Array(100); let s = 0;
  const snap = k => { for (let c = 0; c < 25; c++) { let m = Q[c * 4], am = 0;
    for (let a = 1; a < 4; a++) if (Q[c * 4 + a] > m) { m = Q[c * 4 + a]; am = a; } VS[k * 25 + c] = m; AM[k * 25 + c] = am; } };
  snap(0);
  for (let k = 0; k < NS; k++) {
    const a = TR[k] & 3, x = s % 5, y = (s / 5) | 0;
    const s2 = Math.min(4, Math.max(0, y + MOVE[a][1])) * 5 + Math.min(4, Math.max(0, x + MOVE[a][0])), done = s2 === 24;
    let mx = Q[s2 * 4]; for (let b = 1; b < 4; b++) mx = Math.max(mx, Q[s2 * 4 + b]);
    const before = Q[s * 4 + a]; Q[s * 4 + a] = before + 0.5 * ((done ? 1 : -0.02) + (done ? 0 : 0.95 * mx) - before);
    s = done ? 0 : s2; snap(k + 1); if (done) ENDS.push(k + 1);
  }
})();
const ROUTE = [0];
for (let i = 0, s = 0; i < 24 && s !== 24; i++) { const a = AM[NS * 25 + s], x = s % 5, y = (s / 5) | 0;
  s = Math.min(4, Math.max(0, y + MOVE[a][1])) * 5 + Math.min(4, Math.max(0, x + MOVE[a][0])); ROUTE.push(s); }
/* ---- clocks: learning from T0 for DL seconds, then the models at work */
const T0 = .6, DL = 3.0, TU = T0 + DL + .3;
const POSTER_T = TU + 1.45;               // the models at work: a new point, the agent on its way
const COL = [20, 350, 680], PW = 190, PH = 140, PY1 = 84, PY2 = 410, MB = 316, RY = PY2 + PH + 78;
const px = k => COL[k] + 78;
/* ---- geometry: clip a polygon to a x + b y + c >= 0 (Sutherland and Hodgman) */
function clipPoly(poly, a, b, c) {
  const out = [];
  for (let i = 0; i < poly.length; i++) {
    const P = poly[i], Q = poly[(i + 1) % poly.length], fp = a * P[0] + b * P[1] + c, fq = a * Q[0] + b * Q[1] + c;
    if (fp >= 0) out.push(P);
    if ((fp >= 0) !== (fq >= 0)) { const s = fp / (fp - fq); out.push([P[0] + s * (Q[0] - P[0]), P[1] + s * (Q[1] - P[1])]); }
  }
  return out;
}
/* the region where score k is the largest, for linear scores [wx, wy, b] */
function regions(lin) {
  return lin.map((li, i) => { let p = [[0, 0], [10, 0], [10, 10], [0, 10]];
    for (let j = 0; j < lin.length && p.length; j++) if (j !== i) p = clipPoly(p, li[0] - lin[j][0], li[1] - lin[j][1], li[2] - lin[j][2]);
    return p; });
}
const TINT = ['rgba(4,48,82,.10)', 'rgba(9,90,148,.13)', 'rgba(91,141,184,.20)'];
const MARKC = [C.navy, C.blue, C.sky];
function mark(k, x, y, o = {}) {           // circle, square, triangle: the three labels
  const { r = 5, alpha = 1, fill = MARKC[k] } = o;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = fill; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1; ctx.beginPath();
  if (k === 0) ctx.arc(x, y, r, 0, 2 * Math.PI);
  else if (k === 1) ctx.rect(x - r * .88, y - r * .88, r * 1.76, r * 1.76);
  else { ctx.moveTo(x, y - r * 1.15); ctx.lineTo(x + r * 1.05, y + r * .75); ctx.lineTo(x - r * 1.05, y + r * .75); ctx.closePath(); }
  ctx.fill(); ctx.stroke(); ctx.restore();
}
function diamond(x, y, r, alpha) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = C.accent; ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.beginPath();
  ctx.moveTo(x, y - r); ctx.lineTo(x + r, y); ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath(); ctx.fill(); ctx.stroke(); ctx.restore();
}
function feat(k, y0, prog) {
  return axes({ x: px(k), y: y0, w: PW, h: PH, xlim: [0, 10], ylim: [0, 10], xticks: [0, 5, 10], yticks: [0, 5, 10],
    xlabel: 'x_{1}', ylabel: 'x_{2}', ylabelGap: 30, progress: prog, tickSize: 14, labelSize: 16 });
}
function fillRegions(g, polys, alpha, stroke = true) {
  polys.forEach((p, k) => { if (p.length < 3) return;
    const pts = p.map(v => [g.X(v[0]), g.Y(v[1])]);
    ctx.save(); ctx.globalAlpha = alpha; ctx.fillStyle = TINT[k]; ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    for (const q of pts) ctx.lineTo(q[0], q[1]); ctx.closePath(); ctx.fill(); ctx.restore();
    if (stroke) line(pts.concat([pts[0]]), { color: C.ink, width: 1.2, alpha }); });
}
/* the new point the trained models are shown: a closed path through all three classes */
const query = u => [5.1 + 3.0 * Math.cos(2 * Math.PI * u + .6), 5.0 + 2.9 * Math.sin(2 * Math.PI * u + .6)];
const QP = 7.5;                                       // seconds per round of the path
function title(s, k, y, t0) { lab(s, px(k) + PW / 2, y, t0, { size: 16, color: C.body, align: 'center' }); }
function modelBox(k, word, t0) {
  const cx = px(k) + PW / 2, a = seg(t0, .35);
  carrow([[cx, PY1 + PH + 56], [cx, MB - 2]], { width: 1.5, progress: seg(t0 + .05, .3) });
  box(cx - 50, MB, 100, 34, { fill: C.steel, width: 1.4, progress: a });
  lab(word, cx, MB + 23, t0 + .1, { size: 16, align: 'center' });
  carrow([[cx, MB + 34], [cx, PY2 - 30]], { width: 1.5, progress: seg(t0 + .12, .3) });
}
function softmax(lin, p) { const s = lin.map(l => l[0] * p[0] + l[1] * p[1] + l[2]), m = Math.max(...s), e = s.map(v => Math.exp(v - m)), z = e.reduce((a, b) => a + b, 0); return e.map(v => v / z); }
function draw() {
  const u = clamp((t - T0) / DL), use = t >= TU, qu = use ? ((t - TU) / QP) % 1 : 0, qa = use ? clamp((t - TU) / .3) : 0;
  const q = query(qu);
  // ================= (a) supervised
  sub('a', 18, 36, 'supervised learning', seg(.08, .3));
  title('labeled examples', 0, PY1 - 10, .2);
  let g = feat(0, PY1, seg(.05, .4));
  g.inside(() => DATA.X.forEach((p, i) => mark(DATA.y[i], g.X(p[0]), g.Y(p[1]), { alpha: seg(.15 + i * .004, .25) })));
  modelBox(0, 'model', .3);
  title('predicted label', 0, PY2 - 10, .4);
  g = feat(0, PY2, seg(.25, .4));
  const it = Math.min(DATA.sm.length - 1, Math.floor(u * u * (DATA.sm.length - 1) * 1.0001)), lin = DATA.sm[it];   // early iterations get the time: that is where the boundaries move
  g.inside(() => { fillRegions(g, regions(lin), seg(T0 - .1, .3));
    DATA.X.forEach((p, i) => mark(DATA.y[i], g.X(p[0]), g.Y(p[1]), { r: 3.6, alpha: .45 * seg(.35, .3) }));
    if (use) diamond(g.X(q[0]), g.Y(q[1]), 7, qa); });
  box(px(0), PY2, PW, PH, { width: 1.3, alpha: seg(.25, .3) });
  const pr = softmax(DATA.sm[DATA.sm.length - 1], q), kq = pr.indexOf(Math.max(...pr));
  if (!use) text(`gradient descent, iteration ${it}`, px(0), RY, { size: 14, color: C.muted, alpha: seg(T0, .3) });
  else { text('new point:', px(0), RY, { size: 15, color: C.body, alpha: qa });
    mark(kq, px(0) + 82, RY - 5, { r: 5.5, alpha: qa });
    math(`p = ${nf(pr[kq], 2)}`, px(0) + 100, RY, { size: 15, alpha: qa }); }
  // ================= (b) unsupervised
  sub('b', 348, 36, 'unsupervised learning', seg(.12, .3));
  title('unlabeled data', 1, PY1 - 10, .25);
  g = feat(1, PY1, seg(.1, .4));
  g.inside(() => DATA.X.forEach((p, i) => dot(g.X(p[0]), g.Y(p[1]), 3.4, { color: '#fff', fill: C.ink, width: .8, alpha: seg(.2 + i * .004, .25) })));
  modelBox(1, 'model', .35);
  title('discovered structure', 1, PY2 - 10, .45);
  g = feat(1, PY2, seg(.3, .4));
  const KM = DATA.km, ks = u * (KM.length - 1), ki = Math.min(KM.length - 1, Math.floor(ks)), kf = ks - ki;
  // assignment by the current centroids, then the centroids glide to their new means
  const cNow = KM[ki].c.map((c0, j) => ki + 1 < KM.length ? [lerp(c0[0], KM[ki + 1].c[j][0], easeInOut(clamp((kf - .35) / .55))), lerp(c0[1], KM[ki + 1].c[j][1], easeInOut(clamp((kf - .35) / .55)))] : c0);
  const labNow = KM[ki].lab;
  const vor = cNow.map(c => [2 * c[0], 2 * c[1], -(c[0] * c[0] + c[1] * c[1])]);
  const pb = seg(T0 - .1, .3);
  g.inside(() => { fillRegions(g, regions(vor), pb);
    DATA.X.forEach((p, i) => dot(g.X(p[0]), g.Y(p[1]), 3.2, { color: '#fff', fill: C.body, width: .8, alpha: .5 * pb }));
    // each centroid's number sits outside the group, away from the other two (from their mean
    // out through the centroid): clear of their marks while they start close together
    const mX = cNow.reduce((s, c) => s + g.X(c[0]), 0) / 3, mY = cNow.reduce((s, c) => s + g.Y(c[1]), 0) / 3;
    cNow.forEach((c, j) => { const X = g.X(c[0]), Y = g.Y(c[1]);         // a centroid: pgfplots' otimes mark
      dot(X, Y, 8.5, { color: C.ink, fill: '#fff', width: 1.4, alpha: pb });
      line([[X - 4.6, Y - 4.6], [X + 4.6, Y + 4.6]], { width: 1.6, alpha: pb }); line([[X - 4.6, Y + 4.6], [X + 4.6, Y - 4.6]], { width: 1.6, alpha: pb });
      const dx = X - mX, dy = Y - mY, dl = Math.hypot(dx, dy) || 1, ux = dl > 1 ? dx / dl : .6, uy = dl > 1 ? dy / dl : -.8;
      text(String(j + 1), X + 19 * ux, Y + 19 * uy + 5, { size: 15, align: 'center', alpha: pb }); });
    if (use) diamond(g.X(q[0]), g.Y(q[1]), 7, qa); });
  box(px(1), PY2, PW, PH, { width: 1.3, alpha: seg(.3, .3) });
  const cF = KM[KM.length - 1].c, dq = cF.map(c => Math.hypot(c[0] - q[0], c[1] - q[1])), gq = dq.indexOf(Math.min(...dq));
  if (!use) text(`k-means, update ${Math.min(KM.length - 1, Math.round(ks))}`, px(1), RY, { size: 14, color: C.muted, alpha: seg(T0, .3) });
  else text(`new point: group ${gq + 1}`, px(1), RY, { size: 15, color: C.body, alpha: qa });
  // ================= (c) reinforcement
  sub('c', 678, 36, 'reinforcement learning', seg(.16, .3));
  title('rewards from its own actions', 2, PY1 - 10, .3);
  const ep = Math.floor(u * 300 * 1.0001), R = DATA.ret;
  g = axes({ x: px(2), y: PY1, w: PW, h: PH, xlim: [0, 300], ylim: [-1.5, 1], xticks: [0, 100, 200, 300], yticks: [-1, 0, 1],
    xlabel: '\\rm{episode}', ylabel: '\\rm{total\\ reward}', ylabelGap: 34, progress: seg(.15, .4), tickSize: 14, labelSize: 16 });
  g.inside(() => { line([[g.X(0), g.Y(0)], [g.X(300), g.Y(0)]], { color: C.rule, width: 1 });
    for (let i = 0; i < Math.min(ep, 300); i++) dot(g.X(i + .5), g.Y(R[i]), 1.7, { color: C.navy, fill: C.navy, width: .5 }); });
  modelBox(2, 'agent', .4);
  title('a strategy', 2, PY2 - 10, .5);
  const cs = 28, gx0 = px(2) + (PW - 5 * cs) / 2, gy0 = PY2;
  const k = ENDS[Math.min(ep, 300)], ga = seg(.35, .4);
  for (let s = 0; s < 25; s++) {
    const X = gx0 + (s % 5) * cs, Y = gy0 + (4 - ((s / 5) | 0)) * cs;
    if (s === 24) { box(X, Y, cs, cs, { fill: C.accent, stroke: null, alpha: ga }); continue; }
    const V = VS[k * 25 + s];
    if (V > 0) { const d = MOVE[AM[k * 25 + s]], L = 7; arrow(X + cs / 2 - d[0] * L, Y + cs / 2 + d[1] * L, X + cs / 2 + d[0] * L, Y + cs / 2 - d[1] * L, { color: C.blue, width: 1.5, head: 7, alpha: ga }); }
  }
  for (let i = 1; i < 5; i++) { line([[gx0 + i * cs, gy0], [gx0 + i * cs, gy0 + 5 * cs]], { color: C.rule, width: 1, alpha: ga });
    line([[gx0, gy0 + i * cs], [gx0 + 5 * cs, gy0 + i * cs]], { color: C.rule, width: 1, alpha: ga }); }
  box(gx0, gy0, 5 * cs, 5 * cs, { width: 1.3, progress: ga });
  // the agent using its strategy; each arrival closes the loop
  const WALK = .26, lap = .2 + (ROUTE.length - 1) * WALK + .8;
  let ax = gx0 + cs / 2, ay = gy0 + 4.5 * cs, aA = 0, lu = -1;
  if (use) { lu = (t - TU) % lap; const kk = clamp((lu - .2) / WALK, 0, ROUTE.length - 1), j = Math.min(ROUTE.length - 2, Math.floor(kk)), f = kk >= ROUTE.length - 1 ? 1 : easeInOut(kk - j);
    const A = ROUTE[j], B = ROUTE[j + 1];
    ax = gx0 + (lerp(A % 5, B % 5, f) + .5) * cs; ay = gy0 + (4 - lerp((A / 5) | 0, (B / 5) | 0, f) + .5) * cs;
    aA = clamp(lu / .2) * (1 - clamp((lu - lap + .25) / .25)); }
  if (aA > 0) dot(ax, ay, 5.5, { color: '#fff', fill: C.navy, width: 1.6, alpha: aA });
  if (!use) text(`Q-learning, episode ${Math.min(ep, 300)}`, px(2), RY, { size: 14, color: C.muted, alpha: seg(T0, .3) });
  else text('follows its strategy', px(2), RY, { size: 15, color: C.body, alpha: qa });
  // the loop closes: from the strategy, through its actions, back to its rewards
  const xl = px(2) + PW + 30, loop = [[gx0 + 5 * cs + 6, gy0 + 2.5 * cs], [xl, gy0 + 2.5 * cs], [xl, PY1 + PH / 2], [px(2) + PW + 6, PY1 + PH / 2]];
  const la = seg(.5, .45);
  carrow(loop, { width: 1.5, progress: la, color: C.ink });
  lab('acts', xl - 8, MB + 22, .7, { size: 16, align: 'right' });
  if (use) { const w = clamp((lu - .2 - (ROUTE.length - 1) * WALK) / .6);
    if (w > 0 && w < 1) { let Lt = 0; const seglen = []; for (let i = 1; i < loop.length; i++) { seglen.push(Math.hypot(loop[i][0] - loop[i - 1][0], loop[i][1] - loop[i - 1][1])); Lt += seglen[i - 1]; }
      let d = easeInOut(w) * Lt, i = 0; while (i < seglen.length - 1 && d > seglen[i]) { d -= seglen[i]; i++; }
      const s = d / seglen[i]; dot(lerp(loop[i][0], loop[i + 1][0], s), lerp(loop[i][1], loop[i + 1][1], s), 4, { color: C.navy, fill: C.navy, alpha: Math.sin(Math.PI * w) }); } }
}
boot();
"""

TITLE = ("Figure 27: Reinforcement learning compared with supervised and unsupervised learning: what feeds "
         "the model, and what it learns to do with it")
ARIA = ("Three columns. Supervised learning: labeled points of three classes feed a model that "
        "learns to predict the label of a new point. Unsupervised learning: the same points without "
        "labels feed a model that discovers three groups. Reinforcement learning: the rewards the "
        "agent's own actions earn feed it, it learns a strategy for a grid world, and an arrow from "
        "the strategy back to the rewards closes the loop.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 640, DATA, JS, L))
