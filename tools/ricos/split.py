"""Cut a document into records, and count what each one costs.

A CMS item holds 500,000 bytes across all of its fields, and a Rich Content
field counts against that. The spec assumed the limit forces the Machine
Learning guide apart, into "about 12 sections". Measured, it does not: the
guide emits 362,379 bytes, and its largest chapter 56,454, so every document in
this corpus fits in one record with room over. This module is where that
estimate became a measurement.

Two different questions are answered here and they must not be confused. `pack`
answers the hard one - does this fit in a record at all - by grouping
consecutive sections until the next one would push the record over, so a
document that fits whole comes back as a single record, which is what the whole
corpus now does. `split_at_headings` answers the editorial one: where would a
reader cut it. The seam is the author's own top-level headings, the seam he
already wrote into the documents, and a chapter per record is what gives each
chapter its own page, its own title and its own address to be found at. Bytes
are the floor, not the reason.

Counting has to be the count Wix charges. `json.dumps` escapes every non-ASCII
character to `\\uXXXX` unless told otherwise, and six ASCII characters where
UTF-8 stores two is not what the field holds. It errs high - 670 bytes across
this corpus, 323 of them in the guide - which is small only because these
documents are almost all ASCII, and would not stay small for a document written
in Turkish. `doc_bytes` counts the bytes that are actually stored.
"""
import json

from tools.ricos.blocks import Para
from tools.ricos.emit import emit

LIMIT = 500_000


def doc_bytes(doc):
    """Bytes the document occupies once stored, the way the limit counts it.

    UTF-8 of the unescaped JSON. `ensure_ascii` is not a detail: left at its
    default it turns every accented letter into six ASCII characters and counts
    them all.
    """
    return len(json.dumps(doc, ensure_ascii=False).encode("utf-8"))


def _heading_text(block, level):
    """The heading's text, or None when this block is not a seam of `level`.

    A heading with nothing written on it is not a seam. There are two of them,
    both in Sound Detection and Tracking, and they are a blank line the author
    left with the heading style still switched on: `emit` drops them, so a cut
    there opens a record whose first line is missing. Answering None keeps the
    blank paragraph in the flow, where the emitter deletes it as it deletes
    every other one.

    The level is the one the reader put on the paragraph, not a style id built
    back up as `f"Heading{level}"`. That spelling is Word's and only Word's,
    and a document that writes it any other way used to come through here as
    one seamless section with nothing said about it.

    Guarding it here rather than asking callers to filter first is deliberate.
    The precondition would be invisible and the failure silent - two extra
    untitled records - and a precondition nobody can see is how these two empty
    headings survived as far as the emitter in the first place.
    """
    if not isinstance(block, Para):
        return None
    if block.heading != level:
        return None
    return "".join(r.text for r in block.runs).strip() or None


def split_at_headings(blocks, level=1):
    """[(title, blocks)] - anything before the first heading gets an empty title.

    The heading stays inside its own section. It is the section's own title on
    the page, and dropping it here would cost the record its opening line.

    An empty title therefore means the preamble and nothing else: every other
    part is named, because a nameless heading is not treated as a seam.

    An untitled first part is not a defect to be papered over. The ML guide's
    contents list names twelve sections and its body carries eleven headings:
    the first section was never given one, and its text is real. It arrives
    here as a preamble with an empty title, and naming it is the author's job.
    """
    parts = [("", [])]
    for block in blocks:
        title = _heading_text(block, level)
        if title is not None:
            parts.append((title, [block]))
        else:
            parts[-1][1].append(block)
    if not parts[0][1]:
        parts.pop(0)
    return parts or [("", [])]


def pack(sections, limit=LIMIT, media_ids=None):
    """Group consecutive sections into records, none larger than `limit`.

    Each record is a dict of four keys, and they are the whole interface the
    CLI above this has to know:

        titles      : [str] - the sections in this record, in order. A list
                      because one record may span several; `titles[0] == ""`
                      is the untitled preamble, and only the first record can
                      carry one.
        doc         : the Ricos document, ready to store
        bytes       : `doc_bytes(doc)`
        over_limit  : `bytes > limit`, when the record is one section that was
                      already too big on its own

    This is the safety net, not the editorial split: it cuts only where the
    bytes force it, so a whole document that fits comes back as one record.

    A single section that is already too big is emitted alone and flagged
    rather than silently cut, because where to cut it is an editorial decision.

    A section with no blocks in it produces no record and its title goes with
    it: `pack([("A", [])])` is `[]`. Nothing here makes one - a section from
    `split_at_headings` always holds at least its own heading - so this is a
    statement about hand-built input rather than a case to guard.

    Each record is measured on its own emitted document rather than by adding
    up its sections, because it is not additive - the wrapper is paid once per
    record, and `emit` numbers nodes from `n1` in each one.

    That measurement is why this is quadratic in the number of sections: every
    section re-emits the record accumulated so far to ask whether it still
    fits. At 47 sections that is the whole corpus in a fraction of a second, so
    it is left simple. The way to make it cheap is not to add section sizes up
    instead - the paragraph above is why that is not a sound count, and it is
    wrong in both directions: the ML guide's twelve sections come to 712 bytes
    *less* than the one record they partition, while Dynamical's eleven come to
    399 more. Use the sum as a cheap screen and re-emit only once it comes
    within a margin of the limit; the answer stays exact where it decides
    anything.
    """
    out = []
    cur_titles, cur_blocks = [], []

    def flush():
        """Close the record being accumulated and start an empty one.

        The reset lives in here on purpose. With it at the call sites, `flush`
        reads two names the loop rebinds, and a reset written one line too
        early loses a whole section with nothing to show for it.
        """
        nonlocal cur_titles, cur_blocks
        if cur_blocks:
            doc = emit(cur_blocks, media_ids)
            size = doc_bytes(doc)
            out.append({"titles": list(cur_titles), "doc": doc,
                        "bytes": size, "over_limit": size > limit})
        cur_titles, cur_blocks = [], []

    for title, blocks in sections:
        trial = emit(cur_blocks + blocks, media_ids)
        if cur_blocks and doc_bytes(trial) > limit:
            flush()
        cur_titles.append(title)
        cur_blocks.extend(blocks)
    flush()
    return out
