"""What the machine learning guide's figures 24 to 33 share (mlc_*.py).

LIB is JavaScript set before each figure's own script, after engine.js: a few
TikZ-like shapes the engine does not have (a box, a curved arrow, a vector of
coloured cells, a colour bar), a label that arrives on Motion's spring, and
number formatting with a true minus sign. build() writes the page and its
still through common.py, and the check file beside the generator.
"""
import os

import common

HERE = os.path.dirname(os.path.abspath(__file__))

LIB = r"""
/* ---- mlc shared: shapes, labels, numbers (tools/numfig/mlc_lib.py) ---- */
const MINUS = '−';
function nf(v, d = 2) { const s = (Math.abs(v) < .5 * Math.pow(10, -d) ? 0 : v).toFixed(d); return s.replace('-', MINUS); }
function pct(v) { return Math.round(v * 100) + ' %'; }
/* a TikZ rectangle: outline drawing itself with `progress`, fill fading in behind it */
function box(x, y, w, h, o = {}) {
  const { fill = null, stroke = C.ink, width = 1.3, alpha = 1, progress = 1, dash = null, fillAlpha = 1 } = o;
  if (progress <= 0 || alpha <= 0) return;
  if (fill) { ctx.save(); ctx.globalAlpha *= alpha * fillAlpha * clamp(progress * 1.6 - .3); ctx.fillStyle = fill; ctx.fillRect(x, y, w, h); ctx.restore(); }
  if (stroke) line([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], { color: stroke, width, alpha, progress, dash });
}
/* a label that arrives: fades in and settles 6 units into place on Motion's spring */
function lab(s, x, y, t0, o = {}) {
  const a = settle(t0, o.visual || .28); if (a <= 0) return 0;
  return text(s, x, y + (o.rise === undefined ? 6 : o.rise) * (1 - a), { size: 16, ...o, alpha: (o.alpha === undefined ? 1 : o.alpha) * a });
}
function mlab(s, x, y, t0, o = {}) {
  const a = settle(t0, o.visual || .28); if (a <= 0) return 0;
  return math(s, x, y + (o.rise === undefined ? 6 : o.rise) * (1 - a), { size: 16, ...o, alpha: (o.alpha === undefined ? 1 : o.alpha) * a });
}
/* panel letter and a short subtitle in the body colour */
function sub(letter, x, y, words, a, o = {}) {
  if (a <= 0) return;
  panel(letter, x, y, { alpha: a });
  if (words) text(words, x + (o.gap || 36), y, { size: 16, color: C.body, alpha: a });
}
/* points of a quadratic Bezier from p0 to p2 bending through control p1 */
function bez(p0, p1, p2, n = 40) {
  const pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n, v = 1 - u;
    pts.push([v * v * p0[0] + 2 * v * u * p1[0] + u * u * p2[0], v * v * p0[1] + 2 * v * u * p1[1] + u * u * p2[1]]); }
  return pts;
}
/* a curved arrow along a polyline, the stealth tip at the end once the stroke arrives */
function carrow(pts, o = {}) {
  const { color = C.ink, width = 1.5, head = 10, progress = 1, alpha = 1, dash = null } = o;
  if (progress <= 0) return;
  let L = 0; const d = [];
  for (let i = 1; i < pts.length; i++) { d.push(Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])); L += d[d.length - 1]; }
  // stop the shaft short of the tip so the tip covers it
  let keep = L * progress - (progress >= 1 ? head * .55 : 0), out = [pts[0]];
  for (let i = 1; i < pts.length && keep > 0; i++) {
    const s = Math.min(1, keep / d[i - 1]);
    out.push([lerp(pts[i - 1][0], pts[i][0], s), lerp(pts[i - 1][1], pts[i][1], s)]); keep -= d[i - 1];
  }
  line(out, { color, width, alpha, dash });
  if (progress >= .98) {
    const q = pts[pts.length - 1], p = pts[pts.length - 2];
    const a = Math.atan2(q[1] - p[1], q[0] - p[0]);
    arrow(q[0] - Math.cos(a) * 2, q[1] - Math.sin(a) * 2, q[0], q[1], { color, width, head, alpha: alpha * clamp((progress - .98) * 50) });
  }
}
/* a colour for v through a LUT (engine's SEQ or DIVERGING), u in [0, 1] */
function lutc(lut, u) { const i = Math.round(clamp(u) * 255) * 3; return `rgb(${lut[i]},${lut[i + 1]},${lut[i + 2]})`; }
/* luminance of a LUT entry: text on it is white above ~0.55 darkness */
function lutDark(lut, u) { const i = Math.round(clamp(u) * 255) * 3; return (.2126 * lut[i] + .7152 * lut[i + 1] + .0722 * lut[i + 2]) / 255 < .5; }
/* a horizontal colour bar with ticks below and a label to its left */
function cbar(x, y, w, h, lut, lo, hi, ticks, label, a = 1, fmtv = v => nf(v, 1)) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;
  for (let i = 0; i < w; i++) { ctx.fillStyle = lutc(lut, i / (w - 1)); ctx.fillRect(x + i, y, 1.5, h); }
  ctx.restore();
  box(x, y, w, h, { width: 1, alpha: a });
  for (const v of ticks) {
    const xx = x + (v - lo) / (hi - lo) * w;
    line([[xx, y + h], [xx, y + h + 4]], { width: 1, alpha: a });
    text(fmtv(v), xx, y + h + 19, { size: 14, align: 'center', alpha: a });
  }
  if (label) math(label, x - 12, y + h - 1, { size: 15, align: 'right', alpha: a });
}
/* colour mixing between two #rrggbb */
function mix(c1, c2, s) {
  const a = _hex(c1), b = _hex(c2);
  return `rgb(${Math.round(lerp(a[0], b[0], s))},${Math.round(lerp(a[1], b[1], s))},${Math.round(lerp(a[2], b[2], s))})`;
}
/* a word in a box, as a token: serif 17, centred */
function token(s, cx, cy, o = {}) {
  const { w = 0, h = 34, size = 17, alpha = 1, stroke = C.ink, fill = '#fff', color = C.ink, width = 1.3, progress = 1 } = o;
  ctx.save(); ctx.font = font({ size }); const tw = ctx.measureText(s).width; ctx.restore();
  const bw = w || tw + 22;
  box(cx - bw / 2, cy - h / 2, bw, h, { fill, stroke, width, alpha, progress });
  if (progress > .3) text(s, cx, cy + size * .34, { size, align: 'center', color, alpha: alpha * clamp(progress * 1.5 - .3) });
  return bw;
}
"""


def build(name, title, aria, h, data, js, check_lines=None, width=672):
    """Write nf-<name>.html (LIB before the figure's script), its still, and
    tools/numfig/<module>.check.txt; returns the still's PNG path."""
    common.build_html(name, title, aria, 1000, h, data, LIB + "\n" + js)
    if check_lines is not None:
        module = name.replace("-", "_")
        text = "\n".join(check_lines) + "\n"
        with open(os.path.join(HERE, f"{module}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    return common.still(name, width=width)
