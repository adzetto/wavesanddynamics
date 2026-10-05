"""Figure 7: vibrational modes of two span beams, (a) similar span lengths,
(b) more different span lengths.

Model: a partially continuous two span Euler-Bernoulli girder. Pins at the
three supports; over the middle pin the two spans' end rotations are joined
by a rotational spring k (a continuity plate, a link slab, a bearing):
k -> infinity is a continuous girder, k = 0 two independent simply
supported spans. Exact: the dynamic stiffness of the four support rotations
(beam_model.ContinuousBeam with joints), natural frequencies by the
Wittrick-Williams count, mode shapes from its null vector and the closed
form field transfer matrix. Cross checked against Hermite finite elements
with the same spring.

His frequencies are values from experience; they read as two nearly
independent simply supported spans (f2 = 4 f1 in each). The fit (run with
--fit): one uniform girder (one EI/m), the two span lengths and k; for each
k the lengths are refitted to his four values (minimax), and k is the
stiffest joint for which every residual stays within 2 %. The result is
rounded (lengths to 0.1 m, k to two figures, down) into PARAMS, and every
run re-checks the residuals.

Run: python tools/numfig/multispan.py [--fit]
"""
import os
import sys

import numpy as np
from scipy.integrate import simpson
from scipy.optimize import minimize

import beam_model as bm
import common

NAME = "multispan"
HERE = os.path.dirname(os.path.abspath(__file__))

EI, M = 1.0e11, 1.0e4               # uniform steel box girder: N m^2, kg/m
C0 = np.sqrt(EI / M)
TOL = 2.0                           # per cent, every residual
HIS = {"a": ["1.3 Hz", "1.45 Hz", "5.2 Hz", "5.92 Hz"],
       "b": ["1.23 Hz", "4.95 Hz", "5.8 Hz", "22.90 Hz"]}
DRAWN_DOM = {"a": "RLRL", "b": "LRLR"}          # his drawing: span marked "Dominating span"
PARAMS = {"a": (58.6, 62.5, 3.5e8),            # left span, right span (m), joint k (N m/rad)
          "b": (64.3, 29.4, 7.9e8)}            # from --fit (k_max 4.08e8, 8.29e8), rounded
NMODES = 8
NPTS = 121
# time: each row slowed by its own round factor (5 Oct 2026: no mode faster than
# about 1 Hz on screen), the smallest of FACTORS that keeps it at or below FMAX_SCREEN
FACTORS = (2, 5, 10, 20, 40, 50, 100)
FMAX_SCREEN = 0.8


def slow_for(f):
    return next(n for n in FACTORS if f / n <= FMAX_SCREEN)


def target(key):
    return np.array([float(s.split()[0]) for s in HIS[key]])


def model(L1, L2, k):
    return bm.ContinuousBeam([(L1, EI, M), (L2, EI, M)], [k])


def ss_length(F):
    """Span length whose first simply supported frequency is F (Hz)."""
    return np.pi * np.sqrt(C0 / (2 * np.pi * F))


def humps(w):
    """Lobes of a span shape: sign changes inside the span, plus one."""
    s = np.sign(w[2:-2])
    s = s[s != 0]
    return int(np.sum(s[1:] != s[:-1])) + 1


def pick(key, modes):
    """The four modes of his panel: (a) the first four; (b) the first three
    and the mode dominated by the short span with two lobes in it (his
    22.90 Hz: 'the shorter span sits right at its own second natural
    frequency and dominates with a two hump shape')."""
    if key == "a":
        return [0, 1, 2, 3]
    j = next(j for j in range(3, len(modes)) if modes[j]["dom"] == 1 and modes[j]["humps"][1] == 2)
    return [0, 1, 2, j]


def analyse(key, L1, L2, k, n=NMODES):
    beam = model(L1, L2, k)
    f = beam.frequencies(n)
    modes = []
    for fj in f:
        xs, ws, resid = beam.mode(fj, NPTS)
        big = max(ws, key=lambda w: np.max(np.abs(w)))
        peak = big[np.argmax(np.abs(big))]
        ws = [w / peak for w in ws]
        amp = [float(np.max(np.abs(w))) for w in ws]
        ke = [float(simpson(M * w ** 2, x=np.linspace(0, Ls, NPTS))) for w, Ls in zip(ws, (L1, L2))]
        modes.append({"f": fj, "w": ws, "amp": amp, "dom": int(np.argmax(amp)), "domE": int(np.argmax(ke)),
                      "ke": ke, "humps": [humps(w) for w in ws], "resid": resid})
    return beam, f, modes


