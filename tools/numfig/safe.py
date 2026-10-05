"""Figure 5: two ways to the equation of motion of a wave in a beam.

(a) The analytical approach: an infinitely long Euler-Bernoulli beam (the
    20 x 20 mm square steel bar of Figure 4) carries the exact flexural wave
    w = A cos(kx - wt), w = k^2 sqrt(EI / rho A). An element
    dx is picked out and enlarged: its shape is the beam's own drawn shape with
    the rigid motion taken out, and the shear forces V = -EI w''' and bending
    moments M = EI w'' on its two faces are drawn to scale, at that place and
    time. Then EI w'''' + rho A w_tt = 0.
(b) The SAFE method: the same bar's cross-section, meshed as in Figure 4
    (16 x 16 Q9 elements of 1.25 mm, safe_model.py), extruded along x in an
    oblique projection. Every point moves as Re{U(y, z) exp(i(kx - wt))}, U the
    computed eigenvector of the fundamental vertical bending mode at the chosen k.

Each panel runs on one fixed clock: a round slow-motion factor, written under
the panel, and the displayed period is the wave's own period times it.

Run: python tools/numfig/safe.py   (writes content/anim/nf-safe.html and .webp,
and tools/numfig/safe.check.txt)
"""
import os
import sys

import numpy as np

import common
import safe_model as sm

NAME = "safe"
HERE = os.path.dirname(os.path.abspath(__file__))
MESH = (16, 16)      # Figure 4's bar: dispersion.NE_BAR elements along each side, 1.25 mm

# (a) the analytical wave
LAM_A = 1.0          # m
A_PHYS = 1e-3        # m, amplitude (drawn exaggerated)
L_A = 2.0            # m of beam drawn
X0_A, DX_A = 1.55, 0.10  # the element picked out, m
TD_A = 3.0           # s, the displayed period aimed at; the slow-motion factor is rounded

# (b) the SAFE wave
LAM_B = 0.050        # m
L_B = 3 * LAM_B      # m of bar drawn
TD_B = 2.5           # s, the displayed period aimed at (as TD_A)
POSTER = 3.0         # s, the printed moment (the intro is over by 1.4 s)


def sig2(v):
    """v rounded to two significant figures."""
    e = int(np.floor(np.log10(v)))
    return round(v / 10 ** e, 1) * 10 ** e


def slow_tex(r):
    """The slow-motion label, as Figure 4 writes it."""
    e = int(np.floor(np.log10(r)))
    return f"\\rm{{shown}}\\ {r / 10 ** e:.1f}\\ \\times\\ 10^{{{e}}}\\ \\rm{{times slower than real time}}"


def compute():
    sec = sm.section_constants()
    EI, rhoA = sm.E * sec["Iy"], sm.RHO * sec["A"]
    ka = 2 * np.pi / LAM_A
    wa = ka ** 2 * np.sqrt(EI / rhoA)
    model = sm.Safe(*MESH)
    # (a) cross-check: the SAFE bending branch at the same wavenumber
    w_safe_a = model.omegas("vertical", ka, 1)[0]
    bs_a = sm.beam_speeds(ka)
    # (b) the SAFE mode
    kb = 2 * np.pi / LAM_B
    wb, V = model.solve("vertical", kb, 3)
    v = V[:, 0]
    ux, uy, uz = model.split(v)
    s = np.sqrt(ux ** 2 + uy ** 2 + uz ** 2).max()
    v = v / s if uz.sum() > 0 else -v / s
    # residual of the eigenpair in the full (unreduced) matrices
    Kk = model.K1 + kb * model.K2 + kb * kb * model.K3
    res = np.linalg.norm(Kk @ v - wb[0] ** 2 * (model.M @ v)) / np.linalg.norm(Kk @ v)
    bs_b = sm.beam_speeds(kb)
    # the mesh: the same waves on meshes of twice and of half the element size
    conv = {}
    for n in (8, 32):
        m = sm.Safe(n, n)
        conv[n] = (m.omegas("vertical", kb, 3), m.omegas("vertical", ka, 1)[0], m.ndof)
    # the square's bending pair: the lateral class at the same k
    w_lat = model.omegas("lateral", kb, 1)[0]
    return dict(EI=EI, rhoA=rhoA, ka=ka, wa=wa, w_safe_a=w_safe_a, bs_a=bs_a,
                kb=kb, wb=wb, v=v, res=res, bs_b=bs_b, ndof=model.ndof,
                loop=model.boundary(), conv=conv, w_lat=w_lat, sec=sec)


