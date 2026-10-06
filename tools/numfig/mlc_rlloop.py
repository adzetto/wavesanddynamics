"""Figure 28 of the machine learning guide (image25): the reinforcement learning
loop, run for real.

The loop turns once per step of a real episode: the first episode of the run
Figure 30 shows (mlc_grid.py: the 5 x 5 grid world, +1 at the goal, -0.02 a
step, Q-learning, epsilon = 0.5 in that episode), its last three steps, the walk
before them drawn as the path so far. Each turn shows the state the
agent observes, the action it takes, the reward and new state the environment
returns, and the policy update: the agent's probabilities of choosing each
action in that state, before and after, exactly as its epsilon-greedy policy
gives them from its values.

Run: python tools/numfig/mlc_rlloop.py
"""
import numpy as np

import mlc_grid as g
import mlc_lib as lib

NAME = "mlc-rlloop"

snaps, log = g.run()
ep1 = [r for r in log if r[0] == 0]
EPS1 = g.eps_decay(0)

Q = np.zeros((25, 4))
steps, L = [], []
say = L.append
say("nf-mlc-rlloop: Figure 28, the reinforcement learning loop")
say("")
say("MODEL")
say("  The grid world and run of Figure 30 (mlc_grid.py, seed 21): the loop turns once per")
say(f"  step of the run's first episode ({len(ep1)} steps), epsilon = {EPS1} in that episode; the page")
say("  plays its last three steps (t = 9, 10, 11 below), the walk before them drawn as the path so far.")
say("  Policy shown: the epsilon-greedy behaviour policy the run used,")
say("    pi(a|s) = eps/4 + (1 - eps) [a among the actions of largest Q(s, .)] / (number of them)")
say("  before and after each update of Q(s, a).")
say("")
say("  t  state   action  reward  new state   pi(up, down, left, right) before -> after")
for i, (ep, s, a, r, s2, done, qb, qa) in enumerate(ep1):
    pb = g.pi_eps_greedy(Q[s], EPS1)
    Q[s, a] = qa
    pa = g.pi_eps_greedy(Q[s], EPS1)
    steps.append({"s": list(g.xy(s)), "a": a, "r": r, "s2": list(g.xy(s2)), "done": bool(done),
                  "pb": pb.tolist(), "pa": pa.tolist(), "qb": qb, "qa": qa})
    say(f"  {i:2d} {str(g.xy(s)):7s} {g.ACTIONS[a]:6s} {r:+.2f}   {str(g.xy(s2)):9s}"
        f"   {np.round(pb, 3)} -> {np.round(pa, 3)}")
say("")
say("CHECKS")
say(f"  probabilities sum to 1 in every row: max |sum - 1| = "
    f"{max(abs(sum(st['pb']) - 1) + abs(sum(st['pa']) - 1) for st in steps):.1e}")
last = steps[-1]
say(f"  the rewarding step: Q(up at (4, 3)) {last['qb']:.3f} -> {last['qa']:.3f} = 0 + 0.5 (1 - 0);")
say(f"  pi(up | (4, 3)) {last['pb'][0]:.4f} -> {last['pa'][0]:.4f} = eps/4 + (1 - eps)"
    f" = {EPS1 / 4 + 1 - EPS1:.4f}: the agent becomes more likely to repeat the move that reached the goal.")
say("  every other step pays -0.02, so the action just tried drops to eps/4 = "
    f"{EPS1 / 4:.3f} while untried actions (Q = 0) share the rest.")
x = np.array(snaps[0])
same = np.max(np.abs(Q - x))
say(f"  table after the episode equals the run's own snapshot after episode 1: max |dQ| = {same:.1e}")

