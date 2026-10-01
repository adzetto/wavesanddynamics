"""Figure 3a: seasonal ARIMA, exponential smoothing and lagged boosted trees.

Same synthetic monthly sensor signal, three origins, 24-step fixed-origin
forecasts. Each model is fitted only to observations before that origin.
The tree forecasts recursively use their own outputs, never test labels.
"""
from pathlib import Path
import warnings

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

import common

NAME = "ml-forecasting"
HORIZON = 24


def lag_features(history, at):
    return [history[at - j] for j in (1, 2, 3, 12, 13, 24)] + [at, np.sin(2 * np.pi * at / 12), np.cos(2 * np.pi * at / 12)]


def fit_origin(series, origin):
    train = np.asarray(series[:origin]).copy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        ar = ARIMA(train, order=(1, 1, 1), seasonal_order=(1, 0, 0, 12)).fit()
    hw = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=12,
                              initialization_method="estimated").fit(optimized=True)
    rows = np.array([lag_features(train, at) for at in range(24, origin)])
    tree = GradientBoostingRegressor(n_estimators=120, max_depth=2, learning_rate=.05,
                                     loss="squared_error", random_state=7).fit(rows, train[24:])
    recursive = train.tolist()
    for at in range(origin, origin + HORIZON):
        recursive.append(float(tree.predict([lag_features(recursive, at)])[0]))
    predictions = [np.asarray(ar.forecast(HORIZON)), np.asarray(hw.forecast(HORIZON)), np.array(recursive[origin:])]
    # ARIMA interval is the model's 95% interval; it does not represent bounds
    # for Holt-Winters or boosting, which are shown as point forecasts.
    ci = np.asarray(ar.get_forecast(HORIZON).conf_int(alpha=.05))
    mechanisms = [dict(names=ar.param_names, values=ar.params.tolist(), converged=bool(ar.mle_retvals.get("converged", False))),
                  {k: float(hw.params[k]) for k in ("smoothing_level", "smoothing_trend", "smoothing_seasonal")},
                  dict(features=["lag 1", "lag 2", "lag 3", "lag 12", "lag 13", "lag 24", "time", "sin", "cos"],
                       importance=tree.feature_importances_.tolist())]
    return dict(origin=origin, predictions=predictions, ci=ci, mechanisms=mechanisms)


def compute():
    rng = np.random.default_rng(17)
    months = np.arange(216)
    innovation = rng.normal(0, .6, len(months))
    noise = np.zeros_like(innovation)
    for i in range(1, len(noise)):
        noise[i] = .55 * noise[i - 1] + innovation[i]
    series = 12 + .035 * months + 2.4 * np.sin(2 * np.pi * months / 12) + noise
    examples = [fit_origin(series, origin) for origin in (120, 156, 192)]
    for example in examples:
        origin = example["origin"]
        actual = series[origin:origin + HORIZON]
        example["rmse"] = [float(np.sqrt(np.mean((p - actual) ** 2))) for p in example["predictions"]]
        example["mae"] = [float(np.mean(abs(p - actual))) for p in example["predictions"]]
        limits = np.concatenate([series[origin - 48:origin + HORIZON], *example["predictions"], example["ci"].ravel()])
        lo, hi = 2 * np.floor(limits.min() / 2), 2 * np.ceil(limits.max() / 2)
        example["ylim"] = [lo, hi]
        example["yticks"] = np.arange(lo, hi + 1, 2 if hi - lo <= 14 else 4)
        assert all(np.isfinite(p).all() for p in example["predictions"])
        assert example["mechanisms"][0]["converged"], "ARIMA did not converge"
    # Refit after replacing EVERY future observation. All three forecasts
    # must remain identical; this catches both training and recursive leaks.
    changed = series.copy(); changed[120:] += 500
    proof = fit_origin(changed, 120)
    leak_error = max(float(np.max(abs(p - q))) for p, q in zip(examples[0]["predictions"], proof["predictions"]))
    assert leak_error == 0
    seasonal_baseline = series[108:120].tolist() * 2
    baseline_rmse = float(np.sqrt(np.mean((seasonal_baseline - series[120:144]) ** 2)))
    notes = ["Figure 3a: synthetic monthly sensor level, seed 17, 216 observations.",
             "Signal = 12 + 0.035 t + 2.4 sin(2 pi t/12) + AR(1) noise (phi .55, innovation SD .6).",
             "Origins 120, 156, 192. Each forecast predicts all 24 steps without observing future values.",
             "Seasonal ARIMA(1,1,1)x(1,0,0,12), fitted by statsmodels; all optimizers converged.",
             "Additive Holt-Winters: level, trend, 12-month seasonality, fitted by statsmodels.",
             "Gradient boosting: 120 depth-2 trees, learning rate .05; lags 1,2,3,12,13,24 plus known calendar features.",
             "Tree forecast is recursive: subsequent lag inputs are predictions, not withheld observations.",
             "All settings fixed before evaluation; independent examples, not a universal method ranking.",
             f"Changing all future observations by +500 leaves every forecast unchanged: max error {leak_error}.",
             f"Seasonal-naive 24-step reference RMSE at origin 120 = {baseline_rmse:.6f}.",
             "A 95% ARIMA prediction interval is displayed only for ARIMA.",
             "Sources: https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html",
             "https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html",
             "https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html"]
    for e in examples:
        notes.append(f"Origin {e['origin']}: RMSE {e['rmse']}; MAE {e['mae']} (ARIMA, Holt-Winters, trees).")
    return dict(series=series, horizon=HORIZON, examples=examples), notes


