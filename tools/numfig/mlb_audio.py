"""Figure 22: audio processing with a neural network. A waveform becomes a
spectrogram, convolution filters scan it for local patterns, and dense layers
turn those patterns into a prediction.

Model: one second of a synthetic machine sound, 8 kHz: a gearbox (30 teeth)
runs up from 13.3 to 53.3 turns per second in 0.25 s and then runs steady;
its gear mesh tone and first harmonic sweep up (pitch changes) and then hold
(steady tones). In the faulty machine a damaged tooth on the output gear
(ratio 1 : 3) strikes once per output turn, a short 2.2 kHz click every
56 ms (repeated sounds). Plus a little white noise.

The spectrogram is the short time Fourier transform (Hann window 128 samples
= 16 ms, hop 4 ms), in dB over a 50 dB range, stored in 8 bits like an image.
Three fixed 9-wide line filters scan it: horizontal (steady tones), rising
(pitch changes), vertical (repeated sounds); ReLU; global average pooling
gives three numbers, and a small dense network (3 -> 4 ReLU -> 2 softmax), trained
here on 300 synthetic clips (half faulty, random speeds, run-ups, click
strengths 0.5 to 1.2 and noise 0.01 to 0.03) turns them into the probabilities of normal and machine
fault.

The motion: a time cursor sweeps the second; the spectrogram and the three
feature maps are computed column by column behind it (the window on the
waveform is the Fourier window); then each map is averaged to one number and
the dense layers give the prediction. A faulty and a normal machine in
turn.

Run: python tools/numfig/mlb_audio.py [--look]
"""
import numpy as np
from scipy.signal import correlate2d, stft

import common
import mlb_common as mc

NAME = "audio"
FS, DUR, NPER, HOP, DBR = 8000, 1.0, 128, 32, 50.0
NS = int(FS * DUR)
TT = np.arange(NS) / FS
TEETH, RATIO, FCLICK, TAU = 30, 3.0, 2200.0, 0.0003


def machine(rng, fault, f0=13.3, f1=53.3, tr=0.25, noise=0.02, imp=1.0):
    fr = np.where(TT < tr, f0 + (f1 - f0) * TT / tr, f1) if tr > 0 else np.full(NS, f1)
    ph = 2 * np.pi * np.cumsum(fr) / FS
    x = 0.5 * np.sin(TEETH * ph) + 0.25 * np.sin(2 * TEETH * ph + 0.7)
    hits = []
    if fault:
        k = np.floor(ph / (2 * np.pi) / RATIO)
        hits = (np.where(np.diff(k) > 0)[0] + 1).tolist()
        for h in hits:
            n = np.arange(NS - h)
            x[h:] += imp * np.exp(-n / FS / TAU) * np.sin(2 * np.pi * FCLICK * n / FS)
    x = x + noise * rng.standard_normal(NS)
    return x / np.max(np.abs(x)), hits


def spectrogram(x):
    f, t, Z = stft(x, FS, window="hann", nperseg=NPER, noverlap=NPER - HOP, boundary=None, padded=False)
    S = 20 * np.log10(np.abs(Z) + 1e-12)
    S = np.clip((S - S.max() + DBR) / DBR, 0, 1)
    return f, t, np.round(S * 254) / 254, Z      # 8 bits, as the page stores it


def line_kernel(slope, n=9, w=0.7):
    r = np.arange(n) - n // 2
    R, Cc = np.meshgrid(r, r, indexing="ij")       # rows: frequency bins, columns: frames
    d = (R - slope * Cc) / np.sqrt(1 + slope ** 2)
    k = np.exp(-0.5 * (d / w) ** 2)
    k -= k.mean()
    return k / np.abs(k).sum() * 2


KH = np.zeros((9, 9)); KH[3] = -.5; KH[4] = 1; KH[5] = -.5; KH /= 9          # steady tones
KV = KH.T.copy()                                                            # repeated sounds
KD = line_kernel(0.6)                                                       # pitch changes
KERN = [KH, KD, KV]
NAMES_K = ["steady tones", "pitch changes", "repeated sounds"]


