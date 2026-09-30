# Math review: the blog

## Where his mathematics is

- **The post bodies have none.** The Ricos bodies (`content/blog/<slug>/post.json`, 33 text
  nodes in eight posts) hold no formula and no symbol. So there is no
  `content/math/blog-<slug>.json` map.
- **It is all in the typed screenshots.** Every piece of mathematics in the blog sits in
  `content/blog/<slug>/text/*.html`, our transcription of his screenshots, which `post_page()`
  splices in place of each picture.
- **Set at the source.** Following the controller's ruling (28 Sep), each piece is now set there
  as a TeX element: `<tex>…</tex>` inline and `<tex display>…</tex>` for a numbered equation. The
  `<div class="eq">` and its `(n)` stay around a display equation. Mathinfra's hook turns each
  element into MathML.
- **Changed:** 169 `<tex>` elements in 11 files of five posts:

  | Post | `<tex>` elements | Files | Pseudo-math | Hand-written MathML |
  |---|---|---|---|---|
  | Impulsive noise detection (SOM) | 102 | 4 | 38 | 64 |
  | Stationary wavelet package transformation | 61 | 3 | 48 | 13 |
  | Multi-objective optimization | 3 | 1 | 3 | 0 |
  | Laser Doppler vibrometer | 2 | 2 | 2 | 0 |
  | Impulse (outlier) detection methods | 1 | 1 | 1 | 0 |

  The pseudo-math was `<i>`, `<sub>` and `<sup>`, or bare letters. The hand-written MathML was
  in STIX. The table at the end lists every replacement.
- **Nothing to set:** the two library posts (file names only) and the wind turbine post (a topic
  list and a download).

## What was read

- **Every typed file, whole.** All 33 typed files: every paragraph, caption, list item, equation
  and reference.
- **Against his originals.** Each file carrying mathematics was checked against his screenshot
  (the PNGs in each post folder): four for the SOM post, three for SWPT, two for multi-objective,
  two for the laser Doppler post and one for the impulse methods post. The transcription matches
  his screenshots in every formula, so everything listed below as looking wrong is his.
- **Wording unchanged.** Only the markup of the mathematics changed. The script
  (`convert.py`, session scratchpad) applied exact replacements with their counts and refused any
  count that differed. A scan afterwards found no `<math>`, no italic single letter, no stray
  `<sub>` or `<sup>` and no bare Greek letter left outside `<tex>`. The two ordinals
  "4<sup>th</sup>" stay text.

## Choices a reviewer might question

- **Letters he set upright are italic now.** In Word he typed some symbols upright. They are set
  italic as LaTeX sets a variable:
  - SOM post: `w_y` beside his italic `w_j`, `η` and `η_0`, the `w_j` of Eq. (22) and
    "(e.g., w<sub>j</sub>)", and "x and y coordinates";
  - SWPT post: the operator `Z`, italic like his `H`, `G` and `D_0`.
- **Angle brackets.** His input space `u^l =< u^l_x, u^l_y >` uses less-than and greater-than
  signs as brackets. It is `u^l = \langle u_x^l, u_y^l \rangle`.
- **Eq. (22) (SOM).** His Word equation has both an `x` under "min" and a lowered
  `x∈[0,N_l]` after it. It is one limit, `\arg\min_{x \in [0, N_l]}`. The alternative, keeping
  his double subscript, is `\arg\min_{x}{}_{x \in [0, N_l]}`.
- **`MD`.** His name for the mean neighbour distance is `\operatorname{MD}_j^l`, upright as the
  rules set an acronym. He had it italic.
- **Bare symbols in prose are now math:**
  - "the point C" (multi-objective), which names point C of Figure 1 (a);
  - "(sin function)" is `\sin` (laser Doppler); "triangle function" stays words;
  - "var[doppler phase]" is `\operatorname{var}[\text{doppler phase}]`, his notation from his
    figure beside it;
  - "-/+ 2π" is `\mp 2\pi` (impulse methods).
- **Word artifacts taken out:**
  - SOM Eq. (1) and (2): his "1,2, …., N_w" has a stray period after the ellipsis. It is
    `1, 2, \ldots, N_w`.
  - SWPT: in "ϵ<sub>J−1,</sub>" the comma sat inside the subscript. It is `\epsilon_{J-1},`.
  - SWPT Eq. (3): his "=" sits in the subscript ("g<sub>n=</sub>"). It is `g_n = …`.
- **`D_o` kept.** In SWPT his decimation operator is `D_o` (letter o) in Eq. (5) and its
  sentence, and `D_0` (zero) everywhere else. Both are kept as he wrote them (see the next
  section).
- **Display sums.** `\sum_{n}` in a display equation puts `n` under the sign, as LaTeX does.
  Word put it beside.
- **Plain parentheses in SOM Eq. (2).** Word enlarged the outer pair of
  `(u_s(k) - w_y(k))` a little. `\bigl( \bigr)` was tried: Chrome drew that pair at normal
  height with gaps inside, so the pair is plain `( )`, as most LaTeX authors write it.
- **Left as text** (next section): numbers in prose, such as "8 and 62", "9 and 63",
  "70 by 70", "downsampled by 2" and "a sequence of 0’s and 1’s".

## Left as text, and why

- Ordinals, counts and sizes in prose: "4<sup>th</sup> order", "9 neurons", "2-D",
  "two-dimensional", "70 by 70", "by 4 points", "8 and 62", "9 and 63", "by 2",
  "0’s and 1’s", "4 data points", "2 objective functions".
