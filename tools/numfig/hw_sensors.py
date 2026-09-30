"""HOW IT WORKS, step 2 (the brochure's image2, 72 x 72): "Sensors on structure(s)".

His icon: a sensor box with a gold dot on a post, three arcs above it, on a
base line. Here, in the figures' line style: the structure is a steel member
(C.steel fill, ink outline, as the figures draw a test piece), the sensor a
box on its post with the one accent, its sensing element, and the arcs are
the crests of the burst it sends.

The live part: the burst leaves the sensor once. Its three crests leave in
turn, one wavelength apart, the first sent the farthest out, and come to rest
where the icon keeps them. Each crest's strength is the far field of a point
source in the plane, |H0(kr)| (a cylindrical wave, falling as 1/sqrt(r)),
drawn through the figures' sequential scale (seq): the nearest crest navy,
the farther ones paler, as in his icon.

Run: python tools/numfig/hw_sensors.py  (writes the page, its still and the
check file).
"""
import numpy as np
from scipy.special import hankel1

import hw_lib as L

NAME, K, W, H = "sensors", 1, 72, 72
LAM = 6.0                        # px, the crests' spacing: one wavelength
R_OUT = 20.0                     # px, the first crest's radius when the icon comes to rest
R = [R_OUT, R_OUT - LAM, R_OUT - 2 * LAM]
SPAN = 50.0                      # degrees each side of the vertical

JS = r"""
const D = DATA, R = D.R, LAM = D.lam;
const PLATE = {x0: 11, x1: 61, y0: 55, y1: 60};      // the structure: a steel member
const PX = 36, BOX = {x0: 28, x1: 44, y0: 33, y1: 45}, SRC = [36, 30.5];
const TE = .34, TD = .55;                              // the burst: sent at, and the time it takes to come to rest
function member() {
  const p = at(0, .26), x0 = snap(PLATE.x0, 1), x1 = snap(PLATE.x1, 1), y0 = snap(PLATE.y0, 1), y1 = snap(PLATE.y1, 1);
  if (p > 0) { ctx.save(); ctx.globalAlpha *= p; ctx.fillStyle = C.steel; ctx.fillRect(x0, y0, x1 - x0, y1 - y0); ctx.restore(); }
  line([[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]], {color: C.ink, width: px(1), progress: p});   // closed by hand: closePath strokes off the grid
}
function sensor() {
  const xp = snap(PX, 1.5), bx0 = snap(BOX.x0, 1.5), bx1 = snap(BOX.x1, 1.5), by0 = snap(BOX.y0, 1.5), by1 = snap(BOX.y1, 1.5);
  line([[xp, snap(PLATE.y0, 1)], [xp, by1]], {color: C.navy, width: px(1.5), progress: at(.08, .18)});
  const p = at(.14, .24);
  if (p > 0) { ctx.save(); ctx.globalAlpha *= p; ctx.fillStyle = '#fff'; ctx.fillRect(bx0, by0, bx1 - bx0, by1 - by0); ctx.restore(); }
  line([[xp, by1], [bx1, by1], [bx1, by0], [bx0, by0], [bx0, by1], [xp, by1]], {color: C.navy, width: px(1.5), progress: p});
  // the one accent: the sensing element
  const s = lands(.3, .24);
  if (s > 0) dot((bx0 + bx1) / 2, (by0 + by1) / 2, 2.3 * s, {color: C.accent, fill: C.accent, width: px(.5)});
}
/* the burst: its crests leave one wavelength apart, the first the farthest, and
   come to rest; each as strong as a point source's far field at its radius */
function burst() {
  const p = seg(S0 + TE, TD, easeOut), lead = R[0] * p, a0 = -Math.PI / 2, sp = D.span * Math.PI / 180;
  for (let n = 0; n < 3; n++) {
    const r = lead - n * LAM;
    if (r <= 2.5) continue;
    const v = clamp(Math.sqrt(R[2] / r)), born = clamp((r - 2.5) / 3);   // 1/sqrt(r), the nearest crest at rest 1
    const pts = []; for (let i = 0; i <= 24; i++) { const a = a0 - sp + 2 * sp * i / 24; pts.push([SRC[0] + r * Math.cos(a), SRC[1] + r * Math.sin(a)]); }
    line(pts, {color: seq(v), width: px(1.5), alpha: born});
  }
}
function draw() {
  member();
  sensor();
  burst();
  cue(S0 + TE + TD + .05);
}
const POSTER_T = S0 + TE + TD + .1;
boot();
"""


def build():
    k = 2 * np.pi / LAM
    amp = np.sqrt(R[-1] / np.array(R))                    # the page's law, 1/sqrt(r), the nearest crest 1
    data = dict(R=R, lam=LAM, span=SPAN)
    title = "Sensors on structure(s)"
    aria = ("A sensor on a post stands on a steel member. It sends a burst: three arcs leave it one after "
            "another and come to rest above it.")
    png = L.publish(NAME, K, title, aria, W, H, data, JS)
    print("still:", png)
    check(k, amp)


def check(k, amp):
    kr = k * np.array(R)
    exact = np.abs(hankel1(0, kr))
    far = np.sqrt(2 / (np.pi * kr))
    say = []
    add = say.append
    add("HOW IT WORKS, step 2 (nf-hw-sensors): Sensors on structure(s), the brochure's image2")
    add("generator: tools/numfig/hw_sensors.py")
    add("")
    add("MODEL")
    add("  the sensor sends a burst; its crests are drawn as a point source's wavefronts in the plane:")
    add(f"  one wavelength apart, lambda = {LAM} px, the first sent the farthest out; at rest their radii are")
    add(f"  {', '.join(f'{r:g}' for r in R)} px, within +-{SPAN:g} degrees of the vertical")
    add("  strength of a crest: the far field of the 2D Green's function, |H0(kr)| ~ sqrt(2/(pi kr)), so")
    add("  1/sqrt(r), normalised to the nearest crest at rest and drawn through the figures' sequential")
    add("  scale seq(); on its way out a crest is drawn as strong as its radius gives (at most 1)")
    add("")
    add("CHECKS")
    add("  the far field against the exact |H0^(1)(kr)| (scipy hankel1) at the three radii at rest:")
    for r, a, e, f in zip(R, amp, exact, far):
        add(f"  r = {r:5.1f} px, kr = {k * r:6.3f}: |H0| = {e:.5f}, sqrt(2/(pi kr)) = {f:.5f}"
            f" ({(f - e) / e:+.3%}); drawn as seq({a:.4f}), exact ratio {e / exact[-1]:.4f}")
    add(f"  the 1/sqrt(r) law between the nearest and the farthest crest: {np.sqrt(R[2] / R[0]):.4f},"
        f" |H0| gives {exact[0] / exact[2]:.4f}")
    add(f"  spacing: {R[0] - R[1]:g} and {R[1] - R[2]:g} px, one wavelength each")
    add("")
    add("DISPLAY")
    add("  the icon is step 2: it starts 0.35 s after the flow is seen; the member, the post and the box")
    add("  are drawn by 0.26 s of its own start, the sensing element arrives (settle), and the burst leaves")
    add("  at 0.34 s: its lead crest runs out to its radius on an ease out over 0.55 s, the others one")
    add("  wavelength behind, all coming to rest together at 0.89 s")
    add("")
    lines, ok = L.overlap_lines(NAME, [0.2, 0.5, 0.8, 1.0, 1.2])
    say += lines
    L.write_check(NAME, say)
    assert ok


if __name__ == "__main__":
    build()
