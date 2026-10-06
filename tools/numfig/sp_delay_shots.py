"""Figure 13 of the signal processing document: one signal at two sensors,
recovered after averaging repeated shots (his "Delayed signal recovery,
method 2: shot averaging, GCC and Wiener filter").

The model and the method are sp_delay_lib's, as in Figure 12, with two
additions from his second page: the excitation is fired M times and each
sensor's records are averaged (M = 1, 16, 64, 256 or 1,024), and the delay
read at the GCC peak is refined below one sample by a parabola through the
peak and its two neighbours. The shots are simulated, not scaled: every shot
draws new noise (sp_delay_lib.shot_noise, seed 25), the average of the first
M is the record, and M = 1 is Figure 12's record. Every choice the page offers
is computed here: 3 signals x 11 SNRs x 5 numbers of shots.

The page steps through his seven stages by itself; a stage chip jumps to its
stage. ?kind=, ?snr=, ?shots= and ?stage= choose a state (for the overlap
check of every state).

Run: python tools/numfig/sp_delay_shots.py [--look]  (writes the page, the
still and the check file; prints the key numbers). A restyle runs this again
(a few seconds): the script lives in sp_delay_lib.JS.
"""
import os
import sys

import numpy as np

import common
import sp_delay_lib as L

NAME = "sp-delay-shots"
H = 752
JS = L.JS
TITLE = "Figure 13: One signal at two sensors, recovered after averaging repeated shots"
ARIA = ("Two sensor records of one signal, the second 48 ms later, buried in heavy noise. The figure steps through "
        "the method by itself: it averages repeated shots, which lowers the noise by 10 log10 M dB, finds the "
        "delay at the peak of a coherence weighted cross-correlation refined below one sample, aligns, averages "
        "and Wiener filters the records, and compares the estimate with the true signal. A table gives the gain, "
        "the delay and the correlation for every number of shots; chips choose the stage, the signal and the "
        "number of shots, a slider the SNR of one shot.")
PARAMS = (r"f_{\rm{s}} = 500\ \rm{Hz, 2,048 samples;  }\tau\ = 48\ \rm{ms = 24 samples;  new noise in every shot;  "
          r"Welch: Hann, 256 samples, 50% overlap;  signal RMS = 1}")


def build():
    noise, codes = L.stored_noise()
    states = L.all_states(2, noise)
    data = L.page_data(2, states, codes)
    data["def"] = {"snr": -20, "m": 64}
    data["params"] = PARAMS
    path = common.build_html(NAME, TITLE, ARIA, 1000, H, data, JS, digits=12)
    print(path, os.path.getsize(path), "bytes")
    return noise, codes, states, path


def at(states, kind, snr, m):
    return next(i for i, (k, r) in enumerate(states) if k == (kind, snr, m))


