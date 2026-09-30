# Round 10 (27 Sep 2026): the brief every agent reads first

wavesanddata.com is the academic site of Dr. Korkut Kaynardag (civil engineering, waves,
SHM/NDT, data analytics).

- **The site.** A static Python generator: `site/build.py` plus `site/parts/*.py`. Each part
  holds CSS and JS strings and render functions. The build publishes `site/dist`.
- **The client.** He asked for this round in Turkish, in these words: every page at the
  level of an advanced motion designer, "mükemmel", professional first, Apple-quality. He
  asked us to use every design and motion skill.
- **Your job.** Your own brief says what you own. This file says how everyone works.

## Load these skills before you design

Load them with the Skill tool, using the exact names below. Read what applies and follow it.

- **`motion`** (motion.dev's own kit, in `.claude/skills/motion`). Read its
  `best-practices/` first. What it says:
  - CSS or Motion: pick the simplest tool that works cross-browser.
  - Springs are for physical motion; there is no overshoot on a serious site.
  - Every animation must show a change of state, a relationship, or feedback, never
    decoration alone.
  - Keep UI animations to 150 to 300 ms, and up to 500 ms for large surfaces.
  - Animate transform, opacity, clip-path and filter only.
  - Respect reduced motion.
- **`apple-design`** and **`emil-design-eng`**: Apple-level interaction and animation craft.
- **`improve-animations`**, **`review-animations`**, **`animate`** and
  **`find-animation-opportunities`**: use these where your brief is about motion.
- **`impeccable:impeccable`** and **`ecc:taste`**: visual quality and taste. Load one of
  them.

Motion's hosted MCP server (docs search) is not loaded in this session. The skill's
`best-practices/` folder works on its own, so rely on it.

## The site's rules (they bind; the client rejected work that broke them)

- **The binding documents.** `site/design/DESIGN_BRIEF.md` binds. `site/design/CONTRACT.md`
  binds on semantics, keyboard, reduced motion and size. Read DESIGN_BRIEF section 4, "Motion
  and the hover vocabulary". It bans, permanently:
  - `transform:translateY` on hover;
  - any box-shadow change on hover;
  - any hue change on hover.

  Every hover rule sits inside `@media (hover:hover)`, and `:focus-visible` stays outside it.
- **Tokens.** They live in `site/parts/theme.py`.
  - Travel uses Motion's springs, `var(--spring-quick|fast|mid|draw|slow)`. Each one is a
    whole transition value: `transition: transform var(--spring-mid)`.
  - Colour and opacity use `var(--t-*) var(--ease-state)`.
  - Colours come only from tokens: `--ink`, `--body`, `--muted`, `--accent`, `--link`,
    `--nav`, `--page`, `--card`, `--surface`, `--rule`, `--line`, `--line-strong`, `--wash`.
    Do not add raw hex in parts.
- **Reduced motion.** Every animation is enhancement inside
  `@media (prefers-reduced-motion:no-preference)`, or is guarded in JS. The end state
  survives and the travel does not.
- **His words are verbatim.** The professor's text (`PROF_*` blocks in `build.py`,
  document text, his slide text) is never reworded. Our own copy is short, and it never
  contains an em dash (U+2014) or a spaced en dash. `python site/build.py --strict` fails
  on those, on broken links, and on privacy. The only public email is
  korkutkaynardag@iyte.edu.tr; never publish another email address or a phone number.
- **Performance.** Pause loops that are off screen. Put no work in scroll handlers that a
  CSS scroll timeline or an IntersectionObserver can do. Keep canvases DPR-capped at 2.
- **Accessibility.** Keep semantics, keyboard reach and focus rings, and give meaningful
  alt or aria text.

## How to work alongside each other

- **Only touch your own files.** Your brief lists them. Many agents are working at once,
  and `site/` has no git history to recover from. If you truly need a change in a file you
  do not own, stop and say so in your final report; do not make it.
- **Build to your own folder:**
  `python site/build.py --strict --no-word --out build/r10-<you>/dist`, then serve that
  folder on your own port: `python -m http.server <port> --bind 127.0.0.1 --directory ...`.
  Use a port from 8971 to 8999; the controller uses 8960.
- **Tests.** Run `python -m pytest -q`. Update or add tests for your own parts only. Tests
  for files you do not own may fail because of others' work in progress; say so, and do
  not "fix" them.
- **Look at your work.** Use Python Playwright: screenshots at 1440×900, 1100×900 and
  390×844, and frames at several moments of every animation. Read the PNGs and iterate
  until it is excellent, not just working.
- **No git commits.** Do not publish to Wix; the controller publishes.
- **Your final message** is at most 150 words: what changed, the files you touched, how
  you verified it, and anything unfinished or needing a decision.
