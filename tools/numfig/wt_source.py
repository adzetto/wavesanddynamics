"""The fun table, "Source location" (image5): an acoustic emission event located.

Model: a crack pops in a large steel plate (plan view of a region of it) and
releases an elastic wave; at low frequency the fundamental symmetric Lamb
mode S0 runs at the plate velocity c = sqrt(E / rho (1 - nu^2)), the same
every way. Four sensors record the arrival times t_i = |s - x_i| / c. The
source time is unknown, so each pair of sensors gives only a difference,
and the points with |p - x_i| - |p - x_j| = c (t_i - t_j) form one branch of
a hyperbola with the pair as foci; the branches meet at the source. That is
the classic time difference of arrival location used in seismology and
acoustic emission.

Run: python tools/numfig/wt_source.py
"""
import numpy as np
from scipy.optimize import brentq, least_squares

import wt_lib

NAME = "source"

E, NU, RHO = 210e9, 0.29, 7850.0
C_PLATE = np.sqrt(E / (RHO * (1 - NU ** 2)))
VIEW = (1.0, 0.40)                                    # m, the region drawn (W x H)
SENS = np.array([[0.085, 0.075], [0.915, 0.085], [0.885, 0.330], [0.125, 0.320]])
SRC = np.array([0.700, 0.205])
PAIRS = [(0, 2), (1, 2), (1, 3)]                      # three independent differences, all four sensors
SLOW = 1.25e4

tarr = np.linalg.norm(SENS - SRC, axis=1) / C_PLATE


def branch(i, j, n=400):
    """Points of the branch |p - x_i| - |p - x_j| = c (t_i - t_j), inside the view."""
    xi, xj = SENS[i], SENS[j]
    d = C_PLATE * (tarr[i] - tarr[j])
    m, f = (xi + xj) / 2, np.linalg.norm(xj - xi) / 2
    e1 = (xj - xi) / (2 * f); e2 = np.array([-e1[1], e1[0]])
    a = d / 2; b = np.sqrt(f * f - a * a)
    u = np.linspace(-4, 4, 4001)
    p = m + np.outer(a * np.cosh(u), e1) + np.outer(b * np.sinh(u), e2)
    inside = (p[:, 0] >= -.02) & (p[:, 0] <= VIEW[0] + .02) & (p[:, 1] >= -.02) & (p[:, 1] <= VIEW[1] + .02)
    p = p[inside]
    # resample evenly by arc length, and note where the source falls along it
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    q = np.array([np.interp(np.linspace(0, s[-1], n), s, p[:, k]) for k in (0, 1)]).T
    return q, d


# ------------------------------------------------------------------ S0 at low frequency: Rayleigh-Lamb
def s0_velocity(f, d):
    """Phase velocity of S0 in a free plate of thickness d at frequency f (Rayleigh-Lamb, symmetric)."""
    cl = np.sqrt(E * (1 - NU) / (RHO * (1 + NU) * (1 - 2 * NU)))
    ct = np.sqrt(E / (2 * RHO * (1 + NU)))
    w, h = 2 * np.pi * f, d / 2

    def F(c):
        k = w / c
        p2, q2 = (w / cl) ** 2 - k * k, (w / ct) ** 2 - k * k
        q = np.sqrt(q2)
        if p2 >= 0:
            p = np.sqrt(p2); cp, psp = np.cos(p * h), p * np.sin(p * h)
        else:
            al = np.sqrt(-p2); cp, psp = np.cosh(al * h), -al * np.sinh(al * h)
        return (k * k - q2) ** 2 * cp * np.sin(q * h) + 4 * k * k * q * psp * np.cos(q * h)

    return brentq(F, 0.95 * C_PLATE, 1.0 * C_PLATE - 1e-6, xtol=1e-12)


