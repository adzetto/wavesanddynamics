"""Figure 26 of the machine learning guide (image23): attention in NLP, "bank"
read differently in each sentence.

Model (mlc_text.sense_head): one scaled dot-product attention head on the
word vectors of Figure 25. The query is "bank", the keys and values are every
word of the sentence ("bank" included); the attention weights blend the words'
vectors into a new vector for "bank", and a logistic read out of that vector
gives the probability of the river sense. The head was trained on the 32
corpus sentences that use "bank" (13 river, 19 money); the two sentences read
here are not among them.

(a), (b): the weights from "bank" to each word, drawn as arcs; (c): the new
vector of "bank" in each sentence on the map of Figure 25.

Run: python tools/numfig/mlc_bank.py
"""
import numpy as np

import mlc_lib as lib
import mlc_text as T

NAME = "mlc-bank"
em = T.embedding()
ix, E = em["ix"], em["E"]
params, reader, info = T.sense_head(E, em["vocab"])
reads = [reader(s) for s in T.TEST]

pos_shown = [T.project(em, E[ix[w]]).tolist() for w in T.SHOWN]
ctx_pos = [T.project(em, c).tolist() for _, _, c, _ in reads]

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-bank: Figure 26, attention reads 'bank' by its context")
say("")
say("MODEL (mlc_text.sense_head): the 4 number word vectors of Figure 25 (e_j);")
say("  a = softmax_j((W_q e_bank) . (W_k e_j) / sqrt(4)) over every word j of the sentence,")
say("  c = sum_j a_j e_j (the new vector of 'bank'), p(river sense) = sigmoid(u . c + b).")
say(f"  trained on the {info['n']} corpus sentences with 'bank' ({info['river']} river sense, {info['n'] - info['river']} money),")
say("  cross entropy + 0.001 (|W_q - I|^2 + |W_k - I|^2 + |u|^2), Adam 0.03, 1500 steps, seed 0.")
say(f"  training sentences read right: {info['acc']:.3f}" + (f" (wrong: {info['wrong']})" if info["wrong"] else ""))
say("  the two sentences below are not in the corpus.")
say("")
for (toks, a, c, p), s in zip(reads, T.TEST):
    say(f"  '{s}':")
    say("    weights  " + "  ".join(f"{w} {v:.3f}" for w, v in zip(toks, a)))
    k = int(np.argmax([v if w != "bank" else -1 for w, v in zip(toks, a)]))
    say(f"    strongest link from 'bank' to another word: '{toks[k]}' ({a[k]:.3f})")
    say(f"    p(river sense) = {p:.4f};  p(money sense) = {1 - p:.4f}")
    near = sorted(((T.cos(c, E[ix[w]]), w) for w in T.SHOWN), reverse=True)[:3]
    say("    new vector of 'bank' nearest to: " + ", ".join(f"{w} {v:.3f}" for v, w in near))
say("")
say("CHECKS")
say(f"  weights sum to 1: {max(abs(a.sum() - 1) for _, a, _, _ in reads):.1e}")
worst = [0.0, 0.0, 0.0]
for (toks, a, c, p), s in zip(reads, T.TEST):          # the head's formula, again, in plain numpy
    e = np.array([E[ix[w]] for w in toks])
    z = (e @ params["Wk"].T) @ (params["Wq"] @ e[toks.index("bank")]) / np.sqrt(4)
    a2 = np.exp(z - z.max()); a2 /= a2.sum()
    c2 = a2 @ e
    p2 = 1 / (1 + np.exp(-(params["u"] @ c2 + params["b"])))
    worst = [max(worst[0], np.max(np.abs(a2 - a))), max(worst[1], np.max(np.abs(c2 - c))), max(worst[2], abs(p2 - p))]
say(f"  softmax(W_k e . W_q e_bank / sqrt 4), sum a e, sigmoid(u . c + b) recomputed in numpy from the")
say(f"  fitted parameters: max differences {worst[0]:.1e} (weights), {worst[1]:.1e} (vector), {worst[2]:.1e} (p)")
say("  static 'bank' (no context): nearest " + ", ".join(f"{w} {c:.3f}" for c, w in sorted(((T.cos(E[ix['bank']], E[ix[w]]), w) for w in T.SHOWN if w != 'bank'), reverse=True)[:2]))
say("  the query is the same vector in both sentences; only the keys differ, so every")
say("  difference between the two readings comes from the context words.")