# ------------------------------------------------------------------ timing
# Round 3 (30 Sep 2026), the client: "slow down Figures 28, 29, 30", the motion
# was too fast to follow. Every part of a turn of the loop runs half as fast as
# the first version's, and a turn ends with a rest to read the updated policy.
L0 = .6                                      # the first turn starts (the intro is unchanged)
P, HOLD, SEAM = 4.8, 3.2, .6                 # one turn; the last turn held; fading back to the lap's start
A0, A1, M1, R1, U1 = .6, 1.7, 2.4, 3.5, 4.4  # in a turn: action out, agent moves, reward back, update
# The coordinator, the same day: at this pace the whole episode made a reader wait
# 55 s for the reward. A lap is the episode's last NT turns: the agent two squares
# from the goal, one ordinary step, a bump into the wall, then the goal. The last
# two turns are in the same square, so one policy is seen updated twice: the
# wall makes "right" less likely, the goal makes "up" much more likely.
NT = 3
FIRST = len(steps) - NT
t_goal = L0 + (NT - 1) * P                   # the rewarding turn starts
say("")
say("TIMING (Round 3, 30 Sep 2026: the client asked for the figure slowed down; about 2 x)")
say(f"  one turn of the loop {P} s (was 2.3 s). In it: what the previous turn left (its tags, its dark")
say("  bar) fades in 0.3 s (was 0.15) while the policy bars settle into the observed state on a 0.45 s")
say(f"  spring (was 0.25); the action travels {A1 - A0:.1f} s (was 0.55); the agent moves {M1 - A1:.1f} s (was 0.35); the")
say(f"  reward and new state travel back {R1 - M1:.1f} s (was 0.55); the update runs round its loop {U1 - R1:.1f} s (was 0.5)")
say("  while the bars move on a 0.55 s spring (was 0.35), their numbers final as the dot arrives;")
say(f"  then {P - U1:.1f} s of rest (was 0.05) to read the new policy.")
say(f"  A lap is the episode's last {NT} turns, t = {FIRST} to {len(steps) - 1} (the first version played all {len(steps)}, 29.2 s")
say(f"  a lap, the reward at 27 s; slowed, all {len(steps)} would put it at 56 s). From the moment the figure is in")
say(f"  view: t = {FIRST} from {L0} s (its action leaves at {L0 + A0:.1f} s), t = {FIRST + 1} from {L0 + P:.1f} s, t = {FIRST + 2} from {t_goal:.1f} s:")
say(f"  the agent reaches the goal at {t_goal + M1:.1f} s, the +1 reaches the agent at {t_goal + R1:.1f} s and its policy has")
say(f"  moved by {t_goal + U1:.1f} s. The frame is then held {HOLD} s (was 1.6); in its last {SEAM} s the walk, the agent and")
say(f"  the tags fade, and the lap opens again with them fading in at (4, 2) (was a cut). One lap {NT * P + HOLD:.1f} s.")
say("  The intro is unchanged (drawn by 1.1 s), the path so far arriving with the grid.")
say(f"  Poster (reduced motion, print): {L0 + NT * P + 1.2:.1f} s (was 28.8), the rewarding turn complete, 1.2 s into")
say("  the hold.")

DATA = {"steps": steps}

