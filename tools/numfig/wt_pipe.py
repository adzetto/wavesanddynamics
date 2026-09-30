"""The fun table, "Pressure-wave reflection" (image4): a pulse finds a leak.

Model: linear water hammer in a long steel water main. A transient
generator at x = 0 sends a pressure pulse (a 40 ms Hann pulse) both ways; a
leak (a 50 mm orifice at 5 bar, linearised) at x_L sends back an echo of
amplitude R = -Z0 Y / (2 + Z0 Y) and passes T = 1 + R on. Exact d'Alembert
solution; the pressure sensor at the generator records the pulse and, at
2 x_L / a, the echo, whose time locates the leak.

Run: python tools/numfig/wt_pipe.py
"""
import numpy as np

import wt_lib

NAME = "pipe"

D, E_WALL, E_S = 0.300, 0.008, 210e9          # bore (m), wall (m), steel (Pa)
K_W, RHO = 2.19e9, 998.0                      # water bulk modulus (Pa), density
A_PIPE = np.pi * D ** 2 / 4
A_WAVE = np.sqrt(K_W / RHO / (1 + K_W * D / (E_S * E_WALL)))     # Korteweg (anchored, c1 = 1)
Z0 = RHO * A_WAVE / A_PIPE                     # Pa s / m^3
P0, D_HOLE, CD = 5e5, 0.050, 0.61             # line pressure, leak orifice, discharge coefficient
Q_LEAK = CD * np.pi * D_HOLE ** 2 / 4 * np.sqrt(2 * P0 / RHO)
Y = Q_LEAK / (2 * P0)                          # d Q / d p of the orifice
R = -Z0 * Y / (2 + Z0 * Y)
T = 1 + R
X_LEAK = 250.0                                 # m from the generator
TAU = 0.040                                    # pulse length (s)
X_VIEW = (-20.0, 380.0)                        # the pipe drawn (m)
PERIOD = 0.70                                  # s, one pulse a loop
SLOW = 8.0

hann = lambda s: np.where((s > 0) & (s < TAU), np.sin(np.pi * np.clip(s, 0, TAU) / TAU) ** 2, 0.0)


def pressure(x, t):
    """Exact p / p_pulse: the pulse both ways from x = 0, the leak's echo and
    the transmitted pulse (infinite pipe either side of the view)."""
    x = np.asarray(x, float)
    p = np.where(x < X_LEAK, hann(t - np.abs(x) / A_WAVE), 0.0)
    p = p + np.where(x < X_LEAK, R * hann(t - (2 * X_LEAK - x) / A_WAVE), 0.0)
    p = p + np.where(x >= X_LEAK, T * hann(t - x / A_WAVE), 0.0)
    return p


lines = []
say = lines.append
say("nf-wt-pipe: the fun table, 'Pressure-wave reflection' (image4)")
say("")
say("MODEL")
say(f"  steel water main, bore {D*1e3:.0f} mm, wall {E_WALL*1e3:.0f} mm; water K = {K_W/1e9} GPa, rho = {RHO:.0f} kg/m^3.")
say(f"  Korteweg wave speed a = sqrt(K/rho / (1 + K D / (E e))) = {A_WAVE:.1f} m/s;"
    f" Z0 = rho a / A = {Z0:.4e} Pa s/m^3.")
say(f"  leak: {D_HOLE*1e3:.0f} mm orifice, Cd = {CD}, at {P0/1e5:.0f} bar: Q = {Q_LEAK*1e3:.1f} L/s;"
    f" linearised dQ/dp = Q / 2p = {Y:.3e} m^3/(s Pa).")
