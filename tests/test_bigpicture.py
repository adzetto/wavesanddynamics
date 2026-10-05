"""The Big Picture page (parts/documents.py), round 11, 27 Sep 2026.

The professor kept round 10's line and asked for three things: his research
out of the topics, and his sentence under them, "My research involves all of
these."; the five topics in his order, the foundation first and the code
last (Probability & Statistics, Signal Processing & System ID, Machine
Learning, Waves and Dynamics, Python / Programming); and every document and
deck as a card right under its topic, so a reader knows what to open where,
with no shelf repeating them. These hold what it became.

Round 15 (29 Sep 2026) brought the site's thinking orbs here: the nodes
think as a point travels the line, a point carries each bridge and writes
its word, a topic in hand wakes its node and sends points along its
bridges, the cards answer the pointer in reading order, and the brace sends
a point to each of the five. The last tests hold that language.
"""

import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import bpnav, documents  # noqa: E402

PAGE = documents.render_big_picture()
ORDER = ["probability-statistics", "signal-processing", "machine-learning", "waves-dynamics",
         "python-programming"]
NAMES = ["Probability & Statistics", "Signal Processing & System ID", "Machine Learning",
         "Waves and Dynamics", "Python\xa0/ Programming"]
SENTENCE = "My research involves all of these."
ART = {"from-bridges-to-photons": ["photons.webp", 640, 360],
       "presentation.html": ["phd-deck.webp", 640, 360]}


def figure(page=PAGE):
    return page[page.index('<figure class="bpm"'):page.index("</figure>") + len("</figure>")]


def node(sid, page=PAGE):
    at = page.index(f'id="{sid}"')
    start = page.rindex("<section", 0, at)
    return page[start:page.index("</section>", at) + len("</section>")]


def research(page=PAGE):
    start = page.index('<section class="bpr"')
    return page[start:page.index("</section>", start) + len("</section>")]


def cards(part):
    return re.findall(r'<a class="bpc[^"]*" href="([^"]+)"', part)


# ---------------------------------------------------------------- the data

def test_the_categories_are_his_five_in_his_order_with_the_keys_the_column_reads():
    cats = documents.CATEGORIES
    assert [c["id"] for c in cats] == ORDER
    for c in cats:
        assert {"id", "label", "docs", "soon", "line"} <= set(c)
    # the column's list is read from them, so it follows his order, each by
    # its short name
    assert [label for _, label, _ in bpnav.categories()] == [
        "Probability & Statistics", "Signal Processing & System ID", "Machine Learning",
        "Waves and Dynamics", "Python / Programming"]
    assert {"DECKS", "RESEARCH_DECKS", "CATEGORIES", "render_big_picture", "families"} <= set(
        documents.__all__)
    # his research is not a topic
    assert "research" not in [c["id"] for c in cats]


def test_each_topics_line_is_his_from_the_column_of_slide_1():
    sub = {href: s for href, _, s, _ in build.NAV}
    first = {c["id"]: (c["docs"] or c.get("decks") or [c["soon"]])[0] for c in documents.CATEGORIES}
    for c in documents.CATEGORIES:
        page = first[c["id"]]
        href = page if page.endswith(".html") else f"doc/{page}.html"
        assert c["line"] == sub[href], c["id"]


def test_the_decks_are_his_titles_with_the_counts():
    assert documents.DECKS == {
        "probability-statistics.html": ("Probability, statistics and estimation",
                                        "Opens with a big-picture map of the subject.", 74),
        "presentation.html": ("Extensive ppt regarding my MSc and PhD Research",
                              "The master's and PhD work, in more depth.", 177)}
    assert documents.RESEARCH_DECKS == ("presentation.html",)
    # the counts are the decks' own, counted as build.py counts the slides it
    # writes (one sNNN-1600.webp each), and stand where a deck is missing
    for href, folder in (("probability-statistics.html", "deck-probstat"), ("presentation.html", "deck-phd")):
        web = os.path.join(ROOT, "content", folder, "web")
        if os.path.isdir(web):
            n = len([f for f in os.listdir(web) if re.fullmatch(r"s\d{3}[a-z]*-1600\.webp", f)])
            assert documents.DECKS[href][2] == n, href
    assert documents._slides("no-such-deck", 5) == 5


