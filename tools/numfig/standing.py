"""Figure 3: flexural waves in a supported beam.

Model: the steel bar of Figure 2 (L = 1 m, pins at both ends, EB), a moment
M(t) = M0 g(t) sin(w_c t) at the left support switched on smoothly, held,
switched off; light viscous damping c (every mode decays as e^{-sigma t},
sigma = c/2m). Exact transient by frequency domain synthesis: for every
frequency of the FFT grid the span's general solution
    w = A e^{-ikx} + B e^{-ik(L-x)} + C e^{-kx} + D e^{-k(L-x)},
    k^4 = (m w^2 - i c w)/EI,
is fitted to w = 0 at both pins, EI w'' = M at x = 0 and w'' = 0 at x = L.
A e^{-ikx} is the wave travelling right (the source and every reflection
from the left pin), B e^{-ik(L-x)} the wave travelling left (every reflection
from the right pin: his 'Reflection'), C and D the near fields of the ends.
Row 1: w_c at the 3rd resonance, k L = 3 pi (three half wavelengths fit);
row 2: k L = 3.5 pi (they do not). Cross checked against an independent
modal time integration.

The page stores the complex envelope W(x, t) = z(x, t) e^{-i w_c t} (z the
analytic signal) and draws Re{W e^{i w_c t}}: exact at the stored instants,
the envelope interpolated between them (error in the check file).

Run: python tools/numfig/standing.py
"""
import os

import numpy as np
from scipy.linalg import expm

import beam_model as bm
import common

NAME = "standing"
HERE = os.path.dirname(os.path.abspath(__file__))

E, RHO, B, HT = 210e9, 7850.0, 0.040, 0.010
EI = E * B * HT ** 3 / 12
M = RHO * B * HT
L = 1.0
f1 = bm.freq_from_z(np.pi, L, EI, M)
CASES = {"res": 3.0, "off": 3.5}          # k L / pi at the drive frequency
fc = {k: bm.freq_from_z(v * np.pi, L, EI, M) for k, v in CASES.items()}
T3 = 1 / fc["res"]
ZETA3 = 0.05
SIGMA = ZETA3 * 2 * np.pi * fc["res"]     # every mode decays as e^{-sigma t}
CV = 2 * M * SIGMA                        # viscous coefficient c (N s/m^2)
RAMP_P, HOLD_P, OFF_P = 1.5, 6.0, 12.0   # in periods of the 3rd mode
CYCLE = (2 * RAMP_P + HOLD_P + OFF_P) * T3
PAD = 16 * T3
DT = T3 / 64
NX = 81
FPS = 8                                    # stored envelope frames per T3
SLOW = 211
TS, RAMP = 0.35, 0.25

xs = np.linspace(0, L, NX)
tt = np.arange(0, CYCLE + PAD, DT)
NT = len(tt)


def envelope(t):
    r, h = RAMP_P * T3, HOLD_P * T3
    g = np.zeros_like(t)
    up = (t >= 0) & (t < r)
    g[up] = 0.5 * (1 - np.cos(np.pi * t[up] / r))
    g[(t >= r) & (t < r + h)] = 1
    dn = (t >= r + h) & (t < 2 * r + h)
    g[dn] = 0.5 * (1 + np.cos(np.pi * (t[dn] - r - h) / r))
    return g


def coefficients(w):
    """(A, B, C, D) per unit moment at x = 0, and k, for each angular frequency w > 0."""
    k = ((M * w ** 2 - 1j * CV * w) / EI + 0j) ** 0.25
    eL, hL = np.exp(-1j * k * L), np.exp(-k * L)
    one = np.ones_like(k)
    Amat = np.stack([
        np.stack([one, eL, one, hL], -1),
        np.stack([-EI * k ** 2, -EI * k ** 2 * eL, EI * k ** 2, EI * k ** 2 * hL], -1),
        np.stack([eL, one, hL, one], -1),
        np.stack([-eL, -one, hL, one], -1),
    ], -2)
    rhs = np.zeros(k.shape + (4,), complex)
    rhs[..., 1] = 1.0
    return np.linalg.solve(Amat, rhs[..., None])[..., 0], k


