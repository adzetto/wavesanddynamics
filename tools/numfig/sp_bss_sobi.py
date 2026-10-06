"""Figure 11 of the signal processing document: blind source separation,
method 2, SOBI-family separation and Wiener denoising (his page "Blind
source separation, method 2: SOBI-family separation and Wiener denoising",
redrawn on the shared model of sp_bss_lib).

The same two sensors, sources, mixing and noise as Figure 10 (at 4 s the
same record). The figure steps through his seven stages by itself:
  1 sources s;  2 sensors x = A s + n;  3 the spectrum: Welch auto and cross
  spectra (Hann, 50% overlap; 256, 1024, 2048 samples for 4, 16, 64 s), the
  white noise floor estimated as the median of each auto spectrum, and the
  bands that rise 4 standard errors above it;  4 noise-corrected whitening:
  W from the bands' summed real cross-spectral matrices with the floor taken
  off the diagonal (W M W' = I; the noise, white and independent between
  sensors, is absent from the cross spectra);  5 joint diagonalization: the
  one rotation that makes every band's whitened matrix diagonal (SOBI's
  principle, in the frequency domain), exact in closed form;  6 separated
  y = R W x;  7 Wiener: each output keeps the bands where it rises above its
  own noise level (known from the floors and R W), gain max(0, P - o N)/P,
  o = 1 + 2/sqrt(K).
(a) the two channels over the first 4 s; (b) their joint scatter with the
images of the source axes; (c) the sensors' spectra (one-sided PSD in dB),
the floors, the bands used, and under them each output's Wiener gain;
(d) the off-diagonal energy left after a rotation by theta, normalized;
the table compares, per source, the SIR and the correlation of kurtosis ICA
(Figure 10's method, on the same data), of this method, and after Wiener.
Chips choose the stage, the sensor SNR (-30 to 40 dB, every 5 dB; 0 dB at
first, his) and the record (4, 16, 64 s, his). ?snr=<dB>&len=<s>&stage=<1..7>
preselect.

Run: python tools/numfig/sp_bss_sobi.py  (page, still, overlap checks over
every state, check file; prints the key numbers). --quick skips the slow
checks.
"""
import math
import os
import sys

import numpy as np

import common
import sp_bss_lib as L

NAME = "sp-bss-sobi"
SNR0, REC0 = 0, 4
H_PAGE = 730

TITLE = "Figure 11: Blind source separation, method 2: SOBI-family separation and Wiener denoising"
ARIA = ("The same two noisy sensor records as Figure 10, separated by a second-order method: the spectra with "
        "their noise floor and the bands above it, whitening from the bands with the noise removed, one rotation "
        "that diagonalizes every band's matrix at once, and a Wiener filter on each output. Time histories, the "
        "joint point cloud, the spectra with the Wiener gains and the off-diagonal curve follow the stages; a "
        "table compares SIR and correlation with kurtosis ICA. Choose a stage, the sensor SNR and the record length.")

