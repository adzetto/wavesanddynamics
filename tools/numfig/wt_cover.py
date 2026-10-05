"""The waves guide's cover (image1): one bridge, two scales of the same physics.

Left, a cable stayed bridge (130 + 300 + 130 m, steel box deck on 44 stays
from two concrete pylons) in elevation, breathing in its first vertical
bending mode, computed by a 2D finite element model (frame elements for
the deck and pylons, truss elements for the stays) and shown in real time;
accelerometers ride its deck. Right, detail A, at the middle of the main
span (the client, 30 Sep 2026: A in the middle of the bridge, not at its
edge), where the first mode bends the deck most and its sagging puts the
bottom flange in tension: that flange of the box girder (a 12 mm steel
plate) at the NDT scale, where a transducer
launches a 200 kHz A0 Lamb wave packet (Fourier synthesis over the exact
Rayleigh-Lamb dispersion) that a fatigue crack partly sends back.
Global vibration at a fraction of a hertz, local guided waves at hundreds of
kilohertz: the two ends of what the document connects.

Run: python tools/numfig/wt_cover.py
"""
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import brentq

import common
import wt_lib

NAME = "cover"

# ------------------------------------------------------------------ the bridge
E_S, E_C, E_ST, RHO_S = 210e9, 36e9, 195e9, 7850.0
DECK = dict(A=1.20, I=3.2, m=18000.0)            # steel box girder with its surfacing (m^2, m^4, kg/m)
PYL = dict(A=24.0, I=70.0, m=62000.0)            # concrete pylon leg pair, in plane
SIDE, MAIN = 130.0, 300.0
HP, HB = 82.0, 45.0                              # pylon above the deck, below it to the pile cap (m)
TOT = 2 * SIDE + MAIN
XP = (SIDE, SIDE + MAIN)
D_AN = [18.0 + 12.0 * k for k in range(11)]      # deck anchors on the main span side, from each pylon
S_AN = [18.0 + 11.0 * k for k in range(11)]      # and on the side span side
P_AN = [HP - 26.0 + 2.6 * k for k in range(11)]  # pylon anchors, heights above the deck
ST_A = lambda Lc: 0.0045 + 0.00006 * Lc          # stay area grows with its length (m^2)


def frame_km(L, EA, EI, m):
    """Local stiffness and consistent mass of a 2D Euler-Bernoulli frame element (u, v, th at each end)."""
    k = np.zeros((6, 6))
    k[[0, 3], [0, 3]] = EA / L; k[0, 3] = k[3, 0] = -EA / L
    idx = [1, 2, 4, 5]
    k[np.ix_(idx, idx)] = EI / L ** 3 * np.array([[12, 6 * L, -12, 6 * L], [6 * L, 4 * L * L, -6 * L, 2 * L * L],
                                                  [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L * L, -6 * L, 4 * L * L]])
    mm = np.zeros((6, 6))
    mm[np.ix_([0, 3], [0, 3])] = m * L / 6 * np.array([[2, 1], [1, 2]])
    mm[np.ix_(idx, idx)] = m * L / 420 * np.array([[156, 22 * L, 54, -13 * L], [22 * L, 4 * L * L, 13 * L, -3 * L * L],
                                                  [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L * L, -22 * L, 4 * L * L]])
    return k, mm


class Model:
    """Nodes (x, y), dofs (u, v, th), K and M, assembled element by element."""

    def __init__(self):
        self.xy, self.el = [], []

    def node(self, x, y):
        self.xy.append((x, y)); return len(self.xy) - 1

    def finish(self, ties=()):
        n = len(self.xy)
        self.dof = np.arange(3 * n).reshape(n, 3)
        for a, b, comp in ties:                   # node b shares node a's dof comp (a bearing)
            self.dof[b, comp] = self.dof[a, comp]
        nd = 3 * n
        self.K, self.M = np.zeros((nd, nd)), np.zeros((nd, nd))
        for kind, a, b, *p in self.el:
            (x1, y1), (x2, y2) = self.xy[a], self.xy[b]
            L = np.hypot(x2 - x1, y2 - y1); c, s = (x2 - x1) / L, (y2 - y1) / L
            if kind == "frame":
                k, mm = frame_km(L, *p)
                T = np.zeros((6, 6))
                for o in (0, 3):
                    T[o:o + 2, o:o + 2] = [[c, s], [-s, c]]; T[o + 2, o + 2] = 1
                g = np.r_[self.dof[a], self.dof[b]]
                self.K[np.ix_(g, g)] += T.T @ k @ T; self.M[np.ix_(g, g)] += T.T @ mm @ T
            else:                                  # truss: axial stiffness, its mass lumped at the ends
                EA, m = p
                g = np.r_[self.dof[a][:2], self.dof[b][:2]]
                self.K[np.ix_(g, g)] += EA / L * np.outer([-c, -s, c, s], [-c, -s, c, s])
                for q in g:
                    self.M[q, q] += m * L / 2

    def modes(self, fixed, n):
        free = np.setdiff1d(np.unique(self.dof), fixed)
        lam, V = eigh(self.K[np.ix_(free, free)], self.M[np.ix_(free, free)], subset_by_index=[0, n - 1])
        full = np.zeros((self.K.shape[0], n)); full[free] = V
        return np.sqrt(lam) / (2 * np.pi), full