def same_mesh_as_figure_4():
    """Figure 4's bar (dispersion.py) node for node: nodes and elements equal."""
    import dispersion
    nodes, elems = dispersion.bar_mesh()
    model = sm.Safe(*MESH)
    return bool(dispersion.NE_BAR == MESH[0] == MESH[1]
                and np.allclose(np.asarray(nodes) / 1e3, model.nodes, atol=1e-12)
                and np.array_equal(np.asarray(elems), model.elems))


def check(R, slow_a, slow_b):
    L = []
    p = L.append
    fa, fb = R["wa"] / 2 / np.pi, R["wb"][0] / 2 / np.pi
    hb = sm.B / MESH[0] * 1e3
    p("Figure 5 (nf-safe): the analytical beam element and the SAFE model of the same bar")
    p("")
    p("(a) ANALYTICAL: Euler-Bernoulli beam, infinitely long (no boundary conditions)")
    p(f"  Figure 4's square steel bar, {sm.B*1e3:.0f} x {sm.H*1e3:.0f} mm (E = {sm.E/1e9:.0f} GPa, nu = {sm.NU},"
      f" rho = {sm.RHO:.0f} kg/m^3): EI = {R['EI']:.2f} N m^2, rho A = {R['rhoA']:.3f} kg/m")
    p(f"  exact wave w = A cos(kx - wt): lambda = {LAM_A} m, k = {R['ka']:.4f} rad/m,")
    p(f"  w = k^2 sqrt(EI/(rho A)) = {R['wa']:.2f} rad/s, f = {fa:.2f} Hz, c_p = w/k = {R['wa']/R['ka']:.2f} m/s")
    p(f"  element: x = {X0_A:g} to {X0_A+DX_A:g} m (k dx = {R['ka']*DX_A:.4f} rad); faces carry")
    p("  M = EI w'' = -EI k^2 A cos(kx - wt) and V = -EI w''' = -EI k^3 A sin(kx - wt),")
    p("  drawn to scale (M / EI k^2 A, V / EI k^3 A). Sign convention: positive M clockwise on")
    p("  the left face and counter-clockwise on the right; positive V down on the left face, up on")
    p("  the right, so that V = -dM/dx and dV/dx = rho A w_tt give EI w'''' + rho A w_tt = 0.")
    # equilibrium of the finite element drawn, integrated exactly
    ka, A = R["ka"], A_PHYS
    th = np.linspace(0, 2 * np.pi, 13)[:-1]
    worst = 0
    for t0 in th:
        x0, x1 = X0_A, X0_A + DX_A
        VL, VR = (-R["EI"] * ka ** 3 * A * np.sin(ka * x - t0) for x in (x0, x1))
        # inertia: integral of rho A w_tt over the element, w_tt = -w^2 A cos(kx - t0)
        inert = -R["rhoA"] * R["wa"] ** 2 * A * (np.sin(ka * x1 - t0) - np.sin(ka * x0 - t0)) / ka
        worst = max(worst, abs((VR - VL) - inert) / (R["EI"] * ka ** 3 * A))
    p("  check of the drawn element over a period: max |V(x+dx) - V(x) - int rho A w_tt dx| /")
    p(f"  (EI k^3 A) = {worst:.1e} (dynamic equilibrium holds exactly)")
    p("  N = EA u' = 0: a flexural wave carries no axial force, so N and N + dN are not drawn.")
    tim = R["bs_a"]["vertical_Timo"] * R["ka"]
    p(f"  SAFE at the same k: f = {R['w_safe_a']/2/np.pi:.3f} Hz, {R['w_safe_a']/R['wa']-1:+.2%} from Euler-Bernoulli;")
    p(f"  Timoshenko (Cowper's shear coefficient) gives {tim/2/np.pi:.3f} Hz ({R['w_safe_a']/tim-1:+.1e} from SAFE):")
    p(f"  at kh = {R['ka']*sm.H:.3f} the shear and rotary inertia that Euler-Bernoulli neglects cost"
      f" {1 - R['w_safe_a']/R['wa']:.2%}.")
    p(f"  clock: slowed {slow_a:,.0f} times (a round factor), so the displayed period is {slow_a / fa:.3f} s")
    p("")
    p("(b) SAFE: Figure 4's bar and its mesh (dispersion.check.txt: the bar's curves and their convergence)")
    p(f"  the same mesh as Figure 4's bar, node for node (dispersion.bar_mesh): {same_mesh_as_figure_4()}")
    p(f"  {MESH[0]} x {MESH[1]} Q9 elements of {hb:.2f} mm, {R['ndof']} dof; fundamental vertical bending mode at")
    p(f"  lambda = {LAM_B*1e3:.0f} mm, k = {R['kb']:.3f} rad/m: f = {fb/1e3:.3f} kHz, "
      f"c_p = {R['wb'][0]/R['kb']:.1f} m/s")
    p(f"  (next branches of the class at this k: {', '.join(f'{w/2/np.pi/1e3:.2f}' for w in R['wb'][1:])} kHz;"
      f" the lateral partner of the square's bending pair: {R['w_lat']/2/np.pi/1e3:.3f} kHz)")
    p(f"  eigenpair residual |(K(k) - w^2 M) V| / |K(k) V| = {R['res']:.1e} (full matrices)")
    p(f"  elements a wavelength: lambda / h = {LAM_B*1e3/hb:.0f} (the field is exact along x; across the section")
    p(f"  the shortest scale of this mode is the section itself, {sm.B*1e3:.0f} mm = {MESH[0]} elements)")
    c8, c32 = R["conv"][8], R["conv"][32]
    p("  MESH CONVERGENCE (the same waves on 8 x 8 and 32 x 32 meshes, elements of 2.5 and 0.625 mm):")
    for i in range(3):
        p(f"    branch {i + 1} at k = {R['kb']:.3f}: 8 x 8 {c8[0][i]/2/np.pi/1e3:.4f} kHz, 16 x 16 {R['wb'][i]/2/np.pi/1e3:.4f},"
          f" 32 x 32 {c32[0][i]/2/np.pi/1e3:.4f} ({R['wb'][i]/c32[0][i]-1:+.2e} against 32 x 32)")
    p(f"    (a)'s wave at k = {R['ka']:.4f}: 16 x 16 {R['w_safe_a']/2/np.pi:.4f} Hz, 32 x 32 {c32[1]/2/np.pi:.4f} Hz"
      f" ({R['w_safe_a']/c32[1]-1:+.1e})")
    tb = R["bs_b"]["vertical_Timo"]
    eb = R["bs_b"]["vertical_EB"]
    c = R["wb"][0] / R["kb"]
    p(f"  beam theories at this k (kh = {R['kb']*sm.H:.2f}): Euler-Bernoulli c_p = {eb:.1f} m/s ({c/eb-1:+.1%}), "
      f"Timoshenko {tb:.1f} m/s ({c/tb-1:+.2%})")
    p("  the published square rod: Figure 4's check compares this bar's bending branch with Hayashi,")
    p("  Kawashima and Rose (2004), Fig. 2 (dispersion.check.txt, THE BAR)")
    p("  u(x, y, z, t) = Re{U(y, z) exp(i(kx - wt))}, U_x = i V_x: the axial part is a quarter")
    p("  period out of phase with the transverse part, which tilts the sections as the wave passes.")
    p(f"  bar drawn over {L_B*1e3:.0f} mm = {L_B/LAM_B:.0f} wavelengths; clock: slowed {slow_b:,.0f} times (a round factor),")
    p(f"  so the displayed period is {slow_b / fb:.3f} s")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA;
