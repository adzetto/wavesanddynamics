"""Geometry the blog figures share: Python computes every point, TeX only
draws them (README.md).

A sketch is drawn in its own frame, fractions (u, v) of its axes, and placed
by frame(x0, y0, ax, ay), which turns fractions into pt."""
import numpy as np
from scipy.interpolate import CubicSpline


def pt(x, y):
    return f"({x:.2f},{y:.2f})"


def frame(x0, y0, ax, ay):
    """Fractions of an axis pair from (x0, y0), ax by ay pt long, to TikZ points,
    moved by d = (dx, dy) pt."""
    def q(u, v, d=(0.0, 0.0)):
        return pt(x0 + u * ax + d[0], y0 + v * ay + d[1])
    return q


def closed(c, n=720):
    """A smooth closed curve through the points c (in order), sampled n times
    along a periodic cubic spline in the arc length of c."""
    c = np.asarray(c, float)
    c = np.vstack([c, c[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    sx, sy = CubicSpline(s, c[:, 0], bc_type="periodic"), CubicSpline(s, c[:, 1], bc_type="periodic")
    u = np.linspace(0, s[-1], n + 1)[:-1]
    return np.column_stack([sx(u), sy(u)])


def smooth(c, n=200):
    """A smooth open curve through the points c, in their arc length."""
    c = np.asarray(c, float)
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
    sx, sy = CubicSpline(s, c[:, 0], bc_type="natural"), CubicSpline(s, c[:, 1], bc_type="natural")
    u = np.linspace(0, s[-1], n)
    return np.column_stack([sx(u), sy(u)])


def path(q, P, close=False):
    """A TikZ path through the fractions P of the frame q."""
    return " -- ".join(q(u, v) for u, v in P) + (" -- cycle" if close else "")


def front(B):
    """The Pareto Front of a closed curve B when both coordinates are minimized:
    the points no other point dominates, in order along B. Asserts they are
    one arc, and that it runs between the curve's leftmost and lowest points."""
    keep = []
    for i, (x, y) in enumerate(B):
        dom = (B[:, 0] <= x) & (B[:, 1] <= y) & ((B[:, 0] < x) | (B[:, 1] < y))
        if not dom.any():
            keep.append(i)
    F = np.array(keep)
    steps = np.diff(np.r_[F, F[0] + len(B)])
    assert (steps == 1).sum() == len(F) - 1, "the Pareto Front is not one arc"
    if steps.max() > 1:                     # start just past the gap
        start = F[(np.argmax(steps) + 1) % len(F)]
        F = np.r_[F[F >= start], F[F < start]]
    ends = B[F[[0, -1]]]
    assert np.isclose(ends[:, 0].min(), B[:, 0].min()) and np.isclose(ends[:, 1].min(), B[:, 1].min())
    return F if B[F[0], 0] <= B[F[-1], 0] else F[::-1]      # from the leftmost to the lowest


def hit(P, p0, d, closed_=True):
    """The first point where the ray p0 + a d (a > 0) crosses the polyline P: (a, point)."""
    p0, d = np.asarray(p0, float), np.asarray(d, float)
    Q = np.vstack([P, P[:1]]) if closed_ else np.asarray(P)
    best = None
    for a_, b_ in zip(Q[:-1], Q[1:]):
        e = b_ - a_
        M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        a, s = np.linalg.solve(M, a_ - p0)
        if a > 1e-9 and -1e-9 <= s <= 1 + 1e-9 and (best is None or a < best[0]):
            best = (a, p0 + a * d)
    assert best is not None, "the ray misses the curve"
    return best


def cross_x(P, x):
    """The points where the polyline P crosses the vertical line at x."""
    out = []
    for a_, b_ in zip(P[:-1], P[1:]):
        if (a_[0] - x) * (b_[0] - x) <= 0 and a_[0] != b_[0]:
            s = (x - a_[0]) / (b_[0] - a_[0])
            out.append(a_ + s * (b_ - a_))
    return np.array(out)


# ------------------------------------------------------------------ label boxes
# A label is placed by its box, which TeX measures: size(tex) returns (width,
# height, depth) in pt, from a cache that make.py fills (measure()) before it
# asks a figure for its picture a second time. Until then size() guesses.
import json
import os
import re
import subprocess
import tempfile

_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                      "build", "blogfig", "sizes.json")
try:
    with open(_CACHE, encoding="utf-8") as _f:
        SIZES = json.load(_f)
except (OSError, ValueError):
    SIZES = {}
MISSING = set()


def size(tex):
    """(width, height, depth) of `tex` set in the figures' 10 pt, in pt."""
    if tex in SIZES:
        return tuple(SIZES[tex])
    MISSING.add(tex)
    return (7.0 * max(1, len(tex) // 3), 7.0, 2.0)


def measure():
    """Measure every label size() was asked for and does not know. Returns
    True if there were any."""
    if not MISSING:
        return False
    todo = sorted(MISSING)
    here = os.path.dirname(os.path.abspath(__file__))
    lines = [r"\documentclass[10pt]{article}", r"\usepackage{tikz}", r"\input{figstyle}", r"\newsavebox\B",
             r"\begin{document}"]
    for i, t in enumerate(todo):
        lines.append(rf"\sbox\B{{{t}}}\typeout{{SIZE:{i}:\the\wd\B:\the\ht\B:\the\dp\B}}")
    lines.append(r"\end{document}")
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "m.tex"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        import shutil
        shutil.copy(os.path.join(here, "figstyle.tex"), d)
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "m.tex"], cwd=d,
                           capture_output=True, text=True, errors="ignore")
    got = {int(m[0]): tuple(float(v) for v in m[1:])
           for m in re.findall(r"SIZE:(\d+):([\d.]+)pt:([\d.]+)pt:([\d.]+)pt", r.stdout)}
    assert len(got) == len(todo), "a label did not measure:\n" + r.stdout[-2000:]
    for i, t in enumerate(todo):
        SIZES[t] = got[i]
    MISSING.clear()
    os.makedirs(os.path.dirname(_CACHE), exist_ok=True)
    with open(_CACHE, "w", encoding="utf-8") as f:
        json.dump(SIZES, f, indent=0, sort_keys=True)
    return True


def lines_size(lines, font="", skip=12.0):
    """The box of a centred stack of lines (TikZ align=center), each `skip` pt apart."""
    s = [size(f"{font} {t}" if font else t) for t in lines]
    return (max(w for w, h, d in s), s[0][1] + skip * (len(s) - 1) + s[-1][2] - 0.0, 0.0)


def beside(p, n, tex, gap=2.0, opts="", box=None):
    """A node holding `tex`, put on the side n (a vector) of the point p, pt: its
    box keeps `gap` pt from the line through p across n, its centre on that
    normal. box = (w, h, d) for a box size() cannot measure (a stack of lines)."""
    w, h, d = box or size(tex)
    n = np.asarray(n, float)
    n = n / np.hypot(*n)
    off = gap + 0.5 * (w * abs(n[0]) + (h + d) * abs(n[1]))
    c = np.asarray(p, float) + off * n
    return rf"\node[anchor=center{', ' + opts if opts else ''}] at {pt(*c)} {{{tex}}};"


def normal(p0, p1, side="left"):
    """The unit normal of the line p0 -> p1, on its left (or right) side."""
    d = np.asarray(p1, float) - np.asarray(p0, float)
    n = np.array([-d[1], d[0]]) / np.hypot(*d)
    return n if side == "left" else -n


# ------------------------------------------------------------------ crowded sketches
def _seg_box_dist(S, b):
    """Distances from segments S (n x 2 x 2) to the box b = (x0, y0, x1, y1), pt
    (0 where a segment crosses the box)."""
    x0, y0, x1, y1 = b
    P0, P1 = S[:, 0], S[:, 1]

    def pt_box(Q):
        dx = np.maximum(np.maximum(x0 - Q[:, 0], 0), Q[:, 0] - x1)
        dy = np.maximum(np.maximum(y0 - Q[:, 1], 0), Q[:, 1] - y1)
        return np.hypot(dx, dy)

    def pt_seg(C):
        d = P1 - P0
        L2 = np.maximum((d * d).sum(1), 1e-12)
        t = np.clip(((C - P0) * d).sum(1) / L2, 0, 1)
        return np.hypot(*(P0 + t[:, None] * d - C).T)

    best = np.minimum(pt_box(P0), pt_box(P1))
    for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        best = np.minimum(best, pt_seg(np.asarray(c, float)))
    # a segment crossing the box without an end inside it
    for (ax_, ay_), (bx_, by_) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)),
                                   ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        e = np.array([bx_ - ax_, by_ - ay_])
        d = P1 - P0
        den = d[:, 0] * e[1] - d[:, 1] * e[0]
        ok = np.abs(den) > 1e-12
        w = np.array([ax_, ay_]) - P0
        t = np.where(ok, (w[:, 0] * e[1] - w[:, 1] * e[0]) / np.where(ok, den, 1), -1)
        s = np.where(ok, (w[:, 0] * d[:, 1] - w[:, 1] * d[:, 0]) / np.where(ok, den, 1), -1)
        best = np.where(ok & (t >= 0) & (t <= 1) & (s >= 0) & (s <= 1), 0.0, best)
    return best


