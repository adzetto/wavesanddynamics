"""Figure 2 of the machine learning guide (stem image1): the five core task
mechanisms, each computed on a small simulated example from the guide's own
words (spam, a house price, customers, a machine's readings, tomorrow's
demand). Seeds fixed; every line, region and marker is the fitted model's.

(a) Classification: 40 emails, links per email and share of capital
    letters; logistic regression (scikit-learn, C = 1e6). The line is p = 0.5.
(b) Regression: the 14 house sales of Figure 8; least squares line.
(c) Clustering: 60 customers, visits a month and spend a visit, no labels;
    k-means with k = 3 (Lloyd's algorithm on features scaled by their axis
    ranges), every iteration kept, checked against scikit-learn's KMeans
    from the same start.
(d) Anomaly detection: 80 readings of a machine in normal running
    (temperature, vibration); a Gaussian fitted to them; a new reading is an
    anomaly if its squared Mahalanobis distance exceeds the chi-square 99 %
    point, 9.21 (the dashed ellipse).
(e) Forecasting: 70 days of demand from an additive Holt-Winters process
    (weekly season). The model is fitted to the first 56 days by least
    squares and forecasts days 57..70 with an 80 % band from the model's
    own forecast variance; the last 14 days, held back, are drawn as they
    come in.

The page runs each mechanism in turn: a new email is classified, a new house
priced, the clusters are found again from the start, new readings are
checked, and the forecast is made and met by the days that follow. Each has
a 6 s window of a 34 s round, paced so every step can be followed (30 Sep
2026: twice as slow as before; the timing is in the check file).

Run: python tools/numfig/mla_tasks.py [--look]
"""
import sys

import numpy as np
from scipy.optimize import minimize
from scipy.stats import chi2, norm
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression

import common
from mla_shared import LIB, house_data, report

NAME, STEM = "mla-tasks", "mla_tasks"
L = []
say = L.append
say("nf-mla-tasks: Figure 2, the five core task mechanisms")
say("")

# ------------------------------------------------------------------ (a) classification
rng = np.random.default_rng(8)
ham = np.c_[rng.normal(3, 1.4, 20), rng.normal(10, 5, 20)]
spam = np.c_[rng.normal(6.5, 1.8, 20), rng.normal(22, 7, 20)]
Xa = np.clip(np.r_[ham, spam], [0.2, 0.5], [11.8, 39])
ya = np.r_[np.zeros(20), np.ones(20)]
lr = LogisticRegression(C=1e6, max_iter=20000, tol=1e-10).fit(Xa, ya)
wa, ba = lr.coef_[0], lr.intercept_[0]
QA = [[8.2, 27.0], [3.4, 17.0]]                    # the new email: rests at the first, visits the second
pa = lr.predict_proba(QA)[:, 1]
say("(a) CLASSIFICATION: 20 + 20 emails (seed 8), logistic regression, C = 1e6")
say(f"  w = ({wa[0]:.5f}, {wa[1]:.5f}), b = {ba:.5f}; training accuracy {lr.score(Xa, ya):.3f}")
g = np.c_[np.ones(len(Xa)), Xa].T @ (ya - lr.predict_proba(Xa)[:, 1])
say(f"  CHECK: score equations [1 X]'(y - p) = ({g[0]:.1e}, {g[1]:.1e}, {g[2]:.1e}) at the optimum"
    f" (sum |x| = {np.abs(Xa).sum():.0f})")
say(f"  new email at {QA[0]}: p(spam) = {pa[0]:.3f}; at {QA[1]}: {pa[1]:.3f}")

# ------------------------------------------------------------------ (b) regression
xb, yb = house_data()
Sxx = ((xb - xb.mean()) ** 2).sum()
b1 = ((xb - xb.mean()) * (yb - yb.mean())).sum() / Sxx
b0 = yb.mean() - b1 * xb.mean()
QB = [2400.0, 1350.0]
say("")
say("(b) REGRESSION: the 14 house sales of Figure 8, least squares")
say(f"  price = {b0:.3f} k$ + {b1*1e3:.4f} $/ft^2 x area (as nf-mla-linreg)")
say(f"  new house {QB[0]:g} ft^2: {b0 + b1*QB[0]:.1f} k$; {QB[1]:g} ft^2: {b0 + b1*QB[1]:.1f} k$")

