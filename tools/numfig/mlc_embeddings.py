"""Figure 25 of the machine learning guide (image22): NLP embeddings, words as
vectors, with similar words close together.

Model (mlc_text.embedding): the 88 sentences of mlc_text.py are read, and every
pair of words within four positions of each other is counted (a). The counts
become positive pointwise mutual information, and gradient descent from small
random vectors factorises it into 4 numbers per word (b). The map (c) shows
the vectors on their first two principal axes, as the descent moves them:
words that share contexts end up close together.

Run: python tools/numfig/mlc_embeddings.py
"""
import numpy as np

import common
import mlc_lib as lib
import mlc_text as T

NAME = "mlc-embeddings"
em = T.embedding()
ix, X, E, traj = em["ix"], em["X"], em["E"], em["traj"]
FIVE = T.SHOWN[:5]
COLS = ["sat", "chased", "pet", "food", "water", "muddy", "steep", "boat", "interest", "money", "credit", "paid"]
GROUPS = [4, 4, 4]

# ------------------------------------------------------------------ the counting, sentence by sentence
sents = [[w.lower() for w in t] for _, t in T.sentences()]
order = np.random.default_rng(3).permutation(len(sents))
cum = np.zeros((len(sents) + 1, len(FIVE), len(COLS)), int)
for k, si in enumerate(order):
    s = sents[si]
    cum[k + 1] = cum[k]
    for i, w in enumerate(s):
        for j in range(max(0, i - 4), min(len(s), i + 5)):
            if j != i and w in FIVE and s[j] in COLS:
                cum[k + 1, FIVE.index(w), COLS.index(s[j])] += 1
assert np.array_equal(cum[-1], np.array([[X[ix[a], ix[b]] for b in COLS] for a in FIVE]))

# ------------------------------------------------------------------ the descent, as the page shows it
ITS = list(range(0, 61)) + list(range(65, 201, 5)) + [400]
pos = np.array([[T.project(em, traj[it][ix[w]]) for w in T.SHOWN] for it in ITS])     # frames x words x 2
vecs = np.array([[traj[it][ix[w]] for w in FIVE] for it in ITS])                       # frames x 5 x 4
near = {}
for w in FIVE:
    sims = sorted(((T.cos(E[ix[w]], E[ix[v]]), v) for v in T.SHOWN if v != w), reverse=True)
    near[w] = [(v, c) for c, v in sims[:2]]

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-embeddings: Figure 25, NLP embeddings")
say("")
say("MODEL (mlc_text.py): 88 sentences, 169 lower case words; counts X_ij of word j within")
say("  4 positions of word i; PPMI_ij = max(0, log(X_ij N / (X_i. X_.j))); factorised as")
say("  PPMI ~ W C^T with 4 columns by plain gradient descent (rate 0.02, 400 iterations) from")
say("  N(0, 0.01) vectors; a word's vector is (W + C)/2, rotated (orthogonal Procrustes) onto")
say("  the SVD basis. Map: the SHOWN words on their first two principal axes, which carry")
say(f"  {em['explained'][0] + em['explained'][1]:.2f} of their spread ({em['explained'][0]:.2f} + {em['explained'][1]:.2f}).")
say("")
say("CHECK 1: gradient descent reaches the best rank 4 factorisation (Eckart and Young)")
say(f"  loss after 400 iterations {em['losses'][-1]:.4f}; SVD floor 0.5 sum_(k>4) s_k^2 = {em['floor']:.4f}")
say(f"  max |vector - SVD vector| = {np.max(np.abs(traj[-1] - E)):.1e} (after rotation)")
say("")
say("CHECK 2: the counts shown in (a) are the model's counts (asserted) and the reading order")
say("  only changes when they arrive, not what they add up to.")
say("")
say("CHECK 3: similarity (cosine of the 4 number vectors)")
for w in FIVE:
    say(f"  {w:6s} nearest: " + ", ".join(f"{v} {c:.3f}" for v, c in near[w]))
say(f"  cat . dog {T.cos(E[ix['cat']], E[ix['dog']]):.3f};  bank . loan {T.cos(E[ix['bank']], E[ix['loan']]):.3f};"
    f"  bank . river {T.cos(E[ix['bank']], E[ix['river']]):.3f};  cat . bank {T.cos(E[ix['cat']], E[ix['bank']]):.3f}")
