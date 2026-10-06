"""Figure 12 of the signal processing document: one signal at two sensors,
recovered by generalized cross-correlation and a Wiener filter (his "Delayed
signal recovery, method 1: GCC and Wiener filter").

The model and the method are sp_delay_lib's (his, line for line): one signal
reaching two sensors 48 ms apart, each record with its own white Gaussian
noise; the delay from the peak of the coherence weighted cross-correlation,
to the nearest sample (2 ms); the second record advanced by it, the two
averaged and Wiener filtered. Every choice the page offers is computed here:
3 signals x 11 SNRs (-30 to 20 dB in 5 dB steps), one noise draw (seed 25,
sp_delay_lib.SEED), so the SNR slider scales the same noise.

The page steps through his stages by itself (signal, noise, delay, align,
Wiener filter, estimate), each a pure function of the clock; a stage chip
jumps to its stage. ?kind=, ?snr= and ?stage= choose a state (for the overlap
check of every state).

Run: python tools/numfig/sp_delay_gcc.py [--look]  (writes the page, the still
and the check file; prints the key numbers). A restyle runs this again (a few
seconds): the script lives in sp_delay_lib.JS, which reskin.py does not track.
"""
import os
import sys

import numpy as np

import common
import sp_delay_lib as L

NAME = "sp-delay-gcc"
H = 700
JS = L.JS
TITLE = "Figure 12: One signal at two sensors, recovered by generalized cross-correlation and a Wiener filter"
ARIA = ("Two sensor records of one signal, the second 48 ms later, each buried in its own noise. The figure steps "
        "through the method by itself: it adds the noise, finds the delay at the peak of a coherence weighted "
        "cross-correlation, aligns the records, averages them, Wiener filters the average, and compares the "
        "estimate with the true signal. Chips choose the stage and the signal, a slider the SNR.")
PARAMS = (r"f_{\rm{s}} = 500\ \rm{Hz, 2,048 samples;  }\tau\ = 48\ \rm{ms = 24 samples;  independent white noise;  "
          r"Welch: Hann, 256 samples, 50% overlap;  signal RMS = 1}")


def build():
    noise, codes = L.stored_noise()
    states = L.all_states(1, noise)
    data = L.page_data(1, states, codes)
    data["def"] = {"snr": -10, "m": 1}
    data["params"] = PARAMS
    path = common.build_html(NAME, TITLE, ARIA, 1000, H, data, JS, digits=12)
    print(path, os.path.getsize(path), "bytes")
    return noise, codes, states, path


def at(states, kind, snr):
    return next(i for i, (k, r) in enumerate(states) if k == (kind, snr, 1))


