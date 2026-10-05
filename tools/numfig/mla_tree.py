"""Figure 10 of the machine learning guide (stem image7): a decision tree
for loan approval, grown on data.

Data: 200 simulated loan applications (seed fixed): income (k$ a year,
lognormal about 52), credit score (normal 690, sd 45, 500..850), debt as a
share of income (uniform 8..48 %). The recorded decision follows a lender's
rule (income up to 50k: approve with a credit score above 720; above 50k:
approve with debt under 38 % of income) with 5 % of the decisions flipped,
as real records are never clean.

Model: scikit-learn's DecisionTreeClassifier (Gini, depth 2) grown on those
200 records. It finds the rule's questions itself; the thresholds are the
tree's own (midpoints between recorded values), shown in the data's
precision. Every count in the figure is the tree's.

The page first pours the 200 records through the tree, each along its own
path (the leaf counts rise as they land), then walks four new applicants
down it, one at a time, writing out each path: every path is auditable.

Run: python tools/numfig/mla_tree.py [--look]
"""
import sys

import numpy as np
from sklearn.tree import DecisionTreeClassifier

import common
from mla_shared import LIB, loan_data, on_grid_above, on_grid_below, report

NAME, STEM = "mla-tree", "mla_tree"
SEED, N = 11, 200

inc, cs, dti, y, flip = loan_data(SEED, N)            # y: 1 approved, 0 declined
X = np.c_[inc, cs, dti]
FEAT = ["income", "credit score", "debt share"]

tree = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X, y)
T = tree.tree_
assert list(T.feature[[0, 1, 4]]) == [0, 1, 2], "the tree's questions changed"
t_inc, t_cs, t_dti = T.threshold[0], T.threshold[1], T.threshold[4]
# the thresholds on the data's own grid (income and debt to 0.1, scores whole):
# for values on that grid, income > t_inc <=> income >= inc_hi, and so on
inc_hi, cs_hi, dti_lo = on_grid_above(t_inc, 0.1), on_grid_above(t_cs, 1), on_grid_below(t_dti, 0.1)
leaf = tree.apply(X)
ids = {"ll": 2, "lr": 3, "rl": 5, "rr": 6}             # sklearn node ids: left, right of each split
counts = {k: [int(((leaf == v) & (y == 0)).sum()), int(((leaf == v) & (y == 1)).sum())] for k, v in ids.items()}
path = np.select([leaf == 2, leaf == 3, leaf == 5, leaf == 6], [0, 1, 2, 3])   # ll, lr, rl, rr
# the leaves on the page: no to the left, yes to the right. For the debt
# question "yes" is debt <= threshold, sklearn's left child.
PAGE_LEAF = {0: 0, 1: 1, 2: 3, 3: 2}                  # sklearn order -> page order
page_path = np.array([PAGE_LEAF[v] for v in path])

APPLICANTS = [(62.0, 640, 24.0), (41.0, 745, 30.0), (73.0, 705, 44.0), (38.0, 668, 21.0)]


def route(a):
    i, c, d = a
    if i >= inc_hi:
        return 3 if d <= dti_lo else 2
    return 1 if c >= cs_hi else 0


# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-tree: Figure 10, decision tree for loan approval")
say("")
say("DATA")
say(f"  {N} simulated applications, seed {SEED}: income ~ lognormal(ln 52, 0.38) k$, credit ~ N(690, 45)"
    f" in [500, 850], debt share ~ U(8, 48) %")
say("  recorded decision: income <= 50 -> approve iff credit > 720; income > 50 -> approve iff debt < 38 %;"
    f" {int(flip.sum())} of {N} flipped (5 %)")
say(f"  approved {int(y.sum())}, declined {int(N - y.sum())}")
say("")
say("TREE (Gini, depth 2)")
say(f"  root: income <= {t_inc:.4f}  (page: income >= ${inc_hi:.1f}k? yes to the right)")
say(f"  left: credit <= {t_cs:.4f}  (page: credit score >= {cs_hi:.0f}?)")
say(f"  right: debt <= {t_dti:.4f}  (page: debt <= {dti_lo:.1f}% of income?)")
for k in ("ll", "lr", "rl", "rr"):
    say(f"  leaf {k}: declined {counts[k][0]}, approved {counts[k][1]}")
say(f"  training accuracy {tree.score(X, y):.3f}")
say("")


