"""Figure 10 of the signal processing document: blind source separation,
method 1, kurtosis ICA (his page "Blind source separation, method 1: kurtosis
ICA", redrawn on the shared model of sp_bss_lib).

Two sensors on a structure record x = A s + n: a harmonic excitation s1 and a
train of impact responses s2, mixed by A = [[1, 0.7], [0.45, 1]] (unknown to
the method), plus white Gaussian sensor noise at the SNR the reader chooses
(-30 to 40 dB, every 5 dB; 10 dB at first, the step nearest his 12 dB). The
figure steps through his five stages by itself, each arriving with motion:
  1 sources s;  2 mixing x = A s + n;  3 whitening z = W x (W from the sample
  covariance: cov z = I);  4 rotation y = R(theta) z, theta turning to the
  maximum of K(theta) = |kurt y1| + |kurt y2| (exact: a trigonometric
  polynomial in the fourth moments of z);  5 estimates against the true
  sources, matched in order and sign (which no method can know).
(a) the two channels over the 4 s record; (b) their joint scatter, the point
cloud itself (every second sample), with the images of the two source axes;
(c) K(theta) on one fixed scale for every SNR, so that noise visibly flattens
it; the table: for each source, the estimate that carries it, its SIR (from
G = R W A) and its correlation with the source. The stage chips jump to a
stage; the SNR chips change the noise. ?snr=<dB>&stage=<1..5> preselect.

The record is the 4 s record of Figure 11 (same sources, mixing and noise):
at 4 s Figure 11's kurtosis ICA numbers are this figure's.

Run: python tools/numfig/sp_bss_ica.py  (page, still, overlap checks over
every state, check file; prints the key numbers). --quick skips the checks
against sklearn and his page.
"""
import math
import os
import sys

import numpy as np

import common
import sp_bss_lib as L

NAME = "sp-bss-ica"
T = 4
SNR0 = 10
H_PAGE = 720

TITLE = "Figure 10: Blind source separation, method 1: kurtosis ICA"
ARIA = ("Two sensors record mixtures of a harmonic excitation and a train of impact responses, plus noise. "
        "The figure steps through kurtosis ICA: the sources, their mixing at the sensors, whitening, and the "
        "rotation that maximizes the absolute kurtosis, shown as time histories, as a joint point cloud that "
        "turns from a parallelogram into a symmetric cloud and onto the axes, and as the kurtosis curve. "
        "A table gives each estimate's correlation with its source and its SIR; choose a stage or the sensor SNR.")

