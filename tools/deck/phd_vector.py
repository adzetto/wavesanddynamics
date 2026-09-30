"""His MSc and PhD presentation, presented as vectors.

presentation.html shows his 177 slides as the pictures PowerPoint drew of them
(content/deck-phd/sNNN.png, and web/sNNN-{320,960,1600}.webp). A 1600 picture
enlarged on a large or Retina screen goes soft, so the viewer (site/parts/deck.py)
draws a slide from web/sNNN.svg while presenting, once every slide has one. This
script makes those SVGs from his PowerPoint and changes nothing else of the deck.
The client, 28 Sep 2026: "Doktora sunumunun içeriğine dokunma sadece present
modunu vektörize yap" (leave the PhD presentation's content alone, only make its
present mode vector).

    copy     his .pptx copied into the work folder with what the published
             pictures show and his file does not: on slides 1 and 56 the address
             korkutkaynardag@iyte.edu.tr where his file has his old one (set in
             Calibri at the size painted over the pictures, the lines around it
             where they were), and slide 132's citation in Calibri, the face
             PowerPoint drew the pictures with (FONTS). Every part of the copy is
             then read for addresses and phone numbers: that address, on those
             two slides, is the only one.
    pdf      PowerPoint prints the copy to a PDF: the slides only (no notes, no
             handouts, no document properties), all of them (none is hidden),
             each page 960 x 540 pt. The same PowerPoint then draws every slide
             of the copy at 1600 x 900, as the published pictures were made, and
             each must be the published picture pixel for pixel (bar the
             address): so the PDF is printed from what the site shows.
    order    every page against the published pictures: page k must look most
             like sNNN.png of slide k, so the count and the order are his.
    svg      each page a standalone SVG (MuPDF; his words as outlines, so it
             needs no font). PowerPoint's PDF scales some of his pictures down
             and turns others into JPEG; each picture that is his, unaltered, is
             put back from the .pptx at its native size: the one in the place
             the slide puts it (its frame's centre), cut as the slide crops it
             and matching PowerPoint's print at full size. Every picture is
             brought down to the pixels it can show on a 5K screen (SHOWN_W),
             never up, and re-encoded as WebP (lossless for a drawing, quality
             LOSSY_Q for a photograph) without metadata; path data is written
             short (vector.minify, then quadratics, smooth runs and baselines
             factored out: the same shapes in fewer bytes).
    check    Chromium draws every SVG in an <img> at 1600 x 900, as the viewer
             does. Against its own page of the PDF (as MuPDF draws it) it must
             not differ by more than PDF_LOCAL_MAX once both are blurred;
             against sNNN-1600.webp and sNNN.png it is measured (mean absolute
             difference, SSIM, the largest blurred difference), and every slide
             past the limits is looked at, where it differs most, in review/
             (LOOKED says what was found).
    privacy  the PDF's text layer and every SVG: no address but
             korkutkaynardag@iyte.edu.tr, no phone number, no text in an SVG, no
             metadata in any picture inside, nothing site/build.py's privacy
             check would refuse (a picture whose data happens to spell it is
             encoded again).
    write    only when all of the above hold: web/sNNN.svg into content/deck-phd/.

    python tools/deck/phd_vector.py            every step, and write if all pass
    python tools/deck/phd_vector.py --look     every step but write
    python tools/deck/phd_vector.py svg 5-9    one step, some slides

Nothing is written but the work folder (build/r12-phddeck/work, or --work) and
content/deck-phd/web/sNNN.svg. The .pptx, its copy, the PDF and his notes never
leave the work folder; no PDF goes into content/deck-phd/, which the site would
publish. PowerPoint is closed when done, unless someone else's presentation is
open in it.
"""

import argparse
import base64
import gc
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import vector  # noqa: E402

SRC = r"C:\Users\lenovo\Downloads\Transfer\PhD_MsC_entire_Review_ppt.pptx"
DECK = os.path.join(ROOT, "content", "deck-phd")
WEB = os.path.join(DECK, "web")
WORK = os.path.join(ROOT, "build", "r12-phddeck", "work")
COUNT = 177
ADDRESS = "korkutkaynardag@iyte.edu.tr"

# What the site may never carry (site/build.py's PRIVATE and EMAIL, which its
# private_report() runs over every .svg it publishes, picture data included),
# and what a phone number looks like in running text.
PRIVATE = re.compile(r"gmail|300\W{0,3}4065", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HIS_PHONES = re.compile(r"512\W{0,3}300|750\W{0,3}68\W{0,3}13")
DIGITS = re.compile(r"\+?\(?\d[\d \t().\-/]{5,}\d")
# The runs of seven or more digits his slides do carry, none a phone number:
# page ranges, years, a patent and the DOIs of his papers.
NOT_PHONES = {"3227-3243", "1991 - 2020", "5 - 10 - 20 - 30", "(9-10-11-12", "04022048",
              "2018/051535", "7364-7381", "00707-023-03484-8", "03611981221094576",
              "40799-020-00401-9"}
DATE = re.compile(r"\d{1,2}[./]\d{1,2}[./]\d{4}")

# ------------------------------------------------------------------ copy
# The paragraph that holds his old address on each slide, known by its hash
# (so the address itself is written nowhere here), and what replaces it. The
# published pictures had the address painted over in Calibri, 28 px on slide
# 1 and 32 px on slide 56 of the 1600 picture: 16.8 pt and 19.2 pt. A fixed
# line height keeps the lines around it where they were (slide 1's box grows
# from the bottom; on slide 56 the line under it follows it).
CALIBRI = ('<a:latin typeface="Calibri" panose="020F0502020204030204" pitchFamily="34" charset="0"/>'
           '<a:cs typeface="Calibri" panose="020F0502020204030204" pitchFamily="34" charset="0"/>')
SWAPS = {
    "ppt/slides/slide1.xml": (
        "6ab4403988c4194bb1621eb0582bb0642f7c3bd3dafa013b5f58ca295716f150",
        '<a:p><a:pPr algn="l"><a:lnSpc><a:spcPts val="1728"/></a:lnSpc></a:pPr><a:r>'
        f'<a:rPr lang="en-US" sz="1680" dirty="0">{CALIBRI}</a:rPr><a:t>{ADDRESS}</a:t></a:r>'
        '<a:endParaRPr lang="en-US" sz="1600" dirty="0"><a:latin typeface="Californian FB" '
        'panose="0207040306080B030204" pitchFamily="18" charset="0"/><a:cs typeface="Times New Roman" '
        'panose="02020603050405020304" pitchFamily="18" charset="0"/></a:endParaRPr></a:p>'),
    "ppt/slides/slide56.xml": (
        "f4b8d6d2e124a9c381878d47883d58b252f4effcc5c7caf34ab0fdca17f5957e",
        '<a:p><a:pPr algn="ctr"><a:lnSpc><a:spcPts val="2400"/></a:lnSpc></a:pPr><a:r>'
        f'<a:rPr lang="en-US" sz="1920" dirty="0"/><a:t>{ADDRESS}    </a:t></a:r></a:p>'),
}
# Four runs of words are drawn in another face than the pictures show. The
# pictures were exported on 25 Sep 2026 at 11:18, the minute Office first
# fetched Playfair Display (a cloud font) for slide 132's citation line, so
# PowerPoint drew those four runs in Calibri; with the font now at hand it
# draws Playfair Display. The copy names Calibri there, which PowerPoint then
# draws pixel for pixel as published.
FONTS = {"ppt/slides/slide132.xml": ('<a:latin typeface="playfair display"/>', '<a:latin typeface="Calibri"/>', 4)}
PARA = re.compile(r"<a:p>(?:(?!</a:p>).)*?</a:p>", re.S)


def paragraphs_with_at(xml):
    return [p for p in PARA.findall(xml) if "@" in p]


def texts(z):
    """(part, the words of each paragraph) for every XML part of a package."""
    for n in z.namelist():
        if n.endswith((".xml", ".rels")):
            x = z.read(n).decode("utf-8", "replace")
            words = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in PARA.findall(x)]
            yield n, x, words


