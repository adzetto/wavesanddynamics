"""Figure 2a: seasonal ARIMA, exponential smoothing and lagged boosted trees.

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
    notes = ["Figure 2a: synthetic monthly sensor level, seed 17, 216 observations.",
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
const D = DATA, POSTER_T = 8, FIG = cv.closest('.fig');
/* the origin on show. The tour takes the three origins in turn, PER s each: the history is
   drawn, then the forecasts, then what happened and the errors; they rest, and fade out before
   the next origin comes in. A chosen origin (a chip, the keyboard, or ?origin=0..2 for the
   checks) stops the tour there. TS: when it was chosen while playing (it is drawn in again from
   then), null when chosen paused or preset (complete at once); HOVER, DOWN: the chip under the
   pointer and the one pressed */
const PER = 10, PICK = /[?&]origin=([0-2])\b/.exec(location.search);
let manual = PICK ? +PICK[1] : null, TS = null, HOVER = -1, DOWN = -1, shown = -1;
function reset() { manual = PICK ? +PICK[1] : null; TS = null; sync(); }
/* the subtitles in the caption's own terms, lower case, as the family sets them */
const titles = ['seasonal ARIMA', 'Holt-Winters smoothing', 'gradient boosted trees'];
/* statsmodels' parameter names, as the textbook writes them */
const SYM = {'ar.L1': '\\phi_1', 'ma.L1': '\\theta_1', 'ar.S.L12': '\\Phi_1'};
function sub(l, x, y, words, a) { panel(l, x, y, {alpha: a}); text(words, x + 35, y, {size: 17, color: C.body, alpha: a}); }
function tw(s, size) { ctx.save(); ctx.font = font({size}); const w = ctx.measureText(s).width; ctx.restore(); return w; }
/* layout: the three panels side by side, each with its errors and its fitted model under it, the
   key under them all; the origin chips on the first line, as Figure 18b sets its number of
   neurons (each chip's hit area 108 by 50 units around it) */
const PX = [80, 395, 710], PY = 100, PW = 270, PH = 214, SY = 398, KY = 546;
const CH = {x: 666, y: 12, w: 100, h: 30, pitch: 108};
/* where the drawing is: the origin i, the time u since it began to come in (s0: that moment on
   the clock), and how much of it shows (fade: 1, or going out at the end of its turn) */
function state() {
  if (manual !== null) return TS === null ? {i: manual, u: 99, s0: -99, fade: 1} : {i: manual, u: t - TS, s0: TS, fade: 1};
  const k = Math.floor(t / PER), u = t - k * PER;
  return {i: k % 3, u, s0: k * PER, fade: 1 - clamp((u - (PER - .4)) / .4)};
}
function draw() {
  const S = state(), ex = D.examples[S.i], origin = ex.origin, start = origin - 48, end = origin + 24, F = S.fade;
  if (S.i !== shown) { shown = S.i; sync(); }
  const E = (a, d) => easeInOut(clamp((S.u - a) / d));
  // in turn: the history (.1 s), the forecasts (.35 s, drawn forward in .75 s), what happened and
  // the errors (1.05 s); this origin's numbers come in with it, the rest of the figure stays
  const hist = E(.1, .4), reveal = clamp((S.u - .35) / .75), act = E(1.05, .3) * F, L = F * clamp(S.u / .3);
  const ar = d => settle(S.s0 + d, .28) * F;
  text('forecast origin', CH.x - 14, CH.y + 20, {size: 16, color: C.body, align: 'right', alpha: settle(0, .28)});
  D.examples.forEach((e, i) => uiChip(CH.x + i * CH.pitch, CH.y, CH.w, CH.h, 'month ' + e.origin,
    {on: i === S.i, hover: i === HOVER, down: i === DOWN, size: 16}));
  // regular 12-month ticks up to origin + 24: the last forecast month falls just before the end
  const xt = [0, 1, 2, 3, 4, 5, 6].map(k => start + 12 * k);
  const yt = ex.yticks.filter(v => (v - ex.yticks[0]) % 4 === 0);
  for (let j = 0; j < 3; j++) {
    const P = {x: PX[j], y: PY, w: PW, h: PH}, ap = seg(.02 * j, .35), aa = clamp(ap * 1.4);
    const X = v => P.x + (v - start) / (end - start) * P.w, Y = v => P.y + P.h - (v - ex.ylim[0]) / (ex.ylim[1] - ex.ylim[0]) * P.h;
    sub(String.fromCharCode(97 + j), P.x - 62, 80, titles[j], settle(.04 * j, .28));
    // the light grid and the ticks as axes() draws them; the numbers are this origin's
    for (const v of xt) line([[X(v), P.y], [X(v), P.y + P.h]], {color: C.grid, width: 1, alpha: aa});
    for (const v of yt) line([[P.x, Y(v)], [P.x + P.w, Y(v)]], {color: C.grid, width: 1, alpha: aa * L});
    const ax = axes({...P, xlim: [start, end], ylim: ex.ylim, xlabel: '\\rm{month}', ylabel: j ? '' : '\\rm{sensor level (a.u.)}',
      tickSize: 16, progress: ap});
    for (const v of xt) {
      line([[X(v), P.y + P.h], [X(v), P.y + P.h - 5]], {width: 1.1, alpha: aa});
      line([[X(v), P.y], [X(v), P.y + 5]], {width: 1.1, alpha: aa});
      math(fmt(v), X(v), P.y + P.h + 22, {size: 16, align: 'center', alpha: aa * L});
    }
    for (const v of yt) {
      line([[P.x, Y(v)], [P.x + 5, Y(v)]], {width: 1.1, alpha: aa * L});
      line([[P.x + P.w, Y(v)], [P.x + P.w - 5, Y(v)]], {width: 1.1, alpha: aa * L});
      math(fmt(v), P.x - 8, Y(v) + 5.6, {size: 16, align: 'right', alpha: aa * L});
    }
    ax.inside(() => {
      ctx.fillStyle = C.steel; ctx.globalAlpha = .45 * aa; ctx.fillRect(X(origin - .5), P.y, X(end) - X(origin - .5), P.h); ctx.globalAlpha = 1;
      const history = Array.from({length: 48}, (_, i) => [X(start + i), Y(D.series[start + i])]);
      const n = Math.max(1, Math.ceil(reveal * D.horizon));
      if (j === 0 && reveal > 0 && n > 1) {
        ctx.beginPath();
        ex.ci.slice(0, n).forEach((v, i) => i ? ctx.lineTo(X(origin + i), Y(v[0])) : ctx.moveTo(X(origin), Y(v[0])));
        for (let i = n - 1; i >= 0; i--) ctx.lineTo(X(origin + i), Y(ex.ci[i][1]));
        ctx.closePath(); ctx.fillStyle = C.mist; ctx.globalAlpha = .35 * F; ctx.fill(); ctx.globalAlpha = 1;
      }
      line(history, {color: C.navy, width: 2.1, progress: hist, alpha: F});
      // what happened: open navy marks on a hairline, once the forecasts are drawn
      const seen = Array.from({length: 24}, (_, i) => [X(origin + i), Y(D.series[origin + i])]);
      line([history[47], ...seen], {color: C.navy, width: 1, alpha: act});
      seen.forEach(p => dot(...p, 2.6, {color: C.navy, fill: '#fff', width: 1.2, alpha: act}));
      // the forecast, the line to follow: crimson, drawn over what happened
      if (reveal > 0) {
        const pp = ex.predictions[j].slice(0, n).map((v, i) => [X(origin + i), Y(v)]);
        line([[X(origin - 1), Y(D.series[origin - 1])], ...pp], {color: C.accent, width: 2.6, alpha: F});
        dot(...pp[n - 1], 4.5, {color: C.accent, fill: '#fff', alpha: F});
      }
      line([[X(origin - .5), P.y], [X(origin - .5), P.y + P.h]], {color: C.guide, width: 1, dash: [5, 4], alpha: aa});
    });
    // under the panel: its errors, then the model as fitted to this history
    const x0 = P.x, la = ar(.25 + .05 * j);
    text('RMSE', x0, SY, {size: 17, alpha: act}); text(ex.rmse[j].toFixed(3), x0 + 58, SY, {size: 17, alpha: act});
    text('MAE', x0 + 140, SY, {size: 17, alpha: act}); text(ex.mae[j].toFixed(3), x0 + 189, SY, {size: 17, alpha: act});
    if (j === 0) {
      const v = ex.mechanisms[0].values, nm = ex.mechanisms[0].names, s = k => (SYM[nm[k]] || '\\rm{' + nm[k] + '}') + ' = ' + v[k].toFixed(3);
      math('(1,\\,1,\\,1)\\ \\times\\ (1,\\,0,\\,0)_{12}', x0, SY + 27, {size: 16, alpha: la});
      math(s(0) + ',\\ \\ ' + s(1), x0, SY + 53, {size: 16, alpha: la});
      math(s(2), x0, SY + 79, {size: 16, alpha: la});
    } else if (j === 1) {
      const p = ex.mechanisms[1];
      text('additive, 12-month season', x0, SY + 27, {size: 16, alpha: la});
      math('\\alpha\\ \\rm{(level)} = ' + p.smoothing_level.toFixed(3), x0, SY + 53, {size: 16, alpha: la});
      math('\\beta\\ \\rm{(trend)} = ' + p.smoothing_trend.toFixed(3), x0, SY + 79, {size: 16, alpha: la});
      math('\\gamma\\ \\rm{(season)} = ' + p.smoothing_seasonal.toFixed(3), x0, SY + 105, {size: 16, alpha: la});
    } else {
      const p = ex.mechanisms[2], order = p.importance.map((v, i) => [i, v]).sort((a, b) => b[1] - a[1]).slice(0, 3);
      text('120 trees, depth 2, rate 0.05', x0, SY + 27, {size: 16, alpha: la});
      text('training feature importance', x0, SY + 52, {size: 15, color: C.muted, alpha: la});
      order.forEach(([i, v], r) => {
        const y = SY + 78 + r * 25, b0 = x0 + 66, b1 = b0 + 120 * v;
        text(p.features[i], x0, y, {size: 16, alpha: la});
        line([[b0, y - 11], [b1, y - 11], [b1, y + 1], [b0, y + 1]], {color: C.blue, width: 1, fill: C.mist, close: true, alpha: la});
        text(v.toFixed(2), x0 + 236, y, {size: 16, align: 'right', alpha: la});
      });
    }
  }
  // the key, as the family draws one: a thin box, white fill, serif 16; what happened comes in
  // with the first errors and stays
  const ka = seg(1.05, .3);
  const keys = [
    [x => line([[x, KY + 16], [x + 28, KY + 16]], {color: C.navy, width: 2.1}), 'observed history', 1],
    [x => line([[x, KY + 16], [x + 28, KY + 16]], {color: C.accent, width: 2.6}), 'forecast', 1],
    [x => { line([[x, KY + 16], [x + 28, KY + 16]], {color: C.navy, width: 1, alpha: ka});
            dot(x + 14, KY + 16, 2.6, {color: C.navy, fill: '#fff', width: 1.2, alpha: ka}); }, 'withheld observations', ka],
    [x => { ctx.save(); ctx.globalAlpha = .6; ctx.fillStyle = C.mist; ctx.fillRect(x, KY + 9, 28, 14); ctx.restore(); }, 'ARIMA 95% interval', 1]];
  const gap = 26, wk = keys.reduce((s, k) => s + 36 + tw(k[1], 16), 0) + gap * (keys.length - 1) + 32;
  line([[PX[0], KY], [PX[0] + wk, KY], [PX[0] + wk, KY + 32], [PX[0], KY + 32]], {color: C.ink, width: 1, fill: '#fff', close: true});
  let kx = PX[0] + 16;
  keys.forEach(([mark, label, a]) => { mark(kx); kx += 36 + text(label, kx + 36, KY + 21, {size: 16, alpha: a}) + gap; });
  text('synthetic monthly signal, seed 17, 216 months', 18, H - 14, {size: 15, color: C.muted});
}
const radios = [];
let said = null;
function sync() { radios.forEach((b, i) => { b.setAttribute('aria-checked', String(i === shown)); b.tabIndex = i === shown ? 0 : -1; }); }
/* choosing never pauses: playing, the new origin is drawn in again from now (history, forecasts,
   then what happened) and stays; paused, the figure shows it complete */
function choose(i) {
  manual = i; TS = playing ? t : null; if (!playing) t = Math.max(t, POSTER_T); render(); sync();
  const e = D.examples[i];
  if (said) said.textContent = 'Forecast from month ' + e.origin + ': RMSE ' + e.rmse.map(v => v.toFixed(3)).join(', ') +
    ' for ARIMA, Holt-Winters and the trees.';
}
if (!STILL) {
  document.head.insertAdjacentHTML('beforeend', '<style>.nfm{position:absolute;pointer-events:auto;box-sizing:border-box;margin:0;padding:0;' +
    'border:0;background:transparent;color:transparent;cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.nfm:focus{outline:none}.nfm::after{content:"";position:absolute;inset:20% 3.7%}' +
    '.nfm:focus-visible::after{outline:2px solid #095A94;outline-offset:1px}</style>');   // the ring hugs the drawn chip
  const group = document.createElement('div'); group.setAttribute('role', 'radiogroup'); group.setAttribute('aria-label', 'Forecast origin');
  group.style.cssText = 'position:absolute;inset:0;pointer-events:none';
  const N = D.examples.length;
  D.examples.forEach((e, i) => {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'nfm'; b.textContent = 'month ' + e.origin;
    b.setAttribute('role', 'radio'); b.setAttribute('aria-label', 'Forecast from month ' + e.origin);
    b.style.left = (CH.x - 4 + i * CH.pitch) / 10 + '%'; b.style.width = (CH.pitch) / 10 + '%';
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
    if (Y < CH.y + CH.h + 18 && X > CH.x - 130) e.stopPropagation();
  }, true);
}
boot();
"""


