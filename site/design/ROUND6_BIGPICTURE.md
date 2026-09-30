# Round 6: the Big Picture page (2026-09-26)

Binding for the work on `site/parts/documents.py`, the only repo file it changes. Where this
file is silent, `ROUND5_SPEC.md` and `DESIGN_BRIEF.md` still bind. It merges two proposals (one
on information, one on motion) and was checked on a prototype of exactly this design, injected
into a build of today's page and measured in headless Chromium: every number below is a
measurement.

## 0. Context

**The professor, 25 Sep 2026.**
1. He called the map "mükemmel bir visualization". Its hub, rings, spokes, flowing dots, hover
   dimming and dashed pills for pages in preparation stay.
2. Probability & Statistics is no longer in preparation: his deck, titled "Probability,
   statistics and estimation" on its slide 1, 73 slides, is `probability-statistics.html`.
3. His "Extensive ppt regarding my MSc and PhD Research", 177 slides, `presentation.html`,
   joins his research.
4. He took his six topics out of the column; the Big Picture row's list (`parts/bpnav.py`) names
   them, read from `CATEGORIES`. Its ids and keys are an interface.

**What his material asks of the map.** His motivation (`PROF_MOTIVATION`) names what took him
years: where the methods are applied, what problems they solve, "how similar concepts reappear
across different fields" and "how deeply interconnected they actually are". His meeting notes
list the Big Picture as Waves, Dynamics, Signal Processing, System Id., Estimation theory,
Optimization, Machine learning, Python / Programming, Blog / Communication tips. After this
round every item of that list but the blog is on the map, as a topic or as the name of a line
between two.

**What is wrong today** (measured on the current page):

| | |
|---|---|
| Phone, 390px | the 740-unit map shrinks to 0.47: labels about 7px, pills 21px tall |
| Dots | no `cx`/`cy`: each waits at the SVG origin, a stray dot at the figure's top left, for up to 3.6s |
| Main thread | 121 layouts and 60 style recalculations a second with the map on screen, about 72ms of every second (SMIL dots, CSS transforms inside the SVG); the motion proposal measured it running on off screen too |
| Links | eight unnamed dotted lines; two (Python to Machine Learning, Communication to research) rest on no text of his |
| Dark theme | hub text white on light amber, 2.3:1; the list's grouped rows mix `#fff` into the page and turn grey, notes unreadable |

## 1. Decisions

Kept as he approved it: the hub disc and its two rings, straight spokes that draw in on load,
the flowing dots, the pills, hover dimming, dashed pills for pages in preparation, and the
jump to the topic's group with its arrival wash.

