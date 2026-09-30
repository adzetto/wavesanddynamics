"""Prove the synthetic .docx fixture before anything is built on it.

Every later test trusts make_docx() and para() to produce what Word would. If the
fixture itself wrote malformed XML or mis-typed relationships, failures downstream
would point at the converter instead of here.
"""

import io
import zipfile

from lxml import etree

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def part(docx_bytes, name):
    """Parse one XML part out of the .docx; malformed XML raises XMLSyntaxError here."""
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
        return etree.fromstring(z.read(name))


def only_relationship(docx_bytes):
    """The single <Relationship> the document part declares."""
    rels = part(docx_bytes, "word/_rels/document.xml.rels")
    (rel,) = rels.xpath("//rel:Relationship", namespaces=NS)
    return rel


def test_text_with_ampersand_and_lt_round_trips(docx_factory, para_factory):
    text = "Ali & Veli, p < 0.05"
    doc = part(docx_factory(para_factory(text)), "word/document.xml")
    assert doc.xpath("string(//w:t)", namespaces=NS) == text


def test_style_with_double_quote_survives_as_attribute(docx_factory, para_factory):
    style = 'Heading "Quoted"'
    doc = part(docx_factory(para_factory("x", style=style)), "word/document.xml")
    assert doc.xpath("string(//w:pStyle/@w:val)", namespaces=NS) == style


def test_http_target_is_an_external_hyperlink_relationship(docx_factory):
    rel = only_relationship(docx_factory("", rels={"rId9": "https://ruder.io/"}))
    assert rel.get("Id") == "rId9"
    assert rel.get("Type").endswith("/hyperlink")
    assert rel.get("Target") == "https://ruder.io/"
    assert rel.get("TargetMode") == "External"


def test_media_target_is_an_internal_image_relationship(docx_factory):
    rel = only_relationship(docx_factory("", rels={"rId5": "media/image1.png"}))
    assert rel.get("Type").endswith("/image")
    assert rel.get("Target") == "media/image1.png"
    assert rel.get("TargetMode") is None


def test_ampersand_in_target_is_escaped(docx_factory):
    url = "https://example.org/?a=1&b=2"
    assert only_relationship(docx_factory("", rels={"rId1": url})).get("Target") == url


def test_alternate_content_and_wp14_attribute_parse(docx_factory):
    body = (
        "<w:p><w:r><mc:AlternateContent><mc:Choice><w:drawing/></mc:Choice>"
        "<mc:Fallback><w:pict/></mc:Fallback></mc:AlternateContent></w:r></w:p>"
        '<w:p><w:r><w:drawing><wp:inline wp14:anchorId="1A2B3C4D"/></w:drawing></w:r></w:p>'
    )
    doc = part(docx_factory(body), "word/document.xml")
    assert doc.xpath("count(//mc:AlternateContent)", namespaces=NS) == 1
    assert doc.xpath("string(//wp:inline/@wp14:anchorId)", namespaces=NS) == "1A2B3C4D"
    ignorable = doc.get(f"{{{NS['mc']}}}Ignorable")
    assert ignorable == "w14 wp14"
    assert set(ignorable.split()) <= set(doc.nsmap)
