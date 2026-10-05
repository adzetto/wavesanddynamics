"""Figure 1 of the waves guide (and of the SHM guide): the lateral natural
dynamic response of a building and its analysis through the discretized
formulation.

A five storey shear building: rigid floors with lumped masses m1..m5 (floor 1
at the bottom), storeys of lateral stiffness k1..k5 (storey 1 at the ground),
M = diag(m), K tridiagonal (k1 + k2, -k2; ...; -k5, k5), exactly the matrices
under the figure. The eigenproblem K phi = w^2 M phi is solved (scipy.linalg.
eigh, mass-normalised modes). The building is set vibrating by a lateral
impulse at the roof, x(0) = 0, M x'(0) = [0, 0, 0, 0, m5 v0]: its undamped free
vibration is exactly x(t) = sum_j phi_j (phi_j^T M x'(0) / w_j) sin(w_j t), drawn
as the total and, term by term, as the 1st, the 2nd and the 3rd mode, each at
its own computed frequency; the 4th and 5th are named in words ("+ higher
modes", the professor's note of Oct 2026), and the total is still the sum of
all five. Columns take the exact shape of a fixed-fixed column between two
rigid floors (cubic).

The reader changes the building: three damage chips (undamaged, storey 3 or
storey 5 at 55 %) and five storey stiffness sliders (20 to 150 %); the page
solves the eigenproblem again (an exact Jacobi solver, checked against scipy
in tests/test_guide_interactions.py and in the check file) and compares the
roof displacement spectrum with the undamaged building's.

Layout (Oct 2026): landscape, 1000 x 730, so that a 16:9 full screen shows it
at about 1.3 px per unit; type 1.3 to 1.5 times the earlier sizes. Query
parameters preselect a state for the overlap check: ?case=1 (a chip) or
?k=20,150,100,100,100 (each storey in percent); without them nothing changes.

Run: python tools/numfig/building.py [--look]   (writes content/anim/
nf-building.html and .webp and tools/numfig/building.check.txt)
"""
import functools
import http.server
import itertools
import math as pymath
import os
import shutil
import sys
import tempfile
import threading

import numpy as np
import scipy.linalg as sla
from scipy.optimize import minimize

import common

NAME = "building"
HERE = os.path.dirname(os.path.abspath(__file__))

M_T = np.array([200.0, 200.0, 200.0, 200.0, 150.0])     # t, floor 1 (bottom) .. roof
K_MN = np.array([350.0, 330.0, 300.0, 260.0, 210.0])     # MN/m, storey 1 (ground) .. 5
H_S = 3.2                                                # m, storey height
ROOF_AMP = 1.5e-3                                        # m, 1st mode amplitude at the roof
SLOW = 5.0                                               # time slowed
DEF = 800.0                                              # displacements drawn x DEF
MAG = [1, 2, 4]                                          # 1st, 2nd, 3rd mode panels, relative
T0 = 0.45                                                # s, the impulse (motion from here)
HL0, HL_DT = 1.4, 1.8                                    # storey highlight: start, s per storey
LO, HI = 0.20, 1.50                                      # the sliders: fraction of each storey's k
DAMAGE = 0.55                                            # the two damage presets

# the drawing (units; W = 1000)
W_, H_ = 1000, 730
SH_U, BW_U = 36.0, 64.0                                  # storey height, building width
GAIN = DEF * SH_U / H_S                                  # units per metre of displacement
GY = 278.0                                               # the ground
OP_HALF = 13.0                                           # half the width of '=' and '+' at 34
LABEL_W, K_W = 28.5, 21.5                                # m_5 and k_5 at 22 units (measured)
HIGH_W = 100.0                                           # "higher modes" and f_4, f_5 at 16
MARGIN_L, MARGIN_R = 14.0, 16.0


def matrices(m, k):
    n = len(m)
    K = np.zeros((n, n))
    for s in range(n):            # storey s joins floor s - 1 (the ground for s = 0) and floor s
        K[s, s] += k[s]
        if s:
            K[s - 1, s - 1] += k[s]
            K[s - 1, s] -= k[s]
            K[s, s - 1] -= k[s]
    return np.diag(m), K


def modes(M, K):
    w2, Phi = sla.eigh(K, M)                 # mass-normalised: Phi^T M Phi = I
    Phi = Phi * np.sign(Phi[-1])             # roof positive
    return np.sqrt(w2), Phi


def roof_case(m, k, v0, factors):
    """Frequencies, mode shapes and modal amplitudes Q_j (m) of the building
    with storey stiffness k * factors, struck at the roof with velocity v0."""
    M, K = matrices(m, k * np.asarray(factors, float))
    w, P = modes(M, K)
    e = np.zeros(len(m)); e[-1] = 1.0
    return w, P, P.T @ M @ e / w * v0


def swings(m, k, v0):
    """The largest displacement each drawing can reach over the sliders' whole
    range (20 to 150 % of every storey's stiffness), in metres: the total
    (sum_j |Q_j phi_j(i)|, the bound the motion can at most reach) and each of
    the 1st, 2nd and 3rd modes (max_i |Q_j phi_j(i)|). Corners and a grid of
    the box, seeded random points, then a local search from the worst."""
    def amps(f):
        f = np.clip(f, LO, HI)
        _, P, Q = roof_case(m, k, v0, f)
        a = np.abs(P * Q)
        return np.array([a.sum(1).max(), a[:, 0].max(), a[:, 1].max(), a[:, 2].max()])

    pts = [np.array(c) for c in itertools.product([LO, 0.4, DAMAGE, 0.8, 1.0, HI], repeat=5)]
    pts += list(np.random.default_rng(1).uniform(LO, HI, (3000, 5)))
    vals = np.array([amps(p) for p in pts])
    worst, where = vals.max(0), [pts[i] for i in vals.argmax(0)]
    for q in range(4):            # refine each from its worst point (bounded by clipping)
        r = minimize(lambda f: -amps(f)[q], where[q], method="Nelder-Mead",
                     options=dict(xatol=1e-4, fatol=1e-12, maxiter=4000))
        f = np.clip(r.x, LO, HI)
        if amps(f)[q] > worst[q]:
            worst[q], where[q] = amps(f)[q], f
    return worst, where


