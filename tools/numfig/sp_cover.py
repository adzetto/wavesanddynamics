"""The cover of the signal processing document: input, system, output, and the
system identified from them by estimation and optimization.

One problem, end to end, with the resonator of sp_model (f_n = 1 Hz,
zeta = 0.1): a swept sine (0.3 to 1.7 Hz in 12 s) drives it; its output is
measured with noise 20 dB below it; the model output yhat(t; f_n, zeta) = x * h
is fitted to the measurement by least squares,

    J(f_n, zeta) = mean (y_meas - yhat)^2,

and gradient descent on J (the steps drawn perpendicular to its contours)
walks from a first guess to the estimate. The page recomputes the model's
impulse response and output for every iterate itself (the exact first order
hold recursion of sp_model), so the system box and the output panel follow
the descent.

Run: python tools/numfig/sp_cover.py  (writes the page, the still and the
check file; prints the key numbers).
"""
import os

import numpy as np
from scipy.optimize import least_squares

import common
import sp_model as SM

DT, T = 0.01, 12.0
F0, F1 = 0.3, 1.7          # the sweep (Hz)
TAPER = 1.0                # cosine taper at each end (s)
SNR_DB = 20.0
SEED = 2026
TH0 = (0.85, 0.27)         # first guess (f_n in Hz, zeta)
ETA = 0.12                 # gradient descent step
KMAX = 60
MC = 500                   # repeated experiments for the spread of the estimate
FL, ZL = (0.8, 1.2), (0.0, 0.3)   # the plane drawn, equal scale in f_n and zeta


def chirp():
    t = np.arange(0, T + DT / 2, DT)
    ph = 2 * np.pi * (F0 * t + (F1 - F0) * t ** 2 / (2 * T))
    tap = np.clip(np.minimum(t, T - t) / TAPER, 0, 1)
    tap = 0.5 * (1 - np.cos(np.pi * tap))
    x = tap * np.sin(ph)
    return t, x.astype(np.float32).astype(np.float64)     # the numbers the page gets


def model(x, th):
    return SM.foh_filter(x, DT, th[0], th[1])