def bridge(h):
    md = Model()
    xs = set(np.round(np.arange(0, TOT + 1e-9, h), 6))
    for k, xp in enumerate(XP):
        for d in D_AN:
            xs.add(round(xp + d if k == 0 else xp - d, 6))
        for d in S_AN:
            xs.add(round(xp - d if k == 0 else xp + d, 6))
    xs = np.array(sorted(xs))
    deck = [md.node(x, 0.0) for x in xs]
    for i in range(len(deck) - 1):
        md.el.append(("frame", deck[i], deck[i + 1], E_S * DECK["A"], E_S * DECK["I"], DECK["m"]))
    ties, pylons, stays = [], [], []
    for k, xp in enumerate(XP):
        ys = np.array(sorted(set(np.round(np.r_[np.arange(-HB, HP + 1e-9, h), P_AN, 0.0], 6))))
        ids = [md.node(xp, y) for y in ys]
        for i in range(len(ids) - 1):
            md.el.append(("frame", ids[i], ids[i + 1], E_C * PYL["A"], E_C * PYL["I"], PYL["m"]))
        dk = deck[int(np.argmin(np.abs(xs - xp)))]
        ties.append((dk, ids[int(np.argmin(np.abs(ys)))], 1))          # vertical bearing on the crossbeam
        for dm, ds, hp in zip(D_AN, S_AN, P_AN):
            pn = ids[int(np.argmin(np.abs(ys - hp)))]
            for xd in ((xp + dm, xp - ds) if k == 0 else (xp - dm, xp + ds)):
                dn = deck[int(np.argmin(np.abs(xs - xd)))]
                A = ST_A(np.hypot(xd - xp, hp))
                md.el.append(("truss", pn, dn, E_ST * A, RHO_S * A * 1.1))
                stays.append((pn, dn))
        pylons.append(ids)
    md.finish(ties)
    fixed = [md.dof[deck[0], 0], md.dof[deck[0], 1], md.dof[deck[-1], 1]]
    for ids in pylons:
        fixed += list(md.dof[ids[0]])                 # pylon bases fixed
    return md, xs, deck, pylons, stays, fixed


lines = []
say = lines.append
say("nf-wt-cover: the waves guide's cover (image1)")
say("")
say("BRIDGE MODEL")
say(f"  cable stayed, spans {SIDE:.0f} + {MAIN:.0f} + {SIDE:.0f} m; steel box deck EA = {E_S*DECK['A']:.3e} N,"
    f" EI = {E_S*DECK['I']:.3e} N m^2, m = {DECK['m']:.0f} kg/m;")
say(f"  concrete pylons {HP:.0f} m above the deck and {HB:.0f} m below, EI = {E_C*PYL['I']:.3e} N m^2,"
    f" m = {PYL['m']:.0f} kg/m, fixed at the pile caps;")
say(f"  {4*len(D_AN)} stays (E = {E_ST/1e9:.0f} GPa, area {ST_A(20)*1e4:.0f} to {ST_A(160)*1e4:.0f} cm^2 by length),"
    f" taut: axial stiffness, no sag, no geometric stiffness;")
say("  deck on rollers at the abutments (fixed longitudinally at the left one) and on vertical bearings")
say("  at the pylon crossbeams. 2D Euler-Bernoulli frame elements, consistent mass.")
say("")
say("CHECK 1: the element, alone, against closed forms")
m1 = Model()
ids = [m1.node(x, 0.0) for x in np.linspace(0, 100, 41)]
for i in range(40):
    m1.el.append(("frame", ids[i], ids[i + 1], E_S * DECK["A"], E_S * DECK["I"], DECK["m"]))
