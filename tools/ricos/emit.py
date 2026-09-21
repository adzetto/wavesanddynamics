"""Turn the intermediate blocks into a Ricos document.

The shapes here are not guessed, because a guess would not announce itself.
Ricos validates nothing on the way in: a node with a misspelled field is stored
happily and then renders as a blank space on the published page, so the only
place a mistake shows up is the live site.

Two sources fix them. The wrapper, PARAGRAPH, TEXT and IMAGE were read off Dr.
Kaynardag's own live Wix site: one of his blog posts was fetched through the
Data API and its richContent field is the template those nodes follow, down to
the empty id a TEXT node carries and the bare media id an image's `src` holds.
The decorations were read off the published ricos-schema typings
(ricos_document.d.ts, v10.102.0): BoldDecoration l.209, ItalicDecoration l.219,
UnderlineDecoration l.229, LinkDecoration l.269 with LinkData l.308 and
Link.url l.73.

Bytes are the standing constraint. A CMS item holds 500,000 bytes across all of
its fields and the rich content counts against that, so nothing optional is
emitted and node ids stay as short as uniqueness allows.
"""
import re
from dataclasses import replace

from tools.ricos.blocks import Callout, Figure, Para, Table

HEADING_LEVEL = {"Heading1": 1, "Heading2": 2, "Heading3": 3, "Heading4": 4}

# Word's own styles for the lines of a contents list, TOC1 down to TOC9.
TOC_STYLE = re.compile(r"TOC[1-9]$")


class Ids:
    """Node ids must be unique, start with a letter, and stay short.

    Short matters: every wasted byte comes out of the 500 KB an item may hold.
    """

    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return f"n{self.n}"


def _decorations(run):
    decs = []
    if run.bold:
        decs.append({"type": "BOLD", "fontWeightValue": 700})
    if run.italic:
        decs.append({"type": "ITALIC", "italicData": True})
    if run.underline:
        decs.append({"type": "UNDERLINE", "underlineData": True})
    if run.link:
        decs.append({"type": "LINK", "linkData": {"link": {"url": run.link}}})
    return decs


def _text_nodes(runs):
    """TEXT nodes carry an empty id; that is what the live document does.

    A run with no text is dropped rather than emitted empty: the schema says a
    TEXT node must hold a non-empty string, so an empty paragraph is a node
    with no children at all.
    """
    return [
        {"type": "TEXT", "id": "", "nodes": [],
         "textData": {"text": r.text, "decorations": _decorations(r)}}
        for r in runs if r.text
    ]


def _para(block, ids):
    """One paragraph or heading node. Nothing is filtered here.

    Everything reaches it through `_nodes`, from the body and from inside a
    table cell alike, so an empty paragraph standing in an empty cell still
    produces its placeholder node; the body's filter is `_drop_from_body`, and
    `emit` applies it before dispatching.
    """
    level = HEADING_LEVEL.get(block.style)
    if level:
        return {"type": "HEADING", "id": ids.next(),
                "nodes": _text_nodes(block.runs),
                "headingData": {"level": level,
                                "textStyle": {"textAlignment": block.align}}}
    return {"type": "PARAGRAPH", "id": ids.next(),
            "nodes": _text_nodes(block.runs),
            "paragraphData": {"textStyle": {"textAlignment": block.align},
                              "indentation": 0}}


def _drop_from_body(block):
    r"""Whether a body paragraph is an artefact rather than content.

    This decision lives in the emitter and not in the reader on purpose. The
    reader's job is to extract the document faithfully, whatever is in it;
    deciding what earns a place on the page is this side's call.

    Two kinds never reach the page:

    A paragraph styled TOC1-TOC9 is a contents list the author typed by hand.
    Word's generated one is an SDT and is already dropped upstream, and this is
    the same artefact by another route: the site builds its navigation from the
    headings, so a second list is redundant, and the typed one arrives broken
    anyway - "1. What is Machine Learning?\t2", the heading fused to a page
    number that means nothing on a web page.

    A paragraph with no text of its own is how Word leaves vertical space. In
    Ricos spacing is styling, not content, so an empty block would render as a
    stray gap and cost about 100 bytes of the item's budget to do it. Nothing
    but whitespace counts as no text: a paragraph holding eight spaces is the
    same artefact typed a different way and renders as the same blank block,
    even though the schema would accept it as a non-empty string.

    **Body only.** This is called from `emit`'s own loop and from nowhere else.
    An empty paragraph inside a table cell is a placeholder that keeps the grid
    rectangular, and it has to survive - see `_cell`, which reaches `_para`
    through `_nodes` and drops nothing on the way.
    """
    if TOC_STYLE.match(block.style):
        return True
    return not "".join(r.text for r in block.runs).strip()


