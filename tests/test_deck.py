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
# the probability deck: his 73 slides and one of ours, the Kalman loop (29 Sep
# 2026: "kalman filter between 65-66 ... kalman filter logic slide"), lettered
# 65a after his 65 since 30 Sep: his slides keep his numbers
PROB = 74
# (source folder under content/, folder under deck/ in the build, slides)
DECKS = (("deck-phd", "phd", 177), ("deck-probstat", "probability", PROB))


def rows():
    """The probability deck's manifest (tools/deck/render.py): a row a slide
    in order, its label, stem, title and, for one that plays, its length."""
    with open(os.path.join(CONTENT, "deck-probstat", "deck.json"), encoding="utf-8") as fh:
        return json.load(fh)


def his_titles():
    return [r["title"] for r in rows()]


def prob_page(**kw):
    r = rows()
    return deck.render(PROB, src="deck/probability/", title=r[0]["title"], slides=r, **kw)


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
    page = prob_page()
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
    # ours between his 65 and his 66, lettered after the one it follows
    assert t[64:67] == ["Kalman filtering: prediction meets a new measurement",
                        "The Kalman loop: predict, observe, weigh, update",
                        "One Kalman update, step by step"]
    assert [r["label"] for r in rows()][63:68] == ["64", "65", "65a", "66", "67"]


def test_a_slide_is_named_by_its_label_and_title_in_its_alt_text():
    page = prob_page()
    alts = re.findall(r'alt="([^"]*)"', page)
    assert alts == [html.escape(f"Slide {r['label']}: {r['title']}") for r in rows()]
    assert "Slide 62: Estimation methods: different criteria for choosing an answer" in alts
    assert "Slide 65a: The Kalman loop: predict, observe, weigh, update" in alts
    assert "Slide 66: One Kalman update, step by step" in alts
    assert "Slide 73: References (3 of 3)" in alts


def test_a_title_is_escaped_and_a_slide_without_one_goes_by_its_number():
    page = deck.render(3, src="deck/x/", titles=["One", 'Two & "three" <b>', ""])
    assert re.findall(r'alt="([^"]*)"', page) == [
        "Slide 1: One", "Slide 2: Two &amp; &quot;three&quot; &lt;b&gt;", "Slide 3 of 3"]


def test_the_script_reads_a_title_and_a_label_back_out_of_the_alt_text():
    # All slides and the live region take a slide's title from its alt text
    # after "Slide N: ", and a deck without titles says "Slide N of M"; N is
    # its label, a number or ours after it with a letter
    rx = re.compile(r"^Slide \d+[a-z]*(?:: | of \d+[a-z]*$)")
    assert r"/^Slide \d+[a-z]*(?:: | of \d+[a-z]*$)/" in deck.JS
    assert rx.sub("", "Slide 12: Kalman filtering") == "Kalman filtering"
    assert rx.sub("", "Slide 65a: The Kalman loop") == "The Kalman loop"
    assert rx.sub("", "Slide 12 of 177") == ""
    assert r"/^Slide (\d+[a-z]*)/" in deck.JS


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


def test_a_lettered_deck_goes_by_its_labels():
    """The capsule, the numbers under the slide and the address name a slide
    by its label; the capsule counts to the deck's last number."""
    page = prob_page(vector=True)
    assert '<span class="deck__at"><span class="deck__cur">1</span> / 73</span>' in page
    nums = re.findall(r'<button class="deck__pg" type="button" data-n="(\d+)" [^>]*>([^<]+)</button>', page)
    assert [n for n, _ in nums] == [str(k) for k in range(1, PROB + 1)]
    assert [x for _, x in nums] == [r["label"] for r in rows()]
    assert ("66", "65a") in nums and ("67", "66") in nums and ("74", "73") in nums
    # the files are the stems'
    assert 'src="deck/probability/s065a-960.webp"' in page and "s074" not in page
    for hook in ("cur.textContent=lab(i)", "'#'+lab(i)", "'Slide '+lab(i)+' of '+last",
                 "/^#(\\d+[a-z]*)$/i"):
        assert hook in deck.JS, hook
    # a deck without a manifest goes by 1 to its count, as it always has
    plain = deck.render(3, src="deck/x/")
    assert '<span class="deck__at"><span class="deck__cur">1</span> / 3</span>' in plain
    with pytest.raises(ValueError):
        deck.render(3, src="deck/x/", slides=[{"label": "1", "stem": "s001", "title": "One"}])


