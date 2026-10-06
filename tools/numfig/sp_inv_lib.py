"""The inverse problem shared by Figures 4 and 5 of the signal processing
document (sp_inv_reg.py, sp_inv_iter.py): his "undoing a blur" example,
computed here once, exactly as his two pages set it up.

    m (the hidden cause): a smooth bump and a sharp block on 0 < x < 1,
        m(x) = exp(-((x - 0.28)/0.07)^2) + 0.75 [0.58 < x < 0.8];
    G (the system): a Gaussian blur on N = 64 cells, x_i = (i + 1/2)/N,
        G_ij = exp(-(x_i - x_j)^2 / (2 s^2)) / (s sqrt(2 pi)) / N,  s = 0.045;
    d = G m + e (the effect), e white Gaussian noise of standard deviation
        sigma = level * max|G m|, level 0.1 %, 1 % or 10 %; three draws of e
        (numpy default_rng seeds 1, 2, 3), each the same standard normal vector
        at every level, as his page scales one draw with its noise slider.

Everything is done through numpy's SVD G = U diag(s) V^T: a regularized
solution is m_f = sum_i f_i (u_i^T d / s_i) v_i, with the filter factors
    none        f_i = 1,
    TSVD        f_i = 1 for i <= k, else 0,
    Tikhonov    f_i = s_i^2 / (s_i^2 + alpha^2),
    Landweber   f_i = 1 - (1 - omega s_i^2)^k,  omega = 1 / s_1^2 (k steps of
                gradient descent from m = 0, in closed form),
and its residual |G m_f - d| = |(1 - f) * U^T d|, its norm |m_f| = |f U^T d / s|
and its error |m_f - m| / |m| follow from the same coefficients. CGLS is run
for real (cgls()). The discrepancy principle takes the noise level as
delta = sigma sqrt(N), the expected |e|, as his pages do.

The figures' pages draw the estimate for any strength the reader sets by the
same sum, from DATA's float64 V, s and U^T d (LIB, synth()): the check files
compare the page's numbers with numpy's (check_page()).
"""
import base64
import os
import shutil
import tempfile
import threading

import numpy as np
from scipy.optimize import brentq, minimize_scalar

import common

N = 64                      # cells
SIG = 0.045                 # blur width
LEVELS = (1e-3, 1e-2, 1e-1)  # noise standard deviation / max |G m|
LEVEL_NAMES = ("0.1%", "1%", "10%")
SEEDS = (1, 2, 3)           # the three noise draws (numpy default_rng)
DECADES = (-7.0, 1.0)       # the strength slider: log10(alpha / s_1), his range
NA = 321                    # alphas on that range, 40 per decade
K_CGLS = 50                 # CGLS iterations, as his page
LW_DECADES = 8.0            # Landweber: k from 1 to 10^8, as his page


# ------------------------------------------------------------------ the problem
def cells():
    return (np.arange(N) + 0.5) / N


def blur(x=None):
    x = cells() if x is None else x
    return np.exp(-(x[:, None] - x[None, :]) ** 2 / (2 * SIG ** 2)) / (SIG * np.sqrt(2 * np.pi)) / N


def truth(x=None):
    x = cells() if x is None else x
    return np.exp(-((x - 0.28) / 0.07) ** 2) + np.where((x > 0.58) & (x < 0.8), 0.75, 0.0)


