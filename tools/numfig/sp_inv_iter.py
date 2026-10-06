"""Figure 5 of the signal processing document: solving by iterating, and
semi-convergence (his "Inverse Problems and Regularization" section, redrawn
from his page iterative-solvers-animation.html).

The problem is Figure 4's (sp_inv_lib): the same blur G, the same cause m and
the same data d = G m + e (noise draw 1 at 0.1, 1 or 10 % of max |G m|), now
solved by iterating from m = 0 instead of through the SVD:
    Landweber (gradient descent on |G m - d|^2 / 2, step omega = 1 / s_1^2):
        m_k = m_{k-1} + omega G^T (d - G m_{k-1}); in closed form through the SVD
        it is the filtered sum with f_i = 1 - (1 - omega s_i^2)^k (checked against
        the iteration itself in the check file);
    CGLS (conjugate gradients for least squares), run for real: 50 iterations.
Every Landweber k is an integer: its curves pass through the iterates only
(every k to 100, then 600 rounded log-spaced k up to 10^8). The page draws the
iterate the reader picks by the filtered sum (Landweber) or from CGLS's own
iterates (their SVD coefficients, float64), checked against numpy.

Panels: (a) the current iterate against m; (b) the iterate as a filter: the
Picard plot of Figure 4 and, under it, the iterate's effective filter factors
f_i = s_i (v_i^T m_k) / (u_i^T d); (c) the error against the truth for both
solvers and the best Tikhonov error (semi-convergence); (d) the residual
against the noise level, where the discrepancy principle stops. Untouched, the
figure runs Landweber from k = 1 to 10^8, then CGLS from 1 to 50. Query keys
choose a state: m=lw|cgls, k=<iteration>, nz=0|1|2, run=1.

Run: python tools/numfig/sp_inv_iter.py [--verify]  (writes the page, the still
and the check file; prints the key numbers).
"""
import os
import sys

import numpy as np

import common
import sp_inv_lib as L

NAME = "sp-inv-iter"
W, H = 1000, 700
TITLE = "Figure 5: Solving by iterating, where the iteration count is the regularization parameter"
ARIA = ("The blurred, noisy measurement of Figure 4 solved by iterating from zero, by Landweber (gradient descent) "
        "and by conjugate gradients (CGLS). The iterate first gains the true shape, then noise: its error against the "
        "truth falls and rises again while the residual keeps falling, so the iteration count acts as the "
        "regularization parameter. CGLS reaches its lowest error in 14 iterations, Landweber in 177. The solver, the "
        "iteration and the noise level can be chosen.")

