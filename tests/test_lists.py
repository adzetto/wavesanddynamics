"""Bulleted and ordered lists, the last content type these documents use.

Word says almost nothing about a list on the paragraph itself. `w:numPr` says
only which numbering definition the item belongs to and how deep it sits;
whether the marker is a bullet or a number lives in word/numbering.xml, a part
away, which is why the reader has to open a second file to answer a question
about a paragraph.

The two models disagree about the list itself, too. Word has no list node at
all - a list is a stretch of consecutive paragraphs that happen to name the same
`w:numId` - while Ricos wants `BULLETED_LIST`/`ORDERED_LIST` holding
`LIST_ITEM`s. So the grouping is not read, it is rebuilt on the way out, and it
is a property of a *flow* of blocks rather than of any one block. That is why it
lives in one helper the body and a table cell both pass through, and why the
aside deliberately does not use it: `BlockquoteNode.nodes` is declared
`ParagraphNode[]`, so a list inside a quote would be off-type.
"""
from conftest import W, para

from tools.ricos.blocks import Callout, Para, Run
from tools.ricos.docx_read import read_blocks
from tools.ricos.emit import emit


def _li(text, num_id="1", ilvl="0"):
    return (
        "<w:p><w:pPr><w:numPr>"
        f'<w:ilvl w:val="{ilvl}"/><w:numId w:val="{num_id}"/>'
        "</w:numPr></w:pPr>"
        f"<w:r><w:t>{text}</w:t></w:r></w:p>"
    )


