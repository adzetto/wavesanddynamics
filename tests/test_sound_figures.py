"""The sound document's three figures, redrawn from models (round 12).

"Understanding Sound Classification, Localization and Tracking and
Similarity to NDT" had three borrowed pictures. tools/numfig/snd_array.py,
snd_kalman.py and snd_denoise.py redraw them in the figures' one style:
Computer Modern through the numfig engine, the palette C, and every
distance, delay, Gaussian and spectrogram computed. content/anim/
anim.sound.json puts each where his picture stood; his captions stay.
"""

import html
import json
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))
sys.path.insert(0, os.path.join(ROOT, "tools", "numfig"))

import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
NUMFIG = os.path.join(ROOT, "tools", "numfig")
SLUG = "sound-detection-and-tracking"
PAGES = {
    "nf-snd-array.html": ("Figure 1: Sensor configurations: (a) linear array sensors (b) circular array sensors",
                          1000, 556, "image1"),
    "nf-snd-kalman.html": ("Figure 2: How Kalman Filter estimates the next location of the target (system) by "
                           "statistically combining next measurement point with an estimate obtained from a model",
                           1000, 616, "image2"),
    "nf-snd-denoise.html": ("Figure 3: A background noise-reduction algorithm", 1000, 600, "image3"),
}
C_AIR = 343.0


def page(name):
    with open(os.path.join(ANIM, name), encoding="utf-8") as fh:
        return fh.read()


def data(name):
    m = re.search(r"^const DATA = (\{.*\});$", page(name), re.M)
    return json.loads(m.group(1))


# ------------------------------------------------------------------ the pages

@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_page_is_a_numfig_page_in_computer_modern_and_nothing_else(name):
    text = page(name)
    title, w, h, _ = PAGES[name]
    assert f"<title>{html.escape(title, quote=False)}</title>" in text
    assert f"const W = {w}, H = {h};" in text
    # the engine is inlined, and the figure starts once the type has loaded
    assert "function boot()" in text and text.count("boot()") >= 2
    assert '"CMU Serif", "Figure Math"' in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "../fonts/figure-math.woff2" in text
    # no other face, and no font set by hand in the figure's own script
    script = text.split("<script>", 1)[1]
    own = script.split("function boot()", 1)[1]
    assert "ctx.font =" not in own.replace("ctx.font = font(", "")
    low = text.lower()
    for face in ("calibri", "carlito", "cambria", "segoe ui", "arial", "helvetica", "sans-serif"):
        assert face not in low, face
    # the palette: crimson, and none of the old burnt orange
    assert "#a7203a" in low
    for warm in ("#a5510b", "#d9822b", "#f2c39a", "#fbebdd", "#7b3d0c"):
        assert warm not in low
    # our copy: no em dash, no spaced en dash, nothing that reads as an address
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)


