"""The system that recreates his probability deck (tools/deck/): his formulas
typeset without a character of his lost, figures that ask for what their
slide's script provides, and the slides written at the sizes the viewer takes.

The full check of a slide (his words against his PowerPoint, overflow, size,
leading) needs his file and a browser: python tools/deck/render.py N --look.
"""

import html
import importlib.util
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECK = os.path.join(ROOT, "tools", "deck")
sys.path.insert(0, DECK)

import fig  # noqa: E402
import his  # noqa: E402
import mathtype  # noqa: E402

# his formulas as his PowerPoint holds them, from slides 4 to 33
HIS = [
    "P(find the defect) = 3/25 = 12%",
    "P(A) = |A| / |Ω| = 3/25 = 12%",
    "P(a < X < b) = ∫ₐᵇ fₓ(x) dx",
    "Cov(X,Y) = E[(X − μₓ)(Y − μᵧ)]",
    "Var(X̄) = (1/n²) × nσ² = σ²/n",
    "SE(X̄) = σ/√n = 3/√25 = 0.6 MPa",
    "Z = (X̄ − μ)/SE  ∼  N(0, 1)",
    "vᴅ = σ²/n: variance of the sample mean",
    "σʏ² = a₁²σ₁² + a₂²σ₂² + 2a₁a₂Cov(X₁, X₂)",
    "= Σᵢ cᵢ²σᵢ² + 2Σᵢ<ⱼ cᵢcⱼ Cov(Xᵢ, Xⱼ)",
    "δᵢ = Xᵢ − μᵢ       cᵢ = ∂f/∂Xᵢ at X = μ       Y ≈ f(μ) + Σᵢ cᵢδᵢ",
    "One input: δ = X − μ, local slope a = f′(μ), curvature b = f″(μ)",
    "Var(Y) ≈ a²σ² + ½b²σ⁴.",
    "3  Repeat N times to obtain y₁, …, yɴ.",
    "p(μ | D) ∝ exp{−½[(μ − m₀)²/v₀",
    "Ŷ, one value",
]


def text_of(markup):
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


@pytest.mark.parametrize("s", HIS)
def test_a_typeset_formula_says_what_his_says(s):
    assert mathtype.norm(text_of(mathtype.typeset(s))) == mathtype.norm(s)


def test_variables_are_math_italic_and_words_upright():
    out = mathtype.typeset("Cov(X,Y) = E[(X − μₓ)(Y − μᵧ)]")
    assert '<span class="w">Cov</span>' in out
    assert '<span class="mi">\U0001D44B</span>' in out            # X, math italic
    assert "<sub>" in out and "<sup>" not in out
    # his subscript gamma is the subscript y he meant
    assert text_of(mathtype.typeset("μᵧ")).endswith("\U0001D466")


def test_stacked_limits_keep_his_order():
    out = mathtype.typeset("∫ₐᵇ")
    assert out.index("<sub>") < out.index("<sup>")               # a before b, as he typed
    assert 'class="ss"' in out


def test_a_changed_word_is_caught():
    assert mathtype.norm("P(find the defect)") != mathtype.norm("P(find a defect)")
    assert mathtype.norm("x − y") == mathtype.norm("x - y")       # the minus sign is one character


def test_tick_numbers_print_as_tex_does():
    assert fig.num(0.2) == "0.2" and fig.num(3) == "3" and fig.num(-1) == "−1"
    assert fig.is_num("10<sup>−1</sup>") and not fig.is_num("<m>a</m>")


def sources():
    """Every slide's source, by its stem less the s: 004, and 065a for a
    slide of ours lettered after his 65."""
    src = os.path.join(DECK, "src")
    return sorted(f[1:-5] for f in os.listdir(src) if re.fullmatch(r"s\d{3}[a-z]*\.html", f))