def test_a_slide_that_plays_brings_its_page_over_the_picture():
    """tools/deck/anim.js: the slide's own page opens in a frame over its
    picture, held (?wait) and unseen until it has drawn its first moment,
    then plays; at its end, or when the slide goes, the frame goes.
    Presenting, a step on while it plays completes it first."""
    page = prob_page(vector=True)
    plays = [r["stem"] for r in rows() if r.get("anim")]
    assert "s065a" in plays
    assert re.findall(r'<li data-anim="([^"]+)">', page) == [f"deck/probability/anim/{s}.html" for s in plays]
    assert page.count("<li><img ") == PROB - len(plays)
    for hook in ("f.src=src+'?wait'", "deckAnim:'play'", "deckAnim:'finish'", "e.source!==p.f.contentWindow",
                 "m==='ready'", "m==='done'", "if(!src||reduce.matches)return", "play(i)",
                 "k===i+1&&showing()&&playing&&playing.k===i&&!playing.done"):
        assert hook in deck.JS, hook
    assert ".deck__list>li>iframe.deck__anim{position:absolute;inset:0;" in deck.CSS
    assert "pointer-events:none;visibility:hidden}" in deck.CSS
    assert ".deck__acts,.deck__bar,.deck__nums,.deck__all,.deck__anim{display:none!important}" in deck.CSS


def _chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


# a slide's page as anim.js speaks to its viewer: ready once drawn, done a
# second after it is told to play, or at once when told to finish
_FAKE = """<!doctype html><html><body style="margin:0;background:#fff"><script>
var t=0;function tell(m){parent.postMessage({deckAnim:m},'*')}
addEventListener('message',function(e){var m=e.data&&e.data.deckAnim;
  if(m==='play')t=setTimeout(function(){tell('done')},1000);
  else if(m==='finish'){clearTimeout(t);tell('done')}});
requestAnimationFrame(function(){tell('ready')});
</script></body></html>"""


@pytest.mark.skipif(not _chromium(), reason="needs Playwright's Chromium")
def test_the_viewer_plays_a_slide_then_lets_its_frame_go(tmp_path):
    import functools
    import http.server
    import threading
    from PIL import Image
    from playwright.sync_api import sync_playwright
    from parts import theme
    slides = [{"label": "1", "stem": "s001", "title": "One"},
              {"label": "1a", "stem": "s001a", "title": "Ours", "anim": 1.0},
              {"label": "2", "stem": "s002", "title": "Two"}]
    d = tmp_path / "deck" / "x"
    (d / "anim").mkdir(parents=True)
    for r in slides:
        for w in (320, 960, 1600):
            Image.new("RGB", (w, w * 9 // 16), "white").save(d / f"{r['stem']}-{w}.webp")
    (d / "anim" / "s001a.html").write_text(_FAKE, encoding="utf-8")
    body = deck.render(3, src="deck/x/", title="Deck", slides=slides)
    (tmp_path / "p.html").write_text(
        '<!doctype html><html class="js"><meta charset="utf-8"><style>' + theme.CSS + deck.CSS +
        "</style><body>" + body + "<script>(function(){" + deck.JS + "})();</script></body></html>",
        encoding="utf-8")

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(tmp_path)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/p.html"
    frame = "document.querySelector('iframe.deck__anim')"
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1100, "height": 800})
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(url)
            pg.wait_for_timeout(300)
            assert pg.evaluate(f"!!{frame}") is False
            pg.keyboard.press("ArrowRight")
            assert pg.eval_on_selector(".deck__at", "e => e.textContent") == "1a / 2"
            assert pg.evaluate("location.hash") == "#1a"
            assert pg.evaluate(f"{frame}.getAttribute('src')") == "deck/x/anim/s001a.html?wait"
            pg.wait_for_function(f"{frame} && {frame}.classList.contains('is-on')", timeout=5000)
            pg.wait_for_function(f"!{frame}", timeout=5000)            # done: the picture is the slide
            # presenting, a step on while it plays completes it and stays
            pg.keyboard.press("ArrowLeft")
            pg.keyboard.press("p")
            pg.keyboard.press("ArrowRight")
            pg.wait_for_function(f"{frame} && {frame}.classList.contains('is-on')", timeout=5000)
            pg.keyboard.press("ArrowRight")
            pg.wait_for_function(f"!{frame}", timeout=900)
            assert pg.eval_on_selector(".deck__at", "e => e.textContent") == "1a / 2"
            pg.keyboard.press("ArrowRight")
            assert pg.eval_on_selector(".deck__at", "e => e.textContent") == "2 / 2"
            # leaving a slide that plays takes its frame away
            pg.keyboard.press("Escape")
            pg.goto(url + "?again#1a")
            pg.wait_for_function(f"!!{frame}", timeout=5000)
            pg.keyboard.press("ArrowRight")
            assert pg.evaluate(f"!!{frame}") is False
            b.close()
    finally:
        srv.shutdown()
    assert errors == []


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
    page = prob_page(pdf=("deck/probability/deck.pdf", 2190686))
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
    assert set(build.SOON) == {"python-programming.html", "communication.html",
                               "personal-advices.html"}
    card = next(i for i in build.topic_items() if i["href"] == "probability-statistics.html")
    assert card["soon"] is False
    line = build.PAGE_DESC["probability-statistics.html"]
    assert len(line) <= 180 and not build.DASH.search(line) and not build.SPACED_EN.search(line)
    assert line != build.PAGE_DESC["presentation.html"]


