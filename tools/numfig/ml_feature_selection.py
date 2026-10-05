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
let manual = null, stepInput = null, lastK = 0;
function reset() { manual = null; }
/* the family's conventions: x_j in math, a true minus, subtitles 17 in C.body,
   booktabs rules, labels that arrive on Motion's spring */
const xv = j => 'x_{' + (j + 1) + '}';
const subset = a => a.map(xv).join(',\\ ');
const plain = a => a.map(j => 'x' + (j + 1)).join(', ');
const n3 = v => (v < 0 ? '−' : '') + Math.abs(v).toFixed(3);
const arrive = t0 => settle(t0, .28);
function sub(l, x, y, words, a) { panel(l, x, y, {alpha: a}); text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }
function rule(x0, x1, y, w, a) { line([[x0, y], [x1, y]], {color: C.ink, width: w, alpha: a}); }
/* the right column; the step slider sits under (b), between its axis label and (c) */
const RX = 682, TX = 910, SLY = 680;
function draw() {
  const u = manual === null ? clamp((t - 1) / 5) : manual;
  const k = Math.min(3, 1 + Math.floor(u * 2.99)), step = D.steps[k - 1];
  if (manual === null && stepInput) stepInput.value = k;
  if (stepInput && k !== lastK) {
    lastK = k;
    stepInput.setAttribute('aria-valuetext', 'step ' + k + ' of 3: ' + plain(step.selected) + ', CV RMSE ' + step.rmse.toFixed(3));
  }
  const xs = 110, ww = 500;
  sub('a', 18, 34, 'filter: score before fitting', arrive(0));
  const a = axes({x: xs, y: 76, w: ww, h: 200, xlim: [0, 1], ylim: [.5, 6.5],
    xticks: [0, .25, .5, .75, 1], yticks: [1, 2, 3, 4, 5, 6], yfmt: v => 'x_{' + (7 - v) + '}',
    xlabel: '|r(x_j, y)|', ylabel: '\\rm{feature}', grid: true, progress: seg(0, .35)});
  for (let j = 0; j < 6; j++) {
    const yy = a.Y(6 - j), kept = D.filter.includes(j), len = D.correlation[j] * seg(.15 + j * .04, .35), x1 = a.X(0) + len * ww;
    // the three kept: navy; the others: mist with a blue edge, as the family draws a bar
    if (len > 0 && kept) { ctx.fillStyle = C.navy; ctx.fillRect(a.X(0), yy - 8, len * ww, 16); }
    else if (len > 0) line([[a.X(0), yy - 8], [x1, yy - 8], [x1, yy + 8], [a.X(0), yy + 8]], {color: C.blue, width: 1, fill: C.mist, close: true});
    text(D.correlation[j].toFixed(3), a.X(len) + 8, yy + 5, {size: 14, alpha: lab()});
  }
  const aa = arrive(.3);
  text('top three correlations', RX, 88, {size: 16, color: C.body, alpha: aa});
  math(subset(D.filter), RX, 117, {size: 17, alpha: aa});
  math('x_4\\ \\rm{repeats much of}\\ x_1', RX, 156, {size: 15, color: C.muted, alpha: aa});
  math('x_3\\ \\rm{carries extra information}', RX, 179, {size: 15, color: C.muted, alpha: aa});
  text('held-out RMSE ' + D.rmse[0].toFixed(3), RX, 228, {size: 16, alpha: aa});
  sub('b', 18, 368, 'wrapper: fit candidate subsets', arrive(.04));
  const b = axes({x: xs, y: 410, w: ww, h: 190, xlim: [1, 6], ylim: [.4, 3],
    xticks: [1, 2, 3, 4, 5, 6], yticks: [.5, 1, 1.5, 2, 2.5, 3],
    xlabel: '\\rm{number of features}', ylabel: '\\rm{CV RMSE}', grid: true, progress: seg(.1, .35)});
  const pp = D.steps.map((s, i) => [b.X(i + 1), b.Y(s.rmse)]);
  b.inside(() => line(pp, {color: C.navy, width: 2.4, progress: seg(.3, .45)}));
  const da = arrive(.3);     // the marks arrive with their line
  pp.forEach((p, i) => dot(...p, 4, {color: C.navy, fill: '#fff', alpha: da}));
  dot(...pp[k - 1], 7, {color: C.accent, fill: C.accent, alpha: da});
  const ab = arrive(.4);
  text('forward step ' + k + ' of 3', RX, 421, {size: 16, color: C.body, alpha: ab});
  math(subset(step.selected), RX, 450, {size: 17, alpha: ab});
  // the candidates of this step, as a booktabs table; the one added in crimson
  rule(RX, TX, 470, 1.3, ab);
  text('candidate', RX, 488, {size: 15, color: C.body, alpha: ab});
  text('CV RMSE', TX, 488, {size: 15, color: C.body, align: 'right', alpha: ab});
  rule(RX, TX, 496, .8, ab);
  step.candidates.forEach(([j, v], i) => {
    const yy = 515 + i * 21, col = step.selected[k - 1] === j ? C.accent : C.body;
    math('\\rm{add}\\ ' + xv(j), RX, yy, {size: 15, color: col, alpha: ab});
    text(v.toFixed(3), TX, yy, {size: 15, align: 'right', color: col, alpha: ab});
  });
  const foot = 515 + (step.candidates.length - 1) * 21 + 10;
  rule(RX, TX, foot, 1.3, ab);
  text('three-feature test RMSE ' + D.rmse[1].toFixed(3), RX, foot + 28, {size: 16, alpha: ab});
  sub('c', 18, 724, 'embedded: L1 shrinks coefficients', arrive(.08));
  const c = axes({x: xs, y: 766, w: ww, h: 200, xlim: [-3, 1], ylim: [-2.5, 3.5],
    xticks: [-3, -2, -1, 0, 1], xfmt: v => String(10 ** v), yticks: [-2, -1, 0, 1, 2, 3],
    xlabel: '\\rm{penalty}\\ \\alpha\\ \\rm{(log scale)}', ylabel: '\\rm{coefficient}', grid: true, progress: seg(.15, .35)});
  const colors = [C.navy, C.blue, C.accent, C.sky, C.guide, C.muted];
  const ga = clamp(seg(.15, .35) * 1.4);   // the guides come with the axes
  c.inside(() => {
    line([[c.X(-3), c.Y(0)], [c.X(1), c.Y(0)]], {color: C.rule, width: 1, alpha: ga});
    for (let j = 0; j < 6; j++) line(D.alphas.map((a, i) => [c.X(Math.log10(a)), c.Y(D.coefs[i][j])]),
      {color: colors[j], width: j < 3 ? 2.4 : 1.4, dash: j > 2 ? [4, 3] : null, progress: seg(.3 + .04 * j, .4)});
    line([[c.X(Math.log10(D.alpha)), c.Y(-2.5)], [c.X(Math.log10(D.alpha)), c.Y(3.5)]], {color: C.guide, width: 1, dash: [5, 4], alpha: ga});
  });
  const ac = arrive(.5);
  math('\\rm{Lasso,}\\ \\alpha\\ = ' + D.alpha, RX, 778, {size: 16, color: C.body, alpha: ac});
  // the key, as the family draws one: a thin box, white fill, serif 15
  line([[RX - 6, 792], [TX + 6, 792], [TX + 6, 934], [RX - 6, 934]], {color: C.ink, width: 1, fill: '#fff', close: true, alpha: ac});
  D.embedded_coef.forEach((v, j) => {
    const yy = 813 + j * 22;
    line([[RX + 4, yy - 5], [RX + 28, yy - 5]], {color: colors[j], width: 2, dash: j > 2 ? [4, 3] : null, alpha: ac});
    math(xv(j) + '\\rm{: ' + D.features[j] + '}', RX + 38, yy, {size: 15, alpha: ac});
    text(n3(v), TX, yy, {size: 15, align: 'right', alpha: ac});
  });
  math('\\rm{selected}\\ ' + subset(D.embedded), RX, 966, {size: 16, alpha: ac});
  text('held-out RMSE ' + D.rmse[2].toFixed(3), RX, 994, {size: 16, alpha: ac});
  text('synthetic sensor features, 360 train, 120 test; same Ridge predictor for all held-out comparisons', 18, H - 14, {size: 14, color: C.muted, alpha: arrive(.6)});
}
function lab() { return seg(.4, .3); }
if (!STILL) {
  /* the step slider in the figure's own terms: a 3 unit C.rule track and a 15 unit white
     handle with a 2 unit navy ring, as Figure 18a draws its epoch slider (larger under the
     pointer), and the focus ring every figure control has */
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
  const ctl = document.createElement('label');
  ctl.style.cssText = 'position:absolute;left:11%;top:' + (SLY - 18) / H * 100 + '%;font:500 15px "CMU Serif";color:#544F48;' +
    'display:flex;align-items:center;gap:14px;width:50%;white-space:nowrap';
  ctl.textContent = 'forward-selection step';
  const input = document.createElement('input'); input.type = 'range'; input.min = 1; input.max = 3; input.step = 1; input.value = 3;
  input.className = 'nfr'; stepInput = input;
  input.setAttribute('aria-label', 'Forward-selection step'); input.style.width = '35%';
  new ResizeObserver(() => {
    const s = cv.getBoundingClientRect().width / W, px = v => v * s + 'px';
    ctl.style.fontSize = px(15); ctl.style.gap = px(14); input.style.height = px(36);
    input.style.setProperty('--th', px(15)); input.style.setProperty('--th2', px(17));
    input.style.setProperty('--tk', Math.max(1, 3 * s) + 'px'); input.style.setProperty('--bw', Math.max(1, 2 * s) + 'px');
  }).observe(cv);
  input.addEventListener('input', () => { manual = (Number(input.value) - 1) / 2; render(); });
  ctl.addEventListener('click', e => e.stopPropagation()); ctl.appendChild(input);
  FIG.insertBefore(ctl, FIG.querySelector('.ctl'));
  // a click just beside the slider (12 units or 8 CSS px) is meant for it: it never pauses
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), u = W / r.width, X = (e.clientX - r.left) * u, Y = (e.clientY - r.top) * u, m = Math.max(12, 8 * u);
    if (Math.abs(Y - SLY) < 18 + m && X > 110 - m && X < 610 + m) e.stopPropagation();
  }, true);
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
