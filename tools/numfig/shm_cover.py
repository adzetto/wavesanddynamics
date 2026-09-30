"""The SHM and NDT guide's cover (understanding-shm-and-ndt, image1): the whole
structure, and one spot of it listened to closely.

His cover is a line drawing without words: a small building, a wave running
away from it that turns from teal to orange, three sensor dots. The redraw
says the same at a glance, from the two models the guide's own figures use,
imported, not copied:

Left, the building of Figure 1 (shm_sensors.py): the continuum model of
Miranda and Taghavi (2005), walls and frames, 80 m tall, alpha = 6, fixed at
the ground, by finite elements, swaying in its first mode (f1 = 0.42 Hz) in
real time, accelerometers riding its floors: vibration based monitoring,
listening to the whole structure.

Middle, detail A: one steel member of it at the NDT scale, a 10 mm plate on
which a transducer launches a 3 cycle, 50 kHz A0 Lamb wave (guided_ut.py,
the model of Figure 5 (a): the exact Rayleigh-Lamb A0 branch and the burst's
Fourier synthesis over it). The packet spreads as it goes (dispersion), a
defect 1.5 m away sends part of it back, and the echo returns to the
transducer: wave propagation based monitoring, listening to one spot closely.

Right, the transducer's received signal, drawn as it arrives: the outgoing
burst, then the echo, spread out by dispersion, a millisecond later.

Run: python tools/numfig/shm_cover.py [--look]   (writes content/anim/
nf-shm-cover.html and .webp and tools/numfig/shm_cover.check.txt)
"""
import os
import sys

import numpy as np
from scipy.signal import hilbert

import common
import guided_ut as G
import shm_sensors as S
import wt_lib

NAME = "shm-cover"
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ the page's clock (s)
T0B = 0.35             # the building, held at full sway, is let go
TF = 0.50              # the first burst leaves the transducer
NSWAY = 3              # a wave cycle on screen lasts three sways of the building
FADE = 0.5             # the record fades before the next burst
POSTER_SWAYS = 1.5     # the still: a sway and a half after the building is let go (full sway)
POSTER_TM = 1030e-6    # ... and the echo's peak reaching the transducer: the wave's slowing follows
# ------------------------------------------------------------------ the wave, as drawn
T_TR = 1400e-6         # s of record (Figure 5 (a) shows the same 1.4 ms)
DT_TR = 1e-6           # its samples
DXM = 4.4e-3           # m between the points along the plate where the page sums the field
NX = 420               # points: x = 0 (the transducer) to (NX - 1) DXM = 1.8436 m in view
PPM = 213.0            # drawing units per metre along the plate
PT = 18.0              # drawn thickness (units) of the 10 mm plate
DZ = 3.6               # u_z drawn this many units at the field's peak
CG = 3.0               # the colour saturates at 1 / CG of the peak (the spread out echo still reads)
QUIET = 3e-3           # the plate is drawn at rest once the field in view is below this share of its peak
# ------------------------------------------------------------------ the building, as drawn
UPM = 1.7              # units per metre: 80 m drawn 136 units
BAYS, BAY = 3, 10.0    # bays of 10 m: 30 m wide
STOREYS = 24           # of 3.33 m (Figure 1's building: 80 m, "about 24 storeys")
AMP = 8.0              # the roof's sway drawn (units), mode 1 alone


def mode_closed(xi, a, g):
    """Miranda and Taghavi (2005), eq. 7: the coupled cantilever's mode shape,
    beta^2 = alpha^2 + gamma^2, fixed at xi = 0, free at xi = 1."""
    b = np.sqrt(a * a + g * g)
    eta = (g * g * np.sin(g) + g * b * np.sinh(b)) / (g * g * np.cos(g) + b * b * np.cosh(b))
    return np.sin(g * xi) - g / b * np.sinh(b * xi) + eta * (np.cosh(b * xi) - np.cos(g * xi))


def echo_field(comp, x, tm):
    """The echo alone along the plate (x <= D): R times the burst at path 2D - x."""
    ph = comp["w"] * tm - np.outer(2 * G.D_DEF - x, comp["k"]) + comp["p"]
    return np.where(x <= G.D_DEF, G.R_DEF * (comp["a"] * np.cos(ph)).sum(1), 0.0)


