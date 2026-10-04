# numfig: figures redrawn from numerical models

The waves guide (`doc/dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation.html`)
had figures drawn by hand or by an image generator. Figures 4, 5, 6, 7, 11, 12 and 13 are
redrawn here. Each one is computed from a real numerical model and animated. Its motion
is the model's motion, not an illustration of it.

The client asked for this in these words (Turkish, 26 Sep 2026):
- the drawings should be like TikZ or pgfplots output from a numerical model, not like an
  AI drawing;
- they should be animated;
- colours should be professional and fit the context;
- the motion should be in the style of manim, but positions and animations must be
  numerically exact;
- any Python library may be used (OpenSees, and so on) to run the analysis.

## What a figure is

Each figure consists of:

- **The generator**: one Python script, `tools/numfig/<name>.py`.
  - It runs the model with numpy and scipy (any pip package is fine; the `openseespy`
    wheel fails to load its DLL on this machine, so write the FE or SAFE yourself).
  - It writes the page through `common.build_html()`.
  - It writes the printed frame through `common.still()`.
  - It writes a validation report, `tools/numfig/<name>.check.txt`.
- **The page**: `content/anim/nf-<name>.html`.
  - A self-contained canvas page in the same frame as the professor's own animations
    (`content/anim/fig*.html`): pause and restart buttons, click to toggle, paused off screen.
  - In a guide's page, pause, restart and full screen sit in a row under the frame, beside
    the caption (`site/preview.py` `BAR`, `site/parts/docs.py`). The frame's own pause and
    restart stand down there (`engine.js` `HOSTED`, the class `chrome-out`), and the page
    drives the frame over `postMessage`. No button lies on the figure. A button the figure
    adds to `.ctl` (Figure 13's 3-D view) stays in the frame's bottom right corner.
  - `build_html()` inlines `engine.js` and your model's numbers (`DATA`) into it.
- **The printed frame**: `content/anim/nf-<name>.webp`, the figure complete at its
  `POSTER_T`. Print, and a page without scripts, show this in place of the old picture.
- **Optional sibling data**: `content/anim/nf-<name>-*.{bin,png,webp,json}`, fetched
  relative to the page. Use this only for data too big to inline, such as FDTD
  wavefield frames.

The site build publishes `content/anim/nf-*` to `anim/`. `content/anim/anim.json` maps each
document picture to its page; the controller (not you) adds your mapping.

## The contract

- **Size.** `build_html(name, title, aria, W, H, DATA, JS)`. Use W = 1000. Choose H for the
  content, typically 560 to 1100.
- **Title.** `title` is `"Figure N: <the first sentence of his caption>"`.
- **Aria text.** `aria` is one or two plain sentences saying what the reader sees.
- **Your script.** `JS` defines `draw()` and `POSTER_T` (the moment of the still). It must
  end with `boot();`.
  - `draw()` must be a pure function of the clock `t` (seconds) and `DATA`. No state
    accumulated across frames, and no `step()` integration.
  - This is what makes every frame exact. It is also what lets `?still&t=2.5` show any
    moment.
- **Engine (`engine.js`).** Do not edit it or `common.py`. If you need more, write helpers
  in your own script. Report engine bugs in your final message. Its API:
  - `C`: the palette.
  - Type: `text`, `math` (a small TeX subset: `_{}`, `^{}`, `\rm{}`, `\sqrt{}`, Greek
    and `\partial \cdot \times \approx \ll` and so on), and `panel('a', x, y)`.
  - Drawing: `line(pts, {progress})`, where `progress` draws the stroke along its arc
    length. Also `arrow`, `dot`, `pin(x, y, {roller})`, `fixedEnd`, `dim`.
  - Axes: `axes({...})` gives a pgfplots box axis, inward ticks and numeric labels, and
    returns `{X, Y, inside}`.
  - Colour: `diverging(v)` and `seq(v)`, plus the LUTs `DIVERGING` and `SEQ` for ImageData.
  - Intro timing: `seg(t0, dur)`, `easeInOut`, `easeOut`, `clamp`, `lerp`.
  - Data decoding: `b64f32` and `b64i8`, with `common.f32` and `common.i8` on the Python side.
- **Looking at your figure.** `common.still(name)` returns a PNG path. Look at it with your
  Read tool. `common.frames(name, [0.4, 1.2, 3, 8])` gives the figure at several moments.
  **Look at every figure you make, at several moments, before you call it done.**
- **Reduced motion.** A reader who asks for less motion sees `POSTER_T` still. So
  `POSTER_T` must show the whole figure complete and meaningful, not a blank frame.

## The look: pgfplots and TikZ, not generated art

- **Type.** CMU Serif (Computer Modern) only, which the engine loads. Variables are in
  italic math (`math('c_{\\rm{p}}', ...)`) and units are upright.
- **Sizes, in W = 1000 drawing units.** The iframe is 672 px wide on a desktop, so text
  shows at about 0.67 of these sizes.
  - Tick labels: 15.
  - Labels: 16 to 17.
  - Panel letters: 19 bold, "(a)", placed top left of each panel.
  - Nothing smaller than 14.
- **Panel subtitles.** A panel may carry a subtitle of five words or fewer after its letter,
  in `C.body`, lowercase, at 17 (`mlc_lib.sub()` sets it 35 units after the letter).
  - No bold sans titles.
  - No sentence-long annotations. The caption under the figure (his, fixed) explains.
  - Short labels are fine: 2 to 5 words at most.
- **Axes.** Real numeric ticks in real units (kHz, m/s, km/s, mm, µs, Hz, m), inward
  ticks, a full box, and a light grid only where reading values matters.
- **Parameter line.** A small parameter line in `C.muted`, size 14, gives credibility, for
  example `steel, 20 × 40 mm, E = 210 GPa, ν = 0.29`.
- **Strokes.**
  - Axes: 1.3.
  - Structures: 1.6 to 2.
  - Data curves: 2.2 to 2.6.
  - Guides: 1, dashed `[5, 4]`, in `C.guide`.
- **Colour.** Use the palette `C`: the site's inks and blues and one crimson (round 11
  replaced the burnt orange, which the client disliked; the crimson is matched to
  `C.blue` in CIELAB lightness, so neither side of a comparison shouts).
  - Ink `C.ink` for structure outlines and text.
  - The blues (`navy`, `blue`, `sky`, `mist`) for the structure's response and primary data.
  - `C.steel` fill with a `C.ink` outline for material cross-sections and plates.
  - The crimson `C.accent` `#A7203A` (and the brighter `C.amber` `#D14457`, the tint
    `C.wash` `#F9EEEE`) ONLY for the one thing the eye must follow:
    a defect, an echo, the highlighted mode, the operating point, a cut-on marker.
  - Signed fields (displacement, pressure) use `DIVERGING` (navy, white, crimson), with a
    colour bar and a numeric scale.
  - Machine learning figures: weights, activations and vector entries are signed values:
    positive blue, negative crimson (`signed()`, `SIGNED`, `S_POS`, `S_NEG` in
    `mlb_common.JS_LIB` and `mlc_lib.LIB`, `DIVERGING` read from its other end), with a key.
  - No gradients on shapes, no shadows, no rounded card boxes, no emoji, no pastel
    rainbow legends.
