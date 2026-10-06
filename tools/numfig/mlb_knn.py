"""Figure 14: KNN, a new patient (the star) classified by a majority vote of
its K = 3 nearest neighbours: 2 orange, 1 purple, so orange.

Data: 31 patients with known labels in two standardized features, 16 orange
and 15 purple. Most are drawn from two Gaussian groups; three are placed
around the new patient at 0.30 to 0.56 so that its three nearest neighbours
are orange, purple, orange and the fourth is clearly farther (0.82). All
distances are Euclidean, in standardized units.

The motion is the method. A circle grows from the star at a steady speed and
takes each patient in the order of its distance; at the third the vote is
counted and the star takes the winning colour. Then the star visits two more
positions (other new patients) and comes back: at every moment its three
nearest neighbours, their distances and the vote are recomputed from the
data, and the tinted regions (every point's K = 3 vote, computed on a grid)
show why the colour changes where it does.

Run: python tools/numfig/mlb_knn.py [--look]
"""
import numpy as np
from sklearn.neighbors import KNeighborsClassifier

import mlb_common as mc

NAME = "knn"
SEED, K = 70, 3
STAR0, DD, ANG, EXCL, NPER = (0.05, 0.1), (0.32, 0.43, 0.54), (155, -35, 75), 0.72, 14


def make(seed):
    r = np.random.default_rng(seed)
    s = np.array(STAR0)
    pts, lab = [], []
    for m, cls in (((-0.95, 0.7), 0), ((0.95, -0.6), 1)):
        k = 0
        while k < NPER:
            p = r.normal(m, [0.55, 0.55])
            if np.linalg.norm(p - s) < EXCL or np.abs(p).max() > 2.2:
                continue
            if pts and np.min(np.linalg.norm(np.array(pts) - p, axis=1)) < 0.2:
                continue
            pts.append(p); lab.append(cls); k += 1
    for d, a, cls in zip(DD, ANG, (0, 1, 0)):
        pts.append(s + d * np.array([np.cos(np.radians(a)), np.sin(np.radians(a))])); lab.append(cls)
    X, y = np.array(pts), np.array(lab)
    mu, sd = X.mean(0), X.std(0)
    return (X - mu) / sd, y, (s - mu) / sd


X, y, star = make(SEED)
clf = KNeighborsClassifier(n_neighbors=K).fit(X, y)
dist, idx = clf.kneighbors(star[None], n_neighbors=5)
dist, idx = dist[0], idx[0]
pred = int(clf.predict(star[None])[0])

# two more new patients the star visits: one the vote gives to purple, one a clear orange
def vote(p):
    d = np.linalg.norm(X - p, axis=1)
    o = np.argsort(d)[:K]
    return int(np.sum(y[o] == 0)), d[o]


cands = [np.array([a, b]) for a in np.linspace(-1.6, 1.6, 33) for b in np.linspace(-1.6, 1.6, 33)]
A = min((c for c in cands if vote(c)[0] == 1 and np.linalg.norm(c - star) > 0.6),
        key=lambda c: abs(np.linalg.norm(c - star) - 0.9) + 0.3 * abs(c[1] - star[1] + 0.55))
B = min((c for c in cands if vote(c)[0] == 3 and np.linalg.norm(c - star) > 0.6),
        key=lambda c: abs(np.linalg.norm(c - star) - 0.95) + 0.3 * abs(c[0] - star[0] + 0.5))

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-knn: Figure 14, KNN with K = 3")
say("")
say("MODEL")
say(f"  {len(y)} patients with known labels ({int(np.sum(y == 0))} orange, {int(np.sum(y == 1))} purple), two features")
say(f"  standardized to mean 0 and deviation 1 (the star with the same transform). Seed {SEED}.")
say(f"  {2*NPER} drawn from two Gaussian groups (sd 0.55, none within {EXCL} of the star); three placed")
say(f"  at {DD} from the star before standardizing. K = {K}, Euclidean distance, majority vote.")
say(f"  new patient (star) at ({star[0]:.4f}, {star[1]:.4f})")
say("")
say("CHECK 1: scikit-learn's KNeighborsClassifier against a direct computation")
d_all = np.linalg.norm(X - star, axis=1)
o = np.argsort(d_all)
say(f"  nearest five by brute force: {o[:5].tolist()}, distances {np.round(d_all[o[:5]], 4).tolist()}")
say(f"  scikit-learn kneighbors:     {idx.tolist()}, distances {np.round(dist, 4).tolist()}")
say(f"  max |difference| in distance: {np.max(np.abs(dist - d_all[o[:5]])):.1e}")
names = ["orange", "purple"]
say(f"  the three nearest: {', '.join(names[c] for c in y[idx[:3]])}; vote {int(np.sum(y[idx[:3]] == 0))} orange,"
    f" {int(np.sum(y[idx[:3]] == 1))} purple; scikit-learn predicts {names[pred]}")
