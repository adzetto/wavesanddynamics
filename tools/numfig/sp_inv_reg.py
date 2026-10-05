"""Figure 4 of the signal processing document: undoing a blur, an ill-posed
inverse problem (his "Inverse Problems and Regularization" section, redrawn
from his page inverse-regularization-animation.html).

Model (sp_inv_lib): a hidden cause m, a smooth bump and a sharp block, is
blurred by a Gaussian kernel G (N = 64 cells, width 0.045) and measured with
white noise, d = G m + e, at 0.1, 1 or 10 % of max |G m|, three seeded draws.
The estimate is the filtered SVD sum m = sum f_i (u_i^T d / s_i) v_i: no
regularization (f = 1), truncated SVD (the first k terms) or Tikhonov,
f_i = s_i^2 / (s_i^2 + alpha^2). Python computes the SVD, the data, the
Tikhonov path on 321 strengths (40 per decade), every truncation k, the
discrepancy principle, the L-curve's corner and the lowest true error; the
page draws the estimate for the strength the reader sets by the same sum from
DATA (float64 V, s, U^T d), checked against numpy in the check file.

Panels: (a) the forward problem, m, G m and d; (b) the inverse problem, the
estimate against m; (c) the L-curve, |G m - d| against |m| on log axes, the
Tikhonov path and the truncated SVD points, the noise level; (d) the Picard
plot, s_i and |u_i^T d| against i, the noise floor and the filter factors.
Untouched, the figure tours: Tikhonov swept once through its strengths, then no
regularization while the noise draw changes every 1.2 s (Hadamard's third
condition failing), then truncated SVD swept. Query keys choose a state:
m=none|tsvd|tik, nz=0|1|2 (noise level), dr=0|1|2 (draw), a=<alpha> or
u=<slider position>, k=<truncation>, sw=1 (sweep), an=1 (draws animated).

Run: python tools/numfig/sp_inv_reg.py [--verify]  (writes the page, the
still and the check file; prints the key numbers; --verify also runs the
overlap check in every reader's state).
"""
import os
import sys

import numpy as np

import common
import sp_inv_lib as L

NAME = "sp-inv-reg"
W, H = 1000, 740
TITLE = "Figure 4: Undoing a blur, an ill-posed inverse problem"
ARIA = ("Four panels on one blurred, noisy measurement. A hidden cause, a smooth bump and a sharp block, "
        "is blurred and measured with noise; the cause recovered from the data is compared with the truth. "
        "Without regularization the recovered cause is more than ten trillion times too large and changes completely "
        "with each noise draw; truncated SVD and Tikhonov regularization recover it. An L-curve and a Picard "
        "plot show why, and where the regularization strength should be: the noise level. The method, the "
        "strength, the noise level and the noise draw can be chosen.")

