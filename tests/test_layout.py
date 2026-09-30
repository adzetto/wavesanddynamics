"""What Word says about how a picture and a table are laid out.

Four things the page could not know before, because the reader threw them away:

- how wide Word draws each picture, beside the width of the text column it
  sits in, so a picture the author set at half the column is not published
  twice as large as he drew it (thirteen figures in this corpus were);
- the part of a picture Word crops away (`a:srcRect`), which the page showed
  anyway: a white slide title and an empty band in one figure, a third of
  blank canvas in another;
- a picture no taller than a line of text, set inside a sentence, which was
  hoisted out of it and, inside a caption, took the caption of the diagram
  above it;
- the widths Word gives a table's columns.
"""

import json

from conftest import EMU_PER_PX, para, picture, png
from PIL import Image

from tools import docx2ricos
from tools.docx2ricos import convert
from tools.ricos.blocks import Figure, Para, Table
from tools.ricos.docx_read import crop_box, read_blocks, text_width
from tools.ricos.emit import emit

REL = {"rId5": "media/image1.png"}


def _sect(page=12240, left=1440, right=1440):
    """The body's section properties: page width and side margins, in twips."""
    return (
        f'<w:sectPr><w:pgSz w:w="{page}" w:h="15840"/>'
        f'<w:pgMar w:top="1440" w:right="{right}" w:bottom="1440" w:left="{left}"/>'
        "</w:sectPr>"
    )


def _run(text):
    return f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'


def _read(body, size=(640, 480)):
    return read_blocks(
        _docx_bytes(body, size),
    )


def _docx_bytes(body, size):
    from conftest import make_docx

    return make_docx(body, rels=REL, media={"word/media/image1.png": png(*size)})


# --- how big Word draws it ---------------------------------------------------------


def test_a_picture_carries_the_size_word_draws_it_at_and_its_column():
    """The ML guide's MLP diagram: 1495 px stored, drawn 322 px wide in a 624 px
    column. The stored size is what the file holds; the drawn size is the
    author's decision, and it is the one the page lost."""
    body = f"<w:p>{picture(size=(322, 187))}</w:p>" + _sect()
    fig = _read(body, size=(1495, 871))[0]
    assert isinstance(fig, Figure)
    assert (fig.width, fig.height) == (1495, 871)
    assert (fig.display_width, fig.display_height) == (322, 187)
    assert fig.column == 624


def test_a_picture_with_no_extent_has_no_drawn_size():
    fig = _read(f"<w:p>{picture()}</w:p>")[0]
    assert (fig.display_width, fig.display_height, fig.column) == (0, 0, 0)


def test_the_text_width_is_the_page_less_its_margins():
    """Twips, 1440 an inch, 15 a CSS pixel: Letter, one-inch margins."""
    from lxml import etree

    root = etree.fromstring(
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{_sect(page=12240, left=1440, right=1440)}</w:body></w:document>"
    )
    assert text_width(root) == 624


def test_a_document_with_no_section_properties_has_no_text_width():
    from lxml import etree

    root = etree.fromstring(
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body/></w:document>"
    )
    assert text_width(root) == 0


# --- the crop ----------------------------------------------------------------------------


def test_a_cropped_picture_measures_as_the_part_word_shows():
    """ML Figure 10: Word hides the bottom 33.696% of a 1610 x 860 canvas."""
    body = f"<w:p>{picture(size=(624, 221), crop={'b': '33696'})}</w:p>"
    fig = _read(body, size=(1610, 860))[0]
    assert fig.crop == (0.0, 0.0, 0.0, 0.33696)
    assert (fig.width, fig.height) == (1610, 570)


def test_a_negative_inset_is_padding_and_not_a_crop():
    """Dynamical Figure 9 crops 18.75% off the top and pads the other three
    sides; the padding is empty space the page already has, so it is dropped."""
    crop = {"l": "-400", "t": "18750", "r": "-400", "b": "-3125"}
    fig = _read(f"<w:p>{picture(size=(605, 259), crop=crop)}</w:p>", size=(1542, 740))[
        0
    ]
    assert fig.crop == (0.0, 0.1875, 0.0, 0.0)
    assert (fig.width, fig.height) == (1542, 601)