class Problem:
    """G, m, the SVD and the nine data sets (three levels times three draws)."""

    def __init__(self):
        self.x = cells()
        self.G = blur(self.x)
        self.m = truth(self.x)
        self.Gm = self.G @ self.m
        self.dmax = float(np.abs(self.Gm).max())
        self.mnorm = float(np.linalg.norm(self.m))
        U, s, Vt = np.linalg.svd(self.G)
        V = Vt.T
        # a fixed sign for each pair (the largest entry of v_i positive), so the
        # numbers do not depend on LAPACK's choice
        sg = np.sign(V[np.abs(V).argmax(0), np.arange(N)])
        self.U, self.s, self.V = U * sg, s, V * sg
        self.t = self.V.T @ self.m           # the truth's coefficients v_i^T m
        self.omega = 1.0 / s[0] ** 2
        self.la = np.log10(s[0]) + np.linspace(DECADES[0], DECADES[1], NA)   # log10 alpha grid
        self.z = {sd: np.random.default_rng(sd).standard_normal(N) for sd in SEEDS}

    def data(self, li, ri):
        """Noise level LEVELS[li], draw SEEDS[ri]: d, U^T d, sigma, delta, e."""
        sig = LEVELS[li] * self.dmax
        e = sig * self.z[SEEDS[ri]]
        d = self.Gm + e
        return dict(d=d, beta=self.U.T @ d, sig=sig, delta=sig * np.sqrt(N), e=e)

    # filters
    def tik(self, alpha):
        return self.s ** 2 / (self.s ** 2 + alpha ** 2)

    def tsvd(self, k):
        return (np.arange(N) < k).astype(float)

    def lw(self, k):
        """Landweber's filter after k steps, 1 - (1 - w)^k with w = omega s^2, without
        cancellation: -expm1(k log1p(-w)) keeps k w where w is far below the precision
        (s_i < 1e-8); w = 1 (to rounding) at i = 1 gives f = 1."""
        w = self.omega * self.s ** 2
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(w < 1.0, -np.expm1(k * np.log1p(-np.minimum(w, 1.0))), 1.0)

    def coef(self, f, beta):
        return f * beta / self.s

    def ev(self, f, beta):
        """residual |G m_f - d|, norm |m_f|, relative error |m_f - m| / |m|."""
        c = f * beta / self.s
        return (float(np.sqrt(np.sum(((1 - f) * beta) ** 2))), float(np.linalg.norm(c)),
                float(np.linalg.norm(c - self.t) / self.mnorm))

    def solution(self, f, beta):
        return self.V @ (f * beta / self.s)

    # parameter choice: Tikhonov
    def tik_path(self, beta):
        return np.array([self.ev(self.tik(10 ** l), beta) for l in self.la])

    def tik_dp(self, D):
        """The discrepancy principle: the alpha whose residual is delta."""
        g = lambda l: self.ev(self.tik(10 ** l), D["beta"])[0] - D["delta"]
        return 10 ** brentq(g, self.la[0], self.la[-1], xtol=1e-14, rtol=1e-14, maxiter=500)

    def tik_best(self, beta):
        """The alpha of the lowest true error (needs the truth)."""
        path = self.tik_path(beta)
        i = int(np.argmin(path[:, 2]))
        lo, hi = self.la[max(i - 1, 0)], self.la[min(i + 1, NA - 1)]
        r = minimize_scalar(lambda l: self.ev(self.tik(10 ** l), beta)[2], bounds=(lo, hi),
                            method="bounded", options={"xatol": 1e-12})
        return 10 ** r.x

    def curvature(self, l, beta):
        """The curvature of the Tikhonov L-curve (ln |r|, ln |m|) at alpha = 10^l,
        in closed form: with eta = |m|^2, rho = |r|^2, eta' = d eta / d alpha =
        -(4/alpha) sum (1 - f) f^2 beta^2 / s^2,
        kappa = 2 eta rho / |eta'| (alpha^2 eta' rho + 2 alpha eta rho + alpha^4 eta eta')
                / (alpha^4 eta^2 + rho^2)^(3/2)."""
        a = 10.0 ** l
        f = self.tik(a)
        c = f * beta / self.s
        eta, rho = np.sum(c * c), np.sum(((1 - f) * beta) ** 2)
        etap = -4 / a * np.sum((1 - f) * f * f * beta * beta / self.s ** 2)
        return float(2 * eta * rho / abs(etap) * (a * a * etap * rho + 2 * a * eta * rho + a ** 4 * eta * etap)
                     / (a ** 4 * eta * eta + rho * rho) ** 1.5)

    def tik_corner(self, beta):
        """The L-curve's corner: its point of greatest curvature."""
        fine = np.linspace(self.la[0], self.la[-1], 4001)
        kap = np.array([self.curvature(l, beta) for l in fine])
        i = int(np.argmax(kap))
        r = minimize_scalar(lambda l: -self.curvature(l, beta), bounds=(fine[max(i - 2, 0)], fine[min(i + 2, 4000)]),
                            method="bounded", options={"xatol": 1e-12})
        return 10 ** r.x, -r.fun

    # parameter choice: truncated SVD
    def tsvd_path(self, beta):
        return np.array([self.ev(self.tsvd(k), beta) for k in range(1, N + 1)])

    def tsvd_dp(self, D):
        p = self.tsvd_path(D["beta"])
        return int(1 + np.argmax(p[:, 0] <= D["delta"]))

    def tsvd_best(self, beta):
        return int(1 + np.argmin(self.tsvd_path(beta)[:, 2]))

    # Landweber: k on a log grid, its discrepancy stop and its best k
    def lw_dp(self, D, kmax=10 ** 9):
        """The first k (an integer) whose residual is at most delta."""
        lo, hi = 1, kmax
        if self.ev(self.lw(hi), D["beta"])[0] > D["delta"]:
            return None
        while lo < hi:
            mid = (lo + hi) // 2
            if self.ev(self.lw(mid), D["beta"])[0] <= D["delta"]:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def lw_best(self, beta, kmax=10 ** 8):
        """The k of the lowest true error: every k to 5,000, then a ratio of
        1.0005, then every k within 0.2 % of the best found."""
        ks = np.unique(np.concatenate([np.arange(1, 5001),
                                       np.round(5000 * 1.0005 ** np.arange(1, int(np.log(kmax / 5000) / np.log(1.0005)) + 2))]))
        ks = ks[ks <= kmax].astype(np.int64)
        err = np.array([self.ev(self.lw(k), beta)[2] for k in ks])
        k0 = int(ks[np.argmin(err)])
        near = np.arange(max(1, int(k0 * 0.998)), int(k0 * 1.002) + 2)
        e2 = np.array([self.ev(self.lw(k), beta)[2] for k in near])
        return int(near[np.argmin(e2)])