- **Shared conventions** (Figures 11, 12 and 13 must look like one family):
  - Transducer or probe: a navy rectangle (`C.navy`) with a white hairline between
    elements for arrays.
  - Test piece: `C.steel` fill, `C.ink` 1.6 outline, back wall drawn 2.4.
  - Flaw or defect: an accent-filled ellipse or notch, outline `#781E2C`.
  - Where his caption names a colour (machine learning Figure 14: "orange",
    "purple"), the figure draws that colour; nowhere else is orange used.
  - A-scans and signals: `C.navy` traces, 1.6 to 2 stroke, zero line in `C.rule`.
  - Machine learning figures:
    - the forecast or new prediction a figure is about is crimson; what happened is open
      navy marks;
    - groups found in data: navy circles, `C.blue` squares, `C.sky` triangles; never
      crimson;
    - training `C.mist` or `C.steel`, validation crimson, test navy (`C.steel2` as a
      band).
- **Supports.** Draw them as TikZ does: `pin()` and `fixedEnd()`. Beams are 2.0 ink lines,
  and deformed shapes are blue.
- **Legends.** Inside the axes, a thin 1 px box, white fill, serif 15.
- **Controls drawn in a figure** (a choice of value, a replay): `uiChip()` in `engine.js`,
  as Figure 18b's chips. White with a `C.guide` edge; the chosen one `C.navy` with white
  type; under the pointer `C.steel` with a navy edge; pressed `C.steel2`; unavailable pale.
  A keyboard stand-in (a transparent DOM button over it) gets a 2 px `#095A94` focus ring.
  Its hit area is as large as the layout allows (24 CSS px at least where it can be). A
  click on a control or on a hint that asks for one never also pauses the figure. Do not
  copy the frame's play or restart glyphs for another meaning.

