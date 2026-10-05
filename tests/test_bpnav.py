"""The Big Picture row and its list (parts/bpnav.py), as of 25 Sep 2026.

That day the professor took his six topic rows out of the column: clicking
Big Picture opens its list, so they need not stand in the column as well.
These hold what he decided and what follows from it: six rows in the column
and the topics in the list, one per category of the Big Picture page under
its short name, each opening the page its old row opened; on a topic's page,
and on From Bridges to Photons, the Big Picture row is the section, the list
is open with the page and the topic is marked. And the chevron he asked to
point down, which calls for a look until the reader has seen the list open.

On 27 Sep 2026 he asked for motion in the column: fills under the pointer,
above all on the Big Picture list's categories, and something for his photo
and the lines under it that stays professional. The last section holds what
that motion may and may not do (DESIGN_BRIEF.md 4: no translateY and no
shadow on hover, fills and rails only; reduced motion keeps the end state).

Later that day (round 11) the list took the Big Picture page's new order,
his five topics on one line, and the row gained the line under its title:
the page's line in small, a bead a topic, which turns down into the list
when it opens, so the topics show once. The call for a look keeps its 6s
beat (the client liked it) and rests off screen.

On 29 Sep 2026 the client asked for the line's dots, its strokes and the
chevron to come alive as the page opens, as thinking orbs do, and the list
and its topics too. The orbs' section holds what that motion says (a warm
thought runs the line in the page's order and each topic wakes into an orb
as it arrives; the list wakes top to bottom as it opens; a topic under the
pointer is reached down the branch; "you are here" keeps a quiet orb) and
what it may not do: run under reduced motion or forced colours, draw a
colour of its own, ask for frames at rest, or reach past the row.

Later that day (round 15) the client asked for it faster, for the list's
topics to answer the pointer without the fill he found very bad, and a
finger on a phone as well, and for the orbs on his photo. So the row reads
in about a second on the site's own springs, the thought is white (warm is
"you are here" and the chevron's alone), nothing turns at rest, not even
"you are here"; a topic lights by its words and a hairline, from the press
on a phone; and the portrait's halo gathers round the photo once a visit
and breathes again under the pointer, never over his face.
"""

import html
import json
import math
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import bpnav, documents, theme  # noqa: E402

BP = "big-picture.html"
# his topics' pages, in the order of the column's old rows (build.NAV); the
# list sets them in the Big Picture page's order, ORDER
TOPICS = [f"doc/{build.WAVES}.html", f"doc/{build.SIGNAL}.html", f"doc/{build.ML}.html",
          "probability-statistics.html", "python-programming.html"]
WAVES_PAGE = TOPICS[0]


def order():
    """The list's pages in the Big Picture page's order (documents.CATEGORIES)."""
    page = {c["id"]: p for c in documents.CATEGORIES for p in TOPICS
            if p in ([c["soon"]] if c.get("soon") else []) + [f"doc/{d}.html" for d in c["docs"]]
            + list(c.get("decks") or ())}
    return [page[c["id"]] for c in documents.CATEGORIES if c["id"] in page]
# Communication keeps a row of its own after Blog (26 Sep 2026), and his
# advice section in preparation follows it (5 Oct 2026)
ROWS = ["about.html", "research.html", "gallery.html", BP, "blog.html", "communication.html",
        "personal-advices.html", "contact.html"]


@pytest.fixture
def column(monkeypatch):
    """nav_html() as the build runs it, with the part loaded (main() sets it)."""
    monkeypatch.setattr(build, "BPNAV", bpnav)
    return build.nav_html


def rows(markup):
    """The column's own rows, the list set aside: [(href, the <a> tag's attributes)]."""
    markup = re.sub(r'<div class="nav__fold".*?</div>', "", markup, flags=re.S)
    return re.findall(r'<a href="([^"]+)"([^>]*)>', markup)


def topics(markup):
    """The list's items: [(href, label, aria-current or None)]. Each label is
    its words' span (.nav__w), which the words' light is laid over."""
    sub = re.search(r'<ul class="nav__sub"[^>]*>(.*?)</ul>', markup, re.S).group(1)
    return [(h, html.unescape(label).replace("\u00a0", " "), cur or None) for h, cur, label in
            re.findall(r'<li(?: class="nav__two")?><a href="([^"]+)"(?: aria-current="([^"]+)")?>'
                       r'<span class="nav__w"[^>]*>([^<]*)</span>'
                       r'(?:<span class="nav__sep"> </span><span class="nav__n">[^<]*</span>)?</a></li>',
                       sub)]


def marked(markup):
    return [(h, a) for h, a in rows(markup) if "aria-current" in a]


def bp_row(markup):
    """The Big Picture <li>, from its class list on."""
    return markup.split('<li class="grp nav__bp', 1)[1]


# ------------------------------------------------------------------ the column and its list

def test_the_column_has_its_rows_and_no_topic_but_communication(column):
    for page, up in (("about.html", ""), (TOPICS[2], "../"), (BP, "")):
        hrefs = [h for h, _ in rows(column(page, up))]
        assert hrefs == [up + h for h in ROWS]


def test_the_list_holds_each_category_under_its_short_name(column):
    items = topics(column("about.html", ""))
    assert [label for _, label, _ in items] == [
        c.get("short") or c["label"] for c in documents.CATEGORIES]
    assert "Signal Processing & System ID" in [label for _, label, _ in items]


def test_the_signal_processing_topic_carries_his_note_in_smaller_type(column):
    """His notes, 5 Oct 2026: "(with connections to estimation, optimization,
    ML, inverse probs, BSS)": add this with smaller font under its name on the
    left tab (menu)."""
    note = "(with connections to estimation, optimization, ML, inverse problems, BSS)"
    assert bpnav.notes() == {"Signal Processing & System ID": note}
    for page, up in (("about.html", ""), (f"doc/{build.SIGNAL}.html", "../")):
        markup = column(page, up)
        lis = re.findall(r'<li[^>]*><a href="[^"]+"[^>]*><span class="nav__w".*?</a></li>', markup)
        two = [li for li in lis if "nav__n" in li]
        assert len(two) == 1 and two[0].startswith('<li class="nav__two">')
        # under the words, inside the link: its name is everything it shows
        assert (f'Signal Processing &amp; System ID</span><span class="nav__sep"> </span>'
                f'<span class="nav__n">{html.escape(note)}</span></a>') in two[0]
    css = bpnav.CSS
    # a set height (three lines) and the bead and branch on the words' line
    assert re.search(r"\.nav \.nav__sub \.nav__n\{[^}]*height:3\.9em", css)
    assert ".nav .nav__sub li.nav__two>a::before" in css
    assert "top:calc(var(--u) * .5px)" in css
    # the trunk reaches that much further for the topics below it, on a finger
    assert ".nav__sub:has(>li.nav__two ~ li>a:is(:focus-visible,:active,.p)){--x:48}" in css
    assert "  .nav__sub:has(>li.nav__two ~ li>a:hover){--x:48}" in css     # in the hover block
    assert "+ var(--x, 0)) / (var(--u) * 12))" in css
    # the orbs aim at the words' line, not the link's middle
    assert "items[i].firstElementChild.offsetTop+items[i].firstElementChild.offsetHeight/2" in bpnav.JS


def test_each_topic_opens_the_page_its_row_opened(column):
    items = topics(column("about.html", ""))
    # his topics' rows, which the home page's topic cards still are, but the
    # one the column keeps as a row of its own
    assert sorted(h for h, _, _ in items) == sorted(
        h for h, _, _, _ in build.NAV if h in build.TOPIC_ICONS and h not in build.OWN_ROW) == sorted(TOPICS)
    assert all("#" not in h for h, _, _ in items)       # a page, never a place in it
    # from a document page every link climbs out of doc/ first
    assert all(h.startswith("../") for h, _, _ in topics(column(f"doc/{build.SHORT}.html", "../")))


def test_the_list_keeps_the_big_picture_pages_order(column):
    # one order everywhere: the list's is the page's (27 Sep 2026, his five on
    # one line, Probability & Statistics first), read from the page's module
    assert [h for h, _, _ in topics(column("about.html", ""))] == order()
    assert [c[0] for c in bpnav.categories()] == [c["id"] for c in documents.CATEGORIES
                                                  if c["id"] not in bpnav.NOT_TOPICS]


def test_his_research_is_not_a_topic_of_the_list(monkeypatch):
    # should the page file his research with the topics, the list leaves it
    # out: the column has its row, My Research Areas
    cats = [dict(id="research", label="From my research", docs=["sound-detection-and-tracking"],
                 soon=None)] + [dict(c) for c in documents.CATEGORIES]
    monkeypatch.setattr(documents, "CATEGORIES", cats)
    assert "research" not in [c[0] for c in bpnav.categories()]
    assert len(bpnav.categories()) == len(cats) - 1