def compute():
    m, k = M_T * 1e3, K_MN * 1e6
    M, K = matrices(m, k)
    w, Phi = modes(M, K)
    n = len(m)
    # the impulse at the roof: modal velocities phi_j^T M x'(0), amplitudes / w_j
    e = np.zeros(n); e[-1] = 1.0
    g = Phi.T @ M @ e / w                     # per unit roof velocity
    v0 = ROOF_AMP / abs(g[0] * Phi[-1, 0])
    Q = g * v0                                # q_j(t) = Q_j sin(w_j t), m
    R = dict(m=m, k=k, M=M, K=K, w=w, Phi=Phi, Q=Q, v0=v0)
    cases = []
    for label, factors in (("undamaged", np.ones(5)),
                           ("storey 3 damaged", np.array([1., 1., DAMAGE, 1., 1.])),
                           ("storey 5 damaged", np.array([1., 1., 1., 1., DAMAGE]))):
        wd, Pd, Qd = roof_case(m, k, v0, factors)
        cases.append({"label": label, "factor": factors.tolist(), "f": (wd / (2 * np.pi)).tolist(),
                      "w": wd.tolist(), "phi": Pd.T.tolist(), "Q": Qd.tolist()})
    R["cases"] = cases
    # checks
    R["res"] = max(np.linalg.norm(K @ Phi[:, j] - w[j] ** 2 * M @ Phi[:, j]) / np.linalg.norm(K @ Phi[:, j])
                   for j in range(n))
    R["orth"] = np.abs(Phi.T @ M @ Phi - np.eye(n)).max()
    R["kortho"] = np.abs(Phi.T @ K @ Phi - np.diag(w ** 2)).max() / w[-1] ** 2
    # uniform building against the closed form w_j = 2 sqrt(k/m) sin((2j - 1) pi / (2(2n + 1)))
    Mu, Ku = matrices(np.full(n, 200e3), np.full(n, 400e6))
    wu, _ = modes(Mu, Ku)
    wc = 2 * np.sqrt(400e6 / 200e3) * np.sin((2 * np.arange(1, n + 1) - 1) * np.pi / (2 * (2 * n + 1)))
    R["uniform"] = (wu, wc)
    # superposition against the exact state-space solution x(t) = expm(A t) [0; x'(0)]
    A = np.block([[np.zeros((n, n)), np.eye(n)], [-np.linalg.solve(M, K), np.zeros((n, n))]])
    z0 = np.concatenate([np.zeros(n), v0 * e])
    err = 0.0
    for tt in np.linspace(0.05, 3.0, 12):
        x_ex = (sla.expm(A * tt) @ z0)[:n]
        x_mod = Phi @ (Q * np.sin(w * tt))
        err = max(err, np.abs(x_ex - x_mod).max() / np.abs(x_ex).max())
    R["super"] = err
    # effective modal masses (base excitation): sum = total mass
    iota = np.ones(n)
    gam = Phi.T @ M @ iota
    R["meff"] = gam ** 2
    # Rayleigh quotient of the static roof-load shape (upper bound on w1)
    xs = np.linalg.solve(K, M @ iota)
    R["rayleigh"] = np.sqrt(xs @ K @ xs / (xs @ M @ xs))
    # the largest swing of each drawing over the sliders' range, for the layout's clearances
    R["swing"], R["swing_at"] = swings(m, k, v0)
    return R


def layout(R):
    """The modes row, left to right: the m labels, the total building, the k
    labels, '=', the 1st mode, '+', the 2nd, '+', the 3rd, '+', the higher modes
    in words. Each building is as wide as its largest possible swing (over every
    slider setting) and the space left is shared equally between them, so
    nothing in the row can meet at any setting. Returns the centres, the label
    offset from the total building's axis, the swings and the gap."""
    sw = R["swing"] * GAIN * np.array([1.0] + MAG)           # units: total, 1st, 2nd, 3rd
    half = BW_U / 2 + 3 + sw                                 # + the floor's 3 unit overhang
    widths = [LABEL_W, 2 * half[0], K_W, 2 * OP_HALF, 2 * half[1], 2 * OP_HALF, 2 * half[2],
              2 * OP_HALF, 2 * half[3], 2 * OP_HALF, HIGH_W]
    gap = (W_ - MARGIN_L - MARGIN_R - sum(widths)) / (len(widths) - 1)
    assert gap >= 8, f"the modes row is too tight: gap {gap:.1f}"
    x, centre = MARGIN_L, []
    for wd in widths:
        centre.append(x + wd / 2)
        x += wd + gap
    rnd = lambda v: round(float(v), 1)
    cx = [rnd(centre[i]) for i in (1, 4, 6, 8)]
    op = [rnd(centre[i]) for i in (3, 5, 7, 9)]
    return dict(cx=cx, op=op, hx=rnd(centre[10]), off=rnd(half[0] + gap), sw=sw, half=half, gap=gap)


def poster_time(R):
    """A moment in the storey 3 highlight where all four drawings are well
    away from zero (the printed frame shows each panel deformed)."""
    w, Q, Phi = R["w"], R["Q"], R["Phi"]
    best, tb = -1, None
    lo, hi = HL0 + 2 * HL_DT + 0.35, HL0 + 3 * HL_DT - 0.35
    bound = np.abs(Phi @ np.diag(Q)).sum(1).max()
    for t in np.linspace(lo, hi, 4000):
        s = np.sin(w * (t - T0) / SLOW)
        rel = [abs(s[j]) for j in range(3)]                   # each mode panel, of its own amplitude
        tot = np.abs(Phi @ (Q * s)).max() / bound
        score = min(rel + [tot * 1.6])
        if score > best:
            best, tb = score, t
    return float(round(tb, 3)), best


