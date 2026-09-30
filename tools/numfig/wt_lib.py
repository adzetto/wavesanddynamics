"""What the waves guide's cover and its fun table's ten small figures share.

The table ("Schematic figure" column) sets each picture at 202 x 81 pt in
Word (405 x 162 px), so each is drawn on a W = 1000, H = 400 canvas: the
same proportion, shown 164 to 260 px wide on the page, a fifth of the size
the numfig figures are drawn for. Strokes and type are scaled to survive
that (STROKE, below), and the frame's controls step out of the way until a
pointer or the keyboard asks for them (CELL_JS). The cover (image1, 1344 x
336 px) keeps its 4 : 1 and is drawn on W = 1000, H = 250.

Each generator wt_<name>.py computes its model, writes the check file
tools/numfig/wt_<name>.check.txt, the page content/anim/nf-wt-<name>.html
and its printed frame nf-wt-<name>.webp (common.build_html, common.still).
"""
import hashlib
import os
import pickle
import tempfile

import numpy as np

import common

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
CELL_W, CELL_H = 1000, 400
CELL_PX = 202          # the still is taken at the width Word gives the picture (half its pixels)


def write_check(name, lines):
    """tools/numfig/wt_<name>.check.txt, printed as well."""
    text = "\n".join(lines).rstrip() + "\n"
    print(text)
    with open(os.path.join(HERE, f"wt_{name}.check.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def publish(name, title, aria, data, js, w=CELL_W, h=CELL_H, px=CELL_PX, cell=True):
    """Write nf-wt-<name>.html and its still; return the still's PNG path."""
    script = (CELL_JS if cell else QUIET_CTL) + "\n" + js
    common.build_html(f"wt-{name}", title, aria, w, h, data, script)
    return common.still(f"wt-{name}", width=px)


def cached(tag, fn, *args, **kw):
    """fn(*args, **kw), kept in the temp directory under a key of its source and
    arguments: the slow checks (FDTD runs) are computed once while the drawing
    is iterated, and again whenever the model changes."""
    import inspect
    key = hashlib.sha1((tag + inspect.getsource(fn) + repr(args) + repr(sorted(kw.items()))).encode()).hexdigest()[:16]
    path = os.path.join(tempfile.gettempdir(), f"wt-{tag}-{key}.pkl")
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            return pickle.load(fh)
    out = fn(*args, **kw)
    with open(path, "wb") as fh:
        pickle.dump(out, fh)
    return out


# ------------------------------------------------------------------ Euler-Bernoulli FE
def hermite_beam(ne, L, EI, m):
    """Stiffness and consistent mass of ne equal Hermite (cubic) beam elements
    over length L, dofs (w, theta) per node, 2 (ne + 1) of them."""
    le = L / ne
    k = EI / le ** 3 * np.array([[12, 6 * le, -12, 6 * le], [6 * le, 4 * le ** 2, -6 * le, 2 * le ** 2],
                                 [-12, -6 * le, 12, -6 * le], [6 * le, 2 * le ** 2, -6 * le, 4 * le ** 2]])
    mm = m * le / 420 * np.array([[156, 22 * le, 54, -13 * le], [22 * le, 4 * le ** 2, 13 * le, -3 * le ** 2],
                                  [54, 13 * le, 156, -22 * le], [-13 * le, -3 * le ** 2, -22 * le, 4 * le ** 2]])
    n = 2 * (ne + 1)
    K, M = np.zeros((n, n)), np.zeros((n, n))
    for e in range(ne):
        s = slice(2 * e, 2 * e + 4)
        K[s, s] += k
        M[s, s] += mm
    return K, M


def hermite_shape(xi, le):
    """Cubic Hermite shape functions at xi in [0, 1] of an element le long."""
    return np.array([1 - 3 * xi ** 2 + 2 * xi ** 3, le * (xi - 2 * xi ** 2 + xi ** 3),
                     3 * xi ** 2 - 2 * xi ** 3, le * (-xi ** 2 + xi ** 3)])


# ------------------------------------------------------------------ the cells' shared script
# Stroke widths in drawing units for a figure shown about 200 px wide (a
# fifth of W): the numfig widths (structure 1.6 to 2, data 2.2 to 2.6, guide
# 1) as seen on a 672 px column, carried to the cell.
QUIET_CTL = r"""
(() => {                                         // the pause and restart buttons, out of the way
  const s = document.createElement('style');      // until a pointer or the keyboard asks for them
  s.textContent = '.ctl{right:3px;bottom:3px;gap:3px;opacity:0}' +
    '.ctl button{width:24px;height:24px;font-size:10px}' +
    '@media (hover:hover){.fig:hover .ctl{opacity:1}}.ctl:focus-within{opacity:1}';
  document.head.appendChild(s);
})();
"""

CELL_JS = QUIET_CTL + r"""
/* ---- the table's small figures (tools/numfig/wt_lib.py) ---- */
const SW = { axis: 5, struct: 7, data: 9, thin: 4.5, guide: 4 };
const DASH = [16, 13];
const TS = 58;                                   // type, the few labels there are
/* a TikZ primitive of the engine, drawn k times its size (strokes too) */
function big(x, y, k, f) { ctx.save(); ctx.translate(x, y); ctx.scale(k, k); f(); ctx.restore(); }
/* hatched ground, as TikZ draws it, from x0 to x1 at y: the line and the hatch below it */
function ground(x0, x1, y, o = {}) {
  const { alpha = 1, step = 26, len = 22, width = SW.thin } = o;
  line([[x0, y], [x1, y]], { color: C.ink, width, alpha });
  ctx.save(); ctx.beginPath(); ctx.rect(x0, y, x1 - x0, len + 2); ctx.clip();
  for (let x = x0 - len; x < x1 + len; x += step)
    line([[x + len, y], [x, y + len]], { color: C.ink, width: width * .7, alpha });
  ctx.restore();
}
/* the share of a loop of period P that phase-shifted time s has reached */
const wrap = (s, P) => ((s % P) + P) % P;
"""
