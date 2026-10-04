r"""fscheck.py -- automatic checks of a blog figure PDF in house style v3.

The checker of adzetto/Continuum_Mechanics_Notes (figures/common/fscheck.py),
as it is there, but for three things: a blog figure may be wider than the
notes' R10 page (a row of panels in the 672 px column), up to MAX_MM; a
label set upright (an axis label turned up the side) is read along its
column as a row is; and a fraction, the glyphs over and under one TeX rule,
is one label (fractions()), so its bar does not part its own numerator from
its denominator.

Rules, as for the course figures (style/v3/fscheck.py):
  1. label clearance: the ink of every label keeps >= 1.5 pt from the ink of
     every stroked line (strokes at their true width, arrow tips filled);
  2. label pairs: the ink of two different labels keeps >= 1.5 pt;
  3. bare tips: every arrow tip sits on a shaft at least as long as the tip;
  4. size: the figure is at most MAX_MM wide.
Ink is measured on a raster at 1200 dpi (0.06 pt per pixel): the labels are
rendered alone (all line art redacted away), the strokes are rasterised from
the vector paths; TeX rules (fraction bars, 0.4 pt) count as label ink.
Glyphs whose font boxes overlap, or which sit on one row (or, set upright,
in one column) less than 2 pt apart, belong to one label (subscripts,
under-tildes, primes, products such as Q x); every ink pixel goes to the
label whose glyph boxes hold it.  Filled areas without a stroke (element and region
fills, fraction rules) are not lines.
Usage:  python fscheck.py fig.pdf [--verbose]
"""
import sys

import numpy as np
import pymupdf
from PIL import Image, ImageDraw
from scipy import ndimage

MIN_CLEAR = 1.5          # pt
ROW_GAP = 2.0            # pt, glyphs on one row closer than this are one label
DPI = 1200
K = DPI / 72.0           # px per pt (PDF units; 1 bp = 1.0038 pt, ignored)
MAX_MM = 165.0
MAX_WIDTH = MAX_MM / 25.4 * 72.0 + 8.0      # and the page's 4 pt margin each side (make.py)


def bez(p0, p1, p2, p3, n=24):
    t = np.linspace(0.0, 1.0, n)[:, None]
    P = [np.array([q.x, q.y]) for q in (p0, p1, p2, p3)]
    return ((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1]
            + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3])


def paths(page, rules):
    """Stroked paths: (list of polylines, width, is_tip, drawing).  Horizontal
    strokes 0.4 pt wide are TeX rules (fraction bars) and go to rules."""
    out = []
    for d in page.get_drawings():
        if d['type'] not in ('s', 'fs'):
            continue
        lines = []
        for it in d['items']:
            if it[0] == 'l':
                lines.append(np.array([[it[1].x, it[1].y], [it[2].x, it[2].y]]))
            elif it[0] == 'c':
                lines.append(bez(*it[1:5]))
            elif it[0] == 're':
                r = it[1]
                lines.append(np.array([[r.x0, r.y0], [r.x1, r.y0], [r.x1, r.y1],
                                       [r.x0, r.y1], [r.x0, r.y0]]))
            elif it[0] == 'qu':
                q = it[1]
                lines.append(np.array([[q.ul.x, q.ul.y], [q.ur.x, q.ur.y],
                                       [q.lr.x, q.lr.y], [q.ll.x, q.ll.y],
                                       [q.ul.x, q.ul.y]]))
        if not lines:
            continue
        wd = d.get('width') or 0.0
        if (d['type'] == 's' and len(lines) == 1 and len(lines[0]) == 2
                and abs(lines[0][0][1] - lines[0][1][1]) < 1e-3
                and 0.39 < wd < 0.41):
            rules.append(lines[0])
            continue
        fill, col = d.get('fill'), d.get('color')
        tip = (d['type'] == 'fs' and fill is not None and col is not None
               and all(it[0] == 'l' for it in d['items'])
               and len(d['items']) <= 4
               and max(abs(a - b) for a, b in zip(fill, col)) < 0.02)
        out.append((lines, d.get('width') or 0.0, tip, d))
    return out