# ------------------------------------------------------------------ (c) clustering
rng = np.random.default_rng(7)
CC = np.array([[2.2, 85], [6.0, 30], [9.5, 70]])
SC = np.array([[0.7, 9], [0.9, 7], [0.8, 9]])
Xc = np.vstack([rng.normal(CC[k], SC[k], (20, 2)) for k in range(3)])
SCALE = np.array([12.0, 120.0])                    # the axes' ranges: both features count alike
Z = Xc / SCALE
init = np.random.default_rng(34).choice(len(Z), 3, replace=False)   # all three start in one group
cen = Z[init].copy()
hist, labs = [cen.copy()], []
for it in range(50):
    lab = ((Z[:, None, :] - cen[None]) ** 2).sum(-1).argmin(1)
    labs.append(lab)
    new = np.array([Z[lab == k].mean(0) for k in range(3)])
    hist.append(new.copy())
    if np.allclose(new, cen, atol=0, rtol=0):
        break
    cen = new
km = KMeans(n_clusters=3, init=Z[init], n_init=1, max_iter=100, tol=0, algorithm="lloyd").fit(Z)
say("")
say("(c) CLUSTERING: 60 customers in 3 groups (seed 7), no labels; k-means, k = 3, from 3 customers (seed 34)")
say(f"  converged after {len(labs)} assignment steps; start at customers {init.tolist()}")
say(f"  CHECK: final centres against sklearn KMeans from the same start: max |diff| ="
    f" {np.abs(np.sort(km.cluster_centers_, 0) - np.sort(hist[-1], 0)).max():.1e}")
truth = np.repeat(np.arange(3), 20)
agree = max(((labs[-1] == np.array(p)[truth]).mean()) for p in
            [(0, 1, 2), (0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1), (2, 1, 0)])
say(f"  CHECK: the groups found match the groups the data were drawn from: {agree*100:.0f} %")
inertia = [((Z - h[l]) ** 2).sum() for h, l in zip(hist[1:], labs)]
say(f"  within-cluster sum of squares by step (scaled units): {', '.join(f'{v:.4f}' for v in inertia)}")
cen_raw = [h * SCALE for h in hist]

# ------------------------------------------------------------------ (d) anomaly detection
rng = np.random.default_rng(11)
MU = np.array([60, 3.0])
COV = np.array([[16, 2.4], [2.4, 0.64]])
Xd = rng.multivariate_normal(MU, COV, 80)
md, Sd = Xd.mean(0), np.cov(Xd.T)
Si = np.linalg.inv(Sd)
THR = chi2.ppf(0.99, 2)
NEW = np.array([[57, 2.6], [66, 3.9], [52, 1.8], [62, 5.6], [74, 3.2], [63, 3.1]])
d2 = np.einsum("ij,jk,ik->i", NEW - md, Si, NEW - md)
ev, evec = np.linalg.eigh(Sd)
ang = np.linspace(0, 2 * np.pi, 181)
ell = md + (evec @ (np.sqrt(ev * THR)[:, None] * np.vstack([np.cos(ang), np.sin(ang)]))).T
say("")
say("(d) ANOMALY DETECTION: 80 normal readings (seed 11); Gaussian: mean"
    f" ({md[0]:.2f} C, {md[1]:.3f} mm/s)")
say(f"  threshold: squared Mahalanobis distance > chi2(2, 0.99) = {THR:.4f}")
inside = np.einsum("ij,jk,ik->i", Xd - md, Si, Xd - md) <= THR
say(f"  CHECK: training readings inside the ellipse {inside.sum()} of 80 (expected about 79.2)")
say(f"  CHECK: the drawn ellipse is the threshold: max |d2(ellipse) - thr| ="
    f" {np.abs(np.einsum('ij,jk,ik->i', ell - md, Si, ell - md) - THR).max():.1e}")