lines = []
say = lines.append
say("nf-wt-source: the fun table, 'Source location' (image5)")
say("")
say("MODEL")
say(f"  a large steel plate, E = {E/1e9:.0f} GPa, nu = {NU}, rho = {RHO:.0f} kg/m^3; S0 at low frequency runs at")
say(f"  the plate velocity c = sqrt(E / rho (1 - nu^2)) = {C_PLATE:.1f} m/s. Region drawn {VIEW[0]} x {VIEW[1]} m.")
say(f"  source at ({SRC[0]}, {SRC[1]}) m; sensors at " + ", ".join(f"({x}, {y})" for x, y in SENS) + " m")
say("  arrival times: " + ", ".join(f"t{i+1} = {t*1e6:.2f} us" for i, t in enumerate(tarr)))
say("")
say("CHECK 1: S0 in a 10 mm plate by the Rayleigh-Lamb equation against the plate velocity")
for f in (10e3, 30e3, 60e3):
    c = s0_velocity(f, 0.010)
    say(f"  f = {f/1e3:4.0f} kHz (fd = {f*10/1e6:.2f} MHz mm): c_S0 = {c:.2f} m/s, c_plate = {C_PLATE:.2f} m/s,"
        f" {c/C_PLATE-1:+.1e}")
say("  so a burst below 30 kHz in a 10 mm plate travels at c_plate within 0.1 %.")
say("")
say("CHECK 2: the source recovered from the arrival time differences alone (source time unknown)")
dt = tarr - tarr[0]
res = least_squares(lambda p: np.linalg.norm(SENS - p[:2], axis=1) / C_PLATE - p[2] - tarr,
                    x0=[0.5, 0.2, 0.0], xtol=1e-15, ftol=1e-15, gtol=1e-15)
say(f"  Gauss-Newton from the centre: ({res.x[0]:.12f}, {res.x[1]:.12f}) m, error"
    f" {np.linalg.norm(res.x[:2]-SRC):.1e} m; source time {res.x[2]*1e6:+.1e} us")
say("")
say("CHECK 3: the drawn hyperbolas satisfy their equation and pass through the source")
for i, j in PAIRS:
    q, d = branch(i, j)
    r = np.abs(np.linalg.norm(q - SENS[i], axis=1) - np.linalg.norm(q - SENS[j], axis=1) - d).max()
    dist = np.min(np.linalg.norm(q - SRC, axis=1))
    say(f"  sensors {i+1}, {j+1}: c (t{i+1} - t{j+1}) = {d*1e3:+8.3f} mm; the drawn polyline off its equation"
        f" by {r*1e6:.2f} um at most; {dist*1e3:.2f} mm from the source at its nearest vertex")
say("")
say("DRAWING")
say(f"  {VIEW[0]} m = 900 units; the front is the circle |p - s| = c t, drawn until it has passed every sensor;")
say("  the plate is drawn with edges, and the fronts and branches are clipped to them (reflections from")
say("  the edges come after the direct arrivals the location uses, and are not drawn).")
say(f"  time slowed {SLOW:.2e} x: the farthest sensor hears the event {tarr.max()*1e6:.0f} us after it,"
    f" {tarr.max()*SLOW:.2f} s on screen.")
wt_lib.write_check(NAME, lines)

hyp = []
for i, j in PAIRS:
    q, d = branch(i, j, 240)
    k = int(np.argmin(np.linalg.norm(q - SRC, axis=1)))
    hyp.append({"p": q.ravel().tolist(), "k": k})
DATA = {"c": C_PLATE, "slow": SLOW, "view": list(VIEW), "sens": SENS.tolist(), "src": SRC.tolist(),
        "t": tarr.tolist(), "hyp": hyp}

