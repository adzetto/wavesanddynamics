"""Figure 6 of the machine learning guide (stem image3): the three feature
engineering steps of section 3.4, each on a small worked example, every
number computed.

(a) Extraction: one purchase timestamp becomes the guide's features: hour,
    weekday, weekend flag, season (meteorological, northern hemisphere) and
    days since the last purchase (Python's datetime).
(b) Transformation: 2,000 simulated incomes (lognormal, median 45 k$,
    seed 6) are right-skewed; the log transform, y = log10(income), makes
    them symmetric. The curve is the transform itself; the histogram of the
    raw values lies along its x axis, that of the logged values along its y
    axis (sample skewness before and after in the figure).
(c) Encoding: one-hot encoding of a hospital's diagnosis group (the guide's
    readmission example): one column per group, 1 where the record belongs.

The page shows all three and plays each in turn: the parts of the timestamp
each feature comes from, a probe carried through the log curve from one
histogram to the other, and the records encoded one by one. Each has an 8 s
window of a 27 s round, paced so every step can be followed (30 Sep 2026:
twice as slow as before; the timing is in the check file).

Run: python tools/numfig/mla_features.py [--look]
"""
import datetime as dt
import sys

import numpy as np
from scipy.stats import skew
from sklearn.preprocessing import OneHotEncoder

import common
from mla_shared import LIB, report

NAME, STEM = "mla-features", "mla_features"
L = []
say = L.append
say("nf-mla-features: Figure 6, the three feature engineering steps")
say("")

# (a) extraction
T = dt.datetime(2024, 12, 5, 14, 32)
PREV = dt.datetime(2024, 11, 29, 9, 10)
SEASON = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
          6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}
feats = [("hour", str(T.hour)), ("weekday", T.strftime("%A")), ("weekend", "no (0)" if T.weekday() < 5 else "yes (1)"),
         ("season", SEASON[T.month]), ("days since last purchase", str((T.date() - PREV.date()).days))]
say(f"(a) EXTRACTION from {T:%Y-%m-%d %H:%M} (previous purchase {PREV:%Y-%m-%d %H:%M})")
for k, v in feats:
    say(f"  {k:26s} {v}")
say(f"  CHECK: weekday index {T.weekday()} (Monday 0); {T:%Y-%m-%d} is a {T:%A}; calendar days between"
    f" the purchases {(T.date() - PREV.date()).days} (elapsed {(T - PREV).total_seconds()/86400:.3f} days)")

# (b) log transform
rng = np.random.default_rng(6)
inc = np.exp(rng.normal(np.log(45), 0.55, 2000))
lg = np.log10(inc)
XB = np.arange(0, 360, 10.0)
YB = np.arange(0.8, 2.66, 0.06)
hx, _ = np.histogram(inc, XB)
hy, _ = np.histogram(lg, YB)
s0, s1 = skew(inc), skew(lg)
say("")
say("(b) TRANSFORMATION: 2000 incomes ~ lognormal(ln 45, 0.55) k$, seed 6")
say(f"  median {np.median(inc):.2f} k$, mean {inc.mean():.2f} k$, max {inc.max():.1f} k$")
say(f"  sample skewness raw {s0:.3f}, after log10 {s1:.3f} (a normal sample's is 0; lognormal theory"
    f" for sigma 0.55: {(np.exp(0.55**2)+2)*np.sqrt(np.exp(0.55**2)-1):.3f})")
say(f"  CHECK: every value inside the drawn ranges: {inc.min():.1f}..{inc.max():.1f} in [0, 350] k$,"
    f" {lg.min():.3f}..{lg.max():.3f} in [0.8, 2.66]; counts {hx.sum()} and {hy.sum()} of 2000")

