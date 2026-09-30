"""The site's sections: the column, the home page's band, the checks, the gallery, the blog.

These hold the shapes the client decided. The column (design/ROUND4_SPEC.md
section 2, 24 Sep, and his change of 25 Sep): the six rows his topics left,
with his sub-lines, the topics themselves in the Big Picture row's list
(tests/test_bpnav.py), and the marking rules, as build.py writes them while
parts/bpnav.py is not loaded; his portrait at the
head of the column and in the phone's bar (ROUND5_SPEC.md section 1). The
band across the home page (section 3.1), his words checked against his deck,
no link into a section of a document, and what must never be published
(section 8). The Gallery as his Wix photos with the
repeated set shown once; the blog's Ricos bodies rendered with the two node
types the documents never used (VIDEO and FILE); and what may go to Wix's
static host.
"""

import io
import json
import os
import re
import sys
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
import preview  # noqa: E402
from parts import blog as blog_part  # noqa: E402
from parts import gallery as gallery_part  # noqa: E402

GONE = ("documents.html", "vibrations-waves.html", "signal-processing.html",
        "machine-learning.html")


def rows(markup):
    """The column's rows: (href, title, sub-line or "", the <a> tag's attributes)."""
    out = []
    for attrs, inner in re.findall(r"<li[^>]*><a ([^>]*)>(.*?)</a></li>", markup, re.S):
        href = re.search(r'href="([^"]+)"', attrs).group(1)
        title = re.search(r'<span class="nav__t"[^>]*>(.*?)</span>', inner).group(1)
        sub = re.search(r'<span class="nav__s"[^>]*>(.*?)</span>', inner)
        out.append((href, title.replace("\u00a0", " "), sub.group(1) if sub else "", attrs))
    return out


def marked(markup):
    """{href: aria-current value} for every marked row."""
    return {h: re.search(r'aria-current="([^"]+)"', a).group(1)
            for h, _, _, a in rows(markup) if "aria-current" in a}


# ------------------------------------------------------------------ the column

def test_the_column_has_its_rows_in_his_order():
    # his topics left the column on 25 Sep: the Big Picture's list holds them,
    # but Communication, which came back as a row of its own after Blog on 26 Sep
    assert [t for _, t, _, _ in rows(build.nav_html("about.html", ""))] == [
        "About Me", "My Research Areas", "Gallery", "Big Picture of Waves and Data Analytics",
        "Blog", "Communication", "Contact"]


def test_his_sub_lines_sit_under_their_rows():
    subs = {t: s for _, t, s, _ in rows(build.nav_html("about.html", "")) if s}
    assert subs == {"My Research Areas": "Sound Waves, NDT, SHM",
                    "Communication": "Meetings, presentations, reports, papers"}


def test_a_row_is_named_by_all_it_shows():
    markup = build.nav_html("about.html", "")
    for li in re.findall(r"<li[^>]*>(.*?)</li>", markup, re.S):
        assert "aria-label" not in li and "aria-describedby" not in li
        name = " ".join(re.sub(r"<[^>]+>", " ", li).split())
        title = re.search(r'<span class="nav__t">(.*?)</span>', li).group(1).replace("\u00a0", " ")
        sub = re.search(r'<span class="nav__s">(.*?)</span>', li)
        assert name == (f"{title} : {sub.group(1)}" if sub else title)
        if sub:
            assert '<span class="nav__sep">: </span><span class="nav__s">' in li


def test_the_rows_open_the_right_pages():
    hrefs = [h for h, _, _, _ in rows(build.nav_html("about.html", ""))]
    assert hrefs == [
        "about.html", "research.html", "gallery.html", "big-picture.html",
        "blog.html", "communication.html", "contact.html"]
    # from a document page every row climbs out of doc/ first
    assert all(h.startswith("../") for h, _, _, _ in rows(build.nav_html("doc/x.html", "../")))


def test_the_groups_open_at_the_big_picture_and_at_blog():
    markup = build.nav_html("about.html", "")
    assert re.findall(r'<li class="grp"><a href="([^"]+)"', markup) == [
        "big-picture.html", "blog.html"]


def test_without_its_part_the_big_picture_row_is_a_plain_link():
    markup = build.nav_html("big-picture.html", "")
    assert "<ul" not in markup and "nav__more" not in markup and "nav__fold" not in markup
    assert len(rows(markup)) == 7


def test_a_page_marks_its_own_row_and_nothing_else():
    for href, _, _, _ in build.NAV:
        if href not in build.TOPIC_ICONS:
            assert marked(build.nav_html(href, "")) == {href: "page"}


def test_his_topics_mark_the_big_picture_row():
    for href in set(build.TOPIC_ICONS) - build.OWN_ROW:
        up = "../" * href.count("/")
        section = build.doc_section(href[4:-5]) if href.startswith("doc/") else ""
        markup = build.nav_html(href, up, section)
        assert marked(markup) == {f"{up}big-picture.html": "true"}


def test_the_research_documents_mark_my_research_areas():
    for slug in (build.SHORT, build.EXTENDED, build.SOUND):
        markup = build.nav_html(f"doc/{slug}.html", "../", build.doc_section(slug))
        assert marked(markup) == {"../research.html": "true"}
        assert '<a href="../research.html" class="on" aria-current="true"' in markup


def test_from_bridges_to_photons_marks_the_big_picture():
    slug = build.PHOTONS
    markup = build.nav_html(f"doc/{slug}.html", "../", build.doc_section(slug))
    assert marked(markup) == {"../big-picture.html": "true"}


def test_the_cv_marks_about_me():
    assert build.PAGE_SECTION["cv.html"] == "about.html"
    markup = build.nav_html("cv.html", "", build.PAGE_SECTION["cv.html"])
    assert marked(markup) == {"about.html": "true"}


