# Math review: Understanding Sound Classification, Localization and Tracking and Similarity to NDT

Read in full: all 29 text nodes of `build/ricos/sound-detection-and-tracking/part-01.json`.
That covers the title block, the three stages, the three figure captions, both "Other
Components" items, "Wrapping Up", the three closing paragraphs and the five sources. The three
figures are canvas animations (`anim/nf-snd-array.html`, `nf-snd-kalman.html`,
`nf-snd-denoise.html`), so none of their text is page text.

## Set as math (1 entry, 1 place)

| His text | TeX | Where |
|---|---|---|
| `m` in "traveled to sensor m." | `m` | Stage 2, "Figure 1 (a) shows how a pair of linear array sensors ..." |

`m` is the sensor's symbol. Figure 1 (a) labels the pair "m" and "n", and its aria-label says
"a pair of sensors m and n". The entry carries context (`before` "additional distance traveled
to sensor ", `after` ". However"), because a bare `m` occurs inside hundreds of words.

## Left as text, and why

- "180-degree symmetry", "two 180-degree sides", "a 360-degree plane": angles written as words
  with their unit. None is part of a formula.
- "roughly 6 dB for every doubling of distance": a quantity with its unit, stated as a rule of
  thumb. There is no formula to set.
- Acronyms and method names in prose: ML, MFCCs, AoA, MUSIC, VAE, KL-divergence, STFT, SHM, NDT,
  FDD, SSI, ERA.
- Enumerators, figure and citation numbers: "1.", "2.", "3.", "Figure 1 (a)" to "Figure 3",
  "14(2), 740", "(pp. 82 to 94)".

## Symbols that live only in the figures (not page text, so outside the map)

These are drawn on the figures' canvases by `tools/numfig`, already in Computer Modern (CMU Serif
with Figure Math), from TeX strings in each figure's data:

- Figure 1 (`nf-snd-array.html`): the sensor positions `(\rho_n, \beta_n)`, `(\rho_m, \beta_m)`,
  `(\rho, \beta_0)` and `(\rho, \beta_2)`, the angles `\theta` and `\gamma`, the extra distances
  `d_{n,m}`, `d_{0,2}` and `\Delta d`, and the parameter line (`c = 343 m/s`,
  `\rho_n = 6 cm`, ...).
- Figure 2 (`nf-snd-kalman.html`): `P_{n|n-1}`, `P_{n|n}`, `R_n`, `K_n`, the step `n`, and the
  parameter line `K_n = P_{n|n-1}/(P_{n|n-1} + R_n)`.

The canvases' aria-labels name "sensors m and n" and "the Kalman gain K" as plain text. An
aria-label cannot carry MathML.

## Split formulas

None. His only symbol in the page text sits inside one text node.

## How it renders

- **Checks.** `python site/mathtex.py check` passes: 1 entry, 1 place. The strict build to
  `build/r13-math-shm/dist` exits 0.
- **The page.** On `doc/sound-detection-and-tracking.html`, "sensor *m*." is set in Site Math
  italic, on the baseline at the text's x-height. It was shot at 1440×900, at 390×844 and in the
  dark palette.

## Things in his mathematics that look wrong (not fixed)

None found. His quantitative statements hold:

- sound pressure from a point source in free field falls about 6 dB per doubling of distance;
- a linear pair cannot tell the two 180-degree sides apart;
- microphone spacing that is large against the wavelength aliases spatially;
- the fused Kalman estimate has a smaller variance than either input;
- the gain is small when the measurement is noisy relative to the model.
