"""The deck as vectors: one PDF of every slide, and each slide as an SVG.

render.py photographs each slide for the pictures the page shows. This
module prints the same slides for the reader who presents or downloads them:

    deck_html()   every slide on one page, one under the other. Each slide
                  sits in a wrapper of its own (#deck-sNNN) that scopes its
                  <style> (@scope), so one slide's layout never reaches
                  another's; deck.js draws each slide's wires in its own
                  corner.
    print_pdf()   Chromium prints that page, a 1920 x 1080 px page to a slide
                  (1440 x 810 pt): his words stay text, selectable and
                  searchable, the figures stay paths. One print job holds the
                  fonts once for the whole deck.
    tidy()        the path coordinates rounded to 0.01 px (the transforms and
                  the colours are left as Chromium wrote them), the deck's
                  title, author and one bookmark a slide (his titles), and
                  every object written once.
    page_svg()    one page as a standalone SVG (MuPDF, his text as outlines,
                  so it needs no font): what the viewer shows while
                  presenting, sharp at any size. Its path data is written
                  short (relative moves, 0.01 px), each glyph once, the
                  glyphs of a line in one group, the clips that clip nothing
                  left out.

render.py checks every page of the PDF, and every SVG as Chromium draws it,
against the slide's photograph before it writes them (render.py --vector).
"""

import math
import re
import xml.etree.ElementTree as ET

DECK_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Probability, statistics and estimation</title>
<link rel="stylesheet" href="/tools/deck/deck.css">
<style>
 /* every slide, one under the other, each a printed page of its own size */
 @page{size:1920px 1080px;margin:0}
 html,body{height:auto;overflow:visible}
 .slide{break-after:page}
</style>
</head>
<body>
%BODY%
<script src="/tools/deck/deck.js"></script>
</body>
</html>
"""

STYLE = re.compile(r"<style>(.*?)</style>", re.S)


def deck_html(sections):
    """The printer's page: [(stem, the slide's <section> markup)] one under
    the other, in the deck's order, each slide's own style scoped to its
    wrapper (#deck-s004, #deck-s065a)."""
    out = []
    for n, body in sections:
        scope = f"deck-{n}" if isinstance(n, str) else f"deck-s{n:03d}"
        body = STYLE.sub(lambda mo: f"<style>@scope (#{scope}){{{mo.group(1)}}}</style>", body)
        out.append(f'<div id="{scope}">{body}</div>')
    return DECK_SHELL.replace("%BODY%", "\n".join(out))


def print_pdf(page, path):
    """Print the open deck page to `path`, a 1920 x 1080 px page a slide."""
    page.emulate_media(media="screen")
    page.pdf(path=path, width="1920px", height="1080px", print_background=True,
             margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})


# ------------------------------------------------------------------ the PDF
# A content stream's tokens: strings, hex strings and comments are copied as
# they are; so are dictionaries and arrays, whose delimiters are tokens.
TOKEN = re.compile(rb"""
    (?P<str>\((?:\\.|[^\\()])*\))
  | (?P<dict><<|>>)
  | (?P<hex><[0-9A-Fa-f\s]*>)
  | (?P<com>%[^\r\n]*)
  | (?P<num>[+-]?(?:\d+\.\d*|\.\d+|\d+))(?![\w.])
  | (?P<op>[A-Za-z'"*][A-Za-z0-9*]*|[\[\]{}]|/[^\s/\[\]()<>{}%]*)
  | (?P<ws>\s+)
""", re.X | re.S)
# The operators whose operands are coordinates of a path (and the text's
# steps along a line): only these are rounded. A transform (cm, Tm) is left
# exact, since in the one long page a slide sits thousands of units down.
PATH_OPS = {b"m": 2, b"l": 2, b"c": 2, b"v": 2, b"y": 2, b"re": 2, b"Td": 3}


def _short(v, nd):
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s in ("", "-0", "-"):
        s = "0"
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s.encode()


def round_stream(data):
    """A content stream with the coordinates of its paths at 0.01 unit (the
    text's steps at 0.001), every other token as it was; one operator a line."""
    buf, pending = bytearray(), []

    def put(tok, end=False):
        if buf and buf[-1] != 10:
            buf.extend(b" ")
        buf.extend(tok)
        if end:
            buf.extend(b"\n")
    pos = 0
    for mo in TOKEN.finditer(data):
        if mo.start() != pos:            # a byte no rule knows: leave the stream alone
            return data
        pos = mo.end()
        kind, tok = mo.lastgroup, mo.group(0)
        if kind == "ws":
            continue
        if kind == "num":
            pending.append(tok)
            continue
        if kind == "op" and tok in PATH_OPS:
            nd = PATH_OPS[tok]
            pending = [_short(float(t), nd) if b"." in t else t for t in pending]
        for t in pending:
            put(t)
        pending = []
        put(tok, end=kind == "com" or (kind == "op" and tok[:1] not in b"/[]{}"))
    if pos != len(data):
        return data
    for t in pending:
        put(t)
    return bytes(buf)


