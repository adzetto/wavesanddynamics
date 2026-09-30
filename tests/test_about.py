"""The About page: parts/about.py and parts/timeline.py.

On 27 Sep 2026 the client asked for motion design on the About page's parts
too, at an advanced motion designer's level and still a professor's page.
These hold what round 10 built for it, and what earlier rounds settled that
it must not break: his words as he wrote them, the page's order, the Career
route drawn by one pen that dwells in each stop for as long as he stayed
there, the figures that settle, and the site's rules for motion (travel on
the springs, every entrance only where motion is welcome and gone once it
has played, hover only under a pointer that can hover, a key answered at
once, never a lift, a shadow or a new hue under the pointer).
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import about, timeline  # noqa: E402

PAGE = about.render_page(build.PROF_ABOUT)
CAREER = timeline.render()
CSS = about.CSS + timeline.CSS


def rules(css):
    """(the @-rules around it, selector, declarations) for every style rule."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []

    def walk(s, chain):
        i = 0
        while True:
            j = s.find("{", i)
            if j < 0:
                return
            depth, k = 1, j + 1
            while depth:
                depth += {"{": 1, "}": -1}.get(s[k], 0)
                k += 1
            head, body = " ".join(s[i:j].split()), s[j + 1:k - 1]
            if head.startswith(("@media", "@supports", "@container")):
                walk(body, chain + (head,))
            elif not head.startswith("@keyframes"):
                out.append((chain, head, body))
            i = k

    walk(css, ())
    return out


def animations(body):
    """The comma-separated animations of an animation: declaration."""
    m = re.search(r"(?:^|;)\s*animation:(.*?)(?:;|$)", body, re.S)
    if not m:
        return []
    parts, depth, cur = [], 0, ""
    for ch in m.group(1):
        depth += {"(": 1, ")": -1}.get(ch, 0)
        if ch == "," and not depth:
            parts.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return parts + [cur.strip()]


# ------------------------------------------------------------------ the page

def test_the_page_keeps_its_order_and_his_words():
    marks = ['<h1 class="abt__h1">About Me</h1>', 'class="abt__card"', 'class="abt__act"',
             'class="abt__areas"', 'class="abt__bio"', 'class="career"', 'class="glance"']
    at = [PAGE.index(m) for m in marks]
    assert at == sorted(at)
    # his text goes in as build.py holds it: the bold runs are already his
    assert build.PROF_ABOUT in PAGE
    assert about.embolden(build.PROF_ABOUT) == build.PROF_ABOUT
    assert "—" not in PAGE + CAREER and "&mdash;" not in PAGE + CAREER


def test_embolden_adds_tags_and_nothing_else():
    src = "<p>I served as an Assistant Professor at Izmir Institute of\nTechnology.</p>"
    out = about.embolden(src)
    assert out.count("<strong>") == 2
    assert re.sub(r"</?strong>", "", out) == src


def test_the_profiles_are_his_and_leave_this_site_out():
    links = [{"label": "Google Scholar", "kind": "scholar", "href": "https://scholar.example/k"},
             {"label": "Home", "kind": "web", "href": "https://www.wavesanddata.com/"},
             {"label": "Mail", "kind": "mail", "href": "mailto:someone@example.com"}]
    act = about.render_page("<p>x</p>", links=links, areas=[])
    assert 'href="https://scholar.example/k" rel="me"' in act
    assert "wavesanddata.com" not in act and "mailto:" not in act
    assert 'class="abt__areas"' not in act


def test_each_figure_leads_to_the_cv_section_that_lists_it():
    hrefs = re.findall(r'class="glance__a" href="([^"]+)"', about.render_glance())
    assert hrefs == ["cv.html#journal-publications", "cv.html#patents", "cv.html#awards"]


# ---------------------------------------------------------------- the route

def test_the_route_has_six_stops_and_turns_only_where_the_lane_changes():
    items = re.findall(r'<li class="([^"]+)" style="--yrs:(\d+)">', CAREER)
    assert [int(y) for _, y in items] == [0, 2, 1, 7, 2, 1]
    assert sum("career__item--now" in c for c, _ in items) == 1
    assert "career__item--now" in items[0][0]
    turns = [i for i, (c, _) in enumerate(items) if "career__item--turn" in c]
    lanes = [r[5] for r in timeline.ROLES]
    assert turns == [i for i in range(len(lanes) - 1) if lanes[i] != lanes[i + 1]]
    assert CAREER.count('class="career__rail" aria-hidden="true"') == 6
    assert "Since <time" in CAREER and "</time>&#8211;<time" in CAREER


