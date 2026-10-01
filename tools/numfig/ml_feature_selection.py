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
    alphas = np.geomspace(4., .003, 80)
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
    ols = np.linalg.lstsq(np.column_stack([np.ones(len(Xt)), Xt[:, :3]]), yt, rcond=None)[0]
    assert np.max(abs(ols[1:] - data["truth"][:3])) < .15
    assert np.isfinite(coefs).all()
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
             "Predictive importance is not causal importance; this is a reproducible synthetic example.",
             "Sources: https://scikit-learn.org/stable/modules/feature_selection.html"]
    return data, notes


JS = r"""
const D = DATA, POSTER_T = 8, FIG = cv.closest('.fig');
let manual = null, stepInput = null;
function reset() { manual = null; }
const subset = a => a.map(j => 'x' + (j + 1)).join(', ');
function draw() {
  const u = manual === null ? clamp((t - 1) / 5) : manual;
  const k = Math.min(3, 1 + Math.floor(u * 2.99)), step = D.steps[k - 1];
  if (manual === null && stepInput) stepInput.value = k;
  const xs = 110, ww = 500;
  panel('a', 22, 34); text('Filter: score before fitting', 58, 34, {size: 19});
  const a = axes({x: xs, y: 76, w: ww, h: 200, xlim: [0, 1], ylim: [.5, 6.5],
    xticks: [0, .25, .5, .75, 1], yticks: [1, 2, 3, 4, 5, 6], yfmt: v => 'x' + (7 - v),
    xlabel: '|r(x_j, y)|', ylabel: '\\rm{feature}', grid: true, progress: seg(0, .35)});
  for (let j = 0; j < 6; j++) {
    const yy = a.Y(6 - j), selected = D.filter.includes(j), len = D.correlation[j] * seg(.15 + j * .04, .35);
    ctx.fillStyle = selected ? C.blue : C.steel2; ctx.fillRect(a.X(0), yy - 8, len * ww, 16);
    text(D.correlation[j].toFixed(3), a.X(len) + 8, yy + 5, {size: 14, alpha: lab()});
  }
  text('Top three correlations', 682, 88, {size: 17});
  text(subset(D.filter), 682, 117, {size: 18, color: C.blue});
  text('x4 repeats much of x1', 682, 156, {size: 16, color: C.muted});
  text('x3 carries extra information', 682, 179, {size: 16, color: C.muted});
  text('Held-out RMSE: ' + D.rmse[0].toFixed(3), 682, 228, {size: 17});
  panel('b', 22, 368); text('Wrapper: fit candidate subsets', 58, 368, {size: 19});
  const b = axes({x: xs, y: 410, w: ww, h: 190, xlim: [1, 6], ylim: [.4, 3],
    xticks: [1, 2, 3, 4, 5, 6], yticks: [.5, 1, 1.5, 2, 2.5, 3],
    xlabel: '\\rm{number of features}', ylabel: '\\rm{CV RMSE}', grid: true, progress: seg(.1, .35)});
  const pp = D.steps.map((s, i) => [b.X(i + 1), b.Y(s.rmse)]);
  b.inside(() => line(pp, {color: C.navy, width: 2.4, progress: seg(.3, .45)}));
  pp.forEach((p, i) => dot(...p, 4, {color: C.navy, fill: '#fff'}));
  dot(...pp[k - 1], 7, {color: C.accent, fill: C.accent});
  text('Forward step ' + k + ' of 3', 682, 421, {size: 17});
  text(subset(step.selected), 682, 450, {size: 18, color: C.blue});
  text('Candidate     CV RMSE', 682, 489, {size: 16, color: C.muted});
  step.candidates.forEach(([j, v], i) => {
    const yy = 516 + i * 21, selected = step.selected[k - 1] === j;
    text('add x' + (j + 1), 682, yy, {size: 15, color: selected ? C.accent : C.body});
    text(v.toFixed(3), 910, yy, {size: 15, align: 'right', color: selected ? C.accent : C.body});
  });
  text('Three-feature test RMSE: ' + D.rmse[1].toFixed(3), 682, 671, {size: 16});
  panel('c', 22, 718); text('Embedded: L1 shrinks coefficients', 58, 718, {size: 19});
  const c = axes({x: xs, y: 766, w: ww, h: 200, xlim: [-3, 1], ylim: [-2.5, 3.5],
    xticks: [-3, -2, -1, 0, 1], xfmt: v => String(10 ** v), yticks: [-2, -1, 0, 1, 2, 3],
    xlabel: '\\rm{penalty}\\ \\alpha\\ \\rm{(log scale)}', ylabel: '\\rm{coefficient}', grid: true, progress: seg(.15, .35)});
  const colors = [C.navy, C.blue, C.accent, C.sky, C.guide, C.muted];
  c.inside(() => {
    line([[c.X(-3), c.Y(0)], [c.X(1), c.Y(0)]], {color: C.rule, width: 1});
    for (let j = 0; j < 6; j++) line(D.alphas.map((a, i) => [c.X(Math.log10(a)), c.Y(D.coefs[i][j])]),
      {color: colors[j], width: j < 3 ? 2.4 : 1.4, dash: j > 2 ? [4, 3] : null, progress: seg(.3 + .04 * j, .4)});
    line([[c.X(Math.log10(D.alpha)), c.Y(-2.5)], [c.X(Math.log10(D.alpha)), c.Y(3.5)]], {color: C.guide, width: 1, dash: [5, 4]});
  });
  text('Lasso, alpha = ' + D.alpha, 682, 778, {size: 17});
  D.embedded_coef.forEach((v, j) => {
    const yy = 815 + j * 22;
    line([[682, yy - 5], [704, yy - 5]], {color: colors[j], width: 2, dash: j > 2 ? [4, 3] : null});
    text('x' + (j + 1) + ': ' + D.features[j], 714, yy, {size: 15});
    text(v.toFixed(3), 972, yy, {size: 15, align: 'right'});
  });
  text('Selected: ' + subset(D.embedded), 682, 971, {size: 16, color: C.blue});
  text('Held-out RMSE: ' + D.rmse[2].toFixed(3), 682, 998, {size: 16});
  text('Synthetic sensor features, 360 train / 120 test; same Ridge predictor for all held-out comparisons', 22, 1051, {size: 14, color: C.muted});
}
function lab() { return seg(.4, .3); }
if (!STILL) {
  const ctl = document.createElement('label');
  ctl.style.cssText = 'position:absolute;left:11%;top:62.5%;font:500 14px "CMU Serif";color:#544F48;display:flex;align-items:center;gap:8px;width:50%';
  ctl.textContent = 'Forward-selection step';
  const input = document.createElement('input'); input.type = 'range'; input.min = 1; input.max = 3; input.step = 1; input.value = 3;
  stepInput = input;
  input.setAttribute('aria-label', 'Forward-selection step'); input.style.width = '35%';
  new ResizeObserver(() => { const scale = cv.getBoundingClientRect().width / W;
    ctl.style.fontSize = (14 * scale) + 'px'; input.style.height = (20 * scale) + 'px';
  }).observe(cv);
  input.addEventListener('input', () => { manual = (Number(input.value) - 1) / 2; render(); });
  ctl.addEventListener('click', e => e.stopPropagation()); ctl.appendChild(input); FIG.appendChild(ctl);
}
boot();
"""


def main():
    data, notes = compute()
    common.build_html(NAME, "Figure 6a: Three approaches to feature selection",
                      "Three numerical examples on the same synthetic regression data: correlation filtering, "
                      "forward subset selection with cross-validation, and a Lasso coefficient path.",
                      1000, 1080, data, JS)
    print(common.still(NAME))
    print(common.frames(NAME, [.6, 2, 5, 8]))
    Path(__file__).with_suffix(".check.txt").write_text("\n".join(notes) + "\nPoster and intro overlap checks passed.\n", encoding="utf-8")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