def model():
    # ---- the building: Figure 1's model and its checks, run as that figure runs them
    R = S.compute()
    f = R["w"] / (2 * np.pi)
    xs = R["xs"]
    psi = R["phi"][:, 0] / R["phi"][-1, 0]                   # mode 1, roof = 1
    gam, lam = S.closed(S.ALPHA, 3)
    shape = mode_closed(xs, S.ALPHA, gam[0])
    shape_err = np.abs(psi - shape / shape[-1]).max()
    f_closed = lam * np.sqrt(R["EI"] / (S.MASS * S.H_M ** 4)) / (2 * np.pi)

    # ---- the wave: Figure 5 (a)'s A0 pulse echo
    comp = G.components("A")
    cp, cg = G.group_velocity("A", G.F0)
    tc = G.NCYC / G.F0 / 2
    ttr = np.arange(0, T_TR + DT_TR / 2, DT_TR)
    trace = G.received(comp, ttr)
    te = np.arange(0, 2.4e-3, 0.1e-6)
    echo = G.synth(comp, 2 * G.D_DEF, te, G.R_DEF)
    tpk, apk, env = G.envelope_peak(te, echo, 0)
    near = np.abs(te - tpk) < 600e-6
    big = te[near][env[near] >= 0.03 * apk]
    win = (float(big[0]), float(min(big[-1], T_TR)))
    w6 = G.width6(te, env, tpk - 600e-6, tpk + 600e-6)
    tb = np.arange(0, 200e-6, 0.1e-6)
    w6b = G.width6(tb, np.abs(hilbert(G.synth(comp, 0.0, tb))), 0, 200e-6)
    # the burst the lines rebuild at the source, against the burst itself
    tt = np.arange(-20e-6, 200e-6, 0.1e-6)
    T = G.NCYC / G.F0
    ref = np.where((tt >= 0) & (tt <= T), 0.5 * (1 - np.cos(2 * np.pi * tt / T)) * np.sin(2 * np.pi * G.F0 * tt), 0)
    src_err = np.abs(G.synth(comp, 0.0, tt) - ref).max() / np.abs(ref).max()

    # the field along the plate in view: its peak over the cycle, and when it is over
    x = np.arange(NX) * DXM
    tms = np.arange(0, 2400e-6, 5e-6)
    fld = np.array([G.field(comp, x, tm) for tm in tms])
    peak = float(np.abs(fld).max())
    level = np.abs(fld).max(1) / peak
    quiet = [tm for tm, lv in zip(tms, level) if tm > tpk and lv < QUIET]
    tend = float(quiet[0])
    resid = float(level[tms >= tend].max())
    # where the echo is while it runs back: the centroid of its energy (the
    # squared Hilbert envelope along the plate), and how much of it is still in
    # the plate, against the most there ever is
    th = np.arange(0.0, tend + 1e-9, 10e-6)
    xe, share = [], []
    for tm in th:
        e2 = np.abs(hilbert(echo_field(comp, x, tm))) ** 2
        xe.append(float((x * e2).sum() / e2.sum()) if e2.sum() > 0 else G.D_DEF)
        share.append(float(e2.sum()))
    share = np.array(share) / max(share)

    # Kirchhoff and Rayleigh limits of the A0 branch the synthesis runs on
    Db = G.E * G.D_PLATE ** 3 / (12 * (1 - G.NU ** 2))
    kirch = lambda fr: (2 * np.pi * fr) ** 0.5 * (Db / (G.RHO * G.D_PLATE)) ** 0.25
    lo = [(fr, G.lowest("A", fr), kirch(fr)) for fr in (100.0, 1e3)]
    hi = G.lowest("A", 2e6)

    # the page's clock: a wave cycle is NSWAY sways of the building; the still
    # at a full sway with the echo's peak arriving fixes the wave's slowing
    TB = 1 / f[0]
    PW = NSWAY * TB
    poster = T0B + POSTER_SWAYS * TB
    slow = (poster - TF) / POSTER_TM
    return dict(R=R, f=f, xs=xs, psi=psi, gam=gam, f_closed=f_closed, shape_err=shape_err,
                comp=comp, cp=cp, cg=cg, tc=tc, ttr=ttr, trace=trace, tpk=tpk, apk=apk, win=win,
                w6=w6, w6b=w6b, src_err=src_err, x=x, peak=peak, tend=tend, resid=resid,
                th=th, xe=np.array(xe), share=share, lo=lo, hi=hi, TB=TB, PW=PW, slow=slow,
                poster=poster)