JS = L.JS_LIB + r"""
const D = DATA;
const LA0 = D.la0, LA1 = D.la1;                     // the strength slider: log10 alpha, his 8 decades
const SETS = D.sets.map(row => row.map(q => ({ ...q, d: b64f32(q.d), beta: b64f64(q.beta),
  rho: b64f32(q.rho), eta: b64f32(q.eta), trho: b64f32(q.trho), teta: b64f32(q.teta) })));
const GM = b64f32(D.Gm), NAP = D.na;
const alphaOf = u => Math.pow(10, LA0 + (LA1 - LA0) * u), uOf = a => (Math.log10(a) - LA0) / (LA1 - LA0);
const rOfK = k => (NC - k) / (NC - 1), kOfR = r => Math.round(NC - (NC - 1) * r);
const ONES = new Float64Array(NC).fill(1);
function filt(o) {
  if (o.m === 0) return ONES;
  const f = new Float64Array(NC);
  if (o.m === 1) { for (let j = 0; j < o.k; j++) f[j] = 1; return f; }
  const a2 = alphaOf(o.u) ** 2;
  for (let j = 0; j < NC; j++) f[j] = SV[j] * SV[j] / (SV[j] * SV[j] + a2);
  return f;
}

/* ================================================ the reader's choices (explicit state)
   ST = null: the tour. Else {m: 0 none, 1 truncated SVD, 2 Tikhonov; nz, dr: noise level and draw;
   u: Tikhonov's slider position; k: the truncation; sw: a sweep {t0, ph}; an: draws animated {t0, d0}} */
let ST = null;
function reset() { ST = null; UI.hov = UI.down = UI.drag = UI.press = ''; }
const TS = 12, HOLD = 1.8, TN = 6, PD_ = 1.2, T0 = .6;   // sweep period, holds, none phase, draw period
const PER = TS + HOLD + TN + TS + HOLD;
const sweep = (t0, ph) => .5 - .5 * Math.cos(2 * Math.PI * (t - t0) / TS + ph);
const phase = r => Math.acos(clamp(1 - 2 * r, -1, 1));          // a sweep from r, stronger first
function tour() {
  const S = SETS[1][0], uD = uOf(S.adp), base = { nz: 1, dr: 0, u: uD, k: S.kdp, sw: null, an: null };
  if (t < T0) return { ...base, m: 2 };
  const c = (t - T0) % PER, c0 = t - c;
  if (c < TS) return { ...base, m: 2, sw: { t0: c0, ph: phase(uD) } };
  if (c < TS + HOLD) return { ...base, m: 2 };
  if (c < TS + HOLD + TN) return { ...base, m: 0, an: { t0: c0 + TS + HOLD, d0: 0, first: 0 } };
  if (c < 2 * TS + HOLD + TN) return { ...base, m: 1, sw: { t0: c0 + TS + HOLD + TN, ph: phase(rOfK(S.kdp)) } };
  return { ...base, m: 1 };
}
/* the state shown at this moment: the tour's or the reader's, with its sweep and its draws run on */
function now() {
  const s = ST || tour(), o = { m: s.m, nz: s.nz, dr: s.dr, u: s.u, k: s.k, sw: !!s.sw, an: !!s.an };
  if (s.sw && s.m > 0) { const r = sweep(s.sw.t0, s.sw.ph); if (s.m === 2) o.u = r; else o.k = kOfR(r); }
  if (s.an) o.dr = (s.an.d0 + Math.max(0, Math.floor((t - s.an.t0) / PD_ + (s.an.first === undefined ? .6 : s.an.first)))) % 3;
  return o;
}
/* the first touch takes the tour's state as the reader's: nothing jumps */
function hold() {
  if (ST) return;
  const s = tour(), o = now();
  ST = { m: o.m, nz: o.nz, dr: o.dr, u: o.u, k: o.k, sw: s.sw, an: s.an ? { t0: t, d0: o.dr } : null };
}
function freeze() { const o = now(); ST.u = o.u; ST.k = o.k; ST.sw = null; }
function startSweep() { const o = now(); ST.u = o.u; ST.k = o.k; ST.sw = { t0: t, ph: phase(ST.m === 2 ? o.u : rOfK(o.k)) }; }
const moves = () => !REDUCED && !STILL;
function choose(f) { hold(); f(); redraw(); }

/* ================================================ the controls */
const ROW1 = 14, ROW2 = 56, CHH = 28, SLY = ROW2 + 14;
const SL = { x0: 50, x1: 318 };
const METH = ['none', 'truncated SVD', 'Tikhonov'];
let LAY = null;
function layout() {                           // chips sized to their words, once the type has loaded
  if (LAY) return LAY;
  const L = { r1: [], r2: [] };
  let x = 20 + tw('method', 15) + 10;
  L.method = x - 10;
  METH.forEach((s, i) => { const w = Math.max(46, tw(s, 15) + 22); L.r1.push({ id: 'm' + i, x, w }); x += w + 6; });
  x += 24; L.noise = x; x += tw('noise', 15) + 10;
  D.names.forEach((s, i) => { L.r1.push({ id: 'n' + i, x, w: 52 }); x += 58; });
  x += 18; L.draw = x; x += tw('draw', 15) + 10;
  for (let i = 0; i < 3; i++) { L.r1.push({ id: 'd' + i, x, w: 30 }); x += 36; }
  L.r1.push({ id: 'an', x, w: tw('animate', 15) + 22 });
  x = 532;
  for (const [id, s] of [['sw', 'sweep'], ['dp', 'discrepancy principle'], ['cn', 'L-curve corner']]) {
    const w = tw(s, 15) + 22; L.r2.push({ id, x, w }); x += w + 8;
  }
  return (LAY = L);
}
function mkChip(g, y, label, on, act, off = () => false, extra = {}) {
  const h = (UI.list.find(c => c.id === g.id) || {});
  Object.assign(h, { id: g.id, kind: 'chip', x: g.x, y, w: g.w, h: CHH, hit: [g.x - 3, y - 8, g.x + g.w + 3, y + CHH + 7],
                     label, on, act, off }, extra);
  if (!UI.list.includes(h)) UI.list.push(h);
}
function buildControls() {
  const L = layout(), at = id => L.r1.find(g => g.id === id) || L.r2.find(g => g.id === id);
  METH.forEach((s, i) => mkChip(at('m' + i), ROW1, () => s, () => now().m === i,
    () => choose(() => { const sw = !!ST.sw; freeze(); ST.m = i; if (sw && i > 0) startSweep(); }),
    () => false, { aria: () => 'Method: ' + (i ? s : 'no regularization') }));
  D.names.forEach((s, i) => mkChip(at('n' + i), ROW1, () => s, () => now().nz === i, () => choose(() => { ST.nz = i; }),
    () => false, { aria: () => 'Noise level ' + s + ' of the largest blurred value' }));
  for (let i = 0; i < 3; i++) mkChip(at('d' + i), ROW1, () => String(i + 1), () => now().dr === i,
    () => choose(() => { ST.dr = i; ST.an = null; }), () => false, { aria: () => 'Noise draw ' + (i + 1) });
  mkChip(at('an'), ROW1, () => 'animate', () => now().an, () => choose(() => {
    if (ST.an) { ST.dr = now().dr; ST.an = null; } else { ST.an = { t0: t, d0: now().dr }; if (!playing) setPlay(true); }
  }), () => !moves(), { toggle: true, aria: () => 'Animate the noise: a new draw every 1.2 seconds' });
  mkChip(at('sw'), ROW2, () => 'sweep', () => now().sw && now().m > 0, () => choose(() => {
    if (ST.sw) freeze(); else { startSweep(); if (!playing) setPlay(true); }
  }), () => !moves() || now().m === 0, { toggle: true, aria: () => 'Sweep the regularization strength' });
  mkChip(at('dp'), ROW2, () => 'discrepancy principle', () => atDP(now()), () => choose(() => {
    freeze(); const S = SETS[ST.nz][now().dr]; if (ST.m === 2) ST.u = uOf(S.adp); else ST.k = S.kdp;
  }), () => now().m === 0, { aria: () => 'Discrepancy principle: the strength whose residual equals the noise level' });
  mkChip(at('cn'), ROW2, () => 'L-curve corner', () => atCorner(now()), () => choose(() => {
    freeze(); ST.u = uOf(SETS[ST.nz][now().dr].acn);
  }), () => now().m !== 2, { aria: () => 'The L-curve corner: the Tikhonov strength of greatest curvature' });
  const sl = UI.list.find(c => c.id === 'sl') || { id: 'sl', kind: 'slider' };
  Object.assign(sl, { x0: SL.x0, x1: SL.x1, y: SLY, hit: [SL.x0 - 14, SLY - 21, SL.x1 + 14, SLY + 21],
    off: () => now().m === 0,
    ticks: now().m === 2 ? [0, 1, 2, 3, 4, 5, 6, 7, 8].map(v => v / 8) : now().m === 1 ? [1, 16, 32, 48, 64].map(k => (k - 1) / 63) : [],
    get: () => { const o = now(); return o.m === 2 ? o.u : (o.k - 1) / (NC - 1); },
    set: v => choose(() => { freeze(); if (ST.m === 2) ST.u = v; else ST.k = Math.round(1 + v * (NC - 1)); }),
    keys: e => {
      const o = now(), big = e.key === 'PageUp' || e.key === 'PageDown';
      const dd = { ArrowRight: 1, ArrowUp: 1, PageUp: 1, ArrowLeft: -1, ArrowDown: -1, PageDown: -1 }[e.key];
      if (!dd && e.key !== 'Home' && e.key !== 'End') return false;
      choose(() => {
        freeze();
        if (ST.m === 2) ST.u = e.key === 'Home' ? 0 : e.key === 'End' ? 1 : clamp(o.u + dd * (big ? 1 / 8 : 1 / 320));
        else ST.k = e.key === 'Home' ? 1 : e.key === 'End' ? NC : clamp(o.k + dd * (big ? 8 : 1), 1, NC);
      });
      return true;
    },
    aria: () => now().m === 2 ? 'Tikhonov regularization strength alpha' : 'Truncated SVD: number of terms kept',
    valueText: () => { const o = now(); return o.m === 2 ? 'alpha ' + alphaOf(o.u).toPrecision(3) : o.m === 1 ? o.k + ' of 64 terms kept' : 'no parameter'; } });
  if (!UI.list.includes(sl)) UI.list.push(sl);
}
const atDP = o => { const S = SETS[o.nz][o.dr]; return !o.sw && (o.m === 2 ? Math.abs(o.u - uOf(S.adp)) < 1e-9 : o.m === 1 && o.k === S.kdp); };
const atCorner = o => !o.sw && o.m === 2 && Math.abs(o.u - uOf(SETS[o.nz][o.dr].acn)) < 1e-9;
UI.ground = (X, Y) => Y < ROW2 + CHH + 12;

function controls(o, a) {
  buildControls();
  const L = layout();
  text('method', L.method, ROW1 + 19, { size: 15, color: C.body, align: 'right', alpha: a });
  text('noise', L.noise, ROW1 + 19, { size: 15, color: C.body, alpha: a });
  text('draw', L.draw, ROW1 + 19, { size: 15, color: C.body, alpha: a });
  for (const c of UI.list) if (c.kind === 'chip') drawChip(c, a);
  const sl = ctlById('sl');
  drawSlider(sl, a);
  if (o.m === 2) {
    math('\\alpha', 20, SLY + 6, { size: 18, alpha: a });
    math('\\alpha\\ = ' + sci(alphaOf(o.u)), SL.x1 + 22, SLY + 6, { size: 16, alpha: a });
  } else if (o.m === 1) {
    math('k', 22, SLY + 6, { size: 18, alpha: a });
    math('k = ' + o.k + '\\rm{ of }' + NC, SL.x1 + 22, SLY + 6, { size: 16, alpha: a });
  } else text('no parameter', SL.x1 + 22, SLY + 6, { size: 15, color: C.muted, alpha: a });
}

/* ================================================ the panels */
const PA = { x: 88, y: 132, w: 364, h: 200 }, PB = { x: 576, y: 132, w: 364, h: 200 };
const PC = { x: 88, y: 434, w: 364, h: 200 }, PD = { x: 576, y: 434, w: 364, h: 146 }, PF = { x: 576, y: 590, w: 364, h: 44 };
const curve = (A, ys, lo = -1e9, hi = 1e9) => Array.from(ys, (v, i) => [A.X(XC[i]), A.Y(clamp(v, lo, hi))]);
const mk = {
  line: (col, w, dash) => (x, y, a) => line([[x - 12, y], [x + 12, y]], { color: col, width: w, dash, alpha: a }),
  dot: (col, fill, r = 3) => (x, y, a) => dot(x, y, r, { color: col, fill, width: 1.2, alpha: a }),
  ring: r => (x, y, a) => dot(x, y, r, { color: C.ink, fill: null, width: 1.5, alpha: a }),
  square: s => (x, y, a) => line([[x - s, y - s], [x + s, y - s], [x + s, y + s], [x - s, y + s]], { color: C.ink, width: 1.5, close: true, alpha: a }),
  vbar: col => (x, y, a) => line([[x, y - 8], [x, y + 8]], { color: col, width: 1.6, dash: [3, 3], alpha: a }),
};
function panelA(o, S) {
  sub('a', 20, PA.y - 14, 'forward problem', lab(0));
  const A = axes({ ...PA, xlim: [0, 1], ylim: [-0.5, 1.6], xticks: [0, .2, .4, .6, .8, 1], yticks: [-0.5, 0, .5, 1, 1.5],
                   xfmt: v => v === 1 || v === 0 ? fmt(v) : v.toFixed(1), yfmt: v => v === 0 ? '0' : Number.isInteger(v) ? fmt(v) : v.toFixed(1).replace('-', '−'),
                   xlabel: '\\rm{position}\\ x', ylabel: '\\rm{amplitude}', ylabelGap: 50, tickSize: 16, progress: seg(0, .35) });
  A.inside(() => {
    line([[PA.x, A.Y(0)], [PA.x + PA.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.1, .3) });
    line(curve(A, MT), { color: C.ink, width: 2.2, progress: seg(.08, .4) });
    line(curve(A, GM), { color: C.blue, width: 1.8, dash: [6, 4], progress: seg(.16, .4) });
  });
  const da = seg(.3, .3);
  if (da > 0) for (let i = 0; i < NC; i++) dot(A.X(XC[i]), A.Y(S.d[i]), 2.5, { color: C.navy, fill: C.navy, width: .8, alpha: da });
  legend(PA.x + PA.w - 8, PA.y + 7, [[[mk.line(C.ink, 2.2), '\\rm{true cause }m'], [mk.line(C.blue, 1.8, [6, 4]), '\\rm{blurred }Gm']],
                                     [[mk.dot(C.navy, C.navy, 2.5), '\\rm{measured }d']]], lab(.4), { right: true });
}
function panelB(o, S, E, mh) {
  sub('b', 508, PB.y - 14, 'inverse problem', lab(.04));
  const none = o.m === 0, sc = D.naive[o.nz];
  const Y = none ? sc.y * 10 ** sc.p : 0;
  const A = none
    ? axes({ ...PB, xlim: [0, 1], ylim: [-Y, Y], xticks: [0, .2, .4, .6, .8, 1], yticks: [-sc.y, -sc.y / 2, 0, sc.y / 2, sc.y].map(v => v * 10 ** sc.p),
             xfmt: v => v === 1 || v === 0 ? fmt(v) : v.toFixed(1), yfmt: v => fmt(v / 10 ** sc.p),
             xlabel: '\\rm{position}\\ x', ylabel: '\\rm{amplitude}\\ (10^{' + sc.p + '})', ylabelGap: 46, tickSize: 16, progress: seg(.04, .35) })
    : axes({ ...PB, xlim: [0, 1], ylim: [-0.6, 1.6], xticks: [0, .2, .4, .6, .8, 1], yticks: [-0.5, 0, .5, 1, 1.5],
             xfmt: v => v === 1 || v === 0 ? fmt(v) : v.toFixed(1), yfmt: v => v === 0 ? '0' : Number.isInteger(v) ? fmt(v) : v.toFixed(1).replace('-', '−'),
             xlabel: '\\rm{position}\\ x', ylabel: '\\rm{amplitude}', ylabelGap: 50, tickSize: 16, progress: seg(.04, .35) });
  const lo = none ? -Y * 1.5 : -20, hi = none ? Y * 1.5 : 20;
  A.inside(() => {
    line([[PB.x, A.Y(0)], [PB.x + PB.w, A.Y(0)]], { color: C.rule, width: 1, alpha: seg(.1, .3) });
    line(curve(A, MT), { color: C.ink, width: 1.8, progress: seg(.12, .4) });
    line(curve(A, mh, lo, hi), { color: C.accent, width: 2.4, progress: seg(.22, .45) });
  });
  const ra = lab(.5);
  math('\\rm{error}\\ ‖m̂ - m‖/‖m‖ = ' + pctv(E.err), PB.x + PB.w, PB.y - 14, { size: 16, align: 'right', alpha: ra });
  legend(PB.x + PB.w - 8, PB.y + 7, [[[mk.line(C.ink, 1.8), '\\rm{true cause }m'], [mk.line(C.accent, 2.4), '\\rm{estimate }m̂']]],
         lab(.44), { right: true });
  let mx = 0; for (let i = 0; i < NC; i++) mx = Math.max(mx, Math.abs(mh[i]));
  if (!none && mx > 1.6) {
    const s = '\\rm{max}\\ |m̂| = ' + sci(mx) + '\\rm{, off the axes}', w = math(s, 0, -1e4, { size: 15, alpha: 0 });
    ctx.save(); ctx.fillStyle = '#fff'; ctx.fillRect(PB.x + PB.w - 14 - w, PB.y + PB.h - 30, w + 8, 22); ctx.restore();
    math(s, PB.x + PB.w - 10, PB.y + PB.h - 14, { size: 15, color: C.accent, align: 'right', alpha: ra });
  }
}
function panelC(o, S, E) {
  sub('c', 20, PC.y - 14, 'L-curve', lab(.08));
  const A = axes({ ...PC, xlim: [-3, 1], ylim: [-2, 5], xticks: [-3, -2, -1, 0, 1], yticks: [-2, -1, 0, 1, 2, 3, 4, 5],
                   xfmt: p10, yfmt: p10, tickSize: 16, ylabelGap: 50,
                   xlabel: '\\rm{residual norm}\\ ‖Gm̂ - d‖', ylabel: '\\rm{solution norm}\\ ‖m̂‖', progress: seg(.08, .35) });
  const lx = Math.log10(S.delta);
  const ta = o.m === 2 ? 1 : .35, ka = o.m === 1 ? 1 : .35;
  A.inside(() => {
    line([[A.X(lx), PC.y], [A.X(lx), PC.y + PC.h]], { color: C.guide, width: 1.2, dash: [5, 4], alpha: seg(.3, .3) });
    const P = []; for (let j = 0; j < NAP; j++) P.push([A.X(Math.log10(S.rho[j])), A.Y(Math.log10(S.eta[j]))]);
    line(P, { color: C.navy, width: 2.2, alpha: ta, progress: seg(.18, .45) });
  });
  const pa = seg(.35, .3);
  for (let k = 1; k <= NC; k++) {
    const x = Math.log10(S.trho[k - 1]), y = Math.log10(S.teta[k - 1]);
    if (x > -3 && x < 1 && y > -2 && y < 5) dot(A.X(x), A.Y(y), 3, { color: C.blue, fill: C.sky, width: 1, alpha: pa * ka });
  }
  // the lowest true error (it needs the truth) and the corner, for the method shown
  const ma = lab(.5);
  if (o.m > 0) {
    const be = o.m === 2 ? [S.bR, S.bE] : [S.trho[S.kbest - 1], S.teta[S.kbest - 1]];
    dot(A.X(Math.log10(be[0])), A.Y(Math.log10(be[1])), 7, { color: C.ink, fill: null, width: 1.5, alpha: ma });
  }
  if (o.m === 2) { const x = A.X(Math.log10(S.cR)), y = A.Y(Math.log10(S.cE)); mk.square(5)(x, y, ma); }
  // the estimate shown, or where it went
  const ex = Math.log10(E.rho), ey = Math.log10(E.eta);
  if (o.m > 0 && ex > -3 && ex < 1 && ey > -2 && ey < 5) dot(A.X(ex), A.Y(ey), 5.5, { color: '#fff', fill: C.accent, width: 1.4, alpha: lab(.45) });
  else math('\\rm{estimate off the chart:}\\ ‖m̂‖ = ' + sci(E.eta), PC.x + PC.w, PC.y - 14, { size: 16, color: C.accent, align: 'right', alpha: ma });
  text('noise level', A.X(lx) + 7, PC.y + 20, { size: 14, color: C.muted, alpha: seg(.3, .3) });
  const marks = o.m === 2 ? [[mk.ring(6), '\\rm{lowest error}'], [mk.square(5), '\\rm{corner}']] : o.m === 1 ? [[mk.ring(6), '\\rm{lowest error}']] : [];
  legend(PC.x + 8, PC.y + PC.h - (marks.length ? 56 : 35), [[[mk.line(C.navy, 2.2), '\\rm{Tikhonov}'], [mk.dot(C.blue, C.sky, 3), '\\rm{truncated SVD}']],
                                      ...(marks.length ? [marks] : [])], lab(.46));
}
function panelD(o, S, f) {
  sub('d', 508, PD.y - 14, 'Picard plot', lab(.12));
  const A = axes({ ...PD, xlim: [.5, NC + .5], ylim: [-18, 1], xticks: [1, 16, 32, 48, 64], yticks: [-16, -12, -8, -4, 0],
                   xfmt: () => '', yfmt: p10, tickSize: 16, ylabelGap: 50, ylabel: '\\rm{magnitude}', progress: seg(.12, .35) });
  const F = axes({ ...PF, xlim: [.5, NC + .5], ylim: [-.12, 1.2], xticks: [1, 16, 32, 48, 64], yticks: [0, 1],
                   xfmt: v => String(v), tickSize: 16, ylabelGap: 50, xlabel: '\\rm{index}\\ i', ylabel: 'f_i', progress: seg(.14, .35) });
  const lf = Math.log10(S.sig), fa = seg(.3, .35), la = lab(.4);
  A.inside(() => {
    line([[PD.x, A.Y(lf)], [PD.x + PD.w, A.Y(lf)]], { color: C.guide, width: 1.2, dash: [5, 4], alpha: seg(.3, .3) });
    if (o.m === 2) { const y = A.Y(Math.log10(alphaOf(o.u))); line([[PD.x, y], [PD.x + PD.w, y]], { color: C.accent, width: 1.3, dash: [3, 3], alpha: la }); }
  });
  // the filter factors under it: a step per index, washed under
  F.inside(() => {
    const P = [[F.X(.5), F.Y(0)]];
    for (let j = 0; j < NC; j++) { P.push([F.X(j + .5), F.Y(f[j])]); P.push([F.X(j + 1.5), F.Y(f[j])]); }
    P.push([F.X(NC + .5), F.Y(0)]);
    if (fa > 0) { ctx.save(); ctx.globalAlpha *= fa; ctx.fillStyle = C.wash; ctx.beginPath(); P.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.fill(); ctx.restore(); }
    line([[PF.x, F.Y(0)], [PF.x + PF.w, F.Y(0)]], { color: C.rule, width: 1, alpha: fa });
    line(P.slice(1, -1), { color: C.accent, width: 1.6, progress: seg(.3, .4) });
  });
  if (o.m === 1) {
    const x = A.X(o.k + .5);
    for (const [y0, y1] of [[PD.y, PD.y + PD.h], [PF.y, PF.y + PF.h]]) line([[x, y0], [x, y1]], { color: C.accent, width: 1.3, dash: [3, 3], alpha: la });
  }
  const da = seg(.2, .3), ba = seg(.26, .3);
  for (let j = 0; j < NC; j++) {
    const ls = Math.log10(SV[j]), lb = Math.log10(Math.abs(S.beta[j]));
    if (da > 0) dot(A.X(j + 1), A.Y(Math.max(-17.8, ls)), 2.3, { color: C.ink, fill: C.ink, width: .6, alpha: da });
    if (ba > 0) dot(A.X(j + 1), A.Y(Math.max(-17.8, lb)), 2.3, { color: C.blue, fill: C.blue, width: .6, alpha: ba });
  }
  const lev = o.m === 2 ? [mk.line(C.accent, 1.3, [3, 3]), 's_i = \\alpha'] : o.m === 1 ? [mk.vbar(C.accent), '\\rm{cut after}\\ k'] : null;
  legend(PD.x + 8, PD.y + PD.h - 52, [[[mk.dot(C.ink, C.ink, 2.3), '\\rm{singular value}\\ s_i'], [mk.dot(C.blue, C.blue, 2.3), '|u_i^{\\rm{T}}d|']],
                                      [[mk.line(C.guide, 1.2, [5, 4]), '\\rm{noise floor}'], ...(lev ? [lev] : [])]], lab(.48), { rh: 20 });
}

function draw() {
  const o = now(), S = SETS[o.nz][o.dr], f = filt(o), E = est(f, S.beta), mh = synth(E.c);
  controls(o, seg(0, .3));
  panelA(o, S);
  panelB(o, S, E, mh);
  panelC(o, S, E);
  panelD(o, S, f);
  math(D.params, 20, H - 14, { size: 14, color: C.muted, alpha: seg(.45, .3) });
  placeKeys([o.m, o.nz, o.dr, o.k, o.u.toFixed(5), o.sw, o.an].join(':'));
}
const POSTER_T = T0 + TS + HOLD / 2;          // the tour's Tikhonov sweep done, held at the discrepancy principle
/* the address can choose a state (for the overlap check of every state); nothing when absent */
if (['m', 'nz', 'dr', 'a', 'u', 'k', 'sw', 'an'].some(k => QS.has(k))) {
  const o = { m: 2, nz: 1, dr: 0 };
  ST = { m: { none: 0, tsvd: 1, tik: 2 }[QS.get('m')] ?? 2, nz: +(QS.get('nz') || 1), dr: +(QS.get('dr') || 0), sw: null, an: null };
  const S = SETS[ST.nz][ST.dr];
  ST.u = QS.has('a') ? uOf(+QS.get('a')) : QS.has('u') ? +QS.get('u') : uOf(S.adp);
  ST.k = QS.has('k') ? +QS.get('k') : S.kdp;
  if (QS.get('sw') === '1') ST.sw = { t0: POSTER_T, ph: phase(ST.m === 2 ? ST.u : rOfK(ST.k)) };
  if (QS.get('an') === '1') ST.an = { t0: POSTER_T, d0: ST.dr };
}
buildControls();
keyStandIns([{ radio: true, label: 'Method', ids: ['m0', 'm1', 'm2'] }, { radio: true, label: 'Noise level', ids: ['n0', 'n1', 'n2'] },
             { radio: true, label: 'Noise draw', ids: ['d0', 'd1', 'd2'] }, { ids: ['an'] },
             { label: 'Regularization strength', ids: ['sl'] }, { ids: ['sw', 'dp', 'cn'] }]);
boot();
"""


