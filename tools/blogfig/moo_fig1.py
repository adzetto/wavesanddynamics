"""Multi-objective optimization, Figure 1: (a) four points against F1(x) and
F2(x); (b) a variable space over x1 and x2; (c) the objective space F(x) maps
it to, with the Pareto Front along its lower left edge.

The objective space is a smooth closed curve (a periodic cubic spline through
the shape of his sketch); its Pareto Front is computed, not drawn by eye: the
points of the boundary that no other point dominates when both F1 and F2 are
minimized, which the generator asserts is one arc, from the leftmost point of
the boundary to the lowest."""
from geom import closed, front, pt

SLUG, STEM = "multi-objective-optimization", "fig1"
AX, AY = 112.0, 86.0                     # axis lengths, pt
PX = (0.0, 150.0, 300.0)                 # the three panels' axis origins, pt
# the objective space: a closed spline through his shape (fractions of the axes), clockwise
B = closed([(0.08, 0.66), (0.14, 0.82), (0.32, 0.92), (0.56, 0.90), (0.76, 0.86), (0.89, 0.72),
            (0.88, 0.52), (0.78, 0.36), (0.62, 0.24), (0.47, 0.20), (0.30, 0.25), (0.15, 0.40)])
arc = front(B)                           # from the leftmost point of the boundary to the lowest
ends = B[arc[[0, -1]]]


def axes(x0, xl, yl):
    """An axis pair from (x0, 0) and its labels (his words, as maths)."""
    return [rf"\draw[fs axis] {pt(x0, 0)} -- {pt(x0 + AX, 0)};",
            rf"\draw[fs axis] {pt(x0, 0)} -- {pt(x0, AY)};",
            rf"\node[fs axlabel, anchor=west] at {pt(x0 + AX + 2.5, 0)} {{${xl}$}};",
            rf"\node[fs axlabel, anchor=south] at {pt(x0, AY + 2.5)} {{${yl}$}};"]


def body():
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    # (a) four solutions in the objective space
    x0 = PX[0]
    L += axes(x0, r"F_2(x)", r"F_1(x)")
    pts = {"A": (0.25, 0.62), "B": (0.72, 0.62), "C": (0.25, 0.22), "D": (0.72, 0.22)}
    for fx in (0.25, 0.72):
        L.append(rf"\draw[fs aux] {pt(x0 + fx * AX, 0)} -- {pt(x0 + fx * AX, 0.72 * AY)};")
    for fy in (0.62, 0.22):
        L.append(rf"\draw[fs aux] {pt(x0, fy * AY)} -- {pt(x0 + 0.82 * AX, fy * AY)};")
    for k, (fx, fy) in pts.items():
        L.append(rf"\node[fs point] at {pt(x0 + fx * AX, fy * AY)} {{}};")
        L.append(rf"\node[anchor=south west] at {pt(x0 + fx * AX + 2.2, fy * AY + 2.2)} {{${k}$}};")
    # (b) the variable space
    x0 = PX[1]
    L += axes(x0, r"x_2", r"x_1")
    q = lambda fx, fy: pt(x0 + fx * AX, fy * AY)
    L.append(rf"\draw[fs curve] {q(0.12, 0.30)} -- {q(0.12, 0.60)} .. controls {q(0.12, 0.80)} and {q(0.17, 0.86)} "
             rf".. {q(0.28, 0.87)} -- {q(0.84, 0.84)} -- {q(0.84, 0.36)} -- {q(0.56, 0.10)} -- cycle;")
    # (c) the objective space and its Pareto Front
    x0 = PX[2]
    L += axes(x0, r"F_2(x)", r"F_1(x)")
    path = " -- ".join(pt(x0 + x * AX, y * AY) for x, y in B)
    L.append(rf"\draw[fs curve] {path} -- cycle;")
    front = " -- ".join(pt(x0 + x * AX, y * AY) for x, y in B[arc])
    L.append(rf"\draw[fs heavy, dash pattern=on 4pt off 2pt, line cap=butt] {front};")
    for x, y in ends:
        L.append(rf"\node[fs point] at {pt(x0 + x * AX, y * AY)} {{}};")
    lab = (x0 + 0.40 * AX, 0.50 * AY)
    L.append(rf"\node[align=center, font=\small] (pf) at {pt(*lab)} {{Pareto\\Front}};")
    for (x, y), side in zip(ends, ("north west", "south")):
        tx, ty = x0 + x * AX, y * AY
        L.append(rf"\draw[fs vec aux, shorten <=2.5pt, shorten >=2.4pt] (pf.{side}) -- {pt(tx, ty)};")
    # the spaces, and F(x) between them
    L.append(rf"\node[anchor=south] (vs) at {pt(PX[1] + 0.52 * AX, AY + 16)} {{Variable Space}};")
    L.append(rf"\node[anchor=south] (os) at {pt(PX[2] + 0.52 * AX, AY + 16)} {{Objective Space}};")
    # (the tips shorten the drawn arc, which lifts its top about 1 pt above the curve the node is put on)
    L.append(r"\draw[fs vec thin, {fs tip med}-{fs tip med}] ([yshift=3pt]vs.north) to[out=32, in=148] node[above=3.5pt] {$F(x)$} ([yshift=3pt]os.north);")
    for k, x0 in zip("abc", PX):
        L.append(rf"\FigPanel{{({x0 - 14:.2f},{AY + 30:.2f})}}{{{k}}}")
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