for p_, v in zip(NEW, d2):
    say(f"  new reading {p_[0]:g} C, {p_[1]:g} mm/s: d2 = {v:.2f} -> {'ANOMALY' if v > THR else 'normal'}")

# ------------------------------------------------------------------ (e) forecasting
M7, NH, NF = 7, 56, 14
WEEK = np.array([0, 4, 6, 5, 8, -9, -14.0])
WEEK -= WEEK.mean()
TRUE_P = (0.35, 0.1, 0.25)


def simulate(seed, n, al, be, ga, sig=4.0):
    rng_ = np.random.default_rng(seed)
    lv, tr, s = 100.0, 0.3, list(WEEK)
    out = []
    for t_ in range(n):
        e = rng_.normal(0, sig)
        out.append(lv + tr + s[t_ % M7] + e)
        lv, tr = lv + tr + al * e, tr + al * be * e
        s[t_ % M7] += ga * e
    return np.array(out)


def holt_winters(par, y, h=0):
    al, be, ga = par
    lv = y[:M7].mean()
    tr = (y[M7:2 * M7].mean() - y[:M7].mean()) / M7
    s = list(y[:M7] - lv)
    fit = []
    for t_ in range(len(y)):
        f = lv + tr + s[t_ % M7]
        fit.append(f)
        e = y[t_] - f
        lv, tr = lv + tr + al * e, tr + al * be * e
        s[t_ % M7] += ga * e
    fc = np.array([lv + k * tr + s[(len(y) + k - 1) % M7] for k in range(1, h + 1)])
    return np.array(fit), fc


ye = simulate(1, NH + NF, *TRUE_P)
yh = ye[:NH]
best = None
for x0 in ([0.3, 0.1, 0.2], [0.5, 0.3, 0.1], [0.1, 0.05, 0.4]):
    r = minimize(lambda p_: ((yh - holt_winters(p_, yh)[0])[M7:] ** 2).sum(), x0,
                 bounds=[(0.001, 0.999)] * 3, method="L-BFGS-B")
    if best is None or r.fun < best.fun:
        best = r
al, be, ga = best.x
fit, fc = holt_winters(best.x, yh, NF)
sig = np.sqrt(((yh - fit)[M7:] ** 2).sum() / (NH - M7 - 3))
cj = [al * (1 + j * be) + ga * (j % M7 == 0) for j in range(1, NF)]
var = sig ** 2 * (1 + np.r_[0, np.cumsum(np.square(cj))])
z80 = norm.ppf(0.9)
half = z80 * np.sqrt(var)
# Monte Carlo of the fitted model: the band's variance formula checked by simulation
rng = np.random.default_rng(0)
NS = 20000
paths = np.zeros((NS, NF))
# the fitted recursion's final state, then 20000 futures drawn from it
lv, tr = yh[:M7].mean(), (yh[M7:2 * M7].mean() - yh[:M7].mean()) / M7
s = list(yh[:M7] - lv)
for t_ in range(NH):
    e = yh[t_] - (lv + tr + s[t_ % M7])
    lv, tr = lv + tr + al * e, tr + al * be * e
    s[t_ % M7] += ga * e
E = rng.normal(0, sig, (NS, NF))
lvs, trs, ss = np.full(NS, lv), np.full(NS, tr), np.tile(np.array(s), (NS, 1))
for k in range(NF):
    idx = (NH + k) % M7
    f = lvs + trs + ss[:, idx]
    paths[:, k] = f + E[:, k]
    lvs, trs = lvs + trs + al * E[:, k], trs + al * be * E[:, k]
    ss[:, idx] += ga * E[:, k]
