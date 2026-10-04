"""Stationary wavelet package transformation, Figure 1: (a) the wavelet packet
tree to level 3, each node split by the low-pass and high-pass filters L and
H and down-sampled by 2; (b) the time-frequency tiling of the level 3
packets; (c) the tiling of the wavelet transform, D_1, AD_2 and AAD_3.

His labels as he wrote them, in his order (AAA_3 at the top of (b)). The
tree's places are computed from its leaves up: each node's L and H boxes sit
beside it, its children under them. In (c) the bands are 4 : 2 : 1 high and
cut into 16, 8 and 4 cells, so every cell has the same area, as a tiling's
cells do. The panels (b) and (c) stand under the tree: beside it the
figure would be wider than the post."""
from geom import pt, size

SLUG, STEM = "stationary-wavelet-package-transformation", "fig1"
W = 462.0
XS = W / 2                                  # the signal box
SPLIT = {"A": -92.0, "D": 92.0}             # level 1, from the signal
SUB = 48.0                                  # level 2, from its parent
LEAF = 22.0                                 # level 3, from its parent (under its L and H boxes)
ROW = {"s": 0.0, "1": -46.0, "2": -92.0, "3": -138.0}   # node rows, pt
FILT = 11.0                                 # the L and H boxes, pt square


def filters(L, x, y, name, half_w):
    """The L and H boxes beside a node (centre x, y, half width half_w): their
    centres, and the lines that join them to it."""
    xl, xh = x - half_w - 4 - FILT / 2, x + half_w + 4 + FILT / 2
    for xf, t in ((xl, "L"), (xh, "H")):
        L.append(rf"\node[fs box, rounded corners=0.8pt, inner sep=0pt, minimum size={FILT}pt] at {pt(xf, y)} {{{t}}};")
    L.append(rf"\draw[fs thin] {pt(x - half_w, y)} -- {pt(xl + FILT / 2, y)};")
    L.append(rf"\draw[fs thin] {pt(x + half_w, y)} -- {pt(xh - FILT / 2, y)};")
    return xl, xh


def branch(L, xf, y, xc, yc, top_c):
    """From a filter box at (xf, y) to the child at (xc, yc): along to xc, down
    through the down-sampling box, to the child's top edge top_c."""
    yd = 0.5 * (y + yc) - 1.5
    side = FILT / 2 if xc < xf else -FILT / 2
    if abs(xc - xf) > 1e-6:
        L.append(rf"\draw[fs thin] {pt(xf - side, y)} -- {pt(xc, y)} -- {pt(xc, yd + 7)};")
        L.append(rf"\draw[fs thin] {pt(xc, yd - 7)} -- {pt(xc, top_c)};")
    else:
        L.append(rf"\draw[fs thin] {pt(xf, y - FILT / 2)} -- {pt(xc, yd + 7)};")
        L.append(rf"\draw[fs thin] {pt(xc, yd - 7)} -- {pt(xc, top_c)};")
    L.append(rf"\node[fs box, rounded corners=0.8pt, inner sep=0pt, minimum width=19pt, minimum height=14pt] at {pt(xc, yd)} {{$\downarrow\!2$}};")


def node(L, x, y, tex, minw=0.0):
    w, h, d = size(tex)
    bw = max(w + 5.0, minw)
    bh = 16.0
    L.append(rf"\node[fs box, rounded corners=0.8pt, inner sep=0pt, minimum width={bw:.2f}pt, minimum height={bh}pt] at {pt(x, y)} {{{tex}}};")
    return bw / 2, y + bh / 2