def test_every_document_lives_somewhere_and_its_crumb_names_that_row():
    assert set(build.DOC_HOME) == set(build.DOCS)
    # every document lives under a row the column shows
    rows = {h for h, _, _, _ in build.NAV if h not in build.TOPIC_ICONS}
    assert all(home in rows for home in build.DOC_HOME.values())
    assert build.nav_title(build.DOC_HOME[build.SOUND]) == "My Research Areas"
    for slug in (build.WAVES, build.SIGNAL, build.ML, build.PHOTONS):
        assert build.nav_title(build.DOC_HOME[slug]) == "Big Picture of Waves and Data Analytics"
    assert build.nav_title(f"doc/{build.SIGNAL}.html") == "Signal Processing, System Identification"


def test_his_guides_lead_up_to_the_big_picture():
    # since 25 Sep his guides are the Big Picture's, like From Bridges to Photons
    for slug in (build.WAVES, build.SIGNAL, build.ML, build.PHOTONS):
        assert '<a href="../big-picture.html">' in build.doc_crumb(slug)
    assert '<a href="../research.html">' in build.doc_crumb(build.SHORT)


def test_the_wix_tools_still_find_what_they_read():
    # tools/wix_import.py labels each document; tools/studio_build.py reads his words
    assert set(build.DOC_LABELS) == set(build.DOCS) == set(build.SRC_DOCX)
    assert all(hasattr(build, n) for n in ("CONTACT", "ALT", "HOSTED_DOCX", "PROF_INTRO",
                                           "PROF_BIO", "PROF_MOTIVATION", "PROF_ABOUT",
                                           "PROF_RESEARCH", "PROF_RESEARCH_MORE"))


def test_no_link_to_a_removed_page_in_the_shell():
    for page in ("index.html", "cv.html", f"doc/{build.ML}.html"):
        depth = page.count("/")
        html = build.shell(page, "t", "<p>x</p>", depth=depth)
        for gone in GONE:
            assert f'href="{"../" * depth}{gone}"' not in html
    footer = build.shell("about.html", "t", "<p>x</p>").split('<footer', 1)[1]
    assert '<a href="big-picture.html">Big Picture</a>' in footer


def test_the_column_needs_no_script_of_its_own():
    head = build.shell("about.html", "t", "<p>x</p>").split("<body>", 1)[0]
    assert "nav__more" not in head and "is-open" not in head


def _imgs(markup, cls):
    return re.findall(rf'<img class="{cls}" ([^>]*)>', markup)


def test_his_portrait_heads_the_column_on_every_page():
    for page, depth in (("index.html", 0), ("cv.html", 0), (f"doc/{build.ML}.html", 1),
                        ("post/x.html", 1)):
        html = build.shell(page, "t", "<p>x</p>", depth=depth)
        side = html.split('<nav class="side"', 1)[1].split("</nav>", 1)[0]
        block = side.split("</a>", 1)[0]
        # first in the name block, before his name
        assert block.index('class="id__pic"') < block.index("<b>Korkut Kaynardag</b>")
        (attrs,) = _imgs(block, "id__pic")
        up = "../" * depth
        assert 'alt="Korkut Kaynardag"' in attrs
        assert 'width="108" height="108"' in attrs
        assert f'src="{up}portrait-sq-64.webp"' in attrs
        assert 'sizes="(max-height: 860px) 56px, 108px"' in attrs
        # sharp at one and two device pixels to the CSS pixel, at both sizes
        widths = {int(d) for _, d in re.findall(r"portrait-sq-(\d+)\.webp (\d+)w", attrs)}
        assert {56, 64, 112, 128} <= widths
        assert f"{up}portrait-sq-168.webp 168w" in attrs


def test_the_phone_bar_shows_his_portrait_small_before_his_name():
    html = build.shell("about.html", "t", "<p>x</p>")
    bar = html.split('<header class="bar">', 1)[1].split("</header>", 1)[0]
    link = re.search(r'<a class="bar__id"[^>]*>(.*?)</a>', bar, re.S).group(1)
    (attrs,) = _imgs(link, "bar__pic")
    # his name is the link's words, so the picture beside it is not read twice
    assert 'alt=""' in attrs and 'width="32" height="32"' in attrs and 'sizes="32px"' in attrs
    assert link.endswith("Korkut Kaynardag")


def test_the_portrait_is_a_calm_square_of_his_headshot():
    left, top, right, bottom = build.PORTRAIT_BOX
    assert right - left == bottom - top and top == 0
    assert right <= 708 and bottom <= 691            # inside headshot-708.png
    assert abs((left + right) / 2 - 348) <= 4          # centred on his face
    assert build.PORTRAIT_SQ == tuple(sorted(build.PORTRAIT_SQ))


def test_the_menu_is_a_button_that_says_whether_it_is_open():
    html = build.shell("about.html", "t", "<p>x</p>")
    assert 'type="checkbox"' not in html and 'id="menu"' not in html
    burger = re.search(r'<button class="burger"[^>]*>', html).group(0)
    for want in ('type="button"', 'aria-label="Menu"', 'aria-controls="site-nav"',
                 'aria-expanded="false"'):
        assert want in burger
    assert '<div id="scrim" aria-hidden="true"></div>' in html
    # the script that runs it marks <html>, which is what shows the button
    assert 'h.classList.add("js")' in html.split("<body>", 1)[0]
    assert ".js .burger{display:grid}" in build.CSS
    assert "aria-expanded" in build.JS and "nav-open" in build.JS


# ------------------------------------------------------------------ the home page