def maps(S):
    return [np.maximum(correlate2d(S, K, mode="same", boundary="symm"), 0) for K in KERN]


def features(S):
    return np.array([m.mean() for m in maps(S)])     # global average pooling


# ------------------------------------------------------------------ the classifier
rng = np.random.default_rng(1)
Xf, yf = [], []
for i in range(400):
    fault = i % 2 == 1
    run = rng.uniform() < 0.6
    x, _ = machine(rng, fault, f0=rng.uniform(8, 20), f1=rng.uniform(40, 60), tr=rng.uniform(0.1, 0.5) if run else 0,
                   noise=rng.uniform(0.01, 0.03), imp=rng.uniform(0.5, 1.2))
    Xf.append(features(spectrogram(x)[2])); yf.append(int(fault))
Xf, yf = np.array(Xf), np.array(yf)
mu, sd = Xf[:300].mean(0), Xf[:300].std(0)
A = (Xf - mu) / sd
g = np.random.default_rng(0)
W1, b1 = g.standard_normal((3, 4)) * 0.5, np.zeros(4)
W2, b2 = g.standard_normal((4, 2)) * 0.5, np.zeros(2)


def dense(Z):
    h = np.maximum(Z @ W1 + b1, 0)
    o = h @ W2 + b2
    o = o - o.max(1, keepdims=True)
    p = np.exp(o)
    return h, p / p.sum(1, keepdims=True)


tr_ = slice(0, 300)
for ep in range(3000):
    h, p = dense(A[tr_])
    d = p.copy(); d[np.arange(300), yf[tr_]] -= 1; d /= 300
    gW2, gb2 = h.T @ d, d.sum(0)
    dh = d @ W2.T * (h > 0)
    gW1, gb1 = A[tr_].T @ dh, dh.sum(0)
    W1 -= 0.5 * gW1; b1 -= 0.5 * gb1; W2 -= 0.5 * gW2; b2 -= 0.5 * gb2
acc_tr = int(np.sum(dense(A[:300])[1].argmax(1) == yf[:300]))
acc_te = int(np.sum(dense(A[300:])[1].argmax(1) == yf[300:]))

# ------------------------------------------------------------------ the two clips shown
rs = np.random.default_rng(7)
CLIPS = []
for fault in (True, False):
    x, hits = machine(rs, fault)
    f, t, S, Z = spectrogram(x)
    M = maps(S)
    feat = np.array([m.mean() for m in M])
    h, p = dense(((feat - mu) / sd)[None])
    arg = [np.unravel_index(int(np.argmax(m)), m.shape) for m in M]
    # the waveform, as each drawing column's lowest and highest sample (440 columns)
    cols = np.array_split(x, 440)
    CLIPS.append({"x": x, "hits": hits, "S": S, "Z": Z, "M": M, "feat": feat, "h": h[0], "p": p[0], "arg": arg,
                  "wmin": np.array([c.min() for c in cols]), "wmax": np.array([c.max() for c in cols]), "fault": fault})
f_bins, t_frames = f, t
MAPMAX = [max(c["M"][k].max() for c in CLIPS) for k in range(3)]

# ------------------------------------------------------------------ checks
L = []
say = L.append
say("nf-mlb-audio: Figure 22, audio processing with a neural network")
say("")
say("MODEL")
say(f"  {DUR:g} s at {FS} Hz; gearbox {TEETH} teeth, run up 13.3 -> 53.3 turns/s in 0.25 s, then steady;")
say(f"  mesh tone 30 f_r and harmonic 60 f_r; faulty: one click per output turn (ratio 1:{RATIO:g}),")
say(f"  {FCLICK:g} Hz, decay {TAU*1e3:g} ms; white noise 0.02. STFT: Hann {NPER} samples ({NPER/FS*1e3:g} ms),"
    f" hop {HOP} ({HOP/FS*1e3:g} ms); {S.shape[0]} bins x {S.shape[1]} frames;")
