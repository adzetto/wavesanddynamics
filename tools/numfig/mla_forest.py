"""Figure 11 of the machine learning guide (stem image8): a random forest
votes.

Data: the 200 simulated loan applications of Figure 10 (mla_shared.
loan_data). Model: scikit-learn's RandomForestClassifier with 5 trees of
depth 2 (so they can be drawn), each grown on its own bootstrap sample of the
200 records and trying 2 of the 3 features at every split (random_state
fixed). The randomness shows: the five trees ask different questions,
three of them start from a different feature.

Each tree votes for its leaf's majority class and the majority of the five
votes wins (the hard vote the caption describes; scikit-learn itself
averages the trees' class shares, and the check file compares the two).
The page routes each applicant through all five trees with the trees' own
questions, draws the votes, counts them and gives the forest's answer.

Run: python tools/numfig/mla_forest.py [--look]
"""
import sys

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

import common
from mla_shared import LIB, loan_data, on_grid_above, on_grid_below, report

NAME, STEM = "mla-forest", "mla_forest"
RS, NT = 31, 5
FEAT = ["income", "credit score", "debt"]
STEP = [0.1, 1, 0.1]

inc, cs, dti, y, flip = loan_data(11, 200)
X = np.c_[inc, cs, dti]
rf = RandomForestClassifier(n_estimators=NT, max_depth=2, max_features=2, random_state=RS).fit(X, y)
Xt_ = loan_data(12345, 5000)
Xt, yt = np.c_[Xt_[0], Xt_[1], Xt_[2]], Xt_[3]


def question(T, i):
    """The page's question at node i: 'yes' goes right on the page. Income
    and credit ask 'at least'; debt asks 'at most', whose yes is sklearn's
    left child."""
    f, t = int(T.feature[i]), float(T.threshold[i])
    if f == 2:
        return {"f": f, "op": "le", "v": on_grid_below(t, STEP[f]),
                "no": int(T.children_right[i]), "yes": int(T.children_left[i])}
    return {"f": f, "op": "ge", "v": on_grid_above(t, STEP[f]),
            "no": int(T.children_left[i]), "yes": int(T.children_right[i])}


trees = []
for e in rf.estimators_:
    T = e.tree_
    assert T.node_count == 7
    root = question(T, 0)
    kids = []
    for side in ("no", "yes"):
        c = root[side]
        q = question(T, c)
        leaves = []
        for s2 in ("no", "yes"):
            lf = q[s2]
            v = T.value[lf][0]
            leaves.append(int(np.argmax(v)))                # 1 approve, 0 decline
        q["leaf"] = leaves
        kids.append(q)
    trees.append({"root": root, "kids": kids})


def vote(tr, a):
    def yes(q):
        x = a[q["f"]]
        return x >= q["v"] - 1e-9 if q["op"] == "ge" else x <= q["v"] + 1e-9
    k = tr["kids"][1 if yes(tr["root"]) else 0]
    return k["leaf"][1 if yes(k) else 0]


APPS = [(38.0, 725, 24.0), (42.0, 725, 40.0), (52.0, 735, 40.0)]
votes = [[vote(tr, a) for tr in trees] for a in APPS]

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mla-forest: Figure 11, random forest voting")
say("")
say("DATA: the 200 simulated applications of Figure 10 (seed 11)")
say(f"MODEL: RandomForestClassifier(n_estimators={NT}, max_depth=2, max_features=2, bootstrap, random_state={RS})")
for k, tr in enumerate(trees):
    def qs(q):
        return f"{FEAT[q['f']]} {'>=' if q['op'] == 'ge' else '<='} {q['v']:g}"
    say(f"  tree {k+1}: {qs(tr['root'])}? no: {qs(tr['kids'][0])}? (leaves {tr['kids'][0]['leaf']}),"
        f" yes: {qs(tr['kids'][1])}? (leaves {tr['kids'][1]['leaf']})  [0 decline, 1 approve]")
say("")
say("CHECK 1: the page's questions route as sklearn's trees (5000 held-out applications)")
worst, oncut = 0, 0
for tr, e in zip(trees, rf.estimators_):
    T = e.tree_
    cuts = [(int(T.feature[i]), float(T.threshold[i])) for i in range(T.node_count) if T.feature[i] >= 0]
    on = np.zeros(len(Xt), bool)
    for f, c in cuts:                        # an application exactly at a cut that lies on the data's grid
        on |= np.abs(Xt[:, f] - c) < 1e-4
    ours = np.array([vote(tr, a) for a in Xt])
    worst = max(worst, int((ours != e.predict(Xt))[~on].sum()))
    oncut = max(oncut, int(((ours != e.predict(Xt)) & on).sum()))
