# Math review: Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation

Read in full: all 139 text nodes of `build/ricos/<slug>/part-01.json`. That covers the title
block, the intro, the "fun table" (11 rows: category, figure label and explanation cells),
the conceptual-schematics note, both disclaimers, every body paragraph, the Figure 1 to 13
captions, the callout, Table 1 (6 rows) and the book list.

The text is prose. It names its quantities in words (wavelength, wavenumber, phase
velocity), not symbols. None of the figure text is page text:

- Figures 1 to 7 and 11 to 13, and the table's pictures, are animated figures, each in its
  own frame (`anim/nf-*.html`).
- Figures 8 to 10 and the book picture are raster images.

## Set as math (1 entry, 4 places)

| His text | TeX | Where |
|---|---|---|
| `N` in "the Nth" (4) | `N` | Periodically supported beams, paragraph 2: "the Nth propagation zone" (2), "the Nth resonance frequency" (2) |

`N` is the index of the zone and the mode. Only the letter becomes math. The ordinal ending
"th" stays text, as LaTeX writes `$N$th`. The entry's context is `the ` before and `th `
after, and it matches exactly these four places.

Rendering was checked on `build/r13-math-waves/dist`, at 1440×900, at 390×844 and with
`data-theme="dark"`. After mathinfra added TeX's italic correction, the N no longer touches
"th", and the result matches lualatex with Latin Modern Math.

## His one equation is a picture, not text

`image16.png` (484×38) is Word's equation editor output: u(x, y, z, t) = U(y, z) e^(i(kx − ωt)).
He placed it twice:

- inline in the SAFE paragraph ("an assumed harmonic wave term of the form [picture].
  Substituting"). This is ricos `IMAGE n123`, joined into `n122` and `n124`;
- inline in the Figure 5 caption ("through the harmonic term [picture]."). This is
  `IMAGE n128`, inserted at offset 414.

The page shows it as `<img class="eq">`, with alt text from `site/build.py` `ALT`. It is a
raster in Word's equation font, not Latin Modern, and a text find cannot reach it.

**Needs a decision (mathinfra or the controller).** It needs a picture-to-TeX hook, for
example in `preview._in_line()`, keyed by the picture's name. I propose this TeX:

    u(x, y, z, t) = U(y, z)\, e^{i(kx - \omega t)}

The `\,` keeps the gap his picture shows before `e`. His `e` is italic, so it stays `e`.
`python site/mathtex.py tex` sets it without error.

## Left as text, and why

- Quantities with units, not part of a formula: 10 to 20 Hz, 1 kHz, 1 and 5 Hz, 1.2 and 5.7 Hz,
  1.3, 1.45, 5.2 and 5.92 Hz, 4.6 and 21.3 Hz, 1.23, 4.95, 5.8 and 22.90 Hz, 25 kHz, 4 or
  5 kHz, 100 kHz, 2 to 3 kHz, 20 kHz, 0 Hz.
- Figure and panel labels: "Figure 2 (b)", "(a)" to "(g)", "Table 1".
- Enumerators and labels: "(i)" to "(iv)", "span #1, #2, and #3", "Disclaimer #1".
- Ordinals: "4th modal dynamic response", "26th floor", "5th floor".
- Names: "A scan", "B scan", "C scan" (scan types, not variables), SHM, NDT, SAFE, FEM, RLC,
  M.Sc., Ph.D.
- The citation "Acta Mech 235, 1453–1469 (2024)" and its DOI.
- Words for quantities: half wavelength, wavenumber, phase and group velocity,
  second-order models, three and two dimensional.

## Split formulas

None. The only formula outside the pictures is the one above, and it is a picture.

## Things in his mathematics that look wrong (not fixed)

1. **Two-span example (a).** His text gives the uncoupled spans as "around 1 and 5 Hz"
   and "around 1.2 and 5.7 Hz", and the coupled beam as "1.3, 1.45, 5.2, and 5.92 Hz".
   - Joining the spans over the shared pin adds one constraint (slope continuity) or one
     rotational spring. Either way, each coupled frequency lies between consecutive
     uncoupled ones (Rayleigh interlacing). So the coupled fundamental must lie between
     1 and 1.2 Hz, but his is 1.3 Hz.
   - My Euler-Bernoulli FE check of a fully continuous girder with span fundamentals
     1 and 1.2 Hz gives 1.08, 1.74, 4.27 and 5.68 Hz.
   - He does say these are "approximate frequency values from experience rather than an
     actual computation".
2. **The simply supported ratio.** A uniform simply supported span has f₂ = 4f₁ (n²). His
   uncoupled pairs give 5 (1 to 5), 4.75 (1.2 to 5.7), 5 (1 to 5) and 4.63 (4.6 to 21.3).
   His coupled values do keep 4:1 (1.3 to 5.2, 1.45 to 5.92, 1.23 to 4.95, 5.8 to 22.90).
   `tools/numfig/multispan.py` found the same thing and fits Figure 7 to his coupled values.
3. **Example (b): the four frequencies are not consecutive modes.** "1.23, 4.95, 5.8, and
   22.90 Hz" skips the long span's third and fourth modes, which lie between 5.8 and
   22.90 Hz (10.87 and 19.28 Hz in the site's model). So 22.90 Hz is the sixth mode. The
   next paragraph ("closer to one of its higher order modes") shows he knows this, but
   "each of the four coupled mode shapes" reads as the first four.
4. **Minor, "the eigenvalues, which are the resonance frequencies".** For Kφ = ω²Mφ the
   eigenvalues are ω², the squared circular natural frequencies. The frequencies are
   f = ω/2π.
5. **Minor, "the group velocity, which is the local slope of the dispersion curve".** This
   is true of the ω–k curve (c_g = dω/dk). The curve he points back to, Figure 4 (a), plots
   phase velocity against frequency. Its slope is dc_p/df, and there
   c_g = c_p²/(c_p − f dc_p/df).
6. **Minor, physics wording.** "above 20 kHz, where wavelengths shrink down to the
   millimeter scale". At 20 kHz, steel wavelengths are about 0.3 m (longitudinal,
   5.9 km/s) and 0.16 m (shear). Millimetre wavelengths need MHz: 5.9 mm at 1 MHz.

The rest checks out:

- Mead's bounds on the propagation zones: pinned-pinned and fixed-fixed spans.
- N frequencies per zone for an N-span beam.
- Standing waves at L = nλ/2.
- Guided modes starting at 0 Hz.
- The SAFE term's form.
