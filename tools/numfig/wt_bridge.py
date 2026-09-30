"""The fun table, "Bridge vibration" (image2): a truck crossing a bridge.

Model: a simply supported Euler-Bernoulli girder under a two axle truck at
constant speed (Fryba's moving force problem), solved exactly by modal
superposition: each mode n obeys q'' + 2 zeta w_n q' + w_n^2 q =
(2 P / m L) sin(n pi v s / L) while an axle is on the span and rings freely
after it leaves, both in closed form. A truck arrives every P seconds, and
the periodic steady state is the sum of the crossings before (linearity),
so the loop is seamless and every frame is the model's.

Run: python tools/numfig/wt_bridge.py
"""
import numpy as np
from scipy.integrate import solve_ivp
from scipy.linalg import eigh

import common
import wt_lib

NAME = "bridge"

L, EI, MASS, ZETA = 40.0, 3.6e10, 12000.0, 0.015     # span (m), N m^2, kg/m, damping
AXLES = [(0.0, 100e3), (4.0, 200e3)]                   # (distance behind the front axle, load N)
V = 30.5                                               # m/s (110 km/h)
PERIOD = 2.5                                           # s between trucks (76 m headway; P f1 = 4.25, off resonance)
SLOW = 2.0                                             # display seconds per model second
NMODE = 8
KBACK = 40                                             # earlier crossings summed (e^-zeta w1 K P ~ 1e-9)
M_SAMP = 480                                           # samples per loop for the page

wn = np.array([(n * np.pi / L) ** 2 * np.sqrt(EI / MASS) for n in range(1, NMODE + 1)])
f1 = wn[0] / (2 * np.pi)


def crossing(s, n, P):
    """Modal coordinate of mode n (1-based) for one axle of load P entering
    the span at s = 0, s in seconds (array), zero before it enters."""
    w = wn[n - 1]
    wd = w * np.sqrt(1 - ZETA ** 2)
    Om = n * np.pi * V / L
    F0 = 2 * P / (MASS * L)
    X = F0 / np.hypot(w ** 2 - Om ** 2, 2 * ZETA * w * Om)
    ph = np.arctan2(2 * ZETA * w * Om, w ** 2 - Om ** 2)
    A = X * np.sin(ph)
    B = (ZETA * w * A - X * Om * np.cos(ph)) / wd
    T = L / V

    def on(u):
        e = np.exp(-ZETA * w * u)
        q = X * np.sin(Om * u - ph) + e * (A * np.cos(wd * u) + B * np.sin(wd * u))
        qd = (X * Om * np.cos(Om * u - ph)
              + e * ((-ZETA * w * A + wd * B) * np.cos(wd * u) + (-ZETA * w * B - wd * A) * np.sin(wd * u)))
        return q, qd

    s = np.asarray(s, float)
    q = np.zeros_like(s)
    qT, qdT = on(T)
    m1 = (s >= 0) & (s <= T)
    q[m1] = on(s[m1])[0]
    m2 = s > T
    u = s[m2] - T
    e = np.exp(-ZETA * w * u)
    q[m2] = e * (qT * np.cos(wd * u) + (qdT + ZETA * w * qT) / wd * np.sin(wd * u))
    return q


def steady(tau):
    """Periodic steady state: modal coordinates (NMODE, len(tau)), tau in
    [0, PERIOD), tau = 0 when the front axle reaches the left support."""
    Q = np.zeros((NMODE, len(tau)))
    for n in range(1, NMODE + 1):
        for d, P in AXLES:
            for k in range(KBACK + 1):
                Q[n - 1] += crossing(tau + k * PERIOD - d / V, n, P)
    return Q


# ------------------------------------------------------------------ the page's numbers
tau = np.arange(M_SAMP) * PERIOD / M_SAMP
Q = steady(tau)
xs = np.linspace(0, L, 121)
Phi = np.array([np.sin(n * np.pi * xs / L) for n in range(1, NMODE + 1)])
Wxt = Phi.T @ Q                                   # deflection (m), positive down
wmax = np.abs(Wxt).max()

# ------------------------------------------------------------------ validation
lines = []
say = lines.append
say("nf-wt-bridge: the fun table, 'Bridge vibration' (image2)")
say("")
say("MODEL")
say(f"  simply supported Euler-Bernoulli girder, L = {L:.0f} m, EI = {EI:.2e} N m^2, m = {MASS:.0f} kg/m,")
say(f"  modal damping zeta = {ZETA}; a two axle truck, {AXLES[0][1]/1e3:.0f} kN front and {AXLES[1][1]/1e3:.0f} kN"
    f" rear, {AXLES[1][0]:.0f} m apart, at v = {V:.1f} m/s ({V*3.6:.0f} km/h),")
