"""The single-source delayed case shared by Figures 12 and 13 of the signal
processing document (sp_delay_gcc.py, sp_delay_shots.py).

His two pages ("Delayed signal recovery, method 1: GCC and Wiener filter" and
"method 2: shot averaging, GCC and Wiener filter") follow one model, kept here
so that both figures agree to the last digit:

    x1(t) = s(t) + n1(t),   x2(t) = s(t - tau) + n2(t),   tau = 48 ms,

one signal reaching two sensors, the second 48 ms later, each sensor adding its
own independent white Gaussian noise. fs = 500 Hz, N = 2048 samples (4.096 s).

The signal is one of his three kinds:
  impacts   eight impacts (his times and amplitudes), each ringing down the
            damped 11 Hz mode, zeta = 0.08, h(t) = exp(-zeta w_n t) sin(w_d t);
  harmonic  a 3 Hz fundamental with 6 and 9 Hz harmonics, amplitude modulated
            at 0.4 Hz (the same formula as his two blind source separation
            pages, Figures 10 and 11);
  both      impacts / 0.27 + 0.6 harmonic.
Each is standardized over the record (mean 0, RMS 1); the delayed copy is the
same function at t - tau with the same mean and scale, so it is a true delay,
not a circular shift. The SNR is the signal power over the noise power of one
record: sigma = 10^(-SNR/20).

Shots (Figure 13): the excitation is fired M times and the records averaged.
The signal repeats exactly; each shot draws new noise. The noise of shot j at
sensor c comes from its own generator (numpy default_rng, SeedSequence(SEED)
spawned per sensor), shot after shot, so the average of the first M shots is
nested: the 64-shot average contains the 16-shot one, and M = 1 is the single
shot of Figure 12. Each averaged noise record is stored as int16 times a power
of two, and those stored values ARE the model's noise (the page recomputes
every record from them): the rounding, at most 6e-5 of the noise's standard
deviation, is below anything plotted. The seed (SEED = 25) is the first whose
outcomes at both figures' default settings lie in the middle half of 400
draws (seed_rule(), the check files): a typical draw, not a lucky one.

The method is his, line for line (the port reproduces both of his pages to
2e-12, sp_delay_*.check.txt):
  1. Welch auto and cross spectra, 256-sample periodic Hann segments, 50%
     overlap (15 segments), S_ij = mean conj(X_i) X_j.
  2. Generalized cross-correlation: the full-length cross spectrum
     conj(A) B (4,096-point zero-padded FFTs, so the correlation is linear)
     weighted by W = g2 / (1 - g2), g2 = |S_12|^2 / (S_11 S_22) clipped at
     0.99, interpolated linearly from the Welch bins; its inverse FFT is the
     GCC, read over lags -125 .. 125 samples (+-250 ms). W is the coherence
     factor of the maximum-likelihood (Hannan-Thomson) processor; the full ML
     weighting also divides by |S_12|, which with 15 segments lifts the noise
     only bins and locks in less often (check file).
  3. The delay: the lag of the largest GCC value; method 2 refines it by a
     parabola through that sample and its two neighbours (at most half a
     sample either way).
  4. Alignment: x2 advanced by the estimate with an FFT phase ramp (his
     circular fractional shift), and the average of the two aligned records.
  5. Wiener filter: G = max(0, Re S_12' - 2 sqrt(S_11' S_22' / (2K))) / S_avg,
     at most 1, from the Welch spectra of the aligned records (S_12' is what
     both share, the signal; the subtracted term is two standard deviations
     of a noise-only cross spectrum) and of their average (S_avg); applied
     to the average by FFT, interpolated linearly between bins; the output
     standardized.
  6. The delayed copy of the estimate: the estimate shifted by the estimated
     delay.

JS is the figures' shared script (both pages): it rebuilds the signals from
the same formulas, every record from the stored noise, and the aligned,
averaged and filtered records from each state's delay and Wiener gain
computed here, with the same FFT steps, so the page draws the model's own
numbers; the check files compare the page's arrays with these.
"""
import numpy as np

import common

FS = 500.0                 # Hz
N = 2048                   # samples, 4.096 s
TAU = 0.048                # s, the true delay
D_TRUE = int(round(TAU * FS))   # 24 samples
MAXLAG = 125               # GCC read over +-125 samples (+-250 ms)
LG = 256                   # Welch segment
NFFT_GCC = 4096            # zero padded: linear correlation
FN, ZETA = 11.0, 0.08      # the mode each impact rings down
WN = 2 * np.pi * FN
WD = WN * np.sqrt(1 - ZETA ** 2)
IMPACTS = ((0.15, 1.0), (0.6, -0.7), (1.05, 0.85), (1.45, 0.6), (2.05, -1.0), (2.6, 0.75),
           (3.05, -0.55), (3.55, 0.9))
KINDS = ("impacts", "harmonic", "both")
KIND_LABEL = {"impacts": "impacts", "harmonic": "harmonic", "both": "both"}
SNRS = tuple(range(-30, 21, 5))          # dB, the slider's stops
SHOTS = (1, 16, 64, 256, 1024)
FMAX = 40.0                              # Hz shown in the spectra
KMAX = int(round(FMAX * LG / FS))        # 20: Welch bins 0 .. 20 shown (0 .. 39.1 Hz)
SEED = 25                                # the first seed whose outcomes at both defaults are typical (check files)


# ------------------------------------------------------------------ the signal
def harmonic(t):
    t = np.asarray(t, float)
    return (1 + 0.5 * np.sin(2 * np.pi * 0.4 * t)) * (np.sin(2 * np.pi * 3 * t)
                                                     + 0.45 * np.sin(2 * np.pi * 6 * t + 0.7)
                                                     + 0.25 * np.sin(2 * np.pi * 9 * t + 1.3))


def impacts(t):
    t = np.asarray(t, float)
    v = np.zeros_like(t)
    for t0, a in IMPACTS:
        u = t - t0
        v = v + np.where(u >= 0, a * np.exp(-ZETA * WN * np.maximum(u, 0)) * np.sin(WD * np.maximum(u, 0)), 0.0)
    return v


def source(kind, t):
    if kind == "impacts":
        return impacts(t) / 0.27
    if kind == "harmonic":
        return harmonic(t)
    return impacts(t) / 0.27 + 0.6 * harmonic(t)


def signals(kind):
    """s(t_n) and s(t_n - tau), standardized with the record's mean and RMS of s."""
    t = np.arange(N) / FS
    s = source(kind, t)
    m = s.mean()
    sd = np.sqrt(((s - m) ** 2).mean())
    return (s - m) / sd, (source(kind, t - TAU) - m) / sd


# ------------------------------------------------------------------ the noise
def shot_noise(seed=None, shots=SHOTS[-1]):
    """(2, shots, N): every shot's noise at both sensors, unit variance."""
    seed = SEED if seed is None else seed
    gens = [np.random.default_rng(c) for c in np.random.SeedSequence(seed).spawn(2)]
    return np.stack([g.standard_normal((shots, N)) for g in gens])


def averaged(noise, ms=SHOTS):
    """{M: (2, N)} the average of the first M shots at each sensor."""
    c = np.cumsum(noise, axis=1)
    return {m: c[:, m - 1] / m for m in ms}


def q16(a):
    """int16 values q and an exponent k with a ~ q 2^-k, the largest k that fits: a power of two
    is exact in binary, so the page (Math.pow(2, -k)) and numpy hold the same numbers."""
    a = np.asarray(a, float)
    k = int(np.floor(np.log2(32767 / np.abs(a).max())))
    return np.round(a * 2.0 ** k).astype(np.int16), k


def stored_noise(seed=None):
    """{M: (2, N)} the averaged noise as the page holds it: int16 times 2^-k.
    Returns (noise, codes) with codes[M][c] = (int16 array, k)."""
    av = averaged(shot_noise(seed))
    out, codes = {}, {}
    for m, v in av.items():
        rows, cd = [], []
        for c in range(2):
            q, k = q16(v[c])
            rows.append(q.astype(float) * 2.0 ** -k)
            cd.append((q, k))
        out[m] = np.array(rows)
        codes[m] = cd
    return out, codes


def i16(q):
    """int16 values as base64 (little endian), for the page's b64i16()."""
    import base64
    return base64.b64encode(np.ascontiguousarray(q, dtype="<i2").tobytes()).decode("ascii")


# ------------------------------------------------------------------ the method (his, line for line)
def hann(L=LG):
    return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(L) / L)