# ------------------------------------------------------------------ the fit
def residuals(key, L1, L2, k):
    _, _, modes = analyse(key, L1, L2, k, n=6 if key == "b" else 4)
    sel = pick(key, modes)
    return 100 * (np.array([modes[j]["f"] for j in sel]) / target(key) - 1)


def fast_res(key, p, k):
    L1, L2 = ss_length(np.exp(p[0])), ss_length(np.exp(p[1]))
    f = model(L1, L2, k).frequencies(6 if key == "b" else 4, tol=1e-10)
    idx = [0, 1, 2, 5] if key == "b" else [0, 1, 2, 3]
    return 100 * (f[idx] / target(key) - 1)


def minimax(key, k, p0):
    o = minimize(lambda p: np.abs(fast_res(key, p, k)).max(), p0, method="Nelder-Mead",
                 options=dict(xatol=1e-8, fatol=1e-7, maxiter=600))
    return o.x, o.fun


def fit(key):
    T = target(key)
    p = np.log([T[1], T[0]] if key == "a" else [T[0], T[2]])     # uncoupled first frequencies
    lo, plo, hi = 0.0, p, 1e8
    p, e = minimax(key, hi, p)
    while e <= TOL:
        lo, plo = hi, p
        hi *= 1.6
        p, e = minimax(key, hi, p)
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        pm, em = minimax(key, mid, plo)
        if em <= TOL:
            lo, plo = mid, pm
        else:
            hi = mid
    kmax = lo
    ex = 10 ** np.floor(np.log10(kmax))
    mant = np.floor(kmax / ex * 10) / 10                 # two figures, down
    while True:                                           # step down until the rounded model fits
        k = round(mant, 1) * ex
        p, _ = minimax(key, k, plo)
        L1, L2 = ss_length(np.exp(p[0])), ss_length(np.exp(p[1]))
        best = None
        for d1 in (-0.1, 0, 0.1):
            for d2 in (-0.1, 0, 0.1):
                c1, c2 = round(round(L1, 1) + d1, 1), round(round(L2, 1) + d2, 1)
                e = np.abs(residuals(key, c1, c2, k)).max()
                if best is None or e < best[0]:
                    best = (e, c1, c2)
        print(f"  ({key}) k = {k:.2e}: rounded L1 = {best[1]} m, L2 = {best[2]} m, max residual {best[0]:.3f} %")
        if best[0] <= TOL:
            break
        mant -= 0.1
    print(f"({key}) k_max = {kmax:.4e} N m/rad; used: L1 = {best[1]} m, L2 = {best[2]} m,"
          f" k = {k:.2e} N m/rad, max residual {best[0]:.3f} %")
    return best[1], best[2], k


if "--fit" in sys.argv:
    for key in HIS:
        print(fit(key))
    sys.exit(0)

# ------------------------------------------------------------------ report
lines = []
say = lines.append
say("nf-multispan: Figure 7, vibrational modes of two span beams")
say("")
say("MODEL")
say("  A partially continuous two span Euler-Bernoulli girder: pins at the three")
say("  supports (w = 0; moment free at the two ends); over the middle pin the two")
say("  spans keep their own end rotation, joined by a rotational spring k. Exact: the")
say("  dynamic stiffness of the four support rotations from the closed form span")
say("  transfer matrix plus the spring; natural frequencies by the Wittrick-Williams")
say("  count (bisection to 1e-13; the spring has no frequencies of its own, so J0 is")
say("  the spans' clamped-clamped count); mode shapes from the null vector. No mesh.")
say(f"  One uniform girder, one frequency scale: EI = {EI:.1e} N m^2, m = {M:.0f} kg/m,"
    f" EI/m = {EI/M:.1e} m^4/s^2")
