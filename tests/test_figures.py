"""Pictures, the caption Word leaves under them, and the number they carry.

A figure is two paragraphs in the file and one thing on the page, and nothing but
their order says so. If the pairing is not made here it cannot be made later: the
caption would arrive as an ordinary italic line, the picture as a bare image, and
the reader would have to guess which line belongs to which picture. The number
comes from the same reading order, so it is settled here too.
"""

from conftest import oversized_png, para, picture, png

from tools.ricos.blocks import Figure, Para
from tools.ricos.docx_read import read_blocks

PICTURE = picture()
DRAWING = f"<w:p>{PICTURE}</w:p>"


def test_reads_figure_and_pairs_caption(docx_factory):
    body = DRAWING + (
        "<w:p><w:r><w:rPr><w:i/></w:rPr>"
        "<w:t>Figure 1. Lateral response of a building.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(640, 480)},
        )
    )
    figs = [b for b in blocks if isinstance(b, Figure)]
    assert len(figs) == 1
    assert figs[0].filename == "image1.png"
    assert figs[0].width == 640
    assert figs[0].height == 480
    assert figs[0].caption == "Figure 1. Lateral response of a building."
    assert figs[0].number == 1
    # the caption paragraph is consumed, not left behind as text
    assert not any(
        isinstance(b, Para) and b.runs and "Lateral" in b.runs[0].text for b in blocks
    )


def test_numbers_figures_in_order(docx_factory):
    body = DRAWING + DRAWING
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    figs = [b for b in blocks if isinstance(b, Figure)]
    assert [f.number for f in figs] == [1, 2]


def test_keeps_prose_written_around_a_picture(docx_factory):
    """Two documents anchor a picture inside the paragraph that describes it.

    Ricos has no inline image, so the picture is hoisted out — but the sentences
    it was sitting in are ordinary body text and have to come with it.
    """
    body = (
        "<w:p><w:r><w:t>The analytical approach works well </w:t></w:r>"
        + PICTURE
        + "<w:r><w:t>for simple cross sections.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[1].runs[0].text == (
        "The analytical approach works well for simple cross sections."
    )


def test_pairs_a_caption_sharing_the_picture_paragraph(docx_factory):
    """One caption is typed into the picture's own paragraph, not the next one."""
    body = (
        f"<w:p>{PICTURE}<w:r><w:rPr><w:i/></w:rPr>"
        "<w:t>Figure 5. Two ways of obtaining the equation.</w:t>"
        "</w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].caption == "Figure 5. Two ways of obtaining the equation."


def test_a_cross_reference_under_a_picture_is_taken_as_its_caption(docx_factory):
    """The edge of the rule, written down rather than left to be discovered.

    Captions here are not reliably italic, so what marks one is that it opens the
    way the author numbers his figures. A body sentence that opens with a
    cross-reference opens the same way and is absorbed too. Three such sentences
    follow a picture in the corpus, and all three sit second, behind the real
    caption, where the test below stops them. A sentence sitting first would land
    here instead; restoring the italic condition is one line.
    """
    body = DRAWING + (
        "<w:p><w:r><w:t>Figure 6 (d) shows the dispersion curves for the rail "
        "section, and the same pattern recurs in every other section.</w:t>"
        "</w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].caption.startswith("Figure 6 (d) shows the dispersion")


def test_keeps_the_first_caption_when_two_lines_follow_one_picture(docx_factory):
    """A second "Figure N." line belongs to the text, not to the picture above.

    This is live, not hypothetical: three figures in the corpus are followed by
    their caption and then by a sentence opening "Figure 13 puts ...", "Table 1
    pulls ...", "Figure 18 below zooms ...". Drop the guard and those captions
    are overwritten and the sentences vanish from the flow.
    """
    body = DRAWING + (
        "<w:p><w:r><w:t>Figure 1. Dispersion curves.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>Figure 2. The rail section.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[0].caption == "Figure 1. Dispersion curves."
    assert blocks[1].runs[0].text == "Figure 2. The rail section."


def test_leaves_an_italic_line_that_is_not_a_caption_alone(docx_factory):
    """Emphasis under a picture is not a caption; only the writer's numbering is."""
    body = DRAWING + (
        "<w:p><w:r><w:rPr><w:i/></w:rPr><w:t>as shown above</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[0].caption == ""


def test_reads_every_picture_in_one_paragraph(docx_factory):
    """Signal Processing lines book covers up two to four to a paragraph."""
    body = f"<w:p>{picture('rId5')}{picture('rId6')}</w:p>"
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png", "rId6": "media/image2.png"},
            media={
                "word/media/image1.png": png(10, 10),
                "word/media/image2.png": png(20, 30),
            },
        )
    )
    assert [type(b) for b in blocks] == [Figure, Figure]
    assert [b.filename for b in blocks] == ["image1.png", "image2.png"]
    assert [(b.width, b.height) for b in blocks] == [(10, 10), (20, 30)]
    assert [b.number for b in blocks] == [1, 2]


def test_figure_survives_an_image_that_cannot_be_measured(docx_factory):
    """A picture Word kept but Pillow cannot open still belongs on the page."""
    blocks = read_blocks(
        docx_factory(
            DRAWING,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": b"not a png"},
        )
    )
    assert blocks[0].filename == "image1.png"
    assert (blocks[0].width, blocks[0].height) == (0, 0)


def test_an_oversized_picture_costs_its_measurements_and_not_the_document(docx_factory):
    """`Image.DecompressionBombError` derives from Exception, not from OSError.

    The narrowed catch beside this one lists the OSError family, so one picture
    declaring more pixels than Pillow will decode used to take the whole
    document's read down with it - the opposite of what `_figure` promises one
    line above. Not in this corpus; a photograph straight off a modern camera
    is not far off the limit.
    """
    blocks = read_blocks(
        docx_factory(
            DRAWING,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": oversized_png()},
        )
    )
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].filename == "image1.png"
    assert (blocks[0].width, blocks[0].height) == (0, 0)


def test_words_own_caption_style_says_caption_whatever_the_line_says(docx_factory):
    """The clause the regex cannot supply for itself.

    Three paragraphs in this corpus carry Word's `Caption` style and all three
    are captions `CAPTION_RE` already catches, so this changes nothing here.
    What it buys is the case the regex is known to get wrong in both
    directions: it can only read the first two words, and the style is the
    author saying outright which lines are captions.
    """
    body = DRAWING + para("A rail section, measured on the west span.", style="Caption")
    blocks = read_blocks(
        docx_factory(
            body,
            rels={"rId5": "media/image1.png"},
            media={"word/media/image1.png": png(10, 10)},
        )
    )
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].caption == "A rail section, measured on the west span."


