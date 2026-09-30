"""His formulas set as LaTeX sets them (site/mathtex.py, round 13).

What these hold:

- the converter sets the style rules' cases as TeX would: italic letters,
  indices down, words and names upright, his * as juxtaposition or \\ast,
  \\cdot as U+22C5, TeX's spaces between atoms (none in scripts), limits under
  in display and beside in text, no delimiter stretched unasked;
- TeX's italic correction after an italic letter (rule 17), between a letter
  and its superscript, and before the superscript of a letter with both
  scripts, read from the font's MATH table;
- a long formula breaks only after a top-level relation or binary operator,
  its pieces read once as one formula; a display formula on a phone breaks
  before a relation, never the first of its clause;
- a map's entries match his text exactly, with their context, their count
  and no two on the same characters, or the build stops naming the entry;
- preview.py's text_node() sets them, escaped, holding each formula to the
  characters touching it, across runs too;
- the blog's <tex> elements and his pictures of formulas are set the same way;
- Site Math (content/fonts-cmu/site-math.woff2) keeps its MATH table and every
  character the converter may set.
"""

import html
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import mathtex  # noqa: E402
import preview  # noqa: E402
from parts import docs  # noqa: E402


def mm(tex, display=False, alt=None):
    return mathtex.mathml(tex, display, alt=alt)


def tokens(markup):
    """[(tag, attributes, text)] of the token elements, in order."""
    return re.findall(r"<(mi|mn|mo|mtext)((?:\s[^>]*)?)>([^<]*)</\1>", markup)


def mo(markup, char):
    """The attributes of the first <mo> holding `char`."""
    for tag, attrs, text in tokens(markup):
        if tag == "mo" and html.unescape(text) == char:
            return attrs
    raise AssertionError(f"no <mo>{char}</mo> in {markup}")


# ------------------------------------------------------------- the converter

def test_letters_are_italic_names_upright_greek_capitals_upright():
    out = mm(r"x + \alpha + \Gamma + \sin\theta + \mathrm{d}x + \mathrm{TP}")
    toks = tokens(out)
    assert ("mi", "", "x") in toks and ("mi", "", "α") in toks        # the browser's math italic
    assert ("mi", ' mathvariant="normal"', "Γ") in toks               # TeX's upright capitals
    assert ("mi", "", "sin") in toks and ("mi", "", "TP") in toks     # names: upright by length
    assert ("mi", ' mathvariant="normal"', "d") in toks


def test_the_client_formula():
    tex = (r"z = w_1 x_1 + w_2 x_2 + w_3 x_3 + \text{bias} \;\rightarrow\; \text{output}"
           r" = \text{activation}(z)")
    out = mm(tex, alt="z = w1*x1 + w2*x2 + w3*x3 + bias → output = activation(z)")
    assert "<msub><mi>w</mi><mn>1</mn></msub><msub><mi>x</mi><mn>1</mn></msub>" in out
    assert "<mtext>bias</mtext>" in out and "<mtext>activation</mtext>" in out
    assert 'alttext="z = w1*x1 + w2*x2 + w3*x3 + bias → output = activation(z)"' in out
    assert mo(out, "=") == ' lspace="0.2778em" rspace="0.2778em"'
    assert mo(out, "+") == ' lspace="0.2222em" rspace="0.2222em"'
    assert "*" not in re.sub(r'(?:alttext|aria-label)="[^"]*"', "", out)   # his * is his text only


@pytest.mark.parametrize("tex, char", [
    (r"a \cdot b", "⋅"), (r"x(t) \ast h(t)", "∗"), ("a * b", "∗"), (r"a \times b", "×"),
    (r"\pm 1", "±"), (r"a \leq b", "≤"), (r"a \geq b", "≥"), (r"a \sim b", "∼"),
    (r"a \approx b", "≈"), (r"a \rightarrow b", "→"), (r"p(x \mid y)", "∣"), ("a - b", "−")])
def test_his_ascii_symbols_become_tex_symbols(tex, char):
    assert mo(mm(tex), char)


