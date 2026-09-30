"""Figure 12 of the machine learning guide (stem image9): gradient boosting.

Model: 50 points y = f(x) + noise, f(x) = 1.3 sin(1.05 x) + 0.3 x - 1.5 the
true pattern (dashed), noise sd 0.4 (seed fixed). Gradient boosting with
squared loss: F_0 = mean(y); for m = 1, 2, ...: the residuals
r = y - F_{m-1}(x) are fitted by a regression tree h_m of depth 2 (scikit-
learn, squared error), and F_m = F_{m-1} + nu h_m with nu = 0.1. Checked
against scikit-learn's GradientBoostingRegressor round by round.

The page evaluates the trees itself: F at any moment is F_0 plus nu times
the trees added so far (the tree being added enters in proportion), so the
sum in (a), the residual stems in (b) and the marker on (c) all follow from
the same 51 trees every frame. Rounds 1 to 5 play one by one; 6 to 50 run
on quickly; the next tree is shown fitted to what is left; then it rewinds.

Run: python tools/numfig/mla_boost.py [--look]
"""
import sys

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor

import common
from mla_shared import LIB, report

NAME, STEM = "mla-boost", "mla_boost"
SEED, N, SIGMA, NU, DEPTH, M = 1, 50, 0.4, 0.1, 2, 50


def truth(x):
    return 1.3 * np.sin(1.05 * x) + 0.3 * x - 1.5


rng = np.random.default_rng(SEED)
x = np.sort(rng.uniform(0, 10, N))
y = truth(x) + rng.normal(0, SIGMA, N)
xg = np.linspace(0, 10, 4001)

F0 = y.mean()
F, Fg = np.full(N, F0), np.full(xg.size, F0)
trees, stages, gap, train = [], [F.copy()], [np.sqrt(((Fg - truth(xg)) ** 2).mean())], [np.sqrt(((y - F) ** 2).mean())]
first_split = None
for m in range(1, M + 2):                     # tree M + 1 is the one shown after the last round
    r = y - F
    t = DecisionTreeRegressor(max_depth=DEPTH, criterion="squared_error", random_state=0).fit(x[:, None], r)
    th = np.sort(t.tree_.threshold[t.tree_.feature >= 0])
    mids = np.r_[th[0] - 1, (th[:-1] + th[1:]) / 2, th[-1] + 1] if len(th) else np.array([5.0])
    vals = t.predict(mids[:, None])
    trees.append({"e": th, "v": vals})
    if m == 1:
        first_split = (t, r.copy())
    if m <= M:
        F = F + NU * t.predict(x[:, None])
        Fg = Fg + NU * t.predict(xg[:, None])
        stages.append(F.copy())
        gap.append(np.sqrt(((Fg - truth(xg)) ** 2).mean()))
        train.append(np.sqrt(((y - F) ** 2).mean()))
gap, train = np.array(gap), np.array(train)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-boost: Figure 12, gradient boosting on residuals")
say("")
say("DATA")
say(f"  {N} points, x ~ U(0, 10) sorted, y = 1.3 sin(1.05 x) + 0.3 x - 1.5 + e, e ~ N(0, {SIGMA}^2), seed {SEED}")
say("MODEL")
say(f"  F_0 = mean(y) = {F0:.6f}; trees of depth {DEPTH} on the residuals; learning rate nu = {NU}; {M} rounds")
say("")
say("CHECK 1: against scikit-learn GradientBoostingRegressor (same loss, depth, rate, criterion)")
sk = GradientBoostingRegressor(loss="squared_error", learning_rate=NU, n_estimators=M, max_depth=DEPTH,
                               criterion="squared_error", random_state=0).fit(x[:, None], y)
