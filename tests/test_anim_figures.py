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
    # the article's Figure 1 is the waves guide's Figure 1 since 5 Oct 2026
    # (his notes: "Figure (animation) 1 in Waves and Dynamics => Fig 1 of this
    # section also"); the brochure keeps the building with sensors
    SHM: {"image2": "nf-building.html", "image4": "nf-shm-ndt.html",
          "image5": "nf-standing.html"},
    BROCHURE: {"image5": "nf-shm-sensors.html"},
}
BUILT = all(os.path.isfile(os.path.join(build.BUILD, s, "part-01.json")) for s in EXPECTED)


def test_each_of_his_files_redraws_the_pictures_it_was_matched_to():
    with open(os.path.join(ANIM, "anim.json"), encoding="utf-8") as fh:
        assert json.load(fh) == EXPECTED
    # every page in content/anim/ redraws a picture: anim.json's, or one of a
    # fragment's (anim.<name>.json, a set drawn apart), and none is left over
    # (a picture redrawn as several figures names a list of them)
    mapped = {f for pics in EXPECTED.values() for f in pics.values()}
    for n in os.listdir(ANIM):
        if re.fullmatch(r"anim\.[\w-]+\.json", n):
            with open(os.path.join(ANIM, n), encoding="utf-8") as fh:
                mapped |= {f for pics in json.load(fh).values() for v in pics.values()
                           for f in (v if isinstance(v, list) else [v])}
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
        for v in got[slug].values():
            for a in (v if isinstance(v, list) else [v]):
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
    # the article's Figure 1 is the waves guide's (5 Oct 2026), its frame named as there
    assert got[SHM]["image2"]["title"] == got[WAVES]["image12"]["title"]
    assert got[SHM]["image2"]["title"].startswith("Lateral natural dynamic response of a building")


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


def test_one_picture_redrawn_as_several_figures_shows_each_over_one_caption(tmp_path):
    # Figure 18 of the machine learning guide: what one neuron computes, then many
    # neurons together, each a figure of its own that fills the screen
    from PIL import Image
    (tmp_path / "anim.json").write_text('{"doc": {"image12": ["nf-a.html", "nf-b.html"]}}', encoding="utf-8")
    for n, h in (("a", 640), ("b", 540)):
        (tmp_path / f"nf-{n}.html").write_text(
            f"<title>Figure 18{n}: Part {n}</title><script>const W = 1000, H = {h};</script>", encoding="utf-8")
        Image.new("RGB", (1344, round(1.344 * h)), "white").save(tmp_path / f"nf-{n}.webp")
    parts = preview.animations("../anim", str(tmp_path))["doc"]["image12"]
    assert [a["src"] for a in parts] == ["../anim/nf-a.html", "../anim/nf-b.html"]
    assert [a["title"] for a in parts] == ["Part a", "Part b"] and [a["h"] for a in parts] == [640, 540]
    moving = _draw({"image12": parts})
    cap = re.search(r"<figcaption>.*?</figcaption>", _draw(None)).group(0)
    # one figure, each part a frame with its own button and printed frame, the caption once, last
    assert moving.startswith('<figure class="fig--parts"><div class="fig--anim"><iframe class="anim" '
                             'src="../anim/nf-a.html"') and moving.endswith(cap + "</figure>")
    assert moving.count('<div class="fig--anim">') == 2 and moving.count(preview.FULL) == 2
    assert moving.count("<figcaption>") == 1 and moving.count("<iframe") == 2
    assert 'style="aspect-ratio:1000/640"' in moving and 'style="aspect-ratio:1000/540"' in moving
    stills = re.findall(r'<img class="anim__still" ([^>]*)>', moving)
    assert [re.search(r'src="([^"]+)"', st).group(1) for st in stills] == ["../anim/nf-a.webp", "../anim/nf-b.webp"]
    # each part is a figure of its own to the page's script and styles (full screen, spacing)
    from parts import docs
    assert ".docpage .fig--parts>.fig--anim+.fig--anim{" in docs.CSS
    assert "document.querySelectorAll('.docpage .fig--anim')" in docs.JS
    # every part prints its frame, and a picture needs two parts at least
    (tmp_path / "nf-b.webp").unlink()
    with pytest.raises(ValueError, match="printed frame"):
        preview.animations("../anim", str(tmp_path))
    # and the real Figure 18 is two such figures in the guide
    with open(os.path.join(ANIM, "anim.ml-b.json"), encoding="utf-8") as fh:
        ml = json.load(fh)["machine-learning-the-complete-picture-and-guide-5"]
    assert ml["image15"] == ["nf-mlb-neuron.html", "nf-mlb-uat.html"]


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
    # (a picture redrawn as several figures stands for the list of them)
    moved = {re.search(r"/(image\d+)\.webp", was).group(1): srcs if len(srcs) > 1 else srcs[0]
             for was, now in zip(before, after) if "<iframe" in now
             for srcs in [re.findall(r'<iframe class="anim" src="\.\./anim/([^"]+)"', now)]}
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
    # the button sits after the frame, in the row under it, and says what it does
    assert preview.FULL in moving and moving.index("</iframe>") < moving.index('class="anim__full"')
    assert 'aria-label="Show this figure full screen"' in preview.FULL
    from parts import docs
    css, js = docs.CSS, docs.JS
    # full screen where the browser gives it, laid over the page where it does not
    assert ".docpage .fig--anim:is(:fullscreen,.is-full)" in css
    assert "requestFullscreen" in js and "fullscreenchange" in js and "Leave full screen" in js
    # the frame keeps its ratio and fills the screen with only its row of
    # buttons under it (42px): no caption, no number
    assert "calc((100dvh - 2 * var(--pad) - 42px) * var(--ar,1.6))" in css
    assert ".docpage .fig--anim:is(:fullscreen,.is-full) figcaption{display:none}" in css
    assert "@media print{.anim__bar{display:none!important}}" in css