def test_a_topic_opens_its_rows_page_whatever_order_its_documents_take(column, monkeypatch):
    cats = [dict(c) for c in documents.CATEGORIES]
    waves = next(c for c in cats if c["id"] == "waves-dynamics")
    waves["docs"] = list(reversed(waves["docs"]))
    monkeypatch.setattr(documents, "CATEGORIES", cats)
    assert WAVES_PAGE in [h for h, _, _ in topics(column("about.html", ""))]


def test_a_topics_page_marks_the_big_picture_row_and_the_topic(column):
    for href in TOPICS:
        up = "../" * href.count("/")
        section = build.doc_section(href[4:-5]) if href.startswith("doc/") else ""
        markup = column(href, up, section)
        assert marked(markup) == [(up + BP, ' class="on" aria-current="true"')]
        assert [(h, c) for h, _, c in topics(markup) if c] == [(up + href, "page")]
        # open with the page, before its first paint
        li = bp_row(markup)
        assert li.startswith(' nav__bp--in">' + bpnav.HOLD + '<div class="nav__row">')
        assert 'aria-expanded="true"' in li.split("</button>", 1)[0]


def test_from_bridges_to_photons_is_marked_under_waves_and_dynamics(column):
    slug = build.PHOTONS
    markup = column(f"doc/{slug}.html", "../", build.doc_section(slug))
    assert marked(markup) == [("../" + BP, ' class="on" aria-current="true"')]
    assert [(h, c) for h, _, c in topics(markup) if c] == [("../" + WAVES_PAGE, "true")]
    assert bp_row(markup).startswith(' nav__bp--in">' + bpnav.HOLD)


def test_the_big_picture_page_opens_its_list_and_marks_no_topic(column):
    markup = column(BP, "")
    assert marked(markup) == [(BP, ' class="on" aria-current="page"')]
    assert not [c for _, _, c in topics(markup) if c]
    # its list opens by the reader's choice, which head_js() reads
    assert bp_row(markup).startswith(' nav__bp--here">') and bpnav.HOLD not in markup
    assert 'aria-expanded="true"' in markup


def test_elsewhere_the_list_is_as_the_reader_left_it(column):
    for page, up, section in (("about.html", "", ""), ("cv.html", "", "about.html"),
                              (f"doc/{build.SOUND}.html", "../", "research.html"),
                              ("post/x.html", "../", "blog.html")):
        markup = column(page, up, section)
        assert "nav__bp--" not in markup and bpnav.HOLD not in markup
        assert 'aria-expanded="false"' in markup
        assert not [c for _, _, c in topics(markup) if c]
        assert [h for h, _ in marked(markup)] == [up + (section or page)]


def test_without_the_part_the_topics_stay_out_and_the_row_is_marked_the_same():
    assert build.BPNAV is None      # as a test imports build; main() loads the part
    markup = build.nav_html(f"doc/{build.ML}.html", "../", build.doc_section(build.ML))
    assert [h for h, _ in rows(markup)] == ["../" + h for h in ROWS]
    assert marked(markup) == [("../" + BP, ' class="on" aria-current="true"')]
    assert "nav__fold" not in markup and "<script" not in markup


def test_the_categories_come_from_the_big_picture_page():
    cats = bpnav.categories()
    assert [c[0] for c in cats] == [c["id"] for c in documents.CATEGORIES]
    pages = dict((c[0], c[2]) for c in cats)
    # a category's pages: its page in preparation, or its documents in order
    assert pages["waves-dynamics"] == (WAVES_PAGE, f"doc/{build.PHOTONS}.html")
    assert pages["python-programming"] == ("python-programming.html",)
    assert "communication" not in pages


def test_a_topic_that_is_a_deck_opens_it(monkeypatch):
    # Probability & Statistics has no document and no page in preparation,
    # only his deck (documents.CATEGORIES' `decks`): read from the module, the
    # list keeps it, rather than the copy standing in for all six
    cats = [dict(c, decks=["x.html"]) if c.get("decks") else c for c in documents.CATEGORIES]
    monkeypatch.setattr(documents, "CATEGORIES", cats)
    assert dict((i, p) for i, _, p in bpnav.categories())["probability-statistics"] == ("x.html",)


def test_the_fallback_is_the_same_list(monkeypatch):
    cats = documents.CATEGORIES
    real = [(i, p) for i, _, p in bpnav.categories()]
    monkeypatch.setattr(documents, "CATEGORIES", None)
    assert [(i, p) for i, _, p in bpnav.categories()] == real
    # a module mid-edit, its documents under another name: the copy stands in
    # whole, rather than a list short of its three guides
    monkeypatch.setattr(documents, "CATEGORIES", [
        {k: v for k, v in c.items() if k != "docs"} for c in cats])
    assert bpnav.categories() == list(bpnav.FALLBACK)


# ------------------------------------------------------------------ the chevron and its call

def _points(d):
    """The vertices of an M/L path with absolute and relative steps."""
    pts, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r"([MLml])([^MLml]*)", d):
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+", args)]
        for i in range(0, len(nums), 2):
            dx, dy = nums[i], nums[i + 1]
            x, y = (x + dx, y + dy) if cmd.islower() else (dx, dy)
            pts.append((x, y))
    return pts