mc_sd = paths.std(0)
say("")
say(f"(e) FORECASTING: 70 days simulated from additive Holt-Winters (alpha, beta, gamma) = {TRUE_P},"
    " weekly season, noise sd 4 (seed 1)")
say(f"  fitted to days 1..56 by least squares: alpha {al:.3f}, beta {be:.3f}, gamma {ga:.3f}; residual sd {sig:.3f}")
say(f"  CHECK: forecast sd, formula vs 20000 simulated futures of the fitted model (h = 1, 7, 8, 14):"
    f" {np.sqrt(var[0]):.3f}/{mc_sd[0]:.3f}, {np.sqrt(var[6]):.3f}/{mc_sd[6]:.3f},"
    f" {np.sqrt(var[7]):.3f}/{mc_sd[7]:.3f}, {np.sqrt(var[13]):.3f}/{mc_sd[13]:.3f}")
say(f"  CHECK: mean of the simulated futures against the point forecast: max |diff| {np.abs(paths.mean(0) - fc).max():.3f}"
    f" (Monte Carlo error about {sig/np.sqrt(NS)*3:.3f})")
inb = int((np.abs(ye[NH:] - fc) <= half).sum())
say(f"  the 14 held-back days inside the 80 % band: {inb} of 14")
say("")
say("TIMING (30 Sep 2026, the client: slow Figure 2 down so each step can be followed): every step")
say("  about twice as slow, old values in brackets; the intro unchanged (readable by 0.8 s, all in by 1.2 s)")
say("  round 34 s (17 s): each mechanism a 6 s window (3 s) from 0.6 s, then 4 s at rest (2 s); poster 31.6 s (16.6 s)")
say("  (a), (b) the new case waits 0.5 s (0.25 s), glides to its second place with a 1.2 s spring (0.7 s),")
say("      stays 3 s (1.5 s) from leaving to coming back, and glides back; first motion at 1.1 s (0.85 s)")
say("  (c) grey, centres back to the start: 0.5 s (0.25 s), then a 0.4 s rest (0.2 s); a k-means step every")
say("      0.8 s (0.34 s): the colours change, and 0.2 s later (0.1 s) the centres glide 0.4 s (0.2 s) and rest")
say("  (d) the readings go in 0.4 s (0.2 s) and come back one by one, 0.76 s apart (0.38 s), each in 0.5 s (0.28 s)")
say("  (e) the forecast goes in 0.5 s (0.25 s) and is drawn forward in 1.8 s (0.9 s); the days that follow")
say("      come in one every 0.2 s (0.1 s)")
say("  5 Oct 2026: type 16 (ticks, labels, keys); the cluster centres an ink cross on a white halo (crimson is")
say("      each panel's new case); (c)'s status changes once the groups have gone grey; (d) a key for the new readings")
report(STEM, L)

DATA = {
    "a": {"x": Xa, "y": ya, "w": wa, "b": ba, "q": QA},
    "b": {"x": xb, "y": yb, "b0": b0, "b1": b1, "q": QB},
    "c": {"x": Xc, "cen": cen_raw, "lab": labs},
    "d": {"x": Xd, "ell": ell, "new": NEW, "an": (d2 > THR).astype(int)},
    "e": {"y": ye, "nh": NH, "fc": fc, "half": half},
}

