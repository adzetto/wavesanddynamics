"""Figure 6a: Filter, Wrapper and Embedded selection on one numerical dataset.

Run: python tools/numfig/ml_feature_selection.py. Fixed seed, train-only
selection/scaling, fold-local standardization, independent held-out RMSE.
"""
from pathlib import Path

import numpy as np
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import common

NAME = "ml-feature-selection"


def compute():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(480, 6))
    X[:, 3] = .97 * X[:, 0] + .15 * X[:, 3]
    y = X @ np.array([3., -2., 1.5, 0., 0., 0.]) + .7 * rng.normal(size=480)
    train, test = np.arange(360), np.arange(360, 480)
    Xt, yt = X[train], y[train]
    r = np.array([np.corrcoef(Xt[:, j], yt)[0, 1] for j in range(6)])
    filter_set = np.argsort(-abs(r))[:3]
    folds = KFold(n_splits=5, shuffle=True, random_state=9)
    chosen, steps = [], []
    for k in range(6):
        candidates = []
        for j in range(6):
            if j in chosen:
                continue
            subset = chosen + [j]
            scores = cross_val_score(make_pipeline(StandardScaler(), Ridge(alpha=1.)),
                                     Xt[:, subset], yt, cv=folds, scoring="neg_mean_squared_error")
            candidates.append([j, float(np.sqrt(-np.mean(scores)))])
        best = min(candidates, key=lambda v: v[1])
        chosen.append(best[0])
        steps.append(dict(selected=chosen.copy(), candidates=candidates, rmse=best[1]))
    scaler = StandardScaler().fit(Xt)
    Z = scaler.transform(Xt)
    # the penalty increasing, as the path is drawn: from almost least squares to no feature at all
    alphas = np.geomspace(.001, 10., 100)
    coefs = np.array([Lasso(alpha=a, max_iter=30000, tol=1e-10).fit(Z, yt).coef_ for a in alphas])
    alpha = .12
    embedded = Lasso(alpha=alpha, max_iter=30000, tol=1e-10).fit(Z, yt)
    embedded_set = np.flatnonzero(abs(embedded.coef_) > 1e-6)

    def evaluate(subset):
        model = make_pipeline(StandardScaler(), Ridge(alpha=1.)).fit(Xt[:, subset], yt)
        return float(np.sqrt(np.mean((model.predict(X[test][:, subset]) - y[test]) ** 2)))

    wrapper_set = steps[2]["selected"]
    data = dict(correlation=abs(r), filter=filter_set.tolist(), steps=steps,
                alphas=alphas, coefs=coefs, alpha=alpha, embedded=embedded_set.tolist(),
                embedded_coef=embedded.coef_, rmse=[evaluate(filter_set), evaluate(wrapper_set), evaluate(embedded_set)],
                features=["energy", "duration", "frequency", "energy proxy", "noise 1", "noise 2"],
                truth=[3., -2., 1.5, 0., 0., 0.], train=360, test=120)
    # Two independent references: Pearson correlation from standardized dot
    # products, and the unregularized least-squares solution on the true inputs.
    z = (Xt - Xt.mean(0)) / Xt.std(0)
    zy = (yt - yt.mean()) / yt.std()
    assert np.max(abs(r - z.T @ zy / len(zy))) < 1e-12
    assert set(wrapper_set) == {0, 1, 2}
    assert all(abs(s["rmse"] / steps[2]["rmse"] - 1) < .005 for s in steps[3:])      # flat after three
    ols = np.linalg.lstsq(np.column_stack([np.ones(len(Xt)), Xt[:, :3]]), yt, rcond=None)[0]
    assert np.max(abs(ols[1:] - data["truth"][:3])) < .15
    assert np.isfinite(coefs).all()
    # Two closed forms for the path's ends (scikit-learn's objective, 1/(2n) squared error plus
    # alpha |w|_1). While no coefficient has reached zero, the optimality condition
    # (Z'Z/n) w = Z'y/n - alpha sign(w) gives w = w_ls - alpha (Z'Z/n)^-1 sign(w_ls), w_ls least
    # squares on the same standardized inputs; and every coefficient is zero from
    # alpha_max = max_j |z_j'(y - mean y)| / n on.
    ols_z = np.linalg.lstsq(np.column_stack([np.ones(len(Z)), Z]), yt, rcond=None)[0][1:]
    near = ols_z - alphas[0] * np.linalg.solve(Z.T @ Z / len(Z), np.sign(ols_z))
    assert np.all(np.sign(near) == np.sign(ols_z))
    lasso_gap = float(np.max(abs(coefs[0] - near)))
    amax = float(np.max(abs(Z.T @ (yt - yt.mean()))) / len(yt))
    assert lasso_gap < 1e-6
    assert np.all(coefs[alphas >= amax] == 0) and np.all(np.any(coefs[alphas < .98 * amax] != 0, axis=1))
    notes = ["Figure 6a: synthetic sensor-feature regression, seed 42, 480 independent rows.",
             "y = 3 x1 - 2 x2 + 1.5 x3 + epsilon; epsilon SD 0.7.",
             "x4 = 0.97 x1 + 0.15 noise; x5 and x6 independent nuisance features.",
             "360 training rows, 120 held-out rows. Test rows never select or scale features.",
             "Filter: top 3 absolute Pearson correlations, training rows only.",
             "Wrapper: forward selection with 5-fold CV Ridge; scaler fitted within each fold.",
             "Embedded: Lasso coefficient path on training-standardized inputs; alpha 0.12 fixed in advance.",
             f"Filter {filter_set + 1}; Wrapper {np.array(wrapper_set) + 1}; Embedded {embedded_set + 1}.",
             f"Held-out RMSE with the same Ridge predictor: {data['rmse']}.",
             f"Pearson vs standardized dot-product max error {np.max(abs(r - z.T @ zy / len(zy))):.2e}.",
             f"OLS true-feature coefficients {ols[1:].tolist()}, true values [3, -2, 1.5].",
             f"Lasso path: 100 penalties from 0.001 to 10, log spaced. At 0.001 the coefficients equal the closed form "
             f"w_ls - alpha (Z'Z/n)^-1 sign(w_ls) within {lasso_gap:.1e} (least squares on the standardized inputs).",
             f"Every coefficient is exactly 0 from alpha_max = max|z_j'(y - mean)|/n = {amax:.4f} on (closed form); "
             f"below 0.98 alpha_max every penalty on the grid keeps at least one feature.",
             "Wrapper CV RMSE by step: " + ", ".join(f"{s['rmse']:.4f}" for s in steps) +
             "; after three features it is flat (within 0.5%), so three are kept.",
             "Predictive importance is not causal importance; this is a reproducible synthetic example.",
             "Page: 1000 x 640, (a), (b), (c) side by side, each with its result under it. The tour shows forward",
             "steps 1, 2, 3 (3.5 s, 2.5 s, then for good), each table going out in 0.15 s before the next comes in;",
             "the slider under (b) shows any of the six steps (?step=1..6 presets one for the checks). The Lasso",
             "paths draw from the smallest penalty to the largest, as the penalty increases.",
             "Sources: https://scikit-learn.org/stable/modules/feature_selection.html"]
    return data, notes


