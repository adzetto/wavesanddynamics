"""From Bridges to Photons, Figure 1, redrawn from a wave model (round 12).

His picture (a PNG with sans-serif labels) stood for the double slit as a
mode-shape problem. tools/numfig/ph_slits.py computes it instead: two
finite slits, the 2D Huygens-Fresnel superposition, the field
Re{U e^{-i w t}} moving; (a) |U_A + U_B|^2 with fringes, (b) perpendicular
polarizations, |U_A|^2 + |U_B|^2 smooth; single photons landing with that
probability and a histogram building up to it. The document draws the page
where his picture stood, under his caption.
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
sys.path.insert(0, os.path.join(ROOT, "site"))

import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
NUMFIG = os.path.join(ROOT, "tools", "numfig")
NAME = "nf-ph-slits"
SLUG = "from-bridges-to-photons"
STEM = "194890829817486182cf69528d402bf91b9c2c39"
TITLE = "Figure 1: Double-slit interference as a mode-shape problem"
RICOS = os.path.join(ROOT, "build", "ricos", SLUG)


def page():
    with open(os.path.join(ANIM, NAME + ".html"), encoding="utf-8") as fh:
        return fh.read()


def data():
    return json.loads(re.search(r"^const DATA = (\{.*\});$", page(), re.M).group(1))


def figure_js():
    """The figure's own script: what follows the engine."""
    text = page()
    return text[text.index("const D = DATA;"):]


def arr(s, dtype):
    return np.frombuffer(base64.b64decode(s), dtype=dtype)


# ---------------------------------------------------------------- the page

def test_the_page_is_a_numfig_page_in_computer_modern():
    text = page()
    assert f"<title>{html.escape(TITLE, quote=False)}</title>" in text
    assert "const W = 1000, H = 600;" in text
    # the engine inlined, its type loaded before the first frame
    assert '"CMU Serif", "Figure Math"' in text and "function boot()" in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "../fonts/figure-math.woff2" in text
    assert text.rstrip().endswith("boot();\n</script>\n</body>\n</html>")
    # no other face; the figure sets type only through the engine's text() and math()
    for face in ("Calibri", "Arial", "Helvetica", "Cambria", "Segoe", "sans-serif", "Liberation"):
        assert face not in text, face
    fonts = set(re.findall(r'font-family:"([^"]+)"', text))
    assert fonts == {"CMU Serif", "Figure Math"}
    js = figure_js()
    assert "ctx.font" not in js and ".font =" not in js
    # colours from the palette only: no hex of its own, no orange anywhere
    assert not re.findall(r"#[0-9A-Fa-f]{3,6}\b", js)
    for warm in ("#A5510B", "#D9822B", "#F2C39A", "#FBEBDD", "#7B3D0C"):
        assert warm.lower() not in text.lower()
    assert "C.blue" in js and "C.accent" in js
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


def test_his_words_are_in_it_verbatim():
    js = figure_js()
    for w in ("Path not recorded: fringes", "Paths tagged: no fringes", "Source", "Screen", "Intensity",
              "Same polarization: waves add and cancel at the screen",
              "Perpendicular polarizations at A and B: the two waves cannot cancel"):
        assert f"'{w}'" in js, w
    assert "text('A'," in js and "text('B'," in js
    assert "panel('a'" in js and "panel('b'" in js
    # his polarization arrows: A's vertical in blue, B's horizontal in crimson
    assert re.search(r"arrow\(xa, [^;]*?xa, [^;]*C\.blue[^;]*both: true", js)
    assert re.search(r"arrow\(xa - (\d+), py\(([^)]*)\), xa \+ \1, py\(\2\)[^;]*C\.accent[^;]*both: true", js)


