"""The contents beside a document on a laptop (the professor's notes, 5 Oct
2026: "a bar on the side that follows the sections"): the margin list, set
smaller, from 1280px with the site's column open and from 1100px with it
folded, where the margin had only the Contents button before."""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

from parts import docs  # noqa: E402


def _block(css, head):
    i = css.index(head) + len(head)
    depth, j = 1, i
    while depth:
        depth += {"{": 1, "}": -1}.get(css[j], 0)
        j += 1
    return css[i:j - 1]


def test_the_margin_holds_the_list_set_smaller_on_a_laptop():
    css = docs.CSS
    wide = _block(css, "@media (min-width:1424px){")
    open_ = _block(css, "@media (min-width:1280px) and (max-width:1423px){")
    folded = _block(css, "@media (min-width:1100px) and (max-width:1239px){")
    # the same list in the margin, as at 1424px: laid in the flow, the card in
    # the text set aside, the list open unless the reader shut it
    for block, p in ((open_, ':root:not([data-side="closed"])'), (folded, '[data-side="closed"]')):
        assert f"{p} .docpage .tocpanel{{position:relative;" in block
        assert f"{p}[data-toc] .docpage.has-toc .toc--body," in block
        assert f'{p}[data-toc="closed"] .docpage .tocpanel{{visibility:hidden;' in block
        # smaller: 13.5px titles in a 148 to 211px list beside the text, two
        # lines a title but the one being read
        assert f"{p}[data-toc] .docpage.has-toc>.tocdock{{width:calc(100% - 20px);margin:-10px 12px 0 0}}" in block
        assert re.search(re.escape(p) + r" \.docpage \.toc--rail a\{padding:0 4px 0 [^;]+;\s*"
                         r"border-block:5px solid transparent;font-size:13\.5px;", block)
        assert "-webkit-line-clamp:2" in block
        assert f"{p} .docpage .toc--rail a[aria-current]{{-webkit-line-clamp:none}}" in block
    # the full size stays from 1424px (open) and 1240px (folded)
    assert ".docpage .toc--rail a{color:var(--muted);font-size:15px}" in wide
    # the button waits for the card to leave the screen only below the margin list
    assert "@media (width > 1000px) and (max-width:1279px){" in css
    assert "@media (width > 1000px) and (max-width:1099px){" in css
    assert "@media (width > 1000px) and (max-width:1423px)" not in css
    assert "@media (width > 1000px) and (max-width:1239px)" not in css


def test_the_margin_widths_hold_the_list():
    """The margin left of a 672px column, with 16px of padding each side of
    the page, at each edge of the ranges: the list (100% - 20px of it) is
    148px at least, where a 13.5px title takes two lines."""
    for width, side in ((1280, 240), (1423, 240), (1100, 56), (1239, 56)):
        margin = (width - side - 32 - 672) / 2
        assert 148 <= margin - 20 <= 220, (width, side, margin)