const POSTER_T = D.poster;

/* ---------------------------------------------------------------- clock
   Intro (README, round 2): the beam draws by .45 s and starts to wave at .3 s;
   the element is picked out at .45 s and enlarged by .95 s; the bar's section
   draws by .5 s, its edges by .7 s, and the wave runs from .45 s; slices follow
   40 ms apart; labels arrive with settle(t0, .28). */
const lab = t0 => settle(t0, .28);         // a label arriving
const rise = s => 4 * (1 - s);             // ... settling 4 units into place

/* ================================================================ (a) */
const A = D.a;
const BX0 = 50, BX1 = 530, BY = 124;
const PXM = (BX1 - BX0) / A.L;             // drawing units per metre along the beam
const GAIN = 22 / A.A;                     // drawing units per metre of deflection (exaggerated)
const HD = A.h * PXM;                      // the beam's depth, true to its length scale
const EL = {x: 662, y: 134, len: 220};     // the enlarged element
const MAG = EL.len / (A.dx * PXM);         // its magnification
const T_A0 = .30, T_PA = D.tpa;            // the wave arrives; its phase origin

/* offsets of a centre line by +-d along its normal */
function offsets(c, d) {
  const up = [], dn = [];
  for (let i = 0; i < c.length; i++) {
    const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)];
    let tx = b[0] - a[0], ty = b[1] - a[1]; const n = Math.hypot(tx, ty); tx /= n; ty /= n;
    up.push([c[i][0] + ty * d, c[i][1] - tx * d]); dn.push([c[i][0] - ty * d, c[i][1] + tx * d]);
  }
  return [up, dn];
}
function more(x, y, dir, alpha) {          // the beam goes on: three dots
  for (let k = 0; k < 3; k++) dot(x + dir * (9 + 7 * k), y, 1.9, {color: C.blue, width: 0, alpha});
}
function momentArc(cx, cy, out, r, m, color) {  // a curved moment arrow, its sweep ~ |m|
  const sw = 2.5 * Math.abs(m);
  if (sw < 0.06) return;
  const left = Math.cos(out) < 0, cw = left ? m > 0 : m < 0;       // + : clockwise on the left face
  const a0 = cw ? out - sw / 2 : out + sw / 2, a1 = cw ? out + sw / 2 : out - sw / 2;
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1 + (cw ? -0.1 : 0.1), !cw); ctx.stroke(); ctx.restore();
  const ex = cx + r * Math.cos(a1), ey = cy + r * Math.sin(a1);
  const tx = cw ? -Math.sin(a1) : Math.sin(a1), ty = cw ? Math.cos(a1) : -Math.cos(a1);
  arrow(ex - tx * 3, ey - ty * 3, ex, ey, {color, width: 2, head: 10});
}

