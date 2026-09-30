# Round 5 spec (2026-09-25): binding for every agent in this round

Builds on `site/design/ROUND4_SPEC.md` (still binding where this file is silent) and
`site/design/DESIGN_BRIEF.md`. Target: the static site in `site/`. No Wix site is touched.

## 0. The user's feedback on round 4 (Turkish, summarised)
1. The Big Picture map must not be done "that way": categorise the topics well, and never link
   into a section of a document, because readers have to read each document in full.
2. The Big Picture can go into the left column again as an expandable list; when someone opens
   it, do something beautiful for that moment.
3. The wind turbine and spectrum animations keep the browser too busy: fix the performance, but
   keep the animations.
4. In the hero illustration, the hover labels (the names shown under it) should be cleaner and
   simpler.
5. My Research Areas page: its document boxes should sit vertically in the empty space on the
   right side of the page.
6. About page: the research-areas list with the dotted line and small circles ("the beaded
   chain") should come alive: when the page opens, when it scrolls into view, and on hover.
7. Endless loops are fine: the masthead wave and the illustration keep looping; no pause
   control is required. `prefers-reduced-motion: reduce` still gives a still page.
8. Home page: no photo of the professor any more. His photo goes to the top of the left column,
   on every page, done beautifully and professionally.

## 1. Rulings
- **Links into documents**: no link anywhere on the site may target an anchor inside a
  document page (`doc/*.html#...`), except the document's own Contents and in-page links. The
  Big Picture page and the column link to whole documents or to places on the Big Picture page.
- **Big Picture categories** (one list, defined once in `site/parts/documents.py` as
  `CATEGORIES`, imported by build.py for the column). Order and whole-document coverage:

  | id | label | covered by (whole documents) |
  |---|---|---|
  | waves | Waves | Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation; From Bridges to Photons |
  | dynamics | Dynamics | Dynamical Behavior of Engineering Structures and Acoustic Wave Propagation |
  | signal-processing | Signal Processing | Signal Processing, System Identification, Estimation Theory and Optimization (the guide) |
  | system-identification | System Identification | the same guide |
  | estimation-theory | Estimation Theory | the same guide |
  | optimization | Optimization | the same guide |
  | machine-learning | Machine Learning | Machine Learning (the guide) |
  | probability-statistics | Probability & Statistics | in preparation (probability-statistics.html) |
  | python-programming | Python / Programming | in preparation (python-programming.html) |
  | communication | Communication | in preparation (communication.html) |

  Each entry: `dict(id, label, docs=[slugs], soon=href or None)`. The three SHM/NDT research
  documents stay on the page as their own group after the categories ("From my research").
  Grouping the categories into a few families with neutral labels is allowed; the round-4
  "Physics / Measurement / Data analytics" framing is dropped (it misfiled topics).
- **Column**: the "Big Picture of Waves and Data Analytics" row becomes expandable (open on the
  Big Picture page itself, closed elsewhere unless the reader opened it; remember the reader's
  choice). Its items are the ten categories, each opening `big-picture.html#<id>`. Rows 5-10
  stay top-level rows exactly as round 4 built them. The opening moment and the arrival on the
  Big Picture page are designed by a design panel (brainstorm, see the workflow).
- **Photo**: remove the portrait block from index.html (photo and the lines under it). Put his
  portrait at the top of the column's name block on every page (desktop column, phone drawer
  header; a small version in the phone top bar is allowed), professional: real photo, calm
  crop, no decorative ring colours outside the palette, alt text, width/height set, sharp at 2x.
  The masthead band on index still lines up with the column (the name block height changes).
  About keeps its larger portrait in the profile header, as in his slide 2.
- **Research page**: at desktop widths the document boxes stack vertically in a right column
  beside his text; below the breakpoint they follow the text as today.
- **Motion**: loops may run indefinitely (ruling 7); they must still pause off-screen and on a
  hidden tab (that is performance, not accessibility), and reduced motion stays static.

## 2. Carry-over findings from round 4
`build/r5/findings-r4.json` holds all 40 findings of the round-4 review with a `status` field:
37 are `open` (3 high, 7 medium, 27 low), 3 are `dropped` (A11Y-1 and RM-2: loops stay, see
ruling 7; C2: superseded by the Big Picture redesign). Each agent fixes the open findings whose
file it owns, lows included, and reports each id it closed.

## 3. Gates
As ROUND4_SPEC section 11, plus: no `doc/*.html#` link outside the document's own page; with
the illustration on screen and no input, the main thread is idle between frames (performance
trace: no recurring style/layout/paint from the turbine or the spectrum bars); the column's
expandable list works with keyboard and screen reader (button with aria-expanded, focus kept).
