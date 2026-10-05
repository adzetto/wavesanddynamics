"""The brochure's acoustic emission diagram (brochure-shm-and-ndt-2-pages,
image6), redrawn from the model of the SHM article's Figure 3 (b).

His picture: "Acoustic Emission (sensor is only listening)" over a steel
beam with a sensor on top, a crack rising from the underside, and waves
spreading from it; "Steel beam". Here the crack grows in four steps along
his path; each step sends out a P wave front, radius c_L t, which the
sensor hears r / c_L later (shm_ndt.py: the arrival checked against the 2D
elastic model with a moment source at the tip). Drawn at his picture's
proportions (691 x 219 in the brochure).

Run: python tools/numfig/sd_ae.py [--look]
"""
import os
import sys

import common
import sd_check
from sd_check import poster_js
import sd_ndtlib as lib

NAME = "sd-ae"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1000, 317                     # his picture: 691 x 219

JS = lib.PRELUDE + r"""
const B = D.b, BS = D.bs, BX0 = D.bx0, BY0 = D.by0, BW = B.w * BS, BD = B.d * BS;
const bx = x => BX0 + x * BS, by = z => BY0 + z * BS;
const POSTER_T = D.poster;
const NEAR = 9;                                               // mm: a front this close to the sensor is drawn arriving
/* a front: points c + R (cos, sin) (mm) where keep(p) holds, drawn as runs */
function front(cx, cz, R, keep, o) {
  if (R <= 0) return;
  const n = Math.max(48, Math.ceil(R * 12)); let run = [];
  const flush = () => { if (run.length > 1) line(run, o); run = []; };
  for (let k = 0; k <= n; k++) {
    const a = 2 * Math.PI * k / n, p = [cx + R * Math.cos(a), cz + R * Math.sin(a)];
    if (keep(p)) run.push([bx(p[0]), by(p[1])]); else flush();
  }
  flush();
}
function draw() {
  const la = lab(.04);
  text('Acoustic Emission (sensor is only listening)', D.tx, D.ty + rise(la), { size: 30, alpha: la });
  piece(BX0, BY0, BW, BD, seg(.04, .35), { cut: false });
  // his label, and the room the fronts leave it
  const sb = lab(.3), sw = text('Steel beam', 0, -1e4, { size: 24, alpha: 0 });
  const lx1 = BX0 + BW - 14, ly = BY0 + BD - 14, box = [lx1 - sw - 5, ly - 23, lx1 + 5, ly + 8];
  text('Steel beam', lx1, ly, { size: 24, color: C.body, align: 'right', alpha: sb });
  const inBox = p => { const X = bx(p[0]), Y = by(p[1]); return X > box[0] && X < box[2] && Y > box[1] && Y < box[3]; };
  const ph = phase(), P = B.crack.map(p => [bx(p[0]), by(p[1])]);
  const reset = 1 - clamp((ph - (MASTER - .35)) / .3);
  // the crack: its first stretch, then one step at each event
  line([P[0], P[1]], { color: C.accent, width: 3, progress: seg(.2, .25) });
  const grown = [P[1]];
  B.events.forEach((te, k) => {
    if (t < te || ph < te) return;
    const g = seg(te + (t - ph), .08);
    grown.push([lerp(P[k + 1][0], P[k + 2][0], g), lerp(P[k + 1][1], P[k + 2][1], g)]);
  });
  if (grown.length > 1) line(grown, { color: C.accent, width: 3, alpha: reset });
  // the P fronts, radius c_L tau from each new tip, inside the beam; as a front comes within
  // 9 mm of the sensor a short arrow rides it on the line from the step to the sensor, pointing in
  const SX = B.sensor[0];
  B.events.forEach((te, k) => {
    const tau = (ph - te) * US;
    if (tau <= 0 || t < te) return;
    const r = CL * tau;                                        // mm
    if (r > 160) return;
    const a = clamp(Math.sqrt(8 / r), .3, 1) * reset;         // 2D spreading, 1 / sqrt r
    const T = B.crack[k + 2], inBeam = p => p[0] > 0 && p[0] < B.w && p[1] > 0 && p[1] < B.d && !inBox(p);
    front(T[0], T[1], r, inBeam, { color: C.blue, width: 1.8, alpha: a });
    const dS = Math.hypot(T[0] - SX, T[1]);
    const arr = clamp((r - (dS - NEAR)) / 3) * (1 - clamp((r - dS - 1) / 4)) * reset;
    if (arr <= 0) return;
    const ux = (SX - T[0]) / dS, uz = -T[1] / dS, qx = T[0] + r * ux, qz = T[1] + r * uz;
    if (qz > .4) arrow(bx(qx - 5 * ux), by(qz - 5 * uz), bx(qx), by(qz), { color: C.navy, width: 1.8, head: 11, alpha: arr });
  });
  // the sensor: it only listens, and lights up as each front reaches it
  const sp = settle(.15, .28), sx = bx(SX), sw_ = B.sensor[1] * BS, sh = 18;
  ctx.save(); ctx.globalAlpha *= sp; ctx.fillStyle = C.navy; ctx.fillRect(sx - sw_ / 2, BY0 - sh + rise(sp), sw_, sh); ctx.restore();
  let heard = 0;
  B.events.forEach((te, k) => { const th = te + B.hits[k] / US; if (t >= th && ph >= th) heard = Math.max(heard, Math.exp(-(ph - th) / .5)); });
  if (heard > .01) { ctx.save(); ctx.globalAlpha *= heard * reset; ctx.fillStyle = C.sky; ctx.fillRect(sx - sw_ / 2, BY0 - sh, sw_, sh); ctx.restore(); }
  const pa = lab(.85);
  row([['t', 'P wave fronts, radius '], ['m', 'c_{\\rm{L}}\\,t'], ['t', ', from each step of the crack; steel, '],
       ['m', 'c_{\\rm{L}} = 5900\\,\\rm{m/s}']], BX0, H - 11, { size: 16, color: C.muted, alpha: pa });
  text(`shown ${(1e6 / US).toLocaleString('en-US')} × slower`, BX0 + BW, D.ty - 6, { size: 16, color: C.muted, align: 'right', alpha: pa });
}
boot();
"""