| Decision | Why | From |
|---|---|---|
| Five named bridges replace the eight unnamed dotted lines; each carries a word both topics' own texts use (sources in 2.3) | it shows his "Aha!", concepts reappearing across fields, in his words, instead of asserting a link | information |
| No bridge touches Python / Programming or Communication | no text of his joins them to another topic yet; a page in preparation keeps its spoke and nothing more | information |
| Waves & Dynamics and From my research swap places (9 and 10:30 o'clock) | four bridges then join neighbours on the rim; only Estimation crosses inside | information |
| A pill's second line says what the topic holds, in the list's words: "18-page read", "73 slides", "2 documents", "In preparation" | one kind of line, true for every topic, computed from the data the list shows; his column sub-lines are long and exist for only some topics, and the bridges now carry the sub-topics | information |
| Signal Processing's bridges are System Identification, Optimization and Estimation | the node and its three words are the category's own label ("Estimation Theory" as his sub-line shortens it), so its sub-topics show exactly where they are shared; no satellites | information |
| Below 740px of figure width a second, portrait map ("tall"): same topics, same bridges | the one map shrank to 7px; a fanned list (motion proposal) loses the picture he praised and its arcs could carry no words | information |
| The tall map's names and second lines are 13.6 and 12.6 units, its hub 46 units | 12px on a 360px phone as well as on 390px; "Data Analytics" clears the disc | judge |
| The rings and the dots are HTML boxes between two SVGs (lines behind; hub, words and pills in front), moved by transform and opacity only | the site's rule for loops (`heroart.py`, `masthead.md`): 0 layouts, and 0 style recalculations once `theme.py`'s observer lets go (7.2); the same picture | judge |
| No IntersectionObserver: the script looks at the figure on scroll and resize, once a frame at most, and on `visibilitychange`, and pauses the loops while the map is off screen or the tab hidden | round-4 finding RM-3: an observer holding a target costs a main-thread frame at every vsync while anything animates | motion, corrected |
| Dots start under the hub disc | no stray dot | both |
| Hub text in `--btn-fg` | 5.55:1 light, 8.1:1 dark | both |
| Keyboard focus: a ring 4 units outside the pill, 2px `--focus`, non-scaling; the highlight is instant | no box around a pill; no travel for a key | both |
| Dimming follows the mouse only; a tap presses and jumps | a touch has no hover to leave, so the map stayed dim | motion |
| A press scales the pill to .97 | feedback on the press itself | motion |
| A visually hidden list names the five bridges | the words are drawn, so a screen reader must be told them | information |
| Dropped: the hover card | it repeats the list right below, covers the hub, and hid its links from assistive technology | (motion) |
| Dropped: marching dashes on lit bridges | motion under words; the map already has two loops | (motion) |
| Dropped: a legend | the caption says it | (information) |

## 2. Data

### 2.1 Module constants

`CATEGORIES`: ids, order, labels, `short` and `docs` unchanged. The probability entry becomes

```python
dict(id="probability-statistics", label="Probability & Statistics", docs=[], soon=None,
     decks=["probability-statistics.html"]),
```

`decks` is a new, optional key: the deck pages that cover a category. `_SOON` loses
`"probability-statistics.html"`; Python / Programming and Communication stay in preparation.

```python
DECKS = {   # href -> (title, note, slide count): the titles are his, the notes ours
    "probability-statistics.html": ("Probability, statistics and estimation",
                                    "Opens with a big-picture map of the subject.", 73),
    "presentation.html": ("Extensive ppt regarding my MSc and PhD Research",
                          "The master's and PhD work, in more depth.", 177),
}
RESEARCH_DECKS = ("presentation.html",)   # after RESEARCH's three documents
```

`__all__` gains `DECKS` and `RESEARCH_DECKS`. `render_big_picture(docs=None, decks=None)`:
`decks` has the shape of `DECKS` and replaces it when given (build.py will pass the real
counts). A deck page missing from `decks` gets no row and counts nowhere, since the build did
not write it. A category left with nothing to open keeps its heading (the column links to its
id), shows no list, and its node is drawn in preparation. `families()` is unchanged.

### 2.2 Nodes

Order = DOM order = Tab order = the list's order. Positions are centres in each map's viewBox
units. Wide: viewBox `-10 -10 740 380`, pills 44 high, rx 22. Tall: viewBox `0 0 330 496`,
pills 46 high, rx 23.

| n | id | name on the map | second line today | wide x, y, width | tall x, y, width |
|---|---|---|---|---|---|
| 0 | waves-dynamics | Waves & Dynamics | 2 documents | 106, 226, 136 | 76, 382, 138 |
| 1 | signal-processing | Signal Processing | 18-page read | 360, 34, 130 | 165, 34, 132 |
| 2 | machine-learning | Machine Learning | 44-page read | 588, 70, 132 | 256, 126, 132 |
| 3 | probability-statistics | Probability & Statistics | 73 slides | 614, 226, 160 | 247, 382, 162 |
| 4 | python-programming | Python / Programming | In preparation | 470, 326, 160 | 247, 468, 162 |
| 5 | communication | Communication | In preparation | 250, 326, 122 | 76, 468, 122 |
| 6 | research | From my research | 3 documents, 177 slides | 132, 70, 154 | 84, 126, 156 |

- The second line comes from what the list shows for the topic: one document, its
  "N-page read" (`_PAGES`); several, "N documents"; decks, "N slides" (their total); both,
  joined by ", "; nothing, "In preparation" (dashed pill, `--muted` text, no dot).
- Type: the name 600, 13 units (tall 13.6), baseline y - 3; the second line 500, 12 units
  (tall 12.6), baseline y + 13 (tall y + 14); both centred on x.
- Width: the wider line measured in Source Sans 3 at its size, plus 32 units (tall 28), rounded
  up to an even number. If a count ever changes the words, measure again.
- Each node is `<a class="bpg__n" href="#<id>" data-n="<id>" aria-label="<name>, <second line>">`
  (`bpg__n bpg__n--soon` in preparation), the second line lower-cased when it is "in
  preparation": "Waves & Dynamics, 2 documents", "Probability & Statistics, 73 slides",
  "Python / Programming, in preparation", "From my research, 3 documents, 177 slides".

### 2.3 Bridges

Dotted lines, each with its word on the line (the label's centre lies on the curve).

| i | word | ends | wide path; label centre | tall path; label centre |
|---|---|---|---|---|
| 0 | Wave Propagation | waves-dynamics, research | `M106 226Q35 137 132 70`; 77, 148 | `M76 382Q24 254 84 126`; 52, 254 |
| 1 | System Identification | research, signal-processing | `M132 70Q206 7 360 34`; 217, 31 | `M84 126Q-4 66 165 34`; 60, 73 |
| 2 | Optimization | signal-processing, machine-learning | `M360 34Q514 7 588 70`; 481, 28 | `M165 34Q341 66 256 126`; 276, 73 |
| 3 | Regression | machine-learning, probability-statistics | `M588 70Q685 137 614 226`; 643, 148 | `M284 126Q302 254 284 382`; 289, 172 |
| 4 | Estimation | signal-processing, probability-statistics | `M360 34Q442 148 614 226`; 491, 158 | `M178 44C172 110 180 180 246 206C272 220 258 300 262 360`; 246, 206 |

On the wide map System Identification and Optimization stand 22 units either side of Signal
Processing's pill, so the top row reads even (at 226, 30 and 494, 30 they were 13 and 35 units
from it).

His words on each side, for the comment over `_BRIDGES`:
- Wave Propagation: the guide's title, "...and Acoustic Wave Propagation"; his research text,
  "acoustic wave propagation" (`PROF_RESEARCH`), and "Understanding SHM and NDT" throughout.
- System Identification: the signal processing guide, "system identification is the main core
  of vibration-based structural health monitoring (SHM)"; "Understanding SHM and NDT", "run
  through system identification algorithms".
- Optimization: the signal processing guide's title, "...Estimation Theory and Optimization
  with the underlying logic of machine learning"; the machine learning guide, "Gradient
  Descent: The optimization algorithm."
- Regression: the machine learning guide, "4.1 Linear Regression: Predict a Number"; his deck,
  slide 22, "Regression: a response depends on predictors".
- Estimation: his column sub-lines "Estimation, Inverse Problems, Optimization, Machine
  Learning" and "Stochastic Process, Estimation"; his deck's title, and slide 61, "Estimation
  theory: designing rules for unknown quantities".
- Rejected: Mode Shapes (a sixth word crowds the phone, and on the signal processing side it is
  body text only); research to Machine Learning (it crosses the map, and its word would be a
  node's name).

On the tall map Regression's word sits just under Machine Learning and Estimation's right of
the hub, so their two lines run down into Probability & Statistics side by side, about 25 units
apart, with no word between them.

### 2.4 Hub, spokes and loops

- Hub: wide (360, 180) r 48; tall (165, 252) r 46. "Waves &" at hub y - 4 and "Data Analytics"
  at hub y + 13, 600 13 units, centred.
- Spokes: `M<hub x> <hub y>L<x> <y>` to every node, its n in `--k`. On the tall map the two
  pages in preparation share a trunk that runs between Waves & Dynamics and Probability &
  Statistics and forks onto the straight part of their pills' top edges (a straight spoke would
  run under the two pills above them): Python / Programming `M165 252L156 420Q156 445 190 445`,
  Communication `M165 252L156 420Q156 445 112 445`.
- The loops layer, in percent of the stage (the stage is the viewBox x0, y0, W, H):
  - hub centre: left (hub x - x0) / W, top (hub y - y0) / H: wide 50%, 50%; tall 50%, 50.806%;
  - rings: width 2r / W (wide 12.973%, tall 27.879%), `aspect-ratio:1`, centred on the hub;
  - one run for each node not in preparation (five): a `.bpg__run` box the size of the stage
    with `--dx` = (x - hub x) / W and `--dy` = (y - hub y) / H, which the animation moves in
    percent of its own box; in it one dot at the hub centre, width 5.2 / W (wide .703%,
    tall 1.576%). Waves & Dynamics, wide: `--dx:-34.324%;--dy:12.105%`;
  - timing by n (today's): `--t` = 3.2 + 0.35n s, `--d` = 1.2 + 0.4n s: Waves & Dynamics
    3.20s and 1.2s, Signal Processing 3.55 and 1.6, Machine Learning 3.90 and 2.0,
    Probability & Statistics 4.25 and 2.4, research 5.30 and 3.6.

## 3. Markup

```html
<figure class="bpg">
 <div class="bpg__stage bpg__stage--wide">
  <svg class="bpg__back" viewBox="-10 -10 740 380" aria-hidden="true">
   <!-- 5 bridges, then 7 spokes -->
   <path class="bpg__e bpg__e--b" style="--i:0" data-a="waves-dynamics research" d="..."/>
   <path class="bpg__e bpg__e--s" style="--k:0" data-a="hub waves-dynamics" d="..."/>
  </svg>
  <span class="bpg__loops" aria-hidden="true">
   <i class="bpg__ring" style="left:50%;top:50%;width:12.973%"></i>
   <i class="bpg__ring bpg__ring--2" style="left:50%;top:50%;width:12.973%"></i>
   <!-- 5 runs -->
   <span class="bpg__run" data-a="hub waves-dynamics"
         style="--dx:-34.324%;--dy:12.105%;--t:3.20s;--d:1.2s"><i style="left:50%;top:50%;width:.703%"></i></span>
  </span>
  <svg class="bpg__front" viewBox="-10 -10 740 380" role="group" aria-label="Map of the topics">
   <g class="bpg__hub" aria-hidden="true"><circle class="c" cx="360" cy="180" r="48"/>
    <text x="360" y="176" text-anchor="middle">Waves &amp;</text>
    <text x="360" y="193" text-anchor="middle">Data Analytics</text></g>
   <g aria-hidden="true"><!-- 5 words -->
    <text class="bpg__w" style="--i:0" data-a="waves-dynamics research" x="77" y="148"
          text-anchor="middle" dominant-baseline="central">Wave Propagation</text></g>
   <!-- 7 nodes -->
   <a class="bpg__n" href="#waves-dynamics" data-n="waves-dynamics" aria-label="Waves &amp; Dynamics, 2 documents">
    <rect class="bpg__f" x="34" y="200" width="144" height="52" rx="26"/>
    <rect class="bpg__r" x="38" y="204" width="136" height="44" rx="22"/>
    <text x="106" y="223" text-anchor="middle">Waves &amp; Dynamics</text>
    <text class="bpg__c" x="106" y="239" text-anchor="middle">2 documents</text></a>
  </svg>
 </div>
 <div class="bpg__stage bpg__stage--tall"><!-- the same, from the tall data --></div>
 <ul class="bp__vh"><li>Wave Propagation, shared by Waves &amp; Dynamics and From my research.</li><!-- 5 --></ul>
 <figcaption class="bpg__cap">Each dotted line names a concept that two topics share. Choose a topic to go to its documents and slides.</figcaption>
</figure>
```

- The focus ring `.bpg__f` is the pill grown by 4 units on every side, rx half its height.
- Paint order carries the picture: lines behind the dots, the dots and rings under the hub
  disc, the words and the pills, so a dot leaves from under the hub and ends under its pill and
  a ring passes under a word's page-coloured halo.
- The hidden list's items read "<word>, shared by <A> and <B>.", A and B in the list's order.
- Attribute values go through `html.escape(..., quote=True)`. No `id` inside either SVG: both
  stages are in the page.

## 4. Style

Tokens only; the two literals kept from the approved map are the rings' curve
`cubic-bezier(.2,.6,.3,1)` and their 3.6s period. In `documents.CSS` every `%` below is
written `%%`. The old map rules go (`.bpg svg`, `.bpg__e--x`, `.bpg__p`, `.bpg__hub circle.c`,
the `max-width:560px` rule and the reduce rule after it). The implementer adds the module's
explain-why comments.

```css
.bpg{container:bpg/inline-size;position:relative;max-width:var(--measure-fig);margin:28px 0 8px}
.bpg__stage{position:relative}
.bpg__stage--wide{aspect-ratio:740/380}
.bpg__stage--tall{aspect-ratio:330/496;max-width:420px}
@container bpg (width >= 740px){.bpg__stage--tall{display:none}}
@container bpg (width < 740px){.bpg__stage--wide{display:none}}
.bpg__back,.bpg__front{position:absolute;inset:0;display:block;width:100%;height:100%;overflow:visible}
.bpg__e{fill:none;stroke:color-mix(in oklab,var(--ink) 16%,transparent);stroke-width:1.2;
  transition:opacity var(--t-fast) var(--ease-state),stroke var(--t-fast) var(--ease-state)}
.bpg__e--b{stroke:color-mix(in oklab,var(--ink) 30%,transparent);stroke-width:1.4;
  stroke-dasharray:2 5;stroke-linecap:round}
.bpg__w{font:600 12px/1 var(--sans);letter-spacing:.01em;fill:var(--muted);pointer-events:none;
  paint-order:stroke;stroke:var(--page);stroke-width:5px;stroke-linejoin:round;
  transition:opacity var(--t-fast) var(--ease-state),fill var(--t-fast) var(--ease-state)}
.bpg__stage--tall .bpg__w{font-size:12.6px}
.bpg__hub .c{fill:var(--accent)}
.bpg__hub text{fill:var(--btn-fg);font:600 13px/1 var(--sans);letter-spacing:.01em}
.bpg__loops{position:absolute;inset:0;overflow:clip;pointer-events:none;display:none}
.bpg__ring{position:absolute;aspect-ratio:1;border:1px solid var(--accent);border-radius:50%;
  translate:-50% -50%;opacity:0}
.bpg__run{position:absolute;inset:0;transition:opacity var(--t-fast) var(--ease-state)}
.bpg__run i{position:absolute;aspect-ratio:1;border-radius:50%;background:var(--accent);
  opacity:.85;translate:-50% -50%}
.bpg__n{cursor:pointer;text-decoration:none;-webkit-tap-highlight-color:transparent;
  transition:opacity var(--t-fast) var(--ease-state)}
.bpg__n:focus-visible{outline:none}
.bpg__r{fill:var(--page);stroke:color-mix(in oklab,var(--ink) 18%,transparent);stroke-width:1;
  transform-box:fill-box;transform-origin:center;
  transition:fill var(--t-fast) var(--ease-state),stroke var(--t-fast) var(--ease-state),
    transform var(--t-fast) var(--ease)}
.bpg__f{fill:none;stroke:var(--focus);stroke-width:2;vector-effect:non-scaling-stroke;opacity:0}
.bpg__n:focus-visible .bpg__f{opacity:1}
.bpg__n text{fill:var(--ink);font:600 13px/1 var(--sans)}
.bpg__n .bpg__c{fill:var(--muted);font-weight:500;font-size:12px}
.bpg__stage--tall .bpg__n text{font-size:13.6px}
.bpg__stage--tall .bpg__n .bpg__c{font-size:12.6px}
.bpg__n--soon .bpg__r{stroke:color-mix(in oklab,var(--ink) 30%,transparent);stroke-dasharray:3 3}
.bpg__n--soon text{fill:var(--muted)}
.bpg__n.on .bpg__r{fill:var(--wash);stroke:var(--accent)}
@media (hover:hover) and (pointer:fine){.bpg__n:hover .bpg__r{transform:scale(1.04)}}
.bpg__n:active .bpg__r{transform:scale(.97);transition-duration:var(--t-quick)}
.bpg[data-on] .bpg__e,.bpg[data-on] .bpg__w,.bpg[data-on] .bpg__n,.bpg[data-on] .bpg__run{
  transition-duration:var(--t-mid)}
.bpg[data-on] .bpg__e:not(.on),.bpg[data-on] .bpg__w:not(.on){opacity:.16}
.bpg[data-on] .bpg__run:not(.on){opacity:.2}
.bpg[data-on] .bpg__n:not(.on){opacity:.45}
.bpg[data-on] .bpg__e.on{stroke:var(--accent)}
.bpg[data-on] .bpg__w.on{fill:var(--accent)}
.bpg[data-key] *{transition:none!important}
.bpg__cap{margin:10px 0 0;font:500 14px/1.5 var(--sans);color:var(--muted)}
@media (prefers-reduced-motion:no-preference){
  .bpg__loops{display:block}
  .bpg__ring{animation:bpg-ring 3.6s cubic-bezier(.2,.6,.3,1) infinite}
  .bpg__ring--2{animation-delay:1.8s}
  .bpg__stage--tall .bpg__ring{animation-name:bpg-ring-t}
  .bpg__run{animation:bpg-run var(--t) linear var(--d) infinite}
  .js .bpg:not([data-run]) .bpg__ring,.js .bpg:not([data-run]) .bpg__run{animation-play-state:paused}
  .bpg__e--s{stroke-dasharray:640;stroke-dashoffset:640;
    animation:bpg-draw 1400ms var(--ease) calc(var(--k) * 90ms) forwards}
  .bpg__e--b,.bpg__w{animation:bpg-in var(--t-slow) var(--ease) calc(900ms + var(--i) * 80ms) backwards}
}
@keyframes bpg-ring{from{scale:1;opacity:.55}to{scale:1.9;opacity:0}}
@keyframes bpg-ring-t{from{scale:1;opacity:.55}to{scale:1.6;opacity:0}}
@keyframes bpg-run{to{transform:translate(var(--dx),var(--dy))}}
@keyframes bpg-draw{to{stroke-dashoffset:0}}
@keyframes bpg-in{from{opacity:0}}
@media (forced-colors:active){
  .bpg__r,.bpg__hub .c{fill:Canvas;stroke:CanvasText}
  .bpg__n text,.bpg__n .bpg__c,.bpg__w,.bpg__hub text{fill:CanvasText}
  .bpg__n--soon .bpg__r{stroke:CanvasText}
  .bpg__f,.bpg__n.on .bpg__r,.bpg[data-on] .bpg__e.on{stroke:Highlight}
  .bpg__loops{display:none}
}
@media print{.bpg{display:none}}
```

In the list's CSS one rule changes (tokens only, and the dark theme's grey rows go):
`.bp__reads{... background:color-mix(in oklab,var(--page) 55%,#fff) ...}` becomes
`background:var(--page);background:oklch(from var(--page) calc(l + .008) c h)`, the same
near-white in light, a shade over the page in dark.

## 5. States and motion

| State | Trigger | What changes | Timing |
|---|---|---|---|
| Rest | | lines 16% ink, bridges 30% ink, dotted `2 5`, round caps; pills `--page`, 18% ink edge; in preparation dashed `3 3`, 30% ink, `--muted` text; words `--muted` on a `--page` halo | |
| Load | first render | spokes draw 1400ms `--ease`, 90ms apart in node order; bridges and words fade in `--t-slow` `--ease` from 900ms, 80ms apart. Not paused: a map whose script never runs must still be whole | once |
| Loops | while seen | rings: .55 to 0, scale 1 to 1.9 (tall 1.6), 3.6s, the second 1.8s behind; dots: from the hub to the node, linear, `--t` and `--d` of 2.4 | forever |
| Unseen | off screen, or the tab hidden (and until the script first looks) | the loops pause where they are | |
| Lit by the mouse | `pointerenter`, pointer type mouse | `.bpg[data-on=<id>]`; the node, its spoke, its dot, its bridges and words, and the nodes at their far ends take `.on`: pills `--wash` with an `--accent` edge, lines and words `--accent`; the hovered pill scales 1.04 (`hover:hover` and `pointer:fine` only); the rest: lines and words .16, dots .2, pills .45 | dim `--t-mid` `--ease-state`, back `--t-fast`; scale `--t-fast` `--ease`; 90ms grace on leaving, so moving to a neighbour never flashes |
| Lit by the keyboard | `:focus-visible` | as above without the scale, at once (`data-key` turns transitions off); the ring `.bpg__f` shows | 0ms |
| Press | `:active` | the pill scales .97 | `--t-quick` |
| Touch | tap | no dimming; the press; the jump | |
| Choose | click, Enter, tap | jumps to `#<id>` (no smooth scrolling); the list's rail and wash play there | |
| Reduced motion | `prefers-reduced-motion: reduce` | no loops layer, no draw, no fade, no scale; lit and unlit switch at once (the site's reduce rule) | |
| Forced colours | `forced-colors: active` | pills Canvas and CanvasText, text CanvasText, lit and focused Highlight, no loops | |
| Print | | the figure is hidden | |

## 6. Script

Before `var bp=document.querySelector('.bp__ledger');` and inside `if(g){...}`: no top-level
`return` in the map's code, since build.py wraps the whole part in one function. The only
layout read is in the frame callback, once a frame at most.

```js
var g=document.querySelector('.bpg');
if(g){var ns=[].slice.call(g.querySelectorAll('.bpg__n')),xs=[].slice.call(g.querySelectorAll('[data-a]')),T=0,look=0;
  var on=function(id,key){clearTimeout(T);g.setAttribute('data-on',id);
    if(key)g.setAttribute('data-key','');else g.removeAttribute('data-key');
    var near={};near[id]=1;
    xs.forEach(function(x){var a=x.getAttribute('data-a').split(' '),h=a.indexOf(id)>=0;
      x.classList.toggle('on',h);if(h)a.forEach(function(y){near[y]=1})});
    ns.forEach(function(n){n.classList.toggle('on',!!near[n.getAttribute('data-n')])})};
  var off=function(){clearTimeout(T);g.removeAttribute('data-on');g.removeAttribute('data-key');
    xs.concat(ns).forEach(function(x){x.classList.remove('on')})};
  ns.forEach(function(n){var id=n.getAttribute('data-n');
    n.addEventListener('pointerenter',function(e){if(e.pointerType==='mouse')on(id)});
    n.addEventListener('pointerleave',function(e){
      if(e.pointerType==='mouse'&&!n.matches(':focus-visible'))T=setTimeout(off,90)});
    n.addEventListener('focus',function(){if(n.matches(':focus-visible'))on(id,1)});
    n.addEventListener('blur',off)});
  var check=function(){look=0;var r=g.getBoundingClientRect();
    if(!document.hidden&&r.bottom>0&&r.top<innerHeight)g.setAttribute('data-run','');
    else g.removeAttribute('data-run')};
  var soon=function(){if(!look)look=requestAnimationFrame(check)};
  addEventListener('scroll',soon,{passive:true});addEventListener('resize',soon);
  addEventListener('pageshow',soon);document.addEventListener('visibilitychange',check);soon()}
```

Without JavaScript the page has no `.js` class, so the loops simply run; hover is CSS-only then.

## 7. Widths, the phone and the budget

### 7.1 Layout rules

The figure is its own container. From 740px of its width the wide map fills it (up to
`--measure-fig`); below, the tall map, at most 420px wide, starts at the page's left edge like
every block on the page. Text sizes are fixed in viewBox units, so the thresholds follow from
them: at 740px the wide map renders 13 and 12px, and 12.6 units stay 12px down to a 316px
column (a 360px phone).

The tall map, top to bottom: Signal Processing centred; From my research left and Machine
Learning right; the hub; Waves & Dynamics left and Probability & Statistics right; then
Communication left and Python / Programming right, reached by the shared trunk. Wave
Propagation runs down the left edge, System Identification and Optimization take the top
corners, Regression runs down the right edge, and Estimation leaves Signal Processing, passes
left of Machine Learning, crosses its spoke and comes down beside Regression.

### 7.2 Measured (prototype, Chromium, device scale 2)

| Window | Map | Map width | Names | Second lines, words | Pill height |
|---|---|---|---|---|---|
| 1440 x 900, column open | wide | 924px | 16.2px | 15.0px | 55px |
| 1280 x 800 | wide | 924 | 16.2 | 15.0 | 55 |
| 820 x 1180 | wide | 761 | 13.4 | 12.3 | 45 |
| 1024 x 768, column open | tall | 420 of 673 | 17.3 | 16.0 | 58.5 |
| 768 x 1024 | tall | 420 of 709 | 17.3 | 16.0 | 58.5 |
| 390 x 844, phone | tall | 346 | 14.3 | 13.2 | 48.2 |
| 360 x 800, phone | tall | 316 | 13.0 | 12.1 | 44.0 |

No word touches a word, a pill or the hub; no line crosses a word but its own or a pill but
its ends; every line of text has at least 13px of room each side inside its pill (19.6px at
1440); no horizontal scroll at 390 or 360.

| Main thread, 2s windows | Layouts a second | Style recalculations a second | Time |
|---|---|---|---|
| Today, map on screen | 121 | 60 | 72 to 77ms a second |
| This spec, map on screen, list not yet scrolled through | 0 | 60 | 21 to 31ms |
| This spec, map on screen, list scrolled through once | 0 | 0 (3 loads of 4) | about 1ms |
| This spec, map off screen | 0 | 0 | |

The 60 recalculations that remain belong to `theme.py`'s reveal observer, which holds the
list's unrevealed groups (see 11.2); in isolation every loop here runs on the compositor.

## 8. The list (R1, R2)

- Probability & Statistics: its one row is the deck: title "Probability, statistics and
  estimation", note "Opens with a big-picture map of the subject.", pill with the slides glyph
  and "73 slides", `href="probability-statistics.html"`, `data-for="probability-statistics"`
  (so the arrival wash plays on it), `--i:0`. No "In preparation" row any more.
- From my research: the three documents as today, then the deck: "Extensive ppt regarding my
  MSc and PhD Research", note "The master's and PhD work, in more depth.", "177 slides",
  `href="presentation.html"`, `--i:3`, no `data-for`.
- A deck row is a document row in every other respect: `.bp__read`, `.bp__title` through
  `_title()`, `.bp__note`, `.bp__meta`, the arrow. The slides glyph, in the pill's 24-unit
  family (stroke 1.7, as the page glyph):

```html
<svg viewBox="0 0 24 24" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2.5 4h19M4 4v11a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V4M12 16v3M8.5 21.5 12 19l3.5 2.5"/><path d="m8 12 2.5-2.5 2 2L16 8"/></svg>
```

- Python / Programming and Communication keep their rows in preparation, unchanged.

## 9. Copy

His words, verbatim: "Probability, statistics and estimation" (slide 1 of his deck, the
title of its page); "Extensive ppt regarding my MSc and PhD Research" (the title of its page);
the five bridge words, each found in his texts as 2.3 shows.

Ours, short and plain, no em dash, no spaced en dash:
- caption: "Each dotted line names a concept that two topics share. Choose a topic to go to its
  documents and slides." ("concept" is his motivation's word)
- notes: "Opens with a big-picture map of the subject." (slides 2 and 3 of his deck are that
  map and how to read it); "The master's and PhD work, in more depth." (his research text says
  the presentation "walks through my master's and PhD work in more depth")
- the second lines of 2.2, the accessible names, and the hidden list's "<word>, shared by <A>
  and <B>."
- unchanged: the map's topic names, "From my research", "In preparation", "Map of the topics".

## 10. Acceptance checks

For a verifier with Python Playwright (headless Chromium), on `big-picture.html` of a
`--strict` build in its own out dir. Phones run with `is_mobile` and `has_touch`. The prototype's
scripts do most of this and can be adapted: `check.py` (geometry), `interact.py` (states),
`budget2.py` (main thread), `arrive.py` (pausing), in
`C:/Users/lenovo/AppData/Local/Temp/claude/C--Users-lenovo-Documents-wavesanddata/4137cc92-ccc8-4f7d-9c0a-954fbd3b649b/scratchpad/wf/judge/`.

1. The build report lists `documents` among the parts and prints `em dash: 0 (build.py 0,
   parts 0); spaced en dash: 0`, `private: 0`, `baglanti: 0 kirik` and `links into a document:
   0`. (Today the run exits 1 on the site-size line alone, `!! site 42.21 MB`, from the deck
   images; any other `!!` line is a failure.)
2. `documents.CSS` holds no hex colour (`#[0-9a-fA-F]{3,8}\b`), no `rgb(` or `hsl(`, no U+2014
   and no spaced en dash; `documents.JS` holds no `IntersectionObserver` and no `return` before
   `var bp=`; the page holds no `animateMotion`.
3. `documents.DECKS` equals 2.1 and `DECKS` is in `__all__`; the six ids, labels and `short`
   are unchanged; the probability entry has `soon` None and `decks`
   `["probability-statistics.html"]`.
4. `render_big_picture()` has exactly two `bp__read--soon` rows (`python-programming.html`,
   `communication.html`); one row to `probability-statistics.html` with
   `data-for="probability-statistics"`, "Probability, statistics and estimation" and
   "73 slides"; the research group's fourth row goes to `presentation.html` with "Extensive ppt
   regarding my MSc and PhD Research" and "177 slides".
5. `render_big_picture(decks={"probability-statistics.html": ("T", "N", 5)})` shows
   "5 slides", has no link to `presentation.html`, and names the research node
   "From my research, 3 documents".
6. Two `.bpg__stage` (wide, tall), each with an `aria-hidden` `.bpg__back`, an `aria-hidden`
   `.bpg__loops` holding two rings and five runs, and a `.bpg__front` (`role="group"`,
   `aria-label="Map of the topics"`) holding seven `a.bpg__n` in the order of 2.2, with
   `href="#<id>"` and the accessible names of 2.2; `bpg__n--soon` on python-programming and
   communication only, and no run for them; five `.bpg__w` with the words of 2.3 in order; the
   hidden list's five items; the caption exactly as in 9.
7. At 1440 x 900 the wide stage shows and the tall one is `display:none`; names render at 16px
   or more, second lines and words at 14.9px or more; pills are 54px tall or more.
8. At 390 x 844 and 360 x 800 the tall stage shows; every text in its front SVG renders at 12px
   or more (names 13px or more); every pill is 44px tall or more;
   `document.documentElement.scrollWidth <= innerWidth`.
9. At 1440, 820, 390 and 360: no word's box meets another word's, a pill or the hub disc; no
   `.bpg__e` passes through a word other than its own or a pill other than its two ends
   (sampled every 1px along `getTotalLength()`); every text has 12px or more of side room in
   its pill.
10. Keyboard, 1440: focus the `h1` (`tabindex=-1`), then Tab seven times: focus visits the
    nodes in the order of 2.2; each has `outline-style: none` and its `.bpg__f` at opacity 1;
    `.bpg` carries `data-on=<id>` and `data-key`; tabbing out of the map removes both.
11. Mouse, 1440, 3s after load: over signal-processing, `.bpg__n.on` is exactly
    {signal-processing, research, machine-learning, probability-statistics}, `.bpg__w.on` is
    {System Identification, Optimization, Estimation}, `.bpg__run.on` is its own run; over
    probability-statistics the lit words are {Regression, Estimation}; over python-programming
    only it is lit and no word; unlit pills settle at opacity .45; 400ms after leaving there is
    no `data-on`.
12. Touch, 390: a tap on signal-processing sets `location.hash` to `#signal-processing` and
    leaves no `data-on`. Mouse, 1440: a click on machine-learning sets `#machine-learning`, and
    after a pointer move there is no `data-on`.
13. About 400ms after load, with the map in view, every `.bpg__run i` centre is at the hub's
    centre; 4s after load at least one lies outside the hub disc.
14. Load `big-picture.html#python-programming` at 1440 (the map above the window): after 2.5s
    `.bpg` has no `data-run`, `.bpg__ring` and `.bpg__run` are `animation-play-state: paused`,
    and the spokes are drawn (`stroke-dashoffset: 0px`); scroll to the top: within 300ms
    `data-run` is set and both run.
15. Main thread (CDP `Performance.getMetrics`, 2s windows, 1440): map on screen 4s after load,
    `LayoutCount` grows by 0; map scrolled out of view, `LayoutCount` and `RecalcStyleCount`
    grow by 0.
16. Reduced motion: `.bpg__loops` is `display:none`; every spoke has `stroke-dashoffset: 0px`;
    every word has opacity 1; `document.getAnimations()` holds nothing inside `.bpg`.
17. Dark (`document.documentElement.dataset.theme='dark'`): hub text fill `rgb(19, 17, 15)` on
    hub fill `rgb(240, 148, 88)` (8.1:1); `.bp__reads` computes to an `oklch()` colour with a
    lightness under .25 (today's `#fff` mix is about .55); in light it stays at .99.
18. Forced colours (`emulate_media(forced_colors="active")`): pill edges and texts CanvasText;
    `.bpg__loops` hidden. Print (`emulate_media(media="print")`): `.bpg` is `display:none`.
19. `big-picture.html#probability-statistics`: the probability group is in view with its rail,
    and its deck row's `::before` plays `bp-wash`.
20. `bpnav.categories()` still gives the six categories in order, the probability one with the
    page `probability-statistics.html`.

## 11. Outside documents.py (for the orchestrator)

1. `bpnav.categories()` reads only `soon` and `docs`. With the probability entry's `soon` None
   and `docs` empty its page list is empty, so it falls back to its own copy (`FALLBACK`),
   which today is the same list, so the column is right and its tests pass. One line in
   `parts/bpnav.py` should add `c.get("decks")` to the pages; not part of this work.
2. `theme.py`'s reveal script keeps an IntersectionObserver on the list's groups until each has
   been revealed; while it holds one, Chromium runs a main-thread frame at every vsync whenever
   anything animates (RM-3). That is the 60 recalculations a second in 7.2. The look on scroll
   that `heroart.py` uses would make the page idle.
3. build.py renders `big-picture.html` before its deck loop counts the slides; to pass real
   counts (R3) it has to count first.
4. `--strict` exits 1 today on the site-size line from the deck images, not on this page.
5. `parts/documents.md` still describes round 5 (ten categories); it is not this work's file.