def test_a_moving_figures_buttons_sit_in_a_row_under_it_and_drive_it():
    # laid over the frame, the buttons hid type in 16 of the machine learning
    # guide's 33 figures on a laptop and 27 on a phone (4 Oct 2026): now play or
    # pause, restart and full screen sit in a row under the frame, beside the caption
    moving, bar = _draw(MOVE), preview.BAR
    assert bar in moving and moving.index("</iframe>") < moving.index('class="anim__bar"') < moving.index("<figcaption>")
    assert bar.index('class="anim__pp"') < bar.index('class="anim__rs"') < bar.index('class="anim__full"')
    assert bar.count(" hidden>") == 2 and 'role="group"' in bar      # play and restart wait for the frame
    from parts import docs
    css, js = docs.CSS, docs.JS
    assert ".js .docpage .fig--anim>.anim__bar{display:flex;gap:8px;float:right;" in css
    rule = css[css.index(".js .docpage .fig--anim>.anim__bar{"):]
    assert "position" not in rule[:rule.index("}")]          # in the flow under the frame, not over it
    # the float stays inside its figure, and table cells keep their grid
    assert ".js .docpage .fig--anim:not(.fig--cell,:fullscreen,.is-full){display:flow-root}" in css
    assert ".js .docpage .tbl .fig--cell>.anim__bar{grid-area:2/1;" in css
    assert ".docpage .fig--anim.is-full{position:fixed;inset:0;z-index:1000;margin:0!important}" in css
    assert "nf:'toggle'" in js and "nf:'restart'" in js and "nf:'hello'" in js and "m.nf!=='state'" in js
    assert preview.PLAY_ICON in js and preview.PAUSE_ICON in js
    # the frame stands its own two down where the row is, and answers it
    sys.path.insert(0, os.path.join(ROOT, "tools", "numfig"))
    import common
    with open(os.path.join(ROOT, "tools", "numfig", "engine.js"), encoding="utf-8") as fh:
        engine = fh.read()
    assert "classList.add('chrome-out')" in engine and "nf: 'state'" in engine
    assert ".chrome-out .ctl :is(#pp,#rs){{display:none;}}" in common.HEAD
    # alone, its own buttons are never under 24 px
    assert "max-width:300px" not in common.HEAD and ".ctl button{{width:24px;height:24px;}}" in common.HEAD


