"""What the machine learning guide's figures share (Figures 2, 4 and 6 to 13
of doc/machine-learning-the-complete-picture-and-guide-5.html, stems image1 to
image10; README.md in this folder is the contract they keep).

LIB is a small set of drawing helpers in the engine's own terms (engine.js),
prepended to each figure's script so the ten figures draw their marks,
tables, tree nodes and loops alike. report() writes and prints the check file.
Nothing here changes engine.js or common.py.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "machine-learning-the-complete-picture-and-guide-5"


def report(stem, lines):
    """Write tools/numfig/<stem>.check.txt and print it."""
    txt = "\n".join(lines).rstrip() + "\n"
    with open(os.path.join(HERE, f"{stem}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


def loan_data(seed=11, n=200):
    """The simulated loan applications of Figures 10 and 11: income (k$ a
    year, to 0.1), credit score (whole), debt as a share of income (%, to
    0.1), and the recorded decision (1 approved): a lender's rule with 5 % of
    the decisions flipped. Returns inc, cs, dti, y, flip."""
    import numpy as np
    rng = np.random.default_rng(seed)
    inc = np.round(np.exp(rng.normal(np.log(52), 0.38, n)), 1)
    cs = np.round(np.clip(rng.normal(690, 45, n), 500, 850))
    dti = np.round(rng.uniform(8, 48, n), 1)
    rule = np.where(inc <= 50, cs > 720, dti < 38)
    flip = rng.random(n) < 0.05
    y = np.where(flip, ~rule, rule).astype(int)
    return inc, cs, dti, y, flip


def house_data():
    """The 14 simulated house sales of Figures 2 and 8: floor area (ft^2, to
    10) and price (k$, to 1), from price = 40 + 0.170 area + N(0, 38^2)."""
    import numpy as np
    rng = np.random.default_rng(2)
    base = 1000 + np.arange(14) * (1800 / 13)
    x = np.round((base + rng.uniform(-40, 40, 14)) / 10) * 10
    y = np.round(40.0 + 0.170 * x + rng.normal(0, 38.0, 14))
    return x, y


def on_grid_above(t, step):
    """The smallest value on the data's grid (0.1 or 1) above a tree's cut t:
    for grid values, x > t <=> x >= this. Cuts are float32 midpoints."""
    import numpy as np
    return float(np.round((np.floor(t / step + 1e-4) + 1) * step, 6))


def on_grid_below(t, step):
    """The largest grid value at or below the cut t: x <= t <=> x <= this."""
    import numpy as np
    return float(np.round(np.floor(t / step + 1e-4) * step, 6))


LIB = r"""
/* ---------------------------------------------------------------- mla
   helpers shared by the machine learning guide's figures */
const arrive = t0 => settle(t0, .28);                 // a label or a mark arriving
const sp = (dt, v = .5) => dt <= 0 ? 0 : settle(t - dt, v);   // a spring let go dt seconds ago
function sub(letter, x, y, words, a = 1) {            // (a) and a subtitle of a few words
  panel(letter, x, y, {alpha: a});
  if (words) text(words, x + 35, y, {size: 17, color: C.body, alpha: a});
}
const nfmt = (v, d = 0) => (v < 0 ? '−' : '') + Math.abs(v).toFixed(d);
const thou = v => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

/* a data mark. kind 1: a filled navy disc; 0: an open disc; 2: unlabelled
   (grey); 3: the accent (the one thing to follow); 4: filled sky. `a` is its
   arrival, 0 to 1: it grows from 0.9 of its size as it fades in, never from
   nothing. */
