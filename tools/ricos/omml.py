"""Word's equations, read back as one line of text.

Word stores an equation as OMML, a tree of fractions, scripts, radicals and
operators under `m:oMath`; MathType stores one as an OLE object with a
picture of it, which this module cannot read and the reader counts instead.
Ricos has neither an equation node nor a picture of one that would survive
the upload, so what an equation can keep is its text - and OMML's text is
already Unicode, α and ∑ and ∫ as themselves. What is lost is the layout,
and what stands in for it is the notation Word itself shows under "Linear":
`a/b`, `x^2`, `P_A`, `√(k/m)`, `∑_(i=1)^n`. A reader who types equations
into Word reads that back without being told.

Two choices make the line readable rather than merely correct. An operand of
one character, or one that Unicode can write as a script of its own, stands
bare - `x²`, `xᵢ`, `a/b` - and anything longer is grouped in parentheses, so
that `(a+b)/2` cannot be read as `a+(b/2)`. And a delimiter the author drew
is kept as drawn, so a matrix inside square brackets stays inside them.

Nothing here knows about Ricos or about runs: `linear` takes an element and
returns a string, and the reader decides what to do with it.
"""

from tools.ricos.glyphs import script

M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# The character Word uses when the author did not choose one.
DEFAULT = {"nary": "∫", "acc": "̂", "begChr": "(", "endChr": ")", "sepChr": "|"}
ROOTS = {"2": "√", "3": "∛", "4": "∜"}


def linear(el):
    """The equation under `el` - an `m:oMath`, or any node of one - as text."""
    return _node(el)


def _children(el):
    """The argument children of a node: everything but its property element."""
    return [c for c in el if not c.tag.endswith("Pr")]


def _join(el):
    return "".join(_node(c) for c in _children(el))


def _arg(el, name):
    """The text of the `m:<name>` child, or "" when there is none."""
    child = el.find(M + name)
    return _join(child) if child is not None else ""


def _val(el, path, default=""):
    """The `m:val` of the element at `path` under `el`, or `default`."""
    found = el.find("/".join(M + part for part in path.split("/")))
    if found is None:
        return default
    return found.get(M + "val", default)


def _on(el, path):
    """A boolean property: present and not switched off."""
    found = el.find("/".join(M + part for part in path.split("/")))
    return found is not None and found.get(M + "val", "1") not in ("0", "false", "off")


def _group(text):
    """`text` as an operand: bare when it is one character, a number, or
    already parenthesised; otherwise in parentheses."""
    if len(text) <= 1 or text.replace(".", "", 1).isdigit():
        return text
    if text.startswith("(") and text.endswith(")") and _balanced(text[1:-1]):
        return text
    return f"({text})"


def _balanced(text):
    depth = 0
    for c in text:
        depth += (c == "(") - (c == ")")
        if depth < 0:
            return False
    return depth == 0


def _delimited(text):
    return len(text) >= 2 and text[0] in "([{|" and text[-1] in ")]}|"


def _fraction(el):
    num, den = _arg(el, "num"), _arg(el, "den")
    if _val(el, "fPr/type") == "noBar":
        return f"({num}¦{den})"
    return f"{_group(num)}/{_group(den)}"


def _scripts(el):
    base = _group(_arg(el, "e"))
    sub = el.find(M + "sub")
    sup = el.find(M + "sup")
    out = base
    if sub is not None:
        out += script(_join(sub), "sub")
    if sup is not None:
        out += script(_join(sup), "super")
    return out


def _prescript(el):
    return (
        f"({script(_arg(el, 'sub'), 'sub')}{script(_arg(el, 'sup'), 'super')})"
        f"{_group(_arg(el, 'e'))}"
    )


def _radical(el):
    body = _arg(el, "e")
    degree = "" if _on(el, "radPr/degHide") else _arg(el, "deg")
    if degree in ROOTS or not degree:
        return ROOTS.get(degree, "√") + _group(body)
    return f"√({degree}&{body})"


def _delimiter(el):
    beg = _val(el, "dPr/begChr", DEFAULT["begChr"])
    end = _val(el, "dPr/endChr", DEFAULT["endChr"])
    sep = _val(el, "dPr/sepChr", DEFAULT["sepChr"])
    return beg + sep.join(_join(e) for e in el.findall(M + "e")) + end


def _nary(el):
    out = _val(el, "naryPr/chr", DEFAULT["nary"])
    if not _on(el, "naryPr/subHide"):
        out += script(_arg(el, "sub"), "sub")
    if not _on(el, "naryPr/supHide"):
        out += script(_arg(el, "sup"), "super")
    return f"{out} {_arg(el, 'e')}"


def _function(el):
    name, arg = _arg(el, "fName"), _arg(el, "e")
    if _delimited(arg):
        return name + arg
    return f"{name} {arg}" if len(arg) <= 1 else f"{name}({arg})"


def _bar(el):
    body = _arg(el, "e")
    top = _val(el, "barPr/pos", "top") == "top"
    if len(body) == 1:
        return body + ("̅" if top else "̲")
    return ("‾" if top else "_") + f"({body})"


def _accent(el):
    body = _arg(el, "e")
    mark = _val(el, "accPr/chr", DEFAULT["acc"])
    return body + mark if len(body) == 1 else f"({body}){mark}"


def _limit(el, kind):
    """The base of a limit is an operator or a function name, never grouped."""
    return _arg(el, "e") + script(_arg(el, "lim"), kind)


def _matrix(el):
    rows = [
        " ".join(_join(e) for e in row.findall(M + "e")) for row in el.findall(M + "mr")
    ]
    body = "; ".join(rows)
    parent = el.getparent()
    if (
        parent is not None
        and parent.tag == M + "e"
        and parent.getparent() is not None
        and parent.getparent().tag == M + "d"
    ):
        return body
    return f"[{body}]"


def _lines(el):
    return "\n".join(_join(e) for e in el.findall(M + "e"))


HANDLERS = {
    M + "f": _fraction,
    M + "sSub": _scripts,
    M + "sSup": _scripts,
    M + "sSubSup": _scripts,
    M + "sPre": _prescript,
    M + "rad": _radical,
    M + "d": _delimiter,
    M + "nary": _nary,
    M + "func": _function,
    M + "bar": _bar,
    M + "acc": _accent,
    M + "limLow": lambda el: _limit(el, "sub"),
    M + "limUpp": lambda el: _limit(el, "super"),
    M + "m": _matrix,
    M + "eqArr": _lines,
    M + "phant": lambda el: "",
    M + "oMathPara": lambda el: "\n".join(_node(o) for o in el.findall(M + "oMath")),
}


def _node(el):
    if el.tag in (M + "t", W + "t"):
        return el.text or ""
    handler = HANDLERS.get(el.tag)
    if handler is not None:
        return handler(el)
    return _join(el)
