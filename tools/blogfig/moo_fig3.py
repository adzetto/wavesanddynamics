"""Multi-objective optimization, Figure 3: the steps of SPEA2, as his flow
chart: his words as he wrote them, his steps numbered as he numbered them;
P_t, EP_t, E_t and t + 1 set as the symbols they are."""
import numpy as np

from geom import Scene, lines_size, pt

SLUG, STEM = "multi-objective-optimization", "fig3"
W = 250.0                                   # content width, pt
XL, XR, XC = 52.0, 194.0, 124.0             # the two top boxes, and the column under them
BOX = {                                     # centre, minimum width and height, content
    "pt": ((XL, -63.0), 74.0, 30.0, r"$P_t$\\(population)"),
    "ep": ((XR, -63.0), 86.0, 30.0, r"$EP_t$ (External\\population)"),
    "ex": ((XC, -131.0), 98.0, 18.0, r"$EP_{t+1}$ (Ex pop)"),
    "mp": ((XC, -179.0), 98.0, 18.0, r"Mating Pool"),
    "pn": ((XC, -232.0), 98.0, 30.0, r"$P_{t+1}$\\(population)"),
}
ND = ("Nondominated", "solutions")


def edge(name, side):
    (x, y), w, h, _ = BOX[name]
    return np.array([x, y + (h / 2 if side == "top" else -h / 2)])


def body():
    S = Scene()
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    L.append(rf"\node[anchor=base] at {pt(W / 2, 0)} {{\large\bfseries SPEA2}};")
    L.append(rf"\node[anchor=base west] at {pt(0, -22)} {{1) Initialize the population}};")
    L.append(rf"\node[anchor=base west] at {pt(0, -36)} {{2) Assign fitness values to $P_t$ and $E_t$}};")
    S.boxes.append((0, -39, W, -14))        # the steps above the chart
    S.boxes.append((0, -215, 14, -80))      # and the column of his step numbers
    for name, ((x, y), w, h, text) in BOX.items():
        L.append(rf"\node[fs box, minimum width={w}pt, minimum height={h}pt] at {pt(x, y)} {{{text}}};")
        S.line([(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2),
                (x - w / 2, y + h / 2), (x - w / 2, y - h / 2)], 0.354)
    # 3) the nondominated solutions of both populations form the next external population
    nd = lines_size(ND)
    for src, dx, side in (("pt", -24.0, -1), ("ep", 24.0, 1)):
        a, b = edge(src, "bottom") + (-16.0 * side, -1.0), edge("ex", "top") + (dx, 1.0)
        L.append(rf"\draw[fs flow] {pt(*a)} -- {pt(*b)};")
        S.line([a, b], 0.354)
        S.tip(a, b, 5.58, 2.5)
    for src, dx, side in (("pt", -24.0, -1), ("ep", 24.0, 1)):
        a, b = edge(src, "bottom") + (-16.0 * side, -1.0), edge("ex", "top") + (dx, 1.0)
        at = a + 0.62 * (b - a)
        node = S.place(r"Nondominated\\solutions", at, (side, 0), 2.5, "align=center", reach=14,
                       box=nd)
        L.append(node)
        if src == "pt":                     # his "3)" on the line of the left label's first word
            cy = float(node.split(" at (")[1].split(",")[1].split(")")[0])
            first = cy + nd[1] / 2 - lines_size(ND[:1])[1]
            L.append(rf"\node[anchor=base west] at {pt(0, first)} {{3)}};")
    # 4) and 5), down the column
    for (top, bot), words, step in ((("ex", "mp"), ("Tournament", "selection"), "4)"),
                                    (("mp", "pn"), ("Recombination", "And Mutation"), "5)")):
        a, b = edge(top, "bottom") + (0, -1.0), edge(bot, "top") + (0, 1.0)
        mid = 0.5 * (a[1] + b[1])
        L.append(rf"\draw[fs flow] {pt(*a)} -- {pt(*b)};")
        L.append(rf"\node[anchor=west, align=center] at {pt(XC + 6, mid)} {{{words[0]}\\{words[1]}}};")
        L.append(rf"\node[anchor=west] at {pt(0, mid)} {{{step}}};")
    L.append(rf"\node[anchor=north west, text width={W}pt, align=left] at {pt(0, -257)} "
             r"{6) Terminate the algorithm if $t$ is at specific number or another stopping criteria "
             r"is met, else $t=t+1$ and go to step 2};")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