def check(R, tp, lay):
    L = []
    p = L.append
    w, Phi, Q = R["w"], R["Phi"], R["Q"]
    f = w / 2 / np.pi
    p("Figure 1 (nf-building): lateral natural vibration of a five storey shear building")
    p("(Figure 1 of the waves guide, and Figure 1 of the SHM guide)")
    p("")
    p("MODEL (floor 1 at the bottom, storey 1 at the ground; the matrices of the figure)")
    p("  m_1 .. m_5 = " + ", ".join(f"{x:.0f}" for x in M_T) + " t")
    p("  k_1 .. k_5 = " + ", ".join(f"{x:.0f}" for x in K_MN) + " MN/m, storey height "
      f"{H_S} m")
    p("  M = diag(m), K = [k1 + k2, -k2; -k2, k2 + k3, -k3; ...; -k5, k5]; C = 0 in the animation")
    p("  K (MN/m):")
    for row in R["K"] / 1e6:
        p("    " + "  ".join(f"{x:7.0f}" for x in row))
    p("")
    p("EIGENPROBLEM K phi = w^2 M phi (scipy.linalg.eigh, mass-normalised)")
    for j in range(5):
        p(f"  mode {j+1}: f = {f[j]:7.4f} Hz, T = {1/f[j]:.4f} s, phi (floor 1..5, roof = 1) = "
          + ", ".join(f"{x/Phi[-1, j]:+.4f}" for x in Phi[:, j]))
    p(f"  residual max |K phi - w^2 M phi| / |K phi| = {R['res']:.1e}")
    p(f"  orthogonality max |Phi^T M Phi - I| = {R['orth']:.1e}, max |Phi^T K Phi - W^2| / w5^2 = {R['kortho']:.1e}")
    wu, wc = R["uniform"]
    p("  CHECK 1: the same solver on a uniform building (m = 200 t, k = 400 MN/m) against the closed form")
    p("  w_j = 2 sqrt(k/m) sin((2j - 1) pi / 22):")
    p("    " + ", ".join(f"f_{j+1} {wu[j]/2/np.pi:.6f} Hz ({wu[j]/wc[j]-1:+.1e})" for j in range(5)))
    p(f"  CHECK 2: Rayleigh quotient of the static shape under floor inertia loads: f = {R['rayleigh']/2/np.pi:.4f} Hz"
      f" >= f_1 ({R['rayleigh']/w[0]-1:+.2e})")
    meff = R["meff"]
    p("  CHECK 3: effective modal masses (t): " + ", ".join(f"{x/1e3:.1f}" for x in meff)
      + f"; sum {meff.sum()/1e3:.3f} t = total mass {M_T.sum():.0f} t")
    p("  the damage presets (storey stiffness x 0.55), frequencies (Hz):")
    for c in R["cases"]:
        p(f"    {c['label']:17s} " + ", ".join(f"{v:.4f}" for v in c["f"]))
    p("")
    p("THE MOTION")
    p(f"  a lateral impulse at the roof, x(0) = 0, x'(0) = {R['v0']*1e3:.3f} mm/s at floor 5, chosen so that")
    p(f"  the 1st mode's roof amplitude is {ROOF_AMP*1e3:.1f} mm; q_j(t) = Q_j sin(w_j t),"
      " Q_j = phi_j^T M x'(0) / w_j")
    p("  roof amplitude of each term (mm): " + ", ".join(f"{abs(Q[j]*Phi[-1, j])*1e3:.4f}" for j in range(5)))
    p("  roof amplitude of each term, relative to the 1st: "
      + ", ".join(f"{abs(Q[j]*Phi[-1, j])/abs(Q[0]*Phi[-1, 0]):.3f}" for j in range(5)))
    hi = np.abs(Phi[:, 3:] * Q[3:]).sum(1).max() / np.abs(Phi * Q).sum(1).max()
    p(f"  the 4th and 5th modes together reach {hi*100:.1f} % of the total's bound: named in words, not drawn")
    p(f"  CHECK 4: the sum of the modal terms against the exact state-space solution expm(A t):"
      f" max relative error {R['super']:.1e}")
    p(f"  displacements drawn x {DEF:.0f} ({GAIN/1e3:.2f} units per mm; a storey is {SH_U:.0f} units for"
      f" {H_S} m); the 2nd mode panel x {MAG[1]} more and the 3rd x {MAG[2]} more (stated in the figure)")
    p(f"  time slowed {SLOW:.0f}: on screen f_1 = {f[0]/SLOW:.3f} Hz ... f_5 = {f[-1]/SLOW:.3f} Hz;"
      f" the impulse at t = {T0} s of the page's clock; a change by the reader strikes the changed")
    p("  building again from rest (while it plays)")
    p(f"  poster (printed frame) at t = {tp} s")
    p("")
    sw = lay["sw"]
    p("THE LAYOUT'S CLEARANCES (nothing can overlap at any slider setting)")
    p(f"  sliders {LO*100:.0f} to {HI*100:.0f} % of each storey's stiffness; the largest displacement each drawing can")
    p("  reach (6^5 grid incl. the corners, 3,000 seeded random points, Nelder-Mead from the worst):")
    names = ["total (sum of |Q_j phi_j|)", "1st mode", "2nd mode", "3rd mode"]
    for q in range(4):
        at = ", ".join(f"{v*100:.0f}" for v in R["swing_at"][q])
        p(f"    {names[q]:27s} {R['swing'][q]*1e3:.3f} mm -> {sw[q]:.1f} units drawn (storeys at {at} %)")
    p(f"  each drawing is placed as wide as its largest swing; the space left is shared equally, so a")
    p(f"  building at its largest swing keeps {lay['gap']:.1f} units from the sign or label beside it")
    p(f"  (axes at x = " + ", ".join(f"{v:g}" for v in lay["cx"]) + "; signs at " + ", ".join(f"{v:g}" for v in lay["op"])
      + f"; m_i and k_i {lay['off']:g} units from the total's axis)")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA, L = D.L;
const POSTER_T = D.poster;
const N = 5;
const lab = t0 => settle(t0, .28);         // a label arriving
const rise = s => 4 * (1 - s);             // ... settling 4 units into place

/* ---------------------------------------------------------------- layout */
const GY = L.gy, SH = L.sh, BW = L.bw;     // ground, storey height, building width
const CX = L.cx, OPX = L.op, HX = L.hx;    // total, 1st, 2nd, 3rd mode; '=', '+', '+', '+'; the words
const lev = i => GY - i * SH;              // floor i (0 = ground)
const G = D.gain;                          // drawing units per metre of displacement
const MM = {lx: 86, x0: 111, dx: 38}, KM = {lx: 356, x0: 400, dx: 76}, MY = {y0: 362, dy: 30, sz: 21};
const SP = {x: 92, y: 530, w: 653, h: 110, fmax: 15};          // the spectrum
const CH = {x: 768, y: 302, w: 216, h: 28, pitch: 36};          // the damage chips
const SL = {lx: 768, x0: 798, x1: 928, vx: 984, y0: 459, pitch: 36, r: 8};   // the sliders, storey 5 first
const slY = i => SL.y0 + (N - 1 - i) * SL.pitch;                // storey i + 1's slider

/* ---------------------------------------------------------------- the reader's building */
let CASE = D.cases[0];
let TSW = null;                            // when the reader last changed it while playing: struck again then
let CHG = [false, false, false, false, false];
const UI = {hc: -1, dc: -1, hs: -1, ds: -1};   // chip and slider under the pointer, pressed
(() => {                                   // ?case=1 or ?k=20,150,100,100,100 preselects a state
  const q = new URLSearchParams(location.search), c = q.get('case'), k = q.get('k');
  if (c !== null && D.cases[+c]) CASE = D.cases[+c];
  else if (k) {
    const f = k.split(',').map(v => clamp(Math.round(Number(v)) / 100, D.lo, D.hi));
    if (f.length === N && f.every(Number.isFinite)) CASE = byFactors(f);
  }
})();
function byFactors(f) {                    // a preset when the factors are one, else solved here
  const i = D.cases.findIndex(p => p.factor.every((v, j) => Math.abs(v - f[j]) < 1e-9));
  return i >= 0 ? D.cases[i] : solveStiffness(f);
}
const presetOf = c => D.cases.indexOf(c);
function reset() { TSW = null; }           // restart: the impulse comes again at t0

/* ---------------------------------------------------------------- the motion
   x_i(t) = sum_j Q_j phi_j(i) sin(w_j (t - t0) / SLOW), zero before the impulse */
function terms() {
  const tau = Math.max(0, t - (TSW === null ? D.t0 : TSW)) / D.slow;
  return CASE.Q.map((q, j) => q * Math.sin(CASE.w[j] * tau));
}
function disp(c, js, mag) {                // floor displacements (units) of the modes js
  const u = [0];
  for (let i = 0; i < N; i++) { let s = 0; for (const j of js) s += c[j] * CASE.phi[j][i]; u.push(s * G * mag); }
  return u;
}
function env(j) { return [0].concat(D.phi[j].map(v => Math.abs(D.Q[j]) * v * G * D.mag[j])); }
const ENV = [env(0), env(1), env(2)];      // the undamaged modal amplitudes, dashed

