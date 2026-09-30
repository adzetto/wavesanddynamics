"""Figure 5 of the SHM article (understanding-shm-and-ndt, image6).

His caption: "(a) Guided wave testing, using active ultrasonic excitation or
passive acoustic emission, shown with its resulting dispersed signal. (b)
Bulk wave, pulse echo ultrasonic testing, shown with its resulting echo
trace."

His picture has four parts, each with his words, kept verbatim here: the
guided wave test and its dispersed received signal, the bulk wave pulse
echo test and its A scan. The physics is the waves guide's own
(guided_ut.py, Figure 12; bulk_ut.py, Figure 11), imported, not copied:

(a) A0 Lamb waves in a free steel plate 10 mm thick (Rayleigh-Lamb, exact
    roots), a 3 cycle Hann burst at 50 kHz from a transducer at x = 0 and
    a defect 1.5 m away (reflection 0.5): the field along the plate and
    the received signal are the Fourier synthesis with the A0 dispersion
    relation, evaluated by the page for every frame. Below, the A0 mode at
    50 kHz through the thickness at true scale (its displacements from the
    traction free null vector): the wavelength (38 mm) is of the order of
    the thickness (10 mm), and the wave moves the whole section.
(b) The 2D elastic finite difference model (EFIT) of a 50 x 25 mm steel
    block: a 10 mm, 5 MHz probe over a flaw; its field every 0.05 us and
    the A scan it records, from the same run (bulk_ut's cached model).

Run: python tools/numfig/sd_waves.py [--look]   (writes content/anim/
nf-sd-waves.html, its field chunks nf-sd-waves-field-*.png, the still
nf-sd-waves.webp, and tools/numfig/sd_waves.check.txt)
"""
import os
import sys

import numpy as np
from scipy.signal import hilbert

import common
import sd_check
from sd_check import poster_js
import guided_ut as G
import bulk_ut as B

NAME = "sd-waves"
HERE = os.path.dirname(os.path.abspath(__file__))

# (a) guided waves: the A0 pulse echo of guided_ut, on a plate drawn to X_A metres
X_A = 1.8                           # m of plate drawn
DXA = 2.5e-3                        # m, the page's field points
SLOW_A = G.SLOW                     # 5000
M0 = -20e-6                         # s, the cycle's model clock starts
TEND_A = 1360e-6                    # s, and ends (the echo is back, the plate is quiet)
T_TRACE = 1400e-6                   # s, the received signal shown
SNAP_A = 724e-6                     # s, the moment the still and the idle state show
# (b) bulk waves: bulk_ut's pulse echo run
SLOW_B = B.SLOW                     # 8e5
TSNAP_B = 3.35                      # us, bulk_ut's snapshot (flaw echo up, incident past the flaw)
CUTS_B = [0, 25, 70, 130, 201]      # field chunks, as bulk_ut
# the page's clock
TA0 = 0.35                          # s: (a)'s first cycle starts
GAP = 0.6                           # s between the cycles
HOLD = 1.5                          # s after (b)'s cycle
FADE = 0.4                          # s: an idle state fades out before its panel's cycle, in after it


def a_model():
    comp = G.components("A")
    cp, cg = G.group_velocity("A", G.F0)
    tc = G.NCYC / G.F0 / 2
    ttr = np.arange(0, T_TRACE + 0.5e-6, 1e-6)
    trace = G.received(comp, ttr)
    # the defect echo alone: its envelope peak, where it is drawn in the accent
    te = np.arange(0, 2.4e-3, 0.1e-6)
    ee = G.synth(comp, 2 * G.D_DEF, te, G.R_DEF)
    tpk, apk, env = G.envelope_peak(te, ee, 0)
    near = np.abs(te - tpk) < 600e-6
    big = te[near][env[near] >= 0.03 * apk]
    win = (max(big[0], 0.0), min(big[-1], T_TRACE))
    w6 = G.width6(te, env, tpk - 600e-6, tpk + 600e-6)
    inc = G.synth(comp, 0.0, np.arange(0, 200e-6, 0.1e-6))
    w6b = G.width6(np.arange(0, 200e-6, 0.1e-6), np.abs(hilbert(inc)), 0, 200e-6)
    # the mode through the thickness at 50 kHz, true scale
    nz = 9
    z = np.linspace(-G.H, G.H, nz)
    ux, uz, det = G.mode_shape("A", G.F0, cp, z)
    return dict(comp=comp, cp=cp, cg=cg, tc=tc, ttr=ttr, trace=trace, echo_t=tpk, echo_amp=apk, win=win,
                w6=w6, w6b=w6b, z=z, ux=ux, uz=uz, det=det, pred=tc + 2 * G.D_DEF / cg)


def inset(A, x0, y0, ppmm, lam_n=2.0, gain=5.0):
    """The A0 mode's section at true scale: its faces and a mesh, displaced by
    Re{u(z) e^{ikx}} (normalised to `gain` drawing units), as polylines in
    drawing units; x0, y0 the top left corner of the undeformed section."""
    lam = A["cp"] / G.F0
    k = 2 * np.pi / lam
    L = lam_n * lam
    s = gain / max(np.abs(A["ux"]).max(), np.abs(A["uz"]).max())
    zf = np.linspace(-G.H, G.H, 41)
    uxf, uzf, _ = G.mode_shape("A", G.F0, A["cp"], zf)

    def pt(x, iz, fine=False):
        ux_, uz_, z_ = (uxf[iz], uzf[iz], zf[iz]) if fine else (A["ux"][iz], A["uz"][iz], A["z"][iz])
        e = np.exp(1j * k * x)
        X = x0 + x * 1e3 * ppmm + s * (ux_ * e).real
        Y = y0 + (G.H - z_) * 1e3 * ppmm - s * (uz_ * e).real
        return [round(float(X), 2), round(float(Y), 2)]

    xs = np.linspace(0, L, 161)
    top = [pt(x, 40, True) for x in xs]
    bot = [pt(x, 0, True) for x in xs]
    verts = [[pt(x, iz, True) for iz in range(41)] for x in np.arange(0, L + 1e-9, lam / 12)]
    hors = [[pt(x, iz) for x in xs] for iz in range(1, len(A["z"]) - 1, 2)]
    return dict(top=top, bot=bot, verts=verts, hors=hors, w=L * 1e3 * ppmm, h=2 * G.H * 1e3 * ppmm,
                lam=lam * 1e3 * ppmm, lam_mm=lam * 1e3, gain=gain)


