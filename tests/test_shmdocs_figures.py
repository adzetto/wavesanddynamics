"""The SHM article's and the brochure's remaining pictures, redrawn from models (round 12).

tools/numfig/sd_*.py redraw five of his pictures in the figures' one style
(Computer Modern through the numfig engine, the crimson palette, every
signal and wave from a computed model):

- the article's Figure 2 (OMA and EMA workflow, image3): nf-sd-omaema;
- the article's Figure 5 (guided and bulk wave testing, image6): nf-sd-waves;
- the brochure's three NDT diagrams (image6, image7, image8): nf-sd-ae,
  nf-sd-pe and nf-sd-img, the model of the article's Figure 3 (shm_ndt.py)
  at each picture's own proportions.

content/anim/anim.shmdocs.json maps them; his words inside each picture are
kept verbatim.
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
SHM = "understanding-shm-and-ndt"
BROCHURE = "brochure-shm-and-ndt-2-pages"
PAGES = {   # name: (title, W, H)
    "nf-sd-omaema.html": ("Figure 2: OMA and EMA workflow", 1000, 512),
    "nf-sd-waves.html": ("Figure 5: Guided wave testing and bulk wave, pulse echo ultrasonic testing", 1000, 780),
    "nf-sd-ae.html": ("Acoustic emission, a passive technique", 1000, 317),
    "nf-sd-pe.html": ("Ultrasonic testing, pulse echo, an active technique", 1000, 435),
    "nf-sd-img.html": ("Ultrasonic testing, imaging, an active technique", 1000, 312),
}
FRAGMENT = {SHM: {"image3": "nf-sd-omaema.html", "image6": "nf-sd-waves.html"},
            BROCHURE: {"image6": "nf-sd-ae.html", "image7": "nf-sd-pe.html", "image8": "nf-sd-img.html"}}
# his pictures' proportions in the brochure (width x height of the Word pictures)
BROCHURE_RATIO = {"nf-sd-ae.html": 691 / 219, "nf-sd-pe.html": 398 / 173, "nf-sd-img.html": 401 / 125}
# the words in his pictures, verbatim (Figure 2's en dash is his; the script joins it between
# quotes, so the page never holds the spaced dash the site's own copy may not use)
HIS_WORDS = {
    "nf-sd-omaema.html": ["Unknown, random force", "(e.g., wind, traffic,", "footsteps)", "Structure",
                          "Sensors measure", "output only", "Output-only System ID",
                          "(Operational Modal Analysis ' + DASH + ' OMA)", "Known, controlled force",
                          "(e.g., shaker,", "earthquake)", "input and output", "Input-Output System ID",
                          "(Experimental Modal Analysis ' + DASH + ' EMA)", "const DASH = '–'"],
    "nf-sd-waves.html": ["Guided wave testing", "(active ultrasonic excitation, or passive acoustic emission)",
                         "transducer (send/receive)", "defect", "incident guided wave", "reflected (echo) wave",
                         "dispersive guided modes (wave occupies the full cross section)",
                         "acoustic emission: the same guided modes, launched passively by the damage",
                         "event itself (e.g. crack growth) instead of by a transducer",
                         "Received signal: dispersed wave packet", "outgoing", "pulse", "defect echo",
                         "(spread out by dispersion)", "Amplitude", "Time", "Bulk wave testing",
                         "(conventional pulse echo / phased array ultrasonic testing)", "transducer",
                         "incident pulse", "flaw echo", "flaw", "back wall echo", "back wall", "thickness",
                         "bulk wave behavior (no dispersive guided modes)", "Resulting A scan", "initial",
                         "Time (≈ depth)"],
    "nf-sd-ae.html": ["Acoustic Emission (sensor is only listening)", "Steel beam"],
    "nf-sd-pe.html": ["Acoustic sensor", "(sends and receives waves)", "Steel beam", "crack", "Recorded signal",
                      "Amplitude", "Excitation", "Reflection", "Boundary", "Time"],
    "nf-sd-img.html": ["Scanning transducers", "structure", "crack", "Resulting Image"],
}


def page(name):
    with open(os.path.join(ANIM, name), encoding="utf-8") as fh:
        return fh.read()


def script(name):
    """The figure's own script: what follows the engine in the page."""
    with open(os.path.join(NUMFIG, "engine.js"), encoding="utf-8") as fh:
        engine = fh.read()
    text = page(name)
    assert engine in text, "the engine is inlined whole"
    return text.split(engine, 1)[1]