def _numbering(fmt, num_id="1"):
    """A word/numbering.xml declaring one list whose level 0 uses `fmt`."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<w:numbering {W}>"
        '<w:abstractNum w:abstractNumId="7">'
        f'<w:lvl w:ilvl="0"><w:numFmt w:val="{fmt}"/></w:lvl>'
        "</w:abstractNum>"
        f'<w:num w:numId="{num_id}"><w:abstractNumId w:val="7"/></w:num>'
        "</w:numbering>"
    ).encode()


def _table(rows):
    body = "".join("<w:tr>" + "".join(f"<w:tc>{c}</w:tc>" for c in row) + "</w:tr>"
                   for row in rows)
    return f"<w:tbl>{body}</w:tbl>"


# --- the reader -----------------------------------------------------------

def test_reader_marks_list_paragraphs(docx_factory):
    blocks = read_blocks(docx_factory(_li("INSPECT") + _li("MONITOR")))
    assert all(b.list_kind == "bullet" for b in blocks)
    assert all(b.list_level == 0 for b in blocks)


def test_reader_records_nesting_level(docx_factory):
    blocks = read_blocks(docx_factory(_li("a") + _li("b", ilvl="1")))
    assert [b.list_level for b in blocks] == [0, 1]


def test_the_marker_comes_from_numbering_xml(docx_factory):
    ordered = docx_factory(_li("first"), media={"word/numbering.xml": _numbering("decimal")})
    bulleted = docx_factory(_li("first"), media={"word/numbering.xml": _numbering("bullet")})
    assert read_blocks(ordered)[0].list_kind == "ordered"
    assert read_blocks(bulleted)[0].list_kind == "bullet"


def test_a_definition_with_no_readable_format_reads_as_a_bullet(docx_factory):
    """Both "no format information" paths agree, and both say bullet.

    A `w:num` pointing at an abstract definition that is not there, and an
    abstract definition whose level declares no `w:numFmt`, mean the same
    thing. A wrongly bulleted list is a smaller defect than a wrongly numbered
    one, which invents an order the author never wrote.
    """
    no_fmt = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<w:numbering {W}>"
        '<w:abstractNum w:abstractNumId="7"><w:lvl w:ilvl="0"/></w:abstractNum>'
        '<w:num w:numId="1"><w:abstractNumId w:val="7"/></w:num>'
        '<w:num w:numId="2"><w:abstractNumId w:val="404"/></w:num>'
        "</w:numbering>"
    ).encode()
    body = _li("a", num_id="1") + _li("b", num_id="2")
    blocks = read_blocks(docx_factory(body, media={"word/numbering.xml": no_fmt}))
    assert [b.list_kind for b in blocks] == ["bullet", "bullet"]


def test_a_malformed_nesting_level_costs_one_paragraph_not_the_document(docx_factory):
    """`_span` guards its own integer; reading a depth must degrade the same way.

    An unreadable `w:ilvl` is one paragraph's indent, and the paragraph is
    still an item of a list. Letting it raise would take the whole document
    read down with it.
    """
    blocks = read_blocks(docx_factory(_li("a", ilvl="deep") + _li("b")))
    assert [b.list_kind for b in blocks] == ["bullet", "bullet"]
    assert [b.list_level for b in blocks] == [0, 0]


def test_a_list_styled_paragraph_without_numbering_is_not_a_list(docx_factory, para_factory):
    """Word styles the indented continuation of an item ListParagraph as well.

    Twelve paragraphs in the corpus are styled that way and carry no `w:numPr`.
    They are prose, and a reader that went by the style name would bullet them.
    """
    blocks = read_blocks(docx_factory(para_factory("continued", style="ListParagraph")))
    assert blocks[0].list_kind == ""
    assert emit(blocks)["nodes"][0]["type"] == "PARAGRAPH"


# --- the grouping ---------------------------------------------------------

def test_emit_groups_consecutive_items_into_one_list():
    items = [Para(runs=[Run(text=t)], list_kind="bullet") for t in ("a", "b", "c")]
    doc = emit(items)
    assert len(doc["nodes"]) == 1
    lst = doc["nodes"][0]
    assert lst["type"] == "BULLETED_LIST"
    assert len(lst["nodes"]) == 3
    item = lst["nodes"][0]
    assert item["type"] == "LIST_ITEM"
    assert item["nodes"][0]["type"] == "PARAGRAPH"
    assert item["nodes"][0]["nodes"][0]["textData"]["text"] == "a"


def test_emit_splits_when_kind_changes():
    doc = emit([
        Para(runs=[Run(text="a")], list_kind="bullet"),
        Para(runs=[Run(text="1")], list_kind="ordered"),
    ])
    assert [n["type"] for n in doc["nodes"]] == ["BULLETED_LIST", "ORDERED_LIST"]


def test_a_new_numbering_definition_starts_a_new_list(docx_factory):
    """Two Word lists back to back are two lists, even with the same marker.

    The ML guide already does this: `numId` 3 ends and `numId` 1 begins with no
    prose between them. Merging them is invisible while both are bulleted, but
    an ordered second list would carry on 4, 5, 6 instead of restarting at 1.
    """
    blocks = read_blocks(docx_factory(_li("a", num_id="1") + _li("b", num_id="3")))
    assert [b.list_id for b in blocks] == ["1", "3"]
    doc = emit(blocks)
    assert [n["type"] for n in doc["nodes"]] == ["BULLETED_LIST", "BULLETED_LIST"]


def test_plain_paragraph_ends_a_list():
    doc = emit([
        Para(runs=[Run(text="a")], list_kind="bullet"),
        Para(runs=[Run(text="prose")]),
        Para(runs=[Run(text="b")], list_kind="bullet"),
    ])
    assert [n["type"] for n in doc["nodes"]] == [
        "BULLETED_LIST", "PARAGRAPH", "BULLETED_LIST"]


def test_a_list_carries_no_indentation_it_cannot_express():
    """`indentation` is documented `1` to `4`, and these lists have none.

    Both data objects are optional (l.426, l.450) and `indentation` holds a
    margin, not a nesting depth - `offset` is the field where `0` means "the
    default" (l.434, l.454). Writing `0` into `indentation` would be a value
    outside its declared range, which Ricos stores happily and renders however
    it likes. Leaving the field out asks for the default instead.
    """
    doc = emit([Para(runs=[Run(text="a")], list_kind="bullet"),
                Para(runs=[Run(text="b")], list_kind="ordered")])
    assert "bulletedListData" not in doc["nodes"][0]
    assert "orderedListData" not in doc["nodes"][1]


def test_an_empty_paragraph_between_items_does_not_split_the_list():
    """The body filter runs before the grouping, so the artefact cannot divide.

    An empty paragraph is how Word leaves vertical space; it is dropped as a
    stray gap either way. Dropping it first means two bullets typed around one
    stay the single list the page shows, instead of two lists restarting.
    """
    doc = emit([Para(runs=[Run(text="a")], list_kind="bullet"),
                Para(),
                Para(runs=[Run(text="b")], list_kind="bullet")])
    assert [n["type"] for n in doc["nodes"]] == ["BULLETED_LIST"]
    assert len(doc["nodes"][0]["nodes"]) == 2


# --- the flows the grouping reaches, and the one it does not --------------

def test_a_list_inside_a_table_cell_is_read_and_grouped(docx_factory):
    body = _table([[_li("a") + _li("b"), para("x")], [para("y"), para("z")]])
    blocks = read_blocks(docx_factory(body))
    assert [b.list_kind for b in blocks[0].rows[0][0]] == ["bullet", "bullet"]
    cell = emit(blocks)["nodes"][0]["nodes"][0]["nodes"][0]
    assert cell["type"] == "TABLE_CELL"
    assert [n["type"] for n in cell["nodes"]] == ["BULLETED_LIST"]
    assert len(cell["nodes"][0]["nodes"]) == 2


def test_a_list_paragraph_in_an_aside_stays_a_flat_paragraph(docx_factory):
    """A quote holds one PARAGRAPH, so a list node there is doubly off-type."""
    blocks = read_blocks(docx_factory(_table([[_li("a") + _li("b")]])))
    assert [b.list_kind for b in blocks[0].blocks] == ["bullet", "bullet"]
    quote = emit(blocks)["nodes"][0]
    assert quote["type"] == "BLOCKQUOTE"
    assert [n["type"] for n in quote["nodes"]] == ["PARAGRAPH"]
    texts = [t["textData"]["text"] for t in quote["nodes"][0]["nodes"]]
    assert texts == ["a", "\n", "b"]


# --- the aside's own two defects -----------------------------------------

def test_an_aside_paragraph_with_no_text_is_dropped():
    """Dropped before the join, so it does not leave a separator behind either."""
    doc = emit([Callout(blocks=[Para(runs=[Run(text="kept")]),
                                Para(),
                                Para(runs=[Run(text="   ")])])])
    inner = doc["nodes"][0]["nodes"]
    assert [n["type"] for n in inner] == ["PARAGRAPH"]
    assert [t["textData"]["text"] for t in inner[0]["nodes"]] == ["kept"]


def test_a_quote_takes_its_id_before_its_children():
    doc = emit([Callout(blocks=[Para(runs=[Run(text="a")])])])
    quote = doc["nodes"][0]
    assert quote["id"] == "n1"
    assert quote["nodes"][0]["id"] == "n2"
