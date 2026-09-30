"""Convert Dr. Kaynardag's Word documents to Ricos, without touching Wix.

    python tools/docx2ricos.py                     every file in content/source
    python tools/docx2ricos.py <file.docx> ...     just these
    python tools/docx2ricos.py --help              this text

Nothing here talks to the network. The point is to see, before anything is
published, how the documents come out and how many records each one needs: a Wix
CMS item holds 500 KB, and the rich content counts against it.

Writes build/ricos/<slug>/ with the parts, the figures and a manifest.

The exit status reports; it does not pass judgement:

    0  converted, with nothing to say about it
    1  converted, and the run has warnings. A warning is a finding about a
       document - a drawing with no picture in it, a figure its author left
       uncaptioned, a section he never gave a heading - and not a fault in the
       conversion. Every document in this corpus produces at least one, so a
       run of all seven ends here: that is the expected result and the report
       working, not the tool failing.
    2  a document could not be converted. This is the only status that means
       the tool did not do its job, and the run names the file and the error.
"""

import glob
import json
import os
import re
import shutil
import sys
import zipfile

# Run as a script - `python tools/docx2ricos.py` - sys.path[0] is the tools
# directory, and that one entry is wrong twice over. The repo root is nowhere on
# the path, so `from tools.ricos... import` raises ModuleNotFoundError; and
# tools/inspect.py stands in front of the standard library's `inspect`, which
# `dataclasses` imports on the way into blocks.py, so adding the root without
# removing this would still not import. One entry causes both faults, so it is
# replaced rather than added to. Run as `python -m tools.docx2ricos`, or
# imported by a test, sys.path[0] is something else and is left alone.
if sys.path and os.path.abspath(sys.path[0]) == os.path.dirname(
    os.path.abspath(__file__)
):
    sys.path[0] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from lxml import etree
from PIL import Image

from tools.ricos.blocks import Callout, Figure, Para, Rule, Table, walk
from tools.ricos.docx_read import crop_box, read_blocks, text_width
from tools.ricos.emit import color_on_page, emit
from tools.ricos.glyphs import UNMAPPED
from tools.ricos.split import LIMIT, doc_bytes, pack, split_at_headings

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "build", "ricos")
SOURCE = os.path.join(HERE, "content", "source")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
MC = "{http://schemas.openxmlformats.org/markup-compatibility/2006}"
OFFICE = "{urn:schemas-microsoft-com:office:office}"
DRAW = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

# What a drawing holds, read off a:graphicData/@uri, as (one, many). Only the
# first of these carries an image part; the rest are drawn in Word and have
# nothing to publish. Both forms are stored because the rule `_n` applies -
# add an "s" - writes "2 SmartArts" and "1 others", and this report is read by
# a person. The manifest is keyed on the singular.
GRAPHIC_KIND = {
    "http://schemas.openxmlformats.org/drawingml/2006/picture": ("picture", "pictures"),
    "http://schemas.microsoft.com/office/word/2010/wordprocessingShape": (
        "shape",
        "shapes",
    ),
    "http://schemas.openxmlformats.org/drawingml/2006/chart": ("chart", "charts"),
    "http://schemas.openxmlformats.org/drawingml/2006/diagram": (
        "SmartArt",
        "SmartArt graphics",
    ),
    "http://schemas.openxmlformats.org/drawingml/2006/table": (
        "drawing table",
        "drawing tables",
    ),
}
UNNAMED_KIND = ("other", "of other kinds")
KIND_PLURAL = dict([*GRAPHIC_KIND.values(), UNNAMED_KIND])

OK, WARNINGS, FAILED = 0, 1, 2


def slugify(name):
    """The output directory name for one source file.

    Raises ValueError when nothing is left of it. Only `[a-z0-9]` survives the
    substitution, so a stem written entirely outside ASCII - "SGU.docx" with
    Turkish letters, an ordinary name here - reduces to "". `os.path.join(OUT,
    "")` is OUT itself, and `convert` empties that directory before it writes:
    an empty slug deletes the whole output tree, the documents already
    converted earlier in the same run included, and then drops part-01.json in
    the root beside the per-document directories. There is no safe answer but
    to refuse, and `main` reports the file like any other that will not convert.
    """
    base = os.path.splitext(os.path.basename(name))[0]
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    if not slug:
        raise ValueError(
            "the file name leaves no output directory name behind - nothing in "
            "it is an ASCII letter or digit. Rename the file to convert it"
        )
    return slug


