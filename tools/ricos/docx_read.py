"""Read a .docx into the intermediate blocks.

We parse the XML rather than going through pandoc because everything that decides
the page is what a generic converter flattens. A heading arriving as an ordinary
paragraph costs the page its outline. Bold, italic and a link are decorations in
Ricos, so a mark dropped here can never be recovered downstream. A picture and
the line beneath it are one figure to a reader and two paragraphs in the file,
and nothing but their order says so. Even a tab is an empty element:
invisible until it is gone and the words on either side have fused.

Tables are the same argument one level down. Word gave the author no aside, so
the boxes he highlights with are tables of a single cell, and nothing but their
shape says they are not data. A cell is otherwise a document in miniature, with
its own paragraphs, pictures and captions, so the rules the body has must reach
inside one.

A run is the same argument one level further down. What it looks like is not
what its own `w:rPr` says but what that says on top of the character style, the
paragraph style, the styles those are based on and the document's defaults.
The Title paragraphs of two documents are bold through their style and nothing
else, and every hyperlink is blue and underlined through Word's `Hyperlink`
style: read off the run alone, the first arrived plain and the second would
have arrived decorated twice.
"""

import copy
import io
import os
import re
import zipfile
from collections import Counter
from dataclasses import replace

from lxml import etree
from PIL import Image

from tools.ricos.blocks import Callout, Figure, Para, Rule, Run, Table, walk
from tools.ricos.glyphs import symbol
from tools.ricos.omml import linear

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
DRAW = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}"

# Word measures a drawing in EMU (914400 an inch) and a page in twips (1440 an
# inch); the page measures in CSS pixels, 96 an inch.
EMU_PER_PX = 9525
TWIPS_PER_PX = 15

# A picture set in a line of text (`wp:inline`) and no taller than two lines
# of 11-point text belongs to the sentence it sits in: an equation or a symbol
# drawn as a picture. The corpus has one, used twice, at 15 and 13 px; the
# next smallest inline picture is a 175 px book cover.
IN_LINE_EMU = 2 * 11 * 12700

ALIGN = {"both": "JUSTIFY", "center": "CENTER", "right": "RIGHT", "left": "LEFT"}
MATH_ALIGN = {
    "left": "LEFT",
    "right": "RIGHT",
    "center": "CENTER",
    "centerGroup": "CENTER",
}

REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Word switches a mark off with a value, not by leaving the element out: a run
# that escapes a bold style carries <w:b w:val="0"/>, and an underline is
# cancelled with <w:u w:val="none"/>. Presence alone would read those as on.
MARK_OFF = {"0", "false", "off", "none"}

# The properties ECMA-376 §17.7.3 calls toggles. Set in both the paragraph
# style and the character style they cancel, which is how a "Strong" run in a
# bold paragraph comes out plain in Word. Everything else simply overrides.
TOGGLES = {"b", "i", "caps", "smallCaps", "strike", "vanish"}

VERTICAL = {"superscript": "super", "subscript": "sub"}

# Word's sixteen highlighter colours, by the names it writes.
HIGHLIGHT = {
    "yellow": "#ffff00",
    "green": "#00ff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "blue": "#0000ff",
    "red": "#ff0000",
    "darkBlue": "#000080",
    "darkCyan": "#008080",
    "darkGreen": "#008000",
    "darkMagenta": "#800080",
    "darkRed": "#800000",
    "darkYellow": "#808000",
    "darkGray": "#808080",
    "lightGray": "#c0c0c0",
    "black": "#000000",
    "white": "#ffffff",
}

# A tab and a line break are empty elements standing between the text pieces of
# a run. A run holding nothing else reads as empty, is dropped, and then the
# merge below fuses its two neighbours: that is how the hand-typed contents list
# in the ML guide came out as "What is Machine Learning?2". A carriage return is
# a break by another name; a non-breaking hyphen is the character it stands
# for; a soft hyphen shows only where a line happens to break, so it is nothing.
CHARS = {
    W + "tab": "\t",
    W + "br": "\n",
    W + "cr": "\n",
    W + "noBreakHyphen": "‑",
    W + "softHyphen": "",
}

# The elements that hold runs one level below the paragraph and mean nothing
# else: a simple field (its result is its runs), a content control, a smart
# tag, custom XML, a tracked insertion or move. A tracked deletion is not among
# them - its runs are the text the author removed - and neither is anything
# not listed, so a container this does not know keeps its words out of the
# page rather than putting a stranger's in.
INLINE = {
    W + "fldSimple",
    W + "sdtContent",
    W + "ins",
    W + "smartTag",
    W + "customXml",
    W + "dir",
    W + "bdo",
    W + "moveTo",
}

# Word leaves a caption as an ordinary paragraph under the picture, and in these
# documents some are italic and some are not, so the only thing that marks one is
# that it opens the way the author numbers his figures. The price of a rule that
# loose is that a sentence beginning "Figure 13 puts the coverage difference ..."
# reads as a caption too. Three of those follow a picture in the corpus, and all
# three sit second, behind the real caption, where folding the first one is what
# brings them within reach. That is the guard in read_blocks, not a spare check:
# without it those three captions are overwritten and the sentences leave the
# flow. The alternative, requiring italics, cost four real captions.
CAPTION_RE = re.compile(r"^\s*(figure|table)\s+\d+", re.I)

# Word's style vocabulary, and the only place that reads it. A style id is
# matched against these with its spaces removed and in lower case, so
# "Heading 1", "heading1" and "HEADING1" are one style - Word writes the first
# of those, an export out of Pages or Docs writes another, and a style id that
# is close but not exact is how a document loses every heading it has without
# anything saying so.
#
# Word offers nine levels and Ricos draws six, as HTML does. The three past
# the sixth keep their outline at the deepest level there is rather than
# falling out of it as plain paragraphs: a level too deep is still a heading.
HEADING_RE = re.compile(r"heading([1-9])$")
DEEPEST_HEADING = 6