# ------------------------------------------------------------------ CGLS
def cgls(G, d, K):
    """K iterations of CGLS (conjugate gradients on the normal equations,
    Hestenes and Stiefel's form for least squares) from x = 0. Returns the
    iterates (K x n) and the residual norms its recursion carries."""
    x = np.zeros(G.shape[1])
    r = d.astype(float).copy()
    s = G.T @ r
    p = s.copy()
    gam = s @ s
    X, R = [], []
    for _ in range(K):
        q = G @ p
        a = gam / (q @ q)
        x = x + a * p
        r = r - a * q
        s = G.T @ r
        gn = s @ s
        p = s + (gn / gam) * p
        gam = gn
        X.append(x.copy())
        R.append(np.linalg.norm(r))
    return np.array(X), np.array(R)


def gkb_krylov(G, d, K):
    """The exact Krylov solutions x_k = argmin |G x - d| over
    span{G^T d, (G^T G) G^T d, ...} for k = 1..K, through Golub-Kahan
    bidiagonalization with full reorthogonalization (the arithmetic CGLS and
    LSQR do in exact arithmetic), and the Ritz values theta_j of each k: the
    squared singular values of the bidiagonal B_k."""
    m, n = G.shape
    Uk = np.zeros((m, K + 1))
    Vk = np.zeros((n, K))
    B = np.zeros((K + 1, K))
    beta1 = np.linalg.norm(d)
    Uk[:, 0] = d / beta1
    X, TH = [], []
    for k in range(K):
        v = G.T @ Uk[:, k] - (B[k, k - 1] * Vk[:, k - 1] if k else 0)
        for _ in range(2):
            v -= Vk[:, :k] @ (Vk[:, :k].T @ v)
        al = np.linalg.norm(v)
        Vk[:, k] = v / al
        B[k, k] = al
        u = G @ Vk[:, k] - al * Uk[:, k]
        for _ in range(2):
            u -= Uk[:, :k + 1] @ (Uk[:, :k + 1].T @ u)
        be = np.linalg.norm(u)
        Uk[:, k + 1] = u / be
        B[k + 1, k] = be
        Bk = B[:k + 2, :k + 1]
        rhs = np.zeros(k + 2)
        rhs[0] = beta1
        y = np.linalg.lstsq(Bk, rhs, rcond=None)[0]
        X.append(Vk[:, :k + 1] @ y)
        TH.append(np.linalg.svd(Bk, compute_uv=False) ** 2)
    return np.array(X), TH


