"""Figure 2: occurrence of resonance modes.

Model: a steel Euler-Bernoulli bar, harmonic point force F e^{i w t} at
x_F, light hysteretic damping (EI -> EI(1 + i eta)).
  (a) infinite beam: the exact Green's function,
      w_inf(x) = -F (i e^{-ik|x-x_F|} + e^{-k|x-x_F|}) / (4 EI k^3);
  (b) its response relative to itself is 1 at every frequency: flat;
  (c) the same force on a simply supported span L: exact response from the
      closed form field transfer matrices (beam_model), drawn on the page
      from its modal sum (60 modes, checked against the exact solution);
  (d) |w(x_F)/w_inf(x_F)| in dB: what the supports' reflections add, peaks at
      the simply supported frequencies (n pi/L)^2 sqrt(EI/m)/2 pi;
  (e), (f) the 4th mode as two counter travelling waves and their sum,
      sin(kx) cos(wt) = [sin(kx - wt) + sin(kx + wt)]/2, exact;
  (g) the first four mode shapes (beam_model, against sin(n pi x/L)).
A frequency sweep, a pure function of the clock, moves along the computed
curves and rests at every resonance, slowing into it (29 Sep: hold the
simulation on the peaks); every panel shows the steady state at the current
frequency.

Run: python tools/numfig/resonance.py
"""
import os

import numpy as np
from scipy.optimize import brentq, minimize_scalar

import beam_model as bm
import common

NAME = "resonance"
HERE = os.path.dirname(os.path.abspath(__file__))

E, RHO, B, HT = 210e9, 7850.0, 0.040, 0.010
EI = E * B * HT ** 3 / 12                 # 700 N m^2
M = RHO * B * HT                          # 3.14 kg/m
L, XF, ETA = 1.0, 0.13, 0.05
NMODE = 60
SLOW = 200
FLO, FHI = 10.0, 500.0
TS, RAMP = 0.35, 0.25                     # the page's physics clock (Round 2)

fn = np.array([bm.freq_from_z(n * np.pi, L, EI, M) for n in range(1, 5)])


def kc(f, eta=ETA):
    return (M * (2 * np.pi * f) ** 2 / (EI * (1 + 1j * eta))) ** 0.25


def alpha_fin(x, f, eta=ETA):
    """Exact receptance w(x)/F of the simply supported span, force at XF."""
    EIc, k = EI * (1 + 1j * eta), kc(f, eta)
    F1, F2 = bm.field(XF, k, EIc), bm.field(L - XF, k, EIc)
    e4 = np.array([0, 0, 0, 1.0])
    a, c = F2 @ F1, F2 @ e4
    th, Q = np.linalg.solve(np.array([[a[0, 1], a[0, 3]], [a[2, 1], a[2, 3]]]), -np.array([c[0], c[2]]))
    y0 = np.array([0, th, 0, Q])
    yF = F1 @ y0 + e4
    return np.array([(bm.field(v, k, EIc) @ y0)[0] if v <= XF else (bm.field(v - XF, k, EIc) @ yF)[0]
                     for v in np.atleast_1d(x)])


def alpha_inf(f, eta=ETA, r=0.0):
    k = kc(f, eta)
    return -(1j * np.exp(-1j * k * abs(r)) + np.exp(-k * abs(r))) / (4 * EI * (1 + 1j * eta) * k ** 3)


def alpha_modal(x, f, eta=ETA, N=NMODE):
    n = np.arange(1, N + 1)
    wn2 = (n * np.pi / L) ** 4 * EI / M
    den = (M * L / 2) * (wn2 * (1 + 1j * eta) - (2 * np.pi * f) ** 2)
    return np.array([np.sum(np.sin(n * np.pi * v / L) * np.sin(n * np.pi * XF / L) / den) for v in np.atleast_1d(x)])


# ------------------------------------------------------------------ the curve of (d)
lf = np.linspace(np.log10(FLO), np.log10(FHI), 700)
lf = np.unique(np.concatenate([lf] + [np.log10(f) + np.linspace(-0.03, 0.03, 61) for f in fn]))
H = np.array([alpha_fin(XF, 10 ** v)[0] / alpha_inf(10 ** v) for v in lf])
dB = 20 * np.log10(np.abs(H))

# peaks of |w/w_inf| near each f_n, and of |w| itself
peaks = [minimize_scalar(lambda v: -abs(alpha_fin(XF, 10 ** v)[0] / alpha_inf(10 ** v)),
                         bounds=(np.log10(f) - 0.05, np.log10(f) + 0.05), method="bounded",
                         options={"xatol": 1e-10}).x for f in fn]