say(f"  one truck every {PERIOD} s. Closed form modal response, {NMODE} modes, the steady state summing")
say(f"  the {KBACK} crossings before (their residue e^(-zeta w1 {KBACK} P) = "
    f"{np.exp(-ZETA*wn[0]*KBACK*PERIOD):.1e}).")
say(f"  speed parameter alpha = v / (2 f1 L) = {V/(2*f1*L):.4f}")
say(f"  the headway is kept off a whole number of first mode periods (P f1 = {PERIOD*f1:.2f}): trucks arriving in")
say("  step with the ringing would pump it (at P f1 = 4.08 the steady state peak is 28 % higher).")
say("")
say("CHECK 1: natural frequencies, closed form (n pi / L)^2 sqrt(EI/m) against Hermite FE (60 elements)")
K, M = wt_lib.hermite_beam(60, L, EI, MASS)
keep = [i for i in range(K.shape[0]) if i not in (0, K.shape[0] - 2)]      # w = 0 at both supports
lam = eigh(K[np.ix_(keep, keep)], M[np.ix_(keep, keep)], eigvals_only=True)[:4]
for n in range(4):
    fe = np.sqrt(lam[n]) / (2 * np.pi)
    say(f"  f{n+1}: closed form {wn[n]/(2*np.pi):8.4f} Hz, FE {fe:8.4f} Hz, rel. error {fe/(wn[n]/(2*np.pi))-1:+.1e}")
say("")
say("CHECK 2: quasi static limit, a load P at midspan: modal series against P L^3 / (48 EI)")
Ps = 1.0
ws = sum(2 * Ps / (MASS * L) / wn[n - 1] ** 2 * np.sin(n * np.pi / 2) ** 2 for n in range(1, NMODE + 1))
wex = Ps * L ** 3 / (48 * EI)
say(f"  {NMODE} modes: {ws:.6e} m, closed form {wex:.6e} m, rel. error {ws/wex-1:+.1e}")
say("")
say("CHECK 3: one crossing, closed form against direct integration of the modal equations (RK45, rtol 1e-10)")
T_one = L / V + AXLES[-1][0] / V + 1.5
sgrid = np.linspace(0, T_one, 3001)
worst = 0.0
for n in (1, 2, 3):
    ref = np.zeros_like(sgrid)
    for d, P in AXLES:
        def rhs(t, y, n=n, d=d, P=P):
            x = V * t - d
            F = 2 * P / (MASS * L) * np.sin(n * np.pi * x / L) if 0 <= x <= L else 0.0
            return [y[1], F - 2 * ZETA * wn[n - 1] * y[1] - wn[n - 1] ** 2 * y[0]]
        sol = solve_ivp(rhs, (0, T_one), [0, 0], t_eval=sgrid, rtol=1e-10, atol=1e-16, max_step=2e-3)
        ref += sol.y[0]
    ours = sum(crossing(sgrid - d / V, n, P) for d, P in AXLES)
    err = np.abs(ours - ref).max() / np.abs(ref).max()
    worst = max(worst, err)
    say(f"  mode {n}: max |closed form - RK45| / max|q| = {err:.1e}")
say("")
say("CHECK 4: the same crossing by an independent FE model (60 Hermite elements, the load consistent")
say("  on the element under each axle, Newmark average acceleration, dt = 2e-4 s, the same modal damping)")
ne = 60
K, M = wt_lib.hermite_beam(ne, L, EI, MASS)
Kf, Mf = K[np.ix_(keep, keep)], M[np.ix_(keep, keep)]
lam_all, Vec = eigh(Kf, Mf)
Vec = Vec / np.sqrt(np.einsum("ij,ik,kj->j", Vec, Mf, Vec))
Cf = Mf @ Vec @ np.diag(2 * ZETA * np.sqrt(lam_all)) @ Vec.T @ Mf
le = L / ne
full = 2 * (ne + 1)


def load(t):
    F = np.zeros(full)
    for d, P in AXLES:
        x = V * t - d
        if 0 <= x <= L:
            e = min(int(x / le), ne - 1)
            F[2 * e:2 * e + 4] += P * wt_lib.hermite_shape(x / le - e, le)
    return F[keep]