function mark(x, y, kind, a = 1, r = 4.6) {
  if (a <= 0) return;
  const rr = r * (.9 + .1 * Math.min(a, 1));
  ctx.save(); ctx.globalAlpha *= clamp(a); ctx.beginPath(); ctx.arc(x, y, rr, 0, 2 * Math.PI);
  if (kind === 0) { ctx.fillStyle = '#fff'; ctx.fill(); ctx.strokeStyle = C.navy; ctx.lineWidth = 1.5; ctx.stroke(); }
  else {
    ctx.fillStyle = kind === 1 ? C.navy : kind === 2 ? C.guide : kind === 3 ? C.accent : C.sky;
    ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = .9; ctx.stroke();
  }
  ctx.restore();
}
/* a ring around a mark: support vectors, the applicant, a flagged value */
function ring(x, y, r, o = {}) {
  const { color = C.accent, width = 1.8, alpha = 1, dash = null } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.arc(x, y, r, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
}
/* a filled rectangle, optionally outlined */
function box(x, y, w, h, o = {}) {
  const { fill = null, stroke = null, width = 1, alpha = 1, dash = null } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha;
  if (fill) { ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; if (dash) ctx.setLineDash(dash); ctx.strokeRect(x, y, w, h); }
  ctx.restore();
}
/* a legend inside the axes: a thin 1 px box, white fill, serif 16 (the round of 5 Oct 2026:
   legends 16 to 17). rows: [[drawKey(x, y), label], ...]; key drawn in a 30 unit slot */
function legend(x, y, rows, a = 1, w = 0) {
  if (a <= 0) return;
  ctx.save(); ctx.font = font({size: 16});
  const tw = Math.max(...rows.map(r => ctx.measureText(r[1]).width)); ctx.restore();
  const W_ = w || tw + 60, H_ = rows.length * 24 + 10;
  box(x, y, W_, H_, {fill: '#fff', stroke: C.ink, width: 1, alpha: a});
  rows.forEach(([key, lab], i) => {
    const yy = y + 23 + 24 * i;
    ctx.save(); ctx.globalAlpha *= a; key(x + 22, yy - 5); ctx.restore();
    text(lab, x + 44, yy, {size: 16, alpha: a});
  });
  return W_;
}
/* a step function drawn from edges e[0..n] and values v[0..n-1] */
function stepPts(e, v, X, Y) {
  const p = [];
  for (let i = 0; i < v.length; i++) { p.push([X(e[i]), Y(v[i])]); p.push([X(e[i + 1]), Y(v[i])]); }
  return p;
}

/* forever: rest at each stop, glide to the next with Motion's spring
   (bounce 0) of visual duration G. stops [[v, rest], ...]. Before t0 the
   value is the last stop; at t0 it glides to the first, and so on round.
   Returns {from, to, p (0..1), k (index of `to`)}; p follows the spring. */
function cycle(t0, stops, G) {
  const n = stops.length; let P = 0;
  for (const s of stops) P += G + s[1];
  if (t < t0) return {from: stops[n - 1][0], to: stops[n - 1][0], p: 1, k: n - 1};
  const tau = (t - t0) % P;
  let S = 0, k = 0;
  for (k = 0; k < n; k++) { const L = G + stops[k][1]; if (tau < S + L || k === n - 1) break; S += L; }
  return {from: stops[(k + n - 1) % n][0], to: stops[k][0], p: sp(tau - S, G), k};
}
const cyc = c => Array.isArray(c.to) ? c.to.map((v, i) => lerp(c.from[i], v, c.p)) : lerp(c.from, c.to, c.p);

/* TikZ node: a rectangle with ink outline, lines of text centred inside */
function node(cx, cy, w, h, lines, o = {}) {
  const { fill = '#fff', stroke = C.ink, width = 1.3, alpha = 1, size = 16, color = C.ink, gap = 20 } = o;
  if (alpha <= 0) return;
  box(cx - w / 2, cy - h / 2, w, h, {fill, stroke, width, alpha});
  const y0 = cy - (lines.length - 1) * gap / 2 + size * .34;
  lines.forEach((s, i) => {
    const spec = typeof s === 'string' ? {s} : s;
    if (spec.math) math(spec.s, cx, y0 + i * gap, {size: spec.size || size, align: 'center', color: spec.color || color, alpha});
    else text(spec.s, cx, y0 + i * gap, {size: spec.size || size, align: 'center', color: spec.color || color,
                                        alpha, italic: spec.italic, bold: spec.bold});
  });
}
/* booktabs rules across [x0, x1] at y: top and bottom 1.3, mid 0.8 */
function rule(x0, x1, y, o = {}) {
  const { width = .8, alpha = 1, progress = 1, color = C.ink } = o;
  line([[x0, y], [x1, y]], {color, width, alpha, progress});
}
/* the width of a run of text or math, without drawing it */
function tw(s, size = 16, o = {}) {
  ctx.save(); ctx.font = font({size, ...o}); const w = ctx.measureText(s).width; ctx.restore(); return w;
}
function mw(s, size = 16) { return math(s, 0, -1e4, {size, alpha: 0}); }
"""
