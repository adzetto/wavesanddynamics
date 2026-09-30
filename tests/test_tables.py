"""Tables, and the one-cell tables the author uses as highlighted asides.

Word gives him no aside, so he draws one: a table of a single cell, shaded, with
the paragraph inside it. Emitted as a table that reads as a one-column grid on
the page and costs a table's worth of nodes out of a 500 KB budget, for something
that was never data. Shape is the only thing that tells the two apart, and it is
decided here because by the time the writer sees a table the cell is gone.

Everything else in this file exists because a cell is a document in miniature:
the same paragraphs, the same pictures anchored in the middle of a sentence, the
same caption underneath. Sixteen of the corpus's pictures live in cells and were
unreachable until this task, so every rule the body already had has to reach
them too.
"""

from conftest import para, picture

from tools.ricos.blocks import Callout, Figure, Para, Table
from tools.ricos.docx_read import read_blocks


def _cell(content):
    """One <w:tc>; a whole <w:tc> passes through, text becomes a paragraph."""
    if content.startswith("<w:tc"):
        return content
    return f"<w:tc>{content if content.startswith('<w:') else para(content)}</w:tc>"


def _span_cell(content, n):
    """One <w:tc> covering `n` grid columns, the way Word stores a merged cell."""
    inner = content if content.startswith("<w:") else para(content)
    return f'<w:tc><w:tcPr><w:gridSpan w:val="{n}"/></w:tcPr>{inner}</w:tc>'


def _table(rows):
    body = "".join(
        "<w:tr>" + "".join(_cell(c) for c in row) + "</w:tr>" for row in rows
    )
    return f"<w:tbl>{body}</w:tbl>"


# --- the shape rule -------------------------------------------------------


def test_one_cell_table_becomes_callout(docx_factory):
    blocks = read_blocks(docx_factory(_table([["How to use this guide"]])))
    assert len(blocks) == 1
    assert isinstance(blocks[0], Callout)
    assert isinstance(blocks[0].blocks[0], Para)
    assert blocks[0].blocks[0].runs[0].text == "How to use this guide"


def test_real_table_keeps_rows_and_cells(docx_factory):
    blocks = read_blocks(docx_factory(_table([["Name", "Role"], ["Ada", "Eng"]])))
    assert len(blocks) == 1
    t = blocks[0]
    assert isinstance(t, Table)
    assert len(t.rows) == 2
    assert len(t.rows[0]) == 2
    assert t.rows[1][0][0].runs[0].text == "Ada"


def test_table_order_is_preserved_among_paragraphs(docx_factory, para_factory):
    body = para_factory("before") + _table([["a", "b"]]) + para_factory("after")
    blocks = read_blocks(docx_factory(body))
    assert [type(b).__name__ for b in blocks] == ["Para", "Table", "Para"]


def test_a_single_row_of_many_cells_is_a_table_not_a_callout(docx_factory):
    """Brochure's process strip is one row of seven cells. Only 1x1 is an aside."""
    blocks = read_blocks(docx_factory(_table([["a", "b", "c"]])))
    assert isinstance(blocks[0], Table)
    assert len(blocks[0].rows) == 1


def test_header_row_when_every_cell_of_the_first_row_is_bold(docx_factory):
    body = _table(
        [
            [para("Category", bold=True), para("Schematic figure", bold=True)],
            ["Structural dynamics", "Bridge vibration"],
        ]
    )
    blocks = read_blocks(docx_factory(body))
    assert blocks[0].header_row is True


def test_no_header_row_when_one_cell_of_the_first_row_is_plain(docx_factory):
    body = _table(
        [
            [para("Category", bold=True), "Schematic figure"],
            ["Structural dynamics", "Bridge vibration"],
        ]
    )
    blocks = read_blocks(docx_factory(body))
    assert blocks[0].header_row is False


def test_an_empty_cell_does_not_veto_a_header_row(docx_factory):
    """A confusion matrix leaves its corner blank and is a header row all the same.

    An empty cell carries no evidence either way, whether the author left it
    empty or flattening a merged cell put it there.
    """
    body = _table(
        [
            [
                "",
                para("Predicted Positive", bold=True),
                para("Predicted Negative", bold=True),
            ],
            [para("Actual Positive", bold=True), "5", "2"],
        ]
    )
    assert read_blocks(docx_factory(body))[0].header_row is True


def test_a_first_row_of_nothing_but_empty_cells_is_not_a_header_row(docx_factory):
    """ "Every cell that speaks is bold" must not pass a row that says nothing."""
    body = _table([["", ""], ["Ada", "Eng"]])
    assert read_blocks(docx_factory(body))[0].header_row is False


