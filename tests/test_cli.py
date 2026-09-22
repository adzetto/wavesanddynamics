"""The command line: what it writes down, and what it reports back.

Two things are pinned here.

The first is that the manifest counts every figure. Sixteen of this corpus's 101
pictures sit inside table cells - six in the Brochure, ten in Dynamical Behavior
- which is where the author puts the ones he wants laid out side by side. A flat
scan of the body sees 85 of them and says so without complaint, and because the
reader numbers figures over the whole document the undercount shows up only as
numbers running past the count.

The second is the difference between a warning and a failure. A run that
converts all seven documents and reports on them still exits non-zero, because
these documents have findings in them: pictures with no caption under them,
drawings with no picture in them, text the author left under no heading. None of
that is the conversion going wrong, and the status that means it did is another
one. A test that only asserted "non-zero" would not know the difference either.
"""
import json

import pytest
from conftest import picture, png, shape

from tools import docx2ricos
from tools.docx2ricos import (
    FAILED,
    OK,
    WARNINGS,
    colliding_slugs,
    convert,
    drawing_counts,
    figures_in,
    main,
    preamble_bytes,
    save_media,
    slugify,
    title_candidates,
    warnings_for,
)
from tools.ricos.blocks import Callout, Figure, Para, Run, Table
from tools.ricos.docx_read import read_blocks
from tools.ricos.split import pack, split_at_headings


def _docx(tmp_path, docx_factory, body, rels=None, media=None):
    """The synthetic document on disk, because the CLI opens files by name."""
    path = tmp_path / "doc.docx"
    path.write_bytes(docx_factory(body, rels=rels, media=media))
    return str(path)


def _tbl(*cells):
    """A Word table of one row; one cell makes it a Callout, two a Table."""
    return "<w:tbl><w:tr>" + "".join(f"<w:tc>{c}</w:tc>" for c in cells) + "</w:tr></w:tbl>"


def _fig(number, filename):
    return Figure(rel_id=f"rId{number}", filename=filename, number=number)


def _manifest(**counts):
    """A manifest with everything quiet, so a test says what it is about."""
    base = {"blocks": 0, "figures": 0, "figures_without_caption": 0,
            "figures_without_file": 0, "tables": 0, "callouts": 0,
            "media_in_zip": 0, "drawings": 0, "drawings_without_picture": 0,
            "drawings_without_picture_kinds": {}, "headings": 1,
            "untitled_preamble_bytes": 0}
    base.update(counts)
    if "drawings" not in counts:
        base["drawings"] = base["figures"] + base["drawings_without_picture"]
    if base["drawings_without_picture"] and not base["drawings_without_picture_kinds"]:
        base["drawings_without_picture_kinds"] = {"shape": base["drawings_without_picture"]}
    return {"source": "D.docx", "slug": "d", "unreferenced_media": [],
            "missing_media": [], "records": [], "counts": base}


def test_slugify_reduces_a_filename_to_a_folder_name():
    assert (slugify("content/source/Brochure - SHM and NDT - 2 pages.docx")
            == "brochure-shm-and-ndt-2-pages")
    assert slugify("/x/From_Bridges_to_Photons.docx") == "from-bridges-to-photons"


def test_a_name_with_nothing_ascii_in_it_is_refused():
    """The empty slug is the destructive one, and the name is not a contrivance.

    `os.path.join(OUT, "")` is OUT itself, so `convert` would empty the whole
    output tree - every document converted earlier in the same run included -
    and then write part-01.json into the root beside the directories.
    """
    with pytest.raises(ValueError):
        slugify("ŞĞÜ.docx")
    with pytest.raises(ValueError):
        slugify("____.docx")


def test_two_names_that_share_a_slug_are_found_before_anything_is_written():
    """"A B.docx" and "A-B.docx" claim one directory, and the directory is
    emptied before it is written, so the first document's parts would be gone
    by the time anyone could notice. A name with no slug at all is left to
    `slugify` to refuse rather than grouped under "".
    """
    assert colliding_slugs(["/x/A B.docx", "/y/A-B.docx", "/z/C.docx"]) == {
        "a-b": ["/x/A B.docx", "/y/A-B.docx"]}
    assert colliding_slugs(["/x/A.docx", "/y/B.docx"]) == {}
    assert colliding_slugs(["/x/ŞĞÜ.docx", "/y/ÇÖİ.docx"]) == {}


