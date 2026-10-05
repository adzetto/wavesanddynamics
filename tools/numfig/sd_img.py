"""The brochure's imaging diagram (brochure-shm-and-ndt-2-pages, image8),
redrawn from the model of the SHM article's Figure 3 (c).

His picture: "Scanning transducers" with an arrow along them, on a
"structure" with a "crack", waves reflecting from it, and an arrow to the
"Resulting Image", which shows the crack. Here (shm_ndt.py, 2D elastic,
steel): a 16 element, 2 MHz array on a 12 mm steel wall with a crack tilted
20 degrees; each element transmits in turn and all receive (full matrix
capture), and the total focusing method builds the image, transmitter by
transmitter. The fronts drawn are the geometric ones of the same model:
incident (with the crack's shadow), the crack's specular reflection and its
edge waves, the back wall's echo. Drawn at his picture's proportions
(401 x 125).

Run: python tools/numfig/sd_img.py [--look]
"""
import os
import sys

import common
import sd_check
from sd_check import poster_js
import sd_ndtlib as lib
import shm_ndt

NAME = "sd-img"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1000, 312                     # his picture: 401 x 125

JS = lib.PRELUDE + r"""
const Cc = D.c, CX0 = D.cx0, CY0 = D.cy0, CS = D.cs, CWd = Cc.w * CS, CHd = Cc.d * CS;
const IX0 = D.ix0, IY0 = CY0;
const cxp = x => CX0 + x * CS, czp = z => CY0 + z * CS;
const E1 = Cc.crack[0], E2 = Cc.crack[1];
const POSTER_T = D.poster;
function crosses(p0, p1, q0, q1) {
  const d = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  return d(p0, p1, q0) * d(p0, p1, q1) < 0 && d(q0, q1, p0) * d(q0, q1, p1) < 0;
}
function mirror(S, a, b) {                                     // S reflected in the line ab
  const ux = b[0] - a[0], uz = b[1] - a[1], L = ux * ux + uz * uz;
  const s = ((S[0] - a[0]) * ux + (S[1] - a[1]) * uz) / L, fx = a[0] + s * ux, fz = a[1] + s * uz;
  return [2 * fx - S[0], 2 * fz - S[1]];
}
const inWall = p => p[0] >= 0 && p[0] <= Cc.w && p[1] >= 0 && p[1] <= Cc.d;
let BOXES = [];                                                // his words in the wall: the fronts leave them room
const clear = p => { const X = cxp(p[0]), Y = czp(p[1]); return !BOXES.some(b => X > b[0] && X < b[2] && Y > b[1] && Y < b[3]); };
/* a front: points c + R (cos, sin) over the angles where keep(p) holds, as runs */
function front(cx, cz, R, keep, o) {
  if (R <= 0) return;
  const n = Math.max(48, Math.ceil(R * 16)); let run = [];
  const flush = () => { if (run.length > 1) line(run, o); run = []; };
  for (let k = 0; k <= n; k++) {
    const a = 2 * Math.PI * k / n, p = [cx + R * Math.cos(a), cz + R * Math.sin(a)];
    if (keep(p) && clear(p)) run.push([cxp(p[0]), czp(p[1])]); else flush();
  }
  flush();
}
const TILE = [];
function tiles() {
  const cv2 = document.createElement('canvas'); cv2.width = IMG.width; cv2.height = IMG.height;
  const g2 = cv2.getContext('2d'); g2.drawImage(IMG, 0, 0);
  const src = g2.getImageData(0, 0, IMG.width, IMG.height).data;
  for (let k = 0; k < Cc.xe.length; k++) {
    const r0 = Math.floor(k / Cc.cols) * Cc.th, c0 = (k % Cc.cols) * Cc.tw;
    const tc = document.createElement('canvas'); tc.width = Cc.tw; tc.height = Cc.th;
    const tg = tc.getContext('2d'), im = tg.createImageData(Cc.tw, Cc.th);
    for (let y = 0; y < Cc.th; y++) for (let x = 0; x < Cc.tw; x++) {
      const v = src[((r0 + y) * IMG.width + c0 + x) * 4], o = (y * Cc.tw + x) * 4;
      im.data[o] = SEQ[v * 3]; im.data[o + 1] = SEQ[v * 3 + 1]; im.data[o + 2] = SEQ[v * 3 + 2]; im.data[o + 3] = 255;
    }
    tg.putImageData(im, 0, 0); TILE.push(tc);
  }
}
/* the box a label's ink takes, left or right aligned at x on baseline y (drawing units), padded */
function inkBox(s, x, y, size, align) {
  const w = text(s, 0, -1e4, { size, alpha: 0 });
  const x0 = align === 'right' ? x - w : x;
  return [x0 - 5, y - size * .78, x0 + w + 5, y + size * .3];
}
function draw() {
  piece(CX0, CY0, CWd, CHd, seg(.02, .35));
  // his words in the wall, and the room the fronts leave them
  const sx = CX0 + 10, sy = CY0 + CHd - 12, kx = cxp(E2[0]) + 7, ky = czp(E2[1]) - 8;
  BOXES = [inkBox('structure', sx, sy, 23, 'left'), inkBox('crack', kx, ky, 23, 'left')];
  text('structure', sx, sy, { size: 23, color: C.body, alpha: lab(.3) });
  const ph = phase(), nF = Cc.xe.length;
  const k = t < Cc.t0 ? -1 : Math.floor((ph - Cc.t0) / Cc.dt);   // the firing under way
  const reset = 1 - clamp((ph - (MASTER - .35)) / .3);
  const fired = k >= 0 && k < nF, tau = fired ? (ph - Cc.t0 - k * Cc.dt) * US : 0;
  const S = fired ? [Cc.xe[k], 0] : null;
  if (fired) {                                                   // the waves of this firing, inside the wall
    ctx.save(); ctx.beginPath(); ctx.rect(CX0, CY0, CWd, CHd); ctx.clip();
    const R = CL * tau, a = clamp(Math.sqrt(2.5 / Math.max(R, .1)), .3, 1);
    const tail = 1 - clamp((tau - (Cc.dt * US - .6)) / .6);
    front(S[0], S[1], R, p => p[1] >= 0 && inWall(p) && !crosses(S, p, E1, E2), { color: C.blue, width: 1.7, alpha: a * tail });
    const Sb = [S[0], 2 * Cc.d];
    front(Sb[0], Sb[1], R, p => {
      if (!inWall(p) || p[1] >= Cc.d) return false;
      const s = (Cc.d - Sb[1]) / (p[1] - Sb[1]), Wp = [Sb[0] + s * (p[0] - Sb[0]), Cc.d];
      return !crosses(S, Wp, E1, E2) && !crosses(Wp, p, E1, E2);
    }, { color: C.sky, width: 1.3, alpha: .8 * a * tail });
    const Sm = mirror(S, E1, E2);
    front(Sm[0], Sm[1], R, p => inWall(p) && crosses(Sm, p, E1, E2), { color: C.accent, width: 1.8, dash: [6, 4], alpha: tail });
    for (const E of [E1, E2]) {
      const r = R - Math.hypot(S[0] - E[0], S[1] - E[1]);
      if (r > 0) front(E[0], E[1], r, inWall, { color: C.accent, width: 1.1, dash: [3, 3], alpha: .75 * clamp(Math.sqrt(1.2 / r), .35, 1) * tail });
    }
    ctx.restore();
  }
  crackLine([cxp(E1[0]), czp(E1[1])], [cxp(E2[0]), czp(E2[1])], Cc.cr.b * CS, 1, seg(.2, .25));
  text('crack', kx, ky, { size: 23, color: C.accent, alpha: lab(.35) });
  // the array: each element transmits in turn (light), all receive (crimson as the crack's echo arrives)
  const ap = settle(.16, .28), ew = Cc.ew * CS, pitch = (Cc.xe[1] - Cc.xe[0]) * CS, ah = 15;
  ctx.save(); ctx.globalAlpha *= ap;
  const ax0 = cxp(Cc.xe[0]) - pitch / 2, ax1 = cxp(Cc.xe[nF - 1]) + pitch / 2, ay0 = CY0 - ah + rise(ap);
  ctx.fillStyle = C.navy; ctx.fillRect(ax0, ay0, ax1 - ax0, ah);
  for (let j = 0; j < nF; j++) {
    const x = cxp(Cc.xe[j]);
    if (fired) {
      const hit = tau - Cc.arrive[k][j];                          // the crack's echo front arrives
      if (hit > 0) { ctx.save(); ctx.globalAlpha *= Math.exp(-hit / 1.5) * .9; ctx.fillStyle = C.accent; ctx.fillRect(x - ew / 2, ay0, ew, ah); ctx.restore(); }
    }
    if (j === k && fired) { ctx.save(); ctx.globalAlpha *= clamp(1 - (tau - D.dur) / 1.5, .45, 1); ctx.fillStyle = C.sky; ctx.fillRect(x - ew / 2, ay0, ew, ah); ctx.restore(); }
  }
  ctx.strokeStyle = '#fff'; ctx.lineWidth = .9;
  for (let j = 1; j < nF; j++) { const x = (cxp(Cc.xe[j - 1]) + cxp(Cc.xe[j])) / 2; ctx.beginPath(); ctx.moveTo(x, ay0); ctx.lineTo(x, ay0 + ah); ctx.stroke(); }
  ctx.restore();
  const sa = lab(.25), ya = CY0 - ah - 17;
  text('Scanning transducers', ax0, ya - 14 + rise(sa), { size: 26, alpha: sa });
  arrow(ax0, ya, ax1, ya, { width: 1.4, head: 9, alpha: sa });
  if (fired) tip(cxp(Cc.xe[k]), CY0 - ah - 1, Math.PI / 2, C.blue, 8, ap);
  // the image, transmitter by transmitter
  const ia = lab(.3), ip = seg(.15, .35), IW = CWd, IH = Cc.zmax * CS;
  text('Resulting Image', IX0 + IW / 2, IY0 - 15 + rise(ia), { size: 26, align: 'center', alpha: ia });
  arrow(CX0 + CWd + 14, CY0 + CHd / 2, IX0 - 14, CY0 + CHd / 2, { width: 3.2, head: 13, alpha: lab(.35) });
  const done = t < Cc.t0 ? 0 : Math.min(nF, Math.floor((ph - Cc.t0) / Cc.dt));   // firings completed
  if (TILE.length && done > 0 && reset > 0) {
    const tin = (ph - Cc.t0 - done * Cc.dt) / .15, cur = TILE[done - 1];
    ctx.save(); ctx.imageSmoothingEnabled = true; ctx.globalAlpha *= reset;
    if (done > 1 && tin < 1) { ctx.drawImage(TILE[done - 2], IX0, IY0, IW, IH); ctx.globalAlpha *= clamp(tin); }
    else if (done === 1 && tin < 1) ctx.globalAlpha *= clamp(tin);
    ctx.drawImage(cur, IX0, IY0, IW, IH); ctx.restore();
  }
  line([[IX0, IY0], [IX0 + IW, IY0], [IX0 + IW, IY0 + IH], [IX0, IY0 + IH], [IX0, IY0]], { width: 1.4, progress: ip });
  if (done > 0) {
    const ra = .9 * reset * clamp((ph - Cc.t0 - Cc.dt) / .3);
    line([[IX0 + E1[0] * CS, IY0 + E1[1] * CS], [IX0 + E2[0] * CS, IY0 + E2[1] * CS]], { color: C.accent, width: 1.1, dash: [3, 3], alpha: ra });
    text('back wall', IX0 + 10, IY0 + (Cc.d - 3.5) * CS, { size: 20, color: C.muted, alpha: ra });
  }
  const pa = lab(.9);
  text(`${nF} elements, pitch 1.5 mm, 2 MHz; total focusing method, 24 dB`, CX0, H - 11, { size: 16, color: C.muted, alpha: pa });
  text(`shown ${(1e6 / US).toLocaleString('en-US')} × slower`, IX0 + IW, 30, { size: 16, color: C.muted, align: 'right', alpha: pa });
}
const IMG = new Image();
IMG.src = D.c.img;
IMG.decode().then(tiles).catch(() => {}).finally(() => boot());
"""


