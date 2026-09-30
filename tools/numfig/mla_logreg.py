"""Figure 9 of the machine learning guide (stem image6): logistic regression.

Model: 40 tumors, diameter x (mm), label 1 malignant, 0 benign, drawn from
two normal distributions (seed fixed). The fit maximises the likelihood of

    p(x) = 1 / (1 + exp(-(b0 + b1 x)))

by Newton's method (iteratively reweighted least squares) to machine
precision, checked against scikit-learn. The score s = b0 + b1 x is drawn as
the figure's top axis: the sigmoid maps it to a probability, and s = 0, p =
0.5, is the threshold. The page moves a probe along the computed curve
through four of the tumors; its probability and class are read off the
fitted model every frame.

Run: python tools/numfig/mla_logreg.py [--look]
"""
import sys

import numpy as np
from scipy.stats import norm
from sklearn.linear_model import LogisticRegression

import common
from mla_shared import LIB, report

NAME, STEM = "mla-logreg", "mla_logreg"
SEED, N0, N1 = 3, 22, 18
MU0, SD0, MU1, SD1 = 13.0, 4.0, 26.0, 6.0          # mm: benign, malignant
LO, HI = 4.0, 44.0

rng = np.random.default_rng(SEED)
x0 = np.clip(rng.normal(MU0, SD0, N0), LO, HI)
x1 = np.clip(rng.normal(MU1, SD1, N1), LO, HI)
x = np.round(np.r_[x0, x1], 1)
y = np.r_[np.zeros(N0), np.ones(N1)]
X = np.c_[np.ones_like(x), x]


def irls(X, y, tol=1e-15):
    b = np.zeros(X.shape[1])
    for it in range(1, 100):
        p = 1 / (1 + np.exp(-X @ b))
        g = X.T @ (y - p)
        Hs = X.T @ (X * (p * (1 - p))[:, None])
        step = np.linalg.solve(Hs, g)
        b = b + step
        if np.abs(step).max() < tol:
            return b, it, g, Hs
    raise RuntimeError("IRLS did not converge")


b, iters, grad, Hs = irls(X, y)
b0, b1 = b
p = 1 / (1 + np.exp(-(b0 + b1 * x)))
xs = -b0 / b1
pred = p > 0.5
mis = int((pred != (y == 1)).sum())
ll = float(np.sum(y * np.log(p) + (1 - y) * np.log(1 - p)))

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-logreg: Figure 9, logistic regression")
say("")
say("DATA")
say(f"  {N0} benign tumors, diameter ~ N({MU0:g}, {SD0:g}) mm; {N1} malignant ~ N({MU1:g}, {SD1:g}) mm;")
say(f"  clipped to [{LO:g}, {HI:g}] mm, rounded to 0.1 mm; seed {SEED}")
say("  benign:    " + " ".join(f"{v:.1f}" for v in x[:N0]))
say("  malignant: " + " ".join(f"{v:.1f}" for v in x[N0:]))
say("")
say("FIT: maximum likelihood by Newton (IRLS)")
say(f"  b0 = {b0:.10f}, b1 = {b1:.10f} per mm, after {iters} Newton steps")
say(f"  log likelihood {ll:.6f}; threshold (p = 0.5) at x* = -b0/b1 = {xs:.4f} mm")
say("")
say("CHECK 1: against scikit-learn (no penalty)")
sk = LogisticRegression(C=np.inf, solver="newton-cg", tol=1e-12, max_iter=1000).fit(x[:, None], y)
say(f"  sklearn: b0 = {sk.intercept_[0]:.10f}, b1 = {sk.coef_[0,0]:.10f}"
    f"  |diff| {abs(sk.intercept_[0]-b0):.1e}, {abs(sk.coef_[0,0]-b1):.1e}")
