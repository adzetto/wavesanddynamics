"""Figure 1 of the signal processing document: input, system, output.

His caption: "The input, system, output relationship that runs through signal
processing, system identification, and machine learning alike, alongside its
two most common mathematical forms: convolution, x(t)*h(t)=y(t), for signal
processing, and the linear system Ax=b, for parameter estimation and inverse
problems."

Model. The system is the damped resonator of sp_model (f_n = 1 Hz,
zeta = 0.1), h(t) = exp(-zeta w_n t) sin(w_d t). The input x is given by its
N = 100 samples, dt = 0.08 s apart (three sin^2 pulses), and is linear between
them. Then
  (a) the relationship: x enters, h is the system, y leaves; each plot titled
      with what it is and its symbol;
  (b) y(t) = integral x(tau) h(t - tau) dtau, exactly (sp_model.foh_filter);
      the page draws h(t - tau) and the product x(tau) h(t - tau) itself and
      integrates the product for the number it prints; its two plots titled;
  (c) the same relationship as a linear system, A x = b, stated with its parts
      named (A the system, x the input, b the output). The professor asked
      (29 Sep) for the matrix picture to go ("karisik oluyor", it confuses);
      the check file still shows that sampled, the convolution is A x = b: A
      is the lower triangular Toeplitz matrix of the exact kernel and
      b_i = y(t_i) to machine precision.

Run: python tools/numfig/sp_io.py  (writes the page, the still and the check
file; prints the key numbers).
"""
import os

import numpy as np

import common
import sp_model as M

T = 8.0                    # the record (s)
N = 100                    # samples of x, and the size of A
DT = T / N                 # 0.08 s
SUB = 20                   # fine points per sample interval, for y(t)
PULSES = [(0.9, 1.0, 1.0), (3.3, 1.4, -0.75), (5.3, 0.9, 0.6)]   # centre, length (s), height
H_PAGE = 610