def b_model():
    ascan, field, dt = B._cached("pe", lambda: B.pulse_echo())
    dt = float(dt)
    ts = (B.REC_EVERY * np.arange(ascan.size) + 0.5) * dt - B.T0
    field = np.concatenate([np.zeros_like(field[:1]), field])       # frame k at 0.05 k us
    X, Z = B.flaw_outline(200001)
    under = np.abs(X - B.PROBE["x"]) <= B.PROBE["w"] / 2
    d_f = float(Z[under].min())
    x_top = float(X[np.argmin(np.where(under, Z, 1e9))])
    tf_th, tb_th = 2 * d_f / B.CL, 2 * B.DB / B.CL
    tf, af = B.env_peak(ts, ascan, tf_th - .6, tf_th + .6)
    tb, ab = B.env_peak(ts, ascan, tb_th - .6, tb_th + .6)
    t_ip, a_ip = B.env_peak(ts, ascan, -.3, .6)
    norm = np.abs(ascan).max()
    env = np.abs(hilbert(ascan))

    def window(t_c):
        i = np.argmin(np.abs(ts - t_c))
        lo = hi = i
        while lo > 0 and env[lo] > 0.08 * env[i]:
            lo -= 1
        while hi < env.size - 1 and env[hi] > 0.08 * env[i]:
            hi += 1
        return [float(ts[lo]), float(ts[hi])]

    return dict(ascan=ascan, field=field, dt=dt, ts=ts, d_f=d_f, x_top=x_top, tf=tf, af=af, tb=tb, ab=ab,
                tf_th=tf_th, tb_th=tb_th, norm=norm, a_ip=a_ip, wf=window(tf), wb=window(tb))


def field_chunks(field):
    """bulk_ut's storage: p/p0 in steps of p0/126 (7 bit), clipped at +-FCLIP, in
    atlases of 10 frames a row, chunked in the order they play."""
    q = (128 + 2 * np.clip(np.round(field / B.FCLIP * 63), -63, 63)).astype(np.uint8)
    q = q.transpose(0, 2, 1)                                             # frames (z, x)
    chunks, sizes = [], []
    for i, (a, b_) in enumerate(zip(CUTS_B[:-1], CUTS_B[1:])):
        png = B._png(B._atlas(q[a:b_], 10))
        src = f"nf-{NAME}-field-{i}.png"
        with open(os.path.join(common.ANIM, src), "wb") as fh:
            fh.write(png)
        chunks.append({"n0": a, "n1": b_, "cols": 10, "src": src})
        sizes.append(len(png))
    return chunks, sizes