function solveStiffness(factors) {
  const k = D.k.map((v, i) => v * factors[i]), m = D.m;
  const K = Array.from({length:N}, () => Array(N).fill(0));
  for (let s=0;s<N;s++) { K[s][s]+=k[s]; if(s) { K[s-1][s-1]+=k[s]; K[s-1][s]-=k[s]; K[s][s-1]-=k[s]; } }
  const A = K.map((row,i)=>row.map((v,j)=>v/Math.sqrt(m[i]*m[j])));
  const V = Array.from({length:N},(_,i)=>Array.from({length:N},(_,j)=>+(i===j)));
  for (let it=0;it<150;it++) {
    let p=0,q=1,big=0;
    for(let i=0;i<N;i++) for(let j=i+1;j<N;j++) if(Math.abs(A[i][j])>big) {big=Math.abs(A[i][j]);p=i;q=j;}
    if(big<1e-11) break;
    const tau=(A[q][q]-A[p][p])/(2*A[p][q]), z=(tau>=0?1:-1)/(Math.abs(tau)+Math.sqrt(1+tau*tau));
    const c=1/Math.sqrt(1+z*z),s=z*c,ap=A[p][p],aq=A[q][q],pq=A[p][q];
    A[p][p]=ap-z*pq; A[q][q]=aq+z*pq; A[p][q]=A[q][p]=0;
    for(let i=0;i<N;i++) {
      if(i!==p&&i!==q) {const a=A[i][p],b=A[i][q]; A[i][p]=A[p][i]=c*a-s*b; A[i][q]=A[q][i]=s*a+c*b;}
      const a=V[i][p],b=V[i][q];V[i][p]=c*a-s*b;V[i][q]=s*a+c*b;
    }
  }
  const ids=Array.from({length:N},(_,i)=>i).sort((i,j)=>A[i][i]-A[j][j]);
  const w=ids.map(j=>Math.sqrt(A[j][j]));
  const phi=ids.map(j=>V.map((row,i)=>row[j]/Math.sqrt(m[i])*(V[N-1][j]<0?-1:1)));
  return {label:'custom stiffness',factor:[...factors],w,f:w.map(v=>v/(2*Math.PI)),phi,
          Q:phi.map((v,j)=>v[N-1]*m[N-1]*D.v0/w[j])};
}

// FFT of the exact undamped roof displacement over 32 physical seconds.
function fftSpectrum(model) {
  const n=2048, fs=64, re=new Float64Array(n), im=new Float64Array(n); let ws=0;
  for(let i=0;i<n;i++) {
    const window=.5-.5*Math.cos(2*Math.PI*i/(n-1)); ws+=window;
    re[i]=1000*window*model.w.reduce((a,w,j)=>a+model.Q[j]*model.phi[j][N-1]*Math.sin(w*i/fs),0);
  }
  for(let i=1,j=0;i<n;i++) {
    let b=n>>1; for(;j&b;b>>=1) j^=b; j^=b;
    if(i<j) {const a=re[i];re[i]=re[j];re[j]=a;}
  }
  for(let len=2;len<=n;len*=2) for(let start=0;start<n;start+=len) {
    for(let j=0;j<len/2;j++) {
      const a=-2*Math.PI*j/len,c=Math.cos(a),s=Math.sin(a),r=start+j,v=r+len/2;
      const tr=c*re[v]-s*im[v],ti=s*re[v]+c*im[v];
      re[v]=re[r]-tr;im[v]=im[r]-ti;re[r]+=tr;im[r]+=ti;
    }
  }
  return Array.from({length:n/2+1},(_,i)=>[i*fs/n,Math.hypot(re[i],im[i])*(i===0||i===n/2?1:2)/ws]);
}

/* ---------------------------------------------------------------- drawing */
function column(cx, x0, u, s, o) {         // the column of storey s: fixed-fixed, cubic
  const pts = [];
  for (let q = 0; q <= 14; q++) {
    const e = q / 14, h = 3 * e * e - 2 * e * e * e;
    pts.push([cx + x0 + u[s - 1] + (u[s] - u[s - 1]) * h, lev(s - 1) - SH * e]);
  }
  line(pts, o);
}
/* a building: its changed storeys' columns in crimson (the stiffness the reader
   changed), and in the total the storey of the highlight */
function building(cx, u, o = {}) {
  const {color = C.blue, width = 1.8, dash = null, alpha = 1, progress = 1, thin = false, hl = 0, hs = 0} = o;
  const pr = progress * N;
  for (let s = 1; s <= N; s++) {
    const ps = clamp(pr - (s - 1));
    if (ps <= 0) break;
    const mark = !thin && CHG[s - 1];
    for (const x0 of [-BW / 2, BW / 2]) {
      column(cx, x0, u, s, {color: mark ? C.accent : color, width: mark ? width + .4 : width, dash, alpha, progress: ps});
      if (hl > 0 && s === hs) column(cx, x0, u, s, {color: C.accent, width: width + .4, alpha: alpha * hl, progress: ps});
    }
    if (ps >= 1 && !thin)                  // a rigid floor
      line([[cx - BW / 2 + u[s] - 3, lev(s)], [cx + BW / 2 + u[s] + 3, lev(s)]], {color: C.navy, width: 3, alpha});
    else if (ps >= 1)
      line([[cx - BW / 2 + u[s], lev(s)], [cx + BW / 2 + u[s], lev(s)]], {color, width, dash, alpha});
  }
}
function ground(x0, x1, y, progress, alpha) {
  line([[x0, y], [x1, y]], {width: 2.2, progress, alpha});
  if (progress < 1) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.strokeStyle = C.ink; ctx.lineWidth = 1; ctx.beginPath();
  for (let x = x0 + 4; x < x1; x += 8) { ctx.moveTo(x, y); ctx.lineTo(x - 6, y + 7); }
  ctx.stroke(); ctx.restore();
}
function xdots(x, y, n, sz, alpha) {       // an italic x with n dots over it; returns its width
  const w = math('x', x, y, {size: sz, alpha});
  const cx = x + w * .5 + sz * .07, cy = y - sz * .66;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.fillStyle = C.ink;
  for (let k = 0; k < n; k++) { ctx.beginPath(); ctx.arc(cx + (k - (n - 1) / 2) * sz * .2, cy, sz * .05, 0, 2 * Math.PI); ctx.fill(); }
  ctx.restore();
  return w;
}
function equation(x, y, alpha) {           // M x'' + C x' + K x = 0 from x; returns where it ends
  const sz = 26, parts = [['M'], [2], [' + C'], [1], [' + Kx = 0']];
  // an italic capital's box reaches over the next letter: a little room after M and C
  let cx = x;
  for (const p of parts) cx += (typeof p[0] === 'number' ? xdots(cx, y, p[0], sz, alpha) : math(p[0], cx, y, {size: sz, alpha})) + 3;
  return cx;
}