/* the engine's dim(), its knockout opaque from the first frame: the line never
   shows through the label while both fade in */
function dimk(x1, x2, y, label, o) {
  const {alpha = 1, size = 17} = o;
  dim(x1, x2, y, '', {alpha});
  if (alpha <= 0) return;
  const w = math(label, 0, -1e4, {size, alpha: 0});
  ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect((x1 + x2) / 2 - w / 2 - 4, y - size * .62, w + 8, size * 1.42); ctx.restore();
  math(label, (x1 + x2) / 2, y + size * .34, {size, align: 'center', alpha});
}
function drawA() {
  panel('a', 18, 34, {alpha: lab(0)});
  const s0 = lab(.03);
  text('analytical approach', 52, 34 + rise(s0), {size: 17, color: C.body, alpha: s0});
  const amp = settle(T_A0, .5), ph = 2 * Math.PI * (t - T_PA) / A.Td;
  const w = x => A.A * amp * Math.cos(A.k * x - ph);          // m, the exact wave
  const X = x => BX0 + x * PXM, Yw = x => BY - GAIN * w(x);
  line([[BX0 - 16, BY], [BX1 + 16, BY]], {color: C.guide, width: 1, dash: [5, 4], progress: seg(0, .30)});
  // the beam, a piece of an infinitely long one
  const n = 240, cl = Array.from({length: n + 1}, (_, i) => { const x = A.L * i / n; return [X(x), Yw(x)]; });
  const [up, dn] = offsets(cl, HD / 2);
  const bd = seg(.05, .40);
  if (bd >= 1) line(up.concat(dn.slice().reverse()), {color: C.steel, width: .1, fill: C.steel, close: true});
  line(up, {color: C.blue, width: 1.6, progress: bd});
  line(dn, {color: C.blue, width: 1.6, progress: bd});
  const ma = lab(.35);
  more(cl[0][0], cl[0][1], -1, ma); more(cl[n][0], cl[n][1], 1, ma);
  const ga = lab(.20), gy = 206;
  arrow(BX0, gy, BX0 + 40, gy, {width: 1.1, head: 7, alpha: ga});
  arrow(BX0, gy, BX0, gy - 32, {width: 1.1, head: 7, alpha: ga});
  math('x', BX0 + 45, gy + 5, {size: 16, alpha: ga});
  math('w', BX0 - 5, gy - 38, {size: 16, alpha: ga});
  // the element picked out
  const i0 = Math.round(A.x0 / A.L * n), i1 = Math.round((A.x0 + A.dx) / A.L * n);
  const ea = settle(.45, .28);
  if (ea > 0) {
    line(up.slice(i0, i1 + 1).concat(dn.slice(i0, i1 + 1).reverse()),
         {color: C.accent, width: 1.6, fill: C.wash, close: true, alpha: ea});
    // named under the beam's lowest reach: the wave never carries the name onto the axis line
    math('\\rm{d}x', X(A.x0 + A.dx / 2), BY + GAIN * A.A + HD / 2 + 21, {size: 16, align: 'center', alpha: ea});
  }
  // enlarged: the drawn shape less its rigid motion (the chord, in linear theory), times MAG
  const m = 40, wl = w(A.x0), wr = w(A.x0 + A.dx);
  const ec = Array.from({length: m + 1}, (_, i) => {
    const s = i / m, dw = w(A.x0 + A.dx * s) - (wl + (wr - wl) * s);
    return [EL.x + EL.len * s, EL.y - MAG * GAIN * dw];
  });
  const [eu, ed] = offsets(ec, HD / 2 * MAG);
  const eg = seg(.55, .40);
  if (ea > 0) {
    const c1 = seg(.50, .30);
    line([up[i0], eu[0]], {color: C.accent, width: 1, dash: [4, 3], progress: c1, alpha: .75});
    line([dn[i0], ed[0]], {color: C.accent, width: 1, dash: [4, 3], progress: c1, alpha: .75});
  }
  if (eg > 0) {
    const poly = eu.concat(ed.slice().reverse());
    if (eg >= 1) line(poly, {color: C.accent, width: 1.8, fill: C.wash, close: true});
    else line(poly.concat([poly[0]]), {color: C.accent, width: 1.8, progress: eg});
    line(ec, {color: C.accent, width: 1, dash: [6, 4], alpha: .55 * seg(.90, .25)});
  }
  // the stress resultants on the two faces, to scale, at this place and time
  const fa = settle(.80, .30), la = lab(.90);
  if (fa > 0) {
    for (const [i, x, side] of [[0, A.x0, -1], [m, A.x0 + A.dx, 1]]) {
      const th = A.k * x - ph;
      const Mn = -Math.cos(th) * amp * fa, Vn = -Math.sin(th) * amp * fa;   // M/(EI k^2 A), V/(EI k^3 A)
      const a = ec[Math.max(0, i - 1)], b = ec[Math.min(m, i + 1)];
      let tx = b[0] - a[0], ty = b[1] - a[1]; const tn = Math.hypot(tx, ty); tx /= tn; ty /= tn;
      const nx = ty, ny = -tx, c = ec[i];                              // n: up, across the axis
      const Lv = 62 * Vn * side, ox = c[0] + side * tx * 11, oy = c[1] + side * ty * 11;
      if (Math.abs(Lv) > 2.5) arrow(ox - nx * Lv / 2, oy - ny * Lv / 2, ox + nx * Lv / 2, oy + ny * Lv / 2,
                                    {color: C.navy, width: 2, head: 10});
      momentArc(c[0], c[1], Math.atan2(side * ty, side * tx), 48, Mn, C.navy);
    }
    const L0 = ec[0], L1 = ec[m], r = rise(la);
    math('V', L0[0] - 14, L0[1] + 76 + r, {size: 17, align: 'right', alpha: la});
    math('M', L0[0] - 44, L0[1] - 54 + r, {size: 17, align: 'right', alpha: la});
    math('V + \\rm{d}V', L1[0] + 14, L1[1] + 76 + r, {size: 17, alpha: la});
    math('M + \\rm{d}M', L1[0] + 44, L1[1] - 54 + r, {size: 17, alpha: la});
  }
  if (eg >= 1) dimk(ec[0][0], ec[m][0], EL.y + 86, '\\rm{d}x', {alpha: lab(.95), size: 16});
  const qa = lab(1.0);
  if (qa > 0) eqn(292, 284 + rise(qa), qa);
  const pa = lab(1.05), pw = text(D.pa, 18, 348, {size: 14, color: C.muted, alpha: pa});
  math(D.slowa, 18 + pw + 6, 348, {size: 14, color: C.muted, alpha: pa});
}

