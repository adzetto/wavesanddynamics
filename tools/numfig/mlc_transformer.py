"""Figure 24 of the machine learning guide (image21): transformer architecture
and attention, computed on a real (tiny) transformer.

mlc_text.tiny_transformer(): two blocks (multi-head attention with 2 heads,
add and norm, feed forward, add and norm), 8 numbers per token, sinusoidal
positions, trained on the 88 sentences of mlc_text.py to predict the next
word. The figure follows "The cat sat" through it: the tokens, their vectors
(embedding plus position), the attention weights of every token on every
other in both blocks, the vectors each block builds, and the probability of
the next word. Every number is the trained model's.

Run: python tools/numfig/mlc_transformer.py  (trains once, ~2 min; the
results are cached in the temp directory)
"""
import os
import tempfile

import numpy as np

import mlc_lib as lib
import mlc_text as T

NAME = "mlc-transformer"
SEED = 0
CACHE = os.path.join(tempfile.gettempdir(), f"mlc_transformer_seed{SEED}.npz")
TOKS = ["The", "cat", "sat"]

if os.path.isfile(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    R = {k: z[k] for k in z.files}
else:
    import torch
    torch.set_num_threads(1)
    model, vocab, pe, info = T.tiny_transformer(seed=SEED)
    ix = {w: i for i, w in enumerate(vocab)}
    with torch.no_grad():
        logits, trace, atts = model(torch.tensor([[ix[w] for w in TOKS]]), torch.tensor([3]))
        emb = model.emb.weight[[ix[w] for w in TOKS]].numpy()
        p = torch.softmax(logits[0], 0).numpy()
        logits2 = model(torch.tensor([[ix["The"], ix["dog"], ix["sat"]]]), torch.tensor([3]))[0]
        p2 = torch.softmax(logits2[0], 0).numpy()
    R = {"emb": emb, "pe": pe[:3], "x0": trace[0][0].numpy(), "x1": trace[1][0].numpy(), "x2": trace[2][0].numpy(),
         "a1": atts[0][0].numpy(), "a2": atts[1][0].numpy(), "p": p, "p2": p2, "vocab": np.array(vocab),
         "loss": info["loss"], "acc": info["acc"], "examples": info["examples"], "V": info["V"]}
    np.savez(CACHE, **R)
vocab = [str(v) for v in R["vocab"]]
p = R["p"]
order = np.argsort(-p)
top = [(vocab[i], float(p[i])) for i in order[:3]]
rest = float(1 - sum(v for _, v in top))

# ------------------------------------------------------------------ validation
sents = [t for _, t in T.sentences()]
after = {}
for s in sents:
    if s[:3] == ["The", "cat", "sat"]:
        after[s[3]] = after.get(s[3], 0) + 1
tot = sum(after.values())
L = []
say = L.append
say("nf-mlc-transformer: Figure 24, a transformer on 'The cat sat'")
say("")
say("MODEL (mlc_text.tiny_transformer): token embedding (8) + sinusoidal position,")
say("  2 blocks of [2 head scaled dot-product attention -> add and norm -> feed forward")
say("  (8 -> 16 -> 8, ReLU) -> add and norm], a linear read out of the last position.")
say(f"  Trained on every prefix of the 88 sentences ({int(R['examples'])} examples, {int(R['V'])} words),")
say(f"  cross entropy, Adam 0.01, 3000 full batch steps, torch seed {SEED}.")
say(f"  final loss {float(R['loss']):.4f}; next word right {float(R['acc']):.3f} of the time (the corpus is")
say("  ambiguous: after 'The cat sat' three words follow).")
say("")
say("CHECK 1: the predicted next word against the corpus's own counts")
say(f"  corpus after 'The cat sat': {after} of {tot}")
say("  model:  " + ", ".join(f"{w} {v:.3f}" for w, v in top) + f", all other words {rest:.4f}")
say("  (cross entropy is minimised by the empirical frequencies: 0.7, 0.2, 0.1)")
p2 = R["p2"]
o2 = np.argsort(-p2)[:2]
say(f"  and after 'The dog sat' (corpus: on 1, by 1): {vocab[o2[0]]} {p2[o2[0]]:.3f}, {vocab[o2[1]]} {p2[o2[1]]:.3f}")
say("  so the model has to look back at the subject: in block 1 head 1 'sat' attends")
say(f"  to 'cat' with weight {R['a1'][0][2][1]:.3f}.")
say("")
say("CHECK 2: every attention row sums to 1")
say(f"  max |row sum - 1| = {max(np.max(np.abs(R[k].sum(-1) - 1)) for k in ('a1', 'a2')):.1e}")
say("")
say("CHECK 3: the input vectors are embedding + position")
say(f"  max |x0 - (e + pe)| = {np.max(np.abs(R['x0'] - (R['emb'] + R['pe']))):.1e}")
say("")
say("ATTENTION WEIGHTS (rows: The, cat, sat attending; columns: The, cat, sat)")
for b, k in ((1, "a1"), (2, "a2")):
    for h in range(2):
        say(f"  block {b} head {h + 1}: " + "  ".join("[" + ", ".join(f"{v:.3f}" for v in row) + "]" for row in R[k][h]))
say("")
say("VECTORS (8 numbers per token)")
for nm in ("x0", "x1", "x2"):
    for i, w in enumerate(TOKS):
        say(f"  {nm} {w:4s} " + " ".join(f"{v:+.2f}" for v in R[nm][i]))

VMAX = float(np.ceil(np.max(np.abs(np.concatenate([R["x0"], R["x1"], R["x2"]]))) * 2) / 2)
DATA = {"x": [R["x0"].tolist(), R["x1"].tolist(), R["x2"].tolist()], "a": [R["a1"].tolist(), R["a2"].tolist()],
        "top": top, "rest": rest, "vmax": VMAX}

JS = r"""
const TOK = ['The', 'cat', 'sat'], XC = [182, 332, 482], CW = 14, VW = 8 * CW;
const LY = [606, 438, 270], TY = 682;                 // vector levels: input, after block 1, after block 2; tokens
const VM = DATA.vmax, sq = v => Math.sign(v) * Math.sqrt(Math.min(1, Math.abs(v) / VM));   // signed square root: small entries stay visible
const AVG = DATA.a.map(b => [0, 1, 2].map(i => [0, 1, 2].map(j => (b[0][i][j] + b[1][i][j]) / 2)));
/* ---- the forward pass, then the attention of each token in turn, for ever */
const F0 = .6, QD = .32;                                 // one query every QD seconds while the pass runs
const tq = (b, i) => F0 + (b * 3 + i) * QD;              // token i of block b gets its new vector
const OUT0 = tq(1, 2) + QD, LOOP0 = OUT0 + 1.2, CYC = 1.25;
const POSTER_T = OUT0 + .9;
function focus() {                                      // which (block, query) the reader follows now
  if (t < F0) return null;
  if (t < OUT0) { const k = Math.min(5, Math.floor((t - F0) / QD)); return { b: (k / 3) | 0, i: k % 3, u: (t - F0) / QD - k }; }
  if (t < LOOP0) return null;
  const k = Math.floor((t - LOOP0) / CYC) % 6, u = ((t - LOOP0) / CYC) % 1;
  return { b: (k / 3) | 0, i: k % 3, u };
}
function vec(vals, cx, y, a, o = {}) {
  if (a <= 0) return;
  const x0 = cx - VW / 2;
  for (let k = 0; k < 8; k++) {
    const ck = clamp(a * 1.6 - k * .08);            // cells arrive left to right
    if (ck <= 0) continue;
    ctx.save(); ctx.globalAlpha = ck; ctx.fillStyle = signed(sq(vals[k])); ctx.fillRect(x0 + k * CW, y - CW / 2, CW, CW); ctx.restore();
  }
  for (let k = 1; k < 8; k++) line([[x0 + k * CW, y - CW / 2], [x0 + k * CW, y + CW / 2]], { color: '#fff', width: 1, alpha: a });
  box(x0, y - CW / 2, VW, CW, { width: 1, alpha: a, stroke: o.stroke || C.ink });
}
/* where the weight of line j -> i in block b is written: beside its own line (a
   fixed gap off its edge), at the first place along it that clears every other
   line of the block, the vectors and the other weights of that query; the same
   place every time the query is read. */
const WPOS = {};
function _hits(p, q, r, pad) {                  // does segment pq come within pad of rectangle r?
  const x0 = r[0] - pad, y0 = r[1] - pad, x1 = r[2] + pad, y1 = r[3] + pad, dx = q[0] - p[0], dy = q[1] - p[1];
  let t0 = 0, t1 = 1;
  for (const [pp, qq] of [[-dx, p[0] - x0], [dx, x1 - p[0]], [-dy, p[1] - y0], [dy, y1 - p[1]]]) {
    if (pp === 0) { if (qq < 0) return false; continue; }
    const s = qq / pp;
    if (pp < 0) { if (s > t1) return false; if (s > t0) t0 = s; } else { if (s < t0) return false; if (s < t1) t1 = s; }
  }
  return t1 >= t0;
}
function weightPos(b, i) {
  const key = b + ':' + i;
  if (WPOS[key]) return WPOS[key];
  const yb = LY[b] - CW / 2 - 3, yt = LY[b + 1] + CW / 2 + 3, hh = 10, GAP = 4, out = [];
  const lines = [];
  for (let q = 0; q < 3; q++) for (let k = 0; k < 3; k++) lines.push({ q, k, p: [XC[k], yb], r: [XC[q], yt], hw: (.6 + 7 * AVG[b][q][k]) / 2 });
  const boxes = [];
  for (const y of [LY[b], LY[b + 1]]) for (const x of XC) boxes.push([x - VW / 2, y - CW / 2, x + VW / 2, y + CW / 2]);
  boxes.push([18, LY[1] + 50, 170, LY[1] + 104]);                 // the line width note
  ctx.save(); ctx.font = font({ size: 14 });
  for (let j = 0; j < 3; j++) {
    const wl = ctx.measureText(nf(AVG[b][i][j], 2)).width, own = lines.find(l => l.q === i && l.k === j);
    const L = Math.hypot(own.r[0] - own.p[0], own.r[1] - own.p[1]), u = [(own.r[0] - own.p[0]) / L, (own.r[1] - own.p[1]) / L], n = [-u[1], u[0]];
    const d = own.hw + GAP + Math.abs(n[0]) * wl / 2 + Math.abs(n[1]) * hh / 2;
    let best = null;
    for (const s of [.3, .38, .22, .46, .54, .62, .15, .7, .78]) {
      for (const side of [1, -1]) {
        const cx = lerp(own.p[0], own.r[0], s) + side * n[0] * d, cy = lerp(own.p[1], own.r[1], s) + side * n[1] * d;
        const r = [cx - wl / 2, cy - hh / 2, cx + wl / 2, cy + hh / 2];
        if (lines.some(l => l !== own && _hits(l.p, l.r, r, l.hw + 3))) continue;
        if (boxes.some(bx => r[0] < bx[2] + 3 && r[2] > bx[0] - 3 && r[1] < bx[3] + 3 && r[3] > bx[1] - 3)) continue;
        best = r; break;
      }
      if (best) break;
    }
    if (!best) best = [0, 0, 0, 0];
    out.push(best); boxes.push(best);
  }
  ctx.restore();
  return (WPOS[key] = out);
}
function draw() {
  const f = focus();
  // ---- the left margin: what each level is
  const ml = (s, y, t0, o) => lab(s, 20, y, t0, { size: 15, color: C.body, ...o });
  ml('tokens', TY + 5, .1); ml('embedding', LY[0] - 3, .15); ml('+ position', LY[0] + 15, .15);
  ml('after block 1', LY[1] + 5, .2); ml('after block 2', LY[2] + 5, .25);
  // ---- tokens and their input vectors
  TOK.forEach((w, i) => {
    token(w, XC[i], TY, { progress: seg(.02 + .05 * i, .3), w: 64 });
    carrow([[XC[i], TY - 17], [XC[i], LY[0] + CW / 2 + 5]], { width: 1.3, head: 8, progress: seg(.12 + .05 * i, .25) });
    vec(DATA.x[0][i], XC[i], LY[0], seg(.18 + .05 * i, .4));
  });
  // ---- attention: lines from every token below to every token above, width by weight
  for (let b = 0; b < 2; b++) {
    const yb = LY[b] - CW / 2 - 3, yt = LY[b + 1] + CW / 2 + 3;
    for (let i = 0; i < 3; i++) {                        // query i, above
      const born = seg(tq(b, i) - QD, QD * .9);
      for (let j = 0; j < 3; j++) {                      // key j, below
        const w = AVG[b][i][j], on = f && f.b === b && f.i === i;
        const dim = f && !on && t >= LOOP0 ? .35 : 1;
        const hot = on ? 1 : 0, col = hot ? C.navy : C.blue;
        line([[XC[j], yb], [XC[i], yt]], { color: col, width: .6 + 7 * w, alpha: born * dim * (.25 + .75 * clamp(w * 3)), progress: born });
        if (on && w >= .02) {                             // the weight, written beside its line
          const s = settle(t - f.u * (t < OUT0 ? QD : CYC), .25), r = weightPos(b, i)[j];
          text(nf(w, 2), (r[0] + r[2]) / 2, r[3], { size: 14, align: 'center', color: C.navy, alpha: s });
        }
      }
      // the new vector of token i: arrives as its attention is read
      vec(DATA.x[b + 1][i], XC[i], LY[b + 1], seg(tq(b, i) - .12, .3), { stroke: f && f.b === b && f.i === i ? C.navy : C.ink });
    }
  }
  const avgA = seg(.5, .3);
  ['line width:', 'attention weight,', 'mean of 2 heads'].forEach((s_, k) => text(s_, 20, LY[1] + 64 + 17 * k, { size: 14, color: C.muted, alpha: avgA }));
  // ---- the output: the next word, read from the last token
  const oa = seg(OUT0 - .2, .35);
  carrow([[XC[2], LY[2] - CW / 2 - 3], [XC[2], 212]], { width: 1.3, head: 8, progress: oa });
  lab('read out', XC[2] + 8, 232, OUT0, { size: 14, color: C.muted });
  lab('next word after \u201cThe cat sat\u201d', 332, 58, .3, { size: 16, align: 'center' });
  const bx = 312, bw = 220;
  DATA.top.concat([['others', DATA.rest]]).forEach(([w, pv], k) => {
    const y = 84 + k * 27, g = settle(OUT0 + .05 * k, .45), acc = k === 0, wa = seg(.35 + .04 * k, .3);
    text(w, bx - 10, y + 13, { size: 16, align: 'right', color: acc && g > .5 ? C.accent : C.ink, alpha: wa });
    line([[bx, y - 2], [bx, y + 20]], { width: 1, alpha: wa, color: C.rule });
    box(bx, y, bw * pv * g, 18, { fill: acc ? C.accent : C.mist, stroke: acc ? C.accent : C.blue, width: 1, alpha: g });
    text(nf(pv, 2), bx + bw * pv * g + 8, y + 14, { size: 14, color: acc ? C.accent : C.body, alpha: g });
  });
  // ---- one block, drawn as the architecture diagrams draw it
  const BX = 650, BW = 200, bxc = BX + BW / 2, rows = [[462, 'multi-head attention', C.steel], [404, 'add & norm', '#fff'],
    [336, 'feed forward', C.steel], [278, 'add & norm', '#fff']];
  const da = seg(.08, .45);
  carrow([[bxc, 546], [bxc, 486]], { width: 1.3, head: 8, progress: da });
  rows.forEach(([y, s, fill], k) => {
    const h = fill === '#fff' ? 30 : 40;
    box(BX, y - h / 2, BW, h, { fill, width: 1.4, progress: seg(.08 + .06 * k, .35) });
    lab(s, bxc, y + 5, .25 + .06 * k, { size: 15, align: 'center' });
    if (k < 3) carrow([[bxc, y - h / 2], [bxc, rows[k + 1][0] + (rows[k + 1][2] === '#fff' ? 15 : 20)]], { width: 1.3, head: 8, progress: da });
  });
  carrow([[bxc, 263], [bxc, 244]], { width: 1.3, head: 8, progress: da });
  // residual paths round the attention and round the feed forward
  carrow([[bxc, 512], [BX + BW + 26, 512], [BX + BW + 26, 404], [BX + BW, 404]], { width: 1.2, head: 8, progress: seg(.35, .4), color: C.body });
  carrow([[bxc, 377], [BX + BW + 26, 377], [BX + BW + 26, 278], [BX + BW, 278]], { width: 1.2, head: 8, progress: seg(.4, .4), color: C.body });
  box(BX - 18, 244, BW + 62, 302, { stroke: C.guide, width: 1, dash: [5, 4], progress: seg(.3, .5) });
  mlab('\\times\\,2', BX + BW + 48, 256, .5, { size: 17 });
  lab('one transformer block', BX - 18, 234, .45, { size: 15, color: C.body });
  // ---- the two heads of block 1, as numbers
  const MX = [640, 796], MY = 592, MC = 34;
  DATA.a[0].forEach((A, h) => {
    const x0 = MX[h], ma = seg(.4 + .08 * h, .35);
    lab(`block 1, head ${h + 1}`, x0 + 1.5 * MC, MY - 14, .5 + .08 * h, { size: 14, color: C.body, align: 'center' });
    for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
      const v = A[i][j], X = x0 + j * MC, Y = MY + i * MC, on = f && f.b === 0 && f.i === i;
      box(X, Y, MC, MC, { fill: lutc(SEQ, v), stroke: C.rule, width: 1, alpha: ma });
      text(nf(v, 2), X + MC / 2, Y + MC / 2 + 5, { size: 14, align: 'center', color: lutDark(SEQ, v) ? '#fff' : C.ink, alpha: ma });
      if (on) box(x0 - 1, Y - 1, 3 * MC + 2, MC + 2, { stroke: C.navy, width: 2, alpha: ma });
    }
    box(x0, MY, 3 * MC, 3 * MC, { width: 1.2, alpha: ma });
    if (h === 0) TOK.forEach((w, i) => text(w, x0 - 6, MY + i * MC + MC / 2 + 5, { size: 14, align: 'right', alpha: ma }));
    TOK.forEach((w, j) => text(w, x0 + j * MC + MC / 2, MY + 3 * MC + 16, { size: 14, align: 'center', alpha: ma }));
  });
  { const ca = seg(.5, .4), x0 = 790, w = 150, y0 = 44;           // colour bar, on the same square root scale
    if (ca > 0) { for (let i = 0; i < w; i++) { ctx.save(); ctx.globalAlpha = ca; ctx.fillStyle = lutc(SIGNED, i / (w - 1)); ctx.fillRect(x0 + i, y0, 1.5, 9); ctx.restore(); }
      box(x0, y0, w, 9, { width: 1, alpha: ca });
      for (const v of [-VM, -1, 0, 1, VM]) { const xx = x0 + (sq(v) + 1) / 2 * w;
        line([[xx, y0 + 9], [xx, y0 + 13]], { width: 1, alpha: ca }); text(v === 0 ? '0' : nf(v, 0), xx, y0 + 28, { size: 15, align: 'center', alpha: ca }); }
      text('vector entry', x0 - 12, y0 + 9, { size: 16, align: 'right', alpha: ca }); } }
  text('2 blocks, 2 heads, 8 numbers per token; trained on 88 short sentences to predict the next word',
       20, H - 12, { size: 14, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 24: Transformer architecture and attention"
ARIA = ("The words The, cat, sat pass up through a small trained transformer: each becomes a vector of "
        "eight numbers, lines between the tokens show how strongly each token attends to every other in "
        "two stacked blocks, the vectors change block by block, and the last one gives the next word: on "
        "with probability 0.70, by 0.20, near 0.10. Beside it, the inside of one block and the attention "
        "weights of its two heads.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 740, DATA, JS, L))
