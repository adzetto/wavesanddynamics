"""Figure 20: underfitting, a good fit and overfitting, as the same 22
training points fit with growing model flexibility.

Model: 22 training points y = sin(2 pi x) + noise (sigma 0.25) at jittered,
evenly spread x in [0, 1]. Least squares polynomials of every degree 0 to 18
(Legendre basis on [0, 1], so the normal equations stay well conditioned).
The three panels stop the same growth at three degrees: 1 (underfitting), the
degree leave-one-out cross validation picks (a good fit) and 18 (overfitting:
it chases every training point, noise included). Each panel's errors are the
model's own: root mean square on the 22 training points and on 20 000 new
points from the same process.

The motion is the growth itself: every panel's curve steps through the least
squares fits of degree 0, 1, 2, ... (each step a blend of two exact fits) and
stops at its own degree; then the three ease back to degree 0 and grow again.

Run: python tools/numfig/mlb_fit.py [--look]
"""
import numpy as np
from numpy.polynomial import Legendre as Lg

import common
import mlb_common as mc

NAME = "fit"
N, SIGMA, SEED = 22, 0.25, 11
D_UNDER, D_OVER = 1, 18
truth = lambda x: np.sin(2 * np.pi * x)

rng = np.random.default_rng(SEED)
x = (np.arange(N) + 0.5 + 0.6 * (rng.uniform(size=N) - 0.5)) / N
y = truth(x) + SIGMA * rng.standard_normal(N)
xn = rng.uniform(0, 1, 20000)                    # new data from the same process
yn = truth(xn) + SIGMA * rng.standard_normal(xn.size)

fits = [Lg.fit(x, y, d, domain=[0, 1]) for d in range(22)]
rms = lambda v: float(np.sqrt(np.mean(v ** 2)))
train = [rms(p(x) - y) for p in fits]
new = [rms(p(xn) - yn) for p in fits]


def loo(d):
    e = []
    for i in range(N):
        m = np.arange(N) != i
        e.append(Lg.fit(x[m], y[m], d, domain=[0, 1])(x[i]) - y[i])
    return rms(np.array(e))


cv = [loo(d) for d in range(19)]
D_GOOD = int(np.argmin(cv))
XS = np.linspace(0, 1, 401)
CURVES = np.clip(np.array([fits[d](XS) for d in range(D_OVER + 1)]), -60, 60)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-fit: Figure 20, underfitting, a good fit and overfitting on the same 22 points")
say("")
say("MODEL")
say(f"  {N} training points, x_i = (i + 1/2 + 0.6 u_i)/{N} with u_i uniform in [-1/2, 1/2]"
    f" (seed {SEED}), y_i = sin(2 pi x_i) + e_i, e_i ~ N(0, {SIGMA}^2).")
say(f"  x from {x.min():.4f} to {x.max():.4f}, smallest gap {np.diff(x).min():.4f}.")
say("  Least squares polynomials of degree d (Legendre basis mapped from [0, 1]); new data:")
say(f"  {xn.size} points, x uniform in [0, 1], same noise. Errors are root mean square (RMS).")
say("")
say("CHECK 1: the least squares solution against a direct solve of the normal equations")
for d in (1, 4, 9):
    V = np.vander(2 * x - 1, d + 1, increasing=True)
    c = np.linalg.solve(V.T @ V, V.T @ y)
    say(f"  d = {d}: max |p(x) - p_normal(x)| on the grid = "
        f"{np.max(np.abs(fits[d](XS) - np.vander(2*XS-1, d+1, increasing=True) @ c)):.1e};"
        f" residual orthogonal to the basis, max |V^T r| = {np.max(np.abs(V.T @ (y - fits[d](x)))):.1e}")
say("")
say("CHECK 2: known limits")
say(f"  degree 0 is the mean: p0 = {fits[0](0.5):.12f}, mean(y) = {y.mean():.12f}")
say(f"  degree {N-1} interpolates all {N} points: max |p(x_i) - y_i| = {np.max(np.abs(fits[N-1](x) - y)):.1e}")
say(f"  training RMS never rises with the degree (nested models): "
    f"{all(train[d+1] <= train[d] + 1e-12 for d in range(21))}")
say(f"  new data RMS can not fall below the noise: min over d = {min(new):.4f} >= sigma = {SIGMA}")
say("")
say("CHECK 3: degree by degree (RMS)")
say("  d   training   leave one out   new data")
for d in range(19):
    tag = {D_UNDER: "  underfitting", D_OVER: "  overfitting"}.get(d, "")
    if d == D_GOOD:
        tag = "  good fit (smallest leave one out error)"
    say(f"  {d:2d}   {train[d]:.4f}     {cv[d]:9.4f}     {new[d]:9.4f}{tag}")
say("")
say(f"PANELS: degree {D_UNDER}, {D_GOOD}, {D_OVER}. Degree {D_OVER} on {N} points: training RMS "
    f"{train[D_OVER]:.3f} (it passes through the noise), new data RMS {new[D_OVER]:.2f}.")
say(f"  curves sampled at {XS.size} points on [0, 1], values clipped to +-60 (the axes show +-2).")
mc.check(NAME, L)

DATA = {
    "x": x, "y": y, "xs": XS, "curves": common.f32(CURVES), "truth": truth(XS),
    "deg": [D_UNDER, D_GOOD, D_OVER], "train": train[:D_OVER + 1], "new": new[:D_OVER + 1],
    "sigma": SIGMA, "n": N, "nnew": int(xn.size),
}

