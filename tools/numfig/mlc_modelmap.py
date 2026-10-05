"""Figure 31 of the machine learning guide (image28): the model selection map.

The experiment (mlc_modelmap_exp.py) trains five model families, from simple to
flexible, on 25 to 6400 examples of a simple pattern (a straight line) and of a
complex one, and scores each against the true pattern on fresh data. Each
panel draws the five learning curves with their standard errors; the strip
above each is the map: which model is best at each amount of data, or no
clear winner where the best two are within two standard errors.

Run: python tools/numfig/mlc_modelmap.py  (the experiment takes a few minutes
once; its results are cached in the temp directory)
"""
import numpy as np

import mlc_lib as lib
import mlc_modelmap_exp as X

NAME = "mlc-modelmap"
res = X.run()
NS, MODELS = X.NS, X.MODELS
NAMES = {"linear": "linear", "tree": "decision tree", "knn": "k-NN", "forest": "random forest", "mlp": "MLP"}


def stats(task):
    m = np.array([[np.mean(res[f"{task}|{n}|{k}"]) for n in NS] for k in MODELS])
    se = np.array([[np.std(res[f"{task}|{n}|{k}"], ddof=1) / np.sqrt(len(res[f"{task}|{n}|{k}"])) for n in NS] for k in MODELS])
    reps = [len(res[f"{task}|{n}|linear"]) for n in NS]
    return m, se, reps


def winners(m, se):
    """For every size: the models whose mean lies within two standard errors of the best."""
    out = []
    for j in range(len(NS)):
        b = int(np.argmin(m[:, j]))
        tied = [k for k in range(len(MODELS)) if m[k, j] - m[b, j] < 2 * np.hypot(se[k, j], se[b, j])]
        out.append(sorted(tied, key=lambda k: m[k, j]))
    return out


panels = {}
L = []
say = L.append
say("nf-mlc-modelmap: Figure 31, a model selection map computed from learning curves")
say("")
say("EXPERIMENT (mlc_modelmap_exp.py): 4 features uniform on [-1, 1]; noise sd 0.3;")
say("  simple pattern: y = x1 - 0.8 x2 + 0.6 x3 + 0.4 x4;  complex: the same + 1.2 x1 x2")
say("  + sin(2.5 x3) cos(1.5 x4) + 0.9 sin(4 x1 + 3 x2) + 0.8 sin(6 x3 x4) + 0.6 cos(7 x1 - 5 x4).")
say("  models (scikit-learn): ridge regression (penalty by CV), decision tree (leaf size by CV),")
say("  k nearest neighbours (k by CV), random forest (100 trees), MLP (64, 64, early stopping).")
say("  score: RMSE against the noiseless pattern on 4000 fresh points; repeats per size")
for task in ("simple", "complex"):
    m, se, reps = stats(task)
    w = winners(m, se)
    panels[task] = {"m": m.tolist(), "se": se.tolist(), "win": w}
    say("")
    say(f"{task.upper()} PATTERN (repeats per size {reps})")
    say("  n      " + "".join(f"{NAMES[k]:>15s}" for k in MODELS) + "   best (within 2 SE)")
    for j, n in enumerate(NS):
        say(f"  {n:5d}  " + "".join(f"{m[k, j]:9.3f}+-{se[k, j]:.3f}" for k in range(len(MODELS)))
            + "   " + ", ".join(NAMES[MODELS[k]] for k in w[j]))
say("")
say("CHECKS")
m, se, _ = stats("simple")
say(f"  simple pattern: the linear model is best at every size, by at least "
    f"{np.min(np.sort(m, 0)[1] - m[0]):.3f} RMSE; its error keeps falling as data grow"
    f" (25 -> 6400: {m[0, 0]:.3f} -> {m[0, -1]:.3f}): the pattern needs nothing more flexible.")
m, se, _ = stats("complex")
Xte = np.random.default_rng(0).uniform(-1, 1, (4000, X.D))
yte = X.target(Xte, True)
A = np.column_stack([np.ones(len(Xte)), Xte])
floor = float(np.sqrt(np.mean((A @ np.linalg.lstsq(A, yte, rcond=None)[0] - yte) ** 2)))
say(f"  complex pattern: the best straight line there is (least squares on the 4000 noiseless test")
say(f"  points themselves) has RMSE {floor:.3f}; the linear model levels off at {m[0, -1]:.3f}, "
    f"{m[0, -1] - floor:+.3f} from it,")