def test_a_crop_that_leaves_nothing_is_ignored():
    fig = _read(
        f"<w:p>{picture(crop={'l': '60000', 'r': '50000'})}</w:p>", size=(100, 50)
    )[0]
    assert fig.crop == ()
    assert (fig.width, fig.height) == (100, 50)


def test_crop_box_is_the_same_pixels_the_reader_measured():
    assert crop_box(1610, 860, (0.0, 0.0, 0.0, 0.33696)) == (0, 0, 1610, 570)
    assert crop_box(1542, 740, (0.0, 0.1875, 0.0, 0.0)) == (0, 139, 1542, 740)


# --- a picture inside a line of text ----------------------------------------------


def test_a_text_height_picture_stays_where_it_was_in_its_sentence():
    """Dynamical Behavior sets its harmonic-wave equation as a 185 x 15 px
    picture in the middle of a sentence. Hoisted above the paragraph, the
    sentence read "of the form ." and the equation floated a paragraph early.
    The paragraph is cut at the picture instead, so the order survives."""
    body = (
        "<w:p>"
        + _run("a harmonic wave term of the form ")
        + picture(size=(185, 15))
        + _run(". Substituting this form")
        + "</w:p>"
    )
    blocks = _read(body, size=(484, 38))
    assert [type(b) for b in blocks] == [Para, Figure, Para]
    assert blocks[0].runs[0].text == "a harmonic wave term of the form "
    assert blocks[1].inline is True
    assert blocks[1].offset == -1
    assert blocks[1].joins == "both"
    assert blocks[2].runs[0].text == ". Substituting this form"


def test_a_caption_keeps_its_caption_for_the_picture_above_it():
    """Dynamical Figure 5: the caption line under the diagram ends on the same
    equation picture. Hoisted ahead of the caption, the equation took the
    caption and the diagram was left with none. The caption now goes to the
    diagram whole, and the equation keeps its place in the caption's text."""
    text = "Figure 5. Two ways, through the harmonic term "
    body = (
        f"<w:p>{picture('rId6', size=(649, 220))}</w:p>"
        "<w:p>" + _run(text) + picture(size=(165, 13)) + _run(".") + "</w:p>"
    )
    from conftest import make_docx

    blocks = read_blocks(
        make_docx(
            body,
            rels={"rId5": "media/image1.png", "rId6": "media/image2.png"},
            media={
                "word/media/image1.png": png(484, 38),
                "word/media/image2.png": png(2640, 840),
            },
        )
    )
    assert [type(b) for b in blocks] == [Figure, Figure]
    diagram, equation = blocks
    assert diagram.filename == "image2.png"
    assert diagram.caption == text + "."
    assert equation.inline is True
    assert equation.caption == ""
    assert equation.offset == len(text)


def test_an_inline_picture_never_takes_the_caption_line_under_it():
    body = (
        "<w:p>"
        + _run("the form ")
        + picture(size=(185, 15))
        + "</w:p>"
        + para("Figure 2. A caption for something else.")
    )
    blocks = _read(body, size=(484, 38))
    assert [type(b) for b in blocks] == [Para, Figure, Para]
    assert blocks[1].caption == ""


def test_a_picture_that_ends_its_paragraph_joins_only_the_text_before_it():
    body = "<w:p>" + _run("where the term is ") + picture(size=(120, 15)) + "</w:p>"
    blocks = _read(body, size=(320, 40))
    assert [type(b) for b in blocks] == [Para, Figure]
    assert blocks[1].joins == "prev"


def test_a_picture_taller_than_two_lines_is_still_hoisted():
    body = (
        "<w:p>"
        + _run("text before ")
        + picture(size=(300, 200))
        + _run("after")
        + "</w:p>"
    )
    blocks = _read(body, size=(900, 600))
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[0].inline is False
    assert blocks[1].runs[0].text == "text before after"