def copy_pptx(work):
    """His .pptx into `work`, with the address swapped on slides 1 and 56 and
    slide 132's citation in the face the pictures show."""
    out = os.path.join(work, "phd.pptx")
    tmp = out + ".part"
    with zipfile.ZipFile(SRC) as zin, zipfile.ZipFile(tmp, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename in SWAPS:
                digest, new = SWAPS[info.filename]
                xml = data.decode("utf-8")
                old = paragraphs_with_at(xml)
                if len(old) != 1 or hashlib.sha256(old[0].encode()).hexdigest() != digest:
                    raise SystemExit(f"{info.filename}: the address paragraph is not the one expected")
                data = xml.replace(old[0], new, 1).encode("utf-8")
            if info.filename in FONTS:
                was, now, count = FONTS[info.filename]
                xml = data.decode("utf-8")
                if xml.count(was) != count:
                    raise SystemExit(f"{info.filename}: {xml.count(was)} runs in the face, not {count}")
                data = xml.replace(was, now).encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            zi.compress_type = info.compress_type
            zi.external_attr = info.external_attr
            zout.writestr(zi, data)
            del data
    os.replace(tmp, out)
    # the copy against his file: the two slides changed, every other part the same
    with zipfile.ZipFile(SRC) as a, zipfile.ZipFile(out) as b:
        ca = {i.filename: i.CRC for i in a.infolist()}
        cb = {i.filename: i.CRC for i in b.infolist()}
        changed = sorted(n for n in ca if cb.get(n) != ca[n])
        if sorted(ca) != sorted(cb) or changed != sorted(set(SWAPS) | set(FONTS)):
            raise SystemExit(f"the copy differs from his file beyond slides 1, 56 and 132: {changed}")
        found = scan_package(b)
    bad = [f for f in found if f[1] != ADDRESS or f[0] not in SWAPS]
    if bad or sorted(f[0] for f in found) != sorted(SWAPS):
        raise SystemExit(f"the copy carries an address or number it must not: {bad or found}")
    print(f"copy: {os.path.relpath(out, ROOT)}; slides 1 and 56 carry {ADDRESS}, slide 132's "
          f"citation is in Calibri as published, nothing else changed; no other address or "
          f"phone number in any part")
    return out


def phone_like(s):
    """A run of seven or more digits that is not one of his known numbers or a date."""
    s = " ".join(s.split())
    return sum(c.isdigit() for c in s) >= 7 and s not in NOT_PHONES and not DATE.fullmatch(s)


def scan_package(z):
    """[(part, what)] for every address, mailto/tel link and phone-like number
    in a package's XML: slides, layouts, masters, notes, charts, diagrams."""
    found = []
    for n, x, words in texts(z):
        for m in EMAIL.finditer(x):
            found.append((n, m.group()))
        found += [(n, m.group()) for m in re.finditer(r"(?:mailto|tel):[^\"<]+", x)]
        for w in words:
            found += [(n, m.group()) for m in PRIVATE.finditer(w)]
            found += [(n, m.group()) for m in HIS_PHONES.finditer(w)]
            found += [(n, m.group()) for m in DIGITS.finditer(w) if phone_like(m.group())]
    return found


# ------------------------------------------------------------------ pdf
def print_pdf(work):
    """PowerPoint prints the copy: slides only, no hidden slides, no notes."""
    import pythoncom
    import win32com.client.dynamic as dyn
    src, out = os.path.join(work, "phd.pptx"), os.path.join(work, "phd.pdf")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(src) as z:
        hidden = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)
                  and re.search(rb'<p:sld\b[^>]*\bshow="(?:0|false)"', z.read(n))]
    pythoncom.CoInitialize()
    app = dyn.Dispatch("PowerPoint.Application")
    others = app.Presentations.Count          # someone else's work stays open
    pres = app.Presentations.Open(src, True, False, False)   # read only, no window
    try:
        n = pres.Slides.Count
        # ppFixedFormatTypePDF, ppFixedFormatIntentPrint, no frames, handout
        # order, ppPrintOutputSlides, hidden slides not printed, no range, all
        # slides, no show name, no document properties, IRM kept, structure
        # tags, fonts that cannot be embedded as bitmaps, not PDF/A
        pres.ExportAsFixedFormat(out, 2, 2, 0, 1, 1, 0, None, 1, "", False, True, True, True, False)
        # and PowerPoint's own pictures of the copy, as the published ones were made
        pics = os.path.join(work, "ppt")
        os.makedirs(pics, exist_ok=True)
        for k in range(1, n + 1):
            pres.Slides(k).Export(os.path.join(pics, f"s{k:03d}.png"), "PNG", 1600, 900)
    finally:
        pres.Close()
        if app.Presentations.Count == 0 and others == 0:
            app.Quit()
        del pres, app
        gc.collect()
        pythoncom.CoUninitialize()
    import fitz
    with fitz.open(out) as doc:
        pages = len(doc)
        sizes = {(round(p.rect.width, 2), round(p.rect.height, 2)) for p in doc}
    if hidden or n != COUNT or pages != COUNT or sizes != {(960.0, 540.0)}:
        raise SystemExit(f"pdf: {pages} pages of {sizes}, {n} slides, hidden {hidden}; "
                         f"expected {COUNT} pages of 960 x 540")
    print(f"pdf: {os.path.relpath(out, ROOT)}, {pages} pages, {os.path.getsize(out) / 1e6:.1f} MB, "
          f"no hidden slide, no notes")
    same_as_published(work)
    return out


# Where PowerPoint's picture of the copy may differ from the published one:
# the painted-over address (and, on slide 1, the two lines over it, which
# the address line's new face moves by a fraction of a pixel).
ADDRESS_BOX = {1: (40, 760, 560, 890), 56: (510, 340, 1010, 395)}


def same_as_published(work):
    """PowerPoint today draws the copy as the published pictures: every slide
    at 1600 x 900, no pixel off by more than 16 of 255 outside ADDRESS_BOX. So
    the PDF, printed by the same PowerPoint from the same copy, holds what the
    pictures show."""
    import numpy as np
    from PIL import Image
    off = []
    for k in range(1, COUNT + 1):
        with Image.open(os.path.join(work, "ppt", f"s{k:03d}.png")) as a,                 Image.open(os.path.join(DECK, f"s{k:03d}.png")) as b:
            d = np.abs(np.asarray(a.convert("RGB"), np.int16) - np.asarray(b.convert("RGB"), np.int16)).max(axis=2)
        if k in ADDRESS_BOX:
            x0, y0, x1, y1 = ADDRESS_BOX[k]
            d[y0:y1, x0:x1] = 0
        if (d > 16).any():
            off.append((k, int((d > 16).sum())))
    print(f"same: PowerPoint draws the copy as published on {COUNT - len(off)} of {COUNT} slides "
          f"(slides 1 and 56 outside the address)")
    if off:
        raise SystemExit(f"same: PowerPoint's pictures of the copy differ from the published ones: {off}")


# ------------------------------------------------------------------ order
def check_order(work):
    """Page k of the PDF looks most like slide k's published picture."""
    import fitz
    import numpy as np
    from PIL import Image
    w, h = 96, 54
    pages, pics = [], []
    with fitz.open(os.path.join(work, "phd.pdf")) as doc:
        for p in doc:
            pix = p.get_pixmap(matrix=fitz.Matrix(w / p.rect.width, h / p.rect.height), alpha=False)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).convert("L")
            pages.append(np.asarray(im.resize((w, h), Image.BOX), dtype=np.float32))
    for k in range(1, COUNT + 1):
        with Image.open(os.path.join(DECK, f"s{k:03d}.png")) as im:
            pics.append(np.asarray(im.convert("L").resize((w, h), Image.BOX), dtype=np.float32))
    P, Q = np.stack(pages), np.stack(pics)
    dist = np.stack([np.abs(Q - page).mean(axis=(1, 2)) for page in P])     # page x picture
    wrong, ties = [], []
    for k in range(len(P)):
        best = int(dist[k].argmin())
        if best != k and dist[k, best] < dist[k, k] - 1e-6:
            wrong.append((k + 1, best + 1, round(float(dist[k, k]), 2), round(float(dist[k, best]), 2)))
        others = np.delete(dist[k], k)
        if others.min() <= dist[k, k] + 0.5:
            ties.append((k + 1, int(np.delete(np.arange(len(P)), k)[others.argmin()]) + 1))
    worst = float(np.diag(dist).max())
    print(f"order: {len(P)} pages for {COUNT} pictures; each page nearest its own slide "
          f"(largest own distance {worst:.2f} of 255){'; near-twins ' + str(ties) if ties else ''}")
    if len(P) != COUNT or wrong:
        raise SystemExit(f"order: pages out of place: {wrong}")
    return {"largest_own_distance": worst, "twins": ties}


