"""Figure 3 of the sound document (sound-detection-and-tracking, image3).

His caption: "Figure 3. A background noise-reduction algorithm where background
noise (noise component of the noisy speech signal) and speech audio (clean
signal of interest) separately used for training a variational autoencoder
neural network model, which estimates the clean spectrogram of the speed
(signal of interest with no noise)." His picture (from Nogales et al. 2024)
is a pipeline: "Background noise" and "Speech audio" go into "Audio mixing",
out comes "Mixed audio", a "Visual transformation representation" turns it
into the "Visual representation mixed audio", the "Variational Autoencoder"
takes that, and the "Visual representation speech audio" comes from the
speech audio through its own "Visual transformation representation".

Model. Every signal is computed:
- speech audio: a synthetic, speech-like voice at 16 kHz: the harmonics of a
  gliding pitch f0 (130 to 215 Hz), each shaped by the vocal tract's formant
  resonances of the vowels u, a, e, i, o (Peterson and Barney's formant
  frequencies), with a -6 dB per octave source, syllable envelopes, and two
  fricatives (s, sh) of band-passed noise;
- background noise: pink noise (power falling 3 dB per octave), stationary;
- audio mixing: their sum, at a signal-to-noise ratio of 10 dB;
- visual transformation representation: the short-time Fourier transform
  (Hann window 32 ms, hop 8 ms), its magnitude in dB: the spectrogram.
The two pictures are the spectrograms of the mixed audio and of the speech
audio, on one dB scale.

The model box. His caption says the VAE is trained on these pairs to
estimate the clean spectrogram; the picture on its right is what his lower
path computes, the speech audio's own spectrogram, the target the network
learns to reproduce. No trained network is claimed here: the VAE is drawn as
a block (encoder, latent z, decoder) with no output of its own, and the
picture it points to is the clean speech's spectrogram, computed exactly.

Run: python tools/numfig/snd_denoise.py [--look]
"""
import base64
import io
import os
import sys

import numpy as np
from PIL import Image
from scipy.signal import butter, istft, sosfiltfilt, stft, welch

import common
import snd_common

NAME = "snd-denoise"
HERE = os.path.dirname(os.path.abspath(__file__))

FS = 16000
DUR = 1.6
N = int(FS * DUR)
TT = np.arange(N) / FS
SNR_DB = 10.0
NPER, HOP = 512, 128                      # 32 ms Hann, 8 ms hop
DB_RANGE = 60.0
SEED = 7

# formant frequencies (Hz) of the vowels, Peterson and Barney (1952), men
VOWEL = {"u": [300, 870, 2240, 3300], "a": [730, 1090, 2440, 3400], "e": [530, 1840, 2480, 3500],
         "i": [270, 2290, 3010, 3700], "o": [570, 840, 2410, 3400]}
BAND = [90.0, 110.0, 160.0, 220.0]        # formant bandwidths (Hz)
SYL = [(0.10, 0.42, "u", "a"), (0.56, 0.84, "e", "e"), (0.95, 1.19, "i", "i"), (1.33, 1.55, "o", "u")]
FRIC = [(0.44, 0.545, 3800.0, 7600.0, 0.16), (1.215, 1.315, 2000.0, 6000.0, 0.12)]


def f0_of(t):
    """The pitch: a declining phrase with a rise on the first syllable."""
    return 150.0 + 55.0 * np.exp(-((t - 0.32) / 0.28) ** 2) + 14.0 * np.sin(2 * np.pi * 1.1 * t + 0.4) - 12.0 * t


def ramp(t, a, b, r):
    """1 inside [a, b], raised cosine edges r seconds long."""
    up = np.clip((t - a) / r, 0, 1)
    dn = np.clip((b - t) / r, 0, 1)
    return np.sin(0.5 * np.pi * up) ** 2 * np.sin(0.5 * np.pi * dn) ** 2


def formants_at(t):
    """The formant frequencies at time t (each syllable glides from its first
    vowel to its second) and the voiced envelope."""
    Fs = np.zeros((t.size, 4))
    env = np.zeros(t.size)
    for (a, b, v0, v1), amp in zip(SYL, [1.0, 0.85, 0.8, 0.7]):
        m = (t >= a) & (t <= b)
        s = np.clip((t[m] - a) / (b - a), 0, 1)
        g = s * s * (3 - 2 * s)
        Fs[m] = np.outer(1 - g, VOWEL[v0]) + np.outer(g, VOWEL[v1])
        env += amp * ramp(t, a, b, 0.035)
    return Fs, env


