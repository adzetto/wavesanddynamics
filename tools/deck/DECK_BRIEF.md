# The deck: how to recreate a slide of "Probability, statistics and estimation"

Read `tools/ROUND10.md` first; it binds. This file says how to recreate his slides 9 to 73
in the system that already made slides 1 to 8 (the deck's numbers: his keep his, and slide 65a
is ours, section 13). Slides 1 to 8 are the reference: when this file and those slides seem to
disagree, look at what the slides do. A slide may also play (section 14).

## 1. The job

- **The deck.** His 73 slides and one of ours (65a, section 13), 74 in all, shown by the presenter
  on `probability-statistics.html` (`site/parts/deck.py`).
- **The client, 27 Sep 2026:** "buradaki her slideı da yine yeniden oluştur. yine slide halde
  olabilsin ama slide halinde de figureler sunum vs mükemmel olsun". Every slide is recreated;
  it stays a slide in the same presenter; the slides and their figures must be perfect.
- **Done means:** `tools/deck/src/sNNN.html` (and `sNNN.py` if it has figures, `sNNN.pic.txt`
  if his picture had words) render through `tools/deck/render.py` with every check passing, you
  have looked at the result beside his original, and the slide is written to
  `content/deck-probstat/`.

## 2. The rules that bind

1. **His words, character for character.** Every word on the slide is his (on a slide of ours,
   section 13, every word is ours instead), from his PowerPoint
   (text boxes and tables, `his.py`) or from inside his pictures (`sNNN.pic.txt`). Nothing of
   his is dropped; nothing is added: no label, caption, parameter line, legend entry or unit
   of our own. His grammar stays ("2 different way", "etc"). The checker enforces this.
2. **His order and his hierarchy.** His headings stay headings, his take-away line stays the
   take-away, his lists keep their order, his tables their rows and columns. You may move a
   block on the page, and you may redraw every figure; you may not reword.
3. **One visual language.** Use the classes in `deck.css` and the figure library `fig.py`.
   Do not invent a new look for one slide. A slide's own `<style>` holds layout only: sizes,
   gaps, grid placement. No raw hex colours (use the tokens), no new fonts, no
   `text-transform`, no italics for text, no shadows, gradients or rounded boxes.
4. **Exact figures.** A curve is its formula, sampled; a sample is a deterministic draw from
   the model he states (`fig.sample`); his numbers are asserted in the script. Nothing drawn
   by eye.
5. **Legible at 960 wide.** Text is 24 px or more on the 1920 slide (the running foot and tick
   numbers 22 px). **Leading:** any text that runs to two lines or more at body or small sizes
   (body text, bullets, notes, box text, the take-away) is set at 1.3 to 1.5. Only a title or a
   heading of 30 px and up may be tighter (1.06 to 1.2), and a one-line label (a stage name in
   capitals, an axis label).
6. **Your files only.** You own `tools/deck/src/sNNN.*` and `content/deck-probstat/sNNN.png`,
   `web/sNNN-{1600,960,320}.webp` and `anim/sNNN.html` for your slides (a slide of ours by its
   stem, `s065a`). Do not edit `deck.css`, `deck.js`, `anim.js`, `fig.py`, `mathtype.py`,
   `render.py`, `his.py`, `vector.py`, `kit.*`, the manifest `deck.json` (render.py writes it) or
   anything in `content/deck-probstat/_orig/` (his originals, the backup). If the shared system
   needs a change, write your helper into your own `sNNN.py` and say so in your final message.

## 3. The workflow, slide by slide

1. **Read his slide.** `python tools/deck/his.py 23` prints every shape top to bottom: its
   place in px on the 1920 x 1080 slide, its fill, each paragraph with its runs (B bold,
   I italic, size in px, colour). It saves his pictures to `build/r10-deck/his/s023-picK.png`
   and prints his speaker notes (never shown; they hold the numbers behind a figure).
   `python tools/deck/his.py 23 --text` prints only his strings, as the checker compares them.
   The number is the deck's; `his.py` finds his slide for it (section 13).