# ------------------------------------------------------------------ svg
SVG_NS = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK)
HREF = f"{{{XLINK}}}href"
LOSSY_Q = 75            # a photograph, as WebP (the published pictures are WebP at 70)
DRAWING_Q = 88          # a picture is a drawing when lossless costs at most
LOSSLESS_UNDER = 1.5    # this many times a WebP at DRAWING_Q
MATCH = 10.0            # the largest mean difference (0 to 255) at 32 x 32 to look closer,
MATCH_FULL = 4.0        # and at full size (both blurred by 1 px) for "the same picture",
PLACE = 3.0             # and how far (pt) its frame's centre may be from the print's
# The widest a slide is ever drawn: presenting full screen on a 2560 px wide
# screen at two device pixels to the CSS pixel (a 5K display). A picture that
# holds more than MORE_THAN times the pixels it covers there is brought down
# to them; no screen shows the difference.
SHOWN_W = 5120
MORE_THAN = 1.1


def _q(tag):
    return f"{{{SVG_NS}}}{tag}"


def rels(z, part):
    """{rId: (type, target part)} of a part."""
    folder, name = posixpath.split(part)
    path = posixpath.join(folder, "_rels", name + ".rels")
    out = {}
    if path not in z.namelist():
        return out
    for r in ET.fromstring(z.read(path)):
        if r.get("TargetMode") == "External":
            continue
        out[r.get("Id")] = (r.get("Type").rsplit("/", 1)[-1],
                            posixpath.normpath(posixpath.join(folder, r.get("Target"))))
    return out


def slide_parts(z):
    """Each slide's part in his order, with its layout and master."""
    pres = ET.fromstring(z.read("ppt/presentation.xml"))
    prels = rels(z, "ppt/presentation.xml")
    out = []
    for sid in pres.iter("{http://schemas.openxmlformats.org/presentationml/2006/main}sldId"):
        slide = prels[sid.get(f"{{{R_NS}}}id")][1]
        layout = next(t for k, t in rels(z, slide).values() if k == "slideLayout")
        master = next(t for k, t in rels(z, layout).values() if k == "slideMaster")
        out.append((slide, layout, master))
    return out


# The one extension a picture of his may carry and still be drawn as it is
# stored ("use the picture's own dpi"); any other child of <a:blip> (a
# brightness, a recolouring, an artistic effect) changes the picture, and
# PowerPoint's print of it is kept.
PLAIN_EXT = {"{28A0092B-C50C-407E-A947-70E740481C1C}"}


def frame_centre(el, parent):
    """The centre, in pt on the slide, of the shape that holds `el` (a
    picture or a shape filled with one), through every group around it; None
    where it has no frame of its own."""
    P = "http://schemas.openxmlformats.org/presentationml/2006/main"
    shape = el
    while shape is not None and shape.tag not in (f"{{{P}}}pic", f"{{{P}}}sp"):
        shape = parent.get(shape)
    if shape is None:
        return None
    x = shape.find(f"{{{P}}}spPr/{{{A_NS}}}xfrm")
    if x is None or x.find(f"{{{A_NS}}}off") is None or x.find(f"{{{A_NS}}}ext") is None:
        return None
    off, ext = x.find(f"{{{A_NS}}}off"), x.find(f"{{{A_NS}}}ext")
    cx = int(off.get("x")) + int(ext.get("cx")) / 2
    cy = int(off.get("y")) + int(ext.get("cy")) / 2
    g = parent.get(shape)
    while g is not None:
        if g.tag == f"{{{P}}}grpSp":
            gx = g.find(f"{{{P}}}grpSpPr/{{{A_NS}}}xfrm")
            if gx is not None and gx.find(f"{{{A_NS}}}chExt") is not None:
                o, e = gx.find(f"{{{A_NS}}}off"), gx.find(f"{{{A_NS}}}ext")
                co, ce = gx.find(f"{{{A_NS}}}chOff"), gx.find(f"{{{A_NS}}}chExt")
                sx = int(e.get("cx")) / max(1, int(ce.get("cx")))
                sy = int(e.get("cy")) / max(1, int(ce.get("cy")))
                cx = int(o.get("x")) + (cx - int(co.get("x"))) * sx
                cy = int(o.get("y")) + (cy - int(co.get("y"))) * sy
        g = parent.get(g)
    return (cx / 12700, cy / 12700)


def fills(z, part):
    """[(media part, crop l, t, r, b as fractions, centre in pt or None)] of
    every picture fill that shows his picture as it is stored: stretched, not
    tiled, not altered."""
    rel = rels(z, part)
    out = []
    root = ET.fromstring(z.read(part))
    parent = {c: p for p in root.iter() for c in p}
    for el in root.iter():
        if not el.tag.endswith("}blipFill"):
            continue
        blip = el.find(f"{{{A_NS}}}blip")
        rid = blip.get(f"{{{R_NS}}}embed") if blip is not None else None
        if rid not in rel or rel[rid][0] != "image" or el.find(f"{{{A_NS}}}stretch") is None:
            continue
        kids = list(blip)
        exts = [e.get("uri") for x in kids if x.tag == f"{{{A_NS}}}extLst" for e in x]
        if any(x.tag != f"{{{A_NS}}}extLst" for x in kids) or not set(exts) <= PLAIN_EXT:
            continue
        src = el.find(f"{{{A_NS}}}srcRect")
        crop = tuple(int(src.get(k, 0)) / 1e5 for k in "ltrb") if src is not None else (0, 0, 0, 0)
        if min(crop) < -0.005:
            continue          # the picture set inside a margin of its own: PowerPoint's print is kept
        # a crop a hair below zero (-0.05 %, under a pixel) crops nothing
        out.append((rel[rid][1], tuple(max(0.0, c) for c in crop), frame_centre(el, parent)))
    return out


