"""Laser Doppler vibrometer, the speckle figure: three charts against the
distance to the surface (the change in the speckle size d_s, in M, and in
the variance of the Doppler phase), and his notes beside them: the
equations he used, what their symbols are, and what follows.

His words are his, as he wrote them ("dedector", "an Polytec", "Z" in the
text and z in the equation), none broken at a line's end. His charts survive as a picture only;
digitize.py read their curves back (data/ldv_speckle.json), each as the
corners of the polyline he plotted, in units of the charts' own gridlines:
his charts give no values up the side, so neither do these. Each chart's
title is the label he set up its side, set across it here. Over the third
chart are his thick stroke, his circle round it and his note, where he put
them; his arrow from the circle to the note is drawn long enough to carry
its head."""
import json
import os

import numpy as np

from geom import pt, size

SLUG, STEM = "laser-doppler-vibrometer-how-it-works-advantages-and-disadvantages-speckle-noise", "fig-speckle"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ldv_speckle.json")
AW, AH = 180.0, 58.0                        # each chart's axes, pt
X0 = 6.0                                    # the charts' left edge
YS = {"a": 0.0, "b": -112.0, "c": -224.0}   # the charts' lower edges
TITLES = {"a": r"Change in $d_s$ with respect to distance",
          "b": r"Change in $M$ with respect to distance",
          "c": r"Change in $\textit{var}[\textit{doppler phase}]$ with respect to distance"}
TX = 214.0                                  # his notes' left edge
TW = 248.0                                  # and their width
NOTES = r"""\setlength{\parindent}{0pt}\setlength{\parskip}{0pt}\hyphenpenalty=10000\exhyphenpenalty=10000%
\[ d_s = \frac{4\lambda z}{\pi d_l} \qquad\text{From [4]} \]
Z is the distance between LDV and surface\\
$d_l$ is the beam spot diameter (I took these values from an Polytec LDV datasheet)\\
$d_s$= speckle size seen by the LDV
\[ \textit{Var}[\textit{phase of doppler signal}] = \frac{\pi^2}{3M^{0.85}} \qquad\text{From [7,8]} \]
\[ M = \frac{\textit{Size of LDV dedector (constant)}}{d_s} \]
\begin{list}{-}{\setlength{\leftmargin}{1.3em}\setlength{\labelwidth}{0.8em}\setlength{\labelsep}{0.5em}%
\setlength{\itemsep}{3pt}\setlength{\parsep}{0pt}\setlength{\topsep}{2pt}}
\item M is like the intensity of speckles (how many speckles seen by the LDV)
\item If you keep the distance and change only the spot size, $d_s$ decreases, M increases, and variance
of doppler phase decreases leading to less noise. This can be explained by the fact that the population
of speckle noise changes more slowly when more speckles are seen by the LDV detector as a result of
speckle size getting smaller.
\end{list}"""


def to_pt(k, x, y):
    return (X0 + x / 6000.0 * AW, YS[k] + y / 5.0 * AH)


def grid(k, holes=()):
    """His gridlines, every 1000 mm across and every line up, each broken
    where it would run through a label: holes are pt boxes (x0, y0, x1, y1)."""
    L = []
    segs = [((X0 + i / 6 * AW, YS[k]), (X0 + i / 6 * AW, YS[k] + AH)) for i in range(0, 7)]
    segs += [((X0, YS[k] + j / 5 * AH), (X0 + AW, YS[k] + j / 5 * AH)) for j in range(1, 6)]
    for (ax_, ay_), (bx_, by_) in segs:
        # the stretches of the line outside every hole
        if ax_ == bx_:
            lo, hi, fixed, vert = ay_, by_, ax_, True
        else:
            lo, hi, fixed, vert = ax_, bx_, ay_, False
        cuts = []
        for x0_, y0_, x1_, y1_ in holes:
            if vert and x0_ <= fixed <= x1_:
                cuts.append((y0_, y1_))
            if not vert and y0_ <= fixed <= y1_:
                cuts.append((x0_, x1_))
        pieces, at = [], lo
        for c0, c1 in sorted(cuts):
            if c0 > at:
                pieces.append((at, min(c0, hi)))
            at = max(at, c1)
        if at < hi:
            pieces.append((at, hi))
        for p0, p1 in pieces:
            a_, b_ = ((fixed, p0), (fixed, p1)) if vert else ((p0, fixed), (p1, fixed))
            L.append(rf"\draw[line width=\FigHair, draw=fsLine!25] {pt(*a_)} -- {pt(*b_)};")
    return L


