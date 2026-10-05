"""Figure 23: RNN and LSTM architecture. Top: an RNN carrying a hidden state
from one time step to the next. Bottom: inside one LSTM cell, the forget,
input and output gates that control what the memory cell keeps.

Task: a sensor stream, one reading per step (mostly small, now and then a
large one); at every step the network must give the largest reading so far,
so it has to remember the peak. Two networks are trained on it here with
PyTorch (Adam, 4000 steps of 128 random sequences of 12 readings): a simple
RNN with 3 tanh hidden units and an LSTM with a single memory cell, each with
a linear read out. Every number on the page is their own computation on the
six readings shown (reproduced in numpy from the trained weights).

The motion steps through time: the reading enters, the RNN cell updates its
hidden state and passes it on, and the LSTM cell below shows the same step:
how far each gate is open, the candidate, and the memory cell's value. At the
spike the input gate opens and the memory takes the new peak; afterwards the
forget gate stays near 1 and the input gate near 0, so the memory keeps it.
A time step takes 1.8 s (CLOCK, below; round 3 made it twice round 2's), so a
reader can follow each one.

Run: python tools/numfig/mlb_rnn.py [--look]
"""
import numpy as np
import torch

import mlb_common as mc

NAME = "rnn"
T, ITERS, BATCH = 12, 4000, 128
SEQ = np.array([0.10, 0.25, 0.85, 0.20, 0.05, 0.30])
torch.set_default_dtype(torch.float64)


def batch(n, g):
    x = g.uniform(0, 1, (n, T)) ** 2 * 0.8
    x = np.where(g.uniform(size=(n, T)) < 0.12, g.uniform(0.5, 1.0, (n, T)), x)
    return torch.tensor(x[..., None]), torch.tensor(np.maximum.accumulate(x, axis=1)[..., None])


class Net(torch.nn.Module):
    def __init__(self, kind, H):
        super().__init__()
        self.r = torch.nn.RNN(1, H, batch_first=True) if kind == "rnn" else torch.nn.LSTM(1, H, batch_first=True)
        self.o = torch.nn.Linear(H, 1)

    def forward(self, x):
        return self.o(self.r(x)[0])


def train(kind, H, seed):
    torch.manual_seed(seed)
    g = np.random.default_rng(seed)
    net = Net(kind, H)
    opt = torch.optim.Adam(net.parameters(), lr=0.01)
    for _ in range(ITERS):
        x, y = batch(BATCH, g)
        loss = ((net(x) - y) ** 2).mean()
        opt.zero_grad(); loss.backward(); opt.step()
    return net


rnn = train("rnn", 3, 0)
# the LSTM: the first seed whose read out weight is positive, so the memory holds the peak as a positive number
for seed in range(10):
    lstm = train("lstm", 1, seed)
    if lstm.o.weight.item() > 0:
        break
LSEED = seed

xt, yt = batch(2000, np.random.default_rng(99))
with torch.no_grad():
    rms_rnn = float(((rnn(xt) - yt) ** 2).mean().sqrt())
    rms_lstm = float(((lstm(xt) - yt) ** 2).mean().sqrt())
    torch_rnn = rnn(torch.tensor(SEQ[None, :, None]))[0, :, 0].numpy()
    torch_lstm = lstm(torch.tensor(SEQ[None, :, None]))[0, :, 0].numpy()

# numpy, from the trained weights: every value the page shows
Wx = rnn.r.weight_ih_l0.detach().numpy()[:, 0]
Wh = rnn.r.weight_hh_l0.detach().numpy()
bR = (rnn.r.bias_ih_l0 + rnn.r.bias_hh_l0).detach().numpy()
Vo, co = rnn.o.weight.detach().numpy()[0], rnn.o.bias.item()
h = np.zeros(3)
RNN = []
for x in SEQ:
    h = np.tanh(Wx * x + Wh @ h + bR)
    RNN.append({"h": h.copy(), "y": float(Vo @ h + co)})