JS = r"""
const D = DATA;
const lab = t0 => settle(t0, .28);
const rise = s => 4 * (1 - s);
const L = D.loop, TA0 = D.ta0, FADE = D.fade;
/* the clock: (a)'s cycle, a gap, (b)'s cycle, a hold; each panel shows its
   idle state (the still's moment, its signal whole) while the other runs */
const loopU = () => ((t - TA0) % L + L) % L;
const A = D.a, Bb = D.b;
const DUR_A = (A.tend - A.m0) * A.slow, U0_B = DUR_A + D.gap, DUR_B = Bb.tend * Bb.slow / 1e6;
function stateA() {
  const u = loopU();
  if (t < TA0) return { run: false, idle: 0, tm: A.m0, rec: -1 };        // before the first cycle: quiet
  if (u < DUR_A) return { run: true, idle: 0, tm: A.m0 + u / A.slow, rec: A.m0 + u / A.slow };
  const inA = clamp((u - DUR_A) / FADE), outA = 1 - clamp((u - (L - FADE)) / FADE);
  return { run: false, idle: Math.min(inA, outA), tm: A.snap, rec: Infinity, wipe: outA };
}
function stateB() {
  const u = loopU();
  if (u >= U0_B && u < U0_B + DUR_B) return { run: true, idle: 0, ts: (u - U0_B) / Bb.slow * 1e6 };
  const back = u >= U0_B + DUR_B ? clamp((u - U0_B - DUR_B) / FADE) : 1;
  const out = u < U0_B ? 1 - clamp((u - (U0_B - FADE)) / FADE) : 1;
  return { run: false, idle: Math.min(back, out), ts: Bb.snap };
}
const POSTER_T = D.poster;

/* ------------------------------------------------------------ shared */
const FLUT = _ramp(['#043052', '#2E6A9E', '#9CBBD6', '#E3EBF2', '#DEABAB', '#B03F4D', '#651020'].map(_hex));
function offscreen(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; const g = c.getContext('2d'); return { c, g, img: g.createImageData(w, h) }; }
function cutEdge(x, y0, y1, o = {}) {                      // a zigzag cut: the plate continues
  const pts = [], n = 6, a = 4;
  for (let i = 0; i <= n; i++) pts.push([x + (i % 2 ? a : -a) * (i > 0 && i < n ? 1 : 0), lerp(y0 - 3, y1 + 3, i / n)]);
  line(pts, { color: C.ink, width: 1.3, ...o });
}
const title = (l, s1, s2, y, a) => {
  const w = panel(l, 20, y, { alpha: a });
  text(s1, 20 + w + 8, y, { size: 17, color: C.body, alpha: a });
  text(s2, 20 + w + 8, y + 21, { size: 15, color: C.body, alpha: a });
};

/* ------------------------------------------------------------ (a) guided */
const XU = x => A.px0 + x * A.ppm, PY = A.py, PH = A.ph;
const MODE = { w: b64f32(A.c.w), k: b64f32(A.c.k), a: b64f32(A.c.a), p: b64f32(A.c.p) };
const TR = b64f32(A.trace), NX = A.nx, DXM = A.dx, ID = Math.round(A.D / DXM);
const U = new Float64Array(NX);
/* the Fourier sum along the plate at model time tm (s): the incident wave from
   x = 0 (transmitted T past the defect) and the echo from the defect (R) */
function fieldAt(tm) {
  U.fill(0);
  const m = MODE, n = m.w.length, D_ = A.D, R = A.R, T = A.T;
  for (let j = 0; j < n; j++) {
    const k = m.k[j], a = m.a[j], ph = m.w[j] * tm + m.p[j];
    const cd = Math.cos(k * DXM), sd = Math.sin(k * DXM);
    let c = Math.cos(ph), s = Math.sin(ph);
    for (let i = 0; i < NX; i++) {
      U[i] += (i <= ID ? a : a * T) * c;
      const c2 = c * cd + s * sd; s = s * cd - c * sd; c = c2;
    }
    const b = ph - 2 * k * D_;
    c = Math.cos(b); s = Math.sin(b);
    for (let i = 0; i <= ID; i++) {
      U[i] += a * R * c;
      const c2 = c * cd - s * sd; s = s * cd + c * sd; c = c2;
    }
  }
  return U;
}
const FIM = offscreen(NX, 3);
let _fa = null;
function paintField(tm, alpha) {
  if (alpha <= 0) return;
  if (_fa !== tm) {
    const u = fieldAt(tm), d = FIM.img.data;
    for (let i = 0; i < NX; i++) {
      const li = Math.round((clamp(u[i] / D.clip, -1, 1) + 1) * 127.5) * 3;
      for (let r = 0; r < 3; r++) { const o = (r * NX + i) * 4; d[o] = FLUT[li]; d[o + 1] = FLUT[li + 1]; d[o + 2] = FLUT[li + 2]; d[o + 3] = 255; }
    }
    FIM.g.putImageData(FIM.img, 0, 0); _fa = tm;
  }
  ctx.save(); ctx.globalAlpha *= alpha; ctx.imageSmoothingEnabled = true;
  ctx.beginPath(); ctx.rect(XU(0), PY, XU(A.xend) - XU(0), PH); ctx.clip();
  ctx.drawImage(FIM.c, 0, 1, NX, 1, XU(-DXM / 2), PY, NX * DXM * A.ppm, PH);
  ctx.restore();
}
function notch(xc, a) {                                    // the defect: a surface notch
  const w = 5, dp = PH * 0.45, x = XU(xc);
  ctx.save(); ctx.globalAlpha *= a;
  ctx.beginPath(); ctx.moveTo(x - w / 2, PY - .5); ctx.lineTo(x - w / 2, PY + dp - w / 2);
  ctx.arc(x, PY + dp - w / 2, w / 2, Math.PI, 0, true); ctx.lineTo(x + w / 2, PY - .5); ctx.closePath();
  ctx.fillStyle = C.accent; ctx.fill(); ctx.strokeStyle = '#781E2C'; ctx.lineWidth = 1.1; ctx.stroke(); ctx.restore();
}
/* arrows under the packets: their centres move at the A0 group velocity */
function packets(tm, al) {
  const cg = A.cg, dt = tm - A.tc, y = PY + PH + 10;
  if (dt <= 0 || al <= 0) return { inc: 0, echo: 0 };
  const put = (x, dir, col) => {
    if (x < 0.12 || x > A.xend - 0.1) return 0;
    const xm = XU(x);
    arrow(xm - dir * 13, y, xm + dir * 13, y, { color: col, width: 1.5, head: 8, alpha: al });
    return 1;
  };
  const xi = cg * dt;
  const inc = put(xi, 1, C.ink);
  const echo = xi > A.D ? put(2 * A.D - xi, -1, C.accent) : 0;
  return { inc: inc && xi < A.D ? 1 : 0, echo };
}
function panelA() {
  const st = stateA(), a0 = lab(0);
  title('a', 'Guided wave testing', '(active ultrasonic excitation, or passive acoustic emission)', 34, a0);
  // the plate: steel, the model's field, the outline drawing itself
  const x0 = XU(0), x1 = XU(A.xend), pa = seg(0, .4);
  ctx.save(); ctx.globalAlpha *= seg(.05, .25); ctx.fillStyle = C.steel; ctx.fillRect(x0, PY, x1 - x0, PH); ctx.restore();
  const fa = st.run ? 1 : st.idle;
  paintField(st.tm, fa);
  line([[x1, PY], [x0, PY], [x0, PY + PH], [x1, PY + PH]], { width: 1.6, progress: pa });
  line([[x0, PY + PH], [x1, PY + PH]], { width: 2.4, progress: pa });
  cutEdge(x1, PY, PY + PH, { alpha: seg(.3, .2) });
  // transducer and defect, and his words for them
  const tIn = settle(.12, .28), dIn = settle(.18, .28);
  ctx.save(); ctx.globalAlpha *= tIn; ctx.fillStyle = C.navy; ctx.fillRect(x0, PY - 13 - 8 * (1 - tIn), 12, 13); ctx.restore();
  ctx.save(); ctx.translate(0, -8 * (1 - dIn)); notch(A.D, dIn); ctx.restore();
  const lIn = lab(.25);
  text('transducer (send/receive)', x0 - 4, PY - 22 + rise(lIn), { size: 15, color: C.body, alpha: lIn });
  text('defect', XU(A.D), PY - 22 + rise(lIn), { size: 15, color: C.body, align: 'center', alpha: lIn });
  // the thickness, at the cut end
  const ha = lab(.35), xh = x1 + 16;
  arrow(xh, PY + PH / 2, xh, PY, { width: 1, head: 6, alpha: ha }); arrow(xh, PY + PH / 2, xh, PY + PH, { width: 1, head: 6, alpha: ha });
  math('h', xh + 7, PY + PH / 2 + 6, { size: 17, alpha: ha });
  // the packets under the plate, and his names for the two waves
  const pk = packets(st.tm, st.run ? 1 : st.idle);
  const ly = PY + PH + 38, la = lab(.4);
  const on = (k) => st.run ? (k ? .45 + .55 * pk.echo : .45 + .55 * pk.inc) : 1;
  arrow(x0 + 4, ly - 5, x0 + 30, ly - 5, { color: C.ink, width: 1.5, head: 8, alpha: la * on(0) });
  text('incident guided wave', x0 + 38, ly, { size: 15, alpha: la * on(0) });
  arrow(x0 + 30, ly + 14, x0 + 4, ly + 14, { color: C.accent, width: 1.5, head: 8, alpha: la * on(1) });
  text('reflected (echo) wave', x0 + 38, ly + 19, { size: 15, color: C.accent, alpha: la * on(1) });
  cbar(XU(1.1), PY + PH + 30, 100, 'u_{z}/u_{0}', lab(.45));
  // the A0 mode at 50 kHz, through the thickness, at true scale
  insetA(lab(.45));
  const na = lab(.55);
  math(A.note1, x0 - 4, A.ny, { size: 15, alpha: na });
  text(A.note2[0], x0 - 4, A.ny + 21, { size: 14, color: C.muted, alpha: na });
  text(A.note2[1], x0 - 4, A.ny + 38, { size: 14, color: C.muted, alpha: na });
  // the received signal
  const P = A.plot, g = axes({ ...P, xlim: [0, A.tmax], ylim: [-1.15, 1.15], xticks: [0, 200, 400, 600, 800, 1000, 1200, 1400],
                               yticks: [-1, 0, 1], ylabel: '\\rm{Amplitude}', ylabelGap: 36, progress: seg(.08, .4) });
  const ta = lab(.2);
  text('Received signal: dispersed wave packet', P.x + P.w / 2, P.y - 14 + rise(ta), { size: 16, align: 'center', alpha: ta });
  const xl = seg(.3, .3);
  const w1 = text('Time ', 0, -1e4, { size: 17, alpha: 0 }), w2 = math('t\\ (\\rm{µs})', 0, -1e4, { size: 17, alpha: 0 });
  text('Time ', P.x + P.w / 2 - (w1 + w2) / 2, P.y + P.h + 48, { size: 17, alpha: xl });
  math('t\\ (\\rm{µs})', P.x + P.w / 2 - (w1 + w2) / 2 + w1, P.y + P.h + 48, { size: 17, alpha: xl });
  g.inside(() => line([[P.x, g.Y(0)], [P.x + P.w, g.Y(0)]], { color: C.rule, width: 1 }));
  const upto = st.run ? st.rec * 1e6 : (t < TA0 ? -1 : A.tmax), wipe = st.run ? 1 : (st.wipe ?? 1);
  const n = Math.min(TR.length, Math.floor(upto) + 1);
  if (n > 1 && wipe > 0) {
    const ia = Math.round(A.win[0]), ib = Math.round(A.win[1]);
    const part = (i0, i1, col) => { i1 = Math.min(i1, n); if (i1 - i0 < 2) return; const pts = []; for (let i = i0; i < i1; i++) pts.push([g.X(i), g.Y(TR[i])]); g.inside(() => line(pts, { color: col, width: 1.6, alpha: wipe })); };
    part(0, ia + 1, C.navy); part(ia, ib + 1, C.accent); part(ib, TR.length, C.navy);
  }
  if (st.run && upto >= 0) {                                // the cursor, under the labels' band
    const xc = g.X(Math.min(upto, A.tmax)), i = clamp(Math.round(upto), 0, TR.length - 1);
    line([[xc, g.Y(.5)], [xc, P.y + P.h - 2]], { color: C.ink, width: 1, alpha: .45 });
    dot(xc, g.Y(upto < 0 ? 0 : TR[i]), 3, { color: C.navy, fill: C.navy });
  }
  const seen = te => st.run ? clamp((upto - te) / 40) : (t < TA0 ? 0 : wipe);
  text('outgoing', g.X(80), g.Y(.86), { size: 15, color: C.body, alpha: seen(40) * lab(.4) });
  text('pulse', g.X(80), g.Y(.86) + 17, { size: 15, color: C.body, alpha: seen(40) * lab(.4) });
  const ex = g.X(A.echolab);
  text('defect echo', ex, g.Y(.86), { size: 15, color: C.accent, align: 'center', alpha: seen(A.echo) });
  text('(spread out by dispersion)', ex, g.Y(.86) + 17, { size: 15, color: C.accent, align: 'center', alpha: seen(A.echo) });
  const pl = lab(.8);
  A.params.forEach((s, i) => text(s, P.x - 36, P.y + P.h + 80 + 18 * i, { size: 14, color: C.muted, alpha: pl }));
  math('\\rm{time slowed }5\\,\\times\\,10^{3}', 958, 34, { size: 14, color: C.muted, align: 'right', alpha: lab(.5) });
}
/* a colour bar of the field's ramp, -0.5 ... 0.5 */
function cbar(x, y, w, labl, a) {
  if (a <= 0) return;
  const g = ctx.createLinearGradient(x, 0, x + w, 0);
  for (let i = 0; i <= 64; i++) { const k = Math.round(i / 64 * 255) * 3; g.addColorStop(i / 64, `rgb(${FLUT[k]},${FLUT[k + 1]},${FLUT[k + 2]})`); }
  ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = g; ctx.fillRect(x, y, w, 8); ctx.restore();
  line([[x, y], [x + w, y], [x + w, y + 8], [x, y + 8]], { width: .8, close: true, alpha: a });
  for (const [v, s] of [[-.5, '-0.5'], [0, '0'], [.5, '0.5']]) {
    const xx = x + (v / D.clip + 1) / 2 * w;
    line([[xx, y + 8], [xx, y + 11]], { width: .8, alpha: a });
    math(s, xx, y + 25, { size: 14, align: 'center', alpha: a });
  }
  math(labl, x - 8, y + 9, { size: 15, align: 'right', alpha: a });
}
function insetA(a) {
  if (a <= 0) return;
  const I = A.inset;
  ctx.save(); ctx.globalAlpha *= a;
  const poly = I.top.concat(I.bot.slice().reverse());
  ctx.beginPath(); ctx.moveTo(poly[0][0], poly[0][1]); for (const p of poly) ctx.lineTo(p[0], p[1]); ctx.closePath();
  ctx.fillStyle = C.steel; ctx.fill(); ctx.restore();
  for (const v of I.verts) line(v, { color: C.sky, width: 1, alpha: a });
  for (const h of I.hors) line(h, { color: C.sky, width: 1, alpha: a });
  line(I.top, { width: 1.6, alpha: a }); line(I.bot, { width: 1.6, alpha: a });
  const x0 = I.x0, y0 = I.y0;
  // one wavelength, dimensioned: |<- label ->|, the line broken for the label (no knockout to fade)
  const d0 = x0 + I.lam * .25, d1 = x0 + I.lam * 1.25, dy = y0 + I.h + 20, dl = '\\lambda\\ = ' + I.lam_mm.toFixed(0) + '\\,\\rm{mm}';
  const dw = math(dl, 0, -1e4, { size: 15, alpha: 0 }), dm = (d0 + d1) / 2;
  arrow(dm - dw / 2 - 6, dy, d0, dy, { width: 1.1, head: 7, alpha: a }); arrow(dm + dw / 2 + 6, dy, d1, dy, { width: 1.1, head: 7, alpha: a });
  line([[d0, dy - 6], [d0, dy + 6]], { width: 1, alpha: a }); line([[d1, dy - 6], [d1, dy + 6]], { width: 1, alpha: a });
  math(dl, dm, dy + 5, { size: 15, align: 'center', alpha: a });
  const xh = x0 + I.w + 14;
  arrow(xh, y0 + I.h / 2, xh, y0, { width: 1, head: 6, alpha: a }); arrow(xh, y0 + I.h / 2, xh, y0 + I.h, { width: 1, head: 6, alpha: a });
  math('h = 10\\,\\rm{mm}', xh + 7, y0 + I.h / 2 + 5, { size: 15, alpha: a });
  math(A.insetlab, x0, y0 - 12, { size: 14, color: C.muted, alpha: a });
}

/* ------------------------------------------------------------ (b) bulk */
const S = Bb.s, BW = Bb.wb * S, BD = Bb.db * S, BX = Bb.bx, BY = Bb.by;
const XB = x => BX + x * S, YB = z => BY + z * S;
const AS = b64f32(Bb.ascan.v);
const FLD = Bb.field.chunks.map(() => null);
function grab(src) {
  return new Promise((ok, no) => {
    const im = new Image();
    im.onload = () => {
      try {                                  // (a page opened from a file cannot read its pixels: no field then)
        const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
        const g = c.getContext('2d', { willReadFrequently: true }); g.drawImage(im, 0, 0);
        const d = g.getImageData(0, 0, c.width, c.height).data, px = new Uint8Array(c.width * c.height);
        for (let i = 0; i < px.length; i++) px[i] = d[4 * i];
        ok({ W: c.width, px });
      } catch (e) { no(e); }
    };
    im.onerror = no; im.src = src;
  });
}
const redraw = () => { if (document.documentElement.dataset.ready === '1' && !playing) render(); };
const first = grab(Bb.field.chunks[0].src).then(d => { FLD[0] = d; redraw(); });
const rest = first.then(async () => { for (let i = 1; i < FLD.length; i++) { FLD[i] = await grab(Bb.field.chunks[i].src); redraw(); } });
const FC = offscreen(Bb.field.w, Bb.field.h);
const FMAP = new Uint16Array(256);
for (let b = 0; b < 256; b++) FMAP[b] = 3 * Math.round(clamp(((b - 128) / Bb.field.span * 2 + 1) / 2) * 255);
let fcur = -1;
function fieldFrame(n) {
  const ch = Bb.field.chunks;
  let i = 0; while (i < ch.length - 1 && n >= ch[i].n1) i++;
  const F = FLD[i];
  if (!F) return false;
  if (n === fcur) return true;
  fcur = n;
  const { w, h } = Bb.field, m = n - ch[i].n0, c = m % ch[i].cols, r = Math.floor(m / ch[i].cols), d = FC.img.data;
  for (let z = 0; z < h; z++) {
    let s = (r * h + z) * F.W + c * w, o = z * w * 4;
    for (let x = 0; x < w; x++, s++, o += 4) { const Lq = FMAP[F.px[s]]; d[o] = FLUT[Lq]; d[o + 1] = FLUT[Lq + 1]; d[o + 2] = FLUT[Lq + 2]; d[o + 3] = 255; }
  }
  FC.g.putImageData(FC.img, 0, 0);
  return true;
}
function ride(s, x, z, up, col, a) {                        // a label riding a front at depth z (mm)
  if (a <= 0) return;
  const y0 = YB(up ? z - 1.2 : z + 1.2), y1 = YB(up ? z - 3.7 : z + 3.7);
  arrow(XB(x), y0, XB(x), y1, { color: col, width: 1.4, head: 7, alpha: a });
  text(s, XB(x + 1.1), (y0 + y1) / 2 + 5, { size: 15, color: col, alpha: a });
}
function panelB() {
  const st = stateB(), a0 = lab(.05);
  title('b', 'Bulk wave testing', '(conventional pulse echo / phased array ultrasonic testing)', Bb.ty, a0);
  ctx.save(); ctx.globalAlpha *= seg(.05, .3); ctx.fillStyle = C.steel; ctx.fillRect(BX, BY, BW, BD); ctx.restore();
  const fa = (st.run ? 1 : st.idle) * seg(.1, .4);
  if (fa > 0 && fieldFrame(clamp(Math.round(st.ts / Bb.field.dt), 0, Bb.field.n - 1))) {
    ctx.save(); ctx.globalAlpha *= fa; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(FC.c, BX, BY, BW, BD); ctx.restore();
  }
  const pr = seg(.05, .4);
  line([[BX, BY + BD], [BX, BY], [BX + BW, BY], [BX + BW, BY + BD]], { width: 1.6, progress: pr });
  line([[BX, BY + BD], [BX + BW, BY + BD]], { width: 2.4, progress: pr });
  const fl = seg(.3, .25);
  if (fl > 0) line(Bb.flaw.x.map((x, i) => [XB(x), YB(Bb.flaw.z[i])]), { color: '#781E2C', width: 1.1, fill: C.accent, close: true, alpha: fl });
  const sp = settle(.18, .28), [p0, p1] = Bb.probe;
  ctx.save(); ctx.globalAlpha *= sp; ctx.fillStyle = C.navy; ctx.fillRect(XB(p0), BY - 15 - 12 * (1 - sp), (p1 - p0) * S, 15); ctx.restore();
  const la = lab(.3);
  text('transducer', XB((p0 + p1) / 2), BY - 23 + rise(la), { size: 15, color: C.body, align: 'center', alpha: la });
  text('flaw', XB(Bb.flaw.lab[0]), YB(Bb.flaw.lab[1]), { size: 15, color: C.accent, align: 'right', alpha: lab(.35) });
  text('back wall', BX + BW, BY + BD + 20, { size: 15, color: C.body, align: 'right', alpha: lab(.38) });
  // the thickness h and one wavelength
  const da = lab(.35), xd = BX - 16;
  arrow(xd, BY + 1, xd, BY + BD - 1, { width: 1.1, head: 7, both: true, alpha: da });
  text('thickness', xd - 8, BY + BD / 2 - 2, { size: 15, color: C.body, align: 'right', alpha: da });
  math('h', xd - 8, BY + BD / 2 + 17, { size: 17, align: 'right', alpha: da });
  // one wavelength at the block's own scale, beside it: lambda against h
  // (a gap this small is dimensioned from outside: two arrows pointing in at its two lines)
  const lx = BX + BW + 15, lam = Bb.lam.mm * S, ly0 = BY + BD / 2 - lam / 2;
  line([[lx - 6, ly0], [lx + 6, ly0]], { width: 1.1, alpha: da }); line([[lx - 6, ly0 + lam], [lx + 6, ly0 + lam]], { width: 1.1, alpha: da });
  arrow(lx, ly0 - 16, lx, ly0, { width: 1.1, head: 6, alpha: da }); arrow(lx, ly0 + lam + 16, lx, ly0 + lam, { width: 1.1, head: 6, alpha: da });
  math('\\lambda', lx + 10, BY + BD / 2 + 6, { size: 17, alpha: da });
  // his words riding the fronts, at the model's c_L
  if (st.run || st.idle > 0) {
    const al = st.run ? 1 : st.idle, ta = st.ts - Bb.t0, c = Bb.cl, [xt, zt] = Bb.flaw.top;
    const win = (a0_, a1, b0, b1) => clamp((ta - a0_) / (a1 - a0_)) * (1 - clamp((ta - b0) / (b1 - b0)));
    ride('incident pulse', Bb.rx, c * ta, false, C.ink, al * win(0.5, 0.8, 3.2, 3.5));
    ride('flaw echo', xt + 1.5, 2 * zt - c * ta, true, C.accent, al * win(2.25, 2.55, 3.08, 3.4));
    ride('back wall echo', Bb.rx, 2 * Bb.db - c * ta, true, C.ink, al * win(4.6, 4.9, 7.45, 7.75));
  }
  cbar(BX + 44, BY + BD + 13, 100, 'p/p_{0}', lab(.45));
  const na = lab(.55);
  math(Bb.note, BX - 50, Bb.ny, { size: 15, alpha: na });
  math(Bb.params, BX - 50, Bb.ny + 22, { size: 14, color: C.muted, alpha: lab(.8) });
  // the A scan: time, and the depth it reads
  const P = Bb.plot;
  const g = axes({ ...P, xlim: [-0.5, 10], ylim: [-1.15, 1.15], xticks: [0, 2, 4, 6, 8, 10], yticks: [-1, 0, 1],
                   ylabel: '\\rm{Amplitude}', ylabelGap: 36, progress: seg(.1, .4) });
  const xa = seg(.3, .3);
  g.inside(() => line([[P.x, g.Y(0)], [P.x + P.w, g.Y(0)]], { color: C.rule, width: 1, alpha: xa }));
  for (const z of [0, 5, 10, 15, 20, 25]) {
    const x = g.X(2 * z / Bb.cl);
    line([[x, P.y], [x, P.y + 5]], { width: 1.1, alpha: xa });
    math(String(z), x, P.y - 7, { size: 15, align: 'center', alpha: xa });
  }
  math('\\rm{depth }z = c_{\\rm{L}}t/2\\ (\\rm{mm})', P.x + P.w / 2, P.y - 28, { size: 15, align: 'center', alpha: xa });
  const tt = lab(.22);
  text('Resulting A scan', P.x + P.w / 2, P.y - 52 + rise(tt), { size: 16, align: 'center', alpha: tt });
  const w1 = text('Time (≈ depth) ', 0, -1e4, { size: 17, alpha: 0 }), w2 = math('t\\ (\\rm{µs})', 0, -1e4, { size: 17, alpha: 0 });
  text('Time (≈ depth) ', P.x + P.w / 2 - (w1 + w2) / 2, P.y + P.h + 48, { size: 17, alpha: xa });
  math('t\\ (\\rm{µs})', P.x + P.w / 2 - (w1 + w2) / 2 + w1, P.y + P.h + 48, { size: 17, alpha: xa });
  // the trace, drawn as the probe records it; whole while the other panel runs
  const E = Bb.echo, q0 = Bb.ascan.t0, dq = Bb.ascan.dt, n = Bb.ascan.n;
  const tr = st.run ? st.ts - Bb.t0 : 10;
  const m = Math.min(n - 1, Math.floor((tr - q0) / dq));
  const outB = st.run ? 1 : (loopU() < U0_B ? 1 - clamp((loopU() - (U0_B - FADE)) / FADE) : 1);
  if (m >= 1 && outB > 0) {
    const pts = []; for (let i = 0; i <= m; i++) pts.push([g.X(q0 + i * dq), g.Y(AS[i])]);
    const [w0, w1_] = E.wf, i0 = Math.ceil((w0 - q0) / dq), i1 = Math.min(m, Math.floor((w1_ - q0) / dq));
    g.inside(() => { line(pts, { color: C.navy, width: 1.6, alpha: outB }); if (i1 > i0) line(pts.slice(i0, i1 + 1), { color: C.accent, width: 1.7, alpha: outB }); });
  }
  if (st.run) {                                             // the cursor, under the labels' band
    const xc = g.X(tr);
    line([[xc, g.Y(.55)], [xc, P.y + P.h - 2]], { color: C.ink, width: 1, alpha: .45 });
    dot(xc, g.Y(AS[clamp(Math.round((tr - q0) / dq), 0, n - 1)]), 3, { color: C.navy });
  }
  const seen = te => (st.run ? clamp((tr - te) / 0.4) : 1) * outB;
  for (const [te, tt_] of [[E.tf, E.tf_th], [E.tb, E.tb_th]]) {       // where 2z/c_L puts each echo
    const a = seen(te + .3) * .9;
    if (a > 0) line([[g.X(tt_), P.y + 1], [g.X(tt_), P.y + P.h - 1]], { color: C.guide, width: 1, dash: [5, 4], alpha: a });
  }
  const two = (s1, s2, x, col, al, align = 'left') => { text(s1, x, g.Y(.86), { size: 15, color: col, align, alpha: al }); text(s2, x, g.Y(.86) + 17, { size: 15, color: col, align, alpha: al }); };
  two('initial', 'pulse', g.X(0.45), C.body, seen(0.3));
  two('flaw', 'echo', g.X(E.tf_th + 0.15), C.accent, seen(E.tf + .3));
  two('back wall', 'echo', g.X(E.tb_th - 0.15), C.body, seen(E.tb + .3), 'right');
  math('\\rm{time slowed }8\\,\\times\\,10^{5}', 958, Bb.ty, { size: 14, color: C.muted, align: 'right', alpha: lab(.5) });
}

function draw() { panelA(); panelB(); }
for (const p of [first, rest]) p.catch(() => {});
if (STILL) Promise.all([first, rest]).then(boot, boot);
else boot();
"""