/* EI d4w/dx4 + rho A d2w/dt2 = 0, set as TeX sets it */
function frac(num, den, x, y, sz, alpha) {
  const wn = math(num, 0, -1e4, {size: sz, alpha: 0}), wd = math(den, 0, -1e4, {size: sz, alpha: 0});
  const w = Math.max(wn, wd) + 6;
  math(num, x + w / 2, y - 6, {size: sz, align: 'center', alpha});
  math(den, x + w / 2, y + sz + 2, {size: sz, align: 'center', alpha});
  line([[x, y], [x + w, y]], {width: 1.1, alpha});
  return w;
}
function eqn(x, y, alpha) {
  const sz = 22, pieces = [['m', 'EI'], ['f', '∂^{4}w', '∂x^{4}'], ['m', '+ ρA'], ['f', '∂^{2}w', '∂t^{2}'], ['m', '= 0']];
  const width = p => p[0] === 'm' ? math(p[1], 0, -1e4, {size: sz, alpha: 0})
    : Math.max(math(p[1], 0, -1e4, {size: sz, alpha: 0}), math(p[2], 0, -1e4, {size: sz, alpha: 0})) + 6;
  const gap = 7, total = pieces.reduce((s, p) => s + width(p) + gap, -gap);
  let cx = x - total / 2;
  for (const p of pieces) {
    cx += (p[0] === 'm' ? math(p[1], cx, y + 7, {size: sz, alpha}) : frac(p[1], p[2], cx, y, sz, alpha)) + gap;
  }
}

