"""HOW IT WORKS, step 3 (the brochure's image3, 92 x 76): "Data analysis".

His icon: a screen with a spiky waveform and three gold nodes joined by lines.
Here, in the figures' line style: a screen with a recorded signal on its zero
line, and the analysis in the one accent: three peaks of the record, found,
and the exponential decay fitted through them.

The record is step 1's building (hw_lib.building): the roof of the six storey
frame swaying freely in its first mode, q(t) = exp(-zeta w1 t) sin(wd t),
over four damped periods. The live part: the record draws itself left to
right; then its peaks arrive, and the decay through them, the logarithmic
decrement that gives the damping ratio back (the check below finds 5 %).

Run: python tools/numfig/hw_analysis.py  (writes the page, its still and the
check file).
"""
import numpy as np

import hw_lib as L

NAME, K, W, H = "analysis", 2, 92, 76
PERIODS = 4              # damped periods on the screen
NS = 221                 # samples of the record the page draws
NPK = 3                  # peaks the analysis marks

JS = r"""
const D = DATA, REC = D.rec, NR = REC.length, TR = D.T, PK = D.pk;
const SCR = {x0: 7, x1: 85, y0: 15, y1: 61, r: 3}, PL = {x0: 13, x1: 79, y: 38, a: 15};
const X = s => PL.x0 + (PL.x1 - PL.x0) * s / TR, Y = v => PL.y - PL.a * v;
/* the screen: a rectangle with round corners, drawn from the middle of its foot round and closed by hand */
function screen() {
  const w = 1.5, x0 = snap(SCR.x0, w), x1 = snap(SCR.x1, w), y0 = snap(SCR.y0, w), y1 = snap(SCR.y1, w), r = SCR.r, m = (x0 + x1) / 2;
  const pts = [[m, y1]], arc = (cx, cy, a0) => { for (let i = 0; i <= 6; i++) { const a = a0 - Math.PI / 2 * i / 6; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } };
  arc(x1 - r, y1 - r, Math.PI / 2); arc(x1 - r, y0 + r, 0); arc(x0 + r, y0 + r, -Math.PI / 2); arc(x0 + r, y1 - r, Math.PI);
  pts.push([m, y1]);
  line(pts, {color: C.navy, width: px(w), progress: at(0, .32)});
}
function record() {
  const y0 = snap(PL.y, 1);
  line([[PL.x0, y0], [PL.x1, y0]], {color: C.rule, width: px(1), alpha: at(.12, .2)});
  const pts = []; for (let i = 0; i < NR; i++) pts.push([X(TR * i / (NR - 1)), Y(REC[i])]);
  line(pts, {color: C.navy, width: px(1.1), progress: at(.15, .45)});
}
/* the one accent: the analysis. The decay fitted through the peaks, exp(-zeta w1 t),
   drawn from the first peak on, and the peaks themselves */
function analysis() {
  const pe = at(.74, .24);
  if (pe > 0) {
    const pts = []; for (let i = 0; i <= 48; i++) { const s = PK[0][0] + (TR - PK[0][0]) * i / 48; pts.push([X(s), Y(D.env * Math.exp(-D.a * s))]); }
    line(pts, {color: C.accent, width: px(1), progress: pe});
  }
  PK.forEach(([s, v], i) => { const l = lands(.6 + .07 * i, .24);
    if (l > 0) dot(X(s), Y(v), 1.9 * l, {color: '#fff', fill: C.accent, width: px(.8)}); });
}
function draw() {
  screen();
  record();
  analysis();
  cue(S0 + 1.0);
}
const POSTER_T = S0 + 1.05;
boot();
"""


def model():
    b = L.building()
    tp, qpk = L.q_first_peak(b)
    T = PERIODS * 2 * np.pi / b["wd"]
    ts = np.linspace(0, T, NS)
    rec = np.exp(-b["a"] * ts) * np.sin(b["wd"] * ts) / qpk          # the first peak 1
    tk = tp + np.arange(NPK) * 2 * np.pi / b["wd"]                    # its maxima, exactly
    pk = np.exp(-b["a"] * tk) * np.sin(b["wd"] * tk) / qpk
    # every maximum lies on c exp(-a t), c = sin(atan(wd / a)) = wd / w1: the decay through the peaks
    env = (b["wd"] / b["w1"]) / qpk
    return b, T, ts, rec, tk, pk, env, qpk


