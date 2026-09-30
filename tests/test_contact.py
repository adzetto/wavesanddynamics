"""The Contact page (parts/contact.py), as round 14 left it (29 Sep 2026).

The professor found round 10's navy card unprofessional. The page is a
register in the lede's measure: Email, Where to find me, Elsewhere, a key in
the sans beside his particulars in the serif, hairlines between. At his word
(29 Sep 2026) Email holds his two public addresses, both first-class: his
institute's and his personal one, each named for what it is, each a link
that writes to him, each with its own copy control. These hold what must not
drift: the two addresses the site may publish and no other, how each is
copied and said, his words and his grouping, nothing moving on its own and
nothing decorative coming back (no slab, no channel, no filled button), and
the rules the design brief binds (DESIGN_BRIEF.md 4): hover inside
(hover:hover), focus outside it, no translateY or shadow on hover, travel
only under a no-preference answer, colours only from tokens.
"""

import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import contact  # noqa: E402

INST = "korkutkaynardag@iyte.edu.tr"
PERSONAL = "korkut.kaynardag@gmail.com"
LINKS = [
    {"label": "LinkedIn", "href": "https://www.linkedin.com/in/someone", "kind": "linkedin"},
    {"label": "Google Scholar", "href": "https://scholar.google.com/citations?user=x",
     "kind": "scholar"},
    {"label": "ResearchGate", "href": "https://www.researchgate.net/profile/x",
     "kind": "researchgate"},
    {"label": "Site", "href": "https://www.wavesanddata.com/", "kind": "website"},
    {"label": "Mail", "href": "mailto:someone@example.com", "kind": "mail"},
]
INFO = {"email": INST, "personal": PERSONAL, "department": "Department of Civil Engineering",
        "institute": "Izmir Institute of Technology", "city": "Izmir", "country": "Turkiye",
        "links": LINKS, "cv_href": "cv.html"}


def _text(markup):
    """What a reader sees: tags gone, entities read, <wbr> nothing."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def _rules(css):
    """Each style rule as (the at-rules around it, its selector, its body)."""
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
    return out


def _rows(page):
    """The register's rows as (heading id, heading, the row's markup)."""
    return re.findall(r'<section class="contact__row" aria-labelledby="([\w-]+)">\s*'
                      r'<h2 class="contact__key" id="\1">([^<]+)</h2>(.*?)</section>', page, re.S)


def _entries(page):
    """The Email row's entries as (kind, the address's markup, the button's markup)."""
    return re.findall(r'<li class="contact__mail">\s*<p class="contact__kind">([^<]+)</p>\s*'
                      r'<p class="contact__addr">(.*?)</p>\s*(<button .*?</button>)\s*</li>',
                      page, re.S)


# ------------------------------------------------------------------ words and the addresses

def test_the_page_is_his_heading_his_lede_and_his_two_addresses():
    page = contact.render(INFO)
    assert page.startswith('<div class="wrap contact">') and "<h1>Contact</h1>" in page
    assert ("Feel free to reach out about research, collaboration, or the educational\n"
            " sections of this site, especially if you are a student or newcomer to these "
            "topics.") in page
    entries = _entries(page)
    assert [(k, _text(a)) for k, a, _ in entries] == [("Institutional", INST),
                                                      ("Personal", PERSONAL)]
    for _, addr, btn in entries:
        mail = _text(addr)
        assert addr.startswith(f'<a href="mailto:{mail}">'), "each one writes to him"
        assert f'data-copy="{mail}"' in btn, "each control copies its own address"
    # no other address anywhere a reader can see
    assert set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", _text(page))) == {INST, PERSONAL}


def test_each_address_is_said_once_and_is_its_own_way_to_write():
    page = contact.render(INFO)
    assert page.count('href="mailto:') == 2
    for mail in (INST, PERSONAL):
        assert _text(page).count(mail) == 1
        assert page.count(f'href="mailto:{mail}"') == 1
    assert "Write an email" not in page


