"""His animated figures (content/anim/) in place of the pictures they redraw.

Five files he sent on 26 Sep ("NDT ve waves vibrationdaki kisimlari bunlarla
degistirsek?"), each a canvas and a script. content/anim/anim.json names the
picture each one redraws in the waves guide, the SHM introduction and the
brochure; preview.animations() reads it with each file's title and canvas
size; build.py publishes the files to anim/ and page_doc() draws each in its
picture's place, over the picture's own caption, with the picture kept inside
the figure for print and for a page without a script.
"""

import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
import preview  # noqa: E402

ANIM = os.path.join(ROOT, "content", "anim")
WAVES = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
SHM = "understanding-shm-and-ndt"
BROCHURE = "brochure-shm-and-ndt-2-pages"
# His five files, and the seven figures of the waves guide redrawn from
# numerical models (tools/numfig/, 26 Sep 2026), which print their own frame.
NUMFIG = {"image12": "nf-building.html", "image13": "nf-resonance.html",
          "image14": "nf-standing.html", "image15": "nf-dispersion.html", "image17": "nf-safe.html", "image18": "nf-periodic.html",
          "image19": "nf-multispan.html", "image23": "nf-bulk-ut.html", "image24": "nf-guided-ut.html",
          "image25": "nf-coverage.html"}
EXPECTED = {
    WAVES: {**NUMFIG},
    SHM: {"image2": "nf-shm-sensors.html", "image4": "nf-shm-ndt.html",
          "image5": "nf-standing.html"},
    BROCHURE: {"image5": "nf-shm-sensors.html"},
}
BUILT = all(os.path.isfile(os.path.join(build.BUILD, s, "part-01.json")) for s in EXPECTED)


def test_each_of_his_files_redraws_the_pictures_it_was_matched_to():
    with open(os.path.join(ANIM, "anim.json"), encoding="utf-8") as fh:
        assert json.load(fh) == EXPECTED
    # every page in content/anim/ redraws a picture: anim.json's, or one of a
    # fragment's (anim.<name>.json, a set drawn apart), and none is left over
    mapped = {f for pics in EXPECTED.values() for f in pics.values()}
    for n in os.listdir(ANIM):
        if re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                mapped |= {f for pics in json.load(fh).values() for f in pics.values()}
    files = sorted(n for n in os.listdir(ANIM) if n.endswith(".html"))
    # or it is drawn only as a Big Picture card (tools/bp_art.py picks its still)
    with open(os.path.join(ROOT, "tools", "bp_art.py"), encoding="utf-8") as fh:
        cards = {f"{n}.html" for n in re.findall(r"content:anim/(nf-[\w-]+)\.webp", fh.read())}
    assert files == sorted(mapped | (cards & set(files)))


def test_a_fragment_adds_its_pictures_and_a_picture_named_twice_stops(tmp_path):
    (tmp_path / "anim.json").write_text('{"doc": {"image1": "a.html"}}', encoding="utf-8")
    for n in ("a", "b"):
        (tmp_path / f"{n}.html").write_text(
            f"<title>Figure 1: {n}</title><script>const W = 1000, H = 500;</script>", encoding="utf-8")
    (tmp_path / "anim.extra.json").write_text('{"doc": {"image2": "b.html"}}', encoding="utf-8")
    got = preview.animations("../anim", str(tmp_path))
    assert sorted(got["doc"]) == ["image1", "image2"] and got["doc"]["image2"]["src"] == "../anim/b.html"
    (tmp_path / "anim.twice.json").write_text('{"doc": {"image1": "b.html"}}', encoding="utf-8")
    with pytest.raises(ValueError, match="named twice"):
        preview.animations("../anim", str(tmp_path))


def test_the_frame_takes_the_canvas_ratio_and_the_title_without_its_number():
    got = preview.animations("../anim")
    # his documents, and any other a fragment redraws (each page a title and a size)
    assert set(EXPECTED) <= set(got)
    for slug in set(got) - set(EXPECTED):
        for a in got[slug].values():
            assert a["title"] and a["w"] > 0 and a["h"] > 0 and a["src"].startswith("../anim/nf-")
    # his last two files are redrawn too (round 11): every frame is an nf- page
    sizes = {"nf-shm-sensors.html": (1000, 500), "nf-shm-ndt.html": (1000, 548)}
    for name in NUMFIG.values():              # drawn 1000 wide, as tall as each needs
        a = next(v for v in got[WAVES].values() if v["src"] == f"../anim/{name}")
        assert a["w"] == 1000 and 400 <= a["h"] <= 1600
        sizes[name] = (a["w"], a["h"])
        # each prints its own frame, the width of two screen pixels to the point
        assert a["still"]["src"] == f"../anim/{name[:-5]}.webp" and a["still"]["w"] == 1344
    for slug, pics in EXPECTED.items():
        for stem, name in pics.items():
            a = got[slug][stem]
            assert a["src"] == f"../anim/{name}"
            assert (a["w"], a["h"]) == sizes[name]
            # his fig4 is Figure 4 in one document and Figure 3 in the other
            assert not re.match(r"Fig", a["title"]) and a["title"]
    # the waves guide's Figure 3 is ours now, named as his caption names it
    assert got[WAVES]["image14"]["title"] == "Flexural waves in a supported beam"
    assert got[SHM]["image2"]["title"] == "Example of a building's dynamic response"


