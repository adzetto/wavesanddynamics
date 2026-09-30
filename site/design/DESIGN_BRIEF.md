# DESIGN BRIEF — wavesanddata, round 2

Binding. Where this file and `CONTRACT.md` disagree, this file wins on palette, type,
radius, motion values and icon stroke. `CONTRACT.md` still binds on scoping, deliverable
shape, semantics, keyboard access, reduced motion and the Wix size limits.

Every number here was measured by me, in Chromium at 1440×900 against the current build, or
computed from the sRGB/OKLCH formulas. Nothing is recalled. Where a value came from a
researcher I kept it only after re-deriving it.

The tokens are already shipped in `parts/theme.py`. It is loaded first by `build.py`, so it
overrides `style.css`. It builds clean: `python build.py` → `parts: theme, hero, topics,
rboxes, gallery, about`.

---

## 0. The diagnosis, in one paragraph

The page does not read as an airy researcher's site for three measured reasons, and none of
them is a shortage of whitespace. **One:** the body was Inter 16.5px in a 749px column,
which I measured at **101.7 characters per line** — over Butterick's 90, Baymard's 80 and
WCAG 2.2 SC 1.4.8's 80. The cause is `.col{max-width:72ch}`; `ch` is the advance of the
digit zero, not of a character. **Two:** the two saturated colours were Microsoft Office's
stock defaults, darkened, and the blue sat at OKLCH hue 233.8, outside the 238–255 band that
Oxford, Yale, Nature and Distill occupy — on the cyan side. **Three:** the active-page
marker was `#80350E` on `#104862`, **1.14:1**, a flat WCAG 1.4.1 and 1.4.11 failure, and the
nav hover went *darker* than its base so a hovered row receded. Fix the measure, the hue and
the states and the page breathes. It is not a padding problem.

---

## 1. Colour

Generated in OKLCH at a pinned hue, chroma clamped into sRGB. Never hand-tune a hex, and
never derive a colour by scaling luminance — that is how `#104862` and `#80350E` lost 20%
and 31% of their chroma.

Three hue families and no more: **paper and ink at H 75–80**, **the column at H 248**, **the
accent at H 52**.

### 1.1 Light

| token | hex | OKLCH | job |
|---|---|---|---|
| `--page` | `#FBF9F6` | .983 / .0045 / 78 | the paper. 81% of every page's pixels |
| `--surface` | `#F6F3EF` | .965 / .0062 / 75 | faintly raised band |
| `--card` | `#F2EFE9` | .953 / .0086 / 85 | card fill |
| `--wash` | `#FEEBDB` | .951 / .0297 / 63 | faint amber wash |
| `--rule` | `#E5E1DB` | .911 / .0092 / 78 | hairline separator |
| `--line` | `#D7D2CA` | .866 / .0122 / 80 | surface border |
| `--line-strong` | `#8A857C` | .618 / .0146 / 82 | **the only border that is an affordance** |
| `--ink` | `#27221C` | .255 / .0133 / 72 | headings |
| `--body` | `#544F48` | .430 / .0131 / 77 | body copy |
| `--muted` | `#6F6A64` | .527 / .0112 / 73 | captions, secondary |
| `--nav` | `#043052` | .300 / .0762 / 248 | the column |
| `--nav-hover` | `#104169` | .365 / .0857 / 248 | **lighter** than `--nav` |
| `--nav-press` | `#002341` | .251 / .0690 / 249 | pressed |
| `--nav-deep` | `#001C35` | .221 / .0599 / 248 | reserved, deepest step |
| `--nav-ink` | `#FFFFFF` | — | label in the column |
| `--nav-mute` | `#C3CDD5` | — | secondary text in the column |
| `--accent` | `#A5510B` | .530 / .1319 / 52 | **warm ink on paper. The only warm that carries text on the page** |
| `--accent-2` | `#E7813B` | .704 / .1501 / 52 | **warm mark on the column. Never text on paper (2.4:1 there)** |
| `--accent-hover` | `#904607` | .479 / .1195 / 52 | filled-button hover |
| `--accent-press` | `#7B3D0C` | .432 / .1032 / 52 | filled-button press |
| `--link` | `#095A94` | .456 / .1173 / 248 | no longer the same hex as `--nav` |
| `--link-hover` | `#004170` | .367 / .0992 / 248 | |
| `--focus` | `= --nav` | — | ring everywhere except inside the column |
| `--btn-fg` | `#FFFFFF` | — | label on a filled amber button |

Legacy names kept and repointed so nothing breaks: `--soft` → `--surface`; `--nav-2` →
`--nav-hover` (its only live consumer is the sidebar hover, which must lighten);
`--active` → `--accent` (numerals, timeline dates, small marks — it is **no longer** the
active-nav fill); `--accent-on-nav` → `--accent-2`, so the call site says what it means.

### 1.2 Dark

`#13110F` page · `#1E1B18` surface · `#272420` card · `#322218` wash · `#322E2A` rule ·
`#423E38` line · `#7B756E` line-strong · `#EBE7E2` ink · `#C1BDB7` body · `#928E88` muted ·
`#12304A` nav · `#1D4161` nav-hover · `#0B243A` nav-press · `#081C2F` nav-deep ·
`#C6CDD4` nav-mute · `#F09458` accent · `#FDA670` accent-2 · `#FFA971` accent-hover ·
`#DA8249` accent-press · `#69A5DE` link · `#90C1F1` link-hover · `--focus = --link` ·
`--btn-fg #13110F`.

Two things **flip** rather than darken. The link goes light, following Carbon's blue 60 →
blue 40 pattern. And the button label flips to dark, because white on any amber light enough
to be seen on a `#13110F` page lands near 3.3:1 and fails — that is what `--btn-fg` is for.

### 1.3 Every ratio I computed

Light (WCAG 2.x, sRGB relative luminance):