def test_operatorname_and_functions_take_tex_spacing():
    out = mm(r"\operatorname{ReLU}(x) = \max(0, x)")
    assert "<mi>ReLU</mi><mo lspace=\"0\" rspace=\"0\">&#x2061;</mo>" in out   # Op then Open: 0
    assert "<mi>max</mi>" in out
    out = mm(r"\sin \theta")
    assert '<mi>sin</mi><mo lspace="0" rspace="0.1667em">&#x2061;</mo><mi>θ</mi>' in out  # Op-Ord: thin


def test_unary_minus_and_spaces_in_scripts_are_tight():
    out = mm(r"e^{-t} + y_{t-1} = -x")
    sup = re.search(r"<msup>.*?</msup>", out).group(0)
    assert 'lspace="0" rspace="0"' in mo(sup, "−")
    sub = re.search(r"<msub>.*?</msub>", out).group(0)
    assert mo(sub, "−") == ' lspace="0" rspace="0"'         # no Bin space in a script
    assert re.search(r'<mo lspace="0.2778em" rspace="0">=</mo><mo lspace="0.2778em" '
                     r'rspace="0">−</mo>', out)                      # = then a unary minus


def test_limits_under_in_display_beside_in_text():
    assert "<munderover><mo" in mm(r"\sum_{i=1}^{n} x_i", True)
    assert "<msubsup><mo" in mm(r"\sum_{i=1}^{n} x_i")
    assert "<munder><mi>max</mi>" in mm(r"\max_\theta f", True)
    assert "<msub><mi>max</mi>" in mm(r"\max_\theta f")
    assert "<msubsup><mo" in mm(r"\int_0^1 f", True)                  # an integral: beside


def test_fractions_roots_accents():
    assert "<mfrac><mi>a</mi><mi>b</mi></mfrac>" in mm(r"\frac{a}{b}", True)
    assert "<msqrt>" in mm(r"\sqrt{x^2+y^2}") and "<mroot>" in mm(r"\sqrt[3]{x}")
    assert '<mover accent="true"><mi>y</mi><mo stretchy="false">ˆ</mo></mover>' in mm(r"\hat{y}")
    assert '<mo stretchy="false">¯</mo>' in mm(r"\bar{m}")


def test_delimiters_never_stretch_unasked():
    out = mm(r"f(x) + [a] + |b| + \lVert c \rVert")
    for ch in "()[]|‖":
        assert 'stretchy="false"' in mo(out, ch)
    assert 'stretchy="true"' in mm(r"\left( \frac{a}{b} \right)")
    assert 'minsize="1.2em"' in mm(r"\bigl( a \bigr)")


def test_text_and_units():
    out = mm(r"9.81\,\mathrm{m/s^2}")
    assert out.count('<mspace width="0.1667em"/>') == 1
    assert '<mi mathvariant="normal">m</mi>' in out and '<mi mathvariant="normal">s</mi>' in out
    assert "<mtext>credit_score</mtext>" in mm(r"\text{credit\_score}")
    assert mm(r"87{,}000").count('rspace="0"') >= 1 and "0.1667em" not in mm(r"87{,}000")
    assert "<mtext> bias </mtext>" in mm(r"\text{ bias }")   # its end spaces kept


def test_escaping_and_alttext():
    out = mm(r"a < b", alt='his "a<b" & c')
    assert 'alttext="his &quot;a&lt;b&quot; &amp; c"' in out
    assert "<mo lspace=\"0.2778em\" rspace=\"0.2778em\">&lt;</mo>" in out
    assert "<mtext>R&amp;D</mtext>" in mm(r"\text{R\&D}")


@pytest.mark.parametrize("tex", [r"\foo", "x^", "{x", "x}", r"\frac{a}", "a & b", r"\left( x",
                                 "x^1^2", r"\text{$x$}", "#", r"\begin{matrix}a\end{matrix}", ""])
def test_what_it_cannot_set_stops_the_build(tex):
    with pytest.raises(mathtex.MapError):
        mathtex.mathml(tex)