# ---------------------------------------------------------------- the five

def test_the_five_stand_in_his_order_numbered_1_to_5():
    fig = figure()
    got = re.findall(r'<section class="bpm__n bpm__n--(\w\w)[^"]*" id="([\w-]+)"', fig)
    assert [i for _, i in got] == ORDER
    assert [a for a, _ in got] == ["pr", "sp", "ml", "wd", "py"]
    # the node over each is numbered as he numbered them
    assert re.findall(r'<span class="bpm__o" aria-hidden="true">(\d)</span>', fig) == list("12345")
    # each under the column's name for it, and his line
    names = re.findall(r'<h2 class="bpm__h" id="bpm-[\w-]+">([^<]+)</h2>', fig)
    assert [html.unescape(n) for n in names] == NAMES
    assert "All vibrations are waves" in node("waves-dynamics")
    assert "Stochastic Process, Estimation" in node("probability-statistics")
    # the home page's links land on them
    with open(build.__file__, encoding="utf-8") as fh:
        linked = set(re.findall(r'href="big-picture\.html#([\w-]+)"', fh.read()))
    assert linked == {"waves-dynamics", "signal-processing", "machine-learning", "python-programming"}
    for sid in linked:
        assert f'id="{sid}"' in fig


def test_there_is_no_research_column():
    assert 'id="research"' not in PAGE and "From my research" not in PAGE
    assert PAGE.count('class="bpm__n ') == 5


def test_each_card_stands_under_its_topic():
    """Every document and deck is a card right under its topic: its picture,
    his title, what it holds; the whole card opens it."""
    for c in documents.CATEGORIES:
        got = cards(node(c["id"]))
        want = ([c["soon"]] if c.get("soon") else
                [f"doc/{s}.html" for s in c["docs"]] + list(c.get("decks") or ()))
        assert got == want, c["id"]
    wd = node("waves-dynamics")
    assert "Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation" in wd
    assert "20-page read" in wd and "3-page read" in wd
    assert "74 slides" in node("probability-statistics") and "44-page read" in node("machine-learning")
    py = node("python-programming")
    assert "bpc--soon" in py and "In preparation" in py and "Communication" not in PAGE
    assert not any("#" in h for h in cards(PAGE))      # never a section of a document (his rule)


def test_no_document_is_listed_twice_and_the_shelf_is_gone():
    hrefs = cards(PAGE)
    assert len(hrefs) == len(set(hrefs))
    assert "All documents and decks" not in PAGE and "bps" not in PAGE and "bps__" not in documents.CSS
    docs = [f"doc/{s}.html" for c in documents.CATEGORIES for s in c["docs"]]
    docs += [f"doc/{s}.html" for s in documents.RESEARCH]
    assert sorted(hrefs) == sorted(docs + list(documents.DECKS) + ["python-programming.html"])


def test_the_titles_are_his_whole():
    page = documents.render_big_picture(build.DOCS)
    for s, (title, *_) in build.DOCS.items():
        if f"doc/{s}.html" in cards(page):
            assert html.escape(title, quote=False).replace(" (", "&nbsp;(").replace(
                "Non-destructive", '<span class="bpc__nb">Non-destructive</span>') in page, s
    for title, _, _ in documents.DECKS.values():
        assert title in PAGE


# ---------------------------------------------------------------- his research

def test_his_sentence_stands_once_under_a_brace_over_all_five():
    assert PAGE.count(SENTENCE) == 1
    part = research()
    assert f'<h2 class="bpr__h" id="bpr-h">{SENTENCE}</h2>' in part
    assert part.index('class="bpr__brace"') < part.index(SENTENCE)
    # the brace comes after the five, inside the figure, and spans its width
    fig = figure()
    assert fig.index('<section class="bpr"') > fig.index('id="python-programming"')
    css = documents.CSS
    assert ".bpr__brace{position:relative;display:flex;" in css and ".bpr__brace .bpr__run{flex:1 1 0;" in css


