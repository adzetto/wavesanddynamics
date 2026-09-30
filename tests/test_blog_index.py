"""The Blog index as boxes (his requests of 26 and 27 Sep 2026): his line
under the heading, one box a post in his order, three to a row on a laptop,
each a single link, and one picture a box: the post's first figure on the
quiet surface or, without one, his opening sentence there."""

import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import blog  # noqa: E402

LEDE = ("The work that never made it into a paper: literature reviews, methods and "
        "experiments from my research, shared here in case they save you some of the "
        "time they took me.")

INDEX = blog.CSS[blog.CSS.index("blog: the index"):blog.CSS.index("blog: a post")]


def post(n, pic=None, lead=None):
    return {"href": f"post/p{n}.html", "title": f"Title {n}", "date": "2022-04-20",
            "shown": "April 20, 2022", "lead": f"Lead {n}." if lead is None else lead,
            "pic": pic}


PIC = {"src": "post/p1/04-fig-speckle.webp", "w": 1326, "h": 762}


def rule(selector):
    """The declarations of the index rule whose selector is exactly `selector`."""
    m = re.search(r"(?:^|[}\s])" + re.escape(selector) + r"\{([^}]*)\}", INDEX)
    assert m, selector
    return m.group(1)


def test_his_line_stands_under_the_heading():
    page = " ".join(build.page_blog("<ul></ul>").split())
    assert f'<p class="lede">{LEDE}</p>' in page
    assert "Shorter pieces" not in page


def test_every_post_is_one_box_in_his_order_and_one_link():
    out = blog.render_index([post(1), post(2, PIC), post(3)])
    assert out.startswith('<ul class="blog__list" role="list">')
    cards = re.findall(r"<li>(.*?)</li>", out)
    assert len(cards) == 3
    for n, card in enumerate(cards, 1):
        assert re.findall(r'href="([^"]+)"', card) == [f"post/p{n}.html"]
        assert f'<h2 class="bcard__title"><a href="post/p{n}.html">Title {n}</a></h2>' in card
        assert '<time class="bcard__date" datetime="2022-04-20">April 20, 2022</time>' in card
        assert 'class="bcard__arrow"' in card


def test_the_title_comes_first_then_the_date_then_the_picture():
    """His title leads for a screen reader too; the picture is drawn above it
    (order:-1) but read last."""
    for card in (blog.render_index([post(1)]), blog.render_index([post(1, PIC)])):
        at = [card.index(s) for s in ('class="bcard__title"', 'class="bcard__date"',
                                      'class="bcard__pic"')]
        assert at == sorted(at)
    assert "order:-1" in rule(".bcard__pic")


def test_a_figure_sits_in_the_frame_at_its_own_size_and_alone():
    card = blog.render_index([post(1, PIC)])
    assert ('<div class="bcard__pic"><span class="bcard__fit">'
            '<img src="post/p1/04-fig-speckle.webp" alt="" width="1326" height="762" '
            'decoding="async"></span></div>') in card
    # one picture a box: a post with a figure does not print its sentence too
    assert "Lead 1." not in card and "bcard__words" not in card


def test_without_a_figure_his_sentence_takes_the_frame_once():
    card = blog.render_index([post(1)])
    assert '<div class="bcard__pic"><p class="bcard__words"><span>Lead 1.</span></p></div>' in card
    assert card.count("Lead 1.") == 1 and "<img" not in card


def test_his_sentence_is_never_cut_short_in_the_markup():
    lead = ("Here, I am presenting the long literature review of methods that can be used in "
            "mitigating the impulsive noise that can be observed in moving laser Doppler "
            "vibrometer (LDV) measurements.")
    assert f"<span>{lead}</span>" in blog.render_index([post(1, lead=lead)])


def test_a_post_with_neither_keeps_an_empty_frame():
    card = blog.render_index([post(1, lead="")])
    assert '<div class="bcard__pic"></div>' in card


def test_the_first_row_loads_at_once_and_the_rest_lazily():
    out = blog.render_index([post(n, PIC) for n in range(1, 6)])
    imgs = re.findall(r"<img [^>]+>", out)
    assert ['loading="lazy"' in i for i in imgs] == [False, False, False, True, True]