JS = r"""
const SC = 900 / DATA.view[0], OX = 50, OY = 20;
const XC = x => OX + x * SC, YC = y => OY + (DATA.view[1] - y) * SC;
const c = DATA.c, S = DATA.sens, SRC = DATA.src, TA = DATA.t;
const TMAX = Math.max(...TA);
const LOOP = 5.6;                                       // seconds on screen
const DISP = tau => tau * DATA.slow;                    // model time to screen time
const U0 = DISP(TMAX) + 1.55, POSTER_T = 0;             // t = 0 (and the still): every sensor heard, the branches drawn
function tri(x, y, r, fill, a) {                         // a sensor, as seismic maps draw one
  line([[x, y - r], [x + r * .9, y + r * .62], [x - r * .9, y + r * .62]], { color: C.navy, width: 3, fill, close: true, alpha: a });
}
function draw() {
  const u = wrap(U0 + t, LOOP);                         // screen time since the event
  const tau = u / DATA.slow;                             // model time since the event
  const aS = 1;
  const k = clamp(1 - (u - (LOOP - .45)) / .4);          // all but the plate fades before the next event
  // the plate: a region of a large one, steel, cut by the frame
  const px0 = XC(0), py0 = YC(DATA.view[1]), pw = DATA.view[0] * SC, ph = DATA.view[1] * SC;
  line([[px0, py0], [px0 + pw, py0], [px0 + pw, py0 + ph], [px0, py0 + ph]], { color: C.ink, width: SW.struct, fill: C.steel, close: true });
  ctx.save(); ctx.beginPath(); ctx.rect(px0, py0, pw, ph); ctx.clip();
  // the front: every point the wave has reached, |p - s| = c t
  const r = c * tau * SC, reach = Math.max(...S.map(p => Math.hypot(XC(p[0]) - XC(SRC[0]), YC(p[1]) - YC(SRC[1]))));
  if (u > 0 && r < reach + 60) {
    const af = k * clamp((reach + 60 - r) / 60) * clamp(r / 30);
    ctx.save(); ctx.globalAlpha *= af; ctx.strokeStyle = C.blue; ctx.lineWidth = SW.data;
    ctx.beginPath(); ctx.arc(XC(SRC[0]), YC(SRC[1]), r, 0, 2 * Math.PI); ctx.stroke(); ctx.restore();
  }
  // the branches, each drawn out from where it meets the source once both its sensors have heard it
  const hs = DISP(TMAX) + .15;
  DATA.hyp.forEach((h, i) => {
    const pts = []; for (let j = 0; j < h.p.length; j += 2) pts.push([XC(h.p[j]), YC(h.p[j + 1])]);
    if (u < hs + .12 * i) return;
    const a1 = pts.slice(0, h.k + 1).reverse(), a2 = pts.slice(h.k);
    const e = easeInOut(clamp((u - hs - .12 * i) / .45));
    line(a1, { color: C.navy, width: SW.thin, dash: DASH, progress: e, alpha: k });
    line(a2, { color: C.navy, width: SW.thin, dash: DASH, progress: e, alpha: k });
  });
  ctx.restore();                                          // the plate's clip
  // the source: the crack, and the point the branches agree on
  const pop = u > 0 ? Math.exp(-u / .5) : 0;
  const sa = Math.max(pop, clamp((u - hs - .5) / .3)) * k;
  if (sa > 0) {
    dot(XC(SRC[0]), YC(SRC[1]), 17, { color: '#781E2C', fill: C.accent, width: 3, alpha: sa });
    if (u > hs + .5) { const q = clamp((u - hs - .5) / .3); dot(XC(SRC[0]), YC(SRC[1]), 17 + 22 * easeOut(q), { color: C.accent, fill: null, width: 4, alpha: k * q * (1 - .4 * q) }); }
  }
  // the sensors: filled once the wave has reached them
  S.forEach((p, i) => {
    const heard = tau >= TA[i];
    const flash = heard ? Math.exp(-(tau - TA[i]) * DATA.slow / .35) : 0;
    tri(XC(p[0]), YC(p[1]), 26, heard ? C.navy : '#fff', aS);
    if (flash > .02) dot(XC(p[0]), YC(p[1]) + 3, 26 + 30 * (1 - flash), { color: C.navy, fill: null, width: 4, alpha: flash * aS });
  });
}
boot();
"""

TITLE = "Source location"
ARIA = ("A crack in a plate releases a circular elastic wave; four sensors hear it one after "
        "another, and the hyperbolas drawn from their arrival time differences meet at the source.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS))
