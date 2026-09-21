"""Turn the intermediate blocks into a Ricos document.

The shapes here are not guessed, because a guess would not announce itself.
Ricos validates nothing on the way in: a node with a misspelled field is stored
happily and then renders as a blank space on the published page, so the only
place a mistake shows up is the live site.

Three sources fix them. The wrapper, PARAGRAPH, TEXT and IMAGE were read off Dr.
Kaynardag's own live Wix site: one of his blog posts was fetched through the
Data API and its richContent field is the template those nodes follow, down to
the empty id a TEXT node carries and the bare media id an image's `src` holds.
The decorations were read off the published ricos-schema typings
(ricos_document.d.ts, v10.102.0): BoldDecoration l.209, ItalicDecoration l.219,
UnderlineDecoration l.229, LinkDecoration l.269 with LinkData l.308 and
Link.url l.73. The containers come from the same file: BlockquoteNode l.340,
OrderedListNode l.416, BulletedListNode l.440, ListItemNode l.457 with
ListItemChildNode l.467.

The third source outranks the typings where they disagree: Wix's own validator,
`POST /ricos/v1/ricos-document/validate`, which is read-only and answers about
the document Wix will actually accept. It rejected a BLOCKQUOTE with two
children although `l.346` declares an array, because a generated array type
cannot express a maximum - see `_callout`. With the plugins these documents use
it passes the whole corpus with no violations, which is what settles three
shapes the typings leave looking wrong: the CAPTION child of an IMAGE (the
typings declare no CAPTION type and give `ImageNode.nodes?: never[]`), the
empty `tableCellData: {}`, and `imageData.caption` beside `altText`.

Bytes are the standing constraint. A CMS item holds 500,000 bytes across all of
its fields and the rich content counts against that, so nothing optional is
emitted and node ids stay as short as uniqueness allows.
"""
import re
from dataclasses import replace

from tools.ricos.blocks import Callout, Figure, Para, Run, Table

HEADING_LEVEL = {"Heading1": 1, "Heading2": 2, "Heading3": 3, "Heading4": 4}

# A list kind, as the reader names it, to its Ricos node type.
LIST_NODE = {"bullet": "BULLETED_LIST", "ordered": "ORDERED_LIST"}

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

    Most blocks reach it through `_nodes`, from the body and from inside a
    table cell alike, so an empty paragraph standing in an empty cell still
    produces its placeholder node; the body's filter is `_drop_from_body`, and
    `emit` applies it before dispatching.

    `_callout` is the exception and calls it directly, past `_nodes`. That is
    deliberate and forced by what Wix's validator accepts, not an oversight:
    `_nodes` folds a run of list paragraphs into a BULLETED_LIST, and a
    BLOCKQUOTE takes one PARAGRAPH and nothing else. See `_callout`.
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


def _has_text(block):
    """True when a paragraph says anything of its own.

    Whitespace does not count. A paragraph holding eight spaces renders as the
    same blank block as an empty one, even though the schema would take it as a
    non-empty string.
    """
    return bool("".join(r.text for r in block.runs).strip())


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
    stray gap and cost about 100 bytes of the item's budget to do it.

    **Body only.** This is called from `emit` and from nowhere else. An empty
    paragraph inside a table cell is a placeholder that keeps the grid
    rectangular, and it has to survive - see `_cell`, which reaches `_para`
    through `_nodes` and drops nothing on the way. An aside has no grid to keep
    square, so `_callout` drops its blank paragraphs; it asks `_has_text`
    directly, because the TOC half of this test has no meaning inside a quote.
    """
    if TOC_STYLE.match(block.style):
        return True
    return not _has_text(block)


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
    picture with no source, which `_node` skips.
    """
    nodes = _nodes(blocks, ids, media_ids)
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


def _joined(paras):
    """The aside's paragraphs as the runs of a single paragraph.

    Word's paragraph boundary is the only thing saying where one ends, so it
    becomes a run of "\\n" and the words on either side keep their gap. Without
    it the ML guide's opening aside reads "How to use this guideRead the
    document step by step..." - glued at every boundary, in the flagship
    document's first box.
    """
    runs = []
    for para in paras:
        if runs:
            runs.append(Run(text="\n"))
        runs.extend(para.runs)
    return runs