def data(name):
    m = re.search(r"^const DATA = (\{.*\});$", page(name), re.M)
    return json.loads(m.group(1))


@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_is_a_numfig_page_in_computer_modern_only(name):
    text = page(name)
    title, w, h = PAGES[name]
    assert f"<title>{html.escape(title, quote=False)}</title>" in text
    assert f"const W = {w}, H = {h};" in text
    # the engine, its two faces, and the figure started once the type has loaded
    assert '"CMU Serif"' in text and '"Figure Math"' in text and "function boot()" in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "../fonts/figure-math.woff2" in text
    faces = set(re.findall(r'font-family:"([^"]+)"', text))
    assert faces == {"CMU Serif", "Figure Math"}
    own = script(name)
    assert "boot()" in own
    # no face of its own: type only through the engine's text() and math()
    assert "ctx.font" not in own and "font-family" not in own
    low = text.lower()
    for face in ("calibri", "carlito", "cambria", "segoe ui", "arial", "helvetica", "dejavu"):
        assert face not in low, face
    # the palette: the crimson, not his reds or the old orange
    assert "#b3261e" not in low and "#c0392b" not in low and "#a7203a" in low
    # our copy: no em dash, no spaced en dash, no address
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)


@pytest.mark.parametrize("name", sorted(PAGES))
def test_his_words_are_kept_verbatim(name):
    text = page(name)                                        # the script, or the DATA it draws from
    for words in HIS_WORDS[name]:
        assert words in text, words