class Natives:
    """His pictures from the .pptx, opened when a page needs one: a small
    signature of each crop for matching, the full picture when it is used."""

    OPEN = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".gif", ".bmp")

    def __init__(self, z):
        self.z = z
        self.sigs = {}

    def open(self, part):
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(io.BytesIO(self.z.read(part)))
        im.seek(0)
        im.load()
        if im.mode not in ("RGB", "RGBA"):
            alpha = im.mode in ("LA", "PA", "RGBa") or "transparency" in im.info
            im = im.convert("RGBA" if alpha else "RGB")
        return im

    @staticmethod
    def box(size, crop):
        W, H = size
        left, top, right, bottom = crop
        return (round(left * W), round(top * H), W - round(right * W), H - round(bottom * H))

    def signature(self, part, crop):
        """(cropped width, height, has alpha, 32 x 32 RGB over white, 32 x 32 alpha)."""
        key = (part, crop)
        if key not in self.sigs:
            self.sigs[key] = None
            if part.lower().endswith(self.OPEN) and min(crop) >= 0 and crop[0] + crop[2] < 1 and crop[1] + crop[3] < 1:
                try:
                    im = self.open(part)
                except Exception:  # noqa: BLE001 - a picture PIL cannot read is matched by nothing
                    im = None
                if im is not None:
                    im = im.crop(self.box(im.size, crop))
                    self.sigs[key] = (im.width, im.height, im.mode == "RGBA", *thumb(im))
                    del im
        return self.sigs[key]

    def picture(self, part, box):
        """His picture `part`, cut to the pixel box (x0, y0, x1, y1)."""
        return self.open(part).crop(box)

    def difference(self, part, crop, im, mask):
        """(mean difference 0 to 255, pixel box): his picture cut as `crop`
        says, against PowerPoint's print `im` of it, both over white (and his
        alpha against `mask`, if any), at full size, where two plots alike at
        a glance differ in every number. Where the print keeps his pixels one
        for one, the cut is also tried a pixel either way, as PowerPoint may
        round a crop the other way; the box that fits is the one used."""
        import numpy as np
        from PIL import Image
        full = self.open(part)
        W, H = full.size
        w, h = im.size
        base = self.box(full.size, crop)
        if abs(base[2] - base[0] - w) <= 2 and abs(base[3] - base[1] - h) <= 2:
            boxes = [(x, y, x + w, y + h) for x in range(base[0] - 1, base[0] + 2)
                     for y in range(base[1] - 1, base[1] + 2) if x >= 0 and y >= 0 and x + w <= W and y + h <= H]
        else:
            boxes = []
        boxes = boxes or [base]
        from scipy.ndimage import gaussian_filter
        white = Image.new("RGB", im.size, (255, 255, 255))
        theirs = Image.composite(im.convert("RGB"), white, mask) if mask is not None else im.convert("RGB")
        blur = (1.0, 1.0, 0)
        b = gaussian_filter(np.asarray(theirs, np.float32), blur)
        m = gaussian_filter(np.asarray(mask, np.float32), 1.0) if mask is not None else None
        best = None
        for box in boxes:
            mine = full.crop(box)
            alpha = mine.getchannel("A") if mine.mode == "RGBA" else None
            mine = mine.convert("RGB")
            if mine.size != im.size:
                mine = mine.resize(im.size, Image.LANCZOS)
                alpha = alpha.resize(im.size, Image.LANCZOS) if alpha is not None else None
            a = Image.composite(mine, white, alpha) if alpha is not None else mine
            d = float(np.abs(gaussian_filter(np.asarray(a, np.float32), blur) - b).mean())
            if m is not None:
                d = max(d, float(np.abs(gaussian_filter(np.asarray(alpha, np.float32), 1.0) - m).mean()))
            if best is None or d < best[0]:
                best = (d, box)
        return best


def thumb(im, mask=None):
    """32 x 32 RGB over white and 32 x 32 alpha (numpy, float) of a picture,
    its alpha its own or `mask`."""
    import numpy as np
    from PIL import Image
    if mask is None and im.mode == "RGBA":
        mask = im.getchannel("A")
    rgb = im.convert("RGB")
    if mask is not None:
        white = Image.new("RGB", rgb.size, (255, 255, 255))
        rgb = Image.composite(rgb, white, mask.resize(rgb.size, Image.BILINEAR))
    t = np.asarray(rgb.resize((32, 32), Image.BOX), dtype=np.float32)
    a = np.asarray((mask if mask is not None else Image.new("L", im.size, 255)).resize((32, 32), Image.BOX),
                   dtype=np.float32)
    return t, a


def decode(href):
    from PIL import Image
    head, _, data = href.partition(",")
    im = Image.open(io.BytesIO(base64.b64decode(data)))
    im.load()
    return im


def encode(im, salt=0):
    """A picture as a short data URI, without metadata: a drawing (a plot, a
    diagram, a screenshot: lossless costs at most LOSSLESS_UNDER times a WebP
    at DRAWING_Q) as lossless WebP, anything else (a photograph) as WebP at
    LOSSY_Q; a mask as lossless WebP or PNG, whichever is shorter. `salt`
    nudges the encoder when the text of a URI happens to spell what the site's
    privacy check refuses (build.py's PRIVATE). Returns (URI, kind)."""
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB")
    if im.mode == "RGBA" and im.getchannel("A").getextrema() == (255, 255):
        im = im.convert("RGB")
    im.info.clear()
    outs = []
    buf = io.BytesIO()
    im.save(buf, "WEBP", lossless=True, quality=80 - salt, method=4, exact=False)
    outs.append(("image/webp", buf.getvalue(), "lossless"))
    if im.mode == "L":
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=salt == 0, compress_level=9 - min(salt, 8))
        outs.append(("image/png", buf.getvalue(), "lossless"))
        best = min(outs, key=lambda o: len(o[1]))
    else:
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=DRAWING_Q, method=4, alpha_quality=100)
        if len(outs[0][1]) <= LOSSLESS_UNDER * len(buf.getvalue()):
            best = outs[0]
        else:
            buf = io.BytesIO()
            im.save(buf, "WEBP", quality=LOSSY_Q - salt, method=4, alpha_quality=100)
            best = ("image/webp", buf.getvalue(), "lossy")
    return f"data:{best[0]};base64," + base64.b64encode(best[1]).decode("ascii"), best[2]


class Pictures:
    """Every picture of the deck, re-encoded once however many slides show it."""

    def __init__(self, natives):
        self.natives = natives
        self.cache = {}           # (key, salt) -> (data URI, kind)
        self.salt = {}            # key -> the salt its URI needs
        self.key_of = {}          # data URI -> key
        self.diffs = {}           # (sha1 of the PDF's picture, part, crop) -> (difference, pixel box) or None
        self.log = []             # (slide, PDF size, part, crop, difference) of each picture put back
        self.kept = []            # (slide, size, mode, masked, pixels shown) of each kept as printed
        self.tried = []           # (slide, centre, [(difference, his picture)], the one taken)
        self.stats = {"native": 0, "native_larger": 0, "kept": 0, "masks": 0}

    def uri(self, key, make):
        k = (key, self.salt.get(key, 0))
        if k not in self.cache:
            self.cache[k] = encode(make(), k[1])
            self.key_of[self.cache[k][0]] = key
        return self.cache[k][0]

    def match(self, im, mask, cands):
        """[(difference at full size, part, crop, pixel box)] of each picture
        of his that `im` (with `mask`) may be PowerPoint's print of, nearest
        first: alike at 32 x 32, then compared at full size."""
        import numpy as np
        w, h = im.size
        t, a = thumb(im, mask)
        close = []
        for part, crop in dict.fromkeys((c[0], c[1]) for c in cands):
            sig = self.natives.signature(part, crop)
            if sig is None:
                continue
            W, H, alpha, nt, na = sig
            if abs(W / H - w / h) > 0.015 * (w / h) or W < w - 2 or H < h - 2:
                continue
            if mask is not None and not alpha:
                continue          # a mask his picture does not carry: an effect of PowerPoint's
            d = float(np.abs(nt - t).mean())
            if mask is not None:
                d = max(d, float(np.abs(na - a).mean()))
            elif alpha and float(na.min()) < 250:
                continue          # his picture is see-through where PowerPoint's print is not
            if d < MATCH:
                close.append((d, part, crop))
        out = []
        for d, part, crop in sorted(close):
            full, box = self.natives.difference(part, crop, im, mask)
            out.append((round(full, 2), part, crop, box))
        return sorted(out)

    @staticmethod
    def choose(found, cands, centre):
        """The one of `found` that is his picture: in the place the slide puts
        it (its frame's centre within PLACE pt of the print's), nearer than
        MATCH_FULL, and clearly nearer than any other in that place, unless
        the two are the same picture. Returns (part, pixel box, difference)
        or None."""
        placed = []
        for full, part, crop, box in found:
            where = [c[2] for c in cands if c[0] == part and c[1] == crop]
            if any(c is None or (abs(c[0] - centre[0]) <= PLACE and abs(c[1] - centre[1]) <= PLACE)
                   for c in where):
                placed.append((full, part, box))
        if not placed or placed[0][0] >= MATCH_FULL:
            return None
        if len(placed) > 1 and placed[1][0] < 2 * placed[0][0] + 1.0 and placed[1][0] >= 0.5:
            return None
        return placed[0][1], placed[0][2], placed[0][0]


def _affine(t):
    """A transform attribute as [a, b, c, d, e, f]; MuPDF writes matrix() only."""
    m = vector._matrix(t) if t else None
    return m or [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]


def _then(m, n):
    """The affine map m after n (n applied first)."""
    return [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1],
            m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
            m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]]


def shown_px(el, parent, w, h):
    """The pixels a picture w x h drawn by `el` covers when its page is drawn
    SHOWN_W wide: (across, down)."""
    m = _affine(el.get("transform"))
    p = parent.get(el)
    while p is not None:
        m = _then(_affine(p.get("transform")), m)
        p = parent.get(p)
    s = SHOWN_W / 960.0
    return w * (m[0] ** 2 + m[1] ** 2) ** .5 * s, h * (m[2] ** 2 + m[3] ** 2) ** .5 * s