def _callout(block, ids, media_ids):
    """A BLOCKQUOTE over the aside's paragraphs, then whatever else it held.

    **A BLOCKQUOTE takes exactly one child**, and that is measured, not read
    off the typings. `POST /ricos/v1/ricos-document/validate` rejects a quote
    with two PARAGRAPH children: `{"path":["nodes","3","nodes"],"message":
    "Expected to have size less than 1, but got 2"}`. The generated
    `ricos_document.d.ts` says `nodes: ParagraphNode[]` (l.346), but a
    generated array type has no way to express a maximum, so it is not
    evidence against one. The shape below is `fixDocument`'s own output: one
    PARAGRAPH, the source paragraphs joined by "\\n" TEXT runs, and
    `paragraphData` carried from the **first** source paragraph. The asides in
    this corpus are justified, thirty-four paragraphs of them, and the first
    paragraph's alignment is the one that speaks for the box.

    One PARAGRAPH decides the three things the quote cannot hold. A heading
    loses its style, because a HEADING node here is stored without complaint
    and renders as nothing; the words are worth more than the weight, and the
    alignment survives either way. A picture cannot be represented at all -
    there is no BlockquoteChildNode union - so it follows the quote as a
    sibling. The aside loses the picture's position inside itself and keeps the
    picture, which is the right way round.

    A list is the third, and it is why the paragraphs below go to `_para`
    directly instead of through `_nodes`: that helper folds a run of list
    paragraphs into a BULLETED_LIST, which is off-type here twice over - wrong
    node type, and a second child. Inside an aside a list item stays part of
    the one paragraph and loses its marker. No aside in this corpus holds one -
    this is the reason written down, so that routing the quote through `_nodes`
    does not look like a tidy-up waiting to happen.

    A paragraph with nothing in it is dropped, before the join so that it
    leaves no separator behind either. It is the same stray gap
    `_drop_from_body` removes from the body, and the reason a cell keeps its
    blanks - a rectangular grid - does not transfer to a box with no grid in
    it. Latent: no aside in this corpus has one.

    An aside holding no paragraphs is just its contents: an empty quote box
    around them would be a stray frame on the page.

    COLLAPSIBLE_LIST was passed over for asides deliberately, and not for want
    of a better box: collapsed content undercuts the raw-HTML indexing this
    whole project depends on.
    """
    said = [b for b in block.blocks if isinstance(b, Para) and _has_text(b)]
    out = []
    if said:
        quote = {"type": "BLOCKQUOTE", "id": ids.next(), "nodes": [],
                 "blockquoteData": {"indentation": 0}}
        # Filled after the dict is made so the quote takes its id before its
        # child takes its own, the way every other container here does.
        quote["nodes"] = [_para(replace(said[0], runs=_joined(said), style=""), ids)]
        out.append(quote)
    out.extend(n for b in block.blocks if not isinstance(b, Para)
               for n in _node(b, ids, media_ids))
    return out