# ------------------------------------------------------------------ the pages
def f64(a):
    """A float array as base64 of float64, for LIB's b64f64(): exact."""
    return base64.b64encode(np.ascontiguousarray(a, dtype="<f8").tobytes()).decode("ascii")


def check_page(name, exprs, query=""):
    """Evaluate JavaScript expressions in nf-<name>.html (served beside the
    fonts, opened as a still) and return the results as numpy arrays."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out = []
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        errors = []
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still{query}")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            for ex in exprs:
                out.append(np.array(pg.evaluate(ex), dtype=float))
            b.close()
        srv.shutdown()
        if errors:
            raise RuntimeError(f"nf-{name}: script errors: {errors}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def overlaps_q(name, queries, width=672):
    """The overlap check (engine.js ?overlap) of nf-<name>.html in the states
    its query string sets: {query: (labels, crossings)}, one load per query,
    a PNG of each state with a fault in the temp directory. Also returns the
    script errors met."""
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="numfig-")
    out, errors = {}, []
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            for j, q in enumerate(queries):
                pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still&overlap&{q}")
                pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
                pg.wait_for_timeout(60)
                lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                out[q] = (lab, cro)
                if lab or cro:
                    pg.locator("canvas").screenshot(path=os.path.join(tempfile.gettempdir(), f"nf-{name}-overlapq-{j}.png"))
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out, errors


# ------------------------------------------------------------------ the pages' shared script
JS_LIB = r"""
/* ---- sp_inv shared (tools/numfig/sp_inv_lib.py): the SVD, the filtered sum, numbers, controls ---- */
function b64f64(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new Float64Array(u.buffer); }
const NC = DATA.n, SV = b64f64(DATA.s), VV = b64f64(DATA.V), TV = b64f64(DATA.t), MT = b64f64(DATA.m), MNORM = DATA.mnorm;
const XC = Array.from({ length: NC }, (_, i) => (i + .5) / NC);
/* an estimate from its filter factors f: coefficients c = f (u^T d) / s, residual |G m - d| = |(1 - f) u^T d|,
   norm |m| = |c| and error |m - m_true| / |m_true| = |c - V^T m_true| / |m_true|; m itself is V c */
