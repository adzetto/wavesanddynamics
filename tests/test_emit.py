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
    doc = emit([Para(runs=[Run(text="Closing Thoughts")], heading=1)])
    node = doc["nodes"][0]
    assert node["type"] == "HEADING"
    assert node["headingData"]["level"] == 1


def test_a_heading_carries_its_level_and_its_own_alignment():
    """`headingData` whole, because the alignment in it was asserted nowhere.

    Replacing `block.align` with a constant here left every test green, and the
    corpus has 548 non-AUTO alignments on top-level paragraphs to lose that
    way. Centring is how the author opens most of these documents.
    """
    doc = emit([Para(runs=[Run(text="Closing Thoughts")], heading=2,
                     align="CENTER")])
    assert doc["nodes"][0]["headingData"] == {
        "level": 2, "textStyle": {"textAlignment": "CENTER"}}


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
    """A hand-typed contents list: redundant, and glued to the page numbers it
    was typed with.

    The role is what this side reads. Which of Word's styles carry it - TOC1 to
    TOC9, and not the "Contents" heading above them - is the reader's answer
    and is pinned there.
    """
    blocks = [Para(runs=[Run(text="1. What is Machine Learning?\t2")], role="TOC"),
              Para(runs=[Run(text="body")], role="TOC"),
              Para(runs=[Run(text="Contents")], heading=1),
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


def test_the_whole_image_node_is_the_shape_the_validator_accepted():
    """Whole dict, because the fields nothing asserts are the ones that go.

    Three of this node's shapes were settled by `POST /ricos/v1/ricos-document
    /validate` and then left unpinned, so removing `nodes: []` or rewriting
    `containerData` changed nothing any test could see - and this module's own
    docstring says why that is the failure mode: Ricos stores a wrong field
    without complaint and renders it as a blank space on the published page.
    `ImageNode.nodes?: never[]` in the typings makes the empty list look
    optional; the validator took it, the live post carries it, and a caption
    goes in it. The ids are what the allocator hands out in order, nothing more.
    """
    doc = emit([Figure(filename="image1.png", width=640, height=480)])
    assert doc["nodes"][0] == {
        "type": "IMAGE", "id": "n1", "nodes": [],
        "imageData": {
            "containerData": {"width": {"size": "CONTENT"},
                              "alignment": "CENTER", "textWrap": True},
            "image": {"src": {"id": "image1.png"}, "width": 640, "height": 480},
        },
    }


def test_the_whole_table_cell_is_the_shape_the_validator_accepted():
    """Whole dict, for the same reason and the other two unpinned shapes.

    `tableCellData: {}` is empty and looks droppable - the validator took it
    and the live document carries it - and `paragraphData.indentation` is the
    field the live post writes on every paragraph. Both survived being deleted
    with 132 tests green. The cell takes its id after its children, which is
    the one container here that does; that is observed, not required.
    """
    doc = emit([Table(rows=[[[Para(runs=[Run(text="x")])]]])])
    assert doc["nodes"][0]["nodes"][0]["nodes"][0] == {
        "type": "TABLE_CELL", "id": "n3", "nodes": [
            {"type": "PARAGRAPH", "id": "n2", "nodes": [
                {"type": "TEXT", "id": "", "nodes": [],
                 "textData": {"text": "x", "decorations": []}}],
             "paragraphData": {"textStyle": {"textAlignment": "AUTO"},
                               "indentation": 0}}],
        "tableCellData": {},
    }


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
    # The deprecated form, emitted on purpose. Nothing else guards it, so a
    # tidy-up would otherwise delete it without a test noticing.
    assert node["imageData"]["caption"] == "Figure 3. Dispersion curves."


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


def test_table_without_a_header_row_says_so():
    """`rowHeader` is emitted either way. False is not the same as absent, and
    a table whose first row is not bold must not claim a header.
    """
    doc = emit([Table(rows=[[[Para(runs=[Run(text="a")])]]], header_row=False)])
    assert doc["nodes"][0]["tableData"]["rowHeader"] is False


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

    The first cell is the one that can tell. It holds a paragraph that is kept
    and one that the body would drop, so the number of children it ends up with
    answers the question. A cell holding nothing but droppable content cannot
    answer it: `_cell`'s fallback puts a placeholder PARAGRAPH back either way,
    which is how this test went on passing with `_drop_from_body` wired into
    `_cell` - every assertion it made held under the mutation it exists to
    catch.
    """
    t = Table(rows=[[[Para(runs=[Run(text="x")]), Para(runs=[])],
                     [Para(runs=[Run(text="  ")])],
                     [Para(runs=[Run(text="y")], role="TOC")]]])
    row = emit([t])["nodes"][0]["nodes"][0]
    assert [c["type"] for c in row["nodes"]] == ["TABLE_CELL"] * 3
    assert all(c["nodes"][0]["type"] == "PARAGRAPH" for c in row["nodes"])
    assert len(row["nodes"][0]["nodes"]) == 2


def test_a_one_paragraph_callout_becomes_a_one_paragraph_blockquote():
    doc = emit([Callout(blocks=[Para(runs=[Run(text="How to use this guide")])])])
    node = doc["nodes"][0]
    assert node["type"] == "BLOCKQUOTE"
    assert len(node["nodes"]) == 1
    assert node["nodes"][0]["type"] == "PARAGRAPH"


def test_a_blockquote_holds_exactly_one_paragraph():
    """Wix's own validator settles this, against the generated typings.

    `POST /ricos/v1/ricos-document/validate` on a BLOCKQUOTE with two
    PARAGRAPH children returns `{"path":["nodes","3","nodes"],"message":
    "Expected to have size less than 1, but got 2"}`. The `.d.ts` says
    `nodes: ParagraphNode[]`, but a generated array type cannot express a
    maximum, so it is not evidence against the limit. One child it is.
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="The core idea")]),
                                Para(runs=[Run(text="It has four parts.")])])])
    quote = doc["nodes"][0]
    assert [n["type"] for n in quote["nodes"]] == ["PARAGRAPH"]