- References to equations, figures and papers: "Eq.2" to "Eq. 7", "Figure 1 (a)", "[1]",
  "[7,8]", "(i)" to "(iv)", "1)" to "6)", and years, volumes and pages in the references.
- Acronyms and method names: SOM, MSOM, ANN, IN, LDV, CSLDV, DWT, SWT, SWPT, DWPT, WPT,
  "ϵDWT" (only the `\epsilon` is math), AC’s, DC’s, SPEA2, NSGA-II, ROM, ROAD, BDND, KF, EM,
  MCMC, PCA, "L-shape".
- "the square root of 2" (laser Doppler): his words, not a symbol, and his words stay.
- The two library posts: file names, a code-like context.
- The alt texts of the cut-out figures ("w1 to w9", "u^s", "d_s = 4λz / (π d_l)"). An alt
  attribute cannot hold MathML, so these stay plain text.
- The mathematics inside the cut-out figures themselves (`fig*.png`): raster pictures, not page
  text.

## Split formulas

Under the ruling these were set whole at the source. His formatting, or the transcription, had
split them across HTML nodes:

- `<i>K</i>+1`;
- `τ<sub>1</sub>` and `τ<sub>2</sub>`;
- `Δ<sup>4</sup><i>l</i>` and `Δ<sup>4</sup><i>s</i>`;
- `<i>l</i>(<i>x</i>)` and `w<sub><i>j</i></sub>`;
- `<i>F</i><sub>1</sub>` and `<i>F</i><sub>2</sub>`;
- `{<i>h<sub>n</sub></i>}` and the sequence `{…, s₋₂, …, s₂, …}`;
- `s₀, s₁, …, s_{N−1}`, `N = 2^J` and `ϵ_{J−1}, ϵ_{J−2}, …, ϵ₀`;
- `(Zs)_{2j} = s_j` and `(Zs)_{2j+1} = 0`;
- `(D₀Hs, D₀Gs)`, `2^r j − N` and `a⁰ = s`;
- `-/+ 2<i>π</i>`.

Each is now one `<tex>` element. The table below gives the exact old markup.

## Things in his mathematics that look wrong (not fixed)

**Impulsive Noise Detection with Semi-organizing Map Neural Networks**

1. **Eq. (2).** The bracket is `(u_s(k) - w_y(k))`. Kohonen's rule, as in Haykin [2] which he
   cites, moves each neuron toward the sample: `(u_s(k) - w_j(k))`. With `w_y`, every neuron in
   the neighbourhood moves along the winner's error vector instead of toward the sample.
2. **Eq. (22) assigns in the wrong direction.** The text says each point is assigned to its
   closest neuron. That is an arg min over the neurons `j`, for each point `x`. The equation
   takes the arg min over the points `x`, for each neuron `j`. It also measures from the scalar
   signal value `l(x)`, while the neurons live in the 2-D input space `u^l` the SOM was trained
   on.
3. **Eq. (1).** The arg min returns the index `y`, but the left side is the neuron `w_y(k)`.
   Steps 2 and 3 write the iteration as `n` (`u_s(n)`, `w_y(n)`) where the equations use `k`.
   Step 1 says `w_i` where everything else says `w_j`.
