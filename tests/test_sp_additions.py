"""The signal processing guide after the professor's notes of 5 Oct 2026: the
shared foundations as its cover, the old cover at the head of its section
"Signal Processing and System Identification", new figures and words in the
inverse problems, optimization and blind source separation sections, and its
figures numbered 1 to 13 in turn, his references following them."""
import html
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
import preview  # noqa: E402

BUILT = os.path.isfile(os.path.join(build.BUILD, build.SIGNAL, "part-01.json"))
ORDER = ["nf-sp-io", "nf-sp-cover", "nf-sp-adaptive", "nf-sp-inv-reg", "nf-sp-inv-iter",
         "nf-sp-inv-update", "nf-sp-opt-types", "nf-sp-landscape", "nf-sp-opt-global",
         "nf-sp-bss-ica", "nf-sp-bss-sobi", "nf-sp-delay-gcc", "nf-sp-delay-shots"]


@pytest.fixture(scope="module")
def page():
    if not BUILT:
        pytest.skip("needs build/ricos (tools/docx2ricos.py)")
    build.ANIM.clear()
    build.ANIM.update(preview.animations("../anim", os.path.join(ROOT, "content", "anim")))
    return build.page_doc(build.SIGNAL)


def _text(markup):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", markup)).split())


def test_the_cover_is_the_shared_foundations(page):
    head = re.search(r'<header class="dochead.*?</header>', page, re.S).group(0)
    assert '../anim/nf-sp-foundations.html' in head and "nf-sp-cover.html" not in head


def test_the_figures_read_1_to_13_in_turn_each_where_it_belongs(page):
    body = page[page.index('<div class="doc">'):]
    frames = re.findall(r'<iframe class="anim" src="\.\./anim/([\w-]+)\.html"', body)
    assert frames == ORDER
    caps = re.findall(r'<figcaption><span class="fign">Figure (\d+)\.</span>', body)
    assert caps == [str(k) for k in range(1, 14)]
    # each in its section
    sections = re.split(r'<h2 id="([^"]+)">', body)
    where = {}
    for sid, part in zip(sections[1::2], sections[2::2]):
        for f in re.findall(r'<iframe class="anim" src="\.\./anim/([\w-]+)\.html"', part):
            where[f] = sid
    assert where["nf-sp-cover"] == "signal-processing-and-system-identification"
    assert {where[f] for f in ORDER[3:6]} == {"inverse-problems-and-regularization"}
    assert {where[f] for f in ORDER[6:9]} == {"optimization"}
    assert {where[f] for f in ORDER[9:]} == {"blind-source-separation"}


def test_the_old_cover_opens_its_section_and_his_references_follow_the_new_numbers(page):
    body = page[page.index('<div class="doc">'):]
    sec = body[body.index('<h2 id="signal-processing-and-system-identification">'):]
    assert sec.index("nf-sp-cover.html") < sec.index("<p>")
    text = _text(body)
    assert "shown in Figure 3, the same input signal is fed" in text
    assert "Figure 8 illustrates the difference" in text
    assert "So, this fits the same picture as Figure 1" in text


def test_the_blind_source_separation_section_opens_with_his_words(page):
    body = page[page.index('<h2 id="blind-source-separation">'):]
    first = re.search(r"<p>(.*?)</p>", body, re.S).group(1)
    assert _text(first) == "For this, I will get into details a bit."
