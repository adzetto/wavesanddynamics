r"""digitize.py -- read the curves of a picture of his plots back into numbers.

    python tools/blogfig/digitize.py <name> <picture> [...]

His data plots survive only as pictures (the posts' figures, as the live site
serves them: post/<slug>/<k>-<stem>.webp). A figure that redraws one reads
its curves from a JSON file in data/, which this script writes from the
picture, once; the picture is not kept in the repository (content/blog/ is
not), so the JSON is what the figure is built from.

A panel is read inside its frame, whose edges are found as the long dark
rows and columns of the picture, and mapped to data by the frame's limits.
Its tick marks and its legend box are masked. What is left is ink, which is
split by connected components: a solid line is one long component, a dotted
line (MATLAB's ':') a scatter of specks, each a point of the curve. A solid
line is kept as a polyline, per pixel column (both ends of a steep stretch,
in the order that keeps it continuous); a dotted one as its specks' centres,
which the figure draws as dots again.
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def gray(path):
    return np.asarray(Image.open(path).convert("L")).astype(float)


def frame(g, rows, cols, thr=200):
    """The frame's inner edges in (rows) y0..y1 and (cols) x0..x1 of the picture:
    the long dark lines found in those bands, as (x0, y0, x1, y1), pixel centres."""
    d = g < thr
    ys = [y for y in range(*rows) if d[y, cols[0]:cols[1]].sum() > 0.8 * (cols[1] - cols[0])]
    xs = [x for x in range(*cols) if d[rows[0]:rows[1], x].sum() > 0.6 * (rows[1] - rows[0])]
    # the outermost lines (a curve can draw a long dark row too: a flat line at zero)
    top = [y for y in ys if y <= min(ys) + 2]
    bot = [y for y in ys if y >= max(ys) - 2]
    lef = [x for x in xs if x <= min(xs) + 2]
    rig = [x for x in xs if x >= max(xs) - 2]
    return (float(np.mean(lef)), float(np.mean(top)), float(np.mean(rig)), float(np.mean(bot)))


def panel(g, box, xlim, ylim, xticks=(), yticks=(), legend=None, thr=170, tick=14, solid_min=60,
          speck_max=14, pad=2.5):
    """The curves inside the frame box = (x0, y0, x1, y1) (pixels), whose edges
    are xlim and ylim in data. legend = (x0, y0, x1, y1) in pixels, masked.
    Returns {"solid": [[x, y], ...] per solid line, "dots": [[x, y], ...]} in data."""
    x0, y0, x1, y1 = box
    H, W = g.shape
    ink = g < thr
    m = np.zeros_like(ink)
    m[int(np.ceil(y0 + pad)):int(np.floor(y1 - pad)) + 1, int(np.ceil(x0 + pad)):int(np.floor(x1 - pad)) + 1] = True
    ink &= m
    sx = (x1 - x0) / (xlim[1] - xlim[0])
    sy = (y1 - y0) / (ylim[1] - ylim[0])
    for t in xticks:                        # tick marks, inside the frame at top and bottom
        px = x0 + (t - xlim[0]) * sx
        c = slice(int(px - 3), int(px + 4))
        ink[int(y0):int(y0 + tick), c] = False
        ink[int(y1 - tick):int(y1) + 1, c] = False
    for v in yticks:
        py = y1 - (v - ylim[0]) * sy
        r = slice(int(py - 3), int(py + 4))
        ink[r, int(x0):int(x0 + tick)] = False
        ink[r, int(x1 - tick):int(x1) + 1] = False
    if legend:
        lx0, ly0, lx1, ly1 = legend
        ink[int(ly0):int(ly1) + 2, int(lx0) - 1:int(lx1) + 2] = False
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    sizes = ndimage.sum(ink, lab, range(1, n + 1))
    to_x = lambda px: xlim[0] + (px - x0) / sx
    to_y = lambda py: ylim[0] + (y1 - py) / sy
    solids = []
    for i in np.nonzero(sizes >= solid_min)[0] + 1:
        mask = lab == i
        cols = np.nonzero(mask.any(axis=0))[0]
        if cols.max() - cols.min() < 0.3 * (x1 - x0):     # not a line across the plot: specks that touch
            continue
        pts, last = [], None
        for c in cols:
            ys = np.nonzero(mask[:, c])[0]
            # the column's runs of ink; a dot touching the line is a run of its own, or a
            # pixel or two on the end of the line's: keep the run the line came in on
            runs, start = [], ys[0]
            for u, v in zip(ys[:-1], ys[1:]):
                if v != u + 1:
                    runs.append((start, u))
                    start = v
            runs.append((start, ys[-1]))
            ref = last if last is not None else np.median(ys)
            a, b = min(runs, key=lambda r_: 0 if r_[0] <= ref <= r_[1] else min(abs(r_[0] - ref), abs(r_[1] - ref)))
            if b - a <= 3:
                seq = [(a + b) / 2]
            else:                           # a steep stretch: both ends, the nearer one first
                seq = [a, b] if last is None or abs(a - last) <= abs(b - last) else [b, a]
            for y in seq:
                pts.append([round(float(to_x(c)), 7), round(float(to_y(y)), 7)])
            last = seq[-1]
        solids.append(pts)
    dots = []
    lines = {int(i) for i in np.nonzero(sizes >= solid_min)[0] + 1
             if np.ptp(np.nonzero((lab == i).any(axis=0))[0]) >= 0.3 * (x1 - x0)}
    for i in [i for i in range(1, n + 1) if i not in lines]:
        if sizes[i - 1] >= speck_max:       # specks that touch: split at their thin necks
            sub, k = ndimage.label(ndimage.binary_erosion(lab == i), structure=np.ones((3, 3)))
            for j in range(1, k + 1):
                cy, cx = ndimage.center_of_mass(sub == j)
                dots.append([round(float(to_x(cx)), 7), round(float(to_y(cy)), 7)])
            continue
        cy, cx = ndimage.center_of_mass(lab == i)
        dots.append([round(float(to_x(cx)), 7), round(float(to_y(cy)), 7)])
    dots.sort()
    return {"solid": solids, "dots": dots, "frame_px": [round(float(v), 2) for v in box],
            "legend_px": [int(v) for v in legend] if legend else None}


def legend_box(g, box, thr=120, frac=0.75, upto=1.0):
    """A legend's rectangle inside the frame box, between the fractions frac and
    upto of its width: its sides are the columns with the longest dark runs
    there, its top and bottom the rows dark from side to side between them."""
    x0, y0, x1, y1 = box
    d = g < thr
    xa, xb, ya, yb = max(int(x0 + frac * (x1 - x0)), int(x0) + 4), int(x0 + upto * (x1 - x0)) - 3, int(y0) + 3, int(y1) - 2

    def longest(col):
        best = run = 0
        for v in col:
            run = run + 1 if v else 0
            best = max(best, run)
        return best
    runs = {x: longest(d[ya:yb, x]) for x in range(xa, xb)}
    tall = [x for x, r in runs.items() if r >= 25]
    lx0, lx1 = min(tall), max(tall)
    col, best, run, s0 = d[ya:yb, lx0], (0, 0, 0), 0, 0   # the left side's longest run bounds the box
    for i, v in enumerate(col):
        if v:
            s0 = i if run == 0 else s0
            run += 1
            best = max(best, (run, s0, i))
        else:
            run = 0
    _, r0, r1 = best
    ys = [y for y in range(ya + r0, ya + r1 + 1) if d[y, lx0 + 2:lx1 - 1].mean() > 0.9]
    top = ys[0]
    while top + 1 in ys:                    # a curve drawn along the box's top touches it: the
        top += 1                            # box's edge is the lowest row of that dark band
    return (lx0, top, lx1, max(ys))


# ------------------------------------------------------------------ the pictures read
def som_fig2(path):
    """impulsive-noise...: 03-fig2: (a) s and its moving median, (b) the fourth
    difference of s and its moving median; both 0.189 to 0.1915 s, -5e-3 to 5e-3."""
    g = gray(path)
    out = {"source": "post/impulsive-noise-detection-with-semi-organizing-map-neural-networks/03-fig2.webp"}
    xt = (0.189, 0.1895, 0.19, 0.1905, 0.191, 0.1915)
    for key, rows, leg in (("a", (35, 215), None), ("b", (286, 466), None)):
        box = frame(g, rows, (150, 1120))
        out[key] = {"box": box}
    # the legend boxes: the dark rectangle in each panel's right quarter
    for key in ("a", "b"):
        out[key] = panel(g, out[key]["box"], (0.189, 0.1915), (-5e-3, 5e-3), xt, (-5e-3, 0, 5e-3),
                         legend_box(g, out[key]["box"]))
    return out


def som_fig3(path):
    """impulsive-noise...: 04-fig3: (a) u^s, with his zoom box; (b) its middle;
    (c) the SOM's neurons; (d) the sorted mean distances MD, two fitted lines
    and the knee point; (e) the points kept."""
    g = gray(path)
    out = {"source": "post/impulsive-noise-detection-with-semi-organizing-map-neural-networks/04-fig3.webp"}
    B = {"a": frame(g, (60, 306), (165, 390)), "b": frame(g, (60, 306), (505, 752)),
         "c": frame(g, (66, 307), (864, 1108)), "d": frame(g, (385, 633), (338, 570)),
         "e": frame(g, (392, 633), (707, 950))}
    m3 = (-3e-3, 3e-3)
    t3 = (-3e-3, -2e-3, -1e-3, 0, 1e-3, 2e-3, 3e-3)
    (zx0, zy0, zx1, zy1), fits = zoom_box(g, B["a"], B["b"])
    edges = [(zx0 - 3, zy0 - 3, zx1 + 3, zy0 + 3), (zx0 - 3, zy1 - 3, zx1 + 3, zy1 + 3),
             (zx0 - 3, zy0 - 3, zx0 + 3, zy1 + 3), (zx1 - 3, zy0 - 3, zx1 + 3, zy1 + 3)]
    for a, b in fits:                       # the dashed lines, inside (a) from the box to the frame
        for c in range(int(zx1), int(B["a"][2]) + 1):
            yc = a * c + b
            edges.append((c, yc - 2.5, c, yc + 2.5))
    t4 = (-0.04, -0.02, 0, 0.02, 0.04)
    out["a"] = specks_and_blobs(g, B["a"], (-0.04, 0.04), (-0.04, 0.04), t4, t4, edges)
    x0, y0, x1, y1 = B["a"]
    sx, sy = (x1 - x0) / 0.08, (y1 - y0) / 0.08
    out["a"]["zoom"] = [-0.04 + (zx0 - x0) / sx, -0.04 + (y1 - zy1) / sy,
                        -0.04 + (zx1 - x0) / sx, -0.04 + (y1 - zy0) / sy]
    for k in "bce":
        out[k] = specks_and_blobs(g, B[k], m3, m3, t3, t3)
    out["d"] = knee_plot(g, B["d"])
    return out


def knee_plot(g, box, thr=150):
    """(d): the curve of the sorted MD, his two lines, the knee's ring and label,
    his legend; 0 to 4750 neurons across, 0 to 4e-4 up."""
    x0, y0, x1, y1 = box
    xl, yl = (0.0, 4750.0), (0.0, 4e-4)
    sx, sy = (x1 - x0) / (xl[1] - xl[0]), (y1 - y0) / (yl[1] - yl[0])
    to_x = lambda px: xl[0] + (px - x0) / sx
    to_y = lambda py: yl[0] + (y1 - py) / sy
    leg = legend_box(g, box, thr=200, frac=0.0, upto=0.75)
    ink = g < thr
    m = np.zeros_like(ink)
    m[int(y0) + 3:int(y1) - 2, int(x0) + 3:int(x1) - 2] = True
    ink &= m
    for t in (950, 1900, 2850, 3800):       # tick marks, inside
        px = x0 + t * sx
        ink[int(y1) - 9:int(y1) + 1, int(px - 2):int(px + 3)] = False
        ink[int(y0):int(y0) + 9, int(px - 2):int(px + 3)] = False
    for v in (1e-4, 2e-4, 3e-4):
        py = y1 - v * sy
        ink[int(py - 2):int(py + 3), int(x0):int(x0) + 9] = False
        ink[int(py - 2):int(py + 3), int(x1) - 9:int(x1) + 1] = False
    ink[leg[1] - 1:leg[3] + 2, leg[0] - 1:leg[2] + 2] = False
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    comps = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        mk = lab[sl] == i
        cy, cx = ndimage.center_of_mass(lab == i)
        comps.append({"i": i, "a": int(mk.sum()), "w": sl[1].stop - sl[1].start, "h": sl[0].stop - sl[0].start,
                      "cx": cx, "cy": cy, "sl": sl})
    big = max(comps, key=lambda c: c["a"])
    # the knee's ring: searched over the lower right of the plot, where the curve bends
    kx, ky, kr = ring(g, box, (x0 + 0.82 * (x1 - x0), y0 + 0.86 * (y1 - y0)), reach=30)
    # the label "Knee point": letter-sized ink up and to the left of the ring
    glyphs = [c for c in comps if 20 <= c["a"] <= 70 and c["h"] >= 8 and c["w"] <= 10
              and kx - 70 < c["cx"] < kx + 5 and ky - 70 < c["cy"] < ky - 5]
    gx0 = min(c["sl"][1].start for c in glyphs); gx1 = max(c["sl"][1].stop for c in glyphs)
    gy0 = min(c["sl"][0].start for c in glyphs); gy1 = max(c["sl"][0].stop for c in glyphs)
    yy, xx = np.ogrid[:g.shape[0], :g.shape[1]]
    ringmask = np.abs(np.hypot(xx - kx, yy - ky) - kr) <= 1.6
    # his lines: Line 2 a dotted line of 3 x 3 squares, steep, right of the knee; Line 1 dashes
    # and squares along the bottom, left of it
    sq = [c for c in comps if 3 <= c["w"] <= 4 and 3 <= c["h"] <= 4 and c["a"] >= 7]
    l2 = np.array([(c["cx"], c["cy"]) for c in sq if c["cx"] >= kx - 6 and c["cy"] < y1 - 4])
    l1 = [c for c in comps if c["cx"] < kx - 6 and c["cy"] > ky and c["a"] >= 7 and c is not big
          and c["h"] <= 4 and (c["w"] >= 2.5 * c["h"] or c["w"] >= 6)]      # his dashes
    b2, a2 = np.polyfit(l2[:, 1], l2[:, 0], 1)          # x = a2 + b2 y, steep
    l1p = np.array([(c["cx"], c["cy"]) for c in l1])
    d1, c1 = np.polyfit(l1p[:, 0], l1p[:, 1], 1)        # y = c1 + d1 x
    # as his lines run: Line 1 from the axis to Line 2, Line 2 from the axis to the plot's edge
    l1x0 = (y1 - c1) / d1
    l1x1 = (a2 + b2 * c1) / (1 - b2 * d1)               # where x = a2 + b2 (c1 + d1 x)
    l2y1 = y1
    l2y0 = (x1 - a2) / b2
    # the curve: the big component, less the ring and his lines' ink
    cv = (lab == big["i"]) & ~ringmask
    py_, px_ = np.nonzero(cv)
    near1 = np.abs(py_ - (c1 + d1 * px_)) <= 2.2
    near2 = np.abs(px_ - (a2 + b2 * py_)) <= 2.2
    keep = ~(near1 & (px_ >= l1x0) & (px_ <= l1x1)) & ~(near2 & (py_ >= l2y0))
    cv2 = np.zeros_like(cv)
    cv2[py_[keep], px_[keep]] = True
    pts = []
    for c in range(int(x0) + 3, int(x1) - 2):          # across where it is flat, up where it is steep
        ys = np.nonzero(cv2[:, c])[0]
        if len(ys) and ys.max() - ys.min() <= 4:
            pts.append((c, ys.mean()))
    for r in range(int(y0) + 3, int(y1) - 2):
        xs = np.nonzero(cv2[r, :])[0]
        if len(xs) and xs.max() - xs.min() <= 4:
            pts.append((xs.mean(), r))
    pts = sorted(set((round(a, 2), round(b, 2)) for a, b in pts), key=lambda q: (q[0] - q[1]))
    # Where the curve runs into his lines or along the axis it cannot be told from them: it is
    # carried through those stretches by a monotone spline through what can be read, from its
    # start at the origin to its top at the plot's edge, where Line 2 ends on it.
    from scipy.interpolate import PchipInterpolator
    P = np.array([(to_x(a), to_y(b)) for a, b in pts])
    P = P[P[:, 0] >= 0.4 * xl[1]]
    # up the steep part his dots and Line 2's squares run together: the middle of that band, row by row
    top_row = min(b for a, b in pts)
    band = []
    for r in range(int(np.ceil(l2y0)) + 1, int(top_row)):
        c = a2 + b2 * r
        xs = np.nonzero(ink[r, int(c - 5):int(c + 6)])[0]
        if len(xs):
            band.append((to_x(int(c - 5) + xs.mean()), to_y(r)))
    if band:
        B_ = np.array(band)
        k_ = 7                              # the band's middle wavers by a pixel: a running mean over 7 rows
        if len(B_) > k_:
            B_[:, 0] = np.convolve(np.pad(B_[:, 0], k_ // 2, mode="edge"), np.ones(k_) / k_, mode="valid")
        P = np.vstack([P, B_])
    P = np.vstack([[0.0, 0.0], P])
    sp = P[:, 0] / xl[1] + P[:, 1] / yl[1]              # both rise along the curve
    o = np.argsort(sp)
    P, sp = P[o], sp[o]
    keep = np.r_[True, np.diff(sp) > 1e-4]
    P, sp = P[keep], sp[keep]
    fx_, fy_ = PchipInterpolator(sp, P[:, 0]), PchipInterpolator(sp, P[:, 1])
    ss = np.linspace(sp[0], sp[-1], 240)
    curve = [[round(float(a), 3), round(float(b), 9)] for a, b in zip(fx_(ss), fy_(ss))]
    # the last neurons, above the curve's top at the right edge: specks
    tail = [c for c in comps if c["a"] <= 6 and c["cx"] > x1 - 0.08 * (x1 - x0)]
    return {"curve": curve,
            "tail": sorted([[round(float(to_x(c["cx"])), 3), round(float(to_y(c["cy"])), 9)] for c in tail]),
            "line1": [[float(to_x(l1x0)), float(to_y(c1 + d1 * l1x0))], [float(to_x(l1x1)), float(to_y(c1 + d1 * l1x1))]],
            "line2": [[float(to_x(a2 + b2 * l2y1)), float(to_y(l2y1))], [float(to_x(a2 + b2 * l2y0)), float(to_y(l2y0))]],
            "knee": [float(to_x(kx)), float(to_y(ky)), float(kr / sx)],
            "label": [float(to_x((gx0 + gx1) / 2)), float(to_y((gy0 + gy1) / 2))],
            "legend": [float(to_x(leg[0])), float(to_y(leg[3])), float(to_x(leg[2])), float(to_y(leg[1]))],
            "frame_px": [float(v) for v in box]}






def specks_and_blobs(g, box, xlim, ylim, xticks=(), yticks=(), masks=(), thr=150, tick=9, speck_max=12,
                     pad=2.5):
    """A scatter plot: its isolated specks as points, and where his points run
    together into solid ink, that ink as filled polygons (outer edges and
    holes), all in data. masks: (x0, y0, x1, y1) pixel boxes left out."""
    import contourpy
    x0, y0, x1, y1 = box
    ink = g < thr
    m = np.zeros_like(ink)
    m[int(np.ceil(y0 + pad)):int(np.floor(y1 - pad)) + 1, int(np.ceil(x0 + pad)):int(np.floor(x1 - pad)) + 1] = True
    ink &= m
    sx = (x1 - x0) / (xlim[1] - xlim[0])
    sy = (y1 - y0) / (ylim[1] - ylim[0])
    for t in xticks:
        px = x0 + (t - xlim[0]) * sx
        c = slice(int(px - 2), int(px + 3))
        ink[int(y0):int(y0 + tick), c] = False
        ink[int(y1 - tick):int(y1) + 1, c] = False
    for v in yticks:
        py = y1 - (v - ylim[0]) * sy
        r = slice(int(py - 2), int(py + 3))
        ink[r, int(x0):int(x0 + tick)] = False
        ink[r, int(x1 - tick):int(x1) + 1] = False
    for a, b, c, d in masks:
        ink[int(b):int(d) + 1, int(a):int(c) + 1] = False
    to_x = lambda px: xlim[0] + (px - x0) / sx
    to_y = lambda py: ylim[0] + (y1 - py) / sy
    lab, n = ndimage.label(ink, structure=np.ones((3, 3)))
    sizes = ndimage.sum(ink, lab, range(1, n + 1))
    dots = []
    for i in np.nonzero(sizes <= speck_max)[0] + 1:
        cy, cx = ndimage.center_of_mass(lab == i)
        dots.append([round(float(to_x(cx)), 8), round(float(to_y(cy)), 8)])
    big = np.isin(lab, np.nonzero(sizes > speck_max)[0] + 1).astype(float)
    polys = []
    if big.any():
        # the edge of the solid ink, half way between an inked pixel and a clear one
        gen = contourpy.contour_generator(z=np.pad(big, 1), line_type="Separate")
        for line in gen.lines(0.5):
            if len(line) < 4:
                continue
            px, py = line[:, 0] - 1, line[:, 1] - 1
            polys.append([[round(float(to_x(a)), 8), round(float(to_y(b)), 8)] for a, b in zip(px, py)])
    dots.sort()
    return {"dots": dots, "polys": polys, "frame_px": [float(v) for v in box]}


def zoom_box(g, box, nxt, thr=150):
    """His zoom box in panel (a), and the two dashed lines from its right
    corners to the left corners of the next panel's frame nxt. The box is a
    rectangle of square dots, whose top row and left column stand clear of
    the cloud; its right side and bottom are in the cloud, so they are found
    where the dashed lines, fitted in the clear gap between the panels, start.
    Returns the box (x0, y0, x1, y1) and each line as (slope, intercept), pixels."""
    x0, y0, x1, y1 = box
    ink = g < thr
    sub = ink[int(y0) + 3:int(y1) - 2, int(x0) + 3:int(x1) - 2]
    lab, n = ndimage.label(sub, structure=np.ones((3, 3)))
    sq = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if 3 <= h <= 6 and 3 <= w <= 6 and 7 <= (lab[sl] == i).sum() <= 20:
            cy, cx = ndimage.center_of_mass(lab == i)
            sq.append((cx + int(x0) + 3, cy + int(y0) + 3))
    sq = np.array(sq)

    def line_of(vals, need=3):
        vals = np.sort(vals)
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if v - cur[-1] <= 1.5:
                cur.append(v)
            else:
                groups.append(cur)
                cur = [v]
        groups.append(cur)
        return [float(np.mean(gp)) for gp in groups if len(gp) >= need]
    top, left = min(line_of(sq[:, 1])), min(line_of(sq[:, 0]))
    # the dashed lines in the gap: each column's ink, upper and lower
    gx0, gx1 = int(x1) + 6, int(x1) + 6 + int(0.35 * (nxt[0] - x1))   # clear of the next panel's labels
    up, lo = [], []
    mid = 0.5 * (y0 + y1)
    for c in range(gx0, gx1):
        ys = np.nonzero(ink[int(y0) - 10:int(y1) + 10, c])[0] + int(y0) - 10
        up += [(c, y) for y in ys if y < mid]
        lo += [(c, y) for y in ys if y >= mid]
    fits = []
    for pts_ in (up, lo):
        P = np.array(pts_, float)
        fits.append(tuple(np.polyfit(P[:, 0], P[:, 1], 1)))
    # where each starts: going left from the frame, the last dash on it
    starts = []
    for k, (a, b) in enumerate(fits):
        xs = [c for c in range(int(left) + 4, int(x1) - 2)
              if ink[int(round(a * c + b)) - 1:int(round(a * c + b)) + 2, c].any()]
        on = np.array(xs)
        # the dashes run unbroken but for gaps of a few pixels: the run that reaches the frame
        run = [on[-1]]
        for v in on[::-1][1:]:
            if run[-1] - v <= 6:
                run.append(v)
            else:
                break
        starts.append(min(run))
    right = float(np.mean(starts))
    bottom = float(fits[1][0] * right + fits[1][1])
    return (left, top, right, bottom), fits


def ring(g, box, near, thr=150, rmin=4, rmax=10, reach=25):
    """A circle drawn round a point (his knee point): the ring of ink within
    `reach` of `near` (pixels). Returns its centre and radius, pixels."""
    x0, y0, x1, y1 = box
    ink = g < thr
    best = None
    for yy in range(int(near[1]) - reach, int(near[1]) + reach + 1):
        for xx in range(int(near[0]) - reach, int(near[0]) + reach + 1):
            if not ink[yy - 1:yy + 2, xx - 1:xx + 2].any():
                continue                    # it rings a point of the curve, not a letter's hole
            for r in range(rmin, rmax + 1):
                t = np.linspace(0, 2 * np.pi, 48, endpoint=False)
                px = np.clip(np.round(xx + r * np.cos(t)).astype(int), 0, g.shape[1] - 1)
                py = np.clip(np.round(yy + r * np.sin(t)).astype(int), 0, g.shape[0] - 1)
                on = ink[py, px].mean()

                def on_ring(rr):
                    qx = np.clip(np.round(xx + rr * np.cos(t)).astype(int), 0, g.shape[1] - 1)
                    qy = np.clip(np.round(yy + rr * np.sin(t)).astype(int), 0, g.shape[0] - 1)
                    return ink[qy, qx].mean()
                score = on - 0.5 * (on_ring(r - 2) + on_ring(r + 2))   # a curve through it crosses all three
                if best is None or score > best[0]:
                    best = (score, xx, yy, r)
    return best[1:]


def ldv_speckle(path):
    """laser-doppler...: 04-fig-speckle: three line charts against distance, 0 to
    6000 mm, with no values up the side: their curves in units of the charts'
    gridlines (0 the axis, 5 the top line), the thick stroke and the circle he
    drew over the third, his arrow and where his note stands."""
    im = np.asarray(Image.open(path).convert("RGB")).astype(int)
    R, G, B = im[..., 0], im[..., 1], im[..., 2]
    gr = (np.abs(R - G) < 8) & (np.abs(G - B) < 8) & (R > 190) & (R < 235)
    blue = (B > 150) & (R < 140) & (B - R > 60)
    red = (R > 150) & (G < 100) & (B < 100)
    dark = (R < 110) & (G < 110) & (B < 110)
    rows = [y for y in range(im.shape[0]) if gr[y, :600].sum() > 250]
    groups, cur = [], [rows[0]]
    for y in rows[1:]:
        if y - cur[-1] <= 1:
            cur.append(y)
        else:
            groups.append(np.mean(cur))
            cur = [y]
    groups.append(np.mean(cur))
    out = {"source": "post/laser-doppler-vibrometer-how-it-works-advantages-and-disadvantages-speckle-noise/04-fig-speckle.webp"}
    for k, chart in enumerate((groups[0:6], groups[6:12], groups[12:18])):
        top, bot = chart[0], chart[-1]
        band = slice(int(top) - 2, int(bot) + 3)
        cs = [x for x in range(600) if gr[band, x].sum() > 0.6 * (bot - top)]
        cg, cur = [], [cs[0]]
        for x in cs[1:]:
            if x - cur[-1] <= 1:
                cur.append(x)
            else:
                cg.append(np.mean(cur))
                cur = [x]
        cg.append(np.mean(cur))
        c0, c6 = cg[0], cg[-1]
        tx = lambda px: (px - c0) / (c6 - c0) * 6000.0
        ty = lambda py: (bot - py) / (bot - top) * 5.0
        area = np.zeros_like(blue)
        area[int(top) - 6:int(bot) + 2, int(c0) - 2:int(c6) + 3] = True
        bl = blue & area
        # the thick stroke he drew (third chart): what is left of the blue after an opening
        thick = ndimage.binary_opening(bl, structure=np.ones((3, 3)))
        lab_, n_ = ndimage.label(thick)
        if n_:                              # only a stroke of some length, not a corner of the line
            sz = ndimage.sum(thick, lab_, range(1, n_ + 1))
            thick = np.isin(lab_, np.nonzero(sz > 30)[0] + 1)
        rec = {"grid_px": [float(v) for v in chart], "cols_px": [float(c0), float(c6)]}
        if thick.sum() > 30:
            yy, xx = np.nonzero(thick)
            P = np.column_stack([xx, yy]).astype(float)
            m = P.mean(axis=0)
            u = np.linalg.svd(P - m)[2][0]
            t = (P - m) @ u
            a_, b_ = m + t.min() * u, m + t.max() * u
            rec["stroke"] = [[float(tx(a_[0])), float(ty(a_[1]))], [float(tx(b_[0])), float(ty(b_[1]))]]
            bl &= ~ndimage.binary_dilation(thick, iterations=2)
        # the curve: per column the middle of the run it came in on (on a straight stretch, steep
        # or not, the middle of each column's run is on the line), and at its two ends the run's
        # far end, where the line starts and stops
        pts, last, ends = [], None, []
        for c in range(int(c0) - 2, int(c6) + 3):
            ys = np.nonzero(bl[:, c])[0]
            if not len(ys):
                continue
            runs, st = [], ys[0]
            for u_, v_ in zip(ys[:-1], ys[1:]):
                if v_ != u_ + 1:
                    runs.append((st, u_))
                    st = v_
            runs.append((st, ys[-1]))
            ref = last if last is not None else np.median(ys)
            a, b = min(runs, key=lambda r_: 0 if r_[0] <= ref <= r_[1] else min(abs(r_[0] - ref), abs(r_[1] - ref)))
            pts.append((c, (a + b) / 2))
            ends.append((c, a, b))
            last = (a + b) / 2
        if len(pts) > 2:                    # the run's far ends at the first and last columns
            (c, a, b), nxt = ends[0], pts[1][1]
            pts[0] = (c, a if abs(a - nxt) > abs(b - nxt) else b)
            (c, a, b), prv = ends[-1], pts[-2][1]
            pts[-1] = (c, a if abs(a - prv) > abs(b - prv) else b)
        # his points: the corners of the polyline he plotted, kept within a pixel
        from geom import simplify as dp
        V = dp(np.array(pts, float), 1.0)
        rec["curve"] = [[round(float(tx(a)), 1), round(float(ty(b)), 4)] for a, b in V]
        if (red & area).sum() > 50:
            rd = red.copy()
            rd[:int(top) - 30] = False
            rd[int(bot) + 10:] = False
            lab, n = ndimage.label(rd, structure=np.ones((3, 3)))
            sizes = ndimage.sum(rd, lab, range(1, n + 1))
            ringc = int(np.argmax(sizes)) + 1
            sl = ndimage.find_objects(lab)[ringc - 1]
            cx, cy = (sl[1].start + sl[1].stop - 1) / 2, (sl[0].start + sl[0].stop - 1) / 2
            rx, ry = (sl[1].stop - sl[1].start) / 2, (sl[0].stop - sl[0].start) / 2
            rec["ring"] = [float(tx(cx)), float(ty(cy)), float(rx / (c6 - c0) * 6000.0), float(ry / (bot - top) * 5.0)]
            arrow = (lab > 0) & (lab != ringc)
            yy, xx = np.nonzero(arrow)
            if len(xx):
                # from nearest the ring's centre to farthest from it
                d = np.hypot(xx - cx, yy - cy)
                i0, i1 = int(np.argmin(d)), int(np.argmax(d))
                rec["arrow"] = [[float(tx(xx[i0])), float(ty(yy[i0]))], [float(tx(xx[i1])), float(ty(yy[i1]))]]
            # his note: the dark ink inside the plot, right of the ring and below the curve's top
            dk = dark & area
            dk[:, :int(cx + rx)] = False
            yy, xx = np.nonzero(dk)
            if len(xx):
                rec["note"] = [float(tx(xx.min())), float(ty(yy.max())), float(tx(xx.max())), float(ty(yy.min()))]
        out["abc"[k]] = rec
    return out


READERS = {"som_fig2": som_fig2, "som_fig3": som_fig3, "ldv_speckle": ldv_speckle}

if __name__ == "__main__":
    name, path = sys.argv[1], sys.argv[2]
    data = READERS[name](path)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    for k, v in data.items():
        if isinstance(v, dict):
            print(k, {kk: (len(vv) if isinstance(vv, list) and vv and isinstance(vv[0], list) else vv)
                      for kk, vv in v.items() if kk != "frame_px"})