say(f"  disagreements off the cuts, worst tree: {worst}")
say(f"  applications exactly at a cut value (income 49.9 k$ at the cut 49.9): {oncut}; sklearn compares in")
say("  float32, where 49.9 > 49.8999996 sends them right; in exact arithmetic (and on the page) x <= 49.9 goes left")
say("CHECK 2: majority of votes (hard) against sklearn's averaged class shares (soft)")
V = np.array([e.predict(Xt) for e in rf.estimators_]).astype(int)
hard = (V.sum(0) >= 3).astype(int)
say(f"  hard and soft agree on {(hard == rf.predict(Xt)).mean()*100:.2f}% of 5000 applications")
say(f"  held-out accuracy: trees alone {', '.join(f'{(v == yt).mean():.3f}' for v in V)};"
    f" majority vote {(hard == yt).mean():.3f}")
say("CHECK 3: more trees, less overfitting (fully grown trees, same data)")
one = DecisionTreeClassifier(random_state=0).fit(X, y)
big = RandomForestClassifier(n_estimators=300, random_state=0).fit(X, y)
ONE, BIG = one.score(Xt, yt), big.score(Xt, yt)
say(f"  one fully grown tree: training {one.score(X, y):.3f}, held-out {ONE:.3f}")
say(f"  forest of 300 fully grown trees: training {big.score(X, y):.3f}, held-out {BIG:.3f}")
say("CHECK 4: the page's applicants")
for a, v in zip(APPS, votes):
    say(f"  income {a[0]:g}k, credit {a[1]}, debt {a[2]:g} %: votes {v} -> {sum(v)} approve,"
        f" {NT - sum(v)} decline; sklearn soft vote {int(rf.predict([a])[0])}")
say("PAGE (1000 x 520): an applicant every 5 s (3.6 s before 5 Oct 2026), so the forest's answer rests 2.6 s;")
say("  tree 1's edges say no (left) and yes (right); the held-out comparison above (CHECK 3) is kept here,")
say("  out of the figure's parameter line.")
report(STEM, L)

DATA = {"trees": trees, "apps": [list(a) for a in APPS], "one": ONE, "big": BIG}

