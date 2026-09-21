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


def test_empty_paragraph_has_no_text_child():
    """The body drops these, but a table cell's placeholder keeps the grid
    rectangular and has to survive, so the node it gets still matters: an empty
    paragraph is a node with no children, never a TEXT holding "". That is the
    shape cell emission will take from `_para`, which filters nothing.
    """
    node = _para(Para(runs=[]), Ids())
    assert node["nodes"] == []


def test_empty_paragraph_is_not_emitted_in_the_body():
    doc = emit([Para(runs=[Run(text="a")]), Para(runs=[]), Para(runs=[Run(text="b")])])
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["a", "b"]


def test_contents_list_paragraph_is_not_emitted():
    """TOC1-TOC9 is a hand-typed contents list: redundant, and glued to the page
    numbers it was typed with."""
    blocks = [Para(runs=[Run(text="1. What is Machine Learning?\t2")], style="TOC1"),
              Para(runs=[Run(text="body")], style="TOC9"),
              Para(runs=[Run(text="kept")])]
    doc = emit(blocks)
    assert [n["nodes"][0]["textData"]["text"] for n in doc["nodes"]] == ["kept"]


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
