"""Where a document is cut, and how much of the 500 KB budget each piece costs.

The spec's "the ML guide is about 12 sections" is an estimate, and an estimate
is not something a record limit can be checked against. These tests pin the two
operations that turn it into a measurement: the seam, which is the author's own
top-level headings, and the count, which has to be the byte count Wix charges -
UTF-8 of the stored JSON, not the escaped ASCII `json.dumps` writes by default.
The two differ by thousands of bytes on a document full of Turkish names, em
dashes and Greek letters, and they differ in the direction that matters, so the
wrong one would report a document as too big for a record it fits in.

`pack` is the safety net under that measurement, not the editorial decision. It
groups consecutive sections while they fit, which means a document that fits
whole comes back as one record; it is only when the bytes force a cut that it
makes more. A single section too big to fit alone is emitted anyway and flagged,
because where to cut inside a section is the author's call, not a program's.
"""
from tools.ricos.blocks import Para, Run
from tools.ricos.emit import emit
from tools.ricos.split import doc_bytes, pack, split_at_headings


def _h(text):
    return Para(runs=[Run(text=text)], style="Heading1")


def _p(text):
    return Para(runs=[Run(text=text)])


def test_doc_bytes_counts_utf8():
    assert doc_bytes(emit([_p("iş")])) > 0
    assert doc_bytes(emit([_p("is")])) < doc_bytes(emit([_p("işşşşşşşşşş")]))


def test_split_at_headings_groups_body_under_its_heading():
    blocks = [_p("intro"), _h("One"), _p("a"), _h("Two"), _p("b")]
    parts = split_at_headings(blocks)
    assert [t for t, _ in parts] == ["", "One", "Two"]
    assert len(parts[0][1]) == 1
    assert len(parts[1][1]) == 2      # heading + body


def test_split_with_no_headings_returns_one_part():
    parts = split_at_headings([_p("a"), _p("b")])
    assert len(parts) == 1
    assert parts[0][0] == ""


def test_pack_keeps_every_record_under_the_limit():
    sections = split_at_headings([_h(f"H{i}") for i in range(6)])
    out = pack(sections, limit=400)
    assert out
    for rec in out:
        assert rec["bytes"] <= 400 or len(rec["titles"]) == 1


def test_pack_reports_an_oversize_single_section():
    big = [_h("Huge")] + [_p("x" * 500) for _ in range(5)]
    out = pack(split_at_headings(big), limit=400)
    assert out[0]["over_limit"] is True
