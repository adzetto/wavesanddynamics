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
    src = os.path.join(DECK, "src")
    return sorted(f[1:4] for f in os.listdir(src) if re.fullmatch(r"s\d{3}\.html", f))


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
    h = his.his(int(nnn))                   # his, kept, under his own number
    assert h is None or os.path.isfile(os.path.join(deck, "_orig", f"s{h:03d}.png"))
    # its vector copies were printed after its photograph, never before: a
    # slide written without them would show one thing and present another
    photo = os.path.getmtime(os.path.join(deck, f"s{nnn}.png"))
    for vec in (os.path.join(deck, "web", f"s{nnn}.svg"),
                os.path.join(deck, "probability-statistics-and-estimation.pdf")):
        assert os.path.getmtime(vec) >= photo, vec


# ------------------------------------------------------------------ the deck's numbers

def test_the_deck_is_his_73_slides_and_our_kalman_loop():
    """29 Sep 2026: a Kalman filter logic slide between his 65 and 66. It is
    the deck's 66; each of his after it is one on (his 66 is our 67), and
    everything that numbers the deck counts 74."""
    import render
    assert his.OURS.keys() == {66} and his.HIS_COUNT == 73
    assert his.COUNT == render.COUNT == 74
    assert [his.his(n) for n in (1, 65, 66, 67, 74)] == [1, 65, None, 66, 73]
    assert sorted(h for n in range(1, 75) if (h := his.his(n))) == list(range(1, 74))
    assert sources() == [f"{n:03d}" for n in range(1, 75)]
    assert render.slides(["all"]) == list(range(1, 75))


def test_each_source_carries_its_title_and_its_place_in_the_deck():
    """Its <h1> is its line in titles.json (the viewer's alt text, the PDF's
    bookmarks), and its running foot ends in its own number (his slide 2,
    the map, has none)."""
    import json
    with open(os.path.join(ROOT, "content", "deck-probstat", "titles.json"), encoding="utf-8") as fh:
        titles = json.load(fh)
    assert len(titles) == 74
    for nnn in sources():
        page = open(os.path.join(DECK, "src", f"s{nnn}.html"), encoding="utf-8").read()
        h1 = re.search(r'<h1 class="title[^"]*">(.*?)</h1>', page, re.S).group(1)
        assert " ".join(text_of(h1).split()) == titles[int(nnn) - 1], nnn
        assert re.findall(r'<span class="num">(\d+)</span>', page) == ([] if nnn == "002" else [str(int(nnn))]), nnn


def test_our_kalman_loop_keeps_the_sites_rules_and_its_numbers():
    import render
    page = open(os.path.join(DECK, "src", "s066.html"), encoding="utf-8").read()
    assert not render.OUR_DASH.search(text_of(page))                 # no em dash, no spaced en dash
    assert not os.path.exists(os.path.join(DECK, "src", "s066.pic.txt"))   # no words of his
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
    spec = importlib.util.spec_from_file_location("t_ours_s066", os.path.join(src, "s066.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert (mod.MU0, mod.Z, mod.PM, mod.R) == (10.0, 14.0, 4.0, 9.0)
    assert round(mod.K, 2) == 0.31 and round(mod.MU1, 2) == 11.23
    assert abs(mod.K / mod.PM - (1 - mod.K) / mod.R) < 1e-15


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