```
ink / page              15.00   body / page              7.72   muted / page        5.10
muted / surface          4.84   muted / card             4.67   muted / wash        4.62
body / card              7.07   body / wash              7.00   ink / card         13.74
link / page              6.89   link-hover / page       10.04   link / card         6.31
accent / page            5.28   accent / card            4.84   accent / wash       4.79
btn-fg / accent          5.55   / accent-hover           6.85   / accent-press      8.35
#fff / nav              13.55   / nav-hover             10.59   / nav-press        15.95
RAIL accent-2 / nav      4.90 [g]   / nav-hover          3.83 [g]
ghost border / page      3.49 [g]   / card               3.20 [g]
focus ring / page       12.89 [g]   / card              11.81 [g]
nav column / page       12.89 [g]
```

Dark:

```
ink / page              15.30   body / page             10.07   muted / page        5.78
muted / card             4.74   body / card              8.26   ink / card         12.55
link / page              7.21   link-hover / page        9.94   accent / page       8.15
btn-fg / accent          8.15   / accent-hover          10.02   / accent-press      6.52
#fff / nav              13.57   / nav-hover             10.60   / nav-press        15.82
RAIL accent-2 / nav      7.02 [g]   ghost border / page  4.14 [g]
focus ring / page        7.21 [g]   / card               5.91 [g]   / nav           5.19 [g]
```

**Nothing under 4.5:1 carries text. Nothing under 3:1 is a meaningful graphic.** Five values
sit below 3:1 on purpose, so nobody "fixes" them later:

- `--line` on page 1.43:1 and `--rule` on page 1.24:1 are decorative. A card is already
  identified by its own fill, so its border is not the sole means of identification and
  SC 1.4.11 does not bite. Where a border **is** the only affordance — text inputs, the
  ghost button — use `--line-strong` at 3.49:1.
- `--nav-hover` vs `--nav` 1.28:1 and `--nav-press` vs `--nav` 1.18:1 are state changes on
  one surface. WCAG sets no ratio for those. What matters is that the white label stays over
  10:1 in all three states, which it does.
- Dark `--nav` vs dark `--page` is **1.39:1**. That is inherent to "deep blue column on a
  dark page" — the old pair was 1.50:1, so this is not a regression — and it is why
  `theme.py` puts a 1px `--line` right border on `.side` **in dark mode only**. Light mode
  is 12.89:1 and must never get that border.

### 1.4 Three colour rules

1. **Blue means place. Warm means action, and "you are here".** A button is never filled
   with `--nav`. GOV.UK proves the split works: brand blue `#1D70B8`, primary button green
   `#00703C`, deliberately different hues so a button is never mistaken for a piece of the
   header. `.hero2__btn` is still `background:var(--nav)` today — literally the same hex as
   the 240px column and as `--link`, one colour carrying three unrelated meanings.
2. **Derive states, do not invent them.** Hover = one lightness step toward the foreground.
   On the dark column that means **lighter**. On paper it means **darker**.
3. **Never use `--accent-2` as text on paper** (2.4:1) and **never use `--accent` as a mark
   on the column** (2.44:1). That is Radix step 9 versus step 11, and it is exactly why the
   old single `--accent` could satisfy neither job.

---

## 2. Type

### 2.1 The pairing

**Source Serif 4 stays and becomes the reading face. Inter goes. Source Sans 3 becomes the
interface face.** Three reasons, all measured:

- Inter's x-height is **0.546 em** against Source Serif 4's **0.4750 em** — 14.9% apart, so
  set at the same px they are two different sizes and every label beside a heading has to be
  hand-tuned. Source Sans 3 is **0.4780 em**, 0.6% off. Adobe drew Source Serif as the
  companion to Source Sans; the metrics show it.
- **Inter's GSUB has no `onum`.** There are no old-style figures in it at any weight. This
  site is built out of numerals: the About page's `12 / 2 / 8`, six career date ranges, and
  `machine-learning-the-complete-picture-and-guide-5.html` with 18 tables and 62 header
  cells. Source Serif 4 and Source Sans 3 both carry `onum`, `tnum` and `pnum`.
- **Inter set as 16.5px body copy is the AI-site tell, not the serif.** gwern.net — the most
  obsessively typeset technical site on the web — runs `"Source Serif 4"` as its *body* face
  and `"Source Sans 3"` as its UI face. Five of eight admired technical long-form sites set
  prose in a serif. Not one sets serif headings over a sans body, which is what we did.

**The request, verbatim.** Replace the `<link>` at `build.py:403`:

```html
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@600&family=Source+Serif+4:opsz,wght@8..60,400..600&display=swap">
```

Keep the two preconnects at 401–402. I downloaded every woff2 and summed the **unique**
files Google serves:

| request | latin | latin-ext | unique total |
|---|---|---|---|
| current (Inter 400;600 + SS4 400;600) | 190.0 KB | 158.2 KB | **348.2 KB** |
| **ruled** (SS3 600 + SS4 400..600) | 134.8 KB | 130.4 KB | **265.2 KB** |
| SS4 400 only (rejected) | 62.8 KB | 71.9 KB | 134.7 KB |

−83 KB, a 23.8% cut, and in practice **233.3 KB**: Google gates `latin-ext` on
`unicode-range`, and every nav label, eyebrow and column head is ASCII, so the sans's 31.9 KB
latin-ext subset is never fetched.

**Why not the 134.7 KB option.** The site has **428 `<strong>` runs**, 288 of them in the
machine-learning guide alone. Loading the serif at 400 only would synthesize bold on all 428.
Faux bold on a transitional serif at 19px is worse than the 130 KB. Requesting the range
`400..600` costs **byte-identical** to `400;600` — Google serves the same variable file — so
ask for the range and take every intermediate weight free.

Two stacks, nothing else, ever:

```
--serif: "Source Serif 4", Georgia, Cambria, "Times New Roman", serif
--sans:  "Source Sans 3", "Segoe UI", system-ui, -apple-system, sans-serif
```

Georgia is within 1.3% of Source Serif 4 on x-height and 2.1% on width, so the `display=swap`
reflow is close to invisible. Do not reorder Times New Roman ahead of it: it is 5.8% short
and 12% narrow.

