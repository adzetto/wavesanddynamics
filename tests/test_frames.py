"""Paragraph borders: the asides he draws without a table, and the rules.

The one-cell table is not the only aside in these documents. Four of them
carry paragraphs with a left border, shading and an indent - a "Disclaimer"
box, a seven-paragraph digression in Understanding SHM and NDT - which is the
same box drawn with paragraph formatting instead of a table. Twenty paragraphs
in the corpus are framed that way, and they arrived on the page as ordinary
prose. A bottom border under the byline, or a top-and-bottom pair around a
closing line, is a rule; Signal Processing even has an empty paragraph whose
whole content is its bottom border, which is how Word draws a horizontal line.
"""

from conftest import para, picture, png

from tools.ricos.blocks import Callout, Figure, Para, Rule, Run, Table
from tools.ricos.docx_read import read_blocks
from tools.ricos.emit import emit


def bordered(text, *sides, style=None, shade=True):
    """A paragraph framed on `sides`, shaded the way the author's asides are."""
    edges = "".join(
        f'<w:{s} w:val="single" w:sz="24" w:color="8A0000"/>' for s in sides
    )
    shd = '<w:shd w:val="clear" w:fill="FBEAEA"/>' if shade else ""
    st = f'<w:pStyle w:val="{style}"/>' if style else ""
    run = f"<w:r><w:t>{text}</w:t></w:r>" if text else ""
    return f"<w:p><w:pPr>{st}<w:pBdr>{edges}</w:pBdr>{shd}</w:pPr>{run}</w:p>"


def kinds(blocks):
    return [type(b).__name__ for b in blocks]


def test_a_paragraph_with_a_left_border_is_an_aside(docx_factory):
    blocks = read_blocks(
        docx_factory(bordered("Disclaimer #1: my own experience.", "left"))
    )
    assert kinds(blocks) == ["Callout"]
    assert blocks[0].blocks[0].runs[0].text == "Disclaimer #1: my own experience."


def test_consecutive_framed_paragraphs_are_one_aside(docx_factory):
    """Understanding SHM and NDT frames seven paragraphs in a row: one box."""
    body = (
        para("before") + bordered("a", "left") + bordered("b", "left") + para("after")
    )
    blocks = read_blocks(docx_factory(body))
    assert kinds(blocks) == ["Para", "Callout", "Para"]
    assert [b.runs[0].text for b in blocks[1].blocks] == ["a", "b"]


def test_a_plain_paragraph_between_two_framed_ones_makes_two_asides(docx_factory):
    body = bordered("a", "left") + para("gap") + bordered("b", "left")
    assert kinds(read_blocks(docx_factory(body))) == ["Callout", "Para", "Callout"]


def test_a_picture_breaks_the_aside_and_its_framed_caption_still_folds(docx_factory):
    """The same document puts a picture inside a framed stretch: the picture's
    own paragraph is not framed, its caption is. Captions fold first, so the
    framed caption goes to the picture and not into a box of its own."""
    body = (
        bordered("a", "left")
        + f"<w:p>{picture()}</w:p>"
        + bordered("Figure 4. Waves in a beam.", "left")
        + bordered("b", "left")
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(4, 4)},
        )
    )
    assert kinds(blocks) == ["Callout", "Figure", "Callout"]
    assert blocks[1].caption == "Figure 4. Waves in a beam."


def test_a_bottom_border_puts_a_rule_after_the_paragraph(docx_factory):
    blocks = read_blocks(
        docx_factory(
            bordered("Dr. Korkut Kaynardag", "bottom", shade=False) + para("body")
        )
    )
    assert kinds(blocks) == ["Para", "Rule", "Para"]


def test_a_top_border_puts_a_rule_before_it(docx_factory):
    """The Brochure closes on a line ruled above and below."""
    blocks = read_blocks(
        docx_factory(bordered("closing", "top", "bottom", shade=False))
    )
    assert kinds(blocks) == ["Rule", "Para", "Rule"]


