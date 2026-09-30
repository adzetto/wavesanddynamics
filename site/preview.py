"""Render an emitted Ricos document to HTML.

build.py's page_doc() reads a document's nodes and hands them to plan(), with
its word on every picture (figure_meta: files, sizes, the author's share of
the column, a picture set in a sentence); then doc_body() renders each node
through render() and sets his rows of small pictures, and page_doc() builds
the page from what comes back, with head(), captions(), outline(), regions()
and zoom(). USAGE records how each picture was drawn, for build.py to write
its file that way.

plan() puts back what a reader of the Word file sees and the JSON no longer
says: the cover that opens most of his documents (picture, title, subtitle,
byline, rule), the chapter and section lines he set in bold instead of a
heading style, the italic line under a table or a row of covers that is its
caption, the "Table of Contents" line whose list Word generated and the
converter could not carry, and notes numbered [1], [2] at the end.

Nothing here changes a word. It decides which element a line becomes, and
which of three colour classes each of his colours lands on.

Run on its own, this prints the start of one document.
"""
import html
import json
import math
import os
import re
import sys

import mathtex

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(HERE, "build", "ricos")

DECOR = {"BOLD": ("<strong>", "</strong>"),
         "ITALIC": ("<em>", "</em>"),
         "UNDERLINE": ("<u>", "</u>"),
         "STRIKETHROUGH": ("<s>", "</s>")}

HEADING_DROP = frozenset({"BOLD", "COLOR"})   # a heading sets its own weight and ink
QUIET_DROP = frozenset({"BOLD", "ITALIC", "COLOR"})
ARROWS = {"→", "->", "⟶", "➔", "⇒"}

BYLINE = re.compile(r"(?:Dr|Prof)\.?\s+\S")
CHAPTER = re.compile(r"\d{1,2}\.\s+\S")            # "4. Non-Neural Network Models"
SECTION = re.compile(r"\d{1,2}\.\d{1,2}\.?\s+\S")   # "4.3 Decision Tree: ..."
NUMBER = re.compile(r"^(\d{1,2}(?:\.\d{1,2})*\.?)(\s+)(?=\S)")
FIGNO = re.compile(r"^((?:Figure|Fig\.|Table)\s*\d+[a-z]?[.:])(?=\s)")
NOTE = re.compile(r"\[(\d{1,3})\]\s")
# A run Word raised or lowered where Unicode has no glyph for it: the converter
# writes it in Word's linear notation, "_A" or "^(i+1)", as a run of its own
# (tools/ricos/glyphs.py script()). A whole run of that shape is a sub- or
# superscript again; an underscore inside other text is left alone.
SCRIPT = re.compile(r"([_^])(?:\((.+)\)|(\S))")

# What plan() decided for the document being rendered: a role per node id, the
# note numbers (and which have been marked once), the label of his contents
# line, the node that ends the cover, and how far heading levels shift so the
# top one becomes h2. "figs" is build.py's word on each picture (its files,
# its size, its share of Word's column, whether it sits in a sentence), by
# node id. A picture set in a sentence is drawn inside the text it came from:
# "with" carries, per paragraph id, the nodes that follow it into its <p> (the
# picture, then the rest of the sentence the converter cut off), "lead" the
# picture that opens a paragraph, "into" the pictures that go back into a
# caption or a heading at a place in its text, and "skip" every node drawn
# that way instead of where it stands. "ctx" is "cell" while a table's cells
# render, where a picture is part of the table and takes no frame, and "step"
# while a row of steps does (the same, but an icon keeps its size). "anim" is
# his animation of a picture, by the picture's file stem (animations()).
_PLAN = {"role": {}, "notes": frozenset(), "refs": set(), "toc": "", "end": None, "shift": 1,
         "flat": False, "figs": {}, "with": {}, "lead": {}, "into": {}, "skip": set(),
         "ctx": "", "anim": {}}

# Every picture file the pages draw, and how: "framed" (a figure, with a frame
# and a zoom link, flattened onto white) or "bare" (in a table, a row of steps
# or a sentence, drawn straight onto the page). build.py reads it after the
# pages are written, to make each file once, the way it is used.
USAGE = {}


# ------------------------------------------------------------- colour classes