peaks_w = [minimize_scalar(lambda v: -abs(alpha_fin(XF, 10 ** v)[0]),
                           bounds=(np.log10(f) - 0.05, np.log10(f) + 0.05), method="bounded",
                           options={"xatol": 1e-10}).x for f in fn]

# the display scale of (c): the largest |w(x)/w_inf(x_F)| over the sweep
xs = np.linspace(0, L, 101)
G = max(np.max(np.abs(alpha_fin(xs, 10 ** p) / alpha_inf(10 ** p))) for p in peaks)

# ------------------------------------------------------------------ the sweep, a pure function of t
# log f glides from FLO to FHI and back and RESTS at every resonance f_n on the
# way (29 Sep: "peakler uzerinde uzun tut", hold the simulation on the peaks):
# it slows into f_n, so the steady state is seen building up the peak, holds
# there, then moves on. Each glide is eased (slow arrival: a Beta(2, 4) ramp)
# in a coordinate u stretched ten times within about +-0.03 decades of each
# f_n, where the steady state grows fastest.
lu = np.linspace(np.log10(FLO) + 0.02, np.log10(FHI) - 0.02, 4001)
wgt = 1 + 9.0 * sum(np.exp(-((lu - np.log10(f)) / 0.03) ** 2) for f in fn)
U = np.concatenate([[0], np.cumsum(0.5 * (wgt[1:] + wgt[:-1]) * np.diff(lu))])
U /= U[-1]
HALF1 = SLOW / (2 * fn[0])                          # half a period of mode 1 on screen (4.26 s)
KEY = [lu[0]] + list(np.log10(fn)) + [lu[-1]]       # the stops: the low end, f1 ... f4, the high end
UKEY = np.interp(KEY, lu, U)
GLIDE = [1.4, 2.0, 1.8, 1.7, 1.2]                   # s on screen: low end -> f1, f1 -> f2, ..., f4 -> high end
DWELL = [HALF1, 2.6, 2.6, 2.6]                      # s at f1 ... f4 (f1 moves so slowly: half its period, a full swing)
REST = [0.2, 0.6, 0.4]                              # s at the low end first, at the high end, at the low end last


def ramp(x):
    """The glide's ease: Beta(2, 4)'s distribution function, 0 to 1, still at both
    ends and slowest on arrival (the last tenth of the way takes two fifths of the time)."""
    return 1 - (1 - x) ** 5 - 5 * x * (1 - x) ** 4


SCHED = [("rest", REST[0], 0)]                      # (kind, seconds, stop or (from, to))
for k in range(4):
    SCHED += [("glide", GLIDE[k], (k, k + 1)), ("dwell", DWELL[k], k + 1)]
SCHED += [("glide", GLIDE[4], (4, 5)), ("rest", REST[1], 5), ("glide", GLIDE[4], (5, 4))]
for k in range(3, -1, -1):
    SCHED += [("dwell", DWELL[k], k + 1), ("glide", GLIDE[k], (k + 1, k))]
SCHED += [("rest", REST[2], 0)]
TSW = sum(s[1] for s in SCHED)                      # one period of the sweep, on screen seconds
EDGES = np.concatenate([[0], np.cumsum([s[1] for s in SCHED])])


def sweep_lf(c):
    """log10 f at physics clock c (s), any c >= 0: the schedule above, periodic."""
    c = np.atleast_1d(np.asarray(c, float)) % TSW
    out = np.empty_like(c)
    for (kind, d, a), t0 in zip(SCHED, EDGES):
        m = (c >= t0) & (c <= t0 + d)
        if kind == "glide":
            out[m] = np.interp(UKEY[a[0]] + (UKEY[a[1]] - UKEY[a[0]]) * ramp((c[m] - t0) / d), U, lu)
        else:
            out[m] = KEY[a]
    return out


C_P = 4 * HALF1                                     # the still, on the physics clock: 4 half periods of mode 1,
POSTER = TS + RAMP / 2 + C_P                        # inside the dwell at f4 (clock(t) = t - TS - RAMP/2 after the ramp)
d4 = [t0 for (kind, d, a), t0 in zip(SCHED, EDGES) if kind == "dwell" and a == 4][0]
assert d4 + 0.3 < C_P < d4 + DWELL[3] - 0.3, "the still must fall inside the dwell at f4"

# the sweep on a 1 ms grid, and the drive's phase: the integral of f over the clock / SLOW
NSUB = 16                                           # the page keeps every 16th point (16 ms)
NPG = int(np.ceil(TSW / (NSUB * 1e-3)))
ts_ = np.linspace(0, TSW, NPG * NSUB + 1)
lf_t = sweep_lf(ts_)
f_t = 10 ** lf_t
phi_t = np.concatenate([[0], np.cumsum(0.5 * (f_t[1:] + f_t[:-1]) * np.diff(ts_))]) * 2 * np.pi / SLOW
PHI_T = phi_t[-1]

