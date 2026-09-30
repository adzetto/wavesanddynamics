"""His formulas set as LaTeX sets them: TeX to MathML, and the maps that say where.

The professor asked (28 Sep 2026) for every formula and every symbol in his
documents to be set as LaTeX would set it, "even a single letter". Each document
has a curated map, content/math/<slug>.json (a blog post: blog-<post slug>.json),
whose entries name a stretch of his text and the TeX for it. tools/ROUND13_MATH.md
holds the schema and the style rules. This module reads the maps, checks them
against the document, and turns each entry's TeX into MathML that preview.py's
text_node() puts in place of his text. His own text stays in the math's alttext.

THE MATCH. An entry's `find` is text exactly as it stands in one TEXT node: its
textData.text in build/ricos/<slug>/part-01.json, before any HTML escaping.
`before` and `after`, when given, must surround it in the same node. The
occurrences are the ones str.count() counts: before + find + after, left to
right, never overlapping. `count` must equal the occurrences in the whole
document, or the build stops and names the entry and where it did match. Two
entries may not claim the same characters. An entry with "joined": true is
matched in the runs of one paragraph joined together instead of in one run:
Word split some formulas into runs (an italic letter, a superscript, a
subscript the converter wrote as "_A"), and their context lies in the
neighbouring runs. A joined match takes the whole stretch, whatever runs it
covers, and keeps only the decorations every one of them shares (a link, a
colour), never the italic: math sets its own.

Every occurrence counted must also reach the page. preview.plan() calls begin()
before a document renders and end() after it; end() stops the build when an
entry was drawn fewer or more times than it occurs. That catches a find that a
callout's line break or a picture set in the sentence cuts, and text the page
does not draw. (It cannot see a table that flattens a cell to plain text for a
one-cell box's title: none holds a formula today.) The document is found by its
text: begin() compares a fingerprint of the nodes it is given with the
documents the maps name, so build.py passes nothing new.

THE CONVERTER. The TeX is turned into MathML Core here, with no library: the
subset the style rules need, written so the page looks like LaTeX in Chrome,
Safari and Firefox. latex2mathml 3.81 was measured first and set aside: it
drops \\mathrm on a single letter, writes \\arg as the literal text "\\arg",
sets \\cdot and \\ast as U+00B7 and U+002A (a text dot and a raised asterisk),
\\pm and \\sim as identifiers, \\operatorname as an operator with thick spaces,
and gives a unary minus binary spacing. So a build needs no pip and no network.
TeX's own rules decide the spacing: each atom takes its class (Ord, Op, Bin,
Rel, Open, Close, Punct, Inner), a Bin with nothing to bind becomes an Ord, and
the space between two atoms is TeXbook's table (p. 170), thin, medium or thick,
with the conditional ones dropped in scripts. Every <mo> carries its lspace and
rspace, so no browser's operator dictionary changes it, and every delimiter
says stretchy="false" unless \\left, \\right or \\big asked for size. A letter is
an <mi> the browser sets in math italic; a name (\\sin, \\operatorname{ReLU})
is an upright <mi> followed by U+2061 FUNCTION APPLICATION with TeX's thin space
where TeX puts one; \\text is <mtext>. Limits go under and over in display
style and beside in text style, as TeX puts them. An unknown command stops the
build: the maps can only use what this converter sets well.

TeX'S OTHER RULES, where Chrome does not follow them. After an italic letter
with no subscript TeX adds the letter's italic correction (rule 17): here an
<mspace> after it, or inside a superscript's base; before the superscript of a
letter with both scripts (rule 18), in the superscript's own em. The values are
the MATH table's own (METRICS). A long inline formula may break where TeX
breaks one, after a relation or binary operator at its outer level: it is set
as <math> pieces in one wrapper (INLINE_SPLIT). A display formula too wide for
a phone breaks before a relation, as amsmath's multline would, and is scaled
to fit what is left (DISPLAY_SPLIT, --mw). preview.py holds each inline
formula to the characters touching it, from space to space (.im-nb).

WHERE ELSE. The blog's typed pages of his text carry <tex> elements, which
build.py hands to typed(). A picture of a formula (Word's equation editor) is
named by a map entry {"picture": "image16", ...} and set in its place by
pictures(), which preview.head() calls once build.py has written its alt text.

THE FONT. Site Math is Latin Modern Math (GUST Font License) cut down to the
characters in REPERTOIRE, with its OpenType MATH table, so fractions, radicals,
scripts and stretchy delimiters take the font's own metrics; its bold face,
Latin Modern's own bold math letters, sets a formula in bold text (LaTeX's
\\boldmath), chosen by the stylesheet's font-weight. The build checks every
character a formula sets against REPERTOIRE; `python site/mathtex.py font`
rebuilds both faces and METRICS from MiKTeX's copy when it grows.
content/fonts-cmu/README.txt says what was changed.

Run on its own:
  python site/mathtex.py check [slug ...]   check every map (or these) against its document
  python site/mathtex.py tex "<TeX>" [--display]   print the MathML for one formula
  python site/mathtex.py font               rebuild the font from Latin Modern Math
"""
import hashlib
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPS = os.path.join(HERE, "content", "math")
RICOS = os.path.join(HERE, "build", "ricos")
BLOG = os.path.join(HERE, "content", "blog")
FONT = os.path.join(HERE, "content", "fonts-cmu", "site-math.woff2")
# each character's advance width in em, written beside the font by `font`,
# so the build can tell how wide a formula will be without a font library
METRICS = os.path.join(HERE, "content", "fonts-cmu", "site-math-metrics.json")
FONT_BOLD = os.path.join(HERE, "content", "fonts-cmu", "site-math-bold.woff2")
LM_MATH = "C:/Users/lenovo/AppData/Local/Programs/MiKTeX/fonts/opentype/public/lm-math/latinmodern-math.otf"
FAMILY = "Site Math"


class TexError(ValueError):
    """TeX the converter cannot set."""


class MapError(SystemExit):
    """A map, a <tex> element or a formula the build must not ship. It stops
    the build with its message, as build.py's own checks do (sys.exit)."""


# ------------------------------------------------------------- atoms

ORD, OP, BIN, REL, OPEN, CLOSE, PUNCT, INNER = ("ord", "op", "bin", "rel", "open", "close",
                                                 "punct", "inner")
D, T, S, SS = "D", "T", "S", "SS"          # display, text, script, scriptscript

# TeXbook p. 170: the space between two atoms, in mu: 0 none, 3 thin, 4 medium,
# 5 thick. A negative entry is only set in display and text style.
_SPACE = {
    ORD:   {ORD: 0, OP: 3, BIN: -4, REL: -5, OPEN: 0, CLOSE: 0, PUNCT: 0, INNER: -3},
    OP:    {ORD: 3, OP: 3, BIN: 0, REL: -5, OPEN: 0, CLOSE: 0, PUNCT: 0, INNER: -3},
    BIN:   {ORD: -4, OP: -4, BIN: 0, REL: 0, OPEN: -4, CLOSE: 0, PUNCT: 0, INNER: -4},
    REL:   {ORD: -5, OP: -5, BIN: 0, REL: 0, OPEN: -5, CLOSE: 0, PUNCT: 0, INNER: -5},
    OPEN:  {ORD: 0, OP: 0, BIN: 0, REL: 0, OPEN: 0, CLOSE: 0, PUNCT: 0, INNER: 0},
    CLOSE: {ORD: 0, OP: 3, BIN: -4, REL: -5, OPEN: 0, CLOSE: 0, PUNCT: 0, INNER: -3},
    PUNCT: {ORD: -3, OP: -3, BIN: 0, REL: -3, OPEN: -3, CLOSE: -3, PUNCT: -3, INNER: -3},
    INNER: {ORD: -3, OP: 3, BIN: -4, REL: -5, OPEN: -3, CLOSE: 0, PUNCT: -3, INNER: -3},
}

def _mu(n):
    """n mu as a CSS length (18 mu to the em)."""
    return "0" if not n else f"{n / 18:.4f}".rstrip("0").rstrip(".") + "em"


def _esc(text):
    return html.escape(text, quote=False)


# How wide a formula is, in em of its own size: the advances of its glyphs
# (content/fonts-cmu/site-math-metrics.json), scripts at 70% and 50% as MathML
# Core and TeX set them, and TeX's spaces. An estimate within a few per cent:
# enough to tell a phone's line from a laptop's.
_SCALE = {"D": 1.0, "T": 1.0, "S": 0.7, "SS": 0.5}
_METRICS = None


def _metrics():
    global _METRICS
    if _METRICS is None:
        try:
            with open(METRICS, encoding="utf-8") as fh:
                _METRICS = json.load(fh)
        except (OSError, ValueError):
            _METRICS = {}
    return _METRICS


def _advance(ch):
    return _metrics().get("advance", {}).get(ch, 0.5)


def _is_italic(ch):
    """A letter of the mathematical italic or bold italic alphabets."""
    o = ord(ch)
    return (0x1D434 <= o <= 0x1D49B or o == 0x210E or 0x1D6E2 <= o <= 0x1D755)


def _italic_correction(ch):
    """TeX's italic correction for a math italic letter, in em: how far its
    top leans out past its advance (the MATH table's MathItalicsCorrectionInfo,
    copied into METRICS by `font`)."""
    return _metrics().get("italic", {}).get(ch, 0.0)


def _em(x):
    return f"{x:.4f}".rstrip("0").rstrip(".") + "em"


# Chrome does not add the MATH table's italic correction after an italic
# letter, so V touches a superscript or the word after it ("where Vis"): the
# page adds it, as TeX does. Below IC_MIN em (w .003, b .014: under half a
# pixel) it would only be markup.
IC_MIN = 0.02


# the operators MathML Core's dictionary lets stretch: TeX never stretches
# one unasked, so these say stretchy="false"
_STRETCHY = set("()[]{}|‖⟨⟩⌊⌋⌈⌉/\\∣∥↑↓↕⇑⇓⇕←→↔⇐⇒⇔⟵⟶⟷⟸⟹⟺↦⟼↩↪⇌⇀↼⇁↽^~¯_ˇ˘˙¨")