4. **Eq. (5).** It defines the width `ε(k)` with initial value `σ_0` (Haykin's `σ`), a second
   name for the same quantity.
5. **Squared versus unsquared.** The text calls `d_{j,y}^2` "the distance" and `ε^2(k)` "the
   width". Those are the squared distance and the squared width. The same sentence reads "the
   distance between and w_j(k)’s and w_y(k)", with a word missing.
6. **Off by one: "robust against artificial peaks with a length of K+1 [3]".** A moving median
   over `2K+1` samples removes runs of at most `K` outliers. With `K+1` outliers in the window,
   the median is itself an outlier. His choice of `K = 8` and `62` for peaks up to 9 and 63
   samples long rests on this. Windows of 17 and 125 cover runs of 8 and 62.
7. **Figure 2 caption.** It writes `\bar{m}_K^s` and `\bar{m}_K^{\Delta^4 s}`, where the text
   and the figure's legend have the window `2K+1` (17 and 125).
8. **Figure 3 (d), in the picture.** The axis reads `MD_i^s` and the legend `MD_j^s`.

**Stationary Wavelet Package Transformation**

9. **Details computed from details.** Eq. (6) has `d^{j+1} = D_0 G d^j` and Eq. (9) has
   `d^{j+1} = G^{[j]} d^j`. In the DWT and the SWT (Nason and Silverman, whom he cites) the
   details at level `j+1` come from the approximation: `D_0 G a^j` and `G^{[j]} a^j`. For a
   packet transform both `a^j` and `d^j` are split by both filters, which the pair of equations
   does not show either.
10. **"the remaining 2^r j − N number of coefficients" is not a count.** It depends on `j`.
    `H^{[r]} = Z^r h` puts `2^r - 1` zeros between consecutive coefficients of `h`. With `L` taps,
    `(L-1)(2^r-1)` of its coefficients are zero.
11. **`H` names two filters.** In the first paragraph `H` is the high-pass filter, with `L` the
    low-pass, as in Figure 1 (a). From the second paragraph on, `H` is the low-pass filter and
    `G` the high-pass.
12. **`D_o` and `D_0`.** Eq. (5) and its sentence write `D_o` (letter o). Eqs. (6) and (8) and
    the text write `D_0`. It is the same operator.
13. **Words that contradict the mathematics:**
    - "leading to shift-invariance" in the first paragraph: aliasing causes shift *variance*,
      as his later paragraph says;
    - "deconvolving the signal with a low pass filter": filtering is convolution;
    - "the number of coefficients is reduced by 2": it is halved;
    - "AC’s and AD’s of SWT" before Eq. (9): AD’s is probably DC’s;
    - "DTW and WPT": DTW is probably DWT.

**Laser Doppler Vibrometer**

14. **His speckle figure** (a picture, not set) says "Z is the distance between LDV and
    surface" but writes lowercase `z` in `d_s = 4λz/(πd_l)`.

**Methods to use in impulse (outlier) detection**

15. **A stray "5".** "low-pass filtering of the signal 5 (computed by Hilbert transform)" has a
    "5" where a word or symbol seems lost (probably the signal's envelope). It is left as it
    stands.

No problem found in the multi-objective post: point C is the one nearest the origin when both
objectives are minimized.

## How it renders (checked 28 Sep, with mathinfra's hook)

- **The build.** `python site/build.py --strict --no-word --out build/r13-math-shm/dist` exits 0.
  The five posts carry 169 formulas, each `<math>`'s alttext its TeX, all in Site Math at 1.1
  times the text.
- **Screenshots.** Every block holding a formula was shot:
  - all 49 blocks (with the sound document's) at 1440×900 and again at 390×844;
  - 18 in the dark palette. The site ships light, so `data-theme="dark"` was forced for this.
- **Checks:**
  - the formulas sit on the text's baseline at the text's x-height;
  - no glyph is clipped;
  - the math keeps the ink colour in both palettes.
- **Phones.** A display formula wider than a 390px column now breaks between its parts (before
  "and", after a comma) and shrinks, through mathinfra's split: SOM Eq. (1), (2) and (22), and
  SWPT Eq. (6), (8) and (9).
  mathinfra's `.im-nb` keeps "w_j’s", "ϵDWT" and "2^r j’th" whole at a line's end.
- **Bold captions.** The math in the bold captions of SOM Figures 2 and 3 stays regular weight,
  as LaTeX sets math in a bold caption.

## For the controller and mathinfra

- **Superscripts crowd some italic capitals.** In `<msubsup>`, where a letter has both a
  subscript and a superscript, the superscript of an italic capital touches the letter:
  `C_j^{l(x)}` in SOM Eq. (22) and its sentence, and `D_0^r` in SWPT Eq. (8). TeX moves that
  superscript right by the letter's italic correction. The converter already does so for
  `<msup>` (`H^{[r]}`, `G^{[r]}`) but not yet for `<msubsup>`.
- **`\bigl` and `\bigr`** drew at normal height with gaps inside (tried in SOM Eq. (2), then
  dropped). Any map that uses `\big` should be looked at.
- **CSS.** `site/parts/blog.py` still sets `.typed math{font-family:"STIX Two Math",...}`.
  mathinfra's `.docpage math.im` outranks it, so it no longer applies to the posts, but it is
  dead weight.
- **A stale generator.** `content/blog/impulsive-noise-detection-with-semi-organizing-map-neural-networks/text/make.py`
  is the one-off script that first wrote four of these files. It still writes the old MathML,
  and running it again would undo this round. It should be deleted or never rerun. It is not
  mine to change.

## Every replacement

`n` is how many times the old fragment was replaced in that file. `(display)` marks a numbered
equation, now `<tex display>` inside its `<div class="eq">`. A `MathML` row shows the element's
text, tags stripped; the appendix gives each element whole.

### Impulsive Noise Detection with Semi-organizing Map Neural Networks

`content/blog/impulsive-noise-detection-with-semi-organizing-map-neural-networks/text/`


`ce0a40_c6d88c08e6974a70b241b0af94df6edc_mv2.html` (picture 1 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `w j` | `w_j` | 5 |
| MathML `N w` | `N_w` | 1 |
| MathML `w i` | `w_i` | 1 |
| MathML `u s ( n )` | `u_s(n)` | 1 |
| MathML `w y ( n )` | `w_y(n)` | 1 |
| MathML `w y ( k ) = arg min y ‖ u s − w y ‖ , y = 1 , 2 , … , N w` | `w_y(k) = \arg\min_{y} \lVert u_s - w_y \rVert, \quad y = 1, 2, \ldots, N_w` (display) | 1 |
| MathML `w j ( k + 1 ) = w j ( k ) + η ( k ) h j , y ( k ) ( u s ( k ) − w y ( k ) ) , j = 1 , 2 , … , N w` | `w_j(k+1) = w_j(k) + \eta(k) h_{j,y}(k) (u_s(k) - w_y(k)), \quad j = 1, 2, \ldots, N_w` (display) | 1 |
| MathML `η ( k ) = η 0 exp ( − k τ 1 )` | `\eta(k) = \eta_0 \exp\left(-\frac{k}{\tau_1}\right)` (display) | 1 |
| MathML `h j , y ( k ) = exp ( − d j , y 2 2 ε 2 ( k ) )` | `h_{j,y}(k) = \exp\left(-\frac{d_{j,y}^2}{2\varepsilon^2(k)}\right)` (display) | 1 |
| `<i>j</i>` | `j` | 1 |
| `x` | `x` | 1 |
| `y` | `y` | 1 |
| `<i>u</i>` | `u` | 1 |
| `<i>k</i>` | `k` | 2 |
| `<i>y</i>` | `y` | 1 |

`ce0a40_8b8d27bbd7a548cd8b208ad32f6d63e0_mv2.html` (picture 2 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `ε ( k ) = σ 0 exp ( − k τ 2 )` | `\varepsilon(k) = \sigma_0 \exp\left(-\frac{k}{\tau_2}\right)` (display) | 1 |
| MathML `η ( k )` | `\eta(k)` | 3 |
| MathML `h j , y ( k )` | `h_{j,y}(k)` | 4 |
| MathML `w j` | `w_j` | 4 |
| MathML `w y ( k )` | `w_y(k)` | 2 |
| MathML `d j , y 2` | `d_{j,y}^2` | 1 |
| MathML `w j ( k )` | `w_j(k)` | 1 |
| MathML `ε 2 ( k )` | `\varepsilon^2(k)` | 2 |
| MathML `ε ( k )` | `\varepsilon(k)` | 1 |
| MathML `h j , y ( k = 1 )` | `h_{j,y}(k=1)` | 1 |
| MathML `u l = < u x l , u y l >` | `u^l = \langle u_x^l, u_y^l \rangle` | 1 |
| MathML `u x l = l − m ‾ 2 K + 1 l` | `u_x^l = l - \bar{m}_{2K+1}^{l}` (display) | 1 |
| MathML `u y l = [ 0 0 Δ 4 l 0 0 ] − m ‾ 2 K + 1 Δ 4 l` | `u_y^l = [0\;0\;\Delta^4 l\;0\;0] - \bar{m}_{2K+1}^{\Delta^4 l}` (display) | 1 |
| MathML `m ‾ 2 K + 1 l` | `\bar{m}_{2K+1}^{l}` | 2 |
| MathML `m ‾ 2 K + 1 Δ 4 l` | `\bar{m}_{2K+1}^{\Delta^4 l}` | 2 |
| MathML `m ‾ 2 K + 1 s` | `\bar{m}_{2K+1}^{s}` | 1 |
| MathML `m ‾ 2 K + 1 Δ 4 s` | `\bar{m}_{2K+1}^{\Delta^4 s}` | 2 |
| MathML `s i f` | `s^{i_f}` | 1 |
| MathML `m ‾ 17 s` | `\bar{m}_{17}^{s}` | 1 |
| MathML `m ‾ 125 Δ 4 s` | `\bar{m}_{125}^{\Delta^4 s}` | 1 |
| `τ<sub>1</sub>` | `\tau_1` | 1 |
| `τ<sub>2</sub>` | `\tau_2` | 1 |
| `<i>n</i>` | `n` | 1 |
| `<i>l</i>` | `l` | 5 |
| `Δ<sup>4</sup><i>l</i>` | `\Delta^4 l` | 4 |
| `<i>K</i>` | `K` | 2 |
| `<i>K</i>+1` | `K+1` | 1 |
| `<i>u</i>` | `u` | 1 |
| `<i>s</i>` | `s` | 3 |
| `<i>u<sup>s</sup></i>` | `u^s` | 1 |
| `Δ<sup>4</sup><i>s</i>` | `\Delta^4 s` | 3 |

`ce0a40_23654ee25d644a86b2a963a57b955a07_mv2.html` (picture 3 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `u s` | `u^s` | 3 |
| MathML `m ‾ K s` | `\bar{m}_{K}^{s}` | 1 |
| MathML `m ‾ K Δ 4 s` | `\bar{m}_{K}^{\Delta^4 s}` | 1 |
| MathML `u l` | `u^l` | 3 |
| MathML `C j l ( x ) = arg min x x ∈ [ 0 , N l ] ‖ l ( x ) − w j ‖ , j = 1 , … , N w` | `C_j^{l(x)} = \arg\min_{x \in [0, N_l]} \lVert l(x) - w_j \rVert, \quad j = 1, \ldots, N_w` (display) | 1 |
| MathML `C j l ( x )` | `C_j^{l(x)}` | 1 |
| MathML `M D j l` | `\operatorname{MD}_j^{l}` | 2 |
| MathML `M D j s` | `\operatorname{MD}_j^{s}` | 2 |
| `s` | `s` | 1 |
| `<i>Δ</i><sup>4</sup><i>s</i>` | `\Delta^4 s` | 1 |
| `<i>l</i>` | `l` | 2 |
| `<i>l</i>(<i>x</i>)` | `l(x)` | 1 |
| `w<sub><i>j</i></sub>` | `w_j` | 1 |
| `<i>s</i>` | `s` | 1 |

`ce0a40_9f4df5e6e3884de195b911abd1ef0522_mv2.html` (picture 4 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `u s` | `u^s` | 4 |
| `<i>s</i>` | `s` | 1 |

### Stationary Wavelet Package Transformation

`content/blog/stationary-wavelet-package-transformation/text/`


`ce0a40_ebddb73eb53b42de8043e2ae2102f9b3_mv2.html` (picture 1 of 4)

| old | new TeX | n |
|---|---|---|
| `<i>A</i>` | `A` | 1 |
| `<i>D</i>` | `D` | 1 |
| `<i>L</i>` | `L` | 1 |
| `<i>H</i>` | `H` | 2 |
| `<i>G</i>` | `G` | 1 |
| `↓&#8201;2` | `\downarrow 2` | 1 |
| `{<i>h<sub>n</sub></i>}` | `\{h_n\}` | 1 |
| `{…, <i>s</i><sub>−2</sub>, <i>s</i><sub>−1</sub>, <i>s</i><sub>0</sub>, <i>s</i><sub>1</sub>, <i>s</i><sub>2</sub>, …}` | `\{\ldots, s_{-2}, s_{-1}, s_0, s_1, s_2, \ldots\}` | 1 |

`ce0a40_e6c3b5fca12e42688a2d56d6ec46d0fe_mv2.html` (picture 2 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `( H s ) k = ∑ n h n − k s n` | `(Hs)_k = \sum_{n} h_{n-k} s_n` (display) | 1 |
| MathML `∑ n h n 2 = 1` | `\sum_n h_n^2 = 1` | 1 |
| MathML `∑ n h n h n + 2 j = 0 , j ≠ 0` | `\sum_{n} h_n h_{n+2j} = 0, \quad j \neq 0` (display) | 1 |
| MathML `g n = ( − 1 ) n h 1 − n` | `g_n = (-1)^n h_{1-n}` (display) | 1 |
| MathML `∑ n h n g n + 2 j = 0` | `\sum_{n} h_n g_{n+2j} = 0` (display) | 1 |
| MathML `( D o s ) j = s 2 j` | `(D_o s)_j = s_{2j}` (display) | 1 |
| MathML `a j + 1 = D 0 H a j and d j + 1 = D 0 G d j` | `a^{j+1} = D_0 H a^j \quad \text{and} \quad d^{j+1} = D_0 G d^j` (display) | 1 |
| `<i>G</i>` | `G` | 1 |
| `<i>g<sub>n</sub></i>` | `g_n` | 1 |
| `<i>h<sub>n</sub></i>` | `h_n` | 1 |
| `<i>D<sub>o</sub></i>` | `D_o` | 1 |
| `↓&#8201;2` | `\downarrow 2` | 1 |
| `<i>s</i>` | `s` | 2 |
| `<i>s</i><sub>0</sub>, <i>s</i><sub>1</sub>, …, <i>s</i><sub><i>N</i>−1</sub>` | `s_0, s_1, \ldots, s_{N-1}` | 1 |
| `<i>N</i> = 2<sup><i>J</i></sup>` | `N = 2^J` | 1 |
| `<i>J</i>` | `J` | 1 |
| `<i>a</i>` | `a` | 1 |
| `<i>d</i>` | `d` | 1 |
| `(<i>D</i><sub>0</sub><i>Hs</i>, <i>D</i><sub>0</sub><i>Gs</i>)` | `(D_0 Hs, D_0 Gs)` | 1 |

`ce0a40_8c2844b7660e4ee0bd8a47e3765da22c_mv2.html` (picture 3 of 4)

| old | new TeX | n |
|---|---|---|
| MathML `( D 1 s ) j = s 2 j + 1` | `(D_1 s)_j = s_{2j+1}` (display) | 1 |
| MathML `D ϵ j` | `D_{\epsilon_j}` | 1 |
| MathML `h 2 r j [ r ] = h j` | `h_{2^r j}^{[r]} = h_j` | 1 |
| MathML `h k [ r ] = 0` | `h_k^{[r]} = 0` | 1 |
| MathML `D 0 r H [ r ] = H D 0 r and D 0 r G [ r ] = G D 0 r` | `D_0^r H^{[r]} = H D_0^r \quad \text{and} \quad D_0^r G^{[r]} = G D_0^r` (display) | 1 |
| MathML `a j + 1 = H [ j ] a j and d j + 1 = G [ j ] d j` | `a^{j+1} = H^{[j]} a^j \quad \text{and} \quad d^{j+1} = G^{[j]} d^j` (display) | 1 |
| `<i>ϵ</i>` | `\epsilon` | 7 |
| `<i>D</i><sub>1</sub>` | `D_1` | 2 |
| `<i>D</i><sub>0</sub>` | `D_0` | 1 |
| `<i>ϵ</i><sub><i>J</i>−1,</sub> <i>ϵ</i><sub><i>J</i>−2</sub>,…, <i>ϵ</i><sub>0</sub>` | `\epsilon_{J-1}, \epsilon_{J-2}, \ldots, \epsilon_0` | 1 |
| `<i>j</i>` | `j` | 1 |
| `Z` | `Z` | 1 |
| `(Z<i>s</i>)<sub>2<i>j</i></sub> = <i>s<sub>j</sub></i>` | `(Zs)_{2j} = s_j` | 1 |
| `(Z<i>s</i>)<sub>2<i>j</i>+1</sub> = 0` | `(Zs)_{2j+1} = 0` | 1 |
| `<i>H</i><sup>[<i>r</i>]</sup>` | `H^{[r]}` | 2 |
| `<i>G</i><sup>[<i>r</i>]</sup>` | `G^{[r]}` | 1 |
| `Z<sup><i>r</i></sup><i>h</i>` | `Z^r h` | 1 |
| `Z<sup><i>r</i></sup><i>g</i>` | `Z^r g` | 1 |
| `<i>H</i>` | `H` | 1 |
| `2<sup><i>r</i></sup><i>j</i>` | `2^r j` | 1 |
| `2<sup><i>r</i></sup><i>j</i> − <i>N</i>` | `2^r j - N` | 1 |
| `<i>k</i>` | `k` | 1 |
| `2<sup><i>r</i></sup>` | `2^r` | 1 |
| `<i>a</i><sup>0</sup> = <i>s</i>` | `a^0 = s` | 1 |

### Multi-objective Optimization

`content/blog/multi-objective-optimization/text/`


`ce0a40_b205da3995314ff5ba642b22b6bac686_mv2.html` (picture 1 of 2)

| old | new TeX | n |
|---|---|---|
| `<i>F</i><sub>1</sub>` | `F_1` | 1 |
| `<i>F</i><sub>2</sub>` | `F_2` | 1 |
| `C` | `C` | 1 |

### Laser Doppler Vibrometer (how it works, advantages and disadvantages, speckle noise)

`content/blog/laser-doppler-vibrometer-how-it-works-advantages-and-disadvantages-speckle-noise/text/`


`ce0a40_ceab5e568ac749f483600e27297584d1_mv2.html` (picture 4 of 8)

| old | new TeX | n |
|---|---|---|
| `var[doppler phase]` | `\operatorname{var}[\text{doppler phase}]` | 1 |

`ce0a40_04b59b4c5741432e96a31bf0364e4cc1_mv2.html` (picture 7 of 8)

| old | new TeX | n |
|---|---|---|
| `sin` | `\sin` | 1 |

### Methods to use in impulse (outlier) detection and estimation of outlier-free signal segments

`content/blog/methods-to-use-in-impulse-outlier-detection-and-estimation-of-outlier-free-signal-segments/text/`


`ce0a40_6da842d935b14d09acf939d20c9d95a4_mv2.html` (picture 1 of 10)

| old | new TeX | n |
|---|---|---|
| `-/+ 2<i>π</i>` | `\mp 2\pi` | 1 |

## Appendix: the hand-written MathML each `MathML` row replaced

For the record, since `content/blog` has no git history. Keyed by the text the rows show.

- `w j`: `<math><msub><mi>w</mi><mi>j</mi></msub></math>`
- `N w`: `<math><msub><mi>N</mi><mi>w</mi></msub></math>`
- `w i`: `<math><msub><mi>w</mi><mi>i</mi></msub></math>`
- `u s ( n )`: `<math><msub><mi>u</mi><mi>s</mi></msub><mo>(</mo><mi>n</mi><mo>)</mo></math>`
- `w y ( n )`: `<math><msub><mi mathvariant='normal'>w</mi><mi>y</mi></msub><mo>(</mo><mi>n</mi><mo>)</mo></math>`
- `w y ( k ) = arg min y ‖ u s − w y ‖ , y = 1 , 2 , … , N w`: `<math display="block"><msub><mi mathvariant='normal'>w</mi><mi>y</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>=</mo><mo>arg</mo><munder><mo>min</mo><mi>y</mi></munder><mo>‖</mo><msub><mi>u</mi><mi>s</mi></msub><mo>−</mo><msub><mi mathvariant='normal'>w</mi><mi>y</mi></msub><mo>‖</mo><mo>,</mo><mspace width='1em'/><mi>y</mi><mo>=</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mo>…</mo><mo>,</mo><msub><mi>N</mi><mi>w</mi></msub></math>`
- `w j ( k + 1 ) = w j ( k ) + η ( k ) h j , y ( k ) ( u s ( k ) − w y ( k ) ) , j = 1 , 2 , … , N w`: `<math display="block"><msub><mi>w</mi><mi>j</mi></msub><mo>(</mo><mi>k</mi><mo>+</mo><mn>1</mn><mo>)</mo><mo>=</mo><msub><mi>w</mi><mi>j</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>+</mo><mi mathvariant='normal'>η</mi><mo>(</mo><mi>k</mi><mo>)</mo><msub><mi>h</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>(</mo><msub><mi>u</mi><mi>s</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>−</mo><msub><mi mathvariant='normal'>w</mi><mi>y</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>)</mo><mo>,</mo><mspace width='1em'/><mi>j</mi><mo>=</mo><mn>1</mn><mo>,</mo><mn>2</mn><mo>,</mo><mo>…</mo><mo>,</mo><msub><mi>N</mi><mi>w</mi></msub></math>`
- `η ( k ) = η 0 exp ( − k τ 1 )`: `<math display="block"><mi mathvariant='normal'>η</mi><mo>(</mo><mi>k</mi><mo>)</mo><mo>=</mo><msub><mi mathvariant='normal'>η</mi><mn>0</mn></msub><mo>exp</mo><mo>(</mo><mo>−</mo><mfrac><mi>k</mi><msub><mi>τ</mi><mn>1</mn></msub></mfrac><mo>)</mo></math>`
- `h j , y ( k ) = exp ( − d j , y 2 2 ε 2 ( k ) )`: `<math display="block"><msub><mi>h</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow></msub><mo>(</mo><mi>k</mi><mo>)</mo><mo>=</mo><mo>exp</mo><mo>(</mo><mo>−</mo><mfrac><msubsup><mi>d</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow><mn>2</mn></msubsup><mrow><mn>2</mn><msup><mi>ε</mi><mn>2</mn></msup><mo>(</mo><mi>k</mi><mo>)</mo></mrow></mfrac><mo>)</mo></math>`
- `ε ( k ) = σ 0 exp ( − k τ 2 )`: `<math display="block"><mi>ε</mi><mo>(</mo><mi>k</mi><mo>)</mo><mo>=</mo><msub><mi>σ</mi><mn>0</mn></msub><mo>exp</mo><mo>(</mo><mo>−</mo><mfrac><mi>k</mi><msub><mi>τ</mi><mn>2</mn></msub></mfrac><mo>)</mo></math>`
- `η ( k )`: `<math><mi mathvariant='normal'>η</mi><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `h j , y ( k )`: `<math><msub><mi>h</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow></msub><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `w y ( k )`: `<math><msub><mi mathvariant='normal'>w</mi><mi>y</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `d j , y 2`: `<math><msubsup><mi>d</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow><mn>2</mn></msubsup></math>`
- `w j ( k )`: `<math><msub><mi>w</mi><mi>j</mi></msub><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `ε 2 ( k )`: `<math><msup><mi>ε</mi><mn>2</mn></msup><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `ε ( k )`: `<math><mi>ε</mi><mo>(</mo><mi>k</mi><mo>)</mo></math>`
- `h j , y ( k = 1 )`: `<math><msub><mi>h</mi><mrow><mi>j</mi><mo>,</mo><mi>y</mi></mrow></msub><mo>(</mo><mi>k</mi><mo>=</mo><mn>1</mn><mo>)</mo></math>`
- `u l = < u x l , u y l >`: `<math><msup><mi>u</mi><mi>l</mi></msup><mo>=</mo><mo>&lt;</mo><msubsup><mi>u</mi><mi>x</mi><mi>l</mi></msubsup><mo>,</mo><msubsup><mi>u</mi><mi>y</mi><mi>l</mi></msubsup><mo>&gt;</mo></math>`
- `u x l = l − m ‾ 2 K + 1 l`: `<math display="block"><msubsup><mi>u</mi><mi>x</mi><mi>l</mi></msubsup><mo>=</mo><mi>l</mi><mo>−</mo><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><mi>l</mi></mrow></msubsup></math>`
- `u y l = [ 0 0 Δ 4 l 0 0 ] − m ‾ 2 K + 1 Δ 4 l`: `<math display="block"><msubsup><mi>u</mi><mi>y</mi><mi>l</mi></msubsup><mo>=</mo><mo>[</mo><mn>0</mn><mspace width='.3em'/><mn>0</mn><mspace width='.3em'/><msup><mi>Δ</mi><mn>4</mn></msup><mi>l</mi><mspace width='.3em'/><mn>0</mn><mspace width='.3em'/><mn>0</mn><mo>]</mo><mo>−</mo><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><msup><mi>Δ</mi><mn>4</mn></msup><mi>l</mi></mrow></msubsup></math>`
- `m ‾ 2 K + 1 l`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><mi>l</mi></mrow></msubsup></math>`
- `m ‾ 2 K + 1 Δ 4 l`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><msup><mi>Δ</mi><mn>4</mn></msup><mi>l</mi></mrow></msubsup></math>`
- `m ‾ 2 K + 1 s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><mi>s</mi></mrow></msubsup></math>`
- `m ‾ 2 K + 1 Δ 4 s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>2</mn><mi>K</mi><mo>+</mo><mn>1</mn></mrow><mrow><msup><mi>Δ</mi><mn>4</mn></msup><mi>s</mi></mrow></msubsup></math>`
- `s i f`: `<math><msup><mi>s</mi><msub><mi>i</mi><mi>f</mi></msub></msup></math>`
- `m ‾ 17 s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>17</mn></mrow><mrow><mi>s</mi></mrow></msubsup></math>`
- `m ‾ 125 Δ 4 s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mn>125</mn></mrow><mrow><msup><mi>Δ</mi><mn>4</mn></msup><mi>s</mi></mrow></msubsup></math>`
- `u s`: `<math><msup><mi>u</mi><mi>s</mi></msup></math>`
- `m ‾ K s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mi>K</mi></mrow><mrow><mi>s</mi></mrow></msubsup></math>`
- `m ‾ K Δ 4 s`: `<math><msubsup><mover><mi>m</mi><mo>‾</mo></mover><mrow><mi>K</mi></mrow><mrow><msup><mi>Δ</mi><mn>4</mn></msup><mi>s</mi></mrow></msubsup></math>`
- `u l`: `<math><msup><mi>u</mi><mi>l</mi></msup></math>`
- `C j l ( x ) = arg min x x ∈ [ 0 , N l ] ‖ l ( x ) − w j ‖ , j = 1 , … , N w`: `<math display="block"><msubsup><mi>C</mi><mi>j</mi><mrow><mi>l</mi><mo>(</mo><mi>x</mi><mo>)</mo></mrow></msubsup><mo>=</mo><mo>arg</mo><munder><mo>min</mo><mi>x</mi></munder><msub><mrow></mrow><mrow><mi>x</mi><mo>∈</mo><mo>[</mo><mn>0</mn><mo>,</mo><msub><mi>N</mi><mi>l</mi></msub><mo>]</mo></mrow></msub><mo>‖</mo><mi>l</mi><mo>(</mo><mi>x</mi><mo>)</mo><mo>−</mo><msub><mi mathvariant="normal">w</mi><mi>j</mi></msub><mo>‖</mo><mo>,</mo><mspace width='1em'/><mi>j</mi><mo>=</mo><mn>1</mn><mo>,</mo><mo>…</mo><mo>,</mo><msub><mi>N</mi><mi>w</mi></msub></math>`
- `C j l ( x )`: `<math><msubsup><mi>C</mi><mi>j</mi><mrow><mi>l</mi><mo>(</mo><mi>x</mi><mo>)</mo></mrow></msubsup></math>`
- `M D j l`: `<math><mi>M</mi><msubsup><mi>D</mi><mi>j</mi><mi>l</mi></msubsup></math>`
- `M D j s`: `<math><mi>M</mi><msubsup><mi>D</mi><mi>j</mi><mi>s</mi></msubsup></math>`
- `( H s ) k = ∑ n h n − k s n`: `<math display="block"><msub><mrow><mo>(</mo><mi>H</mi><mi>s</mi><mo>)</mo></mrow><mi>k</mi></msub><mo>=</mo><msub><mo>∑</mo><mi>n</mi></msub><msub><mi>h</mi><mrow><mi>n</mi><mo>−</mo><mi>k</mi></mrow></msub><msub><mi>s</mi><mi>n</mi></msub></math>`
- `∑ n h n 2 = 1`: `<math><msub><mo>∑</mo><mi>n</mi></msub><msup><msub><mi>h</mi><mi>n</mi></msub><mn>2</mn></msup><mo>=</mo><mn>1</mn></math>`
- `∑ n h n h n + 2 j = 0 , j ≠ 0`: `<math display="block"><msub><mo>∑</mo><mi>n</mi></msub><msub><mi>h</mi><mi>n</mi></msub><msub><mi>h</mi><mrow><mi>n</mi><mo>+</mo><mn>2</mn><mi>j</mi></mrow></msub><mo>=</mo><mn>0</mn><mo>,</mo><mspace width="1em"/><mi>j</mi><mo>≠</mo><mn>0</mn></math>`
- `g n = ( − 1 ) n h 1 − n`: `<math display="block"><msub><mi>g</mi><mi>n</mi></msub><mo>=</mo><msup><mrow><mo>(</mo><mo>−</mo><mn>1</mn><mo>)</mo></mrow><mi>n</mi></msup><msub><mi>h</mi><mrow><mn>1</mn><mo>−</mo><mi>n</mi></mrow></msub></math>`
- `∑ n h n g n + 2 j = 0`: `<math display="block"><msub><mo>∑</mo><mi>n</mi></msub><msub><mi>h</mi><mi>n</mi></msub><msub><mi>g</mi><mrow><mi>n</mi><mo>+</mo><mn>2</mn><mi>j</mi></mrow></msub><mo>=</mo><mn>0</mn></math>`
- `( D o s ) j = s 2 j`: `<math display="block"><msub><mrow><mo>(</mo><msub><mi>D</mi><mi>o</mi></msub><mi>s</mi><mo>)</mo></mrow><mi>j</mi></msub><mo>=</mo><msub><mi>s</mi><mrow><mn>2</mn><mi>j</mi></mrow></msub></math>`
- `a j + 1 = D 0 H a j and d j + 1 = D 0 G d j`: `<math display="block"><msup><mi>a</mi><mrow><mi>j</mi><mo>+</mo><mn>1</mn></mrow></msup><mo>=</mo><msub><mi>D</mi><mn>0</mn></msub><mi>H</mi><msup><mi>a</mi><mi>j</mi></msup><mspace width="2em"/><mtext>and</mtext><mspace width="2em"/><msup><mi>d</mi><mrow><mi>j</mi><mo>+</mo><mn>1</mn></mrow></msup><mo>=</mo><msub><mi>D</mi><mn>0</mn></msub><mi>G</mi><msup><mi>d</mi><mi>j</mi></msup></math>`
- `( D 1 s ) j = s 2 j + 1`: `<math display="block"><msub><mrow><mo>(</mo><msub><mi>D</mi><mn>1</mn></msub><mi>s</mi><mo>)</mo></mrow><mi>j</mi></msub><mo>=</mo><msub><mi>s</mi><mrow><mn>2</mn><mi>j</mi><mo>+</mo><mn>1</mn></mrow></msub></math>`
- `D ϵ j`: `<math><msub><mi>D</mi><msub><mi>ϵ</mi><mi>j</mi></msub></msub></math>`
- `h 2 r j [ r ] = h j`: `<math><msubsup><mi>h</mi><mrow><msup><mn>2</mn><mi>r</mi></msup><mi>j</mi></mrow><mrow><mo>[</mo><mi>r</mi><mo>]</mo></mrow></msubsup><mo>=</mo><msub><mi>h</mi><mi>j</mi></msub></math>`
- `h k [ r ] = 0`: `<math><msubsup><mi>h</mi><mi>k</mi><mrow><mo>[</mo><mi>r</mi><mo>]</mo></mrow></msubsup><mo>=</mo><mn>0</mn></math>`
- `D 0 r H [ r ] = H D 0 r and D 0 r G [ r ] = G D 0 r`: `<math display="block"><msubsup><mi>D</mi><mn>0</mn><mi>r</mi></msubsup><msup><mi>H</mi><mrow><mo>[</mo><mi>r</mi><mo>]</mo></mrow></msup><mo>=</mo><mi>H</mi><msubsup><mi>D</mi><mn>0</mn><mi>r</mi></msubsup><mspace width="2em"/><mtext>and</mtext><mspace width="2em"/><msubsup><mi>D</mi><mn>0</mn><mi>r</mi></msubsup><msup><mi>G</mi><mrow><mo>[</mo><mi>r</mi><mo>]</mo></mrow></msup><mo>=</mo><mi>G</mi><msubsup><mi>D</mi><mn>0</mn><mi>r</mi></msubsup></math>`
- `a j + 1 = H [ j ] a j and d j + 1 = G [ j ] d j`: `<math display="block"><msup><mi>a</mi><mrow><mi>j</mi><mo>+</mo><mn>1</mn></mrow></msup><mo>=</mo><msup><mi>H</mi><mrow><mo>[</mo><mi>j</mi><mo>]</mo></mrow></msup><msup><mi>a</mi><mi>j</mi></msup><mspace width="2em"/><mtext>and</mtext><mspace width="2em"/><msup><mi>d</mi><mrow><mi>j</mi><mo>+</mo><mn>1</mn></mrow></msup><mo>=</mo><msup><mi>G</mi><mrow><mo>[</mo><mi>j</mi><mo>]</mo></mrow></msup><msup><mi>d</mi><mi>j</mi></msup></math>`
