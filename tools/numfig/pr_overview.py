"""The probability deck's first slide in motion: four connected questions.

Slide 1 of "Probability, statistics and estimation" (tools/deck/src/s001.html)
organises the subject as four connected questions, his words:
  Probability, "Given a model, what could happen?"
  Statistics, "Given observations, what can we learn?"
  Stochastic processes, "How do uncertain values relate across time or space?"
  Estimation, "What is an unknown parameter, state or future response?"
with his arrows: Statistics to Probability, "learn and check a model";
Probability to Stochastic processes; Statistics to Estimation; Stochastic
processes to Estimation, "model + observations". This figure draws the four
as four computations on his running examples, in his 2 x 2 and with his
arrows, for the deck's card on the Big Picture page (tools/bp_art.py). It is
in no document, so it has no fragment.

Model.
  Probability: his concrete strength, one cylinder X ~ N(32, 3^2) MPa
      (slides 16 to 21: sigma = 3 MPa, mean 32 MPa). Its density, its lower 5%
      (slide 13's "Lower 5%", below mu - 1.645 sigma = 27.07 MPa), and the
      tests falling out of it one by one, then faster: N = 1000 draws from
      the model (numpy default_rng, seed SEED), the same every run.
  Statistics: the same tests as they land, a histogram in his 2 MPa bins
      (slide 13), drawn as a density on the same axes as the model, and the
      normal model fitted to them (sample mean, sample SD), his "Fitted normal
      model".
  Stochastic processes: his random walk of sensor bias (slide 51), four paths
      X_n = X_0 + e_1 + ... + e_n, e ~ N(0, 0.3^2) mm, X_0 = 0, 160 steps, his
      seed 5101 (the same four paths his slide draws), inside his pointwise 95%
      band +-1.96 x 0.3 sqrt(n) mm about E[X_n] = X_0.
  Estimation: the unknown mean strength from the same tests, the running mean
      xbar_n with its 95% interval xbar_n +- 1.96 sigma / sqrt(n) (slide 17:
      known sigma = 3 MPa, SE = 0.6 MPa and +-1.176 MPa at n = 25), on a log n
      axis as his slide 34 draws a running mean, closing on the fixed true mean.

Run: python tools/numfig/pr_overview.py [--look]   (writes the page, the still
and tools/numfig/pr_overview.check.txt; --look also writes frames)
"""
import os
import sys

import numpy as np
from scipy import stats

import common

NAME = "pr-overview"
HERE = os.path.dirname(os.path.abspath(__file__))

MU, SIGMA = 32.0, 3.0                  # his cylinder strength, MPa
N = 1000                               # tests
SEED = 2                               # pick_seed(): the first from 1 that holds the mean
Z95 = float(stats.norm.ppf(0.975))
Q05 = float(stats.norm.ppf(0.05, MU, SIGMA))
E0, BW, NB = 19.0, 2.0, 13             # his 2 MPa bins, 19 to 45 MPa
RW_SIGMA, RW_N, RW_K, RW_SEED = 0.3, 160, 4, 5101   # his random walk (slide 51)

# the clock (s): the first test leaves the model at T0; test i leaves RUN ln i / ln N
# later and falls for FALL; the finished picture holds, fades and starts again
T0, RUN, FALL, HOLD, FADE, GAP = 0.6, 9.0, 0.45, 2.4, 0.5, 0.3
PER = RUN + FALL + HOLD + FADE + GAP
N_POSTER = 150                         # tests landed in the printed frame


def tests(seed=SEED):
    return np.random.default_rng(seed).normal(MU, SIGMA, N)


def walks():
    rng = np.random.default_rng(RW_SEED)
    return np.concatenate([np.zeros((RW_K, 1)), np.cumsum(rng.normal(0, RW_SIGMA, (RW_K, RW_N)), axis=1)],
                          axis=1)


def running(x):
    n = np.arange(1, x.size + 1)
    xb = np.cumsum(x) / n
    sd = np.array([x[:k].std(ddof=1) if k > 1 else 0.0 for k in n])
    return n, xb, sd


def misses(x):
    """How many n the running 95% interval leaves the true mean out."""
    n = np.arange(1, x.size + 1)
    return int(np.sum(np.abs(np.cumsum(x) / n - MU) > Z95 * SIGMA / np.sqrt(n)))


def covers_all(x):
    return misses(x) == 0