def content_streams(doc):
    """The xrefs of every content stream: the pages', the form XObjects' and
    the glyph procedures of the Type 3 fonts Chromium writes its variable
    fonts as."""
    xs = set()
    for p in doc:
        xs.update(p.get_contents())
    for x in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(x, compressed=True).replace(" ", "")
        except Exception:  # noqa: BLE001 (a free slot in the table)
            continue
        if "/Subtype/Form" in obj and doc.xref_is_stream(x):
            xs.add(x)
        if "/Subtype/Type3" in obj:
            kind, val = doc.xref_get_key(x, "CharProcs")
            if kind == "xref":
                val = doc.xref_object(int(val.split()[0]), compressed=True)
            xs.update(int(r) for r in re.findall(r"(\d+) 0 R", val))
    return sorted(xs)


def tidy(src, dst, titles, title, author, labels=None):
    """The printed deck, made small and named: `titles` one bookmark a page,
    each under its slide's label (his number, or ours: 65a)."""
    import fitz
    doc = fitz.open(src)
    for x in content_streams(doc):
        doc.update_stream(x, round_stream(doc.xref_stream(x)))
    doc.set_metadata({"title": title, "author": author, "subject": f"{len(doc)} slides",
                      "creator": "wavesanddata.com", "producer": "Chromium, MuPDF",
                      "creationDate": "", "modDate": "", "keywords": "", "trapped": ""})
    labels = labels or [str(k) for k in range(1, len(titles) + 1)]
    doc.set_toc([[1, f"{lab}  {t}", k] for k, (lab, t) in enumerate(zip(labels, titles), 1)])
    doc.save(dst, garbage=4, deflate=True, no_new_id=True)


# ------------------------------------------------------------------ the SVG
SVG = "http://www.w3.org/2000/svg"
XLINK = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG)
NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
PATH_TOK = re.compile(r"[MmLlHhVvCcQqZz]|[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|[^\s,]")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "Z": 0}


def _q(tag):
    return f"{{{SVG}}}{tag}"


def fmt(v, nd):
    """A number as short as it can be written at nd decimals."""
    return _short(v, nd).decode()


def parse_path(d):
    """Path data as absolute segments [(M|L|C|Q|Z, points)]; H and V become L.
    ValueError for anything else (arcs), which is then left as it was."""
    toks = PATH_TOK.findall(d)
    out, i, cmd = [], 0, None
    cx = cy = sx = sy = 0.0
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            if t not in "MmLlHhVvCcQqZz":
                raise ValueError(t)
            cmd = t
            i += 1
            if cmd in "Zz":
                out.append(("Z", []))
                cx, cy = sx, sy
                continue
        elif cmd is None or cmd in "Zz" or not NUM.fullmatch(t):
            raise ValueError(t)
        up = cmd.upper()
        n = ARGS[up]
        a = [float(x) for x in toks[i:i + n]]
        if len(a) < n or not all(NUM.fullmatch(x) for x in toks[i:i + n]):
            raise ValueError(d[:40])
        i += n
        rel = cmd.islower()
        if up == "H":
            cx = a[0] + (cx if rel else 0)
            out.append(("L", [cx, cy]))
        elif up == "V":
            cy = a[0] + (cy if rel else 0)
            out.append(("L", [cx, cy]))
        else:
            pts = [a[k] + ((cx if k % 2 == 0 else cy) if rel else 0) for k in range(n)]
            out.append((up, pts))
            cx, cy = pts[-2], pts[-1]
            if up == "M":
                sx, sy = cx, cy
                cmd = "l" if rel else "L"       # pairs after a move are lines
    return out


def _join(prev, s):
    """s after the number prev: a space only where the two would run together."""
    if not prev or s[0] == "-" or (s[0] == "." and "." in prev):
        return s
    return " " + s


def encode_path(segs, nd):
    """The shortest path data for `segs`: each segment relative or absolute,
    whichever is shorter, numbers at nd decimals, no repeated letter. The pen
    follows the rounded points, so the rounding never drifts along a path."""
    q = 10 ** nd
    out, last, tail = [], None, ""
    px = py = sx = sy = 0.0
    for c, pts in segs:
        if c == "Z":
            out.append("z")
            last, tail = "z", ""
            px, py = sx, sy
            continue
        P = [round(v * q) / q for v in pts]
        rel = [P[k] - (px if k % 2 == 0 else py) for k in range(len(P))]
        opts = [(c, P), (c.lower(), rel)]
        if c == "L" and P[1] == py:
            opts += [("H", [P[0]]), ("h", [rel[0]])]
        if c == "L" and P[0] == px:
            opts += [("V", [P[1]]), ("v", [rel[1]])]
        best = None
        for cc, vals in opts:
            strs = [fmt(v, nd) for v in vals]
            omit = cc not in "Mm" and (cc == last or (last == "M" and cc == "L") or (last == "m" and cc == "l"))
            text, prev = ("", tail) if omit else (cc, "")
            for s in strs:
                text += _join(prev, s)
                prev = s
            if best is None or len(text) < len(best[0]):
                best = (text, cc, strs[-1])
        out.append(best[0])
        last, tail = best[1], best[2]
        px, py = P[-2], P[-1]
        if c == "M":
            sx, sy = px, py
    return "".join(out)