def test_his_research_documents_stay_right_there_with_the_way_to_his_research_page():
    part = research()
    assert cards(part) == [f"doc/{s}.html" for s in documents.RESEARCH] + ["presentation.html"]
    assert "177 slides" in part and "11-page read" in part
    assert '<a class="bpr__a" href="research.html">My Research Areas' in part


# ---------------------------------------------------------------- the line and its arcs

def test_the_big_picture_has_no_cross_topic_bridges():
    fig = figure()
    got = json.loads(html.unescape(re.search(r'data-bridges="([^"]+)"', fig).group(1)))
    assert got == []
    assert 'class="bp__vh"' not in fig
    assert "Estimation, shared by" not in fig
    assert "Optimization, shared by" not in fig
    assert "Mode Shapes, shared by" not in fig


def test_the_topics_stand_side_by_side_under_the_line():
    """Five columns, one per topic, with a numbered line over their heads and
    their rows are the table's, so the cards start level. Upright below 920px,
    cards upright on a phone."""
    css, js = documents.CSS, documents.JS
    assert "grid-template-columns:repeat(5,minmax(0,1fr))" in css
    # the room over the line is the arcs': with none, only the nodes' air
    assert ("--band:106px" if documents._BRIDGES else "--band:52px") in css
    assert "grid-template-rows:subgrid" in css
    assert "@container bpm (width < 920px)" in css and "@container bpm (width < 560px)" in css
    assert ".wrap.bp{max-width:1240px}" in css
    assert "edge('l','line','line'" in js
    assert 'data-bridges="[]"' in figure()
    assert "Each arc names an idea two topics share." not in figure()


# ---------------------------------------------------------------- the pictures

def test_a_card_shows_its_picture_with_its_size_or_none():
    page = documents.render_big_picture(art=ART)
    assert '<img src="art/photons.webp" width="640" height="360" alt="" loading="lazy"' in page
    assert '<img src="art/phd-deck.webp" width="640" height="360"' in page
    assert page.count("<img") == 2 and PAGE.count("<img") == 0
    # the Photons card sits under Waves and Dynamics, the deck under the brace
    assert "art/photons.webp" in node("waves-dynamics", page)
    assert "art/phd-deck.webp" in research(page)
    # a deck the build did not write is nowhere on the page
    page = documents.render_big_picture(decks={"probability-statistics.html": ("T", "N", 5)})
    assert "presentation.html" not in page and "5 slides" in page


def test_the_pictures_on_disk_are_cut_for_the_cards_box():
    folder = os.path.join(ROOT, "content", "bigpicture")
    with open(os.path.join(folder, "art.json"), encoding="utf-8") as fh:
        art = json.load(fh)
    keys = {s for c in documents.CATEGORIES for s in c["docs"]} | set(documents.RESEARCH) | set(
        documents.DECKS)
    assert set(art) == keys
    from PIL import Image
    for f, w, h in art.values():
        with Image.open(os.path.join(folder, f)) as im:
            assert im.size == (w, h) == (640, 360), f      # the card's 16:9 box, twice over
    # the vibrations guide's is its building's modes now, not the 4:1 strip
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import bp_art
    assert bp_art.PICKS[documents._VW][0] == "content:anim/nf-building.webp"


# ---------------------------------------------------------------- the words and the motion

def test_our_words_are_short_and_dash_free():
    assert '<p class="lede bp__lede">Every document and slide deck on this site, by topic.</p>' in PAGE
    for text in (documents.CSS, documents.JS, PAGE, open(documents.__file__, encoding="utf-8").read()):
        assert not build.DASH.search(text) and not build.SPACED_EN.search(text)


def blocks(css, head):
    """The bodies of the blocks that open with `head` (one level of nesting)."""
    return re.findall(re.escape(head) + r"\{((?:[^{}]|\{[^{}]*\})*)\}", css)