def synthesize(key):
    wc = 2 * np.pi * fc[key]
    drive = envelope(tt) * np.sin(wc * tt)
    Mw = np.fft.rfft(drive)
    w = 2 * np.pi * np.fft.rfftfreq(NT, DT)
    co, k = coefficients(np.maximum(w, 1e-9))
    co[0] = 0
    kx = np.outer(k, xs)
    R = co[:, 0, None] * np.exp(-1j * kx)
    Lg = co[:, 1, None] * np.exp(-1j * (np.outer(k, L - xs)))
    N = co[:, 2, None] * np.exp(-kx) + co[:, 3, None] * np.exp(-np.outer(k, L - xs))
    out = {}
    for name, part in (("tot", R + Lg + N), ("left", Lg), ("right", R)):
        spec = part * Mw[:, None]
        full = np.zeros((NT, NX), complex)                 # analytic signal: positive frequencies x 2
        full[:len(w)] = spec
        full[1:len(w)] *= 2
        z = np.fft.ifft(full, axis=0)
        out[name] = z * np.exp(-1j * wc * tt)[:, None]    # complex envelope
    return out, drive


def modal_reference(key, x_probe, nmodes=300):
    """Independent check: modal superposition, each mode integrated exactly
    for piecewise linear forcing (ramp invariant discretisation)."""
    wc = 2 * np.pi * fc[key]
    drive = envelope(tt) * np.sin(wc * tt)
    n = np.arange(1, nmodes + 1)
    wn = (n * np.pi / L) ** 2 * np.sqrt(EI / M)
    Qn = -(n * np.pi / L) / (M * L / 2)   # end moment's generalized force per modal mass (EI w''(0) = M)
    Phi = np.empty((nmodes, 2, 2)); G0 = np.empty((nmodes, 2)); G1 = np.empty((nmodes, 2))
    for j in range(nmodes):
        Z = np.zeros((4, 4))
        Z[:2, :2] = np.array([[0, 1], [-wn[j] ** 2, -2 * SIGMA]]) * DT
        Z[:2, 2] = np.array([0, 1]) * DT
        Z[2, 3] = 1
        E4 = expm(Z)
        Phi[j], G0[j], G1[j] = E4[:2, :2], E4[:2, 2], E4[:2, 3]
    s = np.zeros((nmodes, 2))
    q = np.zeros((NT, nmodes))
    for i in range(NT - 1):
        s = np.einsum("jab,jb->ja", Phi, s) + (G0 * drive[i] + G1 * (drive[i + 1] - drive[i])) * Qn[:, None]
        q[i + 1] = s[:, 0]
    return q @ np.sin(np.outer(n, x_probe) * np.pi / L)


res = {}
for key in CASES:
    res[key] = synthesize(key)

# frames for the page: every T3/FPS over one cycle
tf = np.arange(0, CYCLE + T3 / FPS / 2, T3 / FPS)          # includes the cycle's end
idx = np.round(tf / DT).astype(int)


def pack(z):
    """int8 of the real and imaginary parts, interleaved, with the scale."""
    m = float(np.max(np.abs(np.concatenate([z.real.ravel(), z.imag.ravel()]))))
    q = np.empty(z.shape + (2,))
    q[..., 0], q[..., 1] = z.real / m * 127, z.imag / m * 127
    return {"s": m, "q": common.i8(q.ravel())}


# ------------------------------------------------------------------ checks
lines = []
say = lines.append
say("nf-standing: Figure 3, flexural waves in a supported beam")
say("")
say("MODEL")
say(f"  steel bar 40 x 10 mm, EI = {EI:.1f} N m^2, m = {M:.3f} kg/m, L = {L} m, pins at both ends")
say(f"  drive: moment M0 g(t) sin(w_c t) at the left pin; g: {RAMP_P} period raised cosine on, {HOLD_P} periods")
say(f"  held, {RAMP_P} off, then {OFF_P} periods free (periods of the 3rd mode, T3 = {T3*1e3:.3f} ms)")
say(f"  damping: viscous, c = {CV:.3f} N s/m^2, every mode decays as e^(-sigma t), sigma = {SIGMA:.2f} 1/s")
say(f"  (zeta = {ZETA3} at the 3rd mode)")
for key, v in CASES.items():
    say(f"  {'row 1' if key=='res' else 'row 2'}: k L = {v:g} pi, f = {fc[key]:.3f} Hz"
        f" ({'the 3rd resonance' if key=='res' else 'between the 3rd and 4th'})")