def nice_scale(v):
    """The axis half-height for a range of +-v: 1, 2 or 5 times a power of ten, and that power."""
    p = int(np.floor(np.log10(v)))
    for y in (1, 2, 5, 10):
        if y * 10 ** p >= v:
            return (y, p) if y < 10 else (1, p + 1)


def compute():
    P = L.Problem()
    sets, info = [], []
    for li in range(len(L.LEVELS)):
        row, irow = [], []
        for ri in range(len(L.SEEDS)):
            Dd = P.data(li, ri)
            b = Dd["beta"]
            path = P.tik_path(b)
            tp = P.tsvd_path(b)
            adp, abest = P.tik_dp(Dd), P.tik_best(b)
            acn, kap = P.tik_corner(b)
            kdp, kbest = P.tsvd_dp(Dd), P.tsvd_best(b)
            ebest, ecn, edp = P.ev(P.tik(abest), b), P.ev(P.tik(acn), b), P.ev(P.tik(adp), b)
            naive = P.solution(np.ones(L.N), b)
            row.append(dict(d=common.f32(Dd["d"]), beta=L.f64(b), sig=Dd["sig"], delta=Dd["delta"],
                            adp=adp, acn=acn, abest=abest, kdp=kdp, kbest=kbest,
                            bR=ebest[0], bE=ebest[1], cR=ecn[0], cE=ecn[1],
                            rho=common.f32(path[:, 0]), eta=common.f32(path[:, 1]),
                            trho=common.f32(tp[:, 0]), teta=common.f32(tp[:, 1])))
            irow.append(dict(D=Dd, path=path, tsvd=tp, adp=adp, abest=abest, acn=acn, kap=kap, kdp=kdp, kbest=kbest,
                             edp=edp, ebest=ebest, ecn=ecn, naive=naive))
        sets.append(row)
        info.append(irow)
    naive_sc = [nice_scale(max(np.abs(q["naive"]).max() for q in irow)) for irow in info]
    data = dict(
        n=L.N, s=L.f64(P.s), V=L.f64(P.V), t=L.f64(P.t), m=L.f64(P.m), mnorm=P.mnorm, Gm=common.f32(P.Gm),
        la0=float(P.la[0]), la1=float(P.la[-1]), na=L.NA, names=list(L.LEVEL_NAMES),
        naive=[dict(y=y, p=p) for y, p in naive_sc], sets=sets,
        params=(r"\rm{Gaussian blur, }N = 64\rm{ cells, width 0.045; noise }\sigma\rm{ = 0.1, 1 or 10% of max }Gm"
                r"\rm{, three draws; discrepancy principle }" "\u2016Gm\u0302 - d\u2016" r" = \sigma\sqrt{N}"),
    )
    return P, info, data, naive_sc


