"""His slide decks (parts/deck.py): the page each deck becomes, the names his
slides carry, and the pictures behind them.

Two decks, one viewer. presentation.html keeps what it always said (his
title, the count and how to move) and probability-statistics.html is no
longer a page in preparation but his Probability, statistics and estimation,
each slide named by its own title. Every slide the pages show is on disk in
the three widths the viewer asks for; with WAD_BUILD=1 the last test builds
the whole site and looks for them in the output.
"""

import html
import json
import os
import re
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import deck  # noqa: E402

CONTENT = os.path.join(ROOT, "content")
# the probability deck: his 73 slides and one of ours, the Kalman loop (66,
# 29 Sep 2026: "kalman filter between 65-66 ... kalman filter logic slide")
PROB = 74
# (source folder under content/, folder under deck/ in the build, slides)
DECKS = (("deck-phd", "phd", 177), ("deck-probstat", "probability", PROB))


def his_titles():
    with open(os.path.join(CONTENT, "deck-probstat", "titles.json"), encoding="utf-8") as fh:
        return json.load(fh)


def images(markup):
    return re.findall(r"<img [^>]+>", markup)


# ------------------------------------------------------------------ the page

def test_the_phd_page_reads_as_it_always_has():
    page = deck.render(177)
    assert "<h1>Extensive ppt regarding my MSc and PhD Research</h1>" in page
    assert '<p class="deck__meta">177 slides</p>' in page
    assert len(images(page)) == 177
    assert 'alt="Slide 12 of 177"' in page


def test_probability_statistics_opens_with_his_title_and_the_count():
    t = his_titles()
    page = deck.render(PROB, src="deck/probability/", title=t[0], titles=t)
    assert "<h1>Probability, statistics and estimation</h1>" in page
    assert '<p class="deck__meta">74 slides</p>' in page
    assert "Probability, statistics and estimation" == t[0]


def test_a_lede_passed_in_is_text():
    page = deck.render(3, src="deck/x/", lede='Three <b>slides</b> & "more"')
    assert '<p class="deck__meta">Three &lt;b&gt;slides&lt;/b&gt; &amp; "more"</p>' in page


def test_every_slide_offers_two_widths_and_the_width_it_is_shown_at():
    tags = images(deck.render(3, src="deck/x/"))
    assert len(tags) == 3
    for k, tag in enumerate(tags, 1):
        one = f"deck/x/s{k:03d}"
        assert f'src="{one}-960.webp"' in tag
        assert f'srcset="{one}-960.webp 960w, {one}-1600.webp 1600w"' in tag
        assert f'sizes="{deck.SIZES}"' in tag
        assert 'width="1600" height="900"' in tag
    # the first is the page's largest picture: fetched first; the rest wait
    assert 'loading="eager"' in tags[0] and 'fetchpriority="high"' in tags[0]
    assert all('loading="lazy"' in t and "fetchpriority" not in t for t in tags[1:])


def test_a_page_one_folder_down_reaches_the_pictures():
    assert 'src="../deck/x/s001-960.webp"' in deck.render(1, "../", src="deck/x/")


# ------------------------------------------------------------------ his titles

def test_the_74_slides_each_have_a_title():
    t = his_titles()
    assert len(t) == PROB and all(t)
    assert all(" ".join(x.split()) == x for x in t)          # whitespace collapsed
    assert t[71:] == ["References (1 of 3)", "References (2 of 3)", "References (3 of 3)"]
    # ours between his 65 and his 66, which is now the deck's 67
    assert t[64:67] == ["Kalman filtering: prediction meets a new measurement",
                        "The Kalman loop: predict, observe, weigh, update",
                        "One Kalman update, step by step"]


def test_a_slide_is_named_by_its_title_in_its_alt_text():
    t = his_titles()
    page = deck.render(PROB, src="deck/probability/", title=t[0], titles=t)
    alts = re.findall(r'alt="([^"]*)"', page)
    assert alts == [html.escape(f"Slide {k}: {x}") for k, x in enumerate(t, 1)]
    assert "Slide 62: Estimation methods: different criteria for choosing an answer" in alts
    assert "Slide 66: The Kalman loop: predict, observe, weigh, update" in alts
    assert "Slide 74: References (3 of 3)" in alts


def test_a_title_is_escaped_and_a_slide_without_one_goes_by_its_number():
    page = deck.render(3, src="deck/x/", titles=["One", 'Two & "three" <b>', ""])
    assert re.findall(r'alt="([^"]*)"', page) == [
        "Slide 1: One", "Slide 2: Two &amp; &quot;three&quot; &lt;b&gt;", "Slide 3 of 3"]