say(f"  gaps: d2/d1 = {dist[1]/dist[0]:.3f}, d3/d2 = {dist[2]/dist[1]:.3f}, d4/d3 = {dist[3]/dist[2]:.3f}"
    " (the order is not a rounding accident)")
say("")
say("CHECK 2: the page's own vote (the same brute force in JavaScript) against scikit-learn on the region grid")
gx = np.linspace(-2.3, 2.3, 451)
G = np.array([[a, b] for b in gx for a in gx])
dG = np.linalg.norm(G[:, None, :] - X[None], axis=2)
kn = np.argsort(dG, axis=1)[:, :K]
mine = (np.sum(y[kn] == 0, axis=1) < 2).astype(int)
sk = clf.predict(G)
say(f"  {G.shape[0]} grid points, agreement {np.mean(mine == sk):.6f}")
say("")
say("CHECK 3: leave one out accuracy on the 31 patients (each classified by the other 30)")
for k in (1, 3, 5):
    acc = np.mean([KNeighborsClassifier(k).fit(np.delete(X, i, 0), np.delete(y, i)).predict(X[i:i+1])[0] == y[i]
                   for i in range(len(y))])
    say(f"  K = {k}: {acc:.3f}")
say("")
say("TOUR: the star also visits")
for nm, p in (("A", A), ("B", B)):
    v, d = vote(p)
    say(f"  {nm} ({p[0]:+.3f}, {p[1]:+.3f}): {v} orange, {K - v} purple, distances {np.round(d, 3).tolist()}")
mc.check(NAME, L)

DATA = {"x": X, "y": y, "star": star, "A": A, "B": B, "k": K}

