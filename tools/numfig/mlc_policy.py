"""Figure 29 of the machine learning guide (image26): what sits inside a
reinforcement learning agent, a table or a neural network.

(a) The tabular policy: the Q-table the run of Figure 30 learned in 300
episodes (mlc_grid.py), one row per state and one column per action; the agent
looks up its row and takes the largest value.
(b) The neural network policy: a deep Q-network (mlc_dqn.py) trained by
interaction on the same world with the position measured as two real numbers.
It takes (x, y) in and puts out the four action values; the page runs its
forward pass at every frame from the trained weights.

Both agents walk to the goal from the same starting positions, the table's
from the square the position lies in.

Run: python tools/numfig/mlc_policy.py   (trains the network once, ~2 min,
then reuses the weights cached in the temp directory)
"""
import os
import tempfile

import numpy as np

import mlc_dqn as dq
import mlc_grid as g
import mlc_lib as lib

NAME = "mlc-policy"
SEED = 3
CACHE = os.path.join(tempfile.gettempdir(), f"mlc_dqn_seed{SEED}_h{dq.HID}.npz")

# ------------------------------------------------------------------ (a) the table
snaps, log = g.run()
QT = snaps[299]
Qs = g.q_star()

# ------------------------------------------------------------------ (b) the network
if os.path.isfile(CACHE):
    z = np.load(CACHE)
    W = [(z["w0"], z["b0"]), (z["w1"], z["b1"]), (z["w2"], z["b2"])]
    info = {"episodes": int(z["episodes"]), "transitions": int(z["transitions"])}
else:
    import torch
    torch.set_num_threads(1)
    net, info = dq.train(seed=SEED)
    W = dq.weights(net)
    np.savez(CACHE, w0=W[0][0], b0=W[0][1], w1=W[1][0], b1=W[1][1], w2=W[2][0], b2=W[2][1], **info)
NPAR = sum(w.size + b.size for w, b in W)

STARTS = [(0.37, 0.58), (2.71, 0.26), (0.44, 3.62), (1.63, 2.21)]


def roll_net(p):
    pts, acts = [tuple(p)], []
    p = np.array(p, float)
    for _ in range(30):
        a = int(np.argmax(dq.forward(W, p)[-1]))
        p, r, done = dq.env_step(p, a)
        pts.append(tuple(p)); acts.append(a)
        if done:
            break
    return pts, acts


def roll_table(p):
    s = g.sid(int(p[0]), int(p[1]))
    cells, acts = [g.xy(s)], []
    for _ in range(30):
        a = int(np.argmax(QT[s]))
        s, r, done = g.step(s, a)
        cells.append(g.xy(s)); acts.append(a)
        if done:
            break
    return cells, acts


laps = []
for p in STARTS:
    pn, an = roll_net(p)
    pt, at = roll_table(p)
    laps.append({"net": pn, "na": an, "tab": pt, "ta": at})

# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-policy: Figure 29, a tabular policy and a neural network policy")
say("")
say("(a) TABLE: the Q-table of Figure 30's run after 300 episodes (mlc_grid.py, seed 21):")
say("  25 rows (states) x 4 columns (up, down, left, right) = 100 numbers, no neurons.")
bad = g.policy_is_shortest(QT)
say(f"  largest value in every row leads one square closer to the goal: {len(bad) == 0}")
say(f"  max |Q - Q*| over the 24 non goal rows: {np.max(np.abs(QT - Qs)[np.arange(25) != 24]):.4f} (Q* by value iteration)")
say("")
say("(b) NETWORK: deep Q-network on the continuous world (mlc_dqn.py): position (x, y) real,")
say("  a move shifts it by 1 (the wall stops it), the goal is the square [4,5) x [4,5),")
say("  +1 there, -0.02 per other step, gamma = 0.95. 2 inputs (x/2.5 - 1, y/2.5 - 1),")
say(f"  hidden 12 tanh, 12 tanh, 4 linear outputs: {NPAR} weights and biases.")
say("  trained by interaction: epsilon-greedy from 1 to 0.05 over 15000 steps, 40000 steps,")
say("  replay buffer 20000, batch 64, Huber loss, Adam 1e-3, target network synced every 250")
say(f"  steps; random start anywhere; {info['episodes']} episodes; torch seed {SEED}.")
say("")
say("CHECK 1: the network at the 25 square centres against the exact Q* of the grid")
errs, agree = [], 0
for s in range(25):
    x, y = g.xy(s)
    if (x, y) == g.GOAL:
        continue
    q = dq.forward(W, (x + .5, y + .5))[-1]
    errs.append(np.max(np.abs(q - Qs[s])))
    best = set(np.flatnonzero(np.isclose(Qs[s], Qs[s].max())))
    agree += int(np.argmax(q)) in best