def _image(block, ids, media_ids):
    """One IMAGE node, with its caption as a child.

    `src` holds the bare media id and nothing else. The `wix:image://v1/...`
    string is the form a CMS *field* takes; put it in a node and the node is
    stored without complaint and renders as a hole. Width and height are not
    optional either: the renderer reserves the space from them.
    """
    file_id = media_ids.get(block.filename, block.filename)
    node = {
        "type": "IMAGE", "id": ids.next(), "nodes": [],
        "imageData": {
            "containerData": {"width": {"size": "CONTENT"},
                              "alignment": "CENTER", "textWrap": True},
            "image": {"src": {"id": file_id},
                      "width": block.width, "height": block.height},
        },
    }
    if block.caption:
        # Both forms on purpose: imageData.caption is deprecated but the
        # official examples still emit it alongside the CAPTION child.
        node["nodes"] = [{"type": "CAPTION", "id": ids.next(), "captionData": {},
                          "nodes": [{"type": "TEXT", "id": "", "nodes": [],
                                     "textData": {"text": block.caption,
                                                  "decorations": []}}]}]
        node["imageData"]["altText"] = block.caption
        node["imageData"]["caption"] = block.caption
    return node


def _cell(blocks, ids, media_ids):
    """One TABLE_CELL. A cell holds blocks, never text of its own.

    Nothing is filtered here. A cell whose only paragraph is empty still emits
    that paragraph, because dropping it would cost the row a cell and leave the
    table ragged. The placeholder also catches a cell whose only content was a
    picture with no source, which `_nodes` skips.
    """
    nodes = [n for b in blocks for n in _nodes(b, ids, media_ids)]
    if not nodes:
        nodes = [{"type": "PARAGRAPH", "id": ids.next(), "nodes": [],
                  "paragraphData": {"textStyle": {"textAlignment": "AUTO"},
                                    "indentation": 0}}]
    return {"type": "TABLE_CELL", "id": ids.next(), "nodes": nodes,
            "tableCellData": {}}


def _table(block, ids, media_ids):
    """TABLE -> TABLE_ROW -> TABLE_CELL -> blocks, strictly in that order."""
    rows = [{"type": "TABLE_ROW", "id": ids.next(),
             "nodes": [_cell(cell, ids, media_ids) for cell in row]}
            for row in block.rows]
    return {"type": "TABLE", "id": ids.next(), "nodes": rows,
            "tableData": {"rowHeader": block.header_row}}


def _callout(block, ids, media_ids):
    """A BLOCKQUOTE holding the aside's paragraphs, then whatever else it held.

    `BlockquoteNode.nodes` is declared `ParagraphNode[]` in the published
    ricos-schema typings (ricos_document.d.ts, v10.102.0, l.346), so the quote
    takes as many paragraphs as the aside had and each keeps its own
    properties. Folding them into one would need a separator between them and
    would flatten every paragraph's alignment to the default - the asides in
    this corpus are justified, thirty-four paragraphs of them.

    `ParagraphNode[]` is exact, and that decides the two things the quote
    cannot hold. A heading loses its style and stays a paragraph, because a
    HEADING node in that array is stored without complaint and renders as
    nothing; the words are worth more than the weight, and the alignment
    survives either way. A picture cannot be represented at all - the typings
    declare no BlockquoteChildNode union - so it follows the quote as a
    sibling. The aside loses the picture's position inside itself and keeps the
    picture, which is the right way round.

    An aside holding no paragraphs is just its contents: an empty quote box
    around them would be a stray frame on the page.

    COLLAPSIBLE_LIST was passed over for asides deliberately, and not for want
    of a better box: collapsed content undercuts the raw-HTML indexing this
    whole project depends on.
    """
    paras = [_para(replace(b, style=""), ids)
             for b in block.blocks if isinstance(b, Para)]
    out = []
    if paras:
        out.append({"type": "BLOCKQUOTE", "id": ids.next(), "nodes": paras,
                    "blockquoteData": {"indentation": 0}})
    out.extend(n for b in block.blocks if not isinstance(b, Para)
               for n in _nodes(b, ids, media_ids))
    return out


def _nodes(block, ids, media_ids):
    """The nodes for one block: none, one, or - for an aside - several.

    Reached from the body and from inside a cell alike, so it filters nothing
    that is content. A picture with no filename is not content: the empty
    filename means Word never declared the relationship it pointed at, and the
    node it would make carries `src: {"id": ""}`, which Ricos stores without
    complaint and renders as a hole. A picture that has a filename but no
    measured size is kept - the file exists, and the upload step can repair the
    dimensions. Neither state occurs in the present corpus.

    `_cell` and `_callout` are defined above it and call it; that is fine,
    because the name is resolved when the call runs, not when it is compiled.
    """
    if isinstance(block, Para):
        return [_para(block, ids)]
    if isinstance(block, Figure):
        return [_image(block, ids, media_ids)] if block.filename else []
    if isinstance(block, Table):
        return [_table(block, ids, media_ids)]
    if isinstance(block, Callout):
        return _callout(block, ids, media_ids)
    return []


def emit(blocks, media_ids=None):
    """Return a complete Ricos document for these blocks.

    `media_ids` maps a filename to the id Wix stored the file under. Phase 1
    has not uploaded anything yet, so without it the filename stands in.

    The body filter is applied here and only here. `_drop_from_body` reads
    `block.style`, which only a Para has, so the test for it is asked first and
    every other kind of block goes straight to `_nodes`.

    Lists are not handled yet and pass through silently; they arrive later.
    """
    media_ids = media_ids or {}
    ids = Ids()
    nodes = []
    for block in blocks:
        if isinstance(block, Para) and _drop_from_body(block):
            continue
        nodes.extend(_nodes(block, ids, media_ids))
    return {"nodes": nodes,
            "metadata": {"version": 1},
            "documentStyle": {}}