def colliding_slugs(paths):
    """{slug: [path, ...]} for the slugs more than one of these paths claims.

    "A B.docx" and "A-B.docx" reduce to the same directory name, and `convert`
    empties that directory before it writes, so the second document would
    delete the first one's parts halfway through the run and nothing would say
    so. The whole command line is checked before anything is written, because
    by the time the second file is reached the damage is already done.

    A name with no slug at all is left out rather than grouped under "":
    `slugify` refuses it, and the run reports that file on its own.
    """
    by_slug = {}
    for path in paths:
        try:
            slug = slugify(path)
        except ValueError:
            continue
        by_slug.setdefault(slug, []).append(path)
    return {slug: names for slug, names in by_slug.items() if len(names) > 1}


def _n(count, noun, plural=None):
    """ "1 drawing" or "2 drawings". The report is read by a person.

    `plural` is for the nouns the "s" rule gets wrong. The kinds of drawing are
    where that happens: "SmartArt" and "other" both come out of it as something
    nobody writes.
    """
    return f"{count} {noun}" if count == 1 else f"{count} {plural or noun + 's'}"


def figures_in(blocks):
    """Every Figure in reading order, the ones inside tables and asides included.

    A flat scan of the body sees 85 of this corpus's 101 pictures. The other 16
    are in table cells - six in the Brochure, ten in Dynamical Behavior - which
    is where the author puts pictures he wants laid out side by side. The reader
    numbers all of them in one sequence over the whole document, so a manifest
    counting only the top level reports 85 figures numbered up to 101 and leaves
    the gaps looking like losses.

    The recursion is `walk`, shared with the reader's numbering. Writing it here
    a second time is what let the count and the numbers disagree unnoticed.
    """
    return (block for block in walk(blocks) if isinstance(block, Figure))


def title_candidates(blocks):
    """Text of the body's title paragraphs, for the next phase to pick from.

    A CMS record needs a title and these documents do not agree on where it is:
    two carry a Title style, the rest open straight into a heading. Reading it
    off the style costs nothing here and is guesswork once the document is gone.

    Candidates, not a title. Sound Detection styles its byline the same way, so
    "Dr. Korkut Kaynardag" arrives as one too, and choosing between them is a
    decision for the phase that writes the record. Recording them changes
    nothing about the page: `emit` still writes these paragraphs into the body.

    Which style means a title is the reader's answer. This module knows nothing
    about Word and had no business comparing a style id to the string "Title".
    """
    out = []
    for block in blocks:
        if isinstance(block, Para) and block.role == "TITLE":
            text = "".join(r.text for r in block.runs).strip()
            if text:
                out.append(text)
    return out


def _document_xml(path_or_root):
    """The document part, parsed; a path is read, an element is passed through.

    The counts below each want the same tree, and the ML guide's is ten
    megabytes, so `convert` parses it once and hands it round. The tests hand
    a path, which is the other thing this accepts.
    """
    if not isinstance(path_or_root, str):
        return path_or_root
    with zipfile.ZipFile(path_or_root) as z:
        return etree.fromstring(z.read("word/document.xml"))


def drawing_counts(path):
    """(drawings in the body, {kind: how many} for the ones holding no picture).

    A `w:drawing` is any anchored drawing object. Only one carrying an `a:blip`
    with an `r:embed` points at a picture file, which is the test the reader
    applies; the rest were drawn in Word and have no image part to carry over,
    so they are dropped on purpose.

    Counting both is what separates a drawing deliberately dropped from a
    picture accidentally lost. Across this corpus: 105 drawings, 4 of them
    without a picture, 101 figures - so the two sides add up and nothing is
    going missing.

    The kind comes from `a:graphicData/@uri` rather than from a guess. All four
    of this corpus's blind drawings are `shape` (Word names them "Straight
    Connector"), but a chart and a SmartArt diagram look identical from the
    outside - no blip, nothing to publish - and the report has no business
    calling one a connector line because the other four were.
    """
    root = _document_xml(path)
    drawings = list(root.iter(W + "drawing"))
    kinds = {}
    for drawing in drawings:
        if any(b.get(REL + "embed") for b in drawing.iter(DRAW + "blip")):
            continue
        data = next(drawing.iter(DRAW + "graphicData"), None)
        uri = data.get("uri") if data is not None else ""
        kind = GRAPHIC_KIND.get(uri, UNNAMED_KIND)[0]
        kinds[kind] = kinds.get(kind, 0) + 1
    return len(drawings), kinds