JS = L.LIB + r"""
/* ================================================ Figure 11: SOBI family and Wiener */
const NS = 7, TURNS = [0, 0, 0, 0, 1, 0, 0], SYM = ['s', 'x', 'x', 'z', 'y', 'y', 'yhat'];
const STAGES = [['sources', 's'], ['sensors', 'x'], ['spectrum', ''], ['whitening', 'W'], ['diagonalize', 'R'],
                ['separated', 'y'], ['Wiener', '']];
const OVS = [0, 0, 0, 0, 0, 1, 1];           // the true sources drawn over the estimates
let SEL = D.snr0, REC = D.rec0;
{ const q = Q.get('snr'); if (q !== null) { const i = D.snrs.indexOf(+q); if (i >= 0) SEL = i; }
  const r = Q.get('len'); if (r !== null) { const i = D.T.indexOf(+r); if (i >= 0) REC = i; } }
const KP = Q.get('stage') !== null ? clamp(Math.round(+Q.get('stage')), 1, NS) - 1 : NS - 1;
const POSTER_T = TOUR_START + KP * PER + 2.6;
const S0 = [[1, 0, 0, 0], [0, 1, 0, 0]];
const st = () => D.st[REC][SEL], U = () => RECS[REC];
function mats() {
  const s = st(), A = D.A;
  const Aug = [[A[0][0], A[0][1], s.sg, 0], [A[1][0], A[1][1], 0, s.sg]].map(r => r.map(v => v / s.kx));
  return [S0, Aug, Aug, s.WA, s.F, s.F, s.F];
}
const YD = {};                                            // the Wiener outputs, decoded once per state
function yden() { const k = REC + ':' + SEL; if (!YD[k]) { const s = st(); YD[k] = s.yd.map((q, i) => i8f(q, s.ysc[i])); } return YD[k]; }
function ends() {
  if (!ENDS) { const M = mats(); ENDS = M.map(m => applyM(m, U())); ENDS[6] = yden(); }
  return ENDS;
}
const colsOf = M => [[M[0][0], M[1][0]], [M[0][1], M[1][1]]];
const lerpCols = (P, Q, e) => P.map((c, j) => [lerp(c[0], Q[j][0], e), lerp(c[1], Q[j][1], e)]);
const angOf = k => k >= 4 ? st().th : 0;
const kapOf = k => k === 1 || k === 2 ? st().kx : k === 6 ? st().kw : 1;
const BAND = [0, 0, 1, 1, 1, 1, 1], GAIN = [.45, .45, .45, .45, .45, .45, 1], JON = [.45, .45, .45, 1, 1, 1, 1];
const DEN = [0, 0, 0, 0, 0, 0, 1];
function viewRaw(w) {
  const E = ends(), M = mats(), s = st(), v = {};
  if (TURNS[w.k]) { const a = s.th * w.e; v.sig = rotSig(a, E[w.k - 1]); v.cols = colsOf(mul24(rotM(a), M[w.k - 1])); v.ang = a; }
  else { v.sig = lerpSig(E[w.from], E[w.k], w.e); v.cols = lerpCols(colsOf(M[w.from]), colsOf(M[w.k]), w.e); v.ang = lerp(angOf(w.from), angOf(w.k), w.e); }
  v.labA = SYM[w.from]; v.labB = SYM[w.k]; v.ls = w.e; v.kA = kapOf(w.from); v.kB = kapOf(w.k);
  const L = (T) => lerp(T[w.from], T[w.k], w.e);
  v.ov = L(OVS); v.band = L(BAND); v.gain = L(GAIN); v.jon = L(JON); v.den = L(DEN);
  v.spec = w.k === 0 ? lerp(1, .45, w.e) : w.from === 0 ? lerp(.45, 1, w.e) : 1;
  return v;
}
function blend(P, V, s) {
  if (s >= 1) return V;
  const dom = P.ls < .5 ? P.labA : P.labB, same = dom === V.labB, l = (a, b) => lerp(a, b, s);
  return {sig: lerpSig(P.sig, V.sig, s), cols: lerpCols(P.cols, V.cols, s), ang: l(P.ang, V.ang),
    labA: same ? V.labA : dom, labB: V.labB, ls: same ? V.ls : s,
    kA: same ? V.kA : (P.ls < .5 ? P.kA : P.kB), kB: V.kB, ov: l(P.ov, V.ov), band: l(P.band, V.band),
    gain: l(P.gain, V.gain), jon: l(P.jon, V.jon), den: l(P.den, V.den), spec: l(P.spec, V.spec)};
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
const SR = {y: 12, h: 30, gap: 22};
const LN = {x: 98, y: 100, w: 484, h: 78, gap: 14};       // (a)
const SC = {x: 726, y: 100, s: 196};                      // (b)
const PS = {x: 98, y: 416, w: 484, h: 92}, GB = {x: 98, y: 516, w: 484, h: 38};   // (c)
const JB = {x: 726, y: 398, w: 212, h: 70};               // (d)
const TB = {x0: 652, x1: 980, y: 532};                    // the table
/* the chips under (c), in the left column: the SNR, then the record */
const SN = {x: 92, y: 620, w: 35, h: 28, pitch: 36};      // SNR chips
const RC = {x: 92, y: 662, w: 50, h: 28, pitch: 56};      // record chips
let SRX = null;

function stageRow(k, ph) {
  if (!SRX) {
    const ws = STAGES.map(s => chipW(s[0], s[1])), tot = ws.reduce((p, q) => p + q, 0) + SR.gap * (NS - 1);
    let x = (W - tot) / 2;
    SRX = ws.map(w => { const r = [x, w]; x += w + SR.gap; return r; });
    place(GS, SRX.map(([x, w]) => [x - 3, 0, w + 6, SR.y + SR.h + 8]), SRX.map(([x, w]) => [x, SR.y, w, SR.h]));
    BANDS.push([SRX[0][0] - 12, 0, SRX[NS - 1][0] + SRX[NS - 1][1] + 12, SR.y + SR.h + 14]);
  }
  for (let i = 0; i < NS; i++) {
    const [x, w] = SRX[i], a = arrive(.02 + .025 * i);
    chip(x, SR.y + rise(a), w, SR.h, STAGES[i][0], STAGES[i][1], {on: i === k, hover: HOV.stage === i, down: DOWN.stage === i}, a);
    if (i < NS - 1) arrow(x + w + 4, SR.y + SR.h / 2, x + w + SR.gap - 4, SR.y + SR.h / 2, {width: 1.2, head: 7, color: C.guide, alpha: a});
  }
  if (!STILL && playing) {
    const [x, w] = SRX[k];
    line([[x, SR.y + SR.h + 4], [x + w * clamp(ph / PER), SR.y + SR.h + 4]], {color: C.navy, width: 2, alpha: .8});
  }
}
function kapLabel(v, x, y) {
  const one = k => Math.abs(k - 1) < .005;
  if (!one(v.kA) && !one(v.kB)) { math('\\times\\ ' + lerp(v.kA, v.kB, v.ls).toFixed(2), x, y, {size: 16, color: C.body}); return; }
  const [a0, a1] = swap(v.ls);
  if (!one(v.kA) && a0 > .01) math('\\times\\ ' + v.kA.toFixed(2), x, y, {size: 16, color: C.body, alpha: a0});
  if (!one(v.kB) && a1 > .01) math('\\times\\ ' + v.kB.toFixed(2), x, y, {size: 16, color: C.body, alpha: a1});
}
function panelA(v, cur) {
  sub('a', 18, 78, 'signals over time', arrive(.04));
  const s = st(), u = U(), col = mix(C.navy, C.blue, v.ov);
  const ov = {a: v.ov, sig: [0, 1].map(i => { const j = s.perm[i], c = lerp(s.c[i], s.cd[i], v.den), o = new Float64Array(NP);
    for (let n = 0; n < NP; n++) o[n] = c * u[j][n]; return o; })};
  lanes(LN, v.sig, {p: seg(0, .35), draw: seg(.12, .45), color: col, ov, cur});
  const [a0, a1] = swap(v.ls), la = arrive(.2);
  for (let i = 0; i < 2; i++) {
    const yc = LN.y + i * (LN.h + LN.gap) + LN.h / 2;
    symLabel(v.labA, i + 1, '(t)', LN.x - 52, yc, {rot: true, alpha: la * a0});
    symLabel(v.labB, i + 1, '(t)', LN.x - 52, yc, {rot: true, alpha: la * a1});
  }
  const yx = LN.y + 2 * LN.h + LN.gap + 50;
  math('t\\ (\\rm{s})', LN.x + LN.w / 2, yx, {size: 17, align: 'center', alpha: la});
  text(D.T[REC] > 4 ? 'first 4 s of ' + D.T[REC] + ' s' : 'real time', LN.x + LN.w, yx, {size: 16, color: C.muted, align: 'right', alpha: seg(.5, .3)});
  kapLabel(v, LN.x, LN.y - 6);
  if (v.ov > .01) {
    const y = LN.y - 9, x1 = LN.x + LN.w, w2 = tw('matched source', 16), w1 = tw('estimate', 16);
    line([[x1 - w2 - 34, y - 5], [x1 - w2 - 8, y - 5]], {color: C.navy, width: 1.3, dash: [5, 3.5], alpha: v.ov});
    text('matched source', x1, y, {size: 16, color: C.body, align: 'right', alpha: v.ov});
    const x2 = x1 - w2 - 52;
    line([[x2 - w1 - 34, y - 5], [x2 - w1 - 8, y - 5]], {color: C.blue, width: 1.6, alpha: v.ov});
    text('estimate', x2, y, {size: 16, color: C.body, align: 'right', alpha: v.ov});
  }
}
function panelB(v, cur) {
  sub('b', SC.x - 72, 78, 'joint scatter', arrive(.06));
  const ax = scatter(SC, v.sig, {p: seg(.05, .35), pts: seg(.2, .35)});
  const arrows = clamp((Math.hypot(...v.cols[0]) - .3) / .25) * clamp((Math.hypot(...v.cols[1]) - .3) / .25) * (1 - v.den);
  sourceArrows(ax, v.cols, arrows * seg(.4, .3), 2.5);
  if (cur.a > 0) dot(ax.X(v.sig[0][cur.n]), ax.Y(v.sig[1][cur.n]), 4.2, {color: C.ink, fill: '#fff', width: 1.4, alpha: cur.a});
  const [a0, a1] = swap(v.ls), la = arrive(.22);
  symLabel(v.labA, 1, '', SC.x + SC.s / 2, SC.y + SC.s + 50, {alpha: la * a0});
  symLabel(v.labB, 1, '', SC.x + SC.s / 2, SC.y + SC.s + 50, {alpha: la * a1});
  symLabel(v.labA, 2, '', SC.x - 46, SC.y + SC.s / 2, {rot: true, alpha: la * a0});
  symLabel(v.labB, 2, '', SC.x - 46, SC.y + SC.s / 2, {rot: true, alpha: la * a1});
  kapLabel(v, SC.x, SC.y - 6);
}
/* a channel's symbol with its index: y-hat (his denoised outputs) is CMU's italic y-hat */
function symLabel(sy, i, suf, x, y, o) {
  const a = o.alpha, size = 18;
  if (a <= .01) return;
  if (sy !== 'yhat') {
    if (o.rot) ylab(sy + '_' + i + suf, x, y, a); else math(sy + '_' + i + suf, x, y, {size, align: 'center', alpha: a});
    return;
  }
  const rest = '_' + i + suf, w1 = tw('\u0177', size) * 1.04, w = w1 + mw(rest, size);
  ctx.save(); ctx.translate(x, y); if (o.rot) ctx.rotate(-Math.PI / 2);
  text('\u0177', -w / 2, 0, {size, italic: true, alpha: a});
  math(rest, -w / 2 + w1, 0, {size, alpha: a});
  ctx.restore();
}
/* (c): the sensors' spectra, the floors, the bands; under them each output's Wiener gain */
const DB0 = D.db0, dB = q => q / 2 + DB0;
function panelC(v) {
  const s = st(), la = arrive(.1), sa = v.spec, n = D.kmax[REC], df = D.df[REC];
  sub('c', 18, PS.y - 38, 'spectra and Wiener gain', la);
  const ax = axes({x: PS.x, y: PS.y, w: PS.w, h: PS.h, xlim: [0, 40], ylim: [-70, 20], xticks: [0, 10, 20, 30, 40],
    yticks: [-60, -40, -20, 0, 20], xfmt: () => '', ylabel: '\\rm{PSD (dB)}', ylabelGap: 50, tickSize: 16, labelSize: 17,
    progress: seg(.1, .35), alpha: sa});
  const sp = s.sp.map((q, i) => b64i8(q));
  ax.inside(() => {
    const ba = sa * v.band;                                // the bands used, shaded
    if (ba > .01) {                                      // each band its own bin, a gap between neighbours
      const bw = ax.X(df) - ax.X(0), g = clamp(.16 * bw, 1, 3.5);
      ctx.save(); ctx.globalAlpha *= ba; ctx.fillStyle = C.steel2;
      for (const k of s.bands) ctx.fillRect(ax.X((k - .5) * df) + g / 2, PS.y, Math.max(1, bw - g), PS.h); ctx.restore(); }
    [C.navy, C.sky].forEach((c, i) => {
      const pts = []; for (let k = 1; k <= n; k++) pts.push([ax.X(k * df), ax.Y(dB(sp[i][k]))]);
      line(pts, {color: c, width: 1.8, progress: seg(.22 + .05 * i, .45), alpha: sa});
      const yf = ax.Y(s.fl[i]);
      line([[PS.x, yf], [PS.x + PS.w, yf]], {color: c, width: 1.3, dash: [5, 4], alpha: sa * v.band, progress: v.band});
    });
  });
  const ga = v.gain;
  const gx = axes({x: GB.x, y: GB.y, w: GB.w, h: GB.h, xlim: [0, 40], ylim: [0, 1], xticks: [0, 10, 20, 30, 40], yticks: [0, 1],
    ylabel: '\\rm{gain}', ylabelGap: 50, xlabel: '\\rm{frequency}\\ f\\ (\\rm{Hz})', tickSize: 16, labelSize: 17,
    progress: seg(.12, .35), alpha: Math.max(ga, .45)});
  const gg = s.g.map(q => b64i8(q));
  gx.inside(() => [C.navy, C.sky].forEach((c, i) => {
    const pts = []; for (let k = 0; k <= n; k++) pts.push([gx.X(k * df), gx.Y(gg[i][k] / 127)]);
    line(pts, {color: c, width: 1.8, alpha: ga, progress: seg(.3, .45)});
  }));
  // which line is which, in one row over the spectra
  const ly = PS.y - 12, ka = la * Math.max(sa, .45);
  let x = PS.x + 4;
  const item = (draw, words) => { draw(x); x += 34 + text(words, x + 34, ly, {size: 16, color: C.body, alpha: ka}) + 18; };
  item(x0 => line([[x0, ly - 5], [x0 + 26, ly - 5]], {color: C.navy, width: 1.8, alpha: ka}), 'channel 1');
  item(x0 => line([[x0, ly - 5], [x0 + 26, ly - 5]], {color: C.sky, width: 1.8, alpha: ka}), 'channel 2');
  item(x0 => line([[x0, ly - 5], [x0 + 26, ly - 5]], {color: C.guide, width: 1.3, dash: [5, 4], alpha: ka}), 'noise floor');
  item(x0 => { ctx.save(); ctx.globalAlpha *= ka; ctx.fillStyle = C.steel2; ctx.fillRect(x0 + 2, ly - 12, 10, 13); ctx.fillRect(x0 + 14, ly - 12, 10, 13); ctx.restore(); }, 'bands used');
}
/* (d): J(theta) / J max = c0 + c1 cos 4 theta + c2 sin 4 theta, exact */
function panelD(v) {
  const s = st(), a = v.jon, la = arrive(.12), J = th => s.J[0] + s.J[1] * Math.cos(4 * th) + s.J[2] * Math.sin(4 * th);
  sub('d', SC.x - 72, PS.y - 38, 'off-diagonal against angle', la);
  const ax = axes({x: JB.x, y: JB.y, w: JB.w, h: JB.h, xlim: [0, 90], ylim: [0, 1.05], xticks: [0, 45, 90], yticks: [0, 1],
    xlabel: '\\rm{rotation angle}\\ \\theta\\ (\\deg)', ylabel: 'J(\\theta)', ylabelGap: 34, tickSize: 16, labelSize: 17,
    progress: seg(.12, .35), alpha: a});
  const pts = []; for (let i = 0; i <= 180; i++) { const d = i / 2; pts.push([ax.X(d), ax.Y(J(d * Math.PI / 180))]); }
  const thd = s.th * 180 / Math.PI;
  ax.inside(() => {
    line([[ax.X(thd), JB.y + JB.h], [ax.X(thd), ax.Y(J(s.th))]], {color: C.guide, width: 1, dash: [5, 4], alpha: a * seg(.4, .3)});
    line(pts, {color: C.navy, width: 2.2, progress: seg(.25, .45), alpha: a});
  });
  dot(ax.X(v.ang * 180 / Math.PI), ax.Y(J(v.ang)), 5, {color: '#fff', fill: C.accent, width: 1.4, alpha: a * seg(.45, .25)});
}
function table(v) {
  const s = st(), a = arrive(.35) * lerp(.55, 1, v.ov), aw = a * lerp(.55, 1, v.den), {x0, x1, y} = TB;
  const cx = [x0 + 162, x0 + 218, x1 - 58, x1];          // right edges of SIR s1, SIR s2, rho s1, rho s2
  rule(x0, x1, y, 1.3, a);
  text('SIR (dB)', (cx[0] + cx[1]) / 2 - 22, y + 21, {size: 16, color: C.body, align: 'center', alpha: a});
  math('\\rm{correlation}\\ \\rho', (cx[2] + cx[3]) / 2 - 20, y + 21, {size: 16, color: C.body, align: 'center', alpha: a});
  [0, 1, 2, 3].forEach(c => math('s_' + (c % 2 + 1), cx[c], y + 43, {size: 16, color: C.body, align: 'right', alpha: a}));
  rule(x0, x1, y + 51, .8, a);
  const rows = [['kurtosis ICA', s.k], ['SOBI family', s.o], ['+ Wiener', s.w]];
  rows.forEach(([name, r], j) => {
    const yy = y + 71 + j * 24, al = j === 2 ? aw : a;
    text(name, x0, yy, {size: 16, alpha: al});
    if (r.sir) r.sir.forEach((t, c) => text(t, cx[c], yy, {size: 16, align: 'right', alpha: al}));
    r.rho.forEach((t, c) => text(t, cx[2 + c], yy, {size: 16, align: 'right', alpha: al}));
  });
  rule(x0, x1, y + 127, 1.3, a);
  math('\\rm{rotation}\\ \\theta^{*} = ' + num(s.th * 180 / Math.PI, 1) + '\\deg\\rm{:}\\ \\ ' + s.pair, x0, y + 149, {size: 16, color: C.body, alpha: arrive(.4)});
}
function controls() {
  const a = arrive(.4);
  text('SNR (dB)', SN.x - 8, SN.y + 19.5, {size: 16, color: C.body, align: 'right', alpha: a});
  D.snrs.forEach((v, i) => chip(SN.x + i * SN.pitch, SN.y, SN.w, SN.h, num(v, 0), null,
    {on: i === SEL, hover: HOV.snr === i, down: DOWN.snr === i}, arrive(.4 + .01 * i)));
  text('record', RC.x - 8, RC.y + 19.5, {size: 16, color: C.body, align: 'right', alpha: a});
  D.T.forEach((v, i) => chip(RC.x + i * RC.pitch, RC.y, RC.w, RC.h, v + ' s', null,
    {on: i === REC, hover: HOV.rec === i, down: DOWN.rec === i}, arrive(.45 + .02 * i)));
  // what the record length gives: the Welch segments K, and the bands found above the floor
  math(st().note, RC.x + D.T.length * RC.pitch + 14, RC.y + 19.5, {size: 16, color: C.muted, alpha: arrive(.45)});
}
function draw() {
  const {w, v} = view(), cur = cursor(w);
  stageRow(w.k, w.ph);
  panelA(v, cur);
  panelB(v, cur);
  panelC(v);
  panelD(v);
  table(v);
  controls();
  mixed(D.params, 18, H - 12, {size: 15, color: C.muted, alpha: seg(.5, .3)});
}
function status() {
  const s = st(), k = clock().k;
  return 'Stage ' + (k + 1) + ' of ' + NS + ', ' + STAGES[k][0] + '. SNR ' + D.snrs[SEL] + ' dB, ' + D.T[REC] + ' s record: SIR ' +
    s.o.sir.join(' and ') + ' dB here, ' + s.k.sir.join(' and ') + ' dB with kurtosis ICA; correlation after Wiener ' + s.w.rho.join(' and ') + '.';
}
const GS = group('stage', 'Stage of the method', STAGES.map((s, i) => ({aria: 'Stage ' + (i + 1) + ': ' + s[0]})),
  () => clock().k, j => chooseStage(j));
const GN = group('snr', 'Sensor SNR', D.snrs.map(v => ({aria: 'SNR ' + v + ' dB'})), () => SEL, i => chooseData(() => { SEL = i; }));
const GR = group('rec', 'Record length', D.T.map(v => ({aria: 'Record ' + v + ' s'})), () => REC, i => chooseData(() => { REC = i; }));
place(GN, D.snrs.map((_, i) => [SN.x + i * SN.pitch - (SN.pitch - SN.w) / 2, SN.y - 7, SN.pitch, SN.h + 14]),
      D.snrs.map((_, i) => [SN.x + i * SN.pitch, SN.y, SN.w, SN.h]));
place(GR, D.T.map((_, i) => [RC.x + i * RC.pitch - (RC.pitch - RC.w) / 2, RC.y - 7, RC.pitch, RC.h + 14]),
      D.T.map((_, i) => [RC.x + i * RC.pitch, RC.y, RC.w, RC.h]));
BANDS.push([SN.x - 80, SN.y - 10, SN.x + D.snrs.length * SN.pitch + 4, SN.y + SN.h + 7]);
BANDS.push([RC.x - 80, RC.y - 7, RC.x + D.T.length * RC.pitch + 4, RC.y + RC.h + 10]);
function reset() { TOUR0 = TOUR_START; JUMP = null; CHG = null; sync(); }
sync();
boot();
"""


