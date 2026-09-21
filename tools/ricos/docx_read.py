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


def _open(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return zipfile.ZipFile(io.BytesIO(path_or_bytes))
    return zipfile.ZipFile(path_or_bytes)


def _runs(p):
    out = []
    for r in p.iter(W + "r"):
        text = "".join(t.text or "" for t in r.iter(W + "t"))
        if not text:
            continue
        rpr = r.find(W + "rPr")
        out.append(
            Run(
                text=text,
                bold=rpr is not None and rpr.find(W + "b") is not None,
                italic=rpr is not None and rpr.find(W + "i") is not None,
                underline=rpr is not None and rpr.find(W + "u") is not None,
            )
        )
    return out


def _para(p):
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
    return Para(runs=_runs(p), style=style, align=align)


def read_blocks(path_or_bytes):
    """Return the document as a flat list of blocks, in reading order."""
    with _open(path_or_bytes) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    return [_para(p) for p in body.findall(W + "p")]