2. **Look at his slide and his pictures.** `content/deck-probstat/_orig/s023.png` and the saved
   pictures. Decide what each part of the slide is (heading, body, formula, figure, table,
   note) and which of slides 1 to 8 is its model (section 11).
3. **Transcribe the words in his pictures** into `src/s023.pic.txt`, one per line, exactly as
   they appear (axis labels, legend entries, annotations). Lines starting with `#` are
   comments. Tick numbers are data and are not listed.
4. **Write `src/s023.html`** (section 5) and, for figures, `src/s023.py` (section 8).
5. **Render and look.** `python tools/deck/render.py 23 --look` renders and checks without
   touching `content/`. It prints `ok` or each problem, and the body's room ("body 235 to 926
   px, used to 885"). Look at `build/r10-deck/review/s023.png` (his slide and yours at 960, side
   by side) and `s023-960.png`; open `build/r10-deck/slides/s023@2x.png` for detail (crop it:
   the figures deserve a full-size look).
6. **Write.** `python tools/deck/render.py 23` renders, checks and, only if every check passes,
   writes `s023.png` (1920 x 1080) and the three web copies, and its line in the manifest
   (`content/deck-probstat/deck.json`: label, stem, title, and the length of a slide that
   plays). Ranges run in the deck's order: `render.py 60-66` holds 65a too.
   After any write it prints the deck as vectors (`vector.py`): the whole deck as one PDF,
   `content/deck-probstat/probability-statistics-and-estimation.pdf`, which the site offers for
   download, and each page as `web/sNNN.svg`, which the viewer draws while presenting. Both are
   written only when every page and every SVG agree with the slides' photographs and the PDF
   is under 3 MB (`render.py --vector` alone reprints them). `render.py --sheet` makes contact
   sheets of the whole deck as it stands (with `--vector`, of the SVGs as drawn too);
   `render.py --kit` renders the component sampler (`kit.html`) to
   `build/r10-deck/review/kit.png`.