def main():
    data, _, L = lib.model()
    b = data["b"]
    bs = 6.5                         # the beam ends short of the page's pause and restart buttons
    page = {"master": data["master"], "us": data["us"], "cl": data["cl"], "f0": data["f0"], "nc": data["nc"],
            "dur": data["dur"], "poster": data["poster"], "b": b, "bs": bs, "bx0": 100.0, "by0": 88.0,
            "tx": 100.0, "ty": 38.0}
    c = L["c"]
    say = []
    p = say.append
    say += lib.header("nf-sd-ae", "image6", ["Acoustic Emission (sensor is only listening)", "Steel beam"],
                      "acoustic emission")
    p("")
    p("THE PICTURE")
    p(f"  beam {b['w']:g} x {b['d']:g} mm (drawn {bs:g} units/mm), his crack path from the underside:")
    p("    " + ", ".join(f"({x:g}, {z:g})" for x, z in b["crack"]) + " mm")
    p(f"  sensor {b['sensor'][1]:g} mm wide on top at x = {b['sensor'][0]:g} mm")
    p("  the crack grows in four steps; each step sends a P wave front from the new tip, radius c_L t,")
    p("  clipped to the beam (the direct fronts; the faces' reflections are not drawn), its stroke fading")
    p("  as 1/sqrt(r) (2D spreading); a front is not drawn through his words \"Steel beam\"")
    for k in range(4):
        tip = b["crack"][k + 2]
        p(f"    step {k+1} at t = {b['events'][k]:g} s: tip ({tip[0]:.1f}, {tip[1]:.1f}) mm, nearest point of the sensor"
          f" {b['hits'][k]*c:.2f} mm away: heard {b['hits'][k]:.3f} us later ({b['hits'][k]/data['us']*1e3:.0f} ms on the page)")
    p("  the fronts travel at c_L: CHECK 1 (shm_ndt.check.txt, CHECK 1), the scheme's own P travel time, an")
    p(f"    80 mm probe's back wall echo through 40 mm, Richardson extrapolated: {L['rich']:.4f} us against"
      f" 2d/c_L = {80 / c:.4f} us ({(L['rich'] / (80 / c) - 1) * 100:+.3f} %)")
    p("  CHECK 2 (shm_ndt.check.txt, CHECK 4): the model with the crack as a 0.3 mm void along the whole path")
    p(f"    and a moment source just past the tip: the sensor's signal first exceeds 2 % of its peak at"
      f" {L['first']:.3f} us;")
    p(f"    the P front's geometric arrival at the sensor's nearest point, {L['rmin']:.3f} mm away, is"
      f" {L['rmin']/c:.3f} us ({L['first']-L['rmin']/c:+.3f} us: the source pulse's rise and the threshold)")
    p("")
    p("TIME")
    p(f"  shown 100,000 times slower (10 us of the model a second); the loop is {data['master']:g} s, growth steps at"
      f" t = " + ", ".join(f"{v:g}" for v in b["events"]) + " s")
    p(f"  poster (printed frame) at t = {data['poster']} s: the fourth step heard, its front arriving at the sensor,")
    p("  the crack grown")
    p("  the sensor only listens: it lights up (sky) as a front reaches it; within 9 mm of it a short arrow rides")
    p("  the front on the line from the step to the sensor, pointing in; nothing leaves the sensor")
    p(f"  drawn at his picture's proportions: {W} x {H} (his 691 x 219)")
    txt = "\n".join(say) + "\n"
    with open(os.path.join(HERE, "sd_ae.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Acoustic emission, a passive technique"
    aria = ("A crack grows in steps from the underside of a steel beam; each step sends out a wave front that "
            "spreads through the beam, and the sensor on top, which only listens, lights up as each front "
            "reaches it.")
    common.build_html(NAME, title, aria, W, H, lib.plain(page), poster_js(JS, page["poster"]))
    print("still:", common.still(NAME))
    sd_check.append(os.path.join(HERE, "sd_ae.check.txt"),
                    sd_check.record(NAME, 2 * data['master'], 0.05, "--dense" in sys.argv))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.0, 3.0, 4.6, 6.0, 7.0]))


if __name__ == "__main__":
    main()