say(f"  at the leak: R = -Z0 Y / (2 + Z0 Y) = {R:.4f}, T = 1 + R = {T:.4f}; leak {X_LEAK:.0f} m from the generator.")
say(f"  pulse: Hann, {TAU*1e3:.0f} ms ({A_WAVE*TAU:.0f} m long); echo at the sensor after 2 x_L / a = {2*X_LEAK/A_WAVE*1e3:.1f} ms.")
say("")
say("CHECK 1: energy at the leak, incident = reflected + transmitted + lost through the orifice")
say(f"  1 = R^2 + T^2 + Z0 Y T^2: {R**2 + T**2 + Z0*Y*T**2:.12f}")
say("")
say("CHECK 2: an independent finite difference run of the water hammer equations")
say("  (p_t = -(rho a^2 / A) q_x, q_t = -(A / rho) p_x on a staggered grid, the orifice as a")
say("  sink Y p at the leak's node, open boundaries by characteristics), against the closed form")
for nx in (2000, 8000):
    xa, xb = -300.0, 800.0
    dx = (xb - xa) / nx
    dt = 0.5 * dx / A_WAVE
    xp = xa + dx * (np.arange(nx) + 0.5)                 # pressure nodes
    p = np.zeros(nx); q = np.zeros(nx + 1)
    il = int(np.argmin(np.abs(xp - X_LEAK)))
    i0 = int(np.argmin(np.abs(xp - 0.0)))
    kp = RHO * A_WAVE ** 2 / A_PIPE
    kq = A_PIPE / RHO
    rec, tt = [], []
    nt = int(0.62 / dt)
    for n in range(nt):
        t = n * dt
        # source: an injected flow at x = 0 making a pulse of p = hann on each side: q_in = 2 hann / Z0
        src = np.zeros(nx); src[i0] = 2 * hann(t + dt / 2) / Z0 / dx
        q[1:-1] -= dt * kq * (p[1:] - p[:-1]) / dx
        q[0] = -p[0] / Z0; q[-1] = p[-1] / Z0                  # outgoing only at both ends
        sink = np.zeros(nx); sink[il] = Y * p[il] / dx
        p -= dt * kp * ((q[1:] - q[:-1]) / dx + sink - src)
        rec.append(p[i0]); tt.append(t + dt)
    rec, tt = np.array(rec), np.array(tt)
    t_echo = 2 * X_LEAK / A_WAVE
    win = tt > t_echo - 0.01
    k = np.argmin(np.where(win, rec, 1e9))
    peak_t, peak = tt[k], rec[k]
    exact = R * 1.0
    say(f"  dx = {dx:.3f} m: echo peak {peak:+.4f} at {peak_t*1e3:.2f} ms; closed form {exact:+.4f} at"
        f" {(t_echo + TAU/2)*1e3:.2f} ms (error {peak/exact-1:+.1e}, {(peak_t-t_echo-TAU/2)*1e3:+.2f} ms)")
say("  the grid converges on R and on 2 x_L / a: the timing that locates a leak.")
say("")
say("CHECK 3: the leak located from the finest run's echo alone: x_L = a (t_peak - tau/2) / 2")
x_est = A_WAVE * (peak_t - TAU / 2) / 2
say(f"  t_peak = {peak_t*1e3:.3f} ms  ->  x_L = {x_est:.2f} m against {X_LEAK:.0f} m ({x_est-X_LEAK:+.3f} m)")
say("")
say("DRAWING")
say(f"  pipe from {X_VIEW[0]:.0f} m to {X_VIEW[1]:.0f} m = 1000 units; bore and wall drawn to no scale")
say(f"  (a {D*1e3:.0f} mm pipe drawn 100 units: the cross direction is not to scale).")
say("  the field: p / p_pulse through the diverging palette over +-0.5 (the pulse saturates, the echo")
say("  shows), uniform across the bore (plane waves);")
say("  under the pipe the sensor's record, its time axis drawn as a t / 2 so each echo sits under")
say("  the place it comes from.")
say(f"  time slowed {SLOW:.0f} x: one pulse every {PERIOD*1e3:.0f} ms, {PERIOD*SLOW:.1f} s on screen.")
wt_lib.write_check(NAME, lines)

DATA = {"a": A_WAVE, "R": R, "T": T, "xl": X_LEAK, "tau": TAU, "x0": X_VIEW[0], "x1": X_VIEW[1],
        "P": PERIOD, "slow": SLOW}