Wl = lstm.r.weight_ih_l0.detach().numpy()[:, 0]           # PyTorch order: input, forget, cell, output
Ul = lstm.r.weight_hh_l0.detach().numpy()[:, 0]
bl = (lstm.r.bias_ih_l0 + lstm.r.bias_hh_l0).detach().numpy()
ow, ob = lstm.o.weight.item(), lstm.o.bias.item()
sig = lambda z: 1 / (1 + np.exp(-z))
hl = c = 0.0
LST = []
for x in SEQ:
    z = Wl * x + Ul * hl + bl
    i, f, gg, o = sig(z[0]), sig(z[1]), np.tanh(z[2]), sig(z[3])
    cp = c
    c = f * c + i * gg
    hl = o * np.tanh(c)
    LST.append({"x": x, "i": i, "f": f, "g": gg, "o": o, "cp": cp, "c": c, "h": hl, "y": ow * hl + ob})
target = np.maximum.accumulate(SEQ)

# ------------------------------------------------------------------ the clock
# Seconds. Round 3 (30 Sep 2026), the client: "fig 21, 23 yavaşlat" (slow them down). A time step
# takes twice as long as in round 2, and everything inside it keeps its place in the step (the
# fractions of the step the script uses: the gates move from .06 for .3, the reading enters at
# .15, the hidden state arrives from .3 for .2, the output at .45), so it too moves at half the
# speed. The intro is unchanged.
T1, STEP, HOLD, RESET = .6, 1.8, 3.6, .9      # the first step starts; one step; held after the sixth; fading out
PER = len(SEQ) * STEP + HOLD + RESET
POSTER_T = T1 + len(SEQ) * STEP + 1.2         # the sixth step complete: reduced motion and print
CLOCK = dict(T1=T1, STEP=STEP, HOLD=HOLD, RESET=RESET, PER=PER, POSTER_T=POSTER_T)

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-rnn: Figure 23, an RNN and an LSTM cell on the same sensor stream")
say("")
say("MODEL")
say(f"  task: readings mostly (U(0,1))^2 x 0.8, with probability 0.12 a large one U(0.5, 1); target at every step:")
say(f"  the largest reading so far. Trained with PyTorch (float64), Adam lr 0.01, {ITERS} steps of {BATCH} sequences")
say(f"  of {T}; MSE. RNN: 3 tanh units + linear read out (seed 0). LSTM: 1 memory cell + linear read out (seed {LSEED},")
say("  the first seed whose read out weight is positive).")
say("")
say("CHECK 1: the page's numpy recurrences against PyTorch on the six readings shown")
say(f"  RNN outputs max |difference| {np.max(np.abs(np.array([r['y'] for r in RNN]) - torch_rnn)):.1e}")
say(f"  LSTM outputs max |difference| {np.max(np.abs(np.array([s['y'] for s in LST]) - torch_lstm)):.1e}")
say("")
say("CHECK 2: gates are fractions, and the memory update is the LSTM's own equation")
say(f"  all gates in (0, 1): {all(0 < s[k] < 1 for s in LST for k in ('i', 'f', 'o'))};"
    f" max |c - (f c_prev + i g)| = {max(abs(s['c'] - (s['f'] * s['cp'] + s['i'] * s['g'])) for s in LST):.1e}")
say("")
say("CHECK 3: how well each remembers, root mean square error over 2000 new sequences of 12")
say(f"  RNN (3 units) {rms_rnn:.4f}; LSTM (1 memory cell) {rms_lstm:.4f}")
say("")
say("THE SIX STEPS SHOWN")
say("  t   x      target   RNN out   LSTM: input  forget  cand.   output  memory   out")
for k, (x, r, s) in enumerate(zip(SEQ, RNN, LST)):
    say(f"  {k+1}  {x:.2f}   {target[k]:.2f}     {r['y']:.3f}          {s['i']:.3f}   {s['f']:.3f}  {s['g']:+.3f}  {s['o']:.3f}"
        f"  {s['c']:+.3f}  {s['y']:.3f}")