def tract(f, Fs):
    """The vocal tract's magnitude at frequency f: its formant resonances,
    each a second order resonator, normalised to 1 at 0 Hz."""
    h = np.ones_like(f)
    for i in range(4):
        F, B = Fs[:, i], BAND[i]
        h *= F * F / np.sqrt((F * F - f * f) ** 2 + (f * B) ** 2)
    return h


def speech():
    f0 = f0_of(TT)
    phase = 2 * np.pi * np.cumsum(f0) / FS
    Fs, env = formants_at(TT)
    on = env > 0
    Fs[~on] = VOWEL["a"]
    s = np.zeros(N)
    kmax = int(7800 / f0.min())
    for k in range(1, kmax + 1):
        fk = k * f0
        live = fk < 7800
        amp = np.where(live, tract(fk, Fs) / k, 0.0)
        s += amp * np.sin(k * phase)
    s *= env
    rng = np.random.default_rng(SEED)
    for a, b, lo, hi, g in FRIC:
        sos = butter(4, [lo, hi], btype="band", fs=FS, output="sos")
        w = sosfiltfilt(sos, rng.standard_normal(N))
        s += g * ramp(TT, a, b, 0.02) * w / np.abs(w).max() * np.abs(s).max()
    return s / np.abs(s).max() * 0.9, f0, Fs, env


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / FS)
    X[1:] /= np.sqrt(f[1:])
    X[f < 20] = 0
    x = np.fft.irfft(X, n)
    return x / x.std()


def spec(x):
    f, t, Z = stft(x, FS, window="hann", nperseg=NPER, noverlap=NPER - HOP)
    return f, t, Z


