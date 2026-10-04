"""What the machine learning figures (Figures 14 to 23 of the machine learning
guide, tools/numfig/mlb_*.py) share on top of common.py and engine.js.

JS_LIB is prepended to each figure's script: the class colours his captions
use (crimson, purple, and blue for a third group; orange only where a caption names it), TikZ marks (circle, star,
cross), a legend box, pixel grids and a network node. publish() writes the
check file, the page, the printed frame and, with --look, a few moments of
the motion to look at.

Timing (README, round 2): frames and axes draw from 0 to about .4 s, the main
curves or structures by .7 s, labels arrive with settle(t0, .28), the model's
own motion starts by .6 s and every arrival is over by 1.4 s.
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402

LOOK = os.environ.get("MLB_LOOK") or os.path.join(
    os.environ.get("TEMP", "/tmp"), "mlb-look")

JS_LIB = r"""
/* ------------------------------------------------ mlb: machine learning figures */
const S = .28;                                   // a label arriving: settle(t0, S)
const lab = t0 => settle(t0, S);
const rise = s => 5 * (1 - s);                   // ... settling 5 units into place
/* the classes: crimson and purple, and blue for a third group. Figure 14's
   caption names its classes orange and purple, so that figure (mlb_knn.py)
   adds K.orange for itself */
const K = {
  red: C.amber, redEdge: C.accent,
  purple: '#6A4F94', purpleEdge: '#46315F',
  blue: '#2E6A9E', blueEdge: C.navy,
};
const CLS = [[K.red, K.redEdge], [K.purple, K.purpleEdge], [K.blue, K.blueEdge]];
const HOLLOW = ['#FFFFFF', C.guide];
/* signed values (weights, activations, vector entries): positive blue,
   negative crimson, matched in lightness, the engine's DIVERGING read from its
   other end; the same in mlc_lib.py, so every figure of the guide agrees */
const SIGNED = (() => { const L = new Uint8ClampedArray(768); for (let i = 0; i < 256; i++) for (let c = 0; c < 3; c++) L[i * 3 + c] = DIVERGING[(255 - i) * 3 + c]; return L; })();
const signed = v => { const i = Math.round((clamp(v, -1, 1) + 1) / 2 * 255) * 3; return '#' + [0, 1, 2].map(c => SIGNED[i + c].toString(16).padStart(2, '0')).join(''); };
const S_POS = C.blue, S_NEG = C.accent;
/* a colour between two, as #rrggbb (so mixes can be mixed again) */
const _h2 = v => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0');
function mixHex(a, b, s) {
  const A = _hex(a), B = _hex(b);
  return '#' + _h2(lerp(A[0], B[0], s)) + _h2(lerp(A[1], B[1], s)) + _h2(lerp(A[2], B[2], s));
}
/* a mark as pgfplots draws it: circle, square, triangle or a five pointed star */
function mark(kind, x, y, r, o = {}) {
  const { fill = '#fff', stroke = C.ink, width = 1.2, alpha = 1 } = o;
  if (alpha <= 0 || r <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath();
  if (kind === 'star') {
    for (let i = 0; i < 10; i++) {
      const a = -Math.PI / 2 + i * Math.PI / 5, q = i % 2 ? r * .45 : r;
      if (i) ctx.lineTo(x + q * Math.cos(a), y + q * Math.sin(a)); else ctx.moveTo(x + q * Math.cos(a), y + q * Math.sin(a));
    }
    ctx.closePath();
  } else if (kind === 'square') ctx.rect(x - r, y - r, 2 * r, 2 * r);
  else if (kind === 'triangle') { ctx.moveTo(x, y - r * 1.15); ctx.lineTo(x + r, y + r * .7); ctx.lineTo(x - r, y + r * .7); ctx.closePath(); }
  else ctx.arc(x, y, r, 0, 2 * Math.PI);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.stroke(); }
  ctx.restore();
}
/* a cross (a cluster center): two strokes over a white halo */
function cross(x, y, r, o = {}) {
  const { color = C.ink, width = 3, alpha = 1 } = o;
  if (alpha <= 0) return;
  for (const [c, w] of [['#fff', width + 3.2], [color, width]]) {
    line([[x - r, y - r], [x + r, y + r]], { color: c, width: w, alpha });
    line([[x - r, y + r], [x + r, y - r]], { color: c, width: w, alpha });
  }
}
/* a legend inside the axes: a thin box, white fill, serif 15. rows are
   [draw(x, y, alpha), words, asMath] with the key drawn at (x, y) */