/* the matrices: entries as terms, each tied to its storey (k) or floor (m) */
const MENT = Array.from({length: N}, (_, i) => Array.from({length: N}, (_, j) => i === j ? [['m', i + 1, '']] : [['0']]));
const KENT = Array.from({length: N}, (_, i) => Array.from({length: N}, (_, j) => {
  if (i === j) return i < N - 1 ? [['k', i + 1, ''], ['k', i + 2, ' + ']] : [['k', i + 1, '']];
  if (Math.abs(i - j) === 1) return [['k', Math.max(i, j) + 1, '-']];
  return [['0']];
}));
/* an entry centred at x; the terms of a marked storey or floor (mk[index] = strength) in crimson */
function entry(terms, x, y, sz, kind, mk, alpha) {
  const str = tm => tm[0] === '0' ? '0' : tm[2] + tm[0] + '_{' + tm[1] + '}';
  const w = terms.reduce((s, tm) => s + math(str(tm), 0, -1e4, {size: sz, alpha: 0}), 0);
  let cx = x - w / 2;
  for (const tm of terms) {
    const a = tm[0] === kind ? (mk[tm[1]] || 0) : 0;
    const ww = math(str(tm), cx, y, {size: sz, alpha, color: a >= 1 ? C.accent : C.ink});
    if (a > 0 && a < 1) math(str(tm), cx, y, {size: sz, color: C.accent, alpha: alpha * a});
    cx += ww;
  }
}
function matrix(name, P, ents, kind, mk, alpha, bp) {
  const {y0, dy, sz} = MY, {x0, dx} = P;
  math(name + ' =', P.lx, y0 + 2 * dy + 8, {size: 24, align: 'right', alpha});
  // the block each marked storey (or floor) assembles into
  for (const key in mk) {
    const s = +key, a = mk[key];
    if (!(a > 0)) continue;
    const r = kind === 'k' ? [Math.max(0, s - 2), s - 1] : [s - 1, s - 1];
    const xa = x0 + r[0] * dx - dx / 2 + 5, xb = x0 + r[1] * dx + dx / 2 - 5;
    const ya = y0 + r[0] * dy - 22, yb = y0 + r[1] * dy + 9;
    ctx.save(); ctx.globalAlpha *= a * alpha; ctx.fillStyle = C.wash; ctx.fillRect(xa, ya, xb - xa, yb - ya); ctx.restore();
  }
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++)
    entry(ents[i][j], x0 + j * dx, y0 + i * dy, sz, kind, mk, alpha);
  const left = x0 - dx / 2 + 2, right = x0 + 4 * dx + dx / 2 - 2, top = y0 - 24, bot = y0 + 4 * dy + 12;
  for (const [x, s] of [[left, 1], [right, -1]])
    line([[x + 8 * s, top], [x, top], [x, bot], [x + 8 * s, bot]], {width: 1.4, progress: bp});
}
function yScale(v) {                       // a top and ticks for the amplitude axis
  for (const s of [.25, .5, 1, 2, 5]) {
    const top = Math.ceil(v * 1.06 / s) * s;
    if (top / s <= 4) return {top, ticks: Array.from({length: Math.round(top / s) + 1}, (_, i) => +(i * s).toFixed(2))};
  }
  return {top: v, ticks: [0, v]};
}
function spectrum(alpha) {
  const P = SP;
  text('roof displacement spectrum', P.x, P.y - 14, {size: 20, color: C.body, alpha});
  // the key, a row over the plot as the family sets one
  const ky = P.y - 20, kx = P.x + P.w;
  const ws = text('selected', 0, -1e4, {size: 17, alpha: 0}), wu = text('undamaged', 0, -1e4, {size: 17, alpha: 0});
  line([[kx - ws - 38, ky], [kx - ws - 8, ky]], {color: C.blue, width: 2.2, alpha});
  text('selected', kx, ky + 6, {size: 17, align: 'right', alpha});
  const ux = kx - ws - 62;
  line([[ux - wu - 38, ky], [ux - wu - 8, ky]], {color: C.guide, width: 1.8, dash: [5, 4], alpha});
  text('undamaged', ux, ky + 6, {size: 17, align: 'right', color: C.body, alpha});
  const lim = s => s.filter(p => p[0] <= P.fmax);
  const top = Math.max(...lim(BASE_SPEC).map(p => p[1]), ...lim(CASE.spectrum).map(p => p[1]));
  const Y = yScale(top);
  const A = axes({x: P.x, y: P.y, w: P.w, h: P.h, xlim: [0, P.fmax], ylim: [0, Y.top],
    xticks: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], yticks: Y.ticks, tickSize: 18, labelSize: 20,
    xlabel: '\\rm{frequency}\\ (\\rm{Hz})', ylabel: '\\rm{amplitude}\\ (\\rm{mm})', ylabelGap: 50,
    progress: seg(.6, .35)});
  const cp = seg(.75, .45);
  A.inside(() => {
    line(lim(BASE_SPEC).map(p => [A.X(p[0]), A.Y(p[1])]), {color: C.guide, width: 1.8, dash: [5, 4], progress: cp});
    line(lim(CASE.spectrum).map(p => [A.X(p[0]), A.Y(p[1])]), {color: C.blue, width: 2.2, progress: cp});
  });
}
/* the controls, in the figure's own terms: uiChip's look (engine.js) with its
   type at 17, and a slider as the family draws one (a 3 unit C.rule track, a
   white handle with a 2 unit ring); the keyboard's stand-ins lie over them */
function chip(x, y, w, h, label, st, a) {
  const fill = st.on ? C.navy : st.down ? C.steel2 : st.hover ? C.steel : '#fff';
  const edge = st.on || st.hover || st.down ? C.navy : C.guide;
  line([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], {color: edge, width: 1, fill, close: true, alpha: a});
  text(label, x + w / 2, y + h / 2 + 6, {size: 18, align: 'center', alpha: a,
    color: st.on ? '#fff' : st.hover ? C.ink : C.body});
}
const kNow = i => (D.k[i] * CASE.factor[i] / 1e6).toFixed(1);
function sliders(a) {
  text('storey stiffness (MN/m)', SL.lx, SL.y0 - 27, {size: 19, color: C.body, alpha: a});
  const x0 = SL.x0 + SL.r, x1 = SL.x1 - SL.r, X = f => x0 + (f - D.lo) / (D.hi - D.lo) * (x1 - x0);
  for (let i = 0; i < N; i++) {
    const y = slY(i), f = CASE.factor[i], col = CHG[i] ? C.accent : C.navy;
    line([[x0, y], [x1, y]], {color: C.rule, width: 3, alpha: a});
    line([[X(1), y - 7], [X(1), y + 7]], {color: C.guide, width: 1, alpha: a});   // the undamaged storey
    line([[x0, y], [X(f), y]], {color: col, width: 3, alpha: a});
    const big = UI.hs === i || UI.ds === i;
    dot(X(f), y, SL.r * (big ? 1.15 : 1), {color: col, fill: UI.ds === i ? C.steel : '#fff', width: 2, alpha: a});
    math('k_{' + (i + 1) + '}', SL.lx, y + 7, {size: 21, color: CHG[i] ? C.accent : C.ink, alpha: a});
    text(kNow(i), SL.vx, y + 6, {size: 18, align: 'right', color: CHG[i] ? C.accent : C.ink, alpha: a});
  }
}

