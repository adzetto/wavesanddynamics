"""Figure 4 of the machine learning guide (stem image2): the five data
cleaning steps of section 3.3, each on a small worked example, every number
computed.

(a) Imputation: a glucose column with one value missing is filled with the
    median of the six observed values, and a missing-value indicator column
    is added (the guide's words).
(b) Inconsistent formats and units: three records with dates in three
    formats and heights in cm, inches, feet and inches become one date
    format (ISO 8601) and one unit (1 in = 2.54 cm exactly).
(c) Outlier handling: fourteen ages; Tukey's fences (Q1 - 1.5 IQR, Q3 +
    1.5 IQR, numpy's linear quartiles) flag 96 and 430; investigated, 96 is
    a real, very old patient and stays; 430 is a typing slip for 43 and is
    corrected.
(d) Normalization and standardization: three features of six patients on
    their own scales become z-scores, z = (x - mean) / sd (population sd,
    as scikit-learn's StandardScaler).
(e) Class imbalance handling: 196 normal transactions and 4 frauds (98 % and
    2 %); SMOTE makes 192 synthetic frauds, each on the segment from a fraud
    to one of its 3 nearest fraud neighbors at a random fraction (seeded).

The page (1000 x 670, three panels over two) shows the cleaned data and replays each
step in turn: what the step made fades out (0.3 s), then it is made again.

Run: python tools/numfig/mla_cleaning.py [--look]
"""
import datetime as dt
import sys

import numpy as np
from sklearn.preprocessing import StandardScaler

import common
from mla_shared import LIB, report

NAME, STEM = "mla-cleaning", "mla_cleaning"
L = []
say = L.append
say("nf-mla-cleaning: Figure 4, the five data cleaning steps")
say("")

# (a) imputation
GLU = [98, 142, None, 115, 104, 131, 88]
obs = np.array([v for v in GLU if v is not None], float)
MED = float(np.median(obs))
srt = np.sort(obs)
say("(a) IMPUTATION: glucose (mg/dL) " + ", ".join("?" if v is None else str(v) for v in GLU))
say(f"  observed sorted {srt.tolist()}; median = ({srt[2]:g} + {srt[3]:g}) / 2 = {MED:g} (numpy {np.median(obs):g});"
    f" mean {obs.mean():g}")

# (b) formats and units
RAW = [("12/05/2024", "172 cm"), ("2024-12-09", "68 in"), ("11 Dec 2024", "5 ft 9 in")]
FMT = ["%m/%d/%Y", "%Y-%m-%d", "%d %b %Y"]
dates = [dt.datetime.strptime(d, f).date().isoformat() for (d, _), f in zip(RAW, FMT)]
cm = [172.0, 68 * 2.54, (5 * 12 + 9) * 2.54]
say("")
say("(b) FORMATS AND UNITS: dates parsed as US month/day, ISO, day month-name; 1 in = 2.54 cm")
for (d, h), iso, c in zip(RAW, dates, cm):
    say(f"  {d:12s} -> {iso};  {h:10s} -> {c:.2f} cm")

# (c) outliers
AGES = np.array([34, 45, 29, 51, 38, 62, 47, 55, 41, 430, 58, 36, 96, 49])
q1, q3 = np.percentile(AGES, [25, 75])
iqr = q3 - q1
lo_f, hi_f = q1 - 1.5 * iqr, q3 + 1.5 * iqr
inl = AGES[(AGES >= lo_f) & (AGES <= hi_f)]
say("")
say(f"(c) OUTLIERS: ages {AGES.tolist()}")
say(f"  Q1 {q1:g}, median {np.median(AGES):g}, Q3 {q3:g}, IQR {iqr:g}; fences {lo_f:g} and {hi_f:g}")
say(f"  outside: {AGES[(AGES < lo_f) | (AGES > hi_f)].tolist()}; whiskers to {inl.min()} and {inl.max()}")
say("  investigated: 96 real (kept); 430 a slip for 43 (corrected)")