@pytest.mark.parametrize("source,folder,count", DECKS)
def test_every_slide_is_on_disk_in_the_three_widths(source, folder, count):
    from PIL import Image
    web = os.path.join(CONTENT, source, "web")
    stems = [r["stem"] for r in rows()] if source == "deck-probstat" else [f"s{k:03d}" for k in range(1, count + 1)]
    assert len(stems) == count
    have = {f for f in os.listdir(web) if re.fullmatch(r"s\d{3}[a-z]*-\d+\.webp", f)}
    assert have == {f"{s}-{w}.webp" for s in stems for w in (320, 960, 1600)}
    for w in (320, 960, 1600):
        with Image.open(os.path.join(web, f"{stems[-1]}-{w}.webp")) as im:
            assert im.size == (w, w * 9 // 16)
    # what the page asks for is what the build copies from here
    page = prob_page() if source == "deck-probstat" else deck.render(count, src=f"deck/{folder}/")
    asked = set(re.findall(rf"deck/{folder}/(s\d{{3}}[a-z]*-\d+\.webp)", page))
    assert asked and asked <= have
    assert not [f for f in os.listdir(os.path.join(CONTENT, source)) if f.endswith(".pptx")]


PDF = os.path.join(CONTENT, "deck-probstat", "probability-statistics-and-estimation.pdf")


def test_the_probability_deck_is_on_disk_as_vectors():
    """An SVG a slide, standalone (it shows in an <img>, which loads nothing
    else), and none over the site's 3 MB a file."""
    web = os.path.join(CONTENT, "deck-probstat", "web")
    svgs = sorted(f for f in os.listdir(web) if f.endswith(".svg"))
    assert svgs == sorted(f"{r['stem']}.svg" for r in rows())
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
    # each page's running foot carries its label: the Kalman loop is page 66
    # of the PDF and reads 65a, his 66 reads 66, and so on to his 73 (his map,
    # slide 2, has none); the bookmarks say the same
    labels = [r["label"] for r in rows()]
    for k, (page, lab) in enumerate(zip(doc, labels), 1):
        lines = [ln.strip() for ln in page.get_text().splitlines()]
        assert lab == "2" or lab in lines, k
        assert k < 67 or str(k) not in lines, k
    assert "The Kalman loop: predict, observe, weigh, update" in plain(doc[65].get_text())
    assert [e[1].split("  ")[0] for e in toc] == labels


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
    # both decks are vectors, each slide its 320 and 960 copies and its SVG;
    # the probability deck adds, in this local build, its PDF, and the pages
    # its slides that play play in (anim/)
    assert len(os.listdir(out / "deck" / "phd")) == 3 * 177
    assert len(os.listdir(out / "deck" / "probability")) == 3 * PROB + 2
    plays = [f"{r['stem']}.html" for r in rows() if r.get("anim")]
    assert sorted(os.listdir(out / "deck" / "probability" / "anim")) == sorted(["anim.js", "deck.css", "deck.js"] + plays)
    assert (out / "fonts" / "latinmodern-math-deck.woff2").is_file()
    for page, folder, count in (("presentation.html", "phd", 177),
                                ("probability-statistics.html", "probability", PROB)):
        text = (out / page).read_text(encoding="utf-8")
        assert len(re.findall(r'<li(?: data-anim="[^"]+")?><img src="deck/', text)) == count
        assert all((out / r).is_file() for r in re.findall(r'"(deck/[a-z]+/s\d{3}[a-z]*-\d+\.webp)', text))
    text = (out / "probability-statistics.html").read_text(encoding="utf-8")
    assert "<title>Probability, statistics and estimation · Korkut Kaynardag</title>" in text
    assert 'alt="Slide 2: THE FULL WORKFLOW OF A PROBABILISTIC DECISION' in text
    assert '<div class="deck" data-vector>' in text
    pdf = re.search(r'<a class="deck__pdf" href="(deck/probability/[^"]+\.pdf)"', text).group(1)
    assert (out / pdf).is_file() and (out / pdf).stat().st_size == os.path.getsize(PDF)
    assert '<div class="deck" data-vector>' not in (out / "presentation.html").read_text(encoding="utf-8")