DATA = {"s": [{"t": s.split(), "a": a.tolist(), "p": p} for (toks, a, _, p), s in zip(reads, T.TEST)], "shown": T.SHOWN,
        "pos": pos_shown, "cpos": ctx_pos}

JS = r"""
const SN = DATA.s, SHOWN = DATA.shown;
const T0 = .5, READ = .9, GAPS = .5, TL = T0 + 2 * READ + GAPS + 1.0, PER = 3.5;
const POSTER_T = TL - .15;
const ROWY = [150, 430], SUBY = [34, 300];            // token row and subtitle of (a) and (b)
function tokenX(toks) {                                // left to right, boxes as wide as their words
  ctx.save(); ctx.font = font({ size: 17 }); const w = toks.map(s => ctx.measureText(s).width + 22); ctx.restore();
  const xs = []; let x = 40; w.forEach(v => { xs.push(x + v / 2); x += v + 12; }); return { xs, w };
}
/* how much sentence k is in front, 0 to 1: in turn, each for PER seconds, the change cross-faded over
   .35 s (before the loop both are in front) */
function bright(k) {
  if (t < TL) return 1;
  const n = Math.floor((t - TL) / PER), act = n % 2, e = easeInOut(clamp((t - TL - n * PER) / .35));
  const was = n === 0 ? 1 : act === k ? 0 : 1, now = act === k ? 1 : 0;
  return lerp(was, now, e);
}
function drawSentence(k, y0) {
  const S = SN[k], toks = S.t, { xs, w } = tokenX(toks), b = toks.indexOf('bank');       // words as he wrote them; the model reads them in lower case
  const t0 = T0 + k * (READ + GAPS / 2), dim = .4 + .6 * bright(k);
  sub('ab'[k], 18, SUBY[k], `sentence ${k + 1}`, seg(.05 + .05 * k, .3));
  toks.forEach((s, j) => token(s, xs[j], y0, { w: w[j], progress: seg(.08 + .04 * j + .06 * k, .3), fill: j === b ? C.steel : '#fff', stroke: C.ink }));
  // the strongest link to another word is the one the eye should follow
  let best = -1; S.a.forEach((v, j) => { if (j !== b && (best < 0 || v > S.a[best])) best = j; });
  const top = y0 - 18;
  toks.forEach((s, j) => {
    const v = S.a[j], pr = seg(t0 + .06 * Math.abs(j - b), .38), col = j === best ? C.accent : C.navy;
    const width = .8 + 11 * v, al = dim * (.3 + .7 * clamp(v * 2.5));
    if (j === b) {                                         // bank to itself: a loop over its own box
      const r = 12, pts = []; for (let i = 0; i <= 48; i++) { const th = Math.PI / 2 + .45 + (2 * Math.PI - .9) * i / 48; pts.push([xs[b] + r * Math.cos(th), top - r + r * Math.sin(th)]); }
      line(pts, { color: col, width, alpha: al, progress: pr });
    } else {
      const dx = xs[j] - xs[b], h = 20 + .2 * Math.abs(dx);
      line(bez([xs[b], top], [(xs[b] + xs[j]) / 2, top - 2 * h], [xs[j], top]), { color: col, width, alpha: al, progress: pr });
    }
    const na = settle(t0 + .3 + .04 * j, .28) * dim;
    text(nf(v, 2), xs[j], y0 + 39, { size: 16, align: 'center', color: j === best ? C.accent : C.ink, alpha: na });
  });
  lab('attention from “bank”', xs[toks.length - 1] + w[toks.length - 1] / 2 + 16, y0 + 39, t0 + .45, { size: 16, color: C.body, alpha: dim });
  // the reading: probability of each sense
  const ra = settle(t0 + READ - .1, .35) * dim, by = y0 + 66, bx = 150, bw = 200;
  [['river sense', S.p], ['money sense', 1 - S.p]].forEach(([lb, v], r) => {
    const yy = by + r * 24;
    text(lb, bx - 10, yy + 14, { size: 16, align: 'right', alpha: ra });
    box(bx, yy, bw * v * clamp(ra * 1.05), 16, { fill: C.mist, stroke: C.blue, width: 1, alpha: ra });
    text(nf(v, 2), bx + bw * v * clamp(ra * 1.05) + 8, yy + 14, { size: 16, color: C.body, alpha: ra });
  });
}
function draw() {
  drawSentence(0, ROWY[0]); drawSentence(1, ROWY[1]);
  // ================= (c) the new vector of bank, on the map of Figure 25
  sub('c', 612, 34, 'bank in context', seg(.15, .3));
  const g = axes({ x: 660, y: 64, w: 300, h: 300, xlim: [-1.1, 1.1], ylim: [-1.2, 1.0], xticks: [-1, 0, 1], yticks: [-1, 0, 1],
    xlabel: '\\rm{dimension\\ 1}', ylabel: '\\rm{dimension\\ 2}', ylabelGap: 34, tickSize: 16, progress: seg(.05, .4) });
  const ma = seg(.2, .4), bk = DATA.pos[SHOWN.indexOf('bank')];
  g.inside(() => {
    const OFF = { river: [-7, -5, 'right'], loan: [7, -8, 'left'], cat: [-7, -6, 'right'], dog: [7, 5, 'left'] };
    SHOWN.forEach((w, k) => { if (w === 'bank') return; const [x, y] = DATA.pos[k], his = k < 5;
      dot(g.X(x), g.Y(y), his ? 3.8 : 2.4, { color: '#fff', fill: his ? C.blue : C.guide, width: .8, alpha: ma });
      if (his) { const o = OFF[w]; text(w, g.X(x) + o[0], g.Y(y) + o[1], { size: 16, align: o[2], alpha: ma }); } });
    dot(g.X(bk[0]), g.Y(bk[1]), 4.5, { color: C.navy, fill: '#fff', width: 1.6, alpha: ma });
    // above right, in the wedge its two arrows leave free (below left sits the dot of "account")
    text('bank alone', g.X(bk[0]) + 8, g.Y(bk[1]) - 8, { size: 16, color: C.body, alpha: ma });
    DATA.cpos.forEach((c, k) => {
      const t0 = T0 + k * (READ + GAPS / 2) + READ - .2, s = settle(t0, .6), on = bright(k);
      if (s <= 0) return;
      const x = lerp(bk[0], c[0], s), y = lerp(bk[1], c[1], s), col = mix(C.guide, C.accent, on);
      carrow([[g.X(bk[0]), g.Y(bk[1])], [g.X(x), g.Y(y)]], { color: col, width: 1.6, head: 9, alpha: .5 + .5 * on });
      dot(g.X(x), g.Y(y), 5, { color: '#fff', fill: col, width: 1.2 });
      // named beside its dot, off its own arrow ((a)'s climbs from the lower right, so its name sits above);
      // the name arrives with the dot, so it never passes over "bank alone" on the way
      text(`bank in (${'ab'[k]})`, g.X(x) + (k ? 12 : 8), g.Y(y) + (k ? 21 : -10), { size: 16, align: k ? 'right' : 'left', color: mix(C.muted, C.accent, on),
        alpha: clamp((s - .55) * 2.5) });
    });
  });
  lab('dots: the words of Figure 25, on its map', 810, 450, .5, { size: 16, color: C.body, align: 'center' });
  text('one attention head, trained on 32 other “bank” sentences',
       20, H - 12, { size: 15, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 26: Attention in NLP"
ARIA = ("Two sentences, The bank is near the river and The bank approved the loan, with arcs from the word "
        "bank to every word, as thick as the attention weight a trained attention head gives it. In the "
        "first the strongest link is to river and the head reads the river sense; in the second it is to "
        "loan and the head reads the money sense. A map shows the new vector of bank moving toward the "
        "river words in one sentence and the money words in the other.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 580, DATA, JS, L))
