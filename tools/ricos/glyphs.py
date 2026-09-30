"""Characters that stand for other characters.

Two things in a Word file are not the character they show. A `w:sym` names a
glyph by its position in a symbol font - the arrow the ML guide draws twice is
`Wingdings` `F0E0`, and Word writes nothing else for it - and a super- or
subscript run holds the ordinary characters with a mark that raises them.
Ricos holds plain text in both cases, so the glyph has to be looked up here
and the script has to become a character of its own where Unicode has one.

The symbol tables are the Adobe Symbol encoding and the Wingdings positions
Word actually uses in these documents' genre: bullets, ticks, arrows, Greek.
They are not complete - Wingdings has 224 glyphs and most are ornaments - and
a position that is not here comes back as U+FFFD, the replacement character,
on purpose: visible on the page and countable in the manifest, where a
silently dropped glyph is neither.
"""

# Adobe Symbol: the letter positions are Greek, the rest are operators.
_GREEK = ("ΑΒΧΔΕΦΓΗΙϑΚΛΜΝΟΠΘΡΣΤΥςΩΞΨΖ", "αβχδεφγηιϕκλμνοπθρστυϖωξψζ")
SYMBOL = {
    **{0x41 + i: g for i, g in enumerate(_GREEK[0])},
    **{0x61 + i: g for i, g in enumerate(_GREEK[1])},
    0x22: "∀",
    0x24: "∃",
    0x27: "∍",
    0x40: "≅",
    0xA3: "≤",
    0xA5: "∞",
    0xAB: "↔",
    0xAC: "←",
    0xAD: "↑",
    0xAE: "→",
    0xAF: "↓",
    0xB0: "°",
    0xB1: "±",
    0xB3: "≥",
    0xB4: "×",
    0xB5: "∝",
    0xB6: "∂",
    0xB7: "•",
    0xB8: "÷",
    0xB9: "≠",
    0xBA: "≡",
    0xBB: "≈",
    0xC5: "⊕",
    0xC7: "∩",
    0xC8: "∪",
    0xCE: "∈",
    0xCF: "∉",
    0xD1: "∇",
    0xD6: "√",
    0xD7: "⋅",
    0xE5: "∑",
    0xF2: "∫",
}

WINGDINGS = {
    0x6C: "●",
    0x6E: "■",
    0x6F: "□",
    0x75: "◆",
    0x76: "❖",
    0xA7: "▪",
    0xD8: "➢",
    0xDC: "➜",
    0xE0: "→",
    0xE8: "⇨",
    0xFB: "✗",
    0xFC: "✓",
    0xFD: "☒",
    0xFE: "☑",
}

FONTS = {"symbol": SYMBOL, "wingdings": WINGDINGS}

UNMAPPED = "�"


def symbol(font, char):
    """The character a `w:sym` shows, or U+FFFD when this table does not know.

    `char` is the hexadecimal position Word wrote. Symbol fonts are addressed
    through the private-use area, F000 to F0FF, so the low byte is the
    position; a value outside that range is an ordinary code point and is
    taken as one.
    """
    try:
        code = int(char or "", 16)
    except ValueError:
        return UNMAPPED
    if 0xF000 <= code <= 0xF0FF:
        return FONTS.get((font or "").lower(), {}).get(code & 0xFF, UNMAPPED)
    if 0 < code < 0xE000:
        return chr(code)
    return UNMAPPED


# The super- and subscript forms Unicode gives a character of its own. The
# digits, signs and brackets render everywhere; of the letters only the
# subscript set and superscript n and i are kept, because the rest are
# phonetic modifier letters that fonts draw unevenly or not at all.
SUPERSCRIPT = dict(zip("0123456789+-−=()ni ", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾ⁿⁱ "))
SUBSCRIPT = dict(
    zip("0123456789+-−=()aehijklmnoprstuvx ", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ ")
)
LINEAR = {"super": "^", "sub": "_"}


def script(text, kind):
    """`text` raised or lowered: as glyphs where every character has one,
    otherwise in the `^`/`_` notation of Word's linear equation format.

    The notation groups anything longer than one character, so that `P_A`
    and `x^(i+1)` read the way the author's equation editor reads them back.
    `kind` is "super" or "sub"; anything else returns the text as it is.
    """
    table = {"super": SUPERSCRIPT, "sub": SUBSCRIPT}.get(kind)
    if table is None or not text:
        return text
    if all(c in table for c in text):
        return "".join(table[c] for c in text)
    return LINEAR[kind] + (text if len(text) == 1 else f"({text})")
