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
    to one of its 3 nearest fraud neighbours at a random fraction (seeded).

The page shows the cleaned data and replays each step in turn.

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
const ROW = [0, 172, 344, 516, 688];
const R0 = .6, WIN = 3, ROUND = 17;
const POSTER_T = R0 + 5 * WIN + 1;
function win(k) { if (t < R0) return -1; const u = (t - R0) % ROUND - k * WIN; return u >= 0 && u < WIN ? u : -1; }
/* a value that, in its window, starts over from `from` and reaches `to` at time a..a+d (spring) */
const replay = (u, a, d = .3) => u < 0 ? 1 : sp(u - a, d);

/* (a) imputation */
function drawA() {
  const y0 = ROW[0], u = win(0), A = D.a;
  sub('a', 18, y0 + 30, 'imputation', arrive(0));
  const X0 = 250, DX = 52, ya = y0 + 70, aa = arrive(.05);
  rule(40, X0 + 6 * DX + 30, ya - 22, {width: 1.3, alpha: aa});
  text('patient', 40, ya - 4, {size: 15, color: C.body, alpha: aa});
  for (let k = 0; k < 7; k++) text(String(k + 1), X0 + k * DX, ya - 4, {size: 15, color: C.body, align: 'center', alpha: aa});
  rule(40, X0 + 6 * DX + 30, ya + 4, {alpha: aa});
  text('glucose (mg/dL)', 40, ya + 20, {size: 15, alpha: aa});
  const ind = replay(u, 1.95);
  /* the empty cell, one thing at a time (out, then in): as the window opens the value gives way
     to '?'; once the median is marked, '?' goes and the median slides in from the strip's side */
  let qa = 0, va = 1, vdx = 0;
  if (u >= 0) {
    const vin = sp(u - 1.55, .3);
    qa = clamp((u - .12) / .15) * (1 - clamp((u - 1.3) / .15));
    va = u < .12 ? 1 - u / .12 : vin; vdx = u < .12 ? 0 : 14 * (1 - vin);
  }
  A.glu.forEach((v, k) => {
    if (v >= 0) { text(String(v), X0 + k * DX, ya + 20, {size: 15, align: 'center', alpha: aa}); return; }
    box(X0 + k * DX - 24, ya + 5, 48, 21, {fill: C.wash, alpha: aa});
    text('?', X0 + k * DX, ya + 20, {size: 16, bold: true, color: C.accent, align: 'center', alpha: aa * qa});
    text(A.med.toFixed(1), X0 + k * DX + vdx, ya + 20, {size: 15, bold: true, color: C.accent, align: 'center', alpha: aa * va});
  });
  text('was missing', 40, ya + 44, {size: 15, alpha: aa * ind});
  A.glu.forEach((v, k) => text(v >= 0 ? '0' : '1', X0 + k * DX, ya + 44, {size: 15, align: 'center', alpha: aa * ind,
    color: v >= 0 ? C.ink : C.accent, bold: v < 0}));
  rule(40, X0 + 6 * DX + 30, ya + 52, {width: 1.3, alpha: aa});
  // the six observed values in order, and their median
  const SX = v => 640 + (v - 80) / 70 * 320, sy = y0 + 110, sa = arrive(.12);
  line([[SX(80), sy], [SX(150), sy]], {width: 1.2, alpha: sa});
  for (const v of [80, 100, 120, 140]) { line([[SX(v), sy], [SX(v), sy + 5]], {width: 1.1, alpha: sa});
    text(String(v), SX(v), sy + 20, {size: 14, align: 'center', alpha: sa}); }
  text('observed glucose (mg/dL)', SX(115), sy + 40, {size: 14, color: C.body, align: 'center', alpha: sa});
  A.glu.forEach(v => { if (v >= 0) mark(SX(v), sy - 12, 1, arrive(.15 + .2 * (v - 80) / 70), 4.4); });
  const ma = u < 0 ? arrive(.4) : clamp((u - .7) / .25);
  for (const v of A.mid) ring(SX(v), sy - 12, 9, {alpha: u < 0 ? 0 : clamp((u - .35) / .2) * (1 - clamp((u - 1.3) / .2))});
  line([[SX(A.med), sy - 32], [SX(A.med), sy]], {color: C.accent, width: 2, alpha: ma});
  text('median ' + A.med.toFixed(1), SX(A.med), sy - 38, {size: 15, color: C.accent, align: 'center', alpha: ma});
  // the median then fills the empty cell (above): it slides in there, it does not fly over the
  // table's rules and column numbers
}

