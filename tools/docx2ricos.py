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
if sys.path and os.path.abspath(sys.path[0]) == os.path.dirname(os.path.abspath(__file__)):
    sys.path[0] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from lxml import etree

from tools.ricos.blocks import Callout, Figure, Para, Table
from tools.ricos.docx_read import read_blocks
from tools.ricos.emit import emit
from tools.ricos.split import LIMIT, doc_bytes, pack, split_at_headings

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "build", "ricos")
SOURCE = os.path.join(HERE, "content", "source")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DRAW = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

OK, WARNINGS, FAILED = 0, 1, 2


def slugify(name):
    base = os.path.splitext(os.path.basename(name))[0]
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def figures_in(blocks):
    """Every Figure in reading order, the ones inside tables and asides included.

    A flat scan of the body sees 85 of this corpus's 101 pictures. The other 16
    are in table cells - six in the Brochure, ten in Dynamical Behavior - which
    is where the author puts pictures he wants laid out side by side. The reader
    numbers all of them in one sequence over the whole document, so a manifest
    counting only the top level would report 85 figures numbered up to 101 and
    leave the gaps looking like losses.
    """
    for block in blocks:
        if isinstance(block, Figure):
            yield block
        elif isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    yield from figures_in(cell)
        elif isinstance(block, Callout):
            yield from figures_in(block.blocks)


def title_candidates(blocks):
    """Text of the body's Title-styled paragraphs, for the next phase to pick from.

    A CMS record needs a title and these documents do not agree on where it is:
    two carry a Title style, the rest open straight into a heading. Reading it
    off the style costs nothing here and is guesswork once the document is gone.

    Candidates, not a title. Sound Detection styles its byline the same way, so
    "Dr. Korkut Kaynardag" arrives as one too, and choosing between them is a
    decision for the phase that writes the record. Recording them changes
    nothing about the page: `emit` still writes these paragraphs into the body.
    """
    out = []
    for block in blocks:
        if isinstance(block, Para) and block.style == "Title":
            text = "".join(r.text for r in block.runs).strip()
            if text:
                out.append(text)
    return out


def drawing_counts(path):
    """(drawings in the body, how many of them hold no picture).

    A `w:drawing` is any anchored drawing object. Only one carrying an `a:blip`
    with an `r:embed` points at a picture file, which is the test the reader
    applies; the rest are connector lines and shapes drawn in Word, with no
    image to carry over, and they are dropped on purpose.

    Counting both is what separates a drawing deliberately dropped from a
    picture accidentally lost. Across this corpus: 105 drawings, 4 of them
    without a picture, 101 figures - so the two sides add up and nothing is
    going missing.
    """
    with zipfile.ZipFile(path) as z:
        root = etree.fromstring(z.read("word/document.xml"))
    drawings = list(root.iter(W + "drawing"))
    blind = sum(1 for d in drawings
                if not any(b.get(REL + "embed") for b in d.iter(DRAW + "blip")))
    return len(drawings), blind


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