# (c) one-hot
DIAG = ["cardiac", "renal", "respiratory", "cardiac", "renal"]
CATS = ["cardiac", "renal", "respiratory"]
enc = OneHotEncoder(categories=[CATS]).fit(np.array(DIAG)[:, None])
OH = enc.transform(np.array(DIAG)[:, None]).toarray().astype(int)
say("")
say("(c) ENCODING: one-hot of diagnosis group " + ", ".join(DIAG))
say(f"  CHECK: scikit-learn OneHotEncoder gives {OH.tolist()}; each row sums to 1: {bool(np.all(OH.sum(1) == 1))}")
say("")
say("TIMING (30 Sep 2026, the client: slow Figure 6 down so each step can be followed): every step")
say("  about twice as slow, old values in brackets; the intro unchanged (readable by 0.6 s, all in by 1.2 s)")
say("  round 27 s (13.5 s): each step an 8 s window (4 s) from 0.6 s, then 3 s at rest (1.5 s); poster 25.6 s (13.6 s)")
say("  (a) each feature in turn every 1.56 s (0.78 s): its source and value light up in 0.3 s (0.15 s),")
say("      hold 0.94 s (0.47 s) and dim in 0.3 s (0.15 s); first at 0.8 s (0.6 s)")
say("  (b) the probe fades in at 18 k$ (it used to appear at 45 k$ and leave mid-glide), then glides to 45, 110")
say("      and 230 k$ with a 0.8 s spring (0.5 s), one stop every 2 s (0.95 s), so each value holds still about")
say("      0.7 s (it never came to rest before), and fades out; timed from its own window (the old cycle of")
say("      4.55 s ran on the page clock and drifted against the 13.5 s round)")
say("  (c) the table's values clear in 0.4 s (at once) and each record takes 1.4 s (0.7 s): it lights up in")
say("      0.24 s (0.12 s), its ones and zeros appear 0.5 s in, in 0.3 s (0.25 s in, 0.15 s), and it dims")
report(STEM, L)

DATA = {
    "a": {"ts": f"{T:%Y-%m-%d %H:%M}", "prev": f"{PREV:%Y-%m-%d}", "f": feats},
    "b": {"xb": XB, "hx": hx, "yb": YB, "hy": hy, "s": [s0, s1]},
    "c": {"d": DIAG, "cats": CATS, "oh": OH},
}