JS = L.LIB + r"""
/* ================================================ Figure 10: kurtosis ICA */
const NS = 5, TURNS = [0, 0, 0, 1, 0], SYM = ['s', 'x', 'z', 'y', 'y'];
const STAGES = [['sources', 's'], ['mixing', 'A'], ['whitening', 'W'], ['rotation', 'R'], ['estimates', 'y']];
const OVS = [0, 0, 0, 0, 1];             // the true sources drawn over the estimates
const KON = [.45, .45, 1, 1, 1];          // (c) in full once the data are white
let SEL = D.snr0;
{ const q = Q.get('snr'); if (q !== null) { const i = D.snrs.indexOf(+q); if (i >= 0) SEL = i; } }
const KP = Q.get('stage') !== null ? clamp(Math.round(+Q.get('stage')), 1, NS) - 1 : NS - 1;
const POSTER_T = TOUR_START + KP * PER + 2.6;
const U = RECS[0], S0 = [[1, 0, 0, 0], [0, 1, 0, 0]];
const st = () => D.st[SEL];
function mats() {
  const s = st(), A = D.A;
  const Aug = [[A[0][0], A[0][1], s.sg, 0], [A[1][0], A[1][1], 0, s.sg]].map(r => r.map(v => v / s.kx));
  return [S0, Aug, s.WA, s.F, s.F];
}
function ends() { if (!ENDS) ENDS = mats().map(M => applyM(M, U)); return ENDS; }
const colsOf = M => [[M[0][0], M[1][0]], [M[0][1], M[1][1]]];
const lerpCols = (P, Q, e) => P.map((c, j) => [lerp(c[0], Q[j][0], e), lerp(c[1], Q[j][1], e)]);
const angOf = k => k >= 3 ? st().th : 0;
const kapOf = k => k === 1 ? st().kx : 1;
function viewRaw(w) {
  const E = ends(), M = mats(), s = st(), v = {};
  if (TURNS[w.k]) { const a = s.th * w.e; v.sig = rotSig(a, E[w.k - 1]); v.cols = colsOf(mul24(rotM(a), M[w.k - 1])); v.ang = a; }
  else { v.sig = lerpSig(E[w.from], E[w.k], w.e); v.cols = lerpCols(colsOf(M[w.from]), colsOf(M[w.k]), w.e); v.ang = lerp(angOf(w.from), angOf(w.k), w.e); }
  v.labA = SYM[w.from]; v.labB = SYM[w.k]; v.ls = w.e; v.kA = kapOf(w.from); v.kB = kapOf(w.k);
  v.ov = lerp(OVS[w.from], OVS[w.k], w.e); v.kon = lerp(KON[w.from], KON[w.k], w.e);
  return v;
}
function blend(P, V, s) {
  if (s >= 1) return V;
  const dom = P.ls < .5 ? P.labA : P.labB, same = dom === V.labB;
  return {sig: lerpSig(P.sig, V.sig, s), cols: lerpCols(P.cols, V.cols, s), ang: lerp(P.ang, V.ang, s),
    labA: same ? V.labA : dom, labB: V.labB, ls: same ? V.ls : s,
    kA: same ? V.kA : (P.ls < .5 ? P.kA : P.kB), kB: V.kB, ov: lerp(P.ov, V.ov, s), kon: lerp(P.kon, V.kon, s)};
}
function view() {
  const w = where();
  let v = viewRaw(w);
  if (JUMP && w.tr < 1 && w.k === JUMP.k && w.cyc === JUMP.cyc) v = blend(JUMP.snap, v, w.tr);
  if (CHG) { const c = settle(CHG.t, .35); if (c < 1) v = blend(CHG.snap, v, c); }
  return {w, v};
}
const snapNow = () => view().v;

/* ------------------------------------------------------------ layout */
const SR = {y: 12, h: 30, gap: 30};                      // the stages, as his flow of boxes
const LN = {x: 98, y: 108, w: 484, h: 92, gap: 18};       // (a)
const SC = {x: 706, y: 108, s: 236};                      // (b)
const KB = {x: 98, y: 446, w: 484, h: 116};               // (c)
const TB = {x0: 640, x1: 980, y: 432};                    // the table
const SN = {x: 92, y: 650, w: 38, h: 28, pitch: 40};      // the SNR chips
let SRX = null;

function stageRow(k, ph) {
  if (!SRX) {
    const ws = STAGES.map(s => chipW(s[0], s[1])), tot = ws.reduce((p, q) => p + q, 0) + SR.gap * (NS - 1);
    let x = (W - tot) / 2;
    SRX = ws.map(w => { const r = [x, w]; x += w + SR.gap; return r; });
    place(GS, SRX.map(([x, w]) => [x - 4, 0, w + 8, SR.y + SR.h + 8]), SRX.map(([x, w]) => [x, SR.y, w, SR.h]));
    BANDS.push([SRX[0][0] - 12, 0, SRX[NS - 1][0] + SRX[NS - 1][1] + 12, SR.y + SR.h + 14]);
  }
  for (let i = 0; i < NS; i++) {
    const [x, w] = SRX[i], a = arrive(.02 + .03 * i);
    chip(x, SR.y + rise(a), w, SR.h, STAGES[i][0], STAGES[i][1], {on: i === k, hover: HOV.stage === i, down: DOWN.stage === i}, a);
    if (i < NS - 1) arrow(x + w + 6, SR.y + SR.h / 2, x + w + SR.gap - 6, SR.y + SR.h / 2, {width: 1.2, head: 7, color: C.guide, alpha: a});
  }
  if (!STILL && playing) {                                 // the stage's time, under its chip
    const [x, w] = SRX[k];
    line([[x, SR.y + SR.h + 4], [x + w * clamp(ph / PER), SR.y + SR.h + 4]], {color: C.navy, width: 2, alpha: .8});
  }
}
function kapLabel(v, x, y) {                               // pgfplots' scaled ticks: the factor the ticks carry
  const one = k => Math.abs(k - 1) < .005;
  if (!one(v.kA) && !one(v.kB)) { math('\\times\\ ' + lerp(v.kA, v.kB, v.ls).toFixed(2), x, y, {size: 16, color: C.body}); return; }
  const [a0, a1] = swap(v.ls);
  if (!one(v.kA) && a0 > .01) math('\\times\\ ' + v.kA.toFixed(2), x, y, {size: 16, color: C.body, alpha: a0});
  if (!one(v.kB) && a1 > .01) math('\\times\\ ' + v.kB.toFixed(2), x, y, {size: 16, color: C.body, alpha: a1});
}
function panelA(v, cur, intro) {
  sub('a', 18, 84, 'signals over time', arrive(.04));
  const col = mix(C.navy, C.blue, v.ov);
  const ov = {a: v.ov, sig: [0, 1].map(i => { const s = st(), j = s.perm[i], c = s.c[i], o = new Float64Array(NP); for (let n = 0; n < NP; n++) o[n] = c * U[j][n]; return o; })};
  lanes(LN, v.sig, {p: seg(0, .35), draw: seg(.12, .45), color: col, ov, cur});
  const [a0, a1] = swap(v.ls), la = arrive(.2);
  for (let i = 0; i < 2; i++) {
    const yc = LN.y + i * (LN.h + LN.gap) + LN.h / 2;
    ylab(v.labA + '_' + (i + 1) + '(t)', LN.x - 52, yc, la * a0);
    ylab(v.labB + '_' + (i + 1) + '(t)', LN.x - 52, yc, la * a1);
  }
  math('t\\ (\\rm{s})', LN.x + LN.w / 2, LN.y + 2 * LN.h + LN.gap + 52, {size: 17, align: 'center', alpha: la});
  text('real time', LN.x + LN.w, LN.y + 2 * LN.h + LN.gap + 52, {size: 16, color: C.muted, align: 'right', alpha: seg(.5, .3)});
  kapLabel(v, LN.x, LN.y - 8);
  if (v.ov > .01) {                                        // which line is which, once the sources are drawn
    const y = LN.y - 9, x1 = LN.x + LN.w;
    const w2 = tw('matched source', 16), w1 = tw('estimate', 16);
    line([[x1 - w2 - 34, y - 5], [x1 - w2 - 8, y - 5]], {color: C.navy, width: 1.3, dash: [5, 3.5], alpha: v.ov});
    text('matched source', x1, y, {size: 16, color: C.body, align: 'right', alpha: v.ov});
    const x2 = x1 - w2 - 52;
    line([[x2 - w1 - 34, y - 5], [x2 - w1 - 8, y - 5]], {color: C.blue, width: 1.6, alpha: v.ov});
    text('estimate', x2, y, {size: 16, color: C.body, align: 'right', alpha: v.ov});
  }
}
function panelB(v, cur) {
  sub('b', SC.x - 70, 84, 'joint scatter', arrive(.06));
  const ax = scatter(SC, v.sig, {p: seg(.05, .35), pts: seg(.2, .35)});
  // the source axes fade out where the signal they carry sinks under the noise
  const arrows = clamp((Math.hypot(...v.cols[0]) - .3) / .25) * clamp((Math.hypot(...v.cols[1]) - .3) / .25);
  sourceArrows(ax, v.cols, arrows * seg(.4, .3), 2.6);
  if (cur.a > 0) dot(ax.X(v.sig[0][cur.n]), ax.Y(v.sig[1][cur.n]), 4.2, {color: C.ink, fill: '#fff', width: 1.4, alpha: cur.a});
  const [a0, a1] = swap(v.ls), la = arrive(.22);
  math(v.labA + '_1', SC.x + SC.s / 2, SC.y + SC.s + 50, {size: 18, align: 'center', alpha: la * a0});
  math(v.labB + '_1', SC.x + SC.s / 2, SC.y + SC.s + 50, {size: 18, align: 'center', alpha: la * a1});
  ylab(v.labA + '_2', SC.x - 46, SC.y + SC.s / 2, la * a0);
  ylab(v.labB + '_2', SC.x - 46, SC.y + SC.s / 2, la * a1);
  kapLabel(v, SC.x, SC.y - 8);
}
/* K(theta) from the fourth moments of z: exact at every angle */
function kurtPair(m, th) {
  const c = Math.cos(th), s = Math.sin(th);
  const k1 = c ** 4 * m[0] + 4 * c ** 3 * s * m[1] + 6 * c * c * s * s * m[2] + 4 * c * s ** 3 * m[3] + s ** 4 * m[4] - 3;
  const k2 = s ** 4 * m[0] - 4 * s ** 3 * c * m[1] + 6 * s * s * c * c * m[2] - 4 * s * c ** 3 * m[3] + c ** 4 * m[4] - 3;
  return Math.abs(k1) + Math.abs(k2);
}
function panelC(v) {
  const a = v.kon, la = arrive(.1);
  sub('c', 18, KB.y - 24, 'kurtosis against rotation', la);
  math('K(\\theta) = |\\rm{kurt}\\ y_1| + |\\rm{kurt}\\ y_2|', KB.x + KB.w, KB.y - 24, {size: 16, color: C.body, align: 'right', alpha: la * a});
  const ax = axes({x: KB.x, y: KB.y, w: KB.w, h: KB.h, xlim: [-45, 45], ylim: [0, D.kmax], xticks: [-45, -30, -15, 0, 15, 30, 45],
    yticks: D.kticks, xlabel: '\\rm{rotation angle}\\ \\theta\\ (\\deg)', ylabel: 'K(\\theta)', ylabelGap: 46,
    tickSize: 16, labelSize: 17, progress: seg(.1, .35), alpha: a});
  const m = st().m, pts = [];
  for (let i = 0; i <= 360; i++) { const d = -45 + i / 4; pts.push([ax.X(d), ax.Y(kurtPair(m, d * Math.PI / 180))]); }
  const thd = st().th * 180 / Math.PI;
  ax.inside(() => {
    line([[ax.X(thd), KB.y + KB.h], [ax.X(thd), ax.Y(kurtPair(m, st().th))]], {color: C.guide, width: 1, dash: [5, 4], alpha: a * seg(.4, .3)});
    line(pts, {color: C.navy, width: 2.2, progress: seg(.25, .45), alpha: a});
  });
  const d = v.ang * 180 / Math.PI;
  dot(ax.X(d), ax.Y(kurtPair(m, v.ang)), 5, {color: '#fff', fill: C.accent, width: 1.4, alpha: a * seg(.45, .25)});
}
function table(v) {
  const s = st(), a = arrive(.35) * lerp(.55, 1, v.ov), {x0, x1, y} = TB;
  const cE = x0 + 132, cS = x0 + 266;
  rule(x0, x1, y, 1.3, a);
  text('source', x0, y + 22, {size: 16, color: C.body, alpha: a});
  text('estimate', cE, y + 22, {size: 16, color: C.body, alpha: a});
  text('SIR', cS, y + 22, {size: 16, color: C.body, align: 'right', alpha: a});
  math('\\rho', x1, y + 22, {size: 17, color: C.body, align: 'right', alpha: a});
  rule(x0, x1, y + 31, .8, a);
  const names = ['harmonic', 'impacts'];
  for (let j = 0; j < 2; j++) {
    const yy = y + 56 + j * 26;
    const w0 = text(names[j] + ' ', x0, yy, {size: 16, alpha: a});
    math('s_' + (j + 1), x0 + w0, yy, {size: 16, alpha: a});
    math(s.est[j], cE, yy, {size: 16, alpha: a});
    text(s.sirs[j] + ' dB', cS, yy, {size: 16, align: 'right', alpha: a});
    text(s.rhos[j], x1, yy, {size: 16, align: 'right', alpha: a});
  }
  rule(x0, x1, y + 92, 1.3, a);
  math('\\rm{rotation}\\ \\theta^{*} = ' + s.thd + '\\deg\\rm{, }\\ K(\\theta^{*}) = ' + s.Ks, x0, y + 122, {size: 16, color: C.body, alpha: a});
  math('\\rm{source kurtosis: }' + D.ks[0] + '\\rm{ (harmonic), }' + D.ks[1] + '\\rm{ (impacts)}', x0, y + 147, {size: 16, color: C.muted, alpha: arrive(.4)});
}
function snrRow() {
  const a = arrive(.4);
  text('SNR (dB)', SN.x - 8, SN.y + 19.5, {size: 16, color: C.body, align: 'right', alpha: a});
  D.snrs.forEach((v, i) => chip(SN.x + i * SN.pitch, SN.y, SN.w, SN.h, num(v, 0), null,
    {on: i === SEL, hover: HOV.snr === i, down: DOWN.snr === i}, arrive(.4 + .01 * i)));
}
function draw() {
  const {w, v} = view(), cur = cursor(w);
  stageRow(w.k, w.ph);
  panelA(v, cur);
  panelB(v, cur);
  panelC(v);
  table(v);
  snrRow();
  mixed(D.params, 18, H - 12, {size: 15, color: C.muted, alpha: seg(.5, .3)});
}
function status() {
  const s = st(), k = clock().k;
  return 'Stage ' + (k + 1) + ' of ' + NS + ', ' + STAGES[k][0] + '. SNR ' + D.snrs[SEL] + ' dB: correlation ' + s.rhos[0] +
    ' with the harmonic source and ' + s.rhos[1] + ' with the impacts.';
}
const GS = group('stage', 'Stage of kurtosis ICA', STAGES.map((s, i) => ({aria: 'Stage ' + (i + 1) + ': ' + s[0]})),
  () => clock().k, j => chooseStage(j));
const GN = group('snr', 'Sensor SNR', D.snrs.map(v => ({aria: 'SNR ' + v + ' dB'})), () => SEL, i => chooseData(() => { SEL = i; }));
place(GN, D.snrs.map((_, i) => [SN.x + i * SN.pitch - (SN.pitch - SN.w) / 2, SN.y - 8, SN.pitch, SN.h + 16]),
      D.snrs.map((_, i) => [SN.x + i * SN.pitch, SN.y, SN.w, SN.h]));
BANDS.push([SN.x - 80, SN.y - 10, SN.x + D.snrs.length * SN.pitch + 6, SN.y + SN.h + 10]);
function reset() { TOUR0 = TOUR_START; JUMP = null; CHG = null; sync(); }
sync();
boot();
"""


