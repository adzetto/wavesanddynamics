"""His MSc and PhD presentation as vectors (tools/deck/phd_vector.py).

presentation.html draws each of his 177 slides from content/deck-phd/web/sNNN.svg
while presenting. These tests hold the SVGs to what the site may publish: one
a slide, standalone, his words as outlines, no address but
korkutkaynardag@iyte.edu.tr, no phone number, no picture metadata, no file over
the site's 3 MB; and they hold the deck's folder to what the client asked for,
present mode only: no PDF, no .pptx.
"""

import base64
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))
sys.path.insert(0, os.path.join(ROOT, "tools", "deck"))

import build  # noqa: E402
import phd_vector  # noqa: E402

DECK = os.path.join(ROOT, "content", "deck-phd")
WEB = os.path.join(DECK, "web")
COUNT = 177


def svgs():
    for k in range(1, COUNT + 1):
        with open(os.path.join(WEB, f"s{k:03d}.svg"), encoding="utf-8") as fh:
            yield k, fh.read()


def test_one_svg_a_slide_and_nothing_else():
    names = sorted(f for f in os.listdir(WEB) if f.endswith(".svg"))
    assert names == [f"s{k:03d}.svg" for k in range(1, COUNT + 1)]
    # every slide the page shows as a picture has its vectors, so build.py
    # hands the viewer vector=True
    assert all(os.path.isfile(os.path.join(WEB, f"s{k:03d}-1600.webp")) for k in range(1, COUNT + 1))


def test_each_svg_stands_alone_and_is_small_enough():
    total = 0
    for k, text in svgs():
        size = len(text.encode())
        total += size
        assert text.startswith('<svg xmlns="http://www.w3.org/2000/svg"'), k
        assert 'viewBox="0 0 960 540"' in text, k                       # his 13.33 x 7.5 in slide
        assert not re.search(r'(?:href|src)="(?!#|data:)', text), k       # an <img> loads nothing else
        assert "<text" not in text and "data-text" not in text, k        # his words as outlines
        assert size < build.WIX_FILE_MAX, (k, size)
    assert total < 40_000_000, total


def test_no_address_but_his_institutional_one_and_no_phone_number():
    """The site's own privacy check (build.py's PRIVATE and EMAIL, which read
    every published .svg as text, picture data included) finds nothing; and no
    SVG carries an address at all, since his words are outlines."""
    for k, text in svgs():
        assert not build.PRIVATE.search(text), k
        assert not build.EMAIL.findall(text), k
        assert "@" not in text and "mailto:" not in text and "tel:" not in text, k


def test_no_picture_inside_carries_metadata():
    for k, text in svgs():
        for uri in re.findall(r'href="data:([^";,]+);base64,([^"]+)"', text):
            kind, data = uri
            assert kind in ("image/webp", "image/png", "image/jpeg"), (k, kind)
            assert not phd_vector.carries_metadata(base64.b64decode(data)), (k, kind)


def test_present_mode_only_no_pdf_and_no_pptx_in_the_deck_folder():
    # build.py publishes the first PDF it finds in content/deck-phd/; the
    # client asked for present mode alone, and his .pptx and notes never ship
    for root, _, names in os.walk(DECK):
        assert not [n for n in names if n.lower().endswith((".pdf", ".pptx", ".ppt"))], root


def test_the_copy_changes_only_what_the_published_pictures_show():
    # his address on slides 1 and 56, as painted over in the pictures
    swaps = phd_vector.SWAPS
    assert sorted(swaps) == ["ppt/slides/slide1.xml", "ppt/slides/slide56.xml"]
    for part, (digest, new) in swaps.items():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)          # the old paragraph, by its hash
        assert build.EMAIL.findall(new) == [phd_vector.ADDRESS] == [build.CONTACT["email"]]
        assert "<a:t>" + phd_vector.ADDRESS in new
    # slide 132's citation in the face PowerPoint drew the pictures with
    assert phd_vector.FONTS == {"ppt/slides/slide132.xml": (
        '<a:latin typeface="playfair display"/>', '<a:latin typeface="Calibri"/>', 4)}
    # the work folder never lies inside the deck's folder
    with pytest.raises(SystemExit):
        phd_vector.main(["privacy", "--work", os.path.join(DECK, "tmp")])


def test_the_phone_filter_still_catches_a_number():
    for s in ("+1 512 300 4065", "(512) 300-4065", "0232 750 68 13", "512-300-4065"):
        assert phd_vector.phone_like(s) or phd_vector.HIS_PHONES.search(s), s
    for s in phd_vector.NOT_PHONES | {"19.04.2023", "4/19/2023"}:
        assert not phd_vector.phone_like(s), s