def test_figures_in_finds_the_pictures_inside_tables_and_asides():
    """The 16 a flat scan of the body misses, and the reader numbers anyway."""
    blocks = [_fig(1, "a.png"),
              Table(rows=[[[_fig(2, "b.png")], [Para()]]]),
              Callout(blocks=[_fig(3, "c.png")]),
              _fig(4, "d.png")]
    assert [f.number for f in figures_in(blocks)] == [1, 2, 3, 4]


def test_the_numbering_and_the_manifest_walk_the_same_tree(docx_factory):
    """The invariant the shared `walk` buys, end to end: the reader numbers the
    figures and the manifest counts them, and while each had its own copy of the
    recursion the count stopped at the top level while the numbers ran past it.
    """
    body = (f"<w:p>{picture('rId5')}</w:p>"
            + _tbl(f"<w:p>{picture('rId6')}</w:p>", f"<w:p>{picture('rId7')}</w:p>")
            + _tbl(f"<w:p>{picture('rId8')}</w:p>")
            + f"<w:p>{picture('rId9')}</w:p>")
    rels = {f"rId{i}": f"media/image{i}.png" for i in range(5, 10)}
    blocks = read_blocks(docx_factory(body, rels=rels))

    assert isinstance(blocks[1], Table) and isinstance(blocks[2], Callout)
    figures = list(figures_in(blocks))
    assert [f.number for f in figures] == [1, 2, 3, 4, 5]
    assert [f.filename for f in figures] == [f"image{i}.png" for i in range(5, 10)]


def test_figures_in_counts_one_picture_used_twice_as_two_figures():
    """Dynamical Behavior embeds one image relationship at two places in the
    text. Both are real pictures on the page; that they are the same file is
    not a collision to be resolved away."""
    blocks = [_fig(1, "image16.png"), _fig(2, "image16.png")]
    assert [f.number for f in figures_in(blocks)] == [1, 2]


def test_title_candidates_takes_the_title_style_and_nothing_else():
    """Candidates, not a title: Sound Detection styles its byline this way too."""
    blocks = [Para(runs=[Run(text="Understanding Sound Classification")], style="Title"),
              Para(runs=[Run(text="Dr. Korkut Kaynardag")], style="Title"),
              Para(runs=[Run(text="   ")], style="Title"),
              Para(runs=[Run(text="Three Main Stages")], style="Heading1"),
              Para(runs=[Run(text="body")])]
    assert title_candidates(blocks) == ["Understanding Sound Classification",
                                        "Dr. Korkut Kaynardag"]


def test_drawing_counts_separates_a_drawing_with_a_picture_from_one_without(
        tmp_path, docx_factory):
    """And names what the blind one holds, off a:graphicData/@uri, rather than
    calling it a connector line because the corpus's four happen to be."""
    path = _docx(tmp_path, docx_factory,
                 f"<w:p>{picture('rId5')}</w:p><w:p>{shape()}</w:p>",
                 rels={"rId5": "media/image1.png"})
    assert drawing_counts(path) == (2, {"shape": 1})


def test_a_drawing_of_an_unknown_kind_is_counted_without_being_named(
        tmp_path, docx_factory):
    body = ('<w:p><w:r><w:drawing><wp:inline><a:graphic>'
            '<a:graphicData uri="urn:something:else"/>'
            "</a:graphic></wp:inline></w:drawing></w:r></w:p>")
    assert drawing_counts(_docx(tmp_path, docx_factory, body)) == (1, {"other": 1})


def test_save_media_copies_the_pictures_and_skips_the_directory_entry(
        tmp_path, docx_factory):
    """From_Bridges_to_Photons stores a `word/media/` entry of its own. Its
    basename is the empty string, so copying it as though it were a file opens
    the output directory for writing and the whole run dies on one document."""
    path = _docx(tmp_path, docx_factory, "<w:p/>",
                 media={"word/media/": b"", "word/media/image1.png": b"PNG"})
    out = tmp_path / "figures"
    assert save_media(path, str(out)) == ["image1.png"]
    assert (out / "image1.png").read_bytes() == b"PNG"


def test_preamble_bytes_measures_the_preamble_and_not_the_record_holding_it():
    """`pack` puts every document in this corpus into one record, so the
    record's size is the whole document and says nothing about the preamble."""
    sections = split_at_headings([Para(runs=[Run(text="opening line")]),
                                  Para(runs=[Run(text="One")], style="Heading1"),
                                  Para(runs=[Run(text="x" * 2000)])])
    assert 0 < preamble_bytes(sections) < pack(sections)[0]["bytes"] - 2000


