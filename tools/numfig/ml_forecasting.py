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
/* the origin shown; TS: when it was chosen while playing (its forecasts are drawn again
   from then, quickly), null on the tour or when chosen paused; the chip under the pointer
   and the one pressed */
let selected = 0, TS = null, HOVER = -1, DOWN = -1;
function reset() { selected = 0; TS = null; sync(); }
/* the subtitles in the caption's own terms, lower case, as the family sets them */
const titles = ['seasonal ARIMA', 'additive Holt-Winters exponential smoothing', 'gradient boosted trees, lagged inputs'];
/* statsmodels' parameter names, as the textbook writes them */
const SYM = {'ar.L1': '\\phi_1', 'ma.L1': '\\theta_1', 'ar.S.L12': '\\Phi_1'};
function sub(l, x, y, words, a) { panel(l, x, y, {alpha: a}); text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }
const arrive = t0 => settle(t0, .28);
function tw(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
/* layout: the origin chips on the first line, as Figure 18b sets its number of neurons;
   each chip's hit area is 100 by 50 units around it */
const TOP = 36, PH = 340, AH = 200, RX = 708, VX = 880, KY = 1030;
const CH = {x: 664, y: TOP - 19, w: 92, h: 28, pitch: 106};
function draw() {
  const ex = D.examples[selected], origin = ex.origin, start = origin - 48, fresh = TS !== null;
  const reveal = fresh ? clamp((t - TS) / 1.2) : clamp((t - 1) / 5), actual = fresh ? seg(TS + 1.2, .3) : seg(6.5, .7);
  const head = fresh ? 1 : seg(.3, .3);
  text('forecast origin', CH.x - 14, TOP, {size: 15, color: C.body, align: 'right'});
  D.examples.forEach((e, i) => uiChip(CH.x + i * CH.pitch, CH.y, CH.w, CH.h, 'month ' + e.origin,
    {on: i === selected, hover: i === HOVER, down: i === DOWN}));
  for (let j = 0; j < 3; j++) {
    const top = TOP + j * PH, AY = top + 35;
    sub(String.fromCharCode(97 + j), 18, top, titles[j], arrive(.04 * j));
    const la = arrive(.25 + .05 * j);   // the panel's labels arrive with its axes
    const ax = axes({x: 100, y: AY, w: 550, h: AH, xlim: [start, origin + D.horizon - 1], ylim: ex.ylim,
      xticks: [start, start + 12, start + 24, start + 36, origin, origin + 12, origin + 23], yticks: ex.yticks,
      xlabel: '\\rm{month}', ylabel: '\\rm{sensor level (a.u.)}', grid: true, progress: seg(.02 * j, .35)});
    ax.inside(() => {
      ctx.fillStyle = C.steel; ctx.globalAlpha = .45; ctx.fillRect(ax.X(origin - .5), AY, ax.X(origin + 23) - ax.X(origin - .5), AH); ctx.globalAlpha = 1;
      const history = Array.from({length: 48}, (_, i) => [ax.X(start + i), ax.Y(D.series[start + i])]);
      line(history, {color: C.navy, width: 2.1, progress: seg(.12, .4)});
      const n = Math.max(1, Math.ceil(reveal * D.horizon));
      if (j === 0 && n > 1) {
        ctx.beginPath();
        ex.ci.slice(0, n).forEach((v, i) => i ? ctx.lineTo(ax.X(origin + i), ax.Y(v[0])) : ctx.moveTo(ax.X(origin), ax.Y(v[0])));
        for (let i = n - 1; i >= 0; i--) ctx.lineTo(ax.X(origin + i), ax.Y(ex.ci[i][1]));
        ctx.closePath(); ctx.fillStyle = C.mist; ctx.globalAlpha = .35; ctx.fill(); ctx.globalAlpha = 1;
      }
      // what happened: open navy marks on a hairline, once the forecasts are drawn
      const seen = Array.from({length: 24}, (_, i) => [ax.X(origin + i), ax.Y(D.series[origin + i])]);
      line([history[47], ...seen], {color: C.navy, width: 1, alpha: actual});
      seen.forEach(p => dot(...p, 2.6, {color: C.navy, fill: '#fff', width: 1.2, alpha: actual}));
      // the forecast, the line to follow: crimson, drawn over what happened
      const pp = ex.predictions[j].slice(0, n).map((v, i) => [ax.X(origin + i), ax.Y(v)]);
      line([[ax.X(origin - 1), ax.Y(D.series[origin - 1])], ...pp], {color: C.accent, width: 2.6, alpha: head});
      dot(...pp[n - 1], 4.5, {color: C.accent, fill: '#fff', alpha: head});
      line([[ax.X(origin - .5), AY], [ax.X(origin - .5), AY + AH]], {color: C.guide, width: 1, dash: [5, 4]});
    });
    text('forecast', ax.X(origin - .5) + 7, AY + AH - 12, {size: 14, color: C.accent, alpha: la});
    // the errors: a label and a value on one right edge, one size
    text('RMSE', RX, AY + 21, {size: 16, alpha: actual}); text(ex.rmse[j].toFixed(3), VX, AY + 21, {size: 16, align: 'right', alpha: actual});
    text('MAE', RX, AY + 45, {size: 16, alpha: actual}); text(ex.mae[j].toFixed(3), VX, AY + 45, {size: 16, align: 'right', alpha: actual});
    if (j === 0) {
      math('(1,\\,1,\\,1)\\ \\times\\ (1,\\,0,\\,0)_{12}', RX, AY + 84, {size: 16, alpha: la});
      const names = ex.mechanisms[0].names, values = ex.mechanisms[0].values;
      names.slice(0, 3).forEach((name, i) => math((SYM[name] || '\\rm{' + name + '}') + ' = ' + values[i].toFixed(3), RX, AY + 112 + i * 23, {size: 15, alpha: la}));
      text('shaded: 95% model interval', RX, AY + AH, {size: 14, color: C.muted, alpha: la});
    } else if (j === 1) {
      const p = ex.mechanisms[1];
      text('additive Holt-Winters', RX, AY + 84, {size: 16, alpha: la});
      math('\\alpha\\ \\rm{(level)} = ' + p.smoothing_level.toFixed(3), RX, AY + 112, {size: 15, alpha: la});
      math('\\beta\\ \\rm{(trend)} = ' + p.smoothing_trend.toFixed(3), RX, AY + 135, {size: 15, alpha: la});
      math('\\gamma\\ \\rm{(season)} = ' + p.smoothing_seasonal.toFixed(3), RX, AY + 158, {size: 15, alpha: la});
      text('period: 12 months', RX, AY + AH, {size: 14, color: C.muted, alpha: la});
    } else {
      const p = ex.mechanisms[2], order = p.importance.map((v, i) => [i, v]).sort((a, b) => b[1] - a[1]).slice(0, 3);
      text('120 trees, depth 2, rate 0.05', RX, AY + 84, {size: 16, alpha: la});
      text('training feature importance', RX, AY + 110, {size: 14, color: C.muted, alpha: la});
      order.forEach(([i, v], r) => {
        const y = AY + 133 + r * 21, x1 = 778 + 100 * v;
        text(p.features[i], RX, y, {size: 15, alpha: la});
        line([[778, y - 10], [x1, y - 10], [x1, y + 1], [778, y + 1]], {color: C.blue, width: 1, fill: C.mist, close: true, alpha: la});
        text(v.toFixed(2), VX, y, {size: 14, align: 'right', alpha: la});
      });
      text('future lags use predictions', RX, AY + AH, {size: 14, color: C.muted, alpha: la});
    }
  }
  // the key, as the family draws one: a thin box, white fill, serif 15
  const keys = [
    [x => line([[x, KY + 16], [x + 28, KY + 16]], {color: C.navy, width: 2.1}), 'observed history', 1],
    [x => line([[x, KY + 16], [x + 28, KY + 16]], {color: C.accent, width: 2.6}), 'forecast', 1],
    [x => { line([[x, KY + 16], [x + 28, KY + 16]], {color: C.navy, width: 1, alpha: actual});
            dot(x + 14, KY + 16, 2.6, {color: C.navy, fill: '#fff', width: 1.2, alpha: actual}); }, 'withheld observations', actual]];
  const room = 550 - 32 - keys.reduce((s, k) => s + 36 + tw(k[1], 15), 0);
  line([[100, KY], [650, KY], [650, KY + 32], [100, KY + 32]], {color: C.ink, width: 1, fill: '#fff', close: true});
  let kx = 116;
  keys.forEach(([mark, label, a]) => { mark(kx); kx += 36 + text(label, kx + 36, KY + 21, {size: 15, alpha: a}) + room / 2; });
  text('synthetic monthly signal; each model sees the same past only; errors compare all 24 forecast months', 18, H - 14, {size: 14, color: C.muted});
}
const radios = [];
let said = null;
function sync() { radios.forEach((b, i) => { b.setAttribute('aria-checked', String(i === selected)); b.tabIndex = i === selected ? 0 : -1; }); }
/* choosing never pauses: playing, the new origin's forecasts are drawn again from now
   (1.2 s, then what happened); paused, the figure shows them complete */
function choose(i) {
  selected = i; TS = playing ? t : null; if (!playing) t = POSTER_T; render(); sync();
  const e = D.examples[i];
  if (said) said.textContent = 'Forecast from month ' + e.origin + ': RMSE ' + e.rmse.map(v => v.toFixed(3)).join(', ') +
    ' for ARIMA, Holt-Winters and the trees.';
}
if (!STILL) {
  document.head.insertAdjacentHTML('beforeend', '<style>.nfm{position:absolute;pointer-events:auto;box-sizing:border-box;margin:0;padding:0;' +
    'border:0;background:transparent;color:transparent;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.nfm:focus{outline:none}.nfm::after{content:"";position:absolute;inset:22% 4%}' +
    '.nfm:focus-visible::after{outline:2px solid #095A94;outline-offset:1px}</style>');   // the ring hugs the drawn chip
  const group = document.createElement('div'); group.setAttribute('role', 'radiogroup'); group.setAttribute('aria-label', 'Forecast origin');
  group.style.cssText = 'position:absolute;inset:0;pointer-events:none';
  const N = D.examples.length;
  D.examples.forEach((e, i) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'nfm'; b.textContent = 'month ' + e.origin;
    b.setAttribute('role', 'radio'); b.setAttribute('aria-label', 'Forecast from month ' + e.origin);
    b.style.left = (CH.x - 4 + i * CH.pitch) / 10 + '%'; b.style.width = '10%';
    b.style.top = (CH.y + CH.h / 2 - 25) / H * 100 + '%'; b.style.height = 50 / H * 100 + '%';
    b.addEventListener('click', ev => { ev.stopPropagation(); choose(i); });
    b.addEventListener('keydown', ev => {
      const step = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[ev.key];
      const to = step ? (i + step + N) % N : ev.key === 'Home' ? 0 : ev.key === 'End' ? N - 1 : -1;
      if (to < 0) return;
      ev.preventDefault(); choose(to); radios[to].focus();
    });
    b.addEventListener('pointerenter', () => { HOVER = i; render(); });
    b.addEventListener('pointerleave', () => { HOVER = -1; DOWN = -1; render(); });
    b.addEventListener('pointerdown', () => { DOWN = i; render(); });
    b.addEventListener('pointerup', () => { DOWN = -1; render(); });
    b.addEventListener('pointercancel', () => { HOVER = -1; DOWN = -1; render(); });
    group.appendChild(b); radios.push(b);
  });
  FIG.insertBefore(group, FIG.querySelector('.ctl'));
  said = document.createElement('div'); said.setAttribute('role', 'status');
  // pinned inside the frame: left at its place under the canvas it made the frame 1 px too tall (a scrollbar)
  said.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;pointer-events:none';
  FIG.appendChild(said); sync();
  // a click just beside the chips or on their label is meant for them: it never pauses
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), X = (e.clientX - r.left) * W / r.width, Y = (e.clientY - r.top) * H / r.height;
    if (Y < CH.y + CH.h + 18 && X > CH.x - 150) e.stopPropagation();
  }, true);
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