say("")
say("FIT (python multispan.py --fit)")
say("  His values are 'approximate frequency values from experience'; each span obeys")
say("  f2 = 4 f1 to within 2 % (a: 1.3 -> 5.2, 1.45 -> 5.8 vs his 5.92; b: 1.23 -> 4.92")
say("  vs 4.95, 5.8 -> 23.2 vs 22.90), which is two nearly independent simply supported")
say("  spans: a weak joint. Free: the two span lengths and k (EI/m fixed; only c/L^2")
say("  and k L/EI enter). For each k the lengths are refitted to his four values")
say("  (minimax); k is then the stiffest joint for which every residual is within 2 %.")
say("  Least squares alone takes (a) to k = 0 (two independent spans), because his")
say("  5.92/1.45 = 4.08 exceeds the simply supported 4 and any joint only lowers it.")
say("  Per span sections (right span EI and m both x r, r = 0.25 to 4) were tried: at the")
say("  stiffest joint within 2 % some row still moves the other span only 1 to 5 % (a) and")
say("  0.5 to 2.4 % (b), the 22.90 Hz row about 2 % for every r; no clearer, so one girder.")
say("  Rounded: lengths to 0.1 m, k to two figures (down); residuals rechecked below.")
say("")

DATA = {"cases": {}}
results = {}
all_ok = True
for key in ("a", "b"):
    L1, L2, k = PARAMS[key]
    beam, f, modes = analyse(key, L1, L2, k)
    sel = pick(key, modes)
    results[key] = (beam, f, modes, sel)
    unc = [[bm.freq_from_z(n * np.pi, Ls, EI, M) for n in (1, 2, 3, 4, 5)] for Ls in (L1, L2)]
    say(f"CASE ({key}): left span L1 = {L1} m, right span L2 = {L2} m, joint k = {k:.2e} N m/rad"
        f" (k L1/EI = {k*L1/EI:.3f}, k L2/EI = {k*L2/EI:.3f})")
    say("  uncoupled spans (k = 0, simply supported, (n pi/L)^2 sqrt(EI/m)/2 pi):")
    say("    left : " + ", ".join(f"{v:.3f}" for v in unc[0]) + " Hz")
    say("    right: " + ", ".join(f"{v:.3f}" for v in unc[1]) + " Hz")
    say("  coupled modes (exact); dominating span by amplitude and by kinetic energy:")
    for j, md in enumerate(modes):
        tag = f"  <- his {HIS[key][sel.index(j)]}" if j in sel else ""
        ratio = min(md["amp"]) / max(md["amp"])
        say(f"    mode {j+1}: {md['f']:8.4f} Hz  amp {'LR'[md['dom']]}  energy {'LR'[md['domE']]}"
            f"  other span {100*ratio:5.1f} %  lobes L,R = {md['humps']}{tag}")
    say(f"  null vector residual (smallest/largest singular value): max {max(m['resid'] for m in modes):.1e}")
    his = target(key)
    got = np.array([modes[j]["f"] for j in sel])
    res = 100 * (got / his - 1)
    all_ok &= bool(np.all(np.abs(res) <= TOL + 1e-9))
    say("  RESIDUALS against his labels (computed / his - 1):")
    for s, g, r in zip(HIS[key], got, res):
        say(f"    {s:>9s}: computed {g:7.3f} Hz, residual {r:+6.2f} %")
    say("")
    rows = []
    for r_, j in enumerate(sel):
        md = modes[j]
        forced = 1 - md["dom"]
        ratio = md["amp"][forced] / md["amp"][md["dom"]]
        mag = 0
        if ratio < 0.25:
            mag = max(n for n in (2, 3, 5, 10, 20, 30, 50, 100) if n * ratio <= 0.8)
        rows.append({"f": md["f"], "w1": md["w"][0], "w2": md["w"][1], "dom": md["dom"],
                     "label": HIS[key][r_], "mag": mag, "slow": slow_for(md["f"])})
    DATA["cases"][key] = {"L": [L1, L2], "k": k, "rows": rows}