JS = L.JS_LIB + r"""
const D = DATA;
const OMEGA = D.omega, KL = D.klmax, KC = D.kcmax;          // Landweber: k to 10^8; CGLS: 50 iterations
const SETS = D.sets.map(q => ({ ...q, d: b64f32(q.d), beta: b64f64(q.beta), cc: b64f64(q.cc),
  lk: b64f32(q.lk), lerr: b64f32(q.lerr), lrho: b64f32(q.lrho), cerr: b64f64(q.cerr), crho: b64f64(q.crho) }));
const SOLV = ['Landweber', 'CGLS'];
/* Landweber's filter after k steps: 1 - (1 - omega s^2)^k, without cancellation */
function lwFilt(k) {
  const f = new Float64Array(NC);
  for (let j = 0; j < NC; j++) { const q = 1 - OMEGA * SV[j] * SV[j]; f[j] = q <= 0 ? 1 : -Math.expm1(k * Math.log1p(-OMEGA * SV[j] * SV[j])); }
  return f;
}
/* the iterate: its coefficients c (m = V c), its filter factors, residual, norm and error */
function iterate(o, S) {
  if (o.m === 0) { const f = lwFilt(o.k); return { f, ...est(f, S.beta) }; }
  const c = S.cc.subarray((o.k - 1) * NC, o.k * NC), f = new Float64Array(NC);
  let r2 = 0, n2 = 0, e2 = 0;
  for (let j = 0; j < NC; j++) {
    f[j] = c[j] * SV[j] / S.beta[j];
    r2 += (S.beta[j] - SV[j] * c[j]) ** 2; n2 += c[j] * c[j]; e2 += (c[j] - TV[j]) ** 2;
  }
  return { f, c, rho: Math.sqrt(r2), eta: Math.sqrt(n2), err: Math.sqrt(e2) / MNORM };
}
const kfmt = k => k < 1000 ? String(k) : String(k).replace(/\B(?=(\d{3})+(?!\d))/g, ',');

/* ================================================ the reader's choices (explicit state)
   ST = null: the tour. Else {m: 0 Landweber, 1 CGLS; nz; kl, kc: each solver's iteration;
   run: the iteration running on {t0, l0} (log10 k at t0)} */
let ST = null;
function reset() { ST = null; UI.hov = UI.down = UI.drag = UI.press = ''; }
const T0 = .6, RL = 14, RC = 15, HD = 2.6, HE = 2.6;                    // runs, the pause at the discrepancy stop, the hold at the end
const RATE_L = D.lwdec / RL, STEP_C = RC / KC;                               // decades of k per s; s per CGLS step
const runK = (m, t0, l0) => m === 0 ? Math.round(Math.pow(10, Math.min(D.lwdec, l0 + RATE_L * (t - t0))))
                                    : Math.min(KC, Math.round(Math.pow(10, l0)) + Math.floor((t - t0) / STEP_C));
/* the tour (1 % noise): Landweber runs from k = 1, pauses at its discrepancy stop, runs on to 10^8 and holds;
   then CGLS the same from 1 to 50 */
const S1 = SETS[1], LD = Math.log10(S1.ldp);
const TL = [LD / RATE_L, HD, (D.lwdec - LD) / RATE_L, HE], TC = [(S1.cdp - 1) * STEP_C, HD, (KC - S1.cdp) * STEP_C, HE];
const PER = [...TL, ...TC].reduce((a, b) => a + b);
function tour() {
  const base = { nz: 1, kl: 1, kc: S1.cdp, run: null };
  if (t < T0) return { ...base, m: 0 };
  let c = (t - T0) % PER, c0 = t - c;
  if (c < TL[0]) return { ...base, m: 0, run: { t0: c0, l0: 0 } };
  if ((c -= TL[0]) < TL[1]) return { ...base, m: 0, kl: S1.ldp };
  if ((c -= TL[1]) < TL[2]) return { ...base, m: 0, run: { t0: t - c, l0: LD } };
  if ((c -= TL[2]) < TL[3]) return { ...base, m: 0, kl: KL };
  if ((c -= TL[3]) < TC[0]) return { ...base, m: 1, kl: KL, kc: 1, run: { t0: t - c, l0: 0 } };
  if ((c -= TC[0]) < TC[1]) return { ...base, m: 1, kl: KL };
  if ((c -= TC[1]) < TC[2]) return { ...base, m: 1, kl: KL, run: { t0: t - c, l0: Math.log10(S1.cdp) } };
  return { ...base, m: 1, kl: KL, kc: KC };
}
function now() {
  const s = ST || tour(), o = { m: s.m, nz: s.nz, kl: s.kl, kc: s.kc, run: false };
  if (s.run) {
    const k = runK(s.m, s.run.t0, s.run.l0);
    if (s.m === 0) o.kl = k; else o.kc = k;
    o.run = s.m === 0 ? k < KL : k < KC;
  }
  o.k = o.m === 0 ? o.kl : o.kc;
  return o;
}
function hold() {
  if (ST) return;
  const s = tour(), o = now();
  ST = { m: o.m, nz: o.nz, kl: o.kl, kc: o.kc, run: o.run ? s.run : null };
}
function freeze() { const o = now(); ST.kl = o.kl; ST.kc = o.kc; ST.run = null; }
const moves = () => !REDUCED && !STILL;
function choose(f) { hold(); f(); redraw(); }

/* ================================================ the controls */
const ROW1 = 14, ROW2 = 56, CHH = 28, SLY = ROW2 + 14;
const SL = { x0: 50, x1: 318 };
let LAY = null;
function layout() {
  if (LAY) return LAY;
  const L = { r1: [], r2: [] };
  let x = 20 + tw('solver', 16) + 10;
  L.solver = x - 10;
  SOLV.forEach((s, i) => { const w = Math.max(46, tw(s, 16) + 22); L.r1.push({ id: 'm' + i, x, w }); x += w + 6; });
  x += 24; L.noise = x; x += tw('noise', 16) + 10;
  D.names.forEach((s, i) => { L.r1.push({ id: 'n' + i, x, w: 52 }); x += 58; });
  x = 532;
  for (const [id, s] of [['run', 'iterate'], ['dp', 'discrepancy principle']]) { const w = tw(s, 16) + 22; L.r2.push({ id, x, w }); x += w + 8; }
  return (LAY = L);
}
function mkChip(g, y, label, on, act, off = () => false, extra = {}) {
  const h = (UI.list.find(c => c.id === g.id) || {});
  Object.assign(h, { id: g.id, kind: 'chip', x: g.x, y, w: g.w, h: CHH, hit: [g.x - 3, y - 6, g.x + g.w + 3, y + CHH + 6],
                     label, on, act, off }, extra);
  if (!UI.list.includes(h)) UI.list.push(h);
}
const uOfK = (m, k) => m === 0 ? Math.log10(k) / D.lwdec : (k - 1) / (KC - 1);
const kOfU = (m, u) => m === 0 ? Math.round(Math.pow(10, u * D.lwdec)) : Math.round(1 + u * (KC - 1));
function buildControls() {
  const L = layout(), at = id => L.r1.find(g => g.id === id) || L.r2.find(g => g.id === id);
  SOLV.forEach((s, i) => mkChip(at('m' + i), ROW1, () => s, () => now().m === i,
    () => choose(() => { const r = !!ST.run; freeze(); ST.m = i; if (r) ST.run = { t0: t, l0: Math.log10(i === 0 ? ST.kl : ST.kc) }; }),
    () => false, { aria: () => 'Solver: ' + (i ? 'conjugate gradients for least squares (CGLS)' : 'Landweber, gradient descent') }));
  D.names.forEach((s, i) => mkChip(at('n' + i), ROW1, () => s, () => now().nz === i, () => choose(() => { ST.nz = i; }),
    () => false, { aria: () => 'Noise level ' + s + ' of the largest blurred value' }));
  mkChip(at('run'), ROW2, () => 'iterate', () => now().run, () => choose(() => {
    const o = now();
    if (o.run) { freeze(); return; }
    const k0 = (o.m === 0 ? o.kl >= KL : o.kc >= KC) ? 1 : o.k;
    freeze(); ST.run = { t0: t, l0: Math.log10(k0) };
    if (!playing) setPlay(true);
  }), () => !moves(), { toggle: true, aria: () => 'Run the iterations on from the one shown' });
  mkChip(at('dp'), ROW2, () => 'discrepancy principle', () => { const o = now(); return !o.run && o.k === (o.m === 0 ? SETS[o.nz].ldp : SETS[o.nz].cdp); },
    () => choose(() => { freeze(); const S = SETS[ST.nz]; if (ST.m === 0) ST.kl = S.ldp; else ST.kc = S.cdp; }),
    () => false, { aria: () => 'Stop at the discrepancy principle: the first iteration whose residual is at most the noise level' });
  const sl = UI.list.find(c => c.id === 'sl') || { id: 'sl', kind: 'slider' };
  Object.assign(sl, { x0: SL.x0, x1: SL.x1, y: SLY, hit: [SL.x0 - 14, SLY - 21, SL.x1 + 14, SLY + 21], off: () => false,
    ticks: now().m === 0 ? [0, 1, 2, 3, 4, 5, 6, 7, 8].map(v => v / 8) : [1, 10, 20, 30, 40, 50].map(k => (k - 1) / (KC - 1)),
    get: () => { const o = now(); return uOfK(o.m, o.k); },
    set: v => choose(() => { freeze(); if (ST.m === 0) ST.kl = kOfU(0, v); else ST.kc = kOfU(1, v); }),
    keys: e => {
      const o = now(), big = e.key === 'PageUp' || e.key === 'PageDown';
      const dd = { ArrowRight: 1, ArrowUp: 1, PageUp: 1, ArrowLeft: -1, ArrowDown: -1, PageDown: -1 }[e.key];
      if (!dd && e.key !== 'Home' && e.key !== 'End') return false;
      choose(() => {
        freeze();
        if (ST.m === 0) ST.kl = e.key === 'Home' ? 1 : e.key === 'End' ? KL
          : big ? clamp(Math.round(o.kl * (dd > 0 ? 10 : .1)), 1, KL) : clamp(dd > 0 ? Math.max(o.kl + 1, Math.round(o.kl * 1.05)) : Math.min(o.kl - 1, Math.round(o.kl / 1.05)), 1, KL);
        else ST.kc = e.key === 'Home' ? 1 : e.key === 'End' ? KC : clamp(o.kc + dd * (big ? 10 : 1), 1, KC);
      });
      return true;
    },
    aria: () => 'Iteration of ' + SOLV[now().m],
    valueText: () => { const o = now(); return 'iteration ' + o.k + ', error ' + (100 * iterate(o, SETS[o.nz]).err).toPrecision(3) + ' percent'; } });
  if (!UI.list.includes(sl)) UI.list.push(sl);
}
UI.ground = (X, Y) => Y < ROW2 + CHH + 12;
function controls(o, a) {
  buildControls();
  const L = layout();
  text('solver', L.solver, ROW1 + 19, { size: 16, color: C.body, align: 'right', alpha: a });
  text('noise', L.noise, ROW1 + 19, { size: 16, color: C.body, alpha: a });
  for (const c of UI.list) if (c.kind === 'chip') drawChip(c, a);
  drawSlider(ctlById('sl'), a);
  math('k', 22, SLY + 6, { size: 18, alpha: a });
  math('k = ' + kfmt(o.k), SL.x1 + 22, SLY + 6, { size: 16, alpha: a });
}

/* ================================================ the panels */
const PA = { x: 88, y: 126, w: 364, h: 192 }, PB = { x: 576, y: 126, w: 364, h: 140 }, PF = { x: 576, y: 274, w: 364, h: 44 };
const PC = { x: 88, y: 416, w: 364, h: 192 }, PD = { x: 576, y: 416, w: 364, h: 192 };
const curve = (A, ys, lo = -1e9, hi = 1e9) => Array.from(ys, (v, i) => [A.X(XC[i]), A.Y(clamp(v, lo, hi))]);
const mk = {
  line: (col, w, dash) => (x, y, a) => line([[x - 12, y], [x + 12, y]], { color: col, width: w, dash, alpha: a }),
  dline: (col, w, fill) => (x, y, a) => { line([[x - 12, y], [x + 12, y]], { color: col, width: w, alpha: a }); dot(x, y, 2.6, { color: col, fill, width: 1, alpha: a }); },
  dot: (col, fill, r = 3) => (x, y, a) => dot(x, y, r, { color: col, fill, width: 1.2, alpha: a }),
  ring: r => (x, y, a) => dot(x, y, r, { color: C.ink, fill: null, width: 1.5, alpha: a }),
  vbar: col => (x, y, a) => line([[x, y - 8], [x, y + 8]], { color: col, width: 1.2, dash: [5, 4], alpha: a }),
};
function panelA(o, S, I, mh) {
  sub('a', 20, PA.y - 14, 'current iterate', lab(0));
  const A = axes({ ...PA, xlim: [0, 1], ylim: [-0.6, 1.6], xticks: [0, .2, .4, .6, .8, 1], yticks: [-0.5, 0, .5, 1, 1.5],
                   xfmt: v => v === 1 || v === 0 ? fmt(v) : v.toFixed(1), yfmt: v => v === 0 ? '0' : Number.isInteger(v) ? fmt(v) : v.toFixed(1).replace('-', '−'),
                   xlabel: '\\rm{position}\\ x', ylabel: '\\rm{amplitude}', ylabelGap: 50, tickSize: 16, progress: seg(0, .35) });
  A.inside(() => {
    line([[PA.x, A.Y(0)], [PA.x + PA.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.1, .3) });
    line(curve(A, MT), { color: C.ink, width: 1.8, progress: seg(.08, .4) });
    line(curve(A, mh, -20, 20), { color: C.accent, width: 2.4, progress: seg(.16, .45) });
  });
  const ra = lab(.5);
  math('\\rm{error}\\ ‖m_k - m‖/‖m‖ = ' + pctv(I.err), PA.x + PA.w, PA.y - 14, { size: 16, align: 'right', alpha: ra });
  legend(PA.x + PA.w - 8, PA.y + 7, [[[mk.line(C.ink, 1.8), '\\rm{true cause }m'], [mk.line(C.accent, 2.4), '\\rm{iterate }m_k']]], lab(.44), { right: true });
  let mx = 0; for (let i = 0; i < NC; i++) mx = Math.max(mx, Math.abs(mh[i]));
  if (mx > 1.6) {
    const s = '\\rm{max}\\ |m_k| = ' + sci(mx) + '\\rm{, off the axes}', w = math(s, 0, -1e4, { size: 16, alpha: 0 });
    ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(PA.x + PA.w - 14 - w, PA.y + PA.h - 30, w + 8, 22); ctx.restore();
    math(s, PA.x + PA.w - 10, PA.y + PA.h - 14, { size: 16, color: C.accent, align: 'right', alpha: ra });
  }
}
function panelB(o, S, I) {
  sub('b', 508, PB.y - 14, 'iterations as a filter', lab(.04));
  const A = axes({ ...PB, xlim: [.5, NC + .5], ylim: [-18, 1], xticks: [1, 16, 32, 48, 64], yticks: [-16, -12, -8, -4, 0],
                   xfmt: () => '', yfmt: p10, tickSize: 16, ylabelGap: 50, ylabel: '\\rm{magnitude}', progress: seg(.04, .35) });
  const F = axes({ ...PF, xlim: [.5, NC + .5], ylim: [-.12, 1.32], xticks: [1, 16, 32, 48, 64], yticks: [0, 1],
                   xfmt: v => String(v), tickSize: 16, ylabelGap: 50, xlabel: '\\rm{index}\\ i', ylabel: 'f_i', progress: seg(.06, .35) });
  const lf = Math.log10(S.sig), fa = seg(.3, .35);
  A.inside(() => line([[PB.x, A.Y(lf)], [PB.x + PB.w, A.Y(lf)]], { color: C.guide, width: 1.2, dash: [5, 4], alpha: seg(.3, .3) }));
  F.inside(() => {
    const P = [[F.X(.5), F.Y(0)]];
    for (let j = 0; j < NC; j++) { const v = clamp(I.f[j], -.12, 1.32); P.push([F.X(j + .5), F.Y(v)]); P.push([F.X(j + 1.5), F.Y(v)]); }
    P.push([F.X(NC + .5), F.Y(0)]);
    if (fa > 0) { ctx.save(); ctx.globalAlpha *= fa; ctx.fillStyle = C.wash; ctx.beginPath(); P.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.fill(); ctx.restore(); }
    line([[PF.x, F.Y(0)], [PF.x + PF.w, F.Y(0)]], { color: C.rule, width: 1, alpha: fa });
    line([[PF.x, F.Y(1)], [PF.x + PF.w, F.Y(1)]], { color: C.rule, width: 1, alpha: fa });
    line(P.slice(1, -1), { color: C.accent, width: 1.6, progress: seg(.3, .4) });
  });
  const da = seg(.2, .3), ba = seg(.26, .3);
  for (let j = 0; j < NC; j++) {
    const ls = Math.log10(SV[j]), lb = Math.log10(Math.abs(S.beta[j]));
    if (da > 0) dot(A.X(j + 1), A.Y(Math.max(-17.8, ls)), 2.3, { color: C.ink, fill: C.ink, width: .6, alpha: da });
    if (ba > 0) dot(A.X(j + 1), A.Y(Math.max(-17.8, lb)), 2.3, { color: C.blue, fill: C.blue, width: .6, alpha: ba });
  }
  legend(PB.x + 8, PB.y + PB.h - 52, [[[mk.dot(C.ink, C.ink, 2.3), '\\rm{singular value}\\ s_i'], [mk.dot(C.blue, C.blue, 2.3), '|u_i^{⊤}d|']],
                                      [[mk.line(C.guide, 1.2, [5, 4]), '\\rm{noise floor}']]], lab(.48), { rh: 20 });
}
/* (c) and (d): k on a log axis from 1 to 10^8; Landweber through its integer iterates, CGLS its 50 */
function kAxes(P, letter, words, ylim, yticks, ylabel, t0) {
  sub(letter, P.x === PC.x ? 20 : 508, P.y - 14, words, lab(t0));
  return axes({ ...P, xlim: [0, D.lwdec], ylim, xticks: [0, 2, 4, 6, 8], yticks, xfmt: p10, yfmt: p10, tickSize: 16, ylabelGap: 50,
                xlabel: '\\rm{iteration}\\ k', ylabel, progress: seg(t0, .35) });
}
function curves(A, S, key, o, t0) {
  const lw = [], cg = [];
  for (let j = 0; j < S.lk.length; j++) lw.push([A.X(Math.log10(S.lk[j])), A.Y(Math.log10(S[key[0]][j]))]);
  for (let k = 1; k <= KC; k++) cg.push([A.X(Math.log10(k)), A.Y(Math.log10(S[key[1]][k - 1]))]);
  A.inside(() => {
    line(lw, { color: C.navy, width: 2.2, alpha: o.m === 0 ? 1 : .45, progress: seg(t0, .45) });
    line(cg, { color: C.blue, width: 1.6, alpha: o.m === 1 ? 1 : .45, progress: seg(t0 + .06, .4) });
  });
  const ca = seg(t0 + .2, .3) * (o.m === 1 ? 1 : .45);
  if (ca > 0) for (const p of cg) dot(p[0], p[1], 2.3, { color: C.blue, fill: '#fff', width: 1.1, alpha: ca });
}
function panelC(o, S, I) {
  const A = kAxes(PC, 'c', 'error against the truth', [-1.3, 2.7], [-1, 0, 1, 2], '‖m_k - m‖/‖m‖', .08);
  const kd = o.m === 0 ? S.ldp : S.cdp, la = lab(.45);
  A.inside(() => {
    line([[PC.x, A.Y(Math.log10(S.tbest))], [PC.x + PC.w, A.Y(Math.log10(S.tbest))]], { color: C.guide, width: 1.2, dash: [5, 4], alpha: seg(.3, .3) });
    line([[A.X(Math.log10(kd)), PC.y], [A.X(Math.log10(kd)), PC.y + PC.h]], { color: C.accent, width: 1.2, dash: [5, 4], alpha: la });
  });
  curves(A, S, ['lerr', 'cerr'], o, .18);
  dot(A.X(Math.log10(S.lbest)), A.Y(Math.log10(S.lbe)), 6.5, { color: C.ink, fill: null, width: 1.5, alpha: la });
  dot(A.X(Math.log10(S.cbest)), A.Y(Math.log10(S.cbe)), 6.5, { color: C.ink, fill: null, width: 1.5, alpha: la });
  dot(A.X(Math.log10(o.k)), A.Y(clamp(Math.log10(I.err), -1.3, 2.7)), 5.5, { color: '#fff', fill: C.accent, width: 1.4, alpha: lab(.4) });
  legend(PC.x + 8, PC.y + 7, [[[mk.line(C.guide, 1.2, [5, 4]), '\\rm{best Tikhonov}'], [mk.ring(6), '\\rm{lowest error}']]], lab(.46));
}
function panelD(o, S, I) {
  const A = kAxes(PD, 'd', 'residual against noise level', [-3, 1], [-3, -2, -1, 0, 1], '\\rm{residual}\\ ‖Gm_k - d‖', .12);
  const kd = o.m === 0 ? S.ldp : S.cdp, la = lab(.45), ld = Math.log10(S.delta);
  A.inside(() => {
    line([[PD.x, A.Y(ld)], [PD.x + PD.w, A.Y(ld)]], { color: C.guide, width: 1.2, dash: [5, 4], alpha: seg(.3, .3) });
    line([[A.X(Math.log10(kd)), PD.y], [A.X(Math.log10(kd)), PD.y + PD.h]], { color: C.accent, width: 1.2, dash: [5, 4], alpha: la });
  });
  curves(A, S, ['lrho', 'crho'], o, .22);
  dot(A.X(Math.log10(o.k)), A.Y(clamp(Math.log10(I.rho), -3, 1)), 5.5, { color: '#fff', fill: C.accent, width: 1.4, alpha: lab(.4) });
  legend(PD.x + PD.w - 8, PD.y + 7, [[[mk.line(C.navy, 2.2), '\\rm{Landweber}'], [mk.dline(C.blue, 1.6, '#fff'), '\\rm{CGLS}']],
                                     [[mk.line(C.guide, 1.2, [5, 4]), '\\rm{noise level}\\ \\sigma\\sqrt{N}'], [mk.vbar(C.accent), '\\rm{discrepancy stop}']]],
         lab(.5), { right: true });
}

function draw() {
  const o = now(), S = SETS[o.nz], I = iterate(o, S), mh = synth(I.c);
  controls(o, seg(0, .3));
  panelA(o, S, I, mh);
  panelB(o, S, I);
  panelC(o, S, I);
  panelD(o, S, I);
  math(D.params, 20, H - 14, { size: 15, color: C.muted, alpha: seg(.45, .3) });
  placeKeys([o.m, o.nz, o.k, o.run].join(':'));
}
/* the poster: the tour's Landweber run paused at its discrepancy stop (1 % noise) */
const POSTER_T = T0 + TL[0] + HD / 2;
if (['m', 'k', 'nz', 'run'].some(k => QS.has(k))) {
  ST = { m: QS.get('m') === 'cgls' ? 1 : 0, nz: +(QS.get('nz') || 1), run: null };
  const S = SETS[ST.nz];
  ST.kl = ST.m === 0 && QS.has('k') ? +QS.get('k') : S.ldp;
  ST.kc = ST.m === 1 && QS.has('k') ? +QS.get('k') : S.cdp;
  if (QS.get('run') === '1') ST.run = { t0: POSTER_T, l0: Math.log10(ST.m === 0 ? ST.kl : ST.kc) };
}
buildControls();
keyStandIns([{ radio: true, label: 'Solver', ids: ['m0', 'm1'] }, { radio: true, label: 'Noise level', ids: ['n0', 'n1', 'n2'] },
             { label: 'Iteration', ids: ['sl'] }, { ids: ['run', 'dp'] }]);
boot();
"""