# TOC1 down to TOC9 are the lines of a contents list. TOCHeading is the word
# "Contents" above it and is deliberately not one of them.
TOC_RE = re.compile(r"toc[1-9]$")

ROLE = {"title": "TITLE", "caption": "CAPTION"}

# The character styles Word puts on a link by itself - blue and underlined -
# which say that the run is a link and nothing about the author's marks.
# Matched on the style's name, which stays "Hyperlink" in every language
# Word ships in, where the id does not.
LINK_STYLES = {"hyperlink", "followedhyperlink"}


def _open(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return zipfile.ZipFile(io.BytesIO(path_or_bytes))
    return zipfile.ZipFile(path_or_bytes)


def _read_rels(z, part="document"):
    """rId -> target, for hyperlinks and images, of one part of the package."""
    try:
        root = etree.fromstring(z.read(f"word/_rels/{part}.xml.rels"))
    except KeyError:
        return {}
    return {
        r.get("Id"): r.get("Target") for r in root.findall(RELS_NS + "Relationship")
    }


def _numbering_kinds(z):
    """numId -> "bullet" | "ordered", read from word/numbering.xml.

    A paragraph's `w:numPr` names a numbering definition; nothing there says
    what the marker looks like. Only `w:numFmt` in this part does, two
    indirections away: the paragraph names a `w:num`, the `w:num` names a
    `w:abstractNum`, and that holds one `w:lvl` per depth.

    Level 0's format stands for the whole definition. Word allows a different
    one at every depth, but the writer has no nesting to hang the difference
    on, so reading per level could only split a list Word drew as one - and all
    107 list paragraphs in this corpus sit at level 0.

    Level 0 is the one whose `w:ilvl` says so, not the one written first. All
    15 abstract definitions here write it first, which makes reading the first
    one right on this corpus and wrong in general: nothing in the format fixes
    the order, and a definition written the other way round would give the
    whole list the marker of whatever depth happened to come first. `w:ilvl` is
    required on a `w:lvl`, so one without it is malformed; it is read as level
    0 rather than skipped, because losing a definition's format over an
    attribute Word always writes would cost more than it saves.

    `bullet` is the only Word format that is not a counter, so a format we can
    read and that is not `bullet` reads as ordered. Everything else reads as a
    bullet, and the two ways of knowing nothing agree: a `w:lvl` that declares
    no `w:numFmt`, and a `w:num` pointing at an abstract definition the part
    never declares. A wrongly bulleted list is the smaller defect - a wrongly
    numbered one invents an order the author never wrote. Neither fallback
    fires on this corpus.
    """
    try:
        root = etree.fromstring(z.read("word/numbering.xml"))
    except KeyError:
        return {}
    abstract = {}
    for a in root.findall(W + "abstractNum"):
        lvl = next(
            (x for x in a.findall(W + "lvl") if (x.get(W + "ilvl") or "0") == "0"), None
        )
        fmt = None if lvl is None else lvl.find(W + "numFmt")
        val = None if fmt is None else fmt.get(W + "val")
        abstract[a.get(W + "abstractNumId")] = (
            "ordered" if val and val != "bullet" else "bullet"
        )
    out = {}
    for n in root.findall(W + "num"):
        ref = n.find(W + "abstractNumId")
        if ref is not None:
            out[n.get(W + "numId")] = abstract.get(ref.get(W + "val"), "bullet")
    return out


def _read_styles(z):
    """styleId -> (basedOn, rPr, pPr, name) from word/styles.xml, and the docDefaults rPr.

    A style says only what differs from the one it is based on, so a mark is
    found by walking `basedOn` until something sets it - see `_chain`. The
    document defaults are the floor under every chain: two documents in the
    corpus set their text colour there and nowhere else.
    """
    try:
        root = etree.fromstring(z.read("word/styles.xml"))
    except KeyError:
        return {}, None
    styles = {}
    for s in root.findall(W + "style"):
        based = s.find(W + "basedOn")
        name = s.find(W + "name")
        styles[s.get(W + "styleId")] = (
            based.get(W + "val") if based is not None else None,
            s.find(W + "rPr"),
            s.find(W + "pPr"),
            (name.get(W + "val") if name is not None else s.get(W + "styleId")) or "",
        )
    return styles, root.find(W + "docDefaults/" + W + "rPrDefault/" + W + "rPr")


def _read_notes(z, kind):
    """id -> the `w:footnote` or `w:endnote` element, separators left out.

    Word puts two notes of its own in every notes part, the separator lines,
    typed `separator` and `continuationSeparator`; only an untyped or `normal`
    note is one the author wrote.
    """
    try:
        root = etree.fromstring(z.read(f"word/{kind}s.xml"))
    except KeyError:
        return {}
    return {
        n.get(W + "id"): n
        for n in root.findall(W + kind)
        if n.get(W + "type") in (None, "normal")
    }


class _Doc:
    """The side parts a paragraph cannot be read without, read once per document.

    Relationships for its links and pictures, numbering for its list marker,
    styles for its marks, and the notes its references point at - all of
    them travel every path of the walk, because `_para_blocks` is reached
    from the body and from inside a cell alike, and a part that fails to
    travel one path makes that path read wrong silently: the fields it
    would have filled already have harmless defaults.

    The note references are numbered here as well, because the number is
    the order in which the document reaches them and only the walk knows it.
    """

    def __init__(self, z, part="document"):
        self.z = z
        self.rels = _read_rels(z, part)
        self.kinds = _numbering_kinds(z)
        self.styles, self.defaults = _read_styles(z)
        self.notes = {kind: _read_notes(z, kind) for kind in ("footnote", "endnote")}
        self.cited = []

    def part(self, name):
        """This document seen from another package part: the relationships
        differ, the styles, numbering and note numbering are shared."""
        other = copy.copy(self)
        other.rels = _read_rels(self.z, name)
        return other

    def mark(self, kind, note_id):
        """The mark for a note reference: "[n]" in reading order, or "" for a
        reference to a note the part does not hold."""
        if note_id not in self.notes[kind]:
            return ""
        key = (kind, note_id)
        if key not in self.cited:
            self.cited.append(key)
        return f"[{self.cited.index(key) + 1}]"


# --- runs ----------------------------------------------------------------------


def _on(el):
    """True when a mark element is present and not switched off."""
    return el is not None and (el.get(W + "val") or "").lower() not in MARK_OFF


def _direct(rpr, name):
    return rpr.find(W + name) if rpr is not None else None


def _chain(styles, sid):
    """A style and the ones it is based on, nearest first; a cycle ends it."""
    out = []
    while sid in styles and sid not in out:
        out.append(sid)
        sid = styles[sid][0]
    return out


def _from_styles(styles, sid, name):
    """The nearest style in the chain from `sid` that sets `name`, as its element."""
    for s in _chain(styles, sid):
        el = _direct(styles[s][1], name)
        if el is not None:
            return el
    return None


def _setting(name, rpr, pstyle, rstyle, doc):
    """The element that decides run property `name`, or None when nothing does.

    The order is Word's: direct formatting, then the character style, then
    the paragraph style, then the document defaults, each chain walked to
    its root. The first one to say anything wins, and what it says may be
    "off": `<w:u w:val="none"/>` in a character style cancels the underline
    the paragraph style gave.
    """
    for el in (
        _direct(rpr, name),
        _from_styles(doc.styles, rstyle, name),
        _from_styles(doc.styles, pstyle, name),
        _direct(doc.defaults, name),
    ):
        if el is not None:
            return el
    return None


def _toggle(name, rpr, pstyle, rstyle, doc):
    """A toggle property, resolved the way ECMA-376 §17.7.3 says Word does.

    Direct formatting is absolute. Below it the two style chains do not
    stack: set in both the paragraph style and the character style, the
    mark is off, which is the rule that keeps a "Strong" run inside a bold
    paragraph from being bold twice - or, as Word draws it, at all. Set in
    one, that one decides; set in neither, the defaults do.
    """
    direct = _direct(rpr, name)
    if direct is not None:
        return _on(direct)
    from_r = _from_styles(doc.styles, rstyle, name)
    from_p = _from_styles(doc.styles, pstyle, name)
    if from_r is not None and from_p is not None:
        return _on(from_r) != _on(from_p)
    el = from_r if from_r is not None else from_p
    return _on(el if el is not None else _direct(doc.defaults, name))


def _hex(val):
    """A Word colour as "#rrggbb", or "" for black, `auto` and anything unreadable.

    Black and `auto` are the page's own colour: a run that says so is saying
    nothing the page does not already do.
    """
    val = (val or "").lower()
    if (
        len(val) != 6
        or val == "000000"
        or not all(c in "0123456789abcdef" for c in val)
    ):
        return ""
    return "#" + val


def _background(highlight, shd):
    """The colour behind the text: the highlighter first, character shading after."""
    if highlight is not None:
        return HIGHLIGHT.get(highlight.get(W + "val") or "", "")
    if shd is not None:
        fill = shd.get(W + "fill") or ""
        return _hex(fill) if fill.lower() != "auto" else ""
    return ""


def _text(r, doc):
    """Run text, from the run's own children and nothing deeper.

    Tabs and breaks are kept as the whitespace they stand for, a symbol as
    the glyph it names, an emoji as itself, a note reference as its number.
    The children are the run's direct ones on purpose: a drawing anchored in
    a run can hold paragraphs of its own, and a walk over every `w:t` beneath
    the run would glue them into the sentence the drawing sat in - twice,
    since Word writes a drawing's text box again under `mc:Fallback`. A text
    box's words are content and are read by `_text_boxes`, once, as
    paragraphs of their own.
    """
    out = []
    for el in r:
        if el.tag == W + "t":
            out.append(el.text or "")
        elif el.tag in CHARS:
            out.append(CHARS[el.tag])
        elif el.tag == W + "sym":
            out.append(symbol(el.get(W + "font"), el.get(W + "char")))
        elif el.tag == MC + "AlternateContent":
            # Word 2016 writes an emoji as a symbol extension whose fallback
            # is the glyph itself, a `w:t` directly under `mc:Fallback`. A
            # drawing's fallback holds no `w:t` of its own, only a shape.
            fallback = el.find(MC + "Fallback")
            if fallback is not None:
                out.append("".join(t.text or "" for t in fallback.findall(W + "t")))
        elif el.tag == W + "footnoteReference":
            out.append(doc.mark("footnote", el.get(W + "id")))
        elif el.tag == W + "endnoteReference":
            out.append(doc.mark("endnote", el.get(W + "id")))
    return "".join(out)


def _run(r, link, anchor, pstyle, doc):
    """One Run, or None when the run is hidden.

    Hidden is `w:vanish`, text Word itself does not show, and `w:webHidden`,
    text it does not show on a web page - the page numbers of every contents
    list in the corpus, 52 runs. Neither is anything the author published.

    `w:caps` shows lower-case letters as capitals while the letters stored
    stay lower case, so the text is raised here; the page would otherwise
    show what Word hides. Small capitals have no plain-text form and the text
    is left as typed.
    """
    rpr = r.find(W + "rPr")
    rstyle = _direct(rpr, "rStyle")
    rstyle = rstyle.get(W + "val") if rstyle is not None else None
    if rstyle in doc.styles and doc.styles[rstyle][3].lower() in LINK_STYLES:
        # Word's own link styling, not the author's: every hyperlink in the
        # corpus is underlined and blue through it, and a link on the page
        # is styled by the site.
        rstyle = None
    args = (rpr, pstyle, rstyle, doc)
    if _toggle("vanish", *args) or _on(_setting("webHidden", *args)):
        return None
    text = _text(r, doc)
    if _toggle("caps", *args):
        text = text.upper()
    color = _setting("color", *args)
    if color is None or color is _direct(doc.defaults, "color"):
        # The default colour is the document's own black, whatever its value.
        color_hex = ""
    else:
        color_hex = _hex(color.get(W + "val"))
    vertical = _setting("vertAlign", *args)
    if (
        r.find(W + "footnoteReference") is not None
        or r.find(W + "endnoteReference") is not None
    ):
        # The mark is "[n]", plain: Word raises its own mark through the
        # FootnoteReference style, and a raised bracket is not a mark.
        vertical = None
    return Run(
        text=text,
        bold=_toggle("b", *args),
        italic=_toggle("i", *args),
        underline=_on(_setting("u", *args)),
        link=link,
        anchor=anchor,
        color=color_hex,
        highlight=_background(_setting("highlight", *args), _setting("shd", *args)),
        vertical=VERTICAL.get(
            vertical.get(W + "val") if vertical is not None else "", ""
        ),
        strike=_toggle("strike", *args) or _on(_setting("dstrike", *args)),
    )


def _inline(el, doc, link="", anchor=""):
    """Every run and equation under `el` in order, with the link it sits in.

    A hyperlink carries a URL through `r:id` or a bookmark name through
    `w:anchor`, and its runs are one level down; so are the runs of the
    containers in INLINE, which mean nothing else. A content control keeps
    its runs under `w:sdtContent`, beside properties that hold none.
    """
    for child in el:
        if child.tag == W + "r" or child.tag in (M + "oMath", M + "oMathPara"):
            yield child, link, anchor
        elif child.tag == W + "hyperlink":
            yield from _inline(
                child,
                doc,
                doc.rels.get(child.get(REL + "id"), ""),
                child.get(W + "anchor") or "",
            )
        elif child.tag == W + "sdt":
            content = child.find(W + "sdtContent")
            if content is not None:
                yield from _inline(content, doc, link, anchor)
        elif child.tag in INLINE:
            yield from _inline(child, doc, link, anchor)


def _merge(runs):
    """Adjacent runs that agree on every mark become one; an empty run is dropped."""
    out = []
    for run in runs:
        if not run.text:
            continue
        if out and replace(out[-1], text="") == replace(run, text=""):
            out[-1].text += run.text
        else:
            out.append(run)
    return out


def _runs(p, pstyle, doc):
    """The paragraph's runs, merged where marks match.

    An equation - `m:oMath`, or the display form `m:oMathPara` - is a child
    of the paragraph beside the runs and reads as a run of its linear text;
    see `omml`. It used to be a child nothing looked at, so the equation left
    the sentence with no trace.
    """
    return _segments(p, pstyle, doc)[0]


def _segments(p, pstyle, doc, cuts=()):
    """The paragraph's runs, cut after each run in `cuts`: one merged list of
    runs per stretch of text, so len(cuts) + 1 of them. With no cuts this is
    `_runs`. A cut is the run that holds a picture set in the sentence, and the
    picture goes between the two stretches it separates."""
    out, cur = [], []
    for el, link, anchor in _inline(p, doc):
        if el.tag == W + "r":
            run = _run(el, link, anchor, pstyle, doc)
            if run is not None:
                cur.append(run)
            if any(el is c for c in cuts):
                out.append(_merge(cur))
                cur = []
        else:
            cur.append(Run(text=linear(el), link=link, anchor=anchor))
    out.append(_merge(cur))
    return out


# --- paragraphs ------------------------------------------------------------------


def _style_numpr(style, doc):
    """The `w:numPr` the paragraph style chain carries, or None."""
    for s in _chain(doc.styles, style):
        ppr = doc.styles[s][2]
        numpr = ppr.find(W + "numPr") if ppr is not None else None
        if numpr is not None:
            return numpr
    return None


def _list_of(ppr, style, doc):
    """The list this paragraph is in, as (kind, numId, level); ("", "", 0) for none.

    The `numId` travels with the paragraph because Word's own boundary between
    two lists is nothing but a change of it. Two lists typed back to back share
    a marker and are still two lists, and the ML guide has exactly that.

    Membership is `w:numPr` and never the style name. Word styles the indented
    continuation of an item `ListParagraph` as well, and twelve paragraphs in
    this corpus are exactly that - prose carrying no `w:numPr`, which a
    style-based test would turn into bullets. A style may carry the `w:numPr`
    itself, though - Word's own "List Bullet" styles do - and then the
    paragraph is a member through it, with its own `w:numPr` free to name
    only the depth. A `w:numPr` that names no definition anywhere names no
    list: read as an empty id it grouped unrelated paragraphs into one.

    A depth that will not read falls back to the top level, the way `_span`
    falls back to one column. An unreadable `w:ilvl` costs one paragraph its
    indent; raising would cost the whole document its read, and the paragraph
    is an item of a list either way.

    `w:numId w:val="0"` is not a numbering definition and never points at one.
    It is how the format says numbering has been *removed* here (ECMA-376
    §17.9.18), which is what Word writes when the author takes one paragraph
    out of a list, and reading it as membership turns exactly that paragraph
    into a bullet. No paragraph in this corpus carries it; the first edit that
    de-lists a line does.
    """
    numpr = ppr.find(W + "numPr") if ppr is not None else None
    num_id = numpr.find(W + "numId") if numpr is not None else None
    ilvl = numpr.find(W + "ilvl") if numpr is not None else None
    if num_id is None:
        styled = _style_numpr(style, doc)
        if styled is not None:
            num_id = styled.find(W + "numId")
            if ilvl is None:
                ilvl = styled.find(W + "ilvl")
    if num_id is None:
        return "", "", 0
    num = num_id.get(W + "val") or ""
    if num == "0":
        return "", "", 0
    level = 0
    if ilvl is not None:
        try:
            level = max(0, int(ilvl.get(W + "val") or 0))
        except ValueError:
            pass
    return doc.kinds.get(num, "bullet"), num, level


def _style_means(style):
    """A Word style id as (heading level, role): what the rest of the code asks.

    The one place the style vocabulary is decoded. It used to be four - a dict
    in the writer, a regex beside it, an f-string in the splitter and an
    equality test in the CLI - which is three chances for them to disagree and
    four to be stricter than Word is. `Heading 1`, with the space Word's own UI
    shows, read as a heading in none of them.

    A style this does not recognise is neither a heading nor a role, and the
    paragraph keeps its raw `style` for whoever comes to name it later.
    """
    key = re.sub(r"\s+", "", style).lower()
    level = HEADING_RE.match(key)
    if level:
        return min(int(level.group(1)), DEEPEST_HEADING), ""
    if TOC_RE.match(key):
        return 0, "TOC"
    return 0, ROLE.get(key, "")


def _edge(pbdr, side):
    """True when the paragraph is bordered on `side`. `nil` is Word's "no border"."""
    el = pbdr.find(W + side)
    return el is not None and (el.get(W + "val") or "single") not in ("nil", "none")


def _para(p, doc):
    ppr = p.find(W + "pPr")
    style = ""
    align = "AUTO"
    left = top = bottom = False
    if ppr is not None:
        s = ppr.find(W + "pStyle")
        if s is not None:
            style = s.get(W + "val") or ""
        j = ppr.find(W + "jc")
        if j is not None:
            align = ALIGN.get(j.get(W + "val") or "", "AUTO")
        pbdr = ppr.find(W + "pBdr")
        if pbdr is not None:
            left, top, bottom = (
                _edge(pbdr, side) for side in ("left", "top", "bottom")
            )
    display = p.find(M + "oMathPara")
    if display is not None and (ppr is None or ppr.find(W + "jc") is None):
        # Word centres a display equation unless its own m:jc says otherwise.
        jc = display.find(M + "oMathParaPr/" + M + "jc")
        align = MATH_ALIGN.get(jc.get(M + "val") if jc is not None else "", "CENTER")
    heading, role = _style_means(style)
    kind, num, level = _list_of(ppr, style, doc)
    # A bar down the left is the box he asides with, whatever else frames it.
    return Para(
        runs=_runs(p, style, doc),
        style=style,
        heading=heading,
        role=role,
        align=align,
        list_kind=kind,
        list_id=num,
        list_level=level,
        aside=left,
        rule_above=top and not left,
        rule_below=bottom and not left,
    )


def _own(el, p, tag):
    """True when no `tag` element stands between `el` and its paragraph `p`.

    A picture or a text box inside a text box belongs to the paragraph inside
    the box, not to the one the box is anchored in; the outer paragraph's
    `iter` reaches both and has to tell them apart.
    """
    for ancestor in el.iterancestors():
        if ancestor is p:
            return True
        if ancestor.tag == tag:
            return False
    return True


def _pictures(p):
    """Every picture anchored in this paragraph itself, in document order.

    Each as its `a:blip` and the drawing that places it - `wp:inline` in the
    line of text or `wp:anchor` floating beside it - which is where Word keeps
    the size it draws the picture at. A picture inside a text box belongs to
    the paragraph inside the box and is skipped here.
    """
    out = []
    for blip in p.iter(DRAW + "blip"):
        if not blip.get(REL + "embed") or not _own(blip, p, W + "txbxContent"):
            continue
        host = next(
            (
                a
                for a in blip.iterancestors()
                if a.tag in (WP + "inline", WP + "anchor")
            ),
            None,
        )
        out.append((blip, host))
    return out


def _extent(host):
    """(width, height) Word draws the picture at, in EMU; (0, 0) when unsaid."""
    ext = host.find(WP + "extent") if host is not None else None
    try:
        return int(ext.get("cx")), int(ext.get("cy"))
    except (AttributeError, TypeError, ValueError):
        return 0, 0


def _crop(blip):
    """The fractions of the stored picture Word hides, (left, top, right, bottom).

    `a:srcRect` insets are thousandths of a percent. A negative one is not a
    crop but padding - the picture shrunk inside its frame - and the page has
    its own space around a figure, so it is read as 0. A crop that leaves
    nothing to show is a mistake in the file and is ignored whole.
    """
    rect = blip.getparent().find(DRAW + "srcRect")
    if rect is None:
        return ()
    sides = []
    for side in "ltrb":
        try:
            sides.append(max(0, int(rect.get(side) or 0)) / 100000)
        except ValueError:
            sides.append(0.0)
    left, top, right, bottom = sides
    if not any(sides) or left + right >= 1 or top + bottom >= 1:
        return ()
    return tuple(sides)


def crop_box(width, height, crop):
    """The pixels of a `width` x `height` picture that `crop` leaves, as a
    Pillow box (left, top, right, bottom). The reader measures a cropped
    picture with this and the CLI cuts the file with it, so the size in the
    part and the size of the file cannot disagree by a rounding."""
    if not crop:
        return 0, 0, width, height
    left, top, right, bottom = crop
    return (
        round(width * left),
        round(height * top),
        width - round(width * right),
        height - round(height * bottom),
    )


def _in_line(host):
    """True for a picture set in the line of text and no taller than two lines."""
    height = _extent(host)[1]
    return host is not None and host.tag == WP + "inline" and 0 < height <= IN_LINE_EMU


def _figure(picture, doc, inline=False, offset=-1):
    """One picture, measured from the file Word stored rather than from the XML.

    The ways this can come up short stay apart, because they are different
    faults and get counted separately. An empty filename means the paragraph
    pointed at a relationship the document never declares, so there is no file to
    go and get.

    A filename with zero width and height means one of two things, and this
    function cannot tell them apart. Either the part is there and Pillow could
    not open it, or there is no part: the target is resolved exactly as Word
    wrote it, so a relationship carrying `TargetMode="External"`, or pointing
    somewhere other than `word/media/`, still yields its basename and measures
    as nothing. Both belong on the page — a picture that cannot be measured is
    no reason to stop reading the document — and what separates them is whether
    the name is among the files copied out of the package, which only the CLI
    knows; `missing_media` in the manifest is where it says so.

    `Image.DecompressionBombError` is caught with the rest because it is the
    one Pillow raises that is not an `OSError`: a picture declaring more pixels
    than Pillow will decode is exactly a picture that cannot be measured, and
    letting it out would stop the whole document over one image - which is the
    opposite of what the paragraph above promises.

    The size is the part Word shows: a cropped picture measures as its crop,
    because the CLI writes the file cropped. The size Word draws it at is
    kept beside it, in CSS pixels.
    """
    blip, host = picture
    rel_id = blip.get(REL + "embed")
    cx, cy = _extent(host)
    target = doc.rels.get(rel_id, "")
    crop = _crop(blip)
    shape = {
        "display_width": round(cx / EMU_PER_PX),
        "display_height": round(cy / EMU_PER_PX),
        "inline": inline,
        "offset": offset,
    }
    if not target:
        return Figure(rel_id=rel_id, **shape)
    width = height = 0
    try:
        with Image.open(io.BytesIO(doc.z.read("word/" + target.lstrip("/")))) as im:
            width, height = im.size
    except (KeyError, OSError, ValueError, Image.DecompressionBombError):
        pass
    if width and height and crop:
        left, top, right, bottom = crop_box(width, height, crop)
        width, height = right - left, bottom - top
    return Figure(
        rel_id=rel_id,
        filename=os.path.basename(target),
        width=width,
        height=height,
        crop=crop if width else (),
        **shape,
    )


def _text_boxes(p, doc):
    """The blocks of every text box anchored in this paragraph, each read once.

    Word writes a text box twice: as a `wps` shape under `mc:Choice` and
    again as VML under `mc:Fallback` for readers that predate it. The two
    hold the same words, so the fallback is read only when there is no
    choice. Only the outermost box is taken here; a box inside it is
    reached through its own paragraph.
    """
    boxes = [b for b in p.iter(W + "txbxContent") if _own(b, p, W + "txbxContent")]
    chosen = [
        b for b in boxes if not any(a.tag == MC + "Fallback" for a in b.iterancestors())
    ]
    out = []
    for box in chosen or boxes:
        out.extend(_flow(box, doc))
    return out


def _is_caption(block):
    """Whether this block is the line Word left under a picture.

    Word's own caption style is asked first, because it is the author saying so
    rather than us inferring it. Three paragraphs in this corpus carry it
    and all three are captions the regex already catches, so it changes
    nothing here - what it buys is the case the regex is known to get wrong. A
    body sentence opening "Figure 13 puts the coverage difference ..." reads as
    a caption to a rule that can only look at the first two words, and the
    style is what tells the two apart for nothing.
    """
    if not isinstance(block, Para) or not block.runs:
        return False
    if block.role == "CAPTION":
        return True
    return bool(CAPTION_RE.match("".join(r.text for r in block.runs)))


def _para_blocks(p, doc):
    """The blocks one paragraph contributes: its pictures, the paragraph, its boxes.

    A picture can sit inside the paragraph that describes it. Ricos has no
    inline image, so the picture is hoisted above the sentences it sat in rather
    than taking them down with it. A text box is hoisted the same way, below
    them, as the paragraphs it holds. A paragraph carrying no picture is kept
    even when it has no runs, since an empty paragraph is still a line on the
    page.

    A picture set in the line and no taller than two lines of text is not
    hoisted: it is part of the sentence - an equation drawn as a picture - and
    a sentence missing it reads "of the form ." while the equation stands a
    paragraph early. An ordinary paragraph is cut at it, so the picture sits
    between the two halves of its sentence; see `_in_sentence`. Any other
    paragraph - a caption, a heading, a list item, an aside - would become two
    of itself if cut, so it is kept whole and the picture follows it, carrying
    where in the text it sat. That is also what keeps a caption line ending on
    such a picture from handing its caption to it.

    This is the only route to `_para`, from the body and from inside a cell
    alike, so `doc` has to travel every path that reaches here or a list
    paragraph reads as a plain one - silently, because the fields it would have
    filled already have harmless defaults.
    """
    pictures = _pictures(p)
    para = _para(p, doc)
    says = any(r.text.strip() for r in para.runs)
    in_line = [x for x in pictures if says and _in_line(x[1])]
    runs = [
        next((a for a in x[0].iterancestors() if a.tag == W + "r"), None)
        for x in in_line
    ]
    segments = _segments(p, para.style, doc, runs) if in_line else []
    if len(segments) != len(in_line) + 1:
        in_line, segments = [], []  # a run the walk never reaches: hoist as before
    out = [_figure(x, doc) for x in pictures if not any(x is y for y in in_line)]
    if in_line and _cuttable(para):
        out.extend(_in_sentence(para, in_line, segments, doc))
    elif in_line:
        out.append(para)
        lead = len(_plain_text(para)) - len(_plain_text(para).lstrip())
        done = 0
        for x, seg in zip(in_line, segments, strict=False):
            done += sum(len(r.text) for r in seg)
            out.append(_figure(x, doc, inline=True, offset=max(0, done - lead)))
    elif para.runs or not out:
        out.append(para)
    out.extend(_text_boxes(p, doc))
    return out


def _plain_text(para):
    return "".join(r.text for r in para.runs)


def _cuttable(para):
    """Whether a paragraph can be cut in two and stay two ordinary paragraphs.

    A heading, a list item, an aside's paragraph, one drawing a rule and a
    caption cannot: each half would be one of those again - two headings, two
    list items, a box broken by the picture, a caption with no picture.
    """
    return not (
        para.heading
        or para.role
        or para.list_kind
        or para.aside
        or para.rule_above
        or para.rule_below
        or _is_caption(para)
    )


def _in_sentence(para, in_line, segments, doc):
    """The paragraph cut at each picture set in its sentence: stretch, picture,
    stretch. A stretch with nothing to say is left out rather than emitted as an
    empty paragraph."""
    said = [any(r.text.strip() for r in seg) for seg in segments]
    out = []
    for k, seg in enumerate(segments):
        if said[k]:
            out.append(replace(para, runs=seg))
        if k < len(in_line):
            figure = _figure(in_line[k], doc, inline=True)
            sides = ("prev" if said[k] else "") + ("next" if said[k + 1] else "")
            figure.joins = "both" if sides == "prevnext" else sides
            out.append(figure)
    return out


def _flow(el, doc):
    """The blocks of the paragraphs and tables directly under `el`, in order.

    Every other child is skipped. In the body the only one carrying text is
    the `w:sdt` holding Word's generated table of contents, which the page
    rebuilds from the headings anyway.
    """
    out = []
    for child in el:
        if child.tag == W + "p":
            out.extend(_para_blocks(child, doc))
        elif child.tag == W + "tbl":
            out.append(_table(child, doc))
    return out


# --- tables -----------------------------------------------------------------------


def _para_text(block):
    return "".join(r.text for r in block.runs).strip()


def _cell_content(tc, doc):
    """One cell's blocks, read the way the body is read; possibly none."""
    out = []
    for child in tc:
        if child.tag == W + "p":
            out.extend(_para_blocks(child, doc))
        elif child.tag == W + "tbl":
            out.extend(_flatten(child, doc))
    return out


def _flatten(tbl, doc):
    """A table inside a cell, as the words its cells hold.

    Ricos forbids a table inside a cell, so the inner grid cannot survive
    either way. What is kept is its content in reading order; what is not is
    the blank paragraph an empty inner cell would have stood for, because the
    placeholder that keeps a grid rectangular belongs to the outer cell and
    one per empty inner cell used to reach the page as so many blank lines.
    """
    out = []
    for row in tbl.findall(W + "tr"):
        for cell in row.findall(W + "tc"):
            out.extend(
                b
                for b in _cell_content(cell, doc)
                if not (isinstance(b, Para) and not _para_text(b))
            )
    return out


def _cell_blocks(tc, doc):
    """One cell, never empty, so a row keeps its cell count and the grid stays
    rectangular."""
    return _cell_content(tc, doc) or [Para()]


def _cell_has_text(cell):
    """True when the cell carries any text of its own."""
    return any(r.text.strip() for b in cell if isinstance(b, Para) for r in b.runs)


def _cell_is_bold(cell):
    """True when any of the cell's text is bold. A bold blank is not text."""
    return any(
        r.bold and r.text.strip() for b in cell if isinstance(b, Para) for r in b.runs
    )


def _span(tc):
    """How many grid columns this cell covers."""
    pr = tc.find(W + "tcPr")
    el = None if pr is None else pr.find(W + "gridSpan")
    if el is None:
        return 1
    try:
        return max(1, int(el.get(W + "val") or 1))
    except ValueError:
        return 1


def _row_cells(tr, doc):
    """One row's cells, with a merged cell expanded to the columns it covers.

    Ricos builds a table strictly as rows of cells and has no reliable colspan,
    so a merged cell is flattened rather than spanned: its content stays in the
    first column it covered and the columns after it arrive empty.
    """
    out = []
    for tc in tr.findall(W + "tc"):
        out.append(_cell_blocks(tc, doc))
        out.extend([Para()] for _ in range(_span(tc) - 1))
    return out


def _table(tbl, doc):
    """A Table, or a Callout when the table is the one-cell kind he asides with.

    The aside test counts the cells the author drew, before any span is
    expanded: one box is one box whatever grid columns it was told to cover.

    Rows are then padded out to the width of the widest one. Word lets a row
    stop short of the grid, so expanding a span is not on its own enough to
    leave every row the same length, and a row shorter than its neighbours is
    what Ricos renders as a broken table. The widest row is the target rather
    than w:tblGrid because the grid outlives the edits that shrank a table and
    can declare a column no row still uses.

    The first row is a header when every cell in it that says anything says it
    in bold. An empty cell is not evidence against a header row: a confusion
    matrix leaves its top-left corner blank and is a header row all the same,
    and flattening a merged cell leaves blanks of our own making that must not
    vote either.
    """
    trs = tbl.findall(W + "tr")
    drawn = trs[0].findall(W + "tc") if len(trs) == 1 else []
    if len(drawn) == 1:
        return Callout(blocks=_cell_blocks(drawn[0], doc))
    rows = [_row_cells(tr, doc) for tr in trs]
    width = max((len(row) for row in rows), default=0)
    for row in rows:
        row.extend([Para()] for _ in range(width - len(row)))
    spoken = [cell for cell in (rows[0] if rows else []) if _cell_has_text(cell)]
    header = bool(spoken) and all(_cell_is_bold(cell) for cell in spoken)
    return Table(rows=rows, header_row=header, widths=_grid_widths(tbl, trs, width))


def _grid_widths(tbl, trs, width):
    """Each column's share of the table, from `w:tblGrid`; [] when unsure.

    The grid is Word's own record of the column widths the author dragged,
    and the page lays the table out from it. It is trusted only when it names
    exactly the columns the rows were padded to, and when no row starts late:
    `w:gridBefore` shifts a row's cells along the grid, which `_row_cells`
    does not follow, so the widths would land on the wrong columns. Two tables
    in the ML guide and one in the Brochure start a row late; all three are
    narrow spacer columns Word left behind, and they lose nothing by it.
    """
    grid = tbl.find(W + "tblGrid")
    cols = grid.findall(W + "gridCol") if grid is not None else []
    if len(cols) != width or any(
        tr.find(W + "trPr/" + W + "gridBefore") is not None for tr in trs
    ):
        return []
    try:
        twips = [max(0, int(c.get(W + "w") or 0)) for c in cols]
    except ValueError:
        return []
    total = sum(twips)
    return [t / total for t in twips] if total else []


# --- the passes over the whole document ---------------------------------------------


def _fold_captions(blocks):
    """Fold the line under each picture into it, within one flow of blocks.

    Only the first such line is taken: a second one belongs to the next picture,
    or to the text. A cell is a flow of its own, so a caption never reaches back
    past the edge of the cell it was typed in, and a line after a table is not
    the caption of the last picture inside it.
    """
    out = []
    for block in blocks:
        if isinstance(block, Table):
            block.rows = [[_fold_captions(c) for c in row] for row in block.rows]
        elif isinstance(block, Callout):
            block.blocks = _fold_captions(block.blocks)
        prev = out[-1] if out else None
        # A picture set in a sentence is part of the text around it, never the
        # figure a caption line names.
        if (
            isinstance(prev, Figure)
            and not prev.caption
            and not prev.inline
            and _is_caption(block)
        ):
            prev.caption = "".join(r.text for r in block.runs).strip()
            continue
        out.append(block)
    return out


def _frame(blocks):
    """Turn the paragraphs' borders into the asides and rules they draw.

    A run of consecutive paragraphs barred down the left is one box: the
    "Disclaimer" pair in two documents, a seven-paragraph digression in a
    third. Anything else - a picture, a plain paragraph, a table - ends it,
    and the next barred paragraph opens another. A line above or below a
    paragraph is a rule on the page beside it; an empty paragraph with only
    a line under it is how Word draws a horizontal rule, and the emitter
    drops the paragraph and keeps the rule.

    A heading keeps its borders to itself. Understanding SHM and NDT rules
    under every one of its Heading1s, and what a heading looks like is the
    theme's decision on the page, as its colour is.

    Runs after the captions have folded, so a framed caption goes to its
    picture and not into a box of its own, and over the body flow only: a
    quote inside a table cell is a shape the validator has not seen.
    """
    out = []
    box = None
    for block in blocks:
        framed = isinstance(block, Para) and not block.heading
        if framed and block.aside:
            if box is None:
                box = Callout(blocks=[])
                out.append(box)
            box.blocks.append(block)
            continue
        box = None
        if framed and block.rule_above:
            out.append(Rule())
        out.append(block)
        if framed and block.rule_below:
            out.append(Rule())
    return out


def _number_figures(blocks):
    """Number the pictures in reading order, cells included.

    One sequence over the whole document, because a picture in a cell is a
    picture: numbering only the top level would leave every one of them at zero
    while the body counted on around it, and nothing would report the collision.

    The recursion is `walk`, which belongs to the model and is shared with
    whatever else has to see every block - see its docstring for what a second
    copy of it cost.
    """
    for number, figure in enumerate(
        (b for b in walk(blocks) if isinstance(b, Figure)), 1
    ):
        figure.number = number


def _body_color(blocks):
    """The colour most of the document's characters are written in, or "".

    The ML guide writes 85% of its characters in 262626 by direct formatting
    on every run, the Brochure 74% in 1A1A1A. That is the document's black,
    whatever the author's template called it, and it is measured in
    characters rather than runs because a run is an accident of editing.
    """
    weight = Counter()
    for block in walk(blocks):
        if isinstance(block, Para):
            for run in block.runs:
                weight[run.color] += len(run.text)
    return weight.most_common(1)[0][0] if weight else ""


def _relative_colors(blocks):
    """Strip the body colour, so that a run's colour is a departure from it.

    A decoration on every run of the document's own black would fight the
    site's text colour and cost the ML guide a tenth of its record. Runs the
    colour had kept apart from their uncoloured neighbours merge once it is
    gone.
    """
    base = _body_color(blocks)
    if not base:
        return
    for block in walk(blocks):
        if isinstance(block, Para):
            for run in block.runs:
                if run.color == base:
                    run.color = ""
            block.runs = _merge(block.runs)


def _note_blocks(doc):
    """The notes the body referred to, in that order, each opening "[n] ".

    Ricos has no note node and a single page has no foot, so the notes
    follow the body as paragraphs of their own, numbered as their marks are.
    A note's first paragraph carries the number; Word's own mark inside the
    note - `w:footnoteRef`, an empty element - reads as nothing, and the
    space the author typed after it goes with it.
    """
    out = []
    for number, (kind, note_id) in enumerate(doc.cited, 1):
        blocks = _flow(doc.notes[kind][note_id], doc.part(kind + "s"))
        first = next((b for b in blocks if isinstance(b, Para) and b.runs), None)
        if first is not None:
            first.runs[0].text = first.runs[0].text.lstrip()
            first.runs = _merge([Run(text=f"[{number}] ")] + first.runs)
        out.extend(b for b in blocks if not (isinstance(b, Para) and not b.runs))
    return out


def read_blocks(path_or_bytes):
    """Return the document as a list of blocks, in reading order.

    Paragraphs and tables are read and every other body child is skipped. The
    only one of those carrying text is the w:sdt holding Word's generated table
    of contents, which the page rebuilds from the headings anyway.

    Pictures become Figure blocks, in a cell as much as in the body, each with
    the "Figure N." line Word left under it folded in and numbered over the
    whole document. Paragraphs framed with a bar down the left become the
    aside they draw, a line above or below one becomes a Rule, and the notes
    the text refers to follow the body. Every colour is then read against the
    document's own body colour.

    The order of the passes is the order their inputs need: captions fold
    before framing so a framed caption reaches its picture, notes are added
    before the figures are numbered so a picture in a note counts, and
    colours are settled last, over everything.
    """
    with _open(path_or_bytes) as z:
        doc = _Doc(z)
        root = etree.fromstring(z.read("word/document.xml"))
        blocks = _frame(_fold_captions(_flow(root.find(W + "body"), doc)))
        blocks.extend(_note_blocks(doc))
    _number_figures(blocks)
    column = text_width(root)
    for figure in walk(blocks):
        if isinstance(figure, Figure):
            figure.column = column
    _relative_colors(blocks)
    return blocks


def text_width(root):
    """The width of the text column, in CSS pixels, or 0 when the file does not
    say: the page width less its left and right margins, from the section
    properties that close the body. The corpus runs from 620 px (From Bridges
    to Photons) to 733 (the Brochure's narrow margins); each of its documents
    is one section."""
    body = root.find(W + "body")
    sect = body.find(W + "sectPr") if body is not None else None
    size = sect.find(W + "pgSz") if sect is not None else None
    margins = sect.find(W + "pgMar") if sect is not None else None
    if size is None or margins is None:
        return 0
    try:
        twips = (
            int(size.get(W + "w"))
            - int(margins.get(W + "left") or 0)
            - int(margins.get(W + "right") or 0)
        )
    except (TypeError, ValueError):
        return 0
    return max(0, round(twips / TWIPS_PER_PX))