def test_the_page_keeps_to_the_themes_colours_and_motion_rules():
    css, js = documents.CSS, documents.JS
    assert "%%" not in css and "%(" not in css
    assert set(re.findall(r"#[0-9A-Fa-f]{3,6}", css)) <= set()
    # every hover sits in (hover:hover), and none lifts, shadows or changes hue
    hovers = blocks(css, "@media (hover:hover)")
    assert hovers and all(":hover" in h for h in hovers)
    rest = re.sub(r"@media \(hover:hover\)\{(?:[^{}]|\{[^{}]*\})*\}", "", css)
    assert ":hover" not in rest
    assert not any("translateY" in h or "box-shadow" in h for h in hovers)
    # all that moves moves only for a reader who welcomes it: the intro, the
    # waiting brace and its opening
    moving = "".join(blocks(css, "@media (prefers-reduced-motion:no-preference)"))
    for rule in (".bpm.is-intro .bpm__o:not(.is-born){", ".bpr.is-armed .bpr__run{transform:scaleX(0)}",
                 ".bpr.is-draw .bpr__run{animation", ".bpm.is-intro .bpm__e--s{stroke-dasharray:1 2;animation",
                 ".js .bpm:not(.is-ready) :is(.bpm__n,.bpm__edges,.bpm__words){animation"):
        assert rule in moving and css.count(rule) == 1, rule
    # things that travel move on Motion's springs; the lines draw on them too
    assert "clip-path var(--spring-mid)" in css and "bpm-draw var(--spring-slow)" in css
    assert "bpr-run var(--spring-slow)" in css
    # until the script lays the table out its topics and its drawing wait,
    # never longer than 2s
    assert (".js .bpm:not(.is-ready) :is(.bpm__n,.bpm__edges,.bpm__words)"
            "{animation:bpm-hold 2s backwards}") in css
    # the brace waits to open only where a watcher will open it
    assert "if(!br||!window.IntersectionObserver)return;" in js and "classList.add('is-armed')" in js
    # the script: lines measured from the page, laid out again as it resizes,
    # points only for a reader who welcomes motion, their ways sampled from
    # the curves themselves (no reading of the drawing while it moves)
    assert "getBoundingClientRect" in js and "ResizeObserver" in js
    assert "reduce.matches" in js and "function poly(c)" in js and "getPointAtLength" not in js
    assert "zoom" not in js


# ---------------------------------------------------------------- round 15: the orbs

def consts(js):
    """The script's numbers of the form NAME=1.5, by name."""
    return {k: float(v) for k, v in re.findall(r"\b([A-Z][A-Z0-9]*)=(-?\d*\.?\d+)(?=[,;])", js)}


def test_the_animations_keep_to_the_blues_and_inks():
    """The client disliked orange in the animations (ROUND15): the lit
    topic, its rule, its node, its bridges, their words, the points, the
    cards' cue and the marks of the icons that draw on it are the page's
    link blue, and the orbs are its ink. The one warm thing is the messenger
    the professor asked for on 5 Oct 2026 ("Add orange dot or wave moving
    between topics"): its dot, its wave and the ring of the node it rests on."""
    css, js = documents.CSS, documents.JS
    warm = re.findall(r"([^{}]*)\{[^}]*var\(--accent\)", css)
    assert [w.strip() for w in warm] == [".bpm__go-d", ".bpm__go-w", ".bpm__o.is-go:not(.is-on):not(.o)"]
    assert ".bpm__ic .i-accent{stroke:var(--link)}" in css
    for rule in ('.bpm__rail::after{content:"";position:absolute;inset:0;background:var(--link);',
                 ".bpm__o.is-on{background:var(--link);", ".bpm__o.is-near{border-color:var(--link);",
                 ".bpm__w.is-hot{color:var(--link)}", ".bpm__lit{fill:none;stroke:var(--link);",
                 ".bpm__pt-c{fill:var(--link)}", ".bpm__pt-s1{stop-color:var(--link);"):
        assert rule in css, rule
    # the canvas takes its colours from the tokens, never a hex of its own
    assert "getPropertyValue('--ink')" in js and "getPropertyValue('--link')" in js
    assert not re.findall(r"#[0-9A-Fa-f]{3,6}\b", js.replace("'url(#'", ""))


