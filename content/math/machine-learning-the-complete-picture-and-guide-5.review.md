# Machine Learning: The Complete Picture and Guide, math review (round 13)

Map: `machine-learning-the-complete-picture-and-guide-5.json`, 52 entries, 85 replacements.
Every find was counted against the TEXT nodes of `build/ricos/<slug>/part-01.json`, by a
script of my own and by `python site/mathtex.py check`: each count matches, no two finds
claim the same characters, and no context reaches into another find.

I read every text node: paragraphs, headings, table cells, callouts, list items and captions.
The guide promises "no equations" (n6), so most of its mathematics is a letter or a short
expression inside a sentence.

## What is set

Formulas and symbol-bearing expressions:

- 5.1 callout: the single-neuron formula, as a display equation, because it is a line of its
  own in the callout (the renderer gives it its own `<p>`). His `*` becomes juxtaposition,
  indices go down, his words (`bias`, `output`, `activation`) stay upright.
- 4.1: the linear-regression prediction, `(weight1 × square footage) + (weight2 × number of
  bedrooms) + bias`. His `×` stays, since juxtaposing two words would not read. Its products
  are not braced: a braced product is about 17em that cannot break, wider than the column of
  a 360px phone, so the line may break after a `×` as well as after a `+`.
- 3.4: the interaction term `age × risk score`.
- Figure 5 table: the nine feature assignments (`age = 42` ... `credit_score = +0.18`). Each
  one is set alone, so the spaces between them still wrap in a narrow cell, and braced
  (`{\text{age} = 42}`), since TeX never breaks inside a group: no cell ends a line at an
  `=`. `87,000` is set as `87{,}000` so the comma takes no punctuation space.
- Figure 5 caption: the interval `[0,1]`.
- Glossary, Feature Vector: `[age=0.47, income=0.34, credit=0.61]`, each item braced and
  `\allowbreak` after its comma, so a phone breaks between items, never inside one.
- 9.4: precision and recall in words, `TP divided by TP+FP` and `TP divided by TP+FN`. The
  counts are set as `\mathrm{TP}` (not `\operatorname`, which would make the `+` unary); his
  "divided by" stays prose.
- Figure 30 caption: `5x5` as `5 \times 5`.
- `K=3` (4.7 and the Figure 14 caption) and `K=5` (9.3).

Letters named in prose:

- `K`: the number of neighbours (4.7), of clusters (4.8, three places) and of folds (9.3,
  four places).
- `Q`: "a value, almost always written Q", and every Q-value (four).
- `X`: "users similar to you liked X", a placeholder item.
- epsilon, three times, as `\varepsilon` (see the decisions below).

Letters inside method names, set italic with the hyphen and the name left as text, the way
Bishop, ESL and Sutton and Barto print them: K-Means (5), K-Nearest and K-nearest (4),
K-fold (4), Q-learning and Q-Learning (7), Deep Q-Network (2), Z-score (3). The math-sp map
sets its k-means and Q-learning the same way.

Indexed names: `F1` as `F_1` (4, the F-measure with beta = 1), `L1` as `L_1` (4), `L2` as
`L_2` (1). His `L` is kept, not renamed to `\ell`. In "L1/L2" and "L1/Lasso" the slash means
"or", so each symbol is set alone and the slash stays text.

Signed values: tanh's range, `−1` and `+1`, and the reward values in 7.4 (`+1`, `-1`,
`-0.02`, with his hyphen becoming a minus sign). The zeros in the same two reward lists are
set too, so each list reads in one font.

## Left as text, and why

- Acronyms and model or metric names: KNN, SVM, MLP, CNN, RNN, LSTM, DQN, PPO, SARSA, ARIMA,
  ReLU, Sigmoid, Tanh, Softmax, MAE, RMSE, ROC AUC, PR AUC, and TP, FP, FN, TN where the
  confusion-matrix cells introduce them. They are names in a sentence, not symbols in a
  formula; a LaTeX author types them as text. "Min-Max" is a method's name.
- Words that contain a capital letter: S-shaped, X-ray, E-commerce, and 2D (the spec keeps
  "2D" and "3D" as words).
- Functions and tests named in words: "log transforms", "cyclical sine and cosine encoding",
  "chi-square tests", "square root", "dot product". These are English names in a sentence,
  as a LaTeX author writes them; unlike epsilon below, none of them stands for a variable.
- Unsigned numbers outside a formula: percentages, counts, thresholds ("the default 0.5"),
  "between 0 and 1", "centered at 0", "a discount near 1", "scored 0.3", "was 7", "$10,000",
  "3am", "2018", "forty moves". Unsigned digits are text in a LaTeX document too.