def page_states(P, info, data):
    """The page's estimate in a set of reader's states against numpy: max differences."""
    la0, la1 = data["la0"], data["la1"]
    uOf = lambda a: (np.log10(a) - la0) / (la1 - la0)
    st = []
    for li, ri in ((1, 0), (0, 1), (2, 2)):
        z = info[li][ri]
        st += [(2, li, ri, uOf(z["adp"]), 0), (2, li, ri, uOf(z["abest"]), 0), (2, li, ri, uOf(z["acn"]), 0),
               (2, li, ri, 0.0, 0), (2, li, ri, 1.0, 0), (1, li, ri, 0, z["kdp"]), (1, li, ri, 0, 40), (0, li, ri, 0, 0)]
    exprs = [f"(() => {{ ST = {{m: {m}, nz: {li}, dr: {ri}, u: {float(u)!r}, k: {int(k) or 1}, sw: null, an: null}}; const o = now(), "
             f"S = SETS[o.nz][o.dr], f = filt(o), E = est(f, S.beta), mm = synth(E.c); return [E.rho, E.eta, E.err, ...mm]; }})()"
             for m, li, ri, u, k in st]
    got = L.check_page(NAME, exprs)
    worst = dict(m=0.0, rho=0.0, eta=0.0, err=0.0, naive=0.0)
    for (m, li, ri, u, k), g in zip(st, got):
        b = info[li][ri]["D"]["beta"]
        f = np.ones(L.N) if m == 0 else P.tsvd(k) if m == 1 else P.tik(10 ** (la0 + (la1 - la0) * u))
        rho, eta, err = P.ev(f, b)
        mm = P.solution(f, b)
        dm = np.abs(g[3:] - mm).max() / max(1.0, np.abs(mm).max())
        if m == 0:
            worst["naive"] = max(worst["naive"], dm)
            continue
        worst["m"] = max(worst["m"], dm)
        worst["rho"] = max(worst["rho"], abs(g[0] - rho) / rho)
        worst["eta"] = max(worst["eta"], abs(g[1] - eta) / eta)
        worst["err"] = max(worst["err"], abs(g[2] - err) / err)
    return len(st), worst