def centre_pt(el, parent, w, h):
    """Where, in pt on the page, the centre of a picture w x h drawn by `el` falls."""
    m = _affine(el.get("transform"))
    p = parent.get(el)
    while p is not None:
        m = _then(_affine(p.get("transform")), m)
        p = parent.get(p)
    return (m[0] * w / 2 + m[2] * h / 2 + m[4], m[1] * w / 2 + m[3] * h / 2 + m[5])


def fitted(im, need):
    """`im` brought down (never up) to the pixels it can show, `need`, when
    it holds more than MORE_THAN times them."""
    from PIL import Image
    f = max(need[0] / im.width, need[1] / im.height)
    if f * MORE_THAN >= 1:
        return im
    return im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)


def quadratics(d):
    """Path data with every cubic that is exactly a quadratic written as the
    quadratic. His fonts are TrueType, whose curves are quadratics; PDF can
    only write cubics, so PowerPoint's PDF holds each as a cubic with its
    control points two thirds of the way to the quadratic's. The shape is the
    same to the last digit MuPDF writes (eight)."""
    try:
        segs = vector.parse_path(d)
    except ValueError:
        return d
    out, n = [], 0
    px = py = sx = sy = 0.0
    for c, pts in segs:
        if c == "C":
            c1x, c1y, c2x, c2y, x, y = pts
            q1x, q1y = 1.5 * c1x - 0.5 * px, 1.5 * c1y - 0.5 * py
            q2x, q2y = 1.5 * c2x - 0.5 * x, 1.5 * c2y - 0.5 * y
            tol = 2e-6 * max(1.0, abs(px), abs(py), abs(x), abs(y))
            if abs(q1x - q2x) <= tol and abs(q1y - q2y) <= tol:
                out.append(("Q", [(q1x + q2x) / 2, (q1y + q2y) / 2, x, y]))
                n += 1
                px, py = x, y
                continue
        out.append((c, pts))
        if c == "Z":
            px, py = sx, sy
        else:
            px, py = pts[-2], pts[-1]
            if c == "M":
                sx, sy = px, py
    return vector.encode_path(out, 7) if n else d


def smooth(d):
    """Written path data with every quadratic whose control point is the
    mirror of the one before (TrueType's implied points) as a T: exact, the
    mirror is computed from the same rounded numbers."""
    if "Q" not in d and "q" not in d:
        return d
    try:
        segs = vector.parse_path(d)
    except ValueError:
        return d
    nd = max((len(t) - t.index(".") - 1 for t in re.findall(r"\d*\.\d+", d)), default=0)
    out, prev, n = [], None, 0
    px = py = sx = sy = 0.0
    for c, pts in segs:
        if c == "Q" and prev is not None:
            rx, ry = round(2 * px - prev[0], nd), round(2 * py - prev[1], nd)
            if rx == round(pts[0], nd) and ry == round(pts[1], nd):
                out.append(("T", pts[2:]))
                n += 1
                prev, (px, py) = pts[:2], pts[2:]
                continue
        out.append((c, pts))
        prev = pts[:2] if c == "Q" else None
        if c == "Z":
            px, py = sx, sy
        else:
            px, py = pts[-2], pts[-1]
            if c == "M":
                sx, sy = px, py
    return vector.encode_path(out, nd) if n else d


def tighten(svg):
    """vector.minify's SVG written shorter still, the picture the same: its
    quadratics smooth where they can be (smooth()), and each run of glyphs on
    one baseline with that baseline in its group's transform, so each glyph
    keeps only x."""
    root = ET.fromstring(svg)
    for el in root.iter():
        if el.get("d"):
            el.set("d", smooth(el.get("d")))
    for g in list(root.iter(_q("g"))):
        kids = list(g)
        m = vector._matrix(g.get("transform"))
        if (not kids or m is None or m[4] or m[5]
                or any(u.tag != _q("use") or u.get("y") is None for u in kids)):
            continue
        ys = {u.get("y") for u in kids}
        if len(ys) == 1:
            y = float(ys.pop())
            g.set("transform", vector._mat(m[:4] + [m[2] * y, m[3] * y], 3))
            for u in kids:
                del u.attrib["y"]
            continue
        # several baselines: a run of four or more glyphs on one gets a
        # group of its own that carries it
        out, i = [], 0
        while i < len(kids):
            j = i
            while j < len(kids) and kids[j].get("y") == kids[i].get("y"):
                j += 1
            if j - i >= 4:
                sub = ET.Element(_q("g"), {"transform": f"translate(0 {kids[i].get('y')})"})
                for u in kids[i:j]:
                    del u.attrib["y"]
                    sub.append(u)
                out.append(sub)
            else:
                out.extend(kids[i:j])
            i = j
        g[:] = out
    return ET.tostring(root, encoding="unicode").replace(" />", "/>")