def test_a_bold_blank_does_not_make_a_cell_count_as_bold(docx_factory):
    """Word leaves bold whitespace behind between words; it is not a label.

    The cell speaks, so it is consulted, and what it says is not bold.
    """
    cell = (
        '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve"> </w:t></w:r>'
        "<w:r><w:t>Category</w:t></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(_table([[cell], ["Ada"]])))
    assert blocks[0].header_row is False


def test_bold_switched_off_does_not_make_a_header_row(docx_factory):
    """Word cancels an inherited bold with a value, not by leaving the tag out."""
    off = '<w:p><w:r><w:rPr><w:b w:val="0"/></w:rPr><w:t>Category</w:t></w:r></w:p>'
    blocks = read_blocks(docx_factory(_table([[off], ["Ada"]])))
    assert blocks[0].header_row is False


# --- every row the same length ---------------------------------------------


def test_a_merged_cell_becomes_the_columns_it_covers(docx_factory):
    """Ricos has rows of cells and no reliable colspan, so a span is flattened."""
    body = _table([[_span_cell("Feature Engineering", 3)], ["a", "b", "c"]])
    blocks = read_blocks(docx_factory(body))
    rows = blocks[0].rows
    assert [len(r) for r in rows] == [3, 3]
    assert rows[0][0][0].runs[0].text == "Feature Engineering"
    assert rows[0][1] == [Para()]
    assert rows[0][2] == [Para()]


def test_a_cell_without_a_span_stays_one_cell(docx_factory):
    body = _table([["Name", "Role"], ["Ada", "Eng"]])
    assert [len(r) for r in read_blocks(docx_factory(body))[0].rows] == [2, 2]


def test_a_row_that_stops_short_of_the_grid_is_padded(docx_factory):
    """Word lets a row hold fewer cells than the table is wide.

    Two of the three corpus tables that merge cells also do this, so expanding
    the span is not on its own enough to leave every row the same length.
    """
    body = _table([["TYPES OF MONITORING"], ["a", "b", "c"]])
    rows = read_blocks(docx_factory(body))[0].rows
    assert [len(r) for r in rows] == [3, 3]
    assert rows[0][0][0].runs[0].text == "TYPES OF MONITORING"
    assert rows[0][2] == [Para()]


def test_padding_cells_are_not_shared_between_rows(docx_factory):
    """Each empty cell is its own list: later stages set ids on these blocks."""
    body = _table([["one"], ["a", "b"], ["two"]])
    rows = read_blocks(docx_factory(body))[0].rows
    assert rows[0][1] is not rows[2][1]
    assert rows[0][1][0] is not rows[2][1][0]


def test_a_one_cell_table_is_a_callout_even_when_it_spans_columns(docx_factory):
    """The aside test counts the cells he drew, not the columns Word gave them."""
    body = f"<w:tbl><w:tr>{_span_cell('How to use this guide', 3)}</w:tr></w:tbl>"
    blocks = read_blocks(docx_factory(body))
    assert isinstance(blocks[0], Callout)
    assert blocks[0].blocks[0].runs[0].text == "How to use this guide"


def test_empty_cell_still_contributes_a_block(docx_factory):
    """A cell holding nothing still holds a place: the grid must stay rectangular."""
    body = f"<w:tbl><w:tr><w:tc/>{_cell('Ada')}</w:tr><w:tr>{_cell('a')}{_cell('b')}</w:tr></w:tbl>"
    blocks = read_blocks(docx_factory(body))
    assert [len(r) for r in blocks[0].rows] == [2, 2]
    assert blocks[0].rows[0][0] == [Para()]


def test_table_of_contents_is_still_skipped(docx_factory, para_factory):
    """Word's generated ToC is a w:sdt, and walking every body child now reaches it."""
    toc = (
        "<w:sdt><w:sdtPr/><w:sdtContent>"
        + para_factory("Table of Contents")
        + para_factory("1. What is ML?")
        + "</w:sdtContent></w:sdt>"
    )
    blocks = read_blocks(docx_factory(toc + para_factory("body")))
    assert [type(b).__name__ for b in blocks] == ["Para"]
    assert blocks[0].runs[0].text == "body"


def test_line_break_in_a_cell_reads_as_a_newline(docx_factory):
    """Every w:br in the corpus is inside a cell, so this path opens only now."""
    cell = "<w:p><w:r><w:t>one</w:t><w:br/><w:t>two</w:t></w:r></w:p>"
    blocks = read_blocks(docx_factory(_table([[cell]])))
    assert blocks[0].blocks[0].runs[0].text == "one\ntwo"


# --- a cell is a document in miniature ------------------------------------


def test_reads_a_picture_inside_a_cell(docx_factory):
    """Sixteen pictures in the corpus live in cells; none was reachable before."""
    body = _table([[f"<w:p>{picture()}</w:p>", "Bridge vibration"]])
    blocks = read_blocks(docx_factory(body, rels={"rId5": "media/image1.png"}))
    fig = blocks[0].rows[0][0][0]
    assert isinstance(fig, Figure)
    assert fig.rel_id == "rId5"
    assert fig.filename == "image1.png"


def test_keeps_prose_written_around_a_picture_in_a_cell(docx_factory):
    """The same anchored picture the body has, inside Brochure's monitoring table.

    Ricos has no inline image, so the picture is hoisted out of the sentence it
    was anchored in; emitting the picture *instead of* the paragraph would drop
    the sentence, and in this cell that is 541 characters of real prose.
    """
    cell = (
        "<w:p><w:r><w:t>Acoustic emission-based monitoring: </w:t></w:r>"
        + picture()
        + "<w:r><w:t>sensors listen for cracking.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(_table([[cell, "other"]])))
    cell_blocks = blocks[0].rows[0][0]
    assert [type(b) for b in cell_blocks] == [Figure, Para]
    assert cell_blocks[1].runs[0].text == (
        "Acoustic emission-based monitoring: sensors listen for cracking."
    )


def test_pairs_a_caption_with_the_picture_above_it_inside_a_cell(docx_factory):
    """Caption folding walks the top level; a cell is a flow of its own too."""
    cell = f"<w:p>{picture()}</w:p>" + para("Figure 3. Bridge vibration.")
    blocks = read_blocks(docx_factory(_table([[cell, "other"]])))
    cell_blocks = blocks[0].rows[0][0]
    assert [type(b) for b in cell_blocks] == [Figure]
    assert cell_blocks[0].caption == "Figure 3. Bridge vibration."


def test_a_caption_never_reaches_back_into_the_cell_before_it(docx_factory):
    """Cells are separate flows: the line beside a picture is not under it."""
    body = _table([[f"<w:p>{picture()}</w:p>", "Figure 3. Bridge vibration."]])
    blocks = read_blocks(docx_factory(body))
    left, right = blocks[0].rows[0]
    assert left[0].caption == ""
    assert right[0].runs[0].text == "Figure 3. Bridge vibration."


def test_a_caption_after_a_table_is_not_the_caption_of_a_picture_before_it(
    docx_factory,
):
    """A table between the two breaks the adjacency the pairing rule relies on."""
    body = (
        f"<w:p>{picture()}</w:p>"
        + _table([["a", "b"]])
        + para("Figure 3. Bridge vibration.")
    )
    blocks = read_blocks(docx_factory(body))
    assert [type(b) for b in blocks] == [Figure, Table, Para]
    assert blocks[0].caption == ""


def test_numbers_figures_inside_tables_in_reading_order(docx_factory):
    """Numbering is one sequence over the document, and a cell is in the document.

    Left unextended, every picture in a cell keeps number 0 while the body's
    pictures count on around it, and nothing anywhere reports the collision.
    """
    pic_cell = f"<w:p>{picture()}</w:p>"
    body = (
        f"<w:p>{picture()}</w:p>"
        + _table([[pic_cell, "b"], ["c", pic_cell]])
        + _table([[pic_cell]])
        + f"<w:p>{picture()}</w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    table, callout = blocks[1], blocks[2]
    assert [b.number for b in blocks if isinstance(b, Figure)] == [1, 5]
    assert table.rows[0][0][0].number == 2
    assert table.rows[1][1][0].number == 3
    assert callout.blocks[0].number == 4


def test_nested_table_is_flattened_into_the_cell(docx_factory):
    """Ricos forbids a table inside a cell, so the inner rows become paragraphs.

    No document in the corpus nests a table today; this is what happens when one
    does, written down rather than left to be discovered.
    """
    inner = _table([["inner a", "inner b"]])
    body = _table([[f"{para('outer')}{inner}", "right"]])
    blocks = read_blocks(docx_factory(body))
    cell_blocks = blocks[0].rows[0][0]
    assert all(isinstance(b, Para) for b in cell_blocks)
    assert [b.runs[0].text for b in cell_blocks] == ["outer", "inner a", "inner b"]


def test_a_nested_tables_empty_cells_leave_no_blank_paragraphs_behind(docx_factory):
    """The placeholder that keeps a grid rectangular belongs to the outer
    cell. Flattening an inner table used to inject one for every empty inner
    cell, and the outer cell then emitted each as a blank line."""
    inner = _table([["inner a", ""], ["", "inner d"]])
    body = _table([[f"{para('outer')}{inner}", "right"]])
    cell_blocks = read_blocks(docx_factory(body))[0].rows[0][0]
    assert [b.runs[0].text for b in cell_blocks] == ["outer", "inner a", "inner d"]


def test_a_cell_holding_only_an_empty_nested_table_keeps_one_placeholder(docx_factory):
    body = _table([[_table([["", ""]]), "right"]])
    assert read_blocks(docx_factory(body))[0].rows[0][0] == [Para()]