def stroke_mask(page, P):
    W, H = int(page.rect.width * K) + 1, int(page.rect.height * K) + 1
    img = Image.new('1', (W, H), 0)
    dr = ImageDraw.Draw(img)
    for lines, w, tip, d in P:
        pw = max(1, int(round(w * K)))
        for L in lines:
            pts = [(float(x * K), float(y * K)) for x, y in L]
            dr.line(pts, fill=1, width=pw, joint='curve')
            for x, y in pts:
                r = pw / 2.0
                dr.ellipse([x - r, y - r, x + r, y + r], fill=1)
        if tip:
            poly = [(float(x * K), float(y * K)) for L in lines for x, y in L]
            dr.polygon(poly, fill=1)
    return np.array(img, dtype=bool)


def text_mask(pdf):
    doc = pymupdf.open(pdf)
    page = doc[0]
    page.add_redact_annot(page.rect)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_REMOVE,
                          graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED,
                          text=pymupdf.PDF_REDACT_TEXT_NONE)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(K, K), colorspace=pymupdf.csRGB,
                          alpha=False)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)
    a = a[:, :3 * pix.width].reshape(pix.height, pix.width, 3)
    return a.min(axis=2) < 128


def glyph_groups(page):
    """Labels as groups of glyphs whose font boxes overlap."""
    raw = page.get_text('rawdict')
    G, vert = [], []
    for b in raw['blocks']:
        for l in b.get('lines', []):
            up = abs(l.get('dir', (1, 0))[0]) < 0.5     # a line set upright (a rotated axis label)
            for sp in l['spans']:
                for c in sp['chars']:
                    if c['c'].strip():
                        G.append([c['c'], list(c['bbox'])])
                        vert.append(up)
    parent = list(range(len(G)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    tol = 0.2
    for i in range(len(G)):
        for j in range(i + 1, len(G)):
            a, b = G[i][1], G[j][1]
            if (a[0] - tol < b[2] and b[0] - tol < a[2]
                    and a[1] - tol < b[3] and b[1] - tol < a[3]):
                parent[find(i)] = find(j)
    groups = {}
    for i, (ch, bb) in enumerate(G):
        groups.setdefault(find(i), []).append((ch, bb, vert[i]))
    groups = [[(ch, bb) for ch, bb, v in g] for g in groups.values()]
    upright = [all(vert[k] for k in range(len(G)) if find(k) == r) for r in
               dict.fromkeys(find(i) for i in range(len(G)))]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a, b = union_box(groups[i]), union_box(groups[j])
                if upright[i] and upright[j]:   # an upright line: its glyphs stack, one column
                    a, b = (a[1], a[0], a[3], a[2]), (b[1], b[0], b[3], b[2])
                hov = min(a[3], b[3]) - max(a[1], b[1])
                gap = max(a[0], b[0]) - min(a[2], b[2])
                if hov > 0.4 * min(a[3] - a[1], b[3] - b[1]) and gap < ROW_GAP:
                    groups[i] += groups[j]
                    upright[i] = upright[i] and upright[j]
                    del groups[j]
                    del upright[j]
                    merged = True
                    break
            if merged:
                break
    return groups


def fractions(groups, rules, reach=5.0):
    """A fraction is one label: the glyphs over a TeX rule (a fraction bar) and
    under it, within `reach` pt of it and across its span, join one group."""
    for (xa, ya), (xb, yb) in rules:
        x0, x1 = min(xa, xb), max(xa, xb)
        hit = [i for i, g in enumerate(groups)
               if (lambda b: b[0] < x1 + 0.5 and b[2] > x0 - 0.5 and b[1] < ya + reach and b[3] > ya - reach)(union_box(g))]
        if len(hit) > 1:
            merged = [c for i in hit for c in groups[i]]
            groups = [g for i, g in enumerate(groups) if i not in hit] + [merged]
    return groups


def union_box(grp):
    return (min(b[0] for c, b in grp), min(b[1] for c, b in grp),
            max(b[2] for c, b in grp), max(b[3] for c, b in grp))


def check(pdf, quiet=False, verbose=False):
    page = pymupdf.open(pdf)[0]
    rules = []
    P = paths(page, rules)
    S = stroke_mask(page, P)
    T = text_mask(pdf)
    h = min(S.shape[0], T.shape[0])
    w = min(S.shape[1], T.shape[1])
    S, T = S[:h, :w], T[:h, :w]
    for (xa, ya), (xb, yb) in rules:
        r = int(0.2 * K) + 1
        T[max(int(ya * K) - r, 0):int(ya * K) + r + 1,
          max(int(min(xa, xb) * K), 0):int(max(xa, xb) * K) + 1] = True
    groups = fractions(glyph_groups(page), rules)
    owner = np.zeros((h, w), dtype=np.int32)
    names = []
    e = 0.6
    for gi, grp in enumerate(groups, start=1):
        names.append(''.join(ch for ch, bb in sorted(grp, key=lambda q: q[1][0])))
        for ch, (x0, y0, x1, y1) in grp:
            owner[max(int((y0 - e) * K), 0):min(int((y1 + e) * K) + 1, h),
                  max(int((x0 - e) * K), 0):min(int((x1 + e) * K) + 1, w)] = gi
    if (owner == 0).any() and (owner > 0).any():
        idx = ndimage.distance_transform_edt(owner == 0, return_distances=False,
                                             return_indices=True)
        owner = owner[idx[0], idx[1]]
    lab = np.where(T, owner, 0)
    n = len(groups)
    dist_s = ndimage.distance_transform_edt(~S)
    ok, msgs, worst = True, [], 1e9
    boxes = ndimage.find_objects(lab, max_label=n)
    for i, sl in enumerate(boxes, start=1):
        if sl is None:
            continue
        y0, x0 = sl[0].start, sl[1].start
        m = lab[sl] == i
        clear = dist_s[sl][m].min() / K - 0.5 / K
        worst = min(worst, clear)
        if clear < MIN_CLEAR:
            ok = False
            msgs.append('label "%s" at (%.1f, %.1f) pt: %.2f pt from a line'
                        % (names[i - 1], x0 / K, y0 / K, clear))
    pad = int(3 * K)
    for i, sl in enumerate(boxes, start=1):
        if sl is None:
            continue
        ys = slice(max(sl[0].start - pad, 0), min(sl[0].stop + pad, h))
        xs = slice(max(sl[1].start - pad, 0), min(sl[1].stop + pad, w))
        win = lab[ys, xs]
        others = (win > i)
        if not others.any():
            continue
        dist = ndimage.distance_transform_edt(win != i)
        for j in np.unique(win[others]):
            dmin = dist[win == j].min() / K - 0.5 / K
            worst = min(worst, dmin)
            if dmin < MIN_CLEAR:
                ok = False
                msgs.append('labels "%s" and "%s": %.2f pt apart'
                            % (names[i - 1], names[j - 1], dmin))
    shafts = [L for lines, wd, tip, d in P if not tip for L in lines]
    for lines, wd, tip, d in P:
        if not tip:
            continue
        V = np.unique(np.round(np.vstack(lines), 3), axis=0)
        if len(V) != 3:
            continue
        best = None
        for a in range(3):
            A, B = V[(a + 1) % 3], V[(a + 2) % 3]
            L = np.linalg.norm(V[a] - 0.5 * (A + B))
            if best is None or L > best[0]:
                best = (L, V[a], 0.5 * (A + B))
        L, apex, base = best
        found = any(np.linalg.norm(e - base) < 1.2
                    and np.sum(np.linalg.norm(np.diff(Lp, axis=0), axis=1)) >= L
                    for Lp in shafts for e in (Lp[0], Lp[-1]))
        if not found:
            ok = False
            msgs.append('bare tip at (%.1f, %.1f), length %.1f pt'
                        % (apex[0], apex[1], L))
    Wd = page.rect.width
    if Wd > MAX_WIDTH:
        ok = False
        msgs.append('figure %.1f mm wide, more than %g mm' % (Wd / 72 * 25.4, MAX_MM))
    if not quiet or not ok:
        for m in msgs:
            print('    ' + m)
    if verbose or not quiet:
        print('    %s: %d labels, %d strokes, smallest clearance %.2f pt, '
              '%.1f x %.1f mm' % (pdf.split('/')[-1], n, len(P), worst,
                                  Wd / 72 * 25.4, page.rect.height / 72 * 25.4))
    return ok


if __name__ == '__main__':
    good = all(check(f, quiet=False, verbose='--verbose' in sys.argv)
               for f in sys.argv[1:] if not f.startswith('--'))
    sys.exit(0 if good else 1)