def page_svg(page, cands, pics, k):
    """One page of the PDF as a standalone SVG, his pictures at native size.

    MuPDF writes a picture once and draws its later occurrences on the page
    as <use> of that first <image>, which may sit inside a mask. Here every
    picture is first moved into <defs> and each occurrence made a <use>, so a
    mask that goes (its picture replaced by his own, alpha and all) takes no
    picture another occurrence still needs."""
    from PIL import Image
    svg = page.get_svg_image(text_as_path=True)
    root = ET.fromstring(svg)
    del svg
    for el in root.iter():
        if el.get("d"):
            el.set("d", quadratics(el.get("d")))
    defs = root.find(_q("defs"))
    if defs is None:
        defs = ET.Element(_q("defs"))
        root.insert(0, defs)
    parent = {c: p for p in root.iter() for c in p}
    images = {}
    for img in list(root.iter(_q("image"))):
        iid = img.get("id") or f"pic{len(images)}"
        img.set("id", iid)
        images[iid] = img
        p = parent[img]
        if p is not defs:
            p[list(p).index(img)] = ET.Element(_q("use"), {HREF: "#" + iid})
            defs.append(img)
    parent = {c: p for p in root.iter() for c in p}
    masks = {m.get("id"): m for m in root.iter(_q("mask"))}

    def target(u):
        h = u.get(HREF) or u.get("href") or ""
        return h[1:] if h.startswith("#") and h[1:] in images else None

    def inside_mask(el):
        while el is not None:
            if el.tag == _q("mask"):
                return True
            el = parent.get(el)
        return False

    def masked_by(el):
        while el is not None:
            v = el.get("mask")
            if v and v.startswith("url(#"):
                return el, masks.get(v[5:-1])
            el = parent.get(el)
        return None, None

    def drawn(el):
        return [e for e in el.iter() if e.tag in (_q("path"), _q("use"), _q("image"), _q("rect"))]

    # every drawing of a picture: the picture, its mask's picture if it is
    # PowerPoint's print of an alpha (a mask of one picture, placed as the
    # picture is, over a group that draws only it), and where it is drawn
    seen = []
    for u in root.iter(_q("use")):
        iid = target(u)
        if iid is None or inside_mask(u):
            continue
        holder, mask_el = masked_by(u)
        mid = None
        if mask_el is not None:
            inner = drawn(mask_el)
            if (len(inner) == 1 and inner[0].tag == _q("use") and target(inner[0])
                    and drawn(holder) == [u]
                    and parent[inner[0]].get("transform") == parent[u].get("transform")):
                mid = target(inner[0])
        w, h = float(images[iid].get("width", 0)), float(images[iid].get("height", 0))
        seen.append((u, iid, holder, mask_el, mid, shown_px(u, parent, w, h), centre_pt(u, parent, w, h)))

    def href(iid):
        return images[iid].get(HREF) or ""

    # what each drawing is: his picture (part, pixel box) or PowerPoint's print
    verdict = {}
    for u, iid, holder, mask_el, mid, need, centre in seen:
        if mask_el is not None and mid is None:
            verdict.setdefault(iid, set()).add(None)       # PowerPoint's composition: kept as printed
            continue
        digest = hashlib.sha1((href(iid) + (href(mid) if mid else "")).encode()).hexdigest()
        todo = [(c[0], c[1]) for c in cands if (digest, c[0], c[1]) not in pics.diffs]
        if todo:
            im = decode(href(iid))
            mask = decode(href(mid)).convert("L") if mid else None
            if mask is not None and mask.size != im.size:
                mask = mask.resize(im.size, Image.BILINEAR)
            found = pics.match(im, mask, [(a, b, None) for a, b in dict.fromkeys(todo)])
            for a, b in todo:
                pics.diffs[(digest, a, b)] = None
            for full, a, b, box in found:
                pics.diffs[(digest, a, b)] = (full, box)
            del im, mask
        found = sorted((pics.diffs[(digest, c[0], c[1])][0], c[0], c[1], pics.diffs[(digest, c[0], c[1])][1])
                       for c in dict.fromkeys((c[0], c[1]) for c in cands) if pics.diffs[(digest, c[0], c[1])])
        choice = Pictures.choose(found, cands, centre)
        if found:
            pics.tried.append((k, [round(v, 1) for v in centre], [(f, a.rsplit("/", 1)[-1]) for f, a, _, _ in found[:3]],
                               choice and choice[2]))
        verdict.setdefault(iid, set()).add(choice and choice[:2])
    # a picture is replaced only when every drawing of it is the same picture of his
    native = {iid: next(iter(v)) for iid, v in verdict.items() if len(v) == 1 and None not in v}
    needs = {}
    for u, iid, holder, mask_el, mid, need, centre in seen:
        needs[iid] = (max(needs.get(iid, (0, 0))[0], need[0]), max(needs.get(iid, (0, 0))[1], need[1]))
        if mid:
            needs[mid] = (max(needs.get(mid, (0, 0))[0], need[0]), max(needs.get(mid, (0, 0))[1], need[1]))
        if iid in native and mask_el is not None:
            del holder.attrib["mask"]           # his own alpha stands for PowerPoint's mask
    # the masks no drawing uses any more go, then the pictures nothing draws
    live = {el.get("mask")[5:-1] for el in root.iter() if (el.get("mask") or "").startswith("url(#")}
    for m in list(defs):
        if m.tag == _q("mask") and m.get("id") not in live:
            defs.remove(m)
    used = {target(u) for u in root.iter(_q("use"))} - {None}
    for iid in list(images):
        if iid not in used:
            defs.remove(images.pop(iid))
    # every picture left, re-encoded at the pixels it can show
    for iid, img in images.items():
        need = needs.get(iid)
        if iid in native:
            part, box = native[iid]
            size0 = (box[2] - box[0], box[3] - box[1])
            size = fitted_size(size0, need)
            pics.stats["native"] += 1
            pics.stats["native_larger"] += size0[0] > float(img.get("width", 0)) + 2
            pics.log.append((k, (img.get("width"), img.get("height")), part, box, size0, size))
            new = pics.uri(("native", part, box, size), lambda: fitted(pics.natives.picture(part, box), need))
        else:
            data = href(iid)
            digest = hashlib.sha1(data.encode()).hexdigest()
            im = decode(data)
            is_mask = all(inside_mask(u) for u in root.iter(_q("use")) if target(u) == iid)
            if is_mask:
                im = im.convert("L")
                pics.stats["masks"] += 1
            else:
                pics.stats["kept"] += 1
                pics.kept.append((k, im.size, im.mode, need and (round(need[0]), round(need[1]))))
            size = fitted_size(im.size, need) if need else im.size
            new = pics.uri(("pdf", digest, size), lambda: fitted(im, need) if need else im)
            del im
        img.set(HREF, new)
        if tuple(size) != (round(float(img.get("width", 0))), round(float(img.get("height", 0)))):
            img.set("preserveAspectRatio", "none")     # the box is the picture's, whatever its pixels
    text = ET.tostring(root, encoding="unicode")
    del root
    return tighten(vector.minify(text))


def fitted_size(size, need):
    """The pixel size fitted() gives a picture of `size`."""
    f = max(need[0] / size[0], need[1] / size[1])
    return tuple(size) if f * MORE_THAN >= 1 else (max(1, round(size[0] * f)), max(1, round(size[1] * f)))


def private_hits(text):
    """What build.py's private_report() would find in a published file."""
    return [m.group() for m in PRIVATE.finditer(text)] + \
        [a for a in set(EMAIL.findall(text)) if a != ADDRESS]


def uri_at(text, pos):
    """The data URI that holds position `pos` of an SVG's text, or None."""
    start = text.rfind('"data:', 0, pos)
    end = text.find('"', start + 1) if start >= 0 else -1
    return text[start + 1:end] if start >= 0 and start < pos < end else None