/* ---------------------------------------------------------------- draw */
function draw() {
  CHG = CASE.factor.map(f => Math.abs(f - 1) > 4e-3);
  const changed = CHG.some(Boolean);
  const c = terms();
  const tot = disp(c, [0, 1, 2, 3, 4], 1), md = [0, 1, 2].map(j => disp(c, [j], D.mag[j]));
  const zero = [0, 0, 0, 0, 0, 0];
  // the storey highlight, one storey at a time, while the building is the undamaged one;
  // a changed building shows its changed storeys instead
  let hs = 0, hl = 0;
  if (!changed && t >= D.hl0) {
    const k_ = Math.floor((t - D.hl0) / D.hldt), ph = (t - D.hl0 - k_ * D.hldt) / D.hldt;
    hs = ((k_ % N) + N) % N + 1; hl = Math.min(1, ph / .15, (1 - ph) / .15);
  }

  // titles and frequencies
  const tt = [lab(.08), lab(.12), lab(.16), lab(.20)];
  text('Total vibration', CX[0], 31 + rise(tt[0]), {size: 22, color: C.body, align: 'center', alpha: tt[0]});
  text('of the building', CX[0], 58 + rise(tt[0]), {size: 22, color: C.body, align: 'center', alpha: tt[0]});
  ['1st mode', '2nd mode', '3rd mode'].forEach((s, j) => {
    text(s, CX[j + 1], 31 + rise(tt[j + 1]), {size: 22, color: C.body, align: 'center', alpha: tt[j + 1]});
    const fa = lab(.30 + .04 * j);
    math('f_{' + (j + 1) + '} = ' + CASE.f[j].toFixed(2) + '\\ \\rm{Hz}', CX[j + 1], 58 + rise(fa), {size: 21, align: 'center', alpha: fa});
    if (D.mag[j] > 1) text('× ' + D.mag[j], CX[j + 1], 82 + rise(fa), {size: 16, color: C.muted, align: 'center', alpha: fa});
  });
  text(D.slowtxt, W - 10, 22, {size: 16, color: C.muted, align: 'right', alpha: lab(.8)});

  // ground and buildings
  ground(L.g0, L.g1, GY, seg(0, .30), 1);
  const bp = [0, 1, 2, 3].map(p => seg(.05 + .05 * p, .35));
  // the undeformed frame behind the total, the undamaged modal amplitudes behind the modes
  building(CX[0], zero, {color: C.rule, width: 1, progress: bp[0], thin: true});
  for (let j = 0; j < 3; j++) for (const sg of [1, -1])
    building(CX[j + 1], ENV[j].map(v => sg * v), {color: C.guide, width: 1, dash: [4, 3], progress: bp[j + 1], alpha: .9, thin: true});
  building(CX[0], tot, {progress: bp[0], hl, hs});
  for (let j = 0; j < 3; j++) building(CX[j + 1], md[j], {progress: bp[j + 1]});
  // the lumped masses on the total building, and the labels of floors and storeys
  for (let i = 1; i <= N; i++) {
    const ms = settle(.30 + .03 * i, .28);
    if (ms <= 0) continue;
    const x = CX[0] + tot[i], y = lev(i), on = hl > 0 && hs === i;
    dot(x, y, 9.5 * (.5 + .5 * ms), {color: C.ink, fill: C.steel, width: 1.2, alpha: ms});
    if (on) dot(x, y, 9.5, {color: C.accent, fill: C.wash, width: 1.8, alpha: hl});
    math('m_{' + i + '}', CX[0] - L.off, y + 7, {size: 22, align: 'right', alpha: ms});
    if (on) math('m_{' + i + '}', CX[0] - L.off, y + 7, {size: 22, align: 'right', color: C.accent, alpha: hl});
    const ky = lev(i - 1) - SH / 2 + 7;
    math('k_{' + i + '}', CX[0] + L.off, ky, {size: 22, color: CHG[i - 1] ? C.accent : C.ink, alpha: ms});
    if (on) math('k_{' + i + '}', CX[0] + L.off, ky, {size: 22, color: C.accent, alpha: hl});
  }
  // =, +, and the higher modes in words
  const oa = lab(.35), oy = lev(2.5) + 12;
  text('=', OPX[0], oy + rise(oa), {size: 34, align: 'center', alpha: oa});
  for (let j = 1; j < 4; j++) text('+', OPX[j], oy + rise(oa), {size: 34, align: 'center', alpha: oa});
  const ha = lab(.40);
  text('higher', HX, oy - 10 + rise(ha), {size: 22, color: C.body, align: 'center', alpha: ha});
  text('modes', HX, oy + 15 + rise(ha), {size: 22, color: C.body, align: 'center', alpha: ha});
  for (let j = 3; j < 5; j++)
    math('f_{' + (j + 1) + '} = ' + CASE.f[j].toFixed(2) + '\\ \\rm{Hz}', HX, oy + 48 + 22 * (j - 3) + rise(ha), {size: 16, color: C.body, align: 'center', alpha: ha});

  // the equation of motion, the eigenproblem, and the matrices
  const ea = lab(.45), ga = lab(.50);
  const ex = equation(MM.lx - 50, 322 + rise(ea), ea);
  const nx = ex + 40, nw = text('natural modes', nx, 322 + rise(ga), {size: 19, color: C.body, alpha: ga});
  math('(K - ω^{2}M)φ = 0', nx + nw + 14, 322 + rise(ga), {size: 24, alpha: ga});
  const mm = {}, km = {};
  if (hl > 0) { mm[hs] = hl; km[hs] = hl; }
  CHG.forEach((v, i) => { if (v) km[i + 1] = 1; });
  const bpm = seg(.5, .30);
  matrix('M', MM, MENT, 'm', mm, lab(.55), bpm);
  matrix('K', KM, KENT, 'k', km, lab(.60), bpm);
  spectrum(lab(.62));

  // the reader's controls: damage chips and storey sliders
  const ca = lab(.66), on = presetOf(CASE);
  D.cases.forEach((cs, i) => chip(CH.x, CH.y + i * CH.pitch, CH.w, CH.h, cs.label,
    {on: i === on, hover: UI.hc === i, down: UI.dc === i}, ca));
  sliders(lab(.70));

  // parameters
  text(D.params, 18, H - 10, {size: 15, color: C.muted, alpha: lab(.80)});
}
const BASE_SPEC=fftSpectrum(D.cases[0]);
D.cases.forEach(c=>c.spectrum=fftSpectrum(c));
if (!CASE.spectrum) CASE.spectrum = fftSpectrum(CASE);

/* ---------------------------------------------------------------- the reader's hand
   chips: a radio group (arrows move and choose); sliders: range inputs, their
   look drawn on the canvas under them. A change re-solves the eigenproblem; while
   the figure plays, the same impulse strikes the changed building again. A click
   on a control, or just beside one, never pauses the figure. */