class _Tok:
    """A token: <mi>, <mn>, <mo> or <mtext>."""

    def __init__(self, tag, text, cls=ORD, **attrs):
        self.tag, self.text, self.cls, self.attrs = tag, text, cls, attrs
        self.fn = False        # a function's name: U+2061 joins it to its argument
        self.limits = False    # scripts under and over it in display style
        if tag == "mo" and "stretchy" not in attrs and text in _STRETCHY:
            self.attrs["stretchy"] = "false"

    def mo(self):
        return self.tag == "mo"

    def xml(self, style, ls="0", rs="0"):
        attrs = "".join(f' {k}="{v}"' for k, v in self.attrs.items())
        if self.tag == "mo":
            attrs = f' lspace="{ls}" rspace="{rs}"' + attrs
        return f"<{self.tag}{attrs}>{_esc(self.text)}</{self.tag}>"

    def ic(self):
        """The italic correction TeX adds after this token (its rule 17): only
        for one letter in math italic, and only where it shows (IC_MIN)."""
        if self.tag != "mi" or len(self.text) != 1 or "mathvariant" in self.attrs:
            return 0.0
        ic = _italic_correction(_italic(self.text))
        return ic if ic >= IC_MIN else 0.0

    def width(self, style):
        text = self.text
        if self.tag == "mi" and len(text) == 1 and "mathvariant" not in self.attrs:
            text = _italic(text)
        size = self.attrs.get("minsize")
        grow = 1.25 if size else 1.0          # a \big delimiter is a size wider
        return sum(_advance(c) for c in text) * _SCALE[style] * grow


class _Space:
    """Explicit space (\\, \\; \\quad ...): not an atom, so TeX's own space
    between the atoms around it still comes on top."""

    def __init__(self, mu):
        self.mu = mu

    def xml(self):
        return f'<mspace width="{_mu(self.mu)}"/>'


class _Group:
    """{...}: an Ord atom (or the class \\mathbin and the like give it)."""
    fn = limits = False

    def __init__(self, items, cls=ORD):
        self.items, self.cls = items, cls

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        return f"<mrow>{_row(self.items, style)}</mrow>"

    def width(self, style):
        return _row_width(self.items, style)


class _Script:
    """A nucleus with a subscript, a superscript or both."""

    def __init__(self, base, sub, sup):
        self.base, self.sub, self.sup = base, sub, sup
        self.cls, self.fn, self.limits = base.cls, base.fn, False

    def mo(self):
        return self.base.mo()

    def _ic(self):
        """TeX's italic correction goes between a letter and its superscript;
        a letter with a subscript stays bare (rule 17)."""
        ic = getattr(self.base, "ic", None)
        return ic() if ic and self.sub is None else 0.0

    def _shift(self):
        """With both scripts TeX sets the subscript at the letter's bare width
        and the superscript past its italic correction; Chrome's msubsup puts
        both at one x, so the superscript opens with that space (rule 18)."""
        ic = getattr(self.base, "ic", None)
        return ic() if ic and self.sub is not None and self.sup is not None else 0.0

    def xml(self, style, ls="0", rs="0"):
        b = self.base.xml(style, ls, rs)
        if self._ic():
            b = f'<mrow>{b}<mspace width="{_em(self._ic())}"/></mrow>'
        small = _SMALLER[style]
        sub = _elem(self.sub, small) if self.sub is not None else None
        sup = _elem(self.sup, small) if self.sup is not None else None
        if self._shift():
            # the space is in the superscript's own em: the base's, scaled
            shift = self._shift() * _SCALE[style] / _SCALE[small]
            sup = f'<mrow><mspace width="{_em(shift)}"/>{_row(self.sup, small)}</mrow>'
        under = self.base.limits and style == D
        tags = ("munder", "mover", "munderover") if under else ("msub", "msup", "msubsup")
        if sub is not None and sup is not None:
            return f"<{tags[2]}>{b}{sub}{sup}</{tags[2]}>"
        if sub is not None:
            return f"<{tags[0]}>{b}{sub}</{tags[0]}>"
        return f"<{tags[1]}>{b}{sup}</{tags[1]}>"

    def width(self, style):
        small = _SMALLER[style]
        base = self.base.width(style)
        scripts = max(_row_width(x, small) + (self._shift() * _SCALE[style] if x is self.sup else 0)
                      for x in (self.sub, self.sup) if x is not None)
        if self.base.limits and style == D:
            return max(base, scripts)
        return base + scripts + (self._ic() + 0.056) * _SCALE[style]   # SpaceAfterScript


class _Frac:
    """\\frac, \\dfrac, \\tfrac and \\binom: an Inner atom."""
    cls, fn, limits = INNER, False, False

    def __init__(self, num, den, size=None, binom=False):
        self.num, self.den, self.size, self.binom = num, den, size, binom

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        own = {"d": D, "t": T}.get(self.size, style)
        inner = {D: T, T: S, S: SS, SS: SS}[own]
        attrs = {"d": ' displaystyle="true"', "t": ' displaystyle="false"'}.get(self.size, "")
        if self.binom:
            attrs += ' linethickness="0"'
        frac = f"<mfrac{attrs}>{_elem(self.num, inner)}{_elem(self.den, inner)}</mfrac>"
        if not self.binom:
            return frac
        fence = ' fence="true" stretchy="true" symmetric="true"'
        return (f'<mrow><mo lspace="0" rspace="0"{fence}>(</mo>{frac}'
                f'<mo lspace="0" rspace="0"{fence}>)</mo></mrow>')

    def width(self, style):
        own = {"d": D, "t": T}.get(self.size, style)
        inner = {D: T, T: S, S: SS, SS: SS}[own]
        w = max(_row_width(self.num, inner), _row_width(self.den, inner)) + 0.24 * _SCALE[own]
        return w + (1.0 * _SCALE[own] if self.binom else 0)


class _Sqrt:
    cls, fn, limits = ORD, False, False

    def __init__(self, body, index=None):
        self.body, self.index = body, index

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        if self.index is not None:
            return f"<mroot>{_elem(self.body, style)}{_elem(self.index, SS)}</mroot>"
        return f"<msqrt>{_row(self.body, style)}</msqrt>"

    def width(self, style):
        index = _row_width(self.index, SS) * 0.6 if self.index is not None else 0
        return _row_width(self.body, style) + (0.833 + 0.1) * _SCALE[style] + index


class _Accent:
    """\\hat{x} and the like, over (or under) the base: an Ord atom."""
    cls, fn, limits = ORD, False, False

    def __init__(self, base, char, stretchy, under=False):
        self.base, self.char, self.stretchy, self.under = base, char, stretchy, under

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        tag, attr = ("munder", "accentunder") if self.under else ("mover", "accent")
        acc = (f'<mo stretchy="{"true" if self.stretchy else "false"}">'
               f'{_esc(self.char)}</mo>')
        return f'<{tag} {attr}="true">{_elem(self.base, style)}{acc}</{tag}>'

    def width(self, style):
        return _row_width(self.base, style)


class _Stack:
    """\\overset and \\underset: the base keeps its class (an = with "def" over
    it is still a relation)."""

    def __init__(self, base, over=None, under=None):
        self.base, self.over, self.under = base, over, under
        self.cls, self.fn, self.limits = base.cls, False, False

    def mo(self):
        return self.base.mo()

    def xml(self, style, ls="0", rs="0"):
        b = self.base.xml(style, ls, rs)
        if self.over is not None and self.under is not None:
            return f"<munderover>{b}{_elem(self.under, S)}{_elem(self.over, S)}</munderover>"
        if self.over is not None:
            return f"<mover>{b}{_elem(self.over, S)}</mover>"
        return f"<munder>{b}{_elem(self.under, S)}</munder>"

    def width(self, style):
        return max([self.base.width(style)] + [_row_width(x, S) for x in (self.over, self.under)
                                                if x is not None])


class _Fenced:
    """\\left( ... \\right): an Inner atom whose delimiters grow with it."""
    cls, fn, limits = INNER, False, False

    def __init__(self, left, items, right):
        self.left, self.items, self.right = left, items, right

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        def fence(c):
            if not c:
                return ""
            return (f'<mo lspace="0" rspace="0" fence="true" stretchy="true" '
                    f'symmetric="true">{_esc(c)}</mo>')
        return f"<mrow>{fence(self.left)}{_row(self.items, style)}{fence(self.right)}</mrow>"

    def width(self, style):
        ends = sum(_advance(c) for c in (self.left, self.right) if c) * 1.3
        return _row_width(self.items, style) + ends * _SCALE[style]


class _Styled:
    """\\displaystyle and its kin: the rest of the group in that style."""
    fn = limits = False
    cls = ORD

    def __init__(self, items, style):
        self.items, self.style = items, style

    def mo(self):
        return False

    def xml(self, style, ls="0", rs="0"):
        attrs = {D: ' displaystyle="true" scriptlevel="0"', T: ' displaystyle="false" scriptlevel="0"',
                 S: ' displaystyle="false" scriptlevel="1"',
                 SS: ' displaystyle="false" scriptlevel="2"'}[self.style]
        return f"<mstyle{attrs}>{_row(self.items, self.style)}</mstyle>"

    def width(self, style):
        return _row_width(self.items, self.style)


_SMALLER = {D: S, T: S, S: SS, SS: SS}


def _classes(atoms):
    """Each atom's class after TeX's rules 5 and 6 (TeXbook appendix G): a Bin
    that opens a list, or follows a Bin, Op, Rel, Open or Punct, is an Ord; so
    is a Bin before a Rel, Close or Punct, and one that ends the list."""
    cls = [a.cls for a in atoms]
    for k, c in enumerate(cls):
        if c == BIN and (k == 0 or cls[k - 1] in (BIN, OP, REL, OPEN, PUNCT)):
            cls[k] = ORD
        elif c in (REL, CLOSE, PUNCT) and k and cls[k - 1] == BIN:
            cls[k - 1] = ORD
    if cls and cls[-1] == BIN:
        cls[-1] = ORD
    return cls


def _gap(left, right, style):
    """TeX's space between two atoms, in mu."""
    mu = _SPACE[left][right]
    if mu < 0:
        mu = -mu if style in (D, T) else 0
    return mu


class _Break:
    """\\allowbreak: a place the line may break, as TeX allows in text."""