JS = r"""
/* ---- the cover: W 1000, H 173 (his picture's 1344 x 233) ---- */
const D = DATA, WV = D.wave, US = 1e-6;
const NARROW = () => (cv.clientWidth || W) < 480;    // a phone: strokes heavier, the few words left out
const K = () => NARROW() ? 1.8 : 1;                   // stroke widths, times
const lab = t0 => settle(t0, .28) * (NARROW() ? 0 : 1);

/* ------------------------------------------------ the clock */
const T0B = D.t0b, TF = D.tf, PW = D.pw, SLOW = D.slow, FADE = D.fade;
const POSTER_T = D.poster;
function Q() { return t < T0B ? 1 : Math.cos(2 * Math.PI * (t - T0B) / D.tb); }   // let go from full sway
function cycle() {                                   // this wave cycle: when it began (s), its model time (s)
  if (t < TF) return { t0: TF, tm: -1 };
  const c = Math.floor((t - TF) / PW), t0 = TF + c * PW;
  return { t0, tm: (t - t0) / SLOW };
}

/* ------------------------------------------------ the building (Figure 1's), mode 1 */
const GY = 156, HB = D.hb, BX = 32, BW = D.bw, NBAY = D.bays, NST = D.storeys;
const AMP = D.amp;                                    // the roof's sway, drawn
const PSI = D.psi, NN = PSI.length;
const lev = xi => GY - HB * xi;
function sway(xi, q) { const p = xi * (NN - 1), i = Math.min(NN - 2, Math.floor(p)); return q * AMP * lerp(PSI[i], PSI[i + 1], p - i); }
function ground(p) {
  line([[6, GY], [134, GY]], { width: 1.8 * K(), progress: p });
  if (p < 1) return;
  ctx.save(); ctx.strokeStyle = C.ink; ctx.lineWidth = K(); ctx.beginPath();
  for (let x = 13; x < 134; x += 7) { ctx.moveTo(x, GY); ctx.lineTo(x - 6, GY + 7); }
  ctx.stroke(); ctx.restore();
}
function building(q, p) {                             // the columns rise; each floor follows
  if (p <= 0) return;
  // at rest, as Figure 1 draws it: the outline in the rule's grey
  line([[BX, GY], [BX, lev(p)], [BX + BW, lev(p)], [BX + BW, GY]], { color: C.rule, width: K() });
  for (let k = 1; k <= NST; k++) {
    const xi = k / NST;
    if (xi > p + 1e-9) break;
    if (NARROW() && k % 3 && k < NST) continue;
    const u = sway(xi, q), y = lev(xi), roof = k === NST;
    line([[BX + u, y], [BX + BW + u, y]], { color: roof ? C.navy : C.sky, width: (roof ? 2.4 : .75) * K() });
  }
  for (let j = 0; j <= NBAY; j++) {
    const pts = [];
    for (let i = 0; i < NN; i++) { const xi = i / (NN - 1); pts.push([BX + j * BW / NBAY + sway(xi, q), lev(xi)]); }
    line(pts, { color: C.blue, width: (j % NBAY ? 1.1 : 1.9) * K(), progress: p });
  }
}
const SENS = [.25, .5, .75, 1];                        // accelerometers on floors 6, 12, 18 and the roof
function sensors(q) {
  SENS.forEach((xi, i) => {
    const a = settle(.3 + .04 * i, .28); if (a <= 0) return;
    const s = 6.4 * Math.sqrt(K()) * (.6 + .4 * a), x = BX + BW / 6 + sway(xi, q), y = lev(xi);
    ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.navy; ctx.fillRect(x - s / 2, y - s - .6, s, s); ctx.restore();
  });
}

/* ------------------------------------------------ detail A: a steel plate of it, A0 */
const FX0 = 190, FX1 = 606, FY0 = 56, FY1 = 124;       // the detail's frame
const PY = 89, PT = D.pt, TW = 13, TH = 8;              // plate centre line, drawn thickness; transducer
const XT = 582, PPM = D.ppm;                            // x = 0 (the transducer) and units per metre; x runs left
const XP = x => XT - x * PPM;
const NX = WV.nx, DXM = WV.dx_mm / 1000, DZ = WV.dz, CG = WV.cg;   // points; drawn deflection, colour gain
const XI = XT + TW / 2;                                 // the plate's end, flush with the transducer
const LW = b64f32(WV.w), LK = b64f32(WV.k), LA = b64f32(WV.a), LP = b64f32(WV.p), NL = LW.length;
const CK = new Float64Array(NL), SK = new Float64Array(NL);
for (let l = 0; l < NL; l++) { CK[l] = Math.cos(LK[l] * DXM); SK[l] = Math.sin(LK[l] * DXM); }
const U = new Float64Array(NX);
let _tmU = null;
/* u_z(x, tm) at the NX points: incident + R echo before the defect, T incident past it (guided_ut.field),
   each spectral line's phasor carried along x by e^{-ik dx} (incident) and e^{+ik dx} (echo) */
function fieldAt(tm) {
  if (tm === _tmU) return U;
  U.fill(0); _tmU = tm;
  const R = WV.R, T = Math.sqrt(1 - R * R), iD = Math.floor(WV.D / DXM + 1e-9);
  for (let l = 0; l < NL; l++) {
    const ph = LW[l] * tm + LP[l], a = LA[l], c = CK[l], s = SK[l];
    let zr = a * Math.cos(ph), zi = a * Math.sin(ph);
    const pe = ph - LK[l] * 2 * WV.D;
    let er = a * Math.cos(pe), ei = a * Math.sin(pe);
    for (let i = 0; i < NX; i++) {
      U[i] += i <= iD ? zr + R * er : T * zr;
      const nz = zr * c + zi * s; zi = zi * c - zr * s; zr = nz;      // times e^{-ik dx}
      const ne = er * c - ei * s; ei = ei * c + er * s; er = ne;      // times e^{+ik dx}
    }
  }
  return U;
}
/* the section's colour: the diverging palette, eased into the plate's own steel where u_z is small,
   so a node inside the packet and the plate at rest read alike */
const RAMP = (() => {
  const st = [0xE3, 0xEB, 0xF2], out = [];
  for (let i = 0; i < 256; i++) {
    const v = i / 255 * 2 - 1, j = Math.round((v + 1) / 2 * 255) * 3, w = clamp(Math.abs(v) / .14);
    const m = w * w * (3 - 2 * w), c = [0, 1, 2].map(k => Math.round(lerp(st[k], DIVERGING[j + k], m)));
    out.push(`rgb(${c[0]},${c[1]},${c[2]})`);
  }
  return out;
})();
const ramp = v => RAMP[Math.round((clamp(v, -1, 1) + 1) / 2 * 255)];
function interp(arr, x0, dx, x) { const p = clamp((x - x0) / dx, 0, arr.length - 1), i = Math.min(arr.length - 2, Math.floor(p)); return lerp(arr[i], arr[i + 1], p - i); }
function detail(a, tm) {
  if (a <= 0) return;
  const live = tm >= 0 && tm <= WV.tend_us * US;
  const u = live ? fieldAt(tm) : null;
  const dz = i => live ? -DZ * clamp(u[i] / WV.peak, -1, 1) : 0;
  const at = x => { const p = clamp(x / DXM, 0, NX - 1), i = Math.min(NX - 2, Math.floor(p)); return lerp(dz(i), dz(i + 1), p - i); };
  ctx.save(); ctx.globalAlpha *= a;
  ctx.beginPath(); ctx.rect(FX0, FY0, FX1 - FX0, FY1 - FY0); ctx.clip();
  ctx.fillStyle = '#fff'; ctx.fillRect(FX0, FY0, FX1 - FX0, FY1 - FY0);
  // the plate: its section coloured by u_z, and bent by it
  const w = PPM * DXM, top = [], bot = [];
  ctx.fillStyle = live ? ramp(u[0] / WV.peak * CG) : C.steel; ctx.fillRect(XT, PY - PT / 2 + dz(0), XI - XT, PT);
  for (let i = 0; i < NX; i++) {
    const X = XP(i * DXM), z = dz(i);
    ctx.fillStyle = live ? ramp(u[i] / WV.peak * CG) : C.steel;
    ctx.fillRect(X - w / 2 - .35, PY - PT / 2 + z, w + .7, PT);
    top.push([X, PY - PT / 2 + z]); bot.push([X, PY + PT / 2 + z]);
  }
  top.unshift([XI, PY - PT / 2 + dz(0)]); bot.unshift([XI, PY + PT / 2 + dz(0)]);
  line(top, { color: C.ink, width: 1.4 * K() }); line(bot, { color: C.ink, width: 1.4 * K() });
  line([top[0], bot[0]], { color: C.ink, width: 1.4 * K() });
  // the defect: a notch up from the lower face
  const xd = XP(WV.D), zd = at(WV.D);
  line([[xd - 3.4, PY + PT / 2 + zd], [xd, PY + PT / 2 - PT * .55 + zd], [xd + 3.4, PY + PT / 2 + zd]], { color: '#781E2C', width: 1.2, fill: C.accent, close: true });
  // the echo, the one thing to follow: an arrow over what of it is still in the plate
  if (live) {
    const xe = interp(WV.xe, 0, WV.dth_us * US, tm), sh = interp(WV.share, 0, WV.dth_us * US, tm);
    const ea = clamp((WV.D - .1 - xe) / .1) * clamp((sh - .12) / .25);
    if (ea > 0) arrow(XP(xe) - 12, PY - PT / 2 - 13, XP(xe) + 12, PY - PT / 2 - 13, { color: C.accent, width: 1.7 * K(), head: 8, alpha: ea });
  }
  // the transducer, sending and receiving, on the upper face
  ctx.fillStyle = C.navy; ctx.fillRect(XT - TW / 2, PY - PT / 2 - TH + dz(0), TW, TH);
  ctx.restore();
}

/* ------------------------------------------------ the received signal */
const SX0 = 648, SX1 = 972, SY = PY, SA = 50, XO = SX0 + 8;   // axes: amplitude at SX0, time along SY from XO
const TR = b64f32(WV.trace), NT = TR.length, DTT = WV.dtt_us * US, TTR = (NT - 1) * DTT;
const XS = tm => XO + tm / TTR * (SX1 - XO);
function record(tm, a) {
  if (tm < 0 || a <= 0) return;
  const n = Math.min(NT - 1, Math.floor(tm / DTT)), pts = [];
  for (let i = 0; i <= n; i++) pts.push([XS(i * DTT), SY - SA * TR[i]]);
  if (n < NT - 1) { const s = tm / DTT - n; pts.push([XS(tm), SY - SA * lerp(TR[n], TR[n + 1], s)]); }
  line(pts, { color: C.navy, width: 1.5 * K(), alpha: a });
  const i0 = Math.round(WV.win_us[0] * US / DTT), i1 = Math.min(pts.length - 1, Math.round(WV.win_us[1] * US / DTT));
  if (i1 > i0) line(pts.slice(i0, i1 + 1), { color: C.accent, width: 1.8 * K(), alpha: a });
}

function draw() {
  const q = Q(), cy = cycle(), tm = cy.tm;
  // the building and its sensors
  ground(seg(0, .25));
  building(q, seg(.02, .36));
  sensors(q);
  // spot A on floor 12, and the lines out to its detail
  const ua = settle(.28, .28), xa = BX + 5 * BW / 6 + sway(.5, q), ya = lev(.5);
  if (ua > 0) {
    line([[xa - 6, ya - 4.5], [xa + 6, ya - 4.5], [xa + 6, ya + 4.5], [xa - 6, ya + 4.5]], { color: C.ink, width: 1.1 * K(), close: true, alpha: ua });
    const sp = seg(.3, .25);
    line([[xa + 6, ya - 4.5], [FX0, FY0]], { color: C.ink, width: .9 * K(), progress: sp });
    line([[xa + 6, ya + 4.5], [FX0, FY1]], { color: C.ink, width: .9 * K(), progress: sp });
  }
  // detail A
  detail(seg(.1, .3), tm);
  line([[FX0, FY0], [FX1, FY0], [FX1, FY1], [FX0, FY1], [FX0, FY0]], { color: C.ink, width: 1.3 * K(), progress: seg(.08, .36) });
  // the record: drawn as it is received, whole until the next burst
  const ax = seg(.16, .3);
  line([[SX0, SY + SA + 3], [SX0, SY - SA - 3]], { color: C.ink, width: 1.1 * K(), progress: ax });
  if (ax > 0) arrow(SX0, SY, lerp(SX0, SX1 + 14, ax), SY, { color: C.ink, width: 1.1 * K(), head: 7, alpha: ax });
  const fa = 1 - clamp((t - cy.t0 - (PW - FADE)) / FADE);
  record(Math.min(tm, TTR), fa);
  // the few words
  math('f_1 = ' + (1 / D.tb).toFixed(2) + '\\,\\rm{Hz}', 100, 36, { size: 17, color: C.body, alpha: lab(.34) });
  math('A_0,\\ 50\\,\\rm{kHz}', XI, FY1 - 10, { size: 16, color: C.body, align: 'right', alpha: lab(.4) });
  math('t', SX1 + 10, SY + 17, { size: 17, color: C.body, alpha: lab(.42) });
  // the echo named, and its time of flight, as it starts to arrive
  if (tm >= WV.win_us[0] * US) {
    const ea = lab(cy.t0 + WV.win_us[0] * US * SLOW) * fa;
    text('echo', XS(WV.tpk_us * US), SY - 22, { size: 16, color: C.accent, align: 'center', alpha: ea });
    dim(XS(WV.tc_us * US), XS(WV.tpk_us * US), SY + SA + 13, (WV.tof_us / 1000).toFixed(1) + '\\,\\rm{ms}', { size: 15, alpha: ea, color: C.body });
  }
}
boot();
"""