**Never disable optical sizing.** The served Source Serif 4 file carries `opsz 8.0–60.0`,
default 20.0, even with the weight pinned. `font-optical-sizing:auto` is set on `body`. Do
not write `font-variation-settings`, which would override it. Optical size and point size —
not weight — carry the refinement at 40px.

**Load no italic.** Source Serif 4 italic 400 is 92.1 KB, more than the entire roman payload.
`.soon`, `.dl.off`, `.find em` and `.doc .ink-m` are already re-set to `font-style:normal` in
`--muted`. Distinguish by size and colour, not by a synthesized oblique.

### 2.2 The scale

Body 19px. **19px Source Serif 4 has a 9.03px x-height against 16.5px Inter's 9.01px**, so
this is not an increase in apparent size — it is a serif at the same optical size with a
bigger number on the ruler. Never ship body copy below 18px on this site.

| role | family | size / line-height | tracking | colour |
|---|---|---|---|---|
| h1 | serif 600 | `clamp(32px,3.4vw,40px)` / 1.12 | −.014em | `--ink` |
| h2 | serif 600 | 28 / 1.22 (34.2px) | −.009em | `--ink` |
| h3 | serif 600 | 23 / 1.30 | −.004em | `--ink` |
| h4 | serif 600 | 19 / 1.35 | 0 | `--ink` |
| lede | serif 400 | 21 / 1.52 | −.004em | `--body` |
| body | serif 400 | 19 / `--lh` | 0 | `--body` |
| figure caption | serif 400 | 16 / 1.50 | 0 | `--muted` |
| table cell | serif 400 | 15 / 1.45 | 0 | `--body` |
| table `th` | **sans 600** | 12 / 1.35 | +.09em, caps | `--muted` |
| eyebrow | **sans 600** | 12 / 1.1 | +.12em, caps | `--muted` |
| nav link | **sans 600** | 15 / 1.40 | +.006em | `--nav-ink` |
| timeline year | **sans 600** | 14 / 1.50 | +.01em | `--muted` |
| button label | **sans 600** | 15 / 1.20 | +.01em | per control |
| sidebar wordmark | serif 600 | 19 / 1.25 | −.004em | `--ink` |
| sidebar affiliation | **sans 400** | 12 / 1.50 | 0 | `--muted` |
| footer | serif 400 | 14 / 1.60 | 0 | `--muted` |

The rule to state to every designer: **serif is the professor's voice, sans is the
interface's voice.** Nothing is set in a family the rule does not assign.

**Weights are monotonic.** h1, h2, h3 are all 600; body is 400. The old h1 was
`font-weight:400` at 40px while h2 was 600 at 25px, so the larger heading was lighter than
the smaller one. `.hero2__h1` still carries the 400 — I measured it at `fontWeight:"400"` on
the live index. Hero designer: drop it.

**Heading rhythm.** h2 `margin:47px 0 21px` — **2.24:1**, against 62.5/15 = 4.17:1 before.
h3 `margin:34px 0 14px` = 2.43:1. Never exceed 2.5:1. A heading floating 62px from what
precedes it and clamped 15px onto what follows makes holes, then density; that is what read
as "gappy, not airy". References: Anthropic 2.0:1, Works in Progress 2.5:1, Tufte 1.5:1.

**The leading ladder**, gwern's technique — the wider the screen, the more leading a line
needs: `--lh` is 1.50 up to 649px, 1.55 from 650px, 1.60 from 1200px. Body copy only, never
headings.

### 2.3 Measure

**Delete every `ch` width in the codebase.** Already done in `theme.py` for `.col`, `.lede`,
`.introlist`, `.pending`, `.toc`, `.rows`, `.tl`, `.doc .docrule`, `figure`, `.callout` and
`.stats span`. Two remain for their owners: `parts/about.py:97,99` (`62ch`) and
`parts/hero.py:47` (`62ch`) — replace with `var(--measure)`. `parts/gallery.py:33`'s `12ch`
is a grid column, not a measure, and may stay.

```
--measure      608px   prose
--measure-wide 720px   lists, tables, timelines — not prose
--measure-fig  924px   figures breaking out
```

Measured in Chromium, Source Serif 4 400 at 19px in 608px: average advance **8.63px**, line
box **30.02px**, **70.5 characters per line**. On the rebuilt pages I measured 72 on index
and 64.5 on research. The admired band is 68–84. We were at 101.7.

`--measure-fig` needs markup, not a token: inside a `.col` clamped to 608px a figure cannot
exceed it. The doc designer breaks out with
`width:var(--measure-fig); max-width:calc(100vw - var(--side) - 96px); margin-left:calc((var(--measure) - min(var(--measure-fig), 100vw - var(--side) - 96px))/2)`.
The contrast between a 608px text column and a 924px figure is what gives the document pages
their rhythm, and it is how gwern.net and distill.pub handle the same problem.

### 2.4 Numerals — three settings, applied by role

Inter could do none of them.

- Body prose (`body`, already set): `oldstyle-nums proportional-nums`. A year inside a
  sentence sits on the x-height instead of shouting at cap-height.
- Table cells and `.tl time` (already set): `lining-nums tabular-nums`, so the right-aligned
  year column aligns digit to digit.
- `.glance__n` (about designer): `lining-nums proportional-nums`, **not** tabular. The
  current tabular setting pads the single-digit `2` and `8` with sidebearing so they do not
  hug the card's left edge the way `12` does.

`-webkit-font-smoothing:antialiased` is removed from `body` and applied only to `.nav a`. It
thins strokes on macOS, which helps white-on-navy labels and hurts 19px dark-on-light serif.

---

## 3. Space, radius, elevation

Spacing stays on the 4 grid: 4 8 12 16 20 24 32 40 48 64 80 96.

**Two radii on the whole site.** `--r-sm`, `--r-md` and `--r-lg` are all **8px**; `--r-pill`
is 999px. Five radii appeared on the homepage (10, 14, 20, 999, 50%); 20px is the SaaS look
and 50% goes with the sidebar avatar. Any hardcoded radius becomes 8px or 999px — that
includes `figure img` (4px), `.callout` (4px), `.toc` (8px) and `.box` (12px) in `build.py`.