def columns(width):
    """How many boxes the grid sets in a list `width` px wide: auto-fill
    tracks of at least the CSS minimum, the gap between them."""
    grid = rule(".blog__list")
    least = int(re.search(r"repeat\(auto-fill,minmax\(min\(100%,(\d+)px\),1fr\)\)", grid).group(1))
    gap = int(re.search(r"(?<![-\w])gap:(\d+)px", grid).group(1))
    return max(1, math.floor((width + gap) / (least + gap)))


def test_three_to_a_row_on_a_laptop_two_on_a_tablet_one_on_a_phone():
    # the list's width: a laptop's column (1280 to 1440 and up), 1100 beside
    # the open column with a classic scrollbar, the phone drawer's 1000,
    # an iPad on its side and upright, a phone
    assert [columns(w) for w in (924, 749, 956)] == [3, 3, 3]
    assert [columns(w) for w in (673, 724)] == [2, 2]
    assert [columns(w) for w in (346, 331, 276)] == [1, 1, 1]
    # never four: at 924px four boxes would be 213px wide
    assert columns(924) < 4


def test_a_post_alone_in_its_row_keeps_one_box_s_width():
    # auto-fill keeps the empty tracks; auto-fit would stretch a lone box
    # across the row
    assert "auto-fill" in rule(".blog__list") and "auto-fit" not in INDEX


def test_every_frame_keeps_one_shape():
    assert "aspect-ratio:2/1" in rule(".bcard__pic")
    assert INDEX.count("aspect-ratio") == 1
    # his figure is fitted whole, never cropped
    assert "object-fit" not in INDEX
    assert "max-width:100%;max-height:100%" in rule(".bcard__fit img")


def test_no_word_is_cut_by_an_ellipsis():
    """Chromium's line-clamp ellipsis cuts a word to make room for itself
    ("impulsi..."): the frame shows whole lines instead."""
    assert "line-clamp" not in INDEX and "ellipsis" not in INDEX
    assert "max-height:round(down,100%,1lh)" in rule(".bcard__words>span")


def test_the_fade_is_shown_only_where_lines_wait():
    """A browser without scroll timelines would run the fade as a plain
    animation and fade every last line, so it waits behind @supports."""
    at = INDEX.index("animation-timeline:scroll(self)")
    assert enclosing(INDEX, at)[0].startswith("@supports (animation-timeline:scroll())")


def test_the_whole_box_is_the_title_s_link():
    """The link's cover lies over the picture as well: without a z-index the
    picture, later in the markup and positioned, took the clicks."""
    cover = rule(".bcard__title a::after")
    assert "position:absolute" in cover and "inset:-1px" in cover and "z-index:1" in cover


def enclosing(css, pos):
    """The block headers (selectors, @media lines) around position `pos`."""
    stack, start = [], 0
    for i, ch in enumerate(css[:pos]):
        if ch == "{":
            stack.append(re.sub(r"/\*.*?\*/", "", css[start:i], flags=re.S).strip())
            start = i + 1
        elif ch == "}":
            stack.pop()
            start = i + 1
        elif ch == ";":
            start = i + 1
    return stack


def test_hover_waits_for_a_fine_pointer_and_motion_for_consent():
    hovers = [m.start() for m in re.finditer(r"(?<!\(hover):hover", INDEX)]
    moves = [m.start() for m in re.finditer(r"transform:(?:scale|translate)", INDEX)]
    assert hovers and moves
    for at in hovers:
        assert "@media (hover:hover) and (pointer:fine)" in enclosing(INDEX, at)[0]
    for at in moves:
        assert "prefers-reduced-motion:no-preference" in enclosing(INDEX, at)[0]


def test_hover_lifts_nothing_shadows_nothing_and_keeps_every_hue():
    """DESIGN_BRIEF section 4: no translateY, no box-shadow change, no hue
    change on hover. A lit box takes a lightness step in its own hues."""
    blocks = re.findall(r"@media \(hover:hover\)[^{]*\{((?:[^{}]*\{[^{}]*\})*)\s*\}", INDEX)
    assert blocks
    for body in blocks:
        assert "translateY" not in body and "box-shadow" not in body
        for token in ("--accent", "--link", "--nav", "--wash"):
            assert token not in body
    assert "translateY" not in INDEX and "box-shadow" not in INDEX


def test_no_em_dash_or_spaced_en_dash_in_the_part():
    src = open(os.path.join(ROOT, "site", "parts", "blog.py"), encoding="utf-8").read()
    assert "—" not in src and " – " not in src
