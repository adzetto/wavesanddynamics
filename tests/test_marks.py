"""What a run means once the style hierarchy has had its say.

`rpr.find()` sees direct formatting and nothing else, and the handover said so:
a bold that arrives through the paragraph style was invisible. Measured, the
corpus does carry marks that way - the Title paragraphs of two documents are
bold through their style and nothing else, Sound Detection's captions are
italic the same way, and every hyperlink is underlined and blue through Word's
`Hyperlink` character style. The rest of this file is the other things a run
carries that were never read: colour, highlight, super- and subscript,
strikethrough, capitals, hidden text, symbol characters, and the text that
sits inside a drawing and must not be read as the paragraph's own.
"""

import pytest
from conftest import XMLNS_W, para

from tools.ricos.blocks import Para, Run
from tools.ricos.docx_read import read_blocks


def styles_xml(*styles, defaults=""):
    """A word/styles.xml declaring `styles`, each an XML string of a w:style.

    `defaults` is the rPr of docDefaults, the formatting every run starts from.
    """
    dd = f"<w:docDefaults><w:rPrDefault><w:rPr>{defaults}</w:rPr></w:rPrDefault></w:docDefaults>"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f"<w:styles {XMLNS_W}>{dd}{''.join(styles)}</w:styles>"
    ).encode()


def style(sid, kind="paragraph", rpr="", based=None, ppr=""):
    based_xml = f'<w:basedOn w:val="{based}"/>' if based else ""
    return (
        f'<w:style w:type="{kind}" w:styleId="{sid}"><w:name w:val="{sid}"/>{based_xml}'
        f"{f'<w:pPr>{ppr}</w:pPr>' if ppr else ''}"
        f"{f'<w:rPr>{rpr}</w:rPr>' if rpr else ''}</w:style>"
    )


def run(text, rpr=""):
    return f'<w:r>{f"<w:rPr>{rpr}</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{text}</w:t></w:r>'


def styled_run(text, rstyle, rpr=""):
    return run(text, f'<w:rStyle w:val="{rstyle}"/>{rpr}')


def p(*runs, style_id=None):
    ppr = f'<w:pPr><w:pStyle w:val="{style_id}"/></w:pPr>' if style_id else ""
    return f"<w:p>{ppr}{''.join(runs)}</w:p>"


def first_run(docx_factory, body, styles=None):
    media = {"word/styles.xml": styles} if styles else None
    return read_blocks(docx_factory(body, media=media))[0].runs[0]


# --- the style hierarchy ---------------------------------------------------


def test_bold_inherited_from_the_paragraph_style(docx_factory):
    """The Title paragraphs of Sound Detection and From Bridges to Photons are
    bold this way and no other, and arrived on the page as plain text."""
    r = first_run(
        docx_factory,
        p(run("From Bridges to Photons"), style_id="Title"),
        styles_xml(style("Title", rpr="<w:b/>")),
    )
    assert r.bold is True


def test_italic_inherited_from_a_character_style(docx_factory):
    r = first_run(
        docx_factory,
        p(styled_run("stress", "Emphasis")),
        styles_xml(style("Emphasis", kind="character", rpr="<w:i/>")),
    )
    assert r.italic is True


def test_the_chain_of_based_on_styles_is_followed(docx_factory):
    """A style says only what differs from the one it is based on."""
    r = first_run(
        docx_factory,
        p(run("x"), style_id="Child"),
        styles_xml(
            style("Root", rpr="<w:b/>"),
            style("Mid", based="Root"),
            style("Child", based="Mid", rpr="<w:i/>"),
        ),
    )
    assert (r.bold, r.italic) == (True, True)


def test_a_child_style_switches_off_what_its_parent_set(docx_factory):
    r = first_run(
        docx_factory,
        p(run("x"), style_id="Child"),
        styles_xml(
            style("Root", rpr="<w:b/>"),
            style("Child", based="Root", rpr='<w:b w:val="0"/>'),
        ),
    )
    assert r.bold is False


def test_direct_formatting_switches_off_an_inherited_mark(docx_factory):
    r = first_run(
        docx_factory,
        p(run("x", '<w:b w:val="0"/>'), style_id="Title"),
        styles_xml(style("Title", rpr="<w:b/>")),
    )
    assert r.bold is False


