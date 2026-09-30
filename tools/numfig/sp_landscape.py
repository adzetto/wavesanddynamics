"""Figure 3 of the signal processing document: convex versus nonconvex
optimization landscapes.

His caption: "Convex versus nonconvex optimization landscapes. In the convex
case, gradient descent reaches the same, globally optimal solution no matter
where it starts. In the nonconvex case, the starting point matters: a local
search started on the left settles into a local minimum that is not the best
possible solution, while one started on the right happens to reach the true
global minimum."

Model. Two objectives of one variable,
  (a) convex:     f(theta) = 0.9 (theta - 0.2)^2 - 0.3,
  (b) nonconvex:  f(theta) = (theta^2 - 1)^2 - 0.3 theta   (a tilted double well),
and plain gradient descent, theta_{k+1} = theta_k - eta f'(theta_k), started at
theta_0 = -1.6 (left) and +1.6 (right) in each, 20 steps, eta = 0.2 in (a) and
0.03 in (b). The iterates are computed here; the page draws them and lets the
marker glide from one to the next along the curve.

Run: python tools/numfig/sp_landscape.py  (writes the page, the still and the
check file; prints the key numbers).
"""
import os

import numpy as np

import common
import sp_model as SM

K = 20
STARTS = (-1.6, 1.6)
ETA = {"a": 0.2, "b": 0.03}
TILT = 0.3


def f_a(t):
    return 0.9 * (t - 0.2) ** 2 - 0.3


def g_a(t):
    return 1.8 * (t - 0.2)


def f_b(t):
    return (t * t - 1) ** 2 - TILT * t


def g_b(t):
    return 4 * t * (t * t - 1) - TILT


def descend(g, t0, eta, k=K):
    p = [t0]
    for _ in range(k):
        p.append(p[-1] - eta * g(p[-1]))
    return np.array(p)


def critical_b():
    """The critical points of (b): the three real roots of 4 t^3 - 4 t - c = 0,
    in closed form (trigonometric, three real roots)."""
    # t^3 + p t + q = 0 with p = -1, q = -c/4
    p, q = -1.0, -TILT / 4
    m = 2 * np.sqrt(-p / 3)
    th = np.arccos(3 * q / (p * m)) / 3
    return np.sort(m * np.cos(th - 2 * np.pi * np.arange(3) / 3))