def validate(noise, codes, states, path, full_sweep=False):
    out = []
    say = out.append
    i0 = at(states, "impacts", -10)
    r0 = states[i0][1]
    seed_tab, q, seed, frac = L.seed_rule()
    say("Figure 12 (nf-sp-delay-gcc): one signal at two sensors, generalized cross-correlation and a Wiener filter")
    say("check of tools/numfig/sp_delay_gcc.py and sp_delay_lib.py (the model shared with Figure 13)")
    say("")
    say("MODEL (his page, 'Delayed signal recovery, method 1: GCC and Wiener filter')")
    say(f"  x1(t) = s(t) + n1(t), x2(t) = s(t - tau) + n2(t), tau = {L.TAU * 1e3:g} ms = {L.D_TRUE} samples at fs = {L.FS:g} Hz,")
    say(f"  N = {L.N} samples ({L.N / L.FS:.3f} s). n1, n2 white Gaussian, independent; SNR = signal power / noise power")
    say("  of one record, sigma = 10^(-SNR/20) on the standardized signal (mean 0, RMS 1 over the record).")
    say("  Signals (his): impacts = sum of 8 impacts (t0, a) = " + ", ".join(f"({t0:g}, {a0:g})" for t0, a0 in L.IMPACTS) + ",")
    say(f"  each a exp(-zeta w_n u) sin(w_d u), f_n = {L.FN:g} Hz, zeta = {L.ZETA:g}, divided by 0.27; harmonic =")
    say("  (1 + 0.5 sin 2 pi 0.4 t)(sin 2 pi 3 t + 0.45 sin(2 pi 6 t + 0.7) + 0.25 sin(2 pi 9 t + 1.3)), the same")
    say("  formula as his blind source separation pages (their impact trains differ, so the delay pages' is kept);")
    say("  both = impacts + 0.6 harmonic. The delayed copy is the formula at t - tau, scaled as s: a true delay.")
    say("  Method (his, line for line): Welch spectra (periodic Hann, 256 samples, 50% overlap, K = 15 segments);")
    say("  GCC = IFFT[W conj(A) B] with 4,096-point zero padded FFTs of the two records and the weight")
    say("  W = g2 / (1 - g2), g2 = |S12|^2 / (S11 S22) clipped at 0.99, linear between Welch bins, read over")
    say("  lags -125 .. 125 samples; delay = the lag of its largest value (whole samples, 2 ms); x2 advanced by it")
    say("  (FFT phase ramp, circular), averaged with x1; Wiener gain G = max(0, Re S12' - 2 sqrt(S11' S22'/(2K)))")
    say("  / S_avg (at most 1) from the aligned records' spectra, applied to the average; the output standardized.")
    say(f"  Every choice is computed here: 3 signals x {len(L.SNRS)} SNRs ({L.SNRS[0]} to {L.SNRS[-1]} dB, 5 dB steps), one noise")
    say(f"  draw scaled by sigma (seed {L.SEED}: numpy default_rng, SeedSequence spawned per sensor; shot 1 of Figure 13).")
    say("")
    say("THE NOISE DRAW SHOWN")
    say(f"  Rule: the first seed whose outcomes at both default settings fall in the middle half of {len(seed_tab)} draws")
    say("  (seeds 1 ..): Figure 12 (impacts, -10 dB) integer delay error at most one sample and correlation within")
    say(f"  the quartiles [{q[2][0]:.3f}, {q[2][2]:.3f}]; Figure 13 (impacts, -20 dB, 64 shots) refined delay error within")
    say(f"  [{q[3][0]:+.3f}, {q[3][2]:+.3f}] samples and correlation within [{q[4][0]:.3f}, {q[4][2]:.3f}]; its single shot at -20 dB")
    say(f"  not within one sample (as {100 * np.mean(np.abs(seed_tab[:, 5]) >= 1):.1f}% of draws). {100 * frac:.0f}% of seeds pass; the first is {seed}"
        f" (SEED = {L.SEED}).")
    hist = {int(k): int(v) for k, v in zip(*np.unique(seed_tab[:, 1].astype(int), return_counts=True))}
    say(f"  Integer delay error at -10 dB over the {len(seed_tab)} draws (samples: count): {hist}; mean {seed_tab[:, 1].mean():+.3f}.")
    say("")
    say("GRID")
    s_imp, _ = L.signals("impacts")
    Pf = np.abs(np.fft.rfft(s_imp)) ** 2
    f = np.fft.rfftfreq(L.N, 1 / L.FS)
    say(f"  Sampling: the impact train keeps {Pf[f > 100].sum() / Pf.sum():.1e} of its energy above 100 Hz and"
        f" {Pf[f > 40].sum() / Pf.sum():.1e} above 40 Hz")
    say(f"  (fs/2 = 250 Hz; the plots stop at 40 Hz); the last impact (3.55 s) has decayed to"
        f" {np.exp(-L.ZETA * L.WN * (L.N / L.FS - 3.55)):.3f} by the record's end.")
    say("  Welch bins 1.95 Hz apart: the mode's half-power band, 2 zeta f_n = 1.76 Hz, spans about one bin.")
    a_, b_ = r0["a"], r0["b"]
    A = np.fft.fft(a_, L.NFFT_GCC)
    B = np.fft.fft(b_, L.NFFT_GCC)
    rr = np.fft.ifft(np.conj(A) * B).real
    lags = np.arange(-L.MAXLAG, L.MAXLAG + 1)
    direct = np.correlate(b_, a_, "full")[L.N - 1 + lags]
    say(f"  GCC: 4,096-point FFTs hold the whole linear correlation (2N - 1 = {2 * L.N - 1} lags); with W = 1 the FFT")
    say(f"  correlation equals numpy.correlate over lags -125 .. 125 within {np.abs(rr[lags % L.NFFT_GCC] - direct).max() / np.abs(direct).max():.1e} (relative).")
    say(f"  Storage: noise as int16 times 2^-k (largest rounding {max(2.0 ** -k for cd in codes.values() for _, k in cd) / 2:.1e} of unit noise), GCC curves as int8")
    say("  (display), Wiener gains as float32; delays to 12 digits; correlations and SNRs as computed.")
    say("")
    say("AT THE DEFAULT SETTING (impacts, -10 dB)")
    say(f"  measured record SNRs {r0['rec_snr'][0]:.2f} and {r0['rec_snr'][1]:.2f} dB; GCC peak at {r0['di']} samples:"
        f" tau_hat = {r0['d'] * 1e3 / L.FS:.0f} ms (true 48 ms, one sample off)")
    say(f"  estimate: correlation with s(t) {r0['rho'][0]:.4f}, delayed copy with s(t - tau) {r0['rho'][1]:.4f};"
        f" SNR of the estimate {L.snr_db(r0['rho'][0]):.2f} dB")
    say(f"  (rho^2/(1 - rho^2)): {L.snr_db(r0['rho'][0]) - r0['rec_snr'][0]:.2f} dB above sensor 1's record.")
    for kind in L.KINDS:
        row = []
        for snr in L.SNRS:
            r = states[at(states, kind, snr)][1]
            row.append(f"{snr:+d}: {r['d'] * 2:.0f} ms/{r['rho'][0]:.2f}")
        say(f"  {kind:8s} " + "  ".join(row[:6]))
        say(f"  {'':8s} " + "  ".join(row[6:]))
    say("")
    say("VALIDATION")
    say(f"  1. {L.HIS_PAGES}.")
    e_w, K = L.welch_vs_scipy(r0["a"], r0["b"])
    say(f"  2. Welch cross spectrum against scipy.signal.csd (Hann 256, overlap 128, density scaling undone):"
        f" {e_w:.1e} relative; K = {K} segments.")
    say("  3. The delay against the Cramer-Rao bound (Knapp and Carter 1976, closed form,")
    say("     var >= [2T int (2 pi f)^2 g2/(1 - g2) df]^-1 with the record's own spectrum): RMS error of the")
    say("     peak refined by the parabola, 300 noise draws each (seeds 10,000 ..):")
    for kind in ("impacts", "both", "harmonic"):
        parts = []
        for snr in (0, 10, 20):
            d = L.mc_delays(kind, snr, 300, True)
            ok = np.abs(d - L.D_TRUE) < 5
            rms = np.sqrt(np.mean((d[ok] - L.D_TRUE) ** 2)) * 1e3 / L.FS
            cr = L.crlb_ms(kind, snr)
            parts.append(f"{snr:+d} dB {rms:.3f} ms vs {cr:.3f} ({rms / cr:.2f}x)")
        say(f"     {kind:8s} " + "; ".join(parts))
    say("     Close to the bound for the impacts (the 11 Hz mode); the harmonic lines (3, 6, 9 Hz) sit 30 to 50% above.")
    rho_i, G_i = L.ideal_wiener(r0, "impacts", -10, 1)
    say(f"  4. Wiener filter against the ideal one (the true signal spectrum and noise level, G = S / (S + N/2)):")
    say(f"     at the default, correlation {r0['rho'][0]:.4f} against {rho_i:.4f}. The estimated gain stays below")
    say(f"     1 - 2/sqrt(2K) = {1 - 2 / np.sqrt(2 * 15):.4f} (its threshold grows with the signal): largest over all states"
        f" {max(r['G'].max() for _, r in states):.4f}.")
    say("     The output is standardized, so only the gain's shape over frequency matters.")
    say("  5. Integer delay over 400 noise draws per point (seeds 10,000 ..), share exactly right / within one sample:")
    for kind in L.KINDS:
        parts = []
        for snr in (-20, -15, -10, -5, 0, 5):
            d = L.mc_delays(kind, snr, 400, False)
            parts.append(f"{snr:+d} dB {np.mean(d == L.D_TRUE):.2f}/{np.mean(np.abs(d - L.D_TRUE) <= 1):.2f}")
        say(f"     {kind:8s} " + "  ".join(parts))
    idx = [i0, at(states, "harmonic", -25), at(states, "both", 5), at(states, "impacts", 20)]
    e16, eex, clock = L.page_vs_python(NAME, states, idx)
    say(f"  6. The page rebuilds every record from the stored noise and the signal formulas, and the aligned record,")
    say(f"     average, estimate and delayed copy with his FFT steps from the delay and gain computed here: against")
    say(f"     numpy at 4 states, within {e16:.1e} (with the float32 gain the page holds; {eex:.1e} from the exact gain).")
    count, faults = L.sweep(NAME, full=full_sweep)
    say("")
    say("DISPLAY")
    say("  Stages (his), each a pure function of the clock: " + ", ".join(f"{n} {s0:.1f} s" for n, s0 in zip(clock["names"], clock["START"]))
        + f"; the return to the clean signal at {clock['END']:.1f} s, period {clock['PERIOD']:.1f} s;")
    say(f"  poster at t = {clock['POSTER_T']:.1f} s (the estimate stage complete). Intro: axes and the clean signal drawn by")
    say("  0.7 s, labels and controls by 0.9 s; the first stage change starts at 2.0 s.")
    say(f"  Overlap check (engine ?overlap): {count} frames ({'every state at the middle and end of every stage and the return' if full_sweep else 'every state at the poster'},")
    say(f"  and every stage of the default state live): {len(faults)} with a collision.")
    say(f"  Page size {os.path.getsize(path):,} bytes.")
    txt = "\n".join(out) + "\n"
    with open(os.path.join(common.HERE, "sp_delay_gcc.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(txt)
    print(txt)
    if faults:
        print("FAULTS:", faults[:10])
    return faults


if __name__ == "__main__":
    noise, codes, states, path = build()
    png = common.still(NAME)
    print("still:", png)
    validate(noise, codes, states, path, full_sweep="--sweep" in sys.argv)
    if "--look" in sys.argv:
        print(common.frames(NAME, [0.5, 1.0, 3.0, 8.0, 13.0, 19.0, 25.0, 29.0, 32.0]))
