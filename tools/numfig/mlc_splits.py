"""Figure 32 of the machine learning guide (image29): splitting labeled data
into training, validation and test sets, and 5-fold cross-validation.

Data: 100 labeled examples, one feature x and a number y to predict
(y = 2 sin(0.8 x) + 0.15 x + noise of standard deviation 0.45), seed 11.
Model: a degree 5 polynomial fitted by least squares; score: root mean square
error (RMSE) on the examples it did not learn from.

(a) One random split, 60 / 20 / 20: the model learns from the 60, is scored
    on the 20 validation examples; the 20 test examples wait.
(b) 5-fold cross-validation on the 80 training and validation examples: five
    rounds, each holding out a different fifth; the five scores are averaged.
    The test set is scored once, at the very end, by the model refitted on all 80.

Run: python tools/numfig/mlc_splits.py
"""
import numpy as np

import mlc_lib as lib

NAME = "mlc-splits"
N, DEG = 100, 5
rng = np.random.default_rng(11)
x = np.sort(rng.uniform(0, 10, N))                     # the order the examples were collected in
f = lambda v: 2 * np.sin(0.8 * v) + 0.15 * v
y = f(x) + rng.normal(0, 0.45, N)
perm = rng.permutation(N)
TR, VA, TE = perm[:60], perm[60:80], perm[80:]
role = np.zeros(N, int)
role[VA], role[TE] = 1, 2


def fit(idx):
    return np.polyfit(x[idx] / 10, y[idx], DEG)


def rmse(c, idx):
    return float(np.sqrt(np.mean((np.polyval(c, x[idx] / 10) - y[idx]) ** 2)))


c1 = fit(TR)
single = {"train": rmse(c1, TR), "val": rmse(c1, VA)}
TV = perm[:80]
folds = [TV[16 * k:16 * k + 16] for k in range(5)]
cv = []
for k in range(5):
    tr = np.concatenate([folds[j] for j in range(5) if j != k])
    ck = fit(tr)
    cv.append({"val": rmse(ck, folds[k]), "train": rmse(ck, tr)})
cvs = np.array([r["val"] for r in cv])
cfin = fit(TV)
test = rmse(cfin, TE)
xs = np.linspace(0, 10, 161)

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-splits: Figure 32, training, validation and test sets; 5-fold cross-validation")
say("")
say(f"DATA: {N} examples, x uniform on [0, 10], y = 2 sin(0.8 x) + 0.15 x + N(0, 0.45^2), seed 11.")
say(f"MODEL: polynomial of degree {DEG} in x/10, least squares (numpy.polyfit). SCORE: RMSE.")
say("")
say("(a) ONE RANDOM SPLIT (a permutation of the 100, seed 11): 60 training, 20 validation, 20 test")
say(f"  training RMSE {single['train']:.4f}, validation RMSE {single['val']:.4f}")
say("")
say("(b) 5-FOLD CROSS-VALIDATION over the 80 training and validation examples, folds of 16")
for k, r in enumerate(cv):
    say(f"  round {k + 1}: trained on 64, validation RMSE {r['val']:.4f} (training {r['train']:.4f})")
say(f"  mean {cvs.mean():.4f}, standard deviation {cvs.std(ddof=1):.4f}; spread of the rounds "
    f"{cvs.min():.3f} to {cvs.max():.3f}")
say(f"  every one of the 80 examples is held out exactly once: {sorted(np.concatenate(folds).tolist()) == sorted(TV.tolist())}")
say("")
say(f"TEST, ONCE, AT THE END: refit on all 80, test RMSE {test:.4f}")
say("")
floor_v, floor_t = (float(np.sqrt(np.mean((f(x[i]) - y[i]) ** 2))) for i in (VA, TE))
say(f"CHECK: the true curve itself scores {floor_v:.4f} on the validation 20 and {floor_t:.4f} on the test")
say(f"  20 (the noise those examples happen to carry); the model's {single['val']:.4f} and {test:.4f} sit")
say(f"  {single['val'] - floor_v:+.4f} and {test - floor_t:+.4f} from these floors.")
say("CHECK: an exact model would score the noise standard deviation, 0.45, on average;")
say(f"  the rounds scatter round it (mean {cvs.mean():.3f}), so the model fits the pattern, not the noise.")
say("  With only 16 examples a fold, one round alone could read anywhere from "
    f"{cvs.min():.2f} to {cvs.max():.2f}: the average is the reliable number.")