def test_an_empty_paragraph_carrying_only_a_border_is_the_rule(docx_factory):
    """Signal Processing draws a horizontal line this way. The paragraph has
    nothing to say and the emitter drops it; the rule is what remains."""
    blocks = read_blocks(
        docx_factory(para("a") + bordered("", "bottom", shade=False) + para("b"))
    )
    assert kinds(blocks) == ["Para", "Para", "Rule", "Para"]
    assert [n["type"] for n in emit(blocks)["nodes"]] == [
        "PARAGRAPH",
        "DIVIDER",
        "PARAGRAPH",
    ]


def test_a_border_on_a_heading_is_the_headings_own_decoration(docx_factory):
    """Understanding SHM and NDT rules under every Heading1. What a heading
    looks like is the theme's decision, as its colour is."""
    body = bordered("One", "bottom", style="Heading1", shade=False) + bordered(
        "Two", "left", style="Heading1"
    )
    blocks = read_blocks(docx_factory(body))
    assert kinds(blocks) == ["Para", "Para"]
    assert [b.heading for b in blocks] == [1, 1]


def test_a_left_border_outranks_the_rules(docx_factory):
    """A box with a bar on the left is an aside, whatever else frames it."""
    blocks = read_blocks(docx_factory(bordered("a", "left", "top", "bottom")))
    assert kinds(blocks) == ["Callout"]


def test_framed_paragraphs_inside_a_cell_stay_paragraphs(docx_factory):
    """A quote inside a table cell is a shape the validator has not seen."""
    body = f"<w:tbl><w:tr><w:tc>{bordered('a', 'left')}</w:tc><w:tc>{para('b')}</w:tc></w:tr></w:tbl>"
    blocks = read_blocks(docx_factory(body))
    assert kinds(blocks[0].rows[0][0]) == ["Para"]


def test_the_aside_reaches_the_page_as_the_same_blockquote_a_table_aside_does(
    docx_factory,
):
    blocks = read_blocks(docx_factory(bordered("a", "left") + bordered("b", "left")))
    quote = emit(blocks)["nodes"][0]
    assert quote["type"] == "BLOCKQUOTE"
    assert [t["textData"]["text"] for t in quote["nodes"][0]["nodes"]] == [
        "a",
        "\n",
        "b",
    ]


def test_a_rule_is_a_divider_node():
    """Whole dict. `DIVIDER` is in the plugin list the handover records for
    the validator, and the three fields are the ones the schema declares
    for `dividerData`; the values are the schema's own enum names. Not run
    through the validator in this session - see the spec."""
    doc = emit([Para(runs=[Run(text="a")]), Rule()])
    assert doc["nodes"][1] == {
        "type": "DIVIDER",
        "id": "n2",
        "nodes": [],
        "dividerData": {"lineStyle": "SINGLE", "width": "LARGE", "alignment": "CENTER"},
    }


def test_a_rule_inside_a_cell_or_an_aside_is_left_where_it_is():
    """Nothing makes one there today; if something does, it is emitted like
    any other block rather than raising."""
    doc = emit(
        [
            Table(rows=[[[Para(runs=[Run(text="x")]), Rule()]]]),
            Callout(blocks=[Para(runs=[Run(text="a")]), Rule()]),
        ]
    )
    assert [n["type"] for n in doc["nodes"][0]["nodes"][0]["nodes"][0]["nodes"]] == [
        "PARAGRAPH",
        "DIVIDER",
    ]
    assert [n["type"] for n in doc["nodes"][1:]] == ["BLOCKQUOTE", "DIVIDER"]


def test_a_figure_keeps_its_number_through_the_framing(docx_factory):
    body = (
        f"<w:p>{picture('rId5')}</w:p>"
        + bordered("a", "left")
        + f"<w:p>{picture('rId6')}</w:p>"
    )
    blocks = read_blocks(
        docx_factory(body, rels={"rId5": "media/i1.png", "rId6": "media/i2.png"})
    )
    assert [b.number for b in blocks if isinstance(b, Figure)] == [1, 2]
    assert kinds(blocks) == ["Figure", "Callout", "Figure"]
