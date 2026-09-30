"""HOW IT WORKS, step 4 (the brochure's image4, 74 x 74): "Decision making".

His icon: a shield with a gold check, and a report in front of it, three lines
of text and a gold seal. Here, in the figures' line style: the shield, the
report with its lines of findings, and the one accent, the check: the
decision, drawn last, after the report is written. There is no model to
draw here; the check file records the drawing and the overlap check.

Run: python tools/numfig/hw_decision.py  (writes the page, its still and the
check file).
"""
import hw_lib as L

NAME, K, W, H = "decision", 3, 74, 74

JS = r"""
/* the shield: a chevron top, straight sides, then two curves to its point */
function cubic(p0, p1, p2, p3, n = 10) {
  const out = []; for (let i = 1; i <= n; i++) { const s = i / n, u = 1 - s;
    out.push([u * u * u * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s * s * s * p3[0],
              u * u * u * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s * s * s * p3[1]]); }
  return out;
}
function shieldPath() {                                       // its straight sides on the pixel grid
  const L0 = snap(8, 1.5), R0 = snap(38, 1.5);
  return [[23, 13.5], [R0, 19], [R0, 36], ...cubic([R0, 36], [R0, 49], [31.5, 56], [23, 60]),
          ...cubic([23, 60], [14.5, 56], [L0, 49], [L0, 36]), [L0, 19], [23, 13.5]];
}
const REP = {x0: 37, x1: 64, y0: 16, y1: 60, f: 7};
const LINES = [[29, 17], [35, 17], [41, 17], [47, 11]];      // y, length: the report's findings
const TICK = [[15, 36.5], [21, 42.5], [31.5, 29]];
function fillPoly(pts, color, a) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (const q of pts.slice(1)) ctx.lineTo(q[0], q[1]); ctx.closePath(); ctx.fill(); ctx.restore();
}
function shield() {
  line(shieldPath(), {color: C.navy, width: px(1.5), progress: at(0, .34)});
}
function report() {
  const w = 1.5, x0 = snap(REP.x0, w), x1 = snap(REP.x1, w), y0 = snap(REP.y0, w), y1 = snap(REP.y1, w), xf = x1 - REP.f, yf = y0 + REP.f;
  const edge = [[x0, y0], [xf, y0], [x1, yf], [x1, y1], [x0, y1], [x0, y0]], p = at(.1, .3);
  fillPoly(edge, '#fff', clamp(p * 3));                        // the page in front of the shield
  line(edge, {color: C.navy, width: px(w), progress: p});
  line([[xf, y0], [xf, yf], [x1, yf]], {color: C.navy, width: px(1), progress: at(.34, .1)});
  LINES.forEach(([y, len], i) => { const yy = snap(y, 1);
    line([[x0 + 5, yy], [x0 + 5 + len, yy]], {color: C.blue, width: px(1), progress: at(.36 + .05 * i, .14)}); });
}
/* the one accent: the decision */
function decide() {
  line(TICK, {color: C.accent, width: px(2), progress: at(.5, .26)});
}
function draw() {
  shield();
  report();
  decide();
  cue(S0 + .8);
}
const POSTER_T = S0 + .85;
boot();
"""


def build():
    title = "Decision making"
    aria = ("A shield with a check mark stands behind a report with lines of findings. The check is drawn "
            "last, once the report is written.")
    png = L.publish(NAME, K, title, aria, W, H, {}, JS)
    print("still:", png)
    say = ["HOW IT WORKS, step 4 (nf-hw-decision): Decision making, the brochure's image4",
           "generator: tools/numfig/hw_decision.py",
           "",
           "THE DRAWING",
           "  no model: a shield (a chevron top, straight sides, two cubic curves to its point), a report",
           "  in front of it (a sheet with a folded corner, four lines of findings) and the one accent, the",
           "  check: the decision, drawn after the report is written",
           "  his seal (a second gold check on the report) is left out: the icon keeps one accent",
           "",
           "DISPLAY",
           "  the icon is step 4: it starts 1.05 s after the flow is seen; the shield draws in 0.34 s, the",
           "  report from 0.10 s, its lines from 0.36 s, the check from 0.50 s to 0.76 s of its own start",
           "  it is the last step: no arrow follows it",
           ""]
    lines, ok = L.overlap_lines(NAME, [0.3, 1.2, 1.4, 1.6, 1.8])
    L.write_check(NAME, say + lines)
    assert ok


if __name__ == "__main__":
    build()