def test_bold_in_both_the_paragraph_style_and_the_character_style_cancels(docx_factory):
    """Word's toggle rule (ECMA-376 §17.7.3): bold from the paragraph style
    and bold again from the character style is *not* bold. This is the rule
    that makes a "Strong" run inside a bold paragraph come out plain in Word,
    and a reader that adds the two up would show it bold on the page."""
    r = first_run(
        docx_factory,
        p(styled_run("x", "Strong"), style_id="Loud"),
        styles_xml(
            style("Loud", rpr="<w:b/>"), style("Strong", kind="character", rpr="<w:b/>")
        ),
    )
    assert r.bold is False


def test_underline_is_not_a_toggle_the_character_style_simply_wins(docx_factory):
    r = first_run(
        docx_factory,
        p(styled_run("x", "Plain"), style_id="Under"),
        styles_xml(
            style("Under", rpr='<w:u w:val="single"/>'),
            style("Plain", kind="character", rpr='<w:u w:val="none"/>'),
        ),
    )
    assert r.underline is False


def test_document_defaults_supply_what_nothing_else_sets(docx_factory):
    r = first_run(docx_factory, p(run("x")), styles_xml(defaults="<w:i/>"))
    assert r.italic is True


def test_a_style_nobody_declares_is_harmless(docx_factory):
    r = first_run(
        docx_factory,
        p(styled_run("x", "Ghost"), style_id="Nobody"),
        styles_xml(style("Other")),
    )
    assert (r.bold, r.italic, r.underline) == (False, False, False)


def test_a_document_without_a_styles_part_reads_as_before(docx_factory):
    r = first_run(docx_factory, p(run("x", "<w:b/>"), style_id="Title"))
    assert r.bold is True


def test_a_paragraph_marks_own_formatting_is_not_the_texts(docx_factory):
    """`w:pPr/w:rPr` formats the pilcrow, not the words. 55 paragraphs in the
    corpus carry a bold there over text that is not bold."""
    body = "<w:p><w:pPr><w:rPr><w:b/></w:rPr></w:pPr>" + run("x") + "</w:p>"
    assert first_run(docx_factory, body).bold is False


# --- hidden text ---------------------------------------------------------------


@pytest.mark.parametrize("rpr", ["<w:vanish/>", "<w:webHidden/>"])
def test_hidden_text_is_not_read(docx_factory, rpr):
    """`w:vanish` is text Word does not show; `w:webHidden` is text it does not
    show on a web page - the page numbers of every contents list here, 52
    runs. Neither is content the author published."""
    blocks = read_blocks(docx_factory(p(run("shown"), run("secret", rpr))))
    assert [r.text for r in blocks[0].runs] == ["shown"]


def test_hidden_through_a_style_and_unhidden_directly_is_read(docx_factory):
    r = first_run(
        docx_factory,
        p(run("x", '<w:vanish w:val="0"/>'), style_id="Hid"),
        styles_xml(style("Hid", rpr="<w:vanish/>")),
    )
    assert r.text == "x"


# --- colour ---------------------------------------------------------------------

BODY = p(run("a long stretch of ordinary text, the colour most of the document is in"))


@pytest.mark.parametrize(
    ("val", "color"),
    [("7A0000", "#7a0000"), ("auto", ""), ("000000", ""), ("", "")],
)
def test_a_run_colour_is_read_as_lower_case_hex(docx_factory, val, color):
    """Black and `auto` are the page's own colour, not a colour."""
    attr = f' w:val="{val}"' if val else ""
    assert (
        first_run(docx_factory, p(run("x", f"<w:color{attr}/>")) + BODY).color == color
    )


def test_the_colour_most_of_the_text_is_written_in_is_the_body_colour(docx_factory):
    """The ML guide writes 85% of its characters in 262626 by direct
    formatting; the brochure 74% in 1A1A1A. That is the document's black, and
    a decoration on every run of it would fight the site's own text colour
    and cost a tenth of the record. Only a departure from it is a colour."""
    body = (
        p(run("a long stretch of ordinary text", '<w:color w:val="262626"/>'))
        + p(run("more of the same", '<w:color w:val="262626"/>'))
        + p(run("accent", '<w:color w:val="7A0000"/>'))
    )
    blocks = read_blocks(docx_factory(body))
    assert [b.runs[0].color for b in blocks] == ["", "", "#7a0000"]


