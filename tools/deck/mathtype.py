"""His formulas, typeset: <m>..</m> in a slide source becomes Computer Modern
maths, from his own characters.

He typed his mathematics as plain Unicode: "P(a < X < b) = ∫ₐᵇ fₓ(x) dx",
"Cov(X,Y) = E[(X − μₓ)(Y − μᵧ)]", "σ²". A source copies that string as it is
into <m>..</m>, and typeset() sets it the way TeX would:

- a single Latin letter is a variable: italic (<i>);
- a run of two or more letters is a word or an operator name (Cov, Var, exp,
  "find the defect"): upright; "d" before a single letter after a space is a
  differential: upright d, italic letter (dx);
- Greek lower case is italic, Greek capitals upright (TeX's rule);
- digits, signs and brackets are upright;
- his sub- and superscript characters (ₐ ᵇ ₓ ² ...) become real sub- and
  superscripts of the letter they stand for; a subscript run followed by a
  superscript run (∫ₐᵇ) is stacked;
- ∫ is set large.

Nothing is added, dropped or reordered: the text of the result is his string
with each sub/superscript character written as its plain letter, which is
what Unicode's compatibility normalisation (NFKC) says it is. norm() is that
comparison: render.py checks every slide against his file through it.

Markup inside <m> is kept as written (a tag passes through untouched), so a
source can force a reading: <m><i>xy</i></m> sets xy as two variables.
"""

import html as _html
import re
import unicodedata

SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₔₕₖₗₘₙₚₛₜᵢᵣᵤᵥⱼᵦᵧᵨᵩᵪ",
               "0123456789+−=()aeoxəhklmnpstiruvjβyρφχ"))
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱᵃᵇᶜᵈᵉᶠᵍʰʲᵏˡᵐᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁᵂᵝᵞᵟᵠᵡ",
               "0123456789+−=()niabcdefghjklmoprstuvwxyzABDEGHIJKLMNOPRTUWβγδφχ"))
# his small capitals are subscript capitals: vᴅ is v with a subscript D, μʏ
# the mean of Y, yɴ the N-th y (Unicode has no subscript capitals)
SMALLCAP = dict(zip("ᴀʙᴄᴅᴇɢʜɪᴊᴋʟᴍɴᴏᴘʀꜱᴛᴜᴠᴡʏᴢ", "ABCDEGHIJKLMNOPRSTUVWYZ"))
SUB.update(SMALLCAP)
# ᵧ is GREEK SUBSCRIPT GAMMA, which Unicode's normalisation reads as γ; he
# used it for a subscript y (μᵧ, the mean of Y), the glyph it looks like
READ_AS = {"ᵧ": "y", **SMALLCAP}
# a sign between two subscripts belongs to them: Σᵢ<ⱼ is a sum over i < j
JOIN = set("<>=,+−-≤≥")
# the operators CMU Serif lacks; set from Latin Modern Math
OPS = set("∫∑∏∝≈≤≥∞∈∉∼≠⇒⇔∂∩∪∅∀∃∇⊂⊆⊥∥≡≪≫⟨⟩∣′″")
GREEK_LOWER = set("αβγδεζηθικλμνξοπρςστυφχψωϑϕϵϱϰϖ")
COMBINING = re.compile(r"[̀-ͯ]")


def _italic(c):
    """A variable as TeX sets it: the Mathematical Italic letter (Latin Modern
    Math draws it), which Unicode's normalisation reads back as the plain
    letter. CMU's own italic θ is the curly form; this one is TeX's θ."""
    o = ord(c)
    if c == "h":
        return "ℎ"
    if 0x41 <= o <= 0x5A:
        return chr(0x1D434 + o - 0x41)
    if 0x61 <= o <= 0x7A:
        return chr(0x1D44E + o - 0x61)
    if 0x3B1 <= o <= 0x3C9:
        return chr(0x1D6FC + o - 0x3B1)
    return {"ϵ": "𝜖", "ϑ": "𝜗", "ϰ": "𝜘", "ϕ": "𝜙",
            "ϱ": "𝜚", "ϖ": "𝜛"}.get(c, c)


# accents he typed as combining marks: a bar (x̄), a hat (θ̂), a tilde, a dot.
# The mark stays in the text (hidden); the stylesheet draws it over the letter.
ACCENT = {"̄": "bar", "̅": "bar", "̂": "hat", "̃": "tilde", "̇": "dot"}


def _var(run):
    """One variable: a letter, maybe with his accents."""
    base, marks = run[0], run[1:]
    letter = f'<span class="mi">{_italic(base)}</span>'
    if not marks:
        return letter
    kind = ACCENT.get(marks[0], "")
    low = " lo" if base.islower() and base not in "bdfhkltβδζθλξϑ" else ""
    hidden = "".join(f'<span class="mk">{m}</span>' for m in marks)
    return f'<span class="acc {kind}{low}">{letter}{hidden}</span>' 
