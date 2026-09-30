"""The shape the reader hands to the writer.

Word and Ricos disagree about almost everything, so neither side is allowed to
see the other. Everything between them travels as these six dataclasses.
"""

from dataclasses import dataclass, field


@dataclass
class Run:
    """A stretch of text with one set of marks.

    The marks are what the run means once Word's style hierarchy has been
    resolved, not what its `w:rPr` says: a bold that arrives through the
    paragraph style is as bold as one typed. `color` and `highlight` are hex
    with a leading `#`, and `color` is set only where the run departs from
    the colour most of the document is written in - the document's own black
    is not a colour. `vertical` is "super", "sub" or "". `anchor` is the
    bookmark a link inside the document points at; `link` is a URL.
    `strike` is carried so the manifest can say it was there: nothing on the
    Ricos side can draw it.
    """

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    link: str = ""
    anchor: str = ""
    color: str = ""
    highlight: str = ""
    vertical: str = ""
    strike: bool = False


@dataclass
class Para:
    """A paragraph, with what Word said about it translated once.

    `heading` and `role` are that translation, and they exist because `style`
    is Word's vocabulary and this side of the boundary is supposed not to speak
    it. Four modules used to decode the raw style id, each in its own way - a
    dict of four names, a regex, an f-string and an equality test - so a
    document whose heading style is not spelled exactly `Heading1` emitted
    every heading as a plain paragraph, produced no section seam, and said
    nothing about it. A localized Word, an export out of Pages or Docs, or
    `Heading 1` with a space is all it takes.

    `style` stays because it is what the reader actually read, and it is the
    only record of the styles nothing here has a name for yet. Nothing outside
    `docx_read` parses it.

    `aside`, `rule_above` and `rule_below` are the paragraph's borders, read
    once: a bar down the left is the box he asides with, a line above or
    below is a rule. The reader turns them into a Callout and Rules before
    the writer sees them, and they stay on the paragraph as the record of
    where those came from.
    """

    runs: list[Run] = field(default_factory=list)
    style: str = ""  # Word's own style id, as written: "Heading1", "TOC1"
    heading: int = 0  # 1-6 for a heading, 0 for everything else
    role: str = ""  # "", "TITLE", "TOC", "CAPTION"
    list_kind: str = ""  # "", "bullet", "ordered"
    list_id: str = ""  # Word's w:numId: which list this item belongs to
    list_level: int = 0
    align: str = "AUTO"  # AUTO | LEFT | RIGHT | CENTER | JUSTIFY
    aside: bool = False
    rule_above: bool = False
    rule_below: bool = False


@dataclass
class Figure:
    """A picture, plus the line Word left underneath it.

    An empty filename means the relationship it points at was never declared.
    Zero width and height under a real filename mean the file is there but could
    not be measured. `number` is reading order, for ordering and anchors: it is
    not the number in the caption, which is the author's and sometimes counts
    pictures that never made it into the file.

    `width` and `height` are the pixels the page shows: the stored picture less
    what Word crops away. `crop` is that crop, as the fractions of the stored
    picture hidden at the left, top, right and bottom; () when nothing is.

    `display_width` and `display_height` are the size Word draws the picture
    at, in CSS pixels at 96 dpi, and `column` the width of the text column it
    was laid out in; 0 where the file does not say. A picture the author set
    at half the column is a decision about the page, and without these three
    numbers it was published at whatever size its pixels happened to be.

    `inline` is a picture no taller than a line or two of text, set inside a
    sentence: an equation drawn as a picture. `offset` says how it went back
    into the text. -1: the paragraph it sat in was cut at it, so the picture
    stands between the two halves. 0 or more: the paragraph could not be cut
    (a caption, a heading, a list item, an aside) and is kept whole, and the
    picture follows it; the number is where in that paragraph's text, with
    its leading spaces not counted, the picture sat. `joins` says which of
    a cut paragraph's halves stand beside the picture: "prev", "next" or
    "both" - a half with nothing to say is not emitted, and whatever lays the
    page out has to know not to join the picture to a stranger.
    """

    rel_id: str = ""
    filename: str = ""
    width: int = 0
    height: int = 0
    caption: str = ""
    number: int = 0
    crop: tuple = ()
    display_width: int = 0
    display_height: int = 0
    column: int = 0
    inline: bool = False
    offset: int = -1
    joins: str = ""


@dataclass
class Table:
    """Rows of cells of blocks. `widths` is each column's share of the table's
    width as Word's grid gives it, summing to 1; [] where the grid cannot be
    trusted to name the columns the rows hold."""

    rows: list = field(default_factory=list)  # list[list[list[Block]]]
    header_row: bool = False
    widths: list = field(default_factory=list)  # list[float]


@dataclass
class Callout:
    """A highlighted aside: a one-cell Word table, or a run of paragraphs he
    framed with a bar down the left. Not data either way."""

    blocks: list = field(default_factory=list)


@dataclass
class Rule:
    """A horizontal rule: the line Word draws as a paragraph border."""


def walk(blocks):
    """Every block in reading order, the ones inside tables and asides included.

    These dataclasses are a tree, not a list: a Table holds cells and a cell
    holds blocks, a Callout holds blocks, and a picture inside either is a
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