JS = (f"const L0 = {L0}, P = {P}, HOLD = {HOLD}, SEAM = {SEAM}, A0 = {A0}, A1 = {A1}, M1 = {M1}, R1 = {R1}, U1 = {U1}, NT = {NT};"
      + r"""
const ST = DATA.steps, NST = ST.length, FIRST = NST - NT, LOOP = NT * P + HOLD;   // a lap: the last NT turns
const POSTER_T = L0 + NT * P + 1.2;                   // after the last step: +1, the goal, the policy after
const AG = { x: 60, y: 36, w: 320, h: 250 }, EN = { x: 620, y: 36, w: 320, h: 250 };
const CS = 36, GX0 = EN.x + (EN.w - 5 * CS) / 2 + 10, GY0 = EN.y + 48;
const YA = 104, YR = 224;                             // the action arrow, the reward and state arrow
const MOVE = [[0, 1], [0, -1], [-1, 0], [1, 0]], WORD = ['up', 'down', 'left', 'right'];
const gx = p => GX0 + (p[0] + .5) * CS, gy = p => GY0 + (4 - p[1] + .5) * CS;
/* the turn i under way, u seconds into it; `out` fades the lap's walk as it ends */
function clockNow() {
  if (t < L0) return { i: FIRST, u: -1, lap: 0, out: 1 };
  const T = t - L0, lap = Math.floor(T / LOOP), r = T - lap * LOOP;
  const n = Math.min(NT - 1, Math.floor(r / P));
  return { i: FIRST + n, u: r - n * P, lap, out: 1 - clamp((r - (LOOP - SEAM)) / SEAM) };
}
const ph = (u, a, b) => clamp((u - a) / (b - a));
const WIN = [[A0, A1], [M1, R1], [R1, U1]];           // when the action, the reward, the update travel
/* the policy bars: four actions, their probabilities in the observed state;
   the action just chosen dark (hi), the previous turn's letting go (was, lo) */
function bars(pi, chosen, hi, a0, was = -1, lo = 0) {
  const base = AG.y + 212, Hm = 104, bw = 34;
  line([[AG.x + 44, base], [AG.x + AG.w - 24, base]], { width: 1.2, alpha: a0 });
  for (let k = 0; k < 4; k++) {
    const cx = AG.x + 82 + k * 64, h = Hm * pi[k];
    const on = Math.max(k === chosen ? hi : 0, k === was ? lo : 0);
    box(cx - bw / 2, base - h, bw, h, { fill: on > 0 ? mix('#A9C3DA', '#043052', on) : C.mist, stroke: C.blue, width: 1.2, alpha: a0 });
    text(nf(pi[k], 3), cx, base - h - 7, { size: 16, align: 'center', alpha: a0 });
    const d = MOVE[k], L = 9;
    arrow(cx - d[0] * L, base + 21 + d[1] * L, cx + d[0] * L, base + 21 - d[1] * L, { width: 1.5, head: 8, alpha: a0 });
  }
}
/* a small tag that travels along an arrow: a word or a number in a white box */
function tag(s, x, y, o = {}) {
  const { color = C.ink, alpha = 1, isMath = false } = o;
  if (alpha <= 0) return;
  ctx.save(); ctx.font = font({ size: 16 }); const w = (isMath ? math(s, 0, -1e4, { size: 16, alpha: 0 }) : ctx.measureText(s).width) + 14; ctx.restore();
  box(x - w / 2, y - 13, w, 26, { fill: '#fff', stroke: color, width: 1.2, alpha });
  if (isMath) math(s, x, y + 6, { size: 16, align: 'center', color, alpha }); else text(s, x, y + 6, { size: 16, align: 'center', color, alpha });
}
function draw() {
  const { i, u, lap, out } = clockNow(), st = ST[i], prev = i > FIRST ? ST[i - 1] : null;
  const live = u >= 0;
  // which part of the loop is working now: its label darkens from the body colour to ink
  const on = k => !live ? 0 : Math.sin(Math.PI * ph(u, WIN[k][0], WIN[k][1]));
  const ink = k => mix('#544F48', '#27221C', on(k));
  // ---- the two boxes, the two arrows, the update loop
  box(AG.x, AG.y, AG.w, AG.h, { fill: C.steel, width: 1.6, progress: seg(0, .42) });
  box(EN.x, EN.y, EN.w, EN.h, { fill: C.steel, width: 1.6, progress: seg(.06, .42) });
  lab('agent', AG.x + 18, AG.y + 30, .25, { size: 17 });
  lab('environment', EN.x + 18, EN.y + 30, .3, { size: 17 });
  carrow([[AG.x + AG.w, YA], [EN.x, YA]], { width: 1.6, progress: seg(.28, .35) });
  carrow([[EN.x, YR], [AG.x + AG.w, YR]], { width: 1.6, progress: seg(.34, .35) });
  mlab('\\rm{action}\\ \\ A_{t}', 500, YA - 22, .45, { size: 17, align: 'center', color: ink(0) });
  mlab('\\rm{reward}\\ \\ R_{t+1},\\ \\ \\rm{new\\ state}\\ \\ S_{t+1}', 500, YR + 44, .5, { size: 17, align: 'center', color: ink(1) });
  const loop = bez([AG.x + 120, AG.y + AG.h], [AG.x + 170, AG.y + AG.h + 96], [AG.x + 220, AG.y + AG.h]);
  carrow(loop, { width: 1.5, progress: seg(.4, .35) });
  lab('policy update', AG.x + 234, AG.y + AG.h + 42, .55, { size: 17, color: ink(2) });
  // ---- the step
  const a0 = seg(.35, .3);
  if (live) mlab(`t = ${i}`, 500, (YA + YR) / 2 + 6, L0, { size: 17, align: 'center' });
  // the policy in the observed state: settles in, then the update moves it
  let pi = st.pb;
  const before = prev || (lap > 0 ? ST[NST - 1] : null);   // the turn that came before, if any
  if (live) {
    const from = before ? before.pa : st.pb, s0 = settle(t - u, .45);
    pi = st.pb.map((v, k) => lerp(from[k], v, s0));
    const up = u >= R1 ? settle(t - u + R1, .55) : 0;   // its numbers final as the loop's dot arrives
    if (up > 0) pi = st.pb.map((v, k) => lerp(v, st.pa[k], up));
  }
  bars(pi, st.a, live ? clamp((u - A0) / .4) : 0, a0, before ? before.a : -1, live ? 1 - clamp(u / .3) : 0);
  const sOb = st.s;
  mlab(`\\pi(a\\,|\\,s),\\ \\ s = (${sOb[0]},\\,${sOb[1]})`, AG.x + 18, AG.y + 62, .4, { size: 16, color: C.body });
  // ---- the grid world, the agent walking its first episode
  const ga = seg(.2, .4);
  for (let y = 0; y < 5; y++) for (let x = 0; x < 5; x++) {
    const X = GX0 + x * CS, Y = GY0 + (4 - y) * CS;
    box(X, Y, CS, CS, { fill: x === 4 && y === 4 ? C.accent : '#fff', stroke: C.rule, width: 1, alpha: ga });
  }
  box(GX0, GY0, 5 * CS, 5 * CS, { width: 1.3, progress: ga });
  lab('goal', GX0 + 4.5 * CS, GY0 - 8, .45, { size: 16, color: C.accent, align: 'center' });
  lab('start', GX0 + .5 * CS, GY0 + 5 * CS + 17, .45, { size: 16, color: C.body, align: 'center' });
  const trail = [[gx(ST[0].s), gy(ST[0].s)]];
  for (let k = 0; k < i; k++) trail.push([gx(ST[k].s2), gy(ST[k].s2)]);
  let ax = gx(st.s), ay = gy(st.s);
  if (live) {
    const e = easeInOut(ph(u, A1, M1));
    if (st.s[0] === st.s2[0] && st.s[1] === st.s2[1]) { const b = Math.sin(Math.PI * e) * 9; ax += MOVE[st.a][0] * b; ay -= MOVE[st.a][1] * b; }
    else { ax = lerp(ax, gx(st.s2), e); ay = lerp(ay, gy(st.s2), e); if (e > 0) trail.push([ax, ay]); }
  }
  // a new lap: the agent and its path so far fade in again, as the lap before them faded
  const back0 = live && lap > 0 && i === FIRST ? clamp(u / .4) : 1;
  line(trail, { color: C.sky, width: 2, alpha: .7 * ga * out * back0 });
  dot(ax, ay, 7, { color: '#fff', fill: C.navy, width: 2, alpha: ga * out * back0 });
  // ---- what travels round the loop: the action out, the reward and the new state back
  if (live) {
    const x0 = AG.x + AG.w + 90, x1 = EN.x - 80;
    const go = ph(u, A0, A1);
    if (u >= A0) tag(WORD[st.a], lerp(x0, x1, easeInOut(go)), YA, { alpha: clamp(go * 5) * out });
    else if (prev) tag(WORD[prev.a], x1, YA, { alpha: 1 - clamp(u / .3) });
    const back = ph(u, M1, R1);
    const two = (s_, alpha, pos) => {
      const x = lerp(x1, x0, pos);
      tag(s_.r > 0 ? '+1' : nf(s_.r, 2), x + 36, YR, { alpha, color: s_.r > 0 ? C.accent : C.ink });
      tag(`(${s_.s2[0]},\\,${s_.s2[1]})`, x - 44, YR, { alpha, isMath: true });
    };
    if (u >= M1) two(st, clamp(back * 5) * out, easeInOut(back));
    else if (prev) two(prev, 1 - clamp(u / .3), 1);
    // the update: a dot running round the loop, along it between its points
    const upd = ph(u, R1, U1);
    if (upd > 0 && upd < 1) { const q = easeInOut(upd) * (loop.length - 1), k = Math.min(loop.length - 2, Math.floor(q)), f = q - k;
      dot(lerp(loop[k][0], loop[k + 1][0], f), lerp(loop[k][1], loop[k + 1][1], f), 4.5, { color: C.navy, fill: C.navy, alpha: Math.sin(Math.PI * upd) }); }
  }
  text('grid world of Figure 30: +1 at the goal, −0.02 a step; ε = 0.5',
       20, H - 12, { size: 15, color: C.muted, alpha: seg(.6, .5) });
}
boot();
""")

TITLE = "Figure 28: The reinforcement learning loop"
ARIA = ("An agent and an environment joined in a loop: the agent's action goes to the environment, "
        "which returns a reward and a new state, and the agent updates its policy. The loop runs "
        "through the last steps of the first episode in the grid world of Figure 30, one step at a "
        "time, until the agent reaches the goal and becomes more likely to repeat the move that got "
        "it there.")

if __name__ == "__main__":
    print("\n".join(L))
    print(lib.build(NAME, TITLE, ARIA, 372, DATA, JS, L))
