"""Where a document is cut, and how much of the 500 KB budget each piece costs.

The spec's "the ML guide is about 12 sections" is an estimate, and an estimate
is not something a record limit can be checked against. These tests pin the two
operations that turn it into a measurement: the seam, which is the author's own
top-level headings, and the count, which has to be the byte count Wix charges -
UTF-8 of the stored JSON, not the escaped ASCII `json.dumps` writes by default.
One `ş` costs 1 byte stored and 5 escaped, which over this corpus comes to 670
bytes and over the guide to 323. The escaped count only ever errs high, so it
never lets an oversized document through and instead reports one as too big for
a record it fits in - which is how it went three tasks without being noticed,
and why the test below has to subtract the two rather than compare them.

`pack` is the safety net under that measurement, not the editorial decision. It
groups consecutive sections while they fit, which means a document that fits
whole comes back as one record; it is only when the bytes force a cut that it
makes more. A single section too big to fit alone is emitted anyway and flagged,
because where to cut inside a section is the author's call, not a program's.
"""

from tools.ricos.blocks import Para, Run
from tools.ricos.emit import emit
from tools.ricos.split import LIMIT, doc_bytes, pack, split_at_headings


def _h(text):
    return Para(runs=[Run(text=text)], heading=1)


def _p(text):
    return Para(runs=[Run(text=text)])


def test_the_record_limit_is_the_number_everything_here_is_measured_against():
    """500,000 bytes: what one Wix CMS item holds across all of its fields.

    The headline constant of this phase, and nothing asserted it - raising it
    to 5,000,000 left all 132 tests green. Every "fits in one record" in the
    report is relative to it, and the guide at 362,379 bytes is 72.5% of it.
    """
    assert LIMIT == 500_000


def test_doc_bytes_counts_utf8():
    """The one byte `ş` costs stored, against the five it costs escaped.

    Subtracting two documents that differ by a single character is the only
    assertion that can tell the conventions apart. Anything comparative passes
    under both, because escaping makes a non-ASCII character bigger too - just
    six times too big.
    """
    assert doc_bytes(emit([_p("ş")])) - doc_bytes(emit([_p("s")])) == 1


def test_split_at_headings_groups_body_under_its_heading():
    blocks = [_p("intro"), _h("One"), _p("a"), _h("Two"), _p("b")]
    parts = split_at_headings(blocks)
    assert [t for t, _ in parts] == ["", "One", "Two"]
    assert len(parts[0][1]) == 1
    assert len(parts[1][1]) == 2  # heading + body


def test_an_empty_heading_is_not_a_section_boundary():
    """Two of these sit in Sound Detection and Tracking, and the emitter drops
    both: a heading with nothing written on it is a blank line the author left
    with the style still switched on, and cutting there would open a record
    with no heading at the top of it."""
    blocks = [
        _h("One"),
        _p("a"),
        Para(heading=1),
        Para(runs=[Run(text="  ")], heading=1),
        _p("b"),
    ]
    parts = split_at_headings(blocks)
    assert [t for t, _ in parts] == ["One"]
    assert len(parts[0][1]) == 5  # they stay in the flow for `emit` to drop


def test_split_with_no_headings_returns_one_part():
    parts = split_at_headings([_p("a"), _p("b")])
    assert len(parts) == 1
    assert parts[0][0] == ""


def test_pack_keeps_every_record_under_the_limit():
    """Six sections of 261 bytes at a limit that takes two of them, not one.

    A limit no two sections fit under makes this test say nothing: every record
    holds a single section, so `len(titles) == 1` is true throughout and the
    size is never looked at. At 600 two fit and three do not, so the records
    are grouped and every assertion below is answered by the packing rather
    than by the shape of the input.

    The titles are checked against the sections they came from because that is
    what a mis-ordered reset inside `pack` destroys: a record dropped there
    takes its sections with it and leaves every remaining record legal.
    """
    sections = split_at_headings([_h(f"H{i}") for i in range(6)])
    out = pack(sections, limit=600)
    assert 0 < len(out) < len(sections)
    assert [t for rec in out for t in rec["titles"]] == [t for t, _ in sections]
    for rec in out:
        assert rec["bytes"] <= 600 or len(rec["titles"]) == 1


def test_pack_reports_an_oversize_single_section():
    big = [_h("Huge")] + [_p("x" * 500) for _ in range(5)]
    out = pack(split_at_headings(big), limit=400)
    assert out[0]["over_limit"] is True


def test_pack_does_not_re_emit_the_whole_record_for_every_section(monkeypatch):
    """Quadratic in the number of sections: every section re-emitted the
    record accumulated so far to ask whether it still fit. The sum of the
    sections' own sizes is the screen; the exact measurement is kept for
    where it decides anything, within a tenth of the limit.

    Measured as blocks handed to `emit`, because the call count is the same
    either way - it is the size of each call that grew.
    """
    from tools.ricos import split

    handed = []
    real = split.emit

    def counting(blocks, media_ids=None):
        handed.append(len(blocks))
        return real(blocks, media_ids)

    monkeypatch.setattr(split, "emit", counting)
    sections = split_at_headings([_h(f"H{i}") for i in range(40)])
    out = pack(sections)
    assert len(out) == 1 and len(out[0]["titles"]) == 40
    assert sum(handed) < 3 * 40


def test_pack_still_measures_exactly_where_the_sum_comes_near_the_limit():
    """Six 261-byte sections at a limit that takes two: the sum alone would
    say three fit (783 < 800 with no wrapper) and the exact count says
    otherwise, so the record must be measured, not estimated, there."""
    sections = split_at_headings([_h(f"H{i}") for i in range(6)])
    out = pack(sections, limit=600)
    assert [len(r["titles"]) for r in out] == [2, 2, 2]
    for rec in out:
        assert rec["bytes"] == doc_bytes(rec["doc"]) <= 600
