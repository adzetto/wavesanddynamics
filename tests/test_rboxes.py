"""parts/rboxes.py: the four documents on My Research Areas.

What the cards promise: his labels verbatim and in his order, one link per
card with the site's arrow inside it and the Word original as a link of its
own beside it (never nested), the words each card marks in his text found
there as he wrote them, and the motion rules the site binds every part to
(DESIGN_BRIEF.md section 4, tools/ROUND10.md): tokens only, hover inside
(hover:hover), focus outside it, travel only without a reduced-motion
request, keyframes named for the part.
"""

import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import rboxes  # noqa: E402

LABELS = [
    "Structural Health Monitoring / Non-destructive Testing (Short)",
    "Extended Structural Health Monitoring / Non-destructive Testing document",
    "Sound Wave Tracking",
    "Extensive ppt regarding my MSc and PhD Research",
]


def text(fragment):
    """Visible text of a fragment: tags dropped, entities read, the word
    joiner and the no-break spaces the labels carry turned back."""
    t = html.unescape(re.sub(r"<[^>]+>", "", fragment))
    return re.sub(r"\s+", " ", t.replace("⁠", "").replace(" ", " ")).strip()


def cards(markup):
    return re.findall(r'<li class="rboxes__doc[^"]*".*?</li>', markup, re.S)


def test_four_cards_with_his_labels_in_his_order():
    out = rboxes.render(docs_ready=True)
    labels = [text(re.search(r'<h3 class="rboxes__title">(.*?)</h3>', c, re.S).group(1))
              for c in cards(out)]
    assert labels == LABELS
    assert out.count('<h2 id="rboxes-h">Research documents</h2>') == 1
    assert out.count("<h2") == 1


def test_each_card_is_one_link_with_the_arrow_and_the_word_line_beside_it():
    out = rboxes.render(docs_ready=True)
    hrefs = []
    for c in cards(out):
        link = re.search(r'<a class="rboxes__link" href="([^"]+)">(.*?)</a>', c, re.S)
        hrefs.append(link.group(1))
        assert 'class="rboxes__arrow"' in link.group(2)     # the arrow is part of the link
        assert link.group(2).count("<a") == 0               # nothing nested inside it
        assert c.count("<a ") == (2 if "doc/" in link.group(1) else 1)
    assert hrefs == ["doc/brochure-shm-and-ndt-2-pages.html", "doc/understanding-shm-and-ndt.html",
                     "doc/sound-detection-and-tracking.html", "presentation.html"]


def test_word_lines_keep_his_file_names_and_the_measured_sizes():
    out = rboxes.render(docs_ready=True,
                        sizes={"understanding-shm-and-ndt": 954816},
                        hrefs={"sound-detection-and-tracking": "https://example.org/s.docx"})
    lines = re.findall(r'<a class="rboxes__dl" href="([^"]+)" download="([^"]+)" '
                       r'aria-label="([^"]+)">', out)
    assert [html.unescape(d) for _, d, _ in lines] == [
        "Brochure - SHM and NDT - 2 pages.docx", "Understanding_SHM_and_NDT.docx",
        "Sound Detection and Tracking.docx"]
    assert [h for h, _, _ in lines] == ["doc/brochure-shm-and-ndt-2-pages.docx",
                                        "doc/understanding-shm-and-ndt.docx",
                                        "https://example.org/s.docx"]
    # the accessible name starts with the visible words (WCAG 2.5.3)
    assert html.unescape(lines[1][2]) == "Download Word, 0.95 MB: " + LABELS[1]
    assert html.unescape(lines[0][2]).startswith("Download Word, 0.11 MB: ")
    assert "177 slides, in the browser" in out


def test_without_the_word_files_the_lines_say_so():
    out = rboxes.render()
    assert 'class="rboxes__dl" href' not in out and "download=" not in out
    assert out.count("Word file, coming soon") == 3


def test_the_marked_words_are_his_as_he_wrote_them():
    # the relation to his text holds only while each phrase stands in it
    his = re.sub(r"\s+", " ", text(build.PROF_RESEARCH))
    refs = [html.unescape(r) for r in re.findall(r'data-ref="([^"]+)"',
                                                 rboxes.render(docs_ready=True))]
    assert len(refs) == 4
    for ref in refs:
        assert ref in his, ref


def test_not_the_item_class_the_theme_reveal_picks_up():
    # theme.py's reveal selects .rboxes__item; the cards arrive on their own
    assert "rboxes__item" not in rboxes.render(docs_ready=True)
    assert "rboxes__item" not in rboxes.CSS


def test_icons_stay_inline_small_and_in_the_family():
    for name, svg in rboxes._ICONS.items():
        assert len(svg.encode()) <= 800, name
        assert 'viewBox="0 0 24 24"' in svg and 'aria-hidden="true"' in svg
        assert 'stroke-width=".75"' in svg        # the plate class of the stroke ladder
    # studio_build.py reads these keys
    for d in rboxes._DOCS:
        assert {"slug", "title", "icon", "mb"} <= set(d)


def rules(css):
    """(selector, declarations, enclosing @-rules) for every rule."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out, stack, head = [], [], ""
    i = 0
    while i < len(css):
        ch = css[i]
        if ch == "{":
            if head.strip().startswith("@"):
                stack.append(head.strip())
            else:
                j = css.index("}", i)
                out.append((head.strip(), css[i + 1:j], tuple(stack)))
                i = j
            head = ""
        elif ch == "}":
            if stack:
                stack.pop()
            head = ""
        else:
            head += ch
        i += 1
    return out


def test_the_site_motion_rules():
    css = rboxes.CSS
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)           # colours from tokens only
    assert "box-shadow" not in css
    found = rules(css)
    assert len(found) > 60
    for sel, body, at in found:
        if any(a.startswith("@keyframes") for a in at):
            continue                     # run only from the rules checked here
        calm = any("prefers-reduced-motion:no-preference" in a for a in at)
        if ":hover" in sel:
            assert any("hover:hover" in a for a in at), sel
            assert "translateY" not in body, sel
        if ":focus-visible" in sel:
            assert not any("hover" in a for a in at), sel
        if re.search(r"(?<![-\w])animation:(?!none)", body):
            assert calm, sel
        # travel only where motion is welcome; a folded wash (scaleX(0)) is a
        # resting state, and reduced motion lays it flat
        for value in re.findall(r"(?<![-\w])transform:([^;}]+)", body):
            assert calm or value.strip() in ("none", "scaleX(0)"), (sel, value)
    for name in re.findall(r"@keyframes\s+([\w-]+)", css):
        assert name.startswith("rboxes-")
    for token in re.findall(r"var\(--(spring-[a-z]+)\)", css):
        assert token in {"spring-quick", "spring-fast", "spring-mid", "spring-draw", "spring-slow"}


def test_no_dashes_and_a_small_script():
    out = rboxes.render(docs_ready=True)
    for s in (out, rboxes.CSS, rboxes.JS):
        assert "—" not in s and " – " not in s
    assert "IntersectionObserver(" not in rboxes.JS         # parts/masthead.py says why
    assert "CSS.highlights" in rboxes.JS and "rboxes-ref" in rboxes.CSS
    code = [ln for ln in re.sub(r"/\*.*?\*/", "", rboxes.JS, flags=re.S).splitlines() if ln.strip()]
    assert len(code) <= 40