say("")
say("CHECK 2: the optimum (score equations and curvature)")
say(f"  gradient X'(y - p) = [{grad[0]:.1e}, {grad[1]:.1e}]; sum p = {p.sum():.10f} = number malignant {N1}")
say(f"  Hessian eigenvalues {np.linalg.eigvalsh(Hs)[0]:.4f}, {np.linalg.eigvalsh(Hs)[1]:.2f} > 0: a maximum")
say("")
say("CHECK 3: the threshold and the slope of the S (closed form)")
say(f"  p(x*) = {1/(1+np.exp(-(b0+b1*xs))):.15f} (exactly 0.5)")
h = 1e-6
dp = (1 / (1 + np.exp(-(b0 + b1 * (xs + h)))) - 1 / (1 + np.exp(-(b0 + b1 * (xs - h))))) / (2 * h)
say(f"  dp/dx at x* = {dp:.8f} per mm, b1/4 = {b1/4:.8f}")
say("")
say("CHECK 4: against the best possible boundary for the distributions the data came from")
pi0, pi1 = N0 / (N0 + N1), N1 / (N0 + N1)
f = lambda v: pi1 * norm.pdf(v, MU1, SD1) - pi0 * norm.pdf(v, MU0, SD0)
from scipy.optimize import brentq  # noqa: E402
xb = brentq(f, MU0, MU1)
say(f"  Bayes boundary (priors {N0}/{N0+N1}, {N1}/{N0+N1}): {xb:.3f} mm; fitted x* = {xs:.3f} mm")
say(f"  misclassified at p = 0.5: {mis} of {N0+N1}")
say("")
# probe stops: four tumors, from benign to malignant and back
order = np.argsort(x)


def near(v):
    return int(order[np.argmin(np.abs(x[order] - v))])


stops = [near(v) for v in (11.0, 17.5, 23.5, 31.0)]
say("PAGE")
say("  the probe rests at four tumors and glides between them along the fitted curve:")
for i in stops:
    say(f"    x = {x[i]:.1f} mm, p = {p[i]:.4f}, label {int(y[i])},"
        f" classified {'positive' if p[i] > 0.5 else 'negative'}")
report(STEM, L)

DATA = {"x": x, "y": y, "b0": b0, "b1": b1, "xs": xs, "stops": [float(x[i]) for i in stops],
        "n0": N0, "n1": N1}

