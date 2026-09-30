"""Figure 8 of the machine learning guide (stem image5): linear regression.

Model: 14 house sales, price against floor area, drawn from a stated line
plus Gaussian noise (seed fixed) and rounded as listings are (10 ft^2, 1 k$).
The fit is ordinary least squares in closed form,

    b1 = Sxy / Sxx,  b0 = ybar - b1 xbar,

checked against numpy's lstsq and scikit-learn. Panel (a) draws each residual
r_i = y_i - (b0 + b1 x_i) and its square (side |r_i| on the price scale, so
its area is r_i^2); panel (b) is the sum of those squares as the slope
changes, the intercept re-chosen for each slope (the line then passes through
the mean point), SSR(b) = Syy - 2 b Sxy + b^2 Sxx: a parabola whose lowest
point is the least squares slope. The page tilts the line about the mean
point and back; every square and the marker on the parabola follow from the
data at each frame.

Run: python tools/numfig/mla_linreg.py [--look]
"""
import sys

import numpy as np
from sklearn.linear_model import LinearRegression

import common
from mla_shared import LIB, house_data, report

NAME, STEM = "mla-linreg", "mla_linreg"
SEED, N = 2, 14
B0_TRUE, B1_TRUE, SIGMA = 40.0, 0.170, 38.0        # k$, k$ per ft^2, k$

x, y = house_data()                                                # ft^2, k$ (seed 2)

xb, yb = x.mean(), y.mean()
Sxx = ((x - xb) ** 2).sum()
Sxy = ((x - xb) * (y - yb)).sum()
Syy = ((y - yb) ** 2).sum()
b1 = Sxy / Sxx
b0 = yb - b1 * xb
r = y - (b0 + b1 * x)
ssr = (r ** 2).sum()
DELTA = 0.045                                                      # k$ per ft^2, the tilt


def ssr_of(b):
    return Syy - 2 * b * Sxy + b * b * Sxx


# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-linreg: Figure 8, linear regression (least squares)")
say("")
say("DATA")
say(f"  {N} house sales, simulated: price = {B0_TRUE:g} k$ + {B1_TRUE*1e3:g} $/ft^2 x area + e,"
    f" e ~ N(0, {SIGMA:g} k$), seed {SEED}")
say(f"  area evenly spread 1000..2800 ft^2 (+-40 ft^2), rounded to 10 ft^2; price rounded to 1 k$")
say("  area (ft^2): " + " ".join(f"{v:.0f}" for v in x))
say("  price (k$):  " + " ".join(f"{v:.0f}" for v in y))
say("")
say("FIT (closed form)")
say(f"  b1 = Sxy/Sxx = {b1*1e3:.4f} $/ft^2,  b0 = ybar - b1 xbar = {b0:.4f} k$")
A = np.c_[np.ones(N), x]
(l0, l1), *_ = np.linalg.lstsq(A, y, rcond=None)
sk = LinearRegression().fit(x[:, None], y)
say("")
say("CHECK 1: closed form against two independent solvers")
say(f"  numpy lstsq:          b0 = {l0:.10f}, b1 = {l1:.12f}  |diff| {abs(l0-b0):.1e}, {abs(l1-b1):.1e}")
say(f"  sklearn Linear...:    b0 = {sk.intercept_:.10f}, b1 = {sk.coef_[0]:.12f}"
    f"  |diff| {abs(sk.intercept_-b0):.1e}, {abs(sk.coef_[0]-b1):.1e}")
say("")
say("CHECK 2: the normal equations (residuals sum to zero and are orthogonal to x)")
say(f"  sum r = {r.sum():.2e} k$,  sum r x = {(r*x).sum():.2e} k$ ft^2")
say("")
say("CHECK 3: the parabola of panel (b), SSR(b) = Syy - 2 b Sxy + b^2 Sxx")
bg = np.linspace(b1 - 0.08, b1 + 0.08, 160001)
direct = [((y - yb - bb * (x - xb)) ** 2).sum() for bb in (b1 - DELTA, b1, b1 + DELTA)]
say(f"  brute force argmin over b (step 1e-6): {bg[np.argmin(ssr_of(bg))]*1e3:.4f} $/ft^2"
    f" (closed form {b1*1e3:.4f})")
say(f"  SSR at b1 - d, b1, b1 + d (d = {DELTA*1e3:g} $/ft^2): direct sum"
    f" {direct[0]:.3f}, {direct[1]:.3f}, {direct[2]:.3f}")
say(f"                                         parabola   {ssr_of(b1-DELTA):.3f}, {ssr_of(b1):.3f},"
    f" {ssr_of(b1+DELTA):.3f}")