JS = r"""
const D = DATA;
const X = b64f32(D.x), YM = b64f32(D.ym), NS = X.length, DT = D.dt, TT = D.T;
const PATH = D.path, KN = PATH.length - 1, FL = D.fl, ZL = D.zl;
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);

/* the model: y = x * h(t; f_n, zeta), exact for x linear between samples
   (the first order hold recursion of sp_model.foh_filter), in complex numbers */
function cexp(re, im) { const m = Math.exp(re); return [m * Math.cos(im), m * Math.sin(im)]; }
function cmul(a, b) { return [a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]]; }
function cdiv(a, b) { const d = b[0] * b[0] + b[1] * b[1]; return [(a[0] * b[0] + a[1] * b[1]) / d, (a[1] * b[0] - a[0] * b[1]) / d]; }
const _mem = {};
function modelOut(fn, z) {
  const key = fn.toFixed(7) + ',' + z.toFixed(7);
  if (_mem[key]) return _mem[key];
  const wn = 2 * Math.PI * fn, p = [-z * wn, wn * Math.sqrt(1 - z * z)];
  const e = cexp(p[0] * DT, p[1] * DT), ei = cdiv([1, 0], e), pp = cmul(p, p), den = [pp[0] * DT, pp[1] * DT];
  const a0 = cdiv([e[0] - 1 - p[0] * DT, e[1] - p[1] * DT], den);
  const cc = cdiv([e[0] + ei[0] - 2, e[1] + ei[1]], den);
  const b1 = cmul([cc[0] - a0[0], cc[1] - a0[1]], e);
  const y = new Float64Array(NS);
  let Y = [0, 0], xp = 0;
  for (let n = 0; n < NS; n++) {
    const xn = X[n], ye = cmul(e, Y);
    Y = [ye[0] + a0[0] * xn + b1[0] * xp, ye[1] + a0[1] * xn + b1[1] * xp];
    y[n] = Y[1]; xp = xn;
  }
  const ks = Object.keys(_mem); if (ks.length > 64) delete _mem[ks[0]];
  return (_mem[key] = y);
}
const hAt = (u, fn, z) => { const wn = 2 * Math.PI * fn; return u < 0 ? 0 : Math.exp(-z * wn * u) * Math.sin(wn * Math.sqrt(1 - z * z) * u); };

/* ------------------------------------------------------------ clock
   Intro (README, round 2): strokes by .9 s, labels by 1.2 s. The descent
   starts at .6 s, one step every .16 s, each a Motion spring glide; it
   rests on the estimate, glides back to the first guess and starts again. */
const T0 = .6, STEP = .16, HOLD = 2.6, BACK = 1.0, REST = .4;
const RUNT = KN * STEP, PER = RUNT + HOLD + BACK + REST;
function clock() {
  if (t < T0) return {k: 0, s: 0, back: 0, trail: 1};
  const c = Math.floor((t - T0) / PER), u = t - T0 - c * PER, b0 = T0 + c * PER;
  if (u < RUNT) { const k = Math.floor(u / STEP); return {k, s: settle(b0 + k * STEP, .14), back: 0, trail: 1}; }
  if (u < RUNT + HOLD) return {k: KN, s: 0, back: 0, trail: 1};
  return {k: KN, s: 0, back: settle(b0 + RUNT + HOLD, BACK * .8), trail: 1 - seg(b0 + RUNT + HOLD, .35)};
}
function theta(st) {
  if (st.back > 0) return [lerp(PATH[KN][0], PATH[0][0], st.back), lerp(PATH[KN][1], PATH[0][1], st.back)];
  if (st.k >= KN) return PATH[KN];
  const a = PATH[st.k], b = PATH[st.k + 1];
  return [lerp(a[0], b[0], st.s), lerp(a[1], b[1], st.s)];
}
const POSTER_T = T0 + RUNT + 1.2;

/* ------------------------------------------------------------ layout */
const PY = 44, PH = 120;
const IN = {x: 60, w: 152}, SB = {x: 262, w: 152}, OUT = {x: 496, w: 152}, OP = {x: 740, w: 160}, XF = 880;
function header(s, x, t0) { const a = lab(t0); math(s, x, 30 + rise(a), {size: 17, align: 'center', alpha: a}); }
function signal(ax, vals, o) {
  const pts = []; for (let n = 0; n < NS; n += 2) pts.push([ax.X(n * DT), ax.Y(vals[n])]);
  ax.inside(() => line(pts, o));
}

function draw() {
  const st = clock(), th = theta(st), fn = th[0], z = th[1];
  // input
  header('\\rm{input}\\quad x(t)', IN.x + IN.w / 2, .1);
  const A1 = axes({x: IN.x, y: PY, w: IN.w, h: PH, xlim: [0, TT], ylim: [-1.25, 1.25], xticks: [0, 6, 12],
                   yticks: [-1, 0, 1], xlabel: 't\\ (\\rm{s})', tickSize: 14, labelSize: 15, progress: seg(0, .3)});
  signal(A1, X, {color: C.navy, width: 1.4, progress: seg(.05, .4)});
  arrow(IN.x + IN.w + 8, PY + PH / 2, SB.x - 6, PY + PH / 2, {width: 1.6, head: 9, alpha: seg(.15, .25)});

  // system: the model's impulse response, and the true one it is after
  header('\\rm{system}\\quad h(t)', SB.x + SB.w / 2, .14);
  line([[SB.x, PY], [SB.x + SB.w, PY], [SB.x + SB.w, PY + PH], [SB.x, PY + PH], [SB.x, PY]], {color: C.ink, width: 1.8, progress: seg(.04, .4)});
  const hx0 = SB.x + 10, hx1 = SB.x + SB.w - 10, hy = PY + PH / 2 + 6, hs = 44, HT = 6;
  const tru = [], mod = [];
  for (let i = 0; i <= 200; i++) {
    const u = HT * i / 200, X_ = hx0 + (hx1 - hx0) * i / 200;
    tru.push([X_, hy - hs * hAt(u, D.fn, D.zeta)]); mod.push([X_, hy - hs * hAt(u, fn, z)]);
  }
  line([[hx0, hy], [hx1, hy]], {color: C.rule, width: 1, alpha: seg(.2, .3)});
  line(mod, {color: C.blue, width: 2.2, progress: seg(.2, .4)});
  line(tru, {color: C.ink, width: 1.1, dash: [4, 3], alpha: .7, progress: seg(.26, .4)});
  arrow(SB.x + SB.w + 6, PY + PH / 2, OUT.x - 34, PY + PH / 2, {width: 1.6, head: 9, alpha: seg(.2, .25)});

  // output: the measurement, and the model's output for the current guess
  header('\\rm{output}\\quad y(t)', OUT.x + OUT.w / 2, .18);
  const A2 = axes({x: OUT.x, y: PY, w: OUT.w, h: PH, xlim: [0, TT], ylim: [-.85, .85], xticks: [0, 6, 12],
                   yticks: [-0.5, 0, 0.5], xlabel: 't\\ (\\rm{s})', tickSize: 14, labelSize: 15, progress: seg(.08, .3)});
  signal(A2, YM, {color: C.mist, width: 1.1, progress: seg(.14, .4)});
  const yh = modelOut(fn, z);
  signal(A2, yh, {color: C.navy, width: 1.6, progress: seg(.22, .4)});
  const la = seg(.4, .25), lx = A2.X(.45), l1 = A2.Y(.68), l2 = A2.Y(.47);
  line([[lx, l1 - 4], [lx + 16, l1 - 4]], {color: C.mist, width: 1.6, alpha: la});
  text('data', lx + 21, l1, {size: 14, color: C.body, alpha: la});
  line([[lx, l2 - 4], [lx + 16, l2 - 4]], {color: C.navy, width: 1.6, alpha: la});
  text('model', lx + 21, l2, {size: 14, color: C.body, alpha: la});
  arrow(OUT.x + OUT.w + 8, PY + PH / 2, OP.x - 36, PY + PH / 2, {width: 1.6, head: 9, alpha: seg(.25, .25)});

  // estimation and optimization: J(f_n, zeta), the descent, the estimate
  header('\\rm{estimation and optimization}', OP.x + OP.w / 2, .22);
  const A3 = axes({x: OP.x, y: PY, w: OP.w, h: PH, xlim: FL, ylim: ZL, xticks: [0.8, 0.9, 1, 1.1, 1.2],
                   yticks: [0, 0.1, 0.2, 0.3], xfmt: v => v.toFixed(1), yfmt: v => v === 0 ? '0' : v.toFixed(1),
                   xlabel: 'f_{\\rm{n}}\\ (\\rm{Hz})', tickSize: 14, labelSize: 15, progress: seg(.1, .3)});
  math('\\zeta', OP.x - 34, PY + 30, {size: 16, alpha: seg(.3, .2)});
  A3.inside(() => {
    D.contours.forEach((lv, i) => {
      const pr = seg(.16 + .03 * i, .35);
      for (const pl of lv) line(pl.map(q => [A3.X(q[0]), A3.Y(q[1])]), {color: C.sky, width: 1, progress: pr});
    });
    // the steps taken so far, and the marker on its way to the next
    if (t >= T0) {
      const k = Math.min(st.k, KN), pts = PATH.slice(0, k + 1).map(q => [A3.X(q[0]), A3.Y(q[1])]);
      if (st.back <= 0) pts.push([A3.X(fn), A3.Y(z)]);
      if (pts.length > 1) line(pts, {color: C.navy, width: 1.4, alpha: st.trail});
      for (let j = 0; j <= k; j++) dot(A3.X(PATH[j][0]), A3.Y(PATH[j][1]), 1.9, {color: C.navy, fill: C.navy, width: .6, alpha: st.trail});
    }
  });
  dot(A3.X(PATH[0][0]), A3.Y(PATH[0][1]), 3.6, {color: C.navy, fill: '#fff', width: 1.3, alpha: seg(.4, .2)});
  dot(A3.X(fn), A3.Y(z), 4.6, {color: '#fff', fill: C.accent, width: 1.3, alpha: seg(.45, .15)});

  // identification: the estimate goes back into the system
  const fb = seg(.3, .4), yl = 232;
  line([[XF, PY + PH], [XF, yl], [SB.x + SB.w / 2, yl]], {width: 1.6, progress: fb});
  arrow(SB.x + SB.w / 2, yl, SB.x + SB.w / 2, PY + PH + 3, {width: 1.6, head: 9, alpha: seg(.6, .2)});
  const ia = lab(.44), ix = 600;
  const s1 = `\\rm{identification}\\quad f_{\\rm{n}} = ${fn.toFixed(4)}\\ \\rm{Hz},\\quad \\zeta\\ = ${z.toFixed(4)}`;
  const w1 = math(s1, 0, -100, {size: 15, alpha: 0});
  ctx.save(); ctx.globalAlpha *= ia; ctx.fillStyle = '#fff'; ctx.fillRect(ix - w1 / 2 - 8, yl - 11, w1 + 16, 20); ctx.restore();
  math(s1, ix, yl + 5 + rise(ia), {size: 15, align: 'center', alpha: ia});
}
boot();
"""