# ------------------------------------------------------------------ the model, per record and SNR
def run():
    recs, states = {}, {}
    for T in L.RECORDS:
        R = L.record(T)
        recs[T] = R
        u, s = R["u"], R["s"]
        for snr in L.SNRS:
            sg = L.sigma(snr)
            Aug = L.augmented(sg)
            x = Aug @ u
            so = L.sobi_family(x, T, turn90=True)
            m = L.match(so["B"])
            k = L.kurtosis_ica(x)
            mk = L.match(k["B"])
            yk = k["B"] @ (x - x.mean(1, keepdims=True))
            perm = m["perm"]
            c = [float(so["yraw"][i] @ s[perm[i]] / (s[perm[i]] @ s[perm[i]])) for i in range(2)]
            # the Wiener stage is drawn in units of its own RMS (the noise it removed is gone)
            kw = math.sqrt(float(np.mean(so["yden"] ** 2)))
            cd = [float(so["yden"][i] @ s[perm[i]] / (s[perm[i]] @ s[perm[i]])) / kw for i in range(2)]
            states[T, snr] = dict(
                T=T, snr=snr, sg=sg, x=x, so=so, m=m, k=k, mk=mk,
                rho_o=L.scores(so["yraw"], s, m), rho_w=L.scores(so["yden"], s, m), rho_k=L.scores(yk, s, mk),
                WA=so["W"] @ Aug, F=L.rot(so["theta"]) @ so["W"] @ Aug, c=c, cd=cd, kx=L.kappa(Aug, u), kw=kw)
    return recs, states


