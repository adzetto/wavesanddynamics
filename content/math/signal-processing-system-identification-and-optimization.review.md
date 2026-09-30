# Math review: Signal Processing, System Identification, and Optimization

Read in full: all 269 text nodes of `build/ricos/<slug>/part-01.json`, including
the title block, both disclaimers, every paragraph and list item, the three figure
captions, all 145 cells of the methods table, and the book captions. The four
figures are canvas animations (`anim/nf-sp-*.html`), so none of their text is page
text.

## Set as math (12 entries, 18 places)

| His text | TeX | Where |
|---|---|---|
| `x(t) * h(t) = y(t)` | `x(t) \ast h(t) = y(t)` | Figure 1 caption |
| `Ax = b` (4) | `Ax = b` | Figure 1 caption; Estimation Theory; Closing Thoughts (2) |
| `A`, `x`, `b` | `A`, `x`, `b` | "where A is the system, x is the input, and b is the output" |
| `e(n) = d(n) − y(n)` | `e(n) = d(n) - y(n)` | Figure 2 caption |
| `H1`, `H2` | `H_1`, `H_2` | table: "estimation (H1/H2)" |
| `L1` (2), `L2` (2) | `L_1`, `L_2` | table: "L1 minimization", "L1 regularization", "Tikhonov (L2)"; Inverse Problems: "Tikhonov (L2) regularization" |
| `k` (2) | `k` | "k-means", table cell and Machine Learning |
| `Q` | `Q` | table: "Q-learning" |

The eight places the old regex heuristics set (the convolution, `Ax = b` four
times, and `A`, `x`, `b`) are all among these, in the same places.

Choices a reviewer might question:

- `H1/H2`: his slash means "or" (the H1 or the H2 estimator), so each symbol is its
  own formula and the slash stays text. One formula `H_1/H_2` would read as a ratio.
- `L1`, `L2`: indices go down; his letter is kept, not renamed to `\ell_1`.
- `k`-means and `Q`-learning: only the letter is math, the hyphen and word stay
  text, as LaTeX papers set them. `k` is the number of clusters; `Q` is the
  action-value function. The ML guide's map sets its K-Means, Q-learning and
  `L1`/`L2` the same way.
- `A`, `x`, `b` are italic, not bold, as in Boyd's *Convex Optimization*, which he
  cites for this framing.

## Left as text, and why

- `(MSE = least squares, cross-entropy = MLE)`, table cell: names of methods, with
  `=` standing for "amounts to". There is no symbol or variable, and setting the
  words in the math font would switch fonts mid-sentence. The ML guide's map leaves
  "Training = adjusting all weights ..." as text for the same reason. **Needs a
  decision** if every `=` must be math; the entries would be `\operatorname{MSE} =
  \text{least squares}` and `\text{cross-entropy} = \operatorname{MLE}`.
- Acronyms and model names in prose: AR, ARMA, ARIMA, ARX, ARMAX, NARX, LMS, RLS,
  MLE, MAP, MMSE, FFT / DFT, SVD, PCA, ICA, N4SID, SGD/Adam.
- Enumerators and counts: "1) … 5)", "(i) … (iv)", "2 main reasons", "8 years",
  "Disclaimer #1", "Figure 1" to "Figure 3", "Field(s)".
- "X-ray" (a word, not a variable), "bias/variance" (words).

## Things in his mathematics that look wrong (not fixed)

1. Signal Processing, paragraph 2: "the signal is being multiplied, in the time
   domain this is a convolution, with the impulse response of the filter or with
   the mother wavelet". Multiplication is by the frequency response, in the
   frequency domain; convolution is with the impulse response, in time. The
   wavelet transform correlates the signal with scaled and shifted copies of the
   mother wavelet.
2. Table, "Least squares (ARX, ARMAX, linear regression)", "Yes (convex, often
   closed-form)": true for ARX and linear regression. ARMAX is not linear in its
   parameters (the noise polynomial multiplies unknown innovations), so it needs
   iterative pseudo-linear regression or the prediction error method, and is in
   general nonconvex.
3. Table, "Kalman filter / Extended Kalman Filter", "Optimality proven once, then
   applied recursively": true of the linear Kalman filter. The EKF is a
   linearization with no optimality guarantee.
4. Table consistency: H1 is the least-squares FRF estimate, yet that row says
   "Optimization? No", while the Wiener filter row says "Yes (closed-form
   minimization of mean squared error)". Closed-form solutions of a minimization
   are "Yes" in some rows (least squares, Wiener) and "No" in others (H1/H2,
   matched filter, LDA, PCA).
5. Optimization, global methods: Simulated Annealing is listed among algorithms
   that "evolve a whole population of candidate solutions"; it moves a single
   candidate.
6. Minor: "When the measurement noise is Gaussian, these two approaches actually
   coincide" (MLE and least squares) needs the noise to be independent with equal
   variance; otherwise MLE is weighted least squares. "Both linear and nonlinear
   optimization problems ... can be constrained or unconstrained": an
   unconstrained linear objective has no optimum unless it is constant.

Not an error, only a note: the Figure 1 caption pairs `Ax = b` with "parameter
estimation and inverse problems", and Closing Thoughts reads `A` as the system and
`x` as the input. That holds for an inverse problem. In parameter estimation the
unknown `x` is the system's parameters and `A` is built from the input data, so the
roles swap.

## Checked

Every count against `part-01.json` (a script of my own and `python site/mathtex.py
check`); `python site/build.py --strict --no-word --out build/r13-math-sp/dist`;
screenshots of every changed paragraph at 1440 and 390, light and dark; a scan from
320 to 1680px wide finds no formula parted from a character touching it.