def _parts(items, style, ends=frozenset()):
    """A row as [(markup, item, class, width in em)], one per atom, space or
    break, with TeX's space between atoms.

    The space goes on the operator beside it, as the right one's lspace or the
    left one's rspace; between two atoms neither of which is an operator it is
    an <mspace>. A function's name is followed by U+2061, which carries the
    space after it. An atom's markup carries what follows it (U+2061, the
    <mspace>), so a line may break between any two parts. After an atom in
    `ends` a line may break, and the space there stays with the line that
    ends, as TeX drops the glue at a break: the next line starts flush."""
    atoms = [x for x in items if not isinstance(x, (_Space, _Break))]
    cls = _classes(atoms)
    n = len(atoms)
    ls, rs, mid = [0] * n, [0] * n, {}
    apply = [atoms[k].fn and k + 1 < n and cls[k + 1] in (ORD, OPEN, INNER)
             for k in range(n)]
    for k in range(n - 1):
        g = _gap(cls[k], cls[k + 1], style)
        if not g:
            continue
        if k in ends:
            if apply[k] or atoms[k].mo():
                rs[k] = g
            else:
                mid[k] = g
        elif atoms[k + 1].mo():
            ls[k + 1] = g
        elif apply[k] or atoms[k].mo():
            rs[k] = g
        else:
            mid[k] = g
    scale = _SCALE[style]
    out, k = [], 0
    for x in items:
        if isinstance(x, _Break):
            out.append(("", x, None, 0.0))
            continue
        if isinstance(x, _Space):
            out.append((x.xml(), x, None, x.mu / 18 * scale))
            continue
        xml = x.xml(style, _mu(ls[k]), _mu(0 if apply[k] else rs[k]))
        ic = x.ic() if isinstance(x, _Tok) else 0.0
        if ic:
            xml += f'<mspace width="{_em(ic)}"/>'
        if apply[k]:
            xml += f'<mo lspace="0" rspace="{_mu(rs[k])}">&#x2061;</mo>'
        if k in mid:
            xml += f'<mspace width="{_mu(mid[k])}"/>'
        width = x.width(style) + ((ls[k] + rs[k] + mid.get(k, 0)) / 18 + ic) * scale
        out.append((xml, x, cls[k], width))
        k += 1
    return out


def _row(items, style):
    """A list of atoms and spaces as MathML (_parts(), joined)."""
    return "".join(p[0] for p in _parts(items, style))


def _row_width(items, style):
    return sum(p[3] for p in _parts(items, style))


def _elem(items, style):
    """One element: an atom alone as itself (a script, a fraction's part, an
    accent's base: one child of its parent, as MathML asks), anything else in
    an <mrow>."""
    if len(items) == 1 and not isinstance(items[0], (_Space, _Break)):
        return items[0].xml(style)
    return f"<mrow>{_row(items, style)}</mrow>"


# ------------------------------------------------------------- what TeX names

_GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ", "varepsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "varkappa": "ϰ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "omicron": "ο", "pi": "π",
    "varpi": "ϖ", "rho": "ρ", "varrho": "ϱ", "sigma": "σ", "varsigma": "ς", "tau": "τ",
    "upsilon": "υ", "phi": "ϕ", "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π",
    "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}
# ordinary symbols, set upright; \partial and the dotless i and j take the
# browser's math italic, as TeX takes them from its math italic font
_ORD = {
    "infty": "∞", "partial": "∂", "nabla": "∇", "forall": "∀", "exists": "∃", "nexists": "∄",
    "emptyset": "∅", "varnothing": "∅", "hbar": "ℏ", "ell": "ℓ", "imath": "ı", "jmath": "ȷ",
    "aleph": "ℵ", "Re": "ℜ", "Im": "ℑ", "wp": "℘", "angle": "∠", "triangle": "△",
    "prime": "′", "top": "⊤", "bot": "⊥", "neg": "¬", "lnot": "¬", "degree": "°",
    "vdots": "⋮", "%": "%", "#": "#", "&": "&", "$": "$", "_": "_", "backslash": "\\",
}
_ITALIC_ORD = {"∂", "ı", "ȷ"}
_BIN = {
    "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "⋅", "ast": "∗", "star": "⋆",
    "circ": "∘", "bullet": "∙", "cap": "∩", "cup": "∪", "setminus": "∖", "smallsetminus": "∖",
    "oplus": "⊕", "ominus": "⊖", "otimes": "⊗", "oslash": "⊘", "odot": "⊙", "wedge": "∧",
    "land": "∧", "vee": "∨", "lor": "∨", "diamond": "⋄", "uplus": "⊎", "sqcap": "⊓",
    "sqcup": "⊔", "dagger": "†", "ddagger": "‡", "wr": "≀", "amalg": "⨿",
}
_REL = {
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "leqslant": "⩽", "geqslant": "⩾",
    "neq": "≠", "ne": "≠", "approx": "≈", "sim": "∼", "simeq": "≃", "cong": "≅",
    "equiv": "≡", "propto": "∝", "ll": "≪", "gg": "≫", "in": "∈", "notin": "∉", "ni": "∋",
    "subset": "⊂", "supset": "⊃", "subseteq": "⊆", "supseteq": "⊇", "mid": "∣",
    "nmid": "∤", "parallel": "∥", "perp": "⊥", "models": "⊨", "vdash": "⊢", "dashv": "⊣",
    "prec": "≺", "succ": "≻", "preceq": "⪯", "succeq": "⪰", "doteq": "≐", "asymp": "≍",
    "triangleq": "≜", "coloneqq": "≔", "lesssim": "≲", "gtrsim": "≳", "nleq": "≰",
    "ngeq": "≱",
    "to": "→", "rightarrow": "→", "gets": "←", "leftarrow": "←", "leftrightarrow": "↔",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔", "longrightarrow": "⟶",
    "longleftarrow": "⟵", "longleftrightarrow": "⟷", "Longrightarrow": "⟹",
    "Longleftarrow": "⟸", "Longleftrightarrow": "⟺", "mapsto": "↦", "longmapsto": "⟼",
    "uparrow": "↑", "downarrow": "↓", "updownarrow": "↕", "Uparrow": "⇑", "Downarrow": "⇓",
    "nearrow": "↗", "searrow": "↘", "swarrow": "↙", "nwarrow": "↖",
    "hookrightarrow": "↪", "hookleftarrow": "↩", "rightleftharpoons": "⇌",
}
# amsmath's arrows with a thick space on each side
_SPACED_REL = {"implies": "⟹", "impliedby": "⟸", "iff": "⟺"}
_INNER = {"ldots": "…", "dots": "…", "cdots": "⋯", "ddots": "⋱"}
_PUNCT = {"colon": ":", "ldotp": ".", "cdotp": "⋅"}
# delimiters by name: (character, class in a formula)
_DELIM = {
    "(": ("(", OPEN), ")": (")", CLOSE), "[": ("[", OPEN), "]": ("]", CLOSE),
    "{": ("{", OPEN), "}": ("}", CLOSE), "lbrace": ("{", OPEN), "rbrace": ("}", CLOSE),
    "lbrack": ("[", OPEN), "rbrack": ("]", CLOSE), "langle": ("⟨", OPEN),
    "rangle": ("⟩", CLOSE), "lvert": ("|", OPEN), "rvert": ("|", CLOSE),
    "lVert": ("‖", OPEN), "rVert": ("‖", CLOSE), "lfloor": ("⌊", OPEN),
    "rfloor": ("⌋", CLOSE), "lceil": ("⌈", OPEN), "rceil": ("⌉", CLOSE),
    "vert": ("|", ORD), "|": ("‖", ORD), "Vert": ("‖", ORD), "/": ("/", ORD),
}
# large operators: (character, limits under and over in display style)
_BIG = {
    "sum": ("∑", True), "prod": ("∏", True), "coprod": ("∐", True), "int": ("∫", False),
    "iint": ("∬", False), "iiint": ("∭", False), "oint": ("∮", False),
    "bigcup": ("⋃", True), "bigcap": ("⋂", True), "bigvee": ("⋁", True),
    "bigwedge": ("⋀", True), "bigoplus": ("⨁", True), "bigotimes": ("⨂", True),
    "bigodot": ("⨀", True), "bigsqcup": ("⨆", True),
}
# named functions, upright: True where display style puts the limits under
_FUNCS = {name: False for name in (
    "arccos arcsin arctan arg cos cosh cot coth csc deg dim exp hom ker lg ln log sec sin "
    "sinh tan tanh").split()}
_FUNCS.update({name: True for name in "det gcd inf lim liminf limsup max min Pr sup".split()})
_FUNC_TEXT = {"liminf": "lim\u2009inf", "limsup": "lim\u2009sup"}
# accents, each the spacing form of its mark: in Chrome with this font the
# combining marks (U+0302 ...) sit left of the letter, and the ASCII ^ and ~
# are the wide ones. \widehat, \overline, \vec and the like are left out:
# no form of them places well in Chrome (tested 28 Sep 2026).
_ACCENTS = {
    "hat": ("ˆ", False), "check": ("ˇ", False), "tilde": ("˜", False), "acute": ("´", False),
    "grave": ("`", False), "dot": ("˙", False), "ddot": ("¨", False), "breve": ("˘", False),
    "bar": ("¯", False), "mathring": ("˚", False),
}
_FONTS = {"mathrm": "rm", "mathup": "rm", "mathit": "it", "mathbf": "bf", "boldsymbol": "bi",
          "bm": "bi", "mathsf": "sf", "mathtt": "tt", "mathcal": "cal", "mathscr": "cal",
          "mathbb": "bb", "mathfrak": "frak", "mathnormal": None}
_TEXT = {"text", "textrm", "textup", "textnormal", "mbox"}
_CLASS = {"mathord": ORD, "mathop": OP, "mathbin": BIN, "mathrel": REL, "mathopen": OPEN,
          "mathclose": CLOSE, "mathpunct": PUNCT, "mathinner": INNER}
_SPACES = {",": 3, ":": 4, ">": 4, ";": 5, "!": -3, " ": 6, "quad": 18, "qquad": 36,
           "enspace": 9, "thinspace": 3, "medspace": 4, "thickspace": 5, "negthinspace": -3,
           "negmedspace": -4, "negthickspace": -5}
_STYLES = {"displaystyle": D, "textstyle": T, "scriptstyle": S, "scriptscriptstyle": SS}
# \big and its kin: the delimiter's size, and its class
_BIGS = {}
for _n, _size in (("big", "1.2em"), ("Big", "1.623em"), ("bigg", "2.047em"), ("Bigg", "2.470em")):
    _BIGS[_n] = (_size, ORD)
    _BIGS[_n + "l"] = (_size, OPEN)
    _BIGS[_n + "r"] = (_size, CLOSE)
    _BIGS[_n + "m"] = (_size, REL)

# the characters a formula may carry as they are, and their class
_ASCII_OPS = {"+": ("+", BIN), "-": ("\u2212", BIN), "*": ("∗", BIN), "/": ("/", ORD),
              "=": ("=", REL), "<": ("<", REL), ">": (">", REL), ":": (":", REL),
              ",": (",", PUNCT), ";": (";", PUNCT), "!": ("!", CLOSE), "?": ("?", CLOSE),
              "(": ("(", OPEN), ")": (")", CLOSE), "[": ("[", OPEN), "]": ("]", CLOSE),
              "|": ("|", ORD), ".": (".", ORD), "@": ("@", ORD)}