class Scene:
    """The strokes and labels of a sketch, in pt, so a label can be put where it
    keeps its distance from both: line() and tip() record what is drawn, place()
    finds a label's spot near where it is wanted."""

    def __init__(self):
        self.segs = np.zeros((0, 2, 2))
        self.half = np.zeros(0)
        self.boxes = []

    def line(self, pts, width=0.709):
        P = np.asarray(pts, float)
        if len(P) > 1:
            self.segs = np.vstack([self.segs, np.stack([P[:-1], P[1:]], axis=1)])
            self.half = np.r_[self.half, np.full(len(P) - 1, width / 2)]
        return P

    def tip(self, p0, p1, length=6.6, width=3.1):
        """An arrow tip at p1 on the line from p0 (fs tip med)."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        u = (p1 - p0) / np.hypot(*(p1 - p0))
        n = np.array([-u[1], u[0]])
        b = p1 - length * u
        self.line([p1, b + n * width / 2, b - n * width / 2, p1], 0.354)

    def circle(self, c, r, width=0.354):
        t = np.linspace(0, 2 * np.pi, 17)
        self.line(np.column_stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)]), width)

    def clearance(self, b):
        d = _seg_box_dist(self.segs, b) - self.half if len(self.segs) else np.array([1e9])
        m = d.min() if len(d) else 1e9
        for o in self.boxes:
            dx = max(o[0] - b[2], b[0] - o[2], 0)
            dy = max(o[1] - b[3], b[1] - o[3], 0)
            m = min(m, np.hypot(dx, dy))
        return m

    def place(self, tex, p, n, gap=2.0, opts="", reach=9.0, need=2.0, box=None, text=None):
        """The node for `tex` (its words `text` if not tex itself): first where
        beside(p, n, gap) puts it, else the nearest spot within `reach` pt that
        keeps `need` pt from every stroke and label; it raises if there is none."""
        w, h, d = box or size(tex)
        n = np.asarray(n, float)
        n = n / np.hypot(*n)
        off = gap + 0.5 * (w * abs(n[0]) + (h + d) * abs(n[1]))
        c0 = np.asarray(p, float) + off * n
        best = None
        r = np.arange(0, reach + 1e-9, 0.5)
        cand = [(0.0, 0.0)] + [(rr * np.cos(a), rr * np.sin(a)) for rr in r[1:]
                               for a in np.linspace(0, 2 * np.pi, max(8, int(rr * 6)), endpoint=False)]
        for dx, dy in cand:
            c = c0 + (dx, dy)
            b = (c[0] - w / 2, c[1] - (h + d) / 2, c[0] + w / 2, c[1] + (h + d) / 2)
            cl = self.clearance(b)
            if cl >= need:
                best = (c, b)
                break
        if best is None:
            raise AssertionError(f"no room for the label {text or tex} near {p}")
        self.boxes.append(best[1])
        return rf"\node[anchor=center{', ' + opts if opts else ''}] at {pt(*best[0])} {{{text or tex}}};"


def dots(points, r, color="fsLine", chunk=400):
    """Points as dots of radius r, pt: each a stroke of no length with a round
    cap, all in a few paths (in the SVG a dot is then a few bytes, not a circle
    of four curves)."""
    out = []
    P = [tuple(p) for p in points]
    for i in range(0, len(P), chunk):
        seg = " ".join(f"{pt(*q)} -- ++(0,0)" for q in P[i:i + chunk])
        out.append(rf"\draw[draw={color}, line width={2 * r:.3f}pt, line cap=round] {seg};")
    return out


def simplify(P, tol):
    """Douglas-Peucker: the outline with its points within tol of it dropped."""
    P = np.asarray(P, float)
    if len(P) < 4:
        return P
    keep = np.zeros(len(P), bool)
    keep[[0, -1]] = True
    stack = [(0, len(P) - 1)]
    while stack:
        i, j = stack.pop()
        a, b = P[i], P[j]
        d = b - a
        L = np.hypot(*d)
        seg = P[i + 1:j]
        if not len(seg):
            continue
        dist = (np.abs(d[0] * (seg[:, 1] - a[1]) - d[1] * (seg[:, 0] - a[0])) / L if L > 1e-12
                else np.hypot(*(seg - a).T))
        m = int(np.argmax(dist))
        if dist[m] > tol:
            keep[i + 1 + m] = True
            stack += [(i, i + 1 + m), (i + 1 + m, j)]
    return P[keep]
