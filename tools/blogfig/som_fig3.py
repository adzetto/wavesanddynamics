"""Impulsive noise detection with self-organizing maps, Figure 3: (a) the
input space u^s, his zoom box over its middle, shown in (b); (c) the neurons
of the map spread over it; (d) the mean distances MD sorted, his two lines
and the knee point where the curve bends; (e) the points kept.

His plots survive as a picture only; digitize.py read them back
(data/som_fig3.json): each isolated point of a cloud as a point, and where
his points ran together into solid ink, that ink as filled shapes; in (d)
the curve, his two straight lines (each fitted to its own dashes, each
drawn as his ran: Line 1 from the axis to Line 2, Line 2 from the axis to
the plot's edge), the ring of the knee point, his label and his legend
where they stood. The axes, ticks and labels are drawn here, in the house
style, over the plots' own data ranges."""
import json
import os

from geom import dots, pt, simplify

SLUG, STEM = "impulsive-noise-detection-with-semi-organizing-map-neural-networks", "fig3"
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "som_fig3.json")
AW, AH = 95.0, 106.0                        # each plot's axes, pt (his are 0.9 as wide as high)
ROW1, ROW2 = 0.0, -150.0                    # the axes' lower edges
X = {"a": 42.0, "b": 194.0, "c": 346.0}
X["d"] = 0.5 * (X["a"] + X["b"])
X["e"] = 0.5 * (X["b"] + X["c"])
Y = {"a": ROW1, "b": ROW1, "c": ROW1, "d": ROW2, "e": ROW2}
M3 = (-3e-3, 3e-3)
LIM = {"a": ((-0.04, 0.04), (-0.04, 0.04)), "b": (M3, M3), "c": (M3, M3), "e": (M3, M3),
       "d": ((0.0, 4750.0), (0.0, 4e-4))}
UX, UY = r"$u_x^s$ (m/s)", r"$u_y^s$ (m/s)"
DOT = 0.36                                  # a point's radius, pt


def to_pt(k, x, y):
    (xa, xb), (ya, yb) = LIM[k]
    return (X[k] + (x - xa) / (xb - xa) * AW, Y[k] + (y - ya) / (yb - ya) * AH)


def frame(k, xticks, xlabels, yticks, ylabels, xlabel, ylabel, scale=None):
    """The axes of plot k as pgfplots draws them: frame, ticks, labels; no data."""
    (xa, xb), (ya, yb) = LIM[k]
    L = [rf"\begin{{scope}}[shift={{({X[k]:.2f}pt,{Y[k]:.2f}pt)}}]",
         rf"\begin{{axis}}[fs plot, anchor=south west, at={{(0pt,0pt)}}, width={AW}pt, height={AH}pt,"
         r" tick label style={font=\footnotesize},"
         rf" scale only axis, xmin={xa}, xmax={xb}, ymin={ya}, ymax={yb},"
         rf" xtick={{{','.join(map(str, xticks))}}}, xticklabels={{{','.join(xlabels)}}},"
         rf" ytick={{{','.join(map(str, yticks))}}}, yticklabels={{{','.join(ylabels)}}},"
         rf" xlabel={{{xlabel}}}, ylabel={{{ylabel}}}]",
         r"\addplot[draw=none] coordinates {(0,0)};",
         r"\end{axis}", r"\end{scope}"]
    if scale:
        L.append(rf"\node[anchor=south west, font=\small] at {pt(X[k], Y[k] + AH + 4)} {{$\times 10^{{{scale}}}$}};")
    L.append(rf"\FigPanel{{({X[k] - 42:.2f},{Y[k] + AH + 3:.2f})}}{{{k}}}")
    return L


def cloud(k, P):
    """A scatter: its points, and its solid ink as one even-odd filled path."""
    L = []
    L += dots([to_pt(k, x, y) for x, y in P["dots"]], DOT)
    shapes = []
    for poly in P["polys"]:
        Q = simplify([to_pt(k, x, y) for x, y in poly], 0.06)
        if len(Q) >= 3:
            shapes.append(" -- ".join(pt(*q) for q in Q) + " -- cycle")
    if shapes:
        L.append(r"\fill[fsLine, even odd rule] " + " ".join(shapes) + ";")
    return L


