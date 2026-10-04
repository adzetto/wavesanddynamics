"""Impulsive noise detection with self-organizing maps, Figure 1: (a) the
network, a 3 x 3 grid of neurons w_1 ... w_9, each fed every component of
the input vector; (b) the map after training: the neurons where the inputs
gather, in the plane of x and y.

(a) is drawn from its rule: three input lines, each down a bus to every
column, and from the buses one arrow per input into each neuron. (b) keeps
his map: the centres of his neurons and of his 53 input points, read off his
picture (the grey discs and the black dots inside his dashed frame, by
connected components of their pixels), in the frame's own units."""
import numpy as np

from geom import pt, size

SLUG, STEM = "impulsive-noise-detection-with-semi-organizing-map-neural-networks", "fig1"
R = 8.5                                     # neuron radius, pt
FH = 108.5                                  # both frames' height, pt
# (a)
AX0, AX1 = 0.0, 212.0                       # its frame
COLS = (64.0, 126.0, 188.0)                 # neuron columns
ROWS = (-15.0, -47.0, -79.0)                # neuron rows
BUS = (-34.0, -29.0, -24.0)                 # each column's buses, from the neuron column: inputs 1, 2, 3
INY = (18.0, 11.0, 4.0)                     # the input lines, above the frame
ARR = (-7.0, 0.0, 7.0)                      # where inputs 1, 2, 3 meet a neuron, from its row
# (b): his frame, in pixels of his picture, and where it goes
HIS = (648.0, 77.0, 1162.0, 327.0)
BX0 = 228.0
BW = 223.0                                  # its width, pt
K = BW / (HIS[2] - HIS[0])               # pt per pixel of his
NEURONS = {1: (707.0, 165.0), 2: (679.0, 208.0), 3: (731.0, 208.4), 4: (904.0, 122.4),
           5: (888.3, 236.0), 6: (931.9, 229.9), 7: (870.4, 288.2), 8: (1070.0, 171.0),
           9: (1059.6, 221.9)}
INPUTS = [(911.8, 90.2), (872.4, 110.3), (701.3, 127.9), (718.8, 131.3), (687.7, 136.5),
          (736.5, 138.5), (1054.6, 142.5), (1090.2, 143.4), (914.4, 151.2), (679.4, 152.3),
          (742.4, 156.2), (1109.6, 162.5), (736.4, 172.7), (671.6, 173.3), (1035.5, 176.0),
          (686.3, 181.9), (729.7, 182.2), (755.2, 186.0), (1103.5, 186.0), (658.4, 191.0),
          (1045.5, 197.4), (763.4, 198.2), (939.6, 199.4), (706.3, 201.3), (907.9, 201.9),
          (1098.9, 201.9), (1081.2, 203.8), (1032.6, 204.4), (888.9, 206.1), (867.4, 208.6),
          (968.0, 213.3), (1095.8, 215.8), (756.5, 226.0), (1027.3, 227.3), (701.2, 231.8),
          (844.2, 234.2), (965.7, 234.3), (667.2, 234.9), (686.6, 237.5), (1085.6, 238.5),
          (734.2, 239.2), (713.8, 247.0), (958.2, 249.4), (1054.9, 254.6), (873.2, 257.8),
          (925.7, 257.7), (944.5, 257.0), (855.3, 260.3), (903.6, 261.6), (895.6, 271.1),
          (834.6, 279.3), (897.8, 307.2), (855.6, 312.3)]
DOT = 2.8                                   # an input point's diameter, pt


def his(p):
    return np.array([BX0 + (p[0] - HIS[0]) * K, -(p[1] - HIS[1]) * K])


def neuron(L, c, k):
    L.append(rf"\node[circle, draw=fsLine, line width=\FigThin, fill=fsElemFill, minimum size={2 * R}pt, "
             rf"inner sep=0pt] at {pt(*c)} {{$w_{k}$}};")


def axes_sign(L, x, y):
    """His sign of the map's axes: x up, y across, dotted."""
    L.append(rf"\draw[fs axis, dash pattern=on 1pt off 1pt] {pt(x, y)} -- {pt(x, y + 13)};")
    L.append(rf"\draw[fs axis, dash pattern=on 1pt off 1pt] {pt(x, y)} -- {pt(x + 13, y)};")
    L.append(rf"\node[fs axlabel, anchor=south] at {pt(x, y + 15)} {{$x$}};")
    L.append(rf"\node[fs axlabel, anchor=west] at {pt(x + 15, y)} {{$y$}};")