def chart(k, P, holes=()):
    y0 = YS[k]
    L = [rf"\begin{{scope}}[shift={{({X0:.2f}pt,{y0:.2f}pt)}}]",
         rf"\begin{{axis}}[fs plot, anchor=south west, at={{(0pt,0pt)}}, width={AW}pt, height={AH}pt,"
         r" scale only axis, xmin=0, xmax=6000, ymin=0, ymax=5, axis x line*=bottom, axis y line=none,"
         r" xtick={0,1000,2000,3000,4000,5000,6000},"
         r" xticklabels={0,1000,2000,3000,4000,5000,6000}, tick label style={font=\footnotesize},"
         r" xlabel={Distance (mm)}, major tick length=0pt]",
         r"\addplot[draw=none] coordinates {(0,0)};",
         r"\end{axis}", r"\end{scope}"]
    L = grid(k, holes) + L
    c = [to_pt(k, x, y) for x, y in P["curve"]]
    L.append(r"\draw[fs med, line join=round] " + " -- ".join(pt(*q) for q in c) + ";")
    L.append(rf"\node[anchor=south, font=\small, text width={AW + 12}pt, align=center] at "
             rf"{pt(X0 + AW / 2, y0 + AH + 4)} {{{TITLES[k]}}};")
    return L


def remarks(P):
    """Over the third chart: his thick stroke, his circle, his note and the arrow to it."""
    k = "c"
    L = []
    a, b = (to_pt(k, *q) for q in P["stroke"])
    L.append(rf"\draw[line width=2pt, fsLine, line cap=round] {pt(*a)} -- {pt(*b)};")
    cx, cy, rx, ry = P["ring"]
    c = np.array(to_pt(k, cx, cy))
    rxp, ryp = rx / 6000.0 * AW, ry / 5.0 * AH
    L.append(rf"\draw[fs thin] {pt(*c)} ellipse ({rxp:.2f}pt and {ryp:.2f}pt);")
    nx0, ny0, nx1, ny1 = P["note"]
    words = ("Real variance in lower distance", "due to curvature effect")
    w = max(size(rf"\small {t}")[0] for t in words)
    h = 2 * 11.0
    # his note where his stood, by its upper left corner, and his arrow from the circle to it; at
    # this size the gap between them is too short for an arrow with its head, so the note moves
    # out along the arrow until the arrow is 12 pt long
    tl = np.array(to_pt(k, nx0, ny1))
    d = tl - c
    u = d / np.hypot(*d)
    t = 1.0 / np.hypot(d[0] / rxp, d[1] / ryp)             # where the line from the centre leaves the circle
    start = c + d * t + u * 1.2
    end = tl - 2.0 * np.sign(d)                             # short of the note's corner
    if np.dot(end - start, u) < 12.0:
        end = start + u * 12.0
        tl = end + 2.0 * np.sign(d)
    L.append(rf"\node[anchor=north west, align=left, font=\small] at {pt(*tl)} {{{words[0]}\\{words[1]}}};")
    L.append(rf"\draw[fs vec thin] {pt(*start)} -- {pt(*end)};")
    return L, (tl, w, h), end


def body():
    with open(DATA, encoding="utf-8") as f:
        D = json.load(f)
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    rem, (tl, w, h), end = remarks(D["c"])
    note = (tl[0] - 2.0, tl[1] - h - 2.5, tl[0] + w + 2.0, tl[1] + 2.0)
    for k in "abc":
        L += chart(k, D[k], [note] if k == "c" else [])
    L += rem
    L.append(rf"\node[anchor=north west, text width={TW}pt, align=justify, inner sep=0pt] at "
             rf"{pt(TX, YS['a'] + AH + 16)} {{{NOTES}}};")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
