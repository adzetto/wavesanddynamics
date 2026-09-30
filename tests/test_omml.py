"""Equations: Word's own (OMML) read as one line of text, and MathType counted.

None of the seven documents holds an equation - the measurement is zero
`m:oMath`, zero `w:object`, zero EMF - and the project record says the next
ones will: the author writes with MathType installed and is told to convert
to Word's own format before exporting. Today an `m:oMath` is a child of the
paragraph that `_runs` never looks at, so the equation vanished from the
sentence with nothing said, and a MathType object went the same way.

Ricos has no equation node. What can be kept exactly is the text: OMML's
characters are already Unicode (α, ∑, ∫), and its structure - fractions,
scripts, radicals, limits - reads back as the linear notation Word itself
offers under "Linear", which is what a reader of these documents types.
"""

import pytest
from lxml import etree

from tools.ricos.docx_read import read_blocks
from tools.ricos.omml import linear

NS = (
    'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
)


def omath(inner):
    return f"<m:oMath {NS}>{inner}</m:oMath>"


def r(text):
    return f"<m:r><m:t>{text}</m:t></m:r>"


def e(inner):
    return f"<m:e>{inner}</m:e>"


@pytest.mark.parametrize(
    ("inner", "text"),
    [
        (r("a+b"), "a+b"),
        # a fraction: single tokens stand bare, anything longer is grouped
        (f"<m:f><m:num>{r('a')}</m:num><m:den>{r('b')}</m:den></m:f>", "a/b"),
        (f"<m:f><m:num>{r('a+b')}</m:num><m:den>{r('2')}</m:den></m:f>", "(a+b)/2"),
        # scripts: a glyph where Unicode has one, Word's linear notation where not
        (f"<m:sSup>{e(r('x'))}<m:sup>{r('2')}</m:sup></m:sSup>", "x²"),
        (f"<m:sSup>{e(r('e'))}<m:sup>{r('iωt')}</m:sup></m:sSup>", "e^(iωt)"),
        (f"<m:sSub>{e(r('P'))}<m:sub>{r('A')}</m:sub></m:sSub>", "P_A"),
        (f"<m:sSub>{e(r('x'))}<m:sub>{r('i')}</m:sub></m:sSub>", "xᵢ"),
        (
            f"<m:sSubSup>{e(r('x'))}<m:sub>{r('i')}</m:sub><m:sup>{r('2')}</m:sup></m:sSubSup>",
            "xᵢ²",
        ),
        # a radical, with and without a degree
        (
            f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/>{e(r("k/m"))}</m:rad>',
            "√(k/m)",
        ),
        (f"<m:rad><m:deg>{r('3')}</m:deg>{e(r('x'))}</m:rad>", "∛x"),
        (f"<m:rad><m:deg>{r('n')}</m:deg>{e(r('x'))}</m:rad>", "√(n&x)"),
        # delimiters, with Word's defaults and with the author's own
        (f"<m:d>{e(r('a+b'))}</m:d>", "(a+b)"),
        (
            f'<m:d><m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>{e(r("x"))}{e(r("y"))}</m:d>',
            "[x|y]",
        ),
        # a sum with limits, an integral with none
        (
            f'<m:nary><m:naryPr><m:chr m:val="∑"/></m:naryPr><m:sub>{r("i=1")}</m:sub>'
            f"<m:sup>{r('n')}</m:sup>{e(r('a'))}</m:nary>",
            "∑ᵢ₌₁ⁿ a",
        ),
        (
            f'<m:nary><m:naryPr><m:subHide m:val="1"/><m:supHide m:val="1"/></m:naryPr>'
            f"<m:sub/><m:sup/>{e(r('f(x) dx'))}</m:nary>",
            "∫ f(x) dx",
        ),
        # a function and a limit under it
        (f"<m:func><m:fName>{r('sin')}</m:fName>{e(r('θ'))}</m:func>", "sin θ"),
        (
            f"<m:func><m:fName>{r('sin')}</m:fName>{e(f'<m:d>{e(r('x+1'))}</m:d>')}</m:func>",
            "sin(x+1)",
        ),
        (
            f"<m:func><m:fName><m:limLow>{e(r('lim'))}<m:lim>{r('x→0')}</m:lim></m:limLow>"
            f"</m:fName>{e(r('f'))}</m:func>",
            "lim_(x→0) f",
        ),
        # a bar and an accent on one letter
        (f"<m:bar>{e(r('x'))}</m:bar>", "x̅"),
        (f'<m:acc><m:accPr><m:chr m:val="̇"/></m:accPr>{e(r("x"))}</m:acc>', "ẋ"),
        (f"<m:acc>{e(r('x'))}</m:acc>", "x̂"),
        # a matrix reads row by row, an equation array line by line
        (
            f'<m:d><m:dPr><m:begChr m:val="["/><m:endChr m:val="]"/></m:dPr>{
                e(
                    f"<m:m><m:mr>{e(r('1'))}{e(r('2'))}</m:mr><m:mr>{e(r('3'))}{e(r('4'))}</m:mr></m:m>"
                )
            }</m:d>',
            "[1 2; 3 4]",
        ),
        (f"<m:m><m:mr>{e(r('1'))}{e(r('2'))}</m:mr></m:m>", "[1 2]"),
        (f"<m:eqArr>{e(r('a=1'))}{e(r('b=2'))}</m:eqArr>", "a=1\nb=2"),
        # a phantom is spacing, a box is nothing, a control run is nothing
        (f"<m:phant>{e(r('x'))}</m:phant>{r('y')}", "y"),
        (
            f'<m:box>{e(r("x"))}</m:box><m:r><m:rPr><m:sty m:val="p"/></m:rPr><m:t>=</m:t></m:r>',
            "x=",
        ),
        # a plain Word run inside the equation
        ("<w:r><w:t>where </w:t></w:r>" + r("x"), "where x"),
    ],
)
def test_omml_reads_back_as_linear_text(inner, text):
    assert linear(etree.fromstring(omath(inner))) == text


