"""Figure 24 of the machine learning guide (image21): transformer architecture
and attention, computed on a real (tiny) transformer.

mlc_text.tiny_transformer(): two blocks (multi-head attention with 2 heads,
add and norm, feed forward, add and norm), 8 numbers per token, sinusoidal
positions, attention both ways (every token attends to every token of its
sentence), trained as BERT is on the 88 sentences of mlc_text.py to fill in a
masked word: every sentence once per word, that word replaced by [MASK]. The
figure follows "My [MASK] barks at night" through it: the tokens, their vectors
(embedding plus position), the attention weights of every token on every token
in both blocks, the vectors each block builds, and the probability of the word
under [MASK], read from the vector at its position. Every number is the
trained model's.

Run: python tools/numfig/mlc_transformer.py  (needs torch; trains once, ~2 min;
the results are cached in the temp directory)
"""
import os
import tempfile

import numpy as np

import mlc_lib as lib
import mlc_text as T

NAME = "mlc-transformer"
SEED = 0
CACHE = os.path.join(tempfile.gettempdir(), f"mlc_transformer_mlm_seed{SEED}.npz")
TOKS = ["My", T.MASK, "barks", "at", "night"]
MI = TOKS.index(T.MASK)
PROBES = {"purrs": "My [MASK] purrs at night", "split": "The [MASK] ate its food", "unseen": "The dog [MASK] on the mat"}

if os.path.isfile(CACHE):
    z = np.load(CACHE, allow_pickle=True)
    R = {k: z[k] for k in z.files}
else:
    import torch
    torch.set_num_threads(1)
    model, vocab, pe, info = T.tiny_transformer(seed=SEED)
    ix = {w: i for i, w in enumerate(vocab)}
    ix[T.MASK] = len(vocab)

    def run(toks):
        return model(torch.tensor([[ix[w] for w in toks]]), torch.tensor([len(toks)]),
                     torch.tensor([toks.index(T.MASK)]))

    with torch.no_grad():
        logits, trace, atts = run(TOKS)
        emb = model.emb.weight[[ix[w] for w in TOKS]].numpy()
        p = torch.softmax(logits[0], 0).numpy()
        probes = {k: torch.softmax(run(s.split())[0][0], 0).numpy() for k, s in PROBES.items()}
    R = {"emb": emb, "pe": pe[:len(TOKS)], "x0": trace[0][0].numpy(), "x1": trace[1][0].numpy(),
         "x2": trace[2][0].numpy(), "a1": atts[0][0].numpy(), "a2": atts[1][0].numpy(), "p": p,
         **{"p_" + k: v for k, v in probes.items()}, "vocab": np.array(vocab), "loss": info["loss"],
         "acc": info["acc"], "examples": info["examples"], "V": info["V"], "torch": torch.__version__}
    np.savez(CACHE, **R)
vocab = [str(v) for v in R["vocab"]]
p = R["p"]
order = np.argsort(-p)
top = [(vocab[i], float(p[i])) for i in order[:2]]
rest = float(1 - sum(v for _, v in top))

# ------------------------------------------------------------------ validation
grp = {}
for toks, i, w in T.masked_examples():
    grp.setdefault(tuple(toks), []).append(w)
# the least cross entropy any model can reach on these examples: each masked sentence's own word frequencies
ce_min = -np.mean([np.log(v.count(w) / len(v)) for v in grp.values() for w in v])


def counted(sentence):
    v = grp.get(tuple(sentence.split()), [])
    return ", ".join(f"{w} {v.count(w)}" for w in sorted(set(v))) or "not in it"


def best(k, n=2):
    q = R["p_" + k]
    return ", ".join(f"{vocab[i]} {q[i]:.3f}" for i in np.argsort(-q)[:n])


