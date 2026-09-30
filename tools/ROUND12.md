# Round 12 (27 Sep 2026): redraw the remaining figures in the numfig style

Read these first, in order:

1. `tools/ROUND10.md`: how agents work (skills, the site's rules, own files, own build
   folder, no commits, no publishing).
2. `tools/ROUND11.md`: the professor's rule "the reader grasps it at once", the crimson
   palette, and Computer Modern everywhere.
3. `tools/numfig/README.md`: the figure contract. It covers the engine API, the timing
   budget, stills, fragments, and `.check.txt`.

Then look at two finished examples, their generators and their pages:

- `tools/numfig/shm_ndt.py` → `content/anim/nf-shm-ndt.html`
- `tools/numfig/sp_io.py` → `content/anim/nf-sp-io.html`

## What the client asked

The client wants every drawing on the site in "our animation style": the figure family
of the waves, signal processing, machine learning and SHM guides. That means:

- **Numerically correct.** Every curve, field, signal and position is computed from a real
  model in Python, and the `.check.txt` shows the checks.
- **LaTeX look.** TikZ/pgfplots precision, Computer Modern type (the engine's text() and
  math() only; never ctx.font), and the palette `C.*`.
- **Motion that explains.** Use manim-like choreography with exact positions: seg() for
  strokes drawing themselves, settle() for things that arrive.
- **"Overlap olmayan mükemmel stil".** Nothing may overlap: no label on a label, no line
  through a label, no arrow through data. The client caught an arrow crossing the live
  coefficients in signal processing Figure 2 and asked for it to be fixed.

## Binding checks for every figure you make

1. **His words.** The caption is his text and stays as it is. Your figure must show what
   the caption says, in its order and with its panel letters. The words inside his
   picture (labels, titles) are his too: keep them verbatim. Setting math in math() is
   fine.
2. **Overlap check.** `python -c "import sys; sys.path.insert(0,'tools/numfig'); import
   common; print(common.overlaps('<name>', [0.3, 0.8, 1.4, <mid-motion times>]))"`
   - `labels` must be empty at every moment you test. That includes the poster, still
     frames, and moments where the motion is busiest.
   - `crossings` must be empty, or each remaining one must be a label deliberately drawn
     on a knockout (a white box drawn after the stroke). Justify each in `.check.txt`.
   - The PNGs with the collisions outlined are written to the temp directory. Look at them.
3. **Look.** Screenshot the document page at 1440×900 and the figure alone at 672 wide.
   Compare side by side with his original picture, which you can see in the built page or
   in `build/ricos/<slug>/`. Iterate until it is better than his in every respect and
   says the same thing.
4. **Wiring.**
   - Your own fragment `content/anim/anim.<you>.json` maps `{doc slug: {picture stem:
     "nf-<you>-<name>.html"}}`. A picture named twice anywhere stops the build.
   - Find each picture's stem in `build/ricos/<slug>/part-01.json` or in the built page's
     `<img src=".../<stem>.webp">`.
   - Build with `python site/build.py --strict --no-word --out build/r12-<you>/dist`.
5. **Tests.** Write a new `tests/test_<you>_figures.py`. It checks:
   - each page exists, uses the engine, has CMU and Figure Math, and has no other font;
   - the fragment maps the right pictures;
   - the overlap check passes, if the test can run Playwright; otherwise record the
     overlap results in `.check.txt`.

## Ownership (only touch your own files)

- **photons**:
  - `tools/numfig/ph_*.py`, `content/anim/nf-ph-*`, `content/anim/anim.photons.json`;
  - `tests/test_photons_figures.py`.
- **prob**:
  - `tools/numfig/pr_*.py`, `content/anim/nf-pr-*`, `tests/test_pr_figures.py`;
  - `tools/bp_art.py` and `content/bigpicture/` (the Big Picture card pictures).
- **shmdocs**:
  - `tools/numfig/sd_*.py`, `content/anim/nf-sd-*`, `content/anim/anim.shmdocs.json`;
  - `tests/test_shmdocs_figures.py`.
- **sound**:
  - `tools/numfig/snd_*.py`, `content/anim/nf-snd-*`, `content/anim/anim.sound.json`;
  - `tests/test_sound_figures.py`.
- **controller**: the engine, `common.py`, every existing generator and nf page,
  `anim.json`, `site/`, and all other tests.
  - If you need an engine feature, say so in your report; do not edit the engine.
  - You may import existing model code (for example `shm_fdtd.py`, `guided_ut.py`,
    `bulk_ut.py`) without editing it.

The controller is regenerating the existing figures and running the overlap check on
them while you work.

Your final message: at most 150 words. Cover what you made, the files, the overlap
results, and anything that needs a decision.