def test_the_body_colour_is_weighed_by_characters_not_runs(docx_factory):
    body = (
        p(run("x", '<w:color w:val="7A0000"/>'))
        + p(run("y", '<w:color w:val="7A0000"/>'))
        + p(run("a much longer stretch of body text", '<w:color w:val="262626"/>'))
    )
    blocks = read_blocks(docx_factory(body))
    assert [b.runs[0].color for b in blocks] == ["#7a0000", "#7a0000", ""]


def test_the_document_default_colour_is_the_body_colour_whatever_the_count(
    docx_factory,
):
    """Two documents set 222831 in docDefaults; a run that repeats it directly
    says nothing new."""
    body = (
        p(run("a long stretch of body text", '<w:color w:val="222831"/>'))
        + p(run("y", '<w:color w:val="6B7280"/>'))
        + p(run("z"))
    )
    blocks = read_blocks(
        docx_factory(
            body,
            media={"word/styles.xml": styles_xml(defaults='<w:color w:val="222831"/>')},
        )
    )
    assert [b.runs[0].color for b in blocks] == ["", "#6b7280", ""]


def test_a_colour_that_comes_through_a_style_is_read(docx_factory):
    r = first_run(
        docx_factory,
        p(run("x"), style_id="Title") + BODY,
        styles_xml(style("Title", rpr='<w:color w:val="8A0000"/>')),
    )
    assert r.color == "#8a0000"


def test_words_own_link_style_is_not_the_authors_mark(docx_factory):
    """Every hyperlink in the corpus is underlined and blue through Word's
    `Hyperlink` character style, 61 runs, and none of that is a mark the
    author made. Matched on the style's name, which a localized Word keeps
    in English while it translates the id."""
    body = (
        '<w:p><w:hyperlink r:id="rId9">'
        + styled_run("ruder.io", "Kpr")
        + "</w:hyperlink>"
        + run("plain")
        + "</w:p>"
    ) + BODY
    styles = styles_xml(
        '<w:style w:type="character" w:styleId="Kpr"><w:name w:val="Hyperlink"/>'
        '<w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>'
    )
    blocks = read_blocks(
        docx_factory(
            body, rels={"rId9": "https://ruder.io/"}, media={"word/styles.xml": styles}
        )
    )
    link = blocks[0].runs[0]
    assert (link.link, link.underline, link.color) == ("https://ruder.io/", False, "")


def test_the_authors_own_underline_on_a_link_is_kept(docx_factory):
    body = (
        '<w:p><w:hyperlink r:id="rId9">'
        + run("x", '<w:u w:val="single"/>')
        + "</w:hyperlink></w:p>"
    )
    blocks = read_blocks(docx_factory(body, rels={"rId9": "https://x.test/"}))
    assert blocks[0].runs[0].underline is True


def test_body_coloured_runs_merge_with_their_uncoloured_neighbours(docx_factory):
    """Once the body colour is gone the runs on either side of it agree."""
    body = p(
        run("Hel", '<w:color w:val="262626"/>'),
        run("lo"),
        run(" world", '<w:color w:val="262626"/>'),
    )
    blocks = read_blocks(docx_factory(body))
    assert [r.text for r in blocks[0].runs] == ["Hello world"]


@pytest.mark.parametrize(
    ("rpr", "highlight"),
    [
        ('<w:highlight w:val="yellow"/>', "#ffff00"),
        ('<w:highlight w:val="none"/>', ""),
        ('<w:shd w:val="clear" w:fill="FBEAEA"/>', "#fbeaea"),
        ('<w:shd w:val="clear" w:fill="auto"/>', ""),
    ],
)
def test_highlight_and_character_shading_are_a_background(docx_factory, rpr, highlight):
    assert first_run(docx_factory, p(run("x", rpr))).highlight == highlight


# --- the marks Ricos has no decoration for -------------------------------------