JS = r"""
const D = DATA;
const X = b64f32(D.x), YF = b64f32(D.y);
const N = D.n, DT = D.dt, DTF = D.dtf, TT = D.T, ZW = D.zw, WD = D.wd;
const hAt = s => s < 0 ? 0 : Math.exp(-ZW * s) * Math.sin(WD * s);
function xAt(u) {                         // the input: linear between its samples
  if (u <= 0 || u >= TT) return 0;
  const k = Math.min(N - 1, Math.floor(u / DT)), w = u / DT - k;
  return X[k] * (1 - w) + X[k + 1] * w;
}
function yAt(u) {
  const f = clamp(u, 0, TT) / DTF, k = Math.min(YF.length - 2, Math.floor(f));
  return lerp(YF[k], YF[k + 1], f - k);
}
const lab = t0 => settle(t0, .28);        // a label arriving
const rise = s => 4 * (1 - s);
/* a plot's title: what it is in words, then its symbol in math, one line
   centred on x (or starting at x); returns its width */
function title(words, m, x, y, o = {}) {
  const { size = 17, color = C.ink, alpha = 1, align = 'center' } = o;
  ctx.save(); ctx.font = font({ size }); const w1 = ctx.measureText(words).width; ctx.restore();
  const w = w1 + (m ? math(m, 0, -1e4, { size, alpha: 0 }) : 0), x0 = align === 'center' ? x - w / 2 : x;
  text(words, x0, y, { size, color, alpha });
  if (m) math(m, x0 + w1, y, { size, color, alpha });
  return w;
}

/* ------------------------------------------------------------ clock
   Intro (README, round 2): every stroke drawn by 1.0 s, labels by 1.3 s.
   The cursor starts at .5 s and runs in real time, 8 s of record in 8 s;
   it rests, glides back to 0 and runs again. */
const T0 = .5, SW = TT, HOLD = 1.1, BACK = .9, REST = .3, PER = SW + HOLD + BACK + REST;
function cursor() {
  if (t < T0) return 0;
  const n = Math.floor((t - T0) / PER), u = t - T0 - n * PER;
  if (u < SW) return u;
  if (u < SW + HOLD) return SW;
  return SW * (1 - settle(T0 + n * PER + SW + HOLD, BACK * .8));
}
function curA() {                         // cursor marks: on while it runs, off while it glides back
  if (t < T0) return seg(.35, .15);
  const n = Math.floor((t - T0) / PER), u = t - T0 - n * PER;
  return u < SW + HOLD ? 1 : 1 - seg(T0 + n * PER + SW + HOLD, .25);
}
const POSTER_T = T0 + D.poster;

/* ------------------------------------------------------------ (a) */
const AY = 128;                            // the diagram's axis line
const IN = {x0: 70, x1: 300, s: 40}, OUT = {x0: 700, x1: 930, s: 40 / D.ymax};
const BOX = {x: 392, y: 80, w: 216, h: 96};
function trace(st, f, t0, t1, o) {
  const pts = [], n = 240;
  for (let i = 0; i <= n; i++) { const u = t0 + (t1 - t0) * i / n; pts.push([st.x0 + (st.x1 - st.x0) * u / TT, AY - st.s * f(u)]); }
  line(pts, o);
}
function panelA(tc, ca) {
  panel('a', 20, 34, {alpha: seg(0, .2)});
  text('input, system, output', 54, 34, {size: 17, color: C.body, alpha: seg(.03, .25)});
  // zero lines, the two signals, the system
  line([[IN.x0, AY], [IN.x1, AY]], {color: C.rule, width: 1, progress: seg(0, .3)});
  line([[OUT.x0, AY], [OUT.x1, AY]], {color: C.rule, width: 1, progress: seg(.1, .3)});
  trace(IN, xAt, 0, TT, {color: C.navy, width: 2.2, progress: seg(.04, .4)});
  const bx = BOX;
  line([[bx.x, bx.y], [bx.x + bx.w, bx.y], [bx.x + bx.w, bx.y + bx.h], [bx.x, bx.y + bx.h], [bx.x, bx.y]],
       {color: C.ink, width: 1.8, progress: seg(.08, .4)});
  const hx0 = bx.x + 14, hx1 = bx.x + bx.w - 14, hy = AY, hs = 36, HT = 6;
  line([[hx0, hy], [hx1, hy]], {color: C.rule, width: 1, alpha: seg(.15, .3)});
  const hp = []; for (let i = 0; i <= 240; i++) { const u = HT * i / 240; hp.push([hx0 + (hx1 - hx0) * u / HT, hy - hs * hAt(u)]); }
  line(hp, {color: C.blue, width: 2.2, progress: seg(.15, .4)});
  trace(OUT, yAt, 0, TT, {color: C.navy, width: 2.2, progress: seg(.2, .4)});
  // the flow
  arrow(IN.x1 + 12, AY, bx.x - 8, AY, {width: 1.6, head: 10, alpha: seg(.1, .3)});
  arrow(bx.x + bx.w + 8, AY, OUT.x0 - 12, AY, {width: 1.6, head: 10, alpha: seg(.16, .3)});
  // each plot titled: what it is, and its symbol (29 Sep: "title ekle neyin ne oldugunu")
  const ty = 64;
  const tl = [['input ', 'x(t)', (IN.x0 + IN.x1) / 2, .12], ['system, impulse response ', 'h(t)', bx.x + bx.w / 2, .17],
              ['output ', 'y(t)', (OUT.x0 + OUT.x1) / 2, .22]];
  for (const [w, m, x, t0] of tl) { const s = lab(t0); title(w, m, x, ty + rise(s), {alpha: s}); }
  // where the cursor of (b) is, on both signals
  if (ca > 0) {
    dot(IN.x0 + (IN.x1 - IN.x0) * tc / TT, AY - IN.s * xAt(tc), 3.4, {color: C.navy, fill: '#fff', width: 1.6, alpha: ca});
    dot(OUT.x0 + (OUT.x1 - OUT.x0) * tc / TT, AY - OUT.s * yAt(tc), 3.4, {color: C.accent, fill: C.accent, width: 1.2, alpha: ca});
  }
}

/* ------------------------------------------------------------ (b) */
const HB = 222;                            // the row of (b) and (c)
const PB = {x: 84, w: 560}, TOP = {y: 258, h: 116}, BOT = {y: 412, h: 104};
const XB = u => PB.x + u / TT * PB.w;
/* x(tau) h(t - tau) on 0 <= tau <= t, and its integral (trapezoids, 5 ms): y(t) */
function product(tc) {
  const n = Math.max(2, Math.ceil(tc / .005)), pts = [];
  let area = 0, prev = 0;
  for (let i = 0; i <= n; i++) {
    const u = tc * i / n, q = xAt(u) * hAt(tc - u);
    pts.push([u, q]);
    if (i) area += (q + prev) / 2 * tc / n;
    prev = q;
  }
  return {pts, area};
}
const areaAt = tc => product(tc).area;
function panelB(tc, ca) {
  panel('b', 20, HB, {alpha: seg(.06, .2)});
  const sa = seg(.1, .25);
  const w0 = text('convolution,', 54, HB, {size: 17, color: C.body, alpha: sa});
  math('x(t) ∗ h(t) = y(t)', 60 + w0, HB, {size: 17, color: C.body, alpha: sa});
  text('real time', PB.x + PB.w, HB, {size: 14, color: C.muted, align: 'right', alpha: seg(.5, .25)});
  const A1 = axes({x: PB.x, y: TOP.y, w: PB.w, h: TOP.h, xlim: [0, TT], ylim: [-1.15, 1.15],
                   xticks: [0, 1, 2, 3, 4, 5, 6, 7, 8], yticks: [-1, 0, 1], xfmt: () => '',
                   progress: seg(.06, .35)});
  math('τ', PB.x + PB.w + 10, TOP.y + TOP.h + 5, {size: 17, alpha: seg(.3, .2)});
  const A2 = axes({x: PB.x, y: BOT.y, w: PB.w, h: BOT.h, xlim: [0, TT], ylim: [-D.yax, D.yax],
                   xticks: [0, 1, 2, 3, 4, 5, 6, 7, 8], yticks: D.yticks, xlabel: 't\\ (\\rm{s})',
                   progress: seg(.12, .35)});
  A1.inside(() => line([[PB.x, A1.Y(0)], [PB.x + PB.w, A1.Y(0)]], {color: C.rule, width: 1}));
  A2.inside(() => line([[PB.x, A2.Y(0)], [PB.x + PB.w, A2.Y(0)]], {color: C.rule, width: 1}));
  // the product x(tau) h(t - tau): its area is y(t)
  const pr = product(tc), prod = pr.pts.map(q => [XB(q[0]), A1.Y(q[1])]), area = pr.area, hh = [];
  for (let i = 0; i <= 400; i++) { const u = tc - tc * i / 400; hh.push([XB(u), A1.Y(hAt(tc - u))]); }
  const pa = ca * seg(.45, .25);
  if (pa > 0 && prod.length > 1) A1.inside(() => {
    const y0 = A1.Y(0), poly = new Path2D();
    poly.moveTo(prod[0][0], y0); for (const q of prod) poly.lineTo(q[0], q[1]); poly.lineTo(prod[prod.length - 1][0], y0); poly.closePath();
    ctx.save(); ctx.globalAlpha *= pa;
    ctx.save(); ctx.beginPath(); ctx.rect(PB.x, TOP.y, PB.w, y0 - TOP.y); ctx.clip(); ctx.fillStyle = C.wash; ctx.fill(poly); ctx.restore();
    ctx.save(); ctx.beginPath(); ctx.rect(PB.x, y0, PB.w, TOP.y + TOP.h - y0); ctx.clip(); ctx.fillStyle = C.steel2; ctx.fill(poly); ctx.restore();
    ctx.restore();
  });
  // x(tau), h(t - tau) and the product's outline
  const xp = []; for (let i = 0; i <= N; i++) xp.push([XB(i * DT), A1.Y(i < N ? X[i] : 0)]);
  A1.inside(() => {
    line(xp, {color: C.navy, width: 2.2, progress: seg(.18, .4)});
    if (hh.length > 1) line(hh, {color: C.blue, width: 2, dash: [7, 4], alpha: ca * seg(.45, .25)});
    if (prod.length > 1) line(prod, {color: C.accent, width: 1.6, alpha: pa});
  });
  // the cursor, inside each plot: the row between them carries the output's title
  if (ca > 0) {
    A1.inside(() => line([[XB(tc), TOP.y], [XB(tc), TOP.y + TOP.h]], {color: C.ink, width: 1, alpha: .5 * ca}));
    A2.inside(() => line([[XB(tc), BOT.y], [XB(tc), BOT.y + BOT.h]], {color: C.ink, width: 1, alpha: .5 * ca}));
  }
  // y(t): whole and faint, and drawn up to the cursor
  const yp = []; for (let i = 0; i < YF.length; i += 2) yp.push([XB(i * DTF), A2.Y(YF[i])]);
  A2.inside(() => {
    line(yp, {color: C.mist, width: 1.6, progress: seg(.22, .4)});
    const k = Math.floor(tc / (2 * DTF));
    if (k > 0) line(yp.slice(0, k + 1).concat([[XB(tc), A2.Y(yAt(tc))]]), {color: C.navy, width: 2.2, alpha: ca});
  });
  if (ca > 0) dot(XB(tc), A2.Y(yAt(tc)), 4.2, {color: '#fff', fill: C.accent, width: 1.4, alpha: ca});
  // the top plot's title: its three curves, each named (the legend is the title)
  const la = seg(.3, .25), ly = TOP.y - 12;
  let lx = PB.x + 2;
  line([[lx, ly - 5], [lx + 26, ly - 5]], {color: C.navy, width: 2.2, alpha: la});
  lx += 32 + title('input ', 'x(\\tau)', lx + 32, ly, {size: 15, align: 'left', alpha: la}) + 22;
  line([[lx, ly - 5], [lx + 26, ly - 5]], {color: C.blue, width: 2, dash: [7, 4], alpha: la});
  lx += 32 + title('flipped impulse response ', 'h(t - \\tau)', lx + 32, ly, {size: 15, align: 'left', alpha: la}) + 22;
  ctx.save(); ctx.globalAlpha *= la; ctx.fillStyle = C.wash; ctx.fillRect(lx, ly - 11, 26, 12); ctx.restore();
  line([[lx, ly - 5], [lx + 26, ly - 5]], {color: C.accent, width: 1.6, alpha: la});
  title('their product', '', lx + 32, ly, {size: 15, align: 'left', alpha: la});
  // the bottom plot's title (29 Sep: "output plotuna"), and the running values of its point:
  // y(t) the page's own integral of the product
  const ba = seg(.35, .25), by = BOT.y - 12;
  title('output ', 'y(t)\\rm{: the area of the product}', PB.x + 2, by, {size: 15, align: 'left', alpha: ba});
  if (ca > 0) {
    const ra = ca * seg(.5, .2);
    const w2 = math(`y(t) = ${area.toFixed(3)}`, PB.x + PB.w, by, {size: 15, align: 'right', alpha: ra});
    math(`t = ${tc.toFixed(1)}\\ \\rm{s}`, PB.x + PB.w - w2 - 18, by, {size: 15, color: C.body, align: 'right', alpha: ra});
  }
}

/* ------------------------------------------------------------ (c)
   A x = b, each part named under a brace, as \underbrace{A}_{\text{system}}
   would set it (29 Sep: the matrix picture confused; its parts, named) */
function brace(x0, x1, y, h, o) {          // a TikZ brace under [x0, x1] from height y, its tip h below
  const r = h / 2, xm = (x0 + x1) / 2, pts = [];
  const arc = (cx, cy, a0, a1) => { for (let i = 0; i <= 8; i++) { const a = lerp(a0, a1, i / 8); pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); } };
  arc(x0 + r, y, Math.PI, Math.PI / 2); arc(xm - r, y + h, -Math.PI / 2, 0);
  arc(xm + r, y + h, Math.PI, 1.5 * Math.PI); arc(x1 - r, y, Math.PI / 2, 0);
  line(pts, o);
}
const EQ = {cx: 842, y: 382, size: 36};
function panelC() {
  panel('c', 690, HB, {alpha: seg(.1, .2)});
  text('linear system', 724, HB, {size: 17, color: C.body, alpha: seg(.14, .25)});
  const parts = [['A', 'system', .2], ['x', 'input', .25], ['=', '', .28], ['b', 'output', .3]];
  ctx.save(); ctx.font = font({size: 16}); const wl = parts.map(p => p[1] ? ctx.measureText(p[1]).width : 0); ctx.restore();
  const ws = parts.map(p => math(p[0], 0, -1e4, {size: EQ.size, alpha: 0}));
  const box = parts.map((p, i) => Math.max(ws[i], wl[i]) + (p[1] ? 14 : 18));
  let x = EQ.cx - box.reduce((a, b) => a + b, 0) / 2;
  parts.forEach(([m, w, t0], i) => {
    const c = x + box[i] / 2, s = lab(t0);
    math(m, c, EQ.y + rise(s), {size: EQ.size, align: 'center', alpha: s});
    if (w) {
      brace(c - ws[i] / 2 - 6, c + ws[i] / 2 + 6, EQ.y + 10, 9, {color: C.ink, width: 1.3, progress: seg(t0 + .1, .35)});
      const u = lab(t0 + .15);
      text(w, c, EQ.y + 44 + rise(u), {size: 16, color: C.body, align: 'center', alpha: u});
    }
    x += box[i];
  });
}

function draw() {
  const tc = cursor(), ca = curA();
  panelA(tc, ca);
  panelB(tc, ca);
  panelC();
  math(D.params, 20, H - 14, {size: 14, color: C.muted, alpha: seg(.4, .3)});
}
boot();
"""


