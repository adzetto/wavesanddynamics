"""The brochure's HOW IT WORKS flow, redrawn in the figures' line style (round 12).

The client: "broşürdeki dört küçük ikonu da aynı çizgi stiline getir", and of
the brochure's "how it works" part, "bunun how it works kısmını da lütfen".

- tools/numfig/hw_*.py draw his four icons (image1 to image4 of
  brochure-shm-and-ndt-2-pages) as quiet numfig pages at his sizes and
  proportions: Structure(s), a six storey frame swaying in its first mode
  beside a cable-stayed bridge; Sensors on structure(s), a sensor sending a
  burst; Data analysis, that frame's record, its peaks and the decay fitted
  through them; Decision making, a shield, a report and the check.
- content/anim/anim.howitworks.json maps them; preview.py keeps each frame
  at his picture's size in the row of steps; parts/docs.py lays the row out
  (equal steps, each arrow halfway between two pictures, a list on a phone)
  and draws his arrows as the figures draw theirs, each after the icon
  before it and before the next.
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
from parts import docs, springs  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
NUMFIG = os.path.join(ROOT, "tools", "numfig")
BROCHURE = "brochure-shm-and-ndt-2-pages"
# his four icons: picture, page, his label (the page's title), his size in CSS px (half his pixels)
ICONS = [("image1", "nf-hw-structure.html", "Structure(s)", 82, 82),
         ("image2", "nf-hw-sensors.html", "Sensors on structure(s)", 72, 72),
         ("image3", "nf-hw-analysis.html", "Data analysis", 92, 76),
         ("image4", "nf-hw-decision.html", "Decision making", 74, 74)]
PAGES = [i[1] for i in ICONS]


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
    return json.loads(re.search(r"^const DATA = (\{.*\});$", page(name), re.M).group(1))


# ------------------------------------------------------------------ the four pages

@pytest.mark.parametrize("stem,name,label,w,h", ICONS)
def test_each_icon_is_a_quiet_numfig_page_at_his_size(stem, name, label, w, h):
    text = page(name)
    assert f"<title>{html.escape(label, quote=False)}</title>" in text
    # his size, so his proportion exactly: one drawing unit is one of his CSS pixels
    assert f"const W = {w}, H = {h};" in text
    assert set(re.findall(r'font-family:"([^"]+)"', text)) == {"CMU Serif", "Figure Math"}
    own = script(name)
    assert "ctx.font" not in own and "font-family" not in own
    # quiet (engine.js): it plays once, with no controls, and ignores clicks
    assert "var QUIET = true;" in own and own.split("</script>")[0].rstrip().endswith("boot();")
    assert own.index("var QUIET = true;") < own.rindex("boot();")
    # the palette's inks and blues and one crimson: no raw colour of its own but the page's white
    assert set(re.findall(r"#[0-9A-Fa-f]{3,6}\b", own)) <= {"#fff"}
    assert "C.accent" in own and "C.navy" in own
    assert "—" not in text and " – " not in text
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)


@pytest.mark.parametrize("stem,name,label,w,h", ICONS)
def test_each_prints_its_own_frame_at_twice_his_pixels(stem, name, label, w, h):
    from PIL import Image
    with Image.open(os.path.join(ANIM, name[:-5] + ".webp")) as im:
        assert im.size == (2 * w, 2 * h)
        px = np.asarray(im.convert("L"))
    assert (px < 128).mean() > 0.01                          # a drawing, not a blank


def test_the_icons_start_in_turn_and_each_lets_the_arrow_after_it_draw():
    import hw_lib
    assert [data(n)["k"] for n in PAGES] == [0, 1, 2, 3]
    js = hw_lib.JS
    assert "const S0 = DATA.k * 0.35;" in js                  # step k starts k x 0.35 s after it is seen
    # the arrow after a step: hidden while its icon waits off screen, drawn in its turn;
    # only in the page (same origin), never in a still or with less motion asked for
    assert "frameElement.closest('.flow__step')" in js and "classList.contains('flow__arrow')" in js
    assert "if (NEXT && !STILL && !REDUCED)" in js
    assert "classList.add('is-wait')" in js and "classList.add('is-in')" in js
    assert "setPlay(false)" in js                             # plays once, then rests
    # each arrow is drawn (the spring's visual time and the tip's lag) before the next icon starts
    lag = int(re.search(r"flow-tip var\(--spring-fast\) (\d+)ms", docs.CSS).group(1))
    assert hw_lib.ARROW_AT + (springs.SPRINGS["fast"][0] + lag) / 1000 < hw_lib.STAGGER


def test_the_building_sways_in_the_first_mode_of_the_code_frame_in_real_time():
    import hw_lib as L
    d = data("nf-hw-structure.html")
    N = L.N
    j = np.arange(N + 1)
    closed = np.sin(j * np.pi / (2 * N + 1)) / np.sin(N * np.pi / (2 * N + 1))
    assert np.allclose(d["phi"], closed, atol=2e-5)
    # T1 = C_t H^(3/4) (EN 1998-1), 5 % damped, in real time
    T1 = L.CT * (N * L.STOREY) ** 0.75
    w1 = 2 * np.pi / T1
    assert d["a"] == pytest.approx(L.ZETA * w1, rel=1e-4)
    assert d["wd"] == pytest.approx(w1 * np.sqrt(1 - L.ZETA ** 2), rel=1e-4)
    # it stops on a zero crossing, where the envelope is under a quarter pixel: nothing jumps
    n = d["tstop"] * d["wd"] / np.pi
    assert n == pytest.approx(round(n), abs=1e-3)
    assert d["U"] / d["qpk"] * np.exp(-d["a"] * d["tstop"]) < 0.25


def test_the_record_is_that_building_and_its_peaks_give_the_damping_back():
    import hw_analysis
    import hw_lib as L
    s, d = data("nf-hw-structure.html"), data("nf-hw-analysis.html")
    assert d["a"] == s["a"]
    rec = np.array(d["rec"])
    ts = np.linspace(0, d["T"], len(rec))
    assert d["T"] == pytest.approx(hw_analysis.PERIODS * 2 * np.pi / s["wd"], rel=1e-5)
    assert np.allclose(rec, np.exp(-s["a"] * ts) * np.sin(s["wd"] * ts) / s["qpk"], atol=1e-4)
    tq, vq = hw_analysis.peaks_of(ts, rec)
    delta = np.log(vq[:-1] / vq[1:])
    assert np.allclose(delta / np.sqrt(4 * np.pi ** 2 + delta ** 2), L.ZETA, atol=2e-4)
    # the marked peaks lie on the fitted decay the page draws
    for t, v in d["pk"]:
        assert d["env"] * np.exp(-d["a"] * t) == pytest.approx(v, rel=1e-4)


def test_the_burst_crests_are_a_wavelength_apart_and_fall_as_one_over_root_r():
    d = data("nf-hw-sensors.html")
    R = np.array(d["R"])
    assert np.allclose(-np.diff(R), d["lam"])
    special = pytest.importorskip("scipy.special")
    k = 2 * np.pi / d["lam"]
    exact = np.abs(special.hankel1(0, k * R))
    assert np.allclose(np.sqrt(R[-1] / R), exact / exact[-1], rtol=2e-3)


def test_the_check_files_record_the_models_and_the_overlap_check():
    for n in ("structure", "sensors", "analysis", "decision"):
        with open(os.path.join(NUMFIG, f"hw_{n}.check.txt"), encoding="utf-8") as fh:
            txt = fh.read()
        assert "OVERLAP" in txt and "nothing collides" in txt, n


# ------------------------------------------------------------------ the wiring

def test_the_fragment_maps_his_four_icons():
    with open(os.path.join(ANIM, "anim.howitworks.json"), encoding="utf-8") as fh:
        assert json.load(fh) == {BROCHURE: {stem: name for stem, name, *_ in ICONS}}
    got = preview.animations("../anim")[BROCHURE]
    for stem, name, label, w, h in ICONS:
        a = got[stem]
        assert a["src"] == f"../anim/{name}" and (a["w"], a["h"]) == (w, h) and a["title"] == label
        assert a["still"] == {"src": f"../anim/{name[:-5]}.webp", "w": 2 * w, "h": 2 * h}


def _text(t):
    return {"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {
        "text": t, "decorations": [{"type": "BOLD", "fontWeightValue": 700}]}}],
        "paragraphData": {"textStyle": {"textAlignment": "CENTER"}}}


def _flow():
    """His row of steps as the converter gives it: a picture and a label a cell, his arrows between."""
    cells = []
    for i, (stem, _, label, w, h) in enumerate(ICONS):
        if i:
            cells.append({"type": "TABLE_CELL", "nodes": [_text("→")]})
        cells.append({"type": "TABLE_CELL", "nodes": [
            {"type": "IMAGE", "id": f"i{i}", "nodes": [], "imageData": {"image": {
                "src": {"id": f"{stem}.png"}, "width": 2 * w, "height": 2 * h}}}, _text(label)]})
    return {"type": "TABLE", "id": "t", "tableData": {"rowHeader": False},
            "nodes": [{"type": "TABLE_ROW", "nodes": cells}]}


def _draw(node, anim):
    preview.plan([node], {}, anim)
    try:
        return preview.render(node, "../fig/d")
    finally:
        preview.plan([])


def test_each_step_is_its_icon_at_his_size_and_a_drawing_not_a_stop():
    anim = {stem: a for stem, a in preview.animations("../anim")[BROCHURE].items()}
    out = _draw(_flow(), anim)
    assert out.startswith('<div class="flow">') and out.count('<div class="flow__step">') == 4
    assert out.count('<span class="flow__arrow" aria-hidden="true">→</span>') == 3
    for stem, name, label, w, h in ICONS:
        fig = re.search(r'<figure class="fig--anim fig--cell" style="width:%dpx">(.*?)</figure>' % w, out).group(1)
        assert fig.startswith(f'<iframe class="anim" tabindex="-1" aria-hidden="true" src="../anim/{name}" ')
        assert f'style="aspect-ratio:{w}/{h}"' in fig
        assert f'<img class="anim__still" src="../anim/{name[:-5]}.webp" alt="" width="{2 * w}" height="{2 * h}"' in fig
        assert f"<strong>{html.escape(label, quote=False)}</strong>" in out    # his words, as they stand
    # without the frames the row is his pictures, as before
    still = _draw(_flow(), {})
    assert "<iframe" not in still and '<figure><img src="../fig/d/image1.png" alt="" width="82" height="82"' in still


def test_a_table_cell_keeps_the_cells_width():
    node = {"type": "TABLE", "id": "t", "tableData": {"rowHeader": True}, "nodes": [
        {"type": "TABLE_ROW", "nodes": [{"type": "TABLE_CELL", "nodes": [_text(t)]} for t in ("A", "B")]},
        {"type": "TABLE_ROW", "nodes": [
            {"type": "TABLE_CELL", "nodes": [_text("x")]},
            {"type": "TABLE_CELL", "nodes": [{"type": "IMAGE", "id": "i9", "nodes": [], "imageData": {
                "image": {"src": {"id": "image1.png"}, "width": 164, "height": 164}}}]}]}]}
    out = _draw(node, {"image1": preview.animations("../anim")[BROCHURE]["image1"]})
    assert '<figure class="fig--anim fig--cell">' in out and 'tabindex="-1"' not in out


@pytest.mark.skipif(not os.path.isfile(os.path.join(build.BUILD, BROCHURE, "part-01.json")),
                    reason="build/ricos is written by tools/docx2ricos.py")
def test_the_brochure_draws_the_flow_with_the_four_icons(monkeypatch):
    monkeypatch.setattr(build, "VERBATIM", [])
    monkeypatch.setattr(build, "ANIM", preview.animations("../anim"))
    out = build.page_doc(BROCHURE)
    flow = re.search(r'<div class="flow">(.*?)</div><ul>', out, re.S).group(1)
    assert [re.search(r"<strong>(.*?)</strong>", s).group(1) for s in flow.split('class="flow__step"')[1:]] \
        == [html.escape(i[2], quote=False) for i in ICONS]
    assert re.findall(r'src="\.\./anim/(nf-hw-[a-z]+\.html)"', flow) == PAGES
    assert flow.count('class="flow__arrow"') == 3


# ------------------------------------------------------------------ the row's rules

def _flow_css():
    css = docs.CSS
    return css[css.index("/* ---------- a row of steps with his arrows between ---------- */"):
               css.index("/* ---------- his asides:")]


def test_the_row_gives_every_step_an_equal_share_and_every_arrow_its_own():
    css = _flow_css()
    assert "grid-auto-columns:minmax(0,1fr) auto" in css
    assert "grid-template-columns:minmax(0,1fr);justify-items:center" in css
    # a label may use the free half of the gap under the arrow beside it
    assert "max-width:calc(100% + var(--flow-arrow) + var(--flow-gap))" in css
    # an icon keeps his size and takes no full screen button
    assert ".js .docpage .doc .flow__step .anim__bar{display:none}" in css
    # a phone: a list, each picture beside its label, the arrows turned down between the pictures
    phone = css[css.index("@media (max-width:640px){"):]
    assert "grid-template-columns:auto minmax(0,1fr)" in phone and "grid-template-columns:subgrid" in phone
    assert "transform:rotate(90deg)" in phone
    # tokens only, and nothing hovers
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", css) and ":hover" not in css
    assert "—" not in css and not build.SPACED_EN.search(css)


def test_his_arrows_are_the_figures_arrow_and_draw_only_where_motion_is_welcome():
    css = _flow_css()
    # a hairline and a TikZ stealth tip (engine.js: corners at 0.38 rad, the notch 0.62 of the head back)
    assert ".docpage .flow__arrow::before{left:0;right:4px;top:5px;height:1px;" in css
    assert "clip-path:polygon(100% 50%,0 0,33.2% 50%,0 100%)" in css
    head = 7
    assert 6.5 == pytest.approx(head * np.cos(.38), abs=.01) and 5.2 == pytest.approx(2 * head * np.sin(.38), abs=.01)
    assert 1 - .62 / np.cos(.38) == pytest.approx(.332, abs=.001)
    # hidden and drawn only on a screen that welcomes motion; paper, less motion and no
    # script see the arrow as it is
    motion = css[css.index("@media screen and (prefers-reduced-motion:no-preference){"):css.index("@keyframes flow-shaft")]
    assert ".is-wait" not in css.replace(motion, "")
    assert "animation:flow-shaft var(--spring-fast) both" in motion
    # the shaft travels on the site's spring, the tip's opacity on the state curve
    assert "flow-tip-in var(--t-fast) var(--ease-state)" in motion
    for kf in re.findall(r"@keyframes flow-[a-z-]+\{from\{([^}]*)\}\}", css):
        assert re.fullmatch(r"(transform:[^;]+|opacity:0)", kf)


# ------------------------------------------------------------------ nothing overlaps

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
    ("hw-structure", [0.2, 0.4, 0.8, 1.2, 2.0, 3.0]),
    ("hw-sensors", [0.5, 0.8, 1.0, 1.2]),
    ("hw-analysis", [0.9, 1.1, 1.4, 1.7]),
    ("hw-decision", [1.2, 1.4, 1.6, 1.8]),
])
def test_nothing_overlaps(name, times):
    import common
    for when, r in common.overlaps(name, times).items():
        assert r["labels"] == [] and r["crossings"] == [], (when, r)