# phase offset: at the still the finite beam's response at f4 is at its extreme
Z = alpha_fin(xs, fn[3]) / alpha_inf(fn[3])
jmax = int(np.argmax(np.abs(Z)))
phi_at_P = np.interp(C_P, ts_, phi_t)
PHI_OFF = -np.angle(Z[jmax]) - phi_at_P

# ------------------------------------------------------------------ checks
lines = []
say = lines.append
say("nf-resonance: Figure 2, occurrence of resonance modes")
say("")
say("MODEL")
say(f"  steel bar {B*1e3:.0f} x {HT*1e3:.0f} mm, E = {E/1e9:.0f} GPa, rho = {RHO:.0f} kg/m^3: EI = {EI:.1f} N m^2,"
    f" m = {M:.3f} kg/m; span L = {L} m, force at x_F = {XF} m")
say(f"  light hysteretic damping: EI -> EI (1 + i eta), eta = {ETA} (every mode zeta = eta/2 = {ETA/2})")
say("  (a) infinite beam, exact Green's function: w_inf(x) = -F (i e^{-ik|x-x_F|} + e^{-k|x-x_F|}) / (4 EI k^3)")
say("  (c) simply supported span, exact: closed form field transfer matrices (beam_model.field)")
say("      with the shear jump F at x_F; the page evaluates the modal sum of the same span")
say(f"      ({NMODE} modes, sin(n pi x/L), damping as above), checked against the exact solution below.")
say("  (b), (d): |w(x_F) / w_inf(x_F)| in dB; the infinite beam is 0 dB at every frequency (flat), the")
say("      span shows what the reflections from its supports add. (His 'flat spectrum' of the")
say(f"      infinite beam: its plain receptance falls as f^(-3/2), smoothly, with no peak.)")
say("")
say("CHECK 1: resonance peaks against the simply supported frequencies (n pi/L)^2 sqrt(EI/m) / 2 pi")
for n, (f, p, pw) in enumerate(zip(fn, peaks, peaks_w), 1):
    say(f"  f_{n} = {f:9.4f} Hz; peak of |w| at {10**pw:9.4f} Hz ({(10**pw/f-1)*100:+.3f} %),"
        f" of |w/w_inf| at {10**p:9.4f} Hz, height {20*np.log10(abs(alpha_fin(XF,10**p)[0]/alpha_inf(10**p))):5.2f} dB")
say("  (the peaks of |w| sit on f_n to within the other modes' pull, eta = 0.05 wide)")
say("")
say("CHECK 2: the infinite beam's receptance against a long span (40 m, force at mid span, eta = 0.2")
say("  so the far supports' reflections die: e^{2 Im(k) 20 m} < 1e-4), modal sum of 4000 modes")
for f in (50.0, 300.0):
    Lb, x0, eta = 40.0, 20.0, 0.2
    n = np.arange(1, 4001)
    wn2 = (n * np.pi / Lb) ** 4 * EI / M
    a = np.sum(np.sin(n * np.pi * x0 / Lb) ** 2 / ((M * Lb / 2) * (wn2 * (1 + 1j * eta) - (2 * np.pi * f) ** 2)))
    say(f"  f = {f:5.0f} Hz: long span / closed form = {a/alpha_inf(f, eta):.6f}")
say("")
say(f"CHECK 3: the page's modal sum ({NMODE} modes) against the exact span, max |difference| / max |w|")
for f in (15.0, 23.4527, 60.0, 211.08, 300.0, 480.0):
    ex, mo = alpha_fin(xs, f), alpha_modal(xs, f)
    say(f"  f = {f:8.3f} Hz: {np.max(np.abs(mo-ex))/np.max(np.abs(ex)):.1e}")
say("")
say("CHECK 4: mode shapes, beam_model (Wittrick-Williams, null vector) against sin(n pi x/L)")
cb = bm.ContinuousBeam([(L, EI, M)])
fcb = cb.frequencies(4)
for n in range(1, 5):
    _, ws, _ = cb.mode(fcb[n - 1], 201)
    s = np.sin(n * np.pi * np.linspace(0, 1, 201))
    w = ws[0] / np.max(np.abs(ws[0])) * np.sign(np.dot(ws[0], s))
    say(f"  mode {n}: f = {fcb[n-1]:.6f} Hz (closed form {fn[n-1]:.6f}), max |shape difference| {np.max(np.abs(w - s)):.1e}")
