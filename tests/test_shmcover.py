"""The SHM and NDT guide's cover, redrawn from models (round 12, shmcover; 5 Oct
2026, twice as tall).

His cover (understanding-shm-and-ndt, image1) is a drawing without words: a
small building, a wave running away from it that turns from teal to orange,
three sensor dots. tools/numfig/shm_cover.py redraws it from models. Since the
professor's notes of 5 Oct 2026 ("Tepedeki resim => vertical size 2x", with a
sketch: a tall building with sensors on its floors, a circled spot and an
arrow to an inset labelled "imaging", an array probe on a piece, a hatched
defect and the back wall) it is twice as tall: a 12-storey steel frame
swaying in its computed first mode with sensors on four floors, one joint
circled and drawn magnified as ultrasonic array imaging of a defect in it,
the elements firing one after another, the echoes from the defect and the
back wall, and the image built from them beside it. content/anim/
anim.shmcover.json puts it where his picture stood.
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

import build  # noqa: E402
import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
SHM = "understanding-shm-and-ndt"
NAME = "nf-shm-cover.html"
TITLE = "A building's first mode, and ultrasonic imaging of a defect in one of its joints"
W, H = 1000, 346                                   # his picture is 1344 x 233; twice as tall
BUILT = os.path.isfile(os.path.join(build.BUILD, SHM, "part-01.json"))


def page():
    with open(os.path.join(ANIM, NAME), encoding="utf-8") as fh:
        return fh.read()


def data():
    return json.loads(re.search(r"^const DATA = (\{.*\});$", page(), re.M).group(1))


def f32(s):
    import base64
    return np.frombuffer(base64.b64decode(s), dtype="<f4").astype(float)


def test_the_cover_is_a_numfig_page_in_computer_modern():
    text = page()
    assert f"<title>{html.escape(TITLE, quote=False)}</title>" in text
    assert f"const W = {W}, H = {H};" in text
    assert abs(W / H - 1344 / 233 / 2) / (1344 / 233 / 2) < 3e-3  # his picture's, twice as tall
    # the engine is inlined and the script starts it once the type has loaded
    assert '"CMU Serif", "Figure Math"' in text and "../fonts/figure-math.woff2" in text
    assert "../fonts/cmu-serif-500-roman.woff2" in text and "function boot()" in text
    assert text.endswith("boot();\n</script>\n</body>\n</html>\n")
    low = text.lower()
    for face in ("calibri", "carlito", "cambria", "segoe ui", "arial", "helvetica", "sans-serif"):
        assert face not in low, face
    # the palette: crimson for the defect and its echo, no orange (his cover's)
    assert "#a7203a" in low and "c.accent" in low
    for warm in ("#a5510b", "#d9822b", "#f2c39a", "#fbebdd", "#7b3d0c"):
        assert warm not in low
    # our copy: no em dash, no spaced en dash, no address; type only through
    # the engine's text() and math(), never a ctx.font of its own
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    assert "ctx.font" not in text.split("/* ---- the cover", 1)[1]


def test_its_controls_are_the_waves_covers():
    # the waves cover keeps pause and restart out of the way until a pointer
    # or the keyboard asks for them (wt_lib.QUIET_CTL), and a click still
    # pauses: not the icon's quiet mode
    import wt_lib
    text = page()
    assert wt_lib.QUIET_CTL.strip() in text
    with open(os.path.join(ANIM, "nf-wt-cover.html"), encoding="utf-8") as fh:
        assert wt_lib.QUIET_CTL.strip() in fh.read()
    assert not re.search(r"\bQUIET\s*=", text.split("/* ---- the cover", 1)[1])


def test_it_prints_its_own_frame_at_its_ratio():
    from PIL import Image
    with Image.open(os.path.join(ANIM, "nf-shm-cover.webp")) as im:
        assert im.size[0] == 1344 and abs(im.size[1] - 1344 * H / W) <= 2
        px = np.asarray(im.convert("RGB")).astype(int)
    # a frame, not a blank: the building, the piece and its image are drawn,
    # and the defect is in the crimson, in the magnified joint
    assert (px.mean(2) < 128).mean() > 0.01
    crimson = (abs(px[..., 0] - 0xA7) < 40) & (px[..., 1] < 90) & (px[..., 2] < 110)
    assert crimson[:, :int(1344 * .25)].sum() == 0
    assert crimson[:, int(1344 * .3):int(1344 * .62)].sum() > 300


def test_the_fragment_puts_it_where_his_picture_stood():
    with open(os.path.join(ANIM, "anim.shmcover.json"), encoding="utf-8") as fh:
        assert json.load(fh) == {SHM: {"image1": NAME}}
    got = preview.animations("../anim")[SHM]["image1"]
    assert got["src"] == f"../anim/{NAME}" and (got["w"], got["h"]) == (W, H)
    assert got["title"] == TITLE
    assert got["still"]["src"] == "../anim/nf-shm-cover.webp"
    # no other picture is drawn by it
    named = []
    for n in os.listdir(ANIM):
        if n == "anim.json" or re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                named += [(s, k) for s, pics in json.load(fh).items() for k, v in pics.items() if v == NAME]
    assert named == [(SHM, "image1")]


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
def test_the_document_head_shows_it_where_the_picture_stood(monkeypatch):
    monkeypatch.setattr(build, "VERBATIM", [])
    monkeypatch.setattr(build, "ANIM", {})
    before = build.page_doc(SHM)
    monkeypatch.setattr(build, "ANIM", preview.animations("../anim"))
    after = build.page_doc(SHM)
    head = lambda p: re.search(r'<header class="dochead[^"]*">(.*?)</header>', p, re.S).group(1)
    was, now = head(before), head(after)
    assert "/image1.webp" in was and "<iframe" not in was
    fig = re.search(r"<figure[^>]*>.*?</figure>", now, re.S).group(0)
    assert fig.startswith(f'<figure class="fig--anim"><iframe class="anim" src="../anim/{NAME}"')
    assert f"aspect-ratio:{W}/{H}" in fig and 'src="../anim/nf-shm-cover.webp"' in fig
    # the title, the words under it and the byline are his, unchanged
    assert re.sub(r"<figure.*?</figure>", "", was, flags=re.S) == re.sub(r"<figure.*?</figure>", "", now, flags=re.S)


def test_the_building_sways_in_its_own_first_mode():
    """A uniform shear building, n equal storeys fixed at the ground: its
    first mode is sin(i pi / (2n + 1)) at floor i, in closed form."""
    b = data()["b"]
    n = b["storeys"]
    assert (n, b["bays"], b["joint"]) == (12, 3, 4)
    ref = np.sin(np.arange(n + 1) * np.pi / (2 * n + 1)) / np.sin(n * np.pi / (2 * n + 1))
    assert np.abs(np.array(b["psi"]) - ref).max() < 1e-5
    assert b["psi"][0] == 0 and b["psi"][-1] == 1 and np.all(np.diff(b["psi"]) > 0)
    assert b["f1"] * b["tb"] == pytest.approx(1, rel=1e-5) and b["f1"] == pytest.approx(0.7752, abs=1e-4)


def test_the_echoes_come_back_along_the_shortest_way_by_the_defect():
    """Each echo of the inset arrives when the reflection's path, element to
    the defect's surface to element, says: the shortest such path (Fermat),
    over the defect's outline, at the steel's P wave speed; the back wall's
    two way time is 2 d / c_L."""
    i = data()["i"]
    xe, A, cl, dfc = np.array(i["xe"]), np.array(i["arrive"]), i["cl"], i["def"]
    assert len(xe) == 16 and np.allclose(np.diff(xe), 1.5) and (i["wp"], i["dp"]) == (30, 16)
    assert cl == pytest.approx(5.9, rel=1e-3)
    th = np.radians(-dfc["tilt"])                 # depth downwards: the tilt turns the other way
    t = np.linspace(0, 2 * np.pi, 100001)
    px = dfc["x"] + dfc["a"] * np.cos(t) * np.cos(th) - dfc["b"] * np.sin(t) * np.sin(th)
    pz = dfc["z"] + dfc["a"] * np.cos(t) * np.sin(th) + dfc["b"] * np.sin(t) * np.cos(th)
    fermat = np.array([[np.min(np.hypot(px - xe[j], pz) + np.hypot(px - xe[k], pz)) / cl
                        for k in range(16)] for j in range(16)])
    assert np.abs(A - fermat).max() < 1e-4 and np.array_equal(A, A.T)        # and reciprocal
    # every echo of the defect comes before the back wall's
    assert A.max() < 2 * i["dp"] / cl


def test_the_clock_loops_on_the_building_and_the_still_tells_it_all():
    d = data()
    b, i = d["b"], d["i"]
    # eleven sways a loop; the building moves from 0.35 s
    assert d["period"] == pytest.approx(11 * b["tb"], rel=1e-5) and d["t0b"] <= 0.6
    # the sixteen elements fire one after another and are done within the loop
    assert i["tf0"] + 16 * i["dtf"] < d["period"]
    # the still: the building at full sway during the sixteenth firing
    assert abs(np.cos(2 * np.pi * (d["poster"] - d["t0b"]) / b["tb"])) == pytest.approx(1, abs=1e-6)
    assert i["tf0"] + 15 * i["dtf"] < d["poster"] < i["tf0"] + 16 * i["dtf"]


def test_the_check_file_records_the_checks_and_nothing_overlaps():
    with open(os.path.join(ROOT, "tools", "numfig", "shm_cover.check.txt"), encoding="utf-8") as fh:
        txt = fh.read()
    for n in range(1, 9):
        assert f"CHECK {n}:" in txt
    over = txt.split("OVERLAP", 1)[1].strip().splitlines()[2:]
    assert len(over) >= 8 and all(l.strip().endswith("labels none, crossings none") for l in over)
    assert "—" not in txt


def test_nothing_overlaps_across_the_motion():
    pytest.importorskip("playwright.sync_api")
    import common
    try:
        got = common.overlaps("shm-cover", [0.45, 0.8, 2.3, 5.6, 9.0, 11.3, 13.9])
    except Exception as e:                        # no browser on this machine
        pytest.skip(f"playwright could not run: {e}")
    assert {k: v for k, v in got.items() if v["labels"] or v["crossings"]} == {}