worst = max(np.abs(p - s).max() for p, s in zip(sk.staged_predict(x[:, None]), stages[1:]))
say(f"  max |F_m(x_i) ours - staged_predict| over m = 1..{M} and all points: {worst:.1e}")
say(f"  sklearn init {sk.init_.constant_[0][0]:.6f} = mean(y) {F0:.6f}")
say("")
say("CHECK 2: the first tree is the best depth 2 split of the residuals (brute force)")
t1, r1 = first_split
xs = x
best = (np.inf, None)
cuts = (xs[:-1] + xs[1:]) / 2


def sse(v):
    return ((v - v.mean()) ** 2).sum() if len(v) else 0.0


for c in cuts:
    L_, R_ = r1[xs <= c], r1[xs > c]
    tot = sse(L_) + sse(R_)
    if tot < best[0]:
        best = (tot, c)
root = t1.tree_.threshold[0]
say(f"  root split: tree {root:.6f}, brute force {best[1]:.6f} (sse {best[0]:.6f})")
say(f"  leaf values are the mean residual in each leaf: max |leaf - mean| = "
    f"{max(abs(v - r1[(x > (trees[0]['e'][k-1] if k else -1e9)) & (x <= (trees[0]['e'][k] if k < len(trees[0]['e']) else 1e9))].mean()) for k, v in enumerate(trees[0]['v'])):.1e}")
say("")
say("CHECK 3: the training error never rises (squared loss, exact leaf means, nu <= 1)")
say(f"  RMS training error: m = 0: {train[0]:.4f}, 1: {train[1]:.4f}, 5: {train[5]:.4f}, 15: {train[15]:.4f},"
    f" 50: {train[50]:.4f}; monotone: {bool(np.all(np.diff(train) <= 1e-12))}")
say("")
say("CHECK 4: the sum of trees approaches the true pattern (RMS gap on a 4001 point grid)")
say(f"  m = 0: {gap[0]:.4f}, 1: {gap[1]:.4f}, 5: {gap[5]:.4f}, 15: {gap[15]:.4f}, 50: {gap[50]:.4f};"
    f" smallest at m = {int(gap.argmin())} ({gap.min():.4f})")
say(f"  noise sd {SIGMA}: the gap after {M} rounds is {gap[M]/SIGMA:.2f} of it")
say("")
say("PAGE: rounds 1 to 5 one by one, 6 to 50 run on, tree 51 shown on the last residuals, rewind")
report(STEM, L)

DATA = {"x": x, "y": y, "F0": F0, "nu": NU, "M": M,
        "trees": [{"e": tr["e"], "v": tr["v"]} for tr in trees],
        "gap": gap, "tx": np.linspace(0, 10, 201), "ty": truth(np.linspace(0, 10, 201))}