def test_the_band_opens_main_on_the_home_page_only():
    home = build.shell("index.html", "t", "<p>x</p>", mast='<div class="m">band</div>')
    assert ('<main id="main">\n<div class="mastrow"><div class="m">band</div></div>\n'
            '<p>x</p>') in home
    assert home.index('<nav class="side"') < home.index('<div class="mastrow">')
    assert "mastrow" not in build.shell("about.html", "t", "<p>x</p>")


def test_the_six_topic_cards_are_his_topic_rows():
    items = build.topic_items()
    assert [i["href"] for i in items] == [h for h, _, _, _ in build.NAV if h in build.TOPIC_ICONS]
    # Probability, Statistics is his deck now (parts/deck.py): two in preparation
    assert [i["soon"] for i in items] == [False, False, False, False, True, True]
    assert [i["icon"] for i in items] == [
        "vibrations-waves", "signal-processing", "machine-learning",
        "probability-statistics", "python-programming", "communication"]
    assert items[3]["sub"] == "Stochastic Process, Estimation" and items[4]["sub"] == ""
    assert all(set(i) == {"href", "title", "sub", "icon", "soon"} for i in items)


def test_a_page_in_preparation_links_pages_that_exist():
    for href in build.SOON:
        for r in build.soon_related(href):
            path = r["href"].split("#")[0]
            assert path in {h for h, _, _, _ in build.NAV} or path[4:-5] in build.DOCS
            assert r["title"]


# ------------------------------------------------------------------ wiring the parts

class _Part:
    __name__ = "parts.demo"

    @staticmethod
    def render(title, sub="", related=()):
        return f"<p>{title}|{sub}|{len(related)}</p>"


def test_ready_calls_a_part_through_its_interface_or_not_at_all(capsys):
    assert build.ready(None, "render", "t") is None
    assert build.ready(_Part, "missing") is None
    assert build.ready(_Part, "render", "T", "s", [1, 2]) == "<p>T|s|2</p>"
    assert build.ready(_Part, "render", "T", items=[]) is None
    assert "does not take its interface yet" in capsys.readouterr().out


def test_wrap_page_adds_only_what_a_part_left_out():
    assert build.wrap_page("T", "<p>x</p>") == '<div class="wrap">\n<h1>T</h1>\n<p>x</p>\n</div>'
    own = '<div class="wrap soon"><h1>Mine</h1><p>x</p></div>'
    assert build.wrap_page("T", own) == own
    assert build.wrap_page("T", '<section><h1>Mine</h1></section>').startswith(
        '<div class="wrap">\n<section><h1>Mine</h1>')
    assert build.wrap_page("T", '<div class="wrap"><p>x</p></div>') == (
        '<div class="wrap">\n <h1>T</h1>\n<p>x</p></div>')


