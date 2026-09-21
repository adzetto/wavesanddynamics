"""Read a .docx into the intermediate blocks.

We parse the XML rather than going through pandoc because everything that decides
the page is what a generic converter flattens. A heading arriving as an ordinary
paragraph costs the page its outline. Bold, italic and a link are decorations in
Ricos, so a mark dropped here can never be recovered downstream. A picture and
the italic line beneath it are one figure to a reader and two paragraphs in the
file, and nothing but their order says so. Even a tab is an empty element:
invisible until it is gone and the words on either side have fused.

Only body-level paragraphs are read so far, so the pictures and text that live
inside table cells are still missing.
"""
import io
import os
import re
import zipfile

from lxml import etree
from PIL import Image

from tools.ricos.blocks import Figure, Para, Run

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

# Word leaves a caption as an ordinary italic paragraph. What tells it apart from
# any other emphasis is that it opens the way the author numbers his figures.
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

    A picture Pillow cannot open still belongs on the page, so a failure leaves
    the size at zero instead of stopping the document; zero reads as unknown.
    """
    target = rels.get(rel_id, "")
    name = os.path.basename(target)
    width = height = 0
    try:
        with Image.open(io.BytesIO(z.read("word/" + target.lstrip("/")))) as im:
            width, height = im.size
    except Exception:
        pass
    return Figure(rel_id=rel_id, filename=name, width=width, height=height)


def _is_caption(block):
    if not isinstance(block, Para) or not block.runs:
        return False
    if not all(r.italic for r in block.runs):
        return False
    return bool(CAPTION_RE.match("".join(r.text for r in block.runs)))


def read_blocks(path_or_bytes):
    """Return the document as a flat list of blocks, in reading order.

    Pictures become Figure blocks. The italic "Figure N." line Word leaves under
    a picture is folded into that Figure and removed from the flow, so it is
    never rendered twice.
    """
    with _open(path_or_bytes) as z:
        rels = _read_rels(z)
        root = etree.fromstring(z.read("word/document.xml"))
        body = root.find(W + "body")

        out = []
        for p in body.findall(W + "p"):
            ids = _blip_ids(p)
            if not ids:
                out.append(_para(p, rels))
                continue
            out.extend(_figure(rel_id, rels, z) for rel_id in ids)
            # A picture can sit inside the paragraph that describes it. Ricos
            # has no inline image, so the picture is hoisted above the sentences
            # it sat in rather than taking them down with it.
            para = _para(p, rels)
            if para.runs:
                out.append(para)

    merged = []
    for block in out:
        if _is_caption(block) and merged and isinstance(merged[-1], Figure):
            merged[-1].caption = "".join(r.text for r in block.runs).strip()
            continue
        merged.append(block)

    n = 0
    for block in merged:
        if isinstance(block, Figure):
            n += 1
            block.number = n
    return merged