def main():
    A = a_model()
    Bm = b_model()

    # ---- layout, drawing units
    ppm = 230.0                                     # (a) plate: units per metre along it
    px0, py, ph = 64.0, 118.0, 26.0
    ins_x0, ins_y0, ins_s = 64.0, 232.0, 4.0        # the inset: its corner and units per mm
    I = inset(A, ins_x0, ins_y0, ins_s)
    I.update(x0=ins_x0, y0=ins_y0)
    b_s = 7.6                                       # (b) block: units per mm
    bx, by = 110.0, 486.0
    ty_b = 400.0

    # ---- (b)'s field
    chunks, fsizes = field_chunks(Bm["field"])
    keep = Bm["ts"] <= 10.0
    ox, oz = B.flaw_outline(97)
    lam_b = B.CL / B.F0                             # mm

    # ---- the clock
    dur_a = (TEND_A - M0) * SLOW_A
    dur_b = 10.0 * SLOW_B / 1e6
    loop = dur_a + GAP + dur_b + HOLD
    poster = round(TA0 + dur_a + GAP + dur_b + 0.9, 2)

    exag = ph / (G.D_PLATE * ppm)
    data = {
        "loop": loop, "ta0": TA0, "gap": GAP, "fade": FADE, "poster": poster, "clip": 0.5,
        "a": {"slow": SLOW_A, "m0": M0, "tend": TEND_A, "snap": SNAP_A, "tc": A["tc"], "cg": A["cg"],
              "D": G.D_DEF, "R": G.R_DEF, "T": G.T_DEF, "xend": X_A, "nx": int(round(X_A / DXA)) + 1, "dx": DXA,
              "ppm": ppm, "px0": px0, "py": py, "ph": ph,
              "c": {k: common.f32(A["comp"][k]) for k in ("w", "k", "a", "p")},
              "trace": common.f32(A["trace"]), "tmax": T_TRACE * 1e6,
              "win": [v * 1e6 for v in A["win"]], "echo": A["echo_t"] * 1e6,
              "plot": {"x": 598, "y": 84, "w": 360, "h": 170},
              "inset": I, "insetlab": r"A_{0}\rm{ at 50 kHz, true scale}", "echolab": 1010.0,
              "ny": 324.0,
              "note1": r"\lambda\ \sim\ h\ " + "⇒" + r"\ \rm{dispersive guided modes (wave occupies the full cross section)}",
              "note2": ["acoustic emission: the same guided modes, launched passively by the damage",
                        "event itself (e.g. crack growth) instead of by a transducer"],
              "params": [f"steel plate, h = 10 mm, drawn {exag:.0f} × thicker; E = 210 GPa, ν = 0.29",
                         "A₀ mode: a 3 cycle Hann burst at 50 kHz",
                         "defect 1.5 m away, reflection 0.5"]},
        "b": {"slow": SLOW_B, "tend": 10.0, "snap": TSNAP_B, "t0": B.T0, "cl": B.CL, "s": b_s, "bx": bx, "by": by,
              "wb": B.WB, "db": B.DB, "ty": ty_b, "rx": 35.0,
              "probe": [B.PROBE["x"] - B.PROBE["w"] / 2, B.PROBE["x"] + B.PROBE["w"] / 2],
              "flaw": {"x": ox, "z": oz, "top": [Bm["x_top"], Bm["d_f"]], "lab": [B.FLAW["x"] - B.FLAW["a"] - 1.0, B.FLAW["z"] + 0.6]},
              "lam": {"x": 23.0, "mm": lam_b},
              "ascan": {"t0": float(Bm["ts"][0]), "dt": float(Bm["ts"][1] - Bm["ts"][0]), "n": int(keep.sum()),
                        "v": common.f32(Bm["ascan"][keep] / Bm["norm"])},
              "echo": {"tf": Bm["tf"], "tb": Bm["tb"], "af": Bm["af"] / Bm["norm"], "ab": Bm["ab"] / Bm["norm"],
                       "tf_th": Bm["tf_th"], "tb_th": Bm["tb_th"], "wf": Bm["wf"], "wb": Bm["wb"]},
              "field": {"n": int(Bm["field"].shape[0]), "w": int(Bm["field"].shape[1]), "h": int(Bm["field"].shape[2]),
                        "chunks": chunks, "span": 126, "dt": B.FRAME_EVERY * B.DT, "clip": B.FCLIP},
              "plot": {"x": 598, "y": 486, "w": 360, "h": 190},
              "ny": 742.0,
              "note": r"\lambda\ \ll\ h\ " + "⇒" + r"\ \rm{bulk wave behavior (no dispersive guided modes)}",
              "params": (r"\rm{steel }50 \times\ 25\ \rm{mm},\ c_{\rm{L}} = 5900\ \rm{m/s};\ \rm{probe 10 mm, 5 MHz, 3 cycle Hann burst};\ "
                         r"\lambda\ = " + f"{lam_b:.2f}" + r"\ \rm{mm}")},
    }
    txt = report(A, Bm, I, dict(loop=loop, dur_a=dur_a, dur_b=dur_b, poster=poster, exag=exag, fsizes=fsizes))
    with open(os.path.join(HERE, "sd_waves.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    title = "Figure 5: Guided wave testing and bulk wave, pulse echo ultrasonic testing"
    aria = ("Two ultrasonic tests on steel, computed from wave models. (a) A guided wave burst travels along a "
            "10 mm plate to a defect 1.5 m away and back; the received echo arrives spread out by dispersion, "
            "and the mode at true scale shows a wavelength of the order of the thickness. (b) A 5 MHz pulse "
            "enters a 25 mm block, and the echoes from a flaw and from the back wall arrive compact, at times "
            "that read as depths.")
    common.build_html(NAME, title, aria, 1000, 780, data, poster_js(JS, poster))
    # the page's own Fourier sum (fieldAt, every frame) against guided_ut's numpy field
    xg = np.arange(int(round(X_A / DXA)) + 1) * DXA
    moments = (366e-6, SNAP_A, 1100e-6)
    worst = G.check_page(NAME, [(f"fieldAt({tm!r})", G.field(A["comp"], xg, tm)) for tm in moments])
    print("still:", common.still(NAME))
    sd_check.append(os.path.join(HERE, "sd_waves.check.txt"), [
        "", "THE PAGE'S OWN SUM",
        f"  (a)'s field, the page's fieldAt() (float32 lines, every frame) against guided_ut.field() (numpy) at t = "
        + ", ".join(f"{tm*1e6:.0f}" for tm in moments) + " us:",
        f"  largest difference {worst:.1e} (the burst's amplitude is 1)"])
    sd_check.append(os.path.join(HERE, "sd_waves.check.txt"),
                    sd_check.record(NAME, 2 * loop + TA0, 0.1, "--dense" in sys.argv))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.4, 2.5, 4.0, 5.5, 8.5, 10.0, 12.0, 14.0, 16.0]))