const FIG = document.querySelector('.fig'), KB = {chips: [], sl: [], said: null};
function syncUI() {
  const on = presetOf(CASE);
  KB.chips.forEach((b, i) => { b.setAttribute('aria-checked', String(i === on)); b.tabIndex = i === Math.max(0, on) ? 0 : -1; });
  KB.sl.forEach((s, i) => {
    s.value = String(Math.round(CASE.factor[i] * 100));
    s.setAttribute('aria-valuetext', kNow(i) + ' MN/m, ' + Math.round(CASE.factor[i] * 100) + ' percent of the undamaged storey');
  });
  if (KB.said) KB.said.textContent = 'Natural frequencies ' + CASE.f.map(v => v.toFixed(2)).join(', ') + ' Hz';
}
function setCase(c) {
  CASE = c;
  if (!CASE.spectrum) CASE.spectrum = fftSpectrum(CASE);
  if (playing) TSW = t;
  syncUI();
  if (!playing) render();
}
if (!STILL) {
  const css = document.createElement('style');
  css.textContent = '.nfc{position:absolute;box-sizing:border-box;margin:0;padding:0;border:0;background:transparent;color:transparent;' +
    'cursor:pointer;font:inherit;overflow:hidden;-webkit-tap-highlight-color:transparent}.nfc:focus{outline:none}' +
    '.nfc::after{content:"";position:absolute;left:0;right:0;top:11.1%;bottom:11.1%}' +
    '.nfc:focus-visible::after{outline:2px solid #095A94;outline-offset:1px}' +
    '.nfr{position:absolute;box-sizing:border-box;-webkit-appearance:none;appearance:none;background:transparent;margin:0;padding:0;' +
    'cursor:pointer;-webkit-tap-highlight-color:transparent}' +
    '.nfr::-webkit-slider-runnable-track{background:transparent;border:0;height:100%}' +
    '.nfr::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:var(--th);height:100%;background:transparent;border:0}' +
    '.nfr::-moz-range-track{background:transparent;border:0}' +
    '.nfr::-moz-range-thumb{width:var(--th);height:100%;background:transparent;border:0;border-radius:0}' +
    '.nfr:focus{outline:none}.nfr:focus-visible{outline:2px solid #095A94;outline-offset:0}';
  document.head.appendChild(css);
  const ctl = FIG.querySelector('.ctl'), pct = (v, of) => (v / of * 100) + '%';
  const group = document.createElement('div');
  group.setAttribute('role', 'radiogroup'); group.setAttribute('aria-label', 'Damage case');
  FIG.insertBefore(group, ctl);
  const names = ['Undamaged building', 'Storey 3 damaged, 55 percent of its stiffness', 'Storey 5 damaged, 55 percent of its stiffness'];
  D.cases.forEach((cs, i) => {
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'nfc'; b.setAttribute('role', 'radio'); b.textContent = cs.label;
    b.setAttribute('aria-label', names[i] || cs.label);
    const y = CH.y + i * CH.pitch - (CH.pitch - CH.h) / 2;
    b.style.left = pct(CH.x, W); b.style.width = pct(CH.w, W); b.style.top = pct(y, H); b.style.height = pct(CH.pitch, H);
    b.addEventListener('click', e => { e.stopPropagation(); setCase(D.cases[i]); });
    b.addEventListener('keydown', e => {
      const d = {ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1}[e.key], n = D.cases.length;
      const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : d ? (i + d + n) % n : -1;
      if (j < 0) return;
      e.preventDefault(); KB.chips[j].focus(); setCase(D.cases[j]);
    });
    const hover = (h, d) => () => { UI.hc = h; UI.dc = d; if (!playing) render(); };
    b.addEventListener('pointerenter', hover(i, -1)); b.addEventListener('pointerleave', hover(-1, -1));
    b.addEventListener('pointerdown', hover(i, i)); b.addEventListener('pointerup', hover(i, -1));
    group.appendChild(b); KB.chips.push(b);
  });
  KB.sl = Array(N);
  for (let i = N - 1; i >= 0; i--) {         // top down, as they read: storey 5 first
    const s = document.createElement('input');
    s.type = 'range'; s.className = 'nfr'; s.min = String(Math.round(D.lo * 100)); s.max = String(Math.round(D.hi * 100)); s.step = '1';
    s.setAttribute('aria-label', `Storey ${i + 1} stiffness, percent of the undamaged storey`);
    s.style.left = pct(SL.x0, W); s.style.width = pct(SL.x1 - SL.x0, W);
    s.style.top = pct(slY(i) - SL.pitch / 2, H); s.style.height = pct(SL.pitch, H);
    s.addEventListener('input', () => { const f = [...CASE.factor]; f[i] = Number(s.value) / 100; setCase(byFactors(f)); });
    s.addEventListener('click', e => e.stopPropagation());
    const hover = (h, d) => () => { UI.hs = h; UI.ds = d; if (!playing) render(); };
    s.addEventListener('pointerenter', hover(i, -1)); s.addEventListener('pointerleave', hover(-1, -1));
    s.addEventListener('pointerdown', hover(i, i)); s.addEventListener('pointerup', hover(i, -1));
    FIG.insertBefore(s, ctl); KB.sl[i] = s;
  }
  // the native thumb as wide as the drawn handle: its centre is then where the handle is drawn
  new ResizeObserver(() => {
    const u = cv.getBoundingClientRect().width / W;
    KB.sl.forEach(s => s.style.setProperty('--th', (2 * SL.r * u).toFixed(2) + 'px'));
  }).observe(cv);
  KB.said = document.createElement('div'); KB.said.setAttribute('role', 'status');
  KB.said.style.cssText = 'position:absolute;left:0;top:0;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap;pointer-events:none';
  FIG.appendChild(KB.said);
  // a click just beside the controls is meant for them: it never pauses
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const r = cv.getBoundingClientRect(), X = (e.clientX - r.left) * W / r.width, Y = (e.clientY - r.top) * H / r.height;
    if (X > CH.x - 14 && Y > CH.y - 12 && Y < slY(0) + SL.pitch / 2 + 8) e.stopPropagation();
  }, true);
  syncUI();
}
boot();
"""


# ------------------------------------------------------------------ in the browser
def _serve():
    tmp = tempfile.mkdtemp(prefix="numfig-")
    os.makedirs(os.path.join(tmp, "anim"))
    shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
    shutil.copy(os.path.join(common.ANIM, f"nf-{NAME}.html"), os.path.join(tmp, "anim"))
    srv = common._server(tmp)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return tmp, srv


def overlaps_at(query, times, width=672):
    """common.overlaps() with a query string (a chip or slider state): the
    collisions at the poster and at each moment in `times`."""
    from playwright.sync_api import sync_playwright
    tmp, srv = _serve()
    out = {}
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?still&overlap&{query}")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            pg.wait_for_timeout(150)
            for s in [None] + list(times):
                if s is not None:
                    pg.evaluate(f"() => {{ t = {s:.6g}; render(); }}")
                lab, cro = pg.evaluate("[window.__overlaps || [], window.__crossings || []]")
                out["still" if s is None else f"t={s:g}"] = {"labels": lab, "crossings": cro}
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def browser_checks(R):
    """The page's own eigensolver and spectrum (the code the reader's changes
    run) against scipy, at the presets and the sliders' extremes; and the
    page's motion against this model at the poster."""
    from playwright.sync_api import sync_playwright
    combos = [[1.0] * 5, [LO] * 5, [HI] * 5] + [list(np.where(np.arange(5) == i, v, 1.0))
                                                 for i in range(5) for v in (LO, HI)]
    combos += [list(R["swing_at"][q]) for q in range(4)]
    tmp, srv = _serve()
    worst = dict(w=0.0, Q=0.0, spec=0.0, disp=0.0)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{NAME}.html?still")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            got = pg.evaluate("(fs) => fs.map(f => { const s = solveStiffness(f); "
                              "return {w: s.w, Q: s.Q, phi: s.phi, sp: fftSpectrum(s).map(p => p[1])}; })", combos)
            for f, g in zip(combos, got):
                w, P, Q = roof_case(R["m"], R["k"], R["v0"], f)
                worst["w"] = max(worst["w"], float(np.abs(np.array(g["w"]) / w - 1).max()))
                Pg = np.array(g["phi"]).T
                Qg = np.array(g["Q"])
                worst["Q"] = max(worst["Q"], float(np.abs(Pg * Qg - P * Q).max() / np.abs(P * Q).max()))
                tt = np.arange(2048) / 64
                roof = 1000 * ((Q * P[-1])[:, None] * np.sin(w[:, None] * tt)).sum(0)
                win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(2048) / 2047)
                amp = np.abs(np.fft.rfft(roof * win)) * 2 / win.sum()
                amp[[0, -1]] *= 0.5
                worst["spec"] = max(worst["spec"], float(np.abs(np.array(g["sp"]) - amp).max() / amp.max()))
            # the drawn floors at the poster: the page's disp() against this model
            tp = R["tp"]
            u = pg.evaluate(f"() => {{ t = {tp}; const c = terms(); return disp(c, [0,1,2,3,4], 1).slice(1); }}")
            s = np.sin(R["w"] * (tp - T0) / SLOW)
            ref = (R["Phi"] @ (R["Q"] * s)) * GAIN
            worst["disp"] = float(np.abs(np.array(u) - ref).max())
            b.close()
    finally:
        srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)
    return worst, len(combos)