def content_counts(path):
    """What the document holds that the page cannot hold as it is, counted
    off the XML: equations, embedded objects, note references, text boxes.

    Each is a count of what was there, beside the reader's answer to it. An
    equation is read as linear text and counted so the owner knows which
    paragraphs to look at; an embedded object - MathType above all, the one
    the author is told to convert before exporting - cannot be read at all,
    and the count is the only trace of it. Objects are keyed on their
    `ProgID`, the way drawings are keyed on their kind, so the report can say
    what they were rather than that they were.

    A text box is counted once however many times Word wrote it: the `wps`
    shape and its VML fallback under `mc:Fallback` are the same box.
    """
    root = _document_xml(path)
    objects = {}
    for obj in root.iter(W + "object"):
        ole = obj.find(OFFICE + "OLEObject")
        kind = (ole.get("ProgID") if ole is not None else None) or "other"
        objects[kind] = objects.get(kind, 0) + 1
    boxes = sum(
        1
        for b in root.iter(W + "txbxContent")
        if not any(
            a.tag in (MC + "Fallback", W + "txbxContent") for a in b.iterancestors()
        )
    )
    return {
        "equations": sum(1 for _ in root.iter(M + "oMath")),
        "objects": sum(objects.values()),
        "object_kinds": objects,
        "footnotes": sum(1 for _ in root.iter(W + "footnoteReference"))
        + sum(1 for _ in root.iter(W + "endnoteReference")),
        "text_boxes": boxes,
    }


def run_counts(blocks):
    """What the runs carry that the page changes or cannot hold, counted off
    the blocks, and the colours that reach the page.

    `internal_links` are links at a bookmark rather than a URL, outside the
    contents list: 51 of the corpus's 52 are the entries of a contents list
    the emitter drops, and the one left points at a bookmark the document
    never declares. `strikethrough_runs` are published as plain text, since
    Ricos has no strikethrough. `unmapped_symbols` are `w:sym` glyphs with no
    entry in the table, written as U+FFFD so that they can be seen and
    counted here. The colours are counted through the emitter's own rule,
    so a heading's colour, a link's, and white text are not among them.
    """
    links = struck = unmapped = colored = 0
    colors = {}
    for block in walk(blocks):
        if not isinstance(block, Para):
            continue
        for run in block.runs:
            if run.anchor and block.role != "TOC":
                links += 1
            struck += run.strike
            unmapped += run.text.count(UNMAPPED)
            color = color_on_page(run, bool(block.heading))
            if color:
                colored += 1
                colors[color] = colors.get(color, 0) + 1
    counts = {
        "internal_links": links,
        "strikethrough_runs": struck,
        "unmapped_symbols": unmapped,
        "colored_runs": colored,
    }
    return counts, dict(sorted(colors.items()))


def save_media(path, out_dir):
    """Copy the pictures out of the .docx next to the parts that reference them.

    Keyed on the zip member, so one stored picture is copied once however often
    the text points at it. Two figures naming the same file is not a collision
    to resolve: Dynamical Behavior embeds one image relationship at two places,
    and both are real pictures on the page that happen to be the same picture.
    """
    os.makedirs(out_dir, exist_ok=True)
    names = []
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            if not member.startswith("word/media/") or member.endswith("/"):
                continue
            name = os.path.basename(member)
            with open(os.path.join(out_dir, name), "wb") as fh:
                fh.write(z.read(member))
            names.append(name)
    return names


def crop_media(figures, out_dir):
    """Cut each cropped picture's file to the part Word shows; return the names
    of the files this writes beside the ones `save_media` copied.

    The crop belongs to the drawing, not to the stored picture: Word keeps the
    whole picture in the package and hides the edges where it draws it. Two
    figures of the corpus crop - Dynamical Behavior's Figure 9 its top 18.75%,
    a white slide title "Comprehensive Exam" and an empty band, the ML guide's
    Figure 10 its bottom 33.7%, blank canvas - and the page showed both whole.

    A file every one of whose figures crops it the same way is cut in place,
    so its name does not change. A file also drawn whole somewhere, or cropped
    two ways, keeps its whole self and each other crop is written as
    `<name>-crop<k>`, the figure pointing at it. The size is read back off the
    written file, so the part cannot disagree with it.
    """
    by_file = {}
    for figure in figures:
        if figure.filename:
            by_file.setdefault(figure.filename, []).append(figure)
    written = []
    for name, users in by_file.items():
        crops = []
        for figure in users:
            if figure.crop not in crops:
                crops.append(figure.crop)
        path = os.path.join(out_dir, name)
        if crops == [()] or not os.path.isfile(path):
            continue
        stem, ext = os.path.splitext(name)
        with Image.open(path) as im:
            im.load()
            whole, fmt = im.copy(), im.format
        for k, crop in enumerate(crops):
            if not crop:
                continue
            target = name if k == 0 else f"{stem}-crop{k}{ext}"
            cut = whole.crop(crop_box(whole.width, whole.height, crop))
            options = {"quality": 95} if fmt == "JPEG" else {}
            cut.save(os.path.join(out_dir, target), fmt, **options)
            if target != name:
                written.append(target)
            for figure in users:
                if figure.crop == crop:
                    figure.filename, (figure.width, figure.height) = target, cut.size
    return written