say("")
say("CHECK 5: at each resonance the forced shape is the mode (MAC of w(x) at the peak with sin(n pi x/L))")
for n, p in enumerate(peaks_w, 1):
    w = alpha_fin(xs, 10 ** p)
    s = np.sin(n * np.pi * xs / L)
    mac = abs(np.vdot(s, w)) ** 2 / (np.vdot(s, s).real * np.vdot(w, w).real)
    say(f"  mode {n}: MAC = {mac:.5f}")
say("")
say("(e), (f): sin(k4 x) cos(w4 t) = [sin(k4 x - w4 t) + sin(k4 x + w4 t)] / 2, exact: the 4th mode is two")
say("  equal waves travelling in opposite directions, k4 = 4 pi / L (four half wavelengths in L).")
say("")
say("SWEEP AND TIME")
say(f"  shown {SLOW} x slower (the page says so); the drive's phase is the integral of f(t)/{SLOW} (a sweep, not a jump)")
say(f"  sweep: log f from {10 ** KEY[0]:.1f} to {10 ** KEY[-1]:.0f} Hz and back, period {TSW:.2f} s on screen; it rests at")
say("  every resonance on the way up and on the way down (29 Sep: hold the simulation on the peaks).")
say(f"  Glides {GLIDE} s, eased (Beta(2, 4): still at both ends, slowest on arrival) in a")
say("  coordinate stretched ten times within about 0.03 decades of each f_n; dwells at f1 ... f4")
say(f"  {', '.join(f'{d:.2f}' for d in DWELL)} s (at f1 half the mode's slow period, {2 * HALF1:.1f} s on screen, so it swings")
say("  once from one extreme to the other). Each frame is the steady state at the frequency of the")
say("  moment (the aria text says so), so arriving at f_n the response is seen building up")
say("  the peak of (d): the curve's value against the time left before the dwell, on the way up:")
dB_t = np.interp(lf_t, lf, dB)
for n in range(4):
    t0 = [t0 for (kind, d, a), t0 in zip(SCHED, EDGES) if kind == "dwell" and a == n + 1][0]
    pk = np.interp(np.log10(fn[n]), lf, dB)
    rise = []
    for drop in (20, 10, 3):
        below = np.nonzero((ts_ < t0) & (dB_t < pk - drop))[0]
        rise.append(t0 - ts_[below[-1]])
    say(f"    f{n + 1} = {fn[n]:7.2f} Hz ({pk:5.2f} dB), dwell {t0:5.2f} to {t0 + DWELL[n]:5.2f} s: within 20, 10, 3 dB"
        f" of it for the last {rise[0]:.2f}, {rise[1]:.2f}, {rise[2]:.2f} s")
say(f"  The still: f4, {C_P - d4:.2f} s into its dwell on the way up, t = {POSTER:.3f} s: 4 half periods of mode 1 after")
say("  the physics clock starts (TS = 0.35 s, eased over 0.25 s), when every mode in (g) and the span")
say("  in (c) are at an extreme (and at the clock's start every mode in (g) is at an extreme too).")
# the page's tables: every 16th point of the 1 ms grid, linear between them
e_lf = np.abs(np.interp(ts_, ts_[::NSUB], np.float32(lf_t[::NSUB])) - lf_t).max()
e_ph = np.abs(np.interp(ts_, ts_[::NSUB], np.float32(phi_t[::NSUB])) - phi_t).max()
fine = np.linspace(0, TSW, 8 * NPG * NSUB + 1)
f_f = 10 ** sweep_lf(fine)
phi_f = np.concatenate([[0], np.cumsum(0.5 * (f_f[1:] + f_f[:-1]) * np.diff(fine))]) * 2 * np.pi / SLOW
say(f"  The page's tables (16 ms, float32, linear between): log f within {e_lf:.1e} decades, the phase")
say(f"  within {e_ph:.1e} rad of the 1 ms grid's; the 1 ms trapezoid phase against 0.125 ms over a whole")
say(f"  period: {abs(phi_f[-1] - PHI_T):.1e} rad of {PHI_T:.1f}.")
say(f"  display scale of (c): G = max over the peaks of |w(x)/w_inf(x_F)| = {G:.3f}")
check = "\n".join(lines) + "\n"
print(check)
with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(check)

# ------------------------------------------------------------------ data
DATA = {
    "slow": SLOW, "L": L, "xF": XF, "eta": ETA, "EI": EI, "m": M, "N": NMODE,
    "fn": fn,
    "lf": lf, "dB": dB, "G": G,
    "sweep": {"T": TSW, "lf": common.f32(lf_t[::NSUB]), "phi": common.f32(phi_t[::NSUB]), "PHI": PHI_T,
              "off": PHI_OFF},
    "pk": [20 * np.log10(abs(alpha_fin(XF, 10 ** p)[0] / alpha_inf(10 ** p))) for p in peaks],
}

