"""Paragraphs and heading styles, the two things every later stage depends on.

A heading that arrives as an ordinary paragraph silently flattens the page
outline, and the outline is what the Ricos writer builds its sections from, so
the style has to be read off the XML here and proved here.
"""
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


def test_skips_empty_paragraph_runs(docx_factory):
    data = docx_factory("<w:p></w:p>")
    blocks = read_blocks(data)
    assert len(blocks) == 1
    assert blocks[0].runs == []