JS = LIB + r"""
const D = DATA;
const PA = {x: 62, y: 62, w: 240, h: 178}, PB = {x: 392, y: 62, w: 240, h: 178}, PC = {x: 722, y: 62, w: 240, h: 178};
const PD = {x: 62, y: 362, w: 240, h: 178}, PE = {x: 392, y: 362, w: 570, h: 178};
/* each mechanism runs in its own window of a 34 s round, then rests; every
   step paced so it can be followed (30 Sep 2026: twice as slow as before) */
const R0 = .6, WIN = 6, ROUND = 34;
const POSTER_T = R0 + 5 * WIN + 1;
function win(k) { if (t < R0) return -1; const u = (t - R0) % ROUND - k * WIN; return u >= 0 && u < WIN ? u : -1; }
/* (a), (b): in its window the new case glides (1.2 s) to its second place, stays, and glides back */
const visit = u => u < 0 ? 0 : sp(u - .5, 1.2) - sp(u - 3.5, 1.2);

/* (a) classification */
function drawA() {
  sub('a', PA.x - 44, 34, 'classification', arrive(0));
  const g = axes({...PA, xlim: [0, 12], ylim: [0, 40], xticks: [0, 4, 8, 12], yticks: [0, 20, 40],
    xlabel: '\\rm{links per email}', ylabel: '\\rm{capital letters (%)}', ylabelGap: 38, tickSize: 16, progress: seg(0, .35)});
  const A = D.a, [w1, w2] = A.w, b = A.b;
  const yAt = x => -(b + w1 * x) / w2;
  g.inside(() => {
    const ra = arrive(.3);
    ctx.save(); ctx.globalAlpha = .7 * ra; ctx.fillStyle = C.steel; ctx.beginPath();
    ctx.moveTo(g.X(0), g.Y(yAt(0))); ctx.lineTo(g.X(12), g.Y(yAt(12))); ctx.lineTo(g.X(12), g.Y(60)); ctx.lineTo(g.X(0), g.Y(60));
    ctx.closePath(); ctx.fill(); ctx.restore();
    line([[g.X(0), g.Y(yAt(0))], [g.X(12), g.Y(yAt(12))]], {width: 2, progress: seg(.2, .36)});
    for (let i = 0; i < A.x.length; i++) mark(g.X(A.x[i][0]), g.Y(A.x[i][1]), A.y[i] ? 1 : 0, arrive(.04 + .2 * A.x[i][0] / 12), 4);
  });
  text('spam', g.X(11.6), g.Y(2.5), {size: 16, color: C.navy, align: 'right', alpha: arrive(.4)});
  text('not spam', g.X(.3), g.Y(22), {size: 16, color: C.body, alpha: arrive(.4)});
  // a new email: rests where it is spam, visits a place where it is not, comes back
  const s = visit(win(0));
  const qx = lerp(A.q[0][0], A.q[1][0], s), qy = lerp(A.q[0][1], A.q[1][1], s);
  const isSpam = w1 * qx + w2 * qy + b > 0, qa = arrive(.5);
  mark(g.X(qx), g.Y(qy), isSpam ? 1 : 0, qa, 5);
  ring(g.X(qx), g.Y(qy), 10, {alpha: qa});
  text('new email: ' + (isSpam ? 'spam' : 'not spam'), PA.x + PA.w, PA.y - 9,
    {size: 16, color: C.accent, align: 'right', alpha: qa});
}

/* (b) regression */
function drawB() {
  sub('b', PB.x - 44, 34, 'regression', arrive(.04));
  const g = axes({...PB, xlim: [800, 3100], ylim: [100, 600], xticks: [1000, 2000, 3000], yticks: [200, 400, 600],
    xlabel: '\\rm{floor area (ft}^{2}\\rm{)}', ylabel: '\\rm{price (k$)}', ylabelGap: 40, tickSize: 16, progress: seg(.03, .35)});
  const B = D.b, f = x => B.b0 + B.b1 * x;
  g.inside(() => {
    line([[g.X(800), g.Y(f(800))], [g.X(3100), g.Y(f(3100))]], {color: C.blue, width: 2.2, progress: seg(.22, .36)});
    for (let i = 0; i < B.x.length; i++) mark(g.X(B.x[i]), g.Y(B.y[i]), 1, arrive(.06 + .2 * (B.x[i] - 900) / 2000), 4);
  });
  const s = visit(win(1));
  const qx = lerp(B.q[0], B.q[1], s), qy = f(qx), qa = arrive(.55);
  line([[g.X(qx), PB.y + PB.h], [g.X(qx), g.Y(qy)]], {color: C.accent, width: 1.1, dash: [4, 3], alpha: qa});
  line([[PB.x, g.Y(qy)], [g.X(qx), g.Y(qy)]], {color: C.accent, width: 1.1, dash: [4, 3], alpha: qa});
  dot(g.X(qx), g.Y(qy), 5, {color: '#fff', fill: C.accent, width: 1.4, alpha: qa});
  text('new house: $' + Math.round(qy) + 'k', PB.x + PB.w, PB.y - 9, {size: 16, color: C.accent, align: 'right', alpha: qa});
}

/* (c) clustering: k-means, run again from its start in its window */
/* the groups as the family draws groups found in data (README): by k-means label a navy circle,
   a sky triangle and a blue square, white edged, so they part by shape for every reader; grey
   circles before they are labelled. It grows from 0.9 of its size as it arrives, as mark() does. */
const GRP = [[C.navy, 'circle'], [C.sky, 'triangle'], [C.blue, 'square']];
function gmark(x, y, k, a = 1, r = 4) {
  if (a <= 0) return;
  const [fill, kind] = GRP[k], rr = r * (.9 + .1 * Math.min(a, 1));
  ctx.save(); ctx.globalAlpha *= clamp(a); ctx.beginPath();
  if (kind === 'square') ctx.rect(x - rr * .88, y - rr * .88, rr * 1.76, rr * 1.76);
  else if (kind === 'triangle') { const q = rr * 1.18; ctx.moveTo(x, y - q * 1.15); ctx.lineTo(x + q * 1.05, y + q * .75); ctx.lineTo(x - q * 1.05, y + q * .75); ctx.closePath(); }
  else ctx.arc(x, y, rr, 0, 2 * Math.PI);
  ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = .9; ctx.stroke(); ctx.restore();
}
/* a cluster centre: an ink cross on a white halo, as Figure 15's key draws one (crimson is each
   panel's new case, not the centres) */
function cross(x, y, a) {
  for (const [c, w] of [['#fff', 5.4], [C.ink, 2.4]]) {
    line([[x - 7, y - 7], [x + 7, y + 7]], {color: c, width: w, alpha: a});
    line([[x - 7, y + 7], [x + 7, y - 7]], {color: c, width: w, alpha: a});
  }
}
function drawC() {
  sub('c', PC.x - 44, 34, 'clustering', arrive(.08));
  const g = axes({...PC, xlim: [0, 12], ylim: [0, 120], xticks: [0, 4, 8, 12], yticks: [0, 60, 120],
    xlabel: '\\rm{visits per month}', ylabel: '\\rm{spend per visit ($)}', ylabelGap: 40, tickSize: 16, progress: seg(.06, .35)});
  const Cd = D.c, n = Cd.x.length, NS = Cd.lab.length, u = win(2);
  // its window: grey, and the centres back to their start (.5 s), a rest, then a k-means step
  // every KS: each customer takes its nearest centre's colour, and .2 s later each centre
  // glides (.4 s) to its customers' mean, and rests
  const K0 = .9, KS = .8;
  let labIdx = NS - 1, grey = 0, cen = Cd.cen[NS], back = -1, note = 'three groups found', na = 1;
  // the status changes once the groups have gone grey, not while they are still coloured
  if (u >= 0 && u < K0) { back = clamp(u / .5); grey = back;
    if (u < .45) na = 1 - u / .45; else { note = 'start: no labels'; na = clamp((u - .45) / .2); } }
  else if (u >= K0) {
    const k = Math.min(NS - 1, Math.floor((u - K0) / KS)), p = sp(u - K0 - k * KS - .2, .4);
    labIdx = k;
    cen = Cd.cen[k].map((c, j) => [lerp(c[0], Cd.cen[k + 1][j][0], p), lerp(c[1], Cd.cen[k + 1][j][1], p)]);
    note = u < K0 + NS * KS + .4 ? 'k-means step ' + (k + 1) : 'three groups found';
  }
  g.inside(() => {
    for (let i = 0; i < n; i++) {
      const a = arrive(.08 + .2 * Cd.x[i][0] / 12), x = g.X(Cd.x[i][0]), y = g.Y(Cd.x[i][1]);
      if (grey > 0) mark(x, y, 2, a * grey, 4);
      if (grey < 1) gmark(x, y, Cd.lab[labIdx][i], a * (1 - grey), 4);
    }
    const ca = arrive(.45);
    if (back >= 0) {
      for (const c of Cd.cen[NS]) cross(g.X(c[0]), g.Y(c[1]), ca * (1 - back));
      for (const c of Cd.cen[0]) cross(g.X(c[0]), g.Y(c[1]), ca * back);
    } else for (const c of cen) cross(g.X(c[0]), g.Y(c[1]), ca);
  });
  text(note, PC.x + PC.w - 8, PC.y + 20, {size: 16, color: C.body, align: 'right', alpha: arrive(.5) * na});
}

/* (d) anomaly detection */
function drawD() {
  sub('d', PD.x - 44, 334, 'anomaly detection', arrive(.12));
  const g = axes({...PD, xlim: [44, 78], ylim: [0, 7], xticks: [45, 60, 75], yticks: [0, 3, 6],
    xlabel: '\\rm{temperature (°C)}', ylabel: '\\rm{vibration (mm/s)}', ylabelGap: 32, tickSize: 16, progress: seg(.09, .35)});
  const Dd = D.d, u = win(3);
  // its window: the new readings go (.4 s) and come back one by one, .76 s apart, each checked
  const seen = i => clamp(1 - u / .4) + sp(u - .7 - .76 * i, .5);
  g.inside(() => {
    for (let i = 0; i < Dd.x.length; i++) mark(g.X(Dd.x[i][0]), g.Y(Dd.x[i][1]), 4, arrive(.1 + .2 * (Dd.x[i][0] - 48) / 24), 3);
    line(Dd.ell.map(p => [g.X(p[0]), g.Y(p[1])]), {width: 1.3, dash: [5, 4], progress: seg(.3, .4)});
    Dd.new.forEach((p, i) => {
      let a = arrive(.55 + .03 * i);
      if (u >= 0) a = seen(i);
      const x = g.X(p[0]), y = g.Y(p[1]);
      if (Dd.an[i]) { mark(x, y, 3, a, 5); }
      else mark(x, y, 0, a, 4.6);
    });
  });
  // labels near the right frame end 8 units inside it, as 'spam' and 'three groups found' do
  const ea = arrive(.6), xin = PD.x + PD.w - 8;
  text('normal (99%)', xin, g.Y(1.25), {size: 16, color: C.body, align: 'right', alpha: ea});
  // what the larger open marks are: the readings being checked
  mark(PD.x + 16, PD.y + 16, 0, ea, 4.6); text('new reading', PD.x + 27, PD.y + 21, {size: 16, color: C.body, alpha: ea});
  Dd.new.forEach((p, i) => {
    if (!Dd.an[i]) return;
    const a = u >= 0 ? seen(i) : ea;
    const edge = p[0] > 70;                  // by the frame: below its mark, clear of the ellipse
    text('anomaly', edge ? xin : g.X(p[0]) + 10, g.Y(p[1]) + (edge ? 22 : 5), {size: 16, color: C.accent,
      align: edge ? 'right' : 'left', alpha: a});
  });
}

/* (e) forecasting */
function drawE() {
  sub('e', PE.x - 44, 334, 'forecasting', arrive(.16));
  const E = D.e, NH = E.nh, NT = E.y.length, NFc = NT - NH;
  const g = axes({...PE, xlim: [0, 71], ylim: [70, 140], xticks: [0, 14, 28, 42, 56, 70], yticks: [80, 100, 120, 140],
    xlabel: '\\rm{day}', ylabel: '\\rm{demand (units)}', ylabelGap: 40, tickSize: 16, progress: seg(.12, .35)});
  const u = win(4);
  // at rest: the forecast and the days that came; in its window they go (.5 s), the forecast is
  // drawn forward from today (1.8 s), and the days come in one by one, one every .2 s
  const out = u >= 0 && u < .5 ? 1 - u / .5 : 1;
  const fp = u < 0 ? seg(.4, .4) : u < .5 ? 1 : clamp((u - .6) / 1.8);
  const nIn = u < .5 ? NFc : Math.max(0, Math.floor((u - 2.6) / .2));
  const inA = u < 0 ? arrive(.8) : u < .5 ? out : 1;
  g.inside(() => {
    const m = NFc * fp;
    if (m > 0) {
      const up = [], dn = [];
      for (let k = 0; k < NFc && k <= m; k++) {
        up.push([g.X(NH + 1 + k), g.Y(E.fc[k] + E.half[k])]); dn.push([g.X(NH + 1 + k), g.Y(E.fc[k] - E.half[k])]);
      }
      ctx.save(); ctx.fillStyle = C.steel; ctx.globalAlpha = .95 * out; ctx.beginPath();
      [...up, ...dn.reverse()].forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath(); ctx.fill(); ctx.restore();
    }
    line(E.y.slice(0, NH).map((v, i) => [g.X(i + 1), g.Y(v)]), {color: C.navy, width: 1.8, progress: seg(.18, .4)});
    for (let i = 0; i < NH; i++) mark(g.X(i + 1), g.Y(E.y[i]), 1, seg(.18 + .4 * i / NH, .1), 2.4);
    line(E.fc.map((v, k) => [g.X(NH + 1 + k), g.Y(v)]), {color: C.accent, width: 2.2, progress: fp, alpha: out});
    for (let k = 0; k < Math.min(nIn, NFc); k++) mark(g.X(NH + 1 + k), g.Y(E.y[NH + k]), 0, inA, 3.2);
  });
  const ta = arrive(.5), xt = g.X(NH + .5);
  line([[xt, PE.y], [xt, PE.y + PE.h]], {color: C.guide, width: 1, dash: [5, 4], alpha: ta});
  text('today', xt - 6, PE.y + PE.h - 10, {size: 16, color: C.body, align: 'right', alpha: ta});
  text('history', g.X(3), PE.y + 20, {size: 16, color: C.navy, alpha: ta});
  text('forecast', g.X(70), PE.y + 20, {size: 16, color: C.accent, align: 'right', alpha: ta});
  // a key along the top: the band, and the days that came after today
  const kx = g.X(15), ky = PE.y + 20;
  box(kx, ky - 12, 14, 13, {fill: C.steel, alpha: ta});
  const kx2 = kx + 22 + text('80% band', kx + 20, ky, {size: 16, color: C.body, alpha: ta}) + 18;
  mark(kx2 + 4, ky - 5, 0, ta, 3.2);
  text('what happened', kx2 + 14, ky, {size: 16, color: C.body, alpha: ta});
}

function draw() {
  drawA(); drawB(); drawC(); drawD(); drawE();
  // the parameter line: words in text (math would set the hyphen as a minus), k in math
  const fa = arrive(.9), fo = {size: 15, color: C.muted, alpha: fa};
  let fx = 18 + text('simulated data, fixed seeds; k-means with ', 18, H - 14, fo);
  fx += math('k = 3', fx, H - 14, fo);
  text('; anomaly beyond 99%', fx, H - 14, fo);
}
boot();
"""

TITLE = ("Figure 2: The five core task mechanisms every ML model is built from: Classification, "
         "Regression, Clustering, Anomaly Detection, and Forecasting")
ARIA = ('Five small plots, each a model fitted to simulated data: a line separating spam from other '
        'emails, a least squares line through house prices, three groups of customers found by k-means, '
        'an ellipse of normal machine readings with two anomalies outside it, and a demand history '
        'extended fourteen days with a forecast band. In turn, each model is shown at work on something new.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 640, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.4, 0.9, 3.1, 9.1, 13.3, 14.0, 15.5, 21.1, 26.1, 28.6]))
