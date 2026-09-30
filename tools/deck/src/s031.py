"""Slide 31: his diagnostic example, X ~ N(0, 1) and Y = X^2.

At mu = 0 the slope is a = f'(0) = 0 and the curvature b = f''(0) = 2. The
first order model keeps Y = f(0) + a delta = 0: its mean and variance are both
zero. The second order model keeps f(0) + a delta + 1/2 b delta^2 = X^2, the
function itself, so it is exact: E[Y] = 1/2 b sigma^2 = 1 and, for a normal
input, Var(Y) = a^2 sigma^2 + 1/2 b^2 sigma^4 = 2 (E[X^4] = 3). The curve is
drawn on his range, X from -3 to 3.

Helpers the later slides of this run (32 to 41) borrow, the shared system
having neither: tw() measures a label in the figures' face from the font files,
legend() draws pgfplots' legend box at any place (fig.py puts it in a corner),
ramp() is a sequential colour scale between two palette colours in OKLab."""
import html
import os
import re
from functools import lru_cache

import numpy as np
from scipy import stats

from fig import Fig, C, DATA_W

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

# his numbers: mean 1, variance 2; the quadratic model's variance agrees
A, B, SIG = 0.0, 2.0, 1.0
assert stats.chi2(1).mean() == 1 and stats.chi2(1).var() == 2
assert A ** 2 * SIG ** 2 + 0.5 * B ** 2 * SIG ** 4 == 2
assert 0.5 * B * SIG ** 2 == 1


# ------------------------------------------------------------------ helpers
@lru_cache(maxsize=None)
def _font(path):
    from fontTools.ttLib import TTFont
    ft = TTFont(os.path.join(ROOT, *path.split("/")))
    return ft.getBestCmap(), ft["hmtx"].metrics, ft["head"].unitsPerEm


def tw(s, size=28):
    """The width in px of a label (HTML, maths allowed) as the figures set it:
    text in CMU Serif, <m>..</m> as mathtype sets it, in Latin Modern Math
    first (as .m does), each face standing in for what the other lacks."""
    import mathtype
    cmu = _font("content/fonts-cmu/cmu-serif-500-roman.woff2")
    lmm = _font("tools/deck/fonts/latinmodern-math-deck.woff2")
    w = 0.0
    for k, part in enumerate(re.split(r"<m>(.*?)</m>", s)):
        maths = k % 2 == 1
        if maths:
            part = mathtype.typeset(part)
        text = html.unescape(re.sub(r"<[^>]+>", "", part))
        for ch in text:
            for cmap, hmtx, upm in ((lmm, cmu) if maths else (cmu, lmm)):
                g = cmap.get(ord(ch))
                if g:
                    w += hmtx[g][0] / upm
                    break
            else:
                w += 0.5
    return w * size


def legend(f, x, y, entries, size=26, pad=16, row=40, sample=48, anchor="north west"):
    """pgfplots' legend (a 1 px ink box on paper) with its `anchor` corner at
    (x, y) in figure px. entries: (label HTML, style) with style keys color,
    width, dash, or kind="area" / "mark". Returns the box (x, y, w, h)."""
    bw = pad + sample + 14 + max(tw(t, size) for t, _ in entries) + pad + 4
    bh = pad * 2 + row * (len(entries) - 1) + size
    bx = x - bw if "east" in anchor else x - bw / 2 if anchor in ("north", "south") else x
    by = y - bh if anchor.startswith("south") else y
    f.rect(bx, by, bw, bh, fill=C.paper, stroke=C.ink, width=1.0)
    for i, (t, st) in enumerate(entries):
        cy = by + pad + size / 2 + i * row
        kind = st.get("kind", "line")
        x0 = bx + pad
        if kind == "area":
            f.rect(x0, cy - 11, sample, 22, fill=st.get("color", C.mist), fill_opacity=st.get("opacity"))
        elif kind == "mark":
            f.circle(x0 + sample / 2, cy, st.get("r", 6), fill=st.get("color", C.navy))
        else:
            f.line([(x0, cy), (x0 + sample, cy)], stroke=st.get("color", C.navy),
                   width=st.get("width", DATA_W - 1), dash=st.get("dash"),
                   cap=st.get("cap", "round" if str(st.get("dash", "")).startswith("0.") else "butt"))
        # a radical is raised over its line; .ml's leading keeps the check from
        # reading that as a second, tightly set line
        f.text(x0 + sample + 14, cy, t, "west", size=size, cls="ml" if "√" in t else "")
    return bx, by, bw, bh


def _lab(hexc):
    c = hexc.lstrip("#")
    rgb = np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)]) / 255
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return m2 @ np.cbrt(m1 @ lin)


def _hex(lab):
    m2i = np.array([[1.0, 0.3963377774, 0.2158037573],
                    [1.0, -0.1055613458, -0.0638541728],
                    [1.0, -0.0894841775, -1.2914855480]])
    m1i = np.array([[4.0767416621, -3.3077115913, 0.2309699292],
                    [-1.2684380046, 2.6097574011, -0.3413193965],
                    [-0.0041960863, -0.7034186147, 1.7076147010]])
    lin = np.clip(m1i @ (m2i @ lab) ** 3, 0, 1)
    rgb = np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055)
    return "#" + "".join(f"{round(v * 255):02X}" for v in rgb)


def ramp(lo, hi):
    """A sequential scale from palette colour lo (t = 0) to hi (t = 1), mixed
    in OKLab: one hue family, light to dark, no rainbow."""
    a, b = _lab(lo), _lab(hi)
    return lambda t: _hex(a + (b - a) * float(np.clip(t, 0, 1)))


# ------------------------------------------------------------------ figure
def parabola():
    f = Fig(832, 394)
    ax = f.axes(118, 8, 690, 296, xlim=(-3.3, 3.3), ylim=(-0.7, 9.7),
                xticks=range(-3, 4), yticks=range(0, 9, 2), grid=True,
                xlabel="<m>X</m> (standardized, dimensionless)", ylabel="<m>Y = X²</m>")
    x = np.linspace(-3, 3, 601)
    ax.plot(x, x ** 2, color=C.blue, width=4.5)
    ax.plot([-3.3, 3.3], [0, 0], color=C.accent, width=3.5, dash="12 8")
    legend(f, ax.x + ax.w / 2, ax.y + 14, [
        ("Exact and second order: <m>Y = X²</m>", {"color": C.blue, "width": 4.5}),
        ("First order at <m>μ = 0</m>: <m>Y ≈ 0</m>", {"color": C.accent, "width": 3.5, "dash": "12 8"}),
    ], anchor="north")
    return f.html()
