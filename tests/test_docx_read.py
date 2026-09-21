"""Paragraphs, heading styles and the inline marks every later stage depends on.

A heading that arrives as an ordinary paragraph silently flattens the page
outline, and the outline is what the Ricos writer builds its sections from, so
the style has to be read off the XML here and proved here. The same goes for the
marks and links a run carries: Ricos stores them as decorations on the text, so
whatever is lost or invented here cannot be recovered downstream.
"""
import pytest

from tools.ricos.blocks import Para
from tools.ricos.docx_read import read_blocks


def test_reads_plain_paragraph(docx_factory, para_factory):
    data = docx_factory(para_factory("Hello world"))
    blocks = read_blocks(data)
    assert len(blocks) == 1
    assert isinstance(blocks[0], Para)
    assert blocks[0].style == ""
    assert blocks[0].runs[0].text == "Hello world"


def test_reads_heading_style(docx_factory, para_factory):
    data = docx_factory(para_factory("Closing Thoughts", style="Heading1"))
    blocks = read_blocks(data)
    assert blocks[0].style == "Heading1"


def test_keeps_paragraph_with_no_runs(docx_factory):
    data = docx_factory("<w:p></w:p>")
    blocks = read_blocks(data)
    assert len(blocks) == 1
    assert blocks[0].runs == []


def test_drops_run_with_empty_text(docx_factory):
    """Word leaves behind runs holding nothing but formatting; they carry no text."""
    data = docx_factory("<w:p><w:r><w:rPr><w:b/></w:rPr><w:t></w:t></w:r></w:p>")
    blocks = read_blocks(data)
    assert blocks[0].runs == []


@pytest.mark.parametrize(
    ("rpr", "marks"),
    [
        ("<w:b/>", (True, False, False)),
        ('<w:b w:val="1"/>', (True, False, False)),
        ('<w:b w:val="0"/>', (False, False, False)),
        ("<w:i/>", (False, True, False)),
        ('<w:i w:val="false"/>', (False, False, False)),
        ('<w:u w:val="single"/>', (False, False, True)),
        ('<w:u w:val="none"/>', (False, False, False)),
    ],
)
def test_reads_marks_and_their_off_toggles(docx_factory, rpr, marks):
    """`<w:b w:val="0"/>` is how Word switches bold off, not a second way to set it."""
    data = docx_factory(f"<w:p><w:r><w:rPr>{rpr}</w:rPr><w:t>x</w:t></w:r></w:p>")
    run = read_blocks(data)[0].runs[0]
    assert (run.bold, run.italic, run.underline) == marks


@pytest.mark.parametrize(
    ("val", "align"),
    [
        ("both", "JUSTIFY"),
        ("center", "CENTER"),
        ("right", "RIGHT"),
        ("left", "LEFT"),
        ("distribute", "AUTO"),
    ],
)
def test_reads_paragraph_alignment(docx_factory, val, align):
    """Word's four names for alignment, and what an unknown fifth falls back to.

    Nothing covered this path: emptying `ALIGN` altogether left all 132 tests
    green, over a corpus carrying 1,376 paragraph-level `w:jc` elements and 548
    non-AUTO alignments on top-level paragraphs. It reaches the page twice
    over - as `textAlignment` on every paragraph and heading, and through the
    first paragraph of an aside, whose alignment now speaks for the whole
    BLOCKQUOTE.

    `distribute` is Word's fifth value and stands for every value we do not
    translate: AUTO is the renderer's own default, which is the right answer
    for an alignment we cannot express.
    """
    body = f'<w:p><w:pPr><w:jc w:val="{val}"/></w:pPr><w:r><w:t>x</w:t></w:r></w:p>'
    assert read_blocks(docx_factory(body))[0].align == align


def test_a_paragraph_with_no_jc_is_auto(docx_factory, para_factory):
    assert read_blocks(docx_factory(para_factory("x")))[0].align == "AUTO"


def test_merges_adjacent_runs_with_same_marks(docx_factory):
    body = (
        "<w:p>"
        "<w:r><w:t>Hel</w:t></w:r>"
        "<w:r><w:t>lo </w:t></w:r>"
        "<w:r><w:rPr><w:b/></w:rPr><w:t>world</w:t></w:r>"
        "</w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    runs = blocks[0].runs
    assert len(runs) == 2
    assert runs[0].text == "Hello "
    assert runs[0].bold is False
    assert runs[1].text == "world"
    assert runs[1].bold is True


def test_reads_hyperlink_target(docx_factory):
    body = (
        '<w:p><w:hyperlink r:id="rId9">'
        "<w:r><w:t>ruder.io</w:t></w:r>"
        "</w:hyperlink></w:p>"
    )
    blocks = read_blocks(docx_factory(body, rels={"rId9": "https://ruder.io/"}))
    assert blocks[0].runs[0].link == "https://ruder.io/"


def test_does_not_merge_a_link_into_the_text_around_it(docx_factory):
    body = (
        "<w:p>"
        "<w:r><w:t>see </w:t></w:r>"
        '<w:hyperlink r:id="rId9"><w:r><w:t>ru</w:t></w:r>'
        "<w:r><w:t>der.io</w:t></w:r></w:hyperlink>"
        "<w:r><w:t> today</w:t></w:r>"
        "</w:p>"
    )
    blocks = read_blocks(docx_factory(body, rels={"rId9": "https://ruder.io/"}))
    runs = blocks[0].runs
    assert [(r.text, r.link) for r in runs] == [
        ("see ", ""),
        ("ruder.io", "https://ruder.io/"),
        (" today", ""),
    ]


def test_keeps_tabs_and_line_breaks_as_whitespace(docx_factory):
    """A run holding only `<w:tab/>` carries no text, and dropping it lets the
    merge fuse its neighbours: the hand-typed contents list in the ML guide comes
    out as "What is Machine Learning?2", heading glued to page number."""
    body = (
        "<w:p>"
        "<w:r><w:t>What is Machine Learning?</w:t></w:r>"
        "<w:r><w:tab/></w:r>"
        "<w:r><w:t>2</w:t></w:r>"
        "</w:p>"
        "<w:p><w:r><w:t>one</w:t><w:br/><w:t>two</w:t></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert blocks[0].runs[0].text == "What is Machine Learning?\t2"
    assert blocks[1].runs[0].text == "one\ntwo"
