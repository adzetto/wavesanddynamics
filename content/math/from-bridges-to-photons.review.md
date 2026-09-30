# Math review: From Bridges to Photons

Read in full: all 40 text nodes of `build/ricos/<slug>/part-01.json`. That covers the title,
the subtitle, 4 headings, 5 paragraphs, the Figure 1 caption and the closing callout.
Figure 1 is a raster picture, so its labels are not page text.

## Set as math (10 entries, 10 places; 7 of them `joined`)

| His text | TeX | Where |
|---|---|---|
| `sinc²` | `\operatorname{sinc}^2` | Figure 1 caption, "(sinc²) envelopes" |
| `V² + D² ≤ 1` (joined) | `V^2 + D^2 \leq 1` | "Why observation removes the fringes": the duality relation |
| `V`, `D` (joined) | `V`, `D` | same sentence: "where V is the fringe visibility and D measures…" |
| `P = P_A + P_B` (joined) | `P = P_{\mathrm{A}} + P_{\mathrm{B}}` | "Why not two bright lines?": the incoherent sum |
| `λL/a` | `\lambda L/a` | same paragraph: the single-slit width |
| `a`, `L`, `d` (joined) | `a`, `L`, `d` | same paragraph: "where a is the slit width and L is the distance…", "the slit separation d" |
| `ad/(λL) > 1` | `ad/(\lambda L) > 1` | same paragraph: the near-field condition |

Choices a reviewer might question:

- sinc has no LaTeX command, so it is `\operatorname{sinc}`. It is squared the way `\sin^2`
  is.
- In Word, `λL/a` and `ad/(λL) > 1` are each one wholly italic run. In LaTeX only the letters
  are italic; the slash, the brackets, `>` and `1` are upright. His slash stays inline,
  because both sit in running text.
- **The subscripts of `P_A` and `P_B` are upright.** A and B name the two slits, and he
  set them upright everywhere:
  - in his Word subscript runs, which carry no italic;
  - in the prose: "slits A and B", the detector's "A" and "B" states;
  - in Figure 1's labels.

  So they are labels, and they are set upright, as ISO sets a label subscript. If the
  controller prefers LaTeX's default, the TeX is `P = P_A + P_B`.

Rendering was checked on `build/r13-math-waves/dist`, at 1440×900, at 390×844 and with
`data-theme="dark"`, against lualatex with Latin Modern Math. Two defects came from the
renderer, not the map, and mathinfra fixed both:

- The missing italic correction made the 2 of V² run into the V, and made "V is" read
  "Vis".
- A comma or bracket could be split from its formula at a line end, as in
  "ad/(λL) > 1 | , where" at 390 px.

## Split formulas, set with mathinfra's `"joined": true`

Word split these formulas into runs: an italic run for each letter, and plain runs for the
rest. `site/mathtex.py` now matches a `joined` entry in the paragraph's runs joined
together. It replaces the whole stretch with one formula and drops his italic. The node
structure is given as `[run index] decorations 'text'` within the paragraph.

**1. The duality relation, `n9`.** The entry covers runs [1] to [4].

    [1] ITALIC 'V'
    [2]        '² + '
    [3] ITALIC 'D'
    [4]        '² ≤ 1, where '     (the formula ends at '1')

Each ² is a Word superscript run. The converter wrote it as U+00B2.

**2. The variables named after it, `n9`.** Each entry covers one run.

    [5] ITALIC 'V'    between [4] '…, where ' and [6] ' is the fringe visibility and '
    [7] ITALIC 'D'    between [6] and [8] ' measures how reliably the path can be identified. …'

Each is a one-letter run with its context in its neighbours. A plain find `V` could not
tell run [5] from run [1].

**3. The incoherent sum, `n11`.** The entry covers runs [1] to [7].

    [1] ITALIC 'P'
    [2]        ' = '
    [3] ITALIC 'P'
    [4]        '_A'
    [5]        ' + '
    [6] ITALIC 'P'
    [7]        '_B'

`_A` and `_B` are Word subscript runs. `tools/ricos/glyphs.script` writes them with `_`
because Unicode has no subscript capital A.

**4. The variables named in the same paragraph, `n11`.** Each entry covers one run.

    [11] ITALIC 'a'   between [10] ', where ' and [12] ' is the slit width and '
    [13] ITALIC 'L'   between [12] and [14] ' is the distance to the screen. …'
    [15] ITALIC 'd'   between [14] '… than the slit separation ' and [16] ', so the two envelopes …'

"a" and "d" occur inside almost every word, and "L" occurs inside the two plain formulas,
so only the joined context finds these three.

I checked all seven with `python site/mathtex.py check` and with my own script, which
reports the runs each match covers: each covers exactly the runs listed above. If the
controller drops `joined`, these seven entries must go. The rest of the map stands on its
own.

## Left as text, and why

- "slits A and B" and the detector's "A" and "B" states: names of the slits, not
  variables. They are upright in Figure 1 and in his subscripts.
- Figure references: "Figure 1(a)", "Figure 1(b)".
- Words: double-slit, single-slit, far-field, near field, squared amplitude, uncertainty
  principle, "half the slit separation".

## Things in his mathematics that look wrong (not fixed)

None. I checked each result:

- `V² + D² ≤ 1` is Englert's duality relation (PRL 77, 2154, 1996), with V the fringe
  visibility and D the distinguishability.
- `P = P_A + P_B` is the incoherent sum for distinguishable paths, with no interference
  term.
- `λL/a` is the half-width of the single-slit central lobe on a screen at distance L. The
  full lobe is 2λL/a, and "roughly" covers the difference.
- `ad/(λL) > 1` is `λL/a < d` rearranged: the single-slit width is smaller than the slit
  separation. It is consistent with his own definitions of a, d and L.
- sinc² is the Fraunhofer single-slit intensity.