TITLE = "A building's first mode, and a guided wave's echo from a defect in one of its members"
ARIA = ("A tall building sways in its first vibration mode with sensors on its floors. A close-up of one "
        "of its steel members shows an ultrasonic guided wave leave a transducer, spread out as it travels, "
        "meet a small defect and return as an echo, which the received signal beside it records.")


def page_data(r):
    us = lambda v: v * 1e6
    return {
        "tb": r["TB"], "psi": r["psi"], "t0b": T0B, "tf": TF, "pw": r["PW"], "fade": FADE,
        "poster": r["poster"], "slow": r["slow"], "pt": PT, "ppm": PPM,
        "hb": S.H_M * UPM, "bw": BAYS * BAY * UPM, "bays": BAYS, "storeys": STOREYS,
        "amp": AMP, "H": S.H_M, "alpha": S.ALPHA,
        "wave": {
            "w": common.f32(r["comp"]["w"]), "k": common.f32(r["comp"]["k"]), "a": common.f32(r["comp"]["a"]),
            "p": common.f32(r["comp"]["p"]), "nx": NX, "dx_mm": DXM * 1e3, "D": G.D_DEF, "R": G.R_DEF,
            "peak": r["peak"], "tend_us": us(r["tend"]), "dz": DZ, "cg": CG, "f0": G.F0, "d_mm": G.D_PLATE * 1e3,
            "trace": common.f32(r["trace"]), "dtt_us": us(DT_TR), "win_us": [us(v) for v in r["win"]],
            "tpk_us": us(r["tpk"]), "tc_us": us(r["tc"]), "tof_us": us(r["tpk"] - r["tc"]),
            "cg_ms": r["cg"], "dth_us": us(r["th"][1] - r["th"][0]), "xe": r["xe"], "share": r["share"],
        },
    }