say(f"  synthesis: FFT over {NT} steps of {DT*1e6:.2f} us ({(CYCLE+PAD)*1e3:.1f} ms, the last {PAD/T3:g} T3 padding),")
say(f"  exact span solution at every frequency; {NX} points along the span")
say("")
say("CHECK 1: the synthesis against an independent modal time integration (300 modes, exact")
say("  discretisation of each mode for piecewise linear forcing), total displacement:")
probe = np.array([0.2, 0.5, 0.8])
jp = [int(np.argmin(np.abs(xs - p))) for p in probe]
for key in CASES:
    ref = modal_reference(key, xs[jp])
    fft_w = res[key][0]["tot"][:, jp] * np.exp(1j * 2 * np.pi * fc[key] * tt)[:, None]
    fft_w = fft_w.real
    sel = tt < CYCLE
    err = np.max(np.abs(fft_w[sel] - ref[sel])) / np.max(np.abs(ref[sel]))
    say(f"  {key}: max |difference| / max |w| over the cycle at x = 0.2, 0.5, 0.8 m: {err:.1e}")
say("")
say("CHECK 2: the boundary conditions hold in the time domain (the synthesis builds them in)")
for key in CASES:
    z = res[key][0]["tot"]
    say(f"  {key}: max |w(0, t)|, |w(L, t)| relative to max |w|: {np.max(np.abs(z[:, 0]))/np.max(np.abs(z)):.1e},"
        f" {np.max(np.abs(z[:, -1]))/np.max(np.abs(z)):.1e}")
say("")
say("CHECK 3: the frames: the complex envelope interpolated linearly between stored instants, against")
say("  the exact synthesis at the midpoints, max |error| / max |w| over the cycle:")
for key in CASES:
    z = res[key][0]["tot"]
    zf = z[idx]
    mid = np.round((tf[:-1] + T3 / FPS / 2) / DT).astype(int)
    interp = 0.5 * (zf[:-1] + zf[1:])
    ph = np.exp(1j * 2 * np.pi * fc[key] * tt[mid])[:, None]
    e = np.max(np.abs((interp * ph).real - (z[mid] * ph).real)) / np.max(np.abs(z))
    say(f"  {key}: {e:.1e} (and int8 storage adds at most 1/254 of each series' maximum)")
say("")
say("CHECK 4: what the figure shows, in numbers")
zr, zo = res["res"][0]["tot"], res["off"][0]["tot"]
say(f"  largest |w| over the cycle, off resonance / at resonance: {np.max(np.abs(zo))/np.max(np.abs(zr)):.3f}")
iend = int(np.round((RAMP_P + HOLD_P) * T3 / DT))
sr = res["res"][0]
say(f"  resonance, end of the drive: travelling right / left amplitude"
    f" {np.max(np.abs(sr['right'][iend]))/np.max(np.abs(sr['left'][iend])):.3f} (the damping across one span)")


def crossings(z, key, t0, t1):
    """Zero crossings inside the span of every instant in [t0, t1) whose shape is at least
    half as large as the largest in that window."""
    i0, i1 = int(np.round(t0 / DT)), int(np.round(t1 / DT))
    w = (z[i0:i1] * np.exp(1j * 2 * np.pi * fc[key] * tt[i0:i1])[:, None]).real
    amp = np.max(np.abs(w), axis=1)
    out = []
    for s_, a in zip(w, amp):
        if a < 0.5 * amp.max():
            continue
        for i in range(4, NX - 5):
            if s_[i] * s_[i + 1] < 0:
                out.append(xs[i] - s_[i] * (xs[i + 1] - xs[i]) / (s_[i + 1] - s_[i]))
    return np.array(out)