def knee(P):
    k = "d"
    L = []
    c = [to_pt(k, x, y) for x, y in P["curve"]]
    L.append(r"\draw[fs heavy, line join=round, line cap=round] " + " -- ".join(pt(*q) for q in c) + ";")
    for x, y in P["tail"]:
        L.append(rf"\fill[fsLine] {pt(*to_pt(k, x, y))} circle ({DOT + 0.2}pt);")
    l1 = [to_pt(k, x, y) for x, y in P["line1"]]
    l2 = [to_pt(k, x, y) for x, y in P["line2"]]
    L.append(rf"\draw[fs med, dash pattern=on 4pt off 1.6pt on 1pt off 1.6pt] {pt(*l1[0])} -- {pt(*l1[1])};")
    L.append(rf"\draw[fs med, dash pattern=on 1.1pt off 1.3pt] {pt(*l2[0])} -- {pt(*l2[1])};")
    kx, ky, kr = P["knee"]
    r = kr / 4750 * AW
    L.append(rf"\draw[fs thin] {pt(*to_pt(k, kx, ky))} circle ({r:.2f}pt);")
    L.append(rf"\node[align=center, font=\small] at {pt(*to_pt(k, *P['label']))} {{Knee\\point}};")
    # his legend, over the same stretch of the plot
    lx0, ly0, lx1, ly1 = P["legend"]
    a, b = to_pt(k, lx0, ly0), to_pt(k, lx1, ly1)
    from geom import size
    need = 3 + 14 + 3 + max(size(rf"\small {t}")[0] for t in ("$MD_j^s$", "Line 1", "Line 2")) + 3.5
    b = (max(b[0], a[0] + need), b[1])      # his box, widened over the empty plot to hold the words
    a = (a[0], b[1] - 6 - 11 * 3)            # and as deep as its three rows
    L.append(rf"\draw[fs thin, fill=white] {pt(*a)} rectangle {pt(*b)};")
    rows = (("dot", "$MD_j^s$"), ("l1", "Line 1"), ("l2", "Line 2"))
    for i, (kind, text) in enumerate(rows):
        yy = b[1] - 3 - 5.5 - 11 * i
        xa, xb = a[0] + 3, a[0] + 17
        if kind == "dot":
            L.append(rf"\fill[fsLine] {pt(0.5 * (xa + xb), yy)} circle ({DOT + 0.2}pt);")
        elif kind == "l1":
            L.append(rf"\draw[fs med, dash pattern=on 4pt off 1.6pt on 1pt off 1.6pt] {pt(xa, yy)} -- {pt(xb, yy)};")
        else:
            L.append(rf"\draw[fs med, dash pattern=on 1.1pt off 1.3pt] {pt(xa, yy)} -- {pt(xb, yy)};")
        L.append(rf"\node[anchor=west, font=\small] at {pt(xb + 3, yy)} {{{text}}};")
    return L


def body():
    with open(DATA, encoding="utf-8") as f:
        D = json.load(f)
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    t4 = (-0.04, -0.02, 0, 0.02, 0.04)
    l4 = ("$-0.04$", "$-0.02$", "$0$", "$0.02$", "$0.04$")
    t3 = (-3e-3, -2e-3, -1e-3, 0, 1e-3, 2e-3, 3e-3)
    l3 = ("$-3$", "$-2$", "$-1$", "$0$", "$1$", "$2$", "$3$")
    L += frame("a", t4, l4, t4, l4, UX, UY)
    for k in "bce":
        L += frame(k, t3, l3, t3, l3, UX, UY, "-3")
    L += frame("d", (0, 950, 1900, 2850, 3800, 4750), ("0", "950", "1900", "2850", "3800", "4750"),
               (0, 1e-4, 2e-4, 3e-4, 4e-4), ("0", "1", "2", "3", "4"), "Number of neurons", r"$MD_i^s$", "-4")
    for k in "abce":
        L += cloud(k, D[k])
    L += knee(D["d"])
    # his zoom box over (a), and the dashed lines from it to (b)
    zx0, zy0, zx1, zy1 = D["a"]["zoom"]
    p0, p1 = to_pt("a", zx0, zy0), to_pt("a", zx1, zy1)
    L.append(rf"\draw[fs med, dash pattern=on 1.1pt off 1.1pt] {pt(*p0)} rectangle {pt(*p1)};")
    for (sx_, sy_), (ex_, ey_) in (((p1[0], p1[1]), (X["b"], Y["b"] + AH)), ((p1[0], p0[1]), (X["b"], Y["b"]))):
        f = (X["b"] - 15 - sx_) / (ex_ - sx_)  # toward (b)'s corner, short of its tick labels
        L.append(rf"\draw[fs aux] {pt(sx_, sy_)} -- {pt(sx_ + f * (ex_ - sx_), sy_ + f * (ey_ - sy_))};")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body()[:3000])