def model():
    tj = np.arange(N + 1) * DT                         # samples, the last one closes the record
    x = sum(M.hann_pulse(tj, *p) for p in PULSES)
    x[-1] = 0.0
    dtf = DT / SUB
    tf = np.arange(N * SUB + 1) * dtf
    xf = np.interp(tf, tj, x)                          # exactly the piecewise linear input
    y = M.foh_filter(xf, dtf)
    g = M.foh_column(N, DT)
    A = np.zeros((N, N))
    for i in range(N):
        A[i, :i + 1] = g[i::-1]
    b = A @ x[:N]
    return dict(tj=tj, x=x, tf=tf, xf=xf, y=y, g=g, A=A, b=b, dtf=dtf)


def build():
    r = model()
    wn = 2 * np.pi * M.FN
    ymax = float(np.abs(r["y"]).max())
    print(f"max |x| = {np.abs(r['x']).max():.3f}, max |y| = {ymax:.4f}, max |A_ij| = {np.abs(r['g']).max():.5f}")
    yax = 0.3 if ymax > 0.22 else 0.25
    data = dict(
        n=N, dt=DT, dtf=r["dtf"], T=T, zw=M.ZETA * wn, wd=wn * np.sqrt(1 - M.ZETA ** 2),
        x=common.f32(r["x"]), y=common.f32(r["y"]),
        ymax=ymax, yax=yax, yticks=[-0.2, 0, 0.2],
        poster=3.55,
        params=(r"\rm{damped resonator, }f_{\rm{n}}\rm{ = %g Hz, }\zeta\rm{ = %g;   input: %d samples, }"
                r"\Delta t\rm{ = %g s apart, linear between them}" % (M.FN, M.ZETA, N, DT)),
    )
    title = ("Figure 1: The input, system, output relationship that runs through signal processing, "
             "system identification, and machine learning alike")
    aria = ("An input of three pulses enters a system, a damped resonator, and leaves as a ringing output. "
            "Below, the same output is built as a convolution: the flipped impulse response slides along "
            "the input and the area of their product traces y(t). Beside it the same relationship as a "
            "linear system, Ax = b, names its parts: A the system, x the input, b the output.")
    common.build_html("sp-io", title, aria, 1000, H_PAGE, data, JS)
    png = common.still("sp-io")
    print("still:", png)
    validate(r)
    return r


