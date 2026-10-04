"""His blog's figures redrawn in the house style of the course notes (his
request of 4 Oct 2026; tools/blogfig/): each a module drawing one picture of
one post, built to content/blog-figs/<slug>/<stem>.svg, which the site
publishes in place of the figure cut out of his screenshot, in the post and
on its card on the Blog."""

import importlib
import json
import os
import re
import sys
import xml.dom.minidom

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGDIR = os.path.join(ROOT, "tools", "blogfig")
sys.path.insert(0, os.path.join(ROOT, "site"))
sys.path.insert(0, FIGDIR)

import build  # noqa: E402
import make  # noqa: E402

SVGS = sorted(os.path.join(d, f) for d, _, fs in os.walk(build.BLOGFIGS) for f in fs if f.endswith(".svg"))


def test_every_figure_module_names_its_post_and_picture_and_is_built():
    seen = set()
    for name in make.FIGS:
        mod = importlib.import_module(name)
        assert re.fullmatch(r"[a-z0-9-]+", mod.SLUG) and re.fullmatch(r"[a-z0-9-]+", mod.STEM), name
        assert (mod.SLUG, mod.STEM) not in seen, f"{name}: a picture drawn twice"
        seen.add((mod.SLUG, mod.STEM))
        assert os.path.isfile(os.path.join(build.BLOGFIGS, mod.SLUG, mod.STEM + ".svg")), name
    # and nothing in content/blog-figs that no module draws
    built = {(os.path.basename(os.path.dirname(p)), os.path.splitext(os.path.basename(p))[0]) for p in SVGS}
    assert built == seen


@pytest.mark.parametrize("path", SVGS, ids=lambda p: os.path.relpath(p, build.BLOGFIGS))
def test_each_svg_is_whole_sized_slim_and_no_wider_than_the_page(path):
    doc = xml.dom.minidom.parse(path)
    svg = doc.documentElement
    w, h = float(svg.getAttribute("width")), float(svg.getAttribute("height"))
    assert 0 < w <= make_width_pt() and 0 < h < 600
    text = open(path, encoding="utf-8").read()
    assert not re.search(r"\d\.\d{3,}", text), "numbers kept past 0.01 pt (make.slim)"
    assert os.path.getsize(path) < 250_000
    # glyphs are outlines: no font to load, no text that could reflow
    assert "<text" not in text and "@font-face" not in text


def make_width_pt():
    import fscheck
    return fscheck.MAX_WIDTH


def test_redrawn_gives_the_figure_its_size_at_sixteen_tenths_of_a_pixel_to_the_point():
    path = SVGS[0]
    slug = os.path.basename(os.path.dirname(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    svg = xml.dom.minidom.parse(path).documentElement
    got = build.redrawn(slug, stem + ".png")
    assert got[0] == path
    assert got[1:] == (round(float(svg.getAttribute("width")) * 1.6),
                       round(float(svg.getAttribute("height")) * 1.6))
    assert build.redrawn(slug, "no-such-picture.png") is None


def fake_post(tmp_path, monkeypatch, redrawn_too):
    """A post with one screenshot set as text and one figure cut out of it."""
    from PIL import Image
    src, figs = tmp_path / "blog", tmp_path / "blog-figs"
    (src / "p1" / "text").mkdir(parents=True)
    Image.new("RGB", (300, 120), "white").save(src / "p1" / "text" / "fig1.png")
    (src / "p1" / "text" / "page1.html").write_text('<p>His words.</p><img data-crop="fig1.png" alt="Figure 1">',
                                                    encoding="utf-8")
    if redrawn_too:
        (figs / "p1").mkdir(parents=True)
        (figs / "p1" / "fig1.svg").write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="250.5" height="100" '
            'viewBox="0 0 250.5 100"></svg>', encoding="utf-8")
    monkeypatch.setattr(build, "BLOGSRC", str(src))
    monkeypatch.setattr(build, "BLOGFIGS", str(figs))
    monkeypatch.setattr(build, "CACHE", str(tmp_path / "cache"))
    return {"slug": "p1", "images": [{"file": "page1.png"}]}


def test_a_redrawn_figure_is_published_as_its_svg_in_the_post_and_on_the_card(tmp_path, monkeypatch):
    post = fake_post(tmp_path, monkeypatch, True)
    here = tmp_path / "out" / "post" / "p1"
    name, w, h = build.cut_out("p1", "fig1.png", 1, str(here))
    assert (name, w, h) == ("01-fig1.svg", 401, 160)
    assert (here / name).read_bytes() == (tmp_path / "blog-figs" / "p1" / "fig1.svg").read_bytes()
    assert not (here / "01-fig1.webp").exists()
    assert build.blog_picture(post) == {"src": "post/p1/01-fig1.svg", "w": 401, "h": 160}


def test_without_a_redrawing_the_cut_out_picture_is_published_as_before(tmp_path, monkeypatch):
    post = fake_post(tmp_path, monkeypatch, False)
    here = tmp_path / "out" / "post" / "p1"
    name, w, h = build.cut_out("p1", "fig1.png", 1, str(here))
    assert (name, w, h) == ("01-fig1.webp", 300, 120)
    assert (here / name).is_file()
    assert build.blog_picture(post) == {"src": "post/p1/01-fig1.webp", "w": 300, "h": 120}


def test_the_svg_type_is_one_wix_serves():
    assert build.file_types(["post/p1/01-fig1.svg"], no_word=True) == ([], [])


def test_digitized_data_names_the_picture_it_was_read_from():
    data = os.path.join(FIGDIR, "data")
    for f in sorted(os.listdir(data)):
        with open(os.path.join(data, f), encoding="utf-8") as fh:
            src = json.load(fh)["source"]
        assert re.fullmatch(r"post/[a-z0-9-]+/\d\d-[a-z0-9-]+\.webp", src), f