def test_a_part_that_fails_to_load_is_reported_not_skipped(tmp_path, monkeypatch):
    pkg = tmp_path / "parts"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "broken.py").write_text("CSS = '\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(build, "PART_ERRORS", [])
    for name in [m for m in sys.modules if m == "parts" or m.startswith("parts.")]:
        monkeypatch.delitem(sys.modules, name)
    assert build.part("broken") is None
    assert build.part("never-written") is None
    assert [n for n, _ in build.PART_ERRORS] == ["broken"]


# ------------------------------------------------------------------ his words

POWER = "<math><mn>7</mn> <mo>&times;</mo> <msup><mn>10</mn><mn>27</mn></msup></math>"


def test_his_band_and_blocks_stand_in_his_deck():
    checked, missing = build.deck_report()
    # 17 since his markup of 27 Sep 2026 struck two paragraphs and his
    # extended heading, which his deck has not, is an approved edit
    assert missing == [] and checked >= 17
    assert build.DECK_SLIDE["PROF_HEADER"] == 1
    # his power of ten is MathML, so a screen reader reads a power (A11Y-4)
    assert POWER in build.PROF_HEADER and "<sup>" not in build.PROF_HEADER


def test_a_power_is_read_as_the_superscript_his_deck_types(monkeypatch):
    # the MathML power and a <sup> both read back as his "10²⁷"
    monkeypatch.setattr(build, "PROF_HEADER", build.PROF_HEADER.replace(
        POWER, '<span class="nw">7 &times; 10<sup>27</sup></span>'))
    assert build.deck_report()[1] == []
    monkeypatch.setattr(build, "PROF_HEADER", build.PROF_HEADER.replace("<sup>27</sup>", "27"))
    assert [n for n, _ in build.deck_report()[1]] == ["PROF_HEADER"]


def test_a_power_written_flat_is_not_his(monkeypatch):
    monkeypatch.setattr(build, "PROF_HEADER", build.PROF_HEADER.replace(
        "<msup><mn>10</mn><mn>27</mn></msup>", "<mn>1027</mn>"))
    assert [n for n, _ in build.deck_report()[1]] == ["PROF_HEADER"]


def test_a_passage_must_be_his_whole_paragraph(monkeypatch):
    # "Myself" is inside his slide's text, but his paragraph ends in a
    # colon: a passage short of it is not his words
    assert "<strong>Myself:</strong>" in build.PROF_BIO
    monkeypatch.setattr(build, "PROF_BIO", build.PROF_BIO.replace("Myself:", "Myself", 1))
    assert build.deck_report()[1] == [("PROF_BIO", "Myself")]


# One change of punctuation, anywhere in each of his blocks: its first, middle
# and last mark dropped, and each swapped for a look-alike. Every change must
# fail the gate, which reads each passage against his whole paragraph.
PUNCT = re.compile(r"[,.:;!?()']|&ldquo;|&rdquo;|&rsquo;")
SWAP = {",": ";", ".": ",", ":": ";", ";": ",", "!": ".", "?": ".", "(": "[", ")": "]",
        "'": "&rsquo;", "&ldquo;": '"', "&rdquo;": '"', "&rsquo;": "'"}


def _his_marks(block):
    """The punctuation his block shows a reader: outside its tags and the
    character references that spell a letter (&#287;, &times;), whose ";" is
    markup, not his."""
    text = re.sub(r"<[^>]+>|&(?!ldquo;|rdquo;|rsquo;)#?\w+;",
                  lambda m: "\0" * len(m.group(0)), block)
    return list(PUNCT.finditer(text))


@pytest.mark.parametrize("name", sorted(build.DECK_SLIDE))
def test_a_changed_mark_anywhere_in_his_blocks_fails_the_gate(monkeypatch, name):
    block = getattr(build, name)
    marks = _his_marks(block)
    assert marks, name
    for m in (marks[0], marks[len(marks) // 2], marks[-1]):
        for new in ("", SWAP[m.group(0)]):
            monkeypatch.setattr(build, name, block[:m.start()] + new + block[m.end():])
            assert [n for n, _ in build.deck_report()[1]] == [name], (name, m.group(0), new)
    monkeypatch.setattr(build, name, block)
    assert build.deck_report()[1] == []


def test_a_changed_capital_fails_the_gate(monkeypatch):
    monkeypatch.setattr(build, "PROF_BIO", build.PROF_BIO.replace("Assistant Professor",
                                                                  "assistant Professor", 1))
    assert [n for n, _ in build.deck_report()[1]] == ["PROF_BIO"]


# His editorial markup of 27 Sep 2026, as tools/ROUND11_EDITS.md reads it: the
# final texts of the three blocks it changed, as a reader gets them.
MARKED = {
    "PROF_RESEARCH": [
        "My research focuses on Structural Health Monitoring (SHM) and Non-Destructive Testing "
        "(NDT): the science of monitoring and testing structures to detect and characterize "
        "defects before they become failures. Because these fields rely heavily on vibration "
        "analysis, acoustic wave propagation, data analytics, and machine learning, my path also "
        "took me to industry, where I worked as an applied data scientist and a Senior AI "
        "Engineer on sound source tracking. The three documents on the right introduce my "
        "research topics, and I've also included a presentation that walks through my master's "
        "and PhD work in more depth."],
    "PROF_RESEARCH_MORE": [
        "The educational sections (topics in the big picture menu)",
        "You'll also find documents about the topics that I used extensively in the Big Picture "
        "menu on the left. I wrote them for newcomers who want the big picture: how these topics "
        "connect, and how to approach learning them, without diving into the equations and "
        "formalism of a textbook or lecture. They reflect my own path into this field, but "
        "everyone's path is different, so I'd encourage you to read a few other guides "
        "alongside these rather than relying on just one."],
    "PROF_MOTIVATION": [
        "Motivation for Creating the Educational Sections",
        "As a civil engineer, I only encountered topics like vibrations, waves, signals, system "
        "identification, probability, statistics, estimation, stochastic process, machine "
        "learning, Python and programming after completing my undergraduate studies. This made "
        "learning them particularly challenging. It took me a long time, with repeated study, "
        "to truly grasp:",
        "What methods are in each topic, what they actually do (the intuition and logic), and "
        "thus what the big picture of each topic is",
        "What kinds of problems they solve and where these methods are applied",
        "How similar concepts reappear across different fields",
        "How deeply interconnected they actually are",
        "That final realization was my “Aha!” moment.",
        "My goal in creating these educational sections is to shorten your learning journey. "
        "These sections are designed not to teach your mathematics of each method/algorithm, "
        "but rather than make you figure out the answers of the 4 questions above. "
        "Accordingly, I aim to help you understand these topics more quickly and clearly, so "
        "you can spend less time struggling with the basics and more time applying them "
        "meaningfully in your work."],
}


def _passages(block):
    return [p for p in (build._words(x) for x in
                        re.split(r"</?(?:p|li|ul|ol|h2|div)\b[^>]*>", block)) if p]


@pytest.mark.parametrize("name", sorted(MARKED))
def test_his_markup_of_27_sep_stands_word_for_word(name):
    assert _passages(getattr(build, name)) == MARKED[name]


def test_what_he_typed_into_the_motivation_is_bold_as_he_asked():
    runs = re.findall(r"<strong>(.*?)</strong>", build.PROF_MOTIVATION, re.S)
    assert [build._words(r) for r in runs] == [
        "These sections are designed not to teach your mathematics of each method/algorithm, "
        "but rather than make you figure out the answers of the 4 questions above. Accordingly,"]


def test_each_approved_edit_is_his_text_against_his_deck_with_its_reason():
    assert build.WHY_MARKUP == "professor's editorial markup, 27 Sep 2026 (reference/prof-edits/)"
    for name, edits in build.APPROVED_EDITS.items():
        assert name in build.DECK_SLIDE
        for ours, his, why in edits:
            assert ours != his and why in (build.WHY_MARKUP, build.WHY_MOVED)
            assert " ".join(ours.split()) in " ".join(getattr(build, name).split())


@pytest.mark.parametrize("name", sorted(MARKED))
def test_every_mark_in_his_marked_blocks_is_held(monkeypatch, name):
    # inside the words his markup brought as much as outside them: each mark
    # dropped and swapped fails the gate, for this block alone (a change inside
    # his two new points reports both, since the pair stands for two of the deck's)
    block = getattr(build, name)
    for m in _his_marks(block):
        for new in ("", SWAP[m.group(0)]):
            monkeypatch.setattr(build, name, block[:m.start()] + new + block[m.end():])
            assert {n for n, _ in build.deck_report()[1]} == {name}, (name, m.group(0), new)


def test_a_block_gone_back_to_his_deck_fails_the_gate(monkeypatch):
    # his deck's words, where his markup has changed them since, are not his text now
    for name, now, then in (("PROF_MOTIVATION", "in your work.", "in your work"),
                            ("PROF_RESEARCH", "took me to industry", "took me through industry"),
                            ("PROF_RESEARCH_MORE", " (topics in the big picture menu)", "")):
        block = getattr(build, name)
        monkeypatch.setattr(build, name, block.replace(now, then, 1))
        assert [n for n, _ in build.deck_report()[1]] == [name], name
        monkeypatch.setattr(build, name, block)
    assert build.deck_report()[1] == []


def test_what_he_struck_may_not_come_back(monkeypatch):
    struck = ("<p>Also, are you also asking about &ldquo;vibrations and waves&ldquo;, \"signal "
              "processing, system identification, estimation, optimization&ldquo;, and "
              "&ldquo;machine learning&rdquo; and similar sections on left menu?</p>")
    monkeypatch.setattr(build, "PROF_RESEARCH_MORE", build.PROF_RESEARCH_MORE + struck)
    report = build.deck_report()[1]
    assert {n for n, _ in report} == {"PROF_RESEARCH_MORE"}
    assert ("PROF_RESEARCH_MORE", build._words(struck)) in report
    # and the record names his paragraphs exactly: words that open none are reported
    monkeypatch.setattr(build, "PROF_RESEARCH_MORE", build.PROF_RESEARCH_MORE.replace(struck, ""))
    monkeypatch.setattr(build, "STRUCK", {3: ("Also, are you asking",)})
    assert build.deck_report()[1] == [("STRUCK", "Also, are you asking")]


def test_the_research_page_sets_his_section_once_after_the_documents():
    page = build.page_research('<section class="rboxes">cards</section>')
    assert page.count(build.PROF_RESEARCH_MORE) == 1
    assert page.count("The educational sections") == 1
    assert page.index("cards") < page.index('<div class="col rboxes-page__more">')
    assert "Also, are you also asking" not in page and "In this webpage" not in page


def test_his_motivation_is_staged_with_his_block_verbatim():
    from parts import motivation
    out = motivation.render(build.PROF_MOTIVATION)
    assert out.startswith('<section class="motiv">') and build.PROF_MOTIVATION in out


def test_his_bold_runs_are_in_the_about_text():
    runs = re.findall(r"<strong>(.*?)</strong>", build.PROF_ABOUT, re.S)
    assert [" ".join(build._words(r).split()) for r in runs] == [
        "master's degrees", "Boğaziçi University in 2013 and 2016", "Ph.D.",
        "The University of Texas at Austin in 2023",
        "Applied Data Scientist at Transtek International Group",
        "Senior AI Engineer at Renesas Electronics America", "Assistant Professor",
        "Izmir Institute of Technology"]


def test_the_column_is_held_to_his_slide(monkeypatch):
    assert build.nav_report() == (17, [])
    nav = [r if r[0] != "research.html" else ("research.html", "My Research Areas",
                                              "Sound Waves, NDE, SHM", "") for r in build.NAV]
    monkeypatch.setattr(build, "NAV", nav)
    assert build.nav_report() == (17, ["Sound Waves, NDE, SHM"])


def test_a_dash_is_billed_to_the_innermost_part_that_wrote_it(tmp_path, monkeypatch):
    art = '<figure class="art"><style>.a{b:c}</style><p>trace &mdash; ripple</p></figure>'
    hero = f'<section class="hero"><p>his words</p>{art}<p>ours &mdash; here</p></section>'
    page = f'<main>{hero}<p>shell &mdash; text</p></main>'
    (tmp_path / "index.html").write_text(page, encoding="utf-8")
    monkeypatch.setattr(build, "OWNED", [("parts/heroart.py", art), ("parts/hero.py", hero)])
    monkeypatch.setattr(build, "VERBATIM", [])
    owners = sorted((o, c) for o, _, c, k in build.emdash_report(str(tmp_path)) if k == "em dash")
    assert [o for o, _ in owners] == ["build.py", "parts/hero.py", "parts/heroart.py"]
    assert "shell" in owners[0][1] and "ours" in owners[1][1] and "trace" in owners[2][1]


# ------------------------------------------------------------------ links into a document

def _site(tmp_path, pages):
    for rel, text in pages.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return str(tmp_path)


def test_only_a_documents_own_page_links_a_place_inside_it(tmp_path):
    site = _site(tmp_path, {
        "index.html": '<a href="doc/a.html">whole</a><a href="big-picture.html#waves">map</a>',
        "big-picture.html": '<a href="doc/a.html#estimation">section</a><a id="waves"></a>',
        "doc/a.html": '<a href="#estimation">own</a><a href="a.html#estimation">own too</a>'
                      '<a href="b.html#x">another</a><a href="../doc/b.html">whole</a>',
        "doc/b.html": '<a href="https://example.org/doc/c.html#x">elsewhere</a><a id="x"></a>',
        "parts.js": "var go='doc/b.html#x',ok='doc/b.html',map='big-picture.html#waves';",
    })
    assert sorted(build.anchor_report(site)) == [
        ("big-picture.html", "doc/a.html#estimation"), ("doc/a.html", "b.html#x"),
        ("parts.js", "doc/b.html#x")]


def test_the_big_pictures_fallback_opens_documents_whole():
    assert all("#" not in href for _, href in build.BIG_TOPICS)
    assert "#" not in build.page_big_picture()


def test_the_strict_build_fails_on_a_link_into_a_document():
    src = open(os.path.join(ROOT, "site", "build.py"), encoding="utf-8").read()
    gate = src.split("inside = anchor_report(OUT)", 1)[1].split("return 1 if fail else 0", 1)[0]
    assert "if inside and args.strict:" in gate and "fail = True" in gate


# ------------------------------------------------------------------ the head of every page

def test_every_page_has_its_own_line_for_search_results():
    lines = {}
    for page in ("index.html", "about.html", "cv.html", "research.html", "gallery.html",
                 "big-picture.html", "blog.html", "contact.html"):
        html = build.shell(page, "t", "<p>x</p>", desc=build.PAGE_DESC[page])
        lines[page] = re.search(r'<meta name="description" content="([^"]*)">', html).group(1)
    assert len(set(lines.values())) == len(lines)
    assert lines["index.html"] == build.DESCRIPTION
    for href in build.SOON:
        assert build.soon_desc(href).startswith(build.nav_title(href))
    assert build.soon_desc("probability-statistics.html") == (
        "Probability, Statistics: Stochastic Process, Estimation. In preparation.")
    assert set(build.DOC_DESC) == set(build.DOCS)
    every = list(build.PAGE_DESC.values()) + list(build.DOC_DESC.values())
    assert all(len(d) <= 180 and not build.DASH.search(d) for d in every)
    # a line is escaped into its attribute
    html = build.shell("about.html", "t", "<p>x</p>", desc='His "words" & more')
    assert 'content="His &quot;words&quot; &amp; more"' in html


def test_the_fonts_come_from_the_site_itself():
    html = build.shell(f"doc/{build.ML}.html", "t", "<p>x</p>", depth=1)
    assert "googleapis" not in html and "gstatic" not in html
    for name in build.FONT_PRELOAD:
        assert (f'<link rel="preload" href="../fonts/{name}.woff2" as="font" '
                f'type="font/woff2" crossorigin>') in html
    files = set(os.listdir(build.FONT_DIR))
    from parts import theme
    faces = re.findall(r"url\(fonts/([\w-]+\.woff2)\)", theme.CSS)
    assert faces and set(faces) <= files
    assert {f"{n}.woff2" for n in build.FONT_PRELOAD} <= set(faces)
    # they ship under their license, and nothing in it is an address
    licenses = [f for f in files if f.startswith("OFL")]
    assert len(licenses) == 2
    for f in licenses:
        text = open(os.path.join(build.FONT_DIR, f), encoding="utf-8").read()
        assert "SIL Open Font License" in text and not build.EMAIL.search(text)


# ------------------------------------------------------------------ what stays private

def test_nothing_private_is_published(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "CV_DOCX", str(tmp_path / "cv.docx"))
    (tmp_path / "cv.docx").write_bytes(b"PK not really a CV")
    site = tmp_path / "site"
    (site / "doc").mkdir(parents=True)
    (site / "index.html").write_text(
        '<a href="mailto:korkutkaynardag@iyte.edu.tr">korkutkaynardag@iyte.edu.tr</a>',
        encoding="utf-8")
    assert build.private_report(str(site)) == []
    # his own Gmail is public for contact (29 Sep 2026); any other is not
    (site / "mine.html").write_text("write to korkut.kaynardag@gmail.com", encoding="utf-8")
    assert build.private_report(str(site)) == []
    (site / "a.html").write_text("write to someone.else@gmail.com", encoding="utf-8")
    (site / "b.js").write_text('var t="+1 (512) 300-4065";', encoding="utf-8")
    (site / "c.css").write_text("/* someone@example.org */", encoding="utf-8")
    with zipfile.ZipFile(site / "doc" / "d.docx", "w") as z:
        z.writestr("word/document.xml", "<w:t>another.one@gmail.com</w:t>")
    (site / "doc" / "Korkut_Kaynardag_Resume.webp").write_bytes(b"x")
    (site / "copy.bin").write_bytes(b"PK not really a CV")
    found = build.private_report(str(site))
    assert ("a.html", "gmail") in found and ("a.html", "someone.else@gmail.com") in found
    assert not [f for f in found if f[0] == "mine.html"]
    assert ("b.js", "300-4065") in found
    assert ("c.css", "someone@example.org") in found
    assert ("doc/d.docx", "gmail") in found
    assert ("doc/Korkut_Kaynardag_Resume.webp", "his Word CV") in found
    assert ("copy.bin", "his Word CV") in found
    (site / "doc" / "e.docx").write_bytes(b"not a zip")
    assert ("doc/e.docx", "a Word file that cannot be opened to check") in (
        build.private_report(str(site)))


def test_a_cv_file_that_is_not_clean_stops_the_build(tmp_path):
    path = tmp_path / "cv.json"
    for bad in ('{"email": "someone.else@gmail.com"}', '{"phone": "+1 (512) 300 4065"}',
                '{"links": [{"href": "mailto:a@b.co"}]}'):
        path.write_text(bad, encoding="utf-8")
        with pytest.raises(SystemExit):
            build.load_cv(str(path))
    assert build.load_cv(str(tmp_path / "none.json")) is None


def test_the_cv_keeps_his_profiles_and_his_institutional_address(tmp_path):
    path = tmp_path / "cv.json"
    path.write_text(json.dumps({
        "name": "Korkut Kaynardag, Ph.D.", "location": "Izmir, Turkiye",
        "links": [{"label": "Personal webpage", "href": "https://www.wavesanddata.com",
                   "kind": "web"},
                  {"label": "Google Scholar", "href": "https://scholar.google.com/x",
                   "kind": "scholar"},
                  {"label": "GitHub", "href": "", "kind": "github"}],
        "areas": ["Structural Health Monitoring"], "sections": []}), encoding="utf-8")
    cv = build.load_cv(str(path))
    assert cv["email"] == "korkutkaynardag@iyte.edu.tr"
    assert [ln["kind"] for ln in cv["links"]] == ["scholar"]
    info = build.contact_info(cv)
    assert info["links"] == cv["links"] and info["cv_href"] == "cv.html"
    assert (info["city"], info["country"]) == ("Izmir", "Turkiye")


def test_about_and_contact_show_his_three_profiles_only():
    # ROUND4_SPEC.md section 12: GitHub and YouTube are on cv.html alone
    cv = {"links": [{"label": k, "href": f"https://{k}.example/k", "kind": k}
                    for k in build.LINK_KINDS]}
    assert [ln["kind"] for ln in build.profiles(cv)] == ["scholar", "linkedin", "researchgate"]
    assert build.contact_info(cv)["links"] == build.profiles(cv)
    assert build.profiles(None) == []


# ------------------------------------------------------------------ gallery

def test_phone_rows_pair_photos_unless_the_pair_would_be_too_wide():
    assert gallery_part.rows([0.75, 1.33, 1.33]) == [[0, 1], [2]]
    assert gallery_part.rows([2.07, 2.06, 1.5]) == [[0], [1], [2]]
    assert gallery_part.rows([0.56, 0.73]) == [[0, 1]]
    assert gallery_part.rows([1.3]) == [[0]]


def _item(kind, w, h, n):
    it = {"kind": kind, "full": f"gallery/{n:02d}.webp", "fw": w, "fh": h,
          "thumb": f"gallery/{n:02d}-thumb.webp", "tw": w // 4, "th": h // 4}
    if kind == "video":
        it.update(stream="https://video.wixstatic.com/video/x/720p/mp4/file.mp4", duration=29.55)
    return it


def test_gallery_markup_keeps_his_caption_and_names_every_link():
    sets = [{"lines": ["Field tests of our damage detection prototype",
                       "at TX in collaboration with BNSF Railroad Company", "(during my Ph.D.)"],
             "items": [_item("video", 1080, 1920, 1), _item("photo", 489, 673, 2)]},
            {"lines": ["Instrumentation of an industrial chimney", "(during my M.Sc.)"],
             "items": [_item("photo", 1339, 1054, 3)]}]
    out = gallery_part.render(sets)
    assert out.count('<h2 class="gset__h"') == 2
    assert ('<span class="gset__t">Field tests of our damage detection prototype at TX in '
            'collaboration with BNSF Railroad Company</span> '
            '<span class="gset__era">(during my Ph.D.)</span>') in out
    video = re.search(r'<li class="gph gph--video".*?</li>', out, re.S).group(0)
    assert 'href="https://video.wixstatic.com/video/x/720p/mp4/file.mp4"' in video
    assert 'data-stream="https://video.wixstatic.com' in video
    assert 'aria-label="Play the video, 0:30"' in video
    assert "<video" not in out                      # the film loads on play only
    assert 'aria-label="Photo, full size"' in out   # alone in its set
    assert 'style="--r:1.2891;--n:2"' in out     # 1080/1920 + 489/673
    assert out.count('loading="eager"') == 2


def test_the_repeated_set_is_shown_once_as_it_first_appeared(tmp_path, monkeypatch):
    items = [{"order": k, "type": "photo", "file": f"photos/{k}.jpg"} for k in (1, 2, 3)]
    manifest = {"sets": [{"order": 1, "lines": ["A", "at TTC"], "items": [1, 2]},
                         {"order": 2, "lines": ["A", "at TTCI"], "items": [1, 2], "repeat_of": 1},
                         {"order": 3, "lines": ["B"], "items": [3]}],
                "items": items}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(build, "GALLERY", str(tmp_path))
    sets = build.gallery_sets()
    assert [s["lines"] for s in sets] == [["A", "at TTC"], ["B"]]
    assert [i["order"] for s in sets for i in s["items"]] == [1, 2, 3]


@pytest.mark.skipif(not os.path.isfile(os.path.join(ROOT, "content", "gallery", "manifest.json")),
                    reason="content/gallery is pulled by tools/wix_pull.py")
def test_his_gallery_twelve_sets_twenty_six_photos_one_film():
    sets = build.gallery_sets()
    kinds = [i["type"] for s in sets for i in s["items"]]
    assert len(sets) == 12
    assert kinds.count("photo") == 26 and kinds.count("video") == 1
    assert sets[1]["lines"][1] == "and rail vibration measurements at TTC"


# ------------------------------------------------------------------ the blog's nodes

def _render(node, figs):
    preview.plan([node], figs)
    try:
        return preview.render(node, "p")
    finally:
        preview.plan([])


VIDEO = {"type": "VIDEO", "id": "v1", "videoData": {"video": {
    "src": {"url": "https://www.youtube.com/watch?v=yRxYIfZUxW8"}, "duration": 82}}}


def test_a_youtube_film_is_a_poster_until_pressed():
    out = _render(VIDEO, {"v1": {"url": "https://www.youtube.com/watch?v=yRxYIfZUxW8",
                                 "embed": "https://www.youtube-nocookie.com/embed/yRxYIfZUxW8",
                                 "title": "Basic principles of laser Doppler vibrometry",
                                 "author": "Polytec", "poster": "p/video.webp",
                                 "pw": 1280, "ph": 720}})
    assert out.startswith('<figure class="postvid"><a class="postvid__a" '
                          'href="https://www.youtube.com/watch?v=yRxYIfZUxW8"')
    assert 'data-embed="https://www.youtube-nocookie.com/embed/yRxYIfZUxW8"' in out
    assert '<img src="p/video.webp" alt="" width="1280" height="720"' in out
    assert "<iframe" not in out
    assert ("<figcaption>Basic principles of laser Doppler vibrometry, Polytec (YouTube)"
            "</figcaption>") in out


def test_a_film_build_said_nothing_about_is_a_plain_link():
    out = _render(VIDEO, {})
    assert out.startswith('<p><a href="https://www.youtube.com/watch?v=yRxYIfZUxW8"')


FILE = {"type": "FILE", "id": "f1", "fileData": {"name": "WT Literature - Final Summary.docx",
                                                 "type": "docx", "size": 115711}}


def test_his_file_downloads_under_his_own_name():
    out = _render(FILE, {"f1": {"href": "wind.docx", "bytes": 115711}})
    assert 'href="wind.docx" download="WT Literature - Final Summary.docx"' in out
    assert '<span class="docdl__t">WT Literature - Final Summary.docx</span>' in out
    assert "0.12&nbsp;MB" in out


def test_his_file_waits_when_the_build_publishes_none():
    out = _render(FILE, {"f1": {"pending": True}})
    assert "docdl--wait" in out and "Word file, coming soon" in out
    assert "href=" not in out


def test_a_paragraph_followed_straight_by_another_closes_up():
    def p(i, text):
        return {"type": "PARAGRAPH", "id": i,
                "nodes": [{"type": "TEXT", "textData": {"text": text}}] if text else []}
    nodes = [p("a", "Fatigue "), p("b", "SHM "), p("c", ""), p("d", "You can download"),
             {"type": "FILE", "id": "e"}]
    assert build.tight(nodes) == {"a"}


def test_the_index_takes_his_opening_sentence_whole():
    post = {"body": {"nodes": [
        {"type": "PARAGRAPH", "nodes": []},
        {"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {
            "text": "\tThe video below shows very clearly how LDV works. Then, I explain (i)"}}]}]}}
    assert build.lead(post) == "The video below shows very clearly how LDV works."


def test_dates_read_as_he_writes_them():
    assert build.shown_date("2022-04-20T17:21:20.261Z") == "April 20, 2022"
    assert build.shown_date("2022-02-03") == "February 3, 2022"


def test_page_images_are_named_for_what_they_are():
    assert build.picture_alt("stationary-wavelet-package-transformation", 2, 4) == \
        "Page 2 of 4 of the post, shown as an image"
    assert build.picture_alt("literature-review-for-finite-element-model-updating", 1, 3) == \
        "Part 1 of 3 of the screenshot of the library, shown as an image"


def test_a_hyphenated_word_in_his_title_stays_whole():
    assert blog_part.title("Detection with Semi-organizing Map") == \
        'Detection with <span class="nw">Semi-organizing</span> Map'


# ------------------------------------------------------------------ what goes to Wix

def test_only_wix_types_publish_and_word_files_only_locally():
    files = ["a/index.html", "a/x.webp", "a/f.woff2", "a/doc/b.docx", "a/v.mp4", "a/p.pdf"]
    local, bad = build.file_types(files)
    assert local == ["a/doc/b.docx"] and bad == ["a/v.mp4"]
    local, bad = build.file_types(files, no_word=True)
    assert local == [] and bad == ["a/doc/b.docx", "a/v.mp4"]


def _jpeg_with_gps(path):
    from PIL import Image
    im = Image.new("RGB", (40, 20), (200, 30, 30))
    exif = Image.Exif()
    exif[274] = 6                                   # rotate 90 degrees to stand upright
    exif.get_ifd(0x8825)[2] = (41.0, 2.0, 3.0)      # a GPS latitude
    im.save(path, "JPEG", exif=exif.tobytes())


def test_a_published_photo_stands_upright_and_carries_no_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(build, "CACHE", str(tmp_path / "cache"))
    src, dst = tmp_path / "in.jpg", tmp_path / "out" / "p.webp"
    _jpeg_with_gps(src)
    assert build.carries_metadata(str(src))
    assert build.derive(str(src), str(dst), edge=2048) == (20, 40)
    assert not build.carries_metadata(str(dst))
    # the second time comes from the cache, the same bytes
    again = tmp_path / "out" / "q.webp"
    assert build.derive(str(src), str(again), edge=2048) == (20, 40)
    assert dst.read_bytes() == again.read_bytes()


def test_the_metadata_check_walks_chunks_not_bytes(tmp_path):
    from PIL import Image
    path = tmp_path / "plain.webp"
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, "WEBP", lossless=True)
    path.write_bytes(buf.getvalue() + b"")       # no EXIF chunk
    assert not build.carries_metadata(str(path))