JS = LIB + r"""
const D = DATA, n = D.x.length;
const POSTER_T = 5.8;
const P = x => 1 / (1 + Math.exp(-(D.b0 + D.b1 * x)));
const A = {x: 96, y: 86, w: 862, h: 356};

/* rows of marks at p = 0 and p = 1: a mark that would overlap its left
   neighbour moves to the next free level, alternately toward the curve and
   away from it, so every tumor stays visible at its own diameter */
const LEV = new Array(n).fill(0), STEP = [0, 1, -1, 2, -2];
(function () {
  for (const lab of [0, 1]) {
    const idx = []; for (let i = 0; i < n; i++) if (D.y[i] === lab) idx.push(i);
    idx.sort((i, j) => D.x[i] - D.x[j]);
    const last = [];                              // the last diameter placed on each level
    for (const i of idx) {
      let k = 0; while (last[k] !== undefined && D.x[i] - last[k] < .55) k++;
      LEV[i] = STEP[Math.min(k, 4)]; last[k] = D.x[i];
    }
  }
})();

function draw() {
  const g = axes({...A, xlim: [0, 45], ylim: [-.06, 1.06], xticks: [0, 5, 10, 15, 20, 25, 30, 35, 40, 45],
    yticks: [0, .25, .5, .75, 1], yfmt: v => v === 0 ? '0' : v === 1 ? '1' : String(v),
    xlabel: '\\rm{tumor diameter}\\ x\\ \\rm{(mm)}', ylabel: '\\rm{probability of malignant}', ylabelGap: 58,
    progress: seg(0, .35), box: false});
  const fa = seg(0, .35);
  line([[A.x, A.y], [A.x + A.w, A.y]], {width: 1.3, progress: fa});
  line([[A.x + A.w, A.y], [A.x + A.w, A.y + A.h]], {width: 1.3, progress: fa});
  // the score, the model's weighted input, as the top axis
  const sa = arrive(.12);
  for (let s = -4; s <= 8; s += 2) {
    const xx = (s - D.b0) / D.b1; if (xx < 0 || xx > 45) continue;
    line([[g.X(xx), A.y], [g.X(xx), A.y + 5]], {width: 1.1, alpha: sa});
    math(fmt(s), g.X(xx), A.y - 8, {size: 15, align: 'center', alpha: sa});
  }
  math('\\rm{score}\\ b_{0} + b_{1}x', A.x + A.w / 2, A.y - 32, {size: 17, align: 'center', alpha: sa});

  // classified positive: where the curve is above one half
  const za = arrive(.5);
  box(g.X(D.xs), A.y, A.x + A.w - g.X(D.xs), A.h, {fill: C.steel, alpha: .75 * za});
  text('classified positive', g.X(D.xs) + 14, g.Y(.9), {size: 15, color: C.navy, alpha: za});
  text('classified negative', g.X(D.xs) - 14, g.Y(.9), {size: 15, color: C.body, align: 'right', alpha: za});
  // the threshold and where the curve crosses it
  const ta = seg(.42, .3);
  line([[A.x, g.Y(.5)], [A.x + A.w, g.Y(.5)]], {color: C.guide, width: 1, dash: [5, 4], progress: ta});
  line([[g.X(D.xs), A.y + A.h], [g.X(D.xs), A.y]], {color: C.guide, width: 1, dash: [5, 4], progress: ta});
  text('0.5 threshold', A.x + A.w - 10, g.Y(.5) - 8, {size: 15, color: C.body, align: 'right', alpha: arrive(.55)});

  // the fitted sigmoid
  const pts = [];
  for (let k = 0; k <= 300; k++) { const xx = 45 * k / 300; pts.push([g.X(xx), g.Y(P(xx))]); }
  g.inside(() => line(pts, {color: C.blue, width: 2.6, progress: seg(.2, .42)}));

  // the tumors at their labels
  for (let i = 0; i < n; i++) {
    const yy = D.y[i] ? g.Y(1) + 8.5 * LEV[i] : g.Y(0) - 8.5 * LEV[i];
    mark(g.X(D.x[i]), yy, D.y[i] ? 1 : 0, arrive(.04 + .26 * D.x[i] / 45));
  }

  // the probe: glides from tumor to tumor along the computed curve
  const c = cycle(.6, D.stops.map((v, k) => [v, k === D.stops.length - 1 ? 1.2 : 1.2]), .75);
  const xp = cyc(c), pp = P(xp), qa = arrive(.62);
  if (qa > 0) {
    const px = g.X(xp), py = g.Y(pp);
    line([[px, A.y + A.h], [px, py]], {color: C.accent, width: 1.2, dash: [4, 3], alpha: qa});
    line([[A.x, py], [px, py]], {color: C.accent, width: 1.2, dash: [4, 3], alpha: qa});
    dot(px, py, 6, {color: '#fff', fill: C.accent, width: 1.6, alpha: qa});
    // the readout, under the legend
    const rx = A.x + 16, ry = A.y + 140;
    math('x = ' + xp.toFixed(1) + '\\ \\rm{mm},\\ \\ p = ' + pp.toFixed(2), rx, ry, {size: 16, alpha: qa});
    text(pp > .5 ? 'classified positive' : 'classified negative', rx, ry + 22, {size: 16, color: C.accent, alpha: qa});
  }
  legend(A.x + 14, A.y + 36, [
    [(x, y) => mark(x, y + 1, 1, 1), 'malignant (label 1)'],
    [(x, y) => mark(x, y + 1, 0, 1), 'benign (label 0)'],
    [(x, y) => line([[x - 12, y + 1], [x + 12, y + 1]], {color: C.blue, width: 2.6}), 'fitted sigmoid'],
  ], arrive(.6));
  math(`\\rm{40 simulated tumors (${D.n0} benign, ${D.n1} malignant); maximum likelihood:} b_0 = ${nfmt(D.b0, 2)}, ` +
       `b_1 = ${D.b1.toFixed(3)} \\rm{per mm; threshold at ${D.xs.toFixed(1)} mm}`, 18, H - 14,
       {size: 14, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = ("Figure 9: Logistic regression: the S-shaped sigmoid curve maps any input to a 0-1 "
         "probability")
ARIA = ('Forty tumors by diameter, malignant ones along the top at probability one and benign ones along the '
        'bottom at zero, with the fitted sigmoid and a dashed 0.5 threshold. Tumors larger than about 19 mm, '
        'where the curve is above the threshold, are classified positive, and a marker moving along the curve '
        'reads off each probability.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 540, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.2, 0.5, 0.8, 1.4, 2.2, 4.2]))