def validate(noise, codes, states, path, full_sweep=False):
    out = []
    say = out.append
    i0 = at(states, "impacts", -20, 64)
    r0 = states[i0][1]
    say("Figure 13 (nf-sp-delay-shots): one signal at two sensors, recovered after averaging repeated shots")
    say("check of tools/numfig/sp_delay_shots.py and sp_delay_lib.py (the model shared with Figure 12)")
    say("")
    say("MODEL (his page, 'Delayed signal recovery, method 2: shot averaging, GCC and Wiener filter')")
    say(f"  As Figure 12 (sp_delay_gcc.check.txt): one signal, tau = {L.TAU * 1e3:g} ms = {L.D_TRUE} samples at fs = {L.FS:g} Hz, N = {L.N},")
    say("  his three signals, his method line for line. His two additions:")
    say("  - shots: the excitation fired M times, the signal repeated exactly, new white Gaussian noise in every")
    say("    shot, the records averaged. His page scales one noise draw by 1/sqrt(M); here the shots are drawn:")
    say(f"    each sensor's own generator (seed {L.SEED}, numpy default_rng, SeedSequence spawned per sensor) gives")
    say(f"    shot after shot, {L.SHOTS[-1]} of them, and the record of M shots is the average of the first M (nested:")
    say("    the 64-shot average holds the 16-shot one; M = 1 is Figure 12's record).")
    say("  - the delay refined below one sample: d = i + (y0 - y2) / (2 (y0 - 2 y1 + y2)), at most half a sample,")
    say("    through the GCC peak y1 at lag i and its neighbours; the record advanced by the fractional d.")
    say(f"  Every choice is computed here: 3 signals x {len(L.SNRS)} SNRs of one shot x {len(L.SHOTS)} numbers of shots.")
    say(f"  The noise draw: seed {L.SEED}, by the rule in sp_delay_gcc.check.txt (typical at both default settings).")
    say("")
    say("AT THE DEFAULT SETTING (impacts, -20 dB per shot, 64 shots)")
    say(f"  record SNRs {r0['rec_snr'][0]:.2f} and {r0['rec_snr'][1]:.2f} dB; GCC peak at {r0['di']} samples, the parabola"
        f" {r0['d'] - r0['di']:+.4f}: tau_hat = {r0['d'] * 1e3 / L.FS:.3f} ms")
    say(f"  estimate: correlation {r0['rho'][0]:.4f} (delayed copy {r0['rho'][1]:.4f}); SNR of the estimate"
        f" {L.snr_db(r0['rho'][0]):.2f} dB, {L.snr_db(r0['rho'][0]) - r0['rec_snr'][0]:.2f} dB above the averaged record")
    say(f"  and {L.snr_db(r0['rho'][0]) + 20:.2f} dB above one shot.")
    say("  Every number of shots (impacts, -20 dB):")
    say("      M     gain sensor 1, 2 (dB)   10 log10 M   tau_hat (ms)   rho")
    for m in L.SHOTS:
        r = states[at(states, "impacts", -20, m)][1]
        r1 = states[at(states, "impacts", -20, 1)][1]
        g = [r["rec_snr"][c] - r1["rec_snr"][c] for c in (0, 1)]
        say(f"  {m:5d}     {g[0]:6.2f}  {g[1]:6.2f}            {10 * np.log10(m):6.2f}     {r['d'] * 2:9.3f}     {r['rho'][0]:.4f}")
    for kind in L.KINDS:
        say(f"  {kind}: from which M on the delay stays within one sample (2 ms) of 48 ms, per SNR of one shot:")
        row = []
        for snr in L.SNRS:
            ds = [states[at(states, kind, snr, m)][1]["d"] for m in L.SHOTS]
            frm = len(L.SHOTS)
            for q in range(len(L.SHOTS) - 1, -1, -1):
                if abs(ds[q] - L.D_TRUE) < 1:
                    frm = q
                else:
                    break
            row.append(f"{snr:+d}: " + ("never" if frm == len(L.SHOTS) else f"M >= {L.SHOTS[frm]}"))
        say("    " + ", ".join(row[:6]))
        say("    " + ", ".join(row[6:]))
    say("")
    say("VALIDATION")
    say("  1. Averaging against 10 log10 M (closed form: M independent noise records averaged keep the signal and")
    say("     divide the noise power by M). This draw, measured on the stored records, above.")
    mc_snrs = (-30, -25, -20, -15, -10)
    dn, gn = L.mc_nested("impacts", mc_snrs, 200)
    gm = gn.mean(axis=(0, 1))
    gs = gn.std(axis=(0, 1))
    say("     Over 200 independent shot sequences (seeds 20,000 ..), both sensors, mean (standard deviation) in dB:")
    say("     " + "; ".join(f"M = {m}: {gm[q]:.3f} ({gs[q]:.3f}) vs {10 * np.log10(m):.3f}" for q, m in enumerate(L.SHOTS) if m > 1))
    say(f"     (the scatter of one draw: a 2,048-sample noise power has a relative standard deviation"
        f" sqrt(2/N) = {np.sqrt(2 / L.N):.3f}).")
    say("  2. The delay locks in: share of the 200 sequences within one sample of 48 ms (impacts):")
    for i, snr in enumerate(mc_snrs):
        within = np.mean(np.abs(dn[:, i, :] - L.D_TRUE) < 1, axis=0)
        say(f"     {snr:+d} dB per shot: " + ", ".join(f"M = {m} {within[q]:.2f}" for q, m in enumerate(L.SHOTS)))
    say("  3. The refined delay against the Cramer-Rao bound (Knapp and Carter 1976, closed form, as in Figure 12;")
    say("     the averaged noise has power sigma^2 / M), the same 200 sequences, RMS error of those within 5 samples:")
    for snr in (-20, -10):
        i = mc_snrs.index(snr)
        parts = []
        for q, m in enumerate(L.SHOTS):
            if m < 16:
                continue
            e = dn[:, i, q] - L.D_TRUE
            ok = np.abs(e) < 5
            rms = np.sqrt(np.mean(e[ok] ** 2)) * 1e3 / L.FS
            cr = L.crlb_ms("impacts", snr, m)
            parts.append(f"M = {m} {rms:.3f} vs {cr:.3f} ms ({rms / cr:.2f}x)")
        say(f"     {snr:+d} dB per shot: " + "; ".join(parts))
    say("     (200 draws leave the RMS itself uncertain by about 5%: ratios near 1 mean the bound is reached.)")
    rho_i, _ = L.ideal_wiener(r0, "impacts", -20, 64)
    say(f"  4. Wiener filter against the ideal one (true spectra, G = S / (S + N/2)): at the default, correlation"
        f" {r0['rho'][0]:.4f} against {rho_i:.4f}.")
    say(f"  5. {L.HIS_PAGES}.")
    e_w, K = L.welch_vs_scipy(r0["a"], r0["b"])
    say(f"  6. Welch cross spectrum against scipy.signal.csd: {e_w:.1e} relative (K = {K}).")
    idx = [i0, at(states, "harmonic", -30, 1024), at(states, "both", 0, 16), at(states, "impacts", -25, 1), at(states, "impacts", 10, 256)]
    e16, eex, clock = L.page_vs_python(NAME, states, idx)
    say("  7. The page rebuilds every record from the stored noise of each M and the signal formulas, and the aligned")
    say(f"     record, average, estimate and delayed copy with his FFT steps (fractional shifts): against numpy at 5 states,")
    say(f"     within {e16:.1e} (with the float32 gain the page holds; {eex:.1e} from the exact gain).")
    count, faults = L.sweep(NAME, full=full_sweep)
    say("")
    say("DISPLAY")
    say("  Stages (his), each a pure function of the clock: " + ", ".join(f"{n} {s0:.1f} s" for n, s0 in zip(clock["names"], clock["START"]))
        + f";")
    say(f"  the return to the clean signal at {clock['END']:.1f} s, period {clock['PERIOD']:.1f} s; poster at t = {clock['POSTER_T']:.1f} s.")
    say("  The averaging stage cross-fades through the nested averages (1, 16, 64, ... up to M); the label names only")
    say("  an average that exists.")
    say(f"  Overlap check (engine ?overlap): {count} frames ({'every state at the middle and end of every stage and the return' if full_sweep else 'every state at the poster'},")
    say(f"  and every stage of the default state live): {len(faults)} with a collision.")
    say(f"  Page size {os.path.getsize(path):,} bytes.")
    txt = "\n".join(out) + "\n"
    with open(os.path.join(common.HERE, "sp_delay_shots.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
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
        print(common.frames(NAME, [0.5, 1.0, 3.0, 8.0, 13.0, 19.0, 25.0, 29.0, 35.0]))
