"""The brochure's pulse echo diagram (brochure-shm-and-ndt-2-pages, image7),
redrawn from the model of the SHM article's Figure 3 (a).

His picture: an "Acoustic sensor (sends and receives waves)" on a "Steel
beam" with a "crack"; waves go down and come back; beside it the "Recorded
signal", "Amplitude" against "Time", with "Excitation", "Reflection" and
"Boundary". Here everything is the model's (shm_ndt.py, 2D elastic, steel):
a 12 mm, 2 MHz probe on a beam 40 mm deep, a crack 14 mm long 17 mm down
under the right half of the probe. The recorded signal is the model's
(the mean normal velocity under the probe); the pulses in the two lanes
travel at c_L and turn at the crack and the back wall where the model's
geometry puts them. Drawn at his picture's proportions (398 x 173).

Run: python tools/numfig/sd_pe.py [--look]
"""
import os
import sys

import common
import sd_check
from sd_check import poster_js
import sd_ndtlib as lib
import shm_ndt

NAME = "sd-pe"
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1000, 435                     # his picture: 398 x 173

JS = lib.PRELUDE + r"""
const A = D.a, AX0 = D.ax0, AY0 = D.ay0, AS = D.as, AW = A.win * AS, AH = A.d * AS;
const PCX = AX0 + A.px * AS, LD = PCX + A.lanes[0] * AS, LU = PCX + A.lanes[1] * AS;
const ay = z => AY0 + z * AS, ax = x => AX0 + x * AS;
const SIG = A.sig, NS = SIG.v.length;
const G = D.g;
const gX = v => G.x + (v - G.xlim[0]) / (G.xlim[1] - G.xlim[0]) * G.w;
const gY = v => G.y + G.h - (v - G.ylim[0]) / (G.ylim[1] - G.ylim[0]) * G.h;
const SW = 9;                                                 // a lane pulse's half width
const POSTER_T = D.poster;
function packet(x, zLead, zTrail, zLo, zHi, f, color, up) {  // one pulse in a lane, z in mm
  const a = Math.max(zLo, Math.min(zLead, zTrail)), b = Math.min(zHi, Math.max(zLead, zTrail));
  if (b <= a) return;
  const pts = [];
  for (let z = a; z <= b + 1e-9; z += .05) { const v = f(z); pts.push([x + SW * (v === null ? 0 : v), ay(z)]); }
  line(pts, { color, width: 1.9 });
  if (zLead >= zLo && zLead <= zHi) tip(x, ay(zLead) + (up ? -3 : 3), up ? -Math.PI / 2 : Math.PI / 2, color, 9);
}
function draw() {
  // the probe, and what he calls it
  const pp = settle(.1, .28), la = lab(.2), pw = A.pw * AS;
  ctx.save(); ctx.globalAlpha *= pp; ctx.fillStyle = C.navy; ctx.fillRect(PCX - pw / 2, AY0 - 17 + rise(pp), pw, 17); ctx.restore();
  text('Acoustic sensor', D.lx, D.ly + rise(la), { size: 19, align: 'right', alpha: la });
  text('(sends and receives waves)', D.lx, D.ly + 23 + rise(la), { size: 17, color: C.body, align: 'right', alpha: la });
  arrow(D.lx + 7, D.ly + 6, PCX - pw / 2 - 4, AY0 - 11, { width: 1.3, head: 8, alpha: la });
  // the beam
  piece(AX0, AY0, AW, AH, seg(.02, .35));
  text('Steel beam', AX0 + 10, AY0 + AH - 13, { size: 19, color: C.body, alpha: lab(.3) });
  const dA = lab(.4);                                          // its depth d, as the signal's 2d / c_L uses it
  arrow(AX0 - 20, AY0, AX0 - 20, AY0 + AH, { width: 1.1, head: 8, both: true, color: C.ink, alpha: dA });
  math('d', AX0 - 29, AY0 + AH / 2 + 6, { size: 20, align: 'right', alpha: dA });
  const [c0, c1] = A.crack, cp = seg(.2, .25);
  crackLine([ax(c0[0]), ay(c0[1])], [ax(c1[0]), ay(c1[1])], A.cb * AS, 1, cp);
  text('crack', ax(c1[0]) + 8, ay(c1[1]) - 5, { size: 19, color: C.accent, alpha: lab(.35) });
  // the lanes' guides
  const gp = seg(.25, .3), ga = .9;
  line([[LD, AY0 + 6], [LD, AY0 + AH - 6]], { color: C.guide, width: 1, dash: [3, 4], progress: gp, alpha: ga });
  line([[LU, AY0 + AH - 6], [LU, AY0 + 6]], { color: C.guide, width: 1, dash: [3, 4], progress: gp, alpha: ga });
  if (gp >= 1) { tip(LD, AY0 + AH - 3, Math.PI / 2, C.guide, 7, ga); tip(LU, AY0 + 3, -Math.PI / 2, C.guide, 7, ga); }
  // the shot: tau, us after the probe starts to send
  const s = t - A.t0, ph = s < 0 ? -1 : s % (MASTER / 2), tau = ph * US;
  const fade = ph < 0 ? 0 : 1 - clamp((ph - (MASTER / 2 - .35)) / .3);
  if (ph >= 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(AX0, AY0 - 1, AW, AH + 2); ctx.clip();
    const d = A.d, z1 = A.z1, z2 = A.z2;
    packet(LD, CL * tau, CL * (tau - D.dur), 0, d, z => burst(tau - z / CL), C.navy, false);
    const t1 = z1 / CL;
    if (tau > t1) packet(LU, z1 - CL * (tau - t1), z1 - CL * (tau - t1 - D.dur), 0, z2, z => burst(tau - t1 - (z1 - z) / CL), C.accent, true);
    const tw = d / CL;
    if (tau > tw) packet(LU, d - CL * (tau - tw), d - CL * (tau - tw - D.dur), 0, d, z => burst(tau - tw - (d - z) / CL), C.navy, true);
    ctx.restore();
  }
  // the recorded signal
  const ap = seg(.05, .4);
  text('Recorded signal', G.x + G.w / 2, G.y - 16 + rise(lab(.1)), { size: 20, align: 'center', alpha: lab(.1) });
  const g = axes({ ...G, xticks: [0, 4, 8, 12, 16], yticks: [-1, 0, 1], progress: ap, tickSize: 16, labelSize: 18,
                   xlabel: '\\rm{Time}\\ \\ t\\ (\\rm{µs})', ylabel: '\\rm{Amplitude}', ylabelGap: 40 });
  g.inside(() => line([[G.x, gY(0)], [G.x + G.w, gY(0)]], { color: C.rule, width: 1, alpha: ap }));
  /* the first shot records the signal as the echoes come back; after it the
     signal stays whole and each shot's cursor replays it */
  const first = t < A.t0 + MASTER / 2, keep = first ? fade : 1;
  if (ph >= 0 && keep > 0) {
    const tn = tau - A.tdur;                                  // the signal's own time (burst centre = 0)
    const nNow = Math.min(NS, Math.floor((tn - SIG.t0) / SIG.dt) + 1), n = first ? nNow : NS;
    if (n > 1) {
      const pts = []; for (let i = 0; i < n; i++) pts.push([gX(SIG.t0 + i * SIG.dt), gY(SIG.v[i])]);
      g.inside(() => {
        line(pts, { color: C.navy, width: 1.7, alpha: keep });
        const i0 = Math.max(0, Math.floor((A.cwin[0] - SIG.t0) / SIG.dt)), i1 = Math.min(n, Math.ceil((A.cwin[1] - SIG.t0) / SIG.dt));
        if (i1 > i0 + 1) line(pts.slice(i0, i1), { color: C.accent, width: 1.9, alpha: keep });
      });
    }
    if (nNow > 0 && tn < G.xlim[1]) {                         // the cursor, below the words
      const xc = gX(tn), v = SIG.v[Math.max(0, nNow - 1)];
      line([[xc, gY(.6)], [xc, gY(-.98)]], { color: C.ink, width: 1, alpha: .45 * fade });   // between the words and the dimension
      dot(xc, gY(v), 3.4, { color: C.navy, fill: C.navy, alpha: fade });
    }
    const seen = te => first ? fade * clamp((tn - te) / 2.5) : 1;   // a word arrives as the signal passes
    text('Excitation', gX(.8), gY(1.02), { size: 18, color: C.body, alpha: seen(0) });
    text('Reflection', gX(A.tc) - 22, gY(.8), { size: 18, color: C.accent, alpha: seen(A.tc) });   // above the cursor's reach
    text('Boundary', gX(A.tb) + 30, gY(.8), { size: 18, color: C.body, align: 'right', alpha: seen(A.tb) });
    const da = seen(A.tb) * .95, yd = gY(-1.1);
    if (da > 0) {
      arrow(gX(0), yd, gX(2 * A.d / CL), yd, { width: .9, head: 6, both: true, color: C.muted, alpha: da });
      const s_ = '2d/c_{\\rm{L}} = ' + (2 * A.d / CL).toFixed(1) + '\\,\\rm{µs}';
      const lw = math(s_, 0, -1e4, { size: 16, alpha: 0 });
      const xm = (gX(0) + gX(2 * A.d / CL)) / 2;
      ctx.save(); ctx.globalAlpha *= da; ctx.fillStyle = '#fff'; ctx.fillRect(xm - lw / 2 - 4, yd - 12, lw + 8, 18); ctx.restore();
      math(s_, xm, yd + 5, { size: 16, color: C.muted, align: 'center', alpha: da });
    }
  }
  const pa = lab(.8);
  row([['m', 'c_{\\rm{L}} = 5900\\,\\rm{m/s}'], ['t', ', beam 40 mm deep; probe 12 mm, 2 MHz, 3 cycles']], AX0 - 30, H - 14, { size: 15, color: C.muted, alpha: pa });
  math('\\rm{time slowed }10^{5}\\,\\times', G.x + G.w, D.ly, { size: 15, color: C.muted, align: 'right', alpha: pa });
}
boot();
"""