## The motion: manim, with the physics exact

- **Easing: two kinds, both pure functions of `t`.**
  - `seg(t0, dur)` is manim's smooth (ease in and out). Use it for strokes drawing
    themselves.
  - `settle(t0, visual, bounce = 0)` is Motion's own spring (motion.dev's `spring()`,
    bundled into the engine). Use it for things that **arrive**: a label or a panel
    settling into place, a marker gliding to a new operating point, a probe stepping to
    its next position.
  - The site's interface moves on the same Motion springs (site/parts/springs.py), so
    the figures and the page feel like one piece.
  - Keep bounce 0 unless the thing is a physical object that would overshoot.
- **The intro** runs once, about 2 to 4 s, and replays on restart:
  - axes and structures draw themselves, using `line(..., {progress: seg(...)})`;
  - curves draw along their arc length, one after another;
  - labels fade in, with alpha from `seg`.
  - Use smooth `easeInOut`. Never bounce or overshoot.
- **Then the physics runs forever.** Every displacement is the model's own:
  - `Re{U e^{iωt}}` of a computed mode;
  - a Fourier synthesis with the computed dispersion relation;
  - a simulation frame.
  - A frequency sweep moves along the computed curve.
- **The time scale is honest.** If the motion is slowed, derive the slow-motion factor from
  the model's numbers. Where it is useful, say it in a tiny muted label, for example
  "time slowed 2 × 10⁵".
- **Every animated quantity is traceable to DATA.** Nothing hand-waved: no fake squiggles,
  no eyeballed curve shapes, no random noise.
- **Performance.** Aim for 60 fps on a laptop. Precompute heavy things in Python. For
  fields, colour an ImageData through the LUT.
- **Loops.** Loops should be seamless: whole periods, or a sweep that eases back.

## Words

- **Language.** English.
- **Labels use his terms from his caption.** His caption stays under the figure unchanged.
  The panels must match the caption's letters and what the caption says each shows.
- **No dashes.** No em dash (U+2014) and no spaced en dash anywhere; `build_html` refuses
  them. Use a comma, a colon or parentheses. Use a minus sign in math (the engine
  converts `-`).
- **Symbols in math.** A variable named in a label is set in math, as in its axis label
  (`K = 3`, `step t`, `n = 200`). In `math()`, a word macro swallows the space after it:
  write `'\\eta\\ = 0.3'`, not `'\\eta = 0.3'`. Percent signs close up (`80%`), and
  thousands take a comma (`20,000`), as his text writes them.
- **No personal data and no emails.**

## Nothing overlaps (round 12, binding)

The client's words: "latex style güzel overlap olmayan mükemmel stil". A label never sits
on another label, a stroke never runs through a label, and an arrow never runs through
data. `engine.js` measures this.

- **How to run it.** Open a page with `?still&overlap` (or `?t=<s>&overlap`), or call
  `common.overlaps(name, times)`.
- **What it records.** Every run of type is kept as its ink quadrilateral (measureText's
  actual bounds, through the current transform, so rotated labels are exact). Every
  dark stroke is kept as its segments, clipped to the current clip.
- **What it reports.** `labels`: pairs of runs from different labels whose ink meets.
  `crossings`: runs a stroke passes through.
- **What it forgives.** A label drawn again in place is a highlight, not a collision. A
  label on a line is fine when a white knockout drawn after the line covers it, as
  `dim()` does. Faint type (alpha below .35) and pale strokes (grids, rules) are left out.