function est(f, beta) {
  const c = new Float64Array(NC); let r2 = 0, n2 = 0, e2 = 0;
  for (let j = 0; j < NC; j++) {
    c[j] = f[j] * beta[j] / SV[j];
    r2 += ((1 - f[j]) * beta[j]) ** 2; n2 += c[j] * c[j]; e2 += (c[j] - TV[j]) ** 2;
  }
  return { c, rho: Math.sqrt(r2), eta: Math.sqrt(n2), err: Math.sqrt(e2) / MNORM };
}
function synth(c) {
  const m = new Float64Array(NC);
  for (let i = 0; i < NC; i++) { let s = 0; for (let j = 0; j < NC; j++) s += VV[i * NC + j] * c[j]; m[i] = s; }
  return m;
}
/* numbers, as his text writes them: three significant digits, a power of ten in TeX */
function sci(v, d = 2) {
  if (!isFinite(v)) return '\\infty';
  if (v === 0) return '0';
  let ex = Math.floor(Math.log10(Math.abs(v))), ms = (v / 10 ** ex).toFixed(d);
  if (Math.abs(parseFloat(ms)) >= 10) { ex += 1; ms = (v / 10 ** ex).toFixed(d); }
  if (ex >= -1 && ex <= 2) return (+v.toPrecision(d + 1)).toString().replace('-', '−');
  return ms.replace('-', '−') + ' \\times\\ 10^{' + ex + '}';
}
function pctv(v) {                         // a relative error as a percentage
  const p = v * 100;
  if (p < 1000) return (p < 10 ? p.toFixed(2) : p.toFixed(1)) + '%';
  return sci(p, 1) + '%';
}
const lab = t0 => settle(t0, .28), rise = s => 4 * (1 - s);
function tw(s, size) { ctx.save(); ctx.font = font({ size }); const w = ctx.measureText(s).width; ctx.restore(); return w; }
function sub(letter, x, y, words, a) {     // a panel's letter and its subtitle (mlc_lib.sub)
  if (a <= 0) return;
  panel(letter, x, y, { alpha: a });
  text(words, x + 35, y, { size: 17, color: C.body, alpha: a });
}
/* a legend as the family draws one: a thin box, white fill, serif 16; items [mark(x, y, a), tex] in rows */
function legend(x, y, rows, a, o = {}) {
  if (a <= 0) return;
  const rh = o.rh || 21, pad = 9, gap = o.gap || 18, mk = 30;
  const mw = s => math(s, 0, -1e4, { size: 16, alpha: 0 });
  const widths = rows.map(r => r.reduce((s, it) => s + mk + 4 + mw(it[1]), 0) + gap * (r.length - 1));
  const w = Math.max(...widths) + 2 * pad, h = rows.length * rh + 6;
  const x0 = o.right ? x - w : x;
  line([[x0, y], [x0 + w, y], [x0 + w, y + h], [x0, y + h]], { color: C.ink, width: 1, fill: '#fff', close: true, alpha: a });
  rows.forEach((r, j) => {
    let cx = x0 + pad; const cy = y + 3 + rh * j + rh / 2;
    for (const [mark, words] of r) { mark(cx + 13, cy, a); cx += mk + math(words, cx + mk + 4, cy + 5.5, { size: 16, alpha: a }) + 4 + gap; }
  });
  return { x: x0, y, w, h };
}
/* log axes: values in log10, tick labels as powers of ten */
const p10 = v => v === 0 ? '1' : v === 1 ? '10' : '10^{' + v + '}';

/* ================================================ controls drawn in the figure
   Chips are engine.js uiChip()s; the slider is Figure 18a's (mlb_neuron): a 3 unit C.rule track,
   C.mist up to the handle, a white handle with a 2 unit navy ring, larger under the pointer or held.
   Each control: {id, kind: 'chip' | 'slider', geometry, hit: [x0, y0, x1, y1], off(), and for a chip
   label(), on(), act(); for a slider get() and set(u), u in [0, 1], and keys(e)}. A transparent DOM
   stand-in over each takes the keyboard. A press on a control, or on the strip that holds them,
   never also pauses the figure (the engine toggles on a click of the canvas). */
