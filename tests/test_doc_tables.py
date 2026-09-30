"""The documents' tables (site/preview.py _table, site/parts/docs.py).

The client, 27 Sep 2026: the tables must be excellent, the waves guide's fun
table first (Category | Schematic figure | Connection and explanation, ten
rows), then the ML guide's eighteen and Signal Processing's one. What these
hold:

- a row's name reads from its left edge and every value too; only a column
  of pictures and a one-row poster stay centred;
- a phone restacks every table but a small matrix: each value beside its
  column's name where every value is a phrase, under it otherwise, and no
  names at all where a picture and one text are all a row holds;
- Signal Processing's notes go under their row (tbl--notes);
- a group of rows that repeat a name (Classification five times) is marked,
  and every word he wrote is still there;
- a picture in a cell that a moving figure redraws is that figure: frame and
  still in one box (fig--cell), the still printed and shown with no script,
  the frame playing only while its row is read.
"""

import html
import inspect
import json
import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "site"))

import build  # noqa: E402
import preview  # noqa: E402
from parts import docs  # noqa: E402

WAVES = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
ML = "machine-learning-the-complete-picture-and-guide-5"
SP = "signal-processing-system-identification-and-optimization"
BROCHURE = "brochure-shm-and-ndt-2-pages"
BUILT = all(os.path.isfile(os.path.join(build.BUILD, s, "part-01.json"))
            for s in (WAVES, ML, SP, BROCHURE))


# ------------------------------------------------------------------ nodes

def text(t, bold=False, align="AUTO"):
    dec = [{"type": "BOLD", "fontWeightValue": 700}] if bold else []
    return {"type": "PARAGRAPH", "nodes": [{"type": "TEXT", "textData": {"text": t, "decorations": dec}}],
            "paragraphData": {"textStyle": {"textAlignment": align}}}


def image(stem, w=405, h=162, nid="i"):
    return {"type": "IMAGE", "id": nid, "nodes": [],
            "imageData": {"image": {"src": {"id": f"{stem}.png"}, "width": w, "height": h}}}


def cell(*blocks):
    return {"type": "TABLE_CELL", "nodes": list(blocks)}


def table(rows, head=True, ratios=None):
    data = {"rowHeader": head}
    if ratios:
        data["dimensions"] = {"colsWidthRatio": ratios}
    return {"type": "TABLE", "id": "t", "tableData": data,
            "nodes": [{"type": "TABLE_ROW", "nodes": [c if isinstance(c, dict) else cell(text(c))
                                                       for c in r]} for r in rows]}


def draw(node, anim=None, figs=None):
    preview.plan([node], figs or {}, anim)
    try:
        return preview.render(node, "../fig/d")
    finally:
        preview.plan([])