/* (b) formats and units */
function drawB() {
  const y0 = ROW[1], u = win(1), B = D.b;
  sub('b', 18, y0 + 30, 'inconsistent formats and units', arrive(.04));
  const tA = [60, 230], tB = [560, 730], y1 = y0 + 62, aa = arrive(.08);
  const table = (x, head, rows, a, rowA) => {
    rule(x - 20, x + 290, y1 - 20, {width: 1.3, alpha: a});
    text(head[0], x, y1 - 2, {size: 15, color: C.body, alpha: a}); text(head[1], x + 170, y1 - 2, {size: 15, color: C.body, alpha: a});
    rule(x - 20, x + 290, y1 + 6, {alpha: a});
    rows.forEach((r, i) => { const ra = a * rowA(i);
      text(r[0], x, y1 + 26 + 22 * i, {size: 15, alpha: ra}); text(r[1], x + 170, y1 + 26 + 22 * i, {size: 15, alpha: ra}); });
    rule(x - 20, x + 290, y1 + 26 + 22 * 2 + 10, {width: 1.3, alpha: a});
  };
  table(tA[0], ['visit date', 'height'], B.raw, aa, () => 1);
  const conv = i => replay(u, .45 + .55 * i);
  table(tB[0], ['visit date', 'height (cm)'], B.iso.map((d, i) => [d, B.cm[i].toFixed(1)]), aa, conv);
  const ar = arrive(.12);
  arrow(400, y1 + 30, 520, y1 + 30, {width: 1.3, head: 9, alpha: ar});
  text('one date format', 460, y1 + 20, {size: 14, color: C.body, align: 'center', alpha: ar});
  text('one unit', 460, y1 + 50, {size: 14, color: C.body, align: 'center', alpha: ar});
  // in its window: the record being converted, on both sides, in the accent
  if (u >= 0) for (let i = 0; i < 3; i++) {
    const h = clamp((u - .3 - .55 * i) / .15) * (1 - clamp((u - .8 - .55 * i) / .15));
    if (h > 0) { box(tA[0] - 12, y1 + 12 + 22 * i, 300, 20, {stroke: C.accent, width: 1.4, alpha: h});
      box(tB[0] - 12, y1 + 12 + 22 * i, 300, 20, {stroke: C.accent, width: 1.4, alpha: h}); }
  }
}

/* (c) outlier handling, on a broken axis */
function drawC() {
  const y0 = ROW[2], u = win(2), Cc = D.c;
  sub('c', 18, y0 + 30, 'outlier handling', arrive(.08));
  const A0 = 60, A1 = 600, B0 = 648, B1 = 740, sy = y0 + 118;
  const X = v => v <= 110 ? A0 + (v - 20) / 90 * (A1 - A0) : B0 + (v - 420) / 20 * (B1 - B0);
  const aa = arrive(.12);
  line([[A0, sy], [A1 + 8, sy]], {width: 1.2, alpha: aa}); line([[B0 - 8, sy], [B1, sy]], {width: 1.2, alpha: aa});
  for (const bx of [A1 + 14, B0 - 14]) line([[bx - 4, sy + 6], [bx + 4, sy - 6]], {width: 1.2, alpha: aa});
  for (const v of [20, 40, 60, 80, 100, 420, 440]) {
    line([[X(v), sy], [X(v), sy + 5]], {width: 1.1, alpha: aa}); text(String(v), X(v), sy + 20, {size: 14, align: 'center', alpha: aa});
  }
  text('age (years)', X(60), sy + 40, {size: 14, color: C.body, align: 'center', alpha: aa});
  // Tukey's box and fence, from the ages as recorded
  const bp = u < 0 ? seg(.3, .4) : clamp((u - .3) / .5), by = sy - 44, [q1, md, q3] = Cc.q;
  box(X(q1), by - 9, X(q3) - X(q1), 18, {stroke: C.ink, width: 1.3, alpha: bp});
  line([[X(md), by - 9], [X(md), by + 9]], {width: 1.6, alpha: bp});
  line([[X(Cc.w[0]), by], [X(q1), by]], {width: 1.2, alpha: bp}); line([[X(q3), by], [X(Cc.w[1]), by]], {width: 1.2, alpha: bp});
  line([[X(Cc.w[0]), by - 5], [X(Cc.w[0]), by + 5]], {width: 1.2, alpha: bp}); line([[X(Cc.w[1]), by - 5], [X(Cc.w[1]), by + 5]], {width: 1.2, alpha: bp});
  line([[X(Cc.f[1]), by - 18], [X(Cc.f[1]), sy]], {color: C.guide, width: 1, dash: [5, 4], alpha: bp});
  text('Q3 + 1.5 IQR', X(Cc.f[1]), by - 24, {size: 14, color: C.body, align: 'center', alpha: bp});
  // the ages; the slip travels from 430 to 43 once it has been checked
  const flag = u < 0 ? arrive(.5) : clamp((u - .85) / .2);
  const keep = u < 0 ? arrive(.6) : clamp((u - 1.25) / .2);
  const fix = u < 0 ? 1 : sp(u - 1.7, .55);
  Cc.ages.forEach((v, i) => {
    const a = arrive(.1 + .25 * i / Cc.ages.length);
    if (v === 430) {
      const x = lerp(X(430), X(43), fix), y = sy - 14 - 46 * Math.sin(Math.PI * fix);
      if (fix > .02) ring(X(430), sy - 14, 9, {alpha: .8 * flag, dash: [3, 3]});
      mark(x, y, 3, a, 4.6);
      if (fix < .98) ring(x, y, 9, {alpha: flag});
    } else {
      mark(X(v), sy - 14, v === 96 ? 3 : 1, a, 4.6);
      if (v === 96) ring(X(v), sy - 14, 9, {alpha: flag});
    }
  });
  text('checked: real, kept', X(96), sy - 30, {size: 14, color: C.accent, align: 'center', alpha: keep});
  text('430 was a typing slip for 43: corrected', X(430), sy + 40, {size: 14, color: C.accent, align: 'center', alpha: clamp(fix * 3 - 2) * (u < 0 ? arrive(.7) : 1)});
}