JS = r"""
/* his caption names the classes orange and purple ("2 orange, 1 purple"):
   the one figure that keeps an orange */
K.orange = '#D9822B'; K.orangeEdge = '#A5510B';
const D = DATA, NP = D.y.length, XL = 2.3;
const AX = { x: 74, y: 24, w: 450, h: 450 };
const SX = v => AX.x + (v + XL) / (2 * XL) * AX.w, SY = v => AX.y + AX.h - (v + XL) / (2 * XL) * AX.h;
const UNIT = AX.w / (2 * XL);                    // drawing units per standardized unit
const CLSN = ['orange', 'purple'];

/* the K nearest of a point: indices and distances, by brute force */
const NI = new Int32Array(3), ND = new Float64Array(3);
function nearest(px, py) {
  ND.fill(Infinity);
  for (let i = 0; i < NP; i++) {
    const d = Math.hypot(D.x[i][0] - px, D.x[i][1] - py);
    if (d < ND[2]) {
      let k = 2; while (k > 0 && d < ND[k - 1]) { ND[k] = ND[k - 1]; NI[k] = NI[k - 1]; k--; }
      ND[k] = d; NI[k] = i;
    }
  }
}
/* the regions: every grid point's own K = 3 vote, computed once */
const GRN = 451, reg = document.createElement('canvas'); reg.width = GRN; reg.height = GRN;
(() => {
  const g = reg.getContext('2d'), im = g.createImageData(GRN, GRN), O = _hex('#F8E4CF'), P = _hex('#E6E0F0');
  for (let r = 0; r < GRN; r++) for (let c = 0; c < GRN; c++) {
    nearest(-XL + 2 * XL * c / (GRN - 1), XL - 2 * XL * r / (GRN - 1));
    let o = 0; for (let k = 0; k < 3; k++) if (D.y[NI[k]] === 0) o++;
    const col = o >= 2 ? O : P, q = (r * GRN + c) * 4;
    im.data[q] = col[0]; im.data[q + 1] = col[1]; im.data[q + 2] = col[2]; im.data[q + 3] = 255;
  }
  g.putImageData(im, 0, 0);
})();

/* the clock: the search, then a tour of two more new patients and back */
const T_S = .6, R_DUR = 1.1;
nearest(D.star[0], D.star[1]);
const D0 = Array.from(ND), I0 = Array.from(NI), R3 = D0[2];
const rNow = () => R3 * (1 - Math.pow(1 - clamp((t - T_S) / R_DUR), 2));      // eases out onto the third
const tFound = k => T_S + R_DUR * (1 - Math.sqrt(1 - D0[k] / R3));            // when the circle reaches it
const T_VOTE = tFound(2) + .12, POSTER_T = T_VOTE + 1.2;
const T_TOUR = POSTER_T + 3, GL = 1.3, RST = 2.6, HOME = 4.2;
const WAY = [D.star, D.A, D.B, D.star];
const TPER = 3 * GL + 2 * RST + HOME;
function starPos() {
  if (t < T_TOUR) return D.star;
  const c = (t - T_TOUR) % TPER;
  let t0 = 0;
  for (let k = 0; k < 3; k++) {
    if (c < t0 + GL + RST || k === 2) {
      const s = settle(t - c + t0, GL * .85);
      return [lerp(WAY[k][0], WAY[k + 1][0], s), lerp(WAY[k][1], WAY[k + 1][1], s)];
    }
    t0 += GL + RST;
  }
  return D.star;
}

function draw() {
  const inSearch = t < T_TOUR, sp = starPos();
  // the regions under everything, clipped to the plot
  ctx.save(); ctx.beginPath(); ctx.rect(AX.x, AX.y, AX.w, AX.h); ctx.clip();
  ctx.globalAlpha = seg(.25, .35); ctx.imageSmoothingEnabled = true;
  const cw = AX.w / (GRN - 1); ctx.drawImage(reg, AX.x - cw / 2, AX.y - cw / 2, AX.w + cw, AX.h + cw); ctx.restore();
  const A = axes({ ...AX, xlim: [-XL, XL], ylim: [-XL, XL], xticks: [-2, -1, 0, 1, 2], yticks: [-2, -1, 0, 1, 2],
    xlabel: 'x_1', ylabel: 'x_2', ylabelGap: 36, tickSize: 16, progress: seg(0, .35) });

  // the star's K nearest now; in the search, only those the circle has reached
  nearest(sp[0], sp[1]);
  const r = inSearch ? rNow() : ND[2];
  const found = k => inSearch ? clamp((t - tFound(k)) / .25) : 1;
  const cx = SX(sp[0]), cy = SY(sp[1]);
  A.inside(() => {
    if (t > T_S) {
      ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = 1.2; ctx.setLineDash([5, 4]);
      ctx.beginPath(); ctx.arc(cx, cy, Math.max(.01, r * UNIT), 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
    }
    for (let k = 0; k < 3; k++) {
      const f = found(k); if (f <= 0) continue;
      const i = NI[k], x = SX(D.x[i][0]), y = SY(D.x[i][1]);
      line([[cx, cy], [x, y]], { color: C.ink, width: 1.3, progress: easeOut(f) });
    }
  });
  // the patients with known labels
  for (let i = 0; i < NP; i++) {
    const p = settle(.06 + .006 * i, .24); if (p <= 0) continue;
    const c = CLSN[D.y[i]], s = .6 + .4 * p;
    mark(D.y[i] ? 'square' : 'circle', SX(D.x[i][0]), SY(D.x[i][1]), (D.y[i] ? 4.2 : 4.8) * s,
         { fill: c === 'orange' ? K.orange : K.purple, stroke: c === 'orange' ? K.orangeEdge : K.purpleEdge, width: 1.1, alpha: p });
  }
  for (let k = 0; k < 3; k++) {                  // the neighbours found, ringed and ranked
    const f = found(k); if (f <= 0) continue;
    const i = NI[k], x = SX(D.x[i][0]), y = SY(D.x[i][1]), a = settle(inSearch ? tFound(k) : -1, .22);
    mark('circle', x, y, 10, { fill: null, stroke: C.ink, width: 1.3, alpha: a });
    const ux = x - cx, uy = y - cy, n = Math.hypot(ux, uy) || 1;
    text(String(k + 1), x + ux / n * 20, y + uy / n * 20 + 6, { size: 16, bold: true, align: 'center', alpha: a });
  }
  // the vote and the star's colour
  let no = 0; for (let k = 0; k < 3; k++) if (D.y[NI[k]] === 0) no++;
  const win = no >= 2 ? 0 : 1, va = inSearch ? seg(T_VOTE, .3) : 1;
  const sa = settle(.3, .28);
  const fill = win === 0 ? mixHex('#FFFFFF', K.orange, va) : mixHex('#FFFFFF', K.purple, va);
  mark('star', cx, cy + rise(sa), 13 * (.7 + .3 * sa), { fill, stroke: C.ink, width: 1.5, alpha: sa });

  /* the tally */
  const TX = 598, la = lab(.2);
  math('K = 3', TX, 62 + rise(la), { size: 17, alpha: la });
  text('nearest neighbors', TX + 52, 62 + rise(la), { size: 17, color: C.body, alpha: la });
  line([[TX, 76], [TX + 360, 76]], { color: C.rule, width: 1, alpha: la });
  for (let k = 0; k < 3; k++) {
    const a = inSearch ? settle(tFound(k), .28) : 1; if (a <= 0) continue;
    const i = NI[k], y = 108 + 34 * k + rise(a), c = D.y[i];
    text(String(k + 1), TX + 6, y, { size: 16, bold: true, align: 'center', alpha: a });
    mark(c ? 'square' : 'circle', TX + 34, y - 5, c ? 4.2 : 4.8, { fill: c ? K.purple : K.orange, stroke: c ? K.purpleEdge : K.orangeEdge, width: 1.1, alpha: a });
    text(CLSN[c], TX + 50, y, { size: 16, alpha: a });
    math(`d = ${ND[k].toFixed(2)}`, TX + 360, y, { size: 16, align: 'right', color: C.body, alpha: a });
  }
  const vv = inSearch ? settle(T_VOTE, .28) : 1;
  if (vv > 0) {
    line([[TX, 196], [TX + 360, 196]], { color: C.rule, width: 1, alpha: vv });
    text(`vote: ${no} orange, ${3 - no} purple`, TX, 228 + rise(vv), { size: 16, color: C.body, alpha: vv });
    mark('star', TX + 8, 258 + rise(vv), 9, { fill: win ? K.purple : K.orange, stroke: C.ink, width: 1.2, alpha: vv });
    text('classified as', TX + 26, 264 + rise(vv), { size: 17, alpha: vv });
    text(CLSN[win], TX + 124, 264 + rise(vv), { size: 17, bold: true, color: win ? K.purpleEdge : K.orangeEdge, alpha: vv });
  }
  // legend
  const lg = lab(.45);
  legend(TX, 372, 190, [
    [(x, y, a) => mark('circle', x, y, 4.8, { fill: K.orange, stroke: K.orangeEdge, width: 1.1, alpha: a }), 'orange class'],
    [(x, y, a) => mark('square', x, y, 4.2, { fill: K.purple, stroke: K.purpleEdge, width: 1.1, alpha: a }), 'purple class'],
    [(x, y, a) => mark('star', x, y, 9, { fill: '#fff', stroke: C.ink, width: 1.3, alpha: a }), 'new patient'],
  ], { alpha: lg });
  text(`${NP} synthetic patients, standardized; Euclidean distance`,
       18, H - 12, { size: 15, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 14: KNN: the star (new patient) looks at its K=3 nearest neighbors"
ARIA = ("A scatter of patients with known labels, orange circles and purple squares, over tinted "
        "regions showing how every point would be voted. A dashed circle grows from a star, the new "
        "patient, and reaches its three nearest neighbors in order: orange, purple, orange. The vote is "
        "2 orange, 1 purple, so the star is classified as orange. The star then visits two other "
        "positions and returns, its neighbors and vote updating as it moves.")

if __name__ == "__main__":
    print(f"star {star}, neighbours {[names[c] for c in y[idx[:3]]]}, d {np.round(dist[:4], 3)}, A {A}, B {B}")
    mc.publish(NAME, TITLE, ARIA, 1000, 572, DATA, JS, look=(0.3, 0.7, 1.0, 1.3, 1.7, 2.2, 6.2, 7.5, 9.5, 12.0))