def test_a_floating_picture_is_not_in_the_line_whatever_its_size():
    body = (
        "<w:p>"
        + _run("text ")
        + picture(size=(40, 12), anchor=True)
        + _run("more")
        + "</w:p>"
    )
    blocks = _read(body, size=(160, 48))
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[0].inline is False


def test_an_inline_picture_in_a_list_item_keeps_the_item_whole():
    """Cutting a list item would make it two items; the picture follows the
    item instead and says where in its text it sat."""
    body = (
        '<w:p><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="3"/></w:numPr></w:pPr>'
        + _run("item with ")
        + picture(size=(60, 14))
        + _run(" inside")
        + "</w:p>"
    )
    blocks = _read(body, size=(240, 56))
    assert [type(b) for b in blocks] == [Para, Figure]
    assert blocks[0].runs[0].text == "item with  inside"
    assert blocks[1].inline is True
    assert blocks[1].offset == len("item with ")


# --- table columns ------------------------------------------------------------------


def _grid_table(grid, rows, trpr=""):
    cols = "".join(f'<w:gridCol w:w="{w}"/>' for w in grid)
    body = "".join(
        f"<w:tr>{trpr}" + "".join(f"<w:tc>{para(c)}</w:tc>" for c in row) + "</w:tr>"
        for row in rows
    )
    return f"<w:tbl><w:tblGrid>{cols}</w:tblGrid>{body}</w:tbl>"


def test_a_table_carries_words_column_widths_as_fractions():
    """ML glossary: Term 1905 twips, Definition 7455 - 20% and 80%."""
    from conftest import make_docx

    table = _grid_table([1905, 7455], [["Term", "Definition"], ["Bias", "An offset"]])
    t = read_blocks(make_docx(table))[0]
    assert isinstance(t, Table)
    assert [round(w, 4) for w in t.widths] == [0.2035, 0.7965]


def test_a_grid_that_does_not_match_the_rows_gives_no_widths():
    from conftest import make_docx

    table = _grid_table([1000, 2000, 3000], [["a", "b"], ["c", "d"]])
    assert read_blocks(make_docx(table))[0].widths == []


def test_a_row_that_starts_late_gives_no_widths():
    """`w:gridBefore` shifts a row's cells along the grid, which the reader does
    not follow, so the grid's widths would name the wrong columns."""
    from conftest import make_docx

    table = _grid_table(
        [1000, 2000],
        [["a", "b"], ["c", "d"]],
        trpr='<w:trPr><w:gridBefore w:val="1"/></w:trPr>',
    )
    assert read_blocks(make_docx(table))[0].widths == []


# --- the Ricos shapes, each confirmed in reference/ricos-schema ------------------


def test_a_picture_drawn_narrower_than_its_column_asks_for_its_own_width():
    """`PluginContainerData_Width.custom`: "A custom width value in pixels", a
    string (ricos_document.d.ts l.181, ricos.jtd.json, the REST reference). The
    JTD makes `size` and `custom` one-of, so only `custom` is written."""
    narrow = Figure(
        filename="a.png",
        width=1495,
        height=871,
        display_width=322,
        display_height=187,
        column=624,
    )
    full = Figure(
        filename="b.png",
        width=2596,
        height=535,
        display_width=624,
        display_height=129,
        column=624,
    )
    nodes = emit([narrow, full])["nodes"]
    assert nodes[0]["imageData"]["containerData"] == {
        "width": {"custom": "322"},
        "alignment": "CENTER",
        "textWrap": True,
    }
    assert nodes[1]["imageData"]["containerData"]["width"] == {"size": "CONTENT"}


def test_a_picture_with_no_drawn_size_keeps_the_content_width():
    node = emit([Figure(filename="a.png", width=10, height=10)])["nodes"][0]
    assert node["imageData"]["containerData"]["width"] == {"size": "CONTENT"}