for name, (t0, t1) in {"building up (first 6 T3)": (0, 6 * T3),
                       "ringing down (the free part)": ((2 * RAMP_P + HOLD_P) * T3, (2 * RAMP_P + HOLD_P + 6) * T3)}.items():
    cr, co_ = crossings(zr, "res", t0, t1), crossings(zo, "off", t0, t1)
    near = [np.max(np.abs(cr[np.abs(cr - n) < 0.15] - n)) for n in (1 / 3, 2 / 3)]
    say(f"  {name}: resonance, crossings of the larger shapes stay within {max(near)*1e3:.0f} mm of L/3 and 2L/3;")
    say(f"    off resonance they spread over {np.ptp(co_):.2f} m, in {len(np.unique(np.round(co_, 2)))} distinct places (to 1 cm)")
say("")
say(f"TIME: slowed {SLOW} x: the 3rd mode oscillates at {fc['res']/SLOW:.2f} Hz on screen; the page opens 3 T3")
say("  into the drive (the build up already under way); the cycle")
say(f"  ({CYCLE/T3:g} T3 = {CYCLE*1e3:.1f} ms) lasts {CYCLE*SLOW:.1f} s and repeats; the response has decayed to")
say(f"  {np.max(np.abs(zr[int(np.round(CYCLE/DT))-1]))/np.max(np.abs(zr)):.1e} of its maximum when it does.")
t_off = (2 * RAMP_P + HOLD_P) * T3
say(f"  Under M(t) the two parts are named: forced vibration while the moment drives, 0 to"
    f" {2 * RAMP_P + HOLD_P:g} T3 = {t_off * 1e3:.2f} ms")
say(f"  ({t_off * SLOW:.1f} s on screen), free vibration from then to the cycle's end ({OFF_P:g} T3,"
    f" {OFF_P * T3 * SLOW:.1f} s); the name the cursor is in is set in ink.")
zi_off = res["res"][0]["tot"][int(np.round(t_off / DT)):int(np.round(CYCLE / DT))]
zf = (zi_off * np.exp(1j * 2 * np.pi * fc["res"] * tt[int(np.round(t_off / DT)):int(np.round(CYCLE / DT))])[:, None]).real
ring = np.abs(zf).max(axis=1)
k_per = int(round(T3 / DT))
per = np.array([ring[k * k_per:(k + 1) * k_per].max() for k in range(int(OFF_P))])
fit = np.exp(np.polyfit(np.arange(1, len(per)), np.log(per[1:]), 1)[0])
say(f"  In the free part the resonant beam rings down at its own damping: the largest |w| of each period,")
say(f"  fitted over periods 2 to {int(OFF_P)}, falls by {fit:.4f} a period against e^(-sigma T3) = {np.exp(-SIGMA * T3):.4f}.")
check = "\n".join(lines) + "\n"
print(check)
with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(check)

# ------------------------------------------------------------------ data
DATA = {"slow": SLOW, "L": L, "nx": NX, "fps": FPS, "T3": T3, "cycle": CYCLE,
        "nf": len(tf), "ramp": RAMP_P, "hold": HOLD_P, "nodes": [L / 3, 2 * L / 3], "rows": {}}
gmax = max(np.max(np.abs(res[k][0]["tot"][idx])) for k in CASES)
for key in CASES:
    r = res[key][0]
    DATA["rows"][key] = {"f": fc[key], "kl": CASES[key], "tot": pack(r["tot"][idx]), "left": pack(r["left"][idx]),
                         "max": float(np.max(np.abs(r["tot"][idx])) / gmax)}