def pick_seed():
    """The stream the figure draws: the first seed from 1 (the slide's number)
    whose running interval holds the true mean at every n up to N, so the one
    path the reader sees shows the rule, not its 5% exception."""
    s = 1
    while not covers_all(tests(s)):
        s += 1
    return s


JS = r"""
const D = DATA;
const XS = b64f32(D.x), NT = XS.length;               // the tests, in the order they are made (MPa)
const WK = b64f32(D.walk), NK = D.nk, NSTEP = D.nstep; // his random walks, NK paths of NSTEP + 1 values (mm)
const MU = D.mu, SG = D.sigma, Q05 = D.q05, Z = D.z, E0 = D.e0, BW = D.bw, NB = D.nb;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);

/* the running mean and standard deviation after n tests (Welford), and each
   test's bin: the page computes them from the tests themselves */
const XB = new Float64Array(NT + 1), SD = new Float64Array(NT + 1), BIN = new Int16Array(NT);
(function () {
  let m = 0, q = 0;
  for (let i = 0; i < NT; i++) {
    const x = XS[i], d = x - m;
    m += d / (i + 1); q += d * (x - m);
    XB[i + 1] = m; SD[i + 1] = i ? Math.sqrt(q / i) : 0;
    BIN[i] = Math.floor((x - E0) / BW);
  }
})();
const CNT = new Float64Array(NB);
function counts(n) { CNT.fill(0); for (let i = 0; i < n; i++) CNT[BIN[i]]++; return CNT; }

/* ------------------------------------------------------------ clock
   Test i (from 1) leaves the model RUN ln i / ln NT s into the loop, so the
   log n axis of Estimation runs at one speed; it lands FALL s later. */
const T0 = D.t0, RUN = D.run, FALL = D.fall, HOLD = D.hold, FADE = D.fade, PER = D.per, LNT = Math.log(NT);
const rel = i => RUN * Math.log(i) / LNT;
const count = u => u < 0 ? 0 : Math.min(NT, Math.floor(Math.exp(u / RUN * LNT) + 1e-9));
let U = -1, L0 = 0, DA = 0;                            // s into this loop, its start, the data's alpha
function clock() {
  if (t < T0) { U = -1; L0 = 0; DA = 0; return; }
  U = (t - T0) % PER; L0 = t - U;
  DA = 1 - clamp((U - (RUN + FALL + HOLD)) / FADE);
}
const landed = () => count(U - FALL);
const arrive = n => settle(L0 + rel(n) + FALL, .2);   // the n-th test arriving, 0 to 1

/* ------------------------------------------------------------ layout */
const LX = 84, RX = 570, PW = 346, TY = 50, BY = 340, PH = 146;
const pdf = (x, m, s) => Math.exp(-.5 * ((x - m) / s) * ((x - m) / s)) / (s * 2.5066282746310002);
function title(s, x, y, color, t0) {
  const a = lab(t0);
  text(s, x, y + rise(a), { size: 26, bold: true, color, align: 'center', alpha: a });
}
function growArrow(x1, y1, x2, y2, p, o) {
  if (p <= 0) return;
  arrow(x1, y1, lerp(x1, x2, p), lerp(y1, y2, p), o);
}

/* ------------------------------------------------------------ Probability */
const SX = v => LX + (v - 20) / 24 * PW, TX = v => RX + (v - 20) / 24 * PW;
const PY = p => TY + PH - p / .2 * PH;
const MODEL = [], TAIL = [];
for (let i = 0; i <= 240; i++) { const x = 20 + 24 * i / 240; MODEL.push([x, pdf(x, MU, SG)]); }
for (let i = 0; i <= 80; i++) { const x = 20 + (Q05 - 20) * i / 80; TAIL.push([x, pdf(x, MU, SG)]); }
function area(pts, X, color, alpha) {                  // the region under a curve, to the axis
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = color; ctx.beginPath();
  ctx.moveTo(X(pts[0][0]), PY(0));
  for (const [x, p] of pts) ctx.lineTo(X(x), PY(p));
  ctx.lineTo(X(pts[pts.length - 1][0]), PY(0)); ctx.closePath(); ctx.fill(); ctx.restore();
}
function panelP() {
  title('Probability', LX + PW / 2, TY - 18, C.navy, 0);
  const g = axes({ x: LX, y: TY, w: PW, h: PH, xlim: [20, 44], ylim: [0, .2], xticks: [20, 25, 30, 35, 40],
                   yticks: [0, .1, .2], xlabel: '\\rm{Strength (MPa)}', ylabel: '\\rm{Density}',
                   progress: seg(.02, .35), ylabelGap: 46, labelSize: 16 });
  const fa = seg(.25, .3);
  g.inside(() => {
    area(MODEL, SX, C.steel, fa);
    area(TAIL, SX, C.amber, .85 * seg(.4, .25));
    line(MODEL.map(([x, p]) => [SX(x), PY(p)]), { color: C.navy, width: 2.6, progress: seg(.08, .4) });
  });
  if (U >= 0 && DA > 0) g.inside(() => {
    /* the tests leaving the model: each leaves the curve at its value and
       drops to the axis in FALL s, so those in the air lie evenly under the
       density, as draws from it do; then a tick where it landed */
    const n0 = landed(), n1 = count(U), R = 3.3;
    ctx.save(); ctx.globalAlpha *= DA;
    for (const warm of [false, true]) {
      ctx.beginPath();
      for (let i = n0 + 1; i <= n1; i++) {
        const x = XS[i - 1];
        if ((x < Q05) !== warm) continue;
        const f = (U - rel(i)) / FALL, y = PY(pdf(x, MU, SG) * (1 - f)), cx = SX(x), r = R * clamp(f / .12, .3, 1);
        ctx.moveTo(cx + r, y); ctx.arc(cx, y, r, 0, 2 * Math.PI);
      }
      ctx.fillStyle = warm ? C.accent : C.navy; ctx.fill();
      if (warm) { ctx.strokeStyle = '#fff'; ctx.lineWidth = .9; ctx.stroke(); }
    }
    // a tick where each lands, fading over a second (six steps of fade, one path each)
    const rug = [];
    for (let k = 0; k < 12; k++) rug.push(new Path2D());
    for (let i = n0; i >= 1; i--) {
      const age = U - rel(i) - FALL;
      if (age > 1) break;
      const lev = Math.min(5, Math.floor((1 - age) * 6)), cx = SX(XS[i - 1]);
      const p = rug[lev * 2 + (XS[i - 1] < Q05 ? 1 : 0)];
      p.moveTo(cx, PY(0)); p.lineTo(cx, PY(0) - 9);
    }
    ctx.lineWidth = 1.3;
    for (let k = 0; k < 12; k++) {
      ctx.save(); ctx.globalAlpha *= ((k >> 1) + 1) / 6; ctx.strokeStyle = k & 1 ? C.accent : C.navy;
      ctx.stroke(rug[k]); ctx.restore();
    }
    ctx.restore();
  });
  // his words for the tail, and his notation for the model, above the curve
  const la = lab(.45), ma = lab(.35);
  text('Lower 5%', SX(22), PY(.06) + rise(la), { size: 15, color: C.accent, alpha: la });
  math('N(32,\\,3^{2})', SX(36.4), PY(.085) + rise(ma), { size: 16, color: C.navy, alpha: ma });
}

/* ------------------------------------------------------------ Statistics */
function panelS() {
  title('Statistics', RX + PW / 2, TY - 18, C.accent, .04);
  const g = axes({ x: RX, y: TY, w: PW, h: PH, xlim: [20, 44], ylim: [0, .2], xticks: [20, 25, 30, 35, 40],
                   yticks: [0, .1, .2], yfmt: () => '', xlabel: '\\rm{Strength (MPa)}',
                   progress: seg(.06, .35), labelSize: 16 });
  if (U < 0 || DA <= 0) return;
  const n = landed();
  if (n < 1) return;
  const p = arrive(n), c = counts(n), last = BIN[n - 1];
  g.inside(() => {
    for (let k = 0; k < NB; k++) {
      const was = n > 1 ? (c[k] - (k === last ? 1 : 0)) / ((n - 1) * BW) : 0, now = c[k] / (n * BW);
      const h = lerp(was, now, p);
      if (h <= 0) continue;
      const x0 = TX(E0 + k * BW), x1 = TX(E0 + (k + 1) * BW), y1 = PY(h);
      ctx.save(); ctx.globalAlpha *= DA; ctx.fillStyle = C.steel2; ctx.fillRect(x0, y1, x1 - x0, PY(0) - y1); ctx.restore();
      line([[x0, PY(0)], [x0, y1], [x1, y1], [x1, PY(0)]], { color: C.navy, width: 1.1, alpha: DA });
    }
    if (n >= D.nfit) {
      const q = n > D.nfit ? p : 1, m = lerp(XB[n - 1], XB[n], q), s = lerp(SD[n - 1], SD[n], q);
      const pts = []; for (let i = 0; i <= 200; i++) { const x = 20 + 24 * i / 200; pts.push([TX(x), PY(pdf(x, m, s))]); }
      line(pts, { color: C.accent, width: 2.6, alpha: DA * (n > D.nfit ? 1 : p) });
    }
  });
  math('n = ' + n, RX + 10, TY + 21, { size: 15, color: C.body, alpha: DA });
  const fa = DA * (n > D.nfit ? 1 : p) * (n >= D.nfit ? 1 : 0);
  text('Fitted normal model', RX + PW - 10, TY + 21, { size: 15, color: C.accent, align: 'right', alpha: fa });
}

/* ------------------------------------------------------------ Stochastic processes */
const WX = v => LX + (v + 4) / 168 * PW, WY = v => BY + PH - (v + 8.4) / 16.8 * PH;
const BAND = [];
for (let j = 0; j <= NSTEP; j++) BAND.push([WX(j), WY(Z * D.rws * Math.sqrt(j))]);
for (let j = NSTEP; j >= 0; j--) BAND.push([WX(j), WY(-Z * D.rws * Math.sqrt(j))]);
const PATHC = [C.navy, C.accent, C.blue, C.sky];      // his colours, path by path
function panelW() {
  title('Stochastic processes', LX + PW / 2, BY - 18, C.sky, .08);
  const g = axes({ x: LX, y: BY, w: PW, h: PH, xlim: [-4, 164], ylim: [-8.4, 8.4], xticks: [0, 40, 80, 120, 160],
                   yticks: [-8, -4, 0, 4, 8], xlabel: '\\rm{Step}\\ n', ylabel: '\\rm{Sensor bias (mm)}',
                   progress: seg(.1, .35), ylabelGap: 44, labelSize: 16 });
  const ba = seg(.2, .3);
  if (ba > 0) { ctx.save(); ctx.globalAlpha *= ba; ctx.fillStyle = C.steel; ctx.beginPath(); ctx.moveTo(BAND[0][0], BAND[0][1]); for (const q of BAND) ctx.lineTo(q[0], q[1]); ctx.closePath(); ctx.fill(); ctx.restore(); }
  line([[WX(-4), WY(0)], [WX(164), WY(0)]], { color: C.guide, width: 1, dash: [5, 4], progress: seg(.2, .35) });
  const bl = lab(.5);
  text('Pointwise 95% band', WX(2), WY(6.2) + rise(bl), { size: 15, color: C.body, alpha: bl });
  if (U < 0 || DA <= 0) return;
  const sw = NSTEP * clamp(U / (RUN + FALL)), j1 = Math.floor(sw), f = sw - j1;
  g.inside(() => {
    for (const k of [0, 2, 3, 1]) {
      const o = k * (NSTEP + 1), pts = [];
      for (let j = 0; j <= j1; j++) pts.push([WX(j), WY(WK[o + j])]);
      if (j1 < NSTEP && f > 0) pts.push([WX(j1 + f), WY(lerp(WK[o + j1], WK[o + j1 + 1], f))]);
      if (pts.length > 1) line(pts, { color: PATHC[k], width: k === 1 ? 2.2 : 1.8, alpha: DA });
    }
  });
}

/* ------------------------------------------------------------ Estimation */
const EX = v => RX + (v + .1) / 3.2 * PW, EY = v => BY + PH - (v - 26) / 12 * PH;
const L10 = Math.LN10;
function panelE() {
  title('Estimation', RX + PW / 2, BY - 18, C.blue, .12);
  const ap = seg(.14, .35), aa = clamp(ap * 1.4);
  const g = axes({ x: RX, y: BY, w: PW, h: PH, xlim: [-.1, 3.1], ylim: [26, 38], xticks: [0, 1, 2, 3],
                   yticks: [28, 32, 36], xfmt: v => ['1', '10', '100', '1000'][v], yfmt: () => '',
                   xlabel: '\\rm{Number of tests}\\ n', progress: ap, labelSize: 16 });
  // the log axis's minor ticks, and the values on the right
  for (let d = 0; d < 3; d++) for (let k = 2; k <= 9; k++) {
    const x = EX(d + Math.log10(k));
    line([[x, BY + PH], [x, BY + PH - 3]], { color: C.ink, width: 1, alpha: aa });
    line([[x, BY], [x, BY + 3]], { color: C.ink, width: 1, alpha: aa });
  }
  for (const v of [28, 32, 36]) math(fmt(v), RX + PW + 8, EY(v) + 15 * .35, { size: 15, alpha: aa });
  math('\\rm{Mean strength (MPa)}', RX + PW + 46, BY + PH / 2, { size: 16, align: 'center', rot: -Math.PI / 2, alpha: aa });
  // the running mean and its 95% interval, test by test; over the interval, the unknown
  const n = U < 0 || DA <= 0 ? 0 : landed(), p = n ? arrive(n) : 0, ea = DA * (n > 1 ? 1 : p);
  const top = [], bot = [], mid = [];
  for (let m = 1; m <= n; m++) {
    let x = Math.log(m) / L10, c = XB[m], h = Z * SG / Math.sqrt(m);
    if (m === n && n > 1) {
      const x0 = Math.log(m - 1) / L10, h0 = Z * SG / Math.sqrt(m - 1);
      x = lerp(x0, x, p); c = lerp(XB[m - 1], c, p); h = lerp(h0, h, p);
    }
    top.push([EX(x), EY(c + h)]); bot.push([EX(x), EY(c - h)]); mid.push([EX(x), EY(c)]);
  }
  if (n) g.inside(() => {
    ctx.save(); ctx.globalAlpha *= ea; ctx.fillStyle = C.steel; ctx.beginPath();
    ctx.moveTo(top[0][0], top[0][1]); for (const q of top) ctx.lineTo(q[0], q[1]);
    for (let i = bot.length - 1; i >= 0; i--) ctx.lineTo(bot[i][0], bot[i][1]);
    ctx.closePath(); ctx.fill(); ctx.restore();
  });
  line([[RX, EY(MU)], [RX + PW, EY(MU)]], { color: C.blue, width: 1.4, dash: [6, 4], progress: seg(.25, .35) });
  const ta = lab(.5);
  text('Fixed true mean', RX + PW - 10, EY(33.1) + rise(ta), { size: 15, color: C.blue, align: 'right', alpha: ta });
  if (!n) return;
  g.inside(() => {
    if (mid.length > 1) line(mid, { color: C.navy, width: 2.4, alpha: ea });
    const e = mid[mid.length - 1], u = top[top.length - 1], l = bot[bot.length - 1];
    line([[e[0], u[1]], [e[0], l[1]]], { color: C.navy, width: 1.4, alpha: ea });
    line([[e[0] - 4, u[1]], [e[0] + 4, u[1]]], { color: C.navy, width: 1.4, alpha: ea });
    line([[e[0] - 4, l[1]], [e[0] + 4, l[1]]], { color: C.navy, width: 1.4, alpha: ea });
    dot(e[0], e[1], 3.6, { color: '#fff', fill: C.navy, width: 1.2, alpha: ea });
  });
  const ca = DA * clamp((n - 14) / 6);
  text('95% CI', EX(1.35), EY(29.2), { size: 15, color: C.body, alpha: ca });
}

/* ------------------------------------------------------------ his arrows */
function arrows() {
  const o = { width: 1.6, head: 10, color: C.ink };
  const ya = TY + PH / 2 + 10, yb = BY + PH / 2 + 10, gx0 = LX + PW + 8, gx1 = RX - 8, cx = (gx0 + gx1) / 2;
  growArrow(gx1, ya, gx0, ya, seg(.35, .3), o);                      // Statistics to Probability
  growArrow(LX + PW / 2, TY + PH + 60, LX + PW / 2, BY - 44, seg(.4, .3), o);   // Probability to Stochastic processes
  growArrow(RX + PW / 2, TY + PH + 60, RX + PW / 2, BY - 44, seg(.45, .3), o);  // Statistics to Estimation
  growArrow(gx0, yb, gx1, yb, seg(.5, .3), o);                       // Stochastic processes to Estimation
  const a1 = lab(.55), a2 = lab(.65), w = { size: 15, color: C.body, align: 'center', italic: true };
  text('learn and', cx, ya - 28 + rise(a1), { ...w, alpha: a1 });
  text('check a model', cx, ya - 10 + rise(a1), { ...w, alpha: a1 });
  text('model +', cx, yb - 28 + rise(a2), { ...w, alpha: a2 });
  text('observations', cx, yb - 10 + rise(a2), { ...w, alpha: a2 });
}

function draw() {
  clock();
  panelP(); panelS(); panelW(); panelE();
  arrows();
}
boot();
"""