def validate(P, info, data):
    """The checks of the check file (README, "Numerics and validation")."""
    import mpmath as mp
    from scipy.linalg import lstsq
    mp.mp.dps = 60
    N, s = L.N, P.s
    # 1. singular values: G is symmetric positive definite, so they are its eigenvalues;
    #    in 60-digit arithmetic, for the matrix of the formula and for its float64 entries
    xs = [(mp.mpf(i) + mp.mpf("0.5")) / N for i in range(N)]
    sg = mp.mpf("0.045")
    Gx = mp.matrix(N, N)
    Gf = mp.matrix(N, N)
    for i in range(N):
        for j in range(N):
            Gx[i, j] = mp.exp(-(xs[i] - xs[j]) ** 2 / (2 * sg ** 2)) / (sg * mp.sqrt(2 * mp.pi)) / N
            Gf[i, j] = mp.mpf(float(P.G[i, j]))
    ex = sorted([float(v) for v in mp.eigsy(Gx, eigvals_only=True)], reverse=True)
    ef = sorted([float(v) for v in mp.eigsy(Gf, eigvals_only=True)], reverse=True)
    ex, ef = np.array(ex), np.array(ef)
    rel = np.abs(s - ef) / ef
    # 2. Tikhonov through the filter against stacked least squares (QR), every set, three alphas
    d2 = 0.0
    for irow in info:
        for z in irow:
            b, d = z["D"]["beta"], z["D"]["d"]
            for a in (z["adp"], z["abest"], z["acn"]):
                ms = P.solution(P.tik(a), b)
                mq = lstsq(np.vstack([P.G, a * np.eye(N)]), np.concatenate([d, np.zeros(N)]), lapack_driver="gelsy")[0]
                d2 = max(d2, np.abs(ms - mq).max() / np.abs(ms).max())
    # 3. Tikhonov at the discrepancy alpha (1 %, draw 1) in 60-digit arithmetic: (G^T G + a^2 I) m = G^T d
    q = info[1][0]
    a = mp.mpf(q["adp"])
    dv = mp.matrix([mp.mpf(float(v)) for v in q["D"]["d"]])
    A = Gf.T * Gf + a * a * mp.eye(N)
    m60 = mp.lu_solve(A, Gf.T * dv)
    m60 = np.array([float(v) for v in m60])
    ms = P.solution(P.tik(q["adp"]), q["D"]["beta"])
    d3 = np.abs(ms - m60).max() / np.abs(m60).max()
    # 4. the discrepancy principle: |G m - d| by a matrix-vector product, against delta
    d4 = max(abs(np.linalg.norm(P.G @ P.solution(P.tik(z["adp"]), z["D"]["beta"]) - z["D"]["d"]) - z["D"]["delta"]) / z["D"]["delta"]
             for irow in info for z in irow)
    # 5. the corner: closed-form curvature against finite differences
    fine = np.linspace(P.la[0], P.la[-1], 4001)
    b = q["D"]["beta"]
    kap = np.array([P.curvature(l, b) for l in fine])
    pts = np.array([P.ev(P.tik(10 ** l), b) for l in fine])
    xr, ye = np.log(pts[:, 0]), np.log(pts[:, 1])
    dx, dy = np.gradient(xr, fine), np.gradient(ye, fine)
    ddx, ddy = np.gradient(dx, fine), np.gradient(dy, fine)
    kfd = (dx * ddy - ddx * dy) / (dx * dx + dy * dy) ** 1.5
    d5 = np.abs(kap - kfd)[50:-50].max()
    acf = 10 ** fine[np.argmax(kfd)]
    # 6. truncated SVD against numpy's pseudo-inverse cut between s_k and s_k+1
    d6 = 0.0
    for irow in info:
        for z in irow:
            k = z["kdp"]
            cut = np.sqrt(s[k - 1] * s[k]) / s[0]
            mp_ = np.linalg.pinv(P.G, rcond=cut) @ z["D"]["d"]
            mt = P.solution(P.tsvd(k), z["D"]["beta"])
            d6 = max(d6, np.abs(mp_ - mt).max() / np.abs(mt).max())
    # 7. the page against numpy
    nst, worst = page_states(P, info, data)
    # 8. Hadamard: the unregularized solution for the three draws (1 %) and Tikhonov's
    hz = info[1]
    dd = [z["D"]["d"] for z in hz]
    nv = [z["naive"] for z in hz]
    tk = [P.solution(P.tik(z["adp"]), z["D"]["beta"]) for z in hz]
    ddat = np.linalg.norm(dd[0] - dd[1]) / np.linalg.norm(dd[0])
    dnv = np.linalg.norm(nv[0] - nv[1]) / P.mnorm
    dtk = np.linalg.norm(tk[0] - tk[1]) / P.mnorm
    nvres = np.linalg.norm(P.G @ nv[0] - dd[0])
    # 9. the Picard plot: where the noise-free coefficients |u_i^T G m| = s_i |v_i^T m| fall under sigma
    cf = np.abs(P.U.T @ P.Gm)
    zz = [np.linalg.norm(P.z[sd]) for sd in L.SEEDS]

    T = []
    say = T.append
    say("Figure 4, undoing a blur (an ill-posed inverse problem): check of tools/numfig/sp_inv_reg.py")
    say("")
    say("MODEL (his page inverse-regularization-animation.html, the same numbers)")
    say(f"  N = {N} cells, x_i = (i + 1/2)/N; G_ij = exp(-(x_i - x_j)^2/(2 s^2)) / (s sqrt(2 pi)) / N, s = {L.SIG}.")
    say(f"  m(x) = exp(-((x - 0.28)/0.07)^2) + 0.75 [0.58 < x < 0.8] at the cells: |m| = {P.mnorm:.6f}, max Gm = {P.dmax:.6f}.")
    say(f"  d = Gm + e, e = sigma z, sigma = level max|Gm| = {', '.join(f'{lv * P.dmax:.4e}' for lv in L.LEVELS)} for")
    say(f"  levels {', '.join(L.LEVEL_NAMES)}; z standard normal, numpy default_rng seeds {L.SEEDS} (draws 1, 2, 3),")
    say(f"  |z| = {', '.join(f'{v:.4f}' for v in zz)} (expected sqrt(64) = 8). The noise level of the discrepancy principle is")
    say("  delta = sigma sqrt(N) = 8 sigma, the expected |e|, as his pages take it.")
    say("  Estimates: m = sum_i f_i (u_i^T d / s_i) v_i with numpy's SVD G = U diag(s) V^T (LAPACK gesdd, float64):")
    say("  none f = 1; truncated SVD f_i = [i <= k]; Tikhonov f_i = s_i^2 / (s_i^2 + alpha^2). Residual, norm and error from")
    say("  the coefficients: |Gm - d| = |(1 - f) U^T d|, |m| = |f U^T d / s|, error |m - m_true| / |m_true|.")
    say("")
    say("GRID AND PARAMETERS")
    say(f"  The problem is discrete by definition (his 64 cells); there is no mesh to converge. The strength slider spans")
    say(f"  log10(alpha / s_1) = -7 to 1 (his range, alpha = {10 ** P.la[0]:.4e} to {10 ** P.la[-1]:.4f}); the L-curve is drawn")
    say(f"  through {L.NA} strengths (40 per decade), the estimate for any strength the reader sets is the page's own sum")
    say("  (7. below). Discrepancy alpha: brentq on log10 alpha (xtol 1e-14); best alpha: bounded minimization of the")
    say("  true error (xatol 1e-12 in log10 alpha); corner: the maximum of the closed-form curvature, refined from 4001")
    say("  strengths. Truncated SVD: every k from 1 to 64.")
    say("")
    say("VALIDATION")
    say("  1. Singular values against 60-digit arithmetic (mpmath; G is symmetric positive definite, so its singular")
    say("     values are its eigenvalues). numpy against the exact eigenvalues of the float64 matrix: relative")
    say(f"     difference {rel[:24].max():.1e} for i <= 24, {rel[:40].max():.1e} for i <= 40, {rel[:56].max():.1e} for i <= 56; the last")
    say(f"     ones are rounding: s_62, s_63, s_64 = {s[61]:.3e}, {s[62]:.3e}, {s[63]:.3e} (numpy) against {ef[61]:.3e}, {ef[62]:.3e},")
    say(f"     {ef[63]:.3e} (exact). Condition number s_1/s_64: {ex[0] / ex[-1]:.3e} for the exact matrix of the formula,")
    say(f"     {ef[0] / ef[-1]:.3e} for its float64 entries, {s[0] / s[-1]:.3e} from numpy's SVD. All exceed 1/eps = {1 / np.finfo(float).eps:.2e}:")
    say("     in double precision G is numerically singular, so the unregularized solution is not even computable; the")
    say("     figure's is numpy's, and its exact value would be larger still (s_64 is 3 times smaller).")
    say(f"     s_1 = {s[0]:.10f} (exact {ex[0]:.10f}); s_i falls below eps s_1 = {np.finfo(float).eps * s[0]:.2e} at i = {int(np.argmax(ex < np.finfo(float).eps * s[0])) + 1} (exact values).")
    say("  2. Tikhonov through the SVD filter against an independent solver, the stacked least squares")
    say("     [G; alpha I] m = [d; 0] by scipy.linalg.lstsq (complete orthogonal factorization, gelsy), at the")
    say(f"     discrepancy, best and corner alphas of all nine data sets: largest difference {d2:.1e} of max|m|.")
    say("  3. Tikhonov at the discrepancy alpha (1 %, draw 1) against 60-digit arithmetic, (G^T G + alpha^2 I) m = G^T d")
    say(f"     with the float64 G and d (mpmath lu_solve): largest difference {d3:.1e} of max|m|.")
    say(f"  4. The discrepancy principle: |G m - d| by a matrix-vector product at alpha_DP against delta, all nine sets:")
    say(f"     largest relative difference {d4:.1e}.")
    say(f"  5. The L-curve curvature in closed form against finite differences of (ln |Gm - d|, ln |m|) on 4001")
    say(f"     strengths (1 %, draw 1): largest difference {d5:.1e} (curvature at the corner {q['kap']:.3f}); the corner at")
    say(f"     alpha = {q['acn']:.5e} (closed form, refined) and {acf:.5e} (finite differences, grid).")
    say(f"  6. Truncated SVD at k_DP against numpy's pseudo-inverse with the cut between s_k and s_k+1, all nine sets:")
    say(f"     largest difference {d6:.1e} of max|m|.")
    say(f"  7. The page (its est() and synth(), float64 V, s, U^T d from DATA) against numpy in {nst} reader's states")
    say(f"     (Tikhonov at the discrepancy, best and corner alphas and at both ends of the slider, truncated SVD at k_DP")
    say(f"     and k = 40, no regularization, for three data sets): estimate {worst['m']:.1e} of max|m|, residual {worst['rho']:.1e},")
    say(f"     norm {worst['eta']:.1e}, error {worst['err']:.1e} (relative); the unregularized estimate {worst['naive']:.1e} of its max.")
    say("")
    say("HADAMARD'S THIRD CONDITION (1 % noise)")
    say(f"  Draws 1 and 2 differ by |d_1 - d_2| / |d_1| = {100 * ddat:.2f} %. The unregularized estimates: max|m| = "
        f"{', '.join(f'{np.abs(v).max():.3e}' for v in nv)},")
    say(f"  |m| = {', '.join(f'{np.linalg.norm(v):.3e}' for v in nv)} for draws 1, 2, 3 (the truth: |m| = {P.mnorm:.3f}, max 1);")
    say(f"  |m_1 - m_2| / |m_true| = {dnv:.3e}: a {100 * ddat:.2f} % change of the data moves the solution by {dnv:.1e} times the")
    say(f"  solution itself. Tikhonov at each draw's discrepancy alpha: |m_1 - m_2| / |m_true| = {100 * dtk:.2f} %.")
    say(f"  (The unregularized estimate's residual by a matrix-vector product is {nvres:.2e}, rounding at its scale; the")
    say("  closed form says 0.)")
    say("")
    say("THE PICARD PLOT")
    for li, lv in enumerate(L.LEVELS):
        sig = lv * P.dmax
        above = np.nonzero(cf > sig)[0]
        say(f"  {L.LEVEL_NAMES[li]:>4s}: sigma = {sig:.3e}; the noise-free coefficients |u_i^T G m| exceed sigma up to i = {above.max() + 1}"
            f" ({len(above)} of the first {above.max() + 1})")
    say("")
    say("NUMBERS (relative error |m - m_true| / |m_true| in brackets)")
    say("  noise draw | Tikhonov: discrepancy  best (needs the truth)  L-curve corner | TSVD: k_DP  k_best")
    for li in range(3):
        for ri in range(3):
            z = info[li][ri]
            say(f"  {L.LEVEL_NAMES[li]:>4s}  {ri + 1}   | {z['adp']:.4e} ({100 * z['edp'][2]:.2f} %)  {z['abest']:.4e} ({100 * z['ebest'][2]:.2f} %)  "
                f"{z['acn']:.4e} ({100 * z['ecn'][2]:.2f} %) | {z['kdp']:2d} ({100 * z['tsvd'][z['kdp'] - 1, 2]:.2f} %)  "
                f"{z['kbest']:2d} ({100 * z['tsvd'][z['kbest'] - 1, 2]:.2f} %)")
    say("")
    say("DISPLAY")
    say("  W x H = 1000 x 740. Untouched, the figure tours: 0.6 s at the discrepancy alpha (1 %, draw 1) while the intro")
    say("  draws, Tikhonov swept once (12 s, a cosine in log10 alpha from alpha_DP, stronger first), held 1.8 s, no")
    say("  regularization for 6 s with a new noise draw every 1.2 s (Hadamard), truncated SVD swept once (12 s, k from")
    say("  k_DP, fewer terms first) and held 1.8 s; then again. POSTER_T = 13.5 s: the sweep done, held at alpha_DP.")
    say("  Controls: method, noise level and noise draw chips, 'animate' (a new draw every 1.2 s, his Animate noise),")
    say("  the strength slider (Tikhonov alpha, log; truncated SVD k), 'sweep' (his Play sweep), 'discrepancy")
    say("  principle', 'L-curve corner'. No regularization draws (b) on its own scale (10^12, 10^13, 10^14 for the three")
    say("  levels). An estimate outside (b)'s axes is clipped and its max stated; an L-curve point outside (c) is stated")
    say("  with its norm. Query keys: m=none|tsvd|tik, nz, dr, a or u, k, sw, an.")
    txt = "\n".join(T) + "\n"
    with open(os.path.join(common.HERE, "sp_inv_reg.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    return txt


def build():
    P, info, data, naive_sc = compute()
    q = info[1][0]
    print(f"s_1 = {P.s[0]:.6f}, s_64 = {P.s[-1]:.3e}, s_1/s_64 = {P.s[0] / P.s[-1]:.3e}")
    for li in range(3):
        for ri in range(3):
            z = info[li][ri]
            print(f"noise {L.LEVEL_NAMES[li]:>4s} draw {ri + 1}: alpha DP {z['adp']:.4e} (err {z['edp'][2]:.4f}), best "
                  f"{z['abest']:.4e} ({z['ebest'][2]:.4f}), corner {z['acn']:.4e} ({z['ecn'][2]:.4f}); TSVD k DP {z['kdp']}, "
                  f"best {z['kbest']}; naive max {np.abs(z['naive']).max():.3e}")
    common.build_html(NAME, TITLE, ARIA, W, H, data, JS, digits=16)
    png = common.still(NAME)
    print("still:", png)
    validate(P, info, data)
    return P, info, data


if __name__ == "__main__":
    build()