def tree():
    L = []
    hs, _ = node(L, XS, ROW["s"], "signal", 60.0)
    sl, sh = filters(L, XS, ROW["s"], "signal", hs)
    leaves = []
    for a, xf in (("A", sl), ("D", sh)):
        x1 = XS + SPLIT[a]
        h1, t1 = node(L, x1, ROW["1"], f"${a}_1$", 24.0)
        branch(L, xf, ROW["s"], x1, ROW["1"], t1)
        l1, r1 = filters(L, x1, ROW["1"], a, h1)
        for b, xf1, sgn in (("A", l1, -1), ("D", r1, 1)):
            x2 = x1 + sgn * SUB
            h2, t2 = node(L, x2, ROW["2"], f"${a}{b}_2$", 24.0)
            branch(L, xf1, ROW["1"], x2, ROW["2"], t2)
            l2, r2 = filters(L, x2, ROW["2"], a + b, h2)
            for c, xf2 in (("A", l2), ("D", r2)):
                h3, t3 = node(L, xf2, ROW["3"], f"${a}{b}{c}_3$")
                branch(L, xf2, ROW["2"], xf2, ROW["3"], t3)
                leaves.append((xf2, h3))
    for x, h3 in leaves:
        L.append(rf"\node at {pt(x, ROW['3'] - 20)} {{$\vdots$}};")
    # the leaves keep apart, and no level-2 group runs into the next
    xs = [x for x, _ in leaves]
    hw = [h for _, h in leaves]
    gaps = [xs[i + 1] - hw[i + 1] - xs[i] - hw[i] for i in range(len(xs) - 1)]
    assert min(gaps) >= 5.0, f"leaves too close: {min(gaps):.1f} pt"
    for k, y in (("1", ROW["1"]), ("2", ROW["2"]), ("3", ROW["3"])):
        L.append(rf"\node[align=center] at {pt(xs[0] - hw[0] - 26, y)} {{Level\\{k}}};")
    L.append(rf"\node[fs box, rounded corners=0.8pt, inner sep=2.5pt] at {pt(XS, ROW['3'] - 40)} "
             r"{$\downarrow$ 2:Down-sampling};")
    L.append(rf"\FigPanel{{({xs[0] - hw[0] - 52:.2f},{ROW['s'] + 4:.2f})}}{{a}}")
    return L


# ------------------------------------------------------------------ the tilings
TW, TH = 130.0, 84.0                        # a tiling's frame, pt
Y0 = -298.0                                 # the frames' lower edge
PACKETS = ["AAA_3", "AAD_3", "ADA_3", "ADD_3", "DAA_3", "DAD_3", "DDA_3", "DDD_3"]


def frame(L, x0, letter):
    """The frame of a tiling at (x0, Y0): its time and frequency axes and labels."""
    L.append(rf"\draw[fs thin] {pt(x0, Y0)} rectangle {pt(x0 + TW, Y0 + TH)};")
    g = 4.0                                 # the axes stand off the frame
    L.append(rf"\draw[fs axis] {pt(x0 - g, Y0 - g)} -- {pt(x0 + TW + 10, Y0 - g)};")
    L.append(rf"\draw[fs axis] {pt(x0 - g, Y0 - g)} -- {pt(x0 - g, Y0 + TH + 10)};")
    L.append(rf"\node[fs axlabel, anchor=north east] at {pt(x0 + TW + 10, Y0 - g - 3)} {{Time}};")
    L.append(rf"\node[fs axlabel, rotate=90, anchor=south] at {pt(x0 - g - 3.5, Y0 + TH / 2)} {{Frequency}};")
    L.append(rf"\FigPanel{{({x0 - 28:.2f},{Y0 + TH + 6:.2f})}}{{{letter}}}")


def tiling_b(x0):
    L = []
    frame(L, x0, "b")
    rh = TH / len(PACKETS)
    for k in range(1, 4):
        L.append(rf"\draw[fs thin] {pt(x0 + k * TW / 4, Y0)} -- {pt(x0 + k * TW / 4, Y0 + TH)};")
    for k, name in enumerate(PACKETS):
        yc = Y0 + TH - (k + 0.5) * rh
        if k:
            L.append(rf"\draw[fs thin] {pt(x0, Y0 + TH - k * rh)} -- {pt(x0 + TW, Y0 + TH - k * rh)};")
        L.append(rf"\node[anchor=west] at {pt(x0 + TW + 4.5, yc)} {{${name}$}};")
    return L


def tiling_c(x0):
    L = []
    frame(L, x0, "c")
    unit = TH / 7.0                         # bands 4 : 2 : 1
    bands = (("D_1", 4, 16), ("AD_2", 2, 8), ("AAD_3", 1, 4))
    top = Y0 + TH
    for k, (name, hgt, cells) in enumerate(bands):
        bot = top - hgt * unit
        if k < len(bands) - 1:
            L.append(rf"\draw[fs thin] {pt(x0, bot)} -- {pt(x0 + TW, bot)};")
        for j in range(1, cells):
            L.append(rf"\draw[fs thin] {pt(x0 + j * TW / cells, bot)} -- {pt(x0 + j * TW / cells, top)};")
        L.append(rf"\node[anchor=west] at {pt(x0 + TW + 4.5, 0.5 * (top + bot))} {{${name}$}};")
        top = bot
    # every cell the same area
    areas = {hgt * unit * TW / cells for _, hgt, cells in bands}
    assert max(areas) - min(areas) < 1e-9
    return L


def body():
    L = [r"\begin{tikzpicture}[fs, x=1pt, y=1pt]"]
    L += tree()
    L += tiling_b(34.0) + tiling_c(274.0)
    L.append(r"\end{tikzpicture}")
    return "\n".join(L)


if __name__ == "__main__":
    print(body())