/* ================================================================ (b) */
const B = D.b;
const NYN = 2 * B.ny + 1, NZN = 2 * B.nz + 1, NN = NYN * NZN;
const U = (() => { const q = b64i8(B.U), v = new Float32Array(q.length); for (let i = 0; i < q.length; i++) v[i] = q[i] / 127; return v; })();
const S = B.s, FX = B.fx, CA = Math.cos(B.al), SA = Math.sin(B.al);
const O = {x: 150, y: 680};                // the section's centre at x = 0
const proj = (x, y, z) => [O.x + y * S + x * S * FX * CA, O.y - z * S - x * S * FX * SA];
const T_B0 = .45, T_PB = D.tpb, NX = 150;  // the wave arrives; its phase origin
const YS = Array.from({length: NYN}, (_, i) => -B.bw / 2 + B.bw * i / (NYN - 1));
const ZS = Array.from({length: NZN}, (_, j) => -B.bh / 2 + B.bh * j / (NZN - 1));
const TL = (NZN - 1) * NYN, TR = NZN * NYN - 1, BR = NYN - 1;               // corner nodes
const TOP = Array.from({length: NYN}, (_, i) => TL + i);                     // left to right
const RIGHT = Array.from({length: NZN}, (_, j) => j * NYN + NYN - 1);        // bottom to top