def make_svgs(work, only=None):
    """Every page (or `only`) as WORK/svg/sNNN.svg."""
    import fitz
    out = os.path.join(work, "svg")
    os.makedirs(out, exist_ok=True)
    z = zipfile.ZipFile(os.path.join(work, "phd.pptx"))
    parts = slide_parts(z)
    pics = Pictures(Natives(z))
    doc = fitz.open(os.path.join(work, "phd.pdf"))
    t0 = time.time()
    sizes = {}
    for k in only or range(1, COUNT + 1):
        slide, layout, master = parts[k - 1]
        cands = list(dict.fromkeys(fills(z, slide) + fills(z, layout) + fills(z, master)))
        for _ in range(8):
            text = page_svg(doc[k - 1], cands, pics, k)
            hits = [m for m in PRIVATE.finditer(text)]
            if not private_hits(text):
                break
            # a picture's data happens to spell what the site refuses: that
            # picture is encoded again, a notch differently
            for m in hits:
                uri = uri_at(text, m.start())
                if uri is None or uri not in pics.key_of:
                    raise SystemExit(f"s{k:03d}: {m.group()!r} outside any picture's data")
                key = pics.key_of[uri]
                pics.salt[key] = pics.salt.get(key, 0) + 1
            print(f"  s{k:03d}: a picture's data spelled {[m.group() for m in hits]}; encoded again")
        else:
            raise SystemExit(f"s{k:03d}: cannot write it without {private_hits(text)}")
        with open(os.path.join(out, f"s{k:03d}.svg"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        sizes[k] = len(text.encode())
        del text
        if k % 10 == 0:
            gc.collect()
            print(f"  svg: s{k:03d} ({time.time() - t0:.0f} s, {sum(sizes.values()) / 1e6:.1f} MB so far)")
    doc.close()
    z.close()
    kinds = {}
    for (uri, kind) in pics.cache.values():
        kinds[kind] = kinds.get(kind, 0) + 1
    with open(os.path.join(work, "pictures.json"), "w", encoding="utf-8") as fh:
        json.dump({"put_back": pics.log, "kept": pics.kept, "tried": pics.tried}, fh)
    print(f"svg: {len(sizes)} pages, {sum(sizes.values()) / 1e6:.2f} MB (largest s{max(sizes, key=sizes.get):03d} "
          f"{max(sizes.values()) / 1e6:.2f} MB); pictures: {pics.stats['native']} put back from the .pptx "
          f"({pics.stats['native_larger']} larger than PowerPoint printed them), {pics.stats['kept']} kept "
          f"from the PDF, {pics.stats['masks']} masks; encodings {kinds}")
    return sizes


# ------------------------------------------------------------------ check
VIEW = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>SVG</title>
<style>html,body{margin:0;background:#fff}img{display:block;width:1600px;height:900px}</style>
</head><body><img alt=""><script>document.querySelector('img').src=location.search.slice(1)</script>
</body></html>
"""


def ssim(a, b):
    """Mean SSIM of two grey pictures (float 0 to 255): Gaussian window,
    sigma 1.5, the usual constants."""
    from scipy.ndimage import gaussian_filter
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = gaussian_filter(a, 1.5), gaussian_filter(b, 1.5)
    saa = gaussian_filter(a * a, 1.5) - mu_a ** 2
    sbb = gaussian_filter(b * b, 1.5) - mu_b ** 2
    sab = gaussian_filter(a * b, 1.5) - mu_a * mu_b
    m = ((2 * mu_a * mu_b + c1) * (2 * sab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (saa + sbb + c2))
    return float(m.mean())


def compare(drawn, ref):
    """(mean absolute difference 0 to 255 over RGB, SSIM of the grey, and the
    largest difference once both are blurred by a Gaussian of 2.5 px with
    where it is) of two same-size RGB pictures. Antialiasing, hinting and the
    phase of a dash leave the blurred pictures alike; a mark that is missing,
    moved or changed does not."""
    import numpy as np
    from scipy.ndimage import gaussian_filter
    a = np.asarray(drawn, dtype=np.float32)
    b = np.asarray(ref, dtype=np.float32)
    mad = float(np.abs(a - b).mean())
    ga = np.asarray(drawn.convert("L"), dtype=np.float32)
    gb = np.asarray(ref.convert("L"), dtype=np.float32)
    s = ssim(ga, gb)
    d = np.abs(gaussian_filter(ga, 2.5) - gaussian_filter(gb, 2.5))
    y, x = np.unravel_index(int(d.argmax()), d.shape)
    return round(mad, 3), round(s, 4), round(float(d.max()), 1), (int(x), int(y))


def check(work, only=None):
    """Chromium draws each SVG in an <img> at 1600 x 900, as the viewer does.
    Each is held against the published pictures (sNNN-1600.webp, sNNN.png),
    and against its own page of the PDF as MuPDF draws it: the SVG is that
    page, so there only antialiasing and the pictures' resampling may differ,
    and a mark lost or changed on the way shows. Returns the report."""
    import fitz
    from PIL import Image
    from playwright.sync_api import sync_playwright
    doc = fitz.open(os.path.join(work, "phd.pdf"))
    svgdir = os.path.join(work, "svg")
    drawn_dir = os.path.join(work, "drawn")
    os.makedirs(drawn_dir, exist_ok=True)
    with open(os.path.join(svgdir, "view.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(VIEW)
    base = "file:///" + svgdir.replace(os.sep, "/")
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--disable-lcd-text", "--font-render-hinting=none"])
        pg = b.new_page(viewport={"width": 1600, "height": 900}, device_scale_factor=1)
        for k in only or range(1, COUNT + 1):
            pg.goto(f"{base}/view.html?s{k:03d}.svg")
            pg.wait_for_function("document.images[0].complete && document.images[0].naturalWidth > 0",
                                 timeout=60000)
            drawn = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
            drawn.save(os.path.join(drawn_dir, f"s{k:03d}.png"))
            with Image.open(os.path.join(WEB, f"s{k:03d}-1600.webp")) as im:
                webp = im.convert("RGB")
            with Image.open(os.path.join(DECK, f"s{k:03d}.png")) as im:
                png = im.convert("RGB")
            pix = doc[k - 1].get_pixmap(matrix=fitz.Matrix(1600 / 960, 1600 / 960), alpha=False)
            page = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            m1, s1, w1, at1 = compare(drawn, webp)
            m2, s2, w2, at2 = compare(drawn, png)
            m3, s3, w3, at3 = compare(drawn, page)
            report[k] = {"webp": {"mad": m1, "ssim": s1, "local": w1, "at": at1},
                         "png": {"mad": m2, "ssim": s2, "local": w2, "at": at2},
                         "pdf": {"mad": m3, "ssim": s3, "local": w3, "at": at3},
                         "bytes": os.path.getsize(os.path.join(svgdir, f"s{k:03d}.svg"))}
            del pix, page
            if k % 20 == 0:
                print(f"  check: s{k:03d}")
        b.close()
    doc.close()
    return report


def review(work, ks, report):
    """What to look at, into WORK/review/: for each slide in `ks` the spot
    where it differs most from its published picture (published left, the
    SVG as drawn right, twice the size), eight to a sheet; and each whole
    slide as the published picture over the SVG as drawn over their
    difference (times four)."""
    from PIL import Image, ImageChops, ImageDraw
    out = os.path.join(work, "review")
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith("spots-"):
            os.remove(os.path.join(out, f))
    tiles = []
    for k in ks:
        with Image.open(os.path.join(DECK, f"s{k:03d}.png")) as im:
            pub = im.convert("RGB")
        drawn = Image.open(os.path.join(work, "drawn", f"s{k:03d}.png")).convert("RGB")
        diff = ImageChops.difference(pub, drawn).point(lambda v: min(255, v * 4))
        sheet = Image.new("RGB", (1600, 2700), "white")
        sheet.paste(pub, (0, 0))
        sheet.paste(drawn, (0, 900))
        sheet.paste(ImageChops.invert(diff), (0, 1800))
        sheet.resize((1066, 1800), Image.LANCZOS).save(os.path.join(out, f"s{k:03d}.png"))
        x, y = report[str(k)]["png"]["at"] if str(k) in report else report[k]["png"]["at"]
        x0, y0 = max(0, min(1600 - 240, x - 120)), max(0, min(900 - 130, y - 65))
        box = (x0, y0, x0 + 240, y0 + 130)
        t = Image.new("RGB", (970, 280), "white")
        t.paste(pub.crop(box).resize((480, 260), Image.LANCZOS), (0, 20))
        t.paste(drawn.crop(box).resize((480, 260), Image.LANCZOS), (490, 20))
        v = report[str(k)] if str(k) in report else report[k]
        ImageDraw.Draw(t).text((4, 4), f"s{k:03d} at ({x}, {y}): published | SVG as drawn   "
                               f"local {v['png']['local']}  SSIM {v['webp']['ssim']}", fill=(200, 0, 0))
        tiles.append(t)
    for i in range(0, len(tiles), 8):
        part = tiles[i:i + 8]
        sheet = Image.new("RGB", (970, 280 * len(part)), "white")
        for j, t in enumerate(part):
            sheet.paste(t, (0, 280 * j))
        sheet.save(os.path.join(out, f"spots-{i // 8 + 1}.png"))


# ------------------------------------------------------------------ privacy
def privacy(work, only=None):
    """[(where, what)] the site must not carry: in the PDF's text layer (what
    the SVGs draw) and in the SVGs themselves."""
    import fitz
    found = []
    with fitz.open(os.path.join(work, "phd.pdf")) as doc:
        for k, p in enumerate(doc, 1):
            t = p.get_text()
            found += [(f"pdf page {k}", a) for a in EMAIL.findall(t) if a != ADDRESS]
            found += [(f"pdf page {k}", "@ outside the address") for _ in range(t.count("@") - t.count(ADDRESS))]
            if ADDRESS in t and k not in (1, 56):
                found.append((f"pdf page {k}", "the address where no slide has it"))
            found += [(f"pdf page {k}", m.group()) for m in PRIVATE.finditer(t)]
            found += [(f"pdf page {k}", m.group()) for m in HIS_PHONES.finditer(t)]
            found += [(f"pdf page {k}", m.group()) for m in DIGITS.finditer(t) if phone_like(m.group())]
            for link in p.get_links():
                if str(link.get("uri", "")).lower().startswith(("mailto:", "tel:")) and ADDRESS not in link["uri"]:
                    found.append((f"pdf page {k}", link["uri"]))
    for k in only or range(1, COUNT + 1):
        path = os.path.join(work, "svg", f"s{k:03d}.svg")
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        found += [(f"s{k:03d}.svg", h) for h in private_hits(text)]
        if "@" in text or "<text" in text or "data-text" in text:
            found.append((f"s{k:03d}.svg", "text in the SVG"))
        if re.search(r'(?:href|src)="(?!#|data:)', text):
            found.append((f"s{k:03d}.svg", "a reference to another file"))
        for uri in re.findall(r'href="(data:[^"]+)"', text):
            if carries_metadata(base64.b64decode(uri.partition(",")[2])):
                found.append((f"s{k:03d}.svg", "a picture with camera metadata"))
    return found


def carries_metadata(data):
    """An EXIF or XMP chunk in a WebP, an Exif or XMP segment in a JPEG, an
    eXIf, tEXt, zTXt or iTXt chunk in a PNG (site/build.py's rule, on bytes)."""
    import struct
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        i = 12
        while i + 8 <= len(data):
            tag, size = data[i:i + 4], struct.unpack("<I", data[i + 4:i + 8])[0]
            if tag in (b"EXIF", b"XMP "):
                return True
            i += 8 + size + (size & 1)
        return False
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF:
            marker, size = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if marker == 0xDA:
                return False
            body = data[i + 4:i + 2 + size]
            if marker == 0xE1 and (body.startswith(b"Exif\x00") or b"ns.adobe.com/xap" in body[:64]):
                return True
            i += 2 + size
        return False
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        i = 8
        while i + 8 <= len(data):
            size, tag = struct.unpack(">I", data[i:i + 4])[0], data[i + 4:i + 8]
            if tag in (b"eXIf", b"tEXt", b"zTXt", b"iTXt"):
                return True
            i += 12 + size
        return False
    return False


# ------------------------------------------------------------------ main
def slides(spec):
    out = []
    for part in spec or ():
        if part == "all":
            return None
        a, _, b = part.partition("-")
        out += range(int(a), int(b or a) + 1)
    return sorted(set(out)) or None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", nargs="?", default="all",
                    choices=("all", "copy", "pdf", "order", "svg", "check", "privacy", "write"))
    ap.add_argument("slides", nargs="*", help="numbers or ranges for svg and check: 5, 1-8")
    ap.add_argument("--work", default=WORK, help="the scratch folder (default build/r12-phddeck/work)")
    ap.add_argument("--look", action="store_true", help="every step but write")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    work = os.path.abspath(a.work)
    if os.path.commonpath([work, DECK]) == DECK:
        raise SystemExit("the work folder may not be inside content/deck-phd/")
    os.makedirs(work, exist_ok=True)
    only = slides(a.slides)
    steps = ("copy", "pdf", "order", "svg", "check", "privacy", "write") if a.step == "all" else (a.step,)
    report = {}
    rpath = os.path.join(work, "report.json")
    if os.path.isfile(rpath):
        with open(rpath, encoding="utf-8") as fh:
            report = json.load(fh)
    for step in steps:
        if step == "copy":
            copy_pptx(work)
        elif step == "pdf":
            print_pdf(work)
        elif step == "order":
            report["order"] = check_order(work)
        elif step == "svg":
            report["svg_bytes"] = {**report.get("svg_bytes", {}),
                                   **{str(k): v for k, v in make_svgs(work, only).items()}}
        elif step == "check":
            res = check(work, only)
            report["check"] = {**report.get("check", {}), **{str(k): v for k, v in res.items()}}
            summarise(work, report["check"])
        elif step == "privacy":
            leaks = privacy(work, only)
            report["privacy"] = leaks
            print(f"privacy: {len(leaks)} findings" + "".join(f"\n      - {w}: {x}" for w, x in leaks))
        elif step == "write":
            if a.look:
                print("write: --look, nothing written")
                continue
            if not write(work, report):
                return 1
        with open(rpath, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=1)
    return 0


# The limits past which a slide's SVG is looked at against its published
# picture; and the one an SVG must keep against its own page of the PDF.
MAD_MAX = 4.0
SSIM_MIN = 0.93
LOCAL_MAX = 40
PDF_LOCAL_MAX = 60
# The slides over those limits, each looked at where it differs most, the
# published picture beside the SVG as drawn (review/spots-N.png), on 28 Sep
# 2026, and why they differ. None misses or changes a mark.
#   dashes: PowerPoint's 1600 pictures draw a dashed line from its width in
#     whole pixels (2.5 px taken as 2, so dashes 20 % short) and start the
#     dashes elsewhere; the PDF, and so the SVG, keeps PowerPoint's own
#     pattern (dash 4, gap 3 times the width for "dash").
#   text: GDI's hinted, gamma-weighted glyphs against the same glyphs as
#     outlines, antialiased; seen most in small serif text, large bold titles
#     and his equations (151: the same symbols, placed a pixel apart).
#   address: slides 1 and 56, where the pictures had the address painted over
#     (Calibri drawn by PIL) and the SVG has PowerPoint's own line, 1 to 2 px lower.
LOOKED = {k: "dashes" for k in (
    4, 5, 8, 9, 10, 11, 12, 13, 16, 20, 22, 23, 30, 35, 40, 41, 42, 45, 60, 62, 64, 65, 66, 68, 72,
    73, 78, 79, 80, 81, 82, 83, 84, 86, 87, 88, 89, 90, 92, 94, 97, 98, 99, 100, 103, 104, 112,
    113, 122, 124, 132, 137, 138)}
LOOKED.update({k: "text" for k in (
    2, 3, 18, 19, 21, 24, 25, 28, 31, 32, 33, 37, 38, 43, 47, 48, 49, 53, 55, 63, 67, 75, 76,
    106, 107, 108, 121, 130, 134, 136, 140, 142, 144, 147, 151, 154, 157, 159, 172, 177)})
LOOKED.update({1: "address", 56: "address"})


def flagged(rep):
    return sorted(int(k) for k, v in rep.items()
                  if v["webp"]["mad"] > MAD_MAX or v["webp"]["ssim"] < SSIM_MIN or v["png"]["local"] > LOCAL_MAX)


def summarise(work, rep):
    ks = sorted(rep, key=lambda k: -rep[k]["png"]["local"])
    n = len(rep)
    print(f"check: {n} SVGs as drawn at 1600 against sNNN-1600.webp (and sNNN.png): "
          f"mean MAD {sum(v['webp']['mad'] for v in rep.values()) / n:.2f}, "
          f"mean SSIM {sum(v['webp']['ssim'] for v in rep.values()) / n:.4f}, "
          f"lowest SSIM {min(v['webp']['ssim'] for v in rep.values()):.4f}")
    for k in ks[:15]:
        v = rep[k]
        print(f"  s{int(k):03d}: local {v['png']['local']:5.1f} at {tuple(v['png']['at'])} | "
              f"webp MAD {v['webp']['mad']:.2f} SSIM {v['webp']['ssim']:.4f} | "
              f"png MAD {v['png']['mad']:.2f} SSIM {v['png']['ssim']:.4f}")
    worst = max(rep, key=lambda k: rep[k]["pdf"]["local"])
    print(f"  against their own pages of the PDF: largest local difference {rep[worst]['pdf']['local']} "
          f"(s{int(worst):03d}; limit {PDF_LOCAL_MAX}), mean SSIM "
          f"{sum(v['pdf']['ssim'] for v in rep.values()) / n:.4f}")
    bad = flagged(rep)
    print(f"  to look at (MAD > {MAD_MAX}, SSIM < {SSIM_MIN}, local > {LOCAL_MAX}): {len(bad)} slides, "
          f"{len([k for k in bad if k not in LOOKED])} not looked at yet {[k for k in bad if k not in LOOKED]}")
    review(work, sorted(set(bad) | {1, 56}), rep)


def write(work, report):
    """The SVGs into content/deck-phd/web/, when every check holds."""
    probs = []
    rep = report.get("check", {})
    if sorted(int(k) for k in rep) != list(range(1, COUNT + 1)):
        probs.append("not every slide has been checked")
    if report.get("privacy"):
        probs.append(f"privacy: {report['privacy'][:5]}")
    sizes = [os.path.getsize(os.path.join(work, "svg", f"s{k:03d}.svg")) for k in range(1, COUNT + 1)]
    if max(sizes) > 3_000_000:
        probs.append(f"an SVG over the site's 3 MB a file: {max(sizes) / 1e6:.2f} MB")
    left = [k for k in flagged(rep) if k not in LOOKED]
    if left:
        probs.append(f"slides over the limits not yet looked at: {left}")
    lost = [int(k) for k, v in rep.items() if v["pdf"]["local"] > PDF_LOCAL_MAX]
    if lost:
        probs.append(f"SVGs that differ from their page of the PDF: {sorted(lost)}")
    if probs:
        for pr in probs:
            print("write: -", pr)
        print("write: nothing written")
        return False
    for k in range(1, COUNT + 1):
        shutil.copyfile(os.path.join(work, "svg", f"s{k:03d}.svg"), os.path.join(WEB, f"s{k:03d}.svg"))
    print(f"write: content/deck-phd/web/s001.svg to s{COUNT:03d}.svg, {sum(sizes) / 1e6:.2f} MB")
    return True


if __name__ == "__main__":
    sys.exit(main())