def test_preamble_bytes_measures_against_the_media_ids_it_is_given():
    """`pack` takes the mapping and this did not, so once Phase 2 has real ids
    the preamble would be measured against filenames while the records it is
    compared with were measured against Wix ids - and a media id is not the
    length of the name it stands in for.
    """
    sections = [("", [Para(runs=[Run(text="opening line")]),
                      Figure(filename="i.png", width=1, height=1)])]
    assert (preamble_bytes(sections, media_ids={"i.png": "ce0a40_9f3b21~mv2.png"})
            == preamble_bytes(sections) + len("ce0a40_9f3b21~mv2.png") - len("i.png"))


def test_preamble_bytes_is_zero_when_the_document_opens_on_a_heading():
    sections = split_at_headings([Para(runs=[Run(text="One")], style="Heading1")])
    assert preamble_bytes(sections) == 0


def test_a_drawing_with_no_picture_is_reported_as_dropped_on_purpose():
    """Four of the 105, and the line names the kind instead of asserting one."""
    (line,) = warnings_for(_manifest(drawings=4, figures=3,
                                     drawings_without_picture=1,
                                     drawings_without_picture_kinds={"chart": 1}))
    assert "1 drawing with no picture file (1 chart)" in line
    assert "dropped rather than lost" in line
    assert "defect" not in line


def test_a_picture_that_reaches_no_figure_is_reported_as_a_defect_here():
    """The one warning in the set that is not about the document. It does not
    fire on this corpus - 105 drawings, 4 blind, 101 figures - and if it ever
    does, the fix belongs in the reader."""
    lines = warnings_for(_manifest(drawings=4, drawings_without_picture=1, figures=2))
    assert any("defect in the reader, not in the document" in ln for ln in lines)


def test_the_kinds_in_the_parenthetical_are_plural_when_there_are_several():
    """Today's real output prints "(2 shape)", in the report a person reads.

    The plural sits beside the name rather than being guessed, because the
    guess - add an "s" - gets two of the five kinds wrong: "2 SmartArts" and
    "1 others" are not what anyone writes.
    """
    (one,) = warnings_for(_manifest(drawings_without_picture=1,
                                    drawings_without_picture_kinds={"shape": 1}))
    assert "(1 shape)" in one
    (many,) = warnings_for(_manifest(drawings_without_picture=2,
                                     drawings_without_picture_kinds={"shape": 2}))
    assert "(2 shapes)" in many
    (mixed,) = warnings_for(
        _manifest(drawings_without_picture=4,
                  drawings_without_picture_kinds={"SmartArt": 2, "chart": 1,
                                                  "other": 1}))
    assert "(2 SmartArt graphics, 1 chart, 1 other)" in mixed


def test_an_uncaptioned_figure_is_reported_as_the_authors_gap():
    """23 of Signal Processing's 26 have none, because he wrote no caption line
    under them. Editorial, and not the converter dropping captions."""
    (line,) = warnings_for(_manifest(figures=26, figures_without_caption=23))
    assert "the author wrote no caption line under them" in line
    assert "defect" not in line


def test_the_report_agrees_with_itself_about_one_and_many():
    """Understanding_SHM_and_NDT has exactly one uncaptioned figure, and one
    document in the run reading "1 of 6 figures carry" is how a report stops
    being trusted."""
    (line,) = warnings_for(_manifest(figures=6, figures_without_caption=1))
    assert "1 of 6 figures with no caption" in line
    (one,) = warnings_for(_manifest(figures=1, figures_without_file=1))
    assert "1 figure pointing at" in one
    (many,) = warnings_for(_manifest(figures=2, figures_without_file=2))
    assert "2 figures pointing at" in many


def test_a_stored_picture_nothing_anchors_is_reported_by_name():
    m = _manifest(media_in_zip=2, figures=1)
    m["unreferenced_media"] = ["image2.png"]
    (line,) = warnings_for(m)
    assert "image2.png" in line and "used by no part" in line


def test_a_figure_pointing_at_no_relationship_is_reported():
    (line,) = warnings_for(_manifest(figures=1, figures_without_file=1))
    assert "no file to publish" in line


def test_a_figure_whose_file_never_reached_the_directory_is_reported():
    """The direction that breaks the upload, and the one nothing checked.

    `_figure` resolves whatever target the relationship names, `TargetMode=
    "External"` and anything outside `word/media/` included, and hands back its
    basename - which the emitter writes into `src.id`. `save_media` copies only
    what is under `word/media/`, so the part names a picture `figures/` does
    not hold. Empty on this corpus, and reachable the first time a picture is
    linked instead of embedded.
    """
    m = _manifest(figures=1, media_in_zip=0)
    m["missing_media"] = ["linked.png"]
    (line,) = warnings_for(m)
    assert "linked.png" in line and "figures/ does not hold" in line