def build():
    t, x = chirp()
    y = model(x, (SM.FN, SM.ZETA))
    rng = np.random.default_rng(SEED)
    sig = y.std() * 10 ** (-SNR_DB / 20)
    ym = (y + sig * rng.standard_normal(len(y))).astype(np.float32).astype(np.float64)
    res = lambda th: ym - model(x, th)
    J = lambda th: np.mean(res(th) ** 2)

    def grad(th, h=1e-7):
        th = np.asarray(th, float)
        return np.array([(J(th + [h, 0]) - J(th - [h, 0])) / (2 * h), (J(th + [0, h]) - J(th - [0, h])) / (2 * h)])

    ls = least_squares(res, [0.95, 0.12], xtol=1e-15, ftol=1e-15, gtol=1e-15)
    th_hat = ls.x
    path = [np.array(TH0, float)]
    for _ in range(KMAX):
        nxt = path[-1] - ETA * grad(path[-1])
        path.append(nxt)
        if np.linalg.norm(nxt - th_hat) < 2e-5:
            break
    path = np.array(path)
    # J on the plane, and its contours (levels spaced geometrically above the minimum)
    fs = np.linspace(*FL, 81)
    zs = np.linspace(max(ZL[0], 0.004), ZL[1], 76)
    Jg = np.array([[J((f, zz)) for f in fs] for zz in zs])
    import contourpy
    gen = contourpy.contour_generator(fs, zs, Jg)
    jmin = J(th_hat)
    levels = jmin * np.array([1.6, 3, 6, 12, 25, 50, 100, 170])
    contours = []
    for lv in levels:
        lines = [np.round(seg_, 5).tolist() for seg_ in gen.lines(lv) if len(seg_) > 2]
        contours.append(lines)
    print(f"estimate f_n = {th_hat[0]:.6f} Hz, zeta = {th_hat[1]:.6f}; J = {jmin:.4e} (sigma^2 = {sig ** 2:.4e})")
    print(f"gradient descent: {len(path) - 1} steps from {TH0} to ({path[-1][0]:.5f}, {path[-1][1]:.5f})")
    print(f"J on the plane: {Jg.min():.3e} to {Jg.max():.3e}; levels {np.round(levels, 5).tolist()}")
    data = dict(
        dt=DT, T=T, fn=SM.FN, zeta=SM.ZETA, x=common.f32(x), ym=common.f32(ym),
        path=np.round(path, 7).tolist(), contours=contours, fl=list(FL), zl=list(ZL),
    )
    title = "Input, system, output, and the system identified from them"
    aria = ("A swept sine enters a damped resonator and its output is measured with noise. Gradient descent on "
            "the squared error between the measured output and a model's output walks across the contours of "
            "that error, from a first guess to the estimated natural frequency and damping ratio, while the "
            "model's impulse response and output settle onto the system's.")
    common.build_html("sp-cover", title, aria, 1000, 253, data, JS)
    png = common.still("sp-cover")
    print("still:", png)
    out = dict(t=t, x=x, y=y, ym=ym, sig=sig, th_hat=th_hat, ls=ls, path=path, J=J, grad=grad, levels=levels)
    validate(out)
    return out