@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_prints_a_complete_frame_at_its_ratio(name):
    from PIL import Image
    _, w, h, _ = PAGES[name]
    with Image.open(os.path.join(ANIM, name[:-5] + ".webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * h / w) <= 2
        px = np.asarray(im.convert("L"))
        assert (px < 128).mean() > 0.01            # a drawn figure, not a blank frame


def test_the_fragment_puts_each_figure_where_his_picture_stood():
    with open(os.path.join(ANIM, "anim.sound.json"), encoding="utf-8") as fh:
        frag = json.load(fh)
    assert frag == {SLUG: {stem: name for name, (_, _, _, stem) in PAGES.items()}}
    got = preview.animations("../anim")[SLUG]          # raises if a picture is named twice
    for name, (title, w, h, stem) in PAGES.items():
        assert got[stem]["src"] == f"../anim/{name}"
        assert got[stem]["title"] == title.split(": ", 1)[1]
        assert (got[stem]["w"], got[stem]["h"]) == (w, h)
        assert got[stem]["still"]["src"] == f"../anim/{name[:-5]}.webp"


def test_no_other_fragment_names_these_pictures():
    for n in os.listdir(ANIM):
        if (n == "anim.json" or re.fullmatch(r"anim\.[\w-]+\.json", n)) and n != "anim.sound.json":
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                assert SLUG not in json.load(fh), n


# ------------------------------------------------------------------ the models

def test_figure1_additional_distance_and_delay_follow_from_the_drawn_geometry():
    d = data("nf-snd-array.html")
    a, b = d["a"], d["b"]
    # (a): the front through n still has (p_n - p_m).s to go to m
    pn, pm, th = np.array(a["pn"]), np.array(a["pm"]), a["th"]
    s = np.array([np.cos(th), np.sin(th)])
    dnm = np.linalg.norm(pm - pn)
    beta_n = np.arctan2(pn[1], pn[0])
    u, v = -pn, pm - pn
    gamma = abs(np.arctan2(u[0] * v[1] - u[1] * v[0], u @ v))
    dd = (pn - pm) @ s
    assert a["dd"] == pytest.approx(dd, rel=1e-4)
    assert dd == pytest.approx(dnm * np.cos(th + gamma - beta_n), rel=1e-9)
    assert a["tau"] == pytest.approx(dd / 100 / C_AIR * 1e6, rel=1e-4)       # us
    # the drawn construction: F on m's ray, nF normal to the wave's direction
    F = np.array(a["F"])
    assert np.linalg.norm(F - pm) == pytest.approx(dd, rel=1e-4)
    assert abs((F - pn) @ s) < 1e-4
    # (b): six sensors on a circle, the extra distance from 0 to 2 is d_02 cos(theta + 30 deg)
    pk = np.array(b["pk"])
    rho = np.linalg.norm(pk, axis=1)
    assert np.allclose(rho, rho[0], rtol=1e-4)
    sb = np.array([np.cos(b["th"]), np.sin(b["th"])])
    d02 = np.linalg.norm(pk[2] - pk[0])
    assert d02 == pytest.approx(rho[0] * np.sqrt(3), rel=1e-4)
    assert b["dd"] == pytest.approx(d02 * np.cos(b["th"] + np.pi / 6), rel=1e-4)
    assert b["tau"] == pytest.approx(b["dd"] / 100 / C_AIR * 1e6, rel=1e-4)
    # the front reaches each sensor when p.s says, so in the order 0, 1, 5, 2, 4, 3
    tk = np.array(b["tk"])
    assert list(np.argsort(tk)) == list(np.argsort(-(pk @ sb)))
    assert list(np.argsort(tk)) == [0, 1, 5, 2, 4, 3]
    # and the page moves it at c, time slowed 10^4 (cm per page second)
    assert d["v"] == pytest.approx(C_AIR * 100 / 1e4)
    assert tk[2] - tk[0] == pytest.approx(b["dd"] / d["v"], rel=1e-4)


def test_figure1_delays_are_what_a_correlator_measures():
    import snd_array as S
    r = S.model()
    _, tau_a, tau_b, rel = S.validate(r)
    fs, n = 48000, 8192
    rng = np.random.default_rng(3)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / fs)
    at = lambda delay: np.fft.irfft(X * np.exp(-2j * np.pi * f * delay), n)
    for tau in (tau_a, tau_b):
        assert S.gcc_phat_delay(at(0.0), at(tau), fs) == pytest.approx(tau, abs=0.5e-6)


def test_figure2_is_a_kalman_filter_with_the_gain_between_0_and_1():
    d = data("nf-snd-kalman.html")
    steps = d["steps"]
    assert len(steps) >= 3
    x = np.linspace(-400, 600, 200001)
    for s in steps:
        K = s["sp"] ** 2 / (s["sp"] ** 2 + s["sm"] ** 2)
        assert s["K"] == pytest.approx(K, rel=1e-4) and 0 < s["K"] < 1
        assert s["mu"] == pytest.approx(s["mp"] + K * (s["z"] - s["mp"]), abs=1e-3)
        assert s["su"] == pytest.approx(np.sqrt((1 - K) * s["sp"] ** 2), rel=1e-4)
        # the present estimate is the normalised product of the two Gaussians
        g = np.exp(-.5 * ((x - s["mp"]) / s["sp"]) ** 2 - .5 * ((x - s["z"]) / s["sm"]) ** 2)
        g /= np.trapezoid(g, x)
        m = np.trapezoid(x * g, x)
        assert m == pytest.approx(s["mu"], abs=1e-3)
        assert np.sqrt(np.trapezoid((x - m) ** 2 * g, x)) == pytest.approx(s["su"], rel=1e-4)
        # narrower than either, between the two
        assert s["su"] < min(s["sp"], s["sm"])
        assert min(s["mp"], s["z"]) < s["mu"] < max(s["mp"], s["z"])
    # K moves across its range: an uncertain model, a noisy measurement
    ks = [s["K"] for s in steps]
    assert max(ks) > 0.8 and min(ks) < 0.2


def test_figure2_filter_agrees_with_batch_least_squares():
    import snd_kalman as S
    seed, x0, z, kf = S.pick_seed()
    d = data("nf-snd-kalman.html")
    for s, st in zip(kf["steps"], d["steps"]):
        assert st["mp"] == pytest.approx(s["xp"][0], abs=1e-3) and st["z"] == pytest.approx(s["z"], abs=1e-3)
    # the last state of the whole trajectory solved at once equals the filter's
    n = len(z)
    dim = 2 * (n + 1)
    A = np.zeros((dim, dim))
    b = np.zeros(dim)
    P0i = np.linalg.inv(kf["P0"])
    A[:2, :2] += P0i
    b[:2] += P0i @ kf["x0"]
    Qi = np.linalg.inv(S.Q)
    for k in range(n):
        G = np.zeros((2, dim))
        G[:, 2 * k:2 * k + 2] = -S.F
        G[:, 2 * k + 2:2 * k + 4] = np.eye(2)
        A += G.T @ Qi @ G
        A[2 * k + 2, 2 * k + 2] += 1 / S.SIG_M[k] ** 2
        b[2 * k + 2] += z[k] / S.SIG_M[k] ** 2
    xs = np.linalg.solve(A, b)
    assert np.allclose(xs[-2:], kf["steps"][-1]["x"], atol=1e-8)
    assert np.allclose(np.linalg.inv(A)[-2:, -2:], kf["steps"][-1]["P"], atol=1e-8)


def test_figure3_signals_mix_at_their_ratio_and_the_pictures_are_their_transforms():
    import snd_denoise as S
    r = S.model()
    s, n, x = r["s"], r["n"], r["x"]
    assert 10 * np.log10(np.sum(s ** 2) / np.sum(n ** 2)) == pytest.approx(S.SNR_DB, abs=1e-9)
    assert np.allclose(x, s + n)
    # the transform is linear, and the picture keeps the signal
    assert np.abs(r["Zx"] - r["Zs"] - r["Zn"]).max() < 1e-12 * np.abs(r["Zx"]).max()
    from scipy.signal import istft
    _, xr = istft(r["Zx"], S.FS, window="hann", nperseg=S.NPER, noverlap=S.NPER - S.HOP)
    assert np.abs(xr[:x.size] - x).max() < 1e-12
    # the page's pictures are those spectrograms: 257 frequencies by the frames, one dB scale
    d = data("nf-snd-denoise.html")
    import base64
    import io
    from PIL import Image
    for key, db in (("img_mix", r["dbx"]), ("img_clean", r["dbs"])):
        raw = base64.b64decode(d[key].split(",", 1)[1])
        a = np.asarray(Image.open(io.BytesIO(raw)))
        assert a.shape == (S.NPER // 2 + 1, d["frames"])
        want = np.round(np.clip((db + S.DB_RANGE) / S.DB_RANGE, 0, 1)[::-1] * 255)
        assert np.abs(a.astype(float) - want).max() <= 1
    # the speech's silences are silent: its picture is white there, the mixed one is not
    j = int(np.argmin(np.abs(r["t"] - 0.03)))
    assert np.all(r["dbs"][:, j] < -S.DB_RANGE) and np.median(r["dbx"][:, j]) > -S.DB_RANGE


def test_the_check_files_record_the_models_and_the_overlap_check():
    for name in ("snd_array", "snd_kalman", "snd_denoise"):
        with open(os.path.join(NUMFIG, name + ".check.txt"), encoding="utf-8") as fh:
            txt = fh.read()
        assert "OVERLAP" in txt and "no label meets another, no stroke crosses a label" in txt
    with open(os.path.join(NUMFIG, "snd_denoise.check.txt"), encoding="utf-8") as fh:
        assert "No trained network is claimed" in fh.read()


# ------------------------------------------------------------------ nothing overlaps

MOMENTS = {
    "snd-array": [0.3, 0.8, 1.4, 2.0, 2.6, 3.2, 4.0, 5.0],
    "snd-kalman": [0.3, 0.8, 1.4, 2.0, 3.3, 4.3, 6.9, 9.6, 11.2, 11.9],
    "snd-denoise": [0.3, 0.8, 1.4, 1.9, 3.0, 4.1],
}


@pytest.mark.parametrize("name", sorted(MOMENTS))
def test_nothing_overlaps_at_the_poster_and_through_the_motion(name):
    pytest.importorskip("playwright.sync_api")
    import common
    try:
        got = common.overlaps(name, MOMENTS[name])
    except Exception as e:                       # no browser on this machine
        pytest.skip(f"Playwright could not run: {e}")
    for when, r in got.items():
        assert r["labels"] == [] and r["crossings"] == [], (name, when, r)