def _figure_entry(f):
    """One figure in the manifest. The layout keys are written only where the
    file says something, so a figure with nothing to add reads as it did."""
    entry = {
        "number": f.number,
        "filename": f.filename,
        "width": f.width,
        "height": f.height,
        "caption": f.caption,
    }
    if f.display_width:
        entry["word_width"], entry["word_height"] = f.display_width, f.display_height
    if f.crop:
        entry["crop"] = [round(x, 5) for x in f.crop]
    if f.inline:
        entry["inline"] = True
        if f.offset >= 0:
            entry["offset"] = f.offset
        elif f.joins:
            entry["joins"] = f.joins
    return entry


def preamble_bytes(sections, media_ids=None):
    """What the text before the first heading costs, or 0 when there is none.

    `media_ids` is the same mapping `pack` takes, and it is here for the same
    reason: a Wix media id is not the length of the filename it replaces, so
    measuring the preamble without it would measure a document nobody stores.
    Phase 1 has no ids yet and passes nothing, and the two measurements have to
    stay comparable once Phase 2 does.

    `split_at_headings` gives an untitled first section to any document that
    says anything before its first heading, and every document here does. The
    size is what tells the two cases apart. Sound Detection's preamble is its
    title and byline, 1,617 bytes; the Machine Learning guide's is 43,751,
    because the section its own contents list calls "1. What is Machine
    Learning?" was never given a heading in the body and so is not a section at
    all as far as the split can see.

    Measured on its own emitted document rather than taken from the record that
    holds it: `pack` puts every document in this corpus into one record, so the
    record's size is the whole document and says nothing about the preamble.
    """
    if not sections or sections[0][0] or not sections[0][1]:
        return 0
    return doc_bytes(emit(sections[0][1], media_ids))


def convert(path):
    """Convert one .docx into build/ricos/<slug>/, and return its manifest.

    The directory is emptied first. What is in it is the whole of what this
    document converts to, and the next phase reads it as such: a run that emits
    fewer parts than the one before, or a document whose pictures came back from
    Word under new names, would otherwise leave the old files sitting beside the
    new ones with nothing to say which is which.

    The clearing is allowed to fail. `ignore_errors=True` silenced exactly the
    case the clearing exists for: one part file held open by an editor, an
    indexer or a virus scanner - routine on Windows - and the stale file
    survives into a directory the next phase will publish, with `makedirs`
    carrying on as though the directory had been emptied. Better the document
    is reported as not converted.
    """
    slug = slugify(path)
    out_dir = os.path.join(OUT, slug)
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    blocks = read_blocks(path)
    media = save_media(path, os.path.join(out_dir, "figures"))
    media += crop_media(figures_in(blocks), os.path.join(out_dir, "figures"))
    sections = split_at_headings(blocks)
    records = pack(sections)

    for i, rec in enumerate(records, 1):
        part = os.path.join(out_dir, f"part-{i:02d}.json")
        with open(part, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec["doc"], fh, ensure_ascii=False)

    figures = list(figures_in(blocks))
    root = _document_xml(path)
    drawings, blind_kinds = drawing_counts(root)
    runs, colors = run_counts(blocks)
    referenced = {f.filename for f in figures if f.filename}
    manifest = {
        "source": os.path.basename(path),
        "slug": slug,
        "title_candidates": title_candidates(blocks),
        # The width of Word's text column in CSS px, which each figure's
        # word_width is a share of; 0 when the file does not say.
        "text_width": text_width(root),
        "records": [
            {
                "part": i,
                "titles": r["titles"],
                "bytes": r["bytes"],
                "over_limit": r["over_limit"],
            }
            for i, r in enumerate(records, 1)
        ],
        "figures": [_figure_entry(f) for f in figures],
        "media_files": sorted(media),
        "unreferenced_media": sorted(set(media) - referenced),
        # Both directions, because they fail differently. A stored picture
        # nothing points at is spare weight; a part pointing at a name
        # `figures/` does not hold is a hole on the published page, and it is
        # the direction the upload step breaks on.
        "missing_media": sorted(referenced - set(media)),
        # Hex -> runs, for the colours that reach the page. What the next
        # phase maps onto the site's palette, if it decides to.
        "colors": colors,
        "counts": {
            "blocks": len(blocks),
            "figures": len(figures),
            "figures_without_caption": sum(1 for f in figures if not f.caption),
            "figures_without_file": sum(1 for f in figures if not f.filename),
            "tables": sum(1 for b in blocks if isinstance(b, Table)),
            "callouts": sum(1 for b in blocks if isinstance(b, Callout)),
            "media_in_zip": len(media),
            "drawings": drawings,
            "drawings_without_picture": sum(blind_kinds.values()),
            "drawings_without_picture_kinds": blind_kinds,
            "headings": sum(1 for title, _ in sections if title),
            "untitled_preamble_bytes": preamble_bytes(sections),
            "rules": sum(1 for b in walk(blocks) if isinstance(b, Rule)),
            **content_counts(root),
            **runs,
        },
    }
    with open(
        os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8", newline="\n"
    ) as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    return manifest