- **The bar.** A figure is done when both lists are empty at the poster and at moments
  across its whole motion. The collisions are outlined in PNGs in the temp directory.

The one known false positive is an italic capital's box meeting the next letter within
an equation that was set in two calls (`building`, "C" and "ẋ"). Where a figure has such
a case, say so in `.check.txt`.

## Numerics and validation (the check file)

For each figure, `<name>.check.txt` lists:

- the model and its parameters;
- the mesh or grid, and how you converged it;
- at least two comparisons against a closed form or a textbook value, with the error.
  Examples: SAFE at low frequency against Euler-Bernoulli bending and rod `√(E/ρ)`;
  band edges against simply supported and clamped span frequencies; FDTD echo arrival
  against `2d/c`; Rayleigh-Lamb against the known S0 and A0 limits.

Print the key numbers when the generator runs.

## Checking inside the site (optional)

1. `python site/build.py --strict --no-word --out build/nf-<you>/dist` builds the site to
   your own folder. Never write to `site/dist`: others are building in parallel.
2. The figure is not in the page until the controller maps it. Test the page itself
   through `common.frames` and `still`.

## Restyling a figure

A change of look (its buttons, its colours, its type) changes the frame (`common.HEAD`),
the engine or the figure's script, and none of its numbers. Running the generator again
would train its model again: slow, impossible where torch or statsmodels is missing, and
with another library version perhaps other numbers. Instead:

1. Edit the figure's `JS` string in `<name>.py` (or `engine.js`, `common.HEAD`, or a
   library: `mla_shared.LIB`, `mlb_common.JS_LIB`, `mlc_lib.LIB`).
2. Run `python tools/numfig/reskin.py <name> --still` (`<name>` without `nf-`; `--all-ml`
   for the machine learning figures, `--all` for every page).

`reskin.py` rebuilds the page from the title, aria text, size and DATA it holds, the
current frame and engine, and its own script with your edits made in it. Each edit is
found in the page by its lines and the lines around them, exactly once. Where the
generator can be imported here, the script is also checked against the one it writes. A
page whose script the committed generator would not write is refused: run the generator
itself. `--still` photographs the poster again and fails on a collision the old page did
not have.

## Files you own

Only your `tools/numfig/<name>.py`, `tools/numfig/<name>.check.txt`, and
`content/anim/nf-<name>*`. Do not touch anything else:

- no other figure's files;
- not `site/`;
- not `anim.json`;
- not `engine.js` or `common.py`;
- not `tests/`.

No git commits.

## Round 2 (27 Sep 2026): faster, and more documents

The client, on the finished figures: "very beautiful, but make them open faster, one waits
a little on arriving at them". So, for every figure, old and new:

- **Timing budget.**
  - Readable within **0.8 s** of coming into view: axes, structures and the main curve are
    there.
  - The whole intro is over within **1.4 s**.
  - Strokes draw in 250 to 450 ms each, with staggers of 40 to 70 ms.
  - Labels arrive with `settle(t0, .28)` or quicker.
  - The physics starts moving by **0.6 s**, while the rest finishes arriving; no waiting
    for a ceremony.
- **The poster frame stays complete.** Reduced motion and print still get the whole
  figure.
- **Wiring a new document's figures.**
  - Do not edit `content/anim/anim.json`. Write your own fragment
    `content/anim/anim.<yourname>.json` in the same shape:
    `{"<document slug>": {"imageN": "nf-<name>.html"}}`.
  - `imageN` is the document's own picture stem. Build once and read
    `site/dist/doc/<slug>.html` (or `build/r10-<you>/dist/...`): every figure's
    `<img src=".../imageN.webp">` names it.
  - A picture named twice stops the build.
- **Pictures in table cells.** A drawing that lives inside a table cell is drawn at the
  cell's proportions (read the Word picture's width and height). The table's own agent
  wires cells; say which stems you drew.
- **Styles are one family.** Match the seven figures of the waves guide (`nf-dispersion`,
  `nf-periodic`, `nf-bulk-ut` and the others). Look at their stills before you design yours.