def test_the_chevron_points_down_centred_on_its_grid():
    # two chevrons, one over the other (the professor: "double arrow"), stroke 2.2,
    # in a span of the page's own that the call nudges on the compositor
    assert bpnav.CHEVRON.startswith('<span class="nav__cv"><svg class="nav__chev" ')
    assert bpnav.CHEVRON.endswith("</svg></span>")
    ds = re.findall(r'<path d="([^"]+)"', bpnav.CHEVRON)
    assert len(ds) == 2 and 'stroke-width="2.2"' in bpnav.CHEVRON
    pts = []
    for d in ds:
        (ax, ay), (tx, ty), (bx, by) = _points(d)
        assert ty > ay == by and ax < tx < bx             # the tip below the arms: down
        pts += [(ax, ay), (tx, ty), (bx, by)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    assert (min(xs) + max(xs)) / 2 == 12 == (min(ys) + max(ys)) / 2
    # open, it has turned half round, on the spring and at rest alike
    assert '[data-bp="open"] .nav__chev{transform:rotate(-180deg)}' in bpnav.CSS
    assert "rotate('+(-180*p)+'deg)" in bpnav.JS


def test_the_call_for_a_look():
    css, js = bpnav.CSS, bpnav.JS
    # warm while the list has never been seen open, under the hover and focus states
    assert ':where([data-bp-new][data-bp="closed"]) .nav__x{color:var(--accent-on-nav)}' in css
    # only where motion is welcome, and only while the question stands: every
    # 6s the chevron dips and the ring swells (the client liked the beat, 27
    # Sep 2026), from when the script marks the row .nav__bp--call
    motion = css.split("@media (prefers-reduced-motion:no-preference){\n  .nav__x::after", 1)[1]
    motion = motion.split("\n}\n", 1)[0]
    call = ':where([data-bp-new][data-bp="closed"]) .nav__bp--call '
    assert (call + ".nav__cv{\n    animation:bpnav-nudge 6s cubic-bezier(.3,0,.2,1) "
            "infinite}") in motion
    assert (call + ".nav__x::after{\n    animation:bpnav-ring 6s cubic-bezier(.2,.8,.2,1) "
            "infinite}") in motion
    # those two are the only loops in the column, and they rest where no one
    # sees them: off screen, or in a hidden tab
    assert css.count("infinite") == 2 and "setInterval" not in js
    assert (".nav__bp.nav__bp--still .nav__cv,.nav__bp.nav__bp--still .nav__x::after{\n"
            "    animation-play-state:paused}") in motion
    assert "function still(){li.classList.toggle('nav__bp--still',!shown||document.hidden)}" in js
    assert "if(asks)document.addEventListener('visibilitychange',still);" in js
    assert "shown=r.intersectionRatio>=.01;if(asks)still();" in js and "{threshold:[0,.01,.9]}" in js
    # never under reduced motion, and the list seen open ends it
    assert "asks=H.hasAttribute('data-bp-new')&&!goal&&!calm.matches" in js
    assert "if(called||goal||!H.hasAttribute('data-bp-new'))return;" in js
    # it starts as the thought that runs the line lands in the chevron, once
    # the row is on screen; cut short (the row hidden on its way) it starts all
    # the same; where no orb is drawn, once the page has been up 1.2s
    assert "if(r.intersectionRatio>=.9){if(orbs)intro();else if(asks)when()}" in js
    assert "else{s=QA+QB;if(!PG){PG=1;arrive()}}" in js
    assert "if(H.hasAttribute('data-bp-new')){call();return}" in js
    assert "if(P===1&&!PG)arrive();" in js
    assert "setTimeout(call,Math.max(300,1200-performance.now()))" in js
    # the light that once ran the beads by keyframes is the thought now
    assert "bpnav-light" not in css and "nav__bp--ask" not in css + js
    # the nudge moves the icon by translate, which never meets the spring's transform
    nudge = re.search(r"@keyframes bpnav-nudge\{(.*?)\n\}", css, re.S).group(1)
    assert "translate:0 3px" in nudge and "translate:0 2px" in nudge and "transform" not in nudge
    ring = re.search(r"@keyframes bpnav-ring\{(.*?)\n\}", css, re.S).group(1)
    assert set(re.findall(r"([a-z-]+):", ring)) <= {"opacity", "transform", "animation-timing-function"}
    # asked for less motion: a warm dot that stands still
    calm = css.split("@media (prefers-reduced-motion:reduce){", 1)[1].split("\n}\n", 1)[0]
    assert "background:var(--accent-on-nav);opacity:1" in calm and "animation" not in calm
    # the hover's dip is for a pointer that hovers and aims, and moves the path
    assert ("@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){"
            "\n  .nav__chev path{transition:translate") in css


def test_hover_intent_is_the_mouses_alone():
    js = bpnav.JS
    assert "fine=matchMedia('(hover: hover) and (pointer: fine)')" in js
    assert "if(e.pointerType!=='mouse'||!fine.matches)return;" in js
    assert "},600);" in js
    # an opening by hover is not stored as the reader's choice
    assert "choose(true,1)" in js and "if(!by)try{localStorage.setItem(K," in js


def test_the_part_draws_no_colour_of_its_own():
    # dark mode comes from the tokens: every colour is one of theme.py's, in
    # the stylesheet and on the orbs' canvas alike, which reads them as it plays
    assert not re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(|oklch\(", bpnav.CSS + bpnav.JS)
    js = bpnav.JS
    assert ("INK=s.getPropertyValue('--nav-ink').trim();MUTE=s.getPropertyValue('--nav-mute').trim();\n"
            "  WARM=s.getPropertyValue('--accent-on-nav').trim();") in js
    styles = re.findall(r"(?:fill|stroke)Style=([^;]+);", js)
    assert styles and all(set(re.findall(r"[A-Z]{3,}", v)) <= {"INK", "MUTE", "WARM"}
                          or v == "o.col" for v in styles), styles
    assert all("'" not in v and '"' not in v for v in styles), styles
    # the thought is white in the column's light, never warm: the client
    # disliked orange in motion, and warm is "you are here" and the chevron's
    # alone (ROUND15); on the canvas it is the warm orb of the page's topic
    assert [v for v in styles if "WARM" in v] == ["warm?WARM:INK"]
    spark = js[js.index("function spark("):js.index("function tail(")]
    assert "g.fillStyle=MUTE;" in spark and "g.fillStyle=INK;" in spark and "WARM" not in spark
    assert "WARM" not in js[js.index("function tail("):js.index("/* start: the orbs")]
    tip = re.search(r"\.nav__tip\{([^}]*)\}", bpnav.CSS).group(1)
    assert "background:var(--nav-ink)" in tip and "accent" not in tip
    # the portrait's halo takes the ring colour on paper, where it sits
    assert "o.col=getComputedStyle(p).getPropertyValue('--focus').trim();" in js


def test_no_dash_in_the_part():
    src = open(bpnav.__file__, encoding="utf-8").read()
    assert "\u2014" not in src and " \u2013 " not in src


# ------------------------------------------------------------------ the line under the title

def _line(markup):
    return re.search(r'<span class="nav__map" aria-hidden="true">(.*?)</span>', markup).group(1)


def _here(markup):
    """The places of the line's marked beads."""
    return [k for k, h in enumerate(re.findall(r'<i class="b( h)?"', _line(markup))) if h]


def test_the_line_draws_a_bead_for_each_topic_in_the_lists_order(column):
    markup = column("about.html", "")
    link = re.search(r'<div class="nav__row"><a [^>]*>(.*?)</a>', markup).group(1)
    # under the title, inside the link, drawn and not said: the link's name is
    # its title, and the list is where a screen reader hears the topics
    assert link.startswith('<span class="nav__t">Big Picture of Waves and Data Analytics</span>'
                           '<span class="nav__map" aria-hidden="true">')
    line = _line(markup)
    assert re.sub(r"<[^>]+>", "", line) == ""
    n = len(topics(markup))
    beads = [int(i) for i in re.findall(r'<i class="b(?: h)?" style="--i:(\d+)"></i>', line)]
    strokes = [int(i) for i in re.findall(r'<i class="s" style="--i:(\d+)"></i>', line)]
    assert n == 5 and beads == list(range(n)) and strokes == list(range(n - 1))
    assert line.endswith('<i class="v"></i>')           # the branch's first stretch
    # no topic is the page here, nor on the Big Picture page itself
    assert _here(markup) == [] and _here(column(BP, "")) == []


def test_the_line_marks_the_topic_the_page_is_filed_under(column):
    for href in TOPICS:
        up = "../" * href.count("/")
        section = build.doc_section(href[4:-5]) if href.startswith("doc/") else ""
        assert _here(column(href, up, section)) == [order().index(href)]
    # From Bridges to Photons, filed under Waves and Dynamics
    markup = column(f"doc/{build.PHOTONS}.html", "../", build.doc_section(build.PHOTONS))
    assert _here(markup) == [order().index(WAVES_PAGE)]


def test_the_line_is_the_list_folded():
    css = bpnav.CSS
    # closed, its beads and strokes show; open, they are gone and the branch's
    # first stretch stands; the same without the script, by the pages whose
    # list shows
    assert '[data-bp="closed"] .nav__map :is(.b,.s){opacity:1}' in css
    assert '[data-bp="closed"] .nav__map .v{transform:scaleY(0)}' in css
    assert ('[data-bp="open"] .nav__map :is(.b,.s){opacity:0}' in css
            and '[data-bp="open"] .nav__map .v{transform:none}' in css)
    assert ":is(.nav__bp--here,.nav__bp--in) .nav__map :is(.b,.s)," in css
    # one axis: the first bead's centre and the first stretch are on the list's
    # branch, 20px of the row's padding less 3px, and half the 7px bead
    assert "margin:5px 0 0 -3px" in css and "width:7px;height:7px" in css
    assert ".nav__map .v{left:3px;top:3px;width:1px;height:calc(var(--pad) + 5px)" in css
    assert ".nav__sub::before{content:\"\";position:absolute;z-index:1;left:20px;top:0;" in css
    assert 20 - 3 + 7 / 2 == 20 - 3 + 3 + 1 / 2 == 20 + 1 / 2
    # the stretch runs from the line's middle (3px) to the row's foot: the rest
    # of the 7px line and the row's bottom padding, --pad and 1px
    assert 7 - 3 + 1 == 5
    theme_pad = re.search(r"padding:var\(--pad\) 16px calc\(var\(--pad\) \+ 1px\) 20px", theme.CSS)
    assert theme_pad


def test_the_line_turns_down_on_the_folds_spring():
    js = bpnav.JS
    paint = js[js.index("function paint(){"):js.index("function clear(){")]
    turn = paint[paint.index("if(map){"):]
    # as far as the line has run down from its first bead, it is short across
    # the row, so it goes round the corner at the fold's speed
    assert "run=p*(h+S),hor=len-run" in turn
    assert set(re.findall(r"\.style\.(\w+)=", turn)) == {"opacity", "transform"}
    # one layout read per toggle and none per frame; at rest nothing is inline
    measure = js[js.index("function measure(){"):js.index("function paint(){")]
    assert "offsetLeft" in measure and "offset" not in paint
    # a topic's place is its <li>'s: the link sits at 0 inside it, so the
    # topics came in all at once instead of top to bottom
    assert "tops[i]=items[i].parentNode.offsetTop" in measure
    clear = js[js.index("function clear(){"):js.index("function scroller(){")]
    for part in ("dots[i].style.opacity=dots[i].style.transform=''",
                 "segs[i].style.opacity=segs[i].style.transform=''", "stub.style.transform=''"):
        assert part in clear


def test_the_lines_states_are_colour_and_keep_the_column_rules():
    css = bpnav.CSS
    lit = "background:var(--nav-mute);border-color:var(--nav-mute)"
    # lit as the list lights a topic's bead: the row being the page...
    assert ":where(.nav__row>a.on) .nav__map .b{" + lit + "}" in css
    # ...under the pointer, where a pointer hovers, each bead as the row's fill
    # reaches it: the fill's edge crosses the row's 240px on the mid spring
    hover = "".join(_blocks(css, "@media (hover:hover){"))
    assert ":where(.nav__row:hover) .nav__map .b{" + lit + ";\n    transition-delay:calc(18ms + var(--i) * 17ms)}" in hover
    from parts.springs import SPRINGS
    _, settle, easing = SPRINGS["mid"]
    ys = [float(v) for v in easing[len("linear("):-1].split(",")]

    def reach(s):
        i = next(i for i in range(1, len(ys)) if ys[i] >= s)
        return (i - 1 + (s - ys[i - 1]) / (ys[i] - ys[i - 1])) * settle / (len(ys) - 1)
    for k in range(5):
        assert abs(reach((20.5 + 28 * k) / 240) - (18 + 17 * k)) < 4
    # ...and under a key, at once, outside the hover block
    assert (":where(.nav__row:has(:focus-visible)) .nav__map .b{background:var(--nav-mute);\n"
            "  border-color:var(--nav-mute);transition:none}") in css
    assert ":focus-visible" not in hover
    # pressed, white with the row
    assert ":where(.nav__row>a:active) .nav__map .b{background:var(--nav-ink);border-color:var(--nav-ink)}" in css
    # warm is "you are here" alone: the bead of the page's topic, on the row
    # that is its section
    assert ".nav__row>a.on .nav__map .b.h{background:var(--accent-on-nav);border-color:var(--accent-on-nav)}" in css
    # its own transitions are colour: the script moves it, by transform and opacity
    for body in re.findall(r"[^{}]*\.nav__map[^{}]*\{([^}]*)\}", css):
        for m in re.findall(r"transition:([^;}]+)", body):
            assert {p.split()[0] for p in m.split(",")} <= {"background-color", "border-color", "none"}, m


# ------------------------------------------------------------------ the column's fit

def test_nothing_hides_or_tightens_when_the_list_opens():
    assert ":has(> a[href" not in theme.CSS           # the topics' rows are gone, not hidden
    assert '[data-bp="open"]' not in theme.CSS        # nothing shrinks for the list


def test_the_portraits_file_is_the_size_the_column_draws_it():
    # the portrait is drawn at --pic, and portrait()'s sizes fetches the file
    # for that size: the two change together, or a short window's is blurred
    tall = re.search(r"--pic:(\d+)px;", theme.CSS).group(1)
    short = re.search(r"@media \(max-height:(\d+)px\)\{\s*:root\{[^}]*--pic:(\d+)px", theme.CSS)
    img = build.portrait("", "id__pic", int(tall))
    assert f'sizes="(max-height: {short.group(1)}px) {short.group(2)}px, {tall}px"' in img


# ------------------------------------------------------------------ before the first paint

NODE = shutil.which("node")
HARNESS = """
const [code, page, store, session, reduce, short] = JSON.parse(process.argv[1]);
const attrs = {};
const doc = {documentElement: {setAttribute(k, v) { attrs[k] = v; }}};
const local = {getItem(k) { if (store === null) throw new Error("refused"); return store[k] ?? null; }};
const sess = {getItem(k) { return session[k] ?? null; }};
const mm = q => ({matches: q.includes("reduce") ? reduce : q.includes("min-height") ? !short : false});
new Function("document", "localStorage", "sessionStorage", "matchMedia", code)(doc, local, sess, mm);
if (page === "in") new Function("document", "matchMedia", %s)(doc, mm);
console.log(JSON.stringify(attrs));
"""


def _first_paint(page, store, session=None, reduce=False, short=False):
    hold = re.search(r"<script>(.*)</script>", bpnav.HOLD).group(1)
    code = bpnav.head_js(page == "bp")
    out = subprocess.run([NODE, "-e", HARNESS % json.dumps(hold),
                          json.dumps([code, page, store, session or {}, reduce, short])],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@pytest.mark.skipif(not NODE, reason="runs the script in node")
def test_the_state_before_the_first_paint():
    # a first visit: closed, and asking for a look
    assert _first_paint("about", {}) == {"data-bp": "closed", "data-bp-new": ""}
    # seen once, it never asks again; nor where storage refuses to remember
    assert _first_paint("about", {"wad:bp-seen": "1"}) == {"data-bp": "closed"}
    assert _first_paint("about", None) == {"data-bp": "closed"}
    # the reader's choice holds from page to page
    assert _first_paint("about", {"wad:bp": "open", "wad:bp-seen": "1"}) == {"data-bp": "open"}
    # the Big Picture page opens its list and never asks
    assert _first_paint("bp", {}) == {"data-bp": "open"}
    assert _first_paint("bp", {"wad:bp": "closed"}) == {"data-bp": "closed"}
    # arriving from a folded list, once a visit, it unfolds after the first paint
    assert _first_paint("bp", {}, {"wad:bp-shown": "closed"}) == {
        "data-bp": "closed", "data-bp-go": "open"}
    assert _first_paint("bp", {}, {"wad:bp-shown": "closed"}, reduce=True) == {"data-bp": "open"}
    # a page the list holds opens it whatever the reader chose
    assert _first_paint("in", {"wad:bp": "closed", "wad:bp-seen": "1"})["data-bp"] == "open"
    # in a window too short for the open list (a laptop's 1440x789 or 1366x657)
    # no page opens it by itself; the reader's own choice still holds
    assert _first_paint("bp", {}, short=True) == {"data-bp": "closed"}
    assert _first_paint("in", {"wad:bp-seen": "1"}, short=True) == {"data-bp": "closed"}
    assert _first_paint("in", {"wad:bp": "open", "wad:bp-seen": "1"}, short=True) == {"data-bp": "open"}


def test_the_open_list_is_held_only_where_it_fits():
    # theme.py's rows end at 827 + 8 x pad (740 + 8 x pad under 860px tall) at
    # the kink's low side, with 24px of air: 6px rows fit from 900px, and from
    # 812px with the shorter identity
    assert bpnav.OPEN_FITS == "(min-height:900px), (min-height:812px) and (max-height:860px)"
    assert bpnav.OPEN_FITS in bpnav.HOLD and bpnav.OPEN_FITS in bpnav.head_js(True)
    css = theme.CSS
    assert "--pad:clamp(6px,min(calc((100vh - 851px) / 8),calc((100vh - 770px) / 16)),12px)" in css
    assert "--pad:clamp(6px,min(calc((100vh - 764px) / 8),calc((100vh - 699px) / 16)),12px)" in css
    for h, shorter in ((900, False), (1026, False), (1200, False), (812, True), (860, True)):
        low, high = ((740, 675) if shorter else (827, 746))
        pad = max(6, min((h - low - 24) / 8, (h - high - 24) / 16, 12))
        # the last row's end: the line in force is the larger of the two
        assert max(low + 8 * pad, high + 16 * pad) <= h - 24 + 1e-9, (h, pad)


ARRIVAL = """
const [code, side, width, reduce, seen, refuse] = JSON.parse(process.argv[1]);
const attrs = side ? {"data-side": side} : {};
const doc = {documentElement: {setAttribute(k, v) { attrs[k] = v; },
                                getAttribute(k) { return k in attrs ? attrs[k] : null; }}};
const kept = seen ? {"wad:id-in": "1"} : {};
const sess = {getItem(k) { if (refuse) throw new Error("refused"); return kept[k] ?? null; },
              setItem(k, v) { if (refuse) throw new Error("refused"); kept[k] = v; }};
const local = {getItem() { return null; }};
const mm = q => ({matches: q.includes("reduce") ? reduce : q.includes("1000px") ? width > 1000 : false});
new Function("document", "localStorage", "sessionStorage", "matchMedia", code)(doc, local, sess, mm);
console.log(JSON.stringify({arrives: "data-id-in" in attrs, kept}));
"""


def _arrival(side="open", width=1440, reduce=False, seen=False, refuse=False):
    out = subprocess.run([NODE, "-e", ARRIVAL, json.dumps(
        [bpnav.head_js(False), side, width, reduce, seen, refuse])],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@pytest.mark.skipif(not NODE, reason="runs the script in node")
def test_the_column_arrives_once_a_visit_and_only_where_it_shows():
    first = _arrival()
    assert first == {"arrives": True, "kept": {"wad:id-in": "1"}}
    assert not _arrival(seen=True)["arrives"]             # every later page opens still
    assert not _arrival(width=900)["arrives"]             # the phone's drawer is shut
    assert not _arrival(side="closed")["arrives"]         # the column is folded away
    assert not _arrival(reduce=True)["arrives"]           # less motion asked for
    assert not _arrival(refuse=True)["arrives"]           # could not remember it had played
    # and the mark leaves once the arrival has played
    assert "H.removeAttribute('data-id-in')" in bpnav.JS


# ------------------------------------------------------------------ the column's motion

def _column_css():
    """The column's own rules in parts/theme.py (THE COLUMN up to THE FOLD), and the part's."""
    css = theme.CSS
    return css[css.index("THE COLUMN"):css.index("THE FOLD")] + bpnav.CSS


def _blocks(css, head):
    """The bodies of the blocks that open with `head`, braces balanced."""
    out, i = [], css.find(head)
    while i >= 0:
        j, depth = i + len(head), 1
        while depth:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        out.append(css[i + len(head):j - 1])
        i = css.find(head, j)
    return out


def test_hover_in_the_column_is_fills_rails_and_lines():
    css = _column_css()
    hover = "".join(_blocks(css, "@media (hover:hover){")
                    + _blocks(css, "@media (hover:hover) and (pointer:fine) and (prefers-reduced-motion:no-preference){"))
    assert hover
    # DESIGN_BRIEF.md 4, banned for good: no translateY, no shadow change
    assert "translateY" not in hover and "box-shadow" not in hover
    # what travels, travels on a spring (a topic's light is a clip); nothing
    # lays anything out
    for prop in re.findall(r"transition:([^;}]+)", hover):
        for part in prop.split(","):
            name = part.split()[0]
            assert name in {"transform", "translate", "--id-arc", "opacity", "clip-path"}, part
            if name != "opacity":
                assert "var(--spring-" in part, part
    # every :hover rule sits in a hover block; :focus-visible never does
    rest = css
    for b in _blocks(css, "@media (hover:hover){"):
        rest = rest.replace(b, "")
    assert ":hover" not in re.sub(r"@media \(hover:hover\)[^{]*\{", "", rest).replace(
        ".nav__row:hover .nav__chev path", "")
    assert ":focus-visible" not in hover


def test_the_rows_fill_out_of_the_rail_and_warm_stays_with_the_current_page():
    css = theme.CSS
    # the fill: a layer under the words, wiping in from the column's edge
    assert ".nav{isolation:isolate;" in css
    fill = re.search(r"\.nav a::after\{([^}]*)\}", css).group(1)
    assert "z-index:-1" in fill and "transform:scaleX(0);transform-origin:0 50%" in fill
    # the rail: grown from the row's middle, light under the pointer
    rail = re.search(r"\.nav a::before\{([^}]*)\}", css).group(1)
    assert "background:var(--nav-mute)" in rail and "transform:scaleY(0)" in rail
    # leaving: both fade where they stand, then fold back unseen
    for layer in (fill, rail):
        assert "transition:opacity var(--t-quick) var(--ease-state),transform 0s var(--t-quick)" in layer
    hover = "".join(_blocks(css, "@media (hover:hover){"))
    assert ".nav a:hover::after{opacity:1;transform:none;transition:transform var(--spring-mid)}" in hover
    assert ".nav a:hover::before{opacity:1;transform:none;transition:transform var(--spring-fast)}" in hover
    # the warm mark is the current page's alone, on the column as in the list
    col = _column_css()
    # (the call's warm light, a keyframe, is held to data-bp-new by the call's test)
    calm = re.sub(r"@keyframes bpnav-light\{.*?\n\}", "", col, flags=re.S)
    warm = [m.group(0) for m in re.finditer(r"[^{}]*\{[^}]*accent-on-nav[^}]*\}", calm)]
    assert all("[aria-current]" in w or ".on" in w or "data-bp-new" in w
               or "nav__x::after" in w or "--accent-on-nav:" in w for w in warm), warm
    assert ".nav .on::before{background:var(--accent-on-nav);opacity:1;transform:none}" in css
    # a key takes the end state at once
    assert ".nav a:focus-visible::before,.nav a:focus-visible::after{opacity:1;transform:none;transition:none}" in css
    # the Big Picture row fills as one, under its button too
    assert "[data-bp] .nav__row>a::after{right:-40px}" in bpnav.CSS
    assert "[data-bp] .nav__row>a::after{right:-48px}" in bpnav.CSS


def test_the_trunk_lights_down_to_the_topic():
    css = bpnav.CSS
    # its reach is where the topic's bead is: the list's 2px of padding, half
    # a row, a row per topic above it, over a line twelve rows long
    assert "padding:2px 0 12px;\n  pointer-events:auto;--u:32}" in css
    assert ".nav .nav__sub a{min-height:32px;" in css and "--u:44}" in css
    # (--x: a topic's note above it makes its row that much taller, 48px)
    assert "--reach:calc((var(--k) * var(--u) - var(--u) / 2 + 2 + var(--x, 0)) / (var(--u) * 12))" in css
    assert "height:calc(var(--u) * 12px)" in css
    for u in (32, 44):
        for k in range(1, 6):
            bead = 2 + u / 2 + u * (k - 1)           # the bead's centre, from the list's top
            assert (k * u - u / 2 + 2) / (u * 12) * (u * 12) == bead < u * 12
    # each topic's place, for the pointer and for a key, ten of them
    for k in range(1, 11):
        assert f".nav__sub:has(>li:nth-child({k})>a:hover){{--k:{k}}}" in css
        assert f".nav__sub:has(>li:nth-child({k})>a:focus-visible){{--k:{k}}}" in css
    # the current topic keeps its warm bead and branch and takes none of it
    assert ".nav .nav__sub li:has(>a[aria-current])::before{content:none}" in css
    assert ".nav__sub:has(>li>a:not([aria-current]):hover)::after" in css
    # under a finger it takes the same path, from the press
    for k in range(1, 11):
        assert f".nav__sub:has(>li:nth-child({k})>a:is(:active,.p)){{--k:{k}}}" in css
    assert ".nav__sub:has(>li>a:not([aria-current]):is(:active,.p))::after{opacity:1;" in css


def test_a_topic_lights_by_its_words_and_a_line_never_a_fill():
    # 29 Sep 2026: the client found the fill that swept under the pointer very
    # bad. A topic takes neither the rows' fill nor their press shade...
    css = bpnav.CSS
    assert ".nav .nav__sub a::after{content:none}" in css
    assert ".nav .nav__sub a:active{background:transparent}" in css
    # ...but its words: a white copy laid over their grey, drawn and not said
    # (its alternative text is empty), uncovered from the left by its clip on
    # a spring and faded where it stands on the way out; and a hairline under
    # them, drawn with the white's edge. No gradient text.
    copy = re.search(r"\.nav \.nav__sub a:not\(\[aria-current\]\) \.nav__w::before\{([^}]*)\}", css).group(1)
    assert 'content:attr(data-w) / "";position:absolute;inset:0;' in copy
    assert "color:var(--nav-ink);pointer-events:none;opacity:0;clip-path:inset(0 100% 0 0);" in copy
    assert "transition:opacity var(--t-quick) var(--ease-state),clip-path 0s var(--t-quick)" in copy
    assert "background-clip" not in css and "text-fill-color" not in css
    line = re.search(r"\.nav \.nav__sub a:not\(\[aria-current\]\) \.nav__w::after\{([^}]*)\}", css).group(1)
    assert "bottom:-2px;height:1px;background:var(--nav-mute)" in line
    assert "transform:scaleX(0);transform-origin:0 50%" in line
    hover = "".join(_blocks(css, "@media (hover:hover){"))
    assert (".nav .nav__sub a:not([aria-current]):hover .nav__w::before{opacity:1;clip-path:inset(0);\n"
            "    transition:clip-path var(--spring-mid) 90ms}") in hover
    assert (".nav .nav__sub a:not([aria-current]):hover .nav__w::after{opacity:1;transform:none;\n"
            "    transition:transform var(--spring-mid) 90ms}") in hover
    # a key: all of it at once, outside the hover block
    assert (".nav .nav__sub a:not([aria-current]):focus-visible .nav__w::before{opacity:1;clip-path:inset(0);\n"
            "  transition:none}") in css
    # the words are said once: the label is the link's text; the copy is an
    # attribute of its span, which breaks where the words do
    markup = bpnav.row(BP, "t", "", "", [("Machine Learning", "ml.html", ""),
                                         ("Python / Programming", "py.html", "")])
    assert ('<a href="ml.html"><span class="nav__w" data-w="Machine Learning">Machine Learning</span></a>'
            in markup)
    assert 'data-w="Python\u00a0/ Programming">Python\u00a0/ Programming</span>' in markup
    # forced colours: no copy, and the line in the system's text colour
    forced = css.split("@media (forced-colors:active){", 1)[1].split("\n}\n", 1)[0]
    assert ".nav .nav__sub a .nav__w::before{content:none}" in forced
    assert ".nav .nav__sub a .nav__w::after{background:CanvasText}" in forced


def test_a_finger_gets_the_same_from_the_press():
    css, js = bpnav.CSS, bpnav.JS
    # :active, and .p, which the script sets as a finger or a pen lands (a
    # touch browser may paint :active late or not at all), on the quick
    # spring; outside the hover block, since a finger cannot hover
    press = ".nav .nav__sub a:not([aria-current]):is(:active,.p)"
    assert (press + " .nav__w::before{opacity:1;clip-path:inset(0);\n"
            "  transition:clip-path var(--spring-quick)}") in css
    assert (press + " .nav__w::after{opacity:1;transform:none;\n"
            "  transition:transform var(--spring-quick)}") in css
    assert ":active" not in "".join(_blocks(css, "@media (hover:hover){"))
    assert "a.addEventListener('pointerdown',function(e){if(e.pointerType!=='mouse')a.classList.add('p')});" in js
    # it lets go if the press became a scroll, or led nowhere
    assert "a.addEventListener('pointercancel',off);" in js
    assert "a.addEventListener('pointerup',function(){setTimeout(off,1500)});" in js
    # the orb wakes at once and the thought runs down on the quick spring
    assert "a.addEventListener('pointerdown',function(e){if(e.pointerType!=='mouse')aim(k,2)});" in js
    assert "if(LA<=0){LT=BY;LV=0}HK=k;HT=1;LW=mode?PRESS:AIM;\n    if(mode)wake(j,performance.now());" in js
    # and the link is followed as ever: nothing waits for the motion
    assert "preventDefault" not in js


def test_the_ring_and_the_arrival():
    css = theme.CSS
    assert '@property --id-arc{syntax:"<angle>";inherits:false;initial-value:0deg}' in css
    hover = "".join(_blocks(css, "@media (hover:hover){"))
    assert ".id:hover::before{--id-arc:360deg;opacity:1;transition:--id-arc var(--spring-draw)}" in hover
    assert ".id:focus-visible::before{--id-arc:360deg;opacity:1;transition:none}" in css
    # the home page's block is the page the reader is on: warm, at rest
    assert ".id[aria-current]::before{--id-arc:360deg;opacity:1;border-color:var(--accent)}" in css
    # the arrival: only on a desktop column, only where motion is welcome
    (arrive,) = _blocks(css, "@media (width > 1000px) and (prefers-reduced-motion:no-preference){")
    assert arrive.count("[data-id-in]") == 8
    frames = re.findall(r"@keyframes id-[\w-]+\{from\{([^}]*)\}\}", css)
    assert len(frames) == 7
    assert {p for f in frames for p in re.findall(r"([\w-]+):", f)} <= {
        "opacity", "filter", "transform", "--id-arc"}
    # and nothing of it outlives the motion: fill backwards, never forwards
    assert "forwards" not in arrive and " both" not in arrive


# ------------------------------------------------------------------ the orbs (29 Sep 2026)

def test_the_orbs_exist_only_where_motion_is_welcome():
    js, css = bpnav.JS, bpnav.CSS
    # made by the script, never in the markup: without a script, asked for
    # less motion, with colours forced or without a canvas, the row is as the
    # stylesheet draws it; asked for less motion later, they go
    assert "nav__orbs" not in bpnav.row(BP, "t", "", "", [("a", "a.html", "")])
    assert "if(calm.matches||!nb||matchMedia('(forced-colors: active)').matches)return;" in js
    assert "g=cv.getContext&&cv.getContext('2d');\n  if(!g)return;" in js
    assert "hush();orbs=0;li.removeChild(cv);li.classList.remove('nav__bp--orbs');" in js
    # drawn, not said, and it takes no pointer; it is the <li>'s own box, so
    # it never reaches past the column's last row or makes the column scroll
    assert "cv.className='nav__orbs';cv.setAttribute('aria-hidden','true');" in js
    assert ".nav__orbs{position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none}" in css
    assert ".nav__bp--orbs{position:relative}" in css
    assert "aria-live" not in js and "role=" not in js
    forced = css.split("@media (forced-colors:active){", 1)[1].split("\n}\n", 1)[0]
    assert ".nav__orbs{display:none}" in forced.replace("\n  ", "")


def test_the_orbs_ask_for_frames_only_while_something_moves():
    js = bpnav.JS
    frame = js[js.index("function frame(now){"):js.index("function kick(){")]
    # every frame while the fold or an orb moves, and none at rest: nothing
    # turns once the page is still (ROUND15: at rest, no requestAnimationFrame)
    assert "if(spin||more)raf=requestAnimationFrame(frame);" in frame
    assert "setTimeout" not in frame and "later=" not in js and "QUIET" not in js
    assert frame.rstrip().endswith("else t0=0;\n}")
    tick = js[js.index("function tick(dt,now){"):js.index("function draw(){")]
    assert tick.rstrip().endswith("return busy;\n}")
    # none while the column is off screen, the tab hidden or the page put away
    assert "else{ovis=r.isIntersecting;if(!ovis)hush();else if(orbs)kick()}" in js
    assert "io.observe(row);if(orbs)io.observe(li);" in js
    assert "addEventListener('pagehide',hush);" in js
    # layout is read at a toggle, a resize or the fonts' arrival, never per frame
    assert "offset" not in tick.replace("if(moved)place();", "")
    assert "offset" not in js[js.index("function draw(){"):js.index("/* start: the orbs")]
    # crisp at the device's ratio, 2 at most, as every canvas on the site
    assert "dpr=Math.min(2,window.devicePixelRatio||1);" in js


def test_an_orb_is_a_turning_sphere_of_dots_that_settles_into_its_bead():
    js = bpnav.JS
    # 48 dots laid evenly on a sphere (a Fibonacci lattice: the golden angle)
    assert "N=48," in js and "t=i*2.399963;" in js
    # its life on a critically damped spring, integrated exactly; it turns as
    # the cube of its excitation, so it spins up and down to a stop
    assert "E[j]=ET[j]+(d+c*dt)*x;EV[j]=(EV[j]-w*c*dt)*x;" in js
    assert "AN[j]+=dt*SPIN*E[j]*E[j]*E[j];" in js
    # it grows out of the 7px bead's ring (radius 3) and settles back into it,
    # fading as it goes; the bead gives way to it by its colours (.o) and
    # comes back
    assert "r=warm?3.5+3*s:3+3.5*s" in js
    assert "g.globalAlpha=al*s*(warm?.45+.55*t:.14+.86*t*t);" in js
    assert "if(OC[j]&&ET[j]!==1&&E[j]<.35)bead(j,0);" in js
    css = bpnav.CSS
    assert ".nav__map .b.o{border-color:transparent;background-color:transparent}" in css
    assert (".nav .nav__bp.nav__bp--orbs .nav__sub a.o:not([aria-current])::before{\n"
            "  border-color:transparent;background-color:transparent}") in css
    # "you are here" keeps its warm bead as a core: it never takes .o, and it
    # settles as every orb does, so nothing turns once the page is still
    assert "if(!HERE[j])bead(j,1);" in js
    assert "if(ET[j]===1&&EH[j]&&now>=EH[j]&&!PIN[j]){ET[j]=0;EW[j]=REST;EH[j]=0}" in js
    assert ("HERE[i]=i<nb?on&&dots[i].classList.contains('h'):items[i-nb].hasAttribute('aria-current');"
            in js)


def test_the_thought_tells_the_rows_order():
    js = bpnav.JS
    # along the line from the first bead to the last, waking each as it
    # reaches its ring, then on into the chevron
    assert "QX.push(x0,x1);QY.push(BY,BY);QD.push(0,x1-x0);QA=x1-x0;" in js
    assert "for(k=0;k<nb;k++)if(!WOKE[k]&&s>=BX[k]-BX[0]-3){WOKE[k]=1;wake(k,now)}" in js
    # the list open, down the branch through each topic; the list opening, at
    # the tip of the branch, each topic waking as the edge uncovers it
    assert "for(k=0;k<ni;k++)if(!WOKE[nb+k]&&PY>=LY+IY[k]-3){WOKE[nb+k]=1;wake(nb+k,now)}" in js
    assert "if(goal)for(k=0;k<ni;k++)if(!WOKE[nb+k]&&y>=IY[k]){WOKE[nb+k]=1;wake(nb+k,now)}" in js
    # once a page view by itself, when the row is first on screen and the tab
    # is seen; again on the pointer's rest or a key, not within 2.5s
    assert "if(document.hidden){document.addEventListener('visibilitychange',intro);return}" in js
    assert "if(!first&&now-lastPlay<1600)return 0;" in js
    assert "if(armed&&!goal){hovered=Date.now();choose(true,1)}else play(0)},600);" in js
    assert "e.target.matches(':focus-visible'))play(0);" in js
    # a topic under a key takes the lit path and its orb at once
    assert "if(mode===1){LT=LG;LV=0;LA=1;E[j]=ET[j]=1;EV[j]=0;EH[j]=0;bead(j,1)}" in js


def _settle(w, left=.002):
    """Seconds a critically damped spring of rate w takes to come within
    `left` of its goal, from rest a whole unit away."""
    t = 0.0
    while (1 + w * t) * math.exp(-w * t) > left:
        t += .001
    return t


def test_the_row_reads_in_about_a_second_on_the_sites_springs():
    js = bpnav.JS
    # 29 Sep 2026: the client asked for it faster. Its springs are the site's
    # tokens (Motion's spring() of the token's visual duration, bounce 0, is
    # critically damped at w = 2 pi / 1.2v), written into the script
    from parts.springs import SPRINGS
    rates = {k: round(2 * math.pi / (1.2 * v / 1000), 2) for k, (v, _, _) in SPRINGS.items()}
    assert bpnav.SPRING_RATES == rates
    assert "var SPR={" + ",".join(f"{k}:{v}" for k, v in rates.items()) + "};" in js
    assert "OUT=SPR.mid,BACK=SPR.fast," in js
    assert "WAKE=SPR.fast,REST=SPR.draw,HOLD=120," in js and "AIM=SPR.fast,PRESS=SPR.quick;" in js
    ta, tb = int(re.search(r"TA=(\d+)", js).group(1)), int(re.search(r"TB=(\d+)", js).group(1))
    hold = int(re.search(r"HOLD=(\d+)", js).group(1))
    # the thought runs the line and lands in the chevron within a second...
    assert ta + tb + 140 <= 1000
    # ...and the fifth bead, which it wakes as it leaves the line, has
    # thought and settled back into its ring by about 1.3s: where it all took
    # 2.5s, it now reads in about 1.2 to 1.5
    assert ta + hold + 1000 * _settle(rates["draw"]) <= 1300
    # it starts 0.22s into a page, 0.56s into the first of a visit, behind the
    # column's arrival
    assert "Math.max(120,(H.hasAttribute('data-id-in')?560:220)-performance.now())" in js


# ------------------------------------------------------------------ the orbs, in a browser

def _chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


CHROMIUM = _chromium()

# what the page does, as it does it: which beads and topics turn into orbs
# (.o) and back, when the call begins, and how many frames are asked for
WATCH = """
window.__log = []; window.__raf = 0;
const raf = window.requestAnimationFrame.bind(window);
window.requestAnimationFrame = cb => { window.__raf++; return raf(cb); };
new MutationObserver(ms => { for (const m of ms) {
  const e = m.target, t = Math.round(performance.now());
  if (!e.matches) continue;
  if (e.matches('.nav__map .b'))
    window.__log.push([t, 'b' + [...e.parentNode.children].indexOf(e), e.classList.contains('o')]);
  else if (e.matches('.nav__sub a'))
    window.__log.push([t, 'i' + [...e.closest('ul').querySelectorAll('a')].indexOf(e), e.classList.contains('o')]);
  else if (e.matches('.nav__bp') && e.classList.contains('nav__bp--call'))
    window.__log.push([t, 'call', true]);
}}).observe(document, {subtree: true, attributes: true, attributeFilter: ['class']});
"""


# his portrait's stand-in: a grey square, drawn at the column's 108px
PIC = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='108' height='108'%3E"
       "%3Crect width='108' height='108' fill='gray'/%3E%3C/svg%3E")


def _page(page, section="", portrait=False):
    """The column as the build writes it, on a page of its own: the part's
    stylesheet over the tokens, its script, and head_js() before the paint;
    with `portrait`, the identity block over it, as build.py's shell() writes
    it."""
    old = build.BPNAV
    build.BPNAV = bpnav
    try:
        nav = build.nav_html(page, "", section)
    finally:
        build.BPNAV = old
    css = (theme.CSS + bpnav.CSS + "body{margin:0;background:var(--page)}"
           ".side{width:240px;background:var(--nav)}.nav{margin:0;padding:0;list-style:none}"
           ".id{display:block;color:inherit;text-decoration:none;background:var(--page)}"
           ".id b,.id span{display:block}")
    ident = (f'<a class="id" href="index.html" aria-label="Korkut Kaynardag, home">'
             f'<img class="id__pic" src="{PIC}" width="108" height="108" alt="Korkut Kaynardag">'
             f'<b>Korkut Kaynardag</b><span class="id__role">PhD, Assistant Professor</span>'
             f'<span class="id__org">Department of Civil Engineering</span></a>') if portrait else ""
    return (f'<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8">'
            f'<script>{bpnav.head_js(page == BP)}</script><style>{css}</style></head><body>'
            f'<nav class="side" aria-label="Site">{ident}<ul class="nav">{nav}</ul></nav>'
            f'<script>(function(){{\n{bpnav.JS}\n}})();</script></body></html>')


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _open(browser, page, seen=True, portrait=False, viewport=(1440, 900), **kw):
    c = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]},
                            device_scale_factor=2, **kw)
    c.add_init_script(WATCH)
    if seen:
        c.add_init_script("try{localStorage.setItem('wad:bp-seen','1')}catch(e){}")
    html = _page(page, portrait=portrait)
    c.route("http://bpnav.test/**", lambda r: r.fulfill(body=html, content_type="text/html")
            if r.request.url.endswith(page) else r.abort())
    pg = c.new_page()
    pg.goto("http://bpnav.test/" + page)
    return c, pg


def _rests(pg, within=6.0):
    """Wait until something has moved, nothing is an orb, and no frame has
    been asked for in 300ms."""
    import time
    end = time.time() + within
    while time.time() < end:
        n = pg.evaluate("window.__raf")
        pg.wait_for_timeout(300)
        if pg.evaluate("""n => window.__raf === n && window.__log.length > 0
                          && !document.querySelector('.nav__bp .o')""", n):
            return
    raise AssertionError("the row did not come to rest")


def _woken(pg, key):
    return [(t, k) for t, k, on in pg.evaluate("window.__log") if on and k.startswith(key)]


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_row_comes_alive_in_its_order_then_rests(browser):
    c, pg = _open(browser, "about.html")
    _rests(pg)
    woken = _woken(pg, "b")
    # each bead once, first to fifth, as the thought reaches it
    assert [k for _, k in woken] == ["b0", "b1", "b2", "b3", "b4"]
    assert [t for t, _ in woken] == sorted(t for t, _ in woken)
    assert _woken(pg, "i") == []                       # the list is closed
    # quick: the fifth bead is back in its ring within about a second of the
    # first one waking (it took 2.5s before 29 Sep 2026)
    log = pg.evaluate("window.__log")
    back = max(t for t, k, on in log if not on and k.startswith("b"))
    assert back - woken[0][0] <= 1100
    # at rest: no frame asked for, the canvas empty, and nothing said
    n = pg.evaluate("window.__raf")
    pg.wait_for_timeout(800)
    assert pg.evaluate("window.__raf") == n
    assert pg.evaluate("""() => { const c = document.querySelector('.nav__orbs');
        return c.getAttribute('aria-hidden') === 'true' && c.width === 480 &&
               c.getContext('2d').getImageData(0, 0, c.width, c.height).data.every(v => v === 0); }""")
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_first_call_begins_as_the_thought_lands(browser):
    c, pg = _open(browser, "about.html", seen=False)
    pg.wait_for_function("document.querySelector('.nav__bp--call')", timeout=6000)
    call = next(t for t, k, _ in pg.evaluate("window.__log") if k == "call")
    assert call > max(t for t, _ in _woken(pg, "b4"))  # after the line's last topic
    assert pg.evaluate("document.documentElement.hasAttribute('data-bp-new')")
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_list_wakes_top_to_bottom_and_a_topic_under_the_pointer(browser):
    c, pg = _open(browser, "about.html")
    _rests(pg)
    pg.evaluate("window.__log = []")
    pg.evaluate("document.querySelector('.nav__x').click()")
    _rests(pg)
    assert [k for _, k in _woken(pg, "i")] == ["i0", "i1", "i2", "i3", "i4"]
    # a topic under the pointer: its orb wakes as the thought arrives down the
    # branch, and stays alive while it is pointed at; away, it settles
    pg.evaluate("window.__log = []")
    pg.hover(".nav__sub li:nth-child(3) a")
    pg.wait_for_function("document.querySelector('.nav__sub li:nth-child(3) a.o')", timeout=2000)
    pg.wait_for_timeout(900)
    assert pg.evaluate("!!document.querySelector('.nav__sub li:nth-child(3) a.o')")
    pg.mouse.move(900, 600)
    _rests(pg)
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_you_are_here_wakes_and_rests_and_so_does_the_big_picture(browser):
    c, pg = _open(browser, "probability-statistics.html")
    _rests(pg)
    # the thought ran down the branch, each topic waking as it passed; the
    # page's own topic keeps its warm core (never .o), and once the page is
    # still, nothing turns: no frame, and an empty canvas
    assert [k for _, k in _woken(pg, "i")] == ["i1", "i2", "i3", "i4"]
    assert pg.evaluate("!document.querySelector('.nav__sub a[aria-current].o')")
    n = pg.evaluate("window.__raf")
    pg.wait_for_timeout(1000)
    assert pg.evaluate("window.__raf") == n
    assert pg.evaluate("""() => { const c = document.querySelector('.nav__orbs');
        return c.getContext('2d').getImageData(0, 0, c.width, c.height).data.every(v => v === 0); }""")
    c.close()
    c, pg = _open(browser, BP)
    _rests(pg)
    n = pg.evaluate("window.__raf")
    pg.wait_for_timeout(800)
    assert pg.evaluate("window.__raf") == n
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_less_motion_or_forced_colours_draw_no_orb(browser):
    for kw in ({"reduced_motion": "reduce"}, {"forced_colors": "active"}):
        c, pg = _open(browser, "about.html", **kw)
        pg.wait_for_timeout(1500)
        assert pg.evaluate("""() => !document.querySelector('.nav__orbs') &&
            !document.querySelector('.nav__bp--orbs') && !document.querySelector('.nav__bp .o')""")
        n = pg.evaluate("window.__raf")
        pg.wait_for_timeout(500)
        assert pg.evaluate("window.__raf") == n
        c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_a_finger_on_a_topic_shows_before_the_page_goes(browser):
    # a phone's press (touch, no hover): within 150ms the topic is pressed
    # (.p), its orb awake (.o) and the thought on its way down the branch
    c, pg = _open(browser, BP, viewport=(390, 844), has_touch=True, is_mobile=True)
    _rests(pg)
    a = pg.locator(".nav__sub li:nth-child(3) a")
    box = a.bounding_box()
    cdp = c.new_cdp_session(pg)
    pg.evaluate("window.__raf = 0")
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [
        {"x": box["x"] + 60, "y": box["y"] + box["height"] / 2}]})
    pg.wait_for_timeout(150)
    assert pg.evaluate("""() => { const a = document.querySelectorAll('.nav__sub a')[2];
        return a.classList.contains('p') && a.classList.contains('o'); }""")
    assert pg.evaluate("window.__raf") > 0
    # a press that turns into a scroll lets go, and the row rests again
    cdp.send("Input.dispatchTouchEvent", {"type": "touchCancel", "touchPoints": []})
    pg.wait_for_timeout(100)
    assert pg.evaluate("!document.querySelector('.nav__sub a.p')")
    _rests(pg)
    c.close()