def test_a_file_without_a_size_stops_the_build(tmp_path):
    (tmp_path / "anim.json").write_text('{"doc": {"image1": "x.html"}}', encoding="utf-8")
    (tmp_path / "x.html").write_text("<title>Figure 9: X</title><canvas></canvas>", encoding="utf-8")
    with pytest.raises(ValueError, match="canvas size"):
        preview.animations("../anim", str(tmp_path))
    assert preview.animations("../anim", str(tmp_path / "none")) == {}


IMAGE = {"type": "IMAGE", "id": "n9", "imageData": {"image": {
    "src": {"id": "image12.png"}, "width": 1344, "height": 1031}},
    "nodes": [{"type": "CAPTION", "nodes": [{"type": "TEXT", "textData": {
        "text": "Figure 1. A building.", "decorations": []}}]}]}
META = {"n9": {"src": "../fig/d/image12.webp", "w": 1344, "h": 1031, "zoom": True,
               "src720": "../fig/d/image12-720.webp", "sizes": "672px"}}
MOVE = {"image12": {"src": "../anim/a.html", "title": "A building's frame", "w": 1000, "h": 790}}


def _draw(anim):
    preview.plan([IMAGE], META, anim)
    try:
        return preview.render(IMAGE, "../fig/d")
    finally:
        preview.plan([])


def test_the_animation_stands_where_the_picture_stood_over_its_caption():
    still, moving = _draw(None), _draw(MOVE)
    cap = re.search(r"<figcaption>.*?</figcaption>", still).group(0)
    assert moving.startswith('<figure class="fig--anim"><iframe class="anim" src="../anim/a.html" '
                             'title="A building&#x27;s frame" loading="lazy" '
                             'style="aspect-ratio:1000/790"></iframe>')
    assert moving.endswith(cap + "</figure>")
    # the picture stays for paper and for a page with no script, the same file
    img = re.search(r'<img class="anim__still" ([^>]*)>', moving).group(1)
    assert 'src="../fig/d/image12.webp"' in img and 'srcset="../fig/d/image12-720.webp 720w' in img
    assert 'width="1344" height="1031"' in img and 'loading="lazy"' in img
    assert "figzoom" not in moving
    assert preview.USAGE["../fig/d/image12.webp"] >= {"framed"}
    # the plan is the document's: the next one draws the picture
    assert "<iframe" not in _draw(None)


def test_a_figure_redrawn_from_a_model_prints_its_own_frame(tmp_path):
    from PIL import Image
    (tmp_path / "anim.json").write_text('{"doc": {"image12": "nf-x.html"}}', encoding="utf-8")
    (tmp_path / "nf-x.html").write_text(
        "<title>Figure 4: A beam</title><script>const W = 1000, H = 500;</script>",
        encoding="utf-8")
    Image.new("RGB", (1344, 672), "white").save(tmp_path / "nf-x.webp")
    got = preview.animations("../anim", str(tmp_path))["doc"]["image12"]
    assert got["still"] == {"src": "../anim/nf-x.webp", "w": 1344, "h": 672}
    moving = _draw({"image12": got})
    img = re.search(r'<img class="anim__still" ([^>]*)>', moving).group(1)
    # its own frame, not the Word picture it replaces, and no copy of that one
    assert img.startswith('src="../anim/nf-x.webp" alt="" width="1344" height="672"')
    assert "srcset" not in img and "image12" not in img
    # his own files bring no frame: the Word picture stays
    assert "still" not in MOVE["image12"] and 'src="../fig/d/image12.webp"' in _draw(MOVE)


