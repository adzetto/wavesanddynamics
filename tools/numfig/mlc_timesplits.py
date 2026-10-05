"""Figure 33 of the machine learning guide (image30): splitting time-ordered data.

Series: two years of daily values, a yearly cycle, a slow drift and noise that
remembers yesterday (AR(1), phi = 0.8), seed 4: the kind of record a sensor
keeps. Model: least squares on (1, t, sin, cos of the yearly cycle); score: mean
absolute error (MAE) on the days held out.

(a) A random split: 80 % of the days train, 20 % test, drawn at random, so the
    model trains on days after the ones it is tested on.
(b) A chronological holdout: one cut; the oldest 60 % train, the next 20 %
    validate, the latest 20 % test.
(c) Expanding window cross-validation: four rounds, training on all the history
    before each validation window.
(d) Sliding window cross-validation: the same validation windows, training on
    the 300 days before each.
In (c) and (d) a gap of 14 days separates training from validation.

Run: python tools/numfig/mlc_timesplits.py
"""
import numpy as np

import mlc_lib as lib

NAME = "mlc-timesplits"
T = 730
rng = np.random.default_rng(4)
t = np.arange(T)
noise = np.zeros(T)
for k in range(1, T):
    noise[k] = 0.8 * noise[k - 1] + rng.normal(0, 1.0)
y = 20 + 6 * np.sin(2 * np.pi * (t - 80) / 365) + 0.004 * t + noise


def design(tt):
    w = 2 * np.pi * tt / 365
    return np.column_stack([np.ones_like(tt, float), tt / 365, np.sin(w), np.cos(w)])


def fit_score(tr, te):
    beta = np.linalg.lstsq(design(tr), y[tr], rcond=None)[0]
    pred = design(te) @ beta
    return float(np.mean(np.abs(pred - y[te]))), beta


# (a) random
perm = rng.permutation(T)
test_r = np.sort(perm[:146])
train_r = np.sort(perm[146:])
mae_r, _ = fit_score(train_r, test_r)
later = int(np.sum(train_r > test_r.min()))
# (b) holdout
c1, c2 = 438, 584
mae_bv, _ = fit_score(np.arange(0, c1), np.arange(c1, c2))
mae_bt, _ = fit_score(np.arange(0, c2), np.arange(c2, T))
# (c), (d): the same four validation windows, 60 days each, ending at the last day
H, GAPD, WIN = 60, 14, 300
vals = [(T - (4 - k) * H, T - (3 - k) * H) for k in range(4)]
exp_, sld = [], []
for v0, v1 in vals:
    te = np.arange(v0, v1)
    e = fit_score(np.arange(0, v0 - GAPD), te)[0]
    s = fit_score(np.arange(v0 - GAPD - WIN, v0 - GAPD), te)[0]
    exp_.append({"tr": [0, v0 - GAPD], "va": [v0, v1], "mae": e})
    sld.append({"tr": [v0 - GAPD - WIN, v0 - GAPD], "va": [v0, v1], "mae": s})

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-timesplits: Figure 33, splitting time-ordered data")
say("")
say("SERIES: 730 days, y = 20 + 6 sin(2 pi (t - 80)/365) + 0.004 t + e_t, e_t = 0.8 e_(t-1) + N(0, 1),")
say("  seed 4. MODEL: least squares on (1, t/365, sin, cos of 2 pi t/365). SCORE: MAE.")
say("")
say(f"(a) RANDOM: 584 training days, 146 test days at random; {later} of the 584 training days come")
say(f"    after the earliest test day: the model trains on the future of the days it is tested on.")
say(f"    Test MAE {mae_r:.3f}.")
say(f"(b) HOLDOUT: train days 0-{c1 - 1}, validate {c1}-{c2 - 1}, test {c2}-{T - 1}.")
say(f"    validation MAE {mae_bv:.3f} (trained on 0-{c1 - 1}); test MAE {mae_bt:.3f} (refit on 0-{c2 - 1}).")
say(f"(c) EXPANDING, (d) SLIDING ({WIN} days): gap {GAPD} days, validation windows of {H} days:")
for k in range(4):
    say(f"    round {k + 1}: validate {vals[k][0]}-{vals[k][1] - 1};  expanding trains 0-{exp_[k]['tr'][1] - 1},"
        f" MAE {exp_[k]['mae']:.3f};  sliding trains {sld[k]['tr'][0]}-{sld[k]['tr'][1] - 1}, MAE {sld[k]['mae']:.3f}")