def _node(block, ids, media_ids):
    """The nodes for one block: none, one, or - for an aside - several.

    Reached from the body and from inside a cell alike, so it filters nothing
    that is content. A picture with no filename is not content: the empty
    filename means Word never declared the relationship it pointed at, and the
    node it would make carries `src: {"id": ""}`, which Ricos stores without
    complaint and renders as a hole. A picture that has a filename but no
    measured size is kept - the file exists, and the upload step can repair the
    dimensions. Neither state occurs in the present corpus.

    A list paragraph arrives here as an ordinary paragraph, because whether it
    belongs in a list is a question about its neighbours and this function sees
    one block. `_nodes` answers it; `_callout` deliberately does not ask.

    `_cell` and `_callout` are defined above it and reach it; that is fine,
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


def _list(kind, items, ids):
    """One BULLETED_LIST or ORDERED_LIST over a run of list paragraphs.

    `ListItemNode.nodes` is `ListItemChildNode[]` (l.457, l.467) and that union
    holds no text node, so an item wraps a PARAGRAPH rather than TEXT. Routing
    it through `_para` gets that for free, along with the item's alignment and,
    since HEADING is in the union too, a heading that was also a list item.

    Nesting is not built. The reader records `list_level` and the union does
    admit a list inside an item, but all 107 list paragraphs in this corpus sit
    at level 0, so a nesting rule here would be a guess with nothing to check
    it against. A deeper item joins its list as a sibling and loses its indent.

    No `bulletedListData`/`orderedListData` is emitted. Both are optional
    (l.450, l.426) and the only field either one could carry here is
    `indentation`, declared as a left margin whose "possible values are from
    `1` to `4`" (l.430, l.433, l.453). These lists have no margin of their own,
    and `0` is outside that range - it is `offset`, not `indentation`, that
    documents `0` as "the default nesting level" (l.434, l.454). Ricos
    validates nothing on the way in, so an out-of-range value would be stored
    and then rendered however the viewer felt; leaving the object out asks for
    the default instead, and saves ~35 bytes a list.
    """
    return {"type": LIST_NODE[kind], "id": ids.next(),
            "nodes": [{"type": "LIST_ITEM", "id": ids.next(),
                       "nodes": [_para(item, ids)]} for item in items]}


def _nodes(blocks, ids, media_ids):
    """One flow of blocks, with each run of list paragraphs folded into a list.

    The folding belongs to the flow and not to any block in it, because Word
    has no list node at all: a list is only a stretch of paragraphs naming the
    same numbering definition. So the run is keyed on that definition - its
    `w:numId`, carried on the block - and on the marker kind, and it ends at
    the first block that does not match: a new definition, a new marker, or
    anything that is not a list paragraph.

    **A new definition matters even when the marker does not change.** Two
    lists typed back to back share a bullet and are still two lists; the ML
    guide has exactly that, `numId` 3 ending and `numId` 1 beginning with no
    prose between them. Merged, bullets hide it. An ordered second list would
    carry on 4, 5, 6 where the author restarted at 1.

    A picture breaks a run the same way and for a worse reason: it is not the
    author's doing. `_para_blocks` hoists a picture out of the paragraph it was
    anchored in, because Ricos has no inline image, so a list interrupted by
    one continues as a second list node. This happens once in the corpus, in
    the ML guide, and cannot be seen - every list there is bulleted, and
    bullets do not count. An **ordered** list would restart at `1`. Either
    break, met in an ordered list, is fixed the same two ways: keep the image
    inside its LIST_ITEM (`ListItemChildNode` l.467 admits one), or set
    `orderedListData.start` (l.437) on the continuation.

    The body and a table cell both come through here, so a list in a cell is a
    list. An aside does not and must not; the reason is in `_callout`.

    What differs between the two flows is upstream of here, and stays there:
    `emit` drops a paragraph with no text and `_cell` keeps one, because an
    empty cell needs a placeholder to keep the grid rectangular and the body
    only needs the gap gone. This helper filters nothing either way.
    """
    out = []
    run_key, run_items = None, []

    def flush():
        nonlocal run_key, run_items
        if run_items:
            out.append(_list(run_key[0], run_items, ids))
        run_key, run_items = None, []

    for block in blocks:
        kind = block.list_kind if isinstance(block, Para) else ""
        if kind:
            key = (kind, block.list_id)
            if key != run_key:
                flush()
                run_key = key
            run_items.append(block)
            continue
        flush()
        out.extend(_node(block, ids, media_ids))
    flush()
    return out


def emit(blocks, media_ids=None):
    """Return a complete Ricos document for these blocks.

    `media_ids` maps a filename to the id Wix stored the file under. Phase 1
    has not uploaded anything yet, so without it the filename stands in.

    The body filter is applied here and only here, and before `_nodes` rather
    than inside it. `_drop_from_body` reads `block.style`, which only a Para
    has, so the test for it is asked first and every other kind of block goes
    through untouched. Filtering first also settles a case the folding would
    otherwise get wrong: an empty paragraph typed between two bullets is a
    stray gap, not a boundary, so removing it before the folding leaves the one
    list the page shows instead of two lists restarting.
    """
    ids = Ids()
    kept = [block for block in blocks
            if not (isinstance(block, Para) and _drop_from_body(block))]
    return {"nodes": _nodes(kept, ids, media_ids or {}),
            "metadata": {"version": 1},
            "documentStyle": {}}