def test_the_pen_dwells_by_the_year_and_runs_at_an_even_pace():
    js = timeline.JS
    # a stop is laid only in view and every stop above it first, in order,
    # all the heights read before anything is written
    assert "items.slice(k,n+1).map(" in js and "for(var i=0;k<=n;k++,i++)" in js
    # 55ms a year in a stop, 0.6px a millisecond along a stretch, measured
    assert "*55" in js and "getBoundingClientRect().height:0" in js and "w=h[i]/.6" in js
    # the next stop opens when the pen has finished this role
    assert "due=t+f+w" in js
    # hidden only if the list was below the screen when the page opened
    assert "var y0=scrollY" in js and "top+scrollY-y0<innerHeight)return" in js
    assert js.strip().count("\n") < 40              # CONTRACT.md 4: at most 40 lines


def test_every_entrance_is_only_where_motion_is_welcome():
    for chain, sel, body in rules(CSS):
        if re.search(r"\.is-(?:in|out|run)\b", sel) and "animation" in body + sel:
            assert any("prefers-reduced-motion:no-preference" in c for c in chain), sel
        if re.search(r"\.is-out\b", sel):
            assert any(c.startswith("@media screen") for c in chain), sel


def test_an_entrance_leaves_nothing_behind_once_it_has_played():
    once = {"career-open", "career-grow", "career-lamp", "career-wipe",
            "career-bar", "career-tail", "glance-draw", "glance-rise", "glance-focus",
            "glance-fade", "glance-lift"}
    seen = set()
    for _, sel, body in rules(CSS):
        for a in animations(body):
            name = a.split()[0]
            if name in once:
                seen.add(name)
                assert re.search(r"\bbackwards$", a) and "forwards" not in a, (sel, a)
    assert seen == once


def test_what_travels_moves_on_the_sites_springs():
    css = re.sub(r"\s+", " ", CSS)
    assert "career-grow var(--spring-mid)" in css
    assert "career-bar var(--spring-mid)" in css and "career-tail var(--spring-slow)" in css
    assert "glance-rise var(--spring-slow)" in css and "glance-draw var(--spring-slow)" in css
    assert "glance-lift var(--spring-mid)" in css
    assert "transition:opacity 0s,transform var(--spring-mid)}" in css   # the glance fill
    assert "a.glance__a{transition:transform var(--spring-quick)}" in css


# ------------------------------------------------------------------ states

def test_hover_lives_under_a_pointer_and_never_lifts_shadows_or_changes_hue():
    for chain, sel, body in rules(CSS):
        if ":hover" in sel:
            assert any("hover:hover" in c for c in chain), sel
            assert "translateY" not in body and "box-shadow" not in body, sel
        if ":focus-visible" in sel:
            assert not any("hover:hover" in c for c in chain), sel


def test_a_key_gets_the_end_state_at_once():
    focus = {sel: body for _, sel, body in rules(CSS) if ":focus-visible" in sel}
    assert focus["a.glance__a:focus-visible::before"] == "opacity:1;transform:none;transition:none"
    for sel in ("a.glance__a:focus-visible .glance__shaft",
                "a.glance__a:focus-visible .glance__head",
                ".abt__links a:focus-visible .abt__ehead"):
        assert "transition:none" in focus[sel], sel


def test_a_press_gives_only_where_motion_is_welcome():
    for chain, sel, body in rules(CSS):
        if ":active" in sel and "scale(" in body:
            assert any("prefers-reduced-motion:no-preference" in c for c in chain) or \
                sel == ".abt__cv:active", sel
    reduce = [(sel, body) for chain, sel, body in rules(CSS)
              if any("prefers-reduced-motion:reduce" in c for c in chain)]
    assert (".abt__cv:active", "transform:none") in reduce


def test_the_lights_go_under_forced_colours():
    forced = " ".join(sel for chain, sel, _ in rules(CSS)
                      if any("forced-colors:active" in c for c in chain))
    for sel in (".career__node::before", ".glance__a::before", ".abt__bead::before"):
        assert sel in forced, sel


def test_colours_come_from_the_tokens():
    for _, sel, body in rules(CSS):
        for decl in body.split(";"):
            if re.search(r"#[0-9a-fA-F]{3,8}\b", decl):
                assert decl.strip().startswith(("-webkit-mask-image", "mask-image")), (sel, decl)