def test_a_document_with_no_heading_at_all_is_one_untitled_section():
    """The Brochure and From Bridges to Photons: no Heading1 anywhere."""
    (line,) = warnings_for(_manifest(headings=0, untitled_preamble_bytes=18_627))
    assert "no heading anywhere" in line and "18,627" in line


def test_a_preamble_beneath_headings_is_reported_at_its_own_size():
    """The Machine Learning guide: 11 headings in the body, and 43,751 bytes in
    front of the first of them that were never given one."""
    (line,) = warnings_for(_manifest(headings=11, untitled_preamble_bytes=43_751))
    assert "43,751 bytes stand before the first of its 11 headings" in line


def test_an_over_limit_record_is_reported_by_part_number():
    m = _manifest()
    m["records"] = [{"part": 1, "titles": ["A"], "bytes": 600_000, "over_limit": True}]
    (line,) = warnings_for(m)
    assert "part 01" in line and "600,000" in line


def test_convert_writes_the_parts_the_figures_and_the_manifest(
        tmp_path, monkeypatch, docx_factory, para_factory):
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    body = (para_factory("Opening", style="Title")
            + f"<w:p>{picture('rId5')}</w:p>"
            + para_factory("Figure 1. A caption.")
            + para_factory("One", style="Heading1")
            + para_factory("body")
            + f"<w:p>{shape()}</w:p>")
    path = _docx(tmp_path, docx_factory, body, rels={"rId5": "media/image1.png"},
                 media={"word/media/image1.png": png(640, 480)})

    manifest = convert(path)
    out = tmp_path / "ricos" / "doc"

    assert json.loads((out / "part-01.json").read_text(encoding="utf-8"))["nodes"]
    assert (out / "figures" / "image1.png").read_bytes() == png(640, 480)
    assert json.loads((out / "manifest.json").read_text(encoding="utf-8")) == manifest
    assert manifest["title_candidates"] == ["Opening"]
    # A real picture, because the next phase lays the page out from these two
    # numbers. The fixture used to be bytes Pillow cannot open, so `width` and
    # `height` were 0 - the same value a failure produces, which made the
    # assertion agree with the code whatever the code did.
    assert manifest["figures"] == [{"number": 1, "filename": "image1.png",
                                    "width": 640, "height": 480,
                                    "caption": "Figure 1. A caption."}]
    assert manifest["counts"]["drawings"] == 2
    assert manifest["counts"]["drawings_without_picture"] == 1
    assert manifest["counts"]["headings"] == 1
    assert manifest["records"][0]["titles"] == ["", "One"]


def test_a_stored_picture_no_paragraph_anchors_reaches_the_manifest(
        tmp_path, monkeypatch, docx_factory, para_factory):
    """Both media lists, measured through `convert` rather than built by hand.

    Hard-coding `unreferenced_media` to `[]` left every test green: the only
    assertion on it handed `warnings_for` a manifest a test had written, so
    nothing checked that `convert` ever puts a name in it. The other direction
    is asserted here too, empty, which is what this corpus produces.
    """
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    path = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1")
                 + f"<w:p>{picture('rId5')}</w:p>",
                 rels={"rId5": "media/image1.png"},
                 media={"word/media/image1.png": png(4, 4),
                        "word/media/image9.png": png(5, 5)})

    manifest = convert(path)
    assert manifest["media_files"] == ["image1.png", "image9.png"]
    assert manifest["unreferenced_media"] == ["image9.png"]
    assert manifest["missing_media"] == []


def test_a_figure_pointing_outside_word_media_is_in_the_manifest_as_missing(
        tmp_path, monkeypatch, docx_factory, para_factory):
    """The direction that breaks Phase 2's upload, end to end.

    `_figure` resolves whatever the relationship names, so a target outside
    `word/media/` still yields a basename and that name goes into `src.id`.
    `save_media` copies only what is under `word/media/`, so the part names a
    picture `figures/` does not hold. Empty on today's corpus and reachable the
    first time a picture is linked rather than embedded.
    """
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    path = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1")
                 + f"<w:p>{picture('rId5')}</w:p>",
                 rels={"rId5": "../customXml/elsewhere.png"},
                 media={"word/customXml/elsewhere.png": png(4, 4)})

    manifest = convert(path)
    assert manifest["figures"][0]["filename"] == "elsewhere.png"
    assert manifest["media_files"] == []
    assert manifest["missing_media"] == ["elsewhere.png"]
    assert any("figures/ does not hold" in line for line in warnings_for(manifest))