def _matrix(t):
    """A transform attribute's six numbers, or None if it is not one matrix()."""
    mo = re.fullmatch(r"\s*matrix\(([^)]*)\)\s*", t or "")
    if not mo:
        return None
    a = [float(x) for x in NUM.findall(mo.group(1))]
    return a if len(a) == 6 else None


def _sig(v, n=6):
    """v to n significant digits, written short."""
    if v == 0:
        return "0"
    return fmt(v, max(0, n - 1 - math.floor(math.log10(abs(v)))))


def _mat(a, nd_move=2):
    """A matrix: its linear part to six significant digits, its move to
    0.01 of the unit it moves in."""
    return "matrix(" + ",".join(_sig(v) if i < 4 else fmt(v, nd_move) for i, v in enumerate(a)) + ")"


def _page_rect(el, W, H):
    """Whether a clip's one path is a rectangle holding the whole page."""
    try:
        segs = parse_path(el.get("d", ""))
    except ValueError:
        return False
    a = _matrix(el.get("transform")) if el.get("transform") else [1, 0, 0, 1, 0, 0]
    if a is None or a[1] or a[2]:
        return False
    pts = [(p[k] * a[0] + a[4], p[k + 1] * a[3] + a[5]) for c, p in segs for k in range(0, len(p), 2)]
    if not pts or any(c not in "MLZ" for c, _ in segs):
        return False
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    corners = {(round(x, 1), round(y, 1)) for x, y in pts}
    box = {(round(min(xs), 1), round(min(ys), 1)), (round(max(xs), 1), round(min(ys), 1)),
           (round(max(xs), 1), round(max(ys), 1)), (round(min(xs), 1), round(max(ys), 1))}
    return (corners == box and min(xs) <= 0.5 and min(ys) <= 0.5
            and max(xs) >= W - 0.5 and max(ys) >= H - 0.5)


def _ids(n):
    """Short ids: a, b, ... z, aa, ab ..."""
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return s


def _scale(el):
    a = _matrix(el.get("transform"))
    return math.sqrt(abs(a[0] * a[3] - a[1] * a[2])) if a else 1.0


def minify(svg):
    """MuPDF's page SVG, written short. The picture is the same: every
    coordinate keeps 0.01 pt (0.013 px of the slide) where it is drawn."""
    root = ET.fromstring(svg)
    W, H = float(root.get("width")), float(root.get("height"))
    # the clips that clip nothing: the page's own rectangle
    noop = set()
    for defs in root.iter(_q("defs")):
        for cp in list(defs):
            if cp.tag == _q("clipPath") and len(cp) == 1 and _page_rect(cp[0], W, H):
                noop.add(cp.get("id"))
                defs.remove(cp)
    for el in root.iter():
        cp = el.get("clip-path")
        if cp and cp.startswith("url(#") and cp[5:-1] in noop:
            del el.attrib["clip-path"]

    # groups that carry nothing give their marks to their parent
    def unwrap(parent):
        kids = []
        for ch in list(parent):
            unwrap(ch)
            if ch.tag == _q("g") and not ch.attrib:
                kids.extend(list(ch))
            else:
                kids.append(ch)
        parent[:] = kids
    unwrap(root)
    # the scale each mark is drawn at: its transforms up to the page, and a
    # mark kept in <defs> (a glyph) at the largest <use> that shows it
    parent = {c: p for p in root.iter() for c in p}
    defs = set(root.iter(_q("defs")))

    def up(el):
        s = 1.0
        while el is not None:
            s *= _scale(el)
            el = parent.get(el)
        return s
    shown = {}
    for u in root.iter(_q("use")):
        href = u.get(f"{{{XLINK}}}href") or u.get("href") or ""
        if href.startswith("#"):
            shown[href[1:]] = max(shown.get(href[1:], 0.0), up(u))

    def drawn(el):
        """(scale to the page, scale to its glyph's em if it is part of one)."""
        s, e = 1.0, el
        while e is not None:
            s *= _scale(e)
            if parent.get(e) in defs:
                i = e.get("id")
                return (s * shown[i], s) if i in shown else (s, None)
            e = parent.get(e)
        return s, None

    def places(scale, tol=0.01):
        """The decimals that keep `tol` at this scale (0.01 pt on the page)."""
        return max(0, min(6, math.ceil(-math.log10(tol / max(scale, 1e-9)))))
    for el in root.iter():
        d = el.get("d")
        if d:
            page, em = drawn(el)
            # a glyph to its font's own grid, 0.001 em; any other mark to 0.01 pt
            nd = places(em, 0.001) if em is not None else places(page)
            try:
                el.set("d", encode_path(parse_path(d), nd))
            except ValueError:
                pass
        a = _matrix(el.get("transform"))
        if a is not None:          # its move is in its parent's units
            el.set("transform", _mat(a, places(drawn(parent[el])[0] if el in parent else 1.0)))
    # every reference by a short id
    rename = {}
    for el in root.iter():
        i = el.get("id")
        if i:
            rename[i] = _ids(len(rename))
            el.set("id", rename[i])
    for el in root.iter():
        el.attrib.pop("data-text", None)
        href = el.attrib.pop(f"{{{XLINK}}}href", None) or el.get("href")
        if href:
            el.set("href", "#" + rename.get(href[1:], href[1:]) if href.startswith("#") else href)
        for att in ("clip-path", "mask", "fill", "stroke"):
            v = el.get(att)
            if v and v.startswith("url(#"):
                el.set(att, f"url(#{rename.get(v[5:-1], v[5:-1])})")
    _lines(root, 1.0)
    _share(root)
    for el in root.iter():        # the line breaks between marks mean nothing
        el.tail = None
        if len(el):
            el.text = None
    return ET.tostring(root, encoding="unicode").replace(" />", "/>")