def test_the_nodes_are_the_sites_orbs():
    """Each node's orb is the column's (parts/bpnav.py): dots on a
    Fibonacci sphere, turning faster the more awake, on a critically damped
    spring, drawn on a canvas inside the node under its number, at the
    device's ratio but never past 2."""
    js, css = documents.JS, documents.CSS
    assert "i*2.399963" in js and "1-2*(i+.5)/N" in js          # the Fibonacci lattice
    assert "Math.min(2,window.devicePixelRatio||1)" in js
    assert "cv.className='bpm__orb'" in js and "os[k].appendChild(cv)" in js
    assert ".bpm__orb{position:absolute;left:50%;top:50%;z-index:-1;" in css
    # while it thinks its ring gives way, and its number keeps a halo of paper
    assert ".bpm__o.o{border-color:transparent;background-color:var(--page);" in css
    assert "text-shadow:0 0 2px var(--page)" in css
    c = consts(js)
    assert 60 <= c["N"] <= 128 and c["R0"] < c["R1"] <= 16 and c["OC"] >= 2 * (c["R1"] + 2)


def test_the_arrival_is_quick_and_then_rests():
    """The thought runs the line within its bounds; at rest nothing asks for
    a frame."""
    js = documents.JS
    c = consts(js)
    arcs = re.search(r"Math\.max\((\d+),Math\.min\((\d+),(\d+)\+\.(\d+)\*Pb\.L\)\)", js)
    end = c["DEP"] + c["TL"] * c["ARC"] + int(arcs.group(2))
    assert 1200 <= end <= 1400, end
    # frames only while something moves: the loop asks for the next one only
    # when busy, and requestAnimationFrame is called nowhere else but to
    # start the arrival and to lay the table out again
    assert "if(busy)raf=requestAnimationFrame(frame);else last=0}" in js
    assert "function kick(){if(!raf)raf=requestAnimationFrame(frame)}" in js
    arrival, messenger = js.split("THE MESSENGER", 1)
    assert arrival.count("requestAnimationFrame(") == 4
    # the messenger (5 Oct 2026) moves while its line is in view, and only
    # then: off screen, in a hidden tab, in forced colours or where less
    # motion is asked for it asks for no frame
    assert "if(!seen||document.hidden||reduce.matches||forced.matches){off();t0=0;return}" in messenger
    assert "var was=seen;seen=on.length?1:0;" in messenger
    # nothing moves where it cannot be seen, or once less motion is asked for
    assert "document.addEventListener('visibilitychange',function(){if(document.hidden)hush()});" in js
    assert "addEventListener('pagehide',hush);" in js
    assert "if(!es[0].isIntersecting&&(runs.length||todo.length||intro1))hush()" in js
    assert "reduce.addEventListener('change'" in js
    assert "function live(){return !reduce.matches&&!forced.matches}" in js


def test_the_brace_points_ride_the_sites_slow_spring():
    """The brace opens on --spring-slow, and its points ride the ends of its
    runs on the same stops."""
    from parts.springs import SPRINGS
    settle, easing = SPRINGS["slow"][1], SPRINGS["slow"][2]
    stops = [float(v) for v in re.findall(r"-?\d*\.?\d+", easing.split("(", 1)[1])]
    js = documents.JS
    got = json.loads(re.search(r"SLOW=(\[[^\]]*\])", js).group(1))
    assert got == stops and f"SLOWT={settle};" in js
    assert "bpr-run var(--spring-slow)" in documents.CSS
    # pointing at one of his research documents runs them again, not sooner
    # than 2.5s after the last time
    assert "now-lastB<2500" in js and "again()" in js


def test_a_card_answers_in_reading_order_and_never_moves():
    """The title's words are an inline of their own, whose underline draws
    through its lines; a hairline of blue opens along the picture's foot;
    the arrow springs. No lift, no shadow; a key gets the end state at once,
    and less motion gets it without the travel."""
    css = documents.CSS
    cards = re.findall(r'<a class="bpc[^"]*" href="[^"]+">.*?</a>', PAGE)
    assert cards and all('<span class="bpc__u">' in a for a in cards)
    hover = "".join(blocks(css, "@media (hover:hover)"))
    assert (".bpc:hover .bpc__u{--bpc-u:var(--ink);background-size:100% 1px;"
            "transition:background-size var(--spring-draw)}") in hover
    assert (".bpc:hover .bpc__art::before{opacity:1;transform:none;"
            "transition:transform var(--spring-draw) 40ms}") in hover
    assert '@property --bpc-u{syntax:"<color>";inherits:false;initial-value:transparent}' in css
    assert ".bpc:focus-visible .bpc__u{--bpc-u:var(--ink);background-size:100% 1px;transition:none}" in css
    calm = "".join(blocks(css, "@media (prefers-reduced-motion:reduce)"))
    assert ".bpc__u,.bpc__art::before{transition:none}" in calm
    assert ".bp__arrow .ar-shaft{stroke-dashoffset:0;transition:none}" in calm