JS = r"""
const X0 = DATA.x0, X1 = DATA.x1, SX = W / (X1 - X0), XC = x => (x - X0) * SX;
const Y1 = 64, Y2 = 164, WALL = 14;                     // bore from Y1 to Y2, walls outside
const TY = 304, TA = 92;                                // the record: zero line, amplitude
const a = DATA.a, xl = DATA.xl, tau = DATA.tau;
const TAU0 = .43, POSTER_T = 0;                         // t = 0 (and the still): the echo back past the sensor
const hann = s => (s > 0 && s < tau) ? Math.pow(Math.sin(Math.PI * s / tau), 2) : 0;
function p(x, s) {                                      // the closed form, p / p_pulse
  if (x < xl) return hann(s - Math.abs(x) / a) + DATA.R * hann(s - (2 * xl - x) / a);
  return DATA.T * hann(s - x / a);
}
function field(s, alpha) {                              // the bore coloured by pressure, column by column
  const n = 250, dw = W / n;
  ctx.save(); ctx.globalAlpha *= alpha;
  for (let i = 0; i < n; i++) {
    const x = X0 + (i + .5) / n * (X1 - X0), v = p(x, s);
    ctx.fillStyle = Math.abs(v) < .004 ? C.steel : diverging(v / .5);   // the palette spans +-0.5
    ctx.fillRect(i * dw, Y1, dw + .6, Y2 - Y1);
  }
  ctx.restore();
}
function draw() {
  const s = wrap(TAU0 + t / DATA.slow, DATA.P);
  const aS = 1, aF = 1;
  field(s, aF);
  // the wall, as a section: steel with ink edges; the leak a notch in the lower wall
  const xL = XC(xl);
  ctx.save(); ctx.globalAlpha *= aS; ctx.fillStyle = C.steel2;
  ctx.fillRect(0, Y1 - WALL, W, WALL); ctx.fillRect(0, Y2, xL - 11, WALL); ctx.fillRect(xL + 11, Y2, W - xL - 11, WALL);
  ctx.restore();
  for (const y of [Y1 - WALL, Y1]) line([[0, y], [W, y]], { color: C.ink, width: SW.struct, alpha: aS });
  for (const y of [Y2, Y2 + WALL]) {
    line([[0, y], [xL - 11, y]], { color: C.ink, width: SW.struct, alpha: aS });
    line([[xL + 11, y], [W, y]], { color: C.ink, width: SW.struct, alpha: aS });
  }
  // the leak: water leaving through the hole, the one thing to follow
  const la = 1;
  line([[xL - 11, Y2], [xL - 11, Y2 + WALL]], { color: C.ink, width: SW.thin, alpha: aS });
  line([[xL + 11, Y2], [xL + 11, Y2 + WALL]], { color: C.ink, width: SW.thin, alpha: aS });
  arrow(xL, Y2 + 6, xL, Y2 + WALL + 34 + 6 * la, { color: C.accent, width: 7, head: 30, alpha: la });
  // the generator with its pressure sensor, on the pipe at x = 0
  const xg = XC(0);
  line([[xg - 26, Y1 - WALL], [xg + 26, Y1 - WALL], [xg + 26, Y1 - WALL - 40], [xg - 26, Y1 - WALL - 40]], { color: C.navy, width: 2, fill: C.navy, close: true, alpha: aS });
  // the record at the sensor: time drawn as distance a t / 2, so the echo sits under the leak
  const xt = tt => XC(a * tt / 2);
  line([[xt(0), TY], [XC(X1), TY]], { color: C.rule, width: SW.thin, alpha: aS });
  const rec = [], echo = [], te = 2 * xl / a;
  for (let k = 0; k <= 300; k++) {
    const tt = k / 300 * Math.min(s, 2 * X1 / a);
    const v = hann(tt) + DATA.R * hann(tt - te);
    (tt > te - .004 && tt < te + tau + .004 ? echo : rec).push([xt(tt), TY - TA * v]);
  }
  ctx.save(); ctx.globalAlpha *= aS * clamp(1 - (s / DATA.P - .93) / .06);   // the record clears before the next pulse
  line(rec.filter(q => q[0] < xt(te - .004) + 1), { color: C.navy, width: SW.thin + 1 });
  if (echo.length > 1) line(echo, { color: C.accent, width: SW.data - 1 });
  const tail = rec.filter(q => q[0] > xt(te + tau));
  if (tail.length > 1) line(tail, { color: C.navy, width: SW.thin + 1 });
  dot(xt(Math.min(s, 2 * X1 / a)), TY - TA * (hann(s) + DATA.R * hann(s - te)), 11, { color: C.navy, fill: C.navy });
  ctx.restore();
  // leader from the leak down to its echo, dashed
  line([[xL, Y2 + WALL + 48], [xL, TY + 50]], { color: C.guide, width: SW.guide, dash: DASH, alpha: aS * .8 });
}
boot();
"""

TITLE = "Pressure-wave reflection"
ARIA = ("A pressure pulse runs along a water pipe; at a leak part of it reflects back as a "
        "negative echo, which the pressure sensor at the start records after a delay that "
        "locates the leak.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