def test_it_prints_its_frame_whole():
    from PIL import Image
    with Image.open(os.path.join(ANIM, NAME + ".webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * 600 / 1000) <= 2
        px = np.asarray(im.convert("RGB")).astype(int)
    assert (px.mean(2) < 128).mean() > 0.01                        # a drawn frame, not a blank
    # both polarizations' colours are in it: (b)'s crimson and the blue
    red = (px[..., 0] > px[..., 2] + 40) & (px[..., 0] > 120)
    blue = (px[..., 2] > px[..., 0] + 40)
    assert red.mean() > 0.002 and blue.mean() > 0.01
    # the poster: every photon has landed on both screens
    d = data()
    for k in ("a", "b"):
        t = arr(d["ph"][k]["t"], "<u2") / 1000
        assert d["tp0"] + t[-1] < d["poster"] < d["tp0"] + d["cycle"] - 0.5


# ---------------------------------------------------------------- the wiring

def test_its_fragment_names_his_picture():
    with open(os.path.join(ANIM, "anim.photons.json"), encoding="utf-8") as fh:
        frag = json.load(fh)
    assert frag == {SLUG: {STEM: NAME + ".html"}}
    got = preview.animations("../anim")[SLUG][STEM]
    assert got["src"] == f"../anim/{NAME}.html"
    assert got["title"] == TITLE.split(": ", 1)[1]
    assert (got["w"], got["h"]) == (1000, 600)
    assert got["still"]["src"] == f"../anim/{NAME}.webp"
    # no other fragment names the picture
    for n in os.listdir(ANIM):
        if re.fullmatch(r"anim(\.[\w-]+)?\.json", n) and n != "anim.photons.json":
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                assert STEM not in fh.read(), n


@pytest.mark.skipif(not os.path.isdir(RICOS), reason="build/ricos is written by tools/docx2ricos.py")
def test_the_stem_is_the_documents_one_picture():
    with open(os.path.join(RICOS, "part-01.json"), encoding="utf-8") as fh:
        ids = re.findall(r'"id":\s*"([0-9a-f]{40})\.png"', fh.read())
    assert ids == [STEM]
    with open(os.path.join(RICOS, "manifest.json"), encoding="utf-8") as fh:
        cap = json.load(fh)["figures"][0]["caption"]
    assert cap.startswith("Figure 1. Double-slit interference as a mode-shape problem.")


# ---------------------------------------------------------------- the model

def test_the_screens_are_the_superposition_the_caption_names():
    d = data()
    Y, dc = d["Y"], d["dc"]
    y = -Y + dc * np.arange(len(d["pa"]))
    pa, pb, pA, pB = (np.array(d[k]) for k in ("pa", "pb", "pA", "pB"))
    # probability densities over the screen (the page keeps five decimals)
    assert np.trapezoid(pa, y) == pytest.approx(1, abs=2e-3)
    assert np.trapezoid(pb, y) == pytest.approx(1, abs=2e-3)
    # (b) is the sum of the two single slits, B's the mirror of A's, and one smooth hump
    assert np.abs(pA + pB - pb).max() < 3e-5
    assert np.abs(pA[::-1] - pB).max() < 3e-5
    peaks = lambda v: int(((v[1:-1] > v[:-2]) & (v[1:-1] >= v[2:])).sum())
    assert peaks(pb) == 1 and 5 <= peaks(pa) <= 9
    # (a) has fringes as deep as interference makes them, and the light is only moved
    mid = np.abs(y) < 2
    assert pa[mid].min() < 0.05 * pa.max()
    assert pa.max() == pytest.approx(2 * pb.max(), rel=0.05)
    # the first dark fringes where the two paths differ by half a wavelength
    L, h = d["L"], d["d"] / 2
    y0 = y[mid][np.argmin(pa[mid] + (y[mid] < 0))]                  # the first minimum above the axis
    assert np.hypot(L, y0 + h) - np.hypot(L, y0 - h) == pytest.approx(0.5, abs=0.02)
    # the far-field side of the document's criterion for two separate bands
    assert d["a"] * d["d"] / (1.0 * L) < 1


def test_the_photons_follow_the_intensity():
    stats = pytest.importorskip("scipy.stats")
    d = data()
    Y, dc = d["Y"], d["dc"]
    y = -Y + dc * np.arange(len(d["pa"]))
    for k, pdf in (("a", np.array(d["pa"])), ("b", np.array(d["pb"]))):
        ph = d["ph"][k]
        yy = -Y + 2 * Y * arr(ph["y"], "<u2") / 65535
        t = arr(ph["t"], "<u2") / 1000
        assert len(yy) == len(t) == 10000 and len(arr(ph["z"], "u1")) == 10000
        assert np.all(np.diff(t) >= 0)                              # in the order they land
        assert 1 <= (t <= 1).sum() <= 10                           # single dots first
        cdf = np.concatenate([[0], np.cumsum((pdf[1:] + pdf[:-1]) / 2 * np.diff(y))])
        cdf /= cdf[-1]
        assert stats.kstest(yy, lambda v: np.interp(v, y, cdf)).pvalue > 0.01


def test_its_check_file_records_the_checks():
    with open(os.path.join(NUMFIG, "ph_slits.check.txt"), encoding="utf-8") as fh:
        txt = fh.read()
    for head in ("CHECK 1", "CHECK 2", "CHECK 2b", "CONVERGENCE", "THE PHOTONS", "OVERLAP"):
        assert head in txt, head
    # the superposition meets the Fraunhofer formula far away
    e = [float(v) for v in re.findall(r"largest difference ([\d.e+-]+) of the peak", txt)[:1]]
    assert e and e[0] < 1e-6
    assert "(the fade and the next build): clean" in txt


# ---------------------------------------------------------------- nothing overlaps

def test_nothing_overlaps_across_its_loop():
    pytest.importorskip("playwright.sync_api")
    sys.path.insert(0, NUMFIG)
    import common
    times = [0.2, 0.45, 0.8, 1.2, 2.0, 3.5, 5.0, 6.5, 7.4, 9.0, 10.6, 11.2, 12.5]
    try:
        got = common.overlaps("ph-slits", times)
    except Exception as e:                                         # no browser here
        pytest.skip(f"playwright cannot run: {e}")
    assert {k: v for k, v in got.items() if v["labels"] or v["crossings"]} == {}