JS = r"""
const POSTER_T = __POSTER_T__;
const SLOW = DATA.slow, TS = 0.35, RAMP = 0.25, NX = DATA.nx, NF = DATA.nf;
function clock() { const s = t - TS; return s <= 0 ? 0 : s < RAMP ? s * s / (2 * RAMP) : s - RAMP / 2; }
const lab = t0 => settle(t0, .28);
function unpack(p) { const q = b64i8(p.q), s = p.s / 127, out = new Float32Array(q.length); for (let i = 0; i < q.length; i++) out[i] = q[i] * s; return out; }
const ROWS = {};
for (const k of ['res', 'off']) { const r = DATA.rows[k]; ROWS[k] = { f: r.f, kl: r.kl, tot: unpack(r.tot), left: unpack(r.left) }; }
const GMAX = Math.max(...['res', 'off'].map(k => { let m = 0; const a = ROWS[k].tot; for (let i = 0; i < a.length; i += 2) m = Math.max(m, Math.hypot(a[i], a[i + 1])); return m; }));
/* the field at physical time tp (s): Re{W e^{i w_c tp}}, W interpolated between frames */
function field(k, arr, tp) {
  const c = ((tp % DATA.cycle) + DATA.cycle) % DATA.cycle, p = c / DATA.T3 * DATA.fps, j = Math.min(NF - 2, Math.floor(p)), s = p - j;
  const ph = 2 * Math.PI * ROWS[k].f * tp, co = Math.cos(ph), si = Math.sin(ph), out = new Float32Array(NX);
  for (let i = 0; i < NX; i++) {
    const a = (j * NX + i) * 2, b = ((j + 1) * NX + i) * 2;
    const re = lerp(arr[a], arr[b], s), im = lerp(arr[a + 1], arr[b + 1], s);
    out[i] = (re * co - im * si) / GMAX;
  }
  return out;
}
function envelope(tp) {
  const c = ((tp % DATA.cycle) + DATA.cycle) % DATA.cycle, r = DATA.ramp * DATA.T3, h = DATA.hold * DATA.T3;
  if (c < r) return .5 * (1 - Math.cos(Math.PI * c / r)); if (c < r + h) return 1;
  if (c < 2 * r + h) return .5 * (1 + Math.cos(Math.PI * (c - r - h) / r)); return 0;
}
const tphys = () => clock() / SLOW + __OFF__;             // the loop starts 3 periods into the drive
function sub(letter, x, y, words, a) { panel(letter, x, y, { alpha: a }); text(words, x + 36, y, { size: 16, color: C.body, alpha: a }); }
const A = 40;
function beamAt(x0, y, prog) {
  line([[x0, y], [x0 + 360, y]], { color: C.ink, width: 1.8, progress: prog });
  if (prog > 0) { pin(x0, y, { s: 12 }); pin(x0 + 360, y, { s: 12, alpha: clamp(prog * 4 - 3) }); }
}
const pts = (x0, y, w, amp) => Array.from(w, (v, i) => [x0 + i / (NX - 1) * 360, y - amp * v]);
/* the moment at the left pin: an arc whose sweep follows M(t) */
function momentArc(x, y, m, a) {
  if (Math.abs(m) < .02 || a <= 0) return;
  const r = 20, a0 = -Math.PI / 2, a1 = a0 - m * 2.4;
  const p = []; for (let i = 0; i <= 24; i++) { const u = a0 + (a1 - a0) * i / 24; p.push([x + r * Math.cos(u), y + r * Math.sin(u)]); }
  line(p, { color: C.accent, width: 1.6, alpha: a });
  const e = p[p.length - 1], q = p[p.length - 3];
  arrow(q[0], q[1], e[0], e[1], { color: C.accent, width: 1.6, head: 7, alpha: a });
}
/* forced vibration while M(t) drives (switched on, held, switched off), free
   vibration from the moment it is off to the cycle's end */
const C_OFF = (2 * DATA.ramp + DATA.hold) * DATA.T3;
/* 1 in the forced part, 0 in the free part; at each switch it passes to the
   other over 0.3 s of the page's clock, so the names follow the cursor */
function forcedW(tp) {
  const c = ((tp % DATA.cycle) + DATA.cycle) % DATA.cycle;
  return c < C_OFF ? easeInOut(clamp(c * SLOW / .3)) : 1 - easeInOut(clamp((c - C_OFF) * SLOW / .3));
}
/* a TikZ brace (decoration brace, mirrored) under [x0, x1] from height y, its tip h below at the middle */
function brace(x0, x1, y, h, o) {
  const r = h / 2, xm = (x0 + x1) / 2, pts = [];
  const arc = (cx, cy, a0, a1) => { for (let i = 0; i <= 8; i++) { const a = lerp(a0, a1, i / 8); pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } };
  arc(x0 + r, y, Math.PI, Math.PI / 2); arc(xm - r, y + h, -Math.PI / 2, 0);
  arc(xm + r, y + h, Math.PI, 1.5 * Math.PI); arc(x1 - r, y, Math.PI / 2, 0);
  line(pts, o);
}
function mixc(a, b, s) { const A = [1, 3, 5].map(i => parseInt(a.slice(i, i + 2), 16)), B = [1, 3, 5].map(i => parseInt(b.slice(i, i + 2), 16));
  return '#' + A.map((v, i) => Math.round(lerp(v, B[i], clamp(s))).toString(16).padStart(2, '0')).join(''); }

function row(key, y0, letters, words, t0, tp) {
  const [la, lb] = letters, [wa, wb] = words;
  sub(la, 18, y0, wa, lab(t0)); sub(lb, 520, y0, wb, lab(t0 + .04));
  const ya = y0 + 96, xa = 60, xb = 560;
  beamAt(xa, ya, seg(t0, .35)); beamAt(xb, ya, seg(t0 + .05, .35));
  const R = ROWS[key], tot = field(key, R.tot, tp), left = field(key, R.left, tp);
  // (a), (c): the reflection and the sum
  line(pts(xa, ya, left, A), { color: C.accent, width: 1.5, progress: seg(t0 + .2, .4) });
  line(pts(xa, ya, tot, A), { color: C.blue, width: 2.4, progress: seg(t0 + .15, .4) });
  const env = envelope(tp), m = env * Math.sin(2 * Math.PI * R.f * tp);
  momentArc(xa, ya, m, lab(t0 + .3));
  const ha = lab(t0 + .4);
  arrow(xa + 40, y0 + 30, xa + 120, y0 + 30, { width: 1.8, head: 9, alpha: ha, color: C.ink });
  text('Wave', xa + 40, y0 + 50, { size: 15, color: C.body, alpha: ha });
  arrow(xa + 320, y0 + 30, xa + 240, y0 + 30, { width: 1.8, head: 9, alpha: ha, color: C.accent });
  text('Reflection', xa + 320, y0 + 50, { size: 15, color: C.body, align: 'right', alpha: ha });
  math(key === 'res' ? 'L = 3\\,\\lambda/2' : 'L = 3.5\\,\\lambda/2', xa + 180, ya + 58, { size: 16, align: 'center', alpha: ha });
  math(`f = ${R.f.toFixed(1)}\\,\\rm{Hz}`, xa + 180, ya + 80, { size: 15, align: 'center', color: C.muted, alpha: ha });
  // (b), (d): the last period, earlier shapes fading
  const sa = lab(t0 + .45);
  if (sa > 0) for (let j = 8; j >= 1; j--) {
    const w = field(key, R.tot, tp - j / R.f / 8);
    line(pts(xb, ya, w, A), { color: C.mist, width: 1.2, alpha: sa * (1 - j / 10) });
  }
  line(pts(xb, ya, tot, A), { color: C.blue, width: 2.4, progress: seg(t0 + .2, .4) });
  const za = lab(t0 + .5);
  if (key === 'res') for (const z of DATA.nodes) dot(xb + z / DATA.L * 360, ya, 4, { color: C.accent, fill: C.accent, alpha: za });
  // the drive, over the cycle: forced vibration while M(t) drives, free vibration once it is off
  const yd = ya + 64, xd0 = xb, xd1 = xb + 360, da = lab(t0 + .55);
  if (da > 0) {
    const e = []; for (let i = 0; i <= 120; i++) { const c = i / 120 * DATA.cycle; e.push([lerp(xd0, xd1, i / 120), yd - 12 * envelope(c)]); }
    line(e, { color: C.guide, width: 1.1, alpha: da });
    line([[xd0, yd], [xd1, yd]], { color: C.rule, width: 1, alpha: da });
    const c = ((tp % DATA.cycle) + DATA.cycle) % DATA.cycle, xc = lerp(xd0, xd1, c / DATA.cycle);
    line([[xc, yd + 3], [xc, yd - 15]], { color: C.accent, width: 1.6, alpha: da });
    math('M(t)', xd0 - 8, yd - 2, { size: 14, align: 'right', color: C.muted, alpha: da });
    // each part of the drive named under it, the one the cursor is in set in ink
    const xf = lerp(xd0, xd1, C_OFF / DATA.cycle), wf = forcedW(tp), ba = lab(t0 + .6);
    const parts = [[xd0 + 1, xf - 2.5, 'forced vibration', wf], [xf + 2.5, xd1 - 1, 'free vibration', 1 - wf]];
    for (const [x0, x1, s, w] of parts) {
      brace(x0, x1, yd + 5, 7, { color: mixc(C.guide, C.ink, w), width: 1.2, alpha: ba });
      text(s, (x0 + x1) / 2, yd + 30, { size: 15, align: 'center', color: mixc(C.muted, C.ink, w), alpha: ba });
    }
  }
}

function draw() {
  const tp = tphys();
  row('res', 34, ['a', 'b'], ['standing waves in constructive form', 'standing waves over time'], 0, tp);
  row('off', 254, ['c', 'd'], ['non standing waves', 'non standing waves over time'], .06, tp);
  const la = lab(.8);
  const LY = 508;
  line([[60, LY - 5], [86, LY - 5]], { color: C.blue, width: 2.4, alpha: la }); text('displacement, now', 92, LY, { size: 14, color: C.body, alpha: la });
  line([[232, LY - 5], [258, LY - 5]], { color: C.mist, width: 1.6, alpha: la }); text('earlier', 264, LY, { size: 14, color: C.body, alpha: la });
  line([[332, LY - 5], [358, LY - 5]], { color: C.accent, width: 1.5, alpha: la }); text('reflection, travelling left', 364, LY, { size: 14, color: C.body, alpha: la });
  dot(560, LY - 5, 4, { color: C.accent, fill: C.accent, alpha: la }); text('nodes of the 3rd mode', 570, LY, { size: 14, color: C.body, alpha: la });
  const ea = la; line([[748, LY - 5], [774, LY - 5]], { color: C.guide, width: 1.1, alpha: ea }); text('drive envelope', 780, LY, { size: 14, color: C.body, alpha: ea });
  const pa = lab(.9);
  text('steel bar 40 × 10 mm, L = 1 m, pins at both ends; moment M(t) at the left pin, switched on, held, off; ζ = 0.05',
       18, H - 12, { size: 14, color: C.muted, alpha: pa });
  text(`time slowed ${SLOW} ×`, W - 18, H - 12, { size: 14, color: C.muted, align: 'right', alpha: pa });
}
boot();
"""

