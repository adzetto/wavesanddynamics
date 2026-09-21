"""Build a tiny .docx in memory so the unit tests never open the real 10 MB files.

A .docx is a zip with a fixed skeleton; only word/document.xml carries content.
Tests hand this helper a body fragment and get real bytes back, so the reader is
exercised against the same XML Word actually writes.
"""
import io
import zipfile
from xml.sax.saxutils import escape

import pytest

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
PIC = 'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"'
WP = 'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"'
MC = 'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"'
WP14 = 'xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"'
W14 = 'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
VML = 'xmlns:v="urn:schemas-microsoft-com:vml"'
OFFICE = 'xmlns:o="urn:schemas-microsoft-com:office:office"'
MATH = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
# Word wraps drawings in mc:AlternateContent and marks its 2010 namespaces
# ignorable, so a snippet pasted out of a real file needs these declarations.
NAMESPACES = (
    f"{W} {R} {A} {PIC} {WP} {MC} {WP14} {W14} {VML} {OFFICE} {MATH} "
    'mc:Ignorable="w14 wp14"'
)

IMAGE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
HYPERLINK_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"

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


def picture(rel_id="rId5"):
    """One run holding an inline picture that points at `rel_id`.

    It lives here with NAMESPACES because it is only well-formed inside them:
    the prefixes it uses are declared once, on the document element above, and a
    second copy of this XML would go stale against them unnoticed.
    """
    return (
        '<w:r><w:drawing><wp:inline>'
        '<a:graphic><a:graphicData><pic:pic><pic:blipFill>'
        f'<a:blip r:embed="{rel_id}"/>'
        "</pic:blipFill></pic:pic></a:graphicData></a:graphic>"
        "</wp:inline></w:drawing></w:r>"
    )


@pytest.fixture
def docx_factory():
    return make_docx


@pytest.fixture
def para_factory():
    return para