say("CHECK 1: finite element cross check, same spring (Hermite cubic, consistent mass)")
for key in ("a", "b"):
    beam, f, modes, sel = results[key]
    say(f"  ({key}) elements per span, max relative difference over the first {NMODES} modes:")
    for ne in (5, 10, 20, 40):
        fe = bm.fe_frequencies(beam.spans, ne, NMODES, beam.joints)
        say(f"    {ne:3d}: {np.max(np.abs(fe/f - 1)):.2e}")
say("  (about 16 x per halving: the h^4 rate of Hermite elements)")
say("")
say("CHECK 2: the two limits of the joint, through the same code")
for key in ("a", "b"):
    L1, L2, k = PARAMS[key]
    fc = model(L1, L2, np.inf).frequencies(6)
    ss = np.sort([bm.freq_from_z(n * np.pi, Ls, EI, M) for Ls in (L1, L2) for n in (1, 2, 3, 4, 5)])[:6]
    hi = [np.max(np.abs(model(L1, L2, k * s).frequencies(6) / fc - 1)) for s in (1e2, 1e4, 1e6)]
    lo = [np.max(np.abs(model(L1, L2, k * s).frequencies(6) / ss - 1)) for s in (1e-2, 1e-4)]
    z0 = np.max(np.abs(model(L1, L2, 0.0).frequencies(6) / ss - 1))
    say(f"  ({key}) k x 1e2, 1e4, 1e6 against the continuous girder: " + ", ".join(f"{v:.1e}" for v in hi))
    say(f"      k x 1e-2, 1e-4, 0 against the simply supported spans: " + ", ".join(f"{v:.1e}" for v in lo)
        + f", {z0:.1e}")
say("  (errors fall as 1/k and as k: both limits are reached)")
eq = bm.ContinuousBeam([(50.0, EI, M), (50.0, EI, M)]).frequencies(4)
z = 50.0 * bm.wavenumber(2 * np.pi * eq, EI, M)
ref = [np.pi, bm.pc_root(1), 2 * np.pi, bm.pc_root(2)]
say("  continuous, two equal spans: k L against pi, 3.926602 (pinned clamped), 2 pi,")
say("  7.068583: " + ", ".join(f"{a:.9f} ({abs(a-b):.0e})" for a, b in zip(z, ref)))
say("")
say("HIS TEXT'S RULES, CHECKED ON THE COMPUTED MODES")
for key in ("a", "b"):
    beam, f, modes, sel = results[key]
    L1, L2, k = PARAMS[key]
    unc = [(bm.freq_from_z(n * np.pi, Ls, EI, M), s) for s, Ls in ((0, L1), (1, L2)) for n in range(1, 6)]
    for r_, j in enumerate(sel):
        md = modes[j]
        near = min(unc, key=lambda u: abs(np.log(md["f"] / u[0])))
        ok = "yes" if near[1] == md["dom"] == md["domE"] else "NO"
        drawn = DRAWN_DOM[key][r_]
        say(f"  ({key}) {HIS[key][r_]:>9s}: closest uncoupled {near[0]:6.3f} Hz ({'LR'[near[1]]} span);"
            f" computed dominating {'LR'[md['dom']]} (energy {'LR'[md['domE']]}): {ok};"
            f" lobes L,R = {md['humps']}; his drawing marks {drawn}"
            + ("" if drawn == "LR"[md["dom"]] else "  <- drawing differs"))
a_modes = [results["a"][2][j] for j in results["a"][3]]
say("  (a) same lobe count in both spans in every mode: "
    + ("yes" if all(m["humps"][0] == m["humps"][1] for m in a_modes) else "NO")
    + " (" + ", ".join(str(m["humps"]) for m in a_modes) + ")")
m22 = results["b"][2][results["b"][3][3]]
say(f"  (b) at 22.90 Hz: short span {m22['humps'][1]} lobes, long span {m22['humps'][0]} lobes"
    f" (mode {results['b'][3][3]+1}; modes 4 and 5, the long span's third and fourth, lie"
    " between and are not in his figure)")