say(f"    means: expanding {np.mean([r['mae'] for r in exp_]):.3f}, sliding {np.mean([r['mae'] for r in sld]):.3f}")
say("")
say("CHECKS")
ok = all(r["tr"][1] + GAPD == r["va"][0] for r in exp_ + sld)
say(f"  every training window ends {GAPD} days before its validation window: {ok}")
say(f"  every training day precedes every validation day in (b), (c), (d): True by construction;")
say(f"  in (a) it does not: the random split's MAE ({mae_r:.3f}) is lower than the honest")
say(f"  forward-looking scores ({np.mean([r['mae'] for r in exp_]):.3f}), because it interpolates between")
say("  days it has already seen on both sides.")
say(f"  noise level for reference: the AR(1) noise has standard deviation {1 / np.sqrt(1 - .64):.3f}, MAE of a")
say(f"  perfect model about {np.sqrt(2 / np.pi) / np.sqrt(1 - .64):.3f}.")

DATA = {"y": y.round(3).tolist(), "test_r": test_r.tolist(), "cuts": [c1, c2], "exp": exp_, "sld": sld,
        "mae": {"r": mae_r, "bv": mae_bv, "bt": mae_bt}, "ylim": [float(y.min()) - .5, float(y.max()) + .5]}

JS = r"""
const Y = DATA.y, NT = Y.length, TEST = new Uint8Array(NT); DATA.test_r.forEach(i => TEST[i] = 1);
const X0 = 150, XW = 700, X = d => X0 + d / NT * XW;
const RH = 30, [YLO, YHI] = DATA.ylim, Yp = (v, y0) => y0 + RH - 2 - (v - YLO) / (YHI - YLO) * (RH - 4);
const COL = { tr: C.blue, va: C.accent, te: C.navy, gap: C.guide, off: C.rule };
const BAND = { tr: C.steel, va: C.wash, te: C.steel2, gap: null, off: null };
const T0 = .6, DR = .5, TLOOP = T0 + 4 * DR + .9, PER = 1.5;
const POSTER_T = TLOOP - .2;
function focus() { if (t < TLOOP) return -1; return Math.floor((t - TLOOP) / PER) % 4; }
/* one row: the series between day a and b, each stretch drawn in its role's colour over a light band */
function row(y0, parts, draw, dim = 1) {
  parts.forEach(([a, b, r]) => {
    if (BAND[r] && b > a) { ctx.save(); ctx.globalAlpha = dim * draw; ctx.fillStyle = BAND[r]; ctx.fillRect(X(a), y0, X(b) - X(a), RH); ctx.restore(); }
  });
  const upto = draw * NT;
  parts.forEach(([a, b, r]) => {
    const e = Math.min(b, upto); if (e <= a) return;
    const pts = []; for (let d = a; d < e; d++) pts.push([X(d + .5), Yp(Y[d], y0)]);
    line(pts, { color: COL[r], width: r === 'off' ? 1 : 1.3, alpha: dim, dash: r === 'gap' ? [2, 2] : null });
  });
}
function splits(w) { const [a, b] = w.tr, [c, d] = w.va; return [[0, a, 'off'], [a, b, 'tr'], [b, c, 'gap'], [c, d, 'va'], [d, NT, 'off']]; }
function draw() {
  const fr = focus();
  const blocks = [['a', 'random split', 58], ['b', 'chronological holdout', 150], ['c', 'expanding window cross-validation', 242], ['d', 'sliding window cross-validation', 418]];
  blocks.forEach(([l, s, y], k) => sub(l, 18, y, s, seg(.05 + .04 * k, .3)));
  lab('MAE', 900, 58, .3, { size: 14, color: C.muted });
  // (a) every day a dot, training or test at random
  const ya = 70, da = seg(.1, .6);
  ctx.save(); ctx.globalAlpha = seg(.1, .3); ctx.fillStyle = C.steel; ctx.fillRect(X(0), ya, XW, RH); ctx.restore();
  for (let d = 0; d < NT * da; d++) { const te = TEST[d] === 1;
    dot(X(d + .5), Yp(Y[d], ya), te ? 1.6 : 1.1, { color: te ? C.accent : C.blue, fill: te ? C.accent : C.blue, width: .4 }); }
  lab('test days fall between training days', X0, ya + RH + 18, .5, { size: 14, color: C.muted });
  const ma = seg(.7, .3);
  text(nf(DATA.mae.r, 2), 900, ya + RH / 2 + 5, { size: 15, alpha: ma });
  // (b) one cut
  const yb = 162, [c1, c2] = DATA.cuts;
  row(yb, [[0, c1, 'tr'], [c1, c2, 'va'], [c2, NT, 'te']], seg(.15, .6));
  [['training 60%', 0, c1, C.blue], ['validation', c1, c2, C.accent], ['test', c2, NT, C.navy]].forEach(([s, a, b, c], k) =>
    lab(s, (X(a) + X(b)) / 2, yb + RH + 17, .55 + .05 * k, { size: 14, align: 'center', color: c }));
  text(nf(DATA.mae.bt, 2), 900, yb + RH / 2 + 5, { size: 15, alpha: seg(.75, .3) });
  // (c), (d): four rounds each, arriving one after another, then taking turns
  [['exp', 254], ['sld', 430]].forEach(([key, y0], b) => {
    DATA[key].forEach((w, k) => {
      const y = y0 + k * (RH + 8), on = fr < 0 || fr === k, arrive = settle(T0 + DR * k + .05 * b, .35);
      lab(`round ${k + 1}`, 18, y + RH / 2 + 5, T0 + DR * k - .1 + .05 * b, { size: 15, alpha: on ? 1 : .45 });
      if (arrive <= 0) return;
      const tr = [lerp(w.va[0], w.tr[0], arrive), lerp(w.va[0], w.tr[1], arrive)];
      row(y, splits({ tr: [Math.round(tr[0]), Math.round(tr[1])], va: w.va }), 1, on ? 1 : .35);
      text(nf(w.mae, 2), 900, y + RH / 2 + 5, { size: 15, alpha: arrive * (on ? 1 : .45), color: fr === k ? C.accent : C.ink });
    });
    const m = DATA[key].reduce((s, w) => s + w.mae, 0) / 4, mt = seg(T0 + 4 * DR, .3);
    line([[890, y0 + 4 * (RH + 8) - 2], [950, y0 + 4 * (RH + 8) - 2]], { width: 1, alpha: mt });
    mlab(`\\rm{mean}\\ ${nf(m, 2)}`, 890, y0 + 4 * (RH + 8) + 16, T0 + 4 * DR, { size: 15 });
  });
  lab('gap', X(DATA.exp[0].tr[1]) - 2, 254 - 6, T0 + .3, { size: 14, color: C.muted });
  // the moving present: where the focused round's validation starts
  if (fr >= 0) { const xv = X(DATA.exp[fr].va[0]), a = clamp(((t - TLOOP) % PER) / .25);
    line([[xv, 254], [xv, 430 + 4 * (RH + 8) - 6]], { color: C.accent, width: 1, dash: [4, 3], alpha: .6 * a }); }
  // the time axis
  const ay = 622, axa = seg(.1, .4);
  line([[X0, ay], [X0 + XW, ay]], { width: 1.3, progress: axa });
  for (let d = 0; d <= 700; d += 100) { line([[X(d), ay], [X(d), ay + 5]], { width: 1, alpha: axa }); text(String(d), X(d), ay + 21, { size: 15, align: 'center', alpha: axa }); }
  math('\\rm{day}', X0 + XW + 24, ay + 5, { size: 17, alpha: axa });
  text('two years of daily values: yearly cycle, slow drift, correlated noise; model: trend + yearly cycle, least squares; score: mean absolute error',
       18, H - 12, { size: 14, color: C.muted, alpha: seg(.6, .4) });
}
boot();
"""

TITLE = "Figure 33: Splitting time-ordered data"
ARIA = ("Four ways to split two years of daily data, each drawn as the series itself coloured by role. A "
        "random split scatters test days between training days. A chronological holdout cuts the timeline "
        "once into training, validation and test. Expanding window cross-validation trains on all history "
        "before each of four validation windows; sliding window cross-validation trains on the 300 days "
        "before each; a small gap separates training from validation. Each split shows its error.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 676, DATA, JS, L))