DB0 = -35.0                                       # spectra as int8 in half decibels about -35 dB


def fmt_sir(v):
    return f"{v:.1f}".replace("-", "−")


def data(recs, states):
    rec_out, st_out = [], []
    kmax = [int(round(L.FMAX * L.WELCH[T] / L.FS)) for T in L.RECORDS]
    for ti, T in enumerate(L.RECORDS):
        pk, sc = L.i8pack(L.shown(recs[T]["u"]))
        rec_out.append(dict(u=pk, sc=sc))
        row = []
        for snr in L.SNRS:
            q = states[T, snr]
            so, m, mk = q["so"], q["m"], q["mk"]
            Lw, n = so["L"], kmax[ti]
            yd, ysc = L.i8pack(L.shown(so["yden"]) / q["kw"])
            spec = L.psd_db(np.array([so["S"][0, 0].real[:n + 1], so["S"][1, 1].real[:n + 1]]), Lw)
            spq = [common.i8(np.clip(np.round((r - DB0) * 2), -127, 127)) for r in spec]
            gq = [common.i8(np.round(np.asarray(g[:n + 1]) * 127)) for g in so["gains"]]
            lam = float(so["ev"][1]) if so["ev"][1] > 0 else 1.0
            G = so["G"]
            J = [(G[0, 0] + G[1, 1]) / 2 / lam, (G[0, 0] - G[1, 1]) / 2 / lam, G[0, 1] / lam]
            out = [m["out"][j] for j in range(2)]
            # the pairing the rotation gives, on the rotation's line; the bands and segments under it
            pair = (r"s_1 \to\ " + ("-" if m["sign"][out[0]] < 0 else "") + f"y_{out[0] + 1},\\ \\ "
                    r"s_2 \to\ " + ("-" if m["sign"][out[1]] < 0 else "") + f"y_{out[1] + 1}")
            note = str(len(so["chosen"])) + r"\rm{ bands;   }K = " + str(so["K"]) + r"\rm{ segments}"
            row.append(dict(
                sg=q["sg"], kx=q["kx"], kw=q["kw"], WA=q["WA"], F=q["F"], th=so["theta"], J=J, perm=m["perm"], c=q["c"], cd=q["cd"],
                yd=yd, ysc=ysc, sp=spq, g=gq, fl=[float(v) for v in L.psd_db(np.array(so["floors"]), Lw)],
                bands=[int(k) for k in so["chosen"] if k <= n],
                k=dict(sir=[fmt_sir(v) for v in mk["sir_src"]], rho=[f"{v:.3f}" for v in q["rho_k"]]),
                o=dict(sir=[fmt_sir(v) for v in m["sir_src"]], rho=[f"{v:.3f}" for v in q["rho_o"]]),
                w=dict(rho=[f"{v:.3f}" for v in q["rho_w"]]), pair=pair, note=note))
        st_out.append(row)
    params = [["t", "Welch: Hann, 50% overlap, 256, 1024, 2048 samples;  floor: the median;  bands: 4 standard errors "
                    "above it;  Wiener over-subtraction "], ["m", r"1 + 2/\sqrt{K}"]]
    return dict(recs=rec_out, dt=L.DECIM / L.FS, show=L.SHOW_T, A=L.A, snrs=list(L.SNRS), T=list(L.RECORDS),
                snr0=L.SNRS.index(SNR0), rec0=L.RECORDS.index(REC0), kmax=kmax,
                df=[L.FS / L.WELCH[T] for T in L.RECORDS], db0=DB0, st=st_out, params=params)