@pytest.mark.parametrize(
    ("val", "vertical"),
    [("superscript", "super"), ("subscript", "sub"), ("baseline", "")],
)
def test_super_and_subscript_are_read(docx_factory, val, vertical):
    r = first_run(docx_factory, p(run("2", f'<w:vertAlign w:val="{val}"/>')))
    assert r.vertical == vertical


@pytest.mark.parametrize("rpr", ["<w:strike/>", "<w:dstrike/>"])
def test_strikethrough_is_read(docx_factory, rpr):
    assert first_run(docx_factory, p(run("gone", rpr))).strike is True


def test_capitals_are_applied_to_the_text_and_small_capitals_are_not(docx_factory):
    """`w:caps` shows lower-case letters as capitals; the letters stored are
    still lower case, so the text has to be raised here or the page shows
    what Word hides. Small capitals have no plain-text equivalent."""
    blocks = read_blocks(
        docx_factory(
            p(run("Introduction", "<w:caps/>")) + p(run("Summary", "<w:smallCaps/>"))
        )
    )
    assert [b.runs[0].text for b in blocks] == ["INTRODUCTION", "Summary"]


def test_runs_merge_only_when_every_mark_agrees(docx_factory):
    body = p(
        run("a", '<w:color w:val="7A0000"/>'),
        run("b"),
        run("c", '<w:vertAlign w:val="superscript"/>'),
        run("d", "<w:strike/>"),
        run("e", '<w:highlight w:val="yellow"/>'),
    )
    blocks = read_blocks(docx_factory(body))
    assert [r.text for r in blocks[0].runs] == ["a", "b", "c", "d", "e"]
    assert blocks[0].runs == [
        Run(text="a", color="#7a0000"),
        Run(text="b"),
        Run(text="c", vertical="super"),
        Run(text="d", strike=True),
        Run(text="e", highlight="#ffff00"),
    ]


# --- what a run holds besides w:t ------------------------------------------------


@pytest.mark.parametrize(
    ("font", "char", "text"),
    [
        ("Wingdings", "F0E0", "→"),  # the arrow the ML guide draws twice
        ("Symbol", "F0B7", "•"),  # the bullet
        ("Symbol", "F061", "α"),  # Symbol's a is alpha
        ("Wingdings", "F0FC", "✓"),  # a tick
        ("Webdings", "F041", "�"),
    ],  # nothing known: visible, and counted
)
def test_a_symbol_character_is_mapped_to_the_glyph_it_stands_for(
    docx_factory, font, char, text
):
    """`w:sym` names a glyph in a symbol font, and Word writes nothing else for
    it. Dropped, the ML guide reads "in your mind  explore the data" with two
    spaces where the arrow was. A glyph with no mapping is written as U+FFFD
    rather than silently omitted, so that it can be counted and seen."""
    body = f'<w:p><w:r><w:t>a </w:t><w:sym w:font="{font}" w:char="{char}"/><w:t> b</w:t></w:r></w:p>'
    assert read_blocks(docx_factory(body))[0].runs[0].text == f"a {text} b"


def test_text_inside_a_drawing_is_not_the_paragraphs_text(docx_factory):
    """A run's text is its own `w:t` children. The ML guide holds one glyph
    inside the VML fallback of a drawn shape, and reading every `w:t` under
    the run glued it to the sentence the shape sat in."""
    body = (
        "<w:p><w:r><w:t>Imputation: fill missing values </w:t></w:r>"
        "<w:r><mc:AlternateContent><mc:Fallback><w:pict><v:shape><v:textbox>"
        "<w:txbxContent><w:p><w:r><w:t>😊</w:t></w:r></w:p></w:txbxContent>"
        "</v:textbox></v:shape></w:pict></mc:Fallback></mc:AlternateContent></w:r>"
        "<w:r><w:t>with an estimate.</w:t></w:r></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert [b.runs[0].text for b in blocks if isinstance(b, Para)][0] == (
        "Imputation: fill missing values with an estimate."
    )