say(f"  max |Q_net - Q*| = {max(errs):.4f}, mean {np.mean(errs):.4f}; its largest output is an optimal")
say(f"  action at {agree} of 24 centres.")
say("")
say("CHECK 2: greedy rollouts of the network from 1000 random real starting positions")
rng = np.random.default_rng(7)
ok = opt = 0
for _ in range(1000):
    p = dq.random_start(rng)
    dist = (4 - int(p[0])) + (4 - int(p[1]))
    pts, acts = roll_net(p)
    done = pts[-1][0] >= 4 and pts[-1][1] >= 4
    ok += done
    opt += done and len(acts) == dist
say(f"  reach the goal: {ok} / 1000; by a shortest route: {opt} / 1000")
say("")
say("CHECK 3: the page's forward pass is this one (numpy float64, tanh); at the four")
say("  starting positions the outputs are")
for p in STARTS:
    say(f"    (x, y) = {p}: Q = {np.round(dq.forward(W, p)[-1], 4)}")
say("")
say("THE WALKS SHOWN")
for lp, p in zip(laps, STARTS):
    say(f"  from {p}: network {len(lp['na'])} steps, table {len(lp['ta'])} steps from square {lp['tab'][0]}")

# ------------------------------------------------------------------ timing
# Round 3 (30 Sep 2026), the client: "slow down Figures 28, 29, 30", the motion
# was too fast to follow. The agents step half as fast as in the first version,
# and rest on each square long enough to read the table's row and the network.
L0 = .6                                       # the first lap opens (the intro is unchanged)
LEAD, STEP, GLIDE, REST = .6, 1.25, .7, 1.6   # a lap: wait, one move per STEP gliding GLIDE, rest at the goal
FIN, FOUT = .4, .5                            # the lap fades in and out
nmax = [max(len(lp["na"]), len(lp["ta"])) for lp in laps]
laplen = [LEAD + n * STEP + REST + FOUT for n in nmax]
say("")
say("TIMING (Round 3, 30 Sep 2026: the client asked for the figure slowed down; about 2 x)")
say(f"  one move every {STEP} s (was 0.62 s): both agents glide {GLIDE} s (was 0.38) and rest {STEP - GLIDE:.2f} s on the")
say("  new square (was 0.24) while the table's row and the network's outputs can be read.")
say(f"  A lap: the agents appear in {FIN} s (was 0.25) and set off {LEAD} s after it opens (was 0.3); at the")
say(f"  goal they rest {STEP - GLIDE + REST:.2f} s (was 1.14), then fade out in {FOUT} s (was 0.3). Laps "
    + ", ".join(f"{v:.2f}" for v in laplen) + " s:")
say(f"  the four walks repeat every {sum(laplen):.1f} s (was 20.9 s). The first move at {L0 + LEAD:.1f} s (was 0.9);")
say(f"  the intro is unchanged (drawn by 1.0 s). Poster (reduced motion, print): {L0 + LEAD + 2 * STEP + GLIDE + .12:.2f} s")
say("  (was 2.64), lap 1, three moves made, the same frame as before.")
say('')
say('THE PAGE (Round 4, 5 Oct 2026)')
say("  (a) The table shows 11 of its 25 rows at a time, the window following the agent's row as it walks")
say("  (and gliding to the next lap's start as that lap fades in); every number set at 16 units.")
say('  Ties: in states (0,0), (0,1), (1,1), (1,2), (1,3) and (2,3) the two best actions (up and right) lead')
say('  by equally short routes, and their learned values agree to within 2e-7 (largest gap 1.6e-7, state (1,3)), so')
say("  the page's four decimals cannot tell them apart. The grid's arrows and the agent take the run's own")
say("  choice (the walks visit all six states, and carry it); the readout names the tie: 'takes right (a")
say("  tie with up)'. (b) Two outputs equal to two decimals are printed to three, the runner up named.")
say("  At a new lap the network's input glides from the last lap's goal to the new start over 0.4 s while")
say('  the agent fades in, so its neurons, edges and outputs change continuously, never in one frame.')

