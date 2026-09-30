"""The home page's "Motivation for Creating the Educational Sections" (parts/motivation.py).

His block goes out byte for byte (tests/test_site.py holds that too); these
hold how it is staged since 29 Sep 2026, when the client asked for "nice
things" on its points 1, 2, 3, 4: a bead beside each numeral, one thread
through the four in his order, and, the first time they are in view, a
thought that draws the thread while each bead wakes into the site's dot orb,
branches an echo back at 3, lights the whole figure at 4 as the wave under
his "Aha!" draws, and rests. A point under the pointer tells its part again.
Asked for less motion, with colours forced or without a script, the final
state stands and nothing moves.
"""

import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
from parts import motivation, theme  # noqa: E402

CSS, JS = motivation.CSS, motivation.JS


# ------------------------------------------------------------------ his block

def test_his_block_goes_out_whole_and_what_is_ours_comes_after_it():
    out = motivation.render(build.PROF_MOTIVATION)
    assert out.startswith('<section class="motiv">' + build.PROF_MOTIVATION)
    # the wave's frame is the one thing the markup adds, after his block
    rest = out[len('<section class="motiv">' + build.PROF_MOTIVATION):]
    assert rest.startswith('<svg class="motiv__wave" aria-hidden="true"')
    assert rest.rstrip().endswith("</section>") and rest.count("<") == 4


def test_a_block_of_another_shape_ships_as_he_wrote_it(capsys):
    two_lists = build.PROF_MOTIVATION.replace("</ul>", "</ul><ul><li>x</li></ul>", 1)
    assert motivation.render(two_lists) == two_lists
    assert "shipped as he wrote it, unstaged" in capsys.readouterr().out


def test_his_markup_is_only_read():
    # the script marks the section, never his <li>s, and writes no word
    assert not re.search(r"pts\[[^\]]*\]\.(classList|setAttribute|style|textContent|innerHTML)", JS)
    assert "sec.classList.toggle('o'+(k+1),!!on)" in JS
    assert "innerHTML" not in JS and "textContent" not in JS
    # a bead gives way to its orb from the section's mark
    assert ".motiv.o1 li:nth-child(1)::after,.motiv.o2 li:nth-child(2)::after" in CSS
    # the numerals, the beads and the thread are the stylesheet's
    assert ".motiv li::before{content:counter(motiv);" in CSS
    assert ".motiv li::after{content:\"\";position:absolute;pointer-events:none;" in CSS


def test_every_rule_is_the_sections_own():
    body = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    assert ":root" not in body
    sels = [m.strip() for m in re.findall(r"([^{}]+)\{", body) if not m.strip().startswith("@")]
    assert len(sels) > 20
    for sel in sels:
        for one in sel.split(","):
            assert ".motiv" in one, one


# ------------------------------------------------------------------ colour

def test_the_figure_is_the_blue_and_never_the_accent():
    body = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    # no colour of the part's own: tokens only, on paper the blue and the inks
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", body)
    assert not re.search(r"#[0-9A-Fa-f]{3,8}\b", re.sub(r"/\*.*?\*/", "", JS, flags=re.S))
    # the thread at rest is --link let into the paper, in sRGB so the canvas
    # draws the same colour as --link at that alpha
    assert "--mv-line:color-mix(in srgb,var(--link) 34%,var(--page))" in body
    assert "runs(M.p,.34)" in JS
    # the wave, the thought and the orbs are the blue: the canvas takes the
    # wave's own colour, which is --link
    assert ".motiv__wave{position:absolute;top:0;left:0;display:none;overflow:visible;\n  pointer-events:none;color:var(--link)}" in body
    assert "function tokens(){INK=getComputedStyle(svg||sec).color}" in JS
    # the accent is the numerals' alone: text, not motion
    assert body.count("var(--accent)") == 1
    assert "font-variant-numeric:lining-nums tabular-nums;letter-spacing:0;color:var(--accent)}" in body


# ------------------------------------------------------------------ motion, where welcome

