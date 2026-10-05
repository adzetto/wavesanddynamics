"""Figure 13 of the machine learning guide (stem image10): linear and RBF SVMs.

(a) Linear SVM. Two classes drawn from two normal clouds (seed fixed), in
scaled features. The hard margin SVM (scikit-learn SVC, linear kernel,
C = 1e8) gives w, b and the support vectors. For any boundary direction the
widest street between the classes is closed form: with u the unit normal,
the street runs from max over class B of u.x to min over class A of u.x, so
its width is m(theta) = min_A u.x - max_B u.x. The page turns the boundary
away from the SVM's and back, drawing that street, its width and the points
that touch it every frame; (a') is m(theta), whose peak is the SVM, 2/|w|.

(b) RBF SVM on two concentric rings (SVC, gamma = 0.5, C = 10, tol 1e-10),
checked against the dual QP solved again by SLSQP:
f(x) = sum_i alpha_i y_i exp(-gamma |x - x_i|^2) + b over the 14 support
vectors. The boundary f = 0 and the margins f = +-1 are traced with contourpy
on a fine grid. The page itself evaluates f from the support vectors, their
coefficients and b (DATA), so every height it draws is the model's.
  (b') f along a line through the rings, turning in 60 degree steps: each
  support vector adds one Gaussian bump, alpha_i y_i exp(-gamma d_i^2)
  exp(-gamma (s - s_i)^2) (s_i its place along the line, d_i its distance
  from it), hung from b; their sum is f, and f = 0 where the line crosses the
  boundary (found by bisection).
  The 3-D view (a click on (b), or the tour): the camera turns from straight
  above to a pgfplots view of the surface z = f(x1, x2) (a 25 x 25 faceted
  mesh, faces sorted back to front, split where they cross z = 0). The points
  sit at their own f; the flat plane z = 0 cuts the surface exactly along the
  boundary, class A above it (f >= 1), class B below (f <= -1).
  The arrow from (a) to (b): the best straight line on the rings, found by an
  exhaustive search over every line through two points (the optimum of the
  0-1 loss in the plane; brute force over 3601 directions agrees), drawn with
  the widest street among those that score best: 89 of 120 (74 %), against
  120 of 120 for the RBF boundary.

Run: python tools/numfig/mla_svm.py [--look]
"""
import sys

import contourpy
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from sklearn.svm import SVC

import common
from mla_shared import LIB, report

NAME, STEM = "mla-svm", "mla_svm"
LIM = 3.2
HPAGE = 736                                   # the page: 1000 x 736 drawing units (840 before 5 Oct 2026)

# ------------------------------------------------------------------ (a) linear
rng = np.random.default_rng(3)
NA = 20
XB = rng.normal([-1.2, -1.0], 0.62, (NA, 2))
XA = rng.normal([1.1, 1.1], 0.62, (NA, 2))
Xl = np.r_[XA, XB]
yl = np.r_[np.ones(NA), -np.ones(NA)]
lin = SVC(kernel="linear", C=1e8, tol=1e-12).fit(Xl, yl)
w, b = lin.coef_[0], lin.intercept_[0]
th_star = float(np.degrees(np.arctan2(w[1], w[0])))


def street(theta_deg):
    u = np.array([np.cos(np.radians(theta_deg)), np.sin(np.radians(theta_deg))])
    s = Xl @ u
    return s[yl > 0].min() - s[yl < 0].max()


best = minimize_scalar(lambda d: -street(d), bounds=(th_star - 3, th_star + 3), method="bounded",
                       options={"xatol": 1e-10})
SWING = 15.0
tg = np.linspace(th_star - 24, th_star + 24, 241)
mg = np.array([street(v) for v in tg])

# ------------------------------------------------------------------ (b) RBF
rng = np.random.default_rng(1)
NR = 60
t0, r0 = rng.uniform(0, 2 * np.pi, NR), rng.normal(1.0, 0.14, NR)
t1, r1 = rng.uniform(0, 2 * np.pi, NR), rng.normal(2.2, 0.16, NR)
Xr = np.r_[np.c_[r0 * np.cos(t0), r0 * np.sin(t0)], np.c_[r1 * np.cos(t1), r1 * np.sin(t1)]]
yr = np.r_[np.ones(NR), -np.ones(NR)]
GAMMA, CR = 0.5, 10.0
rbf = SVC(kernel="rbf", gamma=GAMMA, C=CR, tol=1e-10).fit(Xr, yr)
SV = Xr[rbf.support_]
CO = rbf.dual_coef_[0]
B0 = rbf.intercept_[0]


def f_rbf(P):
    d2 = ((P[:, None, :] - SV[None, :, :]) ** 2).sum(-1)
    return np.exp(-GAMMA * d2) @ CO + B0


NGRID = 241
gx = np.linspace(-LIM, LIM, NGRID)
GXX, GYY = np.meshgrid(gx, gx)
FG = f_rbf(np.c_[GXX.ravel(), GYY.ravel()]).reshape(NGRID, NGRID)
gen = contourpy.contour_generator(gx, gx, FG, line_type="SeparateCode")


def lines_at(level):
    """closed lines only: f = -1 also crosses the plot's corners, far from
    every point, where f tends to b; those open pieces are left out"""
    segs, codes = gen.lines(level)
    return [np.round(s, 3).tolist() for s, c in zip(segs, codes) if len(s) > 3 and c[-1] == 79]


CONT = {"0": lines_at(0.0), "p": lines_at(1.0), "m": lines_at(-1.0)}
NS = 25                                       # the lifted surface: a 25 x 25 faceted mesh
sg = np.linspace(-LIM, LIM, NS)
SGX, SGY = np.meshgrid(sg, sg)
SF = f_rbf(np.c_[SGX.ravel(), SGY.ravel()]).reshape(NS, NS)
fr = rbf.decision_function(Xr)

# the best straight line on the rings: any line can be moved, keeping its
# score, until it passes through two points, and those two can then be put on
# either side of it; so the best score is the best over every pair and both
# orientations of (the others on their side) + 2
nR = len(Xr)
opt, top = [], -1
for i in range(nR):
    for j in range(i + 1, nR):
        d = Xr[j] - Xr[i]
        side = (Xr - Xr[i]) @ np.array([-d[1], d[0]])
        for sgn in (1, -1):
            ok = np.sign(sgn * side) == yr
            ok[[i, j]] = True
            c = int(ok.sum())
            if c > top:
                top, opt = c, []
            if c == top:
                opt.append(ok.copy())
# brute force, as a second opinion: 3601 directions, every cut between points
brute = 0
for a in np.linspace(0, np.pi, 3601):
    p = Xr @ np.array([np.cos(a), np.sin(a)])
    o = np.sort(p)
    cuts = np.r_[o[0] - 1, (o[1:] + o[:-1]) / 2, o[-1] + 1]
    hit = (np.sign(p[None, :] - cuts[:, None]) == yr[None, :]).sum(1)
    brute = max(brute, int(hit.max()), int((len(yr) - hit).max()))
# of the lines that score best, the one with the widest street: the hard
# margin line of the points it gets right. Its street is pinned by three of
# them (two of one class, one of the other), so it is closed form: parallel to
# the pair, halfway to the third. SLSQP on the primal agrees (check file).
OPTS = {tuple(o) for o in opt}
BOK = np.array(next(iter(OPTS)))
Xs, ys = Xr[BOK], yr[BOK]
qpl = minimize(lambda v: .5 * (v[0] ** 2 + v[1] ** 2), np.zeros(3), jac=lambda v: np.array([v[0], v[1], 0.]),
               method="SLSQP", constraints=[{"type": "ineq", "fun": lambda v: ys * (Xs @ v[:2] + v[2]) - 1,
                                             "jac": lambda v: np.c_[ys[:, None] * Xs, ys]}],
               options={"ftol": 1e-15, "maxiter": 1000})