JS = LIB + r"""
const D = DATA, n = D.x.length, NU = D.nu, M = D.M, TR = D.trees;
const PA = {x: 84, y: 62, w: 600, h: 246}, PB = {x: 84, y: 392, w: 600, h: 180}, PC = {x: 792, y: 62, w: 176, h: 246};
/* the cumulative split points of trees 1..m, for drawing the sum as exact steps */
const CUTS = [[]];
for (let m = 1; m <= TR.length; m++) CUTS.push([...new Set([...CUTS[m - 1], ...TR[m - 1].e])].sort((a, b) => a - b));
const hk = (k, x) => { const T = TR[k - 1]; let i = 0; while (i < T.e.length && x > T.e[i]) i++; return T.v[i]; };
function Fs(s, x) {                        // the sum after s trees (the last one entering in proportion)
  let v = D.F0; const m = Math.floor(s);
  for (let k = 1; k <= m; k++) v += NU * hk(k, x);
  if (s > m && m < TR.length) v += NU * (s - m) * hk(m + 1, x);
  return v;
}
function sumPts(s, X, Y) {                 // F_s as a step line over [0, 10]
  const c = CUTS[Math.min(TR.length, Math.ceil(s))], e = [0, ...c.filter(v => v > 0 && v < 10), 10], p = [];
  for (let i = 0; i < e.length - 1; i++) { const v = Fs(s, (e[i] + e[i + 1]) / 2); p.push([X(e[i]), Y(v)], [X(e[i + 1]), Y(v)]); }
  return p;
}
function treePts(k, X, Y, sc = 1) {
  const T = TR[k - 1], e = [0, ...T.e.filter(v => v > 0 && v < 10), 10], p = [];
  for (let i = 0; i < e.length - 1; i++) { const v = sc * hk(k, (e[i] + e[i + 1]) / 2); p.push([X(e[i]), Y(v)], [X(e[i + 1]), Y(v)]); }
  return p;
}

/* the boosting clock: s trees added so far, the tree on show in (b), its draw progress */
const T1 = .75, RD = 1.25, NR = 5, FF = 4.0, END = 3.0, RW = 1.1, REST = .5;
const LOOP = NR * RD + FF + END + RW + REST;
function clockAt() {
  if (t < T1) return {s: 0, k: 1, draw: 0, show: 0, loop: 0};
  const tau = (t - T1) % LOOP, loop = Math.floor((t - T1) / LOOP);
  if (tau < NR * RD) {                     // rounds 1..5: draw tree k, then add it
    const k = Math.floor(tau / RD) + 1, u = tau - (k - 1) * RD;
    const add = sp(u - .5, .5);
    return {s: k - 1 + add, k, draw: easeInOut(clamp(u / .38)), show: 1 - clamp((u - 1.0) / .2), loop};
  }
  let u = tau - NR * RD;
  if (u < FF) return {s: NR + (M - NR) * easeInOut(u / FF), k: 0, draw: 0, show: 0, loop};
  u -= FF;
  if (u < END) return {s: M, k: M + 1, draw: easeInOut(clamp(u / .38)), show: 1, loop};
  u -= END;
  if (u < RW) return {s: M * (1 - sp(u, .8)), k: M + 1, draw: 1, show: 1 - clamp(u / .25), loop};
  return {s: 0, k: 1, draw: 0, show: 0, loop};
}
const POSTER_T = T1 + NR * RD + FF + 1.6;

function draw() {
  const ck = clockAt(), s = ck.s;
  /* (a) the sum of trees */
  sub('a', 18, 34, 'sum of trees so far', arrive(0));
  const g = axes({...PA, xlim: [0, 10], ylim: [-3.5, 2.5], xticks: [0, 2, 4, 6, 8, 10], yticks: [-3, -2, -1, 0, 1, 2],
    xlabel: 'x', ylabel: 'y', ylabelGap: 38, progress: seg(0, .35)});
  g.inside(() => {
    line(D.tx.map((v, i) => [g.X(v), g.Y(D.ty[i])]), {color: C.ink, width: 1.6, dash: [7, 5], progress: seg(.16, .4)});
    // earlier sums, left behind as the rounds go on
    for (const [m, lab] of [[1, '1'], [5, '5'], [15, '15']]) {
      const a = s > m ? .9 * clamp((s - m) * 3) : 0;
      if (a > 0) line(sumPts(m, g.X, g.Y), {color: C.mist, width: 1.5, alpha: a});
    }
    line(sumPts(s, g.X, g.Y), {color: C.navy, width: 2.5, progress: seg(.3, .36)});
    for (let i = 0; i < n; i++) mark(g.X(D.x[i]), g.Y(D.y[i]), 4, arrive(.04 + .26 * D.x[i] / 10), 3.9);
  });
  const na = Math.floor(s + 1e-6);
  math('\\rm{after}\\ ' + na + '\\ \\rm{tree' + (na === 1 ? '' : 's') + '}', PA.x + PA.w - 12, PA.y + PA.h - 14,
    {size: 17, align: 'right', alpha: arrive(.5)});

  /* (b) the residuals, and the next tree fitted to them */
  sub('b', 18, PB.y - 28, 'residuals and the next tree', arrive(.1));
  const h = axes({...PB, xlim: [0, 10], ylim: [-2.5, 2.5], xticks: [0, 2, 4, 6, 8, 10], yticks: [-2, 0, 2],
    xlabel: 'x', ylabel: '\\rm{residual}', ylabelGap: 38, progress: seg(.06, .35)});
  h.inside(() => {
    line([[PB.x, h.Y(0)], [PB.x + PB.w, h.Y(0)]], {color: C.rule, width: 1});
    for (let i = 0; i < n; i++) {
      const r = D.y[i] - Fs(s, D.x[i]), a = seg(.45 + .2 * D.x[i] / 10, .25);
      line([[h.X(D.x[i]), h.Y(0)], [h.X(D.x[i]), h.Y(r)]], {color: C.sky, width: 1.4, progress: a});
      if (a > .5) mark(h.X(D.x[i]), h.Y(r), 4, a, 3.2);
    }
    if (ck.k && ck.show > 0) line(treePts(ck.k, h.X, h.Y), {color: C.accent, width: 2.4, progress: ck.draw, alpha: ck.show});
  });
  const ta = ck.k ? ck.show * clamp(ck.draw * 2) : 0;
  if (ta > 0) {
    math('\\rm{tree}\\ ' + ck.k + '\\rm{, added} \\times ' + NU, PB.x + PB.w - 12, PB.y + PB.h - 12,
      {size: 16, align: 'right', color: C.accent, alpha: ta});
  }

  /* (c) how far the sum is from the true pattern */
  sub('c', PC.x - 62, 34, 'distance to the true pattern', arrive(.12));
  const q = axes({...PC, xlim: [0, 50], ylim: [0, 1.4], xticks: [0, 25, 50], yticks: [0, .5, 1],
    yfmt: v => v === 0 ? '0' : v.toFixed(1), xlabel: '\\rm{trees}', ylabel: '\\rm{RMS distance}', ylabelGap: 40,
    progress: seg(.08, .35)});
  q.inside(() => line(D.gap.map((v, i) => [q.X(i), q.Y(v)]), {color: C.navy, width: 2.2, progress: seg(.2, .42)}));
  const gi = Math.min(M, Math.floor(s)), gv = lerp(D.gap[gi], D.gap[Math.min(M, gi + 1)], s - gi);
  dot(q.X(s), q.Y(gv), 5.5, {color: '#fff', fill: C.accent, width: 1.4, alpha: arrive(.55)});

  legend(PC.x - 62, PB.y - 10, [
    [(x, y) => mark(x, y + 1, 4, 1, 3.9), 'data'],
    [(x, y) => line([[x - 13, y + 1], [x + 13, y + 1]], {width: 1.6, dash: [7, 5]}), 'true pattern'],
    [(x, y) => line([[x - 13, y + 1], [x + 13, y + 1]], {color: C.navy, width: 2.5}), 'sum of trees'],
    [(x, y) => line([[x - 13, y + 1], [x + 13, y + 1]], {color: C.mist, width: 1.5}), 'after 1, 5, 15 trees'],
    [(x, y) => line([[x, y - 8], [x, y + 9]], {color: C.sky, width: 1.4}), 'residual'],
    [(x, y) => line([[x - 13, y + 5], [x - 3, y + 5], [x - 3, y - 4], [x + 13, y - 4]], {color: C.accent, width: 2.4}), 'next tree'],
  ], arrive(.65), 238);
  text('50 simulated points, noise sd 0.4; depth 2 regression trees, learning rate 0.1, 50 rounds', 18, H - 14,
       {size: 14, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = ("Figure 12: Gradient boosting: each new shallow tree is trained only on the residual errors "
         "left by the trees before it, and its prediction is added in with a small weight")
ARIA = ("Fifty noisy points around a dashed true pattern. Round by round a depth two tree is fitted "
        "to the residuals, drawn as stems below, and a tenth of its prediction is added to the sum "
        "of trees, a step curve that moves toward the dashed line; a small plot shows the gap "
        "between them shrinking over fifty rounds.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 660, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.5, 1.2, 1.9, 3.0, 8.0, 12.0]))