def validate(r):
    """Three independent routes to y, the closed forms of h, and the page's
    own integral; writes sp_io.check.txt and prints it."""
    from scipy.integrate import quad, solve_ivp
    wn = 2 * np.pi * M.FN
    wd = wn * np.sqrt(1 - M.ZETA ** 2)
    tj, x, tf, y = r["tj"], r["x"], r["tf"], r["y"]
    xf = lambda u: np.interp(u, tj, x)
    # 1. the equation of motion: y'' + 2 zeta wn y' + wn^2 y = wd x(t), integrated
    #    sample interval by sample interval (the forcing is linear on each)
    s, ode = np.zeros(2), [0.0]
    for k in range(N):
        a, b = tj[k], tj[k + 1]
        rhs = lambda u, q: [q[1], wd * xf(u) - 2 * M.ZETA * wn * q[1] - wn * wn * q[0]]
        sol = solve_ivp(rhs, (a, b), s, method="DOP853", rtol=1e-12, atol=1e-15,
                        t_eval=tf[(tf > a + 1e-12) & (tf <= b + 1e-12)])
        ode += list(sol.y[0])
        s = sol.y[:, -1]
    e_ode = np.abs(np.array(ode) - y).max()
    # 2. adaptive quadrature of the convolution integral at a few times
    tq = [1.3, 2.1, 3.552, 5.2, 7.9]
    yq = []
    for tc in tq:
        pts = [u for u in tj if 0 < u < tc]
        v, _ = quad(lambda u: xf(u) * M.h(tc - u), 0, tc, points=pts, limit=400, epsabs=1e-14, epsrel=1e-13)
        yq.append(v)
    yf_at = np.interp(tq, tf, y)
    e_quad = np.abs(np.array(yq) - yf_at).max()
    # 3. A x = b against y at the samples
    e_b = np.abs(r["b"] - y[::SUB][:N]).max()
    # 4. closed forms of h: its integral, its zero crossings
    ih, _ = quad(lambda u: M.h(u), 0, 80, limit=2000, epsabs=1e-14)
    ih_cf = wd / wn ** 2
    zc = np.pi / wd
    # 5. the page's own integral of the product, and its y(t)
    exprs = [f"[{', '.join(f'areaAt({v})' for v in tq)}]", f"[{', '.join(f'yAt({v})' for v in tq)}]"]
    area_pg, y_pg = M.check_page("sp-io", exprs)
    e_pg = np.abs(area_pg - yf_at).max()
    e_py = np.abs(y_pg - yf_at).max()
    ymax = np.abs(y).max()

    L = []
    say = L.append
    say("Figure 1, input, system, output: check of tools/numfig/sp_io.py")
    say("")
    say("MODEL")
    say(f"  System: the damped resonator h(t) = exp(-zeta w_n t) sin(w_d t), f_n = {M.FN:g} Hz,")
    say(f"  zeta = {M.ZETA:g}, w_d = w_n sqrt(1 - zeta^2) = {wd:.6f} rad/s (the impulse response of")
    say("  w_d / (s^2 + 2 zeta w_n s + w_n^2)).")
    say(f"  Input: {N} samples dt = {DT:g} s apart over {T:g} s, three sin^2 pulses (centre, length,")
    say(f"  height) = {PULSES}, and linear between the samples (first order hold).")
    say("  Output: y = x * h, exact for that input: the kernel of the hold, g_0 and g_k = Im C e^{p k dt},")
    say("  run as a complex first order recursion (sp_model.foh_filter), on a grid of")
    say(f"  dt/{SUB} = {r['dtf']:g} s. max |y| = {ymax:.5f}.")
    say(f"  A x = b, the linear system (c) states: A the {N} x {N} lower triangular Toeplitz matrix of the")
    say(f"  same kernel on the sample grid, A_ij = g_(i-j), max |A_ij| = {np.abs(r['g']).max():.5f}; x the input's")
    say("  samples; b = A x.")
    say("")
    say("VALIDATION")
    say("  1. The equation of motion y'' + 2 zeta w_n y' + w_n^2 y = w_d x(t), integrated interval by")
    say("     interval (DOP853, rtol 1e-12), against the recursion on the whole fine grid:")
    say(f"     largest difference {e_ode:.1e} ({e_ode / ymax:.1e} of max |y|).")
    say("  2. Adaptive quadrature of the convolution integral (breakpoints at the samples) at")
    say(f"     t = {tq} s: largest difference {e_quad:.1e}.")
    say(f"  3. b = A x against y(t_i) at all {N} samples: largest difference {e_b:.1e}: sampled, the")
    say("     convolution of (b) is the linear system of (c), b the output. Row i of A is h(t_i - tau)")
    say("     sampled with the hold's weights: the flipped impulse response of (b).")
    say(f"  4. Integral of h from 0 to infinity: {ih:.10f} against w_d / w_n^2 = {ih_cf:.10f}")
    say(f"     ({(ih - ih_cf) / ih_cf:+.1e}); zero crossings of h every pi / w_d = {zc:.6f} s.")
    say("  5. The page: its own trapezoid integral of x(tau) h(t - tau) (5 ms steps), the number it")
    say(f"     prints as y(t), against y at the same t: largest difference {e_pg:.1e}; its y(t) curve")
    say(f"     (float32) against y: {e_py:.1e}.")
    say("")
    say("DISPLAY")
    say("  (a) each plot titled with what it is and its symbol: input x(t), system, impulse response")
    say("  h(t), output y(t). (b) runs in real time: 8 s of record in 8 s, then rests 1.1 s and glides")
    say("  back; its top plot is titled by naming its three curves (input, flipped impulse response,")
    say("  their product), its bottom plot 'output y(t): the area of the product', with the running")
    say("  t and y(t) on the same row. The cursor is drawn inside each plot, never across the row")
    say("  between them. (c) states A x = b with each part named under a brace (A system, x input,")
    say("  b output); the matrix picture of the first version is gone at the professor's request")
    say("  (29 Sep), its numbers stay in 3. above.")
    say("  (a) draws x and y each to its own height (y is 0.23 at most); (b) carries the scales.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_io.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
