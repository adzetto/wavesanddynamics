"""The probability deck's card, redrawn as a moving figure (round 12).

The client, of the Big Picture page: the picture standing for Probability &
Statistics was slide 1 itself; make it something animated. So
tools/numfig/pr_overview.py draws slide 1's four connected questions as four
computations in the figures' family (content/anim/nf-pr-overview.html): his
concrete strength model with its tests falling out of it, the histogram and
the normal model fitted to them, his random walk of sensor bias in its
pointwise 95% band, and the running mean closing on the true mean as its 95%
interval narrows; his arrows and their words between them. tools/bp_art.py
cuts its still for the card. The figure is in no document, so no fragment
maps it.
"""

import base64
import html
import json
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANIM = os.path.join(ROOT, "content", "anim")
DECK = os.path.join(ROOT, "tools", "deck", "src")
NUMFIG = os.path.join(ROOT, "tools", "numfig")
NAME = "nf-pr-overview"
KEY = "probability-statistics.html"


def page():
    with open(os.path.join(ANIM, NAME + ".html"), encoding="utf-8") as fh:
        return fh.read()


def data():
    return json.loads(re.search(r"^const DATA = (\{.*\});$", page(), re.M).group(1))


def figure_js():
    """The figure's own script: after the engine, from its first line."""
    return page().split("<script>", 1)[1].split("const D = DATA;", 1)[1]


def f32(s):
    return np.frombuffer(base64.b64decode(s), "<f4").astype(float)


def his(name):
    with open(os.path.join(DECK, name), encoding="utf-8") as fh:
        return html.unescape(re.sub(r"<[^>]+>", " ", fh.read()))


# ---------------------------------------------------------------- the page

def test_the_page_is_a_numfig_figure_in_computer_modern():
    text = page()
    assert "<title>Probability, statistics and estimation</title>" in text     # the deck's title
    assert "const W = 1000, H = 562;" in text                                    # 16:9 to half a unit
    # the engine inlined, its type loaded before the first frame
    assert '"CMU Serif", "Figure Math"' in text and "function boot()" in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "../fonts/figure-math.woff2" in text
    assert "document.fonts.load('500 16px \"Figure Math\"'" in text
    assert text.rstrip().endswith("boot();\n</script>\n</body>\n</html>")
    # no other face, and the figure sets type only through the engine's text() and math()
    for face in ("Calibri", "Arial", "Helvetica", "Cambria", "Segoe", "sans-serif"):
        assert face not in text, face
    js = figure_js()
    assert "ctx.font" not in js and ".font =" not in js
    # colours from the palette only (white paper aside), no orange
    assert set(re.findall(r"#[0-9A-Fa-f]{3,6}\b", js)) <= {"#fff"}
    for warm in ("#A5510B", "#D9822B", "#F2C39A", "#FBEBDD", "#7B3D0C"):
        assert warm.lower() not in text.lower()
    # our copy: no em dash, no spaced en dash, no address
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)


def test_every_sign_it_sets_has_a_computer_modern_glyph():
    ttLib = pytest.importorskip("fontTools.ttLib")
    fonts = os.path.join(ROOT, "content", "fonts-cmu")
    have = set(ttLib.TTFont(os.path.join(fonts, "cmu-serif-500-roman.woff2")).getBestCmap())
    have |= set(ttLib.TTFont(os.path.join(fonts, "figure-math.woff2")).getBestCmap())
    script = page().split("<script>", 1)[1]
    assert not {ch for ch in script if ord(ch) > 126 and ord(ch) not in have}


def test_it_prints_its_frame_whole_at_16_9():
    from PIL import Image
    with Image.open(os.path.join(ANIM, NAME + ".webp")) as im:
        assert im.size == (1344, 756)
        px = np.asarray(im.convert("L"))
    assert (px < 128).mean() > 0.01                  # a drawn frame, not a blank one
    # the poster: all four under way, the tests still falling
    d = data()
    u = d["poster"] - d["t0"]
    landed = int(np.exp((u - d["fall"]) / d["run"] * np.log(1000)) + 1e-9)
    left = int(np.exp(u / d["run"] * np.log(1000)) + 1e-9)
    assert 100 <= landed < left < 1000 and u < d["run"]


# ---------------------------------------------------------------- his words