def gini(v):
    if len(v) == 0:
        return 0.0
    p = v.mean()
    return 2 * p * (1 - p)


def best_split(Xs, ys):
    best = (np.inf, None, None)
    for f in range(Xs.shape[1]):
        u = np.unique(Xs[:, f])
        for c in (u[:-1] + u[1:]) / 2:
            l, r = ys[Xs[:, f] <= c], ys[Xs[:, f] > c]
            g = (len(l) * gini(l) + len(r) * gini(r)) / len(ys)
            if g < best[0] - 1e-12:
                best = (g, f, c)
    return best


say("CHECK 1: every split is the best Gini split of its node (brute force over all features, all cuts)")
g0, f0, c0 = best_split(X, y)
say(f"  root: brute force {FEAT[f0]} <= {c0:.4f}, weighted Gini {g0:.6f}; tree {FEAT[T.feature[0]]} <= {t_inc:.4f}"
    f" (parent Gini {gini(y):.6f})")
m = X[:, 0] <= t_inc
g1, f1, c1 = best_split(X[m], y[m])
say(f"  left:  brute force {FEAT[f1]} <= {c1:.4f}, Gini {g1:.6f}; tree {FEAT[T.feature[1]]} <= {t_cs:.4f}")
g2, f2, c2 = best_split(X[~m], y[~m])
say(f"  right: brute force {FEAT[f2]} <= {c2:.4f}, Gini {g2:.6f}; tree {FEAT[T.feature[4]]} <= {t_dti:.4f}")
say("CHECK 2: the tree's questions against the rule the records came from")
say(f"  income cut {t_inc:.2f} (rule 50), credit cut {t_cs:.1f} (rule 720), debt cut {t_dti:.2f} % (rule 38)")
say(f"  records the tree gets wrong: {int((tree.predict(X) != y).sum())}; records flipped from the rule:"
    f" {int(flip.sum())}; wrong and not flipped: {int(((tree.predict(X) != y) & ~flip).sum())}")
say("CHECK 3: the page's four new applicants, routed by the page's questions and by sklearn")
for a in APPLICANTS:
    pg = route(a)
    sk = PAGE_LEAF[int(np.select([tree.apply([a])[0] == v for v in (2, 3, 5, 6)], [0, 1, 2, 3]))]
    say(f"  income {a[0]:g}k, credit {a[1]}, debt {a[2]:g} %: page leaf {pg}, sklearn leaf {sk},"
        f" {'approve' if pg in (1, 3) else 'decline'}")
say("PAGE: an applicant every 4.8 s (3.1 s before 5 Oct 2026); each path rests 2.6 s, written out.")
report(STEM, L)

order = np.random.default_rng(99).permutation(N)
DATA = {
    "path": page_path[order].tolist(), "y": y[order].tolist(),
    "q": {"inc": float(inc_hi), "cs": float(cs_hi), "dti": float(dti_lo)},
    "n": {"root": [int(N - y.sum()), int(y.sum())],
          "l": [int(((X[:, 0] <= t_inc) & (y == 0)).sum()), int(((X[:, 0] <= t_inc) & (y == 1)).sum())],
          "r": [int(((X[:, 0] > t_inc) & (y == 0)).sum()), int(((X[:, 0] > t_inc) & (y == 1)).sum())],
          "leaf": [counts["ll"], counts["lr"], counts["rr"], counts["rl"]]},
    "app": [list(a) for a in APPLICANTS], "route": [route(a) for a in APPLICANTS],
}

