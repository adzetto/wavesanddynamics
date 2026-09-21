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
"""
import io
import os
import re
import zipfile

from lxml import etree
from PIL import Image

from tools.ricos.blocks import Callout, Figure, Para, Run, Table

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DRAW = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

ALIGN = {"both": "JUSTIFY", "center": "CENTER", "right": "RIGHT", "left": "LEFT"}

REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Word switches a mark off with a value, not by leaving the element out: a run
# that escapes a bold style carries <w:b w:val="0"/>, and an underline is
# cancelled with <w:u w:val="none"/>. Presence alone would read those as on.
MARK_OFF = {"0", "false", "off", "none"}

# A tab and a line break are empty elements standing between the text pieces of
# a run. A run holding nothing else reads as empty, is dropped, and then the
# merge below fuses its two neighbours: that is how the hand-typed contents list
# in the ML guide came out as "What is Machine Learning?2".
WHITESPACE = {W + "tab": "\t", W + "br": "\n"}

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


def _open(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return zipfile.ZipFile(io.BytesIO(path_or_bytes))
    return zipfile.ZipFile(path_or_bytes)


def _read_rels(z):
    """rId -> target, for hyperlinks and images."""
    try:
        root = etree.fromstring(z.read("word/_rels/document.xml.rels"))
    except KeyError:
        return {}
    return {r.get("Id"): r.get("Target") for r in root.findall(RELS_NS + "Relationship")}


def _mark(rpr, name):
    """True when run property `name` is present and not switched off."""
    if rpr is None:
        return False
    el = rpr.find(W + name)
    if el is None:
        return False
    return (el.get(W + "val") or "").lower() not in MARK_OFF


def _text(r):
    """Run text, with tabs and line breaks kept as the whitespace they stand for."""
    return "".join(
        el.text or "" if el.tag == W + "t" else WHITESPACE[el.tag]
        for el in r.iter(W + "t", W + "tab", W + "br")
    )


def _run(r, link):
    rpr = r.find(W + "rPr")
    return Run(
        text=_text(r),
        bold=_mark(rpr, "b"),
        italic=_mark(rpr, "i"),
        underline=_mark(rpr, "u"),
        link=link,
    )


def _runs(p, rels):
    """Direct-child runs plus runs inside hyperlinks, merged where marks match."""
    out = []
    for child in p:
        if child.tag == W + "r":
            out.append(_run(child, ""))
        elif child.tag == W + "hyperlink":
            target = rels.get(child.get(REL + "id"), "")
            for r in child.findall(W + "r"):
                out.append(_run(r, target))
    merged = []
    for run in out:
        if not run.text:
            continue
        if merged and (
            merged[-1].bold == run.bold
            and merged[-1].italic == run.italic
            and merged[-1].underline == run.underline
            and merged[-1].link == run.link
        ):
            merged[-1].text += run.text
        else:
            merged.append(run)
    return merged


def _para(p, rels):
    ppr = p.find(W + "pPr")
    style = ""
    align = "AUTO"
    if ppr is not None:
        s = ppr.find(W + "pStyle")
        if s is not None:
            style = s.get(W + "val") or ""
        j = ppr.find(W + "jc")
        if j is not None:
            align = ALIGN.get(j.get(W + "val") or "", "AUTO")
    return Para(runs=_runs(p, rels), style=style, align=align)


def _blip_ids(p):
    """Relationship ids of every picture anchored in this paragraph."""
    return [b.get(REL + "embed") for b in p.iter(DRAW + "blip")
            if b.get(REL + "embed")]


def _figure(rel_id, rels, z):
    """One picture, measured from the file Word stored rather than from the XML.

    The two ways this can come up short stay apart, because they are different
    faults and get counted separately. An empty filename means the paragraph
    pointed at a relationship the document never declares, so there is no file to
    go and get. A filename with zero width and height means the part is there but
    could not be measured — which still belongs on the page, since a picture
    Pillow cannot open is no reason to stop reading the document.
    """
    target = rels.get(rel_id, "")
    if not target:
        return Figure(rel_id=rel_id)
    width = height = 0
    try:
        with Image.open(io.BytesIO(z.read("word/" + target.lstrip("/")))) as im:
            width, height = im.size
    except (KeyError, OSError, ValueError):
        pass
    return Figure(rel_id=rel_id, filename=os.path.basename(target),
                  width=width, height=height)


def _is_caption(block):
    if not isinstance(block, Para) or not block.runs:
        return False
    return bool(CAPTION_RE.match("".join(r.text for r in block.runs)))


def _para_blocks(p, rels, z):
    """The blocks one paragraph contributes: its pictures, then the paragraph.

    A picture can sit inside the paragraph that describes it. Ricos has no
    inline image, so the picture is hoisted above the sentences it sat in rather
    than taking them down with it. A paragraph carrying no picture is kept even
    when it has no runs, since an empty paragraph is still a line on the page.
    """
    out = [_figure(rel_id, rels, z) for rel_id in _blip_ids(p)]
    para = _para(p, rels)
    if para.runs or not out:
        out.append(para)
    return out


def _cell_blocks(tc, rels, z):
    """One cell, read the way the body is read.

    Never empty, so a row keeps its cell count and the grid stays rectangular.
    """
    out = []
    for child in tc:
        if child.tag == W + "p":
            out.extend(_para_blocks(child, rels, z))
        elif child.tag == W + "tbl":
            # Ricos forbids a table inside a cell, so the inner grid cannot
            # survive either way. Flattening it to its paragraphs keeps the words.
            for row in child.findall(W + "tr"):
                for cell in row.findall(W + "tc"):
                    out.extend(_cell_blocks(cell, rels, z))
    return out or [Para()]


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


def _row_cells(tr, rels, z):
    """One row's cells, with a merged cell expanded to the columns it covers.

    Ricos builds a table strictly as rows of cells and has no reliable colspan,
    so a merged cell is flattened rather than spanned: its content stays in the
    first column it covered and the columns after it arrive empty.
    """
    out = []
    for tc in tr.findall(W + "tc"):
        out.append(_cell_blocks(tc, rels, z))
        out.extend([Para()] for _ in range(_span(tc) - 1))
    return out


def _table(tbl, rels, z):
    """A Table, or a Callout when the table is the one-cell kind he asides with.

    The aside test counts the cells the author drew, before any span is
    expanded: one box is one box whatever grid columns it was told to cover.

    Rows are then padded out to the width of the widest one. Word lets a row
    stop short of the grid, so expanding a span is not on its own enough to
    leave every row the same length, and a row shorter than its neighbours is
    what Ricos renders as a broken table. The widest row is the target rather
    than w:tblGrid because the grid outlives the edits that shrank a table and
    can declare a column no row still uses.
    """
    trs = tbl.findall(W + "tr")
    drawn = trs[0].findall(W + "tc") if len(trs) == 1 else []
    if len(drawn) == 1:
        return Callout(blocks=_cell_blocks(drawn[0], rels, z))
    rows = [_row_cells(tr, rels, z) for tr in trs]
    width = max((len(row) for row in rows), default=0)
    for row in rows:
        row.extend([Para()] for _ in range(width - len(row)))
    header = bool(rows and rows[0]) and all(
        any(r.bold for b in cell if isinstance(b, Para) for r in b.runs)
        for cell in rows[0]
    )
    return Table(rows=rows, header_row=header)


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
        if isinstance(prev, Figure) and not prev.caption and _is_caption(block):
            prev.caption = "".join(r.text for r in block.runs).strip()
            continue
        out.append(block)
    return out


def _number_figures(blocks, n=0):
    """Number the pictures in reading order, cells included, and return the count.

    One sequence over the whole document, because a picture in a cell is a
    picture: numbering only the top level would leave every one of them at zero
    while the body counted on around it, and nothing would report the collision.
    """
    for block in blocks:
        if isinstance(block, Figure):
            n += 1
            block.number = n
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    n = _number_figures(cell, n)
        elif isinstance(block, Callout):
            n = _number_figures(block.blocks, n)
    return n


def read_blocks(path_or_bytes):
    """Return the document as a list of blocks, in reading order.

    Paragraphs and tables are read and every other body child is skipped. The
    only one of those carrying text is the w:sdt holding Word's generated table
    of contents, which the page rebuilds from the headings anyway.

    Pictures become Figure blocks, in a cell as much as in the body, each with
    the "Figure N." line Word left under it folded in and numbered over the
    whole document.
    """
    with _open(path_or_bytes) as z:
        rels = _read_rels(z)
        root = etree.fromstring(z.read("word/document.xml"))
        body = root.find(W + "body")

        out = []
        for child in body:
            if child.tag == W + "p":
                out.extend(_para_blocks(child, rels, z))
            elif child.tag == W + "tbl":
                out.append(_table(child, rels, z))

    blocks = _fold_captions(out)
    _number_figures(blocks)
    return blocks