# ------------------------------------------------------------------ the model, per SNR
def run():
    R = L.record(T)
    u, s = R["u"], R["s"]
    states = []
    for snr in L.SNRS:
        sg = L.sigma(snr)
        Aug = L.augmented(sg)
        x = Aug @ u
        k = L.kurtosis_ica(x)
        m = L.match(k["B"])
        y = k["B"] @ (x - x.mean(1, keepdims=True))
        rho = L.scores(y, s, m)
        WA = k["W"] @ Aug
        F = L.rot(k["theta"]) @ WA
        # the dashed overlay: each output's least-squares share of its matched source
        c = [float(y[i] @ s[m["perm"][i]] / (s[m["perm"][i]] @ s[m["perm"][i]])) for i in range(2)]
        states.append(dict(snr=snr, sg=sg, x=x, k=k, m=m, y=y, rho=rho, WA=WA, F=F, c=c,
                           kx=L.kappa(Aug, u)))
    return R, states


def data(R, states):
    u = L.shown(R["u"])
    pk, sc = L.i8pack(u)
    kmax_all = max(float(L.kcrit(st["k"]["m"], np.deg2rad(np.linspace(-45, 45, 3601))).max()) for st in states)
    kmax = math.ceil(kmax_all * 2 + 1e-9) / 2
    ks = [float(np.mean(R["s"][j] ** 4) - 3) for j in range(2)]
    st_out = []
    for st in states:
        m = st["m"]
        est = []
        for j in range(2):
            i = m["out"][j]
            est.append(("-" if m["sign"][i] < 0 else "") + f"y_{i + 1}")
        st_out.append(dict(
            sg=st["sg"], kx=st["kx"], WA=st["WA"], F=st["F"], th=st["k"]["theta"], m=st["k"]["m"],
            perm=m["perm"], c=st["c"], est=est,
            sirs=[f"{v:.1f}".replace("-", "−") for v in m["sir_src"]],
            rhos=[f"{v:.3f}" for v in st["rho"]],
            thd=f"{math.degrees(st['k']['theta']):.1f}".replace("-", "−"), Ks=f"{st['k']['K']:.2f}"))
    params = [["m", r"A = [1,\ 0.7;\ 0.45,\ 1]"],
              ["t", ";   4 s at 500 Hz;   white Gaussian noise, the SNR of the weaker sensor;   each stage drawn in units of its RMS"]]
    return dict(recs=[dict(u=pk, sc=sc)], dt=L.DECIM / L.FS, show=L.SHOW_T, A=L.A, snrs=list(L.SNRS),
                snr0=L.SNRS.index(SNR0), st=st_out, kmax=kmax,
                kticks=[v for v in np.arange(0, kmax + 1e-9, 0.5).tolist()],
                ks=[f"{v:.2f}".replace("-", "−") for v in ks], params=params)


