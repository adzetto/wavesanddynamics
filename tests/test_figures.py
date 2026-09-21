"""Pictures, the caption Word leaves under them, and the number they carry.

A figure is two paragraphs in the file and one thing on the page, and nothing but
their order says so. If the pairing is not made here it cannot be made later: the
caption would arrive as an ordinary italic line, the picture as a bare image, and
the reader would have to guess which line belongs to which picture. The number
comes from the same reading order, so it is settled here too.
"""
import struct
import zlib

from tools.ricos.blocks import Figure, Para
from tools.ricos.docx_read import read_blocks

PICTURE = (
    '<w:r><w:drawing><wp:inline>'
    '<a:graphic><a:graphicData><pic:pic><pic:blipFill>'
    '<a:blip r:embed="rId5"/>'
    "</pic:blipFill></pic:pic></a:graphicData></a:graphic>"
    "</wp:inline></w:drawing></w:r>"
)
DRAWING = f"<w:p>{PICTURE}</w:p>"


def _png(width, height):
    """Smallest valid PNG with the given dimensions."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(b"\x00" * (width * 3 + 1) * height))
            + chunk(b"IEND", b""))


def test_reads_figure_and_pairs_caption(docx_factory):
    body = DRAWING + (
        "<w:p><w:r><w:rPr><w:i/></w:rPr>"
        "<w:t>Figure 1. Lateral response of a building.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(body, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": _png(640, 480)})
    )
    figs = [b for b in blocks if isinstance(b, Figure)]
    assert len(figs) == 1
    assert figs[0].filename == "image1.png"
    assert figs[0].width == 640
    assert figs[0].height == 480
    assert figs[0].caption == "Figure 1. Lateral response of a building."
    assert figs[0].number == 1
    # the caption paragraph is consumed, not left behind as text
    assert not any(isinstance(b, Para) and b.runs and "Lateral" in b.runs[0].text
                   for b in blocks)


def test_numbers_figures_in_order(docx_factory):
    body = DRAWING + DRAWING
    blocks = read_blocks(
        docx_factory(body, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": _png(10, 10)})
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
        docx_factory(body, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": _png(10, 10)})
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
        docx_factory(body, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": _png(10, 10)})
    )
    assert [type(b) for b in blocks] == [Figure]
    assert blocks[0].caption == "Figure 5. Two ways of obtaining the equation."


def test_leaves_an_italic_line_that_is_not_a_caption_alone(docx_factory):
    """Emphasis under a picture is not a caption; only the writer's numbering is."""
    body = DRAWING + (
        "<w:p><w:r><w:rPr><w:i/></w:rPr><w:t>as shown above</w:t></w:r></w:p>"
    )
    blocks = read_blocks(
        docx_factory(body, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": _png(10, 10)})
    )
    assert [type(b) for b in blocks] == [Figure, Para]
    assert blocks[0].caption == ""


def test_figure_survives_an_image_that_cannot_be_measured(docx_factory):
    """A picture Word kept but Pillow cannot open still belongs on the page."""
    blocks = read_blocks(
        docx_factory(DRAWING, rels={"rId5": "media/image1.png"},
                     media={"word/media/image1.png": b"not a png"})
    )
    assert blocks[0].filename == "image1.png"
    assert (blocks[0].width, blocks[0].height) == (0, 0)