A1, A2 = R["a1"], R["a2"]
MEAN = [(A1[0] + A1[1]) / 2, (A2[0] + A2[1]) / 2]
L = []
say = L.append
say("nf-mlc-transformer: Figure 24, a transformer filling in 'My [MASK] barks at night'")
say("")
say("MODEL (mlc_text.tiny_transformer): token embedding (8) + sinusoidal position,")
say("  2 blocks of [2 head scaled dot-product attention -> add and norm -> feed forward")
say("  (8 -> 16 -> 8, ReLU) -> add and norm], a linear read out at the masked position.")
say("  Attention both ways: every token attends to every token of its sentence (only the")
say("  padding of shorter sentences is masked before the softmax), as in BERT.")
say("  Trained as BERT is to fill in a masked word: each of the 88 sentences once per word, that")
say(f"  word replaced by [MASK] ({int(R['examples'])} examples, {int(R['V'])} words), cross entropy, Adam 0.01,")
say(f"  6000 full batch steps, torch seed {SEED} (torch {R['torch']}).")
say(f"  final loss {float(R['loss']):.4f}, the corpus's own minimum {ce_min:.4f} (each masked sentence's own")
say(f"  word frequencies); masked word right {float(R['acc']):.3f} of the time (the corpus is ambiguous in")
say("  places: 'The [MASK] ate its food' is cat once and dog once).")
say("")
say("CHECK 1: the predicted word against the corpus's own counts")
say(f"  corpus for 'My [MASK] barks at night': {counted('My [MASK] barks at night')}")
say("  model:  " + ", ".join(f"{w} {v:.3f}" for w, v in top) + f", all other words {rest:.4f}")
say(f"  the word after the gap decides it: 'My [MASK] purrs at night' (corpus: {counted(PROBES['purrs'])})")
say(f"    gives {best('purrs')}")
say(f"  where the corpus is split, so is the model: 'The [MASK] ate its food' (corpus: {counted(PROBES['split'])})")
say(f"    gives {best('split')}")
say(f"  a sentence not in the corpus: 'The dog [MASK] on the mat' gives {best('unseen')}")
say("  [MASK] weighs the words on both sides of it: in block 2 head 1 it puts")
say(f"  {A2[0][MI][2]:.3f} on 'barks' (after it), in head 2 {A2[1][MI][0]:.3f} on 'My' (before it); the mean the")
say(f"  figure draws: My {MEAN[1][MI][0]:.2f}, barks {MEAN[1][MI][2]:.2f}.")
say("")
say("CHECK 2: every attention row sums to 1 over all five tokens, none masked")
say(f"  max |row sum - 1| = {max(np.max(np.abs(R[k].sum(-1) - 1)) for k in ('a1', 'a2')):.1e}")
say(f"  smallest weight {min(float(np.min(R[k])) for k in ('a1', 'a2')):.1e} (a masked score would give exactly 0)")
say("")
say("CHECK 3: the input vectors are embedding + position")
say(f"  max |x0 - (e + pe)| = {np.max(np.abs(R['x0'] - (R['emb'] + R['pe']))):.1e}")
say("")
say("ATTENTION WEIGHTS (rows: My, [MASK], barks, at, night attending; columns the same)")
for b, k in ((1, "a1"), (2, "a2")):
    for h in range(2):
        say(f"  block {b} head {h + 1}:")
        for w, row in zip(TOKS, R[k][h]):
            say(f"    {w:7s} " + " ".join(f"{v:.3f}" for v in row))
    say(f"  block {b}, mean of 2 heads (drawn: line widths and the table):")
    for w, row in zip(TOKS, MEAN[b - 1]):
        say(f"    {w:7s} " + " ".join(f"{v:.2f}" for v in row))
say("")
say("VECTORS (8 numbers per token)")
for nm in ("x0", "x1", "x2"):
    for i, w in enumerate(TOKS):
        say(f"  {nm} {w:7s} " + " ".join(f"{v:+.2f}" for v in R[nm][i]))