def lw_grid():
    """Landweber's iterates drawn: every k to 100, then 600 rounded log-spaced k to 10^8."""
    return np.unique(np.concatenate([np.arange(1, 101), np.round(np.logspace(2, L.LW_DECADES, 600))])).astype(np.int64)


def compute():
    P = L.Problem()
    ks = lw_grid()
    sets, info = [], []
    for li in range(len(L.LEVELS)):
        Dd = P.data(li, 0)
        b = Dd["beta"]
        lw = np.array([P.ev(P.lw(k), b) for k in ks])
        ldp, lbest = P.lw_dp(Dd), P.lw_best(b)
        X, R = L.cgls(P.G, Dd["d"], L.K_CGLS)
        cc = X @ P.V                                   # each iterate's coefficients v_i^T x_k
        cerr = np.linalg.norm(X - P.m, axis=1) / P.mnorm
        crho = np.linalg.norm(Dd["d"] - X @ P.G.T, axis=1)
        cdp = int(1 + np.argmax(crho <= Dd["delta"]))
        cbest = int(1 + np.argmin(cerr))
        abest = P.tik_best(b)
        tbest = P.ev(P.tik(abest), b)[2]
        lbe, ldpe = P.ev(P.lw(lbest), b), P.ev(P.lw(ldp), b)
        sets.append(dict(d=common.f32(Dd["d"]), beta=L.f64(b), sig=Dd["sig"], delta=Dd["delta"],
                         lk=common.f32(ks), lerr=common.f32(lw[:, 2]), lrho=common.f32(lw[:, 0]),
                         cc=L.f64(cc), cerr=L.f64(cerr), crho=L.f64(crho),
                         ldp=ldp, lbest=lbest, lbe=lbe[2], cdp=cdp, cbest=cbest, cbe=float(cerr[cbest - 1]), tbest=tbest))
        info.append(dict(D=Dd, lw=lw, ldp=ldp, lbest=lbest, lbe=lbe, ldpe=ldpe, X=X, R=R, cc=cc, cerr=cerr, crho=crho,
                         cdp=cdp, cbest=cbest, abest=abest, tbest=tbest))
    data = dict(
        n=L.N, s=L.f64(P.s), V=L.f64(P.V), t=L.f64(P.t), m=L.f64(P.m), mnorm=P.mnorm,
        omega=P.omega, klmax=int(10 ** L.LW_DECADES), kcmax=L.K_CGLS, lwdec=L.LW_DECADES, names=list(L.LEVEL_NAMES), sets=sets,
        params=(r"\rm{Figure 4's problem (noise draw 1), both from }m_0 = 0\rm{; Landweber }m_k = m_{k-1} + \omega G^{⊤}(d - Gm_{k-1})"
                r"\rm{, }\omega\ = 1/s_1^2\rm{; CGLS, 50 iterations}"),
    )
    return P, ks, info, data


