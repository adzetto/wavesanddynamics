# tools/blogfig: his blog's figures, redrawn

His posts' figures were screenshots of slides and plots. On 4 Oct 2026 he
asked for each to be redrawn in the house style of his course notes
(adzetto/Continuum_Mechanics_Notes, `figures/common`, style v3), as still
pictures. Each figure here is one module, which draws one picture of one
post; `make.py` builds them all to `content/blog-figs/<slug>/<stem>.svg`, and
`site/build.py` publishes that SVG wherever the post shows the figure cut out
of his screenshot (`text/<stem>.png`): in the post, and on the post's card on
the Blog.

```
python tools/blogfig/make.py [name ...] [--no-check] [--dpi 300]
```

| module        | post                                                     | picture       |
|---------------|----------------------------------------------------------|---------------|
| `som_fig1`    | impulsive-noise-detection-with-semi-organizing-map-...  | `fig1`        |
| `som_fig2`    | impulsive-noise-detection-with-semi-organizing-map-...  | `fig2`        |
| `som_fig3`    | impulsive-noise-detection-with-semi-organizing-map-...  | `fig3`        |
| `ldv_speckle` | laser-doppler-vibrometer-how-it-works-...-speckle-noise  | `fig-speckle` |
| `moo_fig1`    | multi-objective-optimization                             | `fig1`        |
| `moo_fig2`    | multi-objective-optimization                             | `fig2`        |
| `moo_fig3`    | multi-objective-optimization                             | `fig3`        |
| `swpt_fig1`   | stationary-wavelet-package-transformation                | `fig1`        |

## The rules

- **His words are his.** Every word in a figure is as he wrote it, spelling
  included ("EVALUATIONARY ALGORITHMS", "Goal Atteintment", "Saticifing",
  "dedector", "an Polytec", the MOGA line twice). Symbols are set as the
  symbols they are (P_t, d_s, MD_i^s); no word is broken at a line's end.
- **Python computes the geometry, TeX only styles it.** A module's `body()`
  returns the TikZ picture with every point already in pt: Pareto fronts as
  the points no other point dominates (`geom.front`), a ray's meeting with a
  region (`geom.hit`), indifference curves tangent to a region, a tree laid
  out from its leaves, tilings whose cells have equal areas.
- **Labels keep their distance.** Every label is placed by its box, which TeX
  measures (`geom.size`, cached in `build/blogfig/sizes.json`; `make.py` asks a
  figure for its picture a second time once the boxes are measured). Where a
  sketch is crowded, `geom.Scene` records the strokes and puts each label at
  the nearest spot that keeps 2 pt from all of them.
- **The checks of the course notes** (`fscheck.py`, theirs as it is but for
  the width: up to 165 mm here, and upright axis labels read as one label,
  and a fraction as one label): label ink at least 1.5 pt from every line and
  from every other label, no arrow head without a shaft, the width. A figure
  that fails is not written.
- **Style**: `figstyle.tex`, the notes' v3 (line weights 0.354/0.709/1.417 pt,
  blue axes and their labels, hollow points, bold blue panel letters, 10 pt
  Computer Modern) and, for the blog, pgfplots axes in the same weights
  (`fs plot`), and green dimension lines (`fs dim`).

## His plots: read back from the pictures

Four figures redraw his data plots, whose numbers survive only as the
pictures the live site serves (`post/<slug>/<k>-<stem>.webp`; `content/blog/`
is not in the repository). `digitize.py` reads their curves back, once, into
`data/<name>.json`, which the figure is built from:

```
python tools/blogfig/digitize.py som_fig2 <the post's 03-fig2.webp>
```

A plot is read inside its frame (its edges found as the picture's long dark
lines), its ticks and legend masked. A solid line is kept as a polyline (per
pixel column, the run it came in on); a dotted one (MATLAB's `:`) as the
specks it was drawn with, which the figure draws as dots again; a scatter as
its isolated points, and where his points ran together into solid ink, that
ink as filled outlines. Legends, notes, circles and fitted lines are found
and kept where he put them; where a curve cannot be told from a line drawn
over it, it is carried through by a monotone spline through what can be read
(`knee_plot`), and the docstrings say so.

## Output

`pdflatex`, then `fscheck.py`, then `pdftocairo -svg` (glyphs as outlines:
no fonts to load), then `make.slim`: numbers to 0.01 pt and no space between
tags. Dots are strokes of no length with round caps, so a dot is a few bytes.
`build/blogfig/<name>.png` is the picture to look at.