Shadows are warmed to the new ink and reduced: `--sh-1: 0 1px 2px rgba(39,34,28,.04)`,
`--sh-2: 0 1px 2px rgba(39,34,28,.04), 0 8px 24px rgba(39,34,28,.06)`,
`--sh-3: 0 2px 4px rgba(39,34,28,.05), 0 16px 40px rgba(39,34,28,.08)`. They exist for rest
states only. **No hover changes a shadow.**

**Do not add padding to make the page airier.** I measured blank scanlines inside the text
column: ours 48.5% on index and 52.7% on research, against gwern 55.2% and MIT Media Lab
45.9%. We are inside the normal band. Fix the measure, the type size, the heading ratio and
the states, then re-measure before touching a single padding value.

---

## 4. Motion and the hover vocabulary

```
--t-quick 120ms   --t-fast 160ms   --t-mid 240ms   --t-slow 420ms
--ease        cubic-bezier(.2,.8,.2,1)    motion: things that travel
--ease-state  cubic-bezier(.2,0,.38,.9)   state: things that change colour (Carbon productive)
--ease-in-out cubic-bezier(.4,0,.2,1)
```

I measured Our World in Data's 618 KB stylesheet: **298 hover rules and zero instances of
`translateY` on hover**, with one card rule explicitly setting `box-shadow:none` on hover.
Docusaurus washes menu items with a 5.1% black overlay. Carbon's `moderate-01` is 150ms,
documented as the default for "micro-interactions… short distance movements". Anthropic moves
link colour and `text-decoration-color` together over 200ms and nothing else. Tufte CSS
changes nothing at all on hover.

**The vocabulary, and it is closed:**

| target | rest | hover | duration |
|---|---|---|---|
| body link | `underline`, thickness 1.5px, offset 3px, `text-decoration-color: color-mix(in oklab, currentColor, 62% transparent)` | `text-decoration-color: currentColor` | 160ms `--ease-state` |
| whole card | transparent fill, 1px `--rule` top hairline | fill `color-mix(in oklab, var(--ink) 4%, var(--page))` = `#F6F4F1`; the card's title gains a 1px underline at 4px offset | 120ms `--ease-state` |
| list row | transparent | fill `color-mix(in oklab, var(--ink) 5%, var(--page))`, bled 12px past the text with `margin-inline:-12px; padding-inline:12px` so it reads as a row, not a box | 120ms |
| nav row | transparent over `--nav` | `--nav-hover`; the 3px rail scales in | 120ms colour, 160ms rail |
| ghost button | 1px `--line-strong`, `--ink` label | fill `--card`, border darkens one step | 160ms |
| filled button | `--accent`, `--btn-fg` | `--accent-hover`; press `--accent-press` | 160ms |

**Banned, everywhere, permanently: `transform:translateY` on hover, any `box-shadow` change
on hover, and any hue change on hover.** Those three are the SaaS-template reflex the
evidence rejects, and they are what `.topics__card`, `.rboxes__card` and `.box` all do today.

Every hover rule goes inside `@media (hover:hover)`. Every `:focus-visible` rule stays
outside it. Touch devices must never hold a stuck hover; keyboard feedback must never be
suppressed.

**Focus ring:** `outline:2px solid var(--focus); outline-offset:2px`, except inside the navy
column where it is `2px solid var(--nav-ink); outline-offset:-4px`, inset so the ring never
clips on the column edge. Stop writing `outline:2px solid var(--nav)` — in dark mode that is
**1.21:1**, an invisible focus ring, and it is currently in `build.py`, `about.py`,
`rboxes.py` and `topics.py`. `theme.py` ships a shim that corrects `outline-color` in dark
mode; delete the shim once every module uses `var(--focus)`.

### 4.1 The arrow on My Research Areas

The client asked for this by name. `translateX(3px)` over 160ms is below the perceptual
threshold, which is why it reads as nothing. Draw the arrow as **two paths** and animate
both:

```html
<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
     stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
  <path class="ar-shaft" d="M3.5 12h13"/>
  <path class="ar-head"  d="m11.5 6.8 5.2 5.2-5.2 5.2"/>
</svg>
```

```css
.ar-shaft{stroke-dasharray:13;stroke-dashoffset:9;
  transition:stroke-dashoffset 240ms cubic-bezier(.2,.8,.2,1)}
.ar-head{transition:transform 240ms cubic-bezier(.2,.8,.2,1) 60ms}
@media (hover:hover){
  a:hover .ar-shaft,a:focus-visible .ar-shaft{stroke-dashoffset:0}
  a:hover .ar-head,a:focus-visible .ar-head{transform:translateX(5px)}
}
@media (prefers-reduced-motion:reduce){
  .ar-shaft{stroke-dashoffset:0;transition:none}
  .ar-head{transition:none;transform:none}
}
```

The shaft draws itself left to right over 240ms while the head slides **5px** — matching
Works in Progress's `transform:translate(5px)` on its read-more, which is the smallest travel
I found that actually reads. The head is staggered 60ms behind the shaft so the eye follows
the line and then the point. Under `prefers-reduced-motion` the shaft is drawn and the head
is home: **the end state survives, the travel does not.** This is the shape the whole site
uses for reveal-style motion — enhancement through the media query, never motion by default
that a query has to claw back.

---

## 5. The sidebar

### 5.1 The duplicated portrait — ruling

**Remove the photograph from the sidebar on all nine pages. Keep it in the hero.** `theme.py`
already hides it with `.id img{display:none}`, but Chrome still downloads a `display:none`
image, so that is a stopgap: delete the `<img>` at `build.py:415` and stop emitting
`headshot.webp` at `build.py:740`.

Reasons, in order of weight:

1. **Cost accounting.** The rail is chrome on nine pages; the hero portrait is content on
   one. Spending 88px of persistent chrome on every page to fix a duplication that occurs on
   two is the wrong trade. NN/g measured a site whose vertical navigation gave a 5:1
   content-to-chrome ratio against 12:1 horizontal — vertical navigation has already spent
   the budget.
2. **86px is the dead zone** — too small to read as a portrait against a busy brick wall, too
   large to read as a mark. It commits to neither job.