def test_both_are_first_class_named_for_what_they_are_the_institutes_first():
    # the same markup and the same type for both: neither is a footnote
    page = contact.render(dict(INFO, email=PERSONAL, personal=INST))
    assert [k for k, _, _ in _entries(page)] == ["Institutional", "Personal"]
    assert [_text(a) for _, a, _ in _entries(page)] == [INST, PERSONAL]
    kind = re.search(r"\.contact__kind\{([^}]*)\}", contact.CSS).group(1)
    assert "font:600 12px/1.1 var(--sans)" in kind and "text-transform:uppercase" in kind
    assert "color:var(--muted)" in kind
    addr = re.search(r"\.contact__addr\{([^}]*)\}", contact.CSS).group(1)
    assert "font:500 clamp(20px,7.2cqi,28px)/1.2 var(--serif)" in addr
    # his personal address sets the row's width: 13.11em at 7.2cqi is 94% of it
    assert 13.11 * 7.2 < 96


def test_render_takes_both_from_build_contact_info():
    page = contact.render(build.contact_info(None))
    assert [_text(a) for _, a, _ in _entries(page)] == [INST, PERSONAL]
    # and with nothing given, both are still there: his, always
    assert [_text(a) for _, a, _ in _entries(contact.render())] == [INST, PERSONAL]


# ------------------------------------------------------------------ only his two addresses

def test_the_two_public_addresses_are_builds():
    assert contact.PUBLIC_EMAILS == build.PUBLIC_EMAILS == {INST, PERSONAL}
    assert {build.CONTACT["email"], build.CONTACT["personal"]} == contact.PUBLIC_EMAILS


def test_any_other_address_is_refused_for_its_default(capsys):
    for bad in ({"email": "someone@gmail.com"}, {"personal": "someone.else@example.com"},
                {"email": "korkutkaynardag@iyte.edu.tr.evil.com"},
                {"personal": "korkut.kaynardag@gmail.com.cn"}):
        page = contact.render(dict(INFO, **bad))
        assert [_text(a) for _, a, _ in _entries(page)] == [INST, PERSONAL], bad
        assert next(iter(bad.values())) not in page
        assert "refused" in capsys.readouterr().out
    # his own, written another way, is his: read as it is published
    page = contact.render(dict(INFO, email=" KorkutKaynardag@IYTE.edu.tr ",
                               personal="Korkut.Kaynardag@Gmail.com"))
    assert [_text(a) for _, a, _ in _entries(page)] == [INST, PERSONAL]
    assert "refused" not in capsys.readouterr().out
    # the same one twice is said once
    once = contact.render(dict(INFO, personal=INST))
    assert [_text(a) for _, a, _ in _entries(once)] == [INST]


def test_the_page_passes_the_privacy_gate():
    # build.py reads his Gmail only whole; the page never breaks it with <wbr>
    page = contact.render(INFO)
    for text in (page, contact.CSS, contact.JS):
        assert not build.PRIVATE.search(text)
        assert set(build.EMAIL.findall(text)) <= build.PUBLIC_EMAILS
    assert f">{PERSONAL}</a>" in page
    assert "korkutkaynardag@<wbr>iyte.edu.tr" in page, "his institute's still breaks after the @"
    assert "gmail" not in (contact.CSS + contact.JS).lower()


# ------------------------------------------------------------------ the register

def test_the_register_is_his_three_groups_in_the_order_of_need():
    rows = _rows(contact.render(INFO))
    assert [(i, h) for i, h, _ in rows] == [("contact-email", "Email"),
                                            ("contact-where", "Where to find me"),
                                            ("contact-elsewhere", "Elsewhere")]
    email, where, elsewhere = (body for _, _, body in rows)
    assert email.count("contact__addr") == 2 and email.count('class="contact__copy"') == 2
    assert '<ul class="contact__mails" role="list">' in email
    assert '<address class="contact__where">' in where
    assert 'href="cv.html"' in elsewhere and elsewhere.count('rel="me"') == 3