JS = r"""
const D = DATA, POSTER_T = 8, FIG = cv.closest('.fig');
/* the forward step on show: the tour takes steps 1, 2 and 3 (the three the wrapper keeps; 3.5,
   2.5 s, then for good), each table going out (.15 s) before the next comes in (.25 s); the
   slider (or ?step=1..6 for the checks) shows any of the six */
const NS = D.steps.length, TOUR = [0, 3.5, 6], PICK = /[?&]step=([1-6])\b/.exec(location.search);
let manual = PICK ? +PICK[1] : null, stepInput = null, lastK = 0;
function reset() { manual = PICK ? +PICK[1] : null; if (stepInput) stepInput.value = manual || 1; }
/* the family's conventions: x_j in math, a true minus, subtitles 17 in C.body,
   booktabs rules, labels that arrive on Motion's spring */
const xv = j => 'x_{' + (j + 1) + '}';
const subset = a => a.map(xv).join(',\\ ');
const plain = a => a.map(j => 'x' + (j + 1)).join(', ');
const n3 = v => (v < 0 ? '−' : '') + Math.abs(v).toFixed(3);
const arrive = t0 => settle(t0, .28);
function sub(l, x, y, words, a) { panel(l, x, y, {alpha: a}); text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }
function rule(x0, x1, y, w, a) { line([[x0, y], [x1, y]], {color: C.ink, width: w, alpha: a}); }
/* layout: the three panels side by side, each with its result under it; the step slider under
   (b), its handle under the plot's own feature counts */
const PX = [74, 400, 726], PY = 62, PW = 250, PH = 190, TY = 372, SLY = 334;
function tour() {          // the step, how much of its table shows, and the marker gliding from the last
  let k = 1; while (k < 3 && t >= TOUR[k]) k++;
  const tc = TOUR[k - 1], next = k < 3 ? TOUR[k] : 1e9;
  const a = (k === 1 ? 1 : clamp((t - tc) / .25)) * (1 - clamp((t - next + .15) / .15));
  return {k, a, from: k === 1 ? 1 : k - 1, glide: k === 1 ? 1 : settle(tc, .4)};
}
function draw() {
  const T = manual === null ? tour() : {k: manual, a: 1, from: manual, glide: 1};
  const k = T.k, step = D.steps[k - 1], ta = T.a;
  if (manual === null && stepInput) stepInput.value = k;
  if (stepInput && k !== lastK) {
    lastK = k;
    stepInput.setAttribute('aria-valuetext', 'step ' + k + ' of ' + NS + ': ' + plain(step.selected) + ', CV RMSE ' + step.rmse.toFixed(3));
  }
  /* (a) the filter: absolute correlations with the target, the three largest kept */
  const xa = PX[0];
  sub('a', xa - 56, 34, 'filter: score before fitting', arrive(0));
  const a = axes({x: xa, y: PY, w: PW, h: PH, xlim: [0, 1], ylim: [.5, 6.5],
    xticks: [0, .25, .5, .75, 1], yticks: [], xlabel: '|r(x_j, y)|', ylabel: '\\rm{feature}', ylabelGap: 40,
    grid: true, tickSize: 16, progress: seg(0, .35)});
  const ya = clamp(seg(0, .35) * 1.4);
  for (let j = 0; j < 6; j++) {
    // the feature's name as its tick label, large enough that its index reads (subscript 13 units)
    const yy = a.Y(6 - j);
    line([[xa, yy], [xa + 5, yy]], {width: 1.1, alpha: ya}); line([[xa + PW, yy], [xa + PW - 5, yy]], {width: 1.1, alpha: ya});
    math(xv(j), xa - 9, yy + 6, {size: 19, align: 'right', alpha: ya});
    const kept = D.filter.includes(j), len = D.correlation[j] * seg(.15 + j * .04, .35), x1 = xa + len * PW;
    // the three kept: navy; the others: mist with a blue edge, as the family draws a bar
    if (len > 0 && kept) { ctx.fillStyle = C.navy; ctx.fillRect(xa, yy - 8, len * PW, 16); }
    else if (len > 0) line([[xa, yy - 8], [x1, yy - 8], [x1, yy + 8], [xa, yy + 8]], {color: C.blue, width: 1, fill: C.mist, close: true});
    text(D.correlation[j].toFixed(3), a.X(len) + 7, yy + 5.5, {size: 16, alpha: seg(.4, .3)});
  }
  const aa = arrive(.3);
  text('top three correlations', xa, TY, {size: 16, color: C.body, alpha: aa});
  math(subset(D.filter), xa, TY + 28, {size: 17, alpha: aa});
  math('x_4\\ \\rm{repeats much of}\\ x_1', xa, TY + 61, {size: 16, color: C.body, alpha: aa});
  math('x_3\\ \\rm{carries extra information}', xa, TY + 85, {size: 16, color: C.body, alpha: aa});
  text('held-out RMSE ' + D.rmse[0].toFixed(3), xa, TY + 120, {size: 17, alpha: aa});

  /* (b) the wrapper: forward selection by cross-validated error */
  const xb = PX[1];
  sub('b', xb - 56, 34, 'wrapper: fit candidate subsets', arrive(.04));
  const b = axes({x: xb, y: PY, w: PW, h: PH, xlim: [1, 6], ylim: [.4, 3],
    xticks: [1, 2, 3, 4, 5, 6], yticks: [.5, 1, 1.5, 2, 2.5, 3],
    xlabel: '\\rm{number of features}', ylabel: '\\rm{CV RMSE}', ylabelGap: 44, grid: true, tickSize: 16, progress: seg(.1, .35)});
  const pp = D.steps.map((s, i) => [b.X(i + 1), b.Y(s.rmse)]);
  b.inside(() => line(pp, {color: C.navy, width: 2.4, progress: seg(.3, .45)}));
  const da = arrive(.3);     // the marks arrive with their line
  pp.forEach(p => dot(...p, 4, {color: C.navy, fill: '#fff', alpha: da}));
  const cp = [lerp(pp[T.from - 1][0], pp[k - 1][0], T.glide), lerp(pp[T.from - 1][1], pp[k - 1][1], T.glide)];
  dot(...cp, 7, {color: C.accent, fill: C.accent, alpha: da});
  // why it keeps three: the error is flat after the third feature
  text('flat after 3', b.X(4.85), b.Y(1.08), {size: 16, color: C.body, align: 'center', alpha: arrive(.5)});
  const ab = arrive(.4) * ta;
  text('forward step ' + k + ' of ' + NS, xb, TY, {size: 16, color: C.body, alpha: ab});
  math(subset(step.selected), xb, TY + 28, {size: 17, alpha: ab});
  // the candidates of this step and the CV RMSE with each added, as a booktabs table in two
  // halves; the one added in crimson
  const HX = [xb, xb + 132], HW = 118, a0 = arrive(.4);
  rule(xb, xb + PW, TY + 42, 1.3, a0);
  HX.forEach(x => { text('add', x, TY + 60, {size: 16, color: C.body, alpha: a0});
                    text('CV RMSE', x + HW, TY + 60, {size: 16, color: C.body, align: 'right', alpha: a0}); });
  rule(xb, xb + PW, TY + 68, .8, a0);
  step.candidates.forEach(([j, v], i) => {
    const x = HX[Math.floor(i / 3)], yy = TY + 89 + (i % 3) * 23, col = step.selected[k - 1] === j ? C.accent : C.body;
    math(xv(j), x, yy, {size: 17, color: col, alpha: ab});
    text(v.toFixed(3), x + HW, yy, {size: 16, align: 'right', color: col, alpha: ab});
  });
  rule(xb, xb + PW, TY + 145, 1.3, a0);
  text('three-feature test RMSE ' + D.rmse[1].toFixed(3), xb, TY + 172, {size: 17, alpha: a0});

  /* (c) the embedded method: the Lasso path, the penalty increasing left to right */
  const xc = PX[2];
  sub('c', xc - 56, 34, 'embedded: L1 shrinks coefficients', arrive(.08));
  const c = axes({x: xc, y: PY, w: PW, h: PH, xlim: [-3, 1], ylim: [-2.5, 3.5],
    xticks: [-3, -2, -1, 0, 1], xfmt: v => String(10 ** v), yticks: [-2, -1, 0, 1, 2, 3],
    xlabel: '\\rm{penalty}\\ \\alpha\\ \\rm{(log scale)}', ylabel: '\\rm{coefficient}', ylabelGap: 40, grid: true, tickSize: 16,
    progress: seg(.15, .35)});
  // the three that matter in the blues, solid; the copy and the two nuisances dashed in greys
  const colors = [C.navy, C.blue, C.sky, C.guide, C.muted, C.body], dashes = [null, null, null, [6, 3], [2, 3], [7, 3, 2, 3]];
  const ga = clamp(seg(.15, .35) * 1.4);   // the guides come with the axes
  c.inside(() => {
    line([[c.X(-3), c.Y(0)], [c.X(1), c.Y(0)]], {color: C.rule, width: 1, alpha: ga});
    for (let j = 5; j >= 0; j--) line(D.alphas.map((v, i) => [c.X(Math.log10(v)), c.Y(D.coefs[i][j])]),
      {color: colors[j], width: j < 3 ? 2.4 : 1.5, dash: dashes[j], progress: seg(.3 + .04 * j, .45)});
    line([[c.X(Math.log10(D.alpha)), c.Y(-2.5)], [c.X(Math.log10(D.alpha)), c.Y(3.5)]], {color: C.guide, width: 1, dash: [5, 4], alpha: ga});
  });
  const ac = arrive(.5);
  math('\\rm{Lasso,}\\ \\alpha\\ = ' + D.alpha, xc, TY, {size: 16, color: C.body, alpha: ac});
  // the key, as the family draws one: a thin box, white fill, serif 16
  const KT = TY + 12, KB = KT + 6 * 22 + 12;
  line([[xc, KT], [xc + PW, KT], [xc + PW, KB], [xc, KB]], {color: C.ink, width: 1, fill: '#fff', close: true, alpha: ac});
  D.embedded_coef.forEach((v, j) => {
    const yy = KT + 23 + j * 22;
    line([[xc + 8, yy - 5], [xc + 32, yy - 5]], {color: colors[j], width: j < 3 ? 2.4 : 1.5, dash: dashes[j], alpha: ac});
    math(xv(j) + '\\rm{: ' + D.features[j] + '}', xc + 40, yy, {size: 16, alpha: ac});
    text(n3(v), xc + PW - 8, yy, {size: 16, align: 'right', alpha: ac});
  });
  math('\\rm{selected}\\ ' + subset(D.embedded), xc, KB + 26, {size: 16, alpha: ac});
  text('held-out RMSE ' + D.rmse[2].toFixed(3), xc, KB + 53, {size: 17, alpha: ac});
  text('synthetic sensor features, 360 train, 120 test', 18, H - 14, {size: 15, color: C.muted, alpha: arrive(.6)});
}
if (!STILL) {
  /* the step slider in the figure's own terms: a 3 unit C.rule track and a 15 unit white handle
     with a 2 unit navy ring, as Figure 18a draws its epoch slider (larger under the pointer), and
     the focus ring every figure control has; the handle's centre runs exactly under (b)'s
     feature counts 1 to 6 */
  document.head.insertAdjacentHTML('beforeend', '<style>' +
    '.nfr{-webkit-appearance:none;appearance:none;background:transparent;margin:0;padding:0;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.nfr::-webkit-slider-runnable-track{height:var(--tk);background:#D7D2CA;border:0}' +
    '.nfr::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;box-sizing:border-box;width:var(--th);height:var(--th);' +
    'margin-top:calc(var(--tk) / 2 - var(--th) / 2);border-radius:50%;background:#fff;border:var(--bw) solid #043052}' +
    '.nfr:hover::-webkit-slider-thumb,.nfr:active::-webkit-slider-thumb{width:var(--th2);height:var(--th2);margin-top:calc(var(--tk) / 2 - var(--th2) / 2)}' +
    '.nfr::-moz-range-track{height:var(--tk);background:#D7D2CA;border:0}' +
    '.nfr::-moz-range-thumb{box-sizing:border-box;width:var(--th);height:var(--th);border-radius:50%;background:#fff;border:var(--bw) solid #043052}' +
    '.nfr:hover::-moz-range-thumb,.nfr:active::-moz-range-thumb{width:var(--th2);height:var(--th2)}' +
    '.nfr:focus{outline:none}.nfr:focus-visible{outline:2px solid #095A94;outline-offset:0}</style>');
  const TH = 15, X0 = PX[1] - TH / 2, X1 = PX[1] + PW + TH / 2;
  const lab = document.createElement('label'); lab.htmlFor = 'nfstep'; lab.textContent = 'forward-selection step';
  lab.style.cssText = 'position:absolute;right:' + (100 - (X0 - 8) / 10) + '%;top:' + (SLY - 10) / H * 100 + '%;' +
    'font:500 16px "CMU Serif";color:#544F48;white-space:nowrap;cursor:pointer';
  const input = document.createElement('input'); input.type = 'range'; input.id = 'nfstep';
  input.min = 1; input.max = NS; input.step = 1; input.value = manual || 1;
  input.className = 'nfr'; stepInput = input;
  input.setAttribute('aria-label', 'Forward-selection step');
  input.style.cssText = 'position:absolute;left:' + X0 / 10 + '%;width:' + (X1 - X0) / 10 + '%;top:' + (SLY - 18) / H * 100 + '%';
  new ResizeObserver(() => {
    const s = cv.getBoundingClientRect().width / W, px = v => v * s + 'px';
    lab.style.fontSize = px(16); lab.style.lineHeight = px(20); input.style.height = px(36);
    input.style.setProperty('--th', px(TH)); input.style.setProperty('--th2', px(17));
    input.style.setProperty('--tk', Math.max(1, 3 * s) + 'px'); input.style.setProperty('--bw', Math.max(1, 2 * s) + 'px');
  }).observe(cv);
  // any touch of the slider takes over, even at the step the tour is showing
  const take = () => { manual = Number(input.value); render(); };
  input.addEventListener('input', take);
  input.addEventListener('change', take);
  input.addEventListener('pointerdown', take);
  input.addEventListener('keydown', take);
  for (const el of [lab, input]) el.addEventListener('click', e => e.stopPropagation());
  FIG.insertBefore(lab, FIG.querySelector('.ctl')); FIG.insertBefore(input, FIG.querySelector('.ctl'));
  // a click just beside the slider (12 units or 8 CSS px) is meant for it: it never pauses
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), u = W / r.width, X = (e.clientX - r.left) * u, Y = (e.clientY - r.top) * u, m = Math.max(12, 8 * u);
    if (Math.abs(Y - SLY) < 18 + m && X > PX[1] - 175 && X < X1 + m) e.stopPropagation();
  }, true);
}
boot();
"""


def main():
    data, notes = compute()
    common.build_html(NAME, "Figure 6a: Three approaches to feature selection",
                      "Three numerical examples on the same synthetic regression data: correlation filtering, "
                      "forward subset selection with cross-validation, and a Lasso coefficient path.",
                      1000, 640, data, JS)
    print(common.still(NAME))
    print(common.frames(NAME, [.3, .7, 1.4, 3.6, 6.2, 8]))
    Path(__file__).with_suffix(".check.txt").write_text("\n".join(notes) + "\nPoster and intro overlap checks passed.\n", encoding="utf-8")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