@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_prints_its_own_frame_at_its_ratio(name):
    from PIL import Image
    _, w, h = PAGES[name]
    with Image.open(os.path.join(ANIM, name[:-5] + ".webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * h / w) <= 2
        px = np.asarray(im.convert("L"))
        assert (px < 128).mean() > 0.01                     # a frame, not a blank
    if name in BROCHURE_RATIO:                               # at his picture's proportions in the brochure
        assert w / h == pytest.approx(BROCHURE_RATIO[name], rel=0.01)


def test_the_fragment_maps_his_five_pictures():
    with open(os.path.join(ANIM, "anim.shmdocs.json"), encoding="utf-8") as fh:
        assert json.load(fh) == FRAGMENT
    got = preview.animations("../anim")
    for slug, pics in FRAGMENT.items():
        for stem, name in pics.items():
            a = got[slug][stem]
            title, w, h = PAGES[name]
            assert a["src"] == f"../anim/{name}" and (a["w"], a["h"]) == (w, h)
            assert a["title"] == re.sub(r"^Figure \d+: ", "", title)
            assert a["still"]["src"] == f"../anim/{name[:-5]}.webp" and a["still"]["w"] == 1344
    # the pictures redrawn before stay as they are
    assert got[SHM]["image2"]["src"].endswith("nf-shm-sensors.html")
    assert got[SHM]["image4"]["src"].endswith("nf-shm-ndt.html")
    assert got[SHM]["image5"]["src"].endswith("nf-standing.html")
    assert got[BROCHURE]["image5"]["src"].endswith("nf-shm-sensors.html")
    # the brochure's four icons are redrawn apart, in the "How it works" flow
    # (anim.howitworks.json, tests/test_howitworks.py), not by this set
    assert all(got[BROCHURE][k]["src"].endswith(".html") and "/nf-hw-" in got[BROCHURE][k]["src"]
               for k in ("image1", "image2", "image3", "image4"))


def test_the_frame_is_the_model_it_names_and_both_workflows_find_its_frequencies():
    d = data("nf-sd-omaema.html")
    m, k = 25e3, 9.5e6                                       # the parameter line's frame
    assert "m\\rm{ = 25 t, }k\\rm{ = 9.5 MN/m" in d["params"]
    n = np.arange(1, 4)
    closed = 2 * np.sqrt(k / m) * np.sin((2 * n - 1) * np.pi / 14) / (2 * np.pi)
    assert np.allclose(d["fn"], closed, rtol=1e-5)
    # output only and input-output: the same frequencies, as the figure prints them
    for ident in (d["oma"], d["ema"]):
        assert [f"{v:.2f}" for v in ident] == [f"{v:.2f}" for v in closed]
    assert np.allclose(d["ema"], closed, rtol=1e-5)          # the fitted FRF: exact
    assert np.allclose(d["oma"], closed, atol=5e-3)          # the 2 h record: within its scatter
    # the printed frame comes after the sweep, the loop once through
    assert d["bt0"] + d["swt"] < d["poster"] - d["t0"] < d["loop"]


def test_the_guided_echo_spreads_and_the_bulk_echoes_read_as_depths():
    d = data("nf-sd-waves.html")
    a, b = d["a"], d["b"]
    # (a) A0 at 50 kHz: the wavelength of the inset is of the order of the thickness
    assert a["inset"]["lam_mm"] == pytest.approx(37.84, abs=0.05)
    assert 2 < a["inset"]["lam_mm"] / 10 < 6
    # the defect echo arrives near 2D / c_g after the burst's centre, spread out
    assert a["echo"] == pytest.approx((a["tc"] + 2 * a["D"] / a["cg"]) * 1e6, rel=0.05)
    assert a["win"][1] - a["win"][0] > 250                   # us: the burst itself lasts 60
    # (b) the echoes at 2z/c_L: the back wall at 2d/c_L, the flaw before it
    e = b["echo"]
    assert e["tb"] == pytest.approx(2 * b["db"] / b["cl"], rel=5e-3)
    assert e["tf"] == pytest.approx(e["tf_th"], rel=5e-3) and e["tf"] < e["tb"]
    # lambda << h: 5 MHz in steel against 25 mm
    assert b["lam"]["mm"] == pytest.approx(b["cl"] / 5.0) and b["db"] / b["lam"]["mm"] > 20
    # its field frames are the page's own files
    for ch in b["field"]["chunks"]:
        assert ch["src"].startswith("nf-sd-waves-field-") and os.path.isfile(os.path.join(ANIM, ch["src"]))


@pytest.mark.parametrize("name,part", [("nf-sd-ae.html", "b"), ("nf-sd-pe.html", "a"), ("nf-sd-img.html", "c")])
def test_the_brochure_draws_the_model_of_figure_3(name, part):
    # the numbers of the article's Figure 3, panel by panel: regenerate the
    # brochure's diagrams (tools/numfig/sd_ae.py, sd_pe.py, sd_img.py) when it changes
    mine, his = data(name), data("nf-shm-ndt.html")
    assert mine[part] == his[part]
    for k in ("master", "us", "cl", "f0", "nc", "dur"):      # (the printed moment is each figure's own)
        assert mine[k] == his[k]
    assert 0 < mine["poster"] < 2 * mine["master"]


def test_the_overlap_check_is_recorded():
    for n in ("sd_omaema", "sd_waves", "sd_ae", "sd_pe", "sd_img"):
        with open(os.path.join(NUMFIG, f"{n}.check.txt"), encoding="utf-8") as fh:
            txt = fh.read()
        assert "OVERLAP" in txt and "nothing collides" in txt, n


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _playwright(), reason="needs Playwright's Chromium")
@pytest.mark.parametrize("name,times", [
    ("sd-omaema", [0.3, 0.8, 1.4, 3.0, 6.9, 9.8, 14.4, 18.0, 21.6, 30.0]),
    ("sd-waves", [0.3, 0.8, 1.4, 2.6, 4.2, 5.8, 8.4, 9.7, 12.2, 14.0, 17.2]),
    ("sd-ae", [0.3, 0.8, 1.4, 2.1, 3.4, 5.2, 7.0, 8.3]),
    ("sd-pe", [0.3, 0.8, 1.2, 1.6, 2.1, 2.4, 4.6, 5.2, 5.65, 9.5]),
    ("sd-img", [0.3, 0.8, 1.4, 2.3, 3.5, 5.1, 6.82, 8.3]),
])
def test_nothing_overlaps(name, times):
    import common
    for when, r in common.overlaps(name, times).items():
        assert r["labels"] == [] and r["crossings"] == [], (when, r)