say("  'bank' lies between its two senses, nearer the money words (19 money, 13 river uses).")
say("")
say("VECTORS")
for w in T.SHOWN:
    say(f"  {w:9s} " + " ".join(f"{v:+.3f}" for v in E[ix[w]]) + "   map " + " ".join(f"{v:+.3f}" for v in T.project(em, E[ix[w]])))

DATA = {"five": FIVE, "shown": T.SHOWN, "cols": COLS, "groups": GROUPS, "cum": common.i8(cum.reshape(-1)),
        "ncum": len(sents), "its": ITS, "pos": common.f32(pos.reshape(-1)), "vec": common.f32(vecs.reshape(-1)),
        "near": near, "cmax": int(cum.max()), "cd": T.cos(E[ix["cat"]], E[ix["dog"]]),
        "bl": T.cos(E[ix["bank"]], E[ix["loan"]])}

JS = r"""
const FIVE = DATA.five, SHOWN = DATA.shown, COLS = DATA.cols, NW = SHOWN.length, NF = DATA.its.length;
const CUM = b64i8(DATA.cum), POS = b64f32(DATA.pos), VEC = b64f32(DATA.vec);
const T0 = .55, DC = 1.4, T1 = T0 + DC + .1, DG = 2.4, TL = T1 + DG + .5, PER = 2.4;
const POSTER_T = T1 + DG + .3;
// labels that would sit on a neighbour; river's on its left, off the lines to its nearest (boat, water)
const LABEL_OFF = { kitten: [-7, -6, 'right'], puppy: [7, 15], boat: [7, 15], fish: [-7, 5, 'right'], account: [-7, 5, 'right'], credit: [7, 16],
                    river: [-7, -6, 'right'] };
const XL = [-1.1, 1.1], YL = [-1.2, 1.0];                   // equal scales: distance on the map is honest
/* the descent's clock: iteration number at time t, then the frame pair around it */
function iterNow() { const u = clamp((t - T1) / DG); return u >= 1 ? 400 : 200 * (u * u * (3 - 2 * u)) * .5 + 200 * u * .5; }
function frameAt(it) { const I = DATA.its; let k = 0; while (k < NF - 2 && I[k + 1] <= it) k++; const s = clamp((it - I[k]) / (I[k + 1] - I[k])); return [k, s]; }
function posOf(w, it) { const [k, s] = frameAt(it), a = (k * NW + w) * 2, b = ((k + 1) * NW + w) * 2; return [lerp(POS[a], POS[b], s), lerp(POS[a + 1], POS[b + 1], s)]; }
function vecOf(r, it) { const [k, s] = frameAt(it); return [0, 1, 2, 3].map(c => lerp(VEC[(k * 5 + r) * 4 + c], VEC[((k + 1) * 5 + r) * 4 + c], s)); }
function focusWord() { if (t < TL) return -1; return Math.floor((t - TL) / PER) % 5; }
/* the map's words move while the descent runs. Each name shows from its own iteration on, the
   first after which it never meets another name that is showing: worked out once, from the
   trajectory and the names' ink as they are set. Where two would meet, a grey name gives way
   to one of the five, and otherwise the name of the word still moving later waits. */
const MX = v => 590 + (v - XL[0]) / (XL[1] - XL[0]) * 370, MY = v => 64 + 370 - (v - YL[0]) / (YL[1] - YL[0]) * 370;
function labelBox(k, it) {
  const w = SHOWN[k], [x, y] = posOf(k, it), off = LABEL_OFF[w] || [7, -6], X = MX(x) + off[0], Y = MY(y) + off[1];
  ctx.save(); ctx.font = font({ size: k < 5 ? 16 : 14 }); ctx.textAlign = off[2] || 'left'; const q = ctx.measureText(w); ctx.restore();
  return [X - q.actualBoundingBoxLeft, Y - q.actualBoundingBoxAscent, X + q.actualBoundingBoxRight, Y + q.actualBoundingBoxDescent];
}
let ARR = null;
function arrivals() {
  if (ARR) return ARR;
  const S = []; for (let it = 0; it <= 200; it += .25) S.push(it); S.push(400);
  const B = S.map(it => SHOWN.map((w, k) => labelBox(k, it))), fin = B[B.length - 1];
  const still = SHOWN.map((w, k) => { let s = S.length - 1;             // from here on within 3 units of its place
    while (s > 0 && Math.abs(B[s - 1][k][0] - fin[k][0]) < 3 && Math.abs(B[s - 1][k][1] - fin[k][1]) < 3) s--; return S[s]; });
  const A = SHOWN.map(() => 14);
  for (let k = 0; k < NW; k++) for (let j = k + 1; j < NW; j++) {
    let L = -1;
    S.forEach((it, s) => { const a = B[s][k], b = B[s][j];
      if (Math.min(a[2], b[2]) - Math.max(a[0], b[0]) > .5 && Math.min(a[3], b[3]) - Math.max(a[1], b[1]) > .5) L = it; });
    if (L < 14) continue;
    const v = (k < 5) !== (j < 5) ? (k < 5 ? j : k) : still[k] > still[j] ? k : j;
    A[v] = Math.max(A[v], L + .25);
  }
  return (ARR = A);
}
function draw() {
  const it = iterNow(), fw = focusWord(), fu = fw < 0 ? 0 : ((t - TL) % PER) / PER;
  const fa = fw < 0 ? 0 : clamp(fu / .12) * (1 - clamp((fu - .88) / .12));
  // ================= (a) counts
  sub('a', 18, 34, 'co-occurrence counts', seg(.05, .3));
  const AX = 100, AY = 92, CWa = 27, RHa = 24, gap = 8;
  const colX = j => AX + j * CWa + Math.floor(j / 4) * gap;
  const kread = clamp((t - T0) / DC) * DATA.ncum, kr = Math.floor(kread);
  const ga = seg(.08, .35);
  FIVE.forEach((w, i) => {
    const y = AY + i * RHa;
    if (i === fw) { ctx.save(); ctx.globalAlpha = fa; ctx.fillStyle = C.steel; ctx.fillRect(18, y, colX(11) + CWa - 18, RHa); ctx.restore(); }
    text(w, AX - 10, y + RHa / 2 + 5, { size: 15, align: 'right', alpha: seg(.1 + .04 * i, .3) });
    COLS.forEach((c, j) => {
      const n = CUM[(Math.min(kr, DATA.ncum) * 5 + i) * COLS.length + j], X = colX(j);
      box(X, y, CWa, RHa, { fill: n > 0 ? lutc(SEQ, Math.sqrt(n / DATA.cmax)) : null, stroke: C.rule, width: 1, alpha: ga });
      if (n > 0) text(String(n), X + CWa / 2, y + RHa / 2 + 5, { size: 14, align: 'center', color: lutDark(SEQ, Math.sqrt(n / DATA.cmax)) ? '#fff' : C.ink, alpha: ga });
    });
  });
  COLS.forEach((c, j) => text(c, colX(j) + CWa / 2 + 4, AY - 8, { size: 14, rot: -Math.PI / 3.2, alpha: seg(.15 + .015 * j, .3), color: C.body }));
  for (let g = 0; g < 3; g++) box(colX(4 * g), AY, 4 * CWa, 5 * RHa, { width: 1.2, alpha: ga });
  if (t < T0 + DC + .6) text(`reading sentence ${Math.max(0, Math.min(DATA.ncum, Math.ceil(kread)))} of ${DATA.ncum}`, AX, AY + 5 * RHa + 22, { size: 14, color: C.muted, alpha: seg(T0 - .1, .3) * (1 - seg(T0 + DC + .3, .3)) });
  else lab('a few of the 169 columns', AX, AY + 5 * RHa + 22, T0 + DC + .4, { size: 14, color: C.muted });
  // ================= (b) the vectors
  sub('b', 18, 334, 'word vectors, 4 numbers each', seg(.12, .3));
  const BX = 100, BY = 354, CB = 52, RB = 27, ba = seg(T1 - .15, .3);
  FIVE.forEach((w, r) => {
    const y = BY + r * (RB + 5), v = vecOf(r, it);
    if (r === fw) { ctx.save(); ctx.globalAlpha = fa; ctx.fillStyle = C.steel; ctx.fillRect(18, y - 2, BX + 4 * CB + 12 - 18, RB + 4); ctx.restore(); }
    text(w, BX - 10, y + RB / 2 + 5, { size: 15, align: 'right', alpha: seg(.15 + .04 * r, .3) });
    for (let c = 0; c < 4; c++) {
      const X = BX + c * CB, u = clamp(v[c] / 1.6, -1, 1);
      box(X, y, CB, RB, { fill: diverging(u), stroke: '#fff', width: 1, alpha: ba });
      text(nf(v[c], 2), X + CB / 2, y + RB / 2 + 5, { size: 14, align: 'center', color: Math.abs(u) > .6 ? '#fff' : C.ink, alpha: ba });
    }
    box(BX, y, 4 * CB, RB, { width: 1, alpha: ba });
  });
  if (t >= T1 - .2) text(it >= 400 ? 'after 400 steps of gradient descent' : `gradient descent, step ${Math.round(it)}`, BX, BY + 5 * (RB + 5) + 16, { size: 14, color: C.muted, alpha: ba });
  // ================= (c) the map
  sub('c', 520, 34, 'embedding space', seg(.18, .3));
  const g = axes({ x: 590, y: 64, w: 370, h: 370, xlim: XL, ylim: YL, xticks: [-1, -.5, 0, .5, 1], yticks: [-1, -.5, 0, .5, 1],
    xlabel: '\\rm{dimension\\ 1}', ylabel: '\\rm{dimension\\ 2}', ylabelGap: 36, progress: seg(.05, .4), tickSize: 14, labelSize: 16 });
  const P = SHOWN.map((w, k) => posOf(k, it)), pa = seg(T1 - .2, .3), ARV = arrivals();
  g.inside(() => {
    // the pairs the text names: cat and dog, bank and loan
    const pair = (a, b, al) => { const A = P[SHOWN.indexOf(a)], B = P[SHOWN.indexOf(b)];
      line([[g.X(A[0]), g.Y(A[1])], [g.X(B[0]), g.Y(B[1])]], { color: C.guide, width: 1, dash: [5, 4], alpha: al }); };
    const pl = seg(T1 + DG - .1, .4) * (fw < 0 ? 1 : 1 - fa);
    pair('cat', 'dog', pl); pair('bank', 'loan', pl);
    // the focused word's two nearest, measured by cosine
    if (fw >= 0) { const A = P[SHOWN.indexOf(FIVE[fw])];
      DATA.near[FIVE[fw]].forEach(([v, c]) => { const B = P[SHOWN.indexOf(v)];
        line([[g.X(A[0]), g.Y(A[1])], [g.X(B[0]), g.Y(B[1])]], { color: C.navy, width: 1.5, alpha: fa }); }); }
    SHOWN.forEach((w, k) => {
      const mine = k < 5, [x, y] = P[k], X = g.X(x), Y = g.Y(y), on = mine && k === fw;
      dot(X, Y, mine ? 4.6 : 3, { color: '#fff', fill: on ? C.accent : mine ? C.navy : C.guide, width: 1, alpha: pa });
      const off = LABEL_OFF[w] || [7, -6];
      text(w, X + off[0], Y + off[1], { align: off[2] || 'left', size: mine ? 16 : 14, color: on ? C.accent : mine ? C.ink : C.muted, alpha: pa * (mine ? 1 : .9) * clamp((it - ARV[k]) / 16) });
    });
  });
  // cosines: the pairs at rest, the focused word's nearest in the loop
  const cy0 = 524;
  if (fw < 0) { const ca = seg(T1 + DG - .05, .35);
    math(`\\rm{cos}(\\rm{cat},\\,\\rm{dog}) = ${nf(DATA.cd, 2)}`, 590, cy0, { size: 15, alpha: ca });
    math(`\\rm{cos}(\\rm{bank},\\,\\rm{loan}) = ${nf(DATA.bl, 2)}`, 748, cy0, { size: 15, alpha: ca }); }
  else { const w = FIVE[fw], nn = DATA.near[w];
    text(`nearest to ${w}:`, 590, cy0, { size: 15, color: C.body, alpha: fa });
    math(nn.map(([v, c]) => `\\rm{${v}}\\ ${nf(c, 2)}`).join(',\\ \\ '), 718, cy0, { size: 15, alpha: fa }); }
  text('88 short sentences, 169 words; counts within 4 words, positive PMI, 4 dimensions; map: vectors scaled to length 1', 20, H - 14, { size: 14, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 25: NLP embeddings"
ARIA = ("Words become vectors: counts of the words each word appears beside, then four numbers per "
        "word learned from those counts, then a map of the words on two axes in which cat sits next "
        "to dog, river among the water words, and bank among the money words near loan.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 572, DATA, JS, L))
