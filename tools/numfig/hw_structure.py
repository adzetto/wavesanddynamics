"""HOW IT WORKS, step 1 (the brochure's image1, 82 x 82): "Structure(s)".

His icon: a building (a grid of windows) and a cable-stayed bridge on the
ground. Here, in the figures' line style: the building is a shear frame of
six storeys and three bays, the bridge a pylon, a deck, its end piers and
six stays, on TikZ's hatched ground.

The live part: the building sways in its first mode, once, in real time. The
model (hw_lib.building) is the uniform shear building whose first period is
the code's T1 = C_t H^(3/4) = 0.686 s (EN 1998-1, a 19.2 m concrete frame),
5 % damped, set moving in its first mode alone: every floor moves as
phi_j q(t), q = exp(-zeta w1 t) sin(wd t), and each storey's columns bend as
the shear frame's do between rigid floors (3 s^2 - 2 s^3). The sway stops at
the zero crossing after its envelope falls below a quarter pixel, where the
displacement is zero: nothing jumps.

Run: python tools/numfig/hw_structure.py  (writes the page, its still and
the check file).
"""
import numpy as np

import hw_lib as L

NAME, K, W, H = "structure", 0, 82, 82
U = 2.2                  # px, the roof's first peak as drawn
T_SW = 0.5               # s into the icon's own start: the frame is drawn, it starts to sway
STOP = 0.25              # px: the sway ends at the zero crossing after its envelope falls below this

JS = r"""
const D = DATA, PHI = D.phi, NS = PHI.length - 1;
const GY = 68, GX0 = 4, GX1 = 79;                  // the ground
const BX = [8, 15, 22, 29], FY = j => GY - 8 * j;  // the frame: column lines, floor j (0 the ground)
const PX = 55, TOP = 11, DY = 48, DX = [34, 76], PIERS = [36, 74];
const STAYS = [[23, 6], [18, 12], [13, 18]];       // anchor on the pylon, reach along the deck: nearest first
const T_SW = S0 + D.tsw, T_END = T_SW + D.tstop;
/* the roof's sway (px): the first mode's free vibration, in real time */
function roof() {
  const s = t - T_SW;
  return s <= 0 || s >= D.tstop ? 0 : D.U * Math.exp(-D.a * s) * Math.sin(D.wd * s) / D.qpk;
}
function ground() {
  const y = snap(GY, 1), p = at(0, .3);
  line([[GX0, y], [GX1, y]], {color: C.ink, width: px(1), progress: p});
  for (let x = GX0 + 3; x <= GX1; x += 4)            // TikZ's hatching: the ground holds what stands on it
    line([[x, y + .5], [x - 2.6, y + 3.1]], {color: C.guide, width: px(1), alpha: .8 * p});
}
function building(u) {
  const ys = []; for (let j = 0; j <= NS; j++) ys.push(snap(FY(j), j === NS ? 1.5 : 1));
  const off = j => u * PHI[j], xl = snap(BX[0], 1.5), xr = snap(BX[3], 1.5);
  // the floors, under the columns, from the first up
  for (let j = 1; j < NS; j++)
    line([[xl + off(j), ys[j]], [xr + off(j), ys[j]]], {color: C.blue, width: px(1), progress: at(.12 + .035 * j, .16)});
  // the columns, rising from the ground; in each storey the shear frame's cubic between rigid floors
  for (let c = 0; c < 4; c++) {
    const outer = c === 0 || c === 3, w = outer ? 1.5 : 1, x0 = snap(BX[c], w), pts = [[x0, ys[0]]];
    for (let j = 1; j <= NS; j++) for (let i = 1; i <= 6; i++) {
      const s = i / 6, h = s * s * (3 - 2 * s);
      pts.push([x0 + off(j - 1) + (off(j) - off(j - 1)) * h, lerp(ys[j - 1], ys[j], s)]);
    }
    line(pts, {color: outer ? C.navy : C.blue, width: px(w), progress: at(.03 + .025 * c, .3)});
  }
  line([[xl + off(NS), ys[NS]], [xr + off(NS), ys[NS]]], {color: C.navy, width: px(1.5), progress: at(.33, .14)});
}
function bridge() {
  const xp = snap(PX, 1.5), yd = snap(DY, 2), gy = snap(GY, 1);
  line([[xp, gy], [xp, TOP]], {color: C.navy, width: px(1.5), progress: at(.08, .3)});
  for (const x of PIERS) line([[snap(x, 1.5), gy], [snap(x, 1.5), yd]], {color: C.navy, width: px(1.5), progress: at(.14, .18)});
  // the deck, cantilevered out from the pylon both ways, as a cable-stayed deck is built
  for (const x of DX) line([[xp, yd], [x, yd]], {color: C.navy, width: px(2), progress: at(.2, .26)});
  STAYS.forEach(([ya, dx], i) => { for (const sg of [-1, 1])
    line([[xp, ya], [xp + sg * dx, yd]], {color: C.blue, width: px(1), progress: at(.28 + .05 * i, .16)}); });
}
/* the one accent: what moves, the roof's sway, a TikZ <-> over the roof */
function sway() {
  const a = lands(D.tsw - .06), y = snap(FY(NS) - 6, 1), x0 = BX[0] + 2, x1 = BX[3] - 2;
  if (a > 0) arrow(x0, y, x1, y, {color: C.accent, width: px(1), head: 3.6, both: true, alpha: a});
}
function draw() {
  ground();
  bridge();
  building(roof());
  sway();
  cue(T_END + .05);
}
const POSTER_T = S0 + D.tsw + D.tstop + .1;
boot();
"""