def page_states(P, info):
    """The page's iterate in reader's states against numpy: max differences."""
    st = [(0, li, k) for li in range(3) for k in (1, 2, info[li]["ldp"], info[li]["lbest"], 10 ** 4, 10 ** 8)]
    st += [(1, li, k) for li in range(3) for k in (1, info[li]["cdp"], info[li]["cbest"], 30, 50)]
    exprs = [f"(() => {{ ST = {{m: {m}, nz: {li}, kl: {k}, kc: {k}, run: null}}; const o = now(), S = SETS[o.nz], I = iterate(o, S), "
             f"mm = synth(I.c); return [I.rho, I.eta, I.err, ...mm, ...I.f]; }})()" for m, li, k in st]
    got = L.check_page(NAME, exprs)
    w = dict(m=0.0, rho=0.0, eta=0.0, err=0.0, f=0.0)
    for (m, li, k), g in zip(st, got):
        z = info[li]
        b = z["D"]["beta"]
        if m == 0:
            f = P.lw(k)
            rho, eta, err = P.ev(f, b)
            mm = P.solution(f, b)
        else:
            mm = z["X"][k - 1]
            rho, eta, err = np.linalg.norm(z["D"]["d"] - P.G @ mm), np.linalg.norm(mm), np.linalg.norm(mm - P.m) / P.mnorm
            f = (P.V.T @ mm) * P.s / b
        w["m"] = max(w["m"], np.abs(g[3:3 + L.N] - mm).max() / np.abs(mm).max())
        w["rho"] = max(w["rho"], abs(g[0] - rho) / rho)
        w["eta"] = max(w["eta"], abs(g[1] - eta) / eta)
        w["err"] = max(w["err"], abs(g[2] - err) / err)
        w["f"] = max(w["f"], np.abs(g[3 + L.N:] - f).max())
    return len(st), w