say(f"  dB over {DBR:g} dB, 8 bit. Filters 9 wide: horizontal, rising (slope 0.6 bin/frame), vertical; ReLU;")
say("  global average; dense 3-4-2 (ReLU, softmax), gradient descent 3000 epochs, rate 0.5.")
say("")
say("CHECK 1: scipy's STFT against a direct DFT of one frame")
x0 = CLIPS[0]["x"]
k0 = 100
fr_ = x0[k0 * HOP:k0 * HOP + NPER] * np.hanning(NPER + 1)[:-1]
dft = np.fft.rfft(fr_) / np.hanning(NPER + 1)[:-1].sum()
say(f"  frame {k0}: max |scipy - numpy DFT| = {np.max(np.abs(CLIPS[0]['Z'][:, k0] - dft)):.1e}"
    " (periodic Hann window, scaled by its sum)")
say("")
say("CHECK 2: what the spectrogram shows against what was synthesized")
Zs = np.abs(CLIPS[1]["Z"][:, 150:])                 # steady part, normal clip
spec_mean = Zs.mean(1)
for fk in (30 * 53.3, 60 * 53.3):
    b = int(round(fk / (FS / NPER)))
    b = b - 2 + int(np.argmax(spec_mean[b - 2:b + 3]))
    a_, b_, c_ = np.log(spec_mean[b - 1:b + 2])
    d = 0.5 * (a_ - c_) / (a_ - 2 * b_ + c_)
    say(f"  steady tone: peak at {(b + d) * FS / NPER:.1f} Hz (parabolic), synthesized {fk:.1f} Hz,"
        f" bin width {FS / NPER:.1f} Hz")
col = CLIPS[0]["M"][2].sum(0)
col = col - col.mean()
ac = np.correlate(col, col, "full")[col.size - 1:]
lag = int(np.argmax(ac[5:40])) + 5
say(f"  repeated sounds: the vertical filter's autocorrelation peaks at {lag} frames = {lag * HOP / FS * 1e3:.1f} ms;"
    f" clicks every {RATIO / 53.3 * 1e3:.2f} ms (steady), {len(CLIPS[0]['hits'])} clicks in the second")
say("")
say("CHECK 3: the page's own correlation (symmetric edges, as written in its script) against scipy")
Sx = CLIPS[0]["S"]
pad = np.pad(Sx, 4, mode="symmetric")
mine = np.maximum(np.array([[np.sum(KV * pad[r:r + 9, c:c + 9]) for c in range(Sx.shape[1])] for r in range(Sx.shape[0])]), 0)
say(f"  vertical filter, faulty clip: max |difference| {np.max(np.abs(mine - CLIPS[0]['M'][2])):.1e}")
say("")
say("CHECK 4: the classifier")
say(f"  training {acc_tr} of 300, held out {acc_te} of 100 synthetic clips")
for c in CLIPS:
    say(f"  {'faulty' if c['fault'] else 'normal'} clip: mean responses {np.round(c['feat'], 4).tolist()} ->"
        f" p(normal, fault) = {np.round(c['p'], 4).tolist()}")
mc.check(NAME, L)

q = lambda S: common.i8(np.round(S * 254) - 127)
DATA = {
    "fs": FS, "hop": HOP, "nper": NPER, "nb": int(S.shape[0]), "nf": int(S.shape[1]),
    "t0": float(t_frames[0]), "dt": HOP / FS, "fmax": FS / 2,
    "kern": [k.ravel() for k in KERN], "kn": NAMES_K, "mapmax": MAPMAX,
    "clips": [{"S": q(c["S"]), "wmin": c["wmin"], "wmax": c["wmax"], "feat": c["feat"], "h": c["h"], "p": c["p"],
               "arg": [[int(a), int(b)] for a, b in c["arg"]], "fault": c["fault"]} for c in CLIPS],
    "acc": [acc_tr, acc_te], "fmean": mu, "fsd": sd, "W1": W1, "W2": W2,
}

