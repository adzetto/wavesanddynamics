"""The fun table, "Discrete states / modes" (image7): a particle in a box and a beam.

Model, left: an electron in a one dimensional infinite well 1 nm wide. Its
states are psi_n = sqrt(2/L) sin(n pi x / L) with energies E_n = n^2 h^2 /
(8 m L^2): discrete, and in the ratio 1 : 4 : 9. Each state is drawn at its
energy, its probability density |psi_n|^2 filled (it does not change in
time), and Re{psi_n e^{-i E_n t / hbar}} oscillating at E_n / h.
Right: a simply supported Euler-Bernoulli beam. Its modes are sin(n pi x /
L) too, with w_n = (n pi / L)^2 sqrt(EI / m): the same shapes, the same n^2
spectrum, drawn at the same heights. The mathematics is shared; what
oscillates is not (a probability amplitude on the left, a displacement on
the right).

Run: python tools/numfig/wt_quantum.py
"""
import numpy as np
from scipy.linalg import eigh, eigh_tridiagonal

import wt_lib

NAME = "quantum"

H_PL, HBAR, M_E, EV = 6.62607015e-34, 1.054571817e-34, 9.1093837015e-31, 1.602176634e-19
LW = 1.0e-9                                           # well width (m)
LB, EI, MB = 1.0, 210e9 * 0.02 ** 4 / 12, 7850 * 0.02 ** 2   # steel bar 20 x 20 mm, 1 m, pinned
F1_SHOW = 0.20                                        # both ground states shown at 0.2 Hz

E1 = H_PL ** 2 / (8 * M_E * LW ** 2)
w1b = (np.pi / LB) ** 2 * np.sqrt(EI / MB)

lines = []
say = lines.append
say("nf-wt-quantum: the fun table, 'Discrete states / modes' (image7)")
say("")
say("MODEL")
say(f"  left: electron in an infinite well, L = {LW*1e9:.0f} nm: E_n = n^2 h^2 / (8 m L^2), E_1 = {E1/EV:.4f} eV,"
    f" f_1 = E_1 / h = {E1/H_PL:.4e} Hz")
say(f"  right: steel bar 20 x 20 mm, {LB:.0f} m, pinned both ends: w_n = (n pi / L)^2 sqrt(EI/m),"
    f" f_1 = {w1b/(2*np.pi):.3f} Hz")
say("  both: eigenfunctions sin(n pi x / L), eigenvalues in the ratio n^2 (E_n and w_n).")
say("")
say("CHECK 1: the well by finite differences, -hbar^2/2m psi'' = E psi, psi = 0 at the walls")
for N in (100, 400, 1600):
    h = LW / N
    lam, vec = eigh_tridiagonal(np.full(N - 1, HBAR ** 2 / (M_E * h * h)), np.full(N - 2, -HBAR ** 2 / (2 * M_E * h * h)),
                                select="i", select_range=(0, 2))
    x = h * np.arange(1, N)
    shape_err = max(np.abs(np.abs(vec[:, n] / np.abs(vec[:, n]).max()) - np.abs(np.sin((n + 1) * np.pi * x / LW))).max()
                    for n in range(3))
    say(f"  {N:5d} intervals: E_n / E_1 = " + ", ".join(f"{v/lam[0]:.6f}" for v in lam)
        + f"; E_1 {lam[0]/E1-1:+.1e}; shapes off sin by {shape_err:.1e}")
say("")
say("CHECK 2: the beam by Hermite finite elements, pinned ends")
for ne in (8, 32):
    K, M = wt_lib.hermite_beam(ne, LB, EI, MB)
    keep = [i for i in range(K.shape[0]) if i not in (0, K.shape[0] - 2)]
    lam, vec = eigh(K[np.ix_(keep, keep)], M[np.ix_(keep, keep)])
    w = np.sqrt(lam[:3])
    say(f"  {ne:3d} elements: w_n / w_1 = " + ", ".join(f"{v/w[0]:.6f}" for v in w)
        + f"; w_1 {w[0]/w1b-1:+.1e}")
say("  both converge to 1, 4, 9: the same spectrum.")
say("")
say("DRAWING")
say(f"  levels at heights in proportion to n^2, the same on both sides; both ground states shown at"
    f" {F1_SHOW} Hz, the others at n^2 times that,")
say(f"  so one loop of {1/F1_SHOW:.0f} s holds whole periods of all three. Time slowed"
    f" {E1/H_PL/F1_SHOW:.1e} x (left) and {w1b/(2*np.pi)/F1_SHOW:.0f} x (right).")
wt_lib.write_check(NAME, lines)

DATA = {"f1": F1_SHOW}

JS = r"""
const POSTER_T = 0;                                      // t = 0 (and the still): every state at full swing
const Y0 = 360, KY = 30, A = 34, NP = 81;             // zero of energy, height per unit of n^2, amplitude
const LX0 = 64, LX1 = 432, RX0 = 574, RX1 = 942;
const yl = n => Y0 - KY * n * n;
function mode(x0, x1, y, n, amp, o) {
  const pts = [];
  for (let i = 0; i < NP; i++) { const u = i / (NP - 1); pts.push([lerp(x0, x1, u), y - amp * Math.sin(n * Math.PI * u)]); }
  line(pts, o);
}
function draw() {
  const tt = t;
  const aS = 1;
  // left: the well's walls, hatched outside
  for (const [x, dir] of [[LX0, 1], [LX1, -1]]) big(x, 214, 4.2, () => fixedEnd(0, 0, { h: 80, dir, alpha: aS }));
  line([[LX0, Y0], [LX1, Y0]], { color: C.ink, width: SW.thin, alpha: aS });
  // right: the three beams, pinned
  for (let n = 1; n <= 3; n++) {
    const y = yl(n), a = 1, w = 2 * Math.PI * DATA.f1 * n * n * tt, c = Math.cos(w);
    // matching heights: E_n on the left, w_n on the right
    line([[LX1 + 22, y], [RX0 - 22, y]], { color: C.guide, width: SW.guide, dash: DASH, alpha: a });
    // the state: |psi|^2 (still) under Re psi (moving)
    const dens = [[LX0, y]];
    for (let i = 0; i < NP; i++) { const u = i / (NP - 1); dens.push([lerp(LX0, LX1, u), y - A * .9 * Math.pow(Math.sin(n * Math.PI * u), 2)]); }
    dens.push([LX1, y]);
    line(dens, { color: C.mist, width: 1, fill: C.mist, close: true, alpha: a * .8 });
    line([[LX0, y], [LX1, y]], { color: C.ink, width: SW.thin, alpha: a });
    mode(LX0, LX1, y, n, A * c, { color: C.blue, width: SW.data - 1 });
    // the beam's mode at the same height
    line([[RX0, y], [RX1, y]], { color: C.ink, width: SW.thin, alpha: a });
    big(RX0, y, 2.4, () => pin(0, 0, { s: 9, alpha: a }));
    big(RX1, y, 2.4, () => pin(0, 0, { s: 9, alpha: a }));
    mode(RX0, RX1, y, n, A * c, { color: C.blue, width: SW.data - 1 });
  }
}
boot();
"""

TITLE = "Discrete states / modes"
ARIA = ("Left, the first three states of a particle in a box at energies in the ratio 1 to 4 to 9; "
        "right, the first three modes of a pinned beam at the same heights: the same sine shapes "
        "and the same spectrum.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