def test_the_page_shows_the_frame_only_where_a_script_runs_and_the_picture_on_paper():
    from parts import docs
    css = docs.CSS
    assert ".docpage :is(.doc,.dochead) .anim{display:none}" in css
    assert ".js .docpage :is(.doc,.dochead) .anim{display:block" in css
    assert ".js .docpage :is(.doc,.dochead) .anim__still{display:none}" in css
    paper = css.split("@media print{", 1)[1]
    assert ".js .docpage :is(.doc,.dochead) .anim{display:none}" in paper
    assert ".js .docpage :is(.doc,.dochead) .anim__still{display:block}" in paper
    assert "beforeprint" in docs.JS
    import inspect
    for text in (css, docs.JS, inspect.getsource(preview.animations),
                 inspect.getsource(preview._animated)):
        assert "—" not in text and not build.SPACED_EN.search(text)


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
@pytest.mark.parametrize("slug", sorted(EXPECTED))
def test_his_figures_keep_their_numbers_and_captions(slug, monkeypatch):
    def figures(page):
        body = page.split('<div class="doc">', 1)[1]
        return re.findall(r"<figure[^>]*>(.*?)</figure>", body, re.S)

    monkeypatch.setattr(build, "VERBATIM", [])
    monkeypatch.setattr(build, "ANIM", {})
    before = figures(build.page_doc(slug))
    monkeypatch.setattr(build, "ANIM", preview.animations("../anim"))
    after = figures(build.page_doc(slug))
    # New worked examples have lettered numbers; the original Word figures
    # and their captions still stay in exactly the same order.
    supplements = {m["src"].rsplit("/", 1)[-1] for key, m in build.ANIM.get(slug, {}).items()
                   if key.startswith("supplement-")}
    added = [f for f in after if any(f'../anim/{name}"' in f for name in supplements)]
    assert len(added) == len(supplements)
    after = [f for f in after if f not in added]
    assert len(before) == len(after)
    caps = [re.findall(r"<figcaption>.*?</figcaption>", f) for f in before]
    assert caps == [re.findall(r"<figcaption>.*?</figcaption>", f) for f in after]
    # the picture each frame stands for, read from the page before the frames
    # (a redrawn figure prints its own frame, so its picture's name is gone)
    moved = {re.search(r"/(image\d+)\.webp", was).group(1):
             re.search(r'src="\.\./anim/([^"]+)"', now).group(1)
             for was, now in zip(before, after) if "<iframe" in now}
    # anim.json's pictures of the document and its fragments' (anim.<name>.json),
    # those in its body (a cover in the head is drawn apart)
    want = dict(EXPECTED[slug])
    for n in os.listdir(ANIM):
        if re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                want.update(json.load(fh).get(slug, {}))
    body = {m.group(1) for f in before for m in [re.search(r"/(image\d+)\.webp", f)] if m}
    assert moved == {k: v for k, v in want.items() if k in body}
    if slug == BROCHURE:     # his diagram's description still names the picture
        assert 'nf-shm-sensors.webp" alt="Diagram: the vibration of a structure' in "".join(after)


def test_a_moving_figure_can_fill_the_screen():
    moving = _draw(MOVE)
    # the button sits over the frame, after it, and says what it does
    assert preview.FULL in moving and moving.index("</iframe>") < moving.index('class="anim__full"')
    assert 'aria-label="Show this figure full screen"' in preview.FULL
    from parts import docs
    css, js = docs.CSS, docs.JS
    # full screen where the browser gives it, laid over the page where it does not
    assert ".docpage .fig--anim:is(:fullscreen,.is-full)" in css
    assert "requestFullscreen" in js and "fullscreenchange" in js and "Leave full screen" in js
    # the frame keeps its ratio and fills the screen alone: no caption, no number
    assert "calc((100dvh - 2 * var(--pad)) * var(--ar,1.6))" in css
    assert ".docpage .fig--anim:is(:fullscreen,.is-full) figcaption{display:none}" in css
    assert "@media print{.anim__full{display:none!important}}" in css


def test_every_redrawn_figure_is_set_in_computer_modern_and_drawn_without_orange():
    # round 11: the client asked for Computer Modern in every figure and no
    # burnt orange. CMU Serif lacks the maths signs (<=, ~, partial ...), so
    # Figure Math (Latin Modern Math's) stands right behind it, loaded before
    # the first frame; orange is left only where his caption names it (kNN)
    ttLib = pytest.importorskip("fontTools.ttLib")
    fonts = os.path.join(ROOT, "content", "fonts-cmu")
    upright = set(ttLib.TTFont(os.path.join(fonts, "cmu-serif-500-roman.woff2")).getBestCmap())
    upright |= set(ttLib.TTFont(os.path.join(fonts, "figure-math.woff2")).getBestCmap())
    pages = sorted(f for f in os.listdir(ANIM) if f.startswith("nf-") and f.endswith(".html"))
    assert len(pages) >= 55
    for page in pages:
        with open(os.path.join(ANIM, page), encoding="utf-8") as fh:
            s = fh.read()
        assert '"CMU Serif", "Figure Math"' in s and "../fonts/figure-math.woff2" in s, page
        assert "document.fonts.load('500 16px \"Figure Math\"'" in s, page
        for face in ("Calibri", "Arial", "Helvetica", "Cambria", "sans-serif"):
            assert face not in s, (page, face)
        # every sign the script can set has a Computer Modern glyph: none
        # falls through to a system face
        script = s.split("<script>", 1)[1]
        assert not {ch for ch in script if ord(ch) > 126 and ord(ch) not in upright}, page
        if page != "nf-mlb-knn.html":
            for warm in ("#A5510B", "#D9822B", "#F2C39A", "#FBEBDD", "#7B3D0C"):
                assert warm.lower() not in s.lower(), (page, warm)