HIS = os.environ.get("NUMFIG_HIS_PAGES", "")        # a folder holding his two BSS pages, if at hand
HIS_M1 = "bss-1-kurtosis-ica.html"
IMP_M1 = [(0.12, 1), (0.5, -0.7), (0.95, 0.85), (1.22, 0.6), (1.78, -1), (2.3, 0.75), (2.62, -0.55)]


def his_m1_record():
    """His method 1 page's own record: 3 s, seven fixed impacts, noise mulberry32(7)."""
    N = 1500
    t = np.arange(N) / L.FS
    s1 = L.standardize(L.harmonic(t))
    s2 = L.standardize(L.impact_train(t, IMP_M1, cut=None))
    g = L.gauss_from(L.mulberry32(7))
    nn = np.array([[g(), g()] for _ in range(N)])
    return np.vstack([s1, s2, L.standardize(nn[:, 0]), L.standardize(nn[:, 1])])


def his_m1_corr(u, snr):
    """His page's readout at stage 5: |corr| of each output with its source, 3 decimals."""
    Aug = L.augmented(L.sigma(snr))
    W, th, F = L.his_kica_grid(u, Aug, 0.5, centre=True, m1=True)
    y = F @ u
    pm = L.his_match(F)
    return [abs(float(np.mean(y[i] * pm[i][1] * u[pm[i][0]]))) for i in range(2)], th