HIS = os.environ.get("NUMFIG_HIS_PAGES", "")        # a folder holding his two BSS pages, if at hand
HIS_M2 = "bss-2-sobi-wiener.html"


def his_corr(a, b):
    return float(a @ b / math.sqrt(float(a @ a) * float(b @ b) + 1e-30))


def his_sirof(B):
    G = B @ L.A
    v = []
    for i in range(2):
        a, b = G[i, 0] ** 2, G[i, 1] ** 2
        v.append(10 * math.log10(max(a, b) / max(min(a, b), 1e-12)))
    return v


def his_m2(u, s, snr, T):
    """His method 2 page, step for step: the 1 deg kurtosis baseline (uncentred covariance),
    the bands, the 0.5 deg joint diagonalization grid, his pairing, his SIR (the mean of the
    two outputs' dB), Wiener and standardized outputs. Returns his readout's numbers."""
    Aug = L.augmented(L.sigma(snr))
    x = Aug @ u
    N = x.shape[1]
    Wk, kb, Fk = L.his_kica_grid(u, Aug, 1.0, centre=False)
    Bk = L.rot(kb) @ Wk
    mk = L.his_match(Bk @ L.A)
    rhoK = [abs(his_corr(Bk[i] @ x, s[mk[i][0]])) for i in range(2)]
    Lw = L.WELCH[T]
    H = Lw // 2 + 1
    S, K = L.welch(x, Lw)
    f1, f2 = L.his_median(S[0, 0].real[1:]), L.his_median(S[1, 1].real[1:])
    a = S[0, 0].real[1:] - f1
    d = S[1, 1].real[1:] - f2
    b = S[0, 1].real[1:]
    ex = a / (f1 / math.sqrt(K)) + d / (f2 / math.sqrt(K))
    order = np.argsort(-ex, kind="stable")
    ch = order[ex[order] > 4]
    if len(ch) < 4:
        ch = order[:4]
    sa, sb, sd = max(a[ch].sum(), 1e-9), b[ch].sum(), max(d[ch].sum(), 1e-9)
    if sa * sd - sb * sb <= 0:
        sb = math.copysign(0.95 * math.sqrt(sa * sd), sb)
    W = L.whitener(sa, sb, sd)
    Ds = [W @ np.array([[a[k], b[k]], [b[k], d[k]]]) @ W.T for k in ch]
    best, bj, dg = 0.0, math.inf, -45.0
    while dg <= 45:
        R = L.rot(dg * math.pi / 180)
        J = sum((R @ Dk @ R.T)[0, 1] ** 2 for Dk in Ds)
        if J < bj:
            bj, best = J, dg * math.pi / 180
        dg += 0.5
    B = L.rot(best) @ W
    mt = L.his_match(B @ L.A)
    yraw = B @ x
    Sy, Ky = L.welch(yraw, Lw)
    over = 1 + 2 / math.sqrt(Ky)
    idx = np.arange(H)
    rhoA = []
    for i in range(2):
        nv = B[i, 0] ** 2 * f1 + B[i, 1] ** 2 * f2
        P = Sy[i, i].real
        g = np.maximum(0, P - over * nv) / (P + 1e-30)
        g = (g[np.maximum(0, idx - 1)] + 2 * g + g[np.minimum(H - 1, idx + 1)]) / 4
        yd = L.standardize(L.gain_apply(yraw[i], g, Lw))
        rhoA.append(abs(his_corr(yd, s[mt[i][0]])))
    return dict(sirA=float(np.mean(his_sirof(B))), sirK=float(np.mean(his_sirof(Bk))), rhoA=rhoA, rhoK=rhoK,
                th=best, chosen=len(ch))