JS = r"""
const D = DATA;
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);
const FA = th => 0.9 * (th - 0.2) ** 2 - 0.3, GA = th => 1.8 * (th - 0.2);
const FB = th => (th * th - 1) ** 2 - D.tilt * th, GB = th => 4 * th * (th * th - 1) - D.tilt;
const K = D.k;

/* ------------------------------------------------------------ clock
   Intro (README, round 2): axes and curves by .8 s, labels by 1.2 s. The
   descent starts at .6 s: one step every .22 s, each marker gliding to its
   next iterate along the curve; the runs rest, glide back and start again. */
const T0 = .6, STEP = .22, HOLD = 1.8, BACK = .9, REST = .35;
const RUNT = K * STEP, PER = RUNT + HOLD + BACK + REST;
function clock() {                      // iteration reached, glide within it, trail alpha
  if (t < T0) return {k: 0, s: 0, back: 0, trail: 1};
  const c = Math.floor((t - T0) / PER), u = t - T0 - c * PER, b0 = T0 + c * PER;
  if (u < RUNT) { const k = Math.floor(u / STEP); return {k, s: settle(b0 + k * STEP, .18), back: 0, trail: 1}; }
  if (u < RUNT + HOLD) return {k: K, s: 0, back: 0, trail: 1};
  const g = settle(b0 + RUNT + HOLD, BACK * .8);
  return {k: K, s: 0, back: g, trail: 1 - seg(b0 + RUNT + HOLD, .3)};
}
const POSTER_T = T0 + RUNT + .8;

/* ------------------------------------------------------------ one landscape */
const PY0 = 64, PH = 272, PW = 392, YL = [-0.7, 3.0];
function landscape(o, st) {
  const {x0, letter, sub, f, g, runs, t0} = o;
  panel(letter, x0 - 56, 34, {alpha: seg(t0, .2)});
  text(sub, x0 - 22, 34, {size: 17, color: C.body, alpha: seg(t0 + .03, .25)});
  const A = axes({x: x0, y: PY0, w: PW, h: PH, xlim: [-1.8, 1.8], ylim: YL,
                  xticks: [-1.5, -1, -0.5, 0, 0.5, 1, 1.5], yticks: [0, 1, 2, 3],
                  xlabel: 'w', ylabel: 'f(w)', ylabelGap: 38, progress: seg(t0, .35)});
  const pts = []; for (let i = 0; i <= 360; i++) { const th = -1.8 + 3.6 * i / 360; pts.push([A.X(th), A.Y(f(th))]); }
  A.inside(() => line(pts, {color: C.navy, width: 2.4, progress: seg(t0 + .08, .4)}));
  // the runs: iterates visited (dots, and the chords of each jump), the marker, its tangent
  for (const R of runs) {
    const it = R.p, col = R.col;
    const ia = seg(.45, .25);
    // the start
    dot(A.X(it[0]), A.Y(f(it[0])), 5.2, {color: col, fill: '#fff', width: 1.6, alpha: ia});
    const ls = lab(.5);
    math('w_0', A.X(it[0]) + R.lx, A.Y(f(it[0])) + R.ly + rise(ls), {size: 16, color: col, align: 'center', alpha: ls});
    if (t < T0) continue;
    const k = st.k, tr = st.trail;
    const chord = []; for (let j = 0; j <= Math.min(k, K); j++) chord.push([A.X(it[j]), A.Y(f(it[j]))]);
    if (chord.length > 1) A.inside(() => line(chord, {color: col, width: 1.1, alpha: .55 * tr}));
    for (let j = 1; j <= Math.min(k, K); j++) dot(A.X(it[j]), A.Y(f(it[j])), 2.6, {color: col, fill: col, width: .8, alpha: tr});
    // the marker: gliding from iterate k to k + 1 along the curve, or back to the start
    let th;
    if (st.back > 0) th = lerp(it[K], it[0], st.back);
    else th = k < K ? lerp(it[k], it[k + 1], st.s) : it[K];
    const X = A.X(th), Y = A.Y(f(th));
    // the tangent, the local slope gradient descent follows: 60 units long on screen
    const dx = A.X(1) - A.X(0), dy = A.Y(g(th)) - A.Y(0), L = Math.hypot(dx, dy), ux = dx / L * 30, uy = dy / L * 30;
    line([[X - ux, Y - uy], [X + ux, Y + uy]], {color: C.ink, width: 1.2, alpha: .75});
    dot(X, Y, 6.2, {color: '#fff', fill: col, width: 1.8});
  }
  return A;
}

/* a TikZ pin: the label above the point, a thin leader down to it */
function pin_(A, at, s, a) {
  if (a <= 0) return;
  const x = A.X(at[0]), y = A.Y(at[1]), top = A.Y(1.72);
  line([[x, top + 6 + rise(a)], [x, y - 12]], {color: C.guide, width: 1, alpha: a});
  text(s, x, top + rise(a), {size: 15, color: C.body, align: 'center', alpha: a});
}

function draw() {
  const st = clock();
  // (a) convex: one minimum, reached from both sides
  const A = landscape({x0: 76, letter: 'a', sub: 'convex', f: FA, g: GA, t0: 0,
                       runs: [{p: D.a.left, col: C.accent, lx: 17, ly: -8}, {p: D.a.right, col: C.blue, lx: -17, ly: -8}]}, st);
  pin_(A, D.a.min, 'global minimum', lab(.36));
  // (b) nonconvex: a local minimum on the left, the global one on the right
  const B = landscape({x0: 576, letter: 'b', sub: 'nonconvex', f: FB, g: GB, t0: .06,
                       runs: [{p: D.b.left, col: C.accent, lx: 19, ly: 6}, {p: D.b.right, col: C.blue, lx: -19, ly: -8}]}, st);
  const mb = lab(.42), gy = B.Y(D.b.glob[1]), ly = B.Y(D.b.loc[1]), xl = B.X(D.b.loc[0]);
  pin_(B, D.b.loc, 'local minimum', mb);
  pin_(B, D.b.glob, 'global minimum', lab(.46));
  // the level of the global minimum, and how far above it the local one stops
  B.inside(() => line([[xl - 22, gy], [B.X(D.b.glob[0]) - 10, gy]], {color: C.guide, width: 1, dash: [5, 4], alpha: mb}));
  if (mb > 0) {
    arrow(xl, gy, xl, ly + 9, {width: 1, head: 6, both: true, alpha: mb});
    math(D.b.gap.toFixed(2), xl + 7, (gy + ly) / 2 + 9, {size: 15, alpha: mb});
  }
  // the iteration counter
  const ca = seg(.5, .2), kk = t < T0 ? 0 : st.back > 0 ? 0 : st.k;
  math(`k = ${kk}`, 980, 34, {size: 16, align: 'right', alpha: ca});
  math(D.params, 20, H - 14, {size: 14, color: C.muted, alpha: seg(.45, .3)});
}
boot();
"""