def main():
    data, _, L = lib.model()
    a = data["a"]
    As = 6.3
    ax0, ay0 = 150.0, 100.0
    # the printed frame: the second shot, 5 us in, the crack's echo rising and the pulse
    # past the crack going down, beside the whole signal the first shot recorded
    poster = round(a["t0"] + data["master"] / 2 + 5.0 / data["us"], 3)
    page = {"master": data["master"], "us": data["us"], "cl": data["cl"], "f0": data["f0"], "nc": data["nc"],
            "dur": data["dur"], "poster": poster, "a": a, "as": As, "ax0": ax0, "ay0": ay0,
            "lx": ax0 + a["px"] * As - a["pw"] * As / 2 - 26, "ly": 40.0,
            "g": {"x": 575, "y": 100, "w": 385, "h": 250, "xlim": [-1, 16], "ylim": [-1.25, 1.25]}}
    c = L["c"]
    say = []
    p = say.append
    say += lib.header("nf-sd-pe", "image7", ["Acoustic sensor (sends and receives waves)", "Steel beam", "crack",
                                             "Recorded signal", "Amplitude", "Excitation", "Reflection",
                                             "Boundary", "Time"], "pulse echo")
    p(f"  grid dx = {shm_ndt.DX} mm; a burst of 3 cycles at 2 MHz, Hann window (1.5 us)")
    p("")
    p("THE PICTURE")
    cr = shm_ndt.A_CR
    p(f"  beam {a['d']:g} mm deep (the page draws {a['win']:g} mm of the {shm_ndt.A_W:g} mm modelled), drawn {As:g} units/mm;")
    p(f"  probe {a['pw']:g} mm wide; crack: a void {2*cr['a']:g} x {2*cr['b']:g} mm, centre {cr['z']:g} mm down,"
      f" {cr['x']-shm_ndt.A_PX:+g} mm from the probe's axis, tilted {cr['tilt']:g} deg")
    p("  the recorded signal: the model's mean normal velocity under the probe, over its peak while it sends:")
    p(f"    Reflection (crack): envelope peak {a['ac']:.3f} at t = {a['tc']:.3f} us")
    p(f"    Boundary (back wall): envelope peak {a['ab']:.3f} at t = {a['tb']:.3f} us")
    p(f"  CHECK 1 (shm_ndt.check.txt): the scheme's P travel time, Richardson extrapolated, {L['rich']:.4f} us"
      f" against 2d/c_L = {2*a['d']/c:.4f} us ({(L['rich']/(2*a['d']/c)-1)*100:+.3f} %)")
    p(f"  CHECK 2: the back wall echo at {a['tb']:.4f} us against 2d/c_L = {2*a['d']/c:.4f} us"
      f" ({(a['tb']/(2*a['d']/c)-1)*100:+.2f} %, the 12 mm probe's own diffraction and the grid)")
    p("  echo times as the grid is refined (from shm_ndt): " + "; ".join(
        f"dx {dx:.3f} mm: {t1:.3f}, {t2:.3f} us" for dx, (t1, _), (t2, _) in L["conv"]))
    p(f"  the lanes: 1D kinematics at c_L, {a['lanes'][0]:g} and {a['lanes'][1]:g} mm right of the probe's axis, where the")
    p(f"    crack is {a['z1']:.2f} and {a['z2']:.2f} mm down: the lane's crack echo back at {2*a['z1']/c:.3f} us, the back wall's")
    p(f"    at {2*a['d']/c:.3f} us; the lanes show where the waves are, the recorded signal how strong")
    p("")
    p("TIME")
    p(f"  time slowed 1e5; a shot every {data['master']/2:g} s from t = {a['t0']:g} s; in the first shot the signal draws"
      " itself as the probe records it and each of his words arrives as the signal passes it; after it the")
    p("  signal stays whole and each shot's cursor replays it")
    p(f"  poster (printed frame) at t = {poster} s: the second shot 5 us in (the crack's echo rising in the right")
    p("  lane, the pulse past the crack going down in the left), the whole signal beside it")
    p(f"  drawn at his picture's proportions: {W} x {H} (his 398 x 173)")
    txt = "\n".join(say) + "\n"
    with open(os.path.join(HERE, "sd_pe.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Ultrasonic testing, pulse echo, an active technique"
    aria = ("An acoustic sensor on a steel beam sends a pulse down; its echoes from a crack and from the far "
            "face of the beam return, and the recorded signal, computed from an elastic wave model, shows "
            "the excitation, the reflection from the crack and the boundary as the signal is recorded.")
    common.build_html(NAME, title, aria, W, H, lib.plain(page), poster_js(JS, page["poster"]))
    print("still:", common.still(NAME))
    sd_check.append(os.path.join(HERE, "sd_pe.check.txt"),
                    sd_check.record(NAME, 2 * data['master'], 0.05, "--dense" in sys.argv,
                                    knock="the 2d/c_L value in the recorded signal, on a white box drawn after"
                                          " its dimension line (as nf-shm-ndt draws it)"))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 1.2, 1.6, 2.0, 2.4, 3.0]))


if __name__ == "__main__":
    main()