const FIG = document.querySelector('.fig');
const UI = { list: [], hov: '', down: '', drag: '', press: '', key: '', ground: () => false, kb: [] };
function redraw() { if (!playing) render(); }
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
const ctlById = id => UI.list.find(c => c.id === id);
const ctlAt = (X, Y) => UI.list.find(c => !c.off() && X >= c.hit[0] && X <= c.hit[2] && Y >= c.hit[1] && Y <= c.hit[3]) || null;
function drawChip(c, a) { uiChip(c.x, c.y, c.w, c.h, c.label(), { on: c.on(), off: c.off(), hover: UI.hov === c.id, down: UI.down === c.id, size: 16 }, a); }
function drawSlider(c, a) {
  const off = c.off(), u = clamp(c.get()), hx = lerp(c.x0, c.x1, u);
  line([[c.x0, c.y], [c.x1, c.y]], { color: C.rule, width: 3, alpha: a });
  for (const v of c.ticks || []) line([[lerp(c.x0, c.x1, v), c.y - 5], [lerp(c.x0, c.x1, v), c.y + 5]], { color: C.rule, width: 1, alpha: a });
  if (off) return;
  line([[c.x0, c.y], [hx, c.y]], { color: C.mist, width: 3, alpha: a });
  dot(hx, c.y, UI.hov === c.id || UI.drag === c.id ? 8.5 : 7.5, { color: C.navy, fill: '#fff', width: 2, alpha: a });
}
const sliderU = (c, X) => clamp((X - c.x0) / (c.x1 - c.x0));
if (!STILL) {
  const css = document.createElement('style');
  /* a stand-in covers its control's whole hit area (24 CSS px at least at the page's 672 px); its
     focus ring hugs the drawn chip, 3 units outside it (::after, set by placeKeys) */
  css.textContent = '.nfk{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;' +
    'outline:none;color:transparent;font:inherit;overflow:visible}' +
    '.nfk::after{content:"";position:absolute;left:var(--l,0);top:var(--t,0);right:var(--r,0);bottom:var(--b,0);pointer-events:none}' +
    '.nfk:focus-visible::after{outline:2px solid #095A94;outline-offset:2px}';
  document.head.appendChild(css);
  cv.style.touchAction = 'pan-y pinch-zoom';
  cv.addEventListener('pointerdown', e => {
    if (e.button !== 0) return;
    const [X, Y] = toUnits(e), c = ctlAt(X, Y);
    UI.press = c ? c.id : (UI.ground(X, Y) ? '#' : '');
    if (!c) return;
    try { cv.setPointerCapture(e.pointerId); } catch (_) {}
    if (c.kind === 'slider') { UI.drag = c.id; c.set(sliderU(c, X)); }
    else UI.down = c.id;
    redraw();
  });
  cv.addEventListener('pointermove', e => {
    const [X, Y] = toUnits(e);
    if (UI.drag) { ctlById(UI.drag).set(sliderU(ctlById(UI.drag), X)); return; }
    if (UI.press && UI.press !== '#' && !UI.drag) {     // a chip held: pressed only while the pointer is on it
      const c = ctlAt(X, Y), d = c && c.id === UI.press ? UI.press : '';
      if (d !== UI.down) { UI.down = d; redraw(); }
    }
    if (e.pointerType !== 'mouse') return;
    const c = ctlAt(X, Y), h = c ? c.id : '';
    cv.style.cursor = c ? 'pointer' : UI.ground(X, Y) ? 'default' : '';
    if (h !== UI.hov) { UI.hov = h; redraw(); }
  });
  const drop = ok => e => {
    if (UI.drag) { UI.drag = ''; redraw(); return; }
    if (!UI.down && !UI.press) return;
    const [X, Y] = toUnits(e), c = ctlAt(X, Y), was = UI.down;
    UI.down = '';
    if (e.pointerType !== 'mouse') UI.hov = '';
    if (ok && c && c.id === was && c.kind === 'chip') c.act(); else redraw();
  };
  cv.addEventListener('pointerup', drop(true));
  cv.addEventListener('pointercancel', drop(false));
  cv.addEventListener('pointerleave', () => { if (UI.drag || UI.down) return; if (UI.hov) { UI.hov = ''; redraw(); } cv.style.cursor = ''; });
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const pr = UI.press; UI.press = '';
    const [X, Y] = toUnits(e);
    if (pr || ctlAt(X, Y) || UI.ground(X, Y)) e.stopPropagation();
  }, true);
}
/* the keyboard's stand-ins: one per control, in radio groups where the chips are a choice of one */
function keyStandIns(groups) {
  if (STILL) return;
  const ctl = FIG.querySelector('.ctl');
  const add = (parent, tag, role, label) => {
    const el = document.createElement(tag); el.className = 'nfk';
    if (tag === 'button') el.type = 'button';
    if (role) el.setAttribute('role', role);
    if (label) el.setAttribute('aria-label', label);
    parent === FIG ? FIG.insertBefore(el, ctl) : parent.appendChild(el);
    return el;
  };
  for (const g of groups) {
    if (g.radio) {
      const box = document.createElement('div'); box.setAttribute('role', 'radiogroup'); box.setAttribute('aria-label', g.label);
      FIG.insertBefore(box, ctl);
      g.ids.forEach((id, i) => {
        const c = ctlById(id), b = add(box, 'button', 'radio', '');
        b.addEventListener('keydown', e => {
          const n = g.ids.length, dd = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
          let j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : dd ? (i + dd + n) % n : (e.key === 'Enter' || e.key === ' ') ? i : -1;
          if (j < 0) return;
          e.preventDefault();
          for (let s = 0; s < n && ctlById(g.ids[j]).off(); s++) j = (j + (dd || 1) + n) % n;
          UI.kb.find(k => k.id === g.ids[j]).el.focus(); ctlById(g.ids[j]).act();
        });
        b.addEventListener('click', e => { e.stopPropagation(); if (!c.off()) c.act(); });
        UI.kb.push({ id, el: b, radio: g });
      });
    } else {
      for (const id of g.ids) {
        const c = ctlById(id);
        if (c.kind === 'slider') {
          const el = add(FIG, 'div', 'slider', g.label); el.tabIndex = 0;
          el.setAttribute('aria-valuemin', '0'); el.setAttribute('aria-valuemax', '100');
          el.addEventListener('keydown', e => { if (!c.off() && c.keys(e)) e.preventDefault(); });
          el.addEventListener('click', e => e.stopPropagation());
          UI.kb.push({ id, el });
        } else {
          const el = add(FIG, 'button', null, '');
          el.addEventListener('click', e => { e.stopPropagation(); if (!c.off()) c.act(); });
          UI.kb.push({ id, el });
        }
      }
    }
  }
}
/* the stand-ins sit on what they stand for, and say what it is and whether it is chosen */
function placeKeys(stamp) {
  if (STILL || !UI.kb.length) return;
  const key = cv.clientWidth + ':' + stamp;
  if (key === UI.key) return;
  UI.key = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  for (const k of UI.kb) {
    const c = ctlById(k.id), el = k.el;
    // the ring's box (the chip, or the slider's track) inside the stand-in, which is the hit area,
    // never less than 36 units (24 CSS px at the page's width) either way
    const [r0, s0, r1, s1] = c.kind === 'slider' ? [c.x0 - 10, c.y - 14, c.x1 + 10, c.y + 14] : [c.x, c.y, c.x + c.w, c.y + c.h];
    let [x0, y0, x1, y1] = c.hit;
    if (x1 - x0 < 36) { const m = (x0 + x1) / 2; x0 = m - 18; x1 = m + 18; }
    if (y1 - y0 < 36) { const m = (y0 + y1) / 2; y0 = m - 18; y1 = m + 18; }
    x0 = Math.min(x0, r0); y0 = Math.min(y0, s0); x1 = Math.max(x1, r1); y1 = Math.max(y1, s1);
    el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0);
    el.style.setProperty('--l', px(r0 - x0)); el.style.setProperty('--t', px(s0 - y0));
    el.style.setProperty('--r', px(x1 - r1)); el.style.setProperty('--b', px(y1 - s1));
    el.setAttribute('aria-label', c.aria ? c.aria() : c.label());
    if (c.off()) el.setAttribute('aria-disabled', 'true'); else el.removeAttribute('aria-disabled');
    if (c.kind === 'slider') { el.setAttribute('aria-valuenow', String(Math.round(100 * clamp(c.get())))); el.setAttribute('aria-valuetext', c.valueText()); }
    else if (k.radio) {
      el.setAttribute('aria-checked', String(c.on()));
      const sel = k.radio.ids.find(id => ctlById(id).on()) || k.radio.ids[0];
      el.tabIndex = k.id === sel ? 0 : -1;
    } else if (c.toggle) el.setAttribute('aria-pressed', String(c.on()));
  }
}
/* ?key=value&...: a state chosen by the address, for the overlap check of every state */
const QS = new URLSearchParams(location.search);
"""