3. **Every content-first site with a persistent rail that I could fetch uses a wordmark.**
   Wikipedia Vector 2022 puts `mw-logo-wordmark` at 8.75em × 1.375em in the pinned menu.
   gwern.net's rail identity is `<a class="logo">`. Docusaurus carries navigation only.
   anthropic.com/research serves one `<img>` on the whole page. karpathy.ai shows one
   240×240 circle and has no rail at all.
4. **The only pattern that repeats the author portrait is Hugo Blox / Wowchemy's academic
   demo, which serves the same face nine times on its homepage** — precisely the template
   look the client called generic. Minimal Mistakes, the most-forked academic theme, does put
   a 110px avatar in its rail, but it never repeats it in the content column. Even the
   template that endorses a rail avatar does not show the face twice at once.
5. NN/g on redundancy: repeating one element on a page raises UX complexity, because users do
   not recognise duplicates until they have spent time reading them.

**If the professor insists on his face in the chrome**, the only defensible form is a **36px
circle inline to the left of the wordmark**, from a square 72×72 re-crop. Against a 280px
hero portrait that is a 7.8× size difference, which nobody reads as a duplicate. An 86px
block above the wordmark is not that.

**The replacement `.id` block** (shipped): name in `--serif` 600 19/1.25, a 28×2px `--accent`
rule 12px beneath it, then affiliation in `--sans` 400 12/1.5 `--muted`, padding
`24px 20px 20px`. Height drops from ~227px to ~148px on every page.

**Change the wordmark string to "Korkut Kaynardag"** and move "PhD" to the first affiliation
line. Two reasons: the rail string and the hero `<h1>` are currently character-identical
240px apart; and I can see in the render that "Korkut Kaynardag, PhD" wraps to two lines in
the narrower column, breaking after the comma. Do not alter any of the professor's own
sentences to achieve this — the wordmark is our furniture.

### 5.2 The column

**`--side` is 240px, down from 264px.** 240px is **16.7% of a 1440px viewport**, which is
exactly the ratio of the column in his own deck (2.23in of 13.33in = 16.73%, or 241px at
1440). The column returns to the width he drew. 264px was 18.3%, and 25.8% at 1024px.

**Keep `.side__end` and keep the navy running to the foot of the viewport.** One researcher
wanted it deleted as "an empty saturated rectangle" and another wanted the identity block
merged into the navy field. I overruled both. `build.py`'s own provenance note records his
deck as *"sidebar … full height / nav block solid accent1"* — a full-height column with the
identity above the solid menu block is his design, not our accident. And I did the
arithmetic: merging the identity into the navy raises the saturated area by **21.6%** at a
900px viewport (177,672 px² → 216,000 px²), which is the opposite of what was wanted. The
column's area problem is solved by narrowing it 9.1% and by the navy being a better navy,
not by moving the seam.

**Labels left-aligned on one hard edge at x=20.** `padding:13px 16px 13px 20px`,
`min-height:44px`, `display:flex; align-items:center`. The 3px rail sits at `left:0`, so all
eight labels share one vertical edge. NN/g names this failure exactly: a left vertical
navigation that "center-aligned the text of each navigation element, creating a jagged edge
that undermined the visual scanning benefit of a vertical list."

**The eight per-row hairlines are gone.** Eight `rgba(255,255,255,.09)` lines across a solid
field make the column read as a stack of buttons. One `--nav-rule` hairline now sits above
item 4 and above item 7, grouping {About Me, My Research Areas, Gallery} · {the three topic
pages} · {Blog, Contact}. **His nav order is not touched** — the three topic pages were
already contiguous.

**States.** Rest: transparent over `--nav`, rail at `scaleY(0)` so nothing shifts. Hover:
`--nav-hover` (**lighter**, white label 10.59:1) and rail to `scaleY(1)`. Current page:
`--nav-hover` fill, rail permanently at `scaleY(1)` (4.90:1 against the column), label weight
600, and the markup must add `aria-current="page"`. Pressed: `--nav-press`. Three cues, only
one of which is colour — SC 1.4.1 satisfied outright. The old full-width rust flood was
1.14:1; even the best warm that can carry white text only reaches 2.44:1 against the navy, so
**the rail is arithmetic, not taste.**

**The long label keeps a `<br>` after each comma.** Change `build.py:39` to:

```python
("signal-processing.html", "Signal Processing,<br>System Identification,<br>Estimation, Optimization", ""),
```

Measured at Source Sans 3 600 / 15px in 204px of available text width: 118.5px / 143.3px /
163.0px — three lines, 41px of slack on the widest. Unbroken the label is **431.0px**. With
the single `<br>` it has today I measured it wrapping to **four** lines at arbitrary points.

---

## 6. The hero

**The About me button is demoted to a ghost control.** I verified on the live page that
`.hero2__btn` still computes to `rgb(4,48,82)` — literally `--nav`. It is the heaviest object
on the homepage, a solid 44px pill at 13.55:1, and it points at the biography, the least
consequential destination on the site. The eye lands on the heaviest thing first; that is the
mechanical cause of the page not feeling airy, more than any gap.

```css
.hero2__btn{background:transparent;color:var(--ink);
  border:1px solid var(--line-strong);            /* 3.49:1 */
  font:600 15px/1.2 var(--sans);letter-spacing:.01em;
  min-height:44px;padding:0 22px;border-radius:var(--r-pill);box-shadow:none;
  transition:background-color 160ms var(--ease-state),border-color 160ms var(--ease-state)}
.hero2__btn:hover{background:var(--card);border-color:var(--ink)}
.hero2__btn:active{background:var(--rule)}
```

Remove `box-shadow:inset 0 0 0 1px rgba(255,255,255,.13)`. A white hairline inside a dark
fill reads as a seam on a light page, not as depth. **Spend the one filled button on the CV
or publications download when it exists**, at `--accent` with `--btn-fg` (5.55:1). If a
filled hero button is non-negotiable, it is `--accent`, never `--nav`.