# ------------------------------------------------------------------ his portrait's halo (29 Sep 2026)

def test_the_halo_is_the_orb_round_his_portrait_and_never_over_his_face():
    js = bpnav.JS
    halo = js[js.index("/* THE HALO"):js.index("/* The Big Picture row (parts/bpnav.py).")]
    # only where motion is welcome and colours are not forced, and with a canvas
    assert "if(calm.matches||matchMedia('(forced-colors: active)').matches)return;" in halo
    assert "o.g=o.cv.getContext&&o.cv.getContext('2d');\n      if(!o.g){o.cv=null;return 0}" in halo
    # the orb's own lattice and tilt: the site's one orb
    assert "t=i*2.399963;" in halo and "py=SY[i]*.93-pz*.37;z=SY[i]*.37+pz*.93;" in halo
    # a dot is drawn only from 1px out of the photo's edge, fading in over the
    # next 2.5px, so no dot ever lies over his face
    assert "k=(r-R-1)/2.5;if(k<=0)continue;if(k>1)k=1;" in halo
    # it gathers into the ring 3.5px out from the column's photo (the pale
    # track, parts/theme.py), 2.5px out from the bar's, and fades there
    assert "col=halo(document.querySelector('.id__pic'),3.5),bar=halo(document.querySelector('.bar__pic'),2.5)" in halo
    assert "r=RR+(RS*q-RR)*s;" in halo and "f=o.amp*Math.min(1,e/.3)" in halo
    # drawn, not said; no pointer; crisp at the device's ratio, 2 at most
    assert "o.cv.className='id__halo';\n      o.cv.setAttribute('aria-hidden','true');" in halo
    assert "dpr=Math.min(2,window.devicePixelRatio||1)" in halo
    assert ".id__halo{position:absolute;pointer-events:none}" in theme.CSS
    forced = theme.CSS.split(".id__halo{position:absolute;pointer-events:none}", 1)[1]
    assert forced.startswith("\n@media (forced-colors:active){.id__halo{display:none}}")
    # on its springs, the site's; frames only while it moves, and at rest the
    # canvas is gone, so it costs nothing
    assert "o.w=SPR.slow;o.hold=now+420;o.back=SPR.slow;" in halo
    assert "o.goal=.55;o.w=SPR.fast;o.hold=now+90;o.back=SPR.mid;o.amp=.62;" in halo
    assert "if(busy)raf=requestAnimationFrame(turn);else t0=0;" in halo
    assert "if(o.cv&&o.cv.parentNode)o.cv.parentNode.removeChild(o.cv);" in halo
    assert "if(document.hidden){stop(o);continue}" in halo
    assert "if(all[j].on&&all[j].link===es[i].target)stop(all[j]);" in halo   # off screen
    assert "seen.observe(o.link)" in halo
    # once a visit as the page opens: with the column's arrival on a desktop,
    # the phone bar's own mark on a phone; again under the pointer or a key,
    # not within 1.6s of the last time
    assert "if(H.hasAttribute('data-id-in'))" in halo
    assert "f=sessionStorage.getItem('wad:id-bar');if(!f)sessionStorage.setItem('wad:id-bar','1')" in halo
    assert "o.link.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse'&&fine.matches)play(o,1)});" in halo
    assert "o.link.addEventListener('focus',function(){if(o.link.matches(':focus-visible'))play(o,1)});" in halo
    assert "(again&&now-o.last<1600)" in halo