JS = LIB + r"""
const D = DATA, NTR = D.trees.length;
const CX = k => 102 + 199 * k, RY = 128, KY = 210, LY = 272, VY = 318;
const BX = 500, BY = 414, BW = 330, BH = 80;
const AT0 = .55, AP = 5.0;                  // an applicant every 5 s: the answer rests 2.6 s
const POSTER_T = AT0 + 2.5;
const FN = ['income', 'credit score', 'debt'];
const cond = q => (q.op === 'ge' ? '≥ ' : '≤ ') +
  (q.f === 0 ? '$' + q.v.toFixed(1) + 'k' : q.f === 1 ? q.v.toFixed(0) : q.v.toFixed(1) + '%');
const yes = (q, a) => q.op === 'ge' ? a[q.f] >= q.v - 1e-9 : a[q.f] <= q.v + 1e-9;

function qbox(cx, cy, w, q, a, hot) {
  node(cx, cy, w, 46, [FN[q.f], cond(q)], {alpha: a, size: 16, gap: 19, stroke: hot ? C.accent : C.ink,
    width: hot ? 1.8 : 1.3});
}
function draw() {
  let who = -1, u = 0;
  if (t >= AT0) { const tau = (t - AT0) % (3 * AP); who = Math.floor(tau / AP); u = tau - who * AP; }
  const fade = who >= 0 ? clamp(u / .25) * (1 - clamp((u - (AP - .35)) / .3)) : 0;
  const app = who >= 0 ? D.apps[who] : null;
  let nApprove = 0, nDecline = 0;

  D.trees.forEach((tr, k) => {
    const cx = CX(k), a = arrive(.02 + .05 * k);
    text('tree ' + (k + 1), cx, RY - 36, {size: 16, color: C.body, align: 'center', alpha: a});
    // this applicant's path through tree k
    const s1 = app ? (yes(tr.root, app) ? 1 : 0) : -1, kid = s1 >= 0 ? tr.kids[s1] : null;
    const s2 = kid ? (yes(kid, app) ? 1 : 0) : -1;
    const p1 = app ? clamp((u - .3 - .06 * k) / .32) * fade : 0, p2 = app ? clamp((u - .66 - .06 * k) / .32) * fade : 0;
    const ea = seg(.1 + .04 * k, .3);
    [0, 1].forEach(side => {
      const kx = cx + (side ? 47 : -47);
      line([[cx, RY + 23], [kx, KY - 23]], {width: 1.3, progress: ea});
      if (side === s1 && p1 > 0) line([[cx, RY + 23], [lerp(cx, kx, p1), lerp(RY + 23, KY - 23, p1)]], {color: C.accent, width: 2.2});
      const q = tr.kids[side];
      [0, 1].forEach(s => {
        const lx = kx + (s ? 24 : -24);
        line([[kx, KY + 23], [lx, LY - 8]], {width: 1.1, progress: seg(.2 + .04 * k, .3)});
        if (side === s1 && s === s2 && p2 > 0) line([[kx, KY + 23], [lerp(kx, lx, p2), lerp(KY + 23, LY - 8, p2)]], {color: C.accent, width: 2.2});
        const la = arrive(.24 + .04 * k);
        box(lx - 8, LY - 8, 16, 16, {fill: q.leaf[s] ? C.navy : '#fff', stroke: C.navy, width: 1.4, alpha: la});
        if (side === s1 && s === s2) ring(lx, LY, 13, {alpha: clamp((u - .98 - .06 * k) / .15) * fade});
      });
      qbox(kx, KY, 90, q, arrive(.12 + .04 * k), side === s1 && p1 >= 1);
    });
    // the first tree says which way an answer goes, as Figure 10 does: no to the left, yes to the right
    if (k === 0) {
      const la = clamp(ea * 2 - 1), my = (RY + 23 + KY - 23) / 2 + 5;
      text('no', cx - 23.5 - 13, my, {size: 16, italic: true, color: C.body, align: 'right', alpha: la});
      text('yes', cx + 23.5 + 13, my, {size: 16, italic: true, color: C.body, alpha: la});
    }
    qbox(cx, RY, 118, tr.root, a, app && p1 > 0);
    // the vote
    if (app) {
      const v = kid.leaf[s2], va = clamp((u - 1.05 - .06 * k) / .2) * fade;
      text(v ? 'approve' : 'decline', cx, VY, {size: 16, bold: true, color: v ? C.navy : C.body, align: 'center', alpha: va});
      const fp = clamp((u - 1.25 - .05 * k) / .3), tx = BX + (k - 2) * 44, ty = BY - BH / 2;
      if (fp > 0) line([[cx, VY + 8], [lerp(cx, tx, fp), lerp(VY + 8, ty, fp)]],
        {color: v ? C.navy : C.guide, width: v ? 1.6 : 1.2, dash: v ? null : [4, 3], alpha: fade});
      if (fp >= 1) { if (v) nApprove++; else nDecline++; }
    }
  });

  // the majority box
  const ba = arrive(.3);
  box(BX - BW / 2, BY - BH / 2, BW, BH, {fill: '#fff', stroke: C.ink, width: 1.3, alpha: ba});
  text('majority vote', BX, BY - 16, {size: 16, color: C.body, align: 'center', alpha: ba});
  if (app) {
    const cnt = (nApprove + nDecline) ? nApprove + ' approve  :  ' + nDecline + ' decline' : '';
    text(cnt, BX, BY + 6, {size: 16, align: 'center', alpha: fade});
    const fa = clamp((u - 1.85) / .2) * fade, win = nApprove > nDecline;
    if (nApprove + nDecline === NTR)
      text('final prediction: ' + (win ? 'approve' : 'decline'), BX, BY + 29,
        {size: 17, bold: true, color: C.accent, align: 'center', alpha: fa});
    // the applicant
    const [ai, ac, ad] = app;
    text('applicant', 30, 38, {size: 16, bold: true, alpha: fade});
    text('income $' + ai.toFixed(0) + 'k,  credit score ' + ac + ',  debt ' + ad.toFixed(0) + '% of income', 122, 38,
      {size: 16, alpha: fade});
  }
  // key to the leaves
  const ka = arrive(.5), kx = 742, ky = 30;
  box(kx, ky - 12, 14, 14, {fill: C.navy, stroke: C.navy, width: 1.4, alpha: ka});
  text('leaf: approve', kx + 20, ky + 1, {size: 16, alpha: ka});
  box(kx + 136, ky - 12, 14, 14, {fill: '#fff', stroke: C.navy, width: 1.4, alpha: ka});
  text('decline', kx + 156, ky + 1, {size: 16, alpha: ka});
  text('5 trees of depth 2; bootstrap samples; 2 of 3 features a split', 18, H - 14,
       {size: 15, color: C.muted, alpha: arrive(.9)});
}
boot();
"""

TITLE = "Figure 11: Random Forest: each tree votes independently"
ARIA = ("Five small decision trees grown on different random samples of the loan applications ask "
        "different questions. An applicant is passed down each tree, each tree votes approve or "
        "decline, and the votes are counted in a majority box that gives the forest's final prediction; "
        "three applicants take turns.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 520, DATA, JS)
    print(common.still(NAME))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.6, 1.2, 2.0, 3.0, 5.0]))