def warnings_for(manifest):
    """What this document has to report about itself, as lines to print.

    All but the first two are findings about the document, and each line says
    whose decision made it so. The first two are the exceptions and the only
    ones here that would mean a part cannot be published as written; neither
    fires on this corpus, and if either does the fix belongs upstream of the
    manifest rather than in the document.
    """
    c = manifest["counts"]
    src = manifest["source"]
    out = []
    if c["drawings"] - c["drawings_without_picture"] != c["figures"]:
        out.append(
            f"{src}: {c['drawings']} drawings, {c['drawings_without_picture']} of them "
            f"with no picture, against {c['figures']} figures - the two do not add up, "
            f"so pictures are being lost or invented on the way through. This one is a "
            f"defect in the reader, not in the document"
        )
    if manifest["missing_media"]:
        names = ", ".join(manifest["missing_media"])
        out.append(
            f"{src}: {_n(len(manifest['missing_media']), 'figure')} naming a file "
            f"figures/ does not hold ({names}) - the relationship resolves to a "
            f"target outside word/media/, or to an external one, so the name went "
            f"into the part and no file went with it. There is nothing for the "
            f"upload to send and the picture would be a hole on the page"
        )
    if c["drawings_without_picture"]:
        kinds = ", ".join(
            _n(n, kind, KIND_PLURAL.get(kind))
            for kind, n in sorted(c["drawings_without_picture_kinds"].items())
        )
        out.append(
            f"{src}: {_n(c['drawings_without_picture'], 'drawing')} with no picture file "
            f"({kinds}) - drawn in Word, with no image part to carry over, so the drawing "
            f"is dropped rather than lost. Redraw by hand where the page needs it"
        )
    if c["figures_without_file"]:
        out.append(
            f"{src}: {_n(c['figures_without_file'], 'figure')} pointing at a relationship "
            f"the document never declares, so there is no file to publish"
        )
    if manifest["unreferenced_media"]:
        names = ", ".join(manifest["unreferenced_media"])
        out.append(
            f"{src}: {_n(len(manifest['unreferenced_media']), 'stored picture')} anchored "
            f"nowhere in the body ({names}) - copied to figures/ and used by no part"
        )
    if c["figures_without_caption"]:
        out.append(
            f"{src}: {c['figures_without_caption']} of {c['figures']} figures with no "
            f"caption, because the author wrote no caption line under them. An editorial "
            f"gap in the document; the converter folds in every caption that is there"
        )
    if c["untitled_preamble_bytes"] and not c["headings"]:
        out.append(
            f"{src}: no heading anywhere in the body, so the whole "
            f"{c['untitled_preamble_bytes']:,}-byte document is one untitled section - "
            f"there is no heading here for a record title to be taken from"
        )
    elif c["untitled_preamble_bytes"]:
        out.append(
            f"{src}: {c['untitled_preamble_bytes']:,} bytes stand before the first of its "
            f"{c['headings']} headings, under none of them - a stretch of text the author "
            f"never gave a section title, and a record with no title to be found by"
        )
    if c["objects"]:
        # A ProgID is a name, not a noun: "2 Equation.DSMT4", never with an "s".
        kinds = ", ".join(
            f"{n} {kind}" for kind, n in sorted(c["object_kinds"].items())
        )
        out.append(
            f"{src}: {_n(c['objects'], 'embedded object')} ({kinds}) - an OLE object's "
            f"content cannot be read out of the file, so nothing of it reaches the page. A "
            f"MathType equation (Equation.DSMT4) is converted in Word first: MathType > "
            f"Convert Equations > to OMML, and it is then read like any other equation"
        )
    if c["equations"]:
        out.append(
            f"{src}: {_n(c['equations'], 'equation')} written in Word's own format (OMML) "
            f"read as linear text - Ricos has no equation node, so a/b, x^2 and √(k/m) "
            f"stand for the layout. Read them on the page"
        )
    if c["footnotes"]:
        out.append(
            f"{src}: {_n(c['footnotes'], 'footnote')} - a single page has no foot, so each "
            f"is a [n] mark in the text and a [n] paragraph after the body"
        )
    if c["internal_links"]:
        verb = "points" if c["internal_links"] == 1 else "point"
        out.append(
            f"{src}: {_n(c['internal_links'], 'link')} {verb} inside the document, at a "
            f"bookmark. The words are kept and the link is not: a Ricos link needs the page "
            f"it points at, which the next phase assigns"
        )
    if c["strikethrough_runs"]:
        out.append(
            f"{src}: {_n(c['strikethrough_runs'], 'run')} struck through in Word, carried as "
            f"a STRIKETHROUGH decoration the validator has not seen (devir notu 7.7). If it "
            f"is refused the text is published plain: delete it in Word if it was deleted"
        )
    if c["unmapped_symbols"]:
        out.append(
            f"{src}: {_n(c['unmapped_symbols'], 'symbol character')} from a symbol font "
            f"this tool has no glyph for, written as {UNMAPPED} so that it can be found"
        )
    if c["text_boxes"]:
        out.append(
            f"{src}: {_n(c['text_boxes'], 'text box')} - the words are kept, as paragraphs "
            f"after the paragraph the box was anchored in; the box is not"
        )
    for r in manifest["records"]:
        if r["over_limit"]:
            out.append(
                f"{src}: part {r['part']:02d} is {r['bytes']:,} bytes, over the "
                f"{LIMIT:,}-byte record limit, and was stored whole - where to cut a "
                f"single section is an editorial decision and not this tool's to make"
            )
    return out


