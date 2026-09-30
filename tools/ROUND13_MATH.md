# Round 13 (28 Sep 2026): every formula and every symbol set as LaTeX would set it

Read `tools/ROUND10.md` first: it has the agent rules (own files, own build folder, no
commits, no publishing, the site's rules). Then read this file.

## The request

The client quoted a formula from the machine learning guide:

> z = w1*x1 + w2*x2 + w3*x3 + bias → output = activation(z)

and wrote: "Bu gibi yerlerde mesela latex ile yazılması lazım böyle şeylerin bir harfin bile.
... bu ve diğer kısımları detaylıca incele". In English: in places like this, such things must
be typeset with LaTeX, even a single letter; examine this and the other parts in detail.

So every mathematical expression in the professor's documents and blog posts must be set as
LaTeX sets it. That covers:

- whole equations and inline formulas;
- a variable named alone in prose ("where x is the input");
- indices, Greek letters, operators, arrows, functions, and a number that belongs to a formula.

Two things stay text: prose, and quantities with units that are not part of a formula
("10 kHz", "3 floors").

## How it works (the pipeline agent "mathinfra" builds it; the schema binds everyone)

Each document has a curated map, `content/math/<slug>.json`. A blog post uses
`content/math/blog-<post slug>.json`.

```json
{"entries": [
  {"find": "z = w1*x1 + w2*x2 + w3*x3 + bias → output = activation(z)",
   "tex": "z = w_1 x_1 + w_2 x_2 + w_3 x_3 + \\text{bias} \\;\\rightarrow\\; \\text{output} = \\text{activation}(z)",
   "count": 1},
  {"find": "x", "before": "where ", "after": " is the input", "tex": "x", "count": 1}
]}
```

The keys:

- **`find`** is the exact text as it stands in ONE text node of the document. It is the node's
  `textData.text` in `build/ricos/<slug>/part-01.json`, before any HTML escaping. It is his
  words, character for character, including his `*`, his `->` or `→`, his spaces and his
  typos.
- **`before` / `after`** are optional exact context strings that must surround `find` in the
  same node. Use them for short or ambiguous finds, such as single letters.
- **`count`** is how many times the (context-qualified) find occurs in the document. The build
  fails if the actual count differs, so no entry is ever silently skipped or applied twice.
- **`tex`** is the LaTeX for exactly what `find` covers, typeset the way the author would have
  written it in LaTeX. `before` and `after` are not included in it.
- **`display`** (optional, default false): true for a formula that stands alone in its
  paragraph as an equation. It is centred and set in display style.
- **`why`** (optional): a short note for anything a reviewer might question.

The build replaces each find with MathML converted from `tex`. The MathML keeps his original
text as `alttext` (for accessibility and provenance). It is set in Latin Modern Math, the
LaTeX font the site bundles.

## LaTeX style rules (binding, so all documents read as one hand)

- **Variables** are italic single letters, which is LaTeX's default: `x`, `w_1`, `\theta`.
- **Indices go down**: `w1` → `w_1`, `x_t`, `y_{t-1}`, `P_{n|n-1}`. Powers go up: `x^2`,
  `e^{-t}`.
- **Multi-letter names are upright.**
  - Words go in `\text{...}` (`\text{bias}`, `\text{output}`, `\text{Loss}`).
  - Standard functions use their commands: `\sin`, `\cos`, `\exp`, `\log`, `\max`,
    `\min`, `\arg\max`.
  - Named functions and acronyms use `\operatorname{...}` (`\operatorname{ReLU}`,
    `\operatorname{softmax}`, `\operatorname{MSE}`).
- **His `*` for multiplication** becomes juxtaposition between symbols (`w_1 x_1`). Between
  numbers, or where juxtaposition would be ambiguous, it becomes `\cdot`. `*` meaning
  convolution becomes `\ast`.
- **His ASCII symbols become their LaTeX symbols**:
  - `->` → `\rightarrow`;
  - `<=` → `\leq`, `>=` → `\geq`;
  - `+-` → `\pm`;
  - `~` → `\approx` or `\sim` by meaning.
- **His `/` fraction** stays inline as `a/b` in running text. Use `\frac` only in a display
  equation.
- **Keep his structure.** Never add or drop terms, never rename his symbols, never "correct"
  his mathematics. If you see an error, list it for the controller; do not fix it. Only the
  typesetting changes.
- **Units inside a formula** are upright with a thin space: `9.81\,\mathrm{m/s^2}`.
- **Leave alone** anything that is not mathematics in his sentence: version numbers, dates,
  figure numbers, section numbers, code identifiers in a code context (a Python name stays
  code), and "3D" or "2D" as words.

## Who owns what

- **mathinfra**:
  - a new module `site/mathtex.py` (TeX → MathML, the map loader and matcher, validation);
  - the hook in `site/preview.py`'s `text_node()`, replacing the regex heuristics
    (`inline_math`, `INLINE_EQ`, `CONV_EQ`). Their current output must be reproduced by map
    entries in the SP guide's map; coordinate through the controller;
  - the math CSS in `site/parts/docs.py` (`math.im` and a display rule);
  - the font `content/fonts-cmu/latinmodern-math*.woff2`, copied by the existing font loop;
  - `tests/test_mathtex.py`;
  - the blog pipeline hook if blog posts go through another renderer (`site/parts/blog.py`).
- **math-ml**: `content/math/machine-learning-the-complete-picture-and-guide-5.json`.
- **math-sp**: `content/math/signal-processing-system-identification-and-optimization.json`.
- **math-waves**:
  - `content/math/dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation.json`;
  - `content/math/from-bridges-to-photons.json`.
- **math-shm**:
  - `content/math/understanding-shm-and-ndt.json`;
  - `content/math/brochure-shm-and-ndt-2-pages.json`;
  - `content/math/sound-detection-and-tracking.json`;
  - `content/math/blog-*.json`.
- **The curators** (math-ml, math-sp, math-waves, math-shm) read the whole document,
  paragraph by paragraph, including:
  - headings, captions, table cells, callouts, list items and footnotes;
  - text inside figures only where it is page text, not canvas.

  Each curator also writes a short `content/math/<slug>.review.md`: what was set, what was
  deliberately left as text and why, and any suspected errors in his mathematics.

## Verification (everyone)

- Build to your own folder: `python site/build.py --strict --no-word --out build/r13-<you>/dist`.
- The build fails on any entry whose find does not match exactly `count` times.
- Screenshot every changed paragraph at 1440×900, and a sample at 390×844 and in dark mode.
  Check three things:
  - the math sits on the text's baseline at a matching size;
  - it has no clipped glyphs;
  - it looks like LaTeX.
- Run `python -m pytest -q`.
- The curators can start before mathinfra finishes: validate finds and counts with a small
  script against `build/ricos/<slug>/part-01.json`, then render once `site/mathtex.py`
  exists.

Final message: at most 150 words.