TAG = re.compile(r"(<(?:/?[A-Za-z][^<>]*)>)")


def norm(s):
    """His text and ours, compared on what they say: sub/superscript
    characters as their letters (NFKC), whitespace collapsed, the minus sign
    and the hyphen-minus one character."""
    for a, b in READ_AS.items():
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("−", "-").replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return " ".join(s.split())


def _esc(s):
    return _html.escape(s, quote=False)


def _script(chars, table):
    return "".join(table[c] for c in chars)


def _body(text):
    """Typeset one run of plain text (no tags)."""
    # a letter he typed with its accent built in (ẋ, Ŷ) is the letter and a mark
    text = "".join(unicodedata.normalize("NFD", ch) if ch.isalpha() and ch not in SUB and ch not in SUP
                   else ch for ch in text)
    out = []
    i, n = 0, len(text)
    prev = " "
    while i < n:
        c = text[i]
        # a sub- or superscript run, maybe stacked with the other kind after it
        if c in SUB or c in SUP:
            j = i
            kind = SUB if c in SUB else SUP
            while j < n and (text[j] in kind or
                             (text[j] in JOIN and j + 1 < n and text[j + 1] in kind)):
                j += 1
            first = _body("".join(kind.get(ch, ch) for ch in text[i:j]))
            other = SUP if kind is SUB else SUB
            k = j
            while k < n and text[k] in other:
                k += 1
            tag1 = "sub" if kind is SUB else "sup"
            if k > j:
                second = _body(_script(text[j:k], other))
                tag2 = "sup" if tag1 == "sub" else "sub"
                out.append(f'<span class="ss"><{tag1}>{first}</{tag1}><{tag2}>{second}</{tag2}></span>')
                i = k
            else:
                out.append(f"<{tag1}>{first}</{tag1}>")
                i = j
            prev = "x"
            continue
        if "A" <= c <= "Z" or "a" <= c <= "z":
            j = i
            while j < n and ("A" <= text[j] <= "Z" or "a" <= text[j] <= "z" or COMBINING.match(text[j])):
                j += 1
            run = text[i:j]
            letters = COMBINING.sub("", run)
            nxt = text[j] if j < n else " "
            if len(letters) == 1:
                out.append(_var(run))
            elif (len(letters) == 2 and letters[0] == "d" and prev in " (" and not nxt.isalpha()
                  and not COMBINING.match(run[1:2] or " ")):
                out.append(f'd{_var(run[1:])}')
            else:
                out.append(f'<span class="w">{_esc(run)}</span>')
            prev = run[-1]
            i = j
            continue
        if c in GREEK_LOWER:
            j = i + 1
            while j < n and COMBINING.match(text[j]):
                j += 1
            out.append(_var(text[i:j]))
            prev = c
            i = j
            continue
        if c == " " and text[i:i + 3] == "   ":
            # his wide gap between two formulas on one line
            j = i
            while j < n and text[j] == " ":
                j += 1
            out.append('<span class="qq"> </span>')
            prev = " "
            i = j
            continue
        if c == "√":
            # a radical over the number or letter that follows it
            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == "." or COMBINING.match(text[j])):
                j += 1
            if j > i + 1:
                out.append(f'<span class="sqrt"><span class="op">√</span><span class="rad">{_body(text[i + 1:j])}</span></span>')
            else:                     # √(..): his brackets show what it covers
                out.append('<span class="sqrt"><span class="op">√</span></span>')
            prev = "x"
            i = j
            continue
        if c == "∫":
            out.append('<span class="op int">∫</span>')
        elif c in OPS:
            out.append(f'<span class="op">{_esc(c)}</span>')
        else:
            out.append(_esc(c))
        prev = c
        i += 1
    return "".join(out)


def typeset(src):
    """The inside of one <m>..</m>: his characters in, maths markup out.
    Tags inside pass through; entities are read first."""
    parts = TAG.split(src)
    return "".join(p if TAG.fullmatch(p) else _body(_html.unescape(p)) for p in parts)


M = re.compile(r"<m>(.*?)</m>", re.S)


def expand(markup):
    """Every <m>..</m> in a slide's markup, typeset."""
    return M.sub(lambda mo: f'<span class="m">{typeset(mo.group(1))}</span>', markup)


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for s in sys.argv[1:] or ["P(a < X < b) = ∫ₐᵇ fₓ(x) dx", "Cov(X,Y) = E[(X − μₓ)(Y − μᵧ)]",
                              "P(find the defect) = 3/25 = 12%", "σ² = 4 MPa²", "p(θ|D) ∝ p(D|θ) p(θ)"]:
        print(s, "\n  ->", typeset(s))