def test_table_widths_become_cols_width_ratio():
    """`TableData.dimensions.colsWidthRatio`: float64 elements, "each column
    width as a fraction to the width of table" (REST reference; the typings and
    the JTD say the same)."""
    cell = [Para()]
    table = Table(rows=[[cell, cell]], header_row=True, widths=[0.20351, 0.79649])
    node = emit([table])["nodes"][0]
    assert node["tableData"] == {
        "rowHeader": True,
        "dimensions": {"colsWidthRatio": [0.2035, 0.7965]},
    }


def test_a_table_with_no_widths_is_the_shape_it_was():
    cell = [Para()]
    node = emit([Table(rows=[[cell, cell]], header_row=False)])["nodes"][0]
    assert node["tableData"] == {"rowHeader": False}


# --- the command line writes what Word shows ------------------------------------


def _convert(tmp_path, monkeypatch, body, media):
    from conftest import make_docx

    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    path = tmp_path / "doc.docx"
    rels = {f"rId{5 + k}": f"media/{name}" for k, name in enumerate(media)}
    path.write_bytes(
        make_docx(
            para("One", style="Heading1") + body + _sect(),
            rels=rels,
            media={f"word/media/{n}": png(*s) for n, s in media.items()},
        )
    )
    manifest = convert(str(path))
    return manifest, tmp_path / "ricos" / "doc"


def test_convert_writes_the_picture_as_word_crops_it(tmp_path, monkeypatch):
    body = f"<w:p>{picture('rId5', size=(624, 221), crop={'b': '33696'})}</w:p>"
    manifest, out = _convert(tmp_path, monkeypatch, body, {"image1.png": (1610, 860)})
    with Image.open(out / "figures" / "image1.png") as im:
        assert im.size == (1610, 570)
    fig = manifest["figures"][0]
    assert (fig["width"], fig["height"]) == (1610, 570)
    assert fig["crop"] == [0.0, 0.0, 0.0, 0.33696]
    part = json.loads((out / "part-01.json").read_text(encoding="utf-8"))
    image = next(n for n in part["nodes"] if n["type"] == "IMAGE")
    assert (
        image["imageData"]["image"]["width"],
        image["imageData"]["image"]["height"],
    ) == (
        1610,
        570,
    )


def test_one_stored_picture_cropped_two_ways_is_written_twice(tmp_path, monkeypatch):
    """The crop belongs to the drawing, not to the file: one picture drawn
    whole in one place and cropped in another keeps its whole file, and the
    cropped drawing gets a file of its own."""
    body = (
        f"<w:p>{picture('rId5', size=(300, 150))}</w:p>"
        f"<w:p>{picture('rId5', size=(300, 75), crop={'t': '50000'})}</w:p>"
    )
    manifest, out = _convert(tmp_path, monkeypatch, body, {"image1.png": (400, 200)})
    names = [f["filename"] for f in manifest["figures"]]
    assert names == ["image1.png", "image1-crop1.png"]
    with Image.open(out / "figures" / "image1.png") as im:
        assert im.size == (400, 200)
    with Image.open(out / "figures" / "image1-crop1.png") as im:
        assert im.size == (400, 100)
    assert manifest["unreferenced_media"] == []
    assert manifest["missing_media"] == []


def test_the_manifest_records_word_widths_the_line_and_the_text_width(
    tmp_path, monkeypatch
):
    body = (
        f"<w:p>{picture('rId5', size=(322, 187))}</w:p>"
        "<w:p>"
        + _run("the form ")
        + picture("rId6", size=(185, 15))
        + _run(". Then")
        + "</w:p>"
    )
    manifest, _ = _convert(
        tmp_path,
        monkeypatch,
        body,
        {"image1.png": (1495, 871), "image2.png": (484, 38)},
    )
    assert manifest["text_width"] == 624
    first, second = manifest["figures"]
    assert (first["word_width"], first["word_height"]) == (322, 187)
    assert "inline" not in first
    assert second["inline"] is True
    assert "offset" not in second
    assert second["joins"] == "both"
    assert (second["word_width"], second["word_height"]) == (185, 15)


def test_extent_units_are_the_ones_word_writes():
    """A guard on the fixture itself: 9525 EMU to the CSS pixel."""
    assert EMU_PER_PX * 96 == 914400