DATA = {
    "q": QT.round(4).tolist(),
    "W": [[w.tolist(), b.tolist()] for w, b in W],
    "laps": laps,
    "npar": NPAR,
}

JS = (f"const L0 = {L0}, LEAD = {LEAD}, STEP = {STEP}, GLIDE = {GLIDE}, REST = {REST}, FIN = {FIN}, FOUT = {FOUT};"
      + r"""
const MOVE = [[0, 1], [0, -1], [-1, 0], [1, 0]], WORD = ['up', 'down', 'left', 'right'];
const Qt = DATA.q, NW = DATA.W, LAPS = DATA.laps;
/* the network, forward: inputs scaled to [-1, 1], two tanh layers, linear out */
function forward(p) {
  let h = [p[0] / 2.5 - 1, p[1] / 2.5 - 1]; const acts = [h];
  for (let l = 0; l < 3; l++) {
    const [w, b] = NW[l], z = b.map((bi, i) => { let s = bi; for (let j = 0; j < h.length; j++) s += w[i][j] * h[j]; return s; });
    h = l < 2 ? z.map(Math.tanh) : z; acts.push(h);
  }
  return acts;
}
const argmax = v => v.reduce((m, x, i) => x > v[m] ? i : m, 0);
/* ---- the laps: both agents walk from the same place */
const lapLen = lp => LEAD + Math.max(lp.na.length, lp.ta.length) * STEP + REST + FOUT;
const LAPT = LAPS.map(lapLen), CYCLE = LAPT.reduce((a, b) => a + b, 0);
function lapNow() {
  if (t < L0) return { k: 0, u: 0, pre: true };
  let r = (t - L0) % CYCLE, k = 0;
  while (r >= LAPT[k]) { r -= LAPT[k]; k++; }
  return { k, u: r };
}
function walk(pts, u) {            // position along a walk at lap time u
  const s = u - LEAD, n = pts.length - 1;
  if (s <= 0) return { p: pts[0], i: 0 };
  const i = Math.min(n, Math.floor(s / STEP)), f = i >= n ? 0 : easeInOut(clamp((s - i * STEP) / GLIDE));
  if (i >= n) return { p: pts[n], i: n };
  return { p: [lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f)], i: f >= 1 ? i + 1 : i };
}
const POSTER_T = L0 + LEAD + 2 * STEP + GLIDE + .12;   // lap 1, three moves made: both panels at work
/* the table's own action in each state: the one its walks take where they pass (the Q-values of the
   two equally short routes agree to within 2e-7, so the page's four decimals cannot split them; the walks
   carry the run's own choice), elsewhere the largest value */
const ACT = Qt.map(argmax);
LAPS.forEach(lp => lp.ta.forEach((a, i) => { ACT[lp.tab[i][1] * 5 + lp.tab[i][0]] = a; }));
const tieWith = s => { const a = ACT[s]; let o = -1; for (let k = 0; k < 4; k++) if (k !== a && Math.abs(Qt[s][k] - Qt[s][a]) < 5e-5) o = k; return o; };
/* ---- layout */
const GA = { x: 30, y: 74, s: 170 }, PB = { x: 528, y: 74, s: 170 };
const TX = 240, TW = [62, 46, 46, 46, 46], TY = 76, RH = 27, NR = 11;    // the table: a window of NR of its 25 rows
/* the window's first row, a real number: centred on the agent's row as it walks, gliding to the next
   lap's start as that lap fades in */
const rowOf = c => c[1] * 5 + c[0], top0 = r => clamp(r - (NR - 1) / 2, 0, 25 - NR);
function tableTop(now) {
  const lp = LAPS[now.k], pts = lp.tab, n = pts.length - 1;
  if (now.pre) return top0(rowOf(pts[0]));
  const s = now.u - LEAD, i = s <= 0 ? 0 : Math.min(n, Math.floor(s / STEP));
  const r = i >= n ? rowOf(pts[n]) : lerp(rowOf(pts[i]), rowOf(pts[i + 1]), s <= 0 ? 0 : easeInOut(clamp((s - i * STEP) / GLIDE)));
  if (now.u < FIN && (now.k > 0 || t - L0 >= CYCLE)) return lerp(top0(24), top0(r), easeInOut(now.u / FIN));
  return top0(r);
}
const NX = [752, 810, 868, 918], NY = { in: [262, 328], hid: Array.from({ length: 12 }, (_, i) => 92 + i * 36), out: [220, 272, 324, 376] };
function glyph(k, x, y, o = {}) { const d = MOVE[k], L = o.L || 7; arrow(x - d[0] * L, y + d[1] * L, x + d[0] * L, y - d[1] * L, { width: 1.4, head: 7, ...o }); }
function draw() {
  const now = lapNow(), lp = LAPS[now.k];
  const fadeLap = now.pre ? 0 : clamp(now.u / FIN) * (1 - clamp((now.u - (LAPT[now.k] - FOUT)) / FOUT));
  sub('a', 18, 36, 'tabular policy', seg(.1, .3));
  sub('b', 516, 36, 'neural network policy', seg(.15, .3));
  // ================= (a) the grid and the table
  const cs = GA.s / 5, ga = seg(.05, .4);
  const tw = walk(lp.tab.map(c => [c[0] + .5, c[1] + .5]), now.u), cell = lp.tab[Math.min(tw.i, lp.tab.length - 1)];
  const srow = now.pre ? -1 : cell[1] * 5 + cell[0];
  for (let s = 0; s < 25; s++) {
    const x = s % 5, y = (s / 5) | 0, X = GA.x + x * cs, Y = GA.y + (4 - y) * cs;
    if (s === 24) { box(X, Y, cs, cs, { fill: C.accent, stroke: null, alpha: ga }); continue; }
    glyph(ACT[s], X + cs / 2, Y + cs / 2, { color: C.sky, alpha: ga, L: 8 });
  }
  for (let i = 1; i < 5; i++) { line([[GA.x + i * cs, GA.y], [GA.x + i * cs, GA.y + GA.s]], { color: C.rule, width: 1, alpha: ga });
    line([[GA.x, GA.y + i * cs], [GA.x + GA.s, GA.y + i * cs]], { color: C.rule, width: 1, alpha: ga }); }
  box(GA.x, GA.y, GA.s, GA.s, { width: 1.4, progress: ga });
  if (!now.pre) dot(GA.x + tw.p[0] * cs, GA.y + (5 - tw.p[1]) * cs, 7, { color: '#fff', fill: C.navy, width: 2, alpha: fadeLap });
  // the table: booktabs rules, one row per state, one column per action; NR rows of the 25 show,
  // the window following the agent's row (a row half out of it is not drawn)
  const ta = seg(.12, .4), x1 = TX + TW.reduce((a, b) => a + b, 0), r0 = tableTop(now), yb = TY + 4 + NR * RH;
  line([[TX, TY - 18], [x1, TY - 18]], { width: 1.3, progress: ta });
  line([[TX, TY + 2], [x1, TY + 2]], { width: .8, progress: ta });
  line([[TX, yb + 3], [x1, yb + 3]], { width: 1.3, progress: ta });
  math('s', TX + TW[0] / 2, TY - 3, { size: 16, align: 'center', alpha: ta });
  for (let k = 0; k < 4; k++) glyph(k, TX + TW[0] + TW[1] * (k + .5), TY - 8, { alpha: ta, L: 6 });
  ctx.save(); ctx.beginPath(); ctx.rect(TX, TY + 4, x1 - TX, NR * RH); ctx.clip();
  for (let s = Math.floor(r0); s <= Math.min(24, Math.floor(r0) + NR); s++) {
    // a row whole in the window is drawn whole; leaving it, the row fades, gone before its ink meets
    // the rules above (it is .35 of a row out) and below (.22 out)
    const yr = TY + 4 + (s - r0) * RH, y = yr + .74 * RH, vis = clamp(Math.min((s - r0 + .35) / .2, (NR - .78 - (s - r0)) / .2));
    const ra = seg(.2 + (s - r0) * .02, .3) * vis;
    if (ra <= 0) continue;
    if (s === srow) { ctx.save(); ctx.globalAlpha = fadeLap * vis; ctx.fillStyle = C.steel; ctx.fillRect(TX, yr, x1 - TX, RH); ctx.restore(); }
    math(`(${s % 5},\\,${(s / 5) | 0})`, TX + TW[0] / 2, y, { size: 16, align: 'center', alpha: ra, color: C.body });
    const best = ACT[s], tie = tieWith(s);
    for (let k = 0; k < 4; k++) {
      const cx = TX + TW[0] + TW[1] * (k + .5), top = s !== 24 && (k === best || k === tie);
      text(nf(Qt[s][k], 2), cx, y, { size: 16, align: 'center', alpha: ra, color: top ? C.ink : s === srow ? C.body : C.muted });
      if (s === srow && s !== 24 && k === best) box(cx - 21, yr + 2, 42, RH - 4, { stroke: C.navy, width: 1.8, alpha: fadeLap * vis });
    }
  }
  ctx.restore();
  lab(`${NR} of its 25 rows`, TX, yb + 27, .6, { size: 16, color: C.body });
  // readout: the largest value, and the action it picks (two equal values: a tie, the walk's choice)
  if (srow >= 0) {
    mlab(`\\rm{state}\\ \\ s = (${cell[0]},\\,${cell[1]})`, GA.x, 306, .5, { size: 16, alpha: fadeLap });
    if (srow !== 24) { const b = ACT[srow], o = tieWith(srow);
      text(`largest value ${nf(Qt[srow][b], 2)}`, GA.x, 330, { size: 16, color: C.body, alpha: fadeLap });
      text(o < 0 ? `takes ${WORD[b]}` : `takes ${WORD[b]} (a tie with ${WORD[o]})`, GA.x, 352, { size: 16, color: C.body, alpha: fadeLap }); }
    else text('goal reached', GA.x, 330, { size: 16, color: C.accent, alpha: fadeLap });
  }
  lab('100 stored numbers,', GA.x, 392, .6, { size: 16, color: C.body });
  lab('25 states × 4 actions', GA.x, 413, .6, { size: 16, color: C.body });
  // ================= (b) the plane and the network
  const pc = PB.s / 5, pa = seg(.08, .4), P = v => [PB.x + v[0] * pc, PB.y + (5 - v[1]) * pc];
  box(PB.x + 4 * pc, PB.y, pc, pc, { fill: C.accent, stroke: null, alpha: pa });
  // the network's action everywhere in the plane: its largest output on a fine lattice
  for (let i = 0; i < 10; i++) for (let j = 0; j < 10; j++) {
    const v = [(i + .5) / 2, (j + .5) / 2]; if (v[0] >= 4 && v[1] >= 4) continue;
    const [X, Y] = P(v); glyph(argmax(FIELD[i * 10 + j]), X, Y, { color: C.sky, alpha: pa, L: 5, head: 6, width: 1.2 });
  }
  box(PB.x, PB.y, PB.s, PB.s, { width: 1.4, progress: pa });
  for (let i = 0; i <= 5; i++) {
    line([[PB.x + i * pc, PB.y + PB.s], [PB.x + i * pc, PB.y + PB.s - 4]], { width: 1, alpha: pa });
    line([[PB.x, PB.y + PB.s - i * pc], [PB.x + 4, PB.y + PB.s - i * pc]], { width: 1, alpha: pa });
    text(String(i), PB.x + i * pc, PB.y + PB.s + 18, { size: 16, align: 'center', alpha: pa });
    text(String(i), PB.x - 7, PB.y + PB.s - i * pc + 6, { size: 16, align: 'right', alpha: pa });
  }
  mlab('x', PB.x + PB.s / 2, PB.y + PB.s + 42, .4, { size: 17, align: 'center' });
  mlab('y', PB.x - 26, PB.y + PB.s / 2 + 5, .4, { size: 17, align: 'right' });
  const nw = walk(lp.net, now.u);
  let pos = now.pre ? lp.net[0] : nw.p;
  if (!now.pre && now.u < FIN && (now.k > 0 || t - L0 >= CYCLE)) {   // a new lap: from the last lap's goal, gliding
    const pl = LAPS[(now.k + LAPS.length - 1) % LAPS.length].net, pe = pl[pl.length - 1], e = easeInOut(now.u / FIN);
    pos = [lerp(pe[0], pos[0], e), lerp(pe[1], pos[1], e)];
  }
  const A = forward(pos), qo = A[3];
  const atGoal = nw.i >= lp.net.length - 1, best = atGoal ? -1 : argmax(qo);
  if (!now.pre) { const [X, Y] = P(pos); dot(X, Y, 7, { color: '#fff', fill: C.navy, width: 2, alpha: fadeLap }); }
  // edges: how much each connection carries for this state, |w a|, in blue (+) or grey (-)
  const layers = [NY.in, NY.hid, NY.hid, NY.out], ea = seg(.2, .5);
  for (let l = 0; l < 3; l++) {
    const [w] = NW[l], a = A[l]; let m = 1e-9;
    for (let i = 0; i < w.length; i++) for (let j = 0; j < a.length; j++) m = Math.max(m, Math.abs(w[i][j] * a[j]));
    for (let i = 0; i < w.length; i++) for (let j = 0; j < a.length; j++) {
      const c = w[i][j] * a[j], al = ea * (.06 + .7 * Math.abs(c) / m);
      line([[NX[l] + 8, layers[l][j]], [NX[l + 1] - 8, layers[l + 1][i]]], { color: c >= 0 ? S_POS : C.guide, width: 1.1, alpha: al });
    }
  }
  // neurons: inputs and hidden units coloured by their value, positive blue, negative crimson
  for (let l = 0; l < 4; l++) layers[l].forEach((y, i) => {
    const na = seg(.1 + .05 * l, .3), v = l < 3 ? A[l][i] : null;
    const isBest = l === 3 && i === best && !now.pre;
    dot(NX[l], y, 8, { color: isBest ? C.navy : C.ink, fill: v === null ? '#fff' : signed(v), width: isBest ? 2.6 : 1.2, alpha: na });
  });
  mlab('x', NX[0] - 14, NY.in[0] + 5, .4, { size: 16, align: 'right' });
  mlab('y', NX[0] - 14, NY.in[1] + 5, .4, { size: 16, align: 'right' });
  for (let k = 0; k < 4; k++) {
    const y = NY.out[k], on = k === best && !now.pre;
    glyph(k, NX[3] + 22, y, { alpha: seg(.4, .3), color: on ? C.navy : C.ink });
    text(nf(qo[k], 2), NX[3] + 36, y + 6, { size: 16, color: on ? C.ink : C.body, alpha: seg(.4, .3) });
  }
  cbar(NX[0] + 20, 518, 110, 8, SIGNED, -1, 1, [-1, 0, 1], '\\rm{activation}', seg(.6, .4), v => v === 0 ? '0' : nf(v, 0));
  if (!now.pre) {
    mlab(`(x,\\,y) = (${nf(pos[0], 2)},\\,${nf(pos[1], 2)})`, PB.x, 306, .5, { size: 16, alpha: fadeLap });
    if (atGoal) text('goal reached', PB.x, 330, { size: 16, color: C.accent, alpha: fadeLap });
    else {     // two outputs equal to two decimals: three decimals, and the runner up named
      const o2 = argmax(qo.map((v, k) => k === best ? -Infinity : v)), close = nf(qo[best], 2) === nf(qo[o2], 2);
      text(`largest output ${nf(qo[best], close ? 3 : 2)}`, PB.x, 330, { size: 16, color: C.body, alpha: fadeLap });
      text(close ? `takes ${WORD[best]} (${WORD[o2]} ${nf(qo[o2], 3)})` : `takes ${WORD[best]}`, PB.x, 352, { size: 16, color: C.body, alpha: fadeLap });
    }
  }
  lab(`${DATA.npar} learned parameters,`, PB.x, 392, .6, { size: 16, color: C.body });
  mlab('\\rm{for any real}\\ (x,\\,y)', PB.x, 413, .6, { size: 16, color: C.body });
}
const FIELD = []; for (let i = 0; i < 10; i++) for (let j = 0; j < 10; j++) FIELD.push(forward([(i + .5) / 2, (j + .5) / 2])[3]);
boot();
""")

TITLE = "Figure 29: What sits inside a reinforcement learning agent"
ARIA = ("Left: the grid world and its Q-table, one row per state and one column per action; the agent "
        "looks up the row of the square it is in and takes the largest value. Right: the same world "
        "with the position measured as two real numbers; a small neural network takes x and y in "
        "and puts out the value of each action, and its connections light up differently as the "
        "agent moves.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 560, DATA, JS, L))