JS = r"""
const D = DATA, NX = D.xs.length, CUR = b64f32(D.curves), DEG = D.deg, DMAX = DEG[2];
const STEP = .2, T_GROW = .6, HOLD = 5, BACK = .9, REST = .5;
const GROW = DMAX * STEP, PER = GROW + HOLD + BACK + REST;
const POSTER_T = T_GROW + GROW + 2;
/* the degree the growth has reached, as a real number: whole numbers are the
   least squares fits, in between a blend of two of them */
function grown() {
  if (t < T_GROW) return { u: 0, back: 0 };
  const c = (t - T_GROW) % PER;
  if (c < GROW) { const k = Math.floor(c / STEP); return { u: k + easeInOut((c - k * STEP) / STEP), back: 0 }; }
  if (c < GROW + HOLD) return { u: DMAX, back: 0 };
  return { u: DMAX, back: easeInOut(clamp((c - GROW - HOLD) / BACK)) };
}
const AX = { y: 60, w: 262, h: 188 }, X0 = [60, 390, 720];
const NAMES = ['underfitting', 'good fit', 'overfitting'];
const pts = new Array(NX);

function draw() {
  const g = grown();
  for (let k = 0; k < 3; k++) {
    const x = X0[k], t0 = .05 * k, a = lab(t0);
    // how far this panel has grown: its own degree at most; easing back, a
    // straight blend from its own fit to the mean (degree 0)
    const u = Math.min(g.u, DEG[k]), d0 = Math.floor(u), s = u - d0, d1 = Math.min(d0 + 1, DEG[k]);
    const dn = g.back < .5 ? Math.round(u) : 0;
    text(NAMES[k], x, 38 + rise(a), { size: 17, color: C.body, alpha: a });
    math(`\\rm{degree}\\ ${dn}`, x + AX.w, 38 + rise(lab(t0 + .04)), { size: 16, color: C.body, align: 'right', alpha: lab(t0 + .04) });
    const A = axes({ x, y: AX.y, w: AX.w, h: AX.h, xlim: [0, 1], ylim: [-2, 2], xticks: [0, .5, 1],
      yticks: [-2, -1, 0, 1, 2], xlabel: 'x', ylabel: k ? '' : 'y', ylabelGap: 34, progress: seg(t0, .35),
      xfmt: v => v === .5 ? '0.5' : fmt(v) });
    A.inside(() => {
      line([[x, A.Y(0)], [x + AX.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.15 + t0, .3) });
      for (let i = 0; i < NX; i++) pts[i] = [A.X(D.xs[i]), A.Y(D.truth[i])];
      line(pts, { color: C.guide, width: 1.3, dash: [6, 4], progress: seg(.22 + t0, .4) });
      for (let i = 0; i < NX; i++) {
        const v = lerp(lerp(CUR[d0 * NX + i], CUR[d1 * NX + i], s), CUR[i], g.back);
        pts[i] = [A.X(D.xs[i]), A.Y(clamp(v, -3, 3))];
      }
      line(pts, { color: C.blue, width: 2.4, progress: seg(.32 + t0, .42) });
    });
    for (let i = 0; i < D.n; i++) {                 // the training points arrive left to right
      const p = settle(.1 + t0 + .008 * i, .24);
      if (p > 0) mark('circle', A.X(D.x[i]), A.Y(D.y[i]), 3.6 * (.55 + .45 * p), { fill: C.navy, stroke: '#fff', width: 1, alpha: p });
    }
    // the model's errors at the degree shown
    const ra = lab(.45 + t0), cx = x + AX.w / 2;
    math(`\\rm{training\\ error}\\ \\ ${D.train[dn].toFixed(2)}`, cx, 322, { size: 15, align: 'center', color: C.body, alpha: ra });
    const nv = D.new[dn], bad = dn === DMAX;
    math(`\\rm{new\\ data\\ error}\\ \\ ${nv < 10 ? nv.toFixed(2) : nv.toFixed(1)}`, cx, 344,
         { size: 15, align: 'center', color: bad ? C.accent : C.body, alpha: ra });
  }
  const la = lab(.55);
  text('real pattern', X0[0] + AX.w * .25, AX.y + AX.h * (2 - 1.32) / 4 + rise(la), { size: 14, color: C.muted, align: 'center', alpha: la });
  text(`${D.n} training points, y = sin 2πx + noise (σ = ${D.sigma}); least squares polynomials; errors are RMS, new data ${D.nnew.toLocaleString('en')} points`,
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.6) });
}
boot();
"""

TITLE = "Figure 20: Underfitting, a good fit, and overfitting"
ARIA = (f"Three plots of the same {N} noisy training points around a dashed sine curve, the real "
        f"pattern, each fit with a least squares polynomial: degree {D_UNDER} underfits with a "
        f"straight line, degree {D_GOOD} follows the real pattern, and degree {D_OVER} chases every "
        "training point and swings wildly between and beyond them. The curves grow through the "
        "degrees one step at a time, and each plot gives its error on the training points and on "
        "new data.")

if __name__ == "__main__":
    print(f"degrees: {D_UNDER}, {D_GOOD}, {D_OVER}; training RMS {train[D_UNDER]:.3f}, {train[D_GOOD]:.3f}, "
          f"{train[D_OVER]:.3f}; new data RMS {new[D_UNDER]:.3f}, {new[D_GOOD]:.3f}, {new[D_OVER]:.2f}")
    mc.publish(NAME, TITLE, ARIA, 1000, 412, DATA, JS, look=(0.3, 0.6, 1.0, 1.8, 3.0, 9.8, 10.4))