def test_an_emoji_written_as_a_symbol_extension_is_read(docx_factory):
    """The one glyph the ML guide keeps in an `mc:AlternateContent` is not a
    drawing: Word 2016 writes an emoji as a `w16se:symEx` choice with the
    plain character as a `w:t` directly under the fallback. That text is the
    run's own - "develop your own 😊." - where a drawing's fallback, one
    element deeper, is not."""
    body = (
        '<w:p><w:r><w:t xml:space="preserve">develop your own </w:t>'
        '<mc:AlternateContent><mc:Choice Requires="w16se">'
        '<w16se:symEx w16se:font="Segoe UI Emoji" w16se:char="1F60A"/></mc:Choice>'
        "<mc:Fallback><w:t>😊</w:t></mc:Fallback></mc:AlternateContent>"
        "<w:t>.</w:t></w:r></w:p>"
    )
    assert read_blocks(docx_factory(body))[0].runs[0].text == "develop your own 😊."


def test_a_fields_instruction_is_not_read_and_its_result_is(docx_factory):
    """Sound Detection numbers its captions with SEQ fields and refers to them
    with REF fields. The instruction is code; the result is the text."""
    body = (
        "<w:p><w:r><w:t>Figure </w:t></w:r>"
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        '<w:r><w:instrText xml:space="preserve"> SEQ Figure \\* ARABIC </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        "<w:r><w:t>1</w:t></w:r>"
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
        "<w:r><w:t>. Sensors.</w:t></w:r></w:p>"
    )
    assert read_blocks(docx_factory(body))[0].runs[0].text == "Figure 1. Sensors."


def test_runs_inside_inline_containers_are_read_and_deleted_text_is_not(docx_factory):
    """`w:fldSimple`, a content control, a smart tag and a tracked insertion
    all hold ordinary runs one level down, where a walk over the paragraph's
    direct children never looked: a citation Word's References tool inserts
    is a content control, and its text vanished. A tracked deletion holds
    text the author removed."""
    body = (
        "<w:p><w:r><w:t>a </w:t></w:r>"
        '<w:fldSimple w:instr=" SEQ Figure "><w:r><w:t>1</w:t></w:r></w:fldSimple>'
        "<w:sdt><w:sdtPr/><w:sdtContent><w:r><w:t> (Doe, 2020)</w:t></w:r></w:sdtContent></w:sdt>"
        '<w:smartTag w:element="place"><w:r><w:t> Ankara</w:t></w:r></w:smartTag>'
        '<w:ins w:id="1" w:author="k"><w:r><w:t> added</w:t></w:r></w:ins>'
        '<w:del w:id="2" w:author="k"><w:r><w:delText> removed</w:delText></w:r></w:del>'
        "</w:p>"
    )
    assert (
        read_blocks(docx_factory(body))[0].runs[0].text
        == "a 1 (Doe, 2020) Ankara added"
    )


def test_a_hyperlink_inside_a_content_control_keeps_its_target(docx_factory):
    body = (
        '<w:p><w:sdt><w:sdtContent><w:hyperlink r:id="rId9"><w:r><w:t>x</w:t></w:r>'
        "</w:hyperlink></w:sdtContent></w:sdt></w:p>"
    )
    blocks = read_blocks(docx_factory(body, rels={"rId9": "https://x.test/"}))
    assert blocks[0].runs[0].link == "https://x.test/"


def test_a_link_inside_the_document_keeps_its_words_and_records_where_it_points(
    docx_factory,
):
    """`w:anchor` names a bookmark, not a URL. There is no page for it to point
    at until the next phase assigns one, so the words stay and the target is
    recorded for the manifest to report."""
    body = (
        '<w:p><w:r><w:t>see </w:t></w:r><w:hyperlink w:anchor="_Ref12">'
        "<w:r><w:t>Figure 2</w:t></w:r></w:hyperlink></w:p>"
    )
    blocks = read_blocks(docx_factory(body))
    assert [(r.text, r.link, r.anchor) for r in blocks[0].runs] == [
        ("see ", "", ""),
        ("Figure 2", "", "_Ref12"),
    ]


def test_the_style_vocabulary_still_reads_a_paragraph_style_from_the_document(
    docx_factory,
):
    """Style resolution must not disturb what `style`, `heading` and `role`
    already say; a heading is a heading whether or not styles.xml is there."""
    block = read_blocks(
        docx_factory(
            para("One", style="Heading1"),
            media={"word/styles.xml": styles_xml(style("Heading1"))},
        )
    )[0]
    assert (block.style, block.heading) == ("Heading1", 1)