def build():
    b = L.building()
    tp, qpk = L.q_first_peak(b)
    env = U / qpk                                        # px, the envelope's start
    n = int(np.ceil(np.log(env / STOP) / (b["a"] * np.pi / b["wd"])))
    tstop = n * np.pi / b["wd"]
    phi = np.concatenate([[0.0], b["phi"]])
    data = dict(phi=phi, U=U, a=b["a"], wd=b["wd"], qpk=qpk, tsw=T_SW, tstop=tstop)
    title = "Structure(s)"
    aria = ("A six storey frame building beside a cable-stayed bridge. The building sways once in its "
            "first mode and comes to rest.")
    png = L.publish(NAME, K, title, aria, W, H, data, JS)
    print("still:", png)
    check(b, tp, qpk, n, tstop)
    return b


def check(b, tp, qpk, n, tstop):
    from scipy.integrate import solve_ivp

    w, w_cf, Phi, Phi_cf = b["w"], b["w_cf"], b["Phi"], b["Phi_cf"]
    e_w = np.max(np.abs(w - w_cf) / w_cf)
    sgn = np.sign(Phi[-1] / Phi_cf[-1])
    shapes = [Phi[:, r] * sgn[r] / np.abs(Phi[:, r]).max() for r in range(L.N)]
    shapes_cf = [Phi_cf[:, r] / np.abs(Phi_cf[:, r]).max() for r in range(L.N)]
    e_phi = max(np.abs(s - c).max() for s, c in zip(shapes, shapes_cf))
    # Rayleigh's quotient with the straight line shape: an upper bound on w1
    lin = np.arange(1, L.N + 1) / L.N
    w_r = np.sqrt(lin @ b["K"] @ lin / (lin @ b["M"] @ lin))
    # the whole frame integrated (classical damping, 5 % in every mode) from a velocity in
    # the first mode's shape, against phi q(t)
    Mn = Phi / np.sqrt(np.diag(Phi.T @ b["M"] @ Phi))
    Cm = b["M"] @ Mn @ np.diag(2 * L.ZETA * w) @ Mn.T @ b["M"]
    Minv = np.linalg.inv(b["M"])
    v0 = b["phi"] * b["wd"]                             # q'(0) = wd, roof 1
    rhs = lambda s, y: np.concatenate([y[L.N:], -Minv @ (b["K"] @ y[:L.N] + Cm @ y[L.N:])])
    ts = np.linspace(0, tstop, 2001)
    sol = solve_ivp(rhs, (0, tstop), np.concatenate([np.zeros(L.N), v0]), method="DOP853",
                    rtol=1e-11, atol=1e-13, t_eval=ts)
    q = np.exp(-b["a"] * ts) * np.sin(b["wd"] * ts)
    e_ode = np.abs(sol.y[:L.N] - np.outer(b["phi"], q)).max()
    # log decrement over one damped period
    delta = b["a"] * 2 * np.pi / b["wd"]

    say = []
    add = say.append
    add("HOW IT WORKS, step 1 (nf-hw-structure): Structure(s), the brochure's image1")
    add("generator: tools/numfig/hw_structure.py (model: hw_lib.building)")
    add("")
    add("MODEL")
    add(f"  a uniform shear building: {L.N} floors of m = {L.MASS / 1e3:.0f} t on {L.N} storeys of "
        f"h = {L.STOREY} m (H = {b['H']:.1f} m), fixed at the ground")
    add(f"  first period from EN 1998-1 4.3.3.2.2(3): T1 = C_t H^(3/4), C_t = {L.CT} (concrete frames)")
    add(f"    T1 = {b['T1']:.4f} s, f1 = {1 / b['T1']:.4f} Hz (the rule of thumb 0.1 N gives {0.1 * L.N:.1f} s)")
    add(f"  storey stiffness from the closed form below: k = {b['k'] / 1e6:.1f} MN/m")
    add(f"  damping: {L.ZETA:.0%} in every mode (EN 1998-1's reference value), classical")
    add("")
    add("MODES: numerical (scipy eigh of K, M) against the closed form of the uniform shear building,")
    add("  w_r = 2 sqrt(k/m) sin((2r - 1) pi / (2 (2N + 1))), phi_jr = sin((2r - 1) j pi / (2N + 1))")
    for r in range(3):
        add(f"  mode {r + 1}: f = {w[r] / 2 / np.pi:8.4f} Hz, closed form {w_cf[r] / 2 / np.pi:8.4f} Hz")
    add(f"  largest relative error of w_r: {e_w:.1e}; of the shapes (max 1): {e_phi:.1e}")
    add(f"  first mode, floors 1..{L.N}, roof 1: " + ", ".join(f"{v:.4f}" for v in b["phi"]))
    add(f"  Rayleigh's quotient with a straight line shape: w = {w_r:.4f} rad/s against w1 = {b['w1']:.4f}"
        f" ({(w_r - b['w1']) / b['w1']:+.2%}, an upper bound, as it must be)")
    add("")
    add("THE SWAY")
    add("  the first mode alone, set moving by a velocity in its shape: u_j(t) = phi_j q(t),")
    add(f"  q(t) = exp(-zeta w1 t) sin(wd t), zeta w1 = {b['a']:.5f} 1/s, wd = {b['wd']:.5f} rad/s")
    add(f"  the whole frame integrated (DOP853, rtol 1e-11) from that velocity, classical damping in all")
    add(f"  {L.N} modes: largest difference from phi q(t) over {tstop:.2f} s: {e_ode:.1e} (q peaks at {qpk:.4f})")
    add(f"  log decrement over a damped period: {delta:.5f} = 2 pi zeta / sqrt(1 - zeta^2)"
        f" = {2 * np.pi * L.ZETA / np.sqrt(1 - L.ZETA ** 2):.5f}")
    add("")
    add("DISPLAY")
    add(f"  real time: the period drawn is T1 = {b['T1']:.3f} s; the roof's first peak (t = {tp:.4f} s) is")
    add(f"  drawn at {U} px (the amplitude of a free vibration is arbitrary; the shape and the decay are not)")
    add(f"  each storey's columns: the shear frame's cubic between rigid floors, u_(j-1) + (u_j - u_(j-1))(3s^2 - 2s^3)")
    add(f"  the sway starts {T_SW} s into the icon (its frame drawn) and stops at its {n}th zero crossing,")
    add(f"  t = {tstop:.3f} s, where the envelope is below {STOP} px and the displacement is exactly zero")
    add(f"  timing: the icon is step 1, it starts as the flow is seen (0 s); drawn by 0.47 s")
    add("")
    lines, ok = L.overlap_lines(NAME, [0.2, 0.4, 0.8, 1.2, 2.0, 3.0])
    say += lines
    L.write_check(NAME, say)
    assert e_w < 1e-10 and e_phi < 1e-10 and e_ode < 1e-8 and ok


if __name__ == "__main__":
    build()