# (d) standardization
FEAT = {"age": [23, 37, 45, 52, 61, 74], "income": [28, 54, 61, 95, 120, 210], "glucose": [82, 96, 104, 118, 141, 187]}
M = np.array(list(FEAT.values()), float).T                 # 6 patients x 3 features
Zs = StandardScaler().fit_transform(M)
Zm = (M - M.mean(0)) / M.std(0)
say("")
say("(d) STANDARDIZATION: z = (x - mean) / sd, sd with ddof 0")
for k, (n, v) in enumerate(FEAT.items()):
    say(f"  {n:8s} mean {M[:, k].mean():8.3f}, sd {M[:, k].std():8.3f}; z = {', '.join(f'{z:+.2f}' for z in Zm[:, k])}")
say(f"  CHECK: against StandardScaler, max |diff| = {np.abs(Zs - Zm).max():.1e}; each z column mean"
    f" {np.abs(Zm.mean(0)).max():.1e}, sd {Zm.std(0).round(12).tolist()}")

# (e) SMOTE
rng = np.random.default_rng(21)
MAJ = rng.normal([0, 0], [1.0, 0.8], (196, 2))
MIN = np.array([[1.5, 1.7], [2.9, 0.3], [2.1, 0.8], [3.7, 1.9]])
K = 3
d = ((MIN[:, None] - MIN[None]) ** 2).sum(-1)
nn = np.argsort(d, 1)[:, 1:K + 1]
NS = 196 - 4
src = rng.integers(0, 4, NS)
nb = nn[src, rng.integers(0, K, NS)]
lam = rng.random(NS)
SYN = MIN[src] + lam[:, None] * (MIN[nb] - MIN[src])
say("")
say(f"(e) SMOTE: 196 normal ~ N(0, diag(1, 0.64)) (seed 21), 4 frauds; k = {K}; {NS} synthetic frauds")
cr = np.abs((SYN - MIN[src])[:, 0] * (MIN[nb] - MIN[src])[:, 1] - (SYN - MIN[src])[:, 1] * (MIN[nb] - MIN[src])[:, 0])
say(f"  CHECK: every synthetic point lies on its segment: max |cross product| {cr.max():.1e}, fraction in"
    f" [{lam.min():.3f}, {lam.max():.3f}]")
say(f"  CHECK: classes after SMOTE: normal 196, fraud {4 + NS} (50 % : 50 %)")
say("")
say("PAGE (1000 x 670, 900 before 5 Oct 2026): (a), (b), (c) on the first row, (d) and (e) on the second. Each step")
say("  replays in its own 3 s window of a 17 s round: what it made fades out in 0.3 s, then it is made again, step")
say("  by step (no part vanishes at once); the first round opens on the gap ('?'), not on the filled answer. (c)'s")
say("  ages are a dot plot (an age whose mark would meet its neighbor's sits a level up); the slip goes out at 430")
say("  and comes in at 43. (e) has axes: two standardized transaction features.")
report(STEM, L)

DATA = {
    "a": {"glu": [(-1 if v is None else v) for v in GLU], "med": MED, "mid": [float(srt[2]), float(srt[3])]},
    "b": {"raw": RAW, "iso": dates, "cm": cm},
    "c": {"ages": AGES, "q": [q1, float(np.median(AGES)), q3], "f": [lo_f, hi_f], "w": [int(inl.min()), int(inl.max())]},
    "d": {"names": ["age (years)", "income (k$)", "glucose (mg/dL)"], "x": M.T, "z": Zm.T,
          "lim": [[20, 80], [0, 240], [60, 200]], "mean": M.mean(0), "sd": M.std(0)},
    "e": {"maj": MAJ, "min": MIN, "syn": SYN, "src": src},
}