say(f"  so its error is the pattern's curvature, not a lack of data; the flexible models keep")
say(f"  improving past it.")
say(f"  at 6400 examples: linear {m[0, -1]:.3f}, MLP {m[4, -1]:.3f}.")

DATA = {"ns": NS, "models": MODELS, "names": NAMES, "p": [panels["simple"], panels["complex"]]}

JS = r"""
const NS = DATA.ns, M = DATA.models, NM = DATA.names, LN = NS.map(n => Math.log10(n));
const STY = { linear: { c: C.ink, d: null, w: 1.8, mk: 'o' }, tree: { c: C.guide, d: [6, 4], w: 1.6, mk: 's' },
  knn: { c: C.sky, d: [8, 3, 2, 3], w: 1.8, mk: 't' }, forest: { c: C.blue, d: [2.5, 3], w: 2, mk: 'S' }, mlp: { c: C.navy, d: null, w: 2.4, mk: 'O' } };
const PX = [96, 578], PW = 370, PY = 118, PHh = 290, YM = [.8, 1.6];
const T0 = .1, TS = .6, SW = 4.0, BACK = 2.8, HOLD = .9;
const CYC = SW + HOLD + BACK + HOLD;
const POSTER_T = TS + SW * .4543;              // the cursor at n = 200: linear in (a), k-NN or forest in (b)
function sweepLog() {                          // log10 n under the cursor
  if (t < TS) return null;
  const u = (t - TS) % CYC, a = LN[0], b = LN[LN.length - 1];
  if (u < SW) return lerp(a, b, easeInOut(u / SW));
  if (u < SW + HOLD) return b;
  if (u < SW + HOLD + BACK) return lerp(b, a, easeInOut((u - SW - HOLD) / BACK));
  return a;
}
function markAt(k, x, y, st, alpha) {
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = st.c; ctx.fillStyle = (st.mk === 'O' || st.mk === 'S') ? st.c : '#fff'; ctx.lineWidth = 1.3; ctx.beginPath();
  if (st.mk === 'o' || st.mk === 'O') ctx.arc(x, y, 3.6, 0, 2 * Math.PI);
  else if (st.mk === 's' || st.mk === 'S') ctx.rect(x - 3.3, y - 3.3, 6.6, 6.6);
  else { ctx.moveTo(x, y - 4.4); ctx.lineTo(x + 4, y + 3); ctx.lineTo(x - 4, y + 3); ctx.closePath(); }
  ctx.fill(); ctx.stroke(); ctx.restore();
}
function envelope(P, lx) {                     // the lowest curve at log n = lx, and which model it is
  let j = 0; while (j < LN.length - 2 && LN[j + 1] < lx) j++;
  const s = clamp((lx - LN[j]) / (LN[j + 1] - LN[j]));
  let best = 0, bv = 1e9;
  M.forEach((k, i) => { const v = lerp(P.m[i][j], P.m[i][j + 1], s); if (v < bv) { bv = v; best = i; } });
  return { v: bv, i: best, j: s < .5 ? j : j + 1 };
}
function panelDraw(p, letter, title) {
  const P = DATA.p[p], x0 = PX[p];
  sub(letter, x0 - 78, 36, title, seg(.05 + .05 * p, .3));
  const g = axes({ x: x0, y: PY, w: PW, h: PHh, xlim: [LN[0] - .08, LN[LN.length - 1] + .08], ylim: [0, YM[p]],
    xticks: [Math.log10(25), 2, Math.log10(400), Math.log10(1600), Math.log10(6400)], xfmt: v => String(Math.round(Math.pow(10, v))),
    yticks: p ? [0, .4, .8, 1.2, 1.6] : [0, .2, .4, .6, .8], yfmt: v => v === 0 ? '0' : nf(v, 1),
    xlabel: '\\rm{training\\ examples}\\ \\ n', ylabel: '\\rm{error\\ (RMSE)}', ylabelGap: 44, progress: seg(.02 + .05 * p, .4), grid: true });
  // the curves draw themselves as the data grow, one after another
  g.inside(() => M.forEach((k, i) => {
    const st = STY[k], pr = seg(.25 + .06 * i + .04 * p, .45);
    const pts = LN.map((l, j) => [g.X(l), g.Y(P.m[i][j])]);
    line(pts, { color: st.c, width: st.w, dash: st.d, progress: pr });
    pts.forEach(([X, Y], j) => { if (pr * (LN.length - 1) + .01 < j) return;
      const e = P.se[i][j]; line([[X, g.Y(P.m[i][j] - e)], [X, g.Y(P.m[i][j] + e)]], { color: st.c, width: 1, alpha: .8 });
      markAt(k, X, Y, st, 1); });
  }));
  // the map: which model is best at each size (ties where the best two are within 2 standard errors)
  const my = PY - 32, mh = 20, mids = LN.map((l, j) => j ? (LN[j - 1] + l) / 2 : LN[0] - .08).concat([LN[LN.length - 1] + .08]);
  const SHORT = { linear: 'linear', tree: 'tree', knn: 'k-NN', forest: 'forest', mlp: 'MLP' };
  const segs = []; P.win.forEach((w, j) => { const key = w.length > 2 ? 'tie' : w.map(i => M[i]).sort().join('+');
    if (segs.length && segs[segs.length - 1].key === key) segs[segs.length - 1].b = mids[j + 1]; else segs.push({ key, a: mids[j], b: mids[j + 1], w }); });
  const ma = seg(.9, .35), lx = sweepLog(), env = lx === null ? null : envelope(P, lx);
  segs.forEach(s => {
    const xa = g.X(s.a), xb = g.X(s.b), on = env && lx >= s.a && lx < s.b + 1e-9;
    box(xa, my, xb - xa, mh, { fill: s.key === 'tie' ? '#fff' : C.steel, stroke: on ? C.accent : C.rule, width: on ? 1.6 : 1, alpha: ma });
    const lbl = s.key === 'tie' ? 'no clear winner' : s.key.split('+').map(k => SHORT[k]).join(', ');
    ctx.save(); ctx.font = font({ size: 14 }); const tw = ctx.measureText(lbl).width; ctx.restore();
    if (tw < xb - xa - 6) text(lbl, (xa + xb) / 2, my + 15, { size: 14, align: 'center', color: s.key === 'tie' ? C.muted : C.ink, alpha: ma });
    else { const ks = s.w.map(i => M[i]), sp = 11, x1 = (xa + xb) / 2 - (ks.length - 1) * sp / 2;   // too narrow for words: the legend's marks
      ks.forEach((k, q) => markAt(k, x1 + q * sp, my + mh / 2, STY[k], ma)); }
  });
  const nNow = env ? Math.round(Math.pow(10, lx)) : 0;
  mlab(env ? `\\rm{best model at}\\ n = ${nNow}` : '\\rm{best model}', x0, my - 7, .95, { size: 14, color: env ? C.accent : C.muted });
  // the cursor: n grows, the best model changes; then it eases back
  if (env) {
    const X = g.X(lx), Y = g.Y(env.v), a = clamp((t - TS) / .3);
    line([[X, PY], [X, PY + PHh]], { color: C.accent, width: 1, dash: [4, 3], alpha: .7 * a });
    dot(X, Y, 5.5, { color: '#fff', fill: C.accent, width: 1.4, alpha: a });
  }
}
function draw() {
  panelDraw(0, 'a', 'a simple pattern'); panelDraw(1, 'b', 'a complex pattern');
  // legend, inside (a) where the curves leave room
  const lx = PX[0] + PW - 158, ly = PY + 8, la = seg(.8, .35);
  box(lx, ly, 150, 104, { fill: '#fff', stroke: C.ink, width: 1, alpha: la });
  M.forEach((k, i) => { const st = STY[k], y = ly + 19 + i * 19;
    line([[lx + 10, y - 4], [lx + 40, y - 4]], { color: st.c, width: st.w, dash: st.d, alpha: la });
    markAt(k, lx + 25, y - 4, st, la);
    text(NM[k], lx + 50, y + 1, { size: 14, alpha: la }); });
  text('4 features, noise sd 0.3; error against the true pattern on fresh data, mean ± standard error of 2 to 16 repeats; several marks: no clear winner',
       18, H - 14, { size: 14, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 31: Model selection map"
ARIA = ("Two panels of learning curves: the error of five models, linear, decision tree, k nearest neighbours, "
        "random forest and a neural network, as the number of training examples grows from 25 to 6400. For a "
        "simple pattern the linear model is best at every size. For a complex pattern no model is clearly best "
        "with little data, then k nearest neighbours and the random forest lead, and from a few hundred "
        "examples the neural network does. A strip above each panel marks the best model at each size.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 500, DATA, JS, L))