def network():
    L = [rf"\draw[fs aux] {pt(AX0, -FH)} rectangle {pt(AX1, 0)};"]
    # the input vector: three lines, from his bracket to the last column's buses
    L.append(rf"\node[anchor=south west] at {pt(3, INY[0] + 6)} {{Input vector}};")
    L.append(rf"\draw[fs thin] {pt(5.5, INY[0] + 3)} -- {pt(3, INY[0] + 3)} -- {pt(3, INY[2] - 3)} -- {pt(5.5, INY[2] - 3)};")
    for i, y in enumerate(INY):
        L.append(rf"\draw[fs thin, -{{fs tip axis}}] {pt(7, y)} -- {pt(21, y)};")
        L.append(rf"\draw[fs thin] {pt(21, y)} -- {pt(COLS[-1] + BUS[i], y)};")
        for X in COLS:                      # its bus down each column, to its last neuron
            L.append(rf"\draw[fs thin] {pt(X + BUS[i], y)} -- {pt(X + BUS[i], ROWS[-1] + ARR[i])};")
    for r, Y in enumerate(ROWS):
        for c, X in enumerate(COLS):
            for i in range(3):
                y = Y + ARR[i]
                if ARR[i] == 0:
                    L.append(rf"\draw[fs thin, -{{fs tip axis}}] {pt(X + BUS[i], y)} -- {pt(X - R - 0.4, Y)};")
                else:                       # along, then onto the neuron at 150 or 210 degrees
                    a = np.radians(180 - 30 * np.sign(ARR[i]))
                    end = (X + (R + 0.4) * np.cos(a), Y + (R + 0.4) * np.sin(a))
                    L.append(rf"\draw[fs thin, -{{fs tip axis}}] {pt(X + BUS[i], y)} -- {pt(X - 17, y)} -- {pt(*end)};")
            neuron(L, (X, Y), 3 * r + c + 1)
            L.append(rf"\draw[fs thin, dash pattern=on 1pt off 1pt, -{{fs tip axis}}] {pt(X + R + 1, Y)} -- {pt(X + R + 12, Y)};")
    assert all(b + BUS[0] - (a + R + 12) >= 3 for a, b in zip(COLS, COLS[1:])), "an output runs into the next buses"
    axes_sign(L, 6.0, -101.0)
    legend(L, AX1 - 4, -FH + 4, (("neuron", "Neuron"),))
    L.append(rf"\FigPanel{{({AX0 - 12:.2f},{-10:.2f})}}{{a}}")
    return L


def legend(L, xr, yb, rows):
    """A legend box, its lower right corner at (xr, yb)."""
    w = max(size(t)[0] for _, t in rows) + 18
    h = 12.0 * len(rows) + 2
    L.append(rf"\draw[fs thin] {pt(xr - w, yb)} rectangle {pt(xr, yb + h)};")
    for k, (kind, text) in enumerate(rows):
        y = yb + h - 7 - 12 * k
        if kind == "neuron":
            L.append(rf"\node[circle, draw=fsLine, line width=\FigThin, fill=fsElemFill, minimum size=7pt, inner sep=0pt] at {pt(xr - w + 7, y)} {{}};")
        else:
            L.append(rf"\node[fs dot, minimum size={DOT}pt] at {pt(xr - w + 7, y)} {{}};")
        L.append(rf"\node[anchor=west] at {pt(xr - w + 13, y)} {{{text}}};")


def feature_map():
    L = [rf"\draw[fs aux] {pt(BX0, -FH)} rectangle {pt(BX0 + BW, 0)};"]
    assert abs((HIS[3] - HIS[1]) * K - FH) < 0.5, "the map's frame keeps his proportions"
    for p in INPUTS:
        L.append(rf"\node[fs dot, minimum size={DOT}pt] at {pt(*his(p))} {{}};")
    for k, p in NEURONS.items():
        neuron(L, his(p), k)
    gap = min(np.hypot(*(his(p) - his(q))) for p in INPUTS for q in NEURONS.values()) - R - DOT / 2
    assert gap > 0.5, f"an input touches a neuron ({gap:.2f} pt)"
    axes_sign(L, BX0 + 6.0, -101.0)
    legend(L, BX0 + BW - 4, -FH + 4, (("dot", "Input"), ("neuron", "Neuron")))
    L.append(rf"\FigPanel{{({BX0 - 13:.2f},{-10:.2f})}}{{b}}")
    return L


def body():
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    L += network() + feature_map()
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