say("")
say("DRAWING")
say("  Solid: the exact mode, one scale for both spans (the kink over the middle pin is")
say("  the joint). Dashed: the other span alone, magnified by the factor printed beside")
say("  it, where it moves less than a quarter of the dominating span.")
say(f"  Labels: his values (every residual within {TOL:g} %: {'yes' if all_ok else 'NO'}).")
say(f"TIME: each row shown slower by its own round factor (printed beside its frequency), the smallest of")
say(f"  {', '.join(map(str, FACTORS))} that keeps it at or below {FMAX_SCREEN} Hz on screen; each mode oscillates at its")
say("  computed frequency / its factor:")
for key in ("a", "b"):
    say(f"  ({key}) " + "; ".join(f"{r['label']}: computed {r['f']:.3f} Hz / {r['slow']} = {r['f'] / r['slow']:.3f} Hz"
                            for r in DATA["cases"][key]["rows"]))
if not all_ok:
    raise SystemExit("a residual exceeds 2 %: rerun --fit")
check = "\n".join(lines) + "\n"
print(check)
with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(check)

JS = r"""
const POSTER_T = __POSTER_T__;            // every mode at its extreme (each row is phased so)
const TS = 0.35, RAMP = 0.25;             // the physics starts at TS, full speed by TS + RAMP
function clock() { const s = t - TS; return s <= 0 ? 0 : s < RAMP ? s * s / (2 * RAMP) : s - RAMP / 2; }
const CP = POSTER_T - TS - RAMP / 2;      // the physics clock at the still
const lab = t0 => settle(t0, .28);        // labels arrive
const SC = 2.75;                           // px per metre, both panels
const ROW0 = 120, DY = 124, A = 30;
const LBW = 134, GAP = 14;                 // the label block left of each row, right-aligned; then the beam

/* a rotational spring over the middle pin, as TikZ draws one: a spiral */
function spiral(cx, cy, r, alpha) {
  const pts = [];
  for (let i = 0; i <= 90; i++) { const s = i / 90, a = -Math.PI / 2 + s * 3.2 * Math.PI; pts.push([cx + r * s * Math.cos(a), cy + r * s * Math.sin(a)]); }
  line(pts, { color: C.ink, width: 1.2, alpha });
}

function column(key, cx0, letter, words, tl) {
  const cs = DATA.cases[key], [L1, L2] = cs.L;
  const ha = lab(tl);
  const pw = panel(letter, cx0, 34, { alpha: ha });
  text(words, cx0 + pw + 8, 34, { size: 18, color: C.body, alpha: ha });
  const lx = cx0 + LBW, bx = lx + GAP, xs = [bx, bx + L1 * SC, bx + (L1 + L2) * SC];
  cs.rows.forEach((r, k) => {
    const y = ROW0 + k * DY, t0 = tl + .07 * k;
    const p = seg(t0, .3);
    line([[xs[0], y], [xs[2], y]], { color: C.ink, width: 1.8, progress: p });
    xs.forEach(x => { const a = p > 0 ? clamp((p - (x - xs[0]) / (xs[2] - xs[0])) * 8 + 1) : 0; if (a > 0) pin(x, y, { s: 12, alpha: a }); });
    const sa = lab(t0 + .2);
    if (sa > 0) { spiral(xs[1], y - 14, 8, sa); if (k === 0) math('k', xs[1] - 12, y - 17, { size: 17, align: 'right', alpha: sa }); }
    // each row on its own clock: its computed frequency over its round factor (printed under it)
    const q = Math.cos(2 * Math.PI * r.f / r.slow * (clock() - CP));
    const n = r.w1.length, pts = [], ghost = [[], []];
    const X1 = i => xs[0] + i / (n - 1) * L1 * SC, X2 = i => xs[1] + i / (n - 1) * L2 * SC;
    for (let i = 0; i < n; i++) { pts.push([X1(i), y - A * q * r.w1[i]]); ghost[0].push([X1(i), y - A * r.w1[i]]); ghost[1].push([X1(i), y + A * r.w1[i]]); }
    for (let i = 1; i < n; i++) { pts.push([X2(i), y - A * q * r.w2[i]]); ghost[0].push([X2(i), y - A * r.w2[i]]); ghost[1].push([X2(i), y + A * r.w2[i]]); }
    const ga = seg(t0 + .45, .3);
    if (ga > 0) for (const g of ghost) {            // the envelope; not over a span drawn magnified
      const keep = r.mag ? (r.dom === 0 ? g.slice(0, n) : g.slice(n - 1)) : g;
      line(keep, { color: C.mist, width: 1.1, alpha: ga });
    }
    // the other span alone, magnified, where it barely moves
    if (r.mag) {
      const w = r.dom === 0 ? r.w2 : r.w1, X = r.dom === 0 ? X2 : X1, ma = seg(t0 + .5, .3);
      if (ma > 0) {
        line(w.map((v, i) => [X(i), y - A * q * r.mag * v]), { color: C.sky, width: 1.5, dash: [4, 3], alpha: ma });
        const ly = y + 49;                              // under the factor: a dashed sample, the magnification
        const tw = text(`×${r.mag}`, lx, ly, { size: 16, color: C.body, align: 'right', alpha: ma });
        line([[lx - tw - 26, ly - 5], [lx - tw - 6, ly - 5]], { color: C.sky, width: 1.5, dash: [4, 3], alpha: ma });
      }
    }
    line(pts, { color: C.blue, width: 2.4, progress: seg(t0 + .12, .4) });
    // his frequency, its slowing, and the span that dominates, arriving
    const fa = lab(t0 + .08);
    if (fa > 0) {
      math(r.label.replace(' Hz', '\\,\\rm{Hz}'), lx - 8 * (1 - fa), y + 6, { size: 18, align: 'right', alpha: fa });
      text(`shown ${r.slow} × slower`, lx - 8 * (1 - fa), y + 28, { size: 15, color: C.muted, align: 'right', alpha: fa });
    }
    const da = lab(t0 + .55);
    if (da > 0) {
      const mx = (xs[r.dom] + xs[r.dom + 1]) / 2;
      text('Dominating span', mx, y - A - 12 + 6 * (1 - da), { size: 16, color: C.body, align: 'center', alpha: da });
    }
  });
  // the span lengths and the joint under the last row
  const yd = ROW0 + 3 * DY + 66, la = lab(tl + .7);
  if (la > 0) {
    dim(xs[0] + 2, xs[1] - 2, yd, `${L1.toFixed(1)}\\,\\rm{m}`, { alpha: la, size: 16 });
    dim(xs[1] + 2, xs[2] - 2, yd, `${L2.toFixed(1)}\\,\\rm{m}`, { alpha: la, size: 16 });
    const e = Math.floor(Math.log10(cs.k)), mant = (cs.k / Math.pow(10, e)).toFixed(1);
    math(`k = ${mant}\\ \\times\\ 10^{${e}}\\,\\rm{N}\\,\\rm{m/rad}`, xs[1], yd + 32 + 5 * (1 - la), { size: 17, align: 'center', alpha: la });
  }
}

function draw() {
  column('a', 18, 'a', 'similar span lengths', 0);
  column('b', 518, 'b', 'more different span lengths', .035);
  const fa = lab(.95);
  math('\\rm{girder}\\ EI = 1.0 \\times\\ 10^{11}\\,\\rm{N\\,m}^{2},\\ m = 10\\,\\rm{t/m},\\ \\rm{on three pins};\\ \\ ' +
       'k\\rm{: rotational spring; dashed: the other span, magnified}', 18, H - 14, { size: 15, color: C.muted, alpha: fa });
}
boot();
"""


# The still: 3 s, the intro over; every row's free vibration is phased to be at its
# extreme then (a free mode's phase is its initial condition's: each row keeps its
# own frequency and factor, only the moment of its extreme is chosen)
POSTER = 3.0
JS = JS.replace("__POSTER_T__", f"{POSTER:.3f}")
print(f"POSTER_T = {POSTER:.3f} s: every mode at its extreme")

TITLE = "Figure 7: Vibrational modes of multi span beams"
ARIA = ("Two columns of computed vibration modes of a two span beam on three pin supports whose spans "
        "are joined over the middle pin by a rotational spring, each mode oscillating in slow motion, "
        "slowed by the factor printed under its frequency: (a) spans of similar length, (b) spans of "
        "more different length. Each mode is labelled with its frequency, and the span with the larger "
        "amplitude is marked as the dominating span.")

if __name__ == "__main__":
    common.build_html(NAME, TITLE, ARIA, 1000, 656, DATA, JS)
    print(common.still(NAME))