# the page (1000 x 630): the three panels side by side, as the timing and the checks run them
PAGE = ["Page: 1000 x 630, the three panels side by side; each panel's errors and fitted model under it.",
        "Timing: the history is drawn by 0.5 s, the forecasts from 0.35 s to 1.1 s, what happened and the errors",
        "by 1.35 s. The tour then rests 8.25 s on each origin (120, 156, 192, 10 s each), fades it out in 0.4 s",
        "and draws the next in; a chosen origin stops the tour there (?origin=0..2 presets one for the checks).",
        "x ticks every 12 months from origin - 48 to origin + 24; the last forecast month is origin + 23."]


def main():
    data, notes = compute()
    common.build_html(NAME, "Figure 2a: Three numerical forecasting examples",
                      "Three forecasts of the same synthetic monthly sensor signal, side by side: seasonal ARIMA, "
                      "additive exponential smoothing and gradient boosted trees with lagged inputs. Held-out "
                      "observations are revealed after the 24-step forecasts. The figure steps through three forecast "
                      "origins; choose one to stay on it.",
                      1000, 630, data, JS)
    print(common.still(NAME))
    print(common.frames(NAME, [.6, 1.4, 5, 9.8, 10.5, 12]))
    Path(__file__).with_suffix(".check.txt").write_text("\n".join(notes + PAGE) + "\nPoster, intro and tour overlap checks passed.\n",
                                                        encoding="utf-8")
    print("\n".join(notes + PAGE))


if __name__ == "__main__":
    main()
