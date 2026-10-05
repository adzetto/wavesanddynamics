"""Impulsive noise detection with self-organizing maps, Figure 2: (a) a stretch
of the velocity signal s and its moving median over 17 samples; (b) the
fourth-order difference of s and its moving median over 125 samples.

His plots survive as a picture only; their curves are read back from it by
digitize.py (data/som_fig2.json): each median as a line, each dotted signal
as the dots his plot drew, so the figure draws them as dots again. His
legends stand where his stood, over the same stretch of each plot, so what
they hid stays hidden."""
import json
import os

from geom import dots, pt

SLUG, STEM = "impulsive-noise-detection-with-semi-organizing-map-neural-networks", "fig2"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "som_fig2.json")
AW, AH = 380.0, 78.0                        # each plot's axes, pt
GAP = 46.0                                  # from the lower edge of (a) to the top of (b)
XT = (0.189, 0.1895, 0.19, 0.1905, 0.191, 0.1915)
XL = ("0.189", "0.1895", "0.19", "0.1905", "0.191", "0.1915")
KEYS = {"a": ("$s$", r"$\bar{m}_{17}^{s}$"), "b": (r"$\Delta^4 s$", r"$\bar{m}_{125}^{\Delta^4 s}$")}
# each legend's box, drawn inside his (pt): its top lowered off the median, which ran along
# his box's top edge in (b) and 1 pt above it in (a), and in (b) its right side drawn back
# from the spike at 0.19147 s, which ran 2 pt beside his. What his box hid stays unread and
# white: only the border moves, inward.
SHRINK = {"a": {"drop": 2.0, "pull": 0.0}, "b": {"drop": 3.0, "pull": 2.5}}


def coords(P, scale=1e3):
    return " ".join(f"({x:.7f},{y * scale:.4f})" for x, y in P)


def axis(key, P, y0):
    """One plot, its axes' lower left corner at (0, y0)."""
    (lx0, ly0, lx1, ly1), (fx0, fy0, fx1, fy1) = P["legend_px"], P["frame_px"]
    t = lambda px: 0.189 + (px - fx0) / (fx1 - fx0) * 0.0025
    v = lambda py: -5.0 + (fy1 - py) / (fy1 - fy0) * 10.0
    L = [rf"\begin{{scope}}[yshift={y0:.2f}pt]",       # each plot's lower left corner
         rf"\begin{{axis}}[fs plot, anchor=south west, at={{(0pt,0pt)}}, width={AW}pt, height={AH}pt,"
         r" scale only axis, xmin=0.189, xmax=0.1915, ymin=-5, ymax=5, ytick={-5,0,5},"
         rf" xtick={{{','.join(map(str, XT))}}}, xticklabels={{{','.join(XL)}}},"
         r" xlabel={Time (s)}, ylabel={Velocity (m/s)}, clip=true,"
         r" x tick label style={/pgf/number format/fixed}]"]
    for line in P["solid"]:
        L.append(rf"\addplot[line width=\FigMed, fsLine, line join=round] coordinates {{{coords(line)}}};")
    # his legend, over the same stretch of the plot, its border inside his (SHRINK)
    s = SHRINK[key]
    a, b = (t(lx0), v(ly1)), (t(lx1) - s["pull"] / AW * 0.0025, v(ly0) - s["drop"] / AH * 10.0)
    L.append(rf"\draw[fs thin, fill=white] (axis cs:{a[0]:.7f},{a[1]:.4f}) rectangle (axis cs:{b[0]:.7f},{b[1]:.4f});")
    for k, (style, text) in enumerate(((r"only marks", KEYS[key][0]), ("line", KEYS[key][1]))):
        fy = 0.70 - 0.42 * k               # the two rows, as fractions of the box
        yy = a[1] + (b[1] - a[1]) * fy
        xa = a[0] + (b[0] - a[0]) * 0.08
        xb = a[0] + (b[0] - a[0]) * 0.38
        if k == 0:
            for i in range(7):              # (an axis runs its drawing at its end: no \foreach)
                L.append(rf"\fill[fsLine] (axis cs:{xa + (xb - xa) * i / 6:.7f},{yy:.4f}) circle (0.33pt);")
        else:
            L.append(rf"\draw[line width=\FigMed, fsLine] (axis cs:{xa:.7f},{yy:.4f}) -- (axis cs:{xb:.7f},{yy:.4f});")
        L.append(rf"\node[anchor=west] at (axis cs:{a[0] + (b[0] - a[0]) * 0.46:.7f},{yy:.4f}) {{{text}}};")
    L.append(r"\end{axis}")
    L.append(r"\end{scope}")
    # his dotted signal, the dots he drew (under his legend there are none: it hid them)
    L += dots([((x - 0.189) / 0.0025 * AW, y0 + (y * 1e3 + 5.0) / 10.0 * AH) for x, y in P["dots"]], 0.33)
    L.append(rf"\node[anchor=south west, font=\small] at {pt(0, y0 + AH + 1.5)} {{$\times 10^{{-3}}$}};")
    L.append(rf"\FigPanel{{({-46:.2f},{y0 + AH + 2:.2f})}}{{{key}}}")
    return L


def body():
    with open(DATA, encoding="utf-8") as f:
        D = json.load(f)
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    L += axis("a", D["a"], AH + GAP)
    L += axis("b", D["b"], 0.0)
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body()[:2000])