def test_the_register_keeps_the_ledes_measure_and_the_addresses_lead_it():
    css = contact.CSS
    assert ".contact__reg{max-width:var(--measure);" in css
    assert re.search(r"\.contact__addr a\{color:var\(--link\);", css)
    for sel in (".contact__where a{", ".contact__link{"):
        body = css[css.index(sel):css.index("}", css.index(sel))]
        assert "color:var(--ink)" in body, sel
    # inside an entry closer than between the two, so each control reads with its address
    assert ".contact__mails{display:grid;row-gap:32px;" in css
    assert "margin:0 0 10px" in re.search(r"\.contact__kind\{([^}]*)\}", css).group(1)
    assert "margin:14px 0 0" in re.search(r"\.contact__copy\{([^}]*)\}", css).group(1)


def test_a_row_is_left_out_when_there_is_nothing_to_put_in_it():
    bare = contact.render(dict(INFO, department="", institute="", city="", country="",
                               links=[], cv_href=""))
    assert [h for _, h, _ in _rows(bare)] == ["Email"]
    cv_only = contact.render(dict(INFO, links=[]))
    assert [h for _, h, _ in _rows(cv_only)][-1] == "Elsewhere"
    assert 'rel="me"' not in cv_only and 'href="cv.html"' in cv_only


# ------------------------------------------------------------------ copying

def test_each_copy_control_is_named_for_its_address_and_says_what_happened():
    page = contact.render(INFO)
    buttons = [b for _, _, b in _entries(page)]
    assert len(buttons) == 2
    for btn, kind in zip(buttons, ("institutional", "personal")):
        assert btn.startswith('<button class="contact__copy" type="button" ')
        name = re.search(r'aria-label="([^"]+)"', btn).group(1)
        assert name == f"Copy {kind} address"
        # its visible words: "Copy", and "Copied" kept out of its name
        assert re.search(r'<span class="contact__lbl-a">Copy</span>', btn)
        assert '<span class="contact__lbl-b" aria-hidden="true">Copied</span>' in btn
        assert name.startswith(_text(re.search(r'<span class="contact__lbl-a">(.*?)</span>',
                                               btn).group(1))), "the label is in the name"
        # its glyph says nothing and takes no focus
        assert 'aria-hidden="true" focusable="false"' in btn
    # one polite line says which was copied, or what to do
    assert page.count('role="status"') == 1
    assert '<p class="contact__say" role="status" aria-live="polite"></p>' in page
    assert "m.name+' address copied.'" in contact.JS
    assert "The address is selected. Copy it with your keyboard." in contact.JS
    assert "@media (scripting:none){.contact__copy{display:none}}" in contact.CSS


def test_the_copy_uses_the_clipboard_then_a_selection_then_leaves_it_selected():
    js = contact.JS
    assert "navigator.clipboard" in js and "window.isSecureContext" in js
    assert "cb.writeText(text).then(" in js
    # the fallback copies a selection of that address; failing, it is left selected
    assert "r.selectNodeContents(addr)" in js and "execCommand('copy')" in js
    assert "if(ok)s.removeAllRanges();" in js


def test_a_copy_settles_after_two_seconds_and_the_clipboard_holds_one():
    js = contact.JS
    assert "ok?2000:6000" in js
    # copying one settles the other at once: one address is lit at a time
    assert "for(var i=0;i<mails.length;i++)settle(mails[i]);" in js
    assert "m.a.classList.add('is-copied')" in js and "m.a.classList.remove('is-copied')" in js
    # the face is centred at rest by half of what "Copied" is wider, in em
    assert "setProperty('--dx'" in js and "'em'" in js
    assert "transform:translateX(var(--dx,.42em))" in contact.CSS


def test_a_copy_lights_the_address_it_took():
    rules = {(ats, sel): body for ats, sel, body in _rules(contact.CSS)}
    light = rules[((), ".contact__addr::before")]
    assert "background:var(--wash)" in light and "opacity:0" in light
    assert "pointer-events:none" in light
    # lit and let go: at rest only the opacity and its timing change
    lit = rules[((), ".contact__addr.is-copied::before")]
    assert {d.split(":")[0] for d in lit.split(";") if d} == {"opacity", "transition-duration"}
    # where motion is welcome the wash sweeps across it, left to right
    moving = ("@media (prefers-reduced-motion:no-preference)",)
    assert "clip-path:inset(0 100% 0 0)" in rules[(moving, ".contact__addr::before")]
    assert "clip-path var(--spring-mid)" in rules[(moving, ".contact__addr.is-copied::before")]