def test_the_script_reads_a_title_back_out_of_the_alt_text():
    # All slides and the live region take a slide's title from its alt text
    # after "Slide N: ", and a deck without titles says "Slide N of M"
    rx = re.compile(r"^Slide \d+(?:: | of \d+$)")
    assert r"/^Slide \d+(?:: | of \d+$)/" in deck.JS
    assert rx.sub("", "Slide 12: Kalman filtering") == "Kalman filtering"
    assert rx.sub("", "Slide 12 of 177") == ""


# ------------------------------------------------------------------ the viewer

def test_the_page_draws_what_the_script_wires():
    page = deck.render(5)
    assert 'data-go="-1" aria-label="Previous slide"' in page
    assert 'data-go="1" aria-label="Next slide"' in page
    assert '<span class="deck__at"><span class="deck__cur">1</span> / 5</span>' in page
    # Present and All slides stay hidden until the script finds the browser
    # can do them; ending a presentation is the capsule's last button
    assert re.search(r'<button class="deck__cta" [^>]*data-show [^>]*hidden>', page)
    assert re.search(r'<button [^>]*data-all [^>]*aria-haspopup="dialog"[^>]*hidden>', page)
    assert 'data-exit aria-label="End the presentation"' in page
    assert re.search(r'<p class="deck__vh deck__say" aria-live="polite"></p>', page)
    for hook in ("showModal()", "requestFullscreen", "webkitRequestFullscreen", "fullscreenchange",
                 "replaceState", "hashchange", "setPointerCapture", "prefers-reduced-motion"):
        assert hook in deck.JS


def test_the_pages_are_numbers_one_tab_stop():
    t = ["One", "Two", "Three"]
    page = deck.render(3, src="deck/x/", titles=t)
    nums = re.findall(r'<button class="deck__pg" type="button" data-n="(\d+)" tabindex="-1" '
                      r'aria-label="([^"]*)">(\d+)</button>', page)
    assert nums == [(str(k), f"Slide {k}: {x}", str(k)) for k, x in enumerate(t, 1)]
    # no slide carries its number as an id, which the browser would scroll to
    assert not re.search(r'<li id="\d+"', page)
    assert '<nav class="deck__nums" aria-label="Slides">' in page
    # the script makes the one on screen the row's stop for the Tab key
    assert "tabIndex=0" in deck.JS and "aria-current" in deck.JS


def test_present_is_the_one_filled_button():
    page = deck.render(4)
    assert page.count('class="deck__cta"') == 1 and ">Present</span>" in page
    assert ".deck.is-show" in deck.CSS and "backdrop-filter" in deck.CSS
    assert "prefers-reduced-transparency" in deck.CSS


def test_a_deck_with_vectors_draws_them_wherever_its_pictures_would_be_enlarged():
    # the client, 27 Sep 2026: presenting lowered the quality. The deck says
    # it has an SVG a slide; the script lays the SVG over the picture while
    # presenting, or where the stage has more device pixels than its largest
    # copy: a deck with vectors publishes no 1600 copy (28 Sep 2026), so past
    # the 960 its SVG takes over; a deck of pictures only keeps the 1600
    page = deck.render(3, src="deck/x/", vector=True)
    assert '<div class="deck" data-vector>' in page
    assert "-1600.webp" not in page and 's003-960.webp 960w"' in page
    plain = deck.render(3, src="deck/x/")
    assert '<div class="deck">' in plain and "s003-1600.webp 1600w" in plain
    assert "big=vec?960:1600" in deck.JS
    assert "data-vector" in deck.JS and ".replace(/-\\d+\\.webp$/,'.svg')" in deck.JS
    assert "showing()||st.clientWidth*(window.devicePixelRatio||1)" in deck.JS and ">big" in deck.JS
    assert "sharpen()" in deck.JS and "addEventListener('resize',sharpen)" in deck.JS
    # the SVG lies over the picture, which stays under it and shows first
    assert re.search(r"\.deck__list>li>img\.deck__vec\{position:absolute;inset:0;", deck.CSS)
    # presenting, the page's scrollbar gutter does not stay beside the slide
    assert "html.deck-show{overflow:hidden;scrollbar-gutter:auto}" in deck.CSS