DATA = {"x": x.tolist(), "y": y.tolist(), "role": role.tolist(), "perm": perm.tolist(), "c1": c1.tolist(),
        "xs": xs.tolist(), "fit": np.polyval(c1, xs / 10).tolist(), "single": single, "cv": cvs.tolist(),
        "folds": [fo.tolist() for fo in folds], "test": test, "mean": float(cvs.mean()), "sd": float(cvs.std(ddof=1))}

JS = r"""
const N = 100, PERM = DATA.perm, ROLE = DATA.role;
const SX = 118, CWs = 5.2, GAP = 12, SY = 70, SH = 26;
const slot = r => SX + r * CWs + (r >= 60 ? GAP : 0) + (r >= 80 ? GAP : 0);    // position in the split strip
const RANK = new Array(N); PERM.forEach((e, r) => RANK[e] = r);
const FILL = [C.mist, C.accent, C.navy], STROKE = [C.blue, C.accent, C.navy];
const T_SH = .55, D_SH = 1.0, T_CV = 1.55, DR = .38, T_LOOP = T_CV + 5 * DR + .9, PER = 1.3;
const POSTER_T = T_LOOP - .2;
function focus() { if (t < T_LOOP) return -1; return Math.floor((t - T_LOOP) / PER) % 5; }
function draw() {
  const fr = focus();
  // ================= (a) one split
  sub('a', 18, 36, 'training, validation and test sets', seg(.05, .3));
  const sw = seg(T_SH + .1, .35);
  text('all 100 labeled examples', SX, SY - 10, { size: 14, color: C.muted, alpha: seg(.1, .3) * clamp(1 - 2 * sw) });   // gone before
  text('shuffled at random, then split', SX, SY - 10, { size: 14, color: C.muted, alpha: clamp(2 * sw - 1) });       // the next shows
  for (let e = 0; e < N; e++) {
    const x0 = SX + e * CWs, x1 = slot(RANK[e]);
    const s = settle(T_SH + .006 * RANK[e], .5), x = lerp(x0, x1, s);
    const c = mix(C.steel2, FILL[ROLE[e]], clamp(s * 1.5));
    ctx.save(); ctx.globalAlpha = seg(.03 + e * .003, .2); ctx.fillStyle = c; ctx.fillRect(x + .5, SY, CWs - 1, SH); ctx.restore();
  }
  const la = seg(T_SH + .7, .3);
  [['training 60%', 0, 60], ['validation 20%', 60, 80], ['test 20%', 80, 100]].forEach(([s, a, b], k) => {
    const xa = slot(a), xb = slot(b - 1) + CWs, cx = (xa + xb) / 2;
    line([[xa, SY + SH + 8], [xa, SY + SH + 13], [xb, SY + SH + 13], [xb, SY + SH + 8]], { width: 1, alpha: la });
    text(s, cx, SY + SH + 32, { size: 15, align: 'center', color: k === 1 ? C.accent : C.ink, alpha: la });
  });
  lab('learns', slot(30), SY + SH + 52, T_SH + .85, { size: 14, color: C.muted, align: 'center' });
  lab('tunes', (slot(60) + slot(79) + CWs) / 2, SY + SH + 52, T_SH + .9, { size: 14, color: C.muted, align: 'center' });
  lab('used once, last', (slot(80) + slot(99) + CWs) / 2, SY + SH + 52, T_SH + .95, { size: 14, color: C.muted, align: 'center' });
  // the data, by role, and the model fitted on the training 60
  const g = axes({ x: 760, y: 58, w: 212, h: 150, xlim: [0, 10], ylim: [-3, 4], xticks: [0, 5, 10], yticks: [-2, 0, 2, 4],
    xlabel: 'x', ylabel: 'y', ylabelGap: 30, progress: seg(.1, .4) });
  const pa = seg(T_SH + .5, .4);
  g.inside(() => {
    line(DATA.xs.map((v, i) => [g.X(v), g.Y(DATA.fit[i])]), { color: C.navy, width: 2, progress: seg(T_SH + .7, .45) });
    DATA.x.forEach((v, i) => { const X = g.X(v), Y = g.Y(DATA.y[i]), r = ROLE[i];
      if (r === 2) box(X - 2.8, Y - 2.8, 5.6, 5.6, { stroke: C.navy, width: 1.2, alpha: pa });
      else dot(X, Y, r === 1 ? 3.4 : 2.6, { color: r === 1 ? '#fff' : C.blue, fill: r === 1 ? C.accent : '#fff', width: r === 1 ? .8 : 1.1, alpha: pa }); });
  });
  mlab(`\\rm{validation\\ RMSE}\\ ${nf(DATA.single.val, 2)}`, 760, 284, T_SH + 1.0, { size: 15 });
  // ================= (b) five rounds
  sub('b', 18, 318, '5-fold cross-validation on the 80%', seg(.1, .3));
  const RY = 350, RH = 24, RG = 10, TVX = SX;
  for (let k = 0; k < 5; k++) {
    const y = RY + k * (RH + RG), ra = seg(T_CV + DR * k - .25, .3), on = fr < 0 || fr === k;
    lab(`round ${k + 1}`, 18, y + RH / 2 + 5, T_CV + DR * k - .2, { size: 15, alpha: on ? 1 : .45 });
    for (let j = 0; j < 80; j++) {
      const fold = Math.floor(j / 16), isVal = fold === k, x = TVX + j * CWs + fold * 3;
      const flip = settle(T_CV + DR * k, .3);
      ctx.save(); ctx.globalAlpha = ra * (on ? 1 : .4);
      ctx.fillStyle = isVal ? mix('#A9C3DA', C.accent, flip) : C.mist; ctx.fillRect(x + .5, y, CWs - 1, RH); ctx.restore();
    }
    const tx = TVX + 80 * CWs + 4 * 3 + GAP;
    ctx.save(); ctx.globalAlpha = ra; ctx.fillStyle = C.steel2; ctx.fillRect(tx, y, 20 * CWs, RH); ctx.restore();
    // this round's score, as it arrives
    const s = settle(T_CV + DR * k + .15, .3);
    if (s > 0) text(nf(DATA.cv[k], 2), tx + 20 * CWs + 16, y + RH / 2 + 5, { size: 15, color: on && fr === k ? C.accent : C.ink, alpha: s * (on ? 1 : .45) });
  }
  const tx = TVX + 80 * CWs + 4 * 3 + GAP;
  lab('test, untouched', tx + 10 * CWs, RY - 8, T_CV, { size: 14, color: C.muted, align: 'center' });
  lab('RMSE', tx + 20 * CWs + 16, RY - 8, T_CV, { size: 14, color: C.muted });
  // the five scores on one axis, their mean, and the test score at the end
  const h = axes({ x: 760, y: RY, w: 212, h: 5 * RH + 4 * RG, xlim: [.5, 5.5], ylim: [.2, .8], xticks: [1, 2, 3, 4, 5], yticks: [.2, .4, .6, .8],
    xlabel: '\\rm{round}', ylabel: '\\rm{RMSE}', ylabelGap: 35, progress: seg(T_CV - .3, .4), yfmt: v => nf(v, 1) });
  const ma = seg(T_CV + 5 * DR, .4);
  h.inside(() => {
    if (ma > 0) { ctx.save(); ctx.globalAlpha = .5 * ma; ctx.fillStyle = C.steel; const y0 = h.Y(DATA.mean + DATA.sd), y1 = h.Y(DATA.mean - DATA.sd);
      ctx.fillRect(h.X(.5), y0, h.X(5.5) - h.X(.5), y1 - y0); ctx.restore();
      line([[h.X(.5), h.Y(DATA.mean)], [h.X(5.5), h.Y(DATA.mean)]], { color: C.navy, width: 1.4, dash: [5, 4], progress: ma }); }
    DATA.cv.forEach((v, k) => { const s = settle(T_CV + DR * k + .15, .3); if (s <= 0) return;
      dot(h.X(k + 1), h.Y(v), 4.5, { color: '#fff', fill: fr === k ? C.accent : C.navy, width: 1.2, alpha: s }); });
  });
  mlab(`\\rm{mean\\ of\\ the\\ 5\\ rounds}\\ \\ ${nf(DATA.mean, 2)}\\,\\pm\\,${nf(DATA.sd, 2)}`, SX, RY + 5 * RH + 4 * RG + 26, T_CV + 5 * DR + .1, { size: 15 });
  mlab(`\\rm{test\\ set,\\ scored\\ once\\ at\\ the\\ end}\\ \\ ${nf(DATA.test, 2)}`, SX + 300, RY + 5 * RH + 4 * RG + 26, T_CV + 5 * DR + .3, { size: 15, color: C.navy });
  text('100 examples, y = 2 sin(0.8 x) + 0.15 x + noise (sd 0.45); model: degree 5 polynomial; score: root mean square error',
       18, H - 14, { size: 14, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 32: Splitting labeled data into training, validation, and test sets (top)"
ARIA = ("Top: one hundred labeled examples are shuffled into sixty for training, twenty for validation "
        "and twenty for test, shown as a strip and as the data with the model fitted on the training "
        "sixty. Bottom: five rounds of cross-validation on the eighty training and validation examples, "
        "each holding out a different fifth, with the five validation scores and their mean; the test "
        "set stays untouched until one final score.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 612, DATA, JS, L))