m1.finish()
f, _ = m1.modes([m1.dof[ids[0], 0], m1.dof[ids[0], 1], m1.dof[ids[-1], 1]], 3)
fc = [(n * np.pi / 100) ** 2 * np.sqrt(E_S * DECK["I"] / DECK["m"]) / (2 * np.pi) for n in (1, 2, 3)]
say("  simply supported 100 m deck beam: " + ", ".join(f"f{n+1} {f[n]:.5f} Hz ({f[n]/fc[n]-1:+.1e})" for n in range(3)))
m2 = Model()
ids = [m2.node(0.0, y) for y in np.linspace(0, HP + HB, 41)]
for i in range(40):
    m2.el.append(("frame", ids[i], ids[i + 1], E_C * PYL["A"], E_C * PYL["I"], PYL["m"]))
m2.finish()
f, _ = m2.modes(list(m2.dof[ids[0]]), 1)
fcant = 1.875104068711961 ** 2 / (2 * np.pi * (HP + HB) ** 2) * np.sqrt(E_C * PYL["I"] / PYL["m"])
say(f"  free standing pylon ({HP+HB:.0f} m cantilever): f1 {f[0]:.5f} Hz, closed form {fcant:.5f} Hz ({f[0]/fcant-1:+.1e})")
say("")
say("CHECK 2: the bridge, mesh convergence of its first frequencies")
for h in (4.0, 2.0, 1.0):
    md, xs, deck, pylons, stays, fixed = bridge(h)
    f, V = md.modes(fixed, 6)
    say(f"  elements of {h:.0f} m: " + ", ".join(f"{v:.4f}" for v in f) + " Hz")
md, xs, deck, pylons, stays, fixed = bridge(2.0)
f, V = md.modes(fixed, 6)
say("  the 2 m mesh is drawn. Mode 1, the first vertical bending of the deck, symmetric:")
v = V[md.dof[deck, 1], 0]; u = V[md.dof[deck, 0], 0]
main = (xs > XP[0]) & (xs < XP[1])
say(f"  f1 = {f[0]:.4f} Hz; deck vertical share of its motion {np.sum(v**2)/(np.sum(v**2)+np.sum(u**2)):.3f};"
    f" symmetry of the main span {np.corrcoef(v[main], v[main][::-1])[0,1]:+.4f}")
say(f"  (then f2 = {f[1]:.4f} Hz, antisymmetric)")
F1 = f[0]
mode = V[:, 0] / np.abs(V[md.dof[deck, 1], 0]).max()
if mode[md.dof[deck[int(np.argmin(np.abs(xs - TOT / 2)))], 1]] > 0:
    mode = -mode                                  # midspan sags first (v < 0 is down)

# ------------------------------------------------------------------ detail A: A0 in the flange
TH = 0.012                                        # plate thickness (m)
NU = 0.29
CL = np.sqrt(E_S * (1 - NU) / (RHO_S * (1 + NU) * (1 - 2 * NU)))
CT = np.sqrt(E_S / (2 * RHO_S * (1 + NU)))
F0, NCYC = 200e3, 3
X_T, X_C = -0.026, 0.020                          # transducer and crack, in the detail (m)
R_CRACK = 0.5                                     # the crack's reflection, assumed; T = sqrt(1 - R^2)
# Rayleigh speed
xr = brentq(lambda x: x ** 6 - 8 * x ** 4 + 8 * (3 - 2 * (1 - 2 * NU) / (2 - 2 * NU)) * x ** 2
            - 16 * (1 - (1 - 2 * NU) / (2 - 2 * NU)), 0.5, 0.99)
CR = xr * CT