**The portrait.** Source is 700×683 (1.02:1), so with `object-fit:cover` in a 4:5 box the
crop takes height and trims width only — `object-position:50% 30%`'s Y component has never
had any effect. Delete it. Regenerate `portrait.webp` as a pre-cropped 4:5 at **x=90, y=0,
w=520, h=650**, WebP quality 80, displayed in a **280px** card: head 49% of frame width, eye
line 36% from the top, 1.86× device density. Today's crop puts the head at 47% and leaves too
much brick. Ask whether a higher-resolution original exists — at 440×550 proportions from a
larger source the composition improves materially.

Put the freed 56px into air, not text: second grid column `clamp(216px,28cqi,280px)`, gap
`clamp(40px,6cqi,72px)`, `.hero2__lede` capped at `var(--measure)`.

`.hero2__h1` drops `font-weight:400` for 600, and `.hero2__lede` / `.hero2__p` drop their
16.5px and 18px for the scale in §2.2. The hero module still sets its own type and is the
only place the h1 weight inversion survives.

---

## 7. Icons

### 7.1 The stroke ladder

`CONTRACT.md` fixes `stroke-width="1.5"`. I read that as normative at the **20px inline
size**, where it yields a **1.25px visual stroke**, and derive the rest so the family reads
at one weight. Userspace `stroke-width` is not the constant; *visual* stroke is.

| class | render | `stroke-width` | visual | where |
|---|---|---|---|---|
| inline / UI | 20px | **1.5** | 1.25px | contact rows, arrows, download marks |
| subject | 28px | **1.2** | 1.40px | the three topic icons |
| plate | 56px | **0.75** | 1.75px | the four `.rboxes` icons |

The `.rboxes` plates currently run `stroke-width:1.5` at 56px = **3.5px visual, 2.8× the
inline family**. That single number is why they read as clip art beside everything else. Fix
it and they become drawings.

Everything else holds: `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`,
`stroke-linecap="round"`, `stroke-linejoin="round"`, `aria-hidden="true"` beside a text
label, ≤ 800 bytes, inline only.

### 7.2 Delete the chips and the ordinals

The three 44×44 solid `--nav` rounded squares go. They put six navy objects on one homepage
(column, About pill, three chips, the topic links) and they are the loudest thing in each
card. Draw the icons **at 28px directly on the paper in `--ink`**, with **exactly one
detail per icon in `--accent`** — one envelope, one peak, one boundary.

The rust `01 / 02 / 03` numerals go. The three topics are not a sequence, so the ordinals are
decoration carrying no meaning, which `CONTRACT.md` §3 forbids.

### 7.3 The three replacements

The current glyphs are stock Feather vocabulary and none is specific to the subject: #01 is a
heart-rate squiggle, #02 a generic bar chart, #03 the five-node network used everywhere for
"share". At 24px inside a navy chip the network is a smudge. Draw his actual subject.

These three are drawn, rendered and checked at 112px, 28px and 20px. **The governing
constraint is that an icon carries about four strokes at 28px and no more.** I drew and
rejected two earlier sets on that test: a decaying free-vibration response under its
envelope, and a time trace stacked above its line spectrum. Both read at 112px and became
tangles at 28px. Do not reintroduce them.

**Vibrations and Waves — a wavefront meeting a boundary, and the front that comes back.**
Wave propagation into an interface is the mechanics of NDT, and it is not in any icon pack.
The reflected front is the accent. 290 bytes.

```html
<path d="M19.4 3.2v17.6"/>
<path d="M9.6 7.4a7.2 7.2 0 0 1 0 9.2"/>
<path d="M13.6 5.2a11 11 0 0 1 0 13.6"/>
<path class="i-accent" d="M8.4 8.6a6 6 0 0 0 0 6.8"/>
```

**Signal Processing — an analysis window over a measured trace.** Windowing a signal is the
first move of the whole discipline. The window is the accent. 316 bytes.

```html
<path d="M2.6 12.4 4.6 8.2 6.4 14.6 8.4 6.4 10.4 15.8 12.4 7.2 14.2 14.2 16.2 9.4 18 13.2 19.6 10.4 21.4 12"/>
<rect class="i-accent" x="7.4" y="3.6" width="6.2" height="16.8" rx="1.4"/>
```

The trace vertices are deliberately irregular. A regular zigzag reads as a mountain range,
which is what the first attempt did.

**Machine Learning — a decision boundary between two labelled classes.** Not a neural net.
Hollow circles one class, filled the other — the clearest two-class distinction at 20px — and
the boundary is the accent. 426 bytes.

```html
<path class="i-accent" d="M3.6 20.2C8 18.4 9.4 12 13 8.6c2.6-2.5 5.2-3.6 7.4-4"/>
<circle cx="6.2" cy="11.6" r="1.7"/><circle cx="10.4" cy="5.6" r="1.7"/>
<circle cx="14.4" cy="16.2" r="1.7" fill="currentColor" stroke="none"/>
<circle cx="18.6" cy="11.4" r="1.7" fill="currentColor" stroke="none"/>
```

`.i-rest{opacity:.4}` · `.i-accent{stroke:var(--accent)}`. In dark mode `--accent` is
`#F09458` at 8.15:1 on the page, so the accent detail survives the flip. All three are under
the 800-byte contract limit with room to spare.

**Budget.** Works in Progress ships 12 SVGs on its homepage; Tufte CSS ships zero; Linear
ships 219. The more editorial and text-led the site, the fewer icons. Fewer and better.

### 7.4 Topic cards

Remove the `--card` fill, the border and the shadow. On research.html I measured the old grey
fill at **8.8% of page pixels against 9.1% for every letter of text** — the cards were
competing with the prose at parity. Replace with a **single 1px `--rule` hairline along the
top edge**, generous internal padding (24px 0 20px) and the paper showing through. Keep the
whole card as the hit target. Hover per §4.

Delete `.topics__card::before`'s `linear-gradient(90deg,var(--accent),var(--accent-2))`. A
gradient across 3px of height inside one hue carries no information. The card must not do
five things at once — today it lifts, shadows, wipes a bar, darkens a chip and slides an
arrow.

---

## 8. Copy: the em dashes