JS = LIB + r"""
const D = DATA;
/* three panels on the first row, two on the second; each step replays in its own window of a
   17 s round: what it made fades out (FD), then it is made again, step by step */
const COL = [18, 344, 670], ROW = [34, 368];
const R0 = .6, WIN = 3, ROUND = 17, FD = .3;
const POSTER_T = R0 + 5 * WIN + 1;
function win(k) { if (t < R0) return -1; const u = (t - R0) % ROUND - k * WIN; return u >= 0 && u < WIN ? u : -1; }
/* in its window: 1 at rest, going out over the first FD s, back from a (a spring of d s) */
const again = (u, a, d = .3) => u < 0 ? 1 : u < FD ? 1 - u / FD : sp(u - a, d);
function ticksUnder(X, vals, y, a) {         // a number line's ticks under it, and their numbers
  for (const v of vals) { line([[X(v), y], [X(v), y + 5]], {width: 1.1, alpha: a});
    text(String(v), X(v), y + 22, {size: 16, align: 'center', alpha: a}); }
}

/* (a) imputation: the glucose column with its gap, the median of what was observed */
function drawA() {
  // the first time round it opens on the gap ('?'), not on the answer, and goes on from there
  const u = t < R0 + .45 ? .45 : win(0), A = D.a, x0 = COL[0];
  sub('a', x0, ROW[0], 'imputation', arrive(0));
  const CX = [x0 + 42, x0 + 148, x0 + 254], top = ROW[0] + 18, RH = 21, r0 = top + 46, aa = arrive(.05);
  rule(x0 + 6, x0 + 296, top, {width: 1.3, alpha: aa});
  ['patient', 'glucose (mg/dL)', 'was missing'].forEach((h, c) =>
    text(h, CX[c], top + 18, {size: 16, color: C.body, align: 'center', alpha: aa}));
  rule(x0 + 6, x0 + 296, top + 26, {alpha: aa});
  // the empty cell, one thing at a time: the value gives way to '?'; once the median is marked,
  // '?' goes and the median slides in from the side; then the new column is filled
  const qa = u < 0 ? 0 : clamp((u - FD) / .15) * (1 - clamp((u - 1.45) / .15));
  const vin = u < 0 ? 1 : u < FD ? 1 - u / FD : sp(u - 1.7, .3), vdx = u < FD ? 0 : 14 * (1 - vin);
  const ind = again(u, 2.1);
  A.glu.forEach((v, k) => {
    const y = r0 + k * RH, a = aa;
    text(String(k + 1), CX[0], y, {size: 16, align: 'center', alpha: a});
    if (v >= 0) text(String(v), CX[1], y, {size: 16, align: 'center', alpha: a});
    else {
      box(CX[1] - 28, y - 16, 56, 22, {fill: C.wash, alpha: a});
      text('?', CX[1], y, {size: 17, bold: true, color: C.accent, align: 'center', alpha: a * qa});
      text(A.med.toFixed(1), CX[1] + vdx, y, {size: 16, bold: true, color: C.accent, align: 'center', alpha: a * vin});
    }
    text(v >= 0 ? '0' : '1', CX[2], y, {size: 16, align: 'center', alpha: a * ind, color: v >= 0 ? C.ink : C.accent, bold: v < 0});
  });
  rule(x0 + 6, x0 + 296, r0 + 6 * RH + 8, {width: 1.3, alpha: aa});
  // the six observed values in order, and their median
  const SX = v => x0 + 86 + (v - 80) / 70 * 200, sy = ROW[0] + 266, sa = arrive(.12);
  text('observed', x0 + 6, sy + 5, {size: 16, color: C.body, alpha: sa});
  line([[SX(80), sy], [SX(150), sy]], {width: 1.2, alpha: sa});
  ticksUnder(SX, [80, 100, 120, 140], sy, sa);
  A.glu.forEach(v => { if (v >= 0) mark(SX(v), sy - 12, 1, arrive(.15 + .2 * (v - 80) / 70), 4.4); });
  const ma = u < 0 ? arrive(.4) : u < FD ? 1 - u / FD : clamp((u - .85) / .25);
  for (const v of A.mid) ring(SX(v), sy - 12, 9, {alpha: u < FD ? 0 : clamp((u - .5) / .2) * (1 - clamp((u - 1.45) / .2))});
  line([[SX(A.med), sy - 30], [SX(A.med), sy]], {color: C.accent, width: 2, alpha: ma});
  text('median ' + A.med.toFixed(1), SX(A.med), sy - 36, {size: 16, color: C.accent, align: 'center', alpha: ma});
}

/* (b) formats and units: the records as they came, and in one format and one unit */
function drawB() {
  const u = win(1), B = D.b, x0 = COL[1];
  sub('b', x0, ROW[0], 'inconsistent formats and units', arrive(.04));
  const DX = x0 + 12, HX = x0 + 150, aa = arrive(.08), L = x0 + 4, R = x0 + 248;
  const table = (top, head, rows, a, rowA) => {
    rule(L, R, top, {width: 1.3, alpha: a});
    text(head[0], DX, top + 18, {size: 16, color: C.body, alpha: a}); text(head[1], HX, top + 18, {size: 16, color: C.body, alpha: a});
    rule(L, R, top + 26, {alpha: a});
    rows.forEach((r, i) => { const ra = a * rowA(i);
      text(r[0], DX, top + 46 + 22 * i, {size: 16, alpha: ra}); text(r[1], HX, top + 46 + 22 * i, {size: 16, alpha: ra}); });
    rule(L, R, top + 100, {width: 1.3, alpha: a});
  };
  const T1 = ROW[0] + 18, T2 = ROW[0] + 168;
  table(T1, ['visit date', 'height'], B.raw, aa, () => 1);
  const conv = i => again(u, .6 + .55 * i);
  table(T2, ['visit date', 'height (cm)'], B.iso.map((d, i) => [d, B.cm[i].toFixed(1)]), aa, conv);
  const ar = arrive(.12), ax = x0 + 60;
  arrow(ax, T1 + 110, ax, T2 - 10, {width: 1.3, head: 9, alpha: ar});
  text('one date format, one unit', ax + 16, (T1 + 100 + T2) / 2 + 6, {size: 16, color: C.body, alpha: ar});
  // in its window: the record being converted, on both sides, in the accent
  if (u >= 0) for (let i = 0; i < 3; i++) {
    const h = clamp((u - .45 - .55 * i) / .15) * (1 - clamp((u - .95 - .55 * i) / .15));
    if (h > 0) for (const T of [T1, T2]) box(L, T + 30 + 22 * i, R - L, 22, {stroke: C.accent, width: 1.4, alpha: h});
  }
}

/* (c) outlier handling, on a broken axis. The ages as a dot plot: an age whose mark would meet
   its neighbor's sits a level up (the levels of the ages as corrected, 43 for the slip) */
const CA0 = COL[2] + 20, CA1 = COL[2] + 216, CB0 = COL[2] + 250, CB1 = COL[2] + 300, CR = 4.2;
const CX_ = v => v <= 100 ? CA0 + (v - 20) / 80 * (CA1 - CA0) : CB0 + (v - 420) / 20 * (CB1 - CB0);
const CLV = (() => {
  const fin = D.c.ages.map(v => v === 430 ? 43 : v), idx = fin.map((_, i) => i).sort((i, j) => fin[i] - fin[j]);
  const lv = new Array(fin.length).fill(0), last = [];
  for (const i of idx) { let l = 0; while (last[l] !== undefined && CX_(fin[i]) - last[l] < 2 * CR + 1.5) l++; lv[i] = l; last[l] = CX_(fin[i]); }
  return lv;
})();
function drawC() {
  const u = win(2), Cc = D.c, x0 = COL[2], X = CX_, sy = ROW[0] + 140;
  sub('c', x0, ROW[0], 'outlier handling', arrive(.08));
  const aa = arrive(.12), lev = l => sy - 13 - 10 * l;
  line([[CA0, sy], [CA1 + 8, sy]], {width: 1.2, alpha: aa}); line([[CB0 - 8, sy], [CB1, sy]], {width: 1.2, alpha: aa});
  for (const bx of [CA1 + 13, CB0 - 13]) line([[bx - 4, sy + 6], [bx + 4, sy - 6]], {width: 1.2, alpha: aa});
  ticksUnder(X, [20, 40, 60, 80, 100, 420, 440], sy, aa);
  text('age (years)', X(60), sy + 44, {size: 16, color: C.body, align: 'center', alpha: aa});
  // Tukey's box and fence, from the ages as recorded
  const bp = u < 0 ? seg(.3, .4) : u < FD ? 1 - u / FD : clamp((u - .45) / .5), by = sy - 56, [q1, md, q3] = Cc.q;
  box(X(q1), by - 9, X(q3) - X(q1), 18, {stroke: C.ink, width: 1.3, alpha: bp});
  line([[X(md), by - 9], [X(md), by + 9]], {width: 1.6, alpha: bp});
  line([[X(Cc.w[0]), by], [X(q1), by]], {width: 1.2, alpha: bp}); line([[X(q3), by], [X(Cc.w[1]), by]], {width: 1.2, alpha: bp});
  line([[X(Cc.w[0]), by - 5], [X(Cc.w[0]), by + 5]], {width: 1.2, alpha: bp}); line([[X(Cc.w[1]), by - 5], [X(Cc.w[1]), by + 5]], {width: 1.2, alpha: bp});
  line([[X(Cc.f[1]), by - 18], [X(Cc.f[1]), sy]], {color: C.guide, width: 1, dash: [5, 4], alpha: bp});
  text('Q3 + 1.5 IQR', X(Cc.f[1]), by - 24, {size: 16, color: C.body, align: 'center', alpha: bp});
  // the ages; once checked, the slip goes out at 430 (a dashed ring keeps its place) and comes in at 43
  // (q: how far the correction has come; going out, the corrected value fades where it is)
  const flag = u < 0 ? arrive(.5) : u < FD ? 1 - u / FD : clamp((u - 1.0) / .2);
  const keep = u < 0 ? arrive(.6) : u < FD ? 1 - u / FD : clamp((u - 1.4) / .2);
  const q = u < FD ? 1 : clamp((u - 1.85) / .5), back = u < 0 ? 1 : u < FD ? 1 - u / FD : clamp((u - FD) / .15);
  Cc.ages.forEach((v, i) => {
    const a = arrive(.1 + .25 * i / Cc.ages.length);
    if (v === 430) {
      if (q < .5) { mark(X(430), lev(0), 3, a * back * (1 - 2 * q), CR); ring(X(430), lev(0), 9, {alpha: flag * (1 - 2 * q)}); }
      else {
        ring(X(430), lev(0), 9, {alpha: .8 * flag * (u < FD ? 1 : 2 * q - 1), dash: [3, 3]});
        mark(X(43), lev(CLV[i]), 3, a * back * (u < FD ? 1 : 2 * q - 1), CR);
      }
    } else {
      mark(X(v), lev(CLV[i]), v === 96 ? 3 : 1, a, CR);
      if (v === 96) ring(X(v), lev(CLV[i]), 9, {alpha: flag});
    }
  });
  // its label starts past the fence, so the fence never runs through it
  text('checked: real, kept', X(Cc.f[1]) + 9, sy - 30, {size: 16, color: C.accent, alpha: keep});
  const sa = u < 0 ? arrive(.7) : u < FD ? 1 - u / FD : clamp(2 * q - 1);
  text('430 was a typing slip for 43: corrected', CB1 + 6, sy + 68, {size: 16, color: C.accent, align: 'right', alpha: sa});
}

/* (d) normalization and standardization: each feature on its own scale, then all as z-scores */
const KIND = [1, 4, 0];
function drawD() {
  const u = win(3), Dd = D.d, x0 = COL[0];
  sub('d', x0, ROW[1], 'normalization and standardization', arrive(.12));
  const RX0 = x0 + 154, RX1 = x0 + 260, ZX0 = x0 + 42, ZX1 = x0 + 282;
  const ys = [ROW[1] + 36, ROW[1] + 64, ROW[1] + 92], zs = [ROW[1] + 154, ROW[1] + 182, ROW[1] + 210];
  const ZX = z => ZX0 + (z + 2.5) / 5 * (ZX1 - ZX0);
  const aa = arrive(.16), za = arrive(.3);
  for (const y of zs) line([[ZX0, y], [ZX1, y]], {width: 1.1, alpha: za});
  Dd.names.forEach((nm, k) => {
    const [lo, hi] = Dd.lim[k], RX = v => RX0 + (v - lo) / (hi - lo) * (RX1 - RX0), y = ys[k];
    text(nm, x0 + 6, y + 5, {size: 16, alpha: aa});
    line([[RX0, y], [RX1, y]], {width: 1.1, alpha: aa});
    for (const v of [lo, hi]) line([[RX(v), y - 4], [RX(v), y + 4]], {width: 1, alpha: aa});
    text(String(lo), RX0 - 6, y + 5, {size: 16, color: C.body, align: 'right', alpha: aa});
    text(String(hi), RX1 + 6, y + 5, {size: 16, color: C.body, alpha: aa});
    for (let i = 0; i < 6; i++) {
      const x1 = RX(Dd.x[k][i]), x2 = ZX(Dd.z[k][i]), a = arrive(.18 + .03 * i + .04 * k);
      mark(x1, y - 7, KIND[k], a, 4.2);
      // in its window the z marks go out, then each travels down from its own scale to its z-score
      if (u < 0) { mark(x2, zs[k] - 7, KIND[k], a, 4.2); continue; }
      if (u < FD) { mark(x2, zs[k] - 7, KIND[k], 1 - u / FD, 4.2); continue; }
      // down from its own scale first, then along to its z-score: clear of the formula on the left
      const p = clamp((u - (.45 + .25 * k + .05 * i)) / .55), e1 = easeInOut(clamp(p / .6)), e2 = easeInOut(clamp((p - .4) / .6));
      if (p > 0 && p < 1) mark(lerp(x1, x2, e2), lerp(y - 7, zs[k] - 7, e1), KIND[k], 1, 4.2);
      if (p >= 1) mark(x2, zs[k] - 7, KIND[k], 1, 4.2);
    }
  });
  const yb = zs[2];
  for (const z of [-2, -1, 0, 1, 2]) { line([[ZX(z), yb], [ZX(z), yb + 5]], {width: 1.1, alpha: za});
    math(fmt(z), ZX(z), yb + 21, {size: 16, align: 'center', alpha: za}); }
  text('z-score (standard deviations)', ZX(0), yb + 43, {size: 16, color: C.body, align: 'center', alpha: za});
  line([[ZX(0), zs[0] - 16], [ZX(0), yb]], {color: C.guide, width: 1, dash: [5, 4], alpha: za});
  const ax = x0 + 238;
  arrow(ax, ys[2] + 14, ax, zs[0] - 20, {width: 1.3, head: 9, alpha: za});
  math('z = (x - \\rm{mean}) / \\rm{sd}', x0 + 6, (ys[2] + zs[0]) / 2 + 5, {size: 16, alpha: za});
}

/* (e) class imbalance handling */
function drawE() {
  const u = win(4), E = D.e, x0 = COL[1];
  sub('e', x0, ROW[1], 'class imbalance handling', arrive(.16));
  const P = {x: x0 + 62, y: ROW[1] + 24, w: 270, h: 150};
  const g = axes({...P, xlim: [-3.2, 4.4], ylim: [-2.8, 2.6], xticks: [-2, 0, 2, 4], yticks: [-2, 0, 2],
    xlabel: '\\rm{feature 1}', ylabel: '\\rm{feature 2}', ylabelGap: 40, tickSize: 16, progress: seg(.18, .35)});
  const nS = E.syn.length;
  // in its window the synthetic frauds go out (FD s), then SMOTE makes them again, 192 in 1.6 s
  const shown = u < 0 ? nS * clamp(seg(.5, .5) * 1.2) : u < FD ? nS : nS * clamp((u - .45) / 1.6);
  const sa = u < 0 ? 1 : u < FD ? 1 - u / FD : 1;
  g.inside(() => {
    for (const p of E.maj) mark(g.X(p[0]), g.Y(p[1]), 4, arrive(.2), 2.2);
    const m = Math.floor(shown);
    for (let i = 0; i < m; i++) {
      const s = E.min[E.src[i]], q = E.syn[i];
      // each synthetic fraud slides out of its source fraud along the segment to its place
      const age = u < FD ? 1 : clamp((shown - i) / 6);
      const x = lerp(s[0], q[0], easeOut(age)), y = lerp(s[1], q[1], easeOut(age));
      ring(g.X(x), g.Y(y), 2.1, {color: C.accent, width: .9, alpha: .85 * sa});
    }
    for (const p of E.min) mark(g.X(p[0]), g.Y(p[1]), 1, arrive(.3), 5);
  });
  // the key, then the counts before and after
  const KX = x0 + 360, ka = arrive(.4), ky = ROW[1] + 32;
  mark(KX + 4, ky - 5, 4, ka, 2.6); let kx = KX + 14 + text('normal', KX + 14, ky, {size: 16, alpha: ka}) + 18;
  mark(kx + 4, ky - 5, 1, ka, 4.4); kx += 14 + text('fraud', kx + 14, ky, {size: 16, alpha: ka}) + 18;
  ring(kx + 4, ky - 5, 3, {color: C.accent, width: 1.1, alpha: ka}); text('synthetic fraud', kx + 14, ky, {size: 16, alpha: ka});
  const BW = 160, bx = n => BW * n / 196, la = arrive(.3), nf = 4 + Math.floor(shown);
  const rows = [[ROW[1] + 74, 'before', 4, 1], [ROW[1] + 150, 'after SMOTE', nf, sa]];
  for (const [y, name, nfr, ra] of rows) {
    text(name, KX, y, {size: 16, color: C.body, alpha: la});
    box(KX, y + 10, bx(196), 12, {fill: C.sky, alpha: la});
    text('normal 196', KX + bx(196) + 8, y + 21, {size: 16, alpha: la});
    box(KX, y + 28, Math.max(1.5, bx(nfr)), 12, {fill: C.navy, alpha: la * ra});
    text('fraud ' + nfr + (name === 'before' ? ' (2%)' : ''), KX + Math.max(1.5, bx(nfr)) + 8, y + 39,
      {size: 16, color: name === 'before' ? C.ink : C.accent, alpha: la * ra});
  }
  text('4 real frauds and ' + (nf - 4) + ' synthetic', KX, ROW[1] + 216, {size: 16, color: C.body, alpha: la * sa});
}

function draw() {
  drawA(); drawB(); drawC(); drawD(); drawE();
  math('\\rm{median fill; 1 in = 2.54 cm; fences at 1.5 IQR; SMOTE,}\\ k = 3', COL[0], H - 14,
       {size: 15, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 4: The five data-cleaning steps from this section, illustrated"
ARIA = ('Five panels, one per cleaning step, each on a small worked example: a missing glucose value filled '
        'with the median and flagged in a new column, dates and heights made consistent, two ages beyond '
        "Tukey's fence investigated (one kept, one typing slip corrected from 430 to 43), three features "
        'turned into z-scores, and four frauds among 196 normal transactions balanced with synthetic frauds by SMOTE.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 670, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.5, 1.9, 4.5, 8.4, 11.0, 14.2, 17.7, 18.2]))