ACT = np.where(BOK)[0][np.abs(ys * (Xs @ qpl.x[:2] + qpl.x[2]) - 1) < 1e-6]
pair = [k for k in ACT if (yr[ACT] == yr[k]).sum() == 2]
lone = [k for k in ACT if (yr[ACT] == yr[k]).sum() == 1][0]
dv = Xr[pair[1]] - Xr[pair[0]]
nv = np.array([-dv[1], dv[0]]) / np.linalg.norm(dv)
BC = -(nv @ Xr[lone] + nv @ Xr[pair[0]]) / 2
if yr[lone] * (nv @ Xr[lone] + BC) < 0:
    nv, BC = -nv, -BC
BWL = nv
BW = abs(nv @ Xr[lone] - nv @ Xr[pair[0]])
BSC = int((np.sign(Xr @ BWL + BC) == yr).sum())
lin_r = SVC(kernel="linear", C=10).fit(Xr, yr)
LINACC = lin_r.score(Xr, yr)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-svm: Figure 13, linear SVM (left) and RBF kernel SVM (right)")
say("")
say("(a) LINEAR")
say(f"  {NA} + {NA} points, class A ~ N((1.1, 1.1), 0.62^2 I), class B ~ N((-1.2, -1.0), 0.62^2 I), seed 3")
say(f"  hard margin SVC (linear, C = 1e8, tol 1e-12): w = ({w[0]:.6f}, {w[1]:.6f}), b = {b:.6f},"
    f" support vectors {len(lin.support_)}")
say(f"  normal direction theta* = {th_star:.6f} deg; street width 2/|w| = {2/np.linalg.norm(w):.9f}")
say("CHECK 1: the widest street over all directions (closed form per direction, bounded search)")
say(f"  argmax m(theta) = {best.x:.6f} deg (SVM {th_star:.6f}); max m = {-best.fun:.9f}"
    f" (2/|w| = {2/np.linalg.norm(w):.9f}, diff {abs(-best.fun - 2/np.linalg.norm(w)):.1e})")
say(f"  m(theta* -+ {SWING:g} deg) = {street(th_star-SWING):.4f}, {street(th_star+SWING):.4f}"
    f" (narrower either way); separable from {tg[mg > 0].min():.1f} to {tg[mg > 0].max():.1f} deg")
qp = minimize(lambda v: 0.5 * (v[0] ** 2 + v[1] ** 2), x0=np.array([3.0, 3.0, 0.0]),
              jac=lambda v: np.array([v[0], v[1], 0.0]), method="SLSQP",
              constraints=[{"type": "ineq", "fun": lambda v: yl * (Xl @ v[:2] + v[2]) - 1,
                            "jac": lambda v: np.c_[yl[:, None] * Xl, yl]}],
              options={"ftol": 1e-15, "maxiter": 500})
say(f"  primal QP by SLSQP from w = (3, 3), b = 0: w = ({qp.x[0]:.6f}, {qp.x[1]:.6f}), b = {qp.x[2]:.6f},"
    f" 2/|w| = {2/np.linalg.norm(qp.x[:2]):.9f}")
marg = yl * (Xl @ w + b)
say("CHECK 2: KKT, y (w.x + b) >= 1, with equality exactly at the support vectors")
say(f"  min over all points {marg.min():.8f}; at the support vectors"
    f" {', '.join(f'{v:.8f}' for v in marg[lin.support_])}")
say("")
say("(b) RBF")
say(f"  {NR} + {NR} points on two rings, radius ~ N(1.0, 0.14) (class A) and N(2.2, 0.16) (class B), seed 1")
say(f"  SVC(rbf, gamma = {GAMMA}, C = {CR:g}, tol 1e-10): {len(rbf.support_)} support vectors,"
    f" training accuracy {rbf.score(Xr, yr):.3f}, b = {B0:.6f}")
say("  alpha_i y_i: " + ", ".join(f"{v:+.4f}" for v in CO))
ours = f_rbf(Xr)
say("CHECK 3: f(x) = sum alpha_i y_i exp(-gamma |x - x_i|^2) + b against scikit-learn")
say(f"  max |ours - decision_function| over the 120 points = {np.abs(ours - fr).max():.1e}")
say(f"  sum alpha_i y_i = {CO.sum():.1e} (the dual's equality constraint)")
Kr = np.exp(-GAMMA * ((Xr[:, None] - Xr[None]) ** 2).sum(-1))
Qr = (yr[:, None] * yr[None]) * Kr
dual = minimize(lambda a: .5 * a @ Qr @ a - a.sum(), np.zeros(nR), jac=lambda a: Qr @ a - 1,
                method="SLSQP", bounds=[(0, CR)] * nR,
                constraints=[{"type": "eq", "fun": lambda a: yr @ a, "jac": lambda a: yr}],
                options={"ftol": 1e-14, "maxiter": 2000})
ad = dual.x
free_d = (ad > 1e-6) & (ad < CR - 1e-6)
bd = float(np.mean(yr[free_d] - Kr[free_d] @ (ad * yr)))
ask = np.zeros(nR)
ask[rbf.support_] = np.abs(CO)
say("CHECK 4: the dual QP again, by SLSQP from alpha = 0 (max 1/2 a'Qa - sum a, 0 <= a <= C, y'a = 0)")
say(f"  {int((ad > 1e-6).sum())} support vectors (the same {int(((ad > 1e-6) == (ask > 0)).all()) and 'set'});"
    f" max |alpha - alpha_sklearn| = {np.abs(ad - ask).max():.1e}; b = {bd:.6f}"
    f" (scikit-learn {B0:.6f}); dual objective {.5 * ad @ Qr @ ad - ad.sum():.9f}"
    f" ({.5 * ask @ Qr @ ask - ask.sum():.9f})")
free = np.abs(CO) < CR - 1e-8
nonsv = np.setdiff1d(np.arange(2 * NR), rbf.support_)
say("CHECK 5: margins: y f(x) >= 1 off the support vectors, = 1 on the free ones")
say(f"  min y f over non support vectors {np.min(yr[nonsv]*fr[nonsv]):.4f};"
    f" y f at free support vectors {np.min(yr[rbf.support_][free]*fr[rbf.support_][free]):.8f}"
    f" .. {np.max(yr[rbf.support_][free]*fr[rbf.support_][free]):.8f}")
say(f"  bounded (alpha = C) support vectors: {int((~free).sum())}")
say(f"  f at the points: class A {fr[yr > 0].min():.4f} .. {fr[yr > 0].max():.4f},"
    f" class B {fr[yr < 0].min():.4f} .. {fr[yr < 0].max():.4f}: the plane z = 0 lies between them")
say("CHECK 6: no straight line separates the rings")
say(f"  best line, exhaustive over all {nR * (nR - 1) // 2} pairs x 2 orientations: {top} of {nR}"
    f" ({top / nR:.1%}); brute force over 3601 directions x every cut: {brute} of {nR}")
say(f"  {len(opt)} (pair, orientation) choices reach it, all one classification ({len(OPTS)});"
    f" drawn: its widest street, pinned by points {pair[0]}, {pair[1]} and {lone}:")
say(f"  unit normal ({BWL[0]:.6f}, {BWL[1]:.6f}), offset {BC:.6f}, street {BW:.6f}, scores {BSC} of {nR};"
    f" SLSQP primal: street {2 / np.linalg.norm(qpl.x[:2]):.6f},"
    f" unit normal ({qpl.x[0] / np.linalg.norm(qpl.x[:2]):.6f}, {qpl.x[1] / np.linalg.norm(qpl.x[:2]):.6f})")
say(f"  (so every line that scores {top} passes within {BW / 2:.4f} of those three points)")
say(f"  (a linear SVC, C = 10, on the rings scores {LINACC:.3f}: the hinge loss is not the count of errors)")
say("")
say(f"GRID: boundary and margins traced on {NGRID} x {NGRID} (step {2*LIM/(NGRID-1):.4f});"
    f" surface {NS} x {NS} (step {2*LIM/(NS-1):.4f})")
for k, v in CONT.items():
    say(f"  level {k}: {len(v)} closed line(s), {sum(len(s) for s in v)} vertices")