function drawB() {
  panel('b', 18, 398, {alpha: lab(.05)});
  const s0 = lab(.08);
  text('SAFE method', 52, 398 + rise(s0), {size: 17, color: C.body, alpha: s0});
  const amp = B.amp * settle(T_B0, .5), ph = 2 * Math.PI * (t - T_PB) / B.Td;
  // node n at axial position x (mm), displaced by Re{U e^{i(kx - wt)}}, U_x = i V_x
  const P = (n, x) => {
    const th = 2 * Math.PI * x / B.lam - ph, c = Math.cos(th), s = Math.sin(th);
    const j = Math.floor(n / NYN), i = n - j * NYN;
    return proj(x - amp * U[3 * n] * s, YS[i] + amp * U[3 * n + 1] * c, ZS[j] + amp * U[3 * n + 2] * c);
  };
  const xs = Array.from({length: NX + 1}, (_, q) => B.L * q / NX);
  const pr = seg(.30, .40), fa = seg(.50, .25);
  const cTL = xs.map(x => P(TL, x)), cTR = xs.map(x => P(TR, x)), cBR = xs.map(x => P(BR, x));
  if (fa > 0) {                            // the faces toward the reader
    const fill = (pts, col, al) => { ctx.save(); ctx.globalAlpha *= fa * al; ctx.fillStyle = col; ctx.beginPath();
      pts.forEach((q, i) => i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])); ctx.closePath(); ctx.fill(); ctx.restore(); };
    const fR0 = RIGHT.map(n => P(n, 0)), fRL = RIGHT.map(n => P(n, B.L));
    const fT0 = TOP.map(n => P(n, 0)), fTL = TOP.map(n => P(n, B.L));
    fill(fR0.concat(cTR, fRL.slice().reverse(), cBR.slice().reverse()), C.steel2, .8);
    fill(fT0.concat(cTR, fTL.slice().reverse(), cTL.slice().reverse()), C.steel, .75);
    // cross-sections along the bar, a quarter wavelength apart
    const nq = Math.round(4 * B.L / B.lam);
    for (let q = 1; q <= nq; q++) {
      const x = B.L * q / nq, sa = seg(.55 + .04 * q, .30);
      if (sa > 0) line(TOP.map(n => P(n, x)).concat(RIGHT.slice().reverse().map(n => P(n, x))),
                       {color: q === nq ? C.ink : C.blue, width: q === nq ? 1.3 : .9, alpha: sa});
    }
  }
  const along = c => c.slice(0, Math.max(2, Math.round(pr * NX) + 1));
  if (pr > .02) for (const c of [cTL, cTR, cBR]) line(along(c), {color: C.ink, width: 1.3});
  // the cross-section at x = 0: its finite elements
  const fr = Array.from({length: NN}, (_, n) => P(n, 0)), md0 = seg(.10, .40), md = md0 > .02 ? md0 : 0;
  if (fa > 0) line(B.loop.map(n => fr[n]), {color: C.steel, width: .1, fill: C.steel, close: true, alpha: fa});
  for (let i = 0; i < NYN; i += 2) line(Array.from({length: NZN}, (_, j) => fr[j * NYN + i]), {color: C.ink, width: .6, alpha: .75, progress: md});
  for (let j = 0; j < NZN; j += 2) line(Array.from({length: NYN}, (_, i) => fr[j * NYN + i]), {color: C.ink, width: .6, alpha: .75, progress: md});
  line(B.loop.map(n => fr[n]), {color: C.ink, width: 1.5, close: true, progress: md});
  // axes
  const aa = lab(.70), g = [330, 776], L = 34;
  arrow(g[0], g[1], g[0] + L, g[1], {width: 1.1, head: 7, alpha: aa});
  arrow(g[0], g[1], g[0], g[1] - L, {width: 1.1, head: 7, alpha: aa});
  arrow(g[0], g[1], g[0] + L * CA, g[1] - L * SA, {width: 1.1, head: 7, alpha: aa});
  math('y', g[0] + L + 5, g[1] + 5, {size: 16, alpha: aa});
  math('z', g[0] - 4, g[1] - L - 6, {size: 16, alpha: aa});
  math('x', g[0] + L * CA + 5, g[1] - L * SA - 3, {size: 16, alpha: aa});
  // what is discrete and what is analytical
  const ta = lab(.80), f0 = proj(0, 0, -B.bh / 2), ty = f0[1] + 36 + rise(ta);
  const w1 = text('finite elements over ', 0, -1e4, {size: 16, alpha: 0}), w2 = math('(y, z)', 0, -1e4, {size: 16, alpha: 0});
  text('finite elements over ', f0[0] - (w1 + w2) / 2, ty, {size: 16, color: C.body, alpha: ta});
  math('(y, z)', f0[0] - (w1 + w2) / 2 + w1, ty, {size: 16, alpha: ta});
  const s1 = proj(B.L * .5, -B.bw / 2, B.bh / 2 + 8);
  ctx.save(); ctx.translate(s1[0], s1[1]); ctx.rotate(-B.al);
  const w3 = text('analytical along ', 0, -1e4, {size: 16, alpha: 0}), w4 = math('x', 0, -1e4, {size: 16, alpha: 0});
  text('analytical along ', -(w3 + w4) / 2, rise(ta), {size: 16, color: C.body, alpha: ta});
  math('x', -(w3 + w4) / 2 + w3, rise(ta), {size: 16, alpha: ta});
  ctx.restore();
  // the harmonic term
  const ha = lab(.90);
  math('u(x,y,z,t) = U(y,z)e^{i(kx - ωt)}', 820, 428 + rise(ha), {size: 24, align: 'center', alpha: ha});
  // the mesh, then the wave and the panel's one clock: its slow-motion factor
  const pb = lab(1.0);
  text(D.pb, 18, H - 34, {size: 14, color: C.muted, alpha: pb});
  const pw = text(D.pb2, 18, H - 14, {size: 14, color: C.muted, alpha: pb});
  math(B.slow, 18 + pw + 6, H - 14, {size: 14, color: C.muted, alpha: pb});
}

