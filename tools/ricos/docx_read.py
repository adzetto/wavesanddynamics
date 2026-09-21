"""Read a .docx into the intermediate blocks.

We parse the XML rather than going through pandoc because three things have to
survive that a generic converter flattens: which tables are really one-cell
asides, which italic line under a picture is its caption, and which heading
style each paragraph carries. Those three decide the whole page.
"""
import io
import zipfile

from lxml import etree

from tools.ricos.blocks import Para, Run

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

ALIGN = {"both": "JUSTIFY", "center": "CENTER", "right": "RIGHT", "left": "LEFT"}

REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
RELS_NS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# Word switches a mark off with a value, not by leaving the element out: a run
# that escapes a bold style carries <w:b w:val="0"/>, and an underline is
# cancelled with <w:u w:val="none"/>. Presence alone would read those as on.
MARK_OFF = {"0", "false", "off", "none"}


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


def _run(r, link):
    text = "".join(t.text or "" for t in r.iter(W + "t"))
    rpr = r.find(W + "rPr")
    return Run(
        text=text,
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


def read_blocks(path_or_bytes):
    """Return the document as a flat list of blocks, in reading order."""
    with _open(path_or_bytes) as z:
        rels = _read_rels(z)
        root = etree.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    return [_para(p, rels) for p in body.findall(W + "p")]