dt = 2e-4
nst = int(round(T_one / dt))
u = np.zeros(len(keep)); vv = np.zeros_like(u); a = np.zeros_like(u)
Keff = Kf + 2 / dt * Cf + 4 / dt ** 2 * Mf
Kinv = np.linalg.inv(Keff)
mid_dof = keep.index(2 * (ne // 2))
fe_mid = [0.0]
for i in range(1, nst + 1):
    t = i * dt
    rhs = load(t) + Mf @ (4 / dt ** 2 * u + 4 / dt * vv + a) + Cf @ (2 / dt * u + vv)
    un = Kinv @ rhs
    vn = 2 / dt * (un - u) - vv
    an = 4 / dt ** 2 * (un - u) - 4 / dt * vv - a
    u, vv, a = un, vn, an
    fe_mid.append(u[mid_dof])
fe_mid = np.array(fe_mid)
tt = np.arange(nst + 1) * dt
modal_mid = sum(np.sin(n * np.pi / 2) * sum(crossing(tt - d / V, n, P) for d, P in AXLES)
                for n in range(1, NMODE + 1))
err_fe = np.abs(fe_mid - modal_mid).max() / np.abs(fe_mid).max()
say(f"  midspan deflection, max |FE - modal| / max |w| = {err_fe:.1e} (max w = {np.abs(fe_mid).max()*1e3:.3f} mm)")
xf_grid = np.linspace(0, L + AXLES[-1][0], 2001)


def static_mid(xf):
    """Static midspan deflection with the front axle at xf (closed form)."""
    w = 0.0
    for d, P in AXLES:
        b = xf - d
        if 0 <= b <= L:
            aa = min(b, L - b)                    # symmetric: load at distance aa from a support
            w += P * aa * (3 * L ** 2 - 4 * aa ** 2) / (48 * EI)
    return w


st = np.array([static_mid(x) for x in xf_grid])
daf = np.abs(modal_mid).max() / st.max()
say(f"  static maximum at midspan {st.max()*1e3:.3f} mm; dynamic amplification {daf:.3f}")
say("")
say("CHECK 5: the loop closes: steady state at the end of a period against its start")
Qe = steady(np.array([PERIOD - 1e-9, 0.0]))
say(f"  max |Q(P) - Q(0)| / max |Q| = {np.abs(Qe[:, 0]-Qe[:, 1]).max()/np.abs(Q).max():.1e}")
say("")
say("DRAWING")
say(f"  deflection drawn {52/(wmax*1e3):.1f} units per mm (peak {wmax*1e3:.2f} mm over a loop drawn 52 units);")
say(f"  span {L:.0f} m = 870 units; girder drawn 2 m deep, to scale.")
say(f"  time slowed {SLOW:.0f} x: the first mode, {f1:.3f} Hz, shows at {f1/SLOW:.3f} Hz; a truck every"
    f" {PERIOD*SLOW:.1f} s on screen.")
say(f"  the page interpolates q_n(t) linearly between {M_SAMP} samples a loop"
    f" ({PERIOD/M_SAMP*1e3:.2f} ms apart); worst error in w:")
fine = np.linspace(0, PERIOD, 20001)[:-1]
Qf = steady(fine)
Qi = np.array([np.interp(fine, np.append(tau, PERIOD), np.append(q, q[0])) for q in Q])
say(f"  {np.abs(Phi.T @ (Qf - Qi)).max()/wmax:.1e} of the peak")
wt_lib.write_check(NAME, lines)

DATA = {
    "L": L, "v": V, "P": PERIOD, "slow": SLOW, "nm": NMODE, "ns": M_SAMP,
    "q": common.f32((Q / wmax).T.ravel()),                  # (sample, mode), scaled so max |w| = 1
    "axles": [d for d, _ in AXLES],
}

JS = r"""
const X0 = -3, X1 = 43, SX = W / (X1 - X0);            // road from -3 m to 43 m
const XC = x => (x - X0) * SX;
const YT = 176, DEPTH = 2.0 * SX, AMP = 52;              // deck top at rest, girder 2 m deep
const Lm = DATA.L, NM = DATA.nm, NS = DATA.ns, Qs = b64f32(DATA.q);
const TAU0 = 0.80;                                       // t = 0 (and the still): the heavy rear axle near midspan
const POSTER_T = 0;
const NX = 97, XS = [], SN = [];
for (let i = 0; i < NX; i++) { XS.push(i / (NX - 1) * Lm); for (let n = 1; n <= NM; n++) SN.push(Math.sin(n * Math.PI * XS[i] / Lm)); }
const qn = new Float32Array(NM);
function modal(tau) {                                     // q_n at loop phase tau, linear between samples
  const u = wrap(tau, DATA.P) / DATA.P * NS, i = Math.floor(u) % NS, j = (i + 1) % NS, s = u - Math.floor(u);
  for (let n = 0; n < NM; n++) qn[n] = lerp(Qs[i * NM + n], Qs[j * NM + n], s);
}
function defl(x) {                                        // deflection at x (m), drawing units, down
  if (x <= 0 || x >= Lm) return 0;
  let w = 0; for (let n = 0; n < NM; n++) w += qn[n] * Math.sin((n + 1) * Math.PI * x / Lm);
  return AMP * w;
}
function truck(xf, a) {                                   // front axle at xf (m), riding the deck
  const xr = xf - DATA.axles[1], R = .5 * SX;
  const pf = [XC(xf), YT + defl(xf) - R], pr = [XC(xr), YT + defl(xr) - R];
  const ang = Math.atan2(pf[1] - pr[1], pf[0] - pr[0]);
  ctx.save(); ctx.globalAlpha *= a; ctx.translate(pr[0], pr[1]); ctx.rotate(ang);
  const m = SX, lw = SW.struct;
  // box body over the rear axle, the cab over the front: TikZ outlines
  const wb = DATA.axles[1] * m;
  const box = [[-1.9 * m, -.35 * m], [2.25 * m, -.35 * m], [2.25 * m, -3.7 * m], [-1.9 * m, -3.7 * m]];
  line(box, { color: C.ink, width: lw, fill: C.steel2, close: true });
  const cab = [[2.45 * m, -.35 * m], [5.25 * m, -.35 * m], [5.25 * m, -1.85 * m], [4.7 * m, -2.95 * m], [2.45 * m, -2.95 * m]];
  line(cab, { color: C.ink, width: lw, fill: C.steel, close: true });
  line([[3.7 * m, -1.7 * m], [4.85 * m, -1.7 * m], [4.4 * m, -2.6 * m], [3.7 * m, -2.6 * m]], { color: C.ink, width: SW.thin, fill: '#fff', close: true });
  for (const x of [0, wb]) { dot(x, 0, R, { color: C.ink, fill: C.ink }); dot(x, 0, R * .38, { color: '#fff', fill: '#fff', width: 1 }); }
  ctx.restore();
}
function abutment(side, a) {                              // earth behind a support, hatched
  const xs = side < 0 ? XC(0) : XC(Lm), yb = YT + DEPTH, seat = yb + 3.2 * 16;
  const back = xs - side * 22, far = side < 0 ? -10 : W + 10;
  const poly = [[far, YT], [back, YT], [back, seat - 30], [xs + side * 40, seat - 30], [xs + side * 40, seat], [xs - side * 60, seat], [xs - side * 60, H + 10], [far, H + 10]];
  ctx.save(); ctx.globalAlpha *= a;
  ctx.beginPath(); poly.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath();
  ctx.fillStyle = '#fff'; ctx.fill(); ctx.clip();
  for (let x = -H; x < W + H; x += 30) line([[x, H + 10], [x + H, 10]], { color: C.rule, width: 3.2 });
  ctx.restore();
  line(poly.slice(0, 7), { color: C.ink, width: SW.struct, alpha: a });
}
function draw() {
  const tau = TAU0 + t / DATA.slow;
  modal(tau);
  const aG = 1, wipe = 1;
  abutment(-1, aG); abutment(1, aG);
  // the rest position of the girder's soffit
  line([[XC(0), YT + DEPTH], [XC(Lm), YT + DEPTH]], { color: C.guide, width: SW.guide, dash: DASH, alpha: aG });
  // supports: a pin on the left, a roller on the right, drawn at the girder's ends
  big(XC(0) + 8, YT + DEPTH, 3.2, () => pin(0, 0, { s: 16, alpha: aG }));
  big(XC(Lm) - 8, YT + DEPTH, 3.2, () => pin(0, 0, { s: 16 - 6, roller: true, alpha: aG }));
  // the girder, deflected: top and soffit follow w(x); drawn in from the left
  const top = [], bot = [];
  for (let i = 0; i < NX; i++) { const x = XC(XS[i]), y = YT + defl(XS[i]); top.push([x, y]); bot.push([x, y + DEPTH]); }
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, XC(0) + (XC(Lm) - XC(0) + 20) * wipe, H); ctx.clip();
  line(top.concat(bot.slice().reverse()), { color: C.ink, width: SW.struct, fill: C.steel, close: true, alpha: clamp(wipe * 3) });
  // the accelerometer at midspan, riding the soffit
  const ym = YT + defl(Lm / 2) + DEPTH;
  line([[XC(Lm / 2) - 15, ym], [XC(Lm / 2) + 15, ym], [XC(Lm / 2) + 15, ym + 26], [XC(Lm / 2) - 15, ym + 26]], { color: C.navy, width: 2, fill: C.navy, close: true });
  ctx.restore();
  // the truck: every P seconds one arrives; draw the one on the road now (and a leaving one)
  const ph = wrap(tau, DATA.P);
  for (const k of [0, -1]) {                              // this truck, and the next one arriving
    const xf = DATA.v * (ph + k * DATA.P);
    if (xf - 7 < X1 + 3 && xf > X0 - 2) truck(xf, 1);
  }
}
boot();
"""

TITLE = "Bridge vibration"
ARIA = ("A truck crosses a simply supported bridge girder every few seconds; the girder sags "
        "under it and keeps ringing in its first modes after it leaves, as an exact moving "
        "load model computes.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