VMAX = float(np.ceil(np.max(np.abs(np.concatenate([R["x0"], R["x1"], R["x2"]]))) * 2) / 2)
DATA = {"toks": TOKS, "mi": MI, "x": [R["x0"].tolist(), R["x1"].tolist(), R["x2"].tolist()],
        "a": [R["a1"].tolist(), R["a2"].tolist()], "top": top, "rest": rest, "vmax": VMAX}

JS = r"""
const TOK = DATA.toks, MI = DATA.mi, N = TOK.length, IDX = TOK.map((_, i) => i);
const XC = IDX.map(i => 170 + 86 * i), CW = 9.5, CH = 12, VW = 8 * CW;
const LY = [572, 416, 260], TY = 646;                 // vector levels: input, after block 1, after block 2; tokens
const VM = DATA.vmax, sq = v => Math.sign(v) * Math.sqrt(Math.min(1, Math.abs(v) / VM));   // signed square root: small entries stay visible
const AVG = DATA.a.map(b => IDX.map(i => IDX.map(j => (b[0][i][j] + b[1][i][j]) / 2)));
/* attention both ways: every token attends to every token, those after it as well as those before it */
/* ---- the forward pass block by block, then the attention of each token in turn, for ever */
const F0 = .6, BD = 1;                                   // block b is computed from F0 + b BD
const OUT0 = F0 + 2 * BD + .2, LOOP0 = OUT0 + 2.5, CYC = 2.5;
const POSTER_T = OUT0 + 1;
function focus() {                                      // which (block, query) the reader follows now
  if (t < LOOP0) return null;
  const k = Math.floor((t - LOOP0) / CYC) % (2 * N);
  return { b: (k / N) | 0, i: k % N };
}
/* the block whose weights the table shows: the one being computed, then the one in focus */
const blockAt = s => s < F0 + BD ? 0 : s < LOOP0 ? 1 : ((Math.floor((s - LOOP0) / CYC) % (2 * N)) / N) | 0;
function shownBlocks() {                                // [block, alpha]: at a change the old fades out, then the new in
  const ts = t >= LOOP0 ? LOOP0 + Math.floor((t - LOOP0) / (N * CYC)) * N * CYC : t >= F0 + BD ? F0 + BD : -1;
  const e = ts < 0 ? 1 : (t - ts) / .5, b = blockAt(t);
  return e >= 1 ? [[b, 1]] : [[blockAt(ts - 1e-6), clamp(1 - 2 * e)], [b, clamp(2 * e - 1)]];
}
function vec(vals, cx, y, a, o = {}) {
  if (a <= 0) return;
  const x0 = cx - VW / 2;
  for (let k = 0; k < 8; k++) {
    const ck = clamp(a * 1.6 - k * .08);            // cells arrive left to right
    if (ck <= 0) continue;
    ctx.save(); ctx.globalAlpha = ck; ctx.fillStyle = signed(sq(vals[k])); ctx.fillRect(x0 + k * CW, y - CH / 2, CW, CH); ctx.restore();
  }
  for (let k = 1; k < 8; k++) line([[x0 + k * CW, y - CH / 2], [x0 + k * CW, y + CH / 2]], { color: '#fff', width: 1, alpha: a });
  box(x0, y - CH / 2, VW, CH, { width: 1, alpha: a, stroke: o.stroke || C.ink });
}
function draw() {
  const f = focus();
  // ---- the left margin: what each level is
  const ml = (s, y, t0) => lab(s, 20, y, t0, { size: 16, color: C.body });
  ml('tokens', TY + 5, .1); ml('embedding', LY[0] - 3, .15); ml('+ position', LY[0] + 16, .15);
  ml('after block 1', LY[1] + 5, .2); ml('after block 2', LY[2] + 5, .25);
  // ---- tokens, the hidden word shaded, and their input vectors
  TOK.forEach((w, i) => {
    token(w, XC[i], TY, { progress: seg(.02 + .05 * i, .3), w: 76, fill: i === MI ? C.steel2 : '#fff' });
    carrow([[XC[i], TY - 17], [XC[i], LY[0] + CH / 2 + 5]], { width: 1.3, head: 8, progress: seg(.12 + .05 * i, .25) });
    vec(DATA.x[0][i], XC[i], LY[0], seg(.18 + .05 * i, .4));
  });
  // ---- attention: a line from every token below to every token above, width by weight
  for (let b = 0; b < 2; b++) {
    const yb = LY[b] - CH / 2 - 3, yt = LY[b + 1] + CH / 2 + 3, born = seg(F0 + b * BD, .5);
    for (let i = 0; i < N; i++) {                        // query i, above
      const on = f && f.b === b && f.i === i, dim = f && !on ? .35 : 1;
      for (let j = 0; j < N; j++) {                      // key j, below: every token, itself included
        const w = AVG[b][i][j];
        line([[XC[j], yb], [XC[i], yt]], { color: on ? C.navy : C.blue, width: .6 + 7 * w, alpha: born * dim * (.25 + .75 * clamp(w * 3)), progress: born });
      }
      // the new vector of token i
      vec(DATA.x[b + 1][i], XC[i], LY[b + 1], seg(F0 + b * BD + .5 + .04 * i, .35), { stroke: on ? C.navy : C.ink });
    }
  }
  const avgA = seg(.5, .3);
  ['line width:', 'attention weight,', 'mean of 2 heads'].forEach((s_, k) =>
    text(s_, 20, LY[2] + 60 + 21 * k, { size: 16, color: C.body, alpha: avgA }));
  // ---- the output: the hidden word, read from the vector at its place
  const oa = seg(OUT0 - .2, .35);
  carrow([[XC[MI], LY[2] - CH / 2 - 3], [XC[MI], 168]], { width: 1.3, head: 8, progress: oa });
  lab('read out', XC[MI] + 9, 215, OUT0, { size: 16, color: C.body });
  lab('the word hidden by [MASK]', 354, 50, .3, { size: 17, align: 'center' });
  const bx = 244, bw = 220;
  DATA.top.concat([['others', DATA.rest]]).forEach(([w, pv], k) => {
    const y = 72 + k * 29, g = settle(OUT0 + .05 * k, .45), acc = k === 0, wa = seg(.35 + .04 * k, .3);
    text(w, bx - 10, y + 14, { size: 17, align: 'right', color: acc && g > .5 ? C.accent : C.ink, alpha: wa });
    line([[bx, y - 2], [bx, y + 20]], { width: 1, alpha: wa, color: C.rule });
    box(bx, y, bw * pv * g, 18, { fill: acc ? C.accent : C.mist, stroke: acc ? C.accent : C.blue, width: 1, alpha: g });
    text(nf(pv, 2), bx + bw * pv * g + 8, y + 15, { size: 16, color: acc ? C.accent : C.body, alpha: g });
  });
  // ---- one block, drawn as the architecture diagrams draw it
  const BX = 650, BW = 200, bxc = BX + BW / 2, rows = [[390, 'multi-head attention', C.steel, 34], [342, 'add & norm', '#fff', 26],
    [294, 'feed forward', C.steel, 34], [246, 'add & norm', '#fff', 26]];
  const da = seg(.08, .45);
  carrow([[bxc, 426], [bxc, 407]], { width: 1.3, head: 8, progress: da });
  rows.forEach(([y, s, fill, h], k) => {
    box(BX, y - h / 2, BW, h, { fill, width: 1.4, progress: seg(.08 + .06 * k, .35) });
    lab(s, bxc, y + 6, .25 + .06 * k, { size: 16, align: 'center' });
    if (k < 3) carrow([[bxc, y - h / 2], [bxc, rows[k + 1][0] + rows[k + 1][3] / 2]], { width: 1.3, head: 8, progress: da });
  });
  carrow([[bxc, 233], [bxc, 212]], { width: 1.3, head: 8, progress: da });
  // residual paths round the attention and round the feed forward
  carrow([[bxc, 418], [BX + BW + 26, 418], [BX + BW + 26, 342], [BX + BW, 342]], { width: 1.2, head: 8, progress: seg(.35, .4), color: C.body });
  carrow([[bxc, 320], [BX + BW + 26, 320], [BX + BW + 26, 246], [BX + BW, 246]], { width: 1.2, head: 8, progress: seg(.4, .4), color: C.body });
  box(BX - 22, 198, BW + 70, 230, { stroke: C.guide, width: 1, dash: [5, 4], progress: seg(.3, .5) });
  mlab('\\times\\,2', BX + BW + 52, 212, .5, { size: 17 });
  lab('one transformer block', BX - 22, 188, .45, { size: 16, color: C.body });
  // ---- the weights the lines draw, as numbers: the block being computed, then the one in focus
  const MX = 628, MY = 482, MW = 54, MH = 30, base = seg(F0, .4);
  for (const [b, al] of shownBlocks()) {
    const ma = base * al;
    if (ma <= 0) continue;
    text(`block ${b + 1}, mean of 2 heads`, MX + N * MW / 2, MY - 12, { size: 16, color: C.body, align: 'center', alpha: ma });
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      const v = AVG[b][i][j], X = MX + j * MW, Y = MY + i * MH;
      box(X, Y, MW, MH, { fill: lutc(SEQ, v), stroke: C.rule, width: 1, alpha: ma });
      text(nf(v, 2), X + MW / 2, Y + MH / 2 + 6, { size: 16, align: 'center', color: lutDark(SEQ, v) ? '#fff' : C.ink, alpha: ma });
    }
    if (f && f.b === b) box(MX - 1, MY + f.i * MH - 1, N * MW + 2, MH + 2, { stroke: C.navy, width: 2, alpha: ma });
  }
  box(MX, MY, N * MW, N * MH, { width: 1.2, alpha: base });
  TOK.forEach((w, i) => {
    text(w, MX - 7, MY + i * MH + MH / 2 + 6, { size: 16, align: 'right', alpha: base });
    text(w, MX + i * MW + MW / 2, MY + N * MH + 19, { size: 16, align: 'center', alpha: base });
  });
  { const ca = seg(.5, .4), x0 = 790, w = 150, y0 = 44;           // colour bar, on the same square root scale
    if (ca > 0) { for (let i = 0; i < w; i++) { ctx.save(); ctx.globalAlpha = ca; ctx.fillStyle = lutc(SIGNED, i / (w - 1)); ctx.fillRect(x0 + i, y0, 1.5, 9); ctx.restore(); }
      box(x0, y0, w, 9, { width: 1, alpha: ca });
      for (const v of [-VM, -1, 0, 1, VM]) { const xx = x0 + (sq(v) + 1) / 2 * w;
        line([[xx, y0 + 9], [xx, y0 + 13]], { width: 1, alpha: ca }); text(v === 0 ? '0' : nf(v, Number.isInteger(v) ? 0 : 1), xx, y0 + 30, { size: 16, align: 'center', alpha: ca }); }
      text('vector entry', x0 - 12, y0 + 10, { size: 16, align: 'right', alpha: ca }); } }
  text('88 training sentences, each word masked in turn; 2 blocks, 2 heads, 8 numbers per token',
       18, H - 12, { size: 15, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 24: Transformer architecture and attention"
ARIA = ("The sentence My [MASK] barks at night, with one word hidden, passes up through a small trained "
        "transformer: each token becomes a vector of eight numbers, lines between the tokens show how "
        "strongly each token attends to every other token, before it or after it, in two stacked blocks, "
        "the vectors change block by block, and the vector at the hidden word gives the word under it: dog "
        "with probability 1.00, cat 0.00. Beside it, the inside of one block and the attention weights of "
        "each block as numbers.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 700, DATA, JS, L))