def validate(r):
    """The output against the equation of motion, the descent against a
    least squares solver, the estimate's spread against Monte Carlo, and the
    page's own model; writes sp_cover.check.txt and prints it."""
    from scipy.integrate import solve_ivp
    t, x, y, ym, sig, th_hat, path = r["t"], r["x"], r["y"], r["ym"], r["sig"], r["th_hat"], r["path"]
    wn = 2 * np.pi * SM.FN
    wd = wn * np.sqrt(1 - SM.ZETA ** 2)
    # 1. y'' + 2 zeta wn y' + wn^2 y = wd x(t), x linear between samples
    rhs = lambda u, q: [q[1], wd * np.interp(u, t, x) - 2 * SM.ZETA * wn * q[1] - wn * wn * q[0]]
    s, ode = np.zeros(2), [0.0]
    for k in range(len(t) - 1):
        sol = solve_ivp(rhs, (t[k], t[k + 1]), s, method="DOP853", rtol=1e-12, atol=1e-15)
        s = sol.y[:, -1]
        ode.append(s[0])
    e_ode = np.abs(np.array(ode) - y).max()
    # 2. the descent against Levenberg-Marquardt / trust region least squares
    e_gd = np.abs(path[-1] - th_hat).max()
    g_end = np.linalg.norm(r["grad"](th_hat))
    g_chk = np.abs(r["grad"](path[3], 1e-5) - r["grad"](path[3], 1e-7)).max() / np.abs(r["grad"](path[3])).max()
    # 3. estimation: Gauss-Newton covariance against 200 repeated experiments
    jac = r["ls"].jac
    s2 = np.sum(r["ls"].fun ** 2) / (len(ym) - 2)
    cov = s2 * np.linalg.inv(jac.T @ jac)
    sd = np.sqrt(np.diag(cov))
    est = []
    for k in range(MC):
        rng = np.random.default_rng(10_000 + k)
        yk = y + sig * rng.standard_normal(len(y))
        est.append(least_squares(lambda th: yk - model(x, th), th_hat, xtol=1e-14, ftol=1e-14).x)
    est = np.array(est)
    sd_mc = est.std(axis=0, ddof=1)
    bias = est.mean(axis=0) - np.array([SM.FN, SM.ZETA])
    # 4. the page's own model output against numpy at the first guess and at the estimate
    a0, a1, b0, b1 = (repr(float(v)) for v in (path[0][0], path[0][1], th_hat[0], th_hat[1]))
    got = SM.check_page("sp-cover", [f"Array.from(modelOut({a0}, {a1}))", f"Array.from(modelOut({b0}, {b1}))"])
    e_pg = max(np.abs(got[0] - model(x, path[0])).max(), np.abs(got[1] - model(x, th_hat)).max())
    snr = 10 * np.log10(np.mean(y ** 2) / sig ** 2)

    L = []
    say = L.append
    say("The cover (input, system, output, identification): check of tools/numfig/sp_cover.py")
    say("")
    say("MODEL")
    say(f"  System: the resonator of sp_model, h(t) = exp(-zeta w_n t) sin(w_d t), f_n = {SM.FN:g} Hz, zeta = {SM.ZETA:g}.")
    say(f"  Input: a linear sweep {F0:g} to {F1:g} Hz over {T:g} s, cosine tapered over {TAPER:g} s at each end,")
    say(f"  sampled every {DT:g} s and linear between samples (float32, as the page gets it).")
    say(f"  Output: y = x * h, exact for that input (sp_model.foh_filter); measured with white Gaussian")
    say(f"  noise sigma = {sig:.5f}, {snr:.1f} dB below the output's power (seed {SEED}).")
    say("  Estimation: least squares, J(f_n, zeta) = mean (y_meas - yhat(f_n, zeta))^2, the maximum")
    say("  likelihood estimate for this Gaussian noise.")
    say(f"  Optimization: gradient descent from ({TH0[0]:g} Hz, {TH0[1]:g}), step {ETA:g}, central differences")
    say("  (1e-7) for the gradient, stopped within 2e-5 of the least squares solution; the plane is drawn")
    say("  at one scale for f_n and zeta, so each step is perpendicular to the contours as drawn.")
    say(f"  {len(path) - 1} steps. Contours of J at {', '.join(f'{v:.3g}' for v in r['levels'] / r['J'](th_hat))} times its minimum, on an 81 x 76 grid.")
    say("")
    say("VALIDATION")
    say("  1. The output against the equation of motion y'' + 2 zeta w_n y' + w_n^2 y = w_d x(t),")
    say(f"     integrated sample by sample (DOP853, rtol 1e-12): largest difference {e_ode:.1e}")
    say(f"     ({e_ode / np.abs(y).max():.1e} of max |y|).")
    say(f"  2. Least squares solver (trust region, scipy): f_n = {th_hat[0]:.6f} Hz, zeta = {th_hat[1]:.6f};")
    say(f"     the descent ends {e_gd:.1e} from it. Gradient of J there: {g_end:.1e} (J = {r['J'](th_hat):.4e},")
    say(f"     sigma^2 = {sig ** 2:.4e}). Central differences 1e-5 against 1e-7 on the path: {g_chk:.1e} (relative).")
    say(f"  3. The estimate's spread: Gauss-Newton covariance s^2 (J^T J)^-1 against {MC} repeated")
    say("     experiments (new noise, seeds 10000 on, each solved by least squares):")
    say(f"     f_n: {sd[0]:.2e} Hz against {sd_mc[0]:.2e} Hz ({(sd[0] - sd_mc[0]) / sd_mc[0] * 100:+.0f} %),"
        f" zeta: {sd[1]:.2e} against {sd_mc[1]:.2e} ({(sd[1] - sd_mc[1]) / sd_mc[1] * 100:+.0f} %);")
    se = sd_mc / np.sqrt(MC)
    say(f"     mean error of the {MC} estimates (bias): f_n {bias[0]:+.1e} Hz, zeta {bias[1]:+.1e}, that is")
    say(f"     {bias[0] / se[0]:+.1f} and {bias[1] / se[1]:+.1f} standard errors of the mean: no significant bias.")
    say(f"     The estimate shown, ({th_hat[0]:.4f} Hz, {th_hat[1]:.4f}), lies {abs(th_hat[0] - SM.FN) / sd[0]:.1f} and"
        f" {abs(th_hat[1] - SM.ZETA) / sd[1]:.1f} standard deviations from the truth.")
    say("  4. The page computes the model's output itself (the same recursion in complex arithmetic):")
    say(f"     against numpy at the first guess and at the estimate, largest difference {e_pg:.1e}.")
    say("")
    say("DISPLAY")
    say("  One descent step every 0.16 s, each a Motion spring glide; the readout on the feedback line is")
    say("  the current (f_n, zeta). The 95 % confidence region (about +-0.001) is below one drawing unit")
    say("  at this scale and is not drawn.")
    txt = "\n".join(L) + "\n"
    with open(os.path.join(common.HERE, "sp_cover.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    build()