def page_check(r):
    """The page's own field sum and record against numpy (guided_ut.field, received)."""
    cases = [(f"fieldAt({tm!r})", G.field(r["comp"], r["x"], tm)) for tm in (200e-6, 540e-6, POSTER_TM)]
    cases.append(("b64f32(WV.trace)", r["trace"]))
    return G.check_page(NAME, cases)


def report(r, page, over):
    L = []
    say = L.append
    R, f = r["R"], r["f"]
    say("nf-shm-cover: the SHM and NDT guide's cover (image1)")
    say("generator: tools/numfig/shm_cover.py; models imported: shm_sensors.py (Figure 1's building),")
    say("guided_ut.py (Figure 5 (a)'s guided waves, the waves guide's Figure 12); their own checks are in")
    say("shm_sensors.check.txt and guided_ut.check.txt; those that bear on this page are rerun here.")
    say("")
    say("THE BUILDING (left): Figure 1's model, run by shm_sensors.compute()")
    say(f"  Miranda and Taghavi (2005) walls and frames continuum, H = {S.H_M:g} m, m = {S.MASS/1e3:g} t/m,"
        f" alpha = {S.ALPHA:g}, EI = {R['EI']:.4e} N m^2")
    say(f"  (so that T1 = {S.T1} s), {S.NE} Hermite elements, consistent mass.")
    say("  CHECK 1: frequencies against the closed form (eq. 6, roots by brentq):")
    for j in range(3):
        say(f"    f{j+1} = {f[j]:.6f} Hz, closed form {r['f_closed'][j]:.6f} Hz ({f[j]/r['f_closed'][j]-1:+.1e})")
    (n1, l1), (n2, l2) = R["conv"][2], R["conv"][3]
    say(f"    (f1's error falls 16 x per halving of the elements: {n1} elements {l1[0]/R['closed'][0]-1:+.1e},"
        f" {n2} elements {l2[0]/R['closed'][0]-1:+.1e})")
    say("  CHECK 2: the 1st mode's shape against the closed form (eq. 7), both 1 at the roof:")
    say(f"    phi(xi) = sin(g xi) - (g/b) sinh(b xi) + eta (cosh(b xi) - cos(g xi)), g = {r['gam'][0]:.6f},")
    say(f"    b^2 = alpha^2 + g^2; largest difference at the {len(r['xs'])} nodes drawn: {r['shape_err']:.1e}")
    bf, be = R["eb"]
    say("  CHECK 3: the same code at alpha = 0 against the Euler-Bernoulli cantilever, beta_n H:")
    say("    " + ", ".join(f"{a:.6f} vs {b:.6f} ({a/b-1:+.1e})" for a, b in zip(bf, be)))
    say(f"  drawn: mode 1 alone, u(x, t) = phi_1(x) U cos(2 pi f1 (t - {T0B})), let go from full sway at")
    say(f"  t = {T0B} s of the page's clock, in real time (f1 = {f[0]:.4f} Hz, a sway every {r['TB']:.3f} s);")
    say(f"  {S.H_M:g} m drawn {S.H_M*UPM:g} units ({UPM:g} per m), {BAYS*BAY:g} m wide ({BAYS} bays), {STOREYS} storeys;"
        f" the roof's sway drawn {AMP:g} units")
    say("  (the displacements enlarged: the mode's shape is exact, its size is not a prediction); its rest")
    say("  outline in the rule's grey, as Figure 1 draws it; accelerometers on floors 6, 12, 18 and the roof;")
    say("  spot A (the detail) on floor 12.")
    say("")
    say("DETAIL A (middle): guided_ut's A0 pulse echo, as Figure 5 (a) shows it")
    say(f"  steel plate d = {G.D_PLATE*1e3:g} mm (a flange of one of the frame's members), E = {G.E/1e9:g} GPa,"
        f" nu = {G.NU}, rho = {G.RHO:g} kg/m3;")
    say(f"  c_L = {G.C_L:.1f}, c_T = {G.C_T:.1f}, c_R = {G.C_R:.2f} m/s")
    c = r["comp"]
    say(f"  a {G.NCYC} cycle Hann burst at {G.F0/1e3:g} kHz from the transducer at x = 0: {len(c['w'])} spectral lines,"
        f" {c['f'][0]/1e3:.1f} to {c['f'][-1]/1e3:.1f} kHz,")
    say(f"  each with its own k(omega) on the exact A0 branch; defect at D = {G.D_DEF:g} m, reflection R ="
        f" {G.R_DEF:g}, transmission {G.T_DEF:.3f}")
    say("  (frequency independent, no mode conversion); the transducer end does not reflect.")
    say(f"  A0 at 50 kHz: c_p = {r['cp']:.1f} m/s, c_g = {r['cg']:.1f} m/s, wavelength {r['cp']/G.F0*1e3:.1f} mm")
    say("  CHECK 4: the A0 branch at low frequency against Kirchhoff bending, c_p = (omega^2 D/(rho d))^(1/4):")
    for fr, cpl, ck in r["lo"]:
        say(f"    {fr/1e3:g} kHz: c_p = {cpl:.4f} m/s against {ck:.4f} m/s ({cpl/ck-1:+.1e}; shear and rotary"
            " inertia, falling as (k d)^2)")
    say(f"  CHECK 5: at f d = 20 MHz mm, c_p = {r['hi']:.4f} m/s against the Rayleigh speed {G.C_R:.4f} m/s"
        f" ({r['hi']/G.C_R-1:+.1e})")
    say(f"  CHECK 6: the lines rebuild the burst at the source to {r['src_err']:.1e} of its peak (-20 to 200 us)")
    say(f"  CHECK 7: the echo's envelope (Hilbert) peaks at {r['tpk']*1e6:.1f} us; the burst's centre + 2D/c_g ="
        f" {(r['tc']+2*G.D_DEF/r['cg'])*1e6:.1f} us")
    say("    (A0: the faster upper half of the band spreads less, so the smeared envelope peaks first, as in")
    say(f"    guided_ut.check.txt); -6 dB widths: the burst {r['w6b']*1e6:.1f} us, the echo {r['w6']*1e6:.1f} us"
        f" ({r['w6']/r['w6b']:.1f} x: dispersion)")
    say(f"  the record draws the echo in the accent where its envelope is above 3 % of its peak:"
        f" {r['win'][0]*1e6:.1f} to {r['win'][1]*1e6:.1f} us")
    say("  CHECK 8: the page's own sum (float32 lines, each line's phasor carried along x) and its record,")
    say(f"    against numpy (guided_ut.field and received) at 200, 540 and {POSTER_TM*1e6:.0f} us: largest"
        f" difference {page:.1e} (a unit burst)")
    say(f"  the field in view (x = 0 to {(NX-1)*DXM:.4f} m, {NX} points) peaks at {r['peak']:.3f}; from"
        f" {r['tend']*1e6:.0f} us it stays under {QUIET:g} of that")
    say(f"    and the page draws the plate at rest (the most it leaves out: {r['resid']:.1e} of the peak,"
        " slow low frequency A0)")
    say("  the arrow over the echo rides the centroid of the echo's energy still in the plate (squared Hilbert")
    say("    envelope along x, every 10 us), and fades as that energy leaves through the transducer")
    say("")
    say("THE RECORD (right): guided_ut.received(), u_z at the transducer, every 1 us to 1.4 ms, drawn as it")
    say("  arrives: its pen is at the model time of the plate beside it.")
    say("")
    say("DRAWING AND CLOCK")
    say(f"  plate {PPM:g} units per m along it; its 10 mm drawn {PT:g} units ({PT/(G.D_PLATE*PPM):.1f} x thicker);"
        f" u_z drawn {DZ:g} units at")
    say(f"  the peak and coloured through the diverging palette (saturating at 1/{CG:g} of the peak; the echo,")
    say(f"  spread out, peaks at {r['apk']:.2f} of the burst), eased into the plate's steel below 0.14 of the scale.")
    say(f"  the wave's time slowed {r['slow']:.0f} x; a cycle is {r['PW']:.3f} s on screen, {NSWAY} sways of the"
        f" building: the burst leaves at t = {TF} s")
    say(f"  and every {r['PW']:.3f} s after, the record is whole from {TF + T_TR*r['slow']:.2f} s and fades over"
        f" {FADE} s before the next burst.")
    say(f"  the still (print, and a reader who asks for less motion): t = {r['poster']:.3f} s, {POSTER_SWAYS} sways"
        f" after the building is let go (full sway)")
    say(f"  and the echo's peak reaching the transducer ({POSTER_TM*1e6:.0f} us; the slowing is set by it).")
    say("")
    say("OVERLAP (engine ?overlap, common.overlaps at 672 px; common.still also samples every 0.25 s")
    say("  up to the poster):")
    for k, v in over.items():
        say(f"  {k}: labels {v['labels'] or 'none'}, crossings {v['crossings'] or 'none'}")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(HERE, "shm_cover.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


def build():
    r = model()
    common.build_html(NAME, TITLE, ARIA, 1000, 173, page_data(r), wt_lib.QUIET_CTL + "\n" + JS)
    page = page_check(r)
    png = common.still(NAME, width=672)
    print("still:", png)
    P = r["PW"]
    times = [0.3, 0.8, 1.4, 2.0, 2.6, r["poster"], r["poster"] + 0.6, TF + P - 0.3, TF + P + 1.0, TF + P + 3.3]
    over = common.overlaps(NAME, times)
    report(r, page, over)
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.1, 0.25, 0.45, 0.8, 1.4, 2.2, r["poster"], 5.5, TF + P - 0.2]))
    return r


if __name__ == "__main__":
    build()
