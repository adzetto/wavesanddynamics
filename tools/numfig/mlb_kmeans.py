"""Figure 15: K-Means clustering. No labels are given; Lloyd's algorithm
finds three customer groups by itself.

Data: 150 synthetic customers in two standardized features, drawn from three
groups (55, 50, 45) whose labels the algorithm never sees. K = 3.

The motion is Lloyd's algorithm, iteration by iteration, exactly as it runs:
the three centers start at three customers picked at random (all three, by
chance, in the same group); each point joins its nearest center (the thin
lines are where two centers are equally near); each center moves to the mean
of its points; this repeats until no point changes group. The small plot
counts the sum of squared distances, which can only fall. The run ends at the
same partition as the best of 200 k-means++ starts (scikit-learn).

Run: python tools/numfig/mlb_kmeans.py [--look]
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

import mlb_common as mc

NAME = "kmeans"
DSEED, ISEED, KC = 3, 500, 3
GROUPS = [((-1.2, -0.6), 0.45, 55), ((0.95, -0.85), 0.40, 50), ((0.15, 1.15), 0.50, 45)]

r = np.random.default_rng(DSEED)
X = np.vstack([r.normal(m, s, (n, 2)) for m, s, n in GROUPS])
truth = np.repeat(np.arange(3), [n for _, _, n in GROUPS])
X = (X - X.mean(0)) / X.std(0)
init_idx = np.random.default_rng(ISEED).choice(len(X), KC, replace=False)


def sse(X, lab, C):
    return float(((X - C[lab]) ** 2).sum())


C = X[init_idx].copy()
centers, labels, J_assign, J_update = [C.copy()], [], [], []
for it in range(100):
    lab = ((X[:, None] - C[None]) ** 2).sum(2).argmin(1)
    if labels and np.array_equal(lab, labels[-1]):
        break
    labels.append(lab)
    J_assign.append(sse(X, lab, C))
    C = np.array([X[lab == k].mean(0) for k in range(KC)])
    centers.append(C.copy())
    J_update.append(sse(X, lab, C))
NIT = len(labels)

# order the clusters by their final mean (lower left, lower right, top) so their colours read the same way
final = centers[-1]
order = np.argsort(np.arctan2(final[:, 1] - 0.0, final[:, 0] - 0.0))
rank = np.empty(KC, int)
rank[order] = np.arange(KC)
centers = [c[order] for c in centers]
labels = [rank[l] for l in labels]

sk = KMeans(KC, init=X[init_idx], n_init=1, algorithm="lloyd", tol=0.0, max_iter=300).fit(X)
best = KMeans(KC, n_init=200, random_state=0).fit(X)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-kmeans: Figure 15, K-Means finding three groups without labels")
say("")
say("MODEL")
say(f"  150 synthetic customers, two features standardized to mean 0, deviation 1 (seed {DSEED});")
say(f"  drawn from three groups {[(g[0], g[1], g[2]) for g in GROUPS]} (mean, sd, size) whose labels")
say("  the algorithm never sees. K = 3. Lloyd's algorithm: assign each point to the nearest")
say("  center (Euclidean), move each center to the mean of its points, repeat until no point")
say(f"  changes group. Start: customers {init_idx.tolist()} (seed {ISEED}), all three in true group"
    f" {sorted(set(truth[init_idx].tolist()))}.")
say("")
say("RUN")
say("  iter  sum of squares after assigning   after moving   centers")
for i in range(NIT):
    cs = "  ".join(f"({c[0]:+.3f},{c[1]:+.3f})" for c in centers[i + 1])
    say(f"  {i+1:3d}   {J_assign[i]:12.4f}                {J_update[i]:10.4f}   {cs}")
say(f"  iteration {NIT + 1}: no point changes group, the algorithm stops")
say("")
say("CHECK 1: the same start in scikit-learn (KMeans, algorithm='lloyd', tol 0)")
skc = sk.cluster_centers_[np.argsort(np.arctan2(sk.cluster_centers_[:, 1], sk.cluster_centers_[:, 0]))]
say(f"  max |center difference| = {np.max(np.abs(skc - centers[-1])):.1e}; inertia {sk.inertia_:.6f} vs {J_update[-1]:.6f};"
    f" iterations {sk.n_iter_} vs {NIT}")
say("")
say("CHECK 2: Lloyd's algorithm never raises the sum of squares")
seq_ = [v for pair in zip(J_assign, J_update) for v in pair]
say(f"  sequence non-increasing: {all(b <= a + 1e-12 for a, b in zip(seq_, seq_[1:]))}")
say("")
say("CHECK 3: the result against the best of 200 k-means++ starts, and against the hidden groups")
say(f"  best inertia {best.inertia_:.6f}; this run {J_update[-1]:.6f} (difference {abs(best.inertia_ - J_update[-1]):.1e})")
say(f"  adjusted Rand index against the groups the data came from: {adjusted_rand_score(truth, labels[-1]):.4f}")
for k in range(KC):
    m = labels[-1] == k
    say(f"  group {k}: {int(m.sum())} points, center ({centers[-1][k][0]:+.4f}, {centers[-1][k][1]:+.4f}),"
        f" mean of its points ({X[m].mean(0)[0]:+.4f}, {X[m].mean(0)[1]:+.4f})")
mc.check(NAME, L)

DATA = {"x": X, "c": [c for c in centers], "lab": [l for l in labels], "ja": J_assign, "ju": J_update, "nit": NIT}

JS = r"""
const D = DATA, NP = D.x.length, NIT = D.nit, XL = 2.7;
const AX = { x: 74, y: 24, w: 450, h: 450 };
const SX = v => AX.x + (v + XL) / (2 * XL) * AX.w, SY = v => AX.y + AX.h - (v + XL) / (2 * XL) * AX.h;