def plain(markup):
    """The words a reader sees: tags gone (a line break is a space). A formula
    set as math (site/mathtex.py) reads as his own text, which it keeps in its
    alttext, or in the aria-label of the wrapper that holds its pieces: TeX's
    spaces are spacing, not characters."""
    markup = re.sub(r"<br\s*/?>", " ", markup)
    # the wrapper's body is its pieces and the break points between them
    markup = re.sub(r'<span[^>]*\brole="math"[^>]*\baria-label="([^"]*)"[^>]*>'
                    r'(?:<span class="im-bk"><wbr></span>|<math.*?</math>)*</span>',
                    lambda m: m.group(1), markup, flags=re.S)
    markup = re.sub(r'<math[^>]*\balttext="([^"]*)"[^>]*>.*?</math>', lambda m: m.group(1),
                    markup, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", markup))).strip()


def classes(out):
    return re.match(r'<div class="([^"]+)"', out).group(1).split()


# ------------------------------------------------------------------ alignment

def test_names_and_values_read_from_their_left_edge_whatever_word_did():
    c = "CENTER"
    rows = [["Model", "Interpretability", "Training speed"],
            [cell(text("Linear Regression", True, c)), cell(text("High", align=c)),
             cell(text("Very fast", align=c))],
            [cell(text("SVM", True, c)), cell(text("Low to medium (kernel-dependent)", align=c)),
             cell(text("Slow on large data", align=c))],
            [cell(text("KNN", True, c)), cell(text("Medium", align=c)), cell(text("Fast", align=c))]]
    out = draw(table(rows))
    assert ' class="c"' not in out
    assert out.count('<th scope="row"') == 3
    # his bold stays his
    assert "<strong>Linear Regression</strong>" in out


def test_a_one_row_poster_keeps_his_centring_and_a_column_of_pictures_is_centred():
    c = "CENTER"
    poster = table([["Inspect", "Monitor", "Model"],
                    [cell(text("Assess the current condition", align=c)),
                     cell(text("Perform long-term monitoring", align=c)),
                     cell(text("Update the numerical model", align=c))]])
    out = draw(poster)
    assert out.count('class="c"') == 6               # three heads and three values
    fun = table([["Category", "Schematic figure", "Connection and explanation"]]
                + [[cell(text(f"Field {k}", True, c)),
                    cell(image(f"image{k}", nid=f"i{k}"), text(f"Picture {k}", align=c)),
                    f"His explanation of field {k}, a sentence or two long."] for k in (2, 3, 4)])
    out = draw(fun)
    assert '<th scope="col" class="c pic"' in out
    assert out.count('<td class="c pic"') == 3
    assert '<th scope="row" role="rowheader">' in out


# ------------------------------------------------------------------ phones

def test_a_phone_restacks_every_table_but_a_small_matrix():
    confusion = table([["", "Predicted Positive", "Predicted Negative"],
                       ["Actually Positive", "True Positive (TP): caught", "False Negative (FN): missed it"],
                       ["Actually Negative", "False Positive (FP): a false alarm",
                        "True Negative (TN): cleared"]])
    out = draw(confusion)
    assert "tbl--scroll" in classes(out) and "tbl--stack" not in classes(out)
    assert 'role="region" tabindex="0"' in out and "data-label" not in out
    wrap_up = table([["", "Non-Neural Model", "Neural Network"]]
                    + [[f"Aspect {k}", f"Short value {k} here", f"Other value {k} here"] for k in range(6)])
    out = draw(wrap_up)
    assert "tbl--stack" in classes(out) and 'role="table"' in out
    seven = table([["Model"] + [f"Property {j}" for j in range(6)]]
                  + [[f"Model {k}"] + [f"Yes (reason {j})" for j in range(6)] for k in range(8)])
    out = draw(seven)
    assert {"tbl--stack", "tbl--dense", "tbl--kv"} <= set(classes(out))


def test_a_value_is_named_beside_it_when_every_value_is_a_phrase():
    rows = [["Set", "What It's For", "When You Touch It"],
            ["Training set", "The model learns its weights from this data.", "Constantly."],
            ["Validation set", "Used to tune hyperparameters.", "Repeatedly."],
            ["Test set", "Held back until the very end.", "Once."]]
    out = draw(table(rows))
    assert "tbl--kv" in classes(out)
    assert out.count('data-label="What It&#x27;s For"') == 3
    listed = [["Domain", "Non-Neural Model Use Cases", "Neural Network Use Cases"]] + [
        [f"Domain {k}", cell(text("One use"), {"type": "BULLETED_LIST", "nodes": []}), "Other use"]
        for k in range(3)]
    assert "tbl--kv" not in classes(draw(table(listed)))


def test_a_picture_and_one_text_need_no_names_on_a_phone():
    fun = table([["Category", "Schematic figure", "Connection and explanation"]]
                + [[cell(text(f"Field {k}", True)), cell(image(f"image{k}", nid=f"i{k}")),
                    f"His explanation of field {k}."] for k in (2, 3, 4)])
    out = draw(fun)
    assert "tbl--fig" in classes(out) and "data-label" not in out
    # two texts to tell apart are named
    two = table([["Aspect", "Bulk wave", "Guided wave"]]
                + [[f"Aspect {k}", f"Bulk value {k}", f"Guided value {k}"] for k in range(3)])
    assert draw(two).count("data-label=") == 6


def test_a_column_of_notes_among_phrases_goes_under_its_row():
    note = "The clearest cross-field link in the table: one method, three names, and more."
    rows = [["Method", "Field(s)", "Estimation theory?", "Optimization?", "Notes / cross-field links"]]
    rows += [[f"Method {k}", "Signal processing", "Yes (it's MLE)", "No", note] for k in range(4)]
    out = draw(table(rows))
    got = set(classes(out))
    assert {"tbl--notes", "tbl--stack", "tbl--kv"} <= got and "tbl--many" not in got
    # five columns of phrases stay a grid of short values
    short = [rows[0]] + [[f"Method {k}", "Signal processing", "Yes", "No", "Same as above."]
                         for k in range(4)]
    assert "tbl--notes" not in classes(draw(table(short)))


def test_rows_that_repeat_a_name_are_one_group_and_keep_every_word():
    rows = [["Task", "Metric", "What It Tells You"],
            ["Classification", "Accuracy", "Overall fraction correct."],
            ["Classification", "Precision", "How trustworthy a positive prediction is."],
            ["Classification", "Recall", "How many real positives it caught."],
            ["Regression", "MAE", "Average size of the error."],
            ["Regression", "RMSE", "Like MAE, but harder on large errors."]]
    out = draw(table(rows))
    trs = re.findall(r"<tr([^>]*)>", out)[1:]
    assert ['tr-same' in t for t in trs] == [False, True, True, False, True]
    assert plain(out).count("Classification") == 3 and plain(out).count("Regression") == 2
    for r in rows[1:]:
        for c in r:
            assert c in plain(out)


# ------------------------------------------------------------------ pictures in cells

NF = {"src": "../anim/nf-string.html", "title": "A vibrating string", "w": 1000, "h": 400,
      "still": {"src": "../anim/nf-string.webp", "w": 1344, "h": 538}}
FIGS = {"i2": {"src": "../fig/d/image2.webp", "w": 406, "h": 162}}


def fun_table():
    return table([["Category", "Schematic figure", "Connection and explanation"],
                  [cell(text("Music and acoustics", True)),
                   cell(image("image2", nid="i2"), text("Vibrating string", align="CENTER")),
                   "A guitar string supports standing waves."]])


def test_a_picture_in_a_cell_becomes_its_moving_figure_frame_and_still_in_one_box():
    out = draw(fun_table(), {"image2": NF}, FIGS)
    fig = re.search(r'<figure class="fig--anim fig--cell">(.*?)</figure>', out).group(1)
    assert fig.startswith('<iframe class="anim" src="../anim/nf-string.html" '
                          'title="A vibrating string" loading="lazy" style="aspect-ratio:1000/400">'
                          '</iframe>')
    # the figure's own printed frame, not the Word picture it redraws
    assert re.search(r'<img class="anim__still" src="\.\./anim/nf-string\.webp" alt="" '
                     r'width="1344" height="538" loading="lazy"', fig)
    assert "image2" not in fig
    # his label stays under it, in the same cell
    assert re.search(r"</figure><p[^>]*>Vibrating string</p></td>", out)
    # the same contract as a figure's frame: _animated() writes it
    block = preview._animated(NF, 'src="x"', "")
    assert block.startswith('<figure class="fig--anim"><iframe class="anim" ')


def test_his_own_animation_in_a_cell_stands_on_the_picture_at_half_its_pixels():
    his = {k: v for k, v in NF.items() if k != "still"}
    out = draw(fun_table(), {"image2": his}, FIGS)
    assert '<figure class="fig--anim fig--cell" style="max-width:203px">' in out
    assert re.search(r'<img class="anim__still" src="\.\./fig/d/image2\.webp" alt="" '
                     r'width="203" height="81"', out)


def test_a_picture_no_figure_redraws_stays_a_picture_at_half_its_pixels():
    out = draw(fun_table(), {"image9": NF}, FIGS)
    assert "fig--cell" not in out and "<iframe" not in out
    assert '<figure><img src="../fig/d/image2.webp" alt="" width="203" height="81" loading="lazy"' in out
    assert preview.USAGE["../fig/d/image2.webp"] >= {"bare"}
    # the plan is the document's: the next one draws no frame
    assert "<iframe" not in draw(fun_table(), None, FIGS)


# ------------------------------------------------------------------ the stylesheet and script

def rule(css, selector):
    m = re.search(re.escape(selector) + r"\{([^}]*)\}", css)
    assert m, selector
    return m.group(1)


def test_one_rows_figure_moves_at_a_time_and_every_other_shows_its_still():
    css = docs.CSS
    parked = rule(css, ".js .docpage .tbl .fig--cell .anim")
    assert "opacity:0" in parked and "visibility:hidden" in parked
    assert "transform:translateX(-300vw)" in parked
    live = rule(css, ".js .docpage .tbl .is-live .fig--cell.is-ready .anim")
    assert "opacity:1" in live and "transform:none" in live and "visibility:visible" in live
    assert "opacity:0" in rule(css, ".js .docpage .tbl .is-live .fig--cell.is-ready .anim__still")
    assert "display:block" in rule(css, ".js .docpage .tbl .fig--cell .anim__still")
    # less motion: every frame shown, still, as a figure's is
    calm = css.split("@media (prefers-reduced-motion:reduce){", 1)[1].split("\n}", 1)[0]
    assert ".js .docpage .tbl .fig--cell .anim{opacity:1;visibility:visible;transform:none" in calm
    assert ".js .docpage .tbl .fig--cell .anim__still{display:none}" in calm
    # paper: the still
    paper = css.split("@media print{", 1)[1]
    assert ".docpage .tbl .fig--cell .anim__still{display:block!important;opacity:1!important}" in paper
    assert ".docpage .tbl :is(thead,thead tr){break-after:avoid}" in paper
    # colour and opacity move on the state tokens, travel does not move at all
    for sel in (".js .docpage .tbl .fig--cell .anim", ".js .docpage .tbl .fig--cell .anim__still"):
        assert "var(--ease-state)" in rule(css, sel)


def test_the_script_plays_the_row_being_read_and_parks_the_rest_out_of_the_tab_order():
    js = docs.JS
    part = js[js.index("a table's moving figures"):js.index("/* the card's fold")]
    assert "rootMargin:'-40% 0px -59% 0px'" in part        # a line two fifths down
    assert "rootMargin:'100% 0px'" in part and "loading='eager'" in part
    assert "prefers-reduced-motion: reduce" in part
    assert "inert=true" in part and "inert=false" in part
    assert "is-live" in part and "is-ready" in part
    # its own scope, before the contents dock's early return: the dock's
    # `rows` and `return` are not touched
    assert "(function(){" in part and part.rstrip().endswith("})();")
    assert js.index("a table's moving figures") < js.index("if(!page||!root.hasAttribute('data-toc'))return;")


def test_tables_hover_nothing_and_carry_no_dashes():
    css = docs.CSS
    start = css.index("/* ---------- tables: set as a book sets them ---------- */")
    end = css.index("/* ---------- a row of steps with his arrows between ---------- */")
    tables = css[start:end] + docs._STACK
    assert ":hover" not in tables and "box-shadow" not in tables
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", tables)     # colours from tokens only
    for src in (tables, docs.JS, inspect.getsource(preview._table), inspect.getsource(preview._in_cell),
                inspect.getsource(preview._column_align), inspect.getsource(preview._beside)):
        assert "—" not in src and not build.SPACED_EN.search(src)


def test_the_phone_rules_serve_a_phone_and_a_narrow_screen_for_the_seven_column_table():
    css = docs.CSS
    assert '@media (max-width:640px){\n  .docpage .tbl--stack :is(table,thead,tbody,tr,th,td)' in css
    assert ("@media (min-width:641px) and (max-width:700px){\n"
            "  .docpage .tbl--stack.tbl--dense :is(table,thead,tbody,tr,th,td)") in css
    assert "%T%" not in css


# ------------------------------------------------------------------ his documents

def tables_of(page):
    return re.findall(r'<div class="(tbl[^"]*)"[^>]*>(.*?)</table></div>', page, re.S)


@pytest.fixture
def page(monkeypatch):
    monkeypatch.setattr(build, "VERBATIM", [])

    def _page(slug, anim=None):
        monkeypatch.setattr(build, "ANIM", anim or {})
        return build.page_doc(slug)
    return _page


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
def test_the_fun_table_a_picture_beside_each_field_and_each_can_move(page):
    got = tables_of(page(WAVES))
    cls, fun = got[0]
    assert "tbl--fig" in cls.split() and "data-label" not in fun
    assert fun.count('<th scope="row"') == 10 and fun.count('<td class="c pic"') == 10
    for name in ("Structural dynamics", "Music and acoustics", "Fluid mechanics",
                 "Seismology and acoustic emission", "Optical fibers", "Quantum mechanics",
                 "Electromagnetics", "Lasers and optics", "Electrical circuits"):
        assert f"<strong>{name}</strong>" in fun
    moving = {WAVES: {f"image{k}": {**NF, "src": f"../anim/nf-t{k}.html"} for k in range(2, 12)}}
    fun = tables_of(page(WAVES, moving))[0][1]
    assert fun.count('<figure class="fig--anim fig--cell">') == 10
    assert [int(k) for k in re.findall(r"nf-t(\d+)\.html", fun)] == list(range(2, 12))


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
def test_the_guides_tables_take_the_shapes_their_content_asks_for(page):
    ml = tables_of(page(ML))
    assert len(ml) == 18
    kinds = [set(c.split()) for c, _ in ml]
    assert {"tbl--dense", "tbl--kv", "tbl--stack"} <= kinds[6]          # Table 1, seven columns
    assert "tbl--scroll" in kinds[15]                                   # the confusion matrix
    assert sum("tbl--scroll" in k for k in kinds) == 1
    assert ml[16][1].count('class="tr-same"') == 5                      # Classification, Regression
    assert ' class="c"' not in ml[6][1]                                  # Table 1 reads from the left
    sp = tables_of(page(SP))
    assert len(sp) == 1 and {"tbl--notes", "tbl--kv"} <= set(sp[0][0].split())
    assert sp[0][1].count("<tr") == 29


@pytest.mark.skipif(not BUILT, reason="build/ricos is written by tools/docx2ricos.py")
@pytest.mark.parametrize("slug", [WAVES, ML, SP, BROCHURE])
def test_every_word_of_his_tables_is_on_the_page(slug, page):
    with open(os.path.join(build.BUILD, slug, "part-01.json"), encoding="utf-8") as fh:
        nodes = json.load(fh)["nodes"]
    shown = plain(page(slug))
    for t in (n for n in nodes if n.get("type") == "TABLE"):
        for row in t["nodes"]:
            for c in row["nodes"]:
                for p in c.get("nodes", []):
                    words = " ".join(preview._text(p).split())
                    if words and p.get("type") == "PARAGRAPH":
                        assert words in shown, words[:60]