def main(argv):
    """Convert the documents named, or the whole corpus, and report on them.

    Returns OK, WARNINGS or FAILED - see this module's docstring for what each
    one means. The three are kept apart because they answer different questions:
    WARNINGS is what the run found in the documents, FAILED is what went wrong
    in the tool. One document that will not convert does not stop the others, so
    every file is attempted and the failures are listed at the end.
    """
    if "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return OK
    paths = argv or sorted(glob.glob(os.path.join(SOURCE, "*.docx")))
    if not paths:
        print(f"no .docx files in {SOURCE}")
        return FAILED
    clashes = colliding_slugs(paths)
    if clashes:
        print("not converted - these are errors in the conversion:")
        for slug, names in sorted(clashes.items()):
            files = ", ".join(os.path.basename(n) for n in names)
            print(
                f" x {files}: all convert to build/ricos/{slug}/, and each one "
                f"empties that directory before it writes, so only the last "
                f"would survive. Rename one of them"
            )
        return FAILED
    print(
        f"{'document':46s} {'parts':>5s} {'largest':>9s} {'figs':>5s} {'nocap':>5s} "
        f"{'tbl':>4s} {'call':>5s}"
    )
    findings, failures = [], []
    for path in paths:
        try:
            m = convert(path)
        except Exception as err:
            failures.append(f"{os.path.basename(path)}: {type(err).__name__}: {err}")
            continue
        largest = max((r["bytes"] for r in m["records"]), default=0)
        c = m["counts"]
        print(
            f"{m['source'][:46]:46s} {len(m['records']):5d} {largest:9,d} "
            f"{c['figures']:5d} {c['figures_without_caption']:5d} "
            f"{c['tables']:4d} {c['callouts']:5d}"
        )
        findings.extend(warnings_for(m))
    if findings:
        print(
            "\nwarnings - findings about the documents, not errors in the conversion:"
        )
        for line in findings:
            print(" !", line)
    if failures:
        print("\nnot converted - these are errors in the conversion:")
        for line in failures:
            print(" x", line)
        return FAILED
    return WARNINGS if findings else OK


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