say(f"  intercept b = {B0:.4f}: f tends to b far from the data")
lvl0 = np.array(CONT["0"][0])
say(f"  the traced boundary against f itself: max |f| on its {len(lvl0)} vertices = {np.abs(f_rbf(lvl0)).max():.1e}")
fine = np.linspace(-LIM, LIM, 97)
FX, FY = np.meshgrid(fine, fine)
Ff = f_rbf(np.c_[FX.ravel(), FY.ravel()]).reshape(97, 97)
from scipy.interpolate import RegularGridInterpolator  # noqa: E402
bil = RegularGridInterpolator((sg, sg), SF.T)(np.c_[FX.ravel(), FY.ravel()]).reshape(97, 97)
say(f"  surface mesh (bilinear between its nodes) against f on a 97 x 97 grid: max |diff| ="
    f" {np.abs(bil - Ff).max():.3f} (of a range {Ff.min():.2f} .. {Ff.max():.2f})")
# the page evaluates f itself, from DATA as build_html writes it (5 decimals)
SVr, COr, B0r = np.round(SV, 5), np.round(CO, 5), round(float(B0), 5)
f_page = np.exp(-GAMMA * ((np.c_[FX.ravel(), FY.ravel()][:, None, :] - SVr[None]) ** 2).sum(-1)) @ COr + B0r
say(f"  f as the page computes it (DATA rounded to 5 decimals) against f: max |diff| on 97 x 97 ="
    f" {np.abs(f_page - Ff.ravel()).max():.1e}")
say("")
say(f"PAGE (nf-mla-svm.html, 1000 x {HPAGE})")
say("  (b) the tour: from 3.2 s the camera turns from straight above to the 3-D view on Motion's spring")
say("      (visual duration 2.0 s, bounce 0; the lift it replaces took 1.0 s), holds 6 s, turns back in")
say("      2.0 s and rests 12 s. A click on (b), the cube button or Enter on it takes over: a spring of")
say("      1.8 s from wherever the camera is. In 3-D a drag turns it (azimuth 0..88 deg, elevation")
say("      8..75 deg). Reduced motion and ?still switch at once; the poster (17.5 s) is the 2-D figure.")
say("  3-D view: azimuth 34 deg, elevation 34 deg; the box holds f in [-3, 3], drawn half as tall as")
say("      wide. Faces are sorted back to front by their horizontal depth alone (exact for a height field")
say("      seen from above) and split at z = 0, so the plane is drawn between the two halves. Points and")
say("      lines are hidden where a ray to the eye meets the mesh (the drawn surface, bilinear), fading")
say("      over 0.12 in f.")
say("  (b') the line turns 60 deg every 7 s (rest 5 s, then a Motion spring of 2 s) from -30 deg; the")
say("      poster shows 90 deg. Its zeros are found by bisection on f (48 halvings).")
say(f"  the arrow: hovered, focused or pinned (a click, Enter), (b) shows the best straight line, its class")
say(f"      A side washed and the {int((~BOK).sum())} points it gets wrong ringed in crimson; {100 * BSC / nR:.0f} % against 100 %.")
report(STEM, L)

DATA = {
    "lim": LIM,
    "a": {"x": Xl, "y": yl, "th": th_star, "swing": SWING, "tg": tg, "mg": mg,
          "wmax": 2 / np.linalg.norm(w)},
    "b": {"x": Xr, "y": yr, "f": fr, "sv": rbf.support_.tolist(), "co": CO, "b0": B0, "gamma": GAMMA,
          "c": CONT, "ns": NS, "sg": sg, "sf": SF.ravel(),
          "line": {"w": BWL, "c": BC, "n": BSC}, "n": nR},
}