/* (d) normalization and standardization */
const KIND = [1, 4, 0];
function drawD() {
  const y0 = ROW[3], u = win(3), Dd = D.d;
  sub('d', 18, y0 + 30, 'normalization and standardization', arrive(.12));
  const RX0 = 196, RX1 = 380, ZX0 = 560, ZX1 = 960, ys = [y0 + 64, y0 + 94, y0 + 124];
  const ZX = z => ZX0 + (z + 2.5) / 5 * (ZX1 - ZX0);
  const aa = arrive(.16);
  Dd.names.forEach((nm, k) => {
    const [lo, hi] = Dd.lim[k], RX = v => RX0 + (v - lo) / (hi - lo) * (RX1 - RX0), y = ys[k];
    text(nm, 40, y + 5, {size: 15, alpha: aa});
    line([[RX0, y], [RX1, y]], {width: 1.1, alpha: aa});
    for (const v of [lo, hi]) line([[RX(v), y - 4], [RX(v), y + 4]], {width: 1, alpha: aa});
    text(String(lo), RX0 - 6, y + 5, {size: 14, color: C.body, align: 'right', alpha: aa});
    text(String(hi), RX1 + 6, y + 5, {size: 14, color: C.body, alpha: aa});
    line([[ZX0, y], [ZX1, y]], {width: 1.1, alpha: aa});
    for (let i = 0; i < 6; i++) {
      const x0 = RX(Dd.x[k][i]), x1 = ZX(Dd.z[k][i]), a = arrive(.18 + .03 * i + .04 * k);
      mark(x0, y - 7, KIND[k], a, 4.2);
      const p = replay(u, .3 + .25 * k + .05 * i, .45);
      if (u >= 0 && p < .999) { const xx = lerp(x0, x1, p); mark(xx, y - 7 - 26 * Math.sin(Math.PI * p), KIND[k], 1, 4.2); }
      if (p > .98 || u < 0) mark(x1, y - 7, KIND[k], u < 0 ? a : 1, 4.2);
    }
  });
  const za = arrive(.3), yb = ys[2];
  for (const z of [-2, -1, 0, 1, 2]) { line([[ZX(z), yb], [ZX(z), yb + 5]], {width: 1.1, alpha: za});
    math(fmt(z), ZX(z), yb + 20, {size: 14, align: 'center', alpha: za}); }
  text('z-score (standard deviations from the mean)', ZX(0), yb + 40, {size: 14, color: C.body, align: 'center', alpha: za});
  line([[ZX(0), ys[0] - 16], [ZX(0), yb]], {color: C.guide, width: 1, dash: [5, 4], alpha: za});
  arrow(424, ys[1] - 7, 536, ys[1] - 7, {width: 1.3, head: 9, alpha: za});
  math('z = (x - \\rm{mean}) / \\rm{sd}', 480, ys[1] - 18, {size: 15, align: 'center', alpha: za});
}