def test_a_glyph_site_math_lacks_stops_the_build():
    assert mathtex.missing_glyphs(mathtex.to_mathml(r"\mathbb{Z}")) == {"ℤ"}
    with pytest.raises(mathtex.MapError, match="U\\+2124"):
        mathtex.mathml(r"\mathbb{Z}")
    assert not mathtex.missing_glyphs(mm(r"\alpha^2 + \sum_{i} x_i \leq \infty"))


# ------------------------------------------------------------- italic correction

def test_italic_correction_after_a_bare_italic_letter():
    ic = mathtex._italic_correction(mathtex._italic("V"))
    assert ic == pytest.approx(0.214, abs=0.001)
    assert mm("V") == '<math class="im" alttext="V"><mi>V</mi><mspace width="0.214em"/></math>'
    # between the letter and its superscript, inside the base
    assert '<msup><mrow><mi>V</mi><mspace width="0.214em"/></mrow><mn>2</mn></msup>' in mm("V^2")
    # a letter with a subscript stays bare
    assert "<msub><mi>P</mi><mi mathvariant=\"normal\">A</mi></msub>" in mm(r"P_{\mathrm{A}}")
    # below IC_MIN it would only be markup
    assert "mspace" not in mm("b")


def test_superscript_of_a_letter_with_both_scripts_moves_past_its_correction():
    out = mm(r"C_j^{l(x)}")
    ic = mathtex._italic_correction(mathtex._italic("C"))
    shift = mathtex._em(ic / 0.7)
    assert f'<msubsup><mi>C</mi><mi>j</mi><mrow><mspace width="{shift}"/>' in out


def test_italic_corrections_come_from_the_font():
    fonttools = pytest.importorskip("fontTools.ttLib")
    font = fonttools.TTFont(mathtex.FONT)
    info = font["MATH"].table.MathGlyphInfo.MathItalicsCorrectionInfo
    corr = dict(zip(info.Coverage.glyphs, (v.Value for v in info.ItalicsCorrection)))
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    for letter in "VYTPFNf":
        ch = mathtex._italic(letter)
        assert mathtex._italic_correction(ch) == round(corr[cmap[ord(ch)]] / upm, 4)


# ------------------------------------------------------------- where lines break

LONG = (r"(\text{weight}_1 \times \text{square footage}) + (\text{weight}_2 \times "
        r"\text{number of bedrooms}) + \text{bias}")


def visible(out):
    """The pieces a reader sees (the whole formula, read aloud, is out of sight)."""
    return re.findall(r'<math class="im"(?: displaystyle="true")? aria-hidden="true" '
                      r'alttext="">(.*?)</math>', out)


def test_a_long_inline_formula_breaks_after_its_operators_only():
    his = "(weight1 × square footage) + (weight2 × number of bedrooms) + bias"
    out = mm(LONG, alt=his)
    # read: the whole formula, once, with his text; seen: its pieces
    assert out.startswith(f'<span class="im-sr"><math class="im" alttext="{his}">')
    assert out.count(f'alttext="{his}"') == 1 and "role=" not in out
    pieces = visible(out)
    assert len(pieces) == 5 and out.count("<wbr>") == 4
    for piece in pieces[:-1]:                     # each ends with × or +, and its space
        assert re.search(r'<mo lspace="0.2222em" rspace="0.2222em">[×+]</mo>$', piece)
    for piece in pieces[1:]:                      # and the next starts flush
        assert not re.match(r'<mo lspace="0\.', piece)


def test_never_inside_a_group_and_not_a_short_formula():
    out = mm(r"\text{a} + \left( \text{bb} + \text{cc} + \text{dd} + \text{ee} + \text{ff} \right) + g")
    pieces = visible(out)
    assert len(pieces) == 3 and "<mrow><mo" in pieces[1]      # the \left...\right group whole
    assert mm("Ax = b").startswith('<math class="im" alttext')  # short: one <math>
    assert "<wbr>" in mm(r"a \allowbreak b")                   # \allowbreak asks for one