# the still: late in the hold, the resonant pattern near an extreme at mid span
c_hold = (RAMP_P + HOLD_P - 0.3) * T3
cand = np.arange(c_hold - 1.5 * T3, c_hold, T3 / 400)
zi = res["res"][0]["tot"][np.round(cand / DT).astype(int)]
vals = np.abs((zi * np.exp(1j * 2 * np.pi * fc["res"] * cand)[:, None]).real).max(axis=1)
tbest = cand[int(np.argmax(vals))]
OFF = 3 * T3
POSTER = TS + RAMP / 2 + (tbest - OFF) * SLOW
JS = JS.replace("__POSTER_T__", f"{POSTER:.4f}").replace("__OFF__", f"{OFF:.9f}")
print(f"POSTER_T = {POSTER:.3f} s")

TITLE = "Figure 3: Flexural waves in a supported beam"
ARIA = ("Computed transient of a simply supported beam driven by a moment at its left support, in forced "
        "vibration while the moment drives and in free vibration after it is switched off: at a "
        "frequency whose half wavelength fits the span, the reflected wave lines up with the outgoing "
        "wave and a standing wave with fixed nodes builds up; at a frequency that does not fit, the "
        "reflections cancel, the response stays small and its zero crossings wander.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 548, DATA, JS)
    print(common.still(NAME))