def a0_cp(fr):
    """A0 phase velocity at fr: the antisymmetric Rayleigh-Lamb equation. A0 stays below the
    Rayleigh speed (so below c_T and c_L), where p = i alpha, q = i beta and the equation reads
    (k^2 + beta^2)^2 tanh(alpha h) = 4 k^2 alpha beta tanh(beta h), here divided by k^4."""
    w, h = 2 * np.pi * fr, TH / 2

    def F(c):
        k = w / c
        a, b = np.sqrt(k * k - (w / CL) ** 2) / k, np.sqrt(k * k - (w / CT) ** 2) / k
        return (1 + b * b) ** 2 * np.tanh(a * k * h) - 4 * a * b * np.tanh(b * k * h)

    cs = np.r_[np.linspace(0.02 * CR, 0.999 * CR, 6000), CR * (1 - np.geomspace(1e-3, 1e-13, 400))]
    vals = np.array([F(c) for c in cs])
    i = np.where(np.sign(vals[:-1]) != np.sign(vals[1:]))[0][0]
    return brentq(F, cs[i], cs[i + 1], xtol=1e-13)


freqs = np.linspace(20e3, 460e3, 89)
cps = np.array([a0_cp(fr) for fr in freqs])
ks = 2 * np.pi * freqs / cps
# Kirchhoff plate at low frequency: c = (w^2 D / rho h)^(1/4)
Dp = E_S * TH ** 3 / (12 * (1 - NU ** 2))
ckirch = lambda fr: (2 * np.pi * fr) ** 0.5 * (Dp / (RHO_S * TH)) ** 0.25
say("")
say("DETAIL A MODEL")
say(f"  the box girder's bottom flange, steel plate {TH*1e3:.0f} mm: c_L = {CL:.1f} m/s, c_T = {CT:.1f} m/s,"
    f" c_R = {CR:.1f} m/s")
say(f"  a {NCYC} cycle Hann burst at {F0/1e3:.0f} kHz from a transducer on the plate launches A0 both ways;")
say(f"  its displacement is the Fourier synthesis over {len(freqs)} frequencies of the exact A0 branch")
say(f"  of the Rayleigh-Lamb equation. A crack {X_C-X_T:.3f} m on reflects R = {R_CRACK} (assumed; no mode"
    f" conversion), passes T = sqrt(1 - R^2) = {np.sqrt(1-R_CRACK**2):.3f}.")
say("")
say("CHECK 3: the A0 branch against its limits")
for fr in (0.5e3, 1e3, 2e3):
    c = a0_cp(fr)
    say(f"  {fr/1e3:3.1f} kHz: c_A0 = {c:.3f} m/s, Kirchhoff plate {ckirch(fr):.3f} m/s ({c/ckirch(fr)-1:+.1e})")
for fr in (0.5e6, 1e6):
    c_hi = a0_cp(fr)
    say(f"  {fr/1e6:.1f} MHz (f d = {fr/1e6*TH*1e3:.0f} MHz mm): c_A0 = {c_hi:.3f} m/s, Rayleigh speed {CR:.3f} m/s"
        f" ({c_hi/CR-1:+.1e})")
i0 = int(np.argmin(np.abs(freqs - F0)))
cg = 2 * np.pi * (freqs[i0 + 1] - freqs[i0 - 1]) / (ks[i0 + 1] - ks[i0 - 1])
say(f"  at {F0/1e3:.0f} kHz: c_p = {cps[i0]:.1f} m/s, c_g = {cg:.1f} m/s, wavelength {cps[i0]/F0*1e3:.2f} mm")

# the burst's spectrum, sampled on the same frequencies
T_B = NCYC / F0
tt = np.linspace(0, T_B, 4001)
burst = np.sin(np.pi * tt / T_B) ** 2 * np.sin(2 * np.pi * F0 * tt)
spec = np.array([np.trapezoid(burst * np.exp(-2j * np.pi * fr * tt), tt) for fr in freqs])
df = freqs[1] - freqs[0]
amp = 2 * np.conj(spec) * df                       # u(x, t) = Re sum amp e^{i (k x - w t)}
# the synthesised packet at the transducer, against the burst itself
tchk = np.linspace(-5e-6, T_B + 5e-6, 800)
syn = np.real(np.exp(-2j * np.pi * np.outer(tchk, freqs)) @ amp)
ref = np.where((tchk > 0) & (tchk < T_B), np.sin(np.pi * tchk / T_B) ** 2 * np.sin(2 * np.pi * F0 * tchk), 0)
say(f"  the {len(freqs)} components rebuild the burst at the source to {np.abs(syn-ref).max()/np.abs(ref).max():.1e}"
    f" of its peak (the spectrum outside 20 to 460 kHz is below {np.abs(spec[[0,-1]]).max()/np.abs(spec).max():.1e})")
