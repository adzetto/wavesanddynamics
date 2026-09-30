"""A smoke test of the engine: a simply supported beam's first mode, exact,
drawn as every figure draws. Not published (writes nf-demo-*, which no
document names); delete the files it writes when done."""
import numpy as np

import common

L, n = 1.0, 200
x = np.linspace(0, L, n)
data = {"x": x, "phi": np.sin(np.pi * x / L), "omega": np.pi ** 2}
JS = r"""
const POSTER_T = 3.2;
function draw() {
  const a = axes({x: 110, y: 40, w: 820, h: 300, xlim: [0, 1], ylim: [-1.2, 1.2],
                  xticks: [0, .25, .5, .75, 1], yticks: [-1, 0, 1], xlabel: 'x/L',
                  ylabel: 'w/w_{\\rm{max}}', progress: seg(0, 1.2), grid: true});
  const q = Math.cos(2 * Math.PI * .5 * Math.max(0, t - 2));
  a.inside(() => line(DATA.x.map((v, i) => [a.X(v), a.Y(DATA.phi[i] * q)]),
                      {color: C.blue, width: 2.4, progress: seg(1, 1)}));
  panel('a', 20, 30, {alpha: seg(.4, .6)});
  math('\\omega_1 = \\pi^2\\sqrt{EI/m}/L^2', 520, 420, {align: 'center', alpha: seg(2, .6)});
  pin(110, 460); pin(930, 460, {roller: true}); line([[110, 460], [930, 460]], {width: 2});
  dim(110, 930, 505, 'L');
  arrow(300, 560, 500, 560, {color: C.accent}); dot(600, 560, 5, {color: C.accent});
  const img = ctx.createLinearGradient(650, 0, 950, 0);
  for (let i = 0; i <= 10; i++) img.addColorStop(i / 10, diverging(i / 5 - 1));
  ctx.fillStyle = img; ctx.fillRect(650, 545, 300, 20);
}
boot();
"""
common.build_html("demo", "Figure 0: Engine smoke test", "A test.", 1000, 600, data, JS)
print(common.still("demo"))
