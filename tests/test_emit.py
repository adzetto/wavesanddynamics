"""The node shapes Wix will accept, pinned down.

Ricos rejects nothing at write time: a node with the wrong field name is stored
and simply renders as nothing, so a mistake here surfaces as a blank section on
the live site rather than as an error. These tests hold the shapes to what the
client's own published post actually contains, and to what the published
ricos-schema typings declare.
"""
import json

from tools.ricos.blocks import Para, Run
from tools.ricos.emit import Ids, _para, emit


def test_paragraph_wraps_text_node():
    doc = emit([Para(runs=[Run(text="Hello")])])
    node = doc["nodes"][0]
    assert node["type"] == "PARAGRAPH"
    assert node["nodes"][0]["type"] == "TEXT"
    assert node["nodes"][0]["textData"]["text"] == "Hello"
    assert node["nodes"][0]["id"] == ""


def test_heading_becomes_heading_node():
    doc = emit([Para(runs=[Run(text="Closing Thoughts")], style="Heading1")])
    node = doc["nodes"][0]
    assert node["type"] == "HEADING"
    assert node["headingData"]["level"] == 1


def test_bold_run_carries_decoration():
    doc = emit([Para(runs=[Run(text="x", bold=True)])])
    decs = doc["nodes"][0]["nodes"][0]["textData"]["decorations"]
    assert {"type": "BOLD", "fontWeightValue": 700} in decs


def test_para_keeps_empty_paragraph_for_cell_placeholder():
    """The body drops these, but a table cell's placeholder keeps the grid
    rectangular and has to survive, so the node it gets still matters: an empty
    paragraph is a node with no children, never a TEXT holding "". That is the
    shape cell emission will take from `_para`, which filters nothing.
    """
    node = _para(Para(runs=[]), Ids())
    assert node["nodes"] == []


def test_italic_underline_and_link_runs_carry_their_decorations():
    """The three shapes this module exists to pin down.

    Only BOLD was verified from a published Wix example; these three were read
    off the ricos-schema typings (v10.102.0): ItalicDecoration l.219,
    UnderlineDecoration l.229, LinkDecoration l.269 with LinkData l.308 and
    Link.url l.73. The whole dict is asserted, not just the type, because a
    renamed data field is stored without complaint and then renders as nothing.
    """
    run = Run(text="x", italic=True, underline=True, link="https://x.test/p")
    decs = emit([Para(runs=[run])])["nodes"][0]["nodes"][0]["textData"]["decorations"]
    assert {"type": "ITALIC", "italicData": True} in decs
    assert {"type": "UNDERLINE", "underlineData": True} in decs
    assert {"type": "LINK", "linkData": {"link": {"url": "https://x.test/p"}}} in decs


def test_empty_paragraph_is_not_emitted_in_the_body():
    doc = emit([Para(runs=[Run(text="a")]), Para(runs=[]), Para(runs=[Run(text="b")])])
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["a", "b"]


def test_whitespace_only_paragraph_is_not_emitted_in_the_body():
    """Spacing the author typed instead of leaving blank: same stray block."""
    doc = emit([Para(runs=[Run(text="a")]), Para(runs=[Run(text="        ")])])
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["a"]


def test_contents_list_paragraph_is_not_emitted():
    """TOC1-TOC9 is a hand-typed contents list: redundant, and glued to the page
    numbers it was typed with.

    TOCHeading is the near-miss the `$` anchor in TOC_STYLE exists for: it is
    the word "Contents" itself, a real heading, and it stays.
    """
    blocks = [Para(runs=[Run(text="1. What is Machine Learning?\t2")], style="TOC1"),
              Para(runs=[Run(text="body")], style="TOC9"),
              Para(runs=[Run(text="Contents")], style="TOCHeading"),
              Para(runs=[Run(text="kept")])]
    doc = emit(blocks)
    texts = [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]]
    assert texts == ["Contents", "kept"]


def test_every_block_node_has_a_unique_id():
    doc = emit([Para(runs=[Run(text=str(i))]) for i in range(5)])
    ids = [n["id"] for n in doc["nodes"]]
    assert len(set(ids)) == 5
    assert all(i and i[0].isalpha() for i in ids)


def test_document_has_metadata_and_style():
    doc = emit([Para(runs=[Run(text="x")])])
    assert doc["metadata"]["version"] == 1
    assert doc["documentStyle"] == {}
    json.dumps(doc)  # must be serialisable