P_W = 80e-6                                       # the wave loop (model seconds)
SLOW_W = 4.0e4


def field(x, t):
    """u_z at x (m) and t (s after the burst leaves), incident both ways, echo, transmitted."""
    e = lambda d: np.real(np.exp(1j * (np.outer(d, ks) - 2 * np.pi * freqs * t)) @ amp)
    x = np.asarray(x, float)
    inc = e(np.abs(x - X_T))
    ech = R_CRACK * e((X_C - X_T) + (X_C - x))
    tra = np.sqrt(1 - R_CRACK ** 2) * e(x - X_T)
    return np.where(x < X_C, inc + ech * (x < X_C), tra)


xd = np.linspace(-0.042, 0.042, 161)
peak = max(np.abs(field(xd, t)).max() for t in np.linspace(0, P_W, 81))
resid = np.abs(field(xd, P_W)).max() / peak
say(f"  the loop: {P_W*1e6:.0f} us; what is left in the view when the next burst leaves: {resid:.1e} of the peak")
say("")
say("DRAWING")
say(f"  bridge 1.2 units per metre; the mode's largest deck deflection drawn 9 units; real time ({F1:.3f} Hz).")
say(f"  detail A: 2.5 units per mm; the plate's u_z drawn 6 units at most and through the diverging palette;")
say(f"  shown {SLOW_W:,.0f} x slower, said in the detail (one burst every {P_W*SLOW_W:.1f} s on screen); the bridge in real time.")
wt_lib.write_check(NAME, lines)

# ------------------------------------------------------------------ data for the page
xy = np.array(md.xy)
nodes_deck = [[float(xs[i]), float(mode[md.dof[n, 0]]), float(mode[md.dof[n, 1]])] for i, n in enumerate(deck)]
pyl = [[[float(xy[n, 1]), float(mode[md.dof[n, 0]]), float(mode[md.dof[n, 1]])] for n in ids] for ids in pylons]
stay = []
for pn, dn in stays:
    stay.append([float(xy[pn, 0]), float(xy[pn, 1]), float(mode[md.dof[pn, 0]]), float(mode[md.dof[pn, 1]]),
                 float(xy[dn, 0]), float(mode[md.dof[dn, 0]]), float(mode[md.dof[dn, 1]])])
DATA = {
    "f1": F1, "tot": TOT, "xp": list(XP), "hp": HP, "hb": HB,
    "deck": nodes_deck[::2] + ([nodes_deck[-1]] if len(nodes_deck) % 2 == 0 else []),
    "pyl": [p[::3] + [p[-1]] for p in pyl], "stay": stay,
    "w": {"k": ks.tolist(), "f": freqs.tolist(), "ar": np.real(amp).tolist(), "ai": np.imag(amp).tolist(),
          "xt": X_T, "xc": X_C, "R": R_CRACK, "T": float(np.sqrt(1 - R_CRACK ** 2)), "P": P_W, "slow": SLOW_W,
          "slowtxt": f"shown {SLOW_W:,.0f} × slower",
          "peak": peak, "th": TH, "cg": float(cg), "tb": T_B},
}