JS = LIB + r"""
const D = DATA, N = D.path.length;
const NODE = {root: [500, 76], l: [262, 222], r: [738, 222]};
const LEAF = [[132, 376], [392, 376], [608, 376], [868, 376]];
const IW = 236, IH = 64, LW = 186, LH = 64;
const PARENT = [NODE.l, NODE.l, NODE.r, NODE.r];
const QS = [
  ['income ≥ $' + D.q.inc.toFixed(1) + 'k?', D.n.root],
  ['credit score ≥ ' + D.q.cs.toFixed(0) + '?', D.n.l],
  ['debt ≤ ' + D.q.dti.toFixed(1) + '% of income?', D.n.r],
];
const POUR0 = .28, POUR = .5, HOP = .28;     // records start, spread, time per level
const AT0 = 1.55, AP = 4.8;                  // the applicants' walk: each path rests 2.6 s, written out
const POSTER_T = AT0 + 2.1;

/* where record k is at time t: from the root down to its leaf, and when it lands */
const emit = k => POUR0 + POUR * k / (N - 1);
function recordPos(k) {
  const u = t - emit(k); if (u <= 0) return null;
  const lf = D.path[k], P = PARENT[lf], R = NODE.root, Lf = LEAF[lf];
  const a = [R[0], R[1] + IH / 2], b = [P[0], P[1] - IH / 2], c = [P[0], P[1] + IH / 2], d = [Lf[0], Lf[1] - LH / 2];
  if (u < HOP) { const s = easeInOut(u / HOP); return [lerp(a[0], b[0], s), lerp(a[1], b[1], s), 1]; }
  if (u < 2 * HOP) { const s = easeInOut((u - HOP) / HOP); return [lerp(c[0], d[0], s), lerp(c[1], d[1], s), 1]; }
  return null;
}
function landed(lf) {                          // records in leaf lf that have arrived
  let a = 0, ap = 0;
  for (let k = 0; k < N; k++) if (D.path[k] === lf && t - emit(k) >= 2 * HOP) { a++; if (D.y[k]) ap++; }
  return [a - ap, ap];
}
function mix(cx, y, w, cnt, alpha) {            // a class-mix bar: approved share in navy
  const tot = cnt[0] + cnt[1]; if (!tot || alpha <= 0) return;
  box(cx - w / 2, y, w, 5, {fill: '#fff', stroke: C.ink, width: .8, alpha});
  box(cx - w / 2, y, w * cnt[1] / tot, 5, {fill: C.navy, alpha});
}
function edge(p, q, lab, side, a, hot) {
  const x0 = p[0], y0 = p[1] + IH / 2, x1 = q[0], y1 = q[1] - (q === NODE.l || q === NODE.r ? IH : LH) / 2;
  line([[x0, y0], [x1, y1]], {color: hot > 0 ? C.accent : C.ink, width: hot > 0 ? 2.2 : 1.4, progress: a});
  if (hot > 0 && hot < 1) line([[x0, y0], [lerp(x0, x1, hot), lerp(y0, y1, hot)]], {color: C.accent, width: 2.2});
  // the answer sits beside the edge's middle, on its outer (upper) side
  const L_ = Math.hypot(x1 - x0, y1 - y0), dx = (x1 - x0) / L_, dy = (y1 - y0) / L_;
  let nx = dy, ny = -dx; if (ny > 0) { nx = -nx; ny = -ny; }
  const mx = (x0 + x1) / 2 + nx * 14, my = (y0 + y1) / 2 + ny * 14 + 5;
  text(lab, mx, my, {size: 16, italic: true, color: hot > 0 ? C.accent : C.body, align: 'center', alpha: clamp(a * 2 - 1)});
}

function draw() {
  /* the applicant being walked down, if any */
  let who = -1, u = 0;
  if (t >= AT0) { const tau = (t - AT0) % (4 * AP); who = Math.floor(tau / AP); u = tau - who * AP; }
  const lf = who >= 0 ? D.route[who] : -1, side1 = lf >= 2 ? 1 : 0;
  const hop1 = who >= 0 ? clamp((u - .35) / .55) : 0, hop2 = who >= 0 ? clamp((u - 1.05) / .55) : 0;
  const fade = who >= 0 ? clamp(u / .25) * (1 - clamp((u - (AP - .35)) / .3)) : 0;
  const hot = (tgt, h) => (who >= 0 && fade > 0 ? h : 0);

  /* edges, with the answers on them */
  const ea = seg(.12, .3), eb = seg(.22, .3);
  edge(NODE.root, NODE.l, 'no', -1, ea, hot(0, side1 === 0 ? hop1 : 0) * fade);
  edge(NODE.root, NODE.r, 'yes', 1, ea, hot(0, side1 === 1 ? hop1 : 0) * fade);
  LEAF.forEach((q, i) => edge(PARENT[i], q, i % 2 ? 'yes' : 'no', i % 2 ? 1 : -1, eb, lf === i ? hop2 * fade : 0));

  /* the records pouring through, behind the boxes */
  for (let k = 0; k < N; k++) {
    const p = recordPos(k); if (!p) continue;
    mark(p[0], p[1], D.y[k] ? 1 : 0, 1, 2.8);
  }

  /* questions */
  const nodes = [NODE.root, NODE.l, NODE.r];
  nodes.forEach((c, i) => {
    const a = arrive(.02 + .08 * i);
    node(c[0], c[1] - 4, IW, IH, [QS[i][0], {s: (QS[i][1][0] + QS[i][1][1]) + ' records, ' +
      Math.round(100 * QS[i][1][1] / (QS[i][1][0] + QS[i][1][1])) + '% approved', size: 16, color: C.body}],
      {alpha: a, gap: 21, stroke: C.ink});
    mix(c[0], c[1] + IH / 2 - 12, IW - 60, QS[i][1], a);
  });
  /* leaves: the prediction, and the records that landed there */
  LEAF.forEach((c, i) => {
    const a = arrive(.18 + .05 * i), cnt = landed(i), full = D.n.leaf[i];
    const approve = full[1] > full[0], tot = cnt[0] + cnt[1];
    const on = lf === i ? clamp((u - 1.55) / .2) * fade : 0;
    node(c[0], c[1] - 4, LW, LH, [{s: approve ? 'approve' : 'decline', bold: true, size: 17,
      color: on > .5 ? C.accent : C.ink},
      {s: tot ? (approve ? cnt[1] : cnt[0]) + ' of ' + tot + (approve ? ' approved' : ' declined') : ' ', size: 16, color: C.body}],
      {alpha: a, fill: C.steel, stroke: on > 0 ? C.accent : C.ink, width: on > 0 ? 2 : 1.3, gap: 21});
    mix(c[0], c[1] + LH / 2 - 12, LW - 60, cnt, a * clamp(tot));
  });

  /* the applicant: a token that walks down, and the path written out */
  if (who >= 0 && fade > 0) {
    const [ai, ac, ad] = D.app[who], P = side1 ? NODE.r : NODE.l, Lf = LEAF[lf], R = NODE.root;
    let px, py;
    if (u < 1.05) { const s = sp(u - .35, .45); px = lerp(R[0], P[0], s); py = lerp(R[1] + IH / 2, P[1] - IH / 2, s); }
    else { const s = sp(u - 1.05, .45); px = lerp(P[0], Lf[0], s); py = lerp(P[1] + IH / 2, Lf[1] - LH / 2, s); }
    dot(px, py, 7, {color: '#fff', fill: C.accent, width: 1.8, alpha: fade});
    const yy = 466, x0 = 30;
    text('applicant', x0, yy, {size: 16, bold: true, alpha: fade});
    text('income $' + ai.toFixed(0) + 'k,  credit score ' + ac + ',  debt ' + ad.toFixed(0) + '% of income',
      x0 + 92, yy, {size: 16, alpha: fade});
    const q1 = side1 ? 'yes' : 'no';
    const q2 = side1 ? (lf === 3 ? 'yes' : 'no') : (lf === 1 ? 'yes' : 'no');
    const s1 = 'income ≥ $' + D.q.inc.toFixed(1) + 'k? ' + q1;
    const s2 = (side1 ? 'debt ≤ ' + D.q.dti.toFixed(1) + '%? ' : 'credit score ≥ ' + D.q.cs.toFixed(0) + '? ') + q2;
    const s3 = (lf === 1 || lf === 3) ? 'approve' : 'decline';
    text('path', x0, yy + 26, {size: 16, bold: true, alpha: fade});
    let xx = x0 + 92;
    xx += text(s1, xx, yy + 26, {size: 16, alpha: fade * clamp((u - .6) / .2)});
    const a2 = fade * clamp((u - 1.3) / .2);
    xx += text('  →  ' + s2, xx, yy + 26, {size: 16, alpha: a2});
    text('  →  ' + s3, xx, yy + 26, {size: 16, bold: true, color: C.accent, alpha: fade * clamp((u - 1.6) / .2)});
  }
  text('200 simulated applications; Gini, depth 2; 5% of records flipped', 18, H - 14,
       {size: 15, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 10: Decision tree for loan approval"
ARIA = ('A decision tree grown on 200 simulated loan applications asks whether income is at least 50 thousand '
        'dollars, then about the credit score or about debt as a share of income, and ends in four leaves that '
        'predict approve or decline, each with the records that reached it. Applicants walk down the tree one '
        'at a time and their path is written out below.')

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 540, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.6, 0.9, 1.3, 2.4, 3.6]))