def test_its_words_are_his_verbatim():
    slide1 = " ".join(his("s001.html").split())
    # his four questions' names and his arrows' words (each arrow's words on two lines)
    for w in ("Probability", "Statistics", "Stochastic processes", "Estimation",
              "learn and check a model", "model + observations"):
        assert w in slide1, w
    js = figure_js()
    for w in ("'Probability'", "'Statistics'", "'Stochastic processes'", "'Estimation'",
              "'learn and'", "'check a model'", "'model +'", "'observations'"):
        assert w in js, w
    # the words inside his charts it borrows, each from the slide it names
    for name, words in (("s013.pic.txt", ["Lower 5%", "Fitted normal model"]),
                        ("s051.pic.txt", ["Pointwise 95% band", "Sensor bias (mm)"]),
                        ("s015.pic.txt", ["Fixed true mean", "Mean strength (MPa)"]),
                        ("s016.pic.txt", ["Strength (MPa)", "Density"])):
        with open(os.path.join(DECK, name), encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        for w in words:
            assert w in lines, (name, w)
            assert w in js, w
    assert "95% CI" in his("s017.html") and "'95% CI'" in js


# ---------------------------------------------------------------- the model

def test_the_model_is_his_running_examples():
    from scipy import stats
    d = data()
    # one cylinder: N(32, 3^2) MPa (slides 16 to 21), its lower 5% (slide 13)
    assert (d["mu"], d["sigma"]) == (32, 3)
    assert d["q05"] == pytest.approx(32 + 3 * stats.norm.ppf(0.05), abs=1e-4)
    assert d["z"] == pytest.approx(stats.norm.ppf(0.975), abs=1e-5)
    # his 2 MPa bins, 19 to 45 MPa
    assert (d["e0"], d["bw"], d["nb"]) == (19, 2, 13)
    # the 1000 tests: seed 2, the first from 1 whose running 95% interval holds
    # the true mean at every n
    x = f32(d["x"])
    assert np.allclose(x, np.random.default_rng(2).normal(32, 3, 1000), atol=1e-5)
    n = np.arange(1, 1001)

    def misses(v):
        return np.sum(np.abs(np.cumsum(v) / n - 32) > stats.norm.ppf(0.975) * 3 / np.sqrt(n))

    assert misses(x) == 0 and misses(np.random.default_rng(1).normal(32, 3, 1000)) > 0
    assert 19 < x.min() and x.max() < 45
    # his four walks of slide 51, the same numbers
    w = f32(d["walk"]).reshape(4, 161)
    rng = np.random.default_rng(5101)
    want = np.concatenate([np.zeros((4, 1)), np.cumsum(rng.normal(0, 0.3, (4, 160)), axis=1)], axis=1)
    assert np.allclose(w, want, atol=1e-5)
    assert (d["nk"], d["nstep"], d["rws"]) == (4, 160, 0.3)
    assert round(1.96 * 0.3 * np.sqrt(160), 1) == 7.4                   # his band's end


def test_the_clock_starts_the_physics_at_once_and_loops():
    d = data()
    assert d["t0"] <= 0.6                                    # the physics moves by 0.6 s
    assert d["per"] == pytest.approx(d["run"] + d["fall"] + d["hold"] + d["fade"] + 0.3)
    # the fit appears once there is something to fit, and its words with it
    assert 3 <= d["nfit"] <= 20


def test_the_check_file_reports_the_model_and_a_clean_loop():
    with open(os.path.join(NUMFIG, "pr_overview.check.txt"), encoding="utf-8") as fh:
        txt = fh.read()
    for need in ("his slide 17's 0.6 and 1.176", "largest\n     difference 0.0e+00 mm",
                 "its counts at n = 1000 equal numpy's: True", "all 1000: True",
                 "label pairs that meet 0, strokes through a label 0"):
        assert need in txt, need


# ---------------------------------------------------------------- the card

def test_the_card_is_its_still_and_no_document_draws_it():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bp_art
    from PIL import Image
    # one panel, Probability, which reads at a card's 190px where the whole
    # poster of four was grey texture (the audit of 5 Oct 2026)
    box = (15, 0, 585, 335)
    assert bp_art.PICKS[KEY] == ("content:anim/nf-pr-overview.webp", "probability-deck", box, "alone")
    folder = os.path.join(ROOT, "content", "bigpicture")
    with open(os.path.join(folder, "art.json"), encoding="utf-8") as fh:
        assert json.load(fh)[KEY] == ["probability-deck.webp", 640, 360]
    with Image.open(os.path.join(ANIM, NAME + ".webp")) as im:
        im = im.convert("RGB")
        want = bp_art.cut(im, bp_art.fit(box, im.size, 16 / 9, True), box).resize((640, 360), Image.LANCZOS)
    with Image.open(os.path.join(folder, "probability-deck.webp")) as got:
        got = np.asarray(got.convert("RGB"), float)
    assert np.abs(got - np.asarray(want, float)).mean() < 3        # its panel of the still (WebP aside)
    with Image.open(os.path.join(ROOT, "content", "deck-probstat", "web", "s001-1600.webp")) as s1:
        slide = np.asarray(s1.convert("RGB").resize((640, 360), Image.LANCZOS), float)
    assert np.abs(got - slide).mean() > 10                        # no longer slide 1
    # in no document: no fragment names it
    for n in os.listdir(ANIM):
        if re.fullmatch(r"anim(\.[\w-]+)?\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                assert NAME + ".html" not in fh.read(), n


def test_the_photons_card_takes_its_redraw_once_there_is_one():
    # agent photons redraws the piece's one figure (nf-ph-slits); its card shows
    # the panel with the fringes, cut about the axis, once the still exists
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bp_art
    pick = bp_art.PICKS["from-bridges-to-photons"]
    if os.path.isfile(os.path.join(ANIM, "nf-ph-slits.webp")):
        assert pick == ("content:anim/nf-ph-slits.webp", "photons", (0, 187, 668, 563), "alone")
    else:
        assert pick[0].startswith("fig/from-bridges-to-photons/")


# ---------------------------------------------------------------- nothing overlaps

def test_nothing_overlaps_across_its_loop():
    pytest.importorskip("playwright.sync_api")
    sys.path.insert(0, NUMFIG)
    import common
    times = [0.5, 0.8, 1.2, 2.0, 3.5, 5.0, 7.0, 8.5, 9.9, 10.5, 12.0, 12.9]
    try:
        got = common.overlaps("pr-overview", times)
    except Exception as e:                                         # no browser here
        pytest.skip(f"playwright cannot run: {e}")
    assert {k: v for k, v in got.items() if v["labels"] or v["crossings"]} == {}