JS = r"""
/* ---- the cover: W 1000, H 250 ---- */
const wrap = (s, P) => ((s % P) + P) % P;
const NARROW = () => (cv.clientWidth || W) < 480;   // a phone: strokes heavier, the few words left out
const SX = 1.2, X0 = 22, YD = 138;                      // units per metre, deck left end, deck level
const XB = x => X0 + x * SX, YB = y => YD - y * SX;     // bridge coordinates to the canvas
const AMP = 9;                                           // largest deck deflection drawn
const T0 = .3, T1 = 1 / DATA.f1;
const WV = DATA.w, NF = WV.f.length;
const CX = 872, CY = 120, CR = 106, DS = 2.5e3;         // detail circle, units per metre inside it
const XA = DATA.xp[0] + (DATA.xp[1] - DATA.xp[0]) / 2;   // detail A on the deck (m): the middle of the main span
const YE = 22;                                           // its leader's run to the circle, over the pylon tops
const POSTER_T = T0 + T1;                                // the deck back at full sag, the echo on its way
const W_OFF = 30e-6 * WV.slow - T1;                     // the wave loop's phase at T0: the still shows the echo on its way back
function q() { return t < T0 ? 1 : Math.cos(2 * Math.PI * DATA.f1 * (t - T0)); }   // from rest at full sag
function deckPts(Q) { return DATA.deck.map(([x, u, v]) => [XB(x) + AMP * Q * u, YD - AMP * Q * v]); }
function pylonPts(k, Q) { const xp = DATA.xp[k]; return DATA.pyl[k].map(([y, u, v]) => [XB(xp) + AMP * Q * u, YB(y) - AMP * Q * v]); }
function deckAt(x, Q) {                                  // deflected deck point at x (m)
  const D = DATA.deck; let i = 1; while (i < D.length - 1 && D[i][0] < x) i++;
  const s = (x - D[i - 1][0]) / (D[i][0] - D[i - 1][0]);
  return [XB(x) + AMP * Q * lerp(D[i - 1][1], D[i][1], s), YD - AMP * Q * lerp(D[i - 1][2], D[i][2], s)];
}
/* the landscape: water level, the embankments at both ends */
function land(a) {
  const yw = YB(-DATA.hb + 3), xl = XB(0), xr = XB(DATA.tot), yb = YB(-DATA.hb - 22);
  // the river bed, and the piles under each pile cap
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.rect(0, yb, W * .755, 12); ctx.clip();
  for (let x = -10; x < W; x += 7) line([[x, yb + 12], [x + 12, yb]], { color: C.rule, width: .9 });
  ctx.restore();
  line([[0, yb], [W * .755, yb]], { color: C.ink, width: 1.1, alpha: a });
  for (const xp of DATA.xp) for (const dx of [-9, 0, 9]) line([[XB(xp) + dx, YB(-DATA.hb) + 7], [XB(xp) + dx, yb + 8]], { color: C.ink, width: 1, alpha: a });
  line([[0, yw], [W * .755, yw]], { color: C.sky, width: 1.1, alpha: a });
  for (const [x0, x1] of [[40, 70], [300, 330], [575, 605]]) line([[x0, yw + 6], [x1, yw + 6]], { color: C.sky, width: 1, alpha: a * .8 });
  // the water level mark, as drawings carry it
  const xm = 250; line([[xm - 6, yw - 9], [xm + 6, yw - 9], [xm, yw - 1]], { color: C.navy, width: 1.1, fill: '#fff', close: true, alpha: a });
  for (const [side, xa] of [[-1, xl], [1, xr]]) {
    const top = YD + 3, toe = yw;
    const poly = side < 0 ? [[0, top], [xa + 4, top], [xa + 34, toe], [0, toe]] : [[W * .75, top], [xa - 4, top], [xa - 34, toe], [W * .75, toe]];
    const clipTo = side < 0 ? poly : [[xa - 4, top], [xa + 40, top], [xa + 40, toe], [xa - 34, toe]];
    ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); clipTo.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.closePath(); ctx.clip();
    for (let x = -60; x < W; x += 7) line([[x, toe + 2], [x + toe - top, top - 2]], { color: C.rule, width: .9 });
    ctx.restore();
    line(side < 0 ? [[0, top], [xa + 4, top], [xa + 34, toe]] : [[xa + 40, top], [xa - 4, top], [xa - 34, toe]], { color: C.ink, width: 1.2, alpha: a });
  }
}
function pylon(k, Q, p, a) {                            // tapered shaft (drawn in from its foot), crossbeam, pile cap
  const P = pylonPts(k, Q), n = P.length;
  const wBot = 11 * SX * .75, wTop = 5.5 * SX * .75;
  const L = [], R = [];
  for (let i = 0; i < n; i++) { const s = i / (n - 1), hw = lerp(wBot, wTop, s) / 2; L.push([P[i][0] - hw, P[i][1]]); R.push([P[i][0] + hw, P[i][1]]); }
  const upto = Math.max(1, Math.round(p * (n - 1)));
  const out = L.slice(0, upto + 1).concat(R.slice(0, upto + 1).reverse());
  line(out, { color: C.ink, width: 1.3, fill: C.steel, close: true, alpha: a });
  const [xc, yc] = P[0];
  line([[xc - 13, yc], [xc + 13, yc], [xc + 13, yc + 7], [xc - 13, yc + 7]], { color: C.ink, width: 1.2, fill: C.steel2, close: true, alpha: a });
}
function sensor(x, Q, a) { const [px, py] = deckAt(x, Q); line([[px - 3.5, py - 3], [px + 3.5, py - 3], [px + 3.5, py - 10], [px - 3.5, py - 10]], { color: C.navy, width: 1, fill: C.navy, close: true, alpha: a }); }
/* detail A: the flange plate, the transducer, the crack, A0 */
const NXD = 150;
const re = new Float32Array(NF), im = new Float32Array(NF), UZ = new Float32Array(NXD);
function wave(tw) {                                      // u_z / peak on NXD points across the detail
  for (let m = 0; m < NF; m++) { const ph = -2 * Math.PI * WV.f[m] * tw; re[m] = Math.cos(ph); im[m] = Math.sin(ph); }
  const e = d => { let s = 0; for (let m = 0; m < NF; m++) { const kd = WV.k[m] * d, c = Math.cos(kd), sn = Math.sin(kd);
    const zr = c * re[m] - sn * im[m], zi = c * im[m] + sn * re[m]; s += WV.ar[m] * zr - WV.ai[m] * zi; } return s; };
  for (let i = 0; i < NXD; i++) {
    const x = (i / (NXD - 1) - .5) * 2 * CR / DS;
    UZ[i] = (x < WV.xc ? e(Math.abs(x - WV.xt)) + WV.R * e((WV.xc - WV.xt) + (WV.xc - x)) : WV.T * e(x - WV.xt)) / WV.peak;
  }
}
function detail(a, tw) {
  if (a <= 0) return;
  const r = CR * (.94 + .06 * a);
  ctx.save(); ctx.globalAlpha *= a;
  ctx.beginPath(); ctx.arc(CX, CY, r, 0, 2 * Math.PI); ctx.fillStyle = '#fff'; ctx.fill(); ctx.clip();
  const th = WV.th * DS, yp = CY + 14, X = x => CX + x * DS;
  wave(tw);
  const dx = 2 * CR / (NXD - 1), top = [], bot = [];
  for (let i = 0; i < NXD; i++) {
    const x = CX - CR + i * dx, dz = -6 * UZ[i];
    ctx.fillStyle = Math.abs(UZ[i]) < .01 ? C.steel : diverging(clamp(UZ[i] * 1.6, -1, 1));
    ctx.fillRect(x - dx / 2, yp - th / 2 + dz, dx + .7, th);
    top.push([x, yp - th / 2 + dz]); bot.push([x, yp + th / 2 + dz]);
  }
  line(top, { color: C.ink, width: 1.4 }); line(bot, { color: C.ink, width: 1.4 });
  // the crack: a notch up from the lower face, where the web's weld would be
  const xc = X(WV.xc), ic = Math.round((xc - (CX - CR)) / dx), dzc = -6 * UZ[Math.max(0, Math.min(NXD - 1, ic))];
  line([[xc - 2.2, yp + th / 2 + dzc], [xc, yp + th / 2 - th * .45 + dzc], [xc + 2.2, yp + th / 2 + dzc]], { color: '#781E2C', width: 1.2, fill: C.accent, close: true });
  // the echo, the one thing to follow: an arrow over it while it runs back
  const tHit = (WV.xc - WV.xt) / WV.cg + WV.tb / 2, xe = WV.xc - WV.cg * (tw - tHit);
  const ea = clamp((xe - WV.xt - .010) / .006) * clamp((WV.xc - .004 - xe) / .004);
  if (ea > 0) arrow(X(xe) + 11, yp - th / 2 - 14, X(xe) - 11, yp - th / 2 - 14, { color: C.accent, width: 1.6, head: 8, alpha: ea });
  // the transducer on the upper face
  const xt = X(WV.xt), it = Math.round((xt - (CX - CR)) / dx), dzt = -6 * UZ[Math.max(0, Math.min(NXD - 1, it))];
  line([[xt - 10, yp - th / 2 + dzt], [xt + 10, yp - th / 2 + dzt], [xt + 10, yp - th / 2 - 13 + dzt], [xt - 10, yp - th / 2 - 13 + dzt]], { color: C.navy, width: 1, fill: C.navy, close: true });
  ctx.restore();
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.arc(CX, CY, r, 0, 2 * Math.PI); ctx.lineWidth = 1.3; ctx.strokeStyle = C.ink; ctx.stroke(); ctx.restore();
}
function draw() {
  const Q = q();
  const aL = seg(0, .25);
  land(aL);
  // the deck's rest line, dashed, and the deck
  line([[XB(0), YD], [XB(DATA.tot), YD]], { color: C.guide, width: 1, dash: [5, 4], alpha: aL * .8 });
  // pylons rise from their feet
  for (let k = 0; k < 2; k++) pylon(k, Q, seg(.01 + .02 * k, .2), aL);
  // stays: each pylon's fan drawn down from its anchors, stay by stay
  DATA.stay.forEach(([xp, yp, up, vp, xd, ud, vd], i) => {
    const p = seg(.17 + .006 * Math.floor((i % 22) / 2), .2);    // once the pylons stand: both fans, anchor by anchor
    if (p <= 0) return;
    const a = [XB(xp) + AMP * Q * up, YB(yp) - AMP * Q * vp], b = [XB(xd) + AMP * Q * ud, YD - AMP * Q * vd];
    line([a, b], { color: C.ink, width: NARROW() ? 1.7 : .9, progress: p });
  });
  const dp = deckPts(Q);
  const lo = dp.map(([x, y]) => [x, y + 2.2]), hi = dp.map(([x, y]) => [x, y - 2.2]).reverse();
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, XB(0) + (XB(DATA.tot) - XB(0) + 6) * seg(0, .3), H); ctx.clip();
  line(lo.concat(hi), { color: C.ink, width: 1.3, fill: C.steel2, close: true });
  ctx.restore();
  // accelerometers on the deck: mid side spans, the main span's quarter points
  // (its middle is detail A's)
  const aS = settle(.2, .28);
  for (const x of [65, 205, 355, 495]) sensor(x, Q, aS);
  // detail A: the flange at the NDT scale
  const aD = settle(.15, .28);
  const [ax, ay] = deckAt(XA, Q);
  ctx.save(); ctx.globalAlpha *= aD; ctx.beginPath(); ctx.arc(ax, ay + 1, 9, 0, 2 * Math.PI); ctx.lineWidth = 1.2; ctx.strokeStyle = C.ink; ctx.stroke(); ctx.restore();
  // the leader: up from A between the two fans of stays, then over the
  // pylon tops to the circle (a straight line would cross the right pylon)
  const ex = CX - Math.sqrt(CR * CR - (CY - YE) * (CY - YE));
  line([[ax, ay - 8], [ax, YE], [ex, YE]], { color: C.ink, width: 1, progress: seg(.15, .25) });
  const tw = t < T0 ? W_OFF / WV.slow : wrap((t - T0 + W_OFF) / WV.slow, WV.P);
  detail(aD, tw);
  // the few words: the mode's frequency, the wave's
  const aT = settle(.25, .28) * (NARROW() ? 0 : 1);
  math('f_1 = ' + DATA.f1.toFixed(2) + '\\,\\rm{Hz}', XB(220), 58, { size: 19, color: C.body, align: 'center', alpha: aT });
  const yd = YD + 25, spans = [[0, DATA.xp[0]], [DATA.xp[0], DATA.xp[1]], [DATA.xp[1], DATA.tot]];
  spans.forEach(([a0, a1]) => dim(XB(a0) + 1, XB(a1) - 1, yd, (a1 - a0).toFixed(0) + '\\,\\rm{m}', { size: 16, alpha: aT * .9, color: C.body }));
  text('A', ax + 7, ay - 22, { size: 17, italic: true, color: C.ink, alpha: aT });
  text('A', CX - CR * .78 - 14, CY - CR * .66, { size: 17, italic: true, color: C.ink, alpha: aT });
  math('A_0,\\ 200\\,\\rm{kHz}', CX, CY + CR - 20, { size: 17, color: C.body, align: 'center', alpha: aT });
  // the wave is slowed (the bridge beside it runs in real time): said, as every figure of the guide says it
  text(WV.slowtxt, CX, CY + CR - 46, { size: 15, color: C.muted, align: 'center', alpha: aT });
}
boot();
"""

TITLE = "A cable stayed bridge, its first mode and a guided wave"
ARIA = ("A cable stayed bridge in elevation, its deck and pylons breathing in their first vertical "
        "mode with accelerometers on the deck; a detail circle magnifies the steel flange, where "
        "an ultrasonic guided wave travels and a crack sends part of it back.")

if __name__ == "__main__":
    print(wt_lib.publish(NAME, TITLE, ARIA, DATA, JS, w=1000, h=250, px=672, cell=False))
