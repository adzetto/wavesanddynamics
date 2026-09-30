"""Build a tiny .docx in memory so the unit tests never open the real 10 MB files.

A .docx is a zip with a fixed skeleton; only word/document.xml carries content.
Tests hand this helper a body fragment and get real bytes back, so the reader is
exercised against the same XML Word actually writes.
"""

import io
import struct
import zipfile
import zlib
from xml.sax.saxutils import escape

import pytest

# A namespace *declaration*, to paste into a document element - not the Clark
# notation `W` that `docx_read` and `docx2ricos` use to name an element. The two
# are opposite halves of the same namespace and one module imports from the
# other, so they must not share a name.
XMLNS_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
PIC = 'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
WP = 'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
MC = 'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
WP14 = (
    'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"'
)
W14 = 'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
VML = 'xmlns:v="urn:schemas-microsoft-com:vml"'
OFFICE = 'xmlns:o="urn:schemas-microsoft-com:office:office"'
MATH = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
WPS = 'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"'
W16SE = 'xmlns:w16se="http://schemas.microsoft.com/office/word/2015/wordml/symex"'
# Word wraps drawings in mc:AlternateContent and marks its 2010 namespaces
# ignorable, so a snippet pasted out of a real file needs these declarations.
NAMESPACES = (
    f"{XMLNS_W} {R} {A} {PIC} {WP} {MC} {WP14} {W14} {VML} {OFFICE} {MATH} {WPS} {W16SE} "
    'mc:Ignorable="w14 wp14"'
)

SHAPE_URI = "http://schemas.microsoft.com/office/word/2010/wordprocessingShape"

IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
HYPERLINK_REL = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
)

CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    "</Types>"
)

ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
    "</Relationships>"
)


def escape_attr(value):
    """Escape `value` for a double-quoted XML attribute."""
    return escape(value, {'"': "&quot;"})


def relationship(rid, target):
    """One <Relationship> element.

    An http(s) target is an external hyperlink; anything else is an image part.
    """
    if target.startswith(("http://", "https://")):
        return (
            f'<Relationship Id="{escape_attr(rid)}" Type="{HYPERLINK_REL}" '
            f'Target="{escape_attr(target)}" TargetMode="External"/>'
        )
    return (
        f'<Relationship Id="{escape_attr(rid)}" Type="{IMAGE_REL}" '
        f'Target="{escape_attr(target)}"/>'
    )


def make_docx(body_xml, rels=None, media=None):
    """Return .docx bytes whose word/document.xml body is `body_xml`.

    rels  : {rId: target} entries for word/_rels/document.xml.rels; an http(s)
            target becomes an external hyperlink, anything else an image part
    media : {"word/media/image1.png": b"..."} extra parts
    """
    rels = rels or {}
    media = media or {}
    rel_xml = "".join(relationship(rid, target) for rid, target in rels.items())
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("_rels/.rels", ROOT_RELS)
        z.writestr(
            "word/document.xml",
            f'<?xml version="1.0" encoding="UTF-8"?>'
            f"<w:document {NAMESPACES}><w:body>{body_xml}</w:body></w:document>",
        )
        z.writestr(
            "word/_rels/document.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rel_xml}</Relationships>",
        )
        for name, data in media.items():
            z.writestr(name, data)
    return buf.getvalue()


def para(text, style=None, bold=False):
    """One <w:p> with a single run; `text` and `style` are escaped the way Word does."""
    ppr = f'<w:pPr><w:pStyle w:val="{escape_attr(style)}"/></w:pPr>' if style else ""
    rpr = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f"<w:p>{ppr}<w:r>{rpr}<w:t>{escape(text)}</w:t></w:r></w:p>"


EMU_PER_PX = 9525  # DrawingML measures in EMU: 914400 an inch, 96 CSS px an inch


def picture(rel_id="rId5", size=None, crop=None, anchor=False):
    """One run holding a picture that points at `rel_id`.

    It lives here with NAMESPACES because it is only well-formed inside them:
    the prefixes it uses are declared once, on the document element above, and a
    second copy of this XML would go stale against them unnoticed.

    With no keywords it is the bare inline picture every older test uses, with
    no size of its own. `size` is the (width, height) Word draws it at, in CSS
    px at 96 dpi, written as `wp:extent` in EMU. `crop` is `a:srcRect` as Word
    writes it: {"l": ..., "t": ..., "r": ..., "b": ...} in thousandths of a
    percent, a negative inset being padding. `anchor` floats it (`wp:anchor`)
    instead of setting it in the line.
    """
    host = "wp:anchor" if anchor else "wp:inline"
    extent = (
        f'<wp:extent cx="{size[0] * EMU_PER_PX}" cy="{size[1] * EMU_PER_PX}"/>'
        if size
        else ""
    )
    src = (
        "<a:srcRect " + " ".join(f'{k}="{v}"' for k, v in crop.items()) + "/>"
        if crop
        else ""
    )
    return (
        f"<w:r><w:drawing><{host}>{extent}"
        "<a:graphic><a:graphicData><pic:pic><pic:blipFill>"
        f'<a:blip r:embed="{rel_id}"/>{src}'
        "</pic:blipFill></pic:pic></a:graphicData></a:graphic>"
        f"</{host}></w:drawing></w:r>"
    )


def shape(name="Straight Connector 1"):
    """One run holding a drawing that has no picture in it.

    Word writes a connector line, or a shape the author drew, as a `w:drawing`
    like any other - but with no `a:blip` under it, so there is no image part to
    carry over to Wix. Four of this corpus's 105 drawings are this, and telling
    them apart from a picture that went missing is why both are counted.

    The `uri` is the one Word writes for a shape, and it is what says which kind
    of drawing this is. Leaving it off would make the fixture agree with code
    that cannot tell a shape from a chart, which is the mistake it is here to
    catch; the corpus's four blind drawings all carry exactly this.

    Here beside `picture` for the same reason: the prefixes are declared once,
    on the document element, and a second copy would go stale against them.
    """
    return (
        "<w:r><w:drawing><wp:inline>"
        f'<wp:docPr id="1" name="{escape_attr(name)}"/>'
        f'<a:graphic><a:graphicData uri="{SHAPE_URI}"/></a:graphic>'
        "</wp:inline></w:drawing></w:r>"
    )


def _chunk(tag, data):
    """One PNG chunk: length, tag, payload, CRC."""
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def png(width, height):
    """The smallest valid PNG of the given dimensions.

    Here rather than in one test module because two of them need it and they
    need it for different reasons: the reader measures a figure with Pillow,
    and the CLI writes those measurements into the manifest for the next phase
    to lay out with. A test that hands either of them bytes Pillow cannot open
    measures 0 x 0, which is the value the code produces when it fails - so it
    passes whatever the code does, and pinning it proves nothing.
    """
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"\x00" * (width * 3 + 1) * height))
        + _chunk(b"IEND", b"")
    )


def oversized_png():
    """A PNG declaring more pixels than Pillow is willing to decode.

    Pillow compares the declared size with MAX_IMAGE_PIXELS as soon as it has
    read the header and raises `Image.DecompressionBombError`, which derives
    from Exception and not from OSError. Nothing is decoded, so the file stays
    a few dozen bytes however many pixels it claims.
    """
    ihdr = struct.pack(">IIBBBBB", 30_000, 30_000, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(b"\x00" * 16))
        + _chunk(b"IEND", b"")
    )


@pytest.fixture
def docx_factory():
    return make_docx


@pytest.fixture
def para_factory():
    return para