The client's instruction is exact and it overrides every researcher who guessed differently:
**the professor's own sentences ship verbatim; the em dashes we introduced are ours to
remove.**

I traced every one. `build.py` carries his transcription under an explicit provenance
comment, and **his own text contains zero em dashes**. There are **18 rendered em dashes**
across the nine top-level pages, not the 11 the source grep suggested.

| # | where | text | verdict |
|---|---|---|---|
| 1 | `parts/hero.py:229` | "the topics I use in my research — on the mechanics…" | **our paraphrase of his `PROF_INTRO`** |
| 2 | `parts/hero.py:234` | "sound target analysis — deployed offline through…" | **our paraphrase of his `PROF_BIO`** |
| 3–4 | `parts/topics.py:121,126` | the two `.topics__desc` lines | ours |
| 5 | `build.py:556` | "Curriculum vitae — coming soon" | ours |
| 6 | `build.py:665` | "the data side of the work — written between…" | ours |
| 7–8 | `parts/gallery.py:96,119` | title-to-note joins | **ours: furniture** |
| 9–11 | `build.py:654` | "based on my own route into the subject — what to read…" ×3 topic pages | ours |
| 12 | `parts/about.py` | `.glance__dash`, `aria-hidden` | **pure ornament** |
| 13–18 | `parts/about.py` | six `.tline__when` date ranges: `2024 — 2026`, `2026 — present` … | **wrong mark, independently** |

**Items 1 and 2 — restore his wording, do not repunctuate ours.** These are paraphrases of
sentences he wrote. His intro is the numbered list beginning *"This webpage introduces you to
followings:"*; his bio reads *"…sound target analysis **which are deployed** off-line through
developed software and tools, cloud data processing or on-board processing via microchips."*
Putting his words back removes both dashes and honours the rule at the same time. Do not
"fix" his grammar — "followings" and "In mechanic and physic side" are his phrasing and ship
as written.

**Items 7 and 8 — a colon, not a dash.** One researcher claimed these are his own document
titles. They are not: `build.py`'s `DOCS` map already writes *"Machine Learning: The Complete
Picture and Guide"* with a colon, and his source filename is
`Machine Learning - The Complete Picture and Guide_5.docx` with a plain hyphen. The `&mdash;`
is `parts/gallery.py` furniture. **Overruled.**

**Items 13–18 — closed-up en dashes.** A range takes an en dash with no spaces:
`2024&#8211;2026`, `2023&#8211;2024`, `2016&#8211;2023`, `2014&#8211;2016`,
`2013&#8211;2014`. This is correct range typography whatever the client had said. Rewrite
`2026 — present` as **"Since 2026"**.

**Item 12** — delete the `<span class="glance__dash">` and its rule. Ornament with no
semantic content; a 12px gap or a 1px `--rule` hairline separates just as well without a mark
we have been asked not to use.

**Everything else** takes a colon, a full stop, a comma, or a restructured sentence:
*"Wave propagation and dynamics: the mechanics and physics side of my research."* ·
*"Curriculum vitae, coming soon."* · *"…based on my own route into the subject: what to read
in what order, and what can safely wait."*

**Add a build-time assertion in `build.py`** that fails the build if any generated HTML
outside the `PROF_` blocks contains U+2014 or `&mdash;`. This has now been caught twice; make
it impossible to regress.

**The email needs no change.** `korkutkaynardag@iyte.edu.tr` in `index.html` and
`contact.html` matches the address supplied, character for character, and it is already the
value in `build.py`'s `CONTACT` dict. Verified.

---

## 9. Bugs that must be fixed

**1. The reveal leaves the homepage's three topic cards permanently invisible.** I reproduced
it: load `index.html`, wait three seconds — well past the 1200ms failsafe — and all three
`.topics__item` elements are still at `opacity:0`. Only scrolling reveals them. A screenshot,
a print, a social preview and any embedded webview that does not scroll get "Explore the
topics" followed by 290px of nothing.

The mechanism is exact: `parts/topics.py`'s JS sets `fired=true` on the *first* observer
callback, but `IntersectionObserver` invokes its callback immediately on `observe()` with
`isIntersecting:false`. The failsafe is disarmed before it can ever help. Fix:

```js
var io=new IntersectionObserver(function(entries){
  for(var n=0;n<entries.length;n++){
    if(!entries[n].isIntersecting)continue;
    fired=true;                       /* only a real intersection disarms it */
    entries[n].target.classList.add('is-in');
    io.unobserve(entries[n].target);
  }
},{threshold:.2,rootMargin:'0px 0px -8% 0px'});
```

**2. `.glance` and `.tline` have no failsafe at all.** `parts.css:368` and `:424` set
`opacity:0` under `[data-anim]` and `parts/about.py`'s JS never adds one. About page content
is lost the same way, with no timeout to rescue it. Add the same guard.
`CONTRACT.md` §4: *"a reveal must never leave content invisible if the observer never
fires."* `theme.py` ships `@media print` and `@media (prefers-reduced-motion:reduce)`
overrides for all three as a floor, but the JS is the real fix.

**3. The dark palette is dead code.** `build.py:397` emits
`<html lang="en" data-theme="light">`, so `:root:not([data-theme="light"])` never matches and
`:root[data-theme="dark"]` never matches. Every dark token on the site — old and new — is
unreachable today. Either ship a toggle that writes the attribute, or emit no attribute so
the `:not()` branch can follow the OS preference. Decide before launch; do not leave a full
dark palette that nobody can reach.

**4. Focus rings are invisible in dark mode** — `outline:2px solid var(--nav)` is 1.21:1 on
the dark page. `theme.py` shims `outline-color`; the modules must move to `var(--focus)`.

---

## 10. Where I overruled a researcher

- **Warm paper over pure white.** One researcher's verified palette assumed `#FFFFFF` and
  slate neutrals at hue 248; another wanted warm paper with warm ink. Both cannot hold — a
  warm page with cool card fills is mud. The page is 81% of the pixels, so the dominant
  surface sets the temperature and everything neutral follows it. Warm paper is where the
  research-institution cluster sits (Anthropic `#FAF9F5`, Allen Institute `#FAF2E9`, Tufte
  `#FFFFF8`, Works in Progress `#FFF7F4`), it is what the reading-comfort literature supports
  against high-contrast white, and it is the largest single change available from colour. The
  cool navy column against warm paper is a near-complementary pairing, which is the cleanest
  possible separation, not a muddy one.
