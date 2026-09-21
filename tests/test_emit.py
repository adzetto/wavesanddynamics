"""The node shapes Wix will accept, pinned down.

Ricos rejects nothing at write time: a node with the wrong field name is stored
and simply renders as nothing, so a mistake here surfaces as a blank section on
the live site rather than as an error. These tests hold the shapes to what the
client's own published post actually contains, and to what the published
ricos-schema typings declare.
"""
import json

from tools.ricos.blocks import Callout, Figure, Para, Run, Table
from tools.ricos.emit import Ids, _para, emit


def test_paragraph_wraps_text_node():
    doc = emit([Para(runs=[Run(text="Hello")])])
    node = doc["nodes"][0]
    assert node["type"] == "PARAGRAPH"
    assert node["nodes"][0]["type"] == "TEXT"
    assert node["nodes"][0]["textData"]["text"] == "Hello"
    assert node["nodes"][0]["id"] == ""


def test_heading_becomes_heading_node():
    doc = emit([Para(runs=[Run(text="Closing Thoughts")], style="Heading1")])
    node = doc["nodes"][0]
    assert node["type"] == "HEADING"
    assert node["headingData"]["level"] == 1


def test_bold_run_carries_decoration():
    doc = emit([Para(runs=[Run(text="x", bold=True)])])
    decs = doc["nodes"][0]["nodes"][0]["textData"]["decorations"]
    assert {"type": "BOLD", "fontWeightValue": 700} in decs


def test_para_keeps_empty_paragraph_for_cell_placeholder():
    """The body drops these, but a table cell's placeholder keeps the grid
    rectangular and has to survive, so the node it gets still matters: an empty
    paragraph is a node with no children, never a TEXT holding "". That is the
    shape cell emission will take from `_para`, which filters nothing.
    """
    node = _para(Para(runs=[]), Ids())
    assert node["nodes"] == []


def test_italic_underline_and_link_runs_carry_their_decorations():
    """The three shapes this module exists to pin down.

    Only BOLD was verified from a published Wix example; these three were read
    off the ricos-schema typings (v10.102.0): ItalicDecoration l.219,
    UnderlineDecoration l.229, LinkDecoration l.269 with LinkData l.308 and
    Link.url l.73. The whole dict is asserted, not just the type, because a
    renamed data field is stored without complaint and then renders as nothing.
    """
    run = Run(text="x", italic=True, underline=True, link="https://x.test/p")
    decs = emit([Para(runs=[run])])["nodes"][0]["nodes"][0]["textData"]["decorations"]
    assert {"type": "ITALIC", "italicData": True} in decs
    assert {"type": "UNDERLINE", "underlineData": True} in decs
    assert {"type": "LINK", "linkData": {"link": {"url": "https://x.test/p"}}} in decs


def test_empty_paragraph_is_not_emitted_in_the_body():
    doc = emit([Para(runs=[Run(text="a")]), Para(runs=[]), Para(runs=[Run(text="b")])])
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["a", "b"]


def test_whitespace_only_paragraph_is_not_emitted_in_the_body():
    """Spacing the author typed instead of leaving blank: same stray block."""
    doc = emit([Para(runs=[Run(text="a")]), Para(runs=[Run(text="        ")])])
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["a"]


def test_contents_list_paragraph_is_not_emitted():
    """TOC1-TOC9 is a hand-typed contents list: redundant, and glued to the page
    numbers it was typed with.

    TOCHeading is the near-miss the `$` anchor in TOC_STYLE exists for: it is
    the word "Contents" itself, a real heading, and it stays.
    """
    blocks = [Para(runs=[Run(text="1. What is Machine Learning?\t2")], style="TOC1"),
              Para(runs=[Run(text="body")], style="TOC9"),
              Para(runs=[Run(text="Contents")], style="TOCHeading"),
              Para(runs=[Run(text="kept")])]
    doc = emit(blocks)
    texts = [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]]
    assert texts == ["Contents", "kept"]


def test_every_block_node_has_a_unique_id():
    doc = emit([Para(runs=[Run(text=str(i))]) for i in range(5)])
    ids = [n["id"] for n in doc["nodes"]]
    assert len(set(ids)) == 5
    assert all(i and i[0].isalpha() for i in ids)


def test_document_has_metadata_and_style():
    doc = emit([Para(runs=[Run(text="x")])])
    assert doc["metadata"]["version"] == 1
    assert doc["documentStyle"] == {}
    json.dumps(doc)  # must be serialisable


def test_image_node_uses_bare_id_and_dimensions():
    """`src.id` is the bare media id, never a `wix:image://v1/...` string.

    That string is the form a CMS *field* takes; inside a node it is stored
    without complaint and renders as a hole in the page. The shape here was
    read off a live IMAGE node on the client's own site through the Data API,
    down to `width`/`height`, which the renderer needs to reserve the space.
    """
    doc = emit([Figure(filename="image1.png", width=640, height=480)],
               media_ids={"image1.png": "ce0a40_abc~mv2.png"})
    node = doc["nodes"][0]
    assert node["type"] == "IMAGE"
    src = node["imageData"]["image"]["src"]
    assert src == {"id": "ce0a40_abc~mv2.png"}
    assert "wix:image" not in str(src)
    assert node["imageData"]["image"]["width"] == 640
    assert node["imageData"]["image"]["height"] == 480