def test_convert_clears_what_an_earlier_run_left_behind(
        tmp_path, monkeypatch, docx_factory, para_factory):
    """The directory is the published contract, so a part or a picture that no
    longer belongs to the document must not survive into the next run."""
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    out = tmp_path / "ricos" / "doc"
    (out / "figures").mkdir(parents=True)
    (out / "part-09.json").write_text("{}", encoding="utf-8")
    (out / "figures" / "renamed-since.png").write_bytes(b"old")

    convert(_docx(tmp_path, docx_factory,
                  para_factory("One", style="Heading1") + para_factory("body")))

    assert not (out / "part-09.json").exists()
    assert not (out / "figures" / "renamed-since.png").exists()
    assert (out / "part-01.json").exists()


def test_a_directory_that_will_not_clear_is_not_written_into(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    """One part file held open - an editor, an indexer, a virus scanner, all
    routine on Windows - used to be swallowed: the clearing failed, `makedirs`
    carried on, and the stale part survived into the published directory. The
    document is reported as not converted instead.
    """
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    (tmp_path / "ricos" / "doc").mkdir(parents=True)

    def held_open(_path):
        raise PermissionError(13, "used by another process")

    monkeypatch.setattr(docx2ricos.shutil, "rmtree", held_open)
    path = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1") + para_factory("body"))
    assert main([path]) == FAILED
    assert "PermissionError" in capsys.readouterr().out


def test_a_name_that_leaves_no_directory_stops_that_document_and_not_the_run(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    body = para_factory("One", style="Heading1") + para_factory("body")
    bad = tmp_path / "ŞĞÜ.docx"
    bad.write_bytes(docx_factory(body))
    good = _docx(tmp_path, docx_factory, body)

    assert main([str(bad), good]) == FAILED
    out = capsys.readouterr().out
    assert "ValueError" in out
    assert (tmp_path / "ricos" / "doc" / "part-01.json").exists()
    assert not (tmp_path / "ricos" / "part-01.json").exists()


def test_two_documents_claiming_one_directory_stop_the_run(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    """Before anything is written: the first document's parts would already be
    deleted by the time the second one reached them."""
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    body = para_factory("One", style="Heading1") + para_factory("body")
    first = tmp_path / "A B.docx"
    second = tmp_path / "A-B.docx"
    for path in (first, second):
        path.write_bytes(docx_factory(body))

    assert main([str(first), str(second)]) == FAILED
    assert "only the last would survive" in capsys.readouterr().out
    assert not (tmp_path / "ricos").exists()


def test_a_run_with_nothing_to_report_exits_clean(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    path = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1") + para_factory("body"))
    assert main([path]) == OK
    assert "!" not in capsys.readouterr().out


def test_a_run_that_converted_everything_and_found_something_is_not_a_failure(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    """This is what all seven documents do, and it is the report working."""
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    path = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1") + f"<w:p>{picture('rId5')}</w:p>",
                 rels={"rId5": "media/image1.png"},
                 media={"word/media/image1.png": b"PNG"})
    assert main([path]) == WARNINGS
    out = capsys.readouterr().out
    assert "findings about the documents, not errors in the conversion" in out
    assert "errors in the conversion:" not in out.split("warnings -")[0]


def test_a_document_that_cannot_be_converted_exits_differently(
        tmp_path, monkeypatch, capsys):
    bad = tmp_path / "broken.docx"
    bad.write_bytes(b"not a zip at all")
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    assert main([str(bad)]) == FAILED
    out = capsys.readouterr().out
    assert "not converted - these are errors in the conversion:" in out
    assert "BadZipFile" in out


def test_one_document_failing_does_not_stop_the_others(
        tmp_path, monkeypatch, docx_factory, para_factory, capsys):
    bad = tmp_path / "broken.docx"
    bad.write_bytes(b"not a zip at all")
    monkeypatch.setattr(docx2ricos, "OUT", str(tmp_path / "ricos"))
    good = _docx(tmp_path, docx_factory,
                 para_factory("One", style="Heading1") + para_factory("body"))
    assert main([str(bad), good]) == FAILED
    assert "doc.docx" in capsys.readouterr().out


def test_help_says_what_a_non_zero_exit_means(capsys):
    assert main(["--help"]) == OK
    out = capsys.readouterr().out
    assert "a finding about a" in out
    assert "2  a document could not be converted" in out


def test_help_is_recognised_wherever_it_appears(capsys):
    """It is the answer to the whole command line, not to its first word."""
    assert main(["some.docx", "-h"]) == OK
    assert "python tools/docx2ricos.py" in capsys.readouterr().out