/* the clock: iteration i (1..NIT) assigns from its start for AS seconds, then the
   centers move for MV seconds; one more assignment finds nothing to change */
const T0 = .6, AS = .45, MV = .7, IT = AS + MV, T_END = T0 + NIT * IT + AS;
const HOLD = 4.5, RESET = 1.0, PER = T_END - T0 + HOLD + RESET;
const POSTER_T = T_END + 1.5;
function clock() {                               // local time within the loop, from T0
  if (t < T0) return -1;
  return (t - T0) % PER;
}
function state() {
  const c = clock();
  if (c < 0) return { it: 0, a: 0, m: 0, reset: 0 };
  if (c >= T_END - T0 + HOLD) return { it: NIT + 1, a: 1, m: 1, reset: easeInOut((c - (T_END - T0 + HOLD)) / RESET) };
  const i = Math.floor(c / IT) + 1, r = c - (i - 1) * IT;
  if (i > NIT) return { it: NIT + 1, a: clamp(r / AS), m: 1, reset: 0 };
  return { it: i, a: clamp(r / .3), m: r < AS ? 0 : springAt(r - AS), reset: 0 };
}
/* Motion's spring at a local time s (settle() reads the global clock) */
const MOVE = MotionSpring({ keyframes: [0, 1], visualDuration: MV * .8, bounce: 0 });
const springAt = s => s <= 0 ? 0 : MOVE.next(s * 1000).value;

/* centers at this moment: moving from iteration it-1's positions to it's */
const CEN = [[0, 0], [0, 0], [0, 0]];
function centersNow(st) {
  for (let k = 0; k < 3; k++) {
    let x, y;
    if (st.it === 0) { x = D.c[0][k][0]; y = D.c[0][k][1]; }
    else if (st.it > NIT) { x = D.c[NIT][k][0]; y = D.c[NIT][k][1]; }
    else { const a = D.c[st.it - 1][k], b = D.c[st.it][k]; x = lerp(a[0], b[0], st.m); y = lerp(a[1], b[1], st.m); }
    if (st.reset > 0) { x = lerp(x, D.c[0][k][0], st.reset); y = lerp(y, D.c[0][k][1], st.reset); }
    CEN[k][0] = x; CEN[k][1] = y;
  }
  return CEN;
}
/* the edges of the three centers' Voronoi cells: rays from the point equally
   near all three, along each pair's bisector, away from the third center */
function voronoi(P, alpha) {
  if (alpha <= 0) return;
  const [a, b, c] = P;
  const d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]));
  if (Math.abs(d) < 1e-9) return;
  const s = q => q[0] * q[0] + q[1] * q[1];
  const ox = (s(a) * (b[1] - c[1]) + s(b) * (c[1] - a[1]) + s(c) * (a[1] - b[1])) / d;
  const oy = (s(a) * (c[0] - b[0]) + s(b) * (a[0] - c[0]) + s(c) * (b[0] - a[0])) / d;
  for (const [i, j, k] of [[0, 1, 2], [1, 2, 0], [2, 0, 1]]) {
    let ux = -(P[j][1] - P[i][1]), uy = P[j][0] - P[i][0];
    if (ux * (P[i][0] - P[k][0]) + uy * (P[i][1] - P[k][1]) < 0) { ux = -ux; uy = -uy; }
    const n = Math.hypot(ux, uy);
    line([[SX(ox), SY(oy)], [SX(ox + ux / n * 12), SY(oy + uy / n * 12)]], { color: C.guide, width: 1.1, dash: [5, 4], alpha });
  }
}