def png_uri(a):
    b = io.BytesIO()
    Image.fromarray(a).save(b, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def envelope(x, cols, scale):
    """min and max of x over each of `cols` columns: the waveform as drawn."""
    k = np.linspace(0, x.size, cols + 1).astype(int)
    lo = np.array([x[k[i]:k[i + 1]].min() for i in range(cols)]) / scale
    hi = np.array([x[k[i]:k[i + 1]].max() for i in range(cols)]) / scale
    return common.f32(np.stack([lo, hi], 1).ravel())


def model():
    s, f0, Fs, env = speech()
    rng = np.random.default_rng(SEED + 1)
    n = pink(N, rng)
    n *= np.sqrt(np.sum(s ** 2) / np.sum(n ** 2) / 10 ** (SNR_DB / 10))
    x = s + n
    f, t, Zx = spec(x)
    _, _, Zs = spec(s)
    _, _, Zn = spec(n)
    ref = np.abs(Zx).max()
    dbx = 20 * np.log10(np.abs(Zx) / ref + 1e-12)
    dbs = 20 * np.log10(np.abs(Zs) / ref + 1e-12)
    return dict(s=s, n=n, x=x, f0=f0, Fs=Fs, env=env, f=f, t=t, Zx=Zx, Zs=Zs, Zn=Zn, dbx=dbx, dbs=dbs)


def validate(r):
    L = []
    say = L.append
    s, n, x, f, t = r["s"], r["n"], r["x"], r["f"], r["t"]
    say("Figure 3 (nf-snd-denoise): a background noise-reduction algorithm.")
    say("Generator: tools/numfig/snd_denoise.py")
    say("")
    say("SIGNALS")
    say(f"  sampling {FS} Hz, {DUR:g} s ({N} samples)")
    say("  speech audio: harmonics k f0(t) of a gliding pitch, amplitude (1/k) times the vocal")
    say("  tract's resonances at the current formants, times the syllable envelope; fricatives are")
    say("  band-passed noise (4th order Butterworth, forward and backward)")
    say(f"    pitch f0: {r['f0'].min():.1f} to {r['f0'].max():.1f} Hz")
    for a, b, v0, v1 in SYL:
        say(f"    syllable {a:.2f} to {b:.2f} s: vowel {v0} to {v1}, formants {VOWEL[v0]} to {VOWEL[v1]} Hz")
    for a, b, lo, hi, g in FRIC:
        say(f"    fricative {a:.3f} to {b:.3f} s: band {lo:g} to {hi:g} Hz")
    say(f"    formant bandwidths {BAND} Hz")
    say("  background noise: pink (amplitude spectrum 1/sqrt(f) above 20 Hz), numpy default_rng"
        f"({SEED + 1})")
    snr = 10 * np.log10(np.sum(s ** 2) / np.sum(n ** 2))
    say(f"  audio mixing: x = speech + noise, SNR = 10 log10(sum s^2 / sum n^2) = {snr:.4f} dB")
    say(f"  visual transformation representation: STFT, Hann {NPER} samples ({NPER / FS * 1e3:g} ms), hop"
        f" {HOP} ({HOP / FS * 1e3:g} ms);")
    say(f"    {r['Zx'].shape[0]} frequencies (0 to {FS // 2} Hz, {FS / NPER:g} Hz apart) by {r['Zx'].shape[1]} frames;"
        f" |X| in dB")
    say(f"    of the mixed audio's largest value, {DB_RANGE:g} dB shown, one scale for both pictures")
    say("")
    say("CHECKS")
    lin = np.abs(r["Zx"] - r["Zs"] - r["Zn"]).max() / np.abs(r["Zx"]).max()
    say(f"  1. The transform is linear: max |X_mix - X_speech - X_noise| / max |X_mix| = {lin:.1e};")
    say("     mixing adds the signals, and their transforms add (their magnitudes do not)")
    _, xr = istft(r["Zx"], FS, window="hann", nperseg=NPER, noverlap=NPER - HOP)
    rec = np.abs(xr[:N] - x).max()
    say(f"  2. The picture keeps the signal: the inverse STFT gives the mixed audio back to"
        f" {rec:.1e} (Hann at 75 % overlap sums to a constant)")
    # 3. the harmonics sit at k f0: per voiced frame, the pitch that best explains the peaks
    Zs = np.abs(r["Zs"])
    errs = []
    for j, tj in enumerate(t):
        i0 = int(round(tj * FS))
        if i0 >= N or r["env"][i0] < 0.9:
            continue
        spec_j = Zs[:, j]
        cand = np.arange(100.0, 260.0, 0.25)
        score = [spec_j[np.clip(np.round(np.arange(1, 9) * c / (FS / NPER)).astype(int), 0, len(spec_j) - 1)].sum()
                 for c in cand]
        est = cand[int(np.argmax(score))]
        errs.append(abs(est - r["f0"][i0]) / r["f0"][i0])
    errs = np.array(errs)
    say(f"  3. The speech picture's harmonics are the synthesised pitch: in {errs.size} voiced frames the")
    say(f"     harmonic sum's best pitch is within {np.median(errs) * 100:.2f} % (median), "
        f"{errs.max() * 100:.2f} % (worst) of f0 at the frame's centre")
    # 4. formants: undo the source's 1/k and the strongest harmonics are those nearest F1 and F2
    j = int(np.argmin(np.abs(t - 1.07)))
    col = Zs[:, j]
    f0c = r["f0"][int(round(t[j] * FS))]
    k = np.arange(1, int(4000 / f0c))
    amps = np.array([col[int(round(kk * f0c / (FS / NPER)))] for kk in k]) * k
    lo_m, hi_m = k * f0c < 1000, (k * f0c > 1500) & (k * f0c < 3500)
    low = k[lo_m][np.argmax(amps[lo_m])] * f0c
    high = k[hi_m][np.argmax(amps[hi_m])] * f0c
    near = lambda F: k[np.argmin(np.abs(k * f0c - F))] * f0c
    say(f"  4. The vowel i at {t[j]:.3f} s (formants 270, 2290 Hz; f0 = {f0c:.1f} Hz): with the source's")
    say(f"     1/k undone, the strongest harmonic below 1 kHz is at {low:.0f} Hz and between 1.5 and")
    say(f"     3.5 kHz at {high:.0f} Hz: the harmonics nearest F1 and F2 are {near(270):.0f} and {near(2290):.0f} Hz")
    ff, P = welch(n, FS, nperseg=4096)
    m = (ff > 100) & (ff < 6000)
    slope = np.polyfit(np.log2(ff[m]), 10 * np.log10(P[m]), 1)[0]
    say(f"  5. The noise is pink: its power spectrum (Welch) falls {slope:.2f} dB per octave (pink: -3.01)")
    peak = r["dbx"].max()
    say(f"  6. The pictures: the mixed audio's spectrogram spans {r['dbx'].min():.0f} to {peak:.0f} dB; the speech"
        f" audio's silences are exactly zero, so its floor is white")
    say("")
    say("THE MODEL BOX")
    say("  His caption: the VAE, trained on pairs made this way, estimates the clean spectrogram.")
    say("  The picture on its right is what his lower path computes, the speech audio's own")
    say("  spectrogram: the target the network learns to reproduce. No trained network is claimed:")
    say("  the VAE is a block (encoder, latent z, decoder) with no output of its own. A Wiener mask")
    say("  or spectral subtraction would be a different algorithm from the one his caption names;")
    say("  drawing its output under the VAE's name would say something that is not true.")
    say("")
    say("DISPLAY")
    say(f"  a cursor sweeps the {DUR:g} s in real time; the waveforms are drawn up to it (each column's")
    say("  minimum and maximum), and each spectrogram column appears when its window's centre")
    say("  has passed; then the picture rests and the sweep starts again.")
    return "\n".join(L) + "\n"


JS = r"""
const D = DATA;
const POSTER_T = D.poster;
const lab = t0 => settle(t0, .28);
const T0 = D.t0, SW = D.dur, HOLD = D.hold, RST = .35, PER = SW + HOLD + RST;
function cursor() {                         // seconds of audio drawn so far, and the picture's fade
  if (t < T0) return { u: 0, a: 1 };
  const p = (t - T0) % PER;
  if (p < SW) return { u: p, a: 1 };
  if (p < SW + HOLD) return { u: SW, a: 1 };
  return { u: SW, a: 1 - easeInOut(clamp((p - SW - HOLD) / RST)) };
}

/* ------------------------------------------------------------ places */
const WN = { x: 22, y: 60, w: 138, h: 46 }, WS = { x: 22, y: 172, w: 138, h: 46 };
const MXB = { x: 186, y: 112, w: 86, h: 52 };
const WM = { x: 298, y: 115, w: 136, h: 46 };
const VT1 = { x: 468, y: 108, w: 124, h: 60 };
const SPM = { x: 440, y: 232, w: 180, h: 190 }, SPC = { x: 770, y: 232, w: 180, h: 190 };
const VAE = { x: 648, y: 277, w: 96, h: 100 };
const VT2 = { x: 292, y: 496, w: 124, h: 60 };
const BOTY = VT2.y + VT2.h / 2;

/* ------------------------------------------------------------ helpers */
function box(b, words, p, t0) {
  if (p <= 0) return;
  ctx.save(); ctx.globalAlpha *= clamp(p * 1.5); ctx.fillStyle = C.steel; ctx.fillRect(b.x, b.y, b.w, b.h); ctx.restore();
  line([[b.x, b.y], [b.x + b.w, b.y], [b.x + b.w, b.y + b.h], [b.x, b.y + b.h], [b.x, b.y]], { width: 1.5, progress: p });
  const a = lab(t0), n = words.length, lh = 17;
  words.forEach((w, i) => text(w, b.x + b.w / 2, b.y + b.h / 2 + (i - (n - 1) / 2) * lh + 5, { size: 15, align: 'center', alpha: a }));
}
function wave(W, env, u, a, t0) {
  const n = env.length / 2, mid = W.y + W.h / 2;
  line([[W.x, mid], [W.x + W.w, mid]], { color: C.rule, width: 1, alpha: seg(t0, .3) });
  const k = Math.floor(n * clamp(u / SW));
  if (k < 1 || a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = C.navy; ctx.lineWidth = W.w / n * 1.05;
  ctx.beginPath();
  for (let i = 0; i < k; i++) {
    const x = W.x + (i + .5) * W.w / n;
    ctx.moveTo(x, mid - env[2 * i + 1] * W.h / 2); ctx.lineTo(x, mid - env[2 * i] * W.h / 2);
  }
  ctx.stroke(); ctx.restore();
  if (u < SW) line([[W.x + W.w * u / SW, W.y - 2], [W.x + W.w * u / SW, W.y + W.h + 2]], { color: C.accent, width: 1.2, alpha: a });
}
function spectro(P, cvs, u, a, t0) {
  const ap = seg(t0, .35);
  if (cvs && a > 0) {
    const cols = D.frames, done = clamp(Math.floor((u - D.tf0) / D.hop) + 1, 0, cols);
    if (done > 0) {
      ctx.save(); ctx.beginPath(); ctx.rect(P.x, P.y, P.w * done / cols, P.h); ctx.clip();
      ctx.globalAlpha *= a; ctx.imageSmoothingEnabled = true; ctx.drawImage(cvs, P.x, P.y, P.w, P.h); ctx.restore();
    }
  }
  if (u < SW && a > 0 && u > 0) line([[P.x + P.w * u / SW, P.y], [P.x + P.w * u / SW, P.y + P.h]], { color: C.accent, width: 1.2, alpha: a });
  return ap;
}
function spAxes(P, left, t0) {
  const ap = seg(t0, .35);
  axes({ x: P.x, y: P.y, w: P.w, h: P.h, xlim: [0, SW], ylim: [0, 8], xticks: [0, .5, 1, 1.5], yticks: [0, 2, 4, 6, 8],
         progress: ap, yfmt: left ? (v => fmt(v)) : (() => ''), xlabel: left ? 't\\ (\\rm{s})' : '' });
  if (!left) {
    for (const v of [0, 2, 4, 6, 8]) math(fmt(v), P.x + P.w + 8, P.y + P.h - v / 8 * P.h + 5, { size: 15, alpha: clamp(ap * 1.4) });
    math('f\\ (\\rm{kHz})', P.x + P.w + 44, P.y + P.h / 2, { size: 17, align: 'center', rot: -Math.PI / 2, alpha: clamp(ap * 1.4) });
  } else math('f\\ (\\rm{kHz})', P.x - 40, P.y + P.h / 2, { size: 17, align: 'center', rot: -Math.PI / 2, alpha: clamp(ap * 1.4) });
}
function arr(pts, p, o = {}) {                  // a polyline ending in an arrow tip
  if (p <= 0) return;
  const n = pts.length;
  if (n > 2) line(pts.slice(0, n - 1), { width: 1.5, progress: p, ...o });
  if (p >= 1) { const a = pts[n - 2], b = pts[n - 1]; arrow(a[0], a[1], b[0], b[1], { width: 1.5, head: 9, ...o }); }
}

/* ------------------------------------------------------------ the pictures, coloured through SEQ */
const IMGS = {};
function paint(name) {
  const img = RAW[name], c = document.createElement('canvas'); c.width = img.width; c.height = img.height;
  const g = c.getContext('2d'); g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height);
  for (let i = 0; i < d.data.length; i += 4) { const v = d.data[i] * 3; d.data[i] = SEQ[v]; d.data[i + 1] = SEQ[v + 1]; d.data[i + 2] = SEQ[v + 2]; d.data[i + 3] = 255; }
  g.putImageData(d, 0, 0); IMGS[name] = c;
}
const RAW = { mix: new Image(), clean: new Image() };
RAW.mix.src = D.img_mix; RAW.clean.src = D.img_clean;
const EN = b64f32(D.env_n), ES = b64f32(D.env_s), EM = b64f32(D.env_m);

/* ------------------------------------------------------------ the VAE: a block, no output of its own */
function vae(p, t0) {
  const a = lab(t0), cy = VAE.y + VAE.h / 2, zw = 14, gap = 7, tw = (VAE.w - zw - 2 * gap) / 2, nk = 20;
  const enc = [[VAE.x, VAE.y], [VAE.x + tw, cy - nk], [VAE.x + tw, cy + nk], [VAE.x, VAE.y + VAE.h]];
  const dec = [[VAE.x + VAE.w, VAE.y], [VAE.x + VAE.w - tw, cy - nk], [VAE.x + VAE.w - tw, cy + nk], [VAE.x + VAE.w, VAE.y + VAE.h]];
  for (const q of [enc, dec]) {
    if (p >= 1) { ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = C.steel; ctx.beginPath(); ctx.moveTo(q[0][0], q[0][1]); for (const r of q.slice(1)) ctx.lineTo(r[0], r[1]); ctx.closePath(); ctx.fill(); ctx.restore(); }
    line(q.concat([q[0]]), { width: 1.5, progress: p });
  }
  const zx = VAE.x + VAE.w / 2;
  line([[zx - zw / 2, cy - 14], [zx + zw / 2, cy - 14], [zx + zw / 2, cy + 14], [zx - zw / 2, cy + 14], [zx - zw / 2, cy - 14]], { width: 1.3, progress: p });
  line([[VAE.x + tw, cy], [zx - zw / 2, cy]], { width: 1.2, alpha: a });
  line([[zx + zw / 2, cy], [VAE.x + VAE.w - tw, cy]], { width: 1.2, alpha: a });
  math('z', zx, cy + 6, { size: 16, align: 'center', alpha: a });
  text('encoder', VAE.x + tw / 2, VAE.y + VAE.h + 20, { size: 14, color: C.muted, align: 'center', alpha: a });
  text('decoder', VAE.x + VAE.w - tw / 2, VAE.y + VAE.h + 20, { size: 14, color: C.muted, align: 'center', alpha: a });
}

function draw() {
  const c = cursor(), u = c.u, fa = c.a;
  // sources, mixing, mixed audio
  const la = lab(.05);
  text('Background noise', WN.x, WN.y - 12, { size: 16, alpha: la });
  text('Speech audio', WS.x, WS.y - 12, { size: 16, alpha: lab(.08) });
  wave(WN, EN, u, fa, .05);
  wave(WS, ES, u, fa, .08);
  box(MXB, ['Audio', 'mixing'], seg(.1, .35), .15);
  arr([[WN.x + WN.w + 6, WN.y + WN.h / 2], [MXB.x - 4, MXB.y + 14]], seg(.15, .3));
  arr([[WS.x + WS.w + 6, WS.y + WS.h / 2], [MXB.x - 4, MXB.y + MXB.h - 14]], seg(.17, .3));
  arr([[MXB.x + MXB.w + 4, MXB.y + MXB.h / 2], [WM.x - 6, MXB.y + MXB.h / 2]], seg(.22, .3));
  text('Mixed audio', WM.x, WM.y - 12, { size: 16, alpha: lab(.2) });
  wave(WM, EM, u, fa, .2);
  arr([[WM.x + WM.w + 6, WM.y + WM.h / 2], [VT1.x - 4, WM.y + WM.h / 2]], seg(.28, .3));
  box(VT1, ['Visual', 'transformation', 'representation'], seg(.25, .35), .3);
  arr([[VT1.x + VT1.w / 2, VT1.y + VT1.h + 4], [VT1.x + VT1.w / 2, SPM.y - 6]], seg(.32, .3));
  // the pictures
  spectro(SPM, IMGS.mix, u, fa, .3);
  spAxes(SPM, true, .3);
  const nm = lab(.4);
  ['Visual representation', 'mixed audio'].forEach((w, i) => text(w, SPM.x + SPM.w / 2, SPM.y + SPM.h + 66 + i * 19, { size: 16, align: 'center', alpha: nm }));
  arr([[SPM.x + SPM.w + 6, VAE.y + VAE.h / 2], [VAE.x - 4, VAE.y + VAE.h / 2]], seg(.38, .3));
  vae(seg(.34, .4), .42);
  ['Variational', 'Autoencoder'].forEach((w, i) => text(w, VAE.x + VAE.w / 2, VAE.y - 34 + i * 19, { size: 16, align: 'center', alpha: lab(.42) }));
  arr([[VAE.x + VAE.w + 4, VAE.y + VAE.h / 2], [SPC.x - 6, VAE.y + VAE.h / 2]], seg(.44, .3));
  spectro(SPC, IMGS.clean, u, fa, .4);
  spAxes(SPC, false, .4);
  ['Visual representation', 'speech audio'].forEach((w, i) => text(w, SPC.x + SPC.w / 2, SPC.y - 34 + i * 19, { size: 16, align: 'center', alpha: lab(.46) }));
  // the speech audio's own path: the target
  const bx = WS.x + 50;
  arr([[bx, WS.y + WS.h + 6], [bx, BOTY], [VT2.x - 4, BOTY]], seg(.3, .4));
  box(VT2, ['Visual', 'transformation', 'representation'], seg(.35, .35), .4);
  arr([[VT2.x + VT2.w + 4, BOTY], [D.upx, BOTY], [D.upx, SPC.y + SPC.h + 6]], seg(.42, .45));
  // the colour scale
  colorbar(seg(.5, .3));
  math(D.params, 22, H - 12, { size: 14, color: C.muted, alpha: seg(.55, .3) });
}
function colorbar(a) {
  if (a <= 0) return;
  const x0 = VAE.x + 4, w = VAE.w - 8, y0 = SPM.y + SPM.h + 26, h = 8;
  if (!colorbar.c) { const c = document.createElement('canvas'); c.width = 256; c.height = 1; const g = c.getContext('2d'), d = g.createImageData(256, 1);
    for (let i = 0; i < 256; i++) d.data.set([SEQ[3 * i], SEQ[3 * i + 1], SEQ[3 * i + 2], 255], 4 * i); g.putImageData(d, 0, 0); colorbar.c = c; }
  ctx.save(); ctx.globalAlpha *= a; ctx.imageSmoothingEnabled = true; ctx.drawImage(colorbar.c, x0, y0, w, h); ctx.restore();
  line([[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]], { width: .8, alpha: a });
  for (const v of [-60, -30, 0]) {
    const x = x0 + (v + D.dbr) / D.dbr * w;
    line([[x, y0 + h], [x, y0 + h + 3]], { width: .8, alpha: a });
    math(fmt(v), x, y0 + h + 18, { size: 14, align: 'center', alpha: a });
  }
  text('dB', x0 + w + 6, y0 + h, { size: 14, alpha: a });
}
Promise.all([RAW.mix.decode(), RAW.clean.decode()]).then(() => { paint('mix'); paint('clean'); }).catch(() => {}).finally(() => boot());
"""


def page_data(r):
    s, n, x = r["s"], r["n"], r["x"]
    scale = np.abs(x).max()
    cols = 146 * 2
    img = {}
    for key in ("dbx", "dbs"):
        db = np.clip((r[key] + DB_RANGE) / DB_RANGE, 0, 1)
        img[key] = np.round(db[::-1] * 255).astype(np.uint8)       # high frequencies up
    tf = r["t"]
    return {
        "poster": 0.5 + DUR + 0.4, "t0": 0.5, "dur": DUR, "hold": 1.8,
        "env_n": envelope(n, cols, scale), "env_s": envelope(s, cols, scale), "env_m": envelope(x, cols, scale),
        "img_mix": png_uri(img["dbx"]), "img_clean": png_uri(img["dbs"]),
        "frames": int(tf.size), "tf0": float(tf[0]), "hop": float(tf[1] - tf[0]), "dbr": DB_RANGE,
        "upx": 770 + 180 * 0.75 / DUR,               # between the time labels 0.5 and 1
        "params": (r"\rm{synthetic speech, }f_{0} = %d\rm{ to }%d\,\rm{Hz, and pink noise, SNR 10 dB;"
                   r"\ \ STFT: Hann 32 ms, hop 8 ms, 16 kHz;\ \ real time}"
                   % (int(round(r["f0"].min())), int(round(r["f0"].max())))),
    }


def main():
    r = model()
    txt = validate(r)
    with open(os.path.join(HERE, "snd_denoise.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    data = page_data(r)
    title = "Figure 3: A background noise-reduction algorithm"
    aria = ("A noise-reduction pipeline. Background noise and speech audio are mixed; the mixed audio's "
            "spectrogram, its visual representation, goes into a variational autoencoder, which learns to "
            "estimate the speech audio's own spectrogram, computed from the speech along the lower path.")
    common.build_html(NAME, title, aria, 1000, 600, data, JS)
    print("still:", common.still(NAME))
    snd_common.append(os.path.join(HERE, "snd_denoise.check.txt"), snd_common.loop_overlaps(NAME, data["t0"] + data["dur"] + data["hold"] + 0.35 + 0.4))
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.3, 0.8, 1.2, 1.7, 2.3, 3.2, 4.2]))


if __name__ == "__main__":
    main()