# What a group may carry for its marks: attributes they inherit, or (a
# transform) compose with their own. Opacity, a mask or a clip would act on
# the group as one, so a mark with any of those keeps its own.
SHARED = {"transform", "fill", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
          "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "fill-opacity",
          "stroke-opacity", "fill-rule"}


def _share(parent):
    """Runs of paths that differ only in their data become one group that
    carries what they share."""
    for ch in list(parent):
        if len(ch) and ch.tag != _q("clipPath"):
            _share(ch)
    kids, run, key = [], [], None

    def flush():
        if len(run) < 2:
            kids.extend(run)
        else:
            g = ET.Element(_q("g"), dict(key))
            for p in run:
                for k, _ in key:
                    del p.attrib[k]
                g.append(p)
            kids.append(g)
        run.clear()
    for ch in list(parent):
        att = {k: v for k, v in ch.attrib.items() if k != "d"}
        ok = ch.tag == _q("path") and "d" in ch.attrib and att and set(att) <= SHARED
        k = tuple(sorted(att.items())) if ok else None
        if k is None or k != key:
            flush()
            key = k
        if k is None:
            kids.append(ch)
        else:
            run.append(ch)
    flush()
    parent[:] = kids


def _lines(parent, scale):
    """Runs of glyphs (<use> with one fill and one linear part) become one
    group that carries the fill and that part; each glyph keeps only where it
    stands, as x and y in the group's own units. `scale` is the parent's, to
    the page."""
    for ch in list(parent):
        if len(ch):
            _lines(ch, scale * _scale(ch))
    kids, run, key = [], [], None

    def flush():
        if len(run) < 3:
            kids.extend(run)
        else:
            fill, (a, b, c, d) = key
            det = a * d - b * c
            att = {"fill": fill} if fill else {}
            att["transform"] = _mat([a, b, c, d, 0, 0])
            g = ET.Element(_q("g"), att)
            nd = max(0, min(6, math.ceil(-math.log10(0.01 / (scale * math.sqrt(abs(det)))))))
            for u in run:
                m = _matrix(u.get("transform"))
                tx, ty = m[4], m[5]
                del u.attrib["transform"]
                u.attrib.pop("fill", None)
                u.set("x", fmt((d * tx - c * ty) / det, nd))
                u.set("y", fmt((-b * tx + a * ty) / det, nd))
                g.append(u)
            kids.append(g)
        run.clear()
    for ch in list(parent):
        m = _matrix(ch.get("transform")) if ch.tag == _q("use") else None
        ok = (m is not None and abs(m[0] * m[3] - m[1] * m[2]) > 1e-12
              and set(ch.attrib) <= {"href", "transform", "fill"})
        k = (ch.get("fill"), tuple(float(_sig(v)) for v in m[:4])) if ok else None
        if k is None or k != key:
            flush()
            key = k
        if k is None:
            kids.append(ch)
        else:
            run.append(ch)
    flush()
    parent[:] = kids


def page_svg(page):
    """One page of the printed deck as a standalone, short SVG."""
    return minify(page.get_svg_image(text_as_path=True))
