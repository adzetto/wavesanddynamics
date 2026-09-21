"""The shape the reader hands to the writer.

Word and Ricos disagree about almost everything, so neither side is allowed to
see the other. Everything between them travels as these five dataclasses.
"""
from dataclasses import dataclass, field


@dataclass
class Run:
    """A stretch of text with one set of marks."""

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    link: str = ""


@dataclass
class Para:
    runs: list[Run] = field(default_factory=list)
    style: str = ""        # "", "Heading1", "Heading2", ...
    list_kind: str = ""    # "", "bullet", "ordered"
    list_id: str = ""      # Word's w:numId: which list this item belongs to
    list_level: int = 0
    align: str = "AUTO"    # AUTO | LEFT | RIGHT | CENTER | JUSTIFY


@dataclass
class Figure:
    """A picture, plus the line Word left underneath it.

    An empty filename means the relationship it points at was never declared.
    Zero width and height under a real filename mean the file is there but could
    not be measured. `number` is reading order, for ordering and anchors: it is
    not the number in the caption, which is the author's and sometimes counts
    pictures that never made it into the file.
    """

    rel_id: str = ""
    filename: str = ""
    width: int = 0
    height: int = 0
    caption: str = ""
    number: int = 0


@dataclass
class Table:
    rows: list = field(default_factory=list)   # list[list[list[Block]]]
    header_row: bool = False


@dataclass
class Callout:
    """A one-cell Word table. He uses these as highlighted asides, not as data."""

    blocks: list = field(default_factory=list)


def walk(blocks):
    """Every block in reading order, the ones inside tables and asides included.

    These five dataclasses are a tree, not a list: a Table holds cells and a
    cell holds blocks, a Callout holds blocks, and a picture inside either is a
    picture on the page like any other. Anything that has to see all of them has
    to recurse, and this is the one place that knows how.

    That it is one place is the point. The recursion was written twice - once to
    number the figures, once to count them for the manifest - and the two
    disagreed silently: the numbering reached all 101 of the corpus's pictures
    while the count reached the 85 at the top level, so the manifest reported 85
    figures numbered up to 101 and nothing said anything was wrong. Two copies
    of a walk over a shape that lives somewhere else is how that happens, so the
    walk lives with the shape.

    A container is yielded before what it contains, which lets a caller filter
    for a kind of block without having to know where it sat.
    """
    for block in blocks:
        yield block
        if isinstance(block, Table):
            for row in block.rows:
                for cell in row:
                    yield from walk(cell)
        elif isinstance(block, Callout):
            yield from walk(block.blocks)