JS = r"""
const POSTER_T = __POSTER_T__;
const SLOW = DATA.slow, TS = __TS__, RAMP = __RAMP__, TP = POSTER_T;
function clock() { const s = t - TS; return s <= 0 ? 0 : s < RAMP ? s * s / (2 * RAMP) : s - RAMP / 2; }
const lab = t0 => settle(t0, .28);
/* the sweep (resonance.py): log f and the drive's phase, the integral of f/SLOW,
   every 16 ms of one period, linear between. It glides and rests at every f_n,
   on the way up and on the way down, slowing into each (the peaks held) */
const SW = DATA.sweep, SLF = b64f32(SW.lf), SPH = b64f32(SW.phi), NS = SLF.length - 1;
function sweepAt(c) {
  const n = Math.floor(c / SW.T), r = (c - n * SW.T) / SW.T * NS, i = Math.min(NS - 1, Math.floor(r)), s = r - i;
  return [lerp(SLF[i], SLF[i + 1], s), n * SW.PHI + lerp(SPH[i], SPH[i + 1], s) + SW.off];
}
const cRel = () => clock() - __CP__;                      // 0 at the still
/* complex helpers */
const cm = (a, b) => [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]];
const cexp = (re, im) => { const e = Math.exp(re); return [e * Math.cos(im), e * Math.sin(im)]; };
const cpow = (z, p) => { const r = Math.hypot(z[0], z[1]), a = Math.atan2(z[1], z[0]); return [Math.pow(r, p) * Math.cos(a * p), Math.pow(r, p) * Math.sin(a * p)]; };
const C4 = cpow([1, DATA.eta], -0.25), C1Q = cpow([1, DATA.eta], 0.25);
const NM = DATA.N, WN2 = [], PHF = [];
for (let n = 1; n <= NM; n++) { WN2.push(Math.pow(n * Math.PI / DATA.L, 4) * DATA.EI / DATA.m); PHF.push(Math.sin(n * Math.PI * DATA.xF / DATA.L)); }
const NX = 121, XS = Array.from({ length: NX }, (_, i) => i / (NX - 1) * DATA.L);
const SIN = XS.map(x => Array.from({ length: NM }, (_, n) => Math.sin((n + 1) * Math.PI * x / DATA.L)));
function k0(f) { return Math.pow(DATA.m * Math.pow(2 * Math.PI * f, 2) / DATA.EI, .25); }
/* (c): w(x)/w_inf(x_F), the span's modal sum over the infinite beam's receptance */
function spanShape(f) {
  const w2 = Math.pow(2 * Math.PI * f, 2), Mn = DATA.m * DATA.L / 2, kk = k0(f);
  const g = cm([-4 * DATA.EI * kk * kk * kk * C1Q[0], -4 * DATA.EI * kk * kk * kk * C1Q[1]], [.5, -.5]);   // -4 EI k^3 (1+i eta)^(1/4) / (1+i)
  const inv = []; for (let n = 0; n < NM; n++) { const a = Mn * WN2[n] - Mn * w2, b = Mn * WN2[n] * DATA.eta, d = a * a + b * b; inv.push([PHF[n] * a / d, -PHF[n] * b / d]); }
  return XS.map((x, j) => { let re = 0, im = 0; for (let n = 0; n < NM; n++) { re += SIN[j][n] * inv[n][0]; im += SIN[j][n] * inv[n][1]; } return cm([re, im], g); });
}
/* (a): w_inf(x)/w_inf(x_F) = (i e^{-ik r} + e^{-k r}) / (1 + i) */
function infShape(f, xs) {
  const kk = k0(f), k = [kk * C4[0], kk * C4[1]];
  return xs.map(x => { const r = Math.abs(x - DATA.xF);
    const a = cexp(k[1] * r, -k[0] * r), b = cexp(-k[0] * r, -k[1] * r), s = [-a[1] + b[0], a[0] + b[1]];
    return cm(s, [.5, -.5]); });
}
const ORD = ['st', 'nd', 'rd', 'th'];
function nearMode(l) { for (let n = 0; n < 4; n++) if (Math.abs(l - Math.log10(DATA.fn[n])) < 0.045) return n; return -1; }
function sub(letter, x, y, words, a) { panel(letter, x, y, { alpha: a }); text(words, x + 36, y, { size: 18, color: C.body, alpha: a }); }
/* (b) and (d) share one dB scale; its top leaves room inside the frame for the peak labels */
const YLIM = [-36, 34];
const LX0 = 130, PXM = 320;                               // (a) and (c): the span from x = 130, 320 px per metre
const X = x => LX0 + x * PXM;

function draw() {
  const c = clock(), [lfNow, ph] = sweepAt(c), fNow = Math.pow(10, lfNow);
  const eph = [Math.cos(ph), Math.sin(ph)], nm = nearMode(lfNow);
  // ---------------------------------------------------------------- (a) infinite beam
  sub('a', 18, 34, 'waves in the infinite beam', lab(0));
  const ya = 108, xa0 = -0.19, xa1 = 1.12;
  line([[X(xa0), ya], [X(xa1), ya]], { color: C.ink, width: 1.8, progress: seg(0, .35) });
  for (const s of [-1, 1]) for (let k = 1; k <= 3; k++) dot(s < 0 ? X(xa0) - 7 * k : X(xa1) + 7 * k, ya, 1.5, { alpha: seg(.2, .2) });
  const xsA = Array.from({ length: 180 }, (_, i) => xa0 + i / 179 * (xa1 - xa0)), wa = infShape(fNow, xsA);
  line(xsA.map((x, i) => [X(x), ya - 24 * (wa[i][0] * eph[0] - wa[i][1] * eph[1])]), { color: C.blue, width: 2.4, progress: seg(.18, .4) });
  const fa = lab(.4);
  arrow(X(DATA.xF), ya - 58, X(DATA.xF), ya - 30, { width: 1.5, head: 8, alpha: fa });
  math('F\\,e^{i\\omega t}', X(DATA.xF) + 8, ya - 44, { size: 17, alpha: fa });
  arrow(X(.47), ya - 46, X(.79), ya - 46, { width: 1.3, head: 8, alpha: fa, color: C.body });
  arrow(X(.02), ya - 46, X(-.14), ya - 46, { width: 1.3, head: 8, alpha: fa, color: C.body });
  text('Direction of travel', X(.63), ya - 54, { size: 16, color: C.body, align: 'center', alpha: fa });
  // ---------------------------------------------------------------- (b) its response: flat
  sub('b', 18, 168, 'response of the infinite beam', lab(.04));
  const gb = axes({ x: 120, y: 188, w: 352, h: 58, xlim: [1, Math.log10(500)], ylim: YLIM,
    xticks: [1, Math.log10(20), Math.log10(50), 2, Math.log10(200), Math.log10(500)], yticks: [-30, 0, 20],
    xfmt: v => String(Math.round(Math.pow(10, v))), progress: seg(.04, .4), ylabel: '\\rm{dB}', ylabelGap: 46, tickSize: 16 });
  gb.inside(() => line([[gb.X(1), gb.Y(0)], [gb.X(3), gb.Y(0)]], { color: C.navy, width: 2.2, progress: seg(.25, .4) }));
  math('w = w_{\\infty}', gb.X(Math.log10(12)), gb.Y(0) - 7, { size: 17, color: C.navy, alpha: lab(.5) });
  const ma = lab(.55);
  if (c > 0 || ma > 0) dot(gb.X(lfNow), gb.Y(0), 4.2, { color: C.accent, fill: C.accent, alpha: ma });
  // ---------------------------------------------------------------- (c) finite beam
  sub('c', 18, 300, 'finite beam', lab(.08));
  // the span's largest excursion over the sweep is 40 units (Ac below): its label sits clear of it
  const yc = 356;
  const pc = seg(.08, .35);
  line([[X(0), yc], [X(DATA.L), yc]], { color: C.ink, width: 1.8, progress: pc });
  if (pc > 0) { pin(X(0), yc, { s: 12 }); pin(X(DATA.L), yc, { s: 12, alpha: clamp(pc * 4 - 3) }); }
  const ws = spanShape(fNow), Ac = 40 / DATA.G;
  line(XS.map((x, i) => [X(x), yc - Ac * (ws[i][0] * eph[0] - ws[i][1] * eph[1])]), { color: C.blue, width: 2.4, progress: seg(.25, .4) });
  const fc = lab(.45);
  arrow(X(DATA.xF), yc - 62, X(DATA.xF), yc - 42, { width: 1.5, head: 8, alpha: fc });
  math('F\\,e^{i\\omega t}', X(DATA.xF) + 8, yc - 48, { size: 17, alpha: fc });
  text('supported at both ends', X(.5), yc + 56, { size: 16, color: C.body, align: 'center', alpha: fc });
  // ---------------------------------------------------------------- (d) its response: peaks
  sub('d', 18, 438, 'response of the finite beam', lab(.12));
  const gd = axes({ x: 120, y: 458, w: 352, h: 142, xlim: [1, Math.log10(500)], ylim: YLIM,
    xticks: [1, Math.log10(20), Math.log10(50), 2, Math.log10(200), Math.log10(500)], yticks: [-30, -20, -10, 0, 10, 20],
    xfmt: v => String(Math.round(Math.pow(10, v))), progress: seg(.12, .4), grid: true, tickSize: 16,
    xlabel: '\\rm{frequency}\\ \\ f\\ (\\rm{Hz})', ylabel: '|w/w_{\\infty}|\\ (\\rm{dB})', ylabelGap: 52 });
  gd.inside(() => {
    line([[gd.X(1), gd.Y(0)], [gd.X(3), gd.Y(0)]], { color: C.guide, width: 1.1, dash: [5, 4], alpha: seg(.5, .3) });
    line(DATA.lf.map((v, i) => [gd.X(v), gd.Y(DATA.dB[i])]), { color: C.navy, width: 2.2, progress: seg(.3, .45) });
  });
  text('infinite beam', gd.X(Math.log10(46)), gd.Y(0) - 6, { size: 16, color: C.body, align: 'center', alpha: lab(.6) });
  DATA.fn.forEach((f, n) => {
    const a = lab(.55 + .05 * n), hot = n === nm, col = hot ? C.accent : C.ink;
    const px = gd.X(Math.log10(f)), py = gd.Y(DATA.pk[n]) - 11 - 4 * (1 - a), s = `f_{${n + 1}}`;
    // TikZ node[fill=white]: the peak's name hides the light grid behind it, never the curve below it
    const w = math(s, 0, -1e4, { size: 17, alpha: 0 });
    ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = '#fff'; ctx.fillRect(px - w / 2 - 2, py - 14, w + 4, 20); ctx.restore();
    math(s, px, py, { size: 17, align: 'center', color: col, alpha: a });
  });
  if (c > 0 || ma > 0) {
    let i = 1; while (i < DATA.lf.length - 1 && DATA.lf[i] < lfNow) i++;
    const v = lerp(DATA.dB[i - 1], DATA.dB[i], (lfNow - DATA.lf[i - 1]) / (DATA.lf[i] - DATA.lf[i - 1]));
    gd.inside(() => line([[gd.X(lfNow), gd.Y(-36)], [gd.X(lfNow), gd.Y(v)]], { color: C.accent, width: 1, alpha: .45 * ma }));
    dot(gd.X(lfNow), gd.Y(v), 4.2, { color: C.accent, fill: C.accent, alpha: ma });
    math(`f = ${fNow < 100 ? fNow.toFixed(1) : fNow.toFixed(0)}\\,\\rm{Hz}`, 472, 438, { size: 18, align: 'right', color: C.accent, alpha: ma });
  }
  // ---------------------------------------------------------------- (e) the 4th mode's two waves
  const RX = x => 560 + x * 360, cr = cRel(), w4 = 2 * Math.PI * DATA.fn[3] / SLOW, k4 = 4 * Math.PI / DATA.L;
  const th4 = w4 * cr + Math.PI / 4;                        // the still: a quarter of the way to the next extreme
  sub('e', 520, 34, 'waves in the finite beam', lab(.02));
  const ye = 132;
  const pe = seg(.04, .35);
  line([[RX(0), ye], [RX(1), ye]], { color: C.ink, width: 1.8, progress: pe });
  if (pe > 0) { pin(RX(0), ye, { s: 12 }); pin(RX(1), ye, { s: 12, alpha: clamp(pe * 4 - 3) }); }
  const xe = Array.from({ length: 161 }, (_, i) => i / 160);
  line(xe.map(x => [RX(x), ye - 30 * .5 * Math.sin(k4 * x - th4)]), { color: C.blue, width: 2.2, progress: seg(.22, .4) });
  line(xe.map(x => [RX(x), ye - 30 * .5 * Math.sin(k4 * x + th4)]), { color: C.sky, width: 2, dash: [7, 5], progress: seg(.27, .4) });
  const ea = lab(.45);
  arrow(RX(.06), ye - 50, RX(.38), ye - 50, { width: 1.3, head: 8, alpha: ea, color: C.blue });
  arrow(RX(.94), ye - 50, RX(.62), ye - 50, { width: 1.3, head: 8, alpha: ea, color: C.sky });
  text('Direction of travel', RX(.22), ye - 58, { size: 16, color: C.body, align: 'center', alpha: ea });
  text('Direction of travel', RX(.78), ye - 58, { size: 16, color: C.body, align: 'center', alpha: ea });
  math('f = f_{4}', RX(.5), ye + 48, { size: 17, align: 'center', alpha: ea });
  // ---------------------------------------------------------------- (f) their sum, a standing wave
  sub('f', 520, 236, '4th modal dynamic response', lab(.06));
  const yf = 326, pf = seg(.08, .35);
  line([[RX(0), yf], [RX(1), yf]], { color: C.ink, width: 1.8, progress: pf });
  if (pf > 0) { pin(RX(0), yf, { s: 12 }); pin(RX(1), yf, { s: 12, alpha: clamp(pf * 4 - 3) }); }
  const snapA = lab(.6);
  for (let j = 6; j >= 1; j--) {
    const q = Math.cos(th4 - w4 * j * .045);
    line(xe.map(x => [RX(x), yf - 36 * Math.sin(k4 * x) * q]), { color: C.mist, width: 1.2, alpha: snapA * (1 - j / 8) });
  }
  line(xe.map(x => [RX(x), yf - 36 * Math.sin(k4 * x) * Math.cos(th4)]), { color: C.blue, width: 2.4, progress: seg(.3, .4) });
  for (let j = 1; j < 4; j++) dot(RX(j / 4), yf, 3.2, { color: C.ink, fill: '#fff', width: 1.3, alpha: lab(.55) });
  const la = lab(.7);
  line([[808, 230], [834, 230]], { color: C.blue, width: 2.4, alpha: la }); text('now', 840, 236, { size: 16, color: C.body, alpha: la });
  line([[888, 230], [914, 230]], { color: C.mist, width: 1.6, alpha: la }); text('earlier', 920, 236, { size: 16, color: C.body, alpha: la });
  // ---------------------------------------------------------------- (g) the first four modes
  sub('g', 520, 438, 'first four modal shapes', lab(.1));
  const yg = 516, half = 44;
  for (let n = 0; n < 4; n++) {
    const cx = 580 + n * 116, hot = n === nm, col = hot ? C.accent : C.blue, t0 = .12 + .05 * n;
    const pg = seg(t0, .3);
    line([[cx - half, yg], [cx + half, yg]], { color: C.ink, width: 1.5, progress: pg });
    if (pg > 0) { pin(cx - half, yg, { s: 9 }); pin(cx + half, yg, { s: 9, alpha: clamp(pg * 4 - 3) }); }
    const q = Math.cos(2 * Math.PI * DATA.fn[n] / SLOW * cr);
    line(Array.from({ length: 61 }, (_, i) => [cx - half + 2 * half * i / 60, yg - 24 * Math.sin((n + 1) * Math.PI * i / 60) * q]),
         { color: col, width: hot ? 2.6 : 2.2, progress: seg(t0 + .2, .35) });
    const a = lab(.5 + .05 * n);
    math(`${n + 1}^{\\rm{${ORD[n]}}}`, cx, yg + 42, { size: 17, align: 'center', color: hot ? C.accent : C.ink, alpha: a });
    text('resonance', cx, yg + 62, { size: 16, align: 'center', color: hot ? C.accent : C.body, alpha: a });   // stacked, as his (g)
    text('mode', cx, yg + 81, { size: 16, align: 'center', color: hot ? C.accent : C.body, alpha: a });
    math(`${DATA.fn[n].toFixed(1)}\\,\\rm{Hz}`, cx, yg + 104, { size: 16, align: 'center', color: C.body, alpha: a });
  }
  const pa = lab(.9);
  math('\\rm{steel bar 40} \\times\\ 10\\,\\rm{mm},\\ \\ L = 1\\,\\rm{m},\\ \\ E = 210\\,\\rm{GPa},\\ \\ \\rho\\ = 7850\\,\\rm{kg/m}^{3},\\ \\ ' +
       '\\rm{loss factor}\\ \\eta\\ = 0.05,\\ \\ \\rm{force at}\\ x = 0.13\\,L', 18, H - 14, { size: 15, color: C.muted, alpha: pa });
  text(`shown ${SLOW} × slower`, W - 18, H - 14, { size: 15, color: C.muted, align: 'right', alpha: pa });
}
boot();
"""
JS = (JS.replace("__POSTER_T__", f"{POSTER:.4f}").replace("__TS__", str(TS)).replace("__RAMP__", str(RAMP))
      .replace("__CP__", f"{C_P:.6f}"))

TITLE = "Figure 2: Occurrence of resonance modes"
ARIA = ("Computed from an exact beam model as a frequency sweep that slows into each resonance and rests there, "
        "each frame the steady state at the frequency of the moment: "
        "waves spreading from a harmonic force on an "
        "infinite beam and its flat response; the same force on a finite simply supported beam and its "
        "frequency response with four resonance peaks; the fourth mode as two waves travelling in opposite "
        "directions and their standing wave; and the first four mode shapes.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 704, DATA, JS)
    print(common.still(NAME))