def validate(R, states, D, quick=False):
    u, s = R["u"], R["s"]
    out = []
    say = out.append
    st10 = states[L.SNRS.index(SNR0)]
    say("Figure 10, blind source separation, method 1, kurtosis ICA: check of tools/numfig/sp_bss_ica.py")
    say("")
    say("MODEL (sp_bss_lib, shared with Figure 11)")
    say(f"  fs = {L.FS:g} Hz, record T = {T} s, N = {R['N']} samples; drawn: the first 4 s, every second sample (1000).")
    say("  s1: (1 + 0.5 sin 2 pi 0.4 t)(sin 2 pi 3t + 0.45 sin(2 pi 6t + 0.7) + 0.25 sin(2 pi 9t + 1.3)).")
    say(f"  s2: impacts ringing an {L.FN:g} Hz mode, zeta = {L.ZETA:g}, his seeded train (mulberry32(21)), here {len(R['imp'])} impacts:")
    say("      " + ", ".join(f"({t0:.3f} s, {a:+.3f})" for t0, a in R["imp"]))
    say("  both standardized; A = [[1, 0.7], [0.45, 1]]; noise: two standardized white Gaussian channels, his")
    say(f"  Box-Muller on mulberry32(7 + T) = mulberry32({7 + T}); sigma^2 = 1.2025 10^(-SNR/10) (the weaker sensor's SNR).")
    c = L.corr(s[0], s[1])
    kk = [float(np.mean(s[j] ** 4) - 3) for j in range(2)]
    say(f"  In this record: corr(s1, s2) = {c:+.4f}; excess kurtosis s1 {kk[0]:+.3f} (sub-Gaussian), s2 {kk[1]:+.3f}.")
    say("  Method: centre; W from the sample covariance (W C W' = I, rows the principal axes over root")
    say("  eigenvalues); z = W x; y = R(theta) z, R = [[cos, sin], [-sin, cos]], theta in [-45, 45) deg maximizing")
    say("  K = |kurt y1| + |kurt y2|. K(theta) = |k(theta)| + |k(theta + 90 deg)|, k a quartic in (cos, sin) through the")
    say("  fourth moments m40, m31, m22, m13, m04 of z: maximized on a 0.01 deg grid, refined (bounded Brent, 1e-13 rad).")
    say("  Order and sign cannot be known by any blind method: outputs are paired with sources by the larger of")
    say("  |G11 G22| and |G12 G21|, G = R W A, and signs taken from G. SIR of a source: G_ij^2 / G_ik^2 in the output")
    say("  that carries it (unit-variance sources); rho: Pearson correlation of that output with the source.")
    say("")
    say("RESULTS (the figure's table; theta* in deg)")
    say("   SNR   theta*      K*   SIR s1   SIR s2   rho s1   rho s2   estimates (s1, s2)")
    for st in states:
        m = st["m"]
        est = [("-" if m["sign"][m["out"][j]] < 0 else "") + f"y{m['out'][j] + 1}" for j in range(2)]
        say(f"  {st['snr']:4d} {math.degrees(st['k']['theta']):8.2f} {st['k']['K']:7.3f} {m['sir_src'][0]:8.1f} "
            f"{m['sir_src'][1]:8.1f} {st['rho'][0]:8.3f} {st['rho'][1]:8.3f}   {est[0]}, {est[1]}")
    say("")
    say("VALIDATION")
    # 1 whitening
    ew = max(float(np.abs(st["k"]["z"] @ st["k"]["z"].T / R["N"] - np.eye(2)).max()) for st in states)
    say(f"  1. Whitening: |cov(z) - I| <= {ew:.1e} over all 15 SNRs (the target 1e-12).")
    # 2 K polynomial against the samples
    z = st10["k"]["z"]
    angs = np.deg2rad([-44.9, -30, -12.5, 0, 7.7, 21, 44.3])
    e_k = 0.0
    for a in angs:
        y1 = math.cos(a) * z[0] + math.sin(a) * z[1]
        y2 = -math.sin(a) * z[0] + math.cos(a) * z[1]
        direct = abs(np.mean(y1 ** 4) / np.mean(y1 ** 2) ** 2 - 3) + abs(np.mean(y2 ** 4) / np.mean(y2 ** 2) ** 2 - 3)
        e_k = max(e_k, abs(direct - float(L.kcrit(st10["k"]["m"], a))))
    say(f"  2. K(theta) from the five moments against the kurtosis of the rotated samples themselves (7 angles,")
    say(f"     {SNR0} dB): largest difference {e_k:.1e}.")
    # 3 the optimum: finer grid, rotation equivariance, his grid
    e_g = 0.0
    for st in states:
        fine = np.deg2rad(np.arange(-45, 45, 0.0005))
        g = fine[int(np.argmax(L.kcrit(st["k"]["m"], fine)))]
        e_g = max(e_g, abs(math.degrees(L.wrap45(g - st["k"]["theta"]))))
    phi = math.radians(17.3)
    zr = L.rot(phi) @ z
    th2 = L.maximize_k(L.moments4(zr))
    e_eq = abs(math.degrees(L.wrap45(th2 - (st10["k"]["theta"] - phi))))
    say(f"  3. The optimum: against a 0.0005 deg grid, within {e_g:.1e} deg at every SNR. Turning the white data")
    say(f"     by 17.3 deg moves it by -17.3 deg (modulo 90): error {e_eq:.1e} deg.")
    dth, drho = 0.0, 0.0
    for st in states:
        Aug = L.augmented(st["sg"])
        Wg, thg, Fg = L.his_kica_grid(u, Aug, 0.5)
        dth = max(dth, abs(math.degrees(L.wrap45(thg - st["k"]["theta"]))))
        mg = L.match(L.rot(thg) @ Wg)
        rg = L.scores(L.rot(thg) @ Wg @ (st["x"] - st["x"].mean(1, keepdims=True)), s, mg)
        drho = max(drho, max(abs(a - b) for a, b in zip(rg, st["rho"])))
    say(f"     His page searches a 0.5 deg grid: its angle is within {dth:.3f} deg of the exact one (at most 0.25),")
    say(f"     and its correlations within {drho:.4f}.")
    if not quick:
        # 4 sklearn
        from sklearn.decomposition import FastICA
        import sklearn
        say(f"  4. Against scikit-learn {sklearn.__version__} FastICA (fun = cube, the kurtosis fixed point; symmetric")
        say("     decorrelation; unit-variance whitening; tol 1e-12; 8 starts, the one with the largest K kept); its")
        say("     fixed points are the stationary points of |kurt y1| + |kurt y2| (signs free). Angle between the")
        say("     unmixing rows (matched in order and sign):")
        for snr in (0, 10, 20, 40):
            st = states[L.SNRS.index(snr)]
            x = st["x"]
            best = None
            for seed in range(8):
                ica = FastICA(n_components=2, algorithm="parallel", whiten="unit-variance", fun="cube",
                              max_iter=20000, tol=1e-12, random_state=seed, whiten_solver="eigh")
                Y = ica.fit_transform(x.T).T
                Ky = sum(abs(np.mean(y ** 4) / np.mean(y ** 2) ** 2 - 3) for y in Y)
                if best is None or Ky > best[0]:
                    best = (Ky, ica.components_.copy(), ica.n_iter_)
            Bm = st["k"]["B"]
            Bs = best[1]
            ang = []
            for i in range(2):
                r1 = Bm[i] / np.linalg.norm(Bm[i])
                cs = [abs(r1 @ (Bs[j] / np.linalg.norm(Bs[j]))) for j in range(2)]
                ang.append(math.degrees(math.acos(min(1.0, max(cs)))))
            say(f"     {snr:3d} dB: {max(ang):.1e} deg (K: FastICA {best[0]:.6f}, here {st['k']['K']:.6f}; {best[2]} iterations)")
        # 5 his page
        path = os.path.join(HIS, HIS_M1) if HIS else ""
        if path and os.path.isfile(path):
            um1 = his_m1_record()
            snrs = (-10, 0, 6, 12, 20, 40)
            acts = [f"(() => {{ const e = document.getElementById('noise'); e.value = '{v}'; e.dispatchEvent(new Event('input')); "
                    f"document.querySelectorAll('#dots button')[4].click(); }})()" for v in snrs]
            got = L.his_page(path, acts, "document.getElementById('q').textContent")
            ok = 0
            say("  5. His page (method 1, its own record: 3 s, seven fixed impacts, noise mulberry32(7)) run headless,")
            say("     against this port of his model and his 0.5 deg search: the correlations it prints at stage 5")
            for v, g in zip(snrs, got):
                mine, th = his_m1_corr(um1, v)
                txt = f"{mine[0]:.3f} and {mine[1]:.3f}"
                ok += txt in g
                say(f"     {v:4d} dB: his page '{g.split(': ')[-1]}', the port {txt}")
            say(f"     {ok} of {len(snrs)} identical to the printed digits: the generator, the sources, the noise and the")
            say("     method are his, number for number.")
        else:
            say("  5. His page: not at hand (set NUMFIG_HIS_PAGES to the folder holding bss-1-kurtosis-ica.html).")
    # 6 the record is short: the sources are not independent in it
    say("  6. Why the separation stops near 12 to 15 dB even without noise: in 4 s the two sources are not")
    say("     independent in the sample. Fourth-order cross-cumulants and noise-free kurtosis ICA per record:")
    for TT in L.RECORDS:
        RR = L.record(TT)
        s1, s2 = RR["s"]
        r12 = float(np.mean(s1 * s2))
        c13 = float(np.mean(s1 * s2 ** 3) - 3 * r12)
        c22 = float(np.mean(s1 ** 2 * s2 ** 2) - 1 - 2 * r12 ** 2)
        kq = L.kurtosis_ica(L.A @ RR["s"])
        mq = L.match(kq["B"])
        say(f"     {TT:2d} s ({len(RR['imp']):3d} impacts): corr {r12:+.4f}, cum(s1,s2,s2,s2) {c13:+.4f}, cum(s1,s1,s2,s2) {c22:+.4f};"
            f" SIR {mq['sir_src'][0]:.1f} and {mq['sir_src'][1]:.1f} dB")
    # 7 other noise records
    say("  7. One noise record is shown (his seed); 50 other records (mulberry32(1000 + i)) at the same settings,")
    say("     median and 10 to 90 % range, and where the record shown falls:")
    for snr in (0, 10, 20, 40):
        rows = []
        for i in range(50 if not quick else 8):
            n = L.noise(R["N"], 1000 + i)
            x = L.A @ s + L.sigma(snr) * n
            kq = L.kurtosis_ica(x)
            mq = L.match(kq["B"])
            yq = kq["B"] @ (x - x.mean(1, keepdims=True))
            rows.append(L.scores(yq, s, mq) + [min(mq["sir_src"])])
        rows = np.array(rows)
        st = states[L.SNRS.index(snr)]
        q = lambda col: np.percentile(rows[:, col], [10, 50, 90])
        r0, r1, sm = q(0), q(1), q(2)
        pr = 100 * np.mean(rows[:, 0] <= st["rho"][0])
        say(f"     {snr:3d} dB: rho s1 {r0[1]:.3f} ({r0[0]:.3f} to {r0[2]:.3f}), rho s2 {r1[1]:.3f} ({r1[0]:.3f} to {r1[2]:.3f}), "
            f"worse SIR {sm[1]:.1f} dB ({sm[0]:.1f} to {sm[2]:.1f}); the record shown at percentile {pr:.0f} (rho s1)")
    # 8 the page itself
    i10 = L.SNRS.index(SNR0)
    angs_d = [-40, -17.5, 0, 12.25, 33]
    ex = [f"Array.from(RECS[0][{c}])" for c in range(4)]
    ex += [f"[{', '.join(f'kurtPair(D.st[{i10}].m, {a} * Math.PI / 180)' for a in angs_d)}]"]
    ex += ["Array.from(applyM(D.st[%d].F, RECS[0])[0])" % i10, "Array.from(applyM(D.st[%d].F, RECS[0])[1])" % i10]
    got = L.page_eval(NAME, "", ex)
    uu = L.shown(u)
    e_u = max(float(np.abs(np.array(got[c]) - uu[c]).max() / np.abs(uu[c]).max()) for c in range(4))
    e_kp = float(np.abs(np.array(got[4]) - L.kcrit(st10["k"]["m"], np.deg2rad(angs_d))).max())
    yv = L.shown(st10["F"] @ u)
    e_y = max(float(np.abs(np.array(got[5 + i]) - yv[i]).max()) for i in range(2))
    say(f"  8. The page: u decoded from int8 within {e_u:.4f} of each channel's largest value (1/254 = 0.0039);")
    say(f"     its K(theta) at 5 angles within {e_kp:.1e} of numpy (it evaluates the same polynomial in double);")
    say(f"     the estimates it draws, F u, within {e_y:.3f} of numpy's (rounding of u; RMS 1).")
    say("")
    say("DISPLAY")
    say("  Every stage is a 2 x 4 matrix on u = [s1, s2, n1, n2] (his device); the page draws M u: sources [I 0],")
    say("  sensors Aug = [A, sigma I], whitened W Aug, rotated R(theta) W Aug (theta turning from 0 to theta*),")
    say("  estimates. Between stages the matrices are interpolated (his device); the rotation is a true rotation.")
    say("  Each stage is drawn in units of its RMS: 1 for s, z and y; the sensors carry the factor printed at the")
    say(f"  axes (x {st10['kx']:.2f} at {SNR0} dB, x {states[0]['kx']:.2f} at -30 dB). The arrows in (b) are the images of the")
    say("  two source axes, the first two columns of the stage's matrix (2.6 units long per unit); they fade out")
    say("  where their length falls under 0.55 (the signal sinks under the noise). (c) one scale for every SNR")
    say(f"  (0 to {D['kmax']:g}), so that noise visibly flattens K(theta). The cursor plays the 4 s in real time.")
    say("  The dashed source over each estimate is that source times the estimate's least-squares share of it.")
    say("  No 'new noise' control: his two pages draw one seeded record (mulberry32(7) and (7 + T)) and so does")
    say("  this figure; item 7 shows how other records scatter.")
    return out