def fit_start(x):
    """The first n from which the fitted curve and the histogram stay clear of
    the words at the top right of Statistics ("Fitted normal model", x from
    about 34.5 MPa, density above 0.165), so the fit and its name arrive
    together and nothing crosses them after."""
    n_all, xb, sd = running(x)
    edges = E0 + BW * np.arange(NB + 1)
    ok = np.zeros(N + 1, bool)
    grid = np.linspace(34.4, 44, 400)
    for n in range(5, N + 1):
        c, _ = np.histogram(x[:n], edges)
        h = c / (n * BW)
        under = (edges[1:] > 34.4)
        ok[n] = h[under].max() < 0.16 and stats.norm.pdf(grid, xb[n - 1], sd[n - 1]).max() < 0.16
    for n in range(5, N + 1):
        if ok[n:].all():
            return n
    raise RuntimeError("no fit start")


def validate(x, W, nfit, data):
    """Closed forms and his slides against the model, the page's own numbers
    against numpy, and the overlap check over a whole loop; writes
    pr_overview.check.txt and prints it."""
    import sp_model
    edges = E0 + BW * np.arange(NB + 1)
    n, xb, sd = running(x)
    L = []
    say = L.append
    say("nf-pr-overview: the probability deck's slide 1, four connected questions in motion")
    say("generator: tools/numfig/pr_overview.py; used as the deck's card on the Big Picture page")
    say("(tools/bp_art.py); in no document, so no fragment")
    say("")
    say("MODEL (his running examples)")
    say(f"  Probability: one cylinder's strength X ~ N({MU:g}, {SIGMA:g}^2) MPa (slides 16 to 21: sigma = 3 MPa,")
    say(f"    mean 32 MPa). Its lower 5% (slide 13): x < mu + sigma z_0.05 = {Q05:.4f} MPa.")
    say(f"  The tests: N = {N} draws from the model, numpy default_rng(seed={SEED}).normal({MU:g}, {SIGMA:g}),")
    say("    the same every run. The seed is the first from 1 (the slide's number) whose running")
    say("    95% interval holds the true mean at every n up to N, so the one path the reader sees")
    say(f"    shows the rule and not its 5% exception; seed 1 misses it for {misses(tests(1))} of its {N} n.")
    shares = np.mean([covers_all(tests(s)) for s in range(1, 201)])
    say(f"    Such paths are common: {shares * 100:.0f} % of seeds 1 to 200 hold the mean at every n <= {N}.")
    say(f"  Statistics: the same tests as they land, a histogram in his 2 MPa bins ({E0:g} to {E0 + NB * BW:g} MPa),")
    say("    as a density (count / (n x 2 MPa)) on the model's axes, and the normal model fitted to")
    say(f"    them (sample mean, sample SD with n - 1), drawn from n = {nfit}: the first n from which")
    say("    neither the fit nor the bars reach the words at the top right, so the fit and its name")
    say("    arrive together.")
    say(f"  Stochastic processes: his random walk of sensor bias (slide 51): {RW_K} paths,")
    say(f"    X_n = X_(n-1) + e_n, e_n ~ N(0, {RW_SIGMA:g}^2) mm, X_0 = 0, {RW_N} steps, default_rng({RW_SEED}),")
    say(f"    in his pointwise 95% band +-{Z95:.4f} x {RW_SIGMA:g} sqrt(n) mm about E[X_n] = X_0.")
    say(f"  Estimation: the unknown mean from the same tests, the running mean xbar_n and its 95%")
    say(f"    interval xbar_n +- {Z95:.4f} sigma / sqrt(n), sigma = {SIGMA:g} MPa known (slide 17), on a log n")
    say("    axis (his slide 34 draws its running mean so).")
    say("")
    say("VALIDATION")
    z05 = -1.6448536269514722                     # the textbook 5 % point of N(0, 1)
    say(f"  1. The lower 5 % point: scipy {Q05:.6f} MPa against mu + sigma z_0.05 = {MU + SIGMA * z05:.6f}")
    say(f"     (z_0.05 = -1.644854); the model's mass below it {stats.norm.cdf(Q05, MU, SIGMA):.6f}.")
    below = (x < Q05).mean()
    say(f"     Share of the {N} tests below it: {below * 100:.1f} % (the model: 5 %, binomial SE"
        f" {np.sqrt(.05 * .95 / N) * 100:.2f} %, so {(below - .05) / np.sqrt(.05 * .95 / N):+.1f} SE).")
    ks = stats.kstest(x, "norm", args=(MU, SIGMA))
    c, _ = np.histogram(x, edges)
    pk = np.diff(stats.norm.cdf(edges, MU, SIGMA))
    keep = N * pk >= 5
    obs = np.r_[c[keep], c[~keep].sum()]
    exp = np.r_[N * pk[keep], N * pk[~keep].sum() + N * (1 - pk.sum())]
    chi2 = ((obs - exp) ** 2 / exp).sum()
    dof = obs.size - 1
    say(f"  2. The tests against their model: Kolmogorov-Smirnov D = {ks.statistic:.4f}, p = {ks.pvalue:.2f};")
    say(f"     histogram chi-square {chi2:.1f} on {dof} degrees of freedom, p = {stats.chi2.sf(chi2, dof):.2f}")
    say(f"     (tail bins merged to 5 expected). Mean {xb[-1]:.3f} MPa, SD {sd[-1]:.3f} MPa (the model: 32, 3).")
    se25 = SIGMA / np.sqrt(25)
    say(f"  3. The interval at n = 25: SE = sigma / sqrt(25) = {se25:.3f} MPa and half width"
        f" {1.96 * se25:.3f} MPa (with 1.96),")
    say(f"     his slide 17's 0.6 and 1.176; with z = {Z95:.6f}: {Z95 * se25:.4f} MPa. At n = {N}:"
        f" {Z95 * SIGMA / np.sqrt(N):.4f} MPa.")
    rng = np.random.default_rng(0)
    cov = []
    for m in (1, 25, N):
        means = rng.normal(MU, SIGMA, (20000, m)).mean(axis=1)
        cov.append((m, np.mean(np.abs(means - MU) <= Z95 * SIGMA / np.sqrt(m))))
    say("     Coverage over 20000 repeated samples: " + ", ".join(f"n = {m}: {v * 100:.2f} %" for m, v in cov)
        + " (95 %).")
    say(f"     The figure's path: xbar_n within its interval of mu at all {N} n: {covers_all(x)}.")
    sys.path[:0] = [os.path.join(common.ROOT, "tools", "deck"), os.path.join(common.ROOT, "tools", "deck", "src")]
    import s051
    say(f"  4. The walks are his: slide 51's four paths (tools/deck/src/s051.py) against these, largest")
    say(f"     difference {np.abs(s051.PATHS - W).max():.1e} mm; his band's end +-1.96 x 0.3 sqrt(160) ="
        f" {Z95 * RW_SIGMA * np.sqrt(RW_N):.3f} mm (his 7.4).")
    mc = np.cumsum(np.random.default_rng(1).normal(0, RW_SIGMA, (100000, RW_N)), axis=1)
    for s in (40, RW_N):
        v = mc[:, s - 1].var()
        inside = np.mean(np.abs(mc[:, s - 1]) <= Z95 * RW_SIGMA * np.sqrt(s))
        say(f"     Var(X_{s}) over 100000 walks {v:.4f} mm^2 against n sigma^2 = {s * RW_SIGMA ** 2:.4f}"
            f" ({v / (s * RW_SIGMA ** 2) - 1:+.2%}); inside the band {inside * 100:.2f} %.")
    # the page's own numbers
    exprs = ["Array.from(XB.slice(1))", "Array.from(SD.slice(1))", f"Array.from(counts({N}))",
             f"Array.from({{length: NT}}, (_, k) => count(rel(k + 1)))",
             f"Array.from({{length: NT}}, (_, k) => count(rel(k + 1) - 1e-7))",
             "(() => { t = POSTER_T; clock(); return landed(); })()"]
    pxb, psd, pc, at, before, npost = sp_model.check_page(NAME, exprs)
    x32 = x.astype(np.float32).astype(float)
    _, xb32, sd32 = running(x32)
    c32, _ = np.histogram(x32, edges)
    say("  5. The page: it computes the running mean and SD (Welford) and the histogram from the tests")
    say(f"     it carries (float32): against numpy on the same values, largest differences"
        f" {np.abs(pxb - xb32).max():.1e} and {np.abs(psd - sd32).max():.1e} MPa;")
    say(f"     its counts at n = {N} equal numpy's: {bool(np.array_equal(pc, c32))}; float32 against the draws:"
        f" {np.abs(x32 - x).max():.1e} MPa.")
    ok = np.array_equal(at, np.arange(1, N + 1)) and np.array_equal(before, np.arange(0, N))
    say(f"     Its clock: test i leaves at RUN ln i / ln N and the count reached there is i (i - 1 just"
        f" before), all {N}: {ok}.")
    say("")
    say("DISPLAY")
    say(f"  The clock: the first test leaves the model at {T0} s; test i leaves {RUN:g} ln i / ln {N} s later,")
    say(f"  so Estimation's log n axis is crossed at one speed, one test at a time at first and")
    say(f"  {N * np.log(N) / RUN:.0f} a second at the end. Each drops from the density curve at its value to the")
    say(f"  axis in {FALL} s, so the tests in the air lie evenly under the curve, as draws from the")
    say(f"  model do; it lands, leaves a tick for 1 s, and joins Statistics and Estimation. The walks")
    say(f"  take the same {RUN + FALL:g} s for their {RW_N} steps. The finished picture holds {HOLD} s, fades in"
        f" {FADE} s,")
    say(f"  and the loop starts again after {GAP} s: {PER:.2f} s a loop. Its intro is done by 1.0 s.")
    say(f"  The printed frame, t = {data['poster']} s: {int(npost)} tests landed, the rest falling, the walks"
        f" {data['poster'] - T0:.2f} s along.")
    say("")
    # the overlap check over a whole loop, beyond the poster the still is checked to
    times = [round(.25 * k, 2) for k in range(1, int(np.ceil((T0 + PER) / .25)) + 1)]
    res = common.overlaps(NAME, times)
    bad = {k: v for k, v in res.items() if v["labels"] or v["crossings"]}
    say("OVERLAPS (engine.js ?overlap, common.overlaps)")
    say(f"  checked at the poster and every 0.25 s from 0.25 to {times[-1]} s ({len(times)} moments, a whole")
    say(f"  loop and its intro): label pairs that meet {sum(len(v['labels']) for v in res.values())}, strokes"
        f" through a label {sum(len(v['crossings']) for v in res.values())}.")
    for k, v in bad.items():
        say(f"    {k}: {v}")
    say("  No label sits on a knockout; the falling tests stay under the curve, below its words.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(HERE, "pr_overview.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return bad


def build():
    assert pick_seed() == SEED
    x = tests()
    assert x.min() > E0 and x.max() < E0 + NB * BW
    W = walks()
    nfit = fit_start(x)
    u_post = RUN * np.log(N_POSTER) / np.log(N) + FALL + 0.3
    data = dict(
        x=common.f32(x), walk=common.f32(W.ravel()), nk=RW_K, nstep=RW_N, rws=RW_SIGMA,
        mu=MU, sigma=SIGMA, q05=Q05, z=Z95, e0=E0, bw=BW, nb=NB, nfit=nfit,
        t0=T0, run=RUN, fall=FALL, hold=HOLD, fade=FADE, per=PER, poster=round(T0 + u_post, 3),
    )
    title = "Probability, statistics and estimation"
    aria = ("Four connected questions, each a computation in motion: tests of concrete strength fall out of a "
            "normal model (probability), pile into a histogram that a fitted normal model settles on "
            "(statistics), and give a running mean whose 95% interval closes on the true mean (estimation), "
            "while four random walks of sensor bias spread inside their 95% band (stochastic processes). "
            "Arrows link the four as on the deck's first slide.")
    common.build_html(NAME, title, aria, 1000, 562, data, JS)
    print("still:", common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.0, 3.5, 5.0, 7.0, 8.5, 10.5, 12.0, 13.0]))
    bad = validate(x, W, nfit, data)
    if bad:
        raise RuntimeError(f"nf-{NAME}: ink collides: {bad}")
    return x, W, nfit, data


if __name__ == "__main__":
    build()