JS = LIB + r"""
const D = DATA;
/* each step runs in its own window of a 27 s round, then rests; paced so it
   can be followed (30 Sep 2026: twice as slow as before) */
const R0 = .6, WIN = 8, ROUND = 27;
const POSTER_T = R0 + 3 * WIN + 1;
function win(k) { if (t < R0) return -1; const u = (t - R0) % ROUND - k * WIN; return u >= 0 && u < WIN ? u : -1; }

/* (a) extraction */
function drawA() {
  const A = D.a, u = win(0), a0 = arrive(0);
  sub('a', 18, 34, 'extraction', a0);
  const bx = 24, by = 70;
  text('purchase time', bx, by, {size: 14, color: C.body, alpha: a0});
  box(bx, by + 8, 200, 32, {stroke: C.ink, width: 1.3, alpha: a0});
  const ts = A.ts, date = ts.slice(0, 10), hh = ts.slice(11, 13);
  const tx = bx + 12, ty = by + 30;
  const wDate = tw(date + ' ', 17), wHH = tw(hh, 17);
  text(ts, tx, ty, {size: 17, alpha: a0});
  text('previous purchase ' + A.prev, bx, by + 62, {size: 14, color: C.body, alpha: arrive(.05)});
  // which part of the raw field each feature comes from: 0 the date, 1 the hour, 2 both dates
  const SRC = [1, 0, 0, 0, 2];
  const FX = 24, FY = 176, RH = 30, LANE = 236;       // LANE: between the names and the values
  // its window: each feature in turn, every AS: its source and value light up (.3 s), hold, and dim (.3 s)
  const A0 = .2, AS = 1.56;
  const k = u < 0 ? -1 : Math.min(4, Math.floor((u - A0) / AS));
  A.f.forEach(([nm, v], i) => {
    const ui = u - A0 - AS * i;
    const a = arrive(.1 + .04 * i), on = i === k ? clamp(ui / .3) * (1 - clamp((ui - 1.24) / .3)) : 0;
    text(nm, FX, FY + i * RH, {size: 15, alpha: a});
    text(v, 318, FY + i * RH, {size: 15, align: 'right', bold: on > .5, color: on > .5 ? C.accent : C.ink, alpha: a});
    line([[FX, FY + i * RH + 9], [318, FY + i * RH + 9]], {color: C.rule, width: 1, alpha: a * .8});
    if (on > 0) {
      // underline the part of the timestamp; a dashed leader runs from it round the text
      // (TikZ -|): down into the gap below, across to a lane clear of every label, down
      // to the feature's row, and across to its value
      const s = SRC[i], x0 = s === 1 ? tx + wDate : tx, x1 = s === 1 ? tx + wDate + wHH : tx + tw(date, 17);
      line([[x0, ty + 5], [x1, ty + 5]], {color: C.accent, width: 2.2, alpha: on});
      const p0 = bx + tw('previous purchase ', 14), p1 = bx + tw('previous purchase ' + A.prev, 14);
      if (s === 2) line([[p0, by + 67], [p1, by + 67]], {color: C.accent, width: 2, alpha: on});
      const sx = s === 2 ? (p0 + p1) / 2 : (x0 + x1) / 2, sy = s === 2 ? by + 70 : ty + 8;
      const gy = s === 2 ? (by + 70 + FY - 12) / 2 : (by + 40 + by + 52) / 2, ry = FY + i * RH - 5;
      const vx = 318 - tw(v, 15, {bold: true}) - 5;
      line([[sx, sy], [sx, gy], [LANE, gy], [LANE, ry], [vx, ry]], {color: C.accent, width: 1.2, dash: [4, 3], alpha: on});
    }
  });
  text('five features from one field', FX, FY + 5 * RH + 4, {size: 14, color: C.muted, alpha: arrive(.3)});
}

/* (b) transformation: the log curve, with the raw histogram above it and
   the logged one beside it (marginal histograms sharing its axes) */
function drawB() {
  const B = D.b, u = win(1);
  sub('b', 352, 34, 'transformation', arrive(.05));
  const P = {x: 410, y: 124, w: 196, h: 196}, MH = 54, GAP = 7;
  const g = axes({...P, xlim: [0, 350], ylim: [.8, 2.66], xticks: [0, 100, 200, 300], yticks: [1, 1.5, 2, 2.5],
    yfmt: v => v === 1 ? '1' : v === 2 ? '2' : v.toFixed(1), xlabel: '\\rm{income (k$)}', ylabel: '\\rm{log}_{10}\\ \\rm{income}',
    ylabelGap: 42, progress: seg(.04, .35), tickSize: 14, labelSize: 15});
  const mx = Math.max(...B.hx), my = Math.max(...B.hy);
  // the probe: an income carried down to the curve and across to its logarithm. Its window: it
  // fades in at 18 k$ (.3 s) and rests, glides (.8 s) to 45, 110 and 230 k$, a stop every 2 s,
  // and fades out; `pa` is how much of it shows
  const STOPS = [18, 45, 110, 230];
  let probe = -1, pa = 0;
  if (u >= 0) {
    pa = clamp((u - .2) / .3) * (1 - clamp((u - 7.5) / .3));
    probe = STOPS[0];
    for (let j = 1; j < STOPS.length; j++) probe += (STOPS[j] - STOPS[j - 1]) * sp(u - 1.5 - 2 * (j - 1), .8);
  }
  const hiX = pa <= 0 ? -1 : Math.floor(probe / 10), hiY = pa <= 0 ? -1 : Math.floor((Math.log10(probe) - .8) / .06);
  const ha = arrive(.15), top = P.y - GAP, right = P.x + P.w + GAP;
  for (let i = 0; i < B.hx.length; i++) {
    const h = MH * B.hx[i] / mx * seg(.2 + .2 * i / B.hx.length, .3), x0 = g.X(B.xb[i]), bw = g.X(B.xb[i + 1]) - x0;
    if (h > .2) box(x0, top - h, bw, h, {fill: C.mist, stroke: '#fff', width: .5, alpha: ha});
    if (h > .2 && i === hiX) box(x0, top - h, bw, h, {fill: C.accent, stroke: '#fff', width: .5, alpha: ha * pa});
  }
  line([[P.x, top], [P.x + P.w, top]], {width: 1, alpha: ha});
  for (let i = 0; i < B.hy.length; i++) {
    const w = MH * B.hy[i] / my * seg(.3 + .2 * i / B.hy.length, .3), y0 = g.Y(B.yb[i + 1]), bh = g.Y(B.yb[i]) - y0;
    if (w > .2) box(right, y0, w, bh, {fill: C.sky, stroke: '#fff', width: .5, alpha: ha});
    if (w > .2 && i === hiY) box(right, y0, w, bh, {fill: C.accent, stroke: '#fff', width: .5, alpha: ha * pa});
  }
  line([[right, P.y], [right, P.y + P.h]], {width: 1, alpha: ha});
  g.inside(() => {
    const pts = []; for (let k = 0; k <= 200; k++) { const x = 6.5 + (350 - 6.5) * Math.pow(k / 200, 2); pts.push([g.X(x), g.Y(Math.log10(x))]); }
    line(pts, {color: C.navy, width: 2.4, progress: seg(.18, .4)});
  });
  // the curve's name, and its ink box: the probe's level line passes behind it, 3 units clear
  const LX = g.X(215), LY = g.Y(2.05) + 30, lw = mw('y = \\rm{log}_{10}\\ x', 15);
  const lb = [LX - lw / 2 - 3, LY - 14, LX + lw / 2 + 3, LY + 7];
  if (pa > 0) {
    const px = g.X(probe), py = g.Y(Math.log10(probe)), pr = {color: C.accent, width: 1.2, dash: [4, 3], alpha: pa};
    line([[px, top], [px, py]], pr);
    if (py > lb[1] && py < lb[3] && px < lb[2]) {
      if (lb[0] > px) line([[px, py], [lb[0], py]], pr);
      line([[Math.max(px, lb[2]), py], [right, py]], pr);
    } else line([[px, py], [right, py]], pr);
    dot(px, py, 5, {color: '#fff', fill: C.accent, width: 1.4, alpha: pa});
    math(probe.toFixed(0) + '\\ \\rm{k$}\\ \\to\\ ' + Math.log10(probe).toFixed(2), P.x + P.w - 6, P.y + P.h - 12,
      {size: 15, color: C.accent, align: 'right', alpha: pa});
  }
  const la = arrive(.45);
  math('y = \\rm{log}_{10}\\ x', LX, LY, {size: 15, color: C.navy, align: 'center', alpha: la});
  text('raw incomes: skewness ' + B.s[0].toFixed(2), P.x, top - MH - 8, {size: 14, color: C.body, alpha: la});
  text('logged', right + 4, P.y + P.h + 20, {size: 14, color: C.body, alpha: la});
  text(nfmt(B.s[1], 2), right + 4, P.y + P.h + 38, {size: 14, color: C.body, alpha: la});
}

/* (c) encoding: one-hot */
function drawC() {
  const Cc = D.c, u = win(2), a0 = arrive(.1);
  sub('c', 708, 34, 'encoding', a0);
  const X0 = 712, CX = [812, 878, 944], Y0 = 96, RH = 32, n = Cc.d.length;
  rule(X0 - 4, 976, Y0 - 22, {width: 1.3, alpha: a0});
  text('diagnosis', X0, Y0 - 4, {size: 15, color: C.body, alpha: a0});
  Cc.cats.forEach((c, j) => text(c, CX[j], Y0 - 4, {size: 14, color: C.body, align: 'center', alpha: a0}));
  rule(X0 - 4, 976, Y0 + 6, {alpha: a0});
  line([[788, Y0 - 22], [788, Y0 + 6 + RH * n + 6]], {color: C.rule, width: 1, alpha: a0});
  // its window: the ones and zeros clear (.4 s), then each record in turn, every ES: it lights
  // up (.24 s), its ones and zeros appear .5 s in (.3 s), and it dims again
  const E0 = .6, ES = 1.4;
  const k = u < 0 ? n : Math.floor((u - E0) / ES);
  for (let i = 0; i < n; i++) {
    const y = Y0 + 28 + RH * i, a = arrive(.14 + .04 * i), ui = u - E0 - ES * i;
    const on = u >= 0 && i === k ? clamp(ui / .24) * (1 - clamp((ui - 1.16) / .24)) : 0;
    text(Cc.d[i], X0, y, {size: 15, color: on > .5 ? C.accent : C.ink, alpha: a});
    const shown = u < 0 ? 1 : u < .4 ? 1 - u / .4 : i < k ? 1 : i === k ? clamp((ui - .5) / .3) : 0;
    Cc.cats.forEach((c, j) => {
      const v = Cc.oh[i][j];
      if (v && on > 0) box(CX[j] - 16, y - 16, 32, 22, {fill: C.wash, alpha: on});
      text(String(v), CX[j], y, {size: 15, align: 'center', bold: v === 1, color: v ? (on > .5 ? C.accent : C.navy) : C.muted, alpha: a * shown});
    });
  }
  rule(X0 - 4, 976, Y0 + 6 + RH * n + 6, {width: 1.3, alpha: a0});
  text('one column per group,', X0, Y0 + RH * n + 44, {size: 14, color: C.muted, alpha: arrive(.3)});
  text('1 where the record belongs', X0, Y0 + RH * n + 62, {size: 14, color: C.muted, alpha: arrive(.3)});
}

function draw() {
  drawA(); drawB(); drawC();
  text('extraction with Python’s datetime; 2,000 simulated incomes (lognormal, median $45k); ' +
       'one-hot encoding with scikit-learn', 18, H - 14, {size: 14, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 6: The three feature-engineering steps from this section, illustrated"
ARIA = ('Three panels: one purchase time broken into hour, weekday, weekend, season and days since the last '
        'purchase; the log curve carrying a right-skewed histogram of 2,000 incomes into a nearly symmetric '
        'one; and five diagnosis groups one-hot encoded into columns of ones and zeros.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 420, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.5, 1.2, 4.5, 7.6, 9.6, 11.6, 13.6, 15.6, 16.8, 17.9, 20.8]))
