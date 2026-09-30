"""Footnotes and endnotes: the mark in the text, and the note it points at.

No document in the corpus has one - six of the seven carry a footnotes part,
but it holds only Word's separator lines - and the reference a run carries
is an empty element, so a note would have vanished twice over: the mark from
the sentence and the note from the document, with nothing said.

Ricos has no note node. What survives exactly is the pairing: a numbered mark
where the reference stood, and the notes in that order at the end of the
document, each opening with its number. Footnotes and endnotes share one
sequence, in reading order, because on a single page there is no foot.
"""

from conftest import XMLNS_W, para

from tools.ricos.blocks import Para
from tools.ricos.docx_read import read_blocks
from tools.ricos.emit import emit


def notes_xml(part, *notes):
    """word/footnotes.xml or word/endnotes.xml, with Word's separators in front."""
    tag = part[:-1]
    sep = (
        f'<w:{tag} w:type="separator" w:id="-1"><w:p><w:r><w:separator/></w:r></w:p></w:{tag}>'
        f'<w:{tag} w:type="continuationSeparator" w:id="0"><w:p><w:r><w:continuationSeparator/>'
        f"</w:r></w:p></w:{tag}>"
    )
    body = "".join(
        f'<w:{tag} w:id="{nid}">'
        + "".join(
            f'<w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>'
            f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:{tag[:-4]}Ref/></w:r>'
            f'<w:r><w:t xml:space="preserve"> {text}</w:t></w:r></w:p>'
            for text in texts
        )
        + f"</w:{tag}>"
        for nid, texts in notes
    )
    return (
        f'<?xml version="1.0" encoding="UTF-8"?><w:{part} {XMLNS_W}>{sep}{body}</w:{part}>'
    ).encode()


def ref(kind, nid):
    return (
        f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/><w:vertAlign w:val="superscript"/></w:rPr>'
        f'<w:{kind}Reference w:id="{nid}"/></w:r>'
    )


def test_a_footnote_becomes_a_mark_in_the_text_and_a_note_at_the_end(docx_factory):
    body = (
        f"<w:p><w:r><w:t>Measured on the west span</w:t></w:r>{ref('footnote', '1')}"
        "<w:r><w:t>.</w:t></w:r></w:p>" + para("Next paragraph.")
    )
    blocks = read_blocks(
        docx_factory(
            body,
            media={
                "word/footnotes.xml": notes_xml(
                    "footnotes", ("1", ["Kaynardag et al., 2019."])
                )
            },
        )
    )
    assert [type(b) for b in blocks] == [Para, Para, Para]
    assert blocks[0].runs[0].text == "Measured on the west span[1]."
    assert "".join(r.text for r in blocks[2].runs) == "[1] Kaynardag et al., 2019."


def test_notes_are_numbered_in_reading_order_across_both_kinds(docx_factory):
    body = (
        f"<w:p><w:r><w:t>a</w:t></w:r>{ref('endnote', '7')}<w:r><w:t>b</w:t></w:r>"
        f"{ref('footnote', '2')}</w:p>"
    )
    blocks = read_blocks(
        docx_factory(
            body,
            media={
                "word/footnotes.xml": notes_xml("footnotes", ("2", ["foot"])),
                "word/endnotes.xml": notes_xml("endnotes", ("7", ["end"])),
            },
        )
    )
    assert blocks[0].runs[0].text == "a[1]b[2]"
    assert ["".join(r.text for r in b.runs) for b in blocks[1:]] == [
        "[1] end",
        "[2] foot",
    ]


def test_a_note_of_several_paragraphs_keeps_them_and_numbers_the_first(docx_factory):
    body = f"<w:p><w:r><w:t>a</w:t></w:r>{ref('footnote', '1')}</w:p>"
    blocks = read_blocks(
        docx_factory(
            body,
            media={
                "word/footnotes.xml": notes_xml("footnotes", ("1", ["first", "second"]))
            },
        )
    )
    assert ["".join(r.text for r in b.runs) for b in blocks[1:]] == [
        "[1] first",
        " second",
    ]


def test_a_reference_to_a_note_that_is_not_there_leaves_no_mark(docx_factory):
    body = f"<w:p><w:r><w:t>a</w:t></w:r>{ref('footnote', '9')}<w:r><w:t>b</w:t></w:r></w:p>"
    blocks = read_blocks(
        docx_factory(body, media={"word/footnotes.xml": notes_xml("footnotes")})
    )
    assert [b.runs[0].text for b in blocks] == ["ab"]


def test_the_notes_reach_the_page_after_the_body(docx_factory):
    body = f"<w:p><w:r><w:t>a</w:t></w:r>{ref('footnote', '1')}</w:p>"
    blocks = read_blocks(
        docx_factory(
            body, media={"word/footnotes.xml": notes_xml("footnotes", ("1", ["note"]))}
        )
    )
    texts = [
        "".join(t["textData"]["text"] for t in n["nodes"])
        for n in emit(blocks)["nodes"]
    ]
    assert texts == ["a[1]", "[1] note"]