def build():
    b, T, ts, rec, tk, pk, env, qpk = model()
    data = dict(T=T, rec=rec, pk=np.stack([tk, pk], 1), env=env, a=b["a"])
    title = "Data analysis"
    aria = ("A screen shows a recorded vibration decaying. Three of its peaks are marked and a decaying "
            "curve is fitted through them.")
    png = L.publish(NAME, K, title, aria, W, H, data, JS)
    print("still:", png)
    check(b, T, ts, rec, tk, pk, env)


def peaks_of(ts, y):
    """Local maxima of a sampled record, each refined by a parabola through
    its three samples: (times, values)."""
    i = np.where((y[1:-1] > y[:-2]) & (y[1:-1] >= y[2:]))[0] + 1
    dt = ts[1] - ts[0]
    a, b_, c = y[i - 1], y[i], y[i + 1]
    d = 0.5 * (a - c) / (a - 2 * b_ + c)
    return ts[i] + d * dt, b_ - 0.25 * (a - c) * d


def check(b, T, ts, rec, tk, pk, env):
    # what the page holds (5 digits), analysed as a record would be
    rec_page = np.round(rec, 5)
    tq, vq = peaks_of(ts, rec_page)
    tq, vq = tq[:NPK], vq[:NPK]
    delta = np.log(vq[:-1] / vq[1:])                                   # logarithmic decrements
    zeta = delta / np.sqrt(4 * np.pi ** 2 + delta ** 2)
    Td = np.diff(tq)
    f1 = 1 / (Td.mean() * np.sqrt(1 - zeta.mean() ** 2))
    slope, icpt = np.polyfit(tq, np.log(vq), 1)                        # the fitted decay
    say = []
    add = say.append
    add("HOW IT WORKS, step 3 (nf-hw-analysis): Data analysis, the brochure's image3")
    add("generator: tools/numfig/hw_analysis.py (model: hw_lib.building, the building of step 1)")
    add("")
    add("THE RECORD")
    add(f"  the roof of step 1's frame in free vibration in its first mode: q(t) = exp(-zeta w1 t) sin(wd t),")
    add(f"  zeta = {L.ZETA}, f1 = {b['w1'] / 2 / np.pi:.4f} Hz, over {PERIODS} damped periods, T = {T:.4f} s,")
    add(f"  {NS} samples (dt = {ts[1] - ts[0]:.5f} s), scaled so its first peak is 1")
    add(f"  its maxima, exactly: t = " + ", ".join(f"{v:.4f}" for v in tk) + " s, q = "
        + ", ".join(f"{v:.4f}" for v in pk))
    add(f"  the decay through them: {env:.5f} exp(-{b['a']:.5f} t) (every maximum lies on (wd/w1) exp(-zeta w1 t))")
    add("")
    add("THE ANALYSIS, run on the record as the page holds it (5 digits)")
    add("  peaks: local maxima of the samples, each refined by a parabola through three samples:")
    add("    t = " + ", ".join(f"{v:.4f}" for v in tq) + " s (exact: " + ", ".join(f"{v:.4f}" for v in tk) + ")")
    add("  logarithmic decrement delta = ln(q_n / q_n+1): " + ", ".join(f"{v:.5f}" for v in delta)
        + f" (exact 2 pi zeta / sqrt(1 - zeta^2) = {2 * np.pi * L.ZETA / np.sqrt(1 - L.ZETA ** 2):.5f})")
    add("  damping ratio zeta = delta / sqrt(4 pi^2 + delta^2): " + ", ".join(f"{v:.5f}" for v in zeta)
        + f" (the model's {L.ZETA})")
    add(f"  first frequency from the peaks' spacing: {f1:.4f} Hz (the model's {b['w1'] / 2 / np.pi:.4f} Hz)")
    add(f"  the decay fitted through the peaks by least squares on ln q: rate {-slope:.5f} 1/s "
        f"(zeta w1 = {b['a']:.5f}), start {np.exp(icpt):.5f} (drawn: {env:.5f})")
    add("")
    add("DISPLAY")
    add("  the icon is step 3: it starts 0.70 s after the flow is seen; the screen draws in 0.32 s, the")
    add("  record draws itself left to right from 0.15 s to 0.60 s, the three peaks arrive (settle) from")
    add("  0.60 s and the fitted decay draws through them from 0.74 s to 0.98 s of its own start")
    add("")
    lines, ok = L.overlap_lines(NAME, [0.3, 0.8, 1.1, 1.4, 1.7])
    say += lines
    L.write_check(NAME, say)
    assert np.abs(zeta - L.ZETA).max() < 2e-4 and abs(f1 - b["w1"] / 2 / np.pi) < 2e-3 and ok


if __name__ == "__main__":
    build()