/* the three groups: a fill and a shape each, so no group is told by colour alone and
   none is crimson (README, shared conventions); a center and its path take its group's colour.
   The three marks weigh alike, as Figure 2(c) sizes them: a square of half side 3.4 and a
   triangle of r 4.8 (mark()'s triangle covers 1.85 r^2) come close to the circle of r 3.9 */
const GRP = [[C.navy, 'circle'], [C.blue, 'square'], [C.sky, 'triangle']];
const MR = { circle: 3.9, square: 3.4, triangle: 4.8 };
function draw() {
  const st = state(), CN = centersNow(st);
  const A = axes({ ...AX, xlim: [-XL, XL], ylim: [-XL, XL], xticks: [-2, -1, 0, 1, 2], yticks: [-2, -1, 0, 1, 2],
    xlabel: 'x_1', ylabel: 'x_2', ylabelGap: 36, tickSize: 16, progress: seg(0, .35) });
  // the cells' edges, from the centers the points are being assigned to
  A.inside(() => voronoi(CN, (st.it > 0 ? 1 : seg(.5, .3)) * (1 - st.reset) * lab(.45)));
  // trails: where each center has been
  A.inside(() => {
    const upto = st.it === 0 ? 0 : Math.min(st.it, NIT);
    for (let k = 0; k < 3; k++) {
      if (upto < 1) break;
      const pts = [[SX(D.c[0][k][0]), SY(D.c[0][k][1])]];
      for (let i = 1; i < upto; i++) pts.push([SX(D.c[i][k][0]), SY(D.c[i][k][1])]);
      pts.push([SX(CN[k][0]), SY(CN[k][1])]);
      line(pts, { color: GRP[k][0], width: 1.4, dash: [4, 3], alpha: .8 * (1 - st.reset) });
      for (let i = 0; i < upto; i++) dot(SX(D.c[i][k][0]), SY(D.c[i][k][1]), 2.4, { color: GRP[k][0], fill: '#fff', width: 1.2, alpha: 1 - st.reset });
    }
  });
  // the customers: no colour until the first assignment, then their center's colour and shape
  // (the shape turns halfway through the change of colour)
  for (let i = 0; i < NP; i++) {
    const p = settle(.05 + .002 * i, .24); if (p <= 0) continue;
    let fill = '#FFFFFF', edge = C.guide, kind = 'circle';
    if (st.it > 0) {
      const now = D.lab[Math.min(st.it, NIT) - 1][i];
      const was = st.it === 1 ? -1 : D.lab[Math.min(st.it - 1, NIT) - 1][i];
      const sNow = GRP[now];
      kind = was !== now && st.it <= NIT && st.a < .5 ? (was < 0 ? 'circle' : GRP[was][1]) : sNow[1];
      if (was === now || st.it > NIT) { fill = sNow[0]; edge = '#FFFFFF'; }
      else {
        const f0 = was < 0 ? '#FFFFFF' : GRP[was][0], e0 = was < 0 ? C.guide : '#FFFFFF';
        fill = mixHex(f0, sNow[0], st.a); edge = mixHex(e0, '#FFFFFF', st.a);
      }
      if (st.reset > 0) { fill = mixHex(sNow[0], '#FFFFFF', st.reset); edge = mixHex('#FFFFFF', C.guide, st.reset); if (st.reset > .5) kind = 'circle'; }
    }
    mark(kind, SX(D.x[i][0]), SY(D.x[i][1]), MR[kind] * (.6 + .4 * p), { fill, stroke: edge, width: 1, alpha: p });
  }
  // the centers
  for (let k = 0; k < 3; k++) {
    const a = settle(.3 + .05 * k, .28);
    cross(SX(CN[k][0]), SY(CN[k][1]) + rise(a), 8, { color: C.ink, width: 3.2, alpha: a });
  }

  /* the side: what the algorithm is doing, and the sum of squares falling */
  const TX = 598, la = lab(.15);
  const lw = text('Lloyd’s algorithm,', TX, 62 + rise(la), { size: 17, color: C.body, alpha: la });
  math('K = 3', TX + lw + 7, 62 + rise(la), { size: 17, alpha: la });
  line([[TX, 76], [TX + 360, 76]], { color: C.rule, width: 1, alpha: la });
  const itShow = st.it === 0 ? 1 : Math.min(st.it, NIT + 1);
  let words = 'centers start at random points';
  if (st.it > 0 && st.it <= NIT) words = st.m > 0 ? 'centers move to the mean' : 'points join the nearest center';
  if (st.it > NIT) words = 'no point changes group';
  const done = st.it > NIT && st.reset === 0;
  const wa = lab(.3), was = clamp(1 - 2 * st.reset), now = clamp(2 * st.reset - 1);
  if (st.reset > 0) {          // the converged words fade out, then the first iteration's fade in
    text('converged', TX, 108, { size: 17, bold: true, color: C.accent, alpha: wa * was });
    text('no point changes group', TX, 134, { size: 16, color: C.body, alpha: wa * was });
    text('iteration 1', TX, 108, { size: 17, alpha: wa * now });
    text('centers start at random points', TX, 134, { size: 16, color: C.body, alpha: wa * now });
  } else {
    text(done ? 'converged' : `iteration ${itShow}`, TX, 108 + rise(wa), { size: 17, bold: done, color: done ? C.accent : C.ink, alpha: wa });
    text(words, TX, 134 + rise(wa), { size: 16, color: C.body, alpha: wa });
  }
  // the sum of squared distances after each move
  const G = axes({ x: TX + 46, y: 190, w: 300, h: 150, xlim: [.5, NIT + .5], ylim: [0, 200],
    xticks: Array.from({ length: NIT }, (_, i) => i + 1), yticks: [0, 50, 100, 150, 200],
    xlabel: '\\rm{iteration}', ylabel: '', tickSize: 16, progress: seg(.1, .35), grid: true });
  const shown = st.it === 0 ? 0 : st.it > NIT ? NIT : st.it - 1 + (st.m > .5 ? 1 : 0);
  const sw = text('sum of squared distances', TX, 172 + rise(la), { size: 16, color: C.body, alpha: la });
  if (shown > 0) math(D.ju[shown - 1].toFixed(1), TX + sw + 10, 172 + rise(la), { size: 16, color: C.blue, alpha: la * (1 - st.reset) });
  const gp = [];
  for (let i = 0; i < shown; i++) gp.push([G.X(i + 1), G.Y(D.ju[i])]);
  const ga = 1 - st.reset;
  line(gp, { color: C.blue, width: 2, alpha: ga });
  for (let i = 0; i < shown; i++) dot(G.X(i + 1), G.Y(D.ju[i]), 3.4, { color: '#fff', fill: C.blue, width: 1.2, alpha: ga });
  // legend
  legend(TX, 408, 206, [
    [(x, y, a) => mark('circle', x, y, 3.9, { fill: '#fff', stroke: C.guide, width: 1, alpha: a }), 'customer, no label'],
    [(x, y, a) => cross(x, y, 6, { color: C.ink, width: 2.6, alpha: a }), 'cluster center'],
    [(x, y, a) => line([[x - 12, y], [x + 12, y]], { color: C.ink, width: 1.4, dash: [4, 3], alpha: a }), 'path of a center'],
  ], { alpha: lab(.45) });
  text('150 synthetic customers, standardized; Euclidean distance', 18, H - 12,
       { size: 15, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 15: K-Means clustering: no labels were given"
ARIA = (f"150 customers as unlabeled points in two features. Three cluster centers start at random points, "
        f"all in the same group, and Lloyd's algorithm runs: each point takes the color of its nearest center, "
        f"each center moves to the mean of its points, and after {NIT} iterations no point changes group. The "
        "three centers have found the three dense groups. A small plot shows the sum of squared distances "
        "falling at every iteration.")

if __name__ == "__main__":
    print(f"{NIT} iterations; inertia {J_update[-1]:.4f} (best {best.inertia_:.4f})")
    mc.publish(NAME, TITLE, ARIA, 1000, 572, DATA, JS, look=(0.3, 0.7, 1.0, 1.5, 2.2, 3.4, 5.0, 7.2, 9.0, 12.5, 13.1))
