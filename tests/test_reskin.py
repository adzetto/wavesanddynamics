"""tools/numfig/reskin.py: a figure page rebuilt with the current frame,
engine and script, keeping every number it holds (README.md, "Restyling a
figure")."""

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "numfig"))

import common  # noqa: E402
import reskin  # noqa: E402

PAGES = sorted(f for f in os.listdir(common.ANIM) if f.startswith("nf-") and f.endswith(".html"))
with open(os.path.join(ROOT, "tools", "numfig", "engine.js"), encoding="utf-8") as _fh:
    ENGINE = _fh.read()


@pytest.mark.parametrize("page", PAGES)
def test_every_page_is_the_current_frame_and_engine_and_its_own_numbers_and_script(page):
    with open(os.path.join(common.ANIM, page), encoding="utf-8") as fh:
        s = fh.read()
    held, engine, script = reskin.split(s)
    # a restyle of the frame or the engine reaches every page (reskin.py --all)
    assert engine == ENGINE, f"{page}: built with another engine.js; run reskin.py"
    assert common.HEAD.format(**held) + engine + "\n" + script + reskin.TAIL == s


SOURCE = '''JS = LIB + r"""
const R = 4;
function draw() {
  text('number of neurons', 10, 20, { size: 15, color: C.body });
  rect(0, 0, 9, 9, { fill: '#fff', stroke: C.guide });
}
boot();
"""
'''
SCRIPT = ("const LIB = 1;\nconst R = 4;\nfunction draw() {\n"
          "  text('number of neurons', 10, 20, { size: 15, color: C.body });\n"
          "  rect(0, 0, 9, 9, { fill: '#fff', stroke: C.guide });\n}\nboot();")


def edit(old, new, script=SCRIPT):
    src = SOURCE.replace(old, new)
    edits = reskin.changes(reskin.literals(SOURCE, {"JS"}), reskin.literals(src, {"JS"}), "test")
    return reskin.patch(script, edits, "test")


def test_an_edit_to_a_generators_script_is_made_in_its_page_and_nothing_else():
    assert edit("stroke: C.guide", "stroke: C.rule") == SCRIPT.replace("stroke: C.guide", "stroke: C.rule")
    added = "  dot(1, 2, 3);\n"
    assert edit("boot();", added + "boot();") == SCRIPT.replace("}\nboot();", "}\n" + added + "boot();")
    assert edit("const R = 4;\n", "") == SCRIPT.replace("const R = 4;\n", "")


def test_a_passage_found_twice_is_widened_until_it_is_found_once():
    # a library put before the figure's script holds the same lines
    lib = SCRIPT[SCRIPT.index("function draw()"):]
    got = edit("{ fill: '#fff', stroke: C.guide }", "{ fill: C.steel, stroke: C.guide }", lib + "\n" + SCRIPT)
    # the generator's line changed; the library's copy of it did not
    assert got == lib + "\n" + SCRIPT.replace("fill: '#fff'", "fill: C.steel")


def test_a_page_whose_script_lacks_the_edited_passage_is_refused():
    with pytest.raises(SystemExit, match="found 0 times"):
        edit("stroke: C.guide", "stroke: C.rule", SCRIPT.replace("C.guide", "C.navy"))


def test_an_edit_to_an_f_strings_value_is_refused():
    old = 'JS = f"const T0 = {T0};" + r"""\nboot();\n"""\n'
    new = 'JS = f"const T0 = {T0 + 1};" + r"""\nboot();\n"""\n'
    old_l, new_l = reskin.literals(old, {"JS"}), reskin.literals(new, {"JS"})
    assert old_l == new_l          # the value is not the generator's text: nothing to carry over
    changed = 'JS = f"const T1 = {T0};" + r"""\nboot();\n"""\n'
    with pytest.raises(SystemExit, match="f-string"):
        reskin.patch("const T0 = 1.5;\nboot();",
                     reskin.changes(old_l, reskin.literals(changed, {"JS"}), "test"), "test")