Several agents render at once (section 15): each run has its own server and browser and writes
only its own slides (`build/r10-deck/review/sNNN.json` is each slide's report).

## 4. The page

A slide is 1920 x 1080, white, three bands:

- **Head** (`<header class="head">`): his title and the line under it. Title top at 64 px.
- **Body** (`<main class="body">`): everything else, on a 12 column grid. Its top follows the
  head: **235 px** under a one-line lede, **281 px** under a two-line one. It ends at **926 px**
  (12 px clear of the foot). So the body is about **690 px** tall (one-line lede) or **645 px**
  (two-line lede). Plan figure heights from this.
- **Foot** (`<footer class="foot">`): the accent rule, his take-away line, and the running line
  (his map reference and sources, then the page number).

The grid: margins 112 px, 12 columns of 112 px, gutters 32 px, content width 1696 px.
Useful widths: 3 columns 400, 4 columns 544, 5 columns 688, 6 columns 832, 7 columns 976,
8 columns 1120.

```html
<section class="slide">
 <style>/* layout for this slide only: sizes, gaps, placement */</style>
 <header class="head">
  <h1 class="title">Probability makes sampling risk visible</h1>
  <p class="lede">A lot has 25 items and exactly one defect. Inspect 3 distinct items selected uniformly at random.</p>
 </header>
 <main class="body g">
  <div class="s5 stack"> ...his text blocks... </div>
  <div data-fig="curve" class="s7 o6"></div>
 </main>
 <footer class="foot">
  <p class="take">A sample can miss a defect even when the sampling procedure is correct.</p>
  <p class="run"><span class="map">SLIDE 2 MAP <span class="sep">/</span> Box 4: event probabilities</span><span class="src">Sources: [1], [4]</span><span class="num">4</span></p>
 </footer>
</section>
```

- **The running line.** His orange line "SLIDE 2 MAP  /  Box 4: ..." and his grey
  "Sources: [..]" sit in the foot, under the take-away, as a running foot: it frees the head
  and keeps his reference on every slide in one place. Write each "/" of his as
  `<span class="sep">/</span>` with spaces around it (some of his have two: "LINEAR CASE / SLIDE
  2 MAP / Box 4: ..."). A "Sources" line on its own is just `<span class="src">`. The page number
  is his text too: `<span class="num">` with his number (slide 2 has none).
- **Titles.** `.title` is 64 px. A long title may take `.title--s` (54 px) or `.title--xs`
  (44 px); keep it to two lines.

## 5. The components (deck.css)

| class | what | size |
|---|---|---|
| `.title` (`--s`, `--xs`) | his title, Source Serif 4 600, ink | 64 (54, 44) |
| `.lede` | his line under the title, body colour | 34 |
| `.h` | his section heading, navy (his 15516A) | 38 |
| `.p` | his body text | 34 |
| `.ps` | his smaller body text (his 15 to 16 pt) | 30 |
| `.note` | his grey small print (536D78) | 28 |
| `.eq` | a display line of his maths, `<m>` inside | 34 |
| `.edge` | his words beside an arrow, accent | 30 |
| `.take` | his take-away line, navy | 32 |
| `.run` `.map` `.sep` `.src` `.num` | the running foot | 24 |
| `.tab` | a table, booktabs rules, first column his row labels | 30 (heads 26) |
| `.refs` | his references, two columns, number hanging | 22 |

Layout:

- `.g`: the 12 column grid. Children take `.s1` to `.s12` (span), `.o1` to `.o12` (start
  column), `.r1` to `.r4` (row), and `.mid`, `.bot`, `.stretch` (vertical alignment).
- `.stack` (56 px between blocks), `.stack--s` (32 px): blocks under each other.
- `.lines`: keep his line breaks. `<p class="p lines"><span>Given a model,</span><span>what
  could happen?</span></p>`. His paragraphs are often single lines he broke by hand; keep them
  where the column is wide enough, drop the spans where a narrow column would break them again.
- `.hair`: a hairline between two bands of the body (his light divider).
- `.route`: boxes in a row with 80 px between them for arrows.

Boxes and arrows (his coloured boxes, TikZ's `draw=colour, fill=colour!6`):

- `.node` with a colour: `.k-navy`, `.k-accent`, `.k-blue`, `.k-sky`, `.k-deep` (section 6).
  Its `.h` takes the colour. Square corners, 2 px border, a 6 % tint.
- `.panel`: his light grey note box (fill EEF2F5), no border.
- Arrows are drawn after layout by `deck.js`: `<i class="wire" data-from="#a" data-to="#b"></i>`
  anywhere in the body. Attributes: `data-from-side`/`data-to-side` (right, left, top, bottom;
  default the facing sides), `data-route` (`straight`, `-|`, `|-`), `data-at`/`data-at-to`
  (0 to 1 along the side), `data-color` (a token: accent by default, as his orange arrows;
  navy, sky ...), `data-width` (3), `data-gap` (6). The tip is TikZ's Stealth.
- A label over an arrow: put `<p class="edge above">his words</p>` in a `.cell` grid cell that
  spans the gap between the two boxes (slide 1).
- `.badge`: his numbers in orange discs (slide 2).

Lists and emphasis: `<ul class="list ps">` for his bullets (a small navy disc); `<b>` for his
bold runs inside a paragraph; `.c-accent`, `.c-blue`, `.c-sky`, `.c-deep`, `.c-muted` for his
coloured runs (section 6).

Leading (the rule of section 2): the classes above already follow it (the tokens `--lh-title`
1.06, `--lh-head` 1.2, `--lh-text` 1.4, `--lh-small` 1.34). In a slide's `<style>`, never set a
`line-height` under 1.3 on text that can wrap, unless it is a title or heading of 30 px and up.
`render.py` fails a slide that does ("tight leading").

## 6. Colour: his logic, the site's palette

His deck uses a handful of colours with steady meanings. Map them as follows, everywhere
(text, boxes, figures):

| his | meaning in his slides | ours (CSS token / text class / node / fig.py) |
|---|---|---|
| 15516A, 104B66 navy | titles, headings, take-away, the model | `--navy`, `.c-navy`, `.k-navy`, `C.navy` |
| 213C48 | body text | `--ink` (default) |
| 536D78 grey | the lede, notes, sources | `--body` (lede), `--muted` (`.note`, `.c-muted`) |
| DC8838, D98A3D, CC6600 orange | emphasis, the map reference, data, evidence, the one thing to follow | the crimson: text and strokes `--accent`, `.c-accent`, `.k-accent`, `C.accent`; fills `C.amber` |
| 775B9B purple | the estimate, the posterior, the result | `--blue`, `.c-blue`, `.k-blue`, `C.blue` |
| 42869A, 3E7A94 teal | processes, a second series | `--sky`, `.c-sky` (set darker as text), `.k-sky`, `C.sky` |
| AD4C3F, 8A2710 red | decisions | `--deep`, `.c-deep`, `.k-deep`, `C.deep` |
| 2E7D5B green (slide 27 only) | the "yes, linear" path | `--navy` |
| AFC9D4 light blue fills | bars, bands | `C.mist`, `C.steel2` |
| EDF4F6, EEF2F5 box fills | panels | `.panel`, node tints |

Series in a figure take `fig.SERIES` in order: navy, accent, blue, sky, deep. Where his figure
gives a series a colour of the list above, use its mapped colour (his prior navy, likelihood
orange, posterior purple become navy, accent, blue). Two series of similar lightness (navy and
blue) differ by line style too: dashed, solid, a fill.

The accent is crimson since 27 Sep 2026 (`tools/ROUND11.md`: accent `#A7203A`, amber `#D14457`,
deep `#781E2C`, wash `#F9EEEE`); the client disliked the burnt orange. One exception: where his
words on a slide name a colour, that slide keeps it. Slide 30 says "The tangent (orange)" and
slide 37 "orange tail is P(G < 0)", so those two marks are drawn in `C.orange` (fills) and
`C.orange_edge` (strokes). Grep a new slide's words for colour names before choosing colours.

## 7. Mathematics: `<m>`

Copy his formula exactly as `his.py` prints it and wrap it in `<m>...</m>`:

```html
<p class="eq"><m>P(a &lt; X &lt; b) = ∫ₐᵇ fₓ(x) dx</m></p>
<p class="ps">Damage <m>D</m>: 1% prior probability</p>
```

`mathtype.py` sets it in Latin Modern Math (Computer Modern) the way TeX would:

- a single letter is a variable, in TeX's math italic; Greek lower case italic, capitals upright;
- a run of two or more letters is a word or an operator name, upright (Cov, Var, SE, exp, "find
  the defect"); "d" before a single letter after a space is a differential (dx);
- his sub- and superscript characters become real ones (fₓ, σ², ₐᵇ stacked); his small capitals
  are subscript capitals (vᴅ, μʏ, yɴ); a sign between two subscripts joins them (Σᵢ<ⱼ);
- his accents (x̄, θ̂, Ŷ) are drawn over the letter; √n and √25 get their bar; three or more
  spaces between two formulas on one line become a wide gap.

Wrap only the maths, not the prose around it. Write `&lt;` for "<" in the source. To force a
reading, put markup inside: `<m><i>xy</i></m>`. The checker compares after Unicode
compatibility normalisation, so "σ²" in his file and σ with a superscript 2 on the slide are the
same text; a changed letter or word is not.

## 8. Figures: `fig.py`

A slide asks for a figure with `<div data-fig="name" class="s7 o6"></div>` (the `data-fig`
attribute first). `render.py` calls `name()` in `src/sNNN.py` and puts the returned HTML there.

```python
"""Slide 5: the M/M/1 queue of his notes: Wq = 5 rho/(1 - rho) min."""
import numpy as np
from fig import Fig, C

def wait():
    f = Fig(976, 616)                                  # px on the slide
    ax = f.axes(120, 14, 838, 468, xlim=(0, 1.04), ylim=(-2.5, 65),
                xticks=[0, .2, .4, .6, .8, 1], yticks=range(0, 61, 10),
                xlabel="Utilization = arrival rate / service rate",
                ylabel="Mean waiting time (min)", grid=True)
    ax.vline(1.0)                                      # a dashed guide
    rho = np.linspace(0, .9305, 900)
    ax.plot(rho, 5 * rho / (1 - rho), color=C.accent, width=4.5)
    for r in (.5, .8, .9):
        ax.mark(r, 5 * r / (1 - r), r=10, color=C.navy)
    return f.html()
```

The API (all sizes are px on the 1920 slide):

- `Fig(w, h)`: the canvas. `f.axes(x, y, w, h, ...)` a pgfplots axis in it. `f.text(x, y, html,
  anchor, size=, color=, cls=, rot=)` a label at a TikZ anchor (`center`, `north`, `south west`,
  `base`, ...); `f.line`, `f.poly`, `f.rect`, `f.circle`, `f.arrow(p0, p1)` (Stealth tip).
- `Axes(..., xlim, ylim, xlog, ylog, xticks, yticks, xticklabels, yticklabels, xtick_nd,
  ytick_nd, xlabel, ylabel, grid, box, ticks, frame)`: `box=True` is pgfplots' full box with
  inward ticks on all four sides; `box=False` the left and bottom lines only; `ticks="out"`
  or `"none"`; `frame=False` for a bare drawing area. `log_ticks(-1, 3)` gives decade ticks
  and their labels.
- Data: `plot`, `area(x, y1, y0)`, `bars`, `hist(values, edges)`, `scatter`, `step`, `stem`,
  `errorbar`, `interval`, `mark` (the operating point: a disc with a paper ring, accent by
  default), `hline`/`vline` (guides), `text` (at data coordinates), `leader`, `legend`.
- `ax.P(x, y)` converts data to figure px; `ax.X`, `ax.Y` for arrays.
- `sample(n, dist)` or `sample(n, dist_x, dist_y, rho=)`: a deterministic draw (Halton points
  through the inverse CDF, a Gaussian copula for pairs). Use it for every scatter and histogram.
- `C` the palette, `SERIES` the series order, `num()` tick formatting (a true minus sign).

The look (as `tools/numfig/README.md`, at slide scale): axes 2 px ink, ticks 10 px inward,
tick numbers Computer Modern 28 px, axis labels 30 px, data curves 4 px (3 px secondary),
guides 1.5 px dashed in `C.guide`, a light grid only where values are read, legends inside
the axes in a 1 px box. Every word in a figure is Computer Modern, and every word is his
(listed in `sNNN.pic.txt` unless it is in his text boxes). Tick numbers are data and may be
chosen freely; a tick labelled with a word (`a`, `b`) is his word and is checked. Put his
formula letters in labels as `<m>`: `xlabel="Unknown mean <m>μ</m> (MPa)"`.

Numbers: state the model in the script's docstring, compute from it, and assert his numbers
(`assert round(100 * post, 1) == 15.4`). His notes often give the model and its parameters.
Where his picture shows an "illustrative" sample, draw it with `sample()` from the model his
caption or notes state. A slide's script may borrow another's figure: `from s002 import
demand_capacity`.

## 9. The checks (`render.py`)

A slide is written to `content/` only when all pass:

- **his words**: every string of his (`his.py --text` plus `sNNN.pic.txt`) appears whole, and
  the words on the slide are exactly his words, counted. "words that are not his: ..." or "his
  words not on the slide: ..." name them.
- **overflow**: nothing outside the page, nothing clipped, text inside its own box, the body
  12 px clear of the foot, no text on other text, every wire found its boxes, and (since
  5 Oct 2026) every figure label inside its figure's box, with 1.5 px of slack. Twelve slides
  render with labels over their boxes today (7, 26, 28, 34, 36, 47, 48, 49, 54, 55, 56, 58):
  they will be refused at their next full render until those labels move; an `--anim-only`
  render reports them "as at HEAD" without refusing.
- **italic correction** (since 5 Oct 2026): `mathtype.py` gives a formula's last math italic
  letter TeX's italic correction from Latin Modern Math's table when text follows it (Y gets
  0.209 em). `fig.text_width` measures label widths from the font files (legend boxes use
  it). Both change how 29 slides set; `render.SET_BEFORE` holds those slides to the old
  setting until each is rendered again (take a label out of the set, then
  `render.py <labels> --force` and print the vectors).
- **legible**: 24 px text (22 px foot and ticks). A slide may lower its own floor with
  `<section class="slide" data-min="22">`; only the map (slide 2, 20) and the reference slides
  (71 to 73, 22) do.
- **leading**: text that runs to two lines is set at 1.3 or more, unless it is a title or a
  heading of 30 px and up.

`his.py` leaves out, with its reason, the only text in his file that is not text on his slide
(`SKIP`: on slide 2 a stray "d" and one line typed twice). If you find another such artifact,
do not add it to `SKIP` yourself; report it.

## 10. Before you call a slide done

- `render.py N` says `ok ... written`.
- Side by side with his slide (`review/sNNN.png`): every part of his is there, in his order,
  with his emphasis (his bold, his colours as mapped); nothing is added.
- The figure at full size: numbers right, labels clear of curves and of each other, nothing
  touching the box edges it should not touch.
- The 960 copy (`review/sNNN-960.png`): everything readable.
- It looks like one of slides 1 to 8: same margins, same components, same figure style.

## 11. Families: which slide to copy

| slides (their labels) | kind | model |
|---|---|---|
| 12, 13, 16, 17, 21 to 25, 28 to 33, 36, 38, 40, 46, 51, 52, 59, 65, 66 | text beside one figure | 4, 5 |
| 9, 20, 35, 39, 41, 60, 62 to 64, 70 | a table | 6 (booktabs `.tab`) |
| 10, 11, 27, 61, 65a, 69 | boxes and arrows | 1, 3 (`.node`, wires) |
| 7, 14, 15, 18, 19, 43, 45, 50, 68 | two or four blocks of text and small figures | 7 |
| 26, 34, 37, 42, 44, 47 to 49, 53 to 58, 67 | several panels of figures | 8, 7 |
| 2 | the map | 2 |
| 71 to 73 | references | `.refs`, `data-min="22"` |

Formula-heavy slides (17 to 19, 28 to 33, 61 to 67 with 65a): one `.eq` line per line of his, in his
order, grouped under his headings; his numbered steps stay numbered as he wrote them. His
multi-space gaps inside a line become wide gaps by themselves.

## 12. Notes

- His originals are backed up in `content/deck-probstat/_orig/` (PNG and `web/`); compare
  against them, never write there.
- `tools/bp_art.py` takes the Big Picture page's picture of this deck from
  `web/s001-1600.webp`; its owner re-runs it (slide 1 has changed).
- The site shows the slides as pictures (`web/*.webp`), draws each from its SVG wherever the
  picture would be enlarged (presenting, a Retina screen, a zoom), and offers the PDF under the
  deck's title. Nothing else in `tools/deck/` is published. The fonts are the site's (Source
  Serif 4, Source Sans 3), CMU Serif, and a subset of Latin Modern Math in `tools/deck/fonts/`
  (GUST Font License); the PDF embeds the glyphs it uses.

## 13. The deck's numbers: his slides keep his, ours are lettered

- **His slides keep his numbers, 1 to 73** (30 Sep 2026). A slide of ours goes by the number
  of his slide it follows and a letter: `65a` is the first after his 65, `65b` would be the
  next. Nothing of his is renumbered when one of ours joins, so his own cross-references
  ("Slides 65–67" on 9, "slides 65–66" on 67) still point where he meant.
- **Slide 65a is ours.** On 29 Sep 2026 the client asked for a slide on the Kalman filter's
  logic between his 65 and 66 ("kalman filter between 65-66 ... kalman filter logic slide").
  It is `src/s065a.*`, "The Kalman loop: predict, observe, weigh, update": the loop in the
  notation of his slide 65 (x̂⁻, F, H, K, indexed by k), and the next slide's hour drawn in
  one dimension, the update the exact product of the two Gaussians, the gain a balanced lever.
  It plays (section 14).
- **Labels and stems.** `his.LABELS` is the deck in order (`"1"` ... `"65"`, `"65a"`, `"66"`
  ... `"73"`); `his.label(x)` reads one (`65A`, ` 065a `); `his.stem(x)` names its files
  (`s065a`, `s004`) in `src/`, in `content/deck-probstat/` and in the review; `his.his(x)` is his
  number, or None for a slide of ours. `render.py` takes labels and ranges (`65a`, `60-66`).
  Every running foot ends in its label, as he typed his own numbers.
- **A slide of ours** is listed in `his.OURS` with its reason; adding one is one line there,
  and its label must be his number and a letter. It has no words of his and no
  `sNNN.pic.txt`; its words are ours and keep the site's rules (short, no em dash, no spaced
  en dash), and `render.py` checks those instead. Its review sheet shows it between the
  deck's slides before and after it.
- **The manifest.** `content/deck-probstat/deck.json` is the deck in order, a row a slide:
  `label`, `stem`, `title` and, for a slide that plays, `anim` (its length in seconds). A
  written slide updates its row; `render.py --manifest` writes it again from `content/`. The
  site reads it (`site/build.py` publishes each slide's files by its stem, and the presenter
  names each slide by its label: "Slide 65a: ...", the capsule's "65a / 73", the address
  `#65a`), and so do the PDF's bookmarks ("65a  The Kalman loop ...").
- **His words where his file is not.** His PowerPoint (`DECK_PPTX`) is on the controller's
  machine only. Elsewhere the words check cannot run and says so ("his words not checked");
  the slide is then written only with `--force`, after its words are held to the last print
  another way (the PDF's text, page by page, the page number aside). Render it again where
  his file is, and print the vectors there, at the next chance.

## 14. Animated slides

A slide may play: from its first moment to its last, which is its photograph. The static slide
is untouched: the photograph, the web copies, the PDF and the SVG are the last moment, and a
reader who asks for less motion (or a printer, or a page without scripts) sees only that.

- **Ask for it.** In `src/sNNN.py`, `ANIM = {"length": 9.8}`: seconds the slide plays; every
  mark is at rest by then. Optional `"frames": [4.2, 6.5]`, moments the review must show.
- **The marks of a figure** (`fig.py`) take `anim=`, and each call of `Fig` and `Axes` takes it:
  `draw(t0, dur)` (a stroke draws itself along its length, its dashes kept; a fill fades),
  `pop(t0, visual)` (it fades in and settles: a mark from 60 % of its size, a label from 10 px
  below), `fade(t0, dur)`, `wipe(t0, dur, dir)` (eased; `ease="linear"` at a steady pace, for a
  band that keeps up with a `seq` along the same axis), `grow(t0, dur, stagger)` (bars and stems from
  their base), `seq(t0, dt)` (marks one after another; on one line, the line extends through
  its points) and `keys(times, values, prop)` (a value from keyframe to keyframe: `xy`, `x`,
  `y`, `h`, `p`, `o`, `s`, `d`, `text`; its last value is the slide's). Combine them with `+`:
  `pop(4.9) + keys([4.9, 5.3], [xa, xf], prop="x")`. Times are seconds from the figure's start;
  `spec.end` is when it has arrived, to start the next thing from. A legend's `anim=` is one
  spec for all of it, or a list: its box, then each entry, so an entry arrives with what it
  names (`fig.Axes.legend` and the slides' own legends alike).
- **A ghost** (`ghost=True`) shows only while the slide plays and must leave (`out(t0)`) before
  the end: the 25 tests that become their average. On a slide of his a ghost's words may only be
  numbers (they are not his).
- **The slide's blocks** take `data-in` in `sNNN.html`: a time (`data-in="2.3"`), a figure's cue
  (`f.cue("observe", 2.3)` in the script, then `data-in="observe"`, `"observe-0.5"`); a cue's
  name is letters, digits and `_`. `data-as` says how it arrives: `pop` (the default), `fade`,
  `wipe` (`wipe-up`, `wipe-left` ...), `draw` (a stroke), `none` (a figure's wrapper that only
  starts its figure's clock). `data-dur` sets how long. A figure's clock starts at its wrapper's
  `data-in`: `<div data-fig="weigh" class="pic" data-in="2">`. A wire with `data-in` draws itself
  (`deck.js`), its tip coming as the line arrives.
- **The motion** is the site's: Motion's spring (bounce 0) for things that arrive, the figures'
  eased stroke for things that draw (`tools/numfig/engine.js`). A slide plays once, about 10 s
  at most; one idea arrives at a time, in the order the slide reads.
- **The page.** `render.py` writes the slide's own page, `content/deck-probstat/anim/sNNN.html`
  (the slide as rendered, its config and `anim.js`), beside the files every such page shares
  (`deck.css` with its fonts from the site's `fonts/`, `deck.js`, `anim.js`). The presenter
  opens it over the slide's picture each time the slide comes on; presenting, a step on while
  it plays completes it first, as a clicker completes a build.
- **The checks** (`render.py`, "animation"): the page runs without a script error; its last
  frame is the photograph (12 of 255 at most); it plays to its end and stops; with less motion
  asked for it shows the slide at once; nothing is still moving after `length`; every ghost
  leaves; every `keys` ends where the slide has it; every `data-in` names a cue that exists.
  The review adds `review/sNNN-anim.png`, the frames on one sheet, and `review/sNNN-anim-<t>.png`.
  Look at every frame: a label that sits on another while the slide plays is as wrong as one on
  the photograph.
- **A finished slide, given its animation:** `render.py 13-24 --anim-only` writes each slide's
  animation page and its manifest line and nothing else: never its photograph, its web copies
  or the vectors. It holds the slide to HEAD's byte for byte once what plays is taken out
  (`data-in`, `data-as`, `data-dur`, `data-anim`, `data-cues`, ghosts) and refuses a slide
  that differs; that check holds his words too, so his PowerPoint is not needed. What the
  layout check finds in a slide so held is reported ("as at HEAD"), not refused: the machine
  that renders may measure the fonts a hair differently from the one that took the photograph.

## 15. Rendering side by side

Several agents render at once. What belongs to one slide (its photograph, its web copies, its
animation page, its review files) is written whole or not at all: to a temporary file, then
renamed into place. What the deck shares is written under a lock in `build/r10-deck/locks/`: the
manifest (read, its line changed, written whole), the animation pages' shared files (written
only when they differ), and the vector print. A plain write never prints the vectors: the
controller runs `render.py --vector` once, when every agent is done. A lock older than an hour
was left by a run that died and is taken over.