_UNICODE_OPS = {}
for _table, _cls in ((_BIN, BIN), (_REL, REL), (_INNER, INNER)):
    for _c in _table.values():
        _UNICODE_OPS.setdefault(_c, (_c, _cls))
_UNICODE_OPS.update({"\u2212": ("\u2212", BIN), "·": ("⋅", BIN), "∗": ("∗", BIN),
                     "′": ("′", ORD), "⟨": ("⟨", OPEN), "⟩": ("⟩", CLOSE), "‖": ("‖", ORD)})
_UNICODE_BIG = {c: (c, lim) for c, lim in _BIG.values()}
_UNICODE_ORD = set(_ORD.values()) - {"%", "#", "&", "$", "_", "\\"}


# ------------------------------------------------------------- letters in a font

def _alnum(ch, font):
    """(character, attributes) for a letter, digit or Greek letter in a font.

    With no font a Latin letter and a lower-case Greek one are left for the
    browser to set in math italic, and a capital Greek letter is upright, as
    TeX sets them. Bold, script and the like are the Unicode mathematical
    alphanumerics, since MathML Core knows no mathvariant but "normal"."""
    o = ord(ch)
    upper = "A" <= ch <= "Z"
    lower = "a" <= ch <= "z"
    digit = "0" <= ch <= "9"
    gcap = 0x391 <= o <= 0x3A9 and o != 0x3A2
    gsmall = 0x3B1 <= o <= 0x3C9
    if font is None:
        if gcap:
            return ch, {"mathvariant": "normal"}
        return ch, {}
    if font == "rm":
        return ch, ({} if digit else {"mathvariant": "normal"})
    if font == "it":
        if gcap:
            return chr(0x1D6E2 + o - 0x391), {}
        return ch, {}
    tables = {
        "bf": (0x1D400, 0x1D41A, 0x1D7CE, 0x1D6A8, 0x1D6C2),
        "bi": (0x1D468, 0x1D482, 0x1D7CE, 0x1D6A8, 0x1D736),
        "sf": (0x1D5A0, 0x1D5BA, 0x1D7E2, None, None),
        "tt": (0x1D670, 0x1D68A, 0x1D7F6, None, None),
        "cal": (0x1D49C, 0x1D4B6, None, None, None),
        "bb": (0x1D538, 0x1D552, 0x1D7D8, None, None),
        "frak": (0x1D504, 0x1D51E, None, None, None),
    }[font]
    holes = {
        "cal": {"B": "ℬ", "E": "ℰ", "F": "ℱ", "H": "ℋ", "I": "ℐ", "L": "ℒ", "M": "ℳ", "R": "ℛ",
                "e": "ℯ", "g": "ℊ", "o": "ℴ"},
        "bb": {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ", "R": "ℝ", "Z": "ℤ"},
        "frak": {"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"},
    }.get(font, {})
    if ch in holes:
        return holes[ch], {}
    base = (tables[0] if upper else tables[1] if lower else tables[2] if digit
            else tables[3] if gcap else tables[4] if gsmall else None)
    if base is None:
        raise TexError(f"{ch!r} has no form in the font {font!r}")
    start = ord("A") if upper else ord("a") if lower else ord("0") if digit else 0x391 if gcap else 0x3B1
    return chr(base + o - start), {}


# ------------------------------------------------------------- the parser

class _Parser:
    def __init__(self, src):
        self.s, self.i, self.n = src, 0, len(src)
        self.font = None

    def fail(self, msg):
        raise TexError(f"{msg} (at character {self.i} of {self.s!r})")

    def _ws(self):
        while self.i < self.n and self.s[self.i] in " \t\r\n":
            self.i += 1

    def token(self):
        """('cs', name), ('ch', c) or None at the end. Spaces between tokens
        mean nothing in math, as in TeX."""
        self._ws()
        if self.i >= self.n:
            return None
        c = self.s[self.i]
        if c != "\\":
            self.i += 1
            return ("ch", c)
        j = self.i + 1
        if j >= self.n:
            self.fail("a backslash with nothing after it")
        if self.s[j].isascii() and self.s[j].isalpha():
            k = j
            while k < self.n and self.s[k].isascii() and self.s[k].isalpha():
                k += 1
            name = self.s[j:k]
            if name == "operatorname" and k < self.n and self.s[k] == "*":
                k += 1
                name += "*"
            self.i = k
            return ("cs", name)
        self.i = j + 1
        return ("cs", self.s[j])

    def peek(self):
        at = self.i
        tok = self.token()
        self.i = at
        return tok

    def parse(self):
        items = self.row(None)
        return items

    def row(self, stop):
        """Atoms up to `stop`: "}" (consumed), "]" (consumed), "right" (left
        for the caller) or None (the end)."""
        items = []
        while True:
            tok = self.peek()
            if tok is None:
                if stop:
                    self.fail(f"a group that never closes (expected {stop!r})")
                return items
            if tok == ("ch", "}"):
                if stop == "}":
                    self.token()
                    return items
                self.fail("a } that closes nothing")
            if tok == ("ch", "]") and stop == "]":
                self.token()
                return items
            if tok == ("cs", "right"):
                if stop == "right":
                    return items
                self.fail("\\right without \\left")
            if tok in (("ch", "&"), ("cs", "\\")):
                self.fail("& and \\\\ belong to an environment, which this converter does not set")
            kind, name = tok
            if kind == "ch" and name == "~":
                self.token()
                items.append(_Space(6))
                continue
            if kind == "cs" and name == "allowbreak":
                self.token()
                items.append(_Break())
                continue
            if kind == "cs" and name in _SPACES:
                self.token()
                items.append(_Space(_SPACES[name]))
                continue
            if kind == "cs" and name in _SPACED_REL:
                self.token()
                items += [_Space(5), _Tok("mo", _SPACED_REL[name], REL), _Space(5)]
                continue
            if kind == "cs" and name in _STYLES:
                self.token()
                rest = self.row(stop)
                items.append(_Styled(rest, _STYLES[name]))
                return items
            items.append(self.atom())

    def atom(self):
        tok = self.peek()
        if tok in (("ch", "^"), ("ch", "_"), ("ch", "'")):
            nucleus = _Group([])
        else:
            nucleus = self.nucleus()
        sub = sup = None
        while True:
            tok = self.peek()
            if tok == ("ch", "^"):
                self.token()
                if sup is not None:
                    self.fail("a double superscript")
                sup = self.argument()
            elif tok == ("ch", "_"):
                self.token()
                if sub is not None:
                    self.fail("a double subscript")
                sub = self.argument()
            elif tok == ("ch", "'"):
                primes = 0
                while self.peek() == ("ch", "'"):
                    self.token()
                    primes += 1
                if sup is not None:
                    self.fail("a prime after a superscript")
                mark = _Tok("mo", "′″‴⁗"[min(primes, 4) - 1], ORD)
                sup = [mark]
                if self.peek() == ("ch", "^"):
                    self.token()
                    sup = [mark] + self.argument()
            elif tok in (("cs", "limits"), ("cs", "nolimits")):
                self.token()
                if nucleus.cls != OP:
                    self.fail(f"\\{tok[1]} after something that is not an operator")
                nucleus.limits = tok[1] == "limits"
            else:
                break
        if sub is None and sup is None:
            return nucleus
        return _Script(nucleus, sub, sup)

    def argument(self):
        """A macro's argument or a script: a group, or one token (with the
        arguments that token takes)."""
        tok = self.peek()
        if tok is None:
            self.fail("an argument is missing")
        if tok == ("ch", "{"):
            self.token()
            return self.row("}")
        if tok in (("ch", "^"), ("ch", "_"), ("ch", "}")):
            self.fail(f"{tok[1]!r} where an argument should be")
        if tok[0] == "ch" and tok[1].isdigit():
            self.token()
            return [_Tok("mn", tok[1])]      # x^23 is x^{2}3, as in TeX
        return [self.nucleus()]

    def group_text(self):
        """A {...} argument read as text: braces must balance."""
        self._ws()
        if self.i >= self.n or self.s[self.i] != "{":
            self.fail("{ expected")
        depth, j = 0, self.i
        while j < self.n:
            c = self.s[j]
            if c == "\\":
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    text = self.s[self.i + 1:j]
                    self.i = j + 1
                    return text
            j += 1
        self.fail("a group that never closes")

    def nucleus(self):
        tok = self.token()
        kind, v = tok
        if kind == "ch":
            if v == "{":
                return _Group(self.row("}"))
            if v.isdigit() or (v == "." and self.i < self.n and self.s[self.i].isdigit()):
                return self.number(v)
            if v.isalpha():
                return self.letter(v)
            if v in _ASCII_OPS:
                ch, cls = _ASCII_OPS[v]
                return _Tok("mo", ch, cls)
            if v in _UNICODE_OPS:
                ch, cls = _UNICODE_OPS[v]
                return _Tok("mo", ch, cls)
            if v in _UNICODE_BIG:
                return self.bigop(*_UNICODE_BIG[v])
            if v in _UNICODE_ORD:
                return self.ordsym(v)
            self.fail(f"{v!r} cannot stand in a formula as it is")
        name = v
        if name in _GREEK:
            return self.letter(_GREEK[name])
        if name in _ORD:
            return self.ordsym(_ORD[name])
        if name in _BIN:
            return _Tok("mo", _BIN[name], BIN)
        if name in _REL:
            return _Tok("mo", _REL[name], REL)
        if name in _INNER:
            return _Tok("mo", _INNER[name], INNER)
        if name in _PUNCT:
            return _Tok("mo", _PUNCT[name], PUNCT)
        if name in ("{", "}") or (name in _DELIM and name not in ("(", ")", "[", "]", "/")):
            ch, cls = _DELIM[name]
            return _Tok("mo", ch, cls)
        if name in _BIG:
            return self.bigop(*_BIG[name])
        if name in _FUNCS:
            t = _Tok("mi", _FUNC_TEXT.get(name, name), OP)
            t.fn, t.limits = True, _FUNCS[name]
            return t
        if name in ("operatorname", "operatorname*"):
            text = self.operator_text(self.group_text())
            attrs = {"mathvariant": "normal"} if len(text) == 1 else {}
            t = _Tok("mi", text, OP, **attrs)
            t.fn, t.limits = True, name.endswith("*")
            return t
        if name in _TEXT:
            return _Tok("mtext", self.text(self.group_text()))
        if name in _FONTS:
            was, self.font = self.font, _FONTS[name]
            self._ws()
            if self.peek() == ("ch", "{"):
                self.token()
                items = self.row("}")
            else:
                items = [self.nucleus()]
            self.font = was
            if _FONTS[name] == "rm":
                items = _merge_upright(items)
            return items[0] if len(items) == 1 else _Group(items)
        if name in _CLASS:
            items = self.argument()
            if len(items) == 1 and isinstance(items[0], _Tok):
                items[0].cls = _CLASS[name]
                return items[0]
            return _Group(items, _CLASS[name])
        if name in ("frac", "dfrac", "tfrac", "cfrac"):
            num, den = self.argument(), self.argument()
            return _Frac(num, den, {"dfrac": "d", "cfrac": "d", "tfrac": "t"}.get(name))
        if name in ("binom", "dbinom", "tbinom"):
            num, den = self.argument(), self.argument()
            return _Frac(num, den, {"dbinom": "d", "tbinom": "t"}.get(name), binom=True)
        if name == "sqrt":
            index = None
            if self.peek() == ("ch", "["):
                self.token()
                index = self.row("]")
            return _Sqrt(self.argument(), index)
        if name in _ACCENTS:
            ch, stretchy = _ACCENTS[name]
            return _Accent(self.argument(), ch, stretchy)
        if name in ("overset", "underset", "stackrel"):
            top, base = self.argument(), self.argument()
            b = base[0] if len(base) == 1 else _Group(base)
            if name == "stackrel":
                b.cls = REL
            return _Stack(b, over=top) if name != "underset" else _Stack(b, under=top)
        if name == "left":
            left = self.delimiter()
            items = self.row("right")
            self.token()                      # \right
            right = self.delimiter()
            return _Fenced(left, items, right)
        if name in _BIGS:
            size, cls = _BIGS[name]
            ch = self.delimiter()
            return _Tok("mo", ch, cls, fence="true", stretchy="true", symmetric="true",
                        minsize=size, maxsize=size)
        self.fail(f"\\{name} is not a command this converter sets")

    def number(self, first):
        text = first
        while self.i < self.n:
            c = self.s[self.i]
            if c.isdigit():
                text += c
            elif c == "." and "." not in text and self.i + 1 < self.n and self.s[self.i + 1].isdigit():
                text += c
            else:
                break
            self.i += 1
        if self.font not in (None, "rm", "it"):
            text = "".join(_alnum(c, self.font)[0] if c.isdigit() else c for c in text)
        return _Tok("mn", text)

    def letter(self, ch):
        o = ord(ch)
        greek = 0x391 <= o <= 0x3C9 or ch in "ϑϕϖϰϱϵ"
        if not (ch.isascii() or greek):
            return _Tok("mi", ch)
        if ch in "ϑϕϖϰϱϵ":
            if self.font in (None, "it"):
                return _Tok("mi", ch)
            if self.font == "rm":
                return _Tok("mi", ch, mathvariant="normal")
            if self.font == "bi":
                return _Tok("mi", chr({"ϵ": 0x1D750, "ϑ": 0x1D751, "ϰ": 0x1D752, "ϕ": 0x1D753,
                                       "ϱ": 0x1D754, "ϖ": 0x1D755}[ch]))
            self.fail(f"{ch!r} in this font")
        text, attrs = _alnum(ch, self.font)
        return _Tok("mi", text, **attrs)

    def ordsym(self, ch):
        if ch in _ITALIC_ORD:
            return _Tok("mi", ch)
        return _Tok("mi", ch, mathvariant="normal")

    def bigop(self, ch, limits):
        t = _Tok("mo", ch, OP, largeop="true", movablelimits="false")
        t.limits = limits
        return t

    def delimiter(self):
        tok = self.token()
        if tok is None:
            self.fail("a delimiter is missing")
        kind, v = tok
        if kind == "ch" and v == ".":
            return ""
        if kind == "ch" and v in "()[]|/":
            return {"|": "|"}.get(v, v)
        if kind == "cs" and v in _DELIM:
            return _DELIM[v][0]
        if kind == "cs" and v in ("uparrow", "downarrow", "updownarrow", "Uparrow", "Downarrow"):
            return _REL[v]
        if kind == "ch" and v in "⟨⟩‖":
            return v
        self.fail(f"{v!r} is not a delimiter")

    def text(self, raw):
        """\\text's argument: his words, with TeX's escapes for the characters
        TeX reserves. Spaces at either end would vanish in <mtext>, so they are
        no-break spaces."""
        out, j = [], 0
        while j < len(raw):
            c = raw[j]
            if c == "\\":
                nxt = raw[j + 1:j + 2]
                if nxt in ("%", "&", "#", "_", "{", "}", "$", " "):
                    out.append(nxt)
                    j += 2
                    continue
                if nxt == ",":
                    out.append("\u2009")
                    j += 2
                    continue
                raise TexError(f"\\text cannot hold \\{nxt}...: {raw!r}")
            if c in "{}":
                j += 1
                continue
            if c in "$^_&#%":
                raise TexError(f"\\text cannot hold {c!r}: {raw!r}")
            out.append("\u00a0" if c == "~" else c)
            j += 1
        text = re.sub(r"\s+", " ", "".join(out))
        lead = len(text) - len(text.lstrip(" "))
        trail = len(text) - len(text.rstrip(" "))
        core = text.strip(" ")
        return "\u00a0" * lead + core + "\u00a0" * trail if core else "\u00a0" * len(text)

    def operator_text(self, raw):
        out, j = [], 0
        while j < len(raw):
            c = raw[j]
            if c == "\\":
                nxt = raw[j + 1:j + 2]
                if nxt in (",", " ", ":", ";"):
                    out.append("\u2009")
                    j += 2
                    continue
                if nxt in ("_", "-"):
                    out.append(nxt)
                    j += 2
                    continue
                raise TexError(f"\\operatorname cannot hold \\{nxt}...: {raw!r}")
            if c.isspace() or c in "{}":
                j += 1
                continue
            if not (c.isalnum() or c in "-*'"):
                raise TexError(f"\\operatorname cannot hold {c!r}: {raw!r}")
            out.append("\u2212" if c == "-" else c)
            j += 1
        if not out:
            raise TexError("an empty \\operatorname")
        return "".join(out)


def _merge_upright(items):
    """Adjacent upright letters as one <mi> (\\mathrm{TP} is "TP", one name,
    upright as a name of two letters is by default); a single one keeps
    mathvariant="normal"."""
    out = []
    for x in items:
        if (isinstance(x, _Tok) and x.tag == "mi" and x.attrs == {"mathvariant": "normal"}
                and x.text.isalpha() and out and isinstance(out[-1], _Tok)
                and out[-1].tag == "mi" and out[-1].text.isalpha() and not out[-1].fn
                and out[-1].attrs in ({"mathvariant": "normal"}, {})):
            prev = out[-1]
            merged = _Tok("mi", prev.text + x.text)
            out[-1] = merged
            continue
        out.append(x)
    return out


# Where a formula may break across lines. A browser never breaks inside one
# <math>, so a long formula is set as consecutive <math> pieces, and a line
# may break between two of them. In text TeX breaks after a relation or a
# binary operator at the outer level of the formula (TeXbook ch. 18), never
# inside a group, and so does the page: an inline formula wider than
# INLINE_SPLIT em is cut after each. TeX never breaks a display formula; a
# phone's line is narrower than any paper, so one wider than DISPLAY_SPLIT em
# is cut as amsmath's multline would cut it by hand: before a relation other
# than the first of its clause, and after a \quad that opens the next clause
# (", \quad j = 1, ..."). \allowbreak marks a place in either. The pieces sit
# in one wrapper, role="math" and named by his text, and are hidden from
# assistive technology one by one, so the formula is read once, whole.
INLINE_SPLIT = 8.0
DISPLAY_SPLIT = 12.0
# A display piece still wider than this (a phone's line is about 14 em of
# formula) may also break before a binary operator outside every bracket,
# the next place a hand-broken multline would: w_j(k+1) = w_j(k) | + eta(k)...
DISPLAY_PIECE = 16.0


def _cuts(parts, display):
    """The indexes of `parts` a new piece starts at."""
    atoms = [k for k, p in enumerate(parts) if p[2] is not None]
    cuts = _primary(parts, display)
    if display:
        edges = [0] + sorted(cuts) + [len(parts)]
        for a, b in zip(edges, edges[1:]):
            if sum(p[3] for p in parts[a:b]) > DISPLAY_PIECE:
                cuts |= _before_binary(parts, a, b)
    first, last = (atoms[0], atoms[-1]) if atoms else (0, 0)
    return sorted(c for c in cuts if first < c <= last)


def _before_binary(parts, a, b):
    """Before each binary operator in parts[a:b] that no bracket encloses, but
    the piece's first."""
    out, depth, seen = set(), 0, False
    for n in range(a, b):
        cls = parts[n][2]
        if cls is None:
            continue
        if cls == OPEN:
            depth += 1
        elif cls == CLOSE:
            depth = max(0, depth - 1)
        elif cls == BIN and depth == 0 and seen:
            out.add(n)
        seen = True
    return out


def _primary(parts, display):
    """Where TeX breaks a formula in text (after a relation or a binary
    operator), or where a display one breaks first (before a relation but the
    first of its clause, and after a \\quad that opens the next clause)."""
    cuts, rel_seen = set(), False
    for n, k in enumerate(parts):
        item, cls = k[1], k[2]
        if isinstance(item, _Break):
            cuts.add(n)
            continue
        if display:
            if isinstance(item, _Space) and item.mu >= 18:
                rel_seen = False                      # a new clause
                cuts.add(n + 1)
            elif cls == REL:
                if rel_seen:
                    cuts.add(n)
                rel_seen = True
        elif cls in (REL, BIN):
            j = n + 1
            while j < len(parts) and isinstance(parts[j][1], _Space):
                j += 1                                # his space stays with the operator
            cuts.add(j)
    return cuts


def to_mathml(tex, display=False, alt=None, cls="im"):
    """The markup for one formula: a <math>, or a long one's pieces in a
    wrapper. `alt` (his own text) becomes the alttext and the wrapper's name;
    without it, the TeX does. A display formula says how wide its widest line
    is (--mw, in em), for the stylesheet to fit it to a narrow column."""
    items = _Parser(tex).parse()
    if not items:
        raise TexError("an empty formula")
    style = D if display else T
    parts = _parts(items, style)
    total = sum(p[3] for p in parts)
    alt_attr = html.escape(tex if alt is None else alt, quote=True)
    cuts = []
    if total > (DISPLAY_SPLIT if display else INLINE_SPLIT) or any(
            isinstance(p[1], _Break) for p in parts):
        cuts = _cuts(parts, display)
    if cuts:
        # set again, the space at each cut on the side of the line that ends
        atom = [sum(1 for p in parts[:c] if p[2] is not None) - 1 for c in cuts]
        parts = _parts(items, style, frozenset(atom))
    whole = "".join(p[0] for p in parts)
    if not cuts:
        if display:
            return (f'<math class="{cls}" display="block" style="--mw:{total:.2f}" '
                    f'alttext="{alt_attr}">{whole}</math>')
        return f'<math class="{cls}" alttext="{alt_attr}">{whole}</math>'
    pieces, at = [], 0
    for c in cuts + [len(parts)]:
        pieces.append(parts[at:c])
        at = c
    # What is read is the whole formula, unbroken and out of sight (.im-sr);
    # what is seen is its pieces, hidden from assistive technology, with a
    # <wbr> between two: siblings in the line, so a reader's text around them
    # is held to the first and the last (preview.py, _hold()) and no break
    # opportunity sits inside a span that may not wrap (Firefox would not
    # take it there).
    style = ' displaystyle="true"' if display else ""
    shape = ' display="block"' if display else ""
    # (a <span> clips it: Firefox and Safari give a <math> no width of 1px)
    read = f'<span class="im-sr"><math class="{cls}"{shape} alttext="{alt_attr}">{whole}</math></span>'
    out = [f'<math class="{cls}"{style} aria-hidden="true" alttext="">'
           f'{"".join(p[0] for p in piece)}</math>' for piece in pieces]
    out[0] = read + out[0]
    if display:
        widest = max(sum(p[3] for p in piece) for piece in pieces)
        return f'<span class="im-dm" style="--mw:{widest:.2f}">{"<wbr>".join(out)}</span>'
    return "<wbr>".join(out)


# ------------------------------------------------------------- the font

def _italic(ch):
    """What the browser draws for a one-letter <mi> (MathML Core's
    text-transform: math-auto)."""
    o = ord(ch)
    if "A" <= ch <= "Z":
        return chr(0x1D434 + o - 65)
    if "a" <= ch <= "z":
        return "\u210e" if ch == "h" else chr(0x1D44E + o - 97)
    if 0x391 <= o <= 0x3A9 and o != 0x3A2:
        return chr(0x1D6E2 + o - 0x391)
    if 0x3B1 <= o <= 0x3C9:
        return chr(0x1D6FC + o - 0x3B1)
    return {"ı": "\U0001d6a4", "ȷ": "\U0001d6a5", "∇": "\U0001d6fb", "∂": "\U0001d715",
            "ϵ": "\U0001d716", "ϑ": "\U0001d717", "ϰ": "\U0001d718", "ϕ": "\U0001d719",
            "ϱ": "\U0001d71a", "ϖ": "\U0001d71b", "ϴ": "\U0001d6f3"}.get(ch, ch)


# What Site Math carries. The build fails on a formula that needs more, and
# says so; add the character here and run `python site/mathtex.py font`. Kept
# to what his documents set and what they are likely to: his words in \text,
# the Latin and Greek letters in math italic, the operators, relations,
# arrows and delimiters of his fields. Bold, script and blackboard letters are
# not in it until a formula asks for them.
_SYMBOLS = ("+−±∓×÷⋅∗∘∙∩∪∖⊕⊗∧∨⋆"            # binary operators
            "=<>≤≥≠≈∼≃≅≡∝≪≫∈∉∋⊂⊃⊆⊇∣∥⊥≔≜⩽⩾≲≳≺≻⊢⊨"  # relations
            "→←↔⇒⇐⇔⟶⟵⟷⟹⟸⟺↦↑↓⇌"             # arrows
            "()[]{}|‖⟨⟩⌊⌋⌈⌉/"                 # delimiters
            "∑∏∫∬∮"                           # large operators
            "∞∂∇∀∃∅ℏℓ′″‴°¬√△∠⊤…⋯⋮⋱"           # ordinary symbols
            "ˆˇ˜´`˙¨˘¯˚"                      # accents
            "±×÷·\u2061")


def _repertoire():
    cps = set(range(0x20, 0x7F)) | {0xA0, 0x2009}
    cps |= {ord(c) for c in _SYMBOLS}
    cps |= set(range(0x391, 0x3AA)) - {0x3A2}              # Greek, upright
    cps |= set(range(0x3B1, 0x3CA)) | {ord(c) for c in "ϑϕϖϰϱϵ"}
    cps |= set(range(0x1D434, 0x1D468)) - {0x1D455} | {0x210E}   # math italic Latin
    cps |= set(range(0x1D6FC, 0x1D71C))                    # math italic Greek, and ∂
    cps |= {int(c, 16) for c in os.environ.get("SITE_MATH_EXTRA", "").split()}
    return frozenset(cps)


REPERTOIRE = _repertoire()
_IGNORABLE = {0x2061}
_TOKEN = re.compile(r"<(mi|mn|mo|mtext)((?:\s[^>]*)?)>([^<]*)</\1>")


def missing_glyphs(mathml):
    """The characters this MathML draws that Site Math does not carry."""
    miss = set()
    for tag, attrs, text in _TOKEN.findall(mathml):
        text = html.unescape(text)
        if tag == "mi" and len(text) == 1 and "mathvariant" not in attrs:
            text = _italic(text)
        miss |= {c for c in text if ord(c) not in REPERTOIRE and ord(c) not in _IGNORABLE}
    return miss


def mathml(tex, display=False, alt=None, where="a formula"):
    """to_mathml(), with the build's checks: TeX it cannot set, or a glyph Site
    Math lacks, stops the build naming `where`."""
    try:
        out = to_mathml(tex, display, alt)
    except TexError as e:
        raise MapError(f"{where}: {e}") from None
    miss = missing_glyphs(out)
    if miss:
        names = ", ".join(f"U+{ord(c):04X} {c}" for c in sorted(miss))
        raise MapError(f"{where}: Site Math has no glyph for {names}; add it to REPERTOIRE "
                       f"in site/mathtex.py and run python site/mathtex.py font")
    return out


# ------------------------------------------------------------- the maps

KEYS = {"find", "before", "after", "tex", "count", "display", "why", "joined"}
# a picture of a formula (Word's equation editor), set as the formula: named
# by its file's stem ("image16"); its alt text is build.py's ALT, or "alt"
PICTURE_KEYS = {"picture", "tex", "count", "display", "why", "alt"}


class Entry:
    """One line of a map, checked and converted."""

    def __init__(self, raw, k, name):
        self.k, self.name = k, name
        where = f"{name}: entry {k}"
        if not isinstance(raw, dict):
            raise MapError(f"{where}: an entry is an object")
        self.picture = raw.get("picture")
        if self.picture is not None:
            self._picture(raw, where)
            return
        extra = set(raw) - KEYS
        if extra:
            raise MapError(f"{where}: unknown key(s) {sorted(extra)}; the keys are {sorted(KEYS)}")
        for key in ("find", "tex", "count"):
            if key not in raw:
                raise MapError(f"{where}: no {key!r}")
        self.find, self.tex = raw["find"], raw["tex"]
        self.before, self.after = raw.get("before", ""), raw.get("after", "")
        self.count, self.display = raw["count"], raw.get("display", False)
        self.joined = raw.get("joined", False)
        for key in ("find", "tex", "before", "after"):
            if not isinstance(raw.get(key, ""), str):
                raise MapError(f"{where}: {key!r} is text")
        if not self.find or not self.tex.strip():
            raise MapError(f"{where}: an empty find or tex")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise MapError(f"{where}: count is a whole number, 1 or more")
        if not isinstance(self.display, bool) or not isinstance(self.joined, bool):
            raise MapError(f"{where}: display and joined are true or false")
        self.label = f"{where} (find {self.find!r}" + (
            f", before {self.before!r}" if self.before else "") + (
            f", after {self.after!r}" if self.after else "") + ")"
        self.pattern = self.before + self.find + self.after
        self.mathml = mathml(self.tex, self.display, alt=self.find, where=self.label)

    def _picture(self, raw, where):
        extra = set(raw) - PICTURE_KEYS
        if extra:
            raise MapError(f"{where}: unknown key(s) {sorted(extra)} for a picture; the keys "
                           f"are {sorted(PICTURE_KEYS)}")
        if not isinstance(self.picture, str) or not re.fullmatch(r"[\w.-]+", self.picture):
            raise MapError(f"{where}: picture is a file's name without its extension")
        self.tex, self.count = raw.get("tex", ""), raw.get("count", 1)
        self.display, self.alt = raw.get("display", False), raw.get("alt")
        if not isinstance(self.tex, str) or not self.tex.strip():
            raise MapError(f"{where}: no tex")
        if not isinstance(self.count, int) or isinstance(self.count, bool) or self.count < 1:
            raise MapError(f"{where}: count is a whole number, 1 or more")
        if not isinstance(self.display, bool) or not (self.alt is None or isinstance(self.alt, str)):
            raise MapError(f"{where}: display is true or false, alt is text")
        self.find, self.before, self.after, self.joined = "", "", "", False
        self.label = f"{where} (picture {self.picture!r})"
        self.mathml = mathml(self.tex, self.display, where=self.label)   # sets, or stops the build

    def spans(self, text):
        """Where this entry's find stands in `text`: (start, end) pairs, as
        str.count counts its context-qualified form."""
        out, i = [], 0
        while True:
            j = text.find(self.pattern, i)
            if j < 0:
                return out
            s = j + len(self.before)
            out.append((s, s + len(self.find)))
            i = j + len(self.pattern)


def load(path):
    """A map's entries, each checked and converted."""
    name = os.path.relpath(path, HERE).replace(os.sep, "/")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        raise MapError(f"{name}: {e}") from None
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise MapError(f'{name}: a map is {{"entries": [...]}}')
    entries = [Entry(raw, k, name) for k, raw in enumerate(data["entries"], 1)]
    seen = {}
    for e in entries:
        key = ("picture", e.picture) if e.picture else (e.before, e.find, e.after, e.joined)
        if key in seen:
            raise MapError(f"{e.label}: the same find as entry {seen[key]}")
        seen[key] = e.k
    return entries


def _texts(nodes):
    """(every TEXT node's textData, every node's list of TEXT children), in
    document order."""
    singles, blocks = [], []

    def walk(ns):
        runs = [n for n in ns if n.get("type") == "TEXT"]
        if runs:
            blocks.append(runs)
        for n in ns:
            if n.get("type") == "TEXT":
                singles.append(n.get("textData") or {})
            walk(n.get("nodes") or [])
    walk(nodes or [])
    return singles, blocks


def _fingerprint(nodes):
    singles, _ = _texts(nodes)
    return hashlib.sha1("\x00".join(d.get("text", "") for d in singles).encode("utf-8")).hexdigest()


def _source(slug):
    """The nodes of the document a map is named for."""
    if slug.startswith("blog-"):
        post = slug[5:]
        index = os.path.join(BLOG, "posts.json")
        if os.path.isfile(index):
            with open(index, encoding="utf-8") as fh:
                for p in json.load(fh):
                    if p.get("slug") == post:
                        with open(os.path.join(BLOG, p["manifest"]), encoding="utf-8") as g:
                            return json.load(g)["body"]["nodes"]
        raise MapError(f"content/math/{slug}.json: no blog post {post!r} in content/blog/posts.json")
    path = os.path.join(RICOS, slug, "part-01.json")
    if not os.path.isfile(path):
        raise MapError(f"content/math/{slug}.json: no document {slug} "
                       f"(build/ricos/{slug}/part-01.json)")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["nodes"]


_INDEX = None


def _index():
    """{fingerprint of a document's text: its map's path}."""
    global _INDEX
    if _INDEX is None:
        found = {}
        names = sorted(os.listdir(MAPS)) if os.path.isdir(MAPS) else []
        for name in names:
            if not name.endswith(".json"):
                continue
            key = _fingerprint(_source(name[:-5]))
            if key in found:
                raise MapError(f"content/math/{name} and {found[key]} name the same document")
            found[key] = os.path.join(MAPS, name)
        _INDEX = found
    return _INDEX


def _overlaps(spans, text, name):
    spans = sorted(spans, key=lambda s: (s[0], s[1]))
    for a, b in zip(spans, spans[1:]):
        if b[0] < a[1]:
            raise MapError(f"{name}: {a[2].label} and {b[2].label} claim the same characters "
                           f"in {text[max(0, a[0] - 30):b[1] + 30]!r}")
    return spans


class Document:
    """One document's map, checked against its nodes, and what the page drew."""

    def __init__(self, path, nodes, entries=None):
        self.name = os.path.relpath(path, HERE).replace(os.sep, "/")
        self.entries = load(path) if entries is None else entries
        self.pictures = [e for e in self.entries if e.picture]
        self.plain = [e for e in self.entries if not e.joined and not e.picture]
        self.joined = [e for e in self.entries if e.joined and not e.picture]
        self.spans = {}
        self.drawn = {e.k: set() for e in self.entries}
        self.keep = []                # the objects whose id() keys `drawn`
        self.rendered = False
        found = {e.k: [] for e in self.entries}
        singles, blocks = _texts(nodes)
        for data in singles:
            text = data.get("text", "")
            if text not in self.spans:
                self.spans[text] = self.match(text)
            for s, t, e in self.spans[text]:
                found[e.k].append(text[max(0, s - 40):t + 40])
        if self.joined:
            for runs in blocks:
                full = "".join((r.get("textData") or {}).get("text", "") for r in runs)
                claimed, at = [], 0
                for r in runs:
                    text = (r.get("textData") or {}).get("text", "")
                    claimed += [(at + s, at + t, e) for s, t, e in self.spans.get(text, ())]
                    at += len(text)
                mine = [(s, t, e) for e in self.joined for s, t in e.spans(full)]
                _overlaps(claimed + mine, full, self.name)
                for s, t, e in mine:
                    found[e.k].append(full[max(0, s - 40):t + 40])
        for e in self.pictures:
            found[e.k] = [f"picture {e.picture}"] * _count_pictures(nodes, e.picture)
        bad = [e for e in self.entries if len(found[e.k]) != e.count]
        if bad:
            lines = []
            for e in bad:
                where = "; ".join(repr(w) for w in found[e.k][:4]) or "nowhere"
                lines.append(f"  {e.label}: count {e.count}, in the document "
                             f"{len(found[e.k])} time(s): {where}")
            raise MapError(f"{self.name}: counts that do not match the document\n"
                           + "\n".join(lines))

    def match(self, text):
        """The plain entries' finds in one run: [(start, end, entry)]."""
        spans = [(s, t, e) for e in self.plain for s, t in e.spans(text)]
        return _overlaps(spans, text, self.name)

    def cut(self, data):
        """A run as [(text, False) | (mathml, True)]."""
        self.rendered = True
        text = data.get("text", "")
        k = data.get("mathtex")
        if k is not None:                     # a joined formula (join())
            entry = next(e for e in self.entries if e.k == k)
            if text != entry.find:
                raise MapError(f"{entry.label}: a picture set in the sentence cuts the formula")
            return [(entry.mathml, True)]
        spans = self.spans.get(text)
        if spans is None:
            spans = self.match(text)
        if not spans:
            return [(text, False)]
        self.keep.append(data)
        out, at = [], 0
        for s, t, e in spans:
            self.drawn[e.k].add((id(data), s))
            if s > at:
                out.append((text[at:s], False))
            out.append((e.mathml, True))
            at = t
        if at < len(text):
            out.append((text[at:], False))
        return out

    def join(self, nodes):
        """A paragraph's runs with each joined formula made one run of its own,
        marked for cut(); the runs it covers are cut at its edges."""
        if not self.joined:
            return nodes
        self.rendered = True
        runs = [n for n in nodes if n.get("type") == "TEXT"]
        full = "".join(r["textData"]["text"] for r in runs)
        spans = sorted(((s, t, e) for e in self.joined for s, t in e.spans(full)),
                       key=lambda x: x[0])
        if not spans:
            return nodes
        self.keep.append(nodes)
        out, at = [], 0                # `at`: where run `r` starts in `full`
        cuts = iter(spans)
        span = next(cuts, None)
        pending = []                   # runs inside the current span
        for r in runs:
            text = r["textData"]["text"]
            end_r = at + len(text)
            pos = at
            while pos < end_r:
                if span is None or pos < span[0]:
                    stop = end_r if span is None else min(end_r, span[0])
                    out.append(_piece(r, text[pos - at:stop - at]))
                    pos = stop
                    continue
                stop = min(end_r, span[1])
                pending.append(r)
                pos = stop
                if pos == span[1]:
                    s, t, e = span
                    self.drawn[e.k].add((id(nodes), s))
                    out.append({"type": "TEXT", "textData": {
                        "text": e.find, "decorations": _shared(pending), "mathtex": e.k}})
                    pending = []
                    span = next(cuts, None)
            at = end_r
        return out

    def verify(self):
        bad = [e for e in self.entries if len(self.drawn[e.k]) != e.count]
        if bad:
            lines = [f"  {e.label}: in the document {e.count} time(s), drawn "
                     f"{len(self.drawn[e.k])}" for e in bad]
            raise MapError(
                f"{self.name}: formulas the page did not draw as often as they occur\n"
                + "\n".join(lines) + "\n  A find must not run across a line break in a "
                "callout or a picture set in the sentence, and a line the page does not draw "
                "(the contents line) takes no math.")


def _piece(run, text):
    return {**run, "textData": {**run["textData"], "text": text}}


def _shared(runs):
    """The decorations every run of a joined formula carries, but its italic."""
    lists = [r["textData"].get("decorations") or [] for r in runs]
    if not lists:
        return []
    return [d for d in lists[0] if d.get("type") != "ITALIC" and all(d in ds for ds in lists[1:])]


# ------------------------------------------------------------- one document at a time

_DOC = None


def begin(nodes):
    """preview.plan() hands every document here before it renders: finish the
    last one, then load and check this one's map, if it has one."""
    global _DOC
    end()
    if not nodes:
        return
    path = _index().get(_fingerprint(nodes))
    if path:
        _DOC = Document(path, nodes)


def end():
    """After a document: every formula counted must have been drawn. (Not
    while another error is on its way out: that one is the news.)"""
    global _DOC
    doc, _DOC = _DOC, None
    if doc is not None and doc.rendered and sys.exc_info()[0] is None:
        doc.verify()


def active():
    """The map of the document being rendered, or None."""
    return _DOC


def cut(data):
    """preview.text_node()'s hook: a run as [(text, False) | (mathml, True)],
    or None when the document has no map."""
    return None if _DOC is None else _DOC.cut(data)


def join(nodes):
    """preview.inline()'s hook: the runs, with joined formulas as runs of
    their own."""
    return nodes if _DOC is None else _DOC.join(nodes)


def _count_pictures(nodes, stem):
    """How many of the document's pictures are the file `stem`."""
    n = 0
    for x in nodes or []:
        if x.get("type") == "IMAGE":
            src = (((x.get("imageData") or {}).get("image") or {}).get("src") or {}).get("id", "")
            n += os.path.splitext(os.path.basename(src))[0] == stem
        n += _count_pictures(x.get("nodes"), stem)
    return n


def pictures(body, usage=None):
    """preview.head()'s hook, once build.py has written its alt text into the
    rendered body: each picture a map names, set as its formula where it stood.

    A picture set in a sentence (<img class="eq">) is replaced by the formula;
    a framed one, with its zoom link and frame, by the formula and its caption
    under it. The alttext is the picture's alt text (build.py's ALT), or the
    entry's "alt". The picture's file leaves `usage` (preview.USAGE), so
    build.py writes no file the page no longer shows. A display formula takes
    the punctuation that followed the
    picture in his sentence, as LaTeX puts the period inside a display (\\,.):
    the text after it would otherwise open its line with ". ". An inline one is
    held to the characters around it, as a found formula is."""
    doc = _DOC
    if doc is None or not doc.pictures:
        return body
    doc.rendered = True
    formulas = []
    for e in doc.pictures:
        img = r'<img\b[^>]*\bsrc="[^"]*/' + re.escape(e.picture) + r'\.[A-Za-z0-9]+"[^>]*>'
        punct = r'([.,;:](?=\s|<|$))?'
        framed = re.compile(r'<figure\b[^>]*>\s*(?:<a\b[^>]*>\s*)?(' + img + r')\s*(?:</a>\s*)?'
                            r'(<figcaption>.*?</figcaption>)?\s*</figure>' + punct, re.S)
        loose = re.compile('(' + img + ')' + punct)

        def one(m, framed_=False, e=e):
            tag = m.group(1)
            src = re.search(r'\bsrc="([^"]*)"', tag)
            if usage is not None and src:
                usage.pop(src.group(1), None)
            alt = re.search(r'\balt="([^"]*)"', tag)
            alt = html.unescape(alt.group(1)) if alt and alt.group(1) else e.alt
            if not alt:
                raise MapError(f"{doc.name}: {e.label}: the picture has no alt text to keep "
                               f"and the entry no \"alt\"")
            mark = m.group(3) if framed_ else m.group(2)
            tex = e.tex
            if e.display and mark:
                tex += r"\," + {":": r"\colon"}.get(mark, mark)
            formulas.append(mathml(tex, e.display, alt=alt, where=e.label))
            doc.drawn[e.k].add(("picture", len(formulas)))
            sign = "\x01" if e.display else "\x00"
            cap = m.group(2) if framed_ and m.group(2) else ""
            cap = f'<p class="cap">{cap[len("<figcaption>"):-len("</figcaption>")]}</p>' if cap else ""
            rest = "" if e.display else (mark or "")
            return f"{sign}{len(formulas) - 1}{sign}{rest}{cap}"
        body = framed.sub(lambda m: one(m, True), body)
        body = loose.sub(one, body)
    return _hold(body, formulas)


def is_display(markup):
    """True for a display formula's markup: a line of its own, which the text
    around it is never held to."""
    return markup.startswith(('<math class="im" display="block"', '<span class="im-dm"'))


# ------------------------------------------------------------- the blog's typed text

_TEX = re.compile(r"<tex\b([^>]*)>(.*?)</tex\s*>", re.S | re.I)


def typed(markup, where):
    """A typed page of his text (content/blog/<slug>/text/*.html) with each
    <tex>TeX</tex> set as MathML, and <tex display> as a display formula. The
    TeX may carry HTML's entities (&lt; for <); the alttext is the TeX. An
    inline formula is held to the characters touching it, up to a space or a
    tag, as preview.py holds his documents' (.im-nb): "w_j’s" does not part."""
    formulas = []

    def one(m):
        line = markup.count("\n", 0, m.start()) + 1
        attrs = m.group(1).strip().lower()
        if attrs not in ("", "display", 'display=""', 'display="block"'):
            raise MapError(f"{where}: line {line}: <tex {m.group(1).strip()}>: "
                           f"only <tex> and <tex display>")
        body = m.group(2)
        if re.search(r"<[A-Za-z/!]", body):
            raise MapError(f"{where}: line {line}: markup inside <tex>: {body[:60]!r}")
        tex = html.unescape(body)
        formulas.append(mathml(tex, bool(attrs), where=f"{where}: line {line}: <tex>{tex}</tex>"))
        mark = "\x01" if attrs else "\x00"
        return f"{mark}{len(formulas) - 1}{mark}"
    out = _TEX.sub(one, markup)
    left = re.search(r"</?tex\b", out, re.I)
    if left:
        line = out.count("\n", 0, left.start()) + 1
        raise MapError(f"{where}: line {line}: a <tex> element that does not close")
    return _hold(out, formulas)


def _hold(markup, formulas):
    """Put each formula back where its mark (\\x00k\\x00 inline, \\x01k\\x01
    display) stands, an inline one held to the characters touching it, up to a
    space or a tag (.im-nb). A long formula's pieces are marks of their own,
    with the <wbr> between them outside any unit."""
    def pieces(m):
        k = int(m.group(1))
        parts = formulas[k].split("<wbr>")
        if len(parts) == 1:
            return m.group(0)
        formulas[k] = parts[0]
        marks = [m.group(0)]
        for extra in parts[1:]:
            formulas.append(extra)
            marks.append(f"\x00{len(formulas) - 1}\x00")
        return "<wbr>".join(marks)
    markup = re.sub(r"\x00(\d+)\x00", pieces, markup)
    markup = re.sub(r"[^\s<>\x00\x01]*(?:\x00\d+\x00[^\s<>\x00\x01]*)+",
                    lambda m: f'<span class="im-nb">{m.group(0)}</span>', markup)
    return re.sub(r"[\x00\x01](\d+)[\x00\x01]", lambda m: formulas[int(m.group(1))], markup)


# ------------------------------------------------------------- run on its own

def _check(slugs):
    names = sorted(n[:-5] for n in os.listdir(MAPS) if n.endswith(".json")) if os.path.isdir(MAPS) else []
    bad = 0
    for slug in slugs or names:
        path = os.path.join(MAPS, slug + ".json")
        try:
            doc = Document(path, _source(slug))
        except MapError as e:
            bad += 1
            print(f"!! {e}")
            continue
        joined = sum(e.joined for e in doc.entries)
        print(f"ok {doc.name}: {len(doc.entries)} entries, {sum(e.count for e in doc.entries)} "
              f"places" + (f", {joined} joined" if joined else ""))
    return 1 if bad else 0


def _bold_map():
    """For Site Math's bold face: each character a formula sets, and the Latin
    Modern Math character whose glyph the bold face draws for it. LaTeX's
    \\boldmath takes bold math italic, bold upright letters and bold digits;
    these are the same designs, as Unicode's mathematical bold alphanumerics.
    Operators and delimiters have no bold in the font and stay as they are."""
    out = {}
    for k in range(26):
        out[0x41 + k], out[0x61 + k] = 0x1D400 + k, 0x1D41A + k          # upright
        out[0x1D434 + k], out[0x1D44E + k] = 0x1D468 + k, 0x1D482 + k    # italic
    out[0x210E] = 0x1D489                                                # italic h
    for k in range(10):
        out[0x30 + k] = 0x1D7CE + k
    for k in range(0x391, 0x3AA):                                        # Greek, upright
        if k != 0x3A2:
            out[k] = 0x1D6A8 + k - 0x391
    for k in range(0x3B1, 0x3CA):
        out[k] = 0x1D6C2 + k - 0x3B1
    out.update({0x3F5: 0x1D6DC, 0x3D1: 0x1D6DD, 0x3F0: 0x1D6DE, 0x3D5: 0x1D6DF,
                0x3F1: 0x1D6E0, 0x3D6: 0x1D6E1, 0x2202: 0x1D6DB, 0x2207: 0x1D6C1})
    for k in range(0x1D6E2, 0x1D71C):                                    # Greek, italic
        out[k] = k + 0x3A
    return out


def _cut(source, unicodes, weight):
    """One face of Site Math from Latin Modern Math: the subset, renamed."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    opts = subset.Options()
    # Latin Modern Math files its script-size glyphs (ssty) and dotless
    # letters under the script tag "math", which only Firefox asks for; Chrome
    # and Safari never use them, so they go (they were 839 of 1,735 glyphs)
    opts.layout_features = []
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    opts.glyph_names = False
    opts.hinting = False           # 44 KB with CFF hints, 39 KB without
    opts.desubroutinize = True     # WOFF2's Brotli packs plain charstrings a little better
    font = TTFont(source, recalcTimestamp=False)
    if weight == "Bold":
        swap, best = _bold_map(), font.getBestCmap()
        for table in font["cmap"].tables:       # every subtable, or the old glyph stays
            for cp in list(table.cmap):
                if cp in swap and swap[cp] in best:
                    table.cmap[cp] = best[swap[cp]]
        font["OS/2"].usWeightClass = 700
        font["OS/2"].fsSelection = (font["OS/2"].fsSelection & ~0x40) | 0x20
        font["head"].macStyle |= 1
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=unicodes)
    sub.subset(font)
    if "MATH" not in font:
        sys.exit("the subset lost its MATH table")
    ps = f"{FAMILY.replace(' ', '')}-{weight}"
    names = {1: FAMILY, 16: FAMILY, 2: weight, 17: weight, 6: ps,
             4: FAMILY if weight == "Regular" else f"{FAMILY} {weight}",
             3: f"{ps};a subset of LatinModernMath-Regular 1.959"}
    table = font["name"]
    for rec in table.names:
        if rec.nameID in names:
            rec.string = names[rec.nameID]
    table.names = [r for r in table.names if r.nameID not in (21, 22)]
    note = ("Site Math is a modified version of Latin Modern Math (GUST Font License): a subset "
            "for wavesanddata.com, renamed; its bold face draws Latin Modern Math's own bold "
            "mathematical alphanumerics. See README.txt beside the files.")
    table.setName(note, 10, 1, 0, 0)
    table.setName(note, 10, 3, 1, 0x409)
    cff = font["CFF "].cff
    cff.fontNames = [ps]
    top = cff.topDictIndex[0]
    top.FullName = names[4]
    top.FamilyName = FAMILY
    top.Weight = weight
    font.flavor = "woff2"
    return font


def _font():
    """Site Math, regular and bold: Latin Modern Math cut down to REPERTOIRE,
    MATH table kept, renamed as a modified version (GUST Font License). Beside
    them, METRICS: each character's advance and each italic letter's italic
    correction, read from the regular face's MATH table."""
    from fontTools.ttLib import TTFont
    have = set(TTFont(LM_MATH).getBestCmap())
    lack = sorted(REPERTOIRE - have - _IGNORABLE - {0x2009, 0x00A0})
    lack += sorted({b for a, b in _bold_map().items() if a in REPERTOIRE} - have)
    if lack:
        sys.exit("Latin Modern Math has no " + ", ".join(f"U+{c:04X}" for c in lack))
    unicodes = sorted(REPERTOIRE & have)
    for weight, path in (("Regular", FONT), ("Bold", FONT_BOLD)):
        font = _cut(LM_MATH, unicodes, weight)
        font.save(path)
        print(f"{os.path.relpath(path, HERE)}: {os.path.getsize(path)} bytes, "
              f"{len(font.getBestCmap())} characters, {len(font.getGlyphOrder())} glyphs")
    font = TTFont(FONT)
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    hmtx = font["hmtx"].metrics
    info = font["MATH"].table.MathGlyphInfo.MathItalicsCorrectionInfo
    corr = dict(zip(info.Coverage.glyphs, (v.Value for v in info.ItalicsCorrection)))
    italic = {chr(cp): round(corr[g] / upm, 4) for cp, g in sorted(cmap.items())
              if corr.get(g) and _is_italic(chr(cp))}
    advance = {chr(cp): round(hmtx[g][0] / upm, 4) for cp, g in sorted(cmap.items())}
    with open(METRICS, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"font": os.path.basename(FONT), "advance": advance, "italic": italic}, fh,
                  ensure_ascii=False, indent=0, sort_keys=True)
        fh.write("\n")
    print(f"{os.path.relpath(METRICS, HERE)}: {len(advance)} advances, "
          f"{len(italic)} italic corrections")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args[:1] == ["check"]:
        sys.exit(_check(args[1:]))
    if args[:1] == ["tex"] and len(args) >= 2:
        print(mathml(args[1], "--display" in args[2:]))
        sys.exit(0)
    if args[:1] == ["font"]:
        _font()
        sys.exit(0)
    print(__doc__.split("Run on its own:")[1])