say("")
say("MOTION (round 3, 30 Sep 2026: the client asked for Figures 21 and 23 slower; round 2 in brackets)")
say(f"  intro unchanged; the first time step starts at t = {T1:.2f} s")
say(f"  one time step {STEP:.2f} s [0.90]; within it, from its start: the gates move from {.06 * STEP:.2f} to"
    f" {.36 * STEP:.2f} s [0.05 to 0.32], the reading enters at {.15 * STEP:.2f} [0.14],")
say(f"  the hidden state arrives from {.3 * STEP:.2f} to {.5 * STEP:.2f} [0.27 to 0.45], the output at"
    f" {.45 * STEP:.2f} [0.41], then {.5 * STEP:.2f} s at rest [0.45]")
say(f"  after the sixth step: held {HOLD:.2f} s [3.20], faded out over {RESET:.2f} s [0.45]; the loop"
    f" {PER:.2f} s [9.05]")
say(f"  poster (reduced motion, print) at t = {POSTER_T:.2f} s [7.20]: the sixth step complete")
mc.check(NAME, L)

DATA = {"x": SEQ, "target": target, "rnn": RNN, "lstm": LST, "rms": [rms_rnn, rms_lstm]}

JS = r"""
const D = DATA, NT = D.x.length;
/* ------------------------------------------------ the clock: one step every STEP seconds (CLOCK, in the Python) */
/*CLOCK*/
function stepNow() {                                // current step k (0..NT-1) and its progress, or -1
  if (t < T1) return { k: -1, p: 0, fade: 1 };
  const c = (t - T1) % PER;
  if (c >= NT * STEP + HOLD) return { k: NT - 1, p: 1, fade: 1 - clamp((c - NT * STEP - HOLD) / RESET) };
  const k = Math.min(NT - 1, Math.floor(c / STEP));
  return { k, p: clamp((c - k * STEP) / STEP), fade: 1 };
}
const vcol = v => signed(v * 2 / 3);               // a value: blue positive, crimson negative

/* ------------------------------------------------ top: the RNN, unrolled */
const RX = k => 196 + 128 * k, RY = 150, RW = 72, RH = 44;
function rnnPart(st) {
  const sa = lab(0);
  text('RNN, unrolled in time', 18, 34 + rise(sa), { size: 16, color: C.body, alpha: sa });
  // what the colours of the hidden state mean (its right edge at 935, where the figure's type ends)
  legend(781, 13, 154, [
    [(x, y, a) => rect(x - 6, y - 6, 12, 12, { fill: vcol(1), stroke: C.ink, width: .8, alpha: a }), 'positive value'],
    [(x, y, a) => rect(x - 6, y - 6, 12, 12, { fill: vcol(-1), stroke: C.ink, width: .8, alpha: a }), 'negative value'],
  ], { alpha: lab(.12) });
  const la = lab(.1);
  text('output', 18, 104, { size: 15, color: C.muted, alpha: la });
  text('largest so far', 18, 122, { size: 14, color: C.muted, alpha: la });
  text('hidden state', 18, 177, { size: 15, color: C.muted, alpha: la });
  text('input', 18, 256, { size: 15, color: C.muted, alpha: la });
  text('reading', 18, 274, { size: 14, color: C.muted, alpha: la });
  // h0 into the first cell
  arrow(RX(0) - RW / 2 - 40, RY + RH / 2, RX(0) - RW / 2 - 2, RY + RH / 2, { width: 1.4, head: 8, alpha: seg(.1, .3) });
  math('h_0', RX(0) - RW / 2 - 36, RY + RH / 2 - 9, { size: 15, align: 'left', color: C.body, alpha: seg(.15, .3) });
  for (let k = 0; k < NT; k++) {
    const cx = RX(k), a = seg(.04 + .05 * k, .32);
    rect(cx - RW / 2, RY, RW, RH, { fill: '#fff', stroke: C.ink, width: 1.4, alpha: a });
    math('\\rm{tanh}', cx, RY + RH / 2 + 6, { size: 15, align: 'center', color: C.body, alpha: a });
    // input and output arrows
    arrow(cx, RY + RH + 50 - 16, cx, RY + RH + 2, { width: 1.3, head: 8, alpha: a });
    arrow(cx, RY - 2, cx, RY - 34, { width: 1.3, head: 8, alpha: a });
    const done = st.k > k || (st.k === k && st.p > .15), on = st.k === k && st.p <= 1 && st.fade > 0;
    const va = done ? st.fade : 0;
    // the reading
    node(cx, RY + RH + 66, 17, { fill: done ? mixHex('#FFFFFF', C.mist, .6 * st.fade) : '#fff', stroke: on ? mixHex(C.ink, C.accent, st.fade) : C.ink, width: on ? lerp(1.3, 2, st.fade) : 1.3, alpha: a });
    math(D.x[k].toFixed(2), cx, RY + RH + 71, { size: 14, align: 'center', alpha: a });
    math(`t = ${k + 1}`, cx, RY + RH + 104, { size: 14, align: 'center', color: C.muted, alpha: a });
    if (on) rect(cx - RW / 2 - 3, RY - 3, RW + 6, RH + 6, { stroke: C.accent, width: 1.8, alpha: st.fade });
    // the output: the RNN's own answer
    const oa = st.k > k || (st.k === k && st.p > .45) ? st.fade : 0;
    math(D.rnn[k].y.toFixed(2), cx, RY - 44, { size: 16, align: 'center', alpha: oa });
    if (k === NT - 1) math(`(\\rm{true}\\ ${D.target[k].toFixed(2)})`, cx + 30, RY - 44, { size: 14, color: C.muted, alpha: oa });
    // the hidden state carried to the next step
    if (k < NT - 1) {
      const x0 = cx + RW / 2, x1 = RX(k + 1) - RW / 2;
      arrow(x0 + 2, RY + RH / 2, x1 - 2, RY + RH / 2, { width: 1.4, head: 8, alpha: a });
    }
    const hx = k < NT - 1 ? (cx + RW / 2 + RX(k + 1) - RW / 2) / 2 : cx + RW / 2 + 28;
    const ha = st.k > k || (st.k === k && st.p > .3) ? st.fade * (st.k === k ? clamp((st.p - .3) / .2) : 1) : 0;
    for (let j = 0; j < 3; j++) rect(hx - 20 + 14 * j, RY + RH / 2 - 22, 12, 12, { fill: vcol(D.rnn[k].h[j]), stroke: C.ink, width: .8, alpha: ha });
    if (ha > 0) math(`h_{${k + 1}}`, hx, RY + RH / 2 + 22, { size: 14, align: 'center', color: C.body, alpha: ha });
  }
}

/* ------------------------------------------------ bottom: inside one LSTM cell */
const CY = 404, BY = 622, GY = 530, GW = 58, GH = 46;
const XF = 330, XI = 430, XG = 530, XO = 650, XT = 740, XM = 480, OY_ = 470, XR = 790;
/* a gate: its box filled from the bottom as far as it is open (lv, moving between
   steps), its symbol, and its value at this step (v, exact) */
function gateBox(x, sym, lv, v, show, a) {
  rect(x - GW / 2, GY - GH / 2, GW, GH, { fill: '#fff', stroke: C.ink, width: 1.3, alpha: a });
  if (lv !== null && show > 0 && sym !== 'tanh') rect(x - GW / 2 + 1, GY + GH / 2 - 1 - (GH - 2) * clamp(lv), GW - 2, (GH - 2) * clamp(lv), { fill: C.mist, stroke: null, alpha: a * show });
  math(sym === 'tanh' ? '\\rm{tanh}' : '\\sigma', x, GY - 3, { size: sym === 'tanh' ? 15 : 18, align: 'center', alpha: a });
  if (v !== null && show > 0) math(num(v), x, GY + 17, { size: 14, align: 'center', color: C.navy, alpha: a * show });
}
function opNode(x, y, s, a) {
  node(x, y, 11, { fill: '#fff', width: 1.3, alpha: a });
  math(s, x, y + 6, { size: 17, align: 'center', alpha: a });
}
/* a label sitting on a line, on white, as TikZ sets a node on a path */
function onLine(words, x, y, a, color = C.ink) {
  const w = text(words, 0, -1e4, { size: 15, alpha: 0 });
  rect(x - w / 2 - 4, y - 13, w + 8, 18, { fill: '#fff', stroke: null, alpha: a });
  text(words, x, y, { size: 15, align: 'center', color, alpha: a });
}
function lstmPart(st) {
  const sa = lab(.2);
  text('inside one LSTM cell', 18, 330 + rise(sa), { size: 16, color: C.body, alpha: sa });
  // this step's values; the gates move from the last step's openness to this one's,
  // and the printed numbers (always the model's own) switch halfway
  const k = st.k, S = k >= 0 ? D.lstm[k] : null, Pv = k > 0 ? D.lstm[k - 1] : null;
  const q = k >= 0 ? easeInOut(clamp((st.p - .06) / .3)) : 0;
  const vis = S ? st.fade * (Pv ? 1 : q) : 0, N = S && Pv && q < .5 ? Pv : S;
  const lv = key => S ? (Pv ? lerp(Pv[key], S[key], q) : S[key]) : null;
  const a = seg(.15, .35), pa = seg(.2, .45);
  // the cell
  rect(170, 356, 660, 300, { fill: null, stroke: C.ink, width: 1.3, alpha: a });
  // the memory line (cell state) across the top: heavy, it carries what the cell keeps
  line([[100, CY], [XF - 11, CY]], { width: 2.4, progress: pa });
  line([[XF + 11, CY], [XM - 11, CY]], { width: 2.4, progress: pa });
  line([[XM + 11, CY], [900, CY]], { width: 2.4, progress: pa });
  arrow(880, CY, 905, CY, { width: 2.4, head: 11, alpha: pa });
  // the hidden state and the input along the bottom
  line([[100, BY], [XO, BY]], { width: 1.5, progress: pa });
  line([[210, 694], [210, BY]], { width: 1.5, progress: pa });
  dot(210, BY, 2.6, { fill: C.ink, alpha: pa });
  for (const x of [XF, XI, XG, XO]) { line([[x, BY], [x, GY + GH / 2 + 1]], { width: 1.3, alpha: pa }); dot(x, BY, 2.4, { fill: C.ink, alpha: pa }); }
  // forget gate: up to its product on the memory line
  arrow(XF, GY - GH / 2, XF, CY + 12, { width: 1.3, head: 8, alpha: pa });
  // input gate times candidate, added to the memory
  line([[XI, GY - GH / 2], [XI, OY_], [XM - 11, OY_]], { width: 1.3, alpha: pa });
  line([[XG, GY - GH / 2], [XG, OY_], [XM + 11, OY_]], { width: 1.3, alpha: pa });
  arrow(XM, OY_ - 11, XM, CY + 12, { width: 1.3, head: 8, alpha: pa });
  // output: tanh of the memory times the output gate, out as the new hidden state
  line([[XT, CY], [XT, CY + 22]], { width: 1.3, alpha: pa });
  rect(XT - 27, CY + 22, 54, 26, { fill: '#fff', stroke: C.ink, width: 1.3, alpha: pa });
  math('\\rm{tanh}', XT, CY + 40, { size: 15, align: 'center', alpha: pa });
  arrow(XT, CY + 48, XT, OY_ - 12, { width: 1.3, head: 8, alpha: pa });
  line([[XO, GY - GH / 2], [XO, OY_], [XT - 11, OY_]], { width: 1.3, alpha: pa });
  line([[XT + 11, OY_], [XR, OY_], [XR, BY], [880, BY]], { width: 1.5, alpha: pa });
  arrow(880, BY, 905, BY, { width: 1.5, head: 9, alpha: pa });
  opNode(XF, CY, '\\times', pa); opNode(XM, CY, '+', pa); opNode(XM, OY_, '\\times', pa); opNode(XT, OY_, '\\times', pa);
  gateBox(XF, 's', lv('f'), N ? N.f : null, vis, pa);
  gateBox(XI, 's', lv('i'), N ? N.i : null, vis, pa);
  gateBox(XG, 'tanh', null, N ? N.g : null, vis, pa);
  gateBox(XO, 's', lv('o'), N ? N.o : null, vis, pa);
  // names, his words, on their lines
  const na = lab(.3), ny = GY + GH / 2 + 30;
  onLine('forget gate', XF, ny, na); onLine('input gate', XI, ny, na);
  onLine('candidate', XG, ny, na, C.body); onLine('output gate', XO, ny, na);
  text('memory cell', 600, CY - 14, { size: 15, align: 'center', alpha: na });
  math('c_{t-1}', 96, CY - 10, { size: 16, align: 'right', alpha: na });
  math('c_t', 912, CY + 6, { size: 16, alpha: na });
  math('h_{t-1}', 96, BY - 10, { size: 16, align: 'right', alpha: na });
  math('h_t', 912, BY + 6, { size: 16, alpha: na });
  math('x_t', 200, 694, { size: 16, align: 'right', alpha: na });
  // this step's numbers
  if (vis > 0) {
    math(num(N.cp), 110, CY + 24, { size: 15, color: C.body, alpha: vis });
    math(`c = ${num(N.c)}`, 822, CY - 12, { size: 16, align: 'right', color: C.accent, alpha: vis });
    math(`h = ${num(N.h)}`, 850, BY + 28, { size: 15, color: C.body, alpha: vis });
    math(`\\rm{output}\\ \\ ${N.y.toFixed(2)}`, 850, BY + 52, { size: 16, alpha: vis });
    math(`x = ${N.x.toFixed(2)}`, 222, 690, { size: 15, color: C.body, alpha: vis });
    math(`\\rm{step}\\ t = ${N === S ? k + 1 : k}`, 830, 346, { size: 15, align: 'right', color: C.muted, alpha: vis });
  }
  // how well each remembers the peak
  const ea = lab(.5);
  text(`error, largest reading so far: RNN (3 units) ${D.rms[0].toFixed(2)}, LSTM (1 memory cell) ${D.rms[1].toFixed(2)}`,
       18, H - 32, { size: 14, color: C.muted, alpha: ea });
  text('both trained here (PyTorch) on random sensor streams of 12 readings; errors are RMS over 2,000 new streams',
       18, H - 12, { size: 14, color: C.muted, alpha: ea });
}

function draw() {
  const st = stepNow();
  rnnPart(st);
  lstmPart(st);
}
boot();
"""
assert JS.count("/*CLOCK*/") == 1
JS = JS.replace("/*CLOCK*/", "const " + ", ".join(f"{k} = {round(v, 6):g}" for k, v in CLOCK.items()) + ";")

TITLE = "Figure 23: RNN and LSTM architecture"
ARIA = ("Top: a simple RNN unrolled over six time steps of a sensor stream. Each step takes a reading, "
        "updates its hidden state of three numbers and passes it to the next step, and outputs its "
        "estimate of the largest reading so far. Bottom: inside one LSTM cell working on the same readings, "
        "the forget gate, the input gate and the output gate, each filled as far as it is open, and the "
        "memory cell running along the top. At the large reading the input gate opens and the memory takes "
        "the new peak; afterwards the forget gate stays open and the input gate closed, so the memory keeps it.")

if __name__ == "__main__":
    print(f"RMS RNN {rms_rnn:.4f}, LSTM {rms_lstm:.4f}; LSTM seed {LSEED}")
    mc.publish(NAME, TITLE, ARIA, 1000, 770, DATA, JS,
               look=(0.3, 0.8, 1.2, 1.6, 2.6, 4.5, 6.4, 8.2, 10.0, 12.6, 15.0, 16.2))