def test_figure_whose_relationship_is_missing_has_no_filename(docx_factory):
    """The two faults stay apart: nothing to fetch, versus fetched but unreadable."""
    blocks = read_blocks(docx_factory(DRAWING))
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].rel_id == "rId5"
    assert blocks[0].filename == ""
    assert (blocks[0].width, blocks[0].height) == (0, 0)


def test_a_text_boxs_paragraphs_are_hoisted_after_the_paragraph_that_anchors_it(
    docx_factory,
):
    """A text box is a drawing holding paragraphs, and Word writes it twice:
    once as a `wps` shape and again as VML under `mc:Fallback` for older
    readers. Its words are content and used to be dropped; the fallback copy
    must not double them. A picture inside the box is read once, in the box.
    """
    box = (
        "<w:txbxContent><w:p><w:r><w:t>Key takeaway</w:t></w:r></w:p>"
        f"<w:p>{picture('rId7')}</w:p></w:txbxContent>"
    )
    body = (
        '<w:p><w:r><w:t>anchor </w:t></w:r><w:r><mc:AlternateContent><mc:Choice Requires="wps">'
        f"<w:drawing><wp:anchor><a:graphic><a:graphicData><wps:wsp><wps:txbx>{box}</wps:txbx>"
        "</wps:wsp></a:graphicData></a:graphic></wp:anchor></w:drawing></mc:Choice>"
        f"<mc:Fallback><w:pict><v:shape><v:textbox>{box}</v:textbox></v:shape></w:pict></mc:Fallback>"
        "</mc:AlternateContent></w:r><w:r><w:t>text.</w:t></w:r></w:p>" + para("after")
    )
    blocks = read_blocks(docx_factory(body, rels={"rId7": "media/image7.png"}))
    assert [type(b) for b in blocks] == [Para, Para, Figure, Para]
    assert [b.runs[0].text for b in blocks if isinstance(b, Para)] == [
        "anchor text.",
        "Key takeaway",
        "after",
    ]
    assert blocks[2].filename == "image7.png" and blocks[2].number == 1


def test_a_text_box_written_only_as_vml_is_still_read(docx_factory):
    body = (
        "<w:p><w:r><w:pict><v:shape><v:textbox><w:txbxContent>"
        "<w:p><w:r><w:t>old style</w:t></w:r></w:p>"
        "</w:txbxContent></v:textbox></v:shape></w:pict></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert [b.runs[0].text for b in blocks if b.runs] == ["old style"]