JS = LIB + r"""
const LIMX = DATA.lim, DA = DATA.a, DB = DATA.b;
const POSTER_T = 17.5;
const SQ = 330, PA = {x: 72, y: 58, w: SQ, h: SQ}, PB = {x: 616, y: 58, w: SQ, h: SQ};
const PC = {x: 72, y: 480, w: SQ, h: 124}, PD = {x: 616, y: 480, w: 348, h: 124};   // (b') a little wider: its key
const rad = d => d * Math.PI / 180;
const INSTANT = REDUCED || STILL;                     // interactions switch at once
const TU = () => performance.now() / 1000;          // the clock of the reader's own actions
const hexc = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mixc = (a, b, s) => { const A = hexc(a), B = hexc(b);
  return 'rgb(' + A.map((v, i) => Math.round(lerp(v, B[i], clamp(s)))).join(',') + ')'; };

/* ------------------------------------------------------------ (a) linear */
function street(th) {
  const ux = Math.cos(rad(th)), uy = Math.sin(rad(th));
  let mA = 1e9, mB = -1e9;
  for (let i = 0; i < DA.x.length; i++) {
    const s = ux * DA.x[i][0] + uy * DA.x[i][1];
    if (DA.y[i] > 0) mA = Math.min(mA, s); else mB = Math.max(mB, s);
  }
  return {ux, uy, mA, mB, c: (mA + mB) / 2, w: mA - mB};
}
function uline(g, S, s) {
  const px = S.ux * s, py = S.uy * s, dx = -S.uy * 10, dy = S.ux * 10;
  return [[g.X(px - dx), g.Y(py - dy)], [g.X(px + dx), g.Y(py + dy)]];
}
function drawA() {
  sub('a', 18, 34, 'linear SVM', arrive(0));
  const g = axes({...PA, xlim: [-LIMX, LIMX], ylim: [-LIMX, LIMX], xticks: [-3, -2, -1, 0, 1, 2, 3],
    yticks: [-3, -2, -1, 0, 1, 2, 3], xlabel: 'x_{1}', ylabel: 'x_{2}', ylabelGap: 42, tickSize: 16, progress: seg(0, .35)});
  const cy = cycle(.6, [[DA.th, 6.0], [DA.th - DA.swing, .8], [DA.th, .8], [DA.th + DA.swing, 1.2]], .8);
  const th = cyc(cy), S = street(th);
  const ra = arrive(.36);
  g.inside(() => {
    if (ra > 0) {
      const [p, q] = uline(g, S, S.c), nx = S.ux * 12, ny = S.uy * 12;
      ctx.save(); ctx.globalAlpha = .7 * ra; ctx.fillStyle = C.steel; ctx.beginPath();
      ctx.moveTo(p[0], p[1]); ctx.lineTo(q[0], q[1]);
      ctx.lineTo(g.X(S.ux * S.c + nx - S.uy * 10), g.Y(S.uy * S.c + ny + S.ux * 10));
      ctx.lineTo(g.X(S.ux * S.c + nx + S.uy * 10), g.Y(S.uy * S.c + ny - S.ux * 10));
      ctx.closePath(); ctx.fill(); ctx.restore();
    }
    const ma = seg(.4, .3);
    line(uline(g, S, S.mA), {color: C.ink, width: 1.2, dash: [6, 4], progress: ma});
    line(uline(g, S, S.mB), {color: C.ink, width: 1.2, dash: [6, 4], progress: ma});
    line(uline(g, S, S.c), {color: C.ink, width: 2.2, progress: seg(.26, .36)});
    for (let i = 0; i < DA.x.length; i++)
      mark(g.X(DA.x[i][0]), g.Y(DA.x[i][1]), DA.y[i] > 0 ? 1 : 0, arrive(.04 + .22 * (DA.x[i][0] + 3) / 6));
    const sa = arrive(.6);
    for (let i = 0; i < DA.x.length; i++) {
      const s = S.ux * DA.x[i][0] + S.uy * DA.x[i][1];
      if (Math.abs(s - (DA.y[i] > 0 ? S.mA : S.mB)) < 2e-3) ring(g.X(DA.x[i][0]), g.Y(DA.x[i][1]), 9.5, {alpha: sa});
    }
  });
  const da = arrive(.7);
  if (da > 0) {
    // the street is as wide everywhere: its dimension sits up its far end, where neither it nor
    // its label meets a point at any angle of the swing (2.6 along the boundary from the centre)
    const along = 2.6, bx = S.ux * S.c - S.uy * along, by = S.uy * S.c + S.ux * along;
    const h = S.w / 2, p0 = [g.X(bx - S.ux * h), g.Y(by - S.uy * h)], p1 = [g.X(bx + S.ux * h), g.Y(by + S.uy * h)];
    arrow(p0[0], p0[1], p1[0], p1[1], {width: 1.1, head: 7, both: true, color: C.accent, alpha: da});
    text('margin ' + S.w.toFixed(2), p1[0] + 16, p1[1] + 4, {size: 16, color: C.accent, alpha: da});
  }
  const h = axes({...PC, xlim: [DA.th - 24, DA.th + 24], ylim: [0, 1.4],
    xticks: [-20, -10, 0, 10, 20].map(v => DA.th + v), yticks: [0, .4, .8, 1.2],
    xfmt: v => fmt(Math.round(v - DA.th)), yfmt: v => v === 0 ? '0' : v.toFixed(1),
    xlabel: '\\rm{boundary rotation (deg)}', ylabel: '\\rm{margin}', ylabelGap: 46, tickSize: 16, progress: seg(.08, .35)});
  const pts = DA.tg.map((v, i) => [h.X(v), h.Y(Math.max(0, DA.mg[i]))]);
  h.inside(() => line(pts, {color: C.navy, width: 2.2, progress: seg(.2, .42)}));
  const pk = arrive(.62);
  line([[h.X(DA.th), h.Y(DA.wmax)], [h.X(DA.th), PC.y + PC.h]], {color: C.guide, width: 1, dash: [5, 4], alpha: pk});
  text('widest: the SVM', h.X(DA.th) + 8, h.Y(DA.wmax) - 8, {size: 16, color: C.body, alpha: pk});
  dot(h.X(th), h.Y(S.w), 5.5, {color: '#fff', fill: C.accent, width: 1.4, alpha: arrive(.5)});
}

/* ------------------------------------------------------------ (b) the RBF SVM
   f(x) = b + sum over the support vectors of alpha_i y_i exp(-gamma |x - x_i|^2),
   evaluated here from DATA: the page draws the model's own heights */
const SVI = DB.sv, SVX = SVI.map(i => DB.x[i]), CO = DB.co, B0 = DB.b0, GAM = DB.gamma;
const SVS = new Set(SVI);
function fx(x, y) {
  let s = B0;
  for (let k = 0; k < CO.length; k++) { const dx = x - SVX[k][0], dy = y - SVX[k][1]; s += CO[k] * Math.exp(-GAM * (dx * dx + dy * dy)); }
  return s;
}
const NS = DB.ns, SG = DB.sg, SF = DB.sf;          // SF[j * NS + i] = f(SG[i], SG[j])
const ZL = 3, HZ = .5;                             // the box: f from -3 to 3, half as tall as it is wide
const FMAX = Math.max(...SF) + .05;
const CAM = {az: 34, el: 34};                      // the 3-D view (deg); a drag moves it
const S3 = 124, C3 = {x: PB.x + SQ / 2 + 2, y: PB.y + SQ / 2 + 4};

/* the camera between straight above (lam 0: the plane as a 2-D plot) and the 3-D view (lam 1) */
function camera(lam) {
  const az = rad(lerp(0, CAM.az, lam)), el = rad(lerp(90, CAM.el, lam));
  const cx = lerp(PB.x + SQ / 2, C3.x, lam), cy = lerp(PB.y + SQ / 2, C3.y, lam);
  const ca = Math.cos(az), sa = Math.sin(az), se = Math.sin(el), ce = lam > 0 ? Math.cos(el) : 0;
  // the scale: from the 2-D plot's to the 3-D view's, but never so large that a corner of the box
  // reaches the titles, the arrow or the figure's edge (a turned or steep view needs less)
  // (what is drawn counts: the walls' top once they show, the f axis's numbers on the left once they show)
  let s = lerp(SQ / 2, S3, lam);
  const left = lerp(PB.x - 36, PB.x - 6, clamp((lam - .5) / .2)), top = HZ * clamp((lam - .72) / .2);
  for (const x of [-1, 1]) for (const y of [-1, 1]) for (const z of [-HZ, 0, top]) {
    const a = x * ca - y * sa, b = (x * sa + y * ca) * se + z * ce;
    if (a > 1e-9) s = Math.min(s, (976 - cx) / a); else if (a < -1e-9) s = Math.min(s, (cx - left) / -a);
    if (b > 1e-9) s = Math.min(s, (cy - 54) / b); else if (b < -1e-9) s = Math.min(s, (PD.y - 70 - cy) / -b);
  }
  const P = (x, y, z) => {
    const xn = x / LIMX, yn = y / LIMX, zn = z / ZL * HZ, xr = xn * ca - yn * sa, yr = xn * sa + yn * ca;
    return [cx + s * xr, cy - s * (yr * se + zn * ce)];
  };
  return {P, lam, az, el, s, cx, cy, ca, sa, se, ce, key: az.toFixed(5) + ':' + el.toFixed(5)};
}

/* the faces of the mesh, split where they cross the plane z = 0: below it and above it */
const FACES = [[], []];
(function () {
  const clip = (poly, up) => {
    const out = [];
    for (let k = 0; k < poly.length; k++) {
      const p = poly[k], q = poly[(k + 1) % poly.length];
      const pin = up ? p[2] >= 0 : p[2] <= 0, qin = up ? q[2] >= 0 : q[2] <= 0;
      if (pin) out.push(p);
      if (pin !== qin) { const s = p[2] / (p[2] - q[2]); out.push([lerp(p[0], q[0], s), lerp(p[1], q[1], s), 0]); }
    }
    return out;
  };
  for (let j = 0; j < NS - 1; j++) for (let i = 0; i < NS - 1; i++) {
    const v = (a, b) => [SG[a], SG[b], SF[b * NS + a]];
    const poly = [v(i, j), v(i + 1, j), v(i + 1, j + 1), v(i, j + 1)];
    const x = (SG[i] + SG[i + 1]) / 2, y = (SG[j] + SG[j + 1]) / 2;
    for (const up of [0, 1]) {
      const p = clip(poly, up); if (p.length < 3) continue;
      FACES[up].push({p, x, y, z: p.reduce((a, q) => a + q[2], 0) / p.length});
    }
  }
})();
/* the surface's colour: pale blues by height (a pgfplots colormap), faceted */
const CMAP = [[-3, '#FFFFFF'], [-1, '#F3F6F9'], [0, '#E3EBF2'], [1, '#CBDAE7'], [2, '#ADC5DB'], [3, '#8CAECE']];
function cmap(z) {
  for (let k = 1; k < CMAP.length; k++) if (z <= CMAP[k][0] || k === CMAP.length - 1)
    return mixc(CMAP[k - 1][1], CMAP[k][1], (z - CMAP[k - 1][0]) / (CMAP[k][0] - CMAP[k - 1][0]));
}
const FLAT = ['#FFFFFF', '#EBF1F6'];                // seen from above: white, and class A's side as in 2-D
function faceStyle(F, up, m) {                     // cached per face, m in steps of 1/64
  const k = Math.round(m * 64);
  if (F.sk === k) return F.sv;
  const a = hexc(FLAT[up]), b = hexc(F.c || (F.c = cmapHex(F.z))), mm = k / 64;
  const fill = a.map((v, i) => Math.round(lerp(v, b[i], mm)));
  const mesh = hexc(C.sky), st = fill.map((v, i) => Math.round(lerp(v, mesh[i], .5 * mm)));
  F.sk = k; F.sv = ['rgb(' + fill.join(',') + ')', 'rgb(' + st.join(',') + ')'];
  return F.sv;
}
function cmapHex(z) {
  const s = cmap(z).slice(4, -1).split(',').map(Number);
  return '#' + s.map(v => v.toString(16).padStart(2, '0')).join('');
}
const _order = [{}, {}];
function sorted(cam, up) {                          // back to front: a height field needs only the horizontal depth
  const o = _order[up];
  if (o.k !== cam.key) {
    const d = FACES[up].map((F, i) => [F.x * cam.sa + F.y * cam.ca, i]);
    d.sort((a, b) => b[0] - a[0]);
    o.i = d.map(e => e[1]); o.k = cam.key;
  }
  return o.i;
}
function faces(cam, up, m) {
  ctx.save(); ctx.lineWidth = .7; ctx.lineJoin = 'round';
  for (const i of sorted(cam, up)) {
    const F = FACES[up][i], [fill, st] = faceStyle(F, up, m);
    ctx.beginPath();
    F.p.forEach((q, k) => { const r = cam.P(q[0], q[1], q[2]); k ? ctx.lineTo(r[0], r[1]) : ctx.moveTo(r[0], r[1]); });
    ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = st; ctx.stroke();
  }
  ctx.restore();
}
/* the height the drawn mesh has at (x, y): bilinear between its nodes */
function fb(x, y) {
  const u = clamp((x + LIMX) / (2 * LIMX) * (NS - 1), 0, NS - 1 - 1e-9), v = clamp((y + LIMX) / (2 * LIMX) * (NS - 1), 0, NS - 1 - 1e-9);
  const i = Math.floor(u), j = Math.floor(v), a = u - i, b = v - j, k = j * NS + i;
  return (1 - b) * ((1 - a) * SF[k] + a * SF[k + 1]) + b * ((1 - a) * SF[k + NS] + a * SF[k + NS + 1]);
}
/* does the camera see (x, y, z) past the surface? 1 seen, 0 behind it; a ray marched toward the eye */
function seen(cam, x, y, z) {
  if (cam.el > rad(78)) return 1;
  const rise = Math.tan(cam.el) * ZL / (HZ * LIMX), dx = -cam.sa, dy = -cam.ca, st = .05;
  let m = 1e9;
  for (let d = st; ; d += st) {
    const X = x + dx * d, Y = y + dy * d, zr = z + rise * d;
    if (Math.abs(X) > LIMX || Math.abs(Y) > LIMX || zr > FMAX) break;
    m = Math.min(m, zr - fb(X, Y));
  }
  return clamp((m + .06) / .12);
}
const _seen = {};
function seenPts(cam) {                             // the points, cached per view
  if (_seen.k !== cam.key) {
    _seen.k = cam.key;
    _seen.p = DB.x.map((p, i) => seen(cam, p[0], p[1], DB.f[i]));
    _seen.c = {};
    for (const [key, z] of [['m', -1], ['0', 0], ['p', 1]])
      _seen.c[key] = DB.c[key].map(ln => ln.map((p, i) => i % 3 ? null : seen(cam, p[0], p[1], z)));
  }
  return _seen;
}
/* a polyline in 3-D drawn in runs by how much of it is seen */
function runs(cam, pts, vis, o) {
  const n = pts.length, q = pts.map(p => cam.P(p[0], p[1], p[2]));
  const level = i => Math.round(clamp(vis(i)) * 4) / 4;
  let i0 = 0;
  for (let i = 1; i <= n; i++) {
    if (i === n || level(i) !== level(i0)) {
      const a = level(i0);
      if (a > 0) line(q.slice(i0, Math.min(n, i + 1)), {...o, alpha: (o.alpha ?? 1) * a});
      i0 = i;
    }
  }
}
const visAt = arr => i => { if (arr[i] !== null && arr[i] !== undefined) return arr[i];
  const a = i - i % 3, b = Math.min(arr.length - 1, a + 3), s = (i - a) / Math.max(1, b - a);
  return lerp(arr[a], arr[b] ?? arr[a], s); };

/* the line of (b'): through the centre at angle psi, turning 60 deg every 7 s */
const PSI0 = -30, SL = 3;                          // the line runs from -3 to 3
function psiAt() {
  const T0 = 2.0, R = 5.0, G = 2.0, P = R + G;
  if (t < T0 + R) return PSI0;
  const n = Math.floor((t - T0 - R) / P), dt = t - T0 - R - n * P;
  return PSI0 + 60 * (n + sp(dt, G));
}
function sliceOf(psi) {
  const ux = Math.cos(rad(psi)), uy = Math.sin(rad(psi)), N = 129, s = [], f = [];
  for (let k = 0; k < N; k++) { const v = -SL + 2 * SL * k / (N - 1); s.push(v); f.push(fx(v * ux, v * uy)); }
  const zeros = [];
  for (let k = 1; k < N; k++) if ((f[k - 1] < 0) !== (f[k] < 0)) {
    let a = s[k - 1], b = s[k], fa = f[k - 1];
    for (let it = 0; it < 48; it++) { const m = (a + b) / 2, fm = fx(m * ux, m * uy); if ((fm < 0) === (fa < 0)) { a = m; fa = fm; } else b = m; }
    zeros.push((a + b) / 2);
  }
  const bumps = SVX.map((p, k) => ({s: p[0] * ux + p[1] * uy, h: CO[k] * Math.exp(-GAM * Math.pow(-p[0] * uy + p[1] * ux, 2))}));
  return {ux, uy, s, f, zeros, bumps};
}

/* the reader's view: the tour until the reader takes over */
const VIEW = {user: null};
const tourAt = () => cycle(3.2, [[1, 6.0], [0, 12.0]], 2.0);
function lamAt() {
  const u = VIEW.user;
  if (!u) return STILL ? cyc(tourAt()) : cyc(tourAt());
  return INSTANT ? u.to : lerp(u.from, u.to, sp(TU() - u.t0, 1.8));
}
const target = () => VIEW.user ? VIEW.user.to : tourAt().to;
/* the comparison the arrow shows: while hovered, focused or pinned */
const CMP = {hover: false, focus: false, pin: false, from: 0, to: 0, t0: -1e9};
const cmpAt = () => INSTANT ? CMP.to : lerp(CMP.from, CMP.to, sp(TU() - CMP.t0, CMP.to ? .28 : .22));

function drawB(sl) {
  const lam = lamAt(), cam = camera(lam), L = LIMX, P = cam.P;
  sub('b', PB.x - 60, 34, 'nonlinear SVM, RBF kernel', arrive(.06));
  // the walls come last, once the box has shrunk to its place (its top would cross the titles before)
  const up = clamp((lam - .72) / .2), m = clamp((lam - .04) / .5), solid = lam > .004;
  const pa = seg(.04, .35), ga = arrive(.36), la = seg(.4, .3), cmp = cmpAt();
  // the box: its floor is the 2-D plot's frame; walls, grid and the f axis rise with the view
  const F = (x, y) => P(x, y, -ZL), T = (x, y) => P(x, y, ZL);
  if (up > 0) {
    for (const z of [-2, -1, 0, 1, 2])
      line([P(-L, L, z), P(L, L, z), P(L, -L, z)], {color: C.grid, width: 1, alpha: up});
    line([F(-L, L), T(-L, L), T(L, L), T(L, -L), F(L, -L)], {color: C.ink, width: 1.1, alpha: up});
    line([F(L, L), T(L, L)], {color: C.ink, width: 1.1, alpha: up});
  }
  const back = () => {
    line([F(-L, L), F(L, L), F(L, -L)], {color: C.ink, width: 1.3, progress: pa});
    for (const v of [-3, -2, -1, 0, 1, 2, 3]) {
      line([F(v, L), F(v, L - 5 / cam.s * L)], {color: C.ink, width: 1.1, alpha: clamp(pa * 1.4)});
      line([F(L, v), F(L - 5 / cam.s * L, v)], {color: C.ink, width: 1.1, alpha: clamp(pa * 1.4)});
    }
  };
  back();
  const V = solid ? seenPts(cam) : null, vp = i => V ? V.p[i] : 1;
  const pts = (cls) => {
    for (let i = 0; i < DB.x.length; i++) {
      if ((DB.y[i] > 0) !== cls) continue;
      const [x, y] = DB.x[i], q = P(x, y, DB.f[i]), a = arrive(.04 + .22 * (x + 3) / 6) * vp(i);
      mark(q[0], q[1], DB.y[i] > 0 ? 1 : 0, a);
      // while the arrow compares: the points the straight line gets wrong, in crimson
      if (cmp > .005 && WRONG[i]) ring(q[0], q[1], 4.6, {width: 1.6, alpha: cmp * a});
      if (SVS.has(i)) ring(q[0], q[1], 9.5, {alpha: arrive(.6) * vp(i) * (1 - .75 * cmp)});
    }
  };
  const contour = (key, z, dash, width, prog) => {
    for (let n = 0; n < DB.c[key].length; n++) {
      const ln = DB.c[key][n];
      if (!solid || prog < 1) { line(ln.map(p => P(p[0], p[1], z)), {color: C.ink, width, dash, progress: prog}); continue; }
      runs(cam, ln.map(p => [p[0], p[1], z]), visAt(V.c[key][n]), {color: C.ink, width, dash});
    }
  };
  // the line of (b'): its profile on the surface, straight from above
  const prof = (upper) => {
    const pts3 = sl.s.map((s, k) => [s * sl.ux, s * sl.uy, sl.f[k]]);
    const pr = seg(.5, .45), wd = lerp(1.4, 2.2, lam), fa = 1 - .7 * cmp;
    // split at the zeros, keep the part on this side of the plane
    const segs = []; let cur = [];
    for (let k = 0; k < pts3.length; k++) {
      const p = pts3[k], on = upper ? p[2] >= 0 : p[2] < 0;
      if (k > 0 && (pts3[k - 1][2] >= 0) !== (p[2] >= 0)) {
        const q = pts3[k - 1], s = q[2] / (q[2] - p[2]), c = [lerp(q[0], p[0], s), lerp(q[1], p[1], s), 0];
        if (on) { cur = [c]; } else { cur.push(c); segs.push(cur); cur = []; }
      }
      if (on) cur.push(p);
    }
    if (cur.length > 1) segs.push(cur);
    for (const sgm of segs) {
      if (!solid || pr < 1) { line(sgm.map(p => P(p[0], p[1], p[2])), {color: C.blue, width: wd, progress: pr, alpha: fa}); continue; }
      const v = sgm.map(p => seen(cam, p[0], p[1], p[2]));
      runs(cam, sgm, i => v[i], {color: C.blue, width: wd, alpha: fa});
    }
  };
  // below the plane
  if (solid) faces(cam, 0, m);
  if (solid) back_ghost(cam, lam, pa, back);
  const pl = clamp((lam - .1) / .4);
  if (cmp > .005 && pl < 1) wash(cam, cmp * (1 - pl));
  prof(false);
  contour('m', -1, [6, 4], 1.2, la);
  pts(false);
  // the plane f = 0: a translucent sheet once lifted; class A's side of it tinted, as in 2-D
  if (pl > 0) {
    const cn = [P(-L, -L, 0), P(L, -L, 0), P(L, L, 0), P(-L, L, 0)];
    ctx.save(); ctx.globalAlpha = .5 * pl; ctx.fillStyle = C.steel; ctx.beginPath();
    cn.forEach((q, k) => k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.closePath(); ctx.fill(); ctx.restore();
    line([...cn, cn[0]], {color: C.ink, width: 1.1, alpha: pl});
  }
  if (ga > 0) {
    ctx.save(); ctx.globalAlpha = .7 * ga; ctx.fillStyle = C.steel; ctx.beginPath();
    for (const ln of DB.c['0']) { ln.forEach((p, k) => { const q = P(p[0], p[1], 0); k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); }); ctx.closePath(); }
    ctx.fill('evenodd'); ctx.restore();
  }
  if (cmp > .005 && pl > 0) wash(cam, cmp * pl);
  if (cmp > .005) bestLine(cam, cmp);
  // above the plane
  if (solid) faces(cam, 1, m);
  contour('0', 0, null, 2.2, seg(.26, .36));
  prof(true);
  contour('p', 1, [6, 4], 1.2, la);
  pts(true);
  // the plane's name, along its far left edge; gone where the view is too turned or steep for it,
  // and where the plane is seen nearly edge on and its name would sit among the points
  const lb = clamp((lam - .8) / .15) * clamp((72 - CAM.az) / 10) * clamp((62 - CAM.el) / 10) * clamp((CAM.el - 10) / 4);
  if (lb > 0) {
    const p = P(-.62 * L, L, 0), q = P(-.3 * L, L, 0), an = Math.atan2(q[1] - p[1], q[0] - p[0]);
    math('f = 0', p[0] + Math.sin(an) * 7, p[1] - Math.cos(an) * 7, {size: 16, color: C.body, rot: an, alpha: lb});
  }
  // where the line of (b') crosses the boundary
  const za = arrive(.85);
  for (const s0 of sl.zeros) {
    const q = P(s0 * sl.ux, s0 * sl.uy, 0), v = solid ? seen(cam, s0 * sl.ux, s0 * sl.uy, 0) : 1;
    dot(q[0], q[1], 4.2, {color: '#fff', fill: C.accent, width: 1.2, alpha: za * v * (1 - .7 * cmp)});
  }
  // the line's direction, seen from above
  const ta = seg(.5, .45) * (1 - clamp(lam * 4)) * (1 - .7 * cmp);
  if (ta > 0) {
    const e = P(SL * sl.ux, SL * sl.uy, 0), d = P((SL - .3) * sl.ux, (SL - .3) * sl.uy, 0);
    arrow(d[0], d[1], e[0], e[1], {color: C.blue, width: 1.4, head: 9, alpha: ta});
  }
  front(cam, pa);
}
/* the floor's far edges and ticks, drawn again over the faces while the view is still nearly flat */
function back_ghost(cam, lam, pa, back) {
  const g = 1 - clamp(lam / .15);
  if (g <= 0) return;
  ctx.save(); ctx.globalAlpha *= g; back(); ctx.restore();
}
/* the best straight line on the rings (DATA), on the plane f = 0, and the side it calls class A */
const WRONG = DB.x.map((p, i) => (DB.line.w[0] * p[0] + DB.line.w[1] * p[1] + DB.line.c > 0 ? 1 : -1) !== DB.y[i]);
const HALF = (() => {
  const [wx, wy] = DB.line.w, c = DB.line.c, L = LIMX;
  const sq = [[-L, -L], [L, -L], [L, L], [-L, L]], half = [], edge = [];
  for (let k = 0; k < 4; k++) {
    const p = sq[k], q = sq[(k + 1) % 4], fp = wx * p[0] + wy * p[1] + c, fq = wx * q[0] + wy * q[1] + c;
    if (fp >= 0) half.push(p);
    if ((fp >= 0) !== (fq >= 0)) { const s = fp / (fp - fq), r = [lerp(p[0], q[0], s), lerp(p[1], q[1], s)]; half.push(r); edge.push(r); }
  }
  return {half, edge};
})();
function wash(cam, a) {
  ctx.save(); ctx.globalAlpha = .8 * a; ctx.fillStyle = C.wash; ctx.beginPath();
  HALF.half.forEach((p, k) => { const q = cam.P(p[0], p[1], 0); k ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); });
  ctx.closePath(); ctx.fill(); ctx.restore();
}
function bestLine(cam, a) {
  const e = HALF.edge;
  if (e.length === 2) line([cam.P(e[0][0], e[0][1], 0), cam.P(e[1][0], e[1][1], 0)], {color: C.accent, width: 2.2, alpha: a});
}
/* the box's near edges, the ticks and their numbers: a pgfplots axis that turns with the view */
const TICKS = [-3, -2, -1, 0, 1, 2, 3], ZT = [-2, -1, 0, 1, 2];
function front(cam, pa) {
  let up;
  const L = LIMX, P = cam.P, F = (x, y) => P(x, y, -ZL), lam = cam.lam;
  const ta = clamp(pa * 1.4);
  line([F(-L, L), F(-L, -L), F(L, -L)], {color: C.ink, width: 1.3, progress: pa});
  const out = (a, b) => {                        // the outward normal of a floor edge, on screen
    const p = F(a[0], a[1]), q = F(b[0], b[1]), c = F(0, 0), mx = (p[0] + q[0]) / 2 - c[0], my = (p[1] + q[1]) / 2 - c[1];
    let nx = q[1] - p[1], ny = p[0] - q[0]; const n = Math.hypot(nx, ny) || 1; nx /= n; ny /= n;
    if (nx * mx + ny * my < 0) { nx = -nx; ny = -ny; }
    return [nx, ny];
  };
  const place = (s, p, n, size, a = 1) => {      // a number just outside the edge, along its normal
    const w = mw(s, size), g = lerp(8, 10.5, Math.abs(n[1])), e = Math.abs(n[0]) * w / 2 + Math.abs(n[1]) * size * .35;
    math(s, p[0] + n[0] * (g + e), p[1] + n[1] * (g + e) + size * .35, {size, align: 'center', alpha: ta * a});
  };
  const nx = out([-L, -L], [L, -L]), ny = out([-L, -L], [-L, L]);
  // an axis seen end on (a drag to its extremes) packs its numbers together: they go before they touch
  const room = (a, b) => { const p = F(a[0], a[1]), q = F(b[0], b[1]);
    return clamp(1 + Math.max(Math.abs(q[0] - p[0]) - 17, Math.abs(q[1] - p[1]) - 12) / 3); };
  const rx = room([0, -L], [1, -L]), ry = room([-L, 0], [-L, 1]);
  for (const v of TICKS) {
    const px = F(v, -L), py = F(-L, v);
    line([px, F(v, -L + 5 / cam.s * L)], {color: C.ink, width: 1.1, alpha: ta});
    line([py, F(-L + 5 / cam.s * L, v)], {color: C.ink, width: 1.1, alpha: ta});
    // in 3-D the two axes meet at the near corner: one -3 there is enough
    place(fmt(v), px, nx, 16, rx); place(fmt(v), py, ny, 16, ry * (v === -3 ? 1 - clamp((lam - .1) / .25) : 1));
  }
  // the axis labels: under and beside the plot from above, off the near edges' middles in 3-D
  const mxp = F(0, -L), myp = F(-L, 0);
  const x1 = [lerp(mxp[0], mxp[0] + nx[0] * 44, lam), lerp(mxp[1] + 48, mxp[1] + nx[1] * 44 + 6, lam)];
  const x2 = [lerp(myp[0] - 40, myp[0] + ny[0] * 46, lam), lerp(myp[1], myp[1] + ny[1] * 46 + 6, lam)];
  math('x_{1}', x1[0], x1[1], {size: 17, align: 'center', alpha: ta});
  math('x_{2}', x2[0], x2[1], {size: 17, align: 'center', rot: -Math.PI / 2 * (1 - lam), alpha: ta});
  // the f axis, on the left wall's edge, once the box is tall enough to carry it
  up = clamp((cam.s * HZ / ZL * cam.ce - 14) / 3) * clamp((lam - .5) / .2);
  if (up > 0) {
    for (const z of ZT) {
      const p = P(-L, L, z);
      line([p, P(-L + 5 / cam.s * L / Math.max(.2, Math.cos(cam.az)), L, z)], {color: C.ink, width: 1.1, alpha: up});
      math(fmt(z), p[0] - 8, p[1] + 5.6, {size: 16, align: 'right', alpha: up});
    }
    const zp = P(-L, L, 0);
    math('f', zp[0] - 34, zp[1] + 5, {size: 17, align: 'center', alpha: up});
  }
}

/* ------------------------------------------------------------ (b') f along the line */
function drawBp(sl) {
  const g = axes({...PD, xlim: [-SL, SL], ylim: [-4.6, 5], xticks: [-3, -2, -1, 0, 1, 2, 3],
    yticks: [-4, -2, 0, 2, 4], xlabel: '\\rm{position along the line}', ylabel: 'f', ylabelGap: 36,
    tickSize: 16, progress: seg(.1, .35)});
  const ba = arrive(.55), ca = seg(.3, .45), za = arrive(.85), N = 97;
  // the decision function the curves below add up, and the surface of the 3-D view is
  math('f(x) = b + \\Sigma_{i}\\ \\alpha_{i} y_{i}\\ \\rm{exp}(-\\gamma\\, |x - x_{i}|^{2})', PD.x + PD.w / 2, PD.y - 14,
       {size: 16, align: 'center', alpha: arrive(.8)});
  g.inside(() => {
    line([[PD.x, g.Y(0)], [PD.x + PD.w, g.Y(0)]], {color: C.ink, width: 1, alpha: arrive(.45)});
    line([[PD.x, g.Y(B0)], [PD.x + PD.w, g.Y(B0)]], {color: C.guide, width: 1, dash: [5, 4], alpha: arrive(.45)});
    for (const bp of sl.bumps) {
      const pts = [];
      for (let k = 0; k < N; k++) { const s = -SL + 2 * SL * k / (N - 1); pts.push([g.X(s), g.Y(B0 + bp.h * Math.exp(-GAM * (s - bp.s) * (s - bp.s)))]); }
      line(pts, {color: C.mist, width: 1.1, alpha: ba});
    }
    line(sl.s.map((s, k) => [g.X(s), g.Y(sl.f[k])]), {color: C.blue, width: 2.4, progress: ca});
  });
  for (const s0 of sl.zeros) dot(g.X(s0), g.Y(0), 4.2, {color: '#fff', fill: C.accent, width: 1.2, alpha: za});
  // what the curves are
  const la = arrive(.8), ly = PD.y + 20;
  line([[PD.x + 10, ly - 5], [PD.x + 30, ly - 5]], {color: C.mist, width: 1.1, alpha: la});
  text('bump per support vector', PD.x + 36, ly, {size: 16, color: C.ink, alpha: la});
  const kw = mw('b + \\rm{their sum}', 16), kx = PD.x + PD.w - 8 - kw;
  line([[kx - 26, ly - 5], [kx - 6, ly - 5]], {color: C.blue, width: 2.4, alpha: la});
  math('b + \\rm{their sum}', kx, ly, {size: 16, alpha: la});
  math('b', PD.x + PD.w + 7, g.Y(B0) + 5.6, {size: 16, color: C.body, alpha: la});
}

/* ------------------------------------------------------------ the arrow from (a) to (b) */
const AR = {x0: PA.x + SQ + 16, x1: PB.x - 60, y: PB.y + SQ / 2 + 4};
/* the arrow's hit area: its label and the free space under it (70 units, 24 CSS px on a phone);
   while the comparison shows, the numbers under it too, so the pointer can move down to read them */
const inArrow = (X, Y) => X > AR.x0 - 8 && X < AR.x1 + 8 && Y > AR.y - 34 && Y < AR.y + (CMP.to ? 112 : 36);
function drawArrow() {
  const a = seg(.55, .35), cmp = cmpAt(), col = cmp > .01 ? mixc(C.ink, C.accent, cmp) : C.ink;
  if (a > 0) {
    line([[AR.x0, AR.y], [lerp(AR.x0, AR.x1 - 6, a), AR.y]], {color: col, width: 1.5});
    if (a >= 1) arrow(AR.x1 - 12, AR.y, AR.x1, AR.y, {color: col, width: 1.5, head: 10});
  }
  const mx = (AR.x0 + AR.x1) / 2;
  text('add a kernel', mx, AR.y - 11, {size: 16, color: C.body, align: 'center', alpha: arrive(.75)});
  if (cmp > .005) {
    text('straight line', mx, AR.y + 34, {size: 16, color: C.accent, align: 'center', alpha: cmp});
    text(Math.round(100 * DB.line.n / DB.n) + '%', mx, AR.y + 54, {size: 17, color: C.accent, align: 'center', alpha: cmp});
    text('RBF kernel', mx, AR.y + 82, {size: 16, color: C.ink, align: 'center', alpha: cmp});
    text('100%', mx, AR.y + 102, {size: 17, color: C.ink, align: 'center', alpha: cmp});
  }
}

/* ------------------------------------------------------------ the legend and the parameters */
function legendRow(y, rows, a) {
  if (a <= 0) return;
  const gap = 26, kw = 30, ws = rows.map(r => kw + 8 + mw(r[1], 16));
  const tot = ws.reduce((s, v) => s + v, 0) + gap * (rows.length - 1), x0 = (W - tot) / 2;
  box(x0 - 14, y, tot + 28, 30, {fill: '#fff', stroke: C.ink, width: 1, alpha: a});
  let x = x0;
  rows.forEach(([key, lab], i) => {
    ctx.save(); ctx.globalAlpha *= a; key(x + kw / 2, y + 15); ctx.restore();
    math(lab, x + kw + 8, y + 21, {size: 16, alpha: a});
    x += ws[i] + gap;
  });
}
function draw() {
  drawA();
  const sl = sliceOf(psiAt());
  drawB(sl); drawBp(sl); drawArrow();
  if (!STILL) hint();
  legendRow(PC.y + PC.h + 66, [
    [(x, y) => mark(x, y, 1, 1), '\\rm{class A}'],
    [(x, y) => mark(x, y, 0, 1), '\\rm{class B}'],
    [(x, y) => { mark(x, y, 1, 1); ring(x, y, 9.5); }, '\\rm{support vector}'],
    [(x, y) => line([[x - 13, y], [x + 13, y]], {width: 2.2}), '\\rm{decision boundary},\\ f = 0'],
    [(x, y) => line([[x - 13, y], [x + 13, y]], {width: 1.2, dash: [6, 4]}), '\\rm{margins},\\ f = \\pm 1'],
  ], arrive(.7));
  // short of the controls in the corner (the 3-D button stays there in the guide's page)
  math('\\rm{scaled features; (a) hard margin; (b)}\\ \\gamma\\ = 0.5,\\ C = 10', 18, H - 14,
       {size: 15, color: C.muted, alpha: arrive(.9)});
}
const TAP = matchMedia('(hover: none)').matches;      // a touch screen: tap, not click
function hint() {
  const to = target(), a = arrive(1.2), w = TAP ? 'tap' : 'click';
  const s = to > .5 ? 'drag to turn, ' + w + ' for 2D' : w + ' for the 3D view';
  text(s, W - 18, 34, {size: 16, color: C.muted, align: 'right', alpha: .9 * a});
}

/* ------------------------------------------------------------ the reader */
function reset() {                                 // the restart button: the tour again, nothing pinned
  VIEW.user = null; CAM.az = 34; CAM.el = 34;
  CMP.pin = false; CMP.to = CMP.from = CMP.hover || CMP.focus ? 1 : 0; CMP.t0 = -1e9; sync();
}
let _rq = false;
function busy() { const n = TU(); return (VIEW.user && n - VIEW.user.t0 < 5) || n - CMP.t0 < 1.5; }
function kick() {                                    // draw while a transition runs, even when paused
  if (_rq) return; _rq = true;
  requestAnimationFrame(() => { _rq = false; if (!(playing && visible)) render(); if (!INSTANT && busy()) kick(); });
}
function toggleView() {
  const l = lamAt(), to = target() > .5 ? 0 : 1;
  VIEW.user = {from: l, to, t0: TU()}; sync(); kick();
}
function cmpSet() {
  const on = CMP.hover || CMP.focus || CMP.pin ? 1 : 0;
  if (on !== CMP.to) { CMP.from = cmpAt(); CMP.to = on; CMP.t0 = TU(); }
  sync(); kick();
}
let B3 = null, BA = null;
function sync() {
  if (B3) B3.setAttribute('aria-pressed', String(target() > .5));
  if (BA) BA.setAttribute('aria-pressed', String(CMP.pin));
}
if (!STILL) {
  const FIG = document.querySelector('.fig'), ctl = FIG.querySelector('.ctl');
  const css = document.createElement('style');
  css.textContent = '#v3 svg{fill:none!important;stroke:currentColor;stroke-width:1.5;stroke-linejoin:round;width:50%!important;height:50%!important}' +
    '#v3[aria-pressed=true]{background:#043052;color:#fff;border-color:#043052}' +
    '.nfa{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;outline:none;color:transparent}' +
    '.nfa:focus-visible{outline:2px solid #095A94;outline-offset:2px}';
  document.head.appendChild(css);
  B3 = document.createElement('button'); B3.id = 'v3'; B3.type = 'button';
  B3.setAttribute('aria-label', 'Show (b) in 3-D: the decision function f as a surface');
  B3.innerHTML = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.8l5.4 3v6.4L8 14.2l-5.4-3V4.8z"/><path d="M2.6 4.8L8 7.8l5.4-3M8 7.8v6.4"/></svg>';
  B3.addEventListener('click', e => { e.stopPropagation(); toggleView(); });
  ctl.insertBefore(B3, ctl.firstChild);
  BA = document.createElement('button'); BA.type = 'button'; BA.className = 'nfa'; BA.textContent = 'add a kernel';
  BA.setAttribute('aria-label', 'Add a kernel: the best straight line separates ' + Math.round(100 * DB.line.n / DB.n) +
    '% of the rings, the RBF kernel 100%');
  BA.addEventListener('click', e => { e.stopPropagation(); CMP.pin = !CMP.pin; cmpSet(); });
  BA.addEventListener('focus', () => { CMP.focus = true; cmpSet(); });
  BA.addEventListener('blur', () => { CMP.focus = false; cmpSet(); });
  FIG.insertBefore(BA, ctl);
  const placeA = () => { const k = cv.clientWidth / W, px = v => (v * k).toFixed(1) + 'px';
    BA.style.left = px(AR.x0 - 8); BA.style.top = px(AR.y - 34); BA.style.width = px(AR.x1 - AR.x0 + 16); BA.style.height = px(48); };
  new ResizeObserver(placeA).observe(cv); placeA();
  sync();
  const toU = e => { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; };
  const inB = (X, Y) => !inArrow(X, Y) && X > PB.x - 46 && X < W - 4 && Y > 14 && Y < PB.y + SQ + 62;
  let drag = null, dragged = false;
  cv.style.touchAction = 'pan-y';
  cv.addEventListener('pointerdown', e => {
    const [X, Y] = toU(e); dragged = false;
    if (inB(X, Y) && lamAt() > .97) {
      drag = {x: e.clientX, y: e.clientY, az: CAM.az, el: CAM.el, moved: false};
      cv.setPointerCapture(e.pointerId);
    }
  });
  cv.addEventListener('pointermove', e => {
    if (drag) {
      const k = W / cv.getBoundingClientRect().width, dx = (e.clientX - drag.x) * k, dy = (e.clientY - drag.y) * k;
      if (!drag.moved && Math.hypot(dx, dy) > 6) { drag.moved = true; if (!VIEW.user) VIEW.user = {from: 1, to: 1, t0: TU() - 10}; }
      if (drag.moved) { CAM.az = clamp(drag.az - dx * .35, 0, 88); CAM.el = clamp(drag.el + dy * .3, 8, 75); cv.style.cursor = 'grabbing'; kick(); }
      return;
    }
    if (e.pointerType !== 'mouse') return;
    const [X, Y] = toU(e), h = inArrow(X, Y);
    if (h !== CMP.hover) { CMP.hover = h; cmpSet(); }
    cv.style.cursor = h ? 'pointer' : inB(X, Y) ? (target() > .5 ? 'grab' : 'pointer') : '';
  });
  const drop = () => { if (drag) { dragged = drag.moved; drag = null; cv.style.cursor = ''; } };
  cv.addEventListener('pointerup', drop);
  cv.addEventListener('pointercancel', drop);
  cv.addEventListener('pointerleave', () => { if (CMP.hover) { CMP.hover = false; cmpSet(); } });
  // a click on (b), its hint or the arrow is theirs, and so is the end of a drag wherever it is let
  // go: none of them also pauses (the engine toggles on a click; open ground still does)
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const [X, Y] = toU(e);
    if (dragged) { dragged = false; e.stopPropagation(); return; }
    if (inArrow(X, Y)) { e.stopPropagation(); CMP.pin = !CMP.pin; cmpSet(); return; }
    if (inB(X, Y)) { e.stopPropagation(); toggleView(); }
  }, true);
}
boot();
"""

TITLE = ("Figure 13: Linear SVM (left) draws a straight boundary when the classes are already "
         "separable that way")
ARIA = ("Left: two separable clouds of points, the widest street between them and its three support "
        "vectors circled, with a plot of the street's width peaking at the SVM's direction. Right: two "
        "concentric rings separated by a closed RBF kernel boundary, and below it the decision function "
        "along a line through the rings, the sum of one Gaussian bump per support vector; clicked, the "
        "right panel turns into a 3-D surface of that function, cut along the boundary by the flat "
        "plane f = 0.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, HPAGE, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.4, 0.8, 1.4, 3.5, 4.2, 5.5, 8.0, 12.0, 17.5]))