def _oklch(r, g, b):
    """OKLCH chroma and hue of an sRGB colour (0-255 channels)."""
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = lin(r), lin(g), lin(b)
    lo = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    mi = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    sh = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    a = 1.9779984951 * lo - 2.4285922050 * mi + 0.4505937099 * sh
    bb = 0.0259040371 * lo + 0.7827717662 * mi - 0.8086757660 * sh
    return math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def colour_class(hexstr):
    """Map an author colour onto the site palette.

    His Word files carry 24 hexes but three intentions: maroons and rusts for
    emphasis, navies for a second voice, greys for what matters less. Carrying
    the raw hexes would fight the page and dropping them would lose his
    meaning, so each is classed and the stylesheet decides the value.

    The class comes from OKLCH chroma and hue, not from channel spread. His
    slate greys (#3B4757, #607283: chroma 0.031 and 0.034) are the colour of his
    subtitles, disclaimers and figure labels, and read as grey; his navies
    start at 0.054. The old test sent both to the navy.
    """
    h = (hexstr or "").lstrip("#")
    if len(h) != 6:
        return ""
    try:
        chroma, hue = _oklch(*(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    except ValueError:
        return ""
    if chroma < 0.045:
        return "ink-m"
    return "ink-a" if hue < 100 or hue >= 330 else "ink-b"


# ------------------------------------------------------------- reading nodes

def _text(node):
    if node.get("type") == "TEXT":
        return node.get("textData", {}).get("text", "")
    return "".join(_text(k) for k in node.get("nodes", []))


def _runs(node):
    """The TEXT runs of a paragraph that say something."""
    return [k for k in node.get("nodes", [])
            if k.get("type") == "TEXT" and k.get("textData", {}).get("text", "").strip()]


def _every(node, kind):
    """True when every run that says something carries the decoration."""
    runs = _runs(node)
    return bool(runs) and all(
        any(d.get("type") == kind for d in r["textData"].get("decorations", [])) for r in runs)


def _some(node, kind):
    return any(any(d.get("type") == kind for d in r["textData"].get("decorations", []))
               for r in _runs(node))


def _align(node):
    return node.get("paragraphData", {}).get("textStyle", {}).get("textAlignment", "AUTO")


def _captioned(image):
    return any(k.get("type") == "CAPTION" and _text(k).strip() for k in image.get("nodes", []))


def _has_image(node):
    return node.get("type") == "IMAGE" or any(_has_image(k) for k in node.get("nodes", []))


def _every_bold(cell):
    paras = [p for p in cell.get("nodes", []) if p.get("type") == "PARAGRAPH" and _runs(p)]
    return bool(paras) and all(_every(p, "BOLD") for p in paras)


# ------------------------------------------------------------- the plan

def plan(nodes, figs=None, anim=None):
    """Decide, once per document, what its top-level lines are for.

    page_doc() calls this before doc_body() renders the nodes and calls it with
    [] afterwards: node ids restart at n1 in every document, so a plan must
    never outlive the document it was made for. `anim` is this document's
    share of animations(): the pictures his animations take the place of.
    The document's formula map starts and ends with it too (mathtex.begin()):
    checked against the nodes before a line renders, and against what the
    page drew once it has.
    """
    mathtex.begin(nodes)
    figs = figs or {}
    role, n = {}, len(nodes)
    idx = {k: x.get("id") for k, x in enumerate(nodes)}

    def para(k):
        return k < n and nodes[k].get("type") == "PARAGRAPH" and _text(nodes[k]).strip()

    # The cover: an opening picture, his title in bold, the italic subtitle, the
    # byline, the rule under them. The machine learning guide opens with a small
    # running line and a rule above its title, and keeps those too.
    cover, i = [], 0
    if n and nodes[0].get("type") == "IMAGE" and not _captioned(nodes[0]):
        cover.append((0, "fm-art"))
        i = 1
    if (para(i) and not _every(nodes[i], "BOLD") and len(_text(nodes[i]).strip()) <= 90
            and i + 2 < n and nodes[i + 1].get("type") == "DIVIDER"
            and para(i + 2) and _every(nodes[i + 2], "BOLD")):
        cover += [(i, "fm-pre"), (i + 1, "fm-rule")]
        i += 2
    t = _text(nodes[i]).strip() if para(i) else ""
    if t and _every(nodes[i], "BOLD") and len(t) <= 160 and not BYLINE.match(t):
        cover.append((i, "fm-title"))
        i += 1
        if (para(i) and _every(nodes[i], "ITALIC") and not _some(nodes[i], "BOLD")
                and len(_text(nodes[i])) <= 240):
            cover.append((i, "fm-dek"))
            i += 1
        if para(i) and BYLINE.match(_text(nodes[i]).strip()) and len(_text(nodes[i])) <= 200:
            cover.append((i, "fm-by"))
            i += 1
        if i < n and nodes[i].get("type") == "DIVIDER":
            cover.append((i, "fm-end"))
            i += 1
    else:
        cover = []
    for k, r in cover:
        role[idx[k]] = r
    front = {k for k, _ in cover}

    # Headings. Word's heading levels shift so his top one becomes h2 under the
    # page's h1. A line he set in bold on its own is a heading too when it is
    # numbered like one ("4.3 Decision Tree", or "1. What is Machine Learning?"
    # in a guide whose other chapters are numbered headings), or when it is a
    # short unpunctuated label inside a section ("Go Deeper With Books", the
    # book categories): in his Word files those are 11.5pt bold with space above.
    levels = [x.get("headingData", {}).get("level", 1) for x in nodes if x.get("type") == "HEADING"]
    shift = 2 - min(levels) if levels else 1
    numbered = sum(1 for x in nodes if x.get("type") == "HEADING"
                   and CHAPTER.match(_text(x).strip())) >= 2
    open_section = False
    for k, x in enumerate(nodes):
        if k in front:
            continue
        if x.get("type") == "HEADING":
            open_section = True
            continue
        if x.get("type") != "PARAGRAPH" or not _every(x, "BOLD") or _some(x, "LINK"):
            continue
        t = _text(x).strip()
        if not t or len(t) > 150:
            continue
        if numbered and CHAPTER.match(t) and not SECTION.match(t):
            role[idx[k]] = "h2"
            open_section = True
        elif open_section and SECTION.match(t):
            role[idx[k]] = "h3"
        elif (open_section and len(t) <= 60 and t[-1] not in ".:;,?!…"
              and _align(x) not in ("CENTER", "RIGHT")):
            role[idx[k]] = "h3"

    # A line of italics straight after a table, or after a picture that has no
    # caption of its own (the last of a row of covers), is that thing's caption.
    for k in range(1, n):
        x, prev = nodes[k], nodes[k - 1]
        if (idx[k] not in role and x.get("type") == "PARAGRAPH" and _every(x, "ITALIC")
                and (prev.get("type") == "TABLE"
                     or (prev.get("type") == "IMAGE" and not _captioned(prev)))):
            role[idx[k]] = "cap"

    # His contents line: Word filled the list in from a field the converter
    # cannot carry, so the page's own contents list goes where it stood.
    label = ""
    for k, x in enumerate(nodes):
        if (x.get("type") == "PARAGRAPH" and idx[k] not in role
                and _text(x).strip().lower() in ("table of contents", "contents")):
            role[idx[k]] = "toc"
            label = _text(x).strip()
            break

    # Notes: the converter writes a footnote as [n] in the sentence and "[n] text"
    # at the end of the document. Only a trailing run that starts at [1] counts.
    notes, k = set(), n
    while k and nodes[k - 1].get("type") == "PARAGRAPH":
        k -= 1
    start = next((j for j in range(k, n) if _text(nodes[j]).startswith("[1] ")), None)
    if start is not None:
        for j in range(start, n):
            m = NOTE.match(_text(nodes[j]))
            if m:
                notes.add(int(m.group(1)))
                role[idx[j]] = "note"
            elif _text(nodes[j])[:1].isspace():
                role[idx[j]] = "note-more"
            else:
                notes = set()
                break
        if not notes:
            for j in range(start, n):
                role.pop(idx[j], None)

    # A document with no heading at all, in Word or among his bold lines (the
    # brochure), carries its sections as boxed titles: those become its h2s.
    flat = bool(nodes) and not levels and not any(r in ("h2", "h3") for r in role.values())
    joined = _joins(nodes, figs)
    _PLAN.update(role=role, notes=frozenset(notes), refs=set(), toc=label, shift=shift,
                 end=idx[max(front)] if front else None, flat=flat, figs=figs, ctx="",
                 anim=anim or {}, **joined)
    return _PLAN


def _joins(nodes, figs):
    """Where each picture that sat in a sentence goes back into its text.

    The converter cut an ordinary paragraph at such a picture, so the picture
    stands between the halves ("joins" says which halves there are), or kept
    a caption, a heading or a list item whole and put the picture after it
    ("offset" says where in its text). Only the top level is joined; a
    picture in a sentence inside a table cell would stand on its own line.
    """
    with_, lead, into, skip, host = {}, {}, {}, set(), {}
    for k, x in enumerate(nodes):
        meta = figs.get(x.get("id")) if x.get("type") == "IMAGE" else None
        if not meta or not meta.get("inline"):
            continue
        prev = nodes[k - 1] if k else None
        nxt = nodes[k + 1] if k + 1 < len(nodes) else None
        if meta.get("offset", -1) >= 0:
            if prev is not None and prev.get("type") in ("PARAGRAPH", "HEADING", "IMAGE"):
                into.setdefault(host.get(prev["id"], prev["id"]), []).append((meta["offset"], x))
                skip.add(x["id"])
            continue
        joins = meta.get("joins", "")
        if "prev" in joins or joins == "both":
            if prev is None or prev.get("type") != "PARAGRAPH":
                continue
            root = host.get(prev["id"], prev["id"])
            parts = [x] + ([nxt] if joins == "both" and nxt is not None
                           and nxt.get("type") == "PARAGRAPH" else [])
            with_.setdefault(root, []).extend(parts)
            for part in parts:
                skip.add(part["id"])
                host[part["id"]] = root
        elif joins == "next" and nxt is not None and nxt.get("type") == "PARAGRAPH":
            lead.setdefault(nxt["id"], []).append(x)
            skip.add(x["id"])
    return {"with": with_, "lead": lead, "into": into, "skip": skip}


# ------------------------------------------------------------- inline

def _noteref(m):
    """[n] in a sentence, linked to note n. The first mark of each carries the
    id the note links back to."""
    k = int(m.group(1))
    if k not in _PLAN["notes"]:
        return m.group(0)
    first = k not in _PLAN["refs"]
    _PLAN["refs"].add(k)
    anchor = f' id="fnref-{k}"' if first else ""
    return f'<a class="fnref"{anchor} href="#fn-{k}">[{k}]</a>'


# In a table cell a line break is how he wrapped a long value by hand to fit
# Word's narrow column: all 45 in the corpus sit in the ML guide's tables,
# mid-phrase ("No (add L1/Lasso / for this)"). On the page the column is
# another width, so the break goes and the browser wraps. A break before a
# list marker would be structure and stays.
CELL_BREAK = re.compile(r"[ \t]*\n[ \t]*(?![•\-–—]|\d+[.)]\s)")


def text_node(node, drop=frozenset(), notes=frozenset(), parts=None):
    """One run of his text as markup.

    A formula his document's map names (content/math/<slug>.json, set by
    mathtex.py) comes back from mathtex.cut() as MathML and goes in as it is:
    the map, not a guess from the letters, decides what is math. The rest is
    escaped, with his line breaks kept (a table cell's go, CELL_BREAK) and his
    note marks linked. A run that is all formula drops its italic, since math
    sets its own; a colour or a link still wraps it. `parts` is the run's
    [(text, False) | (markup, True)] when inline() has cut it already."""
    data = node.get("textData", {})
    raw = data.get("text", "")
    cell = _PLAN["ctx"] in ("cell", "step")
    if parts is None:
        parts = mathtex.cut(data) or [(raw, False)]
    words = "".join(v for v, formula in parts if not formula)
    script = None if any(m for _, m in parts) else SCRIPT.fullmatch(
        CELL_BREAK.sub(" ", words) if cell else words)
    if script:
        tag = "sub" if script.group(1) == "_" else "sup"
        out = f"<{tag}>{html.escape(script.group(2) or script.group(3), quote=False)}</{tag}>"
        if notes:
            out = re.sub(r"\[(\d{1,3})\]", _noteref, out)
    else:
        out = []
        for piece, formula in parts:
            if not formula:
                if cell:
                    piece = CELL_BREAK.sub(" ", piece)
                piece = html.escape(piece, quote=False).replace("\n", "<br>")
                if notes:
                    piece = re.sub(r"\[(\d{1,3})\]", _noteref, piece)
            out.append(piece)
        out = "".join(out)
        if all(m for _, m in parts):
            drop = drop | {"ITALIC"}
    link = ""
    for dec in data.get("decorations", []):
        kind = dec.get("type")
        if kind in drop:
            continue
        if kind in DECOR:
            open_tag, close_tag = DECOR[kind]
            out = open_tag + out + close_tag
        elif kind == "LINK":
            link = dec.get("linkData", {}).get("link", {}).get("url", "")
        elif kind == "COLOR":
            cls = colour_class((dec.get("colorData") or {}).get("foreground", ""))
            if cls:
                out = f'<span class="{cls}">{out}</span>'
    if link:
        out = f'<a href="{html.escape(link)}" rel="noopener">{out}</a>'
    return out


def _glued(runs, drop, notes):
    """The runs as markup, each formula held to the characters touching it.

    A browser may break a line on either side of a <math>: "(L1)" can end a
    line at "(", and "Q-values" start the next at "-values". So each formula,
    with his characters around it up to the nearest space on either side,
    goes in a span that does not wrap (.im-nb). One such unit may hold several
    formulas and the characters between them ("(H1/H2)", "Ax = b,"), and may
    cross runs: each run keeps its own decorations inside it. A long formula
    comes as pieces with a <wbr> between two (mathtex.py): the line may break
    there, so only its first and last pieces are held. A display formula
    stands alone and is never held."""
    cut = [(r, _pieces(mathtex.cut(r.get("textData", {}))
                       or [(r.get("textData", {}).get("text", ""), False)])) for r in runs]
    if not any(m for _, parts in cut for _, m in parts):
        return "".join(text_node(r, drop, notes, parts) for r, parts in cut)
    # one token per character of his text and per formula
    toks = []                    # (run, part, character offset or None)
    for i, (_, parts) in enumerate(cut):
        for j, (value, formula) in enumerate(parts):
            if formula:
                toks.append((i, j, None))
            else:
                toks.extend((i, j, k) for k in range(len(value)))

    def gap(t):                  # a place the line may break: a space, a <wbr>, a display
        i, j, k = t
        value, formula = cut[i][1][j]
        if formula:
            return formula == "wbr" or mathtex.is_display(value)
        return value[k].isspace() and value[k] != " "

    unit, uid = [None] * len(toks), 0
    for n, t in enumerate(toks):
        if t[2] is not None or gap(t) or unit[n] is not None:
            continue
        lo = hi = n
        while lo > 0 and not gap(toks[lo - 1]):
            lo -= 1
        while hi + 1 < len(toks) and not gap(toks[hi + 1]):
            hi += 1
        if lo == hi:
            continue             # a formula alone between spaces: nothing to hold
        uid += 1
        for m in range(lo, hi + 1):
            unit[m] = uid
    # each run's parts cut where a unit starts or ends, rendered with the run's
    # own decorations; a unit's fragments share one span
    frags, n = [], 0             # (unit, markup)
    for i, (run, parts) in enumerate(cut):
        cur, pieces = None, []
        for value, formula in parts:
            spans = [(unit[n], value, True)] if formula else []
            if not formula:
                at = 0
                for k in range(1, len(value) + 1):
                    if k == len(value) or unit[n + k] != unit[n + at]:
                        spans.append((unit[n + at], value[at:k], False))
                        at = k
            n += 1 if formula else len(value)
            for u, v, f in spans:
                if u != cur and pieces:
                    frags.append((cur, text_node(run, drop, notes, pieces)))
                    pieces = []
                cur = u
                pieces.append((v, f))
        if pieces:
            frags.append((cur, text_node(run, drop, notes, pieces)))
    out, k = [], 0
    while k < len(frags):
        u = frags[k][0]
        j = k
        while j < len(frags) and frags[j][0] == u:
            j += 1
        body = "".join(f for _, f in frags[k:j])
        out.append(f'<span class="im-nb">{body}</span>' if u is not None else body)
        k = j
    return "".join(out)


def _pieces(parts):
    """A run's parts with each long formula's pieces as parts of their own and
    the <wbr> between two as a part that is a place to break ("wbr")."""
    out = []
    for value, formula in parts:
        if formula and "<wbr>" in value and not mathtex.is_display(value):
            for k, piece in enumerate(value.split("<wbr>")):
                if k:
                    out.append(("<wbr>", "wbr"))
                out.append((piece, True))
        else:
            out.append((value, formula))
    return out


def inline(nodes, drop=frozenset(), notes=frozenset(), host=None):
    """The TEXT nodes as markup. `host` is the id of the node they belong to: a
    picture that sat in its sentence goes back in where it stood. A formula
    Word split into runs, which its map joins, comes back as a run of its own
    (mathtex.join())."""
    nodes = mathtex.join(nodes)
    inserts = _PLAN["into"].get(host) if host else None
    if not inserts:
        return _glued([n for n in nodes if n.get("type") == "TEXT"], drop, notes)
    texts = [n for n in nodes if n.get("type") == "TEXT"]
    full = "".join(n["textData"]["text"] for n in texts)
    lead = len(full) - len(full.lstrip())
    marks = sorted((lead + offset, pic) for offset, pic in inserts)
    out, at = [], 0
    for n in texts:
        text = n["textData"]["text"]
        start, cut = at, 0
        for pos, pic in marks:
            if start + cut <= pos <= start + len(text) and not pic.get("_done"):
                piece = text[cut:pos - start]
                if piece:
                    out.append(text_node({**n, "textData": {**n["textData"], "text": piece}},
                                         drop, notes))
                out.append(_in_line(pic))
                pic["_done"] = True
                cut = pos - start
        rest = text[cut:]
        if rest:
            out.append(text_node({**n, "textData": {**n["textData"], "text": rest}}, drop, notes))
        at += len(text)
    out.extend(_in_line(pic) for _, pic in marks if not pic.pop("_done", False))
    for _, pic in marks:
        pic.pop("_done", None)
    return "".join(out)


def _in_line(node):
    """A picture set in a line of text, drawn in the line at the text's own
    size: an equation, 1.12em tall (its glyphs fill 89% of its height, so its
    letters come out the size of the words around it)."""
    meta = _PLAN["figs"].get(node.get("id"), {})
    img = node["imageData"]["image"]
    src = meta.get("src") or img["src"]["id"]
    USAGE.setdefault(src, set()).add("bare")
    alt = html.escape(node["imageData"].get("altText", ""))
    return (f'<img class="eq" src="{src}" alt="{alt}" width="{meta.get("w", img.get("width", ""))}" '
            f'height="{meta.get("h", img.get("height", ""))}" loading="lazy" decoding="async">')


def _numbered(markup):
    """Set a heading's own number apart ("4.3" in "4.3 Decision Tree"), so it can
    take lining figures and a quieter ink. The words are untouched."""
    return NUMBER.sub(r'<span class="hn">\1</span>\2', markup, count=1)


def _figno(markup):
    """Set "Figure 12." apart at the head of a caption."""
    return FIGNO.sub(r'<span class="fign">\1</span>', markup, count=1)


def _lines(par):
    """A paragraph's runs cut into lines at the line breaks it carries. His
    callouts were one-cell tables in Word, and each paragraph inside one reaches
    Ricos as a line break in a single paragraph."""
    lines, cur = [], []
    for r in par.get("nodes", []):
        if r.get("type") != "TEXT":
            continue
        for j, part in enumerate(r.get("textData", {}).get("text", "").split("\n")):
            if j:
                lines.append(cur)
                cur = []
            if part:
                cur.append({**r, "textData": {**r["textData"], "text": part}})
    lines.append(cur)
    return [{"type": "PARAGRAPH", "nodes": ln, "paragraphData": par.get("paragraphData", {})}
            for ln in lines if any(x["textData"]["text"].strip() for x in ln)]


def _para(node, cls="", drop=frozenset()):
    """An ordinary paragraph. One set wholly in italic is set upright in the
    quieter ink: no italic is loaded (DESIGN_BRIEF 2.1), and a synthesized
    oblique across a whole paragraph is the worst of it. Italic inside a
    sentence keeps its emphasis."""
    classes = [cls] if cls else []
    align = _align(node)
    if align in ("CENTER", "RIGHT"):
        classes.append(f"a-{align.lower()}")
    if _every(node, "ITALIC"):
        drop = drop | {"ITALIC"}
        classes.append("p-it")
    nid = node.get("id")
    body = inline(node.get("nodes", []), drop, _PLAN["notes"], host=nid)
    # the picture that sat in this sentence, and the rest of the sentence the
    # converter cut off at it, come back into the same paragraph
    lead = "".join(_in_line(x) for x in _PLAN["lead"].get(nid, []))
    tail = "".join(_in_line(x) if x.get("type") == "IMAGE"
                   else inline(x.get("nodes", []), drop, _PLAN["notes"], host=x.get("id"))
                   for x in _PLAN["with"].get(nid, []))
    body = lead + body + tail
    if not body.strip():
        return ""
    attr = f' class="{" ".join(classes)}"' if classes else ""
    return f"<p{attr}>{body}</p>"


def _plain(markup):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", markup))).strip()


def _repeats(alt, caption):
    """True when a picture's alt text says what its caption says: the same
    words, whatever the spacing and case, with or without the caption's
    "Figure 3." in front."""
    a, c = " ".join(alt.split()).casefold(), " ".join(caption.split())
    return bool(a) and a in (c.casefold(), FIGNO.sub("", c, count=1).strip().casefold())


# ------------------------------------------------------------- blocks

def _callout(node, figdir):
    """His asides. The first line is the title when it is bold and more follows."""
    parts = []
    for kid in node.get("nodes", []):
        if kid.get("type") == "PARAGRAPH":
            parts += [("p", ln) for ln in _lines(kid)]
        else:
            parts.append(("x", kid))
    out, cls = [], "callout"
    for k, (kind, x) in enumerate(parts):
        if kind == "x":
            out.append(render(x, figdir))
        elif k == 0 and _every(x, "BOLD") and len(_text(x).strip()) <= 100:
            if len(parts) == 1:
                cls += " callout--label"
            tag = "h2" if _PLAN["flat"] else "p"
            out.append(f'<{tag} class="callout__t">'
                       f'{inline(x["nodes"], frozenset({"BOLD"}))}</{tag}>')
        else:
            out.append(_para(x))
    # A div, not an aside: inside main and article an aside is either a
    # nameless landmark or nothing, and his boxes are part of the text
    return f'<div class="{cls}">{"".join(out)}</div>'


def _table(node, figdir):
    """A table as he meant it, from the grid the converter could carry.

    Ricos has no colspan, so the converter flattens a merged cell: its content
    stays in the first column, the columns it covered arrive empty, and rows
    are padded to the widest. Put back here: a row that says something only in
    its first cell spans the table, and a column empty in every other row is a
    gap in Word's grid and goes. What is left decides the shape: one cell wide
    is an aside, one row is a sequence of steps, the rest is a table.

    Each table also knows how it behaves on a phone. Everything but a small
    matrix (blank top-left corner, the confusion matrix) restacks, one row to
    a block under the row's name, each value beside or under its column's
    name; nothing scrolls sideways where a block reads better.
    """
    rows = [list(r.get("nodes", [])) for r in node.get("nodes", [])]

    def full(c):
        return bool(_text(c).strip()) or _has_image(c)

    rows = [r for r in rows if any(full(c) for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    for r in rows:
        r.extend({} for _ in range(width - len(r)))
    span = [width > 1 and full(r[0]) and not any(full(c) for c in r[1:]) for r in rows]
    keep = [j for j in range(width)
            if any(not s and full(r[j]) for r, s in zip(rows, span, strict=True))]
    keep = keep or [0]
    rows = [[r[0]] + [{}] * (len(keep) - 1) if s else [r[j] for j in keep]
            for r, s in zip(rows, span, strict=True)]
    ncol = len(keep)

    def cell(c, ctx="cell"):
        # in a table a picture is part of the table (see _image); in an aside
        # it is a figure like any other
        was, _PLAN["ctx"] = _PLAN["ctx"], ctx
        try:
            return "".join(render(b, figdir) for b in c.get("nodes", []))
        finally:
            _PLAN["ctx"] = was

    if ncol == 1:                       # a box in Word: an aside
        head = rows[0][0]
        short = len(_text(head).strip()) <= 100 and not _has_image(head)
        title = html.escape(_plain(cell(head, "")), quote=False)
        tag = "h2" if _PLAN["flat"] else "p"
        first = f'<{tag} class="callout__t">{title}</{tag}>' if short else cell(head, "")
        rest = "".join(cell(r[0], "") for r in rows[1:])
        label = " callout--label" if short and not rest else ""
        return f'<div class="callout{label}">{first}{rest}</div>'

    if len(rows) == 1:                  # one row: steps, with his arrows between
        steps = []
        for c in rows[0]:
            if not full(c):
                continue
            t = _text(c).strip()
            if t in ARROWS and not _has_image(c):
                steps.append(f'<span class="flow__arrow" aria-hidden="true">'
                             f'{html.escape(t)}</span>')
            else:
                steps.append(f'<div class="flow__step">{cell(c, "step")}</div>')
        return f'<div class="flow">{"".join(steps)}</div>'

    head = node.get("tableData", {}).get("rowHeader", False) and not span[0]
    body = rows[1:] if head else rows
    bspan = span[1:] if head else span
    matrix = head and not full(rows[0][0])
    real = [r for r, s in zip(body, bspan, strict=True) if not s]
    words = [len(_text(c).split()) for r in real for c in r if full(c)]
    avg = sum(words) / len(words) if words else 0
    # the first column names its row: in a matrix, in any table of three rows or
    # more (his are all key and values), or where he set it in bold
    titled = (matrix or len(real) >= 3
              or (len(real) >= 2 and sum(_every_bold(r[0]) for r in real) >= 0.8 * len(real)))
    # A phone restacks every table but a small matrix, which it can hold (the
    # confusion matrix: two rows, two columns, read where they meet)
    stack = not (matrix and ncol <= 3 and len(real) <= 3)
    wide = ncol >= 4 or _has_image(node) or (ncol >= 3 and avg >= 12)
    pics = [any(_has_image(r[j]) for r in real) for j in range(ncol)]
    stub = [j == 0 and titled for j in range(ncol)]
    # Five columns and more whose last is sentences among phrases (Signal
    # Processing's "Notes / cross-field links", ten words a cell where the
    # others have three or four) set that column under the row, across the
    # columns after its name: in a fifth of the width it was a column of
    # seven-line cells, every row as tall as its note.
    means = [_mean_words(real, j, full) for j in range(ncol)]
    notes = (ncol >= 5 and not matrix and means[-1] >= 8
             and means[-1] >= 2 * max(means[1 if titled else 0:-1]))
    # On a phone a value says which column it is when its row holds two
    # values or more to tell apart; a picture and the words beside it (the
    # waves guide's fun table) need no names. Where every such value is a
    # phrase, it sits beside its name, not under it.
    named = [j for j in range(ncol) if not stub[j] and not pics[j]]
    labelled = stack and head and len(named) >= 2
    beside = labelled and all(_beside(real, j, full) for j in named if not (notes and j == ncol - 1))

    labels = [re.sub(r"\s+", " ", _text(c)).strip() for c in rows[0]] if head else [""] * ncol
    al = [_column_align(real, j, stub=stub[j], poster=len(real) <= 1) for j in range(ncol)]

    def aria(r):
        # a restacked table keeps its semantics only if they are spelled out
        return f' role="{r}"' if stack else ""

    def c_(j):
        # "c" centres the column; "pic" is a column of pictures
        names = " ".join(n for n, on in (("c", al[j]), ("pic", pics[j])) if on)
        return f' class="{names}"' if names else ""

    out = [_colgroup(node, keep)]
    if head:
        ths = "".join("<td></td>" if j == 0 and matrix
                      else f'<th scope="col"{c_(j)}{aria("columnheader")}>{cell(c)}</th>'
                      for j, c in enumerate(rows[0]))
        out.append(f'<thead{aria("rowgroup")}><tr{aria("row")}>{ths}</tr></thead>')
    trs, last = [], None
    for r, s in zip(body, bspan, strict=True):
        if s:
            trs.append(f'<tr class="tr-span"{aria("row")}><td colspan="{ncol}"{aria("cell")}>'
                       f'{cell(r[0])}</td></tr>')
            last = None
            continue
        # a row whose name is the one above it, word for word, is more of that
        # group (the ML guide's metrics: Classification five times, then
        # Regression twice, as he typed them): the stylesheet draws no rule
        # inside a group and sets the repeated name in the quieter ink
        name = _plain(cell(r[0])) if titled else None
        same = bool(name) and name == last
        last = name
        tds = []
        for j, c in enumerate(r):
            if stub[j]:
                tds.append(f'<th scope="row"{c_(j)}{aria("rowheader")}>{cell(c)}</th>')
                continue
            lab = labels[j] if labelled and j in named else ""
            lab = f' data-label="{html.escape(lab)}"' if lab else ""
            tds.append(f'<td{c_(j)}{lab}{aria("cell")}>{cell(c)}</td>')
        more = ' class="tr-same"' if same else ""
        trs.append(f'<tr{more}{aria("row")}>{"".join(tds)}</tr>')
    out.append(f'<tbody{aria("rowgroup")}>{"".join(trs)}</tbody>')
    cls = ("tbl" + (" tbl--wide" if wide else "") + (" tbl--stack" if stack else " tbl--scroll")
           + (" tbl--many" if ncol >= 5 and not notes else "")
           + (" tbl--dense" if ncol >= 7 else "") + (" tbl--notes" if notes else "")
           + (" tbl--kv" if beside else "") + (" tbl--fig" if any(pics) else ""))
    scroll = "" if stack else ' role="region" tabindex="0" aria-label="Table"'
    return f'<div class="{cls}"{scroll}><table{aria("table")}>{"".join(out)}</table></div>'


def _mean_words(real, j, full):
    counts = [len(_text(r[j]).split()) for r in real if full(r[j])]
    return sum(counts) / len(counts) if counts else 0


def _beside(real, j, full):
    """True when every value in column `j` is a phrase: one paragraph, no
    list or picture, fourteen words on average and thirty at most. On a
    phone such a value sits beside its column's name, in a column of names
    the eye runs down, instead of under it."""
    cells = [r[j] for r in real if full(r[j])]
    if not cells or any(_has_image(c) for c in cells):
        return False
    blocks = [sum(1 for b in c.get("nodes", []) if b.get("type") != "PARAGRAPH" or _text(b).strip())
              for c in cells]
    counts = [len(_text(c).split()) for c in cells]
    return max(blocks) <= 1 and sum(counts) / len(counts) <= 14 and max(counts) <= 30


def _column_align(real, j, stub=False, poster=False):
    """"c" to centre column `j`, "" to set it left like the text.

    Word centres the cells of eleven of the ML guide's eighteen tables and all
    of Signal Processing's, the long ones included: glossary definitions of 20
    words, a paragraph to a cell. Centred, a column of values that wrap reads
    as a ragged run of lines with no edge to return to, and a row's name hangs
    in ragged lines ("Medical ultrasound, sonar and echolocation" in four under
    "Structural dynamics"); beside a column set left, even a column of one-word
    ratings (High, Medium) reads as a hole. So names and values read from
    their left edge, like the text. Two things stay centred: a column of
    pictures, with the words under them, and a table that is one row, which
    is not data but a row of parallel statements set out like a poster (the
    Brochure's Inspect / Monitor / Model, the ML guide's pipeline), where he
    centred it. The heading over a column follows the column, which is what
    the phone table and the eye both expect.
    """
    if stub:
        return ""
    if any(_has_image(r[j]) for r in real):
        return "c"
    if not poster:
        return ""
    aligns = [_align(p) for r in real for p in r[j].get("nodes", [])
              if p.get("type") == "PARAGRAPH" and _text(p).strip()]
    return "c" if aligns and sum(a == "CENTER" for a in aligns) * 2 > len(aligns) else ""


def _colgroup(node, keep):
    """Word's column widths, as the share of the table each column he kept
    takes (`tableData.dimensions.colsWidthRatio`, over the columns before the
    gaps went), or "" when the converter could not read them.

    Four columns at most. A table of five or more is a grid of short values
    set a step smaller, and its columns are as narrow as their longest word
    allows; held to Word's shares, the ML guide's seven-column table needed
    774px instead of 714 and scrolled. The browser's own widths fit it."""
    ratios = node.get("tableData", {}).get("dimensions", {}).get("colsWidthRatio") or []
    if not ratios or max(keep) >= len(ratios) or len(keep) > 4:
        return ""
    kept = [ratios[j] for j in keep]
    total = sum(kept)
    if total <= 0 or len(kept) < 2:
        return ""
    cols = "".join(f'<col style="width:{100 * r / total:.1f}%">' for r in kept)
    return f"<colgroup>{cols}</colgroup>"


# ------------------------------------------------------------- pictures

def _image(node, figdir, role):
    """One picture as a figure, sized by build.py's word on it (`_PLAN["figs"]`).

    Three ways to be drawn. In a table's cell or a row of steps the picture is
    part of the table: no frame, at half its pixels, so it is sharp on a
    screen of two pixels to the point and never stretched to the cell; one
    redrawn as a moving figure is that figure, at the cell's width, or in a
    row of steps at the icon's own size (_in_cell). In a
    sentence it is set in the line (`_in_line`). Anywhere else it is a
    figure: the column's width at most and never past its own pixels, a
    narrower share of the column where the author set it narrower in Word
    (`fig--inset`, the share floored at 60%), with a 720px copy for a screen
    that does not need the full file, and a link to the full file when it is
    drawn smaller than it is. A figure he made an animation of is that
    animation, the column's width, over the same caption (_animated()).
    """
    meta = _PLAN["figs"].get(node.get("id"), {})
    if meta.get("inline"):
        return _in_line(node)            # a sentence picture no text could take back
    kids = node.get("nodes", [])
    img = node["imageData"]["image"]
    src = meta.get("src") or f'{figdir}/{img["src"]["id"]}'
    w, h = meta.get("w", img.get("width", "")), meta.get("h", img.get("height", ""))
    alt = node["imageData"].get("altText", "")
    cap = ""
    for child in kids:
        if child.get("type") == "CAPTION" and _text(child).strip():
            words = inline(child.get("nodes", []), frozenset({"ITALIC"}), _PLAN["notes"],
                           host=node.get("id"))
            cap = f"<figcaption>{_figno(words)}</figcaption>"
            # The converter copies each caption into the picture's alt text
            # (tools/ricos/emit.py), and read aloud that is the caption
            # twice: once for the picture, once for the figcaption, which
            # already names the figure. An alt that only repeats the
            # caption becomes alt=""; alt text of its own stays.
            if _repeats(alt, _text(child)):
                alt = ""
    alt = html.escape(alt)
    load = 'loading="eager" fetchpriority="high"' if role == "fm-art" else 'loading="lazy"'
    if _PLAN["ctx"] in ("cell", "step"):
        USAGE.setdefault(src, set()).add("bare")
        if isinstance(w, int) and isinstance(h, int):
            w, h = max(1, round(w / 2)), max(1, round(h / 2))
        anim = _PLAN["anim"].get(os.path.splitext(img["src"]["id"])[0])
        if anim:
            return _in_cell(anim, src, alt, w, h, cap)
        return (f'<figure><img src="{src}" alt="{alt}" width="{w}" height="{h}" '
                f'{load} decoding="async">{cap}</figure>')
    USAGE.setdefault(src, set()).add("framed")
    classes, style, srcset = [], "", ""
    if meta.get("src720"):
        srcset = f' srcset="{meta["src720"]} 720w, {src} {w}w" sizes="{meta["sizes"]}"'
    anim = _PLAN["anim"].get(os.path.splitext(img["src"]["id"])[0])
    if anim:
        if anim.get("still"):            # a redrawn figure prints its own frame
            still = anim["still"]
            return _animated(anim, f'src="{still["src"]}" alt="{alt}" width="{still["w"]}" '
                                   f'height="{still["h"]}"', cap)
        return _animated(anim, f'src="{src}" alt="{alt}"{srcset} width="{w}" height="{h}"', cap)
    if meta.get("inset"):
        classes.append("fig--inset")
        style = f' style="--inset:{meta["inset"]}%;--nat:{w}px"'
    if meta.get("zoom") and role != "fm-art":
        classes.append("fig--zoom")
    klass = f' class="{" ".join(classes)}"' if classes else ""
    return (f'<figure{klass}{style}><img src="{src}" alt="{alt}"{srcset} '
            f'width="{w}" height="{h}" {load} decoding="async">{cap}</figure>')


def _in_cell(anim, src, alt, w, h, cap):
    """A picture in a table's cell that a moving figure redraws (the waves
    guide's fun table: content/anim/anim.<name>.json names the pictures): the
    frame and its still, as _animated() writes them for a figure, marked
    `fig--cell`. The figure is drawn at the picture's proportions in the cell
    (tools/numfig/README.md), so the frame and the still share one box, the
    cell's width. The still is the figure's own printed frame where it has
    one, else the picture at half its pixels, and then the box is no wider.

    parts/docs.py shows the still until the row is read: then the frame fades
    in over it and plays, and fades back when the reader moves on, so one
    row's figure moves at a time. Print, a page with no script and a reader
    who asks for less motion get the figure as _animated() gives it.

    In a row of steps the picture is an icon beside his label: its frame
    keeps the picture's size (half its pixels, not the step's width), plays
    once as it comes into view (the figure's own), and is a drawing, not a
    stop for the keyboard or a screen reader, as his picture was (alt="")."""
    if anim.get("still"):
        still, size = anim["still"], ""
    else:
        still, size = {"src": src, "w": w, "h": h}, f' style="max-width:{w}px"'
    moving = _animated(anim, f'src="{still["src"]}" alt="{alt}" width="{still["w"]}" '
                             f'height="{still["h"]}"', cap)
    if _PLAN["ctx"] == "step":
        size = f' style="width:{w}px"'
        moving = moving.replace('<iframe class="anim" ', '<iframe class="anim" tabindex="-1" aria-hidden="true" ', 1)
    return moving.replace('<figure class="fig--anim">', f'<figure class="fig--anim fig--cell"{size}>', 1)


# ------------------------------------------------------------- his animations

ANIM_SRC = os.path.join(HERE, "content", "anim")
CANVAS = re.compile(r"\bconst W = (\d+), H = (\d+)\b")   # his files' drawing size


def animations(href="../anim", src=ANIM_SRC):
    """His animated figures and the pictures they take the place of, as
    {slug: {picture's file stem: {"src", "title", "w", "h"}}}.

    content/anim/anim.json names, per document, the picture each of his
    animations redraws; `href` is where build.py publishes his files. Each
    file draws on a W by H canvas (`const W = 1000, H = 790`) and sets the
    canvas to the width it is given at that ratio, so a frame of that ratio
    fits it exactly: nothing to scroll, and no jump when it loads. The
    frame's name is the file's title without its number: his fig4 is Figure
    4 in the SHM introduction and Figure 3 in the waves guide, and the
    caption under the frame gives the page's own number. A file without a
    title or a size stops the build rather than draw a frame of a guessed
    shape.

    A figure redrawn from a numerical model (nf-*.html, tools/numfig/) comes
    with a frame of its own beside it, nf-*.webp, and that frame, not the
    picture it replaces, is what paper and a page without a script show.

    Beside anim.json, each anim.<name>.json holds one set of redrawn figures
    in the same shape (tools/numfig/: a document's figures, a table's
    drawings), so the people drawing them never write one file at once. A
    picture named twice stops the build.
    """
    path = os.path.join(src, "anim.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        wanted = json.load(fh)
    for extra in sorted(n for n in os.listdir(src) if re.fullmatch(r"anim\.[\w-]+\.json", n)):
        with open(os.path.join(src, extra), encoding="utf-8") as fh:
            for slug, pictures in json.load(fh).items():
                have = wanted.setdefault(slug, {})
                twice = set(have) & set(pictures)
                if twice:
                    raise ValueError(f"content/anim/{extra}: {slug} {sorted(twice)} named twice")
                have.update(pictures)
    files, out = {}, {}
    for slug, pictures in wanted.items():
        for stem, name in pictures.items():
            if name not in files:
                with open(os.path.join(src, name), encoding="utf-8") as fh:
                    text = fh.read()
                size, title = CANVAS.search(text), re.search(r"<title>(.*?)</title>", text, re.S)
                if not size or not title:
                    raise ValueError(f"content/anim/{name}: no <title>, or no canvas size "
                                     f"(const W = ..., H = ...)")
                name_ = " ".join(html.unescape(title.group(1)).split())
                files[name] = {"src": f"{href}/{name}", "w": int(size.group(1)),
                               "h": int(size.group(2)),
                               "title": FIGNO.sub("", name_, count=1).strip() or name_}
                frame = os.path.join(src, os.path.splitext(name)[0] + ".webp")
                if os.path.isfile(frame):
                    from PIL import Image
                    with Image.open(frame) as im:
                        fw, fh_ = im.size
                    files[name]["still"] = {"src": f"{href}/{os.path.splitext(name)[0]}.webp",
                                            "w": fw, "h": fh_}
            out.setdefault(slug, {})[stem] = files[name]
    return out


def _animated(anim, still, cap):
    """His animation where the picture stood, under the picture's caption.

    The frame takes the canvas's ratio (animations()) and loads as it nears
    the screen. The picture stays inside the figure for where the frame
    cannot run and for paper: parts/docs.py shows the frame only once the
    page's script has marked <html> "js", and the picture in print. `still`
    is the picture's attributes as _image() writes them."""
    return (f'<figure class="fig--anim"><iframe class="anim" src="{anim["src"]}" '
            f'title="{html.escape(anim["title"])}" loading="lazy" '
            f'style="aspect-ratio:{anim["w"]}/{anim["h"]}"></iframe>{FULL}'
            f'<img class="anim__still" {still} loading="lazy" decoding="async">{cap}</figure>')


# The button that shows a moving figure full screen (parts/docs.py runs it):
# four corners that open outward, and fold in again once it is full screen.
FULL = ('<button class="anim__full" type="button" aria-label="Show this figure full screen">'
        '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" '
        'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        'focusable="false"><g class="af-open"><path class="af-a" d="M4 9V4h5"/>'
        '<path class="af-b" d="M20 9V4h-5"/><path class="af-c" d="M4 15v5h5"/>'
        '<path class="af-d" d="M20 15v5h-5"/></g><g class="af-shut"><path d="M9 4v5H4"/>'
        '<path d="M15 4v5h5"/><path d="M9 20v-5H4"/><path d="M15 20v-5h5"/></g></svg></button>')


# ------------------------------------------------------------- render

def render(node, figdir):
    out = _render(node, figdir)
    if node.get("id") and node.get("id") == _PLAN["end"]:
        out += "<!--/dochead-->"
    return out


def _render(node, figdir):
    kind = node.get("type")
    kids = node.get("nodes", [])
    role = _PLAN["role"].get(node.get("id")) if node.get("id") else None
    if node.get("id") in _PLAN["skip"]:
        return ""                        # drawn inside the text it came from

    if kind == "PARAGRAPH":
        if role == "fm-title":
            return f"<h1>{inline(kids, QUIET_DROP)}</h1>"
        if role in ("fm-dek", "fm-by", "fm-pre"):
            return f'<p class="dochead__{role[3:]}">{inline(kids, QUIET_DROP)}</p>'
        if role in ("h2", "h3"):
            return f"<{role}>{_numbered(inline(kids, HEADING_DROP))}</{role}>"
        if role == "toc":
            return "<!--toc-->"
        if role == "cap":
            return f'<p class="cap">{_figno(inline(kids, frozenset({"ITALIC", "COLOR"})))}</p>'
        if role == "note":
            body = inline(kids)
            m = re.match(r"\[(\d{1,3})\]", body)
            if m:
                return (f'<p class="fn" id="fn-{m.group(1)}"><a class="fn__back" '
                        f'href="#fnref-{m.group(1)}">{m.group(0)}</a>{body[m.end():]}</p>')
        if role == "note-more":
            return _para(node, "fn")
        return _para(node)

    if kind == "HEADING":
        level = min(max(node.get("headingData", {}).get("level", 1) + _PLAN["shift"], 2), 6)
        words = inline(kids, HEADING_DROP, _PLAN["notes"], host=node.get("id"))
        return f"<h{level}>{_numbered(words)}</h{level}>"

    if kind == "IMAGE":
        return _image(node, figdir, role)

    if kind == "DIVIDER":
        if role == "fm-end":
            return ""                    # the page header draws the rule under the cover
        if role == "fm-rule":
            return '<hr class="dochead__rule">'
        return '<hr class="docrule">'

    if kind in ("BULLETED_LIST", "ORDERED_LIST"):
        tag = "ul" if kind == "BULLETED_LIST" else "ol"
        items = "".join(f"<li>{''.join(render(b, figdir) for b in i.get('nodes', []))}</li>"
                        for i in kids)
        return f"<{tag}>{items}</{tag}>"

    if kind == "BLOCKQUOTE":
        return _callout(node, figdir)

    if kind == "TABLE":
        return _table(node, figdir)

    if kind == "VIDEO":
        return _video(node)

    if kind == "FILE":
        return _file(node)

    return ""


# ------------------------------------------------------------- film and file

PLAY = ('<svg viewBox="0 0 76 76" aria-hidden="true"><circle cx="38" cy="38" r="37" '
        'fill="rgba(20,17,14,.5)" stroke="rgba(255,255,255,.85)" stroke-width="1.5"/>'
        '<path d="M31 25.5v25l20-12.5z" fill="#fff"/></svg>')

DOWNLOAD = ('<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" '
            'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true"><path d="M12 5v10m-4.5-4.5L12 15l4.5-4.5M6 19h12"/></svg>')


def _video(node):
    """A film his post embeds (Wix's VIDEO node). build.py's word on it, in
    `_PLAN["figs"]` by node id, gives the poster it wrote and, for YouTube,
    the embed address. The poster is a link to the film where it lives, so it
    plays without JavaScript; parts/blog.py swaps in the player on a press,
    and until then nothing is fetched from the film's site. A film build.py
    said nothing about is a plain link to it."""
    meta = _PLAN["figs"].get(node.get("id"), {})
    url = meta.get("url") or node.get("videoData", {}).get("video", {}).get("src", {}).get("url", "")
    if not url:
        return ""
    title = meta.get("title") or "Video"
    by = f', {meta["author"]}' if meta.get("author") else ""
    name = html.escape(f"Play the video: {title}{by}, on YouTube" if meta.get("embed")
                       else f"Play the video: {title}{by}")
    if not meta.get("poster"):
        return f'<p><a href="{html.escape(url)}" rel="noopener">{name}</a></p>'
    embed = (f' data-embed="{html.escape(meta["embed"])}" data-title="{html.escape(title)}"'
             if meta.get("embed") else "")
    cap = html.escape(f"{title}{by}" + (" (YouTube)" if meta.get("embed") else ""), quote=False)
    return (f'<figure class="postvid"><a class="postvid__a" href="{html.escape(url)}" '
            f'rel="noopener"{embed} aria-label="{name}">'
            f'<img src="{meta["poster"]}" alt="" width="{meta["pw"]}" height="{meta["ph"]}" '
            f'loading="lazy" decoding="async"><span class="postvid__play">{PLAY}</span></a>'
            f'<figcaption>{cap}</figcaption></figure>')


def _file(node):
    """A file his post offers (Wix's FILE node): the download row his document
    pages use, under his own file name, or its waiting state where build.py
    publishes no copy of the file (`pending`), in the words the research boxes
    use for a Word file that is not up yet."""
    meta = _PLAN["figs"].get(node.get("id"), {})
    data = node.get("fileData", {})
    name = data.get("name") or "File"
    if meta.get("href") and not meta.get("pending"):
        size = meta.get("bytes") or data.get("size") or 0
        return (f'<p class="docmeta postfile"><a class="docdl" href="{html.escape(meta["href"])}" '
                f'download="{html.escape(name)}">{DOWNLOAD}'
                f'<span class="docdl__t">{html.escape(name, quote=False)}</span> '
                f'<span class="docdl__size">{size / 1e6:.2f}&nbsp;MB</span></a></p>')
    kind = "Word file" if (data.get("type") or "").lower() in ("doc", "docx") else "File"
    return (f'<p class="docmeta postfile"><span class="docdl docdl--wait">{DOWNLOAD}'
            f'<span>{kind}, coming soon</span></span></p>')


# ------------------------------------------------------------- the page's pieces

def head(body):
    """Split the rendered body at the end of the cover: (cover, rest). First,
    each picture of a formula his map names is set as the formula
    (mathtex.pictures()): build.py has written its alt text by now, and its
    file leaves USAGE, since the page no longer draws it."""
    body = mathtex.pictures(body, USAGE)
    cover, mark, rest = body.partition("<!--/dochead-->")
    return (cover, rest) if mark else ("", body)


def captions(body):
    """Hang each caption line on the table, picture or row of covers above it."""
    cap = r'\s*<p class="cap">(.*?)</p>'
    row = r'<div class="figrow"((?: style="[^"]*")?)>((?:(?!</div>).)*)</div>'
    body = re.sub(row + cap, r'<figure class="figrow"><div class="figrow__row"\1>\2</div>'
                  r'<figcaption>\3</figcaption></figure>', body, flags=re.S)
    body = re.sub(row, r'<div class="figrow"><div class="figrow__row"\1>\2</div></div>',
                  body, flags=re.S)
    body = re.sub(r'(<figure(?: class="[^"]*")?(?: style="[^"]*")?><img [^>]*>)</figure>' + cap,
                  r'\1<figcaption>\2</figcaption></figure>', body, flags=re.S)
    table = r'(<div class="tbl[^"]*"[^>]*>(?:(?!<div class="tbl).)*?</table></div>)'
    count = iter(range(1, 10_000))

    def tfig(m):
        # a table that scrolls is a focusable region: its caption names it
        k = next(count)
        grid = m.group(1).replace(' aria-label="Table"', f' aria-labelledby="tcap-{k}"', 1)
        return (f'<figure class="tfig">{grid}'
                f'<figcaption id="tcap-{k}">{m.group(2)}</figcaption></figure>')

    return re.sub(table + cap, tfig, body, flags=re.S)


def _slug(text, seen):
    s = re.sub(r"[^a-z0-9]+", "-", NUMBER.sub("", text.lower(), count=1)).strip("-") or "section"
    s = s[:60].rstrip("-")
    base, k = s, 2
    while s in seen:
        s, k = f"{base}-{k}", k + 1
    seen.add(s)
    return s


def outline(body):
    """Give every h2 and h3 an id; return (body, sections).

    sections is [(id, level, inner markup, plain text)] in reading order. The
    ids are the words of the heading without its number, so a link to a
    section says what it is and survives a renumbering.
    """
    seen, sections = set(), []

    def tag(m):
        level, inner = int(m.group(1)), m.group(2)
        plain = _plain(inner)
        sid = _slug(plain, seen)
        sections.append((sid, level, inner, plain))
        return f'<h{level} id="{sid}">{inner}</h{level}>'

    body = re.sub(r"<h([23])>(.*?)</h\1>", tag, body, flags=re.S)
    return body, sections


def regions(body):
    """A table that scrolls is a focusable region, and a region needs a name.
    captions() gives a captioned one its caption; one without a caption is
    named by the heading it sits under, not by the word "Table"."""
    heading = [None]

    def name(m):
        if m.group(1):
            heading[0] = m.group(1)
            return m.group(0)
        return f'aria-labelledby="{heading[0]}"' if heading[0] else m.group(0)

    return re.sub(r'<h[23] id="([^"]+)"|aria-label="Table"', name, body)


# the mark a zoomable picture carries where there is no zoom cursor to say
# so (a touch screen): two corners pulling apart, in the inline icon family
EXPAND = ('<span class="figzoom__mark" aria-hidden="true"><svg viewBox="0 0 24 24" width="16" '
          'height="16" fill="none" stroke="currentColor" stroke-width="1.5" '
          'stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4.75h4.75v4.75M9.5 '
          '19.25H4.75V14.5M19.25 4.75l-5.5 5.5M4.75 19.25l5.5-5.5"/></svg></span>')


def zoom(body):
    """A picture drawn smaller than it is links to its full-size file, the only
    way to read the small type in a 1280px diagram on a phone. _image() marks
    which (`fig--zoom`).

    The link takes its name from the picture's own alt text when it has one.
    A captioned picture has alt="" (render() drops an alt that repeats the
    caption), so its link is named by the figure's number, "Figure 3, full
    size", and a screen reader still hears the caption once, as the caption.
    A picture with neither alt text nor a caption gets no link.
    """
    def link(m):
        opening, img, src, alt, cap, num = m.groups()
        if alt:
            name = ""
        elif cap:
            label = f"{num.rstrip('.:')}, full size" if num else "Full-size image"
            name = f' aria-label="{html.escape(label)}"'
        else:
            return m.group(0)
        return f'{opening}<a class="figzoom" href="{src}"{name}>{img}{EXPAND}</a>'

    return re.sub(r'(<figure class="[^"]*\bfig--zoom\b[^"]*"(?: style="[^"]*")?>)'
                  r'(<img src="([^"]+)" alt="([^"]*)"[^>]*>)'
                  r'(?=(<figcaption>)?(?:<span class="fign">([^<]*)</span>)?)', link, body)


# ------------------------------------------------------------- standalone use

def document(slug, part="part-01.json", figdir=None):
    path = os.path.join(BUILD, slug, part)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    figdir = figdir if figdir is not None else f"fig/{slug}"
    plan(doc["nodes"])
    try:
        return "".join(render(n, figdir) for n in doc["nodes"])
    finally:
        plan([])


def pick(slug, part, types, limit, figdir):
    """A few real nodes of the named types, for showing a component that the
    main document happens not to contain."""
    with open(os.path.join(BUILD, slug, part), encoding="utf-8") as fh:
        doc = json.load(fh)
    got, out = 0, []
    for n in doc["nodes"]:
        if n.get("type") in types:
            out.append(render(n, figdir))
            got += 1
            if got >= limit:
                break
    return "".join(out)


if __name__ == "__main__":
    body = document("understanding-shm-and-ndt")
    print(len(body), "chars of HTML")
    print(body[:400])