- Ranges written with a hyphen: "0-1 range", "(0-1)", "0-1 probability", "0-255 to 0-1",
  "10-30%". They are prose ranges; only "[0,1]", his interval notation, is set.
- "under ~100k rows" and "100k+": quantities with a unit (rows), the spec's "3 floors" case.
- Section, figure, table and step numbers, and the list markers (1), (2), (3).
- The arrow in the 3 callout, "Keep these steps separate in your mind → explore the data":
  punctuation in a sentence, not an arrow between two mathematical statements.
- The Figure 17 caption, "Training = adjusting all weights to reduce prediction error": the
  `=` is shorthand for "means" in a caption sentence, not an equation.
- Text drawn inside the figure images is canvas, outside the text nodes.

## Decisions for the controller

1. epsilon. He spells the letter as a word: "epsilon-greedy", "with a small probability,
   epsilon, take a random one instead", "Epsilon usually starts high". I set all three as
   `\varepsilon` (ε-greedy, as Sutton and Barto print it), because the word names the
   variable. If his spelled-out word should stay, delete the three `epsilon` entries.
2. Letters inside names (K-Means, K-fold, Q-learning, Z-score ...) are set, including in three
   headings (4.7, 4.8, 7.4) and four table cells. If names should stay plain words, delete the
   entries that have only an `after` context.
3. Signed numbers are set, unsigned ones are not. In the activation table after Figure 16 the
   tanh row (`−1`, `+1`) is therefore math and the sigmoid row ("between 0 and 1") is text.

## Possible errors in his mathematics (not fixed)

1. Figure 30 against 7.4. The caption says "the only reward is reaching the goal" and "After
   one episode only the square beside the goal has any value". 7.4 says of the same grid
   world "it is +1 for reaching the goal and -0.02 for every step taken". With a step reward
   of −0.02, every square visited in the first episode gets a small negative value, so the
   caption and the text describe two different reward functions. The text also says "in your
   Figure 30", which reads like a reply addressed to the author.
2. 7.4, Q-learning in words: "The reward plus that best next value is a better estimate".
   The target is the reward plus the discounted best next value, r + γ max Q. The discount
   factor appears two sentences later as a knob, but this sentence leaves it out.
3. 4.5: "the residuals, or more precisely the gradient of the loss function". Each tree fits
   the negative gradient (the pseudo-residuals); the sign is missing.
4. 4.1: "the line is positioned to minimize the total squared distance between itself and
   every data point". Least squares minimises the squared vertical distances, as the Figure 8
   caption says correctly; "distance between itself and every point" reads as perpendicular
   distance, which is a different fit (total least squares).
5. Figure 5 caption: "Z-score standardization is more robust" to outliers. The mean and the
   standard deviation are themselves pulled by outliers; z-scores only avoid squeezing the
   other values into a small range. Debatable rather than wrong.
6. The Glossary's feature vector names `credit=0.61` where Figure 5 names the same value
   `credit_score = 0.61`. Naming only.
7. The introduction (n6) says "It has no equations"; 5.1 now shows a display equation and 4.1
   an inline formula.

## Rendering check

Built with `python site/build.py --strict --no-word --out build/r13-math-ml/dist` on
mathinfra's renderer (TeX break points, glue spans, bold math in bold runs). Every block
that holds math was screenshotted at 1440x900 and 390x844, with a sample in dark mode, and
measured at nine widths from 320 to 1920px:

- all 93 inline math elements (85 formulas, some in pieces) sit on the text baseline
  within 0.6px;
- no page scrolls sideways, and no formula is wider than its block;
- no line breaks between a formula and a character glued to it (K | -Means, L1 | /Lasso);
- the single-neuron display is one centred line on a desktop and two lines on a phone,
  breaking before the arrow;
- math in headings and bold cells is Latin Modern's bold; in dark mode it takes the text's
  ink.

The one flag at 390, a `Z` "clipped" in the Figure 5 table head, is the head row the phone
layout hides on purpose; its column names come back as labels.

Not mathematics, seen while reading (left untouched): "multi-layer perception (MLP)" in the
scope note (perceptron), "Weighs decide" in the 5.1 callout (Weights), "Learning
reinforcement learns from consequences" in the 7.5 callout, "the classic reason THAT a SARSA
agent" in 7.4.


## Controller ruling (28 Sep 2026)

His word "epsilon" (3 places) stays his word: setting it as a symbol would change his words, not only their typesetting. The three entries were removed.