def test_the_pdf_is_offered_under_the_title_as_a_word_file_is():
    t = his_titles()
    page = deck.render(PROB, src="deck/probability/", title=t[0], titles=t,
                       pdf=("deck/probability/deck.pdf", 2190686))
    link = re.search(r'<a class="deck__pdf" [^>]*>.*?</a>', page).group(0)
    assert 'href="deck/probability/deck.pdf"' in link
    assert 'download="Probability, statistics and estimation.pdf"' in link
    assert 'type="application/pdf"' in link
    assert '<span class="deck__pdft">Download PDF</span> <span class="deck__size">2.19&nbsp;MB</span>' in link
    assert '<p class="deck__meta"><span>74 slides</span><a class="deck__pdf"' in page
    # a page one folder down reaches it; a deck without a PDF offers none
    assert 'href="../deck/x/d.pdf"' in deck.render(1, "../", src="deck/x/", pdf=("deck/x/d.pdf", 1))
    assert "deck__pdf" not in deck.render(3, src="deck/x/")
    # a link in the site's download vocabulary: the words underlined in the
    # link's colour, the size muted, a 44px target, the focus ring outside hover
    assert ".deck__pdf{display:inline-flex;align-items:center;gap:8px;min-height:44px;" in deck.CSS
    assert "color:var(--link)" in deck.CSS
    assert ".deck__pdf:focus-visible{outline:2px solid var(--focus)" in deck.CSS
    assert "@media (hover:hover){ .deck__pdf:hover .deck__pdft{text-decoration-color:currentColor} }" in deck.CSS


def test_the_viewer_keeps_to_the_sites_colours_and_its_quiet():
    # the tokens of parts/theme.py; #fff is the stage under his white slides
    assert set(re.findall(r"#[0-9A-Fa-f]{3,6}\b", deck.CSS)) == {"#fff"}
    assert "@media (prefers-reduced-motion:reduce)" in deck.CSS
    assert "@media print" in deck.CSS
    for text in (deck.CSS, deck.JS, open(deck.__file__, encoding="utf-8").read()):
        assert not build.DASH.search(text) and not build.SPACED_EN.search(text)


# ------------------------------------------------------------------ the site

def test_probability_statistics_is_no_longer_in_preparation():
    assert "probability-statistics.html" not in build.SOON
    assert set(build.SOON) == {"python-programming.html", "communication.html"}
    card = next(i for i in build.topic_items() if i["href"] == "probability-statistics.html")
    assert card["soon"] is False
    line = build.PAGE_DESC["probability-statistics.html"]
    assert len(line) <= 180 and not build.DASH.search(line) and not build.SPACED_EN.search(line)
    assert line != build.PAGE_DESC["presentation.html"]