JS = r"""
const D = DATA, POSTER_T = 10, FIG = cv.closest('.fig');
let selected = 0;
function reset() { selected = 0; sync(); }
const titles = ['ARIMA: past values and errors', 'Exponential smoothing: level, trend, season', 'Gradient boosted trees: lagged features'];
function draw() {
  const ex = D.examples[selected], origin = ex.origin, start = origin - 48;
  const reveal = clamp((t - 1) / 5), actual = seg(6.5, .7);
  text('One history, three forecasts', 22, 31, {size: 20});
  text('24 months ahead; training ends before month ' + origin, 22, 59, {size: 16, color: C.muted});
  D.examples.forEach((e, i) => text('month ' + e.origin, 666 + i * 106, 42,
    {size: 15, color: i === selected ? C.ink : C.blue}));
  const colors = [C.blue, C.blue, C.blue];
  for (let j = 0; j < 3; j++) {
    const top = 110 + j * 300;
    panel(String.fromCharCode(97 + j), 22, top); text(titles[j], 58, top, {size: 18});
    const ax = axes({x: 100, y: top + 35, w: 550, h: 185, xlim: [start, origin + D.horizon - 1], ylim: ex.ylim,
      xticks: [start, start + 12, start + 24, start + 36, origin, origin + 12, origin + 23], yticks: ex.yticks,
      xlabel: '\\rm{month}', ylabel: '\\rm{sensor level (a.u.)}', grid: true, progress: seg(.02 * j, .35)});
    ax.inside(() => {
      ctx.fillStyle = C.steel; ctx.globalAlpha = .45; ctx.fillRect(ax.X(origin - .5), top + 35, ax.X(origin + 23) - ax.X(origin - .5), 185); ctx.globalAlpha = 1;
      const history = Array.from({length: 48}, (_, i) => [ax.X(start + i), ax.Y(D.series[start + i])]);
      line(history, {color: C.navy, width: 2.1, progress: seg(.12, .4)});
      const n = Math.max(1, Math.ceil(reveal * D.horizon));
      if (j === 0 && n > 1) {
        ctx.beginPath();
        ex.ci.slice(0, n).forEach((v, i) => i ? ctx.lineTo(ax.X(origin + i), ax.Y(v[0])) : ctx.moveTo(ax.X(origin), ax.Y(v[0])));
        for (let i = n - 1; i >= 0; i--) ctx.lineTo(ax.X(origin + i), ax.Y(ex.ci[i][1]));
        ctx.closePath(); ctx.fillStyle = C.mist; ctx.globalAlpha = .35; ctx.fill(); ctx.globalAlpha = 1;
      }
      const pp = ex.predictions[j].slice(0, n).map((v, i) => [ax.X(origin + i), ax.Y(v)]);
      line([[ax.X(origin - 1), ax.Y(D.series[origin - 1])], ...pp], {color: colors[j], width: 2.6});
      if (n) dot(...pp[n - 1], 4.5, {color: colors[j], fill: '#fff'});
      line(Array.from({length: 24}, (_, i) => [ax.X(origin + i), ax.Y(D.series[origin + i])]),
        {color: C.accent, width: 1.8, dash: [5, 4], alpha: actual});
      line([[ax.X(origin - .5), top + 35], [ax.X(origin - .5), top + 220]], {color: C.guide, width: 1, dash: [5, 4]});
    });
    text('Forecast', 653, top + 27, {size: 14, color: C.blue, align: 'right'});
    text('RMSE  ' + ex.rmse[j].toFixed(3), 708, top + 56, {size: 18, alpha: actual});
    text('MAE    ' + ex.mae[j].toFixed(3), 708, top + 85, {size: 17, alpha: actual});
    if (j === 0) {
      text('(1,1,1) x (1,0,0,12)', 708, top + 126, {size: 16});
      const names = ex.mechanisms[0].names, values = ex.mechanisms[0].values;
      names.slice(0, 3).forEach((name, i) => text(name + ' = ' + values[i].toFixed(3), 708, top + 157 + i * 23, {size: 15}));
      text('Shaded: 95% model interval', 708, top + 239, {size: 14, color: C.muted});
    } else if (j === 1) {
      const p = ex.mechanisms[1];
      text('Additive Holt-Winters', 708, top + 126, {size: 16});
      text('alpha (level) = ' + p.smoothing_level.toFixed(3), 708, top + 157, {size: 15});
      text('beta (trend) = ' + p.smoothing_trend.toFixed(3), 708, top + 180, {size: 15});
      text('gamma (season) = ' + p.smoothing_seasonal.toFixed(3), 708, top + 203, {size: 15});
      text('Period: 12 months', 708, top + 239, {size: 14, color: C.muted});
    } else {
      const p = ex.mechanisms[2], order = p.importance.map((v, i) => [i, v]).sort((a, b) => b[1] - a[1]).slice(0, 3);
      text('120 trees, depth 2, rate 0.05', 708, top + 126, {size: 15});
      text('Training feature importance', 708, top + 157, {size: 14, color: C.muted});
      order.forEach(([i, v], r) => {
        text(p.features[i], 708, top + 182 + r * 22, {size: 15});
        ctx.fillStyle = C.steel2; ctx.fillRect(778, top + 172 + r * 22, 100 * v, 11);
        text(v.toFixed(2), 920, top + 182 + r * 22, {size: 14, align: 'right'});
      });
      text('Future lags use predictions', 708, top + 259, {size: 14, color: C.muted});
    }
  }
  line([[100, 1050], [125, 1050]], {color: C.navy, width: 2}); text('observed history', 136, 1055, {size: 15});
  line([[325, 1050], [350, 1050]], {color: C.blue, width: 2.6}); text('forecast', 361, 1055, {size: 15});
  line([[495, 1050], [520, 1050]], {color: C.accent, width: 1.8, dash: [5, 4], alpha: actual});
  text('withheld observations', 531, 1055, {size: 15, alpha: actual});
  text('Synthetic monthly signal; each model sees the same past only. Errors compare all 24 forecast months.', 22, 1095, {size: 14, color: C.muted});
}
const buttons = [];
function sync() { buttons.forEach((b, i) => b.setAttribute('aria-pressed', String(i === selected))); }
if (!STILL) {
  const group = document.createElement('div'); group.setAttribute('role', 'group'); group.setAttribute('aria-label', 'Forecast origin');
  group.style.cssText = 'position:absolute;inset:0;pointer-events:none';
  D.examples.forEach((e, i) => {
    const b = document.createElement('button'); b.type = 'button'; b.textContent = 'month ' + e.origin;
    b.style.cssText = 'position:absolute;pointer-events:auto;background:transparent;border:0;color:transparent;padding:0;cursor:pointer;left:' +
      ((660 + i * 106) / 10) + '%;top:2%;width:10%;height:3%';
    b.setAttribute('aria-label', 'Forecast from month ' + e.origin);
    b.addEventListener('click', event => { event.stopPropagation(); selected = i; t = playing ? 0 : POSTER_T; render(); sync(); });
    group.appendChild(b); buttons.push(b);
  }); FIG.appendChild(group); sync();
}
boot();
"""


def main():
    data, notes = compute()
    common.build_html(NAME, "Figure 3a: Three numerical forecasting examples",
                      "Three forecasts of the same synthetic monthly sensor signal: seasonal ARIMA, additive "
                      "exponential smoothing and gradient boosted trees with lagged inputs. Held-out observations "
                      "are revealed after the 24-step forecasts. Choose between three forecast origins.",
                      1000, 1120, data, JS)
    print(common.still(NAME))
    print(common.frames(NAME, [.6, 3, 7, 10]))
    Path(__file__).with_suffix(".check.txt").write_text("\n".join(notes) + "\nPoster and intro overlap checks passed.\n", encoding="utf-8")
    print("\n".join(notes))


if __name__ == "__main__":
    main()