def _chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chromium(), reason="needs Playwright's Chromium")
def test_in_a_browser_the_row_plays_pauses_and_restarts_the_frame_and_covers_none_of_it(tmp_path):
    import functools
    import http.server
    import shutil
    import threading
    from parts import docs
    from playwright.sync_api import sync_playwright
    name = "nf-mlb-activation.html"
    (tmp_path / "anim").mkdir()
    (tmp_path / "doc").mkdir()
    shutil.copy(os.path.join(ANIM, name), tmp_path / "anim" / name)
    shutil.copytree(os.path.join(ROOT, "content", "fonts-cmu"), tmp_path / "fonts")
    w, h = re.search(r"const W = (\d+), H = (\d+);", open(os.path.join(ANIM, name), encoding="utf-8").read()).groups()
    fig = preview._animated({"src": f"../anim/{name}", "title": "Activation", "w": w, "h": h},
                            'src="../anim/x.webp" alt="" width="10" height="10"',
                            "<figcaption>Figure 1. His caption.</figcaption>")
    (tmp_path / "doc" / "p.html").write_text(
        f'<!doctype html><html class="js"><meta charset="utf-8"><style>{docs.CSS}</style>'
        f'<div class="docpage"><div class="doc" style="width:672px">{fig}</div></div>'
        f'<script>(function(){{{docs.JS}}})();</script></html>', encoding="utf-8")
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(
        type("Q", (http.server.SimpleHTTPRequestHandler,), {"log_message": lambda *a: None}), directory=str(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 800, "height": 900})
            pg.goto(f"http://127.0.0.1:{srv.server_address[1]}/doc/p.html")
            frame = pg.frame_locator("iframe.anim")
            pg.wait_for_function("!document.querySelector('.anim__pp').hidden", timeout=20000)
            inner = pg.frames[1]
            # the frame's own pause and restart stand down; the row's speak for them
            assert inner.evaluate("getComputedStyle(document.getElementById('pp')).display") == "none"
            assert inner.evaluate("playing") is True
            assert pg.get_attribute(".anim__pp", "aria-label") == "Pause animation"
            pg.click(".anim__pp")
            pg.wait_for_function("document.querySelector('.anim__pp').getAttribute('aria-label') === 'Play animation'")
            assert inner.evaluate("playing") is False
            pg.click(".anim__rs")
            pg.wait_for_function("document.querySelector('.anim__pp').getAttribute('aria-label') === 'Pause animation'")
            assert inner.evaluate("playing") is True and inner.evaluate("t") < 1
            # no button lies on the frame
            box = pg.locator("iframe.anim").bounding_box()
            for sel in (".anim__pp", ".anim__rs", ".anim__full"):
                r = pg.locator(sel).bounding_box()
                assert r["y"] >= box["y"] + box["height"], sel
            assert frame.locator("canvas").count() == 1
            b.close()
    finally:
        srv.shutdown()


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


def test_a_still_without_words_takes_its_frames_title():
    """The audit of 5 Oct 2026: the printed stills of the signal guide's cover
    and his Figures 1, 3 and 8 had empty alt text (his Word pictures had none)."""
    fig = ('<figure class="fig--anim"><iframe class="anim" src="../anim/nf-x.html" '
           'title="A beam&#x27;s modes" loading="lazy"></iframe><div class="anim__bar"></div>'
           '<img class="anim__still" src="../anim/nf-x.webp" alt="" width="1344" height="672">'
           '<figcaption>Figure 4.</figcaption></figure>')
    assert 'alt="A beam&#x27;s modes" width="1344"' in build.still_alt(fig)
    # his own words stay, and a table's cell keeps its empty alt beside its label
    worded = fig.replace('alt=""', 'alt="His words"')
    assert build.still_alt(worded) == worded
    cell = fig.replace('class="fig--anim"', 'class="fig--anim fig--cell"')
    assert build.still_alt(cell) == cell
    # one figure's title never reaches the next figure's still
    two = fig.replace('alt=""', 'alt="His words"') + fig.replace("A beam&#x27;s modes", "A plate")
    assert build.still_alt(two).count('alt="A plate"') == 1 and "A beam&#x27;s modes\" w" not in build.still_alt(two)
