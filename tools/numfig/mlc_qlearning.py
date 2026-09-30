"""Figure 30 of the machine learning guide (image27): tabular Q-learning on a
5 x 5 grid world, the value of every square after 1, 10 and 300 episodes.

Model: mlc_grid.py, the grid world the text describes (+1 for reaching the
goal, -0.02 for every other step), Q-learning with alpha = 0.5, gamma = 0.95
and epsilon falling from 0.5 to 0.2, seed 21. The page receives the run's
whole transcript (every state and action, 3803 steps) and replays the Q
update on it, so what each panel shows at any moment is the table as the run
left it at that step, exactly.

Run: python tools/numfig/mlc_qlearning.py
"""
import numpy as np

import common
import mlc_grid as g
import mlc_lib as lib

NAME = "mlc-qlearning"

snaps, log = g.run()
ends = [0]
for k, rec in enumerate(log):
    if rec[5]:
        ends.append(k + 1)
lens = np.diff(ends)
V1, V10, V300 = (snaps[i].max(1) for i in (0, 9, 299))
Vs = g.v_star()
GOAL_S = g.sid(*g.GOAL)
mask = np.arange(25) != GOAL_S


def grid_txt(V, Q=None):
    out = []
    for y in range(4, -1, -1):
        row = []
        for x in range(5):
            s = g.sid(x, y)
            if s == GOAL_S:
                row.append("  goal ")
                continue
            arr = " ^v<>"[1 + int(np.argmax(Q[s]))] if (Q is not None and V[s] > 0) else " "
            row.append(f"{V[s]:6.3f}{arr}")
        out.append("    " + " ".join(row))
    return out


# ------------------------------------------------------------------ validation
L = []
say = L.append
say("nf-mlc-qlearning: Figure 30, tabular Q-learning on a 5 x 5 grid world")
say("")
say("MODEL")
say("  5 x 5 grid, start (0, 0) bottom left, goal (4, 4) top right; actions up, down,")
say("  left, right; a move into the wall stays put. Reward +1 on reaching the goal")
say("  (episode ends), -0.02 for every other step (the text's own numbers).")
say("  Q-learning, Q = 0 at first: Q(s,a) += alpha [r + gamma max Q(s',.) - Q(s,a)],")
say(f"  alpha = {g.ALPHA}, gamma = {g.GAMMA}; epsilon-greedy with epsilon falling linearly from")
say("  0.5 (episode 1) to 0.2 (episode 300); ties broken at random; numpy seed 21.")
say(f"  300 episodes, {len(log)} steps; episode lengths 1..10: {list(map(int, lens[:10]))};")
say(f"  last 10: {list(map(int, lens[-10:]))} (8 is the shortest route).")
say("  The page replays the transcript (state, action per step) with the same update in")
say("  double precision; the replay is checked against this run below.")
say("")
say("WHAT THE CAPTION SAYS, CHECKED ON THE RUN")
say("  value V(s) = max_a Q(s, a); a square 'has value' when V(s) > 0.")
pos1 = [g.xy(s) for s in range(25) if V1[s] > 0]
say(f"  after 1 episode, squares with value: {pos1} (the square beside the goal),")
say(f"    V = {V1[g.sid(4, 3)]:.3f} = alpha x 1; every other square 0 or below.")
say("  after 10 episodes:")
L.extend(grid_txt(V10, snaps[9]))
pos10 = [g.xy(s) for s in range(25) if V10[s] > 0]
say(f"    {len(pos10)} squares with value, along the route the agent took; the rest")
say("    of what it visited has only paid the step cost (negative).")
say("  after 300 episodes:")
L.extend(grid_txt(V300, snaps[299]))
bad = g.policy_is_shortest(snaps[299])
say(f"    squares with value: {int(np.sum(V300[mask] > 0))} of 24; squares whose arrow does not lead one")
say(f"    square closer to the goal: {len(bad)} {bad if bad else ''}")
say("")
say("CHECK 1: learned values against the exact optimal values")
say("  closed form V*(d) = gamma^(d-1) - 0.02 (1 - gamma^(d-1)) / (1 - gamma), d the")
say("  Manhattan distance to the goal; value iteration agrees to")
cf = max(abs(Vs[g.sid(x, y)] - g.closed_form_v(x, y)) for x in range(5) for y in range(5))
say(f"  {cf:.1e}.")
err = np.abs(V300 - Vs)[mask]
worst = int(np.flatnonzero(mask)[np.argmax(err)])
say(f"  after 300 episodes: max |V - V*| = {err.max():.4f} at {g.xy(worst)} (V = {V300[worst]:.4f},")
say(f"  V* = {Vs[worst]:.4f}); mean |V - V*| = {err.mean():.4f}; {int(np.sum(err < 1e-3))} of 24 squares within 0.001.")
say(f"  start square: V = {V300[0]:.4f}, V* = {Vs[0]:.4f} (8 steps: 0.95^7 - 0.4 (1 - 0.95^7))")
say("")
say("CHECK 2: the first positive value is alpha times the goal reward")
first = next(r for r in log if r[3] > 0)
say(f"  first rewarding step: episode {first[0] + 1}, from {g.xy(first[1])} {g.ACTIONS[first[2]]}:"
    f" Q {first[6]:.3f} -> {first[7]:.3f} (= 0 + 0.5 (1 - 0))")