def test_the_copy_glyph_gives_way_to_a_check_that_draws_itself():
    page = contact.render(INFO)
    assert page.count('<g class="contact__cp">') == 2
    assert page.count('<path class="contact__ck" d="m5.5 12.6 4.2 4.2 8.8-9.1" '
                      'pathLength="1"/>') == 2
    rules = {sel: body for ats, sel, body in _rules(contact.CSS)
             if any("no-preference" in a for a in ats)}
    assert "stroke-dasharray:1;stroke-dashoffset:1" in rules[".contact__ck"]
    assert "stroke-dashoffset var(--spring-mid) 40ms" in rules[".contact__copy.is-done .contact__ck"]
    assert "transform:scale(.55);filter:blur(2px)" in rules[".contact__copy.is-done .contact__cp"]
    # "Copy" into a 2px blur, "Copied" out of one, 60ms behind
    assert "filter:blur(2px)" in rules[".contact__copy.is-done .contact__lbl-a"]
    assert "60ms" in rules[".contact__copy.is-done .contact__lbl-b"]
    # the press gives 3%, on the quick spring
    assert "transform:scale(.97)" in rules[".contact__copy:active"]
    assert "transform var(--spring-quick)" in rules[".contact__copy"]


# ------------------------------------------------------------------ restraint

def test_no_slab_no_channel_no_filled_button():
    css, page = contact.CSS, contact.render(INFO)
    assert "--nav" not in css, "blue here is the link's, not a surface"
    assert not re.search(r"background(-color)?:var\(--accent", css), "no filled amber"
    for gone in ("contact__sig", "contact__pk", "contact__sensor", "contact__lit",
                 "contact__send"):
        assert gone not in page and gone not in css
    assert "ping(" not in contact.JS


def test_nothing_moves_on_its_own():
    css = re.sub(r"/\*.*?\*/", "", contact.CSS, flags=re.S)
    assert "animation" not in css and "@keyframes" not in css
    assert "infinite" not in css and "setInterval" not in contact.JS
    assert "requestAnimationFrame" not in contact.JS
    # the only clock is the minute's, for the time in Izmir
    assert contact.JS.count("setTimeout(show") == 1


def test_under_reduced_motion_nothing_travels_and_the_faces_swap_by_opacity():
    travels = ("transform", "filter", "clip-path", "stroke-dashoffset")
    for ats, sel, body in _rules(contact.CSS):
        welcome = any("no-preference" in a for a in ats)
        # every transition of a thing that travels is motion's
        for decl in body.split(";"):
            prop, _, val = decl.partition(":")
            if prop.strip() == "transition" and val.strip() != "none":
                moved = {item.split()[0] for item in val.split(",")} & set(travels)
                assert welcome or not moved, (sel, moved)
        # and so is every blur, every scale, the sweep and the dash
        for mark in ("filter:blur", "scale(", "clip-path:inset(0 100%", "stroke-dasharray"):
            if mark in body:
                assert welcome, (sel, mark)
    # what is left for reduced motion is the end state, by opacity
    rest = {sel: body for ats, sel, body in _rules(contact.CSS) if not ats}
    assert rest[".contact__lbl-b,.contact__ck"] == "opacity:0"
    assert rest[".contact__copy.is-done :is(.contact__lbl-a,.contact__cp)"] == "opacity:0"
    assert rest[".contact__copy.is-done :is(.contact__lbl-b,.contact__ck)"] == "opacity:1"
    assert "transform" not in rest[".contact__copy:active"]


# ------------------------------------------------------------------ where to find him

def test_where_to_find_him_links_his_department_and_institute():
    page = contact.render(INFO)
    where = re.search(r'<address class="contact__where">(.*?)</address>', page, re.S).group(1)
    assert '<a href="https://civil.iyte.edu.tr/en/home-page/">Department of Civil Engineering</a>' in where
    assert '<a href="https://en.iyte.edu.tr/">Izmir Institute of Technology</a>' in where
    # one line each, kept apart when copied or read aloud
    assert _text(where.replace("<br>", "\n")).split("\n") == [
        "Department of Civil Engineering", "Izmir Institute of Technology", "Izmir, Turkiye"]
    # a name the page does not know is set, not linked
    other = contact.render(dict(INFO, department="Department of Physics"))
    assert '<address class="contact__where">Department of Physics<br>' in other
    assert 'href="https://civil' not in other
    assert "font-style:normal" in re.search(r"\.contact__where\{([^}]*)\}", contact.CSS).group(1)


