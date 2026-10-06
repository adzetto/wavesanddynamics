"""Figure 16: the three most common activation functions, ReLU, sigmoid and
tanh, on the same input axis z.

Each curve is the closed form sampled finely enough that the polyline's chord
error is under a hundredth of a drawing unit. One input z sweeps the axis
back and forth (a sine, whole periods), and each panel marks what its function
makes of that same z: ReLU passes a positive z unchanged and zeroes a
negative one, sigmoid squashes it into (0, 1), tanh into (-1, 1) about 0.

Run: python tools/numfig/mlb_activation.py [--look]
"""
import numpy as np

import mlb_common as mc

NAME = "activation"
Z = np.linspace(-4.2, 4.2, 337)                 # 0.025 apart


def relu(z):
    return np.maximum(0.0, z)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


FUN = {"relu": relu(Z), "sig": sigmoid(Z), "tanh": np.tanh(Z)}

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-activation: Figure 16, the three most common activation functions")
say("")
say("MODEL")
say("  ReLU(z) = max(0, z); sigmoid(z) = 1 / (1 + e^-z); tanh(z). Closed forms,")
say(f"  sampled at {Z.size} points on z in [-4.2, 4.2] (step {Z[1]-Z[0]:.4f}).")
say("")
say("CHECK 1: values the text states")
say(f"  sigmoid(0) = {sigmoid(0.0):.15f} (0.5), tanh(0) = {np.tanh(0.0):.1e} (centred at 0)")
say(f"  sigmoid range on the grid: [{FUN['sig'].min():.5f}, {FUN['sig'].max():.5f}] inside (0, 1)")
say(f"  tanh range on the grid:    [{FUN['tanh'].min():.5f}, {FUN['tanh'].max():.5f}] inside (-1, 1)")
say(f"  ReLU: max |ReLU(z) - z| for z >= 0 = {np.max(np.abs(FUN['relu'][Z >= 0] - Z[Z >= 0])):.1e},"
    f" max |ReLU(z)| for z < 0 = {np.max(np.abs(FUN['relu'][Z < 0])):.1e}")
say("")
say("CHECK 2: identities (closed form against closed form)")
zz = np.linspace(-8, 8, 10001)
say(f"  tanh(z) = 2 sigmoid(2z) - 1:   max error {np.max(np.abs(np.tanh(zz) - (2*sigmoid(2*zz) - 1))):.1e}")
say(f"  sigmoid(-z) = 1 - sigmoid(z):  max error {np.max(np.abs(sigmoid(-zz) - (1 - sigmoid(zz)))):.1e}")
say(f"  ReLU(z) = (z + |z|)/2:         max error {np.max(np.abs(relu(zz) - (zz + np.abs(zz))/2)):.1e}")
say("")
say("CHECK 3: slopes at 0 by central differences against 1/4 and 1")
h = 1e-5
ds = (sigmoid(h) - sigmoid(-h)) / (2*h)
dt = (np.tanh(h) - np.tanh(-h)) / (2*h)
say(f"  sigmoid'(0) = {ds:.10f} (0.25, error {abs(ds-.25):.1e}); tanh'(0) = {dt:.10f} (1, error {abs(dt-1):.1e})")
say("")
say("CHECK 4: sampling. The largest gap between the curve and its polyline,")
say("  in drawing units at the page's scale (plot 196 high):")
for k, f in (("sigmoid", sigmoid), ("tanh", np.tanh)):
    zm = (Z[:-1] + Z[1:]) / 2
    chord = (f(Z[:-1]) + f(Z[1:])) / 2
    ys = {"sigmoid": 196 / 1.2, "tanh": 196 / 2.4}[k]
    say(f"  {k:8s} {np.max(np.abs(f(zm) - chord)) * ys:.4f} units")
say("")
PER = 7.0
say(f"MOTION: z(t) = 3.6 sin(2 pi t / {PER:g} s) after an eased start; whole periods, seamless.")
mc.check(NAME, L)

DATA = {"z": Z, "relu": FUN["relu"], "sig": FUN["sig"], "tanh": FUN["tanh"], "per": PER}