def _halo_frames(pg, until_ms):
    """Sample the halo's canvas until it has gone: [(ms, drawn, over the photo)],
    counting pixels drawn anywhere and within the photo's disc."""
    import time
    got, t0 = [], time.time()
    while (time.time() - t0) * 1000 < until_ms:
        v = pg.evaluate("""() => {
            const c = document.querySelector('.id__halo'), p = document.querySelector('.id__pic');
            if (!c) return null;
            const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data,
                  s = c.width / parseFloat(c.style.width), R = p.offsetWidth / 2 * s, C = c.width / 2;
            let all = 0, over = 0;
            for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
              if (!d[(y * c.width + x) * 4 + 3]) continue;
              all++; if ((x + .5 - C) ** 2 + (y + .5 - C) ** 2 < R * R) over++;
            }
            return [all, over]; }""")
        got.append((round((time.time() - t0) * 1000), v))
        if v is None and len(got) > 3 and any(g for _, g in got):
            break
        pg.wait_for_timeout(40)
    return got


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_halo_gathers_round_the_portrait_then_is_gone(browser):
    c, pg = _open(browser, "about.html", portrait=True)
    got = _halo_frames(pg, 3000)
    drawn = [v for _, v in got if v]
    # it came, it was drawn, never a pixel over his face, and it went
    assert drawn and max(a for a, _ in drawn) > 200
    assert all(over == 0 for _, over in drawn)
    assert got[-1][1] is None
    # at rest, the row's own motion over too: no canvas and no frame
    _rests(pg)
    n = pg.evaluate("window.__raf")
    pg.wait_for_timeout(600)
    assert pg.evaluate("window.__raf") == n and not pg.query_selector(".id__halo")
    # the pointer on the block: it breathes again, fainter, and goes
    pg.mouse.move(120, 80)
    got = _halo_frames(pg, 2500)
    assert [v for _, v in got if v] and all(v[1] == 0 for _, v in got if v)
    assert got[-1][1] is None
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_less_motion_or_forced_colours_draw_no_halo(browser):
    for kw in ({"reduced_motion": "reduce"}, {"forced_colors": "active"}):
        c, pg = _open(browser, "about.html", portrait=True, **kw)
        pg.wait_for_timeout(1200)
        pg.mouse.move(120, 80)
        pg.wait_for_timeout(600)
        assert not pg.query_selector(".id__halo")
        c.close()