def build():
    runs = {}
    for key, g, f in (("a", g_a, f_a), ("b", g_b, f_b)):
        runs[key] = {side: descend(g, t0, ETA[key]) for side, t0 in zip(("left", "right"), STARTS)}
    crit = critical_b()
    loc, hump, glob = crit[0], crit[1], crit[2]
    gap = f_b(loc) - f_b(glob)
    for key, f in (("a", f_a), ("b", f_b)):
        for side in ("left", "right"):
            p = runs[key][side]
            print(f"({key}) {side}: w_0 = {p[0]:+.2f} -> w_{K} = {p[-1]:+.5f}, f = {f(p[-1]):+.5f}")
    print(f"(b) minima: local {loc:+.6f} (f = {f_b(loc):+.6f}), global {glob:+.6f} (f = {f_b(glob):+.6f}), "
          f"barrier at {hump:+.6f}; gap {gap:.4f}")
    data = dict(
        k=K, tilt=TILT,
        a=dict(left=runs["a"]["left"], right=runs["a"]["right"], min=[0.2, f_a(0.2)]),
        b=dict(left=runs["b"]["left"], right=runs["b"]["right"], loc=[loc, f_b(loc)], glob=[glob, f_b(glob)],
               gap=gap),
        params=(r"\rm{gradient descent }w_{k+1} = w_k - \eta f" "′" r"(w_k)\rm{, 20 steps from }w_0 = \pm 1.6\rm{;   (a) }"
                r"f = 0.9(w - 0.2)^2 - 0.3\rm{, }\eta\ = 0.2\rm{;   (b) }f = (w^2 - 1)^2 - 0.3w\rm{, }\eta\ = 0.03"),
    )
    title = "Figure 3: Convex versus nonconvex optimization landscapes"
    aria = ("Two curves with gradient descent run on each from a start on the left and a start on the right. "
            "On the convex bowl both runs step down to the same, global minimum. On the tilted double well the "
            "run started on the left stops in the higher, local minimum, 0.60 above the global one that the run "
            "started on the right reaches.")
    common.build_html("sp-landscape", title, aria, 1000, 436, data, JS)
    png = common.still("sp-landscape")
    print("still:", png)
    res = dict(runs=runs, crit=crit, gap=gap)
    validate(res)
    return res


