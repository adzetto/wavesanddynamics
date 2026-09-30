# Round 15 (29 Sep 2026): the "thinking orb" and micro-interaction language, site-wide

Read these first:

- `tools/ROUND10.md`: the agent rules (own files, own build folder, no commits, no
  publishing), the skills to load, DESIGN_BRIEF's hover bans, tokens, and reduced motion;
- `tools/ROUND11.md`: the professor's rule that the reader grasps it at once;
- `site/parts/bpnav.py`: the column's Big Picture row. It is the reference implementation of
  the language this round spreads.

## The client's words

"o repolardaki şeyleri big-picture.html burada da yap. sol paneldeki fotoğrafa ve big picture
kısmındaki animasyona yap, daha hızlı yap ayrıca onu. [Motivation] buradaki 1,2,3,4 kısmına
da güzel şeyler yapsın. index.html buradaki headerdaki animasyonlar vs güzel ama çok stylish
clear güzel olsun."

In English, do the things from those repos in these places:

- the Big Picture page;
- the photo in the left panel;
- the column's Big Picture animation, which should also get faster;
- the Motivation section's items 1, 2, 3, 4.

The header animation on the home page is nice, but it must be very stylish, clear and
beautiful.

"Those repos" are:

- https://rareformlabs.github.io/thinking-orbs/: tiny orbs of dots on a sphere that rotate and
  change shape per state (Solving, Thinking, Searching, Listening, Composing, Shaping), with a
  shimmer across their label. Frames are in `ref_orbs.png`, under
  `C:\Users\lenovo\AppData\Local\Temp\claude\C--Users-lenovo-Documents-wavesanddata\4137cc92-ccc8-4f7d-9c0a-954fbd3b649b\scratchpad\`.
- https://reactbits.dev/c/micro/: micro-interactions such as Branched Menu, Thought Line,
  Lattice Loader, Status Mark, Spring Check, Comet Dial and Flip Card. Take ideas, never code.

The column row (bpnav.py) already speaks this language: a warm point runs bead to bead, and
each bead becomes a spinning Fibonacci-sphere dot-orb and settles. Reuse its orb renderer's
approach and look, so the whole site shares one orb. If you need its code, copy the minimal
part into your own file rather than editing bpnav.py; only agent "column" edits that file.

## Binding

- **Serious academic site.** Exquisite, calm, clear. Motion must mean something: a topic is
  thinking, a connection is travelling, a point is arriving. No busy loops.
  - Intros take 1 to 2 s, then rest.
  - Replay on hover or focus.
  - At rest there is no requestAnimationFrame.
- **Colours from tokens.** Figures and animations avoid orange (the client disliked it in
  animations).
  - On paper, use the blues and inks.
  - On the navy column, use `--nav-ink` and `--nav-mute`. The column's existing warm mark,
    `--accent-on-nav`, may stay for its "you are here" and chevron roles only.
- **Performance and access.**
  - Canvas at DPR 2 at most.
  - Pause when hidden or off screen.
  - Reduced motion shows the final state.
  - Forced colours and no-script degrade cleanly.
  - Keyboard and screen readers behave as today.
- **Verify.**
  - Build with `python site/build.py --strict --no-word --out build/r15-<you>/dist`.
  - Take Playwright frames every 100 ms of the intro and the interactions, at 1440×900 DPR 2
    and 390×844.
  - Read them and iterate.
  - Update your tests, then run `python -m pytest -q`.

## Ownership

- **bporbs**: `site/parts/documents.py`, `tests/test_bigpicture.py`.
- **column**:
  - `site/parts/bpnav.py`, `tests/test_bpnav.py`;
  - the identity block's photo rules (`.id` in `site/parts/theme.py`: only the photo and its
    ring or halo, nothing else), with a test.
- **motivation**: `site/parts/motivation.py` and the test that covers it.
  - His words are verbatim (`PROF_MOTIVATION` in build.py; do not edit build.py).
- **masthead3**: `site/parts/masthead.py`, `site/parts/masthead.md`, `tests/test_masthead.py`.

Final message: at most 150 words.