function draw() { drawA(); drawB(); }
boot();
"""


def main():
    R = compute()
    fa, fb = R["wa"] / 2 / np.pi, R["wb"][0] / 2 / np.pi
    s_px, fx, al = 6.2, 0.66, np.radians(15)
    slow_a, slow_b = sig2(fa * TD_A), sig2(fb * TD_B)
    td_a, td_b = slow_a / fa, slow_b / fb          # s: the displayed periods, one clock a panel
    v = R["v"]
    # the poster: the element's middle at phase 3 pi / 4, where both faces carry
    # a clear shear force and bending moment
    th = (R["ka"] * (X0_A + DX_A / 2) - 0.75 * np.pi) % (2 * np.pi)
    tpa = POSTER - th / (2 * np.pi) * td_a
    hb = sm.B / MESH[0] * 1e3
    data = {
        "poster": POSTER, "tpa": tpa, "tpb": 0.0,
        "a": {"L": L_A, "A": A_PHYS, "k": R["ka"], "x0": X0_A, "dx": DX_A, "Td": td_a,
              "h": sm.H, "EI": R["EI"], "rhoA": R["rhoA"], "w": R["wa"]},
        "b": {"ny": MESH[0], "nz": MESH[1], "bw": sm.B * 1e3, "bh": sm.H * 1e3,
              "U": common.i8(v * 127), "loop": R["loop"].tolist(), "lam": LAM_B * 1e3,
              "L": L_B * 1e3, "s": s_px, "fx": fx, "al": al,
              "amp": 2.2, "Td": td_b, "slow": slow_tex(slow_b)},
        "pb": (f"SAFE: {MESH[0]} × {MESH[1]} quadratic elements of {hb:.3g} mm ({LAM_B*1e3/hb:.0f} per wavelength), "
               f"{R['ndof']} dof, the mesh of Figure 4"),
        "pb2": (f"fundamental bending mode, λ = {LAM_B*1e3:.0f} mm, f = {fb/1e3:.1f} kHz, "
                f"phase velocity {R['wb'][0]/R['kb']:.0f} m/s;"),
    }
    data["pa"] = (f"Euler-Bernoulli: steel {sm.B*1e3:.0f} × {sm.H*1e3:.0f} mm, λ = {LAM_A:g} m, "
                  f"f = {fa:.0f} Hz, phase velocity {R['wa']/R['ka']:.0f} m/s;")
    data["slowa"] = slow_tex(slow_a)
    title = "Figure 5: Two ways of obtaining the governing equation of motion for a wave propagating in a beam"
    aria = ("A bending wave travels along a long steel beam; a small element of it is enlarged with the shear "
            "forces and bending moments on its faces, which change as the wave passes, above the beam's equation "
            "of motion. Below, the same square bar in three dimensions, its cross section meshed with finite "
            "elements as in Figure 4, carries a computed bending wave along its axis.")
    common.build_html(NAME, title, aria, 1000, HEIGHT, data, JS)
    txt = check(R, slow_a, slow_b)
    look = common.still(NAME)                        # also writes content/anim/nf-{NAME}.webp
    txt += overlap_lines()
    with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    print("still:", look)
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.4, 1.0, 1.6, 2.2, 3.0, 4.2, 5.0]))


HEIGHT = 860
OVERLAP_T = [0.4, 1.0, 1.6, 2.2, POSTER, 4.2, 5.0, 7.5]


def overlap_lines():
    """common.overlaps through the intro, at the poster and over a period of each wave."""
    out = common.overlaps(NAME, OVERLAP_T)
    bad = {k: v for k, v in out.items() if v["labels"] or v["crossings"]}
    if bad:
        raise RuntimeError(f"collisions: {bad}")
    size = os.path.getsize(os.path.join(common.ANIM, f"nf-{NAME}.html"))
    webp = os.path.getsize(os.path.join(common.ANIM, f"nf-{NAME}.webp"))
    return ("\nLAYOUT\n"
            f"  common.overlaps at t = {', '.join(f'{t:g}' for t in OVERLAP_T)} s: no label collisions, no crossings\n"
            f"  page {size / 1024:.0f} KB, still {webp / 1024:.0f} KB\n")


if __name__ == "__main__":
    main()