def test_motion_exists_only_where_it_is_welcome():
    body = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    # the thread waits for the thought only where motion is welcome and a
    # script runs (html.js); the script hands it back at once where it will
    # not play
    pre = body.split("@media (prefers-reduced-motion:no-preference){", 1)[1].split("\n}\n", 1)[0]
    assert ".js .motiv:not(.motiv--done) li::after{--mv-r:transparent}" in pre
    assert "if(!fig){sec.classList.add('motiv--done');due=1}" in JS
    # the wave's draw is added for motion, never clawed back
    assert "@media (prefers-reduced-motion:no-preference){\n  .motiv__wave{opacity:0}" in body
    # no canvas asked for less motion, with colours forced, or without one
    assert "if(calm.matches||n<2||matchMedia('(forced-colors: active)').matches)return;" in JS
    assert "g=cv.getContext&&cv.getContext('2d');\n  if(!g){cv=null;return}" in JS
    assert "hush();fig=0;sec.removeChild(cv);cv=null;" in JS
    assert "@media (forced-colors:active){.motiv__wave,.motiv__orbs{display:none!important}}" in body
    # drawn, not said; it takes no pointer, so his words stay selectable
    assert "cv.className='motiv__orbs';cv.setAttribute('aria-hidden','true');" in JS
    assert ".motiv__orbs{position:absolute;left:0;top:0;pointer-events:none}" in body
    assert "aria-live" not in JS and "role=" not in JS and "tabindex" not in JS.lower()


def test_frames_only_while_something_moves():
    frame = JS[JS.index("function frame(now){"):JS.index("function paint(now){")]
    assert "if(busy){paint(now);raf=requestAnimationFrame(frame)}\n  else rest();" in frame
    # at rest the canvas holds no pixels
    assert "if(cv){cv.width=cv.height=0;cv.style.display='none'}" in JS
    # layout is read at a play, never in a frame
    for fn in ("function frame(now){", "function paint(now){", "function runs(p,al){",
               "function thought(T,now,lv){", "function orb(x,y,e,a,down){", "function step(T,now){"):
        body = JS[JS.index(fn):]
        body = body[:body.index("\n}\n")]
        assert "getBoundingClientRect" not in body and "getComputedStyle" not in body, fn
        assert "offset" not in body, fn
    # crisp at the device's ratio, 2 at most, as every canvas on the site
    assert "dpr=Math.min(2,window.devicePixelRatio||1);" in JS
    # looked at on scroll, once a frame at most, never by an IntersectionObserver
    assert "IntersectionObserver" not in JS
    assert "function soon(){if(!lk)lk=requestAnimationFrame(look)}" in JS
    assert "addEventListener('scroll',soon,{passive:true})" in JS
    # off screen, a hidden tab or a page put away: to the end at once
    assert "if(raf&&list){r=list.getBoundingClientRect();if(r.bottom<=0||r.top>=vh)hush()}" in JS
    assert "document.addEventListener('visibilitychange',function(){if(document.hidden&&raf)hush()});" in JS


def test_an_orb_is_the_columns_orb():
    # dots laid evenly on a sphere (a Fibonacci lattice: the golden angle), as
    # dense as the column's 48 on 6.5px; tilted toward the reader; its life on
    # a critically damped spring, turning as the cube of its excitation
    assert "t=i*2.399963;" in JS and "Math.round(48*R1*R1/42.25)" in JS
    assert "py=SY[i]*.93-pz*.37;z=SY[i]*.37+pz*.93;" in JS
    assert "E[k]=ET[k]+(d+c*dt)*x;EV[k]=(EV[k]-w*c*dt)*x;" in JS
    assert "AN[k]+=dt*SPIN*E[k]*E[k]*E[k];" in JS
    # it grows out of the bead's ring (radius 3) and settles back into it
    assert "r=3+(R1-3)*s" in JS and "if(OC[k]&&!ET[k]&&E[k]<.45)bead(k,0);" in JS
    # settling, it fades faster than it grew, so it collapses into the ring
    assert "f=down?s*s:s" in JS and "g.globalAlpha=f*(.12+.88*t*t);" in JS