@pytest.mark.parametrize("source,folder,count", DECKS)
def test_every_slide_is_on_disk_in_the_three_widths(source, folder, count):
    from PIL import Image
    web = os.path.join(CONTENT, source, "web")
    have = {f for f in os.listdir(web) if re.fullmatch(r"s\d{3}-\d+\.webp", f)}
    assert have == {f"s{k:03d}-{w}.webp" for k in range(1, count + 1) for w in (320, 960, 1600)}
    for w in (320, 960, 1600):
        with Image.open(os.path.join(web, f"s{count:03d}-{w}.webp")) as im:
            assert im.size == (w, w * 9 // 16)
    # what the page asks for is what the build copies from here
    page = deck.render(count, src=f"deck/{folder}/")
    asked = set(re.findall(rf"deck/{folder}/(s\d{{3}}-\d+\.webp)", page))
    assert asked and asked <= have
    assert not [f for f in os.listdir(os.path.join(CONTENT, source)) if f.endswith(".pptx")]


PDF = os.path.join(CONTENT, "deck-probstat", "probability-statistics-and-estimation.pdf")


def test_the_probability_deck_is_on_disk_as_vectors():
    """An SVG a slide, standalone (it shows in an <img>, which loads nothing
    else), and none over the site's 3 MB a file."""
    web = os.path.join(CONTENT, "deck-probstat", "web")
    svgs = sorted(f for f in os.listdir(web) if f.endswith(".svg"))
    assert svgs == [f"s{k:03d}.svg" for k in range(1, PROB + 1)]
    total = 0
    for f in svgs:
        with open(os.path.join(web, f), encoding="utf-8") as fh:
            text = fh.read()
        total += len(text.encode())
        assert text.startswith('<svg xmlns="http://www.w3.org/2000/svg"') and 'viewBox="0 0 1440 810"' in text
        assert not re.search(r'(?:href|src)="(?!#|data:)', text), f   # nothing fetched
        assert "<text" not in text                                    # his words as outlines
        assert len(text.encode()) < 3_000_000
    assert total < 20_000_000
    # the PhD deck presents from vectors too (round 12, tools/deck/phd_vector.py,
    # tests/test_phd_vector.py): one per slide, and no PDF to download
    phd = [f for f in os.listdir(os.path.join(CONTENT, "deck-phd", "web")) if f.endswith(".svg")]
    assert len(phd) == 177
    assert not [f for f in os.listdir(os.path.join(CONTENT, "deck-phd")) if f.endswith(".pdf")]


def test_the_pdf_is_the_74_slides_as_vectors_named_and_small():
    import unicodedata
    fitz = pytest.importorskip("fitz")
    assert os.path.getsize(PDF) < 3_000_000                   # the site's limit for a file
    doc = fitz.open(PDF)
    assert len(doc) == PROB
    assert all(p.rect == fitz.Rect(0, 0, 1440, 810) for p in doc)   # 1920 x 1080 px a slide
    assert doc.metadata["title"] == "Probability, statistics and estimation"
    assert doc.metadata["author"] == "Korkut Kaynardag"
    toc = doc.get_toc()
    assert [e[2] for e in toc] == list(range(1, PROB + 1)) and all(e[0] == 1 for e in toc)

    def plain(s):
        return " ".join(unicodedata.normalize("NFKC", s).split())
    # his text is text: each page carries its own slide's title, in order,
    # and pictures are none (the figures are paths)
    for k, (page, title) in enumerate(zip(doc, his_titles()), 1):
        assert plain(title) in plain(page.get_text()), k
        assert not page.get_images(), k
    assert "orange tail is" in doc[36].get_text()
    # each page's running foot carries its place in the deck: the Kalman loop
    # is page 66, his 66 is our 67, and so on to 74 (his map, slide 2, has none)
    for k, page in enumerate(doc, 1):
        lines = [ln.strip() for ln in page.get_text().splitlines()]
        assert k == 2 or str(k) in lines, k
        assert k < 67 or str(k - 1) not in lines, k
    assert "The Kalman loop: predict, observe, weigh, update" in plain(doc[65].get_text())


def test_his_colour_words_keep_their_colour():
    # slide 30 names the tangent orange and slide 37 the tail: those two keep
    # his orange; every other mark of his takes the crimson
    src = os.path.join(ROOT, "tools", "deck", "src")
    users = sorted(f for f in os.listdir(src) if f.endswith(".py")
                   and "C.orange" in open(os.path.join(src, f), encoding="utf-8").read())
    assert users == ["s030.py", "s037.py"]
    assert "The tangent (orange)" in open(os.path.join(src, "s030.html"), encoding="utf-8").read()
    assert "orange tail is" in open(os.path.join(src, "s037.html"), encoding="utf-8").read()


@pytest.mark.skipif(not os.environ.get("WAD_BUILD"),
                    reason="builds the whole site, about 30s: WAD_BUILD=1 runs it")
def test_the_build_publishes_both_decks(tmp_path):
    out = tmp_path / "dist"
    subprocess.run([sys.executable, os.path.join(ROOT, "site", "build.py"), "--out", str(out)],
                   capture_output=True, text=True, timeout=600)
    # the PhD deck is pictures; the probability deck adds an SVG a slide and,
    # in this local build, its PDF
    assert len(os.listdir(out / "deck" / "phd")) == 3 * 177
    assert len(os.listdir(out / "deck" / "probability")) == 4 * PROB + 1
    for page, folder, count in (("presentation.html", "phd", 177),
                                ("probability-statistics.html", "probability", PROB)):
        text = (out / page).read_text(encoding="utf-8")
        assert text.count('<li><img src="deck/') == count
        assert all((out / r).is_file() for r in re.findall(r'"(deck/[a-z]+/s\d{3}-\d+\.webp)', text))
    text = (out / "probability-statistics.html").read_text(encoding="utf-8")
    assert "<title>Probability, statistics and estimation · Korkut Kaynardag</title>" in text
    assert 'alt="Slide 2: THE FULL WORKFLOW OF A PROBABILISTIC DECISION' in text
    assert '<div class="deck" data-vector>' in text
    pdf = re.search(r'<a class="deck__pdf" href="(deck/probability/[^"]+\.pdf)"', text).group(1)
    assert (out / pdf).is_file() and (out / pdf).stat().st_size == os.path.getsize(PDF)
    assert '<div class="deck" data-vector>' not in (out / "presentation.html").read_text(encoding="utf-8")
