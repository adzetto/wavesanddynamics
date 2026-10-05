"""The SHM article's two moving figures, redrawn from models (round 11).

His own animations of Figure 1 (a building's dynamic response) and Figure 3
(NDT techniques) set their words in Calibri and Cambria Math in his own
colours. tools/numfig/shm_sensors.py and shm_ndt.py redraw them in the
figures' one style: Computer Modern through the numfig engine, the crimson
palette, and every mode shape, wave and echo from a computed model. His
files are archived in content/anim-originals/, and the documents draw the
redraws in their place.
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

import build  # noqa: E402
import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
ORIG = os.path.join(ROOT, "content", "anim-originals")
SHM = "understanding-shm-and-ndt"
BROCHURE = "brochure-shm-and-ndt-2-pages"
PAGES = {
    "nf-shm-sensors.html": ("Figure 1: Example of a building's dynamic response", 1000, 500),
    "nf-shm-ndt.html": ("Figure 3: NDT techniques", 1000, 548),
}
HIS = {"fig1-building-sensors.html": "Figure 1: Example of a building's dynamic response",
       "fig3-ndt-techniques.html": "Figure 3: NDT techniques"}


def page(name):
    with open(os.path.join(ANIM, name), encoding="utf-8") as fh:
        return fh.read()


def data(name):
    m = re.search(r"^const DATA = (\{.*\});$", page(name), re.M)
    return json.loads(m.group(1))


@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_redraw_is_a_numfig_page_in_computer_modern(name):
    text = page(name)
    title, w, h = PAGES[name]
    assert f"<title>{html.escape(title, quote=False)}</title>" in text
    assert f"const W = {w}, H = {h};" in text
    # the engine is inlined and the figure's script starts it once the type has loaded
    assert '"CMU Serif"' in text and '"Figure Math"' in text and "function boot()" in text
    assert text.count("boot()") >= 2
    assert "../fonts/cmu-serif-500-roman.woff2" in text
    # none of his faces, his reds or the old orange
    low = text.lower()
    for face in ("calibri", "carlito", "cambria", "segoe ui", "arial"):
        assert face not in low, face
    assert "#b3261e" not in low and "#a7203a" in low
    # our copy: no em dash, no spaced en dash, no address
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)


@pytest.mark.parametrize("name", sorted(PAGES))
def test_each_prints_its_own_frame_at_its_ratio(name):
    from PIL import Image
    _, w, h = PAGES[name]
    with Image.open(os.path.join(ANIM, name[:-5] + ".webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * h / w) <= 2
        # a frame, not a blank: the still is drawn at POSTER_T with the whole figure
        px = np.asarray(im.convert("L"))
        assert (px < 128).mean() > 0.01


def test_the_article_draws_the_redraws_where_his_animations_stood():
    got = preview.animations("../anim")
    shm = got[SHM]
    # his Figure 1 is the waves guide's Figure 1 since 5 Oct 2026 (his notes:
    # "Figure (animation) 1 in Waves and Dynamics => Fig 1 of this section also")
    assert shm["image2"]["src"] == "../anim/nf-building.html"
    assert shm["image4"]["src"] == "../anim/nf-shm-ndt.html"
    assert shm["image5"]["src"] == "../anim/nf-standing.html"
    assert shm["image2"]["title"].startswith("Lateral natural dynamic response of a building")
    assert shm["image4"]["title"] == "NDT techniques"
    for stem, name in (("image4", "nf-shm-ndt"),):
        assert (shm[stem]["w"], shm[stem]["h"]) == PAGES[name + ".html"][1:]
        assert shm[stem]["still"]["src"] == f"../anim/{name}.webp"


def test_the_brochure_draws_the_redraw_and_its_frame_keeps_the_description():
    # the brochure's Figure 1 has no caption; build.ALT describes his picture
    # (image5), and doc_body() hands those words to the frame the redrawn
    # figure prints (nf-shm-sensors.webp); test_anim_figures checks the page
    got = preview.animations("../anim")[BROCHURE]["image5"]
    assert got["src"] == "../anim/nf-shm-sensors.html"
    assert not os.path.isfile(os.path.join(ANIM, "fig1-building-sensors.html"))
    assert build.ALT[BROCHURE]["image5"].startswith("Diagram: the vibration of a structure")


def test_his_originals_are_archived_and_no_longer_published_unused():
    for name, title in HIS.items():
        with open(os.path.join(ORIG, name), encoding="utf-8") as fh:
            his = fh.read()
        assert f"<title>{title}</title>" in his and "Calibri" in his
    assert not os.path.isfile(os.path.join(ANIM, "fig3-ndt-techniques.html"))
    # every page in content/anim is drawn in some document
    mapped = set()
    for n in os.listdir(ANIM):
        if n == "anim.json" or re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                # (a picture redrawn as several figures names a list of them)
                mapped |= {f for pics in json.load(fh).values() for v in pics.values()
                           for f in (v if isinstance(v, list) else [v])}
    # ... or drawn only as a Big Picture card (tools/bp_art.py picks its still)
    with open(os.path.join(ROOT, "tools", "bp_art.py"), encoding="utf-8") as fh:
        mapped |= {f"{n}.html" for n in re.findall(r"content:anim/(nf-[\w-]+)\.webp", fh.read())}
    assert {n for n in os.listdir(ANIM) if n.endswith(".html")} <= mapped


def test_the_building_is_the_model_it_names():
    from scipy.optimize import brentq
    d = data("nf-shm-sensors.html")
    # T1 = 2.4 s, and the 2nd mode where the walls-and-frames continuum puts it
    # (Miranda and Taghavi 2005, eq. 6, alpha = 6), solved here on its own
    a = d["alpha"]

    def char(g):
        b = np.sqrt(a * a + g * g)
        return 2 + (2 + a ** 4 / (g * g * b * b)) * np.cos(g) * np.cosh(b) + a * a / (g * b) * np.sin(g) * np.sinh(b)

    gs = np.linspace(0.05, 10, 20001)
    v = char(gs)
    roots = [brentq(char, gs[i], gs[i + 1]) for i in np.where(np.sign(v[:-1]) != np.sign(v[1:]))[0][:2]]
    lam = [g * np.sqrt(g * g + a * a) for g in roots]
    # (the page keeps five decimals of every number)
    assert d["f"][0] == pytest.approx(1 / 2.4, rel=1e-4)
    assert d["f"][1] / d["f"][0] == pytest.approx(lam[1] / lam[0], rel=1e-4)
    # shapes normalised at the roof, fixed at the ground; the 2nd mode has one node
    psi = np.array(d["psi"])
    assert np.allclose(psi[:, -1], 1) and np.allclose(psi[:, 0], 0)
    assert np.sum(np.diff(np.sign(psi[1, 1:])) != 0) == 1
    # his five sensors
    assert d["sensors"] == [0.95, 0.73, 0.5, 0.27, 0.05]


def test_the_echoes_arrive_when_the_wave_speed_says():
    d = data("nf-shm-ndt.html")
    a, c = d["a"], d["cl"]
    # the back wall echo of the recorded signal at 2d / c_L, the crack's before it
    assert a["tb"] == pytest.approx(2 * a["d"] / c, rel=5e-3)
    assert 2 * min(p[1] for p in a["crack"]) / c < a["tc"] < a["tb"]
    v = np.array(a["sig"]["v"])
    assert np.abs(v).max() == pytest.approx(1, abs=0.02)            # over the sent pulse's peak
    # the acoustic emission is heard r / c_L after each step
    b = d["b"]
    for k, hit in enumerate(b["hits"]):
        tip = b["crack"][k + 2]
        x0, x1 = b["sensor"][0] - b["sensor"][1] / 2, b["sensor"][0] + b["sensor"][1] / 2
        assert hit == pytest.approx(np.hypot(tip[0] - np.clip(tip[0], x0, x1), tip[1]) / c, rel=1e-4)
    # the poster: the pulse echo recorded, the last step heard, the image complete
    t = d["poster"]
    assert (t - a["t0"]) % (d["master"] / 2) * d["us"] > 16
    assert t > b["events"][3] + b["hits"][3] / d["us"]
    cc = d["c"]
    assert t > cc["t0"] + len(cc["xe"]) * cc["dt"]