def test_the_count_is_one_to_two_seconds():
    tm = int(re.search(r"TM=(\d+)", JS).group(1))
    hold = int(re.search(r"HOLD=(\d+)", JS).group(1))
    # the thought's run, the orbs' last hold and most of their settling
    assert 1000 <= tm <= 1400 and tm + hold + 450 <= 2100


def test_no_dash_in_the_part():
    src = open(motivation.__file__, encoding="utf-8").read()
    assert chr(0x2014) not in src and " " + chr(0x2013) + " " not in src


# ------------------------------------------------------------------ in a browser

def _chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


CHROMIUM = _chromium()

# what the page does, as it does it: which orbs are awake (the section's
# o1..o4), when the thread is handed back and the wave drawn, and how many
# frames are asked for
WATCH = """
window.__log = []; window.__raf = 0;
const raf = window.requestAnimationFrame.bind(window);
window.requestAnimationFrame = cb => { window.__raf++; return raf(cb); };
document.addEventListener('DOMContentLoaded', () => {
  const s = document.querySelector('.motiv');
  if (!s) return;
  new MutationObserver(() => window.__log.push([Math.round(performance.now()), s.className]))
    .observe(s, {attributes: true, attributeFilter: ['class']});
});
"""


def _page(width, js=True):
    """The section as the build writes it, on a page of its own: the base
    stylesheet, the tokens and the part's stylesheet, his block staged, and
    the part's script; html.js as the shell sets it before the paint."""
    css = (build.CSS + theme.CSS + CSS +
           "body{margin:0;background:var(--page)}.wrap{max-width:none;padding:0}")
    return (f'<!doctype html><html lang="en" data-theme="light"{" class=js" if js else ""}>'
            f'<head><meta charset="utf-8"><style>{css}</style></head><body>'
            f'<div style="height:1500px"></div>'
            f'<div class="wrap" style="width:{width}px;margin:0 0 0 24px">'
            f'{motivation.render(build.PROF_MOTIVATION)}</div><div style="height:1500px"></div>'
            f'<script>(function(){{\n{JS}\n}})();</script></body></html>')


@pytest.fixture(scope="module")
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _open(browser, width=924, view=(1440, 900), js=True, **kw):
    c = browser.new_context(viewport={"width": view[0], "height": view[1]},
                            device_scale_factor=2, **kw)
    c.add_init_script(WATCH)
    html = _page(width, js)
    c.route("http://motiv.test/**", lambda r: r.fulfill(body=html, content_type="text/html")
            if r.request.url.endswith("/index.html") else r.abort())
    pg = c.new_page()
    pg.goto("http://motiv.test/index.html")
    pg.evaluate("document.fonts.ready.then(() => 1)")
    return c, pg


def _into_view(pg):
    pg.evaluate("""() => { const u = document.querySelector('.motiv ul').getBoundingClientRect();
        window.scrollTo(0, scrollY + u.top - innerHeight * .3); }""")


def _rests(pg, within=6.0):
    """Wait until the section has moved, is done, and no frame has been
    asked for in 400ms."""
    import time
    end = time.time() + within
    while time.time() < end:
        n = pg.evaluate("window.__raf")
        pg.wait_for_timeout(400)
        if pg.evaluate("""n => window.__raf === n && window.__log.length > 0 &&
                          !/\\bo\\d/.test(document.querySelector('.motiv').className)""", n):
            return
    raise AssertionError("the section did not come to rest")


def _awake(log):
    """For each logged moment from the first orb on, which orbs were awake
    (1-based)."""
    out = [(t, tuple(int(k) for k in re.findall(r"\bo(\d)\b", cls))) for t, cls in log]
    while out and not out[0][1]:
        out.pop(0)
    return out