def test_forced_colours_and_print_leave_the_plain_drawing():
    css = documents.CSS
    forced = "".join(blocks(css, "@media (forced-colors:active)"))
    assert ".bpm__orb,.bpm__pt,.bpm__lit,.bpr__pts,.bpc__art::before,.bpm__go{display:none}" in forced
    assert "forced=matchMedia('(forced-colors: active)')" in documents.JS
    # its own classes never meet another's: the lit way is not the heading
    assert "mk('path','bpm__h')" not in documents.JS


def test_a_warm_dot_travels_between_the_topics():
    """The professor's notes, 5 Oct 2026: "Add orange dot or wave moving
    between topics in 'Big Picture' section"."""
    js, css = documents.JS, documents.CSS
    block = js[js.index("THE MESSENGER"):]
    # one dot and the wave behind it, in an svg of their own over the line
    assert "sv.setAttribute('class','bpm__go')" in block and "dt.setAttribute('r','4.5')" in block
    assert ".bpm__go{position:absolute;inset:0;z-index:1;" in css
    assert ".bpm__go-d{fill:var(--accent)}" in css and "stroke:var(--accent)" in css
    # from node to node in his order, resting on each, which answers in the warm
    assert "MOVE=1300,STAY=700,FADE=450,K=os.length-1" in block
    assert "os[k].classList.add('is-go')" in block
    assert re.search(r"\.bpm__o\.is-go:not\(\.is-on\):not\(\.o\)\{border-color:var\(--accent\)", css)
    # the wave's height is the dot's speed: none while it rests; its length
    # shortens with the speed, so it never lies on the line as a straight stroke
    assert "A=AMP*rate(u/M[i])/1.5" in block and "if(A>.05)" in block
    assert "var n=Math.min(TAIL,gone)*Math.min(1,A/(.6*AMP))" in block
    # a long hop (the phone's upright spine) keeps the line's pace
    assert "M.push(Math.max(MOVE,L/PACE))" in block and "PACE=.168" in block
    # nothing is read from the layout while it moves (MotionScore's frame
    # thrashing): the nodes are measured once per size, the dot moves by its
    # transform, and its opacity is written only when it changes
    frame = block[block.index("function frame(ts){"):block.index("function go(){")]
    assert "clientWidth" not in frame and "getBoundingClientRect" not in frame
    assert "setAttribute('cx'" not in block and "dt.setAttribute('transform','translate('" in frame
    assert "if(window.ResizeObserver)new ResizeObserver(function(){P=[]}).observe(st);" in block
    assert "function op(v){if(v!==shown){sv.style.opacity=v;shown=v}}" in block
    # waiting, it looks again in 200ms rather than asking for every frame
    assert "raf=-1;setTimeout(function(){raf=0;go()},200);return}" in frame
    # on screen means a node on screen, and the round starts again from the
    # first topic when it comes back into view or back from a hidden tab
    assert "os.forEach(function(o){io.observe(o)})" in block and ".observe(fig)" not in block
    assert "if(seen&&!was){t0=0;go()}" in block
    assert "document.addEventListener('visibilitychange',function(){if(!document.hidden){t0=0;go()}});" in block
    # nothing moves off screen, in a hidden tab, in forced colours or where
    # less motion is asked for, nor while a topic is in hand or the table arrives
    for guard in ("IntersectionObserver", "document.hidden", "reduce.matches", "forced.matches",
                  "fig.hasAttribute('data-focus')", "fig.classList.contains('is-intro')"):
        assert guard in block, guard
    assert ".bpr__pts,.bpc__art::before,.bpm__go{display:none}" in css      # forced colours
    assert ".bpm__edges,.bpm__words,.bpm__o,.bpr__brace,.bpm__go{display:none}" in css  # print
    assert "Math.random" not in block
