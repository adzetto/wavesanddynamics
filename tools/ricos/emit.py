"""Turn the intermediate blocks into a Ricos document.

The shapes here are not guessed, because a guess would not announce itself.
Ricos validates nothing on the way in: a node with a misspelled field is stored
happily and then renders as a blank space on the published page, so the only
place a mistake shows up is the live site.

Two sources fix them. The wrapper, PARAGRAPH and TEXT were read off Dr.
Kaynardag's own live Wix site: one of his blog posts was fetched through the
Data API and its richContent field is the template those nodes follow, down to
the empty id a TEXT node carries. The decorations were read off the published
ricos-schema typings (ricos_document.d.ts, v10.102.0): BoldDecoration l.209,
ItalicDecoration l.219, UnderlineDecoration l.229, LinkDecoration l.269 with
LinkData l.308 and Link.url l.73.

Bytes are the standing constraint. A CMS item holds 500,000 bytes across all of
its fields and the rich content counts against that, so nothing optional is
emitted and node ids stay as short as uniqueness allows.
"""
import re

from tools.ricos.blocks import Para

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

    Cell emission calls this directly, so that an empty paragraph standing in
    an empty table cell still produces its placeholder node; the body's filter
    is `_drop_from_body`, one level up.
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

    A paragraph with no text is how Word leaves vertical space. In Ricos
    spacing is styling, not content, so an empty block would render as a stray
    gap and cost about 100 bytes of the item's budget to do it.

    **Body only.** An empty paragraph inside a table cell is a placeholder that
    keeps the grid rectangular, and it has to survive - see `_para`, which
    drops nothing and is what cell emission calls.
    """
    if TOC_STYLE.match(block.style):
        return True
    return not any(r.text for r in block.runs)


def emit(blocks):
    """Return a complete Ricos document for these blocks.

    Figures, tables, callouts and lists are not handled yet and pass through
    silently; they arrive in later tasks.
    """
    ids = Ids()
    nodes = []
    for block in blocks:
        if not isinstance(block, Para) or _drop_from_body(block):
            continue
        nodes.append(_para(block, ids))
    return {"nodes": nodes,
            "metadata": {"version": 1},
            "documentStyle": {}}