def main():
    data, _, L = lib.model()
    c = data["c"]
    cs = 10.2
    # the printed frame: the last firing 2.2 us in, its fronts in the wall (the crack's echo on its
    # way back), beside the image of the fifteen firings before it
    nF = len(c["xe"])
    poster = round(c["t0"] + (nF - 1) * c["dt"] + 2.2 / data["us"], 3)
    page = {"master": data["master"], "us": data["us"], "cl": data["cl"], "f0": data["f0"], "nc": data["nc"],
            "dur": data["dur"], "poster": poster, "c": c, "cs": cs, "cx0": 56.0, "cy0": 112.0,
            "ix0": 56.0 + c["w"] * cs + 72}
    cl = L["c"]
    say = []
    p = say.append
    say += lib.header("nf-sd-img", "image8", ["Scanning transducers", "structure", "crack", "Resulting Image"],
                      "imaging")
    cr = shm_ndt.C_CR
    p("")
    p("THE PICTURE")
    p(f"  wall {c['w']:g} mm of {c['w'] + 2*shm_ndt.C_M:g} mm modelled, {c['d']:g} mm thick, drawn {cs:g} units/mm; crack: a void"
      f" {2*cr['a']:g} x {2*cr['b']:g} mm at ({cr['x']:g}, {cr['z']:g}) mm, tilted {cr['tilt']:g} deg")
    p(f"  array: {len(c['xe'])} elements, pitch {shm_ndt.C_P:g} mm, width {c['ew']:g} mm; full matrix capture,"
      f" {len(c['xe'])} runs of {shm_ndt.C_T:g} us")
    p(f"  CHECK 1 (shm_ndt.check.txt, CHECK 5): reciprocity of the scattered data, max|h_ij - h_ji| / max|h| ="
      f" {L['recip']:.1e}")
    p(f"  CHECK 2 (CHECK 6): the image's crack peak at ({L['pc'][0]:.2f}, {L['pc'][1]:.2f}) mm, {L['dist']:.2f} mm from the"
      f" crack's line; the back wall imaged at z = {L['zb']:.2f} mm (true {c['d']:g}), {L['lvl_bw']:+.1f} dB")
    p("  total focusing: I(x, z) = |sum_i sum_j H[h_ij](t_i + t_j)|; after the k-th firing the sum over transmitters")
    p("  1 ... k divided by all 16 (the image grows out of white), in dB of the complete image's peak, 24 dB range")
    p("  the fronts drawn: the incident circle c_L t about the transmitter, cut where the crack shadows it;")
    p("  the crack's specular front (the transmitter's mirror image in the crack's line), its edge waves,")
    p("  the back wall's echo; a front is not drawn through his words \"structure\" and \"crack\"")
    p("")
    p("TIME")
    p(f"  shown 100,000 times slower; a firing every {c['dt']:g} s from t = {c['t0']:g} s ({c['dt']*data['us']:.0f} us each, every echo"
      " back before the next firing); the loop is"
      f" {data['master']:g} s")
    p(f"  poster (printed frame) at t = {poster} s: the last firing 2.2 us in, its fronts in the wall, the image of")
    p(f"  the {nF - 1} firings before it (the sum over transmitters 1 ... {nF - 1}, over all {nF})")
    p(f"  drawn at his picture's proportions: {W} x {H} (his 401 x 125)")
    txt = "\n".join(say) + "\n"
    with open(os.path.join(HERE, "sd_img.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Ultrasonic testing, imaging, an active technique"
    aria = ("An array of scanning transducers on a steel structure fires one element after another; the waves "
            "reflect from a crack inside, and the resulting image, built from every firing by the total "
            "focusing method, shows the crack and the back wall.")
    common.build_html(NAME, title, aria, W, H, lib.plain(page), poster_js(JS, page["poster"]))
    print("still:", common.still(NAME))
    sd_check.append(os.path.join(HERE, "sd_img.check.txt"),
                    sd_check.record(NAME, 2 * data['master'], 0.05, "--dense" in sys.argv))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.2, 3.4, 5.0, 6.6, 7.0]))


if __name__ == "__main__":
    main()