JS = r"""
const D = DATA, NB = D.nb, NFR = D.nf;
/* ------------------------------------------------ layout */
const LX = 88, LW = 440, WAV = { y: 46, h: 78 }, SPC = { y: 166, h: 150 }, MY = [352, 420, 488], MH = 58;
const TX = s => LX + s * LW;                          // clip time (s) to x
const KX = 546, KS = 6, DX = 800, OX = 872;
/* ------------------------------------------------ images: the spectrograms, and the maps the filters make of them */
function unpack(b) { const v = b64i8(b), S = new Float64Array(v.length); for (let i = 0; i < v.length; i++) S[i] = (v[i] + 127) / 254; return S; }
function correlate(S, K) {                         // same size, symmetric boundary, like scipy's correlate2d
  const R = new Float64Array(NB * NFR), ref = (i, n) => i < 0 ? -i - 1 : i >= n ? 2 * n - i - 1 : i;
  for (let r = 0; r < NB; r++) for (let c = 0; c < NFR; c++) {
    let s = 0;
    for (let a = 0; a < 9; a++) for (let b = 0; b < 9; b++) s += K[a * 9 + b] * S[ref(r + a - 4, NB) * NFR + ref(c + b - 4, NFR)];
    R[r * NFR + c] = Math.max(0, s);
  }
  return R;
}
function toCanvas(V, scale) {
  const cv_ = document.createElement('canvas'); cv_.width = NFR; cv_.height = NB;
  const g = cv_.getContext('2d'), im = g.createImageData(NFR, NB);
  for (let r = 0; r < NB; r++) for (let c = 0; c < NFR; c++) {
    const li = Math.round(clamp(V[r * NFR + c] / scale) * 255) * 3, o = ((NB - 1 - r) * NFR + c) * 4;
    im.data[o] = SEQ[li]; im.data[o + 1] = SEQ[li + 1]; im.data[o + 2] = SEQ[li + 2]; im.data[o + 3] = 255;
  }
  g.putImageData(im, 0, 0); return cv_;
}
const IMG = D.clips.map(c => { const S = unpack(c.S); return { spec: toCanvas(S, 1), maps: D.kern.map((K, k) => toCanvas(correlate(S, K), D.mapmax[k])) }; });
/* ------------------------------------------------ the clock: a faulty, then a normal machine */
const T0 = .3, CP = 7.6, SW0 = .3, SW = 2.5, PL0 = SW0 + SW + .1, DN0 = PL0 + .5, OT0 = DN0 + .4;
const POSTER_T = T0 + 5.5;
function now() {
  if (t < T0) return { k: 0, u: -1 };
  const c = (t - T0) % (2 * CP);
  return { k: c < CP ? 0 : 1, u: c < CP ? c : c - CP };
}
const frameX = j => TX(D.t0 + j * D.dt);
const binY = (i, y0, h) => y0 + h - (i + .5) / NB * h;

function drawImage(cvs, y, h, upto, alpha) {         // the image, revealed up to clip time upto
  if (alpha <= 0 || upto <= 0) return;
  ctx.save(); ctx.globalAlpha *= alpha; ctx.beginPath(); ctx.rect(LX, y, Math.min(LW, upto * LW), h); ctx.clip();
  ctx.imageSmoothingEnabled = true;
  const x0 = frameX(-.5), x1 = frameX(NFR - .5);
  ctx.drawImage(cvs, x0, y, x1 - x0, h); ctx.restore();
}

function draw() {
  const st = now(), C_ = D.clips[st.k], I_ = IMG[st.k], u = st.u;
  const fin = u >= 0 ? 1 - clamp((u - (CP - .35)) / .3) : 0, din = u >= 0 ? clamp(u / .3) : 0;
  const cur = u < SW0 ? 0 : Math.min(1, (u - SW0) / SW);           // clip time the sweep has reached
  const la = lab(.05);
  /* waveform */
  text('waveform', LX, WAV.y - 12 + rise(la), { size: 16, color: C.body, alpha: la });
  const Aw = axes({ x: LX, y: WAV.y, w: LW, h: WAV.h, xlim: [0, 1], ylim: [-1.1, 1.1], xticks: [0, .2, .4, .6, .8, 1], yticks: [-1, 0, 1],
    xfmt: () => '', ylabel: '\\rm{pressure}', ylabelGap: 40, progress: seg(0, .35) });
  if (din > 0) {
    ctx.save(); ctx.globalAlpha *= din * fin; ctx.strokeStyle = C.navy; ctx.lineWidth = 1; ctx.beginPath();
    const n = C_.wmin.length;
    for (let i = 0; i < n; i++) { const x = LX + (i + .5) / n * LW; ctx.moveTo(x, Aw.Y(C_.wmax[i])); ctx.lineTo(x, Aw.Y(C_.wmin[i]) + .5); }
    ctx.stroke(); ctx.restore();
  }
  // the Fourier window at the cursor
  const sweeping = u >= SW0 && u < SW0 + SW + .05 && fin > 0;
  if (sweeping) {
    const tc = D.t0 + cur * (1 - D.t0), w = D.nper / D.fs;
    rect(TX(tc - w / 2), WAV.y + 1, w * LW, WAV.h - 2, { fill: C.wash, stroke: C.accent, width: 1.4, alpha: fin });
  }
  /* spectrogram */
  text('spectrogram', LX, SPC.y - 12 + rise(lab(.1)), { size: 16, color: C.body, alpha: lab(.1) });
  drawImage(I_.spec, SPC.y, SPC.h, u >= SW0 ? cur : 0, fin);
  axes({ x: LX, y: SPC.y, w: LW, h: SPC.h, xlim: [0, 1], ylim: [0, 4], xticks: [0, .2, .4, .6, .8, 1], yticks: [0, 1, 2, 3, 4],
    xfmt: () => '', ylabel: 'f\\ (\\rm{kHz})', ylabelGap: 34, progress: seg(.05, .35) });
  /* the three filters and their maps */
  text('convolution filters', KX, SPC.y + SPC.h + 26 + rise(lab(.18)), { size: 16, color: C.body, alpha: lab(.18) });
  text('local patterns', LX, SPC.y + SPC.h + 26 + rise(lab(.15)), { size: 16, color: C.body, alpha: lab(.15) });
  for (let k = 0; k < 3; k++) {
    const y = MY[k], a = seg(.1 + .04 * k, .35);
    drawImage(I_.maps[k], y, MH, u >= SW0 ? cur : 0, fin);
    axes({ x: LX, y, w: LW, h: MH, xlim: [0, 1], ylim: [0, 4], xticks: [0, .2, .4, .6, .8, 1], yticks: [],
      xfmt: k === 2 ? (v => v === 0 ? '0' : v.toFixed(1)) : (() => ''), xlabel: k === 2 ? '\\rm{time}\\ \\ t\\ (\\rm{s})' : '', progress: a });
    // the kernel, as a picture of its weights (higher frequency up, as in the spectrogram)
    cells(KX, y + 2, 9, 9, KS, (i, j) => { const w = D.kern[k][(8 - i) * 9 + j]; return w >= 0 ? mixHex('#FFFFFF', C.blue, clamp(w / .12)) : mixHex('#FFFFFF', K.red, clamp(-w / .12)); },
          { alpha: a, gridColor: null, frame: C.ink, frameWidth: 1 });
    text(D.kn[k], KX + 9 * KS + 12, y + 18 + rise(lab(.2 + .04 * k)), { size: 15, alpha: lab(.2 + .04 * k) });
    // global average pooling: each map becomes one number, its mean
    const pa = u < PL0 ? 0 : clamp((u - PL0) / .3) * fin;
    if (pa > 0) {
      rect(LX, y, LW, MH, { stroke: C.accent, width: 1.6, alpha: pa * (1 - clamp((u - PL0 - .5) / .4)) });
      math(`\\rm{mean}\\ \\ ${C_.feat[k].toFixed(3)}`, KX + 9 * KS + 12, y + 42, { size: 15, color: C.accent, alpha: pa });
    }
  }
  if (sweeping) for (const [y, h] of [[SPC.y, SPC.h], [MY[0], MY[2] + MH - MY[0]]]) {
    const x = TX(D.t0 + cur * (1 - D.t0));
    line([[x, y], [x, y + h]], { color: C.accent, width: 1.2, alpha: fin });
  }
  /* dense layers and the prediction */
  text('dense layers', DX, 214 + rise(lab(.25)), { size: 16, color: C.body, alpha: lab(.25), align: 'center' });
  text('prediction', OX + 18, 214 + rise(lab(.28)), { size: 16, color: C.body, alpha: lab(.28) });
  const dn = u < DN0 ? 0 : clamp((u - DN0) / .35), ot = u < OT0 ? 0 : clamp((u - OT0) / .35);
  const HY = i => 250 + i * 46, OY = j => 280 + j * 78, hm = Math.max(...C_.h, 1e-6);
  const ea = seg(.3, .35);
  for (let k = 0; k < 3; k++) for (let i = 0; i < 4; i++) {
    const w = D.W1[k][i], a = Math.min(1, Math.abs(w) / 3);
    line([[KX + 9 * KS + 118, MY[k] + 37], [DX - 9, HY(i)]], { color: w >= 0 ? C.blue : K.red, width: .5 + 2 * a, alpha: (.2 + .5 * a) * ea });
  }
  for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) {
    const w = D.W2[i][j], a = Math.min(1, Math.abs(w) / 3);
    line([[DX + 9, HY(i)], [OX - 11, OY(j)]], { color: w >= 0 ? C.blue : K.red, width: .5 + 2 * a, alpha: (.2 + .5 * a) * ea });
  }
  for (let i = 0; i < 4; i++) node(DX, HY(i), 9, { fill: mixHex('#FFFFFF', C.blue, dn * fin * C_.h[i] / hm), width: 1.3, alpha: seg(.3 + .03 * i, .3) });
  const pred = C_.p[1] > C_.p[0] ? 1 : 0, names = ['normal', 'machine fault'];
  for (let j = 0; j < 2; j++) {
    const y = OY(j), a = seg(.36 + .04 * j, .3), win = j === pred && ot >= 1;
    node(OX, y, 11, { fill: mixHex('#FFFFFF', C.blue, ot * fin * C_.p[j]), width: 1.3, alpha: a });
    text(names[j], OX + 18, y - 4, { size: 15, bold: win, color: win ? C.accent : C.ink, alpha: a });
    rect(OX + 18, y + 5, 60, 10, { stroke: C.rule, width: .8, alpha: a });
    if (ot > 0) rect(OX + 18, y + 5, Math.max(.4, 60 * C_.p[j] * easeOut(ot)), 10, { fill: win ? C.accent : C.blue, stroke: null, alpha: fin });
    if (ot > 0) math(C_.p[j].toFixed(2), OX + 84, y + 14, { size: 14, color: win ? C.accent : C.body, alpha: ot * fin });
  }
  text(`synthetic gearbox sound, 8 kHz; STFT Hann 16 ms, hop 4 ms; dense 3-4-2 trained on 300 clips, ${D.acc[1]}/100 held out right`,
       18, H - 12, { size: 14, color: C.muted, alpha: lab(.5) });
}
boot();
"""

TITLE = "Figure 22: Audio processing with a neural network"
ARIA = ("One second of a machine's sound: its waveform on top, its spectrogram below it, computed column by "
        "column as a cursor sweeps the second. Three convolution filters scan the spectrogram and light up "
        "three local patterns: the rising tones of the machine speeding up, its steady tones, and the "
        "repeated clicks of a damaged gear tooth. Each map, averaged to one number, goes through dense layers "
        "to the prediction, machine fault, and then the same for a normal machine, which has no clicks.")

if __name__ == "__main__":
    print(f"classifier {acc_tr}/300, {acc_te}/100; clips p = {[np.round(c['p'], 3).tolist() for c in CLIPS]}")
    mc.publish(NAME, TITLE, ARIA, 1000, 640, DATA, JS, look=(0.3, 0.8, 1.5, 2.4, 3.3, 3.9, 4.5, 5.8, 9.5, 12.5))