def validate(recs, states, quick=False):
    from scipy import signal, stats
    out = []
    say = out.append
    q0 = states[REC0, SNR0]
    say("Figure 11, blind source separation, method 2, SOBI family and Wiener: check of tools/numfig/sp_bss_sobi.py")
    say("")
    say("MODEL (sp_bss_lib, shared with Figure 10; at 4 s the same record)")
    for T in L.RECORDS:
        R = recs[T]
        s = R["s"]
        say(f"  {T:2d} s: N = {R['N']:5d}, {len(R['imp']):3d} impacts, noise mulberry32({7 + T}); corr(s1, s2) {L.corr(s[0], s[1]):+.4f};"
            f" kurt s1 {np.mean(s[0] ** 4) - 3:+.3f}, s2 {np.mean(s[1] ** 4) - 3:+.3f}; Welch {L.WELCH[T]} samples,"
            f" K = {states[T, 0]['so']['K']} segments, {L.FS / L.WELCH[T]:.3f} Hz bins")
    say("  Method (his): Welch auto and cross spectra (periodic Hann, 50% overlap, no scaling: S_ij = mean conj(X_i) X_j);")
    say("  floor f_i = his median of S_ii over bins 1..L/2 (element floor(n/2) of the sorted values); a bin is a band if")
    say("  (S_11 - f_1)/(f_1/sqrt K) + (S_22 - f_2)/(f_2/sqrt K) > 4 (at least the best 4); M = sum over the bands of")
    say("  [[S_11 - f_1, Re S_12], [Re S_12, S_22 - f_2]]; W0 M W0' = I (his PCA convention), then W = W0 scaled so that")
    say("  W x has unit RMS (the scale is free); D_k = W0 M_k W0'; the rotation theta minimizing J = sum (R D_k R')_12^2,")
    say("  in closed form (h_k = ((D_k)_12, ((D_k)_22 - (D_k)_11)/2), J = v' G v, v = (cos 2 theta, sin 2 theta), v the")
    say("  eigenvector of G = sum h_k h_k' of the smaller eigenvalue), taken in [0, 90) deg (a quarter turn is the")
    say("  permutation); y = R W x; Wiener gain per output max(0, P - o N)/P, N = B_i1^2 f_1 + B_i2^2 f_2, o = 1 + 2/sqrt(K),")
    say("  smoothed [1 2 1]/4 over bins, applied through a zero-padded FFT with linear interpolation (his applyGain).")
    say("  Order and sign matched as in Figure 10; SIR per source from G = R W A; rho: Pearson correlation.")
    say("  Kurtosis ICA (the table's first row) is Figure 10's method, exact, on the same sensors.")
    say("")
    say("RESULTS (the figure's table: SIR s1, s2 in dB; rho s1, s2)")
    say("    T   SNR | kurtosis ICA               | SOBI family                | + Wiener      | bands  theta*")
    for T in L.RECORDS:
        for snr in L.SNRS:
            q = states[T, snr]
            say(f"   {T:2d} {snr:5d} | {q['mk']['sir_src'][0]:6.1f} {q['mk']['sir_src'][1]:6.1f} {q['rho_k'][0]:6.3f} {q['rho_k'][1]:6.3f} |"
                f" {q['m']['sir_src'][0]:6.1f} {q['m']['sir_src'][1]:6.1f} {q['rho_o'][0]:6.3f} {q['rho_o'][1]:6.3f} |"
                f" {q['rho_w'][0]:6.3f} {q['rho_w'][1]:6.3f} | {len(q['so']['chosen']):5d} {math.degrees(q['so']['theta']):7.2f}")
    say("")
    say("VALIDATION")
    # 1 Welch against scipy
    e_w = 0.0
    for T in L.RECORDS:
        q = states[T, 0]
        x, Lw = q["x"], L.WELCH[T]
        win = signal.get_window("hann", Lw, fftbins=True)
        for i in range(2):
            for j in range(2):
                f, P = signal.csd(x[i], x[j], fs=L.FS, window=win, nperseg=Lw, noverlap=Lw // 2, detrend=False,
                                  scaling="density", return_onesided=True)
                fac = np.full(len(f), 2.0)
                fac[0] = 1.0
                fac[-1] = 1.0
                mine = q["so"]["S"][i, j] * fac / (L.FS * np.sum(win ** 2))
                e_w = max(e_w, float(np.abs(mine - P).max() / np.abs(P).max()))
    say(f"  1. The Welch cross spectra against scipy.signal.csd (same window, overlap, density scaling): largest")
    say(f"     difference {e_w:.1e} of the largest value, all records and channel pairs at 0 dB.")
    # 2 the noise floor
    say("  2. The floor against the closed form: white noise of variance sigma^2 has E S_ii = sigma^2 sum w^2 =")
    say("     sigma^2 3L/8 (periodic Hann); a Welch value is that times chi^2_nu / nu, nu = 2K / (1 + 2 c^2 (K - 1)/K),")
    say("     c = 0.1667 the overlap correlation of Hann at 50% (Welch 1967), so the median sits at chi^2_nu median / nu.")
    say("     Where the noise fills every bin (-30 and -20 dB):")
    for T in L.RECORDS:
        for snr in (-30, -20):
            q = states[T, snr]
            K = q["so"]["K"]
            nu = 2 * K / (1 + 2 * 0.1667 ** 2 * (K - 1) / K)
            true = q["sg"] ** 2 * 3 * L.WELCH[T] / 8
            r = [f / true for f in q["so"]["floors"]]
            say(f"     {T:2d} s, {snr:4d} dB: floor / sigma^2 3L/8 = {r[0]:.3f}, {r[1]:.3f}; chi^2 median / nu = "
                f"{stats.chi2.median(nu) / nu:.3f} (nu = {nu:.1f})")
    # 3 whitening and the residual
    e_m = max(float(np.abs(q["so"]["W0"] @ q["so"]["Msum"] @ q["so"]["W0"].T - np.eye(2)).max()) for q in states.values())
    rr = [float(q["so"]["ev"][0] / q["so"]["ev"][1]) for q in states.values()]
    say(f"  3. Noise-corrected whitening: |W0 M W0' - I| <= {e_m:.1e} over all 45 states. Off-diagonal energy left")
    say(f"     after the rotation, J_min / J_max: {np.median(rr):.1e} (median of the 45 states), "
        f"{states[REC0, SNR0]['so']['ev'][0] / states[REC0, SNR0]['so']['ev'][1]:.1e} at 4 s, 0 dB.")
    # 4 joint diagonalization checks
    rng = np.random.default_rng(5)
    errs, jmins = [], []
    for trial in range(20):
        phi = rng.uniform(-np.pi / 4, np.pi / 4)
        Qm = L.rot(phi).T
        Dk = [Qm @ np.diag(rng.normal(size=2) * 3) @ Qm.T for _ in range(9)]
        th, G, ev = L.jd_angle(Dk)
        errs.append(abs(math.degrees(L.wrap45(th - phi))))
        jmins.append(sum((L.rot(th) @ D @ L.rot(th).T)[0, 1] ** 2 for D in Dk))
    say(f"  4. Joint diagonalization, the closed form:")
    say(f"     a. 20 sets of nine matrices Q diag(l_k) Q', Q a random rotation, exactly diagonalizable: the rotation")
    say(f"        found is Q' to {max(errs):.1e} deg, the off-diagonal left {max(jmins):.1e}.")
    Dk = [Qm @ np.diag(rng.normal(size=2)) @ Qm.T for _ in range(2)]
    ev2, vec2 = np.linalg.eig(np.linalg.solve(Dk[0], Dk[1]))
    th_g = math.atan2(vec2[1, 0], vec2[0, 0])
    th_c, _, _ = L.jd_angle(Dk)
    e_ge = abs(math.degrees(L.wrap45(th_g - th_c)))            # modulo 90 deg: order and sign
    say(f"     b. For a pair, the generalized eigenvectors of (D_1, D_2) give the same rotation: {e_ge:.1e} deg.")
    from scipy.optimize import minimize_scalar
    e_bf = 0.0
    for key in [(4, 0), (4, -10), (16, 0), (64, -15), (64, 20)]:
        Ds = states[key]["so"]["Ds"]
        Jf = lambda th: sum((L.rot(th) @ D @ L.rot(th).T)[0, 1] ** 2 for D in Ds)
        grid = np.deg2rad(np.arange(-45, 45, 0.01))
        g0 = grid[int(np.argmin([Jf(t_) for t_ in grid]))]
        r = minimize_scalar(Jf, bounds=(g0 - 2e-4, g0 + 2e-4), method="bounded", options=dict(xatol=1e-12))
        e_bf = max(e_bf, abs(math.degrees(L.wrap45(r.x - states[key]["so"]["theta"]))))
    say(f"     c. On the figure's own band matrices (5 states), a brute-force minimization of J (matrix products,")
    say(f"        0.01 deg grid then Brent): within {e_bf:.1e} deg of the closed form.")
    # 5 Wiener
    q = q0
    so, m, s = q["so"], q["m"], recs[REC0]["s"]
    n = recs[REC0]["n"]
    parts = []
    e_lin = 0.0
    for i in range(2):
        G = m["G"]
        comp = [G[i, 0] * s[0], G[i, 1] * s[1], q["sg"] * (so["B"][i] @ n)]
        filt = [L.gain_apply(c_, so["gains"][i], so["L"]) for c_ in comp]
        e_lin = max(e_lin, float(np.abs(sum(filt) - so["yden"][i]).max()))
        j = m["perm"][i]
        sig_b, nse_b = float(np.mean(comp[j] ** 2)), float(np.mean(comp[2] ** 2))
        sig_a, nse_a = float(np.mean(filt[j] ** 2)), float(np.mean(filt[2] ** 2))
        parts.append((j, 10 * math.log10(sig_b / nse_b), 10 * math.log10(sig_a / nse_a)))
    say(f"  5. Wiener, linear for its fixed gains: filtering each part of an output (its source, the other source, its")
    say(f"     noise) and adding them gives the filtered output to {e_lin:.1e}. At 4 s, 0 dB the output SNR rises from")
    for j, b_, a_ in sorted(parts):
        say(f"     {b_:.1f} to {a_:.1f} dB for s{j + 1};")
    nvr = [so["nv"][i] / (q["sg"] ** 2 * 3 * so["L"] / 8 * (so["B"][i] @ so["B"][i])) for i in range(2)]
    say(f"     the noise level each gain assumes, B_i1^2 f_1 + B_i2^2 f_2, against the exact sigma^2 |B_i|^2 3L/8: "
        f"{nvr[0]:.3f}, {nvr[1]:.3f}.")
    # 6 his page
    if not quick:
        path = os.path.join(HIS, HIS_M2) if HIS else ""
        if path and os.path.isfile(path):
            cases = [(4, -10), (4, 0), (4, 10), (16, 0), (16, -10), (64, 0), (64, -15)]
            acts = []
            for T, snr in cases:
                acts.append(f"(() => {{ const l = document.getElementById('len'); l.value = '{T}'; l.dispatchEvent(new Event('change')); "
                            f"const e = document.getElementById('noise'); e.value = '{snr}'; e.dispatchEvent(new Event('input')); "
                            f"document.querySelectorAll('#dots button')[6].click(); }})()")
            got = L.his_page(path, acts, "document.getElementById('q').textContent", wait=2500)
            ok = 0
            say("  6. His page (method 2) run headless, against this port of his whole pipeline (his 1 deg kurtosis")
            say("     baseline, his 0.5 deg rotation grid, his pairing and his SIR, the mean of the two outputs' dB):")
            for (T, snr), g in zip(cases, got):
                h = his_m2(recs[T]["u"], recs[T]["s"], snr, T)
                txt = (f"Separation (SIR): {h['sirA']:.0f} dB here, {h['sirK']:.0f} dB with kurtosis ICA. Correlation with the "
                       f"true sources: {h['rhoA'][0]:.2f} and {h['rhoA'][1]:.2f} (kurtosis ICA: {h['rhoK'][0]:.2f} and {h['rhoK'][1]:.2f}).")
                same = txt == g.strip()
                ok += same
                say(f"     {T:2d} s {snr:4d} dB: {'same' if same else 'DIFFERENT'}: {g.strip()}")
                if not same:
                    say(f"        port: {txt}")
            say(f"     {ok} of {len(cases)} readouts identical character for character.")
            # the figure against his grid
            dmax = 0.0
            for (T, snr) in cases:
                h = his_m2(recs[T]["u"], recs[T]["s"], snr, T)
                dmax = max(dmax, abs(math.degrees(L.wrap45(h["th"] - states[T, snr]["so"]["theta"]))))
            say(f"     His 0.5 deg grid against the closed form on these cases: within {dmax:.3f} deg (at most 0.25).")
        else:
            say("  6. His page: not at hand (set NUMFIG_HIS_PAGES to the folder holding bss-2-sobi-wiener.html).")
    # 7 why method 1 fails at low SNR: ordinary whitening
    say("  7. Why kurtosis ICA breaks at low SNR whatever the record: it whitens with the noisy covariance")
    say("     C = A A' + sigma^2 I, after which the two source directions are no longer at 90 deg, and no rotation can")
    say("     separate both (the best leaves 20 log10 cot((90 - a)/2) dB in each output, a the angle between them):")
    for snr in (-10, -5, 0, 5, 10, 20, 30):
        C = L.A @ L.A.T + L.sigma(snr) ** 2 * np.eye(2)
        V = L.whitener(C[0, 0], C[0, 1], C[1, 1]) @ L.A
        c1, c2 = V[:, 0] / np.linalg.norm(V[:, 0]), V[:, 1] / np.linalg.norm(V[:, 1])
        ang = math.degrees(math.acos(abs(c1 @ c2)))
        cap = 20 * math.log10(1 / math.tan(math.radians((90 - ang) / 2)))
        say(f"     {snr:4d} dB: a = {ang:5.1f} deg, at most {cap:5.1f} dB")
    say("     Noise-corrected whitening takes the floors off before whitening, so the directions stay at 90 deg as")
    say("     long as the floors and the bands are right.")
    # 8 other noise records
    if not quick:
        say("  8. Fifty other noise records (mulberry32(1000 + i)), 4 s: median and 10 to 90% range of the worse")
        say("     output's SIR and of the mean correlation, and where the record shown falls (percentile, worse SIR):")
        s4 = recs[4]["s"]
        for snr in (-10, -5, 0, 10):
            rows = []
            for i in range(50):
                nn = L.noise(recs[4]["N"], 1000 + i)
                x = L.A @ s4 + L.sigma(snr) * nn
                so2 = L.sobi_family(x, 4, turn90=True)
                m2 = L.match(so2["B"])
                k2 = L.kurtosis_ica(x)
                mk2 = L.match(k2["B"])
                rows.append([min(m2["sir_src"]), np.mean(L.scores(so2["yden"], s4, m2)),
                             min(mk2["sir_src"]), np.mean(L.scores(k2["B"] @ (x - x.mean(1, keepdims=True)), s4, mk2))])
            rows = np.array(rows)
            p = lambda c_: np.percentile(rows[:, c_], [10, 50, 90])
            a0, a1, a2, a3 = p(0), p(1), p(2), p(3)
            qq = states[4, snr]
            pr = 100 * np.mean(rows[:, 0] <= min(qq["m"]["sir_src"]))
            say(f"     {snr:4d} dB: SOBI {a0[1]:5.1f} dB ({a0[0]:5.1f} to {a0[2]:5.1f}), Wiener rho {a1[1]:.3f} ({a1[0]:.3f} to {a1[2]:.3f});"
                f" kurtosis ICA {a2[1]:5.1f} dB ({a2[0]:5.1f} to {a2[2]:5.1f}), rho {a3[1]:.3f}; shown at percentile {pr:.0f}")
    # 9 the page
    exprs = [f"Array.from(RECS[{r}][{c}])" for r in range(3) for c in range(4)]
    exprs += ["(() => { const s = D.st[0][%d]; return [0, 1, 2, 3].map(i => s.J[0] + s.J[1] * Math.cos(4 * i * .3) + s.J[2] * Math.sin(4 * i * .3)); })()"
              % L.SNRS.index(SNR0)]
    exprs += ["Array.from(yden()[0])", "Array.from(yden()[1])"]
    got = L.page_eval(NAME, "", exprs)
    e_u = 0.0
    for r, T in enumerate(L.RECORDS):
        uu = L.shown(recs[T]["u"])
        for c in range(4):
            e_u = max(e_u, float(np.abs(np.array(got[4 * r + c]) - uu[c]).max() / np.abs(uu[c]).max()))
    G = q0["so"]["G"]
    lam = q0["so"]["ev"][1]
    jt = [float(L.jcurve(G, i * .3) / lam) for i in range(4)]
    e_j = float(np.abs(np.array(got[12]) - jt).max())
    yd = L.shown(q0["so"]["yden"]) / q0["kw"]
    e_y = max(float(np.abs(np.array(got[13 + i]) - yd[i]).max()) for i in range(2))
    say(f"  9. The page: u decoded within {e_u:.4f} of each channel's largest value (int8); J(theta) from its three")
    say(f"     numbers within {e_j:.1e} of numpy; the Wiener outputs it draws within {e_y:.3f} (int8, RMS 1).")
    say("")
    say("DISPLAY")
    say("  As Figure 10: every stage but Wiener is a 2 x 4 matrix on u; between stages the matrices are interpolated,")
    say("  the diagonalizing rotation is a true rotation. Each stage in units of its RMS (sensors x kappa, Wiener x its")
    say("  own RMS, both printed at the axes). (c) one-sided PSD 2 S / (fs sum w^2) in dB re 1 per Hz (the signals in")
    say("  units of the sources' standard deviation), one scale (-70 to 20 dB) for every state so that the floor visibly")
    say("  rises with the noise; bins 1 to 40 Hz; the bands up to 40 Hz shaded; the gains under them on the same")
    say("  frequency axis (channel 1 = output 1); each band shaded on its own bin with a white gap (16 % of a bin, 1 to")
    say("  3.5 units) between neighbours, so that nine contiguous bands at 4 s read as nine. (d) J(theta) / J_max over")
    say("  one period, 0 to 90 degrees; theta* printed under the table. The spectra are int8 in half decibels, the gains")
    say("  int8 in 1/127.")
    say(f"  W x H = 1000 x {H_PAGE}: the SNR and record chips in two rows under (c), the parameter line 24 units under them;")
    say("  beside the record chips, what the record gives: the bands found and the Welch segments K. The table, its")
    say("  readout, the legends and the labels at 16 units, the parameter line at 15.")
    say("  No 'new noise' control: his page draws one seeded record per length (mulberry32(7 + T)); item 8 shows the")
    say("  spread over other records.")
    return out


