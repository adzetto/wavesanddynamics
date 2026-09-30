# -*- coding: utf-8 -*-
"""Write the Big Picture's artwork: one picture from each document and deck.

    python tools/bp_art.py [DIST]     (after a build: it reads DIST/fig,
                                       site/dist unless another is named)

The Big Picture page (site/parts/documents.py) shows every document and deck
as a card under its topic, with a picture of its own, the way a shelf shows
books by their covers: a figure the professor drew or chose for that
document, as its page draws it, or a slide of the deck. Nothing is made for
the card but the probability deck's (below); every other picture is his.

Round 11 (27 Sep 2026): every picture is cut for its box. A card's picture is
16:9 (the box the page gives it, 190 to 330px wide), so each pick names the
part of its figure that reads at that size, and that part is fitted to 16:9:
cut down where the figure is photographic or a slide, and widened with the
figure's own white paper where the figure is narrower or wider than the box
(the page multiplies that white into its plate, so it reads as the plate's
margin). Written at 640 x 360, twice the smallest box and enough for the
largest, WebP quality 82, to content/bigpicture/<name>.webp, with art.json
beside them: {key: [file, width, height]}, key the document's slug or the
deck's page. build.py copies the pictures to art/ and hands the table to the
page.

The picks, and why each:
  - the vibrations and waves guide: its building shaking in its first modes,
    the total motion as the sum of the modes, which is what "dynamical
    behavior of engineering structures" means. (Its cover, a 4:1 strip of the
    bridge, was lost in a 16:9 box.)
  - the photons piece: its one figure, the two slits and their fringes; since
    round 12 its redraw from a model (nf-ph-slits), the panel where the path
    is not recorded, cut about the axis from the source to the intensity.
  - the signal guide: its cover's input, system and the arrow out, the idea
    the guide is built on.
  - the machine learning guide: the logistic curve, one clean picture of
    learning a boundary.
  - the probability deck: its first slide's four connected questions, each
    one computed and in motion in the figures' family (nf-pr-overview,
    tools/numfig/pr_overview.py), his words and his arrows. Round 12: the
    client asked for "animative bir şey" in place of the slide itself, the one
    picture here made for its card; it is 16:9, so nothing is cut.
  - the brochure: the vibration modes of a structure with its sensors.
  - the SHM introduction: the sensor, the crack, its echo and the recorded
    signal.
  - the sound piece: the microphone array's geometry.
  - the PhD deck: its thesis title slide, with the test car on the rail.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "content", "bigpicture")
SIZE, QUALITY = (640, 360), 82

_VW = "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation"
_SP = "signal-processing-system-identification-and-optimization"
_ML = "machine-learning-the-complete-picture-and-guide-5"
_FB = "from-bridges-to-photons"

# key -> (source under DIST, or content: for a deck's slide or a figure redrawn
# from a numerical model; out name; the part to show, (left, top, right,
# bottom) in the source's pixels, None for all of it; and, for a panel that
# must stand alone, "alone": its neighbours are left out and the box is
# widened with paper instead).
PICKS = {
    _VW: ("content:anim/nf-building.webp", "waves-guide", (30, 168, 948, 622), "alone"),
    _FB: ("content:anim/nf-ph-slits.webp", "photons", (0, 187, 668, 563), "alone"),
    _SP: ("content:anim/nf-sp-cover.webp", "signal-guide", (20, 0, 600, 292), "alone"),
    _ML: ("content:anim/nf-mla-logreg.webp", "ml-guide", (126, 25, 1300, 685)),
    "probability-statistics.html": ("content:anim/nf-pr-overview.webp", "probability-deck", None),
    # his research documents' pictures are redrawn too (round 12): each card
    # shows its document's own figure in the family's style
    "brochure-shm-and-ndt-2-pages": ("content:anim/nf-shm-sensors.webp", "shm-brochure",
                                     (0, 0, 1195, 672)),
    "understanding-shm-and-ndt": ("content:anim/nf-shm-ndt.webp", "shm-introduction",
                                  (0, 0, 1312, 738)),
    "sound-detection-and-tracking": ("content:anim/nf-snd-array.webp", "sound",
                                     (0, 0, 1330, 748)),
    "presentation.html": ("content:deck-phd/web/s003-1600.webp", "phd-deck", None),
}


def fit(box, size, aspect, alone=False):
    """The box widened (never narrowed) to the aspect about its centre, then,
    unless its part must stand alone, moved back inside the picture where it
    can be; what still falls outside is paper to be added."""
    w0, h0 = size
    x0, y0, x1, y1 = box or (0, 0, w0, h0)
    w, h = x1 - x0, y1 - y0
    if w / h > aspect:
        h = w / aspect
    else:
        w = h * aspect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    x0 = cx - w / 2 if alone or w > w0 else min(max(0, cx - w / 2), w0 - w)
    y0 = cy - h / 2 if alone or h > h0 else min(max(0, cy - h / 2), h0 - h)
    return round(x0), round(y0), round(x0 + w), round(y0 + h)


def cut(im, box, keep=None):
    """The part of the picture in the box (and in `keep`, when only that part
    is to be seen), on the picture's own paper (its top left pixel) wherever
    the box runs past it."""
    from PIL import Image
    x0, y0, x1, y1 = box
    k0, l0, k1, l1 = keep or (0, 0, im.width, im.height)
    a, b = max(x0, k0, 0), max(y0, l0, 0)
    out = Image.new("RGB", (x1 - x0, y1 - y0), im.getpixel((0, 0)))
    out.paste(im.crop((a, b, min(x1, k1, im.width), min(y1, l1, im.height))), (a - x0, b - y0))
    return out


def main(dist=None):
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
    from PIL import Image
    dist = os.path.abspath(dist or os.path.join(ROOT, "site", "dist"))
    os.makedirs(OUT, exist_ok=True)
    table = {}
    for key, (src, name, box, *how) in PICKS.items():
        path = (os.path.join(ROOT, "content", src[8:]) if src.startswith("content:")
                else os.path.join(dist, src))
        with Image.open(path) as im:
            im = im.convert("RGB")
            alone = "alone" in how
            part = fit(box, im.size, SIZE[0] / SIZE[1], alone)
            pic = cut(im, part, box if alone else None).resize(SIZE, Image.LANCZOS)
        dst = os.path.join(OUT, f"{name}.webp")
        pic.save(dst, "WEBP", quality=QUALITY, method=6)
        table[key] = [f"{name}.webp", *SIZE]
        print(f"{name:18s} {SIZE[0]}x{SIZE[1]} from {part}  {os.path.getsize(dst) // 1024} KB")
    with open(os.path.join(OUT, "art.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(table, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:2]))