say(f"  minimum SSR = Syy - Sxy^2/Sxx = {Syy - Sxy**2/Sxx:.3f} (k$)^2 = sum r^2 = {ssr:.3f}")
say(f"  tilt by +-d raises it by d^2 Sxx = {DELTA**2*Sxx:.1f} (k$)^2 either way")
say("")
say("CHECK 4: against the line the data were drawn from")
s2 = ssr / (N - 2)
se1 = np.sqrt(s2 / Sxx)
se0 = np.sqrt(s2 * (1 / N + xb ** 2 / Sxx))
say(f"  b1 = {b1*1e3:.1f} +- {se1*1e3:.1f} $/ft^2 (1 s.e.), true {B1_TRUE*1e3:g}: "
    f"{abs(b1-B1_TRUE)/se1:.2f} s.e. away")
say(f"  b0 = {b0:.1f} +- {se0:.1f} k$, true {B0_TRUE:g}: {abs(b0-B0_TRUE)/se0:.2f} s.e. away")
say(f"  residual s = sqrt(SSR/(n-2)) = {np.sqrt(s2):.1f} k$ (sigma used {SIGMA:g})")
say("")
say("PAGE")
say("  the line tilts about the mean point (xbar, ybar) ="
    f" ({xb:.1f} ft^2, {yb:.2f} k$) to b1 -+ {DELTA*1e3:g} $/ft^2 and back;")
say("  squares, segments and the marker on (b) are computed from the data every frame.")
report(STEM, L)

DATA = {"x": x, "y": y, "xb": xb, "yb": yb, "b0": b0, "b1": b1, "d": DELTA,
        "Sxx": Sxx, "Sxy": Sxy, "Syy": Syy, "ssr": ssr}

