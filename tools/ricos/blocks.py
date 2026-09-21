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