def test_the_quote_joins_its_source_paragraphs_with_a_line_break():
    """The separator is a TEXT run of "\\n", which is what `fixDocument` emits.

    Word's boundary between two paragraphs is the only thing saying where one
    ends, and running them together glued "How to use this guide" to the
    sentence after it in the ML guide's opening aside.
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="The core idea")]),
                                Para(runs=[Run(text="It has four parts.")])])])
    texts = [t["textData"]["text"] for t in doc["nodes"][0]["nodes"][0]["nodes"]]
    assert texts == ["The core idea", "\n", "It has four parts."]


def test_the_quote_paragraph_takes_the_first_source_paragraph_s_properties():
    """`fixDocument` carries `paragraphData` from the first source paragraph.

    Every multi-paragraph aside in the corpus is justified or centred in Word.
    Rebuilding the quote's paragraph from its runs alone silently reset all of
    them to AUTO, which no test caught because none looked at this field.
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="a")], align="JUSTIFY"),
                                Para(runs=[Run(text="b")], align="CENTER")])])
    inner = doc["nodes"][0]["nodes"][0]
    assert inner["paragraphData"]["textStyle"]["textAlignment"] == "JUSTIFY"


def test_a_heading_inside_a_callout_stays_a_paragraph():
    """A HEADING node in a quote is stored without complaint and renders as
    nothing. The words are worth more than the weight, so the style goes and
    the paragraph stays - alignment included.
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="The core idea")],
                                     heading=2, align="CENTER")])])
    inner = doc["nodes"][0]["nodes"][0]
    assert inner["type"] == "PARAGRAPH"
    assert inner["paragraphData"]["textStyle"]["textAlignment"] == "CENTER"


def test_the_body_filter_still_applies_beside_the_new_block_types():
    """`emit` now handles four block types instead of one, and the empty and
    contents-list paragraphs still have to go. The guard that drops them reads
    `block.role`, which only a Para has, so widening the loop is exactly where
    the filter gets lost - or gets handed a Figure and raises AttributeError.
    """
    blocks = [Para(runs=[]),
              Para(runs=[Run(text="1. What is Machine Learning?\t2")], role="TOC"),
              Figure(filename="i.png", width=1, height=1),
              Table(rows=[[[Para(runs=[Run(text="x")])]]]),
              Callout(blocks=[Para(runs=[Run(text="aside")])]),
              Para(runs=[Run(text="   ")]),
              Para(runs=[Run(text="kept")])]
    types = [n["type"] for n in emit(blocks)["nodes"]]
    assert types == ["IMAGE", "TABLE", "BLOCKQUOTE", "PARAGRAPH"]


def test_a_picture_in_a_callout_survives_as_a_sibling():
    """A BLOCKQUOTE holds one paragraph and nothing else - there is no
    BlockquoteChildNode union in the typings - so a picture inside the aside
    has nowhere to go. It follows the quote instead of being dropped: the aside
    loses where the picture sat inside it and keeps the picture, which is the
    right way round. No aside in the corpus holds one, so this is the latent
    case, pinned before it can happen quietly.
    """
    doc = emit([Callout(blocks=[Para(runs=[Run(text="The core idea")]),
                                Figure(filename="i.png", width=1, height=1),
                                Para(runs=[Run(text="It has four parts.")])])])
    assert [n["type"] for n in doc["nodes"]] == ["BLOCKQUOTE", "IMAGE"]
    quote = doc["nodes"][0]
    assert [n["type"] for n in quote["nodes"]] == ["PARAGRAPH"]


def test_a_callout_holding_no_paragraphs_is_not_wrapped_in_an_empty_quote():
    doc = emit([Callout(blocks=[Figure(filename="i.png", width=1, height=1)])])
    assert [n["type"] for n in doc["nodes"]] == ["IMAGE"]


def test_figure_with_no_source_is_skipped_but_an_unmeasured_one_is_kept():
    """An empty filename means Word never declared the relationship the picture
    pointed at, so `src` would be `{"id": ""}` - stored without complaint and
    rendered as a hole. A figure that has a file but no measured size is the
    other case and is kept: the file is real and the upload step can repair the
    dimensions. Neither state occurs in the present corpus.
    """
    doc = emit([Figure(filename="", width=640, height=480),
                Figure(filename="real.png", width=0, height=0)])
    assert [n["type"] for n in doc["nodes"]] == ["IMAGE"]
    assert doc["nodes"][0]["imageData"]["image"]["src"] == {"id": "real.png"}


def test_a_cell_emptied_by_a_skipped_figure_keeps_its_placeholder():
    """Skipping a picture must not cost the row a cell."""
    t = Table(rows=[[[Figure(filename="")], [Para(runs=[Run(text="x")])]]])
    row = emit([t])["nodes"][0]["nodes"][0]
    assert [c["type"] for c in row["nodes"]] == ["TABLE_CELL", "TABLE_CELL"]
    assert row["nodes"][0]["nodes"][0]["type"] == "PARAGRAPH"