@pytest.mark.parametrize("nnn", sources())
def test_every_figure_a_slide_asks_for_exists(nnn):
    src = os.path.join(DECK, "src")
    page = open(os.path.join(src, f"s{nnn}.html"), encoding="utf-8").read()
    wanted = re.findall(r'<div\s+data-fig="([\w-]+)"', page)
    if not wanted:
        return
    spec = importlib.util.spec_from_file_location(f"t_s{nnn}", os.path.join(src, f"s{nnn}.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, src)
    spec.loader.exec_module(mod)
    for name in wanted:
        out = getattr(mod, name)()
        assert out.startswith('<div class="fig') and "<svg" in out


@pytest.mark.parametrize("nnn", sources())
def test_a_source_keeps_to_the_shared_look(nnn):
    page = open(os.path.join(DECK, "src", f"s{nnn}.html"), encoding="utf-8").read()
    style = " ".join(re.findall(r"<style>(.*?)</style>", page, re.S))
    assert not re.search(r"#[0-9A-Fa-f]{3,6}\b", style)          # colours come from the tokens
    assert "font-family" not in style and "text-transform" not in style
    assert page.count('<section class="slide') == 1 and '<footer class="foot">' in page


@pytest.mark.parametrize("nnn", sources())
def test_a_recreated_slide_is_written_at_every_size(nnn):
    from PIL import Image
    deck = os.path.join(ROOT, "content", "deck-probstat")
    with Image.open(os.path.join(deck, f"s{nnn}.png")) as im:
        assert im.size == (1920, 1080)
    for w in (1600, 960, 320):
        with Image.open(os.path.join(deck, "web", f"s{nnn}-{w}.webp")) as im:
            assert im.size == (w, w * 9 // 16)
    h = his.his(nnn)                        # his, kept, under his own number
    assert h is None or os.path.isfile(os.path.join(deck, "_orig", f"s{h:03d}.png"))
    # its vector copies were printed after its photograph, never before: a
    # slide written without them would show one thing and present another
    photo = os.path.getmtime(os.path.join(deck, f"s{nnn}.png"))
    for vec in (os.path.join(deck, "web", f"s{nnn}.svg"),
                os.path.join(deck, "probability-statistics-and-estimation.pdf")):
        assert os.path.getmtime(vec) >= photo, vec


# ------------------------------------------------------------------ the deck's numbers

def test_the_deck_is_his_73_slides_and_our_kalman_loop_lettered_after_his_65():
    """29 Sep 2026: a Kalman filter logic slide between his 65 and 66. Since
    30 Sep his slides keep his numbers (his 66 is the deck's 66) and a slide
    of ours goes by the one it follows and a letter: 65a."""
    import render
    assert his.OURS.keys() == {"65a"} and his.HIS_COUNT == 73
    assert his.COUNT == render.COUNT == 74 == len(his.LABELS)
    assert his.LABELS[63:67] == ["64", "65", "65a", "66"] and his.LABELS[-1] == "73"
    assert [his.his(x) for x in ("1", "65", "65a", "66", "73")] == [1, 65, None, 66, 73]
    assert [his.stem(x) for x in (4, "65a", " 65A ", "066")] == ["s004", "s065a", "s065a", "s066"]
    assert sorted(h for x in his.LABELS if (h := his.his(x))) == list(range(1, 74))
    assert sources() == sorted([f"{n:03d}" for n in range(1, 74)] + ["065a"])
    # a range runs in the deck's order, so it holds the lettered slides in it
    assert render.slides(["all"]) == his.LABELS
    assert render.slides(["64-66"]) == ["64", "65", "65a", "66"] and render.slides(["65a"]) == ["65a"]
    assert his.key("7") < his.key("7a") < his.key("7b") < his.key("8")
    for bad in ("74", "65b", "x", "0"):
        with pytest.raises(ValueError):
            his.label(bad)


def test_the_manifest_is_the_deck_in_order():
    """content/deck-probstat/deck.json (render.py): a row a slide, in the
    deck's order, its label, stem and title; the viewer's alt text and the
    PDF's bookmarks. Each source's <h1> is its title, and its running foot
    ends in its label (his slide 2, the map, has none)."""
    import json
    with open(os.path.join(ROOT, "content", "deck-probstat", "deck.json"), encoding="utf-8") as fh:
        rows = json.load(fh)
    assert [r["label"] for r in rows] == his.LABELS
    assert [r["stem"] for r in rows] == [his.stem(x) for x in his.LABELS]
    # the slides that play say how long; each has its page beside the shared files
    plays = [r for r in rows if "anim" in r]
    assert "65a" in [r["label"] for r in plays] and all(r["anim"] > 0 for r in plays)
    anim = os.path.join(ROOT, "content", "deck-probstat", "anim")
    assert sorted(os.listdir(anim)) == sorted(["anim.js", "deck.css", "deck.js"] + [f"{r['stem']}.html" for r in plays])
    for r in rows:
        page = open(os.path.join(DECK, "src", f"{r['stem']}.html"), encoding="utf-8").read()
        h1 = re.search(r'<h1 class="title[^"]*">(.*?)</h1>', page, re.S).group(1)
        assert " ".join(text_of(h1).split()) == r["title"], r["label"]
        assert re.findall(r'<span class="num">(\d+[a-z]*)</span>', page) == ([] if r["label"] == "2" else [r["label"]]), r["label"]
    # the old titles list is gone: the manifest is the one place titles live
    assert not os.path.exists(os.path.join(ROOT, "content", "deck-probstat", "titles.json"))


def test_our_kalman_loop_keeps_the_sites_rules_and_its_numbers():
    import render
    page = open(os.path.join(DECK, "src", "s065a.html"), encoding="utf-8").read()
    assert not render.OUR_DASH.search(text_of(page))                 # no em dash, no spaced en dash
    assert not os.path.exists(os.path.join(DECK, "src", "s065a.pic.txt"))  # no words of his
    # his notation of slide 65 (x̂⁻ = F x̂, z = H x + v, the gain K), indexed by k
    for s in ("x̂ₖ⁻ = F x̂ₖ₋₁", "Pₖ⁻ = F Pₖ₋₁ Fᵀ + Q", "zₖ = H xₖ + vₖ", "Kₖ = Pₖ⁻ Hᵀ (H Pₖ⁻ Hᵀ + R)⁻¹",
              "x̂ₖ = x̂ₖ⁻ + Kₖ (zₖ − H x̂ₖ⁻)", "Pₖ = (I − Kₖ H) Pₖ⁻"):
        assert f"<m>{s}</m>" in page, s
    # the loop runs predict, observe, weigh, update and back
    wires = re.findall(r'data-from="#(\w+)" data-to="#(\w+)"', page)
    assert wires == [("pred", "obs"), ("obs", "gain"), ("gain", "upd"), ("upd", "pred")]
    # its picture is the next slide's hour, the update the product of the two
    # (s066.py asserts it on import), and the lever balances
    src = os.path.join(DECK, "src")
    sys.path.insert(0, src)
    spec = importlib.util.spec_from_file_location("t_ours_s065a", os.path.join(src, "s065a.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (mod.MU0, mod.Z, mod.PM, mod.R) == (10.0, 14.0, 4.0, 9.0)
    assert round(mod.K, 2) == 0.31 and round(mod.MU1, 2) == 11.23
    assert abs(mod.K / mod.PM - (1 - mod.K) / mod.R) < 1e-15


# ------------------------------------------------------------------ the slides that play

def test_a_spec_is_data_the_runtime_reads():
    """fig.py writes how a mark arrives as data (data-anim); anim.js plays
    it. Times are seconds from the figure's start; .end is when it has
    arrived, .done when it is exactly at rest (Motion's spring, bounce 0)."""
    a = fig.pop(1) + fig.keys([1, 1.4], [10, 20], prop="x", visual=.8)
    assert a.json() == [{"k": "pop", "t": 1, "v": 0.35},
                        {"k": "keys", "t": [1, 1.4], "p": "x", "v": [10, 20], "e": "settle", "vd": 0.8}]
    assert a.end == 2.2 and a.done == round(1.4 + fig.spring_done(.8), 3)
    # the spring's rest: within 0.005 of its target and slower than 0.01 a second
    for v in (.3, .8, 2.0):
        w, t = 2 * 3.141592653589793 / (1.2 * v), fig.spring_done(v)
        assert 2.71828 ** (-w * t) * (1 + w * t) <= .005 and w * w * t * 2.71828 ** (-w * t) <= .0101
    # several marks: each its own start
    s = fig.seq(0.5, 0.1, n=3)
    assert [s.at(i).json()[0]["t"] for i in range(3)] == [0.5, 0.6, 0.7] and s.end == 1.0
    assert fig.grow(0, .5, stagger=.1).bind(3).at(2).json() == [{"k": "grow", "t": 0.2, "v": 0.5}]
    # an arrow's tip comes as its line reaches it
    assert fig.draw(1, .5).head().json() == [{"k": "fade", "t": 1.4, "d": 0.12}]
    with pytest.raises(ValueError):
        fig.keys([1, 0.5], [0, 1])                                      # times in order


def test_every_axes_call_takes_anim_and_draws_the_same_picture_without_it():
    import numpy as np

    def one(anim=None):
        fig.Fig._uid = 0                        # the same clip ids each time
        f = fig.Fig(400, 300)
        ax = f.axes(40, 10, 340, 250, xlim=(0, 4), ylim=(0, 4), xticks=[0, 2, 4], yticks=[0, 2, 4])
        kw = {} if anim is None else {"anim": anim}
        ax.plot([0, 1, 2, 3], [0, 1, 2, 3], **kw)
        ax.bars([1, 2], [1, 2], **kw)
        ax.scatter([1, 2, 3], [1, 2, 3], **kw)
        ax.step([0, 1, 2], [0, 1, 2], **kw)
        ax.stem([1, 2], [2, 3], **kw)
        ax.errorbar([1], [2], [1.5], [2.5], **kw)
        ax.interval(1, 3, 1, **kw)
        ax.mark(2, 2, **kw)
        ax.hline(1, **kw)
        ax.area(np.array([0, 1, 2]), [1, 2, 1], **kw)
        ax.text(2, 3.5, "a", **kw)
        return f.html()
    plain = one()
    assert "data-anim" not in plain and "data-cues" not in plain
    played = one(fig.pop(0.5))
    assert re.sub(r" data-anim='[^']*'", "", played) == plain       # the same picture, with its data
    # a seq on one line extends it through its points: progress keys, linear
    # in its length, point i at its moment
    f = fig.Fig(300, 200)
    ax = f.axes(0, 0, 300, 200, xlim=(0, 3), ylim=(0, 1), frame=False)
    ax.plot([0, 1, 2, 3], [0, 0, 0, 0], anim=fig.seq(1, .5))
    spec = json_anim(f.html())[0]
    assert spec == [{"k": "keys", "t": [1, 1.5, 2, 2.5], "p": "p", "v": [0, 0.3333, 0.6667, 1], "e": "linear"}]
    # a step reaches data point i at its riser's top (the line's vertex 2i)
    f = fig.Fig(300, 200)
    ax = f.axes(0, 0, 300, 200, xlim=(0, 2), ylim=(0, 2), frame=False)
    ax.step([0, 1, 2], [0, 1, 2], anim=fig.seq(0, 1))
    assert json_anim(f.html())[0][0]["v"] == [0, 0.5, 1]
    # bars grow from their base; keys of where a mark is are data, then px
    # offsets from its place
    f = fig.Fig(300, 200)
    ax = f.axes(0, 0, 300, 200, xlim=(0, 3), ylim=(0, 2), frame=False)
    ax.bars([1], [2], anim=fig.grow(0))
    ax.scatter([1], [1], anim=fig.keys([0, 1], [(0, 1), (1, 1)]))
    bar, dot = json_anim(f.html())
    assert bar == [{"k": "grow", "t": 0, "v": 0.5, "b": 200}]
    assert dot[0]["v"] == [[-100, 0], [0, 0]]
    # a figure names its moments for the slide's blocks
    f = fig.Fig(10, 10)
    f.cue("hour", 2.5)
    assert "data-cues='{\"hour\":2.5}'" in f.html()


def json_anim(markup):
    import json
    import html as _h
    return [json.loads(_h.unescape(a)) for a in re.findall(r"data-anim='([^']*)'", markup)]


def kalman():
    src = os.path.join(DECK, "src")
    sys.path.insert(0, src)
    spec = importlib.util.spec_from_file_location("t_play_s065a", os.path.join(src, "s065a.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_kalman_loop_plays_once_round_its_loop():
    """The pilot of the slides that play (DECK_BRIEF.md "Animated slides"):
    each box comes as its step does, each wire as the loop reaches the next
    box, the picture drawn as the step says; the take-away last."""
    import json
    mod = kalman()
    page = open(os.path.join(DECK, "src", "s065a.html"), encoding="utf-8").read()
    out = mod.weigh()
    cues = json.loads(re.search(r"data-cues='([^']*)'", out).group(1))
    assert cues == {"predict": mod.T_PRED, "observe": mod.T_OBS, "weigh": mod.T_GAIN,
                    "update": mod.T_UPD, "next": mod.T_NEXT}
    assert mod.T_PRED < mod.T_OBS < mod.T_GAIN < mod.T_UPD < mod.T_NEXT < mod.ANIM["length"]
    boxes = re.findall(r'<div class="node [^"]*" id="(\w+)" data-in="(\w+)">', page)
    assert boxes == [("pred", "predict"), ("obs", "observe"), ("gain", "weigh"), ("upd", "update")]
    wires = re.findall(r'data-from="#(\w+)" data-to="#(\w+)"[^>]* data-in="([\w.+-]+)"', page)
    assert [w[2] for w in wires] == ["observe-0.5", "weigh-0.5", "update-0.5", "next-0.1"]
    assert re.search(r'<p class="take" data-in="next\+0.5" data-as="fade">', page)
    # every mark and label of the picture arrives with its step, and all
    # are at rest by the end
    drawn = re.sub(r"<defs>.*?</defs>", "", out, flags=re.S)
    marks = re.findall(r"<(?:path|rect)\b[^>]*>", drawn) + re.findall(r'<span class="ft\b[^>]*>', drawn)
    specs = json_anim(out)
    assert len(marks) == len(specs) == 23 and all("data-anim" in m for m in marks)
    last = max(p["t"][-1] if p["k"] == "keys" else p["t"] + p.get("d", p.get("v", 0)) for sp in specs for p in sp)
    assert last < mod.ANIM["length"]
    # the manifest says it plays, and for how long
    with open(os.path.join(ROOT, "content", "deck-probstat", "deck.json"), encoding="utf-8") as fh:
        row = next(r for r in json.load(fh) if r["label"] == "65a")
    assert row["anim"] == mod.ANIM["length"]


def test_the_runtime_keeps_to_its_contract():
    js = open(os.path.join(DECK, "anim.js"), encoding="utf-8").read()
    for hook in ("window.DeckAnim", "report", "seek", "finish", "play", "running", "frames", "slowest",
                 "dataset.anim = 'ready'", "anim-wait", "prefers-reduced-motion: reduce",
                 "q.get('t')", "q.has('wait')", "q.get('speed')", "postMessage", "window.DECK_READY"):
        assert hook in js, hook
    # the same spring rule as fig.spring_done() (Motion's rest: 0.005 and 0.01)
    assert "e * (1 + x) <= .005 && w * w * tau * e <= .01" in js
    # the runtime writes nothing the site's pages may not carry
    assert "—" not in js and " – " not in js
    # deck.js hands a wire's data-in to the path it draws
    assert "setAttribute('data-in', w.dataset.in)" in open(os.path.join(DECK, "deck.js"), encoding="utf-8").read()


def test_the_page_a_slide_plays_in_is_on_disk_with_what_it_needs():
    import json
    anim = os.path.join(ROOT, "content", "deck-probstat", "anim")
    assert {"anim.js", "deck.css", "deck.js", "s065a.html"} <= set(os.listdir(anim))
    page = open(os.path.join(anim, "s065a.html"), encoding="utf-8").read()
    cfg = json.loads(re.search(r'<script type="application/json" id="deck-anim">(.*?)</script>', page, re.S).group(1))
    assert cfg == {"length": kalman().ANIM["length"], "label": "65a", "stem": "s065a"}
    assert '<script src="anim.js"></script>' in page and 'class="anim-page anim-wait"' in page
    # its copies of the shared files are the deck's own
    for f in ("anim.js", "deck.js"):
        assert open(os.path.join(anim, f), encoding="utf-8").read() == open(os.path.join(DECK, f), encoding="utf-8").read()
    # its fonts are the site's fonts/ (three folders up on the site); each is one it publishes
    css = open(os.path.join(anim, "deck.css"), encoding="utf-8").read()
    fonts = re.findall(r"url\(([^)]+)\)", css)
    assert fonts and all(u.startswith("../../../fonts/") for u in fonts)
    have = set(os.listdir(os.path.join(ROOT, "site", "fonts"))) | set(os.listdir(os.path.join(ROOT, "content", "fonts-cmu"))) \
        | set(os.listdir(os.path.join(DECK, "fonts")))
    assert {u.rsplit("/", 1)[1] for u in fonts} <= have


def _chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _chromium(), reason="needs Playwright's Chromium")
def test_the_kalman_loop_plays_from_empty_to_its_photograph():
    import io
    import render
    from PIL import Image
    from playwright.sync_api import sync_playwright
    url = f"{render.server()}/content/deck-probstat/anim/s065a.html"
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none"])
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(url + "?t=0")
        pg.wait_for_function("document.documentElement.dataset.anim === 'ready'", timeout=30000)
        rep = pg.evaluate("DeckAnim.report()")
        assert rep["problems"] == [] and rep["ghostText"] == [] and rep["length"] == 9.8
        assert rep["actors"] >= 40 and rep["end"] <= rep["length"]
        # at its first moment the boxes and the picture's curves are not yet there
        assert pg.evaluate("getComputedStyle(document.querySelector('#pred')).opacity") == "0"
        # its last moment is the slide as photographed, nothing the runtime set left on it
        pg.evaluate("DeckAnim.seek('end')")
        assert pg.evaluate("DeckAnim.state") == "done"
        assert pg.evaluate("""[...document.querySelectorAll('[data-anim],[data-in]')].filter(e =>
            e.style.opacity || e.style.translate || e.style.scale || e.style.clipPath || e.style.visibility ||
            (e instanceof SVGElement && e.hasAttribute('transform'))).length""") == 0
        with Image.open(io.BytesIO(pg.screenshot())) as im:
            last = im.convert("RGB").resize((1920, 1080), Image.Resampling.LANCZOS)
        with Image.open(os.path.join(ROOT, "content", "deck-probstat", "s065a.png")) as im:
            photo = im.convert("RGB")
        # the photograph may come from another machine (his file and the
        # photographs live on Windows): the vector check's measure, over 10 px
        assert render._worst(photo, last, radius=10) <= render.VEC_TOL
        # played fast, it ends and stops asking for frames
        pg.goto(url + "?speed=20")
        pg.wait_for_function("window.DeckAnim && DeckAnim.state === 'done'", timeout=15000)
        pg.wait_for_timeout(100)
        assert pg.evaluate("DeckAnim.running") is False and pg.evaluate("DeckAnim.frames") > 5
        # less motion asked for: the slide at once
        ctx = b.new_context(viewport={"width": 960, "height": 540}, reduced_motion="reduce")
        q = ctx.new_page()
        q.goto(url)
        q.wait_for_function("document.documentElement.dataset.anim === 'ready'", timeout=30000)
        assert q.evaluate("DeckAnim.state") == "done"
        # scaled to its window
        assert q.evaluate("document.querySelector('.slide').style.transform") == "scale(0.5)"
        b.close()
    assert errors == []


# ------------------------------------------------------------------ the palette

def test_the_figures_and_the_slides_take_the_crimson():
    # tools/ROUND11.md: accent #A7203A, amber #D14457, wash #F9EEEE, deep #781E2C
    want = {"accent": "#A7203A", "amber": "#D14457", "deep": "#781E2C", "wash": "#F9EEEE"}
    assert {k: getattr(fig.C, k) for k in want} == want
    css = open(os.path.join(DECK, "deck.css"), encoding="utf-8").read()
    for k, v in want.items():
        assert f"--{k}:{v};" in css
    # the burnt orange is gone but for his own colour words (fig.C.orange*)
    old = re.compile(r"#(?:A5510B|D9822B|7B3D0C|FEEBDB|EBC6A4)\b", re.I)
    assert not old.search(css)
    src = os.path.join(DECK, "src")
    for f in os.listdir(src):
        if f.endswith((".py", ".html")):
            assert not old.search(open(os.path.join(src, f), encoding="utf-8").read()), f
    assert (fig.C.orange, fig.C.orange_edge) == ("#D9822B", "#A5510B")
    assert fig.mix("#FFFFFF", "#000000", 0.5) == "#808080" and fig.mix(fig.C.amber, fig.C.paper, 1) == fig.C.amber


# ------------------------------------------------------------------ the vectors

import vector  # noqa: E402


def test_path_data_is_written_short_and_lands_where_it_was():
    d = "M34 0V-19L138-32H189L304-19V0H34ZM107 0C108.33-26.67 109.33-57.67 110-93 110.67-128.33 111.5-203.5 111-313"
    segs = vector.parse_path(d)
    short = vector.encode_path(segs, 2)
    assert len(short) < len(d)
    again = vector.parse_path(short)
    assert [c for c, _ in again] == [c for c, _ in segs]
    for (_, a), (_, b) in zip(segs, again):
        assert all(abs(x - y) < 0.006 for x, y in zip(a, b))       # 0.01 steps, no drift
    # a whole number keeps its zeros (70 is not 7)
    assert vector.encode_path(vector.parse_path("M0 0L70 100"), 0) == "M0 0 70 100"
    with pytest.raises(ValueError):
        vector.parse_path("M0 0A5 5 0 0 1 10 10")                    # an arc stays as it was


def test_only_path_coordinates_are_rounded_in_the_pdf():
    s = (b"q 3.125 0 0 3.125 0 -10125 cm\n1 0 0 -1 112 3360 Tm <11> Tj 33.320984 0 Td\n"
         b"151.779984 152.269989 m 151.505936 153.647644 l f\n500 0 34 -19 304 665 d1\n"
         b"/G3 gs (a 1.2345 b) Tj [3.5 2] 0 d")
    out = vector.round_stream(s)
    assert b"3.125 0 0 3.125 0 -10125 cm" in out and b"1 0 0 -1 112 3360 Tm" in out
    assert b"151.78 152.27 m" in out and b"151.51 153.65 l" in out
    assert b"33.321 0 Td" in out
    assert b"d1" in out and b"(a 1.2345 b)" in out and re.search(rb"\[\s*3\.5 2\s*\]\s*0 d", out)


def test_every_slide_prints_in_its_own_scope():
    page = vector.deck_html([(2, '<section class="slide s2"><style>.s2 .title{font-size:30px}</style></section>'),
                             (3, '<section class="slide"><style>.x{color:red}</style></section>')])
    assert '<div id="deck-s002"><section class="slide s2"><style>@scope (#deck-s002){.s2 .title{font-size:30px}}' in page
    assert "@scope (#deck-s003){.x{color:red}}" in page
    assert "@page{size:1920px 1080px;margin:0}" in page and ".slide{break-after:page}" in page


def test_the_deck_script_draws_each_slides_wires_in_its_own_corner():
    js = open(os.path.join(DECK, "deck.js"), encoding="utf-8").read()
    assert "slides.forEach(drawWires)" in js and "var o = slide.getBoundingClientRect();" in js


def test_the_brief_keeps_the_sites_dashes():
    text = open(os.path.join(DECK, "DECK_BRIEF.md"), encoding="utf-8").read()
    assert "—" not in text and " – " not in text