/* (e) class imbalance handling */
function drawE() {
  const y0 = ROW[4], u = win(4), E = D.e;
  sub('e', 18, y0 + 30, 'class imbalance handling', arrive(.16));
  const P = {x: 60, y: y0 + 46, w: 380, h: 118};
  const g = axes({...P, xlim: [-3.2, 4.4], ylim: [-2.8, 2.6], xticks: [], yticks: [], progress: seg(.18, .35)});
  const nS = E.syn.length, shown = u < 0 ? nS * clamp(seg(.5, .5) * 1.2) : (u < .3 ? nS * (1 - u / .3) : nS * clamp((u - .45) / 1.6));
  g.inside(() => {
    for (const p of E.maj) mark(g.X(p[0]), g.Y(p[1]), 4, arrive(.2), 2.2);
    const m = Math.floor(shown);
    for (let i = 0; i < m; i++) {
      const s = E.min[E.src[i]], q = E.syn[i];
      // each synthetic fraud slides out of its source fraud along the segment to its place
      const age = u < 0 ? 1 : clamp((shown - i) / 6);
      const x = lerp(s[0], q[0], easeOut(age)), y = lerp(s[1], q[1], easeOut(age));
      ring(g.X(x), g.Y(y), 2.1, {color: C.accent, width: .9, alpha: .85});
    }
    for (const p of E.min) mark(g.X(p[0]), g.Y(p[1]), 1, arrive(.3), 5);
  });
  // the counts, before and after
  const BX = 620, BW = 250, bx = n => BW * n / 196, la = arrive(.3), nf = 4 + Math.floor(shown);
  const rowsY = [y0 + 84, y0 + 128];
  text('before', 490, rowsY[0] + 5, {size: 15, color: C.body, alpha: la});
  text('after SMOTE', 490, rowsY[1] + 5, {size: 15, color: C.body, alpha: la});
  for (const [r, nfr] of [[0, 4], [1, nf]]) {
    const y = rowsY[r];
    box(BX, y - 18, bx(196), 12, {fill: C.sky, alpha: la});
    text('normal 196', BX + bx(196) + 8, y - 8, {size: 14, alpha: la});
    box(BX, y, Math.max(1.5, bx(nfr)), 12, {fill: C.navy, alpha: la});
    text('fraud ' + nfr + (r === 0 ? ' (2%)' : ''), BX + Math.max(1.5, bx(nfr)) + 8, y + 10, {size: 14, color: r ? C.accent : C.ink, alpha: la});
  }
  text('4 real frauds and ' + (nf - 4) + ' synthetic', BX, rowsY[1] + 34, {size: 14, color: C.body, alpha: la});
  const ka = arrive(.4), kx = 490, ky = y0 + 50;
  mark(kx + 4, ky - 4, 4, ka, 2.6); text('normal', kx + 12, ky, {size: 14, alpha: ka});
  mark(kx + 72, ky - 4, 1, ka, 4.4); text('fraud', kx + 82, ky, {size: 14, alpha: ka});
  ring(kx + 132, ky - 4, 3, {color: C.accent, width: 1.1, alpha: ka}); text('synthetic fraud', kx + 140, ky, {size: 14, alpha: ka});
}

function draw() {
  drawA(); drawB(); drawC(); drawD(); drawE();
  text('median imputation with an indicator column; ISO dates and centimetres; Tukey’s fences; z-scores; ' +
       'SMOTE, 3 neighbours', 18, H - 14, {size: 14, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 4: The five data-cleaning steps from this section, illustrated"
ARIA = ('Five rows, one per cleaning step, each on a small worked example: a missing glucose value filled '
        'with the median and flagged in a new column, dates and heights made consistent, two ages beyond '
        "Tukey's fence investigated (one kept, one typing slip corrected from 430 to 43), three features "
        'turned into z-scores, and four frauds among 196 normal transactions balanced with synthetic frauds by SMOTE.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 900, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.5, 1.9, 4.5, 8.4, 11.0, 14.2]))