def test_a_long_display_formula_breaks_before_a_relation():
    tex = (r"w_j(k+1) = w_j(k) + \eta(k) h_{j,y}(k) \bigl(u_s(k) - w_y(k)\bigr), "
           r"\quad j = 1, 2, \ldots, N_w")
    out = mm(tex, True)
    assert out.startswith('<span class="im-dm" style="--mw:')
    assert '<span class="im-sr"><math class="im" display="block" alttext=' in out  # read
    pieces = visible(out)
    plain = [re.sub(r"<[^>]+>|&#x2061;", "", p) for p in pieces]
    # "w_j(k+1) = w_j(k) + ...," is 22 em: wider than DISPLAY_PIECE, it may also
    # break before its + (not the − inside the brackets); then comes its clause,
    # whose first = stays
    assert plain == ["wj(k+1)=wj(k)", "+η(k)hj,y(k)(us(k)−wy(k)),", "j=1,2,…,Nw"]
    assert pieces[1].startswith('<mo lspace="0" rspace="0.2222em">+</mo>')
    widest = float(re.search(r"--mw:([\d.]+)", out).group(1))
    assert 10 < widest < mathtex.DISPLAY_PIECE
    short = mm(r"\frac{a}{b}", True)
    assert short.startswith('<math class="im" display="block" style="--mw:')


def test_the_client_formula_breaks_at_its_arrow():
    tex = (r"z = w_1 x_1 + w_2 x_2 + w_3 x_3 + \text{bias} \;\rightarrow\; \text{output}"
           r" = \text{activation}(z)")
    pieces = visible(mm(tex, True))
    assert pieces[1].startswith('<mo lspace="0" rspace="0.2778em" stretchy="false">→</mo>')
    assert pieces[2].startswith('<mo lspace="0" rspace="0.2778em">=</mo>')


# ------------------------------------------------------------- the maps

def doc(entries, *texts, runs=None):
    """A Document for a map of `entries` over paragraphs of one run each (or
    `runs`, one paragraph of several runs), written to a temporary map."""
    nodes = [{"type": "PARAGRAPH", "id": f"p{k}", "nodes": [
        {"type": "TEXT", "textData": {"text": t, "decorations": []}}]} for k, t in enumerate(texts)]
    if runs:
        nodes.append({"type": "PARAGRAPH", "id": "pr", "nodes": [
            {"type": "TEXT", "textData": {"text": t, "decorations": d}} for t, d in runs]})
    parsed = [mathtex.Entry(e, k, "content/math/test.json") for k, e in enumerate(entries, 1)]
    return mathtex.Document(os.path.join(ROOT, "content", "math", "test.json"), nodes, parsed), nodes


def test_find_with_context_and_count():
    d, _ = doc([{"find": "x", "before": "where ", "after": " is", "tex": "x", "count": 2}],
               "where x is the input, and where x is", "x marks nothing here: examples")
    assert [s[:2] for s in d.spans["where x is the input, and where x is"]] == [(6, 7), (32, 33)]
    parts = d.cut({"text": "where x is the input, and where x is"})
    assert [p[1] for p in parts] == [False, True, False, True, False]
    assert parts[0][0] == "where " and parts[2][0] == " is the input, and where "


def test_a_count_that_does_not_match_names_the_entry():
    with pytest.raises(mathtex.MapError, match=r"entry 1 \(find 'Ax = b'\): count 2, in the "
                                               r"document 1 time"):
        doc([{"find": "Ax = b", "tex": "Ax = b", "count": 2}], "boiled down to Ax = b, where")


def test_counts_as_str_count_does():
    d, _ = doc([{"find": "aa", "tex": "a", "count": 2}], "aaaa")      # never overlapping
    assert [s[:2] for s in d.spans["aaaa"]] == [(0, 2), (2, 4)]


@pytest.mark.parametrize("entries, message", [
    ([{"find": "x", "tex": "x", "count": 1, "befor": "a"}], "unknown key"),
    ([{"find": "x", "tex": "x"}], "no 'count'"),
    ([{"find": "", "tex": "x", "count": 1}], "empty find"),
    ([{"find": "x", "tex": "x", "count": 0}], "count is a whole number"),
    ([{"find": "x", "tex": r"\nope", "count": 1}], r"\\nope is not a command"),
])
def test_a_bad_entry_stops_the_build(entries, message):
    with pytest.raises(mathtex.MapError, match=message):
        doc(entries, "x")