# ------------------------------------------------------------------ his layout requests

def test_a_figure_moves_below_the_text_it_belongs_to(monkeypatch):
    monkeypatch.setattr(build, "FIGURE_AFTER", {"d": [("Figure 2. X", "Last words")]})
    body = ('<p>First.</p><figure><img src="a"><figcaption>Figure 2. X shows</figcaption></figure>'
            '<p>Middle.</p><p>Last words of the section.</p><h2>Next</h2>')
    out = build.place_figures(body, "d")
    assert out.index("Last words") < out.index("<figure>") < out.index("<h2>")
    assert out.count("<figure>") == 1 and "Middle." in out
    with pytest.raises(SystemExit):
        build.place_figures(body.replace("Last words", "Other"), "d")


def test_his_words_gain_a_link_without_changing(monkeypatch):
    real = dict(build.DOC_LINKS)
    monkeypatch.setattr(build, "DOC_LINKS", {"d": [("see my blog for more", "my blog", "../post/p.html")]})
    out = build.link_words("<p>Please see my blog for more.</p>", "d")
    assert out == '<p>Please see <a class="inlink" href="../post/p.html">my blog</a> for more.</p>'
    with pytest.raises(SystemExit):
        build.link_words("<p>nothing here</p>", "d")
    # the real ones point at pages that exist
    for slug, links in real.items():
        for _, _, href in links:
            assert os.path.isfile(os.path.join(build.ROOT, "content", "blog", href.split("/")[-1][:-5], "post.json"))