def build():
    recs, states = run()
    D = data(recs, states)
    common.build_html(NAME, TITLE, ARIA, 1000, H_PAGE, D, JS)
    for T in L.RECORDS:
        for snr in L.SNRS:
            q = states[T, snr]
            print(f"T {T:2d} SNR {snr:4d}: SOBI SIR {q['m']['sir_src'][0]:5.1f} {q['m']['sir_src'][1]:5.1f} rho "
                  f"{q['rho_o'][0]:.3f} {q['rho_o'][1]:.3f} Wiener {q['rho_w'][0]:.3f} {q['rho_w'][1]:.3f} | "
                  f"KICA SIR {q['mk']['sir_src'][0]:5.1f} {q['mk']['sir_src'][1]:5.1f} rho {q['rho_k'][0]:.3f} {q['rho_k'][1]:.3f}")
    return recs, states, D


STAGE_TIMES = []
for _k in range(7):
    STAGE_TIMES += [round(_k * 5.2 + d, 3) for d in (0.15, 0.4, 0.7, 1.6, 4.9)]
STAGE_TIMES += [36.55, 36.8, 37.2]


def main():
    quick = "--quick" in sys.argv
    recs, states, D = build()
    png = common.still(NAME)
    print("still:", png)
    queries = [f"snr={v}&len={T}" for T in L.RECORDS for v in L.SNRS]
    faults, n, errs = L.check_states(NAME, queries, STAGE_TIMES)
    print(f"overlap over {len(queries)} states x {len(STAGE_TIMES) + 1} moments: {n} drawn, {len(faults)} faults, errors {errs}")
    for f in faults[:40]:
        print("  ", f)
    steps = [
        ("intro over, playing", "", "playing === true && t > 1.2", 1600),
        ("stage chip 5 chosen, still playing", "click:.nfb[aria-label='Stage 5: diagonalize']", "clock().k === 4 && playing === true", 300),
        ("record chip 64 s chosen, still playing", "click:.nfb[aria-label='Record 64 s']", "REC === 2 && playing === true", 400),
        ("SNR chip -10 dB chosen, still playing", "click:.nfb[aria-label='SNR -10 dB']", "SEL === D.snrs.indexOf(-10) && playing === true", 300),
        ("arrow key moves the SNR", "key:ArrowLeft", "SEL === D.snrs.indexOf(-15)", 200),
        ("canvas click away from the controls pauses", "(() => { const r = cv.getBoundingClientRect(); "
         "cv.dispatchEvent(new MouseEvent('click', {bubbles: true, clientX: r.left + r.width * .3, clientY: r.top + r.height * .25})); })()",
         "playing === false", 150),
        ("paused, a stage chip shows it complete", "click:.nfb[aria-label='Stage 7: Wiener']", "clock().k === 6 && where().e > .99 && playing === false", 150),
        ("click between the chip rows does not toggle", "(() => { const r = cv.getBoundingClientRect(); "
         f"cv.dispatchEvent(new MouseEvent('click', {{bubbles: true, clientX: r.left + r.width * {150 / 1000}, clientY: r.top + r.height * {655 / H_PAGE}}})); }})()",
         "playing === false", 150),
    ]
    fails, errs2 = L.interact(NAME, steps)
    glide_acts = [(t0, a) for t0 in (2.0, 7.0, 12.5, 17.0, 22.5, 27.5, 33.0, 36.3)
                  for a in [f"chooseStage({j})" for j in range(7)]
                  + [f"chooseData(() => {{ SEL = {i}; }})" for i in (0, 6, 9, 14)]
                  + [f"chooseData(() => {{ REC = {r}; }})" for r in (0, 1, 2)]]
    ng, gfaults = L.check_glides(NAME, glide_acts)
    print(f"glides: {ng} frames, {len(gfaults)} faults", gfaults[:10])
    print("interaction failures:", fails, "errors:", errs2)
    lines = validate(recs, states, quick)
    lines += ["", "CHECKS OF THE PAGE",
              f"  Overlap (engine ?overlap): the poster and every 0.25 s up to it (common.still), and {len(queries)} states",
              f"  (?snr= x ?len=) x {len(STAGE_TIMES) + 1} moments across the seven stages and the loop back: {n} frames, "
              f"{len(faults)} faults.",
              "  Through the glides a reader starts (a stage chosen, an SNR or record chosen, while playing, at",
              f"  moments across the tour, each glide drawn at 11 moments over 1.2 s): {ng} frames, {len(gfaults)} faults.",
              f"  In a browser: {len(steps) - len(fails)} of {len(steps)} interactions as intended (stage, SNR and record chips",
              "  never pause the figure, arrow keys move the choice, a click on open ground pauses, a paused choice",
              f"  shows the stage complete); console errors: {len(errs) + len(errs2)}.",
              f"  Page {os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.html')) / 1024:.0f} KB, poster "
              f"{os.path.getsize(os.path.join(common.ANIM, 'nf-' + NAME + '.webp')) / 1024:.0f} KB."]
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(common.HERE, "sp_bss_sobi.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)


if __name__ == "__main__":
    main()