say("")
say("CHECK 3: the greedy policy after 300 episodes walks start -> goal in 8 steps")
s, path = g.sid(*g.START), [g.START]
for _ in range(20):
    s, _, done = g.step(s, int(np.argmax(snaps[299][s])))
    path.append(g.xy(s))
    if done:
        break
say(f"  route: {path} ({len(path) - 1} steps; the shortest is 8)")

# ------------------------------------------------------------------ timing
# Round 3 (30 Sep 2026), the client: "slow down Figures 28, 29, 30", the motion
# was too fast to follow. Every panel learns half as fast as in the first
# version, and the learned policy walks half as fast.
T0, DUR = .75, (3.8, 5.0, 6.2)       # learning starts; (a) 1, (b) 10, (c) 300 episodes take DUR s
UPD, AREST, AFADE = .45, .7, .8      # (a): its rewarding update eases in; its agent rests, then fades
WAIT = .7                            # (c) learned, until its first greedy walk
LEAD, STEP, REST, FOUT, GAP = .4, .56, 1.8, .6, 1.0   # a greedy walk: fade in, a step, at the goal, fade, gap
nroute = len(path) - 1
lap = LEAD + nroute * STEP + REST + FOUT + GAP
say("")
say("TIMING (Round 3, 30 Sep 2026: the client asked for the figure slowed down; about 2 x)")
say(f"  learning starts at {T0} s (was 0.55; the agent of (a) appears in the 0.3 s before it).")
say(f"  (a) walks its episode's {lens[0]} steps in {DUR[0]} s, {DUR[0] / lens[0]:.2f} s a step (was 1.9 s, 0.16 s); the value")
say(f"  its rewarding step earns eases in over {UPD} s (was 0.07); its agent rests at the goal {AREST} s")
say(f"  (was 0.35), then fades out in {AFADE} s (was 0.4). (b) plays its 10 episodes in {DUR[1]} s (was 2.5), (c)")
say(f"  its 300 in {DUR[2]} s (was 3.1): the three finish {DUR[1] - DUR[0]:.1f} s apart (was 0.6).")
say(f"  {WAIT} s after (c) has learned (was 0.35), its greedy policy walks from the start, again and")
say(f"  again: {STEP} s a step (was 0.28), at the goal {REST} s (was 0.9), fading in {LEAD} s and out {FOUT} s")
say(f"  (was 0.2 and 0.3), {GAP} s between walks (was 0.5): every {lap:.2f} s (was 4.14 s).")
say(f"  Poster (reduced motion, print): {T0 + DUR[2] + WAIT + lap - GAP / 2:.2f} s (was 7.89), between two walks: the tables")
say("  alone, the same frame as before.")