JS = r"""
const D = DATA, ZA = 3.6, PER = D.per, T_RUN = .6, ZP = 1.2;
const clockZ = () => runClock(T_RUN, .8);
const zNow = () => ZA * Math.sin(2 * Math.PI * clockZ() / PER);
// the still: z = ZP on the first upswing
const POSTER_T = (() => { const c = PER * Math.asin(ZP / ZA) / (2 * Math.PI); return T_RUN + (c < .4 ? Math.sqrt(1.6 * c) : c + .4); })();

const sig = z => 1 / (1 + Math.exp(-z));
const PANELS = [
  { key: 'relu', name: 'ReLU', f: z => Math.max(0, z), formula: '\\rm{max}(0,\\,z)', out: '\\rm{ReLU}(z)',
    ylim: [-.55, 4.3], yticks: [0, 1, 2, 3, 4], yfmt: v => fmt(v), guides: [], dig: 2 },
  { key: 'sig', name: 'Sigmoid', f: sig, formula: '1\\,/\\,(1 + e^{-z})', out: '\\sigma(z)',
    ylim: [-.1, 1.1], yticks: [0, .5, 1], yfmt: v => v === .5 ? '0.5' : fmt(v), guides: [0, 1], dig: 3 },
  { key: 'tanh', name: 'Tanh', f: Math.tanh, formula: '\\rm{tanh}(z)', out: '\\rm{tanh}(z)',
    ylim: [-1.2, 1.2], yticks: [-1, -.5, 0, .5, 1], yfmt: v => fmt(v), guides: [-1, 1], dig: 3 },
];
const AX = { y: 62, w: 250, h: 196 }, X0 = [70, 399, 728];

function draw() {
  const z = zNow(), pa = lab(.55);
  PANELS.forEach((p, k) => {
    const x = X0[k], t0 = .05 * k;
    text(p.name, x, 40 + rise(lab(t0)), { size: 17, color: C.body, alpha: lab(t0) });
    math(p.formula, x + AX.w, 40 + rise(lab(t0 + .04)), { size: 17, color: C.body, align: 'right', alpha: lab(t0 + .04) });
    const A = axes({ x, y: AX.y, w: AX.w, h: AX.h, xlim: [-4.4, 4.4], ylim: p.ylim, xticks: [-4, -2, 0, 2, 4],
      yticks: p.yticks, yfmt: p.yfmt, grid: true, xlabel: 'z', tickSize: 16, progress: seg(t0, .35), ylabelGap: 40 });
    A.inside(() => {
      const zr = seg(.2 + t0, .3);
      line([[A.X(0), AX.y], [A.X(0), AX.y + AX.h]], { color: C.rule, width: 1.1, alpha: zr });
      line([[x, A.Y(0)], [x + AX.w, A.Y(0)]], { color: C.rule, width: 1.1, alpha: zr });
      for (const g of p.guides) line([[x, A.Y(g)], [x + AX.w, A.Y(g)]], { color: C.guide, width: 1, dash: [5, 4], progress: seg(.3 + t0, .35) });
      const Z = D.z, F = D[p.key], pts = new Array(Z.length);
      for (let i = 0; i < Z.length; i++) pts[i] = [A.X(Z[i]), A.Y(F[i])];
      line(pts, { color: C.blue, width: 2.4, progress: seg(.14 + .06 * k, .42) });
      // the one input z, and what this function makes of it
      if (pa > 0) {
        const y = p.f(z), px = A.X(z), py = A.Y(y);
        line([[px, AX.y + AX.h], [px, py]], { color: C.guide, width: 1, dash: [4, 3], alpha: pa });
        line([[x, py], [px, py]], { color: C.guide, width: 1, dash: [4, 3], alpha: pa });
        dot(px, py, 4.6, { color: '#fff', fill: C.accent, width: 1.4, alpha: pa });
      }
    });
    if (pa > 0) {                     // the readout, on white so the guides pass behind it
      const y = p.f(z), s1 = `z = ${num(z)}`, s2 = `${p.out} = ${num(y, p.dig)}`;
      const w = Math.max(math(s1, 0, -1e4, { size: 16, alpha: 0 }), math(s2, 0, -1e4, { size: 16, alpha: 0 }));
      rect(x + 6, AX.y + 29, w + 12, 49, { fill: '#fff', stroke: null, alpha: pa });
      math(s1, x + 12, AX.y + 47, { size: 16, color: C.body, alpha: pa });
      math(s2, x + 12, AX.y + 70, { size: 16, color: C.accent, alpha: pa });
    }
  });
  math('\\rm{one input}\\ z\\rm{, swept between \u22123.6 and 3.6, drives all three}', 18, H - 10, { size: 15, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 16: The three most common activation functions"
ARIA = ("Three plots on the same input axis z from minus 4 to 4: ReLU, zero for negative z and equal "
        "to z for positive z; sigmoid, an S curve from 0 to 1 through 0.5 at z = 0; and tanh, an S "
        "curve from minus 1 to 1 through 0. One input value sweeps back and forth and each plot marks "
        "its output for that same input.")

if __name__ == "__main__":
    mc.publish(NAME, TITLE, ARIA, 1000, 350, DATA, JS, look=(0.15, 0.35, 0.6, 0.9, 1.4, 3.0))