function legend(x, y, w, rows, o = {}) {
  const { alpha = 1, rowH = 22, size = 15 } = o;
  if (alpha <= 0) return;
  const h = rows.length * rowH + 10;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = '#fff'; ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.strokeRect(x, y, w, h); ctx.restore();
  rows.forEach(([key, words, asMath], i) => {
    const yy = y + 5 + rowH * (i + .5);
    key(x + 22, yy, alpha);
    if (asMath) math(words, x + 42, yy + size * .34, { size, alpha });
    else text(words, x + 42, yy + size * .34, { size, alpha });
  });
  return h;
}
/* a filled and outlined rectangle */
function rect(x, y, w, h, o = {}) {
  const { fill = null, stroke = C.ink, width = 1.2, alpha = 1, dash = null } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha;
  if (fill) { ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; if (dash) ctx.setLineDash(dash); ctx.strokeRect(x, y, w, h); }
  ctx.restore();
}
/* an n by m grid of cells from (x, y), cell size s, colour col(i, j) or null */
function cells(x, y, n, m, s, col, o = {}) {
  const { alpha = 1, gridColor = C.rule, gridWidth = .8, frame = C.ink, frameWidth = 1.2 } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha;
  for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
    const c = col(i, j); if (!c) continue;
    ctx.fillStyle = c; ctx.fillRect(x + j * s, y + i * s, s + .35, s + .35);
  }
  if (gridColor) {
    ctx.strokeStyle = gridColor; ctx.lineWidth = gridWidth; ctx.beginPath();
    for (let i = 1; i < n; i++) { ctx.moveTo(x, y + i * s); ctx.lineTo(x + m * s, y + i * s); }
    for (let j = 1; j < m; j++) { ctx.moveTo(x + j * s, y); ctx.lineTo(x + j * s, y + n * s); }
    ctx.stroke();
  }
  if (frame) { ctx.strokeStyle = frame; ctx.lineWidth = frameWidth; ctx.strokeRect(x, y, m * s, n * s); }
  ctx.restore();
}
/* a neuron: a circle, ink outline, filled with the colour of its value */
function node(x, y, r, o = {}) {
  const { fill = '#fff', stroke = C.ink, width = 1.4, alpha = 1 } = o;
  mark('circle', x, y, r, { fill, stroke, width, alpha });
}
/* piecewise linear interpolation on an increasing grid */
function interp(xs, ys, x) {
  let lo = 0, hi = xs.length - 1;
  if (x <= xs[0]) return ys[0]; if (x >= xs[hi]) return ys[hi];
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] > x) hi = m; else lo = m; }
  return lerp(ys[lo], ys[hi], (x - xs[lo]) / (xs[hi] - xs[lo]));
}
/* a number for math(): fixed decimals, the minus sign is the engine's */
const num = (v, d = 2) => (Math.abs(v) < .5 * Math.pow(10, -d) ? 0 : v).toFixed(d);
/* the clock of a motion that starts at t0 and eases in over r seconds */
function runClock(t0, r = .6) {
  const s = t - t0;
  return s <= 0 ? 0 : s < r ? s * s / (2 * r) : s - r / 2;
}
"""


def check(name, lines):
    """Write tools/numfig/mlb_<name>.check.txt and print it."""
    body = "\n".join(lines) + "\n"
    print(body)
    with open(os.path.join(HERE, f"mlb_{name}.check.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(body)


def publish(name, title, aria, w, h, data, js, look=(), digits=5):
    """Write content/anim/nf-mlb-<name>.html and its printed frame; with
    --look on the command line, also photograph the moments in `look`."""
    page = common.build_html(f"mlb-{name}", title, aria, w, h, data, JS_LIB + js, digits)
    kb = os.path.getsize(page) / 1024
    print(f"page {page} ({kb:.0f} KB)")
    png = common.still(f"mlb-{name}")
    print(f"still {png}")
    if "--look" in sys.argv and look:
        os.makedirs(LOOK, exist_ok=True)
        for p in common.frames(f"mlb-{name}", list(look), out=LOOK):
            print(f"frame {p}")
    return png
