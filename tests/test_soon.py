"""The pages in preparation (parts/soon.py), as round 10 left them (27 Sep 2026).

The client asked for these pages to be made excellent, never a generic
"coming soon". Each now says what the topic will hold (his sub-line, or
where he wrote none one sentence of ours), draws the topic's own work one
step short of done with "In preparation" where the next step goes, and
links the pages already written that it draws on. These hold what must not
drift: his label and sub-line as given, one sentence of ours at most, the
state's words readable by everyone, whole-page links only, the way back to
the Big Picture for its own topics alone, and the motion rules the design
brief binds (DESIGN_BRIEF.md 4).
"""

import html
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

from parts import documents, soon  # noqa: E402

ML = "doc/machine-learning-the-complete-picture-and-guide-5.html"
SP = "doc/signal-processing-system-identification-and-optimization.html"
PY_RELATED = [{"href": ML, "title": "Machine Learning"},
              {"href": SP, "title": "Signal Processing, System Identification"}]
COMM_RELATED = [{"href": "blog.html", "title": "Blog"},
                {"href": "research.html", "title": "My Research Areas"}]


def _text(markup):
    """What a reader and a screen reader get: aria-hidden subtrees and tags gone."""
    markup = re.sub(r'<(\w+)[^>]*aria-hidden="true"[^>]*>.*?</\1>', "", markup, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()


def _rules(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    stack, buf, out = [], "", []
    for ch in css:
        if ch == "{":
            stack.append(buf.strip())
            buf = ""
        elif ch == "}":
            if buf.strip() and stack:
                out.append((tuple(stack[:-1]), stack[-1], buf.strip()))
            buf = ""
            stack.pop()
        else:
            buf += ch
    return [r for r in out if not any(a.startswith("@keyframes") for a in r[0])]


def _rows(page):
    return re.findall(r'<a class="soonpg__row" href="([^"]+)">', page)


# ------------------------------------------------------------------ Python / Programming

def test_python_says_what_will_come_in_one_sentence_of_ours():
    page = soon.render("Python / Programming", "", PY_RELATED)
    assert "<h1>Python&nbsp;/ Programming</h1>" in page
    ledes = re.findall(r'<p class="soonpg__sub">(.*?)</p>', page)
    assert ledes == ["Programming for waves and data: the methods of the guides below, in Python."]


def test_python_is_a_session_left_one_line_short():
    page = soon.render("Python / Programming", "", PY_RELATED)
    state = re.search(r'<div class="soonpg__state soonpg__state--py">(.*?)</div>\s*<section',
                      page, re.S).group(1)
    assert state.count('class="soonpg__pr') == 2, "two prompts: a line run, a line waiting"
    assert state.count('class="soonpg__s"') == 50
    # the state is said as well as drawn, and a screen reader hears the words only
    assert _text(state) == "In preparation"
    assert '<span class="soonpg__hash" aria-hidden="true"># </span>In preparation' in state


def test_each_sample_is_the_signal_at_its_instant():
    page = soon.render("Python / Programming", "", PY_RELATED)
    for x, tip in re.findall(r'<path d="M(\d+) 24V([-\d.]+)"/>', page):
        assert math.isclose(24 - float(tip), soon._vib(int(x)), abs_tol=0.006)
    xs = [int(x) for x in re.findall(r'<path d="M(\d+) 24V', page)]
    assert xs == [8 + 11 * k for k in range(50)]


def test_python_links_the_guides_with_their_notes_and_ends_at_its_place_on_the_big_picture():
    page = soon.render("Python / Programming", "", PY_RELATED)
    assert _rows(page) == [ML, SP, "big-picture.html#python-programming"]
    ids = {c["id"] for c in documents.CATEGORIES}
    assert "python-programming" in ids
    assert "Twelve sections, from what machine learning is to how to learn it." in page
    assert '<span class="soonpg__m">44-page read</span>' in page
    assert '<span class="soonpg__m">18-page read</span>' in page
    assert "Every document and slide deck on this site, by topic." in page


# ------------------------------------------------------------------ Communication

def test_communication_keeps_his_sub_line_and_adds_nothing_of_ours():
    page = soon.render("Communication", "Meetings, presentations, reports, papers", COMM_RELATED)
    ledes = re.findall(r'<p class="soonpg__sub">(.*?)</p>', page)
    assert ledes == ["Meetings, presentations, reports, papers"]
    assert "soonpg__state--boxes" in page


def test_communication_holds_his_four_boxes_side_by_side_each_with_its_picture():
    """His notes, 5 Oct 2026: "Inside communication put 4 boxes ... make these
    4 boxes next to each other": paper writing, how to make presentations,
    technical reports writing, talking/updating to your professor, each with
    a picture."""
    page = soon.render("Communication", "Meetings, presentations, reports, papers", COMM_RELATED)
    boxes = re.search(r'<ul class="soonpg__boxes" role="list">(.*?)</ul>', page, re.S).group(1)
    items = re.findall(r'<li class="soonpg__bi" style="--k:(\d)">(.*?)</li>', boxes, re.S)
    assert [k for k, _ in items] == ["0", "1", "2", "3"]
    assert [re.search(r'<h2 class="soonpg__bt">(.*?)</h2>', b).group(1) for _, b in items] == [
        "Paper writing", "How to make presentations", "Technical reports writing",
        "Talking/updating to your professor"]
    for _, b in items:
        assert b.count('<svg class="soonpg__bpic" viewBox="0 0 240 160" aria-hidden="true"') == 1
        assert '<p class="soonpg__bs">In preparation</p>' in b
        assert re.search(r"soonpg__b(?:warm|warmline|now)\b", b)   # a warm mark: the work under way
    # four across where there is room, two, then one on a phone
    css = soon.CSS
    assert ".soonpg__boxes{display:grid;grid-template-columns:repeat(4,minmax(0,1fr))" in css
    assert "@media (max-width:1180px){.soonpg__boxes{grid-template-columns:repeat(2,minmax(0,1fr))}}" in css
    assert "@media (max-width:520px){.soonpg__boxes{grid-template-columns:minmax(0,1fr)}}" in css


def test_his_advice_section_says_under_construction():
    """His notes, 5 Oct 2026: "Make a section called 'Personal Advices on
    Working on a Project' and say under construction"."""
    page = soon.render("Personal Advices on Working on a Project", "",
                       [{"href": "communication.html", "title": "Communication"}])
    assert "<h1>Personal Advices on Working on a Project</h1>" in page
    assert "soonpg__state--plan" in page and "soonpg__sub" not in page
    state = re.search(r'<div class="soonpg__state soonpg__state--plan">(.*?)</div>\s*<section',
                      page, re.S).group(1)
    assert _text(state) == "Under construction"
    assert _rows(page) == ["communication.html"]


def test_communication_is_no_topic_of_the_big_picture_so_it_does_not_lead_there():
    page = soon.render("Communication", "Meetings, presentations, reports, papers", COMM_RELATED)
    assert _rows(page) == ["blog.html", "research.html"]
    assert "Literature reviews, methods and experiments." in page


# ------------------------------------------------------------------ any other page

def test_another_title_gets_the_signal_and_no_sentence_of_ours():
    page = soon.render("Something Else", "", [{"href": "blog.html", "title": "Blog"}])
    assert "soonpg__state--sig" in page and "soonpg__sub" not in page
    assert _rows(page) == ["blog.html"]
    # a caller's own note wins over ours
    page = soon.render("Something Else", "", [{"href": "blog.html", "title": "Blog", "note": "Mine."}])
    assert "Mine." in page and "Literature reviews" not in page


def test_links_open_whole_pages_and_the_hub_is_not_doubled():
    page = soon.render("Python / Programming", "",
                       PY_RELATED + [{"href": "big-picture.html", "title": "Big Picture"}])
    hrefs = _rows(page)
    assert sum(h.split("#")[0] == "big-picture.html" for h in hrefs) == 1
    assert all("#" not in h or h.startswith("big-picture.html#") for h in hrefs)


# ------------------------------------------------------------------ the brief's rules

def test_every_motion_waits_for_a_no_preference_answer():
    rules = _rules(soon.CSS)
    for ats, sel, body in rules:
        if "animation:" in body:
            assert any("prefers-reduced-motion:no-preference" in a for a in ats), sel
    # the cursor blinks three times and stays: nothing loops
    assert "infinite" not in soon.CSS
    assert re.search(r"soonpg-blink 1\.1s steps\(1,end\) \d+ms 3\}", soon.CSS)


def test_hover_lives_inside_hover_hover_and_focus_outside_it():
    for ats, sel, body in _rules(soon.CSS):
        if ":hover" in sel:
            assert any("hover:hover" in a for a in ats), sel
            assert "translateY" not in body and "box-shadow" not in body, sel
        if ":focus-visible" in sel:
            assert not any("hover:hover" in a for a in ats), sel


def test_colours_come_from_tokens_and_names_from_the_part():
    css = re.sub(r"/\*.*?\*/", "", soon.CSS, flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css)
    names = re.findall(r"@keyframes ([\w-]+)", css)
    assert names and all(n.startswith("soonpg-") for n in names)
    for sel in (s for _, s, _ in _rules(soon.CSS)):
        for part in sel.split(","):
            assert ".soonpg" in part, part
    assert soon.JS == ""


def test_no_dash_of_ours():
    for page in (soon.render("Python / Programming", "", PY_RELATED),
                 soon.render("Communication", "Meetings, presentations, reports, papers",
                             COMM_RELATED)):
        assert "\u2014" not in page and " \u2013 " not in page
    assert "\u2014" not in soon.CSS