def validate(r):
    """Closed forms of the minima and of the descent's convergence against the
    iterates, and the page's own curves; writes sp_landscape.check.txt."""
    runs, crit = r["runs"], r["crit"]
    loc, hump, glob = crit
    roots = np.sort(np.roots([4, 0, -4, -TILT]).real)
    e_roots = np.abs(roots - crit).max()
    # (a) is quadratic: w_k - 0.2 = (w_0 - 0.2)(1 - eta f'')^k exactly
    q = 1 - ETA["a"] * 1.8
    e_a = max(np.abs(runs["a"][s] - 0.2 - (runs["a"][s][0] - 0.2) * q ** np.arange(K + 1)).max() for s in ("left", "right"))
    # (b): each run ends in its own basin; near a minimum the error shrinks by 1 - eta f''(w*)
    fpp = lambda w: 12 * w * w - 4
    lines = []
    for side, wstar in (("left", loc), ("right", glob)):
        pth = runs["b"][side]
        err = pth - wstar
        ratio = err[-1] / err[-2]
        lines.append((side, wstar, pth[-1], abs(err[-1]), ratio, 1 - ETA["b"] * fpp(wstar)))
    # the page's own objective functions against these
    ws = np.linspace(-1.8, 1.8, 9)
    lst = ", ".join(f"{w:.3f}" for w in ws)
    fa_pg, fb_pg = SM.check_page("sp-landscape", [f"[{lst}].map(FA)", f"[{lst}].map(FB)"])
    e_pg = max(np.abs(fa_pg - f_a(np.round(ws, 3))).max(), np.abs(fb_pg - f_b(np.round(ws, 3))).max())
    # nonconvexity of (b): f'' < 0 on |w| < 1/sqrt(3)
    L = []
    say = L.append
    say("Figure 3, convex versus nonconvex optimization landscapes: check of tools/numfig/sp_landscape.py")
    say("")
    say("MODEL")
    say("  (a) f(w) = 0.9 (w - 0.2)^2 - 0.3: convex, f'' = 1.8 everywhere; one minimum, w* = 0.2, f* = -0.3.")
    say(f"  (b) f(w) = (w^2 - 1)^2 - {TILT:g} w: a tilted double well; f'' = 12 w^2 - 4 < 0 on |w| < 1/sqrt(3),")
    say("      so it is not convex.")
    say(f"  Gradient descent w_(k+1) = w_k - eta f'(w_k), {K} steps from w_0 = {STARTS[0]:g} (left) and {STARTS[1]:g}")
    say(f"  (right); eta = {ETA['a']:g} in (a), {ETA['b']:g} in (b). Double precision, no line search.")
    say("")
    say("VALIDATION")
    say("  1. Critical points of (b), the roots of f' = 4 w^3 - 4 w - 0.3, in closed form")
    say("     (trigonometric solution of the cubic):")
    say(f"     local minimum w = {loc:.9f}, f = {f_b(loc):.9f}")
    say(f"     barrier       w = {hump:.9f}, f = {f_b(hump):.9f}")
    say(f"     global minimum w = {glob:.9f}, f = {f_b(glob):.9f}")
    say(f"     against numpy's polynomial roots: {e_roots:.1e}. The local minimum lies f = {r['gap']:.4f} above the")
    say("     global one (the 0.60 drawn in (b)).")
    say("  2. (a) is quadratic, so w_k - 0.2 = (w_0 - 0.2)(1 - eta f'')^k exactly, with 1 - eta f'' =")
    say(f"     {q:g}: both runs against it, largest difference {e_a:.1e}; both end at")
    say(f"     w = {runs['a']['left'][-1]:.5f} and {runs['a']['right'][-1]:.5f}, f = {f_a(runs['a']['left'][-1]):.6f} and {f_a(runs['a']['right'][-1]):.6f} (f* = -0.3).")
    say("  3. (b): each run ends in the basin it started in; near a minimum w* the error shrinks by")
    say("     1 - eta f''(w*) per step (linear convergence):")
    for side, wstar, wend, err, ratio, th in lines:
        say(f"     {side:5s}: w_{K} = {wend:.6f}, |w_{K} - w*| = {err:.1e}, last ratio {ratio:.5f} against {th:.5f}")
    say(f"     The left run stops at f = {f_b(runs['b']['left'][-1]):.5f}; the right run reaches f = {f_b(runs['b']['right'][-1]):.5f}.")
    say(f"  4. The page's own f(w) in (a) and (b) against these at 9 points: {e_pg:.1e}.")
    say("")
    say("DISPLAY")
    say("  One step every 0.22 s; between iterates the marker glides along the curve (a Motion")
    say("  spring, for the eye only). The segments are the chords of the jumps; the short line")
    say("  through each marker is the tangent, slope f'(w), that the next step follows.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_landscape.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