def report(A, Bm, I, X):
    L = []
    say = L.append
    say("Figure 5 (nf-sd-waves): (a) guided wave testing, (b) bulk wave, pulse echo ultrasonic testing")
    say("generator: tools/numfig/sd_waves.py; models imported: guided_ut.py (Figure 12 of the waves guide),")
    say("bulk_ut.py (Figure 11); their own checks are in guided_ut.check.txt and bulk_ut.check.txt")
    say("")
    say("(a) GUIDED WAVES")
    say(f"  steel plate d = h = {G.D_PLATE*1e3:g} mm, E = {G.E/1e9:g} GPa, nu = {G.NU}, rho = {G.RHO:g} kg/m3;"
        f" c_L = {G.C_L:.1f}, c_T = {G.C_T:.1f} m/s")
    say(f"  A0 at {G.F0/1e3:g} kHz (Rayleigh-Lamb, exact roots): c_p = {A['cp']:.1f} m/s, c_g = {A['cg']:.1f} m/s,")
    say(f"  wavelength c_p / f = {A['cp']/G.F0*1e3:.2f} mm: {A['cp']/G.F0/G.D_PLATE:.1f} times the thickness"
        " (his lambda ~ h)")
    say(f"  burst: {G.NCYC} cycle Hann window at {G.F0/1e3:g} kHz, {len(A['comp']['w'])} spectral lines, each with its own k on A0")
    say(f"  defect at {G.D_DEF:g} m, reflection {G.R_DEF:g}, transmission {G.T_DEF:.3f}")
    say(f"  CHECK 1: the echo's envelope peak {A['echo_t']*1e6:.1f} us against the burst centre + 2D/c_g ="
        f" {A['pred']*1e6:.1f} us ({(A['echo_t']-A['pred'])*1e6:+.1f} us: the upper half of the band travels faster")
    say("    and spreads less, guided_ut.check.txt)")
    say(f"  CHECK 2, the dispersion: the echo's -6 dB width {A['w6']*1e6:.0f} us against the burst's {A['w6b']*1e6:.0f} us"
        f" ({A['w6']/A['w6b']:.1f} times): his \"spread out by dispersion\"")
    say(f"  the inset: the A0 mode shape at {G.F0/1e3:g} kHz (guided_ut.mode_shape, |det| scaled {A['det']:.1e}),")
    say(f"    Re{{u(z) e^(ikx)}} over {2:g} wavelengths, true scale ({4:g} units/mm); the largest displacement"
        f" drawn {I['gain']:.1f} units")
    uz = np.abs(A["uz"])
    ux = np.abs(A["ux"])
    say(f"    u_z varies {(uz.min()/uz.max()-1)*100:+.1f} % through the thickness; |u_x| at the faces"
        f" {ux.max()/uz.max():.3f} of |u_z|: the whole section moves (his \"wave occupies the full cross section\")")
    say(f"  the plate: {X_A:g} m drawn at 230 units/m, its thickness drawn {X['exag']:.0f} times enlarged (said on the page);")
    say(f"    the field is guided_ut's Fourier sum, evaluated by the page every frame on {int(round(X_A/DXA))+1} points")
    say(f"  the arrows under the plate ride the packets' centres at c_g; time slowed {SLOW_A:g} times")
    say("")
    say("(b) BULK WAVES")
    say(f"  bulk_ut's EFIT model: steel block {B.WB:g} x {B.DB:g} mm, c_L = {B.CL*1e3:.0f} m/s, c_T = {B.CT*1e3:.0f} m/s;")
    say(f"  probe {B.PROBE['w']:g} mm at x = {B.PROBE['x']:g} mm, {B.F0:g} MHz, {B.NC} cycles; flaw: elliptical void at"
        f" ({B.FLAW['x']:g}, {B.FLAW['z']:g}) mm")
    say(f"  wavelength c_L / f = {B.CL/B.F0:.3f} mm: 1/{B.DB/(B.CL/B.F0):.0f} of the thickness (his lambda << h)")
    say(f"  CHECK 3: back wall echo {Bm['tb']:.3f} us against 2d/c_L = {Bm['tb_th']:.3f} us ({(Bm['tb']/Bm['tb_th']-1)*100:+.2f} %)")
    say(f"  CHECK 4: flaw echo {Bm['tf']:.3f} us against 2 z_f/c_L = {Bm['tf_th']:.3f} us, z_f = {Bm['d_f']:.2f} mm the top"
        f" of the void under the probe ({(Bm['tf']/Bm['tf_th']-1)*100:+.2f} %)")
    say(f"  the echoes stay compact: flaw echo {Bm['af']/Bm['a_ip']:.3f}, back wall {Bm['ab']/Bm['a_ip']:.3f} of the"
        " initial pulse, no spreading (the grid convergence and the plane wave check: bulk_ut.check.txt)")
    say(f"  the field: p = -(s_xx + s_zz)/2 over p0, every {B.FRAME_EVERY*B.DT:.3f} us, {B.BOX * B.DX:.1f} mm pixels, colour range +-{B.FCLIP:g}")
    say("    (the page's own copy: nf-sd-waves-field-0..3.png, " + ", ".join(f"{s/1e3:.0f}" for s in X["fsizes"]) + " kB)")
    say(f"  the words ride the fronts at c_L (as bulk_ut's page); time slowed {SLOW_B:g} times")
    say("")
    say("TIME")
    say(f"  (a)'s cycle {X['dur_a']:.2f} s, a {GAP:g} s gap, (b)'s cycle {X['dur_b']:.2f} s, a {HOLD:g} s hold: the loop is"
        f" {X['loop']:.2f} s; each panel rests at its idle moment (the still's) while the other runs")
    say(f"  (a) idle at t = {SNAP_A*1e6:.0f} us of its clock (the echo {(2*G.D_DEF - A['cg']*(SNAP_A-A['tc'])):.2f} m from the"
        f" transducer), (b) at {TSNAP_B:g} us")
    say(f"  poster (printed frame) at t = {X['poster']} s: both idle, both signals whole")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