JS = LIB + r"""
const D = DATA, n = D.x.length;
const G = .8, T0 = .6;
const POSTER_T = 2.4;
const SSR = b => D.Syy - 2 * b * D.Sxy + b * b * D.Sxx;
const PA = {x: 100, y: 58, w: 500, h: 392}, PB = {x: 712, y: 58, w: 250, h: 392};
const K = PA.h / 500;                        // drawing units per k$ (price axis 100..600)

function draw() {
  /* the slope, as the page tilts the line and lets it settle back */
  const c = cycle(T0, [[D.b1, 2.2], [D.b1 - D.d, .7], [D.b1, 2.2], [D.b1 + D.d, .7]], G);
  const b = cyc(c), off = clamp(Math.abs(b - D.b1) / D.d);
  const a0 = D.yb - b * D.xb;                // the line through the mean point

  /* (a) */
  sub('a', 18, 34, 'best-fit line and residuals', arrive(0));
  const g = axes({...PA, xlim: [800, 3100], ylim: [100, 600], xticks: [1000, 1500, 2000, 2500, 3000],
    yticks: [100, 200, 300, 400, 500, 600], xlabel: '\\rm{floor area (ft}^{2}\\rm{)}', ylabel: '\\rm{price (k$)}',
    ylabelGap: 54, progress: seg(0, .35)});
  const segA = i => seg(.34 + .018 * i, .26);
  g.inside(() => {
    // squared residuals: a square on each residual, away from the line
    for (let i = 0; i < n; i++) {
      const yh = a0 + b * D.x[i], rr = D.y[i] - yh, s = Math.abs(rr) * K, px = g.X(D.x[i]);
      const top = g.Y(Math.max(D.y[i], yh)), a = arrive(.44 + .018 * i);
      if (a > 0) box(rr > 0 ? px - s : px, top, s, s, {fill: C.wash, stroke: C.amber, width: 1, alpha: .9 * a});
    }
    // the best fit, dashed, while the line is tilted away from it (not while it first settles);
    // it comes in only once the line's own name (below) has gone, so the two never cross
    const ghost = clamp((off - .3) / .7) * clamp((t - 1.6) * 4);
    if (ghost > 0) line([[g.X(800), g.Y(D.b0 + D.b1 * 800)], [g.X(3100), g.Y(D.b0 + D.b1 * 3100)]],
      {color: C.blue, width: 1.3, dash: [6, 4], alpha: .75 * ghost});
    line([[g.X(800), g.Y(a0 + b * 800)], [g.X(3100), g.Y(a0 + b * 3100)]],
      {color: C.blue, width: 2.6, progress: seg(.2, .36)});
    // residuals, then the houses on top
    for (let i = 0; i < n; i++) {
      const yh = a0 + b * D.x[i];
      line([[g.X(D.x[i]), g.Y(yh)], [g.X(D.x[i]), g.Y(D.y[i])]], {color: C.accent, width: 1.6, progress: segA(i)});
    }
    for (let i = 0; i < n; i++) mark(g.X(D.x[i]), g.Y(D.y[i]), 1, arrive(.05 + .22 * i / (n - 1)));
  });
  // the mean point the line turns about
  const ma = arrive(.62), mx = g.X(D.xb), my = g.Y(D.yb);
  if (ma > 0) {
    line([[mx - 6, my - 6], [mx + 6, my + 6]], {width: 1.5, alpha: ma});
    line([[mx - 6, my + 6], [mx + 6, my - 6]], {width: 1.5, alpha: ma});
    text('mean point', mx + 10, my + 20, {size: 15, color: C.body, alpha: ma});
  }
  // the line's name, set along it below its left end (TikZ: node[sloped, below])
  // it names the line only while the line is the best fit: gone within the first 15 % of a tilt
  const la = arrive(.7) * clamp(1 - off / .15), xa = 830, ang = Math.atan2(g.Y(a0 + b * (xa + 100)) - g.Y(a0 + b * xa), g.X(xa + 100) - g.X(xa));
  if (la > 0) {
    ctx.save(); ctx.translate(g.X(xa), g.Y(a0 + b * xa)); ctx.rotate(ang);
    text('best-fit line', 0, 25, {size: 16, color: C.blue, alpha: la});
    ctx.restore();
  }
  legend(PA.x + 14, PA.y + 14, [
    [(x, y) => mark(x, y + 1, 1, 1), 'house sale'],
    [(x, y) => line([[x, y - 8], [x, y + 9]], {color: C.accent, width: 1.6}), 'residual'],
    [(x, y) => box(x - 7, y - 6, 13, 13, {fill: C.wash, stroke: C.amber, width: 1}), 'squared residual'],
  ], arrive(.55));

  /* (b) */
  sub('b', PB.x - 64, 34, 'sum of squared residuals', arrive(.08));
  const h = axes({...PB, xlim: [100, 240], ylim: [0, 40000], xticks: [100, 140, 180, 220],
    yticks: [0, 10000, 20000, 30000, 40000], yfmt: v => thou(v),
    xlabel: '\\rm{slope ($ per ft}^{2}\\rm{)}', ylabel: '\\rm{sum of squared residuals (k$}^{2}\\rm{)}',
    ylabelGap: 66, progress: seg(.04, .35)});
  const par = [];
  for (let k = 0; k <= 140; k++) { const bb = (100 + k) / 1000; par.push([h.X(bb * 1000), h.Y(SSR(bb))]); }
  h.inside(() => line(par, {color: C.navy, width: 2.2, progress: seg(.18, .42)}));
  const ga = arrive(.66);
  line([[h.X(D.b1 * 1000), h.Y(SSR(D.b1))], [h.X(D.b1 * 1000), PB.y + PB.h]],
    {color: C.guide, width: 1, dash: [5, 4], alpha: ga});
  // named beside its guide (TikZ: node[right]), not on it
  text('least squares', h.X(D.b1 * 1000) + 7, h.Y(SSR(D.b1)) + 28, {size: 15, color: C.body, alpha: ga});
  const pa = arrive(.5);
  dot(h.X(b * 1000), h.Y(SSR(b)), 5.5, {color: '#fff', fill: C.accent, width: 1.4, alpha: pa});
  // the numbers of the line being drawn
  const ra = arrive(.74), cx = PB.x + PB.w / 2;
  math('\\rm{slope $' + (b * 1000).toFixed(0) + ' per ft}^{2}', cx, PB.y + 30, {size: 16, align: 'center', alpha: ra});
  math('\\rm{sum ' + thou(SSR(b)) + ' k$}^{2}', cx, PB.y + 52, {size: 16, align: 'center',
    color: off > .02 ? C.accent : C.ink, alpha: ra});

  text('14 simulated house sales; least squares: price = ' + D.b0.toFixed(1) + ' k$ + $' + (D.b1 * 1000).toFixed(1) +
       ' per ft² × area; each square’s side is its residual', 18, H - 14, {size: 14, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = ("Figure 8: Linear regression: the model finds the line that minimizes the sum of squared "
         "vertical distances (residuals) to each data point")
ARIA = ("Fourteen house sales, price against floor area, with the least squares line. Each residual is "
        "drawn as a vertical segment with its square beside it; tilting the line about the mean point "
        "makes the squares larger, and the second panel shows their sum as a parabola whose lowest point "
        "is the best-fit slope.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 560, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.15, 0.4, 0.8, 1.4, 3.9, 4.6, 7.0]))