def validate(P, ks, info):
    from scipy.sparse.linalg import lsqr
    T = []
    say = T.append
    # 1. Landweber: the iteration itself against the closed form
    KMAX = 25000
    checks = [1, 2, 10, 100, 1000, 10000, KMAX]
    d1 = {}
    for li in range(3):
        z = info[li]
        want = sorted(set(checks + [z["ldp"], z["lbest"]]) & set(range(1, KMAX + 1)))
        x = np.zeros(L.N)
        d = z["D"]["d"]
        worst = 0.0
        for k in range(1, KMAX + 1):
            x = x + P.omega * (P.G.T @ (d - P.G @ x))
            if k in want:
                xc = P.solution(P.lw(k), z["D"]["beta"])
                worst = max(worst, np.abs(x - xc).max() / np.abs(xc).max())
        d1[li] = (worst, want)
    # 2. and 3. CGLS against LSQR and the exact Krylov solution (GKB, full reorthogonalization), Ritz filters
    c2 = {}
    for li in range(3):
        z = info[li]
        X = z["X"]
        dl = np.array([np.linalg.norm(lsqr(P.G, z["D"]["d"], atol=0, btol=0, conlim=0, iter_lim=k)[0] - X[k - 1]) / np.linalg.norm(X[k - 1])
                       for k in range(1, L.K_CGLS + 1)])
        XG, TH = L.gkb_krylov(P.G, z["D"]["d"], L.K_CGLS)
        dg = np.linalg.norm(XG - X, axis=1) / np.linalg.norm(X, axis=1)
        ge = np.linalg.norm(XG - P.m, axis=1) / P.mnorm
        fr = 0.0
        for k in range(1, 13):
            fR = 1 - np.prod(1 - P.s[:, None] ** 2 / TH[k - 1][None, :], axis=1)
            fC = (P.V.T @ X[k - 1]) * P.s / z["D"]["beta"]
            fr = max(fr, np.abs(fR - fC).max())
        rr = np.abs(z["R"] - z["crho"]).max() / z["crho"].min()
        c2[li] = dict(dl=dl, dg=dg, fr=fr, kl=max(k for k in range(1, 51) if dl[k - 1] < 1e-10),
                      kg=max(k for k in range(1, 51) if dg[k - 1] < 1e-10), gbest=int(1 + np.argmin(ge)), gbe=ge.min(), rr=rr)
    # the iteration counts for every data set (draws 2 and 3 are not drawn; their numbers for the text)
    tab = []
    for li in range(3):
        for ri in range(3):
            Dd = P.data(li, ri)
            b = Dd["beta"]
            ldp, lbest = P.lw_dp(Dd), P.lw_best(b)
            X, R = L.cgls(P.G, Dd["d"], L.K_CGLS)
            ce = np.linalg.norm(X - P.m, axis=1) / P.mnorm
            cr = np.linalg.norm(Dd["d"] - X @ P.G.T, axis=1)
            cdp, cbest = int(1 + np.argmax(cr <= Dd["delta"])), int(1 + np.argmin(ce))
            tb = P.ev(P.tik(P.tik_best(b)), b)[2]
            tab.append((li, ri, ldp, P.ev(P.lw(ldp), b)[2], lbest, P.ev(P.lw(lbest), b)[2], cdp, ce[cdp - 1], cbest, ce[cbest - 1], tb))
    # the page
    nst, w = page_states(P, info)

    say("Figure 5, solving by iterating (semi-convergence): check of tools/numfig/sp_inv_iter.py")
    say("")
    say("MODEL (his page iterative-solvers-animation.html, the same numbers)")
    say("  Figure 4's problem (sp_inv_lib; see sp_inv_reg.check.txt): N = 64, Gaussian blur s = 0.045, m a bump and a")
    say("  block; d = Gm + e with noise draw 1 (numpy default_rng seed 1) at 0.1, 1 and 10 % of max Gm; delta = sigma sqrt(N).")
    say(f"  Landweber: m_k = m_(k-1) + omega G^T (d - G m_(k-1)), m_0 = 0, omega = 1/s_1^2 = {P.omega:.10f}; in closed form")
    say("  m_k = sum f_i (u_i^T d / s_i) v_i, f_i = 1 - (1 - omega s_i^2)^k (computed as -expm1(k log1p(-omega s_i^2))).")
    say(f"  CGLS: {L.K_CGLS} iterations from m_0 = 0 (Hestenes-Stiefel form, no reorthogonalization), run for real.")
    say("  Effective filter of an iterate: f_i = s_i (v_i^T m_k) / (u_i^T d).")
    say("")
    say("GRID")
    say(f"  Landweber's curves pass through {len(ks)} integer iterates: every k to 100, then 600 log-spaced k (rounded) to")
    say("  10^8; the iterate the reader picks (any integer k) is the page's own sum, its marker exactly on the curve's")
    say("  formula. The discrepancy stop is the first integer k with |G m_k - d| <= delta (bisection over integers); the")
    say("  best k minimizes the true error over every k to 5,000, then k growing by 0.05 %, then every k within 0.2 %.")
    say("  CGLS: every iteration 1 to 50.")
    say("")
    say("VALIDATION")
    say(f"  1. Landweber's closed form against the iteration itself (up to k = {KMAX:,}), at k = 1, 2, 10, 100, 1,000, 10,000,")
    say(f"     25,000 and at each level's discrepancy and best k (where within reach):")
    for li in range(3):
        say(f"     {L.LEVEL_NAMES[li]:>4s}: largest difference {d1[li][0]:.1e} of max|m_k| (k checked: {', '.join(f'{k:,}' for k in d1[li][1])})")
    say("  2. CGLS against scipy.sparse.linalg.lsqr (LSQR, the same Krylov iterates in exact arithmetic; atol = btol =")
    say("     conlim = 0, iter_lim = k) and against the exact Krylov solution, argmin |Gx - d| over")
    say("     span{G^T d, (G^T G) G^T d, ...}, by Golub-Kahan bidiagonalization with full reorthogonalization:")
    for li in range(3):
        c = c2[li]
        say(f"     {L.LEVEL_NAMES[li]:>4s}: CGLS = LSQR within 1e-10 up to k = {c['kl']}, = exact Krylov up to k = {c['kg']} (largest difference there "
            f"{c['dg'][:c['kg']].max():.1e}); at k = 50 they differ by {c['dl'][-1]:.1e} (LSQR) and {c['dg'][-1]:.1e} (Krylov):")
    say("     past about 15 iterations rounding destroys the orthogonality of the Krylov basis (Lanczos in floating")
    say("     point), and CGLS, LSQR and exact arithmetic part. The curves drawn are CGLS as it runs in double precision.")
    for li in range(3):
        c = c2[li]
        z = info[li]
        say(f"     {L.LEVEL_NAMES[li]:>4s}: CGLS best k = {z['cbest']} ({100 * z['cerr'][z['cbest'] - 1]:.2f} %), exact Krylov best k = {c['gbest']} ({100 * c['gbe']:.2f} %);"
            f" CGLS and exact Krylov differ by {c['dg'][z['cdp'] - 1]:.0e} at the discrepancy stop k = {z['cdp']}, {c['dg'][z['cbest'] - 1]:.0e} at k = {z['cbest']}.")
    say("  3. CGLS's filter factors s_i (v_i^T m_k) / (u_i^T d) against the Ritz polynomial 1 - prod_j (1 - s_i^2 / theta_j),")
    say("     theta_j the squared singular values of the Golub-Kahan bidiagonal B_k (k <= 12): largest difference "
        f"{max(c2[li]['fr'] for li in range(3)):.1e}.")
    say(f"     CGLS's own recursion residual against |d - G m_k| by a matrix-vector product: {max(c2[li]['rr'] for li in range(3)):.1e} (relative).")
    say(f"  4. The page (its Landweber filter and synth(), CGLS from its stored SVD coefficients) against numpy in {nst} states:")
    say(f"     iterate {w['m']:.1e} of max|m_k|, residual {w['rho']:.1e}, norm {w['eta']:.1e}, error {w['err']:.1e} (relative), filter")
    say(f"     factors {w['f']:.1e}.")
    say("")
    say("SEMI-CONVERGENCE: ITERATIONS TO THE LOWEST ERROR AND TO THE DISCREPANCY STOP (error in brackets)")
    say("  noise draw | Landweber: discrepancy stop  lowest error | CGLS: discrepancy stop  lowest error | best Tikhonov")
    for li, ri, ldp, lde, lb, lbe, cdp, cde, cb, cbe, tb in tab:
        say(f"  {L.LEVEL_NAMES[li]:>4s}  {ri + 1}   | {ldp:>6,} ({100 * lde:.2f} %)  {lb:>7,} ({100 * lbe:.2f} %) | {cdp:>3} ({100 * cde:.2f} %)  "
            f"{cb:>3} ({100 * cbe:.2f} %) | {100 * tb:.2f} %")
    say("  His page says CGLS needs about ten iterations where Landweber needs a couple of hundred: at 1 % noise (his")
    say("  default) it is 14, 13, 13 against 177, 166, 162 for the three draws. The ratio grows as the noise falls")
    say("  (0.1 %: 29 against 23,588) and shrinks as it rises (10 %: 6 against 23).")
    say("")
    say("DISPLAY")
    say(f"  W x H = 1000 x {H}. Untouched (1 % noise): Landweber runs from k = 1 at 8/14 = 0.57 decades of k a second")
    say(f"  (every k an integer), pauses 2.6 s at its discrepancy stop (k = {info[1]['ldp']}), runs on to 10^8 (14 s in all) and holds")
    ld1 = info[1]["ldp"]
    say(f"  2.6 s; then CGLS the same, 0.3 s an iteration, pausing 2.6 s at k = {info[1]['cdp']} and at k = 50; then again.")
    say(f"  POSTER_T = 0.6 + log10({ld1}) x 14/8 + 1.3 = {0.6 + np.log10(ld1) * 14 / 8 + 1.3:.4f} s: Landweber paused at its discrepancy stop.")
    say("  Controls (hit areas 40 units tall, 27 CSS px at the page's 672 px, the keyboard's stand-ins as large; the")
    say("  focus ring 3 units outside the drawn chip): solver and noise chips, the iteration slider (log k for")
    say("  Landweber, k for CGLS), 'iterate' (his Play: the iterations run on from the one shown), 'discrepancy")
    say("  principle' (his Stop at discrepancy principle). Query keys: m=lw|cgls, k, nz, run.")
    txt = "\n".join(T) + "\n"
    with open(os.path.join(common.HERE, "sp_inv_iter.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return txt


def build():
    P, ks, info, data = compute()
    for li in range(3):
        z = info[li]
        print(f"noise {L.LEVEL_NAMES[li]:>4s}: Landweber DP k {z['ldp']} (err {z['ldpe'][2]:.4f}), best k {z['lbest']} "
              f"(err {z['lbe'][2]:.4f}); CGLS DP k {z['cdp']} (err {z['cerr'][z['cdp'] - 1]:.4f}), best k {z['cbest']} "
              f"(err {z['cerr'][z['cbest'] - 1]:.4f}); best Tikhonov err {z['tbest']:.4f}")
    common.build_html(NAME, TITLE, ARIA, W, H, data, JS, digits=16)
    png = common.still(NAME)
    print("still:", png)
    validate(P, ks, info)
    return P, ks, info, data


if __name__ == "__main__":
    build()