def welch(chs, L=LG):
    """S[i][j][k] = mean over segments of conj(X_i) X_j, bins 0 .. L/2; and K."""
    w = hann(L)
    starts = range(0, len(chs[0]) - L + 1, L // 2)
    X = [np.array([np.fft.rfft(np.asarray(c)[o:o + L] * w) for o in starts]) for c in chs]
    S = [[(np.conj(X[i]) * X[j]).mean(0) for j in range(len(chs))] for i in range(len(chs))]
    return S, len(starts)


def to_grid(Wk, M, L=LG):
    """A real function of the Welch bins on an M-point FFT grid, linear between bins."""
    k = np.arange(M)
    kk = np.where(k <= M // 2, k, M - k)
    pos = kk * L / M
    k0 = np.floor(pos).astype(int)
    k1 = np.minimum(k0 + 1, L // 2)
    return Wk[k0] + (Wk[k1] - Wk[k0]) * (pos - k0)


def gcc(a, b, refine):
    """The coherence weighted GCC of two records and the delay at its peak (samples)."""
    S, K = welch([a, b])
    g2 = np.minimum(np.abs(S[0][1]) ** 2 / (S[0][0].real * S[1][1].real + 1e-30), 0.99)
    Wk = g2 / (1 - g2)
    A = np.fft.fft(a, NFFT_GCC)
    B = np.fft.fft(b, NFFT_GCC)
    r = np.fft.ifft(to_grid(Wk, NFFT_GCC) * np.conj(A) * B).real
    lags = np.arange(-MAXLAG, MAXLAG + 1)
    v = r[lags % NFFT_GCC]
    i = int(np.argmax(v))                # the first of equal maxima, as his '>'
    di = int(lags[i])
    y0, y1, y2 = r[(di - 1) % NFFT_GCC], r[di % NFFT_GCC], r[(di + 1) % NFFT_GCC]
    den = y0 - 2 * y1 + y2
    frac = max(-0.5, min(0.5, 0.5 * (y0 - y2) / den)) if (refine and den < 0) else 0.0
    return dict(curve=v / np.abs(v).max(), di=di, d=di + frac, peak=(y0, y1, y2), g2=g2, W=Wk, r=r)


def shift(x, d):
    """x(t + d samples): his circular shift by an FFT phase ramp."""
    M = len(x)
    X = np.fft.fft(x)
    k = np.arange(M)
    f = np.where(k <= M // 2, k, k - M)
    X = X * np.exp(1j * 2 * np.pi * f * d / M)
    X[M // 2] = X[M // 2].real
    return np.fft.ifft(X).real


def apply_gain(x, G):
    return np.fft.ifft(np.fft.fft(x) * to_grid(G, len(x))).real


def standardize(a):
    a = a - a.mean()
    sd = np.sqrt((a * a).mean())
    return a / (sd or 1.0)


def corr(a, b):
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-30))


def wiener(a, b, d):
    """Align b by d samples, average, filter: his steps 4 and 5."""
    ba = shift(b, d)
    av = 0.5 * (a + ba)
    S, K = welch([a, ba, av])
    thr = 2 * np.sqrt(S[0][0].real * S[1][1].real / (2 * K))
    G = np.minimum(1.0, np.maximum(0.0, S[0][1].real - thr) / (S[2][2].real + 1e-30))
    e = standardize(apply_gain(av, G))
    return dict(ba=ba, av=av, G=G, e=e, Pavg=S[2][2].real, C=S[0][1].real, thr=thr, K=K)


def recover(a, b, refine):
    g = gcc(a, b, refine)
    w = wiener(a, b, g["d"])
    w.update(g)
    w["eT"] = shift(w["e"], -g["d"])
    return w


def snr_db(rho):
    """The SNR of an estimate whose correlation with the truth is rho (best scale)."""
    r2 = min(rho * rho, 1 - 1e-12)
    return 10 * np.log10(r2 / (1 - r2)) if r2 > 0 else -np.inf


def state(kind, snr, m, noise, refine):
    """Everything the page holds for one choice: the records' noise is noise[m]."""
    s, st = signals(kind)
    sig = 10 ** (-snr / 20)
    a = s + sig * noise[m][0]
    b = st + sig * noise[m][1]
    r = recover(a, b, refine)
    r["rho"] = (corr(r["e"], s), corr(r["eT"], st))
    r["rec_snr"] = tuple(10 * np.log10((x * x).mean() / (sig * sig * (n * n).mean()))
                         for x, n in ((s, noise[m][0]), (st, noise[m][1])))
    r["s"], r["st"], r["a"], r["b"] = s, st, a, b
    return r


def locked(d):
    """Within one sample (2 ms) of the true delay."""
    return abs(d - D_TRUE) < 1.0


# ------------------------------------------------------------------ the page's numbers
def b64(a, dtype):
    import base64
    return base64.b64encode(np.ascontiguousarray(a, dtype=dtype).tobytes()).decode("ascii")


def db_rel(v, top):
    """10 log10(v) - top in half dB steps, -63.5 .. 0, as int8; v <= 0 (a cross
    spectrum's real part can be negative) is -128: below the plot."""
    v = np.asarray(v, float)
    out = np.full(v.shape, -128, dtype=np.int8)
    pos = v > 0
    d = np.clip(10 * np.log10(np.where(pos, v, 1.0)) - top, -63.5, 0.0)
    out[pos] = np.round(2 * d[pos]).astype(np.int8)
    return out


def all_states(method, noise):
    """Every choice the page offers, in the page's order (kind, SNR, shots)."""
    ms = SHOTS if method == 2 else (1,)
    out = []
    for kind in KINDS:
        for snr in SNRS:
            for m in ms:
                out.append(((kind, snr, m), state(kind, snr, m, noise, method == 2)))
    return out


def page_data(method, states, codes):
    """DATA for nf-sp-delay-gcc (method 1) or nf-sp-delay-shots (method 2)."""
    ms = SHOTS if method == 2 else (1,)
    gcc_q, spec, coh, gidx, gk, gv = [], [], [], [0], [], []
    d, di, rho, rs, so = [], [], [], [], []
    for (kind, snr, m), r in states:
        gcc_q.append(np.round(127 * r["curve"]).astype(np.int8))
        top = max(10 * np.log10(r["Pavg"][1:KMAX + 1].max()),
                  10 * np.log10(max(r["C"][1:KMAX + 1].max(), 1e-300)))
        spec.append(np.concatenate([db_rel(r["Pavg"][:KMAX + 1], top), db_rel(r["C"][:KMAX + 1], top)]))
        coh.append(np.round(255 * r["g2"][:KMAX + 1]).astype(np.uint8))
        nz = np.nonzero(r["G"])[0]
        gk += nz.tolist()
        gv += r["G"][nz].tolist()
        gidx.append(len(gk))
        d.append(round(float(r["d"]), 12))
        di.append(int(r["di"]))
        rho.append([round(r["rho"][0], 4), round(r["rho"][1], 4)])
        rs.append([round(float(x), 2) for x in r["rec_snr"]])
        so.append(round(float(max(snr_db(r["rho"][0]), -99.0)), 2))
    return dict(
        method=method, n=N, fs=FS, tau=TAU, dtrue=D_TRUE, maxlag=MAXLAG, lg=LG, kmax=KMAX,
        fn=FN, zeta=ZETA, impacts=[list(p) for p in IMPACTS],
        kinds=list(KINDS), snrs=list(SNRS), shots=list(ms),
        noise=[[[i16(q), k] for q, k in codes[m]] for m in ms],
        gcc=b64(np.concatenate(gcc_q), "i1"), spec=b64(np.concatenate(spec), "i1"),
        coh=b64(np.concatenate(coh), "u1"), gidx=gidx, gk=b64(np.array(gk), "u1"), gv=common.f32(np.array(gv)),
        d=d, di=di, rho=rho, rs=rs, so=so,
        gain_th=[round(10 * np.log10(m), 2) for m in ms],
    )


# ------------------------------------------------------------------ checks shared by both check files
def welch_vs_scipy(a, b):
    """The Welch cross spectrum against scipy.signal.csd (an independent implementation):
    S = Pxy fs sum(w^2) / 2 inside, without the 2 at DC and Nyquist. Largest relative error."""
    from scipy.signal import csd
    S, K = welch([a, b])
    w = hann()
    f, P = csd(a, b, fs=FS, window=w, nperseg=LG, noverlap=LG // 2, detrend=False, scaling="density")
    sc = np.full(len(f), FS * (w * w).sum() / 2)
    sc[0] *= 2
    sc[-1] *= 2
    return float(np.abs(P * sc - S[0][1]).max() / np.abs(S[0][1]).max()), K


def crlb_ms(kind, snr, m=1):
    """The Cramer-Rao bound of the delay (Knapp and Carter 1976), in ms:
    var >= 1 / (2 T int (2 pi f)^2 g2 / (1 - g2) df), one-sided spectra, the signal's from
    its periodogram over the record, each sensor's white noise N0 = 2 sigma^2 / (fs M)."""
    s, _ = signals(kind)
    f = np.fft.rfftfreq(N, 1 / FS)
    S = 2 * np.abs(np.fft.rfft(s)) ** 2 / (FS * N)
    S[0] /= 2
    S[-1] /= 2
    N0 = 2 * 10 ** (-snr / 10) / (FS * m)
    I = np.sum((2 * np.pi * f) ** 2 * S ** 2 / (N0 * (2 * S + N0))) * FS / N
    return 1e3 / np.sqrt(2 * (N / FS) * I)


def mc_delays(kind, snr, draws, refine, m=1, seed0=10_000):
    """Delay estimates (samples) of `draws` independent noise draws (seeds seed0 ...), the
    m-shot average drawn as its own distribution, N(0, 1/m) per sample."""
    s, st = signals(kind)
    sig = 10 ** (-snr / 20) / np.sqrt(m)
    out = []
    for j in range(draws):
        n = np.random.default_rng(seed0 + j).standard_normal((2, N))
        out.append(gcc(s + sig * n[0], st + sig * n[1], refine)["d"])
    return np.array(out)


def ideal_wiener(r, kind, snr, m):
    """The Wiener filter with the true spectra, G = S / (S + N/2) on the Welch bins (the
    average of two aligned records halves each sensor's noise power), applied to the same
    average: the correlation it reaches, against the method's."""
    s, _ = signals(kind)
    S, K = welch([s])
    w = hann()
    Pn = 10 ** (-snr / 10) / m * (w * w).sum() / 2
    G = S[0][0].real / (S[0][0].real + Pn)
    return corr(standardize(apply_gain(r["av"], G)), s), G


def seed_rule(draws=400):
    """The noise draw shown: of seeds 1, 2, ..., the first whose outcomes at both default
    settings fall in the middle half of `draws` draws (seeds 1 .. draws): Figure 12 (impacts,
    -10 dB, one shot) its integer delay error at most one sample and its correlation between
    the quartiles; Figure 13 (impacts, -20 dB, 64 shots) its refined delay error and its
    correlation between the quartiles; and its single shot at -20 dB not within a sample
    (as 96% of draws). Returns the table and the seed."""
    s, st = signals("impacts")
    rows = []
    for seed in range(1, draws + 1):
        sh = shot_noise(seed, 64)
        n1, n64 = sh[:, 0], sh.mean(1)
        r1 = recover(s + 10 ** .5 * n1[0], st + 10 ** .5 * n1[1], False)
        r2 = recover(s + 10 * n64[0], st + 10 * n64[1], True)
        r3 = gcc(s + 10 * n1[0], st + 10 * n1[1], True)
        rows.append((seed, r1["d"] - D_TRUE, corr(r1["e"], s), r2["d"] - D_TRUE, corr(r2["e"], s), r3["d"] - D_TRUE))
    A = np.array(rows)
    q = {j: np.percentile(A[:, j], [25, 50, 75]) for j in (1, 2, 3, 4)}
    ok = ((np.abs(A[:, 1]) <= 1) & (A[:, 2] >= q[2][0]) & (A[:, 2] <= q[2][2]) & (A[:, 3] >= q[3][0])
          & (A[:, 3] <= q[3][2]) & (A[:, 4] >= q[4][0]) & (A[:, 4] <= q[4][2]) & (np.abs(A[:, 5]) >= 1))
    return A, q, int(A[ok][0, 0]), float(ok.mean())


def page_arrays(name, idx):
    """The page's own records, aligned record, average, estimate and delayed copy for the
    states idx (run in Chromium), and its stage clock."""
    from playwright.sync_api import sync_playwright
    import shutil
    import tempfile
    import threading
    tmp = tempfile.mkdtemp(prefix="nfdelay-")
    out = []
    try:
        import os
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?still")
            pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
            for i in idx:
                out.append(pg.evaluate(f"""() => {{ const w = waves({i}), A = a => Array.from(a);
                    return {{ s: A(w.S.s), st: A(w.S.st), m1: A(w.m1), m2: A(w.m2), ba: A(w.ba), av: A(w.av),
                              e: A(w.e), eT: A(w.eT), G: A(w.G) }}; }}"""))
            clock = pg.evaluate("({ START, END, PERIOD, POSTER_T, names: NAMES })")
            b.close()
        srv.shutdown()
        if errs:
            raise RuntimeError(errs)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out, clock


def page_vs_python(name, states, idx):
    """Largest differences between the page's arrays and the generator's: with the gain the
    page holds (float32), and with the exact gain."""
    got, clock = page_arrays(name, idx)
    e16, eex = 0.0, 0.0
    for i, g in zip(idx, got):
        r = states[i][1]
        Gq = r["G"].astype(np.float32).astype(float)
        e_q = standardize(apply_gain(r["av"], Gq))
        ref = dict(s=r["s"], st=r["st"], m1=r["a"], m2=r["b"], ba=r["ba"], av=r["av"], e=e_q, eT=shift(e_q, -r["d"]), G=Gq)
        e16 = max(e16, max(float(np.abs(np.array(g[k]) - v).max()) for k, v in ref.items()))
        eex = max(eex, float(np.abs(np.array(g["e"]) - r["e"]).max()), float(np.abs(np.array(g["eT"]) - r["eT"]).max()))
    return e16, eex, clock



def sweep(name, full=False, width=672):
    """The engine's overlap check (?overlap, README "Nothing overlaps") on the page's states,
    one page load per pass: every state (kind, SNR, shots) at the poster moment and, with
    `full`, at the middle and the end of every stage and in the return; and a live pass (not
    ?still: the stage hairline drawn) through every stage of the default state. Returns
    (frames checked, faults)."""
    import os
    import shutil
    import tempfile
    import threading
    from playwright.sync_api import sync_playwright
    tmp = tempfile.mkdtemp(prefix="nfdelay-")
    faults, count = [], 0
    try:
        os.makedirs(os.path.join(tmp, "anim"))
        shutil.copytree(common.FONTS, os.path.join(tmp, "fonts"))
        shutil.copy(os.path.join(common.ANIM, f"nf-{name}.html"), os.path.join(tmp, "anim"))
        srv = common._server(tmp)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            b = p.chromium.launch()
            for live in (False, True):
                pg = b.new_page(viewport={"width": width, "height": 1400}, device_scale_factor=1)
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/anim/nf-{name}.html?{'overlap' if live else 'still&overlap'}")
                pg.wait_for_function("document.documentElement.dataset.ready === '1'", timeout=30000)
                if live:
                    pg.evaluate("setPlay(false)")
                c = pg.evaluate("({S: START, T: KEY.map(k => TRD[k]), E: END, R: RET, PT: POSTER_T, NK: D.kinds.length, NS, NM})")
                every = []
                for k, (st, tr) in enumerate(zip(c["S"], c["T"])):
                    every += ([st + .5 * tr] if tr else []) + [st + tr + .3 if k else 1.7]
                every += [c["E"] + .5 * c["R"]]
                if live:
                    plan = [(None, every + [c["PT"]])]
                else:
                    plan = [((ki, si, mi), (every if full else []) + [c["PT"]])
                            for ki in range(c["NK"]) for si in range(c["NS"]) for mi in range(c["NM"])]
                for st, moments in plan:
                    if st:
                        pg.evaluate("([a, b, c]) => { KI = a; SI = b; MI = c; }", list(st))
                    for tt in moments:
                        lab, cro = pg.evaluate(f"() => {{ t = {tt}; render(); return [window.__overlaps || [], window.__crossings || []]; }}")
                        count += 1
                        if lab or cro:
                            faults.append((live, st, round(tt, 2), lab, cro))
                if errs:
                    faults.append(("errors", errs))
                pg.close()
            b.close()
        srv.shutdown()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return count, faults



def mc_nested(kind, snrs, draws, seed0=20_000):
    """Refined delays (samples) of `draws` independent shot sequences (seeds seed0 ...), each
    averaged over its first M shots as the page does: shape (draws, len(snrs), len(SHOTS)); and
    the measured averaging gain 10 log10(P_1 / P_M) of each draw and sensor, (draws, 2, len(SHOTS))."""
    s, st = signals(kind)
    d = np.zeros((draws, len(snrs), len(SHOTS)))
    g = np.zeros((draws, 2, len(SHOTS)))
    for j in range(draws):
        av = averaged(shot_noise(seed0 + j))
        p1 = (av[1] ** 2).mean(1)
        for q, m in enumerate(SHOTS):
            g[j, :, q] = 10 * np.log10(p1 / (av[m] ** 2).mean(1))
            for i, snr in enumerate(snrs):
                sig = 10 ** (-snr / 20)
                d[j, i, q] = gcc(s + sig * av[m][0], st + sig * av[m][1], True)["d"]
    return d, g


# the one-off comparison with his two pages (the brief's files, 5 Oct 2026): his page script run
# in Chromium with its internals exposed, against this module fed his own noise (mulberry32(11),
# Box-Muller, n1 and n2 interleaved); method 1 at (-10 dB, impacts), (-15, harmonic), (5, both),
# (-20, impacts); method 2 at (-20, impacts, 64 shots), (-30, both, 1,024), (0, harmonic, 16),
# (-25, impacts, 1)
HIS_PAGES = ("his page reproduced: signals, noise, GCC, Wiener gain, aligned record, average, estimate and "
             "its delayed copy agree within 1.8e-12; the delays (23 samples at his default, -10 dB: 46 ms; "
             "23.649964 samples at his method 2 default) and the correlations to all printed digits")

# ------------------------------------------------------------------ the page's script (both figures)
JS = r"""
/* ---- one signal at two sensors, Figures 12 and 13 (tools/numfig/sp_delay_lib.py) ----
   D.method 1: generalized cross-correlation, integer delay, Wiener filter (Figure 12);
   D.method 2: the same after averaging M shots, delay refined below a sample (Figure 13). */
const D = DATA, M2 = D.method === 2, N = D.n, FS = D.fs, NL = 2 * D.maxlag + 1, NB = D.kmax + 1;
const NS = D.snrs.length, NM = D.shots.length;
const sidx = (ki, si, mi) => (ki * NS + si) * NM + mi;
const num = (v, d) => (Math.abs(v) < .5 * Math.pow(10, -d) ? 0 : v).toFixed(d).replace('-', '−');
const thou = v => String(v).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
const arrive = t0 => settle(t0, .28);

/* ================================================ the model's numbers, as the generator left them */
function bytes64(s) { const b = atob(s), u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
const GCC = b64i8(D.gcc), SPEC = b64i8(D.spec), COH = bytes64(D.coh), GK = bytes64(D.gk), GV = b64f32(D.gv);
/* the signal from its formulas (his), standardized over the record; the delayed copy is the same
   function 48 ms later with the same mean and scale */
const WN = 2 * Math.PI * D.fn, WD = WN * Math.sqrt(1 - D.zeta * D.zeta);
const harmonic = t => (1 + .5 * Math.sin(2 * Math.PI * .4 * t)) *
  (Math.sin(2 * Math.PI * 3 * t) + .45 * Math.sin(2 * Math.PI * 6 * t + .7) + .25 * Math.sin(2 * Math.PI * 9 * t + 1.3));
function impactTrain(t) { let v = 0; for (const [t0, a] of D.impacts) { const u = t - t0; if (u >= 0) v += a * Math.exp(-D.zeta * WN * u) * Math.sin(WD * u); } return v; }
const SRC = [t => impactTrain(t) / .27, harmonic, t => impactTrain(t) / .27 + .6 * harmonic(t)];
const SIG = SRC.map(f => {
  const s = new Float64Array(N), st = new Float64Array(N);
  let m = 0, q = 0;
  for (let n = 0; n < N; n++) { s[n] = f(n / FS); m += s[n]; }
  m /= N;
  for (let n = 0; n < N; n++) { s[n] -= m; q += s[n] * s[n]; }
  const sd = Math.sqrt(q / N);
  for (let n = 0; n < N; n++) { s[n] /= sd; st[n] = (f(n / FS - D.tau) - m) / sd; }
  return { s, st };
});
/* the noise of each sensor averaged over the first M shots, int16 times 2^-k (exact) */
const NU = D.noise.map(pair => pair.map(([code, k]) => {
  const q = new Int16Array(bytes64(code).buffer), v = new Float64Array(N), sc = Math.pow(2, -k);
  for (let n = 0; n < N; n++) v[n] = q[n] * sc;
  return v;
}));
/* his FFT, shift and filter, line for line */
function fft(re, im, inv) {
  const n = re.length;
  for (let i = 1, j = 0; i < n; i++) { let b = n >> 1; for (; j & b; b >>= 1) j ^= b; j ^= b;
    if (i < j) { let q = re[i]; re[i] = re[j]; re[j] = q; q = im[i]; im[i] = im[j]; im[j] = q; } }
  for (let len = 2; len <= n; len <<= 1) {
    const ang = (inv ? 2 : -2) * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
    for (let i = 0; i < n; i += len) { let cr = 1, ci = 0;
      for (let k = 0; k < len / 2; k++) {
        const a = i + k, b = a + len / 2, tr = re[b] * cr - im[b] * ci, ti = re[b] * ci + im[b] * cr;
        re[b] = re[a] - tr; im[b] = im[a] - ti; re[a] += tr; im[a] += ti;
        const ncr = cr * wr - ci * wi; ci = cr * wi + ci * wr; cr = ncr; } } }
  if (inv) for (let i = 0; i < n; i++) { re[i] /= n; im[i] /= n; }
}
function shift(x, d) {                         // x(t + d samples), circular
  const M = x.length, r = Float64Array.from(x), im = new Float64Array(M);
  fft(r, im);
  for (let k = 0; k < M; k++) { const f = k <= M / 2 ? k : k - M, ph = 2 * Math.PI * f * d / M, c = Math.cos(ph), sn = Math.sin(ph);
    const a = r[k] * c - im[k] * sn; im[k] = r[k] * sn + im[k] * c; r[k] = a; }
  im[M / 2] = 0;
  fft(r, im, true); return r;
}
function applyGain(x, G) {                     // a real gain on the Welch bins, linear between them
  const M = x.length, L = D.lg, r = Float64Array.from(x), im = new Float64Array(M);
  fft(r, im);
  for (let k = 0; k < M; k++) { const kk = k <= M / 2 ? k : M - k, pos = kk * L / M, k0 = Math.floor(pos), k1 = Math.min(k0 + 1, L / 2);
    const g = G[k0] + (G[k1] - G[k0]) * (pos - k0); r[k] *= g; im[k] *= g; }
  fft(r, im, true); return r;
}
function standardize(a) {
  let m = 0; for (const v of a) m += v; m /= a.length;
  let q = 0; for (let i = 0; i < a.length; i++) { a[i] -= m; q += a[i] * a[i]; }
  const sd = Math.sqrt(q / a.length) || 1; for (let i = 0; i < a.length; i++) a[i] /= sd;
  return a;
}
/* one choice's records, aligned record, average, estimate and its delayed copy, from the stored
   noise and the generator's delay and Wiener gain */
const CACHE = new Map();
function waves(i) {
  let w = CACHE.get(i);
  if (w) return w;
  const ki = Math.floor(i / (NS * NM)), si = Math.floor(i / NM) % NS, mi = i % NM;
  const S = SIG[ki], sig = Math.pow(10, -D.snrs[si] / 20), nu = NU[mi], d = D.d[i];
  const m1 = new Float64Array(N), m2 = new Float64Array(N), av = new Float64Array(N), G = new Float64Array(D.lg / 2 + 1);
  for (let n = 0; n < N; n++) { m1[n] = S.s[n] + sig * nu[0][n]; m2[n] = S.st[n] + sig * nu[1][n]; }
  const ba = shift(m2, d);
  for (let n = 0; n < N; n++) av[n] = .5 * (m1[n] + ba[n]);
  for (let j = D.gidx[i]; j < D.gidx[i + 1]; j++) G[GK[j]] = GV[j];
  const e = standardize(applyGain(av, G)), eT = shift(e, -d);
  w = { i, ki, si, mi, sig, d, m1, m2, ba, av, e, eT, S, G };
  if (CACHE.size >= 40) CACHE.delete(CACHE.keys().next().value);   // the oldest goes
  CACHE.set(i, w);
  return w;
}

/* ================================================ the reader's choices */
let KI = 0, SI = D.snrs.indexOf(D.def.snr), MI = D.shots.indexOf(D.def.m);
const QS = new URLSearchParams(location.search);
{ const k = D.kinds.indexOf(QS.get('kind')); if (k >= 0) KI = k; }
{ const k = D.snrs.indexOf(Number(QS.get('snr'))); if (QS.has('snr') && k >= 0) SI = k; }
{ const k = D.shots.indexOf(Number(QS.get('shots'))); if (QS.has('shots') && k >= 0) MI = k; }
const cur = () => sidx(KI, SI, MI);

/* ================================================ the clock: his stages, one after another */
const NAMES = M2 ? ['signal', 'noise', 'averaging', 'delay', 'align', 'Wiener filter', 'estimate']
                 : ['signal', 'noise', 'delay', 'align', 'Wiener filter', 'estimate'];
const KEY = NAMES.map(s => s.split(' ')[0]), K = NAMES.length, AT_ = k => KEY.indexOf(k);
const TRD = { signal: 0, noise: 1.5, averaging: 1.8, delay: 2.2, align: 1.4, Wiener: 2.2, estimate: 1.6 };
const S0 = 2.0, HOLD = 4.2, RET = 1.3;
const START = [0];
for (let k = 1; k < K; k++) START.push(START[k - 1] + (k === 1 ? S0 : TRD[KEY[k - 1]] + HOLD));
const END = START[K - 1] + TRD[KEY[K - 1]] + HOLD, PERIOD = END + RET;
const done = k => START[k] + (k ? TRD[KEY[k]] : 1.6);          // stage k complete (cycle 0)
const QSTAGE = QS.has('stage') ? clamp(Math.round(Number(QS.get('stage'))) - 1, 0, K - 1) : -1;
const POSTER_T = QSTAGE >= 0 ? done(QSTAGE) + .05 : done(K - 1) + 1.2;
if (QSTAGE >= 0 && !STILL && !REDUCED) t = PERIOD + START[QSTAGE];
/* where the clock is: the stage, its transition eased (e), the share of the stage gone (frac);
   k = -1 is the return to the clean signal that closes a cycle */
function phase() {
  const u = t < PERIOD ? t : t % PERIOD;
  if (u >= END) return { k: -1, e: easeInOut(clamp((u - END) / RET)), frac: 1, u };
  let k = K - 1;
  while (k > 0 && u < START[k]) k--;
  const dur = TRD[KEY[k]], el = u - START[k], next = k < K - 1 ? START[k + 1] : END;
  return { k, e: dur ? easeInOut(clamp(el / dur)) : 1, el, frac: el / (next - START[k]), u };
}
/* a step's progress: 0 before its stage, its transition while it runs, 1 after; a share of the
   transition (a, b) gives a part of it its own moment */
function P(ph, key, a = 0, b = 1) {
  const j = AT_(key);
  if (j < 0) return 0;
  if (ph.k === -1) return 1;
  if (ph.k < j) return 0;
  if (ph.k > j) return 1;
  const dur = TRD[key];
  return easeInOut(clamp((ph.el / dur - a) / (b - a)));
}

/* ================================================ the layout (drawing units) */
const LA = { x: 96, w: 876, y1: 86, h: 90, gap: 14 };          // the two lanes of (a)
LA.y2 = LA.y1 + LA.h + LA.gap;
const PB = { x: 96, w: 352, y: LA.y2 + LA.h + 100, h: 114 };    // (b) the GCC
const PC = { x: 590, w: 382, y: PB.y, h1: 64, gap: 16, h2: 34 }; // (c) the spectra over the gain
PC.y2 = PC.y + PC.h1 + PC.gap;
const BOT = PB.y + PB.h + 72;                                   // the controls and numbers
const STG = { y: 14, h: 30, gap: 26 };
const STX = [];                                                 // the stage chips, set once the type is in
function stageChips() {
  if (STX.length) return;
  ctx.save(); ctx.font = font({ size: 16 });
  const ws = NAMES.map((s, k) => ctx.measureText((k + 1) + '  ' + s).width + 26);
  ctx.restore();
  const tot = ws.reduce((a, b) => a + b, 0) + STG.gap * (K - 1);
  let x = (W - tot) / 2;
  ws.forEach(w => { STX.push({ x, w }); x += w + STG.gap; });
}
/* the controls: the SNR slider, the kind of signal, the shots (Figure 13) */
const CX0 = 650;                                                // the controls' column
const SL = { x0: CX0 + 12, x1: CX0 + 252, y: BOT + 28 };
const KC = { x: CX0 + 62, y: BOT + 68, w: [84, 92, 64], h: 28, gap: 8 };
const MC = { x: 262, y: BOT - 6, w: 60, h: 28, pitch: 72 };      // shots chips: the table's head
const HOVER = { type: '', i: -1 }, DOWN = { type: '', i: -1 };
let DRAG = false;

/* ================================================ drawing helpers */
function mix(c1, c2, s) {
  const a = _hex(c1), b = _hex(c2);
  return `rgb(${Math.round(lerp(a[0], b[0], s))},${Math.round(lerp(a[1], b[1], s))},${Math.round(lerp(a[2], b[2], s))})`;
}
function sub(letter, x, y, words, a) {
  if (a <= 0) return;
  panel(letter, x, y, { alpha: a });
  text(words, x + 35, y, { size: 17, color: C.body, alpha: a });
}
/* math with an accent over a part: [['x', 'bar'], ['_1(t)']], [['s', 'hat'], ['(t)']] */
function accent(kind, x0, w, size, color, alpha) {
  const sl = size * .07;
  if (kind === 'bar') line([[x0 + w * .14 + sl, -size * .63], [x0 + w * .96 + sl, -size * .63]], { color, width: Math.max(1, size * .06), alpha });
  else line([[x0 + w * .12 + sl, -size * .6], [x0 + w * .45 + sl, -size * .78], [x0 + w * .78 + sl, -size * .6]],
            { color, width: Math.max(1, size * .055), alpha });
}
function amath(parts, x, y, o = {}) {
  const { size = 17, color = C.ink, align = 'left', alpha = 1, rot = 0 } = o;
  const ws = parts.map(p => math(p[0], 0, -1e4, { size, alpha: 0 }));
  const tot = ws.reduce((a, b) => a + b, 0);
  if (alpha <= 0) return tot;
  let off = align === 'center' ? -tot / 2 : align === 'right' ? -tot : 0;
  ctx.save(); ctx.translate(x, y); if (rot) ctx.rotate(rot);
  parts.forEach((p, j) => {
    math(p[0], off, 0, { size, color, alpha });
    if (p[1]) accent(p[1], off, ws[j], size, color, alpha);
    off += ws[j];
  });
  ctx.restore();
  return tot;
}
const tw = (s, size) => { ctx.save(); ctx.font = font({ size }); const w = ctx.measureText(s).width; ctx.restore(); return w; };
/* a nice tick step for a half range R: one of 1, 2, 2.5, 5 times a power of ten in [.45 R, .9 R] */
function tick(R) {
  const p = Math.pow(10, Math.floor(Math.log10(R * .9)));
  for (const m of [5, 2.5, 2, 1]) if (m * p <= R * .9) return m * p;
  return p / 2;
}

/* ================================================ (a) the lanes */
const BUF = [new Float64Array(N), new Float64Array(N), new Float64Array(N), new Float64Array(N)];
const PTS = Array.from({ length: N }, () => [0, 0]);
const TX = n => LA.x + n / (N - 1) * LA.w;
function shiftIdx(src, out, k) { for (let n = 0; n < N; n++) out[n] = src[((n + k) % N + N) % N]; return out; }
function lerpArr(a, b, s, out) { for (let n = 0; n < N; n++) out[n] = a[n] + (b[n] - a[n]) * s; return out; }
/* what each lane holds now: the trace, its colour, the clean signal under it (hidden: solid;
   the truth an estimate is judged by: dashed), and the lane's name */
const LAB = {
  s1: [['s(t)']], s2: [['s(t - \\tau)']], x1: [['x_1(t)']], x2: [['x_2(t)']],
  b1: [['x', 'bar'], ['_1(t)']], b2: [['x', 'bar'], ['_2(t)']], a2: [['x', 'bar'], ['_2(t + '], ['\\tau', 'hat'], [')']],
  m1: [['x_1(t)']], m2a: [['x_2(t + '], ['\\tau', 'hat'], [')']],
  av: [['\\rm{average}']], e1: [['s', 'hat'], ['(t)']], e2: [['s', 'hat'], ['(t - '], ['\\tau', 'hat'], [')']],
};
function laneState(w, ph) {
  const S = w.S, s = S.s, st = S.st, A = BUF[0], B = BUF[1];
  const key = ph.k === -1 ? 'return' : KEY[ph.k], e = ph.e;
  const n1 = NU[0], sig = w.sig, bar = M2 ? 'b' : 'x';
  const L = { A: s, B: st, ca: C.navy, cb: C.navy, wa: 2, wb: 2, ra: null, rb: null, rdash: false, ralpha: 0,
              la: LAB.s1, lb: LAB.s2, info: '' };
  const hidden = (ra, rb, al) => { L.ra = ra; L.rb = rb; L.ralpha = al; L.rdash = false; };
  const rec = () => { L.ca = L.cb = C.sky; L.wa = L.wb = 1; };
  if (key === 'signal') return L;
  if (key === 'noise') {
    for (let n = 0; n < N; n++) { A[n] = s[n] + e * sig * n1[0][n]; B[n] = st[n] + e * sig * n1[1][n]; }
    Object.assign(L, { A, B, la: LAB.x1, lb: LAB.x2 }); rec(); hidden(s, st, e);
    L.info = 'snr1'; return L;
  }
  if (key === 'averaging') {
    const chain = w.mi, p = e * chain, j = Math.min(Math.floor(p), Math.max(chain - 1, 0)), f = chain ? p - j : 0;
    const u0 = NU[j], u1 = NU[Math.min(j + 1, chain)];
    for (let n = 0; n < N; n++) {
      A[n] = s[n] + sig * (u0[0][n] + (u1[0][n] - u0[0][n]) * f);
      B[n] = st[n] + sig * (u0[1][n] + (u1[1][n] - u0[1][n]) * f);
    }
    Object.assign(L, { A, B, la: e > .5 ? LAB.b1 : LAB.x1, lb: e > .5 ? LAB.b2 : LAB.x2 }); rec(); hidden(s, st, 1);
    L.info = 'avg'; L.avgAt = chain ? D.shots[f < .5 ? j : Math.min(j + 1, chain)] : 1;
    return L;
  }
  const la1 = M2 ? LAB.b1 : LAB.m1, la2 = M2 ? LAB.b2 : LAB.x2, laa = M2 ? LAB.a2 : LAB.m2a;
  if (key === 'delay') {
    Object.assign(L, { A: w.m1, B: w.m2, la: la1, lb: la2 }); rec(); hidden(s, st, 1);
    L.info = 'rec'; return L;
  }
  if (key === 'align') {
    const k = Math.round(e * w.d);
    Object.assign(L, { A: w.m1, B: e >= 1 ? w.ba : shiftIdx(w.m2, B, k), la: la1, lb: e > .5 ? laa : la2 }); rec();
    hidden(s, shiftIdx(st, BUF[2], e >= 1 ? Math.round(w.d) : k), 1);
    L.info = 'rec'; return L;
  }
  if (key === 'Wiener') {
    const g = P(ph, 'Wiener', .35, 1);
    Object.assign(L, { A: lerpArr(w.m1, w.av, g, A), B: lerpArr(w.ba, w.e, g, B), la: g > .5 ? LAB.av : la1, lb: g > .5 ? LAB.e1 : laa });
    rec(); L.cb = mix(C.sky, C.accent, g); L.wb = 1 + 1.2 * g; hidden(s, s, 1);
    L.info = 'rec'; return L;
  }
  if (key === 'estimate') {
    const k = Math.round(e * w.d);
    Object.assign(L, { A: lerpArr(w.av, w.e, e, A), B: e >= 1 ? w.eT : shiftIdx(w.e, B, -k), la: e > .5 ? LAB.e1 : LAB.av,
                       lb: e > .5 ? LAB.e2 : LAB.e1 });
    L.ca = mix(C.sky, C.accent, e); L.wa = 1 + 1.2 * e; L.cb = C.accent; L.wb = 2.2;
    L.ra = s; L.rb = st; L.rdash = true; L.ralpha = e; L.info = 'est';
    return L;
  }
  // the return: the estimates become the clean signals again
  Object.assign(L, { A: lerpArr(w.e, s, e, A), B: lerpArr(w.eT, st, e, B), la: e > .5 ? LAB.s1 : LAB.e1, lb: e > .5 ? LAB.s2 : LAB.e2 });
  L.ca = L.cb = mix(C.accent, C.navy, e); L.wa = L.wb = 2.2 - .2 * e;
  L.ra = s; L.rb = st; L.rdash = true; L.ralpha = 1 - e;
  return L;
}
function laneScale(v, r, ra) {
  let m = 1e-9;
  for (let n = 0; n < N; n++) m = Math.max(m, Math.abs(v[n]));
  if (r && ra > .05) for (let n = 0; n < N; n++) m = Math.max(m, Math.abs(r[n]));
  return m * 1.1;
}
function drawLane(j, v, col, wd, r, ra, rdash, label, prog, axp, la) {
  const y = j ? LA.y2 : LA.y1, R = laneScale(v, r, ra), st = tick(R), ticks = [];
  for (let q = -2; q <= 2; q++) if (Math.abs(q * st) <= R * .9) ticks.push(q * st);
  const A = axes({ x: LA.x, y, w: LA.w, h: LA.h, xlim: [0, (N - 1) / FS], ylim: [-R, R],
                   xticks: [0, 1, 2, 3, 4], yticks: ticks, xfmt: j ? (v => fmt(v)) : () => '',
                   xlabel: j ? '\\rm{time}\\ \\ t\\ \\ (\\rm{s})' : '', tickSize: 16, labelSize: 17, progress: axp });
  const ga = clamp(axp * 1.4);
  A.inside(() => {
    line([[LA.x, A.Y(0)], [LA.x + LA.w, A.Y(0)]], { color: C.rule, width: 1, alpha: ga });
    for (let n = 0; n < N; n++) { PTS[n][0] = TX(n); PTS[n][1] = A.Y(v[n]); }
    line(PTS, { color: col, width: wd, progress: prog });
    if (r && ra > 0) {
      for (let n = 0; n < N; n++) { PTS[n][0] = TX(n); PTS[n][1] = A.Y(r[n]); }
      line(PTS, { color: C.navy, width: rdash ? 1.5 : 1.6, dash: rdash ? [6, 4] : null, alpha: ra });
    }
  });
  amath(label, LA.x - 58, y + LA.h / 2, { size: 17, align: 'center', rot: -Math.PI / 2, alpha: la });
}
function panelA(w, ph) {
  const L = laneState(w, ph), a0 = arrive(0), axp = seg(.02, .35);
  sub('a', 18, 70, 'sensor records', a0);
  // the clean signals draw themselves in the intro
  const pr = t < PERIOD ? seg(.15, .45) : 1, pr2 = t < PERIOD ? seg(.22, .45) : 1;
  drawLane(0, L.A, L.ca, L.wa, L.ra, L.ralpha, L.rdash, L.la, pr, axp, arrive(.3));
  drawLane(1, L.B, L.cb, L.wb, L.rb, L.ralpha, L.rdash, L.lb, pr2, seg(.06, .35), arrive(.34));
  // which line is which
  const ka = arrive(.4), ky = 70, items = [[C.sky, 1, null, 'record'], [C.navy, 1.6, null, 'clean signal, unseen'],
    [C.accent, 2.2, null, 'estimate'], [C.navy, 1.5, [6, 4], 'true signal']];
  let kx = LA.x + LA.w;
  for (let q = items.length - 1; q >= 0; q--) {
    const [col, wd, dash, words] = items[q];
    kx -= tw(words, 16);
    text(words, kx, ky, { size: 16, color: C.body, alpha: ka });
    kx -= 34;
    line([[kx, ky - 5], [kx + 26, ky - 5]], { color: col, width: wd, dash, alpha: ka });
    kx -= 22;
  }
  // the records' SNR, as the stage leaves them (each sensor's own draw of noise)
  const y = LA.y2 + LA.h + 16 + 17 + 16, two = r => `${num(r[0], 1)}\\ \\rm{and}\\ ${num(r[1], 1)}\\ \\rm{dB}`;
  let words = '';
  if (L.info === 'snr1') words = (M2 ? '\\rm{one shot: SNR}\\ ' : '\\rm{the records: SNR}\\ ') + two(D.rs[sidx(w.ki, w.si, 0)]);
  else if (L.info === 'avg') words = L.avgAt > 1 ? `\\rm{the average of}\\ M = ${thou(L.avgAt)}\\ \\rm{shots}` : '\\rm{one shot: nothing to average}';
  else if (L.info === 'rec' || L.info === 'est')
    words = M2 && w.mi ? `\\rm{average of}\\ ${thou(D.shots[w.mi])}\\ \\rm{shots: SNR}\\ ` + two(D.rs[w.i])
                       : (M2 ? '\\rm{one shot: SNR}\\ ' : '\\rm{the records: SNR}\\ ') + two(D.rs[w.i]);
  if (words) math(words, LA.x + LA.w, y, { size: 16, color: C.body, align: 'right', alpha: arrive(.4) });
  return L;
}

/* ================================================ (b) the GCC */
function panelB(w, ph, V) {
  const a0 = arrive(.04);
  sub('b', 18, PB.y - 20, 'cross-correlation', a0);
  const A = axes({ x: PB.x, y: PB.y, w: PB.w, h: PB.h, xlim: [-250, 250], ylim: [-1.15, 1.15],
                   xticks: [-250, -125, 0, 125, 250], yticks: [-1, 0, 1], xlabel: '\\rm{lag\\ \\ (ms)}',
                   ylabel: '\\rm{GCC}', ylabelGap: 44, tickSize: 16, labelSize: 17, progress: seg(.06, .35) });
  const ga = clamp(seg(.06, .35) * 1.4), XT = A.X(D.tau * 1e3), fade = ph.k === -1 ? 1 - ph.e : 1;
  A.inside(() => {
    line([[PB.x, A.Y(0)], [PB.x + PB.w, A.Y(0)]], { color: C.rule, width: 1, alpha: ga });
    line([[XT, PB.y], [XT, PB.y + PB.h]], { color: C.guide, width: 1, dash: [5, 4], alpha: ga });
  });
  const sweep = P(ph, 'delay', .3, 1), off = w.i * NL;
  if (sweep > 0) {
    const n = Math.max(2, Math.round(sweep * NL)), pts = [];
    for (let q = 0; q < n; q++) pts.push([A.X((q - D.maxlag) * 1e3 / FS), A.Y(GCC[off + q] / 127)]);
    A.inside(() => line(pts, { color: C.navy, width: 2.2, alpha: fade }));
  }
  // the estimate: once the sweep has passed the peak
  const tq = D.di[w.i] + D.maxlag, ma = V.d;
  const tauHat = D.d[w.i] * 1e3 / FS, xm = A.X(tauHat), ym = A.Y(GCC[off + tq] / 127);
  if (ma > 0) {
    A.inside(() => line([[xm, ym + 6], [xm, PB.y + PB.h]], { color: C.accent, width: 1.4, alpha: ma }));
    dot(xm, ym, 4.5, { color: '#fff', fill: C.accent, width: 1.4, alpha: ma });
  }
  // the readout: estimate against the truth
  const ra = ma * a0, rx = PB.x + PB.w;
  const tt = `\\rm{true}\\ \\tau\\ = ${num(D.tau * 1e3, 0)}\\ \\rm{ms}`;
  const wt = math(tt, rx, PB.y - 20, { size: 16, color: C.body, align: 'right', alpha: a0 });
  if (ra > 0) amath([['\\tau', 'hat'], [` = ${num(tauHat, M2 ? 1 : 0)}\\ \\rm{ms,}\\ \\ `]], rx - wt - 4, PB.y - 20,
                    { size: 16, color: C.accent, align: 'right', alpha: ra });
}

/* ================================================ (c) the spectra and the gain */
function panelC(w, ph) {
  const a0 = arrive(.08), XF = f => PC.x + f / 40 * PC.w;
  sub('c', PC.x - 76, PC.y - 20, 'Wiener filter', a0);
  const top = axes({ x: PC.x, y: PC.y, w: PC.w, h: PC.h1, xlim: [0, 40], ylim: [-40, 0], xticks: [0, 10, 20, 30, 40],
                     yticks: [-40, -20, 0], xfmt: () => '', ylabel: '\\rm{dB}', ylabelGap: 40, tickSize: 16, labelSize: 17,
                     progress: seg(.08, .35) });
  const bot = axes({ x: PC.x, y: PC.y2, w: PC.w, h: PC.h2, xlim: [0, 40], ylim: [0, 1], xticks: [0, 10, 20, 30, 40],
                     yticks: [0, 1], xlabel: '\\rm{frequency}\\ \\ f\\ \\ (\\rm{Hz})', ylabel: 'G,\\ \\gamma^2', ylabelGap: 40,
                     tickSize: 16, labelSize: 17, progress: seg(.1, .35) });
  const fade = ph.k === -1 ? 1 - ph.e : 1, fb = k => k * FS / D.lg, so = w.i * 2 * NB;
  // the coherence of the two records: what weights the GCC (with the delay)
  const pc = P(ph, 'delay', 0, .45);
  if (pc > 0) {
    const pts = []; for (let k = 0; k < NB; k++) pts.push([XF(fb(k)), bot.Y(COH[w.i * NB + k] / 255)]);
    bot.inside(() => line(pts, { color: C.navy, width: 1.3, dash: [4, 3], progress: pc, alpha: fade }));
  }
  // after alignment: the average's spectrum, what both share, and the gain it gives
  const p1 = P(ph, 'Wiener', 0, .4), p2 = P(ph, 'Wiener', .15, .55), p3 = P(ph, 'Wiener', .35, .8);
  const curve = (o, col, wd, p) => {
    if (p <= 0) return;
    const pts = [];
    for (let k = 1; k < NB; k++) { const q = SPEC[so + o + k]; pts.push([XF(fb(k)), top.Y(q === -128 ? -60 : q / 2)]); }
    top.inside(() => line(pts, { color: col, width: wd, progress: p, alpha: fade }));
  };
  curve(0, C.guide, 1.6, p1);
  curve(NB, C.navy, 2.2, p2);
  if (p3 > 0) {
    const pts = [[XF(0), bot.Y(0)]];
    for (let k = 0; k < NB; k++) pts.push([XF(fb(k)), bot.Y(w.G[k])]);
    pts.push([XF(fb(NB - 1)), bot.Y(0)]);
    bot.inside(() => {
      ctx.save(); ctx.globalAlpha *= p3 * fade * .85; ctx.fillStyle = C.steel2; ctx.beginPath();
      pts.forEach((p, q) => q ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath(); ctx.fill(); ctx.restore();
      line(pts.slice(1, -1), { color: C.blue, width: 1.6, alpha: p3 * fade });
    });
  }
  // which line is which
  const ka = arrive(.42), ky = PC.y - 20;
  const items = [[x => line([[x, ky - 5], [x + 22, ky - 5]], { color: C.guide, width: 1.6, alpha: ka }), '\\rm{average}', 28],
                 [x => line([[x, ky - 5], [x + 22, ky - 5]], { color: C.navy, width: 2.2, alpha: ka }), '\\rm{common}', 28],
                 [x => line([[x, ky - 12], [x + 14, ky - 12], [x + 14, ky], [x, ky]], { color: C.blue, width: 1, fill: C.steel2, close: true, alpha: ka }), 'G', 20],
                 [x => line([[x, ky - 5], [x + 22, ky - 5]], { color: C.navy, width: 1.3, dash: [4, 3], alpha: ka }), '\\gamma^2', 28]];
  let kx = PC.x + PC.w;
  for (let q = items.length - 1; q >= 0; q--) {
    const [mark, words, mw] = items[q];
    kx -= math(words, 0, -1e4, { size: 16, alpha: 0 });
    math(words, kx, ky, { size: 16, color: C.body, alpha: ka });
    kx -= mw;
    mark(kx);
    kx -= 14;
  }
}

/* ================================================ the stages, the controls, the numbers */
function stages(ph) {
  stageChips();
  const cur = ph.k === -1 ? 0 : ph.k;
  STX.forEach((c, k) => {
    const a = arrive(.02 * k);
    uiChip(c.x, STG.y, c.w, STG.h, (k + 1) + '  ' + NAMES[k], { on: k === cur, hover: HOVER.type === 'stage' && HOVER.i === k,
           down: DOWN.type === 'stage' && DOWN.i === k, size: 16 }, a);
    if (k < K - 1) arrow(c.x + c.w + 5, STG.y + STG.h / 2, c.x + c.w + STG.gap - 5, STG.y + STG.h / 2,
                         { color: C.guide, width: 1.1, head: 7, alpha: a });
  });
}
/* how far the stage has run: a hairline under its chip (drawn over the frame kept in a hold) */
function hairline(ph) {
  if (STILL || ph.k < 0 || !STX.length) return;
  const c = STX[ph.k], y = STG.y + STG.h + 5;
  line([[c.x, y], [c.x + c.w * clamp(ph.frac), y]], { color: C.navy, width: 2, alpha: arrive(.2) });
}
function slider(a) {
  const n = NS - 1, X = q => SL.x0 + q / n * (SL.x1 - SL.x0), hx = X(SI);
  text(M2 ? 'SNR of one shot' : 'SNR of each record', CX0, SL.y - 20, { size: 16, color: C.body, alpha: a });
  line([[SL.x0, SL.y], [SL.x1, SL.y]], { color: C.rule, width: 3, alpha: a });
  line([[SL.x0, SL.y], [hx, SL.y]], { color: C.mist, width: 3, alpha: a });
  for (let q = 0; q <= n; q++) line([[X(q), SL.y - 5], [X(q), SL.y + 5]], { color: C.rule, width: 1, alpha: a });
  for (let q = 0; q <= n; q += 2) math(num(D.snrs[q], 0), X(q), SL.y + 25, { size: 16, color: C.muted, align: 'center', alpha: a });
  dot(hx, SL.y, HOVER.type === 'slider' || DRAG ? 8.5 : 7.5, { color: C.navy, fill: '#fff', width: 2, alpha: a });
  math(`${num(D.snrs[SI], 0)}\\ \\rm{dB}`, SL.x1 + 18, SL.y + 6, { size: 16, alpha: a });
}
function kinds(a) {
  text('signal', CX0, KC.y + KC.h / 2 + 5, { size: 16, color: C.body, alpha: a });
  let x = KC.x;
  D.kinds.forEach((s, k) => {
    uiChip(x, KC.y, KC.w[k], KC.h, s, { on: k === KI, hover: HOVER.type === 'kind' && HOVER.i === k, down: DOWN.type === 'kind' && DOWN.i === k, size: 16 }, a);
    x += KC.w[k] + KC.gap;
  });
}
const kindX = k => KC.x + KC.w.slice(0, k).reduce((s, v) => s + v + KC.gap, 0);
/* when the numbers a stage gives are on: the delay once the sweep has found the peak, the estimate's
   with its stage; both leave with the return to the clean signal */
function shown(ph, w) {
  if (ph.k === -1) return { d: 1 - ph.e, e: 1 - ph.e };
  const sweep = P(ph, 'delay', .3, 1), tq = D.di[w.i] + D.maxlag;
  const d = P(ph, 'delay') >= 1 ? 1 : sweep * NL >= tq + 1 ? clamp((sweep * NL - tq) / 12) : 0;
  return { d, e: P(ph, 'estimate') };
}
/* Figure 12: the numbers of the choice shown */
function numbers1(w, V) {
  const x = 18, y = BOT + 8, i = w.i, a = arrive(.45), x1 = 106, x2 = 262;
  text('delay', x, y, { size: 16, color: C.body, alpha: a });
  amath([['\\tau', 'hat'], [` = ${num(D.d[i] * 2, 0)}\\ \\rm{ms}`]], x1, y, { size: 16, color: C.accent, alpha: a * V.d });
  math('\\rm{true}\\ \\tau\\ = 48\\ \\rm{ms;\\ one\\ sample}\\ = 2\\ \\rm{ms}', x2, y, { size: 16, color: C.muted, alpha: a });
  text('estimate', x, y + 30, { size: 16, color: C.body, alpha: a });
  math(`\\rho\\ = ${num(D.rho[i][0], 3)},\\ ${num(D.rho[i][1], 3)}`, x1, y + 30, { size: 16, alpha: a * V.e });
  amath([['\\rm{correlation of}\\ '], ['s', 'hat'], ['(t)\\ \\rm{and}\\ '], ['s', 'hat'], ['(t - '], ['\\tau', 'hat'],
         [')\\ \\rm{with the truth}']], x2, y + 30, { size: 16, color: C.muted, alpha: a * V.e });
  text('SNR', x, y + 60, { size: 16, color: C.body, alpha: a });
  // the gain as the two rounded numbers shown give it
  const so = D.so[i], fin = so > -99, r1 = Math.round(D.rs[i][0] * 10) / 10, s1 = Math.round(so * 10) / 10;
  // an estimate that does not follow the signal has no SNR or gain to speak of
  const lost = !fin || Math.abs(D.rho[i][0]) < .1;
  math(`${num(r1, 1)}\\ \\rm{dB}` + (lost ? '' : `\\ \\to\\ ${num(s1, 1)}\\ \\rm{dB}`), x1, y + 60, { size: 16, alpha: a * V.e });
  math(lost ? '\\rm{the estimate does not follow the signal}' : `\\rm{sensor 1 to estimate: a gain of}\\ ${num(s1 - r1, 1)}\\ \\rm{dB}`,
       x2, y + 60, { size: 16, color: C.muted, alpha: a * V.e });
}
/* Figure 13: what averaging buys, for every number of shots */
function table2(w, V) {
  const a = arrive(.45), x = 18, cx = q => MC.x + MC.w / 2 + q * MC.pitch, y0 = MC.y + MC.h + 25, dy = 24;
  const at = q => sidx(w.ki, w.si, q), right = cx(NM - 1) + MC.pitch / 2;
  text('shots', x, MC.y + MC.h / 2 + 5, { size: 16, color: C.body, alpha: a });
  math('M', x + 46, MC.y + MC.h / 2 + 5, { size: 16, color: C.body, alpha: a });
  D.shots.forEach((m, q) => uiChip(MC.x + q * MC.pitch, MC.y, MC.w, MC.h, thou(m),
    { on: q === MI, hover: HOVER.type === 'shots' && HOVER.i === q, down: DOWN.type === 'shots' && DOWN.i === q, size: 16 }, a));
  const gain = q => (D.rs[at(q)][0] + D.rs[at(q)][1] - D.rs[at(0)][0] - D.rs[at(0)][1]) / 2;
  const rows = [
    [[['10\\ \\rm{log}_{10}\\ M\\ \\ (\\rm{dB})']], q => num(D.gain_th[q], 1), 1, C.muted],
    [[['\\rm{gain, measured\\ \\ (dB)}']], q => num(gain(q), 1), 1, C.ink],
    [[['\\rm{delay}\\ '], ['\\tau', 'hat'], ['\\ \\ (\\rm{ms})']], q => num(D.d[at(q)] * 2, 1), V.d, C.ink],
    [[['\\rm{correlation}\\ \\rho']], q => num(D.rho[at(q)][0], 2), V.e, C.ink]];
  // the chosen column, behind its numbers
  ctx.save(); ctx.globalAlpha *= a * .75; ctx.fillStyle = C.steel;
  ctx.fillRect(cx(MI) - MC.pitch / 2 + 5, y0 - 18, MC.pitch - 10, dy * rows.length + 2); ctx.restore();
  line([[x, y0 - 20], [right, y0 - 20]], { color: C.ink, width: 1.3, alpha: a });
  rows.forEach(([lab, val, ra, col], r) => {
    const y = y0 + r * dy;
    amath(lab, x, y, { size: 16, color: C.body, alpha: a });
    for (let q = 0; q < NM; q++) math(val(q), cx(q), y, { size: 16, align: 'center', color: col, alpha: a * ra });
  });
  line([[x, y0 + rows.length * dy - 14], [right, y0 + rows.length * dy - 14]], { color: C.ink, width: 1.3, alpha: a });
  // from which number of shots on the delay stays within a sample of 48 ms
  let from = NM;
  for (let q = NM - 1; q >= 0; q--) { if (Math.abs(D.d[at(q)] - D.dtrue) < 1) from = q; else break; }
  const note = from === 0 ? '\\rm{delay within one sample of 48 ms at every}\\ M'
    : from === NM ? '\\rm{delay not within one sample of 48 ms at any}\\ M'
    : `\\rm{delay within one sample of 48 ms from}\\ M = ${thou(D.shots[from])}\\ \\rm{on}`;
  math(note, x, y0 + rows.length * dy + 8, { size: 16, color: C.body, alpha: a * V.d });
}

/* while a stage holds, nothing but its hairline moves: the frame is kept and drawn again from
   memory (the dense noisy records are the costly strokes). Not for the still or the overlap check. */
const OFF = document.createElement('canvas');
let OFFKEY = '';
function frameKey(ph) {
  if (CHECK || STILL || ph.k < 0 || ph.e < 1 || t < 1.6 || (ph.k === 0 && t < PERIOD && t < 2)) return '';
  return [cv.width, cv.height, ph.k, KI, SI, MI, HOVER.type, HOVER.i, DOWN.type, DOWN.i, DRAG].join(':');
}
function draw() {
  const ph = phase(), key = frameKey(ph);
  if (key && key === OFFKEY) {
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.drawImage(OFF, 0, 0); ctx.restore();
    hairline(ph); place();
    return;
  }
  const w = waves(cur()), V = shown(ph, w);
  stages(ph);
  panelA(w, ph);
  panelB(w, ph, V);
  panelC(w, ph);
  const ca = arrive(.5);
  slider(ca);
  kinds(ca);
  if (M2) table2(w, V); else numbers1(w, V);
  math(D.params, 18, H - 14, { size: 15, color: C.muted, alpha: arrive(.55) });
  if (key) {
    OFF.width = cv.width; OFF.height = cv.height;
    OFF.getContext('2d').drawImage(cv, 0, 0); OFFKEY = key;
  }
  hairline(ph);
  place();
}

/* ================================================ the reader's hand: pointer and keyboard */
const FIG = document.querySelector('.fig'), KB = { st: [], kd: [], ms: [], sl: null, key: '' };
function toUnits(e) { const r = cv.getBoundingClientRect(); return [(e.clientX - r.left) * W / r.width, (e.clientY - r.top) * H / r.height]; }
function redraw() { if (!playing) render(); }
function hit(X, Y) {
  if (STILL) return { type: '', i: -1 };
  for (let k = 0; k < STX.length; k++) {
    const c = STX[k];
    if (X >= c.x - STG.gap / 2 && X <= c.x + c.w + STG.gap / 2 && Y >= 0 && Y <= STG.y + STG.h + 10) return { type: 'stage', i: k };
  }
  if (Math.abs(Y - SL.y) < 20 && X > SL.x0 - 14 && X < SL.x1 + 14) return { type: 'slider', i: -1 };
  for (let k = 0; k < D.kinds.length; k++)
    if (X >= kindX(k) - KC.gap / 2 && X <= kindX(k) + KC.w[k] + KC.gap / 2 && Y >= KC.y - 8 && Y <= KC.y + KC.h + 8) return { type: 'kind', i: k };
  if (M2) for (let q = 0; q < NM; q++)
    if (X >= MC.x + q * MC.pitch - 8 && X <= MC.x + q * MC.pitch + MC.w + 8 && Y >= MC.y - 10 && Y <= MC.y + MC.h + 10) return { type: 'shots', i: q };
  return { type: '', i: -1 };
}
/* a new choice holds the stage shown for a whole hold, so it can be looked at; it never pauses */
function hold() {
  const ph = phase();
  if (!playing || ph.k < 0) return;
  const c = t < PERIOD ? 0 : Math.floor(t / PERIOD);
  t = c * PERIOD + done(ph.k) + .01;
  if (c === 0 && t < 1.6) t = 1.6;
}
function choose(type, i) {
  if (type === 'kind') KI = i;
  else if (type === 'shots') MI = i;
  else if (type === 'snr') SI = clamp(i, 0, NS - 1);
  else if (type === 'stage') { t = PERIOD + (playing ? START[i] + .01 : done(i) + .01); render(); return; }
  hold(); render();
}
const snrAt = X => Math.round(clamp((X - SL.x0) / (SL.x1 - SL.x0)) * (NS - 1));
let PRESS = '';
if (!STILL) {
  const css = document.createElement('style');
  /* a stand-in covers its control's hit area (24 CSS px at least at the page's 672 px); its focus
     ring hugs the drawn chip, 3 units outside it (::after, set by place) */
  css.textContent = '.nfk{position:absolute;margin:0;padding:0;border:0;background:transparent;pointer-events:none;' +
    'outline:none;color:transparent;font:inherit;overflow:visible}' +
    '.nfk::after{content:"";position:absolute;left:var(--l,0);top:var(--t,0);right:var(--r,0);bottom:var(--b,0);pointer-events:none}' +
    '.nfk:focus-visible::after{outline:2px solid #095A94;outline-offset:2px}';
  document.head.appendChild(css);
  const ctl = FIG.querySelector('.ctl');
  const add = (parent, role, label) => {
    const el = document.createElement(role === 'slider' ? 'div' : 'button'); el.className = 'nfk';
    if (role !== 'slider') el.type = 'button';
    el.setAttribute('role', role); if (label) el.setAttribute('aria-label', label);
    parent === FIG ? FIG.insertBefore(el, ctl) : parent.appendChild(el);
    return el;
  };
  const group = label => { const g = document.createElement('div'); g.setAttribute('role', 'radiogroup'); g.setAttribute('aria-label', label); FIG.insertBefore(g, ctl); return g; };
  const roving = (list, i, pick) => e => {
    const dd = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key], n = list.length;
    const j = e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : dd ? (i + dd + n) % n : (e.key === 'Enter' || e.key === ' ') ? i : -1;
    if (j < 0) return;
    e.preventDefault(); list[j].focus(); pick(j);
  };
  const gS = group('Stage of the method');
  NAMES.forEach((s, k) => { const b = add(gS, 'radio', `Stage ${k + 1}: ${s}`); b.addEventListener('keydown', roving(KB.st, k, j => choose('stage', j))); KB.st.push(b); });
  const gK = group('Signal');
  D.kinds.forEach((s, k) => { const b = add(gK, 'radio', `Signal: ${s}`); b.addEventListener('keydown', roving(KB.kd, k, j => choose('kind', j))); KB.kd.push(b); });
  if (M2) {
    const gM = group('Number of shots averaged');
    D.shots.forEach((m, q) => { const b = add(gM, 'radio', `${m} shot${m > 1 ? 's' : ''}`); b.addEventListener('keydown', roving(KB.ms, q, j => choose('shots', j))); KB.ms.push(b); });
  }
  KB.sl = add(FIG, 'slider', M2 ? 'SNR of one shot, dB' : 'SNR per record, dB');
  KB.sl.tabIndex = 0;
  KB.sl.setAttribute('aria-valuemin', String(D.snrs[0])); KB.sl.setAttribute('aria-valuemax', String(D.snrs[NS - 1]));
  KB.sl.addEventListener('keydown', e => {
    const dd = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 2, PageDown: -2 }[e.key];
    const q = e.key === 'Home' ? 0 : e.key === 'End' ? NS - 1 : dd ? SI + dd : -1;
    if (q < 0 || q === SI) { if (dd) e.preventDefault(); return; }
    e.preventDefault(); choose('snr', q);
  });
  cv.style.touchAction = 'pan-y pinch-zoom';
  cv.addEventListener('pointermove', e => {
    const [X, Y] = toUnits(e);
    if (DRAG) { const q = snrAt(X); if (q !== SI) choose('snr', q); return; }
    if (e.pointerType !== 'mouse') return;
    const h = hit(X, Y);
    cv.style.cursor = h.type ? 'pointer' : '';
    if (h.type !== HOVER.type || h.i !== HOVER.i) { HOVER.type = h.type; HOVER.i = h.i; redraw(); }
  });
  cv.addEventListener('pointerleave', () => { if (DRAG) return; HOVER.type = ''; HOVER.i = -1; DOWN.type = ''; cv.style.cursor = ''; redraw(); });
  cv.addEventListener('pointerdown', e => {
    const [X, Y] = toUnits(e), h = e.button === 0 ? hit(X, Y) : { type: '', i: -1 };
    PRESS = h.type;
    if (h.type === 'slider') { DRAG = true; cv.setPointerCapture(e.pointerId); const q = snrAt(X); if (q !== SI) choose('snr', q); else redraw(); }
    else if (h.type) { DOWN.type = h.type; DOWN.i = h.i; redraw(); }
  });
  const drop = () => { if (DRAG || DOWN.type) { DRAG = false; DOWN.type = ''; DOWN.i = -1; redraw(); } };
  cv.addEventListener('pointerup', drop);
  cv.addEventListener('pointercancel', drop);
  // a click on a control is a choice and never also pauses (the engine toggles on a click of the canvas)
  FIG.addEventListener('click', e => {
    if (e.target !== cv) return;
    const pr = PRESS; PRESS = '';
    const [X, Y] = toUnits(e), h = hit(X, Y);
    if (pr === 'slider') { e.stopPropagation(); return; }
    if (h.type && h.type !== 'slider') { if (pr === h.type) choose(h.type, h.i); e.stopPropagation(); return; }
    if (h.type === 'slider') { e.stopPropagation(); return; }
    // a near miss on the controls' own ground does nothing either
    if (Y < STG.y + STG.h + 14 || (Y > BOT - 30 && (X > CX0 - 10 || (M2 && Y < MC.y + MC.h + 12)))) e.stopPropagation();
  }, true);
}
/* the keyboard's stand-ins sit on what they choose, and say what is chosen */
function place() {
  if (STILL || !KB.sl || !STX.length) return;
  const ph = phase(), k = ph.k === -1 ? 0 : ph.k;
  const key = cv.clientWidth + ':' + k + ':' + KI + ':' + SI + ':' + MI;
  if (key === KB.key) return;
  KB.key = key;
  const u = cv.clientWidth / W, px = v => (v * u).toFixed(1) + 'px';
  // each stand-in is the control's hit area (as hit() takes it); [r] is the drawn chip its ring hugs
  const box = (el, x0, y0, x1, y1, r) => {
    el.style.left = px(x0); el.style.top = px(y0); el.style.width = px(x1 - x0); el.style.height = px(y1 - y0);
    el.style.setProperty('--l', px(r[0] - x0)); el.style.setProperty('--t', px(r[1] - y0));
    el.style.setProperty('--r', px(x1 - r[2])); el.style.setProperty('--b', px(y1 - r[3]));
  };
  KB.st.forEach((b, j) => {
    const c = STX[j];
    box(b, c.x - STG.gap / 2 + 1, STG.y - 8, c.x + c.w + STG.gap / 2 - 1, STG.y + STG.h + 8, [c.x, STG.y, c.x + c.w, STG.y + STG.h]);
    b.setAttribute('aria-checked', String(j === k)); b.tabIndex = j === k ? 0 : -1;
  });
  KB.kd.forEach((b, j) => {
    box(b, kindX(j) - KC.gap / 2, KC.y - 8, kindX(j) + KC.w[j] + KC.gap / 2, KC.y + KC.h + 8, [kindX(j), KC.y, kindX(j) + KC.w[j], KC.y + KC.h]);
    b.setAttribute('aria-checked', String(j === KI)); b.tabIndex = j === KI ? 0 : -1;
  });
  KB.ms.forEach((b, j) => {
    const x = MC.x + j * MC.pitch;
    box(b, x - 6, MC.y - 6, x + MC.w + 6, MC.y + MC.h + 6, [x, MC.y, x + MC.w, MC.y + MC.h]);
    b.setAttribute('aria-checked', String(j === MI)); b.tabIndex = j === MI ? 0 : -1;
  });
  box(KB.sl, SL.x0 - 14, SL.y - 19, SL.x1 + 14, SL.y + 19, [SL.x0 - 10, SL.y - 14, SL.x1 + 10, SL.y + 14]);
  const i = cur();
  KB.sl.setAttribute('aria-valuenow', String(D.snrs[SI]));
  KB.sl.setAttribute('aria-valuetext', `${D.snrs[SI]} dB: estimated delay ${num(D.d[i] * 2, M2 ? 1 : 0)} ms, correlation ${num(D.rho[i][0], 2)}`);
}
boot();
"""