def build(quick=False):
    R, states = run()
    D = data(R, states)
    common.build_html(NAME, TITLE, ARIA, 1000, H_PAGE, D, JS)
    for st in states:
        print(f"SNR {st['snr']:4d} dB: theta* {math.degrees(st['k']['theta']):7.2f} deg, K* {st['k']['K']:.3f}, "
              f"SIR {st['m']['sir_src'][0]:6.1f} {st['m']['sir_src'][1]:6.1f} dB, "
              f"rho {st['rho'][0]:.3f} {st['rho'][1]:.3f}")
    return R, states, D


STAGE_TIMES = []                                   # moments across a whole tour and the loop back
for _k in range(5):
    STAGE_TIMES += [round(_k * 5.2 + d, 3) for d in (0.15, 0.35, 0.55, 0.8, 1.6, 3.0, 4.9)]
STAGE_TIMES += [26.15, 26.35, 26.6, 27.0]


def main():
    quick = "--quick" in sys.argv
    R, states, D = build(quick)
    png = common.still(NAME)
    print("still:", png)
    faults, n, errs = L.check_states(NAME, [f"snr={v}" for v in L.SNRS], STAGE_TIMES)
    print(f"overlap over {len(L.SNRS)} SNR states x {len(STAGE_TIMES) + 1} moments: {n} drawn, {len(faults)} faults, errors {errs}")
    for f in faults[:30]:
        print("  ", f)
    steps = [
        ("intro over, playing", "", "playing === true && t > 1.2", 1600),
        ("stage chip 4 chosen, still playing", "click:.nfb[aria-label='Stage 4: rotation']", "clock().k === 3 && playing === true", 300),
        ("rotation stage glides from the stage shown", "", "JUMP !== null && JUMP.k === 3", 50),
        ("SNR chip 0 dB chosen, still playing", "click:.nfb[aria-label='SNR 0 dB']", "SEL === D.snrs.indexOf(0) && playing === true", 300),
        ("arrow key moves the SNR", "key:ArrowRight", "SEL === D.snrs.indexOf(5)", 200),
        ("canvas click away from the controls pauses", "(() => { const r = cv.getBoundingClientRect(); "
         "cv.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: r.left + r.width * .3, clientY: r.top + r.height * .3})); })()",
         "playing === false", 150),
        ("paused, a stage chip shows it complete", "click:.nfb[aria-label='Stage 2: mixing']", "clock().k === 1 && where().e > .99 && playing === false", 150),
        ("click beside the SNR chips does not toggle", "(() => { const r = cv.getBoundingClientRect(); "
         f"cv.dispatchEvent(new MouseEvent('click', {{bubbles: true, clientX: r.left + r.width * {(92 - 40) / 1000}, clientY: r.top + r.height * {664 / 720}}})); }})()",
         "playing === false", 150),
    ]
    fails, errs2 = L.interact(NAME, steps)
    glide_acts = [(t0, a) for t0 in (2.0, 7.0, 12.5, 17.0, 22.5, 25.9)
                  for a in [f"chooseStage({j})" for j in range(5)]
                  + [f"chooseData(() => {{ SEL = {i}; }})" for i in (0, 5, 8, 14)]]
    ng, gfaults = L.check_glides(NAME, glide_acts)
    print(f"glides: {ng} frames, {len(gfaults)} faults", gfaults[:10])
    print("interaction failures:", fails, "errors:", errs2)
    lines = validate(R, states, D, quick)
    lines += ["", "CHECKS OF THE PAGE",
              f"  Overlap (engine ?overlap): the poster and every 0.25 s up to it (common.still), and {len(L.SNRS)} SNR",
              f"  states (?snr=) x {len(STAGE_TIMES) + 1} moments across the five stages and the loop back: {n} frames, "
              f"{len(faults)} faults.",
              "  Through the glides a reader starts (a stage chosen, an SNR chosen, while playing, at",
              f"  moments across the tour, each glide drawn at 11 moments over 1.2 s): {ng} frames, {len(gfaults)} faults.",
              f"  In a browser: {len(steps) - len(fails)} of {len(steps)} interactions as intended (stage and SNR chips never",
              "  pause the figure, arrow keys move the choice, a click on open ground pauses, a paused choice shows",
              f"  the stage complete); console errors: {len(errs) + len(errs2)}.",
              f"  Page {os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.html')) / 1024:.0f} KB, poster "
              f"{os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.webp')) / 1024:.0f} KB."]
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(common.HERE, "sp_bss_ica.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