def test_an_inline_equation_stays_in_its_sentence(docx_factory):
    body = (
        "<w:p><w:r><w:t>the natural frequency </w:t></w:r>"
        f"<m:oMath><m:f><m:num>{r('1')}</m:num><m:den>{r('2π')}</m:den></m:f>"
        f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/>{e(r("k/m"))}</m:rad></m:oMath>'
        "<w:r><w:t> of the system.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert [x.text for x in blocks[0].runs] == [
        "the natural frequency 1/(2π)√(k/m) of the system."
    ]


def test_a_display_equation_is_its_own_centred_paragraph(docx_factory):
    """`m:oMathPara` is Word's display mode: the equation on a line of its
    own, centred by default, with `m:jc` where the author moved it."""
    body = (
        f"<w:p><m:oMathPara><m:oMath>{r('E=mc')}<m:sSup>{e(r('c'))}<m:sup>{r('2')}</m:sup></m:sSup>"
        "</m:oMath></m:oMathPara></w:p>"
        f'<w:p><m:oMathPara><m:oMathParaPr><m:jc m:val="left"/></m:oMathParaPr>'
        f"<m:oMath>{r('a')}</m:oMath><m:oMath>{r('b')}</m:oMath></m:oMathPara></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert [b.runs[0].text for b in blocks] == ["E=mcc²", "a\nb"]
    assert [b.align for b in blocks] == ["CENTER", "LEFT"]


def test_an_equation_inside_a_list_item_or_a_cell_is_read_too(docx_factory):
    body = (
        f"<w:tbl><w:tr><w:tc><w:p><m:oMath>{r('x')}</m:oMath></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>y</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
    )
    blocks = read_blocks(docx_factory(body))
    assert blocks[0].rows[0][0][0].runs[0].text == "x"