def preamble_bytes(sections):
    """What the text before the first heading costs, or 0 when there is none.

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
    return doc_bytes(emit(sections[0][1]))


def convert(path):
    """Convert one .docx into build/ricos/<slug>/, and return its manifest."""
    slug = slugify(path)
    out_dir = os.path.join(OUT, slug)
    os.makedirs(out_dir, exist_ok=True)

    blocks = read_blocks(path)
    media = save_media(path, os.path.join(out_dir, "figures"))
    sections = split_at_headings(blocks)
    records = pack(sections)

    for i, rec in enumerate(records, 1):
        part = os.path.join(out_dir, f"part-{i:02d}.json")
        with open(part, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec["doc"], fh, ensure_ascii=False)

    figures = list(figures_in(blocks))
    drawings, drawings_without_picture = drawing_counts(path)
    referenced = {f.filename for f in figures if f.filename}
    manifest = {
        "source": os.path.basename(path),
        "slug": slug,
        "title_candidates": title_candidates(blocks),
        "records": [{"part": i, "titles": r["titles"], "bytes": r["bytes"],
                     "over_limit": r["over_limit"]}
                    for i, r in enumerate(records, 1)],
        "figures": [{"number": f.number, "filename": f.filename,
                     "width": f.width, "height": f.height,
                     "caption": f.caption} for f in figures],
        "media_files": sorted(media),
        "unreferenced_media": sorted(set(media) - referenced),
        "counts": {
            "blocks": len(blocks),
            "figures": len(figures),
            "figures_without_caption": sum(1 for f in figures if not f.caption),
            "figures_without_file": sum(1 for f in figures if not f.filename),
            "tables": sum(1 for b in blocks if isinstance(b, Table)),
            "callouts": sum(1 for b in blocks if isinstance(b, Callout)),
            "media_in_zip": len(media),
            "drawings": drawings,
            "drawings_without_picture": drawings_without_picture,
            "headings": sum(1 for title, _ in sections if title),
            "untitled_preamble_bytes": preamble_bytes(sections),
        },
    }
    with open(os.path.join(out_dir, "manifest.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    return manifest


def warnings_for(manifest):
    """What this document has to report about itself, as lines to print.

    All but the first are findings about the document, and each line says whose
    decision made it so. The first is the exception and the only one here that
    would mean the converter lost something; it does not fire on this corpus,
    and if it ever does the fix belongs in the reader.
    """
    c = manifest["counts"]
    src = manifest["source"]
    out = []
    if c["drawings"] - c["drawings_without_picture"] != c["figures"]:
        out.append(
            f"{src}: {c['drawings']} drawings, {c['drawings_without_picture']} of them "
            f"with no picture, against {c['figures']} figures - the two do not add up, "
            f"so pictures are being lost or invented on the way through. This one is a "
            f"defect in the reader, not in the document")
    if c["drawings_without_picture"]:
        out.append(
            f"{src}: {c['drawings_without_picture']} drawing(s) hold no picture - "
            f"connector lines and shapes drawn in Word, correctly dropped because there "
            f"is no image to carry over. Redraw them by hand if the page needs them")
    if c["figures_without_file"]:
        out.append(
            f"{src}: {c['figures_without_file']} figure(s) point at a relationship the "
            f"document never declares, so there is no file to publish for them")
    if manifest["unreferenced_media"]:
        names = ", ".join(manifest["unreferenced_media"])
        out.append(
            f"{src}: {len(manifest['unreferenced_media'])} stored picture(s) are anchored "
            f"nowhere in the body ({names}) - copied to figures/ and used by no part")
    if c["figures_without_caption"]:
        out.append(
            f"{src}: {c['figures_without_caption']} of {c['figures']} figures carry no "
            f"caption, because the author wrote no caption line under them. An editorial "
            f"gap in the document; the converter folds in every caption that is there")
    if c["untitled_preamble_bytes"] and not c["headings"]:
        out.append(
            f"{src}: no heading anywhere in the body, so the whole "
            f"{c['untitled_preamble_bytes']:,}-byte document is one untitled section - "
            f"there is no heading here for a record title to be taken from")
    elif c["untitled_preamble_bytes"]:
        out.append(
            f"{src}: {c['untitled_preamble_bytes']:,} bytes stand before the first of its "
            f"{c['headings']} headings, under none of them - a stretch of text the author "
            f"never gave a section title, and a record with no title to be found by")
    for r in manifest["records"]:
        if r["over_limit"]:
            out.append(
                f"{src}: part {r['part']:02d} is {r['bytes']:,} bytes, over the "
                f"{LIMIT:,}-byte record limit, and was stored whole - where to cut a "
                f"single section is an editorial decision and not this tool's to make")
    return out


def main(argv):
    """Convert the documents named, or the whole corpus, and report on them.

    Returns OK, WARNINGS or FAILED - see this module's docstring for what each
    one means. The three are kept apart because they answer different questions:
    WARNINGS is what the run found in the documents, FAILED is what went wrong
    in the tool. One document that will not convert does not stop the others, so
    every file is attempted and the failures are listed at the end.
    """
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__.strip())
        return OK
    paths = argv or sorted(glob.glob(os.path.join(SOURCE, "*.docx")))
    if not paths:
        print(f"no .docx files in {SOURCE}")
        return FAILED
    print(f"{'document':46s} {'parts':>5s} {'largest':>9s} {'figs':>5s} {'nocap':>5s} "
          f"{'tbl':>4s} {'call':>5s}")
    findings, failures = [], []
    for path in paths:
        try:
            m = convert(path)
        except Exception as err:
            failures.append(f"{os.path.basename(path)}: {type(err).__name__}: {err}")
            continue
        largest = max((r["bytes"] for r in m["records"]), default=0)
        c = m["counts"]
        print(f"{m['source'][:46]:46s} {len(m['records']):5d} {largest:9,d} "
              f"{c['figures']:5d} {c['figures_without_caption']:5d} "
              f"{c['tables']:4d} {c['callouts']:5d}")
        findings.extend(warnings_for(m))
    if findings:
        print("\nwarnings - findings about the documents, not errors in the conversion:")
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