def test_the_time_in_izmir_is_kept_in_place_and_drawn_only_with_a_script():
    page = contact.render(INFO)
    assert ('<p class="contact__clock"><time></time> local time'
            '<span class="contact__utc"></span></p>') in page
    assert "timeZone:'Europe/Istanbul'" in contact.JS and "hourCycle:'h23'" in contact.JS
    css = contact.CSS
    clock = re.search(r"\.contact__clock\{([^}]*)\}", css).group(1)
    assert "visibility:hidden" in clock and "tabular-nums" in clock
    assert ".contact__clock.is-set{visibility:visible}" in css
    assert "@media (scripting:none){.contact__clock{display:none}}" in css
    # the clock is Izmir's: none where the city is another or not given
    assert "contact__clock" not in contact.render(dict(INFO, city=""))
    assert "contact__clock" not in contact.render(dict(INFO, city="Ankara"))


# ------------------------------------------------------------------ elsewhere

def test_elsewhere_is_his_cv_then_his_known_services_and_nothing_else():
    rows = contact._profiles(LINKS)
    assert [k for k, _, _ in rows] == ["scholar", "linkedin", "researchgate"]
    page = contact.render(INFO)
    names = re.findall(r'<a class="contact__link" href="[^"]+"(?: rel="me")?>'
                       r'<svg[^>]*>.*?</svg><span>([^<]+)</span>', page, re.S)
    assert names == ["Curriculum vitae", "Google Scholar", "LinkedIn", "ResearchGate"]
    assert page.count('rel="me"') == 3 and "wavesanddata.com" not in page
    assert "example.com" not in page and "Download CV" not in page


def test_the_glyphs_are_the_inline_family():
    page = contact.render(INFO)
    svgs = re.findall(r"<svg[^>]*>.*?</svg>", page, re.S)
    assert len(svgs) == 2 + 4 + 4   # two copy glyphs, four glyphs, four arrows
    for svg in svgs:
        assert 'viewBox="0 0 24 24"' in svg and 'aria-hidden="true"' in svg
        assert 'stroke-width="1.5"' in svg and 'focusable="false"' in svg
        assert len(svg.encode()) <= 800


# ------------------------------------------------------------------ the brief's rules

def test_hover_lives_inside_hover_hover_and_focus_outside_it():
    for ats, sel, body in _rules(contact.CSS):
        if ":hover" in sel:
            assert any("hover:hover" in a for a in ats), sel
            assert "translateY" not in body and "box-shadow" not in body, sel
            # no hue change: a hover only darkens a neutral, or draws a line
            assert not re.search(r"var\(--(link|accent|wash)", body), sel
        if ":focus-visible" in sel:
            assert not any("hover:hover" in a for a in ats), sel
    # every control has its ring
    for sel in (".contact__copy:focus-visible{", ".contact__addr a:focus-visible{",
                ".contact__link:focus-visible{"):
        body = contact.CSS[contact.CSS.index(sel):]
        assert body[:body.index("}")].count("outline:2px solid var(--focus)") == 1, sel


def test_colours_come_from_tokens_and_names_from_the_part():
    css = re.sub(r"/\*.*?\*/", "", contact.CSS, flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", css), "colours are tokens"
    assert not re.search(r"(?m)^\s*:root\s*\{", css), "no :root property is written"
    for sel in (s for _, s, _ in _rules(contact.CSS)):
        for part in sel.split(","):
            assert ".contact" in part, part
    # Windows contrast themes: the controls keep their edge, the light goes
    assert "@media (forced-colors:active){\n  .contact__copy{border-color:ButtonText}" in contact.CSS


def test_no_dash_of_ours():
    page = contact.render(INFO)
    for text in (page, contact.CSS, contact.JS, contact.__doc__):
        assert "—" not in text and " – " not in text