def test_two_entries_on_the_same_characters_stop_the_build():
    with pytest.raises(mathtex.MapError, match="claim the same characters"):
        doc([{"find": "Ax = b", "tex": "Ax = b", "count": 1},
             {"find": "x", "before": "A", "tex": "x", "count": 1}], "so Ax = b holds")


def test_a_joined_find_crosses_runs_and_keeps_shared_decorations():
    italic = [{"type": "ITALIC"}]
    runs = [("patterns, ", []), ("P", italic), (" = ", []), ("P", italic), ("_A", []),
            (" + ", []), ("P", italic), ("_B", []), (", with no", [])]
    d, nodes = doc([{"find": "P = P_A + P_B", "tex": r"P = P_A + P_B", "count": 1,
                     "joined": True}], runs=runs)
    out = d.join(nodes[0]["nodes"])
    texts = [n["textData"]["text"] for n in out]
    assert texts == ["patterns, ", "P = P_A + P_B", ", with no"]
    assert out[1]["textData"]["mathtex"] == 1 and out[1]["textData"]["decorations"] == []
    assert d.cut(out[1]["textData"])[0][1] is True
    d.verify()


def test_a_formula_the_page_did_not_draw_stops_the_build():
    d, _ = doc([{"find": "x", "before": "the ", "tex": "x", "count": 1}], "the x axis")
    d.rendered = True
    with pytest.raises(mathtex.MapError, match="drawn 0"):
        d.verify()


def test_begin_finds_the_document_by_its_text(tmp_path, monkeypatch):
    maps, ricos = tmp_path / "math", tmp_path / "ricos"
    (ricos / "a-doc").mkdir(parents=True)
    maps.mkdir()
    nodes = [{"type": "PARAGRAPH", "id": "n1", "nodes": [
        {"type": "TEXT", "textData": {"text": "so Ax = b holds", "decorations": []}}]}]
    (ricos / "a-doc" / "part-01.json").write_text(json.dumps({"nodes": nodes}), encoding="utf-8")
    (maps / "a-doc.json").write_text(json.dumps({"entries": [
        {"find": "Ax = b", "tex": "Ax = b", "count": 1}]}), encoding="utf-8")
    monkeypatch.setattr(mathtex, "MAPS", str(maps))
    monkeypatch.setattr(mathtex, "RICOS", str(ricos))
    monkeypatch.setattr(mathtex, "_INDEX", None)
    try:
        preview.plan(nodes)
        assert mathtex.active() is not None
        out = preview.inline(nodes[0]["nodes"])
        assert out.startswith('so <math class="im" alttext="Ax = b">')   # alone: nothing held
        assert out.endswith("</math> holds")
    finally:
        preview.plan([])
    assert mathtex.active() is None
    preview.plan([{"type": "PARAGRAPH", "id": "n1", "nodes": [
        {"type": "TEXT", "textData": {"text": "another document", "decorations": []}}]}])
    try:
        assert mathtex.active() is None                   # no map: nothing is math
    finally:
        preview.plan([])
    # a map named for no document stops the build
    (maps / "gone.json").write_text('{"entries": []}', encoding="utf-8")
    monkeypatch.setattr(mathtex, "_INDEX", None)
    with pytest.raises(mathtex.MapError, match="no document gone"):
        preview.plan(nodes)
    preview.plan([])


# ------------------------------------------------------------- text_node and the glue

@pytest.fixture
def active(monkeypatch):
    """A document with a map, active as preview.plan() would make it."""
    def make(entries, *texts, runs=None):
        d, nodes = doc(entries, *texts, runs=runs)
        monkeypatch.setattr(mathtex, "_DOC", d)
        return d, nodes
    yield make
    mathtex._DOC = None


def test_text_node_escapes_his_text_and_sets_the_formula(active):
    _, nodes = active([{"find": "x < y", "tex": "x < y", "count": 1}], "if x < y & z")
    out = preview.text_node(nodes[0]["nodes"][0])
    assert out.startswith("if <math") and out.endswith("</math> &amp; z")
    assert 'alttext="x &lt; y"' in out