- **Hue 248 over hue 236/243 for the navy.** The band argument is measured and the other is
  not: Oxford 254.4, Yale 254.4, Nature 238.0, Distill 250.2, Stanford HAI 249.3. 248 sits
  inside it; 233.8 did not, which is the arithmetic behind "generic".
- **Headings at 600, not 400.** One researcher wanted every heading at 400 with optical size
  alone carrying hierarchy. Against a sans-600 furniture layer that reads under-set, and the
  600 is already being downloaded for the 428 `<strong>` runs, so it costs nothing.
- **Serif 400+600, not 400 alone.** The 134.7 KB option would faux-bold 428 inline runs, 288
  of them in one document. 265.2 KB with real bold.
- **`--accent` stays the paper-safe deep amber.** One researcher's token scheme made
  `--accent` the bright amber. Fourteen existing rules use `--accent` as ink or stroke on a
  light surface (`.glance__n`, `.tline__when`, `.pending__tag`, `.doc .ink-a`, `.rb-w`,
  `.topics__step`); that swap would have silently broken every one of them, putting a 2.4:1
  amber on white. The bright value is `--accent-2` / `--accent-on-nav` instead.
- **`.side__end` and the identity block stay as they are.** Deleting the full-height navy, or
  merging the identity into it, were both proposed. The deck is a full-height column with the
  identity above the solid menu block, and merging *raises* the saturated area 21.6%.
- **Keep the `<br>` breaks in the long nav label.** One researcher wanted natural wrapping.
  The label is four fields; breaking mid-field is worse than breaking after each comma, and I
  measured every comma-segment fitting with 41px to spare.
- **The gallery em dashes are ours, not his.** Sourced against `DOCS` and the original
  filenames.

---

## 11. What I could not settle

- **IYTE has no published hex.** I sampled the institution's own logo files served from
  `bhib.iyte.edu.tr` and both resolve to a deep crimson, `#980820` / `#900808`
  (`oklch(0.432 0.170 22)`). So the institutional colour is **not blue at all**. I did not
  anchor the palette to it: `BRIEF2.md` requires the site to still read as a deep blue column
  with a warm accent, and a personal site is not an institutional one. The finding does carry
  one consequence — the deck's brick accent at hue 43.8 sits much closer to IYTE crimson than
  amber at hue 52 does, which is independent support for the warmer accent. If anyone ever
  wants the palette anchored to the institution, someone has to open the corporate identity
  guide at `iyte.edu.tr/hakkinda/kurumsal-gorseller/`, which I could not reach in a
  measurable form. The `#f17203` orange on `iyte.edu.tr` belongs to a calendar plugin, not to
  the brand.
- **Apple's HIG pages are client-rendered and returned only titles** to every fetch. Where I
  invoke HIG — deference, hit targets, motion as feedback — I am relying on `CONTRACT.md`'s
  own transcription and on secondary summaries, not on a page I read.
- **19px is a judgement about this client, not a measurement.** The x-height arithmetic proves
  it is not an increase in apparent size, and gwern (20px) and ciechanow.ski (19.2px) support
  it, but a client who reads "19px" after "16.5px" may react to the number. Show the page
  before defending the number. If he still finds it large, 18px with the same measure rule is
  the floor.
- **I have not seen the deck.** Every claim about what he wrote verbatim comes from
  `build.py`'s transcription and its provenance comment. If that transcription is wrong, my
  em-dash authorship ruling for items 1 and 2 inherits the error. Someone should open
  `content/source/NEW WAVES AND DATA.pptx` and confirm those two sentences before they are
  rewritten.
- **The portrait crop coordinates** (eye line y≈234, head width ≈255px, head centre x≈340)
  were read off the rendered image by eye, not by a face detector. Assume ±10px.
- **I inspected `blog.html`, `contact.html` and the `doc/` pages as markup and computed
  styles, not visually.** The 608px measure narrows the document pages considerably; the
  figure and table breakout in §2.3 is the intended answer, but it needs a designer to look
  at a real 30-figure, 18-table document before it ships.

---

## 12. Worklist by owner

**theme** — done and building. `parts/theme.py`.

**integrator (`build.py`)** — swap the font `<link>` at 403 · delete the `<img>` at 415 and
the `headshot.webp` emit at 740 · change the wordmark string to "Korkut Kaynardag" and move
PhD to the affiliation · rewrite the nav label at 39 with a `<br>` after each comma · add
`aria-current="page"` to the active nav item · decide the `data-theme` question at 397 · fix
the em dashes at 474, 486, 494, 499, 521, 523, 556, 590, 654, 665 · normalise hardcoded radii
to 8px · add the U+2014 build assertion.

**hero** — ghost About-me button · h1 to 600 and the §2.2 scale · the two-path arrow · drop
`object-position` and ship the 520×650 crop in a 280px card · restore his `PROF_INTRO` and
`PROF_BIO` wording · `62ch` → `var(--measure)` · focus rings to `var(--focus)`.

**topics** — delete the chips, the ordinals and the gradient bar · the three new icons at
28px / stroke 1.2 with one `--accent` detail each · hairline-top card, no fill, no border, no
shadow · §4 hover · fix the observer failsafe · title and description to the §2.2 scale · two
em dashes.

**about** — `.glance__n` to `lining-nums proportional-nums` · six date ranges to closed-up en
dashes · "Since 2026" · delete `.glance__dash` · add the reveal failsafe · `62ch` →
`var(--measure)` · §4 hover on `.glance__card` and `.tline__item` · focus rings.

**rboxes** — plate icons to `stroke-width:0.75` at 56px · remove `translateY(-2px)` and the
shadow change · §4 card hover · focus rings.

**gallery** — the `&mdash;` joiners to colons · `.g-row` hover per §4 · focus rings.