def test_media_id_falls_back_to_the_filename():
    """Phase 1 has no Wix ids yet, so the name stands in and the upload fills
    it in later. Without this the id would be `None` and the node would be
    stored as a picture of nothing."""
    doc = emit([Figure(filename="image7.png", width=2, height=3)])
    assert doc["nodes"][0]["imageData"]["image"]["src"] == {"id": "image7.png"}


def test_image_caption_is_a_child_node_and_alt_text():
    """Both caption forms on purpose: `imageData.caption` is deprecated, but
    Wix's own published examples still carry it beside the CAPTION child."""
    doc = emit([Figure(filename="i.png", width=1, height=1,
                       caption="Figure 3. Dispersion curves.")])
    node = doc["nodes"][0]
    cap = node["nodes"][0]
    assert cap["type"] == "CAPTION"
    assert cap["nodes"][0]["textData"]["text"] == "Figure 3. Dispersion curves."
    assert node["imageData"]["altText"] == "Figure 3. Dispersion curves."


def test_table_nests_row_cell_paragraph():
    """TABLE -> TABLE_ROW -> TABLE_CELL -> block content, strictly. A cell's
    text is never a child of the cell itself; it needs its own paragraph."""
    t = Table(rows=[[[Para(runs=[Run(text="Name")])],
                     [Para(runs=[Run(text="Role")])]]], header_row=True)
    doc = emit([t])
    table = doc["nodes"][0]
    assert table["type"] == "TABLE"
    assert table["tableData"]["rowHeader"] is True
    row = table["nodes"][0]
    assert row["type"] == "TABLE_ROW"
    cell = row["nodes"][0]
    assert cell["type"] == "TABLE_CELL"
    assert cell["nodes"][0]["type"] == "PARAGRAPH"


def test_empty_cell_gets_paragraph_with_no_text_child():
    t = Table(rows=[[[Para(runs=[])], [Para(runs=[Run(text="x")])]]])
    doc = emit([t])
    cell = doc["nodes"][0]["nodes"][0]["nodes"][0]
    assert cell["nodes"][0]["type"] == "PARAGRAPH"
    assert cell["nodes"][0]["nodes"] == []


def test_the_body_filter_does_not_reach_inside_a_cell():
    """The boundary the grid depends on.

    An empty or whitespace-only paragraph is dropped from the body, but inside
    a cell it is the placeholder that keeps the row's cell count, so the filter
    must not be reachable from `_cell`. Drop it there and the row loses a cell
    and the table stops being rectangular.
    """
    t = Table(rows=[[[Para(runs=[])], [Para(runs=[Run(text="  ")])],
                     [Para(runs=[Run(text="x")], style="TOC1")]]])
    row = emit([t])["nodes"][0]["nodes"][0]
    assert [c["type"] for c in row["nodes"]] == ["TABLE_CELL"] * 3
    assert all(c["nodes"][0]["type"] == "PARAGRAPH" for c in row["nodes"])


def test_callout_becomes_blockquote_with_one_child():
    doc = emit([Callout(blocks=[Para(runs=[Run(text="How to use this guide")])])])
    node = doc["nodes"][0]
    assert node["type"] == "BLOCKQUOTE"
    assert len(node["nodes"]) == 1
    assert node["nodes"][0]["type"] == "PARAGRAPH"


def test_callout_paragraphs_are_joined_with_a_line_break():
    """A BLOCKQUOTE takes exactly one child, so the paragraphs of a multi-part
    aside have to become one. They are joined with a newline and not end to
    end: ten of the twelve asides in the corpus run to several paragraphs, the
    first of them a title, so gluing the runs directly would read "How to use
    this guideRead the document step by step".
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="The core idea")]),
                                Para(runs=[Run(text="It has four parts.")])])])
    para = doc["nodes"][0]["nodes"][0]
    assert len(doc["nodes"][0]["nodes"]) == 1
    text = "".join(t["textData"]["text"] for t in para["nodes"])
    assert text == "The core idea\nIt has four parts."


def test_the_body_filter_still_applies_beside_the_new_block_types():
    """`emit` now handles four block types instead of one, and the empty and
    contents-list paragraphs still have to go. The guard that drops them reads
    `block.style`, which only a Para has, so widening the loop is exactly where
    the filter gets lost - or gets handed a Figure and raises AttributeError.
    """
    blocks = [Para(runs=[]),
              Para(runs=[Run(text="1. What is Machine Learning?\t2")], style="TOC1"),
              Figure(filename="i.png", width=1, height=1),
              Table(rows=[[[Para(runs=[Run(text="x")])]]]),
              Callout(blocks=[Para(runs=[Run(text="aside")])]),
              Para(runs=[Run(text="   ")]),
              Para(runs=[Run(text="kept")])]
    types = [n["type"] for n in emit(blocks)["nodes"]]
    assert types == ["IMAGE", "TABLE", "BLOCKQUOTE", "PARAGRAPH"]
