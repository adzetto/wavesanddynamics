"""Slide 13: his 32 illustrative cylinder tests, the normal model fitted to
them, and the strength with 5% of that model below it.

The tests are the 32 values slide 12's normal Q-Q plot shows (s012.TESTS):
his reconstructed sample (his notes: n = 32, sample mean 32.1 MPa, sample SD
3.1 MPa), a seeded random draw from N(32.1, 3.1^2) MPa rescaled to exactly
those statistics. The fitted normal is N(32.1, 3.1^2); its 5th percentile,
32.1 - 1.645 x 3.1 = 27.00 MPa, is his 27.0. The histogram has his 2 MPa bins
from 25 to 39 MPa, drawn as a density so the fitted curve sits on it.

Also here, for slides 13, 15 and 19: legend(), pgfplots' legend box as
fig.Axes.legend draws it, but as wide as its words are in Computer Modern
(measured from the CMU Serif font the figures use), so the box closes on the
text with the same margin on both sides."""
import functools
import html
import os
import re

import numpy as np
from scipy import stats

from fig import Fig, C, DATA_W
from s012 import TESTS

MEAN, SD = TESTS.mean(), TESTS.std(ddof=1)
FIT = stats.norm(MEAN, SD)
Q05 = FIT.ppf(0.05)
assert (round(MEAN, 1), round(SD, 1), round(Q05, 1)) == (32.1, 3.1, 27.0)
EDGES = np.arange(25, 40, 2)                      # 25, 27, ..., 39 MPa
assert EDGES[0] < TESTS.min() and TESTS.max() < EDGES[-1]


# ------------------------------------------------------------------ legend
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


@functools.lru_cache(maxsize=1)
def _cmu():
    from fontTools.ttLib import TTFont
    font = TTFont(os.path.join(ROOT, "content", "fonts-cmu", "cmu-serif-500-roman.woff2"))
    return font["head"].unitsPerEm, font.getBestCmap(), font["hmtx"]


def text_width(s, size):
    """The advance width of a label's words in CMU Serif at `size` px."""
    upm, cmap, hmtx = _cmu()
    plain = html.unescape(re.sub(r"<[^>]+>", "", s))
    return sum(hmtx[cmap[ord(ch)]][0] for ch in plain) / upm * size


def legend(ax, entries, at="north east", size=26, row=38, pad=16, sample=44, gap=12, inset=14):
    """fig.Axes.legend with the box fitted to its words. entries are (label,
    style) as there: color, width, dash, opacity, kind='area' or 'mark'. `at`
    is a corner of the axes, or (x, y), the box's top left in figure px."""
    f = ax.f
    bw = pad + sample + gap + max(text_width(t, size) for t, _ in entries) + pad
    bh = 2 * pad + row * (len(entries) - 1) + size
    if isinstance(at, tuple):
        bx, by = at
    else:
        bx = ax.x + ax.w - inset - bw if "east" in at else ax.x + inset
        by = ax.y + inset if "north" in at else ax.y + ax.h - inset - bh
    f.rect(bx, by, bw, bh, fill=C.paper, stroke=C.ink, width=1.0)
    for i, (t, st) in enumerate(entries):
        cy = by + pad + size / 2 + i * row
        kind = st.get("kind", "line")
        if kind == "area":
            f.rect(bx + pad, cy - 10, sample, 20, fill=st.get("color", C.mist),
                   fill_opacity=st.get("opacity"))
        elif kind == "mark":
            f.circle(bx + pad + sample / 2, cy, st.get("r", 6), fill=st.get("color", C.navy))
        else:
            f.line([(bx + pad, cy), (bx + pad + sample, cy)], stroke=st.get("color", C.navy),
                   width=st.get("width", DATA_W - 1), dash=st.get("dash"), cap="butt")
        f.text(bx + pad + sample + gap, cy, t, "west", size=size)
    return bx, by, bw, bh


# ------------------------------------------------------------------ the figure
def fitted():
    f = Fig(976, 650)
    ax = f.axes(136, 14, 822, 500, xlim=(20, 44), ylim=(0, 0.19),
                xticks=[20, 25, 27, 30, 35, 40], yticks=np.arange(0, 0.161, 0.04),
                ytick_nd=2, xlabel="28-day compressive strength (MPa)",
                ylabel="Probability density")
    ax.hist(TESTS, EDGES, color=C.steel2, stroke=C.navy, gap=0)
    lo = np.linspace(20, Q05, 300)
    ax.area(lo, FIT.pdf(lo), color=C.amber, opacity=0.85)
    x = np.linspace(20, 44, 900)
    ax.plot(x, FIT.pdf(x), color=C.navy, width=4)
    ax.vline(Q05, color=C.accent, width=2.5, dash="9 7")
    legend(ax, [("32 illustrative tests", {"kind": "area", "color": C.steel2}),
                ("Fitted normal model", {"color": C.navy, "width": 4}),
                ("Lower 5%", {"kind": "area", "color": C.amber, "opacity": 0.85})])
    return f.html()