def test_a_run_all_formula_drops_its_italic_keeps_its_link(active):
    run = {"type": "TEXT", "textData": {"text": "K", "decorations": [
        {"type": "ITALIC"}, {"type": "LINK", "linkData": {"link": {"url": "https://x.org"}}}]}}
    _, _ = active([{"find": "K", "tex": "K", "count": 1}], "K")
    out = preview.text_node(run)
    assert "<em>" not in out and out.startswith('<a href="https://x.org"')


def test_glue_runs_from_space_to_space(active):
    _, nodes = active([{"find": "H1", "before": "(", "tex": "H_1", "count": 1},
                       {"find": "H2", "after": ")", "tex": "H_2", "count": 1},
                       {"find": "k", "after": "-means", "tex": "k", "count": 1}],
                      "the (H1/H2) estimators and k-means, done")
    out = preview.inline(nodes[0]["nodes"])
    units = re.findall(r'<span class="im-nb">(.*?)</span>(?= |$)', out)
    plain = [re.sub(r"<math.*?</math>", "M", u) for u in units]
    assert plain == ["(M/M)", "M-means,"]


def test_glue_crosses_runs(active):
    italic = [{"type": "ITALIC"}]
    runs = [("with ", []), ("V", italic), ("² + ", []), ("D", italic), ("² ≤ 1, where", [])]
    _, nodes = active([{"find": "V² + D² ≤ 1", "tex": r"V^2 + D^2 \leq 1", "count": 1,
                        "joined": True}], runs=runs)
    out = preview.inline(nodes[0]["nodes"])
    assert re.search(r'<span class="im-nb"><math class="im"[^>]*>.*?</math>,</span> where$', out)


def test_a_long_formula_is_held_by_its_first_and_last_pieces_only(active):
    his = "(weight1 × square footage) + (weight2 × number of bedrooms) + bias"
    _, nodes = active([{"find": his, "tex": LONG, "count": 1}], f"predicted as {his}. The model")
    out = preview.inline(nodes[0]["nodes"])
    # no break opportunity inside a span that may not wrap: Firefox would not
    # take it there, and the line would run past the column
    units = re.findall(r'<span class="im-nb">(.*?)</span>', out)
    assert len(units) == 1 and "<wbr>" not in units[0]
    assert units[0].endswith("</math>.")                         # the last piece and his period
    assert out.startswith('predicted as <span class="im-sr">')     # a space before: nothing held
    assert out.count("<wbr>") == 4 and out.endswith("</span> The model")


def test_a_display_formula_is_never_held(active):
    _, nodes = active([{"find": "E = mc^2", "tex": "E = mc^2", "count": 1, "display": True}],
                      "so E = mc^2.")
    out = preview.inline(nodes[0]["nodes"])
    assert "im-nb" not in out and 'display="block"' in out


# ------------------------------------------------------------- the blog's <tex>

def test_typed_tex_elements():
    out = mathtex.typed('<p>the <tex>w_j</tex>’s and <tex>a &lt; b</tex>.</p>\n'
                        '<div class="eq"><tex display>\\frac{a}{b}</tex><span>(1)</span></div>',
                        "content/blog/x/text/a.html")
    assert '<span class="im-nb"><math class="im" alttext="w_j">' in out
    assert "</math>’s</span>" in out
    assert 'alttext="a &lt; b"' in out and "</math>.</span>" in out
    assert '<div class="eq"><math class="im" display="block"' in out     # display: not held
    assert "<tex" not in out


@pytest.mark.parametrize("markup, message", [
    ("<tex inline>x</tex>", "only <tex> and <tex display>"),
    ("<tex><i>x</i></tex>", "markup inside"),
    ("<tex>x", "does not close"),
    ("<tex>\\nope</tex>", "line 1"),
])
def test_typed_tex_that_cannot_be_set_stops_the_build(markup, message):
    with pytest.raises(mathtex.MapError, match=message):
        mathtex.typed(markup, "content/blog/x/text/a.html")


# ------------------------------------------------------------- his pictures of formulas