# ------------------------------------------------------------------ data
code = np.array([rec[1] * 4 + rec[2] for rec in log])
DATA = {"tr": common.i8(code), "n": len(log), "v300": [float(v) for v in V300]}

JS = (f"const T0 = {T0}, DUR = {list(DUR)}, UPD = {UPD}, AREST = {AREST}, AFADE = {AFADE}, WAIT = {WAIT}, "
      f"LEAD = {LEAD}, STEP = {STEP}, REST = {REST}, FOUT = {FOUT}, GAP = {GAP};"
      + r"""
const S = 56, GX = [30, 360, 690], GY = 78;
const TR = b64i8(DATA.tr), NS = DATA.n;
const MOVE = [[0, 1], [0, -1], [-1, 0], [1, 0]];
/* the run, replayed: Q after every step, from the transcript (mlc_grid.py) */
const VS = new Float32Array((NS + 1) * 25), AM = new Int8Array((NS + 1) * 25), POS = new Uint8Array(NS + 1), ACT = new Int8Array(NS + 1), ENDS = [0];
(() => {
  const Q = new Float64Array(100); let s = 0;
  const snap = k => { for (let c = 0; c < 25; c++) { let m = Q[c * 4], am = 0;
    for (let a = 1; a < 4; a++) if (Q[c * 4 + a] > m) { m = Q[c * 4 + a]; am = a; }
    VS[k * 25 + c] = m; AM[k * 25 + c] = am; } };
  snap(0);
  for (let k = 0; k < NS; k++) {
    const s0 = TR[k] >> 2, a = TR[k] & 3;
    if (s0 !== s) throw new Error('replay out of step at ' + k);
    const x = s % 5, y = (s / 5) | 0;
    const nx = Math.min(4, Math.max(0, x + MOVE[a][0])), ny = Math.min(4, Math.max(0, y + MOVE[a][1])), s2 = ny * 5 + nx;
    const done = s2 === 24, r = done ? 1 : -0.02;
    let mx = Q[s2 * 4]; for (let b = 1; b < 4; b++) mx = Math.max(mx, Q[s2 * 4 + b]);
    const target = r + (done ? 0 : 0.95 * mx), before = Q[s * 4 + a];
    Q[s * 4 + a] = before + 0.5 * (target - before);
    ACT[k] = a; POS[k + 1] = s2; s = done ? 0 : s2;
    snap(k + 1);
    if (done) ENDS.push(k + 1);
  }
  for (let c = 0; c < 25; c++) if (Math.abs(VS[NS * 25 + c] - DATA.v300[c]) > 1e-4) throw new Error('replay differs at square ' + c);
})();
/* the greedy route after 300 episodes, from the start */
const ROUTE = [0];
for (let i = 0, s = 0; i < 24 && s !== 24; i++) { const a = AM[NS * 25 + s], x = s % 5, y = (s / 5) | 0;
  s = Math.min(4, Math.max(0, y + MOVE[a][1])) * 5 + Math.min(4, Math.max(0, x + MOVE[a][0])); ROUTE.push(s); }

const EPIS = [1, 10, 300];
const TL = T0 + DUR[2] + WAIT, LAP = LEAD + (ROUTE.length - 1) * STEP + REST + FOUT + GAP;
const POSTER_T = TL + LAP - GAP / 2;      // between two walks: the table alone, complete
const ASTEP = DUR[0] / ENDS[1];           // (a): one step of its episode

const cx = (p, s) => GX[p] + (s % 5 + .5) * S, cy = s => GY + (4 - ((s / 5) | 0) + .5) * S;
/* continuous episodes done -> step index */
function kAt(c) { const e = Math.min(Math.floor(c), ENDS.length - 2), f = c - e; return ENDS[e] + f * (ENDS[e + 1] - ENDS[e]); }
function clockC(p) {                       // episodes done in panel p at time t
  const u = clamp((t - T0) / DUR[p]);
  if (p === 2) return u <= 0 ? 0 : Math.pow(EPIS[2] + 1, easeOut(u) * .15 + u * .85) - 1;
  return EPIS[p] * (p === 0 ? u : easeInOut(u) * .25 + u * .75);
}
/* the value panel p shows for square s at replay step j + f: (a) eases each update in
   as its agent arrives, the one its rewarding step earns over UPD seconds */
function cellV(p, s, j, f) {
  const V = VS[j * 25 + s];
  if (p !== 0 || j >= NS) return V;
  if (j >= ENDS[1] - 1) { const i = ENDS[1] - 1;
    return lerp(VS[i * 25 + s], VS[(i + 1) * 25 + s], easeInOut(clamp((t - T0 - (i + .55) * ASTEP) / UPD))); }
  return lerp(V, VS[(j + 1) * 25 + s], easeInOut(clamp((f - .55) / .45)));
}
/* the parts of a route in (a) over squares with no fill (value 0 or below, not the goal):
   a filled square hides what is under it, so nothing is drawn there */
function openRoute(trail, j, f) {
  const out = []; let run = null;
  const open = (x, y) => { const s = (4 - Math.floor((y - GY) / S)) * 5 + Math.floor((x - GX[0]) / S);
    return s !== 24 && !(cellV(0, s, j, f) > 0); };
  for (let i = 1; i < trail.length; i++) {
    const p = trail[i - 1], q = trail[i], cut = [0, 1];
    for (const d of [0, 1]) {                 // where the move crosses a square's edge
      const o = d ? GY : GX[0], a = (p[d] - o) / S, b = (q[d] - o) / S;
      if (a !== b) for (let k = Math.ceil(Math.min(a, b)); k <= Math.floor(Math.max(a, b)); k++) cut.push((k - a) / (b - a));
    }
    cut.sort((u, v) => u - v);
    for (let c = 1; c < cut.length; c++) {
      if (cut[c] - cut[c - 1] < 1e-9) continue;
      const A = [lerp(p[0], q[0], cut[c - 1]), lerp(p[1], q[1], cut[c - 1])], B = [lerp(p[0], q[0], cut[c]), lerp(p[1], q[1], cut[c])];
      if (open((A[0] + B[0]) / 2, (A[1] + B[1]) / 2)) { if (!run) out.push(run = [A]); run.push(B); } else run = null;
    }
  }
  return out;
}
function cellArrow(x, y, a, col, alpha) {
  const L = 12, dx = MOVE[a][0], dy = -MOVE[a][1];
  arrow(x - dx * L, y - dy * L, x + dx * L, y + dy * L, { color: col, width: 1.8, head: 9, alpha });
}
function drawGrid(p) {
  const x0 = GX[p], pa = seg(.04 + .06 * p, .4);
  const c = clockC(p), done = Math.floor(c + 1e-9), k = kAt(c), j = Math.floor(k), f = k - j;
  const va = seg(T0 - .05, .3);
  for (let s = 0; s < 25; s++) {
    const X = x0 + (s % 5) * S, Y = GY + (4 - ((s / 5) | 0)) * S;
    if (s === 24) { box(X, Y, S, S, { fill: C.accent, stroke: null, progress: seg(.2 + .06 * p, .3) }); continue; }
    const V = cellV(p, s, j, f), a = AM[j * 25 + s];
    if (V > 0) box(X, Y, S, S, { fill: lutc(SEQ, V), stroke: null, alpha: va });
    const dark = V > 0 && lutDark(SEQ, V), col = dark ? '#fff' : C.ink;
    if (V > 0) cellArrow(X + S / 2, Y + S * .4, a, col, va);
    if (Math.abs(V) >= .005) text(nf(V, 2), X + S / 2, Y + S - 8, { size: 14, align: 'center', color: V < 0 ? C.muted : col, alpha: va });
  }
  // the lattice over the fills
  ctx.save(); ctx.globalAlpha = pa;
  for (let i = 1; i < 5; i++) { line([[x0 + i * S, GY], [x0 + i * S, GY + 5 * S]], { color: C.rule, width: 1 });
    line([[x0, GY + i * S], [x0 + 5 * S, GY + i * S]], { color: C.rule, width: 1 }); }
  ctx.restore();
  box(x0, GY, 5 * S, 5 * S, { width: 1.4, progress: pa });
  const n = Math.min(done, EPIS[p]);
  sub('abc'[p], x0 - 2, 44, `after ${n} episode${n === 1 ? '' : 's'}`, seg(.1 + .05 * p, .3));
  lab('start', x0 + S / 2, GY + 5 * S + 20, .35 + .05 * p, { size: 14, color: C.muted, align: 'center' });
  // named above its square, as 'start' is below its own: the agent comes to rest inside it
  lab('goal', x0 + 4.5 * S, GY - 10, .35 + .05 * p, { size: 14, color: C.muted, align: 'center' });
}
/* (a): the agent walking its first episode; its route stays, faint, under the fills */
function drawWalker(route) {
  const c = clockC(0); if (t < T0 - .3) return;
  const k = kAt(c), j = Math.min(Math.floor(k), ENDS[1]), f = j >= ENDS[1] ? 0 : k - j;
  const trail = [];
  for (let i = 0; i <= j; i++) trail.push([cx(0, POS[i]), cy(POS[i])]);
  const e = easeInOut(f); let ax = cx(0, POS[j]), ay = cy(POS[j]);
  if (j < ENDS[1]) {
    const nx = cx(0, POS[j + 1]), ny = cy(POS[j + 1]);
    if (POS[j + 1] === POS[j]) { const b = Math.sin(Math.PI * e) * 10; ax += MOVE[ACT[j]][0] * b; ay -= MOVE[ACT[j]][1] * b; }
    else { ax = lerp(ax, nx, e); ay = lerp(ay, ny, e); trail.push([ax, ay]); }
  }
  const fade = 1 - seg(T0 + DUR[0] + AREST, AFADE);
  if (route) { for (const r of openRoute(trail, j, f)) line(r, { color: C.sky, width: 2, alpha: .75 - .35 * (1 - fade) }); return; }
  if (fade > 0) dot(ax, ay, 7.5, { color: '#fff', fill: C.navy, width: 2, alpha: seg(T0 - .3, .3) * fade });
}
/* (c): the learned policy walking from the start, over and over */
function drawGreedy() {
  if (t < TL) return;
  const u = (t - TL) % LAP, fin = clamp((u - LEAD - (ROUTE.length - 1) * STEP - REST) / FOUT);
  const alpha = clamp(u / LEAD) * (1 - fin);
  const k = clamp((u - LEAD) / STEP, 0, ROUTE.length - 1), j = Math.min(Math.floor(k), ROUTE.length - 2), f = easeInOut(k - j);
  const last = k >= ROUTE.length - 1;
  const ax = lerp(cx(2, ROUTE[j]), cx(2, ROUTE[j + 1]), last ? 1 : f), ay = lerp(cy(ROUTE[j]), cy(ROUTE[j + 1]), last ? 1 : f);
  if (alpha > 0) dot(ax, ay, 7.5, { color: '#fff', fill: C.navy, width: 2, alpha });
}
function draw() {
  drawWalker(true);
  for (let p = 0; p < 3; p++) drawGrid(p);
  drawWalker(false); drawGreedy();
  const fa = seg(.6, .5);
  cbar(560, H - 42, 150, 10, SEQ, 0, 1, [0, .5, 1], '\\rm{value}\\ \\ \\rm{max}_{a}\\,Q(s,a)', fa, v => nf(v, 1));
  text('reward +1 at the goal, −0.02 per step;  α = 0.5,  γ = 0.95,  ε from 0.5 to 0.2', 28, H - 16, { size: 14, color: C.muted, alpha: fa });
}
boot();
""")

TITLE = "Figure 30: Tabular Q-learning on a 5x5 grid world, where the only reward is reaching the goal"
ARIA = ("Three copies of a five by five grid world with the goal in the top right corner, showing "
        "the value the agent has learned for every square and the direction it would move. After "
        "one episode only the square beside the goal has value; after ten, value has spread back "
        "along the route it took; after three hundred, every square has value and the arrows lead "
        "to the goal.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 436, DATA, JS, L))