def _thread(pg, k=0):
    return pg.evaluate(f"""getComputedStyle(document.querySelectorAll('.motiv li')[{k}], '::after')
                           .getPropertyValue('--mv-r')""")


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_count_is_told_in_order_then_rests(browser):
    c, pg = _open(browser)
    # before it is seen, the beads stand alone: the thread waits for the thought
    pg.wait_for_timeout(300)
    assert pg.evaluate("!document.querySelector('.motiv').classList.contains('motiv--done')")
    assert _thread(pg) == "rgba(0, 0, 0, 0)"
    _into_view(pg)
    _rests(pg)
    awake = _awake(pg.evaluate("window.__log"))
    # each point wakes in his order, the first time the thread reaches it
    first = []
    for _, on in awake:
        first += [k for k in on if k not in first]
    assert first == [1, 2, 3, 4]
    # 1 settles while the thought runs on, and is awake again at the end
    ones = [1 in on for _, on in awake]
    assert ones[0] and False in ones and True in ones[ones.index(False):]
    # at 4 the four are awake at once, one connected figure, and the thread
    # is handed back to the stylesheet; the wave under "Aha!" is drawn
    assert any(set(on) == {1, 2, 3, 4} for _, on in awake)
    cls = pg.evaluate("document.querySelector('.motiv').className")
    assert "motiv--done" in cls and "motiv--drawn" in cls
    assert _thread(pg) != "rgba(0, 0, 0, 0)"
    # all of it in about two seconds
    t0, t1 = awake[0][0], max(t for t, _ in awake)
    assert t1 - t0 <= 2300
    # at rest: no frame asked for, the canvas empty and out of the way
    n = pg.evaluate("window.__raf")
    pg.wait_for_timeout(800)
    assert pg.evaluate("window.__raf") == n
    assert pg.evaluate("""() => { const c = document.querySelector('.motiv__orbs');
        return c.getAttribute('aria-hidden') === 'true' && c.width === 0 &&
               getComputedStyle(c).display === 'none'; }""")
    # it is told once a page view: back in view, nothing plays by itself
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(200)
    _into_view(pg)
    pg.wait_for_timeout(600)
    assert pg.evaluate("window.__raf") - n <= 3
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_a_phone_is_told_the_count_down_its_column(browser):
    # the column stands taller than a desktop's row: with its top at a third
    # of the window it plays, top to bottom, and rests
    c, pg = _open(browser, width=331, view=(390, 844))
    _into_view(pg)
    _rests(pg)
    awake = _awake(pg.evaluate("window.__log"))
    first = []
    for _, on in awake:
        first += [k for k in on if k not in first]
    assert first == [1, 2, 3, 4]
    assert any(set(on) == {1, 2, 3, 4} for _, on in awake)
    assert "motiv--done" in pg.evaluate("document.querySelector('.motiv').className")
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_each_point_tells_its_part_under_the_pointer(browser):
    c, pg = _open(browser)
    _into_view(pg)
    _rests(pg)
    pts = pg.query_selector_all(".motiv li")

    def hover(k):
        pg.evaluate("window.__log = []")
        b = pts[k].bounding_box()
        pg.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] - 6)
        _rests(pg)
        pg.mouse.move(2, 2)
        return _awake(pg.evaluate("window.__log"))

    # 1 thinks, alone
    assert {k for _, on in hover(0) for k in on} == {1}
    # 2 is reached from 1
    two = hover(1)
    assert {k for _, on in two for k in on} == {1, 2}
    assert next(t for t, on in two if 1 in on) <= next(t for t, on in two if 2 in on)
    # 3 sends its echo back: 3, then 2, then 1
    three = hover(2)
    order = []
    for _, on in three:
        order += [k for k in on if k not in order]
    assert order == [3, 2, 1]
    # 4 lights the whole figure at once
    assert any(set(on) == {1, 2, 3, 4} for _, on in hover(3))
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_less_motion_or_forced_colours_show_the_final_state(browser):
    for kw in ({"reduced_motion": "reduce"}, {"forced_colors": "active"}):
        c, pg = _open(browser, **kw)
        _into_view(pg)
        pg.wait_for_timeout(900)
        assert pg.evaluate("""() => !document.querySelector('.motiv__orbs') &&
            document.querySelector('.motiv').classList.contains('motiv--done') &&
            !/\\bo\\d/.test(document.querySelector('.motiv').className)""")
        if "reduced_motion" in kw:     # the thread and the wave stand, drawn
            assert _thread(pg) != "rgba(0, 0, 0, 0)"
            assert pg.evaluate("document.querySelector('.motiv').classList.contains('motiv--wave')")
            assert pg.evaluate("getComputedStyle(document.querySelector('.motiv__wave')).opacity") == "1"
        n = pg.evaluate("window.__raf")
        pg.wait_for_timeout(500)
        assert pg.evaluate("window.__raf") == n
        c.close()
    # without a script the thread and the beads are the final state as well
    c, pg = _open(browser, js=False, java_script_enabled=False)
    assert _thread(pg) != "rgba(0, 0, 0, 0)"
    c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_the_points_stand_in_a_row_or_a_column_with_a_bead_by_each_numeral(browser):
    for width, view, row in ((924, (1440, 900), True), (749, (1100, 900), False),
                             (331, (390, 844), False)):
        c, pg = _open(browser, width=width, view=view, reduced_motion="reduce")
        geo = pg.evaluate("""() => [...document.querySelectorAll('.motiv li')].map(li => {
            const r = li.getBoundingClientRect(), a = getComputedStyle(li, '::after'),
                  b = getComputedStyle(li, '::before');
            return {left: r.left, top: r.top, bl: parseFloat(a.left), bt: parseFloat(a.top),
                    bw: parseFloat(a.width), bh: parseFloat(a.height), fs: parseFloat(b.fontSize)}; })""")
        assert len(geo) == 4
        if row:     # four across: one top, the thread from each bead to the next numeral
            assert len({round(g["top"]) for g in geo}) == 1
            for a, b in zip(geo, geo[1:]):
                end = a["left"] + a["bl"] + a["bw"]
                assert 8 <= b["left"] - end <= 12
            assert geo[3]["bw"] == 7
        else:       # a column: one left, the thread from each bead down to the next bead
            assert len({round(g["left"]) for g in geo}) == 1
            for a, b in zip(geo, geo[1:]):
                assert abs(a["top"] + a["bt"] + a["bh"] - (b["top"] + b["bt"])) < .6
            assert geo[3]["bh"] == 7
        # each bead sits after its numeral's figure, on its capitals' middle
        for g in geo:
            assert g["bl"] >= g["fs"] * .482 + 3
            assert g["fs"] * .2 <= g["bt"] + 3.5 <= g["fs"] * .6
        c.close()


@pytest.mark.skipif(not CHROMIUM, reason="needs Playwright's Chromium")
def test_in_a_browser_his_words_stay_text_under_the_figure(browser):
    c, pg = _open(browser)
    _into_view(pg)
    pg.wait_for_timeout(500)       # the thought is running: the canvas is over the points
    assert pg.evaluate("getComputedStyle(document.querySelector('.motiv__orbs')).display") == "block"
    # a drag across his fourth point selects his words, as on any page
    a, b = pg.evaluate("""() => { const li = document.querySelectorAll('.motiv li')[3],
            r = document.createRange(); r.selectNodeContents(li);
        const q = [...r.getClientRects()].filter(x => x.width > 2), f = q[0], l = q[q.length - 1];
        return [[f.left + 1, f.top + f.height / 2], [l.right - 1, l.top + l.height / 2]]; }""")
    pg.mouse.move(*a)
    pg.mouse.down()
    pg.mouse.move(*b, steps=8)
    pg.mouse.up()
    got = pg.evaluate("getSelection().toString().replace(/\\s+/g, ' ').trim()")
    assert "deeply interconnected they actually" in got
    c.close()