def picture_doc(monkeypatch, count=2, display=True, alt=None):
    nodes = [{"type": "IMAGE", "id": "n1", "imageData": {"image": {"src": {"id": "image16.png"}}}},
             {"type": "PARAGRAPH", "id": "n2", "nodes": [
                 {"type": "IMAGE", "id": "n3", "imageData": {"image": {"src": {"id": "image16.png"}}}}]}]
    raw = {"picture": "image16", "tex": r"u = U\, e^{i\omega t}", "count": count, "display": display}
    if alt:
        raw["alt"] = alt
    d = mathtex.Document(os.path.join(ROOT, "content", "math", "test.json"), nodes,
                         [mathtex.Entry(raw, 1, "content/math/test.json")])
    monkeypatch.setattr(mathtex, "_DOC", d)
    return d


IMG = ('<img class="eq" src="../fig/doc/image16.webp" alt="u = U e^(iωt)" width="484" '
       'height="38" loading="lazy" decoding="async">')


def test_a_picture_becomes_its_formula(monkeypatch):
    d = picture_doc(monkeypatch)
    body = (f"<p>a term of the form {IMG}. Substituting it</p>"
            f'<figure><a class="zoom" href="x"><img src="../fig/doc/image16.webp" alt="u = U e^(iωt)">'
            f"</a><figcaption>the term</figcaption></figure>")
    out = mathtex.pictures(body)
    assert "image16" not in out
    assert out.count('<math class="im" display="block"') == 2
    assert out.count('alttext="u = U e^(iωt)"') == 2
    # his period goes inside the display, after a thin space, as LaTeX sets it
    assert '<mspace width="0.1667em"/><mo lspace="0" rspace="0">.</mo></math> Substituting' in out
    assert '</math><p class="cap">the term</p>' in out
    d.verify()
    mathtex._DOC = None


def test_a_picture_count_or_alt_that_is_wrong_stops_the_build(monkeypatch):
    with pytest.raises(mathtex.MapError, match="count 3, in the document 2"):
        picture_doc(monkeypatch, count=3)
    d = picture_doc(monkeypatch, count=2)
    mathtex.pictures(f"<p>{IMG}</p>")
    d.rendered = True
    with pytest.raises(mathtex.MapError, match="drawn 1"):
        d.verify()
    picture_doc(monkeypatch, count=2)
    with pytest.raises(mathtex.MapError, match="no alt text"):
        mathtex.pictures('<p><img class="eq" src="../fig/doc/image16.webp" alt=""></p>')
    mathtex._DOC = None


# ------------------------------------------------------------- the font and the stylesheet

def test_site_math_keeps_its_math_table_and_every_character():
    fonttools = pytest.importorskip("fontTools.ttLib")
    for path in (mathtex.FONT, mathtex.FONT_BOLD):
        font = fonttools.TTFont(path)
        assert font.flavor == "woff2"
        assert "MATH" in font and font["MATH"].table.MathVariants.VertGlyphCount > 0
        assert font["name"].getDebugName(1) == "Site Math"
        assert mathtex.REPERTOIRE <= set(font.getBestCmap()) | mathtex._IGNORABLE
        assert "GSUB" not in font or not font["GSUB"].table.FeatureList.FeatureRecord
    bold = fonttools.TTFont(mathtex.FONT_BOLD)
    regular = fonttools.TTFont(mathtex.FONT)
    assert bold["OS/2"].usWeightClass == 700
    italic_x = 0x1D465
    assert bold.getBestCmap()[italic_x] != regular.getBestCmap()[italic_x]   # its own bold glyph


def test_the_stylesheet_sets_site_math_and_holds_formulas():
    css = docs.CSS
    assert "STIX" not in css and "Cambria" not in css
    assert 'src:url(fonts/site-math.woff2) format("woff2")' in css
    assert "font-weight:600 900" in css and "site-math-bold.woff2" in css
    assert ".docpage math.im{font-family:\"Site Math\",math;font-size:1.1em;font-weight:inherit" in css
    assert ".docpage .im-nb{white-space:nowrap}" in css and "im-bk" not in css
    assert ".docpage .im-sr{position:absolute;width:1px;height:1px;overflow:hidden;" in css
    assert "var(--mw" in css


def test_every_map_matches_its_document():
    assert mathtex._check([]) == 0