def main():
    R = compute()
    tp, score = poster_time(R)
    R["tp"] = tp
    lay = layout(R)
    w, Phi, Q = R["w"], R["Phi"], R["Q"]
    f = w / 2 / np.pi
    data = {
        "poster": tp, "t0": T0, "slow": SLOW, "hl0": HL0, "hldt": HL_DT,
        "w": w.tolist(), "f": f.tolist(), "Q": Q.tolist(), "phi": Phi.T.tolist(),
        "gain": GAIN, "mag": MAG, "lo": LO, "hi": HI,
        "L": {"gy": GY, "sh": SH_U, "bw": BW_U, "cx": lay["cx"], "op": lay["op"], "hx": lay["hx"],
              "off": lay["off"], "g0": 24.0, "g1": lay["op"][3] - OP_HALF},
        "params": ("floors 200, 200, 200, 200, 150 t; storeys 350, 330, 300, 260, 210 MN/m, 3.2 m high; "
                   f"impulse at the roof, C = 0; displacements × {DEF:.0f}"),
        "slowtxt": f"time slowed {SLOW:.0f} ×",
        "cases": R["cases"],
        "m": R["m"].tolist(), "k": R["k"].tolist(), "v0": R["v0"],
    }
    title = ("Figure 1: Lateral natural dynamic response of a building and its analysis through "
             "discretized formulation")
    aria = ("A five storey building struck at the roof vibrates freely; its total motion is drawn as the "
            "exact sum of its 1st, 2nd and 3rd modes and the higher modes, each vibrating at its own computed "
            "natural frequency. Below, the equation of motion with the mass and stiffness matrices, whose "
            "entries light up storey by storey, and the roof displacement spectrum.")
    aria += (" Choose a damage case or change any storey stiffness to recompute the natural modes and compare "
             "the spectrum with the undamaged building.")
    # twelve places: the mass-normalised shapes are of order 1e-3, and five places (the default)
    # would leave them two or three digits
    common.build_html(NAME, title, aria, W_, H_, data, JS, digits=12)
    txt = check(R, tp, lay)
    print(txt)
    print("poster score", round(score, 3))
    # the poster, and the overlap check at the poster and every 0.25 s up to it
    print("still:", common.still(NAME))
    # every state: the chips, each slider at both ends, all at both ends, the worst swings
    times = [0.3, 0.6, 0.9, 1.4, 2.2, 3.1, 4.7, 6.4, 8.8, 11.5, 17.3, 23.9]
    states = ["case=0", "case=1", "case=2", "k=" + ",".join(["20"] * 5), "k=" + ",".join(["150"] * 5)]
    for i in range(5):
        for v in (20, 150):
            states.append("k=" + ",".join(str(v) if j == i else "100" for j in range(5)))
    for q in range(4):
        states.append("k=" + ",".join(str(int(round(v * 100))) for v in R["swing_at"][q]))
    bad = []
    for qs in states:
        res = overlaps_at(qs, times)
        for when, r in res.items():
            if r["labels"] or r["crossings"]:
                bad.append((qs, when, r))
    for b in bad:
        print("COLLISION", b)
    worst, ncombo = browser_checks(R)
    txt += "\n".join([
        "",
        "THE PAGE'S OWN NUMBERS (evaluated in the browser, Playwright)",
        f"  the page's Jacobi eigensolver against scipy.linalg.eigh at {ncombo} stiffness settings (the presets'",
        "  storeys, each slider at both ends, all at both ends, the worst swings): largest relative difference",
        f"  of the frequencies {worst['w']:.1e}, of the modal terms Q_j phi_j {worst['Q']:.1e}",
        f"  its 2048 point FFT spectrum against numpy.fft.rfft of the same record: {worst['spec']:.1e} of the peak",
        f"  the drawn floors at the poster against this model: largest difference {worst['disp']:.1e} units",
        "",
        "OVERLAP (engine.js ?overlap)",
        "  common.still(): at the poster and every 0.25 s up to the poster time: no label meets a label,",
        "  no stroke crosses a label (the still would not have been written otherwise); nothing is allowed",
        f"  every state through the page's query (?case=0, 1, 2; ?k= each slider at 20 and 150 %, all at 20 and",
        f"  150 %, the four worst swings: {len(states)} states), at the poster and at "
        + ", ".join(f"{x:g}" for x in times) + " s:",
        "  " + ("nothing collides" if not bad else f"{len(bad)} moments collide"),
    ]) + "\n"
    with open(os.path.join(HERE, f"{NAME}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt[-1500:])
    if bad:
        raise SystemExit("collisions in some state")
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.6, 0.9, 1.4, 3.0, 6.0]))


if __name__ == "__main__":
    main()
